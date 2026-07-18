# K8s Observability AI Agent

Python FastAPI service that routes observability questions through tool adapters (Prometheus, Kubernetes, logs/alerts/kb stubs) and an LLM stub.

## Quickstart
- Install deps: `python -m venv .venv && source .venv/bin/activate && pip install -r requirements.txt`
- Configure env: `cp .env.example .env` then set `GEMINI_API_KEY` and any URLs for Prometheus/Loki/Alertmanager.
- Run dev server: `uvicorn app:app --reload`
- Sample request:
  ```bash
  curl -X POST http://127.0.0.1:8000/chat \
    -H "Content-Type: application/json" \
    -d '{"question":"Why are pods restarting?","namespace":"default","service":"demo"}'
  ```

## Configuration
Environment variables:
- `PROMETHEUS_BASE_URL`, `LOKI_BASE_URL`, `ALERTMANAGER_URL`
- `GEMINI_MODEL`, `GEMINI_API_KEY`
- `KUBE_CONTEXT`, `REQUEST_TIMEOUT_SECONDS`, `LOG_LEVEL`

Kubernetes client: auto-detects in-cluster config, falls back to local kubeconfig if available.

## Status
- Prometheus and Kubernetes adapters read-only; logs/alerts/kb are stubs with structured responses.
- LLM call is stubbed but preserves response shape (summary + sections).
