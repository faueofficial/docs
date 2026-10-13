# FAUE email templates

Thirteen emails, one layout. Open `index.html` to browse them; each has a `.html`
(what is sent), a `.txt` (the plain-text part) and phone and desktop screenshots in
`previews/`.

Rebuild:

```
cd api-gateway && PYTHONPATH=. python scripts/render_email_previews.py
cd ../landing && CHROME=$(command -v google-chrome) node ../docs/brand/email/source/screenshot.mjs
cd ../docs/brand/email/source && python3 build_banners.py     # banners and fonts
```

Layout rules (tested in `api-gateway/tests/unit/test_email_layout.py`): phone first,
a 2:1 banner with the headline set in Instrument Serif, body in Plus Jakarta Sans
with Helvetica and Georgia fallbacks, full-width buttons on a phone, and an
Unsubscribe link only on mail the person can opt out of.

## What triggers each email

| Template | Sent when | Where in the code | Unsubscribe link |
|---|---|---|---|
| `waitlist_joined` | Someone joins the waitlist; and, for anyone who never got it, on every worker pass after a deploy | `app/api/v1/early_access.py` (instant), `app/workers/pending_deliveries.py` (sweep, no age limit) | yes |
| `waitlist_invite` | An admin sets a member to `invited` (`PATCH /admin/v1/waitlist/{id}`), once | `app/api/admin/waitlist.py` → `WaitlistNotifier.send_invite` | yes |
| `waitlist_removed` | An admin deletes a member (`DELETE /admin/v1/waitlist/{id}`) | `app/api/admin/waitlist.py` → `WaitlistNotifier.send_removed` | no |
| `staff_message` | An admin writes to one member | `POST /admin/v1/waitlist/{id}/message` | no |
| `contact_received` | Someone uses the contact form (to the team) | `app/events/handlers/contact.py` | no |
| `contact_reply` | An admin replies to a contact message | `POST /admin/v1/contact/messages/{id}/reply` | no |
| `magic_link` | Someone asks to sign in | `app/modules/identity` | no |
| `admin_invite` | An admin is invited | `app/modules/admin/invite.py` | no |
| `welcome_new` | An account signs in for the first time (verified address) | `app/modules/identity/service.py` `_sign_in` | no |
| `dna_card_ready` | A signed-in user finishes the quiz (with their card) | `quiz.completed` → `QuizCompletedNotifier` | no |
| `look_ready` | **Not triggered yet**: looks are not built | event `look.completed` is bound to a no-op | no |
| `welcome_back` | **Not triggered yet**: needs a lapsed-user campaign job | none | yes |
| `detty_december` | **Not triggered yet**: needs a seasonal campaign job | none | yes |

The unsubscribe link is `https://faueofficial.com/unsubscribe#t=<signed token>`;
the page confirms, then posts to `POST /v1/unsubscribe/{token}`. The same token is
in the `List-Unsubscribe` header so a mail client's own button works.
