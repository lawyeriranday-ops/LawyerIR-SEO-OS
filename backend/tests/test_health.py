def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ("healthy", "degraded")
    assert "database" in data


def test_api_status(client):
    response = client.get("/api/v1/status")
    assert response.status_code == 200
    assert response.json()["ready"] is True
