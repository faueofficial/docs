# Runbook — Review Queue Backing Up

**Severity:** SEV4 · **Trigger:** More than 50 pending flagged sessions

## Check

```sql
SELECT review_status, count(*) FROM ase.spree_sessions
WHERE flagged GROUP BY 1;
```

## Why it matters

The review queue is the loop that keeps guardrails and eval sets attached to reality. Reviewer verdicts feed the golden sets; without them, evaluation freezes at whatever was true on launch day and the guardrails begin to rot.

An unworked queue is not a backlog — it is a feedback loop that has silently stopped.

## Act

Triage in the admin console. For each session mark correct refusal, false positive, or missed detection.

- **False positives** → the guardrail is too broad; add the case and adjust.
- **Missed detections** → add to `spree_safety` immediately; this is a real gap.
- **Correct refusals** → sample a few into the eval set to prevent regression.

## Prevent

If the queue is consistently large, either the flagging threshold is too sensitive or the review cadence is too slow. Both are fixable; ignoring it is not.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
