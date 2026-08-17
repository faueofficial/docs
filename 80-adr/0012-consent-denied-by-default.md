# ADR 0012: Every consent purpose defaults to denied, enforced by a shared dependency

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE processes styling preferences, body data, photographs, imported social content, and location — several of which are sensitive under GDPR and the Nigeria Data Protection Act. Compliance can be a policy document or an architectural property.

## Decision

A consent registry with named, independently revocable purposes, every one defaulting to denied. Enforcement lives in a shared FastAPI dependency rather than in per-endpoint code. Missing consent degrades the feature gracefully and says so; it does not raise an error.

## Rationale

Per-endpoint discipline fails the moment someone adds an endpoint in a hurry, and the failure is silent — the feature works, and only an audit reveals it should not have. A shared dependency makes the check impossible to forget because the endpoint will not compile into the router without declaring its purposes.

Denied-by-default matters because the alternative is that a new purpose silently applies to every existing user, which is precisely what regulators treat as unlawful processing.

## Consequences

**Positive:** Compliance is verifiable by reading the router. New purposes cannot retroactively apply. Revocation is immediate and total.

**Negative:** Every feature needs a consent surface designed before it can ship, and several such surfaces are missing from the current design. More onboarding friction, mitigated by requesting purposes at the moment of use rather than in a wall at signup.

**Reversal cost:** Not applicable — this is a legal obligation, not a preference.

## Alternatives considered

Blanket terms-of-service consent — rejected; not valid consent under GDPR for optional processing. Per-endpoint checks — rejected as unenforceable.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
