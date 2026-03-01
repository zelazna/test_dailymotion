

async def test_status(client):
    response = await client.get("/status")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}
