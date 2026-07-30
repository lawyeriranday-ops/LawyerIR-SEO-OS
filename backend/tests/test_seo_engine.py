import pytest
from dataclasses import FrozenInstanceError
from bs4 import BeautifulSoup

from app.services.seo_engine import (
    SEOAuditEngine,
    SEOAuditConfig,
    AuditContext,
    BaseSEORule,
    RuleResult,
    ENGINE_VERSION,
    RULESET_VERSION,
)

SAMPLE_GOOD_HTML = """<!DOCTYPE html>
<html lang="fa">
<head>
    <meta charset="UTF-8">
    <title>وکیل پایه یک دادگستری در تهران - مشاوره حقوقی تخصصی</title>
    <meta name="description" content="بهترین وکیل پایه یک دادگستری در تهران. ارائه خدمات مشاوره حقوقی تخصصی آنلاین و تلفنی در زمینه دعاوی ملکی، کیفری و خانوادگی.">
    <link rel="canonical" href="https://lawyerir.com/lawyers/tehran">
    <meta name="robots" content="index, follow">
</head>
<body>
    <h1>وکیل پایه یک دادگستری در تهران</h1>
    <h2>خدمات مشاوره حقوقی</h2>
    <p>""" + " دفتر وکالت ما آماده ارائه مشاوره حقوقی تخصصی به شما عزیزان می‌باشد." * 30 + """</p>
    <img src="https://lawyerir.com/logo.png" alt="لوگوی دفتر وکالت LawyerIR">
    <a href="https://lawyerir.com/about">درباره ما</a>
    <a href="https://google.com">گوگل</a>
</body>
</html>"""

SAMPLE_BAD_HTML = """<html>
<head>
    <meta name="robots" content="noindex, nofollow">
</head>
<body>
    <h1>اولین تیتر اصلی</h1>
    <h1>دومین تیتر اصلی (اشتباه)</h1>
    <p>محتوای بسیار کوتاه.</p>
    <img src="test.jpg">
</body>
</html>"""


def test_audit_context_immutability():
    soup = BeautifulSoup("<html></html>", "html.parser")
    ctx = AuditContext(
        url="https://example.com",
        html="<html></html>",
        soup=soup,
        text_content="",
        config=SEOAuditConfig(),
    )
    with pytest.raises(FrozenInstanceError):
        ctx.url = "https://other.com"


def test_versioned_audit_output():
    engine = SEOAuditEngine()
    result = engine.analyze_html(SAMPLE_GOOD_HTML, base_url="https://lawyerir.com")
    assert result["engine_version"] == ENGINE_VERSION
    assert result["ruleset_version"] == RULESET_VERSION
    assert "score" in result
    assert "metrics" in result
    assert "score_breakdown" in result


def test_good_html_analysis():
    engine = SEOAuditEngine()
    result = engine.analyze_html(SAMPLE_GOOD_HTML, base_url="https://lawyerir.com/lawyers/tehran")

    assert result["score"] >= 90
    metrics = result["metrics"]
    assert metrics["title"] == "وکیل پایه یک دادگستری در تهران - مشاوره حقوقی تخصصی"
    assert metrics["h1_count"] == 1
    assert metrics["h2_count"] == 1
    assert metrics["language"] == "fa"
    assert metrics["images_count"] == 1
    assert metrics["images_without_alt_count"] == 0
    assert metrics["internal_links_count"] == 1
    assert metrics["external_links_count"] == 1

    # Check evidence structure in breakdown
    breakdown = result["score_breakdown"]
    assert breakdown["title"]["passed"] is True
    assert "evidence" in breakdown["title"]
    assert breakdown["title"]["evidence"]["length"] > 0


def test_bad_html_analysis():
    engine = SEOAuditEngine()
    result = engine.analyze_html(SAMPLE_BAD_HTML, base_url="https://example.com")

    assert result["score"] < 50
    issues = result["issues"]
    issue_types = [i["type"] for i in issues]

    assert "missing_title" in issue_types
    assert "missing_meta_description" in issue_types
    assert "multiple_h1" in issue_types
    assert "low_word_count" in issue_types
    assert "noindex_detected" in issue_types

    assert len(result["recommendations"]) > 0


def test_custom_rule_extension():
    class CustomFaviconRule(BaseSEORule):
        def evaluate(self, ctx: AuditContext) -> RuleResult:
            icon = ctx.soup.find("link", attrs={"rel": lambda r: r and "icon" in r.lower()})
            if not icon:
                return RuleResult(
                    rule_name="favicon",
                    passed=False,
                    score=0.0,
                    max_score=5.0,
                    evidence={"favicon": None},
                    issues=[{"severity": "info", "type": "missing_favicon", "message": "Favicon missing."}],
                    recommendations=["Add a favicon."],
                )
            return RuleResult(
                rule_name="favicon",
                passed=True,
                score=5.0,
                max_score=5.0,
                evidence={"favicon": icon.get("href")},
            )

    engine = SEOAuditEngine()
    engine.register_rule(CustomFaviconRule())

    html_with_icon = "<html><head><title>Title Title Title Title Title Title</title><link rel='icon' href='/favicon.ico'></head><body></body></html>"
    res = engine.analyze_html(html_with_icon)
    assert "favicon" in res["score_breakdown"]
    assert res["score_breakdown"]["favicon"]["passed"] is True


def test_configurable_scoring():
    custom_config = SEOAuditConfig(weight_title=50.0, weight_meta_desc=50.0)
    engine = SEOAuditEngine()

    html = "<html><head><title>Title Title Title Title Title Title</title></head><body></body></html>"
    res = engine.analyze_html(html, config=custom_config)

    # Title passed (50/50), meta description missing (0/50) -> score roughly 50%
    breakdown = res["score_breakdown"]
    assert breakdown["title"]["max_score"] == 50.0
    assert breakdown["meta_description"]["max_score"] == 50.0
