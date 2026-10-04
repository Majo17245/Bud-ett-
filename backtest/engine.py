"""Backtest zdarzeniowy na świecach 1h z kontekstem 4h/1d - ten sam silnik decyzji co live.

Model egzekucji (konserwatywny):
  - decyzja na zamknięciu świecy 1h, wejście na otwarciu następnej (+ poślizg, prowizja taker),
    wielkość liczona od faktycznej ceny wejścia; R:R sprawdzane ponownie po cenie wejścia
  - SL: jeśli w jednej świecy osiągnięte SL i TP -> zakładamy najpierw SL; luka cenowa za SL
    -> wypełnienie po cenie otwarcia; wyjście taker + poślizg
  - TP1/TP2: zlecenia limit reduce-only (maker, bez poślizgu); TP3 (takeProfit giełdy) - taker
  - po TP1 SL -> break-even (+bufor) od następnej świecy; po TP2 trailing stop (odległość 3 ATR)
  - funding co 8h (00/08/16 UTC) od wartości pozycji
  - wcześniejsze wyjście (unieważnienie scenariusza) na zamknięciu świecy (taker + poślizg)
  - para BTC/ETH: stop/TP na ratio sprawdzane na zamknięciu świecy (zarządzane przez bota),
    twarde SL nóg sprawdzane intrabar
"""
from __future__ import annotations

import logging
from dataclasses import dataclass, field

import numpy as np
import pandas as pd

from risk.manager import OpenRisk, RiskManager
from risk.sizing import choose_leverage, loss_per_unit, pair_hard_stops, pair_size, position_size
from signals.engine import check_exit, evaluate_entry
from signals.features import build_features, build_pair_features
from signals.scoring import module_scores

log = logging.getLogger(__name__)
PAIR_KEY = "BTC/ETH"
DEFAULT_SPECS = {"BTCUSDT": {"qty_step": 0.001, "min_qty": 0.001, "mmr": 0.005, "max_lev": 100},
                 "ETHUSDT": {"qty_step": 0.01, "min_qty": 0.01, "mmr": 0.005, "max_lev": 100}}


@dataclass
class Leg:
    symbol: str
    direction: int
    qty: float
    entry: float
    hard_sl: float | None = None
    open: bool = True


@dataclass
class Position:
    key: str
    kind: str
    side: str
    direction: int
    entry_time: pd.Timestamp
    entry: float
    sl: float
    sl_initial: float
    tps: list
    fractions: list
    qty0: float
    qty: float
    risk_amount: float
    plan_rr: float
    plan_rr_blended: float
    atr: float
    invalidation: float | None
    score: float
    counter_trend: bool
    leverage: float = 1.0
    legs: list = field(default_factory=list)       # para: [Leg BTC, Leg ETH]
    tp_hit: list = field(default_factory=lambda: [False, False, False])
    trailing: bool = False
    trail_dist: float = 0.0
    watermark: float = 0.0
    bars: int = 0
    max_fav_r: float = 0.0
    realized: float = 0.0
    fees: float = 0.0
    funding: float = 0.0
    exits: list = field(default_factory=list)
    be_pending: bool = False

    @property
    def remaining_frac(self) -> float:
        return self.qty / self.qty0 if self.qty0 else 0.0


class Backtester:
    def __init__(self, cfg, dataset: dict, include_pair: bool | None = None, use_funding: bool | None = None,
                 specs: dict | None = None, vp_step: int = 1):
        self.cfg = cfg
        self.ds = dataset
        bt = cfg.get("backtest", {})
        self.symbols = [s for s in bt.get("symbols", ["BTCUSDT", "ETHUSDT"]) if s in dataset["symbols"]]
        self.include_pair = bt.get("include_pair", True) if include_pair is None else include_pair
        self.include_pair = self.include_pair and {"BTCUSDT", "ETHUSDT"} <= set(self.symbols) \
            and cfg.get_path("instruments.pair.enabled", True)
        self.use_funding = bt.get("use_funding", True) if use_funding is None else use_funding
        self.specs = specs or DEFAULT_SPECS
        self.vp_step = vp_step
        self.F: dict[str, pd.DataFrame] = {}
        self.S: dict[str, pd.DataFrame] = {}
        self._prepared = False

    # ------------------------------------------------------------ preparation
    def prepare(self) -> None:
        if self._prepared:
            return
        macro, fng = self.ds.get("macro", {}), self.ds.get("fng")
        for sym in self.symbols:
            log.info("Cechy %s ...", sym)
            self.F[sym] = build_features(self.ds["symbols"][sym], self.cfg, macro, fng, vp_step=self.vp_step)
        if self.include_pair:
            log.info("Cechy %s ...", PAIR_KEY)
            fp = build_pair_features(self.ds["symbols"]["BTCUSDT"], self.ds["symbols"]["ETHUSDT"],
                                     self.F["BTCUSDT"], self.F["ETHUSDT"], self.cfg, vp_step=self.vp_step)
            for c in [c for c in fp.columns if c.startswith("liq_")]:
                fp[c] = np.nan
            self.F[PAIR_KEY] = fp
        self.rescore(self.cfg)
        idx = None
        for f in self.F.values():
            idx = f.index if idx is None else idx.intersection(f.index)
        self.timeline = idx.sort_values()
        self.rows = {k: f.reindex(self.timeline).to_dict("records") for k, f in self.F.items()}
        if {"BTCUSDT", "ETHUSDT"} <= set(self.F):
            rb = np.log(self.F["BTCUSDT"]["close"]).diff()
            re = np.log(self.F["ETHUSDT"]["close"]).diff()
            win = int(self.cfg.get_path("risk.correlation_window", 720))
            self.corr = rb.rolling(win, min_periods=100).corr(re).reindex(self.timeline).fillna(0.85).values
        else:
            self.corr = np.full(len(self.timeline), 0.85)
        self.funding = {}
        for sym in self.symbols:
            fd = self.ds["symbols"][sym].get("funding")
            if fd is not None and len(fd):
                s = fd["funding_rate"].copy()
                s.index = pd.DatetimeIndex(s.index).as_unit("ns")
                self.funding[sym] = s[~s.index.duplicated()].to_dict()
        self._prepared = True

    def rescore(self, cfg) -> None:
        self.S = {k: module_scores(f, cfg, kind="pair" if k == PAIR_KEY else "single") for k, f in self.F.items()}
        if self._prepared:
            self.srows = {k: s.reindex(self.timeline).to_dict("records") for k, s in self.S.items()}

    # ------------------------------------------------------------------- run
    def run(self, cfg=None, start: pd.Timestamp | None = None, end: pd.Timestamp | None = None,
            schedule: list[tuple[pd.Timestamp, pd.Timestamp, object]] | None = None,
            initial_capital: float | None = None) -> dict:
        """schedule: lista (od, do, cfg) - parametry wejścia zmienne w czasie (walk-forward OOS)."""
        self.prepare()
        cfg = cfg or self.cfg
        if not hasattr(self, "srows"):
            self.srows = {k: s.reindex(self.timeline).to_dict("records") for k, s in self.S.items()}
        tl = self.timeline
        warm = int(cfg.get_path("backtest.warmup_bars", 300))
        i0 = max(warm, int(tl.searchsorted(start)) if start is not None else 0)
        i1 = int(tl.searchsorted(end)) if end is not None else len(tl)
        capital = float(initial_capital or cfg.get_path("backtest.initial_capital", 10_000))
        rm = RiskManager(cfg)
        rcfg = cfg.get("risk", {})
        taker, maker = rcfg["fees"]["taker"], rcfg["fees"]["maker"]
        slip = rcfg["slippage"]
        cash = capital
        positions: dict[str, Position] = {}
        pending: dict[str, tuple] = {}
        last_exit: dict[str, int] = {}
        trades: list[dict] = []
        equity_curve = []
        decisions_count = {"signals": 0, "rejected_risk": 0, "rejected_rr_fill": 0, "risk_reasons": {}}
        keys = list(self.rows)

        def price(sym: str, i: int, col: str) -> float:
            return self.rows[sym][i][col]

        for i in range(i0, i1):
            ts = tl[i]
            cfg_i = cfg
            if schedule:
                for a, b, c in schedule:
                    if a <= ts < b:
                        cfg_i = c
                        break
                else:
                    cfg_i = None  # poza harmonogramem - brak nowych wejść

            # ---------------------------------------------- 1) wejścia oczekujące
            for key, (plan, budget, dec_i) in list(pending.items()):
                del pending[key]
                eq_now = equity_curve[-1][1] if equity_curve else cash
                pos = self._open(key, plan, budget, i, ts, taker, slip, eq_now, cfg)
                if pos is None:
                    decisions_count["rejected_rr_fill"] += 1
                    continue
                positions[key] = pos

            # ---------------------------------------------- 2) zarządzanie pozycjami
            for key, pos in list(positions.items()):
                pos.bars += 1
                if pos.kind == "single":
                    closed = self._process_single(pos, self.rows[key][i], taker, maker, slip)
                else:
                    closed = self._process_pair(pos, i, taker, slip)
                if not closed and self.use_funding and ts.hour % 8 == 0:
                    self._apply_funding(pos, ts, i)
                if not closed:
                    srow = self.srows[key][i]
                    reason = check_exit(pos.side, self.rows[key][i], srow, cfg, pos.bars, pos.max_fav_r,
                                        pos.invalidation)
                    if reason:
                        self._close_all(pos, i, "early_exit: " + reason, taker, slip)
                        closed = True
                if closed:
                    trades.append(self._trade_record(pos, ts))
                    cash += self._net_pnl(pos)
                    del positions[key]
                    last_exit[key] = i
            equity = cash + sum(self._unrealized(p, i) for p in positions.values())
            rm.update_equity(equity, ts.to_pydatetime())
            equity_curve.append((ts, equity, cash, len(positions)))

            # ---------------------------------------------- 3) nowe sygnały
            if cfg_i is None or i >= i1 - 1:
                continue
            for key in keys:
                if key in positions or key in pending:
                    continue
                kind = "pair" if key == PAIR_KEY else "single"
                bse = i - last_exit[key] if key in last_exit else None
                dec = evaluate_entry(key, self.rows[key][i], self.srows[key][i], cfg_i, kind=kind, ts=ts,
                                     bars_since_exit=bse)
                if dec.action == "none":
                    continue
                decisions_count["signals"] += 1
                assets = ({"BTCUSDT": dec.plan.direction, "ETHUSDT": -dec.plan.direction} if kind == "pair"
                          else {key: dec.plan.direction})
                open_r = [self._open_risk(p) for p in positions.values()]
                open_r += [OpenRisk(k, "pair" if k == PAIR_KEY else "single", v[0].direction, v[1],
                                    {"BTCUSDT": 1, "ETHUSDT": -1} if k == PAIR_KEY else {k: v[0].direction})
                           for k, v in pending.items()]
                rd = rm.evaluate_new(equity, key, kind, dec.plan.direction, assets, open_r,
                                     risk_factor=dec.plan.risk_factor, correlation=float(self.corr[i]))
                if not rd.allowed:
                    decisions_count["rejected_risk"] += 1
                    why = rd.reason.split("(")[0].strip()
                    decisions_count["risk_reasons"][why] = decisions_count["risk_reasons"].get(why, 0) + 1
                    continue
                pending[key] = (dec.plan, rd.risk_budget, i)
                dec.plan.meta["score"] = dec.score

        # zamknięcie pozostałych pozycji na końcu
        last = i1 - 1
        for key, pos in list(positions.items()):
            self._close_all(pos, last, "koniec backtestu", taker, slip)
            trades.append(self._trade_record(pos, tl[last]))
            cash += self._net_pnl(pos)
            del positions[key]
        if equity_curve:
            equity_curve[-1] = (equity_curve[-1][0], cash, cash, 0)
        eq = pd.DataFrame(equity_curve, columns=["ts", "equity", "cash", "positions"]).set_index("ts")
        tr = pd.DataFrame(trades)
        return {"trades": tr, "equity": eq, "initial_capital": capital, "counts": decisions_count,
                "start": tl[i0] if i0 < len(tl) else None, "end": tl[i1 - 1] if i1 > 0 else None}

    # ------------------------------------------------------------- helpers
    def _spec(self, sym: str) -> dict:
        return self.specs.get(sym, {"qty_step": 0.001, "min_qty": 0.001, "mmr": 0.005, "max_lev": 50})

    def _open(self, key, plan, budget, i, ts, taker, slip, equity, cfg) -> Position | None:
        d = plan.direction
        tpc = cfg.get_path("exits.tp", {})
        lev_cfg = cfg.get_path("risk.leverage", {})
        if plan.kind == "single":
            o = self.rows[key][i]["open"]
            fill = o * (1 + d * slip)
            if d * (fill - plan.sl) <= 0:
                return None
            r2 = d * (plan.tps[1] - fill) / (d * (fill - plan.sl))
            if r2 < float(tpc.get("min_rr", 2.0)):
                return None
            sp = self._spec(key)
            size = position_size(max(equity, 0), fill, plan.sl, 0.01, taker, slip, sp["qty_step"], sp["min_qty"],
                                 budget=budget)
            if not size.ok:
                return None
            lev = choose_leverage(fill, plan.sl, plan.side, sp["mmr"], lev_cfg.get("max", 10), lev_cfg.get("min", 1),
                                  lev_cfg.get("liq_safety_factor", 2.5), sp["max_lev"])
            if not lev.ok:
                return None
            fee = size.qty * fill * taker
            risk_amt = size.qty * loss_per_unit(fill, plan.sl, taker, slip)
            return Position(key, "single", plan.side, d, ts, fill, plan.sl, plan.sl, list(plan.tps),
                            list(plan.fractions), size.qty, size.qty, risk_amt, round(r2, 3), plan.rr_blended,
                            plan.atr, plan.invalidation, plan.meta.get("score", 0.0), plan.counter_trend,
                            leverage=lev.leverage, fees=fee, watermark=fill)
        # para BTC/ETH
        rb, re = self.rows["BTCUSDT"][i], self.rows["ETHUSDT"][i]
        pb = rb["open"] * (1 + d * slip)
        pe = re["open"] * (1 - d * slip)
        ratio_fill = pb / pe
        if d * (ratio_fill - plan.sl) <= 0:
            return None
        r2 = d * (plan.tps[1] - ratio_fill) / (d * (ratio_fill - plan.sl))
        if r2 < float(tpc.get("min_rr", 2.0)):
            return None
        sb, se = self._spec("BTCUSDT"), self._spec("ETHUSDT")
        ps = pair_size(max(equity, 0), ratio_fill, plan.sl, 0.01, pb, pe, taker, slip, sb["qty_step"], se["qty_step"],
                       sb["min_qty"], se["min_qty"], budget=budget)
        if not ps.ok:
            return None
        pc = cfg.get_path("instruments.pair", {})
        # noga kupowana: BTC dla long ratio, ETH dla short ratio
        buy, sell = (("BTCUSDT", pb, rb), ("ETHUSDT", pe, re)) if d == 1 else (("ETHUSDT", pe, re), ("BTCUSDT", pb, rb))
        sl_buy, sl_sell = pair_hard_stops(d, ratio_fill, plan.sl, buy[1], sell[1], buy[2].get("h4_atr"),
                                          sell[2].get("h4_atr"), pc.get("hard_stop_mult", 4.0),
                                          pc.get("hard_stop_atr4h_mult", 3.0))
        hard = {buy[0]: sl_buy, sell[0]: sl_sell}
        legs = [Leg("BTCUSDT", d, ps.qty_long, pb, hard["BTCUSDT"]), Leg("ETHUSDT", -d, ps.qty_short, pe, hard["ETHUSDT"])]
        fee = (ps.qty_long * pb + ps.qty_short * pe) * taker
        return Position(key, "pair", plan.side, d, ts, ratio_fill, plan.sl, plan.sl, list(plan.tps),
                        list(plan.fractions), 1.0, 1.0, ps.risk_amount, round(r2, 3), plan.rr_blended, plan.atr,
                        plan.invalidation, plan.meta.get("score", 0.0), plan.counter_trend, legs=legs, fees=fee,
                        watermark=ratio_fill)

    def _book_partial(self, pos: Position, frac_of_initial: float, px: float, fee_rate: float, slip: float,
                      reason: str, i: int) -> None:
        """Zamyka część pozycji pojedynczej (frac_of_initial z ilości początkowej)."""
        q = min(pos.qty, pos.qty0 * frac_of_initial)
        if q <= 0:
            return
        fill = px * (1 - pos.direction * slip)
        pnl = pos.direction * (fill - pos.entry) * q
        pos.realized += pnl
        pos.fees += q * fill * fee_rate
        pos.qty -= q
        pos.exits.append((reason, round(fill, 6), round(q, 6), i))

    def _process_single(self, pos: Position, r: dict, taker: float, maker: float, slip: float) -> bool:
        d = pos.direction
        o, h, l, c = r["open"], r["high"], r["low"], r["close"]
        risk_u = abs(pos.entry - pos.sl_initial)
        if pos.be_pending:
            be = pos.entry * (1 + d * self.cfg.get_path("exits.break_even_fee_buffer", 0.0015))
            if d * (be - pos.sl) > 0:
                pos.sl = be
            pos.be_pending = False
        # stop (luka / intrabar)
        stop_hit = (d == 1 and l <= pos.sl) or (d == -1 and h >= pos.sl)
        if stop_hit:
            px = o if d * (o - pos.sl) <= 0 else pos.sl
            tag = "trailing_stop" if pos.trailing else ("break_even" if pos.tp_hit[0] else "stop_loss")
            self._book_partial(pos, pos.remaining_frac, px, taker, slip, tag, 0)
            return True
        # take profity
        for k in range(3):
            if pos.tp_hit[k] or pos.qty <= 1e-12:
                continue
            tp = pos.tps[k]
            if (d == 1 and h >= tp) or (d == -1 and l <= tp):
                pos.tp_hit[k] = True
                if k < 2:
                    self._book_partial(pos, pos.fractions[k], tp, maker, 0.0, f"tp{k + 1}", 0)
                    if k == 0 and self.cfg.get_path("exits.break_even_after_tp1", True):
                        pos.be_pending = True
                    if k == 1:
                        pos.trailing = True
                        pos.trail_dist = self.cfg.get_path("exits.trailing.atr_mult", 3.0) * pos.atr
                        pos.watermark = tp
                else:
                    self._book_partial(pos, pos.remaining_frac, tp, taker, slip, "tp3", 0)
            else:
                break
        if pos.qty <= pos.qty0 * 1e-9:
            return True
        fav = (h - pos.entry) if d == 1 else (pos.entry - l)
        pos.max_fav_r = max(pos.max_fav_r, fav / risk_u if risk_u > 0 else 0)
        if pos.trailing:
            pos.watermark = max(pos.watermark, h) if d == 1 else min(pos.watermark, l)
            new_sl = pos.watermark - d * pos.trail_dist
            if d * (new_sl - pos.sl) > 0:
                pos.sl = new_sl
        return False

    def _process_pair(self, pos: Position, i: int, taker: float, slip: float) -> bool:
        """Para: stop/TP na ratio pilnowane przez bota (live co ~10 s) -> intrabar na przybliżonym
        high/low ratio; wyjście obiema nogami po cenach odpowiadających poziomowi ratio."""
        d = pos.direction
        rb, re = self.rows["BTCUSDT"][i], self.rows["ETHUSDT"][i]
        rr = self.rows[PAIR_KEY][i]
        bars = {"BTCUSDT": rb, "ETHUSDT": re}
        # twarde SL nóg (intrabar) - zabezpieczenie katastroficzne
        for leg in pos.legs:
            r = bars[leg.symbol]
            hit = (leg.direction == 1 and r["low"] <= leg.hard_sl) or (leg.direction == -1 and r["high"] >= leg.hard_sl)
            if leg.open and hit:
                px = r["open"] if leg.direction * (r["open"] - leg.hard_sl) <= 0 else leg.hard_sl
                self._close_leg(pos, leg, px, taker, slip, 1.0, "hard_stop_leg", i)
                for other in pos.legs:
                    if other.open:
                        self._close_leg(pos, other, bars[other.symbol]["close"], taker, slip, 1.0,
                                        "hedge_leg_closed", i)
                pos.qty = 0
                return True
        o, h, l, c = rr["open"], rr["high"], rr["low"], rr["close"]
        risk_u = abs(pos.entry - pos.sl_initial)
        if pos.be_pending:
            be = pos.entry * (1 + d * self.cfg.get_path("exits.break_even_fee_buffer", 0.0015))
            if d * (be - pos.sl) > 0:
                pos.sl = be
            pos.be_pending = False
        if (d == 1 and l <= pos.sl) or (d == -1 and h >= pos.sl):
            gap = d * (o - pos.sl) <= 0
            level, eth_ref = (o, re["open"]) if gap else (pos.sl, re["close"])
            tag = "trailing_stop" if pos.trailing else ("break_even" if pos.tp_hit[0] else "stop_loss")
            self._close_pair_at_ratio(pos, pos.qty, level, eth_ref, taker, slip, tag, i)
            return True
        for k in range(3):
            if pos.tp_hit[k]:
                continue
            tp = pos.tps[k]
            if (d == 1 and h >= tp) or (d == -1 and l <= tp):
                pos.tp_hit[k] = True
                frac = pos.fractions[k] if k < 2 else pos.qty
                self._close_pair_at_ratio(pos, min(frac, pos.qty), tp, re["close"], taker, slip, f"tp{k + 1}", i)
                if k == 0 and self.cfg.get_path("exits.break_even_after_tp1", True):
                    pos.be_pending = True
                if k == 1:
                    pos.trailing = True
                    pos.trail_dist = self.cfg.get_path("exits.trailing.atr_mult", 3.0) * pos.atr
                    pos.watermark = tp
            else:
                break
        if pos.qty <= 1e-9:
            return True
        fav = (h - pos.entry) if d == 1 else (pos.entry - l)
        pos.max_fav_r = max(pos.max_fav_r, fav / risk_u if risk_u > 0 else 0)
        if pos.trailing:
            pos.watermark = max(pos.watermark, h) if d == 1 else min(pos.watermark, l)
            new_sl = pos.watermark - d * pos.trail_dist
            if d * (new_sl - pos.sl) > 0:
                pos.sl = new_sl
        return False

    def _close_pair_at_ratio(self, pos: Position, frac_of_initial: float, ratio_level: float, eth_ref: float,
                             taker: float, slip: float, reason: str, i: int) -> None:
        """Zamyka część pary po cenach nóg spełniających BTC/ETH = ratio_level (ETH = eth_ref)."""
        if pos.qty <= 0:
            return
        rel = min(1.0, frac_of_initial / pos.qty)
        prices = {"ETHUSDT": eth_ref, "BTCUSDT": ratio_level * eth_ref}
        for leg in pos.legs:
            if leg.open:
                self._close_leg(pos, leg, prices[leg.symbol], taker, slip, rel, reason, i)
        pos.qty -= frac_of_initial

    def _close_leg(self, pos, leg: Leg, px: float, taker: float, slip: float, frac: float, reason: str, i: int):
        q = leg.qty * frac
        fill = px * (1 - leg.direction * slip)
        pos.realized += leg.direction * (fill - leg.entry) * q
        pos.fees += q * fill * taker
        leg.qty -= q
        if leg.qty <= 1e-12:
            leg.open = False
        pos.exits.append((f"{reason}:{leg.symbol}", round(fill, 6), round(q, 6), i))

    def _close_pair_frac(self, pos: Position, frac_of_initial: float, i: int, taker: float, slip: float, reason: str):
        if pos.qty <= 0:
            return
        rel = min(1.0, frac_of_initial / pos.qty)
        for leg in pos.legs:
            if leg.open:
                self._close_leg(pos, leg, self.rows[leg.symbol][i]["close"], taker, slip, rel, reason, i)
        pos.qty -= frac_of_initial

    def _close_all(self, pos: Position, i: int, reason: str, taker: float, slip: float) -> None:
        if pos.kind == "single":
            self._book_partial(pos, pos.remaining_frac, self.rows[pos.key][i]["close"], taker, slip, reason, i)
        else:
            self._close_pair_frac(pos, pos.qty, i, taker, slip, reason)
            pos.qty = 0

    def _apply_funding(self, pos: Position, ts: pd.Timestamp, i: int) -> None:
        if pos.kind == "single":
            rate = self.funding.get(pos.key, {}).get(ts)
            if rate is not None:
                pos.funding -= pos.direction * pos.qty * self.rows[pos.key][i]["close"] * rate
        else:
            for leg in pos.legs:
                rate = self.funding.get(leg.symbol, {}).get(ts)
                if rate is not None and leg.open:
                    pos.funding -= leg.direction * leg.qty * self.rows[leg.symbol][i]["close"] * rate

    def _unrealized(self, pos: Position, i: int) -> float:
        if pos.kind == "single":
            u = pos.direction * (self.rows[pos.key][i]["close"] - pos.entry) * pos.qty
        else:
            u = sum(leg.direction * (self.rows[leg.symbol][i]["close"] - leg.entry) * leg.qty
                    for leg in pos.legs if leg.open)
        return u + pos.realized + pos.funding - pos.fees

    @staticmethod
    def _net_pnl(pos: Position) -> float:
        return pos.realized + pos.funding - pos.fees

    def _open_risk(self, pos: Position) -> OpenRisk:
        taker = self.cfg.get_path("risk.fees.taker", 0.00055)
        slip = self.cfg.get_path("risk.slippage", 0.0005)
        if pos.kind == "single":
            risk = pos.qty * loss_per_unit(pos.entry, pos.sl, taker, slip)
            if pos.direction * (pos.sl - pos.entry) >= 0:
                risk = 0.0
            return OpenRisk(pos.key, "single", pos.direction, risk, {pos.key: pos.direction})
        frac = pos.qty
        risk = pos.risk_amount * frac if pos.direction * (pos.sl - pos.entry) < 0 else 0.0
        return OpenRisk(pos.key, "pair", pos.direction, risk, {"BTCUSDT": pos.direction, "ETHUSDT": -pos.direction})

    def _trade_record(self, pos: Position, ts) -> dict:
        net = self._net_pnl(pos)
        return {
            "symbol": pos.key, "kind": pos.kind, "side": pos.side, "entry_time": pos.entry_time, "exit_time": ts,
            "entry": pos.entry, "sl": pos.sl_initial, "tp1": pos.tps[0], "tp2": pos.tps[1], "tp3": pos.tps[2],
            "qty": pos.qty0 if pos.kind == "single" else None, "risk_amount": pos.risk_amount,
            "pnl": net, "fees": pos.fees, "funding": pos.funding, "r_multiple": net / pos.risk_amount
            if pos.risk_amount > 0 else 0.0, "planned_rr": pos.plan_rr, "planned_rr_blended": pos.plan_rr_blended,
            "score": pos.score, "counter_trend": pos.counter_trend, "leverage": pos.leverage,
            "bars": pos.bars, "max_fav_r": pos.max_fav_r, "exit_reason": pos.exits[-1][0] if pos.exits else "",
            "exits": ";".join(f"{e[0]}@{e[1]}" for e in pos.exits), "tp_hit": sum(pos.tp_hit),
        }
