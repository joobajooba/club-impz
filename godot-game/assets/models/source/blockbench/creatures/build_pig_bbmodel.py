"""Build the Blockbench pig: a small, round, friendly piglet (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m.
- Box sizes in whole texture pixels (0.5 units). Odd widths for the centred
  parts (body, head, snout, tuft) so the face has a centre column.
- Per-face UV, one 64x64 texture (inside the 128x128 small-creature budget),
  hidden faces removed.
- Lit from the top, slightly front-left; hue-shifted ramps (shadows toward
  plum, highlights toward peach), edge highlights on lit edges, painted shadow
  where parts meet, markings that follow the form, clusters not noise.
- Big friendly face (BLOCKBENCH-STUDY 3.1): painted dark eyes with a warm
  glint on a pale face, a saturated snout as the accent, floppy folded ears.
- Bones use the shared creature names (body, head, ear_*, leg_*, tail) and
  pivots sit at the joints. Animations: idle, walk, run, attack, hit.

There is no icon for a pig, so the colours come from ART-DIRECTION section 5
(the warm creature swatches and the dirt swatch #6A5667 for mud), with the
hue-shift rules of MODELS-BLOCKBENCH 4.3.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground, the pig faces north (-z), its right side is +x.

Usage: python build_pig_bbmodel.py [out_dir]   (writes pig.bbmodel, pig.png,
pig_preview.png and pig_silhouette.png)
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

TEX = 64   # texture size in pixels: everything fits, under the 128 budget (MODELS-BLOCKBENCH 7)
PX = 0.5   # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


# Ramps, darkest first. Shadows lean plum, highlights lean peach. The skin and
# patch ramps were pulled down a step after the first Godot test: the game's
# sun washed the top faces out to near white.
SKIN = ramp("#713859", "#a5566f", "#d0808b", "#e6a39b", "#f5c6b1")
PATCH = ramp("#472a41", "#673b53", "#865262", "#a87274", "#c39282")   # brown-mauve spots
SNOUT = ramp("#86325a", "#c2507a", "#ee7f98", "#ffa8b0", "#ffd4c8")   # the accent
INNER = ramp("#7c2f55", "#b24a70", "#dc7088", "#f59aa6")              # inside the ears
HOOF = ramp("#2e2236", "#493444", "#6a4b57", "#8e6b70")
MUD = ramp("#3e3140", "#584555", "#6a5667", "#86717d")                # ART-DIRECTION dirt
EYE_DARK = hexrgb("#231a34")
EYE_IRIS = hexrgb("#41376a")
EYE_GLINT = hexrgb("#fff5e4")   # the single near-white pixel per eye
NOSTRIL = ramp("#3b1631", "#5a2346")
MOUTH = hexrgb("#8a3f60")

# Face brightness on the 5-step ramps: light from the top, front (north) and
# the pig's left (west).
FACE_SHADE = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi):
    return {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}


ELEMENTS = [
    # Body: 13 wide, 10 tall, 15 long, with a narrower cap on top so the back
    # reads round (a stepped bevel, MODELS-BLOCKBENCH 10.4).
    el("body", "body", "skin", (-6.5, 4, -7.5), (6.5, 14, 7.5)),
    el("body_back", "body", "skin", (-5.5, 14, -6.5), (5.5, 15, 6.5)),
    # Head: oversized for charm, 11 wide, 10 tall, 8 deep, 1 px into the body.
    el("head", "head", "skin", (-5.5, 6, -14.5), (5.5, 16, -6.5)),
    # A cap and two jowls round the head off, as the back cap does the body.
    el("head_top", "head", "skin", (-4.5, 16, -13.5), (4.5, 17, -7.5)),
    el("cheek_right", "head", "skin", (5.5, 7, -13.5), (6.5, 10, -10.5)),
    el("cheek_left", "head", "skin", (-6.5, 7, -13.5), (-5.5, 10, -10.5)),
    el("snout", "head", "snout", (-3.5, 7, -16.5), (3.5, 11, -14.5)),
    # A cowlick of bristles, set off-centre toward the light.
    el("tuft", "head", "tuft", (-1.5, 17, -12.5), (1.5, 18, -9.5)),
    el("tuft_top", "head", "tuft", (-1.5, 18, -11.5), (0.5, 19, -9.5)),
    # Ears: a 4 x 5 flap resting on each top corner of the head, angled out,
    # and a 2 px tip that flops forward over the brow.
    el("ear_right", "ear_right", "ear", (3.5, 17, -13.5), (7.5, 18, -8.5)),
    el("ear_right_tip", "ear_right_tip", "ear", (3.5, 17, -15.5), (7.5, 18, -13.5)),
    el("ear_left", "ear_left", "ear", (-7.5, 17, -13.5), (-3.5, 18, -8.5)),
    el("ear_left_tip", "ear_left_tip", "ear", (-7.5, 17, -15.5), (-3.5, 18, -13.5)),
    # Legs: 5 wide, 4 deep, 2 px hidden in the body so a swing never opens a gap.
    el("leg_front_right", "leg_front_right", "leg", (1, 0, -6.5), (6, 6, -2.5)),
    el("leg_front_left", "leg_front_left", "leg", (-6, 0, -6.5), (-1, 6, -2.5)),
    el("leg_back_right", "leg_back_right", "leg", (1, 0, 2.5), (6, 6, 6.5)),
    el("leg_back_left", "leg_back_left", "leg", (-6, 0, 2.5), (-1, 6, 6.5)),
    # Curly tail, 2 px thick: out, up, and hooked back over.
    el("tail_1", "tail", "skin", (-1, 11, 7.5), (1, 12, 10.5)),
    el("tail_2", "tail", "skin", (-1, 12, 9.5), (1, 14, 10.5)),
    el("tail_3", "tail", "skin", (-1, 13, 8.5), (1, 14, 9.5)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "pig": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("pig", (0, 9, 0), (0, 0, 0)),
    "head": ("body", (0, 10, -7.5), (0, 0, 0)),
    "ear_right": ("head", (3.5, 17, -8.5), (10, -10, -32)),
    "ear_right_tip": ("ear_right", (5.5, 17, -13.5), (-70, 0, 0)),
    "ear_left": ("head", (-3.5, 17, -8.5), (10, 10, 32)),
    "ear_left_tip": ("ear_left", (-5.5, 17, -13.5), (-70, 0, 0)),
    "tail": ("body", (0, 11.5, 7.5), (0, 0, 0)),
    "leg_front_right": ("pig", (3.5, 5, -4.5), (0, 0, 0)),
    "leg_front_left": ("pig", (-3.5, 5, -4.5), (0, 0, 0)),
    "leg_back_right": ("pig", (3.5, 5, 4.5), (0, 0, 0)),
    "leg_back_left": ("pig", (-3.5, 5, 4.5), (0, 0, 0)),
}
ROTATED = {"ear_right", "ear_right_tip", "ear_left", "ear_left_tip"}


def inside(p, e, eps=1e-6):
    return all(e["lo"][k] + eps < p[k] < e["hi"][k] - eps for k in range(3))


def solid(q, me):
    """True if q is inside any unrotated element other than `me`."""
    return any(inside(q, e) for e in ELEMENTS if e is not me and e["bone"] not in ROTATED)


def covered(p, f, me):
    if me["bone"] in ROTATED:
        return False
    n = NORMAL[f]
    return solid(tuple(p[k] + 0.25 * n[k] for k in range(3)), me)


def tangents(f):
    n = NORMAL[f]
    return [t for t in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if not any(t[k] and n[k] for k in range(3))]


def contact(p, f, me):
    """Painted shadow: the texel sits right next to another part."""
    if me["bone"] in ROTATED:
        return False
    n = NORMAL[f]
    q = [p[k] + 0.5 * n[k] for k in range(3)]
    for t in tangents(f):
        for s in (-1, 1):
            if solid(tuple(q[k] + s * t[k] for k in range(3)), me):
                return True
    return False


# ---------------------------------------------------------------- markings

# Brown-mauve patches, as unions of blobs in 3D so they wrap round the form:
# one over the right eye and down the cheek, a saddle on the right of the
# back, and two small ones on the left. Clean edges, no speckle.
PATCHES = [
    ((3.8, 12.8, -14.5), (2.4, 2.2, 3.0)), ((5.8, 11.0, -12.0), (1.4, 1.6, 2.2)),
    ((4.0, 13.5, 1.5), (4.0, 3.2, 3.5)), ((2.0, 15.0, 4.0), (2.5, 1.2, 2.0)),
    ((-6.5, 9.0, -3.0), (2.0, 2.0, 2.2)),
    ((-4.5, 13.0, 5.5), (2.2, 2.0, 2.0)),
]


def in_patch(p):
    return any(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)) < 1.0 for c, r in PATCHES)


# Spine bristles on the back cap: three short pale strokes along the middle.
# (column x, first z row, length)
BRISTLES = [(0, -6, 2), (0, -2, 3), (0, 3, 2)]

# Mud splashes on the legs: (leg, face, column index from the face's left, row y).
MUD_SPOTS = {
    "leg_front_right": {("east", 0, 2), ("east", 1, 2), ("north", 4, 2), ("south", 0, 2)},
    "leg_front_left": {("west", 3, 2), ("north", 0, 2), ("north", 1, 2)},
    "leg_back_right": {("east", 1, 2), ("east", 2, 2), ("east", 2, 3), ("south", 3, 2),
                       ("south", 4, 2), ("north", 3, 2)},
    "leg_back_left": {("west", 0, 2), ("west", 1, 2), ("west", 1, 3), ("south", 1, 2),
                      ("south", 0, 2), ("north", 0, 2)},
}


# ---------------------------------------------------------------- painting

def clamp(v, lo=0, hi=4):
    return max(lo, min(hi, v))


def skin_shade(e, f, p, i, j, w, h):
    """Shade index on the 5-step skin ramp for a body/head/tail texel."""
    x, y, z = p
    v = FACE_SHADE[f]
    if f == "up":
        # Edge highlight on the lit edges (north and west), soft on the others.
        if i == 0 or j == 0:
            v = 4
    elif f != "down":
        if j == 0:
            v += 1                       # top-edge highlight
        if e["name"] == "body" and y < 7:
            v -= 1                       # belly band: lighter at the top, darker below
        elif e["name"] in ("head", "cheek_right", "cheek_left") and y < 7:
            v -= 1                       # chin in the head's own shadow
    else:
        v = 1 if e["name"] in ("body", "head") and not contact(p, f, e) else 0
    # Form shading on the flanks: a shoulder and a haunch catch the light.
    if e["name"] == "body" and f in ("west", "east"):
        if (-6 <= z <= -3 and 8.5 <= y <= 11) or (2.5 <= z <= 6 and 9 <= y <= 12):
            if not (z in (-6, 6) and y in (8.5, 11, 9, 12)):
                v += 1
    if e["name"] == "body" and f == "up":
        v = 4 if (i == 0 or j == 0) else 3   # the ring left round the back cap
    # Creases: behind the shoulder and in front of the haunch, short and curved.
    if e["name"] == "body" and f in ("west", "east"):
        if (round(z * 2) / 2 == -1.5 and 7 <= y < 10) or (round(z * 2) / 2 == 1.5 and 8 <= y < 11):
            v -= 1
    # Painted shadow of the ears on the top of the head.
    if e["name"] in ("head", "head_top") and f == "up" and 3 <= abs(x) <= 5.5 and -13 <= z <= -9:
        v -= 1
    if contact(p, f, e):
        v -= 1
    return clamp(v)


def paint_skin(e, f, p, i, j, w, h):
    x, y, z = p
    v = skin_shade(e, f, p, i, j, w, h)
    if e["name"] == "body_back" and f == "up":
        c, r = round(x), math.floor(z)
        for bc, bz, n in BRISTLES:
            if c == bc and bz <= r < bz + n:
                return PATCH[4] if in_patch(p) else SKIN[4]
    if e["name"] == "head" and f == "north":
        face = paint_face(x, y)
        if face:
            return face
    if e["bone"] != "tail" and in_patch(p):
        return PATCH[v]
    return SKIN[v]


def paint_face(x, y):
    """The head's front: wide-set eyes, brows, cheeks and a smile.
    Columns are x (-5..5), rows are y (6..15); the snout covers -3..3, 7..10."""
    c, r = round(x), math.floor(y)
    ac = abs(c)
    if ac in (3, 4) and 11 <= r <= 13:            # eyes, 2 wide and 3 tall
        if r == 13 and c in (-4, 3):
            return EYE_GLINT                       # glint on the side of the light
        if r == 11:
            return EYE_IRIS
        return EYE_DARK
    if r == 14 and ac in (3, 4):                   # brows: one shade darker
        return SKIN[1]
    if r == 14 and ac == 5:
        return SKIN[2]
    if r == 10 and ac in (4, 5):                   # cheek blush
        return SNOUT[3]
    if r == 6 and ac <= 1:
        return MOUTH                               # a small mouth under the snout
    return None


def paint_snout(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), math.floor(y)
    v = FACE_SHADE[f]
    if f == "north":
        if abs(c) == 2 and r in (8, 9):            # two upright oval nostrils
            return NOSTRIL[0] if r == 9 else NOSTRIL[1]
        if abs(c) == 1 and r == 9:
            v = 1
        if r == 10:
            v = 4 if c == -3 else 3                # lit rim, brightest corner
        elif r == 7:
            v = 1
    elif f == "up":
        v = 4 if j == h - 1 or i == 0 else 3       # front and left edges catch light
    elif f in ("west", "east") and j == 0:
        v += 1
    if contact(p, f, e):
        v -= 1
    return SNOUT[clamp(v)]


def paint_tuft(e, f, p, i, j, w, h):
    v = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    if f != "up" and j == h - 1 and e["name"] == "tuft":
        v -= 1                                     # root of the bristles
    return SKIN[clamp(v)]


def paint_ear(e, f, p, i, j, w, h):
    """Skin on top, rosy inside (the down face, which faces forward once the
    ear is raised and its tip folded), with a skin rim."""
    if f == "down":
        rim = i in (0, w - 1) or (e["name"].endswith("tip") and j == h - 1) or \
            (not e["name"].endswith("tip") and j == 0)
        if rim:
            return SKIN[2]
        deep = (e["name"].endswith("tip") and j == 0) or (not e["name"].endswith("tip") and j >= h - 2)
        return INNER[1 if deep else 2]
    if f == "up":
        outer_left = e["name"].startswith("ear_left")
        edge = (i == 0) if outer_left else (i == w - 1)
        return SKIN[4 if edge else 3]
    return SKIN[{"north": 2, "south": 1, "west": 2, "east": 1}[f]]


def paint_leg(e, f, p, i, j, w, h):
    x, y, z = p
    r = math.floor(y)
    if f == "down":
        return HOOF[0]
    if (f, i, r) in MUD_SPOTS[e["name"]]:
        return MUD[2 if f in ("north", "west") else 1]
    if r <= 1:                                     # hoof, 2 px tall
        cx = (e["lo"][0] + e["hi"][0]) / 2
        if f in ("north", "south") and abs(x - cx) < 0.5:
            return HOOF[0]                         # the cleft between the toes
        v = 2 if r == 1 else 1
        if f in ("north", "west") and r == 1:
            v = 3
        if f in ("east", "south"):
            v -= 1
        if r == 1 and (f, i, r + 1) in MUD_SPOTS[e["name"]]:
            return MUD[1]
        return HOOF[clamp(v, 0, 3)]
    v = FACE_SHADE[f] if f != "up" else 2
    if r >= 3:
        v -= 1                                     # shadow under the belly
    if r >= 4:
        v -= 1
    return SKIN[clamp(v)]


PAINTERS = {"skin": paint_skin, "snout": paint_snout, "tuft": paint_tuft,
            "ear": paint_ear, "leg": paint_leg}


# ---------------------------------------------------------------- animation

def kf(channel, t, x, y, z, interp="catmullrom"):
    return {"channel": channel, "data_points": [{"x": x, "y": y, "z": z}],
            "uuid": str(uuid.uuid4()), "time": t, "color": -1, "interpolation": interp}


def track(channel, keys, interp="catmullrom"):
    return [kf(channel, t, *v, interp=interp) for t, v in keys]


def loop_keys(times, values):
    return list(zip(times, values))


# Rotations are in Blockbench's animation convention: a positive x turns the
# head's snout down and swings a leg's foot backward.
ANIMATIONS = {
    # Never still: breathing, a look round, ear flicks, a lazy tail wag.
    "idle": {"loop": "loop", "length": 2.0, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.0, (1.015, 1.025, 1.01)), (2.0, (1, 1, 1))]),
        "head": track("rotation", [(0, (0, 0, 0)), (0.5, (-2, 5, 0)), (1.0, (-3, 0, 0)),
                                   (1.5, (-1, -5, 0)), (2.0, (0, 0, 0))]),
        "ear_right": track("rotation", [(0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.3, (0, 0, -14)),
                                        (1.42, (0, 0, 5)), (1.55, (0, 0, 0)), (2.0, (0, 0, 0))]),
        "ear_left": track("rotation", [(0, (0, 0, 0)), (0.35, (0, 0, 0)), (0.45, (0, 0, 10)),
                                       (0.55, (0, 0, -3)), (0.7, (0, 0, 0)), (2.0, (0, 0, 0))]),
        "tail": track("rotation", [(0, (0, 0, 0)), (0.5, (0, 22, 0)), (1.0, (0, 0, 0)),
                                   (1.5, (0, -22, 0)), (2.0, (0, 0, 0))]),
    }},
    # Trot: diagonal pairs, body bob twice per cycle, head lag, ears bounce.
    "walk": {"loop": "loop", "length": 0.8, "bones": {
        "leg_front_right": track("rotation", [(0, (25, 0, 0)), (0.4, (-25, 0, 0)), (0.8, (25, 0, 0))]),
        "leg_back_left": track("rotation", [(0, (25, 0, 0)), (0.4, (-25, 0, 0)), (0.8, (25, 0, 0))]),
        "leg_front_left": track("rotation", [(0, (-25, 0, 0)), (0.4, (25, 0, 0)), (0.8, (-25, 0, 0))]),
        "leg_back_right": track("rotation", [(0, (-25, 0, 0)), (0.4, (25, 0, 0)), (0.8, (-25, 0, 0))]),
        "body": track("position", [(0, (0, 0, 0)), (0.2, (0, 0.4, 0)), (0.4, (0, 0, 0)),
                                   (0.6, (0, 0.4, 0)), (0.8, (0, 0, 0))])
        + track("rotation", [(0, (0, 0, 2)), (0.4, (0, 0, -2)), (0.8, (0, 0, 2))]),
        "head": track("rotation", [(0, (0, 0, 0)), (0.2, (3, 0, 0)), (0.4, (0, 0, 0)),
                                   (0.6, (3, 0, 0)), (0.8, (0, 0, 0))]),
        "ear_right": track("rotation", [(0, (0, 0, 0)), (0.2, (-8, 0, 0)), (0.4, (0, 0, 0)),
                                        (0.6, (-8, 0, 0)), (0.8, (0, 0, 0))]),
        "ear_left": track("rotation", [(0, (0, 0, 0)), (0.2, (-8, 0, 0)), (0.4, (0, 0, 0)),
                                       (0.6, (-8, 0, 0)), (0.8, (0, 0, 0))]),
        "tail": track("rotation", [(0, (0, 18, 0)), (0.4, (0, -18, 0)), (0.8, (0, 18, 0))]),
    }},
    # Flee: a fast trot, bigger strides and bob, ears pinned back, tail up.
    "run": {"loop": "loop", "length": 0.4, "bones": {
        "leg_front_right": track("rotation", [(0, (40, 0, 0)), (0.2, (-40, 0, 0)), (0.4, (40, 0, 0))]),
        "leg_back_left": track("rotation", [(0, (40, 0, 0)), (0.2, (-40, 0, 0)), (0.4, (40, 0, 0))]),
        "leg_front_left": track("rotation", [(0, (-40, 0, 0)), (0.2, (40, 0, 0)), (0.4, (-40, 0, 0))]),
        "leg_back_right": track("rotation", [(0, (-40, 0, 0)), (0.2, (40, 0, 0)), (0.4, (-40, 0, 0))]),
        "body": track("position", [(0, (0, 0, 0)), (0.1, (0, 0.9, 0)), (0.2, (0, 0, 0)),
                                   (0.3, (0, 0.9, 0)), (0.4, (0, 0, 0))])
        + track("rotation", [(0, (-4, 0, 0)), (0.1, (-6, 0, 0)), (0.2, (-4, 0, 0)),
                             (0.3, (-6, 0, 0)), (0.4, (-4, 0, 0))]),
        "head": track("rotation", [(0, (6, 0, 0)), (0.1, (9, 0, 0)), (0.2, (6, 0, 0)),
                                   (0.3, (9, 0, 0)), (0.4, (6, 0, 0))]),
        "ear_right": track("rotation", [(0, (-30, 0, 0)), (0.2, (-36, 0, 0)), (0.4, (-30, 0, 0))]),
        "ear_left": track("rotation", [(0, (-30, 0, 0)), (0.2, (-36, 0, 0)), (0.4, (-30, 0, 0))]),
        "tail": track("rotation", [(0, (25, 25, 0)), (0.2, (25, -25, 0)), (0.4, (25, 25, 0))]),
    }},
    # Headbutt: rear back (anticipation), snap forward, overshoot, settle.
    "attack": {"loop": "once", "length": 0.9, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.3, (0, 0.3, 1.2)), (0.42, (0, -0.2, -2.5)),
                                   (0.55, (0, 0, -2.0)), (0.9, (0, 0, 0))])
        + track("rotation", [(0, (0, 0, 0)), (0.3, (-6, 0, 0)), (0.42, (5, 0, 0)),
                             (0.55, (3, 0, 0)), (0.9, (0, 0, 0))]),
        "head": track("rotation", [(0, (0, 0, 0)), (0.3, (-16, 0, 0)), (0.42, (22, 0, 0)),
                                   (0.55, (12, 0, 0)), (0.9, (0, 0, 0))]),
        "leg_back_right": track("rotation", [(0, (0, 0, 0)), (0.3, (-12, 0, 0)), (0.42, (18, 0, 0)),
                                             (0.9, (0, 0, 0))]),
        "leg_back_left": track("rotation", [(0, (0, 0, 0)), (0.3, (-12, 0, 0)), (0.42, (18, 0, 0)),
                                            (0.9, (0, 0, 0))]),
        "leg_front_right": track("rotation", [(0, (0, 0, 0)), (0.3, (10, 0, 0)), (0.42, (-14, 0, 0)),
                                              (0.9, (0, 0, 0))]),
        "leg_front_left": track("rotation", [(0, (0, 0, 0)), (0.3, (10, 0, 0)), (0.42, (-14, 0, 0)),
                                             (0.9, (0, 0, 0))]),
        "ear_right": track("rotation", [(0, (0, 0, 0)), (0.3, (-25, 0, 0)), (0.42, (15, 0, 0)),
                                        (0.9, (0, 0, 0))]),
        "ear_left": track("rotation", [(0, (0, 0, 0)), (0.3, (-25, 0, 0)), (0.42, (15, 0, 0)),
                                       (0.9, (0, 0, 0))]),
    }},
    # Hit: a short recoil and squash; the flash is done in Godot (STUDY 6).
    "hit": {"loop": "once", "length": 0.4, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.07, (0, 0, 1.2)), (0.2, (0, 0, -0.3)),
                                   (0.4, (0, 0, 0))])
        + track("scale", [(0, (1, 1, 1)), (0.07, (1.08, 0.9, 1.06)), (0.2, (0.97, 1.04, 0.98)),
                          (0.4, (1, 1, 1))]),
        "head": track("rotation", [(0, (0, 0, 0)), (0.07, (-18, 0, 6)), (0.2, (4, 0, -2)),
                                   (0.4, (0, 0, 0))]),
        "ear_right": track("rotation", [(0, (0, 0, 0)), (0.07, (0, 0, -25)), (0.4, (0, 0, 0))]),
        "ear_left": track("rotation", [(0, (0, 0, 0)), (0.07, (0, 0, 25)), (0.4, (0, 0, 0))]),
        "tail": track("rotation", [(0, (0, 0, 0)), (0.07, (30, 0, 0)), (0.4, (0, 0, 0))]),
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
        parent, piv, rot = BONES[bone]
        if any(rot):
            R = rot_matrix(*rot)
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

    places = pack([(k, w, h) for k, (w, h) in visible.items()], TEX)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        w, h = visible[(ei, f)]
        for i, j, p in texels(e, f):
            img.putpixel((ox + i, oy + j), PAINTERS[e["part"]](e, f, p, i, j, w, h))

    tex_png = out_dir / "pig.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, left side, front (the pig faces -z).
    views = [(-145, 22), (145, 22), (-35, 22), (-90, 0), (180, 0)]
    tiles = [render(img, places, yw, pt, 9, (320, 300)) for yw, pt in views]
    sheet = Image.new("RGBA", (320 * len(tiles), 300), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (320 * k, 0))
    sheet.save(out_dir / "pig_preview.png")
    sil = Image.new("RGBA", (640, 300), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 22, 9, (320, 300), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 9, (320, 300), True), (320, 0))
    sil.save(out_dir / "pig_silhouette.png")

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
        "from": [8, 0, -2], "to": [12, 18, 2], "autouv": 0, "color": 1,
        "origin": [10, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    elements.append(dummy)

    def group(name):
        _, piv, rot = BONES[name]
        kids = [group(b) for b, (parent, _, _) in BONES.items() if parent == name]
        return {"name": name, "origin": [u(v) for v in piv], "rotation": list(rot),
                "color": 0, "uuid": bone_uuid[name], "export": True, "mirror_uv": False,
                "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
                "children": children[name] + kids}

    outliner = [
        group("pig"),
        {"name": "scale_dummy", "origin": [10, 0, 0], "rotation": [0, 0, 0], "color": 0,
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
        "name": "pig", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": TEX, "height": TEX},
        "elements": elements, "outliner": outliner, "textures": [texture],
        "animations": animations,
    }
    (out_dir / "pig.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(ELEMENTS)}  bones: {len(BONES)}  visible faces: {len(visible)}  "
          f"texels used: {used}/{TEX * TEX}  animations: {', '.join(ANIMATIONS)}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
