"""Powiadomienia Telegram (otwarcie / zamknięcie pozycji, błędy krytyczne).

Wysyłka w osobnym wątku z kolejką - awaria Telegrama nie blokuje bota.
Bez TELEGRAM_BOT_TOKEN / TELEGRAM_CHAT_ID moduł działa jako no-op (log).
"""
from __future__ import annotations

import logging
import queue
import threading
import time

import requests

log = logging.getLogger(__name__)


class TelegramNotifier:
    def __init__(self, token: str | None, chat_id: str | None, prefix: str = ""):
        self.token, self.chat_id, self.prefix = token, chat_id, prefix
        self.enabled = bool(token and chat_id)
        self.q: queue.Queue = queue.Queue(maxsize=500)
        self.sent: list[str] = []  # historia (testy / dashboard)
        if self.enabled:
            threading.Thread(target=self._worker, name="telegram", daemon=True).start()
        else:
            log.warning("Telegram nieskonfigurowany (TELEGRAM_BOT_TOKEN/TELEGRAM_CHAT_ID) - powiadomienia tylko w logu")

    def send(self, text: str) -> None:
        msg = f"{self.prefix}{text}"
        self.sent.append(msg)
        log.info("NOTIFY: %s", msg.replace("\n", " | "))
        if self.enabled:
            try:
                self.q.put_nowait(msg)
            except queue.Full:
                log.warning("Kolejka Telegram pełna - wiadomość pominięta")

    def _worker(self) -> None:
        url = f"https://api.telegram.org/bot{self.token}/sendMessage"
        while True:
            msg = self.q.get()
            for attempt in range(3):
                try:
                    r = requests.post(url, json={"chat_id": self.chat_id, "text": msg[:4000],
                                                 "disable_web_page_preview": True}, timeout=10)
                    if r.status_code == 429:
                        time.sleep(int(r.json().get("parameters", {}).get("retry_after", 3)))
                        continue
                    r.raise_for_status()
                    break
                except Exception as exc:  # noqa: BLE001
                    log.warning("Telegram błąd (%s/3): %s", attempt + 1, str(exc)[:150])
                    time.sleep(2 * (attempt + 1))


def fmt_open(key: str, side: str, entry: float, sl: float, tps: list[float], qty: str, risk: float, rr: float,
             score: float, lev: float, mode: str) -> str:
    return (f"🟢 OTWARCIE {key} {side.upper()} [{mode}]\n"
            f"Wejście: {entry:.6g}  SL: {sl:.6g}\nTP: {', '.join(f'{t:.6g}' for t in tps)}\n"
            f"Ilość: {qty}  Dźwignia: {lev}x  Ryzyko: {risk:.2f} USDT  R:R: {rr:.2f}\nScore: {score:.1f}")


def fmt_close(key: str, side: str, reason: str, pnl: float | None, mode: str) -> str:
    pnl_s = f"{pnl:+.2f} USDT" if pnl is not None else "n/d"
    icon = "✅" if (pnl or 0) > 0 else "🔴"
    return f"{icon} ZAMKNIĘCIE {key} {side.upper()} [{mode}]\nPowód: {reason}\nPnL: {pnl_s}"
