# Auth Flows

**Stage:** MVP · **Contract:** [`../30-contracts/openapi/gateway.v1.yaml`](../30-contracts/openapi/gateway.v1.yaml) tag `auth`

Three ways in: magic link, Google, Apple. No passwords anywhere.

---

## 1. Magic link

The default path. The user types an email address and receives a link.

```
1  client generates session_challenge  (32 random bytes, base64url, kept in memory
                                        and in secure storage for this session)
2  POST /auth/link/request { email, session_challenge }
   → 202 { expires_in: 600 }              always 202, even for unknown addresses
3  show "check your email" screen with a resend cooldown
4  user taps the link → https://faueofficial.com/auth/verify?t=<token>
5a app installed  → universal/app link opens the app at /auth/verify
5b not installed  → faue-web renders a page with an explicit "Sign in" button
6  POST /auth/link/consume { token, session_challenge }
   → 200 Session
```

### Why the link must not sign the user in on GET

Mail security scanners — corporate gateways, some consumer providers, link-preview bots — fetch every URL in a message before the recipient sees it. If a `GET` consumed the token, the login would already be spent by the time the user tapped it, and the failure would look random.

So: opening the link **renders a page**. Signing in requires a `POST`, triggered either by the app or by an explicit button. Never make the web landing page auto-submit on load; a scanner that executes JavaScript would defeat that too.

### Cross-device

The user requests on their phone and opens the mail on a laptop, or vice versa. Common, not an edge case.

```
POST /auth/link/consume { token, session_challenge: <laptop's, which differs> }
→ 409 { device_code_required: true, device_code: "418209" }

The laptop page displays: "Enter this code in the FAUE app: 418209"
The original app session then calls:
POST /auth/link/consume { token, session_challenge: <phone's>, device_code: "418209" }
→ 200 Session
```

The session lands on the device that started the flow, which is what the user expects.

### Client responsibilities

| Situation | Response |
|---|---|
| `202` received | Show the check-email screen. Start the cooldown from `resend_available_in` in the body — never a hardcoded 60, which drifts the moment the server rule changes. Display `masked_destination` so the user can see they typed the address correctly. |
| Resend tapped | Call `/auth/link/request` again. The previous token is invalidated server-side. |
| `410` on consume | "That link has expired or was already used." Offer to send a new one. |
| `409` on consume | Show the device code prominently and explain where to type it. |
| `429` | Read `Retry-After`. Show remaining time; do not retry automatically. |
| App resumed from background | Re-check for a pending deep link; iOS may deliver it late. |

### Deliverability

Login depends on email arriving. Delivery is **Resend**, sending from the subdomain `faueofficial.com` so a reputation problem never affects the apex.

> **Resend's root-domain DNS layout looks wrong and is not.** For a root sending
> domain, DKIM goes on the domain itself while SPF and MX go on a `send.`
> subdomain:
>
> ```
> resend._domainkey.faueofficial.com   TXT   DKIM — proves ownership, signs mail
> send.faueofficial.com                TXT   SPF  — the MAIL FROM / return path
> send.faueofficial.com                MX          bounce handling
> _dmarc.faueofficial.com              TXT   DMARC
> ```
>
> `send.faueofficial.com` is where **bounces** go, not where mail comes from. The
> from-address stays on the apex: `hello@faueofficial.com`. Reading the split as a
> misplaced record and "fixing" it breaks verification.
>
> `api-gateway/scripts/check_email_dns.py` checks all four against a public
> resolver.

> **Two different addresses, and they cannot be the same one.** The public contact
> address is `faueofficial@gmail.com`. The magic-link **sending** address must be on
> a domain FAUE controls and has verified in Resend — Resend will not send `from` a
> Gmail address, and neither will any transactional provider, because sending as a
> domain you do not own is what SPF and DKIM exist to prevent. SPF, DKIM and DMARC on that subdomain are an operational requirement, not a nicety.

Resend allows 2 requests per second on the default plan, so a signup burst can be rate-limited upstream. The client should treat a `503` on link request as retryable, not as a rejected address.

---

## 2. Google

```
1  native Google Sign-In → id_token + nonce
2  POST /auth/oauth/google { id_token, nonce }
   → 200 Session
```

The server verifies the token against Google's JWKS, checking `iss`, `aud`, `nonce`, and `exp`. Never send a profile object from the client — it is trivially forged and will be ignored.

---

## 3. Apple

```
1  Sign in with Apple → identity_token, authorization_code, and (first time only) full name
2  POST /auth/oauth/apple { identity_token, authorization_code, full_name?, nonce }
   → 200 Session
```

Three Apple-specific rules:

1. **`full_name` arrives only on the very first authorization.** If the client does not forward it on that call, it is gone permanently — Apple will never send it again, even after revoking and re-authorising. Forward it unconditionally when present.
2. **Private-relay addresses are normal.** `xyz@privaterelay.appleid.com` is a real, working address. Do not validate it away or ask the user to "use a real email".
3. **In-app account deletion is mandatory.** Offering Sign in with Apple obliges the app to offer account deletion in-app. `POST /privacy/delete` exists for this and the screen is currently missing from the design.

---

## 4. Account linking

One person, one account, several identities. Linking happens server-side when a **verified** email matches an existing account.

| Scenario | Outcome |
|---|---|
| Magic link, then Google with the same verified address | Linked automatically. Same account. |
| Google, then Apple with a private-relay address | **Not** linked — the addresses differ. Two accounts unless the user links manually. |
| Any provider with an unverified address matching an existing account | **Never** auto-linked. This is an account-takeover path. |

Manual linking from Profile is `M1-2`. Until then, tell users on the auth screen that they should use the same method they signed up with — a small line of copy prevents a support burden.

---

## 5. Session lifecycle

```
access token    JWT, 15 minutes, sent as Authorization: Bearer
refresh token   opaque, 30 days, rotating — every use returns a new one
```

### Refresh

```
POST /auth/refresh { refresh_token } → 200 { access_token, refresh_token, expires_in }
```

Refresh proactively at roughly 80% of the access token's lifetime (about 12 minutes), or reactively on the first `401`. Serialise refreshes: if several requests `401` at once, one refresh runs and the rest wait for it, otherwise the rotation race revokes the family.

### Reuse detection

Presenting an already-rotated refresh token revokes the **entire family** and returns `401`. That is theft detection working as intended. The correct client response is to clear credentials and return to `/auth` — never to retry.

The most common cause of hitting this accidentally is parallel refresh calls, which is why serialising matters.

### Storage

| Platform | Store |
|---|---|
| Flutter (iOS) | Keychain via `flutter_secure_storage` |
| Flutter (Android) | EncryptedSharedPreferences via `flutter_secure_storage` |
| Web | Memory for the access token; refresh token in an httpOnly, Secure, SameSite=Lax cookie |

Never put tokens in `SharedPreferences`, `localStorage`, or a log line.

### Logout

```
POST /auth/logout → 204
```

Revokes the presented family. The client must also clear secure storage, drop cached user data, and unregister the push device token — otherwise notifications continue arriving for a signed-out account, which reads as a privacy failure whether or not it technically is one.

---

## 6. Session states

```
                 ┌──────────────┐
                 │ unauthenticated │──── /auth
                 └──────┬───────┘
                        │ sign in
                 ┌──────▼───────┐
       ┌─────────│ authenticated │─────────┐
       │         └──────┬───────┘          │
  access expired        │             logout / 401 on refresh
       │                │                  │
 ┌─────▼──────┐   onboarding incomplete    │
 │ refreshing │         │                  │
 └─────┬──────┘   ┌─────▼──────┐           │
       │          │ onboarding │           │
   success        └────────────┘           │
       └──────────────────────────────────►┘
```

Sign-in responses (`/auth/link/consume`, `/auth/oauth/*`) already carry `onboarding`, so the app routes straight from the auth screen with no second call — that matters on the slowest screen in the product. `/auth/refresh` deliberately does **not**: it runs every twelve minutes in the background and no screen reads onboarding at that moment.

`GET /me` returns the same `onboarding` block, for resuming after a reinstall or a device change:

```json
{ "username_set": true, "quiz_completed": true, "pinterest_connected": false,
  "vault_started": false, "body_profile_set": false }
```

Resume order: username → quiz → permissions → Pinterest → vault → body profile. Only username and quiz are required to reach the dashboard; the rest are skippable and re-offerable later.

---

## 7. Screens still needed

Listed in [`screens.md`](screens.md) §9 and repeated here because they block sign-in:

- **Check-email screen** with resend cooldown.
- **Verify screen** in-app: verifying, success, expired, already-used.
- **Cross-device code entry** — display on web, input in app.
- **Web magic-link landing** with an explicit sign-in button.

---

## 8. Testing

- Sign in on device A, open the link on device B → expect the code path, not a failure.
- Tap a link twice → second attempt shows the expired message.
- Let a token sit 11 minutes → expired message.
- Force two concurrent `401`s → exactly one refresh call, no family revocation.
- Sign in with Apple on a fresh install → name captured; delete and reinstall → name still present from the server, not re-requested.
- Sign out → push notifications stop.
