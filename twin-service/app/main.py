"""TwinLab twin-service: the business-process digital twin core.

One small FastAPI app that owns the twin's state model, runs the planning
calculations, answers what-if questions and serves the live 2D flow view.
It replaces Eclipse Ditto + Hono + Kafka + the MQTT publisher from the old
architecture.
"""
from __future__ import annotations

import asyncio
import contextlib
from collections import defaultdict

from fastapi import Body, FastAPI, HTTPException, Query, UploadFile, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware

from . import config, db, store
from .calculations import plan_production
from .flow import derive_flow
from .ingest import parse_movements
from .seed import seed_demo


@contextlib.asynccontextmanager
async def lifespan(_: FastAPI):
    await db.connect()
    if config.SEED_DEMO:
        await seed_demo()
    yield
    await db.disconnect()


app = FastAPI(title="TwinLab twin-service", version="0.1.0", lifespan=lifespan)
app.add_middleware(
    CORSMiddleware,
    allow_origins=config.CORS_ORIGINS or ["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- tiny in-process pub/sub for the flow view -------------------------------
_subs: dict[str, set[asyncio.Queue]] = defaultdict(set)


async def _publish(twin_id: str, message: dict) -> None:
    for queue in list(_subs.get(twin_id, ())):
        queue.put_nowait(message)


async def _require_twin(twin_id: str) -> dict:
    twin = await store.get_twin(twin_id)
    if twin is None:
        raise HTTPException(404, f"twin '{twin_id}' not found")
    return twin


def _merge_params(twin: dict, override: dict | None) -> dict:
    defaults = (twin.get("config") or {}).get("plan_defaults", {})
    return {**defaults, **(override or {})}


# --- routes ----------------------------------------------------------------

@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/api/twins")
async def get_twins():
    return await store.list_twins()


@app.post("/api/twins", status_code=201)
async def post_twin(payload: dict = Body(...)):
    required = {"id", "name"}
    if not required <= payload.keys():
        raise HTTPException(422, f"missing fields: {required - payload.keys()}")
    return await store.create_twin(
        payload["id"], payload["name"], payload.get("kind", "process"),
        payload.get("config", {}), payload.get("state", {}),
        payload.get("flow", {"nodes": [], "edges": []}),
    )


@app.get("/api/twins/{twin_id}")
async def get_one(twin_id: str):
    return await _require_twin(twin_id)


@app.patch("/api/twins/{twin_id}/state")
async def patch_state(twin_id: str, patch: dict = Body(...)):
    twin = await store.patch_state(twin_id, patch)
    if twin is None:
        raise HTTPException(404, f"twin '{twin_id}' not found")
    await store.add_event(twin_id, "state.patched", patch)
    await _publish(twin_id, {"event": "state", "state": twin["state"]})
    return twin


@app.get("/api/twins/{twin_id}/history")
async def get_history(
    twin_id: str,
    metric: str | None = None,
    since_hours: int | None = Query(None, ge=1),
    limit: int = Query(2000, ge=1, le=50000),
):
    await _require_twin(twin_id)
    return await store.history(twin_id, metric, since_hours, limit)


@app.post("/api/twins/{twin_id}/measurements")
async def post_measurements(twin_id: str, samples: list[dict] = Body(...)):
    await _require_twin(twin_id)
    count = await store.add_measurements(twin_id, samples)
    return {"ingested": count}


@app.post("/api/twins/{twin_id}/ingest")
async def ingest_csv(
    twin_id: str,
    file: UploadFile | None = None,
    body: str | None = Body(None, media_type="text/csv"),
):
    twin = await _require_twin(twin_id)
    if file is not None:
        text = (await file.read()).decode("utf-8-sig")
    elif body:
        text = body
    else:
        raise HTTPException(422, "provide a CSV file upload or a text/csv body")
    rows = parse_movements(text, (twin.get("config") or {}).get("ingest"))
    if not rows:
        raise HTTPException(422, "no valid movement rows found")
    count = await store.replace_movements(twin_id, rows)
    await store.add_event(twin_id, "ingested", {"movements": count})
    return {"movements": count, "first": rows[0]["date"], "last": rows[-1]["date"]}


@app.post("/api/twins/{twin_id}/plan")
async def run_plan(
    twin_id: str,
    params: dict | None = Body(None),
    activate: bool = Query(False),
):
    twin = await _require_twin(twin_id)
    rows = await store.load_movements(twin_id)
    if not rows:
        raise HTTPException(409, "no movement history — ingest a CSV first")
    merged = _merge_params(twin, params)
    result = plan_production(rows, merged)

    # A what-if preview is not persisted; only ?activate=true writes a plan row
    # and moves the twin state.
    if not activate:
        return {"active": False, "params": merged, "result": result}

    plan = await store.save_plan(twin_id, merged, result, activate=True)
    await store.patch_state(
        twin_id,
        {"stock": result["current_stock"],
         "status": "ok" if result["stock_ok"] else "low"},
    )
    await store.add_event(twin_id, "plan.activated", {"plan_id": plan["id"]})
    await _publish(twin_id, {"event": "plan", "plan": plan})
    return plan


@app.get("/api/twins/{twin_id}/plan")
async def get_plan(twin_id: str):
    await _require_twin(twin_id)
    return {
        "active": await store.active_plan(twin_id),
        "history": await store.list_plans(twin_id),
    }


@app.get("/api/twins/{twin_id}/flow")
async def get_flow(twin_id: str):
    twin = await _require_twin(twin_id)
    plan = await store.active_plan(twin_id)
    return derive_flow(twin, plan)


@app.websocket("/api/twins/{twin_id}/ws")
async def flow_ws(websocket: WebSocket, twin_id: str):
    await websocket.accept()
    queue: asyncio.Queue = asyncio.Queue()
    _subs[twin_id].add(queue)
    try:
        twin = await store.get_twin(twin_id)
        if twin is not None:
            plan = await store.active_plan(twin_id)
            await websocket.send_json({"event": "flow", "flow": derive_flow(twin, plan)})
        while True:
            await websocket.send_json(await queue.get())
    except WebSocketDisconnect:
        pass
    finally:
        _subs[twin_id].discard(queue)
