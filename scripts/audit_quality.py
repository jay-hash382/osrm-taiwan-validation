#!/usr/bin/env python3
"""Audit OSRM route quality without changing or integrating the application."""

from __future__ import annotations

import argparse
import json
import math
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


def coordinate(point: list[float]) -> str:
    return f"{point[0]:.7f},{point[1]:.7f}"


def haversine_km(start: list[float], end: list[float]) -> float:
    lon1, lat1, lon2, lat2 = map(math.radians, [start[0], start[1], end[0], end[1]])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    value = math.sin(dlat / 2) ** 2 + math.cos(lat1) * math.cos(lat2) * math.sin(dlon / 2) ** 2
    return 6371.0088 * 2 * math.asin(math.sqrt(value))


def audit_route(base_url: str, case: dict[str, Any], policy: dict[str, float], timeout: float) -> tuple[dict[str, Any], dict[str, Any] | None]:
    coords = f"{coordinate(case['from'])};{coordinate(case['to'])}"
    query = urllib.parse.urlencode({
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "annotations": "distance,duration,speed,nodes",
    })
    payload, latency_ms = request_json(f"{base_url}/route/v1/driving/{coords}?{query}", timeout)
    result: dict[str, Any] = {
        "id": case["id"],
        "category": case["category"],
        "description": case["description"],
        "code": payload.get("code"),
        "latency_ms": latency_ms,
        "status": "fail",
        "hard_failures": [],
        "review_reasons": [],
    }
    if payload.get("code") != "Ok" or not payload.get("routes"):
        result["hard_failures"].append(payload.get("message", "No route returned"))
        return result, None

    route = payload["routes"][0]
    distance_km = route["distance"] / 1000
    aerial_km = max(haversine_km(case["from"], case["to"]), 0.001)
    detour_ratio = distance_km / aerial_km
    snap_distances = [float(item.get("distance", math.inf)) for item in payload.get("waypoints", [])]
    steps = [step for leg in route.get("legs", []) for step in leg.get("steps", [])]
    unnamed_distance = sum(float(step.get("distance", 0)) for step in steps if not step.get("name", "").strip())
    unnamed_ratio = unnamed_distance / max(float(route["distance"]), 1)
    speeds = [
        float(speed)
        for leg in route.get("legs", [])
        for speed in leg.get("annotation", {}).get("speed", [])
        if isinstance(speed, (int, float))
    ]
    max_speed_kmh = max(speeds, default=0) * 3.6
    geometry = route.get("geometry", {})
    geometry_coordinates = geometry.get("coordinates", [])

    hard_snap = float(case.get("hard_max_snap_distance_m", policy["hard_max_snap_distance_m"]))
    review_snap = float(case.get("review_snap_distance_m", policy["review_snap_distance_m"]))
    review_detour = float(case.get("review_detour_ratio", policy["review_detour_ratio"]))
    review_unnamed = float(case.get("review_unnamed_distance_ratio", policy["review_unnamed_distance_ratio"]))

    if len(snap_distances) != 2 or max(snap_distances, default=math.inf) > hard_snap:
        result["hard_failures"].append(f"endpoint snap exceeds {hard_snap:g} m")
    elif max(snap_distances) > review_snap:
        result["review_reasons"].append(f"endpoint snap exceeds review threshold {review_snap:g} m")
    if not case["min_distance_km"] <= distance_km <= case["max_distance_km"]:
        result["hard_failures"].append("route distance outside expected range")
    if len(geometry_coordinates) < 2:
        result["hard_failures"].append("missing route geometry")
    if not steps:
        result["hard_failures"].append("missing route guidance steps")
    if max_speed_kmh > policy["hard_max_speed_kmh"]:
        result["hard_failures"].append("annotation speed exceeds safety ceiling")
    if detour_ratio > review_detour:
        result["review_reasons"].append(f"detour ratio {detour_ratio:.2f} exceeds {review_detour:g}")
    if unnamed_ratio > review_unnamed:
        result["review_reasons"].append(f"unnamed route ratio {unnamed_ratio:.2f} exceeds {review_unnamed:g}")

    if result["hard_failures"]:
        status = "fail"
    elif result["review_reasons"]:
        status = "review"
    else:
        status = "pass"
    result.update({
        "status": status,
        "distance_km": round(distance_km, 3),
        "duration_min": round(float(route["duration"]) / 60, 1),
        "aerial_distance_km": round(aerial_km, 3),
        "detour_ratio": round(detour_ratio, 3),
        "snap_distances_m": [round(value, 1) for value in snap_distances],
        "unnamed_distance_ratio": round(unnamed_ratio, 3),
        "max_annotation_speed_kmh": round(max_speed_kmh, 1),
        "step_names": list(dict.fromkeys(step.get("name", "") for step in steps if step.get("name"))),
    })
    feature = {
        "type": "Feature",
        "properties": {
            "id": case["id"],
            "category": case["category"],
            "status": status,
            "distance_km": round(distance_km, 3),
            "detour_ratio": round(detour_ratio, 3),
        },
        "geometry": geometry,
    }
    return result, feature


def audit_profile(profile_path: Path, tokens: list[str]) -> dict[str, Any]:
    if not profile_path.exists():
        return {"status": "fail", "missing": [str(profile_path)]}
    source = profile_path.read_text(encoding="utf-8")
    missing = [token for token in tokens if token not in source]
    return {"status": "pass" if not missing else "fail", "missing": missing}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--cases", type=Path, default=ROOT / "tests" / "quality-cases.json")
    parser.add_argument("--profile", type=Path, default=ROOT / "reports" / "car.lua")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "quality-audit.json")
    parser.add_argument("--geojson", type=Path, default=ROOT / "reports" / "quality-routes.geojson")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    config = json.loads(args.cases.read_text(encoding="utf-8"))
    report: dict[str, Any] = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url.rstrip("/"),
        "profile": audit_profile(args.profile, config["profile_required_tokens"]),
        "routes": [],
    }
    features: list[dict[str, Any]] = []
    try:
        for case in config["routes"]:
            result, feature = audit_route(report["base_url"], case, config["policy"], args.timeout)
            report["routes"].append(result)
            if feature:
                features.append(feature)
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as error:
        report["fatal_error"] = str(error)

    statuses = [item["status"] for item in report["routes"]]
    if report["profile"]["status"] == "fail":
        statuses.append("fail")
    report["summary"] = {
        "pass": statuses.count("pass"),
        "review": statuses.count("review"),
        "fail": statuses.count("fail"),
        "total": len(statuses),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    args.geojson.write_text(
        json.dumps({"type": "FeatureCollection", "features": features}, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 1 if report["summary"]["fail"] else 0


if __name__ == "__main__":
    sys.exit(main())

