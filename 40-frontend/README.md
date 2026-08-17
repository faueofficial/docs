# Frontend Handoff

**For:** the frontend engineer building `faue-app` (Flutter) and `faue-web` (Next.js)
**From:** backend · **Updated:** 2026-08-17

You should be able to build every screen without reading a backend document or running a backend service. If you cannot, that is a bug in this documentation — tell me and I will fix it.

---

## 1. Read in this order

| # | Document | Why |
|---|---|---|
| 1 | [`../00-product/mvp-scope.md`](../00-product/mvp-scope.md) | What is being built, and what is deliberately not |
| 2 | [`screens.md`](screens.md) | Every screen → route → endpoints → states, with the gaps listed |
| 3 | [`design-tokens.md`](design-tokens.md) | Colours, type, spacing, components, Flutter and Tailwind mappings |
| 4 | [`../30-contracts/openapi/gateway.v1.yaml`](../30-contracts/openapi/gateway.v1.yaml) | The API. Generate your client from this |
| 5 | [`auth-flows.md`](auth-flows.md) | Magic link, OAuth, session lifecycle |
| 6 | [`error-model.md`](error-model.md) | Error codes, retry policy, user-facing copy |
| 7 | [`realtime.md`](realtime.md) | Job progress for look generation |
| 8 | [`pagination.md`](pagination.md) · [`offline-and-caching.md`](offline-and-caching.md) · [`deeplinks.md`](deeplinks.md) | The rest of the integration detail |

Watch [`../30-contracts/CHANGELOG.md`](../30-contracts/CHANGELOG.md). Every contract change lands there before it lands in a service.

---

## 2. Getting started

```bash
# generate the Dio client
openapi-generator generate \
  -i docs/30-contracts/openapi/gateway.v1.yaml \
  -g dart-dio -o lib/api

# staging
BASE_URL=https://staging-api.faue.app/v1
```

Ask me for a staging test account. For any endpoint not yet built, send `X-Mock-Mode: true` and you will get recorded fixtures — build the screen now, switch the header off when the flow lands.

---

## 3. Seven things that will bite if you skip them

**1. Look generation is asynchronous.** `POST /looks/generate` returns `202` with a job envelope. Follow SSE at `stream_url` or poll `poll_url`. Expect 20–45 seconds. The "Building your fit… 70%" screen must show *real* progress from the server — a fake animation reads as broken the first time it stalls.

**2. `403 consent_required` is not an error.** It means the user has not granted a purpose, named in `errors[0].field`. Show the consent surface, not an error dialog. This is the expected path on a first generation.

**3. Magic links consume on POST, never GET.** The link opens a page; signing in requires an explicit action. If the link is opened on a different device you get `409` with a `device_code` — that is a normal flow that needs a screen.

**4. Quiz content comes from the API.** `GET /quiz` returns questions, options, and copy. **Question 6 has three options where the others have four** — build the layout from the response, never from a hardcoded four-card grid. Copy will change after review without an app release.

**5. Uploads go direct to the CDN.** `POST /uploads/sign` → upload → poll `GET /uploads/{asset_id}` until `status: ready`. The asset cannot be referenced by anything else until then, because it is passing PII redaction. `rejected` is a normal outcome with a reason.

**6. Tolerate unknown fields and enum values.** New occasions, new personas, and new statuses will be added within `v1`. A client that crashes on an unrecognised value blocks every future backend release.

**7. Percentages already total 100.** Style DNA percentages are computed with largest-remainder. No client-side rounding correction.

---

## 4. Design changes needed

From [`screens.md`](screens.md) §9. The first three block launch.

| Change | Status |
|---|---|
| **Magic-link screens** — check email, verify, cross-device code entry | **Blocking** — sign-in cannot complete without them |
| **AI processing consent surface** | **Blocking** — generation requires it |
| **Account deletion screen** | **Blocking** — App Store requires it given Sign in with Apple |
| Body profile capture (shape, height, fit, sizes) | Needed for recommendation quality |
| Location consent (city-level only) | Weather-aware suggestions |
| Notification preferences | Compliance |
| Wear logging | The agent has nothing to learn from without it |
| Web share pages (`/dna/:id`, `/look/:id`) | The viral loop breaks without them |
| **Remove the Instagram card** from Connected Accounts | The API cannot deliver what it promises |
| Style DNA answer options B–D | Content exists in [`../00-product/style-dna.md`](../00-product/style-dna.md), needs designing |
| Bottom nav uses `#613EEA` and SF Pro Text | Off-brand; should be `primary-500` and Plus Jakarta Sans |

---

## 5. Not your problem

Deliberately, so you do not build around them:

- Model calls, prompts, guardrails, rendering strategy.
- Style DNA scoring — submit answers, receive a result.
- Which items go in a look and why — the server decides and explains.
- Image redaction — server-side and mandatory; a client-side blur is a preview nicety, never a control.
- Event publishing, embeddings, ranking.

---

## 6. Asking

| Question | Where |
|---|---|
| "What does this endpoint return?" | `gateway.v1.yaml` |
| "What states does this screen need?" | `screens.md` |
| "What does this error code mean?" | `error-model.md` |
| "What colour is this?" | `design-tokens.md` |
| "Did something change?" | `CHANGELOG.md` |
| Anything not answered above | Ask me — and I will add it to these documents |

The last row matters. A question asked twice means a document is missing something, and the fix belongs here rather than in a chat thread that nobody can find in three months.
