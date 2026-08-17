# Realtime and Long-Running Jobs

**Stage:** MVP

Anything that can take longer than two seconds is a job, not a request. Look generation, fabric analysis, Pinterest import, card rendering, and data export all follow the same pattern.

The design's "Building your fit… 70%" screen is a product requirement: it must show real progress, not a spinner with a fake animation.

---

## 1. The job pattern

```
POST /looks/generate  →  202
{
  "job_id": "0192...",
  "status": "queued",
  "poll_url":   "/v1/looks/jobs/0192...",
  "stream_url": "/v1/looks/jobs/0192.../stream",
  "estimated_seconds": 30
}
```

Follow `stream_url` over SSE. Fall back to polling `poll_url` when SSE is unavailable or the connection drops repeatedly.

Progress is **server-side state**, so nothing is lost by disconnecting. A user can background the app mid-generation, return, and reattach to the same job.

---

## 2. States

| Status | Progress | Label (design copy) |
|---|---|---|
| `queued` | 0 | "Building your fit…" |
| `analyzing` | 10–30 | "Building your fit…" |
| `assembling` | 30–60 | "Creating your styles..." |
| `rendering` | 60–95 | "Creating your styles..." |
| `done` | 100 | — |
| `failed` | — | error state |

`done` and `failed` are terminal; the stream closes after either.

Take labels from the response rather than hardcoding them — copy will change, and the server knows which stage is actually running.

---

## 3. SSE

```
GET /v1/looks/jobs/{job_id}/stream
Accept: text/event-stream
Authorization: Bearer <access_token>
```

```
event: progress
data: {"status":"analyzing","progress":15,"label":"Building your fit…"}

event: progress
data: {"status":"rendering","progress":70,"label":"Creating your styles..."}

event: done
data: {"look_ids":["0192...","0193..."]}
```

```
event: failed
data: {"reason_code":"model_unavailable","message":"We couldn't create this look."}
```

A comment line (`: heartbeat`) arrives every 15 seconds to keep intermediaries from closing an idle connection.

### Client rules

- Reconnect at most 3 times with backoff (1s, 3s, 9s). After that, switch to polling and stay there for this job.
- Reattach on resume from background rather than starting a new job.
- Ignore unknown event names — new ones will be added.
- Never assume the stream is ordered relative to other jobs; each stream covers one job.
- Progress is monotonic within a job. If a lower value arrives, ignore it.

---

## 4. Polling fallback

```
GET /v1/looks/jobs/{job_id}   every 2 seconds
```

Stop on `done` or `failed`. Give up after 120 seconds and show the error state with a Try Again action — the job may still complete server-side, and the resulting look will appear in `/looks` if it does.

Poll only while the screen is visible. Polling from the background wastes battery on exactly the connections where it matters most.

---

## 5. Which endpoints are jobs

| Endpoint | Typical duration | Stream | Terminal event |
|---|---|---|---|
| `POST /looks/generate` | 20–45 s | yes | `look.completed` / `look.failed` |
| `POST /looks/{id}/regenerate` | 20–45 s | yes | same |
| `POST /looks/{id}/adjust` | 20–45 s | yes | same |
| `POST /vault/items/{id}/style` | 20–45 s | yes | same |
| `POST /integrations/pinterest/import` | 30 s – 5 min | no, poll | `integration.synced` |
| `POST /privacy/export` | minutes | no, poll | email when ready |
| `POST /uploads/sign` → processing | 2–10 s | no, poll `GET /uploads/{id}` | `status: ready` |
| `POST /quiz/submit` → card render | 3–10 s | no, poll `GET /quiz/card` | `status: ready` |

Fabric analysis (`POST /fabric/{asset_id}/style`) is **synchronous**, typically under 15 seconds. It returns the full result directly.

---

## 6. Perceived performance

Thirty to forty-five seconds is a long time to look at a progress bar. Things that help, in order of effect:

1. **Show real progress.** Users tolerate waiting far better when the number moves and the label changes. A bar that jumps 0 → 100 reads as broken even when it is faster.
2. **Let the wait be productive.** The building screen is a good place for the DNA card, a styling note, or the pieces being considered.
3. **Allow backgrounding.** The user should be able to leave and get a notification when the look is ready — `look.completed` already drives one.
4. **Never block the whole app.** The building screen is a route, not a modal over a frozen UI.
5. **Do not fake it.** If rendering stalls, the bar stalls. A bar that keeps moving while nothing happens destroys trust in every subsequent wait.

---

## 7. Cancellation

`M1-2`. Until then the building screen's back action abandons the UI but lets the job finish — the resulting look still appears in `/looks`, which is better than discarding paid-for work.

---

## 8. Testing

- Kill the network mid-stream → falls back to polling, then recovers.
- Background the app at 40% → returns to correct current progress, not a restart.
- Trigger `model_unavailable` → designed error state, Try Again works.
- Start two generations at once → two independent streams, no crossed progress.
- Slow 3G → heartbeats keep the connection alive; no spurious reconnect loop.
