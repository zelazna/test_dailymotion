from unittest.mock import AsyncMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.api.depends import get_email_service
from app.db.pool import get_pool
from app.db.pool import pool as db_pool
from app.main import app
from app.services.resend_client import ResendClient


@pytest.fixture(scope="session")
async def init_db():
    """Initialize the DB pool once for the whole test session."""
    async with db_pool():
        yield


@pytest.fixture
async def db_connection(init_db):
    async with get_pool().acquire() as conn:
        yield conn


@pytest.fixture(autouse=True)
async def resend_client():
    mock_email = ResendClient(_http=AsyncMock())
    mock_email.send_email = AsyncMock()
    app.dependency_overrides[get_email_service] = lambda: mock_email
    yield mock_email
    app.dependency_overrides.clear()


@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app), base_url="http://test"
    ) as c:
        yield c

@pytest.fixture(autouse=True)
async def clean_db(init_db):
    yield
    async with get_pool().acquire() as conn:
        await conn.execute("TRUNCATE TABLE users CASCADE")
