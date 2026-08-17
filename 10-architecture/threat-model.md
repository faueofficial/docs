# Threat Model

**Stage:** MVP · **Method:** STRIDE per trust boundary · **Reviewed:** 2026-08-17

Review triggers: any new trust boundary, any new third party, any tool that mutates state, or any real incident.

---

## Assets, ranked by what a breach would cost

| Asset | Why it matters |
|---|---|
| User photographs | Faces, homes, possessions. The most personally exposing data FAUE holds |
| Body profile | Sensitive category under GDPR; deeply personal |
| Email and phone | Identity, account recovery, spam exposure |
| OAuth tokens | Access to a user's Pinterest account |
| Session tokens | Account takeover |
| Style library | The core content asset; expensive to rebuild |
| Model API keys | Direct financial loss |
| Admin access | Everything above, for everyone |

---

## Boundary 1 — Client → gateway

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **S** | Forged token | Signed JWTs, JWKS verification, short lifetimes | Low |
| **S** | Account enumeration via magic-link responses | Always `202` regardless of whether the address exists | Low |
| **S** | Magic-link interception in email | 10-min TTL, single-use, POST-only, device binding | **Medium** — email compromise defeats it, as with all magic links |
| **T** | Client-supplied OAuth profile forged | Server-side verification only | Low |
| **T** | Body constraints tampered to alter results | Constraints derived server-side, never client-supplied | Low |
| **R** | User denies an action | Action events with trace ids | Low |
| **I** | Enumerating other users' looks | Share ids are separate, unguessable, revocable | Low |
| **I** | Response leaks another user's data | Repository queries always scoped by `user_id`; contract tests assert it | Low |
| **D** | Request flood | Rate limits per IP, user, and endpoint class | Medium |
| **D** | **Generation abuse burning model budget** | Per-user daily caps, token budgets, kill switches | Medium |
| **E** | User token used on admin endpoints | Separate realm, audience claim | Low |

The magic-link residual is inherent: anyone with the user's mailbox can sign in. That is true of every passwordless system and of every password-reset flow, so it is accepted rather than solved.

---

## Boundary 2 — Gateway → ase

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **S** | Forged service token | Audience-scoped JWT, 5-minute life | Low |
| **S** | `ase` reached directly from the internet | Private network, no public domain | Low |
| **T** | `X-User-Id` spoofed | Only the gateway can call; gateway authenticates the user | Low |
| **I** | `ase` compromise exposes PII | **`ase` holds no direct identifiers** — no email, no phone, no measurements | Low |
| **D** | Slow model calls exhaust gateway connections | Timeouts, circuit breakers, degraded paths | Low |
| **E** | `ase` reads `gateway` data | Postgres role has no grant on the `gateway` schema | Low |

The containment here is deliberate and is the single most valuable structural decision in the model: compromising the service that talks to model providers yields vectors and looks, not identities.

---

## Boundary 3 — ase → model providers

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **T** | **Prompt injection via user or imported content** | Trust tiers, delimiting, read-only tools, output validation, ingest screening | **Medium** — see [`prompt-injection.md`](prompt-injection.md) |
| **I** | PII sent to a provider | Text redaction, image pipeline, abstracted body data | Low |
| **I** | Provider retains or trains on data | Zero-retention allowlist enforced per request | **Medium** — contractual, not technical |
| **I** | Model output leaks another user's data | Tools are session-scoped; nothing cross-user is reachable | Low |
| **D** | Provider outage | Tier fallback, circuit breakers, template paths | Low |
| **D** | Runaway cost | Budgets, caps, kill switches, `ai.budget.exceeded` | Medium |
| **E** | Injected model performs an action | **No tool mutates state, sends, or spends** | Low |

The provider-retention residual is the honest one: FAUE can enforce an allowlist and check policies, but cannot technically verify what a provider does with a prompt after receiving it. Redaction before egress is the compensating control — a provider that misbehaves receives nothing identifying.

---

## Boundary 4 — Pinterest → ingest

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **T** | Malicious content in pin captions | Ingest injection screening, delimited as untrusted | Medium |
| **T** | Malicious image payloads | Re-encode, safety classification, PII pipeline | Low |
| **I** | Over-broad OAuth scopes | Read-only scopes; user selects which boards | Low |
| **I** | Token theft yields Pinterest access | Encrypted at rest, read-only scopes, revocable | Medium |
| **D** | Import flood | Rate limits, cursor-based incremental sync | Low |
| **E** | SSRF via pin image URLs | Allowlist of Pinterest CDN hosts | Low |

The SSRF vector is worth naming explicitly: fetching an arbitrary URL supplied by a third-party API is exactly how internal services get scanned. The host allowlist is not optional.

---

## Boundary 5 — Staff → admin

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **S** | Staff credential theft | MFA mandatory, network gate | Low |
| **T** | Unauthorised data modification | RBAC, audit log, confirmations | Low |
| **R** | Staff denies an action | Immutable audit log with actor, IP, justification | Low |
| **I** | **Staff browsing user PII casually** | Masked by default, reveal requires a reason and is audited | **Medium** — this is the realistic insider risk |
| **I** | Impersonation misused | Read-only, consent-required, fully audited | Medium |
| **D** | Accidental destructive action | Confirmations, no bulk delete without break-glass | Low |
| **E** | Privilege escalation | Per-capability permissions, time-boxed break-glass with second-person alert | Low |

At a two-person team the insider risk is low in practice and high in principle. The controls exist because the team will grow, and retrofitting audit logging onto an admin console that never had it is far harder than building it in.

---

## Boundary 6 — Supply chain

| STRIDE | Threat | Mitigation | Residual |
|---|---|---|---|
| **T** | Malicious dependency | Pinned versions, lock files, Dependabot, `pip-audit` | Medium |
| **T** | Compromised base image | Pinned digests, minimal images, regular rebuilds | Medium |
| **E** | Compromised CI | Least-privilege tokens, no secrets in logs, protected branches | Medium |
| **I** | **Leaked credential in a repository** | Secret scanning in CI, pre-commit hooks | **HIGH — see §0 of [`security.md`](security.md)** |

The high residual here is not theoretical. A live PAT is currently embedded in a git remote URL, and it must be revoked.

---

## Attack scenarios worth walking through

**A stolen phone with an unlocked app.** Session tokens are in the OS keychain, so an unlocked device yields full account access. Mitigation: 15-minute access tokens limit an extracted token; remote logout revokes the family. Accepted — no app solves an unlocked device.

**A user uploads a photo containing someone else's face.** Realistic, since people photograph clothes on other people. The pipeline redacts every detected face regardless of whose it is, which is why redaction is unconditional rather than "the user's own face".

**An attacker imports a Pinterest board full of injected captions.** Screened at ingest, delimited as untrusted, and even a successful injection reaches only read-only tools. The output is then validated against the legal pool.

**A model provider silently changes a model behind a stable identifier.** Detected by the weekly canary run against a fixed prompt set; mitigated by the tier fallback and by pinning specific model versions where the provider supports it.

**Generation abuse from a scripted account.** Per-user daily budget, then the template path. Cost is capped before it becomes material, and `ai.budget.exceeded` fires.

---

## Prioritised remediation

| Priority | Item | Owner |
|---|---|---|
| **1** | Revoke the leaked PAT and reset the remote | Backend, immediately |
| 2 | Consent surfaces for `ai_processing`, `location_weather`, `pinterest_sync` | Design + backend, launch-blocking |
| 3 | Account deletion screen | Design + backend, launch-blocking (App Store) |
| 4 | Secret scanning in CI | Backend |
| 5 | Restore test executed at least once | Backend |
| 6 | Penetration test before public launch | External |
| 7 | Cross-region backup replication | M1-2 |
