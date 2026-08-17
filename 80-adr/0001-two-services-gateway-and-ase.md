# ADR 0001: Two services now, four more designed

**Status:** Accepted
**Date:** 2026-08-17
**Deciders:** Testimony (backend and AI)
**Stage:** all

## Context

FAUE's product documentation contained two incompatible architectures: the MVP document assumed a single FastAPI monolith, while the Style DNA document assumed `api-gateway`, a separate `ase` service, and RabbitMQ between them. A choice had to be made before any code was written, because the wrong one is expensive to reverse once schemas and deployments exist.

Three options were considered: a modular monolith, two services, or four-plus microservices.

## Decision

Build `api-gateway` and `ase` as separate services now. Design `catalog`, `media`, `brand`, and `commerce` in the HLD with their boundaries and schemas defined, but do not build them until their stage arrives.

## Rationale

`api-gateway` and `ase` have genuinely opposite operational profiles. The gateway is I/O-bound, latency-sensitive, and holds all the PII. Ase is compute-bound, tolerant of seconds-long work, and holds no direct identifiers. They scale differently, fail differently, and deploy at different cadences. Merging them means the ML dependency stack ships in the gateway image and a model timeout can exhaust the connection pool serving logins.

Four services would be correct eventually and wrong now — six deployments, six CI pipelines, and distributed debugging for a two-person team with no users yet.

## Consequences

**Positive:** ase can be degraded without the gateway failing — vault, saves, and profile stay usable when generation is down. The ML stack never enters the gateway image. The service boundary forces the interface to be explicit from day one.

**Negative:** Two deployments instead of one. Local development runs two processes. Cross-service calls need service authentication and timeout handling that a monolith would not.

**Reversal cost:** Low in either direction. Merging is mechanical; the further splits are already designed.

## Alternatives considered

Modular monolith — rejected because the ML dependency stack and the failure isolation both argue for a process boundary. Full microservices — rejected as premature for the team size.

---

*ADRs are immutable once accepted. To change this decision, write a new ADR that supersedes it.*
