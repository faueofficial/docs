# look_rank

How close the order ASE serves is to the order a stylist would put the same candidates in.

| File | What it is |
|---|---|
| `cases.jsonl` | 14 regression anchors: a rule or a preference the top look must respect (a disliked colour loses, wool in 36 °C is out). Always run |
| `rankings.jsonl` | Graded candidate sets. Each row is a wardrobe, an occasion and 4 to 12 candidate looks graded 0 to 3 |
| `baseline.json` | What the engine scored on each `draft_rules` row when the seed was made |

## Grades

3 I would put them in this · 2 good · 1 acceptable, not what I would choose · 0 wrong for the occasion or the person.

## Sources

- `stylist`: graded by a person. **These are the gate**: each row passes at nDCG@10 of 0.85 or more, and once there are 30 the mean must hold too. Until then the report says "collecting".
- `draft_rules`: graded by the written rubric in `ase/eval/rubric.py`, which reads only what a person can see in a look and never calls ASE's scorer. It is **not taste**. These rows only guard against regression: each passes while it stays within 0.05 of its baseline.

## Collecting stylist grades

```bash
cd ase
../.venv/bin/python eval/label_looks.py export --out label_session.html      # send this one file to the stylist
../.venv/bin/python eval/label_looks.py import grades-<name>.json            # what they send back
```

The page is self-contained: it opens in a browser, needs no account or network, and sends nothing. It shows each wardrobe and ASE's best candidates plus a few it ranks low, so a look the stylist would love but ASE buries still gets graded. Import checks every grade is 0 to 3 and every graded look is one the engine builds today.

## Metrics

nDCG@10, precision@5 (grade 2 or more in the top five) and pairwise accuracy (of two looks graded differently, how often ASE puts the better one first), over the graded candidates only. Run `../.venv/bin/python ase/eval/runner.py look_rank`.

## What the seed already found

A scorer that compared the *average* formality of the pieces to the occasion let one casual shoe be averaged away by a dressy outfit (church: nDCG 0.58). It now holds each piece to the occasion and counts the weakest at 40%, which brought church to 0.97. The casual-day cases still disagree with the rubric (the engine ranks office wear first on a casual day); that is a judgement for a stylist, which is what the labelling page is for.
