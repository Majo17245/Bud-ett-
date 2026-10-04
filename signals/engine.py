"""Silnik decyzji: reguły wejścia, filtry "nie handluj", warunki wcześniejszego wyjścia.

Ta sama funkcja `evaluate_entry` jest używana przez backtest i bota live.
Każda decyzja zawiera komplet sprawdzonych warunków i wartości wskaźników
(logowane do logs/decisions.jsonl).

REGUŁY WEJŚCIA (long; short lustrzanie), oceniane na zamknięciu świecy 1h:
  1. |score| >= entry.threshold (30) i kierunek = znak score
  2. 1d (reżim): trend 1d > -20 (nie bessa). Przy bessie (pozycja przeciw trendowi 1d)
     wymagany score >= strong_threshold (55) i ryzyko x0.5
  3. 4h (struktura): trend 4h >= structure_min (0)
  4. 1h (timing): close > EMA20(1h) i histogram MACD(1h) rośnie
  5. zgodność: >= 3 moduły zgodne (|s| >= 10), <= 1 moduł silnie przeciwny (|s| >= 50)
  6. brak konfliktu: nie (trend 1h i 4h przeciwne i oba |s| >= 30)
  7. plan SL/TP z R:R >= min_rr (2.0)
FILTRY: dane makro USA (okno -60/+45 min), skrajna zmienność (ATR% > 95 percentyl
lub świeca > 3 ATR), niska płynność (RVOL < 0.35; live: spread > 5 bps, głębokość
+-1% < 2 mln USD), cooldown 3h po wyjściu z instrumentu.
"""
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime

import numpy as np

from signals.levels import TradePlan, plan_levels
from signals.scoring import MODULES, agreement

LOG_FIELDS = [
    "close", "atr", "h1_ema20", "h1_ema50", "h1_ema200", "h1_adx", "h1_rsi", "h1_macd_hist", "h1_divergence",
    "h1_struct", "h4_struct", "d1_struct", "h4_adx", "d1_adx", "h4_rsi", "d1_ema50", "d1_ema200",
    "atr_pct", "h1_atr_pct_rank", "h1_bar_range_atr", "cvd_norm", "rvol", "poc", "vah", "val",
    "oi_chg", "funding", "ls_ratio", "ls_z", "liq_above", "liq_below", "liq_up1", "liq_dn1",
    "corr_spx", "corr_gold", "risk_regime", "fng", "h1_last_sl", "h1_last_sh", "h4_last_sl", "h4_last_sh",
]


@dataclass
class Decision:
    symbol: str
    ts: str
    action: str                 # long / short / none
    score: float
    modules: dict
    checks: dict = field(default_factory=dict)
    reasons: list = field(default_factory=list)
    plan: TradePlan | None = None
    indicators: dict = field(default_factory=dict)
    warnings: list = field(default_factory=list)

    def to_record(self) -> dict:
        return {
            "type": "decision", "symbol": self.symbol, "ts": self.ts, "action": self.action,
            "score": self.score, "modules": self.modules, "checks": self.checks, "reasons": self.reasons,
            "warnings": self.warnings, "plan": self.plan.to_dict() if self.plan else None,
            "indicators": self.indicators,
        }


def _num(x) -> float:
    try:
        x = float(x)
    except (TypeError, ValueError):
        return float("nan")
    return x


def evaluate_entry(symbol: str, row: dict, srow: dict, cfg, kind: str = "single", ts: str | datetime = "",
                   live: dict | None = None, bars_since_exit: int | None = None,
                   extra_levels: dict | None = None, entry_price: float | None = None) -> Decision:
    """row: cechy (słownik), srow: wyniki modułów; live: dane tylko z trybu live."""
    en, flt = cfg.get("entry", {}), cfg.get("filters", {})
    live = live or {}
    score = _num(srow.get("composite"))
    modules = {m: _round(srow.get(m)) for m in MODULES}
    modules.update({k: _round(srow.get(k)) for k in ("trend_1h", "trend_4h", "trend_1d")})
    dec = Decision(symbol=symbol, ts=str(ts), action="none", score=_round(score), modules=modules,
                   indicators={k: _round(row.get(k)) for k in LOG_FIELDS if k in row})
    checks = dec.checks
    close = _num(row.get("close"))
    entry = entry_price if entry_price is not None else close

    def fail(name: str, msg: str, value=None) -> Decision:
        checks[name] = {"ok": False, "value": value}
        dec.reasons.append(msg)
        return dec

    def ok(name: str, value=None) -> None:
        checks[name] = {"ok": True, "value": value}

    if not np.isfinite(score) or not np.isfinite(close) or not np.isfinite(_num(row.get("atr"))):
        return fail("data", "niepełne dane (rozgrzewka wskaźników)")
    ok("data")

    # ----------------------------------------------------- filtry "nie handluj"
    if live.get("macro_event"):
        return fail("macro_event", f"ważne dane makro USA: {live['macro_event']}", live["macro_event"])
    ok("macro_event")
    rank = _num(row.get("h1_atr_pct_rank"))
    bar_rng = _num(row.get("h1_bar_range_atr"))
    if (np.isfinite(rank) and rank > flt.get("max_atr_percentile", 0.95)) or \
            (np.isfinite(bar_rng) and bar_rng > flt.get("max_bar_range_atr", 3.0)):
        return fail("volatility", f"skrajna zmienność (ATR pct={rank:.2f}, świeca={bar_rng:.1f} ATR)",
                    {"atr_rank": rank, "bar_range_atr": bar_rng})
    ok("volatility", {"atr_rank": _round(rank), "bar_range_atr": _round(bar_rng)})
    rvol = _num(row.get("rvol"))
    if np.isfinite(rvol) and rvol < flt.get("min_rvol", 0.35):
        return fail("liquidity", f"niska płynność (RVOL={rvol:.2f})", rvol)
    if live.get("spread_bps") is not None and live["spread_bps"] > flt.get("max_spread_bps", 5):
        return fail("liquidity", f"szeroki spread {live['spread_bps']:.1f} bps", live["spread_bps"])
    if live.get("depth_usd_1pct") is not None and kind == "single" and \
            live["depth_usd_1pct"] < flt.get("min_depth_usd_1pct", 2e6):
        return fail("liquidity", f"płytki order book (+-1%: {live['depth_usd_1pct'] / 1e6:.2f} mln USD)",
                    live["depth_usd_1pct"])
    ok("liquidity", _round(rvol))
    if bars_since_exit is not None and bars_since_exit < en.get("cooldown_bars", 3):
        return fail("cooldown", f"cooldown po wyjściu ({bars_since_exit}h)", bars_since_exit)

    # ----------------------------------------------------------- reguły wejścia
    thr = en.get("threshold", 30)
    if abs(score) < thr:
        return fail("threshold", f"|score| {score:.1f} < próg {thr}", score)
    d = 1 if score > 0 else -1
    side = "long" if d == 1 else "short"
    ok("threshold", _round(score))

    t1d = _num(srow.get("trend_1d"))
    regime_thr = en.get("regime_threshold", 20)
    counter = np.isfinite(t1d) and d * t1d < -regime_thr
    risk_factor = 1.0
    if counter:
        strong = en.get("strong_threshold", 55)
        if abs(score) < strong:
            return fail("regime_1d", f"{side} przeciw trendowi 1d ({t1d:.0f}) wymaga |score| >= {strong}",
                        _round(t1d))
        risk_factor = float(en.get("counter_trend_risk_factor", 0.5))
        dec.warnings.append("pozycja przeciw trendowi 1d - połowa ryzyka")
    ok("regime_1d", _round(t1d))

    t4h = _num(srow.get("trend_4h"))
    if np.isfinite(t4h) and d * t4h < en.get("structure_min", 0):
        return fail("structure_4h", f"struktura 4h niezgodna ({t4h:.0f})", _round(t4h))
    ok("structure_4h", _round(t4h))

    t1h = _num(srow.get("trend_1h"))
    if np.isfinite(t1h) and np.isfinite(t4h) and t1h * t4h < 0 and abs(t1h) >= 30 and abs(t4h) >= 30:
        return fail("conflict", f"sprzeczne sygnały 1h ({t1h:.0f}) vs 4h ({t4h:.0f})")
    n_agree, n_opp, opp_names = agreement(srow, d)
    if n_agree < en.get("min_agreeing_modules", 3):
        return fail("conflict", f"za mało zgodnych modułów ({n_agree})", n_agree)
    if n_opp > en.get("max_strong_opposing", 1):
        return fail("conflict", f"silnie przeciwne moduły: {opp_names}", opp_names)
    ok("conflict", {"agree": n_agree, "opposing": opp_names})

    if en.get("require_1h_trigger", True):
        ema20 = _num(row.get("h1_ema20"))
        slope = _num(row.get("h1_macd_slope"))
        if not (np.isfinite(ema20) and d * (close - ema20) > 0 and np.isfinite(slope) and d * slope > 0):
            return fail("trigger_1h", "brak triggera 1h (close vs EMA20 / histogram MACD)",
                        {"close": close, "ema20": _round(ema20), "macd_slope": slope})
    ok("trigger_1h")

    sent = cfg.get_path("indicators.sentiment", {})
    fng = _num(row.get("fng"))
    if np.isfinite(fng):
        if fng > sent.get("extreme_greed", 80) and d == 1:
            dec.warnings.append(f"skrajna chciwość F&G={fng:.0f} - ostrożnie z longami")
        if fng < sent.get("extreme_fear", 20) and d == -1:
            dec.warnings.append(f"skrajny strach F&G={fng:.0f} - ostrożnie z shortami")
    if live.get("volume_suspicious"):
        dec.warnings.append("skok wolumenu niepotwierdzony na innych giełdach - obniżona waga RVOL")

    plan, why = plan_levels(symbol, side, entry, row, cfg, kind=kind, extra_levels=extra_levels)
    if plan is None:
        return fail("levels", why)
    plan.counter_trend = bool(counter)
    plan.risk_factor = risk_factor
    ok("levels", {"rr": plan.rr, "rr_blended": plan.rr_blended})
    dec.plan = plan
    dec.action = side
    dec.reasons.append(f"{side.upper()} score={score:.1f}, R:R={plan.rr:.2f} (blended {plan.rr_blended:.2f}), "
                       f"SL: {plan.sl_reason}, TP: {plan.tp_reasons}")
    return dec


def check_exit(side: str, row: dict, srow: dict, cfg, bars_open: int, max_fav_r: float,
               invalidation: float | None) -> str | None:
    """Wcześniejsze wyjście, gdy scenariusz się unieważnił. Zwraca powód lub None."""
    inv = cfg.get_path("exits.invalidation", {})
    d = 1 if side == "long" else -1
    score = _num(srow.get("composite"))
    if np.isfinite(score) and d * score <= inv.get("score_flip", -15):
        return f"odwrócenie scoringu ({score:.1f})"
    t4h = _num(srow.get("trend_4h"))
    if np.isfinite(t4h) and d * t4h <= inv.get("structure_4h_flip", -35):
        return f"struktura 4h odwrócona ({t4h:.0f})"
    close = _num(row.get("close"))
    if inv.get("close_beyond_structure", True) and invalidation is not None and np.isfinite(close):
        if d * (close - invalidation) < 0:
            return f"zamknięcie 1h za poziomem unieważnienia {invalidation:.4f}"
    if bars_open >= inv.get("time_stop_bars", 72) and max_fav_r < inv.get("time_stop_min_r", 0.5):
        return f"time stop ({bars_open}h bez +{inv.get('time_stop_min_r', 0.5)}R)"
    return None


def _round(x, nd: int = 4):
    try:
        x = float(x)
    except (TypeError, ValueError):
        return None
    if not np.isfinite(x):
        return None
    return round(x, nd)
