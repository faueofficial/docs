# Runbook — Service Down

**Severity:** SEV1 · **Trigger:** `readyz` failing for 2 minutes

## Check

```bash
railway status --service api-gateway
curl -sf https://api.faue.app/healthz || echo "process down"
curl -s  https://api.faue.app/readyz  | jq
```

`healthz` failing = the process is down. `readyz` failing alone = a dependency is unreachable; `readyz` names which.

## Act

| Finding | Action |
|---|---|
| Deployed in the last 30 minutes | `railway rollback --service api-gateway --to <previous-sha>` |
| Dependency unreachable | Follow [database-issues](database-issues.md) or check Redis/RabbitMQ status |
| Out of memory | Check recent memory graph; restart, then investigate the leak |
| No obvious cause | Restart the service, then diagnose from logs |

`ase` being down is **not** SEV1. Generation degrades; vault, saves, profile, and existing looks keep working. If the gateway also fails when `ase` is down, that is a bug — the gateway must not depend on `ase` for `readyz`.

## Verify

Smoke tests from [deployment.md](../deployment.md) §9.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
