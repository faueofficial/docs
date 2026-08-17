# Runbook — Notification Opt-Out Spike

**Severity:** SEV3 · **Trigger:** Opt-out above 5% monthly

## Check

```sql
SELECT category, channel, count(*) FILTER (WHERE NOT enabled) AS opted_out, count(*) AS total
FROM gateway.notify_preferences GROUP BY 1,2;

SELECT template_id, count(*) AS sent
FROM gateway.notify_deliveries
WHERE created_at > now() - interval '7 days' GROUP BY 1 ORDER BY 2 DESC;
```

## Causes

| Cause | Action |
|---|---|
| Too many sends | Tighten the frequency cap |
| Poorly timed | Check quiet-hours enforcement and send times |
| Low-value content | Review the template; is it worth interrupting someone for? |
| A new campaign | Correlate the spike with its launch date |

## Why it matters

Opt-out is nearly irreversible. It is a **guardrail metric on retention work**: a campaign that lifts D7 while pushing opt-outs up has borrowed retention rather than earned it, and the borrowing cannot be repaid.

## Act

Pause the offending campaign, reduce the frequency cap, and re-examine whether the notification deserved to exist.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
