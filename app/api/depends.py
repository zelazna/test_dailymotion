from typing import Annotated, AsyncGenerator

from asyncpg import Connection
from asyncpg.pool import PoolConnectionProxy
from fastapi import BackgroundTasks, Depends

from app.db.pool import get_pool
from app.services.resend_client import ResendClient, get_resend_client
from app.services.user import UserService


async def get_db() -> AsyncGenerator[PoolConnectionProxy, None]:
    async with get_pool().acquire() as conn:
        yield conn


def get_email_service() -> ResendClient:
    return get_resend_client()


def get_user_service(
    conn: Annotated[Connection, Depends(get_db)],
    email_client: Annotated[ResendClient, Depends(get_email_service)],
    background_tasks: BackgroundTasks,
) -> UserService:
    return UserService(conn, email_client, background_tasks)
