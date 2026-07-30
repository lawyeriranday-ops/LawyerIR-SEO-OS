from app.services.audit_service import decode_audit_summary


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


def test_run_audit_endpoint_with_html(client, seed_url):
    url_id = seed_url["id"]
    sample_html = """<!DOCTYPE html>
<html lang="fa">
<head>
    <title>عنوان تست مشاوره حقوقی وکلای دادگستری</title>
    <meta name="description" content="توضیحات متای تست برای آنالیز سئوی آنلاین وکیل پایه یک دادگستری و مشاوره حقوقی تخصصی.">
</head>
<body>
    <h1>عنوان اصلی صفحه وکالت</h1>
    <h2>بخش خدمات</h2>
    <p>""" + " متن نمونه سئوی محتوا." * 40 + """</p>
</body>
</html>"""

    response = client.post(
        f"/api/v1/urls/{url_id}/audits/run",
        json={"html_content": sample_html},
    )
    assert response.status_code == 201
    audit = response.json()
    assert audit["url_id"] == url_id
    assert audit["status"] == "completed"
    assert audit["score"] is not None
    assert audit["score"] > 70

    # Verify summary JSON decoding helper
    decoded_summary = decode_audit_summary(audit["summary"])
    assert decoded_summary["engine_version"] == "1.0.0"
    assert decoded_summary["ruleset_version"] == "1.0.0"
    assert "metrics" in decoded_summary
    assert "score_breakdown" in decoded_summary
    assert decoded_summary.get("keyword_analysis") is None
    assert decoded_summary.get("link_intelligence") is not None

    # Verify Url model updated fields
    url_res = client.get(f"/api/v1/urls/{url_id}")
    assert url_res.status_code == 200
    url_data = url_res.json()
    assert url_data["title"] == "عنوان تست مشاوره حقوقی وکلای دادگستری"
    assert url_data["meta_description"] == "توضیحات متای تست برای آنالیز سئوی آنلاین وکیل پایه یک دادگستری و مشاوره حقوقی تخصصی."
    assert url_data["last_crawled_at"] is not None


def test_run_audit_endpoint_with_target_keyword(client, seed_url):
    url_id = seed_url["id"]
    sample_html = """<!DOCTYPE html>
<html lang="fa">
<head>
    <title>وکیل ملکی در تهران - مشاوره تخصصی</title>
    <meta name="description" content="بهترین وکیل ملکی در تهران جهت پیگیری دعاوی ثبتی و خلع ید.">
</head>
<body>
    <h1>وکیل ملکی متخصص در تهران</h1>
    <h2>خدمات وکیل ملکی</h2>
    <p>اگر به دنبال وکیل ملکی هستید با دفتر ما تماس بگیرید.</p>
</body>
</html>"""

    response = client.post(
        f"/api/v1/urls/{url_id}/audits/run",
        json={"html_content": sample_html, "target_keyword": "وکیل ملکی"},
    )
    assert response.status_code == 201
    audit = response.json()
    assert audit["status"] == "completed"

    decoded_summary = decode_audit_summary(audit["summary"])
    assert decoded_summary.get("keyword_analysis") is not None
    kw_analysis = decoded_summary["keyword_analysis"]
    assert kw_analysis["target_keyword"] == "وکیل ملکی"
    assert kw_analysis["metrics"]["in_title"] is True
    assert kw_analysis["metrics"]["in_h1"] is True
    assert kw_analysis["metrics"]["keyword_count"] >= 3
    assert decoded_summary.get("link_intelligence") is not None


def test_run_audit_endpoint_includes_link_intelligence(client, seed_url):
    url_id = seed_url["id"]
    sample_html = """<!DOCTYPE html>
<html lang="fa">
<head>
    <title>عنوان تست لینک‌ها</title>
</head>
<body>
    <a href="/internal-page">لینک داخلی</a>
    <a href="https://external.org" rel="nofollow">لینک خارجی</a>
</body>
</html>"""

    response = client.post(
        f"/api/v1/urls/{url_id}/audits/run",
        json={"html_content": sample_html},
    )
    assert response.status_code == 201
    audit = response.json()

    decoded_summary = decode_audit_summary(audit["summary"])
    assert "link_intelligence" in decoded_summary
    link_info = decoded_summary["link_intelligence"]
    assert "score" in link_info
    assert "metrics" in link_info
    assert link_info["metrics"]["total_links"] == 2

