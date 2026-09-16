# Product Requirements

**Stage:** MVP · **Owner:** backend · **Updated:** 2026-08-22

The entry point to the product documentation. It states the problem, the users,
what the product must do, and how we will know whether it worked.

It does not duplicate the documents around it. Where a subject has its own
document, this one states the requirement and links to it — a requirement
restated in two places drifts in one of them.

| For | Read |
|---|---|
| Why this exists at all | [`vision.md`](vision.md) |
| Who it is for | [`personas.md`](personas.md) |
| What ships first and what does not | [`mvp-scope.md`](mvp-scope.md) |
| When the rest arrives | [`roadmap.md`](roadmap.md) |
| Thresholds and instrumentation | [`metrics.md`](metrics.md) |
| How the system is built | [`../10-architecture/hld.md`](../10-architecture/hld.md) |
| The API the app codes against | [`../30-contracts/openapi/gateway.v1.yaml`](../30-contracts/openapi/gateway.v1.yaml) |
| What is actually built so far | [`../90-meta/build-status.md`](../90-meta/build-status.md) |

---

## 1. The problem

Getting dressed well in Nigeria costs more time and money than it should.

**Ready-to-wear** discovery is scattered across brand Instagram pages with no way
to see how pieces combine. **Bespoke** has a worse gap: between "I bought fabric"
and "I know what to tell my tailor" sits Pinterest browsing, screenshots in
WhatsApp groups, and miscommunication that produces a garment nobody wears — at
₦30,000–80,000 a time, several times a year.

Neither path understands context: Owambe dress codes, Aso-Ebi coordination, the
switch between native and corporate registers, harmattan changing what fabric is
bearable, or the fact that a large-motif Ankara and a heavily seamed cut destroy
each other.

And underneath both: most people already own clothes they do not wear, because
they cannot see the combinations.

**The problem is not a shortage of inspiration. It is the absence of a decision.**

---

## 2. Users

| | Who | What they need |
|---|---|---|
| **Primary** | Amara, 28, Lagos — fashion-conscious professional, frequent events, buys fabric several times a year | A specific answer, fast, that respects the occasion |
| **Secondary** | Tunde, 32, Abuja — owns good clothes, does not combine them well | Confidence that what he owns already works |
| **Tertiary** | Chidinma, 23, Ibadan — style-curious, price-sensitive | To look expensive without spending |
| **Recipient, not user (MVP)** | The tailor | To receive a clear brief over WhatsApp without installing anything |

The tailor becomes a primary user in Y2; the stylist arrives with the
professional track. Both are designed for in
[`professional-strategy.md`](professional-strategy.md) and neither is built at
MVP. Detail and anti-personas: [`personas.md`](personas.md).

---

## 3. The core loop

```
Style DNA quiz  →  Vault (own clothes) and/or fabric upload
                →  Generate a look (occasion · mood · weather · note)
                →  See it, with reasoning: "Why this works for you"
                →  Save · Share · Send to tailor
                →  Come back
```

Every requirement below serves that loop. A request that does not is a roadmap
item, not a scope change.

---

## 4. Functional requirements

Numbered so a test, a screen, and a contract can all cite the same requirement.
`MUST` is launch-blocking; `SHOULD` ships if it does not delay launch.

### 4.1 Access

| # | Requirement |
|---|---|
| FR-1 | A user MUST be able to sign in with a magic link, Google, or Apple. No passwords exist anywhere in the system |
| FR-2 | A magic link MUST NOT be consumable by a `GET`. Mail scanners fetch every URL in a message before the recipient sees it, so a `GET` that signed the user in would spend the login before it was tapped |
| FR-3 | Opening the link on a different device from the one that requested it MUST complete the sign-in on the requesting device, via a 6-digit code |
| FR-4 | Two providers MUST link to one account only when both sides present the **same verified** email. An unverified match is an account-takeover path and MUST NOT link |
| FR-5 | Presenting an already-rotated refresh token MUST revoke the whole token family. Logout MUST NOT be indistinguishable from theft in the audit trail |
| FR-6 | The app MUST be able to delete the account from inside the app. Offering Sign in with Apple obliges this |

Detail: [`../40-frontend/auth-flows.md`](../40-frontend/auth-flows.md).

### 4.2 Knowing the user

| # | Requirement |
|---|---|
| FR-7 | A 6-question quiz MUST produce a Style DNA: a dominant persona from a closed set of six, with percentage weights over all six |
| FR-8 | Scoring MUST be deterministic and pure — the same answers always give the same result, with no model involved |
| FR-9 | The result MUST render as a shareable card. This is the acquisition loop, not a decoration |
| FR-10 | A user MUST be able to record a body profile — shape, height, fit preference, sizes — and every field MUST be independently omittable |
| FR-11 | The body profile MUST NOT leave the gateway as measurements. `ase` receives derived silhouette constraints (`favor: defined_waist`), never a number and never a shape name |
| FR-12 | A user SHOULD be able to connect Pinterest so that aspiration signal exists before the vault is populated |

Detail: [`style-dna.md`](style-dna.md).

### 4.3 The wardrobe

| # | Requirement |
|---|---|
| FR-13 | A user MUST be able to photograph, categorise, edit, search, and delete items in a vault |
| FR-14 | Every uploaded image MUST be re-encoded before persistence — this strips EXIF, embedded payloads, and polyglot files in one step |
| FR-15 | Faces MUST be detected and redacted before an image reaches any model or any other service |
| FR-16 | A user MUST be able to log that an item was worn. The wear log is what makes the north-star metric measurable |

### 4.4 The answer

| # | Requirement |
|---|---|
| FR-17 | A user MUST be able to generate a look from occasion, mood, weather, and a free-text note |
| FR-18 | Rules MUST define the legal pool of items and validate what comes back. The model selects, assembles, ranks, and explains **within** that pool. A generated look MUST NOT contain an item the user does not own or that the rules excluded |
| FR-19 | Every look MUST carry a "Why this works for you" explanation. A look without a reason is a guess |
| FR-20 | Weather MUST come from the device's location, and only with `location_weather` consent granted |
| FR-21 | A user MUST be able to upload fabric and receive native style suggestions, and MUST be able to send one to a tailor over WhatsApp |
| FR-22 | A user MUST be able to save, share, and regenerate a look |
| FR-23 | Spree — conversational styling — MUST answer only about pieces the user owns, and MUST refuse anything outside that scope |
| FR-24 | When generation is unavailable, every other surface MUST keep working. The vault, saves, and profile MUST NOT depend on `ase` |

Detail: [`../10-architecture/model-plane.md`](../10-architecture/model-plane.md),
[`../60-ai/guardrails.md`](../60-ai/guardrails.md).

### 4.5 Coming back

| # | Requirement |
|---|---|
| FR-25 | The agent MUST offer a suggestion on dashboard open (L0). Push and proactive triggers are M1-2 |
| FR-26 | Notifications MUST respect consent, quiet hours, and a frequency cap, and every send MUST be suppressible without losing the inbox copy |
| FR-27 | A user MUST be able to unsubscribe from every marketing message, from the message itself, without signing in |

Detail: [`retention-system.md`](retention-system.md).

### 4.6 Privacy, as product behaviour

Legal obligations that are also user-visible behaviour, so they are requirements
rather than a compliance appendix.

| # | Requirement |
|---|---|
| FR-28 | Every consent purpose MUST be denied by default. Nothing is granted implicitly by signing up except what the service cannot function without, and that grant MUST be **recorded**, not assumed |
| FR-29 | Revocation MUST take effect immediately and MUST destroy the data derived under that purpose. A flag flipped to false with the data intact is opt-out on paper and profiling in practice |
| FR-30 | A user MUST be able to export their data and delete their account, and deletion MUST complete within 30 days across every module |
| FR-31 | No PII MUST appear in an event payload, a log line, or a model prompt |
| FR-32 | Every free-text input reaching a model MUST pass prompt-injection guardrails, and a guardrail MUST NOT be loosened to clear an alert |

Detail: [`../10-architecture/privacy.md`](../10-architecture/privacy.md),
[`../10-architecture/pii-handling.md`](../10-architecture/pii-handling.md),
[`../10-architecture/prompt-injection.md`](../10-architecture/prompt-injection.md).

### 4.7 Operating it

| # | Requirement |
|---|---|
| FR-33 | An admin MUST be able to curate the style library, work review queues, handle support, and throw kill switches — without a `psql` session |
| FR-34 | Every AI-costing feature MUST have a kill switch that degrades the product rather than breaking it |

Detail: [`../20-services/admin.md`](../20-services/admin.md).

---

## 5. Non-functional requirements

| # | Requirement | Source |
|---|---|---|
| NFR-1 | Look generation p95 under 45 seconds | [`metrics.md`](metrics.md) |
| NFR-2 | Generation failure rate under 5% | [`metrics.md`](metrics.md) |
| NFR-3 | Read endpoints p95 under 200 ms; quiz submission under 400 ms | [`metrics.md`](metrics.md) |
| NFR-3a | Fabric analysis p95 under 15 s; Spree first token under 2 s; app cold start under 2.5 s | [`metrics.md`](metrics.md) |
| NFR-4 | Total infrastructure and model spend under $150/month at MVP scale | [`../70-ops/environments.md`](../70-ops/environments.md) |
| NFR-5 | Uploads capped at 20 MB, MIME sniffed rather than extension-trusted | [`../10-architecture/security.md`](../10-architecture/security.md) |
| NFR-6 | Access tokens live 15 minutes; refresh tokens 30 days and rotate on every use | [`../40-frontend/auth-flows.md`](../40-frontend/auth-flows.md) |
| NFR-7 | Rate limits per IP, per user, and per endpoint class, enforced at the edge | [`../20-services/api-gateway/api.md`](../20-services/api-gateway/api.md) §2 |
| NFR-8 | Sensitive columns encrypted at rest with per-value data keys; equality lookups via blind index | [`../10-architecture/security.md`](../10-architecture/security.md) |
| NFR-9 | `ase` has no public ingress and never receives direct identifiers | [`../10-architecture/hld.md`](../10-architecture/hld.md) |
| NFR-10 | Every state change published through the outbox, in the same transaction | [`../10-architecture/event-catalog.md`](../10-architecture/event-catalog.md) |
| NFR-11 | The app MUST tolerate unknown fields and unknown enum values — a client that crashes on a new occasion type blocks every future release | [`../20-services/api-gateway/api.md`](../20-services/api-gateway/api.md) |

---

## 6. What success looks like

**North star: weekly looks worn.** Not generated, not sessions, not signups — the
only metric that cannot be inflated by a good demo or a push notification. Until
the wear-log rate is healthy, **looks saved** is the working proxy.

Launch-blocking thresholds:

| Metric | Threshold |
|---|---|
| Quiz completion | ≥ 60% of starts |
| Look generated in first session | ≥ 70% of quiz completions |
| Look save rate | ≥ 25% of generated looks |
| 14-day return, unprompted | ≥ 20% |
| DNA card share | ≥ 10% of completions |
| Tailor share | ≥ 15% of fabric uploads |

Full funnel and instrumentation: [`metrics.md`](metrics.md).

### What would tell us we are wrong

Stated in advance, so the result is not reinterpreted afterwards.

- **Quiz abandonment above 40%** — the cold-start price is too high for the value promised.
- **Looks generated once and never saved** — recommendations are not good enough. This is the failure that matters most, because everything else is downstream of it.
- **Zero tailor shares** — the bespoke loop, the strongest differentiator, is not a real workflow.
- **No unprompted returns** — the problem is not painful enough, or the product does not solve it.

Any of these means fixing the loop, not adding to it.

---

## 7. Constraints already decided

Recorded so they are not relitigated in a planning meeting. Full reasoning in
[`../80-adr/`](../80-adr/).

| Constraint | Where |
|---|---|
| Two services at MVP: `api-gateway` (public, holds all PII) and `ase` (internal, no direct identifiers) | [0001](../80-adr/0001-two-services-gateway-and-ase.md) |
| `spree` folded into `ase`, `notify` folded into `api-gateway`, both with extraction seams | [0002](../80-adr/0002-spree-and-notify-as-modules.md) |
| Rules define the legal pool; the model works inside it | [0008](../80-adr/0008-closed-set-model-policy.md) |
| The model assembles rather than a rules engine deciding combinations | [0017](../80-adr/0017-model-led-assembly.md) |
| Generative rendering is the default; `composite` is the cost lever | [0018](../80-adr/0018-generative-rendering-default.md) |
| Consent denied by default for every purpose | [0012](../80-adr/0012-consent-denied-by-default.md) |
| Image PII handling is server-authoritative, never trusted to the client | [0013](../80-adr/0013-server-authoritative-image-pii-pipeline.md) |
| Six-question Style DNA | [0011](../80-adr/0011-six-question-style-dna.md) |
| Magic-link authentication, no passwords | [0016](../80-adr/0016-magic-link-authentication.md) |
| Style library licensed or generated, never scraped | [0020](../80-adr/0020-style-library-licensed-not-scraped.md) |
| Instagram integration removed — the platform API cannot return saved posts | [0019](../80-adr/0019-remove-instagram-integration.md) |
| Catalog and affiliate deferred past MVP | [0010](../80-adr/0010-defer-catalog-and-affiliate.md) |
| `workspace_id` on every user-owned table from day one, single-tenant in behaviour | [0021](../80-adr/0021-workspace-tenancy-model.md) |
| Canonical domain `faueofficial.com`; `ase` retained as the service name | [0022](../80-adr/0022-canonical-domain-and-service-naming.md) |

---

## 8. Deliberately unsolved at MVP

Named so nobody thinks they were forgotten. Reasoning in
[`mvp-scope.md`](mvp-scope.md) §5.

Cold start with an empty vault · style library depth · reference image
consistency · Nigerian sizing · multi-user households.

---

## 9. Open questions

Tracked in [`../90-meta/doc-status.md`](../90-meta/doc-status.md); repeated here
because they are product decisions, not documentation gaps.

| # | Question | Blocks |
|---|---|---|
| 1 | Persona taxonomy and quiz option copy need sign-off | Quiz implementation, share-card design |
| 2 | Generative image provider — cost, latency, African fashion fidelity, commercial terms | Renderer |
| 3 | Style library licensing — which tailors, who owns the conversation | Library content |
| 6 | Tailor segment reachability — validate with 5 tailors before building anything | Professional track |
| 7 | Delegated consent design (client → stylist, partial and revocable) | Professional track |
| 8 | VTO consent purpose and its guardrail exception | Virtual try-on |

---

## 10. Change log

Scope changes are recorded here with the date and the reasoning, so drift is
visible rather than remembered differently by each person.

| Date | Change |
|---|---|
| 2026-08-22 | Document created, consolidating requirements that were spread across `vision.md`, `mvp-scope.md`, and `metrics.md`. No scope change |
