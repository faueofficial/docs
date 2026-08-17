# ADR 0019: Remove the Instagram integration

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The Connected Accounts screen offers Instagram alongside Pinterest, promising to "analyze your fashion-related posts and saves" in order to understand style preferences and suggest similar looks.

## Decision

Instagram is removed from the design and from scope. The `IntegrationProvider` interface remains general so another platform can be added without rework.

## Rationale

The Instagram platform cannot deliver what the screen promises. The Graph API does not expose a user's saved posts or collections, and the Basic Display API is deprecated. What remains reachable is a user's own published media, and only for Business and Creator accounts — a small minority of the target audience, offering a much weaker style signal than a Pinterest board that was curated as aspiration in the first place.

Shipping a connection that promises analysis it cannot perform is worse than shipping nothing: it consumes a permission grant, sets an expectation, and fails quietly.

## Consequences

**Positive:** No misleading permission request. Engineering effort concentrates on the integration that works. Onboarding is shorter.

**Negative:** One fewer signal source, and one fewer familiar logo on a screen where familiarity aids conversion.

**Reversal cost:** Low. The interface is general; if the platform changes, an adapter is all that is needed.

## Alternatives considered

Building against own-media only — rejected as delivering far less than the screen implies for a minority of users. Keeping the screen and disabling the button — rejected as dishonest.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
