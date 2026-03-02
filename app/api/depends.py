from typing import Annotated, AsyncGenerator

from asyncpg import Connection
from asyncpg.pool import PoolConnectionProxy
from fastapi import Depends
from fastapi.exceptions import HTTPException
from fastapi.security import HTTPBasic, HTTPBasicCredentials

from app.db.pool import get_pool
from app.db.user import User
from app.services.user import UserService


async def get_db() -> AsyncGenerator[PoolConnectionProxy, None]:
    async with get_pool().acquire() as conn:
        yield conn


def get_user_service(
    conn: Annotated[Connection, Depends(get_db)],
) -> UserService:
    return UserService(conn)


async def get_authenticated_user(
    credentials: Annotated[HTTPBasicCredentials, Depends(HTTPBasic())],
    user_service: Annotated[UserService, Depends(get_user_service)],
) -> User:
    if user := (
        await user_service.get_authenticated_user(
            credentials.username, credentials.password
        )
    ):
        return user
    raise HTTPException(status_code=401, detail="Invalid credentials")
