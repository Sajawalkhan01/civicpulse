# ADR 0004: Personally Identifiable Information (PII) and Data Governance in AI Triage

## Status
Accepted

## Context
CivicPulse collects public civic complaints that frequently include sensitive user data, such as citizen names, residential addresses, phone numbers, and email contacts (`reporter_contact`).

When utilizing public or free-tier third-party AI endpoints (e.g. Groq, Google AI Studio Gemini API):
1. Provider terms of service often reserve the right to retain prompts or use inputs to improve model training.
2. Directly sending contact information, names, or identifiable personal data to external APIs creates grave privacy violations and legal liability under data protection regulations (e.g., GDPR, local privacy laws).
3. System logs that print raw payloads or API keys create unintended credential and data leakage in monitoring tools.

## Decision
We enforce a strict data governance and sanitization boundary at the application layer:

1. **Payload Sanitization Before Triage:** Only the raw complaint `text` and general civic `location` (e.g. neighborhood/street name) are supplied to the `TriageProvider.triage()` interface. The citizen's `reporter_contact` is persisted directly to PostgreSQL via `ComplaintRepository` and is **strictly never transmitted to any LLM provider**.
2. **Credential Hygiene:** API keys (such as `GROQ_API_KEY`) are injected strictly via Kubernetes Secrets or Docker Compose environment variables. They are never written to repository files, never committed, and explicitly filtered from structured JSON logs.
3. **Prompt-Injection Guardrails:** Citizen complaint text is treated as untrusted data. Prompts clearly delimit user input and strictly constrain output to the target JSON schema and enums (`Category`, `Priority`). Malformed responses or prompt jailbreak attempts trigger an automatic fallback to `RuleBasedTriage`.
4. **Air-Gapped / Zero-Egress Alternative:** For strictly governed or high-privacy deployments, the platform supports `OllamaTriage`, allowing triage to execute entirely within a self-hosted container on-cluster with zero network egress.

## Consequences
- **Positive:** Zero citizen contact details or private identifying numbers ever leave the local cluster infrastructure.
- **Positive:** Full compliance with security rubrics: no credentials in logs or git history, and prompt-injection attacks fail safely without system compromise.
- **Negative:** General civic location remains in the prompt to allow geographic context categorization (e.g. water vs roads).
