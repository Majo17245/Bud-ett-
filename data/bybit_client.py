"""Bybit API V5 - dane rynkowe (REST) przez pybit.

Endpointy: /v5/market/kline, /orderbook, /tickers, /open-interest,
/funding/history, /account-ratio, /instruments-info, /risk-limit.
Każde wywołanie przechodzi przez limiter i retry z backoffem.
"""
from __future__ import annotations

import logging
import time
from typing import Any

import pandas as pd
import requests

from core.utils import RateLimiter, norm_index

try:
    from pybit.unified_trading import HTTP
    from pybit.exceptions import FailedRequestError, InvalidRequestError
except ImportError:  # pragma: no cover
    HTTP = None
    FailedRequestError = InvalidRequestError = Exception  # type: ignore

log = logging.getLogger(__name__)

INTERVAL_MS = {"1": 60_000, "5": 300_000, "15": 900_000, "60": 3_600_000, "240": 14_400_000,
               "D": 86_400_000, "W": 604_800_000}
OI_INTERVAL = {"60": "1h", "240": "4h", "D": "1d"}
RETRYABLE_CODES = {10000, 10002, 10006, 10016, 10018, 10429, 30034, 30035, 130035, 130150, 170146}


class BybitAPIError(RuntimeError):
    def __init__(self, code: int | None, message: str):
        self.code = code
        super().__init__(f"Bybit error {code}: {message}")


class BybitREST:
    """Cienka warstwa nad pybit.HTTP z limiterem, retry i normalizacją wyników."""

    def __init__(self, testnet: bool = True, api_key: str | None = None, api_secret: str | None = None,
                 rate_per_s: float = 8, timeout: int = 10, recv_window: int = 10000,
                 session: Any = None, max_tries: int = 5):
        if session is not None:
            self.session = session
        else:
            if HTTP is None:
                raise RuntimeError("Brak biblioteki pybit - pip install pybit")
            self.session = HTTP(testnet=testnet, api_key=api_key, api_secret=api_secret,
                                timeout=timeout, recv_window=recv_window, max_retries=2, retry_delay=1)
        self.testnet = testnet
        self.limiter = RateLimiter(rate_per_s, burst=int(rate_per_s))
        self.max_tries = max_tries
        self._instrument_cache: dict[str, dict] = {}

    # ------------------------------------------------------------------ core
    def call(self, method: str, **params) -> dict:
        fn = getattr(self.session, method)
        last_exc: Exception | None = None
        for attempt in range(1, self.max_tries + 1):
            self.limiter.acquire()
            try:
                resp = fn(**params)
            except InvalidRequestError as exc:  # błąd logiczny zwrócony przez Bybit
                code = getattr(exc, "status_code", None)
                if code in RETRYABLE_CODES and attempt < self.max_tries:
                    last_exc = exc
                    self._sleep(attempt, f"{method} code={code}")
                    continue
                raise BybitAPIError(code, getattr(exc, "message", str(exc))) from exc
            except (FailedRequestError, requests.RequestException, ConnectionError, TimeoutError) as exc:
                last_exc = exc
                if attempt < self.max_tries:
                    self._sleep(attempt, f"{method}: {str(exc)[:120]}")
                    continue
                raise BybitAPIError(None, f"{method} failed after {attempt} tries: {exc}") from exc
            if not isinstance(resp, dict):
                raise BybitAPIError(None, f"unexpected response {type(resp)}")
            code = resp.get("retCode", 0)
            if code == 0:
                return resp.get("result") or {}
            if code in RETRYABLE_CODES and attempt < self.max_tries:
                self._sleep(attempt, f"{method} retCode={code}")
                continue
            raise BybitAPIError(code, resp.get("retMsg", ""))
        raise BybitAPIError(None, f"{method}: {last_exc}")

    @staticmethod
    def _sleep(attempt: int, why: str) -> None:
        delay = min(20.0, 0.75 * 2 ** (attempt - 1))
        log.warning("Bybit retry %s za %.1fs (%s)", attempt, delay, why)
        time.sleep(delay)

    # --------------------------------------------------------------- market
    def server_time_ms(self) -> int:
        res = self.call("get_server_time")
        return int(res.get("timeNano", 0)) // 1_000_000 or int(res.get("timeSecond", 0)) * 1000

    def get_klines(self, symbol: str, interval: str, limit: int = 1000, start: int | None = None,
                   end: int | None = None, category: str = "linear") -> pd.DataFrame:
        params: dict[str, Any] = {"category": category, "symbol": symbol, "interval": interval,
                                  "limit": min(limit, 1000)}
        if start is not None:
            params["start"] = int(start)
        if end is not None:
            params["end"] = int(end)
        res = self.call("get_kline", **params)
        return klines_to_df(res.get("list", []))

    def get_klines_range(self, symbol: str, interval: str, start: int, end: int,
                         category: str = "linear") -> pd.DataFrame:
        """Paginacja wstecz od `end` do `start` (Bybit zwraca max 1000 świec)."""
        step = INTERVAL_MS[interval]
        frames = []
        cur_end = end
        while cur_end > start:
            df = self.get_klines(symbol, interval, limit=1000, start=start, end=cur_end, category=category)
            if df.empty:
                break
            frames.append(df)
            first = int(df.index[0].value // 1_000_000)
            if first <= start or len(df) < 2:
                break
            cur_end = first - step
        if not frames:
            return klines_to_df([])
        out = pd.concat(frames).sort_index()
        return out[~out.index.duplicated(keep="last")]

    def get_orderbook(self, symbol: str, limit: int = 200, category: str = "linear") -> dict:
        res = self.call("get_orderbook", category=category, symbol=symbol, limit=limit)
        bids = [(float(p), float(q)) for p, q in res.get("b", [])]
        asks = [(float(p), float(q)) for p, q in res.get("a", [])]
        return {"bids": bids, "asks": asks, "ts": int(res.get("ts", 0) or 0)}

    def get_ticker(self, symbol: str, category: str = "linear") -> dict:
        res = self.call("get_tickers", category=category, symbol=symbol)
        lst = res.get("list", [])
        if not lst:
            raise BybitAPIError(None, f"no ticker for {symbol}")
        t = lst[0]
        out = {}
        for k in ("lastPrice", "markPrice", "indexPrice", "bid1Price", "ask1Price", "bid1Size",
                  "ask1Size", "fundingRate", "openInterest", "openInterestValue", "volume24h",
                  "turnover24h", "price24hPcnt"):
            try:
                out[k] = float(t.get(k) or 0)
            except (TypeError, ValueError):
                out[k] = 0.0
        out["nextFundingTime"] = int(t.get("nextFundingTime") or 0)
        return out

    def get_open_interest(self, symbol: str, interval: str = "60", start: int | None = None,
                          end: int | None = None, limit: int = 200, max_pages: int = 200) -> pd.DataFrame:
        params: dict[str, Any] = {"category": "linear", "symbol": symbol,
                                  "intervalTime": OI_INTERVAL.get(interval, interval), "limit": limit}
        if start is not None:
            params["startTime"] = int(start)
        if end is not None:
            params["endTime"] = int(end)
        rows: list[dict] = []
        for _ in range(max_pages):
            res = self.call("get_open_interest", **params)
            rows.extend(res.get("list", []))
            cursor = res.get("nextPageCursor")
            if not cursor or start is None:
                break
            params["cursor"] = cursor
        if not rows:
            return pd.DataFrame(columns=["open_interest"])
        df = pd.DataFrame(rows)
        df["ts"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms", utc=True)
        df["open_interest"] = df["openInterest"].astype(float)
        return norm_index(df.set_index("ts")[["open_interest"]].sort_index()).loc[lambda d: ~d.index.duplicated()]

    def get_funding_history(self, symbol: str, start: int | None = None, end: int | None = None,
                            max_pages: int = 100) -> pd.DataFrame:
        rows: list[dict] = []
        cur_end = end
        for _ in range(max_pages):
            params: dict[str, Any] = {"category": "linear", "symbol": symbol, "limit": 200}
            if start is not None:
                params["startTime"] = int(start)
            if cur_end is not None:
                params["endTime"] = int(cur_end)
            res = self.call("get_funding_rate_history", **params)
            lst = res.get("list", [])
            if not lst:
                break
            rows.extend(lst)
            oldest = min(int(r["fundingRateTimestamp"]) for r in lst)
            if start is None or oldest <= start or len(lst) < 200:
                break
            cur_end = oldest - 1
        if not rows:
            return pd.DataFrame(columns=["funding_rate"])
        df = pd.DataFrame(rows)
        df["ts"] = pd.to_datetime(df["fundingRateTimestamp"].astype("int64"), unit="ms", utc=True)
        df["funding_rate"] = df["fundingRate"].astype(float)
        return norm_index(df.set_index("ts")[["funding_rate"]].sort_index()).loc[lambda d: ~d.index.duplicated()]

    def get_long_short_ratio(self, symbol: str, period: str = "1h", start: int | None = None,
                             end: int | None = None, max_pages: int = 100) -> pd.DataFrame:
        params: dict[str, Any] = {"category": "linear", "symbol": symbol, "period": period, "limit": 500}
        if start is not None:
            params["startTime"] = int(start)
        if end is not None:
            params["endTime"] = int(end)
        rows: list[dict] = []
        for _ in range(max_pages):
            res = self.call("get_long_short_ratio", **params)
            rows.extend(res.get("list", []))
            cursor = res.get("nextPageCursor")
            if not cursor or start is None:
                break
            params["cursor"] = cursor
        if not rows:
            return pd.DataFrame(columns=["buy_ratio"])
        df = pd.DataFrame(rows)
        df["ts"] = pd.to_datetime(df["timestamp"].astype("int64"), unit="ms", utc=True)
        df["buy_ratio"] = df["buyRatio"].astype(float)
        return norm_index(df.set_index("ts")[["buy_ratio"]].sort_index()).loc[lambda d: ~d.index.duplicated()]

    def get_instrument(self, symbol: str) -> dict:
        if symbol in self._instrument_cache:
            return self._instrument_cache[symbol]
        res = self.call("get_instruments_info", category="linear", symbol=symbol)
        lst = res.get("list", [])
        if not lst:
            raise BybitAPIError(None, f"unknown instrument {symbol}")
        it = lst[0]
        lot, pf, lev = it.get("lotSizeFilter", {}), it.get("priceFilter", {}), it.get("leverageFilter", {})
        info = {
            "symbol": symbol,
            "tick_size": float(pf.get("tickSize", 0.1)),
            "qty_step": float(lot.get("qtyStep", 0.001)),
            "min_qty": float(lot.get("minOrderQty", 0.001)),
            "max_qty": float(lot.get("maxMktOrderQty") or lot.get("maxOrderQty", 1e9)),
            "min_notional": float(lot.get("minNotionalValue", 5) or 5),
            "max_leverage": float(lev.get("maxLeverage", 100)),
            "leverage_step": float(lev.get("leverageStep", 0.01)),
        }
        self._instrument_cache[symbol] = info
        return info

    def get_maintenance_margin(self, symbol: str) -> float:
        try:
            res = self.call("get_risk_limit", category="linear", symbol=symbol)
            lst = res.get("list", [])
            if lst:
                first = sorted(lst, key=lambda r: float(r.get("riskLimitValue", 0)))[0]
                return float(first.get("maintenanceMargin", 0.005))
        except BybitAPIError as exc:
            log.warning("risk-limit %s niedostępny: %s", symbol, exc)
        return 0.005


def klines_to_df(rows: list) -> pd.DataFrame:
    cols = ["open", "high", "low", "close", "volume", "turnover"]
    if not rows:
        return pd.DataFrame(columns=cols, index=pd.DatetimeIndex([], tz="UTC", name="ts").as_unit("ns"))
    df = pd.DataFrame(rows, columns=["ts"] + cols)
    df["ts"] = pd.to_datetime(df["ts"].astype("int64"), unit="ms", utc=True)
    for c in cols:
        df[c] = df[c].astype(float)
    df = norm_index(df.set_index("ts").sort_index())
    return df[~df.index.duplicated(keep="last")]


def drop_unclosed(df: pd.DataFrame, interval: str, now_ms_: int | None = None) -> pd.DataFrame:
    """Usuwa ostatnią, jeszcze niezamkniętą świecę (Bybit zwraca bieżącą świecę)."""
    if df.empty:
        return df
    now_ms_ = now_ms_ or int(time.time() * 1000)
    step = INTERVAL_MS[interval]
    last_open = int(df.index[-1].value // 1_000_000)
    if last_open + step > now_ms_:
        return df.iloc[:-1]
    return df
