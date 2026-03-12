import structlog

from app.config import settings
from app.ingestion.base import BaseMarketClient

logger = structlog.get_logger()


class MetaculusClient(BaseMarketClient):
    """Client for the Metaculus forecasting platform API."""

    def __init__(self):
        super().__init__()
        self.base_url = settings.METACULUS_API_URL
        self.api_key = settings.METACULUS_API_KEY

    def _headers(self) -> dict:
        return {
            "Authorization": f"Token {self.api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def fetch_events(self) -> list[dict]:
        """Fetch questions from Metaculus relevant to geopolitical risk."""
        url = f"{self.base_url}/questions/"
        params = {
            "limit": 100,
            "status": "open",
            "type": "binary",
            "order_by": "-activity",
        }

        try:
            data = await self._request(url, headers=self._headers(), params=params)
        except Exception:
            await logger.aerror("Failed to fetch Metaculus events")
            return []

        results = data.get("results", []) if isinstance(data, dict) else data
        events = []

        for question in results:
            title = question.get("title", "")
            description = question.get("description", question.get("description_html", title))
            # Strip HTML if present
            if "<" in description:
                import re

                description = re.sub(r"<[^>]+>", "", description)

            prediction = question.get("community_prediction", {})
            if isinstance(prediction, dict):
                probability = prediction.get("full", {}).get("q2", 0.5)
            else:
                probability = float(prediction) if prediction else 0.5

            events.append(
                {
                    "title": title[:500],
                    "description": description[:2000] if description else title,
                    "category": "geopolitical",
                    "region": "Global",
                    "source": "metaculus",
                    "source_id": str(question.get("id", "")),
                    "source_url": question.get(
                        "url", f"https://www.metaculus.com/questions/{question.get('id', '')}"
                    ),
                    "current_probability": float(probability) if probability else 0.5,
                    "resolution_date": question.get("resolve_time"),
                    "status": "active",
                }
            )

        await logger.ainfo("Fetched Metaculus events", count=len(events))
        return events

    async def fetch_prices(self, source_id: str) -> list[dict]:
        """Fetch prediction history for a Metaculus question."""
        url = f"{self.base_url}/questions/{source_id}/"

        try:
            data = await self._request(url, headers=self._headers())
        except Exception:
            await logger.aerror("Failed to fetch Metaculus prices", source_id=source_id)
            return []

        # Metaculus provides prediction history in the question detail
        prediction_timeseries = data.get("prediction_timeseries", [])
        if not isinstance(prediction_timeseries, list):
            return []

        points = []
        for point in prediction_timeseries:
            community = point.get("community_prediction", 0.5)
            if isinstance(community, dict):
                community = community.get("full", {}).get("q2", 0.5)
            points.append(
                {
                    "probability": float(community) if community else 0.5,
                    "source_bid": None,
                    "source_ask": None,
                    "volume_24h": None,
                    "recorded_at": point.get("t", point.get("time")),
                }
            )

        return points
