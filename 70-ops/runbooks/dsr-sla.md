# Runbook — DSR SLA at Risk

**Severity:** SEV1 · **Trigger:** Deletion request 5 days from its 30-day SLA

## Check

```sql
SELECT id, user_id, modules_pending, requested_at, sla_due_at
FROM gateway.deletion_ledger
WHERE completed_at IS NULL ORDER BY sla_due_at;
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
