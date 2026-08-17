# ADR 0015: Deploy on Railway first; evaluate a VPS on cost

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

The original MVP document assumed Vercel plus Railway at roughly $25–45 per month. The system now includes self-hostable embeddings, a broker, workers, and image processing, none of which fit that assumption.

## Decision

Deploy services on Railway initially, with Postgres and Redis as plugins and RabbitMQ from a template or a hosted free tier. Static surfaces stay on Vercel. Document the VPS migration path and the embedding-provider break-even calculation, and revisit once usage is predictable.

## Rationale

Railway removes operational work that a two-person team should not be doing at launch — no server patching, no TLS renewal, no manual database backups. The cost premium buys time that is worth more than the money at this stage.

The embedding provider choice follows the host: on Railway, idle RAM is billed continuously so a hosted embedding API is likely cheaper; on a VPS, self-hosting is unlimited within a fixed cost. Because the provider is pluggable, this is configuration rather than architecture.

## Consequences

**Positive:** Fast deployment, minimal operational load, easy rollback. Private networking keeps ase off the public internet without extra work.

**Negative:** Higher unit cost at scale, and continuous billing for idle memory penalises the self-hosted embedding path. Some vendor-specific configuration to unwind later.

**Reversal cost:** Low. Services are containerised; a VPS migration is a compose file and a DNS change.

## Alternatives considered

VPS from the start — rejected; operational load outweighs savings at launch volume. Kubernetes — rejected outright at this scale.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
