import functools
import json
from typing import Any, Callable

import redis.asyncio as aioredis

from app.config import settings

pool = aioredis.ConnectionPool.from_url(settings.REDIS_URL, decode_responses=True)


async def get_redis() -> aioredis.Redis:
    return aioredis.Redis(connection_pool=pool)


def cache(prefix: str, ttl: int = 60):
    """Decorator that caches function results in Redis as JSON.

    The decorated function must accept a `redis_conn` keyword argument
    (an aioredis.Redis instance). Cache keys are built from `prefix`
    plus positional/keyword arguments.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        async def wrapper(*args: Any, redis_conn: aioredis.Redis | None = None, **kwargs: Any):
            if redis_conn is None:
                return await func(*args, **kwargs)

            key_parts = [prefix]
            key_parts.extend(str(a) for a in args)
            key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()) if k != "redis_conn")
            cache_key = ":".join(key_parts)

            cached = await redis_conn.get(cache_key)
            if cached is not None:
                return json.loads(cached)

            result = await func(*args, **kwargs)
            await redis_conn.set(cache_key, json.dumps(result, default=str), ex=ttl)
            return result

        return wrapper

    return decorator
