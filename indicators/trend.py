"""Trend: EMA, ADX (+DI/-DI), struktura rynku (HH/HL, LH/LL, BOS).

Wszystkie funkcje są przyczynowe (bez lookahead): pivot jest znany dopiero
po `lookback` świecach od jego wystąpienia i dopiero wtedy trafia do danych.
"""
from __future__ import annotations

import numpy as np
import pandas as pd


def ema(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(span=n, adjust=False, min_periods=n).mean()


def wilder(s: pd.Series, n: int) -> pd.Series:
    return s.ewm(alpha=1.0 / n, adjust=False, min_periods=n).mean()


def true_range(df: pd.DataFrame) -> pd.Series:
    prev = df["close"].shift(1)
    return pd.concat([df["high"] - df["low"], (df["high"] - prev).abs(), (df["low"] - prev).abs()],
                     axis=1).max(axis=1)


def adx(df: pd.DataFrame, n: int = 14) -> pd.DataFrame:
    up = df["high"].diff()
    down = -df["low"].diff()
    plus_dm = pd.Series(np.where((up > down) & (up > 0), up, 0.0), index=df.index)
    minus_dm = pd.Series(np.where((down > up) & (down > 0), down, 0.0), index=df.index)
    atr_ = wilder(true_range(df), n)
    pdi = 100 * wilder(plus_dm, n) / atr_
    mdi = 100 * wilder(minus_dm, n) / atr_
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi).replace(0, np.nan)
    return pd.DataFrame({"adx": wilder(dx, n), "pdi": pdi, "mdi": mdi}, index=df.index)


def swing_points(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """Pivoty potwierdzone po `lookback` świecach.

    Kolumny (wartości tylko na świecy potwierdzenia, reszta NaN):
      sh_confirm - cena swing high, sl_confirm - cena swing low,
      sh_pos / sl_pos - pozycja (int) świecy pivota.
    """
    h, l = df["high"].values, df["low"].values
    n = len(df)
    win = 2 * lookback + 1
    sh = np.full(n, np.nan)
    sl = np.full(n, np.nan)
    shp = np.full(n, np.nan)
    slp = np.full(n, np.nan)
    if n >= win:
        hw = np.lib.stride_tricks.sliding_window_view(h, win)
        lw = np.lib.stride_tricks.sliding_window_view(l, win)
        center_h = h[lookback:n - lookback]
        center_l = l[lookback:n - lookback]
        is_sh = (center_h >= hw.max(axis=1)) & (np.argmax(hw, axis=1) == lookback)
        is_sl = (center_l <= lw.min(axis=1)) & (np.argmin(lw, axis=1) == lookback)
        piv = np.arange(lookback, n - lookback)
        conf = piv + lookback  # świeca, na której pivot jest już znany
        sh[conf[is_sh]] = center_h[is_sh]
        shp[conf[is_sh]] = piv[is_sh]
        sl[conf[is_sl]] = center_l[is_sl]
        slp[conf[is_sl]] = piv[is_sl]
    return pd.DataFrame({"sh_confirm": sh, "sl_confirm": sl, "sh_pos": shp, "sl_pos": slp}, index=df.index)


def market_structure(df: pd.DataFrame, lookback: int = 3) -> pd.DataFrame:
    """Struktura: ostatnie dwa swing high/low, HH/HL/LH/LL i Break of Structure."""
    sp = swing_points(df, lookback)
    last_sh = sp["sh_confirm"].ffill()
    last_sl = sp["sl_confirm"].ffill()
    prev_sh = _prev_value(sp["sh_confirm"])
    prev_sl = _prev_value(sp["sl_confirm"])
    hh = np.sign(last_sh - prev_sh)  # +1 HH, -1 LH
    hl = np.sign(last_sl - prev_sl)  # +1 HL, -1 LL
    close = df["close"]
    bos_up = (close > last_sh).astype(float)
    bos_dn = (close < last_sl).astype(float)
    struct = (hh.fillna(0) + hl.fillna(0)) / 2.0
    struct = (struct + 0.5 * bos_up - 0.5 * bos_dn).clip(-1, 1)
    return pd.DataFrame({
        "last_sh": last_sh, "prev_sh": prev_sh, "last_sl": last_sl, "prev_sl": prev_sl,
        "hh": hh, "hl": hl, "bos_up": bos_up, "bos_dn": bos_dn, "struct": struct,
        "sh_confirm": sp["sh_confirm"], "sl_confirm": sp["sl_confirm"],
    }, index=df.index)


def _prev_value(confirm: pd.Series) -> pd.Series:
    """Dla każdej świecy: przedostatnia potwierdzona wartość pivota."""
    vals = confirm.dropna()
    prev = vals.shift(1)
    return prev.reindex(confirm.index).ffill()


def trend_score(df: pd.DataFrame, ema_periods=(20, 50, 200), adx_n: int = 14, lookback: int = 3) -> pd.DataFrame:
    """Wynik trendu -100..+100 dla jednego interwału + kolumny pomocnicze."""
    close = df["close"]
    e1, e2, e3 = (ema(close, p) for p in ema_periods)
    s_ema = (np.sign(close - e1) + np.sign(e1 - e2) + np.sign(e2 - e3) + np.sign(close - e3)) / 4.0
    # przy niepełnej historii EMA200 - używamy dostępnych średnich
    s_ema_short = (np.sign(close - e1) + np.sign(e1 - e2)) / 2.0
    s_ema = s_ema.where(e3.notna(), s_ema_short)
    ax = adx(df, adx_n)
    s_di = np.sign(ax["pdi"] - ax["mdi"])
    strength = ((ax["adx"] - 15) / 20).clip(0, 1)
    ms = market_structure(df, lookback)
    raw = (0.45 * s_ema.fillna(0) + 0.35 * ms["struct"] + 0.20 * s_di.fillna(0)).clip(-1, 1)
    score = 100 * raw * (0.5 + 0.5 * strength.fillna(0))
    out = pd.DataFrame({
        "ema20": e1, "ema50": e2, "ema200": e3, "adx": ax["adx"], "pdi": ax["pdi"], "mdi": ax["mdi"],
        "s_ema": s_ema, "trend_score": score,
    }, index=df.index)
    return pd.concat([out, ms], axis=1)
