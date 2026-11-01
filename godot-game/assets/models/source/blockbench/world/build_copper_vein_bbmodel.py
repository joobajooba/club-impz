"""Build an EXPERIMENTAL Blockbench copper ore vein: a rounded stone boulder with copper
breaking out of it (Generic Model).

Experimental: D-047 keeps the world, ore veins included, out of voxel style
(veins follow the Stylized Ore look, D-019). The user asked for this as an
experiment; it does not replace models/copper_vein.glb and changes no rule.

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. Every box is
  a whole number of texture pixels; no stretching, no Inflate.
- Not a square rock: the boulder is described as a smooth, lumpy solid (three
  rounded lobes and a flatter top shelf, warped by low-frequency noise), filled
  with 2 px steps and greedily merged into boxes. The stepped, layered outline
  reads round from the camera, like the stacked slabs of the Stylized rock
  references (ART-DIRECTION 9.4).
- Per-face UV, one texture, hidden faces removed.
- Lit from the top, slightly front-left; hue-shifted ramps; the light-facing
  edge of every ledge highlighted, painted shadow in every step and where the
  ore meets the rock; strata lines, cracks, sparse mineral flecks, moss on top.
- A vein is a calm rock body with bright ore in it (ART-DIRECTION 9.1): warm
  purple-grey rock (the Stylized Ore swatch #847385, allowed per tier by
  D-017) and copper as the accent. Copper streaks run across the rock along
  two vein planes, and chunky copper pieces break out where the veins meet the
  surface, a few of them angled out (rotation used sparingly, MODELS-BLOCKBENCH
  4.2). Loose rubble and copper nuggets lie at the foot.
- Colours from the copper icons (CLAUDE.md "Item pictures"): the ore ramp and
  its grey flecks from sprites/items/nugget_copper.png, the green patina from
  the fleck on sprites/items/ingot_copper.png.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground; the vein's front faces north (-z).

Usage: python build_copper_vein_bbmodel.py [out_dir]   (writes copper_vein.bbmodel,
copper_vein.png, copper_vein_preview.png and copper_vein_silhouette.png)
"""

import base64
import io
import json
import math
import sys
import uuid
from pathlib import Path

from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from build_pickaxe_bbmodel import FACES, NORMAL, face_frame, texels  # noqa: E402

PX = 0.5   # Blockbench units per texture pixel (D-053)
CELL = 2   # the rock is sculpted in 2 px steps


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


# Ramps, darkest first. Rock shadows lean violet, its highlights lean warm.
# One step darker than first drawn: the game's sun washed the first Godot test
# out to near white.
ROCK = ramp("#211a27", "#2b2231", "#463a4b", "#625466", "#847385", "#a0909b")
CRACK = hexrgb("#1f1824")
COPPER = ramp("#6d2521", "#803a22", "#ad4524", "#cf6142", "#eb7f5c", "#f59275", "#f5afa8")
FLECK = ramp("#594c44", "#6e5d5a", "#786b5e")                          # grey flecks in the ore
PATINA = ramp("#4a4e26", "#6a7030", "#7d8432", "#9a9e4c")               # verdigris, from the ingot
MOSS = ramp("#2c3a22", "#43562a", "#5e7633", "#7c9640")                 # ART-DIRECTION canopy swatch
LICHEN = ramp("#8d8a6a", "#aaa680")                                     # pale crusts on the top

FACE_SHADE = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}


# ---------------------------------------------------------------- the boulder as a solid

def ellipsoid(p, c, r):
    """Approximate signed distance (px) to an ellipsoid."""
    q = math.sqrt(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)))
    return (q - 1.0) * min(r)


def smin(a, b, k):
    h = max(k - abs(a - b), 0.0) / k
    return min(a, b) - h * h * k * 0.25


LOBES = [
    ((0.0, 7.0, 0.5), (17.0, 15.0, 14.0)),     # the main body
    ((-11.0, 4.5, 7.0), (9.5, 9.0, 8.0)),      # a lower lobe at the back left
    ((11.0, 3.5, -8.0), (7.5, 6.5, 6.5)),      # a small lump at the front right
    ((3.0, 17.5, -1.5), (10.5, 5.0, 9.0)),     # a flatter shelf on top, off-centre
]


def rock_field(p):
    x, y, z = p
    d = ellipsoid(p, *LOBES[0])
    for c, r in LOBES[1:]:
        d = smin(d, ellipsoid(p, c, r), 4.0)
    # Low-frequency warping: bulges and dents, no two sides alike.
    d += 1.1 * math.sin(0.21 * x + 0.33 * z + 1.1)
    d += 0.8 * math.sin(0.31 * z - 0.19 * y + 2.0)
    d += 0.5 * math.sin(0.43 * x + 0.29 * y + 0.5)
    return d


NX, NY, NZ = 21, 13, 19
X0, Y0, Z0 = -21, 0, -19


def cell_box(i, j, k):
    return (X0 + i * CELL, Y0 + j * CELL, Z0 + k * CELL)


def build_grid():
    g = set()
    for i in range(NX):
        for j in range(NY):
            for k in range(NZ):
                x, y, z = cell_box(i, j, k)
                if rock_field((x + 1, y + 1, z + 1)) < 0:
                    g.add((i, j, k))
    # Keep only cells joined to the ground: no floating crumbs.
    keep, todo = set(), [c for c in g if c[1] == 0]
    while todo:
        c = todo.pop()
        if c in keep:
            continue
        keep.add(c)
        i, j, k = c
        for d in ((1, 0, 0), (-1, 0, 0), (0, 1, 0), (0, -1, 0), (0, 0, 1), (0, 0, -1)):
            n = (i + d[0], j + d[1], k + d[2])
            if n in g and n not in keep:
                todo.append(n)
    # Calm the surface: drop lone knobs, fill pits (two passes of a 26-neighbour
    # vote), so the steps run in long ledges instead of crumbs.
    for _ in range(2):
        nxt = set(keep)
        for i in range(NX):
            for j in range(NY):
                for k in range(NZ):
                    n = sum((i + a, j + b, k + c) in keep
                            for a in (-1, 0, 1) for b in (-1, 0, 1) for c in (-1, 0, 1)
                            if (a, b, c) != (0, 0, 0) and j + b >= 0)
                    if j == 0:
                        n += 9                     # the ground counts as solid below
                    if (i, j, k) in keep and n < 10:
                        nxt.discard((i, j, k))
                    elif (i, j, k) not in keep and n >= 17:
                        nxt.add((i, j, k))
        keep = nxt
    return keep


GRID = build_grid()


def greedy_boxes(grid):
    """Merge cells into boxes: grow along x, then z, then y."""
    left = set(grid)
    boxes = []
    for j in range(NY):
        for k in range(NZ):
            for i in range(NX):
                if (i, j, k) not in left:
                    continue
                i1 = i
                while (i1 + 1, j, k) in left:
                    i1 += 1
                k1 = k
                while all((ii, j, k1 + 1) in left for ii in range(i, i1 + 1)):
                    k1 += 1
                j1 = j
                while all((ii, j1 + 1, kk) in left for ii in range(i, i1 + 1) for kk in range(k, k1 + 1)):
                    j1 += 1
                for ii in range(i, i1 + 1):
                    for jj in range(j, j1 + 1):
                        for kk in range(k, k1 + 1):
                            left.discard((ii, jj, kk))
                lo = cell_box(i, j, k)
                hi = tuple(v + CELL for v in cell_box(i1, j1, k1))
                boxes.append((lo, hi))
    return boxes


def rock_at(p):
    """True if the point (px) is inside the rock."""
    i = math.floor((p[0] - X0) / CELL)
    j = math.floor((p[1] - Y0) / CELL)
    k = math.floor((p[2] - Z0) / CELL)
    return (i, j, k) in GRID


def surface_point(direction, centre=(0.0, 9.0, 0.0)):
    """March out from the centre until leaving the rock; returns the last
    point inside (px)."""
    d = direction
    n = math.sqrt(sum(v * v for v in d))
    d = [v / n for v in d]
    p = list(centre)
    last = tuple(p)
    for _ in range(200):
        p = [p[k] + 0.25 * d[k] for k in range(3)]
        if rock_at(p):
            last = tuple(p)
        elif p[1] < 0 or math.dist(p, centre) > 40:
            break
    return last


# ---------------------------------------------------------------- elements

def el(name, group, part, lo, hi, rot=None, pivot=None):
    return {"name": name, "group": group, "part": part, "lo": list(lo), "hi": list(hi),
            "rot": rot, "pivot": pivot}


def hash01(*key):
    h = 2166136261
    for v in key:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def snap(v):
    return round(v)


def chunk(name, direction, size, lean=0.0, sink=0.45, part="ore"):
    """A copper piece set into the surface where `direction` leaves the rock.
    The box is sunk by `sink` of its height along its main axis; `lean`
    (degrees) tips it outward around its base."""
    s = surface_point(direction)
    w, h, d = size
    dx, dy, dz = direction
    horiz = math.hypot(dx, dz)
    up = dy > horiz                               # sits on a top face or sticks out of a side
    if up:
        base = (snap(s[0]), snap(s[1] + 1 - sink * h), snap(s[2]))
        lo = (base[0] - w / 2, base[1], base[2] - d / 2)
        hi = (base[0] + w / 2, base[1] + h, base[2] + d / 2)
        pivot = (base[0], base[1] + sink * h, base[2])
    else:
        base = (snap(s[0]), snap(s[1]), snap(s[2]))
        lo = (base[0] - w / 2, base[1] - h / 2, base[2] - d / 2)
        hi = (base[0] + w / 2, base[1] + h / 2, base[2] + d / 2)
        # Push it out along its strongest horizontal axis so it pokes out.
        if abs(dx) >= abs(dz):
            off = (1 if dx > 0 else -1) * w * (0.5 - sink)
            lo, hi = (lo[0] + off, lo[1], lo[2]), (hi[0] + off, hi[1], hi[2])
        else:
            off = (1 if dz > 0 else -1) * d * (0.5 - sink)
            lo, hi = (lo[0], lo[1], lo[2] + off), (hi[0], hi[1], hi[2] + off)
        pivot = tuple(base)
    rot = None
    if lean:
        hn = horiz or 1.0
        rot = [round(lean * dz / hn, 1), 0, round(-lean * dx / hn, 1)]
    # Break the cube: a narrower cap on its outer face and a knob on one side,
    # so each piece reads as a faceted nugget, not a die.
    out = [el(name, "ore", part, lo, hi, rot, pivot)]
    if min(w, h, d) >= 3:
        if up:
            cap = ((lo[0] + 1, hi[1], lo[2] + 1), (hi[0] - 1, hi[1] + 1, hi[2] - 1))
        elif abs(dx) >= abs(dz):
            sx = 1 if dx > 0 else -1
            xo = hi[0] if sx > 0 else lo[0] - 1
            cap = ((xo, lo[1] + 1, lo[2] + 1), (xo + 1, hi[1] - 1, hi[2] - 1))
        else:
            sz = 1 if dz > 0 else -1
            zo = hi[2] if sz > 0 else lo[2] - 1
            cap = ((lo[0] + 1, lo[1] + 1, zo), (hi[0] - 1, hi[1] - 1, zo + 1))
        out.append(el(name + "_cap", "ore", part, *cap, rot, pivot))
        kw = max(2, w // 2)
        knob = ((hi[0] - 1, lo[1], lo[2] + 1), (hi[0] - 1 + kw, lo[1] + max(2, h // 2), lo[2] + 1 + kw))             if (hash01(len(name), w, h) > 0.5) else             ((lo[0] + 1 - kw, lo[1], hi[2] - 1 - kw), (lo[0] + 1, lo[1] + max(2, h // 2), hi[2] - 1))
        out.append(el(name + "_knob", "ore", part, *knob, rot, pivot))
    return out


def rock_elements():
    out = []
    for n, (lo, hi) in enumerate(greedy_boxes(GRID)):
        out.append(el(f"rock_{n + 1:02d}", "rock", "rock", lo, hi))
    return out


# Copper breaks out along the vein planes (see VEINS below): a big angled
# cluster at the front, a tall spike on the top shelf, lumps down the sides.
ORE = [p for c in [
    chunk("ore_crown", (0.15, 1.0, -0.35), (5, 6, 5), lean=18, sink=0.35),
    chunk("ore_crown_side", (0.45, 1.0, -0.2), (3, 5, 3), lean=28, sink=0.4),
    chunk("ore_front", (0.2, 0.25, -1.0), (6, 6, 5), lean=20, sink=0.4),
    chunk("ore_front_small", (-0.15, 0.05, -1.0), (4, 4, 4), sink=0.45),
    chunk("ore_front_low", (0.45, -0.25, -1.0), (3, 3, 3), sink=0.4),
    chunk("ore_right", (1.0, 0.35, -0.25), (5, 5, 4), lean=22, sink=0.4),
    chunk("ore_right_small", (1.0, -0.05, 0.2), (3, 3, 3), sink=0.45),
    chunk("ore_left", (-1.0, 0.55, -0.45), (4, 5, 4), lean=16, sink=0.45),
    chunk("ore_back", (0.25, 0.45, 1.0), (5, 4, 4), sink=0.45),
    chunk("ore_back_left", (-0.8, 0.1, 1.0), (3, 4, 3), lean=14, sink=0.45),
    chunk("ore_top_nugget", (-0.35, 1.0, 0.25), (3, 3, 3), sink=0.5),
] for p in c]

# Loose rubble and copper nuggets at the foot of the boulder.
RUBBLE = [
    el("rubble_1", "rubble", "rock", (-21, 0, -13), (-17, 2, -9)),
    el("rubble_2", "rubble", "rock", (-19, 0, -16), (-17, 1, -14)),
    el("rubble_3", "rubble", "rock", (17, 0, 4), (21, 3, 8)),
    el("rubble_4", "rubble", "rock", (5, 0, -20), (8, 2, -17)),
    el("nugget_1", "rubble", "nugget", (9, 0, -21), (11, 2, -19)),
    el("nugget_2", "rubble", "nugget", (-16, 0, -18), (-14, 1, -16)),
    el("nugget_3", "rubble", "nugget", (19, 0, -2), (21, 2, 0)),
]

ELEMENTS = rock_elements() + ORE + RUBBLE
ROTATED = {id(e) for e in ELEMENTS if e["rot"]}


def inside(p, e, eps=1e-6):
    return all(e["lo"][k] + eps < p[k] < e["hi"][k] - eps for k in range(3))


def solid(q, me):
    """True if q is inside the rock or an unrotated piece other than `me`.
    Angled pieces neither hide faces nor take painted shadow."""
    if id(me) in ROTATED:
        return False
    if rock_at(q):
        return True
    return any(e is not me and id(e) not in ROTATED and inside(q, e) for e in ORE + RUBBLE)


def covered(p, f, me):
    n = NORMAL[f]
    return solid(tuple(p[k] + 0.25 * n[k] for k in range(3)), me)


def offset(p, *moves):
    q = list(p)
    for d, s in moves:
        for k in range(3):
            q[k] += d[k] * s
    return tuple(q)


UP = (0, 1, 0)


def tangents(f):
    n = NORMAL[f]
    return [t for t in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if not any(t[k] and n[k] for k in range(3))]


def contact(p, f, me):
    n = NORMAL[f]
    q = offset(p, (n, 0.5))
    return any(solid(offset(q, (t, s)), me) for t in tangents(f) for s in (-1, 1))


# ---------------------------------------------------------------- markings

def fi(v):
    return math.floor(v)


def seg_dist(p, a, b):
    ab = [b[k] - a[k] for k in range(3)]
    ap = [p[k] - a[k] for k in range(3)]
    t = max(0.0, min(1.0, sum(ap[k] * ab[k] for k in range(3)) / sum(v * v for v in ab)))
    return math.dist(p, [a[k] + t * ab[k] for k in range(3)])


# Copper veins: planes through the boulder, as (normal, offset, half width).
# Where they cut the surface the rock shows a copper streak with a dark rim.
VEINS = [
    ((0.55, -0.35, 0.75), -1.0, 0.75),
    ((-0.45, 0.75, 0.3), 9.0, 0.4),
]

# Cracks: polylines over the surface.
CRACKS = [
    [(-14, 14, -10), (-9, 10, -13), (-6, 4, -14), (-7, 0, -13)],
    [(12, 18, 4), (15, 12, 6), (17, 6, 3)],
    [(-4, 20, 8), (-9, 17, 11), (-14, 13, 12)],
]

# Moss on the sheltered top, as blobs.
MOSS_BLOBS = [((-6.0, 22.0, 4.0), (7.0, 4.0, 6.0)), ((-14.0, 13.0, 9.0), (5.0, 3.0, 4.0)),
              ((8.0, 20.0, 6.0), (4.0, 3.0, 3.5))]


def vein_dist(p):
    best = 99.0
    for (nx, ny, nz), d0, half in VEINS:
        n = math.sqrt(nx * nx + ny * ny + nz * nz)
        wob = 0.35 * math.sin(0.5 * p[0] + 0.3 * p[2]) + 0.25 * math.sin(0.7 * p[1])
        d = abs((nx * p[0] + ny * p[1] + nz * p[2]) / n - d0 + wob) - half
        best = min(best, d)
    return best


def on_crack(p):
    for line in CRACKS:
        for a, b in zip(line, line[1:]):
            if seg_dist(p, a, b) < 0.75:
                return True
    return False


def in_moss(p):
    return any(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)) < 1 for c, r in MOSS_BLOBS)


# ---------------------------------------------------------------- painting

def clamp(v, lo, hi):
    return max(lo, min(hi, v))


def rock_shade(e, f, p):
    """Shade index on the 6-step rock ramp, from the face direction, the
    height, and what is around the texel."""
    x, y, z = p
    n = NORMAL[f]
    v = FACE_SHADE[f]
    if y > 17:
        v += 1                                     # lighter where the sky hits
    elif y < 5:
        v -= 1                                     # darker near the ground
    if y < 1.5 and f not in ("up", "down"):
        v -= 1
    out = offset(p, (n, 0.5))
    if f == "up":
        # Light-facing ledge edges catch the light; steps beside a wall sit in shadow.
        if not rock_at(offset(p, ((-1, 0, 0), 1.0), (UP, -0.5))) or \
           not rock_at(offset(p, ((0, 0, -1), 1.0), (UP, -0.5))):
            v += 1
        if any(rock_at(offset(out, (t, s))) for t in ((1, 0, 0), (0, 0, 1)) for s in (-1, 1)):
            v -= 1
    elif f != "down":
        if f in ("north", "west") and not rock_at(offset(p, (n, -0.5), (UP, 1.0))):
            v += 1                                 # top row of a ledge facing the light
        if rock_at(offset(out, (UP, 1.0))):
            v -= 1                                 # tucked under an overhang
    return v


def paint_rock(e, f, p, i, j, w, h):
    x, y, z = p
    v = rock_shade(e, f, p)
    if contact(p, f, e):
        v -= 1                                     # shadow round the ore and the rubble
    rubble = e["group"] == "rubble"
    if not rubble:
        vd = vein_dist(p)
        if vd < 0:
            return COPPER[clamp(v, 1, 5)]          # copper streak in the rock
        if vd < 0.7:
            v -= 1                                 # dark rim round the streak
        if on_crack(p):
            return CRACK if f != "up" else ROCK[clamp(v - 2, 0, 5)]
        if f == "up" and in_moss(p):
            k = hash01(fi(x / 2), fi(z / 2), 7)
            return MOSS[clamp(v - 2 + (1 if k > 0.7 else (-1 if k < 0.2 else 0)), 0, 3)]   # tufts
        if f == "up" and y > 14 and hash01(fi(x / 2), fi(z / 2), 3) < 0.05:
            return LICHEN[1 if (fi(x) + fi(z)) % 2 else 0]      # lichen spots, 2 px
        if f in ("north", "south", "west", "east") and in_moss(offset(p, (UP, 1.5))) and \
                not rock_at(offset(p, (NORMAL[f], 0.5), (UP, 1.0))) and fi(y) % 2 == 0 and \
                hash01(fi(x), fi(z)) < 0.6:
            return MOSS[clamp(v - 2, 0, 3)]        # moss hanging over a ledge
        # Strata: thin, gently tilted layer lines with breaks.
        if f in ("north", "south", "west", "east"):
            band = fi(y + 1.2 * math.sin(0.18 * (x + z)))
            if band % 6 == 0 and hash01(fi(x / 3), fi(z / 3), band) > 0.5:
                v -= 1
        # Sparse mineral flecks: 2 px clusters, lighter, few and far between.
        if f == "up" and hash01(fi(x / 3), fi(z / 3)) < 0.06 and fi(x) % 3 != 2:
            v += 1
    return ROCK[clamp(v, 0, 5)]


def paint_ore(e, f, p, i, j, w, h):
    """Copper chunks: lit top and light-side faces, a sparkle on the top
    corner nearest the light, grey flecks like the icon, patina low down."""
    x, y, z = p
    v = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    if f == "up" and (i == 0 or j == 0):
        v = 5                                      # lit edges
    if f == "up" and i == 0 and j == 0:
        return COPPER[6]                           # the sparkle
    if f not in ("up", "down") and j == 0:
        v += 1
    if f not in ("up", "down") and j >= h - 1 and e["rot"] is None:
        v -= 1                                     # where it sinks into the rock
    if contact(p, f, e):
        v -= 1
    k = hash01(fi(x * 2), fi(y * 2), fi(z * 2), FACES.index(f))
    if f not in ("up",) and j >= h - 2 and k < 0.45 and e["name"] in ("ore_front", "ore_right", "ore_back"):
        return PATINA[clamp(v - 1, 0, 3)]          # verdigris creeping up from the rock
    if w >= 4 and h >= 4 and f in ("north", "south", "west", "east"):
        # Grey rock caught in the ore, as 2 px clusters low on the bigger faces.
        if hash01(i // 2, j, len(e["name"]), FACES.index(f)) > 0.9 and j >= h // 2:
            return FLECK[clamp(v - 2, 0, 2)]
    return COPPER[clamp(v, 0, 6)]


def paint_nugget(e, f, p, i, j, w, h):
    v = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    if f == "up" and i == 0 and j == 0:
        v = 5
    return COPPER[v]


PAINTERS = {"rock": paint_rock, "ore": paint_ore, "nugget": paint_nugget}


def skyline_pack(rects, size):
    """Tighter than the shelf packer: tallest first, each rect goes where the
    skyline is lowest. Returns key -> (x, y), or None if it doesn't fit."""
    heights = [0] * size
    out = {}
    for key, w, h in sorted(rects, key=lambda r: (-r[2], -r[1])):
        best = None
        for x in range(size - w + 1):
            y = max(heights[x:x + w])
            if y + h <= size and (best is None or y < best[1]):
                best = (x, y)
        if best is None:
            return None
        x, y = best
        for k in range(x, x + w):
            heights[k] = y + h
        out[key] = (x, y)
    return out


# ---------------------------------------------------------------- preview

def rot_matrix(rx, ry, rz):
    """Blockbench/three.js Euler order ZYX: R = Rz . Ry . Rx."""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = [[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]]
    Ry = [[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]]
    Rz = [[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]]

    def mul(A, B):
        return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]
    return mul(Rz, mul(Ry, Rx))


def to_world(e, p):
    if not e["rot"]:
        return p
    R = rot_matrix(*e["rot"])
    piv = e["pivot"]
    d = [p[k] - piv[k] for k in range(3)]
    return tuple(piv[i] + sum(R[i][k] * d[k] for k in range(3)) for i in range(3))


def render(img, places, yaw, pitch, scale, size, silhouette=False):
    """Orthographic painter's render of every visible texel."""
    cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
    cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

    def proj(q):
        x, y, z = q
        x1, z1 = x * cy - z * sy, x * sy + z * cy
        y2, z2 = y * cp - z1 * sp, y * sp + z1 * cp
        return x1, y2, z2

    quads = []
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        o, u, v, w, h = face_frame(e, f)
        for j in range(int(h)):
            for i in range(int(w)):
                corners = []
                for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                    q = tuple(o[k] + (i + di) * u[k] + (j + dj) * v[k] for k in range(3))
                    corners.append(proj(to_world(e, q)))
                depth = sum(c[2] for c in corners) / 4
                col = (20, 20, 24, 255) if silhouette else img.getpixel((ox + i, oy + j))
                quads.append((depth, corners, col))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    cx, cyy = size[0] / 2, size[1] * 0.72
    for depth, corners, col in sorted(quads, key=lambda q: q[0]):
        d.polygon([(cx + c[0] * scale, cyy - c[1] * scale) for c in corners], fill=col)
    return out


# ---------------------------------------------------------------- build

def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    visible = {}
    for ei, e in enumerate(ELEMENTS):
        for f in FACES:
            if all(covered(p, f, e) for _, _, p in texels(e, f)):
                continue
            _, _, _, w, h = face_frame(e, f)
            visible[(ei, f)] = (int(w), int(h))

    rects = [(k, w, h) for k, (w, h) in visible.items()]
    for tex in (128, 256):
        places = skyline_pack(rects, tex)
        if places:
            break
    img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        w, h = visible[(ei, f)]
        for i, j, p in texels(e, f):
            img.putpixel((ox + i, oy + j), PAINTERS[e["part"]](e, f, p, i, j, w, h))

    tex_png = out_dir / "copper_vein.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, back-right, top-down three-quarter.
    views = [(-145, 25), (145, 25), (-35, 25), (35, 25), (-160, 60)]
    tiles = [render(img, places, yw, pt, 6, (360, 300)) for yw, pt in views]
    sheet = Image.new("RGBA", (360 * len(tiles), 300), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (360 * k, 0))
    sheet.save(out_dir / "copper_vein_preview.png")
    sil = Image.new("RGBA", (720, 300), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 25, 6, (360, 300), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 6, (360, 300), True), (360, 0))
    sil.save(out_dir / "copper_vein_silhouette.png")

    # ------------------------------------------------------------ .bbmodel
    def uid():
        return str(uuid.uuid4())

    def u(v):
        return round(v * PX, 4)

    groups = {g: [] for g in ("rock", "ore", "rubble")}
    elements = []
    for ei, e in enumerate(ELEMENTS):
        faces = {}
        for f in FACES:
            if (ei, f) in places:
                ox, oy = places[(ei, f)]
                w, h = visible[(ei, f)]
                faces[f] = {"uv": [ox, oy, ox + w, oy + h], "texture": 0}
            else:
                faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
        x = {
            "name": e["name"], "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": [u(v) for v in e["lo"]], "to": [u(v) for v in e["hi"]],
            "autouv": 0, "color": {"rock": 0, "ore": 1, "rubble": 2}[e["group"]],
            "origin": [u(v) for v in (e["pivot"] or (0, 0, 0))],
            "faces": faces, "type": "cube", "uuid": uid(),
        }
        if e["rot"]:
            x["rotation"] = list(e["rot"])
        elements.append(x)
        groups[e["group"]].append(x["uuid"])

    # Scale dummy: hidden and never exported. Height is a PLACEHOLDER taken from
    # the Three.js test character (models/character.glb, ~1.13 m = 18 units)
    # until the Imp's height is decided (MODELS-BLOCKBENCH open question 1).
    dummy = {
        "name": "scale_dummy_imp_placeholder", "box_uv": False, "rescale": False,
        "locked": True, "light_emission": 0, "render_order": "default",
        "allow_mirror_modeling": True, "export": False, "visibility": False,
        "from": [14, 0, -2], "to": [18, 18, 2], "autouv": 0, "color": 1,
        "origin": [16, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    elements.append(dummy)

    def group(name, children, export=True, visibility=True):
        return {"name": name, "origin": [0, 0, 0], "rotation": [0, 0, 0], "color": 0,
                "uuid": uid(), "export": export, "mirror_uv": False, "isOpen": name != "rock",
                "locked": False, "visibility": visibility, "autouv": 0, "children": children}

    outliner = [
        group("copper_vein", [group(g, groups[g]) for g in ("rock", "ore", "rubble")]),
        group("scale_dummy", [dummy["uuid"]], export=False, visibility=False),
    ]

    buf = io.BytesIO()
    img.save(buf, "PNG")
    texture = {
        "path": str(tex_png.resolve()), "name": tex_png.name, "folder": "",
        "namespace": "", "id": "0", "group": "", "width": tex, "height": tex,
        "uv_width": tex, "uv_height": tex, "particle": False,
        "use_as_default": False, "layers_enabled": False, "sync_to_project": "",
        "render_mode": "default", "render_sides": "auto", "pbr_channel": "color",
        "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
        "frame_interpolate": False, "visible": True, "internal": True,
        "saved": True, "uuid": uid(),
        "relative_path": tex_png.name,
        "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
    }
    model = {
        "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
        "name": "copper_vein", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": tex, "height": tex},
        "elements": elements, "outliner": outliner, "textures": [texture],
    }
    (out_dir / "copper_vein.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    rock = sum(1 for e in ELEMENTS if e["group"] == "rock")
    print(f"boxes: {len(ELEMENTS)} (rock {rock}, ore {len(ORE)}, rubble {len(RUBBLE)})  "
          f"visible faces: {len(visible)}  texture: {tex}x{tex}  texels used: {used}/{tex * tex}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
