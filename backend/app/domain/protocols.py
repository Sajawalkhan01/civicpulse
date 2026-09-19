from typing import Protocol

from .models import TriageResult


class TriageProvider(Protocol):
    name: str

    def triage(self, text: str, location: str) -> TriageResult: ...
