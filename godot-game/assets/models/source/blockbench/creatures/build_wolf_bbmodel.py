"""Build the Blockbench grey wolf (Generic Model), the tier 4 hunting animal (D-032).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m.
- Box sizes in whole texture pixels (0.5 units). Odd widths for the centred
  parts (body, head, muzzle, nose, ruff) so the face has a centre column.
- Per-face UV, one texture inside the small-creature budget, hidden faces removed.
- Lit from the top, slightly front-left; edge highlights on lit edges, painted
  shadow where parts meet, fur in clusters that follow the lie of the fur,
  fringe pixels on the belly, cheeks, ruff and tail (BLOCKBENCH-STUDY 3.1, 5.3).
- Colours from the wolf icons (MODELS-BLOCKBENCH 4.3): the fur and belly ramps
  from sprites/items/hide_wolf.png, the teeth from trophy_wolf_fang.png. The
  amber eyes are the accent; there is no glow (it is an animal, not a demon).
- Bones use the shared creature names, pivots at the joints. The bushy tail is
  a three-bone chain (tail, tail_mid, tail_tip) so it can sway with lag, and
  the jaw is its own bone for the bite. Animations: idle, walk, run, attack, hit.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground, the wolf faces north (-z), its right side is +x.

Usage: python build_wolf_bbmodel.py [out_dir]   (writes wolf.bbmodel, wolf.png,
wolf_preview.png and wolf_silhouette.png)
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
from build_pickaxe_bbmodel import FACES, NORMAL, face_frame, pack, texels  # noqa: E402

TEX = 128  # texture size in pixels (MODELS-BLOCKBENCH 7, small creature)
PX = 0.5   # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


# Ramps, darkest first. FUR and CREAM are the hide icon's own colours; their
# shadows already lean blue-violet and the cream highlights lean warm. Each
# ramp sits one step down the icon's (its lightest shade dropped, one darker
# hue-shifted shade added) because the game's sun washed the first Godot test
# out to white and pale blue.
FUR = ramp("#1f1f27", "#2a2a30", "#45464e", "#666870", "#8c8e96")
SADDLE = ramp("#17111d", "#1d1724", "#2d2734", "#45464e", "#666870")   # the dark back, one step down
CREAM = ramp("#5e4a3e", "#7a6450", "#a88e74", "#cdb698", "#e8d8c0")
FANG = ramp("#6a5a48", "#9a8670", "#c4b298", "#e2d4bc")
NOSE = ramp("#17111d", "#241f2b", "#45464e", "#8c8e96")
AMBER = ramp("#7e5628", "#c88a2c", "#f0b43c", "#ffdd70")                # the accent
PUPIL = hexrgb("#17111d")
MOUTH = ramp("#3a1a2c", "#5e2a40", "#a8505f", "#cf7480")                # gums and tongue

FACE_SHADE = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi):
    return {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}


def legs():
    out = []
    for side, s in (("right", 1), ("left", -1)):
        def xs(a, b):
            return (a, b) if s > 0 else (-b, -a)
        fx, px_, tx = xs(1.5, 5.5), xs(1, 6), xs(2, 6.5)
        out += [
            # Forelegs: long and straight, 2 px hidden in the chest.
            el(f"leg_front_{side}", f"leg_front_{side}", "leg",
               (fx[0], 2, -9), (fx[1], 12, -5)),
            el(f"paw_front_{side}", f"leg_front_{side}", "paw",
               (px_[0], 0, -10), (px_[1], 2, -5)),
            # Hind legs: a heavy haunch over a lean shank.
            el(f"thigh_{side}", f"leg_back_{side}", "thigh",
               (tx[0], 8, 1.5), (tx[1], 16, 8.5)),
            el(f"leg_back_{side}", f"leg_back_{side}", "leg",
               (fx[0], 2, 3), (fx[1], 9, 7)),
            el(f"paw_back_{side}", f"leg_back_{side}", "paw",
               (px_[0], 0, 2), (px_[1], 2, 7)),
        ]
    return out


ELEMENTS = [
    # Body: a deep chest and shoulders in front of a leaner waist, a rounded
    # spine cap, and a thick ruff round the neck.
    el("body", "body", "fur", (-5.5, 11, -10.5), (5.5, 21, 8.5)),
    el("body_back", "body", "fur", (-4.5, 21, -9.5), (4.5, 22, 7.5)),
    el("chest", "body", "fur", (-6.5, 10, -11.5), (6.5, 22, -3.5)),
    el("ruff", "body", "ruff", (-7.5, 12, -13.5), (7.5, 23, -9.5)),
    # Head: broad skull, cheek fluff, a long muzzle, a nose that overhangs.
    el("head", "head", "fur", (-5.5, 16, -19.5), (5.5, 25, -12.5)),
    el("cheek_fluff", "head", "cheek", (-6.5, 16, -17.5), (6.5, 21, -13.5)),
    el("muzzle", "head", "muzzle", (-2.5, 16, -25.5), (2.5, 20, -19.5)),
    el("nose", "head", "nose", (-1.5, 19, -26.5), (1.5, 21, -24.5)),
    el("fang_right", "head", "fang", (1.5, 15, -25), (2.5, 16, -24)),
    el("fang_left", "head", "fang", (-2.5, 15, -25), (-1.5, 16, -24)),
    el("jaw", "jaw", "jaw", (-1.5, 14, -24.5), (1.5, 16, -18.5)),
    # Ears: tall and pointed, a 3 px base and a 1 px tip, tilted out.
    el("ear_right", "ear_right", "ear", (2.5, 25, -16.5), (5.5, 29, -14.5)),
    el("ear_right_tip", "ear_right", "ear", (3.5, 29, -16), (4.5, 30, -15)),
    el("ear_left", "ear_left", "ear", (-5.5, 25, -16.5), (-2.5, 29, -14.5)),
    el("ear_left_tip", "ear_left", "ear", (-4.5, 29, -16), (-3.5, 30, -15)),
    # Tail: thin at the root, bushy in the middle, tapering to a dark tip.
    el("tail_1", "tail", "tail", (-1.5, 17.5, 8.5), (1.5, 20.5, 13.5)),
    el("tail_2", "tail_mid", "tail", (-3.5, 15.5, 12.5), (3.5, 22.5, 20.5)),
    el("tail_3", "tail_tip", "tail", (-2.5, 16.5, 19.5), (2.5, 21.5, 25.5)),
    el("tail_end", "tail_tip", "tail", (-1.5, 17.5, 25.5), (1.5, 20.5, 27.5)),
] + legs()

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "wolf": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("wolf", (0, 16, 0), (0, 0, 0)),
    "head": ("body", (0, 19, -12.5), (0, 0, 0)),
    "jaw": ("head", (0, 16, -18.5), (0, 0, 0)),
    "ear_right": ("head", (4, 25, -15.5), (-8, 0, -12)),
    "ear_left": ("head", (-4, 25, -15.5), (-8, 0, 12)),
    # Wolves carry the tail low: the chain droops and curls out at the end.
    "tail": ("body", (0, 19, 8.5), (40, 0, 0)),
    "tail_mid": ("tail", (0, 19, 13), (10, 0, 0)),
    "tail_tip": ("tail_mid", (0, 19, 20), (-22, 0, 0)),
    "leg_front_right": ("wolf", (3.5, 11, -7), (0, 0, 0)),
    "leg_front_left": ("wolf", (-3.5, 11, -7), (0, 0, 0)),
    "leg_back_right": ("wolf", (4, 13, 5), (0, 0, 0)),
    "leg_back_left": ("wolf", (-4, 13, 5), (0, 0, 0)),
}
ROTATED = {"ear_right", "ear_left", "tail", "tail_mid", "tail_tip"}


def inside(p, e, eps=1e-6):
    return all(e["lo"][k] + eps < p[k] < e["hi"][k] - eps for k in range(3))


def solid(q, me, group=None):
    """True if q is inside another element. Unrotated elements test against
    each other; elements of a rotated bone only against their own bone."""
    for e in ELEMENTS:
        if e is me:
            continue
        if group is None and e["bone"] not in ROTATED and inside(q, e):
            return True
        if group is not None and e["bone"] == group and inside(q, e):
            return True
    return False


def scope(me):
    return me["bone"] if me["bone"] in ROTATED else None


def covered(p, f, me):
    n = NORMAL[f]
    return solid(tuple(p[k] + 0.25 * n[k] for k in range(3)), me, scope(me))


def tangents(f):
    n = NORMAL[f]
    return [t for t in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if not any(t[k] and n[k] for k in range(3))]


def contact(p, f, me):
    """Painted shadow: the texel sits right next to another part."""
    n = NORMAL[f]
    q = [p[k] + 0.5 * n[k] for k in range(3)]
    for t in tangents(f):
        for s in (-1, 1):
            if solid(tuple(q[k] + s * t[k] for k in range(3)), me, scope(me)):
                return True
    return False


# ---------------------------------------------------------------- markings

def fi(v):
    return math.floor(v)


def jag(k):
    """A fixed 0/1/0/-1 rhythm for fringe edges: tufts, not noise."""
    return (0, 1, 0, -1, 1, 0)[k % 6]


def saddle(e, f, p):
    """The dark saddle over the back and shoulders, with a tufted edge."""
    x, y, z = p
    if e["name"] in ("body_back",):
        return True
    if e["name"] in ("body", "chest") and f == "up":
        return abs(x) < 4 + 0.5 * jag(fi(z))
    if e["name"] in ("body", "chest") and f in ("west", "east"):
        return y >= 19 + jag(fi(z)) - (1 if -9 <= z <= 2 else 0)
    if e["name"] == "ruff" and f == "up":
        return abs(x) < 3.5 + 0.5 * jag(fi(z))
    if e["name"] == "head" and f == "up":
        return abs(x) < 2 + 0.5 * jag(fi(z))      # dark stripe down the forehead
    return False


def belly(e, f, p):
    """Cream underside rising into the grey with a fringe edge."""
    x, y, z = p
    if f == "down":
        return True
    if e["name"] == "body" and f in ("west", "east"):
        return y < 13 + jag(fi(z))
    if e["name"] == "chest" and f in ("west", "east"):
        return y < 12.5 + jag(fi(z))
    if e["name"] == "chest" and f == "north":
        return y < 18 + jag(round(x)) and abs(x) < 4.5   # the pale bib
    return False


def fur_stroke(f, p, v):
    """Fur lies back and down: sparse 3 px strokes running along the body
    (along z on the flanks and the back, along x on the front and rear),
    on every third row and staggered, so they read as tufts, not texture."""
    x, y, z = p
    if f == "up":
        r, k = round(x) + 30, fi(z)
    else:
        r, k = fi(y), (fi(z) if f in ("west", "east") else round(x))
    if r % 3:
        return v
    if (k + 4 * (r // 3)) % 9 in (0, 1, 2):
        return v + 1 if (f == "up" or r >= 15) else v - 1
    return v


# ---------------------------------------------------------------- painting

def clamp(v, lo=0, hi=4):
    return max(lo, min(hi, v))


def base_shade(e, f, p, i, j):
    v = FACE_SHADE[f]
    if f == "up":
        if i == 0 or j == 0:
            v = 4
    elif f != "down" and j == 0:
        v += 1
    if contact(p, f, e):
        v -= 1
    return v


def paint_fur(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if e["name"] == "head" and f == "north":
        face = paint_face(x, y)
        if face:
            return face
    if e["name"] == "head" and f in ("west", "east") and y < 19:
        return CREAM[clamp(v)]                     # pale lower cheeks
    if f in ("west", "east", "north", "south", "up"):
        v = fur_stroke(f, p, v)
    if saddle(e, f, p):
        return SADDLE[clamp(v)]
    if belly(e, f, p):
        return CREAM[clamp(v - 1 if f != "down" else (1 if not contact(p, f, e) else 0))]
    return FUR[clamp(v)]


def paint_face(x, y):
    """The skull's front. Columns are x (-5..5), rows are y (16..24); the muzzle
    covers -2..2, 16..19. Amber eyes under a low brow, a dark forehead stripe,
    pale brow spots and a dark tear line: the grey-wolf mask."""
    c, r = round(x), fi(y)
    ac, s = abs(c), (1 if c > 0 else -1)
    if ac in (2, 3) and r in (20, 21):              # eyes, 2 x 2
        outer = ac == 3
        if r == 21:
            return AMBER[3] if (outer and c < 0) or (not outer and c > 0) else AMBER[2]
        return AMBER[1] if outer else PUPIL
    if (r == 22 and ac in (2, 3)) or (r == 21 and ac == 1):
        return SADDLE[1]                            # low, angled brow
    if ac == 4 and r in (19, 20):
        return SADDLE[1]                            # tear line under the eye
    if r == 23 and ac in (3, 4):
        return CREAM[3]                             # pale brow spots
    if ac <= 1 and r >= 22:
        return SADDLE[2] if r < 24 else SADDLE[3]   # forehead stripe
    if r <= 19 and ac >= 3:
        return CREAM[2] if r < 19 else CREAM[3]     # cheeks
    _ = s
    return None


def paint_cheek(e, f, p, i, j, w, h):
    """Cheek fluff: grey above, cream below, with tufts pointing back."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if f in ("west", "east"):
        if y < 18 + jag(fi(z) + 2):
            return CREAM[clamp(v)]
        return FUR[clamp(v + (1 if (fi(z) + fi(y)) % 3 == 0 else 0))]
    if f == "south":
        return FUR[clamp(v - (1 if y < 18 else 0))]
    if f == "down":
        return CREAM[1]
    return CREAM[clamp(v)] if y < 18.5 else FUR[clamp(v)]


def paint_ruff(e, f, p, i, j, w, h):
    """The neck ruff: the fluffiest fur, cream bib at the front."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if y < 16 + jag(round(x) + 1):
            return CREAM[clamp(v + (1 if round(x) % 3 == 0 else 0))]
        return FUR[clamp(v + (1 if (round(x) + fi(y)) % 4 == 0 else 0))]
    if f in ("west", "east"):
        if y < 15 + jag(fi(z) + 3):
            return CREAM[clamp(v - 1)]
        v = v + 1 if (fi(z) * 2 + fi(y)) % 5 == 0 else v   # tufts of lighter fur
    if saddle(e, f, p):
        return SADDLE[clamp(v)]
    if f == "down":
        return CREAM[0]
    return FUR[clamp(v)]


def paint_muzzle(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "down":
        return MOUTH[1]                            # roof of the mouth, seen when it opens
    if f == "up":
        if c == 0 and z > -24:
            return SADDLE[3]                       # the dark bridge of the nose
        return FUR[clamp(v)]
    if f == "north":
        if r == 16:
            return MOUTH[0]                        # lip line
        return CREAM[clamp(v + (1 if r == 18 else 0))]
    if r <= 17:
        return CREAM[clamp(v)]                     # pale lips and chin
    if r == 18 and ((fi(z) % 2) == 0):
        return SADDLE[2]                           # whisker spots
    return FUR[clamp(v)]


def paint_nose(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    if f == "up":
        return NOSE[3] if (i == 0 and j == h - 1) else NOSE[2]   # wet glint, lit corner
    if f == "north":
        if r == 19 and abs(c) == 1:
            return NOSE[0]                         # nostrils
        return NOSE[2] if r == 20 else NOSE[1]
    return NOSE[1 if f in ("west", "south") else 0]


def paint_fang(e, f, p, i, j, w, h):
    return FANG[{"up": 3, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]]


def paint_jaw(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    if f == "up":                                  # inside of the mouth
        if c == 0 and z > -23.5:
            return MOUTH[3 if z < -21 else 2]      # tongue
        return MOUTH[0] if z > -22 else FANG[3]    # front teeth along the rim
    if f == "north":
        return FANG[3] if r == 15 and c != 0 else CREAM[1]
    if f == "down":
        return CREAM[0]
    return CREAM[2 if f == "west" else 1] if r == 14 else (FANG[2] if z < -23.5 and r == 15 else CREAM[2])


def paint_ear(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    if e["name"].endswith("tip"):
        return SADDLE[1 if f in ("east", "south") else 2]
    if f == "north":                               # inner ear: pale fluff round a dark hollow
        if i in (0, w - 1) or r >= 28:
            return FUR[3] if r < 28 else SADDLE[2]
        return NOSE[1] if r >= 26 else CREAM[2]
    if f == "south":
        return SADDLE[2] if r >= 27 else FUR[1]
    if f == "up":
        return SADDLE[3]
    v = FACE_SHADE[f] + (1 if r >= 28 else 0)
    return SADDLE[clamp(v)] if r >= 27 else FUR[clamp(v)]


def paint_leg(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    front = e["name"].startswith("leg_front")
    cx = (e["lo"][0] + e["hi"][0]) / 2
    if r >= (10 if front else 8) - 1:
        v -= 1                                     # shadow under the body
    if front and f == "north" and 4 <= r <= 9 and abs(x - cx) < 1:
        return SADDLE[clamp(v)]                    # the dark stripe down a grey wolf's foreleg
    inner = (f == "west" and x > 0) or (f == "east" and x < 0)
    if inner or f == "south" or r <= 3:
        return CREAM[clamp(v - 1 + (1 if r <= 3 else 0))]
    if f in ("west", "east") and r % 3 == 0 and (fi(z) + r) % 2 == 0:
        v -= 1                                     # fur clusters
    return FUR[clamp(v)]


def paint_thigh(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    outer = (f == "east" and x > 0) or (f == "west" and x < 0)
    if outer and 11 <= y < 14 and 3 <= z < 7:
        v += 1                                     # the haunch catches the light
    if f == "south":
        return CREAM[clamp(v - (1 if y < 11 + jag(round(x)) else 0))]   # pale trousers
    if f in ("west", "east"):
        v = fur_stroke(f, p, v)
        if y < 9 + jag(fi(z)):
            return CREAM[clamp(v - 1)]
    if f == "down":
        return CREAM[0]
    return FUR[clamp(v)]


def paint_paw(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    if f == "down":
        return NOSE[1]                             # pads
    if f == "north" and r == 0:
        return FANG[2] if i % 2 == 0 else NOSE[1]  # claws between the toes
    if f == "up":
        return CREAM[3] if j == 0 else CREAM[2]
    v = {"north": 2, "west": 2, "south": 1, "east": 1}[f] + (1 if r == 1 else 0)
    return CREAM[clamp(v)]


def paint_tail(e, f, p, i, j, w, h):
    """Grey with a dark top stripe and tip, cream underneath, and fringe tufts
    along the lower edge of each side."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    seg = e["name"]
    tip = seg == "tail_end" or (seg == "tail_3" and (z > 23.5 + 0.5 * jag(fi(y)) or f == "south"))
    if tip:
        return SADDLE[clamp(v - 1)]
    if f == "down":
        return CREAM[2]
    if f == "up":
        return SADDLE[clamp(v - (0 if abs(x) < 1 else 1) + 1)] if abs(x) < 1.5 else FUR[clamp(v)]
    if f in ("west", "east"):
        lo = e["lo"][1]
        if y < lo + 1 + (0.5 + 0.5 * jag(fi(z)) if seg == "tail_2" else 0):
            return CREAM[clamp(v)]
        if (fi(z) + 2 * fi(y)) % 5 == 0:
            v += 1                                 # tufts
        if y > e["hi"][1] - 1:
            return SADDLE[clamp(v + 1)]
    return FUR[clamp(v)]


PAINTERS = {"fur": paint_fur, "ruff": paint_ruff, "cheek": paint_cheek, "muzzle": paint_muzzle,
            "nose": paint_nose, "fang": paint_fang, "jaw": paint_jaw, "ear": paint_ear,
            "leg": paint_leg, "thigh": paint_thigh, "paw": paint_paw, "tail": paint_tail}


# ---------------------------------------------------------------- animation

def kf(channel, t, x, y, z, interp="catmullrom"):
    return {"channel": channel, "data_points": [{"x": x, "y": y, "z": z}],
            "uuid": str(uuid.uuid4()), "time": t, "color": -1, "interpolation": interp}


def track(channel, keys, interp="catmullrom"):
    return [kf(channel, t, *v, interp=interp) for t, v in keys]


def rot(*keys):
    return track("rotation", keys)


def sway(length, amp, phase, axis=1, base=(0, 0, 0)):
    """A looping sine sway in 8 keys, phase in cycles (for tail lag)."""
    out = []
    for k in range(9):
        t = length * k / 8
        a = amp * math.sin(2 * math.pi * (k / 8 - phase))
        v = list(base)
        v[axis] += round(a, 2)
        out.append((round(t, 4), tuple(v)))
    return track("rotation", out)


# Rotations are in Blockbench's animation convention: a positive x turns the
# head's snout down, swings a foot backward, opens the jaw and lifts the tail.
ANIMATIONS = {
    # Alert idle: breathing, a slow look round, ear flicks, panting, and a
    # tail sway that ripples down the chain.
    "idle": {"loop": "loop", "length": 2.4, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.2, (1.012, 1.02, 1.0)), (2.4, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.6, (-2, 6, 2)), (1.2, (1, 0, 0)), (1.8, (-2, -6, -2)),
                    (2.4, (0, 0, 0))),
        "jaw": rot(*[(round(0.3 * k, 2), (5 if k % 2 else 1, 0, 0)) for k in range(9)]),
        "ear_right": rot((0, (0, 0, 0)), (1.5, (0, 0, 0)), (1.6, (-10, 0, -8)), (1.75, (2, 0, 2)),
                         (1.9, (0, 0, 0)), (2.4, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.5, (0, 0, 0)), (0.6, (-8, 0, 8)), (0.75, (2, 0, -2)),
                        (0.9, (0, 0, 0)), (2.4, (0, 0, 0))),
        "tail": sway(2.4, 8, 0.0),
        "tail_mid": sway(2.4, 10, 0.1),
        "tail_tip": sway(2.4, 14, 0.2),
    }},
    # Trot: diagonal pairs, body bob twice per cycle, head nod, tail sway.
    "walk": {"loop": "loop", "length": 0.9, "bones": {
        "leg_front_right": rot((0, (-24, 0, 0)), (0.45, (24, 0, 0)), (0.9, (-24, 0, 0))),
        "leg_back_left": rot((0, (-20, 0, 0)), (0.45, (20, 0, 0)), (0.9, (-20, 0, 0))),
        "leg_front_left": rot((0, (24, 0, 0)), (0.45, (-24, 0, 0)), (0.9, (24, 0, 0))),
        "leg_back_right": rot((0, (20, 0, 0)), (0.45, (-20, 0, 0)), (0.9, (20, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.225, (0, 0.5, 0)), (0.45, (0, 0, 0)),
                                   (0.675, (0, 0.5, 0)), (0.9, (0, 0, 0))])
        + rot((0, (0, 0, 1.5)), (0.45, (0, 0, -1.5)), (0.9, (0, 0, 1.5))),
        "head": rot((0, (0, 0, 0)), (0.225, (3, 0, 0)), (0.45, (0, 0, 0)), (0.675, (3, 0, 0)),
                    (0.9, (0, 0, 0))),
        "tail": sway(0.9, 10, 0.0),
        "tail_mid": sway(0.9, 12, 0.12),
        "tail_tip": sway(0.9, 14, 0.24),
    }},
    # Gallop: front pair and back pair reach and push together, half a beat
    # apart; the spine flexes, the head stays level, ears back, tail streams.
    "run": {"loop": "loop", "length": 0.5, "bones": {
        "leg_front_right": rot((0, (-45, 0, 0)), (0.25, (40, 0, 0)), (0.5, (-45, 0, 0))),
        "leg_front_left": rot((0, (-40, 0, 0)), (0.25, (45, 0, 0)), (0.5, (-40, 0, 0))),
        "leg_back_right": rot((0, (40, 0, 0)), (0.25, (-40, 0, 0)), (0.5, (40, 0, 0))),
        "leg_back_left": rot((0, (45, 0, 0)), (0.25, (-35, 0, 0)), (0.5, (45, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.125, (0, 1.2, 0)), (0.25, (0, 0, 0)),
                                   (0.375, (0, 0.6, 0)), (0.5, (0, 0, 0))])
        + rot((0, (-6, 0, 0)), (0.25, (6, 0, 0)), (0.5, (-6, 0, 0))),
        "head": rot((0, (8, 0, 0)), (0.25, (-4, 0, 0)), (0.5, (8, 0, 0))),
        "jaw": rot((0, (12, 0, 0)), (0.25, (16, 0, 0)), (0.5, (12, 0, 0))),
        "ear_right": rot((0, (-28, 0, 0)), (0.5, (-28, 0, 0))),
        "ear_left": rot((0, (-28, 0, 0)), (0.5, (-28, 0, 0))),
        "tail": rot((0, (25, 0, 0)), (0.25, (30, 0, 0)), (0.5, (25, 0, 0))),
        "tail_mid": rot((0, (8, 0, 0)), (0.25, (2, 0, 0)), (0.5, (8, 0, 0))),
        "tail_tip": rot((0, (12, 0, 0)), (0.25, (4, 0, 0)), (0.5, (12, 0, 0))),
    }},
    # Lunge and bite: crouch with the jaw opening (anticipation), spring
    # forward with the jaw wide, snap it shut, overshoot, settle.
    "attack": {"loop": "once", "length": 0.8, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.28, (0, -1.0, 1.5)), (0.4, (0, 0.6, -3.5)),
                                   (0.5, (0, 0, -3.0)), (0.8, (0, 0, 0))])
        + rot((0, (0, 0, 0)), (0.28, (4, 0, 0)), (0.4, (-6, 0, 0)), (0.5, (2, 0, 0)), (0.8, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.28, (10, 0, 0)), (0.4, (-12, 0, 0)), (0.46, (8, 0, 0)),
                    (0.8, (0, 0, 0))),
        "jaw": track("rotation", [(0, (0, 0, 0)), (0.28, (14, 0, 0)), (0.4, (35, 0, 0)), (0.44, (0, 0, 0)),
                           (0.8, (0, 0, 0))], interp="linear"),
        "leg_front_right": rot((0, (0, 0, 0)), (0.28, (12, 0, 0)), (0.4, (-40, 0, 0)), (0.8, (0, 0, 0))),
        "leg_front_left": rot((0, (0, 0, 0)), (0.28, (12, 0, 0)), (0.4, (-35, 0, 0)), (0.8, (0, 0, 0))),
        "leg_back_right": rot((0, (0, 0, 0)), (0.28, (-15, 0, 0)), (0.4, (30, 0, 0)), (0.8, (0, 0, 0))),
        "leg_back_left": rot((0, (0, 0, 0)), (0.28, (-15, 0, 0)), (0.4, (30, 0, 0)), (0.8, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.28, (-25, 0, 0)), (0.5, (-15, 0, 0)), (0.8, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.28, (-25, 0, 0)), (0.5, (-15, 0, 0)), (0.8, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.28, (15, 0, 0)), (0.4, (25, 0, 0)), (0.8, (0, 0, 0))),
    }},
    # Hit: recoil and squash, head jerks aside, ears flatten, tail tucks.
    "hit": {"loop": "once", "length": 0.4, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.07, (0, 0, 1.5)), (0.2, (0, 0, -0.3)),
                                   (0.4, (0, 0, 0))])
        + track("scale", [(0, (1, 1, 1)), (0.07, (1.06, 0.92, 1.04)), (0.2, (0.98, 1.03, 0.99)),
                          (0.4, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.07, (-14, 10, 6)), (0.2, (3, -2, -1)), (0.4, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.07, (18, 0, 0)), (0.4, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.07, (-35, 0, -10)), (0.4, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.07, (-35, 0, 10)), (0.4, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.07, (-25, 0, 0)), (0.4, (0, 0, 0))),
    }},
}


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


def to_world(bone, p):
    """Rest-pose position of a bone-local point (px)."""
    while bone:
        parent, piv, r = BONES[bone]
        if any(r):
            R = rot_matrix(*r)
            d = [p[k] - piv[k] for k in range(3)]
            p = tuple(piv[i] + sum(R[i][k] * d[k] for k in range(3)) for i in range(3))
        bone = parent
    return p


def render(img, places, yaw, pitch, scale, size, silhouette=False):
    """Orthographic painter's render of every visible texel (rest pose)."""
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
                    corners.append(proj(to_world(e["bone"], q)))
                depth = sum(c[2] for c in corners) / 4
                col = (20, 20, 24, 255) if silhouette else img.getpixel((ox + i, oy + j))
                quads.append((depth, corners, col))
    out = Image.new("RGBA", size, (0, 0, 0, 0))
    d = ImageDraw.Draw(out)
    cx, cyy = size[0] / 2, size[1] * 0.8
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

    places = pack([(k, w, h) for k, (w, h) in visible.items()], TEX)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        w, h = visible[(ei, f)]
        for i, j, p in texels(e, f):
            img.putpixel((ox + i, oy + j), PAINTERS[e["part"]](e, f, p, i, j, w, h))

    tex_png = out_dir / "wolf.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, left side, front (the wolf faces -z).
    views = [(-145, 22), (145, 22), (-35, 22), (-90, 0), (180, 0)]
    tiles = [render(img, places, yw, pt, 7, (360, 320)) for yw, pt in views]
    sheet = Image.new("RGBA", (360 * len(tiles), 320), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (360 * k, 0))
    sheet.save(out_dir / "wolf_preview.png")
    sil = Image.new("RGBA", (720, 320), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 22, 7, (360, 320), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 7, (360, 320), True), (360, 0))
    sil.save(out_dir / "wolf_silhouette.png")

    # ------------------------------------------------------------ .bbmodel
    def uid():
        return str(uuid.uuid4())

    def u(v):
        return round(v * PX, 4)

    bone_uuid = {b: uid() for b in BONES}
    children = {b: [] for b in BONES}
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
            # A box named like its bone gets "_box", so Godot's nodes stay unique.
            "name": e["name"] + ("_box" if e["name"] in BONES else ""),
            "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": [u(v) for v in e["lo"]], "to": [u(v) for v in e["hi"]],
            "autouv": 0, "color": 0, "origin": [u(v) for v in BONES[e["bone"]][1]],
            "faces": faces, "type": "cube", "uuid": uid(),
        }
        elements.append(x)
        children[e["bone"]].append(x["uuid"])

    # Scale dummy: hidden and never exported. Height is a PLACEHOLDER taken from
    # the Three.js test character (models/character.glb, ~1.13 m = 18 units)
    # until the Imp's height is decided (MODELS-BLOCKBENCH open question 1).
    dummy = {
        "name": "scale_dummy_imp_placeholder", "box_uv": False, "rescale": False,
        "locked": True, "light_emission": 0, "render_order": "default",
        "allow_mirror_modeling": True, "export": False, "visibility": False,
        "from": [10, 0, -2], "to": [14, 18, 2], "autouv": 0, "color": 1,
        "origin": [12, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    elements.append(dummy)

    def group(name):
        _, piv, r = BONES[name]
        kids = [group(b) for b, (parent, _, _) in BONES.items() if parent == name]
        return {"name": name, "origin": [u(v) for v in piv], "rotation": list(r),
                "color": 0, "uuid": bone_uuid[name], "export": True, "mirror_uv": False,
                "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
                "children": children[name] + kids}

    outliner = [
        group("wolf"),
        {"name": "scale_dummy", "origin": [12, 0, 0], "rotation": [0, 0, 0], "color": 0,
         "uuid": uid(), "export": False, "mirror_uv": False, "isOpen": False,
         "locked": False, "visibility": False, "autouv": 0, "children": [dummy["uuid"]]},
    ]

    animations = []
    for name, a in ANIMATIONS.items():
        animators = {}
        for bone, keys in a["bones"].items():
            for k in keys:
                if k["channel"] == "position":   # authored in px, stored in units
                    k["data_points"] = [{ax: round(val * PX, 4) for ax, val in k["data_points"][0].items()}]
            animators[bone_uuid[bone]] = {"name": bone, "type": "bone", "keyframes": keys}
        animations.append({
            "uuid": uid(), "name": name, "loop": a["loop"], "override": False,
            "length": a["length"], "snapping": 24, "selected": False,
            "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
            "animators": animators,
        })

    buf = io.BytesIO()
    img.save(buf, "PNG")
    texture = {
        "path": str(tex_png.resolve()), "name": tex_png.name, "folder": "",
        "namespace": "", "id": "0", "group": "", "width": TEX, "height": TEX,
        "uv_width": TEX, "uv_height": TEX, "particle": False,
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
        "name": "wolf", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": TEX, "height": TEX},
        "elements": elements, "outliner": outliner, "textures": [texture],
        "animations": animations,
    }
    (out_dir / "wolf.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(ELEMENTS)}  bones: {len(BONES)}  visible faces: {len(visible)}  "
          f"texels used: {used}/{TEX * TEX}  animations: {', '.join(ANIMATIONS)}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
