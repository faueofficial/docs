"""Generates faceless model photographs for the Style DNA card background.

Uses OpenRouter's image models. The key is read from the repo's .env and never
printed. Each image is framed from the neck down (or turned away), so no face is
shown: FAUE does not use people's faces, and an AI face would read as a real
person. Output is labelled illustrative wherever it is shown.

    python3 generate_models.py            # every persona: 2 women and 2 men each
    python3 generate_models.py CM         # one persona
"""
import base64, json, pathlib, re, sys, urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[5]
OUT = pathlib.Path(__file__).resolve().parent.parent / "models"
MODEL = "google/gemini-2.5-flash-image"
# `--tall` makes the 9:16 set for stories; the default is the 4:5 set for feed cards.
TALL = "--tall" in sys.argv
RATIO = "9:16" if TALL else "4:5"
SUFFIX = "-tall" if TALL else ""

FRAME = ("Editorial fashion photograph of Nigerian fashion, Lagos, portrait {ratio} full length, warm natural light, "
         "plain soft backdrop. Shot from the neck down so that NO face and no head is visible, "
         "with a Nigerian person's dark brown skin tone visible on the hands and forearms. "
         "No text, no logos, no watermark. Subject: ")

# Per persona: two women (f) and two men (m), in clothes people in Nigeria actually wear.
PERSONAS = {
    "CM": {
        "f": ["a woman in a minimalist iro and buba in plain sand-coloured hand-woven cotton, clean lines, one rust accent",
              "a woman in a long plain undyed cotton boubou with a subtle woven stripe over sage trousers"],
        "m": ["a man in a plain sand linen senator two-piece, round neckline, no embroidery, restrained",
              "a man in a simple olive cotton kaftan with matching trousers, clean and minimal"],
    },
    "OR": {
        "f": ["a woman in a burgundy and gold aso-oke iro, buba and ipele shawl, coral bead necklace and bracelets, ceremonial",
              "a woman in an emerald and gold Aso Ebi lace corset gown with a peplum, owambe celebration wear"],
        "m": ["a man in a richly embroidered royal-blue and gold agbada over matching trousers, coral beads on the wrist",
              "a man in a burgundy aso-oke agbada with gold embroidery, wearing a gold watch, ceremonial"],
    },
    "SL": {
        "f": ["a woman in a cream silk kaftan dress with a soft flowing drape, tonal, effortless Lagos chic",
              "a woman in a champagne satin wrapper skirt with a soft matching blouse, tonal layers"],
        "m": ["a man in a relaxed cream silk-cotton kaftan and drawstring trousers, tonal, easy",
              "a man in a soft taupe linen shirt-jacket and trousers, relaxed Lagos weekend wear"],
    },
    "SC": {
        "f": ["a woman in an oversized thrifted blazer over an adire-print skirt with chunky sneakers, eclectic Lagos streetwear",
              "a woman in layered mixed prints: an Ankara patchwork jacket over a graphic tee and denim"],
        "m": ["a man in an oversized denim jacket with Ankara patchwork over a graphic tee and wide cargo trousers, sneakers",
              "a man in a layered vintage football shirt over a long-sleeve top with kampala print trousers"],
    },
    "CE": {
        "f": ["a woman in a sharp black tailored trouser suit with a gold brooch, executive, polished",
              "a woman in a charcoal structured blazer dress, precise, one bold gold necklace"],
        "m": ["a man in a navy slim tailored two-piece and white shirt with a subtle pocket square, Lagos executive",
              "a man in a sharp black tailored senator two-piece with clean lines, polished and precise"],
    },
    "NF": {
        "f": ["a woman in a modern peplum top and tailored trousers in bold Ankara print, contemporary cut",
              "a woman in an adire-print blazer dress with a modern silhouette, heritage meets now"],
        "m": ["a man in an Ankara print bomber jacket over a plain tee with tailored neutral trousers",
              "a man in a kaftan-cut blazer in aso-oke fabric over a plain tee and slim jeans"],
    },
}


def key() -> str:
    text = (ROOT / ".env").read_text()
    found = re.findall(r"^\s*OPENROUTER_API_KEY\s*=\s*(.+?)\s*$", text, re.M)
    if not found:
        sys.exit("OPENROUTER_API_KEY is not in .env")
    return found[-1].strip("'\"")


def generate(prompt: str, api_key: str) -> bytes:
    body = json.dumps({
        "model": MODEL,
        "modalities": ["image", "text"],
        "image_config": {"aspect_ratio": RATIO},
        "messages": [{"role": "user", "content": FRAME.format(ratio=RATIO) + prompt}],
    }).encode()
    req = urllib.request.Request(
        "https://openrouter.ai/api/v1/chat/completions", data=body,
        headers={"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"})
    with urllib.request.urlopen(req, timeout=180) as r:
        data = json.load(r)
    if "choices" not in data:
        raise RuntimeError("OpenRouter said: " + json.dumps(data.get("error", data))[:300])
    images = data["choices"][0]["message"].get("images") or []
    if not images:
        raise RuntimeError("no image returned: " + json.dumps(data)[:300])
    url = images[0]["image_url"]["url"]
    return base64.b64decode(url.split(",", 1)[1])


if __name__ == "__main__":
    OUT.mkdir(exist_ok=True)
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    only = args[0] if args else None
    api_key = key()
    for pid, groups in PERSONAS.items():
        if only and pid != only:
            continue
        for sex, prompts in groups.items():
            for i, prompt in enumerate(prompts, 1):
                dest = OUT / f"{pid}-{sex}{i}{SUFFIX}.png"
                if dest.exists():
                    continue
                for attempt in (1, 2):
                    try:
                        dest.write_bytes(generate(prompt, api_key))
                        print("wrote", dest.name, flush=True)
                        break
                    except Exception as exc:  # rerun fills any gaps
                        print("failed", dest.name, attempt, "-", exc, flush=True)
