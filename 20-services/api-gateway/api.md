# api-gateway — API Reference

**Stage:** MVP · **Authoritative contract:** [`../../30-contracts/openapi/gateway.v1.yaml`](../../30-contracts/openapi/gateway.v1.yaml)

The OpenAPI document is the contract; this page adds what a specification cannot express — which consent purposes gate which route, which routes cost money, and which are rate-limited how.

---

## 1. Consent and authorisation matrix

Every route declares its purposes as dependencies. A missing grant returns `403 consent_required` with the purpose in `errors[0].field`.

| Route | Auth | Consent | Notes |
|---|---|---|---|
| `POST /auth/link/request` | none | — | Rate limited hard |
| `POST /auth/link/consume` | none | — | Single-use, POST only |
| `POST /auth/oauth/*` | none | — | |
| `POST /auth/refresh` | none | — | Reuse revokes the family |
| `POST /auth/logout` | user | — | |
| `POST /auth/username` | user | — | |
| `GET /me` | user | — | Returns consent state itself |
| `PATCH /me` | user | — | |
| `GET/PUT /me/body-profile` | user | `personalization` | Sensitive |
| `GET/PUT /me/consents` | user | — | Never gated on itself |
| `GET /quiz` | none | — | Public definition |
| `POST /quiz/submit` | user | — | Essential to the product |
| `GET /quiz/result`, `/card` | user | — | |
| `POST /quiz/retake` | user | — | Once per 30 days |
| `POST /uploads/sign` | user | `camera_photos` | |
| `GET /uploads/{id}` | user | — | |
| `GET/POST /vault/items` | user | — | |
| `PATCH/DELETE /vault/items/{id}` | user | — | |
| `POST /vault/items/{id}/style` | user | `ai_processing` | **Costs money** |
| `POST /vault/wear` | user | — | |
| `POST /looks/generate` | user | `ai_processing` | **Costs money** |
| `POST /looks/{id}/regenerate` | user | `ai_processing` | **Costs money** |
| `POST /looks/{id}/adjust` | user | `ai_processing` | **Costs money** |
| `GET /looks`, `/looks/{id}` | user | — | |
| `POST /looks/{id}/save`, `/share`, `/feedback` | user | — | |
| `POST /fabric/{id}/style` | user | `ai_processing` | **Costs money** |
| `POST /fabric/{id}/tailor-share` | user | — | Render only |
| `POST /spree/sessions` | user | `ai_processing` | |
| `POST /spree/.../messages` | user | `ai_processing` | **Costs money** |
| `GET /agent/today` | user | `personalization` | |
| `GET/PUT /agent/settings` | user | `agent_proactive` for push | `M1-2` |
| `GET /integrations` | user | — | |
| `GET /integrations/pinterest/authorize` | user | `pinterest_sync` | |
| `POST /integrations/pinterest/import` | user | `pinterest_sync` | |
| `DELETE /integrations/{provider}` | user | — | Revocation never gated |
| `GET /notifications*` | user | — | |
| `PUT /notifications/preferences` | user | — | |
| `POST /notifications/devices` | user | — | |
| `POST /privacy/*` | user | — | Rights are never gated on consent |

Two rules that hold without exception: **revocation is never blocked**, and **privacy rights are never gated**. Both would be unlawful.

`use_weather: true` on generation additionally requires `location_weather`. Without it the request still succeeds — weather is simply not used, and the response says so.

---

## 2. Rate limits

Per user unless stated. Exceeding returns `429` with `Retry-After`.

| Class | Limit | Rationale |
|---|---|---|
| `POST /auth/link/request` | 3/hour per address, 10/hour per IP | Email cost and enumeration defence |
| `POST /auth/link/consume` | 10/hour per IP | Brute-force defence |
| `POST /auth/oauth/*` | 20/hour | |
| Generation (`/looks/*`, `/vault/items/{id}/style`) | 20/day, 5/hour | Cost control |
| `POST /fabric/{id}/style` | 30/day | Cost control |
| `POST /spree/.../messages` | 50/day, 20/hour | Cost control |
| `POST /uploads/sign` | 100/day | Storage cost |
| Reads | 300/minute | Abuse defence only |
| Admin | 600/minute | Internal |

Generation limits are also enforced as a **token budget** in `ase`, since a request count is a poor proxy for spend. Hitting the budget emits `ai.budget.exceeded` and degrades rather than erroring.

---

## 3. Idempotency

Required on mutations that spend money or send messages:

`POST /looks/generate`, `/regenerate`, `/adjust`, `/vault/items/{id}/style`, `/fabric/{id}/style`, `/auth/link/request`, `/privacy/delete`.

```
Idempotency-Key: <uuid generated when the user acted>
```

Keys are stored for 24 hours. A repeat with the same key returns the original response rather than doing the work again. Generate the key at the moment of user intent, not at send time, so a retry after a crash reuses it.

---

## 4. Headers

| Header | Direction | Purpose |
|---|---|---|
| `Authorization: Bearer` | in | Access token |
| `X-Trace-Id` | both | Propagated end to end; generated at the edge if absent |
| `X-Client-Version` | in | Compatibility gating and debugging |
| `Idempotency-Key` | in | See above |
| `X-Mock-Mode` | in | Staging only — returns recorded fixtures |
| `Retry-After` | out | On 429 and 503 |

### Mock mode

On staging, `X-Mock-Mode: true` returns recorded fixtures for every endpoint. It exists so the frontend engineer can build screens before the corresponding backend flow is finished, which he will need for at least the first several weeks. Mock mode is rejected in production.

---

## 5. Versioning

`/v1` is stable. Additive changes — new endpoints, new optional fields, new enum values — happen within it and are recorded in [`../../30-contracts/CHANGELOG.md`](../../30-contracts/CHANGELOG.md).

Breaking changes require `/v2` running in parallel. Clients must tolerate unknown fields and unknown enum values; a client that crashes on a new occasion type is a client that blocks every future release.

---

## 6. Admin API

`/admin/v1/*`, separate auth realm, documented in [`../admin.md`](../admin.md). Never accessible with a user token, never exposed on the public domain, and always behind the network gate.
