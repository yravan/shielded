import base64
import time
from pathlib import Path
from urllib.parse import urlparse

import structlog
from cryptography.hazmat.primitives import hashes, serialization
from cryptography.hazmat.primitives.asymmetric import padding

from app.config import settings
from app.ingestion.base import BaseMarketClient, NormalizedEvent, NormalizedMarket, PricePoint, is_event_relevant

logger = structlog.get_logger()


def _load_private_key():
    """Load the RSA private key from KALSHI_API_KEY (PEM content or file path)."""
    value = settings.KALSHI_API_KEY
    if value.startswith("-----"):
        # PEM content passed directly via env var
        pem_data = value.encode()
    else:
        # File path
        key_path = Path(value)
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


def _parse_fpd(value: str | None) -> float:
    """Parse a FixedPointDollars string like '0.5600' to float 0.56."""
    if value is None:
        return 0.0
    try:
        return float(value)
    except (ValueError, TypeError):
        return 0.0


def _strike_to_value(mkt: dict) -> float | None:
    """Extract numeric outcome value from Kalshi strike fields."""
    floor = mkt.get("floor_strike")
    cap = mkt.get("cap_strike")
    if floor is not None and cap is not None:
        return (float(floor) + float(cap)) / 2.0
    if floor is not None:
        return float(floor)
    if cap is not None:
        return float(cap)
    return None


def _short_strike_label(mkt: dict) -> str:
    """Build a short label from strike fields when yes_sub_title is empty.

    Examples: '51-52', '≥57', '<49', '53'
    """
    floor = mkt.get("floor_strike")
    cap = mkt.get("cap_strike")
    strike_type = mkt.get("strike_type", "")

    def _fmt(v) -> str:
        f = float(v)
        return str(int(f)) if f == int(f) else str(f)

    if strike_type == "between" and floor is not None and cap is not None:
        return f"{_fmt(floor)}-{_fmt(cap)}"
    if strike_type in ("greater", "greater_or_equal") and floor is not None:
        return f"≥{_fmt(float(floor) + 1)}" if strike_type == "greater" else f"≥{_fmt(floor)}"
    if strike_type in ("less", "less_or_equal") and cap is not None:
        return f"<{_fmt(cap)}" if strike_type == "less" else f"≤{_fmt(cap)}"
    if floor is not None:
        return _fmt(floor)
    if cap is not None:
        return _fmt(cap)
    return ""


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
        if not next_cursor or not raw_events:
            next_cursor = None

        events: list[NormalizedEvent] = []

        for raw in raw_events:
            title = raw.get("title", "")
            description = raw.get("sub_title", raw.get("description", title))

            # Skip events not relevant to geopolitical risk
            if not is_event_relevant(title, description):
                continue

            category = raw.get("category", "").lower() or "geopolitical"
            event_ticker = str(raw.get("event_ticker", raw.get("id", "")))
            series_ticker = raw.get("series_ticker", "")
            mutually_exclusive = raw.get("mutually_exclusive", False)

            base = {
                "source": "kalshi",
                "source_url": f"https://kalshi.com/events/{event_ticker}",
                "title": title[:500],
                "description": (description or title)[:2000],
                "category": category,
                "region": "Global",
                "status": "active",
                "series_ticker": series_ticker,
            }

            api_markets = raw.get("markets", [])

            if len(api_markets) <= 1:
                # Flat event — single market
                market = api_markets[0] if api_markets else {}
                market_ticker = str(market.get("ticker", event_ticker))
                prob = _parse_fpd(market.get("last_price_dollars"))
                volume = _parse_fpd(market.get("volume_fp")) or None
                close_time = market.get("close_time")

                events.append(NormalizedEvent(
                    **base,
                    source_id=market_ticker,
                    probability=prob,
                    is_parent=False,
                    mutually_exclusive=False,
                    resolution_date=close_time,
                    volume=volume,
                ))
            else:
                # Parent event with multiple markets
                markets: list[NormalizedMarket] = []
                for mkt in api_markets:
                    mkt_ticker = str(mkt.get("ticker", ""))
                    prob = _parse_fpd(mkt.get("last_price_dollars"))
                    outcome_label = mkt.get("yes_sub_title", "")

                    # Use API strike_type field instead of regex parsing
                    strike_type = mkt.get("strike_type", "")
                    is_numeric_strike = strike_type in (
                        "greater", "greater_or_equal", "less", "less_or_equal",
                        "between", "functional", "structured",
                    )
                    outcome_value = _strike_to_value(mkt) if is_numeric_strike else None
                    volume = _parse_fpd(mkt.get("volume_fp")) or None
                    close_time = mkt.get("close_time")

                    # Determine if market is closed
                    mkt_status = mkt.get("status", "")
                    mkt_closed = mkt_status in ("closed", "settled")
                    if not mkt_closed and close_time:
                        try:
                            from datetime import datetime, timezone
                            ct = datetime.fromisoformat(close_time.replace("Z", "+00:00"))
                            mkt_closed = ct < datetime.now(timezone.utc)
                        except (ValueError, TypeError):
                            pass

                    # Prefer yes_sub_title, then generated strike label, then full title
                    short_label = outcome_label or _short_strike_label(mkt) or mkt.get("title", title)

                    markets.append(NormalizedMarket(
                        source_id=mkt_ticker,
                        title=short_label,
                        probability=prob,
                        volume=volume,
                        close_ts=None,
                        outcome_label=outcome_label,
                        outcome_value=outcome_value,
                        series_ticker=series_ticker,
                        is_closed=mkt_closed,
                    ))

                # Use first market's close_time as event resolution date
                resolution_date = api_markets[0].get("close_time") if api_markets else None

                events.append(NormalizedEvent(
                    **base,
                    source_id=event_ticker,
                    probability=0.0,
                    is_parent=True,
                    mutually_exclusive=mutually_exclusive,
                    markets=markets,
                    resolution_date=resolution_date,
                ))

        return events, next_cursor

    async def fetch_prices(self, source_id: str, hours: int = 720, series_ticker: str | None = None) -> list[PricePoint]:
        """Fetch price history for a Kalshi market.

        Requires series_ticker to build the candlesticks URL.
        If series_ticker is provided (from DB), skips the expensive API resolution.
        Otherwise tries: GET /events/{event_ticker} to resolve series_ticker,
        then falls back to using source_id as both.
        """
        market_ticker = source_id

        if series_ticker:
            # series_ticker provided from DB — skip resolution entirely
            pass
        else:
            series_ticker = source_id
            # Try to resolve series_ticker from the event (NOT market detail —
            # series_ticker is not available on market detail responses)
            try:
                event_data = await self._request(f"{self.base_url}/events/{source_id}")
                event_info = (
                    event_data.get("event", {}) if isinstance(event_data, dict) else {}
                )
                series_ticker = event_info.get("series_ticker", source_id)
                api_markets = (
                    event_data.get("markets", []) if isinstance(event_data, dict) else []
                )
                if api_markets:
                    market_ticker = api_markets[0].get("ticker", source_id)
            except Exception:
                # For child markets, the source_id is a market ticker like
                # KXNEWPOPE-70-PPAR or KXTVSEASON...-30-JAN.
                # Progressively strip trailing segments to find the event ticker.
                resolved = False
                remaining = source_id
                while "-" in remaining and not resolved:
                    remaining = remaining.rsplit("-", 1)[0]
                    try:
                        event_data = await self._request(
                            f"{self.base_url}/events/{remaining}"
                        )
                        event_info = (
                            event_data.get("event", {})
                            if isinstance(event_data, dict)
                            else {}
                        )
                        series_ticker = event_info.get("series_ticker", remaining)
                        market_ticker = source_id
                        resolved = True
                    except Exception:
                        continue
                if not resolved:
                    await logger.awarning(
                        "Failed to resolve Kalshi series_ticker", source_id=source_id
                    )

        end_ts = int(time.time())
        start_ts = end_ts - (hours * 3600)
        # Use daily candles for ranges > 30 days, hourly otherwise
        period_interval = 1440 if hours > 720 else settings.KALSHI_PERIOD_INTERVAL
        url = f"{self.base_url}/series/{series_ticker}/markets/{market_ticker}/candlesticks"
        params = {"start_ts": start_ts, "end_ts": end_ts, "period_interval": period_interval}

        try:
            data = await self._request(url, params=params)
        except Exception:
            await logger.aerror(
                "Failed to fetch Kalshi prices",
                source_id=source_id,
                market_ticker=market_ticker,
            )
            return []

        candlesticks = data.get("candlesticks", []) if isinstance(data, dict) else []
        if not isinstance(candlesticks, list):
            return []

        points: list[PricePoint] = []
        last_prob = 0.0
        for point in candlesticks:
            ts = point.get("end_period_ts")
            if ts is None:
                continue

            # Use bid/ask midpoint as the price signal — it reflects the
            # live order book even in hours with zero trades, matching
            # Kalshi's own chart.  Fall back to trade close, then forward-fill.
            bid_data = point.get("yes_bid", {})
            ask_data = point.get("yes_ask", {})
            bid_close = _parse_fpd(bid_data.get("close_dollars")) if isinstance(bid_data, dict) else 0.0
            ask_close = _parse_fpd(ask_data.get("close_dollars")) if isinstance(ask_data, dict) else 0.0

            if bid_close and ask_close:
                prob = (bid_close + ask_close) / 2.0
                last_prob = prob
            else:
                price_data = point.get("price", {})
                close_val = price_data.get("close_dollars") if isinstance(price_data, dict) else None
                if close_val is not None:
                    prob = _parse_fpd(close_val)
                    last_prob = prob
                else:
                    prob = last_prob  # forward-fill

            vol_str = point.get("volume_fp")
            vol = _parse_fpd(vol_str) if vol_str else None

            points.append(PricePoint(
                timestamp=int(ts),
                probability=prob,
                volume=vol,
            ))

        return points
