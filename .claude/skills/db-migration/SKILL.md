---
name: db-migration
description: Create or apply Alembic database migrations for this service. Use when the user asks to add a migration, generate a migration for a model change, or apply pending migrations.
disable-model-invocation: true
---

This service uses Alembic for schema migrations against the async SQLAlchemy models in `app/infrastructure/orm/models.py`.

**Creating a new migration** (after changing ORM models):
1. Ensure a local Postgres matching `DATABASE_URL` in `.env` is reachable — autogenerate compares against the live DB.
2. `alembic revision --autogenerate -m "<short description>"`
3. Open the generated file under `alembic/versions/` and check the diff actually matches the intended model change — autogenerate can miss things like column type changes or index-only tweaks.

**Applying migrations:**
`alembic upgrade head`

Note: in the deployed environment, migrations run automatically as a Kubernetes initContainer before the app container starts (see `k8s/base/deployment.yaml`) — don't rely on the app auto-creating tables.
