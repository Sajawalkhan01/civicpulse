# AI Usage Attribution

In accordance with Section 5.5 of the CivicPulse course policy, this document provides an honest, transparent record of how AI assistance was leveraged in the architecture, implementation, and debugging of this system.

---

## 1. Tools Used
- **Claude 3.7 Sonnet & Gemini 2.5 Pro (via Antigravity IDE / Cursor):** Used as an interactive pair programmer for scaffolding, test writing, Kubernetes manifest formulation, and CI/CD workflow drafting.

---

## 2. Parts Shaped or Scaffolding Authored by AI

### A. Kubernetes Manifests & Kustomize Structure
- **What AI Generated:** The initial boilerplate for `k8s/base/` and overlays, including the StatefulSet volume claim templates, HPA v2 definitions, and Traefik ingress paths.
- **What We Changed & Why:**
  - Added `imagePullPolicy: IfNotPresent` across `backend.yaml` and `frontend.yaml` because local `k3d image import` avoids failing out-of-band GHCR registry pulls.
  - Corrected the VPA CRD definition and tuned the `hpa.yaml` metrics average utilization target to exactly match the 60% requirement specified in §3.3.

### B. CI/CD Workflows (`.github/workflows/`)
- **What AI Generated:** Drafts of `ci.yml`, `cd.yml`, and `release.yml`.
- **What We Changed & Why:**
  - Resolved a YAML parser syntax error with `sqlite:///:memory:` by properly quoting connection strings in GitHub Actions `env` blocks.
  - Configured `PYTHONPATH: "backend"` and patched `conftest.py` with `sys.path.insert` because the CI runner's isolated pytest execution failed to resolve `app.*` imports when invoked from the repository root.

### C. Docker Healthchecks and Nginx IPv6 Binding
- **What AI Generated:** Initial multi-stage Dockerfiles for backend and frontend.
- **What We Changed & Why:**
  - Diagnosed that Alpine Linux (`musl`) resolves `localhost` to IPv6 `::1`, while unprivileged Nginx originally listened on IPv4 only. We patched `frontend/nginx.conf` with `listen [::]:8080;` and explicitly referenced `127.0.0.1` in the healthcheck definitions.

---

## 3. Team Member Contributions and Verification
- Every generated component was tested locally in Docker Compose and on a local `k3d` cluster before committing.
- All team members participated in live reviews, load testing with k6, and architecture validation to ensure full defense during oral examination (viva).
