"""Ładowanie konfiguracji (config.yaml + .env) i twarde limity bezpieczeństwa."""
from __future__ import annotations

import copy
import os
from pathlib import Path
from typing import Any

import yaml

try:
    from dotenv import load_dotenv
except ImportError:  # pragma: no cover
    load_dotenv = None

ROOT = Path(__file__).resolve().parent.parent
DEFAULT_CONFIG = ROOT / "config" / "config.yaml"

# Zasady nienaruszalne - nawet błędny config.yaml nie może ich przekroczyć.
HARD_LIMITS = {
    "risk_per_trade": 0.01,
    "max_total_risk": 0.03,
    "daily_loss_limit": 0.03,
    "weekly_loss_limit": 0.06,
    "min_rr": 2.0,
}


class Config(dict):
    """Słownik z dostępem po ścieżce: cfg.get_path('risk.fees.taker')."""

    def get_path(self, path: str, default: Any = None) -> Any:
        node: Any = self
        for part in path.split("."):
            if isinstance(node, dict) and part in node:
                node = node[part]
            else:
                return default
        return node

    def set_path(self, path: str, value: Any) -> None:
        node: Any = self
        parts = path.split(".")
        for part in parts[:-1]:
            node = node.setdefault(part, {})
        node[parts[-1]] = value

    def copy_with(self, overrides: dict[str, Any] | None = None) -> "Config":
        new = Config(copy.deepcopy(dict(self)))
        for k, v in (overrides or {}).items():
            new.set_path(k, v)
        enforce_hard_limits(new)
        return new

    @property
    def is_live(self) -> bool:
        return self.get("mode") == "live"


def enforce_hard_limits(cfg: Config) -> Config:
    risk = cfg.setdefault("risk", {})
    for key in ("risk_per_trade", "max_total_risk", "daily_loss_limit", "weekly_loss_limit"):
        val = float(risk.get(key, HARD_LIMITS[key]))
        if val <= 0 or val > HARD_LIMITS[key]:
            raise ValueError(
                f"risk.{key}={val} narusza twardy limit {HARD_LIMITS[key]} (zasada nienaruszalna)"
            )
    min_rr = float(cfg.get_path("exits.tp.min_rr", HARD_LIMITS["min_rr"]))
    if min_rr < HARD_LIMITS["min_rr"]:
        raise ValueError(f"exits.tp.min_rr={min_rr} < {HARD_LIMITS['min_rr']} (zasada nienaruszalna)")
    if cfg.get("mode") not in ("testnet", "live"):
        raise ValueError("mode musi być 'testnet' albo 'live'")
    if cfg.get("mode") == "live" and not cfg.get("live_confirm", False):
        raise ValueError("mode=live wymaga dodatkowo live_confirm: true w config.yaml")
    return cfg


def load_config(path: str | Path | None = None) -> Config:
    path = Path(path) if path else DEFAULT_CONFIG
    with open(path, "r", encoding="utf-8") as fh:
        raw = yaml.safe_load(fh) or {}
    cfg = Config(raw)
    enforce_hard_limits(cfg)
    return cfg


def load_env() -> dict[str, str | None]:
    """Wczytuje .env (klucze API, Telegram, Coinglass)."""
    if load_dotenv is not None:
        load_dotenv(ROOT / ".env", override=False)
    return {
        "BYBIT_API_KEY": os.getenv("BYBIT_API_KEY"),
        "BYBIT_API_SECRET": os.getenv("BYBIT_API_SECRET"),
        "BYBIT_TESTNET_API_KEY": os.getenv("BYBIT_TESTNET_API_KEY"),
        "BYBIT_TESTNET_API_SECRET": os.getenv("BYBIT_TESTNET_API_SECRET"),
        "TELEGRAM_BOT_TOKEN": os.getenv("TELEGRAM_BOT_TOKEN"),
        "TELEGRAM_CHAT_ID": os.getenv("TELEGRAM_CHAT_ID"),
        "COINGLASS_API_KEY": os.getenv("COINGLASS_API_KEY"),
    }


def api_credentials(cfg: Config, env: dict[str, str | None]) -> tuple[str | None, str | None]:
    """Klucze zależne od trybu: testnet używa BYBIT_TESTNET_*, live używa BYBIT_*."""
    if cfg.is_live:
        return env.get("BYBIT_API_KEY"), env.get("BYBIT_API_SECRET")
    return (
        env.get("BYBIT_TESTNET_API_KEY") or env.get("BYBIT_API_KEY"),
        env.get("BYBIT_TESTNET_API_SECRET") or env.get("BYBIT_API_SECRET"),
    )
