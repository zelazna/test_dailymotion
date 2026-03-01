from typing import AsyncGenerator

from asyncpg.pool import PoolConnectionProxy

from app.core.pool import get_pool


async def get_db() -> AsyncGenerator[PoolConnectionProxy, None]:
    async with get_pool().acquire() as conn:
        yield conn
