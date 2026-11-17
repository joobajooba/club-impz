"""First release poster: "Club Impz, coming December".

Follows docs/posters.md: drawn on a 640 x 360 art canvas in the menu look
(ui_kit.gd colours, gold bevelled frames, Pixelify Sans), then scaled x3 with
nearest-neighbour to 1920 x 1080.

    python tools/posters/first_release_poster.py

Writes docs/images/posters/first_release_poster.png.
"""
from pathlib import Path
import random

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
OUT = ROOT / "docs/images/posters/first_release_poster.png"
FONT = ROOT / "godot-game/ui/fonts/PixelifySans.ttf"
ITEMS = ROOT / "godot-game/assets/sprites/source/items"
PICKAXES = ROOT / "godot-game/assets/sprites/source/pickaxes"
BODIES = ROOT / "docs/imp-traits/bodies"

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


def font(size):
    return ImageFont.truetype(str(FONT), size)


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


def text(x, y, s, size, color, shadow=2, anchor="la"):
    f = font(size)
    if shadow:
        draw.text((x + shadow, y + shadow), s, font=f, fill=OUTLINE, anchor=anchor)
    draw.text((x, y), s, font=f, fill=color, anchor=anchor)


def text_w(s, size):
    b = font(size).getbbox(s)
    return b[2] - b[0]


def paste(im, x, y, scale=1):
    if scale != 1:
        im = im.resize((im.width * scale, im.height * scale), Image.NEAREST)
    img.alpha_composite(im, (x, y))


def gold_tab(x, y, s, size=16):
    """A menu title: gold text with the dark drop shadow, on a small dark tab."""
    w = text_w(s, size) + 14
    h = size + 6
    panel(x, y, w, h, fill=BG, studs=False)
    text(x + 7, y + h // 2 + 1, s, size, GOLD, shadow=1, anchor="lm")
    return w, h


# ---------------------------------------------------------------- background

rng = random.Random(7)
bands(0, 0, W, H, [hexc("#120d24"), hexc("#1d1638"), hexc("#2c2350"), hexc("#3a2d5a")], steps=5)
for _ in range(140):
    x, y = rng.randrange(W), rng.randrange(int(H * 0.8))
    put(x, y, mix(KEY, hexc("#8fa8ff"), rng.random() * 0.5) if rng.random() < 0.8 else RARE)
for _ in range(9):            # a few bright cross stars
    x, y = rng.randrange(W), rng.randrange(int(H * 0.6))
    for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
        put(x + dx, y + dy, KEY if (dx, dy) == (0, 0) else hexc("#9db0ff"))
# far hills along the bottom, calm and dark
for i in range(W):
    hh = 26 + int(10 * abs(((i * 0.013) % 2) - 1)) + (i * 7 % 13 == 0)
    for j in range(H - hh, H):
        put(i, j, hexc("#1a1430"))
for i in range(W):
    hh = 14 + int(8 * abs(((i * 0.021 + 0.4) % 2) - 1))
    for j in range(H - hh, H):
        put(i, j, hexc("#130f24"))


# ---------------------------------------------------------------- biome scenes

def scene_forest(x, y, w, h):
    bands(x, y, w, h, [hexc("#8fc8f0"), hexc("#d8eef8")], steps=3)
    disc(x + w - 16, y + 12, 6, hexc("#fff2d8"))
    for i in range(w):  # far hills
        t = 34 + int(6 * abs(((i * 0.05) % 2) - 1))
        for j in range(t, h):
            put(x + i, y + j, hexc("#6fae5a"))
    for i in range(w):  # near grass
        t = 48 + int(3 * abs(((i * 0.09 + 0.5) % 2) - 1))
        for j in range(t, h):
            put(x + i, y + j, hexc("#4f9a3c") if (i + j) % 7 else hexc("#5aa846"))
    for i in range(w):  # winding river
        c = int(w * 0.55 + 10 * __import__("math").sin(i * 0.12))
        pass
    for j in range(50, h):
        cx = int(w * 0.45 + (j - 50) * 1.3)
        half = 2 + (j - 50) // 4
        for i in range(cx - half, cx + half):
            if 0 <= i < w:
                put(x + i, y + j, hexc("#4aa8e8") if (i + j) % 5 else hexc("#bfe6ff"))

    def pine(px_, base, hgt, dark, mid):
        put(x + px_, y + base, hexc("#5a3a22"))
        put(x + px_, y + base - 1, hexc("#5a3a22"))
        for k in range(hgt):
            half = (k % (hgt // 3 + 1)) // 2 + k // 4
            yy = base - 2 - (hgt - 1 - k)
            for i in range(-half, half + 1):
                put(x + px_ + i, y + yy, mid if i < 0 else dark)
        put(x + px_, y + base - hgt - 2, dark)

    for px_, base, hg in ((8, 52, 20), (20, 50, 16), (66, 50, 18), (78, 53, 22), (90, 51, 15)):
        pine(px_, base, hg, hexc("#1f5a32"), hexc("#2f7a3e"))
    for mx in (30, 60):  # mushrooms
        put(x + mx, y + 60, KEY)
        for i in (-1, 0, 1):
            put(x + mx + i, y + 59, hexc("#d8382c"))
        put(x + mx, y + 58, hexc("#d8382c"))
    for fx, fy, c in ((14, 64, "#f4a0c8"), (44, 66, "#ffffff"), (72, 63, "#7ab0ff"), (52, 58, "#f4a0c8")):
        put(x + fx, y + fy, hexc(c))


def scene_mountain(x, y, w, h):
    bands(x, y, w, h, [hexc("#a8c4e0"), hexc("#f2b8a0")], steps=4)
    disc(x + 14, y + 40, 5, hexc("#ffe0b0"))
    peaks = [(-6, h), (18, 14, ), (34, h)]
    poly([(-4, h), (22, 12), (48, h)], hexc("#7d8fae"), x, y)
    poly([(30, h), (60, 6), (92, h)], hexc("#6a7c9c"), x, y)
    poly([(22, 12), (16, 20), (20, 19), (24, 22), (28, 18)], KEY, x, y)
    poly([(60, 6), (52, 16), (57, 14), (61, 18), (66, 14), (69, 16)], KEY, x, y)
    for i in range(w):  # shaded right faces
        pass
    poly([(60, 6), (69, 16), (92, h), (74, h)], hexc("#56678a"), x, y)
    poly([(60, 6), (66, 14), (69, 16)], hexc("#c8d8ec"), x, y)
    # pink mist
    for j in range(46, 52):
        for i in range(w):
            if (i + j * 3) % 4:
                put(x + i, y + j, hexc("#e8b8a8", 180))
    for i in range(w):  # olive slopes
        t = 56 + int(5 * abs(((i * 0.07) % 2) - 1))
        for j in range(t, h):
            put(x + i, y + j, hexc("#7c8a44") if (i * 3 + j) % 9 else hexc("#8e9c50"))
    for mx, my, c in ((10, 58, "#d8482c"), (24, 60, "#f08a2c"), (40, 57, "#e8b030"), (70, 59, "#d8482c"), (84, 57, "#f08a2c")):
        disc(x + mx, y + my, 4, hexc(c))
        put(x + mx, y + my + 5, hexc("#4a2c1a"))
        put(x + mx, y + my + 6, hexc("#4a2c1a"))
    for hx in (32, 50, 62):  # heather
        put(x + hx, y + 66, hexc("#a060c0"))
        put(x + hx + 1, y + 65, hexc("#a060c0"))


def scene_frost(x, y, w, h):
    bands(x, y, w, h, [hexc("#3a78d8"), hexc("#bcd8f4")], steps=4)
    # ice spire
    poly([(56, 4), (48, 46), (64, 46)], hexc("#a8e4f8"), x, y)
    poly([(56, 4), (56, 46), (64, 46)], hexc("#6ab8e0"), x, y)
    poly([(42, 22), (38, 46), (46, 46)], hexc("#c8f0ff"), x, y)
    for i in range(w):
        t = 40 + int(6 * abs(((i * 0.045 + 0.3) % 2) - 1))
        for j in range(t, h):
            put(x + i, y + j, hexc("#e8f2fc") if j - t > 2 or i % 3 else KEY)
    for i in range(w):  # blue shadow ripples
        if i % 9 < 5:
            put(x + i, y + 50 + (i // 9) % 2, hexc("#b0c8ec"))
    # frozen lake with cracks
    for j in range(56, 66):
        half = 26 - abs(j - 61) * 3
        for i in range(48 - half, 48 + half):
            put(x + i, y + j, hexc("#8cc4ec") if (i + j) % 11 else hexc("#d8f0ff"))
    for cx, cy in ((40, 60), (41, 61), (42, 61), (43, 62), (56, 58), (57, 59), (58, 59)):
        put(x + cx, y + cy, KEY)

    def snowpine(px_, base, hg):
        for k in range(hg):
            half = k // 3
            yy = base - hg + k
            for i in range(-half, half + 1):
                put(x + px_ + i, y + yy, KEY if k % 4 == 0 or abs(i) == half and k % 2 == 0 else hexc("#1f4a3a"))
        put(x + px_, y + base, hexc("#4a3424"))

    for px_, b, hg in ((8, 50, 18), (18, 48, 14), (80, 49, 17), (90, 50, 12)):
        snowpine(px_, b, hg)
    for sx, sy in ((10, 8), (30, 14), (74, 6), (84, 20), (22, 30), (70, 34), (4, 24)):
        put(x + sx, y + sy, KEY)


def scene_plains(x, y, w, h):
    bands(x, y, w, h, [hexc("#90b8d8"), hexc("#e8d8a8")], steps=4)
    # mesa and stone arch
    rect(x + 58, y + 26, 30, 22, hexc("#c89a68"))
    rect(x + 58, y + 26, 30, 3, hexc("#e0b888"))
    for j in (34, 41):
        rect(x + 58, y + j, 30, 1, hexc("#a87a50"))
    rect(x + 8, y + 30, 6, 18, hexc("#b88a5a"))
    rect(x + 26, y + 30, 6, 18, hexc("#b88a5a"))
    rect(x + 8, y + 26, 24, 6, hexc("#c89a68"))
    rect(x + 8, y + 26, 24, 1, hexc("#e0b888"))
    for i in range(w):  # rolling gold grass
        t = 44 + int(4 * abs(((i * 0.06) % 2) - 1))
        for j in range(t, h):
            put(x + i, y + j, hexc("#d8b048") if (i * 5 + j * 3) % 7 else hexc("#f0d070"))
    for i in range(0, w, 3):  # tall grass blades
        put(x + i, y + 43 + (i % 5 == 0), hexc("#f0d070"))
    # giant titanwood
    rect(x + 40, y + 18, 6, 40, hexc("#7a828c"))
    rect(x + 43, y + 18, 3, 40, hexc("#5a626c"))
    for cx, cy, r in ((43, 14, 12), (33, 18, 8), (54, 17, 9)):
        disc(x + cx, y + cy, r, hexc("#3c6a4a"))
    for cx, cy, r in ((40, 10, 6), (31, 15, 4)):
        disc(x + cx, y + cy, r, hexc("#4f8a5c"))
    for sx, sy in ((20, 60), (70, 62), (84, 56), (10, 66)):  # seeds in the wind
        put(x + sx, y + sy, KEY)


def scene_swamp(x, y, w, h):
    bands(x, y, w, h, [hexc("#5e8a78"), hexc("#7aa898"), hexc("#5e9a80")], steps=3)
    # murky water
    for j in range(46, h):
        for i in range(w):
            put(x + i, y + j, hexc("#2e5a3e") if (i + j * 2) % 13 else hexc("#4a8a52"))
    # runewood: twisted trunk with hanging vines and glowing runes
    for tx in (16, 70):
        rect(x + tx, y + 14, 7, 36, hexc("#3a2c22"))
        rect(x + tx + 5, y + 14, 2, 36, hexc("#2a1e16"))
        for rx, ry in ((2, 22), (3, 30), (2, 38)):
            put(x + tx + rx, y + ry, hexc("#7cf0d8"))
            put(x + tx + rx + 1, y + ry, hexc("#7cf0d8"))
        for cx, r in ((tx + 3, 12), (tx - 6, 7), (tx + 13, 8)):
            disc(x + cx, y + 10, r, hexc("#2f4a2c"))
        for vx in range(tx - 10, tx + 18, 3):
            for vy in range(14, 14 + (vx * 7) % 16):
                put(x + vx, y + vy, hexc("#3e6a34"))
    # roots, lily pads, mushrooms
    for i in range(w):
        if i % 23 < 6:
            put(x + i, y + 47, hexc("#3a2c22"))
    for lx, ly in ((40, 56), (52, 62), (30, 66), (84, 60)):
        rect(x + lx, y + ly, 4, 2, hexc("#6ab04a"))
        put(x + lx + 1, y + ly - 1, hexc("#f080b0") if lx == 52 else hexc("#6ab04a"))
    disc(x + 46, y + 44, 5, hexc("#c84a8a"))
    rect(x + 45, y + 44, 3, 6, hexc("#e8d8c0"))
    for fx, fy in ((34, 30), (58, 22), (50, 36), (86, 40), (6, 38)):  # fireflies
        put(x + fx, y + fy, hexc("#f8f070"))
    for bx, by in ((62, 54), (22, 60)):  # bubbles
        put(x + bx, y + by, hexc("#9ae8a0"))


def scene_void(x, y, w, h):
    bands(x, y, w, h, [hexc("#2a1440"), hexc("#5a2a7a"), hexc("#3a1a58")], steps=4)
    # rift in the sky
    for j in range(4, 20):
        put(x + 70 + (j % 3) - 1, y + j, hexc("#e0a0ff"))
        put(x + 71 + (j % 3) - 1, y + j, hexc("#a050e0"))

    def island(cx, cy, rw, depth):
        for j in range(depth):
            half = rw - j * rw // depth
            for i in range(-half, half + 1):
                put(x + cx + i, y + cy + j, hexc("#1a0e26") if j else hexc("#3e2456"))
        for i in range(-rw, rw + 1, 4):
            put(x + cx + i, y + cy + 1, hexc("#c070ff"))

    island(26, 50, 22, 16)
    island(72, 36, 14, 10)
    island(80, 60, 8, 6)
    # voidstone crystals
    for cx, base, hg in ((20, 50, 18), (28, 50, 12), (74, 36, 14)):
        poly([(cx, base - hg), (cx - 3, base), (cx + 3, base)], hexc("#b060f0"), x, y)
        poly([(cx, base - hg), (cx, base), (cx + 3, base)], hexc("#7030b0"), x, y)
        put(x + cx - 1, y + base - hg + 4, hexc("#f0c8ff"))
    for rx, ry in ((40, 28), (52, 44), (10, 30), (88, 24)):  # floating debris
        rect(x + rx, y + ry, 2, 2, hexc("#1a0e26"))
    for ex, ey in ((34, 40), (46, 20), (60, 58), (14, 22), (84, 48)):  # embers
        put(x + ex, y + ey, hexc("#e090ff"))


def scene_stellar(x, y, w, h):
    bands(x, y, w, h, [hexc("#140c2a"), hexc("#3a2a6a")], steps=4)
    r = random.Random(3)
    for _ in range(40):
        put(x + r.randrange(w), y + r.randrange(h), KEY if r.random() < 0.7 else RARE)
    # galaxy ring
    for i in range(-30, 31):
        yy = int(i * 0.25)
        put(x + 40 + i, y + 18 + yy, mix(hexc("#ffe8a0"), hexc("#a080ff"), abs(i) / 30))
        if abs(i) < 18:
            put(x + 40 + i, y + 17 + yy, hexc("#fff4d0", 160))
    disc(x + 40, y + 18, 3, hexc("#fff4d0"))
    # ringed planet
    disc(x + 76, y + 12, 7, hexc("#e8804a"))
    disc(x + 74, y + 10, 3, hexc("#f8a868"))
    for i in range(-12, 13):
        put(x + 76 + i, y + 13 - i // 5, hexc("#f0e0c0"))
    # floating island with star dust and a stellarite crystal
    for j in range(14):
        half = 26 - j * 2
        for i in range(-half, half + 1):
            put(x + 38 + i, y + 50 + j, hexc("#1c2448") if j else hexc("#e8c860"))
            if j and (i * 7 + j * 3) % 17 == 0:
                put(x + 38 + i, y + 50 + j, KEY)
    poly([(40, 26), (34, 50), (46, 50)], hexc("#fff0b0"), x, y)
    poly([(40, 26), (40, 50), (46, 50)], hexc("#e8c860"), x, y)
    poly([(32, 36), (29, 50), (35, 50)], hexc("#fff8e0"), x, y)
    for ox, oy in ((50, 34), (28, 30), (48, 26)):  # orbiting fragments
        put(x + ox, y + oy, RARE)
    # asteroid stepping stones
    for ax, ay in ((80, 50), (88, 60), (8, 58)):
        rect(x + ax, y + ay, 4, 3, hexc("#2a3460"))


BIOMES = [
    ("FOREST", scene_forest, 14), ("MOUNTAIN", scene_mountain, 12), ("FROST", scene_frost, 14),
    ("PLAINS", scene_plains, 10), ("SWAMP", scene_swamp, 8), ("VOID", scene_void, 6), ("STELLAR", scene_stellar, 12),
]


def render_scene(scene, w, h, crop_x):
    """Draw a scene on its own 96-wide canvas, then crop the part the tile shows."""
    global img, px, draw
    keep = img, px, draw
    img = Image.new("RGBA", (96, h), OUTLINE)
    px, draw = img.load(), ImageDraw.Draw(img)
    scene(0, 0, 96, h)
    out = img.crop((crop_x, 0, crop_x + w, h))
    img, px, draw = keep
    return out


def biome_tile(x, y, w, h, name, scene, crop_x):
    """Small gold title above, framed scene below."""
    tw = text_w(name, 12)
    text(x + w // 2 - tw // 2, y, name, 12, RARE, shadow=1)
    ty = y + 13
    inset = panel(x, ty, w, h, fill=None)
    paste(render_scene(scene, w - 2 * inset, h - 2 * inset, crop_x), x + inset, ty + inset)
    return ty + h


# ---------------------------------------------------------------- right: biomes

RX, RW = 252, 380
RY, RH = 14, 232
panel(RX, RY, RW, RH)
TW, TH, GAP = 84, 86, 8
ix = RX + 10
for n, (name, scene, crop_x) in enumerate(BIOMES):
    row, col = divmod(n, 4)
    if row == 0:
        tx = ix + col * (TW + GAP)
    else:
        tx = ix + (TW + GAP) // 2 + col * (TW + GAP)
    biome_tile(tx, RY + 18 + row * (TH + 17), TW, TH, name, scene, crop_x)
gold_tab(RX + 12, RY - 8, "EXPLORE SEVEN BIOMES", 16)

# ---------------------------------------------------------------- right: features

FY, FH = 258, 96
panel(RX, FY, RW, FH)
gold_tab(RX + 12, FY - 8, "IN THE GAME", 16)


def chat_icon():
    """Two speech bubbles, drawn in the item icon style (48 x 48, dark outline)."""
    ic = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    p = ic.load()

    def bubble(bx, by, bw, bh, fill, tail_left):
        for y in range(bh):
            for x in range(bw):
                c = cut(x, y, bw, bh, 3)
                if c == 0:
                    continue
                edge = c == 1 or x in (0, bw - 1) or y in (0, bh - 1)
                p[bx + x, by + y] = OUTLINE if edge else (lighten(fill, 0.35) if y == 1 or x == 1 else fill)
        tx = bx + (5 if tail_left else bw - 9)
        for k in range(5):
            for i in range(4 - k):
                xx = tx + (i if tail_left else 3 - i) + (0 if tail_left else 0)
                p[xx, by + bh - 1 + k] = fill if 0 < i < 3 - k else OUTLINE
            p[tx + (3 - k if tail_left else k), by + bh - 1 + k] = OUTLINE

    bubble(2, 6, 28, 20, KEY, True)
    for dx in (9, 15, 21):
        for j in range(2):
            for i in range(2):
                p[2 + dx - 1 + i, 6 + 9 + j] = OUTLINE
    bubble(18, 20, 28, 20, hexc("#f0a0c0"), False)
    heart = [".kk.kk.", "kRRkRRk", "kRRRRRk", ".kRRRk.", "..kRk..", "...k..."]
    for j, row in enumerate(heart):
        for i, ch in enumerate(row):
            if ch != ".":
                p[29 + i, 26 + j] = OUTLINE if ch == "k" else hexc("#e03050")
    return ic


FEATURES = [
    ("LEVEL", "UP", Image.open(ITEMS / "prestige_0.png").convert("RGBA")),
    ("MINE", "ORES", Image.open(PICKAXES / "iron_pickaxe.png").convert("RGBA")),
    ("CHOP", "TREES", Image.open(ITEMS / "tool_iron_axe.png").convert("RGBA")),
    ("GO", "FISHING", Image.open(ITEMS / "tool_oak_rod.png").convert("RGBA")),
    ("FIND", "GEMS", Image.open(ITEMS / "gemstone_diamond.png").convert("RGBA")),
    ("MEET", "PLAYERS", chat_icon()),
]
CW = 56
cx0 = RX + 10 + (RW - 20 - (len(FEATURES) * CW + (len(FEATURES) - 1) * 6)) // 2
for n, (a, b, icon) in enumerate(FEATURES):
    cx = cx0 + n * (CW + 6)
    slot(cx + 2, FY + 12, 52, 52)
    paste(icon, cx + 4, FY + 14)
    for k, s in enumerate((a, b)):
        text(cx + CW // 2 - text_w(s, 12) // 2, FY + 64 + k * 11, s, 12, KEY, shadow=1)

# ---------------------------------------------------------------- left: title

LX, LW = 8, 236
tw = text_w("CLUB IMPZ", 48)
text(LX + LW // 2 - tw // 2, 0, "CLUB IMPZ", 48, GOLD, shadow=2)
sub = "A SOCIAL MMO"
text(LX + LW // 2 - text_w(sub, 12) // 2, 48, sub, 12, MUTED, shadow=1)
# COMING DECEMBER! on a raised amber pill
cd = "COMING DECEMBER!"
pw = text_w(cd, 24) + 20
pill(LX + LW // 2 - pw // 2, 64, pw, 30, ENERGY, lip=3)
draw.text((LX + LW // 2, 64 + 13), cd, font=font(24), fill=OUTLINE, anchor="mm")

# ---------------------------------------------------------------- left: heroes


def cut_out(path):
    """Key out the collection's flat purple background by flood fill from the edges."""
    im = Image.open(path).convert("RGBA")
    p = im.load()
    w, h = im.size

    def is_bg(c):
        k = c[2] / 105
        return k > 0.45 and abs(c[0] - 88 * k) < 10 and abs(c[1] - 72 * k) < 10

    seen = set()
    stack = [(x, y) for x in range(w) for y in (0, h - 1)] + [(x, y) for y in range(h) for x in (0, w - 1)]
    while stack:
        x, y = stack.pop()
        if (x, y) in seen or not (0 <= x < w and 0 <= y < h):
            continue
        seen.add((x, y))
        if not is_bg(p[x, y]):
            continue
        p[x, y] = (0, 0, 0, 0)
        stack += [(x + 1, y), (x - 1, y), (x, y + 1), (x, y - 1)]
    return im


def ground(cx, top, half, depth):
    """A small floating grass island for the heroes to stand on."""
    for j in range(depth):
        hw = half - (j * j) // max(depth // 2, 1) if j > 3 else half
        for i in range(-hw, hw + 1):
            if j < 3:
                c = hexc("#6ab04a") if j else hexc("#8ad060")
            else:
                c = hexc("#7a4e30") if (i + j) % 6 else hexc("#5a3820")
            put(cx + i, top + j, c)
        put(cx - hw - 1, top + j, OUTLINE)
        put(cx + hw + 1, top + j, OUTLINE)


ground(LX + LW // 2, 330, 108, 22)
left = cut_out(BODIES / "body_gold_408.png")
right = cut_out(BODIES / "body_diamond_158.png")
hero = cut_out(BODIES / "body_cyan_111.png")
paste(left, LX - 8, 330 - 134, 2)
paste(right, LX + LW - 120, 330 - 134, 2)
paste(hero, LX + LW // 2 - 96, 330 - 186, 3)

# ---------------------------------------------------------------- save

OUT.parent.mkdir(parents=True, exist_ok=True)
img.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST).save(OUT)
print("saved", OUT)
