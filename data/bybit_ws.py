"""Bybit V5 public WebSocket: orderbook, publicTrade (CVD), allLiquidation, tickers.

- Lokalny order book odbudowywany ze snapshot + delta.
- CVD liczony z realnych transakcji (strona agresora: Buy = agresywny kupujący).
- Likwidacje z kanału allLiquidation.
- Watchdog: jeśli strumień milczy dłużej niż `stale_seconds`, websocket jest
  tworzony od nowa (pybit dodatkowo sam wznawia połączenie po błędzie).
"""
from __future__ import annotations

import logging
import threading
import time
from collections import defaultdict, deque
from typing import Callable

log = logging.getLogger(__name__)

try:
    from pybit.unified_trading import WebSocket
except ImportError:  # pragma: no cover
    WebSocket = None


class LocalOrderBook:
    def __init__(self, symbol: str):
        self.symbol = symbol
        self.bids: dict[float, float] = {}
        self.asks: dict[float, float] = {}
        self.update_id = 0
        self.ts = 0
        self.lock = threading.Lock()

    def apply(self, msg_type: str, data: dict, ts: int) -> None:
        with self.lock:
            if msg_type == "snapshot" or data.get("u") == 1:
                self.bids = {float(p): float(q) for p, q in data.get("b", [])}
                self.asks = {float(p): float(q) for p, q in data.get("a", [])}
            else:
                for p, q in data.get("b", []):
                    p, q = float(p), float(q)
                    if q == 0:
                        self.bids.pop(p, None)
                    else:
                        self.bids[p] = q
                for p, q in data.get("a", []):
                    p, q = float(p), float(q)
                    if q == 0:
                        self.asks.pop(p, None)
                    else:
                        self.asks[p] = q
            self.update_id = int(data.get("u", 0) or 0)
            self.ts = ts

    def snapshot(self, levels: int = 500) -> dict:
        with self.lock:
            bids = sorted(self.bids.items(), key=lambda x: -x[0])[:levels]
            asks = sorted(self.asks.items(), key=lambda x: x[0])[:levels]
            return {"bids": bids, "asks": asks, "ts": self.ts}


class TradeAggregator:
    """Agreguje transakcje do koszyków minutowych: wolumen agresywnych kupujących/sprzedających."""

    def __init__(self, keep_minutes: int = 60 * 24 * 3):
        self.buckets: dict[str, dict[int, list[float]]] = defaultdict(dict)
        self.keep = keep_minutes
        self.lock = threading.Lock()

    def add(self, symbol: str, ts_ms: int, side: str, qty: float, price: float) -> None:
        minute = ts_ms // 60_000
        with self.lock:
            b = self.buckets[symbol].setdefault(minute, [0.0, 0.0, 0.0])
            if side == "Buy":
                b[0] += qty
            else:
                b[1] += qty
            b[2] += qty * price
            if len(self.buckets[symbol]) > self.keep:
                for k in sorted(self.buckets[symbol])[: len(self.buckets[symbol]) - self.keep]:
                    del self.buckets[symbol][k]

    def delta_since(self, symbol: str, since_ms: int) -> tuple[float, float]:
        """Zwraca (buy_volume, sell_volume) od podanego czasu."""
        start = since_ms // 60_000
        with self.lock:
            buy = sum(v[0] for m, v in self.buckets[symbol].items() if m >= start)
            sell = sum(v[1] for m, v in self.buckets[symbol].items() if m >= start)
        return buy, sell

    def hourly_delta(self, symbol: str) -> dict[int, float]:
        """CVD per godzina (klucz: początek godziny w ms)."""
        out: dict[int, float] = defaultdict(float)
        with self.lock:
            for m, v in self.buckets[symbol].items():
                out[(m // 60) * 3_600_000] += v[0] - v[1]
        return dict(out)

    def coverage_minutes(self, symbol: str) -> int:
        with self.lock:
            return len(self.buckets[symbol])


class BybitPublicStreams:
    def __init__(self, symbols: list[str], testnet: bool = False, depth: int = 200,
                 stale_seconds: int = 60, on_book_snapshot: Callable[[str, dict], None] | None = None,
                 snapshot_interval_s: float = 5.0):
        self.symbols = symbols
        self.testnet = testnet
        self.depth = depth
        self.stale_seconds = stale_seconds
        self.books = {s: LocalOrderBook(s) for s in symbols}
        self.trades = TradeAggregator()
        self.liquidations: deque = deque(maxlen=20_000)
        self.tickers: dict[str, dict] = {}
        self.last_msg: dict[str, float] = defaultdict(float)
        self.on_book_snapshot = on_book_snapshot
        self.snapshot_interval_s = snapshot_interval_s
        self._last_snap: dict[str, float] = defaultdict(float)
        self.ws = None
        self._stop = threading.Event()
        self._watchdog: threading.Thread | None = None
        self.connected = False

    # ----------------------------------------------------------- lifecycle
    def start(self) -> None:
        self._connect()
        self._watchdog = threading.Thread(target=self._watch, name="ws-watchdog", daemon=True)
        self._watchdog.start()

    def stop(self) -> None:
        self._stop.set()
        self._close()

    def _connect(self) -> None:
        if WebSocket is None:
            raise RuntimeError("pybit niedostępny")
        try:
            self.ws = WebSocket(testnet=self.testnet, channel_type="linear", retries=0,
                                restart_on_error=True, ping_interval=20, ping_timeout=10)
            self.ws.orderbook_stream(depth=self.depth, symbol=self.symbols, callback=self._on_book)
            self.ws.trade_stream(symbol=self.symbols, callback=self._on_trade)
            self.ws.ticker_stream(symbol=self.symbols, callback=self._on_ticker)
            try:
                self.ws.all_liquidation_stream(symbol=self.symbols, callback=self._on_liq)
            except Exception as exc:  # noqa: BLE001
                log.warning("allLiquidation niedostępny: %s", exc)
            now = time.time()
            for k in ("book", "trade", "ticker"):
                self.last_msg[k] = now
            self.connected = True
            log.info("WebSocket połączony (%s): %s", "testnet" if self.testnet else "mainnet", self.symbols)
        except Exception as exc:  # noqa: BLE001
            self.connected = False
            log.error("WebSocket - błąd połączenia: %s", exc)

    def _close(self) -> None:
        try:
            if self.ws is not None:
                self.ws.exit()
        except Exception:  # noqa: BLE001
            pass
        self.ws = None
        self.connected = False

    def _watch(self) -> None:
        backoff = 5
        while not self._stop.wait(10):
            now = time.time()
            stale = [k for k in ("book", "trade", "ticker") if now - self.last_msg[k] > self.stale_seconds]
            if self.ws is None or stale:
                log.warning("WebSocket nieaktywny (%s) - ponowne łączenie", stale or "brak połączenia")
                self._close()
                time.sleep(backoff)
                self._connect()
                backoff = 5 if self.connected else min(120, backoff * 2)

    # ----------------------------------------------------------- callbacks
    def _on_book(self, msg: dict) -> None:
        try:
            data = msg.get("data", {})
            sym = data.get("s")
            if sym in self.books:
                self.books[sym].apply(msg.get("type", "delta"), data, int(msg.get("ts", 0)))
                self.last_msg["book"] = time.time()
                if self.on_book_snapshot and time.time() - self._last_snap[sym] >= self.snapshot_interval_s:
                    self._last_snap[sym] = time.time()
                    self.on_book_snapshot(sym, self.books[sym].snapshot())
        except Exception as exc:  # noqa: BLE001
            log.debug("orderbook msg error: %s", exc)

    def _on_trade(self, msg: dict) -> None:
        try:
            for t in msg.get("data", []):
                self.trades.add(t["s"], int(t["T"]), t["S"], float(t["v"]), float(t["p"]))
            self.last_msg["trade"] = time.time()
        except Exception as exc:  # noqa: BLE001
            log.debug("trade msg error: %s", exc)

    def _on_ticker(self, msg: dict) -> None:
        try:
            data = msg.get("data", {})
            sym = data.get("symbol")
            if sym:
                cur = self.tickers.setdefault(sym, {})
                for k, v in data.items():
                    cur[k] = v
                cur["_ts"] = time.time()
            self.last_msg["ticker"] = time.time()
        except Exception as exc:  # noqa: BLE001
            log.debug("ticker msg error: %s", exc)

    def _on_liq(self, msg: dict) -> None:
        try:
            data = msg.get("data", [])
            if isinstance(data, dict):
                data = [data]
            for d in data:
                # S = strona pozycji: "Buy" -> zlikwidowany long, "Sell" -> zlikwidowany short
                self.liquidations.append({
                    "ts": int(d.get("T", 0)), "symbol": d.get("s"), "side": d.get("S"),
                    "qty": float(d.get("v", 0)), "price": float(d.get("p", 0)),
                })
        except Exception as exc:  # noqa: BLE001
            log.debug("liquidation msg error: %s", exc)

    # ----------------------------------------------------------- accessors
    def last_price(self, symbol: str) -> float | None:
        t = self.tickers.get(symbol)
        if not t or time.time() - t.get("_ts", 0) > self.stale_seconds:
            return None
        try:
            return float(t.get("lastPrice"))
        except (TypeError, ValueError):
            return None

    def recent_liquidations(self, symbol: str, since_ms: int) -> list[dict]:
        return [x for x in list(self.liquidations) if x["symbol"] == symbol and x["ts"] >= since_ms]
