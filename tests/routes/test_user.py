from app.core.config import settings

URL = f"{settings.API_V1_STR}/users"
USER_PAYLOAD = {"email": "test@example.com", "password": "supersecret"}


async def test_create_user(client, resend_client, monkeypatch):
    monkeypatch.setattr("app.services.user.secrets.randbelow", lambda _: 2768)
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 201
    data = response.json()
    assert data == {
        "email": "test@example.com",
        "id": data["id"],
        "created_at": data["created_at"],
    }
    resend_client.send_email.assert_called_once_with(
        to="test@example.com",
        subject="Your verification code",
        html="<p>Your verification code is: <strong>2768</strong></p><p>It expires in 60 seconds.</p>",
    )


async def test_create_user_duplicate_email(client):
    await client.post(URL, json=USER_PAYLOAD)
    response = await client.post(URL, json=USER_PAYLOAD)
    assert response.status_code == 409
