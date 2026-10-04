"""Generator SYNTETYCZNYCH danych rynkowych - wyłącznie do testów technicznych.

Używany, gdy brak dostępu do API Bybit (np. sandbox bez internetu) i w testach
jednostkowych. Model: reżimy (hossa/bessa/konsolidacja) jako łańcuch Markowa,
zmienność GARCH(1,1), ogony t-Studenta, korelacja BTC-ETH ~0.8, wolumen zależny
od |zwrotu|, syntetyczne OI / funding / long-short ratio / makro / Fear&Greed.

WYNIKI BACKTESTU NA TYCH DANYCH NIE MÓWIĄ NIC O SKUTECZNOŚCI STRATEGII
NA PRAWDZIWYM RYNKU - służą tylko do sprawdzenia, że cały pipeline działa.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import numpy as np
import pandas as pd

REGIMES = {  # dryf na godzinę, mnożnik zmienności, średni czas trwania (h)
    "bull": (0.00010, 0.9, 24 * 45),
    "bear": (-0.00011, 1.15, 24 * 30),
    "range": (0.0, 0.8, 24 * 35),
}


def _regime_path(n: int, rng: np.random.Generator) -> np.ndarray:
    names = list(REGIMES)
    out = np.empty(n, dtype=object)
    i, cur = 0, rng.choice(names)
    while i < n:
        dur = int(rng.exponential(REGIMES[cur][2])) + 24
        out[i:i + dur] = cur
        i += dur
        cur = rng.choice([x for x in names if x != cur])
    return out


def _garch_returns(n: int, rng: np.random.Generator, base_vol: float, shocks: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    omega, alpha, beta = base_vol ** 2 * 0.04, 0.08, 0.88
    var = np.empty(n)
    ret = np.empty(n)
    var[0] = base_vol ** 2
    for t in range(n):
        if t > 0:
            var[t] = omega + alpha * ret[t - 1] ** 2 + beta * var[t - 1]
        ret[t] = np.sqrt(var[t]) * shocks[t]
    return ret, np.sqrt(var)


def _ohlcv(close: np.ndarray, vol: np.ndarray, rng: np.random.Generator, base_volume: float,
           idx: pd.DatetimeIndex) -> pd.DataFrame:
    open_ = np.concatenate([[close[0]], close[:-1]])
    wick = np.abs(rng.normal(0, 0.55, (2, len(close)))) * vol
    high = np.maximum(open_, close) * (1 + wick[0])
    low = np.minimum(open_, close) * (1 - wick[1])
    hour = idx.hour.values
    season = 1 + 0.35 * np.sin((hour - 8) / 24 * 2 * np.pi)  # sesja US/EU - większy wolumen
    rel_move = np.abs(np.log(close / open_)) / np.maximum(vol, 1e-9)
    volume = base_volume * season * (0.6 + 0.9 * rel_move) * rng.lognormal(0, 0.35, len(close))
    return pd.DataFrame({"open": open_, "high": high, "low": low, "close": close,
                         "volume": volume, "turnover": volume * close}, index=idx)


def resample_ohlcv(df: pd.DataFrame, rule: str) -> pd.DataFrame:
    agg = {"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum", "turnover": "sum"}
    out = df.resample(rule, label="left", closed="left").agg(agg).dropna()
    out.index = out.index.as_unit("ns")
    return out


def generate_dataset(symbols: list[str] | None = None, years: float = 2.5, seed: int = 7,
                     end: datetime | None = None) -> dict:
    symbols = symbols or ["BTCUSDT", "ETHUSDT"]
    rng = np.random.default_rng(seed)
    n = int(years * 365 * 24) + 24 * 60
    end = (end or datetime(2026, 10, 1, tzinfo=timezone.utc)).replace(minute=0, second=0, microsecond=0)
    idx = pd.date_range(end=end - timedelta(hours=1), periods=n, freq="1h", tz="UTC").as_unit("ns")
    idx.name = "ts"

    regimes = _regime_path(n, rng)
    drift = np.array([REGIMES[r][0] for r in regimes])
    vmult = np.array([REGIMES[r][1] for r in regimes])

    t_shocks = rng.standard_t(4, size=(2, n)) / np.sqrt(2.0)  # wariancja t(4) = 2
    common = t_shocks[0]
    idio = t_shocks[1]
    btc_ret, btc_vol = _garch_returns(n, rng, 0.0055, common)
    eth_shock = 0.82 * common + np.sqrt(1 - 0.82 ** 2) * idio
    eth_ret, eth_vol = _garch_returns(n, rng, 0.0068, eth_shock)

    # konsolidacja: powrót do średniej z ostatnich 5 dni
    out: dict = {"symbols": {}, "macro": {}, "fng": None, "source": "synthetic"}
    start_px = {"BTCUSDT": 42000.0, "ETHUSDT": 2300.0}
    base_volume = {"BTCUSDT": 9000.0, "ETHUSDT": 120000.0}
    rets = {"BTCUSDT": (btc_ret, btc_vol), "ETHUSDT": (eth_ret, eth_vol)}
    closes = {}
    for sym in symbols:
        r, v = rets.get(sym, rets["BTCUSDT"])
        beta = 1.0 if sym == "BTCUSDT" else 1.15
        logp = np.empty(n)
        logp[0] = np.log(start_px.get(sym, 1000.0))
        anchor = logp[0]
        for t in range(1, n):
            mr = 0.0
            if regimes[t] == "range":
                anchor = 0.995 * anchor + 0.005 * logp[t - 1]
                mr = -0.02 * (logp[t - 1] - anchor)
            logp[t] = logp[t - 1] + beta * drift[t] + mr + r[t] * vmult[t]
        close = np.exp(logp)
        closes[sym] = close
        h1 = _ohlcv(close, v * vmult, rng, base_volume.get(sym, 1000.0), idx)
        d = {"60": h1, "240": resample_ohlcv(h1, "4h"), "D": resample_ohlcv(h1, "1D")}

        ret72 = pd.Series(np.log(close)).diff(72).fillna(0).values
        z = ret72 / (np.std(ret72) + 1e-9)
        funding = 0.0001 + 0.00025 * np.tanh(z) + rng.normal(0, 0.00005, n)
        f_idx = idx[idx.hour % 8 == 0]
        d["funding"] = pd.DataFrame({"funding_rate": pd.Series(funding, index=idx).loc[f_idx].values}, index=f_idx)
        oi = np.empty(n)
        oi[0] = 1.0
        oi_noise = rng.normal(0, 0.004, n)
        for t in range(1, n):
            oi[t] = oi[t - 1] * (1 + 0.15 * np.tanh(z[t]) * 0.01 + oi_noise[t] - 0.0002 * (oi[t - 1] - 1))
        d["oi"] = pd.DataFrame({"open_interest": oi * 50000 * (1 if sym == "BTCUSDT" else 12)}, index=idx)
        ls = 0.55 + 0.08 * np.tanh(z) + rng.normal(0, 0.02, n)
        d["ls"] = pd.DataFrame({"buy_ratio": np.clip(ls, 0.2, 0.85)}, index=idx)
        out["symbols"][sym] = d

    days = pd.date_range(idx[0].normalize(), idx[-1].normalize(), freq="1D", tz="UTC").as_unit("ns")
    btc_daily = pd.Series(closes[symbols[0]], index=idx).resample("1D").last().reindex(days).ffill()
    btc_dret = np.log(btc_daily).diff().fillna(0).values
    spx_ret = 0.00015 + 0.075 * btc_dret + rng.normal(0, 0.009, len(days))
    gold_ret = 0.0002 + rng.normal(0, 0.008, len(days))
    biz = days.dayofweek < 5
    out["macro"]["spx"] = pd.Series(5000 * np.exp(np.cumsum(spx_ret)), index=days)[biz]
    out["macro"]["gold"] = pd.Series(2000 * np.exp(np.cumsum(gold_ret)), index=days)[biz]
    r30 = np.log(btc_daily).diff(30).fillna(0)
    fng = 50 + 35 * np.tanh(r30 / 0.15) + rng.normal(0, 6, len(days))
    out["fng"] = pd.Series(np.clip(fng, 1, 99).round(), index=days)
    return out
