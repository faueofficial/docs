# Roadmap

**Stage:** all

Each phase unlocks only if the previous one hits its criteria. Building the next phase before the current one is proven is how a product acquires features nobody uses.

---

## MVP — the styling loop

**Ships:** Style DNA, vault, look generation, fabric styling, tailor share, saving, sharing, Pinterest import, agent L0, spree, body profile, notifications, privacy, landing and share pages, admin console.

**Proves:** that generated, explained, culturally-correct looks drive action and return.

**Unlock criteria for the next phase:**

| Metric | Threshold |
|---|---|
| Quiz completion | ≥ 60% of starts |
| Look generation in first session | ≥ 70% of users who finish the quiz |
| Look save rate | ≥ 25% of generated looks |
| 14-day return, unprompted | ≥ 20% |
| DNA card share | ≥ 10% of completions |
| Tailor share | ≥ 15% of fabric uploads |

Falling short of these means fixing the loop, not adding to it.

---

## M1-2 — depth and habit

**Conditional on:** 20%+ 14-day return.

| Item | Why now |
|---|---|
| **Agent L1** — daily push suggestion | Wear-log data now exists to make suggestions worth receiving |
| **Agent L2** — weather, event, and new-pin triggers | Same |
| **Catalog service** — 500 curated products | Recommendations extend beyond what the user owns |
| **Affiliate links** on catalog items | First revenue signal, and the traffic data needed for brand conversations |
| **Media service extraction** | Image processing load justifies its own deployment |
| **Virtual try-on** | Retention booster, now that retention is worth boosting. Requires the `body_imagery` consent purpose and a deliberate exception to the no-people rendering rule — see [`professional-strategy.md`](professional-strategy.md) §9 |
| **Phone OTP** | Broadens reach beyond email-first users |
| **Manual account linking** | Support burden becomes real at volume |
| **Deferred deep linking** | Share-driven installs are material enough to attribute |
| **Generation cancellation** | Quality-of-life once generation volume is high |
| **Cross-encoder reranking** | Enough interaction data to beat the heuristic ranker |

**Unlock criteria for M3+:**

| Metric | Threshold |
|---|---|
| Affiliate click-through | ≥ 10% of users click at least one |
| 30-day retention | ≥ 15% |
| Weekly active / monthly active | ≥ 0.35 |
| Agent suggestion accept rate | ≥ 20% |

---

## M3+ — partners and money

**Conditional on:** affiliate click-through proving demand is real.

| Item | Why now |
|---|---|
| **Brand service and dashboard** | Approach the brands whose products got the most clicks, holding traffic data rather than promises |
| **Commerce service** — subscriptions, affiliate ledger | Monetise a proven habit |
| **FAUE Pro** subscription | Unlimited generation, priority features, deeper DNA insight |
| **Aso-Ebi group coordination** | The highest-value social use case, and it needs a working single-user product underneath |
| **Spree extraction** | Conversational load competes with generation for capacity |
| **Learning-to-rank** | Enough labelled interaction data to train properly |
| **Agent L3** — event and travel planning | Trust established through L1 and L2 |

---

## Y2 — the production layer

Two tracks run in parallel from here: the consumer platform below, and the **professional product** in [`professional-strategy.md`](professional-strategy.md). The professional track is sequenced tailors → stylists → shows, and nothing in it starts before consumer retention is proven.

### Consumer platform

| Item | Notes |
|---|---|
| **Tailor network** | Vetted tailors, in-app booking, quality tracking, dispute handling. Closes fabric → style → garment |
| **Marketplace** | Brands selling directly through FAUE |
| **Regional expansion** | Ghana and Senegal — different traditional wear, same structural problem |
| **Style DNA API** | Let other platforms use FAUE's style intelligence |
| **FAUE label** | Own line, built on data about what people actually want and cannot find |

---

## Deliberately never

| Item | Why |
|---|---|
| Social feed, followers, likes | FAUE ends the search; it does not become another place to scroll |
| Body optimisation framing | Clothes fit people, not the reverse |
| Scraped style library | Legal exposure on the core asset ([ADR 0020](../80-adr/0020-style-library-licensed-not-scraped.md)) |
| Instagram integration as designed | The API cannot deliver it ([ADR 0019](../80-adr/0019-remove-instagram-integration.md)) |
| Full web app parity | The product is the app; web serves sharing and acquisition |

---

## Architectural work that follows the product

Boundaries already exist for all of these; each is triggered by load rather than by schedule.

| Trigger | Change |
|---|---|
| Professional features begin | Workspaces activate — the schema is already capable ([ADR 0021](../80-adr/0021-workspace-tenancy-model.md)) |
| Virtual try-on research completes | Fourth `ImageRenderer` strategy plus a `body_imagery` consent purpose |
| Spree competes with generation for capacity | Extract `spree` from `ase` |
| Notification volume or channel count grows | Extract `notify` from `gateway` |
| Curation begins in earnest | Extract `catalog` |
| Image processing dominates gateway CPU | Extract `media` |
| Second backend engineer joins | Split `faue-db` into per-service Alembic projects |
| Embedding volume outgrows hosted pricing | Move embeddings self-hosted |
| Traffic exceeds a single instance | Introduce Kubernetes — not before |
