# ADR 0021: Workspace tenancy from the first migration

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** MVP (data model) · Y2 (behaviour)

## Context

FAUE's long-term direction is a fashion-technology platform serving professionals — stylists managing many clients, tailors holding many measurement books, production workspaces for shows and pop-ups — alongside the consumer product. That direction was confirmed after the MVP architecture was designed.

The current data model is single-tenant in the strictest sense: one user, one vault, one style context, one set of looks. Every table keys on `user_id` and every query scopes by it.

A stylist with twenty clients does not fit that model. Neither does a tailor with two hundred measurement books, nor a show workspace with forty looks and six people working on them.

The question is not whether to build professional features now — they are `Y2` and clearly should not be built now. The question is whether the **data model** accommodates them, because that is the part that cannot be added cheaply later.

## Decision

Introduce the workspace concept in the data model from the first migration, and leave it single-tenant in behaviour.

```
workspaces         (id, kind, name, owner_user_id, created_at)
workspace_members  (workspace_id, user_id, role, joined_at)
```

Every user-owned table gains a `workspace_id`, populated with the user's implicit personal workspace. Repository access goes through a scoping helper rather than a raw `user_id` filter.

`kind` is `personal` at MVP. `stylist`, `tailor`, and `production` are reserved and unused.

Nothing in the MVP's behaviour changes. Every account has exactly one workspace, created at registration, containing exactly one member. The API does not expose workspaces and the client never sees the concept.

## Rationale

The asymmetry in cost is the whole argument.

**Deciding now** costs one nullable column per user-owned table, a backfill in the same migration that creates them, and a scoping helper in the repository layer. Perhaps a day of work, and it happens before any data exists.

**Deciding in year two** means a migration touching every table in `gateway` and `ase`, rewriting every query, revisiting every consent check, and doing it against a live database with real users — during which the consumer product cannot ship anything that touches those tables.

This is the classic case where an abstraction that looks premature is actually just cheap insurance. The distinguishing feature is that the future requirement is already known and specific, not hypothetical.

There is a second reason. Professional features require **delegated access** — a client granting a stylist visibility into their wardrobe, revocably and partially. That is a genuinely hard privacy design problem, and it is far easier to design into a model that already has a membership concept than to bolt onto one that does not.

The single-tenant behaviour matters as much as the multi-tenant model. Building workspace *features* now would be the mistake this ADR is often confused with — the decision is to make the schema capable, not to make the product capable.

## Consequences

**Positive:** professional features become an additive build rather than a restructuring. Delegated consent has somewhere to live. Show and pop-up workspaces are a `kind`, not a new subsystem. Personal accounts are a degenerate case of the general model, so there is one code path rather than two.

**Negative:** every query carries a scope the MVP does not need, which is a small ongoing cognitive tax. There is a real risk of scope creep — of someone deciding that since workspaces exist, workspace features may as well be built. The mitigation is this ADR: the model is capable, the product deliberately is not.

A subtler cost: a nullable `workspace_id` that is always populated is a lie the schema tells until it becomes true. It should be non-nullable from the start, with the personal workspace created in the same transaction as the user.

**Reversal cost:** low. Dropping the column later is trivial if the direction changes. That asymmetry — cheap to add, cheap to remove, expensive to retrofit — is the reason to do it.

## Alternatives considered

**Add workspaces when professional features are built (Y2).** Rejected. The migration cost against a live database is high, and it would freeze consumer development while it happened.

**Build professional features now alongside the consumer product.** Rejected outright. Different users, different sales motion, different support burden. Two people cannot build both, and attempting it is the most likely way the consumer product stalls before proving retention.

**A separate database or service for professional users.** Rejected. It duplicates the styling engine, the style library, and the model plane — which is precisely the shared spine that makes a professional product worth building on FAUE rather than from scratch.

**Row-level security in Postgres instead of an application-layer scope.** Considered and deferred. It is a stronger guarantee, but it complicates local development and the migration story. Worth revisiting when workspaces carry real multi-member data.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
