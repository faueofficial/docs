"""Draws sample look and tailor share cards for review. The pieces are made-up shapes, not photographs.

From api-gateway/:  PYTHONPATH=. ../.venv/bin/python ../docs/60-ai/sample-output/cards/generate_cards.py
"""
import io
import pathlib
import random

from PIL import Image, ImageDraw, ImageFilter

from app.modules.cards import looks

OUT = pathlib.Path(__file__).parent


def _jpeg(img: Image.Image) -> bytes:
    buf = io.BytesIO()
    img.save(buf, format="JPEG", quality=92)
    return buf.getvalue()


def _ground(w=700, h=900, tone=(238, 232, 220)) -> Image.Image:
    img = Image.new("RGB", (w, h), tone)
    d = ImageDraw.Draw(img)
    for y in range(h):  # a soft studio gradient
        k = y / h
        d.line((0, y, w, y), fill=tuple(round(c * (1.04 - 0.1 * k)) for c in tone))
    return img


def _shade(img: Image.Image) -> Image.Image:
    return img.filter(ImageFilter.GaussianBlur(0.8))


def garment(kind: str, colour: tuple[int, int, int], trim=(231, 168, 61)) -> bytes:
    img = _ground()
    d = ImageDraw.Draw(img)
    dark = tuple(max(c - 35, 0) for c in colour)
    if kind == "shirt":
        d.polygon([(190, 170), (300, 140), (350, 190), (400, 140), (510, 170), (640, 330), (560, 380), (510, 300), (510, 760), (190, 760), (190, 300), (140, 380), (60, 330)], fill=colour)
        d.line((350, 190, 350, 760), fill=dark, width=4)
        for y in range(260, 740, 90):
            d.ellipse((340, y, 360, y + 20), fill=dark)
    elif kind == "trousers":
        d.polygon([(190, 130), (510, 130), (540, 790), (385, 790), (350, 360), (315, 790), (160, 790)], fill=colour)
        d.line((190, 175, 510, 175), fill=dark, width=8)
    elif kind == "agbada":
        d.polygon([(250, 120), (450, 120), (680, 420), (660, 800), (40, 800), (20, 420)], fill=colour)
        d.polygon([(300, 120), (400, 120), (350, 330)], fill=dark)
        d.rectangle((320, 330, 380, 800), fill=tuple(min(c + 30, 255) for c in colour))
        for x in range(60, 640, 36):
            d.line((x, 560, x + 10, 800), fill=trim, width=3)
        d.line((250, 120, 20, 420), fill=trim, width=8)
        d.line((450, 120, 680, 420), fill=trim, width=8)
    elif kind == "kaftan":
        d.polygon([(230, 130), (470, 130), (610, 330), (570, 390), (500, 300), (520, 820), (180, 820), (200, 300), (130, 390), (90, 330)], fill=colour)
        d.polygon([(310, 130), (390, 130), (350, 260)], fill=dark)
        d.line((350, 260, 350, 560), fill=trim, width=5)
    elif kind == "shoes":
        for dx, dy in ((0, 0), (0, 260)):
            d.rounded_rectangle((170, 220 + dy, 540, 330 + dy), radius=45, fill=colour)
            d.ellipse((430, 200 + dy, 590, 330 + dy), fill=colour)
            d.rectangle((170, 322 + dy, 545, 345 + dy), fill=dark)
    elif kind == "fila":
        d.polygon([(150, 560), (210, 330), (350, 280), (490, 330), (550, 560)], fill=colour)
        d.rounded_rectangle((120, 540, 580, 620), radius=24, fill=dark)
        for x in range(190, 520, 28):
            d.line((x, 345, x + 6, 530), fill=trim, width=3)
    return _jpeg(_shade(img))


def fabric(colours: list[tuple[int, int, int]], w=960, h=540) -> bytes:
    """Aso-oke style: bands of colour with a fine woven grain."""
    rnd = random.Random(7)
    img = Image.new("RGB", (w, h))
    d = ImageDraw.Draw(img)
    x = 0
    while x < w:
        band = rnd.choice((26, 40, 64, 18))
        d.rectangle((x, 0, x + band, h), fill=colours[(x // 7) % len(colours)])
        x += band
    for y in range(0, h, 4):
        d.line((0, y, w, y), fill=(0, 0, 0), width=1)
    for _ in range(9000):
        gx, gy = rnd.randrange(w), rnd.randrange(h)
        d.point((gx, gy), fill=(255, 255, 255))
    return _jpeg(img.filter(ImageFilter.GaussianBlur(0.6)))


NAVY, CREAM, CHARCOAL, BROWN, GOLD, WHITE = (24, 41, 92), (231, 220, 196), (44, 46, 52), (110, 70, 42), (214, 162, 58), (240, 238, 232)

# The reasons below are real output of the ASE engine for this sample wardrobe (the static explanation, which is what a look carries
# when the model plane is off). A model-written reason, when one passes the grounding check, replaces it.
OWAMBE_WHY = "Navy is here because you like it. The navy agbada is the whole outfit; the shoes are all it needs. Your navy holds it steady and lets the rest be quieter."
OFFICE_WHY = "A top, bottoms and shoes, kept simple. It is built around your white, with the other colours kept calm beside it. Everything here sits in a quiet palette."
CHURCH_WHY = "The cream kaftan has no wears logged, which makes it a fresh pick. Your cream holds it steady and lets the rest be quieter. Cream and gold sit well together."

owambe_tiles = [looks.Tile("native", "Navy agbada", garment("agbada", NAVY)), looks.Tile("shoes", "Gold sandals", garment("shoes", GOLD)),
                looks.Tile("accessory", "Navy fila", garment("fila", NAVY))]
cards = {}
for ratio in looks.RATIOS:
    cards[f"look-card-owambe-{ratio}"] = looks.render_look_card(title="Owambe, sorted", why=OWAMBE_WHY, tiles=owambe_tiles, ratio=ratio)
cards["look-card-office-4x5"] = looks.render_look_card(
    title="A look for the office", why=OFFICE_WHY, ratio="4x5",
    tiles=[looks.Tile("top", "White shirt", garment("shirt", WHITE)), looks.Tile("bottom", "Black trousers", garment("trousers", CHARCOAL)),
           looks.Tile("shoes", "Brown loafers", garment("shoes", BROWN))])
cards["look-card-no-photo-4x5"] = looks.render_look_card(
    title="Sunday, dressed", why=CHURCH_WHY, ratio="4x5",
    tiles=[looks.Tile("native", "Cream kaftan", None), looks.Tile("shoes", "Gold sandals", garment("shoes", GOLD))])
cards["tailor-card"] = looks.render_tailor_card(looks.TailorSpec(
    style="Agbada with a matching fila",
    fabric=fabric([NAVY, GOLD, CREAM]),
    fabric_name="Aso oke, navy and gold, 6 yards",
    garment="Three-piece agbada, wide sleeves, gold edging",
    note="Keep the shoulder line sharp and the sleeves wide. Gold thread on the neckline only. I need it by the 14th for the wedding.",
    measurements=[("Chest", "42"), ("Waist", "36"), ("Shoulder", "18.5"), ("Sleeve", "25"), ("Length", "58"), ("Neck", "16")],
))
for old in OUT.glob("*.jpg"):
    old.unlink()
for name, data in cards.items():
    (OUT / f"{name}.jpg").write_bytes(data)
    print(name, len(data) // 1024, "KB", Image.open(io.BytesIO(data)).size)
