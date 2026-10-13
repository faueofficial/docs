# FAUE brand

## Wordmark

`FAUE` in caps, set in Instrument Serif (Regular), letters converted to outlines. Letter spacing 0.03 em. The rectangle padding is 0.6x the letter height on all sides, measured from the letter edges.

| File (in `logo/svg/`, PNGs in `logo/png/` at 256/512/1024/2048 px wide) | Use |
|---|---|
| `faue-wordmark-box-green` | Primary. Cream letters on `#0F3D2E` |
| `faue-wordmark-box-light` | Green letters on `#F7F8F8`, for placing on dark green |
| `faue-wordmark-box-outline` | Green outline, transparent background |
| `faue-wordmark-box-outline-white` | White outline, for dark backgrounds |
| `faue-wordmark-box-black` | One-colour print (white letters on black) |
| `faue-wordmark-only-green` / `-white` | Letters only, no rectangle |

## Colour

Brand anchor `#0F3D2E` and page background `#F7F8F8`, from `docs/40-frontend/design-tokens.md`.

## Icon

`logo/icon/`: square FAUE icon (cream FAUE wordmark on `#0F3D2E`), used for the favicon, apple-touch icon and PWA sizes. SVG with rounded corners, PNGs full-bleed (the OS applies its own mask). Readable at 32 px and up; at 16 px it reads as the brand block.

## Social profile picture

`social/`: square 1024 px profile pictures for Instagram, X and any other network, as SVG and PNG. The wordmark sits inside the central circle, so circular crops (Instagram, X personal view) and rounded-square crops (X organisation view) both keep the full word. Readable at 48 px.

| File | Use |
|---|---|
| `faue-pfp-green` | **Primary.** Cream letters on `#0F3D2E`, the same as the site icon. Use this everywhere first |
| `faue-pfp-obsidian` | Cream letters on `#051611` with the gold accent bar. For dark-mode contexts or a seasonal alternate |
| `faue-pfp-light` | Green letters on `#F7F8F8`, for light-only surfaces |

Upload the PNG. Keep one picture across every network so the accounts read as the same organisation.

### Banners and info images

| File | Size | Use |
|---|---|---|
| `faue-x-header-1500x500.png` | 1500x500 | X header. The left 240 px is kept clear because the profile picture overlaps the bottom-left corner. Text sits in the middle band so mobile cropping does not cut it |
| `faue-info-strip-1200x300.png` | 1200x300 | The "footer" image: logo, tagline, status and all contact details in one strip. For email signatures, documents, link cards and the bottom of decks |
| `faue-about-card-1080x1350.png` | 1080x1350 (4:5) | A pinned Instagram post that says what FAUE is, with contact details and "App coming soon" |

Sources are in `social/source/*.html` (open in Chrome, screenshot at the size above). The cloth in the lettering and background is stock photography from Pexels, as on the website (see `landing/ASSETS.md`); replace it with commissioned imagery before paid promotion. Contact lines show `hello@faueofficial.com` and `@faueofficial`; the info strip also shows `partners@faueofficial.com`. Update them in the source files if an address changes.

## Fonts

`fonts/InstrumentSerif-Regular.ttf` (SIL OFL, licence in `fonts/OFL.txt`) is used for the logo only. Product typefaces are unchanged: Playfair Display for headings and Plus Jakarta Sans for UI (see design tokens).

## Style DNA illustrations

`illustrations/style-dna/share-cards/`: one share card per persona (CM, OR, SL, SC, CE, NF) in 4:5 (1080x1350, Instagram/X) and 9:16 (1080x1920, stories). Each has the dominant persona, a two-line description, a blend bar, a six-colour palette, four trait chips and the sign-off, on a persona gradient with a pattern. Percentages, descriptions, palettes and traits are placeholder copy until the real tier lines and card renderer exist.

`illustrations/style-dna/input-diagrams/`: five concept images of the card with its six quiz inputs attached (core identity, occasion, energy, palette, fit, risk appetite), 3200x2000.

## Not yet made

Brand sheet PDF, clear-space and minimum-size rules.
