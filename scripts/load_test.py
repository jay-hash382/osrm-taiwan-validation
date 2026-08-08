#!/usr/bin/env python3
"""Run repeatable concurrent initial-route and reroute load tests against OSRM."""

from __future__ import annotations

import argparse
import concurrent.futures
import json
import math
import statistics
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]


def percentile(values: list[float], percentage: float) -> float:
    if not values:
        return math.inf
    ordered = sorted(values)
    rank = (len(ordered) - 1) * percentage
    lower = math.floor(rank)
    upper = math.ceil(rank)
    if lower == upper:
        return ordered[lower]
    return ordered[lower] + (ordered[upper] - ordered[lower]) * (rank - lower)


def route_url(base_url: str, case: dict[str, Any]) -> str:
    start = f"{case['from'][0]:.7f},{case['from'][1]:.7f}"
    end = f"{case['to'][0]:.7f},{case['to'][1]:.7f}"
    query = urllib.parse.urlencode({
        "overview": "full",
        "geometries": "geojson",
        "steps": "true",
        "annotations": "distance,duration,speed",
    })
    return f"{base_url.rstrip('/')}/route/v1/driving/{start};{end}?{query}"


def execute_request(base_url: str, case: dict[str, Any], timeout: float) -> dict[str, Any]:
    started = time.perf_counter()
    try:
        with urllib.request.urlopen(route_url(base_url, case), timeout=timeout) as response:
            raw = response.read()
        payload = json.loads(raw)
        ok = payload.get("code") == "Ok" and bool(payload.get("routes"))
        error = None if ok else payload.get("message", payload.get("code", "invalid response"))
    except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as exception:
        raw = b""
        ok = False
        error = str(exception)
    return {
        "id": case["id"],
        "type": case["type"],
        "ok": ok,
        "latency_ms": (time.perf_counter() - started) * 1000,
        "response_bytes": len(raw),
        "error": error,
    }


def summarize(concurrency: int, elapsed: float, results: list[dict[str, Any]], thresholds: dict[str, float]) -> dict[str, Any]:
    successes = [result for result in results if result["ok"]]
    latencies = [result["latency_ms"] for result in successes]
    errors = len(results) - len(successes)
    error_rate = errors / max(len(results), 1)
    p95 = percentile(latencies, 0.95)
    by_type: dict[str, dict[str, Any]] = {}
    for route_type in sorted({result["type"] for result in results}):
        subset = [result for result in results if result["type"] == route_type]
        subset_success = [result for result in subset if result["ok"]]
        subset_latencies = [result["latency_ms"] for result in subset_success]
        by_type[route_type] = {
            "requests": len(subset),
            "errors": len(subset) - len(subset_success),
            "p50_ms": round(percentile(subset_latencies, 0.50), 2),
            "p95_ms": round(percentile(subset_latencies, 0.95), 2),
        }
    return {
        "concurrency": concurrency,
        "requests": len(results),
        "errors": errors,
        "error_rate": round(error_rate, 5),
        "elapsed_seconds": round(elapsed, 3),
        "throughput_rps": round(len(results) / max(elapsed, 0.001), 2),
        "p50_ms": round(percentile(latencies, 0.50), 2),
        "p95_ms": round(p95, 2),
        "p99_ms": round(percentile(latencies, 0.99), 2),
        "mean_ms": round(statistics.fmean(latencies), 2) if latencies else None,
        "average_response_bytes": round(statistics.fmean(result["response_bytes"] for result in successes), 1) if successes else 0,
        "by_type": by_type,
        "passed": error_rate <= thresholds["max_error_rate"] and p95 <= thresholds["max_p95_ms"],
    }


def run_level(base_url: str, cases: list[dict[str, Any]], concurrency: int, count: int, timeout: float, thresholds: dict[str, float]) -> dict[str, Any]:
    selected = [cases[index % len(cases)] for index in range(count)]
    started = time.perf_counter()
    with concurrent.futures.ThreadPoolExecutor(max_workers=concurrency) as executor:
        results = list(executor.map(lambda case: execute_request(base_url, case, timeout), selected))
    return summarize(concurrency, time.perf_counter() - started, results, thresholds)


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--base-url", default="http://127.0.0.1:5000")
    parser.add_argument("--cases", type=Path, default=ROOT / "tests" / "load-cases.json")
    parser.add_argument("--output", type=Path, default=ROOT / "reports" / "load-test.json")
    parser.add_argument("--timeout", type=float, default=30)
    args = parser.parse_args()

    config = json.loads(args.cases.read_text(encoding="utf-8"))
    for case in config["routes"]:
        execute_request(args.base_url, case, args.timeout)
    levels = [
        run_level(
            args.base_url,
            config["routes"],
            int(concurrency),
            int(config["requests_per_level"]),
            args.timeout,
            config["thresholds"],
        )
        for concurrency in config["concurrency_levels"]
    ]
    report = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "base_url": args.base_url.rstrip("/"),
        "thresholds": config["thresholds"],
        "levels": levels,
        "passed": all(level["passed"] for level in levels),
    }
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2))
    return 0 if report["passed"] else 1


if __name__ == "__main__":
    sys.exit(main())

