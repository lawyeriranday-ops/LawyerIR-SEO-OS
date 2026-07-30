import re
from dataclasses import dataclass, field
import logging

logger = logging.getLogger(__name__)


def normalize_text(text: str | None) -> str:
    """Normalizes Persian and English text for accurate keyword matching."""
    if not text:
        return ""
    
    # Standardize Persian characters
    s = text.replace("ك", "ک").replace("ي", "ی").replace("ئ", "ی")
    # Replace ZWNJ (نیم‌فاصله) with standard space for word tokenization
    s = s.replace("\u200c", " ")
    # Convert to lowercase
    s = s.lower()
    # Remove punctuation except spaces and word characters
    s = re.sub(r"[^\w\s]", " ", s)
    # Collapse multiple whitespaces
    s = re.sub(r"\s+", " ", s).strip()
    return s


@dataclass
class KeywordMetrics:
    target_keyword: str
    keyword_count: int
    total_words: int
    density_percentage: float
    in_title: bool
    in_title_front: bool
    in_meta_description: bool
    in_h1: bool
    in_h2: bool
    in_introduction: bool
    in_url_slug: bool
    in_image_alts: bool


@dataclass
class KeywordAnalysisResult:
    target_keyword: str
    score: int
    metrics: dict
    issues: list[dict] = field(default_factory=list)
    recommendations: list[str] = field(default_factory=list)


class KeywordAnalyzerEngine:
    """Modular engine for analyzing target keyword optimization in HTML content."""

    def __init__(
        self,
        min_density: float = 0.5,
        max_density: float = 2.5,
        stuffing_threshold: float = 3.5,
        min_reliable_words: int = 100,
    ):

        self.min_density = min_density
        self.max_density = max_density
        self.stuffing_threshold = stuffing_threshold
        self.min_reliable_words = min_reliable_words

    def calculate_density(self, target_keyword: str, text_content: str) -> tuple[int, int, float]:
        norm_kw = normalize_text(target_keyword)
        norm_text = normalize_text(text_content)

        if not norm_kw or not norm_text:
            return 0, 0, 0.0

        words = norm_text.split()
        total_words = len(words)
        if total_words == 0:
            return 0, 0, 0.0

        kw_words = norm_kw.split()
        kw_word_count = len(kw_words)

        if kw_word_count == 1:
            count = words.count(norm_kw)
        else:
            # Multi-word phrase matching over tokenized words
            count = 0
            for i in range(len(words) - kw_word_count + 1):
                if words[i : i + kw_word_count] == kw_words:
                    count += 1

        # Calculate density: (kw occurrences * kw word length / total words) * 100
        density = round(((count * kw_word_count) / total_words) * 100, 2)
        return count, total_words, density

    def check_placement(
        self,
        target_keyword: str,
        title: str | None = None,
        meta_desc: str | None = None,
        h1: str | None = None,
        h2_list: list[str] | None = None,
        intro_text: str | None = None,
        image_alts: list[str] | None = None,
        url_path: str | None = None,
    ) -> dict[str, bool]:
        norm_kw = normalize_text(target_keyword)
        if not norm_kw:
            return {
                "in_title": False,
                "in_title_front": False,
                "in_meta_description": False,
                "in_h1": False,
                "in_h2": False,
                "in_introduction": False,
                "in_url_slug": False,
                "in_image_alts": False,
            }

        norm_title = normalize_text(title)
        in_title = norm_kw in norm_title if norm_title else False

        # Front-loaded title check (appears within the first 4 words of title)
        in_title_front = False
        if in_title and norm_title:
            title_words = norm_title.split()[:4]
            front_snippet = " ".join(title_words)
            in_title_front = norm_kw in front_snippet

        norm_meta = normalize_text(meta_desc)
        in_meta = norm_kw in norm_meta if norm_meta else False

        norm_h1 = normalize_text(h1)
        in_h1 = norm_kw in norm_h1 if norm_h1 else False

        in_h2 = False
        if h2_list:
            for h2 in h2_list:
                if norm_kw in normalize_text(h2):
                    in_h2 = True
                    break

        norm_intro = normalize_text(intro_text)
        in_intro = norm_kw in norm_intro if norm_intro else False

        in_image_alts = False
        if image_alts:
            for alt in image_alts:
                if norm_kw in normalize_text(alt):
                    in_image_alts = True
                    break

        norm_url = normalize_text(url_path)
        in_url_slug = norm_kw in norm_url if norm_url else False

        return {
            "in_title": in_title,
            "in_title_front": in_title_front,
            "in_meta_description": in_meta,
            "in_h1": in_h1,
            "in_h2": in_h2,
            "in_introduction": in_intro,
            "in_url_slug": in_url_slug,
            "in_image_alts": in_image_alts,
        }

    def analyze_keyword(
        self,
        target_keyword: str,
        text_content: str,
        title: str | None = None,
        meta_desc: str | None = None,
        h1: str | None = None,
        h2_list: list[str] | None = None,
        image_alts: list[str] | None = None,
        url_path: str | None = None,
    ) -> dict:
        if not target_keyword or not target_keyword.strip():
            return {
                "target_keyword": "",
                "score": 0,
                "metrics": {},
                "issues": [{"severity": "warning", "type": "empty_target_keyword", "message": "No target keyword provided."}],
                "recommendations": [],
            }

        # Extract introduction text (first 100 words of body text)
        words = normalize_text(text_content).split()
        intro_text = " ".join(words[:100]) if words else ""

        kw_count, total_words, density = self.calculate_density(target_keyword, text_content)
        placements = self.check_placement(
            target_keyword, title, meta_desc, h1, h2_list, intro_text, image_alts, url_path
        )

        metrics = {
            "target_keyword": target_keyword,
            "keyword_count": kw_count,
            "total_words": total_words,
            "density_percentage": density,
            **placements,
        }

        # Calculate keyword optimization score (max 100 pts)
        earned = 0.0
        total_possible = 100.0

        # Title placement: 25 pts (15 pts in title + 10 pts front-loaded)
        if placements["in_title"]:
            earned += 15.0
            if placements["in_title_front"]:
                earned += 10.0
        # H1 placement: 20 pts
        if placements["in_h1"]:
            earned += 20.0
        # Meta description placement: 15 pts
        if placements["in_meta_description"]:
            earned += 15.0
        # Introduction placement (first 100 words): 15 pts
        if placements["in_introduction"]:
            earned += 15.0
        # H2 placement: 10 pts
        if placements["in_h2"]:
            earned += 10.0
        # Keyword density score: 15 pts
        if self.min_density <= density <= self.max_density:
            earned += 15.0
        elif 0 < density < self.min_density or total_words < self.min_reliable_words:
            earned += 7.5

        issues = []
        recommendations = []

        if total_words < self.min_reliable_words:
            issues.append({
                "severity": "info",
                "type": "short_content_density_unreliable",
                "message": f"Content length ({total_words} words) is below the reliable threshold ({self.min_reliable_words} words) for keyword density evaluation."
            })
            recommendations.append(f"Add more content (at least {self.min_reliable_words} words) for an accurate keyword density assessment.")
        elif density > self.stuffing_threshold:
            issues.append({
                "severity": "critical",
                "type": "keyword_stuffing",
                "message": f"Keyword density ({density}%) exceeds threshold ({self.stuffing_threshold}%). Risk of search engine penalty."
            })
            recommendations.append(f"Reduce usage of '{target_keyword}' to bring density between {self.min_density}% and {self.max_density}%.")
        elif density < self.min_density:
            issues.append({
                "severity": "warning",
                "type": "low_keyword_density",
                "message": f"Keyword density ({density}%) is below recommended minimum ({self.min_density}%)."
            })
            recommendations.append(f"Naturally incorporate '{target_keyword}' more frequently in main content.")

        if not placements["in_title"]:
            issues.append({
                "severity": "critical",
                "type": "keyword_missing_title",
                "message": f"Target keyword '{target_keyword}' is missing from <title> tag."
            })
            recommendations.append(f"Include '{target_keyword}' near the beginning of your <title> tag.")

        if not placements["in_h1"]:
            issues.append({
                "severity": "critical",
                "type": "keyword_missing_h1",
                "message": f"Target keyword '{target_keyword}' is missing from <h1> tag."
            })
            recommendations.append(f"Include '{target_keyword}' in the main <h1> heading.")

        if not placements["in_meta_description"]:
            issues.append({
                "severity": "warning",
                "type": "keyword_missing_meta",
                "message": f"Target keyword '{target_keyword}' is missing from meta description."
            })
            recommendations.append(f"Add '{target_keyword}' to the meta description tag.")

        if not placements["in_introduction"]:
            issues.append({
                "severity": "warning",
                "type": "keyword_missing_intro",
                "message": f"Target keyword '{target_keyword}' is missing from first 100 words."
            })
            recommendations.append(f"Mention '{target_keyword}' in the opening paragraph/introduction of the page.")

        final_score = round((earned / total_possible) * 100)

        return {
            "target_keyword": target_keyword,
            "score": max(0, min(100, final_score)),
            "metrics": metrics,
            "issues": issues,
            "recommendations": recommendations,
        }
