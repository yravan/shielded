import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient

logger = structlog.get_logger()

# Geopolitical keywords for filtering relevant markets
GEO_KEYWORDS = [
    "tariff",
    "sanction",
    "war",
    "conflict",
    "nato",
    "china",
    "russia",
    "iran",
    "taiwan",
    "trade",
    "embargo",
    "regulation",
    "climate",
    "treaty",
    "election",
    "coup",
    "invasion",
    "nuclear",
    "oil",
    "opec",
    "brexit",
    "eu",
    "fed",
    "interest rate",
    "recession",
    "gdp",
    "inflation",
]


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

    async def fetch_events(self) -> list[dict]:
        """Fetch geopolitically-relevant markets from Polymarket."""
        url = f"{self.base_url}/markets"
        params = {"limit": 100, "active": True}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror("Failed to fetch Polymarket events")
            return []

        markets = data if isinstance(data, list) else data.get("data", data.get("markets", []))
        events = []
        for market in markets:
            title = market.get("question", market.get("title", ""))
            description = market.get("description", "")
            text_lower = (title + " " + description).lower()

            if not any(kw in text_lower for kw in GEO_KEYWORDS):
                continue

            price = market.get("lastTradePrice", market.get("outcomePrices", 0.5))
            if isinstance(price, str):
                try:
                    price = float(price)
                except (ValueError, TypeError):
                    price = 0.5
            if isinstance(price, list) and len(price) > 0:
                try:
                    price = float(price[0])
                except (ValueError, TypeError):
                    price = 0.5

            events.append(
                {
                    "title": title,
                    "description": description[:2000] if description else title,
                    "category": _categorize_event(title, description),
                    "region": _extract_region(title, description),
                    "source": "polymarket",
                    "source_id": str(
                        market.get("condition_id", market.get("id", market.get("slug", "")))
                    ),
                    "source_url": f"https://polymarket.com/event/{market.get('slug', '')}",
                    "current_probability": float(price) if price else 0.5,
                    "resolution_date": market.get("end_date_iso", market.get("endDate")),
                    "status": "active",
                }
            )

        await logger.ainfo("Fetched Polymarket events", count=len(events))
        return events

    async def fetch_prices(self, source_id: str) -> list[dict]:
        """Fetch price history for a Polymarket market."""
        url = f"{self.base_url}/prices-history"
        params = {"market": source_id, "interval": "max", "fidelity": 60}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror("Failed to fetch Polymarket prices", source_id=source_id)
            return []

        history = data.get("history", data) if isinstance(data, dict) else data
        if not isinstance(history, list):
            return []

        points = []
        for point in history:
            timestamp = point.get("t", point.get("timestamp"))
            price = point.get("p", point.get("price", 0.5))
            points.append(
                {
                    "probability": float(price),
                    "source_bid": None,
                    "source_ask": None,
                    "volume_24h": point.get("volume", None),
                    "recorded_at": timestamp,
                }
            )

        return points
