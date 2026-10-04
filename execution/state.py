"""Trwały stan bota (logs/state.json) - zapis atomowy, odczyt po restarcie."""
from __future__ import annotations

import json
import os
import threading
from dataclasses import asdict, dataclass, field
from pathlib import Path

from core.utils import ROOT, clean_for_json, utcnow


@dataclass
class ManagedPosition:
    key: str
    kind: str                     # single / pair
    side: str                     # long / short (dla pary: kierunek BTC/ETH)
    entry: float
    sl: float
    sl_initial: float
    tps: list
    fractions: list
    qty0: float                   # single: ilość początkowa; pair: 1.0
    qty: float                    # single: ilość pozostała; pair: pozostała frakcja
    risk_amount: float
    atr: float
    invalidation: float | None
    entry_time: str
    tp_hit: list = field(default_factory=lambda: [False, False, False])
    trailing: bool = False
    bars: int = 0
    max_fav_r: float = 0.0
    legs: list = field(default_factory=list)  # [{symbol, side, qty0, qty, entry, hard_sl}]
    adopted: bool = False
    score: float = 0.0
    rr: float = 0.0
    leverage: float = 1.0
    meta: dict = field(default_factory=dict)

    @property
    def direction(self) -> int:
        return 1 if self.side == "long" else -1

    @property
    def symbols(self) -> list[str]:
        return [leg["symbol"] for leg in self.legs] if self.kind == "pair" else [self.key]


class StateStore:
    def __init__(self, path: str | Path = "logs/state.json"):
        self.path = ROOT / path if not Path(path).is_absolute() else Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()
        self.data: dict = {"positions": {}, "risk": {}, "last_exit": {}, "scores": {}, "equity": None,
                           "history": []}
        self.load()

    def load(self) -> None:
        if self.path.exists():
            try:
                self.data.update(json.loads(self.path.read_text(encoding="utf-8")))
            except Exception:  # noqa: BLE001
                bak = self.path.with_suffix(".corrupt.json")
                os.replace(self.path, bak)

    def save(self) -> None:
        with self.lock:
            self.data["updated"] = utcnow().isoformat()
            tmp = self.path.with_suffix(".tmp")
            tmp.write_text(json.dumps(clean_for_json(self.data), indent=2, ensure_ascii=False), encoding="utf-8")
            os.replace(tmp, self.path)

    # ------------------------------------------------------------ positions
    def positions(self) -> dict[str, ManagedPosition]:
        out = {}
        for k, v in self.data.get("positions", {}).items():
            out[k] = ManagedPosition(**v)
        return out

    def put(self, pos: ManagedPosition) -> None:
        self.data.setdefault("positions", {})[pos.key] = asdict(pos)
        self.save()

    def remove(self, key: str, record: dict | None = None) -> None:
        self.data.setdefault("positions", {}).pop(key, None)
        self.data.setdefault("last_exit", {})[key] = utcnow().isoformat()
        if record:
            hist = self.data.setdefault("history", [])
            hist.append(record)
            self.data["history"] = hist[-500:]
        self.save()
