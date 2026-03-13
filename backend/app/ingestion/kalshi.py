import base64
import time
from pathlib import Path
from urllib.parse import urlparse

import structlog
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import settings
from app.ingestion.base import BaseMarketClient, NormalizedEvent, NormalizedMarket, PricePoint
from app.ingestion.ev import extract_numeric_value

logger = structlog.get_logger()


def _load_private_key():
    """Load the RSA private key from the file path in KALSHI_API_KEY."""
    key_path = Path(settings.KALSHI_API_KEY)
    if not key_path.is_absolute():
        key_path = Path(__file__).resolve().parents[2] / key_path
    pem_data = key_path.read_bytes()
    return serialization.load_pem_private_key(pem_data, password=None)


def _sign_request(private_key, timestamp_ms: int, method: str, path: str) -> str:
    """Create RSA PSS signature for Kalshi API request."""
    message = f"{timestamp_ms}{method}{path}".encode()
    signature = private_key.sign(
        message,
        padding.PSS(
            mgf=padding.MGF1(hashes.SHA256()),
            salt_length=padding.PSS.MAX_LENGTH,
        ),
        hashes.SHA256(),
    )
    return base64.b64encode(signature).decode()


class KalshiClient(BaseMarketClient):
    """Client for the Kalshi prediction market API with RSA request signing."""

    def __init__(self):
        super().__init__()
        self.base_url = settings.KALSHI_API_URL
        self.key_id = settings.KALSHI_KEY_ID
        self._private_key = _load_private_key()

    @property
    def source_name(self) -> str:
        return "kalshi"

    def _signed_headers(self, method: str, url: str) -> dict:
        """Build headers with RSA PSS signature for the given request."""
        timestamp_ms = int(time.time() * 1000)
        path = urlparse(url).path
        signature = _sign_request(self._private_key, timestamp_ms, method.upper(), path)
        return {
            "KALSHI-ACCESS-KEY": self.key_id,
            "KALSHI-ACCESS-SIGNATURE": signature,
            "KALSHI-ACCESS-TIMESTAMP": str(timestamp_ms),
            "Content-Type": "application/json",
            "Accept": "application/json",
        }

    async def _request(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """Override base _request to inject RSA-signed headers."""
        signed = self._signed_headers("GET", url)
        if headers:
            signed.update(headers)
        return await super()._request(url, headers=signed, params=params)

    async def fetch_events_page(
        self, cursor: str | None = None
    ) -> tuple[list[NormalizedEvent], str | None]:
        """Fetch one page of events from Kalshi with cursor pagination."""
        url = f"{self.base_url}/events"
        params: dict = {
            "limit": 100,
            "status": "open",
            "with_nested_markets": "true",
        }
        if cursor:
            params["cursor"] = cursor

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror("Failed to fetch Kalshi events page", cursor=cursor)
            return [], None

        if not isinstance(data, dict):
            return [], None

        raw_events = data.get("events", [])
        next_cursor = data.get("cursor", None)
        # Kalshi returns empty cursor or same cursor when done
        if not next_cursor or not raw_events:
            next_cursor = None

        events: list[NormalizedEvent] = []

        for raw in raw_events:
            title = raw.get("title", "")
            description = raw.get("sub_title", raw.get("description", title))
            category = raw.get("category", "").lower() or "geopolitical"
            event_ticker = str(raw.get("event_ticker", raw.get("id", "")))
            mutually_exclusive = raw.get("mutually_exclusive", False)

            base = {
                "source": "kalshi",
                "source_url": f"https://kalshi.com/events/{event_ticker}",
                "title": title[:500],
                "description": (description or title)[:2000],
                "category": category,
                "region": "Global",
                "status": "active",
                "resolution_date": raw.get("close_time", raw.get("expected_expiration_time")),
            }

            api_markets = raw.get("markets", [])

            if len(api_markets) <= 1:
                # Flat event
                market = api_markets[0] if api_markets else {}
                market_ticker = str(market.get("ticker", event_ticker))
                yes_price = market.get("yes_bid", market.get("last_price", 50))
                prob = float(yes_price) / 100.0 if yes_price > 1 else float(yes_price)

                events.append(NormalizedEvent(
                    **base,
                    source_id=market_ticker,
                    probability=prob,
                    is_parent=False,
                    mutually_exclusive=False,
                ))
            else:
                # Parent event with multiple markets
                markets: list[NormalizedMarket] = []
                for mkt in api_markets:
                    mkt_ticker = str(mkt.get("ticker", ""))
                    yes_price = mkt.get("yes_bid", mkt.get("last_price", 50))
                    prob = float(yes_price) / 100.0 if yes_price > 1 else float(yes_price)
                    child_title = mkt.get("subtitle", mkt.get("title", title))
                    outcome_label = child_title
                    outcome_value = extract_numeric_value(outcome_label)

                    markets.append(NormalizedMarket(
                        source_id=mkt_ticker,
                        title=child_title,
                        probability=prob,
                        volume=mkt.get("volume", None),
                        close_ts=None,
                        outcome_label=outcome_label,
                        outcome_value=outcome_value,
                    ))

                events.append(NormalizedEvent(
                    **base,
                    source_id=event_ticker,
                    probability=0.0,
                    is_parent=True,
                    mutually_exclusive=mutually_exclusive,
                    markets=markets,
                ))

        return events, next_cursor

    async def fetch_prices(self, source_id: str) -> list[PricePoint]:
        """Fetch price history for a Kalshi market."""
        market_ticker = source_id
        series_ticker = source_id

        # Resolve source_id → series_ticker + market_ticker
        try:
            market_data = await self._request(f"{self.base_url}/markets/{source_id}")
            market_info = market_data.get("market", {}) if isinstance(market_data, dict) else {}
            series_ticker = market_info.get("series_ticker", source_id)
            market_ticker = market_info.get("ticker", source_id)
        except Exception:
            try:
                event_data = await self._request(f"{self.base_url}/events/{source_id}")
                event_info = (
                    event_data.get("event", {}) if isinstance(event_data, dict) else {}
                )
                series_ticker = event_info.get("series_ticker", source_id)
                markets = (
                    event_data.get("markets", []) if isinstance(event_data, dict) else []
                )
                if markets:
                    market_ticker = markets[0].get("ticker", source_id)
            except Exception:
                await logger.awarning(
                    "Failed to resolve Kalshi source_id", source_id=source_id
                )

        end_ts = int(time.time())
        start_ts = end_ts - (30 * 24 * 3600)
        url = f"{self.base_url}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
        params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": 1440}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror(
                "Failed to fetch Kalshi prices",
                source_id=source_id,
                market_ticker=market_ticker,
            )
            return []

        candlesticks = data.get("candlesticks", data.get("history", []))
        if not isinstance(candlesticks, list):
            return []

        points: list[PricePoint] = []
        for point in candlesticks:
            volume = point.get("volume", point.get("volume_fp"))
            if not volume:
                continue

            price_data = point.get("price", {})
            if isinstance(price_data, dict):
                close_val = price_data.get("close", price_data.get("close_dollars"))
                if close_val is not None:
                    prob = float(close_val)
                    if prob > 1:
                        prob = prob / 100.0
                else:
                    prob = 0.5
            else:
                prob = float(price_data)
                if prob > 1:
                    prob = prob / 100.0

            ts = point.get("end_period_ts")
            if ts is None:
                continue

            points.append(PricePoint(
                timestamp=int(ts),
                probability=prob,
                volume=float(volume) if volume else None,
            ))

        return points
