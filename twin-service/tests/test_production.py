"""Unit tests for the production-planning calculation (no DB, no network)."""
import pathlib
import sys

sys.path.insert(0, str(pathlib.Path(__file__).parents[1]))

from app.calculations.production import plan_production  # noqa: E402
from app.ingest import parse_movements  # noqa: E402

SEED = pathlib.Path(__file__).parents[1] / "seed"
INGEST_CFG = {
    "columns": {"date": "Дата", "inflow": "Приход", "outflow": "Расход", "stock": "Остаток"},
    "date_format": "%d.%m.%Y",
    "scale": 0.001,
}
PARAMS = {
    "forecast_days": 7,
    "weekend_factor": 3,
    "safety_factor": 0.2,
    "recipe": {"груши": 650, "ананас": 125, "ингредиент V": 500, "конфеты": 100},
}


def _rows():
    return parse_movements((SEED / "product_movement_data.csv").read_text(), INGEST_CFG)


def test_parse_movements_skips_opening_balance():
    rows = _rows()
    assert rows, "expected parsed rows"
    assert all(r["date"] for r in rows)
    assert rows == sorted(rows, key=lambda r: r["date"])


def test_plan_is_self_consistent():
    plan = plan_production(_rows(), PARAMS)
    assert plan["daily_avg_consumption"] > 0
    assert plan["forecast_stock"] > plan["safety_stock"] > 0
    assert plan["required_production"] >= 2.0
    assert set(plan["ingredients"]) == set(PARAMS["recipe"])
    # ingredient amount scales with the recipe rate
    vol = plan["required_production"]
    assert plan["ingredients"]["груши"] == round(vol * 650, 2)


def test_empty_history_is_safe():
    plan = plan_production([], PARAMS)
    assert plan["daily_avg_consumption"] == 0.0
    assert plan["required_production"] == 2.0


def test_what_if_higher_demand_raises_production():
    base = plan_production(_rows(), PARAMS)
    spike = plan_production(_rows(), {**PARAMS, "weekend_factor": 6})
    assert spike["required_production"] >= base["required_production"]
