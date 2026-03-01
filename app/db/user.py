from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID

import asyncpg

from app.db.verification_code import VerificationCode


class UniqueViolationError(Exception): ...


@dataclass
class User:
    id: UUID
    email: str
    created_at: datetime
    password_hash: str | None = None
    is_active: bool = False
    verification_code: VerificationCode | None = None


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


_USER_COLS = """
    SELECT u.id,
           u.email,
           u.created_at,
           u.password_hash,
           u.is_active,
           c.id         AS code_id,
           c.code       AS code,
           c.user_id    AS code_user_id,
           c.expires_at AS code_expires_at,
           c.created_at AS code_created_at
    FROM users u
    LEFT JOIN verification_codes c ON c.user_id = u.id
"""


def _row_to_user(row: asyncpg.Record) -> User:
    vc: VerificationCode | None = None
    if row["code_id"] is not None:
        vc = VerificationCode(
            id=row["code_id"],
            code=row["code"],
            user_id=row["code_user_id"],
            expires_at=row["code_expires_at"],
            created_at=row["code_created_at"],
        )
    return User(
        id=row["id"],
        email=row["email"],
        created_at=row["created_at"],
        password_hash=row["password_hash"],
        is_active=row["is_active"],
        verification_code=vc,
    )


async def get_user_by_email(conn: asyncpg.Connection, email: str) -> User | None:
    row = await conn.fetchrow(_USER_COLS + "WHERE u.email = $1", email)
    if row is None:
        return None
    return _row_to_user(row)


async def get_user_by_id_with_lock(conn: asyncpg.Connection, user_id: UUID) -> User | None:
    row = await conn.fetchrow(
        _USER_COLS + "WHERE u.id = $1 FOR UPDATE OF u",
        user_id,
    )
    if row is None:
        return None
    return _row_to_user(row)


async def activate_user(conn: asyncpg.Connection, user_id: UUID):
    query = """
    UPDATE users
    SET is_active = TRUE
    WHERE id = $1
    """
    await conn.execute(query, user_id)
