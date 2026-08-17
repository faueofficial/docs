# Contract Changelog

Every change to `openapi/*.yaml` or `events/*.schema.json` is recorded here **before** the implementing service merges. This file is how the frontend engineer learns something changed without reading a diff.

Format: newest first. Each entry states the change, its type, and what a consumer must do.

**Change types:**

| Type | Meaning | Consumer action |
|---|---|---|
| `added` | New endpoint, field, or event | None — safe to ignore until needed |
| `changed` | Behaviour altered, still compatible | Read the note |
| `deprecated` | Still works, will be removed | Migrate before the stated date |
| `breaking` | Requires a new API version | Coordinate; never lands in `v1` |
| `fixed` | Contract corrected to match intent | Check whether you coded around the old behaviour |

---

## 2026-08-17 — Initial contract

`added` — **`gateway.v1.yaml`**, the first public API contract. 52 paths, 61 operations across auth, profile, quiz, uploads, vault, looks, fabric, spree, agent, integrations, notifications, and privacy.

`added` — **33 event schemas** in `events/`, covering identity, quiz, vault, looks, fabric, integrations, agent, notifications, catalog, and operations.

Notes for consumers:

- **Authentication is magic link**, not password or typed OTP. Token consumption is `POST /auth/link/consume`, never a `GET` — a `GET` that consumed the token would be spent by mail security scanners before the user tapped the link. The cross-device path returns `409` with a `device_code`; that is a normal flow, not an error.
- **Look generation is asynchronous.** `POST /looks/generate` returns `202` with a job envelope. Follow `stream_url` (SSE) or poll `poll_url`. Expect 20–45 seconds. Progress states are `queued`, `analyzing`, `assembling`, `rendering`, `done`, `failed`.
- **Consent gates several endpoints.** A `403` with `type: consent_required` means the user has not granted a purpose; the purpose name is in `errors[0].field`. Present the consent surface for that purpose rather than an error dialog. This is expected on a first run, not a failure.
- **Quiz definitions come from the API.** `GET /quiz` returns questions, options, and copy. Build option layouts from that response — question 6 has three options where the others have four, and copy will change after review without an app release.
- **Uploads are direct to CDN.** Get credentials from `POST /uploads/sign`, upload directly, then poll `GET /uploads/{asset_id}` until `status` is `ready`. An asset cannot be referenced by other endpoints until then, because it is still passing the PII redaction pipeline.
- **Instagram is not in the contract.** The Connected Accounts screen must drop the Instagram card — the platform API cannot return a user's saved posts, so the promised capability is undeliverable. Pinterest only.
- **Percentages on Style DNA results always total exactly 100.** No client-side rounding correction is needed.
- **Errors are RFC 7807.** Branch on `type`, never on `title` or `detail` — those are human-facing and will be reworded.

Endpoints marked `M1-2` in their descriptions (`/agent/settings`) are specified but not implemented; calling them before that stage returns `404`.

---

*Add new entries above this line.*
