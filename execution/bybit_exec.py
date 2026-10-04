"""Egzekucja na Bybit V5 (USDT Perpetual, kategoria linear).

Gwarancje:
  - zlecenie otwierające ZAWSZE zawiera parametr stopLoss (tpslMode=Full, SL po cenie mark)
  - po otwarciu pozycja jest weryfikowana; brak SL -> natychmiastowe ustawienie przez
    set_trading_stop, a gdy to się nie uda -> natychmiastowe zamknięcie pozycji
  - po otwarciu sprawdzana jest cena likwidacji (musi leżeć daleko za SL), inaczej zamknięcie
  - margin isolated, tryb one-way (positionIdx=0)
  - TP1/TP2 jako zlecenia limit reduce-only, TP3 jako takeProfit pozycji
"""
from __future__ import annotations

import logging
import time
import uuid
from dataclasses import dataclass

from core.utils import fmt_num, round_down, round_to_tick
from data.bybit_client import BybitAPIError, BybitREST

log = logging.getLogger(__name__)

NOT_MODIFIED = {110025, 110026, 110043, 34036, 3400050}


@dataclass
class OpenResult:
    ok: bool
    symbol: str
    side: str
    qty: float = 0.0
    avg_price: float = 0.0
    sl: float = 0.0
    tp: float = 0.0
    liq_price: float = 0.0
    order_id: str = ""
    tp_order_ids: list | None = None
    reason: str = ""


class BybitExecutor:
    def __init__(self, rest: BybitREST, cfg):
        self.rest = rest
        self.cfg = cfg
        ex = cfg.get("exchange", {})
        self.category = ex.get("category", "linear")
        self.account_type = ex.get("account_type", "UNIFIED")
        self.sl_trigger = ex.get("sl_trigger_by", "MarkPrice")
        self.tp_trigger = ex.get("tp_trigger_by", "LastPrice")
        self.is_uta = self.account_type == "UNIFIED"

    # ------------------------------------------------------------ account
    def setup_account(self, symbols: list[str]) -> dict:
        """Tryb one-way i margin isolated. Zwraca status (rzuca wyjątek, gdy isolated niemożliwy)."""
        status = {"position_mode": None, "margin_mode": None}
        try:
            self.rest.call("switch_position_mode", category=self.category, coin="USDT", mode=0)
            status["position_mode"] = "one_way"
        except BybitAPIError as exc:
            if exc.code in NOT_MODIFIED:
                status["position_mode"] = "one_way"
            else:
                log.warning("switch_position_mode: %s", exc)
        if self.is_uta:
            try:
                info = self.rest.call("get_account_info")
                mode = info.get("marginMode")
            except BybitAPIError as exc:
                log.warning("get_account_info: %s", exc)
                mode = None
            if mode != "ISOLATED_MARGIN":
                try:
                    res = self.rest.call("set_margin_mode", setMarginMode="ISOLATED_MARGIN")
                    reasons = res.get("reasons") or []
                    if reasons:
                        raise BybitAPIError(None, f"set_margin_mode: {reasons}")
                    mode = "ISOLATED_MARGIN"
                except BybitAPIError as exc:
                    if exc.code in NOT_MODIFIED:
                        mode = "ISOLATED_MARGIN"
                    else:
                        raise RuntimeError(
                            f"Nie można ustawić margin isolated: {exc}. Zamknij pozycje/zlecenia i spróbuj ponownie "
                            "lub ustaw 'Isolated Margin' ręcznie w ustawieniach konta Bybit.") from exc
            status["margin_mode"] = mode
        else:
            for sym in symbols:
                try:
                    self.rest.call("switch_margin_mode", category=self.category, symbol=sym, tradeMode=1,
                                   buyLeverage="1", sellLeverage="1")
                except BybitAPIError as exc:
                    if exc.code not in NOT_MODIFIED:
                        raise RuntimeError(f"Nie można ustawić isolated dla {sym}: {exc}") from exc
            status["margin_mode"] = "ISOLATED (per symbol)"
        log.info("Konto: %s", status)
        return status

    def get_equity(self) -> dict:
        res = self.rest.call("get_wallet_balance", accountType=self.account_type, coin="USDT")
        lst = res.get("list", [])
        if not lst:
            raise BybitAPIError(None, "brak danych portfela")
        acc = lst[0]
        coin = next((c for c in acc.get("coin", []) if c.get("coin") == "USDT"), {})

        def f(x):
            try:
                return float(x)
            except (TypeError, ValueError):
                return 0.0
        equity = f(coin.get("equity")) or f(acc.get("totalEquity"))
        available = f(acc.get("totalAvailableBalance")) or f(coin.get("availableToWithdraw")) or \
            max(0.0, f(coin.get("walletBalance")) - f(coin.get("totalPositionIM")) - f(coin.get("totalOrderIM")))
        return {"equity": equity, "available": available, "wallet": f(coin.get("walletBalance")),
                "unrealised": f(coin.get("unrealisedPnl"))}

    # ------------------------------------------------------------ queries
    def positions(self, symbol: str | None = None) -> list[dict]:
        params = {"category": self.category}
        if symbol:
            params["symbol"] = symbol
        else:
            params["settleCoin"] = "USDT"
        res = self.rest.call("get_positions", **params)
        out = []
        for p in res.get("list", []):
            size = float(p.get("size") or 0)
            if size <= 0:
                continue
            out.append({
                "symbol": p["symbol"], "side": p.get("side"), "size": size,
                "avg_price": float(p.get("avgPrice") or 0), "mark": float(p.get("markPrice") or 0),
                "sl": float(p.get("stopLoss") or 0), "tp": float(p.get("takeProfit") or 0),
                "trailing": float(p.get("trailingStop") or 0), "liq_price": float(p.get("liqPrice") or 0),
                "leverage": float(p.get("leverage") or 0), "upnl": float(p.get("unrealisedPnl") or 0),
                "trade_mode": p.get("tradeMode"), "created": p.get("createdTime"),
            })
        return out

    def position(self, symbol: str) -> dict | None:
        lst = self.positions(symbol)
        return lst[0] if lst else None

    def open_orders(self, symbol: str) -> list[dict]:
        res = self.rest.call("get_open_orders", category=self.category, symbol=symbol)
        return res.get("list", [])

    def last_price(self, symbol: str) -> float:
        return self.rest.get_ticker(symbol)["lastPrice"]

    def closed_pnl(self, symbol: str, since_ms: int | None = None) -> float | None:
        try:
            params = {"category": self.category, "symbol": symbol, "limit": 50}
            if since_ms:
                params["startTime"] = int(since_ms)
            res = self.rest.call("get_closed_pnl", **params)
            return sum(float(x.get("closedPnl") or 0) for x in res.get("list", []))
        except BybitAPIError as exc:
            log.warning("closed_pnl %s: %s", symbol, exc)
            return None

    # ------------------------------------------------------------ helpers
    def instrument(self, symbol: str) -> dict:
        return self.rest.get_instrument(symbol)

    def round_price(self, symbol: str, price: float, mode: str = "nearest") -> float:
        return round_to_tick(price, self.instrument(symbol)["tick_size"], mode)

    def round_qty(self, symbol: str, qty: float) -> float:
        return round_down(qty, self.instrument(symbol)["qty_step"])

    def _p(self, symbol: str, price: float) -> str:
        return fmt_num(price, self.instrument(symbol)["tick_size"])

    def _q(self, symbol: str, qty: float) -> str:
        return fmt_num(qty, self.instrument(symbol)["qty_step"])

    def set_leverage(self, symbol: str, leverage: float) -> None:
        lev = f"{leverage:.2f}".rstrip("0").rstrip(".")
        try:
            self.rest.call("set_leverage", category=self.category, symbol=symbol, buyLeverage=lev, sellLeverage=lev)
        except BybitAPIError as exc:
            if exc.code not in NOT_MODIFIED:
                raise

    # ------------------------------------------------------------ orders
    def open_position(self, symbol: str, side: str, qty: float, sl: float, tp_final: float | None,
                      leverage: float, partial_tps: list[tuple[float, float]] | None = None,
                      min_liq_gap: float | None = None, tag: str = "bot") -> OpenResult:
        """Market z SL (i TP) w jednym zleceniu. partial_tps: [(cena, ilość)] jako reduce-only limit."""
        d = 1 if side == "long" else -1
        q = self.round_qty(symbol, qty)
        if q <= 0 or q < self.instrument(symbol)["min_qty"]:
            return OpenResult(False, symbol, side, reason=f"ilość {qty} poniżej minimum")
        if not sl or sl <= 0:
            return OpenResult(False, symbol, side, reason="odmowa: zlecenie bez SL")
        sl_r = self.round_price(symbol, sl, "down" if d == 1 else "up")
        self.set_leverage(symbol, leverage)
        link = f"{tag}-{uuid.uuid4().hex[:20]}"
        params = {"category": self.category, "symbol": symbol, "side": "Buy" if d == 1 else "Sell",
                  "orderType": "Market", "qty": self._q(symbol, q), "positionIdx": 0, "orderLinkId": link,
                  "stopLoss": self._p(symbol, sl_r), "slTriggerBy": self.sl_trigger, "tpslMode": "Full",
                  "timeInForce": "IOC"}
        tp_r = None
        if tp_final:
            tp_r = self.round_price(symbol, tp_final)
            params.update(takeProfit=self._p(symbol, tp_r), tpTriggerBy=self.tp_trigger)
        try:
            res = self.rest.call("place_order", **params)
        except BybitAPIError as exc:
            return OpenResult(False, symbol, side, reason=f"place_order: {exc}")
        order_id = res.get("orderId", "")
        pos = None
        for _ in range(10):
            pos = self.position(symbol)
            if pos and pos["size"] > 0:
                break
            time.sleep(0.5)
        if not pos:
            return OpenResult(False, symbol, side, order_id=order_id, reason="zlecenie przyjęte, brak pozycji")
        # --- gwarancja SL
        if not pos["sl"]:
            log.error("%s: pozycja bez SL po otwarciu - ustawiam SL awaryjnie", symbol)
            if not self.set_stop_loss(symbol, sl_r):
                self.close_position(symbol, side, pos["size"], "brak możliwości ustawienia SL")
                return OpenResult(False, symbol, side, reason="nie udało się ustawić SL - pozycja zamknięta")
            pos = self.position(symbol) or pos
        # --- likwidacja daleko za SL
        if pos.get("liq_price") and min_liq_gap:
            entry = pos["avg_price"]
            liq_gap = abs(entry - pos["liq_price"]) / entry
            sl_gap = abs(entry - sl_r) / entry
            wrong_side = (d == 1 and pos["liq_price"] >= sl_r) or (d == -1 and pos["liq_price"] <= sl_r)
            if wrong_side or liq_gap < min_liq_gap * sl_gap:
                self.close_position(symbol, side, pos["size"], "likwidacja zbyt blisko SL")
                return OpenResult(False, symbol, side, reason=f"likwidacja {pos['liq_price']} zbyt blisko SL {sl_r}")
        tp_ids = []
        for price, tq in partial_tps or []:
            oid = self.place_reduce_limit(symbol, side, tq, price)
            if oid:
                tp_ids.append(oid)
        return OpenResult(True, symbol, side, pos["size"], pos["avg_price"], sl_r, tp_r or 0.0, pos.get("liq_price", 0),
                          order_id, tp_ids)

    def place_reduce_limit(self, symbol: str, side: str, qty: float, price: float) -> str | None:
        """Częściowy TP: limit reduce-only po stronie przeciwnej do pozycji."""
        q = self.round_qty(symbol, qty)
        if q < self.instrument(symbol)["min_qty"]:
            return None
        try:
            res = self.rest.call("place_order", category=self.category, symbol=symbol,
                                 side="Sell" if side == "long" else "Buy", orderType="Limit",
                                 qty=self._q(symbol, q), price=self._p(symbol, self.round_price(symbol, price)),
                                 timeInForce="GTC", reduceOnly=True, positionIdx=0,
                                 orderLinkId=f"tp-{uuid.uuid4().hex[:20]}")
            return res.get("orderId")
        except BybitAPIError as exc:
            log.warning("%s: częściowy TP %s nie złożony: %s", symbol, price, exc)
            return None

    def set_stop_loss(self, symbol: str, sl: float) -> bool:
        try:
            self.rest.call("set_trading_stop", category=self.category, symbol=symbol, positionIdx=0, tpslMode="Full",
                           stopLoss=self._p(symbol, sl), slTriggerBy=self.sl_trigger)
            return True
        except BybitAPIError as exc:
            if exc.code in NOT_MODIFIED or exc.code == 34040:  # not modified
                return True
            log.error("%s: set_trading_stop SL=%s nieudane: %s", symbol, sl, exc)
            return False

    def set_take_profit(self, symbol: str, tp: float) -> bool:
        try:
            self.rest.call("set_trading_stop", category=self.category, symbol=symbol, positionIdx=0, tpslMode="Full",
                           takeProfit=self._p(symbol, tp), tpTriggerBy=self.tp_trigger)
            return True
        except BybitAPIError as exc:
            if exc.code == 34040:
                return True
            log.warning("%s: set TP nieudane: %s", symbol, exc)
            return False

    def set_trailing_stop(self, symbol: str, distance: float, active_price: float | None = None) -> bool:
        params = {"category": self.category, "symbol": symbol, "positionIdx": 0, "tpslMode": "Full",
                  "trailingStop": self._p(symbol, distance)}
        if active_price:
            params["activePrice"] = self._p(symbol, active_price)
        try:
            self.rest.call("set_trading_stop", **params)
            return True
        except BybitAPIError as exc:
            log.warning("%s: trailing stop nieudany: %s", symbol, exc)
            return False

    def close_position(self, symbol: str, side: str, qty: float | None = None, reason: str = "") -> bool:
        pos = self.position(symbol)
        if not pos:
            return True
        q = pos["size"] if qty is None else min(qty, pos["size"])
        q = self.round_qty(symbol, q)
        if q <= 0:
            return True
        close_side = "Sell" if pos["side"] == "Buy" else "Buy"
        try:
            self.rest.call("place_order", category=self.category, symbol=symbol, side=close_side, orderType="Market",
                           qty=self._q(symbol, q), reduceOnly=True, positionIdx=0, timeInForce="IOC",
                           orderLinkId=f"close-{uuid.uuid4().hex[:18]}")
            log.info("%s: zamknięcie %s (%s)", symbol, q, reason)
            return True
        except BybitAPIError as exc:
            log.error("%s: zamknięcie nieudane: %s", symbol, exc)
            return False

    def cancel_all(self, symbol: str) -> None:
        try:
            self.rest.call("cancel_all_orders", category=self.category, symbol=symbol)
        except BybitAPIError as exc:
            log.warning("%s: cancel_all: %s", symbol, exc)
