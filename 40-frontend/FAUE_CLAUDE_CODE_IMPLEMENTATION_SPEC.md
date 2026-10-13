# FAUE --- Product, Frontend & Motion Implementation Specification

**For Claude Code and future frontend engineering contributors**

**Document status:** Implementation brief / source of truth for the
first frontend build\
**Product:** FAUE --- fashion intelligence and personal styling for
African fashion contexts\
**Canonical domain:** `faueofficial.com`\
**Primary audience:** Nigerian users first, with architecture that can
expand across African markets\
**Build principle:** Build the smallest complete, high-quality product
loop; preserve clean seams for future contributors.

------------------------------------------------------------------------

## 0. Instructions to Claude Code --- read this first

Treat this document as the frontend implementation brief, not permission
to replace or redesign the existing backend.

1.  **Inspect before editing.** First inspect the repository, existing
    apps, package manager, API contracts/OpenAPI specification,
    authentication flow, design assets, environment variables, test
    commands, and deployment setup. Report what already exists before
    proposing structural changes.
2.  **Preserve working systems.** Do not rebuild existing backend
    services, invent API routes, silently change API contracts, or
    replace established architecture just to fit this document. Adapt
    the frontend to the actual repository and contracts.
3.  **Make a plan before implementation.** Identify what can be reused,
    what is missing, risks, dependencies, and a phased plan. Then
    implement in small, testable increments.
4.  **Do not fake product functionality.** A polished demo state is
    acceptable only when clearly labelled as demo content. Do not
    present mock generation, mock authentication, fake saved looks, or
    fake uploads as production functionality.
5.  **Use typed contracts.** Prefer existing OpenAPI-generated
    types/client where available. If no typed client exists, create a
    narrow typed API layer and document assumptions. Do not spread raw
    `fetch` calls through components.
6.  **Keep visual and domain logic separate.** UI components should not
    own scoring algorithms, API mapping, image-processing policy, or
    business rules.
7.  **Avoid a giant component.** Build reusable sections, components,
    hooks, types, and feature modules. Keep files small enough for a
    future engineer to understand and change confidently.
8.  **Do not add infrastructure or dependencies without a reason.**
    Check the installed stack first. Avoid introducing a second state
    manager, animation library, component library, or styling system
    without a concrete need.
9.  **Respect security and consent.** Never put secrets in client code.
    Do not log personal data, raw body measurements, uploaded image
    URLs, authentication tokens, or model prompts. Respect
    consent-denied-by-default requirements.
10. **Validate every phase.** Run lint, type-check, unit tests, relevant
    end-to-end tests, and a production build. Report exact results and
    any unimplemented items; never claim a check passed if it was not
    run.

### First output expected from Claude Code

Before modifying files, return: - repository and framework summary; -
existing backend/API/auth integration points; - existing design assets
and conventions; - proposed file structure and dependencies; - a short
implementation plan with acceptance checks; - any blockers or decisions
that genuinely require the founder.

Proceed with sensible defaults where the specification is explicit. Do
not ask the founder to decide routine implementation details.

------------------------------------------------------------------------

## 1. Product definition

### 1.1 Positioning

**Core one-liner:**\
\> FAUE turns what you already own into what you should wear --- and
what your tailor should make.

**Brand line:**\
\> Know what to wear. Know what to make.

**Product principle:**\
\> The problem is not a shortage of inspiration. It is the absence of a
decision.

FAUE is a personal styling and fashion-decision platform. It helps
people make better use of clothes and fabrics they already own, make
outfit decisions that fit their personal style and occasion, and
communicate a chosen bespoke style clearly to a tailor.

FAUE is not simply a fashion catalogue, a generic chatbot, or a shopping
storefront. The product's distinctive loop is:

**Discover personal style → add clothes or fabric → receive a specific
look → understand why it works → save, share, or send a tailor-ready
reference.**

### 1.2 The problem to solve

Fashion discovery is fragmented across social feeds, screenshots,
moodboards, and conversations. A person may own good clothes but
struggle to combine them, or buy beautiful fabric without knowing what
cut, silhouette, or finishing details to request from a tailor. The gap
creates decision fatigue, wasted clothing, avoidable spending, and
disappointment when a bespoke garment differs from the imagined result.

FAUE should help users move from vague inspiration to a concrete,
explainable decision --- especially within Nigerian fashion contexts
such as Owambe, Aso-Ebi, native wear, workwear, celebrations, and
changing weather.

### 1.3 Audience

-   **Primary:** Fashion-conscious Nigerian professionals who attend
    events and buy fabric or bespoke clothing several times a year.
-   **Secondary:** People who already own clothes but need help
    combining them.
-   **Tertiary:** Style-curious and price-sensitive users who want to
    look intentional without constantly buying more.
-   **MVP recipient:** The tailor, who should be able to receive a clear
    brief through WhatsApp without needing a FAUE account.

Design for all genders and different style preferences. Avoid reducing
African fashion to a single aesthetic, country, body type, or occasion.

### 1.4 The core product loop

1.  Complete the six-question Style DNA quiz.
2.  See a personal style profile and shareable Style DNA card.
3.  Add owned clothing to the Vault and/or upload fabric.
4.  Choose occasion, mood, weather context, and an optional note.
5.  Receive a look using only items in the allowed/owned pool, with a
    "Why this works for you" explanation.
6.  Save, regenerate, share, log an item as worn, or send a fabric/style
    reference to a tailor via WhatsApp.
7.  Return to the dashboard for another useful suggestion.

Every MVP screen should support this loop. Anything outside it should be
treated as a later roadmap item unless the existing product contract
explicitly says otherwise.

------------------------------------------------------------------------

## 2. Product scope and important boundaries

### 2.1 MVP frontend surfaces

The first frontend should support:

-   Marketing landing page with strong editorial storytelling and
    restrained motion.
-   Authentication entry and completion flows that match the existing
    API.
-   Six-question Style DNA quiz and results card.
-   Dashboard/home state.
-   Wardrobe Vault: add, view, edit, categorise, search, and delete
    owned items.
-   Look generation form: occasion, mood, weather (only with consent),
    and optional note.
-   Generated look result with visual, explanation,
    save/regenerate/share actions.
-   Fabric upload and native-style suggestion flow.
-   WhatsApp tailor handoff with a useful prefilled message and
    shareable reference.
-   Saved looks.
-   Profile, optional body-profile fields, consent settings, data
    export/delete entry points, and logout.
-   Clear loading, empty, error, offline, and generation-unavailable
    states.

### 2.2 Explicitly not MVP unless already implemented and contracted

-   Affiliate storefront or cross-brand shopping catalogue.
-   Claims that a catalogue contains 500+ items.
-   Full stylist/tailor professional portal.
-   Virtual try-on.
-   Unapproved integrations with social platforms.
-   A general-purpose assistant that can recommend items outside the
    user's owned wardrobe.
-   Push notifications or proactive notification systems beyond existing
    backend support.
-   New backend services created solely to support a visual demo.

The current product requirements specify **six** Style DNA questions. Do
not use the older ten-question concept unless the product owner updates
the canonical requirements and backend contract.

### 2.3 Product truth rules

-   A generated wardrobe look must not contain items the user does not
    own or that the rules exclude.
-   Every generated look needs a clear explanation of why it suits the
    user's style and context.
-   If generation is unavailable, the Vault, profile, saved looks, and
    other non-generation surfaces must remain usable.
-   Weather-based recommendations require explicit `location_weather`
    consent. Do not silently request geolocation.
-   Every consent purpose is denied by default unless the service cannot
    function without it and the grant is recorded.
-   Users must be able to revoke consent, export their data, and delete
    their account through supported product flows.
-   The browser must never be treated as authoritative for image privacy
    processing. Follow the existing backend image pipeline.
-   The frontend must tolerate unknown API enum values and fields
    without crashing.

------------------------------------------------------------------------

## 3. Recommended frontend stack

Use the existing stack if it is already sound. If the repository does
not already contain a frontend with established conventions, use the
following default stack.

  -----------------------------------------------------------------------
  Concern                 Recommendation          Reason
  ----------------------- ----------------------- -----------------------
  Application framework   **Next.js App Router +  Strong route/layout
                          React + TypeScript**    structure, server
                                                  rendering for public
                                                  pages, and a widely
                                                  understood React
                                                  ecosystem for future
                                                  hires.

  Language                **TypeScript, strict    Makes API contracts,
                          mode**                  component props, and
                                                  domain states safer to
                                                  evolve.

  Styling                 **Tailwind CSS** using  Fast implementation
                          the currently supported with consistent tokens;
                          stable version          keep design tokens
                                                  central rather than
                                                  scattering arbitrary
                                                  values.

  UI primitives           **shadcn/ui + Radix     Accessible, inspectable
                          primitives where        components that can be
                          appropriate**           adapted to FAUE's
                                                  visual identity instead
                                                  of imposing a generic
                                                  theme. Do not install
                                                  the entire library
                                                  blindly.

  Icons                   **Lucide React**        Consistent line icons
                                                  and broad team
                                                  familiarity.

  Local UI animation      **Motion for React**    Small component
                          (`motion/react`)        transitions, card
                                                  states, menus, and
                                                  progressive reveal.
                                                  Respect reduced-motion
                                                  preferences.

  Signature scroll        **GSAP +                Strong control over
  storytelling            ScrollTrigger**, used   pinned sections and
                          selectively and loaded  carefully choreographed
                          only where needed       scroll sequences. Avoid
                                                  using GSAP for every
                                                  hover or button.

  Forms and validation    **React Hook Form +     Typed form validation
                          Zod**, if not already   with clear error
                          covered by the existing handling.
                          stack                   

  Server state            **TanStack Query** for  Prevents API fetching
                          a REST API-heavy        logic from being
                          authenticated app, if   duplicated across
                          the app needs           components. Pick one
                          client-side             clear approach per data
                          caching/refetching;     flow.
                          otherwise use Next.js   
                          server data patterns    
                          where appropriate       

  API contracts           Existing                Keeps UI aligned with
                          OpenAPI-generated       the backend gateway and
                          TypeScript client/types reduces contract drift.
                          if available; otherwise 
                          a typed `src/lib/api`   
                          adapter                 

  Unit/component tests    **Vitest + React        Tests user-visible
                          Testing Library** if    behaviour and domain
                          compatible with the     utilities.
                          repository; otherwise   
                          preserve the existing   
                          test runner             

  End-to-end tests        **Playwright**          Covers critical
                                                  journeys across browser
                                                  routes and responsive
                                                  layouts.

  Lint and formatting     Existing                Consistency and easier
                          ESLint/Prettier or      onboarding. Do not add
                          repository standard     competing formatters.

  Package manager         Preserve the            Avoid dependency churn.
                          repository's lockfile   If new project, use
                          and package manager     pnpm unless project
                                                  constraints favour npm.
  -----------------------------------------------------------------------

Official references: - Next.js installation and App Router defaults:
https://nextjs.org/docs/app/getting-started/installation - Tailwind CSS
framework setup:
https://tailwindcss.com/docs/installation/framework-guides/nextjs - GSAP
ScrollTrigger: https://gsap.com/docs/v3/Plugins/ScrollTrigger/ - Motion
accessibility and reduced motion:
https://motion.dev/docs/react-accessibility - Playwright:
https://playwright.dev/docs/intro - Vitest: https://vitest.dev/guide/

### 3.1 Why this stack is future-team friendly

-   React and TypeScript are widely understood and give a future
    frontend engineer a familiar foundation.
-   Next.js provides a clear route and layout convention rather than a
    custom routing system.
-   Tailwind tokens and reusable primitives make visual changes
    consistent.
-   Animation code is kept in dedicated components/hooks and does not
    contaminate business logic.
-   API calls go through a typed adapter rather than living in random UI
    components.
-   The feature-based directory structure below supports additions
    without creating one enormous component tree.

### 3.2 Do not over-engineer

Do not introduce micro-frontends, a custom design system package, a
global state library, GraphQL, a second API client, a motion framework
for every element, or a monorepo migration unless the existing
repository demonstrates a concrete need. The aim is a well-organised
application, not architecture theatre.

------------------------------------------------------------------------

## 4. Visual identity and art direction

### 4.1 Brand feeling

FAUE should feel like **quiet confidence, contemporary African style,
intelligence, and craftsmanship**. It should not feel like a loud
discount marketplace, a generic AI dashboard, or a neon gaming
interface.

Use: - deep charcoal and near-black foundations; - warm off-white / bone
surfaces and text; - one restrained neon/lime green accent for
interaction and moments of emphasis; - editorial fashion photography and
fashion-character illustration where useful; - large, confident
typography; - generous negative space; - deliberate asymmetry and
layered compositions; - clear visual hierarchy and a tactile sense of
fabric/material.

Avoid: - multicolour gradients everywhere; - glow effects around every
card; - excessive rounded cards that make the site look like a SaaS
admin template; - stock photos that feel unrelated to African users or
the brand; - using neon green for all body text; - excessive parallax,
scroll hijacking, or decorative motion that delays the product story.

### 4.2 Starting design tokens

These are initial values, not a substitute for checking existing brand
assets. Centralise them in CSS variables/design tokens and tune contrast
during implementation.

``` css
:root {
  --faue-ink: #111310;
  --faue-charcoal: #1A1D19;
  --faue-panel: #222620;
  --faue-bone: #F2EFE6;
  --faue-muted: #A7AA9F;
  --faue-line: rgba(242, 239, 230, 0.14);
  --faue-accent: #B7F34A;
  --faue-accent-ink: #14180D;
  --faue-danger: #E46C65;
  --faue-success: #A9D99A;
}
```

Rules: - Use accent green for primary CTA, active state, key metric, and
occasional motion cue --- not for every border. - Body text should
remain highly legible on both dark and light surfaces. - Use a
consistent spacing scale (e.g. 4/8/12/16/24/32/48/64/96 px) and a
restrained radius scale. - Use a typography system with one editorial
display face and a highly legible UI/body face. Prefer
licensed/self-hostable fonts and verify performance. Do not invent a
paid font dependency. - Use responsive image sizes, correct aspect
ratios, and intentional crop positions. - Do not use a generated AI
fashion image as a factual example of a user's real wardrobe. Label
illustrative/demo content.

### 4.3 Editorial imagery

Art direction should show diverse Black/African people and real styling
contexts without turning the entire brand into costume imagery.
Balance: - contemporary tailoring and smart casual; - native silhouettes
and formalwear; - Ankara, lace, Aso-Oke, and other fabrics in context; -
workwear, events, everyday looks, and personal expression; -
garment/fabric detail shots that communicate texture and construction.

Use properly licensed, commissioned, or generated assets. Do not scrape
other brands' sites or social feeds for production assets. Keep an asset
manifest with source, licence/permission, usage limits, and attribution
where required.

------------------------------------------------------------------------

## 5. Site map and navigation

### 5.1 Public routes

-   `/` --- landing page
-   `/style-dna` --- Style DNA introduction/quiz entry, if quiz can
    begin before sign-in under the existing product rules
-   `/how-it-works` --- optional explanatory route only if the landing
    page needs more room
-   `/privacy` --- privacy notice route or verified link to the
    canonical policy
-   `/terms` --- terms route or verified link to the canonical terms
-   `/auth/*` --- routes required by the existing authentication
    implementation

Do not add every optional route automatically. Prefer one excellent
landing page over many thin pages.

### 5.2 Authenticated routes

-   `/app` --- dashboard
-   `/app/style-dna` --- view/edit Style DNA through supported flows
-   `/app/vault` --- wardrobe items
-   `/app/vault/new` --- add item
-   `/app/fabric` --- fabric upload and native-style suggestions
-   `/app/looks/new` --- look request
-   `/app/looks/[id]` --- look detail
-   `/app/saved` --- saved looks
-   `/app/profile` --- profile and optional body profile
-   `/app/settings/privacy` --- consent, export, and account deletion
-   `/app/settings/account` --- authentication providers, logout, and
    account management where supported

Route names should be adapted to existing backend and app conventions.
Do not create empty routes simply to match this list.

### 5.3 Navigation behaviour

Desktop public navigation: - FAUE wordmark; - "How it works" anchor; -
"Style DNA" or "Discover your style" link; - sign-in link if
authentication exists; - one primary CTA.

Mobile public navigation: - compact wordmark; - one accessible menu
trigger; - primary CTA visible without forcing a user to open the menu
if layout allows.

Authenticated navigation: - clear dashboard/home; - Vault; - Create a
look; - Saved; - profile/settings. Use a compact bottom navigation on
mobile only if it is clear and does not crowd the viewport. Keep the
"Create a look" action prominent.

------------------------------------------------------------------------

## 6. Landing page --- detailed content and section plan

The landing page should be an editorial story that demonstrates the
decision-making product, not merely a list of features. Reference the
visual restraint of COS, editorial storytelling of SSENSE, and more
cinematic motion patterns such as DICH Fashion, but do not copy their
layouts or assets.

### Section 1 --- Hero: "Know what to wear. Know what to make."

**Purpose:** Make the product's value obvious in the first screen.

**Layout:** - full-viewport or near-full-viewport hero on desktop,
shorter and carefully composed on mobile; - charcoal background; -
wordmark and restrained navigation; - left or central editorial
headline; - concise supporting copy; - primary CTA: **Discover your
Style DNA**; - secondary CTA: **See how FAUE works**; - right-side or
background fashion portrait / editorial composition; - a small visual
hint of a Style DNA card or fabric sample, not a cluttered UI collage.

**Suggested copy:** - Eyebrow: `PERSONAL STYLE, MADE CLEAR` - Headline:
`Know what to wear. Know what to make.` - Body:
`FAUE helps you turn the clothes and fabrics you already own into looks that feel like you — and gives your tailor a clearer brief when it is time to make something new.` -
CTA: `Discover your Style DNA` - Secondary: `See how it works`

**Motion:** - wordmark appears first with a simple opacity/short
vertical reveal; - headline reveals in two intentional groups, not one
letter at a time; - image uses a gentle masked reveal or scale from 1.03
to 1.0; - CTA enters after the headline, with a subtle accent underline
or colour shift; - optional small fabric-texture layer drifts only a few
pixels on desktop. - No forced delay before the CTA becomes usable. - No
autoplay audio. If video is used, provide a poster, disable autoplay
under reduced motion, and keep mobile data cost in mind.

### Section 2 --- Problem statement: "You have the fabric. Now what?"

**Purpose:** Make the user feel understood.

**Layout:** - warm bone/off-white background to create a strong tonal
shift; - large editorial statement; - paired imagery: fabric detail and
an unfinished/uncertain outfit reference; - short copy about scattered
inspiration, outfit indecision, and unclear tailor briefs.

**Suggested copy:** \> You found the fabric. Saved the references. Sent
the screenshots.\
\> Now comes the hard part: deciding what actually works.

Follow with: \> FAUE brings the decision into focus --- around your
style, your occasion, and what you already own.

**Motion:** - section heading enters on viewport; - fabric close-up and
reference-image cards slide/fade into a considered arrangement; - avoid
pinning the whole section on mobile; - use a single transition to guide
the eye from "inspiration" to "decision".

### Section 3 --- Style DNA: "A clearer picture of your style."

**Purpose:** Introduce the six-question quiz and its shareable result.

**Layout:** - editorial portrait/illustration on one side; - Style DNA
card on the other; - show a fictional demo profile clearly marked
"Example profile"; - display dominant style, weighted traits, palette,
and a few styling cues; - CTA to start the quiz.

**Card example content (illustrative only):** - `STYLE DNA` -
`Modern Minimalist` - `92% profile match` only if the scoring system
truly returns this metric; otherwise use "Dominant style" rather than
implying model confidence. - traits such as "Clean lines", "Intentional
layers", "Quiet detail"; - palette chips; - `Share your card`.

**Motion:** - card assembles from two or three layers:
background/palette, profile text, then accent line; - use a short
progress animation for the quiz preview; - on scroll, reveal the card
with a gentle perspective/scale treatment; avoid aggressive 3D tilt; -
card remains legible and usable as a static composition on mobile and
reduced-motion settings.

**Important:** Style DNA scoring is deterministic and should not call an
AI model. Frontend displays the backend result or the canonical
deterministic scoring utility; it must not invent its own competing
score.

### Section 4 --- Wardrobe Vault: "Make more of what you own."

**Purpose:** Show that FAUE is not simply asking users to buy more
clothes.

**Layout:** - wardrobe item tiles or a clean collage of owned pieces; -
one highlighted item expands into a coordinated look; - short supporting
text: "Your wardrobe becomes a starting point, not a limitation."

**Motion:** - a few clothing tiles move into a composed outfit as the
user scrolls; - transitions should suggest arrangement, not imply items
are being purchased; - on mobile, convert the sequence into a normal
stacked layout or a tap/swipe interaction; - do not make content depend
on scroll position to be readable.

### Section 5 --- The decision: "A look that makes sense for you."

**Purpose:** Demonstrate the generated result and its reasoning.

**Layout:** - large look visual; - compact context labels: occasion,
mood, weather if permitted; - "Why this works for you" panel with three
short, specific reasons; - clear actions: Save look, Regenerate, Share.

**Example explanation structure:** - `Fits your Style DNA` --- connect
to an actual returned profile trait. - `Works for the occasion` ---
reference the user's selected context. - `Uses your wardrobe` ---
identify owned items used in the look. Never show fabricated reasoning
or unsupported body/appearance claims.

**Motion:** - visual resolves first, then explanation rows fade/slide
in; - loading state uses a calm progress treatment with explanatory
copy; - generation must not be represented as complete before the API
confirms success; - show a cancel/leave option if supported; preserve
form state on failure.

### Section 6 --- Fabric-to-tailor: "From fabric photo to a clearer brief."

**Purpose:** Present FAUE's strongest differentiator.

**Layout:** 1. photo of a fabric swatch; 2. suggested silhouette /
native style direction; 3. reference image and construction notes; 4.
WhatsApp-ready tailor brief preview.

**Suggested copy:** \> Your tailor knows how to sew. FAUE helps you
arrive with a clearer idea of what to ask for.

**Motion --- signature sequence:** - on desktop, the fabric swatch is
the anchor; - scroll reveals a style silhouette beside it; - the
reference card forms next; - final state shows a tailor-ready brief with
a clear "Send via WhatsApp" CTA; - use GSAP ScrollTrigger only for this
one carefully choreographed sequence; - if pinned scroll is used, keep
the pinned duration short and provide a natural static/stacked mobile
version; - do not make the user scroll through a long animation before
they can understand the value.

**WhatsApp handoff:** - use the actual generated/reference asset and
approved brief data; - construct a URL with properly encoded message
text; - open in a new tab/window or use the platform's standard share
behaviour; - do not include private profile fields, body measurements,
or unrelated user data in the message; - give the user a chance to
review the brief before sharing.

### Section 7 --- How it works: "Three steps. A better decision."

Use three concise steps: 1. `Know your style` --- answer six short
questions. 2. `Bring what you own` --- add wardrobe items or upload
fabric. 3. `Make the call` --- get a look, understand why it works, and
share it.

Use small line illustrations or simple UI samples. Do not add a fourth
step just to fill the layout.

### Section 8 --- Closing CTA

**Headline:** `Your next look starts with what you already have.`\
**Body:**
`Build your Style DNA and make your next outfit decision with more confidence.`\
**CTA:** `Discover your Style DNA`

Keep it visually strong and calm, with a dark background, a single lime
accent, and no artificial urgency.

### Section 9 --- Footer

-   wordmark;
-   concise positioning line;
-   links to privacy and terms;
-   contact/support link only if the destination exists;
-   social links only when official accounts are supplied;
-   copyright year generated dynamically;
-   no fabricated customer counts, press logos, testimonials, partner
    logos, or trust badges.

------------------------------------------------------------------------

## 7. Authenticated app --- page specifications

### 7.1 Dashboard (`/app`)

**Purpose:** Give the user one clear next action, not an analytics
dashboard.

Content order: 1. Welcome line that does not expose sensitive data. 2.
Primary action: `Create a look`. 3. Secondary actions:
`Add to your Vault`, `Style my fabric`. 4. Recent saved/generated looks
if available. 5. A useful next suggestion only when the backend supplies
it. 6. Style DNA summary card. 7. Clear empty state for new users.

Avoid generic KPI tiles, fake activity, and decorative charts. If
generation is unavailable, make the rest of the dashboard functional and
explain the limitation.

### 7.2 Style DNA quiz (`/style-dna` or authenticated equivalent)

-   Six questions exactly, unless the canonical product contract
    changes.
-   One question per screen or a compact progressive flow; choose the
    version that is most usable on mobile.
-   Show progress clearly, e.g. `Question 2 of 6`.
-   Support keyboard navigation and visible focus.
-   Provide a Back action without losing earlier answers.
-   Validate that a choice exists before moving forward.
-   Avoid forced timers, gamification noise, or invented "AI is
    thinking" states.
-   If answers are held locally before submission, define the storage
    lifetime and clear them after completion/logout as appropriate.
-   Submit once; handle retry/idempotency according to the API.
-   Results must display the six-style weighted profile using the
    canonical scoring response.

**Result page/card:** - dominant style label; - percentage weights only
if the contract defines them as weights, not confidence; - style
description grounded in canonical taxonomy; - palette and traits if
returned; - CTA: `Explore your Vault` / `Create a look`; - shareable
card with a high-contrast static fallback.

### 7.3 Wardrobe Vault (`/app/vault`)

**Primary jobs:** Browse owned items, add items, search/filter, edit
metadata, delete items, and record an item as worn.

Components: - responsive grid/list toggle only if useful; - item card
with image, category, optional colour/season metadata, and accessible
name; - search input; - filters for category and other fields that the
API supports; - `Add item` CTA; - empty state explaining the value of
starting with a few items; - skeleton/loading state; - retryable error
state; - confirmation dialog for destructive deletion.

**Add/edit flow:** - image picker/camera upload; - clear upload
constraints and progress; - category and metadata fields supported by
the API; - preview before save; - remove/replace image; - explicit
success/failure state. - Do not rely on client-side EXIF removal or face
redaction; those are server-authoritative pipeline responsibilities.

**Accessibility:** Every image needs meaningful alternative text or an
empty alt when decorative. Buttons must have explicit accessible names.
Filters should be usable without a mouse.

### 7.4 Create a look (`/app/looks/new`)

Fields: - occasion (from canonical API enum; unknown values should not
crash the UI); - mood (from supported values); - weather context: derive
from location only when `location_weather` consent is granted; otherwise
allow a manual choice if the product contract supports it; - optional
note with clear character limit and validation; - source/pool selection
if supported: Vault items or fabric flow; - primary CTA:
`Create my look`.

Behaviour: - preserve form values after a recoverable error; - explain
what will happen before a potentially slow request; - disable duplicate
submission while request is in flight; - provide cancel/back if
supported; - never imply a look exists before the API returns it; - do
not send a raw body profile or unnecessary identifiers to the model.

### 7.5 Look result (`/app/looks/[id]`)

Layout: - large primary visual; - context summary; - list of owned items
included; - "Why this works for you" explanation; - save/unsave; -
regenerate; - share/download only when supported; - `Send to tailor`
when this look came from a fabric/bespoke flow and has an appropriate
brief; - feedback action only if backend supports it.

State handling: - loading/skeleton; - completed; - generation in
progress; - failed with retry; - missing/deleted; - unsupported/unknown
fields. Never render an item as owned if the API does not establish that
relationship.

### 7.6 Fabric upload (`/app/fabric`)

-   explain accepted image types and max upload size from the API
    (current product requirement: maximum 20 MB);
-   validate MIME type and size before upload for usability, but rely on
    server-side validation for security;
-   preview image and allow replacement/removal before submission;
-   show upload and analysis progress without fabricated percentage
    precision;
-   keep the user informed about what happens to the image and relevant
    consent;
-   result should show native style suggestions, explanation, and a
    tailor-ready brief where supported;
-   allow the user to review and edit the brief before WhatsApp handoff;
-   provide retry and a safe error path;
-   do not promise a perfect rendering or garment outcome.

### 7.7 Saved looks (`/app/saved`)

-   grid/list of saved looks;
-   filter/search only if the data size and API justify it;
-   open detail;
-   unsave with a clear, reversible interaction where possible;
-   useful empty state;
-   never confuse "generated" with "saved".

### 7.8 Profile and settings

-   editable non-sensitive profile fields supported by the API;
-   body profile fields independently optional;
-   no required body measurements unless explicitly required by an
    approved flow;
-   consent settings separated by purpose;
-   weather/location consent default off;
-   export data;
-   delete account;
-   sign out;
-   clear explanation of the consequences of revoking consent;
-   confirmation for destructive actions. Sensitive profile fields must
    not be copied into analytics events or client logs.

------------------------------------------------------------------------

## 8. Motion design system

Motion should communicate meaning, sequence, and state. It should never
be a barrier to understanding or completing a task.

### 8.1 Motion principles

1.  **Editorial, not theatrical.** Motion supports the fashion story; it
    does not compete with it.
2.  **One signature moment.** The fabric-to-tailor sequence is the main
    cinematic scroll interaction. Other sections should be simpler.
3.  **Fast feedback.** Buttons and form controls respond immediately.
    Never delay basic interaction for aesthetic timing.
4.  **Progressive enhancement.** All content and CTAs remain
    understandable if animation fails, JavaScript is delayed, or reduced
    motion is enabled.
5.  **Mobile-first restraint.** Avoid pinned scroll sequences,
    hover-dependent information, heavy parallax, and large continuous
    animations on mobile.
6.  **Respect reduced motion.** Use `prefers-reduced-motion`; disable
    parallax/pinning and autoplay for users who request reduced motion.
    Replace large spatial movement with brief opacity/state changes.
7.  **Performance first.** Prefer transform and opacity; avoid animating
    layout-heavy properties, expensive blur, or giant shadow changes on
    every frame.
8.  **No scroll hijacking.** Do not trap the scroll wheel or force a
    fixed animation duration before the user can move on.

### 8.2 Motion tokens

Start with these ranges and tune by testing on real devices:

  ------------------------------------------------------------------------
  Token                               Starting range Use
  --------------------- ---------------------------- ---------------------
  `instant`                               80--120 ms pressed state, tiny
                                                     feedback

  `fast`                                 140--200 ms hover/focus, icon
                                                     response

  `standard`                             220--320 ms card/section reveal

  `editorial`                            400--650 ms headline/image reveal

  `sequence`                      700--1200 ms total staged multi-part
                                                     story, never blocking
                                                     interaction
  ------------------------------------------------------------------------

Use consistent easing, such as a restrained ease-out for entrance and a
short ease-in-out for state transitions. Do not use spring bounce on
every element.

### 8.3 Motion inventory

  ----------------------------------------------------------------------------------
  Component/section   Trigger             Motion                   Guardrail
  ------------------- ------------------- ------------------------ -----------------
  Hero headline       initial viewport    staggered opacity +      CTA is available
                      load                12--20 px vertical       immediately; no
                                          reveal                   typewriter

  Hero image          initial load        clipped reveal + slight  no flashing, no
                                          scale settling           high-frequency
                                                                   video

  Section headings    enter viewport      opacity + 16--24 px y    one-time reveal;
                                          movement                 content still
                                                                   readable before
                                                                   trigger

  Style DNA card      section enters      layers assemble in 2--3  do not imply
                                          steps                    model confidence

  Wardrobe            scroll progress     small group of tiles     disable/present
  composition                             align into look          static layout on
                                                                   mobile/reduced
                                                                   motion

  Look explanation    result ready        short stagger between    announce
                                          explanation rows         completion to
                                                                   assistive tech

  Fabric-to-tailor    scroll progress on  fabric → silhouette →    single signature
  sequence            desktop             reference → brief        pinned section;
                                                                   static stack
                                                                   fallback

  CTA                 hover/focus/press   colour/underline/scale   keyboard focus
                                          \<= 1.02                 visible; no
                                                                   motion-only
                                                                   meaning

  Dialog/sheet        open/close          opacity + small y/scale  focus trap,
                                                                   Escape, focus
                                                                   return

  Upload/generation   actual state change progress indicator +     never fake
                                          status text              progress or
                                                                   success

  Share card          button action       small confirmation       copy/share must
                                          feedback                 work without
                                                                   animation
  ----------------------------------------------------------------------------------

### 8.4 GSAP implementation rules

-   Put GSAP logic in dedicated client components/hooks, not in server
    components or domain utilities.
-   Register `ScrollTrigger` only where used.
-   Prefer GSAP context/scoped selectors and cleanup on unmount.
-   Kill/revert timelines and ScrollTriggers during cleanup.
-   Avoid global selectors that accidentally animate multiple
    components.
-   Lazy-load the heavy motion sequence below the fold if practical.
-   Use matchMedia or equivalent to provide desktop and reduced-motion
    variants.
-   Avoid animating layout properties where transform/opacity can
    achieve the same effect.
-   Do not apply scroll-triggered animation to form controls or critical
    app navigation.
-   Keep all content in the document and avoid hiding essential content
    indefinitely while waiting for a trigger.

### 8.5 Motion for React implementation rules

-   Use Motion for small component state transitions: tabs, menus, card
    reveal, dialog state, progress feedback.
-   Configure the application to respect the user's reduced-motion
    preference.
-   Avoid duplicating GSAP-driven transforms on the same element.
-   Do not add a global animation abstraction that obscures simple
    transitions.
-   For simple hover/focus effects, prefer CSS transitions.

### 8.6 Reduced-motion behaviour

When reduced motion is enabled: - remove parallax and scroll pinning; -
show the complete fabric-to-tailor story as a static stacked layout; -
replace large translations/scale effects with brief opacity transitions
or no animation; - stop autoplaying background video; - keep all
progress and state changes understandable; - do not remove essential
visual information or controls.

------------------------------------------------------------------------

## 9. Responsive behaviour

Test at minimum: - small mobile: 320--375 px; - common mobile: 390--430
px; - tablet: 768--1024 px; - laptop: 1280--1440 px; - large desktop:
1600 px and above.

Rules: - no horizontal overflow; - body copy remains comfortably
readable; - tap targets are comfortably sized (aim for approximately 44
× 44 CSS px for primary touch controls); - image crops preserve the
subject and garment details; - cards stack logically rather than
shrinking into illegibility; - mobile forms use appropriate input types
and visible labels; - menu, dialog, upload, and share flows work with
touch and keyboard; - avoid desktop-only hover affordances; - pinned
scroll sequences become normal content on mobile; - content is useful at
200% zoom and browser text scaling.

------------------------------------------------------------------------

## 10. Frontend architecture and code organisation

If a new frontend app is required, prefer a feature-oriented structure
similar to:

``` text
src/
  app/
    (marketing)/
      page.tsx
      layout.tsx
      privacy/page.tsx
      terms/page.tsx
    (auth)/
      auth/
        sign-in/page.tsx
        callback/page.tsx
        verify/page.tsx
    (product)/
      app/
        layout.tsx
        page.tsx
        style-dna/page.tsx
        vault/page.tsx
        vault/new/page.tsx
        fabric/page.tsx
        looks/new/page.tsx
        looks/[id]/page.tsx
        saved/page.tsx
        profile/page.tsx
        settings/
          account/page.tsx
          privacy/page.tsx
    api/                    # only when server routes are actually needed
    globals.css
    layout.tsx

  components/
    ui/                     # accessible primitives and adapted shadcn components
    layout/                 # nav, footer, shell, mobile navigation
    marketing/              # hero, editorial sections, CTA, footer
    motion/                 # reusable animation wrappers and motion preferences
    feedback/               # loading, empty, error, toast, confirmation
    data-display/           # cards, chips, badges, image treatments

  features/
    style-dna/
      components/
      hooks/
      schemas/
      types.ts
      scoring.ts            # only if canonical scoring is owned by frontend
      api.ts
    vault/
      components/
      hooks/
      schemas/
      types.ts
      api.ts
    looks/
      components/
      hooks/
      schemas/
      types.ts
      api.ts
    fabric/
      components/
      hooks/
      schemas/
      types.ts
      api.ts
    profile/
      components/
      hooks/
      schemas/
      types.ts
      api.ts
    auth/
      components/
      hooks/
      types.ts
      api.ts

  lib/
    api/
      client.ts
      errors.ts
      generated/             # generated API contracts if applicable
    auth/
    config/
    consent/
    analytics/
    utils/
    validation/

  styles/
    tokens.css

tests/
  unit/
  e2e/

public/
  images/
  fonts/
```

Adapt this to the existing repository instead of blindly creating every
folder. Use route groups only where they clarify layouts or access
control.

### 10.1 Component boundaries

-   **Page/route:** assembles features and owns route-level
    metadata/loading/error boundaries.
-   **Feature component:** implements a specific product job, such as
    uploading fabric or rendering a Style DNA card.
-   **UI primitive:** generic accessible control with no FAUE business
    logic.
-   **API adapter:** translates backend contracts into typed application
    data and normalises errors.
-   **Domain utility:** pure deterministic
    transformation/scoring/formatting function.
-   **Motion component:** visual animation only; it does not perform API
    requests or decide business rules.

Avoid a single `components.tsx`, a massive landing page file, or generic
abstractions that have only one caller and no meaningful reuse.

### 10.2 State management

-   Use React local state for transient UI state (open dialog, selected
    tab, unsaved form input).
-   Use the chosen server-state strategy for remote API data.
-   Keep form state in form components.
-   Do not mirror the entire API cache into a global store.
-   Do not persist sensitive profile data or tokens in `localStorage`.
-   Do not introduce Zustand/Redux unless the actual product
    requirements demonstrate a cross-route client state need that cannot
    be handled cleanly otherwise.

### 10.3 API layer

All API access must go through one typed boundary. It should provide: -
base URL from environment configuration; - request/response types from
the actual OpenAPI contract when available; - consistent
authentication/session behaviour matching backend design; - safe error
normalisation; - request cancellation where appropriate; - typed
handling of unknown enum values; - no secret keys in the browser; - no
logging of request bodies containing PII.

Do not guess endpoint names. Inspect the gateway contract and current
service implementation first. If an endpoint does not exist, document
the frontend dependency rather than fabricating it.

### 10.4 Authentication

The current product specification describes passwordless magic-link
authentication plus Google/Apple providers. Implement only the flows the
backend actually supports. Key requirements: - no password UI unless the
canonical contract has changed; - magic-link completion must follow the
security design; do not consume a link on a simple `GET` if the backend
contract forbids it; - support cross-device verification code if
required by the backend; - account-provider linking only through
verified-email rules; - logout and refresh behaviour must match the
backend; - provide account deletion where required and supported; -
never store access/refresh tokens insecurely just to simplify UI state.

### 10.5 Analytics and telemetry

Use the existing approved analytics provider if one exists. Track
product events, not personal data. Candidate event names: -
`style_dna_started` - `style_dna_completed` - `style_dna_card_shared` -
`vault_item_added` - `look_generation_requested` -
`look_generation_succeeded` - `look_generation_failed` - `look_saved` -
`item_marked_worn` - `fabric_upload_started` -
`fabric_suggestion_completed` - `tailor_brief_shared`

Event payloads must not contain email, name, exact location, body
measurements, raw user notes, raw image URLs, auth tokens, or model
prompts. Respect consent. Avoid adding an analytics provider before the
consent and privacy behaviour is defined.

------------------------------------------------------------------------

## 11. Accessibility and inclusive design

Minimum standard: target **WCAG 2.2 AA** for the implemented user flows.

-   Semantic headings and landmarks.
-   Visible keyboard focus.
-   Logical keyboard order and no keyboard traps except accessible modal
    focus management.
-   Correct labels and accessible validation messages.
-   Colour contrast checked for text, controls, states, and focus.
-   Do not communicate status using colour alone.
-   Provide text alternatives for meaningful images.
-   Respect reduced motion.
-   Announce asynchronous status changes with appropriate live regions.
-   Provide focus return after closing dialogs.
-   Use accessible error summaries for multi-field forms when needed.
-   Test with keyboard-only navigation and at least one screen
    reader/browser combination before release.
-   Make the landing page content usable without animation.
-   Do not use auto-advancing carousels for essential content.

------------------------------------------------------------------------

## 12. Performance requirements

The product is image-heavy and may be used on mobile connections. Avoid
making cinematic motion expensive to load.

-   Use Next.js image optimisation or the repository's established image
    pipeline.
-   Provide responsive image sizes and modern formats where supported.
-   Reserve image dimensions to avoid layout shift.
-   Lazy-load below-the-fold media and animation code.
-   Keep hero media optimised; avoid shipping huge video files as the
    default.
-   Avoid loading GSAP on routes/sections that do not use it.
-   Prefer CSS for simple interactions.
-   Avoid unnecessary client components; keep static marketing content
    server-rendered where practical.
-   Prevent layout shifts when fonts/images load.
-   Test on throttled mobile network and a mid-range mobile device.
-   Aim for strong Core Web Vitals; establish baseline measurements
    before tuning rather than inventing a score.
-   The product should remain navigable if image generation or other AI
    services are slow or unavailable.

------------------------------------------------------------------------

## 13. Error, loading, empty, and offline states

Every data-driven surface must define the states below, not just its
happy path.

### Loading

-   skeletons should resemble the final layout;
-   show a clear status for long-running generation;
-   preserve user input;
-   never animate a fake percentage unless the backend reports real
    progress.

### Empty

-   explain why the empty state matters;
-   offer one next action;
-   do not shame users for having few clothes or no saved looks;
-   avoid placeholder content that looks like real user data.

### Error

-   explain what happened in plain language;
-   offer retry where safe;
-   keep unrelated features usable;
-   do not show stack traces, raw backend responses, secrets, or
    provider error messages;
-   preserve recoverable input.

### Generation unavailable

-   explain that look generation is temporarily unavailable;
-   let the user return to the Vault, profile, saved looks, or retry
    later;
-   never make the entire app dependent on generation service
    availability.

### Upload failure

-   distinguish file type/size problems from server failure;
-   permit replacement and retry;
-   do not leave a broken preview or claim the file was saved when it
    was not.

------------------------------------------------------------------------

## 14. Security and privacy requirements

These are product requirements, not optional polish.

-   Never expose provider keys or backend secrets in `NEXT_PUBLIC_*`
    variables.
-   Validate uploaded file size and declared type in the client for user
    feedback; server must perform authoritative MIME sniffing and safe
    re-encoding.
-   Treat all client-side data as untrusted.
-   Never place PII in logs, analytics, error reporting, URLs, or model
    prompts.
-   Do not log full API payloads in production.
-   Avoid persisting tokens or sensitive body profile data in browser
    storage.
-   Ensure consent is purpose-specific and denied by default.
-   Weather/location permission must be requested only when needed and
    only after clear explanation.
-   Revocation should immediately affect the relevant feature according
    to backend contract.
-   Keep export and account deletion flows visible and understandable.
-   Use HTTPS in production and secure cookie/session settings according
    to the existing auth architecture.
-   Follow the backend's CSP, CORS, CSRF, and session requirements; do
    not weaken them to make local development easier.
-   Never put raw personal information in shareable Style DNA cards
    unless the user explicitly chose it.
-   Review WhatsApp message text before opening the external share
    target.

------------------------------------------------------------------------

## 15. Testing strategy and acceptance criteria

### 15.1 Unit tests

Test pure logic and formatting: - six-question quiz progress and
validation; - Style DNA rendering for all known profile categories; -
unknown enum fallback; - API error normalisation; - consent-gated
weather UI; - WhatsApp brief URL/message encoding; - no duplicate
submission; - image file size/type feedback; - reduced-motion branch
selection where testable.

If scoring is implemented in the frontend, write tests against the
canonical scoring rules. Do not duplicate backend scoring if the backend
is authoritative.

### 15.2 Component tests

Test user-observable behaviour: - quiz can go forward/back and cannot
submit incomplete answers; - upload shows preview and supports
replacement; - look result presents loading/success/error states; -
save/unsave reflects server result; - dialog supports Escape and focus
management; - menu and controls work by keyboard; - reduced-motion users
still receive all essential content.

### 15.3 End-to-end tests (Playwright)

Minimum critical journeys: 1. Landing page loads and primary CTA
navigates correctly. 2. Sign-in flow works against a test environment or
a clearly isolated mocked API in test mode. 3. User completes
six-question Style DNA flow and sees the result. 4. User adds a wardrobe
item and sees it in the Vault. 5. User requests a look and receives a
proper result or clear failure state. 6. User saves and reopens a look.
7. User uploads fabric and can review the tailor brief. 8. WhatsApp
handoff opens a correctly encoded URL without leaking disallowed data.
9. User can revoke weather consent and the UI stops requesting/using
location weather. 10. Navigation and key flows work at mobile and
desktop viewport sizes. 11. Reduced-motion mode removes pinned/parallax
motion and preserves content.

### 15.4 Release acceptance checklist

-   [ ] Production build succeeds.
-   [ ] Type-check passes.
-   [ ] Lint passes.
-   [ ] Unit/component tests pass.
-   [ ] Critical Playwright journeys pass.
-   [ ] No horizontal overflow at supported viewport sizes.
-   [ ] Keyboard navigation and focus states verified.
-   [ ] Reduced-motion behaviour verified.
-   [ ] Landing page works if animation fails.
-   [ ] No fabricated social proof, partner logos, user counts, or
    product claims.
-   [ ] No secrets or PII in client bundles/logs/analytics.
-   [ ] API contracts match the current backend.
-   [ ] All incomplete or mocked integrations are explicitly documented.

------------------------------------------------------------------------

## 16. Implementation phases

Claude Code should work in these phases and keep the app runnable at the
end of each.

### Phase 0 --- Repository reconnaissance

-   inspect existing code, contracts, scripts, environment variables,
    and deployment;
-   identify current frontend status and reusable assets;
-   produce a short implementation plan;
-   do not rewrite working architecture.

**Exit check:** A written summary of current state and a scoped plan.

### Phase 1 --- Foundation and design tokens

-   configure/verify Next.js, TypeScript, linting, tests, and Tailwind
    if needed;
-   set up tokens, typography, layout primitives, navigation, buttons,
    inputs, cards, dialogs, and feedback states;
-   establish route layouts and error/loading boundaries.

**Exit check:** App builds; design tokens and basic accessible
components exist.

### Phase 2 --- Marketing landing page

-   implement hero, problem narrative, Style DNA section, Vault section,
    look explanation, fabric-to-tailor sequence, how-it-works, closing
    CTA, and footer;
-   use realistic licensed/demo assets;
-   implement reduced-motion and mobile fallbacks;
-   ensure the page is complete without animation.

**Exit check:** Responsive, accessible landing page with one signature
motion sequence and a working CTA.

### Phase 3 --- Authentication and app shell

-   connect to the real supported auth flow;
-   build protected app layout/navigation;
-   handle loading, unauthenticated, expired session, and error states.

**Exit check:** Authentication and route protection work against the
actual API contract.

### Phase 4 --- Style DNA

-   implement six-question flow and result card;
-   wire the canonical API/scoring contract;
-   add shareable card and accessible static fallback.

**Exit check:** deterministic, tested flow with no invented scoring
behaviour.

### Phase 5 --- Vault and profile

-   build CRUD flows supported by the gateway;
-   implement image preview, upload states, search/filter, optional
    profile fields, and settings entry points.

**Exit check:** user can manage wardrobe items and profile data with
proper error handling.

### Phase 6 --- Look generation and fabric-to-tailor

-   connect create-look flow;
-   display results and reasoning;
-   implement save/regenerate/share;
-   implement fabric upload, suggestion result, and reviewed WhatsApp
    handoff.

**Exit check:** the core product loop works end-to-end; AI failure does
not break unrelated pages.

### Phase 7 --- Hardening

-   add/finish unit, component, and Playwright tests;
-   run accessibility and responsive checks;
-   check performance, consent, privacy, and security boundaries;
-   update developer documentation and environment example.

**Exit check:** release checklist completed with truthful test results.

------------------------------------------------------------------------

## 17. Future-proofing for a frontend engineer joining later

-   Keep code conventions consistent and document non-obvious decisions.
-   Maintain a concise `README.md` with setup, scripts, env variables,
    architecture, test commands, and deployment notes.
-   Maintain `.env.example` with placeholder values only.
-   Use clear PR-sized changes and avoid unrelated refactors.
-   Add ADRs for meaningful architectural decisions (e.g. API client,
    auth handling, animation ownership).
-   Keep design tokens central and document component variants.
-   Keep a component showcase or Storybook only if the team needs it; do
    not add it automatically for a solo MVP.
-   Use accessible, composable primitives rather than opaque
    mega-components.
-   Avoid styling directly against generated DOM structure from a
    library.
-   Document every mocked API and remove or isolate mocks before
    production.
-   Do not bind the product's domain logic to GSAP, Motion, or a
    specific component library.
-   Make animation optional enhancement: content and business flows must
    work when the animation layer is removed.

------------------------------------------------------------------------

## 18. Reference direction --- inspiration, not replication

Use these references to study principles, not to copy visual designs or
source code:

-   **DICH Fashion** --- cinematic transitions and fashion-focused
    movement: https://dich-fashion.webflow.io/
-   **SSENSE** --- editorial image-led fashion storytelling and content
    hierarchy: https://www.ssense.com/
-   **COS** --- restraint, negative space, material detail, and premium
    minimalism: https://www.cos.com/
-   **Awwwards Fashion collection** --- broad visual research and
    current interaction patterns:
    https://www.awwwards.com/websites/fashion/
-   **GSAP ScrollTrigger documentation** --- implementation details for
    scroll-controlled sequences:
    https://gsap.com/docs/v3/Plugins/ScrollTrigger/
-   **Motion accessibility documentation** --- reduced-motion behaviour:
    https://motion.dev/docs/react-accessibility

**FAUE's own signature:** fabric → style decision → finished look →
tailor-ready reference. This should be the memorable narrative, not a
copy of another fashion website's animation.

------------------------------------------------------------------------

## 19. Decisions and assumptions to verify before production

Claude Code should inspect the repository and mark each item as
**confirmed**, **not present**, or **requires product decision**:

-   [ ] Existing frontend framework and version.
-   [ ] Current gateway base URL and environment naming.
-   [ ] Existing OpenAPI contract / generated TypeScript types.
-   [ ] Actual supported authentication providers and callback routes.
-   [ ] Exact Style DNA taxonomy, question copy, option copy, and
    scoring payload.
-   [ ] Actual endpoints for Vault CRUD, look generation, saves, fabric
    upload, and share metadata.
-   [ ] How look images are stored, delivered, and permission-checked.
-   [ ] Whether image generation and fabric analysis return asynchronous
    job IDs or synchronous responses.
-   [ ] Actual supported occasion/mood enums and unknown-value
    behaviour.
-   [ ] Exact consent API and weather provider behaviour.
-   [ ] Official privacy policy, terms, contact email, and social links.
-   [ ] Licensed/approved production imagery and brand assets.
-   [ ] Whether the current product already has analytics and error
    reporting.
-   [ ] Deployment target and required environment variables.
-   [ ] Whether the marketing landing page and authenticated app should
    live in one Next.js app or separate deployments, based on existing
    architecture.

Do not block implementation on optional copy or imagery if sensible
placeholders can be clearly isolated and labelled. Do block any claim or
interaction that would misrepresent backend functionality, privacy
behaviour, or product status.

------------------------------------------------------------------------

## 20. Definition of done

The frontend is ready for review when:

1.  The landing page tells the complete FAUE story and has a strong,
    restrained motion identity.
2.  Users can understand the product without animations.
3.  The core loop is implemented against real, verified backend
    contracts.
4.  The six-question Style DNA flow and card are accurate to the product
    specification.
5.  Wardrobe, look, fabric, save, and tailor-handoff states are coherent
    and accessible.
6.  Mobile layouts are first-class, not desktop layouts squeezed down.
7.  Reduced-motion users receive an equally complete experience.
8.  API, consent, authentication, image, and privacy rules are
    respected.
9.  Tests, type-check, lint, and production build results are reported
    honestly.
10. A future frontend engineer can run the app, understand the
    architecture, and add a feature without reverse-engineering a giant
    component.

**Final instruction:** Prioritise a complete and trustworthy product
loop over decorative complexity. FAUE should feel premium because every
design and engineering decision is deliberate --- not because every
element moves.
