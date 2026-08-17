# Runbook — Authentication Failures

**Severity:** SEV1 · **Trigger:** Auth failure rate above 20% for 5 minutes

## Check, in this order

```sql
SELECT provider, count(*) FROM gateway.auth_identities
WHERE last_used_at > now() - interval '1 hour' GROUP BY provider;
```

1. **Email provider** — most likely. Magic links are the primary path; if email stops, sign-ins stop and nothing else looks wrong. Check the provider dashboard and `notify_deliveries` failures.
2. **Redis** — magic-link tokens live only in Redis. If it is down, every link consumption fails.
3. **Apple client secret expired** — breaks all Apple sign-ins simultaneously and nothing else. ES256 JWT, six-month maximum life. Regenerate from `APPLE_PRIVATE_KEY`.
4. **JWKS fetch failing** — provider key rotation with a cached miss. Force-refresh the JWKS cache.

## Refresh-token family revocations

A spike in `refresh_reuse_detected` almost always means the client is issuing parallel refresh calls, not that tokens are being stolen. Confirm by looking for near-simultaneous refresh attempts per user, then fix the client to serialise refreshes.

## Act

Email outage: switch to the backup provider if configured, otherwise post a status notice — there is no workaround for the user.
Apple secret: regenerate and deploy. Roughly 15 minutes.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
