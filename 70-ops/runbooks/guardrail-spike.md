# Runbook — Guardrail Trip Spike

**Severity:** SEV3 · **Trigger:** Trips above 5% of spree messages

## Check

```sql
SELECT guardrail_verdict, count(*), count(DISTINCT session_id) AS sessions
FROM ase.spree_messages
WHERE created_at > now() - interval '1 hour' AND guardrail_verdict IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC;
```

## Read the pattern

| Pattern | Cause | Action |
|---|---|---|
| Sustained, few users | Deliberate attempts | Rate-limit those accounts; add the cases to `spree_safety` |
| Broad, sudden | False-positive regression after a guardrail change | Roll back the guardrail change |
| Gradual | Legitimate usage the intent classifier misreads | Update the classifier, not the guardrail |

## Do not

**Never loosen a guardrail to clear an alert.** Add the failing cases to the eval set, fix properly, let CI prove it. A guardrail loosened during an incident stays loose.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
