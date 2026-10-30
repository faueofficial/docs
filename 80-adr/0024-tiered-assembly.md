# ADR 0024: Looks are assembled by rules and a ranker; a model only breaks ties and words things

**Status:** Accepted; supersedes [0017](0017-model-led-assembly.md) for the default path
**Date:** 2026-10-21
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

ADR 0017 had a model select and assemble looks. A reasoning-tier call on every generation costs money, adds seconds, and varies from run to run, and a model can still name a piece the person does not own.

## Decision

The default assembler is code: a legal pool, a beam search under hard ontology rules, a linear scorer with diversity (MMR) and a margin-based confidence (`ase/app/engine`). A model is used only (1) to break a near tie between the top looks and (2) to word a reason, through the `look-pipeline` skill's `words` phase, with the engine's own fact-grounded sentence as the fallback. The model never edits an outfit and never sees a piece the engine did not already approve.

## Rationale

Aesthetic judgement is still learned, not hand-coded: the ranker's weights and the ontology's rules are data that reviewers and logged outcomes change. But validity (right slot, owned, right formality, safe for the weather) is not a thing to ask a model for; it is checked in code, every time, for free. A tie is the only moment a model's taste adds something the scorer cannot.

## Consequences

**Positive:** about $0.0001 and milliseconds per look on the default path; reproducible; a look can always be explained from facts; the product works with the model plane off. **Negative:** the ranker is only as good as its features and labels, so `look_rank` needs stylist rankings to replace the author's regression anchors. **Reversal:** low; the model path is a skill phase that can be widened.
