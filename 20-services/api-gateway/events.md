# api-gateway — Events

**Stage:** MVP · **Catalog:** [`../../10-architecture/event-catalog.md`](../../10-architecture/event-catalog.md)

---

## 1. Produced

All published through `gateway.outbox`, written in the same transaction as the state change.

| Event | Emitted when | Notes |
|---|---|---|
| `user.registered` | First successful sign-in | Once per user, never on later logins |
| `user.profile.updated` | Profile fields change | Carries changed field names only |
| `user.body_profile.updated` | Body profile saved | Empty payload — `ase` fetches derived constraints |
| `user.deletion.requested` | Deletion requested | Starts the fan-out |
| `user.deletion.completed` | Gateway finished its own purge | One per module |
| `consent.changed` | Grant or revoke | Consumers must react immediately |
| `quiz.completed` | Quiz scored and stored | Drives card render and style context |
| `share.dna` | DNA card shared | |
| `vault.item.added` | Item created, asset ready | Triggers embedding |
| `vault.item.removed` | Item deleted | Removes from the legal pool |
| `vault.item.worn` | Wear logged | Strongest behavioural signal |
| `look.saved` | Look saved | |
| `look.shared` | Look shared | |
| `recommendation.feedback` | Feedback given | |
| `tailor.share.created` | Tailor image generated | |
| `integration.connected` | OAuth completed | |
| `integration.synced` | Import finished | |
| `integration.disconnected` | Revoked or failed | |
| `notification.sent` | Dispatch succeeded | |
| `notification.opened` | Open tracked | |
| `shop.clicked` | Affiliate click | `M1-2` |
| `admin.action.performed` | Any admin mutation | Mirrors the audit log |

---

## 2. Consumed

| Queue | Events | Handler behaviour |
|---|---|---|
| `gateway.card-ready` | `media.card.ready` | Store card URLs on the DNA result so polling resolves |
| `gateway.notify` | `quiz.completed`, `look.completed`, `look.failed`, `agent.suggestion.ready`, `integration.synced`, `media.card.ready` | Dispatch notifications subject to consent, quiet hours, and caps |
| `gateway.deletion` | `user.deletion.completed` | Update the ledger; close it when all modules acknowledge |

---

## 3. Handler rules

**Idempotent on `event_id`.** Every handler records processed identifiers and no-ops on redelivery. The notification path enforces this at the database level through `UNIQUE (user_id, template_id, event_id)`.

**Consent is re-checked at consume time, not publish time.** A user may revoke between the two. A handler that drops an event because consent was revoked has behaved correctly and records the drop rather than failing.

**Failures retry three times** (1s, 8s, 60s) then dead-letter. A non-empty DLQ is an alert with a runbook.

**No handler makes a synchronous call to `ase`.** If a handler needs styling work, it publishes an event; otherwise a slow model call blocks the queue.

---

## 4. Notification triggers

| Event | Template | Category | Consent |
|---|---|---|---|
| `look.completed` | `look_ready` | style | `essential` |
| `look.failed` | `look_failed` | activity | `essential` |
| `media.card.ready` | `dna_card_ready` | activity | `essential` |
| `agent.suggestion.ready` | `daily_fit` | style | `agent_proactive` |
| `integration.synced` | `pinterest_ready` | activity | `essential` |
| `quiz.completed` | `welcome_dna` | activity | `essential` |

Lifecycle campaigns (D1, D3, D7, D14, D30) are scheduled by the `lifecycle` worker rather than triggered by events, and all require `marketing_comms`. See [`../../00-product/retention-system.md`](../../00-product/retention-system.md).

Job-completion notifications are `essential` because they inform the user about work they explicitly requested — but they still respect quiet hours and frequency caps.
