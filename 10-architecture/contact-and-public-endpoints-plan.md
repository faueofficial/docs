# Backend plan: contact messages and public endpoints

**Stage:** Part 1 built, not yet released · **Written:** 2026-10-09 · **Drives:** the landing site (`landing/`)

The landing site now has a contact form and a cookie panel. The form calls an endpoint that does not exist yet, and the shareable pages the product docs promise (`/dna/{id}`, `/look/{id}`, `/auth/verify`) have no backend to read from. This plan lists what the gateway needs, in the order the site needs it.

Nothing here is built. Names and shapes are proposals; the OpenAPI file is updated first, per the contract rules.

## Status (2026-10-09)

**Part 1, contact messages, is built and tested locally. It is not released.**

| Piece | Where | State |
|---|---|---|
| `gateway.contact_messages` table, migration `0008_contact_messages` | `faue-db` | Applies, rolls back and reapplies; `alembic check` clean; schema tests pass |
| `POST /v1/contact` | `api-gateway`: `app/api/v1/contact.py`, `app/modules/contact/` | 52 tests: validation, honeypot, idempotency, encryption at rest, rate limit, outbox event, optional sign-in |
| `contact.received` handler and `contact_received` email | `app/events/handlers/contact.py`, `notify/templates/` | Sends once, reply-to is the sender, subject never contains sender text, HTML escaped, retries on failure |
| 72-hour purge | `app/workers/contact_purge.py`, `purge_expired()` | Clears every personal column, keeps the residual row; runs every 15 minutes |
| Rate limit class `contact` | `ratelimit/policy.py` | 5 per hour, 20 per day per IP |
| `reply_to` on the email sender | `identity/email_sender.py` | Resend and the recording sender |
| Contract and docs | `gateway.v1.yaml`, `event-catalog.md`, `ropa.md`, `error-model.md` | Updated |

**Also built (2026-10-12), see "Admin and waitlist" below:** the admin API for messages (list, read, mark, reply), `POST /v1/quiz/preview`, `POST /v1/early-access`, and the admin API for the waitlist.

**Not built yet:** export and erasure of one person's messages by `email_bidx`; unsubscribe link and flow for waitlist members; the public share read endpoints (`/dna/{id}`, `/look/{id}`) and the share-id records behind them; an admin console UI (only the API exists).

### Admin and waitlist (built 2026-10-12)

| Piece | Where |
|---|---|
| `GET/PATCH /admin/v1/contact/messages[/{id}]`, `POST .../reply` | `app/api/admin/contact.py`, `app/modules/contact/admin.py`. Capabilities `contact.read`, `contact.write` (roles `support`, `admin`). A reply is emailed from the team to the sender with their own message quoted, replies go to `hello@` or `partners@` by topic, nothing is saved if sending fails, and it is refused for a purged message. Reads and changes are audited without the text |
| `POST /v1/quiz/preview` | Scores answers with no account and stores nothing. Public, rate limited per IP |
| `POST /v1/early-access` | Public. Scores answers on the server, stores email (encrypted, blind-indexed), username reservation, answers and style. Duplicate email gets an identical answer. Replies with the card, so the website can show it as the reward for joining. Sends one confirmation email through the outbox |
| `GET /admin/v1/waitlist`, `/summary`, `/{id}`, `PATCH`, `POST /{id}/message` | `app/api/admin/waitlist.py`. Capabilities `waitlist.read`, `waitlist.write`. Search by exact email or username prefix. A message goes to one member, refused if they unsubscribed |
| Username reservation at sign-up | `POST /auth/username` refuses a name reserved on the waitlist unless the account has the email it was reserved with, and links the two |
| `faue-db` migration `0009_waitlist_entries` | New table `gateway.waitlist_entries` |
| Worker crash fix | `sqlalchemy[asyncio]` declared in `api-gateway`, `faue-core` and `faue-db`, and the Dockerfile fails the build if `greenlet` is missing |

### To release

1. `faue-db`: commit, tag a new version (it is `v0.1.0` now) and push. It now carries two migrations, `0008` and `0009`. The gateway installs it by git tag, so without a new tag the deployed gateway has no `ContactMessage` model.
2. `api-gateway`: point `pyproject.toml` at the new `faue-db` tag, deploy.
3. Apply the migrations to the production database **before** deploying the gateway and workers: `alembic upgrade head` from `faue-db`, with `DATABASE_URL` set to the migrator role. A worker that starts first fails with `relation "gateway.contact_messages" does not exist`.
4. Gateway environment: add the site to CORS, for example `CORS_ORIGINS=["https://faueofficial.com","https://www.faueofficial.com"]` (the default allows only `http://localhost:3000`, so browsers would block the form). `RESEND_API_KEY` must be set, or the handler only records emails in memory.
5. Resend: the sending domain `faueofficial.com` must be verified. It shares the domain with Cloudflare Email Routing for inbound mail, so the domain can have only **one SPF record**: merge Cloudflare's and Resend's `include:` entries into it.
6. Run the workers: `python -m app.workers outbox_relay contact_purge pending_deliveries`. Name them, so a worker whose configuration is missing (for example `backup_replication` without storage settings) cannot take the others down. `pending_deliveries` is the safety net for emails: with `EVENT_TRANSPORT=inprocess` a handler that raises is logged and skipped and the event is marked published, so the outbox does **not** retry it. The sweep finds saved rows with no sent timestamp and sends them. With `EVENT_TRANSPORT=inprocess` the relay runs the email handler itself. With `rabbit`, the queue `gateway.contact` must exist and be consumed.
7. The website needs no change: it already calls this endpoint, and the "Sending is not switched on yet" message stops appearing once it answers `202`.

## What exists today (checked in `api-gateway`, 2026-10-09)

| Area | State |
|---|---|
| `GET /quiz`, `POST /quiz/submit`, `GET /quiz/result`, `GET /quiz/card`, `POST /quiz/retake` | Implemented. Submit, result, card and retake need a bearer token. |
| `quiz.scoring.score(answers)` | A pure function. It needs no user and no database, so scoring without an account is possible. |
| `POST /looks/{id}/share`, `POST /fabric/{id}/tailor-share` | Routes exist and raise `NotImplementedError`. The same is true of all `/looks/*`, `/fabric/*` and `/privacy/*` routes. |
| Share ids | No model, table or service. `docs/40-frontend/deeplinks.md` requires separate, unguessable, revocable ids. |
| Email | `identity/email_sender.py` sends through Resend behind a protocol, with a recording sender for tests. Sending address is on the `faueofficial.com` domain, never Gmail. |
| Rate limiting | `ratelimit/policy.py`: classes by method and path. Anything unmatched falls to `write` (120/min), which is far too loose for a public form. |
| CORS | Allows `GET POST PATCH DELETE` and the `Idempotency-Key` header. `PUT` is missing (already noted). |
| Events | Outbox publisher and idempotent consumers exist in `faue-core`. |

## Part 1. Contact messages

### Contract

`POST /v1/contact` — no authentication, `202 Accepted`.

```json
{
  "topic": "support | data_request | press_partnership | other",
  "name": "string, 1-100",
  "email": "valid address, max 254",
  "message": "string, 10-4000",
  "reference_code": "string, max 64, optional",
  "policy_version": "2026-10-draft-1",
  "website": "honeypot, must be empty"
}
```

Response: `{ "reference": "FAUE-XXXXXX" }`. The reference is short, human-readable and non-sequential. Headers: `Idempotency-Key` required. Errors follow RFC 7807: `422 validation_error`, `429 rate_limited`, `400 idempotency_key_required`.

If a valid bearer token is present, store `user_id` as well. The site does not send one today.

Partner enquiries (`/partners` form) use the same endpoint with `topic: "press_partnership"` and three extra optional fields: `partner_type` (`tailor`, `designer`, `fabric_seller`, `event_planner`, `stylist_creator`, `media`, `other`), `organisation` (max 120) and `role` (max 80). Store them in the same table as encrypted or plain columns per the PII rules.

**Routing:** the inbox email goes to `hello@faueofficial.com` by default and to `partners@faueofficial.com` when `topic` is `press_partnership`. Both mailboxes exist as Cloudflare forwarding addresses (2026-10-09). Settings: `contact_inbox` and `contact_inbox_partners`. The sending address stays on the Resend-verified domain, never a Gmail or forwarding address.

### Storage

New table `gateway.contact_messages` in `faue-db`, with an Alembic migration.

| Column | Notes |
|---|---|
| `id` uuid, `reference` text unique | Reference shown to the sender. |
| `topic` enum, `status` enum (`new`, `replied`, `closed`) | Status is what lets us "track the writer". |
| `name_enc`, `email_enc`, `message_enc` | Envelope encryption from `faue-core`. These are personal data. |
| `email_blind_index` | Blind index from `faue-core`, so all messages from one person can be found and exported or erased without decrypting everything. |
| `reference_code`, `user_id` (nullable) | Optional links to an app error trace or an account. |
| `policy_version`, `created_at`, `replied_at`, `handled_by` | `policy_version` records what the sender agreed to. |
| `ip_hash` | Keyed hash, for abuse analysis only. Never the raw IP. |
| `deleted_at` | Soft delete, then the retention worker removes the row. |

Not workspace-scoped: the sender may not have an account.

### Delivery to the FAUE inbox

1. The request handler validates, stores the row and writes a `contact.received` outbox event in the same transaction.
2. A consumer renders a catalog template (like `magic_link`) and sends it through the existing `EmailSender` with `reply_to` set to the sender and the recipient set from a new setting `contact_inbox`. Both settings default to the domain mailboxes, which forward to the team's inbox.
3. User-supplied text appears only in the body, never in headers or the subject beyond the topic label, so header injection is not possible.
4. If sending fails the row is still stored and the consumer retries. The sender is not told, because the message is saved.

No automatic confirmation email to the sender in the first release. The on-page reference is the confirmation.

### Abuse controls

- New rate class `contact`: 5 per hour and 20 per day per IP, added to `policy.py` before the route ships. Without it the route falls into the generic write limit.
- Honeypot: a non-empty `website` returns a normal-looking `202` with a fake reference and stores nothing. Count it in a metric.
- Hard size limits at the edge and in the schema. Reject HTML-only or link-only messages later if spam appears.
- Idempotency key stops double submits and retries from creating two rows.
- Phase 2, if spam shows up: Cloudflare Turnstile token verified server-side. The form needs a field for it. Do not add it speculatively.

### Admin, privacy and docs

- Admin API (`/admin/v1/contact-messages`): list, filter by status or topic, open one, mark replied or closed. Admin reads go in the audit log.
- Data rights: export and erase must find messages by `email_blind_index`. Add `contact_messages` to the export bundle and the deletion fan-out.
- Update `ropa.md` (purpose: answering enquiries; lawful basis: legitimate interest and steps requested by the person), `privacy.md` and the retention table.
- **Decided (2026-10-09): contact messages are kept for 3 days.** The `retention_ttl` worker deletes `name_enc`, `email_enc`, `message_enc`, `email_blind_index` and `ip_hash` 72 hours after `created_at`. Consequences to design for:
  - Keep a residual row with no personal data (`reference`, `topic`, `status`, `created_at`, `replied_at`) so admins can still count and audit. Say so in `ropa.md`.
  - The inbox email is the working copy. Anything that must outlive 3 days (a data request in progress, a partnership thread) lives in the mailbox or ticket the team uses, not in this table.
  - A `data_request` must not wait on the 3-day clock. The 30-day statutory deadline is tracked in the existing privacy request flow; the message only prompts the team to open one.
  - The site promises no reply time, so a message can be deleted unanswered. The success screen and privacy page say that it is deleted after 3 days; revisit once a reply target exists.
  - Add a test: after 72 hours no personal column is readable, and the residual row remains.

### Tests

Schema limits; honeypot stores nothing; idempotent replay returns the same reference; rate limit returns 429 on the sixth request; outbox event is written in the same transaction; consumer sends once and is safe to run twice; header injection attempt in `name`; erase by blind index removes rows; contract test against the OpenAPI file.

## Part 2. Public endpoints for the web

### 2a. Score without an account (smallest win)

`POST /v1/quiz/preview` — no authentication, no storage.

Body: `{ "answers": { "1": "A", ... } }`. Response: the same `DnaResult` shape as `GET /quiz/result`, minus anything tied to a user. It calls `quiz.scoring.score` and the existing copy loader. Rate class `quiz_preview` per IP.

This lets the landing quiz end in the real card for anyone, with a "save this" prompt to sign in. It also removes the biggest gap on the site today, where the quiz is a read-only preview.
**Decided (2026-10-09): the quiz may be taken before sign-up, and the step after it prompts sign-up.** The docs assumed the quiz sits behind an account; update `docs/40-frontend/screens.md` and `auth-flows.md` to match.

Flow on the web: answer six questions, call `quiz/preview`, show the real card, then ask the person to sign in to save it, get the share image and unlock the rest. After a magic-link sign-in the client calls `POST /quiz/submit` with the answers it kept, so the saved result is the one they saw. Keep the answers in memory or session storage only until sign-in completes, and delete them afterwards. Preview results are never stored on the server, so closing the tab without signing in loses nothing the server held.

### 2b. Sign in on the web

The app side is built: `POST /auth/link/request` and `POST /auth/link/consume` work. What is missing is the page at `https://faueofficial.com/auth/verify` in the landing project, and it needs no new backend work except:

- add `faueofficial.com` and the staging site to `cors_origins`;
- return the token in the response body of `consume` for web clients, or set it as a cookie. **Decision needed:** where the web client keeps its token (memory plus refresh cookie is the safe default).
- the page must consume on `POST` after a button press, never on `GET`, as the docs require.

### 2c. Share ids and public reads

Build in this order, because each depends on the one before.

1. **Share record.** Table `gateway.shares`: `id`, `share_id` (random, 12+ chars, not derived from any internal id), `kind` (`dna`, `look`, `tailor_brief`), `owner_user_id`, `payload_snapshot` (the exact content to show, so later edits or deletes do not leak), `created_at`, `revoked_at`, `expires_at` nullable.
2. **Create.** Implement `POST /quiz/card` sharing (the card endpoint exists; add share creation), `POST /looks/{id}/share` and `POST /fabric/{id}/tailor-share`. These currently raise `NotImplementedError`. Looks and fabric depend on the generation work, so DNA sharing ships first.
3. **Revoke.** `DELETE /shares/{share_id}` for the owner. Revocation returns `410 Gone` on the public read immediately.
4. **Public reads.** `GET /v1/public/dna/{share_id}`, `GET /v1/public/look/{share_id}`. No authentication. Return only the snapshot: persona ids, percentages, tier line, palette, first name or a chosen display name if the owner opted in, and a share image URL. Never user id, email or anything unsnapshotted. `Cache-Control` short; `404` and `410` are distinct. Rate class `public_read` per IP, generous but not exempt.
5. **Consent.** Sharing is an act by the owner. Record it as a consent-style event with the policy version, and show exactly what the page will contain before it is created.
6. **Web pages.** `landing/` adds `/dna/[id]` and `/look/[id]` as server-rendered pages with Open Graph tags pointing at the share image, a "make your own" call to action, and a `noindex` option for owners who want it.

### 2d. Smaller items

- `/.well-known/apple-app-site-association` and `assetlinks.json` are served by the landing site once the app ids exist. Needs the Apple team id and the Android signing fingerprint from the app team.
- `/style/{style_id}` public pages can reuse the `/styles` content already on the site; a gateway endpoint is only needed if styles become editable data.
- Add `PUT` to CORS methods when the first `PUT` route is called from a browser.
- Fix the stale `staging-api` host in the docs (does not resolve; the live host is `api.faueofficial.com`).

## Suggested order

| Step | Work | Unblocks on the site |
|---|---|---|
| 1 | `contact_messages` table, `POST /contact`, rate class, outbox consumer, inbox email, tests, OpenAPI | The contact form starts working with no frontend change |
| 2 | Admin list for contact messages | Someone can work the inbox |
| 3 | `POST /quiz/preview` (if approved) | Real result card at the end of the web quiz |
| 4 | Web token handling decision, CORS origins | `/auth/verify` and web sign-in |
| 5 | `shares` table, DNA share create, revoke, public read | `/dna/[id]` |
| 6 | Looks and fabric share, after generation exists | `/look/[id]` and tailor briefs |

Steps 1 to 3 now have every product decision they need. Step 1 is roughly a day of work including tests.

## Decisions for the founders

0. **Early-access sign-up (decided to build with the backend):** `POST /v1/early-access` with email, optional WhatsApp number, separate consent text and policy version, dedupe on the email blind index and an idempotency key. It needs its own retention rule, because unlike a contact message it is kept until launch or until the person unsubscribes. Same rate-limit and honeypot approach as `/contact`.
1. ~~Retention period for contact messages~~ Decided: 3 days.
2. ~~Is scoring the quiz before sign-up allowed?~~ Decided: yes, with a sign-up prompt after the result.
3. Where the web client keeps its sign-in token. (step 4)
4. ~~A domain address for the FAUE inbox~~ Done: `hello@` and `partners@faueofficial.com`.
5. Whether owners can choose a display name on shared cards, or shares are always anonymous.
