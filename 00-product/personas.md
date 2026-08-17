# User Personas

**Stage:** MVP

Who FAUE is for. Distinct from **style personas** (`CM`, `OR`, `SL`, `SC`, `CE`, `NF`), which describe how someone dresses — see [`style-dna.md`](style-dna.md). These describe who they are and why they would open the app.

---

## Primary — Amara, 28, Lagos

**Marketing manager, Victoria Island. Lives in Lekki. Earns ₦450k–700k a month.**

Attends two to four social events a month — weddings, birthdays, church, work functions. Buys fabric four to six times a year, usually Aso-Ebi for a friend's wedding, and spends ₦30,000–80,000 on the complete look each time.

**Her week:** dresses for the office four days, one of them client-facing. Weekends are events. December is relentless.

**What she does today:** saves outfits to a Pinterest board she rarely revisits. Screenshots Instagram looks and forwards them to a WhatsApp group for opinions. Sends her tailor a screenshot of someone else's outfit and hopes. Owns clothes she has worn once.

**What frustrates her:** the gap between the screenshot and the finished garment. She has been disappointed enough times to be cautious, but not enough to stop. She also has a wardrobe full of pieces she cannot see combinations for.

**Why she opens FAUE:** an event is coming and she has fabric with no plan. Or it is Tuesday and she is bored of her own rotation.

**What makes her return:** a look she actually wore that got a compliment. Nothing else compounds like that.

**What makes her leave:** generic suggestions that could have come from any Western app. A recommendation that ignores her fabric's motif scale. Anything that makes her feel judged about her body.

---

## Secondary — Tunde, 32, Abuja

**Consultant. Earns ₦600k–1m a month. Dresses well and does not want to think about it.**

Wears Senator or a suit most days, full native for weekends and family events. Owns good pieces and repeats them confidently. Buys less often but spends more.

**What he does today:** has a tailor he trusts and a rotation that works. Occasionally wants something new and does not know where to start. Does not browse fashion content.

**Why he opens FAUE:** a specific occasion with an unfamiliar dress code, or fabric he was gifted and has no plan for.

**What makes him return:** speed. If it answers in under a minute, he will use it again. If it asks him to browse, he will not.

**What makes him leave:** anything that feels like a social app. Feeds, likes, discovery for its own sake.

**Design implication:** Tunde is why the agent's on-open suggestion and occasion shortcuts exist. He wants an answer, not a session.

---

## Tertiary — Chidinma, 23, Ibadan

**Final-year student, FUNAAB. Budget ₦5k–20k per item. Style-forward, cash-limited.**

Thrifts, remixes, borrows. Owns fewer pieces and gets more out of each. Highly active on Instagram and X, and shares constantly.

**Why she opens FAUE:** to get more from what she already owns, and because the DNA card is worth posting.

**What makes her return:** the vault genuinely showing her combinations she had not seen.

**What makes her leave:** recommendations she cannot afford. Nothing kills trust faster than being shown a ₦120,000 dress when everything she owns cost less than that.

**Design implication:** Chidinma is why the MVP works from the user's own wardrobe rather than a catalogue, and why budget must constrain recommendations the moment a catalogue exists.

---

## Recipient today, primary user later — the tailor

**Baba Segun, 45, Ojota. Twenty years' experience. WhatsApp only.**

### At MVP — a recipient, not a user

He receives what FAUE's tailor share produces. He does not have the app and will not install one.

**What he needs:** a clear fabric photograph, a clear style reference, and measurements or notes, in one image he can look at while cutting.

**What he currently gets:** a blurry screenshot of a celebrity, with "I want something like this."

**Design implication:** the tailor share image is a product surface with a real user, and it must be legible on a cracked phone screen in poor light. It is image-first for exactly this reason — he may never tap a link.

### At Y2 — a primary user

FAUE is already in his WhatsApp. The distance from passive recipient to retained user is short, and the wedge is specific: **his measurements live in a paper notebook** that gets lost, and clients get re-measured inconsistently. Nothing else in his working life solves that.

His constraints shape the product entirely: a low-end Android, metered data, WhatsApp as the primary computing surface, often limited written English. WhatsApp bot before app, offline-first genuinely, voice input for measurements, Yoruba and Hausa and Pidgin.

Full analysis in [`professional-strategy.md`](professional-strategy.md).

---

## Future primary — the stylist

**Folake, 31, Lekki. Freelance stylist. Eight to fifteen active clients.**

Manages her clients' wardrobes with no system — photos scattered across her camera roll, lookbooks built in slide decks, borrowed samples tracked in a notes app, approvals chased over WhatsApp, invoices written by hand.

**Why she would use FAUE:** the reconciliation engine — aspiration versus body versus budget — is a formalisation of what she does manually for every client. The consumer product is structurally an automated junior stylist, and selling that as leverage rather than replacement is the entire pitch.

**What would hold her:** her clients' wardrobes and her lookbook history. Neither moves to a competitor.

**What would lose her instantly:** any framing that implies she is unnecessary. Augment, never replace.

**Stage:** `Y2`, after tailors. Fewer of them, higher willingness to pay, more digitally comfortable.

---

## Anti-personas

Explicitly not the target **for the consumer product**. Building the consumer app for them would pull it away from the people it is for.

| Not for (consumer app) | Why |
|---|---|
| Fast-fashion bargain hunters | Optimising for price over styling is a different product |
| Non-African markets at launch | The cultural depth that is the moat becomes overhead |
| Users wanting a social network | FAUE ends the search rather than extending it |
| Under-16s | Age-gated; the data model and consent framework assume adults |

### A correction worth recording

Earlier versions of this document listed **fashion professionals — stylists, buyers, editors** as an anti-persona, on the reasoning that they have tools and taste and would find FAUE simplistic.

That reasoning still holds for the **consumer app**, and it is why the MVP does not court them. It does not hold for **FAUE the platform**, whose direction is fashion technology used in shows, in pop-up collaborations, and daily by the people who make clothes happen.

The resolution is not to make the consumer app serve professionals. It is a distinct professional surface on the same data spine — which is why [ADR 0021](../80-adr/0021-workspace-tenancy-model.md) makes the schema workspace-capable now while the product deliberately stays single-tenant.

Buyers and editors remain out of scope with no current plan.

---

## What they share

Every **consumer** persona above:

- **Owns clothes they do not fully use.** The vault has value from the first session.
- **Has been disappointed by a tailor.** The fabric flow addresses a remembered, specific pain.
- **Uses WhatsApp for everything.** Sharing must work there before anywhere else.
- **Is on metered mobile data.** Image weight is a cost, not a detail.
- **Dresses for occasions that have names and rules.** Owambe, corporate, church, casual — a Western app's "smart casual" does not map.

These commonalities are why the MVP looks as it does. If a proposed feature does not serve at least two of them, it is probably serving an imagined user instead.
