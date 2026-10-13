# FAUE API: developer guide

For the people building the FAUE mobile app, the website and the admin console. This is the document to read first. It says how the API behaves; the two reference files list every endpoint with its request and response schemas.

| Read | For |
|---|---|
| **This guide** | Conventions, sign-in, errors, limits, and the flows that span several endpoints |
| [`api-reference.md`](api-reference.md) | Every public endpoint, with request and response field tables and example payloads |
| [`admin-api-reference.md`](admin-api-reference.md) | The admin console's endpoints |
| [`openapi/gateway.v1.yaml`](openapi/gateway.v1.yaml), [`openapi/gateway.admin.v1.yaml`](openapi/gateway.admin.v1.yaml) | The contracts. Generate clients from these. |
| [`CHANGELOG.md`](CHANGELOG.md) | What changed, and what you must do about it |
| [`../40-frontend/`](../40-frontend/README.md) | Deeper client notes: [auth flows](../40-frontend/auth-flows.md), [error model](../40-frontend/error-model.md), [pagination](../40-frontend/pagination.md), [realtime](../40-frontend/realtime.md), [deep links](../40-frontend/deeplinks.md), [offline and caching](../40-frontend/offline-and-caching.md) |

The two reference files are generated from the YAML by `tools/build_reference.py`. Change the YAML and rerun it; never edit the references by hand.

---

## 1. The basics

| | |
|---|---|
| Base URL | `https://api.faueofficial.com/v1` (production). Staging and local are in the contract's `servers`. |
| Admin base URL | `https://api.faueofficial.com/admin/v1`, a separate realm, see section 12 |
| Format | JSON in, JSON out, UTF-8. Errors are `application/problem+json`. |
| Timestamps | RFC 3339 in UTC: `2026-10-13T09:30:00Z` |
| Identifiers | UUIDs as strings. Treat them as opaque. |
| `204 No Content` | Success with no body. Do not parse one. |
| Live docs | `GET /docs` (Scalar), `GET /openapi.json` |

### Headers

| Header | Direction | Use |
|---|---|---|
| `Authorization: Bearer <access_token>` | request | Every endpoint marked "Auth: bearer token" in the reference |
| `X-Trace-Id` | request | Send one to correlate your logs with ours. Echoed back in `instance` on every error. |
| `Idempotency-Key` | request | On POSTs that create something. A retry with the same key returns the original result. |
| `X-Client-Version` | request | Lets the server keep older app builds working |
| `Retry-After` | response | Seconds to wait, on every `429` |

### Stage tags

Each operation's description starts with a stage tag: `MVP`, `M1-2`, `M3+`, `Y2`. Anything beyond `MVP` is specified but **not implemented**; do not build against it yet.

---

## 2. Signing in

Access tokens are short (15 minutes). Refresh tokens are long (30 days) and **rotate on every use**.

### Email link (the default)

```
POST /auth/link/request   { "email": "ada@example.com", "session_challenge": "<random 32+ chars you keep>" }
        -> 202 { delivery, masked_destination, expires_in, resend_available_in }
```

Always `202`, whether or not the address has an account. The body is byte-identical for known and unknown addresses; do not try to infer anything from it. Show `masked_destination` on the "check your email" screen and drive the resend cooldown from `resend_available_in`, not a constant.

The email contains a link carrying a token. Open it in the app (deep link) and:

```
POST /auth/link/consume   { "token": "<from the link>", "session_challenge": "<the same value>" }
        -> 200 Session
```

- **POST only.** Mail scanners prefetch URLs, so a GET that consumed the token would burn it before the person tapped.
- A token works once. A second use returns **410** `link_already_used`; an old one returns **410** `link_expired`.
- If the link is opened on a **different device** than the one that asked, the response is **409** `device_code_required` with a 6 digit `device_code`. The person types that code into the original device, which calls `consume` again with `device_code` set.

### Google and Apple

`POST /auth/oauth/google` takes `{ id_token, nonce }`. `POST /auth/oauth/apple` takes `{ identity_token, authorization_code, nonce, full_name }` (Apple sends the name only once, on the first sign-in). The server verifies the token against the provider's keys; a profile sent by the client is never trusted. Both return a `Session`.

### The session

```json
{
  "access_token": "eyJ...",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "...",
  "refresh_expires_in": 2592000,
  "is_new_user": true,
  "onboarding": { "...": "see the Session schema" }
}
```

Route straight from `is_new_user` and `onboarding`; you do not need a `GET /me` first.

### Refresh and sign out

```
POST /auth/refresh   { "refresh_token": "..." }  -> 200 RefreshedSession   (same as Session, without onboarding)
POST /auth/logout    { "refresh_token": "..." }  -> 204
```

Refresh in the background a minute or two before `expires_in`. **Store the new refresh token immediately**: the old one stops working. Presenting a refresh token that was already rotated returns **401** `refresh_reuse_detected` and revokes the whole session family. That is theft detection; the correct response is to sign the user out.

### Choosing a username

After first sign-in, `POST /auth/username`. Usernames are unique and case-insensitive. A name someone reserved on the waitlist can be taken by the person with the same email address, and nobody else. Taken or reserved names return **409** `username_taken`.

---

## 3. Errors

Every failure is a problem document:

```json
{
  "type": "consent_required",
  "title": "Consent required",
  "status": 403,
  "detail": "ai_processing has not been granted",
  "instance": "a35442eeb2d24660a2991670a2539027",
  "errors": [{ "field": "ai_processing", "code": "consent_required", "message": "..." }]
}
```

- **Branch on `type`**, never on `title` or `detail`; those are prose and may be reworded.
- `instance` is the trace id. Show it in "something went wrong" screens and put it in bug reports.
- `errors` appears for field-level validation failures (`422`) and for consent.

| `type` | Status | Meaning, and what the app should do |
|---|---|---|
| `unauthenticated` | 401 | No or bad token. Send the person to sign in. |
| `token_expired` | 401 | Refresh, then retry once. |
| `refresh_reuse_detected` | 401 | Sign out everywhere. |
| `forbidden` | 403 | Not allowed. Do not retry. |
| `consent_required` | 403 | Show the consent screen for the purpose in `errors[0].field`. Not an error dialog. |
| `age_restricted` | 403 | Under the age limit. |
| `link_expired`, `link_already_used` | 410 | Offer a new link. |
| `device_code_required` | 409 | Ask for the code shown on the other device. |
| `device_code_invalid` | 400 | Wrong code; let them retry. |
| `validation_failed` | 422 | Read `errors[]` and mark the fields. |
| `idempotency_key_required` | 400 | Send a unique `Idempotency-Key` (contact form). |
| `username_taken` | 409 | `errors[0].field` is `username`. Offer another. |
| `not_found` | 404 | |
| `conflict` | 409 | The item is not in a state that allows this. |
| `unsupported_media_type`, `payload_too_large` | 415, 413 | Image type or size. |
| `asset_not_ready` | 409 | The upload is still being processed. Poll the asset. |
| `asset_rejected` | 422 | The image failed the safety checks. Ask for another. |
| `empty_pool` | 422 | Not enough in the wardrobe to build a look. |
| `budget_exceeded` | 429 | The daily generation allowance is used. |
| `guardrail_blocked` | 422 | The request cannot be processed. |
| `rate_limited` | 429 | Wait `Retry-After` seconds. |
| `model_unavailable`, `service_unavailable`, `maintenance` | 503 | Try again later. |
| `render_failed` | 500 | A look could not be rendered. Offer to try again. |

---

## 4. Limits

Limits are applied per user where there is one and per IP address where there is not. Exceeding one returns **429** with `Retry-After`; retrying sooner extends the wait.

| Class | Applies to | Limit |
|---|---|---|
| `auth_link_request` | `POST /auth/link/request` | 10 per hour per IP |
| `auth_link_consume` | `POST /auth/link/consume` | 10 per hour per IP |
| `auth_oauth` | `POST /auth/oauth/*` | 20 per hour per IP |
| `early_access` | `POST /early-access` | 5 per hour, 20 per day, per IP |
| `contact` | `POST /contact` | 5 per hour, 20 per day, per IP |
| `quiz_preview` | `POST /quiz/preview` | 60 per hour per IP |
| `generation` | `POST /looks/*` | 5 per hour, 20 per day |
| `fabric_style` | `POST /fabric/*/style` | 30 per day |
| `spree_message` | `POST /spree/sessions/*/messages` | 20 per hour, 50 per day |
| `upload_sign` | `POST /uploads/sign` | 100 per day |
| `read` | other GETs | 300 per minute |
| `write` | other writes | 120 per minute |

Not limited: `/healthz`, `/readyz`, `/openapi.json`, `/v1/cards/*` and `/v1/dna/*` (card images and share data are signed, and link-preview crawlers fetch them in bursts).

---

## 5. Consent

Some endpoints need a consent purpose to be granted: `camera_photos`, `ai_processing`, `location_weather`, `marketing_comms`, and others. The reference names the purpose in each operation's description (`Consent: <purpose>`).

- `GET /me/consents` lists what the person has granted; `PUT /me/consents` changes it.
- A missing grant returns `403 consent_required`. Show the consent surface for that purpose, then retry.
- Revoking marketing consent also stops marketing email (see section 11).

---

## 6. Lists, pagination and jobs

### Cursor pagination

List endpoints accept `limit` (1 to 100, default 20) and `cursor`, and return the page's items with `next_cursor` and `has_more`. Pass `next_cursor` back as `cursor` to get the next page; `has_more: false` means the end. Cursors are opaque; do not build or parse them.

### Long-running work

Look generation and fabric styling return **202** with a job envelope:

```json
{ "job_id": "…", "status": "queued", "poll_url": "…", "stream_url": "…", "estimated_seconds": 30 }
```

Follow it one of two ways:

- **Server-sent events** at `stream_url`. Events: `progress`, `done`, `failed`. The connection closes after a terminal event. If it drops, reconnect or fall back to polling; progress is server-side state, nothing is lost.
- **Polling** `GET /looks/jobs/{job_id}` every 2 seconds.

States: `queued`, `analyzing`, `assembling`, `rendering`, `done`, `failed`. Typical time is 20 to 45 seconds.

### Uploads

Photos never go straight to a CDN: the server redacts faces and text first.

1. `POST /uploads/sign` with `{ kind, content_type, byte_size }` (consent `camera_photos`) returns **201** with `{ asset_id, upload_url, fields, expires_at }`.
2. `PUT {upload_url}` as `multipart/form-data` with one field, `file`.
3. Poll `GET /uploads/{asset_id}` until `status` is `ready` or `rejected`. Until `ready` the asset cannot be used elsewhere (`409 asset_not_ready`).

---

## 7. Style DNA: the quiz, the card and sharing

### The quiz

`GET /quiz` returns the questions. **Build the screen from the response**, never from a fixed layout: the number of options varies and so does how many may be chosen.

```json
{
  "id": 4,
  "prompt": "Pick your tones.",
  "progress": 45,
  "max_choices": 3,
  "options": [ { "id": "A", "label": "Neutral" }, { "id": "B", "label": "Earth & Heritage" } ]
}
```

- `max_choices: 1` means a single choice (radio buttons). More than 1 means checkboxes, up to that many. A response without the field means 1.
- Ticked options **share** the question's weight equally, so choosing more never gives a question a bigger say. The server does the scoring; the client never computes a result.

### Sending answers

`answers` maps a question id to an option id, or to a list of option ids:

```json
{ "quiz_version": "dna-2026-08-v1",
  "answers": { "1": ["A", "C"], "2": "C", "3": "D", "4": ["A", "D"], "5": "A", "6": "A" } }
```

A single choice may be a string or a one element list. Order and repeats do not matter. An empty list, more than `max_choices`, or an unknown option is `422`.

| Endpoint | Auth | Stores | Use |
|---|---|---|---|
| `POST /quiz/preview` | none | nothing | Show a card to a visitor before they sign up. Limited per IP. |
| `POST /quiz/submit` | bearer | yes | The signed-in flow. Once per 30 days; use `POST /quiz/retake` to open the window. |
| `GET /quiz/result`, `GET /quiz/card` | bearer | | Read the stored result and the card status |

### The result

A `DnaResult` has `dominant`, optional `alter_ego` and `wildcard` (each `{id, name, percentage, gradient_from, gradient_to}`), `tagline`, `blend_line`, optional `personal_line`, raw `scores`, and `card_urls`. Percentages across the shown personas total exactly 100; never round them again. Close the layout up when `alter_ego`, `wildcard` or `personal_line` is null.

The six persona ids are `CM` (Cultural Minimalist), `OR` (Owambe Royalty), `SL` (Soft Luxe), `SC` (Street Alchemist), `CE` (Corporate Edge) and `NF` (Neo-Fusion).

### The card as an image

`card_urls` carries **signed** addresses:

| Field | Image |
|---|---|
| `stories_url` | 1080×1920 PNG, for Instagram Stories, WhatsApp status, TikTok |
| `square_url` | 1080×1350 PNG (4:5), for a feed post |
| `share_url` | The public page for this card (see below) |

Use the addresses exactly as given. They are signed, so a changed address returns `401`, and the image behind an address never changes, so it is served with a one year `immutable` cache.

Offer **Story** and **Post** as the two shapes. A browser or app cannot know which app the person will share to, so let them choose; default to Story on a phone.

### Link previews

`share_url` is `https://faueofficial.com/dna/<token>`. Pasting it into WhatsApp, iMessage, X, Facebook or LinkedIn shows a preview card (a 1200×630 image, the persona and the blend) because the page serves Open Graph tags.

To read a shared card natively in the app, take the part after `/dna/` and call:

```
GET /v1/dna/{token}   (no sign-in)
  -> { username, persona, persona_id, percentage, blend[], tagline, blend_line, title, description,
       images: { preview, story, post } }
```

A forged or invented token returns `401`. The answer is cacheable for an hour.

---

## 8. The waitlist (before the app opens)

`POST /early-access` is public. It takes the quiz answers plus the details to hold, scores the answers again on the server, stores the entry and returns the card in one round trip.

```json
{ "email": "ada@example.com", "username": "ada_obi", "quiz_version": "dna-2026-08-v1",
  "answers": { "1": ["A", "C"], "2": "C", "3": "D", "4": "A", "5": "A", "6": "A" },
  "gender": "female", "consent": true, "policy_version": "2026-10-draft-1", "website": "" }
```

- `gender` is `female`, `male` or `prefer_not_to_say`, and optional. It only decides which model photograph sits behind the card; `prefer_not_to_say` gets the plain card.
- `consent` must be `true`. `website` is a honeypot and must be empty.
- The username is a **reservation**. A name that is reserved, in use or reads as official (`admin`, `faue`, `support`) is `409 username_taken`.
- An address already on the list gets the **same** response as a first signup, so the endpoint cannot be used to find out who has joined.
- The response carries `card_photo` (`f1`, `f2`, `m1`, `m2` or null) and `dna.card_urls` with `share_url`.

A confirmation email goes out once, with the person's card in it.

---

## 9. Contact form

`POST /contact` is public and limited per IP. Required: `topic` (`support`, `data_request`, `press_partnership`, `other`), `name`, `email`, `message` and `policy_version`. Optional: `partner_type`, `organisation`, `role`, `reference_code`, and a `website` honeypot that must be empty. The **`Idempotency-Key` header is required** (8 to 128 printable characters, unique per submission); without it the call returns **400** `idempotency_key_required`. A retry with the same key returns the original `reference`. Show the `reference` to the person. Message text and sender details are deleted after 72 hours.

---

## 10. Unsubscribing

No sign-in is needed, because someone who wants the email to stop will not sign in to stop it.

```
GET  /unsubscribe/{token}   -> { "category": "waitlist" | "marketing" | ... }     (changes nothing)
POST /unsubscribe/{token}   -> { "category": "...", "unsubscribed": true }       (idempotent)
```

- `token` comes from the unsubscribe link in an email, `https://faueofficial.com/unsubscribe#t=<token>`. The token is in the URL **fragment** so it never reaches a server log.
- Show a confirmation screen after `GET`; only `POST` acts. That also keeps mail scanners from unsubscribing anyone by prefetching.
- Waitlist members who unsubscribe are marked `unsubscribed` and their reserved username is released.
- The `List-Unsubscribe` and `List-Unsubscribe-Post` headers on list email point at the same `POST`, so a mail client's own Unsubscribe button works.

---

## 11. Email the system sends

| Email | When | Has an unsubscribe link |
|---|---|---|
| Sign-in link | Someone asks to sign in | no |
| Welcome | An account signs in for the first time | no |
| Style DNA ready | A signed-in user finishes the quiz, with their card | no |
| Waitlist confirmation | Someone joins the waitlist | yes |
| "FAUE is open" | A team member invites a waitlist member | yes |
| Removed from the waitlist | A team member deletes an entry | no |
| Reply to a message, message from the team | A team member writes | no |
| Look ready, welcome back, seasonal | **Not triggered yet** | marketing ones yes |

Transactional email cannot be unsubscribed from (you cannot unsubscribe from a sign-in link). Marketing email always has the link and is stopped by revoking `marketing_comms` consent.

---

## 12. The admin API

The operations console uses `https://api.faueofficial.com/admin/v1`. It is a **separate realm**: a user token cannot authenticate there, and an admin token cannot authenticate against `/v1`. Sessions are 8 hours, never sliding, and revocation takes effect immediately.

### Signing in

```
POST /auth/link/request   { "email" }                       -> 202 (always; reveals nothing about who is an admin)
        # an email goes only to an ACTIVE admin account, with a link to https://admin.faueofficial.com/auth/verify?t=<token>
POST /auth/link/consume   { "token", "code" }               -> 200 { access_token, token_type, expires_in, role }
```

`code` is the 6 digit TOTP from the authenticator app; both factors are checked before the link is spent.

**First sign-in** returns **428** `mfa_enrolment_required` with an `enrolment_token` in the problem document (not an error to show). Then:

```
POST /auth/mfa/enrol     { "enrolment_token" }          -> { secret, provisioning_uri }   (render provisioning_uri as a QR)
POST /auth/mfa/confirm   { "enrolment_token", "code" }  -> 204
```

then sign in again with a new link. A new admin arrives by invitation: `POST /admins/invite` (admin role) emails a link to `https://admin.faueofficial.com/auth/invite?t=<token>`, which the invitee spends with `POST /auth/invite/accept` to receive an enrolment token. The account cannot sign in until MFA is confirmed.

### Roles and capabilities

| Role | Can |
|---|---|
| `viewer` | Read health, queues, flags, model config, style library |
| `curator` | Read health; read and write the style library |
| `support` | Read health; read and write contact messages and the waitlist; user support actions |
| `ml_ops` | Health and queues; review queue; model config and flags |
| `admin` | Everything, including the audit log and managing the team |

`GET /me` returns the signed-in role and its `capabilities`; build the menu from that. A call without the capability returns `403` that names the capability it lacked.

### Endpoint index

| Area | Endpoints |
|---|---|
| Console | `GET /me`, `GET /overview`, `GET /audit`, `GET /admins` |
| Messages | `GET /contact/messages`, `GET`/`PATCH /contact/messages/{id}`, `POST /contact/messages/{id}/reply` |
| Waitlist | `GET /waitlist`, `GET /waitlist/summary`, `GET`/`PATCH`/`DELETE /waitlist/{id}`, `POST /waitlist/{id}/message` |
| Monitoring | `GET /ops/health`, `GET /ops/events`, `GET /ops/notifications` |
| Sessions and team | `GET /auth/sessions`, `DELETE /auth/sessions/{jti}`, `POST /auth/sessions/revoke`, `POST /auth/logout`, `POST /admins/invite` |

Details, schemas and examples for each are in [`admin-api-reference.md`](admin-api-reference.md).

### Things the admin API will not do

- Reply text, and message text in general, is never written to the audit log. Only the fact, the target and a length are.
- Setting a waitlist member to `invited` sends the launch email once and refuses anyone who unsubscribed.
- Deleting a waitlist member emails them a short confirmation first, then deletes the entry.

---

## 13. Keeping this current

1. Change the endpoint in `api-gateway`.
2. Change the contract in `openapi/gateway.v1.yaml` or `openapi/gateway.admin.v1.yaml`, and add an entry to `CHANGELOG.md` **before** the change merges.
3. Run `python3 tools/build_reference.py` to refresh the two reference files.
4. Contract tests in `api-gateway/tests/contract` keep the code and the published schema from drifting; if one fails, the contract or the code is wrong.
