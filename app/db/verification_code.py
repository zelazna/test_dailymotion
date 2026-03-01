from dataclasses import dataclass
from datetime import datetime
from typing import cast
from uuid import UUID

import asyncpg


@dataclass
class VerificationCode:
    id: UUID
    user_id: UUID
    code: str
    expires_at: datetime
    created_at: datetime


async def create_verification_code(
    conn: asyncpg.Connection,
    user_id: UUID,
    code: str,
    expires_at: datetime,
) -> VerificationCode:
    # Replace any existing code for this user.
    await conn.execute(
        "DELETE FROM verification_codes WHERE user_id = $1",
        user_id,
    )
    result = cast(
        asyncpg.Record,
        await conn.fetchrow(
            """
            INSERT INTO verification_codes (user_id, code, expires_at)
            VALUES ($1, $2, $3)
            RETURNING id, user_id, code, expires_at, created_at
            """,
            user_id,
            code,
            expires_at,
        ),
    )
    return VerificationCode(**dict(result))
