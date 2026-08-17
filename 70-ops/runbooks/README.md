# Runbooks

One per alert defined in [observability.md](../observability.md). An alert without a runbook is noise that gets muted within a week.

| Runbook | Severity | Trigger |
|---|---|---|
| [Service Down](service-down.md) | SEV1 | `readyz` failing for 2 minutes |
| [Database Problems](database-issues.md) | SEV1 | Database unreachable or degraded |
| [Authentication Failures](auth-failures.md) | SEV1 | Auth failure rate above 20% for 5 minutes |
| [Cost Spike](cost-spike.md) | SEV1 | Cost per active user above $2/day |
| [PII Pipeline Failure](pii-pipeline-failure.md) | SEV1 | Any asset stored unredacted |
| [DSR SLA at Risk](dsr-sla.md) | SEV1 | Deletion request 5 days from its 30-day SLA |
| [Elevated Error Rate](elevated-errors.md) | SEV2 | 5xx above 5% for 5 minutes |
| [Generation Failures](generation-failures.md) | SEV2 | Failure rate above 10% for 15 minutes |
| [Model Provider Degraded](model-provider-degraded.md) | SEV2 | Fallback depth above 1 sustained for 15 minutes |
| [Dead-Letter Queue Not Empty](dlq-nonempty.md) | SEV2 | Any DLQ non-empty for 10 minutes |
| [Render Failures](render-failures.md) | SEV3 | Render failure rate above 5% |
| [Guardrail Trip Spike](guardrail-spike.md) | SEV3 | Trips above 5% of spree messages |
| [Embedding Coverage Below Threshold](embedding-coverage.md) | SEV3 | Coverage below 98% |
| [Notification Opt-Out Spike](optout-spike.md) | SEV3 | Opt-out above 5% monthly |
| [Funnel Drop](funnel-drop.md) | SEV3 | Quiz completion below 40% over 24 hours |
| [Apple Client Secret Expiring](apple-secret-expiry.md) | SEV3 | 30 days from expiry |
| [Review Queue Backing Up](review-queue.md) | SEV4 | More than 50 pending flagged sessions |

## Before anything else

1. **Stabilise, then diagnose.** With one person on call, understanding a problem while users are affected costs more than rolling back.
2. **Note the time of awareness.** If personal data may be involved, the 72-hour regulatory clock starts there.
3. **Reach for a flag before a deploy.** Kill switches and feature flags are runtime values in Redis and take effect in seconds.
