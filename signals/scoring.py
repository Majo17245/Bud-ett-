"""System scoringu: każdy moduł daje ocenę -100 (silny short) .. +100 (silny long).

Wynik końcowy = średnia ważona dostępnych modułów (wagi z config.yaml,
renormalizowane, gdy moduł jest niedostępny - np. order book w backteście).
Funkcje działają wektorowo na całym DataFrame cech (backtest) i na jednym
wierszu (live) - ten sam kod w obu trybach.
"""
from __future__ import annotations

import numpy as np
import pandas as pd

MODULES = ("trend", "momentum", "volume", "positioning", "orderbook", "macro", "sentiment")


def _wavg(parts: list[tuple[pd.Series, float]], index) -> pd.Series:
    num = pd.Series(0.0, index=index)
    den = pd.Series(0.0, index=index)
    for s, w in parts:
        s = pd.Series(s, index=index) if not isinstance(s, pd.Series) else s
        ok = s.notna()
        num = num + s.fillna(0) * w
        den = den + ok.astype(float) * w
    return (num / den.replace(0, np.nan))


def _col(F: pd.DataFrame, name: str) -> pd.Series:
    return F[name] if name in F.columns else pd.Series(np.nan, index=F.index)


def module_scores(F: pd.DataFrame, cfg, kind: str = "single", volume_weight: pd.Series | float = 1.0) -> pd.DataFrame:
    sc = cfg.get("scoring", {})
    tfw = sc.get("trend_tf_weights", {"60": 0.3, "240": 0.4, "D": 0.3})
    mfw = sc.get("momentum_tf_weights", {"60": 0.5, "240": 0.5})
    idx = F.index
    out = pd.DataFrame(index=idx)
    out["trend_1h"] = _col(F, "h1_trend_score")
    out["trend_4h"] = _col(F, "h4_trend_score")
    out["trend_1d"] = _col(F, "d1_trend_score")
    out["trend"] = _wavg([(out["trend_1h"], tfw["60"]), (out["trend_4h"], tfw["240"]), (out["trend_1d"], tfw["D"])], idx)
    out["momentum"] = _wavg([(_col(F, "h1_momentum_score"), mfw["60"]), (_col(F, "h4_momentum_score"), mfw["240"])], idx)

    if kind == "pair":
        rel_cvd = np.tanh(3 * _col(F, "rel_cvd"))
        out["volume"] = 100 * _wavg([(rel_cvd, 0.6), (_col(F, "s_vp"), 0.4)], idx).clip(-1, 1)
        f_rel = (_col(F, "rel_funding") / 0.0003).clip(-1, 1)
        ls_rel = (_col(F, "rel_ls_z") / 2).clip(-1, 1)
        out["positioning"] = 100 * _wavg([(f_rel, 0.5), (ls_rel, 0.5)], idx)
        # risk-off -> BTC zyskuje względem ETH; skrajny strach -> dominacja BTC
        out["macro"] = -60 * _col(F, "risk_regime")
        out["sentiment"] = -60 * _col(F, "fng_extreme")
        out["orderbook"] = _col(F, "orderbook_score")
    else:
        rv = _col(F, "rvol_dir") * volume_weight
        out["volume"] = 100 * _wavg([(_col(F, "s_cvd"), 0.4), (rv, 0.3), (_col(F, "s_vp"), 0.3)], idx).clip(-1, 1)
        out["positioning"] = 100 * _wavg([(_col(F, "s_oi"), 0.30), (_col(F, "s_funding"), 0.25),
                                          (_col(F, "s_ls"), 0.20), (_col(F, "s_liq"), 0.25)], idx).clip(-1, 1)
        out["orderbook"] = _col(F, "orderbook_score")
        out["macro"] = _col(F, "macro_score")
        out["sentiment"] = _col(F, "sentiment_score")

    weights = sc.get("pair_weights" if kind == "pair" else "weights", {})
    out["composite"] = _wavg([(out[m], float(weights.get(m, 0))) for m in MODULES], idx).clip(-100, 100)
    return out


def agreement(row: dict, direction: int, weak: float = 10, strong: float = 50) -> tuple[int, int, list[str]]:
    """Liczba modułów zgodnych z kierunkiem i liczba silnie przeciwnych."""
    agree, opp, opp_names = 0, 0, []
    for m in MODULES:
        v = row.get(m)
        if v is None or not np.isfinite(v):
            continue
        if direction * v >= weak:
            agree += 1
        if direction * v <= -strong:
            opp += 1
            opp_names.append(m)
    return agree, opp, opp_names
