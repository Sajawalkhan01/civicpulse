import os

from app.domain.protocols import TriageProvider
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
    if provider_name in ("llm", "ollama"):
        raise NotImplementedError(
            f"TRIAGE_PROVIDER={provider_name!r} is not built yet in this chunk; "
            "only 'rules' and 'simulated' are available."
        )
    raise ValueError(
        f"Unknown TRIAGE_PROVIDER={provider_name!r}; expected one of {sorted(_KNOWN_PROVIDERS)}"
    )
