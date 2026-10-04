"""Model klastrów likwidacji (estymacja jak w heatmapach Coinglass / Hyblock).

Dla każdej świecy przyrost open interest (lub - bez OI - część wolumenu) traktujemy
jako nowo otwarte pozycje po cenie typowej, rozdzielone na longi/shorty
(long/short ratio lub kierunek świecy) i rozłożone na typowe dźwignie.
Cena likwidacji:  long = p*(1 - 1/L + MMR),  short = p*(1 + 1/L - MMR).
Poziomy, przez które cena już przeszła, są usuwane (pozycje zlikwidowane),
a stare poziomy wygasają wykładniczo (pozycje zamykane z innych powodów).

Wynik dla każdej świecy: intensywność likwidacji shortów powyżej ceny i longów
poniżej ceny (w zakresie skanowania) oraz 3 najsilniejsze klastry z każdej strony.
Klastry działają jak magnes (cena "poluje" na płynność) - wykorzystywane do
scoringu, wyboru TP oraz do tego, by NIE stawiać SL wewnątrz klastra.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


class LiquidationModel:
    def __init__(self, price_lo: float, price_hi: float, leverages=(10, 25, 50, 100),
                 lev_weights=(0.35, 0.35, 0.2, 0.1), mmr: float = 0.005, bin_pct: float = 0.0025,
                 decay: float = 0.995):
        self.log_lo = np.log(price_lo * 0.5)
        self.step = np.log(1 + bin_pct)
        self.nbins = int(np.ceil((np.log(price_hi * 2.0) - self.log_lo) / self.step)) + 1
        self.long_map = np.zeros(self.nbins)   # poziomy likwidacji longów (poniżej ceny)
        self.short_map = np.zeros(self.nbins)  # poziomy likwidacji shortów (powyżej ceny)
        self.lev = np.asarray(leverages, float)
        self.lw = np.asarray(lev_weights, float) / np.sum(lev_weights)
        self.mmr = mmr
        self.decay = decay

    def idx(self, price: float) -> int:
        return int(np.clip((np.log(price) - self.log_lo) / self.step, 0, self.nbins - 1))

    def price_of(self, i: int | np.ndarray):
        return np.exp(self.log_lo + (np.asarray(i) + 0.5) * self.step)

    def update(self, high: float, low: float, typical: float, new_long: float, new_short: float) -> None:
        self.long_map *= self.decay
        self.short_map *= self.decay
        self.long_map[self.idx(low):] = 0.0          # longi z likwidacją >= low zostały zlikwidowane
        self.short_map[: self.idx(high) + 1] = 0.0   # shorty z likwidacją <= high zostały zlikwidowane
        if new_long > 0:
            lp = typical * (1 - 1 / self.lev + self.mmr)
            for p, w in zip(lp, self.lw):
                self.long_map[self.idx(p)] += new_long * w
        if new_short > 0:
            sp = typical * (1 + 1 / self.lev - self.mmr)
            for p, w in zip(sp, self.lw):
                self.short_map[self.idx(p)] += new_short * w

    def add_observed(self, price: float, size: float, side_long: bool) -> None:
        """Zewnętrzne poziomy (np. heatmapa Coinglass)."""
        (self.long_map if side_long else self.short_map)[self.idx(price)] += size

    def features(self, close: float, scan_pct: float = 0.05, min_share: float = 0.08, top: int = 3) -> dict:
        ci = self.idx(close)
        k = int(np.ceil(np.log(1 + scan_pct) / self.step))
        above = self.short_map[ci + 1: ci + 1 + k]
        below = self.long_map[max(0, ci - k): ci]
        ia, ib = float(above.sum()), float(below.sum())
        out = {"liq_above": ia, "liq_below": ib}
        for name, arr, offset, tot in (("up", above, ci + 1, ia), ("dn", below, max(0, ci - k), ib)):
            prices, shares = [], []
            if tot > 0:
                order = np.argsort(arr)[::-1][:top]
                for j in order:
                    sh = arr[j] / tot
                    if sh >= min_share:
                        prices.append(float(self.price_of(offset + j)))
                        shares.append(float(sh))
            for t in range(top):
                out[f"liq_{name}{t + 1}"] = prices[t] if t < len(prices) else np.nan
                out[f"liq_{name}{t + 1}_share"] = shares[t] if t < len(shares) else 0.0
        return out


def liquidation_features(df: pd.DataFrame, oi: pd.Series | None = None, buy_ratio: pd.Series | None = None,
                         leverages=(10, 25, 50, 100), lev_weights=(0.35, 0.35, 0.2, 0.1), mmr: float = 0.005,
                         bin_pct: float = 0.0025, decay: float = 0.995, scan_pct: float = 0.05,
                         min_share: float = 0.08) -> pd.DataFrame:
    """Rolling estymacja klastrów - wartości w wierszu t znane na zamknięciu świecy t."""
    model = LiquidationModel(float(df["low"].min()), float(df["high"].max()), leverages, lev_weights,
                             mmr, bin_pct, decay)
    typical = ((df["high"] + df["low"] + df["close"]) / 3).values
    if oi is not None and oi.notna().sum() > 10:
        oi_al = oi.reindex(df.index).ffill()
        new_pos = (oi_al.diff().clip(lower=0) * df["close"]).fillna(0).values  # USD nowych pozycji
    else:
        new_pos = (df["volume"] * df["close"] * 0.1).fillna(0).values
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    clv = ((2 * df["close"] - df["high"] - df["low"]) / rng).fillna(0).values
    if buy_ratio is not None and buy_ratio.notna().sum() > 10:
        long_share = buy_ratio.reindex(df.index).ffill().fillna(0.5).clip(0.2, 0.8).values
    else:
        long_share = np.clip(0.5 + 0.2 * clv, 0.2, 0.8)
    h, l, c = df["high"].values, df["low"].values, df["close"].values
    rows = []
    for i in range(len(df)):
        model.update(h[i], l[i], typical[i], new_pos[i] * long_share[i], new_pos[i] * (1 - long_share[i]))
        rows.append(model.features(c[i], scan_pct, min_share))
    out = pd.DataFrame(rows, index=df.index)
    tot = out["liq_above"] + out["liq_below"]
    out["s_liq"] = ((out["liq_above"] - out["liq_below"]) / tot.replace(0, np.nan)).fillna(0)
    return out
