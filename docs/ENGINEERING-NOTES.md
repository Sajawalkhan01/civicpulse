# Engineering Notes

## Data layer

- `ix_complaints_status_priority` (composite index on `status, priority`) serves the filtered listing in `ComplaintRepository.list()`, which the admin queue view uses to pull complaints by `status` and/or `priority` (e.g. all `open` + `high` priority complaints) without a sequential scan.
- `ix_complaints_created_at` serves the `ORDER BY created_at DESC` clause in `ComplaintRepository.list()`, which paginates complaints newest-first by default.

## Cache layer

Redis is given a persistent volume with AOF enabled even though everything stored in it — triage results keyed by content hash, the 30s `/api/stats` snapshot — is, in principle, rebuildable from Postgres or by re-running triage. The reason isn't durability of the *data*; it's protecting the *system* it's rebuildable data would have to be rebuilt through. Triage results are the output of a rate-limited, sometimes-paid LLM call with real per-request latency; losing that cache on every container restart or redeploy means every complaint whose text was already triaged today gets re-triaged from scratch, silently converting a cache-miss cost (occasional) into a cache-miss cost (universal, right after every deploy) — exactly when traffic is also least tolerant of a latency spike. AOF turns "Redis restarted" back into "a warm cache came back warm" instead of "every one of today's dedupe wins was just erased." The rate limiter counters are the sharper case: without persistence, a pod restart resets every client's window to zero, so a restart timed by an attacker (or just bad luck during a rolling deploy) becomes a free way to bypass the rate limit entirely. AOF (append-only, fsync'd more often than an RDB snapshot) is worth the extra disk I/O over RDB-only specifically because both of these are short-TTL, high-churn keys where losing even the last few seconds of writes on a crash (not just a clean restart) reopens the same gap.
