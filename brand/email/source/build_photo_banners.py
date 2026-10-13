"""Photographic email banners: a real photo, a brand fade and a gold badge.

Every photo is faceless fabric or clothing from the website's licensed set (see
landing/ASSETS.md and /credits). The meaning is carried by the badge icon and by
the email's own copy, never by text in the image. Output is JPEG (photos compress
far better than PNG) at 1200x400, shown at 600x200.

    python3 build_photo_banners.py
"""
import pathlib
from PIL import Image, ImageDraw, ImageFilter

HERE = pathlib.Path(__file__).resolve().parent
PHOTOS = HERE.parents[3] / "landing" / "public" / "images"
OUT = HERE.parent / "assets"

FOREST, OBSIDIAN, GOLD = (15, 61, 46), (5, 22, 17), (231, 168, 61)
W, H = 1200, 400

#: banner key -> (photo, focal y 0..1, badge icon)
BANNERS = {
    "signin":   ("drape-black.webp", 0.45, "key"),
    "welcome":  ("fabric-stall-clean.webp", 0.40, "star"),
    "dna":      ("indigo-patchwork.webp", 0.50, "bars"),
    "look":     ("flatlay-peach-crop.webp", 0.50, "hanger"),
    "detty":    ("style-or-1.webp", 0.50, "star"),
    "waitlist": ("style-sl-3.webp", 0.50, "tick"),
    "invite":   ("style-or-2.webp", 0.45, "arrow"),
    "envelope": ("sewing-tools.webp", 0.50, "envelope"),
    "done":     ("style-ce-2.webp", 0.50, "tick"),
}


def cover(im: Image.Image, focal_y: float) -> Image.Image:
    s = max(W / im.width, H / im.height)
    im = im.resize((round(im.width * s), round(im.height * s)), Image.LANCZOS)
    left = (im.width - W) // 2
    top = round((im.height - H) * focal_y)
    return im.crop((left, top, left + W, top + H))


def fade(im: Image.Image) -> Image.Image:
    """Forest from the left, clear on the right: anchors the badge and keeps the
    whole set recognisably one family whatever the photo."""
    over = Image.new("RGBA", (W, H))
    px = over.load()
    for x in range(W):
        a = max(0, int(255 * 0.78 * (1 - x / (W * 0.62))))
        for y in range(H):
            px[x, y] = (*FOREST, a)
    return Image.alpha_composite(im.convert("RGBA"), over)


def badge(im: Image.Image, icon: str) -> Image.Image:
    S = 4                                    # supersample for clean edges
    layer = Image.new("RGBA", (W * S, H * S), (0, 0, 0, 0))
    d = ImageDraw.Draw(layer)
    cx, cy, r = 118 * S, 280 * S, 70 * S
    d.ellipse((cx - r - 7 * S, cy - r - 7 * S, cx + r + 7 * S, cy + r + 7 * S), fill=(*OBSIDIAN, 70))
    d.ellipse((cx - r, cy - r, cx + r, cy + r), fill=(*GOLD, 255))
    ink = (*OBSIDIAN, 255)
    w = 13 * S

    def line(*pts):
        d.line([(cx + x * S, cy + y * S) for x, y in pts], fill=ink, width=w, joint="curve")
        for x, y in (pts[0], pts[-1]):
            d.ellipse((cx + x * S - w / 2, cy + y * S - w / 2, cx + x * S + w / 2, cy + y * S + w / 2), fill=ink)

    if icon == "tick":
        line((-26, 2), (-8, 20), (28, -20))
    elif icon == "key":
        d.ellipse((cx - 38 * S, cy - 17 * S, cx - 4 * S, cy + 17 * S), outline=ink, width=w)
        line((-4, 0), (36, 0)); line((22, 0), (22, 16)); line((36, 0), (36, 12))
    elif icon == "star":
        import math
        pts = []
        for i in range(10):
            ang = -math.pi / 2 + i * math.pi / 5
            rad = 38 if i % 2 == 0 else 16
            pts.append((cx + rad * math.cos(ang) * S, cy + rad * math.sin(ang) * S))
        d.polygon(pts, fill=ink)
    elif icon == "bars":
        for i, (hh, x) in enumerate(((26, -30), (44, -4), (62, 22))):
            d.rounded_rectangle((cx + x * S, cy + (30 - hh) * S, cx + (x + 16) * S, cy + 32 * S), radius=5 * S, fill=ink)
    elif icon == "hanger":
        line((0, -12), (0, -26)); line((0, -12), (-36, 18), (36, 18), (0, -12))
    elif icon == "envelope":
        d.rounded_rectangle((cx - 38 * S, cy - 26 * S, cx + 38 * S, cy + 26 * S), radius=8 * S, outline=ink, width=w)
        line((-34, -20), (0, 8), (34, -20))
    elif icon == "arrow":
        line((-28, 0), (28, 0)); line((6, -22), (28, 0), (6, 22))
    layer = layer.resize((W, H), Image.LANCZOS)
    return Image.alpha_composite(im, layer)


def build() -> None:
    OUT.mkdir(parents=True, exist_ok=True)
    for key, (photo, fy, icon) in BANNERS.items():
        im = cover(Image.open(PHOTOS / photo).convert("RGB"), fy)
        im = badge(fade(im), icon).convert("RGB")
        d = ImageDraw.Draw(im)
        d.rectangle((0, H - 8, W, H), fill=GOLD)           # the brand's one accent, as a rule
        dest = OUT / f"banner-{key}.jpg"
        im.save(dest, "JPEG", quality=80, optimize=True, progressive=True)
        print(f"{key:9} {photo:24} {dest.stat().st_size // 1024:4d} KB")


if __name__ == "__main__":
    build()
