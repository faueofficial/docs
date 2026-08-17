# ADR 0008: Closed-set policy: models act within a rule-defined legal pool

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE's outputs are styling recommendations that users act on with real money, at a tailor or in a store. A model that invents a garment, a price, or a brand produces a result the user cannot obtain. The question was how much latitude models should have.

## Decision

Rules define the **legal pool** — everything available, in the right size, owned or in catalog, permitted by consent. Within that pool the model selects, assembles, ranks, and explains with full latitude, including rejecting combinations the rules would have allowed. After the model returns, every identifier is validated against the pool; unknown identifiers are dropped, never repaired.

## Rationale

An earlier framing — "rules decide, models narrate" — was too restrictive and was corrected. Colour harmony, proportion, layering, and cultural appropriateness are judgement problems that rule tables handle badly, and they are precisely where the product's quality lives. Constraining the model to narration would have thrown away its strongest contribution.

What must remain deterministic is *existence*: an item is real, available, and the right size. That is a data question, not a judgement question.

Deterministic colour analysis is supplied to the model as a **prior, not a gate**, so it reasons from measured facts rather than inferring hex values from prose.

## Consequences

**Positive:** A hallucinated recommendation cannot reach a user. Results are reproducible given the same pool. Model swaps cannot silently change what exists. Bad output is bounded and diagnosable.

**Negative:** Validation and pool construction add pipeline stages. A thin pool produces thin results, so filter tuning matters more than it would otherwise.

**Reversal cost:** Not applicable — loosening this is a product safety decision, not a technical one.

## Alternatives considered

Free generation with post-hoc verification — rejected, since verifying a hallucinated product requires the catalog lookup that would have prevented it. Pure rules — rejected as insufficient for aesthetic judgement.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
