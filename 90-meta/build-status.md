# Build Status

**Updated:** 2026-09-02 · **Branch:** `slice-0-1-infra-identity` · **Tests:** 514 passing (api-gateway), 89 (faue-core), 19 (faue-db), 19 (faue-infra)

What is actually implemented, as distinct from what is documented. [`doc-status.md`](doc-status.md)
tracks the documentation; this tracks the code, because a document marked `done`
says nothing about whether the endpoint it describes exists.

Status values: `done` (implemented and tested) · `partial` (some paths real, some
raise `NotImplementedError`) · `stub` (scaffolded, raises) · `planned`.

---

## Slices

| Slice | Scope | Status |
|---|---|---|
| 0 | Repos, shared packages, database, migrations, CI, local environment | done |
| 1 | Identity — magic link, Google, Apple, sessions, refresh rotation, linking | done |
| 2 | Profile, consent enforcement, `/me`, body profile, edge rate limiting | done |
| 3 | Quiz scoring end to end, Style DNA persistence | done except card rendering, which belongs to `media` |
| 3.5 | Event backbone (relay, transports, consumers) and notify channels | relay and inbox/email done; quiet hours and frequency cap outstanding |
| 4 | Vault, uploads, image PII pipeline | pipeline, storage, vault and uploads done; the detection models are declared but not installed |
| 5 | Look generation through `ase` | stub |

---

## api-gateway

| Area | Status | Notes |
|---|---|---|
| `identity` | done | Magic link, Google, Apple, refresh rotation with family revocation, linking on verified email only. Access tokens are EdDSA with an overlapping-rotation verify key |
| `profile` | done | `/me`, `PATCH /me`, body profile behind `personalization` |
| `profile.consent` | done | Denied by default, revocation cascades, `consent.changed` emitted |
| `events.publisher` | done | Outbox insert in the caller's transaction; never commits |
| `notify` templates | done | Jinja `SandboxedEnvironment`, per-message templates, unsubscribe rules enforced |
| `notify` channels | partial | `inbox` and `email` are real and render from the catalog; `push` waits on a device token (app work), `sms`/`whatsapp` are M1-2 |
| `notify` dispatch | partial | Consent checked at consume time, deduped on `(user, template, event)`. Quiet hours and the frequency cap are not implemented yet |
| `events.relay` | done | Claims with `FOR UPDATE SKIP LOCKED`, stamps `published_at`, parks a row after 5 failed attempts rather than blocking the queue |
| `events` transports | done | In-process for local, RabbitMQ (topic, durable, publisher-confirmed) elsewhere |
| Structured logging | done | JSON, scrubbed by the formatter, `trace_id` bound per request and returned in `X-Trace-Id`. One line per request with route templated, never the payload |
| Outcome vocabulary | done | success / partial / failure with validated reason codes; log level derived from status |
| `admin` auth realm | done | Separate `aud`, 8-hour absolute session, MFA enforced at issue, account re-read on every request so revocation and demotion take effect mid-session |
| `admin` login flow | done | Magic link + TOTP. Enrolment-token bootstrap, replay protection on codes, tight per-IP rate limits, sign-in and enrolment audited |
| `admin` logout and revocation | done | Per-session logout by `jti`; account-wide revocation as a rounded-up timestamp cutoff. Verification fails closed when Redis is unreachable |
| `admin` session listing | done | Sorted-set index per account, coarse device label, `current` marker, ending one session from another device. Ownership is structural — the key is namespaced by account |
| `admin` invitations | done | `role.write` only, three-day single-use invite, own email template. An invited account cannot sign in until enrolment activates it |
| `admin` RBAC | done | Capability-based, fails closed on an unknown role or capability |
| `admin` audit log | done | Closed set of actions, justification required for PII-touching ones, `before`/`after` scrubbed |
| `admin` ops endpoints | done | `/ops/health`, `/ops/events`, `/ops/notifications` — per-dependency health, backlog split into unpublished vs parked, delivery outcomes by status and failure reason |
| `quiz` | done | Scoring verified against all 3,072 combinations; submit/result/retake persist and announce `quiz.completed`. `/quiz/card` reports `pending` — rendering lives in `media`, which is M1-2 |
| `vault` | done | CRUD, category filter, search over name and notes, soft delete, wear log. An item may only reference a `ready` asset |
| `media` backup replication | done — **verified against Railway's live bucket** | S3-compatible: Cloudflare R2, Railway's bucket service, or MinIO. Reconciled by a worker, never inline — a backup outage must not fail an upload |
| `media` (uploads + PII pipeline) | partial | Pipeline, storage and the asset lifecycle are done and tested against real image bytes. Cloudinary implemented over its REST API, with signing pinned against the official SDK. The **detectors are `NullDetector`** — see the gap below |
| `looks`, `spree`, `agent`, `integrations`, `privacy`, `fabric` | stub | |
| `clients.ase_client`, `clients.media_client` | stub | |
| worker `outbox_relay` | done | Runs the shared relay loop; logs parked rows as an error |
| worker entrypoint | done | `python -m app.workers` runs every implemented worker in one process. Exits if any loop dies — a worker service that looks healthy while events pile up is worse than a restart |
| workers (`notify_dispatch`, `pinterest_sync`, `dsr_purge`, `retention_ttl`, `lifecycle`, `link_cleanup`) | stub | |
| Edge rate limiting | done | Fixed-window on Redis, atomic via Lua; per user where there is one, per IP otherwise |

## ase

| Area | Status |
|---|---|
| `engine/scoring.py` | done — ported from `atelier/drip-match` |
| Everything else | stub |

## Shared

| Package | Status |
|---|---|
| `faue-core` — events envelope, crypto (envelope encryption, blind index, Ed25519 signing keys), consent purposes, error taxonomy, telemetry scrub, config | done |
| `faue-db` — 44 models, 2 migrations, 4 schema invariant guards | done |
| `faue-infra` — compose, provisioning, secret generation, reusable CI workflow | done |

---

## Known gaps that are not stubs

These are implemented paths with a deliberate limit, recorded so they are not
mistaken for oversights.

- **`consent.changed` is written but never delivered.** `outbox_relay` is a stub,
  so the event sits unpublished. Correct for slice 2 — the outbox exists so the
  event survives until a relay runs — but no consumer reacts to a revocation yet.
- **Pinterest revocation deletes the local row, not the upstream grant.** Calling
  Pinterest's revocation endpoint belongs with the integration itself.
- **`/quiz/card` always reports `pending`.** Card rendering runs in `media`,
  which is M1-2. The client already polls for this state and the result screen
  does not depend on the card, so this degrades to "no card" rather than to an
  error.
- **22 of 30 Style DNA blend lines are unwritten** and fall back to a generic
  line. Open item 11 in [`doc-status.md`](doc-status.md).
- **Quiet hours and the frequency cap are not enforced.** Consent and
  deduplication are; the other two suppression rules belong to the dispatcher
  and are not written. Nothing at MVP sends often enough to hit a cap yet, but
  that stops being true the moment the agent's daily suggestion ships.
- **The network gate is not code.** `admin.md` requires a VPN, SSO or IP
  allowlist in front of the whole console. That is deployment configuration on
  Railway and Vercel, not something this repository can assert — so the
  application-level controls above are the only ones currently proven.
- **No image is actually being examined yet.** The pipeline runs end to end —
  EXIF is stripped, variants are derived, redaction is applied and verified by
  reading pixels back — but `NullDetector` finds no faces, no text and refuses
  nothing. `pipeline.process` raises outside `local` rather than recording
  redaction that never happened, so this cannot reach staging by accident. The
  three models (MediaPipe, Tesseract, open-clip) are declared in
  `faue-core/requirements/media.in` and are not installed. **Uploads cannot go
  live until they are, and until they have been run against real Nigerian
  fashion photographs** — a face detector tuned on one population and deployed
  to another is a well-documented way to fail exactly the users you meant to
  protect.
- **Cloudinary is implemented but never exercised against the real service.**
  Signing is verified against the official SDK and the request shape is tested
  with a fake transport, but no upload has reached Cloudinary — there are no
  credentials in any environment yet. First real upload is the test that matters.
- **The backup is verified against Railway's real bucket** (`t3.storageapi.dev`)
  — an upload was processed, all three variants replicated byte-identically, and
  the copies confirmed to carry no EXIF. Cloudinary itself has still never been
  written to; the primary in that run was local storage.
- **`original_retained` is always false.** Keeping originals needs a consent
  purpose that does not exist. The column is there to make that visible.
- **`faue-core` and `faue-db` have no release tags.** `pyproject.toml` pins
  `@v0.1.0` in both services and in `faue-db` itself; nothing is tagged, so any
  container build fails at dependency resolution. Reproduced in a clean
  virtualenv. Tag `faue-core` first — `faue-db` pins it in turn.
- **`lifespan` reads `get_settings()` rather than the settings handed to
  `create_app`.** Harmless today because production passes nothing, but a test
  or script that constructs an app with explicit settings gets different
  configuration inside the lifespan than outside it.
- **Redis is now a hard dependency for admin auth.** The revocation deny-list is
  checked on every admin request and fails closed, so a Redis outage locks the
  console rather than honouring sessions someone has already ended. Deliberate,
  and the trade worth revisiting only if it actually bites.
- **`scripts/create_admin.py` still exists alongside invitations.** It is the
  bootstrap for the very first account, since inviting requires an admin to
  already exist. Nothing removes it, and nothing should until there is another
  way to create account zero.
- **Session metadata now lives in Redis.** Listing required storing what was
  previously stateless: an IP and a coarse device label per session, expiring
  with the session. The raw user-agent is deliberately not kept. Worth naming in
  the RoPA as a new place personal data sits, however briefly.
- **Sessions are listed per account, never across accounts.** An `admin` cannot
  see or end another operator's sessions; suspending the account is the lever
  for a departure. Cross-account session management would need its own
  capability and its own audit story.
- **The ops endpoints are read-only.** Kill switches, flags and the deletion
  ledger are next in the documented build order and are not built.
- **Internal service auth is configured but not enforced.** `SERVICE_JWT_SECRET`
  and `ASE_SERVICE_TOKEN` are generated and present on both services, but
  nothing mints or checks them yet — that is slice 5, alongside the first real
  `AseClient` call. Safe in the meantime only because `ase` has no public
  ingress, which makes it a launch blocker rather than a live exposure.
- **Email header artwork is specified, not produced.** See
  [`../50-data/email-assets.md`](../50-data/email-assets.md).
