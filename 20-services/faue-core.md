# faue-core

**Stage:** MVP · **Repo:** `faueofficial/faue-core`

Shared runtime library. Exists because four services need identical plumbing and copy-paste drifts — the second copy of an event publisher is where the outbox stops being reliable.

Also owns the shared dependency contract.

---

## 1. Layout

```
faue-core/
├─ faue_core/
│  ├─ events/       envelope.py outbox.py publisher.py consumer.py inprocess.py
│  ├─ telemetry/    otel.py logging.py scrub.py
│  ├─ crypto/       envelope.py blind_index.py signing.py
│  ├─ consent/      dependency.py purposes.py
│  ├─ errors/       taxonomy.py handlers.py problem.py
│  ├─ auth/         service_jwt.py
│  ├─ config/       settings.py
│  └─ health/       endpoints.py
├─ requirements/    base.in web.in worker.in ml.in dev.in constraints.txt
└─ tests/
```

---

## 2. events

```python
@dataclass(frozen=True)
class Event:
    event_id: UUID          # UUIDv7; consumers deduplicate on this
    name: str               # noun.past_tense_verb
    version: int
    occurred_at: datetime   # when the fact became true, not when published
    producer: str
    user_id: UUID | None
    trace_id: str
    payload: dict

class EventPublisher(Protocol):
    async def publish(self, event: Event, *, session: AsyncSession) -> None: ...
```

Two implementations selected by `EVENT_TRANSPORT`: `RabbitPublisher` (production, via outbox) and `InProcessPublisher` (local development, dispatches after commit). The interface is identical, so no service knows which is running.

### Outbox

```python
async def publish(self, event, *, session):
    session.add(OutboxRow.from_event(event))   # same transaction as the state change
    # a separate relay publishes and stamps published_at
```

Publishing requires a session. There is no API for publishing outside a transaction, which is what makes "state saved but event lost" structurally impossible rather than merely discouraged.

### Idempotent consumer

```python
class IdempotentConsumer:
    async def handle(self, event: Event) -> None:
        if await self._already_processed(event.event_id):
            return                                   # redelivery is normal
        async with self.uow() as session:
            await self._handler(event, session)
            await self._mark_processed(event.event_id, session)
```

Marking and handling share a transaction. Otherwise a crash between them causes a redelivery to be skipped, which is worse than processing twice.

---

## 3. telemetry

OpenTelemetry wiring, one `trace_id` from the Flutter client through gateway, `ase`, the model call, and back.

```python
setup_telemetry(service_name="api-gateway", otlp_endpoint=settings.otel_endpoint)
```

Instruments FastAPI, SQLAlchemy, HTTPX, and aio-pika automatically. Trace context propagates over HTTP headers and through event envelopes, so asynchronous work stays attached to the user action that caused it.

### PII-scrubbing logs

```python
logger.info("vault item added", item_id=item.id, user_id=user.id)   # fine
logger.info("user signed in", email=user.email)                     # BLOCKED
```

The scrubber redacts values for known-sensitive keys, and a CI check fails the build on PII-shaped log statements. It is blunt and it catches the mistake that actually happens.

---

## 4. crypto

```python
class EnvelopeEncryptor:
    def encrypt(self, plaintext: str) -> bytes: ...
    def decrypt(self, ciphertext: bytes) -> str: ...
    def rotate(self, ciphertext: bytes) -> bytes: ...   # re-wraps the data key only

def blind_index(value: str, pepper: bytes) -> str:
    return hmac_sha256(pepper, normalise(value)).hex()
```

Envelope encryption means master-key rotation re-encrypts data keys rather than rows — minutes rather than hours.

`normalise` lowercases and trims before hashing, so `Foo@Bar.com ` and `foo@bar.com` produce the same index. Getting that wrong makes login silently fail for a subset of users, which is a miserable bug to find.

### Signing keys

```python
def generate_keypair() -> tuple[str, str]:        # (private, public), base64url
def public_key_for(private_b64: str) -> str:      # derives the public half
def load_private_key(value: str) -> Ed25519PrivateKey: ...
def load_public_key(value: str) -> Ed25519PublicKey: ...
```

Ed25519 keys for user access tokens, encoded as **base64url of the 32 raw bytes on a single line** — not PEM. PEM is multi-line, and both `.env` files and Railway environment variables mangle embedded newlines badly enough that the value arrives corrupted and the error surfaces somewhere unrelated.

The format lives here rather than in either consumer because two repositories have to agree on it: `faue-infra`'s generator writes it and `api-gateway` reads it. Two implementations of one encoding drift, and the symptom is every access token failing to verify at once.

`generate_keypair` derives the public half from the private one rather than generating them side by side — an unrelated pair produces tokens that never verify, which reads as a configuration error rather than a generation bug.

---

## 5. consent

```python
def require_consent(*purposes: str) -> Callable:
    """FastAPI dependency. 403 consent_required naming the missing purpose."""
```

Used as a dependency rather than a call inside a handler, so a route that needs a purpose declares it in its signature and cannot forget it. The consent matrix in the API docs is generated from these declarations.

Purposes are an enum in `purposes.py` — a typo becomes an import error rather than a silently ungated endpoint.

---

## 6. errors

Domain exception taxonomy plus the RFC 7807 translation layer.

```python
class FaueError(Exception):
    problem_type: str
    status: int

class ConsentMissing(FaueError):   problem_type = "consent_required";  status = 403
class LinkExpired(FaueError):      problem_type = "link_expired";      status = 410
class BudgetExceeded(FaueError):   problem_type = "budget_exceeded";   status = 429
```

Modules raise domain exceptions; the handler translates once at the boundary. No module imports `HTTPException`, which is what keeps business logic callable from a worker as well as a request.

The `problem_type` values are the same strings documented in [`../40-frontend/error-model.md`](../40-frontend/error-model.md), so the contract cannot drift from the code.

---

## 7. auth

```python
def issue_service_token(audience: str, ttl: int = 300) -> str: ...
def verify_service_token(token: str, expected_audience: str) -> ServiceClaims: ...
```

Five-minute lifetime, audience-scoped. The audience check is what stops a user token from ever working on an internal endpoint even if one ended up in the wrong header.

---

## 8. config

```python
class BaseSettings(PydanticBaseSettings):
    service_name: str
    environment: Literal["local", "staging", "prod"]
    database_url: SecretStr
    redis_url: SecretStr
    otel_endpoint: str | None = None
```

Read once at startup. A missing required variable fails immediately and loudly, not on first use at 3 a.m. Services subclass this with their own fields.

---

## 9. health

```python
add_health_endpoints(app, checks=[postgres_check, redis_check, rabbit_check])
```

- `/healthz` — process alive. No dependency checks. Never fails for a downstream outage.
- `/readyz` — dependencies reachable. Failing removes the instance from rotation.
- `/metrics` — Prometheus.

The distinction matters: a gateway whose `ase` connection is down must stay in rotation and keep serving vault, saves, and profile. Conflating the two takes the whole product down for a partial outage.

---

## 10. Dependency contract

```
requirements/
├─ base.in         FastAPI, SQLAlchemy, Pydantic, OpenTelemetry, shared runtime
├─ web.in          uvicorn, HTTP-serving extras
├─ worker.in       arq, worker extras
├─ ml.in           ase only — open-clip, torch, pillow, pgvector extras
├─ dev.in          ruff, mypy, pytest, testcontainers
└─ constraints.txt shared pins; every service resolves against this
```

```bash
pip-compile --constraint requirements/constraints.txt requirements/base.in
```

Services declare their roles and never pin a shared library themselves. `constraints.txt` is what prevents two services resolving FastAPI to different versions — a class of bug that only appears at the integration boundary and is miserable to diagnose.

`ml` requirements install into `ase` only and must never enter the gateway image.

---

## 11. Versioning

Semantic, tagged, pinned by every service.

| Change | Bump |
|---|---|
| New helper or optional parameter | Minor |
| Bug fix | Patch |
| Interface change, removed helper, changed error semantics | **Major** |
| Dependency constraint change | Minor, or major if it forces a service upgrade |

Because every service pins an exact version, a major bump is a coordinated release. That is the intended friction — shared plumbing should be hard to change carelessly.
