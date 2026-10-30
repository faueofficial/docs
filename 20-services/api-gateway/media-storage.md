# Media storage: what is kept, where, and for how long

**Stage:** MVP · **Owner:** backend · **Audited:** 2026-10-14, from the code and the
local configuration. The deployed Railway variables were not available to read,
so section 4 lists what must be checked there. Findings fixed the same day are marked.

## 1. What is stored where

| What | Bytes live in | Record in the database | Backup copy |
|---|---|---|---|
| Uploaded images (vault, fabric, avatar, share): cleaned full size, 400 px preview, 200 px thumbnail | **Primary store**: Cloudinary in deployed environments, local disk in `local` | `gateway.assets` row: keys, size, pipeline flags | **Yes**, S3-compatible replica (Railway bucket here, R2 by default), copied by the `backup_replication` worker |
| Originals | **Nowhere.** Discarded once the derivative exists | `original_retained` is always false | n/a |
| Rejected uploads | **Nowhere.** Never written | Row with `status = rejected` and a reason | Never replicated |
| Pinterest pins | Copied through the pipeline as kind `pin` (up to 30 per import); the rest keep only Pinterest's CDN address | `gateway.imported_pins` (`asset_id`, `image_status`) | Same as uploads |
| Shared looks (TikTok, Instagram, Pinterest links) | **Not copied.** The platform's preview address only; a screenshot is an upload (row 1) | `gateway.shared_items` | n/a |
| Style DNA cards | **Not stored.** Drawn on request from a signed address and cached by the CDN | none | n/a |
| Data exports | Encrypted JSON in the database, 7 days | `gateway.data_exports` | Covered by database backups |
| Email banners and icons | Cloudinary, uploaded by hand, referenced by fixed URL in `notify/templates/registry.py` | none | none |
| Detector models | In the container image, `/opt/models/media` | none | n/a |

Keys are `assets/{user_id}/{asset_id}/{full|thumb|preview}.jpg`, the same on
every provider, so a user's images can be listed or deleted by prefix without the
database.

## 2. Providers

| Setting | Meaning | State |
|---|---|---|
| `STORAGE_PROVIDER=local` | Disk under `STORAGE_LOCAL_PATH` | Only when `ENVIRONMENT=local`; it refuses to start elsewhere |
| `STORAGE_PROVIDER=cloudinary` | Primary. `CLOUDINARY_URL`, **or** `CLOUDINARY_CLOUD_NAME` + `CLOUDINARY_API_KEY` + `CLOUDINARY_API_SECRET` | Implemented; a missing part is named at startup |
| `STORAGE_PROVIDER=r2` | Primary on R2: `R2_ACCOUNT_ID`, `STORAGE_BUCKET`, `STORAGE_ACCESS_KEY_ID`, `STORAGE_SECRET_ACCESS_KEY` | Implemented |
| `STORAGE_PROVIDER=railway` | Primary on Railway's bucket; accepts the injected `RAILWAY_*` names | Implemented |
| `STORAGE_PROVIDER=s3` | Any S3-compatible bucket: also `STORAGE_ENDPOINT_URL` | Implemented |
| `STORAGE_PUBLIC_BASE_URL` | Public base for delivery (custom domain or `r2.dev`) | Optional. Without it images are served by presigned links that expire after an hour |
| `STORAGE_MIRROR` (default on) | Also write each upload to the backup while the request is open | Implemented; a failure never fails the upload, the worker settles it |
| Backup: `BACKUP_PROVIDER` `r2` / `railway` / `minio` | Replica, deliberately a different provider from the primary | Implemented. The primary and the backup may not be the same bucket: startup refuses |

Primary and backup are separate on purpose: a backup that shares a failure domain
with the thing it backs up is not one.

## 3. Findings and their state

| # | Finding | State |
|---|---|---|
| 1 | Account deletion did not reach the backup replica | **Fixed.** The purge deletes from both; if either fails `storage` stays pending on the ledger |
| 2 | Deleting a vault item kept its image forever | **Fixed.** A deleted item is restorable for 30 days; then its images are removed from both stores and the row stays as a tombstone (name and category for wear history; notes and brand cleared) |
| 3 | Abandoned uploads were never swept | **Fixed.** `pending`/`processing` rows older than 24 hours are removed, with any bytes, from both stores |
| 4 | `STORAGE_PROVIDER=r2` advertised, not built | **Fixed** (section 2) |
| 5 | No inventory | **Fixed.** Console page "Uploads and storage": counts by status and kind, bytes, refusals by reason, safety verdicts, backup backlog, clean-up due |
| 6 | Email images share Cloudinary with user media (cloud `snapfeast`) | **Open.** Use a separate sub-account or folder-scoped key for the app |
| 7 | Imported pin images were never copied | **Fixed.** Copied through the pipeline (up to 30 per import), deleted with the pins from every store, and swept if orphaned |

## 4. To check on the deployment

These cannot be read from the repository:

- `STORAGE_PROVIDER=cloudinary` and `CLOUDINARY_URL` are set on **every**
  service that processes or deletes images: the API and the workers
  (`backup_replication`, `dsr_purge`). A worker without them either refuses to
  start or, in `local` mode, writes to a disk that disappears. This is the likely
  cause of the `backup_replication` crash loop seen earlier.
- The backup bucket variables are set on the worker, and the worker's backlog is
  zero.
- The Cloudinary plan's bandwidth and storage against the current asset count.
- Whether the backup bucket has versioning or object lock on: deletion has to be
  able to remove objects, and a retention lock would make a deletion request
  impossible to honour.

## 5. How an image's life ends

| Event | Primary | Backup | Row |
|---|---|---|---|
| Upload rejected | never written | never written | kept, with the reason |
| Vault item deleted | kept 30 days, then deleted | kept 30 days, then deleted | item and asset rows stay as a tombstone |
| Upload never finished | deleted after 24 hours | deleted after 24 hours | removed |
| Pinterest disconnected | copies deleted | copies deleted | pin rows removed |
| Account deleted | deleted at `purge_after` | deleted at `purge_after` | removed with the user |
| Deletion cancelled in the waiting period | untouched | untouched | untouched |
