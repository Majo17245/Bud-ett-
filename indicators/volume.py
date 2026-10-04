"""Wolumen: CVD, RVOL, Volume Profile (POC / VAH / VAL / HVN).

CVD: w trybie live liczony z realnych transakcji (websocket publicTrade, strona
agresora). W backteście (brak historii transakcji w API) - przybliżenie ze świec:
delta = wolumen x CLV, CLV = (2*close - high - low) / (high - low).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def candle_delta(df: pd.DataFrame) -> pd.Series:
    rng = (df["high"] - df["low"]).replace(0, np.nan)
    clv = ((2 * df["close"] - df["high"] - df["low"]) / rng).fillna(0)
    return df["volume"] * clv


def rvol(volume: pd.Series, n: int = 20) -> pd.Series:
    base = volume.rolling(n, min_periods=max(5, n // 2)).mean().shift(1)
    return volume / base.replace(0, np.nan)


def cvd_features(df: pd.DataFrame, delta: pd.Series, window: int = 24) -> pd.DataFrame:
    d_sum = delta.rolling(window, min_periods=window // 2).sum()
    v_sum = df["volume"].rolling(window, min_periods=window // 2).sum()
    cvd_norm = d_sum / v_sum.replace(0, np.nan)  # -1..1 udział agresywnej strony
    price_chg = df["close"].pct_change(window)
    # dywergencja CVD vs cena: cena rośnie, a agresywni sprzedają (i odwrotnie)
    cvd_div = np.where((price_chg > 0) & (cvd_norm < -0.05), -1.0,
                       np.where((price_chg < 0) & (cvd_norm > 0.05), 1.0, 0.0))
    return pd.DataFrame({"cvd": delta.cumsum(), "cvd_norm": cvd_norm, "cvd_div": cvd_div}, index=df.index)


def profile_from_arrays(prices: np.ndarray, volumes: np.ndarray, bins: int = 60,
                        value_area: float = 0.70, lo: float | None = None, hi: float | None = None) -> dict:
    """Volume Profile z tablic (cena typowa, wolumen)."""
    lo = float(np.nanmin(prices)) if lo is None else lo
    hi = float(np.nanmax(prices)) if hi is None else hi
    if not np.isfinite(lo) or not np.isfinite(hi) or hi <= lo:
        return {"poc": np.nan, "vah": np.nan, "val": np.nan, "hvn": [], "lvn": []}
    hist, edges = np.histogram(prices, bins=bins, range=(lo, hi), weights=volumes)
    centers = (edges[:-1] + edges[1:]) / 2
    total = hist.sum()
    if total <= 0:
        return {"poc": np.nan, "vah": np.nan, "val": np.nan, "hvn": [], "lvn": []}
    poc_i = int(np.argmax(hist))
    lo_i = hi_i = poc_i
    acc = hist[poc_i]
    while acc < value_area * total and (lo_i > 0 or hi_i < bins - 1):
        up = hist[hi_i + 1] if hi_i < bins - 1 else -1
        dn = hist[lo_i - 1] if lo_i > 0 else -1
        if up >= dn:
            hi_i += 1
            acc += hist[hi_i]
        else:
            lo_i -= 1
            acc += hist[lo_i]
    mean = hist.mean()
    hvn = [float(centers[i]) for i in range(1, bins - 1)
           if hist[i] > 1.5 * mean and hist[i] >= hist[i - 1] and hist[i] >= hist[i + 1]]
    lvn = [float(centers[i]) for i in range(1, bins - 1)
           if hist[i] < 0.4 * mean and hist[i] <= hist[i - 1] and hist[i] <= hist[i + 1]]
    return {"poc": float(centers[poc_i]), "vah": float(edges[hi_i + 1]), "val": float(edges[lo_i]),
            "hvn": hvn, "lvn": lvn}


def rolling_volume_profile(df: pd.DataFrame, window: int = 720, bins: int = 60, value_area: float = 0.70,
                           step: int = 1) -> pd.DataFrame:
    """POC/VAH/VAL liczone z ostatnich `window` świec (włącznie z bieżącą zamkniętą)."""
    tp = ((df["high"] + df["low"] + df["close"]) / 3).values
    vol = df["volume"].values
    n = len(df)
    poc = np.full(n, np.nan)
    vah = np.full(n, np.nan)
    val = np.full(n, np.nan)
    min_bars = min(window, max(48, window // 4))
    last = None
    for i in range(min_bars - 1, n):
        if last is not None and (i % step) != 0:
            poc[i], vah[i], val[i] = last
            continue
        a = max(0, i - window + 1)
        prof = profile_from_arrays(tp[a:i + 1], vol[a:i + 1], bins, value_area)
        last = (prof["poc"], prof["vah"], prof["val"])
        poc[i], vah[i], val[i] = last
    return pd.DataFrame({"poc": poc, "vah": vah, "val": val}, index=df.index)


def volume_features(df: pd.DataFrame, delta: pd.Series | None = None, rvol_n: int = 20, cvd_window: int = 24,
                    vp_window: int = 720, vp_bins: int = 60, value_area: float = 0.70,
                    vp_step: int = 1) -> pd.DataFrame:
    delta = candle_delta(df) if delta is None else delta
    cv = cvd_features(df, delta, cvd_window)
    rv = rvol(df["volume"], rvol_n)
    direction = np.sign(df["close"] - df["open"])
    rvol_dir = (direction * ((rv - 1) / 1.5).clip(0, 1)).rolling(3, min_periods=1).mean()
    vp = rolling_volume_profile(df, vp_window, vp_bins, value_area, step=vp_step)
    c = df["close"]
    width = (vp["vah"] - vp["val"]).replace(0, np.nan)
    s_vp = np.where(c > vp["vah"], 1.0, np.where(c < vp["val"], -1.0,
                    ((c - vp["poc"]) / (width / 2)).clip(-1, 1) * 0.5))
    s_vp = pd.Series(s_vp, index=df.index).where(vp["poc"].notna(), 0.0)
    s_cvd = np.tanh(3 * cv["cvd_norm"].fillna(0)) * 0.7 + 0.3 * cv["cvd_div"]
    return pd.DataFrame({
        "cvd_norm": cv["cvd_norm"], "cvd_div": cv["cvd_div"], "rvol": rv, "rvol_dir": rvol_dir,
        "poc": vp["poc"], "vah": vp["vah"], "val": vp["val"], "s_vp": s_vp, "s_cvd": s_cvd,
    }, index=df.index)
