"""Walk-forward (kroczące okna train -> test) i hold-out out-of-sample.

Dla każdego okna: na danych treningowych (np. 180 dni) wybieramy z małej siatki
parametry (próg wejścia, minimalne R:R) maksymalizujące SQN (wymagana minimalna
liczba transakcji), a następnie stosujemy je na kolejnych `test_days` dniach,
których optymalizacja nie widziała. Wynik OOS to jedna ciągła krzywa kapitału
z parametrami przełączanymi na granicach okien.
Mała siatka (8 kombinacji) i kryterium SQN ograniczają przeuczenie.
"""
from __future__ import annotations

import itertools
import logging

import numpy as np
import pandas as pd

from backtest.metrics import trade_stats

log = logging.getLogger(__name__)


def _objective(trades: pd.DataFrame, min_trades: int) -> float:
    if len(trades) < min_trades:
        return -np.inf
    st = trade_stats(trades)
    if st["profit_factor"] < 1.0:
        return st["sqn"] - 10  # ujemne, ale porównywalne
    return st["sqn"]


def walk_forward(bt, cfg) -> dict:
    wf = cfg.get_path("backtest.walk_forward", {})
    train_d = pd.Timedelta(days=int(wf.get("train_days", 180)))
    test_d = pd.Timedelta(days=int(wf.get("test_days", 60)))
    grid = wf.get("grid", {"entry.threshold": [25, 30, 35, 40], "exits.tp.min_rr": [2.0, 2.5]})
    min_trades = int(wf.get("min_trades_train", 8))
    bt.prepare()
    tl = bt.timeline
    warm = int(cfg.get_path("backtest.warmup_bars", 300))
    first = tl[min(warm, len(tl) - 1)]
    keys = list(grid)
    combos = [dict(zip(keys, vals)) for vals in itertools.product(*[grid[k] for k in keys])]
    default = {k: cfg.get_path(k) for k in keys}
    windows = []
    test_start = first + train_d
    while test_start < tl[-1]:
        test_end = min(test_start + test_d, tl[-1] + pd.Timedelta(hours=1))
        windows.append((test_start - train_d, test_start, test_end))
        test_start = test_end
    schedule, details = [], []
    for tr_start, te_start, te_end in windows:
        best, best_val = default, -np.inf
        scores = []
        for combo in combos:
            c = cfg.copy_with(combo)
            res = bt.run(c, start=tr_start, end=te_start)
            val = _objective(res["trades"], min_trades)
            scores.append((combo, val, len(res["trades"])))
            closer = sum(abs(combo[k] - default[k]) for k in keys) < sum(abs(best[k] - default[k]) for k in keys)
            if val > best_val + 1e-9 or (abs(val - best_val) <= 1e-9 and closer):
                best, best_val = combo, val
        if not np.isfinite(best_val):
            best = default  # za mało transakcji w treningu -> parametry domyślne
        schedule.append((te_start, te_end, cfg.copy_with(best)))
        details.append({"train": [str(tr_start), str(te_start)], "test": [str(te_start), str(te_end)],
                        "chosen": best, "train_objective": None if not np.isfinite(best_val) else round(best_val, 3),
                        "grid": [(s[0], None if not np.isfinite(s[1]) else round(s[1], 3), s[2]) for s in scores]})
        log.info("WF okno test %s..%s -> %s (SQN train %.2f)", te_start.date(), te_end.date(), best,
                 best_val if np.isfinite(best_val) else float("nan"))
    if not schedule:
        return {"result": None, "windows": []}
    oos = bt.run(cfg, start=schedule[0][0], end=schedule[-1][1], schedule=schedule)
    return {"result": oos, "windows": details}


def holdout_split(bt, cfg) -> tuple[pd.Timestamp, pd.Timestamp]:
    bt.prepare()
    tl = bt.timeline
    frac = float(cfg.get_path("backtest.walk_forward.holdout_fraction", 0.2))
    return tl[0], tl[int(len(tl) * (1 - frac))]
