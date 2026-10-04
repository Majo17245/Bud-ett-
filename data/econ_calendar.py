"""Kalendarz ważnych danych makro z USA (blokada handlu wokół publikacji).

Źródła (kolejno): feed ForexFactory (high impact, USD) -> statyczny plik
config/macro_events.yaml -> automatyczny NFP (pierwszy piątek miesiąca 8:30 ET).
"""
from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo

import requests
import yaml

log = logging.getLogger(__name__)
NY = ZoneInfo("America/New_York")
ROOT = Path(__file__).resolve().parent.parent


class MacroCalendar:
    def __init__(self, cfg: dict):
        self.cfg = cfg
        self.events: list[tuple[datetime, str]] = []
        self.last_fetch = 0.0

    def refresh(self, now: datetime | None = None) -> None:
        now = now or datetime.now(timezone.utc)
        events: list[tuple[datetime, str]] = []
        events += self._static()
        if self.cfg.get("auto_nfp", True):
            events += self._nfp(now)
        if self.cfg.get("fetch_calendar", True):
            events += self._online()
        dedup = {(e[0].replace(second=0, microsecond=0), e[1]) for e in events}
        self.events = sorted(dedup)
        self.last_fetch = now.timestamp()

    def _static(self) -> list[tuple[datetime, str]]:
        path = ROOT / self.cfg.get("static_file", "config/macro_events.yaml")
        if not path.exists():
            return []
        try:
            raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
            out = []
            for ev in raw.get("events", []):
                t = datetime.strptime(str(ev["time"]), "%Y-%m-%d %H:%M").replace(tzinfo=NY)
                out.append((t.astimezone(timezone.utc), str(ev.get("name", "event"))))
            return out
        except Exception as exc:  # noqa: BLE001
            log.warning("macro_events.yaml - błąd: %s", exc)
            return []

    @staticmethod
    def _nfp(now: datetime) -> list[tuple[datetime, str]]:
        out = []
        for delta in (-1, 0, 1):
            y, m = now.year, now.month + delta
            if m < 1:
                y, m = y - 1, 12
            elif m > 12:
                y, m = y + 1, 1
            d = datetime(y, m, 1, 8, 30, tzinfo=NY)
            while d.weekday() != 4:
                d += timedelta(days=1)
            out.append((d.astimezone(timezone.utc), "NFP (Non-Farm Payrolls)"))
        return out

    def _online(self) -> list[tuple[datetime, str]]:
        url = self.cfg.get("calendar_url")
        if not url:
            return []
        try:
            r = requests.get(url, timeout=10)
            r.raise_for_status()
            out = []
            for ev in r.json():
                if ev.get("country") == "USD" and str(ev.get("impact", "")).lower() == "high":
                    t = datetime.fromisoformat(ev["date"]).astimezone(timezone.utc)
                    out.append((t, str(ev.get("title", "USD event"))))
            return out
        except Exception as exc:  # noqa: BLE001
            log.warning("Kalendarz makro online niedostępny (używam listy statycznej): %s", str(exc)[:150])
            return []

    def blocking_event(self, now: datetime | None = None) -> tuple[datetime, str] | None:
        now = now or datetime.now(timezone.utc)
        before = timedelta(minutes=int(self.cfg.get("block_before_min", 60)))
        after = timedelta(minutes=int(self.cfg.get("block_after_min", 45)))
        for t, name in self.events:
            if t - before <= now <= t + after:
                return t, name
        return None
