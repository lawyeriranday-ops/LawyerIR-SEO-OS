import pytest
from app.services.link_engine import LinkIntelligenceEngine, LinkAuditConfig


def test_is_generic_anchor_persian_and_english():
    engine = LinkIntelligenceEngine()

    assert engine.is_generic_anchor("اینجا") is True
    assert engine.is_generic_anchor("ادامه مطلب") is True
    assert engine.is_generic_anchor("click here") is True
    assert engine.is_generic_anchor("READ MORE") is True
    assert engine.is_generic_anchor("وکیل پایه یک دادگستری") is False


def test_extract_links_classification_and_rel_attributes():
    engine = LinkIntelligenceEngine()
    html = """<!DOCTYPE html>
<html>
<body>
    <a href="/about">درباره ما</a>
    <a href="https://google.com" rel="nofollow sponsored">گوگل</a>
    <a href="https://forum.example.com" rel="ugc">فروم</a>
    <a href="/contact"></a>
    <a href="/gallery"><img src="photo.jpg" alt="گالری تصاویر"></a>
</body>
</html>"""

    links = engine.extract_links(html, base_url="https://lawyerir.com")
    assert len(links) == 5

    # Internal link
    about_link = next(l for l in links if l.href == "/about")
    assert about_link.is_internal is True
    assert about_link.is_external is False
    assert about_link.text == "درباره ما"

    # External link with nofollow + sponsored
    google_link = next(l for l in links if "google.com" in l.href)
    assert google_link.is_external is True
    assert google_link.is_nofollow is True
    assert google_link.is_sponsored is True

    # Empty anchor link
    empty_link = next(l for l in links if l.href == "/contact")
    assert empty_link.is_empty is True

    # Image link with alt text
    img_link = next(l for l in links if l.href == "/gallery")
    assert img_link.is_image_link is True
    assert img_link.image_alt == "گالری تصاویر"


def test_analyze_links_well_structured():
    engine = LinkIntelligenceEngine()
    html = """<!DOCTYPE html>
<html>
<body>
    <a href="/lawyers/tehran">وکلای دادگستری تهران</a>
    <a href="/services/property-law">مشاوره دعاوی ملکی</a>
    <a href="https://external-legal.org" rel="nofollow">مرجع قوانین حقوقی</a>
</body>
</html>"""

    result = engine.analyze_links(html, base_url="https://lawyerir.com")
    assert result["score"] >= 90
    assert result["metrics"]["internal_links_count"] == 2
    assert result["metrics"]["external_links_count"] == 1
    assert result["metrics"]["generic_anchors_count"] == 0
    assert len(result["issues"]) == 0


def test_analyze_links_issues_detection():
    engine = LinkIntelligenceEngine()
    html = """<!DOCTYPE html>
<html>
<body>
    <a href="https://external-site.com">اینجا کلیک کنید</a>
    <a href="https://another-site.com"></a>
</body>
</html>"""

    result = engine.analyze_links(html, base_url="https://lawyerir.com")
    assert result["score"] < 60
    assert result["metrics"]["internal_links_count"] == 0
    assert result["metrics"]["generic_anchors_count"] == 1
    assert result["metrics"]["empty_anchors_count"] == 1

    issue_types = [i["type"] for i in result["issues"]]
    assert "missing_internal_links" in issue_types
    assert "generic_anchor_texts" in issue_types
    assert "empty_anchor_texts" in issue_types


def test_custom_link_audit_config():
    custom_cfg = LinkAuditConfig(min_recommended_internal=5)
    engine = LinkIntelligenceEngine(config=custom_cfg)

    html = "<html><body><a href='/a'>لینک ۱</a></body></html>"
    result = engine.analyze_links(html, base_url="https://lawyerir.com")
    assert result["score"] < 100
