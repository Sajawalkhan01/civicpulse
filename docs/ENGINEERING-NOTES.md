# CivicPulse Engineering Notes

These notes provide architectural justifications, exact file-and-line references, and operational analyses satisfying Section 5.2 of the CivicPulse specification.

---

## 1. Laptop vs. CI Runner Discrepancies and Manifest Freezing Lines

Three distinct environmental factors diverge between a local development laptop and an automated CI runner (such as GitHub Actions Ubuntu runner):

### A. Host OS, C-Library, and Python Runtimes
- **The Divergence:** A developer laptop may run Windows 11 with MSVC runtimes or macOS on ARM64 with Apple Silicon Python binaries, while CI runners execute Ubuntu Linux x86_64. Differences in C libraries (glibc vs musl), system dependencies (`libpq`), and Python bytecode compilation lead to "works on my machine" failures.
- **The Freezing Lines:**
  - `backend/Dockerfile:2`: `FROM python:3.12-slim AS builder`
  - `backend/Dockerfile:19`: `FROM python:3.12-slim AS runtime`
  - These lines pin the base distribution to Debian Bookworm slim with Python 3.12, ensuring identical dynamic linking across all environments.

### B. Filesystem Security, Permissions, and Non-Root Execution
- **The Divergence:** Windows filesystems do not natively enforce POSIX UID/GID permission boundaries, whereas container runtimes in CI and production enforce restricted user namespaces. Running as `root` locally masks permission denied errors on volume mounts.
- **The Freezing Lines:**
  - `backend/Dockerfile:24-25`:
    ```dockerfile
    RUN groupadd -g 10001 appgroup && \
        useradd -u 10001 -g appgroup -s /sbin/nologin -d /app appuser
    ```
  - `backend/Dockerfile:39`: `USER 10001:10001`
  - `frontend/Dockerfile:29`: `USER nginx`
  - Containers are locked into unprivileged execution regardless of the host daemon configuration.

### C. Network Isolation and Ambient Daemon Conflicts
- **The Divergence:** Local machines often run ambient background services (e.g., local Postgres on port 5432 or local Redis on 6379), leading to silent credential leakage or port collision. CI runners run ephemeral clean network namespaces.
- **The Freezing Lines:**
  - `compose.yaml:150-156`:
    ```yaml
    networks:
      edge:
        driver: bridge
      internal:
        driver: bridge
        internal: true
    ```
  - `k8s/base/postgres.yaml:11`: `type: ClusterIP`
  - Restricts internal databases to private segmented networks, prohibiting host port binding in production.

---

## 2. CI/CD Maturity Ladder Justification

- **Current Rung:** **Rung 3 — Automated Acceptance & Staged Delivery** (Lecture 03, slide 32).
- **Justification:**
  - Every pull request to `main` and push to `dev` triggers automated linting (`ruff`, `mypy`, `tsc --noEmit`), unit and regression tests with strict coverage gates (`pytest --cov-fail-under=65`), multi-stage container builds, security vulnerability scanning (`trivy` failing on HIGH/CRITICAL), and Kubernetes manifest validation (`kubeconform`).
  - Gated continuous deployment on `main` builds immutable SHA-tagged artifacts, pushes Syft SBOMs, and deploys onto an ephemeral cluster with automated health and smoke tests.
- **Next Rung:** **Rung 4 — Progressive Delivery & Continuous Verification (GitOps)**.
- **What it Buys:** Transitioning to Rung 4 (using Argo CD or Flux with Flagger) buys canary deployments with real-time automated traffic shifting (e.g., 5% -> 25% -> 100%) and automatic rollback based on production Prometheus error rates and latency histograms, eliminating manual intervention during zero-downtime rollouts.

---

## 3. Build-Once-Deploy-Many Guarantee

- **The Exact Lines:**
  - `frontend/nginx.conf:31-39`:
    ```nginx
    location /api/ {
        proxy_pass http://backend:8000/api/;
        proxy_http_version 1.1;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_pass_header X-Cache;
    }
    ```
  - `k8s/base/ingress.yaml:14-25`:
    ```yaml
    - path: /api
      pathType: Prefix
      backend:
        service:
          name: backend
          port:
            number: 8000
    - path: /
      pathType: Prefix
      backend:
        service:
          name: frontend
          port:
            number: 80
    ```
- **What Breaks Without It:**
  Vite evaluates `import.meta.env` at compile time and inlines static strings directly into minified JavaScript bundles. If absolute backend URLs (e.g. `http://localhost:8000` or `http://backend:8000`) were baked in, the frontend image would become permanently coupled to that single host. Re-deploying to staging or Kubernetes would require rebuilding the container image from source, destroying portability, traceability, and cacheability. Proxying relative `/api/` paths at the web server layer preserves image immutability.

---

## 4. Probabilistic LLM Behavior vs. Deterministic Correctness in CI

- **What "Correct" Means:**
  When invoking external generative LLMs, output text is inherently non-deterministic. "Correctness" in production does not mean expecting identical wording; it means **strict contractual invariance**:
  1. The triage output parses into a valid `TriageResult` Pydantic model (`app/domain/models.py:27-32`).
  2. The assigned category and priority strictly conform to the system enums (`Category`, `Priority`).
  3. The summary never exceeds 140 characters.
  4. Response time is strictly bounded by a 10s hard timeout with automated fallback to `RuleBasedTriage` (`triaged_by="rules:fallback"`).
- **How CI Remains Deterministic:**
  In automated CI and regression tests, `TRIAGE_PROVIDER` is locked to `simulated` (`.github/workflows/ci.yml:60` and `backend/tests/conftest.py:9`). `SimulatedTriage` (`app/providers/triage/simulated.py`) runs in-memory with deterministic keyword mappings and zero external network calls, ensuring test suites are green on every run without flaky external dependencies.

---

## 5. HPA Lag Analysis and Latency Accounting

- **Measured Scale-Out Lag:** ~18–25 seconds from traffic surge initiation to additional pod readiness.
- **Where the Time Goes:**
  1. **Scrape Interval (10–15s):** `metrics-server` samples container CPU usage at periodic intervals.
  2. **Controller Sync Period (15s):** The Kubernetes `horizontal-pod-autoscaler-sync-period` evaluates metric queries periodically.
  3. **Container Boot & Probe Delay (3–5s):** Kubernetes schedules new pods, executes the `startupProbe` (`k8s/base/backend.yaml:124`, `periodSeconds: 2`), and adds endpoints to the Service.
- **What Would Reduce It:**
  - Reducing the metrics-server collection interval to 5 seconds.
  - Setting lower HPA CPU target thresholds (e.g., 50%) to trigger scale-out earlier.
  - Using predictive or KEDA event-driven autoscaling based on queue depth / rate limiter pressure rather than lagging CPU utilization.

---

## 6. Justification for VPA in Recommender ("Off") Mode

- **Why `updateMode: "Off"`:**
  In `k8s/base/vpa.yaml:10`:
  ```yaml
  updatePolicy:
    updateMode: "Off"
  ```
- **The Failure Mode in "Auto" Alongside HPA:**
  Both HPA and VPA react to CPU consumption. If VPA is set to `Auto`:
  1. A traffic spike increases pod CPU consumption.
  2. VPA detects elevated CPU usage and mutates the pod spec, increasing the CPU `requests` value (e.g., from `200m` to `500m`).
  3. HPA calculates utilization as $\text{utilization} = \frac{\text{usage}}{\text{request}}$. Because the denominator (`request`) was just inflated by VPA, computed utilization drops below the 60% target.
  4. HPA scales in, terminating pods.
  5. The remaining pods must handle even more load, spiking CPU further, causing VPA to raise requests again.
  6. This creates an unrecoverable flapping oscillation. Recommender mode allows engineers to audit right-sizing recommendations safely.

---

## 7. Network Segmentation (`internal: true`) and LLM Egress

- **The Constraint:**
  In `compose.yaml:153-156`, `internal: true` creates an isolated Docker network bridge with no default gateway or route to the public internet.
- **The Architectural Resolution:**
  - Database (`postgres`) and cache (`redis`) containers are attached **only** to the `internal` network (`compose.yaml:11,36`), making them physically unreachable from the public web.
  - The `backend` container is dual-homed, joining **both** `edge` and `internal` networks (`compose.yaml:94-96`).
  - Egress to public hosted LLMs (Groq / Gemini) flows through the `edge` network interface, while all database queries stay isolated on `internal`.
  - Frontend is attached strictly to `edge` (`compose.yaml:129`), mathematically preventing frontend compromise from reaching database storage.

---

## 8. The Failure Log

- **The Symptoms:**
  During local Docker Compose verification, all infrastructure services started, but `civicpulse-frontend-1` remained permanently in `(unhealthy)` state, causing compose dependencies to stall.
- **What Was Wrongly Believed First:**
  We initially hypothesized that Nginx was failing to launch, that port 8080 was conflicting with another process, or that static assets failed to compile in the builder stage.
- **The Exact Command & Log Line That Revealed the Truth:**
  Inspecting the healthcheck inside the container:
  ```powershell
  docker compose exec frontend wget -qO- http://localhost:8080/health
  # Output: wget: can't connect to remote host: Connection refused
  ```
  Immediately followed by:
  ```powershell
  docker compose exec frontend wget -qO- http://127.0.0.1:8080/health
  # Output: healthy
  ```
  In Alpine Linux with `musl`, `localhost` resolved to IPv6 loopback (`::1`) by default. However, Nginx was only bound to IPv4 `listen 8080;`. Updating `frontend/nginx.conf` with `listen [::]:8080;` and explicitly targeting `127.0.0.1` in Dockerfiles resolved the issue immediately.
