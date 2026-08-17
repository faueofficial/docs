# ADR 0009: Look rendering is a pluggable strategy; generative is the default

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The Figma design shows rendered outfit images with multi-second building states. No prior document specified how those images are produced. Three approaches were viable and the team preferred to decide empirically.

## Decision

Define an `ImageRenderer` interface with three implementations: `generative` (diffusion, the default), `composite` (server-side layout of the user's real vault photographs), and `hybrid` (real items where available, generated fill elsewhere, visually labelled). All three share one job model, progress reporting, storage path, and guardrail set.

## Rationale

Each strategy is right under different conditions. Generative gives the visual appeal the design promises and works before a user has photographed anything. Composite is honest, free, fast, and never hallucinates a garment — which matters most once a vault is populated. Hybrid is the likely long-term answer and the hardest to evaluate without data from the other two.

Choosing by argument would have been guessing. The interface costs little and defers the decision to save rate, share rate, and cost per look.

## Consequences

**Positive:** The decision is measurable rather than argued. Strategy is a configuration flag, so it can be A/B tested or varied by user segment.

**Negative:** Three implementations to maintain, and the guardrail set must satisfy the strictest of them. Generative brings per-image cost, 10–40 second latency, and NSFW and likeness risk.

**Reversal cost:** Low — changing the default is configuration.

## Alternatives considered

Generative only — rejected as it discards the honesty advantage of showing real owned clothes. Composite only — rejected because it cannot render anything before a vault exists.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
