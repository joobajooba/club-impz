"""Build implingz_voxel_character_model: the green Imp from the pixel-art portrait, as a
Hytale-style Blockbench model at 100% scale with a high-detail texture.

A different take from build_impling_bbmodel.py, which is the voxel Imp at
D-053. This one follows the pixel-art portrait (white crescent horns, a bald
head, wide pointed ears, glaring purple eyes under heavy brows, a chest
with pecs and a navel, mitten hands, a thin tail with a pale spade) and the
way Hytale models are made:
- Few, chunky boxes, the detail in the texture. The head is bevelled (a core
  box with a slab on each side); the body is one flat box, like a Minecraft
  character's. The face is all texture: no box sticks out for the brows or
  the nose.
- 100% scale: the Imp's in-game height, 1.16 m to the horn tips, the same as
  the scale dummy every model is built against.
- Geometry in 0.25-unit steps ("px" below), the texture SUB times finer:
  8 texture pixels per Blockbench unit (128 per metre), four times D-053.
  The UVs stay in px (uv size half the image), so Blockbench maps every box
  the same. The texture carries painted detail: smooth baked light from the
  shape each part stands for, ambient occlusion where parts meet, lit edges,
  horn rings, chest, navel and finger lines, and the face: angry
  eyes (a round bottom cut by a hard diagonal lid that drops toward the
  nose, black rims, a socket shadow, a squint pushing the cheek up), big
  striated irises with a limbal ring and collarette, slit-oval pupils and
  two glints, thick painted brows in an angry V pressing down on the lids,
  the furrow knotted between them, creases up the forehead, a nose, and a
  frown. One green all over, and clean banded shading with no noise, after
  the Hytale reference the user gave.
- Mirrored exactly: every left-side face reuses its right twin's pixels
  through a mirrored UV, and everything that spans both sides (head, body)
  is painted from |x| with light that is the same on both sides. The build
  checks every face against its mirror and stops if one differs.

Not a game asset: it does not follow D-053, so nothing in the game uses it.

Usage: python build_implingz_voxel_character_model.py [out_dir]   (writes
implingz_voxel_character_model.bbmodel, its .png texture, _preview.png,
implingz_voxel_character_model_render.png)
"""

import json
import math
import sys
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent))
import bbcreature  # noqa: E402
from bbcreature import NORMAL, Creature, Texel, corners, el, hexrgb, mirror, pack, tangents  # noqa: E402
from bbcreature import face_frame, texels  # noqa: E402

PX_HD = 0.25            # Blockbench units per px of geometry
SUB = 2                 # texture pixels per px: 8 per unit, 128 per metre
IMP_HEIGHT_PX = 74      # 1.156 m, the scale dummy's height


def ramp(*cs):
    return [np.array(hexrgb(c)[:3], float) for c in cs]


# Ramps, darkest first, sampled from the portrait and pushed the Hytale way:
# shadows lean blue-teal, highlights lean yellow.
SKIN = ramp("#0f3328", "#1b5a2e", "#2c8a30", "#46ad3a", "#7ccf58", "#bfe88e")
HORN = ramp("#57536a", "#8f8ba3", "#c6c3d3", "#e9e7f0", "#fbfaff", "#ffffff")
SPADE = ramp("#2c4f6e", "#5f93b6", "#a3d2e6", "#d6f0f8", "#f4fcff", "#ffffff")
SCLERA = ramp("#5e4e78", "#9a87b8", "#cfc0e2", "#ece4f5", "#fdfaff")
IRIS = ramp("#1a0b2c", "#3a1960", "#64309a", "#9257c8", "#c79ef0")
PUPIL = np.array(hexrgb("#0e0716")[:3], float)
GLINT = np.array((255, 255, 255), float)
LINE = np.array(hexrgb("#08190f")[:3], float)        # lash lines, mouth


# ---------------------------------------------------------------- geometry

def rbox(name, bone, part, lo, hi, b):
    """A box with its four vertical edges bevelled b px: a core the full
    depth, and a slab b px thick on each side, set in by b front and back."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    return [el(name, bone, part, (x0 + b, y0, z0), (x1 - b, y1, z1)),
            el(f"{name}_r", bone, part, (x1 - b, y0, z0 + b), (x1, y1, z1 - b)),
            el(f"{name}_l", bone, part, (x0, y0, z0 + b), (x0 + b, y1, z1 - b))]


def segment(name, bone, part, base, angle, length, width, z):
    """A horn segment standing on base (x, y), turned angle degrees out from
    upright (to +x), reaching 1 px back into the one before. Returns the box
    and where it ends."""
    x, y = base
    a = math.radians(angle)
    box = el(name, bone, part, (x - width / 2, y - 1, z[0]), (x + width / 2, y + length, z[1]),
             rot=(0, 0, -angle), origin=(x, y, (z[0] + z[1]) / 2))
    return box, (x + length * math.sin(a), y + length * math.cos(a))


def horn():
    """The right horn: a big crescent out of the top corner of the head, out
    and then up, the tip leaning back in."""
    out, at = [], (11, 59)
    for name, angle, length, width, z in (("base", 72, 6, 8, (-6, 2)), ("out", 46, 5, 7, (-5.5, 1.5)),
                                          ("up", 14, 4, 6, (-5, 1)), ("tip", -6, 3, 4, (-4, 0)),
                                          ("point", -22, 2, 2, (-3, -1))):
        box, at = segment(f"horn_*_{name}", "horn_*", "horn", at, angle, length, width, z)
        out.append(box)
    return out


ELEMENTS = [
    # Feet and stubby legs.
    *mirror("foot_*", "leg_*", "foot", (1.5, 0, -7), (9.5, 4, 3)),
    *mirror("toes_*", "leg_*", "foot", (2.5, 0, -9), (8.5, 3, -7)),
    *mirror("leg_*_box", "leg_*", "skin", (2, 4, -3.5), (9, 12, 3.5)),
    # One flat body under the big head, like a Minecraft character's.
    el("torso", "body", "skin", (-9, 11, -5), (9, 30, 4)),
    # The head: half the Imp's height. A bevelled block, a smaller block on
    # top for the crown and one underneath for the jaw.
    *rbox("jaw", "head", "head", (-11, 30, -12), (11, 33, 10), 3),
    *rbox("skull", "head", "head", (-15, 33, -14), (15, 62, 14), 3),
    *rbox("crown", "head", "head", (-12, 62, -11), (12, 66, 11), 3),
    # Horns.
    *[b for h in horn() for b in mirror(h["name"], h["bone"], h["part"], h["lo"], h["hi"],
                                         h["rot"], h["origin"])],
    # Ears: wide at the root, a flat top edge, stepping up to a point.
    *mirror("ear_*_root", "ear_*", "ear", (14, 40, -2), (18, 53, 2)),
    *mirror("ear_*_mid", "ear_*", "ear", (18, 42, -1.5), (21, 53, 1.5)),
    *mirror("ear_*_end", "ear_*", "ear", (21, 45, -1.5), (24, 53, 1.5)),
    *mirror("ear_*_tip", "ear_*", "ear", (24, 48, -1), (26, 53, 1)),
    *mirror("ear_*_point", "ear_*", "ear", (26, 50, -1), (28, 53, 1)),
    # Arms hung out from the shoulders, mitten hands with a thumb.
    *mirror("arm_*_box", "arm_*", "skin", (9, 18, -2.5), (14, 29, 2.5)),
    *mirror("hand_*", "arm_*", "hand", (8.5, 12, -3), (14.5, 18, 3)),
    *mirror("thumb_*", "arm_*", "hand", (7.5, 13, -4), (10.5, 17, -2)),
    # Tail: modelled straight back, curled out and up by its bones.
    el("tail_root", "tail", "tail", (-1.5, 13, 4), (1.5, 16, 10)),
    el("tail_mid", "tail_mid", "tail", (-1, 13.5, 10), (1, 15.5, 17)),
    el("tail_end", "tail_end", "tail", (-1, 13.5, 17), (1, 15.5, 24)),
    el("tail_tip", "tail_tip", "tail", (-1, 13.5, 24), (1, 15.5, 28)),
    el("spade_base", "tail_tip", "spade", (-1, 11, 28), (1, 18, 30)),
    el("spade_mid", "tail_tip", "spade", (-1, 12, 30), (1, 17, 32)),
    el("spade_end", "tail_tip", "spade", (-1, 13, 32), (1, 16, 34)),
    el("spade_point", "tail_tip", "spade", (-0.5, 14, 34), (0.5, 15, 35)),
]

BONES = {
    "impling": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("impling", (0, 12, -1), (0, 0, 0)),
    "chest": ("body", (0, 22, -0.5), (0, 0, 0)),
    "head": ("chest", (0, 30, -1), (0, 0, 0)),
    "horn_right": ("head", (12, 59, -2), (0, 0, 0)),
    "horn_left": ("head", (-12, 59, -2), (0, 0, 0)),
    "ear_right": ("head", (15, 47, 0), (0, -12, 14)),
    "ear_left": ("head", (-15, 47, 0), (0, 12, -14)),
    "arm_right": ("chest", (11, 28.5, 0), (0, 0, 22)),
    "arm_left": ("chest", (-11, 28.5, 0), (0, 0, -22)),
    "leg_right": ("body", (5.5, 12, 0), (0, 0, 0)),
    "leg_left": ("body", (-5.5, 12, 0), (0, 0, 0)),
    "tail": ("body", (0, 14.5, 5), (8, -100, 0)),
    "tail_mid": ("tail", (0, 14.5, 10), (-22, 0, 0)),
    "tail_end": ("tail_mid", (0, 14.5, 17), (-42, 0, 0)),
    "tail_tip": ("tail_end", (0, 14.5, 24), (-38, 0, 0)),
}


# ---------------------------------------------------------------- painting

def hash3(x, y, z, seed=0.0):
    """Deterministic noise in -1..1 for a point, the same on both sides
    (it takes |x|), so the texture mirrors exactly."""
    x = abs(x)
    v = math.sin(x * 12.9898 + y * 78.233 + z * 37.719 + seed * 4.581) * 43758.5453
    return 2 * (v - math.floor(v)) - 1


def grad(stops, v):
    """Colour at v (0..1) along a ramp, interpolated."""
    v = min(max(v, 0.0), 1.0) * (len(stops) - 1)
    k = min(int(v), len(stops) - 2)
    return stops[k] + (stops[k + 1] - stops[k]) * (v - k)


def rgba(c):
    return tuple(int(round(min(max(v, 0), 255))) for v in c) + (255,)


def unit(n):
    n = np.asarray(n, float)
    return n / max(float(np.linalg.norm(n)), 1e-6)


def light(n):
    """Baked light from a world normal: from the top and the front, the same
    on both sides, so each side is the other's reflection."""
    return 0.38 + 0.32 * n[1] - 0.18 * n[2] - 0.07 * abs(n[0])


def ball(t, centre, radii):
    """Normal of the smooth shape a bevelled block stands for (side faces);
    top and bottom faces keep their own, rounded toward their edges."""
    return unit([(t.q[k] - centre[k]) / radii[k] ** 2 for k in range(3)])


def tube(t, axis=1):
    """Normal of the round limb a box stands for, along its own long axis."""
    if NORMAL[t.f][axis]:
        return np.asarray(t.n, float)
    lo, hi = t.e["lo"], t.e["hi"]
    d = [(t.p[k] - (lo[k] + hi[k]) / 2) / max((hi[k] - lo[k]) / 2, 1) for k in range(3)]
    d[axis] = 0.0
    d = [d[k] + 0.6 * NORMAL[t.f][k] for k in range(3)]
    return unit(t.e["M"][:3, :3] @ np.array(d, float))


BANDS = 20              # shades per ramp: clean bands, the way Hytale textures are painted


def finish(stops, v, t, ao=0.16, edge=0.07):
    """Ramp colour after occlusion and lit edges, snapped to clean bands. No
    noise: the detail is drawn, not sprinkled."""
    if t.contact:
        v -= ao
    if t.edge:
        v += edge
    return rgba(grad(stops, round(v * BANDS) / BANDS))


HEAD_BALL = ((0, 47, 0), (24, 22, 16))


# --- the face, drawn on the front of the skull (z = -14) under the brows.
# Coordinates are world px; u = |x|, so the left eye mirrors the right.
#
# The angry eye: a round bottom (an ellipse) cut across the top by the upper
# lid, a hard straight diagonal that drops toward the nose. The inner end is
# pinched shut, the outer end stays open and round. A thick painted brow sits
# right on the lid, and the iris glares in from under it.

EYE_C, EYE_R = (6.4, 46.6), (4.8, 3.6)     # the ellipse
LID_Y, LID_SLOPE = 45.2, 0.52               # the lid: LID_Y at u = 1.6, rising outward
IRIS_C, IRIS_R = (5.6, 45.5), 2.65         # big, in toward the nose, its top under the lid
PUPIL_R = (0.8, 1.35)                      # a tall oval, nearly a slit


def lid(u):
    return LID_Y + LID_SLOPE * (u - 1.6)


def ellipse(u, y, grow=0.0):
    """<= 1 inside the eye's ellipse grown by grow px."""
    return ((u - EYE_C[0]) / (EYE_R[0] + grow)) ** 2 + ((y - EYE_C[1]) / (EYE_R[1] + grow)) ** 2


def eyeball(t, x, y, u):
    """Colour of a texel inside the eye opening."""
    gap = lid(u) - y                               # px below the lid
    ix, iy = IRIS_C
    d = math.hypot(u - ix, y - iy)
    # Glints, mirrored like everything else: a big one high on the side
    # toward the nose, a small bounce light low on the outer side.
    if math.hypot(u - (ix - 0.95), y - (iy + 0.7)) < 0.62:
        return rgba(GLINT)
    if math.hypot(u - (ix + 1.05), y - (iy - 1.1)) < 0.33:
        return rgba(GLINT * 0.8 + IRIS[4] * 0.2)
    if ((u - ix) / PUPIL_R[0]) ** 2 + ((y - iy) / PUPIL_R[1]) ** 2 <= 1:
        return rgba(PUPIL)
    if d < IRIS_R:
        r = d / IRIS_R
        theta = math.atan2(y - iy, u - ix)
        v = 0.4 + 0.34 * (iy - y + IRIS_R) / (2 * IRIS_R)      # lit from below, inside the eye
        v += (0.08 * math.sin(theta * 11 + 1.3) + 0.05 * math.sin(theta * 23 + 0.4)) * r   # striations
        if r > 0.86:
            v -= 0.32                              # the dark limbal ring
        elif 0.38 < r < 0.55:
            v += 0.13                              # the bright collarette round the pupil
        elif r <= 0.38:
            v -= 0.1                               # a dark rim on the pupil
        v -= 0.45 * max(0.0, 1 - gap / 1.2)        # the lid's shadow over its top
        return rgba(grad(IRIS, v))
    # The white: shadowed under the lid, rounder and darker toward its rim.
    v = 0.25 + 0.8 * min(gap / 2.2, 1.0) - 0.35 * max(0.0, ellipse(u, y) - 0.6) / 0.4
    return rgba(grad(SCLERA, v))


def face(t):
    """('col', colour) for a painted feature, else ('dv', light change) for
    the shaping round the eyes, nose and brows."""
    x, y, _ = t.q
    u = abs(x)
    e = ellipse(u, y)
    top = lid(u)
    if e <= 1 and y < top:
        return "col", eyeball(t, x, y, u)
    # The upper lid: a thick black line along the diagonal, running a little
    # past the inner corner toward the nose like a scowl.
    thick = 0.85 + 0.25 * (u - 1.6) / 9.4
    if top <= y < top + thick and (ellipse(u, y, 0.9) <= 1 or 1.0 <= u < 1.6):
        return "col", rgba(LINE)
    # The rim round the rest: black round the outer side, fading to dark
    # green along the bottom.
    if e > 1 and ellipse(u, y, 0.55) <= 1 and y < top:
        lower = y < EYE_C[1] - 1.0
        return "col", rgba(grad(SKIN, 0.1) * 0.6 + LINE * 0.4 if lower else LINE)
    # The brow: one bold dark stroke in an angry V, steeper than the lid and
    # sitting right on it, thickest at the knotted inner end, tapering to a
    # point outside. A touch lighter along its top edge.
    lo_b = brow_low(u)
    th = brow_thick(u)
    if 0.9 <= u <= 11.6 and lo_b <= y < lo_b + th:
        knot = 0.04 * max(0.0, 1 - (u - 0.9) / 2.5)
        top_edge = 0.06 if y >= lo_b + th - 0.5 and th > 1.2 else 0.0
        return "col", rgba(grad(SKIN, 0.05 - knot + top_edge) * 0.75 + LINE * 0.25)
    dv = 0.0
    if ellipse(u, y, 1.8) <= 1 and y < top + thick + 0.6:
        dv -= 0.14 * (1 - (ellipse(u, y, 1.8) - ellipse(u, y, 0.55)) / max(1 - ellipse(u, y, 0.55), 1e-6))
        dv = max(dv, -0.14)                        # the socket: the eye sits in
    if 0.35 <= y - (EYE_C[1] - EYE_R[1] - 0.55) + 1.4 < 0.9 and abs(u - EYE_C[0]) < 3.2:
        dv += 0.07                                 # the squint pushes the cheek up
    # The scowl: two furrows between the brows, the ridge between them, the
    # lines running up from the brows' inner ends, a crease on the nose.
    if 45.0 <= y <= 50.8 and 0.4 <= u <= 0.85:
        dv -= 0.2
    if 45.0 <= y <= 50.8 and u < 0.4:
        dv += 0.06
    for y0 in (1.0, 2.4):                          # forehead creases following the brows
        line = brow_low(u) + brow_thick(u) + y0
        if abs(y - line) < 0.3 and 1.2 < u < 6.5 - y0:
            dv -= 0.08
    if 43.4 <= y < 43.9 and u < 1.3:
        dv -= 0.12                                 # a crease across the bridge of the nose
    if 40 <= y < 42.5 and u < 2.2:
        dv += 0.07                                 # the tip of the nose catches the light
    if 39.5 <= y < 40 and 2.2 > u:
        dv -= 0.1                                  # and shades the lip under it
    return "dv", dv


def brow_low(u):
    """Bottom edge of the painted brow: just above the lid, rising faster."""
    return 45.9 + 0.62 * (u - 1.0)


def brow_thick(u):
    return max(0.0, 2.6 - 1.1 * (u - 1.0) / 10.5 - max(0.0, u - 10.0) * 0.9)


def mouth(t):
    x, y, _ = t.p
    if t.e["name"] == "skull" and t.f == "north" and 40 <= y < 41 and 0.8 <= abs(x) <= 1.8:
        return rgba(LINE)                          # nostrils
    if t.e["name"] == "skull" and t.f == "north" and abs(x) < 3:
        m = 37.8 - 0.09 * x * x                    # a frown under the nose, the corners turned down
        if abs(y - m) < 0.3:
            return rgba(LINE)
    return None


def paint_head(t):
    x, y, z = t.p
    if t.f == "down":
        return finish(SKIN, 0.12, t, ao=0)
    m = mouth(t)
    if m is not None:
        return m
    v = light(ball(t, *HEAD_BALL))
    if t.f == "north" and t.e["name"].startswith("skull"):
        kind, f = face(t)
        if kind == "col":
            return f
        v += f
    if t.e["name"].startswith("jaw"):
        v -= 0.08
    if t.f == "north" and z < -13.5 and 40 <= y <= 42 and 5 <= abs(x) <= 10.5:
        v += 0.04                                  # cheeks catch the light
    return finish(SKIN, v, t)


def paint_ear(t):
    """Front: a dark inner ear with a fold, a lit rim round it."""
    x, y, z = t.p
    v = light(t.n)
    if t.f == "down":
        return finish(SKIN, 0.15, t, ao=0)
    if t.f == "north":
        lo, hi = t.e["lo"], t.e["hi"]
        if y >= 51.5 or y < lo[1] + 1:
            return finish(SKIN, v + 0.1, t)          # the rim
        depth = (hi[0] - abs(x)) / 14
        return finish(SKIN, 0.18 + 0.12 * (1 - depth) + 0.05 * math.sin(abs(x) * 1.4), t, ao=0.06)
    return finish(SKIN, v, t)


def paint_horn(t):
    """White and cool: grooved rings, darker and stained at the root, the
    tip brightest."""
    name = t.e["name"]
    along = t.p[1] - t.e["origin"][1]
    v = light(t.n) + 0.05
    if name.endswith("_base"):
        v -= 0.18 * max(0.0, 1.5 - along) / 1.5 + 0.06
    if name.endswith(("_tip", "_point")):
        v += 0.1
    if t.f not in ("up", "down") and not name.endswith("_point"):
        ring = (along + 0.2) % 2.5 / 2.5             # growth rings: a soft groove, a lit ridge
        v -= 0.1 * max(0.0, 1 - abs(ring - 0.15) / 0.15) - 0.04 * max(0.0, 1 - abs(ring - 0.4) / 0.15)
    return finish(HORN, v, t, ao=0.2)


def paint_skin(t):
    """Torso, arms and legs: pecs, navel, spine and shoulder blades on the
    flat body, round light on the limbs."""
    x, y, z = t.p
    name = t.e["name"]
    if t.f == "down":
        return finish(SKIN, 0.1, t, ao=0)
    torso = name == "torso"
    v = light(t.n) + 0.05 * (y - 20.5) / 9.5 if torso else light(tube(t))
    if torso and t.f == "north":
        u = abs(x)
        pec = 25.0 + 0.05 * u * u
        if u <= 6.5 and pec - 0.6 <= y < pec:
            v -= 0.16                                # under the pecs
        if u <= 6.5 and pec <= y < pec + 2.0:
            v += 0.05                                # the pecs catch the light
        if u < 0.5 and 18 <= y < pec + 2.0:
            v -= 0.1                                 # the line down the middle
        if 20.5 <= y < 21 and 1.5 < u < 5:
            v -= 0.08                                # under the ribs
        n = math.hypot(x, (y - 16.3) * 0.8)
        if n < 0.75:
            return finish(SKIN, 0.12 + 0.12 * (y - 16.3), t)   # navel, lit on its lower lip
    if torso and t.f == "south":
        u = abs(x)
        if u < 0.5 and 14 <= y < 28:
            v -= 0.1                                 # spine
        if 2 <= u <= 5.5 and 25 <= y < 28:
            v += 0.05                                # shoulder blades
    if name.startswith("leg_") and t.f == "north" and 8 <= y < 9:
        v += 0.06                                    # knees
    if name.startswith("leg_") and y < 5.5:
        v -= 0.08 * (5.5 - y) / 1.5                  # into the foot's shadow
    return finish(SKIN, v, t)


def paint_hand(t):
    """Mitts: three finger grooves round the lower half, a crease at the thumb."""
    x, y, z = t.p
    v = light(tube(t))
    if t.f == "down":
        return finish(SKIN, 0.2, t, ao=0)
    if t.e["name"].startswith("hand_") and y < 15.5:
        across = z if t.f in ("east", "west") else x
        if t.f in ("east", "west") and abs(((across + 3) % 2) - 0) < 0.55 and -2.5 < across < 2.5:
            v -= 0.14                                # between the fingers
        if t.f in ("north", "south"):
            v -= 0.04
    if t.e["name"].startswith("hand_") and 17 <= y:
        v -= 0.07                                    # the wrist
    return finish(SKIN, v + 0.03, t)


def paint_foot(t):
    x, y, z = t.p
    v = light(t.n)
    if t.f == "down":
        return finish(SKIN, 0.05, t, ao=0)
    if t.e["name"].startswith("toes_") and t.f in ("north", "up"):
        c = abs(x) - 2.5
        if abs(c - 2) < 0.5 or abs(c - 4) < 0.5:
            v -= 0.15                                # three toes
        v += 0.05
    return finish(SKIN, v - 0.03 * (4 - y), t)


def paint_tail(t):
    v = light(tube(t, axis=2))
    if t.f == "down":
        return finish(SKIN, 0.15, t, ao=0)
    return finish(SKIN, v - 0.03, t)


def paint_spade(t):
    """Pale blue, glassy: bright toward the point, a dark line down the
    middle of each flat side."""
    x, y, z = t.p
    v = light(t.n) + 0.05 + 0.05 * (z - 28) / 7
    if t.f in ("east", "west") and abs(y - 14.5) < 0.5 and z < 33:
        v -= 0.25
    if t.e["name"] == "spade_base" and z < 28.5:
        v -= 0.2                                     # where it meets the tail
    return finish(SPADE, v, t)


PAINTERS = {"head": paint_head, "ear": paint_ear, "horn": paint_horn,
            "skin": paint_skin, "hand": paint_hand, "foot": paint_foot, "tail": paint_tail,
            "spade": paint_spade}

# Parts that are one continuous skin: no painted shadow where they meet.
FAMILY = {"skin": "body", "hand": "body", "foot": "body", "tail": "body"}


class ImplingHD(Creature):
    def contact(self, e, f, p):
        """Occlusion only where a box meets another part, and only from above
        or beside (what's below casts nothing)."""
        n = NORMAL[f]
        q = [p[k] + 0.5 * n[k] for k in range(3)]
        mine = FAMILY.get(e["part"], e["part"])
        other = np.array([FAMILY.get(o["part"], o["part"]) != mine and o["part"] not in ("tail", "spade")
                          for o in self.elements])
        for tg in bbcreature.tangents(f):
            for sg in (-1, 1):
                for reach in (1, 2):
                    if self.world_dir(e, [sg * c for c in tg])[1] < -0.7:
                        continue
                    w = self.world(e, [q[k] + reach * sg * tg[k] for k in range(3)])
                    ql = np.einsum("nij,j->ni", self.MINV, np.array([*w, 1.0]))[:, :3]
                    if (np.all((ql > self.LO + 1e-6) & (ql < self.HI - 1e-6), axis=1) & other).any():
                        return True
        return False

    def edge(self, e, f, p, nw):
        """Edge highlight one texture pixel (half a px) wide, so it stays a
        fine line at SUB times the density."""
        n = NORMAL[f]
        step = 1 / SUB
        for tg in tangents(f):
            for sg in (-1, 1):
                d = [sg * step * tg[k] for k in range(3)]
                dw = self.world_dir(e, d)
                if nw[1] < 0.7 and dw[1] < 0.7 * step:
                    continue
                q = [p[k] + d[k] - 0.25 * n[k] for k in range(3)]
                if not self.inside_any(self.world(e, q)):
                    return True
        return False

    def subtexels(self, e, f):
        """Yield (i, j, centre) for every texture pixel of a face, SUB x SUB
        to each px of geometry."""
        o, u, v, w, h = face_frame(e, f)
        for j in range(int(h) * SUB):
            for i in range(int(w) * SUB):
                yield i, j, tuple(o[k] + (i + 0.5) / SUB * u[k] + (j + 0.5) / SUB * v[k] for k in range(3))

    def mirror_twins(self):
        """Each left-side face -> the right-side face it reflects (by name,
        *_left* / *_l to *_right* / *_r; east and west swap). The left face
        reuses that face's texture flipped, so the two sides are exact
        mirror images."""
        index = {e["name"]: k for k, e in enumerate(self.elements)}
        twins = {}
        for (ei, f), size in self.visible.items():
            name = self.elements[ei]["name"]
            if "left" in name:
                other = name.replace("left", "right")
            elif name.endswith("_l"):
                other = name[:-2] + "_r"
            else:
                continue
            g = {"east": "west", "west": "east"}.get(f, f)
            key = (index.get(other), g)
            if self.visible.get(key) == size:
                twins[(ei, f)] = key
        return twins

    def paint(self, sizes=(256, 512)):
        """As Creature.paint, packed in px and painted SUB times finer. Left
        faces with a right twin are not painted: they share its pixels."""
        self.visible = self.visible_faces()
        self.twins = self.mirror_twins()
        rects = [(k, w, h) for k, (w, h) in self.visible.items() if k not in self.twins]
        for tex in sizes:
            try:
                self.places = pack(rects, tex)
                break
            except SystemExit:
                continue
        self.tex = tex
        img = Image.new("RGBA", (tex * SUB, tex * SUB), (0, 0, 0, 0))
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            w, h = self.visible[(ei, f)]
            nw = self.world_dir(e, NORMAL[f])
            for i, j, p in self.subtexels(e, f):
                t = Texel()
                t.e, t.f, t.p, t.i, t.j, t.w, t.h = e, f, p, i / SUB, j / SUB, w, h
                t.q = self.world(e, p)
                t.n = nw
                t.light = 0
                t.edge = self.edge(e, f, p, nw)
                t.contact = self.contact(e, f, p)
                img.putpixel((ox * SUB + i, oy * SUB + j), self.painters[e["part"]](t))
        for k, twin in self.twins.items():
            self.places[k] = self.places[twin]
        self.img = img
        return img

    def render(self, yaw, pitch, scale, size, silhouette=False, anchor=0.85):
        """Orthographic painter's render of every texture pixel (rest pose)."""
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

        def proj(q):
            x, y, z = q
            x1, z1 = x * cy - z * sy, x * sy + z * cy
            return x1, y * cp - z1 * sp, y * sp + z1 * cp

        quads = []
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            o, u, v, w, h = face_frame(e, f)
            M = e["M"]
            flip = (ei, f) in self.twins
            for j in range(int(h) * SUB):
                for i in range(int(w) * SUB):
                    ti = int(w) * SUB - 1 - i if flip else i
                    cs = []
                    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        q = [o[k] + (i + di) / SUB * u[k] + (j + dj) / SUB * v[k] for k in range(3)]
                        cs.append(proj(M[:3, :3] @ np.array(q) + M[:3, 3]))
                    col = (20, 20, 24, 255) if silhouette else self.img.getpixel((ox * SUB + ti, oy * SUB + j))
                    quads.append((sum(c[2] for c in cs) / 4, cs, col))
        out = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(out)
        cx, cyy = size[0] / 2, size[1] * anchor
        for _, cs, col in sorted(quads, key=lambda q: q[0]):
            d.polygon([(cx + c[0] * scale, cyy - c[1] * scale) for c in cs], fill=col)
        return out

    def mirror_errors(self):
        """Faces whose texture is not the exact reflection of their mirror
        face's (the tail, on one side only, is left out)."""
        img = np.asarray(self.img).astype(int)
        index = {e["name"]: k for k, e in enumerate(self.elements)}

        def pixels(key):
            (ox, oy), (w, h) = self.places[key], self.visible[key]
            a = img[oy * SUB:(oy + h) * SUB, ox * SUB:(ox + w) * SUB]
            return a[:, ::-1] if key in self.twins else a

        bad = []
        for (ei, f) in self.visible:
            e = self.elements[ei]
            name = e["name"]
            if e["part"] in ("tail", "spade") or "right" in name or name.endswith("_r"):
                continue
            other = name.replace("left", "right") if "left" in name else                 name[:-2] + "_r" if name.endswith("_l") else name
            key = (index[other], {"east": "west", "west": "east"}.get(f, f))
            a = pixels((ei, f))
            b = pixels(key)[:, ::-1] if key in self.visible else None
            if b is None or a.shape != b.shape or np.abs(a - b).max() > 0:
                bad.append(f"{name}.{f}")
        return bad

    def write_bbmodel(self, out_dir, imp_height_px=IMP_HEIGHT_PX):
        """As Creature.write_bbmodel; the image is SUB times the UV size, and
        the left twins' UVs run right to left (Blockbench's mirrored UV)."""
        super().write_bbmodel(out_dir, imp_height_px)
        path = Path(out_dir) / f"{self.name}.bbmodel"
        model = json.loads(path.read_text())
        for tx in model["textures"]:
            tx["width"] = tx["height"] = self.tex * SUB
        for (ei, f) in self.twins:
            uv = model["elements"][ei]["faces"][f]["uv"]
            uv[0], uv[2] = uv[2], uv[0]
        path.write_text(json.dumps(model, indent="\t"))

    def backdrop(self, w, h, tile):
        top, bot = np.array((43, 36, 64)), np.array((92, 80, 120))
        yy, xx = np.mgrid[0:h, 0:w]
        k = (0.6 * yy / h + 0.4 * (xx % tile) / tile)[..., None]
        rgb = (top + (bot - top) * k).astype(np.uint8)
        return Image.fromarray(np.dstack([rgb, np.full((h, w), 255, np.uint8)]), "RGBA")

    def closeup(self, path, size=900, scale=19, ss=3):
        """The face, front on, for checking the eyes."""
        bg = self.backdrop(size, size, size)
        anchor = (size / 2 + 50 * scale) / size
        big = self.render(180, 2, scale * ss, (size * ss, size * ss), anchor=anchor)
        bg.alpha_composite(big.resize((size, size), Image.LANCZOS))
        bg.convert("RGB").save(path)

    def hero(self, path, views, tile=900, scale=10.5, ss=3):
        """A presentation render: views side by side on the portrait's purple
        backdrop, supersampled, each standing in a soft shadow."""
        bg = self.backdrop(tile * len(views), tile, tile)
        for i, (yaw, pitch) in enumerate(views):
            shadow = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).ellipse((tile * 0.27, tile * 0.86, tile * 0.73, tile * 0.95),
                                           fill=(15, 10, 30, 120))
            bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(tile / 60)), (i * tile, 0))
            big = self.render(yaw, pitch, scale * ss, (tile * ss, tile * ss), anchor=0.9)
            bg.alpha_composite(big.resize((tile, tile), Image.LANCZOS), (i * tile, 0))
        bg.convert("RGB").save(path)


IMPLING_HD = ImplingHD("implingz_voxel_character_model", ELEMENTS, BONES, PAINTERS, {})

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    out.mkdir(parents=True, exist_ok=True)
    bbcreature.PX = PX_HD
    m = IMPLING_HD
    m.paint(sizes=(256, 512))
    bad = m.mirror_errors()
    assert not bad, f"not mirrored: {bad}"
    m.previews(out, scale=4.5, tile=(440, 400), anchor=0.92)
    m.write_bbmodel(out)
    m.hero(out / "implingz_voxel_character_model_render.png", [(180, 4), (-148, 14), (-35, 14)])
    m.closeup(out / "implingz_voxel_character_model_face.png")
    top = max(m.world(e, c)[1] for e in m.elements for c in corners(e))
    print(f"boxes: {len(m.elements)}  visible faces: {len(m.visible)} "
          f"({len(m.twins)} share their mirror twin's pixels, every face mirrors exactly)  "
          f"texture: {m.tex * SUB}x{m.tex * SUB} (uv {m.tex})  "
          f"height: {top:.1f} px = {top / 64:.3f} m")
