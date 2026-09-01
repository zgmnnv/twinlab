# twin-service

The business-process digital twin core. One FastAPI app that owns the twin's
state model, runs the planning calculations, answers what-if questions and
serves the live 2D flow view over REST + WebSocket.

Replaces Eclipse Ditto + Hono + Kafka + the MQTT publisher from the old stack.

## Layout

```
app/
  main.py              API routes, WebSocket, lifespan
  config.py            env config
  db.py                asyncpg pool + schema apply
  store.py             all SQL
  schema.sql           PostgreSQL / TimescaleDB schema
  ingest.py            movement-CSV parser (was TableManager)
  flow.py              overlays live status onto the stored flow diagram
  calculations/
    production.py      forecast / safety stock / batch / recipe (was ProductionCalculator)
  seed.py              demo twin bootstrap
seed/                  demo twin spec + sample CSV
tests/                 pure unit tests, no DB
```

## Run tests

```bash
pip install -r requirements.txt pytest
python -m pytest -q
```

## Run locally

```bash
TWIN_DATABASE_URL=postgresql://twin:twin@localhost:5432/twin \
  uvicorn app.main:app --reload --port 8000
```

## Env vars

| var | default | meaning |
|---|---|---|
| `TWIN_DATABASE_URL` | `postgresql://twin:twin@postgres:5432/twin` | database DSN |
| `TWIN_SEED_DEMO` | `true` | seed the tincture demo twin on empty DB |
| `TWIN_CORS_ORIGINS` | `*` | comma-separated allowed origins |
