import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from asyncpg.connection import Connection
from fastapi.background import BackgroundTasks
from httpx import HTTPError, RequestError

from app.core.config import settings
from app.core.logging import logger
from app.core.security import get_password_hash, verify_password
from app.db.user import User, activate_user, create_user, get_user_by_email
from app.db.verification_code import create_verification_code
from app.services.resend_client import ResendClient


class CodeExpiredError(Exception):
    message = "Verification code expired"


class CodeInvalidError(Exception):
    message = "Verification code invalid"


class CodeNotFoundError(Exception):
    message = "Verification code not found"


async def _send_account_verification_code(
    code: str, email: str, client: ResendClient
) -> None:
    try:
        await client.send_email(
            to=email,
            subject="Your verification code",
            html=f"<p>Your verification code is: <strong>{code}</strong></p>"
            f"<p>It expires in {settings.verification_code_ttl_seconds} seconds.</p>",
        )
    except (RequestError, HTTPError) as exc:
        logger.error("Failed to send verification email to {}: {}", email, exc)


@dataclass
class UserService:
    conn: Connection
    email_service: ResendClient
    background_tasks: BackgroundTasks

    async def create_user(
        self,
        email: str,
        password: str,
    ):
        password_hash = get_password_hash(password)
        async with self.conn.transaction():
            user = await create_user(self.conn, email, password_hash)
            code = str(secrets.randbelow(10000)).zfill(4)
            expires_at = datetime.now(timezone.utc) + timedelta(
                seconds=settings.verification_code_ttl_seconds
            )
            await create_verification_code(self.conn, user.id, code, expires_at)
        # This should be replaced with msg queue + workers in prod
        self.background_tasks.add_task(
            _send_account_verification_code, code, user.email, self.email_service
        )
        return user

    async def get_authenticated_user(
        self,
        email: str,
        password: str,
    ) -> User | None:
        user = await get_user_by_email(self.conn, email)
        if user is None:
            return None
        is_valid, _ = verify_password(password, user.password_hash)  # pyright: ignore[reportArgumentType]
        if not is_valid:
            return None
        return user

    async def activate_user(self, user: User, code: str) -> bool:
        # Should be idempotent
        if user.is_active is True:
            return True

        if not user.verification_code:
            raise CodeNotFoundError()

        # Code expired
        if user.verification_code.expires_at < datetime.now(timezone.utc):
            raise CodeExpiredError()
        # Code mismatch
        if user.verification_code.code != code:
            raise CodeInvalidError()

        await activate_user(self.conn, user.id)

        return True
