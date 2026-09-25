import os

import httpx

from app.domain.models import TriageResult
from app.providers.triage.base import (
    TRIAGE_SYSTEM_PROMPT,
    NonRetryableTriageError,
    RetryableTriageError,
    TriageValidationError,
    build_triage_user_prompt,
    validate_triage_payload,
)

_DEFAULT_BASE_URL = "http://ollama:11434"
_DEFAULT_MODEL = "llama3.2:1b"
_DEFAULT_TIMEOUT_SECONDS = 8.0


class OllamaTriage:
    """Live triage provider calling a local/self-hosted Ollama chat endpoint.

    Unreachable-by-default is the expected state until Ollama is actually
    running: connection failures and timeouts are mapped to
    RetryableTriageError so the caller's existing retry-then-fallback logic
    handles them the same as any other provider outage.
    """

    name = "llm:ollama"

    def __init__(
        self,
        base_url: str | None = None,
        model: str | None = None,
        timeout_seconds: float = _DEFAULT_TIMEOUT_SECONDS,
    ) -> None:
        self._base_url = (
            base_url or os.environ.get("OLLAMA_BASE_URL") or _DEFAULT_BASE_URL
        ).rstrip("/")
        self._model = model or os.environ.get("OLLAMA_MODEL") or _DEFAULT_MODEL
        self._timeout_seconds = timeout_seconds

    def triage(self, text: str, location: str) -> TriageResult:
        payload = {
            "model": self._model,
            "format": "json",
            "stream": False,
            "messages": [
                {"role": "system", "content": TRIAGE_SYSTEM_PROMPT},
                {"role": "user", "content": build_triage_user_prompt(text, location)},
            ],
        }

        try:
            response = httpx.post(
                f"{self._base_url}/api/chat",
                json=payload,
                timeout=self._timeout_seconds,
            )
            response.raise_for_status()
        except (httpx.ConnectError, httpx.TimeoutException) as exc:
            raise RetryableTriageError(
                f"Ollama unreachable: {type(exc).__name__}"
            ) from exc
        except httpx.HTTPStatusError as exc:
            status_code = exc.response.status_code
            if status_code >= 500:
                raise RetryableTriageError(f"Ollama returned {status_code}") from exc
            raise NonRetryableTriageError(f"Ollama returned {status_code}") from exc
        except httpx.HTTPError as exc:
            raise RetryableTriageError(
                f"Ollama request failed: {type(exc).__name__}"
            ) from exc

        try:
            body = response.json()
        except ValueError as exc:
            raise TriageValidationError(
                f"Ollama response was not valid JSON: {exc}"
            ) from exc

        content = (body.get("message") or {}).get("content")
        if not content:
            raise TriageValidationError("Ollama response had no message content")

        return validate_triage_payload(content)
