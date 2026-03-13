"""Tests for NormalizedEvent serialization roundtrip."""

import json
from dataclasses import asdict

from app.ingestion.base import NormalizedEvent, NormalizedMarket, PricePoint


class TestNormalizedEventRoundtrip:
    def test_flat_event_roundtrip(self):
        event = NormalizedEvent(
            source="kalshi",
            source_id="TEST-TICKER",
            source_url="https://kalshi.com/events/TEST",
            title="Test Event",
            description="A test event",
            category="economics",
            region="Global",
            status="active",
            resolution_date="2026-06-30T23:59:59Z",
            probability=0.72,
            is_parent=False,
            expected_value=None,
            is_quantitative=False,
            series_ticker="TEST",
            volume=53457.0,
        )

        data = asdict(event)
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        restored = NormalizedEvent(**loaded)

        assert restored.source == event.source
        assert restored.source_id == event.source_id
        assert restored.probability == event.probability
        assert restored.is_parent == event.is_parent
        assert restored.markets == []
        assert restored.series_ticker == "TEST"
        assert restored.volume == 53457.0

    def test_parent_event_with_markets_roundtrip(self):
        markets = [
            NormalizedMarket(
                source_id="MKT-1",
                title="4.00% or below",
                probability=0.15,
                volume=8920.0,
                outcome_label="4.00% or below",
                outcome_value=4.0,
                series_ticker="FED-RATE",
            ),
            NormalizedMarket(
                source_id="MKT-2",
                title="4.00% to 4.25%",
                probability=0.35,
                volume=12100.0,
                outcome_label="4.00% to 4.25%",
                outcome_value=4.125,
                series_ticker="FED-RATE",
                clob_token_id="abc123",
            ),
        ]
        event = NormalizedEvent(
            source="kalshi",
            source_id="EVT-1",
            source_url="https://kalshi.com/events/EVT-1",
            title="Rate Event",
            description="Test",
            category="economics",
            region="Global",
            status="active",
            is_parent=True,
            mutually_exclusive=True,
            probability=0.0,
            markets=markets,
            expected_value=4.08,
            is_quantitative=True,
            tags=["Finance", "Economy"],
            series_ticker="FED-RATE",
        )

        data = asdict(event)
        json_str = json.dumps(data)
        loaded = json.loads(json_str)

        loaded_markets = [NormalizedMarket(**m) for m in loaded.pop("markets")]
        restored = NormalizedEvent(**loaded, markets=loaded_markets)

        assert restored.is_parent is True
        assert restored.mutually_exclusive is True
        assert len(restored.markets) == 2
        assert restored.markets[0].source_id == "MKT-1"
        assert restored.markets[0].outcome_value == 4.0
        assert restored.markets[0].series_ticker == "FED-RATE"
        assert restored.markets[1].clob_token_id == "abc123"
        assert restored.expected_value == 4.08
        assert restored.is_quantitative is True
        assert restored.tags == ["Finance", "Economy"]
        assert restored.series_ticker == "FED-RATE"

    def test_event_with_new_fields_defaults(self):
        """Ensure old serialized data without new fields still loads."""
        minimal = {
            "source": "polymarket",
            "source_id": "abc123",
            "source_url": "https://polymarket.com/event/test",
            "title": "Test",
            "description": "Test",
            "category": "politics",
            "region": "Global",
            "status": "active",
        }
        event = NormalizedEvent(**minimal)
        assert event.is_parent is False
        assert event.expected_value is None
        assert event.is_quantitative is False
        assert event.markets == []
        assert event.image_url is None
        assert event.tags == []
        assert event.series_ticker is None
        assert event.volume is None

    def test_market_with_new_fields_defaults(self):
        """Ensure old market data without new fields still loads."""
        minimal = {
            "source_id": "test",
            "title": "Test",
            "probability": 0.5,
        }
        market = NormalizedMarket(**minimal)
        assert market.clob_token_id is None
        assert market.series_ticker is None
        assert market.image_url is None
        assert market.is_closed is False
        assert market.group_item_title is None


class TestPricePointSerialization:
    def test_price_point_list_roundtrip(self):
        points = [
            PricePoint(timestamp=1739404800, probability=0.66, volume=520.0),
            PricePoint(timestamp=1739491200, probability=0.68, volume=680.0),
            PricePoint(timestamp=1739577600, probability=0.70, volume=None),
        ]

        data = [asdict(p) for p in points]
        json_str = json.dumps(data)
        loaded = json.loads(json_str)
        restored = [PricePoint(**p) for p in loaded]

        assert len(restored) == 3
        assert restored[0].timestamp == 1739404800
        assert restored[0].probability == 0.66
        assert restored[0].volume == 520.0
        assert restored[2].volume is None
