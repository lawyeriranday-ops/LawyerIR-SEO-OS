from dataclasses import dataclass, field
import logging
import re
from urllib.parse import urlparse
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

GENERIC_ANCHORS = {
    # Persian generic anchors
    "اینجا", "اینجا کلیک کنید", "کلیک کنید", "ادامه", "ادامه مطلب", "اطلاعات بیشتر",
    "بیشتر بخوانید", "مشاهده", "منبع", "لینک", "این صفحه", "این لینک", "دیدن",
    # English generic anchors
    "here", "click here", "read more", "more", "learn more", "link", "this link",
    "this page", "website", "url", "source", "info", "details"
}


@dataclass
class LinkAuditConfig:
    weight_internal_presence: float = 25.0
    weight_anchor_quality: float = 35.0
    weight_external_balance: float = 20.0
    weight_rel_attributes: float = 20.0
    max_recommended_links: int = 100
    min_recommended_internal: int = 2


@dataclass
class LinkItem:
    href: str
    text: str
    is_internal: bool
    is_external: bool
    is_nofollow: bool
    is_sponsored: bool
    is_ugc: bool
    is_generic: bool
    is_empty: bool
    is_image_link: bool
    image_alt: str | None = None
    rel: list[str] = field(default_factory=list)


class LinkIntelligenceEngine:
    """Modular engine for analyzing internal/external link structure and anchor text quality."""

    def __init__(self, config: LinkAuditConfig | None = None):
        self.config = config or LinkAuditConfig()

    def is_generic_anchor(self, text: str | None) -> bool:
        if not text:
            return False
        cleaned = re.sub(r"[^\w\s]", "", text.strip().lower())
        # Collapse spaces
        cleaned = re.sub(r"\s+", " ", cleaned)
        return cleaned in GENERIC_ANCHORS

    def extract_links(self, html: str = "", base_url: str = "", soup: BeautifulSoup | None = None) -> list[LinkItem]:
        if soup is None:
            soup = BeautifulSoup(html, "html.parser")
        base_domain = urlparse(base_url).netloc.lower() if base_url else ""
        link_items: list[LinkItem] = []


        for a in soup.find_all("a"):
            href = a.get("href", "").strip()
            if not href or href.startswith("#") or href.startswith("javascript:"):
                continue

            rel_attr = a.get("rel", [])
            if isinstance(rel_attr, str):
                rel_list = rel_attr.lower().split()
            else:
                rel_list = [r.lower() for r in rel_attr]

            is_nofollow = "nofollow" in rel_list
            is_sponsored = "sponsored" in rel_list
            is_ugc = "ugc" in rel_list

            parsed = urlparse(href)
            is_external = bool(parsed.netloc and base_domain and parsed.netloc.lower() != base_domain)
            is_internal = not is_external

            img_tag = a.find("img")
            is_image_link = img_tag is not None
            img_alt = img_tag.get("alt", "").strip() if img_tag and img_tag.get("alt") else None

            anchor_text = a.get_text(strip=True)
            if not anchor_text and is_image_link and img_alt:
                anchor_text = f"[Image: {img_alt}]"

            is_empty = not bool(anchor_text)
            is_generic = self.is_generic_anchor(anchor_text)

            link_items.append(LinkItem(
                href=href,
                text=anchor_text,
                is_internal=is_internal,
                is_external=is_external,
                is_nofollow=is_nofollow,
                is_sponsored=is_sponsored,
                is_ugc=is_ugc,
                is_generic=is_generic,
                is_empty=is_empty,
                is_image_link=is_image_link,
                image_alt=img_alt,
                rel=rel_list,
            ))

        return link_items

    def analyze_links(
        self,
        html: str = "",
        base_url: str = "",
        config: LinkAuditConfig | None = None,
        soup: BeautifulSoup | None = None,
    ) -> dict:
        cfg = config or self.config
        links = self.extract_links(html=html, base_url=base_url, soup=soup)


        total_links = len(links)
        internal_links = [l for l in links if l.is_internal]
        external_links = [l for l in links if l.is_external]
        generic_links = [l for l in links if l.is_generic]
        empty_links = [l for l in links if l.is_empty]
        nofollow_links = [l for l in links if l.is_nofollow]
        sponsored_links = [l for l in links if l.is_sponsored]
        ugc_links = [l for l in links if l.is_ugc]

        # Calculate scores
        # 1. Internal Presence Score
        internal_score = cfg.weight_internal_presence
        if len(internal_links) < cfg.min_recommended_internal:
            internal_score *= (len(internal_links) / cfg.min_recommended_internal)

        # 2. Anchor Quality Score
        anchor_score = cfg.weight_anchor_quality
        if total_links > 0:
            bad_anchors = len(generic_links) + len(empty_links)
            good_ratio = max(0.0, (total_links - bad_anchors) / total_links)
            anchor_score *= good_ratio

        # 3. External Balance Score
        external_score = cfg.weight_external_balance
        if total_links > cfg.max_recommended_links:
            external_score *= (cfg.max_recommended_links / total_links)

        # 4. Rel Attributes Score
        rel_score = cfg.weight_rel_attributes

        total_score = round(internal_score + anchor_score + external_score + rel_score)
        total_score = max(0, min(100, total_score))

        issues = []
        recommendations = []

        if len(internal_links) == 0:
            issues.append({
                "severity": "critical",
                "type": "missing_internal_links",
                "message": "Page has zero internal links."
            })
            recommendations.append("Add relevant internal links to guide users and search bots to related site content.")

        if len(generic_links) > 0:
            issues.append({
                "severity": "warning",
                "type": "generic_anchor_texts",
                "message": f"Found {len(generic_links)} link(s) with uninformative generic anchor text (e.g., 'click here', 'اینجا')."
            })
            recommendations.append("Replace generic anchor texts with descriptive keywords representing the target page subject.")

        if len(empty_links) > 0:
            issues.append({
                "severity": "warning",
                "type": "empty_anchor_texts",
                "message": f"Found {len(empty_links)} link(s) with empty anchor text."
            })
            recommendations.append("Ensure all links contain visible descriptive text or img alt text.")

        if total_links > cfg.max_recommended_links:
            issues.append({
                "severity": "warning",
                "type": "excessive_links",
                "message": f"High link count ({total_links} links). Recommended maximum is {cfg.max_recommended_links} links per page."
            })
            recommendations.append(f"Reduce total link count to under {cfg.max_recommended_links} to preserve link equity flow.")

        return {
            "score": total_score,
            "metrics": {
                "total_links": total_links,
                "internal_links_count": len(internal_links),
                "external_links_count": len(external_links),
                "generic_anchors_count": len(generic_links),
                "empty_anchors_count": len(empty_links),
                "nofollow_links_count": len(nofollow_links),
                "sponsored_links_count": len(sponsored_links),
                "ugc_links_count": len(ugc_links),
            },
            "link_details": [
                {
                    "href": l.href,
                    "text": l.text,
                    "is_internal": l.is_internal,
                    "is_external": l.is_external,
                    "is_generic": l.is_generic,
                    "is_empty": l.is_empty,
                    "rel": l.rel,
                }
                for l in links[:50]
            ],
            "issues": issues,
            "recommendations": recommendations,
        }
