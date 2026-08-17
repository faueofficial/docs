# Error Model

**Stage:** MVP

Every error response is an RFC 7807 problem document. Branch on `type`; never parse `title` or `detail`, which are human-facing and will be reworded without notice.

```json
{
  "type": "consent_required",
  "title": "Consent required",
  "status": 403,
  "detail": "The ai_processing purpose has not been granted.",
  "instance": "4bf92f3577b34da6a3ce929d0e0e4736",
  "errors": [{ "field": "ai_processing", "code": "not_granted", "message": "Required for look generation" }]
}
```

`instance` is the trace id. Show it in a support screen — it lets a backend engineer find the exact request, prompt version, and tool calls behind a user's complaint.

---

## 1. Codes

### Authentication and authorisation

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `unauthenticated` | 401 | Missing or invalid access token | Refresh once, then sign out |
| `token_expired` | 401 | Access token expired | Refresh, retry the original request |
| `refresh_reuse_detected` | 401 | A rotated refresh token was presented | **Sign out immediately.** Do not retry |
| `forbidden` | 403 | Authenticated but not permitted | Show a message; do not retry |
| `consent_required` | 403 | A consent purpose is not granted | Present the consent surface for `errors[0].field` |
| `age_restricted` | 403 | Under the minimum age | Terminal; explain, offer support contact |

### Magic link

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `link_expired` | 410 | Token past its 10-minute life | Offer to send a new link |
| `link_already_used` | 410 | Single-use token reused | Offer to send a new link |
| `device_code_required` | 409 | Opened on a different device | Show the returned code |
| `device_code_invalid` | 400 | Wrong code entered | Allow retry; lock after 5 attempts |

### Validation

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `validation_failed` | 422 | One or more fields invalid | Map `errors[].field` onto form fields |
| `username_taken` | 409 | Username in use | Inline error, suggest alternatives |
| `unsupported_media_type` | 415 | Not an accepted image type | Explain accepted formats |
| `payload_too_large` | 413 | Over 20 MB | Compress client-side and retry once |

### Resources

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `not_found` | 404 | Does not exist or is not visible to this user | Navigate back, refresh the list |
| `asset_not_ready` | 409 | Asset still in the PII pipeline | Poll `GET /uploads/{id}`, retry when `ready` |
| `asset_rejected` | 422 | Failed safety classification | Show the reason from `errors[0].code` |
| `conflict` | 409 | State changed underneath | Refetch and let the user retry |

### Generation

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `empty_pool` | 422 | Nothing available to build from | Suggest adding vault items or widening the occasion |
| `budget_exceeded` | 429 | Daily generation limit reached | Show when it resets; do not retry |
| `guardrail_blocked` | 422 | Input failed a safety guardrail | Show the templated message; do not retry the same input |
| `model_unavailable` | 503 | All models in the tier are down | Show the designed error state, offer Try Again |
| `render_failed` | 500 | Assembly succeeded, rendering did not | Look may still be viewable without its image |

### Infrastructure

| `type` | Status | Meaning | Client action |
|---|---|---|---|
| `rate_limited` | 429 | Too many requests | Honour `Retry-After`; back off |
| `internal_error` | 500 | Unexpected | Generic message with `instance`; retry once |
| `service_unavailable` | 503 | Dependency down | Retry with backoff |
| `maintenance` | 503 | Planned | Show the maintenance screen |

---

## 2. Retry policy

| Status | Retry? | How |
|---|---|---|
| 400, 403, 404, 409, 413, 415, 422 | No | The request is wrong; retrying changes nothing |
| 401 | Once, after refresh | Except `refresh_reuse_detected`, which is terminal |
| 429 | After `Retry-After` | Never sooner; never automatically more than once |
| 500, 502, 503, 504 | Yes, up to 3 | Exponential backoff with jitter: 1s, 3s, 9s |
| Network timeout | Yes, up to 3 | Same backoff |

Mutating requests that cost money or send messages carry an `Idempotency-Key`, so a retry cannot double-charge or double-send. Generate one UUID per user intent and reuse it across retries of that intent.

---

## 3. User-facing copy

Never show `detail` to a user. Map `type` to copy the product team owns.

| `type` | Copy |
|---|---|
| `consent_required` | *(no error — show the consent screen)* |
| `link_expired` | "That link has expired. We'll send a fresh one." |
| `link_already_used` | "That link has already been used. Want a new one?" |
| `empty_pool` | "We need a bit more to work with. Add a few pieces to your vault, or try a different occasion." |
| `budget_exceeded` | "You've reached today's generation limit. It resets at midnight." |
| `guardrail_blocked` | "We can't work with that image. Try a clear photo of the piece itself." |
| `model_unavailable` | "We couldn't create this look. Try adjusting your inputs or generate again." |
| `render_failed` | "We couldn't create this look. Try adjusting your inputs or generate again." |
| `asset_rejected` | "That photo didn't work. Make sure it shows the clothing clearly." |
| `rate_limited` | "Slow down a moment — try again shortly." |
| `internal_error` | "Something went wrong on our side. Please try again." |
| `service_unavailable` | "FAUE is having a moment. Try again in a few minutes." |

`model_unavailable` and `render_failed` share copy deliberately — the distinction matters to engineering, not to the user, and both resolve the same way.

**Consent is not an error.** A `403 consent_required` on a first generation is the expected path, and showing an error dialog there would be a bug. Present the consent screen instead.

---

## 4. Degraded states

Some failures should not surface as errors at all, because the product is designed to work without the failing part.

| Failure | Behaviour |
|---|---|
| Weather unavailable | Generate without it. No message. |
| Agent suggestion unavailable | Hide that dashboard section. No message. |
| Share card still rendering | Show a placeholder with a subtle loading state. |
| Reasoning text unavailable | Show the look without "Why this works". No message. |
| Pinterest sync failed | Badge on Connected Accounts, retry in background. |
| Analytics failing | Silent. Never block or surface. |

The rule: if the user did not ask for it, do not tell them it failed.

---

## 5. Offline

The client distinguishes *no connection* from *server error*, because the remedies differ.

- No connection → "You're offline" with cached content where available. See [`offline-and-caching.md`](offline-and-caching.md).
- Server unreachable but connection present → treat as `service_unavailable`.
- Request queued while offline → retry automatically on reconnect, once, with the same `Idempotency-Key`.

---

## 6. Reporting

Every error the user actually sees should be reportable in one tap, carrying `instance` (the trace id), `type`, the route, and the app version. That single string turns "generation failed for me yesterday" into a resolvable ticket.
