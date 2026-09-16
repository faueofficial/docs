# API documentation

**Stage:** MVP · **Owner:** backend · **Relates to:** [`railway-setup.md`](../70-ops/railway-setup.md), [`openapi/`](openapi/)

Both services generate and serve their own reference. This page says where it
is, what is deliberately hidden, and how it stays honest.

---

## 1. Where it is

Every service serves these paths off its base URL:

| Path | What it is |
|---|---|
| `/` | Service identity and links to everything else |
| `/docs` | Swagger UI — executes requests against the live service |
| `/redoc` | ReDoc — reads best as a reference |
| `/scalar` | Scalar — reads well *and* generates client snippets |
| `/openapi.json` | The generated document all three render |

There is one schema and three renderings of it. None of them is a second source
of truth, and none is edited by hand.

### The root endpoint

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

`/` exists because Railway gives every service a URL and the first thing anyone
does with a URL is open it. A 404 answers none of the questions the person
opening it actually has.

`docs` reflects what is **actually mounted**. When documentation is disabled the
object is empty rather than listing links to 404s.

---

## 2. Who can see it

| | local | staging | prod |
|---|---|---|---|
| api-gateway | yes | yes | **yes** |
| ase | yes | yes | **no** |

**The gateway publishes in production, deliberately.** It is the public,
customer-facing API; a readable contract is a feature of it, and the app's
client is generated from that document.

**ase does not.** It has no public domain and no consumer that is not already
inside Railway's private network, so publishing there could only describe the
internal surface to whoever reached it.

### The admin realm has its own reference

`/admin/v1/*` is **documented**, but never from the public URL:

| | local | staging | prod |
|---|---|---|---|
| `/docs`, `/redoc`, `/scalar`, `/openapi.json` | `/v1` only | `/v1` only | `/v1` only |
| `/admin/docs`, `/admin/scalar` | page loads | page loads | page loads |
| `/admin/openapi.json` | **admin token required** | **admin token required** | **admin token required** |

The admin reference is served in **every** environment, including production —
operators work against production, and a reference that exists only where they
do not is a reference nobody reads. What protects it is authentication, not
absence.

The split is deliberate. `/admin/openapi.json` *is* the operator surface, so it
requires an admin session token, re-checked against the account and the
revocation deny-list on every request: a demoted or signed-out admin loses the
reference at the moment they lose the API. The two HTML pages hold no API
description at all — a token box and a loader, under 3 KB — so they stay
reachable, because they are where the credential is entered.

Swagger and Scalar both load a spec by URL using their own `fetch`, which sends
no `Authorization` header, so pointing either at a guarded document renders an
empty page and no explanation. The pages therefore fetch the document
themselves with the token attached and hand the renderer the parsed object
rather than a URL. The token lives in `sessionStorage`, so it dies with the tab
rather than lingering on a shared machine.

Both documents are filtered views of one generated schema, so they cannot
drift — there is no second description to maintain.

The admin routers are registered *in* the schema and the `/admin` paths are
stripped from the published document by an `app.openapi()` override. That is
deliberate, and the opposite of the obvious approach: `include_in_schema=False`
at registration hid the operator API from the public document *and* from the
operators, which is why nobody could find it. A contract test asserts the
guarantee that actually matters, independently of how it is achieved:

```python
async def test_admin_is_still_absent_from_the_public_document(client):
    schema = (await client.get("/openapi.json")).json()
    assert not [p for p in schema["paths"] if p.startswith("/admin")]
```

Publishing the operator surface at `api.faueofficial.com/docs` would hand anyone
who opened the address a map of the sign-in, MFA, invite and kill-switch flows.

### Health endpoints are documented, and tagged apart

`/`, `/healthz` and `/readyz` appear under an `operations` tag. They expose no
user data and need no token, and hiding them meant the generated reference —
the one place someone looks — was the one place they could not be found. The
tag keeps them out of the customer-facing list rather than out of the document.

---

## 2a. One token, every endpoint

The document declares a **global default** — `security: [{"bearerAuth": []}]` at
the root — so the rule is stated once rather than inferred from sixty-four
operations: this API is authenticated unless an operation says otherwise.

Under OpenAPI a root default is inherited by any operation that stays silent,
and sign-in is silent. So every operation that declares no requirement is given
an explicit empty one, and **no operation is left to inference**:

| | count |
|---|---|
| declare `bearerAuth` | 53 |
| declare `[]` (genuinely public) | 11 |
| silent | **0** |

The requirement is still derived from the handler's dependency — an operation is
secured because it declares a principal, never because a list says so. The root
default states the intent; the per-operation entry is what Swagger uses to
attach the token.

In the UI: press **Authorize**, paste the access token once, and it goes on
every request from that page. `persistAuthorization` keeps it across reloads,
so it is one paste per token rather than one per endpoint — without it Swagger
drops the credential on every refresh, which is how a request goes out with no
`Authorization` header at all and looks like a broken endpoint.

---

## 2b. The schemes themselves

Every guarded operation carries a `security` requirement, and the document
declares the schemes:

| Scheme | Used by | Credential |
|---|---|---|
| `bearerAuth` | the public document | user access token (JWT, short-lived) |
| `adminBearerAuth` | the admin document | admin session token (JWT, 8h, revocable) |

This was missing entirely, and it was not cosmetic. `current_user` read
`Authorization` through FastAPI's `Header()`, which works perfectly at runtime
and tells OpenAPI nothing — so the published document declared **no**
`securitySchemes` and **not one** of 61 operations declared `security`. Swagger
rendered no padlocks and no **Authorize** button, every endpoint read as public,
and a client generated from that document had no reason to send the token at
all. The guards were real the whole time; the contract simply did not say so.

Both schemes use `auto_error=False`, so FastAPI's own 403 never fires: a missing
credential is `401 unauthenticated` in this API's error model, and that taxonomy
is the contract. The scheme describes the door; it does not decide what happens
at it.

Each document advertises only the scheme its own operations use. Left unpruned,
the admin reference would render an Authorize box for the user token — inviting
someone to paste the wrong credential and conclude the API is broken when it is
correctly refused.

---

## 3. What the tests enforce

Publishing an undescribed schema produces a list of URLs. These run in both
services' suites:

| Test | Prevents |
|---|---|
| every endpoint has a summary | an operation rendered as a bare method and path |
| every endpoint has a description | a reader who cannot tell when to call it |
| every endpoint is tagged | 70+ operations in one flat list under "default" |
| every endpoint documents a success response | a 204 and an undescribed 200 looking identical to a generated client |
| admin paths absent | the operator console's surface in a document the app downloads |
| Scalar pins its bundle version | a CDN release changing the page on a service nobody deployed |

The description comes from the handler's docstring and the summary from its
name, so writing the endpoint is writing the documentation. There is no second
artefact to keep in sync — which is the only reason it stays in sync.

---

## 4. Unimplemented endpoints say so

Much of the surface is still a stub that raises `NotImplementedError`, which a
caller sees as a **500**.

Those operations remain in the schema — the paths, methods and tags are the
agreed contract and are worth building against. But each one opens with:

> **Planned — not yet implemented.** Calling it now returns 500.

Publishing a planned endpoint as though it works sends a client developer to
build against a 500. In ase every operation currently carries the marker, and a
test asserts it:

```python
async def test_unimplemented_endpoints_say_so(client):
    ...
    assert not undisclosed
```

When an endpoint is implemented, the marker comes off and the test narrows on
its own.

---

## 5. Relationship to `openapi/`

`30-contracts/openapi/*.yaml` are the **agreed** contracts — negotiated, and
what the services are supposed to implement. `/openapi.json` is what a service
**actually** serves.

They should match. Where they do not, the YAML wins and the service has a bug.

That is not hypothetical. Every ase route was mounted at `/internal/internal/…`
— the routers declared a `/internal` prefix and `create_app` added a second
one. `ase.internal.v1.yaml` said `/internal/looks/generate`, the code was wrong,
and nothing had called ase yet so nothing caught it. Generating the reference is
what made it visible, and a test now holds the paths to the contract.

---

## 6. Changing the Scalar version

Pinned in `app/docs.py`, in both services:

```python
SCALAR_VERSION = "1.68.0"
```

Not `@latest`. A floating CDN tag lets a Scalar release change — or break — the
documentation page of a service nobody deployed, with no commit to point at.
Bump it deliberately, in a commit, and check the page renders.
