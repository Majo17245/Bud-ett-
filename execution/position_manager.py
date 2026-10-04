"""Zarządzanie otwartymi pozycjami na żywo.

Co pętlę (domyślnie 10 s):
  - synchronizacja ze stanem giełdy (pozycje zamknięte przez SL/TP -> rozliczenie, powiadomienie)
  - niezmiennik: każda pozycja ma SL na giełdzie - brak -> ustawienie natychmiast
  - TP1 wykonany -> SL na break-even (+bufor); TP2 wykonany -> natywny trailing stop Bybit
  - para BTC/ETH: SL/TP na ratio pilnowane przez bota; brak jednej nogi -> zamknięcie drugiej
Po restarcie: pozycje z giełdy nieobecne w stanie są PRZEJMOWANE (adopt) - dostają SL
(jeśli brak), poziomy TP i trafiają pod zarządzanie.
Co godzinę: warunki unieważnienia scenariusza (check_exit) -> wcześniejsze wyjście.
"""
from __future__ import annotations

import logging
from dataclasses import asdict
from datetime import datetime

import numpy as np

from core.utils import JsonlWriter, utcnow
from execution.bybit_exec import BybitExecutor
from execution.state import ManagedPosition, StateStore
from notifications.telegram import fmt_close, fmt_open
from risk.manager import OpenRisk
from risk.sizing import loss_per_unit
from signals.engine import check_exit
from signals.levels import plan_levels

log = logging.getLogger(__name__)


class PositionManager:
    def __init__(self, executor: BybitExecutor, state: StateStore, cfg, notifier, trades_log: JsonlWriter | None = None,
                 traded: list[str] | None = None, mode: str = "testnet"):
        self.ex = executor
        self.state = state
        self.cfg = cfg
        self.notifier = notifier
        self.trades_log = trades_log
        self.traded = traded or cfg.get_path("instruments.traded", ["BTCUSDT", "ETHUSDT"])
        self.mode = mode
        r = cfg.get("risk", {})
        self.taker, self.slip = r["fees"]["taker"], r["slippage"]
        self.be_buffer = float(cfg.get_path("exits.break_even_fee_buffer", 0.0015))
        self.trail_mult = float(cfg.get_path("exits.trailing.atr_mult", 3.0))

    # ------------------------------------------------------------- risk view
    def open_risks(self) -> list[OpenRisk]:
        out = []
        for p in self.state.positions().values():
            d = p.direction
            losing_side = d * (p.sl - p.entry) < 0
            if p.kind == "single":
                risk = p.qty * loss_per_unit(p.entry, p.sl, self.taker, self.slip) if losing_side else 0.0
                out.append(OpenRisk(p.key, "single", d, risk, {p.key: d}))
            else:
                risk = p.risk_amount * p.qty if losing_side else 0.0
                out.append(OpenRisk(p.key, "pair", d, risk, {leg["symbol"]: (1 if leg["side"] == "long" else -1)
                                                              for leg in p.legs}))
        return out

    # ------------------------------------------------------------- sync loop
    def sync(self, features: dict | None = None) -> None:
        try:
            ex_positions = {p["symbol"]: p for p in self.ex.positions()}
        except Exception as exc:  # noqa: BLE001
            log.error("Nie można pobrać pozycji z giełdy: %s", exc)
            return
        managed = self.state.positions()
        claimed: set[str] = set()
        for key, mp in managed.items():
            claimed.update(mp.symbols)
            try:
                if mp.kind == "single":
                    self._sync_single(mp, ex_positions.get(key))
                else:
                    self._sync_pair(mp, ex_positions)
            except Exception as exc:  # noqa: BLE001
                log.exception("Błąd zarządzania %s: %s", key, exc)
        for sym, p in ex_positions.items():
            if sym in claimed:
                continue
            try:
                self.adopt(p, (features or {}).get(sym))
            except Exception as exc:  # noqa: BLE001
                log.exception("Błąd przejęcia pozycji %s: %s", sym, exc)

    def _finalize(self, mp: ManagedPosition, reason: str) -> None:
        since = None
        try:
            since = int(datetime.fromisoformat(mp.entry_time).timestamp() * 1000)
        except Exception:  # noqa: BLE001
            pass
        pnl = 0.0
        have = False
        for sym in mp.symbols:
            self.ex.cancel_all(sym)
            v = self.ex.closed_pnl(sym, since)
            if v is not None:
                pnl += v
                have = True
        rec = {"type": "trade_closed", "ts": utcnow().isoformat(), "key": mp.key, "kind": mp.kind, "side": mp.side,
               "entry": mp.entry, "sl_initial": mp.sl_initial, "tps": mp.tps, "reason": reason,
               "pnl": pnl if have else None, "risk_amount": mp.risk_amount,
               "r_multiple": (pnl / mp.risk_amount) if have and mp.risk_amount else None,
               "entry_time": mp.entry_time, "tp_hit": mp.tp_hit, "adopted": mp.adopted}
        if self.trades_log:
            self.trades_log.write(rec)
        self.state.remove(mp.key, rec)
        self.notifier.send(fmt_close(mp.key, mp.side, reason, pnl if have else None, self.mode))

    def _sync_single(self, mp: ManagedPosition, p: dict | None) -> None:
        if p is None:
            if mp.trailing:
                reason = "trailing stop"
            elif mp.tp_hit[1] or mp.tp_hit[0]:
                reason = "SL na break-even / TP3"
            else:
                reason = "stop loss / take profit (giełda)"
            self._finalize(mp, reason)
            return
        d = mp.direction
        # niezmiennik: SL zawsze na giełdzie
        if not p["sl"] and not p["trailing"]:
            log.error("%s: pozycja BEZ SL na giełdzie - ustawiam %s", mp.key, mp.sl)
            if not self.ex.set_stop_loss(mp.key, mp.sl):
                self.ex.close_position(mp.key, mp.side, None, "nie można przywrócić SL")
                self.notifier.send(f"⚠️ {mp.key}: brak SL i nie udało się go ustawić - pozycja zamknięta")
                return
        mark = p.get("mark") or p["avg_price"]
        risk_u = abs(mp.entry - mp.sl_initial)
        if risk_u > 0:
            mp.max_fav_r = max(mp.max_fav_r, d * (mark - mp.entry) / risk_u)
        filled = mp.qty0 - p["size"]
        changed = False
        f1, f2 = mp.fractions[0], mp.fractions[0] + mp.fractions[1]
        if not mp.tp_hit[0] and filled >= f1 * mp.qty0 * 0.95:
            mp.tp_hit[0] = True
            changed = True
            if self.cfg.get_path("exits.break_even_after_tp1", True):
                be = self.ex.round_price(mp.key, mp.entry * (1 + d * self.be_buffer), "up" if d == 1 else "down")
                if d * (be - mp.sl) > 0 and d * (mark - be) > 0 and self.ex.set_stop_loss(mp.key, be):
                    mp.sl = be
                    self.notifier.send(f"ℹ️ {mp.key}: TP1 wykonany, SL przesunięty na break-even {be}")
        if not mp.tp_hit[1] and filled >= f2 * mp.qty0 * 0.95:
            mp.tp_hit[1] = True
            changed = True
            dist = self.trail_mult * mp.atr
            if self.ex.set_trailing_stop(mp.key, dist):
                mp.trailing = True
                self.notifier.send(f"ℹ️ {mp.key}: TP2 wykonany, trailing stop {dist:.4g}")
        if p["sl"] and d * (p["sl"] - mp.sl) > 0:  # trailing przesunął SL na giełdzie
            mp.sl = p["sl"]
            changed = True
        if abs(p["size"] - mp.qty) > 1e-12:
            mp.qty = p["size"]
            changed = True
        if changed:
            self.state.put(mp)

    def _sync_pair(self, mp: ManagedPosition, ex_positions: dict) -> None:
        missing = [leg for leg in mp.legs if leg["symbol"] not in ex_positions]
        if missing:
            for leg in mp.legs:
                if leg["symbol"] in ex_positions:
                    self.ex.close_position(leg["symbol"], leg["side"], None, "druga noga pary zamknięta")
            self._finalize(mp, f"twardy SL nogi {[m['symbol'] for m in missing]} - para zamknięta")
            return
        for leg in mp.legs:  # niezmiennik SL na każdej nodze
            p = ex_positions[leg["symbol"]]
            if not p["sl"]:
                if not self.ex.set_stop_loss(leg["symbol"], leg["hard_sl"]):
                    self.close_pair(mp, "nie można przywrócić SL nogi")
                    return
        prices = {leg["symbol"]: self.ex.last_price(leg["symbol"]) for leg in mp.legs}
        ratio = prices["BTCUSDT"] / prices["ETHUSDT"]
        d = mp.direction
        risk_u = abs(mp.entry - mp.sl_initial)
        if risk_u > 0:
            mp.max_fav_r = max(mp.max_fav_r, d * (ratio - mp.entry) / risk_u)
        if d * (ratio - mp.sl) <= 0:
            tag = "trailing stop (ratio)" if mp.trailing else "stop loss (ratio)"
            self.close_pair(mp, tag)
            return
        changed = False
        for k in range(3):
            if mp.tp_hit[k] or d * (ratio - mp.tps[k]) < 0:
                continue
            mp.tp_hit[k] = True
            changed = True
            if k == 2:
                self.close_pair(mp, "TP3 (ratio)")
                return
            frac_rel = mp.fractions[k] / mp.qty if mp.qty > 0 else 1.0
            for leg in mp.legs:
                p = ex_positions[leg["symbol"]]
                self.ex.close_position(leg["symbol"], leg["side"], p["size"] * frac_rel, f"TP{k + 1} pary")
            mp.qty -= mp.fractions[k]
            if k == 0:
                be = mp.entry * (1 + d * self.be_buffer)
                if d * (be - mp.sl) > 0:
                    mp.sl = be
            if k == 1:
                mp.trailing = True
                mp.meta["watermark"] = ratio
            self.notifier.send(f"ℹ️ {mp.key}: TP{k + 1} na ratio {ratio:.5f}")
        if mp.trailing:
            wm = mp.meta.get("watermark", ratio)
            wm = max(wm, ratio) if d == 1 else min(wm, ratio)
            mp.meta["watermark"] = wm
            new_sl = wm - d * self.trail_mult * mp.atr
            if d * (new_sl - mp.sl) > 0:
                mp.sl = new_sl
                changed = True
        if changed:
            self.state.put(mp)

    def close_pair(self, mp: ManagedPosition, reason: str) -> None:
        for leg in mp.legs:
            self.ex.close_position(leg["symbol"], leg["side"], None, reason)
        self._finalize(mp, reason)

    def close(self, mp: ManagedPosition, reason: str) -> None:
        if mp.kind == "pair":
            self.close_pair(mp, reason)
            return
        self.ex.cancel_all(mp.key)
        self.ex.close_position(mp.key, mp.side, None, reason)
        self._finalize(mp, reason)

    # ------------------------------------------------------------- hourly
    def on_new_bar(self, rows: dict, srows: dict) -> None:
        """Wcześniejsze wyjście, gdy scenariusz się unieważnił (wywoływane po zamknięciu świecy 1h)."""
        for key, mp in self.state.positions().items():
            mp.bars += 1
            row, srow = rows.get(key), srows.get(key)
            self.state.put(mp)
            if row is None or srow is None:
                continue
            inval = mp.invalidation
            if inval is not None and mp.meta.get("scale"):
                inval = inval / mp.meta["scale"]  # poziom unieważnienia w cenach danych analitycznych
            reason = check_exit(mp.side, row, srow, self.cfg, mp.bars, mp.max_fav_r, inval)
            if reason:
                log.info("%s: wcześniejsze wyjście - %s", key, reason)
                self.close(mp, "unieważnienie: " + reason)

    # ------------------------------------------------------------- adopt
    def adopt(self, p: dict, feat_row: dict | None) -> ManagedPosition | None:
        sym = p["symbol"]
        if sym not in self.traded:
            log.warning("Pozycja %s poza listą instrumentów - pomijam (nie zarządzam)", sym)
            return None
        side = "long" if p["side"] == "Buy" else "short"
        d = 1 if side == "long" else -1
        entry = p["avg_price"]
        mark = p.get("mark") or entry
        atr = None
        plan = None
        scale = 1.0
        if feat_row is not None and np.isfinite(feat_row.get("close", np.nan)):
            scale = mark / feat_row["close"] if feat_row["close"] else 1.0
            atr = float(feat_row.get("atr", np.nan)) * scale
            row_scaled = {k: (v * scale if isinstance(v, float) and k.endswith(("_sl", "_sh", "poc", "vah", "val"))
                              else v) for k, v in feat_row.items()}
            row_scaled["atr"] = atr
            for k in [c for c in row_scaled if c.startswith("liq_") and not c.endswith("share")]:
                if isinstance(row_scaled[k], float):
                    row_scaled[k] = row_scaled[k] * scale
            plan, _ = plan_levels(sym, side, entry, row_scaled, self.cfg)
        if atr is None or not np.isfinite(atr):
            atr = entry * 0.01
        sl = p["sl"] or (plan.sl if plan else entry - d * 2.0 * atr)
        if d * (mark - sl) <= 0:  # rynek już za proponowanym SL - ciasny SL od bieżącej ceny
            sl = mark - d * 1.0 * atr
        if not p["sl"]:
            sl = self.ex.round_price(sym, sl, "down" if d == 1 else "up")
            if not self.ex.set_stop_loss(sym, sl):
                self.ex.close_position(sym, side, None, "przejęta pozycja bez SL - nie można ustawić SL")
                self.notifier.send(f"⚠️ Przejęta pozycja {sym} bez SL - zamknięta (nie udało się ustawić SL)")
                return None
        risk_u = abs(entry - sl)
        tps = plan.tps if plan else [entry + d * r * risk_u for r in (1.5, 3.0, 5.0)]
        if not p["tp"]:
            self.ex.set_take_profit(sym, tps[2])
        try:
            has_reduce = any(o.get("reduceOnly") for o in self.ex.open_orders(sym))
        except Exception:  # noqa: BLE001
            has_reduce = False
        fr = list(self.cfg.get_path("exits.tp.fractions", [0.35, 0.35, 0.30]))
        if not has_reduce:
            for k in (0, 1):
                if d * (tps[k] - mark) > 0:
                    self.ex.place_reduce_limit(sym, side, p["size"] * fr[k], tps[k])
        mp = ManagedPosition(
            key=sym, kind="single", side=side, entry=entry, sl=sl, sl_initial=sl, tps=list(tps), fractions=fr,
            qty0=p["size"], qty=p["size"], risk_amount=p["size"] * loss_per_unit(entry, sl, self.taker, self.slip),
            atr=atr, invalidation=(plan.invalidation if plan else None), entry_time=utcnow().isoformat(),
            adopted=True, leverage=p.get("leverage", 1.0), meta={"scale": scale})
        self.state.put(mp)
        log.warning("Przejęto pozycję %s %s %.6g @ %.6g, SL=%.6g, TP=%s", sym, side, p["size"], entry, sl, tps)
        self.notifier.send(f"🔁 Przejęto pozycję po restarcie: {sym} {side.upper()} {p['size']} @ {entry:.6g}\n"
                           f"SL: {sl:.6g}  TP: {', '.join(f'{t:.6g}' for t in tps)}")
        return mp

    def register_open(self, mp: ManagedPosition, qty_str: str) -> None:
        self.state.put(mp)
        rec = {"type": "trade_opened", "ts": utcnow().isoformat(), **asdict(mp)}
        if self.trades_log:
            self.trades_log.write(rec)
        self.notifier.send(fmt_open(mp.key, mp.side, mp.entry, mp.sl, mp.tps, qty_str, mp.risk_amount, mp.rr,
                                    mp.score, mp.leverage, self.mode))
