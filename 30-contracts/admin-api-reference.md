# FAUE admin API reference (v1)

> Generated from the OpenAPI contract by `tools/build_reference.py`. Do not edit by hand.

The operations console's API. A separate auth realm from the public API. Read [app-developer-guide.md](app-developer-guide.md#12-the-admin-api) for how it signs in.

**Base URL:** `https://api.faueofficial.com/admin/v1`

## Contents

- [admin-auth](#admin-auth) (10)
- [admin-ops](#admin-ops) (3)
- [admin-console](#admin-console) (4)
- [admin-contact](#admin-contact) (4)
- [admin-waitlist](#admin-waitlist) (8)
- [admin-integrations](#admin-integrations) (3)
- [admin-lifecycle](#admin-lifecycle) (1)
- [admin-settings](#admin-settings) (3)
- [admin-flags](#admin-flags) (2)
- [admin-media](#admin-media) (2)
- [admin-privacy](#admin-privacy) (6)

## admin-auth

Magic link, then TOTP. Two factors from genuinely different places.

### `POST /auth/link/request`

**Request a sign-in link**

Always `202`, whatever the address. Which addresses hold admin accounts
is precisely the list an attacker wants before choosing who to phish, so
the response cannot depend on it.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string (email) | yes |  |

```json
{
  "email": "ada@example.com"
}
```

**Responses**

- **202**: Link dispatched if the address belongs to an active admin.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `expires_in` | integer |  |  |

```json
{
  "expires_in": 600
}
```

- **429**: Admin sign-in is the highest-value endpoint in the system and is limited far more tightly than the user flow — a stolen link plus a brute-forced six-digit code is only 10^6 attempts.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/link/consume`

**Complete sign-in with the link and a TOTP code**

Both factors are checked before either is spent, so a mistyped code does
**not** burn the link — otherwise every typo costs a fresh email.

A code cannot be replayed. TOTP codes stay valid for roughly 90 seconds
including drift allowance, and used codes are held for that span.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `token` | string | yes |  |
| `code` | string | yes | Six digits from the authenticator. |

```json
{
  "token": "string",
  "code": "318204"
}
```

**Responses**

- **200**: Signed in

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes |  |
| `expires_in` | integer | yes | Eight hours, absolute. Never renewed by activity. |
| `role` | `viewer` / `curator` / `support` / `ml_ops` / `admin` | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 28800,
  "role": "viewer"
}
```

- **401**: Link expired or already used.
- **403**: Wrong or already-used code. The link is still valid.
- **428**: Account has not completed MFA enrolment. Not a refusal — the body carries an enrolment token, and the console shows the QR flow.
  - body: `application/problem+json`, see *Errors* in the guide
- **429**: Admin sign-in is the highest-value endpoint in the system and is limited far more tightly than the user flow — a stolen link plus a brute-forced six-digit code is only 10^6 attempts.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/mfa/enrol`

**Begin MFA enrolment**

Authorised by an enrolment token rather than a session: a new admin has
no session yet, and the link they clicked already proved inbox control.

`provisioning_uri` contains the secret. Show it once as a QR code; never
log it, never re-display it. An already-enrolled account cannot re-enrol
itself — a live session could otherwise swap the second factor for one
an attacker controls.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `enrolment_token` | string | yes |  |

```json
{
  "enrolment_token": "string"
}
```

**Responses**

- **200**: Secret issued. Enrolment is not complete until confirmed.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `secret` | string | yes |  |
| `provisioning_uri` | string | yes |  |

```json
{
  "secret": "string",
  "provisioning_uri": "otpauth://totp/FAUE:ada%40faueofficial.com?secret=...&issuer=FAUE"
}
```

- **401**: Enrolment token expired or already spent.
- **403**: Already enrolled.

### `POST /auth/mfa/confirm`

**Confirm MFA enrolment**

`mfa_enrolled` flips here, not when the secret was issued. A stored
secret only proves one was generated; if the operator never successfully
scanned it, treating them as enrolled locks them out permanently.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `enrolment_token` | string | yes |  |
| `code` | string | yes |  |

```json
{
  "enrolment_token": "string",
  "code": "string"
}
```

**Responses**

- **204**: Enrolled. The enrolment token is now spent.
- **401**: Enrolment token expired or already spent.
- **403**: That code did not match.

### `GET /auth/sessions`

**List live sessions**

Every live session on this account, newest first.

`current` marks the session making the call — without it you cannot tell
which row is the device in your hand, and ending the wrong one signs you
out.

The raw user-agent is never stored; `device` is a coarse label, which is
enough to answer "is one of these not me?" without keeping a
fingerprint.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `sessions` | array of object | yes |  |
| `sessions[]` | object |  |  |
| `sessions[].jti` | string | yes | Pass to DELETE /auth/sessions/{jti} to end it. |
| `sessions[].created_at` | string (date-time) | yes |  |
| `sessions[].expires_at` | string (date-time) | yes |  |
| `sessions[].ip` | string or null |  |  |
| `sessions[].device` | string | yes | Coarse by design. The raw user-agent is a fingerprint and is not stored. |
| `sessions[].current` | boolean | yes | The session making this call. Ending it signs you out. |

```json
{
  "sessions": [
    {
      "jti": "string",
      "created_at": "2026-10-13T09:30:00Z",
      "expires_at": "2026-10-13T09:30:00Z",
      "ip": "string",
      "device": "Chrome on macOS",
      "current": true
    }
  ]
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide

### `DELETE /auth/sessions/{jti}`

**End one session**

The lever people actually need: not "end everything", but "end that
session on the laptop I left at the office".

Only your own. The storage key is namespaced by account, so another
account's session id is not there and returns `404` — the same as an
unknown or already-ended session, which an operator on a stale screen
should learn about rather than be told it worked.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `jti` | path | string | yes |  |

**Responses**

- **204**: Session ended. That device stops working immediately.
- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such session on this account.

### `POST /auth/logout`

**End this session**

Scoped to the session making the call. Signing out of a laptop must not
sign you out of a phone — anything broader and people stop signing out.

**Auth:** bearer token

**Responses**

- **204**: Session ended. The token stops working immediately.
- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/sessions/revoke`

**End every session this account holds**

The lever for a lost device. A timestamp cutoff rather than a list —
sessions cannot be enumerated, and the point is reaching the ones nobody
knows about. Includes the session making the call.

A cutoff, not a ban: signing in again works. A permanent block is
`status = 'suspended'`, a different decision.

**Auth:** bearer token

**Responses**

- **204**: All sessions ended.
- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /admins/invite`

**Invite an admin**

`Capability: role.write` — admin only. Granting a role is effectively
granting everything that role can reach.

Creates the account but **not** access: `status = 'invited'` cannot sign
in until MFA enrolment activates it. An invite that produced a usable
account would make a forwarded email an admin account.

Invites last three days and are single-use.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string (email) | yes |  |
| `role` | `viewer` / `curator` / `support` / `ml_ops` / `admin` | yes |  |

```json
{
  "email": "ada@example.com",
  "role": "viewer"
}
```

**Responses**

- **201**: Invited

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `invited` |  |  |
| `role` | string |  |  |

```json
{
  "status": "invited",
  "role": "string"
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **409**: That address already has an admin account.
- **422**: Unknown role.

### `POST /auth/invite/accept`

**Accept an invitation**

Unauthenticated by necessity — the invitee has no session yet, and the
token in the mail is the credential. Single-use, so a forwarded invite
is spent rather than live.

Returns an enrolment token; enrolment then follows the same two calls as
any other account, and confirming it activates the account.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `invite_token` | string | yes |  |

```json
{
  "invite_token": "string"
}
```

**Responses**

- **200**: Invite accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `enrolment_token` | string | yes |  |

```json
{
  "enrolment_token": "string"
}
```

- **401**: Invite expired or already used.
- **429**: Admin sign-in is the highest-value endpoint in the system and is limited far more tightly than the user flow — a stolen link plus a brute-forced six-digit code is only 10^6 attempts.
  - body: `application/problem+json`, see *Errors* in the guide

## admin-ops

Health, queues and delivery outcomes.

### `GET /ops/health`

**Per-dependency health**

`Capability: ops.read`

Not a boolean. Which dependency is down decides what to do next, and a
single flag collapses "the API is serving but Redis is down" into the
same value as "everything is fine".

`partial` is the state that matters: requests are being served while
something behind them is not.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `degraded` | boolean | yes |  |
| `checked_at` | string (date-time) | yes |  |
| `dependencies` | object | yes |  |
| `dependencies.<key>` | object |  |  |
| `failing` | array of string | yes |  |

```json
{
  "status": "success",
  "degraded": true,
  "checked_at": "2026-10-13T09:30:00Z",
  "dependencies": {
    "<key>": {
      "status": "success",
      "latency_ms": 0,
      "reason": "string"
    }
  },
  "failing": [
    "string"
  ]
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /ops/events`

**Event backlog**

`Capability: ops.read_queues`

`unpublished` and `parked` are different problems. Unpublished means the
relay is behind and usually catches up on its own. Parked means those
events exist and **no consumer will ever see them** without someone
intervening — an incident, not a queue depth.

Parked rows are named individually, because a count does not say which
handler to fix.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `unpublished` | integer | yes | Still retryable — the relay is behind. |
| `parked` | integer | yes | Attempts exhausted. Nothing will publish these without intervention. |
| `oldest_unpublished_at` | string or null (date-time) | yes |  |
| `unpublished_by_event` | object |  |  |
| `unpublished_by_event.<key>` | integer |  |  |
| `parked_events` | array of object |  |  |
| `parked_events[]` | object |  |  |
| `parked_events[].event_id` | string (uuid) | yes |  |
| `parked_events[].event_name` | string | yes |  |
| `parked_events[].attempts` | integer | yes |  |
| `parked_events[].occurred_at` | string (date-time) | yes |  |

```json
{
  "status": "success",
  "unpublished": 0,
  "parked": 0,
  "oldest_unpublished_at": "2026-10-13T09:30:00Z",
  "unpublished_by_event": {
    "<key>": 0
  },
  "parked_events": [
    {
      "event_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "event_name": "look.failed",
      "attempts": 0,
      "occurred_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /ops/notifications`

**Delivery outcomes**

`Capability: ops.read_queues`

"Notifications are broken" is not actionable. "62 suppressed for
`no_consent`, 3 failed on `provider_unavailable`" says which of those is
a bug and which is the system working — suppression usually is, which is
why it reads as `partial` rather than `failure`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `hours` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `window_hours` | integer | yes |  |
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `by_status` | object | yes |  |
| `by_status.<key>` | integer |  |  |
| `by_failure_reason` | object | yes |  |
| `by_failure_reason.<key>` | integer |  |  |
| `by_channel` | array of object |  |  |
| `by_channel[]` | object |  |  |
| `by_channel[].channel` | string |  |  |
| `by_channel[].status` | string |  |  |
| `by_channel[].count` | integer |  |  |

```json
{
  "window_hours": 0,
  "status": "success",
  "by_status": {
    "sent": 412,
    "suppressed": 62,
    "failed": 3
  },
  "by_failure_reason": {
    "no_consent": 62,
    "provider_unavailable": 3
  },
  "by_channel": [
    {
      "channel": "string",
      "status": "string",
      "count": 0
    }
  ]
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

## admin-console

Who is signed in, the overview numbers, the audit log and the team.

### `GET /me`

**Who is signed in, and what they may do**

The console calls this first. `capabilities` is the list the role holds, so the console can show
only the pages the role can open. The API enforces every capability regardless.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `role` | `viewer` / `curator` / `support` / `ml_ops` / `admin` | yes |  |
| `capabilities` | array of string | yes |  |
| `session_expires_at` | string (date-time) | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "role": "viewer",
  "capabilities": [
    "ops.read",
    "contact.read",
    "contact.write"
  ],
  "session_expires_at": "2026-10-13T09:30:00Z"
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /overview`

**The numbers on the console's front page**

`Capability: ops.read`. Counts and 30 day series, no personal data. A section the role cannot read
(`waitlist` needs `waitlist.read`, `contact` needs `contact.read`) is `null`.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `generated_at` | string (date-time) | yes |  |
| `waitlist` | object | yes | Null without `waitlist.read`. |
| `waitlist.total` | integer |  |  |
| `waitlist.by_status` | object |  | Keys: waiting, invited, joined, unsubscribed. |
| `waitlist.by_status.<key>` | integer |  |  |
| `waitlist.by_dominant` | object |  | Persona id to count. |
| `waitlist.by_dominant.<key>` | integer |  |  |
| `waitlist.by_gender` | object |  | female, male, prefer_not_to_say, not_given. |
| `waitlist.by_gender.<key>` | integer |  |  |
| `waitlist.first_joined_at` | string or null (date-time) |  |  |
| `waitlist.daily` | array of object |  | Exactly 30 entries, oldest first, zeros included. |
| `waitlist.daily[]` | object |  |  |
| `waitlist.daily[].date` | string (date) | yes |  |
| `waitlist.daily[].count` | integer | yes |  |
| `waitlist.welcomed` | integer |  | Members whose confirmation email went out. |
| `contact` | object | yes | Null without `contact.read`. |
| `contact.counts` | object |  | Keys: new, replied, closed. |
| `contact.counts.<key>` | integer |  |  |
| `contact.by_topic` | object |  |  |
| `contact.by_topic.<key>` | integer |  |  |
| `contact.daily` | array of object |  |  |
| `contact.daily[]` | object |  |  |
| `contact.daily[].date` | string (date) | yes |  |
| `contact.daily[].count` | integer | yes |  |
| `contact.oldest_unanswered_at` | string or null (date-time) |  |  |
| `accounts` | object | yes |  |
| `accounts.total` | integer |  |  |
| `accounts.quiz_completed` | integer |  |  |
| `accounts.by_dominant` | object |  |  |
| `accounts.by_dominant.<key>` | integer |  |  |
| `delivery` | object | yes |  |
| `delivery.last_24h` | object |  | Notification outcome to count: sent, suppressed, failed. |
| `delivery.last_24h.<key>` | integer |  |  |
| `delivery.unpublished_events` | integer |  |  |

```json
{
  "generated_at": "2026-10-13T09:30:00Z",
  "waitlist": {
    "total": 0,
    "by_status": {
      "<key>": 0
    },
    "by_dominant": {
      "<key>": 0
    },
    "by_gender": {
      "<key>": 0
    },
    "first_joined_at": "2026-10-13T09:30:00Z",
    "daily": [
      {
        "date": "string",
        "count": 0
      }
    ],
    "welcomed": 0
  },
  "contact": {
    "counts": {
      "<key>": 0
    },
    "by_topic": {
      "<key>": 0
    },
    "daily": [
      {
        "date": "string",
        "count": 0
      }
    ],
    "oldest_unanswered_at": "2026-10-13T09:30:00Z"
  },
  "accounts": {
    "total": 0,
    "quiz_completed": 0,
    "by_dominant": {
      "<key>": 0
    }
  },
  "delivery": {
    "last_24h": {
      "<key>": 0
    },
    "unpublished_events": 0
  }
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /audit`

**The audit log**

`Capability: audit.read` (admin role). Newest first. Entries hold the action, the target and a few
non-personal facts. Message text and email addresses are never written to the log.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `action` | query | string |  | An action, or the start of one: `waitlist`, `contact.replied`. |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].action` | string | yes |  |
| `items[].occurred_at` | string (date-time) | yes |  |
| `items[].actor` | object | yes |  |
| `items[].actor.id` | string (uuid) |  |  |
| `items[].actor.role` | string |  |  |
| `items[].actor.email` | string or null |  |  |
| `items[].target` | object | yes |  |
| `items[].target.type` | string |  |  |
| `items[].target.id` | string or null (uuid) |  |  |
| `items[].before` | object or null |  |  |
| `items[].after` | object or null |  |  |
| `items[].ip` | string or null |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "action": "waitlist.status_changed",
      "occurred_at": "2026-10-13T09:30:00Z",
      "actor": {
        "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
        "role": "string",
        "email": "string"
      },
      "target": {
        "type": "waitlist_entry",
        "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
      },
      "before": {},
      "after": {},
      "ip": "string"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /admins`

**Everyone with a console account**

`Capability: role.write` (admin role). Whether MFA is set up, never the factor itself.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].email` | string | yes |  |
| `items[].role` | string | yes |  |
| `items[].status` | `invited` / `active` / `suspended` | yes |  |
| `items[].mfa_enrolled` | boolean | yes |  |
| `items[].last_login_at` | string or null (date-time) |  |  |
| `items[].created_at` | string (date-time) | yes |  |
| `roles` | array of string | yes | Roles an invitation may name. |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "email": "string",
      "role": "string",
      "status": "invited",
      "mfa_enrolled": true,
      "last_login_at": "2026-10-13T09:30:00Z",
      "created_at": "2026-10-13T09:30:00Z"
    }
  ],
  "roles": [
    "string"
  ]
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

## admin-contact

Website messages: read, mark and reply.

### `GET /contact/messages`

**List website messages**

`Capability: contact.read`. Newest first, with a one-line preview. `counts` are for the whole inbox,
not the page. Opening the list is audited (that it happened, never the text).

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | `new` / `replied` / `closed` |  |  |
| `topic` | query | `support` / `data_request` / `press_partnership` / `other` |  |  |
| `before` | query | string (date-time) |  | Pass `next_before` from the previous page. |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].reference` | string | yes |  |
| `items[].topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `items[].topic_label` | string | yes |  |
| `items[].status` | `new` / `replied` / `closed` | yes |  |
| `items[].partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].replied_at` | string or null (date-time) |  |  |
| `items[].purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `items[].name` | string or null |  |  |
| `items[].email` | string or null |  |  |
| `items[].snippet` | string or null |  | First 140 characters, whitespace collapsed. |
| `next_before` | string or null (date-time) | yes |  |
| `counts` | object | yes |  |
| `counts.new` | integer |  |  |
| `counts.replied` | integer |  |  |
| `counts.closed` | integer |  |  |
| `counts.purged` | integer |  |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "reference": "FAUE-7K4M2Q",
      "topic": "support",
      "topic_label": "Support and complaints",
      "status": "new",
      "partner_type": "tailor",
      "created_at": "2026-10-13T09:30:00Z",
      "replied_at": "2026-10-13T09:30:00Z",
      "purged": true,
      "name": "string",
      "email": "string",
      "snippet": "string"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "counts": {
    "new": 0,
    "replied": 0,
    "closed": 0,
    "purged": 0
  }
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /contact/messages/{message_id}`

**Read one message**

`Capability: contact.read`. Audited. A message past its 72 hour retention has `purged: true` and no text or address.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `message_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `reference` | string | yes |  |
| `topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `topic_label` | string | yes |  |
| `status` | `new` / `replied` / `closed` | yes |  |
| `partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `created_at` | string (date-time) | yes |  |
| `replied_at` | string or null (date-time) |  |  |
| `purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `name` | string or null |  |  |
| `email` | string or null |  |  |
| `snippet` | string or null |  | First 140 characters, whitespace collapsed. |
| `message` | string or null |  |  |
| `organisation` | string or null |  |  |
| `role` | string or null |  |  |
| `partner_type_label` | string or null |  |  |
| `reference_code` | string or null |  |  |
| `linked_account` | boolean |  |  |
| `policy_version` | string |  |  |
| `notified_at` | string or null (date-time) |  |  |
| `handled_by` | string or null (uuid) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "reference": "FAUE-7K4M2Q",
  "topic": "support",
  "topic_label": "Support and complaints",
  "status": "new",
  "partner_type": "tailor",
  "created_at": "2026-10-13T09:30:00Z",
  "replied_at": "2026-10-13T09:30:00Z",
  "purged": true,
  "name": "string",
  "email": "string",
  "snippet": "string",
  "message": "string",
  "organisation": "string",
  "role": "string",
  "partner_type_label": "string",
  "reference_code": "string",
  "linked_account": true,
  "policy_version": "string",
  "notified_at": "2026-10-13T09:30:00Z",
  "handled_by": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
}
```

- **404**: No such message

### `PATCH /contact/messages/{message_id}`

**Mark a message**

`Capability: contact.write`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `message_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `new` / `replied` / `closed` | yes |  |

```json
{
  "status": "new"
}
```

**Responses**

- **200**: The message

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `reference` | string | yes |  |
| `topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `topic_label` | string | yes |  |
| `status` | `new` / `replied` / `closed` | yes |  |
| `partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `created_at` | string (date-time) | yes |  |
| `replied_at` | string or null (date-time) |  |  |
| `purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `name` | string or null |  |  |
| `email` | string or null |  |  |
| `snippet` | string or null |  | First 140 characters, whitespace collapsed. |
| `message` | string or null |  |  |
| `organisation` | string or null |  |  |
| `role` | string or null |  |  |
| `partner_type_label` | string or null |  |  |
| `reference_code` | string or null |  |  |
| `linked_account` | boolean |  |  |
| `policy_version` | string |  |  |
| `notified_at` | string or null (date-time) |  |  |
| `handled_by` | string or null (uuid) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "reference": "FAUE-7K4M2Q",
  "topic": "support",
  "topic_label": "Support and complaints",
  "status": "new",
  "partner_type": "tailor",
  "created_at": "2026-10-13T09:30:00Z",
  "replied_at": "2026-10-13T09:30:00Z",
  "purged": true,
  "name": "string",
  "email": "string",
  "snippet": "string",
  "message": "string",
  "organisation": "string",
  "role": "string",
  "partner_type_label": "string",
  "reference_code": "string",
  "linked_account": true,
  "policy_version": "string",
  "notified_at": "2026-10-13T09:30:00Z",
  "handled_by": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
}
```

- **404**: No such message
- **422**: Unknown status

### `POST /contact/messages/{message_id}/reply`

**Reply to a message by email**

`Capability: contact.write`. Emails the person from the FAUE team, with their own message quoted
underneath, and marks the message `replied`. Replies to it come back to the team mailbox for the
topic. Nothing is saved if sending fails. The reply text is not stored and not written to the audit log.

Refused with **409** once the message is past retention, because there is no address left.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `message_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `body` | string | yes |  |

```json
{
  "body": "string"
}
```

**Responses**

- **200**: Sent

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `replied` | yes |  |
| `reference` | string | yes |  |

```json
{
  "status": "replied",
  "reference": "FAUE-7K4M2Q"
}
```

- **409**: Past retention, or the provider failed. Nothing was marked.
- **404**: No such message

## admin-waitlist

Early-access members: read, invite, write to, mark as left, delete.

### `GET /waitlist`

**List waitlist members**

`Capability: waitlist.read`. Newest first. Search by exact email address or by the start of a username.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | `waiting` / `invited` / `joined` / `unsubscribed` |  |  |
| `dominant` | query | string |  | Dominant Style DNA persona id. |
| `q` | query | string |  |  |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].username` | string | yes |  |
| `items[].email` | string | yes |  |
| `items[].status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `items[].dna` | object | yes |  |
| `items[].dna.dominant` | string |  |  |
| `items[].dna.alter_ego` | string or null |  |  |
| `items[].dna.wildcard` | string or null |  |  |
| `items[].linked` | boolean | yes | Has an account with the same email address. |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].welcomed_at` | string or null (date-time) |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "username": "string",
      "email": "string",
      "status": "waiting",
      "dna": {
        "dominant": "CM",
        "alter_ego": "string",
        "wildcard": "string"
      },
      "linked": true,
      "created_at": "2026-10-13T09:30:00Z",
      "welcomed_at": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /waitlist/summary`

**Waitlist totals**

`Capability: waitlist.read`. Totals only, no personal data.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `total` | integer | yes |  |
| `by_status` | object | yes |  |
| `by_status.<key>` | integer |  |  |
| `by_dominant` | object | yes |  |
| `by_dominant.<key>` | integer |  |  |
| `first_joined_at` | string or null (date-time) | yes |  |

```json
{
  "total": 0,
  "by_status": {
    "<key>": 0
  },
  "by_dominant": {
    "<key>": 0
  },
  "first_joined_at": "2026-10-13T09:30:00Z"
}
```


### `GET /waitlist/{entry_id}`

**One member, with their quiz answers and scores**

`Capability: waitlist.read`. Audited.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `entry_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `username` | string | yes |  |
| `email` | string | yes |  |
| `status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `dna` | object | yes |  |
| `dna.dominant` | string |  |  |
| `dna.alter_ego` | string or null |  |  |
| `dna.wildcard` | string or null |  |  |
| `linked` | boolean | yes | Has an account with the same email address. |
| `created_at` | string (date-time) | yes |  |
| `welcomed_at` | string or null (date-time) |  |  |
| `answers` | object |  |  |
| `answers.<key>` | string or array |  |  |
| `scores` | object |  | Raw persona scores. Percentages are recomputed from these. |
| `scores.<key>` | integer |  |  |
| `quiz_version` | string |  |  |
| `policy_version` | string |  |  |
| `consented_at` | string (date-time) |  |  |
| `source` | string |  |  |
| `gender` | `female` / `male` / `prefer_not_to_say` / null |  |  |
| `invited_at` | string or null (date-time) |  |  |
| `unsubscribed_at` | string or null (date-time) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "email": "string",
  "status": "waiting",
  "dna": {
    "dominant": "CM",
    "alter_ego": "string",
    "wildcard": "string"
  },
  "linked": true,
  "created_at": "2026-10-13T09:30:00Z",
  "welcomed_at": "2026-10-13T09:30:00Z",
  "answers": {
    "<key>": "string"
  },
  "scores": {
    "<key>": 0
  },
  "quiz_version": "string",
  "policy_version": "string",
  "consented_at": "2026-10-13T09:30:00Z",
  "source": "web_quiz",
  "gender": "female",
  "invited_at": "2026-10-13T09:30:00Z",
  "unsubscribed_at": "2026-10-13T09:30:00Z"
}
```

- **404**: No such member

### `PATCH /waitlist/{entry_id}`

**Change a member's status**

`Capability: waitlist.write`. Setting `invited` **sends the launch email** ("FAUE is open"), once;
setting it again does not email twice. If the email fails the status is not changed. A member who
has unsubscribed cannot be invited (**409**). `unsubscribed` stops all email and releases the username.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `entry_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `waiting` / `invited` / `unsubscribed` | yes |  |

```json
{
  "status": "waiting"
}
```

**Responses**

- **200**: The member

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `username` | string | yes |  |
| `email` | string | yes |  |
| `status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `dna` | object | yes |  |
| `dna.dominant` | string |  |  |
| `dna.alter_ego` | string or null |  |  |
| `dna.wildcard` | string or null |  |  |
| `linked` | boolean | yes | Has an account with the same email address. |
| `created_at` | string (date-time) | yes |  |
| `welcomed_at` | string or null (date-time) |  |  |
| `answers` | object |  |  |
| `answers.<key>` | string or array |  |  |
| `scores` | object |  | Raw persona scores. Percentages are recomputed from these. |
| `scores.<key>` | integer |  |  |
| `quiz_version` | string |  |  |
| `policy_version` | string |  |  |
| `consented_at` | string (date-time) |  |  |
| `source` | string |  |  |
| `gender` | `female` / `male` / `prefer_not_to_say` / null |  |  |
| `invited_at` | string or null (date-time) |  |  |
| `unsubscribed_at` | string or null (date-time) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "email": "string",
  "status": "waiting",
  "dna": {
    "dominant": "CM",
    "alter_ego": "string",
    "wildcard": "string"
  },
  "linked": true,
  "created_at": "2026-10-13T09:30:00Z",
  "welcomed_at": "2026-10-13T09:30:00Z",
  "answers": {
    "<key>": "string"
  },
  "scores": {
    "<key>": 0
  },
  "quiz_version": "string",
  "policy_version": "string",
  "consented_at": "2026-10-13T09:30:00Z",
  "source": "web_quiz",
  "gender": "female",
  "invited_at": "2026-10-13T09:30:00Z",
  "unsubscribed_at": "2026-10-13T09:30:00Z"
}
```

- **409**: Unsubscribed members cannot be invited
- **404**: No such member

### `DELETE /waitlist/{entry_id}`

**Remove a member and delete their data**

`Capability: waitlist.write`. Emails the person a short confirmation, then deletes the address,
username and quiz answers. Audited as `waitlist.deleted` (the entry's id, never what was deleted).

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `entry_id` | path | string (uuid) | yes |  |

**Responses**

- **204**: Deleted
- **404**: No such member

### `POST /waitlist/{entry_id}/message`

**Write to one member**

`Capability: waitlist.write`. One person at a time, on purpose. Refused for anyone who unsubscribed
(**409**). The text is not stored or copied into the audit log, only that a message of that length
was sent. A subject containing a line break is refused (**422**).

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `entry_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `subject` | string | yes |  |
| `body` | string | yes |  |

```json
{
  "subject": "string",
  "body": "string"
}
```

**Responses**

- **200**: Sent

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `sent` |  |  |

```json
{
  "status": "sent"
}
```

- **409**: The member unsubscribed
- **422**: Invalid subject or body

### `POST /waitlist/invite-batch`

**Invite the next people on the list**

`Capability: waitlist.write`. Sends the launch invite to the next `limit` (1 to 50) members
who are still `waiting`, oldest first, optionally only one dominant style. Never selects
anyone invited, joined or unsubscribed. Each person is committed on their own, so a
provider failure part way leaves the ones already sent invited. `dry_run` only counts.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `limit` | integer |  |  |
| `dominant` | string |  |  |
| `dry_run` | boolean |  |  |

```json
{
  "limit": 0,
  "dominant": "string",
  "dry_run": true
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `selected` | integer |  |  |
| `invited` | integer |  |  |
| `failed` | integer |  |  |
| `dry_run` | boolean |  |  |
| `still_waiting` | integer |  |  |

```json
{
  "selected": 0,
  "invited": 0,
  "failed": 0,
  "dry_run": true,
  "still_waiting": 0
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /waitlist/export.csv`

**Export the waitlist as CSV**

`Capability: user.export`. Email, username, status, styles, gender and dates. `reason` (10 to
300 characters) is required and is kept in the audit log with the row count. Members who
unsubscribed are left out unless `status=unsubscribed` is asked for. Cells that begin with
`=`, `+`, `-` or `@` are prefixed so a spreadsheet does not run them.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `reason` | query | string | yes |  |
| `status` | query | `waiting` / `invited` / `joined` / `unsubscribed` |  |  |

**Responses**

- **200**: CSV

  Body (`text/csv`):

```json
"string"
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **422**: Reason missing or too short

## admin-integrations

Connected accounts and the pins imported through them.

### `GET /integrations`

**Connected accounts**

`Capability: integration.read`. Newest connection first. Tokens are never returned. Audited. `summary` counts the whole set.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | `active` / `syncing` / `needs_reauth` / `revoked` |  |  |
| `provider` | query | `pinterest` |  |  |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].user_id` | string (uuid) | yes |  |
| `items[].provider` | `pinterest` | yes |  |
| `items[].status` | `active` / `syncing` / `needs_reauth` / `revoked` | yes |  |
| `items[].scopes` | array of string | yes |  |
| `items[].connected_at` | string (date-time) | yes |  |
| `items[].last_sync_at` | string or null (date-time) |  |  |
| `items[].token_expires_at` | string or null (date-time) |  |  |
| `items[].boards_imported` | integer | yes |  |
| `items[].pins_imported` | integer | yes |  |
| `next_before` | string or null (date-time) | yes |  |
| `summary` | object | yes |  |
| `summary.by_status` | object | yes |  |
| `summary.by_status.<key>` | integer |  |  |
| `summary.connected` | integer | yes |  |
| `summary.pins_imported` | integer | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "provider": "pinterest",
      "status": "active",
      "scopes": [
        "string"
      ],
      "connected_at": "2026-10-13T09:30:00Z",
      "last_sync_at": "2026-10-13T09:30:00Z",
      "token_expires_at": "2026-10-13T09:30:00Z",
      "boards_imported": 0,
      "pins_imported": 0
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "summary": {
    "by_status": {
      "active": 12,
      "needs_reauth": 1
    },
    "connected": 0,
    "pins_imported": 0
  }
}
```

- **401**: Missing, invalid, or expired admin session — including a valid *user* token.
  - body: `application/problem+json`, see *Errors* in the guide
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /integrations/{account_id}/pins`

**Pins imported through one connection**

`Capability: integration.read_pins`. Newest first, with the boards they came from. Titles and descriptions are text written by strangers on Pinterest: render as plain text. Audited.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `account_id` | path | string (uuid) | yes |  |
| `board_id` | query | string |  |  |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `account` | object | yes |  |
| `account.id` | string (uuid) | yes |  |
| `account.user_id` | string (uuid) | yes |  |
| `account.provider` | `pinterest` | yes |  |
| `account.status` | `active` / `syncing` / `needs_reauth` / `revoked` | yes |  |
| `account.scopes` | array of string | yes |  |
| `account.connected_at` | string (date-time) | yes |  |
| `account.last_sync_at` | string or null (date-time) |  |  |
| `account.token_expires_at` | string or null (date-time) |  |  |
| `account.boards_imported` | integer | yes |  |
| `account.pins_imported` | integer | yes |  |
| `boards` | array of object | yes |  |
| `boards[]` | object |  |  |
| `boards[].board_id` | string | yes |  |
| `boards[].name` | string | yes |  |
| `boards[].pins` | integer | yes |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].pin_id` | string | yes |  |
| `items[].board_id` | string | yes |  |
| `items[].board_name` | string | yes |  |
| `items[].title` | string or null |  | Untrusted text. Render as plain text. |
| `items[].description` | string or null |  | Untrusted text. Render as plain text. |
| `items[].image_url` | string or null |  | A Pinterest CDN address (i.pinimg.com). |
| `items[].image_status` | `none` / `pending_detector` / `cached` / `rejected` / `failed` | yes |  |
| `items[].imported_at` | string (date-time) | yes |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "account": {
    "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "provider": "pinterest",
    "status": "active",
    "scopes": [
      "string"
    ],
    "connected_at": "2026-10-13T09:30:00Z",
    "last_sync_at": "2026-10-13T09:30:00Z",
    "token_expires_at": "2026-10-13T09:30:00Z",
    "boards_imported": 0,
    "pins_imported": 0
  },
  "boards": [
    {
      "board_id": "string",
      "name": "string",
      "pins": 0
    }
  ],
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "pin_id": "string",
      "board_id": "string",
      "board_name": "string",
      "title": "string",
      "description": "string",
      "image_url": "string",
      "image_status": "none",
      "imported_at": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such connected account

### `DELETE /integrations/{account_id}`

**Disconnect on the person's behalf**

`Capability: integration.write`. Deletes the stored token and every pin imported through it. The person is not notified. Audited.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `account_id` | path | string (uuid) | yes |  |

**Responses**

- **204**: Disconnected
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such connected account

## admin-lifecycle

Lifecycle campaigns: state and results.

### `GET /lifecycle/overview`

**Campaigns, state and results**

`Capability: ops.read`. Whether campaigns are on (`lifecycle_enabled` under Settings), how many people agreed to marketing, and for each message what was sent and opened in the last 30 days. Counts only.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):



- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

## admin-settings

Tunable, non-secret values: thresholds, limits and clean-up periods.

### `GET /settings`

**Tunable settings**

`Capability: settings.read`. Each with its type, bounds, default and what is in force. Secrets, keys and addresses are not tunable and are not listed.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):



- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `PUT /settings/{key}`

**Change a setting**

`Capability: settings.write`. Checked against the type and bounds in the list (`422` outside them); a reason of at least 5 characters is required and audited. Takes effect within about ten seconds; workers pick it up on their next pass.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `key` | path | string | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `value` | object | yes | A number or a boolean |
| `reason` | string | yes |  |

```json
{
  "value": null,
  "reason": "string"
}
```

**Responses**

- **200**: The setting after the change
- **404**: Not a tunable setting
- **422**: Wrong type or outside the bounds

### `DELETE /settings/{key}`

**Return a setting to its default**

`Capability: settings.write`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `key` | path | string | yes |  |

**Responses**

- **200**: The setting at its default
- **404**: Not a tunable setting

## admin-flags

Feature switches: pause a feature without a deploy.

### `GET /flags`

**Feature switches**

`Capability: flags.read`. Every switch with its default, current value and who last changed it. `enabled: true` means the feature is working.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):



- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `PUT /flags/{key}`

**Turn a switch off or on**

`Capability: flags.write`. Keys: `service` (whole product API into maintenance), `uploads`,
`pinterest`, `shares`, `waitlist_signups`. A paused feature answers `503`. Takes effect
within about ten seconds on every instance. A reason of at least 5 characters is
required and is written to the audit log.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `key` | path | string | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `enabled` | boolean | yes |  |
| `reason` | string | yes |  |

```json
{
  "enabled": true,
  "reason": "string"
}
```

**Responses**

- **200**: The switch after the change
- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such switch

## admin-media

Uploads, storage, backup and sharing, as counts.

### `GET /media/overview`

**Uploads and storage**

`Capability: media.read`. Counts only: what is stored and refused, where, whether the backup is keeping up, and what the clean-up has left. No image, key or address.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):



- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /sharing/overview`

**Sharing, in and out**

`Capability: media.read`. `to_faue` counts looks shared to FAUE by source; `from_faue` counts cards shared out by kind and surface, and shared links opened (which includes chat link previews).

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):



- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

## admin-privacy

Deletion requests, and accounts: reveal an address, delete an account.

### `GET /privacy/requests`

**Deletion requests**

`Capability: deletion_ledger.read`. The deletion ledger. Unfinished requests come soonest deadline first. `scheduled` is inside the waiting period: the account is signed out but nothing has been removed and it can be cancelled. `summary` counts the whole ledger.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `state` | query | `scheduled` / `open` / `overdue` / `completed` / `cancelled` |  |  |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].user_id` | string (uuid) | yes | The account that was deleted. |
| `items[].state` | `scheduled` / `open` / `overdue` / `completed` / `cancelled` | yes |  |
| `items[].requested_at` | string (date-time) | yes |  |
| `items[].purge_after` | string or null (date-time) |  | When the data is removed. |
| `items[].sla_due_at` | string (date-time) | yes |  |
| `items[].completed_at` | string or null (date-time) |  |  |
| `items[].cancelled_at` | string or null (date-time) |  |  |
| `items[].days_left` | integer or null |  | Negative when overdue. Null once completed. |
| `items[].modules_pending` | array of string | yes | Modules that have not confirmed yet. |
| `items[].modules_done` | array of string | yes |  |
| `items[].third_parties_done` | array of string | yes |  |
| `next_before` | string or null (date-time) | yes |  |
| `summary` | object | yes |  |
| `summary.scheduled` | integer | yes |  |
| `summary.open` | integer | yes |  |
| `summary.overdue` | integer | yes |  |
| `summary.due_within_5_days` | integer | yes |  |
| `summary.completed` | integer | yes |  |
| `summary.cancelled` | integer | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "state": "scheduled",
      "requested_at": "2026-10-13T09:30:00Z",
      "purge_after": "2026-10-13T09:30:00Z",
      "sla_due_at": "2026-10-13T09:30:00Z",
      "completed_at": "2026-10-13T09:30:00Z",
      "cancelled_at": "2026-10-13T09:30:00Z",
      "days_left": 0,
      "modules_pending": [
        "string"
      ],
      "modules_done": [
        "string"
      ],
      "third_parties_done": [
        "string"
      ]
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "summary": {
    "scheduled": 0,
    "open": 0,
    "overdue": 0,
    "due_within_5_days": 0,
    "completed": 0,
    "cancelled": 0
  }
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /privacy/requests/{ledger_id}/acknowledge`

**Record a module as purged**

`Capability: deletion_ledger.write`. Verify first (see the DSR runbook). The note is kept in the audit log. The request closes when every module has been recorded. `409` for a module that is not part of the request.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `ledger_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `module` | string | yes |  |
| `note` | string | yes |  |

```json
{
  "module": "ase",
  "note": "string"
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `user_id` | string (uuid) | yes | The account that was deleted. |
| `state` | `scheduled` / `open` / `overdue` / `completed` / `cancelled` | yes |  |
| `requested_at` | string (date-time) | yes |  |
| `purge_after` | string or null (date-time) |  | When the data is removed. |
| `sla_due_at` | string (date-time) | yes |  |
| `completed_at` | string or null (date-time) |  |  |
| `cancelled_at` | string or null (date-time) |  |  |
| `days_left` | integer or null |  | Negative when overdue. Null once completed. |
| `modules_pending` | array of string | yes | Modules that have not confirmed yet. |
| `modules_done` | array of string | yes |  |
| `third_parties_done` | array of string | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "state": "scheduled",
  "requested_at": "2026-10-13T09:30:00Z",
  "purge_after": "2026-10-13T09:30:00Z",
  "sla_due_at": "2026-10-13T09:30:00Z",
  "completed_at": "2026-10-13T09:30:00Z",
  "cancelled_at": "2026-10-13T09:30:00Z",
  "days_left": 0,
  "modules_pending": [
    "string"
  ],
  "modules_done": [
    "string"
  ],
  "third_parties_done": [
    "string"
  ]
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such request
- **409**: The module is not part of this request

### `GET /accounts`

**Accounts**

`Capability: user.read`. Newest first. Addresses are masked. `q` is the start of a username, or a full email address. Audited.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `q` | query | string |  |  |
| `before` | query | string (date-time) |  |  |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].username` | string or null |  |  |
| `items[].email_masked` | string or null |  |  |
| `items[].status` | string | yes |  |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].quiz_completed` | boolean | yes |  |
| `items[].restricted` | boolean | yes | The person restricted processing. |
| `items[].integrations` | array of string | yes |  |
| `items[].deletion_scheduled` | boolean |  | Waiting out the deletion period. |
| `items[].purge_after` | string or null (date-time) |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "username": "string",
      "email_masked": "a***@e***.com",
      "status": "string",
      "created_at": "2026-10-13T09:30:00Z",
      "quiz_completed": true,
      "restricted": true,
      "integrations": [
        "string"
      ],
      "deletion_scheduled": true,
      "purge_after": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /accounts/{user_id}/reveal`

**Reveal an account's email address**

`Capability: user.read_pii`. A reason of at least 10 characters is required and is stored in the audit log.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `user_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `justification` | string | yes |  |

```json
{
  "justification": "string"
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string | yes |  |

```json
{
  "email": "string"
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such account
- **422**: Reason missing or too short

### `POST /accounts/{user_id}/delete`

**Schedule an account for deletion**

`Capability: user.delete`. The same as the person's own request: sessions end at once and the data
is removed after the waiting period, during which `restore` undoes it. `immediate: true` removes it
at the next purge pass instead and cannot then be undone. Idempotent while a request is open. A
reason of at least 10 characters is required and is stored in the audit log.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `user_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `justification` | string | yes |  |
| `immediate` | boolean |  |  |

```json
{
  "justification": "string",
  "immediate": true
}
```

**Responses**

- **202**: Scheduled

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `ledger_id` | string (uuid) | yes |  |
| `sla_due_at` | string (date-time) | yes |  |
| `purge_after` | string or null (date-time) |  |  |

```json
{
  "ledger_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "sla_due_at": "2026-10-13T09:30:00Z",
  "purge_after": "2026-10-13T09:30:00Z"
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: No such account
- **422**: Reason missing or too short

### `POST /accounts/{user_id}/restore`

**Cancel a scheduled deletion**

`Capability: user.delete`. Only before the data is removed (`409` after). The person signs in as normal. A reason is required and audited.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `user_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `justification` | string | yes |  |

```json
{
  "justification": "string"
}
```

**Responses**

- **200**: Restored

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `restored` |  |  |

```json
{
  "status": "restored"
}
```

- **403**: The role lacks the capability. The message names the capability, because "forbidden" tells an operator nothing about what to grant.
  - body: `application/problem+json`, see *Errors* in the guide
- **409**: Nothing waiting

## Schemas

### Me

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `role` | `viewer` / `curator` / `support` / `ml_ops` / `admin` | yes |  |
| `capabilities` | array of string | yes |  |
| `session_expires_at` | string (date-time) | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "role": "viewer",
  "capabilities": [
    "ops.read",
    "contact.read",
    "contact.write"
  ],
  "session_expires_at": "2026-10-13T09:30:00Z"
}
```

### DayCount

| Field | Type | Required | Notes |
|---|---|---|---|
| `date` | string (date) | yes |  |
| `count` | integer | yes |  |

```json
{
  "date": "string",
  "count": 0
}
```

### WaitlistStatus

```json
"waiting"
```

### ContactStatus

```json
"new"
```

### ContactTopic

```json
"support"
```

### Overview

| Field | Type | Required | Notes |
|---|---|---|---|
| `generated_at` | string (date-time) | yes |  |
| `waitlist` | object | yes | Null without `waitlist.read`. |
| `waitlist.total` | integer |  |  |
| `waitlist.by_status` | object |  | Keys: waiting, invited, joined, unsubscribed. |
| `waitlist.by_status.<key>` | integer |  |  |
| `waitlist.by_dominant` | object |  | Persona id to count. |
| `waitlist.by_dominant.<key>` | integer |  |  |
| `waitlist.by_gender` | object |  | female, male, prefer_not_to_say, not_given. |
| `waitlist.by_gender.<key>` | integer |  |  |
| `waitlist.first_joined_at` | string or null (date-time) |  |  |
| `waitlist.daily` | array of object |  | Exactly 30 entries, oldest first, zeros included. |
| `waitlist.daily[]` | object |  |  |
| `waitlist.daily[].date` | string (date) | yes |  |
| `waitlist.daily[].count` | integer | yes |  |
| `waitlist.welcomed` | integer |  | Members whose confirmation email went out. |
| `contact` | object | yes | Null without `contact.read`. |
| `contact.counts` | object |  | Keys: new, replied, closed. |
| `contact.counts.<key>` | integer |  |  |
| `contact.by_topic` | object |  |  |
| `contact.by_topic.<key>` | integer |  |  |
| `contact.daily` | array of object |  |  |
| `contact.daily[]` | object |  |  |
| `contact.daily[].date` | string (date) | yes |  |
| `contact.daily[].count` | integer | yes |  |
| `contact.oldest_unanswered_at` | string or null (date-time) |  |  |
| `accounts` | object | yes |  |
| `accounts.total` | integer |  |  |
| `accounts.quiz_completed` | integer |  |  |
| `accounts.by_dominant` | object |  |  |
| `accounts.by_dominant.<key>` | integer |  |  |
| `delivery` | object | yes |  |
| `delivery.last_24h` | object |  | Notification outcome to count: sent, suppressed, failed. |
| `delivery.last_24h.<key>` | integer |  |  |
| `delivery.unpublished_events` | integer |  |  |

```json
{
  "generated_at": "2026-10-13T09:30:00Z",
  "waitlist": {
    "total": 0,
    "by_status": {
      "<key>": 0
    },
    "by_dominant": {
      "<key>": 0
    },
    "by_gender": {
      "<key>": 0
    },
    "first_joined_at": "2026-10-13T09:30:00Z",
    "daily": [
      {
        "date": "string",
        "count": 0
      }
    ],
    "welcomed": 0
  },
  "contact": {
    "counts": {
      "<key>": 0
    },
    "by_topic": {
      "<key>": 0
    },
    "daily": [
      {
        "date": "string",
        "count": 0
      }
    ],
    "oldest_unanswered_at": "2026-10-13T09:30:00Z"
  },
  "accounts": {
    "total": 0,
    "quiz_completed": 0,
    "by_dominant": {
      "<key>": 0
    }
  },
  "delivery": {
    "last_24h": {
      "<key>": 0
    },
    "unpublished_events": 0
  }
}
```

### AuditEntry

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `action` | string | yes |  |
| `occurred_at` | string (date-time) | yes |  |
| `actor` | object | yes |  |
| `actor.id` | string (uuid) |  |  |
| `actor.role` | string |  |  |
| `actor.email` | string or null |  |  |
| `target` | object | yes |  |
| `target.type` | string |  |  |
| `target.id` | string or null (uuid) |  |  |
| `before` | object or null |  |  |
| `after` | object or null |  |  |
| `ip` | string or null |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "action": "waitlist.status_changed",
  "occurred_at": "2026-10-13T09:30:00Z",
  "actor": {
    "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "role": "string",
    "email": "string"
  },
  "target": {
    "type": "waitlist_entry",
    "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
  },
  "before": {},
  "after": {},
  "ip": "string"
}
```

### AuditList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].action` | string | yes |  |
| `items[].occurred_at` | string (date-time) | yes |  |
| `items[].actor` | object | yes |  |
| `items[].actor.id` | string (uuid) |  |  |
| `items[].actor.role` | string |  |  |
| `items[].actor.email` | string or null |  |  |
| `items[].target` | object | yes |  |
| `items[].target.type` | string |  |  |
| `items[].target.id` | string or null (uuid) |  |  |
| `items[].before` | object or null |  |  |
| `items[].after` | object or null |  |  |
| `items[].ip` | string or null |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "action": "waitlist.status_changed",
      "occurred_at": "2026-10-13T09:30:00Z",
      "actor": {
        "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
        "role": "string",
        "email": "string"
      },
      "target": {
        "type": "waitlist_entry",
        "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
      },
      "before": {},
      "after": {},
      "ip": "string"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

### TeamMember

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `email` | string | yes |  |
| `role` | string | yes |  |
| `status` | `invited` / `active` / `suspended` | yes |  |
| `mfa_enrolled` | boolean | yes |  |
| `last_login_at` | string or null (date-time) |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "email": "string",
  "role": "string",
  "status": "invited",
  "mfa_enrolled": true,
  "last_login_at": "2026-10-13T09:30:00Z",
  "created_at": "2026-10-13T09:30:00Z"
}
```

### Team

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].email` | string | yes |  |
| `items[].role` | string | yes |  |
| `items[].status` | `invited` / `active` / `suspended` | yes |  |
| `items[].mfa_enrolled` | boolean | yes |  |
| `items[].last_login_at` | string or null (date-time) |  |  |
| `items[].created_at` | string (date-time) | yes |  |
| `roles` | array of string | yes | Roles an invitation may name. |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "email": "string",
      "role": "string",
      "status": "invited",
      "mfa_enrolled": true,
      "last_login_at": "2026-10-13T09:30:00Z",
      "created_at": "2026-10-13T09:30:00Z"
    }
  ],
  "roles": [
    "string"
  ]
}
```

### ContactSummary

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `reference` | string | yes |  |
| `topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `topic_label` | string | yes |  |
| `status` | `new` / `replied` / `closed` | yes |  |
| `partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `created_at` | string (date-time) | yes |  |
| `replied_at` | string or null (date-time) |  |  |
| `purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `name` | string or null |  |  |
| `email` | string or null |  |  |
| `snippet` | string or null |  | First 140 characters, whitespace collapsed. |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "reference": "FAUE-7K4M2Q",
  "topic": "support",
  "topic_label": "Support and complaints",
  "status": "new",
  "partner_type": "tailor",
  "created_at": "2026-10-13T09:30:00Z",
  "replied_at": "2026-10-13T09:30:00Z",
  "purged": true,
  "name": "string",
  "email": "string",
  "snippet": "string"
}
```

### ContactDetail

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `reference` | string | yes |  |
| `topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `topic_label` | string | yes |  |
| `status` | `new` / `replied` / `closed` | yes |  |
| `partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `created_at` | string (date-time) | yes |  |
| `replied_at` | string or null (date-time) |  |  |
| `purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `name` | string or null |  |  |
| `email` | string or null |  |  |
| `snippet` | string or null |  | First 140 characters, whitespace collapsed. |
| `message` | string or null |  |  |
| `organisation` | string or null |  |  |
| `role` | string or null |  |  |
| `partner_type_label` | string or null |  |  |
| `reference_code` | string or null |  |  |
| `linked_account` | boolean |  |  |
| `policy_version` | string |  |  |
| `notified_at` | string or null (date-time) |  |  |
| `handled_by` | string or null (uuid) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "reference": "FAUE-7K4M2Q",
  "topic": "support",
  "topic_label": "Support and complaints",
  "status": "new",
  "partner_type": "tailor",
  "created_at": "2026-10-13T09:30:00Z",
  "replied_at": "2026-10-13T09:30:00Z",
  "purged": true,
  "name": "string",
  "email": "string",
  "snippet": "string",
  "message": "string",
  "organisation": "string",
  "role": "string",
  "partner_type_label": "string",
  "reference_code": "string",
  "linked_account": true,
  "policy_version": "string",
  "notified_at": "2026-10-13T09:30:00Z",
  "handled_by": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
}
```

### ContactList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].reference` | string | yes |  |
| `items[].topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `items[].topic_label` | string | yes |  |
| `items[].status` | `new` / `replied` / `closed` | yes |  |
| `items[].partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` / null |  |  |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].replied_at` | string or null (date-time) |  |  |
| `items[].purged` | boolean | yes | True once the 72 hour retention has deleted the text and sender. |
| `items[].name` | string or null |  |  |
| `items[].email` | string or null |  |  |
| `items[].snippet` | string or null |  | First 140 characters, whitespace collapsed. |
| `next_before` | string or null (date-time) | yes |  |
| `counts` | object | yes |  |
| `counts.new` | integer |  |  |
| `counts.replied` | integer |  |  |
| `counts.closed` | integer |  |  |
| `counts.purged` | integer |  |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "reference": "FAUE-7K4M2Q",
      "topic": "support",
      "topic_label": "Support and complaints",
      "status": "new",
      "partner_type": "tailor",
      "created_at": "2026-10-13T09:30:00Z",
      "replied_at": "2026-10-13T09:30:00Z",
      "purged": true,
      "name": "string",
      "email": "string",
      "snippet": "string"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "counts": {
    "new": 0,
    "replied": 0,
    "closed": 0,
    "purged": 0
  }
}
```

### WaitlistMember

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `username` | string | yes |  |
| `email` | string | yes |  |
| `status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `dna` | object | yes |  |
| `dna.dominant` | string |  |  |
| `dna.alter_ego` | string or null |  |  |
| `dna.wildcard` | string or null |  |  |
| `linked` | boolean | yes | Has an account with the same email address. |
| `created_at` | string (date-time) | yes |  |
| `welcomed_at` | string or null (date-time) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "email": "string",
  "status": "waiting",
  "dna": {
    "dominant": "CM",
    "alter_ego": "string",
    "wildcard": "string"
  },
  "linked": true,
  "created_at": "2026-10-13T09:30:00Z",
  "welcomed_at": "2026-10-13T09:30:00Z"
}
```

### WaitlistDetail

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `username` | string | yes |  |
| `email` | string | yes |  |
| `status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `dna` | object | yes |  |
| `dna.dominant` | string |  |  |
| `dna.alter_ego` | string or null |  |  |
| `dna.wildcard` | string or null |  |  |
| `linked` | boolean | yes | Has an account with the same email address. |
| `created_at` | string (date-time) | yes |  |
| `welcomed_at` | string or null (date-time) |  |  |
| `answers` | object |  |  |
| `answers.<key>` | string or array |  |  |
| `scores` | object |  | Raw persona scores. Percentages are recomputed from these. |
| `scores.<key>` | integer |  |  |
| `quiz_version` | string |  |  |
| `policy_version` | string |  |  |
| `consented_at` | string (date-time) |  |  |
| `source` | string |  |  |
| `gender` | `female` / `male` / `prefer_not_to_say` / null |  |  |
| `invited_at` | string or null (date-time) |  |  |
| `unsubscribed_at` | string or null (date-time) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "email": "string",
  "status": "waiting",
  "dna": {
    "dominant": "CM",
    "alter_ego": "string",
    "wildcard": "string"
  },
  "linked": true,
  "created_at": "2026-10-13T09:30:00Z",
  "welcomed_at": "2026-10-13T09:30:00Z",
  "answers": {
    "<key>": "string"
  },
  "scores": {
    "<key>": 0
  },
  "quiz_version": "string",
  "policy_version": "string",
  "consented_at": "2026-10-13T09:30:00Z",
  "source": "web_quiz",
  "gender": "female",
  "invited_at": "2026-10-13T09:30:00Z",
  "unsubscribed_at": "2026-10-13T09:30:00Z"
}
```

### WaitlistList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].username` | string | yes |  |
| `items[].email` | string | yes |  |
| `items[].status` | `waiting` / `invited` / `joined` / `unsubscribed` | yes |  |
| `items[].dna` | object | yes |  |
| `items[].dna.dominant` | string |  |  |
| `items[].dna.alter_ego` | string or null |  |  |
| `items[].dna.wildcard` | string or null |  |  |
| `items[].linked` | boolean | yes | Has an account with the same email address. |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].welcomed_at` | string or null (date-time) |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "username": "string",
      "email": "string",
      "status": "waiting",
      "dna": {
        "dominant": "CM",
        "alter_ego": "string",
        "wildcard": "string"
      },
      "linked": true,
      "created_at": "2026-10-13T09:30:00Z",
      "welcomed_at": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

### WaitlistSummary

| Field | Type | Required | Notes |
|---|---|---|---|
| `total` | integer | yes |  |
| `by_status` | object | yes |  |
| `by_status.<key>` | integer |  |  |
| `by_dominant` | object | yes |  |
| `by_dominant.<key>` | integer |  |  |
| `first_joined_at` | string or null (date-time) | yes |  |

```json
{
  "total": 0,
  "by_status": {
    "<key>": 0
  },
  "by_dominant": {
    "<key>": 0
  },
  "first_joined_at": "2026-10-13T09:30:00Z"
}
```

### AdminSessionRow

| Field | Type | Required | Notes |
|---|---|---|---|
| `jti` | string | yes | Pass to DELETE /auth/sessions/{jti} to end it. |
| `created_at` | string (date-time) | yes |  |
| `expires_at` | string (date-time) | yes |  |
| `ip` | string or null |  |  |
| `device` | string | yes | Coarse by design. The raw user-agent is a fingerprint and is not stored. |
| `current` | boolean | yes | The session making this call. Ending it signs you out. |

```json
{
  "jti": "string",
  "created_at": "2026-10-13T09:30:00Z",
  "expires_at": "2026-10-13T09:30:00Z",
  "ip": "string",
  "device": "Chrome on macOS",
  "current": true
}
```

### AdminSession

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes |  |
| `expires_in` | integer | yes | Eight hours, absolute. Never renewed by activity. |
| `role` | `viewer` / `curator` / `support` / `ml_ops` / `admin` | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 28800,
  "role": "viewer"
}
```

### EnrolmentRequired

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string | yes |  |
| `title` | string | yes |  |
| `status` | integer | yes |  |
| `enrolment_token` | string | yes | Short-lived, authorises exactly the two enrolment calls. |

```json
{
  "type": "mfa_enrolment_required",
  "title": "string",
  "status": 428,
  "enrolment_token": "string"
}
```

### OutcomeStatus

```json
"success"
```

### DependencyState

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `latency_ms` | number |  |  |
| `reason` | string or null |  | Exception type, not its message. The message varies per incident, so grouping by it produces one bucket per occurrence. |

```json
{
  "status": "success",
  "latency_ms": 0,
  "reason": "string"
}
```

### HealthReport

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `degraded` | boolean | yes |  |
| `checked_at` | string (date-time) | yes |  |
| `dependencies` | object | yes |  |
| `dependencies.<key>` | object |  |  |
| `failing` | array of string | yes |  |

```json
{
  "status": "success",
  "degraded": true,
  "checked_at": "2026-10-13T09:30:00Z",
  "dependencies": {
    "<key>": {
      "status": "success",
      "latency_ms": 0,
      "reason": "string"
    }
  },
  "failing": [
    "string"
  ]
}
```

### ParkedEvent

| Field | Type | Required | Notes |
|---|---|---|---|
| `event_id` | string (uuid) | yes |  |
| `event_name` | string | yes |  |
| `attempts` | integer | yes |  |
| `occurred_at` | string (date-time) | yes |  |

```json
{
  "event_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "event_name": "look.failed",
  "attempts": 0,
  "occurred_at": "2026-10-13T09:30:00Z"
}
```

### EventBacklog

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `unpublished` | integer | yes | Still retryable — the relay is behind. |
| `parked` | integer | yes | Attempts exhausted. Nothing will publish these without intervention. |
| `oldest_unpublished_at` | string or null (date-time) | yes |  |
| `unpublished_by_event` | object |  |  |
| `unpublished_by_event.<key>` | integer |  |  |
| `parked_events` | array of object |  |  |
| `parked_events[]` | object |  |  |
| `parked_events[].event_id` | string (uuid) | yes |  |
| `parked_events[].event_name` | string | yes |  |
| `parked_events[].attempts` | integer | yes |  |
| `parked_events[].occurred_at` | string (date-time) | yes |  |

```json
{
  "status": "success",
  "unpublished": 0,
  "parked": 0,
  "oldest_unpublished_at": "2026-10-13T09:30:00Z",
  "unpublished_by_event": {
    "<key>": 0
  },
  "parked_events": [
    {
      "event_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "event_name": "look.failed",
      "attempts": 0,
      "occurred_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```

### DeliveryReport

| Field | Type | Required | Notes |
|---|---|---|---|
| `window_hours` | integer | yes |  |
| `status` | `success` / `partial` / `failure` | yes | The same vocabulary the logs use. `partial` means it worked and something is still wrong — the state a boolean loses. |
| `by_status` | object | yes |  |
| `by_status.<key>` | integer |  |  |
| `by_failure_reason` | object | yes |  |
| `by_failure_reason.<key>` | integer |  |  |
| `by_channel` | array of object |  |  |
| `by_channel[]` | object |  |  |
| `by_channel[].channel` | string |  |  |
| `by_channel[].status` | string |  |  |
| `by_channel[].count` | integer |  |  |

```json
{
  "window_hours": 0,
  "status": "success",
  "by_status": {
    "sent": 412,
    "suppressed": 62,
    "failed": 3
  },
  "by_failure_reason": {
    "no_consent": 62,
    "provider_unavailable": 3
  },
  "by_channel": [
    {
      "channel": "string",
      "status": "string",
      "count": 0
    }
  ]
}
```

### Justification

| Field | Type | Required | Notes |
|---|---|---|---|
| `justification` | string | yes |  |

```json
{
  "justification": "string"
}
```

### ConnectedAccount

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `user_id` | string (uuid) | yes |  |
| `provider` | `pinterest` | yes |  |
| `status` | `active` / `syncing` / `needs_reauth` / `revoked` | yes |  |
| `scopes` | array of string | yes |  |
| `connected_at` | string (date-time) | yes |  |
| `last_sync_at` | string or null (date-time) |  |  |
| `token_expires_at` | string or null (date-time) |  |  |
| `boards_imported` | integer | yes |  |
| `pins_imported` | integer | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "provider": "pinterest",
  "status": "active",
  "scopes": [
    "string"
  ],
  "connected_at": "2026-10-13T09:30:00Z",
  "last_sync_at": "2026-10-13T09:30:00Z",
  "token_expires_at": "2026-10-13T09:30:00Z",
  "boards_imported": 0,
  "pins_imported": 0
}
```

### IntegrationList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].user_id` | string (uuid) | yes |  |
| `items[].provider` | `pinterest` | yes |  |
| `items[].status` | `active` / `syncing` / `needs_reauth` / `revoked` | yes |  |
| `items[].scopes` | array of string | yes |  |
| `items[].connected_at` | string (date-time) | yes |  |
| `items[].last_sync_at` | string or null (date-time) |  |  |
| `items[].token_expires_at` | string or null (date-time) |  |  |
| `items[].boards_imported` | integer | yes |  |
| `items[].pins_imported` | integer | yes |  |
| `next_before` | string or null (date-time) | yes |  |
| `summary` | object | yes |  |
| `summary.by_status` | object | yes |  |
| `summary.by_status.<key>` | integer |  |  |
| `summary.connected` | integer | yes |  |
| `summary.pins_imported` | integer | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "provider": "pinterest",
      "status": "active",
      "scopes": [
        "string"
      ],
      "connected_at": "2026-10-13T09:30:00Z",
      "last_sync_at": "2026-10-13T09:30:00Z",
      "token_expires_at": "2026-10-13T09:30:00Z",
      "boards_imported": 0,
      "pins_imported": 0
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "summary": {
    "by_status": {
      "active": 12,
      "needs_reauth": 1
    },
    "connected": 0,
    "pins_imported": 0
  }
}
```

### ImportedPin

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `pin_id` | string | yes |  |
| `board_id` | string | yes |  |
| `board_name` | string | yes |  |
| `title` | string or null |  | Untrusted text. Render as plain text. |
| `description` | string or null |  | Untrusted text. Render as plain text. |
| `image_url` | string or null |  | A Pinterest CDN address (i.pinimg.com). |
| `image_status` | `none` / `pending_detector` / `cached` / `rejected` / `failed` | yes |  |
| `imported_at` | string (date-time) | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "pin_id": "string",
  "board_id": "string",
  "board_name": "string",
  "title": "string",
  "description": "string",
  "image_url": "string",
  "image_status": "none",
  "imported_at": "2026-10-13T09:30:00Z"
}
```

### PinList

| Field | Type | Required | Notes |
|---|---|---|---|
| `account` | object | yes |  |
| `account.id` | string (uuid) | yes |  |
| `account.user_id` | string (uuid) | yes |  |
| `account.provider` | `pinterest` | yes |  |
| `account.status` | `active` / `syncing` / `needs_reauth` / `revoked` | yes |  |
| `account.scopes` | array of string | yes |  |
| `account.connected_at` | string (date-time) | yes |  |
| `account.last_sync_at` | string or null (date-time) |  |  |
| `account.token_expires_at` | string or null (date-time) |  |  |
| `account.boards_imported` | integer | yes |  |
| `account.pins_imported` | integer | yes |  |
| `boards` | array of object | yes |  |
| `boards[]` | object |  |  |
| `boards[].board_id` | string | yes |  |
| `boards[].name` | string | yes |  |
| `boards[].pins` | integer | yes |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].pin_id` | string | yes |  |
| `items[].board_id` | string | yes |  |
| `items[].board_name` | string | yes |  |
| `items[].title` | string or null |  | Untrusted text. Render as plain text. |
| `items[].description` | string or null |  | Untrusted text. Render as plain text. |
| `items[].image_url` | string or null |  | A Pinterest CDN address (i.pinimg.com). |
| `items[].image_status` | `none` / `pending_detector` / `cached` / `rejected` / `failed` | yes |  |
| `items[].imported_at` | string (date-time) | yes |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "account": {
    "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "provider": "pinterest",
    "status": "active",
    "scopes": [
      "string"
    ],
    "connected_at": "2026-10-13T09:30:00Z",
    "last_sync_at": "2026-10-13T09:30:00Z",
    "token_expires_at": "2026-10-13T09:30:00Z",
    "boards_imported": 0,
    "pins_imported": 0
  },
  "boards": [
    {
      "board_id": "string",
      "name": "string",
      "pins": 0
    }
  ],
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "pin_id": "string",
      "board_id": "string",
      "board_name": "string",
      "title": "string",
      "description": "string",
      "image_url": "string",
      "image_status": "none",
      "imported_at": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

### DeletionRequest

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `user_id` | string (uuid) | yes | The account that was deleted. |
| `state` | `scheduled` / `open` / `overdue` / `completed` / `cancelled` | yes |  |
| `requested_at` | string (date-time) | yes |  |
| `purge_after` | string or null (date-time) |  | When the data is removed. |
| `sla_due_at` | string (date-time) | yes |  |
| `completed_at` | string or null (date-time) |  |  |
| `cancelled_at` | string or null (date-time) |  |  |
| `days_left` | integer or null |  | Negative when overdue. Null once completed. |
| `modules_pending` | array of string | yes | Modules that have not confirmed yet. |
| `modules_done` | array of string | yes |  |
| `third_parties_done` | array of string | yes |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "state": "scheduled",
  "requested_at": "2026-10-13T09:30:00Z",
  "purge_after": "2026-10-13T09:30:00Z",
  "sla_due_at": "2026-10-13T09:30:00Z",
  "completed_at": "2026-10-13T09:30:00Z",
  "cancelled_at": "2026-10-13T09:30:00Z",
  "days_left": 0,
  "modules_pending": [
    "string"
  ],
  "modules_done": [
    "string"
  ],
  "third_parties_done": [
    "string"
  ]
}
```

### DeletionRequestList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].user_id` | string (uuid) | yes | The account that was deleted. |
| `items[].state` | `scheduled` / `open` / `overdue` / `completed` / `cancelled` | yes |  |
| `items[].requested_at` | string (date-time) | yes |  |
| `items[].purge_after` | string or null (date-time) |  | When the data is removed. |
| `items[].sla_due_at` | string (date-time) | yes |  |
| `items[].completed_at` | string or null (date-time) |  |  |
| `items[].cancelled_at` | string or null (date-time) |  |  |
| `items[].days_left` | integer or null |  | Negative when overdue. Null once completed. |
| `items[].modules_pending` | array of string | yes | Modules that have not confirmed yet. |
| `items[].modules_done` | array of string | yes |  |
| `items[].third_parties_done` | array of string | yes |  |
| `next_before` | string or null (date-time) | yes |  |
| `summary` | object | yes |  |
| `summary.scheduled` | integer | yes |  |
| `summary.open` | integer | yes |  |
| `summary.overdue` | integer | yes |  |
| `summary.due_within_5_days` | integer | yes |  |
| `summary.completed` | integer | yes |  |
| `summary.cancelled` | integer | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "state": "scheduled",
      "requested_at": "2026-10-13T09:30:00Z",
      "purge_after": "2026-10-13T09:30:00Z",
      "sla_due_at": "2026-10-13T09:30:00Z",
      "completed_at": "2026-10-13T09:30:00Z",
      "cancelled_at": "2026-10-13T09:30:00Z",
      "days_left": 0,
      "modules_pending": [
        "string"
      ],
      "modules_done": [
        "string"
      ],
      "third_parties_done": [
        "string"
      ]
    }
  ],
  "next_before": "2026-10-13T09:30:00Z",
  "summary": {
    "scheduled": 0,
    "open": 0,
    "overdue": 0,
    "due_within_5_days": 0,
    "completed": 0,
    "cancelled": 0
  }
}
```

### Account

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | string (uuid) | yes |  |
| `username` | string or null |  |  |
| `email_masked` | string or null |  |  |
| `status` | string | yes |  |
| `created_at` | string (date-time) | yes |  |
| `quiz_completed` | boolean | yes |  |
| `restricted` | boolean | yes | The person restricted processing. |
| `integrations` | array of string | yes |  |
| `deletion_scheduled` | boolean |  | Waiting out the deletion period. |
| `purge_after` | string or null (date-time) |  |  |

```json
{
  "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "email_masked": "a***@e***.com",
  "status": "string",
  "created_at": "2026-10-13T09:30:00Z",
  "quiz_completed": true,
  "restricted": true,
  "integrations": [
    "string"
  ],
  "deletion_scheduled": true,
  "purge_after": "2026-10-13T09:30:00Z"
}
```

### AccountList

| Field | Type | Required | Notes |
|---|---|---|---|
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].id` | string (uuid) | yes |  |
| `items[].username` | string or null |  |  |
| `items[].email_masked` | string or null |  |  |
| `items[].status` | string | yes |  |
| `items[].created_at` | string (date-time) | yes |  |
| `items[].quiz_completed` | boolean | yes |  |
| `items[].restricted` | boolean | yes | The person restricted processing. |
| `items[].integrations` | array of string | yes |  |
| `items[].deletion_scheduled` | boolean |  | Waiting out the deletion period. |
| `items[].purge_after` | string or null (date-time) |  |  |
| `next_before` | string or null (date-time) | yes |  |

```json
{
  "items": [
    {
      "id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "username": "string",
      "email_masked": "a***@e***.com",
      "status": "string",
      "created_at": "2026-10-13T09:30:00Z",
      "quiz_completed": true,
      "restricted": true,
      "integrations": [
        "string"
      ],
      "deletion_scheduled": true,
      "purge_after": "2026-10-13T09:30:00Z"
    }
  ],
  "next_before": "2026-10-13T09:30:00Z"
}
```

### Problem

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string | yes |  |
| `title` | string | yes |  |
| `status` | integer | yes |  |
| `detail` | string |  |  |
| `trace_id` | string |  |  |

```json
{
  "type": "string",
  "title": "string",
  "status": 0,
  "detail": "string",
  "trace_id": "string"
}
```
