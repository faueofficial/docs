# Admin Console

**Stage:** MVP · **Repo:** `faueofficial/faue-admin` (Next.js) · **Backend:** `gateway.admin` at `/admin/v1/*`

Internal operations. Separate deployment, separate domain, separate auth realm, network-gated. It is also the largest PII exposure in the system, so it carries controls the user API does not.

**Design principle:** every new backend capability ships with its admin surface specified in the same pull request. Otherwise the console permanently lags the system and staff end up in `psql` — which is unauditable, unsafe, and the thing this exists to prevent.

---

## 1. Auth realm

Entirely separate from user auth: different issuer, different audience claim, shorter token lifetime, and a separate identity table (`admin_users`). A user token can never authenticate here, and an admin token can never authenticate against `/v1/*`.

| Control | Rule |
|---|---|
| First factor | Magic link to the account's address |
| Second factor | TOTP (RFC 6238), **mandatory for every account**, founders included |
| Session | 8 hours, absolute — never sliding |
| Network gate | VPN, SSO, or IP allowlist in front of the whole application |
| Indexing | `noindex`, never publicly linked |

### The flow

```
POST /admin/v1/auth/link/request  { email }
  → 202 always, whatever the address

POST /admin/v1/auth/link/consume  { token, code }
  → 200 { access_token, expires_in: 28800, role }
  → 403 wrong or replayed code — the link is NOT spent
  → 428 not enrolled, with an enrolment_token in the body
```

**Why two factors from different places.** The link arrives by email, so on its
own a compromised inbox is admin access to everyone's PII. TOTP requires the
physical device holding the secret. Chosen over SMS deliberately: SIM swaps are
common in the launch market, and SMS costs money per message.

**The 202 never varies.** Which addresses hold admin accounts is precisely the
list an attacker wants before choosing who to phish.

**A wrong code does not spend the link.** Both factors are checked before
anything is consumed — otherwise a mistyped code forces a fresh email every
attempt, and people learn to hate the flow.

**Codes cannot be replayed.** A TOTP code is valid for its window plus one step
of drift allowance, roughly 90 seconds. Used codes are held in Redis for that
span, claimed with `SET NX` so two requests racing with the same observed code
cannot both succeed.

**Drift allowance is one step, and is not a dial.** Phone clocks skew, and a
strictly-current check locks people out for a reason they cannot diagnose.
Wider than one step materially weakens the factor.

### Enrolment, and the bootstrap

A new admin is not enrolled, so they cannot hold a session — but enrolment has
to be authorised by something. Consuming a link on an unenrolled account returns
`428` with a short-lived **enrolment token**: clicking the link proved control of
the inbox, which is enough to *begin* enrolment and nowhere near enough to read
anyone's data.

```
POST /admin/v1/auth/mfa/enrol    { enrolment_token }  → 200 { secret, provisioning_uri }
POST /admin/v1/auth/mfa/confirm  { enrolment_token, code }  → 204
```

`mfa_enrolled` flips on **confirmation**, not on issuing the secret. A stored
secret only proves one was generated; if the operator never successfully scanned
it, treating them as enrolled locks them out permanently.

The provisioning URI contains the secret. Shown once, never logged, never
re-displayed — and an enrolled account cannot re-enrol itself, because a live
session could otherwise replace the second factor with one an attacker controls
and survive the account being locked. Replacement is an `admin`-role action
against another account.

The TOTP secret is encrypted at rest: whoever holds it can mint valid second
factors, which makes it exactly as sensitive as the account.

### Invitations

Accounts are created by invitation, not by hand. Inviting is a `role.write`
action — granting someone a role is effectively granting them everything that
role can reach — so only `admin` may do it.

```
POST /admin/v1/admins/invite        { email, role }   → 201   (admin only)
POST /admin/v1/auth/invite/accept   { invite_token }  → 200 { enrolment_token }
  → then the same enrol / confirm pair as any other enrolment
```

An invited account has `status = 'invited'` and **cannot sign in**. Enrolment is
what activates it. That separation is the point: an invite that produced a
usable account would make a forwarded email an admin account.

Invites expire in three days — long enough to survive a weekend, short enough
that a stale invite is not a standing path to an account — and are single-use,
so a forwarded mail is spent rather than live.

Re-inviting an existing address is refused rather than silently duplicating the
account or quietly changing someone's role.

### Sessions

```
GET    /admin/v1/auth/sessions        → 200   every live session, newest first
DELETE /admin/v1/auth/sessions/{jti}  → 204   ends one — the laptop at the office
POST   /admin/v1/auth/logout          → 204   ends the session in your hand
POST   /admin/v1/auth/sessions/revoke → 204   ends every session the account holds
```

Sessions were deliberately unstored until listing was needed — a JWT requires no
server state, so there was nothing to leak and nothing to prune. Listing changes
that, which makes *what* is stored a decision rather than an accident.

Each row carries when it began, when it ends, roughly where from, and a coarse
device label (`Chrome on macOS`). That is what answers "is one of these not
me?". The **raw user-agent is never stored** — a full agent string is a
fingerprint and buys nothing beyond that question.

`current: true` marks the session making the call. Without it the list is
unusable: you cannot tell which row is the device in your hand, and ending the
wrong one signs you out.

Ownership is structural rather than a check that can be forgotten — the storage
key is namespaced by account, so another account's session id simply is not
there and returns `404`. Ending an unknown session is a `404` too: an operator
clicking "end session" on a stale screen should learn it is already gone rather
than be told it worked.

Storage is a sorted set per account plus one key per session, so listing is
`O(log n)` rather than a `SCAN` across the keyspace. Expired entries are pruned
on read and each session key carries its own TTL, so a dead session disappears
even if the list is never opened again.

#### The two blunt levers

Logout is scoped to the session's `jti`: signing out of a laptop must not sign
you out of a phone, or people stop signing out at all. Revocation is a timestamp
cutoff rather than a list, because sessions cannot be enumerated and the point
of the lever is reaching the ones nobody knows about — a lost device, a
departure.

Revocation is a cutoff, not a ban. Signing in again afterwards works; a
permanent block is `status = 'suspended'`, which is a different decision.

**The cutoff rounds up to the next whole second.** JWT `iat` is integer seconds,
so a token issued at `12:00:00.9` records `12:00:00`; comparing that against a
fractional cutoff would let a session created *before* the revocation outlive
it. The cost is that a re-login inside that same second is also caught and needs
one retry — the right side to err on here.

**Verification fails closed if Redis is unreachable.** If the deny-list cannot
be read, a revoked session cannot be recognised, and on this surface "we cannot
tell whether this was revoked" has to mean no. It makes Redis a hard dependency
for admin auth: an outage locks the console rather than honouring sessions
somebody has already ended.

**Codes are single-use, and that is visible as friction.** Signing in on a
second device inside the same 30-second window is a replay and is refused — a
real person waits for the code to roll over. Worth knowing before someone
reports it as a bug.

---

## 2. RBAC

Permissions are per-capability, not hardcoded per role, so adding a role is configuration rather than a rewrite.

| Role | Can |
|---|---|
| `viewer` | Read dashboards, health and queue state. No PII, no mutations |
| `curator` | Style library, catalogue content, reference images. **No user PII** |
| `support` | User lookup, masked PII, reveal with reason, trigger DSR, read-only impersonation |
| `ml_ops` | Model config, prompt versions, eval runs, kill switches, review queue |
| `admin` | Everything, plus role management and break-glass |

Least privilege by default. Oladunni needs `curator` and nothing else — content work requires no access to a single user's email.

Capabilities are finer-grained than the role table suggests. `ops.read` covers
health and the embedded dashboards; `ops.read_queues` covers the event backlog
and delivery breakdowns. A curator holds the first and not the second: knowing
the system is up is reasonable for anyone working in the console, and the outbox
backlog is not their concern.

A route declares the capability it needs as a dependency, so a route that needs
one cannot forget to check it — the same reasoning as consent on the user API.
An unknown capability name denies rather than grants, so a typo fails closed.

---

## 3. Surfaces

### MVP

**Observability** — the six Grafana dashboards from [`../70-ops/observability.md`](../70-ops/observability.md), embedded rather than a second tool to log into.

**Style library** *(curator)* — the 30 native styles: create, edit, tag fabric suitability, occasion, formality, body notes. Manage reference images with provenance fields (`source`, `license_type`, `attribution`, `model_release`, `stylist_approved_by`). Generated references cannot reach `active` without stylist approval.

This is Oladunni's daily tool. Without it, curation happens in a spreadsheet and drifts from the database within a week.

**AI review queue** *(ml_ops)* — flagged sessions, low-rated outputs, and a random sample. Reviewers mark each correct refusal, false positive, or missed detection. Verdicts feed the golden sets, which is what keeps evaluation attached to reality.

**User support** *(support)* — lookup by id, email, or phone; view state (DNA, profile, vault count, generations, consents); trigger export or deletion; read-only impersonation with consent and full audit.

**Flags and kill switches** *(ml_ops, admin)* — per-task AI kill switches, renderer selection, budget caps, feature flags, maintenance mode. Runtime values in Redis, so an incident does not wait for CI.

**Deletion ledger** *(admin)* — open requests, modules pending, SLA countdown, manual acknowledgement with a recorded reason.

### M1-2

Experiments (config, exposure, guardrail metrics, halt button) · notification composer with template preview and segment targeting · model configuration with tier ordering and eval history · shadow-mode comparison views · catalogue operations including dead-link queue and re-embed triggers · curation intelligence showing which personas get thin results.

### M3+

Brand and partner administration · commerce operations, affiliate ledger, payouts, subscriptions · moderation at scale with appeals · tailor network vetting and quality tracking.

---

## 4. PII controls

The realistic insider risk is not theft — it is casual browsing. These controls address that specifically.

| Control | Behaviour |
|---|---|
| **Masked by default** | Email shows as `t•••@•••.com`, phone as `+234•••••1234`, measurements hidden entirely |
| **Reveal requires a reason** | A free-text justification, minimum 10 characters, written to the audit log |
| **Body profile** | Never revealable in admin. There is no legitimate support reason to see someone's measurements |
| **Impersonation** | Read-only, requires user consent recorded on a ticket, time-boxed to 30 minutes, fully audited |
| **Bulk export** | Requires `admin` plus break-glass |
| **Image viewing** | Redacted derivatives only; originals are not accessible |

Body profile being permanently unrevealable is a deliberate choice: making it technically impossible removes the judgement call entirely.

---

## 5. Audit log

Every PII read and every mutation:

```sql
gateway.audit_log (actor_id, actor_role, action, target_type, target_id,
                   before, after, justification, ip, occurred_at)
```

Append-only at the role level — the service role holds `INSERT` and `SELECT`, never `UPDATE` or `DELETE`. Retention seven years, separate from every other table.

This is the artefact that demonstrates access accountability to a regulator. It survives user deletion, because deleting the record of who accessed someone's data would defeat its purpose.

Audited actions include: PII reveal, impersonation start and end, user data export, deletion trigger, ledger acknowledgement, style library changes, flag and kill-switch changes, model configuration changes, role changes, and break-glass elevation.

---

## 6. Break-glass

For access beyond a role's normal permissions:

```
request → state a reason → elevated for 30 minutes → auto-expires
        → a second person is alerted immediately
        → every action during the window is audited and marked elevated
```

Auto-expiry matters: standing elevated access becomes normal access within a month, and nobody notices it happened.

---

## 7. Destructive actions

| Action | Requires |
|---|---|
| Delete a user | Typed confirmation of the user id, plus a reason |
| Purge catalogue | `admin` plus break-glass |
| Retire a style | Confirmation; blocked if referenced by active looks |
| Flip a kill switch | Confirmation showing the user-facing impact |
| Maintenance mode | Confirmation plus an estimated duration |

Confirmations show what will happen in user terms, not database terms. "This will stop generation for all users" is a better prompt than "set looks_generation_enabled = false".

---

## 8. What admin is not

- **Not a database client.** If something needs raw SQL, it needs an admin feature. `psql` on production is unaudited and is what this console exists to replace.
- **Not a public surface.** It is never linked from the app, never indexed, always network-gated.
- **Not a place to bypass consent.** Staff cannot grant consent on a user's behalf or read data a user has restricted.
- **Not a content editor for user data.** Support can correct a typo in a display name; it cannot rewrite someone's quiz answers or wear log.

---

## 9. Build order

| Priority | Surface | Why |
|---|---|---|
| 1 | Auth, RBAC, audit log | Nothing else can be built safely first |
| 2 | Style library | Blocks content work, which is on the critical path |
| 3 | Flags and kill switches | Needed the first time production misbehaves |
| 4 | Embedded dashboards | Needed to know production is misbehaving |
| 5 | User support | Needed from the first user complaint |
| 6 | Review queue | Needed once spree is live |
| 7 | Deletion ledger | Needed before launch — legal obligation |

The audit log comes first for a reason: retrofitting it onto a console that already has PII access means a period of unaudited access that can never be reconstructed.
