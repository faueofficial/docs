# Backend close-out before the ASE work

**Written:** 2026-10-14 · **Scope:** everything in `api-gateway`, `faue-db`, the
admin console and the landing that does **not** depend on the ASE.

A line says what is done, what is left, and what it is waiting on. Items marked
**You** need a decision, an account or a setting only the owner can give.

## 1. Closed in this stretch

| Area | What closed |
|---|---|
| Pinterest | Connect, boards, import, disconnect, images copied through the pipeline, admin view of connections and pins |
| Privacy | Export, deletion with a 14-day waiting period and session kill, restriction, the deletion ledger, admin ledger and accounts pages, purge worker |
| Media | Light detector (faces, text, safety), R2, Railway and S3 primaries, Cloudinary credentials by parts, upload mirrored to the backup, backup deleted on account deletion |
| Clean-up | Deleted vault items restorable 30 days then purged to a tombstone, abandoned uploads swept, orphaned pin images swept |
| Retention | `retention_ttl` enforces every period the gateway owns |
| Sharing | Share a look to FAUE by link or image, shares from FAUE counted, link opens counted |
| Notifications | Inbox, unread count, preferences (enforced at delivery), device tokens |
| Admin | Connected accounts, pins, privacy requests, accounts, uploads and storage, sharing, switches |
| Switches | Kill switches for the whole service, uploads, Pinterest, shares and waitlist sign-ups, each with a reason and an audit row |
| Waitlist | Invite the next 10, 25 or 50 oldest waiting members, and export to CSV with a reason |
| Deletion emails | One when a request is received (with the date it can be cancelled until), one when it completes |
| Clean-up of dead code | `AdminService` stub removed |
| Pinterest sync | Worker built: images copied a few at a time in the background, imported boards refreshed daily, deleted pins and boards removed, `needs_reauth` on a refused token |
| Audit log retention | `gateway.purge_audit_log()` removes rows past seven years and refuses any shorter period itself; the retention worker calls it |
| Push, SMS, WhatsApp | Firebase push, Termii SMS and WhatsApp Cloud channels, with phone verification (`/me/phone`); each skips with `not_configured` until its credentials are set |
| Detector golden set | 82 labelled images, an evaluation script and a test with floors; defaults retuned from the numbers (text 960 px, safety 0.7) |
| Lifecycle campaigns | D5, D7, D10, D14, D21, D30, D45, D60 and Detty December: policy in code (one a day, four a week, quiet hours in Lagos, backoff, hard stop, final message), seven new templates, an hourly worker that is **off until `lifecycle_enabled`**, a Campaigns page, and open tracking from inbox reads |
| Tunable settings | Thresholds, limits and clean-up periods editable from the console within safe bounds, with a reason and an audit row; secrets are not tunable |
| Cloudinary | A live upload was run end to end. It found that deletions had never worked (signed with the wrong parameters and ignored); fixed and verified |

## 2. Still open, and not waiting on the ASE

### Needs building

| # | Item | Why it matters | Size |
|---|---|---|---|
| 4 | **`notify_dispatch` and `link_cleanup`** (stubs) | `link_cleanup` is probably unnecessary (links expire in Redis); `notify_dispatch` is needed only for scheduled sends | Small once the first two are decided |
| 8 | **Contact "complaint" topic.** Undecided whether it is separate from support | Routing and the SLA differ | Decision (**You**), then small |
| 12 | **Share targets on the clients:** web share target manifest, iOS and Android share extension, WhatsApp inbound | Sharing to FAUE has an endpoint and no front door | The web-app work |
| 13 | **Image delivery check.** Presigned links expire after an hour; confirm a custom public domain for the bucket or accept re-fetching lists | Cached image URLs break in a client | Decision (**You**) |

### Needs your hands

| # | Item |
|---|---|
| A | Create the Pinterest developer app (Trial) and put the client id and secret in the environment; redeploy `landing/` so `/privacy#pinterest` is live first |
| B | Set `STORAGE_PROVIDER` and the Cloudinary and Railway variables on the API **and** on the `backup_replication`, `dsr_purge`, `retention_ttl` and `pinterest_sync` workers (verified working from this machine) |
| C | Run migrations `0011` to `0019`, tag and push `faue-db`, bump the pin |
| D | Confirm the backup bucket has no object lock or retention, so a deletion can actually remove objects |
| E | Revoke the bare `AQ.` key and the duplicate `OPENROUTER_API_KEY` line in `.env` |
| F | Confirm Resend SPF and DKIM for `faueofficial.com` |
| G | Install Playwright browsers and run the landing end-to-end suite |
| H | Free disk toward your 50% target (Timeshift snapshots, `~/Videos`) |
| I | Decide whether to keep the Intellign environments |

### Waiting on something else

| Item | Waiting on |
|---|---|
| Real Pinterest run with the Figma-screens board, then the OAuth demo video for Standard | A, plus Pinterest's approval |
| Instagram captions on shared links | `META_OEMBED_TOKEN` and, per Meta's docs, possibly App Review |
| Account-deletion acknowledgement from `ase` (`user.deletion.completed`) | The ASE side |
| Style library, review queue and model configuration pages | The ASE: the data lives there |
| The `web-app` (`staging.faueofficial.com`) | Not started; it consumes everything above |

## 3. Depends on the ASE (for when credits are back)

- `ase_client` and `media_client` (stubs), and the looks, fabric, spree and agent
  routes that sit on them (25 routes).
- Analysing a shared look (the share items are ready to be handed over).
- `look_ready` email trigger.
- Embedding imported pins into the aspiration vector, and the deletion
  acknowledgement above.

## 4. Suggested order

1. WhatsApp **inbound** (people sending a link or photo to FAUE's number), which
   needs the phone verification that now exists to know who is writing.
2. D1 and D3 campaign steps, once the looks data can be asked for (ASE).
3. A second labelling pass on the golden set with real uploads, once there are
   some, and a minors and non-apparel decision.
4. The small decisions (8, 13), whenever you have a minute.
