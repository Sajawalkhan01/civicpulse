# ADR 0003: Deployment by Immutable Commit SHA and Digest References

## Status
Accepted

## Context
Deploying software using mutable container image tags (such as `:latest`, `:dev`, or branch names) introduces serious operational risks:
1. **Lack of Traceability:** An engineer cannot deterministically correlate a running container in production to an exact commit in git history. "What is production running?" requires inspecting registries rather than pasting a SHA into `git show`.
2. **Nondeterministic Rollouts & Pod Restarts:** If an image with tag `:latest` is overwritten in the container registry, new pods scheduled during a scale-out or node failure will run a different version than existing pods in the same Deployment.
3. **Unreliable Rollbacks:** Re-applying a manifest that references `:latest` does not roll back changes.

## Decision
We enforce deployment strictly by **immutable references**:

1. **Tagging by Commit SHA:** Every production image built in GitHub Actions (`cd.yml`) is tagged with the full git commit SHA (`${{ github.sha }}`) and its short SHA.
2. **Gated Publishing:** Images are only built and pushed to GitHub Container Registry (GHCR) after the full test suite passes (`needs: test`).
3. **Kustomize Image Injection:** Deployment manifests in `k8s/overlays/prod` use Kustomize image transformations to inject the exact commit SHA before applying:
   ```bash
   kustomize edit set image ghcr.io/sajawalkhan01/civicpulse-backend=ghcr.io/sajawalkhan01/civicpulse-backend:${{ github.sha }}
   ```
4. **SBOM & Digest Tracking:** Syft generates an SPDX Software Bill of Materials (SBOM) for the exact image SHA, and the immutable container image digest (`sha256:...`) is captured as a pipeline artifact.
5. **No Production `:latest` Deployments:** While `:latest` may be pushed to GHCR for convenience, production manifests and deployments are strictly prohibited from using `:latest`.

## Consequences
- **Positive:** Absolute auditability: any pod running in production maps 1-to-1 with a single git commit.
- **Positive:** Rollbacks can be executed with zero ambiguity either declaratively (re-applying the previous commit SHA manifest) or imperatively (`kubectl rollout undo`).
- **Negative:** Deployment pipelines must dynamically update image tags in deployment manifests via Kustomize before applying.
