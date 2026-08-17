# ADR 0022: Canonical domain is faueofficial.com; `ase` retained over `archive` + `atelier`

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** MVP

## Context

Two naming questions were open at the same time and are resolved together here, because both touch nearly every document and both are cheap now and expensive later.

**Domain.** Earlier documents assumed `faue.app`. The domain actually purchased is **`faueofficial.com`**. `faue.app` may be acquired later, or may not.

**Service naming.** The `docs` remote contained an independently written architecture (`90-meta/legacy/01_SYSTEM_ARCHITECTURE.md`) proposing three services — `api-gateway`, `archive` (storage and vectorisation) and `atelier` (generation and VTO) — against the current design's two: `api-gateway` and `ase`. Both were considered work, and the conflict was recorded in `90-meta/reconciliation.md` rather than resolved unilaterally.

## Decision

**Domain:** `faueofficial.com` is canonical. Subdomains follow: `api.`, `staging-api.`, `admin.`, `cdn.`, `mail.`. Bundle identifiers become `com.faueofficial.app`.

**Services:** retain `api-gateway` + `ase`. The `archive` + `atelier` split is **rejected**. [ADR 0001](0001-two-services-gateway-and-ase.md) stands.

## Rationale

### Domain

Nothing subtle — it is the domain that exists. Recording it as a decision rather than a find-and-replace matters because `faue.app` appeared in 18 files including deep-link well-known files, the OpenAPI servers block, share URLs, and the email sending domain. A stale domain in `apple-app-site-association` silently breaks every universal link, and it fails quietly rather than loudly.

If `faue.app` is acquired later it becomes a redirect, not a migration: the canonical domain stays `faueofficial.com` so that share links already in circulation keep resolving.

### Services

The legacy split is genuinely defensible — storage and vectorisation are I/O and batch shaped, generation is compute and latency shaped, and they scale differently. It was rejected for one specific reason.

**The semantic matcher sits on the hot path of every generation.** `atelier` would query `archive`'s vector index on every look, for every user, every time. Putting a service boundary and a network hop inside the loop the entire product is built around buys separation that is not yet needed and costs latency on the operation that defines the product.

Secondary reasons: both halves share the model plane and the embedding configuration, so splitting them duplicates that layer or creates a third shared library; and two people should not run three deployments before there are users.

The pressure the split anticipates is real, and the boundary is already drawn — `ase.spree` is documented as extractable, and `catalog` and `media` are designed as separate services for exactly the batch and CPU-spiky work the legacy document was separating out. When generation load justifies it, `ase` splits along seams that already exist.

## Consequences

**Positive:** no network hop in the generation hot path; one model plane; two deployments instead of three; the existing 140-document corpus, four repositories, and the applied migration all stay consistent.

**Negative:** `ase` carries two workload shapes in one service, so a runaway generation job competes with embedding work for the same process. Mitigated by separate worker pools. The name `ase` is also less self-describing than `archive` and `atelier` to a newcomer — mitigated by the glossary, which explains the Yoruba *àṣẹ*.

The `Vault`/`Archive` naming is settled separately and in the design's favour: the Figma uses "My Vault" across seven screens, so the interface says Vault and the table is `vault_items`.

**Reversal cost:** moderate and decreasing. `spree` already has extraction seams; `catalog` and `media` are designed and unbuilt. Splitting `ase` later is the documented evolution path rather than a rewrite.

## Alternatives considered

**Adopt `archive` + `atelier` wholesale.** Rejected on the hot-path argument above, and because it would invalidate an applied migration, four repositories and roughly forty documents for a boundary the roadmap already reaches by another route.

**Rename `ase` to `atelier` while keeping two services.** Considered. Rejected because `atelier` in the legacy document means specifically the generation half, so reusing the name for the whole service would be actively misleading to anyone who read that document.

**Keep `faue.app` in documentation and treat `faueofficial.com` as an alias.** Rejected — documenting a domain nobody owns is how a wrong value reaches a well-known file.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
