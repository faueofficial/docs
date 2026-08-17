# Model Plane

**Stage:** MVP · **Lives in:** `ase/app/models/` · **ADRs:** [0006](../80-adr/0006-openrouter-tier-addressed-llms.md), [0007](../80-adr/0007-pluggable-embeddings-self-hosted-default.md), [0008](../80-adr/0008-closed-set-model-policy.md), [0009](../80-adr/0009-pluggable-look-rendering.md)

Every model call in FAUE goes through this layer. **No vendor SDK is imported outside `ase.models`** — that single rule is what makes providers swappable, costs measurable, and PII containable.

---

## 1. Three planes, three interfaces

```python
class LLMProvider(Protocol):
    async def complete(self, req: LLMRequest) -> LLMResponse: ...
    async def stream(self, req: LLMRequest) -> AsyncIterator[LLMChunk]: ...

class EmbeddingProvider(Protocol):
    model_id: str
    dim: int
    modalities: set[Literal["text", "image"]]
    async def embed_text(self, texts: list[str]) -> list[Vector]: ...
    async def embed_image(self, images: list[ImageRef]) -> list[Vector]: ...

class ImageRenderer(Protocol):
    strategy: Literal["generative", "composite", "hybrid"]
    async def render(self, spec: LookSpec) -> RenderResult: ...
```

---

## 2. LLM plane

### Task addressing

Application code names a **task**. Configuration resolves task → tier → an ordered list of models.

```python
result = await router.run("look.reasoning", context=ctx)   # never a model name
```

Model identifiers change constantly. A slug hardcoded in a service is a future outage, and finding every occurrence during an incident is not a task anyone wants at 2 a.m.

### Configuration

```yaml
# ase/app/models/config/models.yaml
providers:
  openrouter:
    base_url: https://openrouter.ai/api/v1
    zdr_only: true              # zero-data-retention providers only, enforced per request
    require_no_train: true
    headers:
      X-Title: FAUE
      HTTP-Referer: https://faue.app

tiers:
  reasoning:  ["<primary>", "<fallback-1>", "<fallback-2>"]
  fast:       ["<primary>", "<fallback-1>"]
  vision:     ["<primary>", "<fallback-1>"]      # image input + tool calling required
  cheap_bulk: ["<primary>", "<fallback-1>"]

tasks:
  look.stylist:        { tier: reasoning,  max_tokens: 1200, temp: 0.7, structured: true }
  look.reasoning:      { tier: fast,       max_tokens: 300,  temp: 0.6, cache: semantic }
  look.rerank:         { tier: fast,       max_tokens: 400,  temp: 0.2, structured: true }
  fabric.classify:     { tier: vision,     max_tokens: 100,  temp: 0.0, structured: true }
  fabric.reasoning:    { tier: fast,       max_tokens: 300,  temp: 0.5, cache: semantic }
  spree.chat:          { tier: vision,     max_tokens: 800,  temp: 0.6, tools: true, stream: true }
  spree.intent_guard:  { tier: cheap_bulk, max_tokens: 20,   temp: 0.0 }
  agent.daily_brief:   { tier: fast,       max_tokens: 250,  temp: 0.5 }
  quiz.tagline:        { tier: fast,       max_tokens: 60,   temp: 0.8, cache: semantic }
  catalog.autotag:     { tier: cheap_bulk, max_tokens: 150,  temp: 0.0, batch: true }   # M1-2

budgets:
  user_daily_usd:   0.50
  task_monthly_usd: { look.stylist: 60, spree.chat: 30, look.reasoning: 20 }
  global_monthly_usd: 150
```

Tier contents are deliberately left as placeholders. They are chosen at implementation time against the current OpenRouter catalogue and re-evaluated regularly — writing specific slugs into a document guarantees the document is wrong within months.

### Call sequence

```
resolve task config
  → check consent (ai_processing)          → refuse cleanly if absent
  → redact PII from inputs                  → never leaves un-redacted
  → semantic cache lookup                   → return on hit
  → budget check (user, task, global)       → template path if exceeded
  → provider call with timeout
      → on 5xx / timeout / rate limit → next model in tier
      → circuit breaker per model
      → tier exhausted → TEMPLATE PATH
  → validate structured output              → one retry, then template path
  → output moderation
  → log to ase.model_calls
```

### Template paths

Every model-backed feature has a non-model form. The product must remain usable with the model plane entirely down.

| Task | Template path |
|---|---|
| `look.stylist` | Heuristic assembler: category coverage, colour-prior scoring, occasion match |
| `look.reasoning` | Rule-derived sentence from item attributes and occasion |
| `look.rerank` | Heuristic score order |
| `fabric.classify` | Ask the user to pick the fabric type — the UI already supports it |
| `fabric.reasoning` | Pre-written reasoning per style-fabric pair from the style library |
| `spree.chat` | "I can't answer that right now" with a link to generation |
| `agent.daily_brief` | Suggestion without narration |
| `quiz.tagline` | The persona's static tagline |

`fabric.reasoning`'s template path is genuinely good, because the style library already carries per-fabric reasoning as content. That is not a coincidence — it was written that way so the degraded path would be acceptable.

### Circuit breaker

Per model: opens after 5 failures in 60 seconds, half-open probe after 30 seconds, closes after 3 consecutive successes. An open breaker skips straight to the next model rather than waiting for a timeout on every request.

---

## 3. Embedding plane

Default is **self-hosted open-CLIP / SigLIP** inside `ase`. Adapters exist for HuggingFace Inference, Voyage, Cohere, and Gemini, selected per environment.

### Provider economics

The choice inverts between hosts, which is exactly why it is configuration:

| Host | Cheaper option | Why |
|---|---|---|
| Railway | Hosted API | Idle RAM is billed continuously; a resident 3 GB model costs money while doing nothing |
| VPS | Self-hosted | Fixed monthly cost, unlimited calls |

**Break-even:** a self-hosted model on Railway needs roughly 2–4 GB resident, at roughly $10–20/month. A hosted API at typical pricing runs about $0.0001 per image. Self-hosting wins above roughly 150,000 embeddings a month. At MVP scale — 5,000 users × 30 vault items, plus pins — that is well under the line, so **hosted is correct on Railway and self-hosted becomes correct after a VPS migration**.

Recheck this arithmetic when either the vault count or the hosting decision changes; do not carry the conclusion forward as though it were permanent.

### Model versioning

Embeddings are not portable between models — different dimensions, different spaces. One row per subject per model:

```sql
PRIMARY KEY (item_id, model_id)
```

Migration: dual-write → shadow-evaluate on `look_rank` → flip reads by flag → soak a week → drop old rows. Never a big-bang re-embed.

**Dimension budget** matters more than it appears: 3072-d vectors cost roughly four times the storage and index memory of 768-d. Irrelevant at 1,000 items, decisive at 100,000. Default to 768–1024-d.

---

## 4. Where models act

```
1  RETRIEVE   ANN over embeddings                          MODEL
2  FILTER     hard constraints → the LEGAL POOL            RULES
3a POOL       everything that survived stage 2             RULES
3b STYLIST    model selects and assembles from the pool    MODEL
3c VALIDATE   ids must exist in the pool                   RULES
4  RANK       order assembled looks                        MODEL
5  RENDER     generative | composite | hybrid              MODEL / deterministic
6  EXPLAIN    "Why this works for you"                     MODEL
```

**The closed-set policy:** within the legal pool the model has full latitude — select, combine, reject, rank. It may not invent an item, price, brand, or style that does not exist. Rules define what is available and verify what came back is real; everything aesthetic in between belongs to the model.

Deterministic colour analysis (LAB distance, harmony relations, neutral anchors) is supplied to the stylist as a **prior, not a gate** — measured fact rather than hex values inferred from prose.

---

## 5. Cost control

| Mechanism | Effect |
|---|---|
| Semantic cache | Normalised prompt + input hash → response, in Redis, TTL per task |
| Precompute | Embeddings and tagging run in batch jobs, never in a request |
| User daily cap | $0.50; exceeded → template path + `ai.budget.exceeded` |
| Task monthly ceiling | Per task; exceeded → template path |
| Global kill switch | Per task, runtime-readable, no deploy needed |
| Renderer switch | `composite` removes image-generation cost entirely |

**Cache invalidation note:** the cache key includes the prompt version, so every prompt edit resets the hit rate to zero. Expect a temporary cost spike after any prompt change and do not mistake it for a regression.

Cost per active user is a tracked, alerted metric. Targets in [`../00-product/metrics.md`](../00-product/metrics.md).

---

## 6. Telemetry

Every call writes to `ase.model_calls`: task, tier, resolved model, prompt version, tokens in and out, cost, latency, cache hit, fallback depth, guardrail verdict, and trace id.

That row is what makes a user complaint answerable. "The look it gave me yesterday was terrible" resolves to the exact model, prompt version, candidate set, and tool calls behind it.

Traces additionally go to Langfuse, adopted from the start rather than retrofitted — see [`../70-ops/observability.md`](../70-ops/observability.md).

---

## 7. Privacy boundary

Nothing containing PII reaches a model.

- **Text** is redacted before egress; the redaction map stays server-side.
- **Images** pass the PII pipeline — safety classification, EXIF strip, face redaction, OCR redaction — before they can be model input.
- **Body data** is converted to abstract silhouette constraints in `gateway`; `ase` never holds a measurement to leak.
- **Providers** are restricted to a zero-retention, no-training allowlist enforced per request, and published as a sub-processor list.
- **Prompt and response retention** is FAUE-side only, TTL-bounded, tied to `ai_processing` consent.

---

## 8. Testing

No test makes a real model call. `RecordedLLMProvider` implements the same interface and replays fixtures, which keeps CI free, fast, and deterministic.

Structured-output parsing, fallback chains, circuit-breaker transitions, budget enforcement, and redaction are unit-tested directly. Quality is measured separately by the eval harness in [`ai-quality.md`](ai-quality.md), which runs against real models on a schedule rather than on every commit.
