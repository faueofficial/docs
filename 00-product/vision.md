# Vision

**Stage:** all · **Requirements:** [`prd.md`](prd.md)

---

## 1. The problem

Getting dressed well in Nigeria takes more work than it should, and the work is unevenly distributed.

**For ready-to-wear**, discovery is scattered across dozens of brand Instagram pages with no way to see how pieces combine. Finding something that suits you means hours of scrolling with no intelligent filtering.

**For bespoke**, the gap between "I bought fabric" and "I know what to tell my tailor" is filled with chaotic Pinterest browsing, screenshots forwarded to WhatsApp groups, and miscommunication that turns into wasted money and a garment nobody wears. This happens several times a year, per person, at ₦30,000–80,000 a time.

**For both**, no platform understands the context: Owambe dress codes, Aso-Ebi coordination, switching between native and corporate registers, harmattan changing what fabric is bearable, or the fact that a large-motif Ankara and a heavily seamed cut destroy each other.

And underneath all of it: most people already own clothes they do not wear, because they cannot see the combinations.

---

## 2. What FAUE is

**A styling intelligence that understands you, your wardrobe, and your culture — and turns all three into something you can wear tomorrow.**

Not a shop. Not a mood board. A system that knows what you own, what you like, what suits you, what the occasion demands, and what the weather is doing, and produces a specific answer with a reason attached.

Three things distinguish it:

1. **It works with what you already have.** The vault is the starting point, not a catalogue.
2. **It handles fabric, not just garments.** The bespoke path — fabric to style to tailor — is a real, frequent, expensive problem nobody has automated.
3. **It is culturally native.** Owambe is a first-class occasion. Aso-Oke drapes differently from chiffon and the system knows it. Harmattan is a weather signal. None of this is a localisation layer bolted onto a Western product; it is the product.

---

## 3. Why now

- **Multimodal models became good enough.** Understanding a fabric photograph, judging whether a combination works, and explaining why in plain language were research problems three years ago and are API calls now.
- **Image generation became affordable enough** to show someone a look rather than describe it.
- **Nigerian fashion commerce is growing but fragmented.** Dozens of brands, no aggregation layer, no intelligence layer.
- **Nobody has built this.** Western styling apps do not know what an Agbada is. Pinterest shows you aspiration with no path to execution. Instagram is discovery without structure.

---

## 4. Who it is for

The early adopter is a fashion-conscious Nigerian professional, 22–35, who attends social events regularly, buys fabric for tailoring several times a year, and spends real money on looking right. They currently use Instagram, Pinterest, and WhatsApp groups to make styling decisions, and are frustrated by how long it takes and how often the result disappoints.

They are not looking for more inspiration. They have too much. They are looking for a decision.

Detail in [`personas.md`](personas.md).

---

## 5. What it becomes

**Year one — the styling layer.** FAUE knows your style, your wardrobe, and your calendar, and answers "what do I wear?" better than you can. Retention comes from accumulated personal data nobody else has.

**Year two — the commerce layer.** Once FAUE drives demonstrable traffic, brands come in with catalogues and partnerships. Recommendations extend from what you own to what you should buy, with attribution that makes the business work.

**Year three — the production layer.** The tailor network closes the loop: fabric to style to a vetted tailor to a finished garment, tracked end to end. This is where the bespoke differentiator becomes a marketplace.

**Underneath all three — the data.** Nobody has structured data on how Nigerians actually dress: which fabrics suit which silhouettes, how occasions map to formality, what people own versus what they wear. That dataset is the durable asset, and it is generated as a side effect of being useful.

---

## 6. What FAUE will not be

- **Not a marketplace first.** Two-sided cold start kills products at this stage. Earn the demand side, then bring the supply side in with data.
- **Not a social network.** No follower counts, no feeds, no comparison. Sharing exists to spread the product and to reach your tailor, not to build an audience.
- **Not a body-optimisation tool.** No weight talk, no "flattering for your problem areas", no before-and-after. Body profile exists to make clothes fit better, and that is the whole of it.
- **Not a Western product with Nigerian skin.** If a feature only makes sense in New York, it does not ship.
- **Not an aggregator of other people's photos.** The style library is licensed or generated, never scraped. See [ADR 0020](../80-adr/0020-style-library-licensed-not-scraped.md).

---

## 7. How we will know it is working

The core assumption is that personalised, culturally-correct, immediately-actionable styling drives action and return visits.

Early proof looks like: people finishing the quiz, generating looks in their first session, saving them, sharing DNA cards unprompted, uploading fabric, sending styles to tailors, and coming back within two weeks without being pushed.

Disproof looks like: quiz abandonment, looks generated once and never saved, zero tailor shares, and no unprompted returns. Those signals mean the recommendations are not good enough or the problem is not painful enough — and both are worth knowing quickly.

Thresholds are in [`metrics.md`](metrics.md).

---

## 8. Principles

**Answer, don't inspire.** The market is saturated with inspiration. FAUE's job is to end the search, not extend it.

**Explain everything.** A look without a reason is a guess. "Why this works for you" is not a feature; it is the product's voice.

**Rules keep it real, models make it good.** The system never recommends something that does not exist, and never reduces taste to a lookup table.

**Culture is not a category.** Owambe is not a filter option bolted on at the end. It is a first-class context that shapes the whole recommendation.

**Every session should improve the next.** The vault grows, the wear log deepens, preferences sharpen. Value compounds, which is the only durable form of retention.

**Privacy is architecture.** Consent denied by default, faces redacted before anything leaves the device's reach, nothing sensitive sent to a model. Not because a regulator is watching, but because users hand over photographs of themselves and their homes.
