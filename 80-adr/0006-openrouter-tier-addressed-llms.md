# ADR 0006: OpenRouter for LLMs, addressed by task and tier, never by model name in code

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE needs language models for reasoning, narration, classification, and conversation. Gemini credits were unavailable, and OpenRouter was chosen as the access path. The open question was how code should refer to models.

## Decision

All LLM access routes through OpenRouter. Code names a **task** (`look.reasoning`, `spree.chat`); configuration resolves task to tier to an ordered list of models. Model identifiers never appear in application code. Provider selection is restricted to a zero-data-retention, no-training allowlist enforced per request.

## Rationale

Model identifiers rot fast. A slug hardcoded in a service is a future outage the day a provider deprecates it, and finding every occurrence during an incident is not a task anyone wants. Tier addressing turns a model swap into a configuration change, which also makes shadow evaluation and per-environment differences trivial.

The zero-retention allowlist is not optional — FAUE processes personal styling data, and a provider that trains on inputs is a compliance problem regardless of its output quality.

## Consequences

**Positive:** Model swaps require no deployment. A/B testing across models is configuration. One place to enforce retention policy, budgets, and logging.

**Negative:** One vendor between FAUE and every model, with its own availability and pricing. Mitigated because the `LLMProvider` interface admits direct providers, and OpenRouter is one implementation rather than an assumption baked into the code.

**Reversal cost:** Low. Adding a direct provider is one adapter.

## Alternatives considered

Direct provider SDKs — rejected for lock-in and the multi-model requirement. A local model — rejected on quality and operational cost for the reasoning tasks that matter.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
