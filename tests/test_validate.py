from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path
from unittest.mock import patch


MODULE_PATH = Path(__file__).resolve().parents[1] / "scripts" / "validate.py"
SPEC = importlib.util.spec_from_file_location("osrm_validate", MODULE_PATH)
assert SPEC and SPEC.loader
validate = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(validate)


class ValidateRouteTests(unittest.TestCase):
    def test_route_passes_with_geometry_steps_and_close_snaps(self) -> None:
        payload = {
            "code": "Ok",
            "routes": [{
                "distance": 5000,
                "duration": 600,
                "geometry": {"coordinates": [[120.0, 23.0], [120.1, 23.1]]},
                "legs": [{"steps": [{"distance": 5000}]}],
            }],
            "waypoints": [{"distance": 4}, {"distance": 8}],
        }
        case = {
            "id": "route",
            "description": "route",
            "from": [120.0, 23.0],
            "to": [120.1, 23.1],
            "min_distance_km": 4,
            "max_distance_km": 6,
        }
        with patch.object(validate, "request_json", return_value=(payload, 12.5)):
            result = validate.validate_route("http://localhost", case, 500, 10)
        self.assertTrue(result["passed"])

    def test_route_fails_when_endpoint_snap_is_too_far(self) -> None:
        payload = {
            "code": "Ok",
            "routes": [{
                "distance": 5000,
                "duration": 600,
                "geometry": {"coordinates": [[120.0, 23.0], [120.1, 23.1]]},
                "legs": [{"steps": [{"distance": 5000}]}],
            }],
            "waypoints": [{"distance": 4}, {"distance": 800}],
        }
        case = {
            "id": "route",
            "description": "route",
            "from": [120.0, 23.0],
            "to": [120.1, 23.1],
            "min_distance_km": 4,
            "max_distance_km": 6,
        }
        with patch.object(validate, "request_json", return_value=(payload, 12.5)):
            result = validate.validate_route("http://localhost", case, 500, 10)
        self.assertFalse(result["passed"])
        self.assertFalse(result["checks"]["snap_distance"])

    def test_nearest_respects_threshold(self) -> None:
        payload = {"code": "Ok", "waypoints": [{"distance": 25}]}
        case = {
            "id": "nearest",
            "description": "nearest",
            "point": [120.0, 23.0],
            "max_distance_m": 50,
        }
        with patch.object(validate, "request_json", return_value=(payload, 3.0)):
            result = validate.validate_nearest("http://localhost", case, 10)
        self.assertTrue(result["passed"])


if __name__ == "__main__":
    unittest.main()

