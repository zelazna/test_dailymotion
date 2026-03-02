import httpx
from celery import Celery, Task

from app.core.config import settings
from app.core.logging import configure_logging, logger

configure_logging()

celery_app = Celery("user_registration", broker=settings.rabbitmq_url)

celery_app.conf.update(task_acks_late=True)


class BaseTask(Task):
    """Base task that lazily creates a shared httpx.Client per worker process."""

    ignore_result = True

    _http_client: httpx.Client | None = None

    @property
    def http_client(self) -> httpx.Client:
        if self._http_client is None:
            self._http_client = httpx.Client()
        return self._http_client


@celery_app.task(
    base=BaseTask,
    name="app.worker.send_verification_email",
    bind=True,
    max_retries=settings.smtp_max_retries,
)
def send_verification_email(self: BaseTask, code: str, email: str) -> None:
    try:
        response = self.http_client.post(
            f"{settings.smtp_api_host}/emails",
            headers={
                "Authorization": f"Bearer {settings.smtp_api_key}",
                "User-Agent": "test-app-dailymotion/1.0",
            },
            json={
                "from": settings.email_from,
                "to": [email],
                "subject": "Your verification code",
                "html": (
                    f"<p>Your verification code is: <strong>{code}</strong></p>"
                    f"<p>It expires in {settings.verification_code_ttl_seconds} seconds.</p>"
                ),
            },
        )
        response.raise_for_status()
    except httpx.HTTPStatusError as exc:
        if exc.response.status_code >= 500:
            raise self.retry(
                exc=exc,
                countdown=min(2**self.request.retries, settings.smtp_retry_max_wait),
            )
        logger.error(f"Failed to send verification email to {email}: {exc!r}")
    except httpx.RequestError as exc:
        raise self.retry(
            exc=exc,
            countdown=min(2**self.request.retries, settings.smtp_retry_max_wait),
        )
