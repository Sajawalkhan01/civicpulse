# CivicPulse Operations Runbook

This runbook provides actionable procedures for deploying, maintaining, monitoring, and troubleshooting CivicPulse in development and production environments.

---

## 1. How to Deploy

### Local Development (Docker Compose)
1. **Initialize configuration:**
   ```powershell
   Copy-Item .env.example .env
   ```
2. **Build and start services:**
   ```powershell
   docker compose up --build -d
   ```
3. **Verify service health:**
   ```powershell
   docker compose ps
   ```
   All 5 containers (`postgres`, `redis`, `ollama`, `backend`, `frontend`) must report `(healthy)`.
4. **Access the application:**
   - Web UI: `http://localhost:3000`
   - API Docs: `http://localhost:8000/docs`

### Kubernetes Deployment (Local k3d or Production Cluster)
1. **Create or connect to cluster:**
   ```powershell
   k3d cluster create civicpulse --port "8081:80@loadbalancer"
   ```
2. **Deploy via Kustomize:**
   ```powershell
   # Development overlay
   kubectl apply -k k8s/overlays/dev

   # Or Production overlay with immutable SHA
   kubectl apply -k k8s/overlays/prod
   ```
3. **Track rollout status:**
   ```powershell
   kubectl rollout status deployment/backend -n civicpulse
   kubectl rollout status deployment/frontend -n civicpulse
   kubectl rollout status statefulset/postgres -n civicpulse
   ```

---

## 2. How to Roll Back

CivicPulse supports two distinct rollback mechanisms:

### A. Fast Imperative Rollback (The 3:00 AM Response)
When a newly deployed image introduces critical defects, roll back the backend immediately to the previous revision:
```bash
kubectl rollout undo deployment/backend -n civicpulse
kubectl rollout undo deployment/frontend -n civicpulse
```
Verify the active revision:
```bash
kubectl rollout status deployment/backend -n civicpulse
kubectl rollout history deployment/backend -n civicpulse
```

### B. Declarative Auditable Rollback (The Post-Incident Clean State)
Once the immediate fire is extinguished, update the production manifest to re-pin the previous known-good commit SHA and re-apply:
```bash
cd k8s/overlays/prod
kustomize edit set image ghcr.io/sajawalkhan01/civicpulse-backend=ghcr.io/sajawalkhan01/civicpulse-backend:<PREVIOUS_GIT_SHA>
kubectl apply -k .
git commit -am "fix: rollback backend to commit <PREVIOUS_GIT_SHA>"
git push origin main
```

---

## 3. Reading and Querying Structured Logs

All backend logs are emitted in **structured JSON format to stdout** (per 12-factor application design). Every log event carries an `x-request-id` correlated across request lifecycles.

### Docker Compose Logs
```powershell
# Follow backend logs
docker compose logs -f backend

# Search for triage fallback events
docker compose logs backend | Select-String "rules:fallback"

# Search by request ID
docker compose logs backend | Select-String "14cb1bc8-e552-400a"
```

### Kubernetes Pod Logs
```bash
# Stream live logs from all backend pods
kubectl logs -n civicpulse -l app=backend -f --tail=100

# Filter for warnings and errors using jq
kubectl logs -n civicpulse -l app=backend --tail=500 | jq 'select(.level=="WARNING" or .level=="ERROR")'
```

---

## 4. Troubleshooting Triage Failures

If external LLM triage providers experience degraded performance or total failure:

### A. Observability Surface (`/api/meta/providers`)
Query the metadata endpoint to inspect the last 20 triage outcomes, latencies, and fallback statuses:
```bash
curl -s http://localhost:8000/api/meta/providers | jq .
```
- If `fallback_rate` spikes towards 1.0, the primary LLM is timing out or encountering HTTP 429 rate limits.
- If latency exceeds 8000ms, external providers are experiencing throttling.

### B. Prometheus Metrics
Inspect live metrics for error and fallback counters:
```bash
curl -s http://localhost:8000/metrics | grep civicpulse_triage_
```

### C. Emergency Provider Switch (Zero-Downtime)
To immediately stop calling an upstream failing provider and switch to local Ollama or deterministic keyword rules:
1. Update `k8s/base/configmap.yaml` or edit the live ConfigMap:
   ```bash
   kubectl create configmap civicpulse-config -n civicpulse \
     --from-literal=TRIAGE_PROVIDER=rules \
     --dry-run=client -o yaml | kubectl apply -f -
   ```
2. Trigger a rolling restart to pick up the new configuration:
   ```bash
   kubectl rollout restart deployment/backend -n civicpulse
   ```
   The backend will now triage all incoming requests with instantaneous keyword matching and zero external network calls.
