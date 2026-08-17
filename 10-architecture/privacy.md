# Privacy

**Stage:** MVP · **Applies to:** GDPR (EU users) and the Nigeria Data Protection Act 2023 · **ADR:** [0012](../80-adr/0012-consent-denied-by-default.md)

Compliance here is an architectural property, not a policy document. The controls below are enforced in code and in the database, because a rule that depends on everyone remembering it will eventually be forgotten by someone in a hurry.

---

## 1. Consent

### Purposes

Named, independently revocable, and **denied by default** without exception.

| Purpose | Covers | Without it |
|---|---|---|
| `essential` | Account, authentication, security, transactional messages | No account is possible |
| `personalization` | Style DNA, body profile, style context, agent suggestions | Generic results only |
| `ai_processing` | Sending sanitised inputs to model providers | No generation, no fabric analysis, no spree |
| `pinterest_sync` | OAuth, board import, aspiration vectors | No Pinterest features |
| `camera_photos` | Uploading and processing images | No vault, no fabric flow |
| `location_weather` | City-level location for weather context | Suggestions ignore weather |
| `agent_proactive` | Scheduled and triggered suggestions | On-open suggestions only |
| `marketing_comms` | Lifecycle campaigns and promotional messages | Transactional messages only |
| `analytics` | Pseudonymous product analytics | Excluded from analytics |

`essential` is the only purpose granted at registration, and it covers only what the service cannot function without.

### Enforcement

A shared FastAPI dependency, not per-endpoint discipline:

```python
@router.post("/looks/generate")
async def generate(
    body: GenerateRequest,
    user: User = Depends(current_user),
    _: None = Depends(require_consent("ai_processing")),
) -> JobEnvelope: ...
```

A route that needs a purpose declares it in its signature. It cannot be forgotten, and the consent matrix in [`../20-services/api-gateway/api.md`](../20-services/api-gateway/api.md) is generated from these declarations rather than maintained by hand.

### Behaviour without consent

Missing consent returns `403 consent_required` with the purpose named. **The client presents the consent surface, not an error.** On a first generation this is the expected path, not a failure.

Features degrade rather than break. No `location_weather` means weather is not used and the response says so; the request still succeeds.

### Revocation

Immediate and total. Revoking `personalization` drops the cached style context; revoking `pinterest_sync` also revokes the upstream token and deletes cached pins; revoking `ai_processing` disables generation and purges retained prompts.

**Revocation is never gated, never delayed, and never behind a retention prompt.** A `consent.changed` event propagates to every service at consume time.

### Recording

```sql
gateway.consents (user_id, purpose, granted, policy_version,
                  granted_at, revoked_at, source)
```

`policy_version` matters: consent is to a specific version of the privacy policy. A material policy change requires re-consent rather than a silent update.

---

## 2. Lawful basis

| Data | Basis |
|---|---|
| Account and authentication | Contract |
| Style DNA, vault, look history | Consent (`personalization`) |
| Body profile | **Explicit consent** — sensitive category |
| Images | Consent (`camera_photos`) |
| Location | Consent (`location_weather`) |
| Model processing | Consent (`ai_processing`) |
| Security logs, audit log | Legitimate interest |
| Transactional messages | Contract |
| Marketing messages | Consent (`marketing_comms`) |

Full field-level register in [`ropa.md`](ropa.md).

---

## 3. Data subject rights

| Right | Endpoint | SLA |
|---|---|---|
| Access and portability | `POST /privacy/export` | 30 days, usually minutes |
| Erasure | `POST /privacy/delete` | 30 days |
| Rectification | `PATCH /me`, `PUT /me/body-profile` | Immediate |
| Restriction | `POST /privacy/restrict` | Immediate |
| Objection | Revoke the relevant purpose | Immediate |

### Deletion

An orchestration, not a `DELETE`:

```
POST /privacy/delete
  → create deletion_ledger { sla_due_at: +30 days, modules_pending: [...] }
  → emit user.deletion.requested
  → each module purges its own tables, then emits user.deletion.completed{module}
  → third parties purged in parallel:
        CDN assets · analytics profile · push tokens · Pinterest token revocation
  → ledger closes when every module and third party has acknowledged
```

What survives deletion, and why:

| Survives | Reason |
|---|---|
| `audit_log` entries | Legal obligation to demonstrate access accountability |
| `deletion_ledger` row | Proof the deletion happened |
| Aggregate, non-identifying analytics | Contains no personal data |

Everything else goes, including embeddings — which are derived from images and are personal data by any reasonable reading.

Offering Sign in with Apple makes in-app deletion an App Store requirement. This flow is launch-blocking.

### Export

The same fan-out, producing a machine-readable archive: profile, quiz responses, vault items with images, looks, wear log, saved items, consents, and integration metadata. Delivered as a link that expires in seven days.

---

## 4. Minimisation

- **Events carry identifiers**, never PII. No event payload contains an email, a name, a measurement, or free text a user typed.
- **Logs carry `user_id` and `trace_id`** and nothing else identifying. CI fails on PII-shaped patterns in log statements.
- **Analytics receives a pseudonymous identifier**, never a direct identifier.
- **`ase` holds no direct identifiers.** Body data is converted to abstract silhouette constraints before it crosses the service boundary, so a compromise of `ase` cannot expose a measurement.
- **Location is city-level.** Coordinates are truncated to a five-character geohash on receipt and the raw values are discarded. No coordinate history, no movement trail. Precise location is never requested, because outfit advice does not need it.

---

## 5. Retention

Every table has a retention period, declared in [`ropa.md`](ropa.md) and enforced by the `retention_ttl` worker — not by intention.

| Category | Period |
|---|---|
| Account data | Life of account |
| Images | Life of the object; originals discarded after derivative creation |
| Spree conversations | 90 days |
| Model call logs | 90 days |
| Action events | 24 months |
| Notification deliveries | 12 months |
| Audit log | 7 years |
| Deletion ledger | 7 years |

---

## 6. Third parties

Every processor is listed publicly as a sub-processor. Each requires a data processing agreement before it touches user data.

| Processor | Receives | Basis |
|---|---|---|
| Model provider (via OpenRouter) | Sanitised text, redacted images | `ai_processing` |
| Image generation provider | Constructed prompts — never user images | `ai_processing` |
| Cloudinary / object storage | Redacted image derivatives | `camera_photos` |
| Transactional email | Email address | Contract |
| FCM / APNs | Device tokens | Contract |
| PostHog | Pseudonymous analytics events | `analytics` |
| Open-Meteo | Coarse geohash — no user identifier | `location_weather` |
| Pinterest | OAuth token exchange | `pinterest_sync` |
| Railway / Vercel | Hosting | Contract |

Model providers are restricted to a **zero-data-retention, no-training allowlist**, enforced per request rather than assumed from a contract.

---

## 7. Security measures

Detail in [`security.md`](security.md) and [`pii-handling.md`](pii-handling.md). Summary:

- TLS everywhere, including service to service.
- Envelope encryption at rest for email, phone, body profile, measurements, and OAuth tokens.
- Blind indexes for equality lookups on encrypted values, so login stays an index scan without storing plaintext.
- Server-authoritative image redaction: safety classification, EXIF strip, face redaction, OCR redaction.
- Role-based database access with per-schema grants.
- Admin access with MFA, RBAC, masking by default, and an immutable audit log.

---

## 8. Age

Minimum 16, verified at registration. No personalisation consent can be granted before verification. There is no under-16 mode — the data model and consent framework assume adults.

---

## 9. Residency and transfers

Single primary region, with the transfer basis documented. All PII is confined to the `gateway` and `media` schemas, so a second region for EU users is feasible without touching the styling stack — that containment is deliberate.

---

## 10. Breach response

72-hour notification clock under both GDPR and NDPA. Procedure, severity ladder, and contacts in [`../70-ops/incident-response.md`](../70-ops/incident-response.md).

The clock starts at **awareness**, not at confirmation. A suspected breach is escalated immediately rather than investigated quietly first.

---

## 11. Privacy by design

Design-stage decisions that made compliance structural rather than added:

| Decision | Effect |
|---|---|
| Consent denied by default | No purpose can silently apply to existing users |
| Enforcement in a shared dependency | A new endpoint cannot forget the check |
| PII confined to two schemas | Limits blast radius and enables regional splits |
| Body data abstracted at the boundary | `ase` has no measurement to leak |
| Coarse location only | No movement history exists to be requested or stolen |
| Server-side image redaction | A leaked derivative contains no face and no coordinates |
| Event payloads carry ids only | The broker never becomes a PII store |
| Per-asset pipeline flags | Compliance is queryable, and a pipeline bug is visible |

---

## 12. Outstanding

| Item | Blocks |
|---|---|
| Privacy policy and terms drafted and published | Launch |
| Consent surfaces designed for `ai_processing`, `location_weather`, `pinterest_sync` | Launch |
| Privacy and data settings screen | Launch — App Store requires in-app deletion |
| Data processing agreements signed with every processor | Launch |
| Sub-processor list published | Launch |
