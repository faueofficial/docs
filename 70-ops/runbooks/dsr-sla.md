# Runbook — DSR SLA at Risk

**Severity:** SEV1 · **Trigger:** Deletion request 5 days from its 30-day SLA

## Check

A request in its **waiting period** (`purge_after` in the future, `gateway` not in `modules_done`) is not late: the
account is signed out and the data is kept on purpose. The 30-day deadline still counts from `requested_at`.
If `purge_after` has passed and `gateway` is not done, the `dsr_purge` worker is not running.

```sql
SELECT id, user_id, modules_pending, modules_done, requested_at, purge_after, sla_due_at
FROM gateway.deletion_ledger
WHERE completed_at IS NULL AND cancelled_at IS NULL ORDER BY sla_due_at;
```

## Act

`modules_pending` names what has not acknowledged.

| Cause | Action |
|---|---|
| Consumer not running | Restart it; the event will redeliver |
| Event never reached the queue | Check the outbox and the binding; republish |
| Module purged but failed to acknowledge | Verify zero rows for that user, then acknowledge manually and record why |
| Third party failing | Check the API; retry, and record if permanently unavailable |

## Verify

Before closing the ledger, confirm the data is actually gone:

```sql
SELECT count(*) FROM gateway.vault_items  WHERE user_id = '<uuid>';
SELECT count(*) FROM ase.looks            WHERE user_id = '<uuid>';
SELECT count(*) FROM ase.vault_embeddings WHERE user_id = '<uuid>';
```

All must be zero. The 30-day SLA is a legal obligation, not a target.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
