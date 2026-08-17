# ADR 0005: Single root virtualenv managed with pip and pip-tools

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

Multiple Python services in one workspace need a dependency strategy. Options were per-service virtualenvs, a `uv` workspace with a shared lock, or a single shared environment. The team specified pip.

## Decision

One `.venv` at the workspace root. `faue-core` owns the dependency contract as role-based requirement files (`base`, `web`, `worker`, `ml`, `dev`) compiled with `pip-tools` against a shared `constraints.txt`. Services install editable into the single environment. Docker images install only their role's compiled file.

## Rationale

A shared `constraints.txt` is what actually prevents version skew — two services resolving FastAPI to different versions produces bugs that only appear at the integration boundary and are miserable to diagnose.

A single environment also removes the per-service activate dance during a session that touches gateway and ase together, which is most of them.

## Consequences

**Positive:** One environment to install and one place where versions are decided. Editable installs mean a change in `faue-core` is immediately live in both services without reinstalling.

**Negative:** A service cannot upgrade a shared dependency alone. The `ml` stack constrains resolution for everything even though only ase uses it — mitigated by isolating `ml` requirements so they never enter the gateway image.

**Reversal cost:** Low. The constraints file makes splitting ase into its own environment mechanical.

## Alternatives considered

Per-service virtualenvs — rejected for workflow friction and skew risk. `uv` workspace — rejected by team preference for pip.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
