#!/usr/bin/env python3
"""Idempotently provision the reference TwinLab dashboard in Superset.

Runs once, in the background, after the Superset API is up (see
scripts/superset-init.sh). Everything is keyed by name/slug, so re-runs are
no-ops. Safe to delete the dashboard/charts in the UI and re-run to recreate.
"""
from __future__ import annotations

import json
import os
import sys
import time
import urllib.error
import urllib.request
from urllib.parse import quote

BASE = os.environ.get("SUPERSET_INTERNAL_URL", "http://localhost:8088")
USER = os.environ.get("SUPERSET_ADMIN_USERNAME", "admin")
PASSWORD = os.environ.get("SUPERSET_ADMIN_PASSWORD", "admin")
DB_NAME = "twin"
DB_URI = os.environ.get("TWIN_DATABASE_URI", "")
TWIN_ID = os.environ.get("TWINLAB_DEMO_TWIN", "tincture_ulun")

DATASETS = ["v_daily", "v_active_plan", "v_plan_history"]


class Client:
    def __init__(self) -> None:
        self.token = ""
        self.csrf = ""
        self.cookie = ""

    def _req(self, method: str, path: str, body=None):
        url = f"{BASE}{path}"
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method)
        req.add_header("Content-Type", "application/json")
        if self.token:
            req.add_header("Authorization", f"Bearer {self.token}")
        if self.csrf:
            req.add_header("X-CSRFToken", self.csrf)
        if self.cookie:
            req.add_header("Cookie", self.cookie)
        try:
            with urllib.request.urlopen(req) as resp:
                if "Set-Cookie" in resp.headers:
                    self.cookie = resp.headers["Set-Cookie"].split(";")[0]
                raw = resp.read()
                return json.loads(raw) if raw else {}
        except urllib.error.HTTPError as err:
            detail = err.read().decode()
            raise RuntimeError(f"{method} {path} -> {err.code}: {detail}") from None

    def login(self) -> None:
        out = self._req("POST", "/api/v1/security/login", {
            "username": USER, "password": PASSWORD,
            "provider": "db", "refresh": True,
        })
        self.token = out["access_token"]
        csrf = self._req("GET", "/api/v1/security/csrf_token/")
        self.csrf = csrf["result"]

    def find(self, kind: str, col: str, value: str):
        safe = str(value).replace("'", "!'")
        q = quote(f"(filters:!((col:{col},opr:eq,value:'{safe}')))", safe="")
        out = self._req("GET", f"/api/v1/{kind}/?q={q}")
        return out.get("result", [])

    def post(self, kind: str, payload: dict) -> int:
        out = self._req("POST", f"/api/v1/{kind}/", payload)
        return out["id"]

    def put(self, kind: str, obj_id: int, payload: dict) -> None:
        self._req("PUT", f"/api/v1/{kind}/{obj_id}", payload)


def ensure_database(c: Client) -> int:
    existing = c.find("database", "database_name", DB_NAME)
    if existing:
        return existing[0]["id"]
    if not DB_URI:
        sys.exit("twin database not registered and TWIN_DATABASE_URI is empty")
    return c.post("database", {
        "database_name": DB_NAME,
        "sqlalchemy_uri": DB_URI,
        "expose_in_sqllab": True,
    })


def ensure_dataset(c: Client, db_id: int, table: str) -> int:
    existing = c.find("dataset", "table_name", table)
    if existing:
        return existing[0]["id"]
    return c.post("dataset", {
        "database": db_id, "schema": "public", "table_name": table,
    })


def metric(col: str, agg: str = "AVG", label: str | None = None) -> dict:
    return {
        "expressionType": "SIMPLE",
        "column": {"column_name": col},
        "aggregate": agg,
        "label": label or col,
    }


def flt(col: str, val: str) -> dict:
    return {
        "expressionType": "SIMPLE", "subject": col, "operator": "==",
        "comparator": val, "clause": "WHERE",
    }


def ensure_chart(c: Client, name: str, ds_id: int, params: dict) -> int:
    existing = c.find("chart", "slice_name", name)
    if existing:
        return existing[0]["id"]
    params = {"datasource": f"{ds_id}__table", **params}
    return c.post("chart", {
        "slice_name": name,
        "viz_type": params["viz_type"],
        "datasource_id": ds_id,
        "datasource_type": "table",
        "params": json.dumps(params),
    })


def build_charts(c: Client, ds: dict[str, int]) -> dict[str, int]:
    twin = flt("twin_id", TWIN_ID)
    charts = {}
    charts["stock"] = ensure_chart(c, "Остаток продукции, л", ds["v_daily"], {
        "viz_type": "echarts_timeseries_line",
        "x_axis": "day", "time_grain_sqla": "P1D",
        "metrics": [metric("last_value", "MAX", "Остаток, л")],
        "adhoc_filters": [twin, flt("metric", "stock")],
        "groupby": [],
    })
    charts["outflow"] = ensure_chart(c, "Расход продукции по дням, л", ds["v_daily"], {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "day", "time_grain_sqla": "P1D",
        "metrics": [metric("avg_value", "AVG", "Расход, л")],
        "adhoc_filters": [twin, flt("metric", "outflow")],
        "groupby": [],
    })
    charts["required"] = ensure_chart(c, "Требуемое производство, л", ds["v_active_plan"], {
        "viz_type": "big_number_total",
        "metric": metric("required_production", "MAX", "Требуемое производство"),
        "adhoc_filters": [twin],
    })
    charts["safety"] = ensure_chart(c, "Текущий / страховой запас, л", ds["v_active_plan"], {
        "viz_type": "echarts_timeseries_bar",
        "x_axis": "created_at",
        "metrics": [
            metric("current_stock", "MAX", "Текущий остаток"),
            metric("safety_stock", "MAX", "Страховой запас"),
        ],
        "adhoc_filters": [twin],
        "groupby": [],
    })
    charts["history"] = ensure_chart(c, "История планов (what-if)", ds["v_plan_history"], {
        "viz_type": "table",
        "query_mode": "raw",
        "columns": ["created_at", "forecast_days", "weekend_factor",
                    "safety_factor", "required_production", "active"],
        "adhoc_filters": [twin],
        "order_by_cols": ['["created_at", false]'],
        "row_limit": 50,
    })
    return charts


def ensure_dashboard(c: Client, charts: dict[str, int]) -> None:
    found = c.find("dashboard", "slug", "twinlab-tincture")
    if found:
        _link_charts(c, found[0]["id"], charts)
        print("dashboard already exists")
        return

    def chart_node(node_id: str, cid: int, w: int, h: int) -> dict:
        return {"type": "CHART", "id": node_id, "children": [],
                "meta": {"chartId": cid, "width": w, "height": h}}

    rows = [
        ["R1", [("C-req", charts["required"], 4, 40), ("C-safe", charts["safety"], 8, 40)]],
        ["R2", [("C-stock", charts["stock"], 6, 50), ("C-out", charts["outflow"], 6, 50)]],
        ["R3", [("C-hist", charts["history"], 12, 50)]],
    ]
    position = {
        "DASHBOARD_VERSION_KEY": "v2",
        "ROOT_ID": {"type": "ROOT", "id": "ROOT_ID", "children": ["GRID_ID"]},
        "GRID_ID": {"type": "GRID", "id": "GRID_ID",
                    "children": [r[0] for r in rows], "parents": ["ROOT_ID"]},
    }
    for row_id, cells in rows:
        position[row_id] = {
            "type": "ROW", "id": row_id, "children": [c[0] for c in cells],
            "parents": ["ROOT_ID", "GRID_ID"],
            "meta": {"background": "BACKGROUND_TRANSPARENT"},
        }
        for node_id, cid, w, h in cells:
            position[node_id] = chart_node(node_id, cid, w, h)
            position[node_id]["parents"] = ["ROOT_ID", "GRID_ID", row_id]

    dash_id = c.post("dashboard", {
        "dashboard_title": "TwinLab — Настойка «Груша-улун»",
        "slug": "twinlab-tincture",
        "published": True,
        "position_json": json.dumps(position),
        "css": "",
    })
    _link_charts(c, dash_id, charts)
    print("dashboard created")


def _link_charts(c: Client, dash_id: int, charts: dict[str, int]) -> None:
    for cid in charts.values():
        try:
            c.put("chart", cid, {"dashboards": [dash_id]})
        except RuntimeError as err:
            print(f"link chart {cid}: {err}", file=sys.stderr)


def wait_for_api() -> None:
    for _ in range(60):
        try:
            urllib.request.urlopen(f"{BASE}/health", timeout=3)
            return
        except OSError:
            time.sleep(2)
    sys.exit("Superset API did not come up")


def main() -> None:
    wait_for_api()
    c = Client()
    c.login()
    db_id = ensure_database(c)
    ds = {name: ensure_dataset(c, db_id, name) for name in DATASETS}
    print("datasets:", ds)
    charts = build_charts(c, ds)
    print("charts:", charts)
    ensure_dashboard(c, charts)
    print("bootstrap done")


if __name__ == "__main__":
    try:
        main()
    except Exception as err:  # noqa: BLE001 - log and exit non-fatally
        print(f"bootstrap_assets: {err}", file=sys.stderr)
        sys.exit(0)
