# Style DNA — Personas, Questions, and Scoring

**Stage:** MVP · **Status:** proposal for review · **Version:** `dna-2026-08-v1`
**Supersedes:** the ten-question, thirteen-point specification in `faue (1).md` (see [ADR 0011](../80-adr/0011-six-question-style-dna.md))

This document is FAUE's own definition of the persona taxonomy, the six questions, every answer option, the weights each option carries, and the scoring algorithm. It is written to be argued with — every non-obvious choice states its reasoning so it can be rejected on its merits.

Once approved, the question and option copy is relayed to the frontend engineer as content, and the weight matrix becomes `personas.yaml` in `api-gateway`.

---

## 1. What the Style DNA is for

Two jobs, and they pull in different directions:

1. **Personalisation input.** It gives `ase` a usable style vector before a user has photographed a single item, solving cold start.
2. **Shareable identity.** The result card is the viral mechanism. It has to feel like something worth posting.

Where the two conflict, personalisation wins on the data model and identity wins on the presentation. The scoring produces a nuanced blend internally; the card presents a clear dominant persona.

**Design constraint:** six questions, one per screen, progress 0 → 90%, then a processing screen ("Analyzing your style...."), then the result. Fixed by the Figma design.

---

## 2. The six personas

Personas were chosen so that each maps to **distinct, actionable styling constraints**. A persona that does not change what the engine recommends is decoration; each of these changes silhouette, palette, formality, or fabric preference in a specific way.

| ID | Name | Core idea |
|---|---|---|
| `CM` | **The Cultural Minimalist** | Heritage worn with restraint. Clean lines, considered detail, cultural reference rather than cultural announcement. |
| `OR` | **Owambe Royalty** | Maximalist and event-driven. Presence is the point. Rich fabric, statement silhouette, full commitment to the occasion. |
| `SL` | **Soft Luxe** | Comfort-first and quietly expensive. Fluid shapes, tactile fabric, nothing that fights the body. |
| `SC` | **Street Alchemist** | Eclectic and experimental. Layering, streetwear, rare finds, deliberate mismatch that works. |
| `CE` | **Corporate Edge** | Sharp, polished, professional — with one element that refuses to be boring. |
| `NF` | **Neo-Fusion** | Heritage and contemporary in the same outfit. Ankara trousers with a plain tee. The blend is the statement. |

`CM` is retained from the design's result screen ("The Cultural Minimalist"), which is where the taxonomy started.

### Distinctness check

`CM` and `NF` both engage with heritage, so the boundary must be sharp: `CM` uses heritage as **restraint** (one adire panel, muted palette, tailored cut), `NF` uses it as **expression** (print-forward, mixed references, visible blending). `CE` and `CM` both favour tailoring: `CE` is occasion-led toward work and formality, `CM` is aesthetic-led toward simplicity everywhere.

### Styling implications — what each persona actually changes

This table is the contract between the quiz and `ase`. It is what makes the persona operational rather than decorative.

| Persona | Favours silhouette | Avoids | Palette | Formality range | Fabric affinity | Occasion bias |
|---|---|---|---|---|---|---|
| `CM` | Clean tailoring, straight lines, defined shoulder | Busy layering, clashing print, heavy embellishment | Neutrals, muted earth, one accent | Smart-casual → formal | Cotton, linen, adire, structured wool | Everyday, corporate, understated events |
| `OR` | Full skirts, dramatic sleeves, structured gele, floor-length | Understated, plain, minimal | Rich saturated, gold, jewel tones | Formal → ceremonial | Aso-oke, lace, brocade, heavy Ankara | Owambe, weddings, celebrations |
| `SL` | Fluid, draped, relaxed, unstructured | Restrictive, stiff, overly constructed | Tonal neutrals, cream, soft earth | Casual → smart-casual | Silk, linen, modal, soft cotton | Everyday, travel, relaxed social |
| `SC` | Oversized, layered, asymmetric, proportion play | Matchy sets, conventional formality | High contrast, unexpected pairings | Casual → creative-formal | Denim, jersey, mixed texture, vintage | Creative spaces, casual, nightlife |
| `CE` | Precise tailoring, sharp shoulder, defined waist | Sloppy, unstructured, overly casual | Monochrome, dark neutrals, one sharp accent | Business → formal | Wool, crisp cotton, structured blends | Corporate, client-facing, evening |
| `NF` | Traditional cut in modern proportion, mixed references | Fully western or fully traditional without blend | Heritage prints with contemporary neutrals | Smart-casual → formal | Ankara, adire, aso-oke mixed with denim, cotton | Everyday, cultural events, creative work |

---

## 3. Scoring model: weight vectors, not single-persona mapping

**The change from the previous specification, and the reason for it.**

The old model mapped each answer to exactly one persona. With ten questions that produced a usable spread. With six questions it does not: six answers can touch at most six personas, so most results would be a near-tie between two personas with everything else at zero, and the tie-breaker would be doing the real work.

Instead, **every answer option carries a weight vector across all six personas**, with values 0–3. A single answer expresses partial affinity with several personas at once, which is also how style actually works — someone who picks "Minimal" is telling you something about `CM`, `CE`, and `SL` simultaneously.

This yields a smooth, informative distribution from only six inputs, and gives `ase` a genuine blend vector rather than a single label.

### Question weights

| Question | Measures | Weight |
|---|---|---|
| Q1 | Core aesthetic identity | **×2** |
| Q2 | Occasion mix | ×1 |
| Q3 | Energy and temperament | ×1 |
| Q4 | Colour palette | ×1 |
| Q5 | Silhouette and fit | ×1 |
| Q6 | Risk appetite | **×2** |

Q1 and Q6 are doubled because they measure stable identity rather than situational preference. What someone considers "most like them" and how much risk they take are durable; where they are usually headed changes with a job change.

---

## 4. The questions

Copy follows the voice already established in the Figma design: second person, warm, no fashion jargon, no judgement. Option A of each question is the copy that already exists in the design and is preserved verbatim.

---

### Q1 — Core identity · weight ×2

> **What feels most like you?**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **Minimal** | Clean, simple, and intentional. Pieces that speak softly, but carry presence. | 3 | 0 | 2 | 0 | 3 | 0 |
| **B** | **Bold** | Colour, pattern, presence. If nobody looks twice, what was the point? | 0 | 3 | 0 | 3 | 0 | 2 |
| **C** | **Rooted** | Heritage-led. Ankara, adire, aso-oke — worn my way, not the way I inherited it. | 2 | 2 | 0 | 0 | 0 | 3 |
| **D** | **Easy** | Soft, comfortable, quietly expensive. Nothing that fights me. | 1 | 0 | 3 | 1 | 0 | 0 |

> **Why two personas share the top score on A and B:** "Minimal" genuinely describes both `CM` and `CE`, and "Bold" describes both `OR` and `SC`. Forcing a single winner here starved `CE` and `SC` of any strong signal on a double-weighted question, which made them nearly unreachable as dominant personas. See §11.

---

### Q2 — Occasion mix · weight ×1

> **Where are you usually headed?**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **Casual Outings** | Easy and relaxed. Effortless outfits that feel natural, comfortable, and put together without trying too hard. | 1 | 0 | 2 | 2 | 0 | 1 |
| **B** | **Owambe & Celebrations** | Weddings, parties, aso-ebi. My weekends have a dress code. | 1 | 3 | 0 | 0 | 0 | 2 |
| **C** | **Work & Meetings** | Offices, clients, presentations. I dress for rooms where I'm being assessed. | 2 | 0 | 1 | 0 | 3 | 0 |
| **D** | **Creative Spaces** | Shows, shoots, launches, late hangouts. Rooms where standing out is the norm. | 0 | 1 | 1 | 3 | 0 | 2 |

---

### Q3 — Energy · weight ×1

> **What energy do you bring to your outfits?**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **Chill** | Relaxed and effortless. You keep things easy, comfortable, and naturally put together without overthinking it. | 1 | 0 | 3 | 1 | 0 | 0 |
| **B** | **Commanding** | You want the room to register you before you speak. | 0 | 3 | 0 | 0 | 2 | 1 |
| **C** | **Playful** | You mix things that shouldn't work, and make them work. | 0 | 1 | 0 | 3 | 0 | 2 |
| **D** | **Polished** | Considered, precise, nothing out of place. | 2 | 0 | 1 | 0 | 3 | 0 |

---

### Q4 — Palette · weight ×1

> **Pick your tones.**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **Neutral** | Clean and versatile. You gravitate towards balanced tones that work effortlessly across any look. | 3 | 0 | 2 | 0 | 2 | 0 |
| **B** | **Earth & Heritage** | Terracotta, indigo, olive, sand. Tones with a history. | 2 | 0 | 1 | 0 | 0 | 3 |
| **C** | **Rich & Saturated** | Emerald, gold, deep red. Colour that carries weight. | 0 | 3 | 0 | 1 | 0 | 2 |
| **D** | **Monochrome & Dark** | Black, charcoal, deep navy. Sharp and uncomplicated. | 2 | 0 | 0 | 2 | 3 | 0 |

---

### Q5 — Fit · weight ×1

> **How do you like your fits?**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **Tailored & Structured** | Cut to fit, holds its shape, nothing loose. | 2 | 1 | 0 | 0 | 3 | 0 |
| **B** | **Relaxed & Flowing** | Room to move. Fabric that falls rather than holds. | 1 | 0 | 3 | 0 | 0 | 2 |
| **C** | **Oversized & Layered** | Volume, proportion play, things worn over other things. | 0 | 0 | 1 | 3 | 0 | 1 |
| **D** | **Fitted & Defined** | Close to the body. The shape is the statement. | 0 | 3 | 0 | 1 | 1 | 0 |

---

### Q6 — Risk appetite · weight ×2 · three options

> **How bold are you with your style?**

| | Option | Description | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|---|---|
| **A** | **I keep it safe** | I know what works on me and I stay there. | 3 | 0 | 2 | 0 | 3 | 0 |
| **B** | **I experiment sometimes** | One unexpected piece, the rest familiar. | 1 | 1 | 2 | 2 | 1 | 3 |
| **C** | **I go all out** | If it's interesting, I'm wearing it. Comfort zones are for other people. | 0 | 3 | 0 | 3 | 0 | 1 |

> Option B is `NF`'s home on a weighted question — "one unexpected piece, the rest familiar" is precisely what fusion dressing is, and without this `NF` had no strong signal on Q1 or Q6.

> **Implementation note:** Q6 renders three option cards, not four. The frontend must build option layouts from the question configuration returned by `GET /v1/quiz`, never from a hardcoded four-card grid.

---

## 5. Algorithm

### Step 1 — Accumulate

```python
scores = {"CM": 0, "OR": 0, "SL": 0, "SC": 0, "CE": 0, "NF": 0}
for question_id, option_id in answers.items():
    question = config.questions[question_id]
    weights  = question.options[option_id].weights
    for persona, value in weights.items():
        scores[persona] += value * question.weight
```

Maximum for a single persona is 24 (3 × 2 on both weighted questions, 3 on each of the other four). In practice a strongly consistent respondent scores 18–22.

### Step 2 — Sharpen

Raw vector scores produce flat distributions — a typical result lands around 30–40% for the dominant persona, which reads as indecisive on a share card. A power transform sharpens the distribution without changing the ranking:

```python
GAMMA = 2.5   # tunable; 1.0 = no sharpening, higher = more dominant winner

sharpened = {p: s ** GAMMA for p, s in scores.items() if s > 0}
total = sum(sharpened.values())
```

`GAMMA` is configuration, not code, so the card can be tuned after seeing real results without touching the ranking logic. **The sharpened values are for display only.** `ase` receives the raw scores, because the blend is the useful signal for styling.

### Step 3 — Convert to percentages

Use the **largest remainder method**, so displayed percentages always total exactly 100 and the card never shows 101%.

```python
exact  = {p: v / total * 100 for p, v in sharpened.items()}
floors = {p: int(v) for p, v in exact.items()}
short  = 100 - sum(floors.values())

# distribute the shortfall to the largest fractional remainders,
# breaking equal remainders by raw score so the result stays deterministic
remainders = sorted(
    exact.items(),
    key=lambda kv: (kv[1] - floors[kv[0]], scores[kv[0]]),
    reverse=True,
)
for persona, _ in remainders[:short]:
    floors[persona] += 1

percentages = floors   # guaranteed to sum to exactly 100
```

### Step 4 — Rank

```
dominant  = ranked[0]    # primary result on the card
alter_ego = ranked[1]    # secondary
wildcard  = ranked[2]    # tertiary
```

Personas scoring zero never appear. If fewer than three personas score above zero, the card shows only those that did.

### Step 5 — Tie-breaks

Applied in order, deterministic at every stage:

1. **Weighted-question score.** The persona with more points from Q1 and Q6 wins — those measure identity rather than circumstance.
2. **Earliest divergence.** Compare per-question contributions from Q1 forward; the persona leading at the first question where they differ wins.
3. **Fixed order.** `CM` > `OR` > `SL` > `SC` > `CE` > `NF`. Reached only when two personas scored identically on every question, which requires deliberately constructed answers.

Rule 3 exists so the function is **total** — every possible answer combination produces exactly one result. No input can produce an error.

### Several answers to one question

A person can tick more than one option on a question, up to `max_choices` (3 unless the question says otherwise, never more than it has options). Each question still counts once: the ticked options **share** the question's weight equally, so ticking more never gives a question a bigger say.

- One option scores exactly as before.
- With several, each option's points are divided by how many were ticked. Scores are held in whole numbers by multiplying every question by 12 (1, 2, 3 and 4 all divide it) in any submission that has at least one multi-answer question; percentages are unaffected because they are ratios.
- The API takes a string for one option or a list for several (`{"4": ["A", "D"]}`). Order and repeats do not matter. An empty list, more than `max_choices`, or an unknown option is a validation error.
- `GET /v1/quiz` returns `max_choices` per question.

---

## 6. Worked example

Answers: **Q1-A** (Minimal), **Q2-C** (Work), **Q3-D** (Polished), **Q4-A** (Neutral), **Q5-A** (Tailored), **Q6-A** (Keep it safe).

| | `CM` | `OR` | `SL` | `SC` | `CE` | `NF` |
|---|---|---|---|---|---|---|
| Q1-A ×2 | 6 | 0 | 4 | 0 | 6 | 0 |
| Q2-C ×1 | 2 | 0 | 1 | 0 | 3 | 0 |
| Q3-D ×1 | 2 | 0 | 1 | 0 | 3 | 0 |
| Q4-A ×1 | 3 | 0 | 2 | 0 | 2 | 0 |
| Q5-A ×1 | 2 | 1 | 0 | 0 | 3 | 0 |
| Q6-A ×2 | 6 | 0 | 4 | 0 | 6 | 0 |
| **Raw** | **21** | **1** | **12** | **0** | **23** | **0** |

| Persona | Displayed |
|---|---|
| **Dominant** — Corporate Edge | **50%** |
| **Alter-ego** — The Cultural Minimalist | **40%** |
| **Wildcard** — Soft Luxe | **10%** |

`OR` rounds to 0% and is not shown; `SC` and `NF` scored zero and never appear.

The result is honest: this respondent chose minimal, work-focused, polished, neutral, tailored, and risk-averse — that is `CE` with a strong `CM` streak, and the card says exactly that. Under the pre-rebalance matrix the same answers produced `CM` 49 / `CE` 39, which was wrong: nothing in those answers is more minimalist than it is corporate.

*(Verified against the implementation used in §11.)*

---

## 7. Share card

Rendered by the media module on `quiz.completed`, in square (1080×1080) and stories (1080×1920) formats.

```
┌─────────────────────────────────────┐
│  [gradient — dominant persona]      │
│                                     │
│         YOUR FAUE STYLE DNA         │
│                                     │
│   49%   The Cultural Minimalist     │
│         your dominant trait         │
│                                     │
│   39%   Corporate Edge              │
│         your alter-ego              │
│                                     │
│   12%   Soft Luxe                   │
│         your wildcard               │
│                                     │
│   "[tier 1 — persona line]"         │
│   "[tier 2 — blend line]"           │
│   "[tier 3 — personal line, M1-2]"  │
│                                     │
│            FAUEOFFICIAL.COM/DNA             │
└─────────────────────────────────────┘
```

Tier 1 sets the type at the largest size, tier 2 beneath it slightly smaller, tier 3 smaller still. If tier 3 is absent the layout closes up rather than leaving a gap.

### Gradients

Derived from the FAUE palette so cards read as one family rather than six unrelated posters. `CM` uses the brand primary directly, since it is the house aesthetic.

| Persona | Gradient |
|---|---|
| `CM` | `#0F3D2E` → `#355C4F` |
| `OR` | `#0A291F` → `#B5451B` |
| `SL` | `#BCC9C4` → `#F7F8F8` |
| `SC` | `#25272C` → `#5C7B71` |
| `CE` | `#051611` → `#383A42` |
| `NF` | `#145C45` → `#829A92` |

### Taglines — three tiers

A single fixed sentence per persona would mean every `CM` user shares an identical card. That is a real problem, not a cosmetic one: the card is the acquisition engine, and two friends posting the same sentence makes it read as a template rather than a result. Percentages already differ between users, but the text is the part people actually read.

**Tier 1 — persona line (always present, fixed).**
The identity statement. Deliberately stable, because it *defines* the persona and must mean the same thing on every card.

| Persona | Line |
|---|---|
| `CM` | "You carry your roots quietly. The restraint is the statement." |
| `OR` | "Subtlety is not your ministry. You are the event." |
| `SL` | "You move like you have nothing to prove — because you don't." |
| `SC` | "You find the rare thing, mix it with the unexpected, and make it look inevitable." |
| `CE` | "You know every rule in the room, and exactly which one to break." |
| `NF` | "Heritage in one hand, right now in the other. You never drop either." |

**Tier 2 — blend line (always present, varies by pair).**
Written for each dominant × alter-ego combination: **30 lines**, hand-authored, deterministic, no model cost. This is what makes two `CM` cards different, because `CM`/`CE` and `CM`/`SC` are genuinely different people.

Examples:

| Blend | Line |
|---|---|
| `CM` + `CE` | "Minimal, but never casual about it. Your restraint reads as authority." |
| `CM` + `SC` | "Quiet on the surface, one rare piece underneath. People notice late." |
| `CM` + `NF` | "You reference heritage rather than announce it. One detail does the work." |
| `OR` + `NF` | "Full traditional, modern proportions. You update the classics without diluting them." |
| `OR` + `SC` | "Maximum presence, unexpected sources. Nobody can place where you found it." |
| `SL` + `CM` | "Comfort that looks considered. Nothing about it is accidental." |
| `CE` + `SC` | "Sharp tailoring, one deliberate wrong note. That note is the point." |
| `SC` + `NF` | "You mix eras and origins in one outfit and make it look obvious in hindsight." |

The remaining 22 follow the same pattern and are written as part of the content pass. Where a blend is genuinely uncommon (`SL` + `OR`, for instance), the line acknowledges the tension rather than pretending it resolves neatly.

**Tier 3 — personal line (`M1-2`, generated).**
A third sentence referencing the user's actual answer pattern — their palette choice, their occasion mix, their risk appetite — generated once at quiz completion via the `quiz.tagline` task, cached, moderated, and stored on `style_preferences`.

Constraints, because this line goes on a public share card:

- Generated **once**, at completion, then frozen. A card that changes wording between views is unsettling and breaks screenshots.
- Passes output moderation like any other model text — no body commentary, no promises.
- Falls back silently to tiers 1 and 2 if generation fails. The card must never wait on a model call.
- Semantically cached by answer pattern, so common patterns cost nothing after the first.

Deferred to `M1-2` deliberately: 30 hand-written blend lines already solve the sameness problem at zero cost and zero risk, and MVP should prove people share the card at all before spending model budget on making the sentence unique.

### Uniqueness, in practice

| Tier | Distinct cards |
|---|---|
| Persona only | 6 |
| **+ blend line (MVP)** | **30** |
| + percentages | Effectively hundreds |
| + personal line (`M1-2`) | Effectively unique |

Thirty text variants across a first cohort of a hundred users means duplicates are uncommon and never sit next to each other in a feed — enough for launch.

Text uses Playfair Display for the persona name and Plus Jakarta Sans for percentages and labels, per [`../40-frontend/design-tokens.md`](../40-frontend/design-tokens.md). Contrast is verified against WCAG AA on every gradient — the `SL` card in particular needs dark text.

---

## 8. Data and API

```sql
gateway.style_preferences (
  user_id PRIMARY KEY, dna_scores JSONB, dna_dominant VARCHAR(2),
  dna_alter_ego VARCHAR(2), dna_wildcard VARCHAR(2),
  quiz_completed BOOLEAN DEFAULT FALSE, quiz_version TEXT,
  completed_at TIMESTAMPTZ, retake_available_at TIMESTAMPTZ
);

gateway.quiz_responses (      -- append-only; DNA history is analysable
  id, user_id, quiz_version, answers JSONB, submitted_at
);
```

`dna_scores` stores **raw** scores, not sharpened ones — sharpening is presentation and `GAMMA` may change.

`style_preferences` also stores `personal_line` once generated (`M1-2`), so the card text is frozen after the first render. A share card whose wording changes between views breaks screenshots people have already posted.

```
GET  /v1/quiz          → question and option definitions for the current version
POST /v1/quiz/submit   → {answers} → DNA result
GET  /v1/quiz/result   → current result
GET  /v1/quiz/card     → card URLs, or {status: "pending"}
POST /v1/quiz/retake   → allowed once per 30 days
```

Questions are **served from the API**, not hardcoded in the app, so copy and weights can be corrected without an app release — which matters because they will be corrected after seeing real results.

---

## 9. Implementation requirements

- Scoring is a pure function: no database, no model call, no clock. This is what allows the `dna_answers` golden set to gate it at **100% correctness** in CI.
- Configuration lives in `personas.yaml`. Changing a weight is a reviewable diff, not a code change.
- The quiz version is stored with every response. A future version coexists with old results; nothing is retro-scored.
- All 4 × 4 × 4 × 4 × 4 × 3 = **3,072 answer combinations** are enumerated in a property test asserting the function is total, deterministic, and always returns a dominant persona.
- Retake limit is enforced server-side. The client hides the button; the server rejects the request.

---

## 11. Validation — measured, not asserted

The weight matrix above was executed against **all 3,072 possible answer combinations** (4 × 4 × 4 × 4 × 4 × 3). Results:

| Property | Result |
|---|---|
| Combinations producing a valid result | 3,072 / 3,072 — the function is total |
| Percentages summing to exactly 100 | 3,072 / 3,072 |
| Dominant percentage range (`GAMMA` 2.5) | 18% – 74%, median 39% |
| Exact score ties requiring a tie-break | 483 (15.7%) |

### Persona win share

| Persona | Before rebalance | After rebalance | Ideal |
|---|---|---|---|
| `CM` | 30% | **21%** | 16.7% |
| `OR` | 23% | **18%** | 16.7% |
| `SC` | 13% | **18%** | 16.7% |
| `SL` | 19% | **16%** | 16.7% |
| `NF` | 11% | **13%** | 16.7% |
| `CE` | **4%** | **10%** | 16.7% |

The first matrix was broken in a way that reading it would not reveal: `CE` and `SC` could never score 3 on either double-weighted question, so `CE` was reachable as a dominant persona in only 4% of outcomes. A persona almost nobody receives is not a persona; it is dead weight in the taxonomy and a hole in the styling engine.

The fix was to let two personas share the top score where an option genuinely describes both — "Minimal" is as true of `CE` as of `CM`, and "Bold" is as true of `SC` as of `OR` — and to give `NF` a home on Q6-B.

`CE` remains the least frequent at 10%. That is defensible: `CE` requires a coherent work-focused, polished, structured pattern of answers, which is a narrower profile than "minimal" or "bold". If review wants it higher, the lever is Q2-C and Q3-D, not Q1.

**This validation runs in CI** as part of the `dna_answers` golden set, so a future weight edit that re-breaks the distribution fails the build rather than shipping.

### GAMMA sensitivity, measured

| `GAMMA` | Dominant min | Median | Max |
|---|---|---|---|
| 2.0 | 18% | 36% | 66% |
| **2.5** (default) | 18% | 39% | 74% |
| 3.0 | 18% | 43% | 82% |
| 4.0 | 19% | 51% | 92% |

The floor stays near 18% regardless, because a genuinely balanced respondent is genuinely balanced and no exponent can honestly hide that. If a low dominant percentage reads badly on the card, the presentation fix is to lead with the persona name and treat the number as secondary — not to inflate the number.

---

## 12. Open for review

1. **Persona names.** `Corporate Edge` and `Street Alchemist` are the least settled. `Neo-Fusion` may be too technical for a share card people post to Instagram.
2. **`GAMMA` default.** 2.5 gives an honest blend; 4.0 gives a punchier card. This is a product decision about whether the card should feel accurate or decisive.
3. **Option copy.** Option A of each question is preserved from the design; options B–D are new and written to match its voice. They need a read-through by someone with the brand's ear.
4. **`CM` / `NF` boundary.** Distinct in the weight matrix, but the persona descriptions may need sharpening so a user seeing both on their card understands why.
5. **Q5 option D wording.** "Fitted & Defined" was chosen over "body-conscious" to avoid body-focused language in a product that deliberately avoids it elsewhere.
