# AI Quality and Evaluation

**Stage:** MVP

How FAUE knows whether a model change made things better or worse. Without this, "we swapped the model" is an untestable claim and quality drifts silently.

---

## 1. Offline evaluation — the deploy gate

Golden sets live in [`../60-ai/eval-sets/`](../60-ai/eval-sets/), versioned and human-labelled. They run in CI on any change to a prompt, model configuration, rule, ranking, or guardrail.

| Set | Size | Measures | Gate |
|---|---|---|---|
| `dna_answers` | 200 | Quiz scoring correctness | **100%, hard block** |
| `pii_images` | 100 | Face recall, EXIF strip, OCR redaction | **Face ≥ 0.98, EXIF 100%, hard block** |
| `spree_safety` | 300 | Jailbreak, injection, off-topic, PII, body, medical, purchase promises | **100% correct refusals, hard block** |
| `render_safety` | 100 | NSFW filtering, no-likeness compliance | **100%, hard block** |
| `fabric_match` | 150 | Fabric type accuracy; style precision@5 | Type ≥ 85%, P@5 ≥ 0.70 |
| `look_rank` | 100 | nDCG@10, precision@5 against stylist ranking | No regression beyond 5% |
| `spree_quality` | 150 | Groundedness, helpfulness | Groundedness ≥ 95% |

**Safety sets are absolute.** A single failure in `spree_safety`, `pii_images`, or `render_safety` blocks the merge. There is no "acceptable" jailbreak rate and no override.

**Quality sets gate on regression**, not an absolute bar — measured against the current production configuration, so a change that makes things worse fails even if it clears some arbitrary threshold.

### Labelling

Ground truth is content work, not engineering work, and it must start early — with no labels there is no evaluation. Process and worked examples in [`../50-data/labeling-guide.md`](../50-data/labeling-guide.md).

### LLM-as-judge

Acceptable for groundedness and tone at scale. **Never the sole gate for safety.** Calibrated against human labels on a sample each cycle; a judge that drifts silently is worse than no judge, because it produces confident numbers that mean nothing.

---

## 2. Online evaluation

### Shadow mode

The standard promotion path for any ranker, renderer, or embedding model. The new component runs alongside production, its output scored and logged, never served. Promotion requires a week of shadow data.

### Interleaving

For ranking comparisons, results from two rankers are interleaved in one list and clicks attributed. Far better signal than a split test at low traffic — which FAUE will have for months — because every user contributes to the comparison.

### A/B testing

Deterministic bucketing by `hash(user_id + experiment_id)`. Exposure logged as an event. Minimum sample and duration declared **before** starting, so nobody peeks and calls it early. Guardrail metrics can halt an experiment automatically.

### Implicit feedback — the real signal

| Signal | What it indicates |
|---|---|
| Save rate | The look was worth keeping |
| **Regenerate rate** | The first answer missed |
| Share rate | Worth showing others |
| Wear-log rate | Worn in the real world — the strongest signal available |
| Agent accept rate | The suggestion was right for the day |
| Fabric correction rate | Classification was wrong |

**Regenerate rate is the sharpest early signal.** It requires no extra user effort to express, unlike a save, and it appears immediately. Watch it first.

Offline metrics only predict these. When they disagree, the online signal is right.

---

## 3. Attribution

Every look records `model_id`, `prompt_version`, `strategy_version`, and `renderer`. Every model call records the same plus tokens, cost, latency, cache hit, and fallback depth.

That makes quality attributable: a drop in save rate after a release can be traced to the exact prompt version responsible, rather than argued about.

---

## 4. Drift

| Type | Watched via | Signal |
|---|---|---|
| Embedding drift | Candidate-set overlap and score distribution week over week | Catalogue or model changed underneath the rankings |
| Input drift | Fabric type mix, image quality, spree intent mix | New usage patterns before they become complaints |
| Output drift | Length, refusal rate, groundedness over time | Provider changed a model behind a stable identifier |
| Data quality | Embedding coverage, dead links, duplicates | Silent degradation of the pool |

**Output drift is the one people miss.** Providers update models behind stable names. The identifier does not change; the behaviour does. A weekly canary run of a fixed prompt set against each production model catches it.

---

## 5. The feedback loop problem

Recommendations train on clicks, and clicks are caused by recommendations. Left alone, a ranking model learns that whatever was shown first is best.

Mitigation, in place from day one:

```sql
ase.look_impressions (user_id, look_id, position, candidate_set_hash, ranker_version, shown_at)
```

Recording served position and candidate set with every impression is cheap now and **impossible to reconstruct later**. Without it, position and exposure bias cannot be corrected for and every future ranking model inherits the bias of the first heuristic.

---

## 6. Human review

Three streams into one queue:

1. Flagged sessions — guardrail trips, injection attempts.
2. Low-rated outputs — `not_my_style`, thumbs down, high regenerate.
3. A random sample of normal sessions, so the queue is not only failures.

Reviewers label in the admin console. Verdicts feed back into the golden sets, which is what keeps evaluation current instead of frozen at launch.

**A review queue nobody works is a feedback loop that has silently stopped.** Queue depth is a monitored metric.

---

## 7. Cadence

| When | What |
|---|---|
| Every commit touching prompts, models, rules, guardrails | Full offline suite |
| Every deploy | Safety sets re-run against production configuration |
| Daily | Online metrics review |
| Weekly | Drift check, canary run, review queue triage |
| Monthly | Judge calibration against human labels; golden set refresh from production cases |
| Quarterly | Full re-label of a sample; retire stale cases |

---

## 8. Tooling

Langfuse for LLM traces, prompt versions, cost, and evaluation runs — adopted from the start rather than retrofitted, because attaching it to an existing system means backfilling nothing and losing the history that mattered.

Evaluation runs are stored with their configuration, so any historical result is reproducible.

---

## 9. What is deliberately not measured

- **Aesthetic quality in the abstract.** There is no objective score for whether an outfit is good. Save, share, and wear rates are the proxies, and they are the honest ones.
- **Model benchmark scores.** How a model performs on public benchmarks says nothing about how it styles a Nigerian wedding outfit. Only FAUE's own sets count.
- **Latency of individual pipeline stages in production alerting.** Tracked for diagnosis, but the user-facing metric is end-to-end generation time; optimising a stage that is not the bottleneck is wasted work.
