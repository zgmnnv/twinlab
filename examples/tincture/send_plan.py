#!/usr/bin/env python3
"""Drive the tincture twin through the twin-service API.

The old example did everything itself: cleaned a CSV, ran the maths, published
to Eclipse Ditto over MQTT and started a Dash dashboard. Now the twin-service
owns all of that. This script just feeds it data and asks for a plan.

    python send_plan.py --csv table/product_movement_data.csv \
        --api http://localhost:8080/api --twin tincture_ulun

Requires only the standard library.
"""
from __future__ import annotations

import argparse
import json
import urllib.request


def _request(method: str, url: str, payload=None, ctype="application/json"):
    data = None
    headers = {}
    if payload is not None:
        data = payload if isinstance(payload, bytes) else json.dumps(payload).encode()
        headers["Content-Type"] = ctype
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req) as resp:
        return json.load(resp)


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--api", default="http://localhost:8080/api")
    ap.add_argument("--twin", default="tincture_ulun")
    ap.add_argument("--csv", default="table/product_movement_data.csv")
    ap.add_argument("--forecast-days", type=int, default=7)
    ap.add_argument("--weekend-factor", type=float, default=3)
    ap.add_argument("--safety-factor", type=float, default=0.2)
    ap.add_argument("--activate", action="store_true", help="make this the active plan")
    args = ap.parse_args()

    base = f"{args.api}/twins/{args.twin}"

    with open(args.csv, "rb") as fh:
        summary = _request("POST", f"{base}/ingest", fh.read(), ctype="text/csv")
    print(f"ingested {summary['movements']} movements "
          f"({summary['first']} … {summary['last']})")

    params = {
        "forecast_days": args.forecast_days,
        "weekend_factor": args.weekend_factor,
        "safety_factor": args.safety_factor,
    }
    q = "?activate=true" if args.activate else ""
    plan = _request("POST", f"{base}/plan{q}", params)
    r = plan["result"]
    print("\nplan:")
    print(f"  average daily consumption : {r['daily_avg_consumption']} L/day")
    print(f"  forecast demand           : {r['forecast_stock']} L")
    print(f"  safety stock              : {r['safety_stock']} L")
    print(f"  required production        : {r['required_production']} L")
    print("  ingredients               :")
    for name, qty in r["ingredients"].items():
        print(f"    {name}: {qty}")
    print(f"  stock ok                  : {r['stock_ok']}")

    flow = _request("GET", f"{base}/flow")
    print("\nprocess node status:")
    for node in flow["nodes"]:
        print(f"  {node['label']:<24} {node['status']}")


if __name__ == "__main__":
    main()
