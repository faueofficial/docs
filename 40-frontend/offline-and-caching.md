# Offline and Caching

**Stage:** MVP

FAUE's users are on Nigerian mobile networks. Connectivity is intermittent, data is metered, and a large image download at the wrong moment costs someone real money. The app should be useful on a bad connection and never surprising on a metered one.

---

## 1. What works offline

| Feature | Offline behaviour |
|---|---|
| Vault browsing | Full — items and thumbnails cached |
| Saved looks | Full — cached with images |
| Style DNA result | Full — cached including the card image |
| Profile | Full — cached |
| Notification inbox | Cached list; marking read queues |
| Look generation | **Unavailable.** Requires the server. Clear message, no queue |
| Fabric analysis | **Unavailable.** Same |
| Spree | **Unavailable.** Same |
| Adding a vault item | **Queued.** Photo stored locally, uploaded on reconnect |
| Wear logging | **Queued.** Applied on reconnect |
| Feedback and saves | **Queued.** Applied on reconnect |

Generation is deliberately not queued. A look generated from stale context hours later, arriving unprompted, is worse than an honest "you need a connection for this".

---

## 2. Cache policy

| Data | TTL | Strategy |
|---|---|---|
| `GET /me` | 5 min | Stale-while-revalidate |
| `GET /quiz` definition | 24 h | Cache-first; changes rarely |
| `GET /quiz/result` | until retake | Cache-first |
| `GET /vault/items` | 10 min | Stale-while-revalidate |
| `GET /looks` | 5 min | Stale-while-revalidate |
| `GET /looks/{id}` | 1 h | Cache-first — a generated look is immutable |
| `GET /notifications` | 2 min | Network-first, cache fallback |
| `GET /integrations` | 5 min | Stale-while-revalidate |
| `GET /agent/today` | until midnight local | Cache-first |
| Images | 30 days | Cache-first, LRU eviction |

**Stale-while-revalidate** is the default for lists: show cached content immediately, fetch in the background, update in place. The app should never show a blank screen for data it already has.

---

## 3. Images

The heaviest cost on a metered connection, so they get explicit treatment.

- Request sized variants, never full resolution for a thumbnail. The CDN supports width parameters; a vault grid thumbnail at 200 px is roughly a twentieth of the full asset.
- Cache on disk with an LRU budget of about 200 MB, evicting oldest first.
- Show a low-quality placeholder or a dominant-colour block while loading rather than a grey box — perceived speed matters more than actual speed here.
- **Never prefetch generated look images on a metered connection** unless the user opted in. A background prefetch of ten renders is megabytes someone paid for.
- Vault thumbnails are prefetched, because the user photographed those and expects them instantly.

---

## 4. The write queue

Queued actions persist across app restarts and survive being killed.

```
queue entry: { id, endpoint, method, body, idempotency_key, created_at, attempts }
```

Rules:

- Every entry carries an `Idempotency-Key` generated when the user acted, not when the request is sent, so a retry after a crash cannot duplicate.
- Process in order on reconnect. One failure does not block the rest unless entries depend on each other — a vault item upload must precede a wear log referencing it.
- Give up after 5 attempts and surface the failure with a retry action. Silent permanent failure is worse than an error.
- Show the queue depth somewhere unobtrusive when non-zero: "3 changes waiting to sync."
- Clear the queue on logout, since it belongs to that account.

Optimistic updates apply immediately in the UI and roll back visibly if the eventual request fails. Rolling back silently makes users think the app is lying to them.

---

## 5. Connectivity detection

Three states, not two:

| State | Meaning | Behaviour |
|---|---|---|
| Online | Requests succeeding | Normal |
| Offline | No network interface | Offline banner, cached content, queue writes |
| Degraded | Network present, requests timing out | Treat as offline for writes, keep retrying reads |

The degraded case is the common one on mobile data and the one naive apps handle worst — a captive portal or a stalled connection looks online to the OS while nothing actually completes. Base the decision on request outcomes, not only on the connectivity API.

---

## 6. Data saver

A user-facing toggle in settings, on by default for users on metered connections:

- No image prefetch
- Lower-resolution image variants
- No background sync
- Generation still permitted — it is what the user came for — but the render is fetched at reduced resolution first

---

## 7. Storage budget

| Store | Budget | Eviction |
|---|---|---|
| Image cache | 200 MB | LRU |
| API response cache | 20 MB | TTL then LRU |
| Write queue | 50 MB | Never evicted; it is user intent |
| Pending upload photos | 100 MB | Deleted after successful upload |

Show total usage in settings with a clear-cache action. Clearing never touches the write queue.

---

## 8. Testing

- Airplane mode → vault and saved looks browse normally, generation shows an honest message.
- Add a vault item offline, reconnect → uploads exactly once.
- Kill the app with a queued write, relaunch → the write still happens, once.
- Simulate 2G with high latency → stale-while-revalidate shows cached content immediately.
- Captive portal → detected as degraded, not online.
- Fill the image cache past budget → oldest evicted, no crash.
