# CivicPulse — CLAUDE.md

Short, load-bearing engineering rules. Paste this file at the start of every session.

## Backend layering (strict, one direction)

`routes → services → repositories/providers`

- **routes/**: HTTP only — parse requests, validate shape, set status codes. No business logic, no SQL, no direct provider calls.
- **services/**: business logic and orchestration. Call repositories/providers. Never called *by* repositories/providers.
- **repositories/**: all SQL/DB access lives here and nowhere else. No SQL outside this layer.
- **providers/** (e.g. `providers/triage/`): all external API calls (LLM, etc.) live here and nowhere else.
- Dependencies point one way only. A lower layer never imports a higher layer.

## State machine

Report status is a single, enforced state machine. Status is never mutated directly from a route or repository — every transition goes through one service function that validates the current state before moving to the next.

Placeholder transitions below — update this section to match the actual assignment spec before relying on it:

```
NEW → TRIAGED → IN_PROGRESS → RESOLVED → CLOSED
NEW → REJECTED
TRIAGED → REJECTED
```

## Health check

`/health` must never touch the database, Redis, or any provider. It only confirms the process is up.

## Secrets

Never commit a real `.env` or API key. If you're about to write a real secret into a tracked file, stop and say so instead — use `.env.example` with placeholder values only.
