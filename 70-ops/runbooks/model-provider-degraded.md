# Runbook — Model Provider Degraded

**Severity:** SEV2 · **Trigger:** Fallback depth above 1 sustained for 15 minutes

## Check

```sql
SELECT model_id, count(*) FILTER (WHERE fallback_depth > 0) AS fell_back,
       count(*) AS total, avg(latency_ms) AS avg_latency
FROM ase.model_calls WHERE created_at > now() - interval '30 min'
GROUP BY model_id ORDER BY fell_back DESC;
```

## Act

1. Confirm against the provider status page.
2. Reorder the tier in `models.yaml` so a healthy model is primary. **This is a configuration change, not a code change** — that is precisely why model identifiers never appear in code.
3. If the whole tier is degraded, add a model from another provider.
4. If everything is down, verify the template paths are working and that the product remains usable.

## Verify

Fallback depth returns to 0. Latency returns to normal. Generation failure rate falls.

## Follow-up

A provider that degrades repeatedly should be demoted in the tier ordering permanently, not just during the incident.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
