# Runbook — Dead-Letter Queue Not Empty

**Severity:** SEV2 · **Trigger:** Any DLQ non-empty for 10 minutes

## Check

```bash
rabbitmqctl list_queues name messages | grep dlq
```

Read one message, take its `trace_id`, find the original failure in logs.

## Causes

| Cause | Action |
|---|---|
| Handler bug on a specific payload shape | Fix the handler, replay |
| Downstream dependency was down | Replay once it is back |
| Poison message — genuinely unprocessable | Record it, then discard deliberately |
| Schema change without a consumer update | Deploy the consumer, replay |

## Act

```bash
# after fixing
python -m app.events.replay_dlq --queue <queue>.dlq --limit 100
```

## Do not

**Never delete a DLQ message without recording what it was.** Each represents a state change that some consumer never saw — a notification never sent, an embedding never created, a deletion never acknowledged.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
