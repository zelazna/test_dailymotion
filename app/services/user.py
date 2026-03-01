import secrets
from dataclasses import dataclass
from datetime import datetime, timedelta, timezone

from asyncpg.connection import Connection
from fastapi.background import BackgroundTasks
from httpx import HTTPError, RequestError
from pwdlib import PasswordHash

from app.core.config import settings
from app.core.logging import logger
from app.db.user import create_user
from app.db.verification_code import create_verification_code
from app.services.resend_client import ResendClient


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


_password_hash = PasswordHash.recommended()


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
        password_hash = _password_hash.hash(password)
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
