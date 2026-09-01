"""Production-planning calculation for the demo twin.

This is the business logic that used to live in ``ProductionCalculator`` in the
standalone example. It is now a set of pure functions: given the movement
history and a set of planning parameters, it returns the plan the twin should
act on. No I/O, no MQTT, no dashboards.

Movement rows are dicts with the keys produced by the ingest endpoint:
    {"date": "2024-01-31", "inflow": <litres>, "outflow": <litres>, "stock": <litres>}
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

MIN_BATCH = 2.0  # minimal production batch, litres (Vm in the original code)


@dataclass
class PlanParams:
    forecast_days: int = 7
    weekend_factor: float = 3.0     # demand multiplier for weekends / peaks
    safety_factor: float = 0.2      # safety stock as a share of forecast demand
    recipe: dict[str, float] = field(default_factory=dict)  # units per litre

    @classmethod
    def from_dict(cls, data: dict[str, Any] | None) -> "PlanParams":
        data = data or {}
        return cls(
            forecast_days=int(data.get("forecast_days", 7)),
            weekend_factor=float(data.get("weekend_factor", 3.0)),
            safety_factor=float(data.get("safety_factor", 0.2)),
            recipe={k: float(v) for k, v in (data.get("recipe") or {}).items()},
        )


def average_daily_consumption(rows: list[dict]) -> float:
    if not rows:
        return 0.0
    total_out = sum(float(r.get("outflow", 0)) for r in rows)
    return round(total_out / len(rows), 2)


def forecasted_stock(rows: list[dict], p: PlanParams) -> float:
    daily = average_daily_consumption(rows)
    return round(daily * p.forecast_days * p.weekend_factor, 2)


def safety_stock(rows: list[dict], p: PlanParams) -> float:
    return round(p.safety_factor * forecasted_stock(rows, p), 2)


def current_stock(rows: list[dict]) -> float:
    return float(rows[-1].get("stock", 0)) if rows else 0.0


def required_production(rows: list[dict], p: PlanParams) -> float:
    demand = forecasted_stock(rows, p)
    target = -(-demand // MIN_BATCH) * MIN_BATCH  # round up to a whole batch
    needed = target - current_stock(rows)
    if needed <= 0:
        return round(MIN_BATCH, 2)
    return round(-(-needed // MIN_BATCH) * MIN_BATCH, 2)


def ingredient_requirements(volume: float, recipe: dict[str, float]) -> dict[str, float]:
    return {name: round(volume * per_litre, 2) for name, per_litre in recipe.items()}


def plan_production(rows: list[dict], params: dict | None = None) -> dict:
    """Return the full production plan for the given movement history."""
    p = PlanParams.from_dict(params)
    daily_avg = average_daily_consumption(rows)
    forecast = forecasted_stock(rows, p)
    safety = safety_stock(rows, p)
    volume = required_production(rows, p)
    return {
        "params": {
            "forecast_days": p.forecast_days,
            "weekend_factor": p.weekend_factor,
            "safety_factor": p.safety_factor,
            "recipe": p.recipe,
        },
        "daily_avg_consumption": daily_avg,
        "forecast_stock": forecast,
        "safety_stock": safety,
        "current_stock": current_stock(rows),
        "required_production": volume,
        "ingredients": ingredient_requirements(volume, p.recipe),
        "stock_ok": current_stock(rows) >= safety,
    }
