"""Seed the demo twin on an empty database."""
from __future__ import annotations

import json
import pathlib

from . import store
from .calculations import get_calculator
from .ingest import parse_movements

SEED_DIR = pathlib.Path(__file__).with_name("seed")
if not SEED_DIR.exists():
    SEED_DIR = pathlib.Path(__file__).parents[1] / "seed"


async def seed_demo() -> None:
    if await store.twin_count() > 0:
        return

    spec = json.loads((SEED_DIR / "tincture_twin.json").read_text())
    twin = await store.create_twin(
        spec["id"], spec["name"], spec["kind"],
        spec["config"], spec["state"], spec["flow"],
    )

    csv_text = (SEED_DIR / "product_movement_data.csv").read_text()
    rows = parse_movements(csv_text, spec["config"].get("ingest"))
    await store.replace_movements(twin["id"], rows)
    await store.refresh_daily_agg()

    # Plan from the day-grouped movements, exactly as POST /plan would.
    daily = await store.load_movements(twin["id"])
    params = spec["config"].get("plan_defaults", {})
    result = get_calculator(twin["kind"])(daily, params)
    await store.save_plan(twin["id"], params, result, activate=True)
    await store.patch_state(
        twin["id"],
        {"stock": result["current_stock"], "status": "ok" if result["stock_ok"] else "low"},
    )
    await store.add_event(twin["id"], "seeded", {"movements": len(rows)})
