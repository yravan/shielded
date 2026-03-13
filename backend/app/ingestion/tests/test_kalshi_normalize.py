"""Tests for Kalshi event normalization logic.

Tests against real per-event fixture data:
  - KXELONMARS-99: flat (single-market binary) event
  - KXNEWPOPE-70: multi-market parent event
  - EVSHARE-30JAN: quantitative event with strike_type/floor_strike
"""

from app.ingestion.tests.conftest import load_fixture


def _normalize_kalshi_event(raw_event: dict):
    """Normalize a raw Kalshi event dict matching the rewritten client behavior."""
    event_ticker = raw_event.get("event_ticker", "")
    series_ticker = raw_event.get("series_ticker", "")
    title = raw_event.get("title", "")
    description = raw_event.get("sub_title", title)
    category = raw_event.get("category", "").lower() or "geopolitical"
    mutually_exclusive = raw_event.get("mutually_exclusive", False)
    api_markets = raw_event.get("markets", [])

    result = {
        "source": "kalshi",
        "source_id": None,
        "source_url": f"https://kalshi.com/events/{event_ticker}",
        "title": title,
        "description": description,
        "category": category,
        "series_ticker": series_ticker,
        "is_parent": False,
        "mutually_exclusive": mutually_exclusive,
        "probability": 0.0,
        "markets": [],
    }

    if len(api_markets) <= 1:
        market = api_markets[0] if api_markets else {}
        ticker = market.get("ticker", event_ticker)
        last_price = market.get("last_price_dollars")
        prob = float(last_price) if last_price else 0.0

        result["source_id"] = ticker
        result["probability"] = prob
        result["resolution_date"] = market.get("close_time")
        vol_str = market.get("volume_fp")
        result["volume"] = float(vol_str) if vol_str else None
    else:
        result["source_id"] = event_ticker
        result["is_parent"] = True
        result["resolution_date"] = api_markets[0].get("close_time") if api_markets else None
        for mkt in api_markets:
            ticker = mkt.get("ticker", "")
            last_price = mkt.get("last_price_dollars")
            prob = float(last_price) if last_price else 0.0
            outcome_label = mkt.get("yes_sub_title", "")
            volume = mkt.get("volume_fp")
            vol_float = float(volume) if volume else None

            result["markets"].append({
                "source_id": ticker,
                "outcome_label": outcome_label,
                "probability": prob,
                "volume": vol_float,
                "series_ticker": series_ticker,
            })

    return result


def _strike_to_value(market: dict) -> float | None:
    """Extract a numeric outcome value from strike fields on a Kalshi market."""
    strike_type = market.get("strike_type")
    numeric_types = {
        "greater", "greater_or_equal", "less", "less_or_equal",
        "between", "functional", "structured",
    }
    if strike_type not in numeric_types:
        return None
    floor = market.get("floor_strike")
    cap = market.get("cap_strike")
    if floor is not None:
        return float(floor)
    if cap is not None:
        return float(cap)
    return None


class TestKalshiFlatEvent:
    """Test normalization of KXELONMARS-99 (single-market flat event)."""

    def setup_method(self):
        data = load_fixture("kalshi/KXELONMARS-99.json")
        self.raw = data
        self.normalized = _normalize_kalshi_event(self.raw)

    def test_source_id_is_market_ticker(self):
        assert self.normalized["source_id"] == "KXELONMARS-99"

    def test_probability_from_last_price_dollars(self):
        # "0.1000" -> 0.1
        assert self.normalized["probability"] == 0.10

    def test_source_url(self):
        assert self.normalized["source_url"] == "https://kalshi.com/events/KXELONMARS-99"

    def test_is_not_parent(self):
        assert self.normalized["is_parent"] is False

    def test_no_child_markets(self):
        assert self.normalized["markets"] == []

    def test_series_ticker_preserved(self):
        assert self.normalized["series_ticker"] == "KXELONMARS"

    def test_category_lowercased(self):
        assert self.normalized["category"] == "world"

    def test_resolution_date_from_close_time(self):
        assert self.normalized["resolution_date"] == "2099-08-01T04:59:00Z"

    def test_volume_parsed(self):
        assert self.normalized["volume"] == 53458.0


class TestKalshiMultiMarketEvent:
    """Test normalization of KXNEWPOPE-70 (7-market parent event)."""

    def setup_method(self):
        data = load_fixture("kalshi/KXNEWPOPE-70.json")
        self.raw = data
        self.normalized = _normalize_kalshi_event(self.raw)

    def test_is_parent(self):
        assert self.normalized["is_parent"] is True

    def test_source_id_is_event_ticker(self):
        assert self.normalized["source_id"] == "KXNEWPOPE-70"

    def test_market_count(self):
        assert len(self.normalized["markets"]) == 7

    def test_each_market_has_source_id(self):
        tickers = [m["source_id"] for m in self.normalized["markets"]]
        assert "KXNEWPOPE-70-PPAR" in tickers
        assert "KXNEWPOPE-70-AARB" in tickers
        assert "KXNEWPOPE-70-MZUP" in tickers

    def test_outcome_labels_from_yes_sub_title(self):
        labels = [m["outcome_label"] for m in self.normalized["markets"]]
        assert "Pietro Parolin" in labels
        assert "Anders Arborelius" in labels
        assert "Matteo Zuppi" in labels

    def test_market_probabilities(self):
        probs = {m["source_id"]: m["probability"] for m in self.normalized["markets"]}
        assert probs["KXNEWPOPE-70-PPAR"] == 0.09
        assert probs["KXNEWPOPE-70-AARB"] == 0.06
        assert probs["KXNEWPOPE-70-LANT"] == 0.08

    def test_mutually_exclusive(self):
        assert self.normalized["mutually_exclusive"] is True

    def test_market_volumes(self):
        vols = {m["source_id"]: m["volume"] for m in self.normalized["markets"]}
        assert vols["KXNEWPOPE-70-PPAR"] == 12745.0
        assert vols["KXNEWPOPE-70-AARB"] == 7951.0

    def test_series_ticker_on_markets(self):
        for m in self.normalized["markets"]:
            assert m["series_ticker"] == "KXNEWPOPE"


class TestKalshiQuantitativeEvent:
    """Test normalization of EVSHARE-30JAN (quantitative event with numeric strikes)."""

    def setup_method(self):
        data = load_fixture("kalshi/EVSHARE-30JAN.json")
        self.raw = data
        self.normalized = _normalize_kalshi_event(self.raw)
        self.api_markets = data.get("markets", [])

    def test_has_multiple_markets(self):
        assert len(self.api_markets) == 4

    def test_markets_have_strike_type(self):
        for mkt in self.api_markets:
            assert mkt.get("strike_type") == "greater"

    def test_markets_have_floor_strike(self):
        strikes = [mkt.get("floor_strike") for mkt in self.api_markets]
        assert 30 in strikes
        assert 20 in strikes
        assert 50 in strikes
        assert 10 in strikes

    def test_strike_to_value_produces_numeric(self):
        for mkt in self.api_markets:
            value = _strike_to_value(mkt)
            assert value is not None, f"Expected numeric value for {mkt['ticker']}"
            assert isinstance(value, float)

    def test_strike_to_value_matches_floor(self):
        values = {mkt["ticker"]: _strike_to_value(mkt) for mkt in self.api_markets}
        assert values["EVSHARE-30JAN-30"] == 30.0
        assert values["EVSHARE-30JAN-20"] == 20.0
        assert values["EVSHARE-30JAN-50"] == 50.0
        assert values["EVSHARE-30JAN-10"] == 10.0

    def test_strike_to_value_returns_none_for_binary(self):
        """A market without strike_type should return None."""
        binary_market = {"ticker": "FAKE", "market_type": "binary"}
        assert _strike_to_value(binary_market) is None

    def test_is_parent(self):
        assert self.normalized["is_parent"] is True

    def test_category(self):
        assert self.normalized["category"] == "climate and weather"


class TestFixedPointDollarsParsing:
    """Test parsing FixedPointDollars strings to floats."""

    def test_standard_price(self):
        assert float("0.5600") == 0.56

    def test_low_price(self):
        assert float("0.0100") == 0.01

    def test_high_price(self):
        assert float("0.9900") == 0.99

    def test_zero_price(self):
        assert float("0.0000") == 0.0

    def test_one_dollar(self):
        assert float("1.0000") == 1.0

    def test_volume_fp(self):
        assert float("15432.00") == 15432.0

    def test_small_volume(self):
        assert float("1.00") == 1.0
