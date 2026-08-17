# ADR 0016: Email magic link as the primary credential

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

Authentication needed to be low-friction on mobile in a market where email is universal and passwords are a known drop-off point. The design shows a single email field with Google and Apple alternatives, and no password anywhere.

## Decision

Email magic link is the primary credential, alongside Google and Apple. The token is 32 random bytes, opaque, stored only as a hash, single-use, ten-minute TTL, one active per identifier, and consumed **only over POST**. Phone OTP is deferred to M1-2.

## Rationale

Three failure modes had to be designed for rather than discovered. Mail security scanners pre-fetch every URL in a message, so a GET that consumes the token burns the login before the user taps it — hence POST-only consumption. Users request on one device and open mail on another, so a session challenge with a typed-code fallback is required rather than optional. And deep linking needs the well-known files served correctly or every link opens a browser.

The token is opaque rather than a JWT because a signed token in a URL is a bearer credential that persists in browser history, referrer headers, and mail server logs.

## Consequences

**Positive:** No passwords to store, leak, or reset. Fewer signup fields. Email ownership is verified as a side effect.

**Negative:** Login depends on email deliverability, which becomes an operational concern with DKIM and SPF configuration. Slower than a typed password for a returning user. Cross-device adds a fallback path that must be built and designed.

**Reversal cost:** Low. Adding password authentication later is additive.

## Alternatives considered

Password authentication — rejected for friction and breach liability. SMS OTP as primary — deferred to M1-2 on cost and deliverability.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
