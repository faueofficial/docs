# ASE output check

Input vault:

- `v-agbada` navy agbada (native, navy)
- `v-kaftan` cream kaftan (native, cream)
- `v-sokoto` cream sokoto (bottoms, cream)
- `v-fila` navy fila (accessories, navy)
- `v-white` white shirt (tops, white)
- `v-blk` black trousers (bottoms, black)
- `v-loaf` brown loafers (shoes, brown)
- `v-sand` gold sandals (shoes, gold)

## corporate - full vault -> done, mode `wardrobe`

**Look 1** - template `native_set`, confidence 0.944, render `composite`
- native: cream kaftan (native)
- shoes: gold sandals (shoes)
- why: The kaftan and the sandals are a classic pairing. The formality suits corporate. It is built around your cream, with the other colours kept calm beside it.

**Look 2** - template `two_piece`, confidence 0.407, render `composite`
- top: white shirt (tops)
- bottom: black trousers (bottoms)
- shoes: brown loafers (shoes)
- why: The shirt and the trousers are a classic pairing. The formality suits corporate. It is built around your white, with the other colours kept calm beside it.

**Look 3** - template `native_set`, confidence 1.0, render `composite`
- native: cream kaftan (native)
- shoes: brown loafers (shoes)
- accessory: navy fila (accessories)
- why: The formality suits corporate. It is built around your cream, with the other colours kept calm beside it. Chosen with today's 29 degrees in mind.

## corporate - empty vault -> done, mode `archetype`

**Look 1** (archetype card, no vault items): `{"id": "a9729668-a791-4104-b358-d065bac3f94a", "job_id": "8b5eea3a-e5a6-4088-bd6a-d6c9ddcd73e0", "parent": null, "mode": "archetype", "pack_hash": "9b11e1344187e3435e1f", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`

## owambe - full vault -> done, mode `wardrobe`

**Look 1** - template `native_set`, confidence 0.306, render `composite`
- native: cream kaftan (native)
- shoes: gold sandals (shoes)
- why: The kaftan and the sandals are a classic pairing. The formality suits owambe. It is built around your cream, with the other colours kept calm beside it.

**Look 2** - template `two_piece`, confidence 0.139, render `composite`
- top: white shirt (tops)
- bottom: black trousers (bottoms)
- shoes: brown loafers (shoes)
- why: The shirt and the trousers are a classic pairing. The formality suits owambe. It is built around your white, with the other colours kept calm beside it.

**Look 3** - template `native_set`, confidence 0.639, render `composite`
- native: navy agbada (native)
- shoes: gold sandals (shoes)
- why: The agbada and the sandals are a classic pairing. The formality suits owambe. It is built around your navy, with the other colours kept calm beside it.

## owambe - empty vault -> done, mode `archetype`

**Look 1** (archetype card, no vault items): `{"id": "7b4f1a2d-a9e9-484e-842d-77604dc00ffe", "job_id": "d5aecc92-af6a-4afc-84b7-dcf49a9e65ec", "parent": null, "mode": "archetype", "pack_hash": "30bc33ee0b00fc608f6c", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`

## wedding - full vault -> done, mode `wardrobe`

**Look 1** - template `native_set`, confidence 0.306, render `composite`
- native: cream kaftan (native)
- shoes: gold sandals (shoes)
- why: The kaftan and the sandals are a classic pairing. The formality suits wedding. It is built around your cream, with the other colours kept calm beside it.

**Look 2** - template `two_piece`, confidence 0.139, render `composite`
- top: white shirt (tops)
- bottom: black trousers (bottoms)
- shoes: brown loafers (shoes)
- why: The shirt and the trousers are a classic pairing. The formality suits wedding. It is built around your white, with the other colours kept calm beside it.

**Look 3** - template `native_set`, confidence 0.639, render `composite`
- native: navy agbada (native)
- shoes: gold sandals (shoes)
- why: The agbada and the sandals are a classic pairing. The formality suits wedding. It is built around your navy, with the other colours kept calm beside it.

## wedding - empty vault -> done, mode `archetype`

**Look 1** (archetype card, no vault items): `{"id": "edff4449-64ac-4d58-b857-4ef437e0a21c", "job_id": "2feaf7db-6735-4a80-ae99-59e6bddb1821", "parent": null, "mode": "archetype", "pack_hash": "a69fed1fc11fde442813", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`

**Look 2** (archetype card, no vault items): `{"id": "14bf38e4-2835-4236-97c7-80143dfdf917", "job_id": "2feaf7db-6735-4a80-ae99-59e6bddb1821", "parent": null, "mode": "archetype", "pack_hash": "a69fed1fc11fde442813", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`

## casual - full vault -> done, mode `wardrobe`

**Look 1** - template `two_piece`, confidence 0.407, render `composite`
- top: white shirt (tops)
- bottom: black trousers (bottoms)
- shoes: gold sandals (shoes)
- why: The shirt and the trousers are a classic pairing. The formality suits casual. It is built around your white, with the other colours kept calm beside it.

**Look 2** - template `two_piece`, confidence 0.0, render `composite`
- top: white shirt (tops)
- bottom: cream sokoto (bottoms)
- shoes: brown loafers (shoes)
- why: The formality suits casual. It is built around your white, with the other colours kept calm beside it. Chosen with today's 29 degrees in mind.

**Look 3** - template `two_piece`, confidence 0.05, render `composite`
- top: white shirt (tops)
- bottom: cream sokoto (bottoms)
- shoes: gold sandals (shoes)
- accessory: navy fila (accessories)
- why: The formality suits casual. It is built around your white, with the other colours kept calm beside it. Chosen with today's 29 degrees in mind.

## casual - empty vault -> done, mode `archetype`

**Look 1** (archetype card, no vault items): `{"id": "018a4614-4dc7-4aba-9322-e502424463e7", "job_id": "e226cb74-4491-4427-9f8a-024b9c8d8836", "parent": null, "mode": "archetype", "pack_hash": "028fbecb8124553a60d2", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`

**Look 2** (archetype card, no vault items): `{"id": "d409a200-3dcd-4ad7-8b27-35d6769f234e", "job_id": "e226cb74-4491-4427-9f8a-024b9c8d8836", "parent": null, "mode": "archetype", "pack_hash": "028fbecb8124553a60d2", "skill_version": "2ce0d2681834da60", "item_ids": [], "slot_map": {}, "template": "archetype", "confidence": 0.0, "archetype": {"n`
