"""Build the Blockbench highland cow: shaggy, ginger, wide-horned, 1.7 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. The user
  asked for 1.7 m: 54 px from the hooves to the horn tips (1.69 m), the
  nearest whole pixel.
- Box sizes in whole texture pixels. Odd widths for the centred parts (body,
  head, muzzle, jaw, forelock) so the face has a centre column.
- Per-face UV, one texture inside the large-creature budget, hidden faces
  removed.
- The long coat is the point of a highland cow. It's built the way the
  study's references build fur (STUDY 3.1, "fringe pixels"): hair hangs
  below the body as a skirt of 1-3 px pieces of uneven length along the
  flanks, chest, belly and rump, hairy "trousers" on the legs, a big dossan
  (forelock) with strands hanging over the eyes, cheek hair, a beard and
  hairy ears. Every piece is a real box, so the silhouette is shaggy from
  any side.
- Painted as long strands: 2 px wide locks running down the form with
  darker partings and lighter locks in clusters, sun-bleached tips on the
  hanging ends, a parting along the spine. Lit from the top, slightly
  front-left, hue-shifted ramps (shadows toward plum, highlights warm).
- There is no highland cow icon, so the colours follow ART-DIRECTION section
  5: the ginger coat is built round the warm creature swatch #BD753B. The
  one saturated accent is a yellow ear tag in each ear, as on farm
  highlands; the horns are the lightest value.
- Bones use the shared creature names, pivots at the joints. The jaw chews,
  the ears flick, the tail is a two-bone chain with a tuft. Animations:
  idle, walk, run, attack (a horn hook), hit.

Usage: python build_highland_cow_bbmodel.py [out_dir]   (writes
highland_cow.bbmodel, highland_cow.png, highland_cow_preview.png and
highland_cow_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py highland_cow.bbmodel --spec build_highland_cow_bbmodel.py
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import Creature, clamp, el, fi, hexrgb, mirror, ramp, rot, sway, track  # noqa: E402

# Ramps, darkest first. Shadows lean plum, highlights lean warm.
# Kept close in value: in the game's light a wider ramp turned the long
# hair into busy flecks of plum and orange.
HAIR = ramp("#5b2a2c", "#803b29", "#a5522a", "#c66d31", "#de914c")     # round #BD753B
SKIN = ramp("#55303a", "#7c4c50", "#a26a64", "#c58b7c", "#dfae98")     # dusky muzzle, inner ears
HORN = ramp("#4e4036", "#8a7560", "#c2a985", "#e3cfaa", "#f4e9d2")
HORN_TIP = ramp("#2e2229", "#4f3a33", "#76573f")
HOOF = ramp("#21191f", "#36282f", "#4f3c41", "#6a5555")
TAG = ramp("#7c4d0e", "#c98a16", "#f0be2a", "#ffe07a")                 # the accent
EYE_DARK = hexrgb("#1a1018")
EYE_GLINT = hexrgb("#fff3e2")

# Uneven lengths for the hanging hair, in px: a rhythm, not noise.
LENS = (3, 5, 4, 2, 5, 3, 4, 5, 2, 4, 3, 5, 4, 3, 2, 4)


# ---------------------------------------------------------------- geometry

def skirt():
    """The coat hanging below the body: along both flanks (1 px clear of the
    legs' trousers), across the chest, and under the belly and the rump
    between the legs, where the legs never swing."""
    out = []
    for k, z0 in enumerate(range(-19, 19, 3)):
        out.append(el(f"fringe_right_{k}", "body", "fringe", (12.5, 17 - LENS[k], z0), (13.5, 17, z0 + 3)))
        L = LENS[(k + 5) % len(LENS)]
        out.append(el(f"fringe_left_{k}", "body", "fringe", (-13.5, 17 - L, z0), (-12.5, 17, z0 + 3)))
    for k in range(7):
        x0 = -10.5 + 3 * k
        out.append(el(f"fringe_chest_{k}", "body", "fringe", (x0, 17 - LENS[k + 2], -21),
                      (x0 + 3, 17, -20)))
    for k, (x0, x1, L) in enumerate(((-3.5, -1.5, 3), (-1.5, 1.5, 4), (1.5, 3.5, 2))):
        out.append(el(f"fringe_rump_{k}", "body", "fringe", (x0, 17 - L, 16), (x1, 17, 18)))
    for k, z0 in enumerate(range(-6, 6, 3)):
        out.append(el(f"fringe_belly_{k}", "body", "fringe", (-3.5, 17 - (2, 3, 2, 3)[k], z0),
                      (3.5, 17, z0 + 3)))
    return out


# The outer coat over the shoulders and flanks: clumps that hang to uneven
# depths, so the side of the body is layered, not one flat box face.
CLUMPS = [(-19, -14, 31), (-14, -9, 28), (-9, -4, 32), (-4, 1, 29), (1, 6, 33), (6, 11, 30),
          (11, 15, 32), (15, 19, 29)]


def mantle():
    out = []
    for k, (z0, z1, yb) in enumerate(CLUMPS):
        out += mirror(f"mantle_*_{k}", "body", "fringe", (13.5, yb, z0), (14.5, 39, z1))
    return out


# Hair hanging over the eyes, left to right: x from, x to, bottom y.
STRANDS = [(-8.5, -6.5, 31), (-6.5, -5.5, 33), (-5.5, -3.5, 34), (-3.5, -1.5, 32), (-1.5, 1.5, 33),
           (1.5, 3.5, 32), (3.5, 5.5, 34), (5.5, 6.5, 33), (6.5, 8.5, 31)]

ELEMENTS = [
    # Body: a deep, long barrel under the coat, a shaggy back and withers,
    # a ruff of neck hair the head grows out of, chest and breech shag.
    el("body", "body", "coat", (-13.5, 17, -19), (13.5, 40, 19)),
    el("body_top", "body", "coat", (-12.5, 40, -18), (12.5, 42, 18)),
    el("withers", "body", "coat", (-10.5, 42, -16), (10.5, 43, -5)),
    el("chest", "body", "coat", (-11.5, 17, -21), (11.5, 38, -19)),
    el("breech", "body", "coat", (-11.5, 20, 19), (11.5, 38, 20)),
    el("ruff", "body", "coat", (-9.5, 24, -26), (9.5, 41, -19)),
    *mantle(),
    *skirt(),
    # Head: broad and short-faced, a dusky muzzle, the dossan and its
    # strands, cheek hair, a chewing jaw with a beard.
    el("head", "head", "face", (-7.5, 25, -39), (7.5, 40, -28)),
    el("neck", "head", "coat", (-4.5, 29, -28), (4.5, 35, -22)),
    el("muzzle", "head", "muzzle", (-6.5, 25, -43), (6.5, 31, -39)),
    el("forelock", "head", "mop", (-8.5, 36, -40), (8.5, 44, -32)),
    el("forelock_top", "head", "mop", (-6.5, 44, -38), (6.5, 45, -33)),
    *[el(f"strand_{k}", "head", "mop", (x0, yb, -40), (x1, 36, -39))
      for k, (x0, x1, yb) in enumerate(STRANDS)],
    *mirror("cheek_*", "head", "coat", (7.5, 28, -38), (8.5, 36, -29)),
    *mirror("cheek_*_tuft", "head", "fringe", (7.5, 25, -36), (8.5, 28, -32)),
    el("jaw", "jaw", "jaw", (-5.5, 22, -42), (5.5, 25, -33)),
    el("beard", "jaw", "fringe", (-4.5, 20, -39), (4.5, 22, -33)),
    # Horns: out from the poll, a slight droop, then sweeping up to tips.
    *mirror("horn_*_1", "head", "horn", (8.5, 38, -34), (13.5, 42, -30)),
    *mirror("horn_*_2", "head", "horn", (13.5, 38, -33.5), (18.5, 41, -30.5)),
    *mirror("horn_*_3", "head", "horn", (18.5, 39, -33.5), (22.5, 42, -30.5)),
    *mirror("horn_*_4", "head", "horn", (21.5, 42, -33.5), (24.5, 46, -30.5)),
    *mirror("horn_*_5", "head", "horn", (22.5, 46, -33), (24.5, 50, -31)),
    *mirror("horn_*_6", "head", "horn", (23, 50, -32.5), (24, 54, -31.5)),
    # Ears: hairy flaps under the horns, a fringe, and a yellow tag.
    *mirror("ear_*", "ear_*", "ear", (7.5, 32, -33), (14.5, 35, -30)),
    *mirror("ear_*_fringe", "ear_*", "fringe", (9.5, 31, -33), (14.5, 32, -30)),
    *mirror("ear_tag_*", "ear_*", "tag", (11.5, 30, -34), (13.5, 33, -33)),
    # Legs: 7 x 7 pillars, 4 px hidden in the body, under hairy trousers
    # and a feathered fetlock, on cloven hooves that step in to a narrow
    # sole, so a hoof's corner never dips into the ground mid-stride. The trousers stop 2 px under the body, so a
    # full stride never drives their corners up into it.
    *mirror("leg_front_*", "leg_front_*", "leg", (4.5, 3, -15), (11.5, 21, -8)),
    *mirror("hoof_front_*", "leg_front_*", "hoof", (5, 1, -14.5), (11, 3, -8.5)),
    *mirror("sole_front_*", "leg_front_*", "hoof", (5.5, 0, -13), (10.5, 1, -10)),
    *mirror("trousers_front_*", "leg_front_*", "trousers", (4, 8, -15.5), (12, 15, -7.5)),
    *mirror("fetlock_front_*", "leg_front_*", "trousers", (4, 4, -15.5), (12, 6, -7.5)),
    *mirror("leg_back_*", "leg_back_*", "leg", (4.5, 3, 8), (11.5, 21, 15)),
    *mirror("hoof_back_*", "leg_back_*", "hoof", (5, 1, 8.5), (11, 3, 14.5)),
    *mirror("sole_back_*", "leg_back_*", "hoof", (5.5, 0, 10), (10.5, 1, 13)),
    *mirror("trousers_back_*", "leg_back_*", "trousers", (4, 8, 7.5), (12, 15, 15.5)),
    *mirror("fetlock_back_*", "leg_back_*", "trousers", (4, 4, 7.5), (12, 6, 15.5)),
    # Tail: a long rope from the top of the rump and a big switch.
    el("tail_1", "tail", "coat", (-1.5, 26, 20), (1.5, 38, 23)),
    el("tail_2", "tail_lower", "coat", (-1.5, 17, 20), (1.5, 26, 23)),
    el("tail_tuft", "tail_lower", "fringe", (-2.5, 9, 19.5), (2.5, 17, 23.5)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "highland_cow": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("highland_cow", (0, 28, 0), (0, 0, 0)),
    "head": ("body", (0, 32, -26), (0, 0, 0)),
    "jaw": ("head", (0, 25, -33), (0, 0, 0)),
    "ear_right": ("head", (8.5, 33.5, -31.5), (0, 0, -12)),
    "ear_left": ("head", (-8.5, 33.5, -31.5), (0, 0, 12)),
    "tail": ("body", (0, 37, 21.5), (0, 0, 0)),
    "tail_lower": ("tail", (0, 26, 21.5), (0, 0, 0)),
    "leg_front_right": ("highland_cow", (8, 17.5, -11.5), (0, 0, 0)),
    "leg_front_left": ("highland_cow", (-8, 17.5, -11.5), (0, 0, 0)),
    "leg_back_right": ("highland_cow", (8, 17.5, 11.5), (0, 0, 0)),
    "leg_back_left": ("highland_cow", (-8, 17.5, 11.5), (0, 0, 0)),
}

# For check_clipping.py: (other bone, joint radius px[, deepest fold px]).
# The legs hang from the body at the hips and shoulders, though both are
# children of the root; the big head turns inside its ruff of neck hair.
JOINTS = {
    **{f"leg_{e}_{s}": [("body", 7.5, 1.5)] for e in ("front", "back") for s in ("right", "left")},
    "head": [("body", 12, 1.5)],
    "jaw": [("head", 6, 1.0)],
    "ear_right": [("head", 3)], "ear_left": [("head", 3)],
    "tail": [("body", 3)], "tail_lower": [("tail", 3)],
}


# ---------------------------------------------------------------- painting

# Each lock's tone (a step darker, the same, or a step lighter) and where
# along it a parting falls; the locks wander sideways in a slow wave, so the
# coat reads as long wavy hair running down the form.
LOCK = (0, -1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 1, 0, -1, 1, 0, 0)
PART = (0, 6, 3, 9, 1, 7, 4, 10, 2, 8, 5, 0, 6, 3, 9, 4, 7)
WAVE = (0, 0, 1, 1, 1, 0, 0, -1, -1, -1)


def strands(a, b, v, period=11):
    """Long hair: 2 px wide locks running along b, each with its own tone,
    a 1 px parting where it ends and a 2 px gleam on the lit side. a runs
    across the hair, b along it (texture pixels)."""
    lock = (a + WAVE[b % len(WAVE)]) // 2
    off = LOCK[lock % len(LOCK)]
    k = (b + PART[lock % len(PART)]) % period
    if k == 0:
        off -= 1
    elif k in (5, 6) and off <= 0 and (a + WAVE[b % len(WAVE)]) % 2 == 0:
        off += 1
    return v + max(-1, min(1, off))


def coat(t, tips=False):
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    if t.f == "down":
        return HAIR[1] if not tips else HAIR[2]
    if t.f == "up":
        if abs(x) < 1 and t.e["name"] in ("body_top", "withers"):
            return HAIR[clamp(v - 1)]               # the parting along the spine
        return HAIR[clamp(strands(zi, fi(abs(x)), v, 9))]
    if t.f in ("west", "east"):
        a = zi
    else:
        a = xi
    if y < 23 and not tips:
        v -= 1                                      # darker toward the belly
    elif y >= 36 and t.f in ("west", "east"):
        v += 1                                      # the sun on the shoulders and back
    v = strands(a, -yi, v)
    if tips and t.j == t.h - 1:
        v += 1                                      # sun-bleached hanging ends
    return HAIR[clamp(v)]


def paint_coat(t):
    return coat(t)


def paint_fringe(t):
    return coat(t, tips=True)


def paint_mop(t):
    """The dossan: thick, wavy and lighter on top, its strands lit at the
    ends where they catch the sun."""
    x, y, z = t.p
    xi, yi = fi(x), fi(y)
    v = t.shade
    if t.f == "up":
        return HAIR[clamp(strands(xi, fi(z), v + (1 if (xi + fi(z)) % 5 == 0 else 0), 6))]
    if t.f == "down":
        return HAIR[1]
    v = strands(xi if t.f in ("north", "south") else fi(z), -yi, v, 6)
    if t.e["name"].startswith("strand") and t.j == t.h - 1:
        v += 1
    return HAIR[clamp(v)]


def paint_face(t):
    """Hair all over the head; the eyes peek out from under the strands."""
    x, y, z = t.p
    xi, yi = fi(x), fi(y)
    v = t.shade
    if t.f == "north":
        if yi in (32, 33) and (xi in (4, 5) or xi in (-6, -5)):
            if yi == 33 and xi in (4, -5):
                return EYE_GLINT
            return EYE_DARK
        if yi in (34, 35):
            return HAIR[clamp(v - 2)]               # shadow under the dossan
        return HAIR[clamp(strands(xi, -yi, v - 1))]
    return coat(t)


def paint_muzzle(t):
    x, y, z = t.p
    xi, yi = fi(x), fi(y)
    v = t.shade
    if t.f == "north":
        if yi in (28, 29) and xi in (2, 3, -4, -3):
            return SKIN[0] if (xi in (2, -3) or yi == 28) else SKIN[1]   # nostrils
        if xi in (-1, 0) and yi <= 27:
            v -= 1                                  # philtrum
        if yi == 25:
            v -= 1
    if t.f == "up":
        return HAIR[clamp(v - 1)] if z > -40 else SKIN[clamp(v)]
    if t.f == "down":
        return SKIN[1]
    return SKIN[clamp(v)]


def paint_jaw(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "up":
        return SKIN[1]                              # inside the mouth
    if t.f == "north":
        return SKIN[clamp(v - (1 if fi(y) == 22 else 0))]
    if fi(z) <= -40:
        return SKIN[clamp(v)]
    return coat(t)


def paint_horn(t):
    """Cream horns with grey-brown ridged bases and dark tips."""
    x, y, z = t.p
    v = t.shade
    n = int(t.e["name"][-1])
    if n >= 5:
        return HORN_TIP[clamp(v - 1 + (1 if n == 5 else 0), 0, 2)] if n == 6 or y >= 48 else HORN[clamp(v)]
    if n == 1:
        v -= 1 if fi(abs(x)) % 2 == 0 else 0        # ridges at the base
        return HORN[clamp(v, 0, 3)]
    if t.f == "down":
        return HORN[1]
    return HORN[clamp(v)]


def paint_ear(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "north":                              # inner ear, hairy rim
        if t.j in (0, t.h - 1) or t.i in (0, t.w - 1):
            return HAIR[clamp(v)]
        return SKIN[3] if t.j == 1 else SKIN[2]
    return coat(t, tips=True)


def paint_tag(t):
    v = t.shade
    if t.f == "north" and t.j == 1 and t.i == 1:
        return TAG[0]                               # the printed number
    if t.f == "down":
        return TAG[1]
    return TAG[clamp(v, 1, 3)]


def paint_leg(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return HAIR[0]
    if fi(y) >= 17:
        v -= 1                                      # under the body
    return HAIR[clamp(strands(fi(z) if t.f in ("west", "east") else fi(x), -fi(y), v - 1), 0, 3)]


def paint_hoof(t):
    """Cloven hooves: a dark cleft down the front and back, lit edges."""
    x, y, z = t.p
    cx = (t.e["lo"][0] + t.e["hi"][0]) / 2
    if t.f == "down":
        return HOOF[0]
    if t.f in ("north", "south") and abs(x - cx) < 0.5:
        return HOOF[0]
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1}[t.f]
    if t.e["name"].startswith("sole"):
        v -= 1
    return HOOF[clamp(v + (1 if t.edge else 0), 0, 3)]


def paint_trousers(t):
    return coat(t, tips=True)


PAINTERS = {"coat": paint_coat, "fringe": paint_fringe, "mop": paint_mop, "face": paint_face,
            "muzzle": paint_muzzle, "jaw": paint_jaw, "horn": paint_horn, "ear": paint_ear,
            "tag": paint_tag, "leg": paint_leg, "hoof": paint_hoof, "trousers": paint_trousers}


# ---------------------------------------------------------------- animation

# Rotations are in Blockbench's animation convention (5.2.2 applies a key as
# -x, -y, +z on top of the rest rotation): a positive x turns the head's nose
# down, opens the jaw, and swings a foot or the hanging tail backward; a
# positive z lifts a right-side part (and swishes the tail to the right).
ANIMATIONS = {
    # Placid idle: slow breathing, chewing the cud, a slow look round, ear
    # flicks, a lazy tail swish.
    "idle": {"loop": "loop", "length": 4.0, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (2.0, (1.008, 1.012, 1.0)), (4.0, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (1.0, (2, 6, 1)), (2.0, (4, 0, 0)), (3.0, (2, -6, -1)),
                    (4.0, (0, 0, 0))),
        "jaw": track("rotation", [(round(0.5 * k, 3), ((3, 4, 0) if k % 2 else (1, -4, 0)))
                                  for k in range(9)]),
        "ear_right": rot((0, (0, 0, 0)), (2.6, (0, 0, 0)), (2.7, (0, 14, 10)), (2.85, (0, -4, -3)),
                         (3.0, (0, 0, 0)), (4.0, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (1.0, (0, 0, 0)), (1.1, (0, -14, -10)), (1.25, (0, 4, 3)),
                        (1.4, (0, 0, 0)), (4.0, (0, 0, 0))),
        "tail": sway(4.0, 10, 0.0, 2),
        "tail_lower": sway(4.0, 14, 0.15, 2),
    }},
    # Walk: a slow, heavy amble, the body rolling on the beat, the head
    # nodding, the tail swinging behind.
    "walk": {"loop": "loop", "length": 1.6, "bones": {
        "leg_front_right": rot((0, (-15, 0, 0)), (0.8, (15, 0, 0)), (1.6, (-15, 0, 0))),
        "leg_back_left": rot((0, (-14, 0, 0)), (0.8, (14, 0, 0)), (1.6, (-14, 0, 0))),
        "leg_front_left": rot((0, (15, 0, 0)), (0.8, (-15, 0, 0)), (1.6, (15, 0, 0))),
        "leg_back_right": rot((0, (14, 0, 0)), (0.8, (-14, 0, 0)), (1.6, (14, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.4, (0, 0.6, 0)), (0.8, (0, 0, 0)),
                                   (1.2, (0, 0.6, 0)), (1.6, (0, 0, 0))])
        + rot((0, (1, 0, 0)), (0.8, (-1, 0, 0)), (1.6, (1, 0, 0))),
        "head": rot((0, (2, 0, 0)), (0.4, (5, 0, 0)), (0.8, (2, 0, 0)), (1.2, (5, 0, 0)),
                    (1.6, (2, 0, 0))),
        "tail": sway(1.6, 8, 0.0, 2),
        "tail_lower": sway(1.6, 12, 0.15, 2),
    }},
    # Run: a rocking gallop, front and back pairs nearly together, the head
    # low and the tail streaming back.
    "run": {"loop": "loop", "length": 0.8, "bones": {
        "leg_front_right": rot((0, (-20, 0, 0)), (0.4, (18, 0, 0)), (0.8, (-20, 0, 0))),
        "leg_front_left": rot((0, (-17, 0, 0)), (0.4, (20, 0, 0)), (0.8, (-17, 0, 0))),
        "leg_back_right": rot((0, (18, 0, 0)), (0.4, (-18, 0, 0)), (0.8, (18, 0, 0))),
        "leg_back_left": rot((0, (20, 0, 0)), (0.4, (-15, 0, 0)), (0.8, (20, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.2, (0, 1.5, 0)), (0.4, (0, 0, 0)),
                                   (0.6, (0, 0.8, 0)), (0.8, (0, 0, 0))])
        + rot((0, (-1, 0, 0)), (0.4, (1, 0, 0)), (0.8, (-1, 0, 0))),
        "head": rot((0, (8, 0, 0)), (0.4, (4, 0, 0)), (0.8, (8, 0, 0))),
        "ear_right": rot((0, (0, -16, 0)), (0.8, (0, -16, 0))),
        "ear_left": rot((0, (0, 16, 0)), (0.8, (0, 16, 0))),
        "tail": rot((0, (30, 0, 0)), (0.4, (40, 0, 0)), (0.8, (30, 0, 0))),
        "tail_lower": rot((0, (10, 0, 0)), (0.4, (18, 0, 0)), (0.8, (10, 0, 0))),
    }},
    # Horn hook: drop the head and swing it aside (anticipation), then hook
    # the horns up and across, hold, settle.
    "attack": {"loop": "once", "length": 1.2, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.4, (0, -0.6, 0.6)), (0.55, (0, 0.3, -1.0)),
                                   (0.75, (0, 0.3, -1.0)), (1.2, (0, 0, 0))])
        + rot((0, (0, 0, 0)), (0.4, (1.5, 0, 0)), (0.55, (-1.5, 0, 0)), (1.2, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.4, (12, 10, 6)), (0.55, (-6, -12, -8)), (0.75, (-5, -11, -7)),
                    (1.2, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.5, (8, 0, 0)), (0.9, (0, 0, 0)), (1.2, (0, 0, 0))),
        "leg_front_right": rot((0, (0, 0, 0)), (0.15, (-16, 0, 0)), (0.28, (4, 0, 0)),
                               (0.4, (0, 0, 0)), (0.55, (-10, 0, 0)), (1.2, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.4, (0, -18, 0)), (1.2, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.4, (0, 18, 0)), (1.2, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.4, (20, 0, 0)), (0.55, (26, 0, 12)), (1.2, (0, 0, 0))),
    }},
    # Hit: a heavy flinch back, head tossed, ears pinned, tail flick.
    "hit": {"loop": "once", "length": 0.5, "bones": {
        "body": track("position", [(0, (0, 0, 0)), (0.08, (0, 0, 1.0)), (0.25, (0, 0, -0.2)),
                                   (0.5, (0, 0, 0))])
        + track("scale", [(0, (1, 1, 1)), (0.08, (1.02, 0.97, 1.01)), (0.25, (0.995, 1.01, 1.0)),
                          (0.5, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.08, (-8, 10, 4)), (0.25, (2, -3, -1)), (0.5, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.08, (10, 0, 0)), (0.5, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.08, (0, -24, 10)), (0.5, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.08, (0, 24, -10)), (0.5, (0, 0, 0))),
        "tail": rot((0, (0, 0, 0)), (0.08, (24, 0, 16)), (0.5, (0, 0, 0))),
    }},
}

HIGHLAND_COW = Creature("highland_cow", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    HIGHLAND_COW.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                       preview_scale=4.4, tile=(420, 360), anchor=0.86)
