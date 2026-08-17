# Reconciliation — legacy architecture vs. current design

**Status:** CLOSED · **Raised:** 2026-08-17 · **Naming resolved:** 2026-08-17 ([ADR 0022](../80-adr/0022-canonical-domain-and-service-naming.md))
**Sources:** [`legacy/01_SYSTEM_ARCHITECTURE.md`](legacy/01_SYSTEM_ARCHITECTURE.md) (from the `docs` remote) vs. [`../10-architecture/hld.md`](../10-architecture/hld.md)

The `docs` remote contained an earlier architecture document written independently of the platform design produced from the Figma file and the design session. Both are considered work. This page lists where they disagree, what was adopted, and what still needs a call.

**Nothing here is resolved unilaterally.** The naming decision in particular touches roughly 140 files and every schema name, so it is a decision to make once, deliberately.

---

## 1. Service topology and naming — **the blocking one**

| | Legacy | Current |
|---|---|---|
| Services | `api-gateway` · `archive` · `atelier` | `api-gateway` · `ase` |
| Ports | 8000 / 8001 / 8002 | 8000 / 8001 (catalog 8002, media 8003) |
| Schemas | `gateway` · `archive` · `atelier` | `gateway` · `ase` (+ `catalog`, `media`) |
| Split rationale | Storage+vectors vs. AI styling | I/O-bound+PII vs. compute-bound+no-PII |

The legacy split is defensible: `archive` owns storage and embeddings, `atelier` owns generation and VTO. The current split ([ADR 0001](../80-adr/0001-two-services-gateway-and-ase.md)) puts both in `ase` on the grounds that they share the vector index and the model plane, and that two people should not run three deployments before launch.

**Argument for merging them (current):** the semantic matcher in `atelier` queries the vector index in `archive` on the hot path of every generation. A service boundary there means a network hop inside the loop the product is built around.

**Argument for splitting them (legacy):** storage and vectorisation are I/O and batch shaped; generation is compute and latency shaped. They scale differently.

**RESOLVED — `ase` retained.** See [ADR 0022](../80-adr/0022-canonical-domain-and-service-naming.md).

The deciding argument: the semantic matcher sits on the **hot path of every generation**. Splitting `archive` from `atelier` puts a network hop inside the loop the product is built around. The pressure the split anticipates is real, and the seams already exist — `spree` is documented as extractable, and `catalog` and `media` are designed as separate services for exactly the batch and CPU-spiky work the legacy document was separating out.

---

## 2. Vault vs. Archive — naming, and the design disagrees with both

The legacy document states *"Archive — the user's intelligent digital wardrobe. Replaces the legacy 'Vault'."*

But the **Figma design says "My Vault"** across seven screens (`704:2252`, `504:2972`, `709:1540`, `711:1596`, `717:3135`, `728:3608`, and the bottom navigation), and the current documentation follows the design.

Three-way conflict, and the user-facing name is the one that matters most:

| Layer | Legacy | Design (Figma) | Current docs |
|---|---|---|---|
| User-facing | Archive | **My Vault** | Vault |
| Service | `archive` | — | `ase` |
| Table | `wardrobe_items` | — | `vault_items` |

**RESOLVED — Vault.** The design uses it across seven screens and the app is what users read. The table stays `vault_items`.

---

## 3. Adopted from the legacy document

These are better than what the current documents had, and are being folded in:

| Idea | Why it is better | Where it lands |
|---|---|---|
| **Ephemeral VTO images, purged after 24h unless saved** | The strongest privacy design in either document. VTO produces full-body imagery; not retaining it by default is exactly right | `60-ai/rendering.md`, `10-architecture/pii-handling.md` |
| **`is_ephemeral` flag on generated assets** | Makes the purge queryable rather than implicit | `media.assets` |
| **Non-retention flag enforced on the VTO provider** | Contractual control made explicit per request | `10-architecture/privacy.md` |
| **Named VTO provider candidates (Fashn.ai, Replicate)** | Concrete where the current doc says "TBD at selection" | `60-ai/rendering.md` |
| **>85% cosine similarity to flag an owned item** | A concrete threshold beats "match against the vault" | `20-services/ase/lld.md` |
| **S3/R2 presigned URLs** | Same shape as the current "signed direct-to-CDN", but names the storage | `70-ops/environments.md` |
| **"Occasion Routing" as a named gateway concern** | Useful framing for the cultural-event triggers | `10-architecture/hld.md` |

---

## 4. Conflicts where the current design should win, with reasons

| Point | Legacy | Current | Why |
|---|---|---|---|
| **Instagram sync** | `archive` ingests IG saves | Removed | The Graph API **cannot** return a user's saved posts, and Basic Display is deprecated. The feature is undeliverable as described ([ADR 0019](../80-adr/0019-remove-instagram-integration.md)) |
| **`vector(512)`** | Fixed 512 dimensions | Dimensionless + cast index | 512 is CLIP ViT-B/32. The current default is ViT-L/14 at 768, and a fixed dimension makes an embedding-model migration a table rewrite ([ADR 0007](../80-adr/0007-pluggable-embeddings-self-hosted-default.md)) |
| **VTO in V1** | Core service concern | `M1-2` | VTO renders a real person's body — it needs its own consent purpose, guardrail exception, and eval set. It does not test the MVP hypothesis |
| **Python 3.11+** | 3.11 | 3.12 | Already pinned across four repositories |
| **Pinterest + IG in `archive`** | Social sync lives with storage | Integrations live in `gateway` | OAuth tokens are PII and belong in the service that holds PII. `ase` deliberately holds no direct identifiers |

---

## 5. Genuinely open

| # | Question | Status |
|---|---|---|
| ~~1~~ | ~~`ase` or `archive` + `atelier`?~~ | **Closed** — `ase` ([ADR 0022](../80-adr/0022-canonical-domain-and-service-naming.md)) |
| ~~2~~ | ~~If split: where does the vector index live?~~ | **Moot** — no split |
| ~~3~~ | ~~Storage: Cloudinary, R2, or Railway?~~ | **Closed** — Cloudinary primary, R2 backup, Railway for local/staging |
| ~~4~~ | ~~"Occasion Routing" — gateway module or part of generation?~~ | **Closed** — neither. `ase.context.occasions`, a context signal beside weather |

### 3. Storage — resolved

**Cloudinary primary, Cloudflare R2 as the backup replica, Railway object storage for local and staging.** All three behind one `StorageProvider` interface.

| Tier | Role | Why |
|---|---|---|
| Cloudinary | Primary — storage, CDN, transforms | Free tier covers the first few hundred users; on-the-fly variants remove a pipeline step; CDN is the requirement metered mobile data imposes |
| Cloudflare R2 | Backup replica | Different provider from the primary, matching the rule already applied to database backups. Zero egress makes restore cheap |
| Railway object storage | Local and staging | Already wired. Nobody's phone downloads from it, so no CDN is needed |

**The watch item is egress, not storage.** Cloudinary's free tier is 25 GB of storage and 25 GB of bandwidth a month. Storage will not be the binding constraint — bandwidth will, because a vault grid is many small image requests on metered connections. Track bandwidth as a first-class metric, and treat approaching the cap as the trigger to move primary to R2, which is a copy job rather than a rewrite because uploads already go through the interface.

Mitigation regardless of provider: request sized variants, never full resolution for a thumbnail; never prefetch generated renders on a metered connection.

---

## 6. How this got here

The `docs` remote was created independently and had three commits. The local documentation was written from the design specification and the Figma extraction, then initialised as a separate history.

The two were merged with `--allow-unrelated-histories`, preserving both. The legacy document is retained under `90-meta/legacy/` with a supersession banner rather than deleted — it is the only written record of the earlier thinking, and several of its ideas are better than what replaced them.

### 4. Occasion routing — resolved

**Neither a gateway module nor part of generation.** It became `ase.context.occasions`, a context signal with the same shape as weather.

The legacy name bundled three concerns:

| Concern | Where it actually lives | Status |
|---|---|---|
| Occasion as a request parameter | An enum on `POST /looks/generate` | Already existed |
| Occasion as a styling constraint | `style_library.occasion_tags`, filtered in the legal pool | Already existed |
| **Occasion as a temporal, cultural signal** | **`ase.context.occasions`** | **This was the real gap** |

The third was scattered across `seasonality.py`, the agent's L2 triggers, and the retention worker's cultural campaigns — three consumers each implying their own copy. Now one source, three readers.

"Routing" was dropped from the name because it describes request dispatch, which this is not.

---

## 7. Closed

Every item in §5 is resolved. The legacy document remains under `legacy/` as the only record of the earlier thinking; it can be deleted once nothing references it, though its ephemeral-VTO design is worth keeping visible until that lands.
