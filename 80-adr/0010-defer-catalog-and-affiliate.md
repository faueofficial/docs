# ADR 0010: Defer the cross-brand catalog and affiliate loop to M1-2

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The MVP document called cross-brand recommendations "FAUE's reason for existing" and specified 500–1,000 curated products with affiliate links. The Figma design contains no brand, no price, and no purchase action anywhere across 72 screens. The designed product is wardrobe and fabric driven.

## Decision

Follow the design. The MVP loop is Style DNA → vault or fabric → generate → save → share. The `catalog` service, product curation, affiliate attribution, and product embeddings move to M1-2, designed in the HLD and unbuilt.

## Rationale

The design is the more recent and more concrete artefact, and it describes a coherent product that does not depend on curating a thousand products before launch. Catalog curation is weeks of content work that would gate the entire release.

The wardrobe-and-fabric loop also tests the sharper hypothesis: whether personalised styling on clothes a user already owns is valuable enough to return for. Affiliate click-through tests monetisation, which is the wrong question before retention is proven.

## Consequences

**Positive:** Launch is not gated on content curation. No dead links or stale prices at launch. The bespoke differentiator gets full attention.

**Negative:** The affiliate revenue signal is deferred, and with it the traffic data that would support brand partnership conversations. Recommendations are limited to what a user owns until the vault fills, making the cold-start problem sharper.

**Reversal cost:** Low. The catalog schema and its events are already designed; building it is additive.

## Alternatives considered

Keeping catalog in MVP — rejected because it gates launch on content work and contradicts the design. Accessories-only catalog — a reasonable middle path, deferred for the same reason.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
