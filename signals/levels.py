"""Wyznaczanie stop lossa i take profitów.

SL (long; short - lustrzanie):
  1. kandydaci strukturalni: swing low 1h/4h/1d poniżej wejścia, minus bufor 0.3 ATR(1h)
  2. wybierany najbliższy, którego odległość mieści się w [min_atr, max_atr] x ATR(1h)
     - najbliższa struktura za blisko -> SL = wejście - min_atr x ATR (poniżej struktury)
     - brak struktury poniżej (nowe minima) -> SL = wejście - 2 x ATR
     - struktura za daleko -> brak transakcji (unieważnienie zbyt odległe)
  3. jeśli w +-0.5 ATR od SL leży klaster likwidacji longów -> SL przesuwany ZA klaster
     (klastry przyciągają cenę - "stop hunt"; SL wewnątrz klastra zostałby zebrany)

TP:
  - przeszkody: swing high 4h/1d, VAH/POC, ściany ask (live)
  - magnesy: klastry likwidacji shortów, swing high 1h, HVN (live)
  - każdy poziom "front-run" o 0.1 ATR (zlecenie przed poziomem)
  - najbliższa przeszkoda < min_rr x R -> brak transakcji (R:R za niskie)
  - TP2 (cel główny = R:R transakcji) = pierwszy poziom z R >= min_rr; brak -> 3R
  - TP1 = pierwszy poziom z 1.2R <= R < R(TP2); brak -> fallback
  - TP3 (runner, trailing) = pierwszy poziom z R >= R(TP2)+1; brak -> 5R (max 8R)
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field

import numpy as np


@dataclass
class TradePlan:
    symbol: str
    side: str
    entry: float
    sl: float
    tps: list[float]
    fractions: list[float]
    r_multiples: list[float]
    rr: float              # R:R celu głównego (TP2) - wymagane >= min_rr
    rr_blended: float      # średnia ważona R wszystkich TP
    atr: float
    invalidation: float | None
    sl_reason: str
    tp_reasons: list[str]
    counter_trend: bool = False
    risk_factor: float = 1.0
    kind: str = "single"
    meta: dict = field(default_factory=dict)

    @property
    def direction(self) -> int:
        return 1 if self.side == "long" else -1

    @property
    def risk_per_unit(self) -> float:
        return abs(self.entry - self.sl)

    def to_dict(self) -> dict:
        return asdict(self)

    def rescaled(self, factor: float) -> "TradePlan":
        """Przeliczenie poziomów procentowo na inną cenę (np. testnet vs mainnet)."""
        d = asdict(self)
        d["entry"] *= factor
        d["sl"] *= factor
        d["tps"] = [t * factor for t in self.tps]
        d["atr"] *= factor
        if self.invalidation is not None:
            d["invalidation"] = self.invalidation * factor
        return TradePlan(**d)


def _f(row: dict, key: str) -> float:
    v = row.get(key)
    try:
        v = float(v)
    except (TypeError, ValueError):
        return np.nan
    return v if np.isfinite(v) else np.nan


def plan_levels(symbol: str, side: str, entry: float, row: dict, cfg, kind: str = "single",
                extra_levels: dict | None = None) -> tuple[TradePlan | None, str]:
    ex = cfg.get("exits", {})
    slc, tpc = ex.get("sl", {}), ex.get("tp", {})
    d = 1 if side == "long" else -1
    atr = _f(row, "atr")
    if not np.isfinite(atr) or atr <= 0 or not np.isfinite(entry):
        return None, "brak ATR/ceny"
    buf = slc.get("structure_buffer_atr", 0.3) * atr
    min_d, max_d = slc.get("min_atr", 1.0) * atr, slc.get("max_atr", 4.0) * atr
    extra_levels = extra_levels or {}

    # ------------------------------------------------------------- STOP LOSS
    lvl = "sl" if d == 1 else "sh"
    struct_keys = [f"h1_last_{lvl}", f"h1_prev_{lvl}", f"h4_last_{lvl}", f"h4_prev_{lvl}", f"d1_last_{lvl}"]
    struct = sorted({_f(row, k) for k in struct_keys if np.isfinite(_f(row, k)) and d * (entry - _f(row, k)) > 0},
                    key=lambda x: d * (entry - x))
    sl, inval, sl_reason = np.nan, None, ""
    for s in struct:
        cand = s - d * buf
        dist = d * (entry - cand)
        if min_d <= dist <= max_d:
            sl, inval, sl_reason = cand, s, "struktura"
            break
    if not np.isfinite(sl):
        if struct and d * (entry - (struct[0] - d * buf)) < min_d:
            sl, inval, sl_reason = entry - d * min_d, struct[0], "min ATR (struktura zbyt blisko)"
        elif not struct:
            sl, inval, sl_reason = entry - d * 2.0 * atr, None, "2xATR (brak struktury)"
        else:
            return None, f"struktura zbyt daleko (>{slc.get('max_atr', 4.0)} ATR)"

    # unikanie klastrów likwidacji
    liq_side = "dn" if d == 1 else "up"
    if kind == "single":
        clusters = [_f(row, f"liq_{liq_side}{i}") for i in (1, 2, 3)]
        clusters += list(extra_levels.get(f"liq_{liq_side}", []))
        avoid = slc.get("liq_avoid_atr", 0.5) * atr
        for _ in range(3):
            moved = False
            for c in clusters:
                if np.isfinite(c) and abs(c - sl) <= avoid and d * (entry - c) > 0:
                    sl = c - d * buf
                    sl_reason += " + za klastrem likwidacji"
                    moved = True
            if not moved:
                break
    risk = d * (entry - sl)
    if risk > max_d * 1.25:
        return None, "SL za klastrem likwidacji zbyt daleko"
    if risk <= 0:
        return None, "nieprawidłowy SL"

    # ------------------------------------------------------------ TAKE PROFIT
    tgt = "sh" if d == 1 else "sl"
    front = 0.1 * atr
    obstacles, magnets = [], []
    for k in (f"h4_last_{tgt}", f"h4_prev_{tgt}", f"d1_last_{tgt}", f"d1_prev_{tgt}"):
        obstacles.append((_f(row, k), k))
    for k in ("vah", "poc", "val"):
        obstacles.append((_f(row, k), f"VP {k.upper()}"))
    for p in extra_levels.get("walls_ask" if d == 1 else "walls_bid", []):
        obstacles.append((p, "ściana order book"))
    for k in (f"h1_last_{tgt}", f"h1_prev_{tgt}"):
        magnets.append((_f(row, k), k))
    if kind == "single":
        opp = "up" if d == 1 else "dn"
        for i in (1, 2, 3):
            magnets.append((_f(row, f"liq_{opp}{i}"), "klaster likwidacji"))
        for p in extra_levels.get(f"liq_{opp}", []):
            magnets.append((p, "klaster likwidacji (Coinglass/ws)"))
    for p in extra_levels.get("hvn", []):
        magnets.append((p, "HVN"))

    def prep(levels):
        out = []
        for p, why in levels:
            if np.isfinite(p) and d * (p - entry) > front:
                t = p - d * front
                out.append((t, d * (t - entry) / risk, why))
        return sorted(out, key=lambda x: x[1])

    obs = prep(obstacles)
    allv = _merge(prep(obstacles + magnets), entry, tpc.get("level_merge_pct", 0.15))
    min_rr = float(tpc.get("min_rr", 2.0))
    max_r = float(tpc.get("max_r", 8.0))
    fb = tpc.get("fallback_atr_r", [1.5, 3.0, 5.0])
    if obs and obs[0][1] < min_rr:
        return None, f"R:R za niskie: przeszkoda ({obs[0][2]}) na {obs[0][1]:.2f}R < {min_rr}R"
    tp2 = next(((p, r, w) for p, r, w in allv if r >= min_rr), None)
    if tp2 is None or tp2[1] > max_r:
        tp2 = (entry + d * fb[1] * risk, float(fb[1]), "fallback 3R (brak poziomów)")
    r2 = tp2[1]
    tp1_min = float(tpc.get("tp1_min_r", 1.2))
    tp1 = next(((p, r, w) for p, r, w in allv if tp1_min <= r < r2 - 0.3), None)
    if tp1 is None:
        r1 = max(tp1_min, min(fb[0], 0.6 * r2))
        tp1 = (entry + d * r1 * risk, r1, "fallback R")
    tp3 = next(((p, r, w) for p, r, w in allv if r2 + 1.0 <= r <= max_r), None)
    if tp3 is None:
        r3 = min(max_r, max(float(fb[2]), r2 + 2.0))
        tp3 = (entry + d * r3 * risk, r3, "fallback R (runner)")
    fr = list(tpc.get("fractions", [0.35, 0.35, 0.30]))
    rs = [tp1[1], tp2[1], tp3[1]]
    blended = float(np.dot(fr, rs))
    if r2 < min_rr or blended < min_rr:
        return None, f"R:R {r2:.2f} < {min_rr}"
    return TradePlan(symbol=symbol, side=side, entry=float(entry), sl=float(sl),
                     tps=[float(tp1[0]), float(tp2[0]), float(tp3[0])], fractions=fr,
                     r_multiples=[round(x, 3) for x in rs], rr=round(r2, 3), rr_blended=round(blended, 3),
                     atr=float(atr), invalidation=float(inval) if inval is not None else None,
                     sl_reason=sl_reason, tp_reasons=[tp1[2], tp2[2], tp3[2]], kind=kind), "ok"


def _merge(levels: list[tuple[float, float, str]], entry: float, merge_pct: float):
    """Łączy poziomy bliższe niż merge_pct % (zostaje bliższy wejściu)."""
    out: list[tuple[float, float, str]] = []
    for p, r, w in levels:
        if out and abs(p / out[-1][0] - 1) * 100 < merge_pct:
            out[-1] = (out[-1][0], out[-1][1], out[-1][2] + " + " + w)
            continue
        out.append((p, r, w))
    return out
