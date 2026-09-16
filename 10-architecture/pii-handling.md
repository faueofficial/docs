# PII Handling

**Stage:** MVP · **ADR:** [0013](../80-adr/0013-server-authoritative-image-pii-pipeline.md)

The full lifecycle of personal data: what is collected, how it is protected, what leaves the system, and how it is destroyed.

---

## 1. Classification

| Class | Examples | Treatment |
|---|---|---|
| **Direct identifiers** | Email, phone, username, device token | Encrypted at rest, blind-indexed for lookup, never in logs or events |
| **Sensitive** | Body shape, height, measurements | Explicit consent, encrypted, never leaves `gateway` in raw form |
| **Images** | Fabric, vault items, fit photos, cached pins | Redaction pipeline before any use |
| **Behavioural** | Wear log, saves, feedback, quiz answers | Pseudonymous, tied to `user_id` |
| **Derived** | Embeddings, style vectors, agent memory | Personal data — derived from personal data, deleted with it |
| **Coarse location** | `geohash5` (~5 km) | Consent-gated, never precise, no history |
| **Operational** | Trace ids, IP in the audit log | Legitimate interest, short retention |

**Embeddings are personal data.** A vector derived from a photograph of someone's clothing is information about that person, and it is deleted on erasure like anything else. Treating vectors as anonymous because they look like numbers is a common and wrong assumption.

---

## 2. Image pipeline

Every user-supplied image — fabric, vault item, fit photo, cached Pinterest pin — passes the same server-side pipeline before it is stored, shared, or sent to any model. **There is no path that skips it.**

> **The client does not upload to the CDN.** The diagram below once said
> "direct to CDN", which cannot be true alongside the data boundary two sections
> down: a direct upload puts the *unredacted original* on Cloudinary, including
> images we then reject, and the table promises Cloudinary receives derivatives
> and nothing else.
>
> Bytes therefore arrive at the gateway, are redacted in memory, and only the
> derivative is stored. That costs us the transfer — modest at MVP scale — and it
> is what makes the guarantee real rather than aspirational.

```
upload (to the gateway with a short-lived signed credential)
  │
  ├─ 1  SAFETY CLASSIFICATION
  │     reject NSFW, minors, non-apparel
  │     rejected images are NOT persisted
  │
  ├─ 2  EXIF STRIP
  │     GPS coordinates, device identifiers, timestamps, orientation preserved
  │
  ├─ 3  FACE DETECTION → IRREVERSIBLE REDACTION
  │     in-process open model (RetinaFace / MediaPipe class)
  │     blur or mask on the derivative
  │
  ├─ 4  OCR SCAN → TEXT REDACTION
  │     names, phone numbers, addresses, card digits masked
  │
  ├─ 5  DERIVATIVE CREATED
  │     this is what is stored, shared, and sent to models
  │
  └─ 6  ORIGINAL DISCARDED
        retention requires explicit consent, encryption, and a TTL
```

### Why each step

**Safety classification** first, so nothing unacceptable is ever written to disk.

**EXIF stripping** because GPS in photo metadata is the most common silent location leak in any photo-upload product, and it is entirely invisible to users. Someone photographing a shirt on their bed has just disclosed their home address.

**Face redaction in-process** rather than via a vendor: sending an unredacted face to a third party in order to detect the face defeats the purpose. The same objection applies one step earlier to safety classification, which runs *first* and would therefore hand a vendor the unredacted image — so that is in-process too.

The three models sit behind one `Detector` protocol, so which model is
configuration rather than an assumption baked into the pipeline:

| Stage | Implementation | Resident |
|---|---|---|
| Safety | `open_clip` zero-shot | ~350 MB |
| Faces | MediaPipe BlazeFace | ~30 MB |
| OCR | Tesseract | ~50 MB |

They live in `faue-core/requirements/media.in`, a **worker-only** role. The
gateway's web image never decodes an image — it signs uploads and reads asset
rows — which is what keeps half a gigabyte of models out of every API instance.

**Redaction is a fill, not a blur.** A blur is reversible enough to matter, and
"unrecognisable to me, squinting" is not the standard. Boxes are also grown
before filling: a tight box around a face leaves the hairline and jaw, which is
still recognisable.

**OCR redaction** because text inside an image reaches a model exactly as text does. A photo of a garment with a delivery label in frame carries an address into a prompt.

**Original discarded** because keeping it means keeping the unredacted face and the coordinates, and nothing in the product needs them.

### Variants are generated in the same pass

The pipeline already decodes and re-encodes every image, so it emits sized variants while it has the bitmap open: a 200 px thumbnail, a 400 px preview, and the full derivative. No separate transformation step, and no transformation service required.

This matters for cost, not tidiness. A vault grid is many small image requests on metered Nigerian mobile data — downloading full resolution for a thumbnail grid spends the user's money.

### Where derivatives are stored

| Tier | Role |
|---|---|
| **Cloudinary** | Primary — storage and CDN for **derivatives only**. Never an original, never a rejected image |
| **Cloudflare R2** | Backup replica. A different provider from primary, the same rule already applied to database backups |
| Railway object storage | Local and staging only; nobody's phone downloads from it |

All three sit behind one `StorageProvider` interface, so the primary is a configuration choice rather than an assumption baked into upload code. `local` is refused outside `ENVIRONMENT=local`: the Railway filesystem is ephemeral, so images would vanish on the next deploy and the user would find out days later as "my wardrobe is empty". Bandwidth — not storage — is the binding constraint, and approaching Cloudinary's free-tier bandwidth is the trigger to move primary to R2.

### Client-side blur is not a control

The Flutter app may blur locally for a better preview. The server repeats every step and treats client output as untrusted. A modified client simply skips a client-side step, and the unredacted image crosses the network regardless.

### Auditability

> **Implemented as `gateway.assets`.** `media` is an M1-2 extraction, so its
> responsibilities live as a bounded module inside the gateway until then — the
> same arrangement as `notify`. The columns and the guarantee are unchanged; only
> the schema name differs, and it moves with the service.

```sql
gateway.assets (   -- media.assets after extraction
  exif_stripped BOOLEAN, faces_redacted BOOLEAN, ocr_redacted BOOLEAN,
  safety_verdict TEXT, original_retained BOOLEAN, retention_until TIMESTAMPTZ
)
```

Per-asset flags make compliance queryable and turn a pipeline bug into something visible rather than silent:

```sql
SELECT count(*) FROM gateway.assets
WHERE status = 'ready' AND (NOT exif_stripped OR NOT faces_redacted);  -- must be zero
```

That query runs as a scheduled check and alerts on any non-zero result.

---

## 3. Encryption at rest

Envelope encryption: each sensitive column is encrypted with a data key, which is itself encrypted by a rotatable master key.

| Table | Encrypted columns |
|---|---|
| `auth_identities` | `email_enc`, `phone_enc` |
| `body_profile` | `height_cm_enc`, `measurements_enc` |
| `integration_accounts` | `access_token_enc`, `refresh_token_enc` |
| `notify_devices` | `token_enc` |
| `admin_users` | `email_enc` |

### Blind indexes

Encrypted values cannot be searched, but login needs to find a user by email. A blind index — HMAC-SHA256 of the normalised value with a server-side pepper — is stored alongside:

```
email_bidx = HMAC(pepper, lower(trim(email)))
```

Equality lookups stay index scans; the plaintext is never stored. The pepper lives in the secret store, separate from the database, so a database dump alone yields neither the value nor the ability to test guesses at scale.

**Do not rotate the pepper casually.** Rotation invalidates every blind index and requires recomputation, during which email lookups fail. It needs a maintenance window.

### Key rotation

Master key rotation re-encrypts data keys, not rows — minutes rather than hours. Procedure in [`../20-services/api-gateway/runbook.md`](../20-services/api-gateway/runbook.md).

---

## 4. Redaction before model egress

Nothing containing PII reaches a model provider.

| Input | Treatment |
|---|---|
| User text (notes, spree messages) | Pattern-based redaction of emails, phones, addresses, card numbers before the call |
| Images | Already redacted by the pipeline; the derivative is what is sent |
| Body data | Converted to abstract constraints (`favor: defined_waist`) in `gateway`; `ase` never holds a measurement |
| Location | Never sent. Weather is resolved server-side and only the resulting conditions reach a prompt |
| Names | Not included in any prompt; the persona is what personalises output |

The redaction map is held server-side and never transmitted, so a redacted value cannot be reversed by the provider.

Stored spree messages are **redacted before persistence**, not before display — a database dump contains no PII even if the application layer is bypassed.

---

## 5. Logging

**Never logged:** email, phone, name, username, measurements, image content or URLs with credentials, tokens, prompt content containing user text, or location beyond a country.

**Always logged:** `trace_id`, `user_id`, service, environment, route, status, duration.

A CI check fails the build on PII-shaped patterns in log statements — string interpolation of a variable named `email`, `phone`, `name`, `token`, or `measurement` into a log call. It is a blunt instrument and it catches the mistake that actually happens.

Structured logs go to Loki with a 30-day retention. Traces carry no PII in attributes.

---

## 6. Third-party egress

| Recipient | Receives | Does not receive |
|---|---|---|
| Model providers | Redacted text, redacted images, abstract constraints | Names, emails, measurements, location, raw photos |
| Image generation | Constructed prompts from `LookSpec` | User images, user text, identifiers |
| Cloudinary | Redacted derivatives | Originals, unless explicitly retained |
| Email provider | Email address, template variables | Anything else |
| FCM / APNs | Device token, notification body | Identifiers beyond the token |
| PostHog | Pseudonymous id, event names, non-PII properties | Direct identifiers |
| Open-Meteo | Coarse geohash | Any user identifier |

Each is a documented sub-processor with a data processing agreement.

---

## 7. Deletion

Deletion must reach derived data and third parties, not only the obvious tables.

| Location | Deleted |
|---|---|
| `gateway` | Users, identities, tokens, profile, body profile, vault, wear log, saves, feedback, actions, consents, integrations, notifications |
| `ase` | Style context, all embeddings, looks, jobs, fabric analyses, spree sessions and messages, agent memory and runs, model call rows |
| `media` | All assets and derivatives |
| CDN | All objects under the user's prefix |
| PostHog | Profile deletion via API |
| Push providers | Token removal |
| Pinterest | Token revocation |

**Not deleted:** audit log entries and the deletion ledger, both retained seven years as legal records; and aggregate analytics containing no personal data.

Progress is tracked in the ledger with a 30-day SLA, alerting five days out.

---

## 8. Access control

| Who | Access | Controls |
|---|---|---|
| Service roles | Own schema only | Postgres grants; cross-schema access fails at the database |
| `faue_migrator` | DDL | Separate role; service roles cannot alter tables |
| Admin `support` | Masked PII, reveal with reason | MFA, RBAC, audit log |
| Admin `curator` | Content only, no user PII | MFA, RBAC |
| Admin `admin` | Full, time-boxed break-glass | MFA, audit, second-person alert |
| Engineers | Production via break-glass only | No standing access |

PII renders masked by default in admin. Revealing requires a stated reason and writes an audit entry — that record is what demonstrates access accountability to a regulator.

---

## 9. Testing

| Test | Gate |
|---|---|
| `pii_images` golden set | Face detection recall ≥ 0.98, EXIF strip 100%, OCR redaction ≥ 0.95 |
| Log scrubbing | CI fails on PII-shaped log statements |
| Redaction before egress | Unit tests over the redaction function with known patterns |
| Deletion completeness | Integration test asserting zero rows across every schema after erasure |
| Encryption round-trip | Every encrypted column encrypts, decrypts, and rotates |
| Blind index | Lookup by encrypted email succeeds; plaintext is absent from storage |

The deletion completeness test is the one that matters most and is easiest to let rot — it must enumerate tables dynamically, so a new table without a deletion path fails the test rather than silently persisting.

---

## 10. Breach handling

If personal data is exposed:

1. Contain — revoke keys, rotate secrets, disable the affected path.
2. Assess — what data, how many people, what risk, using the audit log and the RoPA.
3. Notify — regulator within 72 hours of awareness; affected users where risk is high.
4. Record — cause, scope, remediation, prevention.

The clock starts at awareness, not at confirmation. Full procedure in [`../70-ops/incident-response.md`](../70-ops/incident-response.md).
