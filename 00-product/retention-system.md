# Retention System

**Stage:** MVP

Retention is a system, not a notification schedule. The notifications are the least important part of it — they are what you reach for when the product itself has not given someone a reason to return.

---

## 1. The habit loop

```
TRIGGER      an event is coming · the weather changed · a daily suggestion
     ↓
ACTION       open, generate, browse the vault, log a wear
     ↓
REWARD       an outfit worth wearing — and worth a compliment
     ↓
INVESTMENT   vault grows · wear log deepens · boards sync · preferences sharpen
     ↓
             the next suggestion is better  →  back to TRIGGER
```

The investment step is what makes this compound rather than repeat. Every session leaves FAUE knowing more about the user, which makes the next session better — and that accumulated knowledge is the thing they cannot get anywhere else.

**The strongest reward is external.** Someone complimenting an outfit FAUE suggested is worth more than any in-app delight. The product's job is to increase how often that happens.

---

## 2. Compounding value

| Session | What FAUE knows | Quality |
|---|---|---|
| 1 | Quiz answers | Generic within their persona |
| 3 | + 10 vault items | Uses clothes they own |
| 10 | + Pinterest boards, some wears | Matches taste and reality |
| 30 | + 20 wears, feedback, seasonality | Knows what they actually reach for |

A user at session 30 cannot switch to a competitor without losing all of that. That is the moat — not features, which are copyable, but accumulated personal data that took months to build.

**Design consequence:** anything that increases what FAUE knows per session is a retention feature, even when it does not look like one. Adding a vault item, logging a wear, and giving feedback are all retention work.

---

## 3. Lifecycle

Scheduled by the `lifecycle` worker. All require `marketing_comms` except where noted.

| Day | Trigger | Message | Purpose |
|---|---|---|---|
| D0 | Quiz completed | DNA card ready *(essential)* | Deliver the shareable artefact |
| D1 | No look generated | "Your first look is waiting" | Get them to the core action |
| D1 | Look generated, none saved | "Anything you'd wear?" | Get to first save |
| D3 | Active | "New looks for your DNA" | Second session |
| D5 | Vault under 5 items | "Add three pieces, get better looks" | Deepen investment |
| D7 | No fabric upload | "Bought fabric lately?" | Introduce the differentiator |
| D10 | Pinterest not connected | "Import what you already love" | Deepen personalisation |
| D14 | Active | Wear-streak or "worn 5 looks" | Reinforce the habit |
| D21 | Inactive 7 days | "Your vault is waiting" | Early win-back |
| D30 | Active | DNA retake now available | Refresh, re-engage |
| D45 | Inactive 21 days | "What changed?" — genuine question | Late win-back and feedback |
| D60 | Inactive | Final message, then stop | Respect the silence |

**Stop after D60.** Someone who has not returned in two months is not going to be persuaded by a seventh message, and continuing costs goodwill that a future relaunch would need.

---

## 4. Cultural and seasonal triggers

Nigeria-specific and the highest-value triggers FAUE has, because they align with when people are actually thinking about clothes.

| Trigger | Window | Message |
|---|---|---|
| **Detty December** | Dec 1 – Jan 5 | Event-density peak; the single biggest styling period of the year |
| Wedding season | Nov – Jan, Apr – Jun | "Aso-ebi fabric? Let's plan the style" |
| Harmattan onset | Dec – Feb | Dust and dry air change what fabric is bearable |
| Rainy season | Apr – Oct | Fabric and footwear practicality |
| Ramadan and Eid | Varies | Modest styling, celebration looks |
| Christmas and Easter | Dec, Mar/Apr | Church and family occasions |
| Month-end | Monthly | Payday; higher purchase and planning intent |
| New Year | January | Style reset; DNA retake |

A generic styling app cannot do this. Knowing that harmattan makes heavy lace unbearable and that Detty December compresses six events into three weeks is exactly the cultural specificity that makes FAUE worth returning to.

---

## 5. Event-driven triggers

Immediate, tied to what the user just did. These outperform scheduled messages because they arrive when attention is already there.

| Event | Message | Consent |
|---|---|---|
| `look.completed` | "Your look is ready" | `essential` |
| `media.card.ready` | "Your Style DNA card is ready to share" | `essential` |
| `integration.synced` | "We found N styles you'll love" | `essential` |
| `agent.suggestion.ready` | Daily fit | `agent_proactive` |
| Friend used your shared link | "Someone tried FAUE from your card" | `marketing_comms` |
| Saved-item price drop (`M1-2`) | Price alert | `marketing_comms` |

---

## 6. Frequency discipline

| Rule | Value |
|---|---|
| Maximum per day | 1 (excluding job-completion messages the user triggered) |
| Maximum per week | 4 |
| Quiet hours | 21:00 – 07:00 WAT, absolute |
| Backoff | After 3 consecutive ignores, pause 7 days |
| Hard stop | After 6 unopened messages, marketing stops entirely |

The backoff rule matters more than it appears. **Opt-out is nearly irreversible**, so backing off is always cheaper than pushing through. An app that keeps talking to someone who has stopped listening gets muted permanently, and a muted app has no retention channel left at all.

---

## 7. In-product retention

The parts that work without sending anything, which is where the real leverage is.

| Mechanism | Effect |
|---|---|
| **Agent suggestion on open** | Every session starts with an answer, not an empty state |
| **Neglected-item surfacing** | "You haven't worn this in a month" — the clearest value proof |
| **Saved looks** | A reason to come back that requires no prompting |
| **DNA card sharing** | Acquisition and re-engagement in one artefact |
| **Wear logging** | Small commitment that improves everything downstream |
| **Vault growth** | Each item makes every future generation better |
| **Occasion shortcuts** | Owambe, Date Night, Corporate, Casual on the dashboard — one tap to value |

**The neglected-item mechanic is the strongest one available.** "You already own this and it works" is more surprising, more useful, and cheaper than any recommendation to buy something — and it is only possible because FAUE knows the wardrobe.

---

## 8. Measurement

| Metric | Target |
|---|---|
| D1 retention | 25% |
| D7 retention | 30% |
| **D14 unprompted** | **20%** — the launch criterion |
| D30 retention | 15% |
| WAU/MAU | 0.30 |
| Sessions per week, active users | 2.5 |
| Wear-log rate | 15% of saved looks |
| Notification opt-out | **≤ 5% monthly — guardrail** |
| Resurrection rate | 5% monthly |

"Unprompted" excludes sessions opened within an hour of a notification. A return you paid for with a push is not the same signal as one you earned, and conflating them hides whether the product is actually working.

**Opt-out rate is a guardrail on every retention experiment.** A campaign that lifts D7 while raising opt-outs has borrowed retention against a channel it cannot repay.

---

## 9. What is deliberately not done

| Not doing | Why |
|---|---|
| Streaks with loss framing | Manufactured anxiety; FAUE is not a language app |
| Daily login rewards | Rewards showing up rather than getting value |
| Social comparison | "Your friends styled 5 looks this week" is pressure, not help |
| Infinite feed | FAUE ends the search rather than extending it |
| Notification-driven growth | Borrowed retention that comes due as opt-outs |
| Dark-pattern unsubscribe | Illegal, and it destroys trust permanently |

The principle: retention should come from the product being useful, and the honest test is whether a metric would still move if every notification were switched off.

---

## 10. Experiment sequence

Ordered by expected effect, highest first:

1. **Agent suggestion quality** — accept rate is the leading indicator for everything else.
2. **Onboarding to first look** — the biggest funnel drop is between quiz and first generation.
3. **Wear-log prompting** — unlocks compounding personalisation; currently has no screen at all.
4. **Vault growth nudges** — more items means better looks means more returns.
5. **DNA card share rate** — acquisition and re-engagement together.
6. **Notification timing and copy** — real, but the smallest lever of the six.

Notification tuning is last deliberately. It is the most tempting thing to optimise and the least durable.
