import asyncio
import time
from abc import ABC, abstractmethod

import httpx
import structlog

logger = structlog.get_logger()


class CircuitBreakerOpen(Exception):
    pass


class BaseMarketClient(ABC):
    """Abstract base class for prediction market API clients.

    Provides circuit breaker pattern and exponential backoff retry logic.
    """

    def __init__(self):
        self.failure_count: int = 0
        self.failure_threshold: int = 5
        self.reset_timeout: float = 900.0  # 15 minutes
        self.last_failure_time: float = 0.0
        self.max_retries: int = 3
        self.base_delay: float = 2.0

    def _check_circuit_breaker(self) -> None:
        """Check if circuit breaker is open and raise if so."""
        if self.failure_count >= self.failure_threshold:
            elapsed = time.monotonic() - self.last_failure_time
            if elapsed < self.reset_timeout:
                raise CircuitBreakerOpen(
                    f"Circuit breaker open. Resets in {self.reset_timeout - elapsed:.0f}s"
                )
            # Reset after timeout
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
                async with httpx.AsyncClient(timeout=30.0) as client:
                    response = await client.get(url, headers=headers, params=params)
                    response.raise_for_status()
                    self._record_success()
                    return response.json()
            except (httpx.HTTPStatusError, httpx.RequestError, httpx.TimeoutException) as exc:
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

    @abstractmethod
    async def fetch_events(self) -> list[dict]:
        """Fetch available events/markets from the platform."""
        ...

    @abstractmethod
    async def fetch_prices(self, source_id: str) -> list[dict]:
        """Fetch price/probability history for a specific event."""
        ...
