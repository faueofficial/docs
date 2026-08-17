# api-gateway — Schema

**Stage:** MVP · **Schema:** `gateway` · **Models:** `faue-db/faue_db/gateway/models.py`

All identifiers are UUIDv7. All timestamps are `TIMESTAMPTZ` in UTC. Columns suffixed `_enc` are envelope-encrypted; `_bidx` columns are blind indexes (HMAC with a pepper) that make equality lookups on encrypted values an index scan.

**No foreign keys cross schemas.** References to `ase` or `media` objects are plain UUID columns.

---

## Workspaces

Reserved by [ADR 0021](../../80-adr/0021-workspace-tenancy-model.md). Present from the first migration, single-tenant in behaviour at MVP.

```sql
CREATE TABLE gateway.workspaces (
  id            UUID PRIMARY KEY,
  kind          TEXT NOT NULL DEFAULT 'personal',  -- personal | stylist | tailor | production
  name          TEXT,
  owner_user_id UUID NOT NULL,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gateway.workspace_members (
  workspace_id UUID NOT NULL REFERENCES gateway.workspaces(id) ON DELETE CASCADE,
  user_id      UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  role         TEXT NOT NULL DEFAULT 'owner',      -- owner | member | client
  joined_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  PRIMARY KEY (workspace_id, user_id)
);
```

**Every user-owned table below carries `workspace_id UUID NOT NULL`**, indexed alongside `user_id`. That is: `profiles`, `body_profile`, `style_preferences`, `quiz_responses`, `vault_items`, `wear_log`, `saved_looks`, `feedback_signals`, `action_events`, `integration_accounts`, and the `notify_*` tables.

A personal workspace is created in the same transaction as the user, so the column is never null and never a lie. At MVP every workspace has exactly one member and the API does not expose the concept.

Repository access goes through a scoping helper rather than a raw `user_id` filter, so activating multi-tenancy later is a change to one function rather than to every query.

## Identity

```sql
CREATE TABLE gateway.users (
  id            UUID PRIMARY KEY,
  status        TEXT NOT NULL DEFAULT 'active',   -- active | suspended | deleted
  age_verified  BOOLEAN NOT NULL DEFAULT FALSE,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at    TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at    TIMESTAMPTZ
);

CREATE TABLE gateway.auth_identities (
  id              UUID PRIMARY KEY,
  user_id         UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  provider        TEXT NOT NULL,          -- magic_link | google | apple | phone_otp
  provider_uid    TEXT NOT NULL,
  email_enc       BYTEA,
  email_bidx      TEXT,                   -- HMAC; the login lookup key
  email_verified  BOOLEAN NOT NULL DEFAULT FALSE,
  phone_enc       BYTEA,
  phone_bidx      TEXT,
  display_name    TEXT,                   -- Apple sends this once, on first auth only
  linked_at       TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_used_at    TIMESTAMPTZ,
  UNIQUE (provider, provider_uid)
);
CREATE INDEX ON gateway.auth_identities (email_bidx) WHERE email_verified;
CREATE INDEX ON gateway.auth_identities (user_id);

CREATE TABLE gateway.refresh_tokens (
  id            UUID PRIMARY KEY,
  user_id       UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  token_hash    TEXT NOT NULL UNIQUE,
  family_id     UUID NOT NULL,
  rotated_from  UUID,
  user_agent    TEXT,
  expires_at    TIMESTAMPTZ NOT NULL,
  revoked_at    TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.refresh_tokens (family_id);
CREATE INDEX ON gateway.refresh_tokens (user_id) WHERE revoked_at IS NULL;
```

Magic-link tokens live in **Redis only**, never Postgres — `magic_link:{sha256}` with a 600-second TTL, holding the identifier, session challenge, and attempt count. Consumption is a Lua script that reads, validates, and deletes atomically, so two concurrent attempts cannot both succeed.

The blind index is only populated for verified emails, because account linking must never match on an unverified address.

---

## Profile

```sql
CREATE TABLE gateway.profiles (
  user_id             UUID PRIMARY KEY REFERENCES gateway.users(id) ON DELETE CASCADE,
  username            CITEXT UNIQUE,
  display_name        TEXT,
  gender_presentation TEXT,      -- feminine | masculine | fluid | prefer_not_to_say
  city                TEXT,
  geohash5            TEXT,      -- ~5km precision; never raw coordinates
  locale              TEXT NOT NULL DEFAULT 'en-NG',
  currency            TEXT NOT NULL DEFAULT 'NGN',
  avatar_asset_id     UUID,
  created_at          TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at          TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gateway.body_profile (
  user_id           UUID PRIMARY KEY REFERENCES gateway.users(id) ON DELETE CASCADE,
  body_shape        TEXT,
  height_cm_enc     BYTEA,
  measurements_enc  BYTEA,       -- optional expansion; absent for most users
  fit_preference    TEXT,        -- fitted | regular | relaxed
  sizes_by_category JSONB,
  updated_at        TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

`body_profile` is the most sensitive table in the system. Every field optional, encrypted where numeric, never present in an event payload, never sent raw to a model — `ase` receives derived silhouette constraints only. Retention: until the user deletes it.

---

## Consent and privacy

```sql
CREATE TABLE gateway.consents (
  user_id        UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  purpose        TEXT NOT NULL,
  granted        BOOLEAN NOT NULL DEFAULT FALSE,   -- denied by default, always
  policy_version TEXT,
  granted_at     TIMESTAMPTZ,
  revoked_at     TIMESTAMPTZ,
  source         TEXT,          -- onboarding | settings | inline_prompt | admin
  PRIMARY KEY (user_id, purpose)
);

CREATE TABLE gateway.deletion_ledger (
  id                  UUID PRIMARY KEY,
  user_id             UUID NOT NULL,
  requested_at        TIMESTAMPTZ NOT NULL DEFAULT now(),
  sla_due_at          TIMESTAMPTZ NOT NULL,
  modules_pending     TEXT[] NOT NULL,
  modules_done        TEXT[] NOT NULL DEFAULT '{}',
  third_parties_done  TEXT[] NOT NULL DEFAULT '{}',
  completed_at        TIMESTAMPTZ
);
CREATE INDEX ON gateway.deletion_ledger (completed_at) WHERE completed_at IS NULL;
```

`deletion_ledger.user_id` deliberately has no foreign key — the user row is deleted while the ledger must survive as the compliance record.

---

## Style DNA

```sql
CREATE TABLE gateway.style_preferences (
  user_id             UUID PRIMARY KEY REFERENCES gateway.users(id) ON DELETE CASCADE,
  dna_scores          JSONB,        -- raw scores, not sharpened
  dna_dominant        VARCHAR(2),
  dna_alter_ego       VARCHAR(2),
  dna_wildcard        VARCHAR(2),
  quiz_completed      BOOLEAN NOT NULL DEFAULT FALSE,
  quiz_version        TEXT,
  completed_at        TIMESTAMPTZ,
  retake_available_at TIMESTAMPTZ
);

CREATE TABLE gateway.quiz_responses (      -- append-only
  id           UUID PRIMARY KEY,
  user_id      UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  quiz_version TEXT NOT NULL,
  answers      JSONB NOT NULL,
  submitted_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.quiz_responses (user_id, submitted_at DESC);
```

Raw scores are stored, not percentages — sharpening is presentation and `GAMMA` may change without invalidating history.

---

## Vault

```sql
CREATE TABLE gateway.vault_items (
  id           UUID PRIMARY KEY,
  user_id      UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  asset_id     UUID NOT NULL,
  name         TEXT NOT NULL,
  category     TEXT NOT NULL,      -- tops | bottoms | native | shoes | accessories
  subcategory  TEXT,
  colors       TEXT[],
  fabric       TEXT,
  brand        TEXT,
  notes        TEXT,
  wear_count   INTEGER NOT NULL DEFAULT 0,
  last_worn_at TIMESTAMPTZ,
  created_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  updated_at   TIMESTAMPTZ NOT NULL DEFAULT now(),
  deleted_at   TIMESTAMPTZ
);
CREATE INDEX ON gateway.vault_items (user_id, category) WHERE deleted_at IS NULL;
CREATE INDEX ON gateway.vault_items (user_id, created_at DESC) WHERE deleted_at IS NULL;

CREATE TABLE gateway.wear_log (
  id        UUID PRIMARY KEY,
  user_id   UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  item_ids  UUID[] NOT NULL,
  look_id   UUID,
  occasion  TEXT,
  worn_on   DATE NOT NULL,
  source    TEXT,      -- manual | suggestion_accepted
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.wear_log (user_id, worn_on DESC);
```

`vault_items` soft-deletes because `wear_log` rows reference items historically, and a wear record pointing at nothing is worse than a tombstone.

---

## Looks and signals

```sql
CREATE TABLE gateway.saved_looks (
  id        UUID PRIMARY KEY,
  user_id   UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  look_id   UUID NOT NULL,       -- lives in ase; no cross-schema FK
  snapshot  JSONB NOT NULL,      -- denormalised so a saved look survives ase changes
  saved_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, look_id)
);

CREATE TABLE gateway.feedback_signals (
  id          UUID PRIMARY KEY,
  user_id     UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  target_type TEXT NOT NULL,     -- look | style | item
  target_id   UUID NOT NULL,
  signal      TEXT NOT NULL,     -- more_like_this | not_my_style
  context     JSONB,
  created_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, target_type, target_id)
);

CREATE TABLE gateway.action_events (
  id         UUID PRIMARY KEY,
  user_id    UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  action     TEXT NOT NULL,      -- shop_click | share_dna | share_look | tailor_share
  item_id    UUID,
  brand_id   UUID,
  look_id    UUID,
  surface    TEXT,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.action_events (user_id, created_at DESC);
```

`saved_looks.snapshot` is the one deliberate denormalisation in the schema: a saved look must remain viewable even if the underlying `ase` record is pruned or its renderer changes.

---

## Integrations

```sql
CREATE TABLE gateway.integration_accounts (
  id                 UUID PRIMARY KEY,
  user_id            UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  provider           TEXT NOT NULL,        -- pinterest
  provider_uid       TEXT NOT NULL,
  access_token_enc   BYTEA NOT NULL,
  refresh_token_enc  BYTEA,
  scopes             TEXT[] NOT NULL,
  expires_at         TIMESTAMPTZ,
  status             TEXT NOT NULL,        -- active | needs_reauth | revoked | syncing
  sync_cursor        JSONB,
  last_sync_at       TIMESTAMPTZ,
  created_at         TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, provider)
);
```

---

## Notifications (module — extractable)

```sql
CREATE TABLE gateway.notify_preferences (
  user_id           UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  category          TEXT NOT NULL,     -- style | activity | marketing
  channel           TEXT NOT NULL,     -- push | email | whatsapp | sms | inbox
  enabled           BOOLEAN NOT NULL DEFAULT TRUE,
  quiet_hours_start SMALLINT,
  quiet_hours_end   SMALLINT,
  PRIMARY KEY (user_id, category, channel)
);

CREATE TABLE gateway.notify_deliveries (
  id             UUID PRIMARY KEY,
  user_id        UUID NOT NULL,
  template_id    TEXT NOT NULL,
  channel        TEXT NOT NULL,
  event_id       UUID,               -- idempotency key against redelivery
  status         TEXT NOT NULL,      -- queued | sent | delivered | failed | suppressed
  failure_reason TEXT,
  sent_at        TIMESTAMPTZ,
  delivered_at   TIMESTAMPTZ,
  opened_at      TIMESTAMPTZ,
  created_at     TIMESTAMPTZ NOT NULL DEFAULT now(),
  UNIQUE (user_id, template_id, event_id)
);

CREATE TABLE gateway.notify_inbox (
  id        UUID PRIMARY KEY,
  user_id   UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  title     TEXT NOT NULL,
  body      TEXT,
  category  TEXT NOT NULL,
  deeplink  TEXT,
  image_url TEXT,
  read_at   TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.notify_inbox (user_id, created_at DESC);

CREATE TABLE gateway.notify_devices (
  id         UUID PRIMARY KEY,
  user_id    UUID NOT NULL REFERENCES gateway.users(id) ON DELETE CASCADE,
  platform   TEXT NOT NULL,
  token_enc  BYTEA NOT NULL,
  last_seen_at TIMESTAMPTZ,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);
```

The `UNIQUE (user_id, template_id, event_id)` constraint on deliveries is what makes redelivery safe: a replayed event cannot produce a second push.

---

## Admin

```sql
CREATE TABLE gateway.admin_users (
  id            UUID PRIMARY KEY,
  email_enc     BYTEA NOT NULL,
  email_bidx    TEXT NOT NULL UNIQUE,
  role          TEXT NOT NULL,     -- viewer | curator | support | ml_ops | admin
  mfa_enrolled  BOOLEAN NOT NULL DEFAULT FALSE,
  status        TEXT NOT NULL DEFAULT 'active',
  last_login_at TIMESTAMPTZ,
  created_at    TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE TABLE gateway.audit_log (          -- append-only; no UPDATE, no DELETE
  id            UUID PRIMARY KEY,
  actor_id      UUID NOT NULL,
  actor_role    TEXT NOT NULL,
  action        TEXT NOT NULL,
  target_type   TEXT NOT NULL,
  target_id     UUID,
  before        JSONB,
  after         JSONB,
  justification TEXT,
  ip            INET,
  occurred_at   TIMESTAMPTZ NOT NULL DEFAULT now()
);
CREATE INDEX ON gateway.audit_log (target_id, occurred_at DESC);
CREATE INDEX ON gateway.audit_log (actor_id, occurred_at DESC);
```

`audit_log` is append-only at the role level: the application role holds `INSERT` and `SELECT`, never `UPDATE` or `DELETE`. Its retention is seven years, separate from every other table, because it is the artefact that demonstrates access accountability to a regulator.

---

## Outbox

```sql
CREATE TABLE gateway.outbox (
  id           UUID PRIMARY KEY,
  event_name   TEXT NOT NULL,
  event_version INTEGER NOT NULL DEFAULT 1,
  user_id      UUID,
  trace_id     TEXT,
  payload      JSONB NOT NULL,
  occurred_at  TIMESTAMPTZ NOT NULL,
  published_at TIMESTAMPTZ,
  attempts     INTEGER NOT NULL DEFAULT 0
);
CREATE INDEX ON gateway.outbox (published_at, occurred_at) WHERE published_at IS NULL;
```

Written in the same transaction as the state change it describes. The relay publishes and stamps `published_at`. This is what makes "state saved but event lost" impossible.

---

## Roles

```sql
CREATE ROLE faue_gateway LOGIN;
GRANT USAGE ON SCHEMA gateway TO faue_gateway;
GRANT SELECT, INSERT, UPDATE, DELETE ON ALL TABLES IN SCHEMA gateway TO faue_gateway;
REVOKE UPDATE, DELETE ON gateway.audit_log FROM faue_gateway;
REVOKE UPDATE, DELETE ON gateway.quiz_responses FROM faue_gateway;

-- no grant on any other schema
REVOKE ALL ON SCHEMA ase, catalog, media FROM faue_gateway;
```

DDL belongs to `faue_migrator` alone. The service role cannot alter tables, so runtime code can never migrate accidentally.

---

## Retention

| Table | Retention | Enforced by |
|---|---|---|
| `refresh_tokens` | 30 days past expiry | `retention_ttl` worker |
| `quiz_responses` | Life of account | — |
| `wear_log` | Life of account | — |
| `action_events` | 24 months | `retention_ttl` worker |
| `notify_deliveries` | 12 months | `retention_ttl` worker |
| `notify_inbox` | 6 months | `retention_ttl` worker |
| `audit_log` | 7 years | Separate policy |
| `deletion_ledger` | 7 years | Separate policy |
| `outbox` | 7 days after publish | `outbox_relay` |

Every retention period also appears in [`../../10-architecture/ropa.md`](../../10-architecture/ropa.md) with its lawful basis. If the two disagree, the RoPA is authoritative.
