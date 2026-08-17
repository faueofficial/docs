# Incident Response

**Stage:** MVP · **On-call:** Testimony (one person)

---

## 1. Severity

| Sev | Meaning | Examples | Response |
|---|---|---|---|
| **SEV1** | Product unusable, or personal data exposed | Gateway down, database lost, PII breach, auth broken for everyone | Immediate, drop everything |
| **SEV2** | Core feature broken, or money leaking | Generation failing broadly, cost spike, all model providers down | Within 1 hour |
| **SEV3** | Degraded but working | Elevated errors, slow generation, one channel failing | Same day |
| **SEV4** | Minor | Cosmetic, single-user issue, non-urgent alert | Next working day |

**Any suspected personal data exposure is SEV1**, regardless of scale, because the 72-hour regulatory clock starts at awareness rather than at confirmation.

---

## 2. Procedure

```
1  ACKNOWLEDGE   silence the alert, note the start time
2  ASSESS        severity, blast radius, whether data is exposed
3  STABILISE     stop the bleeding — rollback, kill switch, flag, rate limit
4  COMMUNICATE   status page or in-app notice if users are affected
5  DIAGNOSE      only after stabilising
6  FIX           the smallest change that resolves it
7  VERIFY        dashboards, smoke tests, the original signal
8  RECORD        timeline, cause, remediation, prevention
```

**Stabilise before diagnosing.** With one person on call, an hour spent understanding a problem while users cannot sign in is an hour of unnecessary damage. Roll back first; the cause will still be there afterwards.

---

## 3. Stabilisation levers

Fastest first, in the order to reach for them:

| Lever | Effect | Time |
|---|---|---|
| `railway rollback` | Previous image, immediately | ~1 min |
| Feature flag off | Disables one feature | Seconds, no deploy |
| AI kill switch per task | That task degrades to its template path | Seconds |
| `renderer: composite` | Stops image-generation spend entirely | Seconds |
| Lower budget caps | Caps runaway cost | Seconds |
| `maintenance_mode` | Everything but auth returns 503 | Seconds |
| Rate limit tightening | Slows abuse | Seconds |

All flags are runtime values in Redis. An incident is the wrong time to wait for CI.

---

## 4. Data breach

If personal data may have been exposed:

```
HOUR 0    Contain — revoke keys, rotate secrets, disable the path
          Record the time of awareness. The 72-hour clock starts HERE.
HOUR 0-6  Assess — what data, how many people, what risk
          Use the audit log and the RoPA to establish scope
HOUR 6-24 Decide on notification (assume yes unless the risk is genuinely nil)
HOUR <72  Notify the regulator: NDPC (Nigeria), and the relevant DPA for EU users
          Notify affected users where risk is high
AFTER     Full write-up, remediation, prevention
```

Do not investigate quietly first and escalate later. The clock has already started, and a delay is itself a compliance failure.

Scope questions the audit log should answer: who accessed what, when, from where, and with what justification. If it cannot answer those, that gap is itself a finding.

---

## 5. Communication

| Audience | When | Where |
|---|---|---|
| Users | SEV1 and SEV2 affecting them | In-app notice, status page |
| Oladunni | SEV1 and SEV2 | Direct message |
| Frontend engineer | Anything affecting the API | Direct message |
| Regulator | Data breach | Formal, within 72 hours |

Tell users what is broken, what still works, and when you will update — not the cause. "Look generation is unavailable; your vault and saved looks are fine. Update in an hour."

---

## 6. Post-incident

Within two working days for SEV1 and SEV2:

```markdown
# Incident YYYY-MM-DD — <short title>
Severity · Duration · Users affected · Data exposed (yes/no)

## Timeline
Detection, actions, resolution, with times

## Root cause
What actually happened

## Why it was not caught earlier
Monitoring gap, test gap, or accepted risk

## Remediation
Done, and planned with owners

## Prevention
The change that stops recurrence
```

**Blameless.** The question is always what in the system allowed this, not who did it. At a two-person team the answer is usually "the system had no guard here", and adding the guard is the output.

Every incident that could recur produces either a test, an alert, or a runbook. An incident that produces none of those has not been learned from.

---

## 7. Contacts

| Need | Contact |
|---|---|
| On-call | Testimony |
| Product | Oladunni |
| Frontend | Frontend engineer |
| Hosting | Railway support |
| Database | Provider support |
| Regulator (Nigeria) | NDPC |
| Security reports | faueofficial@gmail.com |

---

## 8. Realistic first incidents

Worth having thought about before they happen, because these are the likely ones at this stage:

**Apple client secret expires.** Every Apple sign-in fails at once, nothing else is affected. Regenerate the ES256 JWT. The 30-day expiry alert exists to prevent this entirely.

**Model provider outage.** Fallback and template paths should absorb it. Verify the product is still usable; if it is not, something depends on `ase` that should not.

**Cost spike from generation abuse.** Budget caps should contain it before it is material. Check whether the caps were set too high rather than assuming an attack.

**Email deliverability collapse.** Nobody can sign in and nothing looks broken on the dashboards, which makes it slow to spot. Auth failure rate is the alert that catches it.

**Migration locks a table.** Long-running `ALTER` on a live table. This is what expand-only migrations exist to prevent; if it happens, it means a migration was not reviewed properly.

**A user reports a bad recommendation.** Not an incident, but it needs a path: get the trace id, find the prompt version and candidate set, add the case to the eval set. That loop is what keeps quality from drifting.
