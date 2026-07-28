def test_url_crud(client, seed_site):
    site_id = seed_site["id"]

    create = client.post(
        f"/api/v1/sites/{site_id}/urls",
        json={
            "path": "/about",
            "full_url": "https://lawyerir.com/about",
            "title": "About",
        },
    )
    assert create.status_code == 201
    url = create.json()
    assert url["path"] == "/about"

    get = client.get(f"/api/v1/urls/{url['id']}")
    assert get.status_code == 200

    update = client.patch(
        f"/api/v1/urls/{url['id']}",
        json={"title": "About Us"},
    )
    assert update.status_code == 200
    assert update.json()["title"] == "About Us"

    duplicate_path = client.post(
        f"/api/v1/sites/{site_id}/urls",
        json={
            "path": "/about",
            "full_url": "https://lawyerir.com/about-page",
        },
    )
    assert duplicate_path.status_code == 409

    delete = client.delete(f"/api/v1/urls/{url['id']}")
    assert delete.status_code == 204


def test_list_urls(client, seed_site, seed_url):
    response = client.get(f"/api/v1/sites/{seed_site['id']}/urls")
    assert response.status_code == 200
    assert response.json()["total"] >= 1
