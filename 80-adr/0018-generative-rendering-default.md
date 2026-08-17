# ADR 0018: Generative rendering is the default strategy

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

With three renderers behind one interface (ADR 0009), one must ship first.

## Decision

`generative` is the default. `composite` and `hybrid` remain implemented and selectable by configuration.

## Rationale

Generative is the only strategy that works before a user has photographed anything, which is every user on their first session — precisely when the product has to be convincing. It also matches the visual quality the design promises.

Committing to a default does not commit to it permanently; it establishes the baseline the other two are measured against on save rate, share rate, and cost per look.

## Consequences

**Positive:** The designed experience ships intact. Cold start is solved — a first-session user sees complete looks immediately.

**Negative:** Per-image cost becomes the dominant variable expense and the first thing to cap. Ten to forty seconds of latency requires the job model and visible progress. Generated garments may not exactly match owned items, which requires careful copy so the user understands what they are seeing.

**Reversal cost:** Trivial — a configuration flag.

## Alternatives considered

Composite default — rejected; cannot render for a user with an empty vault. Hybrid default — rejected as the hardest to evaluate without baselines from the other two.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
