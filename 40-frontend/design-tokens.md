# Design Tokens

**Stage:** MVP · **Source:** Figma `KtCAHrBGLQXEdQrPbWJVVS`, page `FAUE (Design System)` (`65:27`), extracted 2026-08-17

Extracted directly from the design-system page. Where this document and Figma disagree, re-extract rather than guessing — the file had no published styles at extraction time, so these values come from the swatch frames themselves.

---

## 1. Colour

### Primary — green

The brand colour. `primary-500` is the button fill, the active state, and the anchor of every gradient.

| Token | Hex | Use |
|---|---|---|
| `primary-50` | `#BCC9C4` | Chip focus, secondary button hover |
| `primary-100` | `#A9B9B4` | Subtle fills |
| `primary-200` | `#829A92` | Borders on tinted surfaces |
| `primary-300` | `#5C7B71` | Secondary text on light green |
| `primary-400` | `#355C4F` | **Primary button hover** |
| `primary-500` | `#0F3D2E` | **Primary button, brand anchor** |
| `primary-600` | `#0D3327` | Pressed |
| `primary-700` | `#0A291F` | **Primary button focus** |
| `primary-800` | `#082018` | Deep surfaces |
| `primary-900` | `#051611` | Darkest, gradient ends |
| `primary-hover` | `#145C45` | Named "Green Hover" in the file; distinct from `primary-400` |

### Neutral — grey

| Token | Hex | Use |
|---|---|---|
| `neutral-50` | `#F7F8F8` | Page background |
| `neutral-100` | `#EDEEF1` | Card background, dividers |
| `neutral-200` | `#D8DBDF` | Borders |
| `neutral-300` | `#B6BAC3` | Disabled text |
| `neutral-400` | `#8E95A2` | Placeholder |
| `neutral-500` | `#6B7280` | Secondary text |
| `neutral-600` | `#5B616E` | Body text on light |
| `neutral-700` | `#4A4E5A` | Strong body |
| `neutral-800` | `#40444C` | Headings on light |
| `neutral-900` | `#383A42` | Emphasis |
| `neutral-950` | `#25272C` | Near-black surfaces |
| `white` | `#FFFFFF` | |
| `black` | `#1E1F20` | Text black — **not** `#000000` |

### Semantic

| Token | Hex | Use |
|---|---|---|
| `success` | `#2ECC71` | Success states, confirmations |
| `error` | `#CB1A14` | Destructive actions, error text |
| `error-hover` | `#DD524D` | Destructive hover |
| `error-focus` | `#9E0A05` | Destructive focus |
| `error-tint` | `#FBEAE9` | Outlined destructive hover fill |
| `text-secondary` | `#A8A8A8` | Muted labels |
| `disabled` | `#D0D5DD` | Disabled fills and borders |
| `disabled-subtle` | `#FBFBFB` | Disabled small-button fill |
| `divider` | `#E4E7EC` | Table and list dividers |
| `surface-alt` | `#F7F9FC` | Shadow and blur demo surfaces |
| `grid` | `#F9FAFB` | Grid overlay |
| `input-cursor` | `#4B4EFC` | Text cursor in input fields |

---

## 2. Typography

Two families. Playfair Display carries brand voice; Plus Jakarta Sans carries everything functional.

### Playfair Display — display and headings

| Token | Size | Use |
|---|---|---|
| `display-lg` | 82 px | Landing hero |
| `display-md` | 66 px | Landing sections |
| `display-sm` | 52 px | Large marketing |
| `heading-lg` | 42 px | Screen titles, share cards |
| `heading-md` | 34 px | Section headers |
| `heading-sm` | 26 px | Card titles |
| `title-lg` | 22 px | Prominent list items |
| `title-md` | 16 px | Compact titles |

Weights: Regular, Medium, SemiBold, Bold. The design system page uses SemiBold (600) for headings.

### Plus Jakarta Sans — body and UI

| Token | Size | Line height | Use |
|---|---|---|---|
| `body-lg` | 16 px | 24 px | Primary body |
| `body-md` | 14 px | 20 px | Standard UI, button labels |
| `body-sm` | 12 px | 20 px | Captions, helper text |
| `body-xs` | 8 px | 12 px | Micro labels — use sparingly, it is below comfortable reading size |

Letter spacing 0%, paragraph spacing 0. Weights: Regular (400), Medium (500), SemiBold (600), Bold (700).

**Inter** appears in the design system's own documentation blocks (the "Why?" annotations) but is not a product typeface. Do not ship it.

---

## 3. Spacing

A 4 px base scale. Token numbers are multipliers.

| Token | Value | | Token | Value |
|---|---|---|---|---|
| `space-1` | 4 px | | `space-10` | 40 px |
| `space-2` | 8 px | | `space-12` | 48 px |
| `space-3` | 12 px | | `space-16` | 64 px |
| `space-4` | 16 px | | `space-20` | 80 px |
| `space-5` | 20 px | | `space-24` | 96 px |
| `space-6` | 24 px | | `space-32` | 128 px |
| `space-7` | 28 px | | `space-40` | 160 px |
| `space-8` | 32 px | | `space-48` | 192 px |

---

## 4. Components

Extracted variant matrices. Build these as configurable components; the design uses every combination.

### Buttons

Variants: `primary`, `secondary`, `destructive-solid`, `destructive-outlined`
Sizes: `sm`, `lg`
States: `default`, `hover`, `focused`, `disabled`
Icon styles: `none`, `leading`, `trailing`, `icon-only`

| Variant | Default | Hover | Focused | Disabled |
|---|---|---|---|---|
| Primary | `#0F3D2E` | `#355C4F` | `#0A291F` | `#D0D5DD` (lg) / `#FBFBFB` (sm) |
| Secondary | `#FFFFFF` | `#BCC9C4` | `#BCC9C4` | `#FFFFFF` |
| Destructive solid | `#CB1A14` | `#DD524D` | `#9E0A05` | `#D0D5DD` |
| Destructive outlined | `#FFFFFF` | `#FBEAE9` | `#FBEAE9` | `#FFFFFF` |

Label typography is `body-md` (14 px) at weight 500.

### Chips

Types: `input`, `filter` · States: `default`, `focused`, `disabled` · Icon: on / off
Default fill `#FFFFFF`, focused fill `#BCC9C4`.

Used for occasion selection (Owambe · Date Night · Corporate · Casual · Custom) and vault categories.

### Input fields

States: `default`, `hover`, `active`, `typing`, `filled`, `success`, `error`, `read-only`
Anatomy: label, frame, placeholder or value, optional right add-on, helper text.
Read-only frame fill is `#FBFBFB`; the cursor is `#4B4EFC`.

Helper text switches to `success` or `error` colour with the corresponding state.

### Progress

Three components: `loading` (indeterminate), `progress-bar` (determinate), `progress-circle` (determinate).

The determinate variants are required by the quiz (0 → 90%) and the Building screen — they display real values, not decoration.

### Bottom navigation

Four tabs: Home · Vault · Saved · Profile, with Generate as a centre action.

> **Known drift.** The bottom-nav component (`283:1894`) uses `#613EEA` (purple) and SF Pro Text, which belong to neither the FAUE palette nor its typography. Build it with `primary-500` for the active state and Plus Jakarta Sans, and correct the Figma component.

---

## 5. Flutter mapping

```dart
class FaueColors {
  static const primary50  = Color(0xFFBCC9C4);
  static const primary400 = Color(0xFF355C4F);
  static const primary500 = Color(0xFF0F3D2E);
  static const primary700 = Color(0xFF0A291F);
  static const primaryHover = Color(0xFF145C45);

  static const neutral50  = Color(0xFFF7F8F8);
  static const neutral200 = Color(0xFFD8DBDF);
  static const neutral500 = Color(0xFF6B7280);
  static const neutral950 = Color(0xFF25272C);
  static const black      = Color(0xFF1E1F20);

  static const success  = Color(0xFF2ECC71);
  static const error    = Color(0xFFCB1A14);
  static const disabled = Color(0xFFD0D5DD);
  static const divider  = Color(0xFFE4E7EC);
}

final faueTheme = ThemeData(
  scaffoldBackgroundColor: FaueColors.neutral50,
  colorScheme: const ColorScheme.light(
    primary: FaueColors.primary500,
    error: FaueColors.error,
    surface: Colors.white,
  ),
  textTheme: const TextTheme(
    displayLarge:  TextStyle(fontFamily: 'PlayfairDisplay', fontSize: 42, fontWeight: FontWeight.w600),
    headlineMedium:TextStyle(fontFamily: 'PlayfairDisplay', fontSize: 26, fontWeight: FontWeight.w600),
    bodyLarge:     TextStyle(fontFamily: 'PlusJakartaSans', fontSize: 16, height: 1.5),
    bodyMedium:    TextStyle(fontFamily: 'PlusJakartaSans', fontSize: 14, height: 1.43),
    bodySmall:     TextStyle(fontFamily: 'PlusJakartaSans', fontSize: 12, height: 1.67),
  ),
);

class FaueSpace {
  static const s1 = 4.0;   static const s2 = 8.0;   static const s3 = 12.0;
  static const s4 = 16.0;  static const s5 = 20.0;  static const s6 = 24.0;
  static const s8 = 32.0;  static const s10 = 40.0; static const s12 = 48.0;
}
```

Both families ship as bundled assets. Do not rely on a network font — a first-run user on a slow connection would see a flash of fallback type on the splash screen.

---

## 6. Tailwind mapping

```js
// tailwind.config.js — faue-web and faue-admin
module.exports = {
  theme: {
    extend: {
      colors: {
        primary: {
          50:'#BCC9C4',100:'#A9B9B4',200:'#829A92',300:'#5C7B71',400:'#355C4F',
          500:'#0F3D2E',600:'#0D3327',700:'#0A291F',800:'#082018',900:'#051611',
          hover:'#145C45',
        },
        neutral: {
          50:'#F7F8F8',100:'#EDEEF1',200:'#D8DBDF',300:'#B6BAC3',400:'#8E95A2',
          500:'#6B7280',600:'#5B616E',700:'#4A4E5A',800:'#40444C',900:'#383A42',950:'#25272C',
        },
        success:'#2ECC71',
        error:{ DEFAULT:'#CB1A14', hover:'#DD524D', focus:'#9E0A05', tint:'#FBEAE9' },
        ink:'#1E1F20',
        divider:'#E4E7EC',
      },
      fontFamily: {
        display: ['"Playfair Display"','serif'],
        sans: ['"Plus Jakarta Sans"','system-ui','sans-serif'],
      },
      spacing: {
        1:'4px',2:'8px',3:'12px',4:'16px',5:'20px',6:'24px',7:'28px',8:'32px',
        10:'40px',12:'48px',16:'64px',20:'80px',24:'96px',32:'128px',40:'160px',48:'192px',
      },
    },
  },
};
```

---

## 7. Style DNA card gradients

Server-rendered, but listed here so app previews match. Full context in [`../00-product/style-dna.md`](../00-product/style-dna.md).

| Persona | From | To |
|---|---|---|
| `CM` The Cultural Minimalist | `#0F3D2E` | `#355C4F` |
| `OR` Owambe Royalty | `#0A291F` | `#B5451B` |
| `SL` Soft Luxe | `#BCC9C4` | `#F7F8F8` |
| `SC` Street Alchemist | `#25272C` | `#5C7B71` |
| `CE` Corporate Edge | `#051611` | `#383A42` |
| `NF` Neo-Fusion | `#145C45` | `#829A92` |

`SL` is the only light gradient and needs dark text (`#1E1F20`) to hold WCAG AA. The others take white.

---

## 8. Accessibility

- Body text at 14 px or larger, except `body-xs` which is reserved for non-essential micro-labels.
- Contrast: `primary-500` on white is 11.6:1 — comfortably AA and AAA. `text-secondary` `#A8A8A8` on white is 2.5:1 and **fails AA**; use `neutral-500` `#6B7280` (5.3:1) for any text a user must read, and reserve `#A8A8A8` for decorative labels only.
- Minimum touch target 44×44 pt, which affects `sm` buttons and chips.
- Never signal state by colour alone — pair `success` and `error` with an icon or text.
- Respect the OS text-scale setting; layouts must survive 200% scaling without clipping.

---

## 9. Re-extraction

The tokens above came from the Figma REST API. To refresh after a design change:

```bash
curl -s -H "X-Figma-Token: $FIGMA_TOKEN" \
  "https://api.figma.com/v1/files/KtCAHrBGLQXEdQrPbWJVVS/nodes?ids=70:164,71:427,72:213,81:3317,83:3865,89:4376&depth=8"
```

Frames: Primary `70:164` · Neutral `71:427` · Semantics `72:213` · Spacings `81:3317` · Buttons `83:3865` · Input fields `89:4376`.

If the team publishes Figma styles or variables, switch to `GET /v1/files/{key}/styles` and `/variables`, which are more stable than reading swatch frames.
