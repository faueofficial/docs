# Solo Grants application: Faue

Form: https://airtable.com/appHaOk5VRk50CpcF/pag93ybs2R8OfxZXD/form
Program: https://sologrants.com/ (check range $100 to $1,000, 1,000-word limit on the written application)

Draft for manual filing. Items in [brackets] are placeholders to fill or verify before pasting.

---

## One-liner for the project

You bought the fabric, now what? Faue shows you what to sew with it, then briefs your tailor for you.

## How much money are you requesting?

$1,000

## Budget breakdown

I am requesting $1,000 to cover the two months before Faue's closed beta, ahead of a public launch in January or February 2027. About a quarter of it, $250, goes to AI credits. Faue calls language, vision and embedding models for outfit matching and "Style My Fabric", and generates style images. My cost model puts model spend at roughly $20 to $40 a month and image generation at $20 to $60 a month. This covers production use, a capped staging budget so model bugs surface before users see them, and the evaluation runs that gate every AI release.

Another $150 pays for two months of hosting: Railway services, Postgres with point-in-time recovery, Redis, object storage, a CDN and transactional email.

$100 goes to style validation. A working tailor or stylist will review the library of 30 native styles and help label the evaluation sets. If "Style My Fabric" gives poor advice for Aso-Oke or Adire, the product fails, so this is where I most want expert eyes.

$250 goes to brand and marketing: a proper logo and Style DNA card templates, because the shareable card is the main growth loop, plus paying small fashion creators to seed it and a small waitlist ad budget.

$130 covers launch essentials: a domain, business email, and Apple ($99) and Google Play ($25) developer fees.

The last $120 is a buffer for model costs, which spike whenever a prompt change resets the cache.

## Share what you're working on

Deciding what to wear in Nigeria is rarely a shortage of inspiration. The hard part is knowing what will actually work. For bespoke clothing the gap is bigger. Someone buys Ankara, lace or Aso-Oke, saves a dozen reference photos, and still doesn't know what to make. The answer ends up as a pile of screenshots sent to a tailor on WhatsApp.

Faue runs one loop. A six-question Style DNA quiz builds a shareable style profile. From there people add what they own, upload fabric, and ask for a look based on the occasion, their mood, the weather and their wardrobe. Faue explains why the combination works for that person. They can save it, share it, or send the chosen style to their tailor as a WhatsApp-ready image.

The feature I care about most is "Style My Fabric". Upload a photo of your Aso-Oke or Ankara and get a useful answer, not a list of generic ideas: which silhouette suits it, which details to avoid, which accessories make sense, and exactly what to tell the person sewing it. I'm starting with Nigerian professionals aged 22 to 35, who typically spend ₦30,000 to ₦80,000 on a full look for each event. Faue is pre-revenue and has no paying users yet.

I'm building Faue alone. The platform is a set of services I designed and built myself: an API gateway, an AI engine that routes calls across model providers with cost caps, a Postgres and pgvector data layer, passwordless and OIDC sign-in, an admin console with MFA, and PII-safe image storage. The gateway alone passes over 900 automated tests, and the system is deployed on Railway. The Style DNA quiz, the waitlist and the shareable cards are built. What remains is what this grant would fund: AI quality and evaluation, content curation and the launch.

I'm the founding engineer at Intellign.ai, where I build the machine learning and optimization layer, keep everything working as it should, and work directly with customers to bring partners on board. At Obscura I was the backend engineer leading the team that built a copy-trading system across several DEXs and CEXs, plus Solana and Base. Outside work I build full products alone. Tawn is a local-first memory layer that gives AI agents like Claude Code and Cursor one shared, user-owned memory, backed by 241 backend tests. Nottra is a Telegram decision-support tool for forex traders, built around discipline rather than prediction: demo accounts only, nothing trades without approval, and I record test results honestly even where they show no edge.

The next problem is not technical. I need to prove that Faue's styling decisions are actually good. The money lets me run a closed beta over the next two months with real users, a curated catalog of 500+ items, and a fixed evaluation set, so that when I change a model or a prompt I can tell whether the product improved. Then I launch in January or February 2027. The aim is to find out whether Faue is useful, not to make it look finished.

## Current financial situation

**1. My situation, the challenges, and how the grant helps**

I'm employed, and I'm grateful for that, but my salary is not enough to fund Faue the way it needs to be funded. Right now I put a fraction of it into the AI compute I need to test the product. That works for experiments. It does not work for a closed beta, where the cost grows with every look a real person generates. The part I can't plan for is model spend, which jumps whenever I change a prompt.

The grant pays for the beta and lets me learn from real users instead of guessing.

**2. My personal and family situation**

I won't be getting financial support from my family for this. Faue is funded from my own pocket, from the same salary that covers my living costs, so every naira that goes into compute is a naira I have to find elsewhere. I'm building it alone, with no outside backing yet.

**3. If I don't get the grant**

I'm employed, not studying, so this comes down to my own income. Faue will keep moving with or without this grant. Without it I will build slowly with the hours and money I can spare, and I will probably have to ask people I know to invest. That adds months to a first test, and I want to see this tested by real people instead of left on my laptop.

---

## Check before filing

- "Nine services" was dropped from the text; the gateway test count (over 900) comes from the last full run of `api-gateway`. Confirm the other services exist if you want to claim them.
- "AI engine that routes calls across model providers" and the closed-beta items are as in the earlier draft; the looks and fabric flows are not wired in the gateway code yet, so keep the wording as "what remains is what this grant would fund".
- Waitlist and shareable cards are built but not deployed yet. Say "built", not "live", until they are.
- The financial section answers the form's three questions. Question 2 says there is no family support and that Faue is funded from your own salary; add dependents or household details only if there are any. Question 3 is for students or people living at home; it is labelled as not applicable and answers the alternative-funding part anyway.
- Word count: the written sections together should stay under the program's 1,000-word limit. Check after any edits.
- Form fields not drafted here: name, contact, city and country, link, "building solo?" (yes).
- Faue is pre-revenue, which fits this program. Projects already commercialising are directed to the sibling Solo Founders Program.
