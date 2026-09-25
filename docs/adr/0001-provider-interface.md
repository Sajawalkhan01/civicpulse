# ADR 0001: Pluggable TriageProvider Interface and Resilient AI Layer

## Status
Accepted

## Context
Municipal complaint systems face a fundamental engineering challenge: while text categorization and triage are critical, the underlying classification mechanism must be easily replaceable over time (from deterministic keyword rules, to hosted LLMs like Groq/Gemini, to on-premise small models like Ollama). 

Furthermore, relying directly on external AI services introduces failure modes:
1. **Unpredictable Latency & Timeouts:** Third-party API calls can hang or slow down under load.
2. **Rate Limits & Outages:** Free-tier or enterprise API limits (HTTP 429) can exhaust worker pools and degrade user experience.
3. **Non-deterministic & Malformed Outputs:** Models may hallucinate, output conversational prose, or violate enum boundaries.
4. **Duplicate Costs:** Duplicate community complaints (e.g. 10 citizens reporting the same burst water pipe) cause repeated redundant API calls.

## Decision
We decouple the complaint ingestion workflow from AI providers by implementing a strict **Hexagonal / Adapter pattern**:

1. **Protocol-Driven Interface:** We define a `TriageProvider` protocol (`app/providers/triage/base.py`) returning a validated Pydantic model `TriageResult` (`category`, `priority`, `summary` <= 140 chars, `confidence` between 0.0 and 1.0).
2. **Four Concrete Implementations:**
   - `LLMTriage`: Uses Groq API (`openai/gpt-oss-20b`) with JSON mode and hard 10s timeouts.
   - `OllamaTriage`: Local self-hosted LLM (`llama3.2:1b`) container for air-gapped environments.
   - `RuleBasedTriage`: Deterministic keyword matching that never fails.
   - `SimulatedTriage`: Deterministic test double for CI and unit testing with configurable failure injection.
3. **Resilience & Fallback:** Calls to external LLMs are bounded by a 10s hard timeout, single jittered retry on 429/5xx errors, and automatic fallback to `RuleBasedTriage` with `triaged_by="rules:fallback"` recorded in the database.
4. **Content-Hash Caching:** Raw complaint text is hashed (SHA-256) and cached in Redis with a 24-hour TTL, preventing repeated inference for duplicate complaints.

## Consequences
- **Positive:** System never returns 500 when an LLM provider fails or is rate-limited; unit and CI tests remain 100% deterministic using `SimulatedTriage`.
- **Negative:** Additional complexity in maintaining provider adapters, Redis cache synchronization, and schema validation.
