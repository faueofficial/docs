# FAUE Platform Architecture — Design Specification

**Version:** 1.0
**Date:** 2026-08-17
**Status:** Approved design, pre-implementation
**Owner:** Testimony (backend + AI). Frontend consumes `docs/40-frontend/` and `docs/30-contracts/`.
**Supersedes:** architecture sections of `faue.md` (MVP v1.0) and `faue (1).md` (Style DNA v1.1) where they conflict.

---

## 1. Purpose and scope

This document is the approved architecture for FAUE across its full lifetime — MVP through platform maturity. It defines the service topology, data architecture, AI/model plane, privacy and security posture, evaluation and monitoring systems, repository layout, and the documentation set to be written from it.

Every component carries a stage tag:

| Tag | Meaning |
|---|---|
| `MVP` | Built first, required for launch |
| `M1-2` | Month 1–2, after the core loop works |
| `M3+` | Month 3 onward, conditional on validation |
| `Y2` | Year 2–3 platform maturity |

Nothing in this document authorizes building an `M3+` component early. It exists so that boundaries drawn today survive those components arriving later.

---

## 2. Product definition (as designed)

The Figma file (`KtCAHrBGLQXEdQrPbWJVVS`, 72 hi-fi frames, last modified 2026-08-13) is authoritative for product scope where it conflicts with the earlier markdown docs. Three conflicts were resolved by decision:

**2.1 The MVP loop is wardrobe- and fabric-driven, not catalog-driven.**

```
Style DNA quiz → Vault (own wardrobe) and/or fabric upload
  → Generate look (occasion · mood · weather · notes)
  → AI result with reasoning ("Why this works for you")
  → Save / Share / Send to tailor
  → Return
```

Cross-brand catalog, brand partnerships, affiliate "Shop This" links, and product curation are **deferred to `M1-2`/`M3+`**. No screen in the design shows a brand, a price, or a purchase action. The `catalog` service is designed here and built later.

**2.2 Look rendering is a pluggable strategy, not a fixed technique.**

The design's AI Result screens require visual outputs. Three strategies are implemented behind one interface and selected by config and experiment:

- `generative` — **default.** Diffusion image generation from the look description.
- `composite` — server-side composition of the user's real vault item photos into a look layout.
- `hybrid` — real items where they exist, generated fill for gaps, clearly labeled.

Generative ships first. The other two remain behind the same interface so the choice can be revisited on measured save rate, share rate, and cost per look rather than argued. The interface, job model, progress reporting, and guardrails are identical across strategies; only the renderer differs.

**2.3 The Style DNA quiz is 6 questions.**

The 10-question / 13-point weighted algorithm in `faue (1).md` is superseded. Scoring is respecified for six questions in `docs/00-product/style-dna.md`. Persona naming must also be reconciled: the design's result screen reads "The Cultural Minimalist", which is not one of the six personas in the prior spec.

---

## 3. Service topology

### 3.1 Services

| Service | Stage | Owns | Ingress |
|---|---|---|---|
| `api-gateway` | MVP | Identity, profile, quiz, vault, saves, actions, integrations, notifications, privacy, admin API | Public |
| `ase` | MVP | Style vectors, embeddings, retrieval, look generation, fabric analysis, spree, agent, weather context | Internal only |
| `catalog` | M1-2 | Brands, products, ingestion, enrichment, link health | Internal only |
| `media` | M1-2 | Uploads, image PII pipeline, renders, share cards | Internal only |
| `brand` | M3+ | Brand dashboard, self-serve catalog, promoted placement | Internal only |
| `commerce` | M3+ | Subscriptions, affiliate ledger, payouts, orders | Internal only |

Until `catalog` and `media` are extracted, their responsibilities live as bounded modules inside `gateway` and `ase` with their future interfaces already drawn.

**Folded modules** (deliberately not separate services yet):

- `ase.spree` — conversational/agentic layer. Extractable.
- `gateway.notify` — notification delivery. Extractable.

Extraction seams, enforced from the first commit:

1. A module owns its own tables, prefixed by module name. No other module reads them directly.
2. Cross-module calls go through an interface class, never direct imports of internals.
3. `notify` is invoked **only** by consuming events, never by an inline function call from a request handler.
4. Each module ships its own OpenAPI fragment and config namespace.

### 3.2 Client surfaces

| Surface | Stage | Role |
|---|---|---|
| `faue-app` (Flutter) | MVP | The product. All flows. |
| `faue-web` (Next.js) | MVP | Landing page, public share pages (`/dna/:id`, `/look/:id`), app-store redirects |
| `faue-admin` (Next.js) | MVP | Internal operations, observability, content tooling, review queues |

One versioned REST API (`/v1/*`) serves app and web alike; OpenAPI generates the Flutter client. Admin uses `/admin/v1/*` under a separate auth realm.

### 3.3 Shared infrastructure

- **PostgreSQL** — one cluster, schema per service, no cross-schema foreign keys (IDs only), so extraction stays cheap.
- **pgvector** — in the `ase` schema. Single datastore; ChromaDB from the `drip-match` prototype is dropped.
- **RabbitMQ** — topic exchange `faue.events`, one durable queue per consumer, dead-letter queue per consumer. A configurable in-process bus implements the same interface for local development.
- **Redis** — cache, rate limiting, OTP TTL storage, semantic model cache.
- **Object storage / CDN** — Cloudinary or S3-compatible for user images and renders.

---

## 4. Core flows

### 4.1 Authentication (`gateway`)

Providers: email **magic link**, Google (OIDC), Apple (Sign in with Apple).

```
POST /v1/auth/link/request  → rate limit (per identifier + per IP) → mint opaque 32-byte token,
                              store hashed, TTL 10m, single-use, one active per identifier
                              → email link https://faue.app/auth/verify?t=…  (universal/app link)
POST /v1/auth/link/consume  → consume token → upsert user → access JWT (15m) + rotating refresh (30d)
POST /v1/auth/oauth/google  → verify id_token server-side (iss, aud, nonce)
POST /v1/auth/oauth/apple   → verify identity token; capture name on first authorization only
POST /v1/auth/username      → design's post-signup username step
```

Magic-link constraints, each addressing a known failure mode:

1. **Consumption is POST-only.** Mail security scanners pre-fetch every URL in a message; a GET that consumes the token burns the login before the user taps it. The link opens the app (or a web confirmation page) which then performs the consuming POST.
2. **Cross-device fallback.** The request stores an opaque `session_challenge` on the requesting device. If the link is opened elsewhere, the landing page shows a 6-digit code to type into the original app session rather than failing.
3. **Deep linking** requires `faue-web` to serve `apple-app-site-association` and `assetlinks.json` with matching bundle identifiers. When the app is not installed, the link falls through to a web page with store links that preserves the token.
4. **Never a JWT in the URL.** A signed token in a link is a bearer credential that persists in browser history, referrer headers, and mail server logs. The token is opaque, stored hashed, and meaningless outside the server.

Phone OTP is deferred to `M1-2` and follows the same store-hashed, single-use, rate-limited model.

Identity model is one user with many identities:

```
users(id, status, age_verified, created_at, deleted_at)
auth_identities(id, user_id, provider, provider_uid, email_enc, email_verified, linked_at, last_used_at)
```

Constraints that must not be discovered late:

- Apple's client secret is an ES256 JWT that must be regenerated at least every six months.
- Apple returns the user's name **only on first authorization**; persist immediately or lose it permanently.
- Apple private-relay addresses mean email is not a reliable identity key.
- Offering Sign in with Apple obliges in-app account deletion.
- Account linking occurs only on a **verified** email match. Unverified auto-linking is an account-takeover path and is forbidden.

`ase` never receives user tokens; the gateway passes `user_id` plus a short-lived service JWT.

### 4.2 Style DNA quiz (`gateway`, synchronous)

```
POST /v1/quiz/submit {answers}
  → pure scoring function (config-driven persona matrix, no I/O)
  → persist style_preferences + append-only quiz_responses
  → respond {dna, tagline, card_urls: pending}
  → emit quiz.completed
media consumes → renders share card (square 1080×1080, stories 1080×1920) → emits media.card.ready
ase   consumes → builds DNA style vector → caches user_style_context
```

Card rendering never blocks submission. The client polls `GET /v1/quiz/card`.

Retake is available from the profile, rate-limited to once per 30 days to preserve data integrity.

### 4.3 Look generation (`gateway` → `ase`, asynchronous with progress)

The design's "Building your fit… 70%" screen requires a job model, not a request/response call.

```
POST /v1/looks/generate {source: vault|fabric|prompt, item_ids[], fabric_id?,
                         occasion, mood?, weather_opt_in, note?}
  → validate, check budget + consent → create job → 202 {job_id}
  → ase worker:
      resolve style context (DNA + aspiration + behavior vectors)
      apply hard constraints (body silhouette, occasion, owned items, availability)
      assemble candidate looks (deterministic combinatorics)
      rank (heuristic → reranker)
      render via LookRenderer strategy (generative | composite | hybrid)
      generate reasoning text ("Why this works for you"), grounded in the chosen look
  → progress events over SSE or polling: queued → analyzing → assembling → rendering → done
GET  /v1/looks/{id}
POST /v1/looks/{id}/save | /adjust | /regenerate | /share
```

Failure surfaces as the designed error state ("We couldn't create this look"), never a raw error.

### 4.4 Fabric styling (`ase`)

```
upload fabric → media pipeline (§7.3) → fabric.uploaded
POST /v1/fabric/{id}/style {fabric_type?, occasion?, gender?, constraints?}
  → embed fabric image
  → classify fabric type (embedding kNN over labeled swatches; vision model fallback)
  → rule match over the native style library (fabric suitability, occasion, formality)
  → rank surviving styles
  → generate per-style reasoning
  → accessory pairing lookup, occasion-aware
POST /v1/fabric/{id}/tailor-share {style_id, notes} → composite share image
```

Style **selection** is deterministic; the model classifies and narrates. A wrong style match costs the user real money at a tailor, which is why the selection layer is rules-first.

### 4.5 Vault (`gateway`)

Item CRUD with photo upload, categories (Tops · Bottoms · Native · Shoes · Accessories), search, item details, edit, delete with confirmation, and "Style this item" — which routes into look generation seeded by a single owned item.

Wear logging feeds the agent's learning loop.

### 4.6 Integrations — Pinterest (`gateway.integrations`)

Entry point is post-quiz ("Connect your Pinterest account") and the Connected Accounts screen.

```
OAuth2 + PKCE → tokens encrypted at rest (envelope encryption)
Pinterest scopes: boards:read, pins:read  (read-only, never write)
sync worker: incremental cursor per board, rate-limit aware, refresh on 401, hard-stop on revoke
user selects which boards to import — never all-by-default
pins → media cache → ase embeds → aspiration_vector per board and per user
```

**Reconciliation is the product value, not import.** Aspiration (what they love) is reconciled against DNA, body profile, and budget to produce: *reproduce* (close match available), *adapt* (same look adjusted, with the reason stated), or *bespoke path* (no ready match → route to fabric/tailor flow).

Imported pins remain private to the user and are never republished.

**Instagram is out of scope and removed from the design.** The Connected Accounts screen promised "analyze your fashion-related posts and saves", which the Instagram platform cannot deliver: the Graph API does not expose a user's saved posts or collections, and Basic Display is deprecated. Only the user's own published media, on Business/Creator accounts, is reachable — far less than the screen implies. The Instagram card is removed from Connected Accounts and from the onboarding flow.

The `IntegrationProvider` interface remains general, so a future integration (a different platform, or Instagram if its API changes) does not require rework.

### 4.7 Spree — conversational styling (`ase.spree`)

The design's Generate screen ("Hi, there 👋 / Tell me what you're going for…", Style Fabric · Generate Look · Style Studio · Use my vault) is a conversational entry point.

```
session → multimodal LLM with tools:
  ase.find_similar · ase.pair_items · ase.check_occasion_fit
  vault.list_owned · profile.get_constraints · context.weather_today
  catalog.search (M1-2)
bounded: max 4 tool rounds, 8 total calls, 30s wall clock
tools are read-only — nothing that mutates state or spends money is exposed
```

The model narrates; tools decide. Any product, price, or brand claim without a matching tool result is stripped from the response.

### 4.8 Agent — daily styling (`ase.agent`)

| Level | Behavior | Stage |
|---|---|---|
| L0 | Suggests on app open ("today's fit") | MVP |
| L1 | Daily scheduled push at a chosen hour | M1-2 |
| L2 | Proactive triggers — weather shift, upcoming event, new pin | M3+ |
| L3 | Planning — event prep, travel packing, aso-ebi coordination, tailor lead times | Y2 |

Learning loop: wear-log events, accepted/rejected suggestions, saves, and seasonality. Memory is three-tiered and inspectable — **profile facts** (durable), **semantic preferences** (learned, decayed), **episodic** (what was worn or suggested, 90-day window). "Why did you suggest this?" must answer from stored facts, never from a re-prompted guess.

Cold start runs on DNA plus Pinterest aspiration; weight shifts to observed behavior at roughly ten logged fits.

### 4.9 Notifications (`gateway.notify`)

Channels: push (FCM/APNs), WhatsApp, email, SMS, in-app inbox. The design's Notification screen has All · Style · Activity tabs.

Consumes `faue.events`, owns templates, preference centre per category, quiet hours (WAT), per-user frequency caps, idempotent on `event_id`, and reports delivery/open back onto the event stream.

**No service sends a message directly.** Everything routes through `notify`, so caps and preferences cannot be bypassed.

---

## 5. Event architecture

Exchange `faue.events`, topic routing. Events are facts: past tense, immutable, additive-only within a major version.

Envelope on every message: `event_id, name, version, occurred_at, producer, user_id?, trace_id, payload`. Consumers are idempotent on `event_id`.

| Event | Producer | Consumers |
|---|---|---|
| `user.registered` | gateway | analytics |
| `quiz.completed` | gateway | ase, media, notify, analytics |
| `media.card.ready` | media | gateway, notify |
| `vault.item.added` | gateway | ase, analytics |
| `vault.item.worn` | gateway | ase, analytics |
| `fabric.uploaded` | media | ase, analytics |
| `look.requested` / `look.completed` / `look.failed` | ase | gateway, notify, analytics |
| `look.saved` / `look.shared` | gateway | ase, analytics |
| `tailor.share.created` | gateway | analytics |
| `integration.connected` / `integration.synced` | gateway | ase, analytics |
| `recommendation.feedback` | gateway | ase |
| `catalog.product.upserted` / `.unavailable` | catalog | ase, gateway |
| `shop.clicked` | gateway | commerce, analytics |
| `user.deletion.requested` / `.completed` | gateway / all | gateway |
| `ai.budget.exceeded` | ase | gateway, admin |

Event payloads carry IDs and minimal fields — never PII, never joined data.

Analytics subscribes as a single consumer rather than each service embedding a vendor SDK.

**Outbox pattern** is mandatory: the event row is written in the same transaction as the state change and relayed asynchronously. Without it, "row saved but event lost" is an untraceable class of bug.

---

## 6. Model plane (`ase.models`)

### 6.1 Two planes

```python
class LLMProvider(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]: ...

class EmbeddingProvider(Protocol):
    model_id: str
    dim: int
    modalities: set[Literal["text", "image"]]
    async def embed_text(self, texts: list[str]) -> list[Vector]: ...
    async def embed_image(self, images: list[ImageRef]) -> list[Vector]: ...

class ImageRenderer(Protocol):
    strategy: Literal["generative", "composite", "hybrid"]
    async def render(self, look: LookSpec) -> RenderResult: ...
```

No vendor SDK is imported outside `ase.models`.

### 6.2 LLM routing

OpenRouter is the router. **Code never names a model** — it names a task; config resolves task → tier → ordered model list. Model identifiers change frequently, and a hardcoded slug is a future outage.

```yaml
tiers:
  reasoning:   [...]
  fast:        [...]
  vision:      [...]      # image input + tool calling
  cheap_bulk:  [...]
providers:
  openrouter:
    zdr_only: true          # zero-data-retention allowlist, enforced per request
    require_no_train: true
tasks:
  look.reasoning:      { tier: fast,       max_tokens: 300, cache: semantic }
  fabric.reasoning:    { tier: fast,       max_tokens: 300, cache: semantic }
  spree.chat:          { tier: vision,     max_tokens: 800, tools: true, stream: true }
  spree.intent_guard:  { tier: cheap_bulk, max_tokens: 20,  temp: 0.0 }
  agent.daily_brief:   { tier: fast,       max_tokens: 250 }
  quiz.tagline:        { tier: fast,       max_tokens: 60 }
  catalog.autotag:     { tier: cheap_bulk, max_tokens: 150, batch: true }   # M1-2
```

Per-call sequence: resolve task → check `ai_processing` consent → redact PII from inputs → semantic cache lookup → budget check → provider call with timeout → schema validation → output moderation → log task, tier, resolved model, prompt version, tokens, cost, latency, cache hit, fallback depth, guardrail verdict.

**Fallback chain:** primary → next model in tier on 5xx/timeout/rate-limit → circuit breaker per model → after tier exhaustion, the **template path**. Every AI feature has a non-AI degraded form. The product must remain usable with the model plane entirely down.

### 6.3 Where models act in recommendation

```
1  RETRIEVE   embedding ANN over candidates                     MODEL
2  FILTER     consent, availability, gender, size,              RULES (hard)
              body silhouette, owned-item suppression
3a POOL       the legal pool: everything that survived stage 2  RULES
              (exists, available, right size, owned/in catalog)
3b STYLIST    model selects and assembles looks from the pool — MODEL
              choosing pieces, judging colour harmony,
              proportion, layering, texture balance, and
              cultural/occasion fit; may propose swaps and
              reject combinations rules would have allowed
3c VALIDATE   every returned item id must exist in the pool;    RULES
              category coverage checked; unknown ids dropped,
              never repaired
4  RERANK     bounded reorder of ~50 candidates                 MODEL
5  RENDER     generative (default) | composite | hybrid         MODEL / deterministic
6  EXPLAIN    "Why this works for you"                          MODEL (narration)
```

Stage 3b is deliberately model-led, and it selects as well as assembles. Which pieces belong in a look, how they sit together, whether the colours harmonise, and whether the result reads correctly for the occasion are all judgement problems a rule table handles badly. Deterministic colour analysis — LAB-space distance, complementary/analogous/triadic relations, neutral-anchor detection — is computed and supplied to the model as a **prior, not a gate**, so it reasons from measured colour facts rather than inferring hex values from prose.

Rules keep exactly two jobs in this stage: defining what is legally available (stage 2), and verifying afterwards that what came back is real (stage 3c). Everything aesthetic between those two points belongs to the model.

The policy is **closed-set, not no-model**: within the legal pool the model has full latitude to select, combine, reject, and rank — but it may not invent an item, price, brand, or style outside the catalog, vault, or style library. Every model output is validated against the candidate set before reaching a user; hallucinated identifiers are dropped, not repaired.

Reranking maturity: heuristic (`MVP`) → cross-encoder or LLM reranker (`M1-2`) → learning-to-rank trained on saves, wears, and shares (`M3+`).

### 6.4 Embedding plane

Default is **self-hosted open-CLIP / SigLIP** inside `ase` — no per-call cost, no vendor lock, and genuinely multimodal, which fabric matching requires. Adapters for HuggingFace Inference, Voyage, Cohere, and Gemini sit behind the same interface and are selected per environment. On Railway, where idle RAM is billed continuously, a hosted embedding API is likely cheaper; on a VPS, self-hosting is. The break-even calculation belongs in `docs/70-ops/environments.md` so that decision is arithmetic rather than preference.

**Embeddings are not portable between models.** One row per subject per model:

```sql
ase.product_embeddings(product_id, model_id, dim, embedding vector, image_hash, created_at,
                       PRIMARY KEY (product_id, model_id))
```

Migration is dual-write: embed with the new model in the background → shadow-evaluate on the golden set → flip reads by config flag → drop old rows after a soak period. No downtime, no big-bang re-embed.

Dimension budget matters: 3072-d vectors cost roughly four times the storage and index memory of 768-d. Default to a 768–1024-d open model and document the tradeoff.

### 6.5 Image rendering

All three strategies share one job model, progress reporting, storage path, and guardrail set.

- **Generative (default)** — external provider (fal, Replicate, or an image-capable model via OpenRouter). Cost per image and 10–40s latency make it a queued job with progress, never a synchronous call. Prompts are constructed from the deterministic `LookSpec`, never from raw user text.
- **Composite** — deterministic server-side layout of the user's own item photos. Fast, free, no hallucinated garments, and the honest option for "this is your wardrobe".
- **Hybrid** — real items where available, generated fill elsewhere, visually labeled so the user always knows which parts they own.

Guardrails specific to rendering: no photorealistic depiction of the user's face or body (looks are rendered on abstract or mannequin forms unless an explicit future feature says otherwise), NSFW filtering on output, provenance metadata on every render, and a visible "generated by FAUE AI" attribution matching the design.

Selection between strategies is an experiment, evaluated on save rate, share rate, and cost per generated look.

### 6.6 Cost control

- Semantic caching on repeated reasoning tasks.
- Precompute over on-demand — embeddings and tagging run in batch jobs, never in a request.
- Per-user daily token cap, per-task monthly ceiling, global kill switch per task.
- Exceeding a cap degrades to the template path and emits `ai.budget.exceeded`; it never bills silently.
- Cost per active user is a tracked, alerted metric.

### 6.7 Prompt discipline

Prompts are versioned files (`ase/prompts/<task>/v3.md`), never inline strings, and the version identifier is logged with every response. A prompt change is a reviewable diff and triggers the eval suite.

---

## 7. Privacy, security, and safety

### 7.1 Consent, by default denied

```sql
gateway.consents(user_id, purpose, granted, policy_version, granted_at, revoked_at, source,
                 PRIMARY KEY (user_id, purpose))
```

Purposes, independently revocable: `essential`, `personalization`, `ai_processing`, `pinterest_sync`, `instagram_sync`, `camera_photos`, `location_weather`, `agent_proactive`, `marketing_comms`, `analytics`.

Every purpose defaults to **denied**. Enforcement is a shared dependency, not per-endpoint discipline, so a new endpoint cannot forget it. Missing consent degrades the feature gracefully; it does not raise an error.

The design's Permission Request screen covers camera/photos and notifications. It does **not** yet cover AI processing, location, or integration data use — those consent surfaces need designing before launch.

### 7.2 GDPR and NDPA obligations

- **RoPA** — every table and field documented with lawful basis, retention TTL, and whether it leaves the system. Anything absent from the register may not be collected.
- **Data subject rights** — export, delete, rectify, restrict. Deletion is orchestrated by event with a ledger tracking per-module acknowledgement against a 30-day SLA, and reaches third parties (CDN derivatives, analytics profiles, push tokens, integration token revocation).
- **Minimization** — events carry IDs; logs carry `user_id` and `trace_id` only. Analytics receives a pseudonymous identifier.
- **Encryption** — TLS in transit including service-to-service; envelope encryption at rest for phone, email, body profile, measurements, and OAuth tokens, with a rotatable key. Encrypted-column lookups use a blind index (HMAC with a pepper) so login remains an index scan.
- **AI boundary** — model providers restricted to a zero-retention, no-training allowlist; sub-processor list published; nothing containing PII reaches a model.
- **Residency** — single primary region with the transfer basis documented; a second region remains feasible because PII is confined to the `gateway` and `media` schemas.
- **Age gate** — 16+, verified at registration, enforced before any personalization consent.

### 7.3 Image PII pipeline (`media`, server-authoritative)

Every user-supplied image — fabric, fit, vault item, cached pin — passes the same pipeline before storage, sharing, or model use:

1. **Safety classification** — reject NSFW, minors, non-apparel. Rejected images are not persisted.
2. **EXIF strip** — GPS, device identifiers, timestamps. The most common silent location leak in any photo-upload product.
3. **Face detection and irreversible redaction** — blur or mask on the derivative used for AI, sharing, and tailor shares. Detection runs on an in-process open model; sending an unredacted face to a third party in order to detect the face defeats the purpose.
4. **OCR scan and text redaction** — names, phone numbers, addresses, card digits caught in frame are masked before the image becomes model input.
5. **Original handling** — discarded by default once the derivative exists. Retention requires explicit consent, encrypted storage, and a TTL.

The Flutter client may blur locally for preview quality, but the server repeats every step and treats client output as untrusted. A client-only blur is not a privacy control.

Pipeline outcomes are recorded per asset (`exif_stripped`, `faces_redacted`, `ocr_redacted`, `safety_verdict`), so compliance is queryable and a pipeline bug is visible rather than silent.

### 7.4 Prompt injection

FAUE feeds untrusted internet content — Pinterest pins, Instagram posts, user uploads, scraped product descriptions — into a model holding real tools. This is a live threat, not a theoretical one.

- **Trust tiers** — system prompt trusted; tool results semi-trusted; user text, images, OCR output, pin captions, and product descriptions **always untrusted**.
- **Channel separation** — untrusted content never enters the system-prompt channel and is always delimited and labeled as data.
- **Ingest-time detection** — heuristics plus a classifier over imported captions and descriptions.
- **OCR text as an injection vector** — the case most often missed, and FAUE processes user photos as a core flow.
- **Tool authorization independent of the model** — a successful injection still cannot invoke a tool the session lacks rights to. The spree tool surface is read-only; nothing mutates state or spends money.
- **Output validation** against the candidate set, so an injected instruction cannot surface a foreign URL or product.
- **Budgets** — per-session tool-call and token caps.
- **Testing** — a dedicated injection suite in the eval harness, run in CI, plus a red-team checklist before any release touching prompts or tools.

### 7.5 Platform security

- **Secrets** — never committed; encrypted at rest (SOPS or a secrets manager) and rotated on schedule.
- **Immediate action required:** the `api-gateway` git remote currently embeds a GitHub personal access token in its URL. That token must be revoked and the remote reset to a plain HTTPS or SSH URL with a credential helper.
- **Service-to-service** — short-TTL service JWTs with audience claims; `ase` is not reachable from the public internet.
- **Rate limiting** at the edge per IP, per user, and per endpoint class, with stricter limits on OTP, uploads, generation, and spree.
- **Upload safety** — size caps, MIME sniffing rather than extension trust, image re-encoding to strip payloads, malware scanning, and signed direct-to-CDN uploads with short-lived credentials.
- **Baseline** — parameterized queries only, output escaping, CORS allowlist, security headers, dependency scanning, SAST in CI.
- **Backups** — nightly dumps plus PITR, restore tested quarterly. Vectors are derived data, excluded from backups and rebuildable.
- **Incident response** — severity ladder, breach notification path (GDPR 72 hours, NDPA equivalent) written before it is needed.
- **Threat model** — STRIDE pass over each trust boundary: client→gateway, gateway→ase, ase→model provider, integrations→ingest, staff→admin.

### 7.6 Spree guardrails

Layered, each implemented as a separate testable object rather than prompt text:

- **Input** — image safety classification and an intent classifier scoping to fashion; off-topic returns a templated refusal without model spend.
- **Grounding** — no product, price, or brand claim survives without a matching tool result.
- **Output** — no body-shaming, no medical or weight advice, no purchase or delivery promises, no PII echo; second-pass moderation on the generated answer.
- **Abuse** — per-user rate limits, daily token budget, maximum images per session.
- **Operations** — full logging with `trace_id`, a refusal taxonomy, and a human review queue for flagged sessions.

---

## 8. Data architecture

Single PostgreSQL cluster, schema per service, UUIDv7 identifiers throughout (time-sortable, non-enumerable).

### 8.1 `gateway`

```
users · auth_identities · refresh_tokens
profiles · body_profile · style_preferences · quiz_responses (append-only)
vault_items · wear_log · saved_looks · feedback_signals · action_events
consents · deletion_ledger · integration_accounts
notify_preferences · notify_deliveries · notify_inbox
admin_users · audit_log (append-only)
```

`body_profile` holds body shape, optional height and measurements, fit preference, sizes by brand, and consent flags. It is sensitive PII: opt-in per field, encrypted, user-deletable, never present in event payloads, and never sent raw to a model — `ase` converts it to abstract silhouette constraints (`avoid: boxy_crop`, `favor: defined_waist`) before anything leaves the service. Body shape drives **hard constraints in filtering and ranking**, because a vector alone will not learn which cuts flatter which shapes from a small dataset.

**Body profile capture is in scope.** It has no screens in the current design and must be added. Specification for the frontend engineer:

- **Placement** — an optional step immediately after the DNA result, framed as "help FAUE fit you better", plus a permanently editable section in Profile. Skippable without penalty; the engine degrades to DNA-only constraints when absent.
- **Fields** — body shape (illustrated options per gender presentation), height, fit preference (fitted / regular / relaxed), and sizes by category. Detailed measurements are a separate, clearly optional expansion.
- **Framing** — no numeric scoring, no "ideal" body language, no before/after imagery. The copy explains what each field improves in the recommendations.
- **Consent** — captured under `personalization` with a distinct, plain-language notice that this is sensitive data, encrypted, deletable at any time, and never shared with a model in raw form.

### 8.2 `ase`

```
user_style_context (dna_vector, aspiration_vector, behavior_vector, constraints)
product_embeddings · style_embeddings · fabric_embeddings
vault_embeddings · aspiration_embeddings
looks · look_jobs · look_impressions
fabric_analyses · style_library · accessory_pairings · compatibility_rules
spree_sessions · spree_messages (TTL-bounded)
agent_memory · agent_runs · weather_cache
```

Three separate vectors rather than one blend: DNA (stated taste), aspiration (Pinterest/Instagram), behavior (learned from wear and saves). Blend weights shift over a user's lifetime — cold start leans on DNA, mature users on behavior — so reweighting is a config change rather than a re-embed.

`look_impressions` records served position and candidate-set hash. Logging this is cheap now and impossible to reconstruct later; without it, future ranking models train on position-biased data.

### 8.3 `catalog` (`M1-2`) and `media` (`M1-2`)

```
catalog: brands · products · product_images · ingest_jobs · link_health · curation_queue
media:   assets · render_jobs
```

`products.status` (`active | out_of_stock | dead_link | archived`) governs index inclusion, so a dead link never reaches a user between syncs.

### 8.4 pgvector strategy

- **HNSW** (`m=16, ef_construction=64`, `ef_search` tuned per query type) — better recall at this scale than IVFFlat, no training step, tolerates incremental inserts.
- **Cosine distance** with vectors normalized on write.
- **Partial indexes per `model_id`**, so multiple embedding models coexist during migration without index bloat.
- **Pre-filter over post-filter** — hard filters applied after ANN collapse narrow result sets. Approach: partial indexes on high-selectivity dimensions, over-fetch `k * 4`, then filter, with a rules-only fallback when the filtered set is thin.

### 8.5 Migrations — one Alembic project

All schemas live in one repository, `faue-db`, which ships both the SQLAlchemy models and the single Alembic project:

```
faue-db/
├─ faue_db/{base,registry}.py
├─ faue_db/{gateway,ase,catalog,media}/models.py
├─ migrations/{env.py,versions/}
└─ tests/
```

Services install it pinned (`faue-db @ git+ssh://...@v0.4.2`). A model change and its migration land in the same pull request, in the same repository — the guarantee is enforced by CI rather than remembered.

**CI gates:** a scratch Postgres runs `alembic upgrade head` then `alembic check`; a non-empty autogenerate diff fails the build. Each revision is also exercised up → down → up, so a broken downgrade is caught at author time.

**Ownership is preserved** by two mechanisms: `CODEOWNERS` per schema directory, and PostgreSQL roles granted only on their own schema, so cross-schema access fails at the database rather than by convention. A separate migrator role owns DDL; service roles hold DML only and cannot alter tables.

**Deploy order** is fixed: migrate first (expand-only — additive, nullable, new tables), then deploy code, then contract in a later release. A breaking migration never ships in the same release as the code needing it, which is what makes rollback safe.

**Tradeoff:** one history means one coordination point, and a service can no longer ship schema changes independently. At a two-person team this is a clear win. The exit path, if the team grows, is splitting `faue_db/<service>` into per-service projects — mechanical, because the schemas are already disjoint and role-isolated.

---

## 9. Evaluation and monitoring

### 9.1 Offline evaluation (pre-deploy gate)

Golden sets live in `faue-platform/eval/`, versioned and human-labeled, and run in CI on any prompt, model-config, rule, or ranking change.

| Set | Target size | Measures |
|---|---|---|
| `dna_answers` | 200 | Scoring correctness — deterministic, must be 100% |
| `fabric_match` | 150 | Fabric-type accuracy; style match precision@5 against stylist labels |
| `look_rank` | 100 | nDCG@10, precision@5 against stylist-ranked candidates |
| `spree_safety` | 300 | Jailbreak, injection, off-topic, PII, body-shaming, medical, purchase-promise → expected refusal |
| `spree_quality` | 150 | Groundedness (every claim traceable to a tool result), helpfulness |
| `pii_images` | 100 | Face-detection recall, EXIF strip, OCR redaction — recall must approach 1.0 |
| `render_safety` | 100 | NSFW filtering, no-likeness compliance on generated looks |

Safety and PII sets are hard blockers. Quality sets block on regression against the current production configuration rather than an absolute threshold.

Labeling is content work, not engineering work, and must start early — with no labels there is no evaluation. A labeling guide belongs in `docs/50-data/`.

LLM-as-judge is acceptable for groundedness and tone at scale, never as the sole safety gate, and is calibrated against human labels on a sample each cycle.

### 9.2 Online evaluation

- **Shadow mode** — new rankers and renderers run alongside production, scored but not served. The standard promotion path.
- **Interleaving** for ranking comparisons — better signal than a full split test at low traffic.
- **A/B framework** — deterministic bucketing by user hash, exposure logged as an event, minimum sample and duration declared upfront, guardrail metrics able to halt an experiment automatically.
- **Implicit feedback as continuous evaluation** — save rate, share rate, wear-log rate, suggestion-accept rate, regenerate rate. These are the real quality signal; offline metrics only predict them.
- **Explicit feedback** tagged with the model and prompt version that produced the result, so quality is attributable.

### 9.3 Observability

OpenTelemetry throughout, with one `trace_id` flowing from the Flutter client through gateway, ase, model calls, and back. Any user complaint must be resolvable to the exact prompt version, model, tool calls, and candidate set that produced their result.

Stack: Prometheus, Loki, Tempo, and Grafana (self-hosted or cloud free tier at this scale); Sentry for errors; Langfuse for LLM traces, prompt versions, cost, and eval runs — adopted from the start rather than retrofitted.

Logs are structured JSON containing `user_id` and `trace_id` and no PII, with a CI check that fails on PII-shaped patterns in log statements.

### 9.4 Dashboards and alerts

Six dashboards — product funnel, AI health, quality, safety, data health, infrastructure — all surfaced inside the admin dashboard rather than a separate tool.

Alerts, each with a runbook: safety guardrail trip-rate spike, groundedness drop, sustained fallback depth above one, cost per user above threshold, non-empty dead-letter queue, embedding coverage below 98%, render failure rate, quiz completion collapse, notification opt-out spike.

### 9.5 Drift and human review

Tracked drift: embedding drift (candidate-set overlap and score distributions week over week), input drift (fabric types, image quality, spree intent mix), and catalog integrity (link health, staleness, duplicates, embedding coverage).

Flagged sessions, low-rated answers, and a random sample of normal sessions route to a review queue with a labeling interface. Reviewer verdicts feed back into the golden sets, which is what keeps evaluation current rather than frozen at launch.

---

## 10. Admin dashboard

Internal-only, separate deployment and domain, backed by `gateway.admin` at `/admin/v1/*` under a **separate auth realm** — different issuer, audience, and token lifetime from user auth.

**MVP surface:** embedded observability dashboards; vault and style-library content tooling; AI review queue; user support (lookup, state view, DSR trigger, read-only impersonation with consent and audit); feature flags and AI kill switches.

**M1-2 / M3+:** experiments, notification composer, model and prompt configuration with eval history, curation intelligence, catalog operations, brand and partner administration, commerce operations, moderation at scale.

Because admin is the largest PII exposure in the system, it carries controls the user API does not: mandatory MFA for all staff; role-based access with per-capability permissions; an immutable audit log recording every PII read and every mutation with actor, target, before/after, justification, and IP; PII masked by default with an explicit reveal action requiring a reason; time-boxed break-glass access that alerts a second person; confirmation on destructive actions; and a network gate (VPN, SSO, or IP allowlist) in front of the entire application.

**Design principle:** every new backend capability ships with its admin surface specified in the same LLD section. Otherwise the dashboard permanently lags the system and staff end up in `psql`.

---

## 11. Repositories and environments

### 11.1 Repositories

The workspace root (`/faue`) is **not** a git repository. Every child directory is a standalone repository under `github.com/faueofficial`.

| Directory | Repository | Stack | Stage |
|---|---|---|---|
| `docs/` | `faue-platform` | Markdown, YAML | MVP |
| `faue-core/` | `faue-core` | Python library | MVP |
| `faue-db/` | `faue-db` | Python, Alembic | MVP |
| `api-gateway/` | `api-gateway` | FastAPI | MVP |
| `ase/` | `ase` | FastAPI, workers | MVP |
| `app/` | `faue-app` | Flutter | MVP |
| `web/` | `faue-web` | Next.js | MVP |
| `admin/` | `faue-admin` | Next.js | MVP |
| `infra/` | `faue-infra` | Compose, CI templates | MVP |
| `catalog/` | `catalog` | FastAPI | M1-2 |
| `media/` | `media` | FastAPI | M1-2 |

`docs/repos.yaml` plus `docs/scripts/bootstrap.sh` clone and update every sibling. That manifest is the monorepo substitute.

`faue-core` holds the plumbing all services share, because copy-paste drifts: event envelope, outbox publisher, idempotent consumer base, OpenTelemetry wiring, PII-scrubbing structured logging, envelope encryption and blind-index helpers, the consent dependency, error taxonomy with RFC 7807 responses, service-JWT signing and verification, and configuration loading.

`atelier/`, `archive/`, and `borr/` remain outside the map. `atelier/drip-match` is a prototype: inspection during repo cleanup found its composer and clash detector both raising `NotImplementedError`, so only `services/scorer.py` held working code. That file is ported to `ase/app/engine/scoring.py`; its ChromaDB layer is not carried forward.

### 11.2 Shared Python environment

One `.venv` at the workspace root, managed with `pip` and `pip-tools`. `faue-core` owns the shared dependency contract:

```
faue-core/requirements/
├─ base.in / base.txt      # FastAPI, SQLAlchemy, Pydantic, OTel, shared runtime
├─ web.in  / web.txt
├─ worker.in / worker.txt
├─ ml.in   / ml.txt        # ase only — embeddings, vision, image handling
├─ dev.in  / dev.txt
└─ constraints.txt         # shared pins every service resolves against
```

Services declare their role files and install editable (`pip install -e ./api-gateway`) into the single environment. `constraints.txt` is what prevents version drift between services. Docker images install only their role's compiled file, so the ML stack never ships in the gateway image.

Tradeoff: one environment means a service cannot upgrade a shared dependency alone. Mitigated by isolating `ml` requirements to `ase`. If the ML stack ever conflicts with the web stack, the exit is giving `ase` its own environment — the constraints file makes that split mechanical.

### 11.3 Environments

| Environment | Purpose | Data |
|---|---|---|
| `local` | Services run directly under uvicorn on fixed ports (gateway 8000, ase 8001, catalog 8002, media 8003) | Seeded fixtures |
| `staging` | Full stack, production-shaped, stable URL for the frontend engineer | Synthetic and anonymized |
| `prod` | Live | Real |

Local development does not require containers. `faue-infra/compose.yaml` provides an infra-only profile (Postgres with pgvector, Redis, RabbitMQ, MinIO) for full-fidelity work, but the documented default is a hosted development database, hosted Redis, and the in-process event bus behind the same `EventPublisher` interface — chosen deliberately to keep local disk and memory usage low.

The gateway also offers **mock mode**: recorded fixtures per endpoint behind a header, so the frontend engineer can build screens before the corresponding backend flow exists.

### 11.4 Deployment

Railway first, with a VPS evaluated over time on cost. Both paths documented, with the break-even calculation written down rather than argued.

- Each service is a Railway service; Postgres and Redis as plugins; RabbitMQ from a template or CloudAMQP.
- `ase` uses private networking with no public domain.
- Batch embedding and render jobs run as scheduled or one-off jobs, so heavy containers exist only while running.
- Static surfaces (`faue-web`, `faue-admin`) deploy to Vercel; the Flutter app ships to TestFlight and the Play internal track from CI.
- CI/CD per repository with templates in `faue-infra`: lint → typecheck → test → build image → push → deploy on tag. The `faue-db` migration job runs before service deployment, gated on the `alembic check` test.
- Rollback: images tagged by commit; expand-only migrations mean rollback never requires a down-migration in production.

### 11.5 Conventions

Python 3.12, FastAPI, SQLAlchemy 2.0 async, Pydantic v2, `pip` + `pip-tools`, `ruff` and `mypy --strict` over `app/`, pytest with testcontainers, pre-commit, Conventional Commits, trunk-based development with short-lived branches, semantic versioning on `faue-core` and `faue-db`, `/healthz` `/readyz` `/metrics` on every service, RFC 7807 error responses, and `X-Trace-Id` propagated end to end.

---

## 12. Design system and screen inventory

Extracted from Figma file `KtCAHrBGLQXEdQrPbWJVVS` on 2026-08-17.

**Colour — primary (green):** 50 `#BCC9C4`, 100 `#A9B9B4`, 200 `#829A92`, 300 `#5C7B71`, 400 `#355C4F`, 500 `#0F3D2E`, 600 `#0D3327`, 700 `#0A291F`, 800 `#082018`, 900 `#051611`; hover `#145C45`.

**Colour — neutral:** 50 `#F7F8F8`, 100 `#EDEEF1`, 200 `#D8DBDF`, 300 `#B6BAC3`, 400 `#8E95A2`, 500 `#6B7280`, 600 `#5B616E`, 700 `#4A4E5A`, 800 `#40444C`, 900 `#383A42`, 950 `#25272C`; white `#FFFFFF`, black `#1E1F20`.

**Colour — semantic:** success `#2ECC71`; error `#CB1A14` (hover `#DD524D`, focus `#9E0A05`, tint `#FBEAE9`); text-secondary `#A8A8A8`; disabled `#D0D5DD`; divider `#E4E7EC`.

**Typography:** Playfair Display for display and headings (82 / 66 / 52 / 42 / 34 / 26 / 22 / 16 px); Plus Jakarta Sans for body and UI (16 / 14 / 12 / 8 px), weights Regular, Medium, SemiBold, Bold.

**Spacing scale:** 4, 8, 12, 16, 20, 24, 28, 32, 40, 48, 64, 80, 96, 128, 160, 192.

**Components:** buttons (primary, secondary, destructive × solid/outlined × sm/lg × default/hover/focused/disabled × none/leading/trailing/icon-only), chips (input, filter × default/disabled/focused × icon on/off), input fields (default, hover, active, typing, filled, success, error, read-only), loading indicators, progress bars, progress circles, bottom navigation.

**Known drift to correct:** the bottom-navigation component uses `#613EEA` and SF Pro Text, inconsistent with the green/Plus Jakarta Sans system.

**Screens:** 72 hi-fi frames at 428×926 (mobile) plus a 1440-wide landing page, covering splash, hook, sign-up/log-in, username, processing, six Style DNA questions, DNA result and share, Pinterest connect, wardrobe upload, dashboard (three variants), generate (with Style Fabric / Generate Look / Style Studio / Use my vault), fabric upload, review item, building states, error state, AI results and details, style details, "Why this works for you", share designs, saved looks with empty states, vault with empty states, item upload/details/edit/delete, notifications, profile, edit profile, connected accounts, permission requests, and logout confirmation.

The full registry — screen, node id, route, endpoints, states, components, and build status — is written to `docs/40-frontend/screens.md` in documentation batch 2.

### Content gaps found in the design

1. Only one answer option is drawn per Style DNA question; the remaining options are content to be written (§16.1) and relayed to the frontend engineer.
2. No body-shape or measurement capture screens; specification for them is in §8.1 and they need designing.
3. No consent surfaces for AI processing, location, or integration data use — only camera/photos and notifications.
4. The persona shown ("The Cultural Minimalist") predates the taxonomy, which FAUE now defines itself (§16.1).
5. The Instagram card must be removed from Connected Accounts and onboarding (§4.6).
6. Magic-link authentication needs a verification/landing screen and a cross-device code-entry state, neither of which exists in the design (§4.1).
7. Look generation needs a job-progress model in the client — the "Building your fit… 70%" screen implies polling or SSE, not a blocking request.

---

## 12A. Style library sourcing policy

The 30-style native library is FAUE's most defensible content asset. Its value is the **structured taxonomy** — silhouette, fabric suitability, formality, occasion, body notes — not the photographs. Images illustrate; the tags do the work. Sourcing effort is budgeted accordingly.

**Primary source — licensed from Nigerian tailors and design houses.** Approach 5–10 tailors and small labels and license existing portfolio images non-exclusively for in-product and marketing use, with visible attribution and an outbound link. Cost is near zero, the imagery is culturally authentic in a way stock photography is not, attribution provides real value to the source, and the relationships seed the `Y2` tailor network. Requires a one-page written agreement per source, and a model release wherever a face is identifiable.

**Secondary source — generated reference images.** Because generative rendering is the default strategy, generated references keep the library visually consistent with the product's own output, carry no licensing exposure, and scale instantly. Two constraints: generated native wear is frequently wrong in the details — Agbada proportions, gele structure, embroidery placement — so **every generated reference requires stylist sign-off before entering the library**; and the provider's commercial-use terms must be verified for output rights. Used to fill gaps in the fabric × style matrix, never as the primary source.

**Later — one commissioned shoot.** Once usage data identifies the styles that matter, a single day with a tailor, two models, and a photographer yields owned, on-brand, consistent imagery for the top ten styles. A real cost, and a brand asset rather than borrowed material. Not a launch expense.

**Prohibited — scraping Instagram or Pinterest for library assets.** Linking to a pin is fine; hosting a designer's photograph as FAUE's own reference material is infringement and a takedown risk on precisely the asset the differentiator depends on. This is distinct from the catalog argument: linking to a product you do not host is standard affiliate practice, republishing a photograph is not.

**Provenance is tracked per asset** — `source`, `license_type`, `license_document`, `attribution`, `model_release`, `expires_at`, `stylist_approved_by`, `generated` — because an unlicensed image discovered after launch means pulling it from a live product.

Sequence: license 15–20 styles from tailors, generate the remainder with stylist review, ship, then commission the shoot for whichever styles the data justifies.

## 13. Documentation plan

Target structure in `faue-platform`:

```
docs/
├─ 00-product/       vision · mvp-scope · roadmap · personas · style-dna · retention-system · metrics
├─ 10-architecture/  hld · data-flows · event-catalog · model-plane · ai-quality
│                    security · privacy · pii-handling · prompt-injection · ropa · threat-model
├─ 20-services/      <service>/{lld,api,schema,events,runbook}.md
├─ 30-contracts/     openapi/ · events/ · CHANGELOG.md
├─ 40-frontend/      screens · auth-flows · error-model · pagination · realtime
│                    design-tokens · offline-and-caching · deeplinks
├─ 50-data/          catalog-model · style-library · curation-guide · labeling-guide
├─ 60-ai/            prompts · guardrails · agent-design · rendering · eval-sets/
├─ 70-ops/           environments · deployment · observability · runbooks/ · incident-response
├─ 80-adr/           0001-*.md (MADR format, immutable once accepted)
└─ 90-meta/          conventions · glossary · doc-status
```

Writing order:

1. **Batch 1 — foundation:** `hld`, `data-flows`, `event-catalog`, `conventions`, `glossary`, `repos.yaml`, bootstrap script, and ADRs for every decision recorded here.
2. **Batch 2 — unblocks frontend:** `openapi/gateway.v1.yaml`, all of `40-frontend/` (including the screen registry and design tokens), `mvp-scope`.
3. **Batch 3 — unblocks backend build:** `lld` and `schema` for gateway and ase, `model-plane`, `privacy`, `pii-handling`, `prompt-injection`, `ropa`, and the `faue-db` model definitions.
4. **Batch 4 — quality and operations:** `ai-quality`, `guardrails`, `agent-design`, `rendering`, `security`, `threat-model`, `observability`, runbooks, `retention-system`.
5. **Batch 5 — content:** `style-library`, `curation-guide`, `labeling-guide`, `catalog-model`.

Repository cleanup follows documentation: restructure `api-gateway` to the specified layout, create `faue-core` and `faue-db`, and port `atelier/drip-match` into `ase`.

---

## 14. Retention system

Documented as a system rather than a feature list, in `docs/00-product/retention-system.md`.

**Habit loop:** trigger (daily fit, upcoming event, weather shift) → action (view, generate, log a wear, save) → reward (a look worth wearing and sharing) → investment (the vault grows, the wear log deepens, boards sync — so the next suggestion is better).

**Lifecycle:** D0 quiz and DNA card share → D1 first generation and integration connect → D3 new looks for your DNA → D7 fabric prompt → D14 wear streak → D30 DNA retake eligibility → D45 dormancy win-back.

**Cultural and seasonal triggers:** Owambe season, December weddings, Detty December, Ramadan, Christmas and Easter dressing, month-end payday.

**Compounding value:** every session should improve the next one. Retention comes from accumulated personal data the user cannot obtain elsewhere, not from notification volume.

**Metrics:** D1/D7/D30 retention, WAU/MAU stickiness, generation and save rates, wear-log rate, suggestion-accept rate, with notification opt-out rate as a guardrail.

---

## 15. Decisions recorded (candidate ADRs)

| # | Decision | Rationale |
|---|---|---|
| 0001 | Two services now (`gateway`, `ase`), four more designed | Matches the Style DNA doc's assumption; keeps operational load low while boundaries are drawn |
| 0002 | `spree` and `notify` as modules, not services | Extraction seams cost nothing now; separate deployments would |
| 0003 | No root git; per-service repositories with a manifest | Team preference; services stay independently deployable |
| 0004 | One shared Alembic project in `faue-db` | Model and migration land together, enforced by CI |
| 0005 | Single root virtualenv with `pip` + `pip-tools` and a shared constraints file | Prevents version skew between services on a familiar toolchain |
| 0006 | OpenRouter for LLMs, tier-addressed, never model-named in code | Model identifiers rot; hardcoding one is a future outage |
| 0007 | Pluggable embeddings, self-hosted default | OpenRouter has no embeddings API; provider economics differ per environment |
| 0008 | Closed-set model policy | Models rank and explain; they may not invent items outside the candidate set |
| 0009 | Pluggable look rendering (generative, composite, hybrid) | The right strategy is an empirical question; measure rather than guess |
| 0010 | Catalog and affiliate deferred to M1-2 | The design shows no shop surface; the wardrobe/fabric loop is the drawn product |
| 0011 | Six-question Style DNA quiz | The design supersedes the ten-question specification; shorter quizzes complete more often |
| 0012 | Consent denied by default, enforced by a shared dependency | GDPR and NDPA compliance cannot rely on per-endpoint discipline |
| 0013 | Server-authoritative image PII pipeline | A client-side blur is not a privacy control |
| 0014 | Untrusted-content trust tiers for all model input | FAUE feeds internet content into a model holding tools |
| 0015 | Railway first, VPS evaluated on cost | Lower operational overhead at launch; the embedding provider choice follows the host |
| 0016 | Email magic link as the primary credential, opaque and POST-consumed | Better UX than typed codes; the opaque POST-only design defeats scanner pre-fetch and URL leakage |
| 0017 | Model-led assembly within a rule-generated candidate pool | Colour harmony, proportion, and cultural fit are judgement problems; computed colour analysis is supplied as a prior |
| 0018 | Generative rendering as the default strategy | Ships the designed experience; alternatives stay behind the interface for measurement |
| 0019 | Instagram integration removed | The platform API cannot deliver what the screen promised |
| 0020 | Style library licensed from tailors, generated to fill gaps, never scraped | Authenticity, zero licensing exposure, and relationships that seed the tailor network |

---

## 16. Open questions

1. **Persona taxonomy and quiz content** — the six personas, six questions, full answer option sets, and per-option weights are FAUE-defined rather than inherited. A complete proposal is drafted in `docs/00-product/style-dna.md` (batch 1) for review, then relayed to the frontend engineer as content. Resolves the "Cultural Minimalist" mismatch by definition rather than reconciliation.
2. **Generative provider selection** — which image provider backs the default renderer, evaluated on cost per image, latency, African fashion fidelity, and commercial-use terms.
3. **Style library licensing outreach** — which tailors and design houses to approach first, and who owns those conversations.
4. **Transactional email provider** — magic-link delivery has hard deliverability requirements; the choice affects DKIM/SPF setup and the sending domain.
5. **Phone OTP timing** — deferred to `M1-2`; confirm no launch market requires it earlier.
```
