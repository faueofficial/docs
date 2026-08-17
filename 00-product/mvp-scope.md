# MVP Scope

**Stage:** MVP · **Supersedes:** the scope sections of `faue.md` where they conflict

What ships first, what does not, and why. If a request is not on the "in" list, it is not in the MVP — say so and put it on the roadmap.

---

## 1. The core loop

```
Style DNA quiz  →  Vault (own clothes) and/or fabric upload
                →  Generate a look (occasion · mood · weather · note)
                →  See it, with reasoning: "Why this works for you"
                →  Save · Share · Send to tailor
                →  Come back
```

Everything in scope serves that loop. Everything else waits.

**The hypothesis being tested:** if FAUE generates looks that are personal, culturally right, and immediately usable — from clothes a user already owns or fabric they already bought — they will act on them and return.

---

## 2. In scope

| Capability | Why it is in |
|---|---|
| **Style DNA quiz** (6 questions) | Solves cold start, produces the personalisation vector, and generates the shareable card that drives acquisition |
| **Magic-link auth + Google + Apple** | Lowest-friction way in; no passwords to leak or reset |
| **Vault** — photograph, categorise, edit, delete, search | The clothes a user owns are the raw material for every generated look |
| **Look generation** with occasion, mood, weather, and notes | The product |
| **"Why this works for you"** | Turns a picture into advice; this is what makes it FAUE rather than a mood board |
| **Fabric analysis → native style suggestions** | The strongest differentiator; nobody else answers "I bought this fabric, what do I sew?" |
| **Send to tailor** | Completes the fabric loop into something actionable |
| **Saved looks** | Retention surface and the reason to return |
| **Sharing** — DNA card, looks | The growth loop |
| **Pinterest import** | Aspiration signal; makes recommendations better from day one |
| **Agent L0** — suggestion on open | "What are you wearing today?" on the dashboard |
| **Spree** — conversational styling with guardrails | The Style Studio surface; answers questions about pieces the user owns |
| **Body profile** | Silhouette constraints; materially improves recommendation quality |
| **Notifications + inbox** | Retention, plus job-completion messages |
| **Consent, privacy, account deletion** | Legal obligation, and an App Store requirement given Sign in with Apple |
| **Landing page + public share pages** | Where shared links land for people without the app |
| **Admin console** | Curation, support, review queues, kill switches — without it, operations happen in `psql` |

---

## 3. Out of scope, with the stage it returns

| Deferred | Returns | Why not now |
|---|---|---|
| Cross-brand product catalog | M1-2 | Weeks of curation that would gate launch; no screen in the design shows a brand or price |
| Affiliate "Shop This" links | M1-2 | Tests monetisation, which is the wrong question before retention is proven |
| Brand dashboard and partnerships | M3+ | Requires traffic data FAUE does not have yet; two-sided cold start |
| Subscriptions and payments | M3+ | Pricing gates suppress the engagement signal needed to validate |
| Virtual try-on | M1-2 | Impressive, but does not test whether recommendations drive action |
| Agent L1–L3 (push, proactive, planning) | M1-2 / M3+ | Needs wear-log data that only exists after launch |
| Instagram integration | Never as specified | The platform API cannot return saved posts; see [ADR 0019](../80-adr/0019-remove-instagram-integration.md) |
| Aso-Ebi group coordination | M3+ | Strong idea, needs a working single-user loop first |
| Tailor network and booking | Y2 | A marketplace on top of an unproven product |
| Phone OTP | M1-2 | Email covers the launch audience; SMS costs money and adds deliverability risk |
| Native web app parity | Not planned | Web is landing plus share pages; the product is the Flutter app |
| Manual account linking | M1-2 | Rare at launch volume; copy on the auth screen mitigates it |
| Deferred deep linking | M1-2 | Needs a third-party service; not worth launch effort |
| Look generation cancellation | M1-2 | Abandoning the screen is an acceptable substitute |

---

## 4. Launch criteria

Not a date. These are the conditions:

**Functional**
- A new user can sign in, complete the quiz, add three vault items, generate a look, save it, and share it — without assistance.
- A user can upload fabric, get style suggestions, and send one to a tailor over WhatsApp.
- Account deletion works end to end and completes within the SLA.
- Every screen has a designed empty, loading, and error state.

**Quality**
- `dna_answers` golden set passes at 100%.
- `pii_images` recall at or above 0.98 for face detection and EXIF stripping.
- `spree_safety` passes at 100%; no jailbreak in the suite produces a non-refusal.
- Look generation p95 under 45 seconds.
- Generation failure rate under 5%.

**Operational**
- All six dashboards live with data flowing.
- Every alert has a runbook.
- Backups running, and a restore tested at least once.
- Cost per active user measured and under the ceiling.

**Legal**
- Consent surfaces exist for every purpose in use.
- Privacy policy and terms published and linked from the app.
- RoPA complete; every collected field has a lawful basis and a retention period.
- The `api-gateway` PAT is revoked and no secret exists in any repository.

---

## 5. Deliberately unsolved at MVP

Named so nobody thinks they were forgotten:

- **Cold start with an empty vault.** Generative rendering covers it — looks can be produced before a user photographs anything — but the first session is weaker than the tenth. Pinterest import helps where a user connects it.
- **Style library depth.** Thirty styles is enough to be useful and not enough to be exhaustive. Gaps will show for unusual fabric and occasion combinations.
- **Reference image consistency.** Licensed tailor photography and generated references will not look like one set. Visual coherence improves with the commissioned shoot, later.
- **Nigerian sizing.** Brand sizing is wildly inconsistent and there is no reliable standard to map to. Body profile captures fit preference rather than pretending to solve sizing.
- **Multi-user households.** One account, one wardrobe. Shared wardrobes are out of scope entirely.

---

## 6. Scope discipline

Three questions before anything is added to MVP scope:

1. **Does it serve the core loop?** If not, it belongs on the roadmap.
2. **Does the design have screens for it?** If not, it needs design before engineering, not after.
3. **What comes out to make room?** Scope is a fixed budget. Adding without removing is how a four-week build becomes four months.

Recorded scope changes go in this document with the date and the reasoning, so the drift is visible rather than remembered differently by each person.
