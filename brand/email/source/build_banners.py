"""Email banners, 2:1 (1200x600), headline drawn in the brand fonts.

Mail clients ignore web fonts (Gmail and Outlook fall back to Arial and Georgia),
so the headline is part of the image: Instrument Serif for the headline and
Plus Jakarta Sans for the kicker, the same faces as the website. The email's own
text underneath carries the same message for readers with images off, and the
image's alt text repeats the headline.

At a 375px phone the image scales to 31%: a 104px headline reads at about 32px.

    python3 build_banners.py
"""
import pathlib, subprocess, shutil, tempfile

from PIL import Image

import build_assets as A

OUT = A.OUT
FONTS = pathlib.Path(__file__).resolve().parents[4] / "landing" / "src" / "fonts"
PHOTOS = pathlib.Path(__file__).resolve().parents[4] / "landing" / "public" / "images"
CHROME = A.CHROME
W, H = 1200, 600

FOREST, OBSIDIAN, SAGE, PEACH, GOLD, BRONZE = A.FOREST, A.OBSIDIAN, A.SAGE, A.PEACH, A.GOLD, A.BRONZE
CREAM, PAPER = A.CREAM, A.PAPER


def key(color=GOLD, ring=None):
    return (f'<circle cx="260" cy="260" r="190" fill="{color}"/>'
            f'<circle cx="260" cy="260" r="214" fill="none" stroke="{ring or color}" stroke-opacity=".4" stroke-width="4"/>'
            f'<g fill="none" stroke="{OBSIDIAN}" stroke-width="22" stroke-linecap="round" stroke-linejoin="round">'
            f'<circle cx="196" cy="260" r="46"/><path d="M242 260H404M352 260V306M388 260V296"/></g>')


def wardrobe(sun_color=GOLD):
    return (A.sun(260, 270, 150, sun_color, 28, ".22")
            + A.garment("kaftan", 0, 140, 250) + A.garment("blazer", 150, 20, 320)
            + A.garment("bag", 350, 250, 170) + A.garment("sneaker", 290, 400, 200))


def swatches():
    pal = ["#f2ede4", "#c9b8a0", "#8a6f57", "#355c4f", "#25272c", "#b5451b"]
    dots = "".join(
        f'<circle cx="{110 + (i % 3) * 150}" cy="{150 + (i // 3) * 150}" r="62" fill="{c}" stroke="#F7F8F8" stroke-opacity=".5" stroke-width="4"/>'
        for i, c in enumerate(pal))
    bar = (f'<rect x="40" y="400" width="250" height="22" rx="11" fill="{GOLD}"/>'
           f'<rect x="298" y="400" width="140" height="22" rx="11" fill="{SAGE}" opacity=".85"/>'
           f'<rect x="446" y="400" width="40" height="22" rx="11" fill="{SAGE}" opacity=".5"/>')
    return dots + bar


def nametag():
    return (f'<path d="M205 0 L232 120 M315 0 L288 120" stroke="{SAGE}" stroke-width="7" stroke-linecap="round"/>'
            f'<g transform="translate(60 110) rotate(-4 200 160)"><rect width="400" height="330" rx="34" fill="{GOLD}" stroke="{OBSIDIAN}" stroke-opacity=".35" stroke-width="4"/>'
            f'<rect x="165" y="28" width="70" height="20" rx="10" fill="{FOREST}"/>'
            f'<rect x="54" y="112" width="200" height="36" rx="18" fill="{OBSIDIAN}" opacity=".85"/>'
            f'<rect x="54" y="172" width="290" height="20" rx="10" fill="{OBSIDIAN}" opacity=".35"/>'
            f'<rect x="54" y="208" width="220" height="20" rx="10" fill="{OBSIDIAN}" opacity=".25"/>'
            f'<circle cx="310" cy="268" r="36" fill="{FOREST}"/><path d="M292 268l13 13 27-30" fill="none" stroke="{PAPER}" stroke-width="9" stroke-linecap="round" stroke-linejoin="round"/></g>')


def door():
    return (A.sun(260, 470, 110, GOLD, 36, ".22")
            + f'<path d="M110 520V230a150 150 0 0 1 300 0V520Z" fill="{GOLD}"/><path d="M146 520V232a114 114 0 0 1 228 0V520Z" fill="{PEACH}"/>'
            + f'<path d="M260 118a114 114 0 0 1 114 114V520H260Z" fill="{CREAM}" opacity=".7"/>'
            + f'<path d="M256 118V520" stroke="{FOREST}" stroke-opacity=".25" stroke-width="4"/><circle cx="340" cy="340" r="11" fill="{FOREST}"/>')


def envelope():
    return (f'<g transform="translate(20 130) rotate(-3 240 130)"><rect width="480" height="280" rx="26" fill="{PAPER}" stroke="{OBSIDIAN}" stroke-opacity=".3" stroke-width="4"/>'
            f'<path d="M8 26 240 170 472 26" fill="none" stroke="{FOREST}" stroke-width="12" stroke-linejoin="round" stroke-linecap="round"/>'
            f'<path d="M8 262 180 130M472 262 300 130" stroke="{FOREST}" stroke-opacity=".35" stroke-width="7" stroke-linecap="round"/>'
            f'<circle cx="240" cy="170" r="38" fill="{GOLD}"/><path d="M224 170l11 11 22-24" fill="none" stroke="{OBSIDIAN}" stroke-width="8" stroke-linecap="round" stroke-linejoin="round"/></g>')


def check():
    return (f'<circle cx="260" cy="260" r="170" fill="{GOLD}"/>'
            f'<path d="M190 264l52 52 98-110" fill="none" stroke="{OBSIDIAN}" stroke-width="30" stroke-linecap="round" stroke-linejoin="round"/>')


# key -> (kicker, headline lines, background, dark?, art, pattern kind, photo)
SPECS = {
    "signin":   ("SIGN IN", ["Your key", "is here."], FOREST, True, key(), "lattice", None),
    "admin":    ("ADMIN CONSOLE", ["You are", "invited in."], OBSIDIAN, True, key(SAGE, GOLD), "grid", None),
    "welcome":  ("WELCOME TO FAUE", ["Your wardrobe,", "on your side."], FOREST, True, wardrobe(), "scallop", None),
    "back":     ("WELCOME BACK", ["Your wardrobe", "missed you."], PEACH, False, wardrobe(BRONZE), "scallop", None),
    "dna":      ("YOUR STYLE DNA", ["This is", "how you dress."], FOREST, True, swatches(), "zigzag", None),
    "look":     ("YOUR LOOK", ["Built from", "what you own."], FOREST, True, "", None, "flatlay-peach-crop.webp"),
    "detty":    ("DETTY DECEMBER", ["Owambe season,", "sorted."], OBSIDIAN, True, "", None, "style-or-1.webp"),
    "reply":    ("FROM THE FAUE TEAM", ["We read", "your message."], FOREST, True, envelope(), "scallop", None),
    "note":     ("A NOTE FROM FAUE", ["Someone wrote", "to you."], FOREST, True, envelope(), "scallop", None),
    "joined":   ("YOU ARE IN", ["Your name", "is saved."], FOREST, True, nametag(), "lattice", None),
    "invite":   ("FAUE IS OPEN", ["Your door", "is open."], OBSIDIAN, True, door(), "medallion", None),
    "done":     ("ALL DONE", ["You are off", "the list."], FOREST, True, check(), "medallion", None),
}


def page(kicker, lines, bg, dark, art, pattern_kind, photo):
    ink = "#FFFFFF" if dark else FOREST
    kick = GOLD if dark else BRONZE
    pat = ""
    if pattern_kind:
        pat = (f'<svg style="position:absolute;inset:0" width="{W}" height="{H}" viewBox="0 0 1200 600">'
               + A.pattern(pattern_kind, "#FFFFFF" if dark else BRONZE, .08 if dark else .10, 90, "bp").replace('height="400"', 'height="600"')
               + '</svg>')
    photo_css = ""
    if photo:
        photo_css = (f'<div style="position:absolute;inset:0;background:url(file://{PHOTOS / photo}) center/cover"></div>'
                     f'<div style="position:absolute;inset:0;background:linear-gradient(90deg,{bg} 0%,{bg}F2 34%,{bg}99 56%,{bg}00 82%)"></div>')
    art_svg = (f'<svg style="position:absolute;left:640px;top:40px" width="520" height="520" viewBox="0 0 520 520">{art}</svg>' if art else "")
    h = "".join(f"<div>{l}</div>" for l in lines)
    return f"""<!doctype html><meta charset=utf-8><style>
@font-face{{font-family:IS;src:url(file://{FONTS}/IS.woff2)}}
@font-face{{font-family:PJS;src:url(file://{FONTS}/PJS.woff2);font-weight:200 800}}
html,body{{margin:0;width:{W}px;height:{H}px;overflow:hidden}}
body{{position:relative;background:{bg}}}
.t{{position:absolute;left:72px;top:0;height:{H}px;width:600px;display:flex;flex-direction:column;justify-content:center}}
.k{{font:700 30px/1 PJS;letter-spacing:.2em;color:{kick}}}
.r{{width:72px;height:6px;border-radius:3px;background:{kick};margin:26px 0 30px}}
.h{{font:400 104px/1.04 IS;color:{ink};letter-spacing:-.01em}}
</style>{photo_css or ''}{pat}{art_svg}
<div class=t><div class=k>{kicker}</div><div class=r></div><div class=h>{h}</div></div>"""


def shoot(name, html):
    with tempfile.TemporaryDirectory() as tmp:
        src = pathlib.Path(tmp) / "b.html"
        src.write_text(html)
        png = pathlib.Path(tmp) / "b.png"
        subprocess.run([CHROME, "--headless=new", "--no-sandbox", "--disable-gpu", "--hide-scrollbars",
                        "--allow-file-access-from-files", "--virtual-time-budget=3000",
                        f"--screenshot={png}", f"--window-size={W},{H}", f"file://{src}"],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        Image.open(png).convert("RGB").save(OUT / f"banner-{name}.jpg", quality=84, optimize=True)


if __name__ == "__main__":
    for old in OUT.glob("banner-*.png"):
        old.unlink()
    for name, spec in SPECS.items():
        shoot(name, page(*spec))
        print("banner", name)
    # brand fonts, served to clients that do honour @font-face (Apple Mail, iOS Mail)
    fonts = OUT / "fonts"
    fonts.mkdir(exist_ok=True)
    for src, dst in (("IS.woff2", "InstrumentSerif-Regular.woff2"), ("IS-Italic.woff2", "InstrumentSerif-Italic.woff2"), ("PJS.woff2", "PlusJakartaSans.woff2")):
        shutil.copy(FONTS / src, fonts / dst)
