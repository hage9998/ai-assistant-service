---
name: deploy-dev
description: Deploy this service to the dev Kubernetes namespace via Kustomize. Use when the user asks to deploy, redeploy, or apply k8s manifests to dev.
disable-model-invocation: true
---

Deploy the `ai-assistant-service` to the `life-gamefication-dev` namespace on **minikube**, using Kustomize.

Both `k8s/base/deployment.yaml` containers use `imagePullPolicy: Never`, so the image must be built directly into minikube's Docker daemon — a registry push is not part of this workflow.

1. Point the local Docker CLI at minikube's daemon: `eval $(minikube docker-env)`
2. Build the image with the tag the manifests expect: `docker build -t ai-assistant-api:latest .` (the initContainer also references `ai-assistant-api:latest`; the main container uses `ai-assistant-api:1.0.0` — check `k8s/base/deployment.yaml` for the exact tag currently referenced and build that one, or confirm with the user if it's unclear)
3. Apply the namespace first if it may not exist yet: `kubectl apply -f k8s/base/namespace.yaml`
4. Apply the dev overlay: `kubectl apply -k k8s/overlays/dev/`
5. Verify: `kubectl get all -n life-gamefication-dev`

If pods are stuck in `ImagePullBackOff`, it almost always means step 1 was skipped and the image was built into the host Docker daemon instead of minikube's.

If the user wants staging or prod instead, swap `overlays/dev/` for `overlays/staging/` or `overlays/prod/` — but confirm with the user before applying to either, since those are shared/higher-risk environments.

Reference: `k8s/README.md` (in Portuguese) documents the full manifest structure.
