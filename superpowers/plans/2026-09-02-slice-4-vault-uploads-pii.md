# Slice 4 — Vault, uploads, and the image PII pipeline

**Created:** 2026-09-02 · **Branch:** `slice-0-1-infra-identity`
**Spec:** [`../../10-architecture/pii-handling.md`](../../10-architecture/pii-handling.md)

---

## Why this is the hard slice

Every earlier slice moved text. This one moves photographs of people's clothes,
taken in their bedrooms, on their phones. The metadata alone discloses a home
address, and the frame frequently contains a face the user did not think about.

The pipeline is therefore not a feature attached to uploads — it *is* uploads.
An image that reaches disk unprocessed cannot be un-disclosed later.

---

## Decision: the models run in-process

`pii-handling.md` says face redaction happens in-process because sending an
unredacted face to a vendor in order to detect the face defeats the purpose.
Safety classification runs *first* in the pipeline, so a hosted classifier would
see the unredacted image too — the same objection, one step earlier.

| Stage | Implementation | Resident |
|---|---|---|
| Safety | `open_clip` zero-shot against a fixed label set | ~350 MB |
| Faces | MediaPipe BlazeFace | ~30 MB |
| OCR | Tesseract via `pytesseract` | ~50 MB |

Roughly 300–500 MB resident, which is real money on Railway and cheaper than the
alternative: no image leaves our infrastructure, which is what the privacy
documents actually promise users.

Behind one `Detector` protocol, so a swap is configuration — the same shape as
pluggable embeddings (ADR 0007) and rendering (ADR 0009).

---

## Order of work

Each step is useful alone and testable without the next.

### 1. `assets` table, in the gateway schema

`media` is an M1-2 extraction, so its responsibilities live as a bounded module
inside the gateway until then — the same arrangement as `notify`. Columns follow
`pii-handling.md` §Auditability exactly: `exif_stripped`, `faces_redacted`,
`ocr_redacted`, `safety_verdict`, `original_retained`, `retention_until`.

Those flags are the point. They make the compliance question a query rather than
an argument:

```sql
SELECT count(*) FROM gateway.assets
WHERE status = 'ready' AND (NOT exif_stripped OR NOT faces_redacted);  -- must be zero
```

### 2. `StorageProvider`

Local filesystem, Cloudinary, R2 behind one interface. Local is the default so
tests and development never touch a paid service or the network.

### 3. The pipeline

```
classify → strip EXIF → redact faces → redact text → derive variants → discard original
```

Ordered deliberately: classification first so nothing unacceptable is ever
written; the original discarded last because every other step reads from it.

Variants (200px thumb, 400px preview, full) are emitted in the same pass — the
bitmap is already decoded, and a vault grid on metered Nigerian mobile data must
not download full resolution to draw thumbnails.

### 4. Upload signing

Short-lived credentials for a direct client-to-CDN upload; the server never
proxies bytes. An asset is unusable by any other endpoint until `status =
'ready'`.

### 5. Vault CRUD

Create, list, filter, update, soft-delete, wear log. Soft delete because
`wear_log` references items historically and a wear record pointing at nothing
is worse than a tombstone.

---

## What must be true when this is done

- No code path writes an unprocessed image to permanent storage.
- The compliance query above returns zero, and a test proves it can fail.
- A rejected image is not persisted at all — not quarantined, not kept "for
  review".
- Client-supplied processing claims are ignored. The Flutter app may blur for a
  nicer preview; the server repeats every step regardless, because a modified
  client simply skips its own.

---

## Out of scope

- Share-card and tailor-share rendering — `media` proper, M1-2.
- Embeddings for vault items — that is `ase`, slice 5.
- Original retention. `original_retained` exists in the schema and stays false;
  keeping originals needs an explicit consent purpose that does not exist yet.
