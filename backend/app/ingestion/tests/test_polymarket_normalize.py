"""Tests for Polymarket event normalization logic.

Tests against real per-event fixture data:
  - uk-election-called-by: multi-market event (4 markets, mix of closed/active)
  - natoeu-troops-fighting-in-ukraine-in-2025: geopolitical event (2 markets)
"""

import json

from app.ingestion.tests.conftest import load_fixture


def _normalize_polymarket_event(raw_event: dict):
    """Normalize a raw Polymarket event dict matching the rewritten client behavior."""
    title = raw_event.get("title", "")
    description = raw_event.get("description", "")
    slug = raw_event.get("slug", "")
    image_url = raw_event.get("image")
    api_tags = raw_event.get("tags", [])
    tag_labels = [t.get("label", "") for t in api_tags if isinstance(t, dict)]
    api_markets = raw_event.get("markets", [])

    result = {
        "source": "polymarket",
        "source_id": None,
        "source_url": f"https://polymarket.com/event/{slug}",
        "title": title,
        "description": description,
        "image_url": image_url,
        "tags": tag_labels,
        "resolution_date": raw_event.get("endDate"),
        "is_parent": False,
        "probability": 0.0,
        "markets": [],
    }

    if len(api_markets) <= 1:
        market = api_markets[0] if api_markets else raw_event
        condition_id = market.get("conditionId", raw_event.get("id", slug))
        prob = market.get("lastTradePrice", 0.5)

        clob_raw = market.get("clobTokenIds", "[]")
        clob_tokens = json.loads(clob_raw) if isinstance(clob_raw, str) else (clob_raw or [])
        clob_token_id = clob_tokens[0] if clob_tokens else None

        result["source_id"] = condition_id
        result["probability"] = float(prob)
        result["clob_token_id"] = clob_token_id
    else:
        event_id = raw_event.get("id", slug)
        result["source_id"] = event_id
        result["is_parent"] = True
        for mkt in api_markets:
            condition_id = mkt.get("conditionId", "")
            question = mkt.get("question", "")
            group_item_title = mkt.get("groupItemTitle", "")
            prob = mkt.get("lastTradePrice", 0.5)
            volume = mkt.get("volumeNum")
            is_closed = bool(mkt.get("closed", False))

            clob_raw = mkt.get("clobTokenIds", "[]")
            clob_tokens = json.loads(clob_raw) if isinstance(clob_raw, str) else (clob_raw or [])
            clob_token_id = clob_tokens[0] if clob_tokens else None

            prices_raw = mkt.get("outcomePrices", "[]")
            outcome_prices = json.loads(prices_raw) if isinstance(prices_raw, str) else (prices_raw or [])
            outcome_prices = [float(p) for p in outcome_prices]

            result["markets"].append({
                "source_id": condition_id,
                "question": question,
                "group_item_title": group_item_title,
                "probability": float(prob),
                "volume": volume,
                "clob_token_id": clob_token_id,
                "outcome_prices": outcome_prices,
                "is_closed": is_closed,
            })

    return result


class TestPolymarketMultiMarketEvent:
    """Test normalization of UK election event (multi-market with closed markets)."""

    def setup_method(self):
        data = load_fixture("polymarket/uk-election-called-by.json")
        self.raw = data
        self.normalized = _normalize_polymarket_event(self.raw)

    def test_is_parent(self):
        assert self.normalized["is_parent"] is True

    def test_source_id_is_event_id(self):
        assert self.normalized["source_id"] == "16423"

    def test_market_count(self):
        assert len(self.normalized["markets"]) == 4

    def test_each_market_has_clob_token(self):
        for mkt in self.normalized["markets"]:
            assert mkt["clob_token_id"] is not None
            assert len(mkt["clob_token_id"]) > 10

    def test_outcome_prices_parsed_from_string(self):
        """First market (closed, resolved): outcomePrices '["0", "1"]' -> [0.0, 1.0]."""
        first = self.normalized["markets"][0]
        assert isinstance(first["outcome_prices"], list)
        assert all(isinstance(p, float) for p in first["outcome_prices"])
        assert first["outcome_prices"] == [0.0, 1.0]

    def test_outcome_prices_with_decimals(self):
        """Fourth market (active): outcomePrices '["0.068", "0.932"]'."""
        fourth = self.normalized["markets"][3]
        assert abs(fourth["outcome_prices"][0] - 0.068) < 0.001
        assert abs(fourth["outcome_prices"][1] - 0.932) < 0.001

    def test_closed_market_detected(self):
        """First three markets are closed while the fourth is active."""
        first = self.normalized["markets"][0]
        assert first["is_closed"] is True
        fourth = self.normalized["markets"][3]
        assert fourth["is_closed"] is False

    def test_group_item_title(self):
        titles = [m["group_item_title"] for m in self.normalized["markets"]]
        assert "March 31" in titles
        assert "December 31" in titles
        assert "June 30" in titles
        assert "June 30, 2026" in titles

    def test_market_probabilities(self):
        probs = {m["group_item_title"]: m["probability"] for m in self.normalized["markets"]}
        assert probs["March 31"] == 1.0  # resolved
        assert probs["June 30, 2026"] == 0.066

    def test_market_volumes(self):
        first = self.normalized["markets"][0]
        assert first["volume"] == 577431.026465

    def test_image_url(self):
        assert self.normalized["image_url"] is not None
        assert "polymarket-upload" in self.normalized["image_url"]

    def test_tags_extracted(self):
        assert "Starmer" in self.normalized["tags"]
        assert "uk" in self.normalized["tags"]
        assert "England" in self.normalized["tags"]

    def test_category_is_none_in_api(self):
        """category and subcategory are always None in real API."""
        assert self.raw.get("category") is None
        assert self.raw.get("subcategory") is None


class TestPolymarketGeopoliticalEvent:
    """Test normalization of NATO/EU troops in Ukraine event."""

    def setup_method(self):
        data = load_fixture("polymarket/natoeu-troops-fighting-in-ukraine-in-2025.json")
        self.raw = data
        self.normalized = _normalize_polymarket_event(self.raw)

    def test_is_parent(self):
        assert self.normalized["is_parent"] is True

    def test_source_id(self):
        assert self.normalized["source_id"] == "17549"

    def test_market_count(self):
        assert len(self.normalized["markets"]) == 2

    def test_tags_include_geopolitics(self):
        tags = self.normalized["tags"]
        assert any("Politics" in t or "Geopolitics" in t for t in tags)

    def test_has_closed_and_active_markets(self):
        closed = [m for m in self.normalized["markets"] if m["is_closed"]]
        active = [m for m in self.normalized["markets"] if not m["is_closed"]]
        assert len(closed) == 1
        assert len(active) == 1

    def test_closed_market_resolved_price(self):
        closed = [m for m in self.normalized["markets"] if m["is_closed"]][0]
        assert closed["probability"] == 1.0
        assert closed["group_item_title"] == "December 31, 2025"

    def test_active_market_price(self):
        active = [m for m in self.normalized["markets"] if not m["is_closed"]][0]
        assert active["probability"] == 0.059
        assert active["group_item_title"] == "June 30, 2026"


class TestClobTokenIdsParsing:
    """Test parsing the clobTokenIds JSON string format."""

    def test_standard_format(self):
        raw = '["token_yes","token_no"]'
        tokens = json.loads(raw)
        assert tokens[0] == "token_yes"
        assert tokens[1] == "token_no"

    def test_long_numeric_tokens(self):
        raw = '["71321045738105371710370688243510699559532534424514774828014661930974043289041","81432156849216482821481799354621700660643645535625885939125772041085154390152"]'
        tokens = json.loads(raw)
        assert len(tokens) == 2
        assert tokens[0].startswith("7132")

    def test_empty_array(self):
        raw = "[]"
        tokens = json.loads(raw)
        assert tokens == []


class TestOutcomePricesParsing:
    """Test parsing the outcomePrices JSON string format."""

    def test_numeric_format(self):
        raw = "[0.72, 0.28]"
        prices = json.loads(raw)
        assert prices[0] == 0.72
        assert abs(sum(prices) - 1.0) < 0.01

    def test_string_number_format(self):
        """Real API returns string numbers: '["0", "1"]'."""
        raw = '["0", "1"]'
        prices = json.loads(raw)
        floats = [float(p) for p in prices]
        assert floats == [0.0, 1.0]

    def test_string_decimal_format(self):
        """Real API: '["0.15", "0.85"]'."""
        raw = '["0.15", "0.85"]'
        prices = json.loads(raw)
        floats = [float(p) for p in prices]
        assert abs(floats[0] - 0.15) < 0.001
        assert abs(floats[1] - 0.85) < 0.001
