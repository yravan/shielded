import asyncio
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

import httpx
import structlog

logger = structlog.get_logger()


@dataclass
class NormalizedMarket:
    source_id: str  # market ticker / condition_id
    title: str
    probability: float  # 0-1
    volume: float | None = None
    close_ts: int | None = None
    outcome_label: str = ""  # "Above 10", "Claude", etc.
    outcome_value: float | None = None  # parsed numeric if quantitative, else None


@dataclass
class NormalizedEvent:
    source: str  # "kalshi" | "polymarket" | "metaculus"
    source_id: str
    source_url: str
    title: str
    description: str
    category: str
    region: str
    status: str
    resolution_date: str | None = None
    image_url: str | None = None
    is_parent: bool = False
    mutually_exclusive: bool = False
    probability: float = 0.0  # for flat events; 0 for parents
    markets: list[NormalizedMarket] = field(default_factory=list)
    expected_value: float | None = None  # computed for quantitative multi-markets
    is_quantitative: bool = False


@dataclass
class PricePoint:
    timestamp: int  # unix seconds
    probability: float
    volume: float | None = None


class CircuitBreakerOpen(Exception):
    pass


class BaseMarketClient(ABC):
    """Abstract base class for prediction market API clients.

    Provides circuit breaker pattern, exponential backoff retry logic,
    and cursor/offset pagination helpers.
    """

    def __init__(self):
        self.failure_count: int = 0
        self.failure_threshold: int = 5
        self.reset_timeout: float = 900.0  # 15 minutes
        self.last_failure_time: float = 0.0
        self.max_retries: int = 3
        self.base_delay: float = 2.0
        self._http: httpx.AsyncClient = httpx.AsyncClient(timeout=30.0)

    async def close(self) -> None:
        """Close the underlying HTTP client."""
        await self._http.aclose()

    @property
    @abstractmethod
    def source_name(self) -> str:
        """Short lowercase name: 'kalshi', 'polymarket', 'metaculus'."""
        ...

    def _check_circuit_breaker(self) -> None:
        if self.failure_count >= self.failure_threshold:
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed < self.reset_timeout:
                raise CircuitBreakerOpen(
                    f"Circuit breaker open. Resets in {self.reset_timeout - elapsed:.0f}s"
                )
            self.failure_count = 0

    def _record_failure(self) -> None:
        self.failure_count += 1
        self.last_failure_time = time.monotonic()

    def _record_success(self) -> None:
        self.failure_count = 0

    async def _request(
        self,
        url: str,
        headers: dict | None = None,
        params: dict | None = None,
    ) -> dict | list:
        """Make an HTTP GET request with exponential backoff and circuit breaker."""
        self._check_circuit_breaker()

        last_exception = None
        for attempt in range(self.max_retries):
            try:
                response = await self._http.get(url, headers=headers, params=params)
                response.raise_for_status()
                self._record_success()
                return response.json()
            except httpx.HTTPStatusError as exc:
                if 400 <= exc.response.status_code < 500:
                    await logger.awarning(
                        "Client error, not retrying",
                        url=url,
                        status=exc.response.status_code,
                    )
                    self._record_failure()
                    raise
                last_exception = exc
                self._record_failure()
            except (httpx.RequestError, httpx.TimeoutException) as exc:
                last_exception = exc
                self._record_failure()
                delay = self.base_delay * (2**attempt)
                await logger.awarning(
                    "Request failed, retrying",
                    url=url,
                    attempt=attempt + 1,
                    delay=delay,
                    error=str(exc),
                )
                if attempt < self.max_retries - 1:
                    await asyncio.sleep(delay)

        await logger.aerror(
            "All retries exhausted",
            url=url,
            error=str(last_exception),
        )
        raise last_exception  # type: ignore[misc]

    async def fetch_all_events(self) -> list[NormalizedEvent]:
        """Paginate through all events using the client's page fetcher."""
        all_events: list[NormalizedEvent] = []
        cursor: str | None = None

        while True:
            events, next_cursor = await self.fetch_events_page(cursor)
            all_events.extend(events)
            if not next_cursor:
                break
            cursor = next_cursor

        await logger.ainfo(
            "Fetched all events",
            source=self.source_name,
            count=len(all_events),
        )
        return all_events

    @abstractmethod
    async def fetch_events_page(
        self, cursor: str | None = None
    ) -> tuple[list[NormalizedEvent], str | None]:
        """Fetch one page of events. Returns (events, next_cursor).

        next_cursor is None when there are no more pages.
        """
        ...

    @abstractmethod
    async def fetch_prices(self, source_id: str) -> list[PricePoint]:
        """Fetch price/probability history for a specific event."""
        ...
