"""Crypto Fear & Greed Index (alternative.me)."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd
import requests

from core.utils import retry

log = logging.getLogger(__name__)
URL = "https://api.alternative.me/fng/"
CACHE = Path(__file__).resolve().parent / "cache" / "fear_greed.csv"


@retry(tries=3, base_delay=2.0)
def fetch_fear_greed(limit: int = 0) -> pd.Series:
    """limit=0 -> cała historia (od 2018). Zwraca serię dzienną 0..100 (indeks UTC)."""
    resp = requests.get(URL, params={"limit": limit, "format": "json"}, timeout=15)
    resp.raise_for_status()
    data = resp.json().get("data", [])
    if not data:
        raise RuntimeError("Fear&Greed: pusta odpowiedź")
    s = pd.Series({pd.to_datetime(int(d["timestamp"]), unit="s", utc=True): float(d["value"]) for d in data})
    return s.sort_index()


def load_fear_greed(use_cache: bool = True) -> pd.Series | None:
    try:
        s = fetch_fear_greed(0)
        if use_cache:
            CACHE.parent.mkdir(exist_ok=True)
            s.to_frame("value").to_csv(CACHE)
        return s
    except Exception as exc:  # noqa: BLE001
        log.warning("Fear & Greed niedostępny: %s", str(exc)[:200])
    if use_cache and CACHE.exists():
        df = pd.read_csv(CACHE, index_col=0)
        df.index = pd.to_datetime(df.index, utc=True)
        log.warning("Fear & Greed: używam danych z cache")
        return df.iloc[:, 0].astype(float)
    return None
