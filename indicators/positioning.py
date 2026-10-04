"""Pozycjonowanie: open interest, funding rate, long/short ratio (+ klastry likwidacji)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def positioning_features(index: pd.DatetimeIndex, close: pd.Series, oi: pd.Series | None,
                         funding: pd.Series | None, buy_ratio: pd.Series | None,
                         oi_window: int = 24, ls_window: int = 720) -> pd.DataFrame:
    """Wartości wyrównane do indeksu świec 1h (czas zamknięcia), tylko dane z przeszłości."""
    out = pd.DataFrame(index=index)
    price_chg = close.pct_change(oi_window)
    if oi is not None and oi.notna().sum() > oi_window:
        oi_al = oi.reindex(index, method="ffill") if not oi.index.equals(index) else oi
        oi_chg = oi_al.pct_change(oi_window)
        out["oi_chg"] = oi_chg
        # cena+OI rosną = nowe longi (+); cena spada, OI rośnie = nowe shorty (-);
        # cena rośnie, OI spada = short covering (słabe +); cena spada, OI spada = likwidacja longów (słabe -)
        mag = np.tanh(np.abs(oi_chg) / 0.03)
        strong = np.where(oi_chg > 0, 0.8, 0.3)
        out["s_oi"] = (np.sign(price_chg) * strong * (0.4 + 0.6 * mag)).fillna(0)
    else:
        out["oi_chg"] = np.nan
        out["s_oi"] = np.nan
    if funding is not None and funding.notna().sum() > 3:
        f_al = funding.reindex(index, method="ffill") if not funding.index.equals(index) else funding
        out["funding"] = f_al
        # kontrariańsko: wysoki dodatni funding = zatłoczone longi -> ujemny wynik
        # neutralna stopa bazowa Bybit = 0.01% / 8h
        out["s_funding"] = (-((f_al - 0.0001) / 0.0004)).clip(-1, 1).fillna(0)
    else:
        out["funding"] = np.nan
        out["s_funding"] = np.nan
    if buy_ratio is not None and buy_ratio.notna().sum() > 48:
        br = buy_ratio.reindex(index, method="ffill") if not buy_ratio.index.equals(index) else buy_ratio
        mean = br.rolling(ls_window, min_periods=48).mean()
        std = br.rolling(ls_window, min_periods=48).std()
        z = (br - mean) / std.replace(0, np.nan)
        out["ls_ratio"] = br
        out["ls_z"] = z
        out["s_ls"] = (-(z / 2)).clip(-1, 1).fillna(0)  # kontrariańsko wobec tłumu
    else:
        out["ls_ratio"] = np.nan
        out["ls_z"] = np.nan
        out["s_ls"] = np.nan
    return out
