# ase — Internal API

**Stage:** MVP · **Ingress:** private network only · **Auth:** service JWT

Called by `api-gateway` and nothing else. Not exposed on any public domain, not reachable from the internet, and no user token is ever accepted.

---

## 1. Service authentication

```
Authorization: Bearer <service_jwt>
X-Trace-Id: <propagated>
X-User-Id: <uuid>        the subject of the request; ase has no session concept
```

The service JWT is short-lived (5 minutes), signed with `SERVICE_JWT_SECRET`, and carries `aud: ase`. A token with the wrong audience is rejected — that check is what stops a user token from ever working here even if one leaked into the wrong header.

`ase` trusts `X-User-Id` because the caller is authenticated as the gateway. It has no way to verify a user itself, and should not.

---

## 2. Endpoints

### Looks

```
POST /internal/looks/generate
  { user_id, source, item_ids?, fabric_asset_id?, occasion?, mood?, note?,
    use_weather, count, constraints, style_context_hint? }
  → 202 { job_id }

GET  /internal/looks/jobs/{job_id}
  → { job_id, status, progress, label, result?, error? }

GET  /internal/looks/{look_id}
  → full look

POST /internal/looks/{look_id}/regenerate   → 202 { job_id }
POST /internal/looks/{look_id}/adjust       → 202 { job_id }
```

`constraints` are the derived silhouette rules from `gateway`. `ase` never receives measurements.

### Fabric

```
POST /internal/fabric/suggest
  { user_id, asset_id, fabric_type?, occasion?, gender_presentation?, constraints[] }
  → { detected_type, confidence, attributes, styles[3..5] }
```

Synchronous, typically under 15 seconds.

### Spree

```
POST /internal/spree/sessions            { user_id } → { session_id }
POST /internal/spree/sessions/{id}/messages
  { user_id, text?, asset_ids[] }
  → text/event-stream
GET  /internal/spree/sessions/{id}       → redacted history
```

### Agent

```
GET  /internal/agent/today       ?user_id=      → suggestion, generating if absent
POST /internal/agent/runs/{run_id}/outcome
  { outcome: accepted|dismissed|regenerate }    → 204
```

### Context

```
GET /internal/context/weather?geohash5=&user_id=
  → { temp_c, feels_like_c, condition, rain_probability, humidity, uv, dust_index }
```

Returns `204` when weather is unavailable or consent is absent. Callers proceed without it; this is never an error.

### Embeddings and admin

```
POST /internal/embeddings/item      { item_id, user_id, image_url }   → 202
POST /internal/embeddings/reembed   { model_id, subject_type }        → 202
GET  /internal/admin/health         → pipeline stage timings, budget state, index stats
GET  /internal/admin/model-config   → resolved task → tier → model mapping
POST /internal/admin/kill-switch    { task, enabled }                 → 204
```

---

## 3. Timeouts and degradation

| Operation | Gateway timeout | On timeout |
|---|---|---|
| `looks/generate` (enqueue) | 5 s | 503, designed error state |
| `looks/jobs/{id}` | 2 s | Client keeps polling |
| `fabric/suggest` | 30 s | 503, designed error state |
| `spree` stream | 30 s idle | Stream closes; partial answer retained |
| `context/weather` | 2 s | Proceed without weather, silently |
| `embeddings/*` | 5 s | Retry via queue; item stays unembedded |

Every call has a circuit breaker. When it opens, the gateway serves the degraded path immediately rather than waiting for a timeout on every request.

---

## 4. Error codes

| Code | Status | Meaning |
|---|---|---|
| `empty_pool` | 422 | Not enough legal items to build from |
| `budget_exceeded` | 429 | User or task budget spent |
| `guardrail_blocked` | 422 | Input failed a safety guardrail |
| `model_unavailable` | 503 | Tier exhausted, template path used |
| `render_failed` | 500 | Assembly succeeded, rendering did not |
| `context_unavailable` | 503 | Style context missing and unbuildable |
| `invalid_constraints` | 400 | Malformed constraints from the gateway |

`empty_pool` and `guardrail_blocked` are **expected outcomes**, not faults — they map to user-facing copy in [`../../40-frontend/error-model.md`](../../40-frontend/error-model.md) and should not page anyone.

---

## 5. Contract

Machine-readable specification: [`../../30-contracts/openapi/ase.internal.v1.yaml`](../../30-contracts/openapi/ase.internal.v1.yaml).

Because both sides of this contract are owned by the same team, it changes more freely than the public API — but it still changes through the contract file first, so the generated gateway client stays in step.
