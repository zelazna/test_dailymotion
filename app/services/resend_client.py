from contextlib import asynccontextmanager
from dataclasses import dataclass

import httpx
from tenacity import (
    AsyncRetrying,
    retry_if_exception,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

_client: "ResendClient | None" = None


class HTTPError(Exception):
    pass


@dataclass
class ResendClient:
    _http: httpx.AsyncClient

    async def send_email(self, to: str, subject: str, html: str) -> None:
        async for attempt in AsyncRetrying(
            wait=wait_exponential(
                multiplier=1, min=1, max=settings.smtp_retry_max_wait
            ),
            stop=stop_after_attempt(settings.smtp_max_retries),
            retry=(
                retry_if_exception(
                    lambda e: (
                        isinstance(e, httpx.HTTPStatusError)
                        and e.response.status_code >= 500
                    )
                )
                | retry_if_exception_type(httpx.RequestError)
            ),
            reraise=True,
        ):
            with attempt:
                response = await self._http.post(
                    f"{settings.smtp_api_host}/emails",
                    headers={"Authorization": f"Bearer {settings.smtp_api_key}", "User-Agent": "test-app-dailymotion/1.0"},
                    json={
                        "from": settings.email_from,
                        "to": [to],
                        "subject": subject,
                        "html": html,
                    },
                )
                response.raise_for_status()


@asynccontextmanager
async def resend_client():
    global _client
    try:
        async with httpx.AsyncClient() as http:
            _client = ResendClient(_http=http)
            yield _client
    finally:
        _client = None


def get_resend_client() -> ResendClient:
    if _client is None:
        raise RuntimeError("Resend client is not initialized")
    return _client
