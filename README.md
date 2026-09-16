# FAUE Platform Documentation

Single source of truth for how FAUE is built. If code and this documentation disagree, one of them is a bug — say which in a pull request rather than letting them drift.

**Repository:** `docs` · **Workspace directory:** `docs/`

---

## Start here

**New to FAUE?** [`00-product/prd.md`](00-product/prd.md) — the problem, the users,
the numbered requirements, and how success is measured. Every other document
elaborates some part of it.

### If you are building the Flutter app or the web surfaces

You should not need to read a backend document to do your job. Read, in order:

1. [`00-product/prd.md`](00-product/prd.md) — the requirements, numbered so a screen and a test can cite the same one. Then [`00-product/mvp-scope.md`](00-product/mvp-scope.md) for what is deliberately *not* being built.
2. [`40-frontend/screens.md`](40-frontend/screens.md) — every screen, its route, the endpoints behind it, and its states.
3. [`40-frontend/design-tokens.md`](40-frontend/design-tokens.md) — colours, type, spacing, components, with Flutter and Tailwind mappings.
4. [`30-contracts/openapi/gateway.v1.yaml`](30-contracts/openapi/gateway.v1.yaml) — the API. Generate your client from this file.
5. [`40-frontend/auth-flows.md`](40-frontend/auth-flows.md), [`error-model.md`](40-frontend/error-model.md), [`realtime.md`](40-frontend/realtime.md), [`pagination.md`](40-frontend/pagination.md), [`deeplinks.md`](40-frontend/deeplinks.md), [`offline-and-caching.md`](40-frontend/offline-and-caching.md) — the integration details.

Watch [`30-contracts/CHANGELOG.md`](30-contracts/CHANGELOG.md). Every contract change lands there before it lands in a service.

### If you are building the backend or the AI system

1. [`10-architecture/hld.md`](10-architecture/hld.md) — services, boundaries, infrastructure.
2. [`10-architecture/data-flows.md`](10-architecture/data-flows.md) — how a request becomes a result.
3. [`10-architecture/event-catalog.md`](10-architecture/event-catalog.md) — the asynchronous contract between services.
4. [`20-services/<service>/lld.md`](20-services/) — the service you are working in.
5. [`10-architecture/model-plane.md`](10-architecture/model-plane.md) — how models are called, routed, budgeted, and evaluated.
6. [`10-architecture/privacy.md`](10-architecture/privacy.md), [`pii-handling.md`](10-architecture/pii-handling.md), [`prompt-injection.md`](10-architecture/prompt-injection.md) — non-negotiable before touching user data or model input.

### If you are curating content

1. [`00-product/style-dna.md`](00-product/style-dna.md) — personas, questions, scoring.
2. [`50-data/style-library.md`](50-data/style-library.md) — the native style taxonomy and how styles are added.
3. [`50-data/curation-guide.md`](50-data/curation-guide.md) — the working process and quality bar.
4. [`50-data/labeling-guide.md`](50-data/labeling-guide.md) — how to label the evaluation sets that gate every AI release.

### If you are operating the system

1. [`70-ops/environments.md`](70-ops/environments.md) — where things run and what they cost.
2. [`70-ops/deployment.md`](70-ops/deployment.md) — how code reaches production and how to get it back.
3. [`70-ops/observability.md`](70-ops/observability.md) — dashboards and alerts.
4. [`70-ops/runbooks/`](70-ops/runbooks/) — one runbook per alert.
5. [`70-ops/incident-response.md`](70-ops/incident-response.md) — severity ladder and the breach clock.

---

## Layout

| Directory | Contents |
|---|---|
| `00-product/` | Vision, scope, roadmap, Style DNA, retention, metrics |
| `10-architecture/` | HLD, data flows, events, model plane, security, privacy, threat model |
| `20-services/` | Per-service low-level design, schema, API, events, runbook |
| `30-contracts/` | OpenAPI specifications, event JSON Schemas, contract changelog |
| `40-frontend/` | Everything the frontend engineer needs, and nothing he does not |
| `50-data/` | Style library, catalog model, curation and labeling guides |
| `60-ai/` | Prompts, guardrails, agent design, rendering, evaluation sets |
| `70-ops/` | Environments, deployment, observability, runbooks, incidents |
| `80-adr/` | Architecture decision records, immutable once accepted |
| `90-meta/` | Conventions, glossary, documentation status |
| `superpowers/` | The originating design specification and implementation plans |

---

## Stage tags

Every component, endpoint, table, and document is tagged with when it exists. Reading a document without checking its tag is how people build M3 features during MVP.

| Tag | Meaning |
|---|---|
| `MVP` | Built first, required for launch |
| `M1-2` | Month 1–2, after the core loop works |
| `M3+` | Month 3 onward, conditional on validation |
| `Y2` | Year 2–3 platform maturity |

---

## Repositories

The workspace root is **not** a git repository. Every directory beneath it is a standalone repository. `repos.yaml` is the manifest; `scripts/bootstrap.sh` hydrates a fresh machine.

```bash
./scripts/bootstrap.sh          # clone what is missing, pull what exists
./scripts/bootstrap.sh --status # show branch and dirty state per repo
```

---

## Contributing to these documents

- One change of substance per pull request. Documentation reviews are cheap; untangling three merged ideas is not.
- Update `30-contracts/CHANGELOG.md` in the same pull request as any contract change.
- A document with `TBD` in it is not finished. Write the answer or write down why it cannot be answered yet, and who decides.
- Decisions go in `80-adr/`, not in prose scattered across documents. If you are explaining *why* for the third time, it wants an ADR.

> **Reconciliation closed.** An earlier architecture document from this repository's
> remote is retained at `90-meta/legacy/01_SYSTEM_ARCHITECTURE.md` with a supersession
> banner. Every conflict is resolved — see [`90-meta/reconciliation.md`](90-meta/reconciliation.md)
> and [ADR 0022](80-adr/0022-canonical-domain-and-service-naming.md).

**Source specification:** [`superpowers/specs/2026-08-17-faue-platform-architecture-design.md`](superpowers/specs/2026-08-17-faue-platform-architecture-design.md) — the approved design every document here elaborates.
