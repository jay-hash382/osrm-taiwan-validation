from __future__ import annotations

import importlib.util
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "audit_quality.py"
SPEC = importlib.util.spec_from_file_location("audit_quality", MODULE_PATH)
assert SPEC and SPEC.loader
audit = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(audit)


POLICY = {
    "hard_max_snap_distance_m": 300,
    "review_snap_distance_m": 75,
    "review_detour_ratio": 3.5,
    "review_unnamed_distance_ratio": 0.65,
    "hard_max_speed_kmh": 180,
}
CASE = {
    "id": "case",
    "category": "test",
    "description": "test",
    "from": [120.0, 23.0],
    "to": [120.01, 23.0],
    "min_distance_km": 0.5,
    "max_distance_km": 5,
}


def payload(snap: float = 10, distance: float = 1200) -> dict:
    return {
        "code": "Ok",
        "waypoints": [{"distance": snap}, {"distance": snap}],
        "routes": [{
            "distance": distance,
            "duration": 120,
            "geometry": {"type": "LineString", "coordinates": [[120.0, 23.0], [120.01, 23.0]]},
            "legs": [{
                "steps": [{"name": "測試路", "distance": distance}],
                "annotation": {"speed": [10, 15], "nodes": [1, 2]},
            }],
        }],
    }


class QualityAuditTests(unittest.TestCase):
    def test_safe_route_passes(self) -> None:
        with patch.object(audit, "request_json", return_value=(payload(), 2.0)):
            result, feature = audit.audit_route("http://localhost", CASE, POLICY, 10)
        self.assertEqual("pass", result["status"])
        self.assertIsNotNone(feature)

    def test_moderate_snap_requires_review(self) -> None:
        with patch.object(audit, "request_json", return_value=(payload(snap=100), 2.0)):
            result, _ = audit.audit_route("http://localhost", CASE, POLICY, 10)
        self.assertEqual("review", result["status"])

    def test_excessive_snap_fails(self) -> None:
        with patch.object(audit, "request_json", return_value=(payload(snap=350), 2.0)):
            result, _ = audit.audit_route("http://localhost", CASE, POLICY, 10)
        self.assertEqual("fail", result["status"])

    def test_profile_tokens_are_required(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            profile = Path(directory) / "car.lua"
            profile.write_text("private driveway", encoding="utf-8")
            result = audit.audit_profile(profile, ["private", "driveway", "steps"])
        self.assertEqual("fail", result["status"])
        self.assertEqual(["steps"], result["missing"])


if __name__ == "__main__":
    unittest.main()

