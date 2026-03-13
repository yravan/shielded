import re

import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient, NormalizedEvent, PricePoint

logger = structlog.get_logger()


class MetaculusClient(BaseMarketClient):
    """Client for the Metaculus forecasting platform API."""

    def __init__(self):
        super().__init__()
        self.base_url = settings.METACULUS_API_URL
        self.api_key = settings.METACULUS_API_KEY

    @property
    def source_name(self) -> str:
        return "metaculus"

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def fetch_events_page(
        self, cursor: str | None = None
    ) -> tuple[list[NormalizedEvent], str | None]:
        """Fetch one page of questions from Metaculus (offset pagination)."""
        url = f"{self.base_url}/questions/"
        offset = int(cursor) if cursor else 0
        limit = 100
        params = {
            "limit": limit,
            "offset": offset,
            "status": "open",
            "type": "binary",
            "order_by": "-activity",
        }

        try:
            data = await self._request(url, headers=self._headers(), params=params)
        except Exception:
            await logger.aerror("Failed to fetch Metaculus events", offset=offset)
            return [], None

        results = data.get("results", []) if isinstance(data, dict) else data
        if not results:
            return [], None

        events: list[NormalizedEvent] = []

        for question in results:
            title = question.get("title", "")
            description = question.get("description", question.get("description_html", title))
            if "<" in description:
                description = re.sub(r"<[^>]+>", "", description)

            prediction = question.get("community_prediction", {})
            if isinstance(prediction, dict):
                probability = prediction.get("full", {}).get("q2", 0.5)
            else:
                probability = float(prediction) if prediction else 0.5

            events.append(NormalizedEvent(
                source="metaculus",
                source_id=str(question.get("id", "")),
                source_url=question.get(
                    "url", f"https://www.metaculus.com/questions/{question.get('id', '')}"
                ),
                title=title[:500],
                description=(description or title)[:2000],
                category="geopolitical",
                region="Global",
                status="active",
                probability=float(probability) if probability else 0.5,
                resolution_date=question.get("resolve_time"),
                is_parent=False,
            ))

        next_cursor = str(offset + limit) if len(results) >= limit else None
        return events, next_cursor

    async def fetch_prices(self, source_id: str, hours: int = 720) -> list[PricePoint]:
        """Fetch prediction history for a Metaculus question."""
        url = f"{self.base_url}/questions/{source_id}/"

        try:
            data = await self._request(url, headers=self._headers())
        except Exception:
            await logger.aerror("Failed to fetch Metaculus prices", source_id=source_id)
            return []

        prediction_timeseries = data.get("prediction_timeseries", [])
        if not isinstance(prediction_timeseries, list):
            return []

        points: list[PricePoint] = []
        for point in prediction_timeseries:
            community = point.get("community_prediction", 0.5)
            if isinstance(community, dict):
                community = community.get("full", {}).get("q2", 0.5)
            ts = point.get("t", point.get("time"))
            if ts is None:
                continue
            points.append(PricePoint(
                timestamp=int(ts),
                probability=float(community) if community else 0.5,
            ))

        return points
