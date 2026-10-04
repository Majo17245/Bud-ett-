"""Dashboard (Streamlit): wyniki backtestu, otwarte pozycje, aktualny scoring, decyzje bota.

Uruchomienie:  streamlit run dashboard/app.py
Czyta wyłącznie pliki: logs/state.json, logs/decisions.jsonl, logs/trades.jsonl, backtest/reports/.
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

import pandas as pd
import plotly.graph_objects as go
import streamlit as st

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

LOGS = ROOT / "logs"
REPORTS = ROOT / "backtest" / "reports"
BLUE, RED, GRAY = "#2a78d6", "#e34948", "#8a8984"
MODULES = ["trend", "momentum", "volume", "positioning", "orderbook", "macro", "sentiment"]

st.set_page_config(page_title="Bybit Bot", layout="wide")


def read_json(path: Path) -> dict:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except Exception:  # noqa: BLE001
        return {}


def read_jsonl(path: Path, tail: int = 300) -> list[dict]:
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()[-tail:]
    out = []
    for ln in lines:
        try:
            out.append(json.loads(ln))
        except json.JSONDecodeError:
            continue
    return out


def pct(x) -> str:
    return "-" if x is None else f"{x * 100:.2f}%"


def num(x, nd=2) -> str:
    try:
        return f"{float(x):,.{nd}f}"
    except (TypeError, ValueError):
        return "-"


def score_bars(scores: dict, title: str) -> go.Figure:
    names = [m for m in MODULES + ["composite"] if scores.get(m) is not None]
    vals = [float(scores[m]) for m in names]
    colors = [BLUE if v >= 0 else RED for v in vals]
    fig = go.Figure(go.Bar(x=vals, y=names, orientation="h", marker_color=colors,
                           text=[f"{v:+.0f}" for v in vals], textposition="outside",
                           hovertemplate="%{y}: %{x:.1f}<extra></extra>"))
    fig.add_vline(x=0, line_color=GRAY, line_width=1)
    fig.update_layout(title=title, height=320, margin=dict(l=10, r=30, t=40, b=10),
                      xaxis=dict(range=[-110, 110], title="← short   ocena   long →", showgrid=True,
                                 gridcolor="rgba(128,128,128,0.15)"),
                      yaxis=dict(autorange="reversed"), showlegend=False, bargap=0.35)
    return fig


def line_fig(series: pd.Series, title: str, color: str, yfmt: str = ",.0f", fill: bool = False) -> go.Figure:
    fig = go.Figure(go.Scatter(x=series.index, y=series.values, mode="lines", line=dict(color=color, width=2),
                               fill="tozeroy" if fill else None,
                               hovertemplate="%{x|%Y-%m-%d %H:%M}<br>%{y:" + yfmt + "}<extra></extra>"))
    fig.update_layout(title=title, height=300, margin=dict(l=10, r=10, t=40, b=10), showlegend=False,
                      hovermode="x", xaxis=dict(showgrid=False),
                      yaxis=dict(gridcolor="rgba(128,128,128,0.15)", tickformat=yfmt))
    return fig


# ---------------------------------------------------------------- nagłówek
state = read_json(LOGS / "state.json")
st.title("Bybit USDT-Perp Bot")
c1, c2, c3, c4 = st.columns(4)
eq = state.get("equity") or {}
rs = state.get("risk_status") or {}
c1.metric("Kapitał [USDT]", num(eq.get("equity")))
c2.metric("Strata dzienna / limit", f"{pct(rs.get('day_loss'))} / {pct(rs.get('day_limit'))}")
c3.metric("Strata tygodniowa / limit", f"{pct(rs.get('week_loss'))} / {pct(rs.get('week_limit'))}")
halted = rs.get("halted_day") or rs.get("halted_week")
c4.metric("Nowe pozycje", "⛔ wstrzymane" if halted else "✅ dozwolone")
st.caption(f"Ostatni cykl: {state.get('last_cycle', '-')} · aktualizacja stanu: {state.get('updated', '-')}"
           if state else "Brak logs/state.json - bot jeszcze nie był uruchomiony.")

tab_live, tab_dec, tab_bt = st.tabs(["Pozycje i scoring", "Decyzje bota", "Backtest"])

# ---------------------------------------------------------------- live
with tab_live:
    st.subheader("Otwarte pozycje")
    pos = state.get("positions") or {}
    if pos:
        rows = []
        for k, p in pos.items():
            rows.append({"instrument": k, "kierunek": p["side"], "typ": p["kind"], "wejście": p["entry"],
                         "SL": p["sl"], "TP1": p["tps"][0], "TP2": p["tps"][1], "TP3": p["tps"][2],
                         "ilość": p["qty"], "ryzyko USDT": round(p["risk_amount"], 2), "R:R": p.get("rr"),
                         "TP trafione": sum(p.get("tp_hit", [])), "trailing": p.get("trailing"),
                         "przejęta": p.get("adopted"), "od": p.get("entry_time", "")[:16]})
        st.dataframe(pd.DataFrame(rows), use_container_width=True, hide_index=True)
    else:
        st.info("Brak otwartych pozycji.")
    st.subheader("Aktualny scoring (-100 short ... +100 long)")
    scores = state.get("scores") or {}
    if scores:
        cols = st.columns(len(scores))
        for col, (k, s) in zip(cols, scores.items()):
            with col:
                st.plotly_chart(score_bars(s, f"{k} · {num(s.get('composite'), 1)}"), use_container_width=True)
                st.caption(f"świeca 1h: {s.get('ts', '-')[:16]} · trend 1h/4h/1d: "
                           f"{num(s.get('trend_1h'), 0)} / {num(s.get('trend_4h'), 0)} / {num(s.get('trend_1d'), 0)}")
        tbl = pd.DataFrame({k: {m: s.get(m) for m in MODULES + ["composite"]} for k, s in scores.items()}).T
        st.dataframe(tbl.round(1), use_container_width=True)
    else:
        st.info("Scoring pojawi się po pierwszym cyklu bota.")
    st.subheader("Historia transakcji (live/testnet)")
    hist = state.get("history") or []
    if hist:
        h = pd.DataFrame(hist)
        st.dataframe(h[[c for c in ("ts", "key", "side", "entry", "reason", "pnl", "r_multiple", "adopted")
                        if c in h]].iloc[::-1], use_container_width=True, hide_index=True)
    else:
        st.caption("Brak zamkniętych transakcji.")

# ---------------------------------------------------------------- decyzje
with tab_dec:
    decs = read_jsonl(LOGS / "decisions.jsonl")
    if not decs:
        st.info("Brak logs/decisions.jsonl.")
    else:
        df = pd.DataFrame([{"czas świecy": d.get("ts", "")[:16], "instrument": d.get("symbol"),
                            "akcja": d.get("action"), "score": d.get("score"),
                            "powód": "; ".join(d.get("reasons", []))[:200], "egzekucja": d.get("execution", ""),
                            "ostrzeżenia": "; ".join(d.get("warnings", []))} for d in decs]).iloc[::-1]
        sym = st.selectbox("Instrument", ["wszystkie"] + sorted(df["instrument"].dropna().unique().tolist()))
        if sym != "wszystkie":
            df = df[df["instrument"] == sym]
        st.dataframe(df, use_container_width=True, hide_index=True)
        with st.expander("Ostatnia decyzja - wszystkie wartości wskaźników"):
            st.json(decs[-1])

# ---------------------------------------------------------------- backtest
with tab_bt:
    runs = sorted([p for p in REPORTS.glob("*") if p.is_dir()], reverse=True)
    if not runs:
        st.info("Brak raportów. Uruchom: python -m backtest.run")
    else:
        run = st.selectbox("Raport", runs, format_func=lambda p: p.name)
        if "synthetic" in run.name:
            st.warning("Raport na danych SYNTETYCZNYCH - test techniczny, nie ocena strategii.")
        names = [n for n in ("full", "in_sample", "holdout", "walk_forward") if (run / f"{n}_metrics.json").exists()]
        part = st.radio("Wariant", names, horizontal=True,
                        format_func=lambda n: {"full": "pełny okres", "in_sample": "in-sample",
                                               "holdout": "hold-out OOS", "walk_forward": "walk-forward OOS"}[n])
        m = read_json(run / f"{part}_metrics.json")
        o = m.get("overall", {})
        k = st.columns(6)
        k[0].metric("Zwrot", pct(o.get("total_return")))
        k[1].metric("Max DD", pct(o.get("max_drawdown")))
        k[2].metric("Sharpe", num(o.get("sharpe")))
        k[3].metric("Profit factor", num(o.get("profit_factor")))
        k[4].metric("Win rate", pct(o.get("win_rate")))
        k[5].metric("Transakcje", o.get("trades", 0))
        eqf = run / f"{part}_equity.csv"
        if eqf.exists():
            e = pd.read_csv(eqf, index_col=0, parse_dates=True)["equity"]
            st.plotly_chart(line_fig(e, "Krzywa kapitału [USDT]", BLUE), use_container_width=True)
            dd = (e / e.cummax() - 1) * 100
            st.plotly_chart(line_fig(dd, "Drawdown [%]", RED, yfmt=".1f", fill=True), use_container_width=True)
        seg = []
        for side, s in (m.get("by_side") or {}).items():
            seg.append({"segment": side.upper(), **{x: s.get(x) for x in ("trades", "win_rate", "profit_factor",
                                                                            "avg_r", "avg_rr_realized", "net_pnl")}})
        for sym, d in (m.get("by_symbol") or {}).items():
            for side in ("all", "long", "short"):
                s = d.get(side, {})
                seg.append({"segment": f"{sym} {side}", **{x: s.get(x) for x in (
                    "trades", "win_rate", "profit_factor", "avg_r", "avg_rr_realized", "net_pnl")}})
        if seg:
            st.dataframe(pd.DataFrame(seg).round(3), use_container_width=True, hide_index=True)
        trf = run / f"{part}_trades.csv"
        if trf.exists():
            with st.expander("Transakcje"):
                st.dataframe(pd.read_csv(trf), use_container_width=True)
        if (run / "report.md").exists():
            with st.expander("Pełny raport (markdown)"):
                st.markdown((run / "report.md").read_text(encoding="utf-8"))
