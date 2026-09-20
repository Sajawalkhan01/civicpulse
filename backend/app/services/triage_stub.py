from app.domain.enums import Category, Priority
from app.domain.models import TriageResult


class StubTriageProvider:
    """Temporary stand-in for a real TriageProvider (see providers/triage/).

    Always returns a fixed, low-confidence classification so the complaint
    endpoints are testable end to end before real triage is wired in.
    """

    name = "stub"

    def triage(self, text: str, location: str) -> TriageResult:
        return TriageResult(
            category=Category.OTHER,
            priority=Priority.NORMAL,
            summary="Pending triage: stub classification",
            confidence=0.5,
        )
