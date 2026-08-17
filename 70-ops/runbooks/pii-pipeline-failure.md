# Runbook — PII Pipeline Failure

**Severity:** SEV1 · **Trigger:** Any asset stored unredacted

**Treat as a potential data breach. The 72-hour clock starts at awareness.**

## Check

```sql
SELECT id, kind, created_at, exif_stripped, faces_redacted, ocr_redacted
FROM media.assets
WHERE NOT exif_stripped OR NOT faces_redacted OR NOT ocr_redacted
ORDER BY created_at DESC;
```

This query must always return zero rows.

## Act

1. **Stop uploads immediately** — disable `uploads_enabled`.
2. Determine scope: how many assets, over what period, whether any were shared or sent to a model provider.
3. Quarantine the affected assets — remove from CDN.
4. Fix the pipeline, verify against the `pii_images` golden set.
5. Reprocess quarantined assets.
6. Assess notification obligation. Shared assets or assets sent to a provider are a higher risk category.

## Cause

Usually a code path that bypassed the pipeline — a new upload kind, or a direct write. The per-asset flags exist precisely so this is detectable rather than silent; the follow-up must add the missing path to the pipeline and a test that fails without it.

---

*Escalation and post-incident process: [incident-response.md](../incident-response.md)*
