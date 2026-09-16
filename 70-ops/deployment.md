# Deployment

**Stage:** MVP · **Platform:** Railway (services), Vercel (static) · **ADR:** [0015](../80-adr/0015-railway-first-vps-later.md)

---

**First deployment?** [`railway-setup.md`](railway-setup.md) is the one-time
setup, in order. This document is the ongoing pipeline.

---

## 1. Topology

```
Vercel                 faue-web (faueofficial.com)  ·  faue-admin (admin.faueofficial.com, network-gated)
Railway  public        api-gateway (api.faueofficial.com)
Railway  private       ase  ·  workers  ·  postgres+pgvector  ·  redis  ·  rabbitmq
External               object storage + CDN  ·  email  ·  push  ·  model providers
```

`ase` has **no public domain**. It is reachable only over Railway's private network, from the gateway.

---

## 2. Pipeline

Per repository, GitHub Actions, templates in `faue-infra`.

```
push to main
  → lint (ruff)
  → typecheck (mypy --strict)
  → unit tests
  → integration tests (testcontainers)
  → contract tests (against the OpenAPI document)
  → eval suite (if prompts, models, engine, or guardrails changed)
  → build image, push to GHCR tagged by commit SHA
  → deploy to staging automatically

tag v*
  → migrations job (faue-db)
  → deploy to production
  → smoke tests
  → notify
```

Merges to `main` reach staging automatically. Production requires a tag, which is the only manual gate and deliberately so.

---

## 3. Migration ordering

Fixed and not negotiable:

```
1  Run migrations (EXPAND ONLY — additive, nullable, new tables)
2  Deploy service code
3  A LATER release contracts (drop columns, tighten constraints)
```

The migration job runs first, as a separate Railway job, and its success gates the service deploy. It runs as `faue_migrator`; service roles cannot alter tables.

Expand-contract is what makes rollback safe. A breaking migration shipped with the code that needs it means rolling back the code leaves the database ahead of it — and rolling back the database loses everything written in between.

CI enforces the model-migration pairing via `alembic check`; see [`../20-services/faue-db.md`](../20-services/faue-db.md).

---

## 4. Rollback

```bash
railway rollback --service api-gateway --to <previous-sha>
```

Images are tagged by commit, so rollback is immediate. Because migrations are expand-only, **no down-migration is ever needed in production** — the previous code runs fine against the newer schema.

If a migration itself is wrong, roll forward with a corrective migration rather than backward. Backward migrations lose data written since.

---

## 5. Zero-downtime

- Two gateway instances minimum, rolling replacement.
- `readyz` gates traffic; an instance receives requests only when its dependencies are reachable.
- Graceful shutdown: stop accepting, finish in-flight work, 30-second drain.
- Workers finish the current job before exiting; jobs are idempotent, so a killed worker's job is safely retried.
- `ase` may restart without gateway impact — generation degrades to the error state, everything else keeps working.

---

## 6. Configuration and secrets

Environment variables in Railway's secret store, per environment. A configuration change restarts the service; a **feature flag change does not**, which is the point — flags live in Redis and are readable at runtime.

Never in the repository. Never in a git remote URL. CI scans for secret patterns.

---

## 7. Static surfaces

Vercel, deployed on push. `faue-web` serves the deep-link well-known files, which must be exact:

```
/.well-known/apple-app-site-association     application/json, no extension, no redirect
/.well-known/assetlinks.json                both signing fingerprints
```

Both are easy to get subtly wrong and hard to debug afterwards — iOS caches the association file aggressively, and Android silently fails if the Play App Signing fingerprint is missing. Verify with a real device from a real message before launch.

`faue-admin` sits behind the network gate and is never publicly indexed.

---

## 8. Mobile

```
main       → build → TestFlight / Play internal track
tag v*     → build → App Store / Play production, staged rollout
```

App review takes days. **Ship the backend first**, keep the API backward compatible, and let the app catch up. A client that crashes on an unknown enum value is a client that blocks every future backend release — tolerance for unknown fields and values is a hard requirement.

---

## 9. Smoke tests

After every production deploy:

```
GET  /healthz                     200
GET  /readyz                      200
GET  /quiz                        200, six questions
POST /auth/link/request           202  (test address)
GET  /me                          200  (test account)
POST /looks/generate              202, job reaches done
```

Failure triggers automatic rollback and an alert. The generation check matters most because it exercises the gateway, `ase`, the model plane, and the renderer in one call.

---

## 10. VPS migration path

Documented now so the option stays open, not scheduled.

```
1  Provision Hetzner CCX (8–16 GB), Ubuntu LTS
2  Caddy for TLS and routing
3  docker compose with the same images from GHCR
4  Postgres managed (Neon) or on-box with PITR to object storage
5  Switch EMBEDDING_PROVIDER to self-hosted — RAM is already paid for
6  Migrate DNS, run in parallel for a week
7  Decommission Railway services
```

Trigger: predictable usage plus a monthly Railway bill materially above the fixed VPS cost, or embedding volume passing the break-even in [`environments.md`](environments.md).

Nothing in the application changes. Services are containerised and the embedding provider is configuration.

---

## 11. Release checklist

- [ ] CI green, including the eval suite
- [ ] Migrations reviewed and expand-only
- [ ] `CHANGELOG.md` updated if contracts changed
- [ ] Feature flags set for anything not yet ready
- [ ] Rollback target identified
- [ ] Deployed in a window where someone can watch it
- [ ] Smoke tests passed
- [ ] Dashboards checked for 15 minutes afterwards

The last one catches what smoke tests do not: error-rate and latency changes that only appear under real traffic.
