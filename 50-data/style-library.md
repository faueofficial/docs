# Style Library

**Stage:** MVP · **Owner:** Content (Oladunni) · **Schema:** `ase.style_library` · **ADR:** [0020](../80-adr/0020-style-library-licensed-not-scraped.md)

Thirty curated native styles, each tagged so the fabric engine can match them. **The taxonomy is the asset** — the tags do the work, the images illustrate. Budget effort accordingly.

---

## 1. Data model

```sql
ase.style_library (
  id, name, gender, silhouette, formality,
  fabric_suitability JSONB,   -- {"ankara":"ideal","aso_oke":"avoid", ...}
  occasion_tags TEXT[], body_notes JSONB, description, status
)
```

### Fields

| Field | Values | Notes |
|---|---|---|
| `name` | Free text | The name a Nigerian tailor would recognise. "Fitted Kaftan with Side Slit", not "Style 14" |
| `gender` | `womens`, `mens`, `unisex` | Presentation, not identity |
| `silhouette` | `fitted`, `structured`, `flowing`, `layered`, `oversized`, `column`, `a_line`, `wrap` | Drives the body-notes match |
| `formality` | `casual`, `smart_casual`, `formal`, `ceremonial` | Must overlap the occasion |
| `fabric_suitability` | Per fabric: `ideal`, `works`, `avoid` | The core matching field |
| `occasion_tags` | `owambe`, `wedding`, `church`, `corporate`, `casual`, `date_night`, `travel`, `funeral` | Multi-valued |
| `body_notes` | `{favors: [...], caution: [...]}` | Abstract silhouette language only |
| `status` | `draft`, `active`, `retired` | Only `active` reaches users |

### Fabric suitability — the important one

Six fabrics: `ankara`, `lace`, `aso_oke`, `adire`, `cotton`, `chiffon`.

These are **physical facts, not preferences**, and getting them wrong costs a user real money at a tailor:

| Fabric | Property | Consequence |
|---|---|---|
| Aso-Oke | Heavy, stiff, structured | Holds architectural shapes. Will not drape. `avoid` for anything flowing |
| Chiffon | Light, sheer, fluid | Drapes beautifully. Cannot hold structure. Usually needs lining |
| Ankara | Medium cotton, bold motifs | **Motif scale matters more than the fabric** — large motifs are destroyed by heavy seaming |
| Lace | Sheer, decorative, delicate | Requires lining, which changes the silhouette. Formal only |
| Adire | Medium cotton, irregular pattern | Versatile; pattern direction constrains panel cutting |
| Cotton | Medium, stable | Works with nearly everything. The safe default |

**Rule:** a style tagged `ideal` for a fabric must be something a competent tailor would actually recommend. When uncertain, tag `works` rather than `ideal`. Over-claiming is worse than being conservative, because the user acts on it.

### Body notes

Abstract silhouette language, never body-focused language.

```json
{ "favors": ["defined_waist", "vertical_line"],
  "caution": ["short_torso"] }
```

Correct: `favors: ["vertical_line"]`
Wrong: `"good for pear-shaped women"` — that framing does not appear anywhere in FAUE, including in internal data.

---

## 2. The thirty

Target composition:

| Category | Count |
|---|---|
| Women's traditional | 10 — Iro and Buba, Boubou, Kaftan gown, wrapper sets, Aso-Oke ensembles |
| Women's contemporary-traditional | 5 — modern cuts in traditional fabric |
| Men's traditional | 8 — Agbada, Kaftan, Senator, Dashiki, Buba and Sokoto |
| Men's contemporary-traditional | 4 — fusion cuts, modern proportions |
| Unisex | 3 — pieces that work across presentations |

Coverage requirements before launch:

- Every fabric has at least four `ideal` styles across both gender categories. A fabric with two options produces repetitive suggestions immediately.
- Every occasion has at least three styles per gender.
- Formality spans casual through ceremonial for both.

**The failure mode to watch:** thirty styles that are all formal Owambe wear. Someone uploading Adire for casual daily wear then gets nothing useful, and the gap is invisible until a user hits it.

---

## 3. Reference images

Three to five per style, ideally showing it in different fabrics. Sourcing policy from [ADR 0020](../80-adr/0020-style-library-licensed-not-scraped.md):

| Source | Priority | Requirements |
|---|---|---|
| **Licensed from tailors** | Primary | Written one-page agreement, attribution, model release where a face is identifiable |
| **Generated** | Gap-fill | **Stylist approval mandatory** before `active` |
| **Commissioned shoot** | Later | Full ownership; for the top ten styles once data shows which matter |
| **Scraped** | **Prohibited** | Infringement, and a takedown risk on the core asset |

### Provenance

Every image records `source`, `license_type`, `license_document`, `attribution`, `model_release`, `generated`, `stylist_approved_by`, `expires_at`.

An unlicensed image discovered after launch means pulling it from a live product, and possibly from share cards already circulating. Every image must be able to answer "where did this come from and may we use it?"

### Generated images — why approval is mandatory

Generated native wear is frequently wrong in ways a non-specialist will not notice: Agbada sleeve proportions, gele structure and tie, embroidery placement, the relationship between wrapper and blouse.

An image that looks plausible to a general audience and wrong to a Nigerian user is worse than no image, because it signals that FAUE does not actually know this domain. Approval is a domain check, not a quality check.

---

## 4. Accessory pairings

Twenty to thirty accessories mapped to styles, occasion-aware.

```sql
ase.accessory_pairings (style_id, name, image_url, occasion, rank, rationale)
```

Occasion changes the pairing entirely: gold and statement jewellery for Owambe, minimal for corporate, texture-led for casual. The same style takes different accessories depending on where it is going, which is why `occasion` is on the pairing rather than the style.

`rationale` is shown to users, so it must say something real — "the gold picks up the thread in this Aso-Oke", not "a great match".

---

## 5. Style-to-fabric reasoning

Every `ideal` and `works` pair needs written reasoning, because it is shown to the user and it is the **template fallback** when the model plane is unavailable.

```
Style: Fitted Kaftan with Side Slit
Fabric: Ankara, large motif
Reasoning: "The uninterrupted panels let a large motif read as one piece
            instead of being cut apart at the seams. The side slit adds
            movement without adding seams through the pattern."
```

Rules: name the fabric property, name what the cut does about it, one or two sentences, no filler. Someone about to spend money at a tailor needs it useful, not flattering.

Roughly 30 styles × relevant fabrics ≈ 100–120 pieces of reasoning. This is the single largest content task before launch and it cannot be parallelised by engineering.

---

## 6. Workflow

```
draft → tag → images sourced → reasoning written → stylist review → active
```

A style reaches `active` only when it has: all tags, at least three reference images with provenance, reasoning for every `ideal` and `works` fabric, and stylist sign-off. `draft` styles are invisible to users.

Managed in the admin console, not a spreadsheet — a spreadsheet drifts from the database within a week, and by month two nobody knows which is right.

---

## 7. Quality bar

Before `active`:

- [ ] Name a tailor would recognise
- [ ] Fabric suitability defensible for every one of the six fabrics
- [ ] At least three occasion tags
- [ ] Body notes in abstract silhouette language, with no body-focused phrasing
- [ ] Three to five images, each with complete provenance
- [ ] Generated images carry stylist approval
- [ ] Reasoning for every `ideal` and `works` fabric
- [ ] Description reads as advice, not as a catalogue entry

---

## 8. Maintenance

| Cadence | Task |
|---|---|
| Weekly | Review new fabric analyses for styles the library lacks |
| Monthly | Check which styles get suggested and shared; expand the winners |
| Monthly | Check licence expiry dates |
| Quarterly | Full coverage audit against the matrix |
| Seasonally | Adjust occasion weighting for wedding season and Detty December |

**The most useful signal** is which fabric uploads produce weak matches. That is the library telling you where its gaps are, and it is visible in `fabric_analyses` before any user complains.
