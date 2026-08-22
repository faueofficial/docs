# Shared packages — how services find `faue-core` and `faue-db`

**Stage:** MVP · **ADRs:** [0003](../80-adr/0003-no-root-git-per-service-repos.md), [0004](../80-adr/0004-single-alembic-project-in-faue-db.md)

`api-gateway` and `ase` both depend on `faue-core` (shared plumbing) and
`faue-db` (models and migrations), which live in their own repositories. That is
the cost ADR 0003 accepted: no monorepo means shared code must be **released**
rather than imported across a directory boundary.

A service will not start until those packages are installed. This page is how.

---

## Three modes, and you need all three

| Mode | Where the packages come from | Used by |
|---|---|---|
| **Editable siblings** | `../faue-core`, `../faue-db` on disk | Local development |
| **Pinned git refs** | `pyproject.toml` dependencies | CI, container builds |
| **Sibling checkout** | `actions/checkout` into a path | CI where a token is unavailable |

### 1. Local development

```bash
make install     # installs dev requirements, then editable siblings, then this service
make dev
```

Editable is the point: a change in `faue-core` is live immediately, with no
tag-and-reinstall cycle. Without it, every shared-library edit becomes a version
bump, and shared plumbing stops getting fixed.

If the siblings are not cloned:

```bash
../docs/scripts/bootstrap.sh
```

### 2. CI and containers

`pyproject.toml` declares pinned git references:

```toml
dependencies = [
    "faue-core @ git+https://github.com/faueofficial/faue-core.git@v0.1.0",
    "faue-db   @ git+https://github.com/faueofficial/faue-db.git@v0.1.0",
]
```

```bash
make install-ci    # pip install -e .
```

### 3. Preflight

Both services run `scripts/preflight.py` before `dev`, `worker` and `test`. A
missing package produces a message naming the package, whether the sibling is
cloned, and the three fixes — rather than an `ImportError` three frames deep in
a router, which tells you nothing.

---

## The private-repository problem

Pinned git references over HTTPS need credentials when the repository is
private. This bites in exactly two places, and neither is obvious until a build
fails.

### CI

Avoid the credential entirely by checking the siblings out:

```yaml
- uses: actions/checkout@v4
  with: { repository: faueofficial/faue-core, path: faue-core, token: ${{ secrets.REPO_TOKEN }} }
- uses: actions/checkout@v4
  with: { repository: faueofficial/faue-db, path: faue-db, token: ${{ secrets.REPO_TOKEN }} }
- run: pip install -e ./faue-core -e ./faue-db -e .
```

### Container and Railway builds

Railway builds from a single connected repository, so the siblings do not exist
and a credential is unavoidable. Options, best first:

| Option | Trade |
|---|---|
| **Make `faue-core` and `faue-db` public** | Removes the problem completely. Neither contains secrets — one is generic plumbing, the other is a schema. The schema reveals product structure, nothing more |
| Build-time secret | Railway build variable holding a fine-grained PAT scoped to those two repositories, read-only. Works, but a token in a build environment is a token to rotate |
| Private package index | GitHub Packages or a private PyPI. Cleanest long-term, most setup now |
| Vendor the packages into the image | Copy the source at build time. Removes versioning, which is the thing the packages exist to provide |

**Recommendation: make both repositories public.** It removes an entire class of
build failure and a credential to rotate, and the only thing being disclosed is
that FAUE has a `vault_items` table. If that is uncomfortable, use a fine-grained
read-only PAT in a Railway build variable and put its rotation on the same
schedule as every other secret.

---

## Releasing a shared package

Both are semantically versioned and tagged. Services pin exact versions.

| Change | Bump | Consequence |
|---|---|---|
| New helper, new optional field | Minor | Services upgrade when convenient |
| Bug fix | Patch | Same |
| Interface change, removed helper | **Major** | Every service updates its pin in the same release cycle |
| Column removed or retyped in `faue-db` | **Major** | Coordinate with the migration deploy ordering |

That coordination is the friction ADR 0003 traded for independent repositories.
At a two-person team it is a few minutes; the exit, if it stops being worth it,
is a monorepo — which is a scripted history graft rather than a redesign.
