# ase — Schema

**Stage:** MVP · **Schema:** `ase` · **Models:** `faue-db/faue_db/ase/models.py`

`ase` holds vectors and styling state. It holds **no direct identifiers** — no email, no phone, no measurements. It knows `user_id` and derived constraints.

Vectors are derived data: rebuildable from source images, excluded from backups, and never in the restore critical path.

---

## Workspace scoping

Per [ADR 0021](../../80-adr/0021-workspace-tenancy-model.md), every user-owned table in this schema carries `workspace_id UUID NOT NULL` alongside `user_id`: `user_style_context`, all `*_embeddings`, `looks`, `look_jobs`, `look_impressions`, `fabric_analyses`, `spree_sessions`, `agent_memory`, and `agent_runs`.

`ase` does not own the `workspaces` table — it holds the identifier only, like every other cross-schema reference. At MVP the value is always the user's personal workspace and no query behaviour depends on it.

This is what makes a stylist's client context a parameter change rather than a redesign: the styling engine already scopes by workspace, it simply has one per user today.

## Style context

```sql
CREATE TABLE ase.user_style_context (
  user_id           UUID PRIMARY KEY,
  dna_vector        vector(768),
  aspiration_vector vector(768),
  behavior_vector   vector(768),
  constraints       JSONB NOT NULL DEFAULT '{}',   -- derived silhouette rules only
  wear_count        INTEGER NOT NULL DEFAULT 0,    -- drives blend weights
  model_id          TEXT NOT NULL,
  computed_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  stale_at          TIMESTAMPTZ
);
```

`constraints` holds abstract rules, never raw body data:

```json
{ "favor": ["defined_waist", "vertical_line"],
  "avoid": ["boxy_crop", "high_volume_hip"],
  "fit_preference": "regular",
  "sizes": { "tops": "M", "bottoms": "32" } }
```

The translation from body profile to constraints happens in `gateway` before it is sent. `ase` never sees a measurement, so a compromise of `ase` cannot expose one.

---

## Embeddings

One row per subject **per model**, so several embedding models coexist during migration.

```sql
CREATE TABLE ase.vault_embeddings (
  item_id    UUID NOT NULL,
  user_id    UUID NOT NULL,
  model_id   TEXT NOT NULL,
  dim        INTEGER NOT NULL,
  embedding  vector NOT NULL,
  image_hash TEXT NOT NULL,           -- skip re-embedding an unchanged image
  attributes JSONB,                   -- category, colours (LAB), fabric, formality
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (item_id, model_id)
);
CREATE INDEX idx_vault_emb_hnsw ON ase.vault_embeddings
  USING hnsw (embedding vector_cosine_ops) WITH (m = 16, ef_construction = 64)
  WHERE model_id = 'open_clip/ViT-L-14-336';
CREATE INDEX ON ase.vault_embeddings (user_id, model_id);

CREATE TABLE ase.aspiration_embeddings (
  pin_id     TEXT NOT NULL,
  user_id    UUID NOT NULL,
  board_id   TEXT NOT NULL,
  model_id   TEXT NOT NULL,
  embedding  vector NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (pin_id, model_id)
);

CREATE TABLE ase.style_embeddings (
  style_id  UUID NOT NULL,
  model_id  TEXT NOT NULL,
  embedding vector NOT NULL,
  PRIMARY KEY (style_id, model_id)
);

CREATE TABLE ase.fabric_embeddings (
  asset_id   UUID NOT NULL,
  user_id    UUID NOT NULL,
  model_id   TEXT NOT NULL,
  embedding  vector NOT NULL,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (asset_id, model_id)
);

CREATE TABLE ase.product_embeddings (      -- M1-2
  product_id UUID NOT NULL,
  model_id   TEXT NOT NULL,
  embedding  vector NOT NULL,
  image_hash TEXT NOT NULL,
  attributes JSONB,
  PRIMARY KEY (product_id, model_id)
);
```

The partial index per `model_id` is what keeps a migration from bloating one index with vectors nobody queries. Dimension is a column rather than a constraint because different providers differ — 768 for open-CLIP ViT-L/14, 512 for ViT-B/32, 1024 for Voyage, 3072 for Gemini-class.

> **pgvector cannot index a dimensionless column.** `CREATE INDEX ... USING hnsw (embedding ...)` on a bare `vector` column fails with `column does not have dimensions`. The index therefore **casts in an expression** and is partial on `model_id`:
>
> ```sql
> CREATE INDEX idx_vault_emb_hnsw_cliplarge ON ase.vault_embeddings
>   USING hnsw ((embedding::vector(768)) vector_cosine_ops)
>   WITH (m = 16, ef_construction = 64)
>   WHERE model_id = 'open_clip/ViT-L-14-336';
> ```
>
> **Queries must repeat the same cast to hit the index:**
>
> ```sql
> SELECT item_id FROM ase.vault_embeddings
> WHERE model_id = 'open_clip/ViT-L-14-336'
> ORDER BY embedding::vector(768) <=> $1::vector(768)
> LIMIT 40;
> ```
>
> A query without the cast silently falls back to a sequential scan — correct results, unusable latency. This was found by running the migration, not by reading the documentation.

---

## Looks

```sql
CREATE TABLE ase.look_jobs (
  id           UUID PRIMARY KEY,
  user_id      UUID NOT NULL,
  source       TEXT NOT NULL,       -- vault | fabric | prompt | agent
  request      JSONB NOT NULL,
  status       TEXT NOT NULL,       -- queued|analyzing|assembling|rendering|done|failed
  progress     SMALLINT NOT NULL DEFAULT 0,
  reason_code  TEXT,
  stage_failed TEXT,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  finished_at  TIMESTAMPTZ
);
CREATE INDEX ON ase.look_jobs (user_id, created_at DESC);
CREATE INDEX ON ase.look_jobs (status) WHERE status NOT IN ('done','failed');

CREATE TABLE ase.looks (
  id              UUID PRIMARY KEY,
  job_id          UUID NOT NULL REFERENCES ase.look_jobs(id) ON DELETE CASCADE,
  user_id         UUID NOT NULL,
  title           TEXT NOT NULL,
  description     TEXT,
  why_this_works  TEXT,
  items           JSONB NOT NULL,   -- [{name, role, vault_item_id?, image_url?, note?}]
  occasion        TEXT,
  image_url       TEXT,
  renderer        TEXT NOT NULL,    -- generative | composite | hybrid
  score           REAL,
  strategy_version TEXT NOT NULL,
  model_id        TEXT,
  prompt_version  TEXT,
  generated_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON ase.looks (user_id, generated_at DESC);

CREATE TABLE ase.look_impressions (
  id                 UUID PRIMARY KEY,
  user_id            UUID NOT NULL,
  look_id            UUID NOT NULL,
  position           SMALLINT NOT NULL,
  candidate_set_hash TEXT NOT NULL,
  ranker_version     TEXT NOT NULL,
  shown_at           TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`look_impressions` records served position and candidate-set hash on every view. Logging this is cheap now and **impossible to reconstruct later**; without it, any future ranking model trains on position-biased data and learns that whatever was shown first is best.

`strategy_version` and `prompt_version` on every look mean a quality complaint can be traced to the exact pipeline that produced it.

---

## Fabric and style library

```sql
CREATE TABLE ase.fabric_analyses (
  id                 UUID PRIMARY KEY,
  user_id            UUID NOT NULL,
  asset_id           UUID NOT NULL,
  detected_type      TEXT NOT NULL,
  confidence         REAL NOT NULL,
  user_corrected_type TEXT,          -- correction rate is a tracked quality metric
  attributes         JSONB,
  suggested_style_ids UUID[],
  reasoning_by_style JSONB,
  model_id           TEXT,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ase.style_library (
  id                 UUID PRIMARY KEY,
  name               TEXT NOT NULL,
  gender             TEXT,
  silhouette         TEXT NOT NULL,
  formality          TEXT NOT NULL,   -- casual|smart_casual|formal|ceremonial
  fabric_suitability JSONB NOT NULL,  -- {"ankara":"ideal","aso_oke":"avoid",...}
  occasion_tags      TEXT[] NOT NULL,
  body_notes         JSONB,
  description        TEXT,
  status             TEXT NOT NULL DEFAULT 'draft',   -- draft|active|retired
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ase.style_reference_images (
  id                UUID PRIMARY KEY,
  style_id          UUID NOT NULL REFERENCES ase.style_library(id) ON DELETE CASCADE,
  image_url         TEXT NOT NULL,
  fabric_type       TEXT,
  source            TEXT NOT NULL,    -- licensed | generated | commissioned
  license_type      TEXT,
  license_document  TEXT,
  attribution       TEXT,
  model_release     BOOLEAN,
  generated         BOOLEAN NOT NULL DEFAULT FALSE,
  stylist_approved_by TEXT,
  expires_at        TIMESTAMPTZ,
  created_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ase.accessory_pairings (
  id         UUID PRIMARY KEY,
  style_id   UUID NOT NULL REFERENCES ase.style_library(id) ON DELETE CASCADE,
  name       TEXT NOT NULL,
  image_url  TEXT,
  occasion   TEXT,
  rank       SMALLINT NOT NULL DEFAULT 0,
  rationale  TEXT
);

CREATE TABLE ase.compatibility_rules (
  id        UUID PRIMARY KEY,
  rule_type TEXT NOT NULL,      -- color | category | occasion | silhouette
  predicate JSONB NOT NULL,
  weight    REAL NOT NULL DEFAULT 1.0,
  version   TEXT NOT NULL,
  active    BOOLEAN NOT NULL DEFAULT TRUE
);
```

The provenance columns on `style_reference_images` exist because an unlicensed image discovered after launch means pulling it from a live product, and possibly from share cards already in circulation. Every image must be able to answer "where did this come from and may we use it?" See [ADR 0020](../../80-adr/0020-style-library-licensed-not-scraped.md).

`generated = true` rows additionally require `stylist_approved_by` before `status` can be `active` — generated native wear is frequently wrong in the details.

---

## spree (module — extractable)

```sql
CREATE TABLE ase.spree_sessions (
  id            UUID PRIMARY KEY,
  user_id       UUID NOT NULL,
  started_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  ended_at      TIMESTAMPTZ,
  message_count INTEGER NOT NULL DEFAULT 0,
  token_spend   INTEGER NOT NULL DEFAULT 0,
  flagged       BOOLEAN NOT NULL DEFAULT FALSE,
  review_status TEXT                        -- pending | cleared | actioned
);

CREATE TABLE ase.spree_messages (
  id               UUID PRIMARY KEY,
  session_id       UUID NOT NULL REFERENCES ase.spree_sessions(id) ON DELETE CASCADE,
  role             TEXT NOT NULL,
  content_redacted TEXT NOT NULL,     -- PII-redacted before storage
  asset_ids        UUID[],
  tool_calls       JSONB,
  model_id         TEXT,
  prompt_version   TEXT,
  tokens_in        INTEGER,
  tokens_out       INTEGER,
  latency_ms       INTEGER,
  guardrail_verdict JSONB,
  created_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  expires_at       TIMESTAMPTZ NOT NULL   -- TTL-bounded, consent-tied
);
CREATE INDEX ON ase.spree_messages (expires_at);
```

Message content is stored **already redacted**. The redaction happens before persistence, not before display, so a database dump contains no PII even if the application layer is bypassed.

---

## agent and context

```sql
CREATE TABLE ase.agent_memory (
  user_id    UUID NOT NULL,
  tier       TEXT NOT NULL,       -- profile | semantic | episodic
  key        TEXT NOT NULL,
  value      JSONB NOT NULL,
  confidence REAL NOT NULL DEFAULT 1.0,
  decayed_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (user_id, tier, key)
);

CREATE TABLE ase.agent_runs (
  id       UUID PRIMARY KEY,
  user_id  UUID NOT NULL,
  trigger  TEXT NOT NULL,          -- daily | weather | event | proactive | on_demand
  level    SMALLINT NOT NULL,
  context  JSONB,
  look_id  UUID,
  rationale TEXT,
  outcome  TEXT,                   -- accepted | dismissed | regenerate | no_response
  ran_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE ase.weather_cache (
  geohash5    TEXT NOT NULL,
  hour_bucket TIMESTAMPTZ NOT NULL,
  payload     JSONB NOT NULL,
  fetched_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (geohash5, hour_bucket)
);
```

`agent_memory` is deliberately readable and editable — the agent must be able to answer "why did you suggest this?" from stored facts rather than a re-prompted guess, and a user must be able to correct something it learned wrongly.

---

## Model operations

```sql
CREATE TABLE ase.model_calls (
  id             UUID PRIMARY KEY,
  user_id        UUID,
  task           TEXT NOT NULL,
  tier           TEXT NOT NULL,
  model_id       TEXT NOT NULL,
  prompt_version TEXT,
  tokens_in      INTEGER,
  tokens_out     INTEGER,
  cost_usd       NUMERIC(10,6),
  latency_ms     INTEGER,
  cache_hit      BOOLEAN NOT NULL DEFAULT FALSE,
  fallback_depth SMALLINT NOT NULL DEFAULT 0,
  guardrail_verdict TEXT,
  trace_id       TEXT,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON ase.model_calls (created_at DESC);
CREATE INDEX ON ase.model_calls (task, created_at DESC);

CREATE TABLE ase.budgets (
  scope      TEXT NOT NULL,        -- user_daily | task_monthly | global
  scope_key  TEXT NOT NULL,
  period     DATE NOT NULL,
  spent_usd  NUMERIC(10,6) NOT NULL DEFAULT 0,
  limit_usd  NUMERIC(10,6) NOT NULL,
  PRIMARY KEY (scope, scope_key, period)
);

CREATE TABLE ase.outbox ( LIKE gateway.outbox INCLUDING ALL );
```

`model_calls` is the table behind the AI health dashboard and behind cost per active user. Retention 90 days; aggregates kept longer.

---

## Roles

```sql
CREATE ROLE faue_ase LOGIN;
GRANT USAGE ON SCHEMA ase TO faue_ase;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA ase TO faue_ase;
REVOKE ALL ON SCHEMA gateway, catalog, media FROM faue_ase;
```

`ase` cannot read `gateway`. If it needs user data it asks over HTTP and receives only what the interface exposes — which for body data is derived constraints, never measurements.

---

## Retention

| Table | Retention |
|---|---|
| `spree_messages` | 90 days, consent-tied |
| `spree_sessions` | 90 days, or until review closed |
| `model_calls` | 90 days |
| `agent_runs` | 12 months |
| `agent_memory` episodic | 90 days rolling |
| `look_jobs` | 30 days after terminal state |
| `looks` | Life of account, unless unsaved and older than 90 days |
| `weather_cache` | 48 hours |
| Embeddings | Life of the source object |
