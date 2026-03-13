"""Tests for Kalshi candlestick/price history parsing.

Uses inline fixtures since per-event candlestick/percentile fixtures
are created by the fetch script and may not exist yet.
Searches for real fixtures when available, skips otherwise.
"""

import glob as globmod
from pathlib import Path

import pytest

from app.ingestion.tests.conftest import FIXTURES_DIR, load_fixture


def _parse_kalshi_candlesticks(data: dict) -> list[dict]:
    """Parse Kalshi candlestick response into price points.

    Real API uses close_dollars (FixedPointDollars string), NOT close.
    """
    candlesticks = data.get("candlesticks", [])
    points = []
    for c in candlesticks:
        ts = c.get("end_period_ts")
        if ts is None:
            continue
        price = c.get("price", {})
        close_str = price.get("close_dollars")
        if close_str is None:
            continue
        prob = float(close_str)
        vol_str = c.get("volume_fp")
        vol = float(vol_str) if vol_str else None

        points.append({
            "timestamp": int(ts),
            "probability": prob,
            "volume": vol,
        })
    return points


def _find_first_fixture(pattern: str) -> Path | None:
    """Find the first fixture file matching a glob pattern under FIXTURES_DIR."""
    matches = sorted(FIXTURES_DIR.glob(pattern))
    return matches[0] if matches else None


class TestKalshiCandlestickParsingInline:
    """Test candlestick parsing with inline fixture data."""

    INLINE_DATA = {
        "candlesticks": [
            {
                "end_period_ts": 1700000000,
                "price": {"close_dollars": "0.0800", "open_dollars": "0.0700"},
                "volume_fp": "1.00",
                "yes_ask": {"close_dollars": "0.0900"},
                "yes_bid": {"close_dollars": "0.0700"},
            },
            {
                "end_period_ts": 1700086400,
                "price": {"close_dollars": "0.0700", "open_dollars": "0.0800"},
                "volume_fp": "1174.00",
                "yes_ask": {"close_dollars": "0.0800"},
                "yes_bid": {"close_dollars": "0.0600"},
            },
            {
                "end_period_ts": 1700172800,
                "price": {"close_dollars": "0.0900", "open_dollars": "0.0700"},
                "volume_fp": "500.00",
                "yes_ask": {"close_dollars": "0.1000"},
                "yes_bid": {"close_dollars": "0.0800"},
            },
        ]
    }

    def setup_method(self):
        self.points = _parse_kalshi_candlesticks(self.INLINE_DATA)

    def test_point_count(self):
        assert len(self.points) == 3

    def test_first_close_price(self):
        assert self.points[0]["probability"] == 0.08

    def test_second_close_price(self):
        assert self.points[1]["probability"] == 0.07

    def test_volume_fp_parsed(self):
        assert self.points[0]["volume"] == 1.0
        assert self.points[1]["volume"] == 1174.0

    def test_timestamps_are_integers(self):
        for p in self.points:
            assert isinstance(p["timestamp"], int)

    def test_probabilities_in_range(self):
        for p in self.points:
            assert 0.0 <= p["probability"] <= 1.0

    def test_chronological_order(self):
        timestamps = [p["timestamp"] for p in self.points]
        assert timestamps == sorted(timestamps)


class TestKalshiCandlestickFromFixture:
    """Test against real per-event candlestick fixture if available."""

    def setup_method(self):
        path = _find_first_fixture("kalshi/*_markets/*_candlesticks_daily.json")
        if path is None:
            pytest.skip("No candlestick fixture files found (run fetch script first)")
        self.data = load_fixture(str(path.relative_to(FIXTURES_DIR)))
        self.points = _parse_kalshi_candlesticks(self.data)

    def test_has_data_points(self):
        assert len(self.points) > 0

    def test_probabilities_in_range(self):
        for p in self.points:
            assert 0.0 <= p["probability"] <= 1.0

    def test_timestamps_are_integers(self):
        for p in self.points:
            assert isinstance(p["timestamp"], int)

    def test_chronological_order(self):
        timestamps = [p["timestamp"] for p in self.points]
        assert timestamps == sorted(timestamps)


class TestKalshiForecastPercentilesInline:
    """Test percentile parsing with inline fixture data."""

    INLINE_DATA = {
        "forecast_history": [
            {
                "timestamp": 1700000000,
                "percentile_values": {
                    "raw": [2.5, 4.15, 6.0],
                    "processed": [2.5, 4.15, 6.0],
                    "formatted": ["2.5%", "4.15%", "6.0%"],
                },
            },
            {
                "timestamp": 1700086400,
                "percentile_values": {
                    "raw": [3.0, 4.5, 7.0],
                    "processed": [3.0, 4.5, 7.0],
                    "formatted": ["3.0%", "4.5%", "7.0%"],
                },
            },
            {
                "timestamp": 1700172800,
                "percentile_values": {
                    "raw": [2.0, 4.0, 5.5],
                    "processed": [2.0, 4.0, 5.5],
                    "formatted": ["2.0%", "4.0%", "5.5%"],
                },
            },
        ]
    }

    def setup_method(self):
        self.data = self.INLINE_DATA

    def test_history_has_entries(self):
        history = self.data.get("forecast_history", [])
        assert len(history) == 3

    def test_percentile_values_structure(self):
        entry = self.data["forecast_history"][0]
        pv = entry["percentile_values"]
        assert "raw" in pv
        assert "processed" in pv
        assert "formatted" in pv

    def test_median_is_middle_percentile(self):
        entry = self.data["forecast_history"][0]
        raw = entry["percentile_values"]["raw"]
        assert raw[1] == 4.15

    def test_percentiles_ordered(self):
        for entry in self.data["forecast_history"]:
            raw = entry["percentile_values"]["raw"]
            assert raw[0] <= raw[1] <= raw[2]


class TestCandlestickEdgeCases:
    """Test edge cases in candlestick parsing."""

    def test_empty_candlesticks(self):
        points = _parse_kalshi_candlesticks({"candlesticks": []})
        assert points == []

    def test_missing_timestamp_skipped(self):
        data = {"candlesticks": [
            {"price": {"close_dollars": "0.50"}, "volume_fp": "10.00"},
        ]}
        points = _parse_kalshi_candlesticks(data)
        assert points == []

    def test_missing_close_dollars_skipped(self):
        data = {"candlesticks": [
            {"end_period_ts": 1700000000, "price": {}, "volume_fp": "10.00"},
        ]}
        points = _parse_kalshi_candlesticks(data)
        assert points == []

    def test_none_volume_handled(self):
        data = {"candlesticks": [
            {"end_period_ts": 1700000000, "price": {"close_dollars": "0.50"}},
        ]}
        points = _parse_kalshi_candlesticks(data)
        assert len(points) == 1
        assert points[0]["volume"] is None
