"""Build the nine metal pickaxes (Generic Model), one model and texture per tier.

The Stone pickaxe is its own model (build_pickaxe_bbmodel.py): a rock head
lashed on with cord. Bronze to Stellarite start from the shape in their icons
(sprites/pickaxes/): a slim metal crescent in a square socket, with the handle
poking out on top. Each tier then gets its own shape and detail, themed on its
metal and its gem (D-012), so the tiers read apart by more than colour:

  Bronze      mattock: a pick on one side, a broad chisel on the other; rivets
  Iron        the plain crescent, as in its icon
  Steel       a long, straight war pick with a top spike and a groove
  Gold        broad flared arms, a crown, an emerald set in the socket
  Obsidian    knapped glass: a chipped top edge, glassy streaks, a jade stone
  Titanite    straight faceted blades, a diamond inset, a crystal cluster
  Dreadstone  a demon engraved on the socket with painite eyes, horns, barbs
  Void        a glowing rift through each arm, a spiral, floating fragments
  Stellarite  the longest crescent, a floating star, an eclipsium orb, stars

Same rules as the Stone pickaxe (docs/MODELS-BLOCKBENCH.md,
docs/BLOCKBENCH-STUDY.md): 2 texture pixels per unit (D-053), boxes in whole
texture pixels, per-face UV, hidden faces removed, lit from the top and
slightly left. Metal and handle colours are picked from the tier's pickaxe
icon, gem colours from its gemstone icon in sprites/items/.

Also writes pickaxes_lineup.bbmodel: all ten pickaxes side by side, Stone
included, for reviewing the set in Blockbench. It is a preview, not an export.

Usage: python build_pickaxe_metal_bbmodel.py <out_dir>
(run build_pickaxe_bbmodel.py first: the lineup reads pickaxe.bbmodel)
"""

import base64
import copy
import io
import json
import sys
import uuid
from pathlib import Path

from PIL import Image

from build_pickaxe_bbmodel import FACES, NORMAL, PX, face_frame, hexrgb, pack, texels


def ramp(*hexes):
    return [hexrgb(h) for h in hexes]


ASH = ramp("301e14", "45271c", "604029", "795331", "7b674b")
OAK = ramp("301a0e", "392011", "482916", "56321b", "643b21")


# ---------------------------------------------------------------- geometry
# Same pixel grid as the Stone pickaxe: columns in x and z centred on whole
# numbers, rows in y from 0 at the bottom of the handle.

def box(name, part, cols, rows, depth, z=0, **extra):
    c0, c1 = cols
    r0, r1 = rows
    h = (depth - 1) / 2
    b = {"name": name, "part": part,
         "lo": [c0 - 0.5, r0, z - h - 0.5], "hi": [c1 + 0.5, r1, z + h + 0.5]}
    b.update(extra)
    return b


def mirror(b, name):
    m = copy.deepcopy(b)
    m["name"] = name
    m["lo"][0], m["hi"][0] = -b["hi"][0], -b["lo"][0]
    return m


def arm(c0, columns):
    """Columns outward from c0: each is (bottom, top, depth), or a list of
    them when the column has a hole in it."""
    return {c0 + i: col if isinstance(col, list) else [col]
            for i, col in enumerate(columns)}


def arm_boxes(side, profile):
    """Merge neighbouring columns with the same profile into one box per
    segment."""
    runs, run = [], []
    for c in sorted(profile):
        if run and profile[c] != profile[run[0]]:
            runs.append(run)
            run = []
        run.append(c)
    runs.append(run)
    boxes = []
    for i, run in enumerate(runs, 1):
        c0, c1 = run[0], run[-1]
        if side == "left":
            c0, c1 = -c1, -c0
        for k, (bot, top, depth) in enumerate(profile[run[0]]):
            name = f"{side}_{i}" + ("" if len(profile[run[0]]) == 1 else "abc"[k])
            boxes.append(box(name, "metal", (c0, c1), (bot, top), depth))
    return boxes


# ---------------------------------------------------------------- tiers
# Tiers in order (D-006, D-020). `icon` is the name in sprites/pickaxes/:
# Titanite and Dreadstone still use the old mithril and adamantite names.
#   metal   head, socket and trim, darkest first (from the pickaxe icon)
#   wood    the handle, from the icon. It follows the hilt (D-058): Ash Wood
#           for Bronze to Gold, Oak Wood for Obsidian to Dreadstone, the Void
#           and Cosmic hilts (made from ingots, so no grain) for the last two.
#   gem     the tier's gem (D-012), from its gemstone icon, darkest first
#   socket  (half width in columns, (bottom row, top row))
#   handle  top row of the handle: above the socket it shows as a knob
#   right   the right arm; `left` is its mirror unless given
#   extras  trim, gems and floating pieces; mirrored ones are listed once
#   face    the socket's front and back, top row first, one character per
#           texture pixel: 0-4 metal, a-d gem, e accent, . plain plate
#   field   the plate colour behind the face (a metal index)
#   marks   painted detail on the arms' front and back: (column, row) -> code

TIERS = {}

TIERS["bronze"] = dict(
    label="Bronze", icon="bronze",
    metal=ramp("795331", "915237", "c67734", "ec9966", "f8ea95"),
    wood=ramp("5d4f3e", "7b674b", "907e62", "b39462", "daccbb"),
    socket=(2, (19, 26)), handle=28,
    right=arm(3, [(20, 25, 3)] * 3 + [(20, 24, 3), (19, 24, 3), (19, 23, 3),
                                       (18, 22, 3), (17, 21, 3), (16, 19, 5), (15, 17, 5)]),
    left=arm(3, [(20, 25, 3)] * 3 + [(20, 24, 3), (19, 24, 3), (19, 23, 3), (18, 22, 3),
                                      (17, 21, 1), (16, 20, 1), (15, 18, 1), (14, 16, 1)]),
    face=[".....",
          ".4.4.",
          ".....",
          ".....",
          ".....",
          ".4.4.",
          "....."],
    # Hammer dents.
    marks={(5, 22): "1", (6, 22): "1", (9, 20): "1", (-6, 21): "1",
           (-9, 20): "1", (-10, 20): "1"},
    # Copper band and pommel on the handle, as in the icon.
    fittings=((9, 11), (0, 2)),
)

TIERS["iron"] = dict(
    label="Iron", icon="iron",
    metal=ramp("4d444c", "5a5d69", "7c899b", "aea7b5", "f8f5f0"),
    wood=ASH,
    socket=(2, (19, 26)), handle=29,
    right=arm(3, [(20, 25, 3)] * 4 + [(20, 24, 3)] * 2 + [(19, 23, 3)] * 2 +
              [(18, 22, 1), (17, 21, 1), (16, 19, 1), (15, 17, 1), (14, 16, 1)]),
    face=[".....",
          ".....",
          ".....",
          "..4..",
          ".....",
          ".....",
          "....."],
)

TIERS["steel"] = dict(
    label="Steel", icon="steel",
    metal=ramp("333a5b", "424461", "545461", "656c81", "91aad5"),
    wood=ASH,
    socket=(2, (19, 27)), handle=27,
    right=arm(3, [(21, 25, 3)] * 5 + [(20, 24, 3)] * 3 +
              [(19, 23, 3), (19, 22, 1), (18, 21, 1), (18, 20, 1), (17, 19, 1),
               (16, 18, 1), (15, 17, 1)]),
    extras=[box("spike_base", "trim", (-1, 1), (27, 28), 3),
            box("spike", "trim", (0, 0), (28, 32), 1)],
    face=[".....",
          ".....",
          ".333.",
          ".000.",
          ".....",
          ".333.",
          ".000.",
          "....."],
    # A groove running along each arm.
    groove=(4, 11),
)

TIERS["gold"] = dict(
    label="Gold", icon="gold",
    metal=ramp("ce6825", "e38a23", "f19f26", "f9d369", "f9f47d"),
    wood=ASH,
    gem=ramp("067739", "1d874c", "24cb3f", "8dfa68"),  # emerald
    socket=(3, (18, 26)), handle=25,
    right=arm(4, [(19, 25, 3)] * 3 + [(19, 24, 3), (18, 24, 3), (18, 23, 3), (17, 22, 3),
                                       (16, 21, 3), (15, 20, 1), (14, 18, 1), (13, 15, 1)]),
    extras=[box("crown_l", "trim", (-2, -2), (26, 27), 1),
            box("crown_m", "trim", (0, 0), (26, 28), 1),
            box("crown_r", "trim", (2, 2), (26, 27), 1)],
    face=[".......",
          ".00000.",
          ".0dcb0.",
          ".0cba0.",
          ".0cba0.",
          ".0baa0.",
          ".00000.",
          "......."],
    wide_band=True,  # two lit rows along the top of each arm
)

TIERS["obsidian"] = dict(
    label="Obsidian", icon="obsidian",
    metal=ramp("2b2332", "382e43", "483b50", "6b5690", "b49dd2"),
    wood=OAK,
    gem=ramp("296952", "3c8e62", "67bc94", "acf0d3"),  # jade
    socket=(2, (19, 26)), handle=29,
    # Knapped: the top edge is chipped, differently on each arm.
    right=arm(3, [(20, 25, 3), (20, 25, 3), (20, 24, 3), (20, 25, 3), (20, 24, 3),
                  (19, 23, 3), (19, 24, 3), (18, 22, 1), (17, 21, 1), (16, 20, 1),
                  (15, 18, 1), (14, 16, 1)]),
    left=arm(3, [(20, 25, 3), (20, 24, 3), (20, 25, 3), (20, 25, 3), (19, 23, 3),
                 (19, 24, 3), (19, 23, 3), (18, 22, 1), (17, 21, 1), (16, 19, 1),
                 (15, 18, 1), (14, 16, 1)]),
    face=[".....",
          ".....",
          ".dcb.",
          ".cba.",
          ".baa.",
          ".....",
          "....."],
    # Glassy streaks.
    marks={(4, 21): "3", (5, 22): "3", (6, 23): "4", (10, 19): "3", (11, 20): "3",
           (-5, 21): "3", (-6, 22): "4", (-10, 19): "3", (-11, 20): "3"},
)

TIERS["titanite"] = dict(
    label="Titanite", icon="mithril",
    metal=ramp("6b5690", "9b7db3", "b49dd2", "cec3e3", "e9d3f3"),
    wood=OAK,
    gem=ramp("3c81cd", "74b7e3", "b5f2fc", "f3fbfe"),  # diamond
    socket=(2, (19, 26)), handle=25,
    # Straight, angled blades.
    right=arm(3, [(20, 25, 3), (20, 25, 3), (20, 24, 3), (19, 23, 3), (19, 22, 3),
                  (18, 22, 3), (18, 21, 1), (18, 20, 1), (17, 19, 1), (17, 19, 1),
                  (16, 18, 1), (16, 17, 1)]),
    extras=[box("crystal_m", "gem", (0, 0), (26, 32), 1),
            box("crystal_l", "gem", (-1, -1), (26, 29), 1, z=-1),
            box("crystal_r", "gem", (1, 1), (26, 30), 1, z=1)],
    face=[".....",
          ".....",
          "..d..",
          ".cdb.",
          "..a..",
          ".....",
          "....."],
    facets=True,  # lit upper half, shaded lower half: a faceted blade
)

TIERS["dreadstone"] = dict(
    label="Dreadstone", icon="adamantite",
    metal=ramp("431420", "5c2c35", "762d35", "98323e", "a36d3f"),
    wood=OAK,
    gem=ramp("62040e", "a10e25", "dd3543", "e94b62"),  # painite
    accent=hexrgb("e94b62"),
    socket=(3, (18, 27)), handle=29,
    right=arm(4, [(20, 25, 3)] * 3 + [(20, 24, 3), (19, 24, 3), (19, 23, 3), (18, 22, 3),
                                       (17, 21, 1), (16, 20, 1), (15, 18, 1), (14, 16, 1),
                                       (13, 15, 1)]),
    extras=[box("barb", "trim", (9, 9), (17, 19), 1, mirrored=True),
            box("horn_base", "trim", (3, 3), (27, 29), 3, mirrored=True, dark=True),
            box("horn_tip", "trim", (4, 4), (28, 31), 1, mirrored=True, dark=True)],
    # The demon: horns, a brow, glowing painite eyes, a snout, fangs, a chin,
    # raised out of a dark sunken field.
    face=[".......",
          ".3...3.",
          ".23332.",
          ".2e2e2.",
          ".22322.",
          ".04040.",
          ".20002.",
          "..222..",
          "......."],
    field=0,
    groove=(5, 10),
)

TIERS["void"] = dict(
    label="Void", icon="void",
    metal=ramp("2b1d3b", "301f4d", "3c2c57", "5e4867", "818190"),
    wood=ramp("2b1d3b", "301f4d", "382658", "49355b", "5e4867"), grain=False,
    gem=ramp("5a2285", "a246c8", "da67ec", "f9d0ed"),  # arcanium
    accent=hexrgb("da67ec"), float_shade=hexrgb("a246c8"),
    socket=(3, (19, 26)), handle=29,
    # A rift through each arm, in a different place on each side.
    right=arm(4, [(20, 25, 3)] * 3 + [[(20, 21, 3), (23, 24, 3)], [(19, 21, 3), (23, 24, 3)],
                                       (19, 23, 3), (18, 22, 3), (17, 21, 1), (16, 20, 1),
                                       (15, 18, 1), (14, 16, 1)]),
    left=arm(4, [(20, 25, 3)] * 3 + [(20, 24, 3), [(19, 21, 3), (23, 24, 3)],
                                      [(19, 20, 3), (22, 23, 3)], (18, 22, 3), (17, 21, 1),
                                      (16, 20, 1), (15, 18, 1), (14, 16, 1)]),
    extras=[box("fragment_1", "float", (16, 16), (17, 18), 1),
            box("fragment_2", "float", (15, 15), (19, 20), 1, z=1),
            box("fragment_3", "float", (-16, -16), (14, 15), 1, z=-1)],
    face=[".......",
          ".33330.",
          ".30000.",
          ".30e30.",
          ".30030.",
          ".03300.",
          "......."],
    field=0,
)

TIERS["stellarite"] = dict(
    label="Stellarite", icon="stellarite",
    metal=ramp("3b5083", "4c6893", "4f99d0", "7995b7", "85b2c3"),
    wood=ramp("3b5083", "4a5270", "557e9f", "4f99d0", "959da3"), grain=False,
    gem=ramp("1d1e24", "1f283e", "7b6e71", "ffffff"),  # eclipsium
    accent=hexrgb("ddffa8"),  # the icon's pale-yellow stars
    float_shade=hexrgb("85b2c3"),
    socket=(3, (19, 26)), handle=25,
    right=arm(4, [(20, 25, 3)] * 3 + [(19, 24, 3)] * 2 + [(18, 23, 3)] * 2 +
              [(17, 22, 1), (16, 21, 1), (15, 20, 1), (14, 18, 1), (13, 17, 1),
               (12, 15, 1), (11, 13, 1)]),
    # A four-pointed star floating above the socket, and two loose stars.
    extras=[box("star_v", "float", (0, 0), (28, 33), 1),
            box("star_l", "float", (-2, -1), (30, 31), 1),
            box("star_r", "float", (1, 2), (30, 31), 1),
            box("star_1", "float", (16, 16), (17, 18), 1, z=1),
            box("star_2", "float", (-15, -15), (19, 20), 1, z=-1)],
    face=[".......",
          "..aaa..",
          ".abbba.",
          ".abdba.",
          ".abbba.",
          "..aaa..",
          "......."],
    marks={(-12, 18): "e", (-7, 22): "e", (6, 23): "e", (9, 21): "e", (13, 18): "e",
           (-10, 20): "e", (11, 19): "e"},
)


def tier_boxes(t):
    hw, (s0, s1) = t["socket"]
    boxes = [box("handle", "wood", (-1, 1), (0, t["handle"]), 3, group="handle"),
             box("socket", "socket", (-hw, hw), (s0, s1), 5)]
    right = t["right"]
    left = t.get("left", right)
    boxes += arm_boxes("left", left) + arm_boxes("right", right)
    for e in t.get("extras", []):
        boxes.append(e)
        if e.get("mirrored"):
            boxes.append(mirror(e, e["name"] + "_l"))
    for b in boxes:
        b.setdefault("group", "head")
    return boxes


def inside(p, b, eps=1e-6):
    return all(b["lo"][k] + eps < p[k] < b["hi"][k] - eps for k in range(3))


def covered(boxes, p, f, me):
    n = NORMAL[f]
    q = tuple(p[k] + 0.25 * n[k] for k in range(3))
    return any(inside(q, b) for b in boxes if b is not me)


def col(p):
    return round(p[0])


def zcol(p):
    return round(p[2])


def row(p):
    return int(p[1] // 1)


def own_col(p, f):
    """The column of the box a face texel belongs to (side faces sit on the
    boundary between two columns)."""
    n = NORMAL[f]
    return col([p[k] - 0.25 * n[k] for k in range(3)])


# ---------------------------------------------------------------- painting

def code_colour(t, code):
    if code.isdigit():
        return t["metal"][int(code)]
    if code == "e":
        return t["accent"]
    return t["gem"]["abcd".index(code)]


def paint_metal(t, b, f, p, i, j):
    m = t["metal"]
    c, r = own_col(p, f), row(p)
    left = c < 0
    profile = (t.get("left", t["right"]) if left else t["right"])
    segs = profile[abs(c)]
    bot, top, _ = next((s for s in segs if s[0] <= r < s[1]), segs[0])
    tip = abs(c) == max(profile)
    hw = t["socket"][0]
    if f in ("north", "south"):
        mark = t.get("marks", {}).get((c, r))
        if mark:
            return code_colour(t, mark)
        if tip:
            return m[4 if left else 3]  # the point catches the light
        if rift_rim(segs, bot, top, r):
            return t["accent"]  # the rim of a rift glows
        v = 2
        mid = (bot + top) // 2
        if r == top - 1:
            v = 3  # lit band along the top of the arm
            # Rim highlight along the top edge of the lit (left) arm, and a
            # shorter one on the right arm. Dimmer on the back face.
            span = range(hw + 2, hw + 9) if left else range(hw + 3, hw + 6)
            if abs(c) in span and f == "south":
                v = 4
        elif r == top - 2 and t.get("wide_band") and top - bot >= 4:
            v = 3
        elif t.get("facets") and r >= mid:
            v = 3  # upper facet faces the light
        elif r == bot:
            v = 1
        groove = t.get("groove")
        if groove and groove[0] <= abs(c) <= groove[1] and top - bot >= 4 and r == mid:
            v = 0
        if abs(c) == hw + 1 and v < 4:  # painted shadow against the socket
            v -= 1
        return m[max(v, 0)]
    if len(segs) > 1 and ((f == "up" and (bot, top) == segs[0][:2])
                          or (f == "down" and (bot, top) == segs[-1][:2])):
        return t["accent"]  # the inside of a rift
    if f == "up":
        w = int(b["hi"][0] - b["lo"][0])
        outer = (i == 0) if left else (i == w - 1)
        if left and outer:
            return m[4]
        return m[3]
    if f == "west":
        return m[3] if r == top - 1 else m[2 if left else 1]
    if f == "east":
        return m[2] if r == top - 1 else m[1]
    return m[0] if abs(c) <= hw + 4 else m[1]  # down


def rift_rim(segs, bot, top, r):
    """True for the row of an arm's front that borders a hole in the arm."""
    if len(segs) < 2:
        return False
    lower, upper = segs[0][:2], segs[-1][:2]
    return (bot, top) == lower and r == top - 1 or (bot, top) == upper and r == bot


def paint_socket(t, b, f, p, i, j):
    """A square plate: lit top and left edges, shaded right and bottom edges,
    and the tier's face (rivets, a gem, an engraving) on the front and back."""
    m = t["metal"]
    c, z, r = col(p), zcol(p), row(p)
    hw, (s0, s1) = t["socket"]
    if f in ("up", "down"):
        return m[3] if f == "up" else m[0]
    if f in ("north", "south"):
        code = t["face"][j][i]
        if code != ".":
            return code_colour(t, code)
    k = c if f == "south" else -c if f == "north" else z if f == "west" else -z
    edge = hw if f in ("north", "south") else 2
    lit = f != "east"
    if r == s1 - 1:
        return m[3 if lit else 2]
    if r == s0:
        return m[0]
    if k == -edge:
        return m[3 if lit else 1]
    if k == edge:
        return m[0]
    return m[t.get("field", 1)]


def paint_trim(t, b, f, p, i, j):
    """Spikes, crowns, horns and barbs: plain metal, lit from the top left.
    Horns are a step darker, with lit tips."""
    m = t["metal"]
    d = 1 if b.get("dark") else 0
    top_row = row(p) == int(b["hi"][1]) - 1
    if f == "up":
        return m[4 - d]
    if f == "down":
        return m[0]
    if f == "east":
        return m[1]
    if top_row:
        return m[3]
    return m[(3 if f == "west" else 2) - d]


def paint_gem(t, b, f, p, i, j):
    """Crystals: lit top and left, a white glint at the top of the front."""
    g = t["gem"]
    if f == "up":
        return g[3]
    if f == "down":
        return g[0]
    if f == "east":
        return g[1]
    if j == 0:
        return g[3]
    return g[2]


def paint_float(t, b, f, p, i, j):
    """Floating fragments and stars glow in the accent colour."""
    if f in ("up", "west", "south"):
        return t["accent"]
    return t["float_shade"]


def paint_wood(t, b, f, p, i, j):
    w = t["wood"]
    c, z, r = col(p), zcol(p), row(p)
    fittings = t.get("fittings")
    if fittings and (any(a <= r < e for a, e in fittings) or f == "down"):
        return paint_fitting(t, f, r)
    if f == "up":
        return w[2] if (c, z) == (0, 0) else w[4]  # end grain, dark heart
    if f == "down":
        return w[2] if (c, z) == (0, 0) else w[1]
    if f == "west":
        v, k = 4, z
    elif f == "east":
        v, k = 2, -z
    else:
        k = c if f == "south" else -c
        v = 4 if c == -1 else 3  # lit edge on the left
    # Grain: short streaks running along the handle, staggered per column.
    if t.get("grain", True):
        phase = (r + 3 * k + (2 if f in ("north", "east") else 0)) % 7
        if phase in (0, 1):
            v -= 1
        elif phase == 4 and v < 4:
            v += 1
    # Painted shadow under the socket and next to Bronze's fittings.
    s0, s1 = t["socket"][1]
    if r == s0 - 1 or r == s1 or r == 0:
        v -= 1
    if fittings and any(r in (a - 1, e) for a, e in fittings):
        v -= 1
    return w[max(v, 0)]


def paint_fitting(t, f, r):
    """Bronze's copper band and pommel: lit top row, shaded bottom row."""
    m = t["metal"]
    if f == "down":
        return m[0]
    lit = f not in ("east", "north")
    if any(r == e - 1 for _, e in t["fittings"]):
        return m[3 if lit else 2]
    return m[2 if lit else 1]


PAINTERS = {"metal": paint_metal, "socket": paint_socket, "wood": paint_wood,
            "trim": paint_trim, "gem": paint_gem, "float": paint_float}


# ---------------------------------------------------------------- .bbmodel

def uid():
    return str(uuid.uuid4())


def u(v):
    return round(v * PX, 4)


def texture_entry(index, img, path):
    buf = io.BytesIO()
    img.save(buf, "PNG")
    w, h = img.size
    return {
        "path": str(path.resolve()), "name": path.name, "folder": "",
        "namespace": "", "id": str(index), "group": "", "width": w, "height": h,
        "uv_width": w, "uv_height": h, "particle": False,
        "use_as_default": False, "layers_enabled": False, "sync_to_project": "",
        "render_mode": "default", "render_sides": "auto", "pbr_channel": "color",
        "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
        "frame_interpolate": False, "visible": True, "internal": True,
        "saved": True, "uuid": uid(), "relative_path": path.name,
        "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
    }


def group(name, origin, children, **extra):
    g = {"name": name, "origin": origin, "color": 0, "uuid": uid(),
         "export": True, "mirror_uv": False, "isOpen": True, "locked": False,
         "visibility": True, "autouv": 0, "children": children}
    g.update(extra)
    return g


def project(name, elements, outliner, textures, size):
    return {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": name, "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": size, "height": size},
        "elements": elements, "outliner": outliner, "textures": textures,
    }


def build_tier(out_dir, key, t):
    boxes = tier_boxes(t)
    visible = {}
    for bi, b in enumerate(boxes):
        for f in FACES:
            if all(covered(boxes, p, f, b) for _, _, p in texels(b, f)):
                continue
            _, _, _, w, h = face_frame(b, f)
            visible[(bi, f)] = (int(w), int(h))
    rects = [(k, w, h) for k, (w, h) in visible.items()]
    size = 64 if sum(w * h for _, w, h in rects) < 0.6 * 64 * 64 else 128
    places = pack(rects, size)

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for (bi, f), (ox, oy) in places.items():
        b = boxes[bi]
        for i, j, p in texels(b, f):
            img.putpixel((ox + i, oy + j), PAINTERS[b["part"]](t, b, f, p, i, j))
    path = out_dir / f"pickaxe_{key}.png"
    img.save(path)

    s0, s1 = t["socket"][1]
    origins = {"handle": [0, u(4), 0],  # grip
               "head": [0, u((s0 + s1) / 2), 0]}  # centre of the socket
    children = {"handle": [], "head": []}
    elements = []
    for bi, b in enumerate(boxes):
        faces = {}
        for f in FACES:
            if (bi, f) in places:
                ox, oy = places[(bi, f)]
                w, h = visible[(bi, f)]
                faces[f] = {"uv": [ox, oy, ox + w, oy + h], "texture": 0}
            else:
                faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
        e = {
            "name": b["name"], "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": [u(v) for v in b["lo"]], "to": [u(v) for v in b["hi"]],
            "autouv": 0, "color": 0, "origin": origins[b["group"]],
            "faces": faces, "type": "cube", "uuid": uid(),
        }
        elements.append(e)
        children[b["group"]].append(e["uuid"])

    # Scale dummy: hidden and never exported. Same PLACEHOLDER height as the
    # Stone pickaxe (~1.13 m = 18 units) until the Imp's height is decided.
    dummy = {
        "name": "scale_dummy_imp_placeholder", "box_uv": False, "rescale": False,
        "locked": True, "light_emission": 0, "render_order": "default",
        "allow_mirror_modeling": True, "export": False, "visibility": False,
        "from": [12, 0, -2], "to": [16, 18, 2], "autouv": 0, "color": 1,
        "origin": [14, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    outliner = [
        group("pickaxe", origins["handle"], [
            group("handle", origins["handle"], children["handle"]),
            group("head", origins["head"], children["head"]),
        ]),
        group("scale_dummy", [14, 0, 0], [dummy["uuid"]], export=False, visibility=False),
    ]
    model = project(f"pickaxe_{key}", elements + [dummy], outliner,
                    [texture_entry(0, img, path)], size)
    (out_dir / f"pickaxe_{key}.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"{key:<11} boxes: {len(boxes):>2}  visible faces: {len(visible):>3}  "
          f"texels used: {used}/{size * size}")
    return elements, img, size


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)
    sets = [("stone", *load_stone(out_dir))]
    for key, t in TIERS.items():
        sets.append((key, *build_tier(out_dir, key, t)))
    write_lineup(out_dir, sets)


def load_stone(out_dir):
    stone = json.loads((out_dir / "pickaxe.bbmodel").read_text())
    elements = [e for e in stone["elements"] if e.get("export", True)]
    img = Image.open(out_dir / "pickaxe_stone.png").convert("RGBA")
    return elements, img, img.size[0]


def write_lineup(out_dir, sets):
    """All ten pickaxes in a row, each with its own texture, Stone first.
    Every model's UVs are scaled onto one 128-pixel grid, the largest size."""
    size = max(s for _, _, _, s in sets)
    elements, outliner, textures = [], [], []
    for ti, (key, src, img, own) in enumerate(sets):
        dx = ti * 20  # 20 units apart
        kids = []
        for e in src:
            e = copy.deepcopy(e)
            e["uuid"] = uid()
            e["from"][0] += dx
            e["to"][0] += dx
            e["origin"] = [e["origin"][0] + dx] + e["origin"][1:]
            for face in e["faces"].values():
                if face["texture"] is not None:
                    face["texture"] = ti
                    face["uv"] = [v * size // own for v in face["uv"]]
            elements.append(e)
            kids.append(e["uuid"])
        outliner.append(group(key, [dx, 2, 0], kids))
        tex = texture_entry(ti, img, out_dir / f"pickaxe_{key}.png")
        tex["uv_width"] = tex["uv_height"] = size
        textures.append(tex)
    model = project("pickaxes_lineup", elements, outliner, textures, size)
    (out_dir / "pickaxes_lineup.bbmodel").write_text(json.dumps(model, indent="\t"))


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
