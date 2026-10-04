"""Budowa cech multi-timeframe (1h / 4h / 1d) - wspólna dla backtestu i bota live.

Zasada braku lookahead: każda świeca jest indeksowana CZASEM ZAMKNIĘCIA
(open_time + interwał). Cechy 4h i 1d są dołączane do świec 1h przez
merge_asof "backward" - w chwili t widzimy tylko świece zamknięte <= t.
OI i long/short ratio są dodatkowo opóźnione o 1h (konserwatywnie).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from indicators.liquidations import liquidation_features
from indicators.macro import align_daily_to_hourly, macro_daily
from indicators.momentum import momentum_features
from indicators.positioning import positioning_features
from indicators.sentiment import sentiment_daily
from indicators.trend import trend_score
from indicators.volatility import volatility_features
from indicators.volume import volume_features

TF_DELTA = {"60": pd.Timedelta(hours=1), "240": pd.Timedelta(hours=4), "D": pd.Timedelta(days=1)}
PREFIX = {"60": "h1_", "240": "h4_", "D": "d1_"}


def to_close_index(df: pd.DataFrame, tf: str) -> pd.DataFrame:
    out = df.copy()
    out.index = (pd.DatetimeIndex(df.index) + TF_DELTA[tf]).as_unit("ns")
    out.index.name = "ts"
    return out


def tf_features(df: pd.DataFrame, tf: str, cfg) -> pd.DataFrame:
    ic = cfg.get("indicators", {})
    vol = volatility_features(df, ic.get("atr_period", 14),
                              cfg.get_path("filters.atr_percentile_window", 2160) if tf == "60" else 500)
    tr = trend_score(df, tuple(ic.get("ema", [20, 50, 200])), ic.get("adx_period", 14), ic.get("swing_lookback", 3))
    mo = momentum_features(df, ic.get("rsi_period", 14), tuple(ic.get("macd", [12, 26, 9])), atr=vol["atr"],
                           lookback=ic.get("swing_lookback", 3), div_age=ic.get("divergence_max_age", 12),
                           div_min=ic.get("divergence_min_bars", 5))
    out = pd.concat([df[["open", "high", "low", "close", "volume"]], vol, tr.drop(columns=[], errors="ignore"), mo],
                    axis=1)
    out = out.loc[:, ~out.columns.duplicated()]
    return to_close_index(out, tf)


def _asof(left: pd.DataFrame, right: pd.DataFrame, prefix: str) -> pd.DataFrame:
    r = right.add_prefix(prefix).sort_index()
    l_idx = pd.DataFrame(index=left.index)
    merged = pd.merge_asof(l_idx.reset_index(), r.reset_index(), on="ts", direction="backward")
    merged.index = left.index
    return merged.drop(columns=["ts"])


def _shift_series(s: pd.Series | None, hours: int = 1) -> pd.Series | None:
    if s is None:
        return None
    s = s.copy()
    s.index = pd.DatetimeIndex(s.index).as_unit("ns") + pd.Timedelta(hours=hours)
    return s


def _align(s: pd.Series | None, index: pd.DatetimeIndex) -> pd.Series | None:
    if s is None or len(s) == 0:
        return None
    s = s[~s.index.duplicated(keep="last")].sort_index()
    return s.reindex(s.index.union(index)).ffill().reindex(index)


def build_features(sym_data: dict, cfg, macro: dict | None = None, fng: pd.Series | None = None,
                   live_delta: pd.Series | None = None, vp_step: int = 1) -> pd.DataFrame:
    """Zwraca DataFrame indeksowany czasem zamknięcia świec 1h."""
    ic = cfg.get("indicators", {})
    h1 = sym_data["60"]
    f1 = tf_features(h1, "60", cfg)
    feats = f1.add_prefix("h1_")
    for tf in ("240", "D"):
        if sym_data.get(tf) is not None and len(sym_data[tf]) > 30:
            feats = pd.concat([feats, _asof(feats, tf_features(sym_data[tf], tf, cfg), PREFIX[tf])], axis=1)
    feats["close"] = f1["close"]
    feats["high"] = f1["high"]
    feats["low"] = f1["low"]
    feats["open"] = f1["open"]
    feats["atr"] = f1["atr"]

    vpc = ic.get("volume_profile", {})
    delta = None
    if live_delta is not None:
        # live: realne CVD z transakcji tam, gdzie jest pokrycie; reszta - przybliżenie ze świec
        from indicators.volume import candle_delta
        approx = candle_delta(h1)
        delta = approx.copy()
        common = live_delta.index.intersection(h1.index)
        delta.loc[common] = live_delta.loc[common]
    vf = volume_features(h1, delta, ic.get("rvol_period", 20), ic.get("cvd_window", 24),
                         vpc.get("window_bars", 720), vpc.get("bins", 60), vpc.get("value_area", 0.7), vp_step)
    vf = to_close_index(vf, "60")
    feats = pd.concat([feats, vf], axis=1)

    oi = sym_data.get("oi")
    funding = sym_data.get("funding")
    ls = sym_data.get("ls")
    oi_s = _shift_series(oi["open_interest"] if oi is not None and len(oi) else None)
    ls_s = _shift_series(ls["buy_ratio"] if ls is not None and len(ls) else None)
    f_s = funding["funding_rate"] if funding is not None and len(funding) else None
    idx = feats.index
    pos = positioning_features(idx, feats["close"], _align(oi_s, idx), _align(f_s, idx), _align(ls_s, idx))
    feats = pd.concat([feats, pos], axis=1)

    lc = ic.get("liquidation_model", {})
    h1c = to_close_index(h1, "60")
    liq = liquidation_features(h1c, _align(oi_s, idx), _align(ls_s, idx), tuple(lc.get("leverages", [10, 25, 50, 100])),
                               tuple(lc.get("leverage_weights", [0.35, 0.35, 0.2, 0.1])),
                               lc.get("maintenance_margin", 0.005), lc.get("bin_pct", 0.0025),
                               lc.get("decay_per_bar", 0.995), lc.get("scan_range_pct", 0.05),
                               lc.get("cluster_min_share", 0.08))
    feats = pd.concat([feats, liq], axis=1)

    mc = ic.get("macro", {})
    macro = macro or {}
    if sym_data.get("D") is not None and (macro.get("spx") is not None or macro.get("gold") is not None):
        md = macro_daily(to_close_index(sym_data["D"][["close"]], "D")["close"], macro.get("spx"), macro.get("gold"),
                         mc.get("corr_window_days", 30), mc.get("min_corr", 0.25))
        feats = pd.concat([feats, align_daily_to_hourly(md, idx)], axis=1)
    else:
        for c in ("corr_spx", "spx_regime", "corr_gold", "gold_trend", "risk_regime", "macro_score"):
            feats[c] = np.nan
    sc = ic.get("sentiment", {})
    sd = sentiment_daily(fng, sc.get("extreme_fear", 20), sc.get("extreme_greed", 80))
    if sd is not None:
        feats = pd.concat([feats, align_daily_to_hourly(sd, idx)], axis=1)
    else:
        feats["fng"] = np.nan
        feats["sentiment_score"] = np.nan
        feats["fng_extreme"] = 0
    return feats


# ---------------------------------------------------------------- BTC/ETH
def ratio_ohlcv(btc: pd.DataFrame, eth: pd.DataFrame) -> pd.DataFrame:
    """Syntetyczne świece BTC/ETH. High/low przybliżone punktami współbieżnymi
    (oba maksima / oba minima) - realny przebieg intrabar jest nieznany."""
    idx = btc.index.intersection(eth.index)
    b, e = btc.loc[idx], eth.loc[idx]
    o = b["open"] / e["open"]
    c = b["close"] / e["close"]
    hh = b["high"] / e["high"]
    ll = b["low"] / e["low"]
    high = pd.concat([o, c, hh, ll], axis=1).max(axis=1)
    low = pd.concat([o, c, hh, ll], axis=1).min(axis=1)
    turnover = b["close"] * b["volume"] + e["close"] * e["volume"]
    return pd.DataFrame({"open": o, "high": high, "low": low, "close": c, "volume": turnover / c,
                         "turnover": turnover}, index=idx)


def build_pair_features(btc_data: dict, eth_data: dict, btc_feats: pd.DataFrame, eth_feats: pd.DataFrame,
                        cfg, vp_step: int = 1) -> pd.DataFrame:
    pair = {tf: ratio_ohlcv(btc_data[tf], eth_data[tf]) for tf in ("60", "240", "D") if tf in btc_data}
    feats = build_features(pair, cfg, macro=None, fng=None, vp_step=vp_step)
    # cechy relatywne BTC vs ETH
    b = btc_feats.reindex(feats.index)
    e = eth_feats.reindex(feats.index)
    feats["rel_cvd"] = b["cvd_norm"] - e["cvd_norm"]
    feats["rel_funding"] = e["funding"] - b["funding"]   # ETH bardziej zatłoczony long -> plus dla BTC/ETH
    feats["rel_ls_z"] = e["ls_z"] - b["ls_z"]
    feats["risk_regime"] = b["risk_regime"]
    feats["fng"] = b["fng"]
    feats["fng_extreme"] = b["fng_extreme"]
    for c in ("macro_score", "sentiment_score", "s_oi", "s_funding", "s_ls", "s_liq"):
        feats[c] = np.nan
    feats["btc_close"] = b["close"]
    feats["eth_close"] = e["close"]
    feats["btc_atr"] = b["atr"]
    feats["eth_atr"] = e["atr"]
    feats["btc_h4_atr"] = b.get("h4_atr")
    feats["eth_h4_atr"] = e.get("h4_atr")
    return feats
