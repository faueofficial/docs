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

## 2026-10-30 (evening) — Pinterest boards you can browse, agent settings, text vectors, an SMS switch

**Gateway (additive)**
- New `GET /v1/integrations/pinterest/boards/{board_id}/pins?limit=&bookmark=`: a page of a board's pins (title, description, image on Pinterest's image host, `imported`) and `next_bookmark`. Read live, not stored. 403 for a board Pinterest will not show this app (not retried), 409 when the connection needs signing in again.
- The Pinterest callback redirect now carries `?pinterest=error&reason=` with one of `grant_rejected`, `credentials_rejected`, `rate_limited`, `unavailable`, `state_expired`, `not_configured`, `pinterest_error`, `unexpected`.
- `GET` and `PUT /v1/agent/settings` are implemented (were stubs). `PUT` takes only the fields being changed; turning on `daily_enabled` or an `autonomy_level` of 1 or more is 403 naming `agent_proactive` unless granted. The response adds `built_level` (0). `use_weather: false` leaves the weather out of looks.
- `POST /v1/looks/generate` accepts `event_id` (one of your events), `mood` and `note` (the last two are used only with personalisation consent).
- Admin: the runtime setting `sms_provider` (`termii`, `africastalking`, `twilio`, `off`) is a new `choice` kind; the settings listing gains `choices` (each value `ready` or `no credentials`). Choosing a provider with no keys in the environment is 422.
- Community publishing now works: the look card is stored as the post's public picture and deleted with the post and with the account.

**Database (expand-only):** migration `0027_agent_settings` adds `gateway.agent_settings`.

**ase (internal, additive)**
- `POST /internal/embeddings/reembed` is implemented (was a stub), with new `POST /internal/embeddings/similar` and `POST /internal/embeddings/fabric-match`. Text vectors of a redacted description of each piece or cloth, through Cloudflare Workers AI (`@cf/baai/bge-m3`, 1024 numbers) or OpenRouter. 424 (not a 5xx) when no embedding model is configured.
- Settings: `EMBEDDING_PROVIDER` accepts `workers_ai` and `openrouter` (`openai/text-embedding-3-small` through OpenRouter works and is what ASE is set to); `CLOUDFLARE_WORKER_AI_KEY` is read as the Workers AI token as well as `CLOUDFLARE_API_TOKEN`.

## 2026-10-30 — Share cards, picture shapes, and reasons written from the whole look

**Gateway (additive)**
- `POST /v1/looks/{id}/share` now works. It returns the shapes a look can be downloaded in (`4x5` feed, `9x16` stories and status, `1x1` square, `og` link preview), a caption, and the default shape for an optional `destination`.
- New `GET /v1/looks/{id}/share-image?ratio=` returns the look card as a JPEG attachment. A look from the person's own wardrobe shows their own photos and is never drawn by a model. A look with nothing owned (an empty-vault style card) gets a generated picture when ase can draw one, and the card is made without one when it cannot.
- `POST /v1/fabric/{id}/tailor-share` now works and returns the tailor card as a JPEG (fabric photo, style, what to make, notes, measurements, and an illustration of the style in the cloth when one can be drawn, labelled as an illustration). New request body `TailorShareIn`. Measurements are not stored or logged.
- Neither card is stored or given a public address: each is drawn when asked for. Nothing to purge on account deletion.
- `POST /v1/looks/generate` now sends ase the nearest matching upcoming event (`kind`, `days_until`, and the person's own title only with personalisation consent).

**ase (internal, additive)**
- New `POST /internal/looks/{id}/image` (archetype looks only; **409** for an owned look) and `POST /internal/fabric/style-image`. Both answer **424** when a picture cannot be drawn, deliberately not a 5xx, so a missing picture never trips the gateway's circuit breaker.
- Context pack accepts `event: {kind, name, days_until}`.
- The look-pipeline skill gains a `narrate` phase (05): a model writes each look's reason from the event, weather, taste, pieces and colour story, kept only if it passes the grounding check. The engine's own sentences, now varied per look and drawn from more facts, remain the fallback.

## 2026-10-21 — The styling engine is connected

| Change | Type | Consumer action |
|---|---|---|
| `POST /looks/generate`, `/looks/{id}/regenerate`, `/looks/{id}/adjust` now work. They return a job (`202`); poll `GET /looks/jobs/{job_id}` (`queued`, `analyzing`, `assembling`, `rendering`, `done`, `failed`) or follow `.../stream` (SSE) | `changed` | Send `Idempotency-Key` to make a retry return the same job. A `failed` job was not counted against the person. |
| `POST /looks/{id}/adjust` takes free words (`instruction`, up to 120 characters), not a fixed list. Words that are not understood fail the job with `unknown_adjustment` | `changed` | Show the failure's hint; the buttons' own words (`warmer`, `cooler`, `less_formal`, `more_formal`) keep working. |
| `GET /looks`, `GET /looks/{id}`, `POST/DELETE /looks/{id}/save`, `POST /looks/{id}/feedback` | `added` (were planned) | `feedback.signal` is one of `more_like_this`, `saved`, `worn`, `shared`, `tailor_send`, `regenerated`, `dismissed`, `not_my_style`; `reason` for `not_my_style` is `too_formal` or `too_casual`. |
| `GET /me/ase`, `POST /me/ase/forget`, `DELETE /me/ase`, `PUT/DELETE /me/ase/facts/{key}` | `added` | The "What ASE knows" page. Erasing takes effect on the next look. |
| `POST /spree/sessions`, `.../messages`, `GET .../{id}` now work. A reply is one JSON body, not SSE; attachments are not accepted yet | `changed` | Off-topic input returns a templated refusal with `refused: off_topic`. |
| `GET /agent/today` and `POST /agent/suggestions/{run_id}/respond` now work. One run per day per person | `changed` | `respond.outcome` is `accepted`, `dismissed`, `saved` or `worn`. |
| `POST /fabric/{asset_id}/style` now works and takes `{"fabric": "<name>"}` | `changed` | Name the cloth; identifying it from the photo arrives with the vision model. |
| `POST /vault/items` returns `suggested_colors` when the request had no `colors` and the person allowed AI processing | `added` | Offer the suggestion; never save it without the person's say. |
| `ase` internal API: `user_id` and `workspace_id` travel in the body or query, not `X-User-Id`; `GET /internal/context/weather` is removed (weather is sent in the context); `GET /internal/agent/today` is now `POST` | `breaking` (internal only) | Only the gateway calls `ase`. |

---

## 2026-10-15 — Web app sign-in, and waitlist members keep their Style DNA

| Change | Type | Consumer action |
|---|---|---|
| `POST /auth/link/request` accepts `surface` (`app` or `web`, default `app`) | `added` | The web app sends `web`. The mobile app can omit it. The emailed link opens on the matching host. |
| A person on the waitlist who signs in with the same **verified** address arrives with their Style DNA and reserved username already set | `changed` | Route on `onboarding` as usual. Do not show the quiz or username screens when `quiz_completed` and `username_set` are true. |
| `GET /quiz/result` after such a sign-in reports the quiz as taken at the time of the waitlist signup, and the retake window counts from then | `changed` | None. |

## 2026-10-15 — Lifecycle campaigns

| Change | Type | Consumer action |
|---|---|---|
| Marketing messages (day 5 to day 60, and Detty December) go to the inbox, email and push of people who granted `marketing_comms`. Off until an operator turns it on | `added` | The inbox may now contain `category: marketing` items. Show them in the All tab. |
| Reading an inbox item (`POST /notifications/{id}/read`) is what counts a message as opened | `changed` | Call it when the person actually opens the item, not when the list loads. |
| Every campaign email carries `List-Unsubscribe` one-click headers and an unsubscribe link that works without signing in | `added` | None. |

## 2026-10-15 — Phone numbers, push, SMS and WhatsApp, tunable settings

| Change | Type | Consumer action |
|---|---|---|
| `GET`, `PUT`, `DELETE /me/phone` and `POST /me/phone/verify` | `added` | Build "add your phone". SMS and WhatsApp are sent only to a verified number. |
| Push, SMS and WhatsApp are real delivery channels. Push goes to every device registered with `POST /notifications/devices`; a token the provider reports dead is removed | `changed` | Register the device token on every launch, and call `DELETE /notifications/devices/{id}` on sign-out. |
| Pinterest imports return at once; pin images arrive in the background over the next minutes (`image_status` `pending` then `cached`) | `changed` | Do not wait for images. Show the Pinterest address until `cached`. |
| Pins per board default to 100 (was 200) | `changed` | None. |
| Admin: `GET /settings`, `PUT` and `DELETE /settings/{key}` | `added` | Console only. |
| Uploads: the safety threshold defaults to 0.7 and text detection looks at 960 px | `changed` | None. Measured against 82 labelled images; see `media-detector.md`. |

## 2026-10-14 — Switches, bulk invites, deletion emails

| Change | Type | Consumer action |
|---|---|---|
| Any product route can answer `503` ("paused for a moment") when an operator has its switch off: uploads, Pinterest, shares, waitlist sign-ups; and the whole API in maintenance with `Retry-After: 300` | `added` | Treat `503` as "try again shortly", not as a failure to report. |
| Deleting an account sends two emails: one when the request is received (with the date it can still be cancelled until) and one when it is complete | `added` | None. Do not send your own. |
| Admin: `GET /flags`, `PUT /flags/{key}`, `POST /waitlist/invite-batch`, `GET /waitlist/export.csv` | `added` | Console only. |

## 2026-10-14 — Media lifecycle, and counting shares

| Change | Type | Consumer action |
|---|---|---|
| `POST /vault/items/{id}/restore` | `added` | Offer "Undo" after a delete. Deleted items are kept 30 days, then their images are removed. |
| `DELETE /vault/items/{id}` keeps the item for 30 days instead of forever | `changed` | None. A deleted item's image URL stops working once it is purged. |
| `POST /share-events` (public, anonymous) | `added` | Call it when a card is sent to Stories, posted, copied as a link or shared natively. |
| Imported pins can have a copied image: `image_status` is `cached`, `pending`, `rejected`, `failed` or `none` (`pending_detector` is renamed `pending`) | `changed` | Admin only; no client change. |
| Uploads can be refused as `unsafe_content` by a real classifier | `changed` | Handle `rejection_reason: unsafe_content` as in the contract. |
| Image URLs may be presigned links that expire after an hour when the store is private | `changed` | Re-fetch the list rather than caching image addresses for long. |
| The notification routes are implemented: `GET /notifications` (cursor paging, unread count), `POST /notifications/{id}/read`, `GET` and `PUT /notifications/preferences`, `POST /notifications/devices` | `changed` | Build the Notification screen and settings. `PUT` replaces the whole set. |
| `DELETE /notifications/devices/{device_id}` | `added` | Call it on sign-out. |

## 2026-10-14 — Share a look to FAUE

| Change | Type | Consumer action |
|---|---|---|
| `POST /shares`, `GET /shares`, `GET` and `DELETE /shares/{id}`, `PUT /shares/{id}/image` | `added` | Build the share target (iOS and Android share sheet, web share target) and the shared looks list. |
| `POST /uploads/sign` accepts `kind: share`; the documented `kind` values are corrected to `vault`, `fabric`, `avatar`, `share` (the contract listed `vault_item` and `fit`, which the API never accepted) | `added` / `fixed` | Use `share` for screenshots sent with a share. Check you were not sending `vault_item` or `fit`. |
| A share can come back `status: needs_image` with `reason` | `added` | Ask for a screenshot, upload it, then `PUT /shares/{id}/image`. This is the normal case for Instagram links. |
| Uploads: `safety_verdict` may be `unchecked` | `changed` | None for clients. No safety classifier is bundled yet, so images are not rejected for content; faces and text are still removed. |

## 2026-10-14 — Deletion waits, and ends sessions

| Change | Type | Consumer action |
|---|---|---|
| `POST /privacy/delete` no longer removes data before responding. It ends every session and schedules removal after a waiting period; the response gains `purge_after` | `changed` | Sign out and clear local data on `202`. Tell the person the date they can still change their mind. |
| `GET /privacy/delete` (is a deletion waiting) and `DELETE /privacy/delete` (cancel it, returns a fresh session) | `added` | Offer "Cancel deletion" when someone signs in during the waiting period, and replace the stored tokens with the ones returned. |
| `403 account_pending_deletion` on every route except the two above and `POST /auth/logout` | `added` | Route to the cancel screen, not a generic error. |
| Admin: ledger states `scheduled` and `cancelled`; accounts carry `deletion_scheduled` and `purge_after`; `POST /accounts/{id}/restore`; `immediate` on delete | `added` | Console only. |
| `user.deletion.requested` is now published when removal starts, not when it is requested | `changed` | Consumers that purge on it (`ase`) do so after the waiting period. |

## 2026-10-14 — Privacy rights, and connected accounts in the console

| Change | Type | Consumer action |
|---|---|---|
| `POST /privacy/export`, `POST /privacy/delete` and `POST /privacy/restrict` are implemented (they returned 500) | `changed` | Build the Privacy and data settings screen against them. Deletion is launch-blocking for the App Store. |
| `GET /privacy/export/{export_id}` | `added` | Fetch `poll_url` from the export job to download the archive (JSON, kept seven days). |
| `DELETE /privacy/restrict` | `added` | Offer "Resume processing" while a restriction is in force. |
| While restricted, gated routes return `403 forbidden` ("processing is restricted"), not `consent_required` | `added` | Show a restriction notice with a way to lift it, not the consent screen. |
| `POST /privacy/delete` removes the account before responding; the ledger tracks the rest | `changed` | Sign the person out and clear local data as soon as it returns `202`. |
| Admin: `GET /admin/v1/integrations`, `/integrations/{id}/pins`, `DELETE /integrations/{id}`, `GET /admin/v1/privacy/requests`, `POST /privacy/requests/{id}/acknowledge`, `GET /admin/v1/accounts`, `POST /accounts/{id}/reveal`, `POST /accounts/{id}/delete` | `added` | Console only. New capabilities `integration.read`, `integration.read_pins`, `integration.write`; the `support` role holds them. |

## 2026-10-14 — Pinterest connection

| Change | Type | Consumer action |
|---|---|---|
| The six `/integrations` operations are implemented (they returned 500) | `changed` | Build the Connect Pinterest, board choice and disconnect screens against them. |
| `GET /integrations/pinterest/authorize` returns a plain authorization-code URL; PKCE is not used | `fixed` | The description said OAuth2 + PKCE. Pinterest does not document PKCE. Nothing to send from the client. |
| `GET /integrations/pinterest/callback` redirects to the app with `?pinterest=connected`, `denied` or `error`; `code` and `state` are no longer required, `error` is accepted | `changed` | Read the `pinterest` parameter on return and show the outcome. |
| `GET /integrations/pinterest/boards` and `POST /integrations/pinterest/import` require consent `pinterest_sync` | `changed` | Handle `403 consent_required` as the consent screen, as for `authorize`. |
| `POST /integrations/pinterest/import`: at most 10 boards per request and 200 pins per board; `409` while an import runs | `added` | Disable the button while `status` is `syncing`. |
| `DELETE /integrations/{provider}` also deletes imported pins; `404` for an unknown provider | `changed` | None. |

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
