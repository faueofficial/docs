# Observability

**Stage:** MVP · **Dashboards surfaced in:** the FAUE admin console

---

## 1. Stack

| Concern | Tool |
|---|---|
| Traces | OpenTelemetry → Tempo |
| Metrics | Prometheus |
| Logs | Structured JSON → Loki |
| Dashboards | Grafana, embedded in admin |
| Errors | Sentry |
| **LLM traces, prompts, cost, evals** | **Langfuse** |
| Product analytics | PostHog, via the single analytics consumer |

Grafana Cloud's free tier covers MVP volume. Langfuse is adopted from the start rather than retrofitted — attaching it later means losing the history that would have explained the early quality problems.

---

## 2. Tracing

One `trace_id` from the Flutter client through gateway, `ase`, the model call, and back. Propagated over HTTP headers and through event envelopes, so asynchronous work stays attached to the user action that caused it.

```
POST /v1/looks/generate                    trace 4bf92f35…
├─ gateway: consent check                  2ms
├─ gateway → ase: enqueue                  40ms
└─ worker: generate                        28s
   ├─ style context                        120ms
   ├─ retrieve (ANN)                       80ms
   ├─ filter → legal pool                  15ms
   ├─ colour prior                         8ms
   ├─ stylist pass (model)                 3.2s
   ├─ validate                             2ms
   ├─ rank (model)                         900ms
   ├─ render (generative)                  22s
   └─ explain (model)                      1.1s
```

A user complaint must resolve to the exact prompt version, model, tool calls, and candidate set behind their result. That is the whole point of the `instance` field in error responses.

---

## 3. Logging

Structured JSON, always carrying `trace_id`, `service`, `environment`, and `user_id` where a user is in scope.

**Never logged:** email, phone, name, username, measurements, image content, prompt text containing user input, tokens, or precise location. A CI check fails the build on PII-shaped log statements.

| Level | Meaning |
|---|---|
| `ERROR` | Needs human action |
| `WARNING` | A degraded path was taken |
| `INFO` | A state change worth reconstructing |
| `DEBUG` | Local only |

### Outcomes

Most operations here can half-succeed: a notification reaches the inbox but not
email, a relay pass publishes eight of ten rows. A boolean calls all of those
`true`, and nobody investigates a `true`.

`faue_core.telemetry.outcome.Outcome` makes the middle state expressible:

| Status | `ok` | `degraded` | Level |
|---|---|---|---|
| `success` | yes | no | `INFO` |
| `partial` | yes | **yes** | `WARNING` |
| `failure` | no | yes | `ERROR` |

The level is derived from the status rather than chosen by the caller, so a
failure cannot be logged at `INFO` and quietly leave the error rate.

A partial outcome must name what was skipped and why; a failure must carry a
reason. Both are validated against `^[a-z][a-z0-9_]{2,48}$` — dashboards group
by these values, and a free-text sentence produces one bucket per incident,
which is the same as no grouping.

Reason codes are deliberately **not** scrubbed. The scrubber is key-based, and
`email` is a delivery channel as well as a PII field name, so scrubbing turned
`{"email": "no_verified_address"}` into `{"email": "[redacted]"}` — deleting the
only part of the line that said what went wrong. The regex is what makes that
safe: no address or phone number can match it.

An HTTP 4xx is `partial`, not `failure`. The request was refused for a stated
reason, which is the system working; counting it as an error buries the 5xx that
need someone.

Exceptions are logged once, at the boundary that handles them. Re-logging on the way up produces duplicate alerts and makes error rates meaningless.

Retention 30 days.

---

## 4. The six dashboards

All embedded in admin, so staff have one place rather than two.

### 1 · Product funnel
Signups, quiz starts and completions, vault items added, looks generated and saved, fabric uploads, tailor shares, shares, D1/D7/D30 retention. Cohorted weekly.

### 2 · AI health
Per task: p50/p95/p99 latency, error rate, fallback depth, cache hit rate, tokens, cost per call, **cost per active user**. Model mix over time.

### 3 · Quality
Save rate, **regenerate rate**, feedback ratio, agent accept rate, groundedness, refusal rate, fabric correction rate. Segmented by prompt version so a regression is attributable.

### 4 · Safety
Guardrail trips by guard and category, injection attempts, PII pipeline rejections, review queue depth, moderation false-positive rate.

### 5 · Data health
Vault items, embedding coverage, style library size, dead-link rate (M1-2), stale items, ingest job success, DLQ depth.

### 6 · Infrastructure
API latency and error rate, database connections and slow queries, Redis memory and evictions, queue depth and consumer lag, worker throughput, instance health.

---

## 5. Alerts

Every alert has a runbook in [`runbooks/`](runbooks/). An alert without one is noise that will be muted within a week.

### Page immediately

| Alert | Threshold | Runbook |
|---|---|---|
| Gateway down | `readyz` failing 2 min | [`service-down.md`](runbooks/service-down.md) |
| Error rate | 5xx > 5% for 5 min | [`elevated-errors.md`](runbooks/elevated-errors.md) |
| Database unreachable | 1 min | [`database-issues.md`](runbooks/database-issues.md) |
| Auth failure rate | > 20% for 5 min | [`auth-failures.md`](runbooks/auth-failures.md) |
| **Cost per user** | > $2/day | [`cost-spike.md`](runbooks/cost-spike.md) |
| PII pipeline bypass | Any asset unredacted | [`pii-pipeline-failure.md`](runbooks/pii-pipeline-failure.md) |
| DSR SLA | 5 days from breach | [`dsr-sla.md`](runbooks/dsr-sla.md) |

### Notify during hours

| Alert | Threshold | Runbook |
|---|---|---|
| Generation failure rate | > 10% for 15 min | [`generation-failures.md`](runbooks/generation-failures.md) |
| Fallback depth | > 1 sustained 15 min | [`model-provider-degraded.md`](runbooks/model-provider-degraded.md) |
| Dead-letter queue | Non-empty 10 min | [`dlq-nonempty.md`](runbooks/dlq-nonempty.md) |
| Guardrail trips | > 5% of messages | [`guardrail-spike.md`](runbooks/guardrail-spike.md) |
| Embedding coverage | < 98% | [`embedding-coverage.md`](runbooks/embedding-coverage.md) |
| Render failure rate | > 5% | [`render-failures.md`](runbooks/render-failures.md) |
| Notification opt-out | > 5% monthly | [`optout-spike.md`](runbooks/optout-spike.md) |
| Quiz completion | < 40% over 24h | [`funnel-drop.md`](runbooks/funnel-drop.md) |
| Apple secret expiry | 30 days out | [`apple-secret-expiry.md`](runbooks/apple-secret-expiry.md) |
| Review queue depth | > 50 pending | [`review-queue.md`](runbooks/review-queue.md) |

Two of these are product alerts rather than infrastructure alerts — quiz completion and opt-out rate. They are here because a silent product regression is as damaging as an outage and far easier to miss.

---

## 6. Metric conventions

```
faue_http_requests_total{service, route, method, status}
faue_http_duration_seconds{service, route}
faue_model_calls_total{task, tier, model, cache_hit, fallback_depth}
faue_model_cost_usd{task, model}
faue_generation_duration_seconds{stage, renderer}
faue_guardrail_trips_total{guard, category}
faue_queue_depth{queue}
faue_embedding_coverage_ratio{subject_type, model_id}
```

Low cardinality on labels. `user_id` is never a label — it would blow up the time series and it is what traces are for.

---

## 7. On-call

One person. Practical consequences that shape everything above:

- **Few alerts, all actionable.** An alert that does not require action gets muted, and muting is contagious.
- Automatic remediation where possible: rollback on smoke-test failure, circuit breakers, degraded paths.
- Every alert has a runbook, so the response does not depend on memory at 3 a.m.
- Non-urgent findings go to a daily review, not a page.

---

## 8. Retention

| Data | Retention |
|---|---|
| Metrics | 15 days raw, 90 days aggregated |
| Traces | 7 days, 100% sampled at MVP volume |
| Logs | 30 days |
| Langfuse traces | 90 days |
| `model_calls` | 90 days, aggregates longer |
| Sentry | 90 days |

100% trace sampling is affordable at MVP volume and enormously more useful than sampled tracing when investigating a single user's complaint. Revisit when volume makes it expensive.
