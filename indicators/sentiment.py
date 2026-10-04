"""Sentyment: Crypto Fear & Greed (0..100).

Skrajne wartości działają kontrariańsko: < 20 (skrajny strach) -> plus dla longów,
> 80 (skrajna chciwość) -> minus dla longów i ostrzeżenie w logu.
W przedziale 20-80 wpływ jest słaby (lekko kontrariański wokół 50).
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def fng_score(v: pd.Series | float, fear: float = 20, greed: float = 80):
    v = pd.Series(v) if not isinstance(v, pd.Series) else v
    mid = (fear + greed) / 2
    mild = -((v - mid) / (greed - mid)) * 0.3
    extreme_fear = 0.6 + 0.4 * ((fear - v) / fear).clip(0, 1)
    extreme_greed = -0.6 - 0.4 * ((v - greed) / (100 - greed)).clip(0, 1)
    s = np.where(v < fear, extreme_fear, np.where(v > greed, extreme_greed, mild))
    return pd.Series(100 * s, index=v.index).where(v.notna())


def sentiment_daily(fng: pd.Series | None, fear: float = 20, greed: float = 80) -> pd.DataFrame | None:
    if fng is None or len(fng) == 0:
        return None
    s = fng.copy()
    s.index = pd.DatetimeIndex(s.index).normalize()
    s = s[~s.index.duplicated(keep="last")]
    return pd.DataFrame({"fng": s, "sentiment_score": fng_score(s, fear, greed),
                         "fng_extreme": np.where(s < fear, -1, np.where(s > greed, 1, 0))}, index=s.index)
