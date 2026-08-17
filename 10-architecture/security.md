# Security

**Stage:** MVP · **Companions:** [`threat-model.md`](threat-model.md), [`pii-handling.md`](pii-handling.md), [`prompt-injection.md`](prompt-injection.md)

---

## 0. Outstanding action

The `api-gateway` git remote contained a GitHub personal access token in its URL. **That token must still be treated as compromised.**

| Step | Status |
|---|---|
| Remote reset to a token-free URL | **Done** (2026-08-17, repo cleanup) |
| Verified the token was never committed to git history | **Done** — it existed only in local `.git/config` |
| Verified no token remains in any working tree | **Done** |
| **Revoke the token at github.com/settings/tokens** | **OUTSTANDING — owner action** |

Removing it from disk does not un-leak it: it was visible in a terminal session and may exist in shell history, backups, or scrollback. Revocation is the only control that actually closes it.

```bash
# verify the remote is clean
git -C api-gateway config --get remote.origin.url
# → https://github.com/faueofficial/api-gateway.git

# optional: switch to SSH once keys are set up
git -C api-gateway remote set-url origin git@github.com:faueofficial/api-gateway.git
```

Revocation is launch-blocking.

---

## 1. Secrets

- Never in a repository, never in a git remote URL, never in a log line.
- Local: `.env`, git-ignored, with `.env.example` documenting every variable.
- Deployed: platform secret store, injected as environment variables.
- Rotation: on schedule, and immediately on any suspicion.
- CI scans for secret patterns and fails the build on a hit.

| Secret | Rotation |
|---|---|
| `ENCRYPTION_MASTER_KEY` | Annually, or on suspicion |
| `BLIND_INDEX_PEPPER` | **Only with a maintenance window** — rotation invalidates every index |
| `JWT_PRIVATE_KEY` | Quarterly, overlapping |
| `SERVICE_JWT_SECRET` | Quarterly |
| Apple client secret | **Every 6 months — it expires** |
| Provider API keys | Annually, or on suspicion |

The Apple secret is the one that will bite: it is an ES256 JWT with a hard six-month maximum life, and expiry breaks every Apple sign-in simultaneously. Its expiry date is an alert, not a calendar note.

---

## 2. Authentication and sessions

Covered in [`../40-frontend/auth-flows.md`](../40-frontend/auth-flows.md). Security-relevant properties:

- No passwords exist, so none can leak.
- Magic-link tokens: 32 random bytes, stored hashed, single-use, 10-minute TTL, POST-only consumption, one active per identifier, atomic consumption via a Redis Lua script.
- Access tokens 15 minutes; refresh tokens rotate, with family revocation on reuse.
- OAuth tokens verified server-side against provider JWKS. Client-supplied profiles are never trusted.
- Account linking only on verified email match — unverified auto-linking is an account-takeover path.

---

## 3. Service-to-service

`ase`, and later `catalog` and `media`, are on a private network with **no public domain**. Calls carry a service JWT with a 5-minute life and an audience claim, so a user token can never work on an internal endpoint even if one ended up in the wrong header.

The gateway is the only service that makes synchronous calls to another service. Everything else is event-driven, which limits the reachable surface if any single service is compromised.

---

## 4. Rate limiting

At the edge, per IP, per user, and per endpoint class. Limits in [`../20-services/api-gateway/api.md`](../20-services/api-gateway/api.md).

Deliberately strict on: magic-link requests (email cost and enumeration), uploads (storage cost), and generation and spree (model spend). These are the endpoints where abuse costs real money rather than just capacity.

---

## 5. Upload safety

| Control | Purpose |
|---|---|
| 20 MB size cap | Resource exhaustion |
| MIME sniffing, not extension trust | Disguised payloads |
| Re-encode every image | Strips embedded payloads and polyglot files |
| Malware scan | Standard hygiene |
| Signed direct-to-CDN with short-lived credentials | The server never proxies bytes |
| Safety classification before persistence | Unacceptable content never lands on disk |

Re-encoding is the control that does the most work: it destroys embedded payloads, strips metadata, and normalises format in one step.

---

## 6. Application baseline

- Parameterised queries only; the ORM is used throughout and raw SQL is reviewed.
- Output escaping in web surfaces; strict CSP on `faue-web` and `faue-admin`.
- CORS allowlist per environment — never `*`.
- Security headers: HSTS, `X-Content-Type-Options`, `Referrer-Policy`, `Permissions-Policy`.
- Dependency scanning (`pip-audit`, Dependabot) and SAST in CI.
- All input validated by Pydantic at the boundary; unknown fields rejected on write paths.
- No user-controlled data in a URL that the server then fetches (SSRF); Pinterest image fetching uses an allowlist of Pinterest CDN hosts.

---

## 7. Database

- Role per service, granted only on its own schema. Cross-schema access fails at the database.
- `faue_migrator` owns DDL; service roles hold DML only and cannot alter tables.
- `audit_log` and `quiz_responses` have `UPDATE` and `DELETE` revoked from the service role.
- TLS required for all connections.
- No production database access from a laptop; admin operations go through the admin console, which audits them.

---

## 8. Admin

The largest PII exposure in the system, so it carries controls the user API does not:

- Separate auth realm, different issuer and audience.
- MFA mandatory for every staff account, founders included.
- RBAC with per-capability permissions rather than hardcoded roles.
- PII masked by default; revealing requires a stated reason and writes an audit entry.
- Immutable audit log of every PII read and every mutation.
- Break-glass elevation is time-boxed, auto-expiring, and alerts a second person.
- Network gate — VPN, SSO, or IP allowlist — in front of the whole application.
- Destructive actions require confirmation.

---

## 9. Backups

| Property | Value |
|---|---|
| Frequency | Nightly full, plus PITR |
| Retention | 30 days |
| Encryption | At rest, separate key from the application |
| Location | Different provider from the primary database |
| **Restore test** | **Quarterly, to a scratch environment** |
| Excluded | Vector tables — derived data, rebuildable from source images |

An untested backup is not a backup. The quarterly restore is the only thing that makes the rest of this row true, and it is the step most likely to be skipped.

Excluding vectors materially reduces backup size and restore time, and costs nothing because they can be recomputed.

---

## 10. Model providers

- Zero-data-retention, no-training allowlist, enforced per request rather than assumed from a contract.
- No PII reaches a provider — text redacted, images pipeline-processed, body data abstracted.
- Sub-processor list published.
- Read-only tool surface, so a compromised or manipulated model cannot act.

---

## 11. Practices

| Practice | Cadence |
|---|---|
| Dependency review | Weekly, automated |
| Secret scan | Every commit |
| SAST | Every pull request |
| Restore test | Quarterly |
| Access review — who has what | Quarterly |
| Threat model review | On architecture change |
| Red team on prompts and tools | Before any release touching them |
| Penetration test | Before public launch, then annually |

---

## 12. Known gaps at MVP

Named honestly rather than omitted:

- **No WAF.** Rate limiting and validation carry the load. Acceptable at launch volume, worth revisiting at scale.
- **No formal SOC.** One person on call. Alerting is the substitute.
- **No hardware token requirement** for admin MFA. TOTP is accepted.
- **Backups in one region.** Cross-region replication is an M1-2 item.
- **No bug bounty.** A security contact address is published instead.
