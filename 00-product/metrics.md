# Metrics

**Stage:** MVP · **Dashboards:** [`../70-ops/observability.md`](../70-ops/observability.md)

What is measured, what the thresholds are, and what would tell us we are wrong.

---

## 1. North star

**Weekly looks worn.**

Not looks generated, not sessions, not signups — looks a user confirmed they actually wore. It is the only metric that cannot be inflated by a good demo or a push notification, and it sits at the exact point where FAUE created value in the real world.

It also has a weakness worth naming: it depends on users logging wear, which they will do inconsistently. Until the wear-log rate is healthy, **looks saved** is the working proxy.

---

## 2. Funnel

| Step | Event | MVP target |
|---|---|---|
| App opened | `app_opened` | — |
| Signup started | `POST /auth/link/request` | 40% of first opens |
| Signup completed | `user.registered` | 70% of starts |
| Quiz started | `quiz_started` | 90% of signups |
| Quiz completed | `quiz.completed` | **60% of starts** |
| DNA card shared | `share.dna` | 10% of completions |
| Vault item added | `vault.item.added` | 50% of quiz completions |
| Look generated | `look.requested` | **70% of quiz completions** |
| Look saved | `look.saved` | **25% of looks generated** |
| Look shared | `look.shared` | 8% of looks saved |
| Fabric uploaded | `fabric.uploaded` | 20% of active users monthly |
| Tailor share | `tailor.share.created` | **15% of fabric uploads** |
| Wear logged | `vault.item.worn` | 15% of saved looks |
| Returned in 14 days | derived | **20%, unprompted** |

Bold entries are the launch criteria in [`mvp-scope.md`](mvp-scope.md).

"Unprompted" excludes sessions opened from a push notification or an email within an hour of receiving one. A return you paid for with a notification is not the same signal as a return you earned.

---

## 3. Retention

| Metric | Definition | Target |
|---|---|---|
| D1 | Returned the next day | 25% |
| D7 | Returned within 7 days | 30% |
| D14 unprompted | Returned within 14 days, no notification | 20% |
| D30 | Returned within 30 days | 15% |
| WAU/MAU | Weekly over monthly active | 0.30 |
| Resurrection | Dormant 30 days, then returned | 5% monthly |

Retention is cohorted weekly. A single blended number hides that the cohort after a fix behaves differently from the cohort before it.

---

## 4. Quality

| Metric | Definition | Target |
|---|---|---|
| Look save rate | Saved / generated | ≥ 25% |
| Regenerate rate | Regenerated / generated | ≤ 30% |
| Negative feedback rate | `not_my_style` / looks viewed | ≤ 15% |
| Agent accept rate | Accepted / suggested | ≥ 20% |
| Fabric classification accuracy | Against stylist labels | ≥ 85% |
| Fabric correction rate | User overrode detected type | ≤ 15% |
| Spree groundedness | Claims traceable to tool results | ≥ 95% |
| Spree refusal accuracy | Correct refusals / should-refuse | 100% |

**Regenerate rate is the sharpest early quality signal.** A user regenerating means the first answer was not good enough, and unlike a save it requires no extra effort to express. Watch it before the save rate.

---

## 5. Performance

| Metric | Target (p95) |
|---|---|
| API latency, reads | 200 ms |
| Quiz submission | 400 ms |
| Look generation, end to end | 45 s |
| Fabric analysis | 15 s |
| Spree first token | 2 s |
| App cold start | 2.5 s |
| Generation failure rate | ≤ 5% |
| Render failure rate | ≤ 3% |

---

## 6. Cost

| Metric | Target |
|---|---|
| Infrastructure + model spend | ≤ $150/month at MVP |
| Cost per active user per month | ≤ $0.50 |
| Cost per generated look | ≤ $0.05 |
| Model fallback depth | ≤ 1 sustained |
| Semantic cache hit rate | ≥ 40% |
| **CDN bandwidth** | Track against Cloudinary's 25 GB/month free tier |

**Bandwidth, not storage, is the binding constraint on images.** A vault grid is many small requests on metered connections. Storage will sit comfortably inside the free tier long after bandwidth stops doing so, and approaching the bandwidth cap is the trigger to move primary storage to R2 — a copy job, because uploads already go through the `StorageProvider` interface.

Cost per generated look is the number that decides whether generative rendering stays the default. If it rises above the target, the answer is the composite renderer, not a smaller budget for everything else.

---

## 7. Safety and compliance

Guardrail metrics — these do not have "targets" so much as thresholds that trigger investigation.

| Metric | Threshold |
|---|---|
| Guardrail trip rate | Investigate above 5% of spree messages |
| Injection attempts detected | Any sustained rise is investigated |
| PII pipeline rejection rate | Investigate above 10% of uploads |
| Face-detection recall (eval) | ≥ 0.98, hard gate |
| Notification opt-out rate | Investigate above 5% monthly |
| DSR completion within SLA | 100%, no exceptions |
| Support tickets citing a wrong recommendation | Track qualitatively from the first one |

Notification opt-out is a guardrail on retention work: a campaign that lifts D7 while pushing opt-outs up has borrowed retention rather than earned it.

---

## 8. Disproof signals

If these appear, stop adding features and reconsider the product.

| Signal | What it means |
|---|---|
| Quiz completion below 40% | The quiz is too long, unclear, or uncompelling — and it gates everything |
| Look save rate below 10% | Recommendations are not good enough. Nothing downstream matters until this is fixed |
| Regenerate rate above 50% | The first answer is usually wrong |
| Zero tailor shares in the first 50 fabric uploads | The bespoke output is not actionable, which kills the main differentiator |
| Zero unprompted returns in 30 days | No habit is forming; the product is a novelty |
| Zero DNA card shares | The viral loop is broken and acquisition has no engine |
| Cost per active user above $2 | Unit economics do not work; the renderer or the model tier must change |

---

## 9. Instrumentation

Events flow through `faue.events` to a single analytics consumer, not through SDKs embedded in each service — one fan-out point, one place to fix when the vendor changes, and no PII leaking into a third party by accident.

Every analytics event carries a pseudonymous user identifier, never an email or phone number. Event definitions live in [`../10-architecture/event-catalog.md`](../10-architecture/event-catalog.md); the analytics consumer derives funnel steps from them rather than requiring separate tracking calls.

**Rule:** if a metric here has no event behind it, either the event is missing or the metric is decorative. Both are worth fixing.
