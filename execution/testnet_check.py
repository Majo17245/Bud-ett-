"""Test połączenia z Bybit Testnet i poprawności zleceń z SL/TP.

    python -m execution.testnet_check            # BTCUSDT: otwarcie z SL+TP, weryfikacja, zamknięcie
    python -m execution.testnet_check --pair     # dodatkowo para BTC/ETH (2 nogi z SL)
    python -m execution.testnet_check --keep     # nie zamykaj pozycji testowej

Kroki: czas serwera -> saldo -> one-way + isolated -> zlecenie market z stopLoss
i takeProfit (ryzyko 0.1% kapitału, SL 2%) -> weryfikacja SL/TP/likwidacji na
pozycji -> częściowy TP jako limit reduce-only -> przesunięcie SL (set_trading_stop)
-> anulowanie zleceń i zamknięcie pozycji. Działa WYŁĄCZNIE na testnecie.
"""
from __future__ import annotations

import argparse
import logging
import sys

from config.settings import api_credentials, load_config, load_env
from core.utils import setup_logging
from data.bybit_client import BybitREST
from execution.bybit_exec import BybitExecutor
from risk.sizing import choose_leverage, position_size

log = logging.getLogger("testnet_check")


class Report:
    def __init__(self):
        self.rows: list[tuple[str, bool, str]] = []

    def add(self, name: str, ok: bool, info: str = "") -> bool:
        self.rows.append((name, ok, info))
        print(f"[{'OK ' if ok else 'BŁĄD'}] {name}" + (f" - {info}" if info else ""), flush=True)
        return ok

    @property
    def ok(self) -> bool:
        return all(r[1] for r in self.rows)


def check_single(ex: BybitExecutor, rest: BybitREST, symbol: str, equity: float, rep: Report, keep: bool,
                 cfg) -> None:
    rcfg = cfg.get("risk", {})
    inst = ex.instrument(symbol)
    px = ex.last_price(symbol)
    rep.add(f"{symbol}: ticker", px > 0, f"cena {px}")
    sl = ex.round_price(symbol, px * 0.98, "down")
    tp = ex.round_price(symbol, px * 1.06)
    tp1 = ex.round_price(symbol, px * 1.03)
    size = position_size(equity, px, sl, 0.001, rcfg["fees"]["taker"], rcfg["slippage"], inst["qty_step"],
                         inst["min_qty"], inst["max_qty"], inst["min_notional"])
    qty = size.qty if size.ok else inst["min_qty"]
    if qty * px < inst["min_notional"]:
        qty = ex.round_qty(symbol, inst["min_notional"] * 1.1 / px + inst["qty_step"])
    lev = choose_leverage(px, sl, "long", rest.get_maintenance_margin(symbol), 10, 1, 2.5, inst["max_leverage"],
                          inst["leverage_step"])
    rep.add(f"{symbol}: dźwignia", lev.ok, f"{lev.leverage}x, likwidacja ~{lev.liq_price:.2f} vs SL {sl}")
    res = ex.open_position(symbol, "long", qty, sl, tp, lev.leverage, partial_tps=[(tp1, qty / 2)],
                           min_liq_gap=2.0, tag="check")
    if not rep.add(f"{symbol}: zlecenie market z stopLoss+takeProfit", res.ok, res.reason or
                   f"qty {res.qty} @ {res.avg_price}"):
        return
    pos = ex.position(symbol)
    rep.add(f"{symbol}: SL na giełdzie", bool(pos and abs(pos["sl"] - sl) < inst["tick_size"] * 2),
            f"SL={pos and pos['sl']}")
    rep.add(f"{symbol}: TP na giełdzie", bool(pos and abs(pos["tp"] - tp) < inst["tick_size"] * 2),
            f"TP={pos and pos['tp']}")
    if pos and pos.get("liq_price"):
        rep.add(f"{symbol}: likwidacja za SL", pos["liq_price"] < sl, f"liq={pos['liq_price']}")
    orders = ex.open_orders(symbol)
    rep.add(f"{symbol}: częściowy TP (limit reduce-only)",
            any(o.get("reduceOnly") in (True, "true") for o in orders), f"{len(orders)} zleceń")
    new_sl = ex.round_price(symbol, px * 0.985, "down")
    rep.add(f"{symbol}: przesunięcie SL (set_trading_stop)", ex.set_stop_loss(symbol, new_sl), f"nowy SL {new_sl}")
    pos = ex.position(symbol)
    rep.add(f"{symbol}: nowy SL potwierdzony", bool(pos and abs(pos["sl"] - new_sl) < inst["tick_size"] * 2))
    if not keep:
        ex.cancel_all(symbol)
        rep.add(f"{symbol}: zamknięcie pozycji testowej", ex.close_position(symbol, "long", None, "test"))
        rep.add(f"{symbol}: brak pozycji po zamknięciu", ex.position(symbol) is None)


def run(rest: BybitREST, cfg, pair: bool = False, keep: bool = False) -> Report:
    rep = Report()
    if cfg.get("mode") != "testnet" and rest.testnet is False:
        rep.add("tryb", False, "testnet_check działa tylko na testnecie")
        return rep
    ex = BybitExecutor(rest, cfg)
    try:
        t = rest.server_time_ms()
        rep.add("połączenie z Bybit Testnet (czas serwera)", t > 0, str(t))
    except Exception as exc:  # noqa: BLE001
        rep.add("połączenie z Bybit Testnet", False, str(exc)[:300])
        return rep
    try:
        eq = ex.get_equity()
        rep.add("saldo konta (klucze API działają)", eq["equity"] > 0, f"{eq['equity']:.2f} USDT")
    except Exception as exc:  # noqa: BLE001
        rep.add("saldo konta / klucze API", False, str(exc)[:300])
        return rep
    try:
        st = ex.setup_account(["BTCUSDT", "ETHUSDT"])
        rep.add("one-way + margin isolated", st.get("margin_mode") is not None, str(st))
    except Exception as exc:  # noqa: BLE001
        rep.add("one-way + margin isolated", False, str(exc)[:300])
        return rep
    for sym in ("BTCUSDT", "ETHUSDT"):
        if ex.position(sym):
            rep.add(f"{sym}: brak otwartej pozycji przed testem", False,
                    "na koncie jest już pozycja - test pominięty, by jej nie naruszyć")
            return rep
    check_single(ex, rest, "BTCUSDT", eq["equity"], rep, keep, cfg)
    if pair:
        px_b, px_e = ex.last_price("BTCUSDT"), ex.last_price("ETHUSDT")
        ib, ie = ex.instrument("BTCUSDT"), ex.instrument("ETHUSDT")
        qb = max(ib["min_qty"], ex.round_qty("BTCUSDT", 10 * 1.2 / px_b + ib["qty_step"]))
        notional = qb * px_b
        qe = max(ie["min_qty"], ex.round_qty("ETHUSDT", notional / px_e))
        r1 = ex.open_position("BTCUSDT", "long", qb, px_b * 0.92, None, 3, tag="pairchk")
        r2 = ex.open_position("ETHUSDT", "short", qe, px_e * 1.08, None, 3, tag="pairchk") if r1.ok else None
        rep.add("para BTC/ETH: noga long BTC z SL", r1.ok, r1.reason)
        rep.add("para BTC/ETH: noga short ETH z SL", bool(r2 and r2.ok), r2.reason if r2 else "pominięte")
        if not keep:
            for s, side in (("BTCUSDT", "long"), ("ETHUSDT", "short")):
                ex.cancel_all(s)
                ex.close_position(s, side, None, "test")
            rep.add("para: zamknięcie nóg", ex.position("BTCUSDT") is None and ex.position("ETHUSDT") is None)
    return rep


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="Test Bybit Testnet: zlecenia z SL i TP")
    p.add_argument("--pair", action="store_true")
    p.add_argument("--keep", action="store_true")
    args = p.parse_args(argv)
    setup_logging()
    cfg = load_config()
    if cfg.get("mode") != "testnet":
        print("Ustaw mode: testnet w config/config.yaml - test działa tylko na testnecie.")
        return 2
    env = load_env()
    key, secret = api_credentials(cfg, env)
    if not key or not secret:
        print("Brak BYBIT_TESTNET_API_KEY / BYBIT_TESTNET_API_SECRET w pliku .env (patrz README).")
        return 2
    rest = BybitREST(testnet=True, api_key=key, api_secret=secret)
    rep = run(rest, cfg, pair=args.pair, keep=args.keep)
    print("\nWYNIK:", "WSZYSTKO OK" if rep.ok else "SĄ BŁĘDY")
    return 0 if rep.ok else 1


if __name__ == "__main__":
    sys.exit(main())
