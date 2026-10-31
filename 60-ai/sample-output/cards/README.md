# Sample share cards

Drawn by `generate_cards.py` with `app/modules/cards/looks.py` from the gateway. The garments and fabric are made-up shapes, not photographs: real cards use the person's own vault photos (already through the privacy pipeline).

| File | What it shows |
|---|---|
| `look-card-owambe-4x5.jpg` | Feed post / WhatsApp chat |
| `look-card-owambe-9x16.jpg` | Stories / WhatsApp status |
| `look-card-owambe-1x1.jpg` | Square post |
| `look-card-owambe-og.jpg` | Link preview (X, Facebook, iMessage) |
| `look-card-office-4x5.jpg` | Top, bottoms and shoes layout |
| `look-card-no-photo-4x5.jpg` | A piece whose photo cannot be read |
| `tailor-card.jpg` | What a tailor receives |

The reasons are real output of the ASE engine for this wardrobe: the static explanation a look carries when the model plane is off. When a live model is available, the `narrate` phase writes each reason from the event, weather, taste, pieces and colour story, and keeps it only if it passes the grounding check.

Where nothing is owned (an empty-vault look, or a style made from a cloth) the card shows one generated picture in place of the tiles, and the tailor card adds an illustration labelled as one. Those need a live image model, so no sample is shown here.
