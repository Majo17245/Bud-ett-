"""Testy jednostkowe modułu ryzyka i wyliczania wielkości pozycji."""
from datetime import datetime, timedelta, timezone

import pytest

from config.settings import Config, enforce_hard_limits, load_config
from risk.manager import OpenRisk, RiskManager
from risk.sizing import choose_leverage, isolated_liq_price, loss_per_unit, pair_size, position_size

TAKER, SLIP = 0.00055, 0.0005


@pytest.fixture
def cfg():
    return load_config()


# ----------------------------------------------------------------- sizing
def test_risk_never_exceeds_one_percent_including_costs():
    res = position_size(10_000, 60_000, 59_000, 0.01, TAKER, SLIP, qty_step=0.001, min_qty=0.001)
    assert res.ok
    assert res.risk_amount <= 100.0 + 1e-9
    # strata przy SL liczona niezależnie: ruch ceny + koszty wejścia i wyjścia
    loss = res.qty * (1000 + 60_000 * (TAKER + SLIP) + 59_000 * (TAKER + SLIP))
    assert loss == pytest.approx(res.risk_amount)
    assert loss <= 100.0


def test_size_formula_matches_spec():
    # (kapitał x 0.01) / odległość do SL (z prowizjami i poślizgiem)
    lpu = loss_per_unit(2000, 1950, TAKER, SLIP)
    res = position_size(5_000, 2000, 1950, 0.01, TAKER, SLIP, qty_step=0.01, min_qty=0.01)
    assert res.qty == pytest.approx(int(50 / lpu * 100) / 100)
    assert lpu > 50  # koszty zwiększają stratę na jednostkę


def test_fees_reduce_position_size():
    no_cost = position_size(10_000, 100, 98, 0.01, 0, 0, qty_step=0.01, min_qty=0.01)
    with_cost = position_size(10_000, 100, 98, 0.01, TAKER, SLIP, qty_step=0.01, min_qty=0.01)
    assert with_cost.qty < no_cost.qty


def test_short_position_size_symmetric():
    res = position_size(10_000, 60_000, 61_000, 0.01, TAKER, SLIP, qty_step=0.001, min_qty=0.001)
    assert res.ok and res.risk_amount <= 100


def test_qty_rounded_down_to_step():
    res = position_size(10_000, 60_000, 59_000, 0.01, TAKER, SLIP, qty_step=0.001, min_qty=0.001)
    assert abs(res.qty * 1000 - round(res.qty * 1000)) < 1e-9


def test_below_min_qty_rejected():
    res = position_size(10, 60_000, 59_000, 0.01, TAKER, SLIP, qty_step=0.001, min_qty=0.001)
    assert not res.ok and res.qty == 0


def test_risk_above_one_percent_raises():
    with pytest.raises(ValueError):
        position_size(10_000, 100, 99, 0.02, TAKER, SLIP)


def test_budget_caps_risk():
    res = position_size(10_000, 100, 98, 0.01, TAKER, SLIP, qty_step=0.01, min_qty=0.01, budget=40)
    assert res.risk_amount <= 40


def test_pair_size_equal_notional_and_risk():
    ps = pair_size(10_000, 25.0, 25.5, 0.0075, 60_000, 2_400, TAKER, SLIP, 0.001, 0.01, 0.001, 0.01)
    assert ps.ok
    n_long, n_short = ps.qty_long * 60_000, ps.qty_short * 2_400
    assert abs(n_long - n_short) / n_long < 0.05
    assert ps.risk_amount <= 75 * 1.05


# --------------------------------------------------------------- leverage
@pytest.mark.parametrize("side,entry,sl", [("long", 60_000, 58_800), ("short", 60_000, 61_200),
                                           ("long", 2_000, 1_900), ("short", 2_000, 2_150)])
def test_liquidation_far_beyond_stop(side, entry, sl):
    lev = choose_leverage(entry, sl, side, mmr=0.005, max_lev=10, safety=2.5)
    assert lev.ok
    sl_dist = abs(entry - sl) / entry
    assert lev.liq_distance >= 2.5 * sl_dist * 0.999
    if side == "long":
        assert lev.liq_price < sl
    else:
        assert lev.liq_price > sl


def test_leverage_capped_by_config():
    lev = choose_leverage(60_000, 59_900, "long", mmr=0.005, max_lev=10, safety=2.5)
    assert lev.leverage <= 10


def test_isolated_liq_price():
    assert isolated_liq_price(100, 10, "long", 0.005) == pytest.approx(90.5)
    assert isolated_liq_price(100, 10, "short", 0.005) == pytest.approx(109.5)


# ----------------------------------------------------------- risk manager
def _rm(cfg):
    rm = RiskManager(cfg)
    rm.update_equity(10_000, datetime(2026, 1, 7, 12, tzinfo=timezone.utc))
    return rm


def test_new_position_gets_one_percent(cfg):
    rm = _rm(cfg)
    d = rm.evaluate_new(10_000, "BTCUSDT", "single", 1, {"BTCUSDT": 1}, [])
    assert d.allowed and d.risk_budget == pytest.approx(100)


def test_counter_trend_half_risk(cfg):
    rm = _rm(cfg)
    d = rm.evaluate_new(10_000, "BTCUSDT", "single", -1, {"BTCUSDT": -1}, [], risk_factor=0.5)
    assert d.allowed and d.risk_budget == pytest.approx(50)


def test_total_risk_limit_three_percent(cfg):
    rm = _rm(cfg)
    open_r = [OpenRisk("A", "single", 1, 100, {"XUSDT": 1}), OpenRisk("B", "single", -1, 100, {"YUSDT": -1}),
              OpenRisk("C", "pair", 1, 100, {"ZUSDT": 1, "WUSDT": -1})]
    rm.max_positions = 10
    d = rm.evaluate_new(10_000, "BTCUSDT", "single", 1, {"BTCUSDT": 1}, open_r, correlation=0.0)
    assert not d.allowed


def test_partial_budget_when_close_to_limit(cfg):
    rm = _rm(cfg)
    rm.max_positions = 10
    open_r = [OpenRisk("A", "single", -1, 100, {"XUSDT": -1}), OpenRisk("B", "pair", 1, 130, {"Z": 1, "W": -1})]
    d = rm.evaluate_new(10_000, "BTCUSDT", "single", 1, {"BTCUSDT": 1}, open_r, correlation=0.0)
    assert d.allowed and d.risk_budget == pytest.approx(70)
    assert rm.total_open_risk(open_r) + d.risk_budget <= 300 + 1e-9


def test_correlated_btc_eth_cluster_limited(cfg):
    rm = _rm(cfg)
    open_r = [OpenRisk("BTCUSDT", "single", 1, 100, {"BTCUSDT": 1})]
    # ETH long przy korelacji 0.85: klaster max 2% -> zostaje 100
    d = rm.evaluate_new(10_000, "ETHUSDT", "single", 1, {"ETHUSDT": 1}, open_r, correlation=0.85)
    assert d.allowed and d.risk_budget == pytest.approx(100)
    open_r.append(OpenRisk("ETHUSDT", "single", 1, 100, {"ETHUSDT": 1}))
    d2 = rm.evaluate_new(10_000, "SOLUSDT", "single", 1, {"SOLUSDT": 1}, open_r, correlation=0.85)
    assert not d2.allowed  # klaster skorelowany wyczerpany (2%)


def test_break_even_positions_free_risk(cfg):
    rm = _rm(cfg)
    open_r = [OpenRisk("BTCUSDT", "single", 1, 0.0, {"BTCUSDT": 1}),
              OpenRisk("ETHUSDT", "single", 1, 0.0, {"ETHUSDT": 1})]
    d = rm.evaluate_new(10_000, "SOLUSDT", "single", 1, {"SOLUSDT": 1}, open_r, correlation=0.85)
    assert d.allowed and d.risk_budget == pytest.approx(100)


def test_instrument_busy_blocks_pair(cfg):
    rm = _rm(cfg)
    open_r = [OpenRisk("BTCUSDT", "single", 1, 100, {"BTCUSDT": 1})]
    d = rm.evaluate_new(10_000, "BTC/ETH", "pair", 1, {"BTCUSDT": 1, "ETHUSDT": -1}, open_r)
    assert not d.allowed


def test_pair_risk_factor(cfg):
    rm = _rm(cfg)
    d = rm.evaluate_new(10_000, "BTC/ETH", "pair", 1, {"BTCUSDT": 1, "ETHUSDT": -1}, [])
    assert d.allowed and d.risk_budget == pytest.approx(75)


def test_daily_loss_limit_halts(cfg):
    rm = _rm(cfg)
    rm.update_equity(9_690, datetime(2026, 1, 7, 18, tzinfo=timezone.utc))
    halted, why = rm.halted()
    assert halted and "dzienny" in why
    d = rm.evaluate_new(9_690, "BTCUSDT", "single", 1, {"BTCUSDT": 1}, [])
    assert not d.allowed
    # nowy dzień -> handel wznowiony (tygodniowa strata 3.1% < 6%)
    rm.update_equity(9_690, datetime(2026, 1, 8, 0, 5, tzinfo=timezone.utc))
    assert not rm.halted()[0]


def test_weekly_loss_limit_halts(cfg):
    rm = RiskManager(cfg)
    start = datetime(2026, 1, 5, 1, tzinfo=timezone.utc)  # poniedziałek
    eq = 10_000.0
    for i in range(4):
        rm.update_equity(eq, start + timedelta(days=i))
        eq *= 0.98  # -2% dziennie (poniżej limitu dziennego)
        rm.update_equity(eq, start + timedelta(days=i, hours=20))
    halted, why = rm.halted()
    assert halted and "tygodniowy" in why
    rm.update_equity(eq, datetime(2026, 1, 12, 0, 30, tzinfo=timezone.utc))  # nowy tydzień
    assert not rm.halted()[0]


def test_hard_limits_cannot_be_raised(cfg):
    bad = Config(dict(cfg))
    bad["risk"] = dict(cfg["risk"], risk_per_trade=0.02)
    with pytest.raises(ValueError):
        enforce_hard_limits(bad)
    bad2 = cfg.copy_with({})
    bad2.set_path("exits.tp.min_rr", 1.5)
    with pytest.raises(ValueError):
        enforce_hard_limits(bad2)


def test_live_requires_confirmation(cfg):
    c = cfg.copy_with({})
    c["mode"] = "live"
    c["live_confirm"] = False
    with pytest.raises(ValueError):
        enforce_hard_limits(c)
