"""Wolumen i order book z Binance, OKX, Coinbase, Kraken (CCXT, publiczne endpointy).

Służy do weryfikacji, że wolumen na Bybit jest realny: skok wolumenu (RVOL)
widoczny tylko na jednej giełdzie jest oznaczany jako podejrzany.
Awaria dowolnej giełdy nie zatrzymuje bota - jest pomijana z ostrzeżeniem.
"""
from __future__ import annotations

import logging
import time

import numpy as np
import pandas as pd

log = logging.getLogger(__name__)

try:
    import ccxt
except ImportError:  # pragma: no cover
    ccxt = None

# Spot - największa i najbardziej wiarygodna płynność na tych giełdach
MARKETS = {
    "binance": {"BTCUSDT": "BTC/USDT", "ETHUSDT": "ETH/USDT"},
    "okx": {"BTCUSDT": "BTC/USDT", "ETHUSDT": "ETH/USDT"},
    "coinbase": {"BTCUSDT": "BTC/USD", "ETHUSDT": "ETH/USD"},
    "kraken": {"BTCUSDT": "BTC/USD", "ETHUSDT": "ETH/USD"},
}


class CrossExchangeData:
    def __init__(self, exchanges: list[str], timeout_ms: int = 10000):
        self.clients: dict = {}
        self.failures: dict[str, int] = {}
        self.disabled_until: dict[str, float] = {}
        if ccxt is None:
            log.warning("ccxt niezainstalowany - weryfikacja wolumenu między giełdami wyłączona")
            return
        for name in exchanges:
            try:
                cls = getattr(ccxt, name)
                self.clients[name] = cls({"enableRateLimit": True, "timeout": timeout_ms})
            except Exception as exc:  # noqa: BLE001
                log.warning("CCXT %s niedostępny: %s", name, exc)

    def _available(self, name: str) -> bool:
        return time.time() >= self.disabled_until.get(name, 0)

    def _fail(self, name: str, exc: Exception) -> None:
        n = self.failures.get(name, 0) + 1
        self.failures[name] = n
        # wykładnicze wyłączenie: 1, 2, 4 ... max 60 min
        self.disabled_until[name] = time.time() + min(3600, 60 * 2 ** (n - 1))
        log.warning("CCXT %s błąd (%s), pauza %.0fs: %s", name, n,
                    self.disabled_until[name] - time.time(), str(exc)[:200])

    def fetch_ohlcv(self, symbol: str, timeframe: str = "1h", limit: int = 72) -> dict[str, pd.DataFrame]:
        out: dict[str, pd.DataFrame] = {}
        for name, client in self.clients.items():
            mkt = MARKETS.get(name, {}).get(symbol)
            if not mkt or not self._available(name):
                continue
            try:
                rows = client.fetch_ohlcv(mkt, timeframe=timeframe, limit=limit)
                df = pd.DataFrame(rows, columns=["ts", "open", "high", "low", "close", "volume"])
                df["ts"] = pd.to_datetime(df["ts"], unit="ms", utc=True)
                out[name] = df.set_index("ts")
                self.failures[name] = 0
            except Exception as exc:  # noqa: BLE001
                self._fail(name, exc)
        return out

    def fetch_orderbooks(self, symbol: str, limit: int = 100) -> dict[str, dict]:
        out: dict[str, dict] = {}
        for name, client in self.clients.items():
            mkt = MARKETS.get(name, {}).get(symbol)
            if not mkt or not self._available(name):
                continue
            try:
                ob = client.fetch_order_book(mkt, limit=limit)
                out[name] = {"bids": [(float(p), float(q)) for p, q, *_ in ob.get("bids", [])],
                             "asks": [(float(p), float(q)) for p, q, *_ in ob.get("asks", [])]}
            except Exception as exc:  # noqa: BLE001
                self._fail(name, exc)
        return out


def volume_spike_consistency(bybit_df: pd.DataFrame, others: dict[str, pd.DataFrame],
                             rvol_period: int = 20, spike_rvol: float = 2.0,
                             min_confirming: int = 2, suspicious_weight: float = 0.3) -> dict:
    """Sprawdza, czy skok wolumenu na Bybit jest widoczny na innych giełdach.

    Zwraca wagę (1.0 = wolumen wiarygodny, `suspicious_weight` = podejrzany).
    """
    def rvol(df: pd.DataFrame) -> float:
        v = df["volume"].astype(float)
        if len(v) < rvol_period + 2:
            return float("nan")
        base = v.iloc[-rvol_period - 2:-2].mean()
        return float(v.iloc[-2] / base) if base > 0 else float("nan")  # ostatnia ZAMKNIĘTA świeca

    bybit_rvol = rvol(bybit_df) if bybit_df is not None and not bybit_df.empty else float("nan")
    other_rvols = {k: rvol(v) for k, v in others.items() if v is not None and not v.empty}
    confirming = sum(1 for r in other_rvols.values() if np.isfinite(r) and r >= spike_rvol * 0.6)
    spiking_others = sum(1 for r in other_rvols.values() if np.isfinite(r) and r >= spike_rvol)
    result = {"bybit_rvol": bybit_rvol, "other_rvol": other_rvols, "confirming": confirming,
              "suspicious": False, "weight": 1.0, "available": len(other_rvols)}
    if not np.isfinite(bybit_rvol) or len(other_rvols) == 0:
        return result
    if bybit_rvol >= spike_rvol and confirming < min(min_confirming, len(other_rvols)):
        result.update(suspicious=True, weight=suspicious_weight, reason="skok wolumenu tylko na Bybit")
    elif spiking_others == 1 and bybit_rvol < spike_rvol * 0.6 and len(other_rvols) >= 3:
        result.update(reason="skok wolumenu tylko na jednej zewnętrznej giełdzie - zignorowany")
    return result
