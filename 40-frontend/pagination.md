# Pagination

**Stage:** MVP

Cursor-based everywhere. No page numbers, no offsets.

---

## 1. Shape

```
GET /v1/vault/items?limit=20
```

```json
{
  "items": [ ... ],
  "next_cursor": "eyJpZCI6IjAxOTIuLi4iLCJ0cyI6MTc1NX0",
  "has_more": true
}
```

```
GET /v1/vault/items?limit=20&cursor=eyJpZCI6IjAxOTIuLi4iLCJ0cyI6MTc1NX0
```

The last page returns `next_cursor: null` and `has_more: false`.

---

## 2. Rules

- **Cursors are opaque.** Base64 today, something else tomorrow. Never decode, construct, or persist one beyond a session.
- **`limit`** defaults to 20, maximum 100. Ask for what fits the screen plus one screen of lookahead; larger pages mostly buy latency.
- **Filters must not change between pages.** Changing `category` or `occasion` mid-scroll invalidates the cursor — start over from no cursor.
- **Order is newest first** by creation time, tie-broken by id. UUIDv7 is time-sortable, so this is stable without a secondary sort column.
- **Stability:** items created during scrolling appear on refresh, not injected mid-scroll. Items deleted during scrolling are simply absent. Neither shifts a cursor, which is the reason for choosing cursors over offsets — with offsets, a deletion silently skips a row on the next page.

---

## 3. Paginated endpoints

| Endpoint | Default order | Filters |
|---|---|---|
| `GET /vault/items` | newest first | `category`, `q` |
| `GET /looks` | newest first | `filter` (recent/saved/all), `occasion` |
| `GET /notifications` | newest first | `category` |

---

## 4. Client pattern

```dart
class Paginated<T> {
  final List<T> items;
  final String? nextCursor;
  final bool hasMore;
  final bool isLoading;
}

Future<void> loadMore() async {
  if (state.isLoading || !state.hasMore) return;   // both guards matter
  state = state.copyWith(isLoading: true);
  final page = await api.getVaultItems(cursor: state.nextCursor, limit: 20);
  state = state.copyWith(
    items: [...state.items, ...page.items],
    nextCursor: page.nextCursor,
    hasMore: page.hasMore,
    isLoading: false,
  );
}
```

Trigger `loadMore` when the scroll position passes roughly 80% of the list — far enough ahead that the next page usually arrives before the user reaches the end.

### Pull to refresh

Discards the cursor and everything loaded, then fetches the first page fresh. Do not attempt to merge — reconciling a refreshed head against an existing tail produces duplicates and gaps for no benefit.

### Empty states

Distinguish three cases, because they need different copy:

| Case | Screen |
|---|---|
| No items at all | The designed empty state ("Build your wardrobe", "Nothing saved yet") |
| No items matching a filter | "Nothing in this category yet" with a clear-filter action |
| Failed to load | Error state with retry — never an empty state, which implies the user has nothing |

---

## 5. Errors

| Situation | Response | Client |
|---|---|---|
| Malformed or stale cursor | `400 validation_failed` | Discard the cursor, reload from the start |
| `limit` above 100 | `422` | Fix the request |
| Load-more fails | any 5xx | Keep loaded items, show an inline retry at the list foot, never clear the list |

A failed page-two load must never blank page one. That is the most common pagination bug and the most annoying one.
