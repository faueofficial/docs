# Documentation Status

**Updated:** 2026-08-22 · **Build status:** [`build-status.md`](build-status.md) · **Consistency sweep:** passed (99 files, 0 broken links, vocabulary verified) · **Repo cleanup:** complete

Status values: `done` (written and verified) · `draft` (written, needs review) · `planned` (task exists, not written) · `deferred` (deliberately not written yet, with a reason).

Owner values: `backend` (Testimony) · `frontend` (frontend engineer) · `content` (Oladunni) · `shared`.

---

## 00-product

| Document | Stage | Owner | Status |
|---|---|---|---|
| `vision.md` | MVP | backend | done |
| `mvp-scope.md` | MVP | backend | done |
| `roadmap.md` | all | backend | done |
| `personas.md` | MVP | content | done |
| `style-dna.md` | MVP | shared | draft — persona taxonomy and question copy need review |
| `retention-system.md` | MVP | backend | done |
| `professional-strategy.md` | Y2 | backend | done |
| `metrics.md` | MVP | backend | done |

## 10-architecture

| Document | Stage | Owner | Status |
|---|---|---|---|
| `hld.md` | all | backend | done |
| `data-flows.md` | MVP | backend | done |
| `event-catalog.md` | all | backend | done |
| `model-plane.md` | MVP | backend | done |
| `ai-quality.md` | MVP | backend | done |
| `security.md` | MVP | backend | done |
| `privacy.md` | MVP | backend | done |
| `pii-handling.md` | MVP | backend | done |
| `prompt-injection.md` | MVP | backend | done |
| `ropa.md` | MVP | backend | done |
| `threat-model.md` | MVP | backend | done |

## 20-services

| Document | Stage | Owner | Status |
|---|---|---|---|
| `api-gateway/lld.md` | MVP | backend | done |
| `api-gateway/schema.md` | MVP | backend | done |
| `api-gateway/api.md` | MVP | backend | done |
| `api-gateway/events.md` | MVP | backend | done |
| `api-gateway/runbook.md` | MVP | backend | done |
| `ase/lld.md` | MVP | backend | done |
| `ase/schema.md` | MVP | backend | done |
| `ase/api.md` | MVP | backend | done |
| `ase/events.md` | MVP | backend | done |
| `ase/runbook.md` | MVP | backend | done |
| `faue-db.md` | MVP | backend | done |
| `faue-core.md` | MVP | backend | done |
| `shared-packages.md` | MVP | backend | done |
| `admin.md` | MVP | backend | done |
| `catalog/*` | M1-2 | backend | deferred — bounded module inside ase until extraction |
| `media/*` | M1-2 | backend | deferred — bounded module inside gateway until extraction |
| `brand/*` | M3+ | backend | deferred — designed in `hld.md` only |
| `commerce/*` | M3+ | backend | deferred — designed in `hld.md` only |

## 30-contracts

| Document | Stage | Owner | Status |
|---|---|---|---|
| `openapi/gateway.v1.yaml` | MVP | backend | done |
| `openapi/ase.internal.v1.yaml` | MVP | backend | done |
| `openapi/gateway.admin.v1.yaml` | MVP | backend | planned — written alongside admin implementation |
| `openapi/catalog shop-click endpoint` | M1-2 | backend | deferred — added with the catalog service |
| `events/*.schema.json` | all | backend | done |
| `CHANGELOG.md` | all | backend | done |

## 40-frontend

| Document | Stage | Owner | Status |
|---|---|---|---|
| `README.md` (handoff) | MVP | backend | done |
| `screens.md` | MVP | shared | done |
| `design-tokens.md` | MVP | shared | done |
| `auth-flows.md` | MVP | backend | done |
| `error-model.md` | MVP | backend | done |
| `pagination.md` | MVP | backend | done |
| `realtime.md` | MVP | backend | done |
| `offline-and-caching.md` | MVP | backend | done |
| `deeplinks.md` | MVP | backend | done |

## 50-data

| Document | Stage | Owner | Status |
|---|---|---|---|
| `style-library.md` | MVP | content | done |
| `curation-guide.md` | MVP | content | done |
| `labeling-guide.md` | MVP | content | done |
| `email-assets.md` | MVP | design | done — **artwork not yet produced** |
| `catalog-model.md` | M1-2 | content | done |

## 60-ai

| Document | Stage | Owner | Status |
|---|---|---|---|
| `prompts.md` | MVP | backend | done |
| `guardrails.md` | MVP | backend | done |
| `agent-design.md` | MVP | backend | done |
| `rendering.md` | MVP | backend | done |
| `eval-sets/README.md` | MVP | shared | done |

## 70-ops

| Document | Stage | Owner | Status |
|---|---|---|---|
| `environments.md` | MVP | backend | done |
| `deployment.md` | MVP | backend | done |
| `observability.md` | MVP | backend | done |
| `incident-response.md` | MVP | backend | done |
| `runbooks/*.md` | MVP | backend | done |

## 80-adr

| Document | Stage | Owner | Status |
|---|---|---|---|
| `0001` – `0022` | all | backend | done |

## 90-meta

| Document | Stage | Owner | Status |
|---|---|---|---|
| `conventions.md` | all | backend | done |
| `glossary.md` | all | shared | done |
| `doc-status.md` | all | backend | done |
| `build-status.md` | all | backend | done |

---

## Open items carried from the design specification

| # | Item | Blocks | Owner |
|---|---|---|---|
| 1 | Persona taxonomy and quiz option copy need review and sign-off | Quiz implementation, share-card design | shared |
| 2 | Generative image provider selection (cost, latency, African fashion fidelity, commercial terms) | Renderer implementation | backend |
| 3 | Style library licensing outreach — which tailors, who owns the conversation | Style library content | content |
| ~~4~~ | ~~Transactional email provider~~ — **resolved: Resend**. Remaining: verify `faueofficial.com` and publish SPF/DKIM/DMARC | Launch (operational) | backend |
| 10 | Public contact address is `faueofficial@gmail.com` for now. A domain address (`hello@faueofficial.com`) is worth having before launch — a Gmail contact on a privacy policy and a regulator notification reads as unestablished | Launch (soft) | backend |
| 5 | Phone OTP timing — confirm no launch market needs it before M1-2 | Nothing currently | backend |
| 6 | Tailor segment reachability — validate with 5 tailors before building anything | Professional track (Y2) | shared |
| 7 | Delegated consent design (client → stylist, partial and revocable) | Professional track (Y2) | backend |
| 8 | VTO consent purpose and guardrail exception, designed alongside the research | VTO | backend |
| 9 | **Revoke the leaked GitHub PAT** — remote is clean, token is not | Launch | backend |

## Design gaps requiring new Figma work

| # | Gap | Documented in |
|---|---|---|
| 1 | Answer options 2–4 for each Style DNA question | `00-product/style-dna.md` |
| 2 | Body profile capture screens | `40-frontend/screens.md` |
| 3 | Consent surfaces for AI processing, location, integrations | `40-frontend/screens.md` |
| 4 | Magic-link verification screen and cross-device code entry | `40-frontend/auth-flows.md` |
| 5 | Instagram card removal from Connected Accounts and onboarding | `40-frontend/screens.md` |
| 6 | Job-progress states for look generation | `40-frontend/realtime.md` |
| 7 | Bottom navigation is off-brand (`#613EEA`, SF Pro Text) | `40-frontend/design-tokens.md` |
