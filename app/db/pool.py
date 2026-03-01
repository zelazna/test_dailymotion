from contextlib import asynccontextmanager

import asyncpg

from app.core.config import settings

_pool: asyncpg.Pool | None = None


@asynccontextmanager
async def pool():
    global _pool
    try:
        _pool = await asyncpg.create_pool(str(settings.database_url))
        yield _pool
    finally:
        if _pool:
            await _pool.close()
        _pool = None


def get_pool() -> asyncpg.Pool:
    if _pool is None:
        raise RuntimeError("Database pool is not initialized")
    return _pool
