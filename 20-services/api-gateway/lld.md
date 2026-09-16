# api-gateway — Low-Level Design

**Stage:** MVP · **Repo:** `faueofficial/api-gateway` · **Schema:** `gateway` · **Ingress:** public

The only service reachable from the internet. It owns identity and all PII, and it is the only service that makes synchronous calls to other services.

---

## 1. Responsibilities

| Owns | Does not own |
|---|---|
| Identity, sessions, account linking | Style vectors, embeddings, retrieval |
| Profile, body profile, consent | Look assembly, ranking, rendering |
| Style DNA scoring | Fabric classification |
| Vault items, wear log | Conversational sessions |
| Saved looks, feedback, actions | Weather context |
| Pinterest integration and sync | |
| Notifications (module) | |
| Privacy and DSR orchestration | |
| Admin API (module) | |

The gateway never computes style. It stores what the user told us and asks `ase` for anything requiring judgement.

---

## 2. Module layout

```
app/
├─ main.py                 app factory, middleware stack, lifespan
├─ config.py               one Settings class, read once at startup
├─ deps.py                 current_user, require_consent, require_scope, db, redis, trace
├─ api/
│  ├─ v1/                  routers — HTTP shape only, no business logic
│  │  auth.py profile.py quiz.py vault.py looks.py fabric.py spree.py
│  │  agent.py integrations.py notifications.py uploads.py privacy.py
│  └─ admin/v1/            separate auth realm
│     catalog.py styles.py review.py users.py flags.py metrics.py
├─ modules/                bounded contexts — the business logic
│  ├─ identity/            magic_link.py oidc_google.py oidc_apple.py
│  │                       linking.py tokens.py service.py
│  ├─ quiz/                scoring.py personas.yaml service.py
│  ├─ profile/             service.py body.py consent.py
│  ├─ vault/               service.py wear.py
│  ├─ looks/               service.py            (delegates to ase)
│  ├─ integrations/
│  │  └─ pinterest/        oauth.py sync.py boards.py token_vault.py
│  ├─ notify/              EXTRACTABLE
│  │  ├─ service.py templates/ preferences.py dispatcher.py
│  │  └─ channels/         push.py whatsapp.py email.py sms.py inbox.py
│  ├─ privacy/             dsr.py deletion_ledger.py export.py
│  └─ admin/               rbac.py audit.py masking.py break_glass.py
├─ clients/                ase_client.py media_client.py
├─ events/                 publisher.py consumers.py handlers/
└─ workers/                pinterest_sync.py notify_dispatch.py
                           lifecycle.py dsr_purge.py retention_ttl.py
```

### Rules

**Routers hold no business logic.** A router validates, calls one module function, and shapes the response. A branch in a router that is not about HTTP belongs in a module.

**Modules expose a service class.** `IdentityService`, `VaultService`, `NotifyService`. Other modules depend on the class, never on internals or on another module's tables.

**Modules raise domain exceptions.** `ConsentMissing`, `LinkExpired`, `UsernameTaken`. Translation to HTTP happens once, in an exception handler. No module imports `HTTPException`.

---

## 3. Request lifecycle

```
request
  → TraceMiddleware        adopt or generate X-Trace-Id, bind to context
  → LoggingMiddleware      structured access log, PII-scrubbed
  → CORSMiddleware         allowlist per environment
  → RateLimitMiddleware    Redis, per IP + per user + per endpoint class
  → AuthDependency         verify JWT, load user, reject on revocation
  → ConsentDependency      check declared purposes for this route
  → router                 validate → module call → response model
  → ExceptionHandler       domain exception → RFC 7807 problem document
response
```

`require_consent` is a dependency, not a call inside a handler. A route that needs a purpose declares it in its signature, so it cannot be forgotten:

```python
@router.post("/looks/generate")
async def generate(
    body: GenerateRequest,
    user: User = Depends(current_user),
    _: None = Depends(require_consent("ai_processing")),
) -> JobEnvelope:
    return await looks_service.generate(user.id, body)
```

---

## 4. Key modules

### identity

Magic link is the primary path. The token is 32 random bytes, stored in Redis as `SHA-256(token) → {user_identifier, session_challenge, attempts}` with a 600-second TTL, consumed atomically via a Lua script so two concurrent consumes cannot both succeed.

Requesting a new link deletes the previous token for that identifier — one active token per address, always.

OAuth verification fetches and caches provider JWKS with a 24-hour TTL and a forced refresh on unknown `kid`. Apple's client secret is an ES256 JWT regenerated on a schedule; it expires in at most six months and a lapse breaks all Apple sign-ins at once, so its expiry is an alert.

Refresh tokens rotate on use, tracked as families. Presenting a rotated token revokes the family — this is theft detection, and the alert threshold on it is deliberately low.

### quiz

Pure scoring. No database, no clock, no model. Reads `personas.yaml`, applies weights, sharpens, ranks, breaks ties. Fully deterministic and gated at 100% by the `dna_answers` golden set over all 3,072 answer combinations. See [`../../00-product/style-dna.md`](../../00-product/style-dna.md).

### integrations/pinterest

OAuth2 with PKCE. Tokens encrypted with envelope encryption before storage. The sync worker paginates per board, persists a cursor, honours rate limits with backoff, refreshes on 401, and permanently stops on revocation, marking the account disconnected and emitting `integration.disconnected`.

Imported pin images go through the media PII pipeline like any other image. Pins are private to the user and never republished.

### notify — extractable

The extraction seam that matters: **notify is invoked only by consuming events**. No request handler calls it. If a handler ever calls it inline, extraction stops being a deploy change and becomes a refactor of every caller.

Dispatch order: resolve template and locale → check the category's consent purpose → check quiet hours in WAT → check the per-user frequency cap → deduplicate on `event_id` → send → record delivery.

### privacy

Deletion is an orchestration, not a `DELETE`. Create a ledger row with a 30-day SLA, emit `user.deletion.requested`, and wait for every module and third party to acknowledge. Third-party purges — CDN assets, analytics profile, push tokens, Pinterest token revocation — are tracked in the same ledger. An alert fires five days before the SLA if the ledger is still open.

### admin

Separate auth realm: different issuer, audience claim, and token lifetime. MFA mandatory. Every PII read and every mutation writes an append-only audit row with actor, action, target, before and after, justification, and IP. PII renders masked by default; revealing requires a reason and writes an audit entry.

---

## 5. Outbound calls

| Target | Purpose | Timeout | On failure |
|---|---|---|---|
| `ase` | Generation, fabric, spree, agent | 5 s (jobs), 30 s (spree stream) | 503 with the designed error state |
| `media` module | Signed uploads, renders | 3 s | Queue and retry; asset stays `processing` |
| Pinterest | OAuth, boards, pins | 10 s | Backoff; sync resumes from cursor |
| Email provider | Magic links | 5 s | Retry twice, then surface a send failure |
| FCM / APNs | Push | 5 s | Retry via the queue; drop after 5 attempts |

All outbound calls carry the trace id. Every one has a circuit breaker and a defined degraded behaviour — no call is allowed to be "assume it works".

---

## 6. Background workers

| Worker | Schedule | Does |
|---|---|---|
| `pinterest_sync` | On demand + daily | Incremental board and pin import |
| `notify_dispatch` | Event-driven | Consumes events, dispatches notifications |
| `lifecycle` | Hourly | D1/D3/D7/D14/D30 lifecycle campaigns |
| `dsr_purge` | Event-driven | Executes deletion for gateway-owned data |
| `retention_ttl` | Daily | Enforces retention TTLs from the RoPA |
| `outbox_relay` | Continuous | Publishes outbox rows to RabbitMQ |
| `link_cleanup` | Every 5 min | Removes expired magic-link tokens |

---

## 7. Configuration

Every variable is documented in `.env.example`. Missing required variables fail at startup, loudly, rather than on first use.

```
DATABASE_URL, REDIS_URL, RABBITMQ_URL, EVENT_TRANSPORT
JWT_PRIVATE_KEY, JWT_PUBLIC_KEY, JWT_PUBLIC_KEY_NEXT, SERVICE_JWT_SECRET
ENCRYPTION_MASTER_KEY, BLIND_INDEX_PEPPER
ASE_BASE_URL, ASE_SERVICE_TOKEN   # the token is shared with ase
GOOGLE_CLIENT_ID, APPLE_TEAM_ID, APPLE_KEY_ID, APPLE_PRIVATE_KEY
PINTEREST_CLIENT_ID, PINTEREST_CLIENT_SECRET
RESEND_API_KEY, EMAIL_FROM_DOMAIN   # sending domain, NOT the contact address
CLOUDINARY_URL, FCM_CREDENTIALS, APNS_CREDENTIALS
POSTHOG_KEY, OTEL_EXPORTER_OTLP_ENDPOINT
RATE_LIMIT_*, MAGIC_LINK_TTL_SECONDS, ACCESS_TOKEN_TTL_SECONDS
```

---

## 8. Testing

| Layer | Covers |
|---|---|
| `tests/unit/` | Quiz scoring (100% branch), consent logic, tie-breaks, token rotation, template selection |
| `tests/integration/` | Repositories, migrations, event consumers, idempotency, Redis atomicity |
| `tests/contract/` | Every response validated against `gateway.v1.yaml` |

Specific cases that must exist because they are the ones that break in production: concurrent magic-link consumption, concurrent token refresh, replayed events, consent revoked mid-request, and deletion with a module that never acknowledges.

---

## 9. Extraction readiness

| Module | Becomes | Blocked by |
|---|---|---|
| `notify` | `notify` service | Nothing — event-driven already |
| `media` responsibilities | `media` service | Currently a thin client; extract when image CPU dominates |
| `admin` | `admin-api` | Nothing — separate namespace and realm already |

For each, the checklist is the same: own tables prefixed, interface-only access, event-driven invocation, separate configuration namespace and OpenAPI fragment.
