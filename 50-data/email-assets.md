# Email Header Assets

**Stage:** MVP · **Owner:** design · **Consumed by:** `api-gateway/app/modules/notify/templates/email/`

The templates support a full-bleed header image. The **slots exist and render**;
the artwork does not exist yet and needs exporting from Figma.

---

## Required assets

| Template | Slot | When it sends | What it should say visually |
|---|---|---|---|
| `welcome_new` | `header_welcome_new` | First signup | Arrival. This person has never seen the product — warm, not explanatory |
| `welcome_back` | `header_welcome_back` | Re-engagement after a lapse | Continuity. Their wardrobe is still here. Calmer than the new-user header |
| `dna_card_ready` | `header_dna` | Quiz completed | Identity and reveal — this is the shareable moment |
| `look_ready` | *(none)* | Look generated | Uses the look render itself, not a static header |
| `magic_link` | *(none)* | Sign-in | **Deliberately no image.** See below |
| `detty_december` | `header_seasonal` | Cultural campaign | Seasonal, changes per campaign |

## Specification

| Property | Value | Why |
|---|---|---|
| Dimensions | **1040 × 400** | Rendered at 520 × 200; 2× for retina |
| Format | PNG or JPEG | Not SVG — Gmail and Outlook strip it |
| Weight | **under 100 KB** | Metered mobile data, and heavy mail is throttled |
| Colour | Design tokens only | See [`../40-frontend/design-tokens.md`](../40-frontend/design-tokens.md) |
| Safe area | 80 px inset | Clients crop the edges inconsistently |
| Text in image | **None** | Blocked images leave the message invisible, and it cannot be translated |
| Hosting | CDN, immutable URL | Never a relative path — email has no origin |

## Why the magic-link email has no header image

It is the only email that **must** arrive. Image-heavy mail is filtered more
aggressively, and images are blocked by default in Outlook and for many Gmail
users. If a sign-in email lands in spam, the user cannot sign in at all — there
is no fallback path.

Every other template can afford to look plainer in a client that blocks images.
This one cannot afford to be filtered.

## Alt text is not optional

Images are blocked by default for a large share of recipients. The alt text is
the message for those people, so it carries meaning rather than describing
decoration:

```
header_image_alt: "Welcome to FAUE"          ✅ carries the message
header_image_alt: "Header image"             ❌ says nothing
header_image_alt: ""                         ❌ screen readers announce the filename
```

## Wiring an asset up

Both variables are optional; supplying neither skips the block entirely.

```python
render(
    "welcome_new", "email",
    quiz_url="https://faueofficial.com/quiz/1",
    header_image_url="https://cdn.faueofficial.com/email/welcome-new-v1.png",
    header_image_alt="Welcome to FAUE",
)
```

Version the filename (`-v1`) rather than replacing in place. Email clients and
proxies cache aggressively, and a replaced image shows the old artwork for weeks.

## Previewing

```bash
cd api-gateway
python scripts/preview_emails.py --open
```

Renders every template with realistic sample values to `preview/` and opens an
index. Realistic values matter — a long look title and a two-digit count are
where a layout actually breaks.
