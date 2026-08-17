# Runbook — Cost Spike

**Severity:** SEV1 · **Trigger:** Cost per active user above $2/day

## Check

```sql
SELECT task, sum(cost_usd) AS spend, count(*) AS calls,
       avg(cache_hit::int) AS cache_rate
FROM ase.model_calls WHERE created_at > now() - interval '24 hours'
GROUP BY task ORDER BY spend DESC;

SELECT user_id, sum(cost_usd) FROM ase.model_calls
WHERE created_at > now() - interval '24 hours'
GROUP BY user_id ORDER BY 2 DESC LIMIT 20;
```

## Causes

| Pattern | Cause | Action |
|---|---|---|
| One user dominating | Abuse or a client retry loop | Lower their cap; check for a client bug |
| Cache rate collapsed | A prompt change reset the cache keys | Expected for a day or two; not a regression |
| Rendering dominates | Generation volume up, or a retry loop | `renderer: composite` stops it immediately |
| Even rise across tasks | Genuine growth | Reassess the budget, not the code |

## Act

Fastest lever is switching the renderer to `composite` — image generation is the dominant variable cost and the switch degrades the product rather than breaking it.

Then per-user caps, then per-task kill switches. `ai.budget.exceeded` should have fired before it became material; if it did not, the caps are set too high.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
