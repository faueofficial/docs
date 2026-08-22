# Build Status

**Updated:** 2026-08-22 · **Branch:** `slice-0-1-infra-identity` · **Tests:** 168 passing (api-gateway)

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
| 2 | Profile, consent enforcement, `/me`, body profile | done except the edge rate limiter |
| 3 | Quiz scoring end to end, Style DNA persistence | scoring done, endpoints stub |
| 4 | Vault, uploads, image PII pipeline | stub |
| 5 | Look generation through `ase` | stub |

---

## api-gateway

| Area | Status | Notes |
|---|---|---|
| `identity` | done | Magic link, Google, Apple, rotation with family revocation, linking on verified email only |
| `profile` | done | `/me`, `PATCH /me`, body profile behind `personalization` |
| `profile.consent` | done | Denied by default, revocation cascades, `consent.changed` emitted |
| `events.publisher` | done | Outbox insert in the caller's transaction; never commits |
| `notify` templates | done | Jinja `SandboxedEnvironment`, per-message templates, unsubscribe rules enforced |
| `notify` channels | stub | email, push, inbox, sms, whatsapp all raise |
| `quiz` | partial | `scoring.py` is real and verified against all 3,072 combinations; the service and endpoints raise |
| `vault`, `uploads`, `looks`, `spree`, `agent`, `integrations`, `privacy`, `fabric` | stub | |
| `clients.ase_client`, `clients.media_client` | stub | |
| workers (`outbox_relay`, `notify_dispatch`, `pinterest_sync`, `dsr_purge`, `retention_ttl`, `lifecycle`, `link_cleanup`) | stub | The outbox is written but nothing relays it yet |
| Edge rate limiting | planned | The magic-link limiter is inline and real; the general middleware is not written |

## ase

| Area | Status |
|---|---|
| `engine/scoring.py` | done — ported from `atelier/drip-match` |
| Everything else | stub |

## Shared

| Package | Status |
|---|---|
| `faue-core` — events envelope, crypto (envelope encryption, blind index), consent purposes, error taxonomy, telemetry scrub, config | done |
| `faue-db` — 44 models, 2 migrations, 4 schema invariant guards | done |
| `faue-infra` — compose, provisioning, reusable CI workflow | done |

---

## Known gaps that are not stubs

These are implemented paths with a deliberate limit, recorded so they are not
mistaken for oversights.

- **`consent.changed` is written but never delivered.** `outbox_relay` is a stub,
  so the event sits unpublished. Correct for slice 2 — the outbox exists so the
  event survives until a relay runs — but no consumer reacts to a revocation yet.
- **Pinterest revocation deletes the local row, not the upstream grant.** Calling
  Pinterest's revocation endpoint belongs with the integration itself.
- **Email header artwork is specified, not produced.** See
  [`../50-data/email-assets.md`](../50-data/email-assets.md).
