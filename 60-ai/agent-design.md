# Agent Design

**Stage:** MVP (L0) · **Lives in:** `ase/app/agent/`

The proactive styling layer. It answers "what do I wear today?" before being asked, and gets better at it by watching what actually gets worn.

---

## 1. Autonomy levels

Graduated deliberately. Trust is earned before it is spent.

| Level | Behaviour | Requires | Stage |
|---|---|---|---|
| **L0** | Suggests on app open | Vault, DNA, weather | MVP |
| **L1** | Daily push at a chosen hour | Notify, scheduler, `agent_proactive` | M1-2 |
| **L2** | Triggered — weather shift, **cultural window** (`ase.context.occasions`), upcoming event, new pin, unworn item | Event stream | M3+ |
| **L3** | Planning — event prep, travel packing, aso-ebi coordination, tailor lead times | Calendar, tailor network | Y2 |

Each level is a separate consent decision. A user who wants an on-open suggestion has not agreed to a daily push, and treating those as the same thing is how apps earn notification opt-outs.

**L0 first because it cannot annoy anyone.** The user opened the app; a suggestion is welcome. L1 arrives uninvited and must therefore be good, which requires the wear data that L0 generates.

---

## 2. Memory

Three tiers, all inspectable, all user-editable.

| Tier | Contents | Source | Lifetime |
|---|---|---|---|
| **Profile** | Persona, fit preference, sizes, silhouette constraints | Quiz, body profile | Durable until changed |
| **Semantic** | Learned preferences — colours, silhouettes, formality, brands | Behaviour over time | Decayed continuously |
| **Episodic** | What was worn or suggested and the outcome | Wear log, agent runs | 90 days rolling |

```sql
ase.agent_memory (user_id, tier, key, value, confidence, decayed_at, updated_at)
```

Example semantic entries:

```
("semantic", "prefers_color_family", {"family": "earth", "weight": 0.7}, confidence 0.8)
("semantic", "avoids_silhouette",   {"silhouette": "oversized"},          confidence 0.6)
("semantic", "formality_by_day",    {"mon": "business", "sat": "casual"}, confidence 0.5)
```

### Decay

Semantic confidence decays with a 90-day half-life. Someone who wore a lot of green in December should not be assumed to want green in June. Decay is applied on read, not by a batch job, so it is always current and costs nothing when the user is inactive.

### Inspectability

"Why did you suggest this?" answers from stored memory, not from a fresh prompt asking the model to explain itself. A re-prompted explanation is a plausible story, not a reason, and users can tell the difference the moment the story is wrong.

Users can view and correct learned preferences. Correcting one sets confidence to 1.0 with a manual flag, and it stops decaying.

---

## 3. The learning loop

```
suggestion → outcome → memory update → better suggestion
```

| Signal | Weight | Meaning |
|---|---|---|
| Wear logged | Highest | Actually worn in the real world |
| Suggestion accepted | High | Chose it |
| Look saved | Medium | Liked it enough to keep |
| Suggestion dismissed | Medium negative | Not today |
| Regenerated | Medium negative | Missed |
| `not_my_style` | High negative | Explicitly wrong |
| Ignored | Weak negative | Ambiguous — could mean unread |

**Ignoring is weak evidence.** A suggestion nobody opened may have arrived during a meeting. Treating silence as rejection makes the agent skittish and it converges on suggesting nothing interesting.

### Cold start

| Wears logged | Weighting |
|---|---|
| 0 | DNA 0.6, aspiration 0.4, behaviour 0.0 |
| 1–10 | Behaviour rises gradually |
| 10–40 | Transition |
| 40+ | DNA 0.2, aspiration 0.3, behaviour 0.5 |

Keeping the three vectors separate makes this a configuration change rather than a re-embed, and it makes the agent's reasoning decomposable.

---

## 4. Suggestion generation

```
trigger fires
  → check consent (personalization; agent_proactive for L1+)
  → gather context:
        weather for geohash5 (if consented)
        day of week, known occasions
        wear log — what is in rotation, what is neglected
        style context (DNA + aspiration + behaviour)
  → generate through the standard look pipeline, biased toward:
        + items owned but rarely worn
        + occasion appropriateness for the day
        + weather suitability
        − items worn in the last 3 days
  → store agent_runs with the rationale
  → L0: return on open   L1+: emit agent.suggestion.ready → notify
```

### The neglected-item bias

The agent deliberately favours things the user owns but does not wear. It is the clearest value the product can deliver — "you already own this and it works" is more useful, more surprising, and cheaper than any recommendation to buy something.

---

## 5. Timing

L1 sends at a user-chosen hour, defaulting to 07:00 WAT — early enough to influence what they wear, late enough not to wake them.

Constraints:

- Quiet hours respected absolutely.
- One suggestion per day maximum, regardless of triggers.
- Skip if the user already generated a look today; they have an answer.
- Skip after three consecutive ignores, and re-engage in a week. An agent that keeps talking to someone who has stopped listening gets muted permanently.

That last rule matters more than it seems. Notification opt-out is nearly irreversible, so backing off is cheaper than pushing through.

---

## 6. Explainability

Every suggestion carries a rationale composed from stored facts:

> *"It's 32° and humid today, so I picked the linen shirt — you haven't worn it in three weeks and it works with the wide-leg trousers you wore on Saturday."*

Built from: weather, wear-log recency, item pairing, and prior wear. Every clause is traceable to data. The model phrases it; it does not invent the reasons.

If the rationale cannot be composed from facts, the suggestion is shown without one rather than with a fabricated explanation.

---

## 7. Failure modes and guards

| Failure | Guard |
|---|---|
| Repetitive suggestions | Track suggested item sets, penalise recent repeats |
| Weather-inappropriate | Weather is a hard filter, not a soft signal |
| Suggesting worn-yesterday items | 3-day recency suppression |
| Suggesting into an empty vault | L0 falls back to fabric or generative looks |
| Over-notifying | One per day, quiet hours, three-ignore backoff |
| Learning from a single outlier | Confidence thresholds; no single event moves a preference far |
| Stale learning after a style change | Decay, plus a retake of the quiz resets profile-tier memory |

The quiz retake case is worth noting: someone whose style genuinely changed will retake the quiz, and the agent must respect that over eighteen months of accumulated behaviour.

---

## 8. Privacy

- Runs only with `personalization`; L1+ additionally requires `agent_proactive`.
- Memory is deleted on erasure like any other personal data.
- Location is coarse; the agent never knows where a user is beyond a city-scale geohash.
- Memory contents are visible and editable — nothing is learned in secret.

---

## 9. Measuring it

| Metric | Target |
|---|---|
| Accept rate | ≥ 20% |
| Wear-log rate after accept | ≥ 40% |
| Dismiss rate | ≤ 40% |
| Ignore rate | ≤ 40% |
| Notification opt-out attributable to the agent | ≤ 2% monthly |
| Neglected items brought back into rotation | Tracked; the clearest value proof |

The last one is the metric that would convince a sceptical user the product works: how many things you already owned did FAUE get you wearing again.
