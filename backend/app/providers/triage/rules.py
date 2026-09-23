from app.domain.enums import Category, Priority
from app.domain.models import TriageResult

_CATEGORY_KEYWORDS: dict[Category, tuple[str, ...]] = {
    Category.WATER: ("burst", "pipe", "leak", "flooding"),
    Category.ELECTRICITY: ("wire", "transformer", "spark", "outage"),
    Category.SANITATION: ("garbage", "sewage", "drain"),
    Category.ROADS: ("pothole", "crack", "road"),
    Category.STREETLIGHTS: ("streetlight", "lamp", "dark"),
}

_HIGH_PRIORITY_KEYWORDS = ("flooding", "spark", "fire", "danger")
_LOW_PRIORITY_KEYWORDS = ("cosmetic", "minor", "faded", "aesthetic")


def _match_category(text: str) -> Category:
    lowered = text.lower()
    for category, keywords in _CATEGORY_KEYWORDS.items():
        if any(keyword in lowered for keyword in keywords):
            return category
    return Category.OTHER


def _match_priority(text: str) -> Priority:
    lowered = text.lower()
    if any(keyword in lowered for keyword in _HIGH_PRIORITY_KEYWORDS):
        return Priority.HIGH
    if any(keyword in lowered for keyword in _LOW_PRIORITY_KEYWORDS):
        return Priority.LOW
    return Priority.NORMAL


class RuleBasedTriage:
    """The permanent fallback provider: no external calls, must never raise."""

    name = "rules"

    def triage(self, text: str, location: str) -> TriageResult:
        try:
            category = _match_category(text)
            priority = _match_priority(text)
            summary = text.strip()[:140] or "No summary available"
            return TriageResult(category=category, priority=priority, summary=summary, confidence=0.4)
        except Exception:
            # Must never raise: any unexpected input falls back to a safe,
            # always-valid result rather than propagating an exception.
            return TriageResult(
                category=Category.OTHER,
                priority=Priority.NORMAL,
                summary="Auto-classification unavailable",
                confidence=0.0,
            )
