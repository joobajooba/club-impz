"""Build the Blockbench ogre: a 2.5 m, sickly green, dark-fantasy brute in rags (Generic Model).

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m, so 2.5 m is
  80 px from the soles to the crown, as asked.
- Box sizes in whole texture pixels (0.5 units). Odd widths for the centred
  parts (head, brow, nose, jaw, buckle, skull) so the face has a centre column.
- Per-face UV, one texture inside the large-creature budget, hidden faces removed.
- Lit from the top, slightly front-left; hue-shifted ramps (shadows toward
  purple, highlights toward yellow), edge highlights on lit edges, painted
  shadow where parts meet, form shading on the muscles and the gut.
- Silhouette first (MODELS-BLOCKBENCH 4.2): a hunched back, a hanging gut,
  arms that reach the knees, a jutting underbite with tusks and trumpet ears
  (the Shrek read), then a club that breaks the outline.
- Dark fantasy, as asked: scars with crude stitches, warts and sickly
  mottling, one blind milky eye and one glowing eye, a bone necklace with a
  skull, a broken shackle and chain, blood on the club and the rags.
- The glowing eye is the one saturated accent; hostile creatures glow
  (BLOCKBENCH-STUDY 3.1). It is painted, not emissive: whether an emission
  texture survives export is still an open question (STUDY 5.4).
- There is no ogre icon; the palette follows ART-DIRECTION section 5's rules
  (tinted neutrals, coloured shadows, saturation kept for the accent).
- Bones use the shared names, pivots at the joints. The jaw is its own bone,
  the elbows bend, the club and the loincloth swing. Animations: idle, walk,
  run, attack, hit, plus roar.

Everything is designed in texture pixels ("px", 1 px = 0.5 units). y = 0 is
the ground, the ogre faces north (-z), its right side is +x.

Usage: python build_ogre_bbmodel.py [out_dir]   (writes ogre.bbmodel, ogre.png,
ogre_preview.png and ogre_silhouette.png)
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


# Ramps, darkest first. Shadows lean purple, highlights lean yellow.
SKIN = ramp("#221f2a", "#343a2b", "#4b5333", "#67703f", "#878a55")     # sickly, greyed olive green
MOTTLE = ramp("#1f1a28", "#2f2b37", "#454a3a", "#5f6644", "#7c8053")   # bruised, greyer patches
SCAR = ramp("#4e3a46", "#6e5560", "#917580")
RAG = ramp("#2a2223", "#45372f", "#64523e", "#837050", "#9f8a66")
STAIN = ramp("#22171a", "#371f22", "#4f2a29", "#653831")
LEATHER = ramp("#1e1618", "#332429", "#4c362f", "#684a39")
IRON = ramp("#25212a", "#3c383f", "#5a5453", "#7a7266")
RUST = ramp("#45271f", "#743d25", "#9b5c2d")
BONE = ramp("#493f33", "#7c705a", "#ab9d80", "#d0c4a5", "#e9dfc3")
WOOD = ramp("#231a1c", "#3a2923", "#573c2b", "#765335", "#946c46")
BLOOD = ramp("#33121a", "#561a22", "#74242a")
GLOW = ramp("#76290f", "#c45f19", "#fbb038", "#ffe486")               # the accent
MILKY = ramp("#7f8577", "#b4baa6", "#d8dbc9")
MOUTH = ramp("#1c0f17", "#3b1924", "#662b38")

FACE_SHADE = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi):
    return {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}


def mirror(name, bone, part, lo, hi, sides=("right", "left")):
    """A right-side box and its mirror on the left ("*" is the side)."""
    out = []
    if "right" in sides:
        out.append(el(name.replace("*", "right"), bone.replace("*", "right"), part, lo, hi))
    if "left" in sides:
        out.append(el(name.replace("*", "left"), bone.replace("*", "left"), part,
                      (-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2])))
    return out


ELEMENTS = [
    # Trunk: rag-wrapped hips, a hanging gut, a broad chest and a hunched back.
    el("pelvis", "body", "rag", (-14.5, 26, -8.5), (14.5, 36, 8.5)),
    el("belly", "body", "skin", (-15.5, 30, -12.5), (15.5, 52, 9.5)),
    el("chest", "body", "skin", (-17.5, 48, -9.5), (17.5, 66, 9.5)),
    el("hump", "body", "skin", (-13.5, 62, -4.5), (13.5, 70, 9.5)),
    el("neck", "body", "skin", (-8.5, 62, -9.5), (8.5, 72, -2.5)),
    el("gut", "body", "skin", (-12.5, 33, -14.5), (12.5, 49, -12.5)),
    el("belt", "body", "leather", (-16.5, 30, -13.5), (16.5, 33, 10.5)),
    el("buckle", "body", "iron", (-2.5, 29, -14.5), (2.5, 34, -13.5)),
    # Bone necklace: a skull charm and two big teeth on a cord (the cord is painted).
    el("skull", "body", "bone", (-1.5, 54, -11.5), (1.5, 57, -9.5)),
    *mirror("tooth_*", "body", "bone", (4, 56, -10.5), (5, 58, -9.5)),
    # Head: hunched forward, a heavy brow, a broad nose, an underbite with tusks.
    el("head", "head", "face", (-9.5, 62, -22.5), (9.5, 79, -6.5)),
    el("crown", "head", "face", (-8.5, 79, -21.5), (8.5, 80, -7.5)),
    *mirror("jowl_*", "head", "face", (9.5, 62, -21), (10.5, 68, -12)),
    el("brow", "head", "brow", (-8.5, 72, -24.5), (8.5, 75, -22.5)),
    el("nose", "head", "nose", (-2.5, 67, -25.5), (2.5, 72, -22.5)),
    el("nose_tip", "head", "nose", (-3.5, 66, -26.5), (3.5, 69, -24.5)),
    el("jaw", "jaw", "jaw", (-8.5, 58, -24.5), (8.5, 64, -10.5)),
    *mirror("tusk_*", "jaw", "tusk", (5, 64, -24.5), (7, 69, -22.5)),
    # Trumpet ears: a stalk and a flared end.
    *mirror("ear_*", "ear_*", "ear", (9.5, 69.5, -15.5), (14.5, 72.5, -12.5)),
    *mirror("ear_*_end", "ear_*", "ear", (14.5, 68, -17), (17.5, 74, -11)),
    # Arms: a round shoulder, a thick upper arm, a heavier forearm and fist.
    *mirror("shoulder_*", "arm_*", "skin", (17.5, 56, -5.5), (28.5, 66, 5.5)),
    *mirror("arm_*", "arm_*", "skin", (18.5, 44, -4.5), (27.5, 57, 4.5)),
    *mirror("forearm_*", "forearm_*", "skin", (18, 27, -6), (29, 46, 6)),
    *mirror("fist_*", "forearm_*", "fist", (18, 17, -5.5), (29, 28, 5.5)),
    # A rag over the left shoulder, a broken shackle and chain on the left wrist.
    el("shoulder_rag", "arm_left", "rag", (-29.5, 62, -6.5), (-16.5, 67, 6.5)),
    el("shackle", "forearm_left", "iron", (-29.5, 29, -6.5), (-17.5, 32, 6.5)),
    el("chain_1", "forearm_left", "iron", (-24, 25, 6.5), (-23, 29, 7.5)),
    el("chain_2", "forearm_left", "iron", (-25, 22, 6.5), (-24, 25, 7.5)),
    # Legs: short and thick, bandaged ankles, broad bare feet.
    *mirror("thigh_*", "leg_*", "skin", (3.5, 13, -4.5), (12.5, 30, 4.5)),
    *mirror("shin_*", "leg_*", "shin", (4.5, 5, -3.5), (11.5, 14, 3.5)),
    *mirror("foot_*", "leg_*", "foot", (3, 0, -9.5), (13, 5, 4.5)),
    # Loincloth: a front flap with a torn hem, and a back flap.
    el("loincloth", "loincloth", "rag", (-6.5, 14, -10.5), (6.5, 30, -9.5)),
    el("loincloth_tatter_1", "loincloth", "rag", (-5.5, 11, -10.5), (-2.5, 14, -9.5)),
    el("loincloth_tatter_2", "loincloth", "rag", (0.5, 12, -10.5), (4.5, 14, -9.5)),
    el("loincloth_back", "body", "rag", (-7.5, 16, 9), (7.5, 30, 10)),
    # The club: a long grip through the fist and a knotted head with nails.
    el("club_handle", "club", "wood", (22, 10, -1.5), (25, 31, 1.5)),
    el("club_head", "club", "clubhead", (19.5, 1, -4), (27.5, 11, 4)),
    el("nail_1", "club", "nail", (27.5, 5, -0.5), (29.5, 6, 0.5)),
    el("nail_2", "club", "nail", (17.5, 7, 1), (19.5, 8, 2)),
    el("nail_3", "club", "nail", (22, 3, -6), (23, 4, -4)),
    el("nail_4", "club", "nail", (24, 8, 4), (25, 9, 6)),
]

# Bones: parent, pivot (px), rest rotation (degrees, Blockbench order).
BONES = {
    "ogre": (None, (0, 0, 0), (0, 0, 0)),
    "body": ("ogre", (0, 30, 0), (0, 0, 0)),
    "head": ("body", (0, 66, -8), (0, 0, 0)),
    "jaw": ("head", (0, 63, -10.5), (0, 0, 0)),
    "ear_right": ("head", (9.5, 71.5, -14), (0, 0, 18)),
    "ear_left": ("head", (-9.5, 71.5, -14), (0, 0, -24)),     # the torn ear droops more
    "arm_right": ("body", (23, 61, 0), (0, 0, 0)),
    "forearm_right": ("arm_right", (23.5, 45, 0), (0, 0, 0)),
    "club": ("forearm_right", (23.5, 22.5, 0), (12, 0, 0)),
    "arm_left": ("body", (-23, 61, 0), (0, 0, 0)),
    "forearm_left": ("arm_left", (-23.5, 45, 0), (0, 0, 0)),
    "loincloth": ("body", (0, 30, -10), (0, 0, 0)),
    "leg_right": ("ogre", (8, 29, 0), (0, 0, 0)),
    "leg_left": ("ogre", (-8, 29, 0), (0, 0, 0)),
}
ROTATED = {"ear_right", "ear_left", "club"}


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
    """A fixed rhythm for torn and frayed edges: tufts, not noise."""
    return (0, 1, 1, 0, -1, 0, 1, -1)[k % 8]


def near_blob(p, blobs):
    return any(sum(((p[k] - c[k]) / r[k]) ** 2 for k in range(3)) < 1.0 for c, r in blobs)


def seg_dist(p, a, b):
    """Distance from p to segment a-b, and the position along it in px."""
    ab = [b[k] - a[k] for k in range(3)]
    ap = [p[k] - a[k] for k in range(3)]
    L2 = sum(v * v for v in ab)
    t = max(0.0, min(1.0, sum(ap[k] * ab[k] for k in range(3)) / L2))
    q = [a[k] + t * ab[k] for k in range(3)]
    return math.dist(p, q), t * math.sqrt(L2)


# Sickly mottling: greyer, bruised patches that wrap the form.
MOTTLES = [
    ((15.5, 40, -2), (1.5, 5, 3)), ((15.5, 37, 2), (1.5, 3, 3)),
    ((-12, 50, -12.5), (4, 2.5, 1.5)), ((-9, 52, -12.5), (2, 2, 1.5)),
    ((6, 66, 9.5), (4, 2.5, 1.5)),
    ((-23, 52, 4.5), (3, 4, 1.5)), ((-21, 49, 4.5), (2, 2, 1.5)),
]

# Warts: (position) of a raised pixel; a darker pixel sits under each.
WARTS = [(-6, 66.5, -22.5), (7.5, 71.5, -22.5), (9.5, 66.5, -18), (-3, 78.5, -14),
         (12, 44.5, -12.5), (-8, 38.5, -12.5), (-17.5, 60.5, -2), (28.5, 38.5, 1),
         (-21, 35.5, -6), (6, 55.5, -9.5), (-15.5, 44.5, 4), (10, 24.5, -4.5)]

# Scars: segments in 3D, crossed by crude stitches where marked.
SCARS = [
    # Across the blind left eye, from brow to cheek.
    ((-7.5, 77, -22.5), (-2.5, 64.5, -22.5), False),
    # A stitched gash across the gut.
    ((-10, 45, -14.5), (8, 38, -14.5), True),
    # Whip marks across the back.
    ((-12, 66, 9.5), (2, 56, 9.5), False), ((-3, 68, 9.5), (11, 58, 9.5), False),
    ((-8, 54, 9.5), (6, 48, 9.5), False),
    # A long stitched cut down the right upper arm, an old one on the scalp.
    ((27.5, 55, -2), (27.5, 46, 3), True), ((-6, 80, -18), (3, 80, -9), True),
]


def scar_at(p):
    """None, 'scar' or 'stitch' for a texel."""
    for a, b, stitched in SCARS:
        d, along = seg_dist(p, a, b)
        if d < 0.6:
            return "scar"
        if stitched and d < 1.6 and fi(along) % 3 == 0:
            return "stitch"
    return None


def wart_at(p):
    for w in WARTS:
        if math.dist(p, w) < 0.75:
            return "top"
        if math.dist(p, (w[0], w[1] - 1, w[2])) < 0.75:
            return "under"
    return None


def sash(e, p, f):
    """The rag sash slung from the left shoulder down across the chest and
    gut to the right hip (and the same band across the back)."""
    if e["name"] not in ("chest", "belly", "gut", "hump") or f in ("west", "east", "down"):
        return False
    x, y, z = p
    centre = -15 + (64 - y) * 0.93
    return abs(x - centre) < 2.5 + 0.5 * jag(fi(y))


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
    """Skin colour for a shade, with mottling, warts and scars on top."""
    s = scar_at(p)
    if s == "scar":
        return SCAR[clamp(v - 1, 0, 2)]
    if s == "stitch":
        return LEATHER[0]
    w = wart_at(p)
    if w == "top":
        return SKIN[clamp(v + 1)]
    if w == "under":
        return SKIN[clamp(v - 2)]
    if near_blob(p, MOTTLES):
        return MOTTLE[clamp(v)]
    return SKIN[clamp(v)]


def paint_skin(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    n = e["name"]
    if n == "gut" and f == "north":
        if y >= 46:
            v += 1                                 # the top of the gut catches the light
        elif y < 37:
            v -= 1                                 # and its underside sags into shadow
        if abs(x) < 1 and 40 <= y < 42:
            return SKIN[0]                         # navel
    if n == "chest" and f == "north":
        if y >= 63:
            v += 1                                 # collarbones catch the light
        if fi(y) == 55 and 2 <= abs(x) <= 14:
            v -= 1                                 # the shadow under the pecs
        if abs(x) < 1 and y > 52:
            v -= 1                                 # breastbone
        if y < 50:
            v -= 1                                 # shadow cast by the gut's top
        if 61 <= y < 62 and abs(x) < 11 and abs(abs(x) - 6) < 5:
            return LEATHER[1]                      # the necklace cord
    if n in ("chest", "belly") and f in ("west", "east") and y < 34:
        v -= 1
    if n == "hump" and f in ("up", "south") and abs(x) < 1 and (fi(z if f == "up" else y) % 3 == 0):
        v += 1                                     # knuckles of the spine
    if n.startswith("shoulder_") and f == "up":
        v = 4 if (i in (0, 1) or j in (0, 1)) else 3
    if n.startswith("arm_") and f in ("north", "west", "east"):
        if y < 46:
            v -= 1                                 # the inside of the elbow
    if n.startswith("forearm_"):
        if y > 43:
            v -= 1                                 # the elbow crease
        if f in ("north", "west", "east"):
            k = fi(z) if f != "north" else round(x)
            if (k + fi(y) // 3) % 9 == 0 and 31 <= y <= 41 and fi(y) % 4 != 0:
                v -= 1                             # veins, short and wavy
    if n.startswith("thigh_"):
        if f == "north" and ((y - 16) / 3) ** 2 + ((x - (8 if x > 0 else -8)) / 3.5) ** 2 < 1:
            v += 1                                 # knee cap
        if y > 26:
            v -= 1                                 # under the rags
    if sash(e, p, f):
        return RAG[clamp(v - (1 if fi(y) % 3 == 0 else 0))]
    return skin(p, v)


def paint_face(e, f, p, i, j, w, h):
    """The head. Front columns x (-9..9), rows y (62..79). The brow covers
    -8..8 at 72..74, the nose -2..2 at 67..71 and its tip -3..3 at 66..68.
    The right eye glows; the left one is blind and milky under a scar."""
    x, y, z = p
    c, r = round(x), fi(y)
    ac = abs(c)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if 3 <= ac <= 5 and r in (69, 70):
            if c > 0:                              # the glowing right eye
                if r == 70:
                    return GLOW[3] if c == 4 else GLOW[2]
                return GLOW[1] if c != 5 else GLOW[0]
            return MILKY[2] if (r == 70 and c == -4) else MILKY[1 if r == 70 else 0]
        if 3 <= ac <= 6 and r in (68, 71):
            return SKIN[0] if r == 71 else SKIN[1]  # deep sockets and bags
        if r in (64, 65) and ac <= 7:
            if r == 64:
                return MOUTH[0] if ac <= 6 else SKIN[1]   # the mouth line
            if ac in (1, 3) or ac == 6:
                return BONE[2]                     # crooked upper teeth
            if ac <= 6:
                return MOUTH[1]
        if r <= 63:
            v -= 1                                 # shadowed chin, behind the jaw
        if ac >= 7 and 65 <= r <= 69:
            v += 1                                 # cheekbones
    if f in ("west", "east"):
        if 70 <= r <= 73 and -16 < z < -12:
            v -= 1                                 # shadow round the ear stalk
        if r == 63 and z < -10:
            v -= 1
    return skin(p, v)


def paint_brow(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if abs(c) == 1:
            return SKIN[0]                         # the scowl's furrow
        if r == 72:
            v -= 1
    if f == "down":
        return SKIN[0]
    if f == "up" and abs(c) in range(2, 8) and (c + fi(z)) % 2 == 0:
        return SKIN[1]                             # bristling brow hair
    return skin(p, v)


def paint_nose(e, f, p, i, j, w, h):
    x, y, z = p
    c = round(x)
    v = base_shade(e, f, p, i, j)
    if e["name"] == "nose_tip":
        if f == "down" or (f == "north" and fi(y) == 66 and abs(c) in (1, 2)):
            return MOUTH[0] if f == "north" or abs(c) in (1, 2) else SKIN[0]   # nostrils
        if f == "north" and fi(y) == 68:
            v += 1
    return skin(p, v)


def paint_jaw(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "up":
        if z < -22.5:                              # lower teeth along the front rim
            return MOUTH[0] if c in (-3, 0, 4) else BONE[3]
        return MOUTH[1] if abs(c) < 6 else MOUTH[0]
    if f == "north":
        if r == 63:
            return MOUTH[0] if c in (-3, 0, 4) else BONE[3]
        if r == 62:
            return BONE[1] if c not in (-3, 0, 4) else MOUTH[0]
        if r <= 59:
            v -= 1
        if abs(c) <= 1 and r == 60:
            return SKIN[1]                         # cleft chin
    return skin(p, v)


def paint_tusk(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    if r <= 64:
        v -= 2                                     # stained at the root
    if r == 68 and f != "up":
        v -= 1
    if e["name"] == "tusk_left" and r >= 67 and f in ("up", "north"):
        return BONE[1]                             # chipped tip
    return BONE[clamp(v)]


def paint_ear(e, f, p, i, j, w, h):
    x, y, z = p
    v = base_shade(e, f, p, i, j)
    left = x < 0
    if e["name"].endswith("_end"):
        if (left and f == "west") or (not left and f == "east"):
            # The trumpet's mouth: dark inside, a lit rim. The left ear is torn.
            if left and fi(y) >= 72 and z < -14:
                return SKIN[clamp(v)]
            if i in (0, w - 1) or j in (0, h - 1):
                return SKIN[clamp(v + 1)]
            return MOUTH[1] if j == 1 or i == 1 else MOUTH[0]
    return skin(p, v)


def paint_fist(e, f, p, i, j, w, h):
    """Four thick fingers curled under big knuckles, yellowed nails, a thumb."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "north":
        if r >= 25:
            v += 1                                 # the knuckle ridge
            if i % 3 == 2:
                v -= 1
        elif 20 <= r <= 23 and i % 3 == 2:
            return SKIN[clamp(v - 2)]              # gaps between the curled fingers
        elif r == 24:
            v -= 1                                 # the crease under the knuckles
        if r <= 18 and i % 3 != 2:
            return BONE[1]                         # nails
    inner = (f == "west" and x > 0) or (f == "east" and x < 0)
    if inner and 19 <= r <= 24 and z < 1:
        v += 1                                     # the thumb over the fingers
    if f == "down":
        return SKIN[0]
    return skin(p, v)


def paint_shin(e, f, p, i, j, w, h):
    """Shins: grimier toward the ground, the ankles bound in rag."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if r <= 8:
        k = (round(x) if f in ("north", "south") else fi(z)) + r
        v2 = v - (1 if k % 3 == 0 else 0)
        return STAIN[clamp(v2 - 1, 0, 3)] if (r == 5 and k % 4 == 0) else RAG[clamp(v2)]
    if r <= 10:
        v -= 1                                     # grime
    return skin(p, v)


def paint_foot(e, f, p, i, j, w, h):
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if f == "down":
        return SKIN[0]
    if f == "north":
        k = i % 2 if i < w - 2 else 0              # three big toes and a small one
        if i in (2, 5, 8) or (i == w - 2):
            return SKIN[clamp(v - 2)]
        if r >= 3:
            return BONE[1 if r == 3 else 0] if k == 0 else BONE[1]   # yellowed toenails
        return skin(p, v - 1)
    if f == "up" and z < -6:
        if i in (2, 5, 8):
            return SKIN[1]
    v -= 1                                         # feet are filthy
    return skin(p, v)


def paint_rag(e, f, p, i, j, w, h):
    """Burlap: thread lines every few pixels, a sewn-on patch, blood stains,
    a hole showing skin, and frayed hems."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    n = e["name"]
    k = round(x) if f in ("north", "south", "up", "down") else fi(z)
    if f in ("north", "south", "west", "east") and j == h - 1:
        return RAG[0] if k % 2 else RAG[clamp(v - 1)]           # frayed hem
    if n.startswith("loincloth") and f == "north":
        if ((x - 2) / 2.5) ** 2 + ((y - 22) / 3) ** 2 < 1:
            return STAIN[clamp(v - 1, 0, 3)]       # dried blood
        if -5 <= x <= -2 and 25 <= y <= 28:
            if x in (-5, -2) or r in (25, 28):
                return LEATHER[0]                  # stitches round a patch
            return LEATHER[2] if (round(x) + r) % 2 else LEATHER[3]
    if n == "pelvis":
        if f in ("west", "east") and ((y - 29) / 1.5) ** 2 + ((z - 2) / 2) ** 2 < 1:
            return SKIN[1]                         # a hole showing skin
        if f == "south" and y < 28:
            v -= 1
    if n == "shoulder_rag" and f == "up" and (round(x) + fi(z)) % 5 == 0:
        return STAIN[2]
    if f in ("up", "down"):
        r = fi(z)                                  # on top, the threads run across the depth
    if r % 3 == 0 and (k + r) % 7 != 0:
        v -= 1                                     # coarse threads running across
    return RAG[clamp(v)]


def paint_leather(e, f, p, i, j, w, h):
    x, y, z = p
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    k = round(x) if f in ("north", "south") else fi(z)
    if f in ("north", "south", "west", "east") and fi(y) == 31 and k % 4 == 0:
        return IRON[3]                             # rivets
    if f != "up" and j == 0:
        v += 1
    if (k + fi(y)) % 7 == 0:
        v -= 1                                     # cracks
    return LEATHER[clamp(v, 0, 3)]


def paint_iron(e, f, p, i, j, w, h):
    """Rusty iron: buckle, shackle, chain."""
    x, y, z = p
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    k = (round(x * 2) + fi(y) * 3 + round(z * 2)) % 5
    if e["name"] == "buckle" and f == "north":
        if abs(round(x)) <= 1 and 30 < y < 33:
            return LEATHER[1]                      # the strap through the frame
    if e["name"] == "shackle" and f in ("west", "east", "north", "south") and fi(y) == 30 and k == 0:
        return IRON[3]                             # rivet heads
    if k == 1 and f != "up":
        return RUST[clamp(v - 1, 0, 2)]
    return IRON[clamp(v, 0, 3)]


def paint_bone(e, f, p, i, j, w, h):
    x, y, z = p
    c, r = round(x), fi(y)
    v = {"up": 4, "north": 3, "west": 3, "south": 2, "east": 2, "down": 1}[f]
    if e["name"] == "skull" and f == "north":
        if abs(c) == 1 and r == 55:
            return MOUTH[0]                        # eye sockets
        if r == 54:
            return BONE[1] if c != 0 else MOUTH[0] # teeth
    return BONE[clamp(v)]


def paint_wood(e, f, p, i, j, w, h):
    """The club's grip: dark wood wrapped in leather where the fist holds it."""
    x, y, z = p
    r = fi(y)
    v = {"up": 3, "north": 2, "west": 2, "south": 1, "east": 1, "down": 0}[f]
    if 18 <= r <= 27:
        return LEATHER[clamp(v - (1 if r % 2 else 0), 0, 3)]
    if (r + (round(x) if f in ("north", "south") else fi(z))) % 4 == 0:
        v -= 1                                     # grain
    return WOOD[clamp(v)]


def paint_clubhead(e, f, p, i, j, w, h):
    """Knotted wood with an iron band, splashed with old blood."""
    x, y, z = p
    r = fi(y)
    v = base_shade(e, f, p, i, j)
    if r in (8, 9):
        return IRON[clamp(v - 1, 0, 3)] if (round(x) + fi(z)) % 4 else RUST[1]
    if near_blob(p, [((27.5, 4, -1), (1.5, 2.5, 2.5)), ((22, 3, -4), (2.5, 2, 1.5)),
                     ((19.5, 6, 2), (1.5, 2, 2))]):
        return BLOOD[clamp(v - 1, 0, 2)]
    if ((round(x) - 23) ** 2 + (r - 5) ** 2) < 2 and f in ("north", "south"):
        return WOOD[1]                             # a knot
    if (r + (round(x) if f in ("north", "south") else fi(z))) % 5 == 0:
        v -= 1
    return WOOD[clamp(v)]


def paint_nail(e, f, p, i, j, w, h):
    return IRON[{"up": 3, "north": 3, "west": 2, "south": 1, "east": 1, "down": 0}[f]]


PAINTERS = {"skin": paint_skin, "face": paint_face, "brow": paint_brow, "nose": paint_nose,
            "jaw": paint_jaw, "tusk": paint_tusk, "ear": paint_ear, "fist": paint_fist,
            "shin": paint_shin, "foot": paint_foot, "rag": paint_rag, "leather": paint_leather,
            "iron": paint_iron, "bone": paint_bone, "wood": paint_wood,
            "clubhead": paint_clubhead, "nail": paint_nail}


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
# head and body forward, swings a foot backward, opens the jaw; a negative x
# raises an arm forward and up and bends the elbow.
ANIMATIONS = {
    # Heavy breathing, a slack jaw, a slow lolling head, arms swaying with the
    # breath, a twitch of the good ear.
    "idle": {"loop": "loop", "length": 3.0, "bones": {
        "body": track("scale", [(0, (1, 1, 1)), (1.5, (1.02, 1.025, 1.02)), (3.0, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.75, (3, 5, 3)), (1.5, (5, 0, 0)), (2.25, (3, -5, -3)),
                    (3.0, (0, 0, 0))),
        "jaw": rot((0, (2, 0, 0)), (1.5, (8, 0, 0)), (3.0, (2, 0, 0))),
        "arm_right": sway(3.0, 3, 0.1, 0),
        "arm_left": sway(3.0, 3, 0.35, 0),
        "forearm_right": rot((0, (-4, 0, 0)), (1.5, (-7, 0, 0)), (3.0, (-4, 0, 0))),
        "forearm_left": rot((0, (-5, 0, 0)), (1.5, (-8, 0, 0)), (3.0, (-5, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (2.0, (0, 0, 0)), (2.1, (0, 0, 12)), (2.25, (0, 0, -4)),
                         (2.4, (0, 0, 0)), (3.0, (0, 0, 0))),
        "loincloth": sway(3.0, 2, 0.2, 0),
    }},
    # A lumbering stomp: alternate legs, opposite arms, a big side-to-side roll,
    # the gut and head lagging, the club swinging from the fist.
    "walk": {"loop": "loop", "length": 1.6, "bones": {
        "leg_right": rot((0, (-22, 0, 0)), (0.8, (22, 0, 0)), (1.6, (-22, 0, 0))),
        "leg_left": rot((0, (22, 0, 0)), (0.8, (-22, 0, 0)), (1.6, (22, 0, 0))),
        "arm_right": rot((0, (14, 0, 0)), (0.8, (-14, 0, 0)), (1.6, (14, 0, 0))),
        "arm_left": rot((0, (-16, 0, 0)), (0.8, (16, 0, 0)), (1.6, (-16, 0, 0))),
        "forearm_left": rot((0, (-12, 0, 0)), (0.8, (-4, 0, 0)), (1.6, (-12, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.4, (0, 1.2, 0)), (0.8, (0, 0, 0)),
                                   (1.2, (0, 1.2, 0)), (1.6, (0, 0, 0))])
        + rot((0, (4, -4, 4)), (0.8, (4, 4, -4)), (1.6, (4, -4, 4))),
        "head": rot((0, (0, 3, -3)), (0.4, (4, 0, 0)), (0.8, (0, -3, 3)), (1.2, (4, 0, 0)),
                    (1.6, (0, 3, -3))),
        "club": sway(1.6, 8, 0.15, 0),
        "loincloth": sway(1.6, 8, 0.1, 0),
    }},
    # Charge: leaning in hard, long strides, arms pumping with bent elbows.
    "run": {"loop": "loop", "length": 0.9, "bones": {
        "leg_right": rot((0, (-35, 0, 0)), (0.45, (32, 0, 0)), (0.9, (-35, 0, 0))),
        "leg_left": rot((0, (32, 0, 0)), (0.45, (-35, 0, 0)), (0.9, (32, 0, 0))),
        "arm_right": rot((0, (30, 0, 0)), (0.45, (-30, 0, 0)), (0.9, (30, 0, 0))),
        "arm_left": rot((0, (-30, 0, 0)), (0.45, (30, 0, 0)), (0.9, (-30, 0, 0))),
        "forearm_right": rot((0, (-30, 0, 0)), (0.9, (-30, 0, 0))),
        "forearm_left": rot((0, (-45, 0, 0)), (0.9, (-45, 0, 0))),
        "body": track("position", [(0, (0, 0, 0)), (0.225, (0, 2, 0)), (0.45, (0, 0, 0)),
                                   (0.675, (0, 2, 0)), (0.9, (0, 0, 0))])
        + rot((0, (12, -5, 3)), (0.45, (12, 5, -3)), (0.9, (12, -5, 3))),
        "head": rot((0, (-8, 0, 0)), (0.225, (-4, 0, 0)), (0.45, (-8, 0, 0)), (0.675, (-4, 0, 0)),
                    (0.9, (-8, 0, 0))),
        "jaw": rot((0, (12, 0, 0)), (0.9, (12, 0, 0))),
        "club": rot((0, (-20, 0, 0)), (0.45, (10, 0, 0)), (0.9, (-20, 0, 0))),
        "loincloth": rot((0, (-20, 0, 0)), (0.45, (-10, 0, 0)), (0.9, (-20, 0, 0))),
    }},
    # Overhead club smash: rear back with the club raised high (anticipation),
    # bring it down hard with the whole body, hold the impact, recover.
    "attack": {"loop": "once", "length": 1.4, "bones": {
        "arm_right": rot((0, (0, 0, 0)), (0.55, (-165, 0, -10)), (0.75, (-30, 0, 0)),
                         (0.95, (-25, 0, 0)), (1.4, (0, 0, 0))),
        "forearm_right": rot((0, (0, 0, 0)), (0.55, (-40, 0, 0)), (0.75, (0, 0, 0)), (1.4, (0, 0, 0))),
        "club": rot((0, (0, 0, 0)), (0.55, (-20, 0, 0)), (0.75, (15, 0, 0)), (1.4, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.55, (25, 0, -15)), (0.75, (-20, 0, -10)), (1.4, (0, 0, 0))),
        "body": rot((0, (0, 0, 0)), (0.55, (-12, 10, 0)), (0.75, (20, -5, 0)), (0.95, (18, -4, 0)),
                    (1.4, (0, 0, 0)))
        + track("position", [(0, (0, 0, 0)), (0.55, (0, 1, 1.5)), (0.75, (0, -2, -3)),
                             (0.95, (0, -2, -3)), (1.4, (0, 0, 0))]),
        "head": rot((0, (0, 0, 0)), (0.55, (-15, 0, 0)), (0.75, (10, 0, 0)), (1.4, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.55, (20, 0, 0)), (0.75, (5, 0, 0)), (1.4, (0, 0, 0))),
        "leg_right": rot((0, (0, 0, 0)), (0.55, (8, 0, 0)), (0.75, (-15, 0, 0)), (1.4, (0, 0, 0))),
        "leg_left": rot((0, (0, 0, 0)), (0.55, (-6, 0, 0)), (0.75, (12, 0, 0)), (1.4, (0, 0, 0))),
    }},
    # Hit: knocked back, head snapped aside, arms flung out, jaw dropped.
    "hit": {"loop": "once", "length": 0.5, "bones": {
        "body": rot((0, (0, 0, 0)), (0.09, (-10, 6, 0)), (0.25, (3, -2, 0)), (0.5, (0, 0, 0)))
        + track("position", [(0, (0, 0, 0)), (0.09, (0, 0, 2)), (0.5, (0, 0, 0))]),
        "head": rot((0, (0, 0, 0)), (0.09, (-16, 14, 8)), (0.25, (4, -3, -2)), (0.5, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.09, (16, 0, 0)), (0.5, (0, 0, 0))),
        "arm_right": rot((0, (0, 0, 0)), (0.09, (-15, 0, 18)), (0.5, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.09, (-15, 0, -18)), (0.5, (0, 0, 0))),
        "loincloth": rot((0, (0, 0, 0)), (0.09, (-15, 0, 0)), (0.3, (6, 0, 0)), (0.5, (0, 0, 0))),
    }},
    # Roar: head thrown back, jaw wide, arms spread and fists shaking.
    "roar": {"loop": "once", "length": 2.2, "bones": {
        "body": rot((0, (0, 0, 0)), (0.4, (6, 0, 0)), (0.7, (-14, 0, 0)), (1.7, (-12, 0, 0)),
                    (2.2, (0, 0, 0)))
        + track("scale", [(0, (1, 1, 1)), (0.4, (1.02, 0.98, 1.02)), (0.7, (1.03, 1.03, 1.03)),
                          (1.7, (1.03, 1.03, 1.03)), (2.2, (1, 1, 1))]),
        "head": rot((0, (0, 0, 0)), (0.4, (10, 0, 0)), (0.7, (-25, 0, 0)), (1.0, (-22, 4, 0)),
                    (1.3, (-25, -4, 0)), (1.7, (-22, 0, 0)), (2.2, (0, 0, 0))),
        "jaw": rot((0, (0, 0, 0)), (0.4, (4, 0, 0)), (0.7, (38, 0, 0)), (1.7, (35, 0, 0)),
                   (2.2, (0, 0, 0))),
        "arm_right": rot((0, (0, 0, 0)), (0.7, (-40, 0, 40)), (1.0, (-45, 0, 38)), (1.3, (-40, 0, 42)),
                         (1.7, (-42, 0, 40)), (2.2, (0, 0, 0))),
        "arm_left": rot((0, (0, 0, 0)), (0.7, (-40, 0, -40)), (1.0, (-45, 0, -38)),
                        (1.3, (-40, 0, -42)), (1.7, (-42, 0, -40)), (2.2, (0, 0, 0))),
        "forearm_right": rot((0, (0, 0, 0)), (0.7, (-50, 0, 0)), (1.7, (-50, 0, 0)), (2.2, (0, 0, 0))),
        "forearm_left": rot((0, (0, 0, 0)), (0.7, (-50, 0, 0)), (1.7, (-50, 0, 0)), (2.2, (0, 0, 0))),
        "ear_right": rot((0, (0, 0, 0)), (0.7, (0, 0, 15)), (1.7, (0, 0, 15)), (2.2, (0, 0, 0))),
        "ear_left": rot((0, (0, 0, 0)), (0.7, (0, 0, -10)), (1.7, (0, 0, -10)), (2.2, (0, 0, 0))),
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
    cx, cyy = size[0] / 2, size[1] * 0.92
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
    for tex in (128, 256):
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

    tex_png = out_dir / "ogre.png"
    img.save(tex_png)

    # ------------------------------------------------------------ previews
    # Front-left, front-right, back-left, left side, front (the ogre faces -z).
    views = [(-145, 15), (145, 15), (-35, 15), (-90, 0), (180, 0)]
    tiles = [render(img, places, yw, pt, 3.6, (360, 330)) for yw, pt in views]
    sheet = Image.new("RGBA", (360 * len(tiles), 330), (176, 196, 222, 255))
    for k, t in enumerate(tiles):
        sheet.alpha_composite(t, (360 * k, 0))
    sheet.save(out_dir / "ogre_preview.png")
    sil = Image.new("RGBA", (720, 330), (235, 235, 235, 255))
    sil.alpha_composite(render(img, places, -145, 15, 3.6, (360, 330), True), (0, 0))
    sil.alpha_composite(render(img, places, -90, 0, 3.6, (360, 330), True), (360, 0))
    sil.save(out_dir / "ogre_silhouette.png")

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
        "from": [18, 0, -2], "to": [22, 18, 2], "autouv": 0, "color": 1,
        "origin": [20, 0, 0],
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
        group("ogre"),
        {"name": "scale_dummy", "origin": [20, 0, 0], "rotation": [0, 0, 0], "color": 0,
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
        "name": "ogre", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": tex, "height": tex},
        "elements": elements, "outliner": outliner, "textures": [texture],
        "animations": animations,
    }
    (out_dir / "ogre.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(ELEMENTS)}  bones: {len(BONES)}  visible faces: {len(visible)}  "
          f"texture: {tex}x{tex}  texels used: {used}/{tex * tex}  "
          f"animations: {', '.join(ANIMATIONS)}")


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
