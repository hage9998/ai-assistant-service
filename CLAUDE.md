# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project overview

FastAPI microservice (part of a polyglot system alongside a NestJS backend) that generates short motivational "advice" messages in a medieval/mythical tone via a local LLM. Learning/personal project, not production-hardened.

## Architecture

Clean Architecture, strictly layered under `app/`:

```
domain/          entities, repository interfaces, domain exceptions — no framework deps
application/     DTOs, use cases, interfaces (e.g. LLMProvider) — orchestrates domain logic
infrastructure/  concrete implementations: SQLAlchemy ORM/repos, Ollama/LangChain provider,
                 JWT handling, pydantic-settings config, async DB session
presentation/    FastAPI routers, request/response schemas, DI wiring (dependencies/)
```

Router pattern: each feature exposes its own `APIRouter` (e.g. `presentation/api/v1/advice_routes.py`). Versioned routers are aggregated in `presentation/api/v1/__init__.py` into `api_v1_router` (prefix `/api/v1`), which `app/main.py`'s `create_app()` mounts via `app.include_router(...)`. Follow this pattern for new endpoints rather than mounting routers directly on `app`.

## Setup

```bash
python -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

Requires: Python 3.12+, a running PostgreSQL, and Ollama running locally with a model pulled (`ollama pull llama3.1`).

Dependencies are managed via pip-tools: edit `requirements.in`, then run `pip-compile --output-file=requirements.txt requirements.in` (do not hand-edit `requirements.txt`).

## Running

- Dev server: `uvicorn app.main:app --reload` (docs at `http://localhost:8000/docs`)
- Migrations: `alembic upgrade head`
- New migration: `alembic revision --autogenerate -m "description"`

## Deployment (local)

Deployed locally to **minikube**, not a remote cluster. `k8s/base/deployment.yaml` uses `imagePullPolicy: Never` on both containers, so images must be built directly into minikube's Docker daemon: `eval $(minikube docker-env)` then `docker build -t ai-assistant-api:latest .` before applying manifests. See the `/deploy-dev` skill for the full workflow.

Migrations run automatically as a Kubernetes initContainer before the app container starts — schema changes always go through Alembic, never auto-create.

## LLM integration

Uses **Ollama** via **LangChain** (`ChatOllama`), not OpenAI/Anthropic — see `app/infrastructure/llm/`. Model, temperature, and base URL are configured via `OLLAMA_MODEL`, `LLM_TEMPERATURE`, `OLLAMA_BASE_URL` env vars. The system prompt in `app/application/use_cases/generate_advice.py` is written in Portuguese and enforces a strict medieval-oracle persona (max 3-4 sentences, no markdown, epic tone).

## Auth

JWT via `python-jose` (`app/infrastructure/security/jwt_handler.py`), expecting `sub`, `email`, and optional `name` claims. `JWT_SECRET` must match the secret used by the separate NestJS backend in this system — it's shared across services, not service-local.

## Commit style

Conventional Commits, short and lowercase, no scopes: `feat:`, `fix:`, `chore:`, and **`refac:`** (not `refactor:` — this repo's deviation from the standard prefix).

Commit incrementally: make a commit between logically distinct changes rather than batching everything into one commit at the end of a task.

Do not add a `Co-Authored-By: Claude` trailer (or similar) to commit messages in this repo.

## Testing and linting

No test suite, linter, or formatter is currently configured in this repo.

## Development Process

Always use the SDD workflow for new features.

The SDD skill is the primary orchestrator.

It may invoke the following skills during development:

- Architecture
- Planner
- Coder
- Reviewer

Architecture is optional and must always be confirmed with the user.