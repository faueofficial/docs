# ADR 0014: All external content is untrusted input to models

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE feeds Pinterest pins, user photographs, OCR text, and (from M1-2) scraped product descriptions into a model that holds tools. This is a live prompt-injection surface, not a theoretical one.

## Decision

Three trust tiers: system prompts are trusted; tool results are semi-trusted; user text, images, OCR output, imported captions, and product descriptions are always untrusted. Untrusted content is delimited and labelled as data and never enters the system-prompt channel. The spree tool surface is read-only. Tool authorisation is enforced outside the model. Output is validated against the legal pool.

## Rationale

Prompt injection cannot be prevented at the prompt layer — the model will eventually be convinced of something. The defence has to be that a convinced model still cannot do anything harmful, which means the tool surface must be incapable of harm rather than merely instructed against it.

OCR text is the vector most often missed. FAUE processes user photographs as a core flow, and text inside an image reaches the model exactly as text does.

## Consequences

**Positive:** A successful injection produces text that is then stripped by validation. No tool mutates state or spends money, so there is nothing to escalate to.

**Negative:** Spree cannot perform actions on the user's behalf — no saving, no purchasing, no sending — which limits what the assistant can be. Ingest-time screening adds latency to imports.

**Reversal cost:** High to loosen. Adding a mutating tool requires a full re-examination of the injection surface, and is an explicit decision rather than a feature addition.

## Alternatives considered

Prompt-level defences alone — rejected as insufficient. Disallowing imported content entirely — rejected; the aspiration layer is a core differentiator.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
