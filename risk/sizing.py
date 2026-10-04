"""Wielkość pozycji i dźwignia.

Wielkość = (kapitał x ryzyko%) / strata na jednostkę, gdzie strata na jednostkę
uwzględnia odległość do SL ORAZ prowizje taker i poślizg na wejściu i na SL:
    loss_per_unit = |entry - SL| + entry*(fee+slip) + SL*(fee+slip)
Ilość jest zaokrąglana W DÓŁ do kroku kontraktu, więc realne ryzyko <= budżet.

Dźwignia (margin isolated): odległość do ceny likwidacji ~ 1/L - MMR.
Wymagamy  1/L - MMR >= safety x odległość_SL  ->  L <= 1 / (safety*sl% + MMR).
Dzięki temu likwidacja leży zawsze daleko za stop lossem.
"""
from __future__ import annotations

import math
from dataclasses import dataclass

from core.utils import round_down


@dataclass
class SizeResult:
    qty: float
    risk_amount: float       # realne ryzyko po zaokrągleniu (z prowizjami i poślizgiem)
    budget: float            # budżet ryzyka
    loss_per_unit: float
    notional: float
    ok: bool
    reason: str = ""


def loss_per_unit(entry: float, sl: float, taker_fee: float, slippage: float) -> float:
    return abs(entry - sl) + entry * (taker_fee + slippage) + sl * (taker_fee + slippage)


def position_size(equity: float, entry: float, sl: float, risk_pct: float, taker_fee: float, slippage: float,
                  qty_step: float = 0.001, min_qty: float = 0.001, max_qty: float | None = None,
                  min_notional: float = 5.0, budget: float | None = None) -> SizeResult:
    if equity <= 0 or entry <= 0 or sl <= 0:
        return SizeResult(0, 0, 0, 0, 0, False, "nieprawidłowe dane wejściowe")
    if risk_pct > 0.01 + 1e-12:
        raise ValueError("ryzyko na pozycję > 1% - zasada nienaruszalna")
    if entry == sl:
        return SizeResult(0, 0, 0, 0, 0, False, "SL równy cenie wejścia")
    budget = equity * risk_pct if budget is None else min(budget, equity * risk_pct)
    lpu = loss_per_unit(entry, sl, taker_fee, slippage)
    qty = round_down(budget / lpu, qty_step)
    if max_qty is not None:
        qty = min(qty, round_down(max_qty, qty_step))
    if qty < min_qty:
        return SizeResult(0, 0, budget, lpu, 0, False, f"ilość {budget / lpu:.6f} < min {min_qty}")
    if qty * entry < min_notional:
        return SizeResult(0, 0, budget, lpu, 0, False, f"wartość {qty * entry:.2f} < min {min_notional} USDT")
    return SizeResult(qty, qty * lpu, budget, lpu, qty * entry, True)


@dataclass
class PairSize:
    qty_long: float
    qty_short: float
    notional: float
    risk_amount: float
    budget: float
    ok: bool
    reason: str = ""


def pair_size(equity: float, ratio_entry: float, ratio_sl: float, risk_pct: float, price_long: float,
              price_short: float, taker_fee: float, slippage: float, step_long: float, step_short: float,
              min_long: float, min_short: float, budget: float | None = None) -> PairSize:
    """Dwie nogi o równej wartości N. Strata przy SL na ratio ~ N*|dR|/R + 4 egzekucje x (fee+slip)."""
    if risk_pct > 0.01 + 1e-12:
        raise ValueError("ryzyko na pozycję > 1% - zasada nienaruszalna")
    budget = equity * risk_pct if budget is None else min(budget, equity * risk_pct)
    d_r = abs(ratio_entry - ratio_sl) / ratio_entry
    per_notional = d_r + 4 * (taker_fee + slippage)
    if per_notional <= 0:
        return PairSize(0, 0, 0, 0, budget, False, "nieprawidłowy SL")
    notional = budget / per_notional
    ql = round_down(notional / price_long, step_long)
    qs = round_down(notional / price_short, step_short)
    if ql < min_long or qs < min_short:
        return PairSize(0, 0, 0, 0, budget, False, "noga poniżej minimalnej ilości")
    n_eff = max(ql * price_long, qs * price_short)
    return PairSize(ql, qs, n_eff, n_eff * per_notional, budget, True)


@dataclass
class LeverageResult:
    leverage: float
    liq_price: float
    liq_distance: float
    sl_distance: float
    ok: bool
    reason: str = ""


def choose_leverage(entry: float, sl: float, side: str, mmr: float = 0.005, max_lev: float = 10,
                    min_lev: float = 1, safety: float = 2.5, instrument_max: float = 100,
                    lev_step: float = 0.01) -> LeverageResult:
    sl_pct = abs(entry - sl) / entry
    raw = 1.0 / (safety * sl_pct + mmr)
    lev = min(raw, max_lev, instrument_max)
    lev = math.floor(lev / lev_step) * lev_step if lev_step > 0 else lev
    lev = max(min_lev, round(lev, 2))
    liq = isolated_liq_price(entry, lev, side, mmr)
    liq_dist = abs(entry - liq) / entry
    ok = liq_dist >= safety * sl_pct * 0.999 and ((side == "long" and liq < sl) or (side == "short" and liq > sl))
    reason = "" if ok else f"likwidacja ({liq:.4f}) zbyt blisko SL ({sl:.4f}) nawet przy dźwigni {lev}"
    return LeverageResult(lev, liq, liq_dist, sl_pct, ok, reason)


def isolated_liq_price(entry: float, leverage: float, side: str, mmr: float = 0.005) -> float:
    if side == "long":
        return entry * (1 - 1 / leverage + mmr)
    return entry * (1 + 1 / leverage - mmr)


def pair_hard_stops(direction: int, ratio_entry: float, ratio_sl: float, price_long: float, price_short: float,
                    atr4h_long: float | None, atr4h_short: float | None, mult: float = 4.0,
                    atr_mult: float = 3.0) -> tuple[float, float]:
    """Awaryjne (twarde) SL nóg pary, ustawiane na giełdzie razem z otwarciem.

    direction=+1: long BTC (noga long) + short ETH (noga short). Zwraca (sl_nogi_long, sl_nogi_short)
    w kolejności (noga kupowana, noga sprzedawana) dla danego kierunku ratio.
    Odległość = max(mult x dystans SL ratio, atr_mult x ATR4h nogi) - poza zasięgiem
    normalnych wspólnych ruchów BTC/ETH; właściwy stop pary to SL na ratio pilnowany przez bota.
    """
    d_r = abs(ratio_entry - ratio_sl) / ratio_entry
    a_l = (atr4h_long / price_long) if atr4h_long and atr4h_long > 0 else 0.02
    a_s = (atr4h_short / price_short) if atr4h_short and atr4h_short > 0 else 0.02
    dist_l = max(mult * d_r, atr_mult * a_l)
    dist_s = max(mult * d_r, atr_mult * a_s)
    return price_long * (1 - dist_l), price_short * (1 + dist_s)
