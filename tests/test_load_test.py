from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "load_test.py"
SPEC = importlib.util.spec_from_file_location("load_test", MODULE_PATH)
assert SPEC and SPEC.loader
load_test = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(load_test)


class LoadTestTests(unittest.TestCase):
    def test_percentile_interpolates(self) -> None:
        self.assertEqual(2.5, load_test.percentile([1, 2, 3, 4], 0.5))

    def test_summary_passes_healthy_results(self) -> None:
        results = [
            {"ok": True, "latency_ms": value, "response_bytes": 100, "type": "initial_route"}
            for value in [10, 20, 30, 40]
        ]
        summary = load_test.summarize(4, 1.0, results, {"max_error_rate": 0.01, "max_p95_ms": 500})
        self.assertTrue(summary["passed"])
        self.assertEqual(4.0, summary["throughput_rps"])

    def test_summary_fails_error_rate(self) -> None:
        results = [
            {"ok": True, "latency_ms": 10, "response_bytes": 100, "type": "reroute"},
            {"ok": False, "latency_ms": 10, "response_bytes": 0, "type": "reroute"},
        ]
        summary = load_test.summarize(2, 1.0, results, {"max_error_rate": 0.01, "max_p95_ms": 500})
        self.assertFalse(summary["passed"])


if __name__ == "__main__":
    unittest.main()

