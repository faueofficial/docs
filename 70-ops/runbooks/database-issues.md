# Runbook — Database Problems

**Severity:** SEV1 · **Trigger:** Database unreachable or degraded

## Check

```sql
SELECT count(*), state FROM pg_stat_activity GROUP BY state;
SELECT pid, now()-query_start AS dur, left(query,80)
FROM pg_stat_activity WHERE state='active' ORDER BY dur DESC LIMIT 10;
SELECT pg_size_pretty(pg_database_size(current_database()));
```

## Causes and actions

| Cause | Action |
|---|---|
| Connection pool exhausted | Most common. Check instance count × pool size against the server limit. Reduce pool size before adding instances |
| Long-running query blocking | Identify with the query above; `pg_cancel_backend(pid)` |
| Migration holding a lock | Wait if it will finish; cancel if it will not. This is why migrations are expand-only |
| Disk full | Check WAL growth and table bloat; a stalled replica is a common cause |
| Provider incident | Check the provider status page before assuming it is you |

## Do not

Do not restart the database to clear a lock without knowing what holds it. Do not increase the pool size to fix exhaustion — that moves the failure to the server. Do not run `VACUUM FULL` on a live table.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
