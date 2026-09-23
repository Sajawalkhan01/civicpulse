import hashlib
import time

from app.domain.enums import Category, Priority
from app.domain.models import TriageResult
from app.providers.triage.base import RetryableTriageError, validate_triage_payload


class SimulatedTriage:
    """Deterministic, network-free triage provider for tests and CI.

    mode="normal" returns a valid, deterministic TriageResult derived from a
    hash of the input text (no randomness). The other modes inject specific
    failure shapes so services/triage_service.py's timeout/retry/fallback/
    validation logic can be exercised without real network calls.

    mode="timeout" only sleeps for `timeout_seconds` and then returns a
    normal result — it doesn't raise anything itself. Whether that counts as
    "too slow" is entirely up to the caller's own hard-timeout wrapper, so
    this provider stays agnostic of what threshold is being enforced.
    """

    name = "simulated"

    def __init__(
        self,
        mode: str = "normal",
        error: Exception | None = None,
        timeout_seconds: float = 0.0,
    ) -> None:
        self.mode = mode
        self.error = error
        self.timeout_seconds = timeout_seconds
        self.call_count = 0

    def triage(self, text: str, location: str) -> TriageResult:
        self.call_count += 1

        if self.mode == "always_raise":
            raise self.error or RetryableTriageError("simulated provider failure")

        if self.mode == "timeout":
            time.sleep(self.timeout_seconds)

        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
        seed = int(digest[:8], 16)

        if self.mode == "malformed":
            # A category not in the enum AND a summary over 140 chars, so
            # validation fails regardless of which check runs first.
            return validate_triage_payload(
                {
                    "category": "not_a_real_category",
                    "priority": "normal",
                    "summary": "x" * 300,
                    "confidence": 0.5,
                }
            )

        categories = list(Category)
        priorities = list(Priority)
        payload = {
            "category": categories[seed % len(categories)].value,
            "priority": priorities[seed % len(priorities)].value,
            "summary": f"Simulated triage summary for hash {digest[:8]}",
            "confidence": round(0.5 + (seed % 50) / 100, 2),
        }
        return validate_triage_payload(payload)
