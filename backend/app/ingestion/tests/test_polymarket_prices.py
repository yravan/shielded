"""Tests for Polymarket price history parsing.

Uses inline fixtures since per-event price fixtures are created by the
fetch script and may not exist yet. Searches for real fixtures when
available, skips otherwise.
"""

from pathlib import Path

import pytest

from app.ingestion.tests.conftest import FIXTURES_DIR, load_fixture


def _parse_polymarket_prices(data) -> list[dict]:
    """Parse Polymarket price history response into price points."""
    history = data.get("history", data) if isinstance(data, dict) else data
    if not isinstance(history, list):
        return []

    points = []
    for pt in history:
        t = pt.get("t")
        p = pt.get("p")
        if t is None or p is None:
            continue
        points.append({
            "timestamp": int(t),
            "probability": float(p),
        })
    return points


def _find_first_fixture(pattern: str) -> Path | None:
    """Find the first fixture file matching a glob pattern under FIXTURES_DIR."""
    matches = sorted(FIXTURES_DIR.glob(pattern))
    return matches[0] if matches else None


class TestPolymarketPriceHistoryInline:
    """Test price parsing with inline fixture data."""

    INLINE_DATA = {
        "history": [
            {"t": 1738800000, "p": 0.65},
            {"t": 1738886400, "p": 0.66},
            {"t": 1738972800, "p": 0.64},
            {"t": 1739059200, "p": 0.68},
            {"t": 1739145600, "p": 0.70},
            {"t": 1739232000, "p": 0.69},
            {"t": 1739318400, "p": 0.71},
            {"t": 1739404800, "p": 0.73},
            {"t": 1739491200, "p": 0.72},
        ]
    }

    def setup_method(self):
        self.points = _parse_polymarket_prices(self.INLINE_DATA)

    def test_point_count(self):
        assert len(self.points) == 9

    def test_prices_in_range(self):
        for p in self.points:
            assert 0.0 <= p["probability"] <= 1.0

    def test_timestamps_are_integers(self):
        for p in self.points:
            assert isinstance(p["timestamp"], int)

    def test_first_point(self):
        assert self.points[0]["timestamp"] == 1738800000
        assert self.points[0]["probability"] == 0.65

    def test_last_point(self):
        assert self.points[-1]["timestamp"] == 1739491200
        assert self.points[-1]["probability"] == 0.72

    def test_chronological_order(self):
        timestamps = [p["timestamp"] for p in self.points]
        assert timestamps == sorted(timestamps)


class TestPolymarketPriceFromFixture:
    """Test against real per-event price fixture if available."""

    def setup_method(self):
        path = _find_first_fixture("polymarket/*_markets/*_prices.json")
        if path is None:
            pytest.skip("No price fixture files found (run fetch script first)")
        self.data = load_fixture(str(path.relative_to(FIXTURES_DIR)))
        self.points = _parse_polymarket_prices(self.data)

    def test_has_data_points(self):
        assert len(self.points) > 0

    def test_prices_in_range(self):
        for p in self.points:
            assert 0.0 <= p["probability"] <= 1.0

    def test_timestamps_are_integers(self):
        for p in self.points:
            assert isinstance(p["timestamp"], int)

    def test_chronological_order(self):
        timestamps = [p["timestamp"] for p in self.points]
        assert timestamps == sorted(timestamps)


class TestPolymarketPriceEdgeCases:
    def test_empty_history(self):
        points = _parse_polymarket_prices({"history": []})
        assert points == []

    def test_direct_array_response(self):
        data = [{"t": 100, "p": 0.5}, {"t": 200, "p": 0.6}]
        points = _parse_polymarket_prices(data)
        assert len(points) == 2

    def test_missing_fields_skipped(self):
        data = {"history": [{"t": 100}, {"p": 0.5}, {"t": 200, "p": 0.6}]}
        points = _parse_polymarket_prices(data)
        assert len(points) == 1
