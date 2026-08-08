#!/usr/bin/env python3
"""Validate an isolated Taiwan OSRM instance using only the Python stdlib."""

from __future__ import annotations

import argparse
import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def request_json(url: str, timeout: float) -> tuple[dict[str, Any], float]:
    started = time.perf_counter()
    with urllib.request.urlopen(url, timeout=timeout) as response:
        payload = json.load(response)
    return payload, round((time.perf_counter() - started) * 1000, 1)


def coordinate(value: list[float]) -> str:
    return f"{value[0]:.7f},{value[1]:.7f}"


def validate_route(base_url: str, case: dict[str, Any], default_snap: float, timeout: float) -> dict[str, Any]:
    coords = f"{coordinate(case['from'])};{coordinate(case['to'])}"
    query = urllib.parse.urlencode({
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "annotations": "distance,duration,speed",
    })
    payload, latency_ms = request_json(f"{base_url}/route/v1/driving/{coords}?{query}", timeout)
    result: dict[str, Any] = {
        "id": case["id"],
        "description": case["description"],
        "code": payload.get("code"),
        "latency_ms": latency_ms,
        "passed": False,
    }
    if payload.get("code") != "Ok" or not payload.get("routes"):
        result["failure"] = payload.get("message", "No route returned")
        return result

    route = payload["routes"][0]
    distance_km = route["distance"] / 1000
    snap_distances = [waypoint.get("distance", float("inf")) for waypoint in payload.get("waypoints", [])]
    max_snap = case.get("max_snap_distance_m", default_snap)
    checks = {
        "distance_min": distance_km >= case["min_distance_km"],
        "distance_max": distance_km <= case["max_distance_km"],
        "snap_distance": len(snap_distances) == 2 and max(snap_distances) <= max_snap,
        "geometry": len(route.get("geometry", {}).get("coordinates", [])) >= 2,
        "steps": all(leg.get("steps") for leg in route.get("legs", [])),
    }
    result.update({
        "distance_km": round(distance_km, 3),
        "duration_min": round(route["duration"] / 60, 1),
        "snap_distances_m": snap_distances,
        "checks": checks,
        "passed": all(checks.values()),
    })
    return result


def validate_nearest(base_url: str, case: dict[str, Any], timeout: float) -> dict[str, Any]:
    payload, latency_ms = request_json(
        f"{base_url}/nearest/v1/driving/{coordinate(case['point'])}?number=3", timeout
    )
    distances = [waypoint.get("distance", float("inf")) for waypoint in payload.get("waypoints", [])]
    passed = payload.get("code") == "Ok" and bool(distances) and min(distances) <= case["max_distance_m"]
    return {
        "id": case["id"],
        "description": case["description"],
        "code": payload.get("code"),
        "latency_ms": latency_ms,
        "nearest_distances_m": distances,
        "passed": passed,
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--cases", type=Path, default=ROOT / "tests" / "cases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "validation.json")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    cases = json.loads(args.cases.read_text(encoding="utf-8"))
    base_url = args.base_url.rstrip("/")
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": base_url,
        "routes": [],
        "nearest": [],
    }
    try:
        report["routes"] = [
            validate_route(base_url, case, cases["max_snap_distance_m"], args.timeout)
            for case in cases["routes"]
        ]
        report["nearest"] = [validate_nearest(base_url, case, args.timeout) for case in cases["nearest"]]
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        report["fatal_error"] = str(error)

    all_results = report["routes"] + report["nearest"]
    report["summary"] = {
        "passed": sum(1 for item in all_results if item["passed"]),
        "failed": sum(1 for item in all_results if not item["passed"]),
        "total": len(all_results),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if all_results and all(item["passed"] for item in all_results) else 1


if __name__ == "__main__":
    sys.exit(main())

