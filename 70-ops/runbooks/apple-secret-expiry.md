# Runbook — Apple Client Secret Expiring

**Severity:** SEV3 · **Trigger:** 30 days from expiry

## Why this alert exists

Sign in with Apple requires an ES256 client secret JWT with a **hard six-month maximum lifetime**. When it expires, every Apple sign-in fails simultaneously and nothing else is affected — which makes it confusing to diagnose from symptoms alone.

## Act

```bash
python -m scripts.generate_apple_secret \
  --team-id $APPLE_TEAM_ID --key-id $APPLE_KEY_ID \
  --client-id app.faue.ios --private-key-path ./AuthKey.p8 --months 6
```

Set the result as `APPLE_CLIENT_SECRET` in the secret store and redeploy the gateway.

## Verify

Sign in with Apple on a real device. The JWKS path is unaffected; only the client secret changes.

## Follow-up

Set the next alert for five months from generation. This should never become an incident — the alert exists precisely so it stays a routine task.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
