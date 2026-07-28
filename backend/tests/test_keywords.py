from pytest import approx


def test_keyword_crud(client, seed_site, seed_url):
    site_id = seed_site["id"]
    url_id = seed_url["id"]

    create = client.post(
        f"/api/v1/sites/{site_id}/keywords",
        json={
            "keyword": "online lawyer",
            "target_url_id": url_id,
            "search_volume": 1200,
            "position": 8.5,
            "clicks": 45,
            "impressions": 900,
            "intent": "transactional",
            "priority": "high",
        },
    )
    assert create.status_code == 201
    keyword = create.json()
    assert keyword["keyword"] == "online lawyer"
    assert keyword["priority"] == "high"
    assert float(keyword["ctr"]) == approx(45 / 900, rel=1e-3)

    get = client.get(f"/api/v1/keywords/{keyword['id']}")
    assert get.status_code == 200

    update = client.patch(
        f"/api/v1/keywords/{keyword['id']}",
        json={"position": 5.0},
    )
    assert update.status_code == 200
    assert float(update.json()["position"]) == 5.0

    duplicate = client.post(
        f"/api/v1/sites/{site_id}/keywords",
        json={"keyword": "online lawyer"},
    )
    assert duplicate.status_code == 409

    delete = client.delete(f"/api/v1/keywords/{keyword['id']}")
    assert delete.status_code == 204


def test_keyword_cross_site_target_url(client, seed_site):
    other_site = client.post(
        "/api/v1/sites",
        json={"url": "https://other.com", "name": "Other"},
    ).json()
    other_url = client.post(
        f"/api/v1/sites/{other_site['id']}/urls",
        json={"path": "/", "full_url": "https://other.com/"},
    ).json()

    response = client.post(
        f"/api/v1/sites/{seed_site['id']}/keywords",
        json={"keyword": "test kw", "target_url_id": other_url["id"]},
    )
    assert response.status_code == 422


def test_keyword_filter(client, seed_site):
    client.post(
        f"/api/v1/sites/{seed_site['id']}/keywords",
        json={"keyword": "high kw", "priority": "high", "intent": "commercial"},
    )
    response = client.get(
        f"/api/v1/sites/{seed_site['id']}/keywords",
        params={"priority": "high", "intent": "commercial"},
    )
    assert response.status_code == 200
    assert response.json()["total"] >= 1
