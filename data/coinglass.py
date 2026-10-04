"""Coinglass API v4 (opcjonalne): heatmapa likwidacji i zagregowane OI.

Bez klucza COINGLASS_API_KEY moduł jest wyłączony (ostrzeżenie w logu),
a bot korzysta z własnego modelu klastrów likwidacji (indicators/liquidations.py).
Heatmapa wymaga płatnego planu Coinglass - przy błędzie 401/403 moduł się wyłącza.
"""
from __future__ import annotations

import logging
import time

import requests

log = logging.getLogger(__name__)
BASE = "https://open-api-v4.coinglass.com"


class CoinglassClient:
    def __init__(self, api_key: str | None, timeout: int = 15):
        self.api_key = api_key
        self.timeout = timeout
        self.enabled = bool(api_key)
        self.disabled_endpoints: set[str] = set()
        if not self.enabled:
            log.warning("Brak COINGLASS_API_KEY - moduł Coinglass wyłączony (bot działa bez niego)")

    def _get(self, path: str, params: dict) -> dict | list | None:
        if not self.enabled or path in self.disabled_endpoints:
            return None
        for attempt in range(3):
            try:
                r = requests.get(BASE + path, params=params, timeout=self.timeout,
                                 headers={"CG-API-KEY": self.api_key, "accept": "application/json"})
                if r.status_code in (401, 403):
                    log.warning("Coinglass %s: brak uprawnień planu (%s) - endpoint wyłączony", path, r.status_code)
                    self.disabled_endpoints.add(path)
                    return None
                if r.status_code == 429:
                    time.sleep(2 * (attempt + 1))
                    continue
                r.raise_for_status()
                body = r.json()
                if str(body.get("code")) not in ("0", "200"):
                    log.warning("Coinglass %s: %s", path, body.get("msg"))
                    return None
                return body.get("data")
            except Exception as exc:  # noqa: BLE001
                log.warning("Coinglass %s błąd: %s", path, str(exc)[:200])
                time.sleep(1 + attempt)
        return None

    def liquidation_levels(self, symbol: str = "BTCUSDT", exchange: str = "Bybit", rng: str = "3d") -> list[dict]:
        """Zwraca listę {price, intensity} z heatmapy (model1)."""
        data = self._get("/api/futures/liquidation/heatmap/model1",
                         {"exchange": exchange, "symbol": symbol, "range": rng})
        if not data or not isinstance(data, dict):
            return []
        try:
            prices = data.get("y_axis") or data.get("yAxis") or []
            cells = data.get("liquidation_leverage_data") or data.get("data") or []
            agg: dict[int, float] = {}
            for cell in cells:
                _, yi, val = cell[0], int(cell[1]), float(cell[2])
                agg[yi] = agg.get(yi, 0.0) + val
            return [{"price": float(prices[i]), "intensity": v} for i, v in agg.items() if i < len(prices)]
        except Exception as exc:  # noqa: BLE001
            log.warning("Coinglass heatmap - nieznany format: %s", exc)
            return []

    def aggregated_oi(self, coin: str = "BTC", interval: str = "1h", limit: int = 48) -> list[dict]:
        data = self._get("/api/futures/open-interest/aggregated-history",
                         {"symbol": coin, "interval": interval, "limit": limit})
        return data if isinstance(data, list) else []
