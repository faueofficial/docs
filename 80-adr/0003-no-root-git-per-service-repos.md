# ADR 0003: No repository at the workspace root; every service is standalone

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE's code will span roughly eleven repositories. The default modern choice is a monorepo. The team explicitly wants each service to be an independent repository under `github.com/faueofficial`, with no git repository at the workspace root.

## Decision

The workspace root is not a git repository and must never be initialised as one. Each directory beneath it is a standalone repository. `docs/repos.yaml` is the manifest and `docs/scripts/bootstrap.sh` hydrates a machine from it.

## Rationale

Team preference, and a defensible one at this size. Independent repositories mean independent access control, independent CI, and the ability to hand a single repository to a contractor without exposing everything else. The frontend engineer needs `faue-app` and `docs`, and nothing more.

The manifest plus bootstrap script recovers the one thing a monorepo genuinely provides — a single command that puts a new machine in a working state.

## Consequences

**Positive:** Clean per-repository permissions. A repository can be open-sourced or handed over in isolation. CI runs only what changed, without tooling to work that out.

**Negative:** A change spanning services needs coordinated pull requests. There is no atomic cross-service commit. Shared code must be versioned and released rather than imported directly — which is why `faue-core` and `faue-db` exist as packages.

**Reversal cost:** Moderate. Merging into a monorepo later is a scripted history graft.

## Alternatives considered

Monorepo — rejected by team preference. Git submodules — rejected because they are a well-known source of confusion for exactly the workflow they claim to serve.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
