"""Redis cache layer for event data.

Key patterns and TTLs:
  events:{source}:all        -> 2h   Full NormalizedEvent list per source
  events:{source}:{source_id} -> 15min Single event detail
  history:{source}:{source_id} -> 5min  Price history
  explore:{query_hash}       -> 2min  Paginated explore results
  pm:tokenmap:{condition_id} -> 24h   PM condition→token mapping
"""

import hashlib
import json
from dataclasses import asdict

from redis.asyncio import Redis

from app.ingestion.base import NormalizedEvent, NormalizedMarket, PricePoint

# TTLs in seconds
TTL_ALL_EVENTS = 7200  # 2h
TTL_SINGLE_EVENT = 900  # 15min
TTL_HISTORY = 300  # 5min
TTL_EXPLORE = 120  # 2min
TTL_TOKEN_MAP = 86400  # 24h


def _serialize_event(event: NormalizedEvent) -> str:
    return json.dumps(asdict(event))


def _deserialize_event(raw: str) -> NormalizedEvent:
    d = json.loads(raw)
    markets = [NormalizedMarket(**m) for m in d.pop("markets", [])]
    return NormalizedEvent(**d, markets=markets)


def _serialize_points(points: list[PricePoint]) -> str:
    return json.dumps([asdict(p) for p in points])


def _deserialize_points(raw: str) -> list[PricePoint]:
    return [PricePoint(**p) for p in json.loads(raw)]


class EventCache:
    """Typed wrapper around Redis for event caching."""

    def __init__(self, redis: Redis):
        self.r = redis

    # --- All events for a source ---

    async def get_all_events(self, source: str) -> list[NormalizedEvent] | None:
        raw = await self.r.get(f"events:{source}:all")
        if raw is None:
            return None
        items = json.loads(raw)
        return [_deserialize_event(json.dumps(item)) for item in items]

    async def set_all_events(self, source: str, events: list[NormalizedEvent]) -> None:
        data = [json.loads(_serialize_event(e)) for e in events]
        await self.r.set(f"events:{source}:all", json.dumps(data), ex=TTL_ALL_EVENTS)

    # --- Single event ---

    async def get_event(self, source: str, source_id: str) -> NormalizedEvent | None:
        raw = await self.r.get(f"events:{source}:{source_id}")
        if raw is None:
            return None
        return _deserialize_event(raw)

    async def set_event(self, source: str, source_id: str, event: NormalizedEvent) -> None:
        await self.r.set(
            f"events:{source}:{source_id}", _serialize_event(event), ex=TTL_SINGLE_EVENT
        )

    # --- Price history ---

    async def get_history(self, source: str, source_id: str) -> list[PricePoint] | None:
        raw = await self.r.get(f"history:{source}:{source_id}")
        if raw is None:
            return None
        return _deserialize_points(raw)

    async def set_history(
        self, source: str, source_id: str, points: list[PricePoint]
    ) -> None:
        await self.r.set(
            f"history:{source}:{source_id}", _serialize_points(points), ex=TTL_HISTORY
        )

    # --- Explore results (paginated) ---

    @staticmethod
    def _explore_key(
        search: str | None,
        category: str | None,
        region: str | None,
        status: str | None,
        sort: str | None,
        page: int,
        page_size: int,
    ) -> str:
        raw = f"{search}:{category}:{region}:{status}:{sort}:{page}:{page_size}"
        h = hashlib.md5(raw.encode()).hexdigest()[:12]
        return f"explore:{h}"

    async def get_explore(
        self, search: str | None, category: str | None, region: str | None,
        status: str | None, sort: str | None, page: int, page_size: int,
    ) -> str | None:
        key = self._explore_key(search, category, region, status, sort, page, page_size)
        return await self.r.get(key)

    async def set_explore(
        self, search: str | None, category: str | None, region: str | None,
        status: str | None, sort: str | None, page: int, page_size: int,
        data: str,
    ) -> None:
        key = self._explore_key(search, category, region, status, sort, page, page_size)
        await self.r.set(key, data, ex=TTL_EXPLORE)

    # --- Polymarket token map ---

    async def get_token_id(self, condition_id: str) -> str | None:
        return await self.r.get(f"pm:tokenmap:{condition_id}")

    async def set_token_id(self, condition_id: str, token_id: str) -> None:
        await self.r.set(f"pm:tokenmap:{condition_id}", token_id, ex=TTL_TOKEN_MAP)
