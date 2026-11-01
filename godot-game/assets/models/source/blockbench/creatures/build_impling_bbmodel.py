"""Build the Blockbench Impling: the green Imp, the player's character, 1.16 m tall (Generic Model).

A voxel rebuild of the game's smooth Imp (game/characters/impling.glb), to the
standard of the other Blockbench creatures. Follows docs/MODELS-BLOCKBENCH.md
and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. The smooth Imp
  is 1.125 m from the soles to the horn tips; at 37 px this one is 1.156 m,
  the height of the scale dummy every other model is built against.
- Proportions measured from the smooth Imp in Blender (vertex bounds per bone,
  joint positions, orthographic renders), then rounded to whole pixels: a
  17 px head on a 10 px body, stubby 6 px legs, arms that hang out at 25
  degrees and reach the hips.
- Box sizes in whole texture pixels. Odd widths for the centred parts (face,
  torso, belly, nose) so the face has a centre column. Round shapes (head,
  torso) are a core box with a 1 px slab on each side, so they read round from
  every angle and no two boxes share a face.
- Per-face UV, one texture, hidden faces removed except where an animation
  opens them up (the joints).
- Lit from the top, slightly front-left; hue-shifted ramps (green shadows lean
  teal, highlights lean yellow), edge highlights on lit edges, painted shadow
  where parts meet. Colours sampled from the smooth Imp's texture: skin
  #47a338, the darker cap over the crown #357d29, purple eyes #9746a1, ivory
  horns. The purple eyes are the accent, the most saturated colour.
- The face is the smooth Imp's: the darker cap comes down to a V between the
  brows, heavy angry brows meet in a furrow, pale eyes with big purple irises
  half under the lids, a small nose, a little frown.
- Shape: bull horns that sweep out and then up, long pointed ears that fan
  out sideways, a round belly with a navel, four-fingered hands (thumb,
  index, a longer middle finger, pinky), round feet, and a thin devil's tail
  that curls up behind into an ivory spade.

Rig, for the player: walk, sprint, jump, hold a tool or weapon in either hand,
and wear clothing or armour later.
- impling > body (hips) > chest > head > horn_*, ear_*; chest > arm_* >
  forearm_* > hand_* > fingers_*, item_*; chest > back; body > tail >
  tail_mid > tail_end; body > thigh_* > leg_* > foot_*.
- item_right / item_left: empty bones at the centre of each closed fist, where
  a held tool or weapon attaches. back: an empty bone between the shoulder
  blades for a backpack, cape or a back item (the NFT "Back" trait).
- Clothing and armour: each piece is a box (or an Inflated copy of a body box)
  parented to the bone it covers: helmets to head, chest pieces to chest,
  belts and kilts to body, sleeves and gauntlets to arm_*/forearm_*/hand_*,
  boots to leg_*/foot_*. The bones are cut where clothing is cut.
- The fingers curl as one bone (fingers_* z) to grip; the legs are three
  bones so the knees bend, and the walk, sprint and landing are solved with
  two-bone IK (bbrig.py) so the feet stay planted on the ground.

Animations: idle, walk, sprint, jump, fall, land, hold_right, hold_left,
attack (a slash), swing (a tool chop), hit. hold_* only move that arm, so a
game can play them on top of the walk or sprint.

Usage: python build_impling_bbmodel.py [out_dir]   (writes impling.bbmodel,
impling.png, impling_preview.png and impling_silhouette.png)
Clip check (Blockbench running with --remote-debugging-port=9333):
    python check_clipping.py impling.bbmodel --spec build_impling_bbmodel.py
"""

import math
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from bbcreature import NORMAL, clamp, el, fi, hexrgb, mirror, ramp, rot, tangents, track  # noqa: E402
from bbrig import RigCreature, sampled, solve_legs, stride  # noqa: E402

# Ramps, darkest first. Shadows lean teal, highlights lean yellow.
SKIN = ramp("#1b4a42", "#29723a", "#43a13b", "#5cba47", "#8cd468")
CAP = ramp("#163a36", "#21582f", "#357d29", "#489532", "#6aaf47")      # the darker crown
HORN = ramp("#5c4f47", "#958676", "#c6b9a5", "#e2d8c5", "#f6efe1")
SCLERA = ramp("#b8a6b3", "#e3d8db", "#f8f2ef")
IRIS = ramp("#2c1339", "#5c2a7b", "#9746a1", "#c47cd4")               # the accent
PUPIL = hexrgb("#170c1d")
GLINT = hexrgb("#fffaf3")
LID = hexrgb("#183d2f")
MOUTH = ramp("#1a1016", "#3d2229")


# ---------------------------------------------------------------- geometry

def layer(name, bone, part, y0, y1, hx, zf, zb, cut):
    """A horizontal slice of a round shape: hx either side of the centre, from
    zf (front) to zb (back), its four vertical edges cut back in cut 1 px
    steps. Boxes never overlap, so no two share a face."""
    out = [el(name, bone, part, (-hx, y0, zf + cut), (hx, y1, zb - cut))]
    for k in range(1, cut + 1):
        out.append(el(f"{name}_f{k}", bone, part, (-(hx - k), y0, zf + cut - k), (hx - k, y1, zf + cut - k + 1)))
        out.append(el(f"{name}_b{k}", bone, part, (-(hx - k), y0, zb - cut + k - 1), (hx - k, y1, zb - cut + k)))
    return out


def segment(name, bone, part, base, angle, length, width, z):
    """A horn segment: a box standing on base (x, y), turned angle degrees
    out from upright (to +x), reaching 1 px back into the segment before it
    so the bend has no notch. Returns the box and where it ends."""
    x, y = base
    a = math.radians(angle)
    box = el(name, bone, part, (x - width / 2, y - 1, z[0]), (x + width / 2, y + length, z[1]),
             rot=(0, 0, -angle), origin=(x, y, (z[0] + z[1]) / 2))
    return box, (x + length * math.sin(a), y + length * math.cos(a))


def horn():
    """The right horn as a crescent: out from the head, bending up, the tip
    leaning back in. Each segment is narrower and sits 0.5 px off the last in
    depth, so no two faces share a plane."""
    out, at = [], (7, 28)
    for name, angle, length, width, z in (("base", 62, 3, 4, (-4.5, -1.5)), ("out", 32, 3, 3, (-4, -2)),
                                          ("up", -4, 2, 3, (-4.5, -2.5)), ("tip", -18, 2, 2, (-4, -3)),
                                          ("point", -28, 1, 1, (-3.5, -2.5))):
        box, at = segment(f"horn_*_{name}", "horn_*", "horn", at, angle, length, width, z)
        out.append(box)
    return out


ELEMENTS = [
    # Hips: a round belly pushing forward, a round rump, a crotch between the
    # legs. Chest: as wide, shallower. Shoulders slope in to the neck.
    *layer("pelvis", "body", "skin", 5, 10, 5.5, -5.5, 4.5, 1),
    el("crotch", "body", "skin", (-0.5, 4, -3.5), (0.5, 5, 2.5)),
    *layer("chest", "chest", "skin", 10, 14, 4.5, -4.5, 3.5, 1),
    *layer("shoulders", "chest", "skin", 14, 15, 3.5, -3.5, 2.5, 1),
    # Head: a ball 17 wide, 18 tall, 17 deep, widest at the eyes, in seven
    # layers. The face is the front of the jaw and skull layers, 13 wide.
    *layer("chin", "head", "head", 15, 16, 4.5, -6.5, 4.5, 1),
    *layer("jaw", "head", "head", 16, 20, 7.5, -8.5, 6.5, 1),
    *layer("skull", "head", "head", 20, 27, 8.5, -8.5, 8.5, 2),
    *layer("forehead", "head", "head", 27, 30, 7.5, -7.5, 7.5, 2),
    *layer("head_top", "head", "head", 30, 31, 6.5, -6.5, 6.5, 2),
    *layer("crown", "head", "head", 31, 32, 5.5, -5.5, 5.5, 2),
    *layer("crown_top", "head", "head", 32, 33, 3.5, -3.5, 3.5, 1),
    # Brows: an angry V in three steps, the inner end lowest, a furrow
    # between. The outer step reaches back past the face's edge.
    *mirror("brow_*_inner", "head", "brow", (0.5, 22, -9.5), (2.5, 23, -8.5)),
    *mirror("brow_*_mid", "head", "brow", (2.5, 23, -9.5), (4.5, 24, -8.5)),
    *mirror("brow_*_outer", "head", "brow", (4.5, 24, -9.5), (7.5, 25, -7.5)),
    el("nose", "head", "nose", (-0.5, 18, -9.5), (0.5, 20, -8.5)),
    # Bull horns from the upper sides of the head: out, then up, the tips
    # leaning back in.
    *[b for h in horn() for b in mirror(h["name"], h["bone"], h["part"], h["lo"], h["hi"],
                                         h["rot"], h["origin"])],
    # Ears: long and pointed, fanning out sideways with a flat top edge, the
    # inner ear facing forward.
    *mirror("ear_*_root", "ear_*", "ear", (7.5, 20.5, -1), (10.5, 26.5, 1)),
    *mirror("ear_*_mid", "ear_*", "ear", (10.5, 22.5, -0.5), (12.5, 26.5, 0.5)),
    *mirror("ear_*_end", "ear_*", "ear", (12.5, 24.5, -0.5), (13.5, 26.5, 0.5)),
    *mirror("ear_*_tip", "ear_*", "ear", (13.5, 25.5, -0.5), (14.5, 26.5, 0.5)),
    # Arms, modelled straight down and hung out 25 degrees at the shoulder.
    # Each segment sits half a pixel off the next, so no two share a side
    # plane when a joint bends.
    *mirror("upper_arm_*", "arm_*", "skin", (4.5, 10.5, -2), (8.5, 13.5, 2)),
    *mirror("forearm_*", "forearm_*", "skin", (5, 8, -2.5), (9, 11, 1.5)),
    *mirror("palm_*", "hand_*", "hand", (5.5, 6, -3), (8.5, 8, 2)),
    *mirror("thumb_*", "hand_*", "hand", (5.5, 5, -4), (7.5, 7, -3)),
    *mirror("finger_index_*", "fingers_*", "finger", (6, 4, -2.5), (8, 6, -1.5)),
    *mirror("finger_middle_*", "fingers_*", "finger", (6, 3, -1), (8, 6, 0)),
    *mirror("finger_pinky_*", "fingers_*", "finger", (6, 4, 0.5), (8, 6, 1.5)),
    # Legs: the thigh mostly inside the hips (it swings out from under the
    # belly), a slimmer shin, a round foot.
    *mirror("thigh_*", "thigh_*", "skin", (1, 4, -2.5), (5, 8, 1.5)),
    *mirror("shin_*", "leg_*", "skin", (1.5, 2, -2), (4.5, 4, 1)),
    *mirror("foot_*", "foot_*", "foot", (0.5, 0, -3.5), (5.5, 2, 1.5)),
    *mirror("toes_*", "foot_*", "foot", (1, 0, -4.5), (5, 1, -3.5)),
    # Tail: modelled straight back, bent at rest into a curl that rises behind
    # the Imp, ending in an ivory spade.
    el("tail_root", "tail", "tail", (-1, 5.5, 3.5), (1, 7.5, 8.5)),
    el("tail_mid", "tail_mid", "tail", (-0.5, 6, 8.5), (0.5, 7, 13.5)),
    el("tail_end", "tail_end", "tail", (-0.5, 6, 13.5), (0.5, 7, 18.5)),
    el("spade", "tail_end", "spade", (-1, 5, 18.5), (1, 8, 19.5)),
    el("spade_tip", "tail_end", "spade", (-0.5, 6, 19.5), (0.5, 7, 20.5)),
]

# Faces an animation opens up although they are covered at rest: the ends of
# limb segments at the joints, the thighs inside the hips, the chin on the
# shoulders.
KEEP = {
    "thigh": ("north", "south", "east", "west", "up", "down"),
    "ear_right_root": ("west",),
    "ear_left_root": ("east",),
    "shin": ("up",),
    "upper_arm": ("down", "west"),
    "forearm": ("up", "down"),
    "palm": ("up",),
    "finger": ("up",),
    "chin": ("down",),
    "shoulders": ("up",),
    "tail_mid": ("north",),
    "tail_end": ("north",),
}
for e in ELEMENTS:
    for prefix, faces in KEEP.items():
        if e["name"].startswith(prefix):
            e["keep"] = faces

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "impling": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("impling", (0, 7, -0.5), (0, 0, 0)),
    "chest": ("body", (0, 10, -0.5), (0, 0, 0)),
    "head": ("chest", (0, 15, -0.5), (0, 0, 0)),
    "horn_right": ("head", (8, 29, -3), (0, 0, 0)),
    "horn_left": ("head", (-8, 29, -3), (0, 0, 0)),
    "ear_right": ("head", (8.5, 24, 0), (0, -25, 12)),     # swept back and up, the inner
    "ear_left": ("head", (-8.5, 24, 0), (0, 25, -12)),     # ear turned forward and out
    "arm_right": ("chest", (6.5, 13.5, -0.5), (0, 0, 25)),
    "forearm_right": ("arm_right", (6.5, 11, -0.5), (0, 0, 0)),
    "hand_right": ("forearm_right", (6.5, 8, -0.5), (0, 0, 0)),
    "fingers_right": ("hand_right", (6.5, 6, -0.5), (0, 0, 0)),
    "item_right": ("hand_right", (6.5, 4.5, -0.5), (0, 0, 0)),
    "arm_left": ("chest", (-6.5, 13.5, -0.5), (0, 0, -25)),
    "forearm_left": ("arm_left", (-6.5, 11, -0.5), (0, 0, 0)),
    "hand_left": ("forearm_left", (-6.5, 8, -0.5), (0, 0, 0)),
    "fingers_left": ("hand_left", (-6.5, 6, -0.5), (0, 0, 0)),
    "item_left": ("hand_left", (-6.5, 4.5, -0.5), (0, 0, 0)),
    "back": ("chest", (0, 12, 3), (0, 0, 0)),
    "tail": ("body", (0, 6.5, 4), (8, 0, 0)),
    "tail_mid": ("tail", (0, 6.5, 8.5), (-40, 0, 0)),
    "tail_end": ("tail_mid", (0, 6.5, 13.5), (-45, 0, 0)),
    "thigh_right": ("body", (3, 7, -0.5), (0, 0, 0)),
    "leg_right": ("thigh_right", (3, 4, -0.5), (0, 0, 0)),
    "foot_right": ("leg_right", (3, 2, -0.5), (0, 0, 0)),
    "thigh_left": ("body", (-3, 7, -0.5), (0, 0, 0)),
    "leg_left": ("thigh_left", (-3, 4, -0.5), (0, 0, 0)),
    "foot_left": ("leg_left", (-3, 2, -0.5), (0, 0, 0)),
}

# For check_clipping.py: the thighs swing inside the hips, the head sits on
# the shoulders, the arms hang against the chest, the waist twists, the ears
# turn in their sockets, and the knees, ankles, elbows, wrists and knuckles
# fold within their own width. (bone, px) or (bone, px, deepest fold in px).
JOINTS = {
    "head": [("chest", 6, 1.0)],
    "chest": [("body", 7, 1.0)],
    "tail": [("body", 2)],
}
for _s in ("right", "left"):
    JOINTS.update({
        f"thigh_{_s}": [("body", 4.5, 1.5)],      # tucks under the belly in a crouch
        f"leg_{_s}": [(f"thigh_{_s}", 3), ("body", 3, 1.0)],   # the knee under the belly
        f"foot_{_s}": [(f"leg_{_s}", 3)],
        f"arm_{_s}": [("chest", 3.5, 1.0)],
        f"forearm_{_s}": [(f"arm_{_s}", 3)],
        f"hand_{_s}": [(f"forearm_{_s}", 2.5)],
        f"fingers_{_s}": [(f"hand_{_s}", 3)],
        f"ear_{_s}": [("head", 4, 1.2)],
    })


# ---------------------------------------------------------------- painting

def col(x):
    """Texture column of a texel centre on a front or back face (0 is the
    centre column)."""
    return round(x)


def on_face(t):
    """The texel is on the front plane of the head (the face and muzzle)."""
    return t.f == "north" and abs(t.p[2] + 8.5) < 1e-6


def cap_line(t):
    """Height where the darker cap starts on this texel's face: a V down to
    the brows on the face, level over the ears, lower at the back."""
    x, y, z = t.p
    if t.f == "north":
        return 25 + abs(x) / 3 if on_face(t) else 27
    if t.f in ("west", "east"):
        return 26 - z / 7
    if t.f == "south":
        return 25
    return -1 if t.f == "up" else 99


def eye(c, r):
    """The eye texel at column c, row r, or None. Each eye is 5 x 3: pale
    sclera, a 3 px purple iris under an angry lid at the inner corner, a dark
    pupil, a glint up and to the light (+x, the same side on both eyes)."""
    u = abs(c) - 2
    if not (0 <= u <= 4 and 19 <= r <= 21):
        return None
    pupil = 4 if c > 0 else -4
    if r == 21 and c == pupil + 1:
        return GLINT
    if r == 21:
        return (LID, IRIS[0], IRIS[0], IRIS[0], SCLERA[0])[u]
    if r == 20:
        return (SCLERA[2], IRIS[2], PUPIL, IRIS[2], SCLERA[2])[u]
    return (SCLERA[1], IRIS[1], IRIS[2], IRIS[1], SCLERA[1])[u]


def round_light(t, centre, radii):
    """Light from the normal of the smooth shape a stack of layers stands for
    (the same top, front-left light as bbcreature), so the shading follows
    the ball, not the steps. Painted contact shadow still applies."""
    n = np.array([(t.q[k] - centre[k]) / radii[k] ** 2 for k in range(3)])
    n /= max(float(np.linalg.norm(n)), 1e-6)
    v = math.floor(2.3 + 1.6 * n[1] - 0.6 * n[2] - 0.6 * n[0])
    return clamp(v) - (1 if t.contact else 0)


def tube_light(t, axis=1):
    """Light for a limb segment from the normal of the round tube it stands
    for (along its own long axis: y for the limbs, z for the tail), so arms
    and legs read round and the joins between segments don't show as
    stripes. The ends keep their face normal."""
    if NORMAL[t.f][axis]:
        n = np.asarray(t.n, float)
    else:
        lo, hi = t.e["lo"], t.e["hi"]
        d = [t.p[k] - (lo[k] + hi[k]) / 2 for k in range(3)]
        d[axis] = 0.0
        n = t.e["M"][:3, :3] @ np.array(d, float)
        n = n / max(float(np.linalg.norm(n)), 1e-6)
    v = math.floor(2.3 + 1.6 * n[1] - 0.6 * n[2] - 0.6 * n[0])
    return clamp(v) - (1 if t.contact else 0)


# The shapes the light follows: taller than the boxes, so the face and belly
# stay evenly lit from the front and only the crown and shoulders turn up to
# the light.
HEAD_BALL = ((0, 24, 0), (8.5, 13, 8.5))
BODY_BEAN = ((0, 9.5, -0.5), (5.5, 9, 5))


def paint_head(t):
    x, y, z = t.p
    c, r = col(x), fi(y)
    v = round_light(t, *HEAD_BALL)
    name = t.e["name"]
    if t.f == "down":
        return SKIN[0] if name.startswith("chin") else SKIN[1]
    if on_face(t):
        e = eye(c, r)
        if e is not None:
            return e
        if r == 18 and 3 <= abs(c) <= 5:
            v -= 1                                 # lower lids
        if r == 17 and 3 <= abs(c) <= 5:
            v += 1                                 # the cheeks catch the light
        if r == 17 and abs(c) <= 1:
            return MOUTH[0] if c == 0 else MOUTH[1]    # the little frown
        if r == 16 and abs(c) == 2:
            v -= 1                                 # its corners turn down
        if r == 16 and abs(c) <= 1:
            v += 1                                 # lower lip and chin
        if c == 0 and r in (22, 23):
            return SKIN[clamp(v - 2)]              # the furrow between the brows
    if name.startswith("chin") and t.f == "north":
        v -= 1
    if y >= cap_line(t):
        return CAP[clamp(v)]
    return SKIN[clamp(v)]


def paint_brow(t):
    x, y, z = t.p
    v = round_light(t, *HEAD_BALL)
    if t.f == "down":
        return SKIN[0]
    if t.f == "north" and t.e["name"].endswith("_inner") and abs(col(x)) == 1:
        v -= 1                                     # the brows knit at the furrow
    return SKIN[clamp(v)]


def paint_nose(t):
    v = t.shade
    if t.f == "down":
        return MOUTH[1]                            # nostrils
    if t.f == "north" and fi(t.p[1]) == 19:
        v += 1
    return SKIN[clamp(v)]


EAR_LOW = {"root": 21, "mid": 23, "end": 25, "tip": 26}    # bottom row of each ear box


def paint_ear(t):
    """Front: a dark inner ear inside a lit rim (the flat top edge and the
    stepped lower edge), deepest at the root."""
    x, y, z = t.p
    r = fi(y)
    ax = abs(x)
    v = t.shade
    part = t.e["name"].rsplit("_", 1)[1]
    if t.f == "north":
        if r == 26 or part in ("end", "tip") or r == EAR_LOW[part]:
            return SKIN[clamp(v + 1)]              # the rim
        if part == "root" and r in (23, 24) and ax < 9.5:
            return SKIN[0]                         # the ear canal
        if part == "root" and ax < 9.5 or r == 24:
            return SKIN[1]                         # the fold
        return SKIN[2]
    if t.f == "down":
        return SKIN[1]
    return SKIN[clamp(v)]


def paint_horn(t):
    """Ivory: stained and ringed at the root, a ring at the bend, cleaner and
    brighter toward the tip."""
    name = t.e["name"]
    along = t.p[1] - t.e["origin"][1]              # px from where the segment starts
    v = t.shade
    if name.endswith("_base"):
        v -= 1 if along < 1.5 else 0               # the root is darker
        if 1.5 <= along < 2.5 and t.f in ("north", "south"):
            v -= 1                                 # a growth ring
    if name.endswith("_out") and 1 <= along < 2 and t.f in ("north", "south"):
        v -= 1                                     # a ring at the bend
    if name.endswith(("_tip", "_point")):
        v += 1
    return HORN[clamp(v)]


def paint_skin(t):
    """Torso, arms and legs: form light, the navel, the spine and shoulder
    blades on the back, knees and elbows."""
    x, y, z = t.p
    c, r = col(x), fi(y)
    name = t.e["name"]
    torso = name.startswith(("pelvis", "chest", "shoulders", "crotch"))
    v = round_light(t, *BODY_BEAN) if torso else tube_light(t)
    if t.f == "down":
        return SKIN[0] if name.startswith(("crotch", "pelvis")) else SKIN[1]
    if name == "pelvis_f1" and t.f == "north":     # the belly
        if c == 0 and r == 7:
            return SKIN[0]                         # navel
        if c == 0 and r == 8:
            v += 1                                 # lit above it
    if name.startswith("pelvis") and t.f in ("east", "west") and r == 5:
        v -= 1                                     # the hips turn under
    if name.startswith(("chest", "pelvis")) and t.f == "south":
        if c == 0 and 6 <= r <= 13:
            v -= 1                                 # spine
        if name.startswith("chest") and r in (12, 13) and 2 <= abs(c) <= 3:
            v += 1                                 # shoulder blades
    if name.startswith("shin_") and t.f == "north" and r == 3:
        v += 1                                     # knees
    return SKIN[clamp(v)]


def paint_hand(t):
    """Palm and thumb: the palm (inner side) a shade darker, a crease where
    the thumb joins."""
    x, y, z = t.p
    v = tube_light(t)
    inner = (t.f == "west" and x > 0) or (t.f == "east" and x < 0)
    if inner:
        v -= 1
    if t.f == "down":
        return SKIN[1]
    return SKIN[clamp(v)]


def paint_finger(t):
    v = tube_light(t)
    if t.f == "down":
        return SKIN[1]                             # fingertips turn under
    return SKIN[clamp(v)]


def paint_foot(t):
    x, y, z = t.p
    v = t.shade
    if t.f == "down":
        return SKIN[0]
    if t.e["name"].startswith("toes_") and t.f == "north":
        v += 1                                     # round toes catch the light
    return SKIN[clamp(v)]


def paint_tail(t):
    v = tube_light(t, axis=2)
    if t.f == "down":
        return SKIN[1]
    return SKIN[clamp(v)]


def paint_spade(t):
    v = t.shade
    if t.e["name"] == "spade_tip":
        v += 1
    return HORN[clamp(v)]


PAINTERS = {"head": paint_head, "brow": paint_brow, "nose": paint_nose, "ear": paint_ear,
            "horn": paint_horn, "skin": paint_skin, "hand": paint_hand, "finger": paint_finger,
            "foot": paint_foot, "tail": paint_tail, "spade": paint_spade}


# ---------------------------------------------------------------- animation

# Rotations are in Blockbench's animation convention (bbrig.py): a positive x
# pitches the body and head forward, swings a hanging arm or leg backward,
# bends a knee, lifts the tail; a negative x raises an arm forward and bends
# the elbow. A negative z curls the right hand's fingers (positive the
# left's); a positive z lifts the right ear and swings the right arm out.

def cyc(length, fn, n=8):
    """A smooth looping track of rotation keys every 1/n of the cycle, from
    fn(phase) with phase in 0..1."""
    return rot(*[(round(length * k / n, 4), tuple(round(c, 2) for c in fn(k / n))) for k in range(n + 1)])


def s(p):
    return math.sin(2 * math.pi * p)


def co(p):
    return math.cos(2 * math.pi * p)


LEGS = [("right", 3), ("left", -3)]
ANKLE = (2, -0.5)                                  # rest pivot of each foot, (y, z) px


def legs_ik(length, specs, body_rot, body_pos):
    """Solve both legs every frame (knees forward) under the body's motion,
    and key the body itself every frame to match."""
    legs = [(f"thigh_{s_}", f"leg_{s_}", f"foot_{s_}", -1, specs[s_]) for s_, _ in LEGS]
    out = solve_legs(BONES, length, legs, rot={"body": body_rot}, pos={"body": body_pos})
    out["body"] = sampled("rotation", length, body_rot) + sampled("position", length, body_pos)
    return out


def planted(t):
    return ("plant", ANKLE, 0)


def ease(keys):
    """A function of time through (t, value) keys, smoothstep between them."""
    def f(t):
        if t <= keys[0][0]:
            return keys[0][1]
        for (t0, v0), (t1, v1) in zip(keys, keys[1:]):
            if t <= t1:
                u = (t - t0) / (t1 - t0)
                u = u * u * (3 - 2 * u)
                if isinstance(v0, tuple):
                    return tuple(a + (b - a) * u for a, b in zip(v0, v1))
                return v0 + (v1 - v0) * u
        return keys[-1][1]
    return f


# The air pose (end of jump, all of fall, start of land): legs tucked, arms up
# and out, ears up, tail curled. Legs as world pitches (thigh, shin, foot), in
# the maths convention bbrig's "free" legs take (positive swings forward).
AIR_LEGS = (22, -28, -8)
AIR_LIFT = 1.5          # px the body rides up in the air pose, so pointed toes clear the ground
AIR = {
    "arm_right": (-35, 0, 30), "forearm_right": (-35, 0, 0), "fingers_right": (0, 0, -20),
    "chest": (-4, 0, 0), "head": (-6, 0, 0), "ear_right": (0, 0, 14),
    "tail": (14, 0, 0), "tail_mid": (-10, 0, 0), "tail_end": (-10, 0, 0),
}


def air_keys(t):
    """AIR as {bone: [(t, key)]}, mirrored to the left."""
    out = {}
    for b, (x, y, z) in AIR.items():
        out.setdefault(b, []).append((t, (x, y, z)))
        if "right" in b:
            out.setdefault(b.replace("right", "left"), []).append((t, (x, -y, -z)))
    return out


def merge(*tracks):
    """Concatenate rotation keys per bone from several {bone: [(t, key)]}."""
    out = {}
    for tr in tracks:
        for b, ks in tr.items():
            out.setdefault(b, []).extend(ks)
    return {b: rot(*sorted(ks)) for b, ks in out.items()}


def walk():
    L = 0.8

    def body_rot(t):
        p = t / L
        return (3, 4 * s(p), -2 * s(p))

    def body_pos(t):
        return (0, -0.7 + 0.3 * s(t / L) ** 2, 0)

    specs = {"right": stride(L, 0.0, ANKLE, 1.5, 1.0, 0.55, 10),
             "left": stride(L, 0.5, ANKLE, 1.5, 1.0, 0.55, 10)}
    out = legs_ik(L, specs, body_rot, body_pos)
    out.update({
        "chest": cyc(L, lambda p: (1, -6 * s(p), 2 * s(p))),
        "head": cyc(L, lambda p: (2 * s(2 * p), 3 * s(p), -1.5 * s(p))),
        "arm_right": cyc(L, lambda p: (18 * co(p), 0, 0)),
        "arm_left": cyc(L, lambda p: (-18 * co(p), 0, 0)),
        "forearm_right": cyc(L, lambda p: (-14 - 8 * max(0.0, -co(p)), 0, 0)),
        "forearm_left": cyc(L, lambda p: (-14 - 8 * max(0.0, co(p)), 0, 0)),
        "fingers_right": cyc(L, lambda p: (0, 0, -15)),
        "fingers_left": cyc(L, lambda p: (0, 0, 15)),
        "ear_right": cyc(L, lambda p: (0, 0, 5 * s(2 * p - 0.15))),
        "ear_left": cyc(L, lambda p: (0, 0, -5 * s(2 * p - 0.15))),
        "tail": cyc(L, lambda p: (0, 12 * s(p - 0.1), 0)),
        "tail_mid": cyc(L, lambda p: (0, 14 * s(p - 0.22), 0)),
        "tail_end": cyc(L, lambda p: (0, 16 * s(p - 0.34), 0)),
    })
    return {"loop": "loop", "length": L, "bones": out}


def sprint():
    L = 0.5

    def body_rot(t):
        p = t / L
        return (4, 6 * s(p), -3 * s(p))            # the chest leans; the belly stays over the knees

    def body_pos(t):
        return (0, -0.9 + 0.5 * s(t / L) ** 2, 0)

    specs = {"right": stride(L, 0.0, ANKLE, 1.3, 0.7, 0.42, 20),
             "left": stride(L, 0.5, ANKLE, 1.3, 0.7, 0.42, 20)}
    out = legs_ik(L, specs, body_rot, body_pos)
    out.update({
        "chest": cyc(L, lambda p: (12, -9 * s(p), 2 * s(p))),
        "head": cyc(L, lambda p: (-14 + 2 * s(2 * p), 4 * s(p), 0)),
        "arm_right": cyc(L, lambda p: (-5 + 28 * co(p), 0, 10)),     # pumps further forward than back
        "arm_left": cyc(L, lambda p: (-5 - 28 * co(p), 0, -10)),
        "forearm_right": cyc(L, lambda p: (-50 - 10 * max(0.0, -co(p)), 0, 0)),
        "forearm_left": cyc(L, lambda p: (-50 - 10 * max(0.0, co(p)), 0, 0)),
        "fingers_right": cyc(L, lambda p: (0, 0, -75)),
        "fingers_left": cyc(L, lambda p: (0, 0, 75)),
        "ear_right": cyc(L, lambda p: (0, 22, -6 + 3 * s(2 * p))),
        "ear_left": cyc(L, lambda p: (0, -22, 6 - 3 * s(2 * p))),
        "tail": cyc(L, lambda p: (10, 8 * s(p - 0.1), 0)),
        "tail_mid": cyc(L, lambda p: (-28, 10 * s(p - 0.25), 0)),
        "tail_end": cyc(L, lambda p: (-30, 12 * s(p - 0.4), 0)),
    })
    return {"loop": "loop", "length": L, "bones": out}


def jump():
    """Crouch (anticipation), spring up with the arms thrown forward, tuck into
    the air pose. Ends on fall's first frame."""
    L = 0.5
    body_rot = ease([(0, (0, 0, 0)), (0.15, (5, 0, 0)), (0.25, (-6, 0, 0)), (0.4, (0, 0, 0)),
                     (L, (0, 0, 0))])
    body_pos = ease([(0, (0, 0, 0)), (0.15, (0, -0.9, 0)), (0.25, (0, 1.7, 0)), (0.4, (0, 1.8, 0)),
                     (L, (0, AIR_LIFT, 0))])
    tuck = ease([(0.25, (8, 8, -30)), (0.4, AIR_LEGS)])

    def spec(t):
        if t <= 0.22:
            return planted(t)
        return ("free", tuck(t))
    out = legs_ik(L, {"right": spec, "left": spec}, body_rot, body_pos)
    air = air_keys(L)
    out.update(merge(
        {"arm_right": [(0, (0, 0, 0)), (0.15, (26, 0, 14)), (0.25, (-60, 0, 25))],
         "forearm_right": [(0, (0, 0, 0)), (0.15, (-10, 0, 0)), (0.25, (-20, 0, 0))],
         "fingers_right": [(0, (0, 0, 0)), (0.25, (0, 0, -10))],
         "arm_left": [(0, (0, 0, 0)), (0.15, (26, 0, -14)), (0.25, (-60, 0, -25))],
         "forearm_left": [(0, (0, 0, 0)), (0.15, (-10, 0, 0)), (0.25, (-20, 0, 0))],
         "fingers_left": [(0, (0, 0, 0)), (0.25, (0, 0, 10))],
         "chest": [(0, (0, 0, 0)), (0.15, (12, 0, 0)), (0.25, (-6, 0, 0))],
         "head": [(0, (0, 0, 0)), (0.15, (-8, 0, 0)), (0.25, (-10, 0, 0))],
         "ear_right": [(0, (0, 0, 0)), (0.15, (0, 0, -12)), (0.25, (0, 0, 18))],
         "ear_left": [(0, (0, 0, 0)), (0.15, (0, 0, 12)), (0.25, (0, 0, -18))],
         "tail": [(0, (0, 0, 0)), (0.15, (-10, 0, 0)), (0.25, (20, 0, 0))],
         "tail_mid": [(0, (0, 0, 0)), (0.25, (-14, 0, 0))],
         "tail_end": [(0, (0, 0, 0)), (0.25, (-14, 0, 0))]},
        air))
    return {"loop": "once", "length": L, "bones": out}


def fall():
    """In the air: the air pose, arms paddling, legs kicking a little."""
    L = 0.6
    a = AIR

    def leg(sign):
        def spec(t):
            p = t / L
            th, sh, ft = AIR_LEGS
            return ("free", (th + 6 * sign * s(p), sh - 6 * sign * s(p), ft))
        return spec
    out = legs_ik(L, {"right": leg(1), "left": leg(-1)}, lambda t: (0, 0, 0), lambda t: (0, AIR_LIFT, 0))
    out.update({
        "arm_right": cyc(L, lambda p: (a["arm_right"][0] + 8 * s(p), 0, a["arm_right"][2] + 6 * s(p))),
        "arm_left": cyc(L, lambda p: (a["arm_right"][0] - 8 * s(p), 0, -a["arm_right"][2] - 6 * s(p))),
        "forearm_right": cyc(L, lambda p: a["forearm_right"]),
        "forearm_left": cyc(L, lambda p: a["forearm_right"]),
        "fingers_right": cyc(L, lambda p: a["fingers_right"]),
        "fingers_left": cyc(L, lambda p: (0, 0, -a["fingers_right"][2])),
        "chest": cyc(L, lambda p: a["chest"]),
        "head": cyc(L, lambda p: (a["head"][0] + 2 * s(p), 0, 0)),
        "ear_right": cyc(L, lambda p: (0, 0, a["ear_right"][2] + 6 * s(p))),
        "ear_left": cyc(L, lambda p: (0, 0, -a["ear_right"][2] - 6 * s(p))),
        "tail": cyc(L, lambda p: (a["tail"][0] + 5 * s(p), 0, 0)),
        "tail_mid": cyc(L, lambda p: (a["tail_mid"][0] + 6 * s(p - 0.15), 0, 0)),
        "tail_end": cyc(L, lambda p: (a["tail_end"][0] + 8 * s(p - 0.3), 0, 0)),
    })
    return {"loop": "loop", "length": L, "bones": out}


def land():
    """From the air pose: feet reach down, a squashed crouch on impact, a
    small rebound, back to rest."""
    L = 0.5
    body_rot = ease([(0, (0, 0, 0)), (0.06, (0, 0, 0)), (0.14, (5, 0, 0)), (0.3, (-3, 0, 0)),
                     (L, (0, 0, 0))])
    body_pos = ease([(0, (0, AIR_LIFT, 0)), (0.06, (0, 0, 0)), (0.14, (0, -1.0, 0)), (0.3, (0, 0.2, 0)),
                     (L, (0, 0, 0))])
    reach = ease([(0, AIR_LEGS), (0.06, (0, 0, 0))])

    def spec(t):
        if t < 0.06:
            return ("free", reach(t))
        return planted(t)
    out = legs_ik(L, {"right": spec, "left": spec}, body_rot, body_pos)
    out.update(merge(
        air_keys(0),
        {"arm_right": [(0.14, (10, 0, 22)), (0.3, (-4, 0, 0)), (L, (0, 0, 0))],
         "forearm_right": [(0.14, (-20, 0, 0)), (L, (0, 0, 0))],
         "fingers_right": [(0.14, (0, 0, -10)), (L, (0, 0, 0))],
         "arm_left": [(0.14, (10, 0, -22)), (0.3, (-4, 0, 0)), (L, (0, 0, 0))],
         "forearm_left": [(0.14, (-20, 0, 0)), (L, (0, 0, 0))],
         "fingers_left": [(0.14, (0, 0, 10)), (L, (0, 0, 0))],
         "chest": [(0.14, (12, 0, 0)), (0.3, (-3, 0, 0)), (L, (0, 0, 0))],
         "head": [(0.14, (-8, 0, 0)), (0.3, (-2, 0, 0)), (L, (0, 0, 0))],   # stays looking ahead
         "ear_right": [(0.14, (0, 0, -16)), (0.3, (0, 0, 6)), (L, (0, 0, 0))],
         "ear_left": [(0.14, (0, 0, 16)), (0.3, (0, 0, -6)), (L, (0, 0, 0))],
         "tail": [(0.14, (-12, 0, 0)), (0.3, (6, 0, 0)), (L, (0, 0, 0))],
         "tail_mid": [(0.14, (8, 0, 0)), (L, (0, 0, 0))],
         "tail_end": [(0.14, (8, 0, 0)), (L, (0, 0, 0))]}))
    out["chest"] += track("scale", [(0, (1, 1, 1)), (0.06, (1, 1, 1)), (0.14, (1.06, 0.92, 1.06)),
                                    (0.3, (0.98, 1.03, 0.98)), (L, (1, 1, 1))])
    return {"loop": "once", "length": L, "bones": out}


# The grip: arm forward, elbow bent, fingers curled round item_*. Only the
# arm's bones, so it plays on top of anything else.
GRIP = {"arm": (-22, 0, 4), "forearm": (-62, 0, 0), "hand": (0, 0, 0), "fingers": (0, 0, -88)}


def hold_one(side):
    m = 1 if side == "right" else -1
    out = {}
    for part, (x, y, z) in GRIP.items():
        k = (x, m * y, m * z)
        out[f"{part}_{side}"] = rot((0, k), (1.0, k))
    return {"loop": "loop", "length": 1.0, "bones": out}


def attack():
    """A one-handed slash with whatever is in the right hand: raise it high
    and out to the side, cut down and forward past the right hip, follow
    through, recover. The Imp's arms are too short to cut across its belly,
    so the blade stays on its own side, as a short-armed fighter's does."""
    L = 0.7
    g = GRIP
    keys = {
        "arm_right": [(0, g["arm"]), (0.25, (-40, 0, 60)), (0.37, (-60, 0, 18)),
                      (0.48, (-20, 0, 12)), (L, g["arm"])],
        "forearm_right": [(0, g["forearm"]), (0.25, (-68, 0, 0)), (0.37, (-10, 0, 0)),
                          (0.48, (-15, 0, 0)), (L, g["forearm"])],
        "fingers_right": [(0, g["fingers"]), (L, g["fingers"])],
        "arm_left": [(0, (0, 0, 0)), (0.25, (-15, 0, -10)), (0.37, (15, 0, -6)), (L, (0, 0, 0))],
        "chest": [(0, (0, 0, 0)), (0.25, (0, 14, 0)), (0.37, (0, -12, 0)), (0.48, (0, -14, 0)),
                  (L, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (0.25, (-4, -8, 0)), (0.37, (4, 8, 0)), (L, (0, 0, 0))],
        "ear_right": [(0, (0, 0, 0)), (0.25, (0, 0, 10)), (0.37, (0, 0, -6)), (L, (0, 0, 0))],
        "ear_left": [(0, (0, 0, 0)), (0.25, (0, 0, -10)), (0.37, (0, 0, 6)), (L, (0, 0, 0))],
        "tail": [(0, (0, 0, 0)), (0.25, (0, -18, 0)), (0.37, (0, 22, 0)), (L, (0, 0, 0))],
        "tail_mid": [(0, (0, 0, 0)), (0.3, (0, -14, 0)), (0.45, (0, 18, 0)), (L, (0, 0, 0))],
    }
    return {"loop": "once", "length": L, "bones": {b: rot(*ks) for b, ks in keys.items()}}


def swing():
    """A tool chop (pickaxe, axe, sickle) with the right hand: lift it up and
    out to the side, bring it down in front, hold the impact, recover."""
    L = 0.9
    g = GRIP
    keys = {
        "arm_right": [(0, g["arm"]), (0.35, (-50, 0, 75)), (0.5, (-45, 0, 2)), (0.6, (-40, 0, 2)),
                      (L, g["arm"])],
        "forearm_right": [(0, g["forearm"]), (0.35, (-55, 0, 0)), (0.5, (-15, 0, 0)), (0.6, (-15, 0, 0)),
                          (L, g["forearm"])],
        "fingers_right": [(0, g["fingers"]), (L, g["fingers"])],
        "arm_left": [(0, (0, 0, 0)), (0.35, (-15, 0, -12)), (0.5, (10, 0, -4)), (L, (0, 0, 0))],
        "chest": [(0, (0, 0, 0)), (0.35, (0, 12, 0)), (0.5, (0, -6, 0)), (0.6, (0, -6, 0)),
                  (L, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (0.35, (-6, -8, 0)), (0.5, (8, 4, 0)), (L, (0, 0, 0))],
        "ear_right": [(0, (0, 0, 0)), (0.35, (0, 0, 8)), (0.5, (0, 0, -10)), (L, (0, 0, 0))],
        "ear_left": [(0, (0, 0, 0)), (0.35, (0, 0, -8)), (0.5, (0, 0, 10)), (L, (0, 0, 0))],
        "tail": [(0, (0, 0, 0)), (0.35, (12, 0, 0)), (0.5, (-6, 0, 0)), (L, (0, 0, 0))],
    }
    return {"loop": "once", "length": L, "bones": {b: rot(*ks) for b, ks in keys.items()}}


def hit():
    """Knocked back: head snapped aside, arms flung out, ears flat, tail jolted."""
    L = 0.4
    keys = {
        "chest": [(0, (0, 0, 0)), (0.07, (-12, 8, 0)), (0.2, (3, -2, 0)), (L, (0, 0, 0))],
        "head": [(0, (0, 0, 0)), (0.07, (-8, 12, 6)), (0.2, (3, -3, -2)), (L, (0, 0, 0))],
        "arm_right": [(0, (0, 0, 0)), (0.07, (-15, 0, 25)), (L, (0, 0, 0))],
        "arm_left": [(0, (0, 0, 0)), (0.07, (-15, 0, -25)), (L, (0, 0, 0))],
        "fingers_right": [(0, (0, 0, 0)), (0.07, (0, 0, 20)), (L, (0, 0, 0))],
        "fingers_left": [(0, (0, 0, 0)), (0.07, (0, 0, -20)), (L, (0, 0, 0))],
        "ear_right": [(0, (0, 0, 0)), (0.07, (0, 18, -10)), (0.25, (0, 4, 0)), (L, (0, 0, 0))],
        "ear_left": [(0, (0, 0, 0)), (0.07, (0, -18, 10)), (0.25, (0, -4, 0)), (L, (0, 0, 0))],
        "tail": [(0, (0, 0, 0)), (0.07, (4, 16, 0)), (0.2, (-4, -4, 0)), (L, (0, 0, 0))],
        "tail_mid": [(0, (0, 0, 0)), (0.1, (0, 8, 0)), (L, (0, 0, 0))],
    }
    return {"loop": "once", "length": L, "bones": {b: rot(*ks) for b, ks in keys.items()}}


def idle():
    """Breathing, a slow look round, an ear twitch, the tail swaying."""
    L = 3.2
    return {"loop": "loop", "length": L, "bones": {
        "chest": track("scale", [(0, (1, 1, 1)), (0.8, (1.02, 1.025, 1.02)), (1.6, (1, 1, 1)),
                                 (2.4, (1.02, 1.025, 1.02)), (L, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.9, (2, 9, 3)), (1.5, (2, 9, 3)), (2.2, (-2, -7, -2)),
                    (2.8, (-2, -7, -2)), (L, (0, 0, 0))),
        "arm_right": cyc(L, lambda p: (2 * s(p), 0, 2 * s(2 * p))),
        "arm_left": cyc(L, lambda p: (2 * s(p + 0.3), 0, -2 * s(2 * p))),
        "fingers_right": cyc(L, lambda p: (0, 0, -10 - 5 * s(p))),
        "fingers_left": cyc(L, lambda p: (0, 0, 10 + 5 * s(p))),
        "ear_right": rot((0, (0, 0, 0)), (1.9, (0, 0, 0)), (1.98, (0, 0, 14)), (2.08, (0, 0, -5)),
                         (2.2, (0, 0, 0)), (L, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.5, (0, 0, 0)), (0.58, (0, 0, -10)), (0.68, (0, 0, 4)),
                        (0.8, (0, 0, 0)), (L, (0, 0, 0))),
        "tail": cyc(L, lambda p: (2 * s(2 * p), 10 * s(p), 0)),
        "tail_mid": cyc(L, lambda p: (3 * s(2 * p - 0.1), 12 * s(p - 0.1), 0)),
        "tail_end": cyc(L, lambda p: (4 * s(2 * p - 0.2), 14 * s(p - 0.2), 0)),
    }}


ANIMATIONS = {
    "idle": idle(),
    "walk": walk(),
    "sprint": sprint(),
    "jump": jump(),
    "fall": fall(),
    "land": land(),
    "hold_right": hold_one("right"),
    "hold_left": hold_one("left"),
    "attack": attack(),
    "swing": swing(),
    "hit": hit(),
}

# Parts that are one continuous skin: no painted shadow where they meet.
FAMILY = {"skin": "body", "hand": "body", "finger": "body", "foot": "body", "tail": "body"}


class Impling(RigCreature):
    """The head and body are round shapes built in 1 px steps, and the limbs
    run on into the hands and feet. Those joins are not where two parts meet,
    so painted contact shadow only falls where a box touches another part
    (the head on the shoulders, under the brows, round the horns and ears)."""

    def contact(self, e, f, p):
        n = NORMAL[f]
        q = [p[k] + 0.5 * n[k] for k in range(3)]
        mine = FAMILY.get(e["part"], e["part"])
        other = np.array([FAMILY.get(o["part"], o["part"]) != mine for o in self.elements])
        for tg in tangents(f):
            for sg in (-1, 1):
                if self.world_dir(e, [sg * c for c in tg])[1] < -0.7:
                    continue                       # lit from above: what's below casts nothing
                w = self.world(e, [q[k] + sg * tg[k] for k in range(3)])
                ql = np.einsum("nij,j->ni", self.MINV, np.array([*w, 1.0]))[:, :3]
                if (np.all((ql > self.LO + 1e-6) & (ql < self.HI - 1e-6), axis=1) & other).any():
                    return True
        return False


IMPLING = Impling("impling", ELEMENTS, BONES, PAINTERS, ANIMATIONS)

if __name__ == "__main__":
    IMPLING.build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent,
                  preview_scale=8, tile=(440, 400), anchor=0.92, sizes=(64, 128, 256))
