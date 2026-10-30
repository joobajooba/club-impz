"""Build the Blockbench pale dragon: a lean, ancient, pale sage dragon with
broad wings, 1.53 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. The 5 ft the
  user asked for is the top of the horns standing on all fours: 49 px
  (1.53 m, the nearest whole pixel to 1.524 m).
- Box sizes in whole texture pixels; odd widths for the centred parts
  (chest, keel, skull, neck base, tail root) so they have a centre column.
- Per-face UV, one texture, hidden faces removed except the ones an
  animation opens up (inside the mouth, the wing bones' inner faces, the
  caps of the joints).
- Lit from the top, slightly front-left; hue-shifted ramps (the sage greens'
  shadows lean blue-grey, their highlights straw), edge highlights where the
  surface turns over, painted shadow where parts meet. Scales are calm
  offset rows, armour plates run down the back, banded ivory plates run
  under the belly, chest and jaw; wear is a few hand-placed scars and worn
  plate edges, never random noise.
- There is no dragon icon, so the colours follow ART-DIRECTION section 5 and
  the user's brief: a pale, faded sage green with ivory and muted tan, kept
  below the accent; the amber eyes are the one saturated colour (STUDY 3.1).

The shape, against the green dragon (build_dragon_bbmodel.py):
- Leaner and taller in the leg, with a deeper keel of ivory chest plates, a
  longer neck (25 px against 20) and a longer tail ending in a bony fin.
- Much bigger wings, the defining feature: 3.9 m across (against 3.2 m),
  with broad membranes (a 17 px chord at the root, 53 cm) that drape down
  the flanks like a cloak when folded, tips raised 18 degrees.
- A long, intelligent head: almond eyes under a heavy brow, a long snout,
  cheek frills, and long ridged horns swept straight back.

The skeleton is the green dragon's (the bone names and joint layout in
bbdragon.py), so both share every animation; this one also glides.

Usage: python build_pale_dragon_bbmodel.py [out_dir]   (writes
pale_dragon.bbmodel, pale_dragon.png, pale_dragon_preview.png and
pale_dragon_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py pale_dragon.bbmodel --spec build_pale_dragon_bbmodel.py
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import clamp, el, fi, hexrgb, mirror, ramp, turn_about  # noqa: E402
from bbdragon import ANIMATION_NAMES, build, moves, plates, scales, side_coords  # noqa: E402
from bbrig import RigCreature  # noqa: E402

# Ramps, darkest first. Sage greens lean blue-grey in the shadows and straw
# in the light; ivory and muted tan for the plates, jaw and membranes. A
# step deeper than they look in Blockbench: the game's sun washed the first
# pass out to mint and white (the cow, chicken and eagle needed the same).
SAGE = ramp("#2e3a32", "#485a45", "#627659", "#7d9270", "#9caf88")       # flank and limb scales
SAGE_DARK = ramp("#252e28", "#3c4738", "#525f49", "#6a785c", "#879574")  # back plates, stripes
IVORY = ramp("#5c5340", "#7e745a", "#9f9575", "#bbb08f", "#d4c9a7")      # belly, chest, jaw plates
MEMBRANE = ramp("#4a4336", "#665d4a", "#81765c", "#9a8d6f", "#b3a684")   # wing leather
HORN = ramp("#413a2c", "#615843", "#857a5e", "#a99d7d", "#c9bf9d")
CLAW = ramp("#22212a", "#3a3842", "#5b5862", "#8b8790")
TEETH = ramp("#a39b80", "#cec6a8", "#ece5cb")
MOUTH = ramp("#391b22", "#622f38", "#8a484a")
IRIS = ramp("#a4580f", "#dd881b", "#f7c13a", "#ffef9e")                  # the accent
PUPIL = hexrgb("#1b1210")

TILT = math.degrees(math.atan2(3, 4))   # the neck's bend, 36.87 degrees (cos 0.8, sin 0.6)
HIP = (0, 15, 6)                        # the body's pivot, on the line through both hip joints
NECK = (0, 22, -14)                     # the neck's base, modelled straight up from here
NECK_PIVOTS = {"neck_base": NECK, "neck_mid": (0, 32, -14), "neck_upper": (0, 42, -14),
               "head": (0, 47, -14)}
NECK_REST = {"neck_base": -TILT, "neck_mid": TILT, "neck_upper": TILT, "head": -TILT}
WING_REST = -18                         # folded wing tips raised 18 degrees


def _head_offset():
    """Where the head's pivot lands at rest minus where it is modelled. The
    neck's bends add up to the head's turn back, so the head only moves."""
    M = np.eye(4)
    for b in ("neck_base", "neck_mid", "neck_upper", "head"):
        M = M @ turn_about((NECK_REST[b], 0, 0), NECK_PIVOTS[b])
    p = NECK_PIVOTS["head"]
    q = M @ np.array([*p, 1.0])
    d = [round(q[k] - p[k], 6) for k in range(3)]
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
    # Body: a deep chest with a keel of ivory plates, a lean waist and hips,
    # and broad wing shoulders running the length of the wing roots; the
    # underside steps up toward the tail. Armour plates and spines down the
    # back.
    el("chest", "body", "body", (-6.5, 13, -18), (6.5, 26, -6)),
    el("keel", "body", "keel", (-3.5, 12, -19), (3.5, 24, -18)),
    el("waist", "body", "body", (-5.5, 16, -6), (5.5, 25, 8)),
    el("hips", "body", "body", (-6.5, 15, 3), (6.5, 26, 12)),
    el("shoulders", "body", "back", (-9, 22, -15), (9, 27, 8)),
    el("mantle", "body", "back", (-4.5, 26, 8), (4.5, 27, 12)),
    el("rump", "body", "body", (-4.5, 17, 12), (4.5, 25, 14)),
    el("spine_1", "body", "spine", (-0.5, 27, -6), (0.5, 29, -3)),
    el("spine_2", "body", "spine", (-0.5, 27, 0), (0.5, 29, 3)),
    el("spine_3", "body", "spine", (-0.5, 27, 6), (0.5, 29, 9)),
    # The shoulder and haunch muscles sit on the flanks; the legs hang from
    # joints at the underside, so a swinging leg never sweeps through the
    # body. Half a pixel in from the legs' sides, so no face shares a plane.
    *mirror("foreshoulder_*", "body", "body", (6.5, 13, -13.5), (8.5, 21, -10.5)),
    *mirror("haunch_*", "body", "body", (6.5, 15, 3), (8.5, 22, 9)),
    # Neck, modelled straight up from each pivot (the rest bends make the S),
    # long and muscled, tapering 9 - 7 - 6, each segment reaching into the next.
    el("neck_base", "neck_base", "neck", (-4.5, 20, -18), (4.5, 33, -10)),
    el("neck_base_spine", "neck_base", "spine", (-0.5, 25, -10), (0.5, 28, -8)),
    el("neck_mid", "neck_mid", "neck", (-3.5, 31, -17.5), (3.5, 43, -10.5)),
    el("neck_mid_spine", "neck_mid", "spine", (-0.5, 35, -10.5), (0.5, 38, -8.5)),
    el("neck_upper", "neck_upper", "neck", (-3, 41, -17), (3, 48, -11)),
    el("neck_upper_spine", "neck_upper", "spine", (-0.5, 43, -11), (0.5, 45, -9)),
    # Head, in world pixels (level): a long skull, a heavy brow over each
    # almond eye, swept cheek frills; the long upper jaw with a nose ridge
    # and an overbite of fangs; the ivory lower jaw hinged under the skull.
    head_el("skull", "head", "skull", (-3.5, 42, -27), (3.5, 47, -18)),
    *head_mirror("brow_*", "head", "skull", (3.5, 45, -27), (4.5, 47, -22)),
    *head_mirror("frill_*", "head", "spike", (3.5, 42, -21), (4.5, 44, -15)),
    head_el("snout", "jaw_upper", "snout", (-2.5, 43, -37), (2.5, 46, -27)),
    head_el("nose", "jaw_upper", "snout", (-1.5, 43, -39), (1.5, 45, -37)),
    head_el("nose_ridge", "jaw_upper", "horn", (-0.5, 46, -35), (0.5, 47, -31)),
    *head_mirror("fang_*", "jaw_upper", "tooth", (2, 41, -36), (3, 43, -35)),
    head_el("jaw", "jaw", "jaw", (-2, 40, -38), (2, 43, -27)),
    head_el("jaw_hinge", "jaw", "jaw", (-3, 40, -27), (3, 42, -25)),
    # Horns: long and ridged, swept straight back from the brow and rising
    # to the dragon's full height.
    *head_mirror("horn_*_root", "horn_*", "horn", (1, 46, -25), (3, 48, -19)),
    *head_mirror("horn_*_mid", "horn_*", "horn", (1.5, 47, -19), (3.5, 49, -12)),
    *head_mirror("horn_*_tip", "horn_*", "horn", (2, 48, -12), (3, 49, -6)),
    # Tail: three long tapering segments, modelled straight back from each
    # pivot and drooping at rest; spines along the top, a bony fin at the end.
    el("tail_root", "tail", "tail", (-3.5, 17.5, 14), (3.5, 24.5, 21)),
    el("tail_root_2", "tail", "tail", (-3, 18, 21), (3, 24, 28)),
    el("tail_spine_1", "tail", "spine", (-0.5, 24.5, 17), (0.5, 26.5, 20)),
    el("tail_mid", "tail_mid", "tail", (-2.5, 18.5, 27), (2.5, 23.5, 35)),
    el("tail_mid_2", "tail_mid", "tail", (-2, 19, 35), (2, 23, 43)),
    el("tail_spine_2", "tail_mid", "spine", (-0.5, 23.5, 31), (0.5, 25.5, 34)),
    el("tail_end", "tail_end", "tail", (-1.5, 19.5, 42), (1.5, 22.5, 51)),
    el("tail_fin", "tail_end", "fin", (-0.5, 22.5, 44), (0.5, 25.5, 51)),
    el("tail_tip", "tail_end", "fin", (-0.5, 20.5, 51), (0.5, 21.5, 54)),
    # Forelegs: an upper arm, a heavy forearm, a large hand with three long
    # fingers and big hooked claws.
    *mirror("arm_*", "arm_*", "limb", (4, 7, -14), (9, 14, -10)),
    *mirror("forearm_*", "forearm_*", "limb", (5, 3, -14.5), (8, 9, -9.5)),
    *mirror("hand_*_palm", "hand_*", "limb", (4.5, 0, -15), (8.5, 3, -9)),
    *mirror("hand_*_finger_1", "hand_*", "limb", (3.5, 0, -18), (4.5, 2, -12)),
    *mirror("hand_*_finger_2", "hand_*", "limb", (6, 0, -19), (7, 2, -15)),
    *mirror("hand_*_finger_3", "hand_*", "limb", (8.5, 0, -18), (9.5, 2, -12)),
    *mirror("hand_*_claw_1", "hand_*", "claw", (3.5, 0, -20), (4.5, 1, -18)),
    *mirror("hand_*_claw_2", "hand_*", "claw", (6, 0, -21), (7, 1, -19)),
    *mirror("hand_*_claw_3", "hand_*", "claw", (8.5, 0, -20), (9.5, 1, -18)),
    # Hind legs: a powerful thigh, a shin, a foot with three toes, claws and
    # a back spur.
    *mirror("thigh_*", "thigh_*", "limb", (4, 7, 2.5), (9, 16, 9.5)),
    *mirror("shin_*", "leg_*", "limb", (5, 3, 4), (8, 9, 8)),
    *mirror("foot_*_heel", "foot_*", "limb", (4.5, 0, 3), (8.5, 3, 9)),
    *mirror("foot_*_toe_1", "foot_*", "limb", (3.5, 0, 0), (4.5, 2, 6)),
    *mirror("foot_*_toe_2", "foot_*", "limb", (6, 0, -1), (7, 2, 3)),
    *mirror("foot_*_toe_3", "foot_*", "limb", (8.5, 0, 0), (9.5, 2, 6)),
    *mirror("foot_*_claw_1", "foot_*", "claw", (3.5, 0, -1), (4.5, 1, 0)),
    *mirror("foot_*_claw_2", "foot_*", "claw", (6, 0, -2), (7, 1, -1)),
    *mirror("foot_*_claw_3", "foot_*", "claw", (8.5, 0, -1), (9.5, 1, 0)),
    *mirror("foot_*_spur", "foot_*", "claw", (6, 0, 9), (7, 1, 11)),
    # Wings, folded along the flanks just outside the legs: broad membranes
    # below a scaled leading-edge bone, centred on the shoulder's pivot so
    # they line up in flight. The trailing edge steps up toward the tip (the
    # scallops between the fingers); a claw sits on the wrist.
    *mirror("wing_*_bone", "wing_*", "wing_bone", (9, 24, -10), (11, 26, 6)),
    *mirror("wing_*_membrane", "wing_*", "membrane", (9.5, 7, -10), (10.5, 24, 6)),
    *mirror("wing_*_mid_bone", "wing_mid_*", "wing_bone", (9, 24, 6), (11, 26, 22)),
    *mirror("wing_*_mid_membrane", "wing_mid_*", "membrane", (9.5, 8, 6), (10.5, 24, 22)),
    *mirror("wing_*_thumb", "wing_mid_*", "claw", (9.5, 26, 5), (10.5, 28, 7)),
    *mirror("wing_*_tip_bone", "wing_tip_*", "wing_bone", (9.5, 24, 22), (10.5, 26, 43)),
    *mirror("wing_*_tip_membrane_1", "wing_tip_*", "membrane", (9.5, 10, 22), (10.5, 24, 28)),
    *mirror("wing_*_tip_membrane_2", "wing_tip_*", "membrane", (9.5, 13, 28), (10.5, 24, 33)),
    *mirror("wing_*_tip_membrane_3", "wing_tip_*", "membrane", (9.5, 16, 33), (10.5, 24, 37)),
    *mirror("wing_*_tip_membrane_4", "wing_tip_*", "membrane", (9.5, 19, 37), (10.5, 24, 40)),
]

# Faces an animation opens up, kept although covered at rest: the inside of
# each wing bone (its top in flight), both sides of the mouth and the caps
# of the joints.
KEEP = {"wing_right_bone": ("west",), "wing_left_bone": ("east",), "keel": ("up",),
        **{f"{b}_{s}": ("down",) for b in ("foreshoulder", "haunch") for s in ("right", "left")},
        "snout": ("down",), "nose": ("down",), "jaw": ("up",), "jaw_hinge": ("up",),
        **{f"{b}_{s}": ("up",) for b in ("arm", "thigh", "forearm", "shin") for s in ("right", "left")},
        "neck_base": ("up",), "neck_mid": ("up",), "neck_upper": ("up",), "tail_root": ("north",),
        "tail_mid": ("north",), "tail_end": ("north",)}
for _e in ELEMENTS:
    _e["keep"] = KEEP.get(_e["name"], ())

# Bones: parent, pivot (px, the model's frame), rest rotation (degrees).
BONES = {
    "dragon": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("dragon", HIP, (0, 0, 0)),
    "neck_base": ("body", NECK_PIVOTS["neck_base"], (NECK_REST["neck_base"], 0, 0)),
    "neck_mid": ("neck_base", NECK_PIVOTS["neck_mid"], (NECK_REST["neck_mid"], 0, 0)),
    "neck_upper": ("neck_mid", NECK_PIVOTS["neck_upper"], (NECK_REST["neck_upper"], 0, 0)),
    "head": ("neck_upper", NECK_PIVOTS["head"], (NECK_REST["head"], 0, 0)),
    "jaw_upper": ("head", up((0, 44, -27)), (0, 0, 0)),
    "jaw": ("head", up((0, 42, -25)), (0, 0, 0)),
    "horn_right": ("head", up((2, 47, -22)), (0, 0, 0)),
    "horn_left": ("head", up((-2, 47, -22)), (0, 0, 0)),
    "wing_right": ("body", (10, 25, -9), (WING_REST, 0, 0)),
    "wing_mid_right": ("wing_right", (10, 25, 6), (0, 0, 0)),
    "wing_tip_right": ("wing_mid_right", (10, 25, 22), (0, 0, 0)),
    "wing_left": ("body", (-10, 25, -9), (WING_REST, 0, 0)),
    "wing_mid_left": ("wing_left", (-10, 25, 6), (0, 0, 0)),
    "wing_tip_left": ("wing_mid_left", (-10, 25, 22), (0, 0, 0)),
    "tail": ("body", (0, 21, 14), (18, 0, 0)),
    "tail_mid": ("tail", (0, 21, 27), (-6, 0, 0)),
    "tail_end": ("tail_mid", (0, 21, 42), (-6, 0, 0)),
    "arm_right": ("body", (6.5, 13, -12), (0, 0, 0)),
    "forearm_right": ("arm_right", (6.5, 8, -12), (0, 0, 0)),
    "hand_right": ("forearm_right", (6.5, 3, -12), (0, 0, 0)),
    "arm_left": ("body", (-6.5, 13, -12), (0, 0, 0)),
    "forearm_left": ("arm_left", (-6.5, 8, -12), (0, 0, 0)),
    "hand_left": ("forearm_left", (-6.5, 3, -12), (0, 0, 0)),
    "thigh_right": ("body", (6.5, 15, 6), (0, 0, 0)),
    "leg_right": ("thigh_right", (6.5, 8, 6), (0, 0, 0)),
    "foot_right": ("leg_right", (6.5, 3, 6), (0, 0, 0)),
    "thigh_left": ("body", (-6.5, 15, 6), (0, 0, 0)),
    "leg_left": ("thigh_left", (-6.5, 8, 6), (0, 0, 0)),
    "foot_left": ("leg_left", (-6.5, 3, 6), (0, 0, 0)),
}

# For check_clipping.py: where skin may fold at a joint (child: [(other bone,
# radius px, deepest fold px)]). Elbows, knees, wrists and ankles fold
# within their own width; the shoulder, hip and tail roots press at most
# 2 px into the body's scales in the biggest strides and landings; the wing
# joints at most 0.5 px, the wing root along its whole 17 px chord; the
# draped membrane brushes the haunch by at most 0.25 px in the claw's twist.
JOINTS = {
    "neck_base": [("body", 8)], "neck_mid": [("neck_base", 7)], "neck_upper": [("neck_mid", 7)],
    "head": [("neck_upper", 8)], "jaw": [("head", 5), ("jaw_upper", 5), ("neck_mid", 6, 0.5)],
    "jaw_upper": [("head", 4)], "horn_right": [("neck_upper", 8, 0.5)], "horn_left": [("neck_upper", 8, 0.5)],
    "tail": [("body", 6, 2.0)], "tail_mid": [("tail", 5)], "tail_end": [("tail_mid", 5)],
    **{f"wing_{s}": [("body", 18, 0.5), (f"thigh_{s}", 20, 0.25)] for s in ("right", "left")},
    **{f"wing_mid_{s}": [(f"wing_{s}", 18, 0.5)] for s in ("right", "left")},
    **{f"wing_tip_{s}": [(f"wing_mid_{s}", 16, 0.5)] for s in ("right", "left")},
    **{f"arm_{s}": [("body", 6, 2.0)] for s in ("right", "left")},
    **{f"thigh_{s}": [("body", 7, 2.0)] for s in ("right", "left")},
    **{f"forearm_{s}": [(f"arm_{s}", 5), ("body", 7, 1.0)] for s in ("right", "left")},
    **{f"hand_{s}": [(f"forearm_{s}", 4), (f"arm_{s}", 5, 1.0)] for s in ("right", "left")},
    **{f"leg_{s}": [(f"thigh_{s}", 5)] for s in ("right", "left")},
    **{f"foot_{s}": [(f"leg_{s}", 4.5), (f"thigh_{s}", 5, 1.5)] for s in ("right", "left")},
}


# ---------------------------------------------------------------- painting

# Hand-placed scars and worn plates: the "ancient" wear, a few clusters, not
# noise. (x or z, y) on the chosen faces.
SCARS = {"chest_east": {(-9, 22), (-8, 21), (-7, 20), (-6, 19)},
         "chest_west": {(-15, 18), (-14, 19), (-13, 20)},
         "waist_east": {(2, 20), (3, 19), (4, 18)},
         "hips_west": {(7, 23), (8, 22)}}


def scar(t):
    if t.f not in ("east", "west"):
        return False
    key = f"{t.e['name']}_{t.f}"
    return (fi(t.p[2]), fi(t.p[1])) in SCARS.get(key, ())


def paint_body(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return IVORY[clamp(plates(fi(z), 2), 1, 3)]
    if scar(t):
        return SAGE[clamp(v + 2, 3, 4)]                # pale healed scar lines
    a, b = side_coords(t)
    if t.f == "north" and abs(x) < 5:
        return IVORY[clamp(plates(fi(y), v), 1, 4)]    # the chest plates
    if t.f in ("east", "west") and y < 17:
        return IVORY[clamp(v, 1, 3)]                   # where the belly plates wrap the side
    v = scales(a, b, v)
    if t.f == "up" or y >= 22:
        return SAGE_DARK[clamp(v + 1, 1, 4)]           # the darker back shading into the flank
    return SAGE[clamp(v, 0, 4)]


def paint_keel(t):
    """The keel: big ivory chest plates, 2 px tall, worn paler at the edges."""
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return IVORY[1]
    v = plates(fi(y), v + 1)
    if t.f == "north" and abs(x) >= 3.5 and fi(y) % 4 == 1:
        v += 1                                         # worn plate corners
    return IVORY[clamp(v, 1, 4)]


def paint_back(t):
    """Armour plates down the back: 4 px wide, 3 px long, a lit ridge on
    each, a dark seam between them, and the odd chipped corner."""
    x, y, z = t.p
    xi, zi = fi(x), fi(z)
    v = t.shade
    if t.f == "up":
        if zi % 3 == 0:
            return SAGE_DARK[clamp(v - 1, 1, 3)]
        if xi in (-1, 0):
            return SAGE_DARK[clamp(v + 1, 2, 4)]
        if (xi, zi) in ((3, -8), (-4, -2), (5, 4), (-6, 7)):
            return SAGE[4]                             # chipped plate corners
        return SAGE_DARK[clamp(v, 2, 4)]
    if t.f == "down":
        return SAGE[1]
    a, b = side_coords(t)
    return SAGE_DARK[clamp(scales(a, b, v) + 1, 1, 4)]


def paint_spine(t):
    """Spines: weathered horn, a pale point on the top edge."""
    v = t.shade
    if t.f == "up":
        return HORN[3] if t.edge else HORN[2]
    if fi(t.p[1]) == fi(t.e["hi"][1] - 0.5):
        return HORN[clamp(v, 1, 3)]
    return HORN[clamp(v - 1, 0, 2)]


def paint_neck(t):
    """Neck scales in rows around the neck, ivory plates down the throat."""
    x, y, z = t.p
    v = t.shade
    if t.f == "north":
        return IVORY[clamp(plates(fi(y), v), 1, 4)]
    if t.f == "down":
        return IVORY[1]
    a, b = side_coords(t)
    if t.f == "south":
        return SAGE_DARK[clamp(scales(fi(x), fi(y), v) + 1, 1, 4)]
    return SAGE[clamp(scales(a, b, v), 0, 4)]


EYE = {(44, -26): "iris_lit", (44, -25): "pupil", (44, -24): "iris", (43, -26): "iris",
       (43, -25): "pupil", (43, -24): "iris_dark"}


def paint_skull(t):
    """Skull: small scales, a dark furrow between the horns, and an almond
    amber eye with a slit pupil under the brow's shadow."""
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.e["name"].startswith("brow"):
        if t.f == "down":
            return SAGE_DARK[0]
        return SAGE_DARK[clamp(v + 1, 1, 4)]
    if t.f in ("east", "west"):
        k = EYE.get((yi, zi))
        if k == "pupil":
            return PUPIL
        if k:
            return {"iris_lit": IRIS[3], "iris": IRIS[2], "iris_dark": IRIS[1]}[k]
        if yi == 42 and zi < -21:
            return IVORY[clamp(v, 1, 3)]               # pale lip scales over the jaw line
    if t.f == "up":
        if xi in (-1, 0):
            return SAGE_DARK[clamp(v - 1, 1, 3)]
        return SAGE_DARK[clamp(scales(xi, -zi, v) + 1, 1, 4)]
    if t.f == "down":
        if zi < -25:
            return MOUTH[0]                            # over the jaw: the back of the mouth
        return IVORY[clamp(plates(-zi, 2), 1, 3)]      # behind it: the throat
    a, b = side_coords(t)
    return SAGE[clamp(scales(a, b, v), 0, 4)]


def paint_snout(t):
    """Snout: small scales, nostrils, a row of teeth along the lip."""
    x, y, z = t.q
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f == "down":
        return MOUTH[1]                                # the roof of the mouth
    if t.f in ("east", "west") and yi == 43:
        return TEETH[2] if zi % 2 == 0 else MOUTH[0]   # upper teeth along the lip
    if t.e["name"] == "nose":
        if t.f == "north" and yi == 44 and xi in (-1, 0):
            return PUPIL                               # nostrils
        if t.f == "up" and zi == -38 and xi in (-1, 0):
            return PUPIL
    if t.f == "up":
        return SAGE_DARK[clamp(scales(xi, -zi, v, 2) + 1, 1, 4)]
    a, b = side_coords(t)
    return SAGE[clamp(scales(a, b, v, 2), 0, 4)]


def paint_jaw(t):
    """The lower jaw is ivory: banded plates, teeth along its edge, the mouth
    inside."""
    x, y, z = t.q
    yi, zi = fi(y), fi(z)
    v = t.shade
    if t.f == "up":
        if abs(x) > 1 and zi % 2 == 0:
            return TEETH[1]                            # lower teeth, seen when it opens
        return MOUTH[1] if abs(x) <= 1 else MOUTH[2]
    if t.f in ("east", "west") and yi == 42 and t.e["name"] == "jaw":
        return TEETH[1] if zi % 2 else MOUTH[0]
    return IVORY[clamp(plates(-zi if t.f in ("down", "north") else yi, v), 1, 4)]


def paint_horn(t):
    """Horn: ridged rings every 2 px, darker at the root, pale at the tip."""
    zi = fi(t.p[2])
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
        return IVORY[clamp(plates(fi(z), 2), 1, 3)]
    if t.f == "up":
        return SAGE_DARK[clamp(scales(fi(x), fi(-z), v) + 1, 1, 4)]
    if t.f in ("east", "west") and abs(y - 21) <= 1 and fi(z) % 6 < 3:
        return SAGE_DARK[clamp(scales(a, b, v), 1, 3)]  # faded bands along each side
    return SAGE[clamp(scales(a, b, v), 0, 4)]


def paint_fin(t):
    """The tail fin: weathered horn, ridged, pale at the edge."""
    v = t.shade
    if t.f == "up" or fi(t.p[2]) == fi(t.e["hi"][2] - 0.5):
        return HORN[clamp(v + 1, 2, 4)]
    return HORN[clamp(v - (1 if fi(t.p[2]) % 2 else 0), 1, 3)]


def paint_limb(t):
    """Limbs: scale rows, ivory on the inside and the soles, knuckle scutes
    on the tops of the fingers and toes."""
    x, y, z = t.p
    v = t.shade
    name = t.e["name"]
    if t.f == "down":
        return IVORY[1]
    inner = t.f in ("east", "west") and ((t.f == "west") == (x > 0))
    a, b = side_coords(t)
    if any(k in name for k in ("finger", "toe", "palm", "heel")):
        if t.f == "up":
            return SAGE[clamp(v + (1 if fi(z) % 2 == 0 else 0), 1, 4)]
        return SAGE[clamp(v - (1 if fi(y) == 0 else 0), 0, 3)]
    if inner:
        return IVORY[clamp(scales(a, b, v - 1), 1, 3)]
    return SAGE[clamp(scales(a, b, v), 0, 4)]


def paint_claw(t):
    """Claws: dark slate, pale at the point."""
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
        return SAGE[clamp(v + (1 if fi(z) % 3 else 0), 2, 4)]
    if t.f in ("east", "west"):
        outer = (t.f == "east") == (x > 0)
        if not outer:                                  # the top in flight
            return SAGE_DARK[clamp(scales(fi(z), fi(y), 3), 1, 4)]
        return SAGE[clamp(scales(fi(-z), fi(y), v), 0, 4)]
    return SAGE[clamp(v, 0, 3)]


# The fingers inside the membrane: lines from the leading edge (top) back
# and down toward the trailing edge, two in the arm, two in the mid, three
# fanning through the hand.
VEINS = [((-10, 24), (-1, 7)), ((0, 24), (5, 8)), ((6, 24), (13, 8)), ((14, 24), (21, 9)),
         ((22, 24), (27, 11)), ((28, 24), (32, 14)), ((33, 24), (36, 17))]
TEARS = {(30, 15), (31, 15), (18, 9), (17, 9)}   # small old tears near the trailing edge


def vein(y, z):
    for (z0, y0), (z1, y1) in VEINS:
        if y1 <= y < y0:
            zz = z0 + (z1 - z0) * (y0 - y - 0.5) / (y0 - y1)
            if abs(z + 0.5 - zz) < 0.75:
                return True
    return False


def paint_membrane(t):
    """Leathery membrane: muted tan, lighter where it is stretched under the
    leading bone and a step darker toward the trailing edge, the finger
    bones showing through as darker veins, a worn trailing edge and a couple
    of old tears."""
    x, y, z = t.p
    yi, zi = fi(y), fi(z)
    if t.f in ("east", "west"):
        outer = (t.f == "east") == (x > 0)
        v = 2 + (t.light - 1 if outer else 1)          # the inside is the top in flight
        if (zi, yi) in TEARS:
            return MEMBRANE[0]
        if vein(y, z):
            return MEMBRANE[clamp(v - 2, 0, 2)]
        lo, hi = t.e["lo"][1], t.e["hi"][1]
        if y > hi - (hi - lo) * 0.3:
            v += 1                                     # stretched taut under the bone
        elif y < lo + (hi - lo) * 0.3:
            v -= 1                                     # slacker toward the trailing edge
        if yi == fi(lo):
            v -= 1
            if (zi * 7) % 5 == 0:
                v -= 1                                 # worn notches
        return MEMBRANE[clamp(v, 0, 4)]
    if t.f == "down":
        return MEMBRANE[0]
    return MEMBRANE[clamp(t.shade, 1, 3)]


PAINTERS = {"body": paint_body, "keel": paint_keel, "back": paint_back, "spine": paint_spine,
            "neck": paint_neck, "skull": paint_skull, "snout": paint_snout, "jaw": paint_jaw,
            "horn": paint_horn, "tooth": paint_tooth, "spike": paint_spine, "tail": paint_tail,
            "fin": paint_fin, "limb": paint_limb, "claw": paint_claw,
            "wing_bone": paint_wing_bone, "membrane": paint_membrane}


# ---------------------------------------------------------------- animation
#
# Written once for both dragons in bbdragon.py.

MOVES = moves(BONES, TILT, HAND=(3, -12), FOOT=(3, 6), WING_UP=90 + WING_REST, FLY_HEIGHT=34,
              ROAR_TAIL_LIFT=22)
ANIMATIONS = build(MOVES, ANIMATION_NAMES)

PALE_DRAGON = RigCreature("pale_dragon", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    PALE_DRAGON.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                      preview_scale=4.8, tile=(460, 360), anchor=0.88)
