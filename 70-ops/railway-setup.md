# Railway — first deployment

**Stage:** MVP · **Owner:** backend · **Complements:** [`deployment.md`](deployment.md), which covers the ongoing pipeline. This is the one-time setup.

Order matters here. Several steps produce values the next step needs, and doing
them out of order means going back to fill in variables against a service that
has already failed to boot.

---

## 0. Before you start

Have ready:

- A Railway account with a card attached. The free tier will not fit Postgres,
  Redis and three services.
- A Cloudinary account (`CLOUDINARY_URL` from its dashboard).
- The Resend API key already in your local `.env`.
- The domain `faueofficial.com` in Hostinger, where DNS lives.

**What you do not have yet, and what that costs:** the image detection models
are not installed, so `NullDetector` is the only detector available — and
`pipeline.process` refuses to run it outside `ENVIRONMENT=local`. **Uploads will
fail on staging and production until the models are installed and validated.**
Everything else works. Deploy anyway; that is the point of getting the rest
standing up first.

---

## 1. Project and environments

One Railway **project**, two **environments**: `staging` and `production`.

Not two projects. Two environments in one project share the service definitions,
so a service added to staging exists in production with its own variables rather
than being recreated by hand and drifting.

---

## 2. Postgres

Add the Postgres plugin. Then, once, from a shell with `DATABASE_URL` pointed at it:

```sql
CREATE EXTENSION IF NOT EXISTS vector;
```

`pgvector` is not enabled by default and the first migration fails without it.

**Roles.** `provision-local.sh` creates `faue_migrator`, `faue_gateway` and
`faue_ase` locally; Railway gives you one superuser. Create the same three there
by hand — the separation is what stops a service role altering tables, and it is
tested in `faue-db`:

Create **only the roles** here, and nothing else:

```sql
CREATE ROLE faue_migrator LOGIN PASSWORD '<generate>' CREATEDB;
CREATE ROLE faue_gateway  LOGIN PASSWORD '<generate>';
CREATE ROLE faue_ase      LOGIN PASSWORD '<generate>';
```

**The grants are owned by the migrations, not by you.** `0001_initial_schema`
issues eight of them and `0007_default_grants` sets the defaults that apply to
tables created later — including the `REVOKE UPDATE, DELETE ON
gateway.audit_log` that keeps the audit log append-only. Granting by hand here
duplicates them and, worse, cannot work: `GRANT USAGE ON SCHEMA gateway` needs
the `gateway` schema, and nothing has created it yet.

The ordering is therefore fixed, and each step fails loudly if you skip the one
before it:

| Order | Step | Skipping it gives you |
|---|---|---|
| 1 | `CREATE EXTENSION vector` (superuser) | `RuntimeError: pgvector is not installed in this database.` |
| 2 | `CREATE ROLE` ×3 (superuser) | `psycopg2.errors.UndefinedObject: role "faue_gateway" does not exist` — from `GRANT USAGE ON SCHEMA gateway TO faue_gateway` inside migration `0001` |
| 3 | `alembic upgrade head` (as `faue_migrator`) | `relation "gateway.auth_identities" does not exist`, at runtime, to a real user |

No migration creates a role. That is deliberate — roles are cluster-level and
shared, so a migration creating one would make the same migration unrunnable on
a cluster where it already exists — but it does mean step 2 is a genuine
prerequisite rather than a convenience.

### `DATABASE_URL` is rewritten for you

Railway's plugin injects `postgresql://...`. SQLAlchemy's async engine needs an
async driver named in the scheme, so the bare form raises

```
InvalidRequestError: The asyncio extension requires an async driver to be used.
The loaded 'psycopg2' is not async.
```

inside the lifespan — which uvicorn reports only as `Application startup failed`,
with the cause buried under a dozen `merged_lifespan` frames.

Both services normalise the scheme on load (`faue_core.config.normalise_database_url`),
so `${{Postgres.DATABASE_URL}}` can be wired straight in. A scheme that already
names a driver is left alone, including a deliberately synchronous one — Alembic
runs sync and is entitled to psycopg.

Enable **PITR** on the plugin. It is the only thing standing between a bad
migration and a lost week.

---

## 3. Redis

Add the Redis plugin. Note the URL.

**Redis is a hard dependency for admin auth.** The session deny-list is checked
on every admin request and fails closed, so a Redis outage locks the console
rather than honouring sessions someone has already ended. It also holds magic
links, rate limits and TOTP replay protection — an outage stops sign-in
entirely. Size it accordingly; this is not a cache.

---

## 4. Secrets

Generate them, do not invent them:

```bash
python faue-infra/scripts/generate_secrets.py
```

Paste into Railway's variable editor per environment. **Never** reuse the values
between staging and production — a staging leak would otherwise be a production
compromise.

| Variable | Notes |
|---|---|
| `JWT_PRIVATE_KEY` / `JWT_PUBLIC_KEY` | Ed25519, base64url, single line. Not PEM — Railway mangles embedded newlines |
| `JWT_PUBLIC_KEY_NEXT` | Leave empty. Set only during a rotation |
| `SERVICE_JWT_SECRET` | **Byte-identical in `api-gateway` and `ase`**, or every internal call is rejected |
| `ASE_SERVICE_TOKEN` | Same — identical in both |
| `CLOUDFLARE_ACCOUNT_ID` / `CLOUDFLARE_API_TOKEN` | `ase` only. Optional: with both set, tasks whose model slug starts `@cf/` (the small, free-tier models the pilots validated) use Workers AI. Without them every model task takes its template path, which is a working product |
| `OPENROUTER_API_KEY` | `ase` only. Optional: lets a paid OpenRouter slug in `app/models/config/models.yaml` serve a tier. Never enable without a budget ceiling (`AI_BUDGET_*`) |
| `RABBITMQ_URL` | `ase-events` as well as the gateway's workers: the broker the event consumer reads |
| `ENCRYPTION_MASTER_KEY` | Losing this makes every encrypted column permanently unreadable. It is the one value worth storing somewhere else as well |
| `BLIND_INDEX_PEPPER` | Rotating it invalidates every email lookup. Set once |

---

## 5. Services

Four, from three repositories.

### `api-gateway` — public

```
Root directory   /            (the api-gateway repo)
Build            pip install .
Start            python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT
Health check     /readyz
Public domain    api.faueofficial.com
```

Three things here, each a failed deploy if changed:

**`python -m uvicorn`, not `uvicorn`.** The bare command depends on a console
script being on the runtime `PATH`, and Railway's build and run phases do not
always resolve the same environment — the symptom is `bash: uvicorn: command not
found` in a restart loop with the package demonstrably installed. `python -m`
runs it through the interpreter that has it.

**`--host 0.0.0.0`.** uvicorn binds `127.0.0.1` by default, the container is then
unreachable from outside itself, and Railway reports a failing health check with
no clue as to why.

**`$PORT`.** Injected by Railway; never hardcode 8000.

`pip install .` is enough — `pyproject.toml` pulls `faue-core[web]` and
`faue-db` from git. There is no `requirements.txt` and no editable install;
those are local-development mechanics.

> **`faue-core` and `faue-db` are not Railway services.** They are libraries,
> installed into each service's image at build time from git. Do not create
> services for them — the container would boot and exit.
>
> `pyproject.toml` already declares them, pinned to `@v0.1.0`. **That tag must
> exist before the first build**, and `faue-core` must be tagged before
> `faue-db` because `faue-db` pins it in turn:
>
> ```bash
> cd faue-core && git tag v0.1.0 && git push origin v0.1.0
> cd ../faue-db && git tag v0.1.0 && git push origin v0.1.0
> ```
>
> Full explanation, including the `[web]` extra and why it is needed:
> [`../20-services/shared-package-deploys.md`](../20-services/shared-package-deploys.md).

### `ase` — private

```
Root directory   /            (the ase repo)
Build            pip install .
Start            python -m uvicorn app.main:create_app --factory --host 0.0.0.0 --port $PORT
Health check     /readyz
No public domain
```

Reachable only over Railway's private network, from the gateway. If `ase` has a
public domain, the internal-auth boundary is decoration.

### `ase-events` — private

The consumer for what the rest of the platform tells `ase` (the same image as `ase`, a different start command). It erases what
`ase` holds when someone withdraws personalisation or AI consent or deletes their account (and confirms with
`user.deletion.completed`), and forgets what was learned from a removed wardrobe item. Without it a deletion request waits
forever for `ase` to confirm:

```
Root directory   /            (the ase repo)
Build            Dockerfile
Start            python -m app.workers.events
No public domain, no health check
```

Needs `DATABASE_URL`, `RABBITMQ_URL` and the `ase` variables. It exits on an unrecoverable error so Railway restarts it; a message
that fails twice goes to the `ase.events.dead` queue rather than blocking the rest. Handlers are idempotent, so redelivery is harmless.

### `workers` — private

One service, both workers in one process. Two small polling loops do not each
justify a container, an idle allocation and something else to watch:

```
Root directory   /            (the api-gateway repo)
Build            pip install .
Start            python -m app.workers
No public domain, no health check
```

`python -m app.workers` runs everything implemented — currently `outbox_relay`
and `backup_replication`. Name them to run a subset:

```
python -m app.workers outbox_relay
```

If one loop dies the process exits rather than limping on, because a worker
service that looks healthy while events pile up unpublished is worse than one
Railway restarts.

Separate from the API because the relay holds row locks while it publishes, and
doing that inside a request would put broker latency on a user's response.

### `media-worker` — private, and not yet

The PII pipeline worker. Do **not** deploy it until the detection models are
installed — see §0. When it exists its start command will be
`python -m app.workers media_pipeline`, from the same repo with the `[media]`
extra installed instead of `[web]`.

Its requirements are `faue-core/requirements/media.in`, which is deliberately a
worker-only role: it carries ~500 MB of models plus torch, and keeping it out of
the gateway's image is why the API instances stay small.

---

## 6. Storage

| Variable | Value |
|---|---|
| `STORAGE_PROVIDER` | `cloudinary` |
| `CLOUDINARY_URL` | `cloudinary://<key>:<secret>@<cloud>` |

`local` is refused outside `ENVIRONMENT=local` and the service will not start
with it. That is deliberate: Railway's filesystem is ephemeral, so images would
vanish on the next deploy and you would find out days later as "my wardrobe is
empty".

### Backup replica

A backup sharing a failure domain with the thing it backs up is not a backup.
Primary is Cloudinary, so **Railway's own bucket service is a genuine backup** —
a Cloudinary outage or account problem leaves the copy intact.

| Variable | Railway | Cloudflare R2 |
|---|---|---|
| `BACKUP_PROVIDER` | `railway` | `r2` |
| `BACKUP_BUCKET` | — see below | bucket name |
| `BACKUP_ENDPOINT_URL` | — see below | — |
| `R2_ACCOUNT_ID` | — | from the R2 dashboard |
| `BACKUP_ACCESS_KEY_ID` / `BACKUP_SECRET_ACCESS_KEY` | — see below | both |

**Railway injects its own names**, and the code reads them directly — copying
four values into differently-named variables is four chances to paste the wrong
half, and the failure is an empty bucket discovered during a restore. Set only
`BACKUP_PROVIDER=railway` and leave these alone:

```
RAILWAY_S3_URL       → endpoint
RAILWAY_NAME         → bucket
RAILWAY_ACCESS_ID    → access key
RAILWAY_SECRET_KEY   → secret
```

The explicit `BACKUP_*` variables still win where set, so a deployment can point
at R2 while Railway's own bucket variables are present in the environment.

Leaving these unset is allowed — the replication worker refuses to run and logs
that every image has exactly one copy, rather than pretending. That is a real
choice with a real cost, made visibly.

Add `python -m app.workers.backup_replication` to the workers service once
configured.

---

## 7. Migrations

A **separate job**, run before the service deploy, as `faue_migrator`:

```bash
cd faue-db
cp .env.example .env     # DATABASE_URL is the only variable this repo reads
alembic upgrade head
alembic current          # confirm: should print a revision, not nothing
```

Service roles cannot alter tables, which is why this is its own job with its own
credentials rather than something the API does at startup.

### Use the migrator role, not the service role

The single most likely mistake is pasting the gateway's `DATABASE_URL` into
`faue-db/.env`. It fails like this:

```
sqlalchemy.exc.ProgrammingError: (psycopg2.errors.InsufficientPrivilege)
permission denied for database faue
[SQL: CREATE SCHEMA IF NOT EXISTS gateway]
```

That is the privilege separation working. `faue_gateway` genuinely cannot
`CREATE`, because a runtime role that can reshape the schema is a runtime role
that can drop it. Check which role a URL carries before assuming it is the
right one:

```bash
psql "$DATABASE_URL" -tAc "SELECT current_user, has_database_privilege(current_user, current_database(), 'CREATE');"
```

`faue_migrator | t` is what you want.

### pgvector must already exist

The first migration needs the extension, and creating an extension requires a
superuser — which `faue_migrator` is not. `env.py` refuses to start without it:

```
RuntimeError: pgvector is not installed in this database.
```

Railway's stock Postgres image does not ship pgvector, so this is a
provisioning decision rather than something to fix afterwards. Verify before
deploying:

```bash
psql "$DATABASE_URL" -tAc "SELECT extname FROM pg_extension WHERE extname='vector';"
```

Empty means redeploy the database from Railway's pgvector template.

### Skipping this is visible in `/readyz`

Migrations are deliberately **not** run at boot — two instances starting at
once would race the same migration, and a migration failing inside a health
check reads as a crash loop rather than as a failed migration.

So "deployed against an empty database" is a state that really happens. It used
to surface as a signed-in user hitting

```
relation "gateway.auth_identities" does not exist
```

on an instance that had reported itself ready, because readiness ran `SELECT 1`
— which an unmigrated database answers perfectly happily. `/readyz` now checks
`alembic_version` separately and reports it under its own key:

```json
{"status": "not_ready",
 "checks": {"migrations": {"status": "failure", "reason": "RuntimeError"}},
 "failing": ["migrations"]}
```

`failing: ["migrations"]` means run `alembic upgrade head`. It is reported
apart from `database` because the two need different actions — one is
connectivity, the other is a command.

**The check uses `to_regclass` only, and must keep doing so.** The obvious
implementation — `SELECT version_num FROM alembic_version` — does not work,
because the service roles are deliberately denied that table:

```
ERROR:  permission denied for table alembic_version
```

Migration metadata is not the gateway's to read. A probe that needs it fails
closed against a perfectly healthy database, so every instance reports
not-ready forever and nothing is ever routed traffic — a total outage produced
by a safeguard. `to_regclass` is a name lookup requiring no privilege on the
table, and it returns `NULL` rather than raising when the relation is absent.

This is invisible to the test suite, which connects as `faue_migrator` and can
read anything. `test_the_migration_check_works_as_the_service_role` drops to
`faue_gateway` specifically to catch it.

Expand-only, always. See [`deployment.md`](deployment.md) §3 — a breaking
migration shipped with the code that needs it makes rollback impossible.

---

## 8. DNS

In Hostinger:

| Record | Name | Value |
|---|---|---|
| CNAME | `api` | Railway's generated domain |
| TXT | `resend._domainkey` | from Resend |
| TXT | `send` | Resend SPF |
| MX | `send` | Resend bounce handling |
| TXT | `_dmarc` | `v=DMARC1; p=none; rua=mailto:...` |

> Resend's root-domain layout looks wrong and is not: DKIM sits on the apex
> while SPF and MX sit on `send.`. Reading that as a misplaced record and
> "fixing" it breaks verification. `api-gateway/scripts/check_email_dns.py`
> verifies all four against a public resolver.

---

## 9. First admin

Inviting requires an admin to already exist, so account zero is created by
script — once, against production:

```bash
python api-gateway/scripts/create_admin.py you@faueofficial.com --role admin
```

It deliberately does not enrol MFA. You do that yourself on first sign-in
through the `428` path, which is what keeps the TOTP secret out of a terminal
and a shell history. Everyone after you is invited from the console.

---

## 10. Verifying the deploy

In order, because each answers a different question:

```bash
curl https://api.faueofficial.com/           # which service, which environment
curl https://api.faueofficial.com/healthz    # the process is alive
curl https://api.faueofficial.com/readyz     # Postgres, Redis and the broker are reachable
```

Start with `/`. It names the service and the environment and links to
everything below, which is what you want when you are holding two Railway URLs
and are not certain which is staging:

```json
{
  "service": "api-gateway",
  "version": "1.0.0",
  "status": "ok",
  "environment": "prod",
  "docs": {"swagger": "/docs", "redoc": "/redoc",
           "scalar": "/scalar", "openapi": "/openapi.json"},
  "health": {"live": "/healthz", "ready": "/readyz"}
}
```

An empty `docs` object is not a fault — ase serves no documentation in
production, and the root advertises only what is actually mounted rather than
linking to a 404.

`readyz` deliberately does **not** check `ase` — the gateway must stay in
rotation and keep serving vault, saves and profile while generation is down.

Then, signed in as admin:

```
GET /admin/v1/ops/health          per-dependency, not a boolean
GET /admin/v1/ops/events          unpublished vs parked
GET /admin/v1/ops/notifications   deliveries by status and failure reason
```

`parked` above zero means events exist that no consumer will ever see without
intervention. That is an incident, not a queue depth.

---

## 5a. Build with the Dockerfile, not Railpack

Each service ships a `Dockerfile`. Railway uses it in preference to its own
builder, and that is deliberate.

Railpack's autodetection produces a build that **succeeds and then cannot
start**:

```
mise python@3.13.15 ✓ installed
pip install .          →  WARNING: Running pip as the 'root' user...
copy /etc/mise/config.toml, /root/.local/state/mise, /app
```

It installs as root into a path the final image layer never copies forward, so
the container starts and reports

```
/mise/installs/python/3.13.15/bin/python: No module named uvicorn
```

on a loop — with a green build log above it. Nothing in the application is
wrong; the packages are simply not in the image.

The Dockerfile removes every variable behind that:

| | Why |
|---|---|
| One venv at `/opt/venv`, named by absolute path | No PATH guessing, no shell profile the runtime may not source |
| Python **3.12**, pinned | Railpack defaults to the newest (3.13); `requires-python` says 3.12 and that is what the suite runs against |
| `import uvicorn, fastapi, faue_core, faue_db` as a build step | Fails the **build** rather than shipping an image that crash-loops |
| `CMD exec ... --port "${PORT:-8000}"` | Shell form so `$PORT` expands; `exec` so uvicorn takes SIGTERM directly and stops in ~2s instead of being killed after the grace period |
| Non-root `faue` user, multi-stage | The build toolchain stays in the builder stage |

**Leave Railway's build and start commands blank.** The Dockerfile supplies
both. Setting them re-introduces exactly the mismatch it exists to prevent.

Verified locally before deploying — build, run, and every property above:

```bash
cd api-gateway && docker build -t faue-gateway:test .
docker run --rm -e PORT=8085 ... faue-gateway:test
```

### Testing the image locally: don't trust `--env-file .env`

Docker's `--env-file` parser is **not** a dotenv parser. It does not strip
trailing comments, so a line written for python-dotenv

```
ENVIRONMENT=local                  # local | staging | prod
```

arrives in the container as the literal string `local                  # local |
staging | prod`, and the service dies before it ever reaches the lifespan:

```
pydantic_core._pydantic_core.ValidationError: 2 validation errors for Settings
environment
  Input should be 'local', 'staging' or 'prod' [type=literal_error, ...]
```

This is a local-testing artifact only — Railway variables are set field by
field in the dashboard and carry no inline comments. But when you are already
hunting a startup crash it looks exactly like one, so override the commented
keys explicitly when running the image by hand:

```bash
docker run --env-file .env -e ENVIRONMENT=local -e EVENT_TRANSPORT=inprocess ...
```

---

## 10a. If the container keeps restarting

`/readyz` was a stub that returned `200 {"status":"ok","checks":{}}` regardless
of whether anything was reachable. That is worse than having no probe: Railway
believes a broken container is healthy, routes traffic to it, and every request
fails — which reads as "crashing a lot" with a green health check and no way to
tell which dependency is down.

It now opens a real connection and returns **503** when one is unreachable:

```json
{
  "status": "not_ready",
  "checks": {
    "database": {"status": "failure", "reason": "ConnectionRefusedError", "latency_ms": 31.4},
    "redis":    {"status": "success", "latency_ms": 6.5}
  },
  "failing": ["database"]
}
```

So when a deploy will not come up, ask the container directly:

```bash
curl -s https://api.faueofficial.com/readyz | jq
```

`healthz` stays 200 through all of this, deliberately: it answers "is the
process alive?" and must never fail for a downstream outage, or a partial outage
becomes a restart loop.

**Point Railway's health check at `/readyz`, not `/healthz`.** `healthz` cannot
fail, so a check pointed at it never removes a broken instance from rotation.

---

## 11. What will bite

Ordered by how likely each is to be your first failure.

1. **`No module named uvicorn`** with a green build log — Railpack installed to
   a path the runtime image does not carry. Build from the Dockerfile and leave
   Railway's build/start commands blank. §5a.
2. **Restart loop with a healthy health check** — the probe is pointed at
   `/healthz`, which cannot fail by design. Point it at `/readyz`. §10a.
3. **`Could not find a version that satisfies the requirement faue-core`** —
   `faue-core` or `faue-db` is private, so the build cannot clone it and falls
   back to PyPI. Reads like a missing package; is a permissions problem. §5.
4. **`pathspec 'v0.1.0' did not match any file(s) known to git`** — the shared
   package tags do not exist, or do not point at the commit you expect. §5.
5. **`permission denied for table <something new>`** — a table added after
   `0001` with no grant. Migration `0007` sets `ALTER DEFAULT PRIVILEGES`, but
   the three roles must exist *before* migrations run. §2.
6. **`extension "vector" does not exist`** — §2, one `CREATE EXTENSION`.
7. **Every internal call rejected** — `SERVICE_JWT_SECRET` differs between
   `api-gateway` and `ase`. It must be byte-identical.
8. **Service will not start with `STORAGE_PROVIDER=local`** — working as
   intended. §6.
9. **Uploads fail** — expected until the detection models are installed. §0.
10. **Admin cannot sign in** — Redis unreachable. It is a hard dependency, not a
    cache. §3.
11. **Magic links never arrive** — DNS not verified in Resend. §8.
