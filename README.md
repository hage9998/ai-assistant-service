# AI Assistant Service

> **Note:** This service is part of the **Life Gamefication Project**, a personal project built for **learning and studying purposes**. The goal is to practice backend architecture, clean code principles, and modern Python tooling in a realistic setting rather than to serve as a production-ready product.

## Overview

The AI Assistant Service is a FastAPI microservice responsible for generating short, motivational "advice" messages for users of the Life Gamefication platform. Each piece of advice is produced by an LLM (via [Ollama](https://ollama.com/) + [LangChain](https://www.langchain.com/)) in a medieval/mythical tone, meant to encourage the user's real-life journey of habits, goals, and missions.

## Architecture

The codebase follows a **Clean Architecture** style, separating concerns into independent layers:

```
app/
├── domain/            # Enterprise-wide business rules: entities, repository
│                       # interfaces, and domain exceptions. No framework deps.
├── application/        # Use cases (application-specific business rules) and
│                       # DTOs that orchestrate the domain layer.
├── infrastructure/      # Concrete implementations: database (SQLAlchemy),
│                       # LLM provider (Ollama/LangChain), settings, security (JWT).
└── presentation/        # FastAPI layer: routes, request/response schemas,
                        # and dependency injection wiring.
```

This keeps the domain and application logic independent of frameworks and external services, making it easier to swap infrastructure pieces (e.g., changing the LLM provider or the database) without touching business rules.

### Key components

- **Domain**: `AdviceLog`, `Message`/`MessageRole` entities and the `AdviceLogRepository` interface.
- **Application**: `GenerateAdviceUseCase`, which builds the prompt, calls the `LLMProvider`, persists an `AdviceLog`, and returns the result.
- **Infrastructure**: `OllamaProvider` (LangChain `ChatOllama` chain), SQLAlchemy session/models, JWT decoding.
- **Presentation**: `/api/v1/advice` routes, Pydantic schemas, and FastAPI dependency providers.

## Tech Stack

- [FastAPI](https://fastapi.tiangolo.com/) — web framework
- [SQLAlchemy](https://www.sqlalchemy.org/) + [Alembic](https://alembic.sqlalchemy.org/) — ORM and database migrations
- [LangChain](https://www.langchain.com/) + [Ollama](https://ollama.com/) — LLM orchestration and local model serving
- [Pydantic](https://docs.pydantic.dev/) / `pydantic-settings` — schemas and configuration
- [python-jose](https://github.com/mpdavis/python-jose) — JWT validation
- [Uvicorn](https://www.uvicorn.org/) — ASGI server

## Getting Started

### Prerequisites

- Python 3.12+
- A running PostgreSQL instance
- [Ollama](https://ollama.com/) running locally with the desired model pulled (e.g. `ollama pull llama3.1`)

### Setup

```bash
# Create and activate a virtual environment
python -m venv .venv
source .venv/bin/activate

# Install dependencies
pip install -r requirements.txt

# Copy the example environment file and adjust values as needed
cp .env.example .env
```

### Environment variables

| Variable | Description | Default |
|---|---|---|
| `APP_NAME` | Application name | `gamification-llm-service` |
| `ENVIRONMENT` | Runtime environment | `development` |
| `DEBUG` | Enable debug mode | `true` |
| `DATABASE_URL` | PostgreSQL connection string (async) | `postgresql+asyncpg://postgres:postgres@localhost:5432/gamification_llm` |
| `DATABASE_ECHO` | Log SQL statements | `false` |
| `JWT_SECRET` | Secret used to validate JWTs | — |
| `JWT_ALGORITHM` | JWT signing algorithm | `HS256` |
| `OLLAMA_BASE_URL` | Ollama server URL | `http://localhost:11434` |
| `OLLAMA_MODEL` | Model used for generation | `llama3.1` |
| `LLM_TEMPERATURE` | Sampling temperature | `0.7` |
| `LOG_LEVEL` | Logging level | `INFO` |

### Running database migrations

```bash
alembic upgrade head
```

### Running the service

```bash
uvicorn app.main:app --reload
```

The interactive API docs will be available at `http://localhost:8000/docs`.

## API

### `GET /advice/daily`

Returns a short (3-4 sentence) medieval/mythical piece of advice to motivate the authenticated user. Intended to be called whenever the user enters the application's main screen. Requires a valid JWT bearer token.

## Deployment

Kubernetes manifests (base + environment overlays for `dev`, `staging`, and `prod`) are available under [`k8s/`](./k8s), managed with [Kustomize](https://kustomize.io/). See [`k8s/README.md`](./k8s/README.md) for deployment instructions.

## Project Context

This service is one of several microservices that make up the **Life Gamefication Project**, a hobby project used to explore backend engineering concepts such as clean architecture, dependency injection, LLM integration, and Kubernetes deployments.
