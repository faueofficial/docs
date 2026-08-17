# FAUE Documentation Set — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Produce the complete `faue-platform` documentation set — architecture, contracts, frontend handoff, service LLDs, AI/quality, ops, content guides, and ADRs — so that backend implementation and frontend work can both start from written contracts rather than conversation.

**Architecture:** Documentation lives in `docs/` (future `faue-platform` repo, not yet git-initialised). Five batches, ordered so each unblocks the next consumer: foundation → frontend handoff → backend build → quality/ops → content. Every document carries a stage tag (`MVP`, `M1-2`, `M3+`, `Y2`) and cross-references the spec section it implements.

**Tech Stack:** Markdown, OpenAPI 3.1 (YAML), JSON Schema for events, Mermaid for diagrams, MADR format for ADRs.

**Spec:** `docs/superpowers/specs/2026-08-17-faue-platform-architecture-design.md`

## Global Constraints

- Services: `api-gateway` (public), `ase` (internal), `catalog` (M1-2), `media` (M1-2), `brand` (M3+), `commerce` (M3+). `spree` is a module of `ase`; `notify` is a module of `gateway`.
- Repos are standalone under `github.com/faueofficial`; the workspace root is **not** a git repository and must not be initialised.
- Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, `pip` + `pip-tools`, single root `.venv`, shared `constraints.txt`.
- One Alembic project in `faue-db`; schema per service; no cross-schema foreign keys; UUIDv7 identifiers.
- API is one versioned REST surface `/v1/*`; admin is `/admin/v1/*` under a separate auth realm.
- Auth providers: email magic link, Google OIDC, Apple. Phone OTP deferred to M1-2. Instagram removed.
- Consent defaults to denied for every purpose; enforcement is a shared dependency.
- Model policy is closed-set: rules define the legal pool and validate returns; the model selects, assembles, ranks, and explains within it.
- Default look renderer is `generative`; `composite` and `hybrid` stay behind the same interface.
- Design tokens are authoritative from Figma file `KtCAHrBGLQXEdQrPbWJVVS` as extracted 2026-08-17.
- No placeholders. A document that says "TBD" is not done.

## Verification standard (applies to every task)

1. **Cross-reference:** every claim traceable to a spec section or the Figma extraction.
2. **No placeholders:** no `TBD`, `TODO`, `???`, or empty sections.
3. **Contract consistency:** endpoint paths, field names, event names, and table names identical across all documents that mention them.
4. **Stage tags:** every component or endpoint marked `MVP` / `M1-2` / `M3+` / `Y2`.

---

## Batch 1 — Foundation

### Task 1: Repository scaffold and meta

**Files:**
- Create: `docs/README.md`, `docs/repos.yaml`, `docs/scripts/bootstrap.sh`
- Create: `docs/90-meta/conventions.md`, `docs/90-meta/glossary.md`, `docs/90-meta/doc-status.md`

- [ ] **Step 1:** Write `README.md` with the audience map (backend / frontend / content / ops) and a "start here" path per audience.
- [ ] **Step 2:** Write `repos.yaml` listing all eleven repositories with directory, remote, stack, stage, and owner.
- [ ] **Step 3:** Write `bootstrap.sh` that clones missing repos and pulls existing ones from `repos.yaml`, idempotent, no root `git init`.
- [ ] **Step 4:** Write `conventions.md` — code style, commit format, branch policy, error model, health endpoints, naming rules, stage tags.
- [ ] **Step 5:** Write `glossary.md` — Style DNA, persona, vault, look, fabric analysis, aspiration vector, spree, ase, Owambe, Aso-Ebi, Agbada, Adire, Aso-Oke, gele, harmattan.
- [ ] **Step 6:** Write `doc-status.md` — table of every planned document with stage, owner, and status.
- [ ] **Step 7:** Verify against the verification standard.

### Task 2: High-level design

**Files:**
- Create: `docs/10-architecture/hld.md`

- [ ] **Step 1:** System context — actors, external systems, trust boundaries.
- [ ] **Step 2:** Service map with responsibilities, ingress rules, schemas owned, stage tags.
- [ ] **Step 3:** Module folding rules and the four extraction seams.
- [ ] **Step 4:** Shared infrastructure — Postgres, pgvector, RabbitMQ, Redis, object storage.
- [ ] **Step 5:** Mermaid container diagram and deployment diagram.
- [ ] **Step 6:** Non-functional requirements — latency targets, availability, scale assumptions, cost ceiling.
- [ ] **Step 7:** Verify.

### Task 3: Data flows

**Files:**
- Create: `docs/10-architecture/data-flows.md`

- [ ] **Step 1:** Magic-link auth flow with the three failure modes and their mitigations.
- [ ] **Step 2:** Quiz → DNA → card render → style context.
- [ ] **Step 3:** Look generation as an async job with progress states.
- [ ] **Step 4:** Fabric styling and tailor share.
- [ ] **Step 5:** Vault CRUD, wear logging, "style this item".
- [ ] **Step 6:** Pinterest connect, board import, reconciliation (reproduce / adapt / bespoke).
- [ ] **Step 7:** Spree session with tool loop; agent daily run.
- [ ] **Step 8:** Notification dispatch; DSR deletion orchestration.
- [ ] **Step 9:** Mermaid sequence diagram per flow.
- [ ] **Step 10:** Verify every flow names its endpoints, events, and tables exactly as the contracts do.

### Task 4: Event catalog

**Files:**
- Create: `docs/10-architecture/event-catalog.md`
- Create: `docs/30-contracts/events/*.schema.json` (one per event)

- [ ] **Step 1:** Envelope specification and versioning rules.
- [ ] **Step 2:** Full event table — name, producer, consumers, stage, payload fields.
- [ ] **Step 3:** Delivery semantics — outbox, idempotency, DLQ, replay, ordering guarantees.
- [ ] **Step 4:** JSON Schema per event.
- [ ] **Step 5:** Verify producer/consumer pairs match the service map in `hld.md`.

### Task 5: Architecture decision records

**Files:**
- Create: `docs/80-adr/0001-*.md` through `docs/80-adr/0020-*.md`

- [ ] **Step 1:** Write ADRs 0001–0010 in MADR format from spec §15.
- [ ] **Step 2:** Write ADRs 0011–0020.
- [ ] **Step 3:** Each carries context, decision, consequences, alternatives considered, and reversal cost.
- [ ] **Step 4:** Verify no ADR contradicts another.

### Task 6: Style DNA product specification

**Files:**
- Create: `docs/00-product/style-dna.md`

- [ ] **Step 1:** Define six personas — id, name, archetype, traits, tagline, gradient, styling implications.
- [ ] **Step 2:** Write six questions with complete answer option sets, copy matching the Figma voice.
- [ ] **Step 3:** Define the persona weight matrix per option.
- [ ] **Step 4:** Specify the scoring algorithm — tally, normalise, rank, tie-break, zero-score handling.
- [ ] **Step 5:** Worked example end to end.
- [ ] **Step 6:** Share-card specification for both formats.
- [ ] **Step 7:** Mark clearly as a proposal for review, with the reasoning behind each design choice.
- [ ] **Step 8:** Verify the algorithm is deterministic and total — every answer combination yields a result.

---

## Batch 2 — Frontend handoff

### Task 7: Gateway OpenAPI contract

**Files:**
- Create: `docs/30-contracts/openapi/gateway.v1.yaml`
- Create: `docs/30-contracts/CHANGELOG.md`

- [ ] **Step 1:** Components — security schemes, error object (RFC 7807), pagination envelope, shared schemas.
- [ ] **Step 2:** Auth paths.
- [ ] **Step 3:** Profile, body profile, consent, privacy paths.
- [ ] **Step 4:** Quiz paths.
- [ ] **Step 5:** Vault and wear-log paths.
- [ ] **Step 6:** Look generation, retrieval, save, adjust, regenerate, share paths.
- [ ] **Step 7:** Fabric paths.
- [ ] **Step 8:** Spree, agent, integrations, notifications paths.
- [ ] **Step 9:** Start the contract changelog.
- [ ] **Step 10:** Verify the document parses as OpenAPI 3.1 and every path in `data-flows.md` exists.

### Task 8: Screen registry

**Files:**
- Create: `docs/40-frontend/screens.md`

- [ ] **Step 1:** Table of all 72 hi-fi frames — name, node id, surface, route, entry points.
- [ ] **Step 2:** Per screen: endpoints called, state model, empty/loading/error states, components used.
- [ ] **Step 3:** Gap analysis — screens with no endpoint, endpoints with no screen.
- [ ] **Step 4:** List the seven content and design gaps from spec §12.
- [ ] **Step 5:** Verify every endpoint referenced exists in `gateway.v1.yaml`.

### Task 9: Frontend integration guides

**Files:**
- Create: `docs/40-frontend/auth-flows.md`, `error-model.md`, `pagination.md`, `realtime.md`, `design-tokens.md`, `offline-and-caching.md`, `deeplinks.md`

- [ ] **Step 1:** `auth-flows.md` — magic link end to end, token lifecycle, refresh rotation, cross-device fallback, logout, deletion.
- [ ] **Step 2:** `error-model.md` — RFC 7807 shape, error code catalogue, retry guidance, user-facing copy mapping.
- [ ] **Step 3:** `pagination.md` — cursor format, limits, stability guarantees.
- [ ] **Step 4:** `realtime.md` — job progress via SSE and polling fallback, reconnection, terminal states.
- [ ] **Step 5:** `design-tokens.md` — full extracted token set with Flutter and Tailwind mappings, plus the bottom-nav drift note.
- [ ] **Step 6:** `offline-and-caching.md` — what is cacheable, TTLs, optimistic updates, conflict handling.
- [ ] **Step 7:** `deeplinks.md` — universal links, app links, share URL structure, required well-known files.
- [ ] **Step 8:** Verify against `gateway.v1.yaml` and the token extraction.

### Task 10: MVP scope and product docs

**Files:**
- Create: `docs/00-product/mvp-scope.md`, `vision.md`, `roadmap.md`, `personas.md`, `metrics.md`

- [ ] **Step 1:** `mvp-scope.md` — in/out lists with reasoning, the core loop, launch criteria.
- [ ] **Step 2:** `vision.md` — problem, why now, differentiation, long-term shape.
- [ ] **Step 3:** `roadmap.md` — MVP, M1-2, M3+, Y2 with unlock conditions per phase.
- [ ] **Step 4:** `personas.md` — user personas (distinct from style personas), primary early adopter.
- [ ] **Step 5:** `metrics.md` — north star, funnel, guardrail metrics, disproof signals.
- [ ] **Step 6:** Verify no scope claim contradicts the design or the spec.

---

## Batch 3 — Backend build

### Task 11: Gateway service documentation

**Files:**
- Create: `docs/20-services/api-gateway/lld.md`, `schema.md`, `api.md`, `events.md`, `runbook.md`

- [ ] **Step 1:** `lld.md` — module layout, request lifecycle, dependencies, module interfaces, extraction seams.
- [ ] **Step 2:** `schema.md` — every table with columns, types, indexes, encryption markers, retention TTL.
- [ ] **Step 3:** `api.md` — endpoint reference with authorization and consent requirements per endpoint.
- [ ] **Step 4:** `events.md` — events produced and consumed with handler semantics.
- [ ] **Step 5:** `runbook.md` — start, health, common failures, key rotation, DSR handling.
- [ ] **Step 6:** Verify schema matches `faue-db` model plan and the OpenAPI contract.

### Task 12: Ase service documentation

**Files:**
- Create: `docs/20-services/ase/lld.md`, `schema.md`, `api.md`, `events.md`, `runbook.md`

- [ ] **Step 1:** `lld.md` — engine pipeline stages, spree, agent, context, vector layer, worker inventory.
- [ ] **Step 2:** `schema.md` — tables, vector columns, index definitions, model-version handling.
- [ ] **Step 3:** `api.md` — internal endpoint reference with service-JWT requirements.
- [ ] **Step 4:** `events.md`.
- [ ] **Step 5:** `runbook.md` — embedding migration, re-embed, budget exhaustion, provider outage.
- [ ] **Step 6:** Verify pipeline stages match spec §6.3 exactly.

### Task 13: Model plane documentation

**Files:**
- Create: `docs/10-architecture/model-plane.md`
- Create: `docs/60-ai/rendering.md`, `docs/60-ai/prompts.md`

- [ ] **Step 1:** Provider interfaces with full type signatures.
- [ ] **Step 2:** Task routing table, tier configuration, resolution order.
- [ ] **Step 3:** Fallback, circuit breaking, budgets, caching, telemetry fields.
- [ ] **Step 4:** Embedding plane, model versioning, migration procedure.
- [ ] **Step 5:** `rendering.md` — three strategies, job model, prompt construction, guardrails, cost model.
- [ ] **Step 6:** `prompts.md` — prompt file conventions, versioning, variables, per-task prompt contents.
- [ ] **Step 7:** Verify every task named in routing has a prompt and an eval set.

### Task 14: Privacy and compliance documentation

**Files:**
- Create: `docs/10-architecture/privacy.md`, `pii-handling.md`, `ropa.md`

- [ ] **Step 1:** `privacy.md` — consent model, purposes, enforcement, DSR endpoints, deletion orchestration, age gate, residency.
- [ ] **Step 2:** `pii-handling.md` — field inventory, image pipeline spec, redaction before model egress, key management, log scrubbing, breach procedure.
- [ ] **Step 3:** `ropa.md` — per-field register: lawful basis, retention TTL, recipients, egress.
- [ ] **Step 4:** Verify every table in both service schemas appears in the register.

### Task 15: Prompt injection and database package

**Files:**
- Create: `docs/10-architecture/prompt-injection.md`
- Create: `docs/20-services/faue-db.md`, `docs/20-services/faue-core.md`

- [ ] **Step 1:** `prompt-injection.md` — trust tiers, channel separation, ingest detection, OCR vector, tool authorization, output validation, budgets, test suite.
- [ ] **Step 2:** `faue-db.md` — package layout, model conventions, migration workflow, CI gates, role grants, deploy ordering.
- [ ] **Step 3:** `faue-core.md` — shared library surface with module-by-module API.
- [ ] **Step 4:** Verify role grants match the schema ownership in both service documents.

---

## Batch 4 — Quality and operations

### Task 16: AI quality and evaluation

**Files:**
- Create: `docs/10-architecture/ai-quality.md`
- Create: `docs/60-ai/guardrails.md`, `docs/60-ai/agent-design.md`
- Create: `docs/60-ai/eval-sets/README.md`

- [ ] **Step 1:** `ai-quality.md` — offline sets with gates, online evaluation, drift, human review loop.
- [ ] **Step 2:** `guardrails.md` — layered guardrails as testable objects, refusal taxonomy, review queue.
- [ ] **Step 3:** `agent-design.md` — autonomy levels, memory tiers, learning loop, cold start, explainability.
- [ ] **Step 4:** `eval-sets/README.md` — set format, labeling workflow, gate thresholds.
- [ ] **Step 5:** Verify every gate threshold is a specific number.

### Task 17: Security and operations

**Files:**
- Create: `docs/10-architecture/security.md`, `threat-model.md`
- Create: `docs/70-ops/environments.md`, `deployment.md`, `observability.md`, `incident-response.md`
- Create: `docs/70-ops/runbooks/*.md`

- [ ] **Step 1:** `security.md` — secrets, service auth, rate limits, upload safety, baseline controls, backups.
- [ ] **Step 2:** `threat-model.md` — STRIDE per trust boundary with mitigations and residual risk.
- [ ] **Step 3:** `environments.md` — local/staging/prod, port map, mock mode, embedding provider economics with the break-even calculation.
- [ ] **Step 4:** `deployment.md` — Railway topology, CI/CD, migration ordering, rollback, VPS migration path.
- [ ] **Step 5:** `observability.md` — telemetry fields, six dashboards, alert list with thresholds.
- [ ] **Step 6:** `incident-response.md` — severity ladder, breach notification clock, contacts.
- [ ] **Step 7:** Runbooks for the alerts defined in `observability.md`.
- [ ] **Step 8:** Verify every alert has a matching runbook.

### Task 18: Retention system and admin

**Files:**
- Create: `docs/00-product/retention-system.md`
- Create: `docs/20-services/admin.md`

- [ ] **Step 1:** Habit loop, lifecycle schedule, cultural triggers, compounding value, metrics.
- [ ] **Step 2:** Notification template catalogue mapped to lifecycle stages and consent purposes.
- [ ] **Step 3:** `admin.md` — surface inventory by stage, RBAC matrix, audit requirements, masking rules.
- [ ] **Step 4:** Verify every notification maps to a consent purpose and a frequency cap.

---

## Batch 5 — Content

### Task 19: Style library and curation

**Files:**
- Create: `docs/50-data/style-library.md`, `curation-guide.md`, `catalog-model.md`

- [ ] **Step 1:** `style-library.md` — taxonomy schema, the 30 styles with tags, fabric suitability matrix, sourcing policy, provenance fields.
- [ ] **Step 2:** `curation-guide.md` — workflow for adding styles and accessories, quality bar, review checklist.
- [ ] **Step 3:** `catalog-model.md` — product data model, tagging vocabulary, ingestion sources, link health (M1-2).
- [ ] **Step 4:** Verify the fabric vocabulary is identical across style library, catalog model, and fabric flow.

### Task 20: Labeling guide and final consistency pass

**Files:**
- Create: `docs/50-data/labeling-guide.md`
- Modify: `docs/90-meta/doc-status.md`

- [ ] **Step 1:** `labeling-guide.md` — how to label each golden set, worked examples, inter-rater guidance.
- [ ] **Step 2:** Full cross-document consistency sweep — endpoints, events, tables, fabric terms, persona ids, stage tags.
- [ ] **Step 3:** Update `doc-status.md` to reflect completion.
- [ ] **Step 4:** Write the handoff summary for the frontend engineer listing exactly which documents he needs.

---

## Self-review notes

- Spec coverage: §3–§14 map to tasks 2–19. §15 ADRs map to task 5. §16 open questions map to task 6 (persona taxonomy) and are otherwise recorded rather than resolved.
- Deliberately excluded: `brand` and `commerce` service LLDs (M3+, designed in `hld.md` only), and Y2 subsystems.
- Repository cleanup and code implementation are a separate plan, written after this documentation set is reviewed.
