"""Metryki backtestu i raport (całość, long/short, każda para osobno)."""
from __future__ import annotations

import numpy as np
import pandas as pd


def trade_stats(t: pd.DataFrame) -> dict:
    n = len(t)
    if n == 0:
        return {"trades": 0}
    pnl = t["pnl"]
    r = t["r_multiple"]
    wins, losses = t[pnl > 0], t[pnl <= 0]
    gross_win, gross_loss = wins["pnl"].sum(), -losses["pnl"].sum()
    avg_win_r = wins["r_multiple"].mean() if len(wins) else 0.0
    avg_loss_r = losses["r_multiple"].mean() if len(losses) else 0.0
    return {
        "trades": int(n),
        "win_rate": float(len(wins) / n),
        "net_pnl": float(pnl.sum()),
        "profit_factor": float(gross_win / gross_loss) if gross_loss > 0 else float("inf"),
        "avg_r": float(r.mean()),
        "expectancy_r": float(r.mean()),
        "avg_win_r": float(avg_win_r),
        "avg_loss_r": float(avg_loss_r),
        "avg_rr_realized": float(avg_win_r / abs(avg_loss_r)) if avg_loss_r < 0 else float("inf"),
        "avg_rr_planned": float(t["planned_rr"].mean()),
        "avg_rr_planned_blended": float(t["planned_rr_blended"].mean()),
        "sqn": float(r.mean() / r.std() * np.sqrt(n)) if n > 1 and r.std() > 0 else 0.0,
        "fees": float(t["fees"].sum()),
        "funding": float(t["funding"].sum()),
        "avg_bars": float(t["bars"].mean()),
        "best_r": float(r.max()),
        "worst_r": float(r.min()),
        "counter_trend_trades": int(t["counter_trend"].sum()),
        "exit_reasons": t["exit_reason"].str.split(":").str[0].value_counts().to_dict(),
    }


def equity_stats(eq: pd.DataFrame, capital: float) -> dict:
    if eq is None or eq.empty:
        return {}
    e = eq["equity"]
    total_ret = e.iloc[-1] / capital - 1
    days = max(1e-9, (e.index[-1] - e.index[0]).total_seconds() / 86400)
    cagr = (e.iloc[-1] / capital) ** (365 / days) - 1 if e.iloc[-1] > 0 else -1.0
    peak = e.cummax()
    dd = e / peak - 1
    daily = e.resample("1D").last().dropna()
    dr = daily.pct_change().dropna()
    sharpe = float(dr.mean() / dr.std() * np.sqrt(365)) if len(dr) > 2 and dr.std() > 0 else 0.0
    downside = dr[dr < 0]
    sortino = float(dr.mean() / downside.std() * np.sqrt(365)) if len(downside) > 2 and downside.std() > 0 else 0.0
    max_dd = float(dd.min())
    return {
        "start": str(e.index[0]), "end": str(e.index[-1]), "days": round(days, 1),
        "initial_capital": capital, "final_equity": float(e.iloc[-1]),
        "total_return": float(total_ret), "cagr": float(cagr), "max_drawdown": max_dd,
        "sharpe": sharpe, "sortino": sortino, "calmar": float(cagr / abs(max_dd)) if max_dd < 0 else float("inf"),
        "exposure": float((eq["positions"] > 0).mean()),
    }


def compute_metrics(result: dict) -> dict:
    t = result["trades"]
    out = {"overall": {**equity_stats(result["equity"], result["initial_capital"]),
                       **trade_stats(t)} if len(t) else equity_stats(result["equity"], result["initial_capital"])}
    out["counts"] = result.get("counts", {})
    if len(t) == 0:
        out["overall"]["trades"] = 0
        return out
    out["by_side"] = {s: trade_stats(t[t["side"] == s]) for s in ("long", "short")}
    out["by_symbol"] = {sym: {"all": trade_stats(g), "long": trade_stats(g[g["side"] == "long"]),
                              "short": trade_stats(g[g["side"] == "short"])}
                        for sym, g in t.groupby("symbol")}
    return out


def _fmt(v, pct=False, nd=2):
    if v is None:
        return "-"
    if isinstance(v, float):
        if np.isinf(v):
            return "inf"
        return f"{v * 100:.{nd}f}%" if pct else f"{v:.{nd}f}"
    return str(v)


def metrics_table(m: dict) -> str:
    rows = [("Liczba transakcji", m.get("trades")), ("Win rate", _fmt(m.get("win_rate"), True)),
            ("Profit factor", _fmt(m.get("profit_factor"))), ("Średni wynik [R]", _fmt(m.get("avg_r"))),
            ("Średni zysk / strata [R]", f"{_fmt(m.get('avg_win_r'))} / {_fmt(m.get('avg_loss_r'))}"),
            ("Średnie R:R zrealizowane", _fmt(m.get("avg_rr_realized"))),
            ("Średnie R:R planowane (TP2 / blended)",
             f"{_fmt(m.get('avg_rr_planned'))} / {_fmt(m.get('avg_rr_planned_blended'))}"),
            ("Wynik netto [USDT]", _fmt(m.get("net_pnl"))), ("Prowizje [USDT]", _fmt(m.get("fees"))),
            ("Funding [USDT]", _fmt(m.get("funding"))), ("SQN", _fmt(m.get("sqn")))]
    if "total_return" in m:
        rows = [("Okres", f"{m['start'][:10]} -> {m['end'][:10]} ({m['days']:.0f} dni)"),
                ("Zwrot całkowity", _fmt(m["total_return"], True)), ("CAGR", _fmt(m["cagr"], True)),
                ("Max drawdown", _fmt(m["max_drawdown"], True)), ("Sharpe (dzienny, ann.)", _fmt(m["sharpe"])),
                ("Sortino", _fmt(m["sortino"])), ("Ekspozycja (czas w rynku)", _fmt(m["exposure"], True))] + rows
    lines = ["| Metryka | Wartość |", "|---|---|"] + [f"| {a} | {b} |" for a, b in rows]
    return "\n".join(lines)


def short_row(name: str, m: dict) -> str:
    if not m or not m.get("trades"):
        return f"| {name} | 0 | - | - | - | - | - |"
    return (f"| {name} | {m['trades']} | {_fmt(m['win_rate'], True, 1)} | {_fmt(m['profit_factor'])} | "
            f"{_fmt(m['avg_r'])} | {_fmt(m['avg_rr_realized'])} | {_fmt(m['net_pnl'])} |")


def render_report(title: str, m: dict, notes: str = "") -> str:
    out = [f"## {title}", ""]
    if notes:
        out += [notes, ""]
    out += [metrics_table(m["overall"]), ""]
    if "by_side" in m:
        out += ["**Podział: long / short i instrumenty**", "",
                "| Segment | Transakcje | Win rate | PF | Śr. R | R:R zreal. | PnL [USDT] |", "|---|---|---|---|---|---|---|"]
        out.append(short_row("LONG (wszystkie)", m["by_side"]["long"]))
        out.append(short_row("SHORT (wszystkie)", m["by_side"]["short"]))
        for sym, d in m["by_symbol"].items():
            out.append(short_row(f"{sym} - razem", d["all"]))
            out.append(short_row(f"{sym} - long", d["long"]))
            out.append(short_row(f"{sym} - short", d["short"]))
        er = m["overall"].get("exit_reasons", {})
        out += ["", "Powody wyjścia: " + ", ".join(f"{k}: {v}" for k, v in er.items())]
    c = m.get("counts", {})
    if c:
        out += ["", f"Sygnały: {c.get('signals', 0)}, odrzucone przez risk manager: {c.get('rejected_risk', 0)}, "
                    f"odrzucone po cenie wejścia (R:R/SL): {c.get('rejected_rr_fill', 0)}"]
        if c.get("risk_reasons"):
            out += ["", "Odrzucenia risk managera: " + ", ".join(f"{k}: {v}" for k, v in c["risk_reasons"].items())]
    return "\n".join(out) + "\n"
