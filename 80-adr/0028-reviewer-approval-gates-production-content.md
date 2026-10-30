# ADR 0028: Cultural content reaches production only by a named reviewer's approval of its exact version

**Status:** Accepted
**Date:** 2026-10-21
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

Style cards, ontology rules and skill references carry cultural claims (what is worn to a funeral, how a gele stands). Nobody on the engineering team is the authority on all of them.

## Decision

Every such item is filed in the review queue by its content hash (`POST /admin/v1/ase/review-sync`). A reviewer named for the tradition approves or sends back a version; an approval covers that hash only, so any edit needs a fresh one. `ase` reads approvals through one read-only view (`ase.approved_content`) and loads in production only approved versions. Outside production drafts load so development is not blocked.

## Rationale

A signature that silently covers later edits is not a signature. One view, not a cross-schema query, keeps ownership of the gateway's tables with the gateway.

## Consequences

**Positive:** a named human stands behind every cultural claim a person sees. **Negative:** production shows nothing cultural until reviewers are named and have worked the queue; that is the intended default. **Reversal:** high to loosen, by design.
