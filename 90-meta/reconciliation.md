# Reconciliation — legacy architecture vs. current design

**Status:** OPEN — needs a decision · **Raised:** 2026-08-17
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

**What needs deciding:** `ase` or `archive` + `atelier`. If the split wins, `ADR 0001` is superseded and the schema, ports, repo names and roughly 40 documents change. Cheap now, expensive in three months.

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

**Recommendation:** keep **Vault** in the interface, because the design uses it and the app is what users read. The service name is a separate question — a service called `archive` can perfectly well own a table called `vault_items`.

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

| # | Question | Blocks |
|---|---|---|
| 1 | `ase`, or `archive` + `atelier`? | Repo names, schema names, ~40 documents. **Decide before slice 2** |
| 2 | If split: does the vector index live with storage or with generation? | The hot path of every generation |
| 3 | Storage: Cloudinary, or S3/R2 as the legacy doc assumes? | `media` module, presigned upload flow |
| 4 | Is "Occasion Routing" a distinct gateway module, or part of look generation? | Module layout |

---

## 6. How this got here

The `docs` remote was created independently and had three commits. The local documentation was written from the design specification and the Figma extraction, then initialised as a separate history.

The two were merged with `--allow-unrelated-histories`, preserving both. The legacy document is retained under `90-meta/legacy/` with a supersession banner rather than deleted — it is the only written record of the earlier thinking, and several of its ideas are better than what replaced them.

**Close this page** by making the decisions in §5, writing an ADR for each, and either updating the legacy document's banner to point at the resolution or deleting it once nothing references it.
