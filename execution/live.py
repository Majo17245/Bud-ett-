"""Bot live (Bybit Testnet domyślnie, mainnet tylko przy mode: live + live_confirm: true).

Uruchomienie:  python bot.py           (pętla ciągła)
               python bot.py --once    (jeden cykl analizy - test)
"""
from __future__ import annotations

import argparse
import logging
import signal
import threading
import time
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from config.settings import api_credentials, load_config, load_env
from core.utils import JsonlWriter, clean_for_json, now_ms, safe_call, setup_logging, utcnow
from data.bybit_client import BybitAPIError, BybitREST, drop_unclosed
from data.coinglass import CoinglassClient
from data.cross_exchange import CrossExchangeData, volume_spike_consistency
from data.econ_calendar import MacroCalendar
from data.macro import MacroData
from data.sentiment import load_fear_greed
from execution.bybit_exec import BybitExecutor
from execution.position_manager import PositionManager
from execution.state import ManagedPosition, StateStore
from indicators.orderbook import OrderBookAnalyzer
from indicators.volume import profile_from_arrays
from notifications.telegram import TelegramNotifier
from risk.manager import RiskManager
from risk.sizing import choose_leverage, pair_hard_stops, pair_size, position_size
from signals.engine import evaluate_entry
from signals.features import build_features, build_pair_features
from signals.scoring import module_scores

log = logging.getLogger("bot")
PAIR_KEY = "BTC/ETH"


class TradingBot:
    def __init__(self, cfg=None, env=None, exec_rest: BybitREST | None = None, market_rest: BybitREST | None = None,
                 ws=None, cross=None, coinglass=None, notifier=None, enable_ws: bool = True,
                 aux_loaders: dict | None = None):
        self.cfg = cfg or load_config()
        self.env = env if env is not None else load_env()
        self.mode = self.cfg["mode"]
        testnet = self.mode != "live"
        ex = self.cfg.get("exchange", {})
        key, secret = api_credentials(self.cfg, self.env)
        if exec_rest is None:
            if not key or not secret:
                raise RuntimeError(
                    "Brak kluczy API w .env (BYBIT_TESTNET_API_KEY / BYBIT_TESTNET_API_SECRET dla testnetu, "
                    "BYBIT_API_KEY / BYBIT_API_SECRET dla live). Zobacz README.")
            exec_rest = BybitREST(testnet=testnet, api_key=key, api_secret=secret,
                                  rate_per_s=ex.get("max_requests_per_second", 8), timeout=ex.get("http_timeout", 10),
                                  recv_window=ex.get("recv_window", 10000))
        self.exec_rest = exec_rest
        data_testnet = testnet and ex.get("market_data_venue", "mainnet") == "same_as_mode"
        self.cross_venue = (data_testnet != testnet)
        self.market = market_rest or BybitREST(testnet=data_testnet, rate_per_s=ex.get("max_requests_per_second", 8))
        self.executor = BybitExecutor(self.exec_rest, self.cfg)
        lg = self.cfg.get("logging", {})
        self.state = StateStore(lg.get("state_file", "logs/state.json"))
        self.decisions = JsonlWriter(lg.get("decisions_file", "logs/decisions.jsonl"))
        self.trades_log = JsonlWriter(lg.get("trades_file", "logs/trades.jsonl"))
        self.notifier = notifier or TelegramNotifier(self.env.get("TELEGRAM_BOT_TOKEN"), self.env.get("TELEGRAM_CHAT_ID"),
                                                     prefix="[BOT] ")
        self.risk = RiskManager(self.cfg)
        self.risk.load(self.state.data.get("risk"))
        self.symbols = list(self.cfg.get_path("instruments.traded", ["BTCUSDT", "ETHUSDT"]))
        self.pm = PositionManager(self.executor, self.state, self.cfg, self.notifier, self.trades_log, self.symbols,
                                  self.mode)
        ic = self.cfg.get("indicators", {})
        obc = ic.get("orderbook", {})
        self.ob = OrderBookAnalyzer(tuple(obc.get("bands_pct", [0.5, 1, 2])), tuple(obc.get("band_weights", [.5, .3, .2])),
                                    obc.get("wall_multiplier", 6.0), obc.get("wall_min_persist_s", 30),
                                    obc.get("spoof_approach_pct", 0.3))
        self.ws = ws
        if ws is None and enable_ws:
            from data.bybit_ws import BybitPublicStreams
            self.ws = BybitPublicStreams(self.symbols, testnet=data_testnet, depth=obc.get("depth", 200),
                                         stale_seconds=self.cfg.get_path("live.ws_stale_seconds", 60),
                                         on_book_snapshot=self.ob.on_snapshot,
                                         snapshot_interval_s=obc.get("snapshot_interval_s", 5))
        self.cross = cross if cross is not None else CrossExchangeData(ic.get("cross_exchange", {}).get(
            "exchanges", ["binance", "okx", "coinbase", "kraken"]))
        self.coinglass = coinglass if coinglass is not None else CoinglassClient(self.env.get("COINGLASS_API_KEY"))
        self.calendar = MacroCalendar(self.cfg.get_path("filters.macro_events", {}))
        self.aux_loaders = aux_loaders or {}
        self.aux: dict = {"macro": {}, "fng": None, "cross_ohlcv": {}, "cross_books": {}, "coinglass": {}}
        self.aux_ts: dict[str, float] = {}
        self.last_bar: pd.Timestamp | None = None
        self.features: dict[str, pd.DataFrame] = {}
        self.scores: dict[str, pd.DataFrame] = {}
        self._stop = threading.Event()

    # ------------------------------------------------------------ startup
    def startup(self) -> None:
        log.info("Start bota - tryb %s, dane analityczne: %s", self.mode.upper(),
                 "mainnet" if not self.market.testnet else "testnet")
        if self.mode == "live":
            log.warning("TRYB LIVE - handel prawdziwymi środkami")
        st = self.exec_rest.server_time_ms()
        drift = abs(st - now_ms())
        if drift > 3000:
            log.warning("Różnica czasu z serwerem Bybit %d ms - zsynchronizuj zegar systemowy (NTP)", drift)
        self.executor.setup_account(self.symbols)
        eq = self.executor.get_equity()
        log.info("Kapitał: %.2f USDT (dostępne %.2f)", eq["equity"], eq["available"])
        self.risk.update_equity(eq["equity"], utcnow())
        self.state.data["equity"] = eq
        self.refresh_aux(force=True)
        self.state.save()
        self.pm.sync(self._latest_rows())
        if self.ws is not None:
            safe_call(self.ws.start, log=log, what="websocket")
        self.notifier.send(f"Bot uruchomiony ({self.mode}). Kapitał {eq['equity']:.2f} USDT. "
                           f"Otwarte pozycje: {list(self.state.positions())}")

    # ------------------------------------------------------------ aux data
    def _due(self, name: str, minutes: float, force: bool) -> bool:
        if force or time.time() - self.aux_ts.get(name, 0) >= minutes * 60:
            self.aux_ts[name] = time.time()
            return True
        return False

    def refresh_aux(self, force: bool = False) -> None:
        mins = self.cfg.get_path("live.aux_refresh_minutes", {})
        mc = self.cfg.get_path("indicators.macro", {})
        if self._due("macro", mins.get("macro", 60), force):
            loader = self.aux_loaders.get("macro") or (lambda: MacroData(mc.get("spx_ticker", "ES=F"), mc.get(
                "spx_fallback", "^GSPC"), mc.get("gold_ticker", "GC=F")).load())
            self.aux["macro"] = safe_call(loader, default=self.aux["macro"], log=log, what="makro (yfinance)") or {}
        if self._due("sentiment", mins.get("sentiment", 60), force):
            loader = self.aux_loaders.get("fng") or load_fear_greed
            self.aux["fng"] = safe_call(loader, default=self.aux["fng"], log=log, what="Fear & Greed")
        if self._due("calendar", mins.get("calendar", 360), force):
            safe_call(self.calendar.refresh, log=log, what="kalendarz makro")
        if self._due("cross", mins.get("cross_exchange", 5), force):
            for sym in self.symbols:
                self.aux["cross_ohlcv"][sym] = safe_call(self.cross.fetch_ohlcv, sym, default={}, log=log,
                                                         what=f"CCXT OHLCV {sym}")
                self.aux["cross_books"][sym] = safe_call(self.cross.fetch_orderbooks, sym, default={}, log=log,
                                                         what=f"CCXT orderbook {sym}")
        if self._due("coinglass", mins.get("coinglass", 15), force) and self.coinglass.enabled:
            for sym in self.symbols:
                self.aux["coinglass"][sym] = safe_call(self.coinglass.liquidation_levels, sym, default=[], log=log,
                                                       what=f"Coinglass {sym}")

    # ------------------------------------------------------------ market data
    def fetch_symbol(self, sym: str) -> dict:
        nb = int(self.cfg.get_path("timeframes.history_bars", 1000))
        n1h = max(nb, int(self.cfg.get_path("filters.atr_percentile_window", 2160)) + 50)
        end = now_ms()
        h1 = self.market.get_klines_range(sym, "60", end - n1h * 3_600_000, end)
        d = {"60": drop_unclosed(h1, "60"),
             "240": drop_unclosed(self.market.get_klines(sym, "240", limit=nb), "240"),
             "D": drop_unclosed(self.market.get_klines(sym, "D", limit=nb), "D")}
        start = end - n1h * 3_600_000
        d["oi"] = safe_call(self.market.get_open_interest, sym, "60", start, end, max_pages=20, log=log,
                            what=f"OI {sym}")
        d["funding"] = safe_call(self.market.get_funding_history, sym, end - 60 * 86_400_000, end, max_pages=3,
                                 log=log, what=f"funding {sym}")
        d["ls"] = safe_call(self.market.get_long_short_ratio, sym, "1h", start, end, max_pages=6, log=log,
                            what=f"long/short {sym}")
        return d

    def _live_delta(self, sym: str, h1: pd.DataFrame) -> pd.Series | None:
        """Realne CVD z websocketu dla godzin w pełni pokrytych transakcjami."""
        if self.ws is None:
            return None
        hd = self.ws.trades.hourly_delta(sym)
        if not hd:
            return None
        s = pd.Series(hd)
        s.index = pd.to_datetime(s.index, unit="ms", utc=True).as_unit("ns")
        start_cover = self.ws.trades.buckets[sym] and min(self.ws.trades.buckets[sym]) * 60_000
        s = s[(s.index.astype("int64") // 1_000_000 > (start_cover or 0)) & (s.index.isin(h1.index))]
        return s if len(s) else None

    def analyze(self) -> dict:
        """Pełna analiza: cechy + scoring dla BTC, ETH i BTC/ETH (ostatnia zamknięta świeca 1h)."""
        self.refresh_aux()
        raw = {}
        for sym in self.symbols:
            raw[sym] = self.fetch_symbol(sym)
        feats, scores, extras = {}, {}, {}
        for sym in self.symbols:
            F = build_features(raw[sym], self.cfg, self.aux.get("macro"), self.aux.get("fng"),
                               live_delta=self._live_delta(sym, raw[sym]["60"]))
            ob = self.ob.features(sym, extra_books=self.aux["cross_books"].get(sym))
            if ob.get("available"):
                F.loc[F.index[-1], "orderbook_score"] = ob["orderbook_score"]
            cc = self.cfg.get_path("indicators.cross_exchange", {})
            vc = volume_spike_consistency(raw[sym]["60"], self.aux["cross_ohlcv"].get(sym, {}),
                                          self.cfg.get_path("indicators.rvol_period", 20), cc.get("spike_rvol", 2.0),
                                          cc.get("min_confirming", 2), cc.get("suspicious_weight", 0.3))
            vw = pd.Series(1.0, index=F.index)
            vw.iloc[-1] = vc["weight"]
            S = module_scores(F, self.cfg, "single", volume_weight=vw)
            feats[sym], scores[sym] = F, S
            extras[sym] = {"ob": ob, "volume_check": vc}
        if self.cfg.get_path("instruments.pair.enabled", True) and {"BTCUSDT", "ETHUSDT"} <= set(self.symbols):
            FP = build_pair_features(raw["BTCUSDT"], raw["ETHUSDT"], feats["BTCUSDT"], feats["ETHUSDT"], self.cfg)
            for c in [c for c in FP.columns if c.startswith("liq_")]:
                FP[c] = np.nan
            ob_b, ob_e = extras["BTCUSDT"]["ob"], extras["ETHUSDT"]["ob"]
            if ob_b.get("available") and ob_e.get("available"):
                FP.loc[FP.index[-1], "orderbook_score"] = (ob_b["orderbook_score"] - ob_e["orderbook_score"]) / 2
            feats[PAIR_KEY], scores[PAIR_KEY] = FP, module_scores(FP, self.cfg, "pair")
            extras[PAIR_KEY] = {}
        self.features, self.scores = feats, scores
        return extras

    def _latest_rows(self) -> dict:
        return {k: f.iloc[-1].to_dict() for k, f in self.features.items() if len(f)}

    # ------------------------------------------------------------ hourly cycle
    def hourly_cycle(self) -> list:
        extras = self.analyze()
        rows = {k: f.iloc[-1].to_dict() for k, f in self.features.items()}
        srows = {k: s.iloc[-1].to_dict() for k, s in self.scores.items()}
        bar_ts = {k: f.index[-1] for k, f in self.features.items()}
        self.pm.sync(rows)
        self.pm.on_new_bar(rows, srows)
        eq = self.executor.get_equity()
        self.risk.update_equity(eq["equity"], utcnow())
        self.state.data["equity"] = eq
        self.state.data["risk"] = self.risk.to_dict()
        self.state.data["risk_status"] = self.risk.loss_status()
        ev = self.calendar.blocking_event()
        decisions = []
        open_keys = set(self.state.positions())
        busy = {s for mp in self.state.positions().values() for s in mp.symbols}
        for key in list(self.features):
            kind = "pair" if key == PAIR_KEY else "single"
            live, extra_levels = self._live_context(key, extras.get(key, {}), ev)
            bse = self._bars_since_exit(key)
            dec = evaluate_entry(key, rows[key], srows[key], self.cfg, kind=kind, ts=bar_ts[key], live=live,
                                 bars_since_exit=bse, extra_levels=extra_levels)
            rec = dec.to_record()
            rec["mode"] = self.mode
            rec["live_context"] = clean_for_json({k: v for k, v in live.items() if k != "levels"})
            if key in open_keys:
                rec["note"] = "pozycja już otwarta - tylko ocena"
            elif dec.action != "none":
                if busy & set(["BTCUSDT", "ETHUSDT"] if kind == "pair" else [key]):
                    rec["execution"] = "pominięte: instrument zajęty"
                else:
                    rec["execution"] = self.execute(dec, kind, eq["equity"])
                    if rec["execution"].startswith("OK"):
                        busy |= set(self.state.positions().get(key).symbols) if key in self.state.positions() else set()
            self.decisions.write(rec)
            decisions.append(rec)
            log.info("[%s] %s score=%.1f -> %s %s", key, bar_ts[key], dec.score or 0, dec.action,
                     rec.get("execution") or "; ".join(dec.reasons)[:200])
        self.state.data["scores"] = {k: clean_for_json({**{m: srows[k].get(m) for m in srows[k]},
                                                        "ts": str(bar_ts[k]), "close": rows[k].get("close")})
                                     for k in srows}
        self.state.data["last_cycle"] = utcnow().isoformat()
        self.state.save()
        return decisions

    def _bars_since_exit(self, key: str) -> int | None:
        t = self.state.data.get("last_exit", {}).get(key)
        if not t:
            return None
        try:
            return int((utcnow() - datetime.fromisoformat(t)).total_seconds() // 3600)
        except Exception:  # noqa: BLE001
            return None

    def _live_context(self, key: str, extra: dict, ev) -> tuple[dict, dict]:
        live: dict = {}
        levels: dict = {}
        if ev:
            live["macro_event"] = f"{ev[1]} @ {ev[0].isoformat()}"
        ob = extra.get("ob") or {}
        if ob.get("available"):
            live["spread_bps"] = ob.get("spread_bps")
            if ob.get("covered_1.0"):
                live["depth_usd_1pct"] = ob.get("depth_usd_1.0")
            levels["walls_ask"] = [p for s, p, q in ob.get("wall_levels", []) if s == "ask"]
            levels["walls_bid"] = [p for s, p, q in ob.get("wall_levels", []) if s == "bid"]
        vc = extra.get("volume_check") or {}
        if vc.get("suspicious"):
            live["volume_suspicious"] = True
        if key != PAIR_KEY and key in self.features:
            F = self.features[key]
            win = int(self.cfg.get_path("indicators.volume_profile.window_bars", 720))
            tail = F.iloc[-win:]
            prof = profile_from_arrays(((tail["high"] + tail["low"] + tail["close"]) / 3).values,
                                       tail["h1_volume"].values if "h1_volume" in tail else np.ones(len(tail)))
            levels["hvn"] = prof.get("hvn", [])
            cg = self.aux["coinglass"].get(key) or []
            close = float(F["close"].iloc[-1])
            levels["liq_up"] = [x["price"] for x in sorted(cg, key=lambda x: -x["intensity"])[:5] if x["price"] > close]
            levels["liq_dn"] = [x["price"] for x in sorted(cg, key=lambda x: -x["intensity"])[:5] if x["price"] < close]
        return live, levels

    # ------------------------------------------------------------ execution
    def execute(self, dec, kind: str, equity: float) -> str:
        plan = dec.plan
        assets = ({"BTCUSDT": plan.direction, "ETHUSDT": -plan.direction} if kind == "pair"
                  else {plan.symbol: plan.direction})
        corr = 0.85
        if {"BTCUSDT", "ETHUSDT"} <= set(self.features):
            rb = np.log(self.features["BTCUSDT"]["close"]).diff()
            re = np.log(self.features["ETHUSDT"]["close"]).diff()
            corr = float(rb.tail(int(self.cfg.get_path("risk.correlation_window", 720))).corr(re.tail(720)))
        rd = self.risk.evaluate_new(equity, plan.symbol, kind, plan.direction, assets, self.pm.open_risks(),
                                    risk_factor=plan.risk_factor, correlation=corr if np.isfinite(corr) else 0.85)
        if not rd.allowed:
            return f"odrzucone przez risk manager: {rd.reason}"
        try:
            if kind == "single":
                return self._execute_single(plan, rd.risk_budget, equity, dec.score)
            return self._execute_pair(plan, rd.risk_budget, equity, dec.score)
        except Exception as exc:  # noqa: BLE001
            log.exception("Błąd egzekucji %s: %s", plan.symbol, exc)
            self.notifier.send(f"⚠️ Błąd egzekucji {plan.symbol}: {str(exc)[:300]}")
            return f"błąd egzekucji: {exc}"

    def _data_price(self, sym: str) -> float:
        p = self.ws.last_price(sym) if self.ws is not None else None
        return p or self.market.get_ticker(sym)["lastPrice"]

    def _execute_single(self, plan, budget: float, equity: float, score: float) -> str:
        sym = plan.symbol
        tpc = self.cfg.get_path("exits.tp", {})
        rcfg = self.cfg.get("risk", {})
        exec_px = self.executor.last_price(sym)
        scale = 1.0
        if self.cross_venue:
            scale = exec_px / self._data_price(sym)
            plan = plan.rescaled(scale)
        d = plan.direction
        sl = self.executor.round_price(sym, plan.sl, "down" if d == 1 else "up")
        if d * (exec_px - sl) <= 0:
            return "pominięte: cena już za SL"
        r2 = d * (plan.tps[1] - exec_px) / (d * (exec_px - sl))
        if r2 < float(tpc.get("min_rr", 2.0)):
            return f"pominięte: R:R po cenie bieżącej {r2:.2f} < min"
        inst = self.executor.instrument(sym)
        size = position_size(equity, exec_px, sl, 0.01, rcfg["fees"]["taker"], rcfg["slippage"], inst["qty_step"],
                             inst["min_qty"], inst["max_qty"], inst["min_notional"], budget=budget)
        if not size.ok:
            return f"pominięte: {size.reason}"
        mmr = self.exec_rest.get_maintenance_margin(sym)
        lc = rcfg.get("leverage", {})
        lev = choose_leverage(exec_px, sl, plan.side, mmr, lc.get("max", 10), lc.get("min", 1),
                              lc.get("liq_safety_factor", 2.5), inst["max_leverage"], inst["leverage_step"])
        if not lev.ok:
            return f"pominięte: {lev.reason}"
        avail = self.executor.get_equity()["available"]
        if size.notional / lev.leverage > avail * 0.95:
            return f"pominięte: za mało wolnego marginu ({avail:.2f})"
        fr = plan.fractions
        partial = [(plan.tps[0], size.qty * fr[0]), (plan.tps[1], size.qty * fr[1])]
        res = self.executor.open_position(sym, plan.side, size.qty, sl, plan.tps[2], lev.leverage, partial,
                                          min_liq_gap=lc.get("liq_safety_factor", 2.5) * 0.9)
        if not res.ok:
            return f"BŁĄD: {res.reason}"
        mp = ManagedPosition(
            key=sym, kind="single", side=plan.side, entry=res.avg_price, sl=res.sl, sl_initial=res.sl,
            tps=list(plan.tps), fractions=list(fr), qty0=res.qty, qty=res.qty,
            risk_amount=size.risk_amount, atr=plan.atr, invalidation=plan.invalidation,
            entry_time=utcnow().isoformat(), score=score, rr=plan.rr, leverage=lev.leverage,
            meta={"scale": scale, "liq_price": res.liq_price, "sl_reason": plan.sl_reason,
                  "tp_reasons": plan.tp_reasons, "counter_trend": plan.counter_trend})
        self.pm.register_open(mp, self.executor._q(sym, res.qty))
        return f"OK: {plan.side} {res.qty} @ {res.avg_price}, SL {res.sl}, TP {plan.tps}, lev {lev.leverage}x"

    def _execute_pair(self, plan, budget: float, equity: float, score: float) -> str:
        rcfg = self.cfg.get("risk", {})
        pc = self.cfg.get_path("instruments.pair", {})
        d = plan.direction
        pb, pe = self.executor.last_price("BTCUSDT"), self.executor.last_price("ETHUSDT")
        ratio = pb / pe
        scale = 1.0
        if self.cross_venue:
            scale = ratio / (self._data_price("BTCUSDT") / self._data_price("ETHUSDT"))
            plan = plan.rescaled(scale)
        if d * (ratio - plan.sl) <= 0:
            return "pominięte: ratio już za SL"
        r2 = d * (plan.tps[1] - ratio) / (d * (ratio - plan.sl))
        if r2 < float(self.cfg.get_path("exits.tp.min_rr", 2.0)):
            return f"pominięte: R:R po cenie bieżącej {r2:.2f} < min"
        ib, ie = self.executor.instrument("BTCUSDT"), self.executor.instrument("ETHUSDT")
        ps = pair_size(equity, ratio, plan.sl, 0.01, pb, pe, rcfg["fees"]["taker"], rcfg["slippage"], ib["qty_step"],
                       ie["qty_step"], ib["min_qty"], ie["min_qty"], budget=budget)
        if not ps.ok:
            return f"pominięte: {ps.reason}"
        buy_sym, sell_sym = ("BTCUSDT", "ETHUSDT") if d == 1 else ("ETHUSDT", "BTCUSDT")
        price = {"BTCUSDT": pb, "ETHUSDT": pe}
        qty = {"BTCUSDT": ps.qty_long, "ETHUSDT": ps.qty_short}
        atr4 = {s: float(self.features[s]["h4_atr"].iloc[-1]) * (price[s] / float(self.features[s]["close"].iloc[-1]))
                for s in ("BTCUSDT", "ETHUSDT")}
        sl_buy, sl_sell = pair_hard_stops(d, ratio, plan.sl, price[buy_sym], price[sell_sym], atr4[buy_sym],
                                          atr4[sell_sym], pc.get("hard_stop_mult", 4.0), pc.get("hard_stop_atr4h_mult", 3.0))
        lc = rcfg.get("leverage", {})
        legs, opened = [], []
        for sym, side, hard in ((buy_sym, "long", sl_buy), (sell_sym, "short", sl_sell)):
            inst = self.executor.instrument(sym)
            lev = choose_leverage(price[sym], hard, side, self.exec_rest.get_maintenance_margin(sym), lc.get("max", 10),
                                  lc.get("min", 1), lc.get("liq_safety_factor", 2.5), inst["max_leverage"],
                                  inst["leverage_step"])
            res = self.executor.open_position(sym, side, qty[sym], hard, None, lev.leverage,
                                              min_liq_gap=lc.get("liq_safety_factor", 2.5) * 0.9, tag="pair")
            if not res.ok:
                for o in opened:  # nie zostawiamy nogi bez pary
                    self.executor.close_position(o["symbol"], o["side"], None, "druga noga pary nieudana")
                return f"BŁĄD pary ({sym}): {res.reason}"
            leg = {"symbol": sym, "side": side, "qty0": res.qty, "qty": res.qty, "entry": res.avg_price,
                   "hard_sl": res.sl, "leverage": lev.leverage}
            opened.append(leg)
            legs.append(leg)
        legs.sort(key=lambda x: x["symbol"])  # BTC, ETH
        entry_ratio = next(l["entry"] for l in legs if l["symbol"] == "BTCUSDT") / \
            next(l["entry"] for l in legs if l["symbol"] == "ETHUSDT")
        mp = ManagedPosition(
            key=PAIR_KEY, kind="pair", side=plan.side, entry=entry_ratio, sl=plan.sl, sl_initial=plan.sl,
            tps=list(plan.tps), fractions=list(plan.fractions), qty0=1.0, qty=1.0, risk_amount=ps.risk_amount,
            atr=plan.atr, invalidation=plan.invalidation, entry_time=utcnow().isoformat(), legs=legs, score=score,
            rr=plan.rr, meta={"scale": scale})
        self.pm.register_open(mp, f"{legs[0]['qty']} BTC / {legs[1]['qty']} ETH")
        return f"OK: para {plan.side} BTC/ETH @ {entry_ratio:.5f}, SL {plan.sl:.5f}, nogi {legs}"

    # ------------------------------------------------------------ main loop
    def run(self, once: bool = False) -> None:
        self.startup()
        delay = self.cfg.get_path("live.decision_delay_s", 8)
        loop_s = self.cfg.get_path("live.loop_seconds", 10)
        if once:
            self.hourly_cycle()
            return
        while not self._stop.is_set():
            try:
                now = utcnow()
                bar = pd.Timestamp(now).floor("1h")
                if (self.last_bar is None or bar > self.last_bar) and (now - bar.to_pydatetime()).total_seconds() >= delay:
                    self.last_bar = bar
                    self.hourly_cycle()
                else:
                    self.pm.sync(self._latest_rows())
                    eq = safe_call(self.executor.get_equity, log=log, what="saldo")
                    if eq:
                        self.risk.update_equity(eq["equity"], utcnow())
                        self.state.data["equity"] = eq
                        self.state.data["risk"] = self.risk.to_dict()
                        self.state.data["risk_status"] = self.risk.loss_status()
                        self.state.save()
            except BybitAPIError as exc:
                log.error("Błąd API Bybit: %s", exc)
            except Exception as exc:  # noqa: BLE001
                log.exception("Błąd pętli: %s", exc)
                self.notifier.send(f"⚠️ Błąd pętli bota: {str(exc)[:300]}")
            self._stop.wait(loop_s)

    def stop(self, *_):
        log.info("Zatrzymywanie bota...")
        self._stop.set()
        if self.ws is not None:
            safe_call(self.ws.stop, log=log, what="ws stop")


def main(argv=None) -> None:
    p = argparse.ArgumentParser(description="Bybit USDT-Perp trading bot")
    p.add_argument("--once", action="store_true", help="jeden cykl analizy i koniec")
    p.add_argument("--config", default=None)
    args = p.parse_args(argv)
    cfg = load_config(args.config)
    setup_logging(cfg.get_path("logging.level", "INFO"), cfg.get_path("logging.dir", "logs"))
    try:
        bot = TradingBot(cfg)
    except RuntimeError as exc:
        log.error("%s", exc)
        raise SystemExit(2) from None
    signal.signal(signal.SIGINT, bot.stop)
    signal.signal(signal.SIGTERM, bot.stop)
    try:
        bot.run(once=args.once)
    except (BybitAPIError, RuntimeError) as exc:
        log.error("Bot zatrzymany: %s", exc)
        bot.notifier.send(f"⛔ Bot zatrzymany: {str(exc)[:300]}")
        raise SystemExit(1) from None


if __name__ == "__main__":
    main()
