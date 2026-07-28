def test_site_crud(client, seed_user):
    user_id = seed_user["id"]

    create = client.post(
        "/api/v1/sites",
        json={
            "url": "https://example.com",
            "name": "Example",
            "owner_id": user_id,
        },
    )
    assert create.status_code == 201
    site = create.json()
    assert site["name"] == "Example"
    assert site["owner_id"] == user_id

    get = client.get(f"/api/v1/sites/{site['id']}")
    assert get.status_code == 200

    update = client.patch(
        f"/api/v1/sites/{site['id']}",
        json={"name": "Example Updated"},
    )
    assert update.status_code == 200
    assert update.json()["name"] == "Example Updated"

    duplicate = client.post(
        "/api/v1/sites",
        json={"url": "https://example.com", "name": "Dup"},
    )
    assert duplicate.status_code == 409

    delete = client.delete(f"/api/v1/sites/{site['id']}")
    assert delete.status_code == 204

    missing = client.get(f"/api/v1/sites/{site['id']}")
    assert missing.status_code == 404


def test_list_sites(client, seed_site):
    response = client.get("/api/v1/sites")
    assert response.status_code == 200
    data = response.json()
    assert data["total"] >= 1
    assert len(data["items"]) >= 1
