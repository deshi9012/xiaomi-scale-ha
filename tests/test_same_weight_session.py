from __future__ import annotations

import importlib.util
import unittest
from pathlib import Path


def _load_same_weight_session():
    metrics_path = (
        Path(__file__).resolve().parents[1]
        / "custom_components"
        / "xiaomi_scale_ha"
        / "metrics.py"
    )
    spec = importlib.util.spec_from_file_location("xiaomi_scale_ha_metrics", metrics_path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"Unable to load {metrics_path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module.same_weight_session


same_weight_session = _load_same_weight_session()


def _measurement(weight: float, unit: str, timestamp: str | None) -> dict:
    payload = {"weight": weight, "unit": unit}
    if timestamp is not None:
        payload["timestamp"] = timestamp
    return payload


class SameWeightSessionTests(unittest.TestCase):
    def test_same_weight_ten_seconds_apart(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(91.9, "kg", "2026-09-23T06:06:24+00:00")
        self.assertTrue(same_weight_session(previous, current))

    def test_weight_tolerance_at_thirty_seconds(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(92.1, "kg", "2026-09-23T06:06:44+00:00")
        self.assertTrue(same_weight_session(previous, current))

    def test_weight_difference_above_tolerance(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(92.11, "kg", "2026-09-23T06:06:20+00:00")
        self.assertFalse(same_weight_session(previous, current))

    def test_same_weight_thirty_one_seconds_apart(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(91.9, "kg", "2026-09-23T06:06:45+00:00")
        self.assertFalse(same_weight_session(previous, current))

    def test_same_weight_next_day(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-22T06:06:14+00:00")
        current = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        self.assertFalse(same_weight_session(previous, current))

    def test_different_unit(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(91.9, "lbs", "2026-09-23T06:06:20+00:00")
        self.assertFalse(same_weight_session(previous, current))

    def test_missing_timestamp(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(91.9, "kg", None)
        self.assertFalse(same_weight_session(previous, current))
        self.assertFalse(same_weight_session(current, previous))

    def test_invalid_timestamp(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = _measurement(91.9, "kg", "not-a-timestamp")
        self.assertFalse(same_weight_session(previous, current))

    def test_non_string_timestamp(self) -> None:
        previous = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        current = {"weight": 91.9, "unit": "kg", "timestamp": 1695456374}
        self.assertFalse(same_weight_session(previous, current))

    def test_consecutive_days_do_not_share_a_session(self) -> None:
        """A later-day reading must not match, so runtime will not copy _finalized."""
        previous = {
            "weight": 91.9,
            "unit": "kg",
            "timestamp": "2026-09-21T06:06:14+00:00",
            "_finalized": True,
        }
        day_two = _measurement(91.9, "kg", "2026-09-22T06:06:14+00:00")
        day_three = _measurement(91.9, "kg", "2026-09-23T06:06:14+00:00")
        self.assertFalse(same_weight_session(previous, day_two))
        self.assertFalse(same_weight_session(day_two, day_three))
        self.assertFalse(same_weight_session(day_three, previous))


if __name__ == "__main__":
    unittest.main()
