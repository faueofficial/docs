# Slice 3.5 — Event backbone and notify channels

**Created:** 2026-08-22 · **Branch:** `slice-0-1-infra-identity`
**Spec:** [`../../10-architecture/event-catalog.md`](../../10-architecture/event-catalog.md)
**Precedes:** slice 4 (vault, uploads, image PII)

---

## Why this before slice 4

`consent.changed` and `quiz.completed` are written to `gateway.outbox` and
nothing reads them. The outbox is doing its job — the events survive — but no
consumer has ever run, so the asynchronous half of the architecture is entirely
unexercised. Every further slice adds more events to a heap nobody drains, and
the first time the transport is tested it will be with five event types at once
rather than two.

Nothing here is blocked on an open decision, which is the other reason it goes
first: slice 4 needs a face-detection model, an OCR engine and a safety
classifier chosen before its pipeline can be written.

---

## Part 1 — the relay

`outbox_relay` moves rows from `gateway.outbox` to the broker and stamps
`published_at`.

**Where the logic lives:** `faue-core`, parameterised by the outbox model. `ase`
needs the identical loop and a second implementation would drift. The worker
entry point stays in each service.

### Claiming

```sql
SELECT ... FROM gateway.outbox
WHERE published_at IS NULL AND attempts < :max
ORDER BY occurred_at
LIMIT :batch
FOR UPDATE SKIP LOCKED
```

`SKIP LOCKED` because two relay instances is the normal state on Railway, not an
edge case, and without it they either deadlock or double-publish.

`ORDER BY occurred_at` gives per-producer ordering. It does **not** give global
ordering, and no consumer may assume it does — a consumer that needs ordering
between two event types has a design problem, not a transport problem.

### Failure

A publish failure increments `attempts` and leaves `published_at` null. Past
`max_attempts` the row is **parked**: excluded from claiming, counted, and
alerted on. The runbook already says a single failing row must not block the
queue, and `attempts < :max` in the claim is what makes that true.

Parking is not deletion. The row stays, because it represents a state change
some consumer never saw, and the runbook forbids deleting it.

### Tests

| Property | Why it matters |
|---|---|
| Only unpublished rows are claimed | A relay restart must not republish the world |
| `published_at` is stamped after a successful publish | Otherwise every restart republishes |
| A transport failure increments `attempts` and leaves `published_at` null | The retry has to be visible |
| A row past `max_attempts` is skipped | The runbook's "must not block the queue" |
| Two relays claim disjoint rows | `SKIP LOCKED`, tested with two real sessions |
| Rows are claimed in `occurred_at` order | Per-producer ordering |
| Publishing and stamping share a transaction | A crash between them republishes rather than loses |

---

## Part 2 — transports

```python
class EventTransport(Protocol):
    async def send(self, event: Event) -> None: ...
```

| Implementation | Used by |
|---|---|
| `InProcessTransport` | `local` — dispatches straight to registered handlers |
| `RabbitTransport` | `staging`, `prod` — topic exchange, routing key is the event name |

`EVENT_TRANSPORT` already selects between them in configuration. The in-process
transport is what lets a laptop exercise handler logic without a broker, and it
is the documented local default.

---

## Part 3 — consumers

`QUEUES` in `app/events/consumers.py` already declares the bindings. This adds
the runtime that binds them to handlers, plus:

**Idempotency.** `notify_deliveries` carries `UNIQUE (user_id, template_id,
event_id)`, so notify dedupes on its own effect table rather than on a separate
ledger. That is deliberate: a dedup key stored beside the effect cannot drift
from it, and there is no second write to keep consistent.

**Consent at consume time, not publish time.** A user may revoke between the two.
Dropping the event is then correct behaviour and is recorded as `suppressed`,
not as a failure.

---

## Part 4 — notify channels

Currently every channel raises. In order:

1. **inbox** — a row in `notify_inbox`. No external dependency, so it is the
   channel that proves the pipeline end to end.
2. **email** — Resend, reusing the template registry that already exists and is
   tested.
3. **push** — deferred until there is a device token to send to; `notify_devices`
   is populated by the app, which has not shipped.
4. **sms / whatsapp** — `M1-2`. They cost money and no launch message needs them.

Suppression rules — consent, quiet hours, frequency cap — belong to the
dispatcher, not to any channel, so a new channel cannot forget them.

---

## Out of scope

- Anything requiring a device token (push registration is app work).
- `ase` consumers. `user_style_context` has no `event_id` column, so ase needs a
  dedup story of its own; that is slice 5 with the rest of the ase work.
- Retry topology in RabbitMQ (DLQ, delay queues). The relay's `attempts` covers
  the producer side; consumer-side DLQ arrives with the first real broker test.
