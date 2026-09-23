import json

from pydantic import ValidationError

from app.domain.models import TriageResult
from app.domain.protocols import TriageProvider

__all__ = [
    "TriageProvider",
    "TriageProviderError",
    "RetryableTriageError",
    "NonRetryableTriageError",
    "TriageValidationError",
    "validate_triage_payload",
]


class TriageProviderError(Exception):
    """Base class for triage provider call failures."""


class RetryableTriageError(TriageProviderError):
    """Timeout, 429, or 5xx-equivalent failure — safe to retry once."""


class NonRetryableTriageError(TriageProviderError):
    """400-equivalent failure — retrying would fail identically."""


class TriageValidationError(TriageProviderError):
    """Raised when a provider's raw output doesn't fit TriageResult.

    Covers: the payload isn't valid JSON, isn't a JSON object, has a category
    or priority not in the domain enums, a summary over 140 chars, or a
    confidence outside [0, 1].
    """


def validate_triage_payload(raw: object) -> TriageResult:
    """Validate a provider's raw output against TriageResult.

    Accepts a dict, or a JSON string that decodes to one, so it works for
    providers that hand back parsed JSON or a raw response body.
    """
    if isinstance(raw, (str, bytes)):
        try:
            raw = json.loads(raw)
        except (json.JSONDecodeError, TypeError, UnicodeDecodeError) as exc:
            raise TriageValidationError(f"Triage payload is not valid JSON: {exc}") from exc

    if not isinstance(raw, dict):
        raise TriageValidationError(f"Triage payload must be a JSON object, got {type(raw).__name__}")

    try:
        return TriageResult.model_validate(raw)
    except ValidationError as exc:
        raise TriageValidationError(f"Triage payload failed validation: {exc}") from exc
