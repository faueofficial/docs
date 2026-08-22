# api-gateway — Runbook

**Stage:** MVP · **On-call:** Testimony

---

## 1. Start and stop

```bash
# local
source .venv/bin/activate
uvicorn app.main:create_app --factory --reload --port 8000

# workers (separate processes)
arq app.workers.WorkerSettings
python -m app.events.consumer

# health
curl localhost:8000/healthz     # process alive; never fails for a downstream outage
curl localhost:8000/readyz      # dependencies reachable; failing removes from rotation
curl localhost:8000/metrics     # Prometheus
```

`readyz` checks Postgres, Redis, and RabbitMQ. It deliberately does **not** check `ase` — the gateway must stay in rotation and serve vault, saves, and profile while generation is down.

---

## 2. Common failures

### Sign-ins failing across the board

Check, in order:

1. **Email provider.** `notify_deliveries` with `status = 'failed'` rising, or provider dashboard. Most likely cause.
2. **Redis.** Magic-link tokens live only in Redis. If Redis is down, every sign-in fails while `readyz` correctly reports unready.
3. **Apple client secret expired.** ES256 JWT, maximum six-month life. Expiry breaks all Apple sign-ins simultaneously and nothing else. Regenerate from `APPLE_PRIVATE_KEY`.
4. **JWKS fetch failing.** Google or Apple key rotation with a cached miss. Force-refresh the JWKS cache.

```sql
-- recent sign-in attempts by provider
SELECT provider, count(*), max(last_used_at)
FROM gateway.auth_identities
WHERE last_used_at > now() - interval '1 hour'
GROUP BY provider;
```

### Refresh token families being revoked

A spike in `refresh_reuse_detected` almost always means the client is issuing **parallel refresh calls**, not that tokens are being stolen. Confirm by checking whether the affected users have several near-simultaneous refresh attempts, then fix the client to serialise.

```sql
SELECT user_id, count(*) AS revoked
FROM gateway.refresh_tokens
WHERE revoked_at > now() - interval '1 hour'
GROUP BY user_id ORDER BY revoked DESC LIMIT 20;
```

### Dead-letter queue not empty

```bash
rabbitmqctl list_queues name messages | grep dlq
```

Read a message, find its `trace_id`, and locate the original failure in logs. Fix the handler, then replay from the DLQ. Never delete a DLQ message without recording what it was — it represents a state change that some consumer never saw.

### Notifications not arriving

Work down the chain: was the event published (`gateway.outbox` with `published_at` set)? Did the consumer receive it? Was it suppressed by consent, quiet hours, or the frequency cap? Did the channel accept it?

```sql
SELECT status, failure_reason, count(*)
FROM gateway.notify_deliveries
WHERE created_at > now() - interval '1 hour'
GROUP BY 1, 2;
```

`status = 'suppressed'` is usually correct behaviour, not a fault.

### Outbox backing up

```sql
SELECT count(*), min(occurred_at)
FROM gateway.outbox WHERE published_at IS NULL;
```

If the relay has stopped, events are safe but stale — nothing is lost. Restart the relay. If a single row keeps failing, its `attempts` will be climbing; move it aside rather than letting it block the queue.

---

## 3. Key rotation

### Encryption master key

```
1. Add the new key as ENCRYPTION_MASTER_KEY_NEXT
2. Deploy — the service reads with either key, writes with the current one
3. Run the re-encrypt job: rotates data keys, not rows
4. Promote NEXT to current, remove the old
5. Deploy
```

Envelope encryption means rotation re-encrypts data keys rather than every row, so this is minutes rather than hours.

### JWT signing key

Publish the new public key alongside the old, sign with the new, wait for the access-token lifetime (15 minutes) plus a margin, then retire the old. No user-visible interruption.

### Blind index pepper

**Do not rotate casually.** Changing the pepper invalidates every blind index and requires recomputing them for all rows, during which email lookups fail. If it must rotate, take a maintenance window and recompute before switching.

---

## 4. Data subject requests

### Deletion stuck

```sql
SELECT id, user_id, modules_pending, sla_due_at
FROM gateway.deletion_ledger
WHERE completed_at IS NULL AND sla_due_at < now() + interval '5 days';
```

A module that never acknowledges is the usual cause. Check whether its consumer is running and whether the event reached its queue. If the module has genuinely completed but failed to acknowledge, publish the acknowledgement manually and record why in the ledger.

The 30-day SLA is a legal obligation. Five days out, it is an alert; two days out, it is an incident.

### Manual export

Support can trigger an export from admin. It never includes another user's data, and the archive link expires in 7 days.

---

## 5. Emergency controls

| Action | Effect |
|---|---|
| Set `looks_generation_enabled = false` | Generation returns the designed error state; everything else works |
| Set `spree_enabled = false` | Spree unavailable; templated message |
| Set `pinterest_sync_enabled = false` | Sync pauses; existing data untouched |
| Set `notify_enabled = false` | All sends suppressed; inbox still populated |
| Set `maintenance_mode = true` | All non-auth routes return 503 with the maintenance screen |

Flags are runtime values in Redis, readable without a deploy. That is the point — an incident is the wrong time to wait for CI.

---

## 6. Scaling

The gateway is stateless; add instances freely. Before scaling, check whether the bottleneck is actually the database connection pool, which it usually is. Each instance holds a pool, so more instances means more connections, and Postgres runs out long before the gateway does.

Redis is the second constraint — rate limiting, magic links, job progress, and caching all share it. Watch memory and eviction before adding instances that will only make it busier.

---

## 7. What not to do

- **Do not delete rows from `audit_log` or `quiz_responses`.** The service role cannot, and neither should a human with psql. Both are append-only for legal reasons.
- **Do not run migrations from the service role.** DDL belongs to `faue_migrator`.
- **Do not clear the outbox to "unblock" a deploy.** Those rows are state changes nobody has seen.
- **Do not disable `readyz` checks to keep an unhealthy instance in rotation.**
- **Do not log a payload to debug an issue.** Use the trace id; payloads contain PII and CI exists to prevent exactly this.
