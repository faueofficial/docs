# Runbook — Elevated Error Rate

**Severity:** SEV2 · **Trigger:** 5xx above 5% for 5 minutes

## Check

Which route, which status, since when:

```
sum by (route, status) (rate(faue_http_requests_total{status=~"5.."}[5m]))
```

Then pull one trace id from Sentry and follow it end to end.

## Common causes

| Pattern | Likely cause |
|---|---|
| One route only | Recent code change to that handler |
| All routes | Database, Redis, or a deploy |
| Started at a deploy | Roll back first, diagnose after |
| Gradual climb | Resource exhaustion — connections, memory, disk |
| Only write routes | Database connection pool exhausted |

## Act

Rolling back is almost always right if a deploy preceded it. Diagnosing a live error spike while users are affected is the wrong order.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
