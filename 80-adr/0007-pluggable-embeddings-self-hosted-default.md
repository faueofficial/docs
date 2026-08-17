# ADR 0007: Pluggable embedding providers with a self-hosted default

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

OpenRouter has no embeddings endpoint, so the multi-model decision could not cover embeddings. FAUE needs multimodal embeddings — image and text in one space — for fabric matching, vault retrieval, and aspiration vectors.

## Decision

Define an `EmbeddingProvider` interface with self-hosted open-CLIP/SigLIP as the default, plus adapters for HuggingFace Inference, Voyage, Cohere, and Gemini. Provider is selected per environment. Stored vectors are keyed by `(subject_id, model_id)` so multiple models coexist; migration is dual-write, shadow-evaluate, flip by flag, soak, drop.

## Rationale

Provider economics invert between environments. On Railway, idle RAM is billed continuously, so a hosted embedding API is likely cheaper. On a VPS with fixed cost, self-hosting is unlimited. Neither answer is right everywhere, so the interface must not assume one.

Embeddings are not portable across models — different dimensions, different spaces — so a provider swap invalidates every stored vector. Designing the per-model key from the start turns that from a rewrite into a migration.

## Consequences

**Positive:** Provider choice follows the deployment target. No vendor lock. Migration path exists before it is needed.

**Negative:** More code than a single provider. Self-hosting adds 2–4 GB of resident memory to ase and a heavier image.

**Reversal cost:** Low for the provider, moderate for the vectors — re-embedding a full catalog takes hours, which is why dual-write exists.

## Alternatives considered

Committing to a single hosted provider — rejected for cost inversion across environments. CLIP via HuggingFace only, as in the original MVP document — rejected for rate limits and cold starts at ingest scale.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
