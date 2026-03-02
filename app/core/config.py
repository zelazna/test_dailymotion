from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: PostgresDsn
    API_V1_STR: str = "/api/v1"

    smtp_api_key: str
    smtp_api_host: str = "https://api.resend.com"
    email_from: str
    verification_code_ttl_seconds: int = 60

    smtp_max_retries: int = 3
    smtp_retry_max_wait: float = 30.0

    log_level: str = "INFO"


settings = Settings()  # pyright: ignore[reportCallIssue]
