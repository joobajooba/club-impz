"""Build the bows (16 tiers, one per animal) and the fishing rods (10 tiers, one per wood) as
Blockbench models (Generic Model), at the pickaxe standard (D-114, D-115): each tier its own
shape and detail.

Bows are made from leather (D-069). Each one carries **its animal's trophy** as decoration,
drawn from the trophy icon in sprites/items/ (trophy_*.png):

   1 Hare               a lucky-foot charm on a gold ring
   2 Fox                a brush-tail tassel, white-tipped limbs
   3 Boar               ivory tusks curving off the tips
   4 Wolf               a fang on a cord, silver nocks
   5 Goldhorn Stag      golden antler tines branching off the limbs, sparkles
   6 Shadowcat          claw-hooked tips, dark stripes
   7 Frostmane Yeti     a frozen heart on the grip, frost tufts
   8 Cinder Salamander  an ember scale with glowing cracks, glowing tips, embers
   9 Voidstalker        a void eye on the grip, drifting orbs
  10 Starwyrm           star horns on the tips, stars
  11 Stormhorn Ram      curled ram horns on the tips, a lightning zigzag
  12 Tidecrest Serpent  an abyss pearl in its shell, wave fins
  13 Mossmane Behemoth  moss strands, a flower on the grip
  14 Crystalback Basilisk  prism crystals along the limbs
  15 Sunfeather Griffin feathers fanning off the tips, sparkles
  16 Eclipse Dragon     an eclipse crown on the grip, recurved tips, motes

Rods are made from planks (D-110), so each is themed on its wood, with the marks the log
icons carry (D-105): Driftwood crooked with knots and twine; Ash plain; Birch black bark
marks; Oak dark grain; Pine resin drops; Goldleaf sparkles; Ebony a purple glint;
Silverbark frost and a crystal tip; Bloodwood dark spots and a glowing drop; Voidwood a
glowing spiral and drifting fragments.

Colours: each bow's limbs and each rod's shaft come from its own tool icon (every colour
the icon doesn't share with the other bows or rods, sorted by brightness); the grip,
string, cork and reel from the colours the icons share; trophy and mark colours from the
trophy and log icons.

Layout matches ToolArt in the game: a bow is centred on its grip, string along Y at x=0,
limbs bulging towards +X; a rod stands on its butt with the tip about 2.2 m up.

Usage: python build_bow_rod_bbmodel.py <out_dir>
"""

import math
import sys
from pathlib import Path

from PIL import Image

from build_pickaxe_bbmodel import hexrgb
from build_pickaxe_metal_bbmodel import box
from bbsprite import sprite_cells, write_lineup, write_model

ICONS = Path(__file__).resolve().parents[4] / "sprites" / "source" / "items"   # godot-game/assets/sprites/source/items


def ramp(*hexes):
    return [hexrgb(h) for h in hexes]


def lum(c):
    return 0.2126 * c[0] + 0.7152 * c[1] + 0.0722 * c[2]


def icon_colours(path, min_count=3):
    counts = {}
    for c in Image.open(path).convert("RGBA").getdata():
        if c[3] > 200 and lum(c) > 18:
            counts[c[:3] + (255,)] = counts.get(c[:3] + (255,), 0) + 1
    return {c for c, n in counts.items() if n >= min_count}


def own_ramp(path, shared, size=5):
    """The colours of an icon that the other icons of its kind don't have, darkest first."""
    cols = sorted(icon_colours(path) - shared, key=lum)
    if len(cols) > size:
        cols = [cols[round(i * (len(cols) - 1) / (size - 1))] for i in range(size)]
    while len(cols) < size:
        cols.append(cols[-1])
    return cols


def floats(points):
    return [box(f"float_{i + 1}", "float", (c, c), (r, r + 1), 1, z=z)
            for i, (c, r, z) in enumerate(points)]


# ---------------------------------------------------------------- bows

ANIMALS = ["hare", "fox", "boar", "wolf", "goldhorn_stag", "shadowcat", "frostmane_yeti",
           "cinder_salamander", "voidstalker", "starwyrm", "stormhorn_ram", "tidecrest_serpent",
           "mossmane_behemoth", "crystalback_basilisk", "sunfeather_griffin", "eclipse_dragon"]

# Trophy colours, darkest first, and the accent (glow, sparkle or highlight), all picked
# from that animal's trophy icon.
TROPHY = {
    "hare": (ramp("5e3c22", "8a5e3a", "b08460", "d4ae8a"), "ffd040"),            # lucky foot
    "fox": (ramp("94360e", "c85a1a", "e8843a", "f8b070"), "fff6e8"),             # brush tail
    "boar": (ramp("9a8670", "c4b298", "e2d4bc", "fff4e0"), "fff4e0"),            # boar tusk
    "wolf": (ramp("6a5a48", "9a8670", "c4b298", "e2d4bc"), "b8bac0"),            # wolf fang
    "goldhorn_stag": (ramp("8a4a06", "c87a0a", "f0a818", "ffd040"), "fff28a"),   # golden antler
    "shadowcat": (ramp("36205a", "4e3480", "7a48c8", "a070e8"), "c8a0ff"),       # shadow claw
    "frostmane_yeti": (ramp("7c88c0", "aab4e6", "d4dcff", "ffffff"), "6cc4e0"),  # frozen heart
    "cinder_salamander": (ramp("7a1218", "ac1e22", "d83a30", "f2705a"), "ffe070"),  # ember scale
    "voidstalker": (ramp("3e2860", "5a2aa0", "7a48c8", "a070e8"), "c8a0ff"),     # void eye
    "starwyrm": (ramp("14224e", "1e3674", "2c4e9a", "4a72c4"), "ffd84a"),        # star horn
    "stormhorn_ram": (ramp("323a44", "4a5666", "687888", "90a0b0"), "fff490"),   # thunder curl
    "tidecrest_serpent": (ramp("0c4a50", "167078", "2a9aa0", "5ccac8"), "e0f6f4"),  # abyss pearl
    "mossmane_behemoth": (ramp("14582c", "1e7a3c", "2ea050", "5cd070"), "ffd040"),  # verdant mane
    "crystalback_basilisk": (ramp("7a1460", "b0228a", "e04cb8", "ff90e0"), "ff90e0"),  # prism shard
    "sunfeather_griffin": (ramp("c09a48", "e6c878", "f8e8b8", "ffffff"), "ffd040"),  # sun feather
    "eclipse_dragon": (ramp("8a4a06", "c87a0a", "f0a818", "ffd040"), "ffffff"),  # eclipse crown
}

GRIP = (5, 7)          # columns of the leather grip
GRIP_ROWS = (-3, 3)


def limb_edge(y):
    """Outer column of the limb at row y: a bow bulging to column 7 at the grip."""
    return round(6 * math.cos(math.pi * y / 40)) + 1


def bow_cells():
    cells = {}
    for y in range(-20, 21):
        xo = limb_edge(y)
        t = 3 if abs(y) <= 6 else 2 if abs(y) <= 14 else 1
        for x in range(xo - t + 1, xo + 1):
            if not (GRIP[0] <= x <= GRIP[1] and GRIP_ROWS[0] <= y < GRIP_ROWS[1]):
                cells[(x, y)] = "#" if abs(y) <= 9 else "+"
    for y in range(-19, 20):
        cells.setdefault((0, y), "w")  # the string
    return cells


def bow_design(key, c):
    """Add the animal's trophy to the base bow. Returns floating pieces."""
    def put(points, ch, mirror=False):
        for x, y in points:
            c[(x, y)] = ch
            if mirror:
                c[(x, -y)] = ch

    def tips(ch, rows=2):
        for (x, y), v in list(c.items()):
            if v != "w" and abs(y) > 20 - rows:
                c[(x, y)] = ch

    def stripe(points, mirror=True):
        for x, y in points:
            for yy in ((y, -y) if mirror else (y,)):
                if (x, yy) in c:
                    c[(x, yy)] = "," if c[(x, yy)] == "+" else "0"

    fl = []
    if key == "hare":
        put([(8, -3), (8, -4)], "E")
        put([(8, -5), (8, -7)], "C")
        put([(9, -5), (9, -7), (8, -8)], "B")
        put([(8, -6)], "D")
        put([(9, -6)], "C")
        put([(9, -8), (8, -9)], "A")
    elif key == "fox":
        tips("E", 3)
        put([(8, -3)], "B")
        put([(8, -4), (9, -5)], "C")
        put([(9, -6), (10, -7)], "D")
        put([(10, -8), (11, -9)], "E")
    elif key == "boar":
        put([(0, 21), (0, 22)], "C", mirror=True)
        put([(1, 23), (2, 23)], "D", mirror=True)
        put([(3, 22)], "E", mirror=True)
        stripe([(limb_edge(y), y) for y in (7, 12)])
    elif key == "wolf":
        tips("E")
        put([(8, -3), (8, -4)], ";")
        put([(8, -5), (8, -6)], "D")
        put([(9, -5), (9, -6)], "C")
        put([(8, -7)], "C")
        put([(8, -8)], "B")
    elif key == "goldhorn_stag":
        for y in (9, 14):
            x = limb_edge(y)
            put([(x + 1, y + 1)], "C", mirror=False)
            put([(x + 2, y + 2)], "D")
            put([(x + 2, y + 3)], "E")
            put([(x + 1, -y - 1)], "C")
            put([(x + 2, -y - 2)], "D")
            put([(x + 2, -y - 3)], "E")
        fl = [(10, 15, 0), (10, -13, 1), (3, 18, -1)]
    elif key == "shadowcat":
        put([(2, 20)], "C", mirror=True)
        put([(3, 19)], "D", mirror=True)
        put([(3, 18)], "E", mirror=True)
        stripe([(limb_edge(y), y) for y in (5, 8, 11, 14)])
    elif key == "frostmane_yeti":
        put([(8, 1), (10, 1), (10, 0)], "C")
        put([(8, 0)], "D")
        put([(9, 0)], "E")
        put([(9, -1)], "B")
        for y in (8, 12, 16):
            put([(limb_edge(y) + 1, y)], "D", mirror=True)
    elif key == "cinder_salamander":
        put([(8, 1), (8, -1), (9, 0)], "C")
        put([(8, -2), (9, -1)], "B")
        put([(8, 0), (9, 1)], "E")
        tips("E", 2)
        fl = [(9, 8, 0), (10, 4, 1), (8, -10, -1), (4, 16, 0)]
    elif key == "voidstalker":
        put([(8, 1), (10, 1), (8, -1), (10, -1)], "B")
        put([(9, 1), (8, 0), (10, 0), (9, -1)], "C")
        put([(9, 0)], "E")
        fl = [(11, 6, 0), (10, -7, 1), (4, 15, -1)]
    elif key == "starwyrm":
        put([(1, 21)], "B", mirror=True)
        put([(2, 22)], "C", mirror=True)
        put([(2, 23)], "D", mirror=True)
        put([(3, 24)], "E", mirror=True)
        put([(limb_edge(6), 6), (limb_edge(-11), -11)], "e")
        fl = [(9, 12, 0), (9, -10, 1), (5, 17, -1)]
    elif key == "stormhorn_ram":
        put([(1, 21), (3, 19)], "B", mirror=True)
        put([(2, 22), (3, 22), (4, 20)], "C", mirror=True)
        put([(4, 21)], "D", mirror=True)
        put([(8, 4), (9, 5), (8, 6), (9, 7)], "E")
    elif key == "tidecrest_serpent":
        put([(8, 1), (8, 0), (8, -1), (10, 1), (10, -1)], "B")
        put([(9, 1), (9, -1), (10, 0)], "C")
        put([(9, 0)], "E")
        for y in (8, 11, 14):
            put([(limb_edge(y) + 1, y)], "C", mirror=True)
    elif key == "mossmane_behemoth":
        for y in (6, 10, -7, -11):
            x = limb_edge(y) + 1
            put([(x, y)], "B")
            put([(x, y - 1)], "C")
            put([(x, y - 2)], "B")
        put([(8, 0)], "E")
    elif key == "crystalback_basilisk":
        for y in (5, 9, 13):
            x = limb_edge(y)
            put([(x + 1, y)], "C", mirror=True)
            put([(x + 2, y)], "D", mirror=True)
    elif key == "sunfeather_griffin":
        put([(1, 21), (2, 21)], "C", mirror=True)
        put([(2, 22), (3, 22)], "D", mirror=True)
        put([(3, 23)], "E", mirror=True)
        fl = [(8, 13, 0), (9, -12, 1), (4, 21, -1)]
    elif key == "eclipse_dragon":
        put([(8, 2), (8, 1), (8, 0), (8, -1), (8, -2)], "B")
        put([(9, 2), (9, -2)], "D")
        put([(9, 0)], "E")
        put([(2, 20), (3, 21)], "+", mirror=True)  # recurved tips
        fl = [(10, 6, 0), (10, -6, 1)]
    return fl


def bow_palette(key, shared):
    tro, accent = TROPHY[key]
    return dict(label=key.replace("_", " ").title(),
                metal=own_ramp(ICONS / f"tool_{key}_bow.png", shared),
                gem=tro, accent=hexrgb(accent), float_shade=tro[2],
                cord=ramp("3e2a2d", "573c30", "6b4a2c", "947a5c"),  # the grip, from the icons
                string=hexrgb("e8e0cc"),
                # Unused by bows, but the shared painters expect them.
                wood=ramp("3e2a2d", "573c30", "6b4a2c", "947a5c", "bcab93"),
                socket=(1, GRIP_ROWS))


def bow_boxes(key):
    cells = bow_cells()
    fl = bow_design(key, cells)
    boxes = [box("grip", "cord", GRIP, GRIP_ROWS, 5, group="handle")]
    boxes += sprite_cells("bow", cells)
    boxes += floats(fl)
    return boxes


# ---------------------------------------------------------------- rods

WOODS = ["driftwood", "ash", "birch", "oak", "pine", "goldleaf", "ebony", "silverbark",
         "bloodwood", "voidwood"]

# Mark colour per wood, from its log icon (Driftwood has none: no tree).
MARK = {"driftwood": "e3dac6", "ash": "f6e8c4", "birch": "261f29", "oak": "3a2614",
        "pine": "e2c286", "goldleaf": "fff08a", "ebony": "705884", "silverbark": "f4f0ff",
        "bloodwood": "e05c4c", "voidwood": "7a48c8"}

GRIP_TOP = 13   # the cork grip, rows 0-12
TIP = 70        # the top row: 2.19 m, where the game ties the line (gatherer.gd: 2.2 m)
GUIDES = (30, 42, 53, 62)


def rod_cells(key):
    c = {}
    for y in range(GRIP_TOP, 23):
        for x in (-1, 0, 1):
            c[(x, y)] = "#"   # the butt section, 3 x 3
    for y in range(23, TIP):
        x = 1 if key == "driftwood" and 38 <= y < 50 else 0   # driftwood is crooked
        c[(x, y)] = "+"
        if key == "driftwood" and y in (38, 49):
            c[(1 - x, y)] = "+"   # join the bend
    shaft = {y: x for (x, y) in c if y >= 23}
    for y in GUIDES:
        x = shaft[y]
        c[(x + 1, y)] = "C"           # line guide
        for yy in (y - 1, y + 1):
            c[(x, yy)] = ";"          # thread wraps
    c[(shaft[TIP - 1], TIP)] = "D"    # tip guide
    # The reel, on the +X side above the grip, and its crank.
    for (x, y), ch in {(2, 11): "b", (3, 11): "c", (2, 10): "c", (3, 10): "d", (2, 9): "b",
                       (3, 9): "c", (4, 10): "C"}.items():
        c[(x, y)] = ch

    def at(rows, ch, dx=0):
        for y in rows:
            c[(shaft.get(y, 0) + dx, y)] = ch

    fl = []
    if key == "driftwood":
        at([28, 45], "1")             # knots
        at([26, 36, 56], ",")
    elif key == "birch":
        at([26, 31, 37, 44, 50, 57, 65], ",")
        c[(-1, 16)] = c[(1, 19)] = "0"
    elif key == "oak":
        at([27, 35, 47, 58], ";")
        c[(1, 15)] = c[(-1, 20)] = "1"
    elif key == "pine":
        at([33, 48], "E")             # resin drops
        c[(-1, 18)] = "e"
    elif key == "goldleaf":
        at([29, 41, 58], "E")         # sparkles
        c[(1, 15)] = "e"
        fl = [(2, 66, 0), (-2, 60, 1)]
    elif key == "ebony":
        at([27, 38, 49, 60], "E")     # purple glint
        c[(-1, 17)] = "e"
    elif key == "silverbark":
        at([25, 36, 46, 57, 66], "E")  # frost
        c[(0, TIP + 1)] = "D"          # a crystal tip
        c[(0, TIP)] = "C"
    elif key == "bloodwood":
        at([26, 34, 45, 51, 64], ",")  # dark spots
        c[(1, 18)] = "e"               # a glowing drop
        c[(-1, 15)] = "0"
    elif key == "voidwood":
        for i, y in enumerate(range(13, 23)):
            c[((i % 4) - 1 if i % 4 < 3 else 0, y)] = "e"   # a spiral round the butt
        at([33, 47, 61], "E")
        fl = [(2, 67, 0), (-2, 63, 1), (2, 58, -1)]
    return c, fl


def rod_palette(key, shared):
    return dict(label=key.title(),
                metal=own_ramp(ICONS / f"tool_{key}_rod.png", shared),
                wood=ramp("cac0ac", "d8d0c0", "e3dac6", "e8e0cc", "f6f2ec"),  # cork
                grain=False,
                gem=ramp("545165", "6f6670", "9aa0a8", "b6b8b5"),           # reel, guides
                accent=hexrgb(MARK[key]), float_shade=hexrgb(MARK[key]),
                socket=(1, (GRIP_TOP, GRIP_TOP)))


def rod_boxes(key):
    cells, fl = rod_cells(key)
    boxes = [box("grip", "wood", (-1, 1), (0, GRIP_TOP), 3, group="handle")]
    boxes += sprite_cells("rod", cells)
    boxes += floats(fl)
    return boxes


# ---------------------------------------------------------------- build

def shared_colours(paths):
    sets = [icon_colours(p) for p in paths]
    return set.intersection(*sets)


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    shared = shared_colours([ICONS / f"tool_{a}_bow.png" for a in ANIMALS])
    sets = []
    for key in ANIMALS:
        name = f"bow_{key}"
        sets.append((name, *write_model(out_dir, name, bow_palette(key, shared), bow_boxes(key),
                                        head_origin=0, handle_origin=0)))
    write_lineup(out_dir, "bows_lineup", sets, spacing=16)

    shared = shared_colours([ICONS / f"tool_{w}_rod.png" for w in WOODS])
    sets = []
    for key in WOODS:
        name = f"rod_{key}"
        sets.append((name, *write_model(out_dir, name, rod_palette(key, shared), rod_boxes(key),
                                        head_origin=GRIP_TOP, handle_origin=6)))
    write_lineup(out_dir, "rods_lineup", sets, spacing=8)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
