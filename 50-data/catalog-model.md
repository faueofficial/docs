# Catalog Model

**Stage:** M1-2 · **Schema:** `catalog` · **ADR:** [0010](../80-adr/0010-defer-catalog-and-affiliate.md)

Designed now, built at M1-2. The MVP loop works from the user's own wardrobe and fabric; the catalogue extends recommendations to things they could buy.

Not built at MVP because curating 500 products is weeks of content work that would gate launch, and because affiliate click-through tests monetisation — the wrong question before retention is proven.

---

## 1. Schema

```sql
catalog.brands (
  id, name, slug, website, instagram, price_tier,
  affiliate_program, commission_rate, status, priority
);

catalog.products (
  id, brand_id, external_id, name, category, subcategory, gender,
  colors TEXT[], fabric, occasion_tags TEXT[], style_archetypes TEXT[],
  price_ngn BIGINT, sizes TEXT[], product_url, affiliate_url,
  status,            -- active | out_of_stock | dead_link | archived
  first_seen_at, last_seen_at
);

catalog.product_images (id, product_id, url, cdn_url, image_hash, is_primary, width, height);
catalog.ingest_jobs  (id, source, brand_id, status, items_found, items_upserted, errors, started_at, finished_at);
catalog.link_health  (product_id PK, last_checked_at, status_code, consecutive_failures, unavailable_since);
catalog.curation_queue (id, product_id, reason, assigned_to, resolved_at);
```

`price_ngn` is a `BIGINT` in kobo — minor units, never a float. Money in floating point is a bug waiting for a rounding error.

---

## 2. Vocabulary

**Shared with the rest of the system.** Divergence here silently breaks matching, because a product tagged `aso-oke` will never match a style tagged `aso_oke`.

| Field | Values |
|---|---|
| `category` | `tops`, `bottoms`, `native`, `shoes`, `accessories`, `outerwear`, `bags`, `jewelry` |
| `fabric` | `ankara`, `lace`, `aso_oke`, `adire`, `cotton`, `chiffon`, `denim`, `silk`, `linen`, `wool`, `other` |
| `occasion_tags` | `owambe`, `wedding`, `corporate`, `casual`, `date_night`, `church`, `travel`, `funeral` |
| `style_archetypes` | `CM`, `OR`, `SL`, `SC`, `CE`, `NF` — the Style DNA personas |
| `price_tier` | `accessible` (<₦15k), `mid` (₦15k–40k), `premium` (>₦40k) |

The first five category values match `VaultCategory` exactly, so a catalogue product and an owned item are interchangeable in a look.

---

## 3. Ingestion

```
source → normalise → dedupe (brand + name + image hash) → tag
       → upsert → emit catalog.product.upserted → ase embeds
```

| Source | Method | Notes |
|---|---|---|
| Manual sheet | CSV import via admin | The MVP-era approach; slow but exact |
| Brand website | Scrape category pages | Most Nigerian brands have no API |
| Instagram storefront | Manual, with permission | Many brands sell only here |
| Brand API | Direct integration | M3+, once partnerships exist |

Scraping product listings to link to them is standard affiliate practice — the brand benefits from the traffic. **Hosting their photographs as FAUE's own content is not**, which is the same distinction that governs the style library.

---

## 4. Link health

The catalogue's failure mode is staleness, and it is the one users notice immediately.

```
nightly: check every active product URL
  404 or 410            → status = dead_link, emit catalog.product.unavailable
  3 consecutive failures → same
  out-of-stock detected  → status = out_of_stock
```

`ase` filters on `status` at query time and reacts to `catalog.product.unavailable`, so a dead product never reaches a user even between syncs.

**Target: dead-link rate under 5%.** Above that, the catalogue is doing more harm than good — nothing erodes trust faster than tapping a recommendation and landing on a 404.

---

## 5. Attribution

```
POST /v1/actions/shop-click {item_id, look_id?}     # M1-2 — not yet in gateway.v1.yaml
  → record server-side
  → 302 to the affiliate URL
```

This endpoint is specified here but deliberately absent from the v1 contract until the catalogue is built. It is added to `gateway.v1.yaml` and the contract changelog in the same release as the `catalog` service.

The redirect goes through the gateway so attribution is server-side rather than trusted from the client. A client-reported click can be forged and cannot be reconciled against a partner's numbers.

Emits `shop.clicked` for `commerce` (M3+) and analytics.

---

## 6. Curation targets

| Milestone | Products | Brands |
|---|---|---|
| M1-2 launch | 500 | 10–15 |
| M2 end | 1,000 | 15–20 |
| M3 | 2,000 | 20–30 |

Composition: both menswear and womenswear, all three price tiers, accessories included, and priority on brands with stable online stores where affiliate links can be tracked.

**Accessories matter more than they look.** They complete a look, they are cheap enough for impulse purchase, and they are the most likely first conversion.

---

## 7. Quality bar

Before `active`:

- [ ] Name matches the brand's own listing
- [ ] Category and fabric from the shared vocabulary
- [ ] At least two occasion tags
- [ ] Price current and in kobo
- [ ] Product URL resolves
- [ ] At least one image, 800 px or wider
- [ ] Brand attribution correct

---

## 8. Why not at MVP

Recorded so the reasoning survives:

1. **The design shows no shop surface.** No brand, no price, no purchase action across 72 hi-fi frames.
2. **Curation gates launch.** 500 products is weeks of content work before a single user sees anything.
3. **It tests the wrong hypothesis.** Affiliate clicks measure monetisation; the MVP needs to know whether personalised styling drives return visits.
4. **Dead links damage trust.** A stale catalogue at launch, with nobody watching it, actively hurts.
5. **Brand conversations need data.** Approaching a brand with "we sent you 400 clicks last month" is a different conversation from "we would like to list your products".

The schema and events exist now so that building it later is additive rather than a restructuring.
