# Runbook — Generation Failures

**Severity:** SEV2 · **Trigger:** Failure rate above 10% for 15 minutes

## Check

```sql
SELECT reason_code, stage_failed, count(*)
FROM ase.look_jobs WHERE status='failed' AND created_at > now() - interval '1 hour'
GROUP BY 1,2 ORDER BY 3 DESC;
```

`reason_code` names the stage and saves most of the investigation.

| Code | Meaning | Action |
|---|---|---|
| `empty_pool` | Not enough legal items | Usually correct for near-empty vaults. Investigate only if it rises for users with populated vaults — a filter is too strict |
| `model_unavailable` | Tier exhausted | See [model-provider-degraded](model-provider-degraded.md) |
| `render_failed` | Rendering failed | See [render-failures](render-failures.md) |
| `budget_exceeded` | Cap hit | See [cost-spike](cost-spike.md) |
| `timeout` | Stage too slow | Check queue depth and worker count |
| `guardrail_blocked` | Input refused | Expected for bad input; investigate spikes only |

## Act

If it is broad and cause is unclear, switch `renderer: composite` — it removes the slowest and most failure-prone stage and keeps the product working while you diagnose.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
