"""Wspólne narzędzia: logowanie, retry z backoffem, limiter zapytań, czas."""
from __future__ import annotations

import functools
import json
import logging
import logging.handlers
import math
import random
import threading
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable

ROOT = Path(__file__).resolve().parent.parent
_LOGGING_READY = False


def setup_logging(level: str = "INFO", log_dir: str | Path = "logs") -> None:
    global _LOGGING_READY
    if _LOGGING_READY:
        return
    log_dir = ROOT / log_dir if not Path(log_dir).is_absolute() else Path(log_dir)
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)-7s %(name)s: %(message)s")
    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    fh = logging.handlers.RotatingFileHandler(
        log_dir / "bot.log", maxBytes=20_000_000, backupCount=5, encoding="utf-8"
    )
    fh.setFormatter(fmt)
    root.addHandler(sh)
    root.addHandler(fh)
    for noisy in ("urllib3", "websocket", "yfinance", "peewee", "ccxt", "pybit"):
        logging.getLogger(noisy).setLevel(logging.WARNING)
    _LOGGING_READY = True


def utcnow() -> datetime:
    return datetime.now(timezone.utc)


def now_ms() -> int:
    return int(time.time() * 1000)


def to_ms(dt: datetime) -> int:
    if dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc)
    return int(dt.timestamp() * 1000)


class RateLimiter:
    """Token bucket - bezpieczny wątkowo."""

    def __init__(self, rate_per_s: float, burst: int | None = None):
        self.rate = float(rate_per_s)
        self.capacity = float(burst or max(1, int(rate_per_s)))
        self.tokens = self.capacity
        self.last = time.monotonic()
        self.lock = threading.Lock()

    def acquire(self) -> None:
        while True:
            with self.lock:
                now = time.monotonic()
                self.tokens = min(self.capacity, self.tokens + (now - self.last) * self.rate)
                self.last = now
                if self.tokens >= 1:
                    self.tokens -= 1
                    return
                wait = (1 - self.tokens) / self.rate
            time.sleep(wait)


def retry(
    tries: int = 4,
    base_delay: float = 1.0,
    max_delay: float = 20.0,
    exceptions: tuple[type[BaseException], ...] = (Exception,),
    logger: logging.Logger | None = None,
    no_retry: Callable[[BaseException], bool] | None = None,
):
    """Dekorator: ponawia wywołanie z wykładniczym backoffem i jitterem."""

    def deco(fn):
        @functools.wraps(fn)
        def wrapper(*args, **kwargs):
            log = logger or logging.getLogger(fn.__module__)
            for attempt in range(1, tries + 1):
                try:
                    return fn(*args, **kwargs)
                except exceptions as exc:  # noqa: PERF203
                    if no_retry and no_retry(exc):
                        raise
                    if attempt == tries:
                        raise
                    delay = min(max_delay, base_delay * 2 ** (attempt - 1)) * (0.8 + 0.4 * random.random())
                    log.warning("%s nieudane (%s/%s): %s - ponawiam za %.1fs",
                                fn.__name__, attempt, tries, str(exc)[:200], delay)
                    time.sleep(delay)
            return None

        return wrapper

    return deco


def safe_call(fn: Callable, *args, default: Any = None, log: logging.Logger | None = None,
              what: str = "", **kwargs) -> Any:
    """Wywołanie, którego awaria nie zatrzymuje bota (dodatkowe źródła danych)."""
    try:
        return fn(*args, **kwargs)
    except Exception as exc:  # noqa: BLE001
        (log or logging.getLogger(__name__)).warning("%s niedostępne: %s", what or fn.__name__, str(exc)[:300])
        return default


def round_down(value: float, step: float) -> float:
    if step <= 0:
        return value
    precision = max(0, -int(math.floor(math.log10(step)))) if step < 1 else 0
    return round(math.floor(value / step + 1e-9) * step, precision + 2)


def round_to_tick(price: float, tick: float, mode: str = "nearest") -> float:
    if tick <= 0:
        return price
    q = price / tick
    if mode == "down":
        n = math.floor(q + 1e-9)
    elif mode == "up":
        n = math.ceil(q - 1e-9)
    else:
        n = round(q)
    decimals = max(0, -int(math.floor(math.log10(tick)))) if tick < 1 else 0
    return round(n * tick, decimals + 2)


def fmt_num(x: float, step: float) -> str:
    """Formatuje liczbę z dokładnością kroku (dla API Bybit - stringi)."""
    if step >= 1:
        return str(int(round(x)))
    decimals = max(0, -int(math.floor(math.log10(step))))
    s = f"{x:.{decimals}f}"
    return s


class JsonlWriter:
    def __init__(self, path: str | Path):
        self.path = ROOT / path if not Path(path).is_absolute() else Path(path)
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.lock = threading.Lock()

    def write(self, record: dict) -> None:
        line = json.dumps(record, default=_json_default, ensure_ascii=False)
        with self.lock, open(self.path, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")


def _json_default(o: Any):
    if isinstance(o, datetime):
        return o.isoformat()
    if hasattr(o, "item"):
        try:
            return o.item()
        except Exception:  # noqa: BLE001
            pass
    if isinstance(o, float) and (math.isnan(o) or math.isinf(o)):
        return None
    return str(o)


def clean_for_json(obj: Any) -> Any:
    """Zamienia NaN/inf/numpy na typy JSON."""
    if isinstance(obj, dict):
        return {str(k): clean_for_json(v) for k, v in obj.items()}
    if isinstance(obj, (list, tuple)):
        return [clean_for_json(v) for v in obj]
    if hasattr(obj, "item") and not isinstance(obj, (str, bytes)):
        try:
            obj = obj.item()
        except Exception:  # noqa: BLE001
            return str(obj)
    if isinstance(obj, float):
        if math.isnan(obj) or math.isinf(obj):
            return None
        return round(obj, 8)
    if isinstance(obj, datetime):
        return obj.isoformat()
    return obj


def norm_index(obj):
    """Ujednolica indeks czasu do datetime64[ns, UTC] (pandas 3 miesza ms/us/ns)."""
    import pandas as pd

    idx = pd.DatetimeIndex(obj.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    obj = obj.copy()
    obj.index = idx.as_unit("ns")
    obj.index.name = "ts"
    return obj


def index_ms(idx):
    """Czas otwarcia świec w ms (niezależnie od rozdzielczości indeksu)."""
    import numpy as np
    import pandas as pd

    idx = pd.DatetimeIndex(idx).as_unit("ns")
    return np.asarray(idx.asi8 // 1_000_000, dtype="int64")
