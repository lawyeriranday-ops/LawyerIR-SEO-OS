from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from urllib.parse import urlparse
import logging
import re
from bs4 import BeautifulSoup
import httpx

from app.services.keyword_engine import KeywordAnalyzerEngine

ENGINE_VERSION = "1.0.0"
RULESET_VERSION = "1.0.0"

logger = logging.getLogger(__name__)


@dataclass
class SEOAuditConfig:
    weight_title: float = 15.0
    title_min_len: int = 30
    title_max_len: int = 60

    weight_meta_desc: float = 15.0
    meta_desc_min_len: int = 70
    meta_desc_max_len: int = 160

    weight_h1: float = 15.0
    weight_h2: float = 10.0

    weight_word_count: float = 15.0
    min_word_count: int = 300

    weight_canonical: float = 10.0
    weight_alt_text: float = 10.0
    weight_robots: float = 5.0
    weight_lang: float = 5.0


@dataclass(frozen=True)
class AuditContext:
    url: str
    html: str
    soup: BeautifulSoup
    text_content: str
    config: SEOAuditConfig
    target_keyword: str | None = None
    engine_version: str = ENGINE_VERSION
    ruleset_version: str = RULESET_VERSION


@dataclass
class RuleResult:
    rule_name: str
    passed: bool
    score: float
    max_score: float
    evidence: dict = field(default_factory=dict)
    issues: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class BaseSEORule(ABC):
    @abstractmethod
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        pass


class TitleRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        title_tag = ctx.soup.find("title")
        title_text = title_tag.get_text(strip=True) if title_tag else None
        title_len = len(title_text) if title_text else 0
        max_pts = ctx.config.weight_title

        if not title_text:
            return RuleResult(
                rule_name="title",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"title": None, "length": 0},
                issues=[{
                    "severity": "critical",
                    "type": "missing_title",
                    "message": "Page is missing a <title> tag."
                }],
                recommendations=["Add a descriptive <title> tag between 30 and 60 characters."]
            )

        if title_len < ctx.config.title_min_len:
            return RuleResult(
                rule_name="title",
                passed=False,
                score=round(max_pts * 0.5, 2),
                max_score=max_pts,
                evidence={"title": title_text, "length": title_len},
                issues=[{
                    "severity": "warning",
                    "type": "title_too_short",
                    "message": f"Title is too short ({title_len} chars). Minimum recommended is {ctx.config.title_min_len} chars."
                }],
                recommendations=[f"Expand title to at least {ctx.config.title_min_len} characters."]
            )

        if title_len > ctx.config.title_max_len:
            return RuleResult(
                rule_name="title",
                passed=False,
                score=round(max_pts * 0.75, 2),
                max_score=max_pts,
                evidence={"title": title_text, "length": title_len},
                issues=[{
                    "severity": "warning",
                    "type": "title_too_long",
                    "message": f"Title is too long ({title_len} chars). Maximum recommended is {ctx.config.title_max_len} chars."
                }],
                recommendations=[f"Shorten title to under {ctx.config.title_max_len} characters to avoid search snippet truncation."]
            )

        return RuleResult(
            rule_name="title",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"title": title_text, "length": title_len}
        )


class MetaDescriptionRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        meta_tag = ctx.soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        meta_text = meta_tag.get("content", "").strip() if meta_tag and meta_tag.get("content") else None
        meta_len = len(meta_text) if meta_text else 0
        max_pts = ctx.config.weight_meta_desc

        if not meta_text:
            return RuleResult(
                rule_name="meta_description",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"meta_description": None, "length": 0},
                issues=[{
                    "severity": "warning",
                    "type": "missing_meta_description",
                    "message": "Page is missing a meta description tag."
                }],
                recommendations=["Add a compelling meta description tag between 70 and 160 characters."]
            )

        if meta_len < ctx.config.meta_desc_min_len or meta_len > ctx.config.meta_desc_max_len:
            return RuleResult(
                rule_name="meta_description",
                passed=False,
                score=round(max_pts * 0.5, 2),
                max_score=max_pts,
                evidence={"meta_description": meta_text, "length": meta_len},
                issues=[{
                    "severity": "warning",
                    "type": "meta_description_length",
                    "message": f"Meta description length ({meta_len} chars) is outside recommended range ({ctx.config.meta_desc_min_len}-{ctx.config.meta_desc_max_len} chars)."
                }],
                recommendations=[f"Adjust meta description to be between {ctx.config.meta_desc_min_len} and {ctx.config.meta_desc_max_len} characters."]
            )

        return RuleResult(
            rule_name="meta_description",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"meta_description": meta_text, "length": meta_len}
        )


class H1Rule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        h1_tags = ctx.soup.find_all("h1")
        h1_count = len(h1_tags)
        h1_text = h1_tags[0].get_text(strip=True) if h1_count > 0 else None
        max_pts = ctx.config.weight_h1

        if h1_count == 0:
            return RuleResult(
                rule_name="h1",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"h1_count": 0, "first_h1": None},
                issues=[{
                    "severity": "critical",
                    "type": "missing_h1",
                    "message": "Page has no <h1> heading tag."
                }],
                recommendations=["Add exactly one <h1> heading tag representing the main page subject."]
            )
        elif h1_count > 1:
            return RuleResult(
                rule_name="h1",
                passed=False,
                score=round(max_pts * 0.5, 2),
                max_score=max_pts,
                evidence={"h1_count": h1_count, "first_h1": h1_text},
                issues=[{
                    "severity": "warning",
                    "type": "multiple_h1",
                    "message": f"Page has multiple ({h1_count}) <h1> heading tags."
                }],
                recommendations=["Use only one <h1> heading tag per page for clean structural hierarchy."]
            )

        return RuleResult(
            rule_name="h1",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"h1_count": 1, "first_h1": h1_text}
        )


class H2Rule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        h2_tags = ctx.soup.find_all("h2")
        h2_count = len(h2_tags)
        max_pts = ctx.config.weight_h2

        if h2_count == 0:
            return RuleResult(
                rule_name="h2",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"h2_count": 0},
                issues=[{
                    "severity": "info",
                    "type": "missing_h2",
                    "message": "Page has no <h2> heading tags."
                }],
                recommendations=["Use <h2> headings to structure content sections."]
            )

        return RuleResult(
            rule_name="h2",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"h2_count": h2_count}
        )


class WordCountRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        words = ctx.text_content.split()
        word_count = len(words)
        max_pts = ctx.config.weight_word_count
        min_words = ctx.config.min_word_count

        if word_count < min_words:
            ratio = word_count / min_words if min_words > 0 else 1.0
            pts = round(max_pts * ratio, 2)
            return RuleResult(
                rule_name="word_count",
                passed=False,
                score=pts,
                max_score=max_pts,
                evidence={"word_count": word_count, "min_recommended": min_words},
                issues=[{
                    "severity": "warning",
                    "type": "low_word_count",
                    "message": f"Low word count ({word_count} words). Recommended minimum is {min_words} words."
                }],
                recommendations=[f"Expand page content to at least {min_words} words of high-quality relevant text."]
            )

        return RuleResult(
            rule_name="word_count",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"word_count": word_count, "min_recommended": min_words}
        )


class CanonicalRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        canonical_tag = ctx.soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
        canonical_url = canonical_tag.get("href", "").strip() if canonical_tag and canonical_tag.get("href") else None
        max_pts = ctx.config.weight_canonical

        if not canonical_url:
            return RuleResult(
                rule_name="canonical",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"canonical": None},
                issues=[{
                    "severity": "warning",
                    "type": "missing_canonical",
                    "message": "Page is missing a canonical link tag."
                }],
                recommendations=["Add a <link rel='canonical' href='...'> tag to specify the primary URL for search engines."]
            )

        return RuleResult(
            rule_name="canonical",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"canonical": canonical_url}
        )


class ImagesAltRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        images = ctx.soup.find_all("img")
        total_images = len(images)
        max_pts = ctx.config.weight_alt_text

        if total_images == 0:
            return RuleResult(
                rule_name="images_alt",
                passed=True,
                score=max_pts,
                max_score=max_pts,
                evidence={"total_images": 0, "missing_alt_count": 0}
            )

        missing_alt = [img for img in images if not img.get("alt") or not img.get("alt").strip()]
        missing_alt_count = len(missing_alt)

        if missing_alt_count > 0:
            ratio = (total_images - missing_alt_count) / total_images
            pts = round(max_pts * ratio, 2)
            return RuleResult(
                rule_name="images_alt",
                passed=False,
                score=pts,
                max_score=max_pts,
                evidence={"total_images": total_images, "missing_alt_count": missing_alt_count},
                issues=[{
                    "severity": "warning",
                    "type": "missing_image_alt",
                    "message": f"{missing_alt_count} out of {total_images} image(s) are missing descriptive alt text."
                }],
                recommendations=["Add meaningful alt text attributes to all non-decorative <img> elements for SEO and accessibility."]
            )

        return RuleResult(
            rule_name="images_alt",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"total_images": total_images, "missing_alt_count": 0}
        )


class RobotsMetaRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        robots_tag = ctx.soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_content = robots_tag.get("content", "").strip() if robots_tag and robots_tag.get("content") else None
        max_pts = ctx.config.weight_robots

        if robots_content and "noindex" in robots_content.lower():
            return RuleResult(
                rule_name="robots_meta",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"robots_meta": robots_content},
                issues=[{
                    "severity": "critical",
                    "type": "noindex_detected",
                    "message": "Robots meta tag specifies 'noindex', preventing search engines from indexing this page."
                }],
                recommendations=["Remove 'noindex' from robots meta tag if this page should be indexed in search results."]
            )

        return RuleResult(
            rule_name="robots_meta",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"robots_meta": robots_content}
        )


class LanguageRule(BaseSEORule):
    def evaluate(self, ctx: AuditContext) -> RuleResult:
        html_tag = ctx.soup.find("html")
        lang = html_tag.get("lang", "").strip() if html_tag and html_tag.get("lang") else None
        max_pts = ctx.config.weight_lang

        if not lang:
            return RuleResult(
                rule_name="language",
                passed=False,
                score=0.0,
                max_score=max_pts,
                evidence={"language": None},
                issues=[{
                    "severity": "info",
                    "type": "missing_language",
                    "message": "The <html> tag is missing a 'lang' attribute."
                }],
                recommendations=["Add a 'lang' attribute to the <html> tag (e.g., lang='fa' or lang='en')."]
            )

        return RuleResult(
            rule_name="language",
            passed=True,
            score=max_pts,
            max_score=max_pts,
            evidence={"language": lang}
        )


class SEOAuditEngine:
    def __init__(self, rules: list[BaseSEORule] | None = None):
        if rules is not None:
            self.rules = list(rules)
        else:
            self.rules = [
                TitleRule(),
                MetaDescriptionRule(),
                H1Rule(),
                H2Rule(),
                WordCountRule(),
                CanonicalRule(),
                ImagesAltRule(),
                RobotsMetaRule(),
                LanguageRule(),
            ]

    def register_rule(self, rule: BaseSEORule) -> None:
        self.rules.append(rule)

    def extract_metrics(self, soup: BeautifulSoup, text_content: str, base_url: str) -> dict:
        title_tag = soup.find("title")
        title = title_tag.get_text(strip=True) if title_tag else None

        meta_tag = soup.find("meta", attrs={"name": re.compile(r"^description$", re.I)})
        meta_description = meta_tag.get("content", "").strip() if meta_tag and meta_tag.get("content") else None

        h1_tags = soup.find_all("h1")
        h1_count = len(h1_tags)
        h1 = h1_tags[0].get_text(strip=True) if h1_count > 0 else None

        h2_tags = soup.find_all("h2")
        h2_count = len(h2_tags)

        word_count = len(text_content.split())

        canonical_tag = soup.find("link", attrs={"rel": re.compile(r"^canonical$", re.I)})
        canonical = canonical_tag.get("href", "").strip() if canonical_tag and canonical_tag.get("href") else None

        robots_tag = soup.find("meta", attrs={"name": re.compile(r"^robots$", re.I)})
        robots_meta = robots_tag.get("content", "").strip() if robots_tag and robots_tag.get("content") else None

        html_tag = soup.find("html")
        language = html_tag.get("lang", "").strip() if html_tag and html_tag.get("lang") else None

        base_domain = urlparse(base_url).netloc.lower() if base_url else ""

        internal_links = []
        external_links = []
        for a in soup.find_all("a", href=True):
            href = a.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue
            parsed_href = urlparse(href)
            if not parsed_href.netloc or (base_domain and parsed_href.netloc.lower() == base_domain):
                internal_links.append(href)
            else:
                external_links.append(href)

        images = soup.find_all("img")
        image_sources = [img.get("src", "").strip() for img in images if img.get("src")]
        images_without_alt = [
            img.get("src", "").strip() for img in images
            if not img.get("alt") or not img.get("alt").strip()
        ]

        return {
            "title": title,
            "meta_description": meta_description,
            "h1": h1,
            "h1_count": h1_count,
            "h2_count": h2_count,
            "word_count": word_count,
            "canonical": canonical,
            "robots_meta": robots_meta,
            "language": language,
            "internal_links_count": len(internal_links),
            "external_links_count": len(external_links),
            "internal_links": internal_links[:20],
            "external_links": external_links[:20],
            "images_count": len(images),
            "images_without_alt_count": len(images_without_alt),
            "images_without_alt": images_without_alt[:20],
        }

    def analyze_html(
        self,
        html: str,
        base_url: str = "",
        config: SEOAuditConfig | None = None,
        target_keyword: str | None = None,
    ) -> dict:
        cfg = config or SEOAuditConfig()
        soup = BeautifulSoup(html, "html.parser")

        # Strip scripts, styles, noscript for clean text extraction
        for element in soup(["script", "style", "noscript"]):
            element.decompose()

        text_content = soup.get_text(separator=" ", strip=True)

        ctx = AuditContext(
            url=base_url,
            html=html,
            soup=soup,
            text_content=text_content,
            config=cfg,
            target_keyword=target_keyword,
            engine_version=ENGINE_VERSION,
            ruleset_version=RULESET_VERSION,
        )

        metrics = self.extract_metrics(soup, text_content, base_url)

        rule_results: list[RuleResult] = []
        issues: list[dict] = []
        recommendations: list[str] = []
        score_breakdown: dict[str, dict] = {}

        total_earned = 0.0
        total_possible = 0.0

        for rule in self.rules:
            res = rule.evaluate(ctx)
            rule_results.append(res)
            total_earned += res.score
            total_possible += res.max_score

            score_breakdown[res.rule_name] = {
                "score": res.score,
                "max_score": res.max_score,
                "passed": res.passed,
                "evidence": res.evidence,
            }

            for iss in res.issues:
                issues.append(iss)
            for rec in res.recommendations:
                if rec not in recommendations:
                    recommendations.append(rec)

        overall_score = round((total_earned / total_possible) * 100) if total_possible > 0 else 0

        keyword_analysis = None
        if target_keyword and target_keyword.strip():
            kw_analyzer = KeywordAnalyzerEngine()
            h2_texts = [h2.get_text(strip=True) for h2 in soup.find_all("h2")]
            image_alts = [
                img.get("alt", "").strip() for img in soup.find_all("img")
                if img.get("alt") and img.get("alt").strip()
            ]
            keyword_analysis = kw_analyzer.analyze_keyword(
                target_keyword=target_keyword,
                text_content=text_content,
                title=metrics["title"],
                meta_desc=metrics["meta_description"],
                h1=metrics["h1"],
                h2_list=h2_texts,
                image_alts=image_alts,
                url_path=base_url,
            )
            for iss in keyword_analysis.get("issues", []):
                issues.append(iss)
            for rec in keyword_analysis.get("recommendations", []):
                if rec not in recommendations:
                    recommendations.append(rec)

        return {
            "engine_version": ENGINE_VERSION,
            "ruleset_version": RULESET_VERSION,
            "score": max(0, min(100, overall_score)),
            "metrics": metrics,
            "score_breakdown": score_breakdown,
            "issues": issues,
            "recommendations": recommendations,
            "rules_evaluated": len(rule_results),
            "keyword_analysis": keyword_analysis,
        }

    async def fetch_and_analyze(
        self,
        url: str,
        config: SEOAuditConfig | None = None,
        target_keyword: str | None = None,
        retries: int = 2,
    ) -> dict:
        headers = {
            "User-Agent": "LawyerIR-SEO-OS/1.0 (SEO Audit Engine)"
        }
        attempt = 0
        last_error = None

        while attempt <= retries:
            try:
                async with httpx.AsyncClient(timeout=10.0, follow_redirects=True) as client:
                    response = await client.get(url, headers=headers)
                    response.raise_for_status()
                    html = response.text
                    return self.analyze_html(
                        html=html,
                        base_url=str(response.url),
                        config=config,
                        target_keyword=target_keyword,
                    )
            except (httpx.HTTPError, httpx.TimeoutException) as exc:
                last_error = exc
                logger.warning("Attempt %d failed fetching %s: %r", attempt + 1, url, exc)
                attempt += 1

        return {
            "engine_version": ENGINE_VERSION,
            "ruleset_version": RULESET_VERSION,
            "score": 0,
            "metrics": {},
            "score_breakdown": {},
            "issues": [{
                "severity": "critical",
                "type": "fetch_failure",
                "message": f"Failed to fetch URL '{url}' after {retries + 1} attempts: {last_error}"
            }],
            "recommendations": ["Verify the target URL is publicly accessible and responding."],
            "rules_evaluated": 0,
            "keyword_analysis": None,
            "error": str(last_error),
        }
