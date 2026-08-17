# Labeling Guide

**Stage:** MVP · **Owner:** Content, with backend support · **Sets:** [`../60-ai/eval-sets/`](../60-ai/eval-sets/)

Golden sets gate every model, prompt, and ranking change. They are the only thing standing between "we changed the model" and "we broke the product without noticing".

**Ground truth is content work.** Engineering can build the harness; only someone who knows Nigerian fashion can say whether a Kaftan suits that Aso-Oke.

---

## 1. Rules that apply to every set

**Label before seeing model output.** Labelling after is contamination — you end up ratifying whatever the model already does, and the set stops being able to detect a regression.

**Record who labelled.** Systematic bias is only visible if it can be attributed.

**Two labellers on 20%.** Disagreement is resolved by discussion. Persistent disagreement means the rubric is ambiguous, not that someone is wrong — fix the rubric.

**Label what is correct, not what is achievable.** If the right answer is a style the library does not contain, label it correctly and log the gap. The set measures reality, not current capability.

**When genuinely unsure, skip.** An uncertain label is worse than no label, because it becomes a permanent false signal.

---

## 2. `fabric_match` — 150 cases

The most valuable and most expensive set. Encodes domain knowledge that exists nowhere else in machine-readable form.

### Per case

```jsonl
{"id": "fabric_0042",
 "image_ref": "cdn://eval/fabric/0042.jpg",
 "labels": {
   "fabric_type": "ankara",
   "motif_scale": "large",
   "weight": "medium",
   "dominant_colors": ["#C1442E", "#1B4D3E", "#E8B84B"],
   "suitable_styles": ["style_uuid_1", "style_uuid_2", "style_uuid_3"],
   "unsuitable_styles": ["style_uuid_9"],
   "notes": "Large repeating motif — panelled cuts destroy the pattern."
 },
 "labeler": "OA", "added": "2026-08-17"}
```

### How to label

1. **Fabric type** — what a fabric seller would call it. Uncertain between two? Skip the case.
2. **Motif scale** — small under 5 cm, medium 5–15 cm, large over 15 cm. This drives more matching decisions than the fabric type does.
3. **Weight** — how it would hang. Light drapes and falls; heavy holds shape; medium is between.
4. **Dominant colours** — up to three, sampled from the actual image, not from memory.
5. **Suitable styles** — three to five that a competent tailor would recommend, ordered best first.
6. **Unsuitable styles** — the ones that would genuinely go wrong. This is the more informative field, and it is usually skipped.
7. **Notes** — one line saying why.

### Sourcing

Photograph fabric at Balogun Market and from personal stock. Vary lighting, angle, and background deliberately — a set of perfectly-lit studio shots trains and evaluates for conditions that never occur on a user's phone.

Target coverage: 25 cases per fabric type, spread across motif scales.

---

## 3. `look_rank` — 100 cases

### Per case

```jsonl
{"id": "rank_0017",
 "profile": {"persona": "CM", "alter_ego": "CE", "occasion": "corporate",
             "constraints": {"favor": ["vertical_line"]}, "weather": {"temp_c": 31}},
 "candidates": ["item_1", "item_2", "...", "item_20"],
 "ranking": ["look_a", "look_b", "look_c", "..."],
 "notes": "look_a wins on occasion fit; look_c is well-composed but too casual.",
 "labeler": "OA"}
```

### How to rank

Given a profile and a candidate pool, rank the assembled looks as you would advise this person.

Criteria, in order:

1. **Occasion fit** — would this be right for where they are going? A beautiful look that is wrong for an Owambe ranks below a plain one that is right.
2. **Persona fit** — does it match how they said they dress?
3. **Composition** — colour, proportion, texture.
4. **Practicality** — weather, comfort, whether someone would actually wear it.

Rank all of them, including the bad ones. **The bottom of the ranking carries as much information as the top**, and a partial ranking teaches the metric nothing about what to avoid.

---

## 4. `spree_safety` — 300 cases

Mostly written by backend and red-team work, but content review matters for one category: whether a refusal reads acceptably to a user.

A refusal that is technically correct and feels rude is a product failure. Review the templates for tone as well as correctness.

---

## 5. `spree_quality` — 150 cases

### Rubric

| Dimension | 1 | 3 | 5 |
|---|---|---|---|
| **Groundedness** | Invents items or prices | Mostly grounded, one vague claim | Every claim traceable to a tool result |
| **Helpfulness** | Does not answer | Answers, generically | Answers specifically and usefully |
| **Cultural fit** | Reads as a Western app | Neutral | Clearly understands the context |
| **Tone** | Stiff or salesy | Fine | Sounds like a knowledgeable friend |

Groundedness is checked mechanically as well; human labels calibrate the automated judge each month.

Score all four. A 5 on helpfulness with a 1 on groundedness is a **failure**, not an average — a confidently wrong answer is worse than an unhelpful one.

---

## 6. `pii_images` — 100 cases

Backend-owned, but the sourcing rule matters to everyone: **only consented photographs from the team or licensed stock. Never user data.**

Label what is present — face count and positions, EXIF GPS present or absent, readable text and its content. The measurement is whether the pipeline caught it.

---

## 7. Cadence

| When | Work |
|---|---|
| Before launch | Build all sets to target size |
| Weekly | Add cases from production failures |
| Monthly | Calibrate the automated judge against human labels on a sample |
| Quarterly | Re-label a 10% sample to check drift; retire stale cases |

**Every production failure becomes a case.** That loop is what keeps evaluation attached to reality instead of to what the team imagined at launch.

---

## 8. Tooling

Labelling happens in the admin console under the `curator` role, not in a spreadsheet. The interface presents one case at a time, hides model output, records the labeller, and writes directly to the set.

Hiding model output is not a convenience — it is what prevents contamination, and a spreadsheet cannot enforce it.

---

## 9. Effort

| Set | Cases | Per case | Total |
|---|---|---|---|
| `fabric_match` | 150 | 4 min | 10 h |
| `look_rank` | 100 | 6 min | 10 h |
| `spree_quality` | 150 | 3 min | 8 h |
| `spree_safety` review | 300 | 1 min | 5 h |
| **Total** | | | **~33 hours** |

Roughly a week of focused work, or three weeks alongside other tasks. **It is on the critical path** — an AI release cannot be gated by an evaluation set that does not exist, and building it after launch means the first months of quality changes are unmeasured.

Start with `fabric_match`. It is the most valuable, the slowest to build, and the one that most directly protects users from a recommendation that costs them money at a tailor.
