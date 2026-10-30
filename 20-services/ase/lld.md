# ase — Low-Level Design

**Stage:** MVP · **Repo:** `faueofficial/ase` · **Schema:** `ase` · **Ingress:** internal only

The styling intelligence. Named for Yoruba *àṣẹ* — the power to make things happen. No public ingress: it is called by `api-gateway` with a service JWT, and driven by events.

`ase` holds no direct identifiers. It knows `user_id` and vectors; it does not know an email, a phone number, or a measurement.

> **See also:** [`../../60-ai/ase-architecture.md`](../../60-ai/ase-architecture.md) — the tiered architecture, per-section low-level diagrams, cost model and evaluation gates (proposed; it asks for ADRs that would supersede 0017 and 0018 in part).

---

## 1. Module layout

```
app/
├─ main.py  config.py  deps.py
├─ api/internal/            gateway-only, service JWT required
│  looks.py fabric.py spree.py agent.py context.py embeddings.py admin.py
├─ models/                  THE MODEL PLANE — no vendor SDK outside this package
│  ├─ router.py             task → tier → provider, fallback, breaker, budget
│  ├─ llm/                  base.py openrouter.py recorded.py (tests)
│  ├─ embedding/            base.py open_clip.py hf.py voyage.py cohere.py gemini.py
│  ├─ render/               base.py generative.py composite.py hybrid.py
│  ├─ cache.py budget.py redaction.py telemetry.py
│  └─ config/models.yaml
├─ prompts/<task>/v<n>.md   versioned files; version logged with every response
├─ engine/
│  ├─ pool.py               stage 2 — hard filters produce the legal pool
│  ├─ color.py              LAB distance, harmony relations, neutral anchors
│  ├─ stylist.py            stage 3b — model selects and assembles
│  ├─ validate.py           stage 3c — ids must exist in the pool
│  ├─ rank.py               stage 4 — heuristic → cross-encoder → LTR
│  ├─ explain.py            stage 6 — grounded narration
│  └─ style_context.py      dna / aspiration / behaviour vectors and blending
├─ fabric/                  classifier.py rules.py library.py pairing.py
├─ spree/                   EXTRACTABLE
│  ├─ session.py  tools/  review.py
│  └─ guardrails/           input.py intent.py injection.py grounding.py output.py
├─ agent/                   planner.py memory.py triggers.py levels.py
├─ context/                 weather.py occasions.py providers/
├─ vector/                  index.py search.py migration.py
├─ events/  workers/        embed_items, rebuild_context, agent_daily, reembed
```

---

## 2. The generation pipeline

```
1  RETRIEVE   ANN over embeddings, over-fetch k*4          MODEL
2  FILTER     consent, availability, size, silhouette,      RULES (hard)
              owned-item suppression → the LEGAL POOL
3a POOL       everything that survived stage 2              RULES
3b STYLIST    model selects and assembles from the pool:    MODEL
              colour harmony, proportion, layering,
              texture, cultural and occasion fit;
              may swap and may reject valid combinations
3c VALIDATE   every returned id must exist in the pool;     RULES
              category coverage checked; unknown ids
              dropped, never repaired
4  RANK       order the assembled looks                     MODEL
5  RENDER     generative (default) | composite | hybrid     MODEL / deterministic
6  EXPLAIN    "Why this works for you"                      MODEL
```

Rules keep exactly two jobs: defining what is legally available, and verifying that what came back is real. Everything aesthetic between those two points belongs to the model. See [ADR 0008](../../80-adr/0008-closed-set-model-policy.md) and [ADR 0017](../../80-adr/0017-model-led-assembly.md).

### Stage 2 — the legal pool

Hard filters, in order of selectivity:

```python
pool = candidates
pool = [i for i in pool if i.available]                    # not deleted, not dead link
pool = [i for i in pool if size_matches(i, profile)]       # from body_profile sizes
pool = [i for i in pool if silhouette_ok(i, constraints)]  # derived body constraints
pool = [i for i in pool if occasion_plausible(i, occasion)]
pool = suppress_recently_worn(pool, wear_log, days=3)      # soft: deprioritise, not remove
```

If the pool falls below a viable size the pipeline stops and returns `empty_pool` rather than producing a bad look from three items. Widening happens by relaxing occasion first, then recency, never by relaxing size or silhouette.

### Stage 3a — the colour prior

Computed, not asked of the model:

- Convert each item's dominant colours to CIELAB.
- Compute pairwise ΔE.
- Classify relations: complementary, analogous, triadic, monochrome, neutral-anchored.
- Flag clashes — high chroma, similar hue, close lightness.

Supplied to the stylist as measured fact. The model then judges what a distance metric cannot: whether the combination reads correctly for an Owambe, whether the proportions work, whether the print scale fights the cut.

### Matching against items the user owns

When the stylist proposes a piece, the system checks whether the user already owns something close enough to use instead. Cosine similarity **above 0.85** flags the owned item and substitutes it into the look.

That threshold is deliberately high: suggesting "wear the shirt you already own" is only valuable when it is actually the right shirt. A near-miss is worse than no match, because the user opens their wardrobe and finds something that does not work.

### Stage 3b — the stylist pass

The model receives the pool with attributes, the colour prior, the style context, the occasion, weather if permitted, and the user's note. It returns ordered looks composed of pool item identifiers, with per-look rationale.

Structured output enforced by schema. One retry on parse failure, then the heuristic assembler as fallback.

### Stage 5 — rendering

Three strategies behind `ImageRenderer`, `generative` by default. Prompts are constructed from the deterministic `LookSpec`, never from raw user text — that is both a quality control and an injection defence. Detail in [`../../60-ai/rendering.md`](../../60-ai/rendering.md).

---

## 3. Style context

Three vectors, deliberately not blended at rest:

| Vector | Source | Weight at cold start | Weight when mature |
|---|---|---|---|
| `dna_vector` | Quiz | 0.6 | 0.2 |
| `aspiration_vector` | Pinterest boards | 0.4 | 0.3 |
| `behavior_vector` | Wear log, saves, feedback | 0.0 | 0.5 |

Maturity is measured by logged wears; the shift is gradual from roughly 10 to 40 wears. Keeping the vectors separate means reweighting is a configuration change rather than a re-embed, and it makes "why did you suggest this?" answerable — the contribution of each source is inspectable.

Context is cached with a `stale_at` timestamp and rebuilt on `quiz.completed`, `vault.item.worn`, `integration.synced`, and `recommendation.feedback`.

---

## 4. Fabric analysis

Rules-first, unlike generation, because a wrong style match costs the user real money at a tailor.

```
embed fabric image
  → classify type: kNN over labelled swatches; vision model only if confidence < 0.7
  → extract attributes: motif scale, weight, dominant colours
  → rule match over the style library:
        fabric_suitability[type] must not be "avoid"
        occasion and formality must overlap
        body notes must not conflict with derived constraints
  → rank surviving styles
  → per-style reasoning grounded in fabric attributes + style tags
  → accessory pairings, occasion-aware
```

Thirty styles across six fabric types is 180 combinations with genuine physical constraints — heavyweight Aso-Oke will not drape as a Boubou; large-motif Ankara loses its pattern in a heavily seamed cut. These are facts, not preferences, and they belong in rules.

---

## 5. spree — extractable

Sessions, tool calls, streaming. The tool surface is **read-only in its entirety**: `find_similar`, `pair_items`, `check_occasion_fit`, `list_owned`, `get_constraints`, `weather_today`, and `catalog.search` from M1-2.

Nothing mutates state. Nothing spends money. That is the injection defence — a successfully injected model still has nothing harmful to reach for.

Bounded: 4 tool rounds, 8 total calls, 30-second wall clock, per-session token budget.

Guardrails are separate composable objects, each independently unit-tested against the `spree_safety` set. A guardrail expressed only as prompt text cannot be tested and cannot be proven.

---

## 6. agent

| Level | Trigger | Stage |
|---|---|---|
| L0 | App open | MVP |
| L1 | Daily schedule | M1-2 |
| L2 | Weather shift, upcoming event, new pin | M3+ |
| L3 | Event and travel planning | Y2 |

Memory in three tiers — profile facts (durable), semantic preferences (learned, decayed), episodic (90 days). All inspectable and user-editable. "Why did you suggest this?" answers from stored facts, never from a fresh prompt.

---

## 7. context

Two signals with the same shape: given a user and a time, return facts that bias generation. Both degrade silently — no consent, no data, or a provider down all mean generation proceeds without them.

### 7.1 weather

Weather from Open-Meteo, cached per `(geohash5, hour_bucket)` so an entire city costs one upstream call. Location is city-level only; precise coordinates are never received or stored.

Signals used: temperature and feels-like, rain probability, humidity, UV, and a **harmattan dust index**. Saharan dust materially changes what fabric and colour are wearable in Nigeria between December and February, and no generic weather integration captures it.

### 7.2 occasions

The cultural calendar. Answers "what is happening, and what is coming" for a user's locale.

This exists as one module because three consumers otherwise each grow their own copy: look generation biases occasion defaults, the agent fires L2 triggers from it, and the retention worker schedules cultural campaigns from it. One source, three readers.

> **It is not "occasion routing".** That name (from the superseded architecture in `90-meta/legacy/`) describes request dispatch, which this is not. Occasion is a styling input, so it lives with the thing that does styling. Putting it in the gateway would mean the gateway either duplicating the style library's occasion knowledge or calling `ase` to ask what an Owambe means — which is backwards.

#### Three layers

**Taxonomy** — the eight occasions and what each implies. Static, versioned with the style library:

| Occasion | Formality | Fabric bias | Notes |
|---|---|---|---|
| `owambe` | formal → ceremonial | Aso-oke, lace, heavy Ankara | The highest-stakes occasion in the product |
| `wedding` | formal → ceremonial | Lace, brocade, Aso-oke | Often aso-ebi coordinated |
| `church` | smart-casual → formal | Modest cuts, lace, cotton | Sunday-specific |
| `corporate` | business → formal | Wool, crisp cotton, structured | Weekday, client-facing variants |
| `casual` | casual | Cotton, denim, linen | The default |
| `date_night` | smart-casual → formal | Silk, fitted cuts | Evening |
| `travel` | casual | Linen, jersey, breathable | Comfort and packing constraints |
| `funeral` | formal | Muted palette, lace, Aso-oke | Palette constraints are strict |

**Windows** — when occasions cluster, which is the part a generic styling app cannot know:

| Window | Kind | Period |
|---|---|---|
| Detty December | fixed | Dec 1 – Jan 5 |
| Wedding season | fixed | Nov – Jan, Apr – Jun |
| Harmattan | weather-derived | Dec – Feb, confirmed by the dust index |
| Ramadan / Eid | **lunar** | Shifts ~11 days a year |
| Christmas / Easter | fixed / computed | Dec 25; Easter is computed |
| Month-end | recurring | Payday; higher planning intent |

**Derived signals** — what the three consumers actually read:

```python
@dataclass(frozen=True)
class OccasionSignal:
    key: str                                    # "detty_december"
    name: str
    status: Literal["active", "upcoming", "inactive"]
    days_until: int | None                      # None when already active
    intensity: float                            # 0.0-1.0, how strongly to bias
```

#### The lunar problem

Ramadan and Eid move roughly eleven days earlier each year. **Hardcoded date windows are silently wrong within two years** — nothing errors, the calendar simply stops matching reality, and the failure shows up as culturally tone-deaf suggestions rather than as a bug.

Handled with **one row per window per year** rather than a computation. Someone confirms the dates annually, which is a fifteen-minute task and auditable, where a lunar-calendar library is a dependency and an approximation. Fixed-date windows (Detty December, Christmas, harmattan) are seeded once.

A window with no row for the current year is treated as inactive and logged — the calendar degrades to silence rather than to a wrong date.

#### Who reads it

| Consumer | Use |
|---|---|
| Look generation | Bias the default occasion and the formality prior when a window is active |
| Agent L2 (`M3+`) | "Detty December in three weeks — plan your looks" |
| Retention worker | Schedule cultural campaigns from real dates, not a hardcoded calendar |
| Dashboard chips | Reorder seasonally — Owambe first in December. A read, not a module |

---

## 8. vector layer

HNSW indexes (`m=16, ef_construction=64`), cosine distance, vectors normalised on write. Partial index per `model_id` so several embedding models coexist during migration.

Migration is dual-write → shadow-evaluate on the golden set → flip reads by flag → soak → drop old rows. No downtime, no big-bang re-embed.

Over-fetch `k*4` before hard filtering, because post-filtering a tight ANN result collapses narrow queries to nothing.

---

## 9. Workers

| Worker | Trigger | Does |
|---|---|---|
| `embed_items` | `vault.item.added` | Embed and index a vault item |
| `embed_pins` | `integration.synced` | Embed imported pins, build aspiration vectors |
| `rebuild_context` | Several events | Recompute a user's style context |
| `generate_look` | Job queue | The pipeline |
| `render_look` | Job queue | Image rendering, separate so it can scale alone |
| `agent_daily` | Schedule (M1-2) | Daily suggestions |
| `reembed` | Manual | Model migration |
| `spree_review` | Continuous | Route flagged sessions to the review queue |

---

## 10. Testing

Pure-logic units — pool construction, colour analysis, validation, fabric rules, guardrails — are unit-tested with no I/O and gated at 100% branch coverage.

Model calls in tests go through `RecordedLLMProvider`, registered through the same `LLMProvider` interface. **No test ever makes a real model call**, which keeps CI free, fast, and deterministic.

Vector search is tested against a real Postgres with pgvector via testcontainers, using a small fixed corpus with known expected neighbours.
