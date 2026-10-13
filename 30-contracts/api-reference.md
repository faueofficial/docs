# FAUE API reference (v1)

> Generated from the OpenAPI contract by `tools/build_reference.py`. Do not edit by hand.

Every endpoint the mobile app and the website use, with request and response schemas. Read [app-developer-guide.md](app-developer-guide.md) first for authentication, errors, pagination and flows.

**Base URL:** `https://api.faueofficial.com/v1`

## Contents

- [auth](#auth) (7)
- [profile](#profile) (6)
- [quiz](#quiz) (6)
- [vault](#vault) (7)
- [looks](#looks) (11)
- [fabric](#fabric) (2)
- [spree](#spree) (3)
- [agent](#agent) (4)
- [integrations](#integrations) (6)
- [notifications](#notifications) (5)
- [uploads](#uploads) (3)
- [privacy](#privacy) (3)
- [contact](#contact) (1)
- [early-access](#early-access) (1)
- [cards](#cards) (2)
- [unsubscribe](#unsubscribe) (2)

## auth

Magic link, OAuth, session lifecycle

### `POST /auth/link/request`

**Request a magic link**

`MVP` Sends a sign-in link to the given email address. Always returns `202`,
whether or not the address is registered — revealing which addresses exist
is an account-enumeration vector.

`session_challenge` is an opaque value the client generates and retains. If
the link is opened on a different device, the landing page falls back to a
6-digit code the user types into this session.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string (email) | yes |  |
| `session_challenge` | string | yes | Client-generated opaque value binding the request to this device. |

```json
{
  "email": "ada@example.com",
  "session_challenge": "string"
}
```

**Responses**

- **202**: Link dispatched if the address is valid. Every field below is derived from the request, so this body is byte-identical for a registered address and an unknown one — that is deliberate, and no field that depends on account existence may be added to it.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `delivery` | `email` / `sms` | yes | Where the code went. `email` today; `sms` arrives in M1-2 — read this rather than assuming. |
| `masked_destination` | string | yes | For the check-email screen. Derived from the address you sent, so it reveals nothing. |
| `expires_in` | integer | yes | Seconds until the link stops working |
| `resend_available_in` | integer | yes | Seconds until another request is accepted. Drive the resend cooldown from this rather than a hardcoded value — the two disagree the moment the server rule changes. |

```json
{
  "delivery": "email",
  "masked_destination": "ad••••@example.com",
  "expires_in": 600,
  "resend_available_in": 60
}
```

- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/link/consume`

**Consume a magic link token**

`MVP` Exchanges a magic-link token for a session. **POST only** — mail security
scanners pre-fetch URLs, so a GET that consumed the token would burn the login
before the user tapped it.

Single-use. A second attempt with the same token returns `410`.

When `session_challenge` does not match the one from the request, the response
is `409` with a `device_code`; the user types that code into the original
session, which then calls this endpoint again with `device_code` set.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `token` | string | yes |  |
| `session_challenge` | string |  |  |
| `device_code` | string |  | Supplied when completing a cross-device sign-in |

```json
{
  "token": "string",
  "session_challenge": "string",
  "device_code": "string"
}
```

**Responses**

- **200**: Signed in

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes | How to present the access token. |
| `expires_in` | integer | yes | Seconds until the access token expires. |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes | Seconds until the refresh token expires. |
| `is_new_user` | boolean | yes | Route to onboarding rather than the dashboard. |
| `onboarding` | object | yes | Included on sign-in so the app can route straight from the auth screen without a second call. Absent from `/auth/refresh` — refresh runs every twelve minutes and no screen reads this at that moment. |
| `onboarding.username_set` | boolean | yes |  |
| `onboarding.quiz_completed` | boolean | yes |  |
| `onboarding.pinterest_connected` | boolean | yes |  |
| `onboarding.vault_started` | boolean | yes |  |
| `onboarding.body_profile_set` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true,
  "onboarding": {
    "username_set": true,
    "quiz_completed": true,
    "pinterest_connected": true,
    "vault_started": true,
    "body_profile_set": true
  }
}
```

- **409**: Opened on a different device; complete with the returned code

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `device_code_required` | boolean | yes |  |
| `device_code` | string |  | 6-digit code to enter in the original session |

```json
{
  "device_code_required": true,
  "device_code": "string"
}
```

- **410**: Token already used or expired
  - body: `application/problem+json`, see *Errors* in the guide
- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/oauth/google`

**Sign in with Google**

`MVP` Verifies the Google ID token server-side against Google's JWKS,
checking `iss`, `aud`, `nonce`, and `exp`. A client-supplied profile is
never trusted.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `id_token` | string | yes |  |
| `nonce` | string | yes |  |

```json
{
  "id_token": "string",
  "nonce": "string"
}
```

**Responses**

- **200**: Signed in

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes | How to present the access token. |
| `expires_in` | integer | yes | Seconds until the access token expires. |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes | Seconds until the refresh token expires. |
| `is_new_user` | boolean | yes | Route to onboarding rather than the dashboard. |
| `onboarding` | object | yes | Included on sign-in so the app can route straight from the auth screen without a second call. Absent from `/auth/refresh` — refresh runs every twelve minutes and no screen reads this at that moment. |
| `onboarding.username_set` | boolean | yes |  |
| `onboarding.quiz_completed` | boolean | yes |  |
| `onboarding.pinterest_connected` | boolean | yes |  |
| `onboarding.vault_started` | boolean | yes |  |
| `onboarding.body_profile_set` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true,
  "onboarding": {
    "username_set": true,
    "quiz_completed": true,
    "pinterest_connected": true,
    "vault_started": true,
    "body_profile_set": true
  }
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/oauth/apple`

**Sign in with Apple**

`MVP` Verifies the Apple identity token against Apple's JWKS.

**`full_name` is returned by Apple only on first authorization.** The client
must forward it on that first call; it is unrecoverable afterwards.

Private-relay addresses (`@privaterelay.appleid.com`) are normal and must not
be treated as invalid.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `identity_token` | string | yes |  |
| `authorization_code` | string |  |  |
| `full_name` | string |  | Present only on first authorization |
| `nonce` | string |  |  |

```json
{
  "identity_token": "string",
  "authorization_code": "string",
  "full_name": "string",
  "nonce": "string"
}
```

**Responses**

- **200**: Signed in

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes | How to present the access token. |
| `expires_in` | integer | yes | Seconds until the access token expires. |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes | Seconds until the refresh token expires. |
| `is_new_user` | boolean | yes | Route to onboarding rather than the dashboard. |
| `onboarding` | object | yes | Included on sign-in so the app can route straight from the auth screen without a second call. Absent from `/auth/refresh` — refresh runs every twelve minutes and no screen reads this at that moment. |
| `onboarding.username_set` | boolean | yes |  |
| `onboarding.quiz_completed` | boolean | yes |  |
| `onboarding.pinterest_connected` | boolean | yes |  |
| `onboarding.vault_started` | boolean | yes |  |
| `onboarding.body_profile_set` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true,
  "onboarding": {
    "username_set": true,
    "quiz_completed": true,
    "pinterest_connected": true,
    "vault_started": true,
    "body_profile_set": true
  }
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/refresh`

**Rotate the session**

`MVP` Exchanges a refresh token for a new pair. Refresh tokens rotate on every
use. Presenting an already-rotated token revokes the entire family — that is
theft detection, and the correct client response is to sign the user out.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `refresh_token` | string | yes |  |

```json
{
  "refresh_token": "string"
}
```

**Responses**

- **200**: Rotated

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes |  |
| `expires_in` | integer | yes |  |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes |  |
| `is_new_user` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /auth/logout`

**Sign out**

`MVP` Revokes the refresh token sent, and ends that session only; other devices stay signed in.
Idempotent: an already revoked or unknown token still returns 204, so a retry after a network
failure needs no special case.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `refresh_token` | string | yes |  |

```json
{
  "refresh_token": "string"
}
```

**Responses**

- **204**: Signed out

### `POST /auth/username`

**Set the username**

`MVP` The post-signup username step. Usernames are unique, case-insensitive.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string | yes |  |

```json
{
  "username": "string"
}
```

**Responses**

- **200**: Set

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (uuid) | yes |  |
| `username` | string or null | yes |  |
| `display_name` | string or null |  |  |
| `gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `city` | string or null |  |  |
| `locale` | string |  |  |
| `avatar_url` | string or null (uri) |  |  |
| `created_at` | string (date-time) |  |  |

```json
{
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "display_name": "string",
  "gender_presentation": "feminine",
  "city": "string",
  "locale": "en-NG",
  "avatar_url": "https://example.com/...",
  "created_at": "2026-10-13T09:30:00Z"
}
```

- **409**: Already taken
  - body: `application/problem+json`, see *Errors* in the guide

## profile

Profile, body profile, consent

### `GET /me`

**Current user**

`MVP` Profile, quiz state, consent summary, and onboarding progress in one call — used on app launch.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `profile` | object | yes |  |
| `profile.user_id` | string (uuid) | yes |  |
| `profile.username` | string or null | yes |  |
| `profile.display_name` | string or null |  |  |
| `profile.gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `profile.city` | string or null |  |  |
| `profile.locale` | string |  |  |
| `profile.avatar_url` | string or null (uri) |  |  |
| `profile.created_at` | string (date-time) |  |  |
| `onboarding` | object | yes | Drives which onboarding step the app resumes at. |
| `onboarding.username_set` | boolean | yes |  |
| `onboarding.quiz_completed` | boolean | yes |  |
| `onboarding.pinterest_connected` | boolean | yes |  |
| `onboarding.vault_started` | boolean | yes |  |
| `onboarding.body_profile_set` | boolean | yes |  |
| `consents` | array of object | yes |  |
| `consents[]` | object |  |  |
| `consents[].purpose` | `essential` / `personalization` / `ai_processing` / `pinterest_sync` / `camera_photos` / `location_weather` / `agent_proactive` / `marketing_comms` / `analytics` | yes |  |
| `consents[].granted` | boolean | yes |  |
| `consents[].policy_version` | string or null |  |  |
| `consents[].granted_at` | string or null (date-time) |  |  |

```json
{
  "profile": {
    "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "username": "string",
    "display_name": "string",
    "gender_presentation": "feminine",
    "city": "string",
    "locale": "en-NG",
    "avatar_url": "https://example.com/...",
    "created_at": "2026-10-13T09:30:00Z"
  },
  "onboarding": {
    "username_set": true,
    "quiz_completed": true,
    "pinterest_connected": true,
    "vault_started": true,
    "body_profile_set": true
  },
  "consents": [
    {
      "purpose": "essential",
      "granted": true,
      "policy_version": "string",
      "granted_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```


### `PATCH /me`

**Update profile**

`MVP` Partial update. Only supplied fields change.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `display_name` | string |  |  |
| `gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `city` | string |  |  |
| `locale` | string |  |  |
| `avatar_asset_id` | string (uuid) |  |  |

```json
{
  "display_name": "string",
  "gender_presentation": "feminine",
  "city": "string",
  "locale": "en-NG",
  "avatar_asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
}
```

**Responses**

- **200**: Updated

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (uuid) | yes |  |
| `username` | string or null | yes |  |
| `display_name` | string or null |  |  |
| `gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `city` | string or null |  |  |
| `locale` | string |  |  |
| `avatar_url` | string or null (uri) |  |  |
| `created_at` | string (date-time) |  |  |

```json
{
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "display_name": "string",
  "gender_presentation": "feminine",
  "city": "string",
  "locale": "en-NG",
  "avatar_url": "https://example.com/...",
  "created_at": "2026-10-13T09:30:00Z"
}
```


### `GET /me/body-profile`

**Get body profile**

`MVP` `Consent: personalization`

Sensitive data. Every field is optional and independently omittable. Absent
values are returned as `null`, never as guesses.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `body_shape` | `hourglass` / `pear` / `rectangle` / `inverted_triangle` / `apple` / `triangle` / `oval` / null |  |  |
| `height_cm` | integer or null |  |  |
| `fit_preference` | `fitted` / `regular` / `relaxed` / null |  |  |
| `sizes_by_category` | object |  |  |
| `sizes_by_category.<key>` | string |  |  |
| `measurements` | object or null |  | Optional expansion. Absent for most users. |

```json
{
  "body_shape": "hourglass",
  "height_cm": 0,
  "fit_preference": "fitted",
  "sizes_by_category": {
    "tops": "M",
    "bottoms": "32",
    "shoes": "43"
  },
  "measurements": {
    "<key>": 0
  }
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `PUT /me/body-profile`

**Set body profile**

`MVP` `Consent: personalization`

Drives hard constraints in look generation — silhouette rules, not vector
similarity. Never sent to a model in raw form; `ase` receives abstract
constraints such as `favor: defined_waist`.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `body_shape` | `hourglass` / `pear` / `rectangle` / `inverted_triangle` / `apple` / `triangle` / `oval` / null |  |  |
| `height_cm` | integer or null |  |  |
| `fit_preference` | `fitted` / `regular` / `relaxed` / null |  |  |
| `sizes_by_category` | object |  |  |
| `sizes_by_category.<key>` | string |  |  |
| `measurements` | object or null |  | Optional expansion. Absent for most users. |

```json
{
  "body_shape": "hourglass",
  "height_cm": 0,
  "fit_preference": "fitted",
  "sizes_by_category": {
    "tops": "M",
    "bottoms": "32",
    "shoes": "43"
  },
  "measurements": {
    "<key>": 0
  }
}
```

**Responses**

- **200**: Saved

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `body_shape` | `hourglass` / `pear` / `rectangle` / `inverted_triangle` / `apple` / `triangle` / `oval` / null |  |  |
| `height_cm` | integer or null |  |  |
| `fit_preference` | `fitted` / `regular` / `relaxed` / null |  |  |
| `sizes_by_category` | object |  |  |
| `sizes_by_category.<key>` | string |  |  |
| `measurements` | object or null |  | Optional expansion. Absent for most users. |

```json
{
  "body_shape": "hourglass",
  "height_cm": 0,
  "fit_preference": "fitted",
  "sizes_by_category": {
    "tops": "M",
    "bottoms": "32",
    "shoes": "43"
  },
  "measurements": {
    "<key>": 0
  }
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /me/consents`

**List consent state**

`MVP` Every purpose and its current state. Purposes not yet granted appear with `granted: false`.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `` | array of object |  |  |
| `[]` | object |  |  |
| `[].purpose` | `essential` / `personalization` / `ai_processing` / `pinterest_sync` / `camera_photos` / `location_weather` / `agent_proactive` / `marketing_comms` / `analytics` | yes |  |
| `[].granted` | boolean | yes |  |
| `[].policy_version` | string or null |  |  |
| `[].granted_at` | string or null (date-time) |  |  |

```json
[
  {
    "purpose": "essential",
    "granted": true,
    "policy_version": "string",
    "granted_at": "2026-10-13T09:30:00Z"
  }
]
```


### `PUT /me/consents`

**Grant or revoke a consent purpose**

`MVP` Revocation takes effect immediately and stops all processing for that
purpose. Revoking `ai_processing` disables generation; revoking
`pinterest_sync` also revokes the upstream token.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `purpose` | `essential` / `personalization` / `ai_processing` / `pinterest_sync` / `camera_photos` / `location_weather` / `agent_proactive` / `marketing_comms` / `analytics` | yes |  |
| `granted` | boolean | yes |  |
| `policy_version` | string | yes |  |

```json
{
  "purpose": "essential",
  "granted": true,
  "policy_version": "2026-08-17"
}
```

**Responses**

- **200**: Updated

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `purpose` | `essential` / `personalization` / `ai_processing` / `pinterest_sync` / `camera_photos` / `location_weather` / `agent_proactive` / `marketing_comms` / `analytics` | yes |  |
| `granted` | boolean | yes |  |
| `policy_version` | string or null |  |  |
| `granted_at` | string or null (date-time) |  |  |

```json
{
  "purpose": "essential",
  "granted": true,
  "policy_version": "string",
  "granted_at": "2026-10-13T09:30:00Z"
}
```


## quiz

Style DNA

### `GET /quiz`

**Get quiz definition**

`MVP` Questions, options, copy, and layout for the current quiz version.

**Render option layouts from this response, never from a hardcoded grid.**
Q6 has three options where the others have four.

**Auth:** none

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `questions` | array of object | yes |  |
| `questions[]` | object |  |  |
| `questions[].id` | integer | yes |  |
| `questions[].prompt` | string | yes |  |
| `questions[].subtitle` | string or null |  |  |
| `questions[].progress` | integer |  | Percentage to show on this screen |
| `questions[].max_choices` | integer |  | How many options may be ticked. 1 means a single choice (radio buttons); more means checkboxes, up to this many. Ticked options share the question's weight equally, so choosing more never gives a question a bigger say. Absent from a gateway that predates multiple answers: treat that as 1. |
| `questions[].options` | array of object | yes | Length varies by question — Q6 has three. Build the layout from this. |
| `questions[].options[]` | object |  |  |
| `questions[].options[].id` | string | yes |  |
| `questions[].options[].label` | string | yes |  |
| `questions[].options[].description` | string |  |  |
| `questions[].options[].image_url` | string or null (uri) |  |  |

```json
{
  "quiz_version": "dna-2026-08-v1",
  "questions": [
    {
      "id": 0,
      "prompt": "string",
      "subtitle": "string",
      "progress": 0,
      "max_choices": 0,
      "options": [
        {
          "id": "A",
          "label": "Minimal",
          "description": "string",
          "image_url": "https://example.com/..."
        }
      ]
    }
  ]
}
```


### `POST /quiz/preview`

**Score answers without an account**

`MVP` Scores answers and returns the Style DNA result. **No sign-in needed and
nothing is stored or published.** The result is the one `POST /quiz/submit` would
give for the same answers, except `card_urls.status` is `not_applicable` and
`retake_available_at` is `null`. Limited per IP address.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `answers` | object | yes | Question id to option id, or a list of option ids, as for `POST /quiz/submit`. |
| `answers.<key>` | string or array |  |  |

```json
{
  "quiz_version": "string",
  "answers": {
    "<key>": "string"
  }
}
```

**Responses**

- **200**: The result.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `dominant` | object | yes |  |
| `dominant.id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `dominant.name` | string | yes |  |
| `dominant.percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `dominant.gradient_from` | string |  |  |
| `dominant.gradient_to` | string |  |  |
| `alter_ego` | object or null |  |  |
| `wildcard` | object or null |  |  |
| `tagline` | string |  | Tier 1 persona line. Fixed per persona. |
| `blend_line` | string |  | Tier 2. Varies by dominant x alter-ego pair; 30 hand-written variants. |
| `personal_line` | string or null |  | Tier 3 (M1-2). Generated once from the answer pattern, then frozen. Null when absent — close the layout up rather than leaving a gap. |
| `scores` | object | yes | Raw scores per persona id. Display uses the percentages on each persona. |
| `scores.<key>` | number |  |  |
| `card_urls` | object |  |  |
| `card_urls.status` | `pending` / `ready` / `failed` | yes |  |
| `card_urls.square_url` | string or null (uri) |  |  |
| `card_urls.stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `card_urls.share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |
| `completed_at` | string (date-time) | yes |  |
| `retake_available_at` | string (date-time) |  |  |

```json
{
  "quiz_version": "string",
  "dominant": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "alter_ego": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "wildcard": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "tagline": "string",
  "blend_line": "string",
  "personal_line": "string",
  "scores": {
    "<key>": 0
  },
  "card_urls": {
    "status": "pending",
    "square_url": "https://example.com/...",
    "stories_url": "https://example.com/...",
    "share_url": "https://example.com/..."
  },
  "completed_at": "2026-10-13T09:30:00Z",
  "retake_available_at": "2026-10-13T09:30:00Z"
}
```

- **422**: Answers are missing or not valid options.
- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /quiz/submit`

**Submit answers**

`MVP` Scores synchronously and returns the result immediately. Card rendering
is asynchronous — `card_urls.status` will be `pending`; poll `/quiz/card`.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `answers` | object | yes | Question id to the chosen option id, or to a list of option ids when the question takes more than one (`max_choices` in `GET /quiz`). A single choice may be sent as a plain string. Order and repeats do not matter. |
| `answers.<key>` | string or array |  |  |

```json
{
  "quiz_version": "dna-2026-08-v1",
  "answers": {
    "1": [
      "A",
      "C"
    ],
    "2": "C",
    "3": "D",
    "4": [
      "A",
      "D"
    ],
    "5": "A",
    "6": "A"
  }
}
```

**Responses**

- **200**: Scored

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `dominant` | object | yes |  |
| `dominant.id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `dominant.name` | string | yes |  |
| `dominant.percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `dominant.gradient_from` | string |  |  |
| `dominant.gradient_to` | string |  |  |
| `alter_ego` | object or null |  |  |
| `wildcard` | object or null |  |  |
| `tagline` | string |  | Tier 1 persona line. Fixed per persona. |
| `blend_line` | string |  | Tier 2. Varies by dominant x alter-ego pair; 30 hand-written variants. |
| `personal_line` | string or null |  | Tier 3 (M1-2). Generated once from the answer pattern, then frozen. Null when absent — close the layout up rather than leaving a gap. |
| `scores` | object | yes | Raw scores per persona id. Display uses the percentages on each persona. |
| `scores.<key>` | number |  |  |
| `card_urls` | object |  |  |
| `card_urls.status` | `pending` / `ready` / `failed` | yes |  |
| `card_urls.square_url` | string or null (uri) |  |  |
| `card_urls.stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `card_urls.share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |
| `completed_at` | string (date-time) | yes |  |
| `retake_available_at` | string (date-time) |  |  |

```json
{
  "quiz_version": "string",
  "dominant": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "alter_ego": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "wildcard": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "tagline": "string",
  "blend_line": "string",
  "personal_line": "string",
  "scores": {
    "<key>": 0
  },
  "card_urls": {
    "status": "pending",
    "square_url": "https://example.com/...",
    "stories_url": "https://example.com/...",
    "share_url": "https://example.com/..."
  },
  "completed_at": "2026-10-13T09:30:00Z",
  "retake_available_at": "2026-10-13T09:30:00Z"
}
```

- **409**: Retake not yet available
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /quiz/result`

**Get current result**

`MVP`

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `dominant` | object | yes |  |
| `dominant.id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `dominant.name` | string | yes |  |
| `dominant.percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `dominant.gradient_from` | string |  |  |
| `dominant.gradient_to` | string |  |  |
| `alter_ego` | object or null |  |  |
| `wildcard` | object or null |  |  |
| `tagline` | string |  | Tier 1 persona line. Fixed per persona. |
| `blend_line` | string |  | Tier 2. Varies by dominant x alter-ego pair; 30 hand-written variants. |
| `personal_line` | string or null |  | Tier 3 (M1-2). Generated once from the answer pattern, then frozen. Null when absent — close the layout up rather than leaving a gap. |
| `scores` | object | yes | Raw scores per persona id. Display uses the percentages on each persona. |
| `scores.<key>` | number |  |  |
| `card_urls` | object |  |  |
| `card_urls.status` | `pending` / `ready` / `failed` | yes |  |
| `card_urls.square_url` | string or null (uri) |  |  |
| `card_urls.stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `card_urls.share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |
| `completed_at` | string (date-time) | yes |  |
| `retake_available_at` | string (date-time) |  |  |

```json
{
  "quiz_version": "string",
  "dominant": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "alter_ego": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "wildcard": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "tagline": "string",
  "blend_line": "string",
  "personal_line": "string",
  "scores": {
    "<key>": 0
  },
  "card_urls": {
    "status": "pending",
    "square_url": "https://example.com/...",
    "stories_url": "https://example.com/...",
    "share_url": "https://example.com/..."
  },
  "completed_at": "2026-10-13T09:30:00Z",
  "retake_available_at": "2026-10-13T09:30:00Z"
}
```

- **404**: Quiz not completed
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /quiz/card`

**Get share card URLs**

`MVP` Returns `status: pending` until the render completes; poll every 2 seconds, up to 30 seconds.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `pending` / `ready` / `failed` | yes |  |
| `square_url` | string or null (uri) |  |  |
| `stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |

```json
{
  "status": "pending",
  "square_url": "https://example.com/...",
  "stories_url": "https://example.com/...",
  "share_url": "https://example.com/..."
}
```


### `POST /quiz/retake`

**Reset for a retake**

`MVP` Allowed once per 30 days. `retake_available_at` on the result says when.

**Auth:** bearer token

**Responses**

- **204**: Reset
- **409**: Too soon
  - body: `application/problem+json`, see *Errors* in the guide

## vault

The user's own wardrobe

### `GET /vault/items`

**List vault items**

`MVP` Cursor-paginated. Categories match the app: tops, bottoms, native, shoes, accessories.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `category` | query | `tops` / `bottoms` / `native` / `shoes` / `accessories` |  |  |
| `q` | query | string |  | Free-text search over name and notes |
| `cursor` | query | string |  | Opaque cursor from the previous page's `next_cursor`. |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `next_cursor` | string or null | yes |  |
| `has_more` | boolean | yes |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].item_id` | string (uuid) | yes |  |
| `items[].name` | string | yes |  |
| `items[].category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `items[].colors` | array of string |  |  |
| `items[].fabric` | string or null |  |  |
| `items[].brand` | string or null |  |  |
| `items[].notes` | string or null |  |  |
| `items[].image_url` | string (uri) | yes |  |
| `items[].wear_count` | integer |  |  |
| `items[].last_worn_at` | string or null (date-time) |  |  |
| `items[].created_at` | string (date-time) | yes |  |

```json
{
  "next_cursor": "string",
  "has_more": true,
  "items": [
    {
      "item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "name": "string",
      "category": "tops",
      "colors": [
        "string"
      ],
      "fabric": "string",
      "brand": "string",
      "notes": "string",
      "image_url": "https://example.com/...",
      "wear_count": 0,
      "last_worn_at": "2026-10-13T09:30:00Z",
      "created_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```


### `POST /vault/items`

**Add a vault item**

`MVP` The asset must be `ready`. The item is embedded asynchronously and becomes available to generation within seconds.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `name` | string | yes |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `colors` | array of string |  |  |
| `fabric` | string |  |  |
| `brand` | string |  |  |
| `notes` | string |  |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string"
}
```

**Responses**

- **201**: Created

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `item_id` | string (uuid) | yes |  |
| `name` | string | yes |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `colors` | array of string |  |  |
| `fabric` | string or null |  |  |
| `brand` | string or null |  |  |
| `notes` | string or null |  |  |
| `image_url` | string (uri) | yes |  |
| `wear_count` | integer |  |  |
| `last_worn_at` | string or null (date-time) |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string",
  "image_url": "https://example.com/...",
  "wear_count": 0,
  "last_worn_at": "2026-10-13T09:30:00Z",
  "created_at": "2026-10-13T09:30:00Z"
}
```


### `GET /vault/items/{item_id}`

**Get a vault item**

`MVP`

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `item_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `item_id` | string (uuid) | yes |  |
| `name` | string | yes |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `colors` | array of string |  |  |
| `fabric` | string or null |  |  |
| `brand` | string or null |  |  |
| `notes` | string or null |  |  |
| `image_url` | string (uri) | yes |  |
| `wear_count` | integer |  |  |
| `last_worn_at` | string or null (date-time) |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string",
  "image_url": "https://example.com/...",
  "wear_count": 0,
  "last_worn_at": "2026-10-13T09:30:00Z",
  "created_at": "2026-10-13T09:30:00Z"
}
```

- **404**: Not found
  - body: `application/problem+json`, see *Errors* in the guide

### `PATCH /vault/items/{item_id}`

**Edit a vault item**

`MVP`

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `item_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `name` | string |  |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` |  |  |
| `colors` | array of string |  |  |
| `fabric` | string |  |  |
| `brand` | string |  |  |
| `notes` | string |  |  |

```json
{
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string"
}
```

**Responses**

- **200**: Updated

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `item_id` | string (uuid) | yes |  |
| `name` | string | yes |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `colors` | array of string |  |  |
| `fabric` | string or null |  |  |
| `brand` | string or null |  |  |
| `notes` | string or null |  |  |
| `image_url` | string (uri) | yes |  |
| `wear_count` | integer |  |  |
| `last_worn_at` | string or null (date-time) |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string",
  "image_url": "https://example.com/...",
  "wear_count": 0,
  "last_worn_at": "2026-10-13T09:30:00Z",
  "created_at": "2026-10-13T09:30:00Z"
}
```


### `DELETE /vault/items/{item_id}`

**Remove a vault item**

`MVP` Permanent. The app shows a confirmation modal; the server does not.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `item_id` | path | string (uuid) | yes |  |

**Responses**

- **204**: Removed

### `POST /vault/items/{item_id}/style`

**Style this item (not served)**

> **Deprecated.**

`MVP` `Consent: ai_processing`

**Not served by the gateway today.** Use `POST /looks/generate` with this item, or
`POST /fabric/{asset_id}/style` for fabric. Kept here until the app stops referring to it.

Starts look generation seeded by this item — the "Style this item" action.
Returns a job envelope; see `/looks/jobs/{job_id}`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `item_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `note` | string |  |  |

```json
{
  "occasion": "owambe",
  "note": "string"
}
```

**Responses**

- **202**: Job accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /vault/wear`

**Log a wear**

`MVP` Records what was actually worn. This is the strongest behavioural signal
the system has and what the agent learns from — worth prompting for.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `item_ids` | array of string (uuid) | yes |  |
| `look_id` | string (uuid) |  |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `worn_on` | string (date) | yes |  |

```json
{
  "item_ids": [
    "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
  ],
  "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "occasion": "owambe",
  "worn_on": "string"
}
```

**Responses**

- **201**: Logged

## looks

Look generation and saved looks

### `POST /looks/generate`

**Generate looks**

`MVP` `Consent: ai_processing`

Asynchronous. Returns a job envelope immediately; follow progress over SSE at
`stream_url` or by polling `poll_url`.

Typical completion is 20–45 seconds. Progress states are `queued`,
`analyzing`, `assembling`, `rendering`, `done`, `failed`.

`use_weather` requires `location_weather` consent; without it the request
still succeeds and weather is simply not used.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `source` | `vault` / `fabric` / `prompt` | yes |  |
| `item_ids` | array of string (uuid) |  | Required when source is vault |
| `fabric_asset_id` | string (uuid) |  | Required when source is fabric |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `mood` | string |  |  |
| `note` | string |  | The app's "Add a note (optional)…" field |
| `use_weather` | boolean |  |  |
| `count` | integer |  |  |

```json
{
  "source": "vault",
  "item_ids": [
    "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
  ],
  "fabric_asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "occasion": "owambe",
  "mood": "string",
  "note": "string",
  "use_weather": true,
  "count": 0
}
```

**Responses**

- **202**: Accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide
- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /looks/jobs/{job_id}`

**Poll job progress**

`MVP` Polling fallback for clients that cannot hold an SSE connection. Poll every 2 seconds.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `job_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` / `analyzing` / `assembling` / `rendering` / `done` / `failed` | yes |  |
| `progress` | integer | yes |  |
| `label` | string |  |  |
| `result` | object |  |  |
| `result.look_ids` | array of string (uuid) |  |  |
| `error` | object |  |  |
| `error.reason_code` | `empty_pool` / `model_unavailable` / `render_failed` / `budget_exceeded` / `guardrail_blocked` / `timeout` / `internal` |  |  |
| `error.message` | string |  | User-safe copy matching the designed error state |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "progress": 0,
  "label": "Building your fit…",
  "result": {
    "look_ids": [
      "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
    ]
  },
  "error": {
    "reason_code": "empty_pool",
    "message": "string"
  }
}
```

- **404**: Not found
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /looks/jobs/{job_id}/stream`

**Stream job progress (SSE)**

`MVP` Server-sent events. Event names: `progress`, `done`, `failed`.
The connection closes after a terminal event. On disconnect, reconnect or
fall back to polling — progress is server-side state, so nothing is lost.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `job_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: Event stream

  Body (`text/event-stream`):

```json
"string"
```


### `GET /looks`

**List looks**

`MVP` Recent and saved looks, matching the dashboard sections.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `filter` | query | `recent` / `saved` / `all` |  |  |
| `occasion` | query | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `cursor` | query | string |  | Opaque cursor from the previous page's `next_cursor`. |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `next_cursor` | string or null | yes |  |
| `has_more` | boolean | yes |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].look_id` | string (uuid) | yes |  |
| `items[].title` | string | yes |  |
| `items[].image_url` | string (uri) | yes |  |
| `items[].occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `items[].is_saved` | boolean |  |  |
| `items[].created_at` | string (date-time) | yes |  |

```json
{
  "next_cursor": "string",
  "has_more": true,
  "items": [
    {
      "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "title": "Cultural Evening Flow",
      "image_url": "https://example.com/...",
      "occasion": "owambe",
      "is_saved": true,
      "created_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```


### `GET /looks/{look_id}`

**Get a look**

`MVP` Full detail including items, reasoning, and the "Why this works for you" explanation.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `look_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `image_url` | string (uri) | yes |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `is_saved` | boolean |  |  |
| `created_at` | string (date-time) | yes |  |
| `description` | string | yes | The look's summary paragraph |
| `why_this_works` | string or null |  | Personalised explanation referencing the user's Style DNA |
| `generated_by_ai` | boolean |  | When true the app shows the "generated by FAUE AI" attribution |
| `renderer` | `generative` / `composite` / `hybrid` |  |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].name` | string | yes |  |
| `items[].role` | string | yes |  |
| `items[].vault_item_id` | string or null (uuid) |  | Present when the piece is one the user owns |
| `items[].image_url` | string or null (uri) |  |  |
| `items[].note` | string or null |  |  |

```json
{
  "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "title": "Cultural Evening Flow",
  "image_url": "https://example.com/...",
  "occasion": "owambe",
  "is_saved": true,
  "created_at": "2026-10-13T09:30:00Z",
  "description": "string",
  "why_this_works": "string",
  "generated_by_ai": true,
  "renderer": "generative",
  "items": [
    {
      "name": "Relaxed Linen Shirt",
      "role": "top",
      "vault_item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "image_url": "https://example.com/...",
      "note": "string"
    }
  ]
}
```

- **404**: Not found
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /looks/{look_id}/save`

**Save a look**

`MVP` Idempotent.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: Saved

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `look_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `image_url` | string (uri) | yes |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `is_saved` | boolean |  |  |
| `created_at` | string (date-time) | yes |  |
| `description` | string | yes | The look's summary paragraph |
| `why_this_works` | string or null |  | Personalised explanation referencing the user's Style DNA |
| `generated_by_ai` | boolean |  | When true the app shows the "generated by FAUE AI" attribution |
| `renderer` | `generative` / `composite` / `hybrid` |  |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].name` | string | yes |  |
| `items[].role` | string | yes |  |
| `items[].vault_item_id` | string or null (uuid) |  | Present when the piece is one the user owns |
| `items[].image_url` | string or null (uri) |  |  |
| `items[].note` | string or null |  |  |

```json
{
  "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "title": "Cultural Evening Flow",
  "image_url": "https://example.com/...",
  "occasion": "owambe",
  "is_saved": true,
  "created_at": "2026-10-13T09:30:00Z",
  "description": "string",
  "why_this_works": "string",
  "generated_by_ai": true,
  "renderer": "generative",
  "items": [
    {
      "name": "Relaxed Linen Shirt",
      "role": "top",
      "vault_item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "image_url": "https://example.com/...",
      "note": "string"
    }
  ]
}
```


### `DELETE /looks/{look_id}/save`

**Unsave a look**

`MVP`

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Responses**

- **204**: Unsaved

### `POST /looks/{look_id}/regenerate`

**Regenerate**

`MVP` `Consent: ai_processing` Same inputs, excluding the previous result. Returns a new job.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Responses**

- **202**: Accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```


### `POST /looks/{look_id}/adjust`

**Adjust a look**

`MVP` `Consent: ai_processing` The "Adjust" action. Swap an item or change the occasion; returns a new job.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `swap_item_id` | string (uuid) |  |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `note` | string |  |  |

```json
{
  "swap_item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "occasion": "owambe",
  "note": "string"
}
```

**Responses**

- **202**: Accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```


### `POST /looks/{look_id}/share`

**Create a share image and link**

`MVP` Produces a branded share image and a public `faueofficial.com/look/{id}` URL.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `surface` | `whatsapp` / `instagram` / `x` / `link` / `other` |  |  |

```json
{
  "surface": "whatsapp"
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `share_url` | string (uri) | yes |  |
| `image_url` | string (uri) | yes |  |

```json
{
  "share_url": "https://example.com/...",
  "image_url": "https://example.com/..."
}
```


### `POST /looks/{look_id}/feedback`

**Give feedback**

`MVP` Feeds the behaviour vector and future ranking. Idempotent per look.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `look_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `signal` | `more_like_this` / `not_my_style` | yes |  |
| `reason` | string |  |  |

```json
{
  "signal": "more_like_this",
  "reason": "string"
}
```

**Responses**

- **204**: Recorded

## fabric

Fabric analysis and tailor share

### `POST /fabric/{asset_id}/style`

**Get style suggestions for a fabric**

`MVP` `Consent: ai_processing`

Classifies the fabric and returns 3–5 native styles suited to it, each with
reasoning specific to this fabric and accessory pairings.

Style selection here is rules-first — a wrong match costs the user money at a
tailor. The model classifies and explains; it does not choose.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `asset_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `fabric_type` | `ankara` / `lace` / `aso_oke` / `adire` / `cotton` / `chiffon` / `other` |  |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `constraints` | array of string |  |  |

```json
{
  "fabric_type": "ankara",
  "occasion": "owambe",
  "gender_presentation": "feminine",
  "constraints": [
    "modest",
    "stand_out"
  ]
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `detected_type` | `ankara` / `lace` / `aso_oke` / `adire` / `cotton` / `chiffon` / `other` | yes |  |
| `confidence` | number | yes |  |
| `attributes` | object |  |  |
| `attributes.motif_scale` | `small` / `medium` / `large` |  |  |
| `attributes.weight` | `light` / `medium` / `heavy` |  |  |
| `attributes.dominant_colors` | array of string |  |  |
| `styles` | array of object | yes |  |
| `styles[]` | object |  |  |
| `styles[].style_id` | string (uuid) | yes |  |
| `styles[].name` | string | yes |  |
| `styles[].reference_image_url` | string (uri) |  |  |
| `styles[].reason` | string | yes | Why this style suits this specific fabric |
| `styles[].formality` | `casual` / `smart_casual` / `formal` / `ceremonial` |  |  |
| `styles[].accessories` | array of object |  |  |
| `styles[].accessories[]` | object |  |  |
| `styles[].accessories[].name` | string |  |  |
| `styles[].accessories[].image_url` | string or null (uri) |  |  |
| `styles[].accessories[].note` | string |  |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "detected_type": "ankara",
  "confidence": 0,
  "attributes": {
    "motif_scale": "small",
    "weight": "light",
    "dominant_colors": [
      "string"
    ]
  },
  "styles": [
    {
      "style_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "name": "Fitted Kaftan with Side Slit",
      "reference_image_url": "https://example.com/...",
      "reason": "string",
      "formality": "casual",
      "accessories": [
        {
          "name": "string",
          "image_url": "https://example.com/...",
          "note": "string"
        }
      ]
    }
  ]
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /fabric/{asset_id}/tailor-share`

**Create a tailor-ready share image**

`MVP` Composites the fabric photograph, the chosen style reference, the user's
notes, and FAUE branding into one image suitable for WhatsApp.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `asset_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `style_id` | string (uuid) | yes |  |
| `notes` | string |  | Measurements or instructions for the tailor |

```json
{
  "style_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "notes": "string"
}
```

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `image_url` | string (uri) | yes |  |

```json
{
  "image_url": "https://example.com/..."
}
```


## spree

Conversational styling

### `POST /spree/sessions`

**Start a styling conversation**

`MVP` `Consent: ai_processing`

**Auth:** bearer token

**Responses**

- **201**: Created

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `session_id` | string (uuid) | yes |  |

```json
{
  "session_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /spree/sessions/{session_id}/messages`

**Send a message**

`MVP` `Consent: ai_processing`

Streams the reply as SSE. Images must be `ready` assets.

Off-topic or unsafe input returns a templated refusal without a model call —
that is expected behaviour, not an error.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `session_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `text` | string |  |  |
| `asset_ids` | array of string (uuid) |  |  |

```json
{
  "text": "string",
  "asset_ids": [
    "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
  ]
}
```

**Responses**

- **200**: SSE stream of the reply

  Body (`text/event-stream`):

```json
"string"
```

- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /spree/sessions/{session_id}`

**Get conversation history**

`MVP` Retention is TTL-bounded; older messages may be absent.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `session_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `session_id` | string (uuid) | yes |  |
| `messages` | array of object | yes |  |
| `messages[]` | object |  |  |
| `messages[].role` | `user` / `assistant` | yes |  |
| `messages[].content` | string | yes |  |
| `messages[].image_urls` | array of string (uri) |  |  |
| `messages[].refused` | boolean |  | True when a guardrail produced a templated refusal |
| `messages[].created_at` | string (date-time) | yes |  |

```json
{
  "session_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "messages": [
    {
      "role": "user",
      "content": "string",
      "image_urls": [
        "https://example.com/..."
      ],
      "refused": true,
      "created_at": "2026-10-13T09:30:00Z"
    }
  ]
}
```


## agent

Proactive daily styling

### `GET /agent/today`

**Today's suggestion**

`MVP` `Consent: personalization`

The dashboard's "What are you wearing today?" content. Returns the current
suggestion, generating one on demand if none exists for today.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `run_id` | string (uuid) | yes |  |
| `look` | object | yes |  |
| `look.look_id` | string (uuid) | yes |  |
| `look.title` | string | yes |  |
| `look.image_url` | string (uri) | yes |  |
| `look.occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `look.is_saved` | boolean |  |  |
| `look.created_at` | string (date-time) | yes |  |
| `trigger` | `daily` / `weather` / `event` / `proactive` / `on_demand` | yes |  |
| `rationale` | string |  | Answers "why this?" from stored facts, not a fresh model guess. |
| `weather` | object |  |  |
| `weather.temp_c` | number |  |  |
| `weather.condition` | string |  |  |
| `weather.rain_probability` | number |  |  |
| `weather.dust_index` | number or null |  | Harmattan season dust level |
| `generated_at` | string (date-time) | yes |  |

```json
{
  "run_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "look": {
    "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "title": "Cultural Evening Flow",
    "image_url": "https://example.com/...",
    "occasion": "owambe",
    "is_saved": true,
    "created_at": "2026-10-13T09:30:00Z"
  },
  "trigger": "daily",
  "rationale": "string",
  "weather": {
    "temp_c": 0,
    "condition": "string",
    "rain_probability": 0,
    "dust_index": 0
  },
  "generated_at": "2026-10-13T09:30:00Z"
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /agent/settings`

**Get agent settings**

`M1-2`

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `daily_enabled` | boolean |  |  |
| `daily_hour_local` | integer |  |  |
| `use_weather` | boolean |  |  |
| `autonomy_level` | integer |  | 0 on-open, 1 daily push, 2 proactive triggers, 3 planning |

```json
{
  "daily_enabled": true,
  "daily_hour_local": 0,
  "use_weather": true,
  "autonomy_level": 0
}
```


### `PUT /agent/settings`

**Update agent settings**

`M1-2` `Consent: agent_proactive` for daily suggestions.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `daily_enabled` | boolean |  |  |
| `daily_hour_local` | integer |  |  |
| `use_weather` | boolean |  |  |
| `autonomy_level` | integer |  | 0 on-open, 1 daily push, 2 proactive triggers, 3 planning |

```json
{
  "daily_enabled": true,
  "daily_hour_local": 0,
  "use_weather": true,
  "autonomy_level": 0
}
```

**Responses**

- **200**: Updated

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `daily_enabled` | boolean |  |  |
| `daily_hour_local` | integer |  |  |
| `use_weather` | boolean |  |  |
| `autonomy_level` | integer |  | 0 on-open, 1 daily push, 2 proactive triggers, 3 planning |

```json
{
  "daily_enabled": true,
  "daily_hour_local": 0,
  "use_weather": true,
  "autonomy_level": 0
}
```


### `POST /agent/suggestions/{run_id}/respond`

**Respond to a suggestion**

`MVP` Accept, dismiss, or request another. Feeds agent memory.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `run_id` | path | string (uuid) | yes |  |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `outcome` | `accepted` / `dismissed` / `regenerate` | yes |  |

```json
{
  "outcome": "accepted"
}
```

**Responses**

- **204**: Recorded

## integrations

Pinterest

### `GET /integrations`

**List connected accounts**

`MVP` Backs the Connected Accounts screen. Instagram is not offered — the platform API cannot deliver what it would promise.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `` | array of object |  |  |
| `[]` | object |  |  |
| `[].provider` | `pinterest` | yes |  |
| `[].connected` | boolean | yes |  |
| `[].connected_at` | string or null (date-time) |  |  |
| `[].last_sync_at` | string or null (date-time) |  |  |
| `[].boards_imported` | integer |  |  |
| `[].pins_imported` | integer |  |  |
| `[].status` | `active` / `needs_reauth` / `revoked` / `syncing` |  |  |

```json
[
  {
    "provider": "pinterest",
    "connected": true,
    "connected_at": "2026-10-13T09:30:00Z",
    "last_sync_at": "2026-10-13T09:30:00Z",
    "boards_imported": 0,
    "pins_imported": 0,
    "status": "active"
  }
]
```


### `GET /integrations/pinterest/authorize`

**Begin Pinterest connection**

`MVP` `Consent: pinterest_sync` Returns an OAuth2 + PKCE authorization URL. Read-only scopes only.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `authorize_url` | string (uri) | yes |  |
| `state` | string | yes |  |

```json
{
  "authorize_url": "https://example.com/...",
  "state": "string"
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /integrations/pinterest/callback`

**OAuth callback**

`MVP` Called by Pinterest. Exchanges the code, stores encrypted tokens, and redirects back into the app.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `code` | query | string | yes |  |
| `state` | query | string | yes |  |

**Responses**

- **302**: Redirect into the app

### `GET /integrations/pinterest/boards`

**List boards**

`MVP` The user chooses which boards to import. Never import everything by default.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `` | array of object |  |  |
| `[]` | object |  |  |
| `[].board_id` | string | yes |  |
| `[].name` | string | yes |  |
| `[].pin_count` | integer | yes |  |
| `[].cover_image_url` | string or null (uri) |  |  |
| `[].imported` | boolean |  |  |

```json
[
  {
    "board_id": "string",
    "name": "string",
    "pin_count": 0,
    "cover_image_url": "https://example.com/...",
    "imported": true
  }
]
```


### `POST /integrations/pinterest/import`

**Import selected boards**

`MVP` Asynchronous. Pins are cached through the PII pipeline and embedded into the aspiration vector.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `board_ids` | array of string | yes |  |

```json
{
  "board_ids": [
    "string"
  ]
}
```

**Responses**

- **202**: Import started

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```


### `DELETE /integrations/{provider}`

**Disconnect**

`MVP` Revokes the upstream token, deletes cached pins, and removes the aspiration vector.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `provider` | path | `pinterest` | yes |  |

**Responses**

- **204**: Disconnected

## notifications

Inbox, preferences, device tokens

### `GET /notifications`

**Notification inbox**

`MVP` Backs the Notification screen. `category` maps to its All / Style / Activity tabs.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `category` | query | `style` / `activity` |  |  |
| `cursor` | query | string |  | Opaque cursor from the previous page's `next_cursor`. |
| `limit` | query | integer |  |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `next_cursor` | string or null | yes |  |
| `has_more` | boolean | yes |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].notification_id` | string (uuid) | yes |  |
| `items[].title` | string | yes |  |
| `items[].body` | string |  |  |
| `items[].category` | `style` / `activity` | yes |  |
| `items[].deeplink` | string or null (uri) |  |  |
| `items[].image_url` | string or null (uri) |  |  |
| `items[].read` | boolean | yes |  |
| `items[].created_at` | string (date-time) | yes |  |
| `unread_count` | integer | yes |  |

```json
{
  "next_cursor": "string",
  "has_more": true,
  "items": [
    {
      "notification_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "title": "New Style Generated",
      "body": "Your Crimson Elegance look is ready to explore",
      "category": "style",
      "deeplink": "https://example.com/...",
      "image_url": "https://example.com/...",
      "read": true,
      "created_at": "2026-10-13T09:30:00Z"
    }
  ],
  "unread_count": 0
}
```


### `POST /notifications/{notification_id}/read`

**Mark as read**

`MVP`

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `notification_id` | path | string (uuid) | yes |  |

**Responses**

- **204**: Marked

### `GET /notifications/preferences`

**Get preferences**

`MVP` Per category and channel, plus quiet hours.

**Auth:** bearer token

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `` | array of object |  |  |
| `[]` | object |  |  |
| `[].category` | `style` / `activity` / `marketing` | yes |  |
| `[].channel` | `push` / `email` / `whatsapp` / `sms` / `inbox` | yes |  |
| `[].enabled` | boolean | yes |  |
| `[].quiet_hours_start` | integer or null |  |  |
| `[].quiet_hours_end` | integer or null |  |  |

```json
[
  {
    "category": "style",
    "channel": "push",
    "enabled": true,
    "quiet_hours_start": 0,
    "quiet_hours_end": 0
  }
]
```


### `PUT /notifications/preferences`

**Update preferences**

`MVP`

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `` | array of object |  |  |
| `[]` | object |  |  |
| `[].category` | `style` / `activity` / `marketing` | yes |  |
| `[].channel` | `push` / `email` / `whatsapp` / `sms` / `inbox` | yes |  |
| `[].enabled` | boolean | yes |  |
| `[].quiet_hours_start` | integer or null |  |  |
| `[].quiet_hours_end` | integer or null |  |  |

```json
[
  {
    "category": "style",
    "channel": "push",
    "enabled": true,
    "quiet_hours_start": 0,
    "quiet_hours_end": 0
  }
]
```

**Responses**

- **200**: Updated

### `POST /notifications/devices`

**Register a device token**

`MVP` Tokens are deleted on logout and on account deletion.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `platform` | `ios` / `android` / `web` | yes |  |
| `token` | string | yes |  |

```json
{
  "platform": "ios",
  "token": "string"
}
```

**Responses**

- **201**: Registered

## uploads

Signed upload credentials

### `POST /uploads/sign`

**Get signed upload credentials**

`MVP` `Consent: camera_photos`

Returns a short-lived, single-use upload URL. `PUT` the image to it.

**Not direct-to-CDN.** The bytes reach the gateway so the PII pipeline
can run before anything is stored — a direct upload would put the
unredacted original on the CDN, including images that are then
rejected.

After upload the asset enters the PII pipeline — safety classification, EXIF
strip, face redaction, OCR redaction. Until `status` is `ready` the asset
cannot be referenced by other endpoints.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `kind` | `fabric` / `vault_item` / `fit` / `avatar` | yes |  |
| `content_type` | `image/jpeg` / `image/png` / `image/heic` / `image/webp` | yes |  |
| `byte_size` | integer |  | Maximum 20 MB |

```json
{
  "kind": "fabric",
  "content_type": "image/jpeg",
  "byte_size": 0
}
```

**Responses**

- **201**: Credentials issued

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `upload_url` | string (uri) | yes |  |
| `fields` | object |  | Form fields to include with the upload |
| `expires_at` | string (date-time) | yes |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "upload_url": "https://example.com/...",
  "fields": {},
  "expires_at": "2026-10-13T09:30:00Z"
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /uploads/{asset_id}`

**Get asset status**

`MVP` Poll after uploading. `status` is `processing`, `ready`, or `rejected`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `asset_id` | path | string (uuid) | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `status` | `processing` / `ready` / `rejected` | yes |  |
| `url` | string or null (uri) |  | The redacted derivative. The original is not exposed. |
| `rejection_reason` | `unsafe_content` / `not_apparel` / `unreadable` / `too_large` / null |  |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "processing",
  "url": "https://example.com/...",
  "rejection_reason": "unsafe_content"
}
```

- **404**: Not found
  - body: `application/problem+json`, see *Errors* in the guide

### `PUT /uploads/{asset_id}`

**Upload the image bytes**

`MVP` `Consent: camera_photos`

Where the bytes go after `POST /uploads/sign`. Send the image as `multipart/form-data` with one
field, `file`. The PII pipeline runs in memory and only the redacted derivative is stored.
Then poll `GET /uploads/{asset_id}` until `status` is `ready` or `rejected`.

**Auth:** bearer token

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `asset_id` | path | string (uuid) | yes |  |

**Request body** (`multipart/form-data`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `file` | string (binary) | yes |  |

```json
{
  "file": "string"
}
```

**Responses**

- **200**: Accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `processing` / `ready` / `rejected` |  |  |

```json
{
  "status": "processing"
}
```

- **403**: A required consent purpose has not been granted. Present the consent surface for the purpose named in `errors[0].field`, not a generic error.
  - body: `application/problem+json`, see *Errors* in the guide
- **404**: Not found
  - body: `application/problem+json`, see *Errors* in the guide
- **413**: Larger than the upload limit

## privacy

Data subject rights

### `POST /privacy/export`

**Request a data export**

`MVP` Asynchronous. Produces a downloadable archive of everything held about the user.

**Auth:** bearer token

**Responses**

- **202**: Accepted

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```


### `POST /privacy/delete`

**Delete the account**

`MVP` Irreversible. Fans out deletion across every module and third party, with
a 30-day completion SLA.

Required by the App Store for any app offering Sign in with Apple, so this is
launch-blocking rather than optional.

**Auth:** bearer token

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `confirm` | boolean | yes |  |
| `reason` | string |  |  |

```json
{
  "confirm": true,
  "reason": "string"
}
```

**Responses**

- **202**: Deletion started

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `ledger_id` | string (uuid) | yes |  |
| `sla_due_at` | string (date-time) | yes |  |

```json
{
  "ledger_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "sla_due_at": "2026-10-13T09:30:00Z"
}
```


### `POST /privacy/restrict`

**Restrict processing**

`MVP` Pauses all optional processing while retaining the account.

**Auth:** bearer token

**Responses**

- **204**: Restricted

## contact

Messages from the website's contact and partners forms

### `POST /contact`

**Send a message to the FAUE team**

`MVP` Saves a message from the website's contact or partners form and emails
the FAUE team. **No sign-in needed**: the sender may have no account. If a
valid access token is sent the message is linked to that account; an invalid
one is ignored rather than refused.

**Retention:** the sender's name, email address, message and any partner
details are deleted **72 hours** after they arrive. Only a reference, the
topic and dates remain. The privacy notice says the same; change both together.

`Idempotency-Key` is required. A retry with the same key returns the original
reference and creates nothing new. Limited to 5 per hour and 20 per day per IP
address; beyond that the answer is `429` with `Retry-After`.

`website` is a honeypot. People never see it, and a non-empty value is answered
exactly like a success while nothing is stored.

`topic: press_partnership` is delivered to the partners mailbox and may carry
`partner_type`, `organisation` and `role`; every other topic goes to the
general mailbox.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `Idempotency-Key` | header | string | yes | Unique per submission, printable characters only. |

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `topic` | `support` / `data_request` / `press_partnership` / `other` | yes |  |
| `name` | string | yes |  |
| `email` | string (email) | yes |  |
| `message` | string | yes |  |
| `reference_code` | string |  | The reference an app error showed, so support can find that request. |
| `partner_type` | `tailor` / `designer` / `fabric_seller` / `event_planner` / `stylist_creator` / `media` / `other` |  |  |
| `organisation` | string |  |  |
| `role` | string |  |  |
| `policy_version` | string | yes | The privacy policy version the sender saw and agreed to. |
| `website` | string |  | Honeypot. Must be empty. |

```json
{
  "topic": "support",
  "name": "string",
  "email": "ada@example.com",
  "message": "string",
  "reference_code": "string",
  "partner_type": "tailor",
  "organisation": "string",
  "role": "string",
  "policy_version": "string",
  "website": "string"
}
```

**Responses**

- **202**: Saved. The team is emailed asynchronously; the sender is not told whether that has happened.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `reference` | string | yes | Short code to quote when following up. |

```json
{
  "reference": "FAUE-7K4M2Q"
}
```

- **400**: `idempotency_key_required` — the header is missing or malformed.
  - body: `application/problem+json`, see *Errors* in the guide
- **422**: A field failed validation. Nothing was saved.
- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

## early-access

Pre-launch waitlist, joined from the website after taking the quiz

### `POST /early-access`

**Join the waitlist**

`MVP` Reserves a username and puts an email address on the waitlist, with the
Style DNA the person just got. **No sign-in needed.**

The answers are scored again on the server and stored with the signup. The
response carries the card for those answers, so the website can show it as the
reward for joining in one round trip.

The username is a **reservation**: when someone signs up with the same email
address they can take it with `POST /auth/username`, and nobody else can. A
handle that is reserved, in use, or reads as official (`admin`, `faue`,
`support`, ...) returns **409** `username_taken` with `username` as the field.

An address that is already on the list is answered exactly like a first
submission, so the response cannot be used to find out who has joined. A
confirmation email is sent once.

`consent` must be `true` and `policy_version` is stored with the signup.
`website` is a honeypot. Limited to 5 per hour and 20 per day per IP address.

**Auth:** none

**Request body** (`application/json`)

| Field | Type | Required | Notes |
|---|---|---|---|
| `email` | string (email) | yes |  |
| `username` | string | yes |  |
| `quiz_version` | string | yes |  |
| `answers` | object | yes | Question id to the chosen option id, or to a list of option ids when the question takes more than one (`max_choices` in `GET /quiz`). A single choice may be sent as a plain string. Order and repeats do not matter. |
| `answers.<key>` | string or array |  |  |
| `gender` | `female` / `male` / `prefer_not_to_say` |  | From the waitlist form's dropdown. Optional so a client that predates it keeps working. It only decides which model photograph sits behind the person's card: `female` and `male` get a photograph from their own Style DNA, and `prefer_not_to_say` (or leaving it out) gets the plain card. |
| `consent` | `true` | yes | Agreement to be emailed when FAUE opens. |
| `policy_version` | string | yes |  |
| `website` | string |  | Honeypot. Must be empty. |

```json
{
  "email": "ada@example.com",
  "username": "string",
  "quiz_version": "string",
  "answers": {
    "1": [
      "A",
      "C"
    ],
    "2": "C",
    "3": "D",
    "4": [
      "A",
      "D"
    ],
    "5": "A",
    "6": "A"
  },
  "gender": "female",
  "consent": true,
  "policy_version": "string",
  "website": "string"
}
```

**Responses**

- **202**: On the list.

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `joined` | yes |  |
| `username` | string | yes | The name asked for, echoed back. Never what is stored. |
| `dna` | object | yes | The result for the submitted answers. `dna.card_urls` carries signed image addresses for the person's own card (`stories_url` 9:16, `square_url` 4:5) and `share_url`, the public page whose link preview shows the card. |
| `dna.quiz_version` | string | yes |  |
| `dna.dominant` | object | yes |  |
| `dna.dominant.id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `dna.dominant.name` | string | yes |  |
| `dna.dominant.percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `dna.dominant.gradient_from` | string |  |  |
| `dna.dominant.gradient_to` | string |  |  |
| `dna.alter_ego` | object or null |  |  |
| `dna.wildcard` | object or null |  |  |
| `dna.tagline` | string |  | Tier 1 persona line. Fixed per persona. |
| `dna.blend_line` | string |  | Tier 2. Varies by dominant x alter-ego pair; 30 hand-written variants. |
| `dna.personal_line` | string or null |  | Tier 3 (M1-2). Generated once from the answer pattern, then frozen. Null when absent — close the layout up rather than leaving a gap. |
| `dna.scores` | object | yes | Raw scores per persona id. Display uses the percentages on each persona. |
| `dna.scores.<key>` | number |  |  |
| `dna.card_urls` | object |  |  |
| `dna.card_urls.status` | `pending` / `ready` / `failed` | yes |  |
| `dna.card_urls.square_url` | string or null (uri) |  |  |
| `dna.card_urls.stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `dna.card_urls.share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |
| `dna.completed_at` | string (date-time) | yes |  |
| `dna.retake_available_at` | string (date-time) |  |  |
| `card_photo` | `f1` / `f2` / `m1` / `m2` / null |  | Which model photograph is behind the card, or null for the plain card. |

```json
{
  "status": "joined",
  "username": "string",
  "dna": {
    "quiz_version": "string",
    "dominant": {
      "id": "CM",
      "name": "The Cultural Minimalist",
      "percentage": 0,
      "gradient_from": "#0F3D2E",
      "gradient_to": "#355C4F"
    },
    "alter_ego": {
      "id": "CM",
      "name": "The Cultural Minimalist",
      "percentage": 0,
      "gradient_from": "#0F3D2E",
      "gradient_to": "#355C4F"
    },
    "wildcard": {
      "id": "CM",
      "name": "The Cultural Minimalist",
      "percentage": 0,
      "gradient_from": "#0F3D2E",
      "gradient_to": "#355C4F"
    },
    "tagline": "string",
    "blend_line": "string",
    "personal_line": "string",
    "scores": {
      "<key>": 0
    },
    "card_urls": {
      "status": "pending",
      "square_url": "https://example.com/...",
      "stories_url": "https://example.com/...",
      "share_url": "https://example.com/..."
    },
    "completed_at": "2026-10-13T09:30:00Z",
    "retake_available_at": "2026-10-13T09:30:00Z"
  },
  "card_photo": "f1"
}
```

- **409**: `username_taken`
  - body: `application/problem+json`, see *Errors* in the guide
- **422**: A field failed validation. Nothing was saved.
- **429**: Too many requests
  - body: `application/problem+json`, see *Errors* in the guide

## cards

Style DNA cards as images, and the public page behind a shared card

### `GET /cards/dna.png`

**A Style DNA card as a PNG**

`MVP` **No sign-in needed**, because email clients and link previews load it.

Draws one card. The address is **signed**: it carries the personas, percentages, handle, shape and
photograph plus a `sig` the server made, so only a card the server issued can be drawn. Take the
full address from `dna.card_urls` or `images` in `GET /dna/{token}`; do not build one.

A changed or unsigned address returns **401**. The image never changes for an address, so it is
sent with `Cache-Control: public, max-age=31536000, immutable`.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `p` | query | string | yes | Persona id and percentage, dominant first. |
| `w` | query | integer |  | Width in pixels. Height follows the shape. |
| `a` | query | `4x5` / `9x16` / `og` |  | `9x16` for Stories, `4x5` for a feed post, `og` (1200x630) for link previews. |
| `u` | query | string |  | The handle signed on the card. |
| `pl` | query | `signature` / `tag` / `chip` / `trait` |  |  |
| `ph` | query | `f1` / `f2` / `m1` / `m2` |  | The model photograph behind the card. |
| `sig` | query | string | yes | Server signature over the other parameters. |

**Responses**

- **200**: The card
  - body: `image/png` (binary image)
- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

### `GET /dna/{token}`

**The data behind a shared Style DNA card**

`MVP` **No sign-in needed.** What the public share page and its link preview are built from.

`token` is the last part of a `share_url` (`https://faueofficial.com/dna/<token>`). It is signed by
the server and carries the personas, percentages, handle and photograph, so only an issued card can
be shown and nothing about the person is looked up. A changed or invented token returns **401**.
The answer never changes for a token and is cached for an hour.

Apps can use it to render a native "shared card" screen from a link they receive.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `token` | path | string | yes |  |

**Responses**

- **200**: The card

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string or null | yes | The handle signed on the card, if it has one. |
| `persona` | string | yes |  |
| `persona_id` | string | yes |  |
| `percentage` | integer | yes | The dominant persona percentage. |
| `blend` | array of object | yes | Dominant first. Percentages total 100. |
| `blend[]` | object |  |  |
| `blend[].id` | string | yes |  |
| `blend[].name` | string | yes |  |
| `blend[].percentage` | integer | yes |  |
| `tagline` | string | yes |  |
| `blend_line` | string |  |  |
| `title` | string | yes |  |
| `description` | string | yes |  |
| `images` | object | yes |  |
| `images.preview` | string (uri) | yes | 1200x630, for link previews. |
| `images.story` | string (uri) | yes | 1080x1920. |
| `images.post` | string (uri) | yes | 1080x1350. |

```json
{
  "username": "string",
  "persona": "The Cultural Minimalist",
  "persona_id": "CM",
  "percentage": 0,
  "blend": [
    {
      "id": "CE",
      "name": "Corporate Edge",
      "percentage": 0
    }
  ],
  "tagline": "string",
  "blend_line": "string",
  "title": "ada_obi is The Cultural Minimalist on FAUE",
  "description": "string",
  "images": {
    "preview": "https://example.com/...",
    "story": "https://example.com/...",
    "post": "https://example.com/..."
  }
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

## unsubscribe

Stopping email, without signing in

### `GET /unsubscribe/{token}`

**What an unsubscribe link is for**

`MVP` **No sign-in needed.** Says what the link would turn off, and changes nothing, so a mail
scanner that opens every link in a message cannot unsubscribe anyone. `category` is `waitlist`
(leave the list, releasing the reserved username) or an account category such as `marketing`.
A forged or damaged token returns **401**.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `token` | path | string | yes |  |

**Responses**

- **200**: OK

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | string | yes |  |

```json
{
  "category": "waitlist"
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

### `POST /unsubscribe/{token}`

**Unsubscribe**

`MVP` **No sign-in needed.** The token is the credential. Also what a mail client's own one-click
Unsubscribe button posts to (RFC 8058, from the `List-Unsubscribe` header). Idempotent: repeating
it, or using a link for an entry that no longer exists, still answers 200.

**Auth:** none

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `token` | path | string | yes |  |

**Responses**

- **200**: Done

  Body (`application/json`):

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | string | yes |  |
| `unsubscribed` | `true` | yes |  |

```json
{
  "category": "waitlist",
  "unsubscribed": true
}
```

- **401**: Missing, invalid, or expired credentials
  - body: `application/problem+json`, see *Errors* in the guide

## Schemas

### Problem

| Field | Type | Required | Notes |
|---|---|---|---|
| `type` | string | yes | Stable machine-readable code. Branch on this, never on `title`. |
| `title` | string | yes |  |
| `status` | integer | yes |  |
| `detail` | string |  | Human-readable. Safe to log, never shown raw to users. |
| `instance` | string |  | Trace id for support |
| `errors` | array of object |  |  |
| `errors[]` | object |  |  |
| `errors[].field` | string |  |  |
| `errors[].code` | string |  |  |
| `errors[].message` | string |  |  |

```json
{
  "type": "consent_required",
  "title": "Consent required",
  "status": 403,
  "detail": "string",
  "instance": "string",
  "errors": [
    {
      "field": "string",
      "code": "string",
      "message": "string"
    }
  ]
}
```

### Page

| Field | Type | Required | Notes |
|---|---|---|---|
| `next_cursor` | string or null | yes |  |
| `has_more` | boolean | yes |  |

```json
{
  "next_cursor": "string",
  "has_more": true
}
```

### Session

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes | How to present the access token. |
| `expires_in` | integer | yes | Seconds until the access token expires. |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes | Seconds until the refresh token expires. |
| `is_new_user` | boolean | yes | Route to onboarding rather than the dashboard. |
| `onboarding` | object | yes | Included on sign-in so the app can route straight from the auth screen without a second call. Absent from `/auth/refresh` — refresh runs every twelve minutes and no screen reads this at that moment. |
| `onboarding.username_set` | boolean | yes |  |
| `onboarding.quiz_completed` | boolean | yes |  |
| `onboarding.pinterest_connected` | boolean | yes |  |
| `onboarding.vault_started` | boolean | yes |  |
| `onboarding.body_profile_set` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true,
  "onboarding": {
    "username_set": true,
    "quiz_completed": true,
    "pinterest_connected": true,
    "vault_started": true,
    "body_profile_set": true
  }
}
```

### RefreshedSession

| Field | Type | Required | Notes |
|---|---|---|---|
| `access_token` | string | yes |  |
| `token_type` | `Bearer` | yes |  |
| `expires_in` | integer | yes |  |
| `refresh_token` | string | yes |  |
| `refresh_expires_in` | integer | yes |  |
| `is_new_user` | boolean | yes |  |

```json
{
  "access_token": "string",
  "token_type": "Bearer",
  "expires_in": 900,
  "refresh_token": "string",
  "refresh_expires_in": 2592000,
  "is_new_user": true
}
```

### Profile

| Field | Type | Required | Notes |
|---|---|---|---|
| `user_id` | string (uuid) | yes |  |
| `username` | string or null | yes |  |
| `display_name` | string or null |  |  |
| `gender_presentation` | `feminine` / `masculine` / `fluid` / `prefer_not_to_say` / null |  |  |
| `city` | string or null |  |  |
| `locale` | string |  |  |
| `avatar_url` | string or null (uri) |  |  |
| `created_at` | string (date-time) |  |  |

```json
{
  "user_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "username": "string",
  "display_name": "string",
  "gender_presentation": "feminine",
  "city": "string",
  "locale": "en-NG",
  "avatar_url": "https://example.com/...",
  "created_at": "2026-10-13T09:30:00Z"
}
```

### OnboardingState

| Field | Type | Required | Notes |
|---|---|---|---|
| `username_set` | boolean | yes |  |
| `quiz_completed` | boolean | yes |  |
| `pinterest_connected` | boolean | yes |  |
| `vault_started` | boolean | yes |  |
| `body_profile_set` | boolean | yes |  |

```json
{
  "username_set": true,
  "quiz_completed": true,
  "pinterest_connected": true,
  "vault_started": true,
  "body_profile_set": true
}
```

### GenderPresentation

```json
"feminine"
```

### BodyProfile

| Field | Type | Required | Notes |
|---|---|---|---|
| `body_shape` | `hourglass` / `pear` / `rectangle` / `inverted_triangle` / `apple` / `triangle` / `oval` / null |  |  |
| `height_cm` | integer or null |  |  |
| `fit_preference` | `fitted` / `regular` / `relaxed` / null |  |  |
| `sizes_by_category` | object |  |  |
| `sizes_by_category.<key>` | string |  |  |
| `measurements` | object or null |  | Optional expansion. Absent for most users. |

```json
{
  "body_shape": "hourglass",
  "height_cm": 0,
  "fit_preference": "fitted",
  "sizes_by_category": {
    "tops": "M",
    "bottoms": "32",
    "shoes": "43"
  },
  "measurements": {
    "<key>": 0
  }
}
```

### Consent

| Field | Type | Required | Notes |
|---|---|---|---|
| `purpose` | `essential` / `personalization` / `ai_processing` / `pinterest_sync` / `camera_photos` / `location_weather` / `agent_proactive` / `marketing_comms` / `analytics` | yes |  |
| `granted` | boolean | yes |  |
| `policy_version` | string or null |  |  |
| `granted_at` | string or null (date-time) |  |  |

```json
{
  "purpose": "essential",
  "granted": true,
  "policy_version": "string",
  "granted_at": "2026-10-13T09:30:00Z"
}
```

### ConsentPurpose

```json
"essential"
```

### QuizDefinition

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `questions` | array of object | yes |  |
| `questions[]` | object |  |  |
| `questions[].id` | integer | yes |  |
| `questions[].prompt` | string | yes |  |
| `questions[].subtitle` | string or null |  |  |
| `questions[].progress` | integer |  | Percentage to show on this screen |
| `questions[].max_choices` | integer |  | How many options may be ticked. 1 means a single choice (radio buttons); more means checkboxes, up to this many. Ticked options share the question's weight equally, so choosing more never gives a question a bigger say. Absent from a gateway that predates multiple answers: treat that as 1. |
| `questions[].options` | array of object | yes | Length varies by question — Q6 has three. Build the layout from this. |
| `questions[].options[]` | object |  |  |
| `questions[].options[].id` | string | yes |  |
| `questions[].options[].label` | string | yes |  |
| `questions[].options[].description` | string |  |  |
| `questions[].options[].image_url` | string or null (uri) |  |  |

```json
{
  "quiz_version": "dna-2026-08-v1",
  "questions": [
    {
      "id": 0,
      "prompt": "string",
      "subtitle": "string",
      "progress": 0,
      "max_choices": 0,
      "options": [
        {
          "id": "A",
          "label": "Minimal",
          "description": "string",
          "image_url": "https://example.com/..."
        }
      ]
    }
  ]
}
```

### DnaResult

| Field | Type | Required | Notes |
|---|---|---|---|
| `quiz_version` | string | yes |  |
| `dominant` | object | yes |  |
| `dominant.id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `dominant.name` | string | yes |  |
| `dominant.percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `dominant.gradient_from` | string |  |  |
| `dominant.gradient_to` | string |  |  |
| `alter_ego` | object or null |  |  |
| `wildcard` | object or null |  |  |
| `tagline` | string |  | Tier 1 persona line. Fixed per persona. |
| `blend_line` | string |  | Tier 2. Varies by dominant x alter-ego pair; 30 hand-written variants. |
| `personal_line` | string or null |  | Tier 3 (M1-2). Generated once from the answer pattern, then frozen. Null when absent — close the layout up rather than leaving a gap. |
| `scores` | object | yes | Raw scores per persona id. Display uses the percentages on each persona. |
| `scores.<key>` | number |  |  |
| `card_urls` | object |  |  |
| `card_urls.status` | `pending` / `ready` / `failed` | yes |  |
| `card_urls.square_url` | string or null (uri) |  |  |
| `card_urls.stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `card_urls.share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |
| `completed_at` | string (date-time) | yes |  |
| `retake_available_at` | string (date-time) |  |  |

```json
{
  "quiz_version": "string",
  "dominant": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "alter_ego": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "wildcard": {
    "id": "CM",
    "name": "The Cultural Minimalist",
    "percentage": 0,
    "gradient_from": "#0F3D2E",
    "gradient_to": "#355C4F"
  },
  "tagline": "string",
  "blend_line": "string",
  "personal_line": "string",
  "scores": {
    "<key>": 0
  },
  "card_urls": {
    "status": "pending",
    "square_url": "https://example.com/...",
    "stories_url": "https://example.com/...",
    "share_url": "https://example.com/..."
  },
  "completed_at": "2026-10-13T09:30:00Z",
  "retake_available_at": "2026-10-13T09:30:00Z"
}
```

### PersonaResult

| Field | Type | Required | Notes |
|---|---|---|---|
| `id` | `CM` / `OR` / `SL` / `SC` / `CE` / `NF` | yes |  |
| `name` | string | yes |  |
| `percentage` | integer | yes | Percentages across shown personas total exactly 100 |
| `gradient_from` | string |  |  |
| `gradient_to` | string |  |  |

```json
{
  "id": "CM",
  "name": "The Cultural Minimalist",
  "percentage": 0,
  "gradient_from": "#0F3D2E",
  "gradient_to": "#355C4F"
}
```

### CardUrls

| Field | Type | Required | Notes |
|---|---|---|---|
| `status` | `pending` / `ready` / `failed` | yes |  |
| `square_url` | string or null (uri) |  |  |
| `stories_url` | string or null (uri) |  | A 1080x1920 PNG for Stories, WhatsApp status and TikTok. |
| `share_url` | string or null (uri) |  | The public page for this card. Pasting it into a chat shows a link preview of the card. |

```json
{
  "status": "pending",
  "square_url": "https://example.com/...",
  "stories_url": "https://example.com/...",
  "share_url": "https://example.com/..."
}
```

### SharedCard

| Field | Type | Required | Notes |
|---|---|---|---|
| `username` | string or null | yes | The handle signed on the card, if it has one. |
| `persona` | string | yes |  |
| `persona_id` | string | yes |  |
| `percentage` | integer | yes | The dominant persona percentage. |
| `blend` | array of object | yes | Dominant first. Percentages total 100. |
| `blend[]` | object |  |  |
| `blend[].id` | string | yes |  |
| `blend[].name` | string | yes |  |
| `blend[].percentage` | integer | yes |  |
| `tagline` | string | yes |  |
| `blend_line` | string |  |  |
| `title` | string | yes |  |
| `description` | string | yes |  |
| `images` | object | yes |  |
| `images.preview` | string (uri) | yes | 1200x630, for link previews. |
| `images.story` | string (uri) | yes | 1080x1920. |
| `images.post` | string (uri) | yes | 1080x1350. |

```json
{
  "username": "string",
  "persona": "The Cultural Minimalist",
  "persona_id": "CM",
  "percentage": 0,
  "blend": [
    {
      "id": "CE",
      "name": "Corporate Edge",
      "percentage": 0
    }
  ],
  "tagline": "string",
  "blend_line": "string",
  "title": "ada_obi is The Cultural Minimalist on FAUE",
  "description": "string",
  "images": {
    "preview": "https://example.com/...",
    "story": "https://example.com/...",
    "post": "https://example.com/..."
  }
}
```

### UnsubscribeResult

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | string | yes |  |
| `unsubscribed` | `true` | yes |  |

```json
{
  "category": "waitlist",
  "unsubscribed": true
}
```

### Asset

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `status` | `processing` / `ready` / `rejected` | yes |  |
| `url` | string or null (uri) |  | The redacted derivative. The original is not exposed. |
| `rejection_reason` | `unsafe_content` / `not_apparel` / `unreadable` / `too_large` / null |  |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "processing",
  "url": "https://example.com/...",
  "rejection_reason": "unsafe_content"
}
```

### VaultCategory

```json
"tops"
```

### VaultItem

| Field | Type | Required | Notes |
|---|---|---|---|
| `item_id` | string (uuid) | yes |  |
| `name` | string | yes |  |
| `category` | `tops` / `bottoms` / `native` / `shoes` / `accessories` | yes |  |
| `colors` | array of string |  |  |
| `fabric` | string or null |  |  |
| `brand` | string or null |  |  |
| `notes` | string or null |  |  |
| `image_url` | string (uri) | yes |  |
| `wear_count` | integer |  |  |
| `last_worn_at` | string or null (date-time) |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "name": "string",
  "category": "tops",
  "colors": [
    "string"
  ],
  "fabric": "string",
  "brand": "string",
  "notes": "string",
  "image_url": "https://example.com/...",
  "wear_count": 0,
  "last_worn_at": "2026-10-13T09:30:00Z",
  "created_at": "2026-10-13T09:30:00Z"
}
```

### Occasion

```json
"owambe"
```

### JobEnvelope

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` | yes |  |
| `poll_url` | string (uri) | yes |  |
| `stream_url` | string or null (uri) |  |  |
| `estimated_seconds` | integer |  |  |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "poll_url": "https://example.com/...",
  "stream_url": "https://example.com/...",
  "estimated_seconds": 30
}
```

### JobStatus

| Field | Type | Required | Notes |
|---|---|---|---|
| `job_id` | string (uuid) | yes |  |
| `status` | `queued` / `analyzing` / `assembling` / `rendering` / `done` / `failed` | yes |  |
| `progress` | integer | yes |  |
| `label` | string |  |  |
| `result` | object |  |  |
| `result.look_ids` | array of string (uuid) |  |  |
| `error` | object |  |  |
| `error.reason_code` | `empty_pool` / `model_unavailable` / `render_failed` / `budget_exceeded` / `guardrail_blocked` / `timeout` / `internal` |  |  |
| `error.message` | string |  | User-safe copy matching the designed error state |

```json
{
  "job_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "status": "queued",
  "progress": 0,
  "label": "Building your fit…",
  "result": {
    "look_ids": [
      "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10"
    ]
  },
  "error": {
    "reason_code": "empty_pool",
    "message": "string"
  }
}
```

### LookSummary

| Field | Type | Required | Notes |
|---|---|---|---|
| `look_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `image_url` | string (uri) | yes |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `is_saved` | boolean |  |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "title": "Cultural Evening Flow",
  "image_url": "https://example.com/...",
  "occasion": "owambe",
  "is_saved": true,
  "created_at": "2026-10-13T09:30:00Z"
}
```

### Look

| Field | Type | Required | Notes |
|---|---|---|---|
| `look_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `image_url` | string (uri) | yes |  |
| `occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `is_saved` | boolean |  |  |
| `created_at` | string (date-time) | yes |  |
| `description` | string | yes | The look's summary paragraph |
| `why_this_works` | string or null |  | Personalised explanation referencing the user's Style DNA |
| `generated_by_ai` | boolean |  | When true the app shows the "generated by FAUE AI" attribution |
| `renderer` | `generative` / `composite` / `hybrid` |  |  |
| `items` | array of object | yes |  |
| `items[]` | object |  |  |
| `items[].name` | string | yes |  |
| `items[].role` | string | yes |  |
| `items[].vault_item_id` | string or null (uuid) |  | Present when the piece is one the user owns |
| `items[].image_url` | string or null (uri) |  |  |
| `items[].note` | string or null |  |  |

```json
{
  "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "title": "Cultural Evening Flow",
  "image_url": "https://example.com/...",
  "occasion": "owambe",
  "is_saved": true,
  "created_at": "2026-10-13T09:30:00Z",
  "description": "string",
  "why_this_works": "string",
  "generated_by_ai": true,
  "renderer": "generative",
  "items": [
    {
      "name": "Relaxed Linen Shirt",
      "role": "top",
      "vault_item_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "image_url": "https://example.com/...",
      "note": "string"
    }
  ]
}
```

### FabricType

```json
"ankara"
```

### FabricAnalysis

| Field | Type | Required | Notes |
|---|---|---|---|
| `asset_id` | string (uuid) | yes |  |
| `detected_type` | `ankara` / `lace` / `aso_oke` / `adire` / `cotton` / `chiffon` / `other` | yes |  |
| `confidence` | number | yes |  |
| `attributes` | object |  |  |
| `attributes.motif_scale` | `small` / `medium` / `large` |  |  |
| `attributes.weight` | `light` / `medium` / `heavy` |  |  |
| `attributes.dominant_colors` | array of string |  |  |
| `styles` | array of object | yes |  |
| `styles[]` | object |  |  |
| `styles[].style_id` | string (uuid) | yes |  |
| `styles[].name` | string | yes |  |
| `styles[].reference_image_url` | string (uri) |  |  |
| `styles[].reason` | string | yes | Why this style suits this specific fabric |
| `styles[].formality` | `casual` / `smart_casual` / `formal` / `ceremonial` |  |  |
| `styles[].accessories` | array of object |  |  |
| `styles[].accessories[]` | object |  |  |
| `styles[].accessories[].name` | string |  |  |
| `styles[].accessories[].image_url` | string or null (uri) |  |  |
| `styles[].accessories[].note` | string |  |  |

```json
{
  "asset_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "detected_type": "ankara",
  "confidence": 0,
  "attributes": {
    "motif_scale": "small",
    "weight": "light",
    "dominant_colors": [
      "string"
    ]
  },
  "styles": [
    {
      "style_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
      "name": "Fitted Kaftan with Side Slit",
      "reference_image_url": "https://example.com/...",
      "reason": "string",
      "formality": "casual",
      "accessories": [
        {
          "name": "string",
          "image_url": "https://example.com/...",
          "note": "string"
        }
      ]
    }
  ]
}
```

### SpreeMessage

| Field | Type | Required | Notes |
|---|---|---|---|
| `role` | `user` / `assistant` | yes |  |
| `content` | string | yes |  |
| `image_urls` | array of string (uri) |  |  |
| `refused` | boolean |  | True when a guardrail produced a templated refusal |
| `created_at` | string (date-time) | yes |  |

```json
{
  "role": "user",
  "content": "string",
  "image_urls": [
    "https://example.com/..."
  ],
  "refused": true,
  "created_at": "2026-10-13T09:30:00Z"
}
```

### AgentSuggestion

| Field | Type | Required | Notes |
|---|---|---|---|
| `run_id` | string (uuid) | yes |  |
| `look` | object | yes |  |
| `look.look_id` | string (uuid) | yes |  |
| `look.title` | string | yes |  |
| `look.image_url` | string (uri) | yes |  |
| `look.occasion` | `owambe` / `wedding` / `corporate` / `casual` / `date_night` / `church` / `travel` / `custom` / null |  |  |
| `look.is_saved` | boolean |  |  |
| `look.created_at` | string (date-time) | yes |  |
| `trigger` | `daily` / `weather` / `event` / `proactive` / `on_demand` | yes |  |
| `rationale` | string |  | Answers "why this?" from stored facts, not a fresh model guess. |
| `weather` | object |  |  |
| `weather.temp_c` | number |  |  |
| `weather.condition` | string |  |  |
| `weather.rain_probability` | number |  |  |
| `weather.dust_index` | number or null |  | Harmattan season dust level |
| `generated_at` | string (date-time) | yes |  |

```json
{
  "run_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "look": {
    "look_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
    "title": "Cultural Evening Flow",
    "image_url": "https://example.com/...",
    "occasion": "owambe",
    "is_saved": true,
    "created_at": "2026-10-13T09:30:00Z"
  },
  "trigger": "daily",
  "rationale": "string",
  "weather": {
    "temp_c": 0,
    "condition": "string",
    "rain_probability": 0,
    "dust_index": 0
  },
  "generated_at": "2026-10-13T09:30:00Z"
}
```

### AgentSettings

| Field | Type | Required | Notes |
|---|---|---|---|
| `daily_enabled` | boolean |  |  |
| `daily_hour_local` | integer |  |  |
| `use_weather` | boolean |  |  |
| `autonomy_level` | integer |  | 0 on-open, 1 daily push, 2 proactive triggers, 3 planning |

```json
{
  "daily_enabled": true,
  "daily_hour_local": 0,
  "use_weather": true,
  "autonomy_level": 0
}
```

### Integration

| Field | Type | Required | Notes |
|---|---|---|---|
| `provider` | `pinterest` | yes |  |
| `connected` | boolean | yes |  |
| `connected_at` | string or null (date-time) |  |  |
| `last_sync_at` | string or null (date-time) |  |  |
| `boards_imported` | integer |  |  |
| `pins_imported` | integer |  |  |
| `status` | `active` / `needs_reauth` / `revoked` / `syncing` |  |  |

```json
{
  "provider": "pinterest",
  "connected": true,
  "connected_at": "2026-10-13T09:30:00Z",
  "last_sync_at": "2026-10-13T09:30:00Z",
  "boards_imported": 0,
  "pins_imported": 0,
  "status": "active"
}
```

### PinterestBoard

| Field | Type | Required | Notes |
|---|---|---|---|
| `board_id` | string | yes |  |
| `name` | string | yes |  |
| `pin_count` | integer | yes |  |
| `cover_image_url` | string or null (uri) |  |  |
| `imported` | boolean |  |  |

```json
{
  "board_id": "string",
  "name": "string",
  "pin_count": 0,
  "cover_image_url": "https://example.com/...",
  "imported": true
}
```

### InboxItem

| Field | Type | Required | Notes |
|---|---|---|---|
| `notification_id` | string (uuid) | yes |  |
| `title` | string | yes |  |
| `body` | string |  |  |
| `category` | `style` / `activity` | yes |  |
| `deeplink` | string or null (uri) |  |  |
| `image_url` | string or null (uri) |  |  |
| `read` | boolean | yes |  |
| `created_at` | string (date-time) | yes |  |

```json
{
  "notification_id": "3f2a9c1e-8b7d-4e55-a3c4-0d1f6b2e9a10",
  "title": "New Style Generated",
  "body": "Your Crimson Elegance look is ready to explore",
  "category": "style",
  "deeplink": "https://example.com/...",
  "image_url": "https://example.com/...",
  "read": true,
  "created_at": "2026-10-13T09:30:00Z"
}
```

### NotificationPreference

| Field | Type | Required | Notes |
|---|---|---|---|
| `category` | `style` / `activity` / `marketing` | yes |  |
| `channel` | `push` / `email` / `whatsapp` / `sms` / `inbox` | yes |  |
| `enabled` | boolean | yes |  |
| `quiet_hours_start` | integer or null |  |  |
| `quiet_hours_end` | integer or null |  |  |

```json
{
  "category": "style",
  "channel": "push",
  "enabled": true,
  "quiet_hours_start": 0,
  "quiet_hours_end": 0
}
```
