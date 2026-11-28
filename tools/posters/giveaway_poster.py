"""Giveaway poster: "Like and share this post for a chance to win an Imp", game coming December.

Same look as first_release_poster.py (docs/posters.md): drawn on a 640 x 360 art canvas with the
ui_kit.gd colours and gold bevelled frames, scaled x3 with nearest-neighbour to 1920 x 1080; text and
the 3D Impz (tools/posters/render_impz.gd renders) are added at full resolution.

    python tools/posters/giveaway_poster.py

Writes docs/images/posters/giveaway_poster.png.
"""
from pathlib import Path
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/images/posters/giveaway_poster.png"
RENDERS = ROOT / "docs/images/posters/first_release_impz_3d"
FONT = ROOT / "tools/posters/fonts/LilitaOne-Regular.ttf"   # title and headers (SIL OFL, fonts/OFL.txt)
SANS = ROOT / "godot-game/ui/fonts/Arimo.ttf"              # small labels (the game's plain "Arial" text style)
ITEMS = ROOT / "godot-game/assets/sprites/source/items"
PICKAXES = ROOT / "godot-game/assets/sprites/source/pickaxes"
BODIES = ROOT / "docs/imp-traits/bodies"
SHOTS = ROOT / "docs/images/posters/first_release_shots"

W, H, SCALE = 640, 360, 3


def hexc(s, a=255):
    s = s.lstrip("#")
    return (int(s[0:2], 16), int(s[2:4], 16), int(s[4:6], 16), a)


def fc(r, g, b, a=1.0):
    return (round(r * 255), round(g * 255), round(b * 255), round(a * 255))


def mix(a, b, t):
    return tuple(round(a[i] + (b[i] - a[i]) * t) for i in range(4))


def lighten(c, t):
    return mix(c, (255, 255, 255, c[3]), t)


def darken(c, t):
    return mix(c, (0, 0, 0, c[3]), t)


# ui_kit.gd colours
BG = fc(0.11, 0.12, 0.15)
SLOT = fc(0.18, 0.19, 0.23)
GOLD = hexc("#c99a4a")
STUD = hexc("#fff2c4")
OUTLINE = hexc("#0b0c10")
MUTED = fc(0.75, 0.74, 0.68)
GOOD = fc(0.55, 0.9, 0.5)
RARE = fc(1.0, 0.86, 0.4)
ENERGY = fc(0.98, 0.78, 0.25)
KEY = fc(0.95, 0.93, 0.85)

BAYER = [[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]

img = Image.new("RGBA", (W, H), OUTLINE)
px = img.load()
draw = ImageDraw.Draw(img)
draw.fontmode = "1"     # no anti-aliasing on text


def font(size, bold=False, sans=False):
    """Arimo is variable (weight 400 to 700). Text is drawn at full resolution, so `size` may be fractional."""
    f = ImageFont.truetype(str(SANS if sans else FONT), round(size * SCALE))
    if bold and sans:
        f.set_variation_by_name("Bold")
    return f


# ---------------------------------------------------------------- primitives

def put(x, y, c):
    if 0 <= x < W and 0 <= y < H:
        if c[3] == 255:
            px[x, y] = c
        elif c[3] > 0:
            px[x, y] = mix(px[x, y], (c[0], c[1], c[2], 255), c[3] / 255)


def rect(x, y, w, h, c):
    for j in range(y, y + h):
        for i in range(x, x + w):
            put(i, j, c)


def bands(x, y, w, h, stops, steps=6):
    """A vertical sky: flat colour bands with a Bayer dither seam between them."""
    for j in range(h):
        t = j / max(h - 1, 1) * (len(stops) - 1)
        k = min(int(t), len(stops) - 2)
        f = t - k
        q = f * steps
        lo = int(q)
        frac = q - lo
        for i in range(w):
            step = lo + (1 if frac * 16 > BAYER[j % 4][i % 4] + 0.5 else 0)
            put(x + i, y + j, mix(stops[k], stops[k + 1], min(step / steps, 1)))


def poly(points, c, ox=0, oy=0):
    draw.polygon([(ox + a, oy + b) for a, b in points], fill=c)


def disc(cx, cy, r, c):
    for j in range(-r, r + 1):
        for i in range(-r, r + 1):
            if i * i + j * j <= r * r + r * 0.6:
                put(cx + i, cy + j, c)


def cut(x, y, w, h, size):
    d = min(x, w - 1 - x) + min(y, h - 1 - y)
    return 0 if d < size else (1 if d == size else 2)


def panel(x0, y0, w, h, fill=BG, edge=GOLD, studs=True):
    """ui_kit.panel(): bevelled gold frame, corner studs, faint shine."""
    inner = 5 if studs else 4
    light, dark = lighten(edge, 0.4), darken(edge, 0.5)
    for y in range(h):
        for x in range(w):
            c = cut(x, y, w, h, 2)
            if c == 0:
                continue
            ring = min(x, y, w - 1 - x, h - 1 - y)
            if ring > inner:
                if fill is not None:
                    put(x0 + x, y0 + y, fill)
                continue
            lit = min(x, y) < min(w - 1 - x, h - 1 - y) or (x < w / 2 and y < h / 2)
            cx, cy = min(x, w - 1 - x), min(y, h - 1 - y)
            if c == 1 or ring == 0:
                col = OUTLINE
            elif studs and cx in (2, 3) and cy in (2, 3):
                col = STUD if cx == 2 and cy == 2 else light
            elif ring == 1:
                col = light if lit else dark
            elif ring < inner - 1:
                col = edge
            elif ring == inner - 1:
                col = mix(OUTLINE, fill or BG, 0.35)
            elif ring == inner and y == inner:
                col = lighten(fill, 0.07) if fill is not None else None
            else:
                col = fill
            if col is not None:
                put(x0 + x, y0 + y, col)
    return inner + 1


def slot(x0, y0, w, h, fill=SLOT, edge=OUTLINE):
    """ui_kit.slot(): recessed, shadow inside the top and left."""
    for y in range(h):
        for x in range(w):
            c = cut(x, y, w, h, 1)
            if c == 0:
                continue
            ring = min(x, y, w - 1 - x, h - 1 - y)
            if ring < 1:
                col = edge
            elif ring == 1:
                col = darken(fill, 0.5) if (x == 1 or y == 1) else lighten(fill, 0.15)
            else:
                col = fill
            put(x0 + x, y0 + y, col)


def pill(x0, y0, w, h, fill, lip=2):
    """ui_kit.button_box('normal'): raised, light top row, dark lip under it."""
    for y in range(h):
        for x in range(w):
            c = cut(x, y, w, h, 1)
            if c == 0:
                continue
            if c == 1 or x in (0, w - 1) or y in (0, h - 1):
                col = OUTLINE
            elif y >= h - 1 - lip:
                col = darken(fill, 0.5)
            elif y == 1:
                col = lighten(fill, 0.3)
            else:
                col = fill
            put(x0 + x, y0 + y, col)


texts = []   # drawn last, on the full 1920 x 1080 image, smooth and sharp (art coordinates x SCALE)


def text(x, y, s, size, color, shadow=2, anchor="la", bold=False, sans=False, stroke=0):
    texts.append((x, y, s, size, color, shadow, anchor, bold, sans, stroke))


def text_w(s, size, bold=False, sans=False):
    b = font(size, bold, sans).getbbox(s)
    return (b[2] - b[0]) / SCALE


def draw_texts(big):
    d = ImageDraw.Draw(big)
    for x, y, s, size, color, shadow, anchor, bold, sans, stroke in texts:
        f = font(size, bold, sans)
        X, Y = round(x * SCALE), round(y * SCALE)
        if shadow:
            o = shadow * 3      # a solid drop shadow, down and right
            d.text((X + o, Y + o), s, font=f, fill=OUTLINE[:3], anchor=anchor, stroke_width=stroke, stroke_fill=OUTLINE[:3])
        d.text((X, Y), s, font=f, fill=color[:3], anchor=anchor, stroke_width=stroke, stroke_fill=OUTLINE[:3])


def paste(im, x, y, scale=1):
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    img.alpha_composite(im, (x, y))


def gold_tab(x, y, s, size=16):
    """A menu title: gold text with the dark drop shadow, on a small dark tab."""
    w = round(text_w(s, size, bold=True)) + 16
    h = size + 6
    panel(x, y, w, h, fill=BG, studs=False)
    text(x + 8, y + h / 2, s, size, RARE, shadow=1, anchor="lm")
    return w, h


# ---------------------------------------------------------------- background

rng = random.Random(11)
bands(0, 0, W, H, [hexc("#120d24"), hexc("#1d1638"), hexc("#2c2350"), hexc("#3a2d5a")], steps=5)
for _ in range(120):
    x, y = rng.randrange(W), rng.randrange(int(H * 0.8))
    put(x, y, mix(KEY, hexc("#8fa8ff"), rng.random() * 0.5) if rng.random() < 0.8 else RARE)
for _ in range(8):            # a few bright cross stars
    x, y = rng.randrange(W), rng.randrange(int(H * 0.6))
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        put(x + dx, y + dy, KEY if (dx, dy) == (0, 0) else hexc("#9db0ff"))
# confetti: little flat 2 x 1 and 1 x 2 bits in the accent colours, a party feel without busy detail
CONFETTI = [RARE, GOOD, hexc("#f0a0c0"), hexc("#7fb2ff"), ENERGY]
for _ in range(70):
    x, y = rng.randrange(W), rng.randrange(int(H * 0.75))
    c = rng.choice(CONFETTI)
    if rng.random() < 0.5:
        rect(x, y, 2, 1, c)
    else:
        rect(x, y, 1, 2, c)
for i in range(W):            # far hills along the bottom, calm and dark
    hh = 26 + int(10 * abs(((i * 0.013) % 2) - 1)) + (i * 7 % 13 == 0)
    for j in range(H - hh, H):
        put(i, j, hexc("#1a1430"))
for i in range(W):
    hh = 14 + int(8 * abs(((i * 0.021 + 0.4) % 2) - 1))
    for j in range(H - hh, H):
        put(i, j, hexc("#130f24"))


# ---------------------------------------------------------------- pixel icons (drawn like the item icons: dark outline)

def pix(rows, colours, scale=2):
    """A small pixel icon from text rows: k outline, other letters from `colours`, '.' clear."""
    h, w = len(rows), max(len(r) for r in rows)
    ic = Image.new("RGBA", (w, h), (0, 0, 0, 0))
    p = ic.load()
    for j, row in enumerate(rows):
        for i, ch in enumerate(row):
            if ch != ".":
                p[i, j] = OUTLINE if ch == "k" else colours[ch]
    return ic.resize((w * scale, h * scale), Image.NEAREST)


HEART = pix([
    "...kkkk...kkkk...",
    "..kHHRRk.kHRRRk..",
    ".kHHRRRRkRRRRRRk.",
    "kHHRRRRRRRRRRRRRk",
    "kHRRRRRRRRRRRRRRk",
    "kRRRRRRRRRRRRRRRk",
    "kRRRRRRRRRRRRRRdk",
    ".kRRRRRRRRRRRRdk.",
    "..kRRRRRRRRRRdk..",
    "...kRRRRRRRRdk...",
    "....kRRRRRRdk....",
    ".....kRRRRdk.....",
    "......kRRdk......",
    ".......kdk.......",
    "........k........",
], {"R": hexc("#e8455f"), "H": hexc("#ff9aa8"), "d": hexc("#a82640")}, scale=3)

SHARE = pix([          # two arrows chasing each other round a loop: the plain "share again" sign
    "...k.............",
    "..kGk............",
    ".kGGGk...........",
    "kGGGGGk..........",
    "kkkGkkkkkkkkkk...",
    "..kGGGGGGGGGGGk..",
    "..kGkkkkkkkkkGk..",
    "..kGk.......kGk..",
    "..kGk.......kGk..",
    "..kGkkkkkkkkkGk..",
    "..kGGGGGGGGGGGk..",
    "...kkkkkkkkkkGkkk",
    "..........kGGGGGk",
    "...........kGGGk.",
    "............kGk..",
    ".............k...",
], {"G": GOOD}, scale=3)


# ---------------------------------------------------------------- left: title and the prize

LX, LW = 8, 300
text(LX + LW / 2, 20, "CLUB IMPZ", 22, RARE, shadow=2, anchor="mm", stroke=3)
text(LX + LW / 2, 54, "GIVEAWAY!", 52, RARE, shadow=2, anchor="mm", stroke=5)
win = "WIN AN IMP!"
pw = round(text_w(win, 26)) + 32
text(LX + LW / 2, 92, "FOR A CHANCE TO", 14, KEY, shadow=1, anchor="mm", bold=True, sans=True)
pill(LX + LW // 2 - pw // 2, 102, pw, 34, ENERGY, lip=3)
text(LX + LW / 2, 102 + 15.5, win, 26, OUTLINE, shadow=0, anchor="mm")

hero_slots = [(RENDERS / "gold_408.png", LX - 12, 186, 140),
              (RENDERS / "diamond_158.png", LX + LW - 132, 186, 140),
              (RENDERS / "cyan_111.png", LX + LW // 2 - 92, 160, 184)]


# ---------------------------------------------------------------- right: how to enter

RX, RW = 326, 306
RY, RH = 18, 196
panel(RX, RY, RW, RH)
gold_tab(RX + 12, RY - 8, "HOW TO ENTER", 16)

STEPS = [("1", "LIKE", "THIS POST", HEART), ("2", "SHARE", "THIS POST", SHARE)]
for n, (num, verb, rest, icon) in enumerate(STEPS):
    sy = RY + 22 + n * 84
    slot(RX + 14, sy, 72, 72)
    paste(icon, RX + 14 + (72 - icon.width) // 2, sy + (72 - icon.height) // 2)
    # the step number on a small gold pill over the slot's corner
    pill(RX + 8, sy - 4, 20, 18, RARE, lip=2)
    text(RX + 18, sy + 3.5, num, 13, OUTLINE, shadow=0, anchor="mm")
    text(RX + 100, sy + 27, verb, 46, KEY, shadow=2, anchor="lm", stroke=3)
    text(RX + 101, sy + 54, rest, 15, MUTED, shadow=1, anchor="lm", bold=True, sans=True)


# ---------------------------------------------------------------- right: the game

GY, GH = 236, 112
panel(RX, GY, RW, GH)
gold_tab(RX + 12, GY - 8, "THE GAME", 16)
cd = "COMING DECEMBER!"
cw = round(text_w(cd, 22)) + 28
pill(RX + RW // 2 - cw // 2, GY + 16, cw, 30, ENERGY, lip=3)
text(RX + RW / 2, GY + 16 + 13.5, cd, 22, OUTLINE, shadow=0, anchor="mm")
ICONS = [PICKAXES / "iron_pickaxe.png", ITEMS / "tool_iron_axe.png", ITEMS / "tool_oak_rod.png",
         ITEMS / "gemstone_diamond.png", ITEMS / "prestige_0.png"]
iw = 52
ix0 = RX + (RW - (len(ICONS) * iw + (len(ICONS) - 1) * 6)) // 2
for n, f in enumerate(ICONS):
    slot(ix0 + n * (iw + 6), GY + 54, iw, iw)
    paste(Image.open(f).convert("RGBA"), ix0 + n * (iw + 6) + 2, GY + 56)


# ---------------------------------------------------------------- save

OUT.parent.mkdir(parents=True, exist_ok=True)
big = img.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST)
for f, x, y, size in hero_slots:
    r = Image.open(f).convert("RGBA").resize((size * SCALE, size * SCALE), Image.LANCZOS)
    big.paste(r, (x * SCALE, y * SCALE), r)
draw_texts(big)
tmp = OUT.with_name(OUT.stem + ".tmp.png")
big.save(tmp)
tmp.replace(OUT)
print("saved", OUT)
