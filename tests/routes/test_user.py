from datetime import datetime, timedelta, timezone
from unittest.mock import Mock

import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import settings
from app.main import app

URL = f"{settings.API_V1_STR}/users"
USER_PAYLOAD = {"email": "test@example.com", "password": "supersecret"}


@pytest.fixture
async def user_factory(client, monkeypatch):
    async def create(email=None, password=None):
        if email is None:
            email = USER_PAYLOAD["email"]
        if password is None:
            password = USER_PAYLOAD["password"]
        monkeypatch.setattr("app.services.user.secrets.randbelow", lambda _: 2768)
        response = await client.post(URL, json={"email": email, "password": password})
        assert response.status_code == 201
        data = response.json()
        return data

    return create


@pytest.fixture
async def authenticated_client(user_factory):
    await user_factory()
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test",
        auth=("test@example.com", "supersecret"),
    ) as c:
        yield c


async def test_create_user(client, mock_celery_task, monkeypatch):
    monkeypatch.setattr("app.services.user.secrets.randbelow", lambda _: 2768)
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "email": "test@example.com",
        "id": data["id"],
        "created_at": data["created_at"],
    }
    mock_celery_task.delay.assert_called_once_with("2768", "test@example.com")


async def test_create_user_duplicate_email(client):
    await client.post(URL, json=USER_PAYLOAD)
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 409


async def test_activate_user(authenticated_client):
    activation_response = await authenticated_client.post(
        f"{URL}/activate", json={"code": "2768"}
    )
    assert activation_response.status_code == 200


async def test_activate_user_invalid_code(authenticated_client):
    activation_response = await authenticated_client.post(
        f"{URL}/activate", json={"code": "1234"}
    )
    assert activation_response.status_code == 400
    assert activation_response.json() == {
        "detail": "Activation failed: Verification code invalid"
    }


async def test_activate_user_expired_code(authenticated_client, monkeypatch):
    datetime_mock = Mock()
    datetime_mock.now.return_value = datetime.now(timezone.utc) + timedelta(minutes=2)
    monkeypatch.setattr("app.services.user.datetime", datetime_mock)
    activation_response = await authenticated_client.post(
        f"{URL}/activate", json={"code": "2768"}
    )
    assert activation_response.status_code == 400
    assert activation_response.json() == {
        "detail": "Activation failed: Verification code expired"
    }
