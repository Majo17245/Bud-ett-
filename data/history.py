"""Pobieranie i cache danych historycznych do backtestu (Bybit + makro + sentyment).

Źródła historyczne dostępne przez API:
  - świece 1h / 4h / 1d (Bybit /v5/market/kline)
  - funding rate (/v5/market/funding/history)
  - open interest 1h (/v5/market/open-interest)
  - long/short ratio 1h (/v5/market/account-ratio)
  - US500 i złoto (yfinance), Fear & Greed (alternative.me)
Order book, CVD z transakcji i likwidacje z websocketu NIE mają historii w API,
więc backtest używa przybliżeń (CVD ze świec, model klastrów likwidacji z OI)
i pomija moduł order book (wagi renormalizowane) - opisane w README.

Użycie:  python -m data.history --years 2.5
"""
from __future__ import annotations

import argparse
import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd

from core.utils import norm_index, setup_logging, to_ms

log = logging.getLogger(__name__)
CACHE = Path(__file__).resolve().parent / "cache"
INTERVALS = ("60", "240", "D")


def _path(name: str) -> Path:
    return CACHE / f"{name}.csv"


def _save(df: pd.DataFrame, name: str) -> None:
    CACHE.mkdir(parents=True, exist_ok=True)
    df.to_csv(_path(name), index_label="ts")


def _load(name: str) -> pd.DataFrame | None:
    p = _path(name)
    if not p.exists():
        return None
    df = pd.read_csv(p, index_col="ts")
    df.index = pd.to_datetime(df.index, utc=True)
    return norm_index(df.sort_index())


def download_history(symbols: list[str], years: float = 2.5, testnet: bool = False) -> None:
    """Pobiera (przyrostowo) dane z Bybit mainnet - publiczne endpointy, bez kluczy."""
    from data.bybit_client import BybitREST
    from data.macro import MacroData
    from data.sentiment import load_fear_greed

    client = BybitREST(testnet=testnet, rate_per_s=8)
    end = datetime.now(timezone.utc)
    start = end - timedelta(days=int(365 * years) + 60)  # +60 dni rozgrzewki wskaźników 1d
    s_ms, e_ms = to_ms(start), to_ms(end)
    for sym in symbols:
        for itv in INTERVALS:
            name = f"{sym}_{itv}"
            old = _load(name)
            fetch_from = s_ms
            if old is not None and not old.empty and old.index[0] <= start + timedelta(days=2):
                fetch_from = to_ms(old.index[-1].to_pydatetime())
            log.info("Pobieram świece %s %s", sym, itv)
            df = client.get_klines_range(sym, itv, fetch_from, e_ms)
            if old is not None and fetch_from != s_ms:
                df = pd.concat([old, df])
                df = df[~df.index.duplicated(keep="last")].sort_index()
            _save(df, name)
            log.info("  %s: %d świec (%s -> %s)", name, len(df), df.index[0] if len(df) else "-",
                     df.index[-1] if len(df) else "-")
        for kind, fn in (
            ("funding", lambda: client.get_funding_history(sym, start=s_ms, end=e_ms)),
            ("oi", lambda: client.get_open_interest(sym, "60", start=s_ms, end=e_ms, max_pages=400)),
            ("ls", lambda: client.get_long_short_ratio(sym, "1h", start=s_ms, end=e_ms, max_pages=200)),
        ):
            try:
                log.info("Pobieram %s %s", kind, sym)
                df = fn()
                _save(df, f"{sym}_{kind}")
                log.info("  %s_%s: %d rekordów", sym, kind, len(df))
            except Exception as exc:  # noqa: BLE001
                log.warning("%s %s niedostępne: %s - backtest pominie ten składnik", kind, sym, exc)
    macro = MacroData().load(start=start.strftime("%Y-%m-%d"))
    for k, s in macro.items():
        _save(s.to_frame("close"), f"macro_{k}")
    fng = load_fear_greed()
    if fng is not None:
        _save(fng.to_frame("value"), "fear_greed")


def load_dataset(symbols: list[str], source: str = "cache", years: float = 2.5, seed: int = 7) -> dict:
    """Zwraca słownik:
    {"symbols": {sym: {"60": df, "240": df, "D": df, "oi": df|None, "funding": df|None, "ls": df|None}},
     "macro": {"spx": Series, "gold": Series}, "fng": Series|None, "source": str}
    """
    if source == "synthetic":
        from data.synthetic import generate_dataset
        return generate_dataset(symbols, years=years, seed=seed)
    if source == "bybit":
        download_history(symbols, years=years)
    out: dict = {"symbols": {}, "macro": {}, "fng": None, "source": "bybit"}
    for sym in symbols:
        d = {}
        for itv in INTERVALS:
            df = _load(f"{sym}_{itv}")
            if df is None or df.empty:
                raise FileNotFoundError(
                    f"Brak danych {sym} {itv} w data/cache. Uruchom: python -m data.history --years {years}"
                )
            d[itv] = df
        for kind in ("oi", "funding", "ls"):
            df = _load(f"{sym}_{kind}")
            d[kind] = df if df is not None and not df.empty else None
        out["symbols"][sym] = d
    for k in ("spx", "gold"):
        df = _load(f"macro_{k}")
        if df is not None and not df.empty:
            out["macro"][k] = df.iloc[:, 0].astype(float)
    fng = _load("fear_greed")
    out["fng"] = fng.iloc[:, 0].astype(float) if fng is not None and not fng.empty else None
    return out


def main() -> None:
    p = argparse.ArgumentParser(description="Pobierz dane historyczne Bybit do backtestu")
    p.add_argument("--years", type=float, default=2.5)
    p.add_argument("--symbols", nargs="+", default=["BTCUSDT", "ETHUSDT"])
    args = p.parse_args()
    setup_logging()
    download_history(args.symbols, years=args.years)


if __name__ == "__main__":
    main()
