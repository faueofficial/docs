# ADR 0023: Looks arrive by share, not by platform connection

**Status:** Accepted
**Date:** 2026-10-14
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

[ADR 0019](0019-remove-instagram-integration.md) removed the Instagram
connection because the platform cannot deliver a person's saved posts. People
still see looks on TikTok and Instagram that they want to try, and their natural
move is to share them.

## Decision

FAUE accepts a **share**: a link to a single post, an image, or both
(`POST /shares`). It does not ask for a login with any of those platforms.

- Links are accepted only for TikTok, Instagram and Pinterest posts, matched
  against fixed address shapes. Any other address is refused and the person is
  told to share a screenshot. Short links are followed one hop at a time, each
  hop checked against the same allow-list.
- A preview is fetched where the platform publishes one (TikTok oEmbed today).
  Instagram's oEmbed no longer returns a cover image, so an Instagram link is
  kept and a screenshot is requested.
- An image arrives through the existing upload flow (`kind: share`) and so goes
  through the PII pipeline before anything uses it.
- A link that yields no picture is kept with `status: needs_image`, never
  treated as an error.

## Rationale

It works for any account, public or private, personal or professional, and needs
no platform review, no business verification and no permission grant that has to
be justified. The cost is that the person does one extra step for platforms that
give no preview, which is the honest limit of what those platforms allow.

Fetching is confined to an allow-list of three platforms and a fixed set of
endpoints, so the share endpoint cannot be used to make the server request an
arbitrary address.

## Consequences

**Positive:** Nothing to approve, nothing to revoke, no tokens to protect.
Works from the phone's share sheet and from a web share target.

**Negative:** Not every link produces a picture. Platforms can change what
their oEmbed returns, so previews are best-effort and the screenshot path is the
one that always works.

**Reversal cost:** Low.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
