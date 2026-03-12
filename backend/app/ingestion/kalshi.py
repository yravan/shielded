import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient

logger = structlog.get_logger()


class KalshiClient(BaseMarketClient):
    """Client for the Kalshi prediction market API."""

    def __init__(self):
        super().__init__()
        self.base_url = settings.KALSHI_API_URL
        self.api_key = settings.KALSHI_API_KEY

    def _headers(self) -> dict:
        return {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def fetch_events(self) -> list[dict]:
        """Fetch events from Kalshi's event and market endpoints."""
        url = f"{self.base_url}/events"
        params = {"limit": 100, "status": "open"}

        try:
            data = await self._request(url, headers=self._headers(), params=params)
        except Exception:
            await logger.aerror("Failed to fetch Kalshi events")
            return []

        raw_events = data.get("events", []) if isinstance(data, dict) else data
        events = []

        for raw in raw_events:
            title = raw.get("title", "")
            description = raw.get("sub_title", raw.get("description", title))
            category = raw.get("category", "geopolitical").lower()
            if category not in (
                "trade",
                "conflict",
                "regulatory",
                "climate",
                "geopolitical",
                "economic",
            ):
                category = "geopolitical"

            # Get the first market's price if available
            markets = raw.get("markets", [])
            probability = 0.5
            if markets:
                yes_price = markets[0].get("yes_bid", markets[0].get("last_price", 50))
                probability = float(yes_price) / 100.0 if yes_price > 1 else float(yes_price)

            events.append(
                {
                    "title": title,
                    "description": description[:2000] if description else title,
                    "category": category,
                    "region": "Global",
                    "source": "kalshi",
                    "source_id": str(raw.get("event_ticker", raw.get("id", ""))),
                    "source_url": f"https://kalshi.com/events/{raw.get('event_ticker', '')}",
                    "current_probability": probability,
                    "resolution_date": raw.get("close_time", raw.get("expected_expiration_time")),
                    "status": "active",
                }
            )

        await logger.ainfo("Fetched Kalshi events", count=len(events))
        return events

    async def fetch_prices(self, source_id: str) -> list[dict]:
        """Fetch price history for a Kalshi market."""
        url = f"{self.base_url}/markets/{source_id}/history"
        params = {"limit": 1000}

        try:
            data = await self._request(url, headers=self._headers(), params=params)
        except Exception:
            await logger.aerror("Failed to fetch Kalshi prices", source_id=source_id)
            return []

        history = data.get("history", data.get("snapshots", []))
        if not isinstance(history, list):
            return []

        points = []
        for point in history:
            yes_price = point.get("yes_price", point.get("price", 50))
            prob = float(yes_price) / 100.0 if yes_price > 1 else float(yes_price)
            points.append(
                {
                    "probability": prob,
                    "source_bid": point.get("yes_bid"),
                    "source_ask": point.get("yes_ask"),
                    "volume_24h": point.get("volume"),
                    "recorded_at": point.get("ts", point.get("created_time")),
                }
            )

        return points
