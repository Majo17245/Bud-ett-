"""Testy egzekucji i bota live na atrapie Bybit V5 (offline)."""
from datetime import datetime, timezone

import pytest

from config.settings import load_config
from data.bybit_client import BybitREST
from data.synthetic import generate_dataset
from execution import testnet_check
from execution.bybit_exec import BybitExecutor
from execution.live import TradingBot
from execution.position_manager import PositionManager
from execution.state import ManagedPosition, StateStore
from notifications.telegram import TelegramNotifier
from tests.fake_bybit import FakeBybitHTTP


@pytest.fixture(scope="module")
def ds():
    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    return generate_dataset(years=0.4, seed=9, end=end)


@pytest.fixture
def cfg(tmp_path):
    c = load_config()
    c = c.copy_with({"logging.state_file": str(tmp_path / "state.json"),
                     "logging.decisions_file": str(tmp_path / "decisions.jsonl"),
                     "logging.trades_file": str(tmp_path / "trades.jsonl"),
                     "filters.macro_events.fetch_calendar": False})
    return c


@pytest.fixture
def fake(ds):
    return FakeBybitHTTP(ds)


@pytest.fixture
def rest(fake):
    return BybitREST(testnet=True, session=fake, rate_per_s=1000)


def test_open_position_always_has_stop_loss(fake, rest, cfg):
    ex = BybitExecutor(rest, cfg)
    ex.setup_account(["BTCUSDT"])
    assert fake.margin_mode == "ISOLATED_MARGIN"
    px = fake.prices["BTCUSDT"]
    res = ex.open_position("BTCUSDT", "long", 0.01, px * 0.98, px * 1.06, 5,
                           partial_tps=[(px * 1.03, 0.004)], min_liq_gap=2.0)
    assert res.ok, res.reason
    order = [c for c in fake.calls if c[0] == "place_order" and c[1]["orderType"] == "Market"][0][1]
    assert "stopLoss" in order and float(order["stopLoss"]) < px
    assert "takeProfit" in order and order["tpslMode"] == "Full"
    assert order["slTriggerBy"] == "MarkPrice"
    pos = ex.position("BTCUSDT")
    assert pos["sl"] > 0 and pos["liq_price"] < pos["sl"]
    assert any(o["reduceOnly"] for o in fake.orders)


def test_refuses_order_without_sl(rest, cfg):
    ex = BybitExecutor(rest, cfg)
    res = ex.open_position("BTCUSDT", "long", 0.01, 0, None, 5)
    assert not res.ok and "SL" in res.reason


def test_closes_when_liquidation_too_close(fake, rest, cfg):
    ex = BybitExecutor(rest, cfg)
    px = fake.prices["ETHUSDT"]
    res = ex.open_position("ETHUSDT", "long", 1.0, px * 0.95, None, 50, min_liq_gap=2.0)
    assert not res.ok and "likwidacja" in res.reason
    assert "ETHUSDT" not in fake.positions


def _pm(rest, cfg, notifier=None):
    ex = BybitExecutor(rest, cfg)
    st = StateStore(cfg.get_path("logging.state_file"))
    return PositionManager(ex, st, cfg, notifier or TelegramNotifier(None, None)), ex, st


def test_adopt_position_without_sl_after_restart(fake, rest, cfg):
    px = fake.prices["BTCUSDT"]
    fake.place_order("linear", "BTCUSDT", "Buy", "Market", "0.010")  # pozycja otwarta "ręcznie", bez SL
    assert fake.positions["BTCUSDT"]["stopLoss"] == 0
    pm, ex, st = _pm(rest, cfg)
    pm.sync({})
    assert fake.positions["BTCUSDT"]["stopLoss"] > 0
    assert fake.positions["BTCUSDT"]["stopLoss"] < px
    assert "BTCUSDT" in st.positions() and st.positions()["BTCUSDT"].adopted


def test_tp1_moves_sl_to_break_even_and_restore_missing_sl(fake, rest, cfg):
    pm, ex, st = _pm(rest, cfg)
    px = fake.prices["BTCUSDT"]
    sl, tp1, tp2, tp3 = px * 0.98, px * 1.03, px * 1.05, px * 1.1
    res = ex.open_position("BTCUSDT", "long", 0.02, sl, tp3, 5, partial_tps=[(tp1, 0.007), (tp2, 0.007)])
    assert res.ok
    st.put(ManagedPosition("BTCUSDT", "single", "long", res.avg_price, res.sl, res.sl, [tp1, tp2, tp3],
                           [0.35, 0.35, 0.3], res.qty, res.qty, 10.0, px * 0.005, None,
                           datetime.now(timezone.utc).isoformat()))
    # usunięcie SL "z zewnątrz" -> bot przywraca
    fake.positions["BTCUSDT"]["stopLoss"] = 0.0
    pm.sync({})
    assert fake.positions["BTCUSDT"]["stopLoss"] == pytest.approx(res.sl)
    # TP1
    fake.set_price("BTCUSDT", tp1 * 1.001)
    pm.sync({})
    mp = st.positions()["BTCUSDT"]
    assert mp.tp_hit[0]
    assert fake.positions["BTCUSDT"]["stopLoss"] > res.avg_price  # break-even + bufor
    # TP2 -> trailing
    fake.set_price("BTCUSDT", tp2 * 1.001)
    pm.sync({})
    assert st.positions()["BTCUSDT"].trailing
    assert fake.positions["BTCUSDT"]["trailingStop"] > 0
    # spadek -> trailing stop zamyka pozycję, bot rozlicza
    fake.set_price("BTCUSDT", px * 0.99)
    pm.sync({})
    assert "BTCUSDT" not in st.positions()
    assert st.data["history"][-1]["key"] == "BTCUSDT"


def _bot(ds, cfg, fake, notifier=None):
    rest = BybitREST(testnet=True, session=fake, rate_per_s=1000)

    class NoCross:
        def fetch_ohlcv(self, *a, **k):
            return {}

        def fetch_orderbooks(self, *a, **k):
            return {}

    class NoCG:
        enabled = False

    return TradingBot(cfg, env={}, exec_rest=rest, market_rest=rest, ws=None, cross=NoCross(), coinglass=NoCG(),
                      notifier=notifier or TelegramNotifier(None, None), enable_ws=False,
                      aux_loaders={"macro": lambda: ds["macro"], "fng": lambda: ds["fng"]})


def test_bot_hourly_cycle_end_to_end(ds, cfg, fake):
    bot = _bot(ds, cfg, fake)
    bot.startup()
    decisions = bot.hourly_cycle()
    keys = {d["symbol"] for d in decisions}
    assert keys == {"BTCUSDT", "ETHUSDT", "BTC/ETH"}
    for d in decisions:
        assert "modules" in d and "checks" in d and "indicators" in d
    # każda otwarta pozycja ma SL na giełdzie
    for sym, p in fake.positions.items():
        assert p["stopLoss"] > 0
    import json
    lines = open(cfg.get_path("logging.decisions_file"), encoding="utf-8").read().splitlines()
    assert len(lines) == 3 and json.loads(lines[0])["type"] == "decision"


def test_bot_executes_forced_signal_with_sl_tp(ds, cfg, fake):
    c = cfg.copy_with({"entry.threshold": 0.0, "entry.min_agreeing_modules": 0, "entry.max_strong_opposing": 9,
                       "entry.require_1h_trigger": False, "entry.structure_min": -100, "entry.strong_threshold": 0,
                       "filters.min_rvol": 0.0, "filters.max_atr_percentile": 1.01, "filters.max_bar_range_atr": 99,
                       "entry.regime_threshold": 1000})
    notifier = TelegramNotifier(None, None)
    bot = _bot(ds, c, fake, notifier)
    bot.startup()
    decisions = bot.hourly_cycle()
    executed = [d for d in decisions if str(d.get("execution", "")).startswith("OK")]
    rejected = [d.get("execution") for d in decisions if d.get("execution")]
    assert executed or rejected, decisions
    for sym, p in fake.positions.items():
        assert p["stopLoss"] > 0, sym
    if executed:
        assert any("OTWARCIE" in m for m in notifier.sent)
        st = StateStore(c.get_path("logging.state_file"))
        assert st.positions()


def test_pair_second_leg_failure_closes_first(ds, cfg, fake):
    bot = _bot(ds, cfg, fake)
    bot.startup()
    bot.analyze()
    from signals.levels import TradePlan
    r = fake.prices["BTCUSDT"] / fake.prices["ETHUSDT"]
    plan = TradePlan("BTC/ETH", "long", r, r * 0.98, [r * 1.03, r * 1.05, r * 1.08], [0.35, 0.35, 0.3],
                     [1.5, 2.5, 4.0], 2.5, 2.6, r * 0.005, None, "test", ["a", "b", "c"], kind="pair")
    fake.reject_symbols.add("ETHUSDT")
    out = bot._execute_pair(plan, 75.0, 10_000, 40.0)
    assert out.startswith("BŁĄD")
    assert "BTCUSDT" not in fake.positions and "ETHUSDT" not in fake.positions
    fake.reject_symbols.clear()
    out = bot._execute_pair(plan, 75.0, 10_000, 40.0)
    assert out.startswith("OK"), out
    assert fake.positions["BTCUSDT"]["stopLoss"] > 0 and fake.positions["ETHUSDT"]["stopLoss"] > 0
    assert fake.positions["BTCUSDT"]["side"] == "Buy" and fake.positions["ETHUSDT"]["side"] == "Sell"
    # twardy SL jednej nogi -> bot zamyka drugą
    fake.set_price("ETHUSDT", fake.positions["ETHUSDT"]["stopLoss"] * 1.001)
    assert "ETHUSDT" not in fake.positions
    bot.pm.sync({})
    assert "BTCUSDT" not in fake.positions
    assert "BTC/ETH" not in bot.state.positions()


def test_testnet_check_against_fake(fake, rest, cfg):
    rep = testnet_check.run(rest, cfg, pair=True)
    assert rep.ok, rep.rows
