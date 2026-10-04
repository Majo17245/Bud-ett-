"""Makro: krocząca korelacja BTC z US500 i złotem, reżim risk-on / risk-off.

Wszystkie serie są indeksowane CZASEM DOSTĘPNOŚCI: dzienna świeca BTC - czasem
zamknięcia (open + 1 dzień), sesja US500/złota z dnia D - od D+1 00:00 UTC
(zamknięcie sesji ~21:00 UTC). Dzięki temu nie ma lookahead.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def _available(s: pd.Series) -> pd.Series:
    s = s.copy()
    s.index = pd.DatetimeIndex(s.index).normalize().as_unit("ns") + pd.Timedelta(days=1)
    return s[~s.index.duplicated(keep="last")]


def macro_daily(btc_daily_close: pd.Series, spx: pd.Series | None, gold: pd.Series | None,
                window: int = 30, min_corr: float = 0.25) -> pd.DataFrame:
    """btc_daily_close: indeks = czas ZAMKNIĘCIA świecy dziennej."""
    days = pd.DatetimeIndex(btc_daily_close.index).normalize().as_unit("ns")
    btc = pd.Series(btc_daily_close.values, index=days)
    btc = btc[~btc.index.duplicated(keep="last")]
    out = pd.DataFrame(index=btc.index)
    btc_r = np.log(btc).diff()
    s_total = pd.Series(0.0, index=btc.index)
    have = False
    if spx is not None and len(spx) > window:
        spx_a = _available(spx)
        spx_d = spx_a.reindex(spx_a.index.union(btc.index)).ffill().reindex(btc.index)
        spx_r = np.log(spx_d).diff()
        corr = btc_r.rolling(window, min_periods=window // 2).corr(spx_r)
        sma50 = spx_d.rolling(50, min_periods=20).mean()
        ret20 = spx_d.pct_change(20)
        regime = np.where((spx_d > sma50) & (ret20 > 0), 1.0, np.where((spx_d < sma50) & (ret20 < 0), -1.0, 0.0))
        out["corr_spx"] = corr
        out["spx_regime"] = regime
        # wpływ makro na BTC tylko gdy korelacja istotna
        w = ((corr - min_corr) / (0.6 - min_corr)).clip(0, 1).fillna(0)
        s_total += 0.7 * regime * (0.3 + 0.7 * w)
        have = True
    else:
        out["corr_spx"] = np.nan
        out["spx_regime"] = np.nan
    if gold is not None and len(gold) > window:
        g_a = _available(gold)
        g = g_a.reindex(g_a.index.union(btc.index)).ffill().reindex(btc.index)
        g_r = np.log(g).diff()
        corr_g = btc_r.rolling(window, min_periods=window // 2).corr(g_r)
        g_ret20 = g.pct_change(20)
        out["corr_gold"] = corr_g
        out["gold_trend"] = np.sign(g_ret20)
        # silnie rosnące złoto przy spadających akcjach = ucieczka do bezpieczeństwa (risk-off)
        flight = ((g_ret20 > 0.04) & (out["spx_regime"].fillna(0) < 0)).astype(float)
        s_total += -0.3 * flight + 0.3 * np.sign(g_ret20).fillna(0) * corr_g.clip(0, 1).fillna(0)
        have = True
    else:
        out["corr_gold"] = np.nan
        out["gold_trend"] = np.nan
    out["risk_regime"] = np.sign(s_total).where(s_total.abs() > 0.2, 0.0)
    out["macro_score"] = (100 * s_total.clip(-1, 1)) if have else np.nan
    return out


def align_daily_to_hourly(daily: pd.DataFrame | pd.Series, hourly_close_index: pd.DatetimeIndex) -> pd.DataFrame:
    """Wartość z indeksem t (czas dostępności) obowiązuje od t."""
    d = daily.copy()
    d.index = pd.DatetimeIndex(d.index).as_unit("ns")
    return d.reindex(d.index.union(hourly_close_index)).ffill().reindex(hourly_close_index)
