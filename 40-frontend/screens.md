# Screen Registry

**Stage:** MVP · **Source:** Figma `KtCAHrBGLQXEdQrPbWJVVS`, page `Hi-FI Visual Design` (`97:408`), extracted 2026-08-17, file last modified 2026-08-13
**Surfaces:** app (Flutter, 428×926) · web (Next.js, 1440 wide) · admin

Every hi-fi frame, its node id, the route it becomes, the endpoints behind it, and the states it must handle. If a screen is not in this table it has not been designed; if an endpoint is not referenced by any screen, it is either unused or a screen is missing — both cases are listed in §4.

`status` values: `designed` (in Figma) · `specced` (contract exists) · `built`.

---

## 1. Onboarding

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| Splash Screen | `98:416` | `/` | — | brand animation → routes to hook or dashboard by session | designed · specced |
| Hook Screen | `102:425` | `/welcome` | — | carousel: "Your style, Understood" / "Your Style DNA" / "AI-Powered Styling" | designed · specced |
| Hook Screen DK | `111:488` | `/welcome` | — | dark variant of the above | designed · specced |
| Sign Up/Log in | `112:555`, `114:541` | `/auth` | `POST /auth/link/request`, `POST /auth/oauth/google`, `POST /auth/oauth/apple` | idle · sending · sent ("check your email") · error · rate-limited | designed · specced |
| **Magic link sent** | **missing** | `/auth/check-email` | — | waiting · resend cooldown · open-mail-app action | **gap** |
| **Magic link verify** | **missing** | `/auth/verify` | `POST /auth/link/consume` | verifying · success · expired · already used · **cross-device code entry** | **gap** |
| Username | `191:776` | `/onboarding/username` | `POST /auth/username` | empty · checking availability · taken · valid | designed · specced |
| Processing screen | `196:1335` | `/onboarding/analyzing` | — | "Analyzing your style...." — shown after quiz submit while the card renders | designed · specced |

Progress indicator on Username reads 100%, so it sits **after** the six quiz questions in the intended order.

---

## 2. Style DNA

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| Style DNA 1 | `114:620`, `142:1909` | `/quiz/1` | `GET /quiz` | option unselected · selected · continue enabled | designed · specced |
| Style DNA 2 | `142:1987`, `142:2191` | `/quiz/2` | — | as above | designed · specced |
| Style DNA 3 | `142:2299`, `148:2537` | `/quiz/3` | — | as above | designed · specced |
| Style DNA 4 | `148:2738`, `148:2826` | `/quiz/4` | — | as above | designed · specced |
| Style DNA 5 | `148:2910` | `/quiz/5` | — | as above | designed · specced |
| Style DNA 6 | `191:677` | `/quiz/6` | `POST /quiz/submit` | **three options, not four** · submitting | designed · specced |
| Style DNA Result | `122:329`, `135:500`, `216:701`, `217:823` | `/quiz/result` | `GET /quiz/result`, `GET /quiz/card` | reveal animation · card pending · card ready · card failed | designed · specced |
| Share Result | `237:5879`, `237:6154`, `348:908` | `/quiz/result/share` | `GET /quiz/card` | square preview · stories preview · copy link · native share sheet | designed · specced |

**Progress values in the design run 0 → 90% across the six questions.** Take the value from `GET /quiz`, do not hardcode.

**Duplicate frames** (`142:1909` vs `114:620` etc.) are visual variants of the same screen; build one and drive it from the question configuration.

---

## 3. Onboarding continued

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| Connect to Pintrest | `135:1682`, `776:1840` | `/onboarding/pinterest` | `GET /integrations/pinterest/authorize` | idle · redirecting · connected · skipped · denied | designed · specced |
| Upload Wardrobe | `135:1759` | `/onboarding/vault` | `POST /uploads/sign`, `POST /vault/items` | empty · uploading · processing · added · skipped | designed · specced |
| Permission Request | `792:2127` | `/onboarding/permissions` | `PUT /me/consents` | camera/photos toggle · notifications toggle | designed · specced |
| **AI processing consent** | **missing** | `/onboarding/permissions` | `PUT /me/consents` | purpose `ai_processing` explained and granted | **gap** |
| **Location consent** | **missing** | `/onboarding/permissions` | `PUT /me/consents` | purpose `location_weather`, city-level only | **gap** |
| **Body profile capture** | **missing** | `/onboarding/fit` | `PUT /me/body-profile` | body shape · height · fit preference · sizes · skip | **gap** |

The existing Permission Request screen covers camera/photos and notifications only. Three consent surfaces are missing; see §4.

---

## 4. Home and generation

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| Dashboard | `260:7025`, `301:3114` | `/home` | `GET /me`, `GET /agent/today`, `GET /looks?filter=recent`, `GET /looks?filter=saved` | loading · empty · populated · agent suggestion present/absent | designed · specced |
| Power Dashboard | `704:2297` | `/home` | as above | variant leading with "Style Your Fabrics" | designed · specced |
| Generate | `398:1022`, `654:63788` | `/generate` | — | entry hub: Style Fabric · Generate Look · Style Studio · Use my vault | designed · specced |
| Generate Look — Generate Look | `654:63666` | `/generate/look` | `POST /looks/generate` | occasion · mood · weather toggle · upload · note · submitting | designed · specced |
| Generate Look — Style Fabric | `622:1988` | `/generate/fabric` | `POST /uploads/sign` | prompt to upload fabric | designed · specced |
| Generate Look — Upload | `625:2080` | `/generate/upload` | `POST /uploads/sign` | camera · gallery · album picker · permission denied | designed · specced |
| Generate Look Extended | `414:968` | `/generate/quick` | `POST /looks/generate` | occasion shortcuts: Owambe · Casual · Date night · Travel | designed · specced |
| Review Item | `629:1349` | `/generate/review` | `POST /fabric/{asset_id}/style` | occasion chips · fabric type · note · save to vault · submitting | designed · specced |
| Building Screen | `427:1005`, `636:2110` | `/generate/building` | `GET /looks/jobs/{job_id}/stream` | queued · analyzing · assembling · rendering · **progress %** · cancel | designed · specced |
| Generate Error State | `516:3353` | `/generate/error` | — | "We couldn't create this look" · Try Again · reason-specific copy | designed · specced |

**The Building Screen is a job-progress UI, not a spinner.** It must consume SSE (or poll) and render real progress; see [`realtime.md`](realtime.md).

---

## 5. Results

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| AI Result | `438:1736` | `/looks/results` | `GET /looks/{id}` | carousel of generated looks · occasion tabs | designed · specced |
| Style Result | `638:32793` | `/styles/results` | `GET /fabric/{asset_id}/style` result | category tabs: Your Styles · Ladies · Men · Inspirational · Casual · Custom | designed · specced |
| AI Result — Details | `471:154224` (428×1760) | `/looks/{id}` | `GET /looks/{id}` | scrolling detail with item breakdown | designed · specced |
| AI Result — Details 2 | `471:185547` | `/looks/{id}` | `GET /looks/{id}`, `POST /looks/{id}/adjust`, `POST /looks/{id}/save` | item list · description · Adjust · Save Look | designed · specced |
| AI Result (Saved Looks) | `475:1869`, `23:292` | `/looks/{id}` | `POST /looks/{id}/save` | post-save confirmation · Organize | designed · specced |
| Styled Item Layout | `724:3473` | `/looks/{id}` | `GET /looks/{id}` | variant seeded from a single vault item | designed · specced |
| Style Details | `660:1406` (428×1084) | `/styles/{id}` | fabric analysis result | style name · occasion chips · description · styling details · accessories | designed · specced |
| Why this works for you | `690:1477` | `/looks/{id}/why` | `GET /looks/{id}` → `why_this_works` | personalised explanation · "generated by Faue Artificial Intelligence" attribution | designed · specced |
| Share Designs | `696:2069` | `/looks/{id}/share` | `POST /looks/{id}/share` | image preview · copy link · native share | designed · specced |
| Saved Looks | `488:1903` | `/saved` | `GET /looks?filter=saved` | populated · board suggestions · organize | designed · specced |
| Saved Empty State | `539:35077` | `/saved` | `GET /looks?filter=saved` | "Nothing saved yet" | designed · specced |

The attribution string on `690:1477` is a product requirement for generated renders, not decoration — see [`../60-ai/rendering.md`](../60-ai/rendering.md).

---

## 6. Vault

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| My Vault | `704:2252` | `/vault` | `GET /vault/items` | category tabs · search · loading · populated | designed · specced |
| My Vault Empty State | `504:2972` | `/vault` | `GET /vault/items` | "Build your wardrobe" · Upload Item | designed · specced |
| Upload | `709:1540` | `/vault/upload` | `POST /uploads/sign` | camera · gallery · album picker · processing · rejected | designed · specced |
| Item Details | `711:1596` (428×1122) | `/vault/items/{id}` | `GET /vault/items/{id}`, `PATCH /vault/items/{id}` | view · edit · name · colour · category · notes | designed · specced |
| Style This item | `717:3135` | `/vault/items/{id}/style` | `POST /vault/items/{id}/style` | occasion · submitting → building screen | designed · specced |
| Delete Confirmation Modal | `728:3608` | overlay | `DELETE /vault/items/{id}` | "Are you sure you want to remove this item?" · Remove Item · Keep Item | designed · specced |
| **Wear logging** | **missing** | `/vault/wear` | `POST /vault/wear` | log what was worn — the agent's primary learning signal | **gap** |

---

## 7. Profile and settings

| Screen | Node | Route | Endpoints | States | Status |
|---|---|---|---|---|---|
| Profile Screen | `728:4143` | `/profile` | `GET /me`, `GET /quiz/result` | DNA summary · Retake Style DNA · Edit Profile · Settings · Connected Accounts · Permission Request · Log Out | designed · specced |
| Edit Profile | `814:1812` | `/profile/edit` | `PATCH /me` | username · email · phone · Done · validation errors | designed · specced |
| Connected Accounts | `774:1712` | `/profile/accounts` | `GET /integrations`, `DELETE /integrations/{provider}` | Pinterest connected/disconnected · **remove the Instagram card** | designed · needs change |
| Log Out Confirmation | `792:1915` | overlay | `POST /auth/logout` | "Log Out?" · Stay Signed In | designed · specced |
| Notification | `929:1812` | `/notifications` | `GET /notifications`, `POST /notifications/{id}/read` | tabs All · Style · Activity · empty · unread badge | designed · specced |
| **Notification preferences** | **missing** | `/profile/notifications` | `GET/PUT /notifications/preferences` | per category and channel · quiet hours | **gap** |
| **Privacy & data** | **missing** | `/profile/privacy` | `GET /me/consents`, `POST /privacy/export`, `POST /privacy/delete` | consent toggles · export · delete account | **gap** |

The Log Out Confirmation frame shows a Settings section listing "Account Settings" and "Privacy & Security" — those destinations are referenced but not drawn.

**Account deletion is launch-blocking**, not optional: offering Sign in with Apple makes in-app deletion an App Store requirement.

---

## 8. Web surface

| Screen | Node | Route | Endpoints | Notes | Status |
|---|---|---|---|---|---|
| Landing Page | `937:1869` (1440×2516) | `/` | — | Home · Features · How It Works · Style Gallery · FAQs · Download App | designed · specced |
| **DNA share page** | **missing** | `/dna/{id}` | public read | What a shared Style DNA card opens to for someone without the app | **gap** |
| **Look share page** | **missing** | `/look/{id}` | public read | What a shared look opens to | **gap** |
| **Magic link landing** | **missing** | `/auth/verify` | `POST /auth/link/consume` | Explicit-action page; must not consume on GET | **gap** |

The landing page headline — "Turn Any Fabric Into a Tailor-Ready Outfit" — confirms fabric styling as the lead marketing message, which matches the MVP scope.

Share pages matter more than they look: the Style DNA card is the viral mechanism, and a shared card that opens to a 404 breaks the loop.

---

## 9. Gap analysis

### Screens missing for specified endpoints

| Gap | Endpoint(s) with no screen | Impact |
|---|---|---|
| Magic-link sent / verify / cross-device code | `POST /auth/link/consume` | **Blocking** — sign-in cannot complete |
| Body profile capture | `PUT /me/body-profile` | Recommendation quality; silhouette constraints unavailable |
| AI processing consent | `PUT /me/consents` | **Blocking** — generation requires `ai_processing` |
| Location consent | `PUT /me/consents` | Weather-aware suggestions unavailable |
| Notification preferences | `GET/PUT /notifications/preferences` | Compliance and opt-out; required by stores |
| Privacy and data settings | `POST /privacy/export`, `POST /privacy/delete` | **Blocking** — App Store requires in-app deletion |
| Wear logging | `POST /vault/wear` | Agent has no behavioural signal to learn from |
| Web share pages | public read | Viral loop breaks for non-users |

### Designed screens needing change

| Screen | Change |
|---|---|
| Connected Accounts `774:1712` | Remove the Instagram card — the API cannot deliver what it promises |
| Bottom navigation `283:1894` | Uses `#613EEA` and SF Pro Text; off-brand against green + Plus Jakarta Sans |
| Style DNA questions | Only one answer option is drawn per question; options B–D exist in [`../00-product/style-dna.md`](../00-product/style-dna.md) and need designing |

### Endpoints with no screen, by design

`GET /uploads/{asset_id}` (polled, not a screen), `POST /looks/{id}/feedback` (inline control), `POST /agent/suggestions/{run_id}/respond` (inline control), `POST /notifications/devices` (background), `POST /privacy/restrict` (support-initiated).

---

## 10. Navigation

Bottom navigation is four tabs — **Home · Vault · Saved · Profile** — with Generate as a centre action rather than a tab.

```
Home     /home        dashboard, agent suggestion, recent and saved looks
Vault    /vault       wardrobe, categories, search
[+]      /generate    centre action, not a tab
Saved    /saved       saved looks, boards
Profile  /profile     DNA, settings, accounts
```

Deep-link targets are documented in [`deeplinks.md`](deeplinks.md). Notification taps route to `/looks/{id}`, `/quiz/result`, or `/notifications`.

---

## 11. Conventions for this registry

- One row per screen, even where Figma has several visual variants — build once, drive from data.
- Endpoints are exact operation paths from [`../30-contracts/openapi/gateway.v1.yaml`](../30-contracts/openapi/gateway.v1.yaml). If they disagree, the contract wins.
- Every screen lists loading, empty, and error states. A screen without an empty state is unfinished; several designed screens already pair with explicit empty states, which is the standard to hold.
- Update `status` as screens are built. `designed` alone means the contract may still move.

## Studio and looks (web-app, built behind `NEXT_PUBLIC_LOOKS_AVAILABLE`)

| Route | Purpose | Backend |
|---|---|---|
| `/studio` | Today's edit, start tiles, week, next event, gaps, what ASE knows | `GET /agent/today` (flag), `/events`, `/me/ase-notes` |
| `/studio/make` | Event, feel, build-from (vault or fabric), note; Make my looks | `POST /looks/generate`; 403 opens the `ai_processing` consent sheet; 429 shows the limit state |
| `/studio/building?job=` | Progress from the job, failure says it did not count against the limit | `GET /looks/jobs/{id}` polled every 1.5 s |
| `/looks/results?job=` | The generated looks | `GET /looks/{id}` |
| `/looks/view?id=` | Save, share to community, more like this / not for me (with "what was off"), I'll wear it, send to tailor | `/looks/{id}/save`, `/feedback`, `/vault/wear` |
| `/studio/tailor?look=` | Review the exact message, choose the tailor, open WhatsApp (`wa.me`); measurements never included | `GET /tailors` |
| `/studio/first` | First looks from Style DNA before any piece is added | `GET /looks?filter=recent` (flag) |
| `/studio/gaps` | Wardrobe gaps counted from the vault and events (rules, no ASE) | `/vault/items`, `/events` |
| `/studio/events`, `/studio/teach`, `/studio/knows` | Events, lasting notes for ASE, what ASE knows | `/events`, `/me/ase-notes` |

Offline: wear logs made without a connection are kept in `localStorage` (`faue.wearQueue`, 50 max) and sent when the browser comes back online.
Not yet built: weather degree in the date chip (needs `PUT /me/location` and `GET /me/context` on the gateway).
