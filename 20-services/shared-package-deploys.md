# How `faue-core` and `faue-db` reach a deployed service

**Stage:** MVP · **Owner:** backend · **Relates to:** [ADR 0003](../80-adr/0003-no-root-git-per-service-repos.md), [`railway-setup.md`](../70-ops/railway-setup.md)

---

## The thing to understand first

**`faue-core` is not deployed.** Neither is `faue-db`. They are libraries — there
is no process to start, no port to bind, no Railway service to create. Creating
one would produce a container that boots and immediately exits.

They are **installed into** the services that use them, at image build time:

```
Railway service   api-gateway          ase              workers
                       │                 │                 │
build step        pip install .     pip install .     pip install .
                       │                 │                 │
                       ▼                 ▼                 ▼
                  faue-core         faue-core         faue-core
                  faue-db           faue-db           faue-db
                       ▲
                  fetched from GitHub, pinned to a tag
```

Three copies of the library exist at runtime, one inside each image. That is
normal for a library and is the whole reason the version is pinned: all three
must be the *same* copy, and a tag is what guarantees that.

---

## Why it cannot just work

Railway builds **one repository per service**. When it builds `api-gateway` it
has that repo and nothing else — no sibling `faue-core` directory, because the
workspace root is deliberately not a git repository ([ADR 0003](../80-adr/0003-no-root-git-per-service-repos.md)).

Locally this is invisible. `make install` does editable installs from the
sibling checkouts, so `import faue_core` resolves to
`/home/you/faue/faue-core/faue_core/`. Nothing in the code notices the
difference, which is exactly why the first container build is where it surfaces.

So each service declares them as **git dependencies**:

```toml
dependencies = [
    "faue-core[web] @ git+https://github.com/faueofficial/faue-core.git@v0.1.0",
    "faue-db @ git+https://github.com/faueofficial/faue-db.git@v0.1.0",
]
```

---

## One extra, and only one

`faue-core`'s dependencies include the whole serving baseline — fastapi,
uvicorn, redis, asyncpg, pyjwt, httpx, jinja2, otel. A bare
`pip install faue-core` gives a service everything it needs to start.

That was not the original design. The baseline sat behind a `[web]` extra, every
service had to remember `faue-core[web]`, and `ase` did not. The symptom was

```
bash: uvicorn: command not found
```

in a restart loop, with the package demonstrably installed — an error that says
nothing about a missing extra and costs a deployment to diagnose. The extra
saved a few tens of megabytes and bought a class of silent failure.

| Extra | Pulls | Used by |
|---|---|---|
| *(none)* | everything a service needs to serve HTTP | **every service** |
| `media` | + pillow, mediapipe, tesseract, open-clip, torch, boto3 | the PII worker only |

`media` remains an extra because it earns it: roughly 2GB of models, and keeping
that out of every API instance is a real saving rather than tidiness.

`web`, `service`, `worker` and `broker` survive as empty aliases so an existing
pin still resolves instead of failing on an unknown extra.

`requirements/*.in` still decides *versions* — it is what pip-compile pins. The
`pyproject.toml` decides *membership*, because a container build cannot read
those files before it has installed anything.

---

## `faue-db` does not declare `faue-core`

It needs it — `faue_db.types.EncryptedStr` reaches into `faue_core.crypto` — but
declaring it would pin a git URL inside a library, making that URL the only
acceptable source. A service installing `faue-core` from anywhere else (a
different tag, a local checkout, an editable install) then gets

```
ERROR: ResolutionImpossible
```

because pip sees two origins for one package. A bare name cannot work either,
since `faue-core` is not on PyPI.

Every consumer installs `faue-core` explicitly, at a version it chooses. The
import is lazy, so `faue_db` imports fine without it and fails only where the
type is used, with a clear `ImportError`.

## Release order during an incident

A fix that lands in `faue-core` does not reach a service until the tag moves.
Deploying the service first gets you a **new** crash — an `ImportError` for a
function that exists on your machine and not in the image.

So, always:

```bash
# 1. faue-core first, and re-point the tag
cd faue-core && git add -A && git commit && git tag -f v0.1.0 && git push -f origin v0.1.0

# 2. faue-db next, if it changed — its own pin resolves against faue-core
cd ../faue-db && git tag -f v0.1.0 && git push -f origin v0.1.0

# 3. only now deploy the services
```

The friction is the point: a shared library that changes under three services
without any of them noticing is how the schema and the models drift apart.

---

## Tagging, which is not optional

The pins reference `@v0.1.0`. **If that tag does not exist the build fails**,
with the least helpful message it could have chosen:

```
error: pathspec 'v0.1.0' did not match any file(s) known to git
```

pip clones the repository successfully first, so this reads like a network or
auth problem and is neither.

Release order matters, because `faue-db` itself depends on `faue-core`:

```bash
# 1. faue-core first — faue-db's own pin resolves against it
cd faue-core && git tag v0.1.0 && git push origin v0.1.0

# 2. then faue-db
cd ../faue-db && git tag v0.1.0 && git push origin v0.1.0

# 3. only now will a service build succeed
```

Bumping a shared package means a new tag and a matching bump in every service
that pins it. That friction is the point: a shared library that changes under
three services without any of them noticing is how the schema and the models
drift apart.

---

## Verifying before you deploy

The failure is a container build failure, which is a slow way to find out. Do it
in a clean virtualenv instead, which is what Railway effectively does:

```bash
python -m venv /tmp/verify
/tmp/verify/bin/pip install "git+https://github.com/faueofficial/faue-core.git@v0.1.0#egg=faue-core[web]"
/tmp/verify/bin/python -c "import faue_core.config, fastapi, uvicorn; print('ok')"
```

If that works, the service build will too. If it does not, no amount of Railway
configuration will help.

---

## Local development is unaffected

```bash
make install     # editable installs from the sibling checkouts
```

Editable installs take precedence over the git pins, so day-to-day work uses the
code in your working tree and an edit to `faue-core` is visible immediately in
`api-gateway` with no reinstall. The pins only take effect where no sibling
checkout exists — CI and container builds.

---

## When this bites

| Symptom | Cause |
|---|---|
| `pathspec 'v0.1.0' did not match any file(s)` | The tag does not exist. Tag and push, `faue-core` first |
| `ModuleNotFoundError: faue_core` | The service's `pyproject.toml` is missing the git dependency |
| `ModuleNotFoundError: fastapi` | Installed `faue-core` without the `[web]` extra |
| `Repository not found` | The repository is private and the build has no credentials |
| Works locally, fails in CI | Editable installs are masking a missing or wrong pin |
