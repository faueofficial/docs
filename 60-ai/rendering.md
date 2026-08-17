# Look Rendering

**Stage:** MVP · **ADRs:** [0009](../80-adr/0009-pluggable-look-rendering.md), [0018](../80-adr/0018-generative-rendering-default.md)

The image a user sees is the product's face. Three strategies produce it, behind one interface, with `generative` as the default.

---

## 1. Why three

| Strategy | Strength | Weakness |
|---|---|---|
| `generative` | Works with an empty vault, visually striking, matches the design | Per-image cost, 10–40 s, may not match owned items exactly |
| `composite` | Free, fast, honest — these are the user's actual clothes | Needs a populated vault; less striking |
| `hybrid` | Real where possible, generated where not | Most complex; hardest to evaluate without baselines |

`generative` ships first because every user's first session has an empty vault, and that is exactly when the product must convince. The others stay implemented and selectable, and the decision is revisited on measured save rate, share rate, and cost per look.

---

## 2. The interface

```python
@dataclass
class LookSpec:
    look_id: UUID
    items: list[LookItem]          # name, role, attributes, optional vault image
    occasion: str | None
    persona: str                   # dominant Style DNA persona
    palette: list[LabColor]        # from the colour prior
    silhouette_notes: list[str]    # derived constraints, never measurements
    weather: WeatherContext | None

class ImageRenderer(Protocol):
    strategy: Literal["generative", "composite", "hybrid"]
    async def render(self, spec: LookSpec) -> RenderResult: ...
```

`LookSpec` is deterministic output from the pipeline. **The renderer never sees raw user text** — the note a user typed influenced assembly, but it does not reach the image prompt. That is both a quality control and an injection defence.

---

## 3. Generative

### Prompt construction

Built from `LookSpec` fields, never concatenated from user input:

```
A styled outfit flat-lay on a neutral background:
{item.role}: {item.name}, {item.color_name}, {item.fabric}
...
Occasion: {occasion}. Aesthetic: {persona_style_descriptor}.
Palette: {palette_description}.
No human faces. No text. No logos. Editorial fashion photography.
```

Negative constraints are explicit and non-negotiable: no faces, no text, no brand marks, no bodies in revealing poses.

### Why no people

Looks render as flat-lays or on abstract mannequin forms, not on photorealistic humans.

Rendering a person means choosing a body, a skin tone, and a face — and every choice is wrong for most users, in ways that range from alienating to offensive. Diffusion models also carry well-documented biases in exactly this territory. Flat-lays sidestep the whole class of problem and read as editorial rather than uncanny.

If the product later renders on a body, it must be the **user's own** body with explicit consent, which is virtual try-on and a separate M1-2 feature with its own design.

### Provider

Selected at implementation against cost, latency, African fashion fidelity, and commercial-use terms. Candidates include fal, Replicate, and image-capable models routed through OpenRouter. The choice is configuration behind `ImageRenderer`, and it is an open item in [`../90-meta/doc-status.md`](../90-meta/doc-status.md).

Non-negotiable when choosing: the provider's terms must permit commercial use of outputs, and the provider must not train on submitted prompts or images.

### Cost and latency

| Property | Expectation |
|---|---|
| Cost per image | Target ≤ $0.02, ceiling $0.05 |
| Latency | 10–40 s, hence the job model |
| Retry | Once on failure, then fall through to `composite` |
| Concurrency | Capped per worker so one user cannot starve the queue |

Cost per generated look is the metric that decides whether `generative` stays the default. If it exceeds target, the answer is switching the renderer, not trimming budgets elsewhere.

---

## 4. Composite

Deterministic server-side layout of the user's real vault photographs.

```
select item images (already PII-redacted derivatives)
  → remove backgrounds (on-device model, no vendor call)
  → arrange by role: top, bottom, outerwear, shoes, accessories
  → apply FAUE layout template with persona-tinted background
  → compose to 1080×1350 with the attribution mark
```

Fast (under two seconds), free, and completely honest — every pixel is something the user owns. Quality depends on their photographs, which is the trade.

---

## 5. Hybrid

Real vault images where the item exists, generated fill where it does not, with a **visible distinction** so the user always knows which pieces they own.

```
items owned      → composite treatment
items suggested  → generated, marked "suggested piece"
```

The marking is not optional. A user who buys a garment because they thought they already owned it has been misled by the interface.

---

## 6. Guardrails

Applied to every strategy, not only the generative one:

| Guard | Check |
|---|---|
| Input safety | Vault images already passed the PII pipeline; re-verified before composition |
| Output NSFW | Every rendered image classified before storage |
| No likeness | Generative output must contain no recognisable face; rejected and regenerated if it does |
| No text or logos | Rejected on detection — generated text is almost always garbled and reads as broken |
| Provenance | Every render records strategy, model, prompt version, and seed |
| Attribution | Generated renders carry the "generated by FAUE AI" mark, as the design specifies |

A render failing a guard is retried once with a stricter prompt, then falls back to `composite`.

---

## 7. Attribution

The design's `690:1477` frame carries "This was generated by Faue Artificial Intelligence". That string is a **product requirement**, not decoration.

Users are being shown clothing they may go and buy or have made. They must know when a garment is a rendering rather than a photograph of a real product. Rules:

- Generated and hybrid renders always carry the mark, in the app and in the share image.
- Composite renders do not — they are photographs of real items.
- The mark survives sharing. A screenshot posted to Instagram still says what it is.

---

## 8. Storage

| Property | Value |
|---|---|
| Format | WebP, JPEG fallback |
| Dimensions | 1080×1350 (4:5, the best-performing social ratio) |
| Share variant | 1080×1080 square and 1080×1920 stories |
| Preview variant | 400 px wide, under 60 KB, for lists |
| Retention | Life of the look; unsaved looks pruned after 90 days |
| CDN | Immutable, content-hashed URLs |

Preview variants matter more than they look. Nigerian mobile data is metered, and a vault grid that loads full renders costs users real money.

---

## 9. Choosing between strategies

Not by argument. The comparison runs as a shadow evaluation and then an experiment:

| Metric | What it decides |
|---|---|
| Save rate | Which renders users actually want |
| Share rate | Which renders are worth showing others |
| Regenerate rate | Which renders miss |
| Cost per look | Whether the quality is affordable |
| Render failure rate | Whether it is reliable |
| Time to first look | Whether the wait is tolerable |

Bias in the reading: `composite` will win on cost and speed and lose on first-session appeal. The honest question is whether `generative`'s cold-start advantage is worth its price once vaults are populated — which is a question about month two, not week one.
