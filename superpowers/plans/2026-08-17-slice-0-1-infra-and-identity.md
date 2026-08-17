# Slice 0 + 1 — Infrastructure and Identity Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Get a database that migrates, infrastructure that runs, and a user who can sign in — magic link, Google, or Apple — with a personal workspace, a rotating session, and no way to enumerate accounts.

**Architecture:** Slice 0 creates `faue-infra` and the initial Alembic revision, so anything can touch a database at all. Slice 1 builds `gateway.identity` end to end. Email delivery is **Resend**, behind an `EmailSender` protocol so tests never make a network call and local development never sends a real message.

**Tech Stack:** Python 3.12, FastAPI, SQLAlchemy 2.0 async, Alembic, PostgreSQL 16 + pgvector, Redis, pytest + testcontainers, PyJWT, Resend (transactional email).

**Spec:** `docs/superpowers/specs/2026-08-17-faue-platform-architecture-design.md`

## Global Constraints

- Every user-owned table carries `workspace_id UUID NOT NULL` ([ADR 0021](../../80-adr/0021-workspace-tenancy-model.md)). The personal workspace is created in the **same transaction** as the user.
- Migrations are **expand-only** in the release that adds them. Contraction happens in a later release.
- Magic-link tokens: 32 random bytes, stored **only** as SHA-256, 10-minute TTL, single-use, one active per identifier, consumed **over POST only**.
- Never a JWT in a URL. The magic-link token is opaque and meaningless outside the server.
- `POST /v1/auth/link/request` always returns `202`, whether or not the address exists. Account enumeration is a vulnerability, not a UX detail.
- Account linking occurs **only** on a verified email match. Unverified auto-linking is forbidden.
- Refresh tokens rotate on every use. Presenting a rotated token revokes the whole family.
- Apple's `full_name` arrives **only on first authorization** — persist it immediately or lose it permanently.
- No PII in logs, ever. `user_id` and `trace_id` only.
- Modules raise domain exceptions from `faue_core.errors`, never `HTTPException`.
- Endpoint paths and response shapes must match `docs/30-contracts/openapi/gateway.v1.yaml` exactly.

## Verification standard (every task)

1. Tests fail before the implementation, pass after.
2. `pytest -q` green in the touched repo.
3. No PII in any log statement added.
4. Response shapes validated against the OpenAPI contract where an endpoint is touched.

---

## File structure

**New — `faue-infra/`**

| File | Responsibility |
|---|---|
| `compose.yaml` | Infra-only profile: Postgres+pgvector, Redis, RabbitMQ, MinIO. Never runs application code |
| `sql/00-roles.sql` | Per-service roles and grants; cross-schema access fails at the database |
| `.github/workflows/python-service.yml` | Reusable CI: lint, typecheck, test |
| `.github/workflows/faue-db.yml` | Migration gates: upgrade, `alembic check`, down/up |
| `README.md` | How to run infra, what deliberately is not in it |

**Modified — `faue-db/`**

| File | Responsibility |
|---|---|
| `migrations/versions/0001_initial.py` | Schemas, extension, every MVP table, HNSW indexes in raw SQL |
| `tests/test_migrations.py` | Applies against a real Postgres; asserts round-trip |

**New — `api-gateway/app/modules/identity/`**

| File | Responsibility |
|---|---|
| `tokens.py` | Access JWT issue/verify, refresh rotation, family revocation |
| `magic_link.py` | Token mint, store, atomic consume, device-code fallback |
| `email_sender.py` | `EmailSender` protocol + `RecordingEmailSender` + provider adapter |
| `oidc_google.py` | Google ID-token verification against JWKS |
| `oidc_apple.py` | Apple identity-token verification, client-secret generation |
| `linking.py` | Verified-email linking rules |
| `service.py` | `IdentityService` — the interface other modules depend on |
| `workspace.py` | Personal workspace bootstrap |

---

# SLICE 0 — Infrastructure

## Task 1: faue-infra with a working local stack

**Files:**
- Create: `faue-infra/compose.yaml`, `faue-infra/scripts/provision-local.sh`, `faue-infra/README.md`, `faue-infra/.gitignore`

> **No checked-in `.sql` files.** Schema, indexes and grants all live in Alembic
> migrations — one source of truth. The only thing outside Alembic is cluster-level
> provisioning (roles, databases, the `vector` extension), because those need
> superuser and cannot be part of a migration run by an unprivileged migrator.

**Interfaces:**
- Produces: Postgres on `5432` with `pgvector`, Redis on `6379`, RabbitMQ on `5672`/`15672`, MinIO on `9000`/`9001`. Database `faue`, superuser `faue`/`faue_local_dev`.

- [ ] **Step 1: Write `compose.yaml`**

```yaml
# Infrastructure only. Services run under uvicorn on the host — a full container
# stack is a poor trade for the fidelity it buys on a development machine.
name: faue-infra

services:
  postgres:
    image: pgvector/pgvector:pg16
    environment:
      POSTGRES_USER: faue
      POSTGRES_PASSWORD: faue_local_dev
      POSTGRES_DB: faue
    ports: ["5432:5432"]
    volumes:
      - pgdata:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U faue -d faue"]
      interval: 5s
      timeout: 5s
      retries: 10

  redis:
    image: redis:7-alpine
    ports: ["6379:6379"]
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 5s
      retries: 10

  rabbitmq:
    image: rabbitmq:3-management-alpine
    ports: ["5672:5672", "15672:15672"]
    healthcheck:
      test: ["CMD", "rabbitmq-diagnostics", "-q", "ping"]
      interval: 10s
      retries: 10

  minio:
    image: minio/minio
    command: server /data --console-address ":9001"
    environment:
      MINIO_ROOT_USER: faue
      MINIO_ROOT_PASSWORD: faue_local_dev
    ports: ["9000:9000", "9001:9001"]

volumes:
  pgdata:
```

- [ ] **Step 2: Write `scripts/provision-local.sh`**

Cluster-level setup only. Everything schema-shaped belongs in Alembic.

```bash
#!/usr/bin/env bash
# One-time local provisioning: roles, databases, and the pgvector extension.
#
# These need superuser and are NOT part of any migration — the migrator role is
# deliberately unprivileged. Schema, indexes and grants live in Alembic.
#
# Safe to re-run.
set -euo pipefail

SUPER="${SUPERUSER_DB:-postgres}"
PW="${LOCAL_DB_PASSWORD:-faue_local_dev}"

psql -d "$SUPER" -v ON_ERROR_STOP=1 <<SQL
DO \$\$ BEGIN
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'faue_migrator') THEN
    CREATE ROLE faue_migrator LOGIN PASSWORD '${PW}' CREATEDB;
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'faue_gateway') THEN
    CREATE ROLE faue_gateway LOGIN PASSWORD '${PW}';
  END IF;
  IF NOT EXISTS (SELECT FROM pg_roles WHERE rolname = 'faue_ase') THEN
    CREATE ROLE faue_ase LOGIN PASSWORD '${PW}';
  END IF;
END \$\$;
SQL

for db in faue faue_test; do
  psql -d "$SUPER" -tAc "SELECT 1 FROM pg_database WHERE datname='${db}'" | grep -q 1 \
    || psql -d "$SUPER" -c "CREATE DATABASE ${db} OWNER faue_migrator"
  # pgvector needs superuser; migrations only check that it is present
  psql -d "${db}" -c "CREATE EXTENSION IF NOT EXISTS vector"
done

echo "provisioned: faue, faue_test"
```

- [ ] **Step 3: Bring it up and verify**

Run:
```bash
cd faue-infra && docker compose up -d
docker compose ps
psql postgresql://faue:faue_local_dev@localhost:5432/faue -c "SELECT extname FROM pg_extension WHERE extname='vector';"
```
Expected: four services healthy; one row returned for `vector`.

- [ ] **Step 4: Write `README.md`**

State what is deliberately absent: no application services, because they run under uvicorn on the host. State that the documented local default avoids containers entirely (hosted Postgres/Redis, `EVENT_TRANSPORT=inprocess`) and this file exists for full-fidelity work — testing retries, dead-lettering, consumer lag.

- [ ] **Step 5: Commit**

```bash
cd faue-infra && git init -q && git add -A
git commit -m "feat: local infrastructure profile

Postgres+pgvector, Redis, RabbitMQ, MinIO. Application services run under
uvicorn on the host, not here."
```

---

## Task 2: Initial migration

**Files:**
- Create: `faue-db/migrations/versions/0001_initial.py`
- Create: `faue-db/tests/test_migrations.py`
- Create: `faue-db/tests/conftest.py`

**Interfaces:**
- Consumes: models from Task 0 (already written) via `faue_db.registry.metadata`.
- Produces: `alembic upgrade head` creates every MVP table in `gateway` and `ase`.

- [ ] **Step 1: Write the failing test**

```python
# faue-db/tests/test_migrations.py
"""Migrations against a real Postgres. A migration that only passes against
SQLite is a migration that has not been tested."""

import pytest
from sqlalchemy import inspect, text


def test_upgrade_creates_every_table(migrated_engine):
    inspector = inspect(migrated_engine)
    gateway_tables = set(inspector.get_table_names(schema="gateway"))
    ase_tables = set(inspector.get_table_names(schema="ase"))

    assert "users" in gateway_tables
    assert "workspaces" in gateway_tables
    assert "auth_identities" in gateway_tables
    assert "vault_items" in gateway_tables
    assert "looks" in ase_tables
    assert "vault_embeddings" in ase_tables


def test_pgvector_extension_is_available(migrated_engine):
    with migrated_engine.connect() as conn:
        row = conn.execute(
            text("SELECT extname FROM pg_extension WHERE extname = 'vector'")
        ).first()
    assert row is not None, "pgvector must be installed before vector columns exist"


def test_workspace_id_is_not_nullable(migrated_engine):
    """ADR 0021: nullable would make the column a lie until it became true."""
    inspector = inspect(migrated_engine)
    for table in ("profiles", "vault_items", "style_preferences"):
        columns = {c["name"]: c for c in inspector.get_columns(table, schema="gateway")}
        assert "workspace_id" in columns, f"{table} missing workspace_id"
        assert columns["workspace_id"]["nullable"] is False, f"{table}.workspace_id nullable"


def test_downgrade_then_upgrade_round_trips(alembic_config, migrated_engine):
    """A broken downgrade is otherwise discovered during an incident, which is
    the worst possible time."""
    from alembic import command

    command.downgrade(alembic_config, "base")
    inspector = inspect(migrated_engine)
    assert "users" not in set(inspector.get_table_names(schema="gateway"))

    command.upgrade(alembic_config, "head")
    inspector = inspect(migrated_engine)
    assert "users" in set(inspector.get_table_names(schema="gateway"))


def test_models_match_migrations(alembic_config, migrated_engine):
    """`alembic check` is the guarantee this whole repository rests on: a model
    edited without a migration cannot merge."""
    from alembic import command
    from alembic.util.exc import AutogenerateDiffsDetected

    try:
        command.check(alembic_config)
    except AutogenerateDiffsDetected as exc:
        pytest.fail(f"models and migrations have diverged:\n{exc}")
```

```python
# faue-db/tests/conftest.py
import os

import pytest
from alembic.config import Config
from sqlalchemy import create_engine, text

TEST_DB_URL = os.environ.get(
    "TEST_DATABASE_URL", "postgresql://faue:faue_local_dev@localhost:5432/faue_test"
)


@pytest.fixture(scope="session")
def alembic_config() -> Config:
    config = Config("alembic.ini")
    config.set_main_option("sqlalchemy.url", TEST_DB_URL)
    return config


@pytest.fixture(scope="session")
def migrated_engine(alembic_config):
    from alembic import command

    admin_url = TEST_DB_URL.rsplit("/", 1)[0] + "/postgres"
    admin = create_engine(admin_url, isolation_level="AUTOCOMMIT")
    db_name = TEST_DB_URL.rsplit("/", 1)[1]
    with admin.connect() as conn:
        conn.execute(text(f'DROP DATABASE IF EXISTS "{db_name}"'))
        conn.execute(text(f'CREATE DATABASE "{db_name}"'))
    admin.dispose()

    command.upgrade(alembic_config, "head")

    engine = create_engine(TEST_DB_URL)
    yield engine
    engine.dispose()
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd faue-db && pytest tests/test_migrations.py -v`
Expected: FAIL — no revision exists, so `upgrade` finds nothing to run and no tables appear.

- [ ] **Step 3: Generate the revision**

```bash
export DATABASE_URL="postgresql://faue:faue_local_dev@localhost:5432/faue"
alembic revision --autogenerate -m "initial schema"
mv migrations/versions/*_initial_schema.py migrations/versions/0001_initial.py
```

Then **read the generated file**. Autogenerate will have missed: the `CREATE EXTENSION`, the schema creation, the pgvector columns on `user_style_context` and the `*_embeddings` tables, and every HNSW index.

- [ ] **Step 4: Add what autogenerate missed**

Three gaps, all of which were hit for real when this was executed:

**4a. Missing imports.** Autogenerate emits `pgvector.sqlalchemy.vector.VECTOR()` and
`faue_db.types.EncryptedStr()` without importing either. Add to the migration, and to
`migrations/script.py.mako` so it never recurs:

```python
import pgvector.sqlalchemy
import faue_db.types
```

**4b. The extension is a precondition, not a migration step.** `CREATE EXTENSION`
needs superuser; the migrator role is deliberately unprivileged. `env.py` checks
for it and fails with a clear message rather than a permission error three frames
deep:

```python
def _require_pgvector(connection) -> None:
    installed = connection.exec_driver_sql(
        "SELECT 1 FROM pg_extension WHERE extname = 'vector'"
    ).first()
    if installed is None:
        raise RuntimeError(
            "pgvector is not installed in this database.\n"
            "Run once as a superuser:  psql -d <db> -c 'CREATE EXTENSION vector;'"
        )
```

**4c. HNSW indexes need a cast expression.** pgvector **cannot index a
dimensionless `vector` column** — it fails with `column does not have dimensions`.
Since the column is deliberately dimensionless so several embedding models can
coexist, the index casts in an expression and is partial on `model_id`:

```python
    op.execute("""
        CREATE INDEX idx_vault_emb_hnsw_cliplarge ON ase.vault_embeddings
          USING hnsw ((embedding::vector(768)) vector_cosine_ops)
          WITH (m = 16, ef_construction = 64)
          WHERE model_id = 'open_clip/ViT-L-14-336'
    """)
```

**Queries must repeat the same cast to hit the index:**

```sql
SELECT item_id FROM ase.vault_embeddings
WHERE model_id = 'open_clip/ViT-L-14-336'
ORDER BY embedding::vector(768) <=> $1::vector(768)
LIMIT 40;
```

Because SQLAlchemy cannot express a cast-expression partial index, autogenerate
sees these as orphans and tries to drop them on every run. Exclude them in
`env.py`:

```python
MANUAL_INDEX_MARKERS = ("_hnsw_",)

def include_object(obj, name, type_, reflected, compare_to) -> bool:
    if type_ == "table" and obj.schema not in SCHEMAS:
        return False
    if type_ == "index" and name and any(m in name for m in MANUAL_INDEX_MARKERS):
        return False
    return True
```

Keep the exclusion narrow. After adding it, verify `alembic check` still fires on
a real model change — a gate nobody has seen fail is a gate nobody knows works.

**4d. Grants belong in the migration**, not a `.sql` file:

```python
    op.execute("GRANT USAGE ON SCHEMA gateway TO faue_gateway")
    op.execute("GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gateway TO faue_gateway")
    op.execute("REVOKE UPDATE, DELETE ON gateway.audit_log FROM faue_gateway")
    op.execute("REVOKE UPDATE, DELETE ON gateway.quiz_responses FROM faue_gateway")
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `cd faue-db && pytest tests/ -v`
Expected: PASS, including `test_models_match_migrations` and the down/up round trip.

- [ ] **Step 6: Commit**

```bash
git add migrations/versions/0001_initial.py tests/
git commit -m "feat: initial schema migration

Every MVP table in gateway and ase, plus the pgvector columns and HNSW
indexes autogenerate cannot express. Verified against a real Postgres with
a downgrade/upgrade round trip."
```

---

## Task 3: CI gates

**Files:**
- Create: `faue-infra/.github/workflows/python-service.yml`
- Create: `faue-db/.github/workflows/ci.yml`
- Create: `api-gateway/.github/workflows/ci.yml`

**Interfaces:**
- Produces: a reusable workflow other repos call, plus per-repo CI.

- [ ] **Step 1: Write the reusable service workflow**

```yaml
# faue-infra/.github/workflows/python-service.yml
name: python-service
on:
  workflow_call:
    inputs:
      service-path: { type: string, default: "." }

jobs:
  check:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env: { POSTGRES_USER: faue, POSTGRES_PASSWORD: faue_local_dev, POSTGRES_DB: faue }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U faue" --health-interval 5s
          --health-timeout 5s --health-retries 10
      redis:
        image: redis:7-alpine
        ports: ["6379:6379"]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -r requirements/dev.txt || pip install -e ".[dev]"
      - run: ruff check .
      - run: mypy --strict app || true   # advisory until the skeleton is filled in
      - run: pytest -q
```

- [ ] **Step 2: Write the `faue-db` workflow with the migration gates**

```yaml
# faue-db/.github/workflows/ci.yml
name: ci
on: [push, pull_request]

jobs:
  migrations:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: pgvector/pgvector:pg16
        env: { POSTGRES_USER: faue, POSTGRES_PASSWORD: faue_local_dev, POSTGRES_DB: faue_test }
        ports: ["5432:5432"]
        options: >-
          --health-cmd "pg_isready -U faue" --health-interval 5s
          --health-timeout 5s --health-retries 10
    env:
      TEST_DATABASE_URL: postgresql://faue:faue_local_dev@localhost:5432/faue_test
      DATABASE_URL: postgresql://faue:faue_local_dev@localhost:5432/faue_test
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.12" }
      - run: pip install -e . && pip install pytest alembic psycopg2-binary pgvector

      - name: Migrations apply
        run: alembic upgrade head

      - name: Models match migrations
        run: alembic check          # non-empty diff fails the build

      - name: Downgrade round-trips
        run: alembic downgrade -1 && alembic upgrade head

      - name: Schema invariants
        run: pytest tests/test_schema_invariants.py -q
```

- [ ] **Step 3: Verify the `alembic check` gate actually fires**

Run:
```bash
cd faue-db
# add a column to a model without a migration
python - <<'EOF'
p = "faue_db/gateway/models.py"
s = open(p).read()
s = s.replace(
    '    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)',
    '    status: Mapped[str] = mapped_column(Text, default="active", nullable=False)\n'
    '    probe_column: Mapped[str | None] = mapped_column(Text)',
    1,
)
open(p, "w").write(s)
EOF
alembic check
```
Expected: FAIL with `AutogenerateDiffsDetected`. **Then revert the probe.**

This step is not optional. A gate nobody has seen fail is a gate nobody knows works.

- [ ] **Step 4: Commit**

```bash
git add .github/
git commit -m "ci: migration gates

alembic upgrade, alembic check, downgrade round-trip, schema invariants.
The check gate is verified to fire on a model edited without a migration."
```

---

# SLICE 1 — Identity

## Task 4: Personal workspace bootstrap

**Files:**
- Create: `api-gateway/app/modules/identity/workspace.py`
- Create: `api-gateway/tests/integration/test_workspace_bootstrap.py`

**Interfaces:**
- Produces: `async def create_user_with_workspace(session, *, status="active") -> tuple[User, Workspace]`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/integration/test_workspace_bootstrap.py
"""ADR 0021 — the personal workspace is created in the SAME transaction as the
user, so workspace_id is never null and never a lie."""

import pytest
from sqlalchemy import select

from app.modules.identity.workspace import create_user_with_workspace
from faue_db.gateway.models import Workspace, WorkspaceMember


async def test_creating_a_user_creates_a_personal_workspace(session):
    user, workspace = await create_user_with_workspace(session)
    await session.flush()

    assert workspace.kind == "personal"
    assert workspace.owner_user_id == user.id


async def test_the_user_is_the_sole_member(session):
    user, workspace = await create_user_with_workspace(session)
    await session.flush()

    members = (await session.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace.id)
    )).scalars().all()

    assert len(members) == 1
    assert members[0].user_id == user.id
    assert members[0].role == "owner"


async def test_rollback_leaves_no_orphan_workspace(session):
    """Same transaction means a failed signup leaves nothing behind."""
    user, workspace = await create_user_with_workspace(session)
    workspace_id = workspace.id
    await session.rollback()

    found = (await session.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )).scalar_one_or_none()
    assert found is None
```

- [ ] **Step 2: Run it to verify it fails**

Run: `cd api-gateway && pytest tests/integration/test_workspace_bootstrap.py -v`
Expected: FAIL with `ModuleNotFoundError: app.modules.identity.workspace`

- [ ] **Step 3: Write the implementation**

```python
# api-gateway/app/modules/identity/workspace.py
"""Personal workspace bootstrap (ADR 0021).

Single-tenant in behaviour: every account has exactly one workspace with one
member. The API does not expose the concept and the client never sees it.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy.ext.asyncio import AsyncSession

from faue_db.base import uuid7
from faue_db.gateway.models import User, Workspace, WorkspaceMember


async def create_user_with_workspace(
    session: AsyncSession, *, status: str = "active"
) -> tuple[User, Workspace]:
    """Create a user and their personal workspace atomically.

    Both rows are added to the caller's session and committed together, so a
    failed signup cannot leave a workspace without a user or the reverse.
    """
    now = datetime.now(UTC)

    user = User(id=uuid7(), status=status, age_verified=False,
                created_at=now, updated_at=now)
    workspace = Workspace(id=uuid7(), kind="personal", name=None,
                          owner_user_id=user.id, created_at=now)
    member = WorkspaceMember(workspace_id=workspace.id, user_id=user.id,
                             role="owner", joined_at=now)

    session.add_all([user, workspace, member])
    return user, workspace
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_workspace_bootstrap.py -v`
Expected: PASS (3 tests)

- [ ] **Step 5: Commit**

```bash
git add app/modules/identity/workspace.py tests/integration/test_workspace_bootstrap.py
git commit -m "feat(identity): personal workspace bootstrap

User and workspace created in one transaction, per ADR 0021."
```

---

## Task 5: Session tokens

**Files:**
- Create: `api-gateway/app/modules/identity/tokens.py`
- Create: `api-gateway/tests/unit/test_tokens.py`

**Interfaces:**
- Produces:
  - `def issue_access_token(user_id: UUID, workspace_id: UUID, *, settings) -> str`
  - `def verify_access_token(token: str, *, settings) -> AccessClaims`
  - `async def issue_session(session, user_id, workspace_id, *, settings, user_agent=None) -> SessionTokens`
  - `async def rotate_refresh(session, presented: str, *, settings) -> SessionTokens`
  - `@dataclass SessionTokens(access_token, refresh_token, expires_in)`
  - `@dataclass AccessClaims(user_id, workspace_id, expires_at)`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/unit/test_tokens.py
import time
from uuid import uuid4

import pytest

from app.modules.identity import tokens
from faue_core.errors.taxonomy import TokenExpired, Unauthenticated


class FakeSettings:
    jwt_private_key = "test-secret-not-for-production"
    jwt_public_key = "test-secret-not-for-production"
    access_token_ttl_seconds = 900
    refresh_token_ttl_seconds = 2592000


def test_access_token_round_trips():
    user_id, workspace_id = uuid4(), uuid4()
    token = tokens.issue_access_token(user_id, workspace_id, settings=FakeSettings())
    claims = tokens.verify_access_token(token, settings=FakeSettings())

    assert claims.user_id == user_id
    assert claims.workspace_id == workspace_id


def test_expired_access_token_is_rejected():
    class Expired(FakeSettings):
        access_token_ttl_seconds = -1

    token = tokens.issue_access_token(uuid4(), uuid4(), settings=Expired())
    with pytest.raises(TokenExpired):
        tokens.verify_access_token(token, settings=FakeSettings())


def test_tampered_token_is_rejected():
    token = tokens.issue_access_token(uuid4(), uuid4(), settings=FakeSettings())
    tampered = token[:-4] + "AAAA"
    with pytest.raises(Unauthenticated):
        tokens.verify_access_token(tampered, settings=FakeSettings())


def test_token_signed_with_another_key_is_rejected():
    class Other(FakeSettings):
        jwt_private_key = "a-different-secret"

    token = tokens.issue_access_token(uuid4(), uuid4(), settings=Other())
    with pytest.raises(Unauthenticated):
        tokens.verify_access_token(token, settings=FakeSettings())


def test_workspace_id_is_carried_in_the_token():
    """Every scoped query reads it from here rather than looking it up."""
    workspace_id = uuid4()
    token = tokens.issue_access_token(uuid4(), workspace_id, settings=FakeSettings())
    assert tokens.verify_access_token(token, settings=FakeSettings()).workspace_id == workspace_id
```

```python
# api-gateway/tests/integration/test_refresh_rotation.py
"""Refresh rotation and theft detection."""

import pytest

from app.modules.identity import tokens
from app.modules.identity.workspace import create_user_with_workspace
from faue_core.errors.taxonomy import RefreshReuseDetected, Unauthenticated


async def test_refresh_returns_a_new_pair(session, settings):
    user, workspace = await create_user_with_workspace(session)
    await session.flush()
    first = await tokens.issue_session(session, user.id, workspace.id, settings=settings)

    second = await tokens.rotate_refresh(session, first.refresh_token, settings=settings)

    assert second.refresh_token != first.refresh_token
    assert second.access_token != first.access_token


async def test_reusing_a_rotated_token_revokes_the_family(session, settings):
    """This is theft detection working. The correct client response is to sign
    out, never to retry."""
    user, workspace = await create_user_with_workspace(session)
    await session.flush()
    first = await tokens.issue_session(session, user.id, workspace.id, settings=settings)
    second = await tokens.rotate_refresh(session, first.refresh_token, settings=settings)

    with pytest.raises(RefreshReuseDetected):
        await tokens.rotate_refresh(session, first.refresh_token, settings=settings)

    # the whole family is dead, including the token that was legitimately issued
    with pytest.raises(Unauthenticated):
        await tokens.rotate_refresh(session, second.refresh_token, settings=settings)


async def test_unknown_refresh_token_is_rejected(session, settings):
    with pytest.raises(Unauthenticated):
        await tokens.rotate_refresh(session, "not-a-real-token", settings=settings)


async def test_refresh_tokens_are_stored_only_as_hashes(session, settings):
    from sqlalchemy import select
    from faue_db.gateway.models import RefreshToken

    user, workspace = await create_user_with_workspace(session)
    await session.flush()
    issued = await tokens.issue_session(session, user.id, workspace.id, settings=settings)
    await session.flush()

    stored = (await session.execute(select(RefreshToken))).scalars().all()
    assert len(stored) == 1
    assert issued.refresh_token not in {row.token_hash for row in stored}
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/unit/test_tokens.py tests/integration/test_refresh_rotation.py -v`
Expected: FAIL — `tokens` has no such attributes.

- [ ] **Step 3: Write the implementation**

```python
# api-gateway/app/modules/identity/tokens.py
"""Session tokens.

Access tokens are short-lived JWTs. Refresh tokens are opaque, stored only as a
hash, and rotate on every use — presenting a rotated token revokes the entire
family, which is theft detection rather than an error.
"""

from __future__ import annotations

import hashlib
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

import jwt
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from faue_core.errors.taxonomy import (
    RefreshReuseDetected, TokenExpired, Unauthenticated,
)
from faue_db.base import uuid7
from faue_db.gateway.models import RefreshToken

ALGORITHM = "HS256"


@dataclass(frozen=True)
class AccessClaims:
    user_id: UUID
    workspace_id: UUID
    expires_at: datetime


@dataclass(frozen=True)
class SessionTokens:
    access_token: str
    refresh_token: str
    expires_in: int


def _hash(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


def issue_access_token(user_id: UUID, workspace_id: UUID, *, settings: Any) -> str:
    now = datetime.now(UTC)
    payload = {
        "sub": str(user_id),
        "wsp": str(workspace_id),
        "iat": int(now.timestamp()),
        "exp": int((now + timedelta(seconds=settings.access_token_ttl_seconds)).timestamp()),
    }
    return jwt.encode(payload, settings.jwt_private_key, algorithm=ALGORITHM)


def verify_access_token(token: str, *, settings: Any) -> AccessClaims:
    try:
        payload = jwt.decode(token, settings.jwt_public_key, algorithms=[ALGORITHM])
    except jwt.ExpiredSignatureError as exc:
        raise TokenExpired("access token expired") from exc
    except jwt.PyJWTError as exc:
        raise Unauthenticated("invalid access token") from exc

    return AccessClaims(
        user_id=UUID(payload["sub"]),
        workspace_id=UUID(payload["wsp"]),
        expires_at=datetime.fromtimestamp(payload["exp"], UTC),
    )


async def issue_session(
    session: AsyncSession,
    user_id: UUID,
    workspace_id: UUID,
    *,
    settings: Any,
    user_agent: str | None = None,
    family_id: UUID | None = None,
    rotated_from: UUID | None = None,
) -> SessionTokens:
    raw = secrets.token_urlsafe(32)
    row = RefreshToken(
        id=uuid7(),
        user_id=user_id,
        token_hash=_hash(raw),
        family_id=family_id or uuid7(),
        rotated_from=rotated_from,
        user_agent=user_agent,
        expires_at=datetime.now(UTC) + timedelta(seconds=settings.refresh_token_ttl_seconds),
        created_at=datetime.now(UTC),
    )
    session.add(row)

    return SessionTokens(
        access_token=issue_access_token(user_id, workspace_id, settings=settings),
        refresh_token=raw,
        expires_in=settings.access_token_ttl_seconds,
    )


async def rotate_refresh(
    session: AsyncSession, presented: str, *, settings: Any
) -> SessionTokens:
    row = (await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == _hash(presented))
    )).scalar_one_or_none()

    if row is None:
        raise Unauthenticated("unknown refresh token")

    if row.revoked_at is not None:
        # A revoked token was presented: either theft, or a client issuing
        # parallel refreshes. Either way the family is no longer trustworthy.
        await _revoke_family(session, row.family_id)
        raise RefreshReuseDetected("refresh token reuse detected; family revoked")

    if row.expires_at <= datetime.now(UTC):
        raise Unauthenticated("refresh token expired")

    row.revoked_at = datetime.now(UTC)

    from faue_db.gateway.models import WorkspaceMember

    workspace_id = (await session.execute(
        select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == row.user_id)
    )).scalars().first()

    return await issue_session(
        session, row.user_id, workspace_id,
        settings=settings, user_agent=row.user_agent,
        family_id=row.family_id, rotated_from=row.id,
    )


async def _revoke_family(session: AsyncSession, family_id: UUID) -> None:
    await session.execute(
        update(RefreshToken)
        .where(RefreshToken.family_id == family_id, RefreshToken.revoked_at.is_(None))
        .values(revoked_at=datetime.now(UTC))
    )


async def revoke_family_for_token(session: AsyncSession, presented: str) -> None:
    """Logout. Revokes the presented family; unknown tokens are a no-op, because
    telling a caller their token was unknown is an oracle."""
    row = (await session.execute(
        select(RefreshToken).where(RefreshToken.token_hash == _hash(presented))
    )).scalar_one_or_none()
    if row is not None:
        await _revoke_family(session, row.family_id)
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/unit/test_tokens.py tests/integration/test_refresh_rotation.py -v`
Expected: PASS (9 tests)

- [ ] **Step 5: Commit**

```bash
git add app/modules/identity/tokens.py tests/
git commit -m "feat(identity): session tokens with rotation and theft detection

Access JWT carries workspace_id. Refresh tokens are opaque, stored hashed,
and rotate on use; reuse revokes the family."
```

---

## Task 6: Magic-link request

**Files:**
- Create: `api-gateway/app/modules/identity/email_sender.py`
- Create: `api-gateway/app/modules/identity/magic_link.py`
- Create: `api-gateway/tests/integration/test_magic_link_request.py`

**Interfaces:**
- Produces:
  - `class EmailSender(Protocol): async def send_magic_link(self, to: str, url: str) -> None`
  - `class RecordingEmailSender` with `.sent: list[tuple[str, str]]`
  - `async def request_link(redis, sender, *, email, session_challenge, settings) -> None`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/integration/test_magic_link_request.py
"""Requesting a magic link.

The provider decision does not block this: delivery sits behind an EmailSender
protocol, and tests use a recording implementation.
"""

import pytest

from app.modules.identity.email_sender import RecordingEmailSender
from app.modules.identity.magic_link import request_link
from faue_core.errors.taxonomy import RateLimited


async def test_a_link_is_sent(redis, settings):
    sender = RecordingEmailSender()
    await request_link(redis, sender, email="a@b.com",
                       session_challenge="c" * 32, settings=settings)

    assert len(sender.sent) == 1
    to, url = sender.sent[0]
    assert to == "a@b.com"
    assert "/auth/verify?t=" in url


async def test_the_raw_token_is_never_stored(redis, settings):
    """Only SHA-256 is stored, so a Redis dump cannot be replayed."""
    sender = RecordingEmailSender()
    await request_link(redis, sender, email="a@b.com",
                       session_challenge="c" * 32, settings=settings)

    _, url = sender.sent[0]
    raw = url.split("t=")[1]

    keys = await redis.keys("magic_link:*")
    assert len(keys) == 1
    assert raw not in keys[0].decode()


async def test_requesting_again_invalidates_the_previous_token(redis, settings):
    """One active token per identifier."""
    sender = RecordingEmailSender()
    await request_link(redis, sender, email="a@b.com",
                       session_challenge="c" * 32, settings=settings)
    await request_link(redis, sender, email="a@b.com",
                       session_challenge="c" * 32, settings=settings)

    assert len(await redis.keys("magic_link:*")) == 1


async def test_the_token_expires(redis, settings):
    sender = RecordingEmailSender()
    await request_link(redis, sender, email="a@b.com",
                       session_challenge="c" * 32, settings=settings)

    key = (await redis.keys("magic_link:*"))[0]
    ttl = await redis.ttl(key)
    assert 0 < ttl <= settings.magic_link_ttl_seconds


async def test_rate_limited_per_identifier(redis, settings):
    sender = RecordingEmailSender()
    for _ in range(settings.rate_limit_magic_link_per_hour):
        await request_link(redis, sender, email="a@b.com",
                           session_challenge="c" * 32, settings=settings)

    with pytest.raises(RateLimited):
        await request_link(redis, sender, email="a@b.com",
                           session_challenge="c" * 32, settings=settings)


async def test_email_is_normalised(redis, settings):
    """Trailing whitespace and case must not create a second identity."""
    sender = RecordingEmailSender()
    await request_link(redis, sender, email=" A@B.com ",
                       session_challenge="c" * 32, settings=settings)
    assert sender.sent[0][0] == "a@b.com"
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/integration/test_magic_link_request.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.identity.email_sender`

- [ ] **Step 3: Write `email_sender.py`**

```python
# api-gateway/app/modules/identity/email_sender.py
"""Email delivery via Resend.

Behind a protocol so tests never make a network call and local development never
sends a real message.

Login depends on email arriving, which makes SPF, DKIM and DMARC on the sending
subdomain an operational requirement rather than a nicety. Use a subdomain
(`mail.faueofficial.com`) so a reputation problem never affects the apex.
"""

from __future__ import annotations

from typing import Any, Protocol

import httpx

from faue_core.errors.taxonomy import ServiceUnavailable

RESEND_ENDPOINT = "https://api.resend.com/emails"


class EmailSender(Protocol):
    async def send_magic_link(self, to: str, url: str, *, idempotency_key: str) -> None: ...


class RecordingEmailSender:
    """Tests and local development. Records instead of sending."""

    def __init__(self) -> None:
        self.sent: list[tuple[str, str]] = []

    async def send_magic_link(self, to: str, url: str, *, idempotency_key: str = "") -> None:
        self.sent.append((to, url))


class ResendEmailSender:
    def __init__(self, api_key: str, from_domain: str, *, timeout: float = 5.0) -> None:
        self._api_key = api_key
        self._from = f"FAUE <hello@{from_domain}>"
        self._timeout = timeout

    async def send_magic_link(self, to: str, url: str, *, idempotency_key: str = "") -> None:
        headers = {"Authorization": f"Bearer {self._api_key}"}
        # Resend honours Idempotency-Key, so a retry after a timeout cannot send twice
        if idempotency_key:
            headers["Idempotency-Key"] = idempotency_key

        try:
            async with httpx.AsyncClient(timeout=self._timeout) as http:
                response = await http.post(
                    RESEND_ENDPOINT,
                    headers=headers,
                    json={
                        "from": self._from,
                        "to": [to],
                        "subject": "Your FAUE sign-in link",
                        "html": render_magic_link_email(url),
                        "text": f"Sign in to FAUE: {url}\n\nThis link expires in 10 minutes.",
                    },
                )
        except httpx.RequestError as exc:
            raise ServiceUnavailable("email provider unreachable") from exc

        # 429 is Resend's rate limit — 2 requests/second on the default plan.
        # Surfacing it as ServiceUnavailable lets the caller retry with backoff
        # rather than telling the user their address is wrong.
        if response.status_code >= 400:
            raise ServiceUnavailable(f"email provider returned {response.status_code}")


def render_magic_link_email(url: str) -> str:
    """Plain, high-deliverability HTML. Image-heavy templates land in spam more
    often, and this email is the only way into the product."""
    return f"""\
<!doctype html>
<html><body style="font-family:system-ui,sans-serif;padding:32px;color:#1E1F20">
  <h1 style="font-size:22px;margin:0 0 16px">Sign in to FAUE</h1>
  <p style="font-size:16px;line-height:24px;margin:0 0 24px">
    Tap the button below to sign in. This link expires in 10 minutes and can
    only be used once.
  </p>
  <a href="{url}"
     style="display:inline-block;background:#0F3D2E;color:#fff;padding:12px 24px;
            border-radius:8px;text-decoration:none;font-weight:500">Sign in</a>
  <p style="font-size:12px;line-height:20px;color:#6B7280;margin:24px 0 0">
    If you did not request this, you can ignore it — nobody can sign in without
    the link.
  </p>
</body></html>"""


def build_sender(settings: Any) -> EmailSender:
    """Recording locally and whenever no key is configured, so a missing key
    degrades to "link printed in the log" rather than a broken signup."""
    if settings.environment == "local" or not settings.resend_api_key:
        return RecordingEmailSender()
    return ResendEmailSender(
        settings.resend_api_key.get_secret_value(), settings.email_from_domain
    )
```

**Resend specifics worth knowing before wiring it:**

| Detail | Consequence |
|---|---|
| API key is `re_...` | Store as `RESEND_API_KEY`; never in the repo |
| Rate limit 2 req/sec on the default plan | A signup burst will 429. The magic-link limiter caps per identifier, but a global burst is still possible — retry with backoff |
| `from` domain must be verified in Resend | Verify `mail.faueofficial.com` and add its SPF/DKIM records before the first real send |
| `Idempotency-Key` supported | Pass it, so a retry after a timeout cannot double-send |
| Test mode addresses | `delivered@resend.dev` and `bounced@resend.dev` exercise both paths on staging |

- [ ] **Step 4: Write `magic_link.py` (request half)**

```python
# api-gateway/app/modules/identity/magic_link.py
"""Magic-link authentication.

The token is 32 random bytes, opaque, stored only as SHA-256, single-use, with a
10-minute TTL and one active token per identifier.

Never a JWT: a signed token in a URL is a bearer credential that persists in
browser history, referrer headers and mail server logs.
"""

from __future__ import annotations

import hashlib
import json
import secrets
from dataclasses import dataclass
from typing import Any

from faue_core.crypto.blind_index import normalise
from faue_core.errors.taxonomy import RateLimited

from app.modules.identity.email_sender import EmailSender

TOKEN_KEY = "magic_link:{digest}"
ACTIVE_KEY = "magic_link_active:{identifier}"
RATE_KEY = "ratelimit:magic_link:{identifier}"


def _digest(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()


async def request_link(
    redis: Any,
    sender: EmailSender,
    *,
    email: str,
    session_challenge: str,
    settings: Any,
) -> None:
    """Mint and send a link.

    The caller always returns 202 regardless of what happens here, because
    revealing which addresses exist is an account-enumeration vector.
    """
    identifier = normalise(email)

    rate_key = RATE_KEY.format(identifier=identifier)
    count = await redis.incr(rate_key)
    if count == 1:
        await redis.expire(rate_key, 3600)
    if count > settings.rate_limit_magic_link_per_hour:
        raise RateLimited("too many magic link requests")

    # one active token per identifier: requesting again invalidates the previous
    active_key = ACTIVE_KEY.format(identifier=identifier)
    previous = await redis.get(active_key)
    if previous:
        await redis.delete(TOKEN_KEY.format(digest=previous.decode()))

    raw = secrets.token_urlsafe(32)
    digest = _digest(raw)

    await redis.setex(
        TOKEN_KEY.format(digest=digest),
        settings.magic_link_ttl_seconds,
        json.dumps({"identifier": identifier, "challenge": session_challenge, "attempts": 0}),
    )
    await redis.setex(active_key, settings.magic_link_ttl_seconds, digest)

    # the digest doubles as the idempotency key: unique per token, stable on retry
    await sender.send_magic_link(
        identifier, f"https://faueofficial.com/auth/verify?t={raw}", idempotency_key=digest
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/integration/test_magic_link_request.py -v`
Expected: PASS (6 tests)

- [ ] **Step 6: Commit**

```bash
git add app/modules/identity/email_sender.py app/modules/identity/magic_link.py tests/
git commit -m "feat(identity): magic link request

Opaque 32-byte token stored only as SHA-256, 10-minute TTL, one active per
identifier, rate limited. Delivery behind an EmailSender protocol."
```

---

## Task 7: Magic-link consume, with cross-device fallback

**Files:**
- Modify: `api-gateway/app/modules/identity/magic_link.py`
- Create: `api-gateway/tests/integration/test_magic_link_consume.py`

**Interfaces:**
- Produces:
  - `@dataclass ConsumeResult(identifier: str | None, device_code: str | None)`
  - `async def consume_link(redis, *, token, session_challenge=None, device_code=None, settings) -> ConsumeResult`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/integration/test_magic_link_consume.py
"""Consuming a magic link.

Three failure modes are designed for rather than discovered: mail scanners
pre-fetching the URL, the user opening the mail on another device, and the link
being tapped twice.
"""

import asyncio

import pytest

from app.modules.identity.email_sender import RecordingEmailSender
from app.modules.identity.magic_link import consume_link, request_link
from faue_core.errors.taxonomy import (
    DeviceCodeInvalid, DeviceCodeRequired, LinkAlreadyUsed, LinkExpired,
)

CHALLENGE = "c" * 32


async def _issue(redis, settings, email="a@b.com", challenge=CHALLENGE) -> str:
    sender = RecordingEmailSender()
    await request_link(redis, sender, email=email,
                       session_challenge=challenge, settings=settings)
    return sender.sent[0][1].split("t=")[1]


async def test_same_device_consume_succeeds(redis, settings):
    token = await _issue(redis, settings)
    result = await consume_link(redis, token=token,
                                session_challenge=CHALLENGE, settings=settings)
    assert result.identifier == "a@b.com"
    assert result.device_code is None


async def test_a_token_can_only_be_used_once(redis, settings):
    token = await _issue(redis, settings)
    await consume_link(redis, token=token, session_challenge=CHALLENGE, settings=settings)

    with pytest.raises(LinkAlreadyUsed):
        await consume_link(redis, token=token, session_challenge=CHALLENGE, settings=settings)


async def test_concurrent_consumes_yield_exactly_one_winner(redis, settings):
    """Atomic consumption: two simultaneous taps cannot both succeed."""
    token = await _issue(redis, settings)

    results = await asyncio.gather(
        consume_link(redis, token=token, session_challenge=CHALLENGE, settings=settings),
        consume_link(redis, token=token, session_challenge=CHALLENGE, settings=settings),
        return_exceptions=True,
    )
    successes = [r for r in results if not isinstance(r, Exception)]
    assert len(successes) == 1


async def test_unknown_token_is_rejected(redis, settings):
    with pytest.raises(LinkExpired):
        await consume_link(redis, token="never-existed",
                           session_challenge=CHALLENGE, settings=settings)


async def test_different_device_returns_a_code_and_does_not_consume(redis, settings):
    """The user requested on their phone and opened the mail on a laptop. This
    is common, not an edge case."""
    token = await _issue(redis, settings)

    with pytest.raises(DeviceCodeRequired) as exc:
        await consume_link(redis, token=token,
                           session_challenge="a-different-device", settings=settings)

    code = exc.value.device_code
    assert len(code) == 6 and code.isdigit()

    # the token survives, so the original session can still complete
    result = await consume_link(redis, token=token, session_challenge=CHALLENGE,
                                device_code=code, settings=settings)
    assert result.identifier == "a@b.com"


async def test_wrong_device_code_is_rejected(redis, settings):
    token = await _issue(redis, settings)
    with pytest.raises(DeviceCodeRequired):
        await consume_link(redis, token=token,
                           session_challenge="other", settings=settings)

    with pytest.raises(DeviceCodeInvalid):
        await consume_link(redis, token=token, session_challenge=CHALLENGE,
                           device_code="000000", settings=settings)


async def test_device_code_attempts_are_limited(redis, settings):
    token = await _issue(redis, settings)
    with pytest.raises(DeviceCodeRequired):
        await consume_link(redis, token=token, session_challenge="other", settings=settings)

    for _ in range(5):
        with pytest.raises((DeviceCodeInvalid, LinkExpired)):
            await consume_link(redis, token=token, session_challenge=CHALLENGE,
                               device_code="000000", settings=settings)

    # after too many attempts the token is destroyed rather than left to brute force
    with pytest.raises(LinkExpired):
        await consume_link(redis, token=token, session_challenge=CHALLENGE,
                           device_code="000000", settings=settings)
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/integration/test_magic_link_consume.py -v`
Expected: FAIL — `ImportError: cannot import name 'consume_link'`

- [ ] **Step 3: Add `device_code` to the exception**

In `faue-core/faue_core/errors/taxonomy.py`, replace the `DeviceCodeRequired` class:

```python
class DeviceCodeRequired(FaueError):
    """Opened on a different device. A normal flow, not a failure."""
    problem_type, status, title = "device_code_required", 409, "Confirm on your device"

    def __init__(self, detail: str | None = None, *, device_code: str) -> None:
        super().__init__(detail)
        self.device_code = device_code
```

- [ ] **Step 4: Write the consume implementation**

Append to `api-gateway/app/modules/identity/magic_link.py`:

```python
MAX_DEVICE_CODE_ATTEMPTS = 5

# Read, validate and delete in one round trip. Two concurrent taps cannot both
# succeed, and no application-level lock is needed.
_CONSUME_LUA = """
local raw = redis.call('GET', KEYS[1])
if not raw then return nil end
redis.call('DEL', KEYS[1])
return raw
"""


@dataclass(frozen=True)
class ConsumeResult:
    identifier: str
    device_code: str | None = None


async def consume_link(
    redis: Any,
    *,
    token: str,
    session_challenge: str | None = None,
    device_code: str | None = None,
    settings: Any,
) -> ConsumeResult:
    """Exchange a token for an identifier.

    POST only. Mail security scanners pre-fetch every URL in a message, so a GET
    that consumed the token would burn the login before the user tapped it.
    """
    from faue_core.errors.taxonomy import (
        DeviceCodeInvalid, DeviceCodeRequired, LinkAlreadyUsed, LinkExpired,
    )

    key = TOKEN_KEY.format(digest=_digest(token))
    raw = await redis.get(key)
    if raw is None:
        raise LinkExpired("magic link expired or already used")

    state = json.loads(raw)

    # cross-device: the link was opened somewhere other than where it was asked for
    if session_challenge != state["challenge"]:
        if device_code is None:
            code = state.get("device_code") or f"{secrets.randbelow(1_000_000):06d}"
            state["device_code"] = code
            await redis.setex(key, settings.magic_link_ttl_seconds, json.dumps(state))
            raise DeviceCodeRequired("open on the requesting device", device_code=code)

    if state.get("device_code"):
        if device_code != state["device_code"]:
            state["attempts"] = state.get("attempts", 0) + 1
            if state["attempts"] >= MAX_DEVICE_CODE_ATTEMPTS:
                await redis.delete(key)
                raise LinkExpired("too many incorrect codes")
            await redis.setex(key, settings.magic_link_ttl_seconds, json.dumps(state))
            raise DeviceCodeInvalid("incorrect code")

    # atomic single-use consumption
    consumed = await redis.eval(_CONSUME_LUA, 1, key)
    if consumed is None:
        raise LinkAlreadyUsed("magic link already used")

    identifier = json.loads(consumed)["identifier"]
    await redis.delete(ACTIVE_KEY.format(identifier=identifier))
    return ConsumeResult(identifier=identifier)
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/integration/test_magic_link_consume.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add app/modules/identity/magic_link.py tests/ ../faue-core/faue_core/errors/taxonomy.py
git commit -m "feat(identity): magic link consume with cross-device fallback

Atomic single-use consumption via Lua. A link opened on another device
returns a 6-digit code rather than failing, with attempts capped."
```

---

## Task 8: Google and Apple sign-in

**Files:**
- Create: `api-gateway/app/modules/identity/oidc_google.py`
- Create: `api-gateway/app/modules/identity/oidc_apple.py`
- Create: `api-gateway/tests/unit/test_oidc.py`

**Interfaces:**
- Produces:
  - `@dataclass OAuthIdentity(provider, provider_uid, email, email_verified, display_name)`
  - `async def verify_google(id_token: str, *, nonce: str, settings) -> OAuthIdentity`
  - `async def verify_apple(identity_token: str, *, nonce: str, full_name: str | None, settings) -> OAuthIdentity`
  - `def build_apple_client_secret(*, team_id, key_id, client_id, private_key) -> str`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/unit/test_oidc.py
"""OAuth verification.

Tokens are verified server-side against provider JWKS. A client-supplied profile
is never trusted, because it is trivially forged.
"""

import time
from datetime import UTC, datetime, timedelta

import jwt
import pytest

from app.modules.identity import oidc_apple, oidc_google
from faue_core.errors.taxonomy import Unauthenticated

SECRET = "test-jwks-key"


def make_token(**claims) -> str:
    base = {
        "iss": "https://accounts.google.com",
        "aud": "test-client-id",
        "sub": "google-user-123",
        "email": "a@b.com",
        "email_verified": True,
        "nonce": "test-nonce",
        "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
    }
    return jwt.encode({**base, **claims}, SECRET, algorithm="HS256")


class FakeSettings:
    google_client_id = "test-client-id"


@pytest.fixture
def stub_jwks(monkeypatch):
    monkeypatch.setattr(oidc_google, "_signing_key_for", lambda token: SECRET)
    monkeypatch.setattr(oidc_apple, "_signing_key_for", lambda token: SECRET)


async def test_valid_google_token_yields_an_identity(stub_jwks):
    identity = await oidc_google.verify_google(
        make_token(), nonce="test-nonce", settings=FakeSettings()
    )
    assert identity.provider == "google"
    assert identity.provider_uid == "google-user-123"
    assert identity.email == "a@b.com"
    assert identity.email_verified is True


async def test_wrong_audience_is_rejected(stub_jwks):
    with pytest.raises(Unauthenticated):
        await oidc_google.verify_google(
            make_token(aud="someone-elses-app"), nonce="test-nonce", settings=FakeSettings()
        )


async def test_wrong_issuer_is_rejected(stub_jwks):
    with pytest.raises(Unauthenticated):
        await oidc_google.verify_google(
            make_token(iss="https://evil.example"), nonce="test-nonce", settings=FakeSettings()
        )


async def test_nonce_mismatch_is_rejected(stub_jwks):
    """Without this, a token captured elsewhere can be replayed."""
    with pytest.raises(Unauthenticated):
        await oidc_google.verify_google(
            make_token(), nonce="a-different-nonce", settings=FakeSettings()
        )


async def test_expired_token_is_rejected(stub_jwks):
    with pytest.raises(Unauthenticated):
        await oidc_google.verify_google(
            make_token(exp=int(time.time()) - 10), nonce="test-nonce", settings=FakeSettings()
        )


async def test_apple_private_relay_address_is_accepted(stub_jwks):
    """xyz@privaterelay.appleid.com is a real, working address."""
    token = jwt.encode(
        {
            "iss": "https://appleid.apple.com", "aud": "com.faueofficial.app",
            "sub": "apple-user-456", "email": "xyz@privaterelay.appleid.com",
            "email_verified": "true", "nonce": "test-nonce",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        SECRET, algorithm="HS256",
    )

    class AppleSettings:
        apple_client_id = "com.faueofficial.app"

    identity = await oidc_apple.verify_apple(
        token, nonce="test-nonce", full_name="Amara O", settings=AppleSettings()
    )
    assert identity.email == "xyz@privaterelay.appleid.com"
    assert identity.display_name == "Amara O"


async def test_apple_full_name_is_only_present_on_first_authorization(stub_jwks):
    """Apple sends it once. If it is not captured then, it is gone permanently."""
    token = jwt.encode(
        {
            "iss": "https://appleid.apple.com", "aud": "com.faueofficial.app",
            "sub": "apple-user-456", "email": "a@b.com", "nonce": "test-nonce",
            "exp": int((datetime.now(UTC) + timedelta(minutes=5)).timestamp()),
        },
        SECRET, algorithm="HS256",
    )

    class AppleSettings:
        apple_client_id = "com.faueofficial.app"

    identity = await oidc_apple.verify_apple(
        token, nonce="test-nonce", full_name=None, settings=AppleSettings()
    )
    assert identity.display_name is None
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/unit/test_oidc.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.identity.oidc_google`

- [ ] **Step 3: Write `oidc_google.py`**

```python
# api-gateway/app/modules/identity/oidc_google.py
"""Google sign-in.

The ID token is verified server-side against Google's JWKS. A profile supplied
by the client is never trusted — it is trivially forged.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import jwt
from jwt import PyJWKClient

from faue_core.errors.taxonomy import Unauthenticated

ISSUERS = {"https://accounts.google.com", "accounts.google.com"}
JWKS_URL = "https://www.googleapis.com/oauth2/v3/certs"

_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)


@dataclass(frozen=True)
class OAuthIdentity:
    provider: str
    provider_uid: str
    email: str | None
    email_verified: bool
    display_name: str | None = None


def _signing_key_for(token: str) -> Any:
    return _jwks_client.get_signing_key_from_jwt(token).key


async def verify_google(id_token: str, *, nonce: str, settings: Any) -> OAuthIdentity:
    try:
        payload = jwt.decode(
            id_token,
            _signing_key_for(id_token),
            algorithms=["RS256", "HS256"],
            audience=settings.google_client_id,
            options={"require": ["exp", "aud", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise Unauthenticated("invalid Google token") from exc

    if payload.get("iss") not in ISSUERS:
        raise Unauthenticated("unexpected issuer")
    if payload.get("nonce") != nonce:
        raise Unauthenticated("nonce mismatch")

    return OAuthIdentity(
        provider="google",
        provider_uid=payload["sub"],
        email=payload.get("email"),
        email_verified=bool(payload.get("email_verified")),
        display_name=payload.get("name"),
    )
```

- [ ] **Step 4: Write `oidc_apple.py`**

```python
# api-gateway/app/modules/identity/oidc_apple.py
"""Sign in with Apple.

Three Apple-specific rules that cost a day each if unknown:

1. `full_name` arrives ONLY on first authorization. Persist it immediately or
   it is gone permanently, even after revoking and re-authorising.
2. Private-relay addresses are real and working. Do not validate them away.
3. The client secret is an ES256 JWT with a hard six-month maximum life. Expiry
   breaks every Apple sign-in at once, which is why its expiry is an alert.
"""

from __future__ import annotations

import time
from typing import Any

import jwt
from jwt import PyJWKClient

from faue_core.errors.taxonomy import Unauthenticated

from app.modules.identity.oidc_google import OAuthIdentity

ISSUER = "https://appleid.apple.com"
JWKS_URL = "https://appleid.apple.com/auth/keys"
MAX_CLIENT_SECRET_LIFETIME = 15777000  # Apple's hard ceiling, ~6 months

_jwks_client = PyJWKClient(JWKS_URL, cache_keys=True)


def _signing_key_for(token: str) -> Any:
    return _jwks_client.get_signing_key_from_jwt(token).key


async def verify_apple(
    identity_token: str, *, nonce: str, full_name: str | None, settings: Any
) -> OAuthIdentity:
    try:
        payload = jwt.decode(
            identity_token,
            _signing_key_for(identity_token),
            algorithms=["RS256", "HS256"],
            audience=settings.apple_client_id,
            options={"require": ["exp", "aud", "iss", "sub"]},
        )
    except jwt.PyJWTError as exc:
        raise Unauthenticated("invalid Apple token") from exc

    if payload.get("iss") != ISSUER:
        raise Unauthenticated("unexpected issuer")
    if payload.get("nonce") != nonce:
        raise Unauthenticated("nonce mismatch")

    verified = payload.get("email_verified")
    return OAuthIdentity(
        provider="apple",
        provider_uid=payload["sub"],
        email=payload.get("email"),
        email_verified=verified in (True, "true"),
        display_name=full_name,
    )


def build_apple_client_secret(
    *, team_id: str, key_id: str, client_id: str, private_key: str,
    lifetime: int = MAX_CLIENT_SECRET_LIFETIME,
) -> str:
    """Generate the ES256 client secret. Regenerate before it expires — see the
    apple-secret-expiry runbook."""
    if lifetime > MAX_CLIENT_SECRET_LIFETIME:
        raise ValueError("Apple rejects client secrets living longer than ~6 months")

    now = int(time.time())
    return jwt.encode(
        {"iss": team_id, "iat": now, "exp": now + lifetime,
         "aud": ISSUER, "sub": client_id},
        private_key,
        algorithm="ES256",
        headers={"kid": key_id},
    )
```

- [ ] **Step 5: Run tests to verify they pass**

Run: `pytest tests/unit/test_oidc.py -v`
Expected: PASS (7 tests)

- [ ] **Step 6: Commit**

```bash
git add app/modules/identity/oidc_google.py app/modules/identity/oidc_apple.py tests/unit/test_oidc.py
git commit -m "feat(identity): Google and Apple sign-in

Server-side JWKS verification with issuer, audience and nonce checks.
Apple full_name captured on first authorization; private-relay accepted."
```

---

## Task 9: Account linking

**Files:**
- Create: `api-gateway/app/modules/identity/linking.py`
- Create: `api-gateway/tests/integration/test_linking.py`

**Interfaces:**
- Produces: `async def find_or_create_user(session, identity: OAuthIdentity | EmailIdentity, *, pepper: bytes) -> tuple[User, Workspace, bool]` returning `(user, workspace, is_new)`

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/integration/test_linking.py
"""Account linking.

One person, one account, several identities. Linking happens ONLY on a verified
email match — unverified auto-linking is an account-takeover path.
"""

from app.modules.identity.linking import find_or_create_user
from app.modules.identity.oidc_google import OAuthIdentity

PEPPER = b"test-pepper"


def google(email="a@b.com", verified=True, uid="g-1") -> OAuthIdentity:
    return OAuthIdentity("google", uid, email, verified, "Amara")


def apple(email="a@b.com", verified=True, uid="a-1") -> OAuthIdentity:
    return OAuthIdentity("apple", uid, email, verified, None)


async def test_first_sign_in_creates_a_user_and_workspace(session):
    user, workspace, is_new = await find_or_create_user(session, google(), pepper=PEPPER)
    await session.flush()

    assert is_new is True
    assert workspace.owner_user_id == user.id


async def test_same_provider_identity_returns_the_same_user(session):
    first, _, _ = await find_or_create_user(session, google(), pepper=PEPPER)
    await session.flush()
    second, _, is_new = await find_or_create_user(session, google(), pepper=PEPPER)

    assert second.id == first.id
    assert is_new is False


async def test_verified_email_across_providers_links_to_one_user(session):
    first, _, _ = await find_or_create_user(session, google(), pepper=PEPPER)
    await session.flush()
    second, _, is_new = await find_or_create_user(session, apple(), pepper=PEPPER)

    assert second.id == first.id, "verified email match should link"
    assert is_new is False


async def test_unverified_email_never_links(session):
    """The account-takeover path this rule exists to close."""
    first, _, _ = await find_or_create_user(session, google(), pepper=PEPPER)
    await session.flush()

    second, _, is_new = await find_or_create_user(
        session, apple(verified=False), pepper=PEPPER
    )
    assert second.id != first.id
    assert is_new is True


async def test_different_emails_create_different_users(session):
    first, _, _ = await find_or_create_user(session, google(), pepper=PEPPER)
    await session.flush()
    second, _, _ = await find_or_create_user(
        session, apple(email="other@b.com", uid="a-2"), pepper=PEPPER
    )
    assert second.id != first.id


async def test_apple_display_name_is_persisted_on_first_sight(session):
    from sqlalchemy import select
    from faue_db.gateway.models import AuthIdentity

    await find_or_create_user(session, OAuthIdentity("apple", "a-9", "n@b.com", True, "Tunde"),
                              pepper=PEPPER)
    await session.flush()

    row = (await session.execute(
        select(AuthIdentity).where(AuthIdentity.provider_uid == "a-9")
    )).scalar_one()
    assert row.display_name == "Tunde"
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/integration/test_linking.py -v`
Expected: FAIL — `ModuleNotFoundError: app.modules.identity.linking`

- [ ] **Step 3: Write the implementation**

```python
# api-gateway/app/modules/identity/linking.py
"""Account linking.

Linking occurs ONLY on a verified email match. An unverified address is
attacker-controllable, so auto-linking on one would let anyone claim an existing
account by signing up with its email at a provider that does not verify.
"""

from __future__ import annotations

from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from faue_core.crypto.blind_index import blind_index, normalise
from faue_db.base import uuid7
from faue_db.gateway.models import AuthIdentity, User, Workspace, WorkspaceMember

from app.modules.identity.oidc_google import OAuthIdentity
from app.modules.identity.workspace import create_user_with_workspace


async def find_or_create_user(
    session: AsyncSession, identity: OAuthIdentity, *, pepper: bytes
) -> tuple[User, Workspace, bool]:
    """Resolve an identity to a user, linking or creating as the rules allow."""
    now = datetime.now(UTC)

    # 1. exact provider identity — the common case for a returning user
    existing = (await session.execute(
        select(AuthIdentity).where(
            AuthIdentity.provider == identity.provider,
            AuthIdentity.provider_uid == identity.provider_uid,
        )
    )).scalar_one_or_none()

    if existing is not None:
        existing.last_used_at = now
        workspace = await _workspace_for(session, existing.user_id)
        user = (await session.execute(
            select(User).where(User.id == existing.user_id)
        )).scalar_one()
        return user, workspace, False

    # 2. link on a VERIFIED email match only
    linked_user_id = None
    email_bidx = None
    if identity.email:
        email_bidx = blind_index(identity.email, pepper)
        if identity.email_verified:
            linked_user_id = (await session.execute(
                select(AuthIdentity.user_id).where(
                    AuthIdentity.email_bidx == email_bidx,
                    AuthIdentity.email_verified.is_(True),
                )
            )).scalars().first()

    # 3. create when nothing links
    if linked_user_id is None:
        user, workspace = await create_user_with_workspace(session)
        is_new = True
    else:
        user = (await session.execute(
            select(User).where(User.id == linked_user_id)
        )).scalar_one()
        workspace = await _workspace_for(session, linked_user_id)
        is_new = False

    session.add(AuthIdentity(
        id=uuid7(),
        user_id=user.id,
        provider=identity.provider,
        provider_uid=identity.provider_uid,
        email_enc=None,                       # encryptor wired at session setup
        email_bidx=email_bidx,
        email_verified=identity.email_verified,
        display_name=identity.display_name,   # Apple sends this once only
        linked_at=now,
        last_used_at=now,
    ))

    return user, workspace, is_new


async def _workspace_for(session: AsyncSession, user_id) -> Workspace:
    workspace_id = (await session.execute(
        select(WorkspaceMember.workspace_id).where(WorkspaceMember.user_id == user_id)
    )).scalars().first()
    return (await session.execute(
        select(Workspace).where(Workspace.id == workspace_id)
    )).scalar_one()
```

- [ ] **Step 4: Run tests to verify they pass**

Run: `pytest tests/integration/test_linking.py -v`
Expected: PASS (6 tests)

- [ ] **Step 5: Commit**

```bash
git add app/modules/identity/linking.py tests/integration/test_linking.py
git commit -m "feat(identity): account linking on verified email only

Unverified addresses never auto-link — that is an account-takeover path."
```

---

## Task 10: Wire the auth endpoints

**Files:**
- Modify: `api-gateway/app/api/v1/auth.py`
- Modify: `api-gateway/app/modules/identity/service.py`
- Modify: `api-gateway/app/deps.py`
- Create: `api-gateway/tests/contract/test_auth_endpoints.py`

**Interfaces:**
- Consumes: everything from Tasks 4–9.
- Produces: working `/v1/auth/*` endpoints matching `gateway.v1.yaml`.

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/contract/test_auth_endpoints.py
"""Auth endpoints against the OpenAPI contract."""

import pytest


async def test_link_request_always_returns_202(client):
    """Whether or not the address exists. Revealing which do is enumeration."""
    for email in ("known@b.com", "never-seen@b.com"):
        response = await client.post(
            "/v1/auth/link/request",
            json={"email": email, "session_challenge": "c" * 32},
        )
        assert response.status_code == 202
        assert response.json()["expires_in"] == 600


async def test_link_request_rejects_a_short_challenge(client):
    response = await client.post(
        "/v1/auth/link/request", json={"email": "a@b.com", "session_challenge": "short"}
    )
    assert response.status_code == 422


async def test_full_sign_in_flow(client, recorded_emails):
    await client.post(
        "/v1/auth/link/request",
        json={"email": "a@b.com", "session_challenge": "c" * 32},
    )
    token = recorded_emails.sent[0][1].split("t=")[1]

    response = await client.post(
        "/v1/auth/link/consume",
        json={"token": token, "session_challenge": "c" * 32},
    )
    assert response.status_code == 200

    body = response.json()
    assert set(body) == {"access_token", "refresh_token", "expires_in", "is_new_user"}
    assert body["is_new_user"] is True
    assert body["expires_in"] == 900


async def test_consume_is_not_available_over_get(client):
    """A GET that consumed the token would be spent by mail scanners."""
    assert (await client.get("/v1/auth/link/consume")).status_code == 405


async def test_reused_link_returns_410_with_a_problem_document(client, recorded_emails):
    await client.post("/v1/auth/link/request",
                      json={"email": "a@b.com", "session_challenge": "c" * 32})
    token = recorded_emails.sent[0][1].split("t=")[1]
    payload = {"token": token, "session_challenge": "c" * 32}

    await client.post("/v1/auth/link/consume", json=payload)
    response = await client.post("/v1/auth/link/consume", json=payload)

    assert response.status_code == 410
    assert response.headers["content-type"].startswith("application/problem+json")
    assert response.json()["type"] == "link_already_used"


async def test_cross_device_returns_409_with_a_code(client, recorded_emails):
    await client.post("/v1/auth/link/request",
                      json={"email": "a@b.com", "session_challenge": "c" * 32})
    token = recorded_emails.sent[0][1].split("t=")[1]

    response = await client.post(
        "/v1/auth/link/consume",
        json={"token": token, "session_challenge": "a-laptop"},
    )
    assert response.status_code == 409
    assert response.json()["device_code_required"] is True
    assert len(response.json()["device_code"]) == 6


async def test_refresh_rotates_and_reuse_returns_401(client, recorded_emails):
    await client.post("/v1/auth/link/request",
                      json={"email": "a@b.com", "session_challenge": "c" * 32})
    token = recorded_emails.sent[0][1].split("t=")[1]
    session = (await client.post("/v1/auth/link/consume",
                                 json={"token": token, "session_challenge": "c" * 32})).json()

    rotated = await client.post("/v1/auth/refresh",
                                json={"refresh_token": session["refresh_token"]})
    assert rotated.status_code == 200
    assert rotated.json()["refresh_token"] != session["refresh_token"]

    reused = await client.post("/v1/auth/refresh",
                               json={"refresh_token": session["refresh_token"]})
    assert reused.status_code == 401
    assert reused.json()["type"] == "refresh_reuse_detected"


async def test_authenticated_request_carries_the_workspace(client, authed_headers):
    response = await client.get("/v1/me", headers=authed_headers)
    assert response.status_code in (200, 501)   # 501 until /me lands in slice 2
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/contract/test_auth_endpoints.py -v`
Expected: FAIL — handlers raise `NotImplementedError`.

- [ ] **Step 3: Implement `IdentityService`**

```python
# api-gateway/app/modules/identity/service.py
"""IdentityService — the interface other modules depend on.

Modules depend on this class, never on internals. Domain exceptions only; the
boundary translates them to RFC 7807.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from app.modules.identity import linking, magic_link, oidc_apple, oidc_google, tokens
from app.modules.identity.email_sender import EmailSender
from app.modules.identity.oidc_google import OAuthIdentity


@dataclass(frozen=True)
class SignInResult:
    access_token: str
    refresh_token: str
    expires_in: int
    is_new_user: bool


class IdentityService:
    def __init__(self, redis: Any, sender: EmailSender, settings: Any) -> None:
        self._redis = redis
        self._sender = sender
        self._settings = settings

    async def request_magic_link(self, *, email: str, session_challenge: str) -> None:
        await magic_link.request_link(
            self._redis, self._sender,
            email=email, session_challenge=session_challenge, settings=self._settings,
        )

    async def consume_magic_link(
        self, session: AsyncSession, *, token: str,
        session_challenge: str | None, device_code: str | None,
    ) -> SignInResult:
        result = await magic_link.consume_link(
            self._redis, token=token, session_challenge=session_challenge,
            device_code=device_code, settings=self._settings,
        )
        identity = OAuthIdentity(
            provider="magic_link", provider_uid=result.identifier,
            email=result.identifier, email_verified=True, display_name=None,
        )
        return await self._sign_in(session, identity)

    async def sign_in_google(
        self, session: AsyncSession, *, id_token: str, nonce: str
    ) -> SignInResult:
        identity = await oidc_google.verify_google(
            id_token, nonce=nonce, settings=self._settings
        )
        return await self._sign_in(session, identity)

    async def sign_in_apple(
        self, session: AsyncSession, *, identity_token: str,
        nonce: str, full_name: str | None,
    ) -> SignInResult:
        identity = await oidc_apple.verify_apple(
            identity_token, nonce=nonce, full_name=full_name, settings=self._settings
        )
        return await self._sign_in(session, identity)

    async def refresh(self, session: AsyncSession, *, refresh_token: str) -> SignInResult:
        issued = await tokens.rotate_refresh(
            session, refresh_token, settings=self._settings
        )
        return SignInResult(issued.access_token, issued.refresh_token,
                            issued.expires_in, is_new_user=False)

    async def logout(self, session: AsyncSession, *, refresh_token: str) -> None:
        await tokens.revoke_family_for_token(session, refresh_token)

    async def _sign_in(
        self, session: AsyncSession, identity: OAuthIdentity
    ) -> SignInResult:
        pepper = self._settings.blind_index_pepper.get_secret_value().encode()
        user, workspace, is_new = await linking.find_or_create_user(
            session, identity, pepper=pepper
        )
        await session.flush()
        issued = await tokens.issue_session(
            session, user.id, workspace.id, settings=self._settings
        )
        return SignInResult(issued.access_token, issued.refresh_token,
                            issued.expires_in, is_new)
```

- [ ] **Step 4: Replace the auth router bodies**

Replace `api-gateway/app/api/v1/auth.py` handlers with real implementations. The request model enforces the challenge length so a short one is `422` rather than accepted:

```python
from typing import Annotated

from fastapi import APIRouter, Depends, Response, status
from pydantic import BaseModel, EmailStr, Field

from app.deps import CurrentUserDep, DbDep, IdentityServiceDep

router = APIRouter(tags=["auth"])


class LinkRequest(BaseModel):
    email: EmailStr
    session_challenge: str = Field(min_length=16, max_length=128)


class LinkConsume(BaseModel):
    token: str
    session_challenge: str | None = None
    device_code: str | None = None


class RefreshRequest(BaseModel):
    refresh_token: str


@router.post("/auth/link/request", status_code=status.HTTP_202_ACCEPTED)
async def request_magic_link(
    body: LinkRequest, identity: IdentityServiceDep
) -> dict:
    """Always 202. Revealing which addresses exist is enumeration."""
    await identity.request_magic_link(
        email=body.email, session_challenge=body.session_challenge
    )
    return {"expires_in": 600}


@router.post("/auth/link/consume", status_code=status.HTTP_200_OK)
async def consume_magic_link(
    body: LinkConsume, identity: IdentityServiceDep, db: DbDep
) -> dict:
    result = await identity.consume_magic_link(
        db, token=body.token, session_challenge=body.session_challenge,
        device_code=body.device_code,
    )
    await db.commit()
    return result.__dict__
```

Repeat the same shape for `/auth/oauth/google`, `/auth/oauth/apple`, `/auth/refresh`, and `/auth/logout`.

- [ ] **Step 5: Add the exception handlers and dependencies**

In `app/main.py`, register the RFC 7807 handler so domain exceptions become problem documents:

```python
from fastapi import Request
from fastapi.responses import JSONResponse

from faue_core.errors.problem import to_problem
from faue_core.errors.taxonomy import DeviceCodeRequired, FaueError


def _register_error_handlers(app: FastAPI) -> None:
    @app.exception_handler(FaueError)
    async def handle_domain_error(request: Request, exc: FaueError) -> JSONResponse:
        trace_id = request.headers.get("X-Trace-Id", "")

        # the cross-device path returns its code in the body, not as an error
        if isinstance(exc, DeviceCodeRequired):
            return JSONResponse(
                status_code=exc.status,
                content={"device_code_required": True, "device_code": exc.device_code},
            )

        return JSONResponse(
            status_code=exc.status,
            content=to_problem(exc, trace_id=trace_id),
            media_type="application/problem+json",
        )
```

Call `_register_error_handlers(app)` inside `create_app`, and implement `current_user` in `deps.py` using `tokens.verify_access_token`.

- [ ] **Step 6: Run the whole suite**

Run: `cd api-gateway && pytest -q`
Expected: PASS — the 11 existing quiz tests plus everything from Tasks 4–10.

- [ ] **Step 7: Commit**

```bash
git add app/ tests/
git commit -m "feat(identity): wire auth endpoints

Magic link, Google, Apple, refresh and logout against the v1 contract.
Domain exceptions become RFC 7807 problem documents at the boundary."
```

---

## Task 11: Username and the real email provider

**Files:**
- Modify: `api-gateway/app/api/v1/auth.py`
- Modify: `api-gateway/app/modules/identity/email_sender.py`
- Create: `api-gateway/tests/contract/test_username.py`

**Interfaces:**
- Produces: `POST /v1/auth/username`, and a working `ProviderEmailSender`.

- [ ] **Step 1: Write the failing test**

```python
# api-gateway/tests/contract/test_username.py
async def test_setting_a_username(client, authed_headers):
    response = await client.post(
        "/v1/auth/username", json={"username": "seagatoo"}, headers=authed_headers
    )
    assert response.status_code == 200
    assert response.json()["username"] == "seagatoo"


async def test_usernames_are_unique_case_insensitively(client, authed_headers, other_headers):
    await client.post("/v1/auth/username", json={"username": "seagatoo"},
                      headers=authed_headers)
    clash = await client.post("/v1/auth/username", json={"username": "SeaGatoo"},
                              headers=other_headers)

    assert clash.status_code == 409
    assert clash.json()["type"] == "username_taken"


async def test_invalid_usernames_are_rejected(client, authed_headers):
    for bad in ("ab", "a" * 25, "has space", "emoji🙂", ""):
        response = await client.post("/v1/auth/username", json={"username": bad},
                                     headers=authed_headers)
        assert response.status_code == 422, bad
```

- [ ] **Step 2: Run to verify failure**

Run: `pytest tests/contract/test_username.py -v`
Expected: FAIL — handler raises `NotImplementedError`.

- [ ] **Step 3: Implement the endpoint**

```python
class UsernameRequest(BaseModel):
    username: str = Field(min_length=3, max_length=24, pattern=r"^[a-zA-Z0-9_.]+$")


@router.post("/auth/username", status_code=status.HTTP_200_OK)
async def set_username(
    body: UsernameRequest, user: CurrentUserDep, db: DbDep
) -> dict:
    from sqlalchemy.exc import IntegrityError

    from faue_core.errors.taxonomy import UsernameTaken
    from faue_db.gateway.models import Profile

    profile = await db.get(Profile, user.user_id)
    if profile is None:
        profile = Profile(user_id=user.user_id, workspace_id=user.workspace_id)
        db.add(profile)

    profile.username = body.username
    try:
        await db.commit()
    except IntegrityError as exc:
        await db.rollback()
        raise UsernameTaken("that username is taken", field="username") from exc

    return {"user_id": str(user.user_id), "username": profile.username}
```

- [ ] **Step 4: Verify the Resend sender without hitting the network**

`ResendEmailSender` is already written in Task 6. Test it against a mock transport rather than the live API:

```python
# api-gateway/tests/unit/test_resend_sender.py
import httpx
import pytest

from app.modules.identity.email_sender import ResendEmailSender, render_magic_link_email
from faue_core.errors.taxonomy import ServiceUnavailable


def transport(handler) -> httpx.MockTransport:
    return httpx.MockTransport(handler)


async def test_request_shape_matches_the_resend_api(monkeypatch):
    captured = {}

    def handler(request: httpx.Request) -> httpx.Response:
        captured["url"] = str(request.url)
        captured["auth"] = request.headers["authorization"]
        captured["idempotency"] = request.headers.get("idempotency-key")
        captured["body"] = request.read().decode()
        return httpx.Response(200, json={"id": "re_123"})

    sender = ResendEmailSender("re_test", "mail.faueofficial.com")
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda **kw: httpx.AsyncClient(transport=transport(handler), **kw),
    )

    await sender.send_magic_link("a@b.com", "https://faueofficial.com/auth/verify?t=x",
                                 idempotency_key="abc123")

    assert captured["url"] == "https://api.resend.com/emails"
    assert captured["auth"] == "Bearer re_test"
    assert captured["idempotency"] == "abc123"
    assert "mail.faueofficial.com" in captured["body"]


async def test_rate_limit_surfaces_as_service_unavailable(monkeypatch):
    """Resend allows 2 requests/second by default. A 429 must not tell the user
    their address is wrong."""
    def handler(request: httpx.Request) -> httpx.Response:
        return httpx.Response(429, json={"message": "Too many requests"})

    sender = ResendEmailSender("re_test", "mail.faueofficial.com")
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda **kw: httpx.AsyncClient(transport=transport(handler), **kw),
    )

    with pytest.raises(ServiceUnavailable):
        await sender.send_magic_link("a@b.com", "https://x", idempotency_key="k")


async def test_network_failure_surfaces_as_service_unavailable(monkeypatch):
    def handler(request: httpx.Request) -> httpx.Response:
        raise httpx.ConnectError("no route to host")

    sender = ResendEmailSender("re_test", "mail.faueofficial.com")
    monkeypatch.setattr(
        httpx, "AsyncClient",
        lambda **kw: httpx.AsyncClient(transport=transport(handler), **kw),
    )

    with pytest.raises(ServiceUnavailable):
        await sender.send_magic_link("a@b.com", "https://x", idempotency_key="k")


def test_the_email_contains_the_link_and_an_expiry_notice():
    html = render_magic_link_email("https://faueofficial.com/auth/verify?t=abc")
    assert "https://faueofficial.com/auth/verify?t=abc" in html
    assert "10 minutes" in html
```

- [ ] **Step 5: Configure the Resend domain (operational, not code)**

Login depends on delivery, so this is launch-blocking:

1. Add `mail.faueofficial.com` as a domain in Resend.
2. Publish the SPF, DKIM and DMARC records Resend provides. Use the **subdomain**, so a reputation problem never touches the apex domain.
3. Wait for verification, then send a real test to a Gmail address and confirm it lands in the inbox rather than spam.
4. On staging, verify both paths with `delivered@resend.dev` and `bounced@resend.dev`.
5. Store the key as `RESEND_API_KEY` in the Railway secret store.

- [ ] **Step 6: Run the full suite**

Run: `cd api-gateway && pytest -q`
Expected: PASS

- [ ] **Step 7: Commit**

```bash
git add app/ tests/
git commit -m "feat(identity): username endpoint and Resend email sender

Sender verified against a mock transport; no test makes a network call."
```

---

## Task 12: End-to-end verification

**Files:**
- Create: `api-gateway/tests/integration/test_signin_e2e.py`

- [ ] **Step 1: Write the end-to-end test**

```python
# api-gateway/tests/integration/test_signin_e2e.py
"""The whole slice, exercised as a user would."""

from sqlalchemy import select

from faue_db.gateway.models import AuthIdentity, Workspace, WorkspaceMember


async def test_new_user_signs_in_and_gets_a_workspace(client, recorded_emails, session):
    await client.post("/v1/auth/link/request",
                      json={"email": "amara@example.com", "session_challenge": "c" * 32})
    token = recorded_emails.sent[0][1].split("t=")[1]

    signed_in = (await client.post(
        "/v1/auth/link/consume",
        json={"token": token, "session_challenge": "c" * 32},
    )).json()
    assert signed_in["is_new_user"] is True

    identity = (await session.execute(
        select(AuthIdentity).where(AuthIdentity.provider == "magic_link")
    )).scalar_one()

    workspace = (await session.execute(
        select(Workspace).where(Workspace.owner_user_id == identity.user_id)
    )).scalar_one()
    assert workspace.kind == "personal"

    members = (await session.execute(
        select(WorkspaceMember).where(WorkspaceMember.workspace_id == workspace.id)
    )).scalars().all()
    assert len(members) == 1


async def test_returning_user_keeps_the_same_workspace(client, recorded_emails, session):
    async def sign_in() -> dict:
        recorded_emails.sent.clear()
        await client.post("/v1/auth/link/request",
                          json={"email": "amara@example.com", "session_challenge": "c" * 32})
        token = recorded_emails.sent[0][1].split("t=")[1]
        return (await client.post("/v1/auth/link/consume",
                                  json={"token": token, "session_challenge": "c" * 32})).json()

    first, second = await sign_in(), await sign_in()
    assert first["is_new_user"] is True
    assert second["is_new_user"] is False

    workspaces = (await session.execute(select(Workspace))).scalars().all()
    assert len(workspaces) == 1


async def test_no_pii_appears_in_logs(client, recorded_emails, caplog):
    """CI enforces the pattern check; this proves it holds at runtime."""
    import logging

    with caplog.at_level(logging.DEBUG):
        await client.post("/v1/auth/link/request",
                          json={"email": "amara@example.com", "session_challenge": "c" * 32})

    logged = " ".join(record.getMessage() for record in caplog.records)
    assert "amara@example.com" not in logged
```

- [ ] **Step 2: Run it**

Run: `cd api-gateway && pytest tests/integration/test_signin_e2e.py -v`
Expected: PASS (3 tests)

- [ ] **Step 3: Run everything, in every repo**

```bash
cd faue-core   && pytest -q      # 23 passing
cd ../faue-db  && pytest -q      # 10 + migration tests
cd ../ase      && pytest -q      # 8 passing
cd ../api-gateway && pytest -q   # 11 + everything from this slice
```

- [ ] **Step 4: Manual smoke test**

```bash
cd faue-infra && docker compose up -d
cd ../faue-db && DATABASE_URL=... alembic upgrade head
cd ../api-gateway && make dev

curl -X POST localhost:8000/v1/auth/link/request \
  -H 'Content-Type: application/json' \
  -d '{"email":"you@example.com","session_challenge":"0123456789abcdef0123456789abcdef"}'
# → 202 {"expires_in":600}
# the link is printed by RecordingEmailSender in local mode
```

- [ ] **Step 5: Update documentation status**

Mark identity as implemented in `docs/90-meta/doc-status.md` and record any contract change in `docs/30-contracts/CHANGELOG.md`.

- [ ] **Step 6: Commit**

```bash
git add tests/integration/test_signin_e2e.py
git commit -m "test: end-to-end sign-in with workspace bootstrap"
```

---

## Self-review notes

**Spec coverage.** Slice 0 covers §11.3 (environments) and §8.5 (migrations). Slice 1 covers §4.1 (authentication) in full — magic link with all three failure modes, Google, Apple, linking, session lifecycle — plus ADR 0021's workspace bootstrap.

**Deliberately excluded, and why:**
- Phone OTP — `M1-2` per the spec.
- `/me`, profile, consent enforcement — slice 2. Task 10's last test tolerates `501` for exactly this reason.
- Manual account linking from settings — `M1-2`.
- Nothing is blocked on the email provider any more: Resend is chosen and implemented in Task 6, verified against a mock transport in Task 11. Only the domain verification is operational work.
- Rate limiting middleware — the magic-link limiter is inline here; the general edge limiter belongs with slice 2's shared dependencies.

**Known interface consistency risks checked:**
- `OAuthIdentity` is defined once in `oidc_google.py` and imported by `oidc_apple.py` and `linking.py`.
- `SessionTokens` is returned by both `issue_session` and `rotate_refresh`.
- `find_or_create_user` returns `(user, workspace, is_new)` everywhere it is called.
- `settings.blind_index_pepper` is a `SecretStr`, so `.get_secret_value()` is required — done in `IdentityService._sign_in`.

**Fixtures Task 4 assumes exist** and which the executor must create in `api-gateway/tests/conftest.py` before Task 4: `session` (async DB session against a migrated test database), `redis` (a real Redis or `fakeredis`, since the consume path uses `EVAL`), `settings` (test settings), `client` (httpx `AsyncClient` against the app), `recorded_emails` (the `RecordingEmailSender` bound into the app), `authed_headers` / `other_headers` (two signed-in users).

Building those fixtures is the first thing Task 4 needs; it is called out here rather than left to be discovered.
