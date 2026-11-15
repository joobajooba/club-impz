"""Build the axes and sickles (Generic Model), one model and texture per tier, Stone to
Stellarite.

They follow the pickaxes (D-114, and the same rules: docs/MODELS-BLOCKBENCH.md): each tier
has its own shape and detail, themed on its metal and gem. Every tool of a tier shares the
pickaxe's palette and its socket "badge" (rivets, a gem, the Dreadstone demon, the Void
spiral, the Stellarite orb), so a tier reads the same across tools. Stone tools are a rock
head lashed on with cord, like the Stone pickaxe.

  Axe       Stone rough wedge; Bronze dented; Iron plain with a poll; Steel bearded with a
            back spike; Gold double-bit with a crown; Obsidian knapped edge; Titanite
            faceted diamond blade with crystals; Dreadstone barbed with horns and a hooked
            spike; Void a glowing rift and floating fragments; Stellarite a crescent moon
            with stars and a floating star.
  Sickle    Stone a thick rough hook; Bronze dented; Iron plain; Steel toothed with a
            groove; Gold a curled tip; Obsidian a chipped spine; Titanite a light facet and a
            crystal shard; Dreadstone barbs, a painite eye and the demon guard; Void a
            glowing rift; Stellarite a longer, star-strewn crescent.

Colours: the tier palettes picked from the pickaxe icons (build_pickaxe_metal_bbmodel.py)
and the gemstone icons; the sickle and axe icons in sprites/items/ use the same colours.
Handles follow the hilt (D-058).

Heads are pixel sprites (bbsprite.py): see its legend. Columns run in x from the handle's
centre, rows in y from the bottom of the handle; each axe drawing lists its top row first.
Sickle blades are generated from two circles, then edited per tier.

Usage: python build_axe_sickle_bbmodel.py <out_dir>
"""

import copy
import math
import sys
from pathlib import Path

from build_pickaxe_bbmodel import CORD, FLECK, STONE, WOOD
from build_pickaxe_metal_bbmodel import TIERS as PICKAXES, box
from bbsprite import sprite, sprite_cells, write_lineup, write_model

ORDER = ["stone", "bronze", "iron", "steel", "gold", "obsidian", "titanite",
         "dreadstone", "void", "stellarite"]

STONE_TIER = dict(label="Stone", metal=STONE, gem=FLECK[:4], wood=WOOD, cord=CORD)


def palette(key):
    if key == "stone":
        return dict(STONE_TIER)
    t = PICKAXES[key]
    return {k: t[k] for k in ("label", "metal", "wood", "gem", "accent", "float_shade",
                              "grain", "face", "field") if k in t}


def socket_size(key):
    """(half width, height) of the tier's socket, as on its pickaxe. Stone: the lashing."""
    if key == "stone":
        return 2, 8
    hw, (s0, s1) = PICKAXES[key]["socket"]
    return hw, s1 - s0


def top_extras(key, s1):
    """The socket-top pieces of the tier's pickaxe (crown, crystals, horns, star, spike),
    moved to sit on this socket."""
    t = PICKAXES.get(key, {})
    dy = s1 - t.get("socket", (0, (s1, s1)))[1][1]
    keep = ("crown", "crystal", "horn", "star_v", "star_l", "star_r", "spike")
    out = []
    for e in t.get("extras", []):
        if not e["name"].startswith(keep):
            continue
        e = copy.deepcopy(e)
        e["lo"][1] += dy
        e["hi"][1] += dy
        out.append(e)
        if e.get("mirrored"):
            m = copy.deepcopy(e)
            m["name"] += "_l"
            m["lo"][0], m["hi"][0] = -e["hi"][0], -e["lo"][0]
            out.append(m)
    return out


def flip(rows):
    return [r[::-1] for r in rows]


def floats(points):
    """Loose 1-pixel pieces: (column, row, z)."""
    return [box(f"float_{i + 1}", "float", (c, c), (r, r + 1), 1, z=z)
            for i, (c, r, z) in enumerate(points)]


# ---------------------------------------------------------------- axes
# Head drawings sit right of the socket, the neck centred on it. The poll (back of the head)
# sits left of it.

AXE = {}

AXE["stone"] = dict(blade=[
    "...####.",
    "..######",
    ".#######",
    "########",
    "##b#####",
    "#####c##",
    "########",
    "########",
    ".###b###",
    "..######",
    "...###..",
], top=29)

AXE["bronze"] = dict(blade=[
    ".......++.",
    ".....##++.",
    "....###++:",
    "...##1#++:",
    "#######++:",
    "##1####++:",
    "#####1#++:",
    "#######++:",
    "###1###++:",
    "...####++:",
    "....##1++:",
    ".....##++.",
    ".......++.",
], poll=["#", "#", "#", "#", "#"])

AXE["iron"] = dict(blade=[
    ".......++.",
    ".....##++.",
    "....###++:",
    "...####++:",
    "#######++:",
    "#######++:",
    "#######++:",
    "#######++:",
    "#######++:",
    "...####++:",
    "....###++:",
    ".....##++.",
    ".......++.",
], poll=["#", "#", "#", "#", "#"])

# Bearded: the blade runs down along the handle. A spike on the back.
AXE["steel"] = dict(blade=[
    ".......++.",
    "......#++.",
    ".....##++:",
    "....###++:",
    "#######++:",
    "#######++:",
    "#11111#++:",
    "#######++:",
    "#######++:",
    "...####++:",
    "....###++:",
    "....###++:",
    ".....##++:",
    ".....##++:",
    "......#++:",
    ".......++:",
    "........+.",
], poll=["..+##", "++###", "..+##"], poll_top=25)

# Double-bit: a scalloped blade on both sides.
GOLD_AXE = [
    ".......++.",
    ".....##++:",
    "....###++.",
    "...####++:",
    "#######++:",
    "#######++.",
    "#######++:",
    "#######++:",
    "#######++.",
    "...####++:",
    "....###++.",
    ".....##++:",
    ".......++.",
]
AXE["gold"] = dict(blade=GOLD_AXE, poll=flip(GOLD_AXE))

# Knapped glass: a chipped edge and glassy streaks.
AXE["obsidian"] = dict(blade=[
    "......+.+.",
    ".....##++.",
    "....###+:.",
    "...##3#++:",
    "####3##++.",
    "###3###+:+",
    "#######++.",
    "##3####++:",
    "#3#####+:.",
    "...##3#++:",
    "....###++.",
    ".....#+++.",
    "......+.+.",
], poll=["#", "#", "#", "#", "#"])

# A faceted diamond-shaped blade, a light facet line above and a dark one below.
AXE["titanite"] = dict(blade=[
    ".........+",
    "........++",
    ".......#++",
    "......##++",
    ".....#4#++",
    "####4###++",
    "###4####++",
    "##4#####++",
    "#1######++",
    "##1#####++",
    ".....1##++",
    "......1#++",
    ".......#++",
    "........++",
    ".........+",
], top=31, poll=["#", "#", "#", "#", "#"])

# Barbed corners that hook back, and a hooked spike on the back.
AXE["dreadstone"] = dict(blade=[
    "....+.....",
    "....##....",
    ".....###+.",
    "......##+:",
    "....####+:",
    "########+:",
    "########+:",
    "##0#0###+:",
    "########+:",
    "########+:",
    "....####+:",
    "......##+:",
    ".....###+.",
    "....##....",
    "....+.....",
], top=32, poll=["+......", ".###...", "...###."], poll_top=27)

# A rift through the blade with a glowing rim, and fragments drifting off the edge.
AXE["void"] = dict(blade=[
    ".......++.",
    ".....##++.",
    "....###++E",
    "...##e#++:",
    "####e.e++:",
    "###e..e++:",
    "####e.e++:",
    "#####e#++:",
    "#######++:",
    "...####++:",
    "....###++E",
    ".....##++.",
    ".......++.",
], poll=["#", "#", "#", "#", "#"], floats=[(16, 27, 0), (17, 22, 1), (15, 31, 0)])

# A crescent moon whose points curl back, strewn with stars.
AXE["stellarite"] = dict(blade=[
    "....++....",
    ".....###..",
    "......###.",
    ".......##+",
    "....####++",
    "#######e++",
    "########++",
    "##e#####++",
    "########++",
    "#####e##++",
    "....####++",
    ".......##+",
    "......###.",
    ".....###..",
    "....++....",
], top=31, poll=["#", "#", "#", "#", "#"], floats=[(16, 29, 1), (-7, 21, -1)])


def axe_boxes(key):
    hw, h = socket_size(key)
    s0 = 21
    s1 = s0 + h
    d = AXE[key]
    has_top = any(e["name"].startswith(("crown", "crystal", "star", "spike"))
                  for e in top_extras(key, s1))
    handle_top = s1 - 1 if has_top else s1 + 2
    boxes = [box("handle", "wood", (-1, 1), (0, handle_top), 3, group="handle")]
    if key == "stone":
        boxes.append(box("binding", "cord", (-2, 2), (s0, s1), 5))
    else:
        boxes.append(box("socket", "socket", (-hw, hw), (s0, s1), 5))
    shift = (h - 7) // 2
    boxes += sprite("blade", hw + 1, d.get("top", 30) + shift, d["blade"])
    poll = d.get("poll")
    if poll:
        width = max(len(r) for r in poll)
        # A small poll centres on the neck; a second blade lines up with the first.
        default = d.get("top", 30) if len(poll) > 5 else 26
        boxes += sprite("poll", -hw - width, d.get("poll_top", default) + shift, poll)
    boxes += top_extras(key, s1)
    boxes += floats(d.get("floats", []))
    return boxes, (s0, s1)


# ---------------------------------------------------------------- sickles
# The blade is a crescent: the ring between two circles, its left side standing on the
# ferrule as a tang and its right side cut off in a point. It is one pixel thick, like the
# reference tool heads, with a light sharpened inner edge and a 3-deep tang. Each tier then
# edits pixels of that base.

OUTER = (8.0, 25.0, 10.6)   # centre column, centre row, radius (for a ferrule top at row 19)
INNER = (10.6, 23.4, 8.2)


def crescent(neck, tip_cut=27):
    """The base blade for a ferrule whose top is row `neck`."""
    dy = neck - 19
    (ox, oy, r), (ix, iy, ri) = OUTER, INNER
    oy, iy = oy + dy, iy + dy

    def in_inner(x, y):
        return (x - ix) ** 2 + (y - iy) ** 2 <= ri * ri

    cells = {}
    for y in range(neck, neck + 18):
        for x in range(-4, 20):
            if (x - ox) ** 2 + (y - oy) ** 2 > r * r or in_inner(x, y):
                continue
            if x > 8 and y < tip_cut + dy:
                continue
            cells[(x, y)] = "+"
    for (x, y) in list(cells):
        if any((x + a, y + b) not in cells and in_inner(x + a, y + b)
               for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1))):
            cells[(x, y)] = ":"  # the sharpened inside edge
        if -2 <= x <= 2 and y < neck + 6:
            cells[(x, y)] = "#"  # the tang
    return cells


def outer_edge(cells, neck):
    """Spine pixels on the outside of the curve, left to right over the top."""
    ox, oy, r = OUTER[0], OUTER[1] + neck - 19, OUTER[2]
    edge = [(x, y) for (x, y) in cells
            if y >= neck + 6 and any((x + a, y + b) not in cells
                                     and (x + a - ox) ** 2 + (y + b - oy) ** 2 > r * r
                                     for a, b in ((1, 0), (-1, 0), (0, 1), (0, -1)))]
    return sorted(edge, key=lambda c: -math.atan2(c[1] - oy, c[0] - ox))


def sickle_cells(key, neck):
    c = crescent(neck, tip_cut=24 if key == "stellarite" else 27)
    d = neck - 19

    def put(points, ch):
        for x, y in points:
            c[(x, y + d)] = ch

    def cut(points):
        for x, y in points:
            c.pop((x, y + d), None)

    if key == "stone":
        # A thick rough stone hook with flecks.
        for k in c:
            c[k] = "#"
        put([(4, 34), (11, 32), (-1, 28)], "b")
        put([(7, 33), (0, 30)], "c")
    elif key == "bronze":
        put([(3, 33), (7, 34), (0, 29), (12, 32)], ";")  # hammer dents
    elif key == "steel":
        # Teeth along the inside edge, a groove along the spine.
        for (x, y), ch in list(c.items()):
            if ch == ":" and y >= 27 + d and (x + y) % 2 == 0:
                del c[(x, y)]
        ox, oy, r = OUTER[0], OUTER[1] + d, OUTER[2]
        for (x, y) in list(c):
            if y >= 29 + d and (r - 2.3) ** 2 <= (x - ox) ** 2 + (y - oy) ** 2 <= (r - 1.4) ** 2:
                c[(x, y)] = ";"
    elif key == "gold":
        put([(18, 26), (17, 25), (16, 25), (15, 26)], ":")  # the tip curls back in
    elif key == "obsidian":
        # A chipped spine and glassy streaks.
        for i, k in enumerate(outer_edge(c, neck)):
            if i % 3 == 1:
                c.pop(k, None)
        put([(0, 29), (1, 30), (2, 31), (8, 33), (9, 34)], ":")
    elif key == "titanite":
        # A light facet line and a crystal shard growing from the spine.
        for k in outer_edge(c, neck)[2:-3]:
            c[k] = "!"
        put([(6, 36), (6, 37), (7, 36)], "c")
        put([(7, 37), (6, 38)], "d")
        put([(5, 36)], "b")
    elif key == "dreadstone":
        # Barbs along the spine and a painite eye at its root.
        put([(1, 35), (2, 34), (8, 37), (8, 36), (15, 34), (14, 34)], "+")
        put([(0, 27)], "E")
    elif key == "void":
        # A rift through the spine with a glowing rim.
        cut([(5, 34), (6, 34), (7, 34)])
        put([(4, 34), (8, 34), (5, 35), (6, 35), (7, 35), (5, 33), (6, 33), (7, 33)], "E")
    elif key == "stellarite":
        put([(2, 33), (9, 35), (14, 32), (-1, 27), (16, 29)], "E")  # stars
    return c


SICKLE_FLOATS = {"void": [(17, 28, 0), (18, 31, 1), (-5, 30, 0)],
                 "stellarite": [(19, 30, 1), (-5, 27, -1)]}


def sickle_boxes(key):
    hw, h = socket_size(key)
    s0 = 9  # a shorter handle than the axe: the sickle stands about as tall as a pickaxe
    s1 = s0 + h
    boxes = [box("handle", "wood", (-1, 1), (0, s1 - 1), 3, group="handle")]
    if key == "stone":
        boxes.append(box("binding", "cord", (-2, 2), (s0, s1), 5))
    else:
        boxes.append(box("socket", "socket", (-hw, hw), (s0, s1), 5))
    boxes += sprite_cells("blade", sickle_cells(key, s1))
    boxes += floats(SICKLE_FLOATS.get(key, []))
    return boxes, (s0, s1)


# ---------------------------------------------------------------- build

def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    for tool, make, fittings in (("axe", axe_boxes, ((10, 12), (0, 2))),
                                 ("sickle", sickle_boxes, ((0, 2),))):
        sets = []
        for key in ORDER:
            boxes, (s0, s1) = make(key)
            t = palette(key)
            t["socket"] = (socket_size(key)[0], (s0, s1))
            if key == "bronze":
                t["fittings"] = fittings
            name = f"{tool}_{key}"
            elements, img, size = write_model(out_dir, name, t, boxes, (s0 + s1) / 2)
            sets.append((name, elements, img, size))
        write_lineup(out_dir, f"{tool}s_lineup", sets)


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
