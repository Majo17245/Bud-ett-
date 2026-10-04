"""Momentum: RSI, MACD, dywergencje (regularne) RSI/cena na potwierdzonych pivotach."""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.trend import ema, swing_points, wilder


def rsi(close: pd.Series, n: int = 14) -> pd.Series:
    d = close.diff()
    gain = wilder(d.clip(lower=0), n)
    loss = wilder((-d).clip(lower=0), n)
    rs = gain / loss.replace(0, np.nan)
    out = 100 - 100 / (1 + rs)
    return out.where(loss != 0, 100.0).where(gain.notna())


def macd(close: pd.Series, fast: int = 12, slow: int = 26, signal: int = 9) -> pd.DataFrame:
    m = ema(close, fast) - ema(close, slow)
    s = m.ewm(span=signal, adjust=False, min_periods=signal).mean()
    return pd.DataFrame({"macd": m, "macd_signal": s, "macd_hist": m - s}, index=close.index)


def divergences(df: pd.DataFrame, osc: pd.Series, lookback: int = 3, max_age: int = 12,
                min_bars: int = 5, max_bars: int = 60) -> pd.Series:
    """+1 = byczo (cena LL, RSI HL), -1 = niedźwiedzio (cena HH, RSI LH), 0 = brak.

    Sygnał aktywny przez `max_age` świec od potwierdzenia drugiego pivota.
    """
    sp = swing_points(df, lookback)
    n = len(df)
    sig = np.zeros(n)
    osc_v = osc.values
    for kind, price_col, pos_col, sign in (("low", "sl_confirm", "sl_pos", 1), ("high", "sh_confirm", "sh_pos", -1)):
        conf_idx = np.where(sp[price_col].notna().values)[0]
        prev = None
        for ci in conf_idx:
            p_pos = int(sp[pos_col].iat[ci])
            price = sp[price_col].iat[ci]
            if prev is not None:
                pp_pos, pp_price = prev
                gap = p_pos - pp_pos
                if min_bars <= gap <= max_bars and np.isfinite(osc_v[p_pos]) and np.isfinite(osc_v[pp_pos]):
                    if kind == "low" and price < pp_price and osc_v[p_pos] > osc_v[pp_pos]:
                        _mark(sig, ci, min(n, ci + max_age), 1)
                    if kind == "high" and price > pp_price and osc_v[p_pos] < osc_v[pp_pos]:
                        _mark(sig, ci, min(n, ci + max_age), -1)
            prev = (p_pos, price)
    return pd.Series(sig, index=df.index, name="divergence")


def _mark(sig: np.ndarray, a: int, b: int, val: int) -> None:
    """Ustawia sygnał; sprzeczne dywergencje w tym samym oknie znoszą się (0)."""
    seg = sig[a:b]
    sig[a:b] = np.where(seg == -val, 0, val)


def momentum_features(df: pd.DataFrame, rsi_n: int = 14, macd_p=(12, 26, 9), atr: pd.Series | None = None,
                      lookback: int = 3, div_age: int = 12, div_min: int = 5) -> pd.DataFrame:
    r = rsi(df["close"], rsi_n)
    m = macd(df["close"], *macd_p)
    div = divergences(df, r, lookback, div_age, div_min)
    norm = atr if atr is not None else (df["high"] - df["low"]).rolling(14).mean()
    hist_n = m["macd_hist"] / norm.replace(0, np.nan)
    # RSI: kierunek momentum, wygaszany przy wykupieniu/wyprzedaniu (ryzyko odwrotu)
    s_rsi = ((r - 50) / 20).clip(-1, 1)
    s_rsi = s_rsi.where(r <= 75, 1 - (r - 75) / 10).where(r >= 25, -1 + (25 - r) / 10).clip(-1, 1)
    slope = np.sign(m["macd_hist"].diff())
    s_macd = 0.5 * np.tanh(2 * hist_n) + 0.5 * slope
    raw = (0.35 * s_rsi.fillna(0) + 0.35 * s_macd.fillna(0) + 0.30 * div).clip(-1, 1)
    return pd.DataFrame({"rsi": r, "macd": m["macd"], "macd_hist": m["macd_hist"], "macd_hist_n": hist_n,
                         "macd_slope": slope, "divergence": div, "s_rsi": s_rsi, "s_macd": s_macd,
                         "momentum_score": 100 * raw}, index=df.index)
