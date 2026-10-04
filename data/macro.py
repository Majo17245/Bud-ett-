"""Dane makro: US500 (ES=F / ^GSPC) i złoto (GC=F) z yfinance - tylko jako filtr."""
from __future__ import annotations

import logging
from pathlib import Path

import pandas as pd

log = logging.getLogger(__name__)
CACHE = Path(__file__).resolve().parent / "cache"


def fetch_yf_daily(ticker: str, start: str | None = None, period: str = "3y") -> pd.Series:
    """Zwraca dzienne zamknięcia (indeks UTC, znormalizowany do północy)."""
    import yfinance as yf  # import leniwy - yfinance jest ciężki

    if start:
        df = yf.download(ticker, start=start, interval="1d", progress=False, auto_adjust=True, threads=False)
    else:
        df = yf.download(ticker, period=period, interval="1d", progress=False, auto_adjust=True, threads=False)
    if df is None or df.empty:
        raise RuntimeError(f"yfinance: brak danych dla {ticker}")
    close = df["Close"]
    if isinstance(close, pd.DataFrame):
        close = close.iloc[:, 0]
    idx = pd.to_datetime(close.index)
    idx = idx.tz_localize("UTC") if idx.tz is None else idx.tz_convert("UTC")
    s = pd.Series(close.values.astype(float), index=idx.normalize(), name=ticker)
    return s[~s.index.duplicated(keep="last")].dropna()


class MacroData:
    def __init__(self, spx: str = "ES=F", spx_fallback: str = "^GSPC", gold: str = "GC=F"):
        self.spx, self.spx_fallback, self.gold = spx, spx_fallback, gold

    def load(self, start: str | None = None, use_cache: bool = True) -> dict[str, pd.Series]:
        out: dict[str, pd.Series] = {}
        for key, tickers in (("spx", [self.spx, self.spx_fallback]), ("gold", [self.gold])):
            series = None
            for t in tickers:
                try:
                    series = fetch_yf_daily(t, start=start)
                    if use_cache:
                        CACHE.mkdir(exist_ok=True)
                        series.to_frame("close").to_csv(CACHE / f"macro_{key}.csv")
                    break
                except Exception as exc:  # noqa: BLE001
                    log.warning("Makro %s (%s) niedostępne: %s", key, t, str(exc)[:200])
            if series is None and use_cache and (CACHE / f"macro_{key}.csv").exists():
                series = load_cached_series(CACHE / f"macro_{key}.csv")
                log.warning("Makro %s: używam danych z cache", key)
            if series is not None:
                out[key] = series
        return out


def load_cached_series(path: Path) -> pd.Series:
    df = pd.read_csv(path, index_col=0)
    df.index = pd.to_datetime(df.index, utc=True)
    return df.iloc[:, 0].astype(float)
