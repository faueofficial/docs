# ADR 0017: Models select and assemble looks within the legal pool

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

An earlier draft assigned outfit assembly to rules, with the model limited to explaining the result. Review rejected this: matching colours correctly, judging proportion, and knowing what reads well for an Owambe are exactly what a model is better at than a rule table.

## Decision

Pipeline stage 3b is model-led. The model selects pieces from the legal pool, assembles them, judges colour harmony, proportion, layering, texture, and occasion fit, proposes swaps, and may reject combinations the rules would have permitted. Rules retain two jobs only: defining the legal pool beforehand and validating identifiers afterwards.

## Rationale

Aesthetic judgement encoded as rules produces recommendations that are technically valid and visibly wrong — the failure mode of every rule-based styling system. The knowledge required is cultural and contextual, and it is exactly what a model trained on the world's fashion imagery carries.

Deterministic colour analysis remains valuable, but as a prior rather than a gate: LAB-space distance and harmony relations are cheap, exact, and give the model measured facts instead of hex values inferred from prose.

## Consequences

**Positive:** Substantially better output quality where the product is judged. Cultural nuance a rule table cannot encode. Rules stay small and comprehensible.

**Negative:** Assembly quality now depends on model quality, making the reranking and assembly prompt a first-class evaluation target. Higher token cost per generation. Results vary between runs — desirable for regeneration, but it means the golden set measures distributions rather than exact matches.

**Reversal cost:** Low. A heuristic assembler remains as the template fallback path.

## Alternatives considered

Rules-only assembly — rejected as producing valid but unattractive combinations. Model-only with no legal pool — rejected under ADR 0008.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
