# Guardrails

**Stage:** MVP · **Lives in:** `ase/app/spree/guardrails/`

Guardrails are **composable objects, not prompt text**. A guardrail expressed only as an instruction cannot be unit-tested and cannot be proven — which means it is a hope, not a control.

---

## 1. The chain

```
message
  → 1  InputSafety      images: NSFW, minors, non-apparel
  → 2  IntentScope      is this about fashion at all?
  → 3  InjectionScreen  instruction-shaped content in untrusted input
  → 4  BudgetCheck      per-session and per-day caps
  → [ model call with tools ]
  → 5  GroundingCheck   every claim traceable to a tool result
  → 6  OutputModeration body, medical, promises, PII echo
  → response
```

Guards 1–4 run **before** any expensive call. An off-topic message costs a single cheap classification, not a vision-model invocation.

Each guard returns `Allow`, `Refuse(reason, template)`, or `Modify(content)`. Refusals emit `ai.guardrail.tripped` and are logged with the session for review.

---

## 2. Guards

### 1 · InputSafety

Images only. Runs before any model sees them, and after the PII pipeline.

| Reject | Why |
|---|---|
| NSFW | Obvious |
| Minors | Absolute, no exceptions |
| Non-apparel | Off-purpose; also a common injection carrier |
| Unreadable | Wastes a model call and produces nonsense |

Rejected images are not persisted. Template: *"We can't work with that image. Try a clear photo of the piece itself."*

### 2 · IntentScope

The cheapest classifier available, temperature 0, twenty tokens: is this about fashion, clothing, style, fabric, or outfits?

`NO` returns a templated redirect with **no further model spend**. This is a cost control as much as a safety one — it is the difference between a fraction of a cent and a full vision call for every off-topic message.

Template: *"I'm here for styling. Ask me about an outfit, a piece you own, or fabric you're working with."*

### 3 · InjectionScreen

Heuristics plus a cheap classifier over untrusted content — user text and OCR output — looking for instruction-shaped phrasing, role markers, delimiter escapes, and system-prompt extraction attempts.

Flagged content is **not refused outright**. It is marked, delimited, and passed as data, with the session flagged for review. Refusing on suspicion produces false positives on innocent messages; the real defence is the read-only tool surface. See [`../10-architecture/prompt-injection.md`](../10-architecture/prompt-injection.md).

### 4 · BudgetCheck

Per session: 4 tool rounds, 8 tool calls, 30-second wall clock, token cap.
Per user per day: message count and token spend.

Exceeding returns a clear message with a reset time, and emits `ai.budget.exceeded`. Never a silent failure and never a silent charge.

### 5 · GroundingCheck

Runs on the model's answer. Every claim about a specific item, price, brand, or availability must correspond to a tool result from this session.

Unsupported claims are **stripped, not rewritten**. Rewriting invites a second hallucination in the repair.

If stripping leaves the answer incoherent, the whole response is replaced by a template and the session is flagged. That is rare and worth investigating when it happens.

### 6 · OutputModeration

| Blocked | Example | Why |
|---|---|---|
| Body commentary | "This flatters your shape" | FAUE styles clothes, not bodies |
| Weight or diet advice | Anything | Not our domain, actively harmful |
| Medical claims | "Good for back pain" | Not qualified |
| Purchase promises | "This will arrive Friday" | FAUE controls no logistics |
| Price claims without a tool result | "That's about ₦25,000" | Unsupported |
| PII echo | Repeating an email from an image | Leak |
| Competitor disparagement | — | Unnecessary |

A block replaces the answer with a template and flags the session.

---

## 3. The body rule

Absolute, and worth stating separately because it is the one a model will violate on its own initiative.

FAUE holds body shape and fit preference to make clothes fit better. It never comments on the body itself. No "flattering", no "slimming", no "for your shape", no "problem areas", no before-and-after framing.

Correct: *"The wide-leg cut works with the drape of this linen."*
Blocked: *"Wide-leg trousers balance your hips."*

The first is about the garment. The second is about the person, and it is not FAUE's place. This appears in every system prompt **and** in output moderation, because prompt instructions alone will not hold across thousands of generations.

---

## 4. Refusal taxonomy

| Code | Cause | Template |
|---|---|---|
| `off_topic` | IntentScope | "I'm here for styling…" |
| `unsafe_image` | InputSafety | "We can't work with that image…" |
| `budget_exceeded` | BudgetCheck | "You've reached today's limit. It resets at midnight." |
| `ungrounded` | GroundingCheck | "I don't have enough information to answer that accurately." |
| `body_commentary` | OutputModeration | "Let me focus on the pieces instead." |
| `out_of_capability` | Requested an action | "I can't do that from here — you can do it in the app." |
| `unsafe_output` | OutputModeration | "I can't help with that." |

Templates are warm and brief. A refusal is a normal part of a conversation, not an error screen.

---

## 5. Testing

Each guard is unit-tested independently against its slice of `spree_safety`, plus a full-chain integration test.

```python
def test_body_commentary_blocked():
    result = OutputModeration().check("Wide-leg trousers balance your hips.")
    assert result.refused
    assert result.reason == "body_commentary"
```

`spree_safety` is a **hard blocker** at 100%. Every real bypass found in production is added to the suite; the set only grows.

Guards are also tested for **false positives** — an over-eager guard that refuses legitimate styling questions is a product failure, even though it looks safe in the metrics.

---

## 6. Monitoring

Watch trip rate by guard and by category. Three patterns, three different causes:

| Pattern | Likely cause |
|---|---|
| Sustained rise from few users | Deliberate attempts; consider account-level rate limiting |
| Broad, sudden rise | False-positive regression after a guardrail change |
| Gradual rise | Legitimate usage the intent classifier does not recognise |

**Never loosen a guardrail to clear an alert.** Add the cases to the eval set, fix properly, let CI prove it. The third pattern is fixed by updating the classifier, not by widening what is permitted.

---

## 7. Review queue

Flagged sessions, low-rated answers, and a random sample of normal sessions route to the admin review queue. Reviewers mark each correct, false positive, or missed, and their verdicts feed the golden sets.

Queue depth is monitored. An unworked queue means the loop that keeps guardrails current has stopped, and the guardrails begin to rot from the day that happens.
