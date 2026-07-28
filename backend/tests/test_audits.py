def test_audit_crud(client, seed_url):
    url_id = seed_url["id"]
    site_id = seed_url["site_id"]

    create = client.post(
        f"/api/v1/urls/{url_id}/audits",
        json={"status": "completed", "score": 85, "summary": "Good SEO"},
    )
    assert create.status_code == 201
    audit = create.json()
    assert audit["url_id"] == url_id
    assert audit["site_id"] == site_id
    assert audit["score"] == 85

    get = client.get(f"/api/v1/audits/{audit['id']}")
    assert get.status_code == 200

    list_by_url = client.get(f"/api/v1/urls/{url_id}/audits")
    assert list_by_url.status_code == 200
    assert list_by_url.json()["total"] == 1

    list_by_site = client.get(f"/api/v1/sites/{site_id}/audits")
    assert list_by_site.status_code == 200
    assert list_by_site.json()["total"] == 1

    update = client.patch(
        f"/api/v1/audits/{audit['id']}",
        json={"score": 90},
    )
    assert update.status_code == 200
    assert update.json()["score"] == 90

    delete = client.delete(f"/api/v1/audits/{audit['id']}")
    assert delete.status_code == 204


def test_audit_invalid_url(client):
    response = client.post(
        "/api/v1/urls/00000000-0000-0000-0000-000000000001/audits",
        json={"status": "pending"},
    )
    assert response.status_code == 404
