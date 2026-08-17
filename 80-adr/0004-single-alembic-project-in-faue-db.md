# ADR 0004: One Alembic project and one model package in faue-db

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

With schema-per-service across independent repositories, the default is per-service migrations. The team wanted a single migrations location so that any model change is visibly accompanied by its migration, without hunting across repositories.

## Decision

All SQLAlchemy models and one Alembic project live in `faue-db`, a standalone pip-installable repository. Services depend on it by pinned version. CI runs `alembic upgrade head` followed by `alembic check` against a scratch database; a non-empty autogenerate diff fails the build. Each revision is exercised up, down, and up again.

## Rationale

Autogenerate needs the models, so co-locating models and migrations is the only way to get a mechanical guarantee rather than a convention. A model edited without a migration cannot merge.

Centralising the schema does not have to mean losing ownership. Two mechanisms preserve it: `CODEOWNERS` per schema directory, and PostgreSQL roles granted only on their own schema, so cross-schema access fails at the database rather than by politeness.

## Consequences

**Positive:** One place to look for the schema. Migrations are always consistent with models. Cross-schema references are impossible to introduce accidentally. A separate migrator role owns DDL, so runtime code cannot alter tables.

**Negative:** One migration history means one coordination point. A service can no longer ship a schema change fully independently. Deploy ordering becomes mandatory: migrate (expand-only), deploy, contract later.

**Reversal cost:** Low. Schemas are disjoint and role-isolated, so splitting into per-service projects is mechanical.

## Alternatives considered

Per-service Alembic projects — rejected because the model/migration co-location guarantee is worth more than independent schema deploys at this team size. Raw SQL migrations — rejected; loses autogenerate checking.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
