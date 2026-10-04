"""Order book: imbalance w pasmach +-0.5% / +-1% / +-2%, ściany płynności, spoofing.

Spoofing: ściana (poziom >= wall_multiplier x mediana) obserwowana co najmniej
`wall_min_persist_s`, która znika, gdy cena podeszła na `spoof_approach_pct`,
a cena NIE przeszła przez jej poziom (czyli nie została zjedzona transakcjami).
Zniknięcie fałszywej ściany bid = sygnał niedźwiedzi (fałszywe wsparcie) i odwrotnie.
"""
from __future__ import annotations

import threading
import time
from dataclasses import dataclass

import numpy as np


def band_imbalance(bids: list[tuple[float, float]], asks: list[tuple[float, float]], mid: float,
                   bands_pct=(0.5, 1.0, 2.0)) -> dict:
    out = {}
    b = np.asarray(bids, float) if bids else np.zeros((0, 2))
    a = np.asarray(asks, float) if asks else np.zeros((0, 2))
    for pct in bands_pct:
        lo, hi = mid * (1 - pct / 100), mid * (1 + pct / 100)
        bv = float((b[:, 0] * b[:, 1])[b[:, 0] >= lo].sum()) if len(b) else 0.0
        av = float((a[:, 0] * a[:, 1])[a[:, 0] <= hi].sum()) if len(a) else 0.0
        out[f"imb_{pct}"] = (bv - av) / (bv + av) if bv + av > 0 else 0.0
        out[f"depth_usd_{pct}"] = bv + av
        # pokrycie: czy book sięga do krawędzi pasma (Bybit 200 poziomów może nie sięgać 2%)
        out[f"covered_{pct}"] = bool(len(b) and len(a) and b[:, 0].min() <= lo and a[:, 0].max() >= hi)
    return out


def find_walls(levels: list[tuple[float, float]], mid: float, multiplier: float = 6.0, max_dist_pct: float = 2.0):
    if not levels:
        return []
    arr = np.asarray(levels, float)
    med = float(np.median(arr[:, 1]))
    if med <= 0:
        return []
    mask = (arr[:, 1] >= multiplier * med) & (np.abs(arr[:, 0] / mid - 1) * 100 <= max_dist_pct)
    return [(float(p), float(q)) for p, q in arr[mask]]


@dataclass
class Wall:
    side: str
    price: float
    size: float
    first_seen: float
    last_seen: float
    min_dist_pct: float


class OrderBookAnalyzer:
    def __init__(self, bands_pct=(0.5, 1.0, 2.0), band_weights=(0.5, 0.3, 0.2), wall_multiplier: float = 6.0,
                 wall_min_persist_s: float = 30, spoof_approach_pct: float = 0.3, spoof_memory_s: float = 900):
        self.bands = tuple(bands_pct)
        self.weights = tuple(band_weights)
        self.mult = wall_multiplier
        self.persist = wall_min_persist_s
        self.approach = spoof_approach_pct
        self.memory = spoof_memory_s
        self.walls: dict[str, dict[tuple[str, float], Wall]] = {}
        self.spoofs: dict[str, list[tuple[float, str, float]]] = {}
        self.last: dict[str, dict] = {}
        self.lock = threading.Lock()

    def on_snapshot(self, symbol: str, snap: dict, now: float | None = None) -> None:
        now = now or time.time()
        bids, asks = snap.get("bids", []), snap.get("asks", [])
        if not bids or not asks:
            return
        mid = (bids[0][0] + asks[0][0]) / 2
        with self.lock:
            walls = self.walls.setdefault(symbol, {})
            spoofs = self.spoofs.setdefault(symbol, [])
            current = {("bid", p): q for p, q in find_walls(bids, mid, self.mult)}
            current.update({("ask", p): q for p, q in find_walls(asks, mid, self.mult)})
            for key, q in current.items():
                dist = abs(key[1] / mid - 1) * 100
                if key in walls:
                    w = walls[key]
                    w.last_seen, w.size, w.min_dist_pct = now, max(w.size, q), min(w.min_dist_pct, dist)
                else:
                    walls[key] = Wall(key[0], key[1], q, now, now, dist)
            for key in list(walls):
                if key in current:
                    continue
                w = walls.pop(key)
                persisted = w.last_seen - w.first_seen >= self.persist
                not_traded = (w.side == "bid" and bids[0][0] > w.price) or (w.side == "ask" and asks[0][0] < w.price)
                if persisted and not_traded and w.min_dist_pct <= self.approach:
                    spoofs.append((now, w.side, w.price))
            self.spoofs[symbol] = [s for s in spoofs if now - s[0] <= self.memory]
            self.last[symbol] = {"bids": bids, "asks": asks, "mid": mid, "ts": now}

    def features(self, symbol: str, now: float | None = None, extra_books: dict[str, dict] | None = None) -> dict:
        now = now or time.time()
        with self.lock:
            snap = self.last.get(symbol)
            walls = list(self.walls.get(symbol, {}).values())
            spoofs = list(self.spoofs.get(symbol, []))
        if not snap or now - snap["ts"] > 120:
            return {"available": False}
        mid = snap["mid"]
        imb = band_imbalance(snap["bids"], snap["asks"], mid, self.bands)
        combined = sum(w * imb[f"imb_{b}"] for b, w in zip(self.bands, self.weights))
        # ściany utrzymujące się >= persist: bid poniżej = wsparcie (+), ask powyżej = opór (-)
        strong = [w for w in walls if w.last_seen - w.first_seen >= self.persist]
        bid_w = sum(w.size * w.price for w in strong if w.side == "bid")
        ask_w = sum(w.size * w.price for w in strong if w.side == "ask")
        wall_score = (bid_w - ask_w) / (bid_w + ask_w) if bid_w + ask_w > 0 else 0.0
        spoof_bid = sum(1 for s in spoofs if s[1] == "bid")
        spoof_ask = sum(1 for s in spoofs if s[1] == "ask")
        spoof_score = float(np.clip((spoof_ask - spoof_bid) / 3.0, -1, 1))  # zniknięte fałszywe bidy = bearish
        spoof_penalty = min(0.5, 0.15 * (spoof_bid + spoof_ask))
        # potwierdzenie z innych giełd (CCXT)
        ext = []
        for book in (extra_books or {}).values():
            if book.get("bids") and book.get("asks"):
                m = (book["bids"][0][0] + book["asks"][0][0]) / 2
                e = band_imbalance(book["bids"], book["asks"], m, self.bands)
                ext.append(sum(w * e[f"imb_{b}"] for b, w in zip(self.bands, self.weights)))
        ext_imb = float(np.mean(ext)) if ext else np.nan
        imb_all = combined if not ext else 0.6 * combined + 0.4 * ext_imb
        raw = (0.55 * imb_all + 0.30 * wall_score + 0.15 * spoof_score) * (1 - spoof_penalty)
        spread_bps = (snap["asks"][0][0] - snap["bids"][0][0]) / mid * 1e4
        return {
            "available": True, "mid": mid, "spread_bps": spread_bps, **imb, "imb_combined": combined,
            "imb_external": ext_imb, "wall_score": wall_score, "walls_bid": bid_w, "walls_ask": ask_w,
            "spoof_bid": spoof_bid, "spoof_ask": spoof_ask, "spoof_penalty": spoof_penalty,
            "orderbook_score": float(np.clip(100 * raw, -100, 100)),
            "wall_levels": [(w.side, w.price, w.size) for w in strong],
        }
