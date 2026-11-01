"""Build the Blockbench snake: green and purple, coiled and reared up, 1 m tall (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m, so the
  1 m the user asked for is 32 px from the ground to the top of the head.
- The coil is drawn the way a pixel artist draws a circle: the body's path is
  a spiral, rasterised onto the pixel grid in plan, and every run of pixels
  of the same height becomes one axis-aligned box. So the coil keeps the
  same pixel grid as the rest of the model (no rotated boxes, no seams, no
  overlapping faces), with stepped round edges like Minecraft circles. A
  flat spiral on the ground climbs onto a second loop, and the neck rises
  from the front of it.
- The neck is three bones with rest rotations that bend it into an S
  ("rotated boxes sparingly": the neck, the head and nothing else), so it
  can sway and strike. The head is a viper wedge: wide jaw muscles, a
  narrower snout, brow ridges over slit-pupil eyes, fangs, a jaw that opens
  and a forked tongue that flicks.
- Painted as scales (STUDY 5.3): rows of 2 px scales, lighter at the top of
  each. Green with purple diamond saddles down the back, purple blotches on
  the sides, a pale belly edge. Lit from the top, slightly front-left, with
  edge highlights where the surface turns over, so the coil reads round.
- No snake icon, so the colours follow ART-DIRECTION section 5: the greens
  shift to teal in shadow and to yellow-green in the light, the purples to
  indigo and lilac. The gold eyes are the one saturated accent (STUDY 3.1).
- Bones: snake > body (the coil) > tail, neck_1 > neck_2 > neck_3 > head >
  jaw > tongue. Animations: idle, walk (a gliding sway), run, attack (a
  strike), hit.

Usage: python build_snake_bbmodel.py [out_dir]   (writes snake.bbmodel,
snake.png, snake_preview.png and snake_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py snake.bbmodel --spec build_snake_bbmodel.py
"""

import math
import sys
from collections import defaultdict
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import Creature, clamp, el, fi, mirror, ramp, rot, sway, track  # noqa: E402

# Ramps, darkest first. Greens shade toward teal and light toward yellow;
# purples shade toward indigo and light toward lilac.
# Both a step deeper and warmer than they look in Blockbench: the game's sun
# washed the first greens out to mint and pushed the purples to blue.
GREEN = ramp("#173230", "#22503a", "#2f6e3e", "#4b8f43", "#78b052")
PURPLE = ramp("#2a1534", "#47204f", "#673073", "#8a4794", "#a866ad")
BELLY = ramp("#4a5a3c", "#7a8a52", "#a9b46c", "#cfd28e")
GOLD = ramp("#6e3f0a", "#c9821a", "#f7c437", "#fff09a")                # the accent: eyes
FANG = ramp("#8f897e", "#d4cdbd", "#f2ecde")
TONGUE = ramp("#4e1230", "#8d2045", "#cf4466")
MOUTH = ramp("#2a1424", "#4e2236", "#7a3550")


# ---------------------------------------------------------------- the coil

CX, CZ = 0.0, 3.0                       # the centre of the coil (px, plan)
GROUND_TURNS = 1.15                     # how far the ground spiral winds in
U = 2 * math.pi * GROUND_TURNS
ALPHA_UP = math.radians(-30)            # where the body climbs onto the upper loop
ALPHA0 = ALPHA_UP - U                   # where the tail tip lies
ALPHA_NECK = math.radians(270)          # the front, where the neck rises
R_UP = 6.0                              # the upper loop's centreline radius
TAIL_END = 1.0                          # the tail bone is the first radian of the spiral


def ground_r(u):
    return 15 - 7 * u / (2 * math.pi)


def ground_w(u):
    return 2 + 5 * min(1.0, u / math.pi)          # the tail tapers to a point


def ground_h(u):
    h = 2 + 4 * min(1.0, u / math.pi)
    ramp_len = math.pi / 3
    if u > U - ramp_len:                          # the climb onto the upper loop
        h += 6 * (u - (U - ramp_len)) / ramp_len
    return h


def ground_s(u):
    """Arc length along the spiral from the tail tip, px."""
    return 15 * u - 7 * u * u / (4 * math.pi)


S_UP0 = ground_s(U)


def polar(x, z):
    return math.hypot(x - CX, z - CZ), math.atan2(z - CZ, x - CX)


def ground_at(x, z):
    """(u, lateral offset) of the ground spiral at this plan point, or None."""
    rho, phi = polar(x, z)
    best = None
    for n in range(-3, 4):
        u = phi - ALPHA0 + 2 * math.pi * n
        if 0 <= u <= U:
            d = rho - ground_r(u)
            if abs(d) <= ground_w(u) / 2 and (best is None or abs(d) < abs(best[1])):
                best = (u, d)
    return best


def upper_at(x, z):
    """(angle travelled from the climb, lateral offset) on the upper loop."""
    rho, phi = polar(x, z)
    a = (phi - ALPHA_UP) % (2 * math.pi)
    if a <= ALPHA_NECK - ALPHA_UP and abs(rho - R_UP) <= 3.5:
        return a, rho - R_UP
    return None


def coil_cells():
    """Every plan pixel of the coil: (x, z) -> (bone, top y)."""
    cells = {}
    for xi in range(-20, 20):
        for zi in range(-16, 22):
            x, z = xi + 0.5, zi + 0.5
            top = 0
            g = ground_at(x, z)
            if g:
                top = max(top, round(ground_h(g[0])))
            if math.hypot(x - CX, z - CZ) < 4.5:
                top = max(top, 6)                 # the packed middle of the coil
            if upper_at(x, z):
                top = max(top, 12)
            if top:
                bone = "tail" if g and g[0] < TAIL_END and top == round(ground_h(g[0])) else "body"
                cells[(xi, zi)] = (bone, top)
    return cells


def coil_boxes():
    """Merge the plan pixels into boxes: runs along x of the same bone and
    height, then identical runs stacked along z."""
    cells = coil_cells()
    runs = defaultdict(list)                      # (x0, x1, bone, top) -> [z rows]
    for zi in range(-16, 22):
        xi = -20
        while xi < 20:
            if (xi, zi) not in cells:
                xi += 1
                continue
            key = cells[(xi, zi)]
            x0 = xi
            while (xi, zi) in cells and cells[(xi, zi)] == key:
                xi += 1
            runs[(x0, xi) + key].append(zi)
    out = []
    for (x0, x1, bone, top), zs in sorted(runs.items(), key=lambda kv: (kv[1][0], kv[0][0])):
        zs.sort()
        start = prev = zs[0]
        for z in zs[1:] + [None]:
            if z is not None and z == prev + 1:
                prev = z
                continue
            out.append(el(f"coil_{len(out)}", bone, "coil", (x0, 0, start), (x1, top, prev + 1)))
            if z is not None:
                start = prev = z
    return out


# ---------------------------------------------------------------- geometry

ELEMENTS = [
    *coil_boxes(),
    # The neck rises out of the front of the upper loop on a base that is
    # part of the coil, then bends into an S over three bones, tapering 7, 6,
    # 5, 4 px to the narrow neck of a viper. Each piece sits 2-3 px inside
    # the wider one below, so a strike never opens a gap.
    el("neck_base", "body", "neck", (-3.5, 6, -6.5), (3.5, 15, 0.5)),
    el("neck_1", "neck_1", "neck", (-3, 12, -6), (3, 19, 0)),
    el("neck_2", "neck_2", "neck", (-2.5, 17, -5.5), (2.5, 24, -0.5)),
    el("neck_3", "neck_3", "neck", (-2, 22, -5), (2, 28, -1)),
    # Head: wide jaw muscles, a narrower snout, a blunt nose, brow ridges.
    # The jaw is hinged under the eyes, in front of the neck.
    el("head", "head", "head", (-4.5, 26, -9), (4.5, 32, 0)),
    el("snout", "head", "head", (-3.5, 26, -14), (3.5, 31, -9)),
    el("nose", "head", "head", (-2.5, 26, -15), (2.5, 30, -14)),
    *mirror("brow_*", "head", "brow", (2.5, 32, -9), (4.5, 33, -5)),
    *mirror("fang_*", "head", "fang", (1.5, 24, -14), (2.5, 26, -13)),
    el("jaw", "jaw", "jaw", (-3.5, 24, -13), (3.5, 26, -6)),
    el("tongue", "tongue", "tongue", (-0.5, 25, -17), (0.5, 26, -9)),
    *mirror("tongue_fork_*", "tongue", "tongue", (0.5, 25, -18), (1.5, 26, -17)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
_g = (lambda u: (CX + ground_r(u) * math.cos(ALPHA0 + u), CZ + ground_r(u) * math.sin(ALPHA0 + u)))(TAIL_END)
BONES = {
    "snake": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("snake", (0, 0, 3), (0, 0, 0)),
    "tail": ("body", (round(_g[0] * 2) / 2, 1, round(_g[1] * 2) / 2), (0, 0, 0)),
    "neck_1": ("body", (0, 13, -3), (12, 0, 0)),
    "neck_2": ("neck_1", (0, 19, -3), (-8, 0, 0)),
    "neck_3": ("neck_2", (0, 24, -3), (-33, 0, 0)),
    "head": ("neck_3", (0, 28, -3), (22, 0, 0)),
    "jaw": ("head", (0, 26, -6.5), (0, 0, 0)),
    "tongue": ("jaw", (0, 25.5, -12.5), (0, 0, 0)),
}

# For check_clipping.py: (other bone, joint radius px[, deepest fold px]).
JOINTS = {
    "neck_1": [("body", 5.5, 1.5)], "neck_2": [("neck_1", 5, 1.5)],
    "neck_3": [("neck_2", 4.5, 1.5)], "head": [("neck_3", 5.5, 1.5)],
    "jaw": [("head", 5, 1.0)], "tongue": [("jaw", 4), ("head", 4)],
    "tail": [("body", 4, 1.5)],
}


# ---------------------------------------------------------------- painting

def scales(a, b, v):
    """Rows of 2 px scales, each row offset by one, lighter at the top of
    each scale. a runs along the body, b across it (texture pixels)."""
    if b % 2 == 1 and (a + b // 2) % 2 == 0:
        return v + 1
    if b % 2 == 0 and (a + b // 2) % 2 == 1:
        return v - 1 if v > 1 else v
    return v


def saddle(s, lat, period=9.0):
    """Purple diamond saddles down the back: 2 inside, 1 on the dark rim."""
    d = abs((s % period) - period / 2) + abs(lat) * 0.9
    return 2 if d < 2.6 else (1 if d < 3.6 else 0)


def coil_param(x, y, z):
    """(arc length, lateral offset, height above the belly) of a coil point."""
    up = upper_at(x, z)
    if up and y > 6.01:
        a, lat = up
        return S_UP0 + R_UP * a, lat, y - 6
    g = ground_at(x, z)
    if g:
        return ground_s(g[0]), g[1], y
    rho, phi = polar(x, z)
    return 0.0, 0.0, y


def paint_coil(t):
    x, y, z = t.q
    s, lat, hy = coil_param(x, y, z)
    v = t.shade
    if t.f == "down":
        return BELLY[1]
    if t.n[1] > 0.7:                               # the back
        sd = saddle(s, lat)
        if sd == 2:
            return PURPLE[clamp(scales(fi(s), fi(lat * 2), v + (1 if t.edge else 0) - 1), 1)]
        if sd == 1:
            return PURPLE[1]
        return GREEN[clamp(scales(fi(s), fi(lat * 2), v + (1 if t.edge else 0)), 1)]
    # the sides: a pale belly edge, scales, purple blotches between saddles
    if hy < 1:
        return BELLY[clamp(v, 0, 3)]
    if 2 <= hy < 4 and abs(((s + 4.5) % 9) - 4.5) < 1.6:
        return PURPLE[clamp(v, 1)]
    return GREEN[clamp(scales(fi(s), fi(hy), v), 0)]


def paint_neck(t):
    """The neck: a pale scuted belly down the front, saddles down the back,
    scales and blotches on the sides."""
    x, y, z = t.p
    xi, yi = fi(x), fi(y)
    v = t.shade
    if t.f == "north":                             # the belly side
        return BELLY[clamp(v + (0 if yi % 2 else -1), 0, 3)]
    if t.f == "south":
        sd = saddle(y, x)
        if sd:
            return PURPLE[1 if sd == 1 else clamp(v, 1)]
        return GREEN[clamp(scales(yi, xi, v))]
    if t.f in ("west", "east"):
        if abs(((y + 4.5) % 9) - 4.5) < 1.6 and z > -4:
            return PURPLE[clamp(v, 1)]
        if z < -5:
            return BELLY[clamp(v, 0, 3)]           # the belly wraps the front corner
        return GREEN[clamp(scales(yi, fi(z), v))]
    if t.f == "up":
        return GREEN[clamp(v)]
    return BELLY[1]


def paint_head(t):
    """Head: a purple cap with a green rim, pale lips, slit-pupil gold eyes,
    nostrils and heat pits."""
    x, y, z = t.p
    xi, yi, zi = fi(x), fi(y), fi(z)
    v = t.shade
    name = t.e["name"]
    if t.f == "up":
        if abs(x) < 2.5 and z > -12:
            return PURPLE[clamp(scales(zi, xi, v), 1)]
        return GREEN[clamp(v)]
    if t.f == "down":
        return BELLY[1]
    if t.f in ("west", "east"):
        if name == "head" and yi in (28, 29) and -8 <= zi <= -6:
            if zi == -7:
                return GOLD[0]                     # the slit pupil
            return GOLD[3] if yi == 29 else GOLD[2]
        if name == "head" and yi == 30 and -8 <= zi <= -6:
            return GREEN[0]                        # shadow under the brow
        if name == "snout" and yi == 27 and zi == -11:
            return MOUTH[0]                        # heat pit
        if yi == 26:
            return BELLY[clamp(v, 0, 3)]           # pale lip scales
        if name == "head" and yi >= 30:
            return PURPLE[clamp(v, 1)]
        return GREEN[clamp(scales(zi, yi, v))]
    if t.f == "north":
        if name == "nose" and yi == 28 and xi in (-2, 1):
            return MOUTH[0]                        # nostrils
        if yi == 26:
            return BELLY[clamp(v, 0, 3)]
        return GREEN[clamp(v + (1 if yi >= 29 else 0))]
    return GREEN[clamp(v - 1)]


def paint_brow(t):
    v = t.shade
    if t.f == "up":
        return PURPLE[clamp(v + 1, 1)]
    return PURPLE[clamp(v, 1)]


def paint_fang(t):
    v = t.shade
    if fi(t.p[1]) == 24:
        return FANG[0]                             # the tip
    return FANG[clamp(v - 1, 1, 2)]


def paint_jaw(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "up":
        return MOUTH[1] if abs(x) < 2.5 else MOUTH[2]      # inside the mouth
    if t.f == "down":
        return BELLY[2] if fi(z) % 2 else BELLY[1]          # chin scutes
    if fi(y) == 25:
        return BELLY[clamp(v, 0, 3)]
    return GREEN[clamp(v - 1)]


def paint_tongue(t):
    v = t.shade
    return TONGUE[clamp(v - 1, 0, 2)]


PAINTERS = {"coil": paint_coil, "neck": paint_neck, "head": paint_head, "brow": paint_brow,
            "fang": paint_fang, "jaw": paint_jaw, "tongue": paint_tongue}


# ---------------------------------------------------------------- animation

def flick(t0):
    """A tongue flick starting at t0: out, two flutters, back."""
    return [(t0, (0, 0, 0)), (t0 + 0.06, (0, 0, -1.5)), (t0 + 0.2, (0, 0, -1.5)), (t0 + 0.28, (0, 0, 0))]


def flutter(t0):
    return [(t0, (0, 0, 0)), (t0 + 0.08, (14, 0, 0)), (t0 + 0.12, (-10, 0, 0)), (t0 + 0.16, (14, 0, 0)),
            (t0 + 0.2, (-10, 0, 0)), (t0 + 0.28, (0, 0, 0))]


# Rotations are in Blockbench's animation convention (a key is applied as
# -x, -y, +z on top of the rest rotation): a positive x bends a neck bone
# forward and opens the jaw, a positive z sways it to its right.
ANIMATIONS = {
    # Idle: slow breathing in the coil, the neck swaying in a lazy S with the
    # head kept level, the tongue tasting the air, a tail-tip twitch.
    "idle": {"loop": "loop", "length": 3.2, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.6, (1.01, 1.02, 1.01)), (3.2, (1, 1, 1))]),
        "neck_1": sway(3.2, 4, 0.0, 2),
        "neck_2": sway(3.2, 5, 0.12, 2),
        "neck_3": sway(3.2, 5, 0.24, 2),
        "head": sway(3.2, -8, 0.3, 2),
        "tongue": track("position", [(0, (0, 0, 0))] + flick(0.6) + flick(2.2) + [(3.2, (0, 0, 0))])
        + track("rotation", [(0, (0, 0, 0))] + flutter(0.6) + flutter(2.2) + [(3.2, (0, 0, 0))]),
        "tail": rot((0, (0, 0, 0)), (1.2, (0, 0, 0)), (1.25, (0, 5, 0)), (1.3, (0, -5, 0)),
                    (1.35, (0, 5, 0)), (1.4, (0, -5, 0)), (1.45, (0, 0, 0)), (3.2, (0, 0, 0))),
    }},
    # Walk: a gliding sway, the S of the neck rippling from the coil to the
    # head, the tail tip flicking (the coil's turns touch, so it can't sweep).
    "walk": {"loop": "loop", "length": 1.2, "bones": {
        "body": sway(1.2, 3, 0.0, 1),
        "neck_1": sway(1.2, 8, 0.0, 2),
        "neck_2": sway(1.2, 10, 0.15, 2),
        "neck_3": sway(1.2, 10, 0.3, 2),
        "head": sway(1.2, -16, 0.4, 2),
        "tail": sway(1.2, 4, 0.25, 1),
    }},
    # Run: the same glide, faster and lower, the neck drawn forward.
    "run": {"loop": "loop", "length": 0.6, "bones": {
        "body": sway(0.6, 4, 0.0, 1),
        "neck_1": sway(0.6, 9, 0.0, 2, bias=(6, 0, 0)),
        "neck_2": sway(0.6, 11, 0.15, 2, bias=(6, 0, 0)),
        "neck_3": sway(0.6, 11, 0.3, 2),
        "head": sway(0.6, -18, 0.4, 2, bias=(-10, 0, 0)),
        "tail": sway(0.6, 5, 0.25, 1),
        "jaw": rot((0, (6, 0, 0)), (0.6, (6, 0, 0))),
    }},
    # Strike: draw the neck back into a tight S (anticipation), lunge with
    # the jaw wide and the fangs out, hold, pull back.
    "attack": {"loop": "once", "length": 1.0, "bones": {
        "neck_1": rot((0, (0, 0, 0)), (0.35, (-10, 0, 0)), (0.47, (22, 0, 0)), (0.62, (20, 0, 0)),
                      (1.0, (0, 0, 0))),
        "neck_2": rot((0, (0, 0, 0)), (0.35, (-14, 0, 0)), (0.47, (20, 0, 0)), (0.62, (18, 0, 0)),
                      (1.0, (0, 0, 0))),
        "neck_3": rot((0, (0, 0, 0)), (0.35, (-12, 0, 0)), (0.47, (16, 0, 0)), (0.62, (14, 0, 0)),
                      (1.0, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.35, (8, 0, 0)), (0.47, (-22, 0, 0)), (0.62, (-19, 0, 0)),
                    (1.0, (0, 0, 0))),
        "jaw": track("rotation", [(0, (0, 0, 0)), (0.3, (0, 0, 0)), (0.47, (40, 0, 0)),
                                  (0.62, (40, 0, 0)), (0.8, (0, 0, 0)), (1.0, (0, 0, 0))], interp="linear"),
        "body": track("scale", [(0, (1, 1, 1)), (0.35, (1.02, 0.98, 1.02)), (0.47, (0.99, 1.02, 0.99)),
                                (1.0, (1, 1, 1))]),
        "tail": rot((0, (0, 0, 0)), (0.35, (0, 5, 0)), (0.47, (0, -5, 0)), (1.0, (0, 0, 0))),
    }},
    # Hit: a recoil, the neck jerking back and aside, the mouth gaping.
    "hit": {"loop": "once", "length": 0.45, "bones": {
        "neck_1": rot((0, (0, 0, 0)), (0.08, (-8, 0, 6)), (0.25, (2, 0, -2)), (0.45, (0, 0, 0))),
        "neck_2": rot((0, (0, 0, 0)), (0.08, (-8, 0, 8)), (0.25, (2, 0, -2)), (0.45, (0, 0, 0))),
        "neck_3": rot((0, (0, 0, 0)), (0.08, (-6, 0, 6)), (0.45, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.08, (-10, 14, 0)), (0.25, (3, -4, 0)), (0.45, (0, 0, 0))),
        "jaw": track("rotation", [(0, (0, 0, 0)), (0.08, (24, 0, 0)), (0.3, (0, 0, 0)),
                                  (0.45, (0, 0, 0))], interp="linear"),
        "body": track("scale", [(0, (1, 1, 1)), (0.08, (1.03, 0.96, 1.03)), (0.22, (0.99, 1.01, 0.99)),
                                (0.45, (1, 1, 1))]),
        "tail": rot((0, (0, 0, 0)), (0.08, (0, 6, 0)), (0.45, (0, 0, 0))),
    }},
}

# The scales sit one step darker than the other creatures' lighting: green
# lit by the game's sun from above read as pale mint at a step higher.
SNAKE = Creature("snake", ELEMENTS, BONES, PAINTERS, ANIMATIONS,
                 light_bias={"coil": -1, "neck": -1, "head": -1})

if __name__ == "__main__":
    SNAKE.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                preview_scale=7.5, tile=(420, 360), anchor=0.86)
