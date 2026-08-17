# Runbook — Embedding Coverage Below Threshold

**Severity:** SEV3 · **Trigger:** Coverage below 98%

## Check

```sql
SELECT count(*) FILTER (WHERE e.item_id IS NULL) AS unembedded, count(*) AS total
FROM gateway.vault_items v
LEFT JOIN ase.vault_embeddings e
  ON e.item_id = v.id AND e.model_id = current_setting('faue.embed_model')
WHERE v.deleted_at IS NULL;
```

## Causes

| Cause | Action |
|---|---|
| `ase.embedding` consumer down | Restart; events redeliver |
| Messages in the DLQ | See [dlq-nonempty](dlq-nonempty.md) |
| Image fetch failing | Check CDN availability and the asset pipeline |
| Migration in progress | Expected — coverage for the new model climbs over hours |

## Why it matters

Unembedded items are **invisible to generation**. Users experience this as "it ignored the shirt I just added", which reads as the product being broken rather than delayed.

## Act

```bash
python -m app.workers.backfill_embeddings --subject vault --missing-only
```

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
