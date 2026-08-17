# Deep Links and Sharing

**Stage:** MVP

Sharing is FAUE's growth loop, and a share that opens a broken page breaks it. Every shareable object has a public web page that works without the app installed.

---

## 1. URL scheme

Canonical domain: `https://faueofficial.com`. Everything routes through HTTPS links — no custom `faue://` scheme, which cannot be shared into WhatsApp usefully and shows a scary dialog when the app is absent.

| URL | Opens in app | Web fallback |
|---|---|---|
| `https://faueofficial.com/auth/verify?t=…` | `/auth/verify` | Sign-in confirmation page |
| `https://faueofficial.com/dna/{share_id}` | `/quiz/result` (own) or a viewer | Public Style DNA card page |
| `https://faueofficial.com/look/{share_id}` | `/looks/{id}` | Public look page |
| `https://faueofficial.com/style/{style_id}` | `/styles/{id}` | Public style page |
| `https://faueofficial.com/invite/{code}` | onboarding with attribution | Landing page |
| `https://faueofficial.com/n/{notification_id}` | target of the notification | Landing page |

Share ids are **not** internal object ids. They are separate, unguessable, and revocable, so unsharing actually works and nobody can enumerate looks by incrementing a number.

---

## 2. Universal Links (iOS)

`faue-web` serves, at `https://faueofficial.com/.well-known/apple-app-site-association`, with `Content-Type: application/json` and **no** `.json` extension:

```json
{
  "applinks": {
    "details": [{
      "appIDs": ["TEAMID.com.faueofficial.app"],
      "components": [
        { "/": "/auth/verify", "?": { "t": "?*" } },
        { "/": "/dna/*" },
        { "/": "/look/*" },
        { "/": "/style/*" },
        { "/": "/invite/*" },
        { "/": "/n/*" }
      ]
    }]
  }
}
```

The app declares `applinks:faueofficial.com` in its Associated Domains entitlement.

Gotchas that cost a day each if unknown: the file must be served over HTTPS with no redirect; iOS caches it aggressively, so changes need an app reinstall to test reliably; and a Universal Link tapped from within Safari on the same domain will not open the app — test from Messages or Notes instead.

---

## 3. App Links (Android)

`https://faueofficial.com/.well-known/assetlinks.json`:

```json
[{
  "relation": ["delegate_permission/common.handle_all_urls"],
  "target": {
    "namespace": "android_app",
    "package_name": "com.faueofficial.app",
    "sha256_cert_fingerprints": ["<release signing cert SHA-256>"]
  }
}]
```

Include the fingerprints for **both** the upload key and the Play App Signing key, or links will work in internal testing and silently fail in production — a classic and confusing failure.

Manifest:

```xml
<intent-filter android:autoVerify="true">
  <action android:name="android.intent.action.VIEW" />
  <category android:name="android.intent.category.DEFAULT" />
  <category android:name="android.intent.category.BROWSABLE" />
  <data android:scheme="https" android:host="faueofficial.com" />
</intent-filter>
```

---

## 4. Behaviour when the app is not installed

The web page must stand on its own, not act as a redirect gate. Specifically:

- **DNA share page** shows the actual card, the persona name and description, and a "Discover yours" call to action. Someone who received it should be able to enjoy it without installing anything — that is what makes them install it.
- **Look share page** shows the look image, its title, and the item list.
- **Magic-link verify page** completes the sign-in with an explicit button and then offers store links.

Never gate content behind an install prompt. A shared card that says "open the app to see this" is a share that converts nobody and irritates the recipient.

### Open Graph

Every public page carries OG and Twitter card tags, since these links are pasted into WhatsApp and Instagram where the preview *is* the experience:

```html
<meta property="og:title"       content="Seagatoo's Style DNA — The Cultural Minimalist" />
<meta property="og:description" content="Discover your FAUE Style DNA." />
<meta property="og:image"       content="https://cdn.faueofficial.com/cards/{share_id}/square.png" />
<meta property="og:url"         content="https://faueofficial.com/dna/{share_id}" />
<meta name="twitter:card"       content="summary_large_image" />
```

WhatsApp caches previews aggressively and prefers images under 300 KB. Serve a compressed preview variant rather than the full-resolution card.

---

## 5. Deferred deep linking

A user taps a shared look, does not have the app, installs it, and opens it. The link's destination should survive that.

`M1-2`, because it needs either a third-party service or fingerprint matching, and neither is worth the launch effort. Until then, a fresh install lands on normal onboarding.

What ships at MVP: `/invite/{code}` sets an attribution cookie on the web page, and if the user later signs up in the same browser session, the source is recorded. Imperfect, but free.

---

## 6. Sharing from the app

Use the native share sheet with **both** an image and a URL — recipients on WhatsApp see the image inline, and the link gives them somewhere to go.

```dart
await Share.shareXFiles(
  [XFile(cardImagePath)],
  text: 'My FAUE Style DNA — The Cultural Minimalist\nhttps://faueofficial.com/dna/$shareId',
);
```

Endpoints returning share material:

| Object | Endpoint | Returns |
|---|---|---|
| Style DNA card | `GET /quiz/card` | `square_url`, `stories_url` |
| Look | `POST /looks/{id}/share` | `image_url`, `share_url` |
| Tailor share | `POST /fabric/{asset_id}/tailor-share` | `image_url` |

The tailor share is deliberately image-first — it goes to a tailor on WhatsApp who needs to *see* the fabric and the style, and may never open a link at all.

---

## 7. Notification routing

Every notification carries a `deeplink`. Tapping routes directly to the destination, never to a generic home screen — landing on the dashboard after tapping "Your Crimson Elegance look is ready" is a small failure that costs a session.

| Notification | Destination |
|---|---|
| Look ready | `/look/{id}` |
| DNA card ready | `/quiz/result` |
| Pinterest import finished | `/profile/accounts` |
| Daily suggestion | `/home` |
| Generic | `/notifications` |

---

## 8. Testing

- Tap a link from WhatsApp, Messages, Instagram DM, and Gmail — behaviour differs across all four.
- Test with the app installed, not installed, and installed but signed out.
- Verify OG previews with the WhatsApp and Twitter card validators before launch.
- Confirm both Android signing fingerprints are present by testing a Play-signed build, not just a local one.
- Confirm the magic-link page does not sign in on load — open it with `curl` and check that no session is created.
