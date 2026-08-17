# ADR 0020: Style library imagery is licensed or generated, never scraped

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The thirty-style native library needs three to five reference images each — ninety to one hundred fifty images of Agbada, Kaftan, Iro and Buba, and similar. Instagram and Pinterest are full of exactly these images.

## Decision

Primary source is non-exclusive licensing from Nigerian tailors and design houses, with visible attribution and a written one-page agreement per source. Gaps are filled with generated references, each requiring stylist sign-off before entering the library. One commissioned shoot follows later for the styles the data justifies. Scraping for library assets is prohibited. Provenance fields are recorded per asset.

## Rationale

Hosting a designer's photograph as FAUE's own reference material is infringement, and the takedown risk falls on precisely the asset the differentiator depends on. This is distinct from the affiliate argument — linking to a product you do not host is standard practice; republishing a photograph is not.

Licensing from tailors costs almost nothing, produces imagery that is culturally authentic in a way stock photography is not, gives the source real value through attribution, and seeds the relationships the tailor network will need later.

Generated references carry no licensing exposure and stay visually consistent with the product's own output, but generated native wear is frequently wrong in the details — Agbada proportions, gele structure, embroidery placement — so stylist review is mandatory rather than advisory.

## Consequences

**Positive:** No legal exposure on the core content asset. Authentic imagery. Relationships that compound into the tailor network.

**Negative:** Outreach is relationship work that takes weeks and cannot be parallelised by engineering. Generated fill requires a stylist review loop before launch. Provenance tracking adds fields and process.

**Reversal cost:** High if violated — an unlicensed image discovered after launch means pulling it from a live product and possibly from shared cards already in circulation.

## Alternatives considered

Licensed stock photography — rejected; sparse and inauthentic for Nigerian native wear. Scraping — rejected on legal and reputational grounds. Commissioned shoot first — rejected as too slow and expensive before knowing which styles matter.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
