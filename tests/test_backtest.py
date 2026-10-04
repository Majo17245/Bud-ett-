"""Testy silnika backtestu: mechanika SL/TP/BE/trailing, księgowanie, brak lookahead."""
import numpy as np
import pandas as pd
import pytest

from backtest.engine import Backtester, Position
from backtest.metrics import compute_metrics
from config.settings import load_config
from data.synthetic import generate_dataset
from signals.features import build_features

TAKER, MAKER, SLIP = 0.00055, 0.0002, 0.0005


@pytest.fixture(scope="module")
def cfg():
    return load_config()


@pytest.fixture(scope="module")
def small_ds():
    return generate_dataset(years=0.6, seed=3)


def _pos(entry=100.0, sl=98.0, tps=(103.0, 104.0, 110.0), side="long", qty=10.0):
    d = 1 if side == "long" else -1
    return Position("TEST", "single", side, d, pd.Timestamp("2026-01-01", tz="UTC"), entry, sl, sl, list(tps),
                    [0.35, 0.35, 0.30], qty, qty, 25.0, 2.0, 2.5, 1.0, None, 40.0, False, watermark=entry)


def _bar(o, h, l, c):
    return {"open": o, "high": h, "low": l, "close": c}


def test_stop_loss_and_gap(cfg, small_ds):
    bt = Backtester(cfg, small_ds, include_pair=False)
    p = _pos()
    assert bt._process_single(p, _bar(99, 99.5, 97.5, 98.2), TAKER, MAKER, SLIP)
    assert p.exits[-1][0] == "stop_loss"
    assert p.exits[-1][1] == pytest.approx(98.0 * (1 - SLIP))
    p2 = _pos()
    assert bt._process_single(p2, _bar(96, 97, 95, 96.5), TAKER, MAKER, SLIP)  # luka poniżej SL
    assert p2.exits[-1][1] == pytest.approx(96.0 * (1 - SLIP))


def test_sl_before_tp_in_same_bar(cfg, small_ds):
    bt = Backtester(cfg, small_ds, include_pair=False)
    p = _pos()
    closed = bt._process_single(p, _bar(100, 103.5, 97.9, 101), TAKER, MAKER, SLIP)
    assert closed and p.exits[0][0] == "stop_loss"  # konserwatywnie


def test_tp1_then_break_even(cfg, small_ds):
    bt = Backtester(cfg, small_ds, include_pair=False)
    p = _pos()
    assert not bt._process_single(p, _bar(100, 103.2, 99.5, 102.5), TAKER, MAKER, SLIP)
    assert p.tp_hit[0] and p.qty == pytest.approx(6.5)
    assert p.be_pending
    closed = bt._process_single(p, _bar(102, 102.2, 99.0, 99.5), TAKER, MAKER, SLIP)
    assert closed and p.exits[-1][0] == "break_even"
    net = p.realized - p.fees
    assert net > 0  # TP1 + wyjście na BE (z buforem) = zysk po kosztach


def test_tp2_activates_trailing_and_tp3(cfg, small_ds):
    bt = Backtester(cfg, small_ds, include_pair=False)
    p = _pos()
    bt._process_single(p, _bar(100, 104.5, 99.8, 104.2), TAKER, MAKER, SLIP)
    assert p.tp_hit[0] and p.tp_hit[1] and p.trailing
    assert p.qty == pytest.approx(3.0)
    closed = bt._process_single(p, _bar(104.2, 110.5, 104.0, 110.2), TAKER, MAKER, SLIP)
    assert closed and p.exits[-1][0] == "tp3"


def test_short_mirror(cfg, small_ds):
    bt = Backtester(cfg, small_ds, include_pair=False)
    p = _pos(entry=100, sl=102, tps=(97, 96, 90), side="short")
    bt._process_single(p, _bar(100, 100.5, 96.8, 97.5), TAKER, MAKER, SLIP)
    assert p.tp_hit[0]
    assert p.realized > 0


def test_full_run_accounting(cfg, small_ds):
    bt = Backtester(cfg, small_ds)
    res = bt.run()
    m = compute_metrics(res)
    eq = res["equity"]["equity"]
    total = res["trades"]["pnl"].sum() if len(res["trades"]) else 0.0
    assert eq.iloc[-1] == pytest.approx(res["initial_capital"] + total, rel=1e-9)
    assert "overall" in m
    if len(res["trades"]):
        # żadna transakcja nie traci istotnie więcej niż zaplanowane ryzyko (1R + luki/funding)
        assert res["trades"]["r_multiple"].min() > -1.6
        assert (res["trades"]["planned_rr"] >= 2.0).all()


def test_daily_risk_never_exceeds_limits(cfg, small_ds):
    bt = Backtester(cfg, small_ds)
    res = bt.run()
    t = res["trades"]
    if len(t):
        assert (t["risk_amount"] <= res["initial_capital"] * 0.01 * 3).all()
        assert (t["risk_amount"] / 10_000 <= 0.0101 * 2).all()


def test_features_no_lookahead(cfg, small_ds):
    sym = small_ds["symbols"]["BTCUSDT"]
    full = build_features(sym, cfg, small_ds["macro"], small_ds["fng"])
    cut = sym["60"].index[-300]
    tr = {"60": sym["60"][sym["60"].index < cut],
          "240": sym["240"][sym["240"].index + pd.Timedelta(hours=4) <= cut],
          "D": sym["D"][sym["D"].index + pd.Timedelta(days=1) <= cut],
          "oi": sym["oi"][sym["oi"].index < cut], "funding": sym["funding"][sym["funding"].index < cut],
          "ls": sym["ls"][sym["ls"].index < cut]}
    part = build_features(tr, cfg, {k: v[v.index < cut] for k, v in small_ds["macro"].items()},
                          small_ds["fng"][small_ds["fng"].index < cut])
    t = part.index[-1]
    a, b = part.loc[t], full.loc[t]
    for c in part.columns:
        if np.issubdtype(part[c].dtype, np.number):
            if pd.isna(a[c]) and pd.isna(b[c]):
                continue
            assert np.isclose(a[c], b[c], rtol=1e-6, atol=1e-9), c
