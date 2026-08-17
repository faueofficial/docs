# Glossary

**Stage:** MVP

Shared vocabulary. Where a term has a precise meaning in FAUE, that meaning is here and nowhere else. Cultural terms are included because the product's differentiation depends on getting them right, and an engineer who has not attended an Owambe should not have to guess.

---

## Product terms

**FAUE** — the platform. Pronounced "fow-ay". Not an acronym; do not expand it.

**ase** — the styling intelligence service, from Yoruba *àṣẹ* (authority, the power to make things happen). Internal only; never exposed to clients. Lower case in code and prose.

**spree** — the conversational and agentic module inside `ase`. Handles chat sessions, tool calls, and the Style Studio surface. A module, not a service.

**Style DNA** — a user's style profile, produced by the six-question quiz. Comprises a dominant persona, an alter-ego, a wildcard, and the underlying score distribution. The onboarding hook and the primary personalisation signal.

**Persona** — one of the six style archetypes a Style DNA result resolves to. Referred to by a two-letter identifier in code and data. Defined in [`00-product/style-dna.md`](../00-product/style-dna.md).

**Alter-ego** — the second-ranked persona in a Style DNA result.

**Wildcard** — the third-ranked persona in a Style DNA result.

**Style DNA card** — the shareable image generated from a quiz result, rendered in square (1080×1080) and stories (1080×1920) formats. The viral mechanism.

**Vault** — the user's own wardrobe inside FAUE. Photographed items with category, colour, and notes. Called "My Vault" in the interface; `vault_items` in the database. Never called "wardrobe" in user-facing copy.

**Look** — a complete assembled outfit: several items, an occasion, a rendered image, and a reasoning paragraph. The primary unit of value.

**Generate** — the user-initiated action producing looks. Asynchronous, with progress states, because rendering takes seconds to tens of seconds.

**Fabric analysis** — the pipeline that takes a photograph of fabric and returns its type, attributes, and the native styles suited to it.

**Style library** — the curated catalogue of native styles (Agbada, Kaftan, Iro and Buba, and the rest), each tagged with fabric suitability, occasion, formality, and body notes. FAUE's most defensible content asset.

**Send to tailor** — the action that composites the fabric photograph, the chosen style reference, and the user's notes into a single image suitable for sharing with a tailor over WhatsApp.

**Aspiration vector** — an embedding derived from a user's imported Pinterest boards, representing what they aspire to wear, as distinct from what they own or what they said in the quiz.

**Reconciliation** — resolving aspiration against DNA, body profile, and budget into one of three outcomes: *reproduce* (a close match is available), *adapt* (the same look adjusted, with the reason stated), or *bespoke path* (no ready match; route to fabric and tailor).

**Agent** — the proactive styling layer. Suggests daily outfits, learns from what the user actually wears, and escalates through four autonomy levels. Defined in [`60-ai/agent-design.md`](../60-ai/agent-design.md).

**Wear log** — the record of what a user actually wore and when. The strongest behavioural signal the system has, and the input the agent learns from.

---

## Technical terms

**Legal pool** — the set of items that survived hard filtering (available, right size, owned or in catalogue, consent-permitted). The model may select freely within it and may not go outside it.

**Closed-set policy** — the rule that models select, assemble, rank, and explain within the legal pool, but never invent an item, price, brand, or style outside the catalogue, vault, or style library. Every model output is validated against the pool before reaching a user.

**Stylist pass** — pipeline stage 3b, where a model selects and assembles a look from the legal pool, judging colour harmony, proportion, layering, and occasion fit.

**Colour prior** — deterministic colour analysis (LAB-space distance, complementary/analogous/triadic relations, neutral-anchor detection) supplied to the stylist pass as measured fact rather than as a constraint.

**Renderer** — the component producing a look's image. Three interchangeable strategies: `generative` (default), `composite`, `hybrid`.

**Model plane** — the abstraction layer over all model providers. Two halves: the LLM plane (routed through OpenRouter, addressed by task and tier) and the embedding plane (pluggable, self-hosted by default).

**Tier** — an ordered list of interchangeable models for a class of work (`reasoning`, `fast`, `vision`, `cheap_bulk`). Code names tasks; configuration resolves tasks to tiers to models. Model identifiers never appear in code.

**Fallback depth** — how far down a tier's model list a request had to go to succeed. Sustained depth above one means the primary is unhealthy.

**Template path** — the non-model degraded response used when a task's tier is exhausted or its budget is spent. Every AI feature has one; the product remains usable with the model plane entirely down.

**Envelope encryption** — encrypting a column with a data key that is itself encrypted by a rotatable master key. Rotation re-encrypts keys, not rows.

**Blind index** — a keyed HMAC of a sensitive value stored alongside its encrypted form, so equality lookups (finding a user by email) remain index scans without storing plaintext.

**Outbox** — the pattern where an event row is written in the same database transaction as the state change it describes, then relayed to the broker asynchronously. Prevents the "state saved but event lost" failure.

**DSR** — data subject request. Export, deletion, rectification, or restriction, under GDPR and the Nigeria Data Protection Act.

**RoPA** — record of processing activities. The register of every field collected, its lawful basis, retention period, and recipients.

**Consent purpose** — a named, independently revocable reason for processing (`personalization`, `ai_processing`, `location_weather`, and others). All default to denied.

**Trust tier** — the classification governing what may enter a prompt. System prompts are trusted; tool results are semi-trusted; user text, images, OCR output, and imported captions are always untrusted.

**Golden set** — a versioned, human-labelled evaluation set that gates deployment. Safety and PII sets are hard blockers.

**Shadow mode** — running a new model, ranker, or renderer alongside production, scoring its output without serving it.

**Geohash5** — a five-character geohash, roughly 5 km precision. The only location granularity FAUE stores; precise coordinates are never persisted.

---

## Cultural terms

Getting these wrong in generated copy or a style recommendation is immediately obvious to a Nigerian user and destroys credibility faster than any bug.

**Owambe** — a large Yoruba party, typically a wedding, funeral, or milestone celebration. Elaborate dress is the point, not an option. The single most important occasion category in FAUE.

**Aso-Ebi** — coordinated fabric worn by a group at a celebration, usually bought in bulk and sewn individually. The reason two people arrive at the same wedding in the same fabric and completely different styles — and the reason "what should I sew?" is a real and frequent question.

**Agbada** — a flowing wide-sleeved robe worn over a shirt and trousers, most formal of Nigerian menswear. Requires structured fabric; drapes badly in lightweight material.

**Kaftan** — a long tunic, less formal than Agbada, worn across many occasions. Forgiving across fabric weights.

**Senator** — a tailored short-sleeved or long-sleeved top and trouser set, the standard for Nigerian business-formal and semi-formal wear.

**Iro and Buba** — Yoruba womenswear: *iro* is the wrapper, *buba* the blouse. Frequently worn with a gele and ipele.

**Gele** — an elaborately tied head wrap worn with traditional womenswear. Its structure depends heavily on fabric stiffness; Aso-Oke ties differently from lace.

**Ipele** — the shoulder sash worn with iro and buba.

**Boubou / Kaftan gown** — a loose full-length gown, comfortable and forgiving, common for both casual and formal wear.

**Ankara** — wax-print cotton fabric, bold patterned, the most common fabric in the market. Large motifs constrain how a garment can be cut without breaking the pattern.

**Aso-Oke** — hand-woven Yoruba fabric, heavy and structured, traditionally for ceremonial wear. Its weight suits structured silhouettes and defeats flowing ones.

**Adire** — Yoruba resist-dyed indigo fabric, typically cotton, with a distinctive irregular pattern. Increasingly used in contemporary cuts.

**Lace** — a broad category in Nigerian fashion covering French, Swiss, and cord lace, used for high-formality occasions. Usually requires lining, which affects style choice.

**Harmattan** — the dry, dusty West African season running roughly December to February, with Saharan dust and low humidity. It changes what fabrics are comfortable and what colours stay clean, which is why FAUE tracks a dust index alongside conventional weather.

**Detty December** — the December social season in Lagos, when diaspora return and events cluster densely. The highest-intensity styling period of the year and a major retention trigger.

**Balogun Market** — the large Lagos fabric market. Referenced as a customer-acquisition channel and as the point where "I bought fabric, now what?" begins.

---

## Words we do not use

| Avoid | Use instead | Why |
|---|---|---|
| Wardrobe (in user copy) | Vault | The interface says Vault; consistency matters |
| Outfit (in code) | Look | `looks` is the table and the domain concept |
| Recommendation engine | Styling engine, or the specific stage | "Recommendation" implies a catalogue that MVP does not have |
| Shop / buy | — | No commerce surface exists before M1-2; do not imply one |
| Native (as a noun for people) | Traditional wear, native wear (clothing only) | Applies to clothing, never to persons |
| Tribal | Cultural, traditional, heritage | "Tribal" is othering and inaccurate |
| Exotic | — | Never appropriate; FAUE's users are the default audience, not a curiosity |
