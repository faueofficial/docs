# Runbook — Render Failures

**Severity:** SEV3 · **Trigger:** Render failure rate above 5%

## Check

```sql
SELECT renderer, count(*) FILTER (WHERE status='failed') AS failed, count(*) AS total
FROM ase.look_jobs WHERE created_at > now() - interval '1 hour' GROUP BY renderer;
```

## Causes

| Cause | Action |
|---|---|
| Image provider outage | Switch `renderer: composite` |
| Guardrail rejecting output (faces, text, NSFW) | Check `render_safety` trip reasons; tighten the prompt |
| Timeout | Provider slow; raise the timeout or switch renderer |
| Quota exhausted | Check the provider account |

## Act

`renderer: composite` restores service immediately and costs nothing. Looks continue to generate using the user's own item photographs — a degradation in visual polish, not in function.

For users with empty vaults, `composite` cannot produce a look; those will return `empty_pool` until the generative path is restored.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
