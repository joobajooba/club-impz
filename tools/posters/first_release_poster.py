"""First release poster: "Club Impz, coming December".

Follows docs/posters.md: drawn on a 640 x 360 art canvas in the menu look
(ui_kit.gd colours, gold bevelled frames, Pixelify Sans), then scaled x3 with
nearest-neighbour to 1920 x 1080.

    python tools/posters/first_release_poster.py         # 2D pixel Impz (the collection art)
    python tools/posters/first_release_poster.py --3d    # 3D Impz (Blockbench renders)

Writes docs/images/posters/first_release_poster.png, or first_release_poster_3d.png with --3d.
The 3D renders come from tools/posters/render_impz.gd.
"""
from pathlib import Path
import random
import sys

from PIL import Image, ImageDraw, ImageFont

ROOT = Path(__file__).resolve().parents[2]
HEROES_3D = "--3d" in sys.argv
OUT = ROOT / ("docs/images/posters/first_release_poster_3d.png" if HEROES_3D else "docs/images/posters/first_release_poster.png")
RENDERS = ROOT / "docs/images/posters/first_release_impz_3d"
FONT = ROOT / "godot-game/ui/fonts/PixelifySans.ttf"
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


def font(size, bold=False):
    f = ImageFont.truetype(str(FONT), size)
    if bold:
        f.set_variation_by_name("Bold")   # Pixelify Sans is a variable font, 400 to 700
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


def text(x, y, s, size, color, shadow=2, anchor="la", bold=False):
    f = font(size, bold)
    if shadow:
        draw.text((x + shadow, y + shadow), s, font=f, fill=OUTLINE, anchor=anchor)
    draw.text((x, y), s, font=f, fill=color, anchor=anchor)


def text_w(s, size, bold=False):
    b = font(size, bold).getbbox(s)
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


# ---------------------------------------------------------------- right: places

# Real in-game screenshots (window runs of the game at 1920 x 1080, cropped to the
# clear middle between the HUD and the chat panel, 612 x 456). Taken with:
#   godot --path godot-game --resolution 1920x1080 -- --world=wilds_forest --shot=<png> --shot_delay=20
# (--world=hub for the hub town). Void and Stellar are not built yet, so they are not on the poster.
PLACES = [("HUB TOWN", "hub"), ("FOREST", "forest"), ("MOUNTAIN", "mountain"),
          ("FROST", "frost"), ("PLAINS", "plains"), ("SWAMP", "swamp")]
shot_slots = []          # (art x, art y, art w, art h, file): pasted at full size after the x3 scale


def place_tile(x, y, w, h, name, shot):
    """Small gold title above, gold frame below; the screenshot goes inside the frame."""
    tw = text_w(name, 12)
    text(x + w // 2 - tw // 2, y, name, 12, RARE, shadow=1)
    ty = y + 13
    inset = panel(x, ty, w, h, fill=None)
    shot_slots.append((x + inset, ty + inset, w - 2 * inset, h - 2 * inset, SHOTS / f"{shot}.png"))


RX, RW = 252, 380
RY, RH = 14, 232
panel(RX, RY, RW, RH)
TW, TH, GAP = 114, 88, 9
for n, (name, shot) in enumerate(PLACES):
    row, col = divmod(n, 3)
    place_tile(RX + 10 + col * (TW + GAP), RY + 18 + row * (TH + 16), TW, TH, name, shot)
gold_tab(RX + 12, RY - 8, "EXPLORE THE WORLD", 16)

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
tw = text_w("CLUB IMPZ", 48, bold=True)
text(LX + LW // 2 - tw // 2, 0, "CLUB IMPZ", 48, GOLD, shadow=2, bold=True)
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


hero_slots = []          # 3D renders: (file, art x, art y, art size), pasted at full size after the x3 scale
if HEROES_3D:
    hero_slots += [(RENDERS / "gold_408.png", LX - 20, 188, 140),
                   (RENDERS / "diamond_158.png", LX + LW - 124, 188, 140),
                   (RENDERS / "cyan_111.png", LX + LW // 2 - 92, 168, 176)]
else:
    paste(cut_out(BODIES / "body_gold_408.png"), LX - 8, 330 - 134, 2)
    paste(cut_out(BODIES / "body_diamond_158.png"), LX + LW - 120, 330 - 134, 2)
    paste(cut_out(BODIES / "body_cyan_111.png"), LX + LW // 2 - 96, 330 - 186, 3)

# ---------------------------------------------------------------- save

OUT.parent.mkdir(parents=True, exist_ok=True)
big = img.convert("RGB").resize((W * SCALE, H * SCALE), Image.NEAREST)
for x, y, w, h, f in shot_slots:      # the screenshots stay sharp: full screen resolution, not art pixels
    big.paste(Image.open(f).convert("RGB").resize((w * SCALE, h * SCALE), Image.LANCZOS), (x * SCALE, y * SCALE))
for f, x, y, size in hero_slots:
    r = Image.open(f).convert("RGBA").resize((size * SCALE, size * SCALE), Image.LANCZOS)
    big.paste(r, (x * SCALE, y * SCALE), r)
tmp = OUT.with_name(OUT.stem + ".tmp.png")
big.save(tmp)
tmp.replace(OUT)
print("saved", OUT)
