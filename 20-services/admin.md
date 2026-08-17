# Admin Console

**Stage:** MVP · **Repo:** `faueofficial/faue-admin` (Next.js) · **Backend:** `gateway.admin` at `/admin/v1/*`

Internal operations. Separate deployment, separate domain, separate auth realm, network-gated. It is also the largest PII exposure in the system, so it carries controls the user API does not.

**Design principle:** every new backend capability ships with its admin surface specified in the same pull request. Otherwise the console permanently lags the system and staff end up in `psql` — which is unauditable, unsafe, and the thing this exists to prevent.

---

## 1. Auth realm

Entirely separate from user auth: different issuer, different audience claim, shorter token lifetime, and a separate identity table (`admin_users`). A user token can never authenticate here, and an admin token can never authenticate against `/v1/*`.

| Control | Rule |
|---|---|
| MFA | **Mandatory for every account**, founders included |
| Session | 8 hours, absolute |
| Network gate | VPN, SSO, or IP allowlist in front of the whole application |
| Indexing | `noindex`, never publicly linked |

---

## 2. RBAC

Permissions are per-capability, not hardcoded per role, so adding a role is configuration rather than a rewrite.

| Role | Can |
|---|---|
| `viewer` | Read dashboards. No PII, no mutations |
| `curator` | Style library, catalogue content, reference images. **No user PII** |
| `support` | User lookup, masked PII, reveal with reason, trigger DSR, read-only impersonation |
| `ml_ops` | Model config, prompt versions, eval runs, kill switches, review queue |
| `admin` | Everything, plus role management and break-glass |

Least privilege by default. Oladunni needs `curator` and nothing else — content work requires no access to a single user's email.

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
