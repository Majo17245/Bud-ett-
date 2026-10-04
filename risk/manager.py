"""Zarządzanie ryzykiem portfela - zasady nienaruszalne.

  - max 1% kapitału ryzyka na pozycję (x0.5 przeciw trendowi 1d, x0.75 para BTC/ETH)
  - max 3% łącznego ryzyka otwartych pozycji (liczone liniowo - bez "zysku z dywersyfikacji",
    bo w krachu korelacje BTC/ETH -> 1)
  - klaster skorelowany: pozycje w TYM SAMYM kierunku na BTC i ETH (korelacja >= 0.6)
    liczone razem, max 2% - BTC i ETH to w praktyce jeden zakład
  - dzienny limit straty 3% i tygodniowy 6% (od kapitału na początku dnia / tygodnia UTC,
    z niezrealizowanym PnL) - po przekroczeniu brak nowych pozycji
"""
from __future__ import annotations

from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta, timezone

from config.settings import HARD_LIMITS


@dataclass
class OpenRisk:
    key: str                 # symbol albo identyfikator pary
    kind: str                # single / pair
    direction: int           # +1 long / -1 short (dla pary: kierunek ratio)
    risk_amount: float       # bieżące ryzyko do SL (0 po przesunięciu SL na BE)
    assets: dict = field(default_factory=dict)  # {"BTCUSDT": +1, "ETHUSDT": -1}


@dataclass
class RiskDecision:
    allowed: bool
    risk_budget: float
    reason: str
    details: dict = field(default_factory=dict)


@dataclass
class LossTracker:
    day_key: str = ""
    week_key: str = ""
    day_start_equity: float = 0.0
    week_start_equity: float = 0.0
    last_equity: float = 0.0


class RiskManager:
    def __init__(self, cfg):
        r = cfg.get("risk", {})
        self.risk_per_trade = min(float(r.get("risk_per_trade", 0.01)), HARD_LIMITS["risk_per_trade"])
        self.max_total = min(float(r.get("max_total_risk", 0.03)), HARD_LIMITS["max_total_risk"])
        self.max_corr = min(float(r.get("max_correlated_risk", 0.02)), self.max_total)
        self.corr_threshold = float(r.get("correlation_threshold", 0.6))
        self.daily_limit = min(float(r.get("daily_loss_limit", 0.03)), HARD_LIMITS["daily_loss_limit"])
        self.weekly_limit = min(float(r.get("weekly_loss_limit", 0.06)), HARD_LIMITS["weekly_loss_limit"])
        self.max_positions = int(r.get("max_positions", 3))
        self.pair_factor = float(cfg.get_path("instruments.pair.risk_factor", 0.75))
        self.tracker = LossTracker()

    # ------------------------------------------------------- dzienny/tygodniowy
    @staticmethod
    def _keys(now: datetime) -> tuple[str, str]:
        now = now.astimezone(timezone.utc)
        monday = (now - timedelta(days=now.weekday())).date()
        return now.date().isoformat(), monday.isoformat()

    def update_equity(self, equity: float, now: datetime) -> None:
        day, week = self._keys(now)
        t = self.tracker
        if t.day_key != day:
            t.day_key, t.day_start_equity = day, equity
        if t.week_key != week:
            t.week_key, t.week_start_equity = week, equity
        t.last_equity = equity

    def loss_status(self) -> dict:
        t = self.tracker
        day_dd = 1 - t.last_equity / t.day_start_equity if t.day_start_equity > 0 else 0.0
        week_dd = 1 - t.last_equity / t.week_start_equity if t.week_start_equity > 0 else 0.0
        return {"day_loss": day_dd, "week_loss": week_dd, "day_limit": self.daily_limit,
                "week_limit": self.weekly_limit,
                "halted_day": day_dd >= self.daily_limit, "halted_week": week_dd >= self.weekly_limit}

    def halted(self) -> tuple[bool, str]:
        s = self.loss_status()
        if s["halted_week"]:
            return True, f"tygodniowy limit straty przekroczony ({s['week_loss']:.2%} >= {self.weekly_limit:.0%})"
        if s["halted_day"]:
            return True, f"dzienny limit straty przekroczony ({s['day_loss']:.2%} >= {self.daily_limit:.0%})"
        return False, ""

    # ------------------------------------------------------------- nowa pozycja
    def evaluate_new(self, equity: float, key: str, kind: str, direction: int, assets: dict,
                     open_risks: list[OpenRisk], risk_factor: float = 1.0, correlation: float = 0.85) -> RiskDecision:
        halted, why = self.halted()
        if halted:
            return RiskDecision(False, 0.0, why)
        if equity <= 0:
            return RiskDecision(False, 0.0, "brak kapitału")
        if any(r.key == key for r in open_risks):
            return RiskDecision(False, 0.0, f"pozycja {key} już otwarta")
        busy = {a for r in open_risks for a in r.assets}
        if busy & set(assets):
            return RiskDecision(False, 0.0, f"instrument zajęty przez inną pozycję ({busy & set(assets)})")
        if len(open_risks) >= self.max_positions:
            return RiskDecision(False, 0.0, f"limit liczby pozycji ({self.max_positions})")
        factor = risk_factor * (self.pair_factor if kind == "pair" else 1.0)
        base = equity * self.risk_per_trade * min(1.0, factor)
        total_open = sum(max(0.0, r.risk_amount) for r in open_risks)
        remaining_total = equity * self.max_total - total_open
        budget = min(base, remaining_total)
        details = {"base": base, "total_open": total_open, "remaining_total": remaining_total}
        if kind == "single" and correlation >= self.corr_threshold:
            cluster = sum(max(0.0, r.risk_amount) for r in open_risks
                          if r.kind == "single" and r.direction == direction)
            remaining_corr = equity * self.max_corr - cluster
            details.update(cluster_open=cluster, remaining_corr=remaining_corr, correlation=correlation)
            budget = min(budget, remaining_corr)
        if budget < 0.5 * base or budget <= 0:
            return RiskDecision(False, 0.0, "limit łącznego / skorelowanego ryzyka wyczerpany", details)
        return RiskDecision(True, budget, "ok", details)

    @staticmethod
    def total_open_risk(open_risks: list[OpenRisk]) -> float:
        return sum(max(0.0, r.risk_amount) for r in open_risks)

    def to_dict(self) -> dict:
        return asdict(self.tracker)

    def load(self, d: dict | None) -> None:
        if d:
            self.tracker = LossTracker(**{k: d[k] for k in asdict(LossTracker()) if k in d})
