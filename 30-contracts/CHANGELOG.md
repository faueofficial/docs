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

## 2026-10-13 — Multiple quiz answers, sharing, unsubscribe, and the console API

| Change | Type | Consumer action |
|---|---|---|
| `GET /quiz` questions gain `max_choices` | `added` | Render checkboxes up to that many when it is greater than 1. A response without it means 1. |
| `answers` on `POST /quiz/submit`, `POST /quiz/preview` and `POST /early-access` may map a question to a **list** of option ids | `changed` | A plain string still works and means one choice. Send a list only when `max_choices` allows. More than `max_choices`, an empty list or an unknown option is `422`. |
| `POST /early-access` gains optional `gender` (`female`, `male`, `prefer_not_to_say`) and returns `card_photo` | `added` | Add the dropdown. Omitting it keeps the plain card. |
| `CardUrls` gains `share_url`; `POST /early-access` now fills `card_urls` with signed `stories_url`, `square_url` and `share_url` | `added` | Offer Story and Post and a Copy link action. Use the addresses exactly as given. |
| `GET /cards/dna.png` (signed card image, 9:16, 4:5 or 1200x630) | `added` | Take addresses from `card_urls`; do not build them. |
| `GET /dna/{token}` (data for a shared card) | `added` | Use it to open a received share link natively. |
| `GET` and `POST /unsubscribe/{token}` | `added` | Back the unsubscribe screen: `GET` to show, `POST` to act. |
| `PUT /uploads/{asset_id}` documented | `fixed` | It was served but missing from the contract. `multipart/form-data`, field `file`. |
| `POST /auth/logout` documents its `refresh_token` body | `fixed` | None, the body was already required. |
| `POST /vault/items/{item_id}/style` marked `deprecated` | `fixed` | It is not served. Use `POST /looks/generate` or `POST /fabric/{asset_id}/style`. |

Admin contract (`gateway.admin.v1.yaml`):

| Change | Type | Consumer action |
|---|---|---|
| `GET /me`, `/overview`, `/audit`, `/admins` | `added` | Console only. `/me` returns the role's capabilities; build the menu from it. |
| Contact: `GET /contact/messages`, `GET`/`PATCH /contact/messages/{id}`, `POST .../reply` | `added` | These existed in the gateway and are now in the contract. |
| Waitlist: list, summary, get, `PATCH` status, `POST .../message`, `DELETE` | `added` | Same. `PATCH` to `invited` now **sends the launch email**; `DELETE` emails a confirmation and deletes the entry. |

New: [`app-developer-guide.md`](app-developer-guide.md), and the generated [`api-reference.md`](api-reference.md) and [`admin-api-reference.md`](admin-api-reference.md) (`tools/build_reference.py`).

---

## 2026-09-02 — Uploads are not direct-to-CDN

| Change | Type | Consumer action |
|---|---|---|
| `POST /uploads/sign` returns an upload URL on **our** domain, not CDN credentials | `changed` | `PUT` the image to `upload_url` as multipart form data. Do not upload to Cloudinary directly. |
| `PUT /uploads/{asset_id}` added | `added` | Where the bytes go. Returns `{status}` — poll `GET /uploads/{asset_id}` until `ready`. |
| `GET /vault/items` gains `q` and `category` filters; `POST /vault/wear` added | `added` | |

The description previously said "direct client-to-CDN upload; the server never
proxies image bytes". That could not be true alongside the privacy guarantee
that Cloudinary receives redacted derivatives and never originals — a direct
upload puts the unredacted original on the CDN, including images that are then
rejected as unsafe.

The bytes now reach the gateway, the PII pipeline runs in memory, and only the
derivative is stored. Same endpoint names, different upload target.

---

## 2026-08-22 — Auth response bodies

| Change | Type | Consumer action |
|---|---|---|
| `POST /auth/link/request` 202 gains `delivery`, `masked_destination`, `resend_available_in` | `added` | **Drive the resend cooldown from `resend_available_in`** rather than a hardcoded 60 seconds — the two disagree the moment the server rule changes. Show `masked_destination` on the check-email screen so a user can see whether they mistyped. |
| `Session` gains `token_type`, `refresh_expires_in`, `onboarding` | `added` | Route straight from the auth screen using `onboarding` instead of calling `/me` first. That saves a round trip on the slowest screen in the product. |
| `POST /auth/refresh` now returns `RefreshedSession`, not `Session` | `changed` | Same fields **minus** `onboarding`. Refresh runs every twelve minutes in the background and no screen reads onboarding at that moment; do not depend on it being there. |

Neither response previously declared `token_type`. It has always been `Bearer`
and still is — it is stated now rather than assumed.

The `202` body remains byte-identical for a registered address and an unknown
one. Every field in it is derived from the request, which is what keeps it from
becoming an account-enumeration oracle. No field that depends on account
existence may be added to it.

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
