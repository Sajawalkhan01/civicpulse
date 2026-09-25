import os

from openai import (
    APIConnectionError,
    APIStatusError,
    APITimeoutError,
    OpenAI,
    RateLimitError,
)

from app.domain.models import TriageResult
from app.providers.triage.base import (
    TRIAGE_SYSTEM_PROMPT,
    NonRetryableTriageError,
    RetryableTriageError,
    TriageValidationError,
    build_triage_user_prompt,
    validate_triage_payload,
)

_GROQ_BASE_URL = "https://api.groq.com/openai/v1"
_DEFAULT_MODEL = "openai/gpt-oss-20b"
_DEFAULT_TIMEOUT_SECONDS = 8.0


class LLMTriage:
    """Live triage provider calling Groq's OpenAI-compatible chat completions API.

    The API key is read from GROQ_API_KEY at construction time and never logged
    or included in any error message — only the exception class/status code is
    surfaced to callers.
    """

    name = "llm:groq"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        api_key = api_key if api_key is not None else os.environ.get("GROQ_API_KEY")
        if not api_key:
            raise NonRetryableTriageError("GROQ_API_KEY is not set")

        self._model = model or os.environ.get("GROQ_MODEL") or _DEFAULT_MODEL
        self._client = OpenAI(
            api_key=api_key, base_url=_GROQ_BASE_URL, timeout=timeout_seconds
        )

    def triage(self, text: str, location: str) -> TriageResult:
        try:
            response = self._client.chat.completions.create(
                model=self._model,
                response_format={"type": "json_object"},
                messages=[
                    {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                    {
                        "role": "user",
                        "content": build_triage_user_prompt(text, location),
                    },
                ],
            )
        except (APITimeoutError, APIConnectionError, RateLimitError) as exc:
            raise RetryableTriageError(
                f"Groq request failed: {type(exc).__name__}"
            ) from exc
        except APIStatusError as exc:
            if exc.status_code >= 500:
                raise RetryableTriageError(f"Groq returned {exc.status_code}") from exc
            raise NonRetryableTriageError(f"Groq returned {exc.status_code}") from exc

        content = response.choices[0].message.content if response.choices else None
        if not content:
            raise TriageValidationError("Groq response had no message content")

        return validate_triage_payload(content)
