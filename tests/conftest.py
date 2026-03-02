from unittest.mock import MagicMock

import pytest
from httpx import ASGITransport, AsyncClient

from app.db.pool import get_pool
from app.db.pool import pool as db_pool
from app.main import app


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
def mock_celery_task(monkeypatch):
    mock_task = MagicMock()
    monkeypatch.setattr("app.services.user.send_verification_email", mock_task)
    return mock_task


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
