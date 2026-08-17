# Conventions

**Stage:** MVP · **Applies to:** every FAUE repository

Conventions exist so that reading unfamiliar code in this system requires no negotiation. Where a convention and a preference conflict, the convention wins; change the convention in a pull request rather than in one file.

---

## 1. Language and tooling

| Concern | Choice |
|---|---|
| Language | Python 3.12 |
| Web framework | FastAPI |
| ORM | SQLAlchemy 2.0, async |
| Validation | Pydantic v2 |
| Migrations | Alembic, single project in `faue-db` |
| Dependencies | `pip` + `pip-tools`, single root virtualenv, shared `constraints.txt` |
| Lint / format | `ruff` (lint + format) |
| Types | `mypy --strict` over `app/` |
| Tests | `pytest`, `pytest-asyncio`, `testcontainers` for integration |
| Task runner | `make` |

Frontend surfaces (`faue-app`, `faue-web`, `faue-admin`) follow their own ecosystem conventions; only the API contract and design tokens are shared.

### Dependency management

`faue-core` owns the dependency contract:

```
faue-core/requirements/
├─ base.in / base.txt          # shared runtime: FastAPI, SQLAlchemy, Pydantic, OTel
├─ web.in / web.txt            # HTTP-serving services
├─ worker.in / worker.txt      # background workers
├─ ml.in / ml.txt              # ase only — embeddings, vision, image handling
├─ dev.in / dev.txt            # lint, types, tests
└─ constraints.txt             # shared pins; every service resolves against this
```

Rules:

- Add a dependency to the `.in` file for the narrowest role that needs it.
- Recompile with `pip-compile --constraint constraints.txt <role>.in`.
- Never pin a shared library version in a service; that is what `constraints.txt` is for.
- `ml` requirements install into `ase` only. They must never appear in the gateway image.

```bash
# fresh machine
python3.12 -m venv .venv && source .venv/bin/activate
pip install -r faue-core/requirements/dev.txt
pip install -e ./faue-core -e ./faue-db -e ./api-gateway -e ./ase
```

---

## 2. Repository layout

Every Python service follows the same shape, so a file's purpose is predictable from its path:

```
<service>/
├─ app/
│  ├─ main.py            # app factory, middleware, lifespan
│  ├─ config.py          # settings, one Pydantic Settings class
│  ├─ deps.py            # FastAPI dependencies
│  ├─ api/               # routers only — no business logic
│  ├─ modules/           # bounded contexts; business logic lives here
│  ├─ clients/           # outbound calls to other services
│  ├─ events/            # publishers, consumers, handlers
│  └─ workers/           # background jobs
├─ tests/{unit,integration,contract}/
├─ Dockerfile
├─ Makefile
└─ pyproject.toml
```

**Routers contain no business logic.** A router validates input, calls one module function, and shapes the response. If a router has a branch that is not about HTTP, that branch belongs in a module.

**Modules do not import each other's internals.** A module exposes an interface class; other modules depend on that class, never on its private functions or its tables. This is what makes a module extractable into a service later.

---

## 3. Naming

| Thing | Rule | Example |
|---|---|---|
| Module, package, file | `snake_case` | `style_context.py` |
| Class | `PascalCase` | `LookRenderer` |
| Function, variable | `snake_case` | `resolve_style_context` |
| Constant | `UPPER_SNAKE` | `MAX_TOOL_ROUNDS` |
| Database table | `snake_case`, plural | `vault_items` |
| Database column | `snake_case`, singular | `body_shape` |
| Encrypted column | suffix `_enc` | `email_enc` |
| Blind index column | suffix `_bidx` | `email_bidx` |
| Event | `noun.past_tense_verb`, dotted | `look.completed` |
| REST path | plural nouns, kebab where multi-word | `/v1/vault-items` |
| Feature flag | `snake_case`, area-prefixed | `looks_generative_renderer` |
| Prompt file | `prompts/<task>/v<n>.md` | `prompts/look.reasoning/v2.md` |

Never abbreviate a domain term. `fabric_analysis`, not `fab_an`. The exceptions are established acronyms: `id`, `url`, `api`, `dna`, `pii`, `otp`, `ttl`.

---

## 4. HTTP API

- One versioned surface: `/v1/*`. Admin lives at `/admin/v1/*` under a separate auth realm.
- Resource-oriented paths, verbs only for actions that are genuinely not CRUD (`/v1/looks/{id}/regenerate`).
- `POST` returns `201` with the created resource, or `202` with a job envelope for asynchronous work.
- Errors are RFC 7807 problem documents. See [`40-frontend/error-model.md`](../40-frontend/error-model.md).
- Every endpoint declares its required consent purposes and authorization scope in its OpenAPI description.
- Pagination is cursor-based everywhere. See [`40-frontend/pagination.md`](../40-frontend/pagination.md).
- Breaking changes require a new version. Additive changes do not, but do require a `30-contracts/CHANGELOG.md` entry.

### Required headers

| Header | Direction | Purpose |
|---|---|---|
| `Authorization: Bearer <jwt>` | in | User or service token |
| `X-Trace-Id` | both | Propagated end to end; generated at the edge if absent |
| `X-Client-Version` | in | App or web build, used for compatibility gating |
| `Idempotency-Key` | in | Required on all non-idempotent mutations that cost money or send messages |

### Health endpoints

Every service exposes:

- `GET /healthz` — process is alive. No dependency checks. Never fails for a downstream outage.
- `GET /readyz` — dependencies reachable (database, broker, cache). Failing removes the instance from rotation.
- `GET /metrics` — Prometheus exposition.

---

## 5. Events

- Events are **facts**: past tense, immutable, never commands.
- Every message carries the envelope defined in [`10-architecture/event-catalog.md`](../10-architecture/event-catalog.md).
- Publishing goes through the outbox — write the event row in the same transaction as the state change.
- Consumers are idempotent on `event_id` and must tolerate redelivery and out-of-order arrival.
- Payloads carry identifiers and minimal fields. Never PII, never joined data.
- Schema changes are additive within a major version. Removing or retyping a field is a new version.

---

## 6. Database

- Schema per service. **No cross-schema foreign keys** — reference by ID.
- Identifiers are UUIDv7: time-sortable, non-enumerable, no hot shard.
- Timestamps are `TIMESTAMPTZ`, always UTC, named `*_at`.
- Booleans are positive: `is_active`, never `is_not_active`.
- Money is stored in minor units as `BIGINT` with an explicit currency column. Never a float.
- Soft delete via `deleted_at` only where the domain needs recovery; otherwise delete.
- Every table has `created_at`; mutable tables have `updated_at`.
- Models and their migration land in the same `faue-db` pull request. CI enforces this via `alembic check`.
- Migrations are expand-only in the release that adds them; contraction happens in a later release.

---

## 7. Errors and logging

- Raise typed domain exceptions from modules; translate to HTTP at the router boundary. Modules never raise `HTTPException`.
- Log in structured JSON. Every line carries `trace_id`, `service`, `env`, and `user_id` where a user is in scope.
- **Never log PII.** No email, phone, measurements, image content, raw prompts containing user text, or tokens. CI fails on PII-shaped patterns in log statements.
- Log levels: `ERROR` needs human action; `WARNING` is a degraded path taken; `INFO` is a state change worth reconstructing; `DEBUG` is local only.
- Exceptions are logged once, at the boundary that handles them. Re-logging on the way up produces duplicate alerts.

---

## 8. Testing

| Layer | Scope | Speed |
|---|---|---|
| `tests/unit/` | Pure logic, no I/O. Scoring, rules, guardrails, colour analysis. | Milliseconds |
| `tests/integration/` | Real Postgres and Redis via testcontainers. Repositories, migrations, consumers. | Seconds |
| `tests/contract/` | Request and response shapes against the OpenAPI specification. | Seconds |

Rules:

- Test behaviour, not implementation. A test that breaks on a rename without a behaviour change is a liability.
- No mocking of code you own — use the real object. Mock only third-party network calls.
- Model calls are stubbed in tests by a recorded-response provider registered through the same `LLMProvider` interface. Never a real model call in CI.
- Every bug fix starts with a failing test that reproduces it.
- Pure logic that gates money, privacy, or safety requires 100% branch coverage: quiz scoring, consent checks, guardrails, the PII pipeline.

---

## 9. Git

- Trunk-based. Short-lived branches, merged within days, never weeks.
- Conventional Commits: `feat:`, `fix:`, `docs:`, `refactor:`, `test:`, `chore:`, `perf:`, `ci:`.
- The subject line says what changed and why in under 72 characters. The body explains why when it is not obvious.
- One logical change per pull request.
- Never commit secrets. Never embed a token in a git remote URL.
- `faue-core` and `faue-db` are semantically versioned and tagged; services pin exact versions.

---

## 10. Configuration and secrets

- All configuration through environment variables, read once into a Pydantic `Settings` object at startup. No `os.environ` reads scattered through the code.
- Every service ships `.env.example` listing every variable with a description and a safe default. A missing required variable fails at startup, loudly, not on first use.
- Secrets never enter the repository. Local development uses `.env` (git-ignored); deployed environments use the platform's secret store.
- Feature flags and model configuration are runtime-readable, so a kill switch does not require a deploy.

---

## 11. Stage tags

Every component, endpoint, table, and document carries a stage tag: `MVP`, `M1-2`, `M3+`, `Y2`. Tags appear in the document header, in OpenAPI descriptions, and in schema comments. Building ahead of the tag is how a four-week MVP becomes a four-month one.

---

## 12. Documentation

- A change to behaviour changes its document in the same pull request.
- Contract changes are recorded in `30-contracts/CHANGELOG.md` before the implementing service merges.
- Decisions go to `80-adr/` in MADR format and are immutable once accepted — superseded by a new ADR, never edited.
- `TBD` is not an acceptable end state. Write the answer, or write who decides it and by when.
