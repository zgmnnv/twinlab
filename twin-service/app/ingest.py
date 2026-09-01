"""Parse a movement CSV into normalised rows.

Replaces the old ``TableManager``: no files written, no pandas. The column
names, date format and unit scale come from ``twin.config.ingest`` so the same
endpoint works for any twin.
"""
from __future__ import annotations

import csv
import io
from datetime import datetime

DEFAULT_INGEST = {
    "columns": {
        "date": "date",
        "inflow": "inflow",
        "outflow": "outflow",
        "stock": "stock",
    },
    "date_format": "%Y-%m-%d",
    "scale": 1.0,
}


def _num(raw: str | None, scale: float) -> float:
    if raw is None:
        return 0.0
    raw = raw.strip().replace(" ", "").replace(",", ".")
    if not raw:
        return 0.0
    try:
        return round(float(raw) * scale, 4)
    except ValueError:
        return 0.0


def parse_movements(text: str, ingest_cfg: dict | None) -> list[dict]:
    cfg = {**DEFAULT_INGEST, **(ingest_cfg or {})}
    cols = {**DEFAULT_INGEST["columns"], **cfg.get("columns", {})}
    scale = float(cfg.get("scale", 1.0))
    date_fmt = cfg.get("date_format", "%Y-%m-%d")

    reader = csv.DictReader(io.StringIO(text))
    rows: list[dict] = []
    for raw in reader:
        date_str = (raw.get(cols["date"]) or "").strip()
        if not date_str:
            continue  # skip opening-balance / headerless rows
        try:
            date = datetime.strptime(date_str, date_fmt).date()
        except ValueError:
            continue
        rows.append(
            {
                "date": date.isoformat(),
                "inflow": _num(raw.get(cols["inflow"]), scale),
                "outflow": _num(raw.get(cols["outflow"]), scale),
                "stock": _num(raw.get(cols["stock"]), scale),
            }
        )
    rows.sort(key=lambda r: r["date"])
    return rows
