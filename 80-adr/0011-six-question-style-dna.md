# ADR 0011: Style DNA is six questions, taxonomy defined by FAUE

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The Style DNA specification described ten questions, a thirteen-point weighted scheme, and six personas. The design shows six question screens with a progress bar running 0 to 90 percent, and a result reading "The Cultural Minimalist" — a persona absent from the specification.

## Decision

Six questions. The persona taxonomy, question copy, answer options, and per-option weights are defined by FAUE in `00-product/style-dna.md` rather than inherited from the earlier specification. Scoring is a pure, deterministic, versioned function gated at 100 percent correctness by a golden set.

## Rationale

The design is the more recent artefact and the shorter quiz directly addresses a risk the MVP document itself flagged: quiz abandonment. Fewer questions complete more often, and completion is the gate on every downstream personalisation.

Six questions cannot cleanly resolve six personas under the old weighted scheme, so respecifying was necessary rather than optional. Defining the taxonomy in-house also means the personas can be tuned to the styling engine's actual needs instead of being a personality quiz bolted on.

## Consequences

**Positive:** Higher completion. Scoring stays deterministic and fully testable. Personas are tuned to what the engine can act on.

**Negative:** The earlier scoring work is discarded. Fewer questions mean a coarser signal, partly offset by Pinterest import and behavioural learning.

**Reversal cost:** Low. `quiz_responses` is append-only and versioned, so a future quiz version coexists with old results.

## Alternatives considered

Keeping ten questions and adding four screens — rejected on completion risk. A hybrid of six required plus four optional — considered and deferred; revisit if the six-question signal proves too coarse.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
