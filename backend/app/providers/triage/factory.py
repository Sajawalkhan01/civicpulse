import os

from app.domain.protocols import TriageProvider
from app.providers.triage.llm import LLMTriage
from app.providers.triage.ollama import OllamaTriage
from app.providers.triage.rules import RuleBasedTriage
from app.providers.triage.simulated import SimulatedTriage

_KNOWN_PROVIDERS = {"rules", "simulated", "llm", "ollama"}


def get_triage_provider() -> TriageProvider:
    # Default to "simulated" if unset — never default to a live network call.
    provider_name = os.environ.get("TRIAGE_PROVIDER", "simulated").strip().lower()

    if provider_name == "rules":
        return RuleBasedTriage()
    if provider_name == "simulated":
        return SimulatedTriage()
    if provider_name == "llm":
        return LLMTriage()
    if provider_name == "ollama":
        return OllamaTriage()
    raise ValueError(
        f"Unknown TRIAGE_PROVIDER={provider_name!r}; expected one of {sorted(_KNOWN_PROVIDERS)}"
    )
