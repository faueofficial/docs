# ase — Events

**Stage:** MVP · **Catalog:** [`../../10-architecture/event-catalog.md`](../../10-architecture/event-catalog.md)

---

## 1. Produced

| Event | Emitted when |
|---|---|
| `look.requested` | Generation job created |
| `look.completed` | Looks generated and rendered |
| `look.failed` | Any pipeline stage failed terminally |
| `fabric.styled` | Fabric classified and styles suggested |
| `agent.suggestion.ready` | Agent produced a suggestion |
| `ai.budget.exceeded` | A user, task, or global budget was hit |
| `ai.guardrail.tripped` | A guardrail blocked input or output |

`look.failed` carries `reason_code` and `stage`, which is what makes generation failures diagnosable in aggregate rather than one trace at a time.

---

## 2. Consumed

| Queue | Events | Handler |
|---|---|---|
| `ase.style-context` | `quiz.completed` | Build the DNA vector, cache the context |
| | `vault.item.worn` | Update the behaviour vector, increment wear count |
| | `vault.item.added` / `.removed` | Mark the context stale |
| | `integration.synced` | Build aspiration vectors from imported pins |
| | `recommendation.feedback` | Adjust the behaviour vector |
| | `consent.changed` | Drop cached context when `personalization` or `ai_processing` is revoked |
| | `user.body_profile.updated` | Refetch derived constraints |
| `ase.embedding` | `vault.item.added` | Embed and index the item |
| | `catalog.product.upserted` | Embed and index the product (`M1-2`) |
| | `catalog.product.unavailable` | Remove from the legal pool (`M1-2`) |
| `ase.deletion` | `user.deletion.requested` | Purge all ase-owned rows, then acknowledge |

---

## 3. Handler rules

**Style context rebuilds are debounced.** A user adding ten vault items in a minute produces ten events; the handler marks the context stale and a worker rebuilds once. Rebuilding per event would be ten times the cost for the same result.

**Embedding is idempotent on `image_hash`.** A redelivered `vault.item.added` for an unchanged image is a no-op, not a second embedding.

**Consent revocation is immediate and destructive.** Revoking `personalization` drops the cached style context; revoking `ai_processing` additionally disables generation for that user. Both take effect at consume time.

**Deletion must complete before acknowledging.** `ase.deletion` purges style context, embeddings, looks, jobs, fabric analyses, spree sessions and messages, agent memory and runs, and model call rows for that user — then emits `user.deletion.completed{module: "ase"}`. Acknowledging early would close the ledger on work that never happened.

**No handler calls the gateway synchronously.** If a handler needs user data it should already have it in the event, or it should not need it.

---

## 4. Ordering

Handlers assume nothing about ordering. `vault.item.worn` can arrive before `vault.item.added` after a retry — the wear handler tolerates an unknown item by recording it and letting the next context rebuild pick it up.

Where sequence genuinely matters, the handler reads current state from the database rather than reconstructing it from event order.
