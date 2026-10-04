"""Uruchomienie backtestu + walk-forward + hold-out i zapis raportu.

  python -m backtest.run                      # dane z cache (najpierw: python -m data.history)
  python -m backtest.run --source bybit       # pobierz/odśwież dane z Bybit i uruchom
  python -m backtest.run --source synthetic   # dane syntetyczne - tylko test techniczny
  python -m backtest.run --no-walk-forward
"""
from __future__ import annotations

import argparse
import json
import logging
import time
from datetime import datetime, timezone
from pathlib import Path

from backtest.engine import Backtester
from backtest.metrics import compute_metrics, render_report
from backtest.walkforward import holdout_split, walk_forward
from config.settings import load_config
from core.utils import clean_for_json, setup_logging
from data.history import load_dataset

log = logging.getLogger("backtest")
REPORTS = Path(__file__).resolve().parent / "reports"


def save_run(out_dir: Path, name: str, res: dict, metrics: dict) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    if len(res["trades"]):
        res["trades"].to_csv(out_dir / f"{name}_trades.csv", index=False)
    res["equity"].to_csv(out_dir / f"{name}_equity.csv")
    (out_dir / f"{name}_metrics.json").write_text(json.dumps(clean_for_json(metrics), indent=2, ensure_ascii=False),
                                                  encoding="utf-8")


def main(argv=None) -> dict:
    p = argparse.ArgumentParser(description="Backtest strategii Bybit USDT-Perp")
    p.add_argument("--source", choices=["cache", "bybit", "synthetic"], default="cache")
    p.add_argument("--years", type=float, default=None)
    p.add_argument("--config", default=None)
    p.add_argument("--no-walk-forward", action="store_true")
    p.add_argument("--no-pair", action="store_true")
    p.add_argument("--seed", type=int, default=7)
    args = p.parse_args(argv)
    setup_logging()
    cfg = load_config(args.config)
    years = args.years or float(cfg.get_path("backtest.years", 2.5))
    t0 = time.time()
    ds = load_dataset(cfg.get_path("backtest.symbols", ["BTCUSDT", "ETHUSDT"]), source=args.source, years=years,
                      seed=args.seed)
    bt = Backtester(cfg, ds, include_pair=not args.no_pair)
    bt.prepare()
    log.info("Cechy gotowe w %.1fs, świec 1h: %d", time.time() - t0, len(bt.timeline))

    stamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    out_dir = REPORTS / f"{stamp}_{ds['source']}"
    synthetic = ds["source"] == "synthetic"
    warn = ("> **UWAGA: dane SYNTETYCZNE** - wynik sprawdza wyłącznie poprawność techniczną pipeline'u "
            "i NIE mówi nic o skuteczności strategii na prawdziwym rynku.\n" if synthetic else "")
    md = [f"# Raport backtestu ({ds['source']}) - {stamp} UTC", "",
          warn, "Koszty: prowizja taker {:.3%}, maker {:.3%}, poślizg {:.3%} na egzekucję rynkową, funding co 8h."
          .format(cfg.get_path("risk.fees.taker"), cfg.get_path("risk.fees.maker"), cfg.get_path("risk.slippage")),
          "Moduły w backteście: trend, momentum, wolumen (CVD ze świec), pozycjonowanie (OI, funding, L/S, "
          "model klastrów likwidacji), makro, sentyment. Order book - tylko live (brak historii w API).", ""]

    full = bt.run(cfg)
    m_full = compute_metrics(full)
    save_run(out_dir, "full", full, m_full)
    md.append(render_report("1. Pełny okres - parametry domyślne", m_full))

    h_start, h_cut = holdout_split(bt, cfg)
    ins = bt.run(cfg, start=h_start, end=h_cut)
    oos = bt.run(cfg, start=h_cut)
    m_ins, m_oos = compute_metrics(ins), compute_metrics(oos)
    save_run(out_dir, "in_sample", ins, m_ins)
    save_run(out_dir, "holdout", oos, m_oos)
    md.append(render_report("2a. In-sample (pierwsze 80%)", m_ins))
    md.append(render_report("2b. Hold-out out-of-sample (ostatnie 20%, nieużywane do doboru parametrów)", m_oos))

    wf_details = []
    m_wf = None
    if not args.no_walk_forward:
        wf = walk_forward(bt, cfg)
        if wf["result"] is not None:
            m_wf = compute_metrics(wf["result"])
            save_run(out_dir, "walk_forward", wf["result"], m_wf)
            wf_details = wf["windows"]
            (out_dir / "walk_forward_windows.json").write_text(
                json.dumps(clean_for_json(wf_details), indent=2, ensure_ascii=False), encoding="utf-8")
            notes = "Parametry wybierane na 180 dniach treningu, testowane na kolejnych 60 dniach:\n\n" + "\n".join(
                f"- test {w['test'][0][:10]} -> {w['test'][1][:10]}: {w['chosen']} (SQN train: {w['train_objective']})"
                for w in wf_details)
            md.append(render_report("3. Walk-forward out-of-sample", m_wf, notes))
    report = "\n".join(md)
    (out_dir / "report.md").write_text(report, encoding="utf-8")
    summary = {"dir": str(out_dir), "source": ds["source"], "full": m_full["overall"], "holdout": m_oos["overall"],
               "walk_forward": m_wf["overall"] if m_wf else None, "generated": stamp}
    (REPORTS / "latest.json").write_text(json.dumps(clean_for_json(summary), indent=2, ensure_ascii=False),
                                         encoding="utf-8")
    print(report)
    log.info("Raport zapisany: %s (%.1fs)", out_dir / "report.md", time.time() - t0)
    return summary


if __name__ == "__main__":
    main()
