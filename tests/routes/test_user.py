from app.core.config import settings

URL = f"{settings.API_V1_STR}/users"
USER_PAYLOAD = {"email": "test@example.com", "password": "supersecret"}


async def test_create_user(client):
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert "id" in data
    assert "created_at" in data


async def test_create_user_duplicate_email(client):
    await client.post(URL, json=USER_PAYLOAD)
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 409
