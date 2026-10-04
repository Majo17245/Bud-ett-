"""Zmienność: ATR (Wilder), ATR% i percentyl ATR% (filtr skrajnej zmienności)."""
from __future__ import annotations

import pandas as pd

from indicators.trend import true_range, wilder


def atr(df: pd.DataFrame, n: int = 14) -> pd.Series:
    return wilder(true_range(df), n)


def volatility_features(df: pd.DataFrame, n: int = 14, pct_window: int = 2160) -> pd.DataFrame:
    a = atr(df, n)
    atr_pct = a / df["close"]
    rank = atr_pct.rolling(pct_window, min_periods=min(pct_window, 200)).rank(pct=True)
    bar_range_atr = (df["high"] - df["low"]) / a.shift(1)
    return pd.DataFrame({"atr": a, "atr_pct": atr_pct, "atr_pct_rank": rank,
                         "bar_range_atr": bar_range_atr}, index=df.index)
