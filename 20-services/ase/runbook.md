# ase — Runbook

**Stage:** MVP · **On-call:** Testimony

---

## 1. Start and stop

```bash
source .venv/bin/activate
uvicorn app.main:create_app --factory --reload --port 8001

# workers
arq app.workers.WorkerSettings            # generation, rendering, embedding
python -m app.events.consumer

curl localhost:8001/healthz
curl localhost:8001/readyz                # Postgres, Redis, RabbitMQ
curl localhost:8001/internal/admin/health # pipeline timings, budgets, index stats
```

`readyz` does **not** check model providers. A provider outage degrades to the template path; it must not remove the instance from rotation.

---

## 2. Generation failing

Read the `reason_code` on `look.failed` first — it names the stage and saves most of the investigation.

| `reason_code` | Meaning | Action |
|---|---|---|
| `empty_pool` | Not enough legal items | Usually correct behaviour for a near-empty vault. Investigate only if it rises for users with populated vaults — that means a filter is too strict |
| `model_unavailable` | Tier exhausted | Check provider status and `fallback_depth` in `model_calls`. Consider adding a model to the tier |
| `render_failed` | Assembly worked, rendering did not | Check the image provider. Switching `renderer` to `composite` restores service immediately |
| `budget_exceeded` | Spend cap hit | Check whether the cap is wrong or the usage is abnormal |
| `guardrail_blocked` | Input refused | Expected for bad input. Investigate only on a spike |
| `timeout` | Stage exceeded its limit | Check queue depth and worker count |

```sql
SELECT reason_code, stage_failed, count(*)
FROM ase.look_jobs
WHERE status = 'failed' AND created_at > now() - interval '1 hour'
GROUP BY 1, 2 ORDER BY 3 DESC;
```

### Generation slow

```sql
SELECT task, percentile_cont(0.95) WITHIN GROUP (ORDER BY latency_ms) AS p95,
       avg(fallback_depth) AS avg_fallback, avg(cache_hit::int) AS cache_rate
FROM ase.model_calls
WHERE created_at > now() - interval '1 hour'
GROUP BY task ORDER BY p95 DESC;
```

Rendering usually dominates. If the stylist pass is the slow stage instead, the prompt has probably grown or the pool is too large — over-fetch multiplier is the first thing to check.

---

## 3. Model provider problems

### Sustained fallback depth above 1

The primary model in a tier is unhealthy. Confirm which:

```sql
SELECT model_id, count(*) FILTER (WHERE fallback_depth > 0) AS fell_back, count(*) AS total
FROM ase.model_calls WHERE created_at > now() - interval '30 min'
GROUP BY model_id;
```

Reorder the tier in `models.yaml` and redeploy configuration. Model identifiers never appear in code precisely so this is a configuration change during an incident, not a code change.

### All models failing

Every task degrades to its template path automatically. Confirm the product is still usable — vault, saves, profile, and previously generated looks must all work. If they do not, something is depending on `ase` that should not be.

### Cost spike

```sql
SELECT task, sum(cost_usd) AS spend, count(*) AS calls
FROM ase.model_calls WHERE created_at > now() - interval '24 hours'
GROUP BY task ORDER BY spend DESC;
```

Usual causes, in order of likelihood: cache hit rate collapsed after a prompt change (the cache key includes the prompt version, so every prompt edit resets it), a retry loop, or genuine usage growth. Use the per-task kill switch if it is neither of the first two and the budget is at risk.

---

## 4. Embedding migration

```bash
curl -XPOST localhost:8001/internal/embeddings/reembed \
  -d '{"model_id":"<new>","subject_type":"vault"}'
```

Sequence, and none of it is optional:

1. **Dual-write.** New rows are written for the new model; the old model keeps serving reads.
2. **Shadow-evaluate.** Run the `look_rank` golden set against the new index. Compare nDCG against the current model.
3. **Flip reads** by configuration flag, per subject type.
4. **Soak** for at least a week, watching save rate and regenerate rate.
5. **Drop** old rows.

Never skip the soak. A worse embedding model shows up as a slow decline in save rate, not as an error.

### Embedding coverage below 98%

```sql
SELECT count(*) FILTER (WHERE e.item_id IS NULL) AS unembedded, count(*) AS total
FROM gateway.vault_items v
LEFT JOIN ase.vault_embeddings e
  ON e.item_id = v.id AND e.model_id = current_setting('faue.embed_model')
WHERE v.deleted_at IS NULL;
```

Unembedded items are invisible to generation, which users experience as "it ignored my new shirt". Check the `ase.embedding` queue and its DLQ; the usual cause is an image that failed to fetch.

---

## 5. Guardrails

### Trip rate spike

```sql
SELECT guardrail_verdict, count(*)
FROM ase.spree_messages
WHERE created_at > now() - interval '1 hour' AND guardrail_verdict IS NOT NULL
GROUP BY 1 ORDER BY 2 DESC;
```

Distinguish three causes: a genuine attack (sustained, from few users), a false-positive regression after a guardrail change (broad, sudden), or a new legitimate use pattern the intent classifier does not recognise (gradual).

Never loosen a guardrail during an incident. Add the failing cases to the `spree_safety` set, fix, and let CI prove it.

### Review queue growing

```sql
SELECT count(*) FROM ase.spree_sessions
WHERE flagged AND review_status = 'pending';
```

Flagged sessions feed the golden sets. A queue nobody works is a feedback loop that has quietly stopped.

---

## 6. Vector index

```sql
SELECT indexrelname, pg_size_pretty(pg_relation_size(indexrelid)) AS size, idx_scan
FROM pg_stat_user_indexes WHERE schemaname = 'ase' ORDER BY pg_relation_size(indexrelid) DESC;
```

Symptoms and causes:

- **Slow ANN queries** → `ef_search` too high, or the index no longer fits in memory.
- **Poor recall** → `ef_search` too low, or over-fetch multiplier too small for the filter selectivity.
- **Index bloat** → leftover rows from a migration that never dropped the old model.

Rebuilding an index is safe — vectors are derived data and can be recomputed from source images at any time.

---

## 7. Emergency controls

| Action | Effect |
|---|---|
| `kill-switch {task: "spree.chat"}` | Spree returns a templated message |
| `kill-switch {task: "look.reasoning"}` | Looks generate without narration |
| Set `renderer: composite` | Generation stops paying for image generation immediately |
| Lower `budget.user_daily` | Caps per-user spend during an abuse event |
| Set `ase_read_only: true` | Serves existing looks, refuses new generation |

Switching the renderer to `composite` is the fastest lever for a cost incident, and it degrades the product rather than breaking it.

---

## 8. What not to do

- **Do not loosen a guardrail to clear an alert.** Fix the cause, add the case to the eval set.
- **Do not hardcode a model id to work around a provider outage.** Reorder the tier in configuration.
- **Do not skip the soak** on an embedding migration.
- **Do not delete `look_impressions`** to reclaim space. It is unreconstructable and every future ranking model depends on it.
- **Do not run a full re-embed during peak hours.** It will compete with generation for the same workers.
