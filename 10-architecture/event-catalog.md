# Event Catalog

**Stage:** all · **Exchange:** `faue.events` (topic) · **Schemas:** [`../30-contracts/events/`](../30-contracts/events/)

The asynchronous contract between services. Adding a consumer should never require changing a producer; that property is what the rules below protect.

---

## 1. Envelope

Every message carries the same envelope. Payload shape varies; the envelope never does.

```json
{
  "event_id": "01924f8e-7c3a-7000-8000-000000000001",
  "name": "look.completed",
  "version": 1,
  "occurred_at": "2026-08-17T00:42:11.482Z",
  "producer": "ase",
  "user_id": "01924f8e-7c3a-7000-8000-0000000000aa",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "payload": { }
}
```

| Field | Type | Rule |
|---|---|---|
| `event_id` | UUIDv7 | Unique per event. Consumers deduplicate on it. |
| `name` | string | `noun.past_tense_verb`. Routing key is the name verbatim. |
| `version` | integer | Payload schema major version. Starts at 1. |
| `occurred_at` | RFC 3339, UTC | When the fact became true, **not** when it was published. |
| `producer` | string | Service name. |
| `user_id` | UUIDv7 or null | Present when a user is in scope. Null for system events. |
| `trace_id` | hex | Propagated from the originating request; ties async work to the user action. |
| `payload` | object | Event-specific. Identifiers and minimal fields only. |

---

## 2. Rules

**Events are facts.** Past tense, immutable, describing something that already happened. `look.completed`, never `generate_look`. A command dressed as an event couples the producer to the consumer's behaviour, which is exactly what this architecture is avoiding.

**Payloads carry identifiers, not data.** A consumer that needs the full object fetches it. Denormalised payloads go stale, leak fields, and make schema changes breaking.

**No PII in payloads. Ever.** No email, phone, name, measurements, image content, or free text a user typed. If a consumer needs it, it has an identifier and — where the consent model allows — an interface to fetch it.

**Publishing goes through the outbox.** The event row is written in the same database transaction as the state change. A relay publishes asynchronously and marks the row sent. Without this, "state saved but event lost" is real, silent, and untraceable.

**Consumers are idempotent on `event_id`.** Redelivery is normal, not exceptional. Handlers record processed identifiers and no-op on repeats.

**No ordering assumptions across streams.** RabbitMQ preserves order within a queue, not across routing keys or after a retry. A consumer needing sequence derives it from the state it fetches, not from arrival order.

**Schema changes are additive within a major version.** New optional fields are free. Removing a field, renaming it, changing its type, or tightening its constraints requires a new `version`, published in parallel until every consumer has migrated.

**Every consumer has a dead-letter queue.** Messages that fail after retries land there rather than blocking the queue or vanishing. A non-empty DLQ is an alert with a runbook.

---

## 3. Topology

```
exchange: faue.events (topic, durable)

queues (durable, one per consumer, bound to explicit routing keys):
  ase.style-context      ← quiz.completed, vault.item.added, vault.item.worn,
                           integration.synced, recommendation.feedback
  ase.embedding          ← vault.item.added, catalog.product.upserted,
                           catalog.product.unavailable
  media.render           ← quiz.completed
  gateway.card-ready     ← media.card.ready
  gateway.notify         ← quiz.completed, look.completed, look.failed,
                           agent.suggestion.ready, integration.synced,
                           media.card.ready
  gateway.deletion       ← user.deletion.completed
  analytics.sink         ← # (all events)

dead-letter: <queue>.dlq for each, with x-dead-letter-exchange configured
retry: 3 attempts with exponential backoff (1s, 8s, 60s) before dead-lettering
```

`analytics.sink` binds to everything and is the single point where events reach PostHog. Services do not embed analytics SDKs — one fan-out point means one place to fix when the vendor changes.

---

## 4. Catalog

### Identity and profile

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `user.registered` | 1 | gateway | analytics | MVP | `provider`, `is_new_user` |
| `user.profile.updated` | 1 | gateway | ase, analytics | MVP | `fields_changed[]` |
| `user.body_profile.updated` | 1 | gateway | ase | MVP | *(empty — ase fetches constraints)* |
| `user.deletion.requested` | 1 | gateway | all modules | MVP | `ledger_id`, `sla_due_at` |
| `user.deletion.completed` | 1 | any module | gateway | MVP | `ledger_id`, `module` |
| `consent.changed` | 1 | gateway | ase, notify, analytics | MVP | `purpose`, `granted`, `policy_version` |

### Style DNA

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `quiz.completed` | 1 | gateway | ase, media, notify, analytics | MVP | `quiz_version`, `dominant`, `alter_ego`, `wildcard`, `scores{}`, `is_retake` |
| `media.card.ready` | 1 | media | gateway, notify | MVP | `subject_id`, `square_url`, `stories_url` |
| `share.dna` | 1 | gateway | analytics | MVP | `surface` |

### Vault

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `vault.item.added` | 1 | gateway | ase, analytics | MVP | `item_id`, `category`, `asset_id` |
| `vault.item.removed` | 1 | gateway | ase, analytics | MVP | `item_id` |
| `vault.item.worn` | 1 | gateway | ase, analytics | MVP | `item_ids[]`, `occasion`, `worn_on` |

### Looks

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `look.requested` | 1 | ase | analytics | MVP | `job_id`, `source`, `occasion` |
| `look.completed` | 1 | ase | gateway, notify, analytics | MVP | `job_id`, `look_ids[]`, `renderer`, `duration_ms` |
| `look.failed` | 1 | ase | gateway, notify, analytics | MVP | `job_id`, `reason_code`, `stage` |
| `look.saved` | 1 | gateway | ase, analytics | MVP | `look_id` |
| `look.shared` | 1 | gateway | analytics | MVP | `look_id`, `surface` |
| `recommendation.feedback` | 1 | gateway | ase, catalog | MVP | `target_type`, `target_id`, `signal` |

### Fabric

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `fabric.uploaded` | 1 | media | ase, analytics | MVP | `asset_id` |
| `fabric.styled` | 1 | ase | analytics | MVP | `asset_id`, `detected_type`, `confidence`, `style_ids[]` |
| `tailor.share.created` | 1 | gateway | analytics | MVP | `asset_id`, `style_id` |

### Integrations

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `integration.connected` | 1 | gateway | ase, notify, analytics | MVP | `provider` |
| `integration.synced` | 1 | gateway | ase, notify, analytics | MVP | `provider`, `boards_imported`, `pins_imported` |
| `integration.disconnected` | 1 | gateway | ase, analytics | MVP | `provider`, `reason` |

### Agent and notifications

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `agent.suggestion.ready` | 1 | ase | notify, analytics | MVP | `run_id`, `look_id`, `trigger` |
| `notification.sent` | 1 | gateway | analytics | MVP | `template_id`, `channel`, `category` |
| `notification.opened` | 1 | gateway | analytics | MVP | `template_id`, `channel` |

### Catalog and commerce

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `catalog.product.upserted` | 1 | catalog | ase | M1-2 | `product_id`, `brand_id`, `image_url`, `fields{}` |
| `catalog.product.unavailable` | 1 | catalog | ase, gateway | M1-2 | `product_id`, `reason` |
| `shop.clicked` | 1 | gateway | commerce, analytics | M1-2 | `item_id`, `brand_id`, `look_id` |

### Operations

| Event | Ver | Producer | Consumers | Stage | Payload |
|---|---|---|---|---|---|
| `ai.budget.exceeded` | 1 | ase | gateway, analytics | MVP | `scope`, `task`, `limit`, `spent` |
| `ai.guardrail.tripped` | 1 | ase | analytics | MVP | `guard`, `category`, `session_id` |
| `admin.action.performed` | 1 | gateway | analytics | MVP | `actor_id`, `action`, `target_type` |

---

## 5. Consumer expectations

| Consumer | Must tolerate | On repeated failure |
|---|---|---|
| `ase.style-context` | Missing user context (rebuild from DNA) | DLQ; context rebuilds lazily on next request |
| `ase.embedding` | Image unavailable or unreadable | DLQ; item stays unembedded and outside the legal pool |
| `media.render` | Duplicate render requests | DLQ; card stays `pending`, user can retry from Profile |
| `gateway.notify` | Consent revoked between publish and consume | Drop silently; not a failure |
| `gateway.deletion` | Partial module acknowledgement | Ledger stays open; alert at SLA − 5 days |
| `analytics.sink` | Any event, including unknown names | DLQ; never blocks other consumers |

A consumer that cannot process an event because consent was revoked drops it and records the drop. That is correct behaviour, not an error.

---

## 6. Local development

The broker is optional locally. `faue-core` exposes one interface:

```python
class EventPublisher(Protocol):
    async def publish(self, event: Event) -> None: ...
```

with two implementations — `RabbitPublisher` and `InProcessPublisher`, selected by `EVENT_TRANSPORT` in configuration. The in-process bus dispatches to registered handlers synchronously after commit, which is enough to exercise handler logic without running a broker on a laptop.

Integration tests that assert delivery semantics — retry, DLQ, idempotency — run against a real RabbitMQ via testcontainers. Handler unit tests use the in-process bus.

---

## 7. Adding an event

1. Add a row to the catalog above with producer, consumers, stage, and payload.
2. Write `../30-contracts/events/<name>.schema.json`.
3. Record the addition in `../30-contracts/CHANGELOG.md`.
4. Declare the queue binding in the consuming service's configuration.
5. Publish through the outbox — never directly to the broker.
6. Add an idempotency test and a redelivery test for the consumer.

Removing an event is the reverse and must wait until no consumer binds to it, verified in production rather than assumed.
