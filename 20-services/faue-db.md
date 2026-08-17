# faue-db

**Stage:** MVP · **Repo:** `faueofficial/faue-db` · **ADR:** [0004](../80-adr/0004-single-alembic-project-in-faue-db.md)

All SQLAlchemy models and the single Alembic project. Services install it as a pinned dependency.

---

## 1. Layout

```
faue-db/
├─ faue_db/
│  ├─ base.py            Base, naming convention, UUIDv7, mixins, encrypted types
│  ├─ registry.py        imports every model → one MetaData for autogenerate
│  ├─ types.py           EncryptedStr, BlindIndex, Vector
│  ├─ gateway/models.py  schema="gateway"
│  ├─ ase/models.py      schema="ase"
│  ├─ catalog/models.py  schema="catalog"   (M1-2)
│  └─ media/models.py    schema="media"     (M1-2)
├─ migrations/
│  ├─ env.py             target_metadata = registry.metadata
│  ├─ script.py.mako
│  └─ versions/          one linear history, all schemas
├─ tests/
├─ CODEOWNERS
└─ pyproject.toml
```

Installed pinned:

```
faue-db @ git+ssh://git@github.com/faueofficial/faue-db.git@v0.4.2
```

---

## 2. Why one project

Autogenerate needs the models. Co-locating models and migrations is the only way to get a **mechanical** guarantee rather than a convention: a model edited without a migration cannot merge.

Centralising the schema does not mean losing ownership — see §5.

---

## 3. Conventions

```python
# base.py
NAMING_CONVENTION = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s",
    "pk": "pk_%(table_name)s",
}
```

Explicit naming matters more than it looks: without it, Alembic generates unnamed constraints that cannot be dropped cleanly in a later migration, and every downgrade breaks.

Rules:

- Primary keys are UUIDv7, generated in Python so the value is known before insert.
- Timestamps are `TIMESTAMPTZ`, UTC, named `*_at`.
- **No `ForeignKey` across schemas.** Cross-schema references are plain `UUID` columns. The linter enforces this.
- Encrypted columns use the `EncryptedStr` type and the `_enc` suffix.
- Blind indexes use `BlindIndex` and the `_bidx` suffix.
- Every model carries a docstring naming its owning service and stage.
- **User-owned models inherit `WorkspaceScopedMixin`**, which supplies `workspace_id UUID NOT NULL` and its index ([ADR 0021](../80-adr/0021-workspace-tenancy-model.md)). A linter check fails the build if a model with a `user_id` lacks the mixin — that is what stops the reservation quietly rotting.

---

## 4. CI gates

```yaml
- name: Migrations apply cleanly
  run: alembic upgrade head

- name: Models match migrations
  run: |
    alembic check          # non-empty autogenerate diff fails the build

- name: Downgrades work
  run: |
    alembic downgrade -1
    alembic upgrade head

- name: No cross-schema foreign keys
  run: python -m tests.lint_cross_schema_fk

- name: Every table has a RoPA entry
  run: python -m tests.lint_ropa_coverage
```

Each gate exists because of a specific, recurring failure:

- **`alembic check`** — the guarantee the whole design rests on. Without it, this repository is just a folder.
- **Downgrade test** — a broken downgrade is discovered during an incident otherwise, which is the worst possible time.
- **Cross-schema FK lint** — one accidental foreign key makes the future service split impossible, and it is invisible until then.
- **RoPA coverage** — a new column collecting personal data without a register entry is a compliance gap that nobody notices until an audit.

---

## 5. Ownership

Centralised location, distributed ownership, enforced two ways.

```
# CODEOWNERS
/faue_db/gateway/   @gateway-owner
/faue_db/ase/       @ase-owner
/faue_db/catalog/   @catalog-owner
/faue_db/media/     @media-owner
/migrations/        @backend-lead
```

And at the database, which is the enforcement that actually holds:

```sql
CREATE ROLE faue_migrator LOGIN;          -- owns DDL, used only by the migration job
CREATE ROLE faue_gateway  LOGIN;
CREATE ROLE faue_ase      LOGIN;

GRANT USAGE ON SCHEMA gateway TO faue_gateway;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gateway TO faue_gateway;
REVOKE ALL ON SCHEMA ase, catalog, media FROM faue_gateway;

GRANT USAGE ON SCHEMA ase TO faue_ase;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ase TO faue_ase;
REVOKE ALL ON SCHEMA gateway, catalog, media FROM faue_ase;

REVOKE UPDATE, DELETE ON gateway.audit_log      FROM faue_gateway;
REVOKE UPDATE, DELETE ON gateway.quiz_responses FROM faue_gateway;
```

Cross-schema access fails at the database, not by politeness. Service roles hold DML only and cannot alter tables, so runtime code can never migrate accidentally.

---

## 6. Deploy ordering

Fixed, and not negotiable:

```
1  Run migrations (EXPAND ONLY — additive, nullable, new tables)
2  Deploy service code
3  A LATER release contracts (drop columns, tighten constraints)
```

Expand-contract is what makes rollback safe. A breaking migration shipped alongside the code that needs it means rolling back the code leaves the database ahead of it — and rolling back the database loses data written in between.

### Adding a non-nullable column

```
Release 1  add the column nullable, with a default
Release 2  backfill
Release 3  set NOT NULL
```

Three releases, no downtime, rollback safe at every point.

### Renaming a column

```
Release 1  add the new column; write to both, read the old
Release 2  backfill; read the new
Release 3  drop the old
```

Never `ALTER TABLE ... RENAME COLUMN` on a live table with running code.

---

## 7. Local workflow

```bash
# after editing a model
alembic revision --autogenerate -m "add wear_count to vault_items"

# review the generated migration — autogenerate is a draft, not an answer
$EDITOR migrations/versions/<rev>_add_wear_count_to_vault_items.py

alembic upgrade head
alembic downgrade -1 && alembic upgrade head   # prove the downgrade works
pytest
```

**Always read the generated migration.** Autogenerate misses column renames (it emits a drop and an add, losing data), server defaults, index changes on expressions, and anything involving `vector` columns. Treat it as a starting point.

---

## 8. Vector columns

```python
from pgvector.sqlalchemy import Vector

class VaultEmbedding(Base):
    __tablename__ = "vault_embeddings"
    __table_args__ = {"schema": "ase"}
    item_id  = mapped_column(UUID, primary_key=True)
    model_id = mapped_column(Text, primary_key=True)
    embedding = mapped_column(Vector())     # dimension varies by model
```

Dimension is deliberately unconstrained at the column level, because several embedding models coexist during a migration and they have different dimensions. HNSW indexes are created per `model_id` in raw SQL within the migration, since autogenerate does not handle partial vector indexes.

---

## 9. Releasing

Semantic versioning, tagged. Services pin exact versions.

| Change | Bump |
|---|---|
| New table or nullable column | Minor |
| New index | Patch |
| Column removed or retyped | **Major** — coordinate with every service |
| Constraint tightened | **Major** |

A major bump means every dependent service updates its pin in the same release cycle. That coordination is the cost of one migration history, and it is worth paying at a two-person team. The exit path, if the team grows, is splitting `faue_db/<service>` into per-service Alembic projects — mechanical, because the schemas are already disjoint and role-isolated.
