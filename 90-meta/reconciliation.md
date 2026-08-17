# Reconciliation — legacy architecture vs. current design

**Status:** PARTIALLY CLOSED · **Raised:** 2026-08-17 · **Naming resolved:** 2026-08-17 ([ADR 0022](../80-adr/0022-canonical-domain-and-service-naming.md))
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
| 3 | Storage: Cloudinary, R2, or object storage on Railway? | **OPEN** — see below |
| 4 | Is "Occasion Routing" a distinct gateway module, or part of look generation? | OPEN — low stakes, decide when building |

### 3. Storage — still open

The legacy document assumes S3/R2 presigned URLs; the current documents say "Cloudinary or S3-compatible". The decision matters more than it looks, because FAUE is image-heavy and its users are on **metered Nigerian mobile data**, which makes egress cost and CDN proximity product concerns rather than infrastructure ones.

Constraints any answer has to satisfy:

- **A CDN close to users.** Serving images from a single origin region is slow and costs users money.
- **Durability.** Vectors are derived and rebuildable; a user's photographs are not.
- **Sized variants.** A vault grid must not download full-resolution renders. Either the store transforms on the fly, or the pipeline pre-generates variants.
- **Egress cost.** The dominant variable cost of an image-heavy product.

---

## 6. How this got here

The `docs` remote was created independently and had three commits. The local documentation was written from the design specification and the Figma extraction, then initialised as a separate history.

The two were merged with `--allow-unrelated-histories`, preserving both. The legacy document is retained under `90-meta/legacy/` with a supersession banner rather than deleted — it is the only written record of the earlier thinking, and several of its ideas are better than what replaced them.

**Close this page** by making the decisions in §5, writing an ADR for each, and either updating the legacy document's banner to point at the resolution or deleting it once nothing references it.
