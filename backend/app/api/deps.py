from typing import Annotated

import redis.asyncio as aioredis
from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.database import get_db
from app.redis import get_redis

DbSession = Annotated[AsyncSession, Depends(get_db)]
RedisConn = Annotated[aioredis.Redis, Depends(get_redis)]
