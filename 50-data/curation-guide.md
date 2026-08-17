# Curation Guide

**Stage:** MVP · **Owner:** Content (Oladunni) · **Tool:** admin console, `curator` role

The working process for building and maintaining FAUE's content. Written for the person doing the work, not for an engineer reading about it.

---

## 1. What content work covers

| Area | Stage | Effort |
|---|---|---|
| Style library — 30 styles, tags, images, reasoning | MVP | **Largest single task** |
| Accessory pairings — 20–30 items | MVP | Medium |
| Quiz copy review | MVP | Small, but blocking |
| Eval set labelling — `fabric_match`, `look_rank` | MVP | **Ongoing, on the critical path** |
| Tailor licensing outreach | MVP | Relationship work, weeks |
| Product catalogue — 500 items | M1-2 | Large |

Two of these cannot be done by engineering and gate the launch: the style library and the two stylist-labelled eval sets. They should start before the code that consumes them is finished.

---

## 2. Style library workflow

### Adding a style

1. **Name it as a tailor would.** "Fitted Kaftan with Side Slit". If a tailor at Balogun would not recognise the name, it is wrong.
2. **Tag silhouette and formality.** Both drive matching; guessing here produces wrong recommendations later.
3. **Tag fabric suitability for all six fabrics.** `ideal`, `works`, or `avoid` — no field left blank. When unsure, `works`.
4. **Tag occasions.** At least three. A style with one occasion tag will almost never surface.
5. **Write body notes** in abstract silhouette language. Never body-focused phrasing.
6. **Source three to five images** with complete provenance.
7. **Write the reasoning** for every `ideal` and `works` fabric.
8. **Stylist review**, then `active`.

### The fabric suitability judgement

The question is always: *would a competent tailor recommend this cut in this fabric?*

| Ask | If the answer is |
|---|---|
| Will it hold the shape? | No → `avoid` for structured styles |
| Will it drape? | No → `avoid` for flowing styles |
| Does the pattern survive the seaming? | No → `avoid` or `works` with a caution |
| Does it need lining, and does lining change the silhouette? | Yes → note it in the reasoning |
| Is it appropriate to the formality? | No → `works` at most |

Two errors to avoid, in order of harm:

**Over-claiming `ideal`** sends someone to a tailor with a bad plan and costs them money. This is the expensive mistake.
**Over-claiming `avoid`** narrows the pool and produces thin results. Annoying, but recoverable.

When genuinely uncertain, `works` and a careful sentence of reasoning.

---

## 3. Writing reasoning

Shown to users, and it is the fallback text when the model plane is down — so it must stand alone.

**Structure:** name the fabric property → name what the cut does about it → stop.

Good:

> "This Ankara has large motifs, so a Kaftan's uninterrupted panels let the pattern read as one piece instead of being cut apart at the seams."

> "Aso-Oke holds its shape rather than falling, which is exactly what an Agbada's structure needs. In something flowing it would look stiff."

Bad:

> "This style is perfect for this beautiful fabric and will make you look amazing." — says nothing, could be about any pairing.

> "Great for hiding problem areas." — body-focused, forbidden, and would be caught in review.

Length: one or two sentences. Voice: knowledgeable friend, not catalogue copy.

---

## 4. Image sourcing

### Approaching tailors

The pitch is straightforward and true: *"We're building a styling app for Nigerian fashion. We'd like to feature your work with your name and a link. No cost to you, and it sends people who like your style to you."*

Then: a one-page written agreement covering non-exclusive use in-product and in marketing, attribution, the ability to withdraw, and a model release where faces are identifiable.

Target 5–10 sources covering both menswear and womenswear. Prioritise those with a strong existing portfolio and a range of fabrics.

### Generated images

For gaps only. Every generated image needs stylist review before `active`, checking specifically:

- Agbada sleeve and shoulder proportions
- Gele structure and tie
- Embroidery placement and density
- Wrapper and blouse relationship
- Whether the fabric behaves as that fabric actually behaves

A generated image that looks plausible to a general audience and wrong to a Nigerian user is worse than no image at all.

### Never scrape

Not from Instagram, not from Pinterest, not from a brand's website. Linking to a product is fine; hosting someone's photograph as FAUE's reference material is infringement on the exact asset the product depends on.

---

## 5. Accessory pairings

Twenty to thirty accessories mapped to styles, occasion-aware.

Same style, different occasion, different accessories — gold and statement pieces for Owambe, minimal for corporate. The `rationale` field is shown to users, so it needs a real reason: "the gold picks up the thread in this Aso-Oke", not "a great match".

---

## 6. Eval labelling

Fully covered in [`labeling-guide.md`](labeling-guide.md). Two sets are content-owned and gate AI releases:

- **`fabric_match`** — 150 fabric photographs labelled with type, motif scale, weight, and the styles that genuinely suit them.
- **`look_rank`** — 100 user profiles with candidate pools, ranked as a stylist would rank them.

These encode domain knowledge that exists nowhere else in machine-readable form. They are the most valuable content FAUE will produce, and the most tedious. Start early; they cannot be rushed at the end.

---

## 7. Quiz copy

Options B–D of each Style DNA question are drafted in [`../00-product/style-dna.md`](../00-product/style-dna.md) and need a read-through for voice. Option A of each is preserved from the design.

Check: does it sound like a Nigerian professional in their late twenties, or like a Western fashion magazine? Would someone recognise themselves in it? Is anything unintentionally judgemental?

Weight changes are a product decision, not a copy decision — flag them rather than editing.

---

## 8. Weekly rhythm

| Day | Task |
|---|---|
| Monday | Review fabric analyses from the past week; note styles the library lacks |
| Tuesday–Wednesday | Style library work — add, tag, source, write |
| Thursday | Eval labelling |
| Friday | Review flagged AI sessions; check licence expiries |

Roughly two-thirds library work and one-third labelling until launch, then it inverts as the library stabilises and evaluation becomes continuous.

---

## 9. Quality bar

Nothing reaches `active` without:

- [ ] A name a tailor would use
- [ ] Complete tags — no blank fields
- [ ] Defensible fabric suitability for all six fabrics
- [ ] Three or more images with complete provenance
- [ ] Stylist approval on any generated image
- [ ] Reasoning for every `ideal` and `works` pairing
- [ ] Abstract silhouette language in body notes, no body-focused phrasing
- [ ] Nothing scraped

---

## 10. When to ask

Flag rather than guess:

- A fabric-style pairing you are unsure about — a wrong `ideal` costs a user money.
- A tailor asking for terms beyond the standard agreement.
- Copy that feels off but you cannot say why — that instinct is usually right.
- A style category with obviously thin coverage.
- Anything that reads as body-focused, however mild.
