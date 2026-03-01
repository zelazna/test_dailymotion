from pydantic import PostgresDsn
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: PostgresDsn
    API_V1_STR: str = "/api/v1"


settings = Settings()  # pyright: ignore[reportCallIssue]
