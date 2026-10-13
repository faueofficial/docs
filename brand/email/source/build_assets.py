"""Builds the email illustrations as PNG (email clients do not reliably show SVG).

Brand tokens only: forest, obsidian, sage, peach, gold, bronze and the persona
accent colours. No text in the images, so the message lives in the email's own
copy, stays translatable and survives images being off. Run from this folder:

    python3 build_assets.py
"""
import pathlib, subprocess, shutil, sys

OUT = pathlib.Path(__file__).resolve().parent.parent / "assets"
CHROME = shutil.which("google-chrome") or shutil.which("chromium") or "google-chrome"

FOREST, OBSIDIAN, SAGE, PEACH, GOLD, BRONZE = "#0F3D2E", "#051611", "#BCC9C4", "#FBE6D9", "#E7A83D", "#663A2B"
RUST, BURGUNDY, INDIGO, CREAM, PAPER = "#B5451B", "#7A1F3D", "#2B3A8C", "#F2EDE4", "#F7F8F8"

TILES = {
    "lattice": '<path d="M60 8 112 60 60 112 8 60Z"/><path d="M60 34 86 60 60 86 34 60Z"/><rect x="54" y="54" width="12" height="12"/>',
    "zigzag": '<path d="M0 30 15 15 30 30 45 15 60 30 75 15 90 30 105 15 120 30"/><path d="M0 60 15 45 30 60 45 45 60 60 75 45 90 60 105 45 120 60"/><path d="M60 78 80 98 60 118 40 98Z"/>',
    "scallop": '<path d="M0 60a30 30 0 0 1 60 0a30 30 0 0 1 60 0"/><path d="M-30 120a30 30 0 0 1 60 0a30 30 0 0 1 60 0a30 30 0 0 1 60 0"/>',
    "grid": '<path d="M0 30H120M0 90H120M30 0V120M90 0V120"/><rect x="24" y="24" width="12" height="12"/><rect x="84" y="84" width="12" height="12"/>',
    "medallion": '<path d="M60 6 114 60 60 114 6 60Z"/><circle cx="60" cy="60" r="22"/><circle cx="60" cy="60" r="8"/><path d="M60 0V16M60 104V120M0 60H16M104 60H120"/>',
}

GARMENTS = {  # d, extra, default fill
    "blazer": ("M33 12 44 8 50 20 56 8 67 12 83 30 77 44 70 38V90H30V38L23 44 17 30Z", "M50 20V90M44 8 50 46 56 8M58 62h4", FOREST),
    "trousers": ("M32 14H68L72 88H54L50 40 46 88H28Z", "M50 14V40", "#B6BAC3"),
    "kaftan": ("M41 8H59L66 15 84 30 80 41 70 35 79 94H21L30 35 20 41 16 30 34 15Z", "M43 8Q50 20 57 8M50 20V52M30 78H70", "#5C7B71"),
    "tee": ("M34 16 44 12Q50 20 56 12L66 16 84 30 76 42 68 36V82H32V36L24 42 16 30Z", "", "#EDEEF1"),
    "bag": ("M26 38H74L78 86H22Z", "M38 38V28Q50 12 62 28V38", "#25272C"),
    "sneaker": ("M14 62Q14 50 28 48L40 52 58 40 70 46Q86 50 88 62V70H14Z", "M14 70H88M40 52 46 60M50 48 56 56", PAPER),
    "gown": ("M40 8H46Q50 18 54 8H60L62 34L58 42Q78 60 86 94H14Q22 60 42 42L38 34Z", "M42 42H58M50 46V92M41 52 30 92M59 52 70 92", BURGUNDY),
    "gele": ("M18 64Q4 38 22 26Q34 8 50 20Q66 6 78 26Q96 38 82 64Q68 74 50 74Q32 74 18 64Z", "M30 28Q42 46 28 64M50 20Q58 46 50 72M70 28Q58 46 72 64M24 74Q50 90 76 74", GOLD),
    "agbada": ("M40 8H60L70 14 96 46 84 64 74 56V92H26V56L16 64 4 46 30 14Z", "M44 8 50 24 56 8M26 56Q50 72 74 56M50 24V92", INDIGO),
}

def pattern(kind, color, opacity, size=70, pid="p"):
    return (f'<defs><pattern id="{pid}" width="{size}" height="{size}" patternUnits="userSpaceOnUse" viewBox="0 0 120 120">'
            f'<g fill="none" stroke="{color}" stroke-width="3">{TILES[kind]}</g></pattern></defs>'
            f'<rect width="1200" height="400" fill="url(#{pid})" opacity="{opacity}"/>')

def garment(name, x, y, size, fill=None, rot=0, print_color=None, pid=None):
    d, extra, default = GARMENTS[name]
    f = fill or default
    s = size / 100
    dark = f.upper() not in {PAPER, "#EDEEF1", CREAM, PEACH, SAGE}
    line = "#F7F8F8" if dark else OBSIDIAN
    overlay = ""
    if print_color:
        overlay = (f'<clipPath id="c{pid}"><path d="{d}"/></clipPath>'
                   f'<rect width="100" height="100" fill="url(#t{pid})" opacity=".55" clip-path="url(#c{pid})"/>'
                   f'<defs><pattern id="t{pid}" width="22" height="22" patternUnits="userSpaceOnUse" viewBox="0 0 120 120">'
                   f'<g fill="none" stroke="{print_color}" stroke-width="6">{TILES["zigzag"]}</g></pattern></defs>')
    return (f'<g transform="translate({x} {y}) rotate({rot} {size/2} {size/2}) scale({s})">'
            f'<path d="{d}" fill="{f}" stroke="{OBSIDIAN}" stroke-opacity=".35" stroke-width="1.4" stroke-linejoin="round"/>'
            f'{overlay}'
            f'<path d="{extra}" fill="none" stroke="{line}" stroke-opacity=".55" stroke-width="1.4" stroke-linecap="round"/></g>') if extra else \
           (f'<g transform="translate({x} {y}) rotate({rot} {size/2} {size/2}) scale({s})"><path d="{d}" fill="{f}" stroke="{OBSIDIAN}" stroke-opacity=".35" stroke-width="1.4" stroke-linejoin="round"/></g>')

def root(body):
    return f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">{body}</svg>'


def svg(body, bg):
    return (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 400" width="1200" height="400">'
            f'<rect width="1200" height="400" fill="{bg}"/>{body}</svg>')

def sun(cx, cy, r, color, n=24, op=".18"):
    import math
    rays = "".join(
        f'<path d="M{cx} {cy} L{cx + r*1.6*math.cos(a - .045):.1f} {cy + r*1.6*math.sin(a - .045):.1f} L{cx + r*1.6*math.cos(a + .045):.1f} {cy + r*1.6*math.sin(a + .045):.1f}Z" fill="{color}" opacity="{op}"/>'
        for a in [i * 2 * math.pi / n for i in range(n)])
    return rays + f'<circle cx="{cx}" cy="{cy}" r="{r}" fill="{color}" opacity=".9"/>'

BANNERS = {}

# 1. welcome: a wardrobe laid out, the start of something
BANNERS["welcome"] = svg(
    pattern("scallop", BRONZE, .12, 90, "pw") + sun(600, 210, 118, GOLD, 28, ".22")
    + garment("kaftan", 190, 60, 250) + garment("blazer", 410, 36, 290) + garment("bag", 700, 90, 220) + garment("sneaker", 900, 140, 190)
    + f'<rect x="0" y="372" width="1200" height="28" fill="{FOREST}"/><rect x="0" y="366" width="1200" height="6" fill="{GOLD}"/>',
    PEACH)

# 2. sign in: a key, in gold, on forest
BANNERS["signin"] = svg(
    pattern("lattice", GOLD, .16, 80, "ps")
    + f'<circle cx="600" cy="200" r="132" fill="{GOLD}"/><circle cx="600" cy="200" r="150" fill="none" stroke="{GOLD}" stroke-opacity=".4" stroke-width="3"/>'
    + f'<g fill="none" stroke="{OBSIDIAN}" stroke-width="16" stroke-linecap="round" stroke-linejoin="round"><circle cx="560" cy="200" r="34"/><path d="M594 200H690M652 200V232M680 200V222"/></g>',
    FOREST)

# 3. Style DNA: the card, tilted, with its blend bar
BANNERS["dna"] = root(
    f'<defs><linearGradient id="g" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{FOREST}"/><stop offset="1" stop-color="{RUST}"/></linearGradient></defs>'
    f'<rect width="1200" height="400" fill="url(#g)"/>' + pattern("zigzag", CREAM, .14, 80, "pd")
    + f'<g transform="translate(470 40) rotate(-5 130 160)"><rect width="260" height="330" rx="26" fill="{FOREST}" stroke="{CREAM}" stroke-opacity=".5" stroke-width="3"/>'
      f'<rect x="26" y="28" width="62" height="30" rx="4" fill="{PAPER}"/><rect x="26" y="130" width="130" height="38" rx="8" fill="{GOLD}"/>'
      f'<rect x="26" y="184" width="190" height="14" rx="7" fill="{CREAM}" opacity=".85"/><rect x="26" y="206" width="150" height="10" rx="5" fill="{CREAM}" opacity=".5"/>'
      f'<rect x="26" y="262" width="120" height="10" rx="5" fill="{GOLD}"/><rect x="150" y="262" width="62" height="10" rx="5" fill="{CREAM}" opacity=".7"/><rect x="216" y="262" width="22" height="10" rx="5" fill="{CREAM}" opacity=".4"/>'
      f'<g fill="{GOLD}"><circle cx="38" cy="300" r="9"/></g><circle cx="64" cy="300" r="9" fill="{RUST}"/><circle cx="90" cy="300" r="9" fill="{BURGUNDY}"/><circle cx="116" cy="300" r="9" fill="{CREAM}"/></g>'
    + f'<circle cx="250" cy="110" r="14" fill="{GOLD}"/><circle cx="950" cy="290" r="20" fill="{CREAM}" opacity=".5"/><circle cx="980" cy="120" r="10" fill="{GOLD}"/>'
)

# 4. look: pieces on a rail, an outfit coming together
BANNERS["look"] = svg(
    pattern("scallop", BRONZE, .10, 90, "pl")
    + f'<path d="M120 86H1080" stroke="{FOREST}" stroke-width="8" stroke-linecap="round"/>'
    + "".join(f'<path d="M{x} 86 v28" stroke="{FOREST}" stroke-width="6"/><circle cx="{x}" cy="86" r="9" fill="{GOLD}"/>' for x in (310, 500, 700, 890))
    + garment("blazer", 190, 112, 220) + garment("tee", 400, 124, 210) + garment("trousers", 612, 112, 220) + garment("bag", 830, 138, 190),
    PEACH)

# 5. waitlist: a reserved name tag
BANNERS["waitlist"] = svg(
    pattern("lattice", GOLD, .15, 80, "pq")
    + f'<path d="M560 0 L585 78 M640 0 L615 78" stroke="{SAGE}" stroke-width="5" stroke-linecap="round"/>'
    + f'<g transform="translate(450 70) rotate(-3 150 130)"><rect width="300" height="260" rx="26" fill="{GOLD}" stroke="{OBSIDIAN}" stroke-opacity=".35" stroke-width="3"/>'
      f'<rect x="125" y="22" width="50" height="14" rx="7" fill="{FOREST}"/>'
      f'<rect x="40" y="86" width="150" height="26" rx="13" fill="{OBSIDIAN}" opacity=".85"/><rect x="40" y="132" width="220" height="14" rx="7" fill="{OBSIDIAN}" opacity=".35"/><rect x="40" y="160" width="170" height="14" rx="7" fill="{OBSIDIAN}" opacity=".25"/>'
      f'<circle cx="226" cy="214" r="26" fill="{FOREST}"/><path d="M213 214l10 10 20-22" fill="none" stroke="{PAPER}" stroke-width="7" stroke-linecap="round" stroke-linejoin="round"/></g>',
    FOREST)

# 6. invite: the door opens
BANNERS["invite"] = svg(
    sun(600, 340, 90, GOLD, 36, ".22")
    + f'<path d="M470 400V190a130 130 0 0 1 260 0V400Z" fill="{GOLD}"/><path d="M500 400V192a100 100 0 0 1 200 0V400Z" fill="{PEACH}"/>'
    + f'<path d="M600 92a100 100 0 0 1 100 100V400H600Z" fill="{CREAM}" opacity=".7"/>'
    + f'<path d="M596 92V400" stroke="{FOREST}" stroke-opacity=".25" stroke-width="3"/>'
    + f'<circle cx="680" cy="270" r="9" fill="{FOREST}"/>'
    + f'<g fill="{GOLD}"><circle cx="300" cy="120" r="10"/><circle cx="920" cy="150" r="14"/><circle cx="240" cy="290" r="7"/><circle cx="980" cy="300" r="9"/></g>',
    OBSIDIAN)

# 7. envelope: a reply on its way
BANNERS["envelope"] = svg(
    pattern("scallop", SAGE, .10, 90, "pe")
    + f'<g transform="translate(400 90) rotate(-2 200 110)"><rect width="400" height="230" rx="22" fill="{PAPER}" stroke="{OBSIDIAN}" stroke-opacity=".3" stroke-width="3"/>'
      f'<path d="M6 20 200 140 394 20" fill="none" stroke="{FOREST}" stroke-width="10" stroke-linejoin="round" stroke-linecap="round"/>'
      f'<path d="M6 214 150 110M394 214 250 110" stroke="{FOREST}" stroke-opacity=".35" stroke-width="6" stroke-linecap="round"/>'
      f'<circle cx="200" cy="140" r="30" fill="{GOLD}"/><path d="M187 140l9 9 18-20" fill="none" stroke="{OBSIDIAN}" stroke-width="6" stroke-linecap="round" stroke-linejoin="round"/></g>',
    FOREST)

# 8. Detty December: the season, dressed
BANNERS["detty"] = root(
    f'<defs><linearGradient id="g2" x1="0" y1="0" x2="1" y2="1"><stop offset="0" stop-color="{BURGUNDY}"/><stop offset="1" stop-color="{RUST}"/></linearGradient></defs>'
    f'<rect width="1200" height="400" fill="url(#g2)"/>' + pattern("zigzag", GOLD, .22, 80, "pt")
    + sun(600, 230, 100, GOLD, 30, ".18")
    + garment("agbada", 215, 110, 200, print_color=GOLD, pid="a") + garment("gown", 515, 80, 230, print_color=GOLD, pid="b") + garment("gele", 810, 130, 170)
    + "".join(f'<circle cx="{x}" cy="{y}" r="{r}" fill="{GOLD}"/>' for x, y, r in ((110, 80, 9), (1080, 110, 12), (170, 320, 7), (1020, 320, 8), (460, 60, 6), (760, 50, 8)))
)

# 9. done: a clean confirmation
BANNERS["done"] = svg(
    pattern("medallion", SAGE, .12, 90, "pn")
    + f'<circle cx="600" cy="200" r="120" fill="{GOLD}"/><path d="M548 202l36 36 72-80" fill="none" stroke="{OBSIDIAN}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round"/>',
    FOREST)

# --- small images -----------------------------------------------------------

def icon_svg(name):
    if name == "instagram":
        return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="96" height="96"><rect width="24" height="24" fill="#051611"/>'
                '<g fill="none" stroke="#F7F8F8" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><rect x="3" y="3" width="18" height="18" rx="5"/><circle cx="12" cy="12" r="4"/></g>'
                '<circle cx="17.2" cy="6.8" r=".9" fill="#F7F8F8"/></svg>')
    return ('<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" width="96" height="96"><rect width="24" height="24" fill="#051611"/>'
            '<path fill="#F7F8F8" d="M17.75 3h3.07l-6.7 7.66L22 21h-6.17l-4.83-6.32L5.47 21H2.4l7.17-8.2L2 3h6.33l4.37 5.78L17.75 3Zm-1.08 16.16h1.7L7.4 4.74H5.58l11.09 14.42Z"/></svg>')

def shoot(svg_text, name, w, h):
    tmp = OUT / f"_{name}.svg"
    tmp.write_text(svg_text)
    dest = OUT / f"{name}.png"
    subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                    f"--screenshot={dest}", f"--window-size={w},{h}", f"file://{tmp}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp.unlink()

if __name__ == "__main__":
    OUT.mkdir(parents=True, exist_ok=True)
    for key, body in BANNERS.items():
        shoot(body, f"banner-{key}", 1200, 400)
        print("banner", key)
    for name in ("instagram", "x"):
        shoot(icon_svg(name), f"icon-{name}", 96, 96)
    # Header and footer marks come from the brand kit, already outlined.
    logos = pathlib.Path(__file__).resolve().parents[2] / "logo" / "png"
    shutil.copy(logos / "faue-wordmark-box-light-512.png", OUT / "logo-light.png")
    shutil.copy(logos / "faue-wordmark-box-green-512.png", OUT / "logo-green.png")
    print("done")
