"""Overlay live status onto a twin's stored process diagram.

The twin stores a static ``flow`` template (nodes with x/y positions and edges).
This module colours nodes and annotates edges from the current state and the
active plan, so the 2D flow-view SPA can render a live picture without knowing
any domain rules.
"""
from __future__ import annotations

from typing import Any

STATUS_OK = "ok"
STATUS_WARN = "warn"
STATUS_LOW = "low"


def derive_flow(twin: dict, plan: dict | None) -> dict:
    template = twin.get("flow") or {"nodes": [], "edges": []}
    state = twin.get("state") or {}
    nodes = [dict(n) for n in template.get("nodes", [])]
    edges = [dict(e) for e in template.get("edges", [])]

    metrics = _plan_metrics(twin, plan, state)
    for node in nodes:
        node.setdefault("status", STATUS_OK)
        node["metrics"] = {k: metrics[k] for k in node.get("show", []) if k in metrics}
        _apply_rules(node, metrics)
    for edge in edges:
        key = edge.get("rate")
        if key and key in metrics:
            edge["label"] = _fmt(metrics[key])
            edge["active"] = bool(metrics[key])
    return {"nodes": nodes, "edges": edges, "metrics": metrics}


def _plan_metrics(twin: dict, plan: dict | None, state: dict) -> dict[str, Any]:
    result = dict(plan.get("result", {})) if plan else {}
    metrics = {
        "required_production": result.get("required_production"),
        "forecast_stock": result.get("forecast_stock"),
        "safety_stock": result.get("safety_stock"),
        "daily_avg_consumption": result.get("daily_avg_consumption"),
        "current_stock": result.get("current_stock", state.get("stock")),
    }
    ingredients = result.get("ingredients") or {}
    if ingredients:
        metrics["ingredients_total"] = round(sum(ingredients.values()), 2)
    return {k: v for k, v in metrics.items() if v is not None}


def _apply_rules(node: dict, metrics: dict) -> None:
    rule = node.get("rule")
    if rule == "stock_vs_safety":
        stock = metrics.get("current_stock")
        safety = metrics.get("safety_stock")
        if stock is None or safety is None:
            return
        if stock < safety:
            node["status"] = STATUS_LOW
        elif stock < safety * 1.5:
            node["status"] = STATUS_WARN
    elif rule == "production_needed":
        req = metrics.get("required_production") or 0
        node["status"] = STATUS_WARN if req > 0 else STATUS_OK


def _fmt(value: Any) -> str:
    if isinstance(value, (int, float)):
        return f"{value:g}"
    return str(value)
