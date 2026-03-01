from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID

import asyncpg


class UniqueViolationError(Exception): ...


@dataclass
class User:
    id: UUID
    email: str
    created_at: datetime


async def create_user(conn: asyncpg.Connection, email: str, password_hash: str) -> User:
    try:
        query = """
        INSERT INTO users (email, password_hash)
        VALUES ($1, $2)
        RETURNING id, email, created_at
        """
        result: asyncpg.Record = cast(
            asyncpg.Record,
            await conn.fetchrow(
                query,
                email,
                password_hash,
            ),
        )
        return User(**dict(result))
    except asyncpg.UniqueViolationError as e:
        raise UniqueViolationError("Email already exists") from e
