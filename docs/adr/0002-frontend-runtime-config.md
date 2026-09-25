# ADR 0002: Frontend Runtime Configuration and Build-Once-Deploy-Many

## Status
Accepted

## Context
In modern single-page application (SPA) toolchains like Vite, environment variables prefixed with `VITE_` or accessed via `import.meta.env` are statically evaluated and inlined into JavaScript bundles at build time. 

If backend API URLs (e.g. `http://localhost:8000` or `http://backend.internal`) are hardcoded or baked into the bundle at build time:
1. The resulting container image becomes environment-specific.
2. A separate Docker build would be required for localhost development, CI integration testing, staging, and production Kubernetes clusters.
3. This completely violates the foundational **"Build-Once-Deploy-Many"** principle of cloud-native engineering.

## Decision
We mandate that the React frontend code contains **zero hardcoded absolute API URLs or hostnames**. All API calls use relative paths starting with `/api/` (e.g., `fetch('/api/complaints')`).

At runtime:
1. **In Production & Docker Compose:** The frontend is served by an unprivileged Nginx reverse proxy (`nginx.conf`). Nginx intercepts `/api/` requests and forwards them internally to the backend service:
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
2. **In Kubernetes:** The Traefik / Nginx Ingress Controller routes `/` to the frontend service and `/api` to the backend service under the same host.
3. **In Local Vite Dev:** Vite dev server uses a proxy config in `vite.config.ts` pointing to `http://localhost:8000`.

## Consequences
- **Positive:** Exactly one immutable frontend Docker image (`civicpulse-frontend:${IMAGE_TAG}`) is built in CI, scanned for vulnerabilities, and deployed identically across Docker Compose, test clusters, and production Kubernetes.
- **Positive:** CORS issues in production are completely eliminated because frontend assets and `/api` share the same origin.
- **Negative:** Requires maintaining the Nginx proxy configuration and ensuring headers like `X-Cache` are passed through.
