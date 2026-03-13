import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient, NormalizedEvent, NormalizedMarket, PricePoint
from app.ingestion.ev import extract_numeric_value

logger = structlog.get_logger()


def _categorize_event(title: str, description: str) -> str:
    """Infer event category from title and description text."""
    text = (title + " " + description).lower()
    if any(w in text for w in ["tariff", "trade", "embargo", "import", "export"]):
        return "trade"
    if any(w in text for w in ["war", "conflict", "invasion", "military", "attack", "coup"]):
        return "conflict"
    if any(w in text for w in ["regulation", "regulatory", "ban", "law", "legislation"]):
        return "regulatory"
    if any(w in text for w in ["climate", "hurricane", "flood", "drought", "emission"]):
        return "climate"
    if any(w in text for w in ["fed", "interest rate", "recession", "gdp", "inflation"]):
        return "economic"
    return "geopolitical"


def _extract_region(title: str, description: str) -> str:
    """Infer region from title and description text."""
    text = (title + " " + description).lower()
    region_map = {
        "china": "Asia-Pacific",
        "taiwan": "Asia-Pacific",
        "japan": "Asia-Pacific",
        "korea": "Asia-Pacific",
        "russia": "Europe",
        "ukraine": "Europe",
        "eu": "Europe",
        "europe": "Europe",
        "nato": "Europe",
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


class PolymarketClient(BaseMarketClient):
    """Client for Polymarket's CLOB API (public, no auth required)."""

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
            category = _categorize_event(title, description)
            region = _extract_region(title, description)
            api_markets = raw.get("markets", [])

            base = {
                "source": "polymarket",
                "source_url": f"https://polymarket.com/event/{slug}",
                "title": title[:500],
                "description": (description or title)[:2000],
                "category": category,
                "region": region,
                "status": "active",
                "resolution_date": raw.get("endDate", raw.get("end_date_iso")),
            }

            if len(api_markets) <= 1:
                # Flat event
                market = api_markets[0] if api_markets else raw
                condition_id = str(
                    market.get("conditionId", market.get("condition_id", raw.get("id", slug)))
                )
                price = market.get("lastTradePrice", market.get("outcomePrices", 0.5))
                price = self._parse_price(price)

                events.append(NormalizedEvent(
                    **base,
                    source_id=condition_id,
                    probability=price,
                    is_parent=False,
                ))
            else:
                # Parent event with multiple markets
                event_id = str(raw.get("id", slug))
                markets: list[NormalizedMarket] = []
                for mkt in api_markets:
                    condition_id = str(
                        mkt.get("conditionId", mkt.get("condition_id", ""))
                    )
                    child_title = mkt.get("question", mkt.get("title", title))
                    price = mkt.get("lastTradePrice", mkt.get("outcomePrices", 0.5))
                    price = self._parse_price(price)
                    outcome_label = child_title
                    outcome_value = extract_numeric_value(outcome_label)

                    markets.append(NormalizedMarket(
                        source_id=condition_id,
                        title=child_title,
                        probability=price,
                        volume=None,
                        outcome_label=outcome_label,
                        outcome_value=outcome_value,
                    ))

                # Infer mutually_exclusive: if markets have distinct outcome labels
                mutually_exclusive = len(markets) > 1

                events.append(NormalizedEvent(
                    **base,
                    source_id=event_id,
                    probability=0.0,
                    is_parent=True,
                    mutually_exclusive=mutually_exclusive,
                    markets=markets,
                ))

        # Next page cursor
        next_cursor = str(offset + limit) if len(raw_events) >= limit else None
        return events, next_cursor

    @staticmethod
    def _parse_price(price) -> float:
        """Normalize various price formats to a 0-1 float."""
        if isinstance(price, str):
            try:
                price = float(price)
            except (ValueError, TypeError):
                return 0.5
        if isinstance(price, list) and len(price) > 0:
            try:
                price = float(price[0])
            except (ValueError, TypeError):
                return 0.5
        return float(price) if price else 0.5

    async def fetch_prices(self, source_id: str) -> list[PricePoint]:
        """Fetch price history for a Polymarket market.

        source_id is a condition_id — we resolve it to a token_id first.
        """
        token_id = source_id
        try:
            market_url = f"{self.base_url}/markets"
            market_data = await self._request(market_url, params={"condition_id": source_id})
            markets = market_data if isinstance(market_data, list) else [market_data]
            if markets and isinstance(markets[0], dict):
                tokens = markets[0].get("tokens", [])
                if tokens:
                    token_id = tokens[0].get("token_id", source_id)
        except Exception:
            await logger.awarning(
                "Failed to resolve PM condition_id to token_id",
                source_id=source_id,
            )

        url = f"{self.base_url}/prices-history"
        params = {"market": token_id, "interval": "max", "fidelity": 60}

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
