import pytest
from fastapi import BackgroundTasks

from app.services.user import UserService


@pytest.fixture
async def service(db_connection, resend_client):
    yield UserService(
        conn=db_connection,
        email_service=resend_client,
        background_tasks=BackgroundTasks(),
    )


async def test_create_user_returns_user(service, monkeypatch):
    monkeypatch.setattr("app.services.user.secrets.randbelow", lambda _: 42)
    user = await service.create_user("user@example.com", "supersecret")
    assert user.email == "user@example.com"
    assert user.id is not None
    assert user.created_at is not None


async def test_create_user_hashes_password(service, db_connection):
    user = await service.create_user("user@example.com", "supersecret")

    row = await db_connection.fetchrow(
        "SELECT password_hash FROM users WHERE id = $1", user.id
    )
    assert row["password_hash"] != "supersecret"
    assert row["password_hash"].startswith("$argon2")


async def test_create_user_stores_verification_code(
    service, monkeypatch, db_connection
):
    monkeypatch.setattr("app.services.user.secrets.randbelow", lambda _: 42)
    user = await service.create_user("user@example.com", "supersecret")
    row = await db_connection.fetchrow(
        "SELECT code FROM verification_codes WHERE user_id = $1", user.id
    )
    assert row["code"] == "0042"
