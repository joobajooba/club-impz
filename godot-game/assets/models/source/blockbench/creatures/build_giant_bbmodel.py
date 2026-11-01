"""Build the Blockbench giant: a 5 m, gaunt, hunched brute with a huge wooden club (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m. Twice the
  ogre's 2.5 m, as asked: 160 px from the soles to the top of the hair.
- Box sizes in whole texture pixels (0.5 units). Odd widths for the centred
  parts (nose, jaw strands) where a centre column matters.
- Per-face UV, one texture inside the large-creature budget, hidden faces removed.
- Lit from the top, slightly front-left; hue-shifted ramps (shadows toward
  violet, highlights toward warm), edge highlights on lit edges, painted
  shadow where parts meet, form shading on the ribs, collarbones and knees.
- Silhouette first (MODELS-BLOCKBENCH 4.2): tall and slender, long shins with
  knees, a hunched back with the shoulders rolled forward and the head jutting
  out, arms that hang past the hips, long hair over the hump, and a club as
  long as a man is tall. The hunch is built from stepped boxes, not a rotated
  spine, so every box stays on the pixel grid.
- As asked: pale sickly skin (blue veins, bruised sockets, sores, grime),
  dirty long grey hair, cloth rags, a giant wooden club, glowing orange eyes.
  The eyes are the one saturated accent; hostile creatures glow (STUDY 3.1).
  Painted, not emissive: emission through export is an open question (STUDY 5.4).
- There is no giant icon; the palette follows ART-DIRECTION section 5's rules
  (tinted neutrals, coloured shadows, saturation kept for the accent).
- Bones use the shared names, pivots at the joints: the knees and elbows
  bend, the jaw opens, the club and the loincloth swing. Animations: idle,
  walk, run, attack, hit, roar.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground, the giant faces north (-z), its right side is +x.

Usage: python build_giant_bbmodel.py [out_dir]   (writes giant.bbmodel, giant.png,
giant_preview.png and giant_silhouette.png)
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
from build_pickaxe_bbmodel import FACES, NORMAL, face_frame, texels  # noqa: E402

PX = 0.5   # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


# Ramps, darkest first. Shadows lean violet-blue, highlights lean warm.
# Warmer and a step darker than first drawn: the game's blue sky light cooled
# the first Godot test to blue-white. Hair a step darker so it parts from the skin.
SKIN = ramp("#3a3240", "#645b62", "#958c70", "#b4ab86", "#cdc49f")     # pale, sallow, sickly
BRUISE = ramp("#2c2433", "#4c4250", "#78706c", "#9a9480", "#b4ad94")   # blotches and sockets
VEIN = ramp("#56587a", "#787b9a")
SORE = ramp("#4a2228", "#73343a", "#8f5550")
HAIR = ramp("#1e1b20", "#35313a", "#524e53", "#726d67", "#918a7e")     # dirty grey
DIRT = ramp("#2e2620", "#4a3d31", "#625140")
RAG = ramp("#29221f", "#433830", "#605244", "#7d6c58", "#978469")
STAIN = ramp("#211816", "#36231f", "#4c3027")
ROPE = ramp("#2c241b", "#4a3c2a", "#6a573b", "#86714c")
WOOD = ramp("#1f1817", "#33261f", "#4d3826", "#6b4e31", "#8a683f")     # club head bark
GRAIN = ramp("#3a2c22", "#5c4430", "#7e603f", "#9c7c52")               # worn handle, end grain
TOOTH = ramp("#4a4232", "#7d735a", "#aca07e", "#cfc4a2")
NAIL = ramp("#3e3830", "#6a6150", "#958a70")
GLOW = ramp("#7a2a0c", "#cc5a14", "#ff9a2a", "#ffd270")                # the accent
MOUTH = ramp("#160d14", "#2f1820", "#56303a")

FACE_SHADE = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi):
    return {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}


def mirror(name, bone, part, lo, hi):
    """A right-side box and its mirror on the left ("*" is the side)."""
    return [el(name.replace("*", "right"), bone.replace("*", "right"), part, lo, hi),
            el(name.replace("*", "left"), bone.replace("*", "left"), part,
               (-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2]))]


ELEMENTS = [
    # Legs: long thighs, bony knees, longer shins, long bare feet.
    *mirror("thigh_*", "leg_*", "skin", (2, 44, -5), (12, 80, 5)),
    *mirror("knee_*", "leg_*", "skin", (2.5, 38, -6), (11.5, 46, 4)),
    *mirror("shin_*", "shin_*", "shin", (3, 5, -4), (11, 42, 4)),
    *mirror("foot_*", "shin_*", "foot", (2, 0, -15), (12, 6, 4)),
    # Trunk: rag-wrapped hips, a thin waist, a ribbed chest, shoulders rolled
    # forward, a hump behind, and a neck thrust out to carry the head.
    el("pelvis", "body", "rag", (-12.5, 72, -7), (12.5, 86, 7)),
    el("rope_belt", "body", "rope", (-13, 84, -7.5), (13, 87, 7.5)),
    el("rope_knot", "body", "rope", (-4, 80, -8.5), (-1, 87, -7.5)),
    el("rope_end", "body", "rope", (-3, 70, -8.5), (-2, 80, -7.5)),
    el("waist", "body", "skin", (-10.5, 85, -6), (10.5, 102, 6)),
    el("chest", "chest", "skin", (-14.5, 100, -10), (14.5, 118, 6)),
    el("upper_chest", "chest", "skin", (-13.5, 116, -15), (13.5, 128, 3)),
    el("hump", "chest", "skin", (-11.5, 106, 2), (11.5, 131, 12)),
    el("neck", "chest", "skin", (-6, 124, -22), (6, 137, -8)),
    # Hair down the back: from the crown, over the hump, down the spine.
    el("hair_mantle", "chest", "hair", (-10.5, 127, -10), (10.5, 133, 14)),
    el("hair_back", "chest", "hair", (-10.5, 98, 12), (10.5, 128, 15)),
    # Head: a long gaunt skull, heavy brow, long nose, a jaw that drops.
    el("head", "head", "face", (-9, 136, -33), (9, 156, -15)),
    el("brow", "head", "brow", (-8, 147, -35), (8, 150, -33)),
    el("nose", "head", "nose", (-1.5, 139, -36), (1.5, 148, -33)),
    el("nose_tip", "head", "nose", (-2.5, 139, -37), (2.5, 142, -34)),
    *mirror("ear_*", "head", "ear", (9, 142, -26), (11, 149, -22)),
    *mirror("ear_*_tip", "head", "ear", (9, 149, -25), (10, 152, -23)),
    el("hair_top", "head", "hair", (-9.5, 156, -33.5), (9.5, 160, -14.5)),
    el("hair_crown_back", "head", "hair", (-9.5, 131, -16), (9.5, 157, -10)),
    *mirror("hair_side_*", "head", "hair", (9, 134, -24), (11, 156, -14)),
    el("strand_right", "head", "hair", (9, 114, -29), (12, 152, -25)),
    el("strand_left", "head", "hair", (-12, 120, -30), (-9, 152, -25)),
    el("strand_left_tail", "head", "hair", (-11, 110, -28), (-9, 121, -26)),
    el("jaw", "jaw", "jaw", (-8, 130, -33), (8, 137, -19)),
    el("beard_strand_1", "jaw", "hair", (-3, 122, -32), (-1, 130, -30)),
    el("beard_strand_2", "jaw", "hair", (2, 125, -31), (4, 130, -29)),
    # Arms: a bony shoulder, a long upper arm, a longer forearm.
    *mirror("shoulder_*", "arm_*", "skin", (14.5, 113, -12.5), (24.5, 125, -2.5)),
    *mirror("arm_*", "arm_*", "skin", (15.5, 90, -11), (23.5, 115, -3)),
    *mirror("forearm_*", "forearm_*", "forearm", (15, 56, -11.5), (24, 92, -2.5)),
    # Right hand: a fist round the club. Left hand: an open claw.
    el("fist_right", "forearm_right", "fist", (15, 42, -12), (24, 57, -2)),
    el("palm_left", "forearm_left", "palm", (-24, 49, -11.5), (-15, 57, -2.5)),
    el("finger_left_1", "forearm_left", "finger", (-24, 39, -10.5), (-22, 49, -8.5)),
    el("finger_left_2", "forearm_left", "finger", (-21.5, 37, -10.5), (-19.5, 49, -8.5)),
    el("finger_left_3", "forearm_left", "finger", (-19, 40, -10.5), (-17, 49, -8.5)),
    el("thumb_left", "forearm_left", "finger", (-16, 45, -12.5), (-14, 53, -10.5)),
    # A rag over the left shoulder.
    el("shoulder_rag", "arm_left", "rag", (-25.5, 119, -14), (-13.5, 127, -1)),
    # Loincloth: a long front flap with a torn hem, and a back flap.
    el("loincloth", "loincloth", "rag", (-7, 50, -8), (7, 74, -7)),
    el("loincloth_tatter_1", "loincloth", "rag", (-6, 44, -8), (-3, 50, -7)),
    el("loincloth_tatter_2", "loincloth", "rag", (1, 46, -8), (5, 50, -7)),
    el("loincloth_back", "body", "rag", (-8, 52, 7.5), (8, 74, 8.5)),
    # The club: a long grip and a huge knotted head with branch stubs.
    el("club_handle", "club", "handle", (17, 22, -9.5), (22, 72, -4.5)),
    el("club_head", "club", "clubhead", (12.5, 1, -14), (26.5, 26, 0)),
    el("club_stub_1", "club", "stub", (26.5, 14, -8.5), (30.5, 17, -5.5)),
    el("club_stub_2", "club", "stub", (14, 18, -18), (17, 21, -14)),
    el("club_stub_3", "club", "stub", (9.5, 7, -4.5), (12.5, 10, -1.5)),
    el("club_cap", "club", "clubhead", (14, 26, -12.5), (25, 29, -1.5)),
    el("club_burl", "club", "clubhead", (10.5, 5, -11.5), (12.5, 15, -3.5)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "giant": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("giant", (0, 82, 0), (0, 0, 0)),
    "chest": ("body", (0, 100, 0), (0, 0, 0)),
    "head": ("chest", (0, 134, -15), (0, 0, 0)),
    "jaw": ("head", (0, 136, -19), (0, 0, 0)),
    "arm_right": ("chest", (19.5, 120, -7.5), (0, 0, 0)),
    "forearm_right": ("arm_right", (19.5, 91, -7), (0, 0, 0)),
    "club": ("forearm_right", (19.5, 49, -7), (8, 0, 0)),
    "arm_left": ("chest", (-19.5, 120, -7.5), (0, 0, 0)),
    "forearm_left": ("arm_left", (-19.5, 91, -7), (0, 0, 0)),
    "loincloth": ("body", (0, 74, -7.5), (0, 0, 0)),
    "leg_right": ("giant", (7, 78, 0), (0, 0, 0)),
    "shin_right": ("leg_right", (7, 43, 0), (0, 0, 0)),
    "leg_left": ("giant", (-7, 78, 0), (0, 0, 0)),
    "shin_left": ("leg_left", (-7, 43, 0), (0, 0, 0)),
}
ROTATED = {"club"}


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


def hash01(*key):
    h = 2166136261
    for v in key:
        h = ((h ^ (int(v) & 0xFFFFFFFF)) * 16777619) & 0xFFFFFFFF
    return h / 0xFFFFFFFF


def jag(k):
    """A fixed rhythm for torn, frayed and ragged edges: tufts, not noise."""
    return (0, 1, 1, 0, -1, 0, 1, -1)[k % 8]


def near_blob(p, blobs):
    return any(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)) < 1.0 for c, r in blobs)


def seg_dist(p, a, b):
    ab = [b[k] - a[k] for k in range(3)]
    ap = [p[k] - a[k] for k in range(3)]
    t = max(0.0, min(1.0, sum(ap[k] * ab[k] for k in range(3)) / sum(v * v for v in ab)))
    return math.dist(p, [a[k] + t * ab[k] for k in range(3)])


# Sickly blotches: greyer, bruised patches that wrap the form.
BLOTCHES = [
    ((10.5, 92, -2), (1.5, 4, 3)), ((-14.5, 110, 0), (1.5, 4, 3)), ((-6, 112, -10), (3, 2.5, 1.5)),
    ((24, 74, -4), (1.5, 4, 3)), ((-12, 60, -5), (2.5, 4, 1.5)), ((6, 33, -4), (2, 4, 1.5)),
]
# Sores: small reddish spots.
SORES = [(-4.5, 95.5, -6), (13.5, 106.5, -10), (-23.5, 80.5, -4), (8.5, 20.5, -4), (-6.5, 60.5, -5)]
# Veins: bluish lines on the arms, neck and temples.
VEINS = [
    ((23.5, 112, -6), (23.5, 96, -4)), ((24, 88, -6), (24, 64, -3)), ((-24, 86, -7), (-24, 62, -4)),
    ((-6, 136, -14), (-6, 127, -9)), ((9, 152, -24), (9, 146, -26)), ((-9, 153, -22), (-9, 146, -25)),
    ((12, 74, -5), (12, 52, -3)),
]
# Scars.
SCARS = [((-14.5, 114, -2), (-14.5, 104, 4)), ((4, 108, -10), (12, 102, -10))]


def skin_mark(p):
    for a, b in SCARS:
        if seg_dist(p, a, b) < 0.6:
            return "scar"
    for a, b in VEINS:
        if seg_dist(p, a, b) < 0.55:
            return "vein"
    for s in SORES:
        d = math.dist(p, s)
        if d < 0.75:
            return "sore"
        if d < 1.4:
            return "sore_rim"
    return None


def sash(e, p, f):
    """The rag slung from the left shoulder across the chest to the right hip
    (front and back)."""
    if e["name"] not in ("chest", "upper_chest", "waist") or f in ("west", "east", "down", "up"):
        return False
    x, y, z = p
    centre = -13 + (126 - y) * 0.62
    return abs(x - centre) < 3 + 0.5 * jag(fi(y))


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


def skin(p, v):
    m = skin_mark(p)
    if m == "scar":
        return BRUISE[clamp(v + 1)]
    if m == "vein":
        return VEIN[1 if v >= 2 else 0]
    if m == "sore":
        return SORE[clamp(v - 1, 0, 2)]
    if m == "sore_rim":
        return SORE[2] if v >= 3 else SKIN[clamp(v - 1)]
    if near_blob(p, BLOTCHES):
        return BRUISE[clamp(v)]
    return SKIN[clamp(v)]


def paint_skin(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    n = e["name"]
    if n in ("chest", "waist") and f in ("north", "west", "east"):
        # Ribs: a dark line every third row over the ribcage, broken at the
        # breastbone, fading out toward the waist.
        if 96 <= y < 114 and fi(y) % 3 == 0 and not (f == "north" and abs(x) < 1.5):
            v -= 1
        if f == "north" and abs(x) < 1 and y >= 104:
            v -= 1                                 # breastbone
    if n == "waist" and f == "north" and y < 92:
        v -= 1                                     # sunken belly
    if n == "upper_chest" and f == "north":
        if y >= 125:
            v += 1                                 # collarbones
        if fi(y) == 122 and 3 <= abs(x) <= 12:
            v -= 1                                 # the hollow under them
    if n == "hump" and f in ("south", "up"):
        if abs(x) < 1 and fi(y if f == "south" else z) % 3 == 0:
            v += 1                                 # knuckles of the spine
        if f == "south" and 4 <= abs(x) <= 9 and 116 <= y < 126:
            v += 1                                 # shoulder blades
    if n.startswith("knee") and f == "north":
        v += 1                                     # bony kneecaps
    if n.startswith("thigh") and y > 74:
        v -= 1                                     # under the rags
    if n.startswith("shoulder") and f == "up":
        v = 4 if (i in (0, 1) or j in (0, 1)) else 3
    if n.startswith("arm_") and y < 93:
        v -= 1                                     # the inside of the elbow
    if n == "neck" and f in ("west", "east") and fi(z) % 4 == 0 and y < 134:
        v -= 1                                     # cords of the neck
    if sash(e, p, f):
        return RAG[clamp(v - (1 if fi(y) % 3 == 0 else 0))]
    return skin(p, v)


def paint_face(e, f, p, i, j, w, h):
    """The head. Front columns x (-9..8), rows y (136..155). The brow covers
    -8..7 at 147..149, the nose -1..1 at 139..147 and its tip -2..2 at 139..141.
    Two glowing eyes sit deep in bruised sockets under the brow."""
    x, y, z = p
    c, r = math.floor(x), fi(y)
    ac = abs(c + 0.5)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if 2.5 <= ac <= 5.5 and r in (144, 145):
            hot = (r == 145 and ((c < 0 and ac == 4.5) or (c > 0 and ac == 3.5)))
            if hot:
                return GLOW[3]                     # the hottest pixel, toward the light
            return GLOW[2] if r == 145 else GLOW[1]
        if 1.5 <= ac <= 6.5 and r in (143, 146):
            return BRUISE[0]                       # deep sockets
        if 1.5 <= ac <= 6.5 and r == 142:
            return BRUISE[1]                       # dark bags
        if 6.5 <= ac and 138 <= r <= 142:
            v -= 1                                 # hollow cheeks
        if ac >= 7.5 and 143 <= r <= 146:
            v += 1                                 # cheekbones
        if r in (151, 153) and ac <= 6.5 and (c + r) % 5 != 0:
            v -= 1                                 # a furrowed forehead
        if r <= 137:
            if ac <= 6.5:
                return MOUTH[0]                    # the upper lip line
    if f == "up":
        v -= 1                                     # under the hair
    if f in ("west", "east"):
        if 140 <= r <= 144 and z < -22:
            v -= 1                                 # hollow temples and cheeks
    return skin(p, v)


def paint_brow(e, f, p, i, j, w, h):
    x, y, z = p
    c = math.floor(x)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if c in (-1, 0):
            return SKIN[0]                         # the scowl
        if fi(y) == 147:
            v -= 1
    if f == "down":
        return BRUISE[0]
    if f == "up" and (c + fi(z)) % 2 == 0:
        return HAIR[1]                             # wild brows
    return skin(p, v)


def paint_nose(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if e["name"] == "nose_tip":
        if f == "down" or (f == "north" and fi(y) == 139 and abs(math.floor(x) + 0.5) >= 1.5):
            return MOUTH[0]                        # nostrils
    if f in ("west", "east"):
        v -= 1
    return skin(p, v)


def paint_ear(e, f, p, i, j, w, h):
    v = base_shade(e, f, p, i, j)
    if f == "north" and not e["name"].endswith("tip") and 0 < i < w - 1 and 0 < j < h - 1:
        return SKIN[0]                             # inside of the ear
    return skin(p, v)


def paint_jaw(e, f, p, i, j, w, h):
    """The lower jaw: crooked, gappy teeth on the rim, a lantern chin."""
    x, y, z = p
    c, r = math.floor(x), fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "up":
        if z < -26:
            return MOUTH[0] if c in (-5, -1, 2, 6) else TOOTH[2 + (c % 2)]
        return MOUTH[1] if abs(c + 0.5) < 6 else MOUTH[0]
    if f == "north":
        if r == 136:
            return MOUTH[0] if c in (-5, -1, 2, 6) else TOOTH[3 if c % 3 else 2]
        if r == 135 and c in (-4, 3):
            return TOOTH[1]                        # two long lower fangs
        if r <= 132:
            v -= 1
    return skin(p, v)


def paint_hair(e, f, p, i, j, w, h):
    """Long, dirty grey hair: strands as constant-shade columns, clumped with
    dirt, lighter on top, ragged at the ends."""
    x, y, z = p
    v = {"up": 3, "north": 2, "west": 2, "south": 2, "east": 1, "down": 0}[f]
    if f in ("north", "south", "west", "east"):
        k = math.floor(x) if f in ("north", "south") else fi(z)
        clump = (k + 40) // 3                      # strands bunch into 3 px clumps
        c = hash01(clump, FACES.index(f), len(e["name"]))
        v += 1 if c > 0.7 else (-1 if c < 0.3 else 0)
        if (k + 40) % 3 == 0 and c > 0.4:
            v -= 1                                 # the parting between two clumps
        if j == 0:
            v += 1
        end = e["lo"][1] + round(3 * c)            # each clump stops at its own length
        if y < end:
            return HAIR[1]
        if y < end + 1:
            return HAIR[clamp(v - 1)]
        if hash01(clump, fi(y / 5), 9) < 0.1:
            return DIRT[clamp(v - 1, 0, 2)]        # clumps of filth
    if f == "up":
        if abs(x) < 1 and e["name"] == "hair_top":
            return SKIN[1]                         # a thin, greasy parting
        k = hash01((math.floor(x) + 40) // 3, fi(z / 6), 5)  # clumps lying back
        v += 1 if k > 0.7 else (-1 if k < 0.25 else 0)
    if contact(p, f, e):
        v -= 1
    return HAIR[clamp(v)]


def paint_shin(e, f, p, i, j, w, h):
    """Long shins: rag bandages wound round the lower half, grime below."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if 8 <= r <= 22:
        k = (math.floor(x) if f in ("north", "south") else fi(z)) + r
        if r in (8, 22) and k % 2:
            return RAG[0]                          # frayed edges of the wrap
        if k % 6 == 0:
            v -= 1                                 # the diagonal turns of the bandage
        if 12 <= r <= 15 and f == "north" and math.floor(x) % 3 == 0:
            return STAIN[1]
        return RAG[clamp(v)]
    if r < 8:
        return DIRT[clamp(v - 1, 0, 2)] if (r + fi(z) + math.floor(x)) % 3 else SKIN[clamp(v - 2)]
    if f == "north" and abs(x - (7 if x > 0 else -7)) < 1:
        v += 1                                     # the shinbone
    return skin(p, v)


def paint_foot(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "down":
        return DIRT[0]
    if f == "north":
        if i in (2, 4, 6, 8):
            return SKIN[0]                         # gaps between long toes
        if r >= 4:
            return NAIL[1]                         # cracked toenails
        return DIRT[clamp(v - 1, 0, 2)]
    if f == "up" and z < -10 and i in (2, 4, 6, 8):
        return SKIN[1]
    return DIRT[clamp(v - 1, 0, 2)] if hash01(i // 2, j, FACES.index(f)) < 0.4 else SKIN[clamp(v - 1)]


def paint_forearm(e, f, p, i, j, w, h):
    """Bony forearms, bandaged at the wrist, veins standing out."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if 56 <= r <= 66:
        k = (math.floor(x) if f in ("north", "south") else fi(z)) + r
        if r in (56, 66) and k % 2:
            return RAG[0]
        return RAG[clamp(v - (1 if k % 4 == 0 else 0))]
    if r >= 89:
        v -= 1
    return skin(p, v)


def paint_hand(e, f, p, i, j, w, h):
    """The fist round the club and the open left palm: bony knuckles, grime."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if e["name"] == "fist_right" and f == "north":
        if r >= 54:
            v += 1                                 # knuckles
            if i % 3 == 2:
                v -= 2
        elif 45 <= r <= 52 and i % 3 == 2:
            return SKIN[0]                         # fingers curled round the grip
        elif r <= 44 and i % 3 != 2:
            return NAIL[0]                         # filthy nails
    if f == "down":
        return DIRT[1]
    if hash01(i // 2, fi(y / 2), FACES.index(f), len(e["name"])) < 0.3:
        return DIRT[clamp(v - 1, 0, 2)]            # grime worked into the skin
    return skin(p, v)


def paint_finger(e, f, p, i, j, w, h):
    """Long bony fingers ending in yellowed claws."""
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    if fi(y) < e["lo"][1] + 2:
        return NAIL[clamp(v - 1, 0, 2)]
    if fi(y) in (e["lo"][1] + 4, e["lo"][1] + 7):
        v -= 1                                     # knuckle creases
    return skin(p, v)


def paint_rag(e, f, p, i, j, w, h):
    """Cloth rags: coarse threads across, a sewn patch, stains, a hole, frayed hems."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    n = e["name"]
    k = math.floor(x) if f in ("north", "south", "up", "down") else fi(z)
    if f in ("north", "south", "west", "east") and j == h - 1:
        return RAG[0] if k % 2 else RAG[clamp(v - 1)]           # frayed hem
    if n == "loincloth" and f == "north":
        if ((x + 2) / 2.5) ** 2 + ((y - 60) / 4) ** 2 < 1:
            return STAIN[clamp(v - 1, 0, 2)]       # old blood
        if 1 <= x <= 5 and 64 <= y <= 69:
            if x in (1, 5) or r in (64, 69):
                return ROPE[0]                     # stitches round a patch
            return RAG[clamp(v + 1)] if (math.floor(x) + r) % 2 else RAG[clamp(v)]
    if n == "pelvis" and f in ("west", "east") and ((y - 78) / 2) ** 2 + ((z + 1) / 2) ** 2 < 1:
        return SKIN[1]                             # a hole showing skin
    if f in ("up", "down"):
        r = fi(z)
    if r % 3 == 0 and (k + r) % 7 != 0:
        v -= 1                                     # coarse threads
    return RAG[clamp(v)]


def paint_rope(e, f, p, i, j, w, h):
    x, y, z = p
    k = (math.floor(x) if f in ("north", "south") else fi(z)) + fi(y)
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    return ROPE[clamp(v - (1 if k % 3 == 0 else 0), 0, 3)]     # the twist


def paint_handle(e, f, p, i, j, w, h):
    """The club's long grip: worn smooth wood, a rag wrap where the fist holds it."""
    x, y, z = p
    r = fi(y)
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    if 40 <= r <= 60:
        k = (math.floor(x) if f in ("north", "south") else fi(z)) + r
        return RAG[clamp(v - (1 if k % 3 == 0 else 0))]
    if f in ("up", "down"):
        return GRAIN[2 if (i + j) % 3 else 1]      # end grain
    if (r + i) % 5 == 0:
        v -= 1                                     # grain
    return GRAIN[clamp(v, 0, 3)]


def paint_clubhead(e, f, p, i, j, w, h):
    """A huge knotted log: deep bark furrows running down it, two knots, end
    grain rings on the cut faces, a few dark stains."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if f in ("up", "down"):
        cx, cz = (19.5, -7)
        ring = int(math.hypot(x - cx, z - cz))
        return GRAIN[1 if ring % 2 else 2] if ring < 5 else WOOD[clamp(v - 1)]
    k = math.floor(x) if f in ("north", "south") else fi(z)
    seg = fi((y + 5 * hash01(k, 1)) / 6)           # furrows break and restart
    b = hash01(k, seg, FACES.index(f))
    if b < 0.28:
        v -= 2                                     # deep bark furrows
    elif b > 0.8:
        v += 1                                     # bark ridges catching the light
    for kx, ky in ((17.5, 15), (23.5, 7)):
        d = math.hypot((x if f in ("north", "south") else z + 26.5) - kx, y - ky)
        if d < 1.5:
            return WOOD[0]                         # knot
        if d < 2.5:
            return WOOD[clamp(v + 1)]
    if near_blob(p, [((26.5, 5, -8.5), (1.5, 3, 3)), ((15, 4, -14), (3, 2.5, 1.5))]):
        return STAIN[clamp(v - 1, 0, 2)]
    return WOOD[clamp(v)]


def paint_stub(e, f, p, i, j, w, h):
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    lo, hi = e["lo"], e["hi"]
    tip = [k for k in range(3) if hi[k] - lo[k] == max(hi[k] - lo[k] for k in range(3))]
    # The cut end of a lopped branch shows pale grain.
    if (f in ("east", "west") and 0 in tip) or (f in ("north", "south") and 2 in tip):
        return GRAIN[2] if (i + j) % 2 else GRAIN[1]
    return WOOD[clamp(v)]


PAINTERS = {"skin": paint_skin, "face": paint_face, "brow": paint_brow, "nose": paint_nose,
            "ear": paint_ear, "jaw": paint_jaw, "hair": paint_hair, "shin": paint_shin,
            "foot": paint_foot, "forearm": paint_forearm, "fist": paint_hand,
            "palm": paint_hand, "finger": paint_finger, "rag": paint_rag, "rope": paint_rope,
            "handle": paint_handle, "clubhead": paint_clubhead, "stub": paint_stub}


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


# Rotations are in Blockbench's animation convention: a positive x pitches the
# head and body forward, swings a foot backward and bends a knee, opens the
# jaw; a negative x raises an arm forward and up and bends an elbow.
ANIMATIONS = {
    # Slow, rattling breaths; the hunched head turns to stare; the free
    # hand's fingers flex; the club rocks in the fist.
    "idle": {"loop": "loop", "length": 4.0, "bones": {
        "chest": track("scale", [(0, (1, 1, 1)), (2.0, (1.025, 1.015, 1.03)), (4.0, (1, 1, 1))])
        + rot((0, (0, 0, 0)), (2.0, (-2, 0, 0)), (4.0, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (1.0, (3, 10, 2)), (2.0, (4, 10, 2)), (2.6, (2, -8, -2)),
                    (3.4, (2, -8, -2)), (4.0, (0, 0, 0))),
        "jaw": rot((0, (2, 0, 0)), (2.0, (7, 0, 0)), (4.0, (2, 0, 0))),
        "arm_left": sway(4.0, 3, 0.2, 0),
        "forearm_left": rot((0, (-6, 0, 0)), (1.0, (-14, 0, 0)), (1.4, (-6, 0, 0)), (4.0, (-6, 0, 0))),
        "arm_right": sway(4.0, 2, 0.45, 0),
        "club": sway(4.0, 3, 0.5, 0),
        "loincloth": sway(4.0, 2, 0.3, 0),
    }},
    # A long, slow stride: the knee lifts and folds, the free arm swings, the
    # club drags along, the hunched upper body sways and the head bobs.
    "walk": {"loop": "loop", "length": 2.0, "bones": {
        "leg_right": rot((0, (-22, 0, 0)), (0.5, (-4, 0, 0)), (1.0, (18, 0, 0)), (1.5, (-10, 0, 0)),
                         (2.0, (-22, 0, 0))),
        "shin_right": rot((0, (6, 0, 0)), (0.5, (2, 0, 0)), (1.0, (10, 0, 0)), (1.5, (45, 0, 0)),
                          (2.0, (6, 0, 0))),
        "leg_left": rot((0, (18, 0, 0)), (0.5, (-10, 0, 0)), (1.0, (-22, 0, 0)), (1.5, (-4, 0, 0)),
                        (2.0, (18, 0, 0))),
        "shin_left": rot((0, (10, 0, 0)), (0.5, (45, 0, 0)), (1.0, (6, 0, 0)), (1.5, (2, 0, 0)),
                         (2.0, (10, 0, 0))),
        "arm_left": rot((0, (16, 0, 0)), (1.0, (-18, 0, 0)), (2.0, (16, 0, 0))),
        "forearm_left": rot((0, (-8, 0, 0)), (1.0, (-20, 0, 0)), (2.0, (-8, 0, 0))),
        "arm_right": rot((0, (-6, 0, 0)), (1.0, (8, 0, 0)), (2.0, (-6, 0, 0))),
        "club": sway(2.0, 6, 0.15, 0),
        "body": track("position", [(0, (0, 0, 0)), (0.5, (0, 2, 0)), (1.0, (0, 0, 0)),
                                   (1.5, (0, 2, 0)), (2.0, (0, 0, 0))])
        + rot((0, (3, -4, 2)), (1.0, (3, 4, -2)), (2.0, (3, -4, 2))),
        "chest": rot((0, (0, 3, -2)), (1.0, (0, -3, 2)), (2.0, (0, 3, -2))),
        "head": rot((0, (0, -3, 2)), (0.5, (4, 0, 0)), (1.0, (0, 3, -2)), (1.5, (4, 0, 0)),
                    (2.0, (0, -3, 2))),
        "loincloth": sway(2.0, 8, 0.1, 0),
    }},
    # A loping charge: deeper lean, longer strides, the club swung up and back.
    "run": {"loop": "loop", "length": 1.1, "bones": {
        "leg_right": rot((0, (-38, 0, 0)), (0.55, (30, 0, 0)), (1.1, (-38, 0, 0))),
        "shin_right": rot((0, (10, 0, 0)), (0.3, (5, 0, 0)), (0.55, (25, 0, 0)), (0.8, (70, 0, 0)),
                          (1.1, (10, 0, 0))),
        "leg_left": rot((0, (30, 0, 0)), (0.55, (-38, 0, 0)), (1.1, (30, 0, 0))),
        "shin_left": rot((0, (25, 0, 0)), (0.25, (70, 0, 0)), (0.55, (10, 0, 0)), (0.85, (5, 0, 0)),
                         (1.1, (25, 0, 0))),
        "arm_left": rot((0, (30, 0, 0)), (0.55, (-32, 0, 0)), (1.1, (30, 0, 0))),
        "forearm_left": rot((0, (-30, 0, 0)), (1.1, (-30, 0, 0))),
        "arm_right": rot((0, (-20, 0, 0)), (0.55, (15, 0, 0)), (1.1, (-20, 0, 0))),
        "forearm_right": rot((0, (-25, 0, 0)), (1.1, (-25, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.275, (0, 3, 0)), (0.55, (0, 0, 0)),
                                   (0.825, (0, 3, 0)), (1.1, (0, 0, 0))])
        + rot((0, (14, -5, 2)), (0.55, (14, 5, -2)), (1.1, (14, -5, 2))),
        "head": rot((0, (-10, 0, 0)), (0.275, (-6, 0, 0)), (0.55, (-10, 0, 0)), (0.825, (-6, 0, 0)),
                    (1.1, (-10, 0, 0))),
        "jaw": rot((0, (12, 0, 0)), (1.1, (12, 0, 0))),
        "loincloth": rot((0, (-18, 0, 0)), (0.55, (-8, 0, 0)), (1.1, (-18, 0, 0))),
    }},
    # Overhead slam: the club comes up and back over the hump (anticipation),
    # then down with the whole body, knees buckling, a held impact, recovery.
    "attack": {"loop": "once", "length": 1.8, "bones": {
        "arm_right": rot((0, (0, 0, 0)), (0.7, (-170, 0, -8)), (0.95, (-72, 0, 0)), (1.25, (-68, 0, 0)),
                         (1.8, (0, 0, 0))),
        "forearm_right": rot((0, (0, 0, 0)), (0.7, (-45, 0, 0)), (0.95, (-8, 0, 0)), (1.25, (-8, 0, 0)),
                             (1.8, (0, 0, 0))),
        "club": rot((0, (0, 0, 0)), (0.7, (-25, 0, 0)), (0.95, (40, 0, 0)), (1.25, (40, 0, 0)),
                    (1.8, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.7, (25, 0, -18)), (0.95, (-25, 0, -10)), (1.8, (0, 0, 0))),
        "body": rot((0, (0, 0, 0)), (0.7, (-10, 12, 0)), (0.95, (20, -6, 0)), (1.25, (18, -5, 0)),
                    (1.8, (0, 0, 0)))
        + track("position", [(0, (0, 0, 0)), (0.7, (0, 2, 2)), (0.95, (0, -5, -5)), (1.25, (0, -5, -5)),
                             (1.8, (0, 0, 0))]),
        "chest": rot((0, (0, 0, 0)), (0.7, (-8, 0, 0)), (0.95, (10, 0, 0)), (1.8, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.7, (-15, 0, 0)), (0.95, (12, 0, 0)), (1.8, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.7, (25, 0, 0)), (0.95, (6, 0, 0)), (1.8, (0, 0, 0))),
        "leg_right": rot((0, (0, 0, 0)), (0.7, (8, 0, 0)), (0.95, (-25, 0, 0)), (1.25, (-25, 0, 0)),
                         (1.8, (0, 0, 0))),
        "shin_right": rot((0, (0, 0, 0)), (0.95, (30, 0, 0)), (1.25, (30, 0, 0)), (1.8, (0, 0, 0))),
        "leg_left": rot((0, (0, 0, 0)), (0.7, (-6, 0, 0)), (0.95, (15, 0, 0)), (1.8, (0, 0, 0))),
        "shin_left": rot((0, (0, 0, 0)), (0.95, (15, 0, 0)), (1.8, (0, 0, 0))),
    }},
    # Hit: rocked back, head snapped aside, jaw dropped, arms flung out.
    "hit": {"loop": "once", "length": 0.6, "bones": {
        "body": rot((0, (0, 0, 0)), (0.1, (-8, 6, 0)), (0.3, (2, -2, 0)), (0.6, (0, 0, 0)))
        + track("position", [(0, (0, 0, 0)), (0.1, (0, 0, 3)), (0.6, (0, 0, 0))]),
        "chest": rot((0, (0, 0, 0)), (0.1, (-6, 0, 0)), (0.6, (0, 0, 0))),
        "head": rot((0, (0, 0, 0)), (0.1, (-18, 14, 8)), (0.3, (4, -3, -2)), (0.6, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.1, (18, 0, 0)), (0.6, (0, 0, 0))),
        "arm_right": rot((0, (0, 0, 0)), (0.1, (-12, 0, 15)), (0.6, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.1, (-20, 0, -20)), (0.6, (0, 0, 0))),
        "loincloth": rot((0, (0, 0, 0)), (0.1, (-15, 0, 0)), (0.35, (6, 0, 0)), (0.6, (0, 0, 0))),
    }},
    # Roar: the hunch straightens, the head tips back, the jaw gapes, the
    # claw hand rises and the club is lifted to the side.
    "roar": {"loop": "once", "length": 2.6, "bones": {
        "chest": rot((0, (0, 0, 0)), (0.5, (6, 0, 0)), (0.9, (-14, 0, 0)), (2.0, (-12, 0, 0)),
                     (2.6, (0, 0, 0)))
        + track("scale", [(0, (1, 1, 1)), (0.5, (1.02, 0.98, 1.02)), (0.9, (1.03, 1.03, 1.03)),
                          (2.0, (1.03, 1.03, 1.03)), (2.6, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.5, (10, 0, 0)), (0.9, (-28, 0, 0)), (1.3, (-25, 6, 0)),
                    (1.7, (-28, -6, 0)), (2.0, (-25, 0, 0)), (2.6, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.5, (4, 0, 0)), (0.9, (40, 0, 0)), (2.0, (36, 0, 0)), (2.6, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.9, (-70, 0, -30)), (1.3, (-75, 0, -28)), (1.7, (-70, 0, -32)),
                        (2.0, (-72, 0, -30)), (2.6, (0, 0, 0))),
        "forearm_left": rot((0, (0, 0, 0)), (0.9, (-40, 0, 0)), (2.0, (-40, 0, 0)), (2.6, (0, 0, 0))),
        "arm_right": rot((0, (0, 0, 0)), (0.9, (-25, 0, 30)), (2.0, (-25, 0, 30)), (2.6, (0, 0, 0))),
        "forearm_right": rot((0, (0, 0, 0)), (0.9, (-30, 0, 0)), (2.0, (-30, 0, 0)), (2.6, (0, 0, 0))),
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
    cx, cyy = size[0] / 2, size[1] * 0.95
    for depth, corners, col in sorted(quads, key=lambda q: q[0]):
        d.polygon([(cx + c[0] * scale, cyy - c[1] * scale) for c in corners], fill=col)
    return out


def skyline_pack(rects, size):
    """Tallest first, each rect goes where the skyline is lowest.
    Returns key -> (x, y), or None if it doesn't fit."""
    heights = [0] * size
    out = {}
    for key, w, h in sorted(rects, key=lambda r: (-r[2], -r[1])):
        best = None
        for x in range(size - w + 1):
            y = max(heights[x:x + w])
            if y + h <= size and (best is None or y < best[1]):
                best = (x, y)
        if best is None:
            return None
        x, y = best
        for k in range(x, x + w):
            heights[k] = y + h
        out[key] = (x, y)
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

    rects = [(k, w, h) for k, (w, h) in visible.items()]
    for tex in (128, 256):
        places = skyline_pack(rects, tex)
        if places:
            break
    img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
    for (ei, f), (ox, oy) in places.items():
        e = ELEMENTS[ei]
        w, h = visible[(ei, f)]
        for i, j, p in texels(e, f):
            img.putpixel((ox + i, oy + j), PAINTERS[e["part"]](e, f, p, i, j, w, h))

    tex_png = out_dir / "giant.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, left side, front (the giant faces -z).
    views = [(-145, 12), (145, 12), (-35, 12), (-90, 0), (180, 0)]
    tiles = [render(img, places, yw, pt, 2.0, (300, 360)) for yw, pt in views]
    sheet = Image.new("RGBA", (300 * len(tiles), 360), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (300 * k, 0))
    sheet.save(out_dir / "giant_preview.png")
    sil = Image.new("RGBA", (600, 360), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 12, 2.0, (300, 360), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 2.0, (300, 360), True), (300, 0))
    sil.save(out_dir / "giant_silhouette.png")

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
        "from": [20, 0, -2], "to": [24, 18, 2], "autouv": 0, "color": 1,
        "origin": [22, 0, 0],
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
        group("giant"),
        {"name": "scale_dummy", "origin": [22, 0, 0], "rotation": [0, 0, 0], "color": 0,
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
        "name": "giant", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": tex, "height": tex},
        "elements": elements, "outliner": outliner, "textures": [texture],
        "animations": animations,
    }
    (out_dir / "giant.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(ELEMENTS)}  bones: {len(BONES)}  visible faces: {len(visible)}  "
          f"texture: {tex}x{tex}  texels used: {used}/{tex * tex}  "
          f"animations: {', '.join(ANIMATIONS)}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
