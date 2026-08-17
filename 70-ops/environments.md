# Environments

**Stage:** MVP

---

## 1. The three

| Environment | Purpose | Data | Who |
|---|---|---|---|
| `local` | Development | Seeded fixtures | Backend |
| `staging` | Integration, frontend development, QA | Synthetic and anonymised | Backend + frontend |
| `prod` | Live | Real | Backend |

---

## 2. Local

Services run **directly under uvicorn**, not in containers. Disk and memory on a development machine are finite, and a full container stack is a poor trade for the fidelity it buys.

```bash
source .venv/bin/activate

uvicorn app.main:app --reload --port 8000   # api-gateway
uvicorn app.main:app --reload --port 8001   # ase
# 8002 catalog (M1-2), 8003 media (M1-2)

arq app.workers.WorkerSettings              # workers, separate process
```

Fixed ports so nothing collides and every runbook can name them.

### Infrastructure without containers

The documented default avoids containers entirely:

| Dependency | Local default | Why |
|---|---|---|
| Postgres + pgvector | Hosted free tier (Neon or similar) | No disk cost, pgvector already enabled |
| Redis | Hosted free tier (Upstash or similar) | Trivial workload |
| RabbitMQ | **In-process event bus** | `EVENT_TRANSPORT=inprocess` behind the same interface |
| Object storage | Local filesystem adapter | No MinIO needed |

The in-process bus dispatches to registered handlers after commit. It exercises handler logic without a broker running, which is enough for most development.

### Full fidelity when needed

`faue-infra/compose.yaml` provides an infra-only profile for the cases where the in-process bus is not enough — testing retry, dead-lettering, or consumer lag:

```bash
docker compose --profile infra up -d   # postgres+pgvector, redis, rabbitmq, minio
```

Services still run under uvicorn. The compose file never runs application code.

### Seeding

```bash
python -m scripts.seed --users 5 --vault-items 20 --looks 10 --style-library
```

Creates test users at each onboarding stage, a populated vault, generated looks with recorded model fixtures, and the style library. No real user data ever reaches a development machine.

---

## 3. Staging

Production-shaped, on Railway, at smaller instance sizes. Stable URL for the frontend engineer.

- Real broker, real Postgres, real Redis.
- Model calls go to **real providers** on a separate budget with a hard monthly cap — otherwise model-related bugs are only ever found in production.
- **Mock mode:** `X-Mock-Mode: true` returns recorded fixtures per endpoint, so frontend work is not blocked on unfinished backend flows.
- Data is synthetic or anonymised. Copying production data to staging is prohibited.
- Reset weekly to keep fixtures predictable.

---

## 4. Production

Railway. Topology and procedure in [`deployment.md`](deployment.md).

| Component | Configuration |
|---|---|
| `api-gateway` | Public domain, 2 instances |
| `ase` | **Private networking only, no public domain** |
| Workers | Separate services, scaled independently |
| Postgres | Railway plugin, PITR enabled |
| Redis | Railway plugin |
| RabbitMQ | Template or CloudAMQP |
| `faue-web`, `faue-admin` | Vercel |
| Object storage | Cloudinary (primary) · Cloudflare R2 (backup) |

---

## 5. Cost

### Expected monthly

| Item | Cost |
|---|---|
| Railway — gateway, ase, workers | $25–40 |
| Postgres | $10–20 |
| Redis | $5–10 |
| RabbitMQ | $0–10 |
| Object storage and CDN | $0–15 |
| Vercel | $0 |
| Model spend (LLM) | $20–40 |
| **Image generation** | **$20–60** |
| Email | $0–10 |
| Monitoring | $0 |
| **Total** | **$80–205** |

Ceiling is $150/month, which the range straddles. **Image generation is the variable that decides it**, and it is the first lever: switching the renderer to `composite` removes that line entirely.

### Embedding provider — the break-even

The provider choice inverts between hosts, which is why it is configuration rather than architecture.

| Option | Cost shape |
|---|---|
| Self-hosted open-CLIP | 2–4 GB resident, ~$10–20/month on Railway, unlimited calls |
| Hosted API | ~$0.0001 per image, no idle cost |

Break-even is roughly **150,000 embeddings per month**.

At MVP scale — 5,000 users × 30 vault items plus imported pins, spread over months — actual volume is well under 50,000/month. **Hosted is cheaper on Railway.** After a VPS migration, where RAM is already paid for, self-hosted becomes cheaper.

Recheck this arithmetic when vault volume or hosting changes. Do not carry the conclusion forward as though it were permanent.

### VPS comparison

| | Railway | Hetzner CCX (8–16 GB) |
|---|---|---|
| Compute | $25–40 | $25–35 fixed |
| Managed database | $10–20 | Self-managed, or Neon |
| Operational load | Near zero | Patching, TLS, backups, monitoring |
| Embeddings | Hosted API cheaper | Self-hosted free within the box |
| Scaling | Automatic | Manual |

Railway wins at launch because operational time is the scarcer resource. Revisit when usage is predictable and the model spend is understood — likely around M1-2.

---

## 6. Configuration

Every service ships `.env.example` documenting every variable. A missing required variable fails at startup, loudly.

Differences that matter across environments:

| Variable | local | staging | prod |
|---|---|---|---|
| `EVENT_TRANSPORT` | `inprocess` | `rabbit` | `rabbit` |
| `EMBEDDING_PROVIDER` | `hosted` | `hosted` | `hosted` |
| `RENDERER_DEFAULT` | `composite` | `generative` | `generative` |
| `AI_BUDGET_GLOBAL_MONTHLY` | 1 | 20 | 150 |
| `MOCK_MODE_ENABLED` | true | true | **false** |
| `LOG_LEVEL` | DEBUG | INFO | INFO |

`RENDERER_DEFAULT=composite` locally so development does not spend money on image generation by accident. That single default has saved more money than any other line in this table.

---

## 7. Access

| Environment | Who | How |
|---|---|---|
| local | Backend | Own machine |
| staging | Backend, frontend | Railway, URL shared |
| prod | Backend only | Railway, MFA required |
| prod database | **Nobody directly** | Admin console, or break-glass |

No standing production database access. Admin operations go through the console, which audits them; anything else needs break-glass with a stated reason.

---

## 8. Frontend onboarding

What the frontend engineer needs, in order:

1. `docs/` — the whole repository.
2. Staging base URL and a test account.
3. `X-Mock-Mode: true` for endpoints not yet built.
4. `gateway.v1.yaml` to generate the Dio client.
5. `screens.md` and `design-tokens.md`.

He needs no backend repository access and no local backend running. That is deliberate — if he does, the handoff documentation has failed.
