"""Build the Blockbench dragon: a fierce green dragon, 1.52 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. The 5 ft the
  user asked for is the top of the horns standing on all fours: 49 px
  (1.53 m, the nearest whole pixel to 1.524 m).
- Box sizes in whole texture pixels; odd widths for the centred parts
  (chest, neck base, skull, snout, tail root) so they have a centre column.
- Per-face UV, one texture, hidden faces removed except the ones an
  animation opens up (inside the mouth, the wing bones' inner faces).
- Lit from the top, slightly front-left; hue-shifted ramps (the greens'
  shadows lean blue, their highlights yellow; the belly is earthy tan),
  edge highlights where the surface turns over, painted shadow where parts
  meet. Scales are painted as rows that follow the form, lighter at the top
  of each scale (STUDY 5.3), with armour plates down the back and banded
  plates under the belly; nothing is random noise.
- There is no dragon icon, so the colours follow ART-DIRECTION section 5 and
  the user's brief: a rich natural green kept below the accent, with earthy
  undertones. The amber eyes are the one saturated accent (STUDY 3.1:
  hostile creatures get a bright eye).

The rig (shared bone names, pivots at the joints):
- The body is level and pivots on the hind hips, so it can rear up on its
  hind legs. Legs are solved by two-bone IK in the animations (bbrig.py), so
  feet stay planted while the body moves: the elbows bend back, the knees
  forward.
- The neck is three segments in an S. Each is modelled straight up from its
  pivot and bent at rest by the 3-4-5 angle (36.87 degrees): forward,
  upright, back. The head turns back by the same angle, so it sits level
  with its pixel grid square to the world, and its pivot lands on whole
  pixels (UPRIGHT moves the head's world pixels into the model's frame).
- Wings fold along the flanks, just outside the legs, tips raised 15
  degrees. As on the eagle, they open in two clean steps: x raises a wing
  straight up in its own plane (key 75, rest -15), then z opens it. In flight
  z is the flap; wing_mid and wing_tip bend on y (about the chord). They
  don't sweep in the wing's own plane, where their membranes would overlap.
  Right wing: folded (0, 0, 0), up (75, 0, 0), level (75, 0, -90), the
  downstroke to -130, the upstroke to -40. The left mirrors y and z.
- The tail is three segments that droop and taper to a spade, for balance
  and secondary motion.

Animations: idle, look, walk, run, turn_left, turn_right, roar, attack
(bite), claw (swipe), hit, takeoff, fly, hover, land. takeoff ends on fly's
first frame; land starts on it and ends on the rest pose.

Usage: python build_dragon_bbmodel.py [out_dir]   (writes dragon.bbmodel,
dragon.png, dragon_preview.png and dragon_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py dragon.bbmodel --spec build_dragon_bbmodel.py
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import clamp, el, fi, hexrgb, mirror, ramp, turn_about  # noqa: E402
from bbdragon import build, moves, plates, scales, side_coords  # noqa: E402
from bbrig import RigCreature  # noqa: E402

# Ramps, darkest first. Greens lean blue in the shadows and yellow in the
# light, the belly is a warm earthy tan, the membrane an olive leather.
GREEN = ramp("#1a271e", "#2a4129", "#3c5d30", "#567c39", "#7a9c46")     # flank and limb scales
DARK = ramp("#151e19", "#213022", "#30452a", "#425c2f", "#5a7637")      # back plates, stripes
BELLY = ramp("#43341f", "#685130", "#8d703d", "#ae904e", "#ccae66")     # belly plates, throat
MEMBRANE = ramp("#25261b", "#383823", "#4f4e2d", "#686638", "#858245")  # wing leather
HORN = ramp("#3a3024", "#5e4e38", "#857252", "#ad9a74", "#d0c39b")
CLAW = ramp("#1f1a1e", "#372f34", "#585055", "#857a74")
TEETH = ramp("#9e9478", "#cbc2a3", "#ebe3c6")
MOUTH = ramp("#34121a", "#62202a", "#8c3437")
IRIS = ramp("#b8650d", "#ec9a17", "#ffcf3a", "#fff09a")                 # the accent
PUPIL = hexrgb("#1a1110")

TILT = math.degrees(math.atan2(3, 4))   # the neck's bend, 36.87 degrees (cos 0.8, sin 0.6)
HIP = (0, 14, 6)                        # the body's pivot, on the line through both hip joints
NECK = (0, 23, -15)                     # the neck's base, modelled straight up from here
NECK_REST = {"neck_base": -TILT, "neck_mid": TILT, "neck_upper": TILT}


def _head_offset():
    """Where the head's pivot lands at rest minus where it is modelled. The
    neck's bends add up to the head's turn back, so the head only moves."""
    M = np.eye(4)
    for b, piv in (("neck_base", NECK), ("neck_mid", (0, 33, -15)), ("neck_upper", (0, 38, -15))):
        M = M @ turn_about((NECK_REST[b], 0, 0), piv)
    M = M @ turn_about((-TILT, 0, 0), (0, 43, -15))
    q = M @ np.array([0, 43, -15, 1.0])
    d = [round(q[k] - (0, 43, -15)[k], 6) for k in range(3)]
    assert all(abs(v * 2 - round(v * 2)) < 1e-6 for v in d), d
    return d


D = _head_offset()   # (0, -3, -3)


def up(p):
    """A world point (px) of the level head, in the model's frame."""
    return tuple(p[k] - D[k] for k in range(3))


def head_el(name, bone, part, lo, hi):
    return el(name, bone, part, up(lo), up(hi))


def head_mirror(name, bone, part, lo, hi):
    return mirror(name, bone, part, up(lo), up(hi))


# ---------------------------------------------------------------- geometry

ELEMENTS = [
    # Body: broad wing shoulders over a deep chest, a narrower waist, and
    # hips; the underside steps up toward the tail. Armour plates and spines
    # run down the back.
    el("chest", "body", "body", (-7.5, 10, -18), (7.5, 27, -6)),
    el("waist", "body", "body", (-6.5, 14, -6), (6.5, 25, 8)),
    el("hips", "body", "body", (-7.5, 13, 3), (7.5, 26, 12)),
    el("shoulders", "body", "back", (-9.5, 22, -15), (9.5, 28, 2)),
    el("mantle", "body", "back", (-5.5, 26, 2), (5.5, 27, 11)),
    el("spine_1", "body", "spine", (-0.5, 28, -8), (0.5, 30, -5)),
    el("spine_2", "body", "spine", (-0.5, 28, -2), (0.5, 30, 1)),
    el("spine_3", "body", "spine", (-0.5, 27, 5), (0.5, 29, 8)),
    # The big shoulder and haunch muscles sit on the flanks; the legs hang
    # from joints just inside the underside, so a swinging leg never sweeps
    # through the body. Half a pixel in from the legs' sides, so no face
    # ever shares a plane with a leg's.
    *mirror("foreshoulder_*", "body", "body", (7.5, 12, -15), (9.5, 21, -9)),
    *mirror("haunch_*", "body", "body", (7.5, 15, 2), (9.5, 24, 10)),
    el("rump", "body", "body", (-5.5, 16, 12), (5.5, 25, 14)),
    # Neck, modelled straight up from each pivot (the rest bends make the S),
    # tapering 9 - 7 - 6, each segment reaching into the next so a bend never
    # opens a gap. A spine on the back of each.
    el("neck_base", "neck_base", "neck", (-4.5, 21, -19), (4.5, 34, -11)),
    el("neck_base_spine", "neck_base", "spine", (-0.5, 26, -11), (0.5, 29, -9)),
    el("neck_mid", "neck_mid", "neck", (-3.5, 32, -18.5), (3.5, 39, -11.5)),
    el("neck_mid_spine", "neck_mid", "spine", (-0.5, 33, -11.5), (0.5, 35, -9.5)),
    el("neck_upper", "neck_upper", "neck", (-3, 37, -18), (3, 44, -12)),
    el("neck_upper_spine", "neck_upper", "spine", (-0.5, 39, -12), (0.5, 41, -10)),
    # Head, in world pixels (level): a broad skull with a jutting brow over
    # each eye and swept cheek spikes; the upper jaw (snout, nose, a horn on
    # the nose, an overbite of fangs); the lower jaw hinged under the skull,
    # with a chin spike.
    head_el("skull", "head", "skull", (-4.5, 38, -28), (4.5, 43, -19)),
    *head_mirror("brow_*", "head", "skull", (4.5, 41, -28), (5.5, 43, -23)),
    *head_mirror("cheek_spike_*", "head", "spike", (4.5, 38, -21), (5.5, 40, -16)),
    head_el("snout", "jaw_upper", "snout", (-3.5, 39, -36), (3.5, 42, -28)),
    head_el("nose", "jaw_upper", "snout", (-2.5, 39, -38), (2.5, 41, -36)),
    head_el("nose_horn", "jaw_upper", "horn", (-0.5, 42, -34), (0.5, 43, -31)),
    *head_mirror("fang_*", "jaw_upper", "tooth", (2.5, 37, -36), (3.5, 39, -35)),
    head_el("jaw", "jaw", "jaw", (-2.5, 36, -37), (2.5, 39, -28)),
    head_el("jaw_hinge", "jaw", "jaw", (-3.5, 36, -28), (3.5, 38, -26)),
    head_el("chin_spike", "jaw", "spike", (-0.5, 35, -34), (0.5, 36, -30)),
    # Horns: rising up and back from the crown in three stepped pieces to
    # the dragon's full height.
    *head_mirror("horn_*_root", "horn_*", "horn", (2, 43, -24), (4, 46, -19)),
    *head_mirror("horn_*_mid", "horn_*", "horn", (2.5, 45, -19), (4.5, 48, -14)),
    *head_mirror("horn_*_tip", "horn_*", "horn", (3.5, 47, -14), (4.5, 49, -9)),
    # Tail: three tapering segments, modelled straight back from each pivot,
    # drooping at rest; spines along the top and a spade at the end.
    el("tail_root", "tail", "tail", (-3.5, 17.5, 14), (3.5, 24.5, 19)),
    el("tail_root_2", "tail", "tail", (-3, 18, 19), (3, 24, 25)),
    el("tail_spine_1", "tail", "spine", (-0.5, 24.5, 15), (0.5, 26.5, 18)),
    el("tail_mid", "tail_mid", "tail", (-2.5, 18.5, 23), (2.5, 23.5, 31)),
    el("tail_mid_2", "tail_mid", "tail", (-2, 19, 31), (2, 23, 38)),
    el("tail_spine_2", "tail_mid", "spine", (-0.5, 23.5, 26), (0.5, 25.5, 29)),
    el("tail_end", "tail_end", "tail", (-1.5, 19.5, 36), (1.5, 22.5, 44)),
    el("tail_spade", "tail_end", "spade", (-3.5, 20.5, 44), (3.5, 21.5, 48)),
    el("tail_spade_tip", "tail_end", "spade", (-1.5, 20.5, 48), (1.5, 21.5, 50)),
    # Forelegs: an upper arm, a heavy forearm, a hand with three splayed
    # fingers and hooked claws.
    *mirror("arm_*", "arm_*", "limb", (5, 6, -14), (10, 11, -10)),
    *mirror("forearm_*", "forearm_*", "limb", (6, 3, -14.5), (9, 7, -9.5)),
    *mirror("hand_*_palm", "hand_*", "limb", (5.5, 0, -15), (9.5, 3, -9)),
    *mirror("hand_*_finger_1", "hand_*", "limb", (4.5, 0, -17), (5.5, 2, -12)),
    *mirror("hand_*_finger_2", "hand_*", "limb", (7, 0, -18), (8, 2, -15)),
    *mirror("hand_*_finger_3", "hand_*", "limb", (9.5, 0, -17), (10.5, 2, -12)),
    *mirror("hand_*_claw_1", "hand_*", "claw", (4.5, 0, -18), (5.5, 1, -17)),
    *mirror("hand_*_claw_2", "hand_*", "claw", (7, 0, -19), (8, 1, -18)),
    *mirror("hand_*_claw_3", "hand_*", "claw", (9.5, 0, -18), (10.5, 1, -17)),
    # Hind legs: a heavy thigh, a shin, a foot with three toes, claws and a
    # back spur.
    *mirror("thigh_*", "thigh_*", "limb", (5, 7, 2.5), (10, 15, 9.5)),
    *mirror("shin_*", "leg_*", "limb", (6, 3, 4), (9, 9, 8)),
    *mirror("foot_*_heel", "foot_*", "limb", (5.5, 0, 3), (9.5, 3, 9)),
    *mirror("foot_*_toe_1", "foot_*", "limb", (4.5, 0, 1), (5.5, 2, 6)),
    *mirror("foot_*_toe_2", "foot_*", "limb", (7, 0, 0), (8, 2, 3)),
    *mirror("foot_*_toe_3", "foot_*", "limb", (9.5, 0, 1), (10.5, 2, 6)),
    *mirror("foot_*_claw_1", "foot_*", "claw", (4.5, 0, 0), (5.5, 1, 1)),
    *mirror("foot_*_claw_2", "foot_*", "claw", (7, 0, -1), (8, 1, 0)),
    *mirror("foot_*_claw_3", "foot_*", "claw", (9.5, 0, 0), (10.5, 1, 1)),
    *mirror("foot_*_spur", "foot_*", "claw", (7, 0, 9), (8, 1, 11)),
    # Wings, folded along the flanks just outside the legs. Each segment is
    # a scaled bone along the leading edge with a 1 px membrane below it,
    # centred on the shoulder's pivot so they line up in flight. The
    # membrane's trailing edge steps up toward the tip (the scallops between
    # the fingers), and a claw sits on the wrist.
    *mirror("wing_*_bone", "wing_*", "wing_bone", (9.5, 25, -11), (11.5, 27, 2)),
    *mirror("wing_*_membrane", "wing_*", "membrane", (10, 14, -11), (11, 25, 2)),
    *mirror("wing_*_mid_bone", "wing_mid_*", "wing_bone", (9.5, 25, 2), (11.5, 27, 13)),
    *mirror("wing_*_mid_membrane", "wing_mid_*", "membrane", (10, 15, 2), (11, 25, 13)),
    *mirror("wing_*_thumb", "wing_mid_*", "claw", (10, 27, 1), (11, 29, 3)),
    *mirror("wing_*_tip_bone", "wing_tip_*", "wing_bone", (10, 25, 13), (11, 27, 30)),
    *mirror("wing_*_tip_membrane_1", "wing_tip_*", "membrane", (10, 17, 13), (11, 25, 18)),
    *mirror("wing_*_tip_membrane_2", "wing_tip_*", "membrane", (10, 19, 18), (11, 25, 23)),
    *mirror("wing_*_tip_membrane_3", "wing_tip_*", "membrane", (10, 22, 23), (11, 25, 27)),
]

# Faces an animation opens up, kept although covered at rest: the inside of
# each wing bone (its top in flight) and both sides of the mouth.
KEEP = {"wing_right_bone": ("west",), "wing_left_bone": ("east",),
        "snout": ("down",), "nose": ("down",), "jaw": ("up",), "jaw_hinge": ("up",),
        **{f"{b}_{s}": ("up",) for b in ("arm", "thigh") for s in ("right", "left")},
        **{f"{b}_{s}": ("up",) for b in ("forearm", "shin") for s in ("right", "left")},
        "neck_base": ("up",), "neck_mid": ("up",), "neck_upper": ("up",), "tail_root": ("north",),
        "tail_mid": ("north",), "tail_end": ("north",)}
for _e in ELEMENTS:
    _e["keep"] = KEEP.get(_e["name"], ())

# Bones: parent, pivot (px, the model's frame), rest rotation (degrees).
BONES = {
    "dragon": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("dragon", HIP, (0, 0, 0)),
    "neck_base": ("body", NECK, (NECK_REST["neck_base"], 0, 0)),
    "neck_mid": ("neck_base", (0, 33, -15), (NECK_REST["neck_mid"], 0, 0)),
    "neck_upper": ("neck_mid", (0, 38, -15), (NECK_REST["neck_upper"], 0, 0)),
    "head": ("neck_upper", (0, 43, -15), (-TILT, 0, 0)),
    "jaw_upper": ("head", up((0, 40, -28)), (0, 0, 0)),
    "jaw": ("head", up((0, 38, -26)), (0, 0, 0)),
    "horn_right": ("head", up((3, 44, -22)), (0, 0, 0)),
    "horn_left": ("head", up((-3, 44, -22)), (0, 0, 0)),
    "wing_right": ("body", (10.5, 26, -10), (-15, 0, 0)),
    "wing_mid_right": ("wing_right", (10.5, 26, 2), (0, 0, 0)),
    "wing_tip_right": ("wing_mid_right", (10.5, 26, 13), (0, 0, 0)),
    "wing_left": ("body", (-10.5, 26, -10), (-15, 0, 0)),
    "wing_mid_left": ("wing_left", (-10.5, 26, 2), (0, 0, 0)),
    "wing_tip_left": ("wing_mid_left", (-10.5, 26, 13), (0, 0, 0)),
    "tail": ("body", (0, 21, 14), (18, 0, 0)),
    "tail_mid": ("tail", (0, 21, 24), (-8, 0, 0)),
    "tail_end": ("tail_mid", (0, 21, 37), (-8, 0, 0)),
    "arm_right": ("body", (7.5, 10, -12), (0, 0, 0)),
    "forearm_right": ("arm_right", (7.5, 6.5, -12), (0, 0, 0)),
    "hand_right": ("forearm_right", (7.5, 3, -12), (0, 0, 0)),
    "arm_left": ("body", (-7.5, 10, -12), (0, 0, 0)),
    "forearm_left": ("arm_left", (-7.5, 6.5, -12), (0, 0, 0)),
    "hand_left": ("forearm_left", (-7.5, 3, -12), (0, 0, 0)),
    "thigh_right": ("body", (7.5, 14, 6), (0, 0, 0)),
    "leg_right": ("thigh_right", (7.5, 8, 6), (0, 0, 0)),
    "foot_right": ("leg_right", (7.5, 3, 6), (0, 0, 0)),
    "thigh_left": ("body", (-7.5, 14, 6), (0, 0, 0)),
    "leg_left": ("thigh_left", (-7.5, 8, 6), (0, 0, 0)),
    "foot_left": ("leg_left", (-7.5, 3, 6), (0, 0, 0)),
}

# For check_clipping.py: where skin may fold at a joint (child: [(other bone,
# radius px, deepest fold px)]). Elbows, knees, wrists and ankles fold
# within their own width; the shoulder, hip and tail roots press at most
# 2 px into the body's scales in the biggest strides and landings.
JOINTS = {
    "neck_base": [("body", 8)], "neck_mid": [("neck_base", 7)], "neck_upper": [("neck_mid", 7)],
    "head": [("neck_upper", 8)], "jaw": [("head", 5), ("jaw_upper", 5), ("neck_mid", 6, 0.5)],
    "jaw_upper": [("head", 4)], "horn_right": [("neck_upper", 8, 0.5)], "horn_left": [("neck_upper", 8, 0.5)],
    "tail": [("body", 6, 2.0)], "tail_mid": [("tail", 5)], "tail_end": [("tail_mid", 5)],
    **{f"wing_{s}": [("body", 12, 0.5)] for s in ("right", "left")},
    **{f"wing_mid_{s}": [(f"wing_{s}", 12, 0.5)] for s in ("right", "left")},
    **{f"wing_tip_{s}": [(f"wing_mid_{s}", 12, 0.5)] for s in ("right", "left")},
    **{f"arm_{s}": [("body", 6, 2.0)] for s in ("right", "left")},
    **{f"thigh_{s}": [("body", 7, 2.0)] for s in ("right", "left")},
    **{f"forearm_{s}": [(f"arm_{s}", 5), ("body", 7, 1.0)] for s in ("right", "left")},
    **{f"hand_{s}": [(f"forearm_{s}", 4), (f"arm_{s}", 5, 1.0)] for s in ("right", "left")},
    **{f"leg_{s}": [(f"thigh_{s}", 5)] for s in ("right", "left")},
    **{f"foot_{s}": [(f"leg_{s}", 4.5), (f"thigh_{s}", 5, 1.5)] for s in ("right", "left")},
}


# ---------------------------------------------------------------- painting

def paint_body(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return BELLY[clamp(plates(fi(z), 2), 1, 3)]
    a, b = side_coords(t)
    if t.f == "north" and abs(x) < 5:
        return BELLY[clamp(plates(fi(y), v), 1, 4)]     # the throat and chest plates
    if t.f in ("east", "west") and y < 13:
        return BELLY[clamp(v, 1, 3)]                   # where the belly plates wrap the side
    v = scales(a, b, v)
    if t.f == "up":
        return DARK[clamp(v + 1, 1, 4)]
    if y >= 22:
        return DARK[clamp(v + 1, 1, 4)]                # the darker back shading into the flank
    return GREEN[clamp(v, 0, 4)]


def paint_back(t):
    """Armour plates down the back: 4 px wide, 3 px long, a lit ridge on
    each and a dark seam between them."""
    x, y, z = t.p
    xi, zi = fi(x), fi(z)
    v = t.shade
    if t.f == "up":
        seam = zi % 3 == 0
        ridge = xi in (-1, 0)
        if seam:
            return DARK[clamp(v - 1, 1, 3)]
        return DARK[clamp(v + (1 if ridge else 0), 2, 4)]
    if t.f == "down":
        return GREEN[1]
    a, b = side_coords(t)
    return DARK[clamp(scales(a, b, v) + 1, 1, 4)]


def paint_spine(t):
    """Spines: dark horn, a pale point on the top edge."""
    v = t.shade
    if t.f == "up":
        return HORN[2] if t.edge else HORN[1]
    if fi(t.p[1]) == fi(t.e["hi"][1] - 0.5):
        return HORN[clamp(v - 1, 1, 2)]
    return HORN[clamp(v - 2, 0, 1)]


def paint_neck(t):
    """Neck scales in rows around the neck, belly plates down the throat
    (the front, -z, which faces forward and down)."""
    x, y, z = t.p
    v = t.shade
    if t.f == "north":
        return BELLY[clamp(plates(fi(y), v), 1, 4)]
    if t.f == "down":
        return BELLY[1]
    a, b = side_coords(t)
    if t.f == "south":
        return DARK[clamp(scales(fi(x), fi(y), v) + 1, 1, 4)]
    return GREEN[clamp(scales(a, b, v), 0, 4)]


EYE_Z = (-27, -26, -25)


def paint_skull(t):
    """Skull: rows of small scales, a dark furrow down the brow, and the
    amber eye with a slit pupil under the brow's shadow."""
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    name = t.e["name"]
    if name.startswith("brow"):
        if t.f == "down":
            return DARK[0]
        return DARK[clamp(v + 1, 1, 4)]
    if t.f in ("east", "west") and yi in (39, 40) and zi in EYE_Z:
        if zi == -26:
            return PUPIL                               # slit pupil
        return IRIS[3] if (yi == 40 and zi == -27) else IRIS[2] if yi == 40 else IRIS[1]
    if t.f in ("east", "west") and yi == 38 and zi < -21:
        return BELLY[clamp(v, 1, 3)]                   # pale lip scales over the jaw line
    if t.f == "up":
        if xi in (-1, 0):
            return DARK[clamp(v - 1, 1, 3)]            # the furrow between the horns
        return DARK[clamp(scales(xi, -zi, v) + 1, 1, 4)]
    if t.f == "down":
        if zi < -26:
            return MOUTH[0]                            # over the jaw: the back of the mouth
        return BELLY[clamp(plates(-zi, 2), 1, 3)]      # behind it: the throat
    a, b = side_coords(t)
    return GREEN[clamp(scales(a, b, v), 0, 4)]


def paint_snout(t):
    """Snout: small scales, nostrils, a row of teeth along the lip."""
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f == "down":
        return MOUTH[1]                                # the roof of the mouth
    if t.f in ("east", "west") and yi == 39:
        return TEETH[2] if zi % 2 == 0 else MOUTH[0]   # upper teeth along the lip
    if t.e["name"] == "nose":
        if t.f == "north" and yi == 40 and xi in (-2, 1):
            return PUPIL                               # nostrils
        if t.f == "up" and zi == -37 and xi in (-2, 1):
            return PUPIL
    if t.f == "up":
        return DARK[clamp(scales(xi, -zi, v, 2) + 1, 1, 4)]
    a, b = side_coords(t)
    return GREEN[clamp(scales(a, b, v, 2), 0, 4)]


def paint_jaw(t):
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f == "up":
        if abs(x) > 1.5 and zi % 2 == 0:
            return TEETH[1]                            # lower teeth, seen when it opens
        return MOUTH[1] if abs(x) <= 1.5 else MOUTH[2]
    if t.f in ("east", "west") and yi == 38 and t.e["name"] == "jaw":
        return TEETH[1] if zi % 2 else MOUTH[0]
    if t.f == "down" or t.f == "north":
        return BELLY[clamp(plates(-zi, v), 1, 3)]
    a, b = side_coords(t)
    return GREEN[clamp(scales(a, b, v, 2), 0, 4)]


def paint_horn(t):
    """Horn: ridged rings every 2 px, darker at the root, pale at the tip."""
    x, y, z = t.p
    zi = fi(z)
    v = t.shade
    name = t.e["name"]
    if "tip" in name:
        v += 1
    if "root" in name:
        v -= 1
    if t.f != "south" and zi % 2 == 0:
        v -= 1
    return HORN[clamp(v, 0, 4)]


def paint_tooth(t):
    return TEETH[clamp(t.shade, 0, 2)]


def paint_tail(t):
    x, y, z = t.p
    v = t.shade
    a, b = side_coords(t)
    if t.f == "down":
        return BELLY[clamp(plates(fi(z), 2), 1, 3)]
    if t.f == "up":
        return DARK[clamp(scales(fi(x), fi(-z), v) + 1, 1, 4)]
    if t.f in ("east", "west") and abs(y - 21) <= 1:
        return DARK[clamp(scales(a, b, v), 1, 3)]       # a dark stripe along each side
    return GREEN[clamp(scales(a, b, v), 0, 4)]


def paint_spade(t):
    """The spade: dark green with a pale horny rim."""
    x, y, z = t.p
    v = t.shade
    rim = abs(x) >= t.e["hi"][0] - 1 or fi(z) == fi(t.e["hi"][2] - 0.5)
    if rim:
        return HORN[clamp(v, 1, 3)]
    return DARK[clamp(v + 1, 1, 4)]


def paint_limb(t):
    """Limbs: scale rows, belly-tan on the inside and the soles, knuckle
    scutes on the tops of the fingers and toes."""
    x, y, z = t.p
    v = t.shade
    name = t.e["name"]
    if t.f == "down":
        return BELLY[1]
    inner = t.f in ("east", "west") and ((t.f == "west") == (x > 0))
    a, b = side_coords(t)
    if "finger" in name or "toe" in name or "palm" in name or "heel" in name:
        if t.f == "up":
            return GREEN[clamp(v + (1 if fi(z) % 2 == 0 else 0), 1, 4)]   # knuckle scutes
        return GREEN[clamp(v - (1 if fi(y) == 0 else 0), 0, 3)]
    if inner:
        return BELLY[clamp(scales(a, b, v - 1), 1, 3)]
    return GREEN[clamp(scales(a, b, v), 0, 4)]


def paint_claw(t):
    """Claws: dark horn, pale at the point."""
    v = t.shade
    name = t.e["name"]
    point = (t.f == "north" and "spur" not in name) or (t.f == "south" and "spur" in name) \
        or (t.f == "up" and "thumb" in name)
    if point:
        return CLAW[3]
    return CLAW[clamp(v - 1, 0, 2)]


def paint_wing_bone(t):
    """The wing's leading-edge bones: scaled, a pale ridge along the top
    (its front in flight)."""
    x, y, z = t.p
    v = t.shade
    if t.f == "up":
        return GREEN[clamp(v + (1 if fi(z) % 3 else 0), 2, 4)]
    if t.f in ("east", "west"):
        outer = (t.f == "east") == (x > 0)
        if not outer:                                  # the top in flight
            return DARK[clamp(scales(fi(z), fi(y), 3), 1, 4)]
        return GREEN[clamp(scales(fi(-z), fi(y), v), 0, 4)]
    return GREEN[clamp(v, 0, 3)]


# The fingers inside the membrane: lines from the leading edge (top) back
# and down toward the trailing edge, one per segment and two in the hand.
VEINS = [((-11, 25), (-2, 14)), ((2, 25), (9, 15)), ((13, 25), (17, 17)), ((19, 25), (24, 19))]


def vein(y, z):
    for (z0, y0), (z1, y1) in VEINS:
        if y1 <= y < y0:
            zz = z0 + (z1 - z0) * (y0 - y - 0.5) / (y0 - y1)
            if abs(z + 0.5 - zz) < 0.75:
                return True
    return False


def paint_membrane(t):
    """Leathery membrane: olive, the finger bones showing through as dark
    veins, soft creases running along the span, the trailing edge darker
    and worn."""
    x, y, z = t.p
    yi, zi = fi(y), fi(z)
    if t.f in ("east", "west"):
        outer = (t.f == "east") == (x > 0)
        v = 2 + (t.light - 1 if outer else 1)          # the inside is the top in flight
        if vein(y, z):
            return MEMBRANE[clamp(v - 2, 0, 2)]
        if yi == fi(t.e["lo"][1]):
            v -= 1                                     # the trailing edge
            if (zi * 7) % 5 == 0:
                v -= 1                                 # worn notches
        elif (yi - fi(t.e["lo"][1])) % 4 == 2:
            v -= 1                                     # creases along the span
        return MEMBRANE[clamp(v, 0, 4)]
    if t.f == "down":
        return MEMBRANE[0]
    return MEMBRANE[clamp(t.shade, 1, 3)]


PAINTERS = {"body": paint_body, "back": paint_back, "spine": paint_spine, "neck": paint_neck,
            "skull": paint_skull, "snout": paint_snout, "jaw": paint_jaw, "horn": paint_horn,
            "tooth": paint_tooth, "spike": paint_spine, "tail": paint_tail, "spade": paint_spade,
            "limb": paint_limb, "claw": paint_claw, "wing_bone": paint_wing_bone,
            "membrane": paint_membrane}


# ---------------------------------------------------------------- animation
#
# Written once for both dragons in bbdragon.py.

MOVES = moves(BONES, TILT)
ANIMATIONS = build(MOVES, ("idle", "look", "walk", "run", "turn_left", "turn_right", "roar", "attack",
                           "claw", "hit", "takeoff", "fly", "hover", "land"))


DRAGON = RigCreature("dragon", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    DRAGON.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                 preview_scale=5.5, tile=(420, 360), anchor=0.86)
