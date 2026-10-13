# Website review: gap report and plan

**Written:** 2026-10-09 · **Inputs:** `FAUE_Website_Review_and_Acceptance_Criteria.docx` (review A), `FAUE Website Design Review.docx` (review B) · **Checked against:** the live build of `landing/` and its source

Method: each claim in the two reviews was checked against the code or the built output. Nothing here is scored from memory or from the reviews' own wording. Items I could not test are marked **not verified**.

## Verdict on the reviews

Both reviews reach the same conclusion: the idea, copy and honesty are strong, and the page explains FAUE well but does not yet convert visitors or invite partners. The code confirms that. Most of what they ask for is small and does not need a rewrite.

Two places where I would not follow them:

- **Palette.** Review A says charcoal and off-white. FAUE's palette comes from `design-tokens.md` and the Figma file (obsidian green, forest, sage, peach, one gold accent). The docs win over a generic brief. Keep it.
- **Review B could not see the rendered page.** Its visual remarks are guesses. Its structural and copy findings are sound and are confirmed below.

## Confirmed findings

| # | Finding | Evidence | Priority | Raised by |
|---|---|---|---|---|
| 1 | Pre-launch status appears once, in the footer. Hero and nav never say the app is not out | `out/index.html`: "not out yet" x1, in `site-footer.tsx` | P0 | B |
| 2 | No sign-up capture anywhere. The only contact is a Gmail `mailto` in the footer | No form besides `/contact`; footer `mailto:faueofficial@gmail.com` | P0 | A, B |
| 3 | No partner path. Nav has no Partners or For tailors, though a tailor is one of the four stories | `site-header.tsx` links; no `/partners` route | P1 | A, B |
| 4 | Product is shown only as drawings and stock photos. No screen of the app | `hero.tsx`, `look-section.tsx`, `vault-section.tsx` use cards and art | P1 | B (A: "product proof") |
| 5 | Section order puts four stories before the product. "Three steps" is second to last | Order in `page.tsx`: Hero, Problem, Stories, Style DNA, Vault, Look, Fabric, How it works, CTA | P1 | A, B |
| 6 | Hero secondary button is "Read the stories", which sends people away from the product | `hero.tsx:46` | P1 | B |
| 7 | Homepage title is the tagline only | Built `<title>` | P1 | B |
| 8 | "Example" and similar notes appear 12 times as separate italic lines | Count in built homepage text | P2 | B |
| 9 | Nothing near the photo features says how images are stored or deleted | `vault-section.tsx`, `fabric-sequence.tsx` | P1 | A, B |
| 10 | Photo credit line reads as developer text and points to a file | `site-footer.tsx` | P2 | B |
| 11 | No pricing or cost line | Copy audit; FAQ says "not announced" | P1 | B |
| 12 | Mobile weight is high for a data-conscious user. See below | Measured from `out/` | P1 | A, B |
| 13 | Analytics events (`quiz_start`, `quiz_complete`, `result_share`, `early_access_signup`) do not exist | No analytics code. Consent switch is ready | P1 | A, B |
| 14 | The quiz on the site is a read-only preview, so the primary journey stops before a result | `/style-dna` copy says so. This is labelled honestly | P0 for the funnel | A, B |
| 15 | Desktop fabric section pins the screen for about 85% of a viewport of scroll | `fabric-sequence.tsx:48` | P2 | A (no scroll hijacking) |
| 16 | About page does not say who is behind FAUE | `about/page.tsx` | P2 | B |

**Already passing** (verified): no broken internal links across the exported pages; no horizontal overflow at 320 to 1600 px; axe checks pass on every page; reduced motion shows all content; forms validate and report real failure; privacy, terms and cookies pages exist; social links are only the two real accounts; every example is labelled.

### Weight measurement (finding 12)

| Item | Size |
|---|---|
| Homepage HTML | 150 KB |
| JavaScript, gzipped | about 227 KB |
| Fonts | 173 KB |
| Above-the-fold hero image (`drape-black.webp`, 1200x1800) | 435 KB |
| Total images referenced on the page | 2.1 MB (21 of 23 are lazy-loaded) |

That is roughly 0.9 MB before the first scroll, and the hero image is about half of it. Not measured on a real device or a throttled connection.

## Proposed changes, in order

### Batch A: no new decisions, no backend (do now)

1. **Say the status up front.** One honest line beside the hero CTA, for example "The app is not out yet. Try the Style DNA preview and be first to know." No invented launch date.
2. **Reorder the homepage:** Hero, Problem (short), Three steps, Style DNA, Fabric to tailor, Vault and Look, Stories, Partners teaser, final CTA. The stories keep their labels.
3. **Hero copy:** shorten the subhead and make the secondary button "See how it works" linking to the three steps.
4. **Title:** add what FAUE is, for example "FAUE — Personal styling and tailor briefs for African fashion" (59 characters).
5. **One "Example" tag component** plus a single explainer near the first demo, replacing the repeated italic notes.
6. **Photo privacy note** near the Vault and fabric sections, drawn only from the privacy page (what is stored, originals discarded after cleaning, deletion in the app), linking to `/privacy`.
7. **Credits:** reword the footer line and add a `/credits` page generated from `ASSETS.md`.
8. **Partners page (`/partners`)** with separate sections for tailors, fabric sellers, brands, event planners and press. Plain value statements, no logos, no claims, no promised numbers. A "For tailors" teaser under Baba Segun. Linked in the footer first, then the nav once it has content. The form reuses the contact form with a Partnership topic and extra fields (organisation, role, interest).
9. **Performance pass:** shrink the hero image to about 150 KB, load Playfair only where the card needs it, load the consent panel lazily, and replace the Motion library in the header with CSS if it is only the menu. Re-measure after.

### Batch B: needs a decision or a backend piece

| Item | What it needs |
|---|---|
| Early-access capture | Backend `POST /v1/early-access` (email, optional WhatsApp number, consent, dedupe) with its own retention rule. Add to the backend plan. Consent wording must be separate from the privacy tick. |
| WhatsApp sign-up | A WhatsApp Business number and a decision on messaging policy. |
| "Free to start" line | Founder confirmation that it is true. I will not write it otherwise. |
| Analytics | Choice of tool. Events fire only when the Usage statistics switch is on. Cloudflare Web Analytics is cookieless but has no custom events. |
| Domain email | Cloudflare Email Routing (free) can forward `hello@` and `partners@` to the Gmail inbox. Then swap `CONTACT_EMAIL`. |
| About: who is behind FAUE | Founder-written facts. |
| Pilot offers (tailor, vendor, brand) | Founder decision on what FAUE can honestly deliver. |

### Batch C: depends on product work

- **Product screens.** The app is not built, so any screen would be a design preview. I can build faithful frames from the Figma Hi-Fi designs, tagged "Design preview". Real screenshots replace them when the app exists.
- **Real social proof** needs the closed beta.
- **Inline first quiz question** that carries into `/style-dna`: build it together with the real quiz (quiz before sign-up), to avoid throwaway work.
- **Per-result share previews:** the share-page Worker from the backend plan.

## Scorecard (0 to 4, scored only on what was inspected)

| Area | Weight | Score | Evidence |
|---|---|---|---|
| Positioning and brand clarity | 15% | 3 | Clear tagline and promise. Status hidden |
| Core CTA and Style DNA journey | 20% | 2 | CTA works; the quiz is a labelled preview with no result |
| Visual quality and consistency | 15% | 3 | Consistent system. Not checked on a real phone |
| Mobile usability and performance | 15% | 2 | No overflow, axe clean. Heavy first load. Device not tested |
| Product-status accuracy and trust | 10% | 3 | Examples and composites labelled. Status buried |
| Early-access conversion and analytics | 10% | 0 | Absent |
| Partnership readiness | 5% | 1 | Contact form only |
| Accessibility and motion | 5% | 3 | Axe passes, reduced motion tested. One pinned section |
| Maintainability and technical quality | 5% | 3 | Typed, tested, documented |
| **Weighted total** | | **2.25 / 4 (56%)** | |

Batch A should lift positioning, trust, partnership and performance without any new product work. The two biggest remaining points are the real quiz result and early-access capture.

## Definition-of-done status (review A, section 13)

Met: no broken links or overflow, reduced motion respected, privacy and contact reachable, build and tests pass, forms report real failure, claims match what is built.
Not met: a first-time visitor can explain FAUE within seconds (not tested with people), the CTA leads to a complete experience, the quiz works start to finish, an early-access form exists, analytics events exist, real user testing has been done.
