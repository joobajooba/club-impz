"""Build the Blockbench eagle: a bald eagle, 0.9 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m, so the
  0.9 m the user asked for is 29 px from the soles to the crown (0.906 m,
  the nearest whole pixel).
- Box sizes in whole texture pixels. Odd widths for the centred parts (body,
  head, beak, tail) so the face and tail have a centre column.
- Per-face UV, one texture, hidden faces removed except the ones an
  animation opens up (under the wings, inside the beak).
- Lit from the top, slightly front-left; hue-shifted ramps (the browns'
  shadows lean plum, the whites' lean lavender, highlights lean warm),
  edge highlights where the surface turns over, painted shadow where parts
  meet. Feathers are painted as groups that follow the form: scallop rows on
  the body, banded coverts and secondaries on the wings, quill partings on
  the primaries and the tail (STUDY 5.3).
- There is no eagle icon, so the colours follow ART-DIRECTION section 5:
  dark chocolate plumage, a white head and tail, and the yellow beak, eyes
  and feet as the one saturated accent.

The rig (bones use the shared names, pivots at the joints):
- The body is modelled level, as it is in flight, and turned nose-up by
  TILT at rest so the eagle stands upright, as Minecraft's parrot does. A
  flight pose is the body turned back by TILT, and the wings then open in the
  body's own axes.
- The neck turns back by TILT, so the head sits level at rest with its pixel
  grid square to the world, and head turns are about the vertical. TILT is
  the 3-4-5 angle, so the neck's pivot lands on whole pixels and the neck and
  head are written below in world pixels (UPRIGHT moves them into the body's
  frame).
- The thighs pivot on the body's own pitch axis at the hip, so they stand
  straight down at rest. Leg poses in the animations are solved in world
  space (two-bone IK, heel back like a real bird) and turned into keys, so
  the feet stay planted while the body moves.
- Wings fold along the flanks. Spreading one is two clean steps: x 90 raises
  it straight up (it turns in its own plane, so it never cuts the body),
  then z opens it like a door hinged at the shoulder. In flight z is the
  flap and nothing else; the wing tip bends on y and sweeps back on x.
  Opening z before x is at 90 would swing the trailing edge into the body.
  Right wing: folded (0, 0, 0), up (90, 0, 0), level (90, 0, -90), the
  downstroke to -135, the upstroke to -40. The left wing mirrors y and z.

Animations: idle, walk, run, attack, hit (the docs' set) and the flight
set: takeoff, fly, glide, land. takeoff ends on fly's first frame, land
starts on it and ends on the rest pose. The flight set holds the bird
FLY_HEIGHT above the ground on the root bone.

Usage: python build_eagle_bbmodel.py [out_dir]   (writes eagle.bbmodel,
eagle.png, eagle_preview.png and eagle_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py eagle.bbmodel --spec build_eagle_bbmodel.py
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import clamp, el, fi, hexrgb, mirror, ramp, rot, track, turn_about  # noqa: E402
from bbrig import (RigCreature, const, ease, frames, lin, pair, sampled, solve_legs,  # noqa: E402
                   two_bone, world)
from bbrig import stride as rig_stride  # noqa: E402

# Ramps, darkest first. Browns lean plum in the shadows and tawny in the
# light; whites lean lavender and cream. Kept a step deep: the game's sun
# lifts everything (the cow's white and the chicken's yellow washed out).
BROWN = ramp("#2a1a25", "#41292c", "#5c3a2c", "#7b5133", "#a0703f")    # body and coverts
QUILL = ramp("#1e1622", "#2e2029", "#452e2c", "#5d4131", "#7b583b")    # flight feathers
WHITE = ramp("#7c7896", "#a6a4c0", "#cfcedd", "#ebe7df", "#fbf5e8")    # head, neck, tail
GOLD = ramp("#83410f", "#c2700e", "#e99d1a", "#f9c838", "#ffe377")     # beak, eyes, feet: the accent
TALON = ramp("#231e29", "#3b3542", "#5d5666")
MOUTH = ramp("#4f1a2a", "#86323e", "#b05558")
PUPIL = hexrgb("#1c1420")
GLINT = hexrgb("#fff4e2")

TILT = math.degrees(math.atan2(3, 4))   # 36.87 degrees nose-up at rest (cos 0.8, sin 0.6)
HIP = (0, 9, 2)                         # the body's pivot, on the line through both hips
NECK = (0, 14, -3)                      # the neck's pivot, in the body's frame


def _upright_offset():
    """Where the neck's pivot lands at rest, minus where it is written. The
    neck turns back by TILT, so its whole subtree only moves by this."""
    q = turn_about((TILT, 0, 0), HIP) @ np.array([*NECK, 1.0])
    d = [round(q[k] - NECK[k], 6) for k in range(3)]
    assert all(abs(v * 2 - round(v * 2)) < 1e-6 for v in d), d
    return d


D = _upright_offset()   # (0, 2, 4)


def up(p):
    """A world point (px) of the upright neck and head, in the body's frame."""
    return tuple(p[k] - D[k] for k in range(3))


def upright(name, bone, part, lo, hi):
    return el(name, bone, part, up(lo), up(hi))


def mirror_upright(name, bone, part, lo, hi):
    return mirror(name, bone, part, up(lo), up(hi))


# ---------------------------------------------------------------- geometry

ELEMENTS = [
    # Body, in its own level frame: an 11-wide back with a rounded mantle
    # between the wings, and a deep chest and belly that end at the hip.
    # Behind the hip the underside rises to the tail (the white undertail),
    # as a real eagle's does, so the legs have room to swing and tuck.
    el("body", "body", "plume", (-5.5, 9, -6), (5.5, 16, 6)),
    el("chest", "body", "plume", (-5.5, 6, -6), (5.5, 9, 2)),
    el("breast", "body", "plume", (-4.5, 6, -7), (4.5, 15, -6)),
    el("mantle", "body", "plume", (-4.5, 16, -4), (4.5, 17, 5)),
    el("belly", "body", "plume", (-4.5, 5, -4), (4.5, 6, 1)),
    # Tail: a white wedge, thick at the root, a wider fan, a rounded tip.
    el("tail_root", "tail", "tail", (-3.5, 13, 6), (3.5, 15, 10)),
    el("tail_fan", "tail", "tail", (-4.5, 13, 10), (4.5, 14, 15)),
    el("tail_tip", "tail", "tail", (-3.5, 13, 15), (3.5, 14, 16)),
    # Wings, folded on the flanks. The arm (shoulder to wrist: coverts and
    # secondaries) is 2 px thick, the hand (primaries) 1 px, both centred on
    # the shoulder's pivot so they line up in flight. Three slotted primaries
    # (the eagle's "fingers") reach past the hand with a slot between each.
    *mirror("wing_*_arm", "wing_*", "wing", (5.5, 8, -5), (7.5, 16, 6)),
    *mirror("wing_*_hand", "wing_tip_*", "wing", (6, 10, 6), (7, 16, 14)),
    *mirror("wing_*_finger_1", "wing_tip_*", "finger", (6, 15, 14), (7, 16, 17)),
    *mirror("wing_*_finger_2", "wing_tip_*", "finger", (6, 13, 14), (7, 14, 18)),
    *mirror("wing_*_finger_3", "wing_tip_*", "finger", (6, 11, 14), (7, 12, 16)),
    # Neck and head, written in world pixels (upright). A thick white neck
    # leaving the chest, a squarish head with a jutting brow over each eye
    # (the eagle's scowl) and a rounded crown.
    upright("neck", "neck", "white", (-2.5, 15, -2), (2.5, 23, 3)),
    upright("head", "head", "head", (-3.5, 22, -4), (3.5, 28, 2)),
    upright("crown", "head", "white", (-2.5, 28, -3), (2.5, 29, 1)),
    *mirror_upright("brow_*", "head", "white", (3.5, 26, -4), (4.5, 27, -1)),
    # Upper beak: a deep base flowing from the forehead, stepping down to a
    # hook. The lower beak (jaw) tucks under it, short of the hook.
    upright("beak_base", "beak", "beak", (-1.5, 24, -6), (1.5, 27, -4)),
    upright("beak_mid", "beak", "beak", (-1.5, 24, -7), (1.5, 26, -6)),
    upright("beak_hook", "beak", "beak", (-1.5, 23, -8), (1.5, 25, -7)),
    upright("beak_hook_tip", "beak", "beak", (-0.5, 22, -8), (0.5, 23, -7)),
    upright("jaw", "jaw", "jaw", (-1.5, 23, -6), (1.5, 24, -4)),
    # Legs, in world pixels (the thighs pivot on the body's own axis, so
    # they stand straight): feathered trousers, a yellow scaled tarsus, a
    # foot with three splayed toes, a back toe (hallux) and dark talons.
    *mirror("thigh_*", "thigh_*", "thigh", (1, 3, 0.5), (5, 9, 3.5)),
    *mirror("tarsus_*", "leg_*", "leg", (2, 1, 1), (4, 5, 3)),
    *mirror("foot_*_pad", "foot_*", "toe", (1.5, 0, 1), (4.5, 1, 3)),
    *mirror("toe_*_inner", "foot_*", "toe", (0.5, 0, -2), (1.5, 1, 2)),
    *mirror("toe_*_middle", "foot_*", "toe", (2.5, 0, -3), (3.5, 1, 1)),
    *mirror("toe_*_outer", "foot_*", "toe", (4.5, 0, -2), (5.5, 1, 2)),
    *mirror("toe_*_hallux", "foot_*", "toe", (2.5, 0, 3), (3.5, 1, 5)),
]

# Faces an animation opens up, kept although they are covered at rest: the
# inside of each wing (its top in flight) and both sides of the mouth.
KEEP = {"wing_right_arm": ("west",), "wing_left_arm": ("east",),
        "beak_base": ("down",), "beak_mid": ("down",), "jaw": ("up",)}
for _e in ELEMENTS:
    _e["keep"] = KEEP.get(_e["name"], ())

# Bones: parent, pivot (px, the body's frame), rest rotation (degrees).
BONES = {
    "eagle": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("eagle", HIP, (TILT, 0, 0)),
    "neck": ("body", NECK, (-TILT, 0, 0)),
    "head": ("neck", up((0, 23, 0)), (0, 0, 0)),
    "beak": ("head", up((0, 24, -4)), (0, 0, 0)),
    "jaw": ("head", up((0, 24, -4)), (0, 0, 0)),
    "wing_right": ("body", (6.5, 16, -4), (0, 0, 0)),
    "wing_tip_right": ("wing_right", (6.5, 16, 6), (0, 0, 0)),
    "wing_left": ("body", (-6.5, 16, -4), (0, 0, 0)),
    "wing_tip_left": ("wing_left", (-6.5, 16, 6), (0, 0, 0)),
    "tail": ("body", (0, 14, 6), (0, 0, 0)),
    "thigh_right": ("body", (3, 9, 2), (-TILT, 0, 0)),
    "leg_right": ("thigh_right", (3, 5, 2), (0, 0, 0)),
    "foot_right": ("leg_right", (3, 1, 2), (0, 0, 0)),
    "thigh_left": ("body", (-3, 9, 2), (-TILT, 0, 0)),
    "leg_left": ("thigh_left", (-3, 5, 2), (0, 0, 0)),
    "foot_left": ("leg_left", (-3, 1, 2), (0, 0, 0)),
}

# For check_clipping.py: where skin may fold at a joint (child: [(other bone,
# radius px, deepest fold px)]). The wing roots roll against the flank in a
# flap (at most 0.41 px, the corner of a 2 px thick wing turning on its
# centre); the hand slides inside the thicker arm when it sweeps back, out
# of sight (at most 0.82 px); the trousers press into the chest feathers in
# the run's stride and the takeoff's spring (at most 1.15 px).
JOINTS = {
    "wing_right": [("body", 9, 0.5)], "wing_left": [("body", 9, 0.5)],
    "wing_tip_right": [("wing_right", 7, 1.0)], "wing_tip_left": [("wing_left", 7, 1.0)],
    "thigh_right": [("body", 5, 1.25)], "thigh_left": [("body", 5, 1.25)],
    "leg_right": [("thigh_right", 3.5)], "leg_left": [("thigh_left", 3.5)],
    "neck": [("body", 5)], "head": [("neck", 4)], "tail": [("body", 4)],
    "beak": [("head", 2.5)], "jaw": [("head", 2.5), ("beak", 2.5)],
}


# ---------------------------------------------------------------- painting

def scallop(a, b, v, w=3):
    """Feather rows: feathers w px wide and 3 rows tall, every other row
    offset by half a feather. The lowest row of each feather is its tip: a
    light fleck in the middle with a dark notch either side, so the rows read
    as overlapping layers, not stripes. a runs along a row, b counts rows."""
    r = b // 3
    c = (a + (r % 2) * (w // 2 + 1)) % w
    if b % 3 == 0:
        return v - 1 if c == 0 else v
    if b % 3 == 1 and c == w // 2:
        return v + 1
    return v


def bib(t):
    """The white hood ends on the upper chest in jagged feather points."""
    x, y, z = t.q
    xi = fi(x)
    jag = (0, 1, 0, -1, 1, 0, -1)[xi % 7]
    return y >= 17.5 + jag + max(0, z - 1) * 0.6


def paint_plume(t):
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f in ("up", "north") and bib(t):
        return WHITE[clamp(v - (1 if t.contact else 0), 1)]
    if t.f == "down":
        if t.e["name"] == "body":
            return WHITE[clamp(scallop(xi, zi, 2), 1, 2)]     # the white undertail
        return BROWN[clamp(v, 0, 1)]
    if t.f in ("east", "west"):
        v = scallop(-zi, yi, v)
    elif t.f == "north":
        v = scallop(xi, yi, v)
    elif t.f == "up":
        v = scallop(xi, -zi, v)
    else:
        v = scallop(xi, yi, v) - 1
    return BROWN[clamp(v, 0, 3)]


def wing_band(yi, zi, dorsal):
    """The arm's feather groups by row, top (the leading edge) down: small
    lesser coverts, larger greater coverts, then the long secondaries with a
    dark parting every 2 px and darker tips on the trailing edge."""
    if yi >= 14:
        v = 3 if dorsal else 2
        return BROWN, v - (1 if (zi + yi) % 2 == 0 and yi == 14 else 0)
    if yi >= 11:
        v = 2 if dorsal else 2
        c = (zi + (1 if yi == 12 else 0)) % 3
        if yi == 11 and c == 0:
            v -= 1
        elif yi == 13 and c == 1:
            v += 1
        return BROWN, v
    v = 3 if dorsal else 2
    if zi % 2 == 0:
        v -= 1
    if yi == 8:
        v -= 1
    return QUILL, v


def hand_band(yi, zi, dorsal):
    """The hand: primary coverts at its root, then long primaries with a
    parting every other row, darkening toward the tip."""
    if zi <= 6:
        return BROWN, (3 if dorsal else 2) - (1 if yi % 2 else 0)
    v = 3 if dorsal else 2
    if yi % 2 == 1:
        v -= 1
    if zi >= 12:
        v -= 1
    return QUILL, v


def paint_wing(t):
    x, y, z = t.p
    yi, zi = fi(y), fi(z)
    hand = t.e["name"].endswith("_hand")
    if t.f in ("east", "west"):
        outer = (t.f == "east") == (x > 0)
        band = hand_band if hand else wing_band
        r, v = band(yi, zi, not outer)
        v += (t.light - 1) if outer else 0     # the outside takes the scene light;
        return r[clamp(v, 0, 4)]               # the inside is the top in flight
    if t.f == "up":                            # the leading edge
        return BROWN[4] if t.edge else BROWN[3]
    if t.f == "down":                          # the trailing edge
        return QUILL[1]
    return QUILL[2] if t.f == "north" else QUILL[1]


def paint_finger(t):
    v = t.shade
    if t.f == "up":
        return QUILL[3]
    if t.f == "south":
        return QUILL[0]                        # dark tips
    return QUILL[clamp(v, 1, 3)]


def paint_tail(t):
    """White tail feathers: a lavender parting every 2 px along the tail,
    shadowed at the root, a cream tip."""
    x, y, z = t.p
    xi, zi = fi(x), fi(z)
    v = t.shade
    if t.f == "up":
        if xi % 2 == 1 and abs(x) < 3.5:
            v -= 1
        if zi <= 7:
            v -= 1
        return WHITE[clamp(v + 1, 1, 4)]
    if t.f == "down":
        return WHITE[1]
    return WHITE[clamp(v, 1, 3)]


def paint_white(t):
    x, y, z = t.q
    v = t.shade
    if t.f == "down":
        return WHITE[1]
    if t.e["name"].startswith("brow") and t.f in ("north", "east", "west"):
        return WHITE[clamp(v + 1, 2, 4)]
    if t.e["name"] == "neck" and t.f in ("east", "west", "south") and fi(z) % 2 == 0:
        v -= 1                                 # hackle streaks down the neck
    return WHITE[clamp(v + 1, 1, 4)]


EYE = {(25, -3): "iris_dark", (25, -2): "pupil", (24, -3): "glint", (24, -2): "iris"}


def paint_head(t):
    """White head. On each side: a pale yellow eye under the brow (the
    brow's shadow on its top row), the yellow gape running back from the
    beak under it."""
    x, y, z = t.q
    yi, zi = fi(y), fi(z)
    v = t.shade
    if t.f in ("east", "west"):
        k = EYE.get((yi, zi))
        if k == "pupil":
            return PUPIL
        if k == "glint":
            return GLINT if t.f == "west" else GOLD[3]
        if k == "iris":
            return GOLD[3]
        if k == "iris_dark":
            return GOLD[2]
        if yi == 24 and zi == -4:
            return GOLD[2]                     # the gape
        if yi == 23 and zi in (-4, -3):
            return WHITE[1]                    # shadow under the gape
        if yi == 25 and zi == -4:
            return WHITE[2]
    if t.f == "down":
        return WHITE[1]
    if t.f == "north" and t.contact:
        return WHITE[2]
    return WHITE[clamp(v + 1, 1, 4)]


def paint_beak(t):
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    name = t.e["name"]
    v = t.shade
    if t.f == "down" and name in ("beak_base", "beak_mid"):
        return MOUTH[1]                        # the roof of the mouth
    if name == "beak_hook_tip" or (name == "beak_hook" and t.f == "north"):
        return GOLD[clamp(v - 1, 1, 3)]        # the hook darkens at the point
    if name == "beak_base" and t.f in ("east", "west") and yi == 25 and zi == -5:
        return GOLD[0]                         # nostril
    if t.f == "up":
        return GOLD[4] if xi == -1 else GOLD[3]   # the ridge catches the light
    return GOLD[clamp(v, 1, 4)]


def paint_jaw(t):
    if t.f == "up":
        return MOUTH[2]
    return GOLD[clamp(t.shade - 1, 1, 3)]


def paint_thigh(t):
    """Feathered trousers: soft brown, with ragged strokes along the hem."""
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    if t.f == "down":
        return BROWN[0]
    v = t.shade
    along = zi if t.f in ("east", "west") else xi
    if yi == 3 and along % 2 == 0:
        v -= 1
    if yi == 4 and along % 3 == 1:
        v -= 1
    return BROWN[clamp(v, 0, 3)]


def paint_leg(t):
    """Scaled tarsus: a darker ring between the scales."""
    v = t.shade
    if fi(t.p[1]) == 2:
        v -= 1
    return GOLD[clamp(v, 1, 3)]


def paint_toe(t):
    x, y, z = t.p
    name = t.e["name"]
    zi = fi(z)
    if t.f == "down":
        return GOLD[0]
    if "hallux" in name:
        talon = zi == 4
    elif "pad" in name:
        talon = False
    else:
        talon = zi == fi(t.e["lo"][2])         # the front pixel of a toe
    if talon:
        return TALON[clamp(t.shade - 1, 0, 2)]
    return GOLD[clamp(t.shade, 1, 4)]


PAINTERS = {"plume": paint_plume, "wing": paint_wing, "finger": paint_finger,
            "tail": paint_tail, "white": paint_white, "head": paint_head,
            "beak": paint_beak, "jaw": paint_jaw, "thigh": paint_thigh,
            "leg": paint_leg, "toe": paint_toe}


# ---------------------------------------------------------------- animation
#
# Keys are in Blockbench's convention (bbrig.py): a positive x turns the
# beak down or the tail up, a positive y turns the head to its right, and a
# positive z rolls the right side up.

FLY_HEIGHT = 16           # px the flight set holds the bird above the ground
TUCK = (-TILT, -80, -95)  # thigh, tarsus, foot world pitch in flight: the thighs keep
                          # their rest angle to the level body, the feet trail back
ANKLE = (1, 2)            # the foot's pivot at rest (y, z px)


def legs(length, body_rot, body_pos=const((0, 0, 0)), root_pos=const((0, 0, 0)),
         right=None, left=None):
    """Thigh, leg and foot keys, every frame, for both legs (heel back, like
    a bird's). Default: planted where they stand."""
    planted = const(("plant", ANKLE, 0))
    return solve_legs(BONES, length,
                      [("thigh_right", "leg_right", "foot_right", 1, right or planted),
                       ("thigh_left", "leg_left", "foot_left", 1, left or planted)],
                      rot={"body": body_rot}, pos={"body": body_pos, "eagle": root_pos})


def stride(period, phase, reach, lift, duty=0.55):
    return rig_stride(period, phase, ANKLE, reach, lift, duty)


def wings(**k):
    """Both wings (wing=[...]) and/or both tips (tip=[...]) from right-side
    keys."""
    interp = k.get("interp", "linear")
    out = {}
    if "wing" in k:
        out.update(pair("wing_*", k["wing"], interp))
    if "tip" in k:
        out.update(pair("wing_tip_*", k["tip"], interp))
    return out


FLY_START = {   # fly's first frame: takeoff ends on it, land starts on it
    "body": (TILT, 0, 0), "neck": (23.13, 0, 0), "head": (-50, 0, 0),
    "wing": (90, 0, -40), "tip": (0, 0, 0), "tail": (0, 0, 0),
}


def idle():
    L = 4.0
    return {"loop": "loop", "length": L, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.0, (1.02, 1, 1.02)), (2.0, (1, 1, 1)),
                                (3.0, (1.02, 1, 1.02)), (4.0, (1, 1, 1))]),
        "neck": rot((0, (0, 0, 0)), (2.0, (-3, 0, 0)), (4.0, (0, 0, 0))),
        # An eagle's head holds still, then snaps to a new look.
        "head": lin((0, (0, 0, 0)), (0.6, (0, 0, 0)), (0.68, (0, 28, 0)), (1.4, (0, 28, 0)),
                    (1.48, (8, 30, 6)), (1.9, (8, 30, 6)), (1.98, (0, -26, -4)),
                    (2.7, (0, -26, -4)), (2.78, (12, 0, 0)), (3.4, (12, 0, 0)),
                    (3.48, (0, 0, 0)), (4.0, (0, 0, 0))),
        "jaw": lin((0, (0, 0, 0)), (3.0, (0, 0, 0)), (3.08, (12, 0, 0)), (3.16, (0, 0, 0)),
                   (3.24, (10, 0, 0)), (3.32, (0, 0, 0)), (4.0, (0, 0, 0))),
        "tail": lin((0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.28, (0, 6, 0)), (1.38, (0, -4, 0)),
                    (1.5, (0, 0, 0)), (4.0, (0, 0, 0))),
        **wings(wing=[(0, (0, 0, 0)), (2.2, (0, 0, 0)), (2.35, (0, 0, 9)), (2.55, (0, 0, 3)),
                      (2.7, (0, 0, 0)), (4.0, (0, 0, 0))], interp="catmullrom"),
    }}


def walk():
    L = 1.2
    body_rot = lambda t: (2 + 1.5 * math.sin(4 * math.pi * t / L),        # noqa: E731
                          3 * math.cos(2 * math.pi * t / L), -3 * math.sin(2 * math.pi * t / L))
    body_pos = lambda t: (0, -0.3 + 0.15 * (1 - math.cos(4 * math.pi * t / L)), 0)   # noqa: E731
    return {"loop": "loop", "length": L, "bones": {
        "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
        **legs(L, body_rot, body_pos, right=stride(L, 0.0, 1.2, 1.5), left=stride(L, 0.5, 1.2, 1.5)),
        "neck": sampled("rotation", L, lambda t: (-2 - 1.5 * math.sin(4 * math.pi * t / L), 0, 0)),
        "head": sampled("rotation", L, lambda t: (0, -3 * math.cos(2 * math.pi * t / L),
                                                  3 * math.sin(2 * math.pi * t / L)))
        + sampled("position", L, lambda t: (0, 0, -0.6 * max(0.0, math.sin(4 * math.pi * t / L)))),
        "tail": sampled("rotation", L, lambda t: (0, 5 * math.sin(2 * math.pi * t / L), 0)),
        **wings(wing=[(t, (0, 0, 6 + 2 * math.sin(4 * math.pi * t / L))) for t in frames(L)[::3]]),
    }}


def run():
    L = 0.6
    body_rot = lambda t: (15 + 3 * math.sin(4 * math.pi * t / L), 0,      # noqa: E731
                          -4 * math.sin(2 * math.pi * t / L))
    body_pos = lambda t: (0, -0.8 + 0.6 * (1 - math.cos(4 * math.pi * t / L)), 0)   # noqa: E731
    return {"loop": "loop", "length": L, "bones": {
        "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
        **legs(L, body_rot, body_pos, right=stride(L, 0.0, 1.8, 2.5, 0.5),
               left=stride(L, 0.5, 1.8, 2.5, 0.5)),
        "neck": rot((0, (18, 0, 0)), (L, (18, 0, 0))),
        "head": rot((0, (-16, 0, 0)), (L, (-16, 0, 0))),
        "jaw": rot((0, (8, 0, 0)), (L, (8, 0, 0))),
        "tail": sampled("rotation", L, lambda t: (4 * math.sin(4 * math.pi * t / L), 0, 0)),
        # Wings held up and half open, beating for balance.
        **wings(wing=[(0, (90, 0, -55)), (0.15, (90, 0, -95)), (0.3, (90, 0, -55)),
                      (0.45, (90, 0, -95)), (0.6, (90, 0, -55))],
                tip=[(0, (0, -12, 0)), (0.15, (0, 14, 0)), (0.3, (0, -12, 0)),
                     (0.45, (0, 14, 0)), (0.6, (0, -12, 0))], interp="catmullrom"),
    }}


def attack():
    """Mantle (rear up, wings raised in a V, beak open), then lunge: the head
    stabs, the right foot strikes with its talons, the wings sweep down for
    balance. Settle, fold."""
    L = 1.25
    body_rot = ease([(0, (0, 0, 0)), (0.3, (-8, 0, 0)), (0.48, (15, 0, 0)),
                     (0.62, (12, 0, 0)), (0.9, (0, 0, 0)), (L, (0, 0, 0))])
    strike = ease([(0, (1.0, 2.0)), (0.3, (2.0, 1.0)), (0.48, (4.0, -2.5)),
                   (0.62, (3.5, -2.0)), (0.88, (1.0, 2.0)), (L, (1.0, 2.0))])
    talon = ease([(0, 0), (0.3, 10), (0.48, 45), (0.62, 40), (0.88, 0), (L, 0)])
    return {"loop": "once", "length": L, "bones": {
        "body": sampled("rotation", L, body_rot),
        **legs(L, body_rot, right=lambda t: ("plant", strike(t), talon(t))),
        "neck": rot((0, (0, 0, 0)), (0.3, (-16, 0, 0)), (0.48, (26, 0, 0)), (0.62, (20, 0, 0)),
                    (0.9, (0, 0, 0)), (L, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.3, (-8, 0, 0)), (0.48, (12, 0, 0)), (0.62, (8, 0, 0)),
                    (0.9, (0, 0, 0)), (L, (0, 0, 0))),
        "jaw": lin((0, (0, 0, 0)), (0.3, (14, 0, 0)), (0.48, (30, 0, 0)), (0.62, (22, 0, 0)),
                   (0.85, (0, 0, 0)), (L, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.3, (10, 0, 0)), (0.48, (-6, 0, 0)), (0.9, (0, 0, 0)),
                    (L, (0, 0, 0))),
        # x reaches 90 (wings straight up) before z opens them, and z is
        # closed again before x folds them down.
        **wings(wing=[(0, (0, 0, 0)), (0.25, (90, 0, 0)), (0.36, (90, 0, -40)),
                      (0.5, (90, 0, -85)), (0.62, (90, 0, -75)), (0.85, (90, 0, 0)),
                      (1.1, (0, 0, 0)), (L, (0, 0, 0))],
                tip=[(0, (0, 0, 0)), (0.36, (0, 10, 0)), (0.5, (0, -12, 0)), (0.62, (0, -6, 0)),
                     (0.85, (0, 0, 0)), (L, (0, 0, 0))]),
    }}


def hit():
    L = 0.5
    body_rot = ease([(0, (0, 0, 0)), (0.06, (-7, 0, 3)), (0.2, (2, 0, -1)), (L, (0, 0, 0))])
    return {"loop": "once", "length": L, "bones": {
        "body": sampled("rotation", L, body_rot),
        **legs(L, body_rot),
        "neck": rot((0, (0, 0, 0)), (0.06, (-12, 0, 0)), (0.2, (4, 0, 0)), (L, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.06, (-10, 12, 6)), (0.2, (3, -4, -2)), (L, (0, 0, 0))),
        "jaw": lin((0, (0, 0, 0)), (0.06, (18, 0, 0)), (0.3, (0, 0, 0)), (L, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.06, (12, 0, 0)), (0.2, (-4, 0, 0)), (L, (0, 0, 0))),
        **wings(wing=[(0, (0, 0, 0)), (0.06, (0, 0, 24)), (0.22, (0, 0, 6)), (L, (0, 0, 0))],
                interp="catmullrom"),
    }}


def fly():
    L = 0.8
    root = lambda t: (0, FLY_HEIGHT + 0.8 * math.sin(2 * math.pi * t / L), 0)   # noqa: E731
    body_rot = lambda t: (TILT - 2 * math.sin(2 * math.pi * t / L), 0, 0)      # noqa: E731
    return {"loop": "loop", "length": L, "bones": {
        "eagle": sampled("position", L, root),
        "body": sampled("rotation", L, body_rot),
        **legs(L, body_rot, root_pos=root, right=const(("free", TUCK)), left=const(("free", TUCK))),
        "neck": rot((0, FLY_START["neck"]), (L, FLY_START["neck"])),
        "head": sampled("rotation", L, lambda t: (-50 + 2 * math.sin(2 * math.pi * t / L), 0, 0)),
        "tail": sampled("rotation", L, lambda t: (3 * math.sin(2 * math.pi * t / L + 1), 0, 0)),
        # Downstroke to the bottom at 0.4, upstroke back. The hand lags: bent
        # up on the way down, bent down and swept back on the way up.
        **wings(wing=[(0, (90, 0, -40)), (0.4, (90, 0, -135)), (L, (90, 0, -40))],
                tip=[(0, (0, 0, 0)), (0.2, (0, 22, 0)), (0.4, (0, 4, 0)), (0.6, (-8, -12, 0)),
                     (L, (0, 0, 0))], interp="catmullrom"),
    }}


def glide():
    L = 2.4
    root = lambda t: (0, FLY_HEIGHT + 0.5 * math.sin(2 * math.pi * t / L), 0)   # noqa: E731
    body_rot = lambda t: (TILT, 0, 7 * math.sin(2 * math.pi * t / L))           # noqa: E731
    return {"loop": "loop", "length": L, "bones": {
        "eagle": sampled("position", L, root),
        "body": sampled("rotation", L, body_rot),
        **legs(L, body_rot, root_pos=root, right=const(("free", TUCK)), left=const(("free", TUCK))),
        "neck": rot((0, FLY_START["neck"]), (L, FLY_START["neck"])),
        "head": sampled("rotation", L, lambda t: (-50, 16 * math.sin(2 * math.pi * t / L + 0.6),
                                                  -7 * math.sin(2 * math.pi * t / L))),
        "tail": sampled("rotation", L, lambda t: (-2, 7 * math.sin(2 * math.pi * t / L), 0)),
        # Wings level with a little lift at the fingers, flexing as it banks.
        "wing_right": sampled("rotation", L, lambda t: (90, 0, -88 + 3 * math.sin(2 * math.pi * t / L))),
        "wing_left": sampled("rotation", L, lambda t: (90, 0, 88 + 3 * math.sin(2 * math.pi * t / L))),
        **wings(tip=[(0, (0, 8, 0)), (L, (0, 8, 0))]),
    }}


def takeoff():
    """Crouch with the wings raised, spring, two big strokes, into fly."""
    L = 1.2
    root = ease([(0, (0, 0, 0)), (0.25, (0, 0, 0)), (0.4, (0, 4, 0)), (0.5, (0, 7, 0)),
                 (0.75, (0, 10, 0)), (1.0, (0, 14.5, 0)), (L, (0, FLY_HEIGHT, 0))])
    body_pos = ease([(0, (0, 0, 0)), (0.25, (0, -2, 0)), (0.4, (0, 0, 0)), (L, (0, 0, 0))])
    body_rot = ease([(0, (0, 0, 0)), (0.25, (8, 0, 0)), (0.45, (26, 0, 0)), (0.8, (TILT + 3, 0, 0)),
                     (L, (TILT, 0, 0))])
    lift = 0.5

    def leg(t):
        if t < lift:
            return ("plant", (1, 2), 0)
        u = min(1.0, (t - lift) / 0.45)
        u = u * u * (3 - 2 * u)
        return ("free", tuple(a * u for a in TUCK))

    return {"loop": "once", "length": L, "bones": {
        "eagle": sampled("position", L, root),
        "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
        **legs(L, body_rot, body_pos, root, right=leg, left=leg),
        "neck": rot((0, (0, 0, 0)), (0.25, (12, 0, 0)), (0.6, (18, 0, 0)), (L, FLY_START["neck"])),
        "head": rot((0, (0, 0, 0)), (0.25, (-10, 0, 0)), (0.6, (-30, 0, 0)), (L, FLY_START["head"])),
        "tail": rot((0, (0, 0, 0)), (0.25, (10, 0, 0)), (0.5, (-8, 0, 0)), (L, (0, 0, 0))),
        **wings(wing=[(0, (0, 0, 0)), (0.25, (90, 0, 0)), (0.45, (90, 0, -135)),
                      (0.72, (90, 0, -40)), (0.98, (90, 0, -135)), (L, FLY_START["wing"])],
                tip=[(0, (0, 0, 0)), (0.25, (0, 0, 0)), (0.35, (0, 22, 0)), (0.45, (0, 4, 0)),
                     (0.6, (-8, -12, 0)), (0.72, (0, 0, 0)), (0.85, (0, 22, 0)),
                     (0.98, (0, 4, 0)), (1.1, (-6, -8, 0)), (L, FLY_START["tip"])]),
    }}


def land():
    """Glide in, flare upright with the feet thrown forward, brake with a
    stroke, touch down and absorb it, close the wings up, then fold."""
    L = 1.5
    root = ease([(0, (0, FLY_HEIGHT, 0)), (0.3, (0, 12, 0)), (0.55, (0, 6, 0)),
                 (0.78, (0, 0, 0)), (L, (0, 0, 0))])
    body_pos = ease([(0, (0, 0, 0)), (0.78, (0, 0, 0)), (0.9, (0, -2, 0)), (1.15, (0, -0.5, 0)),
                     (L, (0, 0, 0))])
    body_rot = ease([(0, (TILT, 0, 0)), (0.3, (20, 0, 0)), (0.6, (-6, 0, 0)), (0.78, (-4, 0, 0)),
                     (0.92, (10, 0, 0)), (1.2, (0, 0, 0)), (L, (0, 0, 0))])
    reach = 0.6
    # The free legs swing down and forward to exactly where the planted
    # solve takes over, so there is no pop at the switch.
    M = world(BONES, "body", {"body": body_rot(reach)}, {"body": body_pos(reach), "eagle": root(reach)})
    hip = (M @ np.array([3, 9, 2, 1.0]))[:3]
    target = ease([(0, (1.0, -1.0)), (reach, (1.0, -1.0)), (0.78, (1.0, 1.0)), (L, (1.0, 2.0))])
    meet = (*two_bone((hip[1], hip[2]), target(reach), 4, 4), 15.0)
    swing = ease([(0, TUCK), (0.3, (5, 0, 0)), (reach, meet)])

    def leg(t):
        if t < reach:
            return ("free", swing(t))
        phi = ease([(reach, 15.0), (0.78, 0.0), (L, 0.0)])(t)
        return ("plant", target(t), phi)

    return {"loop": "once", "length": L, "bones": {
        "eagle": sampled("position", L, root),
        "body": sampled("rotation", L, body_rot) + sampled("position", L, body_pos),
        **legs(L, body_rot, body_pos, root, right=leg, left=leg),
        "neck": rot((0, FLY_START["neck"]), (0.3, (10, 0, 0)), (0.6, (-6, 0, 0)), (0.9, (8, 0, 0)),
                    (1.2, (0, 0, 0)), (L, (0, 0, 0))),
        "head": rot((0, FLY_START["head"]), (0.3, (-25, 0, 0)), (0.6, (6, 0, 0)), (0.9, (-4, 0, 0)),
                    (1.2, (0, 0, 0)), (L, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.3, (-10, 0, 0)), (0.6, (-18, 0, 0)), (0.9, (4, 0, 0)),
                    (1.2, (0, 0, 0)), (L, (0, 0, 0))),
        # z closes to 0 (wings straight up) before x folds them down.
        **wings(wing=[(0, FLY_START["wing"]), (0.3, (90, 0, -90)), (0.5, (90, 0, -55)),
                      (0.7, (90, 0, -110)), (0.98, (90, 0, 0)), (1.3, (0, 0, 0)), (L, (0, 0, 0))],
                tip=[(0, FLY_START["tip"]), (0.3, (0, 8, 0)), (0.5, (-8, -10, 0)),
                     (0.7, (0, 18, 0)), (0.98, (0, 0, 0)), (L, (0, 0, 0))]),
    }}


ANIMATIONS = {"idle": idle(), "walk": walk(), "run": run(), "attack": attack(), "hit": hit(),
              "takeoff": takeoff(), "fly": fly(), "glide": glide(), "land": land()}

EAGLE = RigCreature("eagle", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    EAGLE.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                preview_scale=10, tile=(420, 380), anchor=0.86)
