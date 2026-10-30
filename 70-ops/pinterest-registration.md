# Pinterest developer app: registration

**Stage:** MVP · **Owner:** backend · **Relates to:** [`data-flows.md` section 6](../10-architecture/data-flows.md), [`threat-model.md`](../10-architecture/threat-model.md), [`gateway.v1.yaml`](../30-contracts/openapi/gateway.v1.yaml), [ADR 0019](../80-adr/0019-remove-instagram-integration.md)

Everything needed to register FAUE with Pinterest, in the order the form asks for it, and what to do after. Copy from here rather than rewriting the answers each time.

---

## 1. Status

| Item | State |
|---|---|
| Pinterest developer app | **Not created** |
| `PINTEREST_CLIENT_ID`, `PINTEREST_CLIENT_SECRET` | Declared in `api-gateway/.env`, **empty** |
| Gateway integration | **Built** (2026-10-14): authorize, callback, boards, import, disconnect and list, with tests against a mock Pinterest. Not yet run against the real Pinterest, because there are no credentials. Needs migration `0011_imported_pins` applied |
| Pin images | Not copied yet. A pin keeps its Pinterest image address (`image_status = pending_detector`) until a real face and text detector exists |
| Privacy policy section | Written: <https://faueofficial.com/privacy#pinterest> |
| Access tier | None yet. Apply for Trial first |

---

## 2. The details the form asks for

| Field | Value |
|---|---|
| App name | FAUE |
| Website | `https://faueofficial.com` |
| Privacy policy | `https://faueofficial.com/privacy#pinterest` |
| Terms of service | `https://faueofficial.com/terms` |
| Contact email | `hello@faueofficial.com` |
| Redirect URI, production | `https://api.faueofficial.com/v1/integrations/pinterest/callback` |
| Redirect URI, local | `http://localhost:8000/v1/integrations/pinterest/callback` |
| Redirect URI, staging | Add once staging has its own API host (it is not `staging-api.faueofficial.com`, which does not resolve) |
| Scopes | `boards:read`, `pins:read`. Add `boards:read_secret` and `pins:read_secret` only if secret boards are in scope |
| Scopes not wanted | Anything ending `:write`, `user_accounts:read`, ads, catalogs |

The redirect URI in the authorization request and the token request must match a registered value **exactly**.

### Short description (character-limited fields)

> FAUE is a personal styling app for African fashion. With the user's permission it reads the Pinterest boards they choose, read-only, to learn their style and suggest outfits and fabric styling ideas. It never posts or edits anything on Pinterest.

### Purpose and use case (long)

> **What FAUE is.** FAUE helps people decide what to wear and what to make from fabric they already own. It builds a style profile through a short quiz and then suggests looks, and styling advice for Ankara, lace and Aso-Oke. The app is currently pre-launch, with a public waitlist at faueofficial.com.
>
> **Why we need Pinterest.** Many of our users already save the clothes they aspire to on Pinterest boards. Letting them connect a board is the quickest way for FAUE to understand their taste without a long questionnaire.
>
> **What we access.** Read-only access to the boards and pins of the Pinterest account that signs in (`boards:read`, `pins:read`). We do not read other people's boards, messages or followers, and we do not post, save, edit or delete anything.
>
> **How the user stays in control.** Pinterest is off until the user switches it on. They then choose which boards to import, and nothing is imported by default. They can disconnect at any time in FAUE or in Pinterest's settings, which revokes access and deletes the imported pins and the stored token.
>
> **How we protect the data.** Tokens are stored encrypted. Pin images go through the same face and text removal as uploaded photos before any model sees them. We do not sell the data, show it to other users, or use it for advertising.

Keep it accurate: say "pre-launch" while the app is not out, and do not claim a feature that is not built.

---

## 3. What Pinterest checks

From [Pinterest's access-tier page](https://developers.pinterest.com/docs/key-concepts/access-tiers/):

**Trial is denied for**
- an inaccurate or inaccessible privacy policy
- a vague app description

**Standard is denied for**
- a demo that does not show the OAuth flow
- a demo that collects login credentials or session cookies instead of using OAuth
- a demo that does not show a live Pinterest integration

So: the privacy policy link must work without signing in, and the description must say what the app reads and why. Both are above.

---

## 4. Access tiers and limits

| | Trial | Standard |
|---|---|---|
| How | Apply with the app registered | Upgrade from Trial with a demo video |
| Boards and pins read | 1,000 requests per day per app | 1,000 requests per minute per user per app |
| All requests | 1,000 per day | 100 per second per user per app |
| Creating boards and pins | Allowed, but they are **sandbox** items "visible only to creator" | Normal |
| Meant for | Exploring and testing | Production |

Reviews are not quick. Applications in Pinterest's own forum are regularly reported as pending for a long time, so register early and do not put it on the launch critical path.

The current numbers are in [Pinterest's rate limits](https://developers.pinterest.com/docs/reference/rate-limits.md) and can change without notice.

---

## 5. OAuth, as Pinterest documents it

Source: [Set up authentication and authorization](https://developers.pinterest.com/docs/getting-started/set-up-authentication-and-authorization/).

| | |
|---|---|
| Flow | Authorization code |
| Authorize | `https://www.pinterest.com/oauth/` with `client_id`, `redirect_uri`, `response_type=code`, `scope`, `state` |
| Token | `POST https://api.pinterest.com/v5/oauth/token`, HTTP Basic with client id and secret, `grant_type=authorization_code` |
| Sandbox host | `https://api-sandbox.pinterest.com` |
| Access token | 30 days (2,592,000 s) |
| Refresh token | Continuous: 60 days, and renewable indefinitely if refreshed before it expires |
| PKCE | Not documented. Use `state` and the server-held secret; do not rely on PKCE |

### Reading only the user's own content

Apps registered on or after **14 September 2026** get **403 `PINNER_DATA_ACCESS_DENIED`** when they read boards or pins that do not belong to the account that authorized the app. [Pinterest says](https://community.pinterest.biz/t/understanding-the-pinner-data-access-denied-access-error/51738): "You do not need additional approval if your app only reads Boards and Pins belonging to the Pinterest account that authorized your app."

FAUE reads only the signed-in user's own boards, so it is unaffected. Two rules follow:

1. **Never add a feature that reads another person's board.** It would need separate approval from Pinterest.
2. **Treat that 403 as non-retryable.** Do not loop; show the person a clear message.

Endpoints it applies to: Get board, List pins on board, List board sections, List pins on board section, Get pin.

---

## 6. Registering, step by step

1. Create an app at <https://developers.pinterest.com/> under **My apps**, signed in with the FAUE Pinterest account (not a personal one).
2. Fill in the details from section 2.
3. Request **Trial access**. Wait for the email.
4. Put the client id and secret in the gateway's environment (`PINTEREST_CLIENT_ID`, `PINTEREST_CLIENT_SECRET`) in the host's secret store. Never commit them.
5. Build and run the integration against the Trial app (section 7).
6. Record the demo video (section 8) and use **Upgrade** on the app card to request Standard.

---

## 7. Testing the connection with the app screens

The design file has the screens (Figma file key `KtCAHrBGLQXEdQrPbWJVVS`; the **Hi-Fi Visual Design** page has 71 frames, including "Connect to Pinterest").

1. Export the Hi-Fi screens as PNG through the Figma image API (`FIGMA_TOKEN` is in the root `.env`).
2. On the FAUE test Pinterest account, create a board "FAUE test" and pin the exports. Creating needs `boards:write` and `pins:write`, which Trial allows. Items created on Trial are sandbox items visible only to the creator, which is what we want for a test.
3. Run the real flow against it: authorize, callback, list boards, choose the test board, import.
4. Check that: the token is stored encrypted; only the chosen board is imported; images pass through the PII pipeline; disconnect revokes the token and deletes the pins.

App screens test the plumbing (tokens, PII pipeline, host allow-list, injection screening). For the quality of the style analysis, also pin fashion images, for example the generated model images in `docs/brand/illustrations/style-dna/models/`.

---

## 8. The demo video Pinterest asks for (Standard)

Show, in one continuous take, on the real app:

1. The Pinterest choice being switched on in FAUE.
2. Tapping Connect, the Pinterest consent screen appearing, and approving.
3. Landing back in FAUE and seeing the list of boards.
4. Choosing one board and importing it.
5. The imported pins appearing in FAUE.
6. Disconnecting, and the pins disappearing.

Do not show any login credentials being typed into FAUE, and do not use anything other than OAuth. Pinterest denies on both.

---

## 9. Instagram

FAUE does **not** offer an Instagram connection ([ADR 0019](../80-adr/0019-remove-instagram-integration.md)). In October 2026 that still holds:

- The Instagram platform supports only **professional (Business and Creator) accounts**, and only their own media. It exposes no saved posts or collections. Serving accounts you do not own needs App Review and Business Verification. ([Meta](https://developers.facebook.com/docs/instagram-platform/overview/))
- The Basic Display API, the only route for personal accounts, ended on 4 December 2024.

What is viable instead is **share to FAUE** (the phone's share sheet or a web share target) and **screenshot upload**, which work for any account and need no platform API. A new ADR should record that.
