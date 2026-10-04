"""Atrapa Bybit V5 (interfejs jak pybit.unified_trading.HTTP) do testów offline.

Symuluje: dane rynkowe (z danych syntetycznych), portfel UTA, pozycje one-way,
zlecenia market/limit reduce-only, SL/TP/trailing na pozycji, cenę likwidacji
(isolated), walidację parametrów jak Bybit (stringi, SL po właściwej stronie ceny,
reduce-only bez pozycji, "not modified").
"""
from __future__ import annotations

import time
import uuid

import pandas as pd
from pybit.exceptions import InvalidRequestError

from core.utils import index_ms

INSTR = {
    "BTCUSDT": {"tickSize": "0.10", "qtyStep": "0.001", "minOrderQty": "0.001", "maxOrderQty": "100",
                "maxMktOrderQty": "100", "minNotionalValue": "5", "maxLeverage": "100.00", "leverageStep": "0.01"},
    "ETHUSDT": {"tickSize": "0.01", "qtyStep": "0.01", "minOrderQty": "0.01", "maxOrderQty": "1000",
                "maxMktOrderQty": "1000", "minNotionalValue": "5", "maxLeverage": "100.00", "leverageStep": "0.01"},
}
MMR = 0.005


def _err(code: int, msg: str):
    raise InvalidRequestError(request="fake", message=msg, status_code=code, time=time.time(), resp_headers={})


def _ok(result: dict | None = None) -> dict:
    return {"retCode": 0, "retMsg": "OK", "result": result or {}}


class FakeBybitHTTP:
    def __init__(self, dataset: dict | None = None, equity: float = 10_000.0, price_offset: float = 1.0):
        self.ds = dataset
        self.equity = equity
        self.positions: dict[str, dict] = {}
        self.orders: list[dict] = []
        self.closed: list[dict] = []
        self.leverage: dict[str, float] = {}
        self.margin_mode = "REGULAR_MARGIN"
        self.position_mode = 3
        self.calls: list[tuple[str, dict]] = []
        self.reject_symbols: set[str] = set()
        self.prices: dict[str, float] = {}
        if dataset:
            for s, d in dataset["symbols"].items():
                self.prices[s] = float(d["60"]["close"].iloc[-1]) * price_offset

    def _log(self, name, kw):
        self.calls.append((name, dict(kw)))

    # ------------------------------------------------------------ market
    def get_server_time(self, **kw):
        return _ok({"timeSecond": str(int(time.time())), "timeNano": str(time.time_ns())})

    def _tf(self, symbol, interval):
        return self.ds["symbols"][symbol]["60" if interval == "60" else interval]

    def get_kline(self, category, symbol, interval, limit=200, start=None, end=None, **kw):
        self._log("get_kline", locals())
        df = self._tf(symbol, interval)
        ms = index_ms(df.index)
        mask = pd.Series(True, index=df.index)
        if start is not None:
            mask &= ms >= int(start)
        if end is not None:
            mask &= ms <= int(end)
        sel = df[mask.values].iloc[-int(limit):]
        rows = [[str(t), *[str(x) for x in r[:6]]] for t, r in zip(index_ms(sel.index), sel[
            ["open", "high", "low", "close", "volume", "turnover"]].values)][::-1]
        return _ok({"list": rows, "symbol": symbol, "category": category})

    def _series_page(self, df, col, out_col, start, end, limit, cursor, ts_key="timestamp"):
        ms = index_ms(df.index)
        mask = pd.Series(True, index=df.index)
        if start is not None:
            mask &= ms >= int(start)
        if end is not None:
            mask &= ms <= int(end)
        sel = df[mask.values].iloc[::-1]
        off = int(cursor or 0)
        page = sel.iloc[off: off + int(limit)]
        rows = [{ts_key: str(t), out_col: str(v)} for t, v in zip(index_ms(page.index), page[col].values)]
        nxt = str(off + int(limit)) if off + int(limit) < len(sel) else ""
        return rows, nxt

    def get_open_interest(self, category, symbol, intervalTime, startTime=None, endTime=None, limit=50, cursor=None):
        rows, nxt = self._series_page(self.ds["symbols"][symbol]["oi"], "open_interest", "openInterest", startTime,
                                      endTime, limit, cursor)
        return _ok({"list": rows, "nextPageCursor": nxt})

    def get_funding_rate_history(self, category, symbol, startTime=None, endTime=None, limit=200):
        rows, _ = self._series_page(self.ds["symbols"][symbol]["funding"], "funding_rate", "fundingRate", startTime,
                                    endTime, limit, None, ts_key="fundingRateTimestamp")
        return _ok({"list": rows})

    def get_long_short_ratio(self, category, symbol, period, startTime=None, endTime=None, limit=50, cursor=None):
        rows, nxt = self._series_page(self.ds["symbols"][symbol]["ls"], "buy_ratio", "buyRatio", startTime, endTime,
                                      limit, cursor)
        for r in rows:
            r["sellRatio"] = str(1 - float(r["buyRatio"]))
        return _ok({"list": rows, "nextPageCursor": nxt})

    def get_tickers(self, category, symbol=None, **kw):
        p = self.prices[symbol]
        return _ok({"list": [{"symbol": symbol, "lastPrice": str(p), "markPrice": str(p), "indexPrice": str(p),
                              "bid1Price": str(p * 0.99995), "ask1Price": str(p * 1.00005), "fundingRate": "0.0001",
                              "openInterest": "1000", "volume24h": "1", "turnover24h": "1",
                              "nextFundingTime": "0"}]})

    def get_orderbook(self, category, symbol, limit=50):
        p = self.prices[symbol]
        b = [[str(p * (1 - 0.0001 * i)), "1.5"] for i in range(1, limit + 1)]
        a = [[str(p * (1 + 0.0001 * i)), "1.4"] for i in range(1, limit + 1)]
        return _ok({"s": symbol, "b": b, "a": a, "ts": int(time.time() * 1000)})

    def get_instruments_info(self, category, symbol=None, **kw):
        it = INSTR[symbol]
        return _ok({"list": [{"symbol": symbol, "priceFilter": {"tickSize": it["tickSize"]},
                              "lotSizeFilter": {k: it[k] for k in ("qtyStep", "minOrderQty", "maxOrderQty",
                                                                   "maxMktOrderQty", "minNotionalValue")},
                              "leverageFilter": {"maxLeverage": it["maxLeverage"], "leverageStep": it["leverageStep"]}}]})

    def get_risk_limit(self, category, symbol=None, **kw):
        return _ok({"list": [{"riskLimitValue": "2000000", "maintenanceMargin": str(MMR)}]})

    # ------------------------------------------------------------ account
    def get_account_info(self, **kw):
        return _ok({"marginMode": self.margin_mode, "unifiedMarginStatus": 4})

    def set_margin_mode(self, setMarginMode, **kw):
        self._log("set_margin_mode", {"setMarginMode": setMarginMode})
        self.margin_mode = setMarginMode
        return _ok({"reasons": []})

    def switch_position_mode(self, category, mode, coin=None, symbol=None):
        self._log("switch_position_mode", {"mode": mode})
        if self.position_mode == mode:
            _err(110025, "Position mode is not modified")
        self.position_mode = mode
        return _ok()

    def get_wallet_balance(self, accountType, coin=None):
        upnl = sum(self._upnl(s) for s in self.positions)
        im = sum(p["size"] * p["avgPrice"] / p["leverage"] for p in self.positions.values())
        eq = self.equity + upnl
        return _ok({"list": [{"accountType": accountType, "totalEquity": str(eq),
                              "totalAvailableBalance": str(eq - im),
                              "coin": [{"coin": "USDT", "equity": str(eq), "walletBalance": str(self.equity),
                                        "unrealisedPnl": str(upnl)}]}]})

    def set_leverage(self, category, symbol, buyLeverage, sellLeverage):
        self._log("set_leverage", locals())
        assert isinstance(buyLeverage, str)
        lev = float(buyLeverage)
        if self.leverage.get(symbol) == lev:
            _err(110043, "Set leverage not modified")
        self.leverage[symbol] = lev
        return _ok()

    # ------------------------------------------------------------ positions
    def _upnl(self, s):
        p = self.positions[s]
        d = 1 if p["side"] == "Buy" else -1
        return d * (self.prices[s] - p["avgPrice"]) * p["size"]

    def get_positions(self, category, symbol=None, settleCoin=None, **kw):
        out = []
        syms = [symbol] if symbol else list(self.positions)
        for s in syms:
            p = self.positions.get(s)
            if not p:
                if symbol:
                    out.append({"symbol": s, "side": "", "size": "0", "avgPrice": "0"})
                continue
            out.append({"symbol": s, "side": p["side"], "size": f"{p['size']:.6f}", "avgPrice": str(p["avgPrice"]),
                        "markPrice": str(self.prices[s]), "stopLoss": str(p.get("stopLoss") or ""),
                        "takeProfit": str(p.get("takeProfit") or ""), "trailingStop": str(p.get("trailingStop") or 0),
                        "liqPrice": str(p["liqPrice"]), "leverage": str(p["leverage"]),
                        "unrealisedPnl": str(self._upnl(s)), "tradeMode": 0, "positionIdx": 0,
                        "createdTime": str(int(time.time() * 1000))})
        return _ok({"list": out})

    def _check_sl_side(self, side_long: bool, sl: float, base: float):
        if side_long and sl >= base:
            _err(10001, f"StopLoss:{sl} set for Buy position should lower than base_price:{base}")
        if not side_long and sl <= base:
            _err(10001, f"StopLoss:{sl} set for Sell position should greater than base_price:{base}")

    def place_order(self, category, symbol, side, orderType, qty, **kw):
        self._log("place_order", {"symbol": symbol, "side": side, "orderType": orderType, "qty": qty, **kw})
        assert isinstance(qty, str), "qty musi być stringiem"
        for k in ("price", "stopLoss", "takeProfit"):
            if k in kw:
                assert isinstance(kw[k], str), f"{k} musi być stringiem"
        if symbol in self.reject_symbols:
            _err(110007, "ab not enough for new order")
        q = float(qty)
        step = float(INSTR[symbol]["qtyStep"])
        if abs(round(q / step) * step - q) > 1e-9:
            _err(10001, "Qty invalid")
        px = self.prices[symbol]
        pos = self.positions.get(symbol)
        reduce = kw.get("reduceOnly", False)
        if reduce and (not pos or (pos["side"] == side)):
            _err(110017, "Reduce-only rule not satisfied")
        oid = uuid.uuid4().hex
        if orderType == "Limit":
            self.orders.append({"orderId": oid, "symbol": symbol, "side": side, "price": float(kw["price"]),
                                "qty": q, "reduceOnly": reduce, "orderLinkId": kw.get("orderLinkId", "")})
            return _ok({"orderId": oid, "orderLinkId": kw.get("orderLinkId", "")})
        if reduce:
            self._reduce(symbol, q, px, "market close")
            return _ok({"orderId": oid})
        if "stopLoss" in kw:
            self._check_sl_side(side == "Buy", float(kw["stopLoss"]), px)
        lev = self.leverage.get(symbol, 10.0)
        if pos:
            if pos["side"] != side:
                _err(10001, "use reduceOnly to close")
            new_size = pos["size"] + q
            pos["avgPrice"] = (pos["avgPrice"] * pos["size"] + px * q) / new_size
            pos["size"] = new_size
        else:
            d = 1 if side == "Buy" else -1
            liq = px * (1 - d / lev + d * MMR)
            pos = {"side": side, "size": q, "avgPrice": px, "leverage": lev, "liqPrice": liq, "stopLoss": 0.0,
                   "takeProfit": 0.0, "trailingStop": 0.0}
            self.positions[symbol] = pos
        if "stopLoss" in kw:
            pos["stopLoss"] = float(kw["stopLoss"])
        if "takeProfit" in kw:
            pos["takeProfit"] = float(kw["takeProfit"])
        self.equity -= q * px * 0.00055
        return _ok({"orderId": oid, "orderLinkId": kw.get("orderLinkId", "")})

    def set_trading_stop(self, category, symbol, positionIdx=0, **kw):
        self._log("set_trading_stop", {"symbol": symbol, **kw})
        pos = self.positions.get(symbol)
        if not pos:
            _err(10001, "can not set tp/sl/ts for zero position")
        px = self.prices[symbol]
        if "stopLoss" in kw:
            sl = float(kw["stopLoss"])
            if sl == pos.get("stopLoss"):
                _err(34040, "not modified")
            if sl > 0:
                self._check_sl_side(pos["side"] == "Buy", sl, px)
            pos["stopLoss"] = sl
        if "takeProfit" in kw:
            pos["takeProfit"] = float(kw["takeProfit"])
        if "trailingStop" in kw:
            pos["trailingStop"] = float(kw["trailingStop"])
            pos["_wm"] = px
        return _ok()

    def get_open_orders(self, category, symbol=None, **kw):
        lst = [{"orderId": o["orderId"], "symbol": o["symbol"], "side": o["side"], "price": str(o["price"]),
                "qty": str(o["qty"]), "reduceOnly": o["reduceOnly"], "orderLinkId": o["orderLinkId"]}
               for o in self.orders if symbol is None or o["symbol"] == symbol]
        return _ok({"list": lst})

    def cancel_all_orders(self, category, symbol=None, **kw):
        self.orders = [o for o in self.orders if symbol and o["symbol"] != symbol]
        return _ok({"list": []})

    def cancel_order(self, category, symbol, orderId=None, **kw):
        self.orders = [o for o in self.orders if o["orderId"] != orderId]
        return _ok()

    def get_closed_pnl(self, category, symbol=None, startTime=None, limit=50, **kw):
        lst = [c for c in self.closed if c["symbol"] == symbol]
        return _ok({"list": [{"symbol": c["symbol"], "closedPnl": str(c["pnl"])} for c in lst]})

    # ------------------------------------------------------------ simulation
    def _reduce(self, symbol, q, px, why):
        pos = self.positions[symbol]
        q = min(q, pos["size"])
        d = 1 if pos["side"] == "Buy" else -1
        pnl = d * (px - pos["avgPrice"]) * q - q * px * 0.00055
        self.equity += pnl
        self.closed.append({"symbol": symbol, "pnl": pnl, "why": why})
        pos["size"] = round(pos["size"] - q, 9)
        if pos["size"] <= 1e-12:
            del self.positions[symbol]
            self.orders = [o for o in self.orders if not (o["symbol"] == symbol and o["reduceOnly"])]

    def set_price(self, symbol: str, price: float) -> None:
        """Przesuwa cenę i wykonuje zlecenia / SL / TP / trailing."""
        self.prices[symbol] = price
        pos = self.positions.get(symbol)
        if not pos:
            return
        d = 1 if pos["side"] == "Buy" else -1
        for o in list(self.orders):
            if o["symbol"] != symbol or not o["reduceOnly"]:
                continue
            if (d == 1 and price >= o["price"]) or (d == -1 and price <= o["price"]):
                self.orders.remove(o)
                self._reduce(symbol, o["qty"], o["price"], "limit tp")
                if symbol not in self.positions:
                    return
        if pos.get("trailingStop"):
            wm = max(pos.get("_wm", price), price) if d == 1 else min(pos.get("_wm", price), price)
            pos["_wm"] = wm
            tsl = wm - d * pos["trailingStop"]
            if not pos["stopLoss"] or d * (tsl - pos["stopLoss"]) > 0:
                pos["stopLoss"] = tsl
        if pos.get("stopLoss") and d * (price - pos["stopLoss"]) <= 0:
            self._reduce(symbol, pos["size"], price, "stop loss")
            return
        if pos.get("takeProfit") and d * (price - pos["takeProfit"]) >= 0:
            self._reduce(symbol, pos["size"], price, "take profit")
            return
        if d * (price - pos["liqPrice"]) <= 0:
            self._reduce(symbol, pos["size"], price, "LIQUIDATION")
