"""All SQL for the twin service lives here."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

from .db import dumps, load_json, pool

MOVEMENT_METRICS = ("inflow", "outflow", "stock")


# --- twins -----------------------------------------------------------------

async def list_twins() -> list[dict]:
    rows = await pool().fetch(
        "SELECT id, name, kind, state, updated_at FROM twin ORDER BY name"
    )
    return [load_json(r, "state") for r in rows]


async def get_twin(twin_id: str) -> dict | None:
    row = await pool().fetchrow(
        "SELECT id, name, kind, config, state, flow, created_at, updated_at "
        "FROM twin WHERE id = $1",
        twin_id,
    )
    return load_json(row, "config", "state", "flow")


async def create_twin(
    twin_id: str, name: str, kind: str, config: dict, state: dict, flow: dict
) -> dict:
    await pool().execute(
        "INSERT INTO twin (id, name, kind, config, state, flow) "
        "VALUES ($1, $2, $3, $4, $5, $6) ON CONFLICT (id) DO NOTHING",
        twin_id, name, kind, dumps(config), dumps(state), dumps(flow),
    )
    return await get_twin(twin_id)


async def patch_state(twin_id: str, patch: dict) -> dict | None:
    async with pool().acquire() as conn:
        async with conn.transaction():
            row = await conn.fetchrow(
                "SELECT state FROM twin WHERE id = $1 FOR UPDATE", twin_id
            )
            if row is None:
                return None
            merged = {**load_json(row, "state")["state"], **patch}
            await conn.execute(
                "UPDATE twin SET state = $2, updated_at = now() WHERE id = $1",
                twin_id, dumps(merged),
            )
            await conn.execute(
                "INSERT INTO twin_state_history (twin_id, state) VALUES ($1, $2)",
                twin_id, dumps(merged),
            )
    return await get_twin(twin_id)


# --- measurements --------------------------------------------------------

async def replace_movements(twin_id: str, rows: list[dict]) -> int:
    """Store parsed movement rows as measurements, replacing any earlier import."""
    records = []
    per_day: dict[str, int] = {}
    for r in rows:
        base = datetime.fromisoformat(r["date"]).replace(tzinfo=timezone.utc)
        seq = per_day.get(r["date"], 0)
        per_day[r["date"]] = seq + 1
        ts = base + timedelta(seconds=seq)
        for metric in MOVEMENT_METRICS:
            records.append((twin_id, ts, metric, float(r[metric])))
    async with pool().acquire() as conn:
        async with conn.transaction():
            await conn.execute(
                "DELETE FROM measurement WHERE twin_id = $1 AND metric = ANY($2)",
                twin_id, list(MOVEMENT_METRICS),
            )
            await conn.copy_records_to_table(
                "measurement",
                records=records,
                columns=["twin_id", "ts", "metric", "value"],
            )
    return len(rows)


async def add_measurements(twin_id: str, samples: list[dict]) -> int:
    records = [
        (
            twin_id,
            _as_ts(s.get("ts")),
            str(s["metric"]),
            float(s["value"]),
        )
        for s in samples
    ]
    await pool().copy_records_to_table(
        "measurement", records=records, columns=["twin_id", "ts", "metric", "value"]
    )
    return len(records)


async def load_movements(twin_id: str) -> list[dict]:
    rows = await pool().fetch(
        """
        SELECT time_bucket('1 day', ts) AS day,
               coalesce(sum(value) FILTER (WHERE metric = 'inflow'), 0)  AS inflow,
               coalesce(sum(value) FILTER (WHERE metric = 'outflow'), 0) AS outflow,
               last(value, ts) FILTER (WHERE metric = 'stock')          AS stock
        FROM measurement
        WHERE twin_id = $1 AND metric = ANY($2)
        GROUP BY day
        ORDER BY day
        """,
        twin_id, list(MOVEMENT_METRICS),
    )
    return [
        {
            "date": r["day"].date().isoformat(),
            "inflow": float(r["inflow"]),
            "outflow": float(r["outflow"]),
            "stock": float(r["stock"]) if r["stock"] is not None else 0.0,
        }
        for r in rows
    ]


async def history(
    twin_id: str, metric: str | None, since_hours: int | None, limit: int
) -> list[dict]:
    clauses = ["twin_id = $1"]
    args: list = [twin_id]
    if metric:
        args.append(metric)
        clauses.append(f"metric = ${len(args)}")
    if since_hours:
        args.append(datetime.now(timezone.utc) - timedelta(hours=since_hours))
        clauses.append(f"ts >= ${len(args)}")
    args.append(limit)
    rows = await pool().fetch(
        f"SELECT ts, metric, value FROM measurement WHERE {' AND '.join(clauses)} "
        f"ORDER BY ts DESC LIMIT ${len(args)}",
        *args,
    )
    return [
        {"ts": r["ts"].isoformat(), "metric": r["metric"], "value": r["value"]}
        for r in rows
    ]


# --- plans / events ----------------------------------------------------

async def save_plan(twin_id: str, params: dict, result: dict, activate: bool) -> dict:
    async with pool().acquire() as conn:
        async with conn.transaction():
            if activate:
                await conn.execute(
                    "UPDATE plan SET active = false WHERE twin_id = $1", twin_id
                )
            row = await conn.fetchrow(
                "INSERT INTO plan (twin_id, params, result, active) "
                "VALUES ($1, $2, $3, $4) RETURNING id, created_at, active",
                twin_id, dumps(params), dumps(result), activate,
            )
    return {
        "id": row["id"],
        "created_at": row["created_at"].isoformat(),
        "active": row["active"],
        "params": params,
        "result": result,
    }


async def active_plan(twin_id: str) -> dict | None:
    row = await pool().fetchrow(
        "SELECT id, created_at, params, result FROM plan "
        "WHERE twin_id = $1 AND active ORDER BY created_at DESC LIMIT 1",
        twin_id,
    )
    if row is None:
        return None
    decoded = load_json(row, "params", "result")
    decoded["created_at"] = row["created_at"].isoformat()
    return decoded


async def list_plans(twin_id: str, limit: int = 20) -> list[dict]:
    rows = await pool().fetch(
        "SELECT id, created_at, params, result, active FROM plan "
        "WHERE twin_id = $1 ORDER BY created_at DESC LIMIT $2",
        twin_id, limit,
    )
    out = []
    for r in rows:
        d = load_json(r, "params", "result")
        d["created_at"] = r["created_at"].isoformat()
        out.append(d)
    return out


async def add_event(twin_id: str, type_: str, payload: dict) -> None:
    await pool().execute(
        "INSERT INTO event (twin_id, type, payload) VALUES ($1, $2, $3)",
        twin_id, type_, dumps(payload),
    )


async def list_events(twin_id: str, limit: int = 50) -> list[dict]:
    rows = await pool().fetch(
        "SELECT ts, type, payload FROM event WHERE twin_id = $1 "
        "ORDER BY ts DESC LIMIT $2",
        twin_id, limit,
    )
    import json
    return [
        {
            "ts": r["ts"].isoformat(),
            "type": r["type"],
            "payload": json.loads(r["payload"]) if isinstance(r["payload"], str) else r["payload"],
        }
        for r in rows
    ]


async def refresh_daily_agg() -> None:
    """Materialise measurement_daily over its full range (safe to call often)."""
    try:
        await pool().execute(
            "CALL refresh_continuous_aggregate('measurement_daily', NULL, NULL)"
        )
    except Exception:  # noqa: BLE001 - best effort; the hourly policy is the backstop
        pass


async def twin_count() -> int:
    return await pool().fetchval("SELECT count(*) FROM twin")


def _as_ts(value) -> datetime:
    if value in (None, ""):
        return datetime.now(timezone.utc)
    if isinstance(value, datetime):
        return value
    return datetime.fromisoformat(str(value).replace("Z", "+00:00"))
