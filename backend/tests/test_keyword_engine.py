import pytest
from app.services.keyword_engine import KeywordAnalyzerEngine, normalize_text


def test_normalize_text_persian_and_english():
    # Persian character standardization and ZWNJ handling
    raw_persian = "وکیل\u200cملکی پایه یک دادگستری كیفر و حقوقي"
    norm = normalize_text(raw_persian)
    assert "وکیل ملکی" in norm
    assert "کیفر" in norm
    assert "حقوقی" in norm

    # English case and punctuation stripping
    raw_english = "LawyerIR: Best SEO Platform & AI Agents!!!"
    norm_en = normalize_text(raw_english)
    assert norm_en == "lawyerir best seo platform ai agents"


def test_calculate_density_single_and_multiword():
    engine = KeywordAnalyzerEngine()

    text = "وکیل ملکی در تهران آماده ارائه مشاوره به عنوان وکیل ملکی متخصص در امور ثبت و املاک می‌باشد. وکیل ملکی تجربه زیادی دارد."
    # Keyword "وکیل ملکی" occurs 3 times. Length of phrase is 2 words.
    count, total_words, density = engine.calculate_density("وکیل ملکی", text)

    assert count == 3
    assert total_words > 10
    assert density > 0.0


def test_check_placement_all_elements():
    engine = KeywordAnalyzerEngine()

    target = "وکیل ملکی"
    title = "وکیل ملکی در تهران | مشاوره حقوقی"
    meta = "خدمات تخصصی وکیل ملکی در تهران"
    h1 = "وکیل ملکی شایسته"
    h2_list = ["چرا به وکیل ملکی نیاز داریم؟", "هزینه دفتر وکالت"]
    intro = "اگر به دنبال وکیل ملکی هستید..."
    alts = ["تصویر وکیل ملکی"]
    slug = "/lawyers/vokala-melki"

    placements = engine.check_placement(
        target_keyword=target,
        title=title,
        meta_desc=meta,
        h1=h1,
        h2_list=h2_list,
        intro_text=intro,
        image_alts=alts,
        url_path=slug,
    )

    assert placements["in_title"] is True
    assert placements["in_title_front"] is True
    assert placements["in_meta_description"] is True
    assert placements["in_h1"] is True
    assert placements["in_h2"] is True
    assert placements["in_introduction"] is True
    assert placements["in_image_alts"] is True


def test_analyze_keyword_well_optimized():
    engine = KeywordAnalyzerEngine()

    target = "وکیل ملکی"
    base_paragraph = (
        "انتخاب یک مشاوره با تجربه می‌تواند به موفقیت پرونده‌های حقوقی و ثبتی شما کمک کند. "
        "دفتر وکالت ما خدمات متنوعی شامل تنظیم قراردادها، پیگیری دعاوی حقوقی و خلع ید ارائه می‌دهد. "
        "همچنین مشاوران ما با بررسی دقیق مدارک پرونده شما، بهترین راهکار قانونی را پیشنهاد خواهند داد. "
        "در صورت نیاز به مشاوره تخصصی در تهران می‌توانید با شماره‌های دفتر تماس بگیرید. "
    )
    text = "وکیل ملکی در تهران آماده ارائه مشاوره حقوقی تخصصی به شماست. " + (base_paragraph * 4) + " خدمات وکیل ملکی با سابقه شامل کلیه امور ثبتی است."

    res = engine.analyze_keyword(
        target_keyword=target,
        text_content=text,
        title="وکیل ملکی تخصصی در تهران",
        meta_desc="مشاوره حقوقی تخصصی با وکیل ملکی در تهران.",
        h1="وکیل ملکی در تهران",
        h2_list=["خدمات وکیل ملکی"],
        image_alts=["دفتر وکیل ملکی"],
    )

    assert res["score"] >= 80
    assert res["metrics"]["in_title"] is True
    assert res["metrics"]["in_h1"] is True
    assert len(res["issues"]) == 0 or all(i["severity"] != "critical" for i in res["issues"])





def test_analyze_keyword_stuffing_warning():
    # Long text (>= 100 words) with keyword density > 3.5%
    engine = KeywordAnalyzerEngine(stuffing_threshold=3.5, min_reliable_words=100)

    target = "وکیل"
    text = "وکیل " * 50 + "محتوای حقوقی دفتر وکالت در تهران برای بررسی " * 10

    res = engine.analyze_keyword(
        target_keyword=target,
        text_content=text,
        title="وکیل",
        h1="وکیل",
    )

    assert any(i["type"] == "keyword_stuffing" for i in res["issues"])
    assert any(i["severity"] == "critical" for i in res["issues"])


def test_short_content_density_unreliable():
    # Short text (< 100 words) should NOT flag critical keyword stuffing
    engine = KeywordAnalyzerEngine(min_reliable_words=100)

    target = "وکیل"
    text = "وکیل وکیل وکیل وکیل در متن کوتاه"

    res = engine.analyze_keyword(
        target_keyword=target,
        text_content=text,
        title="وکیل",
        h1="وکیل",
    )

    # Should have info issue for short content instead of critical keyword stuffing
    assert any(i["type"] == "short_content_density_unreliable" for i in res["issues"])
    assert not any(i["type"] == "keyword_stuffing" for i in res["issues"])


def test_empty_target_keyword():
    engine = KeywordAnalyzerEngine()
    res = engine.analyze_keyword("", "محتوای صفحه")
    assert res["score"] == 0
    assert len(res["issues"]) == 1
    assert res["issues"][0]["type"] == "empty_target_keyword"

