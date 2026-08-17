# ADR 0002: spree and notify are modules, not services

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The conversational/agentic layer (`spree`) and notification delivery (`notify`) are both plausible services. Both were initially designed as separate deployables and folded back after review.

## Decision

`spree` runs as a module inside `ase`. `notify` runs as a module inside `api-gateway`. Both maintain four extraction seams from the first commit: they own their own prefixed tables, they are reachable only through an interface class, notify is invoked exclusively by consuming events, and each ships its own configuration namespace and OpenAPI fragment.

## Rationale

Neither has independent scaling pressure yet. Spree's load is a fraction of generation load; notify's volume at a hundred users is trivial. The cost of a separate service is real and immediate; the benefit is hypothetical until traffic exists.

Extraction seams cost nothing to maintain and everything to retrofit. The seam that actually decides the cost is the third one — if request handlers call notify inline, extraction means rewriting every caller. Event-only invocation makes it a deploy change.

## Consequences

**Positive:** Two fewer deployments. Extraction remains a configuration change rather than a refactor.

**Negative:** Spree's model latency shares a process with generation workers; a runaway session can consume capacity that generation wanted. Mitigated by per-session budgets and separate worker pools.

**Reversal cost:** Low, by construction. That is the entire point of the seams.

## Alternatives considered

Separate services from the start — rejected as premature. Merging notify into each service that sends messages — rejected outright, because frequency caps and consent checks would then be bypassable by any new feature that forgets them.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
