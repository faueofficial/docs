# Runbook — Funnel Drop

**Severity:** SEV3 · **Trigger:** Quiz completion below 40% over 24 hours

## Check

Compare the funnel dashboard against the previous week. Identify the exact step where users leave.

| Drop at | Likely cause |
|---|---|
| Quiz start | Onboarding copy or the hook screen changed |
| A specific question | That question's copy or options are confusing |
| Submission | API errors — check the error rate for `/quiz/submit` |
| Result screen | Card rendering failing, leaving a blank result |

## Act

1. Check for a recent app or backend release; correlate with its timing.
2. Check `/quiz/submit` error rates — a silent 500 looks like abandonment in the funnel.
3. Check whether card rendering is failing; a result screen with no card reads as a broken app.
4. If it is a copy or content change, roll it back and re-test.

## Note

This is a **product alert**, not an infrastructure one. It is here because a silent product regression is as damaging as an outage and far easier to miss — nothing errors, users simply stop.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
