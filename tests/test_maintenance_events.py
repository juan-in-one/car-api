async def test_health_ok(client):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


async def test_create_and_get_event(client):
    payload = {
        "type": "oil_change",
        "event_date": "2026-01-15",
        "odometer_km": 45000,
        "notes": "Cambio de aceite y filtro",
    }

    create_response = await client.post("/maintenance-events", json=payload)
    assert create_response.status_code == 201
    created = create_response.json()
    assert created["type"] == payload["type"]
    assert created["odometer_km"] == payload["odometer_km"]

    get_response = await client.get(f"/maintenance-events/{created['id']}")
    assert get_response.status_code == 200
    assert get_response.json()["id"] == created["id"]


async def test_get_nonexistent_event_returns_404(client):
    fake_id = "00000000-0000-0000-0000-000000000000"
    response = await client.get(f"/maintenance-events/{fake_id}")
    assert response.status_code == 404


async def test_delete_event(client):
    payload = {
        "type": "itv",
        "event_date": "2026-02-01",
        "odometer_km": 46000,
        "notes": None,
    }
    created = (await client.post("/maintenance-events", json=payload)).json()

    delete_response = await client.delete(f"/maintenance-events/{created['id']}")
    assert delete_response.status_code == 204

    get_response = await client.get(f"/maintenance-events/{created['id']}")
    assert get_response.status_code == 404
