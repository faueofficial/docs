# Regenerates this folder. From ase/: PYTHONPATH=. ../.venv/bin/python ../docs/60-ai/sample-output/generate.py
import asyncio, json, pathlib
from app.archetypes.loader import load_cards
from app.store import MemoryStore
from app.workers.jobs import LookService

OUT = pathlib.Path(__file__).parent; OUT.mkdir(exist_ok=True)
CONSENT = {"ai_processing": True, "location": True, "personalisation": True}
VAULT = [
 {"id":"v-agbada","category":"native","name":"navy agbada","colours":["navy"],"fabric":"aso oke"},
 {"id":"v-kaftan","category":"native","name":"cream kaftan","colours":["cream"],"fabric":"cotton"},
 {"id":"v-sokoto","category":"bottoms","name":"cream sokoto","colours":["cream"],"fabric":"cotton"},
 {"id":"v-fila","category":"accessories","name":"navy fila","colours":["navy"]},
 {"id":"v-white","category":"tops","name":"white shirt","colours":["white"],"fabric":"cotton"},
 {"id":"v-blk","category":"bottoms","name":"black trousers","colours":["black"],"fabric":"cotton"},
 {"id":"v-loaf","category":"shoes","name":"brown loafers","colours":["brown"]},
 {"id":"v-sand","category":"shoes","name":"gold sandals","colours":["gold"]},
]
NAMES = {i["id"]: f'{i["name"]} ({i["category"]})' for i in VAULT}
async def main():
    md = ["# ASE output check\n", "Input vault:\n"] + [f"- `{i['id']}` {i['name']} ({i['category']}, {'/'.join(i['colours'])})" for i in VAULT] + [""]
    for occ in ("corporate", "owambe", "wedding", "casual"):
        for label, items in (("full vault", VAULT), ("empty vault", [])):
            st = MemoryStore(); svc = LookService(st, cards=lambda: load_cards(allow_draft=True))
            req = {"consents":CONSENT,"items":items,"occasion":occ,"gender":"male","weather":{"temp_c":29}}
            job = await svc.submit("u1","k",req,workspace_id="w1"); job = await svc.run(job.id)
            pub = job.public()
            (OUT / f"{occ}_{label.split()[0]}.json").write_text(json.dumps({"request": req, "result": pub}, indent=2, default=str))
            md.append(f"## {occ} - {label} -> {job.status}, mode `{pub.get('mode')}`\n")
            for n, lk in enumerate(pub.get("looks", []), 1):
                if lk.get("mode") == "wardrobe":
                    md.append(f"**Look {n}** - template `{lk['template']}`, confidence {lk['confidence']}, render `{lk['render'].get('strategy')}`")
                    md += [f"- {slot}: {NAMES[i]}" for slot, i in lk["slot_map"].items()]
                    md.append(f"- why: {lk['explanation']['why']}\n")
                else:
                    md.append(f"**Look {n}** (archetype card, no vault items): `{json.dumps(lk, default=str)[:300]}`\n")
    (OUT / "SUMMARY.md").write_text("\n".join(md))
asyncio.run(main())
