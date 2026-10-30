"""Build the Blockbench cow: a big, gentle Hereford-style cow with a brass bell (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m.
- Box sizes in whole texture pixels (0.5 units). Odd widths for the centred
  parts (body, head, muzzle, jaw, dewlap, bell) so the face has a centre column.
- Per-face UV, one texture inside the large-creature budget, hidden faces removed.
- Lit from the top, slightly front-left; hue-shifted ramps (shadows toward
  plum, highlights toward warm), edge highlights on lit edges, painted shadow
  where parts meet, form shading on shoulder, ribs and hips. Short-haired
  hide, so "very few pixels of noise; let the form shading do the work"
  (BLOCKBENCH-STUDY 5.3).
- Size asked for by the user: about 1.5 m to the horn tips, twice the average
  height of the pig (0.59 m) and the wolf (0.94 m).
- There is no cow icon, so the colours come from ART-DIRECTION section 5: the
  hide is built round the warm creature swatch #BD753B, and the brass bell,
  the one accent, round the gold swatch #DFBD56.
- Bones use the shared creature names, pivots at the joints. The jaw is its
  own bone so the cow can chew, the bell swings, and the tail is a two-bone
  chain with a tuft. Animations: idle, walk, run, attack, hit.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground, the cow faces north (-z), its right side is +x.

Usage: python build_cow_bbmodel.py [out_dir]   (writes cow.bbmodel, cow.png,
cow_preview.png and cow_silhouette.png)
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

PX = 0.5   # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


# Ramps, darkest first. Shadows lean plum or violet, highlights lean warm.
HIDE = ramp("#3b2130", "#62342f", "#8a4f35", "#b06a38", "#cf9156")     # round #BD753B
# Creamy white, a step down from true white and leaning warm: in the first
# Godot tests a true white blew out under the sun and a cool one went blue
# under the sky light.
WHITE = ramp("#5a4a50", "#7d6b6c", "#a8968c", "#d0bfab", "#ebdcc4")
SKIN = ramp("#713750", "#a8586c", "#d08088", "#e8a59e", "#f7cbb6")     # muzzle, udder, inner ears
HORN = ramp("#4f4038", "#8a7664", "#b9a68c", "#dccdb2", "#f1e7d4")
HOOF = ramp("#271d2a", "#3e2f3d", "#5a4552", "#77606b")
HAIR = ramp("#2b1a24", "#47292a", "#6a3e2f", "#8c5835")               # tail tuft shadowing
LEATHER = ramp("#2e1a20", "#4c2827", "#6c3a2f", "#8a5038")             # the collar
BRASS = ramp("#5e3f19", "#9a6c26", "#d4ab4c", "#f0d27a", "#fff2b8")    # the accent: the bell
EYE_DARK = hexrgb("#1e1420")
EYE_GLINT = hexrgb("#fff6e8")

FACE_SHADE = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi):
    return {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}


def mirror(name, bone, part, lo, hi):
    """A right-side box and its mirror on the left."""
    right = el(name.replace("*", "right"), bone.replace("*", "right"), part, lo, hi)
    left = el(name.replace("*", "left"), bone.replace("*", "left"), part,
              (-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2]))
    return [right, left]


ELEMENTS = [
    # Body: a big barrel, 23 wide, 22 tall, 39 long, with a rounded back,
    # raised hips and a fuller belly.
    el("body", "body", "hide", (-11.5, 15, -19.5), (11.5, 37, 19.5)),
    el("body_back", "body", "hide", (-10.5, 37, -18.5), (10.5, 38, 18.5)),
    el("rump", "body", "hide", (-9.5, 38, 10.5), (9.5, 39, 17.5)),
    # The belly sits between the front and back legs, with room for a full
    # stride, and the udder between the hind legs, so neither cuts a leg.
    el("belly", "body", "hide", (-10.5, 14, -7.5), (10.5, 15, 7.5)),
    el("udder", "body", "udder", (-2.5, 12, 6.5), (2.5, 14, 13.5)),
    *mirror("teat_front_*", "body", "udder", (1, 10, 8), (2, 12, 9)),
    *mirror("teat_back_*", "body", "udder", (1, 10, 11), (2, 12, 12)),
    # The fold of skin under the throat, the collar and its bell.
    el("dewlap", "body", "dewlap", (-3.5, 20, -22.5), (3.5, 28, -19.5)),
    el("collar", "body", "collar", (-8.5, 27, -25.5), (8.5, 29, -19.5)),
    el("bell_top", "bell", "bell", (-1.5, 25, -26.5), (1.5, 27, -23.5)),
    el("bell_body", "bell", "bell", (-2.5, 21, -27.5), (2.5, 25, -22.5)),
    # Head: broad and long, a big pink muzzle, a chewing jaw, curls on the
    # forehead, horns that sweep out and up.
    el("head", "head", "face", (-7.5, 28, -31.5), (7.5, 43, -18.5)),
    el("muzzle", "head", "muzzle", (-6.5, 28, -35.5), (6.5, 34, -31.5)),
    el("forelock", "head", "forelock", (-3.5, 43, -30.5), (3.5, 45, -25.5)),
    *mirror("horn_*_1", "head", "horn", (6.5, 40, -27.5), (10.5, 43, -24.5)),
    *mirror("horn_*_2", "head", "horn", (10.5, 41, -27), (13.5, 43, -25)),
    *mirror("horn_*_3", "head", "horn", (12.5, 43, -27), (14.5, 47, -25)),
    el("jaw", "jaw", "jaw", (-5.5, 25, -35), (5.5, 28, -27)),
    # Ears: wide flaps that stick out sideways under the horns.
    *mirror("ear_*", "ear_*", "ear", (7.5, 36, -24.5), (13.5, 39, -23.5)),
    # Legs: 7 x 7 pillars, 4 px hidden in the body so a stride never opens a gap.
    *mirror("leg_front_*", "leg_front_*", "leg", (3.5, 0, -16), (10.5, 18, -9)),
    *mirror("leg_back_*", "leg_back_*", "leg", (3.5, 0, 9), (10.5, 18, 16)),
    # Tail: hangs from the top of the rump, a long thin rope and a tuft.
    el("tail_1", "tail", "tail", (-1, 26, 19.5), (1, 36, 21.5)),
    el("tail_2", "tail_lower", "tail", (-1, 18, 19.5), (1, 26, 21.5)),
    el("tail_tuft", "tail_lower", "tuft", (-2, 13, 18.5), (2, 18, 22.5)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "cow": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("cow", (0, 26, 0), (0, 0, 0)),
    "head": ("body", (0, 32, -19.5), (0, 0, 0)),
    "jaw": ("head", (0, 27.5, -27), (0, 0, 0)),
    "ear_right": ("head", (7.5, 37.5, -24), (0, 0, -22)),
    "ear_left": ("head", (-7.5, 37.5, -24), (0, 0, 22)),
    "bell": ("body", (0, 27, -25), (0, 0, 0)),
    "tail": ("body", (0, 36, 20.5), (-10, 0, 0)),
    "tail_lower": ("tail", (0, 26, 20.5), (6, 0, 0)),
    "leg_front_right": ("cow", (7, 16, -12.5), (0, 0, 0)),
    "leg_front_left": ("cow", (-7, 16, -12.5), (0, 0, 0)),
    "leg_back_right": ("cow", (7, 16, 12.5), (0, 0, 0)),
    "leg_back_left": ("cow", (-7, 16, 12.5), (0, 0, 0)),
}
ROTATED = {"ear_right", "ear_left", "tail", "tail_lower"}


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
    """A fixed rhythm for the edges of the white markings: soft tufts, not noise."""
    return (0, 1, 1, 0, -1, 0, 1, 0)[k % 8]


# White markings as unions of blobs in 3D, so they wrap round the form: a
# patch on the left flank and a small one on the right hip.
PATCHES = [
    ((-11.5, 27.0, 4.0), (3.0, 4.5, 5.0)), ((-11.5, 23.5, 8.0), (2.5, 2.5, 3.0)),
    ((11.5, 33.0, 13.0), (2.0, 2.5, 3.0)),
]


def in_patch(p):
    return any(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)) < 1.0 for c, r in PATCHES)


def white_body(e, f, p):
    """Hereford markings on the body: belly, chest bib, the crest along the
    top of the neck, and the patches."""
    x, y, z = p
    if f == "down":
        return True
    if e["name"] == "belly":
        return True
    if f in ("west", "east"):
        if y < 18 + jag(fi(z)) * 0.5 + (2 if z < -12 else 0):
            return True                            # white underline, rising to the chest
    if f == "north":
        return abs(x) < 7 + jag(fi(y)) * 0.5 and y < 31
    if f == "up" and z < -12 + 2 * jag(round(x) + 3):
        return abs(x) < 2.5                        # crest stripe over the withers
    return in_patch(p)


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


def paint_hide(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if e["name"] == "body" and f in ("west", "east"):
        if ((z + 14.5) / 3.6) ** 2 + ((y - 29) / 4.2) ** 2 < 1:
            v += 1                                 # the shoulder catches the light
        elif ((z - 14) / 3.6) ** 2 + ((y - 31) / 4.6) ** 2 < 1:
            v += 1                                 # and the hip
        elif z in (-6.5, -2.5, 1.5) and 21 <= y < 29 and (fi(y) + fi(z)) % 2 == 0:
            v -= 1                                 # faint ribs
        if y < 21:
            v -= 1                                 # belly in shadow
    if e["name"] == "body" and f == "south" and abs(x) < 1.5 and y > 30:
        v -= 1                                     # shadow under the tail root
    if e["name"] == "rump" and f == "up" and abs(x) > 6.5:
        v = 4                                      # hook bones
    if white_body(e, f, p):
        return WHITE[clamp(v - (1 if f == "down" else 0))]
    return HIDE[clamp(v)]


def paint_face(e, f, p, i, j, w, h):
    """The head: a white face with brown 'spectacles' round the eyes, brown
    sides and poll. Front columns are x (-7..7), rows y (28..42); the muzzle
    covers -6..6, 28..33."""
    x, y, z = p
    c, r = round(x), fi(y)
    ac = abs(c)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if ac in (5, 6) and 34 <= r <= 36:          # eyes, 2 x 3, wide-set
            if r == 36 and ((c < 0 and ac == 6) or (c > 0 and ac == 5)):
                return EYE_GLINT
            return EYE_DARK
        if r == 37 and 4 <= ac <= 7:
            return HIDE[0]                          # heavy lids and lashes
        if 4 <= ac and 33 <= r <= 38:
            return HIDE[clamp(v)]                   # brown round the eyes
        return WHITE[clamp(v)]
    if f in ("west", "east"):
        if z < -28.5 + 0.5 * jag(r) or r < 31:
            return WHITE[clamp(v)]                  # the white wraps round the front
        if r == 35 and -28.5 <= z < -27.5:
            return HIDE[0]                          # corner of the eye seen from the side
        return HIDE[clamp(v)]
    if f == "up":
        return WHITE[clamp(v)] if z < -24.5 + jag(round(x)) * 0.5 else HIDE[clamp(v)]
    if f == "down":
        return WHITE[1]
    return HIDE[clamp(v)]


def paint_muzzle(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if abs(c) in (3, 4) and r in (30, 31):
            return SKIN[0] if (r == 31 or abs(c) == 3) else SKIN[1]   # nostrils
        if c == 0 and r <= 29:
            v -= 1                                 # philtrum
        if r == 28:
            v -= 1
    if f == "up":
        v = 4 if j == h - 1 else 3
        if abs(c) <= 1 and z > -33.5:
            v = 3
    if f == "down":
        return SKIN[1]
    if f in ("west", "east") and r == 28:
        v -= 1
    return SKIN[clamp(v)]


def paint_jaw(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "up":
        return SKIN[0] if abs(x) < 4 else SKIN[1]   # inside the mouth
    if f == "north":
        return SKIN[0] if r == 27 else WHITE[clamp(v - (1 if r == 25 else 0))]
    if f == "down":
        return WHITE[1]
    return SKIN[1] if r == 27 and z < -31 else WHITE[clamp(v)]


def paint_forelock(e, f, p, i, j, w, h):
    """White curls: small 2 px crescents, lighter on top."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if f == "up":
        k = (round(x) + 2 * fi(z)) % 4
        return WHITE[4 if k == 0 else (2 if k == 2 else 3)]
    if f in ("north", "west", "east", "south"):
        k = (fi(y) + round(x) + fi(z)) % 3
        return WHITE[clamp(v - (1 if k == 0 else 0))]
    return WHITE[1]


def paint_horn(e, f, p, i, j, w, h):
    """Cream horns with a darker base ring and dark tips."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if e["name"].endswith("_3") and y >= 45:
        return HORN[clamp(v - 2, 0, 2)]
    if e["name"].endswith("_1") and abs(x) < 8.5:
        v -= 1                                     # base, where it leaves the skull
    if f == "down":
        v = 1
    return HORN[clamp(v)]


def paint_ear(e, f, p, i, j, w, h):
    x, y, z = p
    if f == "north":                               # inner ear, with a pale hairy rim
        if j in (0, h - 1) or i in (0, w - 1):
            return WHITE[3] if j == 0 else WHITE[2]
        return SKIN[1] if j == 1 else SKIN[2]
    v = FACE_SHADE[f] + (1 if f in ("west", "east") and j == 0 else 0)
    return HIDE[clamp(v)]


def paint_dewlap(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if fi(y) % 3 == 0:
        v -= 1                                     # soft folds
    return WHITE[clamp(v)]


def paint_collar(e, f, p, i, j, w, h):
    x, y, z = p
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    if f in ("north", "west", "east") and fi(y) == 27:
        k = round(x) if f == "north" else fi(z)
        if k % 3 == 0:
            return BRASS[2]                        # brass studs
    if f != "up" and j == 0:
        v += 1
    return LEATHER[clamp(v, 0, 3)]


def paint_bell(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    if e["name"] == "bell_top":
        return BRASS[{"up": 3, "north": 2, "west": 2}.get(f, 1)]
    if f == "down":
        return BRASS[0] if abs(c) <= 1 and abs(z + 25) < 1.5 else BRASS[1]
    if f == "north":
        if r == 21 and c == 0:
            return BRASS[0]                        # the clapper slot
        if c == -2 and r >= 23:
            return BRASS[4]                        # glint on the lit edge
        if c == -1:
            return BRASS[3]
        if r == 21:
            return BRASS[1]                        # lip
        return BRASS[2]
    if f == "up":
        return BRASS[3]
    v = 2 if f == "west" else 1
    if r == 24:
        v += 1
    return BRASS[v]


def paint_udder(e, f, p, i, j, w, h):
    v = base_shade(e, f, p, i, j)
    if e["name"].startswith("teat"):
        v = 2 if f in ("north", "west") else 1
    return SKIN[clamp(v)]


def paint_leg(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    cx = (e["lo"][0] + e["hi"][0]) / 2
    if f == "down":
        return HOOF[0]
    if r <= 2:                                     # hooves, 3 px
        if f in ("north", "south") and abs(x - cx) < 0.5:
            return HOOF[0]                         # the cleft
        hv = {2: 2, 1: 2, 0: 1}[r] + (1 if f in ("north", "west") and r == 2 else 0)
        if f in ("east", "south"):
            hv -= 1
        return HOOF[clamp(hv, 0, 3)]
    if f == "south" and r == 4 and abs(x - cx) < 1.5:
        return HOOF[1]                             # dew claws
    if r == 10:
        v -= 1                                     # the knee
    if r >= 14:
        v -= 1                                     # shadow under the body
    if r < 8 + jag(fi(z) + round(x)) * 0.5:
        return WHITE[clamp(v)]                     # white socks
    return HIDE[clamp(v)]


def paint_tail(e, f, p, i, j, w, h):
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    if contact(p, f, e):
        v -= 1
    return HIDE[clamp(v)]


def paint_tuft(e, f, p, i, j, w, h):
    """A white switch with strands hanging down."""
    x, y, z = p
    v = {"up": 3, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    k = round(x * 2) if f in ("north", "south") else round(z * 2)
    if f not in ("up", "down") and fi(y) <= 14 and k % 2:
        v -= 1                                     # strand ends
    if f not in ("up", "down") and fi(y) == 17:
        return HIDE[1]                             # where the rope meets the tuft
    return WHITE[clamp(v)]


PAINTERS = {"hide": paint_hide, "face": paint_face, "muzzle": paint_muzzle, "jaw": paint_jaw,
            "forelock": paint_forelock, "horn": paint_horn, "ear": paint_ear,
            "dewlap": paint_dewlap, "collar": paint_collar, "bell": paint_bell,
            "udder": paint_udder, "leg": paint_leg, "tail": paint_tail, "tuft": paint_tuft}


# ---------------------------------------------------------------- animation

def kf(channel, t, x, y, z, interp="catmullrom"):
    return {"channel": channel, "data_points": [{"x": x, "y": y, "z": z}],
            "uuid": str(uuid.uuid4()), "time": t, "color": -1, "interpolation": interp}


def track(channel, keys, interp="catmullrom"):
    return [kf(channel, t, *v, interp=interp) for t, v in keys]


def rot(*keys):
    return track("rotation", keys)


def sway(length, amp, phase, axis, cycles=1):
    """A looping sine sway in keys every 1/8 cycle, phase in cycles (for lag)."""
    n = 8 * cycles
    out = []
    for k in range(n + 1):
        v = [0, 0, 0]
        v[axis] = round(amp * math.sin(2 * math.pi * (k / 8 - phase)), 2)
        out.append((round(length * k / n, 4), tuple(v)))
    return track("rotation", out)


# Rotations are in Blockbench's animation convention: a positive x turns the
# head's snout down, swings a foot backward, opens the jaw, and swings a
# hanging part (bell, tail) forward.
ANIMATIONS = {
    # Placid idle: slow breathing, chewing the cud, a look round, ear flicks,
    # a lazy tail swish and the bell rocking.
    "idle": {"loop": "loop", "length": 3.0, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.5, (1.01, 1.018, 1.0)), (3.0, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.75, (2, 7, 2)), (1.5, (4, 0, 0)), (2.25, (2, -7, -2)),
                    (3.0, (0, 0, 0))),
        "jaw": track("rotation", [(round(0.375 * k, 3), ((3, 6, 0) if k % 2 else (1, -6, 0)))
                                  for k in range(9)]),
        "ear_right": rot((0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.1, (0, 15, -10)), (2.25, (0, -4, 3)),
                         (2.4, (0, 0, 0)), (3.0, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.7, (0, 0, 0)), (0.8, (0, -15, 10)), (0.95, (0, 4, -3)),
                        (1.1, (0, 0, 0)), (3.0, (0, 0, 0))),
        "tail": sway(3.0, 12, 0.0, 2),
        "tail_lower": sway(3.0, 16, 0.15, 2),
        "bell": sway(3.0, 4, 0.1, 0),
    }},
    # Walk: a slow, heavy trot, deep body sway, head nod, the bell swinging
    # behind the beat.
    "walk": {"loop": "loop", "length": 1.4, "bones": {
        "leg_front_right": rot((0, (-18, 0, 0)), (0.7, (18, 0, 0)), (1.4, (-18, 0, 0))),
        "leg_back_left": rot((0, (-16, 0, 0)), (0.7, (16, 0, 0)), (1.4, (-16, 0, 0))),
        "leg_front_left": rot((0, (18, 0, 0)), (0.7, (-18, 0, 0)), (1.4, (18, 0, 0))),
        "leg_back_right": rot((0, (16, 0, 0)), (0.7, (-16, 0, 0)), (1.4, (16, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.35, (0, 0.6, 0)), (0.7, (0, 0, 0)),
                                   (1.05, (0, 0.6, 0)), (1.4, (0, 0, 0))])
        + rot((0, (0, 0, 2)), (0.7, (0, 0, -2)), (1.4, (0, 0, 2))),
        "head": rot((0, (2, 0, 0)), (0.35, (6, 0, 0)), (0.7, (2, 0, 0)), (1.05, (6, 0, 0)),
                    (1.4, (2, 0, 0))),
        "bell": sway(1.4, 14, 0.15, 0, 2),
        "tail": sway(1.4, 10, 0.0, 2),
        "tail_lower": sway(1.4, 14, 0.15, 2),
    }},
    # Run: a lumbering gallop, front and back pairs together, head low.
    "run": {"loop": "loop", "length": 0.7, "bones": {
        "leg_front_right": rot((0, (-34, 0, 0)), (0.35, (30, 0, 0)), (0.7, (-34, 0, 0))),
        "leg_front_left": rot((0, (-30, 0, 0)), (0.35, (34, 0, 0)), (0.7, (-30, 0, 0))),
        "leg_back_right": rot((0, (30, 0, 0)), (0.35, (-30, 0, 0)), (0.7, (30, 0, 0))),
        "leg_back_left": rot((0, (34, 0, 0)), (0.35, (-26, 0, 0)), (0.7, (34, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.175, (0, 1.5, 0)), (0.35, (0, 0, 0)),
                                   (0.525, (0, 0.8, 0)), (0.7, (0, 0, 0))])
        + rot((0, (-4, 0, 0)), (0.35, (4, 0, 0)), (0.7, (-4, 0, 0))),
        "head": rot((0, (10, 0, 0)), (0.35, (4, 0, 0)), (0.7, (10, 0, 0))),
        "ear_right": rot((0, (0, -20, 0)), (0.7, (0, -20, 0))),
        "ear_left": rot((0, (0, 20, 0)), (0.7, (0, 20, 0))),
        "bell": sway(0.7, 25, 0.15, 0),
        "tail": rot((0, (-35, 0, 0)), (0.35, (-45, 0, 0)), (0.7, (-35, 0, 0))),
        "tail_lower": rot((0, (-10, 0, 0)), (0.35, (-20, 0, 0)), (0.7, (-10, 0, 0))),
    }},
    # Horn charge: drop the head and paw (anticipation), shove forward with
    # the horns, toss the head up, settle.
    "attack": {"loop": "once", "length": 1.0, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.35, (0, -0.8, 1.5)), (0.5, (0, 0.4, -4.0)),
                                   (0.62, (0, 0.6, -3.5)), (1.0, (0, 0, 0))])
        + rot((0, (0, 0, 0)), (0.35, (4, 0, 0)), (0.5, (-3, 0, 0)), (1.0, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.35, (28, 0, 0)), (0.5, (22, 0, 0)), (0.62, (-18, 0, 0)),
                    (1.0, (0, 0, 0))),
        "leg_front_right": rot((0, (0, 0, 0)), (0.15, (-25, 0, 0)), (0.25, (5, 0, 0)),
                               (0.35, (-20, 0, 0)), (0.5, (-15, 0, 0)), (1.0, (0, 0, 0))),
        "leg_back_right": rot((0, (0, 0, 0)), (0.35, (-8, 0, 0)), (0.5, (22, 0, 0)), (1.0, (0, 0, 0))),
        "leg_back_left": rot((0, (0, 0, 0)), (0.35, (-8, 0, 0)), (0.5, (22, 0, 0)), (1.0, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.35, (0, -25, 0)), (1.0, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.35, (0, 25, 0)), (1.0, (0, 0, 0))),
        "bell": rot((0, (0, 0, 0)), (0.35, (12, 0, 0)), (0.5, (-30, 0, 0)), (0.62, (25, 0, 0)),
                    (0.8, (-10, 0, 0)), (1.0, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.35, (-30, 0, 0)), (1.0, (0, 0, 0))),
    }},
    # Hit: a heavy flinch, head tossed aside, ears pinned, tail flick, bell clang.
    "hit": {"loop": "once", "length": 0.45, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.08, (0, 0, 1.5)), (0.22, (0, 0, -0.3)),
                                   (0.45, (0, 0, 0))])
        + track("scale", [(0, (1, 1, 1)), (0.08, (1.04, 0.95, 1.03)), (0.22, (0.99, 1.02, 0.99)),
                          (0.45, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.08, (-12, 12, 6)), (0.22, (3, -3, -1)), (0.45, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.08, (12, 0, 0)), (0.45, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.08, (0, -30, 15)), (0.45, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.08, (0, 30, -15)), (0.45, (0, 0, 0))),
        "bell": rot((0, (0, 0, 0)), (0.08, (-30, 0, 0)), (0.18, (20, 0, 0)), (0.3, (-8, 0, 0)),
                    (0.45, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.08, (-30, 0, 20)), (0.45, (0, 0, 0))),
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
    cx, cyy = size[0] / 2, size[1] * 0.85
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

    # The smallest power-of-two sheet the faces pack into (budget: 256).
    rects = [(k, w, h) for k, (w, h) in visible.items()]
    for tex in (64, 128, 256):
        try:
            places = pack(rects, tex)
            break
        except SystemExit:
            continue
    img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        w, h = visible[(ei, f)]
        for i, j, p in texels(e, f):
            img.putpixel((ox + i, oy + j), PAINTERS[e["part"]](e, f, p, i, j, w, h))

    tex_png = out_dir / "cow.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, left side, front (the cow faces -z).
    views = [(-145, 22), (145, 22), (-35, 22), (-90, 0), (180, 0)]
    tiles = [render(img, places, yw, pt, 5, (420, 360)) for yw, pt in views]
    sheet = Image.new("RGBA", (420 * len(tiles), 360), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (420 * k, 0))
    sheet.save(out_dir / "cow_preview.png")
    sil = Image.new("RGBA", (840, 360), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 22, 5, (420, 360), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 5, (420, 360), True), (420, 0))
    sil.save(out_dir / "cow_silhouette.png")

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
        "from": [14, 0, -2], "to": [18, 18, 2], "autouv": 0, "color": 1,
        "origin": [16, 0, 0],
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
        group("cow"),
        {"name": "scale_dummy", "origin": [16, 0, 0], "rotation": [0, 0, 0], "color": 0,
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
        "name": "cow", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": tex, "height": tex},
        "elements": elements, "outliner": outliner, "textures": [texture],
        "animations": animations,
    }
    (out_dir / "cow.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(ELEMENTS)}  bones: {len(BONES)}  visible faces: {len(visible)}  "
          f"texture: {tex}x{tex}  texels used: {used}/{tex * tex}  "
          f"animations: {', '.join(ANIMATIONS)}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
