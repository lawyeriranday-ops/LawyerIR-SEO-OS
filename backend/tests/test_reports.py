def test_report_crud(client, seed_site, seed_url):
    site_id = seed_site["id"]

    audit = client.post(
        f"/api/v1/urls/{seed_url['id']}/audits",
        json={"status": "completed", "score": 75},
    ).json()

    create = client.post(
        f"/api/v1/sites/{site_id}/reports",
        json={
            "title": "Monthly SEO Report",
            "content": "Summary content",
            "audit_id": audit["id"],
        },
    )
    assert create.status_code == 201
    report = create.json()
    assert report["audit_id"] == audit["id"]

    get = client.get(f"/api/v1/reports/{report['id']}")
    assert get.status_code == 200

    update = client.patch(
        f"/api/v1/reports/{report['id']}",
        json={"title": "Updated Report"},
    )
    assert update.status_code == 200

    delete = client.delete(f"/api/v1/reports/{report['id']}")
    assert delete.status_code == 204


def test_report_mismatched_audit(client, seed_site):
    other_site = client.post(
        "/api/v1/sites",
        json={"url": "https://other2.com", "name": "Other2"},
    ).json()
    other_url = client.post(
        f"/api/v1/sites/{other_site['id']}/urls",
        json={"path": "/", "full_url": "https://other2.com/"},
    ).json()
    other_audit = client.post(
        f"/api/v1/urls/{other_url['id']}/audits",
        json={"status": "pending"},
    ).json()

    response = client.post(
        f"/api/v1/sites/{seed_site['id']}/reports",
        json={"title": "Bad Report", "audit_id": other_audit["id"]},
    )
    assert response.status_code == 422
