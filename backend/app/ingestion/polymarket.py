import json

import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient, NormalizedEvent, NormalizedMarket, PricePoint, is_event_relevant

logger = structlog.get_logger()


# --- Tag-based category extraction ---

_TAG_TO_CATEGORY: dict[str, str] = {
    "politics": "geopolitical",
    "geopolitics": "geopolitical",
    "world": "geopolitical",
    "finance": "economic",
    "economy": "economic",
    "stocks": "economic",
    "business": "economic",
    "crypto": "economic",
    "tech": "regulatory",
    "science": "regulatory",
    "climate": "climate",
    "weather": "climate",
    "conflict": "conflict",
    "war": "conflict",
    "military": "conflict",
    "trade": "trade",
    "tariff": "trade",
}

_TAG_TO_REGION: dict[str, str] = {
    "china": "Asia-Pacific",
    "taiwan": "Asia-Pacific",
    "japan": "Asia-Pacific",
    "korea": "Asia-Pacific",
    "india": "Asia-Pacific",
    "russia": "Europe",
    "ukraine": "Europe",
    "eu": "Europe",
    "europe": "Europe",
    "nato": "Europe",
    "uk": "Europe",
    "france": "Europe",
    "iran": "Middle East",
    "israel": "Middle East",
    "saudi": "Middle East",
    "africa": "Africa",
    "us": "North America",
    "america": "North America",
    "canada": "North America",
    "mexico": "Latin America",
    "brazil": "Latin America",
}


def _extract_category_from_tags(tags: list[dict]) -> str:
    """Extract category from Polymarket tags array. Falls back to keyword inference."""
    for tag in tags:
        label = tag.get("label", "").lower()
        if label in _TAG_TO_CATEGORY:
            return _TAG_TO_CATEGORY[label]
    return "geopolitical"


def _extract_region_from_tags(tags: list[dict]) -> str:
    """Extract region from tags array. Falls back to 'Global'."""
    for tag in tags:
        label = tag.get("label", "").lower()
        slug = tag.get("slug", "").lower()
        for key, region in _TAG_TO_REGION.items():
            if key in label or key in slug:
                return region
    return "Global"


def _extract_region_from_text(title: str, description: str) -> str:
    """Fallback region inference from title/description text."""
    text = (title + " " + description).lower()
    region_map = {
        "china": "Asia-Pacific",
        "taiwan": "Asia-Pacific",
        "japan": "Asia-Pacific",
        "korea": "Asia-Pacific",
        "india": "Asia-Pacific",
        "russia": "Europe",
        "ukraine": "Europe",
        "eu": "Europe",
        "europe": "Europe",
        "nato": "Europe",
        "uk": "Europe",
        "france": "Europe",
        "macron": "Europe",
        "starmer": "Europe",
        "iran": "Middle East",
        "israel": "Middle East",
        "saudi": "Middle East",
        "opec": "Middle East",
        "africa": "Africa",
        "us": "North America",
        "america": "North America",
        "canada": "North America",
        "mexico": "Latin America",
        "brazil": "Latin America",
    }
    for keyword, region in region_map.items():
        if keyword in text:
            return region
    return "Global"


import re


def _shorten_market_title(question: str, parent_title: str) -> str:
    """Extract the key differentiator from a verbose child market question.

    E.g. 'Will Google (GOOGL) finish week of March 9 above $300?' -> '> $300'
         'Will the highest temperature in Munich be 7°C on March 15?' -> '7°C'
    """
    # Try common patterns
    # "above/below $X" or "above/below X°"
    m = re.search(r'(above|below|over|under|at least|at most)\s+(\$?[\d,.]+[°℉℃]?[FfCc]?)', question, re.I)
    if m:
        direction = m.group(1).lower()
        value = m.group(2)
        prefix = ">" if direction in ("above", "over", "at least") else "<"
        return f"{prefix} {value}"

    # "between X-Y" or "be X-Y°F"
    m = re.search(r'(?:between\s+)?(\$?[\d,.]+)\s*[-–]\s*(\$?[\d,.]+[°℉℃]?[FfCc]?)', question)
    if m:
        return f"{m.group(1)}-{m.group(2)}"

    # "be X°C/°F on"
    m = re.search(r'be\s+(\$?[\d,.]+[°℉℃][FfCc]?)\s', question)
    if m:
        return m.group(1)

    # "be $X or" / "hit $X"
    m = re.search(r'(?:be|hit|reach|close at)\s+(\$[\d,.]+)', question)
    if m:
        return m.group(1)

    return question


def _parse_clob_token_ids(raw: str | list | None) -> list[str]:
    """Parse clobTokenIds from JSON string or list."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            return json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    return raw if isinstance(raw, list) else []


def _parse_outcome_prices(raw: str | list | None) -> list[float]:
    """Parse outcomePrices — handles JSON string with string or numeric elements."""
    if raw is None:
        return []
    if isinstance(raw, str):
        try:
            parsed = json.loads(raw)
        except (json.JSONDecodeError, TypeError):
            return []
    else:
        parsed = raw
    if not isinstance(parsed, list):
        return []
    return [float(p) for p in parsed]


class PolymarketClient(BaseMarketClient):
    """Client for Polymarket's Gamma + CLOB APIs."""

    def __init__(self):
        super().__init__()
        self.base_url = settings.POLYMARKET_API_URL
        self.gamma_url = settings.POLYMARKET_GAMMA_API_URL

    @property
    def source_name(self) -> str:
        return "polymarket"

    async def fetch_events_page(
        self, cursor: str | None = None
    ) -> tuple[list[NormalizedEvent], str | None]:
        """Fetch one page of events from Polymarket's Gamma API (offset pagination)."""
        url = f"{self.gamma_url}/events"
        offset = int(cursor) if cursor else 0
        limit = 100
        params: dict = {"limit": limit, "active": True, "closed": False, "offset": offset}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.awarning("Gamma API failed", offset=offset)
            return [], None

        raw_events = data if isinstance(data, list) else data.get("data", data.get("events", []))

        if not raw_events:
            return [], None

        events: list[NormalizedEvent] = []

        for raw in raw_events:
            title = raw.get("title", "")
            description = raw.get("description", "")
            slug = raw.get("slug", "")
            image_url = raw.get("image")
            api_tags = raw.get("tags", [])
            tag_labels = [t.get("label", "") for t in api_tags if isinstance(t, dict)]

            # Skip events not relevant to geopolitical risk
            if not is_event_relevant(title, description, tag_labels):
                continue

            # Category from tags (category/subcategory fields are always None)
            category = _extract_category_from_tags(api_tags)

            # Region from tags first, then text fallback
            region = _extract_region_from_tags(api_tags)
            if region == "Global":
                region = _extract_region_from_text(title, description)

            api_markets = raw.get("markets", [])
            event_volume = raw.get("volume")
            event_volume_float = float(event_volume) if event_volume else None

            base = {
                "source": "polymarket",
                "source_url": f"https://polymarket.com/event/{slug}",
                "title": title[:500],
                "description": (description or title)[:2000],
                "category": category,
                "region": region,
                "status": "active",
                "resolution_date": raw.get("endDate"),
                "image_url": image_url,
                "tags": tag_labels,
                "volume": event_volume_float,
            }

            if len(api_markets) <= 1:
                # Flat event
                market = api_markets[0] if api_markets else raw
                condition_id = str(
                    market.get("conditionId", market.get("condition_id", raw.get("id", slug)))
                )
                prob = market.get("lastTradePrice", 0.5)
                prob = float(prob) if prob is not None else 0.5

                clob_tokens = _parse_clob_token_ids(market.get("clobTokenIds"))
                clob_token_id = clob_tokens[0] if clob_tokens else None

                volume = market.get("volumeNum")

                events.append(NormalizedEvent(
                    **base,
                    source_id=condition_id,
                    probability=prob,
                    is_parent=False,
                    markets=[NormalizedMarket(
                        source_id=condition_id,
                        title=market.get("question", title),
                        probability=prob,
                        volume=float(volume) if volume else None,
                        clob_token_id=clob_token_id,
                        image_url=market.get("image"),
                        is_closed=bool(market.get("closed", False)),
                        group_item_title=market.get("groupItemTitle"),
                    )],
                ))
            else:
                # Parent event with multiple markets
                event_id = str(raw.get("id", slug))
                markets: list[NormalizedMarket] = []
                for mkt in api_markets:
                    condition_id = str(mkt.get("conditionId", ""))
                    is_closed = bool(mkt.get("closed", False))

                    # Use groupItemTitle for multi-market outcome labels
                    group_title = mkt.get("groupItemTitle", "")
                    question = mkt.get("question", mkt.get("title", title))
                    outcome_label = group_title or question

                    # Use API-provided bounds instead of regex parsing
                    lower = mkt.get("lowerBound")
                    upper = mkt.get("upperBound")
                    if lower is not None and upper is not None:
                        outcome_value = (float(lower) + float(upper)) / 2.0
                    elif lower is not None:
                        outcome_value = float(lower)
                    elif upper is not None:
                        outcome_value = float(upper)
                    else:
                        outcome_value = None

                    prob = mkt.get("lastTradePrice", 0.5)
                    prob = float(prob) if prob is not None else 0.5

                    volume = mkt.get("volumeNum")
                    clob_tokens = _parse_clob_token_ids(mkt.get("clobTokenIds"))
                    clob_token_id = clob_tokens[0] if clob_tokens else None

                    short_title = group_title or _shorten_market_title(question, title)

                    markets.append(NormalizedMarket(
                        source_id=condition_id,
                        title=short_title,
                        probability=prob,
                        volume=float(volume) if volume else None,
                        outcome_label=outcome_label,
                        outcome_value=outcome_value,
                        clob_token_id=clob_token_id,
                        image_url=mkt.get("image"),
                        is_closed=is_closed,
                        group_item_title=group_title,
                    ))

                mutually_exclusive = len(markets) > 1

                # Use API-provided EV fields for classification and expected value
                estimated_value = raw.get("estimatedValue")
                ev_is_quant = False
                ev_value = None
                if estimated_value and raw.get("estimateValue") and not raw.get("cantEstimate"):
                    ev_value = float(estimated_value)
                    ev_is_quant = True

                events.append(NormalizedEvent(
                    **base,
                    source_id=event_id,
                    probability=0.0,
                    is_parent=True,
                    mutually_exclusive=mutually_exclusive,
                    markets=markets,
                    expected_value=ev_value,
                    is_quantitative=ev_is_quant,
                ))

        next_cursor = str(offset + limit) if len(raw_events) >= limit else None
        return events, next_cursor

    async def fetch_prices(self, source_id: str, hours: int = 720, series_ticker: str | None = None) -> list[PricePoint]:
        """Fetch price history for a Polymarket market.

        Uses clob_token_id directly from the cached event data when available,
        avoiding the unreliable Gamma /markets?condition_id=X call.
        """
        from app.cache import EventCache
        import redis.asyncio as aioredis
        from app.config import settings as app_settings

        token_id = None

        # Try to get clob_token_id from cached event data
        try:
            redis = aioredis.from_url(app_settings.REDIS_URL, decode_responses=True)
            cache = EventCache(redis)
            cached_event = await cache.get_event("polymarket", source_id)
            if cached_event and cached_event.markets:
                for m in cached_event.markets:
                    if m.source_id == source_id and m.clob_token_id:
                        token_id = m.clob_token_id
                        break
                if not token_id and cached_event.markets[0].clob_token_id:
                    token_id = cached_event.markets[0].clob_token_id

            # Also check if source_id itself is stored as event with market info
            if not token_id:
                all_events = await cache.get_all_events("polymarket")
                if all_events:
                    for evt in all_events:
                        for m in evt.markets:
                            if m.source_id == source_id and m.clob_token_id:
                                token_id = m.clob_token_id
                                break
                        if token_id:
                            break

            await redis.aclose()
        except Exception:
            pass

        # Last resort: try CLOB /markets/{condition_id} endpoint
        if not token_id:
            try:
                market_data = await self._request(
                    f"{self.base_url}/markets/{source_id}"
                )
                if isinstance(market_data, dict):
                    tokens = market_data.get("tokens", [])
                    if tokens:
                        token_id = tokens[0].get("token_id", source_id)
            except Exception:
                await logger.awarning(
                    "Failed to resolve PM token_id",
                    source_id=source_id,
                )

        if not token_id:
            token_id = source_id

        url = f"{self.base_url}/prices-history"
        # fidelity = interval in minutes between data points
        if hours > 2160:  # > 3 months: 1 day intervals
            fidelity = 1440
        elif hours > 720:  # > 1 month: 6 hour intervals
            fidelity = 360
        else:  # <= 1 month: 1 hour intervals
            fidelity = 60
        params = {"market": token_id, "interval": "max", "fidelity": fidelity}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror(
                "Failed to fetch PM prices", source_id=source_id, token_id=token_id
            )
            return []

        history = data.get("history", data) if isinstance(data, dict) else data
        if not isinstance(history, list):
            return []

        points: list[PricePoint] = []
        for point in history:
            timestamp = point.get("t", point.get("timestamp"))
            if timestamp is None:
                continue
            price = point.get("p", point.get("price", 0.5))
            points.append(PricePoint(
                timestamp=int(timestamp),
                probability=float(price),
                volume=point.get("volume"),
            ))

        return points
