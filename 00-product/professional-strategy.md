# Professional Strategy

**Stage:** Y2 (build) · MVP (one data-model decision) · **ADR:** [0021](../80-adr/0021-workspace-tenancy-model.md)

FAUE's long-term direction is fashion technology, not a consumer styling app that happens to be popular — used in fashion shows, in pop-up collaborations, and daily by the stylists and tailors who actually make clothes happen in Nigeria.

This document defines who those professionals are, what would make them stay, the order to approach them in, and — the only part that affects work today — what must be true of the data model before code is written.

---

## 1. The principle

**Hold comes from data professionals cannot take with them, not from features.**

Features get copied within a quarter. A tailor's measurement book with two hundred clients, versioned over three years, does not move. A stylist's client wardrobes and lookbook history do not move. That is the whole strategy; everything below is an expression of it.

A second principle follows from the first: **the professional product is a different product**, sharing a spine with the consumer app. Different users, different sales motion, different support burden, different economics. Treating it as a feature of the consumer app is how both end up mediocre.

---

## 2. What must be decided now

Only one thing: **tenancy**.

The current model is one user, one vault, one style context. A stylist with twenty clients does not fit it. Neither does a tailor with two hundred measurement books, nor a show workspace with forty looks and six people in it.

```
now:     user_id     → vault, looks, style_context
needed:  workspace_id → members(role) → clients → vaults, looks, jobs
         a personal account is a workspace of one
```

Adding a `workspace_id` before any data exists costs about a day. Adding it in year two means migrating every table in `gateway` and `ase` against a live database, rewriting every query, and freezing consumer development while it happens.

**Decision: the schema becomes workspace-capable now; the product deliberately does not.** Rationale and consequences in [ADR 0021](../80-adr/0021-workspace-tenancy-model.md).

Nothing else in this document affects work before `Y2`.

---

## 3. Tailors — first, and already reachable

The strongest wedge, because FAUE is already in their WhatsApp. Every tailor share sends them an image today; the distance from passive recipient to retained user is short.

### The pain, in order of severity

1. **Measurements live in a paper notebook.** They get lost, re-taken inconsistently, and mixed up between clients. This is the trade's defining administrative problem.
2. **Job tracking runs on WhatsApp threads.** Who ordered what, what deposit was paid, what is due Friday — reconstructed by scrolling. Money is lost here routinely.
3. **Fabric quantity is estimated by memory.** Wrong estimates mean either wasted fabric the client paid for, or a second trip to the market.
4. **New clients come only by referral.** No portfolio that works while they sleep.

### What FAUE would offer

| Feature | Why it holds |
|---|---|
| **Measurement book** | Digital, per client, versioned over time. **This alone is the wedge** — it solves the defining problem and nothing else in their life does |
| **Job pipeline** | Order, deposit, due date, collection. Replaces the WhatsApp thread |
| **Fabric yardage calculator** | Style + measurements → yards required. Pure computation over data FAUE already models |
| **Attributed portfolio** | Their work in the style library, credited, linked. Generates leads |
| **Client history** | What this person ordered before, what fit, what came back |

After six months the switching cost is their entire client book. That is the hold.

### The real constraint is not features

A low-end Android phone, metered data, WhatsApp as the primary computing surface, and often limited written English. The best feature set in Nigeria goes unused if this is got wrong.

Design consequences, none optional:

- **WhatsApp bot before app.** The surface they already live in.
- **Offline-first, genuinely.** Not a cache — full function without connectivity, syncing when it returns.
- **Voice input** for measurements. Reading a tape while typing is not realistic.
- **Yoruba, Hausa, and Pidgin** interfaces, not only English.
- **Data-light by default.** Every image sized down, nothing prefetched.

### Strategic weight

Tailors are also the supply side of the `Y2` tailor network. Every tailor retained by the measurement book is a tailor available for in-app booking later. The style library licensing outreach — which starts before launch — is already the first conversation.

---

## 4. Stylists — second, higher value per user

Fewer of them, more willing to pay, more digitally comfortable.

### The pain

Managing many clients' wardrobes with no system. Building lookbooks in slide decks. Tracking borrowed samples across shoots in a notes app. Chasing approvals over WhatsApp. Invoicing manually.

### What FAUE would offer

| Feature | Why it holds |
|---|---|
| **Multi-client wardrobes** | The consumer vault × N clients. This is exactly the tenancy problem |
| **Lookbook builder** | Assemble, sequence, present. The look pipeline already produces the units |
| **Pull sheets and sample tracking** | Which piece, from which brand, due back when. Shoots lose real money here |
| **Client presentation mode** | Send a styled proposal, capture approval, track decisions |
| **Rate card and invoicing** | Boring, and it is why they stay |

### The head start

FAUE's reconciliation engine — aspiration versus body versus budget, resolving to *reproduce*, *adapt*, or *bespoke path* — is a formalisation of what a stylist does by hand. The consumer product is, structurally, an automated junior stylist. Selling the same engine to a professional as leverage rather than replacement is a coherent pitch.

The framing matters: **augment, do not replace**. A tool that implies a stylist is unnecessary will not be adopted by stylists.

---

## 5. Shows and pop-ups — third, and measured differently

Low frequency, high visibility. Nobody retains on four events a year.

### What it would offer

Run-of-show sequencing, model-to-look assignment, dresser sheets with quick-change flags, backstage coordination, and post-show analytics on which looks drew attention. Pop-ups add appointment booking, on-site styling sessions, and a capture funnel into the consumer product.

### How to judge it

**As distribution and credibility, not retention.** This is how FAUE becomes the platform the industry knows, how it reaches designers and brands, and how it earns the relationships that make `M3+` partnerships possible.

Measuring it on monthly active users will make it look like a failure while it is doing exactly its job. The right metrics are events run, brands reached, consumer signups attributed, and press.

---

## 6. Sequencing

```
CONSUMER RETENTION PROVEN     D14 ≥ 20% unprompted
        ↓
TAILOR — measurement book     WhatsApp-first, offline, voice, multi-language
        ↓                     also builds the Y2 tailor-network supply side
STYLIST — client wardrobes    needs workspaces; higher revenue per user
        ↓
SHOWS AND POP-UPS             credibility and distribution, not retention
```

**Nothing professional starts before consumer retention is proven.** A professional tool built on an unproven consumer product is two unproven products, and two people cannot carry that.

The exception, and the only one: the tenancy decision in §2, which is made now precisely so that none of this requires restructuring later.

---

## 7. What the architecture already gives free

More than expected, because several MVP decisions happen to generalise:

| Existing | Why it transfers |
|---|---|
| **`ase` holds no direct identifiers** | It knows `user_id` and vectors. Pointing it at a stylist's client context is a parameter, not a redesign |
| **Closed-set policy** | A stylist's client wardrobe is just a different legal pool |
| **Style library provenance fields** | `source`, `license_type`, `attribution` already model the tailor relationship — the supply-side hook exists |
| **`ImageRenderer` interface** | Virtual try-on becomes a fourth strategy with no structural change |
| **Events and outbox** | Multi-party workflows need no new mechanism |
| **Image PII pipeline** | Already handles third-party faces, which becomes critical the moment a stylist uploads client photos |
| **Job model with progress** | Show and lookbook rendering are the same shape as look generation |

---

## 8. What needs genuinely new design

| Gap | Weight | Notes |
|---|---|---|
| **Workspace tenancy** | **Decide now** | [ADR 0021](../80-adr/0021-workspace-tenancy-model.md) |
| **Delegated consent** | Heavy | Client grants a stylist partial, revocable access. The consent registry is currently user↔FAUE, not user↔user |
| Role model beyond admin RBAC | Medium | Workspace roles: owner, member, client |
| B2B billing, seats, invoicing | Medium | Different from consumer subscription |
| Offline-first | Heavy | Non-negotiable for tailors |
| Multi-language and voice | Heavy | Non-negotiable for tailors |
| Show production data model | Medium | Run of show, dresser sheets, model assignment |

**Delegated consent is the subtle one.** "Amara lets her stylist see her wardrobe but not her measurements, and can revoke it at any time" is a real GDPR and NDPA design problem. It is far easier to design into a model that already has membership than to bolt onto one that does not — which is a second reason the tenancy decision cannot wait.

---

## 9. Virtual try-on

Researched separately. Where it attaches, so the research has a target:

- **Interface:** a fourth `ImageRenderer` strategy. The job model, progress states, storage, and guardrails are unchanged.
- **Guardrails:** this is the first feature that renders a real person's body, so §6 of [`../60-ai/rendering.md`](../60-ai/rendering.md) — currently "no people, ever" — needs a deliberate exception with its own consent purpose, its own retention rule, and its own eval set.
- **Consent:** a new purpose (`body_imagery`), explicit, separate from `camera_photos`, revocable, with immediate deletion of derived assets on revocation.
- **Professional relevance:** far higher than consumer. A stylist showing a client a look, or a tailor confirming a cut before cutting fabric, is worth more than a consumer previewing an outfit.

The consumer case is a retention booster. The professional case is a reason to buy.

---

## 10. Honest risks

**It is a second product.** Different users, sales motion, support burden. The most likely failure is attempting it before the consumer loop is proven and stalling both.

**It reintroduces two-sidedness.** The marketplace was cut precisely to escape cold start ([ADR 0010](../80-adr/0010-defer-catalog-and-affiliate.md)). Professional tools bring it back — a stylist with no clients on FAUE gets less value; a tailor with no orders through FAUE gets none. Mitigation: the measurement book and job pipeline are **single-player useful**. They work with zero other FAUE users. Any professional feature that requires network effects to be useful is the wrong first feature.

**The tailor segment may not be reachable digitally at all.** This is the genuine unknown. Validate before building: sit with five tailors, watch how they actually work, and try the measurement book as a WhatsApp conversation with no product behind it. If that fails, no amount of engineering fixes it.

**Professional expectations are higher.** A consumer forgives a mediocre suggestion. A stylist whose pull sheet is wrong loses a shoot; a tailor who cuts to a wrong measurement loses fabric and a client. Correctness requirements go up sharply.

---

## 11. What to do before Y2, at near-zero cost

1. **Take the tenancy decision** ([ADR 0021](../80-adr/0021-workspace-tenancy-model.md)). One column, one helper, one day.
2. **Use the style library outreach as professional research.** Those tailor conversations are already scheduled. Ask about measurements, job tracking, and fabric estimation while you are there.
3. **Track which tailors receive shares.** The tailor-share flow already touches them; counting distinct recipients costs nothing and sizes the segment for free.
4. **Keep `ase` identity-free.** It is already true and is what makes multi-tenant styling cheap.
5. **Design VTO consent alongside the VTO research**, not after it.

Everything else waits for the consumer loop to prove itself.
