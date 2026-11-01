"""Build the Blockbench chicken: a plump, golden-yellow hen, 0.5 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m, so the
  0.5 m the user asked for is 16 px from the soles to the top of the comb.
- Box sizes in whole texture pixels. Odd widths for the centred parts (body,
  breast, head, comb, beak) so the face has a centre column.
- Per-face UV, one texture inside the small-creature budget, hidden faces
  removed.
- Lit from the top, slightly front-left; hue-shifted ramps (the yellow's
  shadows lean ochre and plum, its highlights cream), edge highlights where
  the surface turns over, painted shadow where parts meet. Feathers are
  painted as scallop rows that follow the form, not noise (STUDY 5.3).
- There is no chicken icon, so the colours follow ART-DIRECTION section 5:
  the plumage is a buttery yellow kept below the accent, and the comb and
  wattles, the one accent, are the most saturated colour on the model.
- At this size every feature is a pixel or two, so the detail is in the
  geometry that changes the silhouette (a three-point comb, wattles, a hooked
  beak, layered wing and tail feathers, splayed toes) and in clean painting.
- Bones use the shared creature names, pivots at the joints. The thighs are
  part of the body, the legs hinge at the knee, and the feet are
  their own bones so they stay flat on the ground through a stride. The jaw
  (lower beak) opens to cluck. Animations: idle, walk, run, attack, hit.

Usage: python build_chicken_bbmodel.py [out_dir]   (writes chicken.bbmodel,
chicken.png, chicken_preview.png and chicken_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py chicken.bbmodel --spec build_chicken_bbmodel.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import Creature, clamp, el, fi, hexrgb, mirror, ramp, rot, sway, track  # noqa: E402

# Ramps, darkest first. Shadows lean ochre then plum, highlights lean cream.
# A step deeper than it looks in Blockbench: the game's sun lifts yellows
# toward cream (the same blow-out the cow's white had in Godot).
PLUME = ramp("#7d4636", "#b8732e", "#d99e2f", "#ebbd3a", "#f6d86e")
FLIGHT = ramp("#673834", "#9c5a2a", "#c68730", "#dfab3a", "#efcb62")    # wing and tail quills
COMB = ramp("#5e1630", "#981f3b", "#d0303f", "#ee5848", "#ff8e72")      # the accent
BEAK = ramp("#7a3c1f", "#bd6229", "#e69033", "#f8bc58", "#ffdc96")
LEG = ramp("#723524", "#ad5728", "#d98034", "#f0a94f", "#fbd087")
CLAW = ramp("#5c4a4a", "#8f7d74", "#c2b3a3")
EYE_DARK = hexrgb("#1e1420")
EYE_GLINT = hexrgb("#fff6e8")
IRIS = hexrgb("#d6782b")


# ---------------------------------------------------------------- geometry

ELEMENTS = [
    # Body: a plump 11-wide barrel, a rounded back, a full breast and a
    # fluffy rump, with soft down between and behind the thighs.
    el("body", "body", "plume", (-5.5, 5, -5), (5.5, 11, 5)),
    el("body_top", "body", "plume", (-4.5, 11, -4), (4.5, 12, 4)),
    el("body_low", "body", "plume", (-4, 4, -4), (4, 5, 4)),
    el("breast", "body", "plume", (-4.5, 6, -6), (4.5, 10, -5)),
    el("rump", "body", "plume", (-4.5, 6, 5), (4.5, 11, 6)),
    el("belly_down", "body", "down", (-1.5, 3, -2), (1.5, 4, 2)),
    el("vent_down", "body", "down", (-3.5, 3, 3), (3.5, 4, 5)),
    # Tail: a fan of quills stepping up and back.
    el("tail_1", "tail", "tail", (-2.5, 8, 6), (2.5, 12, 8)),
    el("tail_2", "tail", "tail", (-2.5, 12, 7), (2.5, 14, 9)),
    el("tail_3", "tail", "tail", (-1.5, 14, 8), (1.5, 15, 10)),
    # Wings: folded slabs on the flanks, coverts, then the primaries
    # reaching back past the rump.
    *mirror("wing_*", "wing_*", "wing", (5.5, 6, -3), (6.5, 10, 3)),
    *mirror("wing_*_primaries", "wing_*", "wing", (5.5, 7, 3), (6.5, 10, 6)),
    *mirror("wing_*_tip", "wing_*", "wing", (5.5, 8, 6), (6.5, 10, 7)),
    # Head: a round head on the front of the body, a hooked beak, the jaw
    # (lower beak), a three-point comb and two wattles.
    el("head", "head", "head", (-3.5, 9, -9), (3.5, 14, -3)),
    el("beak", "head", "beak", (-1.5, 11, -11), (1.5, 12, -9)),
    el("beak_tip", "head", "beak", (-0.5, 10, -12), (0.5, 12, -11)),
    el("comb", "head", "comb", (-0.5, 14, -8), (0.5, 15, -3)),
    el("comb_1", "head", "comb", (-0.5, 15, -8), (0.5, 16, -7)),
    el("comb_2", "head", "comb", (-0.5, 15, -6), (0.5, 16, -5)),
    el("comb_3", "head", "comb", (-0.5, 15, -4), (0.5, 16, -3)),
    *mirror("wattle_*", "head", "wattle", (0.5, 7, -9), (1.5, 9, -8)),
    el("jaw", "jaw", "beak", (-1.5, 10, -11), (1.5, 11, -9)),
    # Legs: a fluffy thigh that is part of the body, as on a real hen, a
    # scaly shank hinged at the knee, and a foot with three splayed toes in
    # pixel steps and a back toe.
    *mirror("thigh_*", "body", "thigh", (1.5, 3, -1), (4.5, 5, 2)),
    *mirror("shank_*", "leg_*", "leg", (2.5, 1, 0), (3.5, 4, 1)),
    *mirror("toe_mid_*", "foot_*", "toe", (2.5, 0, -3), (3.5, 1, 2)),
    *mirror("toe_in_*", "foot_*", "toe", (1.5, 0, -2), (2.5, 1, -1)),
    *mirror("toe_in_tip_*", "foot_*", "toe", (0.5, 0, -3), (1.5, 1, -2)),
    *mirror("toe_out_*", "foot_*", "toe", (3.5, 0, -2), (4.5, 1, -1)),
    *mirror("toe_out_tip_*", "foot_*", "toe", (4.5, 0, -3), (5.5, 1, -2)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "chicken": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("chicken", (0, 5, 0.5), (0, 0, 0)),
    "head": ("body", (0, 10, -4), (0, 0, 0)),
    "jaw": ("head", (0, 11, -9), (0, 0, 0)),
    "wing_right": ("body", (5.5, 10, -1), (0, 0, 0)),
    "wing_left": ("body", (-5.5, 10, -1), (0, 0, 0)),
    "tail": ("body", (0, 9, 6), (0, 0, 0)),
    "leg_right": ("chicken", (3, 3.5, 0.5), (0, 0, 0)),
    "leg_left": ("chicken", (-3, 3.5, 0.5), (0, 0, 0)),
    "foot_right": ("leg_right", (3, 1, 0.5), (0, 0, 0)),
    "foot_left": ("leg_left", (-3, 1, 0.5), (0, 0, 0)),
}

# For check_clipping.py: the legs hang from the body at the hips, though
# both are children of the root, and the head sits deep in the body.
JOINTS = {
    "leg_right": [("body", 2.5)], "leg_left": [("body", 2.5)],
    "head": [("body", 5.5)], "tail": [("body", 3.5)], "jaw": [("head", 3)],
}


# ---------------------------------------------------------------- painting

def scallop(a, b, v):
    """Feather rows: every feather is 4 px wide and 3 rows tall, rows offset
    by half a feather, with a 2 px shadow under its lower edge. a runs along
    the row, b counts rows (texture pixels)."""
    r = b // 3
    c = (a + (r % 2) * 2) % 4
    if b % 3 == 0 and c in (1, 2):
        return v - 1
    return v


def paint_plume(t):
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f == "down":
        return PLUME[1]
    if t.f in ("west", "east"):
        if y < 6:
            v -= 1                                  # lighter at the top, darker near the ground
        v = scallop(-zi, yi, v)
    elif t.f in ("north", "south"):
        v = scallop(xi, yi, v)
        if t.e["name"] == "breast" and yi >= 8 and abs(xi + 0.5) < 3:
            v += 1                                  # the breast catches the light
    return PLUME[clamp(v, 1)]


def paint_down(t):
    """Soft, pale down under the body: no rows, just light and shadow."""
    v = t.shade
    if t.f == "down":
        return PLUME[2]
    return PLUME[clamp(v + 1, 2)]


def paint_tail(t):
    """Quills: one column per feather, a darker parting between feathers,
    lighter tips on top, ochre on the inner (back-facing) side."""
    x, y, z = t.p
    xi, zi = fi(x), fi(z)
    v = t.shade
    v += 1
    if t.f in ("north", "south"):
        if xi % 2 == 0:
            v -= 1
    elif t.f in ("west", "east"):
        if zi % 2 == 1:
            v -= 1
    if t.f == "up":
        v = 4
    if t.f == "down":
        v = 2
    return FLIGHT[clamp(v, 2)]


def paint_wing(t):
    """Folded wing: scalloped coverts on the shoulder, long secondaries
    below with dark partings, primaries reaching back with darker tips."""
    x, y, z = t.p
    yi, zi = fi(y), fi(z)
    name = t.e["name"]
    v = t.shade
    if t.f in ("east", "west") and abs(x) > 6:     # the outside of the wing
        if name.endswith("_tip"):
            return FLIGHT[2] if yi == 8 else FLIGHT[3]
        if name.endswith("_primaries"):
            if yi == 7:
                return FLIGHT[2]                    # shadowed underside of the tips
            return FLIGHT[3] if zi % 3 else FLIGHT[2]
        if yi >= 8:
            return PLUME[clamp(v + (1 if yi == 9 else 0), 2)]   # coverts
        if yi == 7:
            return FLIGHT[3] if zi % 3 else FLIGHT[2]
        return FLIGHT[2] if zi % 3 else FLIGHT[1]   # bottom edge of the secondaries
    if t.f == "up":
        return PLUME[4] if t.edge else PLUME[3]
    if t.f == "down":
        return FLIGHT[1]
    if t.f in ("north", "south"):
        return FLIGHT[clamp(v + 1, 2)]
    return PLUME[clamp(v, 1)]                       # the inner face, against the body


def paint_head(t):
    """Yellow feathers on the crown and the hackles, red bare skin round the
    eye and down to the beak, a red ear lobe, an orange-ringed eye."""
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f in ("west", "east"):
        if zi in (-7, -6) and yi in (11, 12):       # the eye, 2 x 2
            if zi == -7 and yi == 12:
                return EYE_GLINT
            if zi == -6 and yi == 11:
                return IRIS
            return EYE_DARK
        if zi == -8 and yi in (11, 12):
            return COMB[2]                                     # bare skin ahead of the eye
        if zi == -7 and yi == 10:
            return COMB[2]                                     # and under it
        if zi == -5 and yi == 10:
            return COMB[3]                                     # the ear lobe
        if yi <= 10 or zi >= -5:
            return PLUME[clamp(v - (1 if zi % 2 else 0), 1)]   # hackle streaks
        return PLUME[clamp(v)]
    if t.f == "north":
        if yi >= 13:
            return PLUME[clamp(v + (1 if abs(xi + 0.5) < 1 else 0))]
        if abs(xi + 0.5) in (2.0,) and 10 <= yi <= 12:
            return COMB[2] if yi == 12 else COMB[1]           # red skin beside the beak
        if yi == 9:
            return PLUME[clamp(v - 1, 1)]
        return PLUME[clamp(v)]
    if t.f == "down":
        return PLUME[1]
    if t.f == "up":
        return PLUME[clamp(v)]
    return PLUME[clamp(v - (1 if xi % 2 else 0), 1)]


def paint_beak(t):
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.e["name"] == "jaw":
        if t.f == "up":
            return COMB[1]                          # the inside of the mouth
        return BEAK[clamp(v - 1, 0, 3)]
    if t.e["name"] == "beak_tip":
        if t.f == "down" or yi == 10:
            return BEAK[1]                          # the hook darkens at the tip
        return BEAK[clamp(v, 1, 4)]
    if t.f == "up":
        if zi == -10 and xi in (-2, 1):
            return BEAK[0]                          # nostrils
        return BEAK[4] if xi == -1 else BEAK[3]     # the ridge catches the light
    if t.f == "down":
        return COMB[1]
    return BEAK[clamp(v)]


def paint_comb(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return COMB[1]
    if t.e["name"] == "comb" and t.f in ("west", "east"):
        return COMB[clamp(v - 1, 1)]                # the blade, a shade under the points
    return COMB[clamp(v, 1)]


def paint_wattle(t):
    x, y, z = t.p
    v = t.shade
    if fi(y) == 7:
        v -= 1
    return COMB[clamp(v, 1)]


def paint_thigh(t):
    """Fluffy thighs: soft, with short downward strokes."""
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade + 1
    if t.f in ("west", "east") and yi == 3 and zi % 2 == 0:
        v -= 1
    if t.f in ("north", "south") and yi == 3 and xi % 2 == 0:
        v -= 1
    if t.f == "down":
        return PLUME[1]
    return PLUME[clamp(v, 1)]


def paint_leg(t):
    """Scaly shanks: a darker line between the scale rings."""
    y = t.p[1]
    v = t.shade
    if fi(y) == 1:
        v -= 1
    return LEG[clamp(v, 0, 3)]


def paint_toe(t):
    x, y, z = t.p
    name = t.e["name"]
    v = t.shade
    if t.f == "down":
        return LEG[0]
    tip = name.endswith("_tip") or (name.startswith("toe_mid") and fi(z) == -3)
    back = name.startswith("toe_mid") and fi(z) == 1
    if tip and (t.f == "north" or fi(z) == -3):
        return CLAW[clamp(v - 1, 0, 2)]             # claws
    if back and t.f == "south":
        return CLAW[1]
    return LEG[clamp(v, 0, 4)]


PAINTERS = {"plume": paint_plume, "down": paint_down, "tail": paint_tail, "wing": paint_wing,
            "head": paint_head, "beak": paint_beak, "comb": paint_comb, "wattle": paint_wattle,
            "thigh": paint_thigh, "leg": paint_leg, "toe": paint_toe}


# ---------------------------------------------------------------- animation

def legs(length, swing):
    """A stride: legs swing in opposite phase from the knee and the feet
    counter-rotate to stay flat. The ankle swings on an arc, so a foot rises
    off the ground at both ends of the stride and never dips into it."""
    h = length / 2
    out = {}
    for side, a, b in (("right", -swing, swing), ("left", swing, -swing)):
        out[f"leg_{side}"] = rot((0, (a, 0, 0)), (h, (b, 0, 0)), (length, (a, 0, 0)))
        out[f"foot_{side}"] = rot((0, (-a, 0, 0)), (h, (-b, 0, 0)), (length, (-a, 0, 0)))
    return out


# Rotations are in Blockbench's animation convention: a positive x turns the
# beak down, swings a foot backward and opens the jaw; a positive z lifts the
# right wing away from the body (and a negative z the left one).
ANIMATIONS = {
    # Idle: breathing, quick jerky glances (a chicken holds its head still,
    # then snaps to a new look), a tail flick, a wing shuffle, a soft cluck.
    "idle": {"loop": "loop", "length": 3.0, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (0.75, (1.02, 1.03, 1.0)), (1.5, (1, 1, 1)),
                                (2.25, (1.02, 1.03, 1.0)), (3.0, (1, 1, 1))]),
        "head": track("rotation", [(0, (0, 0, 0)), (0.4, (0, 0, 0)), (0.46, (-5, 12, 3)),
                                   (1.0, (-5, 12, 3)), (1.06, (4, -14, -4)), (1.7, (4, -14, -4)),
                                   (1.76, (10, 0, 0)), (2.3, (10, 0, 0)), (2.36, (0, 0, 0)),
                                   (3.0, (0, 0, 0))], interp="linear"),
        "jaw": rot((0, (0, 0, 0)), (2.4, (0, 0, 0)), (2.5, (14, 0, 0)), (2.6, (0, 0, 0)),
                   (2.7, (12, 0, 0)), (2.8, (0, 0, 0)), (3.0, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.3, (0, 0, 10)), (1.4, (0, 0, -8)),
                    (1.5, (0, 0, 4)), (1.65, (0, 0, 0)), (3.0, (0, 0, 0))),
        "wing_right": rot((0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.12, (0, 0, 14)), (2.3, (0, 0, 0)),
                          (3.0, (0, 0, 0))),
        "wing_left": rot((0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.12, (0, 0, -14)), (2.3, (0, 0, 0)),
                         (3.0, (0, 0, 0))),
    }},
    # Walk: the classic head bob (the head pushes forward, then holds while
    # the body catches up), short strides, a waddle in the tail.
    "walk": {"loop": "loop", "length": 0.8, "bones": {
        **legs(0.8, 24),
        "body": track("position", [(0, (0, 0, 0)), (0.2, (0, 0.5, 0)), (0.4, (0, 0, 0)),
                                   (0.6, (0, 0.5, 0)), (0.8, (0, 0, 0))])
        + rot((0, (0, -3, 0)), (0.4, (0, 3, 0)), (0.8, (0, -3, 0))),
        "head": track("position", [(0, (0, 0, 0)), (0.12, (0, 0, -1.5)), (0.4, (0, 0, 0)),
                                   (0.52, (0, 0, -1.5)), (0.8, (0, 0, 0))])
        + rot((0, (0, 3, 0)), (0.4, (0, -3, 0)), (0.8, (0, 3, 0))),
        "tail": sway(0.8, 6, 0.1, 2),
    }},
    # Run: leaning forward, wings half open and beating, long fast strides.
    "run": {"loop": "loop", "length": 0.4, "bones": {
        **legs(0.4, 32),
        "body": rot((0, (14, 0, 0)), (0.4, (14, 0, 0)))
        + track("position", [(0, (0, 0, 0)), (0.1, (0, 0.8, 0)), (0.2, (0, 0, 0)),
                             (0.3, (0, 0.8, 0)), (0.4, (0, 0, 0))]),
        "head": rot((0, (-12, 0, 0)), (0.4, (-12, 0, 0))),
        "wing_right": rot((0, (0, 0, 20)), (0.1, (0, 0, 55)), (0.2, (0, 0, 20)),
                          (0.3, (0, 0, 55)), (0.4, (0, 0, 20))),
        "wing_left": rot((0, (0, 0, -20)), (0.1, (0, 0, -55)), (0.2, (0, 0, -20)),
                         (0.3, (0, 0, -55)), (0.4, (0, 0, -20))),
        "tail": rot((0, (-10, 0, 0)), (0.4, (-10, 0, 0))),
        "jaw": rot((0, (10, 0, 0)), (0.4, (10, 0, 0))),
    }},
    # Attack: rear back with the wings up (anticipation), a fast double peck,
    # a beat of the wings, settle.
    "attack": {"loop": "once", "length": 0.9, "bones": {
        "body": rot((0, (0, 0, 0)), (0.25, (-8, 0, 0)), (0.36, (12, 0, 0)), (0.46, (6, 0, 0)),
                    (0.56, (12, 0, 0)), (0.7, (3, 0, 0)), (0.9, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.25, (-20, 0, 0)), (0.36, (24, 0, 0)), (0.46, (12, 0, 0)),
                    (0.56, (24, 0, 0)), (0.7, (0, 0, 0)), (0.9, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.25, (15, 0, 0)), (0.36, (0, 0, 0)), (0.46, (13, 0, 0)),
                   (0.56, (0, 0, 0)), (0.9, (0, 0, 0))),
        "wing_right": rot((0, (0, 0, 0)), (0.25, (0, 0, 60)), (0.36, (0, 0, 20)),
                          (0.46, (0, 0, 50)), (0.56, (0, 0, 15)), (0.9, (0, 0, 0))),
        "wing_left": rot((0, (0, 0, 0)), (0.25, (0, 0, -60)), (0.36, (0, 0, -20)),
                         (0.46, (0, 0, -50)), (0.56, (0, 0, -15)), (0.9, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.25, (-14, 0, 0)), (0.36, (8, 0, 0)), (0.9, (0, 0, 0))),
    }},
    # Hit: a squawking jolt, feathers puffed, wings flared, head tossed.
    "hit": {"loop": "once", "length": 0.45, "bones": {
        "body": rot((0, (0, 0, 0)), (0.08, (-8, 0, 3)), (0.22, (2, 0, -1)), (0.45, (0, 0, 0)))
        + track("scale", [(0, (1, 1, 1)), (0.08, (1.08, 1.06, 1.06)), (0.22, (0.98, 1.0, 0.99)),
                          (0.45, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.08, (-12, 10, 5)), (0.22, (3, -3, -2)), (0.45, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.08, (16, 0, 0)), (0.3, (0, 0, 0)), (0.45, (0, 0, 0))),
        "wing_right": rot((0, (0, 0, 0)), (0.08, (0, 0, 50)), (0.25, (0, 0, 8)), (0.45, (0, 0, 0))),
        "wing_left": rot((0, (0, 0, 0)), (0.08, (0, 0, -50)), (0.25, (0, 0, -8)), (0.45, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.08, (-16, 0, 6)), (0.45, (0, 0, 0))),
    }},
}

CHICKEN = Creature("chicken", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    CHICKEN.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                  preview_scale=16, tile=(420, 360), anchor=0.82)
