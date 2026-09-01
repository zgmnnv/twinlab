"""Thin async PostgreSQL layer built on asyncpg."""
from __future__ import annotations

import json
import pathlib
from typing import Any

import asyncpg

from . import config

_pool: asyncpg.Pool | None = None

SCHEMA_PATH = pathlib.Path(__file__).with_name("schema.sql")


def pool() -> asyncpg.Pool:
    if _pool is None:  # pragma: no cover - guarded by lifespan
        raise RuntimeError("database pool is not initialised")
    return _pool


async def connect(retries: int = 30, delay: float = 2.0) -> None:
    """Open the pool, waiting for PostgreSQL to accept connections."""
    global _pool
    import asyncio

    last_err: Exception | None = None
    for _ in range(retries):
        try:
            _pool = await asyncpg.create_pool(
                config.DATABASE_URL, min_size=1, max_size=10
            )
            break
        except (OSError, asyncpg.PostgresError) as err:  # noqa: PERF203
            last_err = err
            await asyncio.sleep(delay)
    else:
        raise RuntimeError(f"could not connect to PostgreSQL: {last_err}")

    await _apply_schema()


async def disconnect() -> None:
    global _pool
    if _pool is not None:
        await _pool.close()
        _pool = None


def _split_statements(sql: str) -> list[str]:
    statements, buf = [], []
    for line in sql.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("--"):
            continue
        buf.append(line)
        if stripped.endswith(";"):
            statements.append("\n".join(buf).rstrip().rstrip(";"))
            buf = []
    if buf:
        statements.append("\n".join(buf))
    return statements


async def _apply_schema() -> None:
    # Continuous aggregates cannot run inside a transaction block, so each
    # statement is executed on its own (asyncpg autocommits single statements).
    async with pool().acquire() as conn:
        for statement in _split_statements(SCHEMA_PATH.read_text()):
            await conn.execute(statement)


# --- helpers -----------------------------------------------------------------

def load_json(record: asyncpg.Record | None, *fields: str) -> dict | None:
    """Return a plain dict with the given jsonb fields decoded."""
    if record is None:
        return None
    row = dict(record)
    for field in fields:
        if isinstance(row.get(field), str):
            row[field] = json.loads(row[field])
    return row


def dumps(value: Any) -> str:
    return json.dumps(value, ensure_ascii=False, default=str)
