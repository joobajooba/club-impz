"""Build the oak: a world tree as a Blockbench model, at the HD Imp's scale and
texture density (D-117, D-118).

- 3 times the Imp's height: 222 px = 3.47 m (the Imp is 74 px, 1.156 m).
  Geometry in 0.25-unit steps ("px"), 64 px per metre, the same as
  build_impling_hd_bbmodel.py.
- Texture SUB = 2 times finer: 8 texture pixels per Blockbench unit, 128 per
  metre (D-118). The UVs stay in px, so Blockbench maps every box the same.
- A broad, lumpy oak crown: nine rounded leaf clusters (a core box with a
  slab on each side and a cap top and bottom), leaf tufts on their sides and
  leaf clumps hanging under them. A thick trunk in three bevelled sections,
  flaring into eight roots; four main limbs, two smaller ones, a low side
  branch with its own leaf clump and a sawn-off stub.
- Painted, not modelled, detail: furrowed oak bark (ridges split by deep
  fissures and broken into plates), knots, a hollow, moss on the roots and
  the north side, pale lichen, end grain on the stub; overlapping lobed oak
  leaves in hue-shifted greens with a midrib and a lit half, a deeper leaf
  layer showing through the gaps, some warmer yellow leaves and a few acorns.
  Baked light from the shape each part stands for (round crown, round trunk),
  ambient occlusion sampled from the real geometry, lit top edges.

Painting is vectorised with numpy: the oak has around 50 times the texels of
the HD Imp, too many for the per-texel painter in bbcreature.py.

Usage: python build_oak_bbmodel.py [out_dir]   (writes oak.bbmodel, oak.png,
oak_preview.png, oak_silhouette.png and oak_render.png)
"""

import json
import math
import random
import sys
import time
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "creatures"))
import bbcreature  # noqa: E402
from bbcreature import NORMAL, corners, el, hexrgb, tangents  # noqa: E402
from bbcreature import face_frame, pack  # noqa: E402
from bbcreature import Creature  # noqa: E402

# The HD Imp's scale (build_impling_hd_bbmodel.py), kept here so the oak
# doesn't depend on that script.
PX_HD = 0.25            # Blockbench units per px of geometry
SUB = 2                 # texture pixels per px: 8 per unit, 128 per metre (D-118)
IMP_HEIGHT_PX = 74      # 1.156 m, the scale dummy's height
HEIGHT_PX = 3 * IMP_HEIGHT_PX   # 222 px, 3.47 m


def ramp(*cs):
    return np.array([hexrgb(c)[:3] for c in cs], float)


# Ramps, darkest first: shadows lean purple or blue, highlights lean warm.
BARK = ramp("#1e1219", "#35212a", "#4f3230", "#6d4936", "#8c623f", "#ad8150", "#cfa56c")
WOOD = ramp("#4a2c22", "#7a5236", "#a9794b", "#cfa46f", "#ead0a0")           # end grain
MOSS = ramp("#16301f", "#2a5229", "#46762e", "#6c9a35", "#9cc04a", "#c9e07a")
LICHEN = ramp("#6f7d68", "#97a58a", "#bfcaa6", "#dfe6c6")
LEAF = ramp("#082022", "#0f3a2c", "#1b5a30", "#2f7a33", "#509b38", "#7fbd45", "#b4dc66", "#e0f39a")
LEAF_WARM = ramp("#18301e", "#33522a", "#58782d", "#86a035", "#b4c44a", "#dbe27a", "#f4f1a8")
ACORN = ramp("#3b2414", "#6a4422", "#9b6b34", "#c79a52", "#e8c47c")
CAP = ramp("#2a1c14", "#4d3624", "#73563a", "#98794f")


# ---------------------------------------------------------------- geometry

def rbox(name, bone, part, lo, hi, b, rot=None, origin=None, **extra):
    """A box with its four long edges bevelled b px: a core the full depth,
    and a slab b px thick on each side, set in by b front and back."""
    (x0, y0, z0), (x1, y1, z1) = lo, hi
    out = [el(name, bone, part, (x0 + b, y0, z0), (x1 - b, y1, z1), rot, origin),
           el(f"{name}_r", bone, part, (x1 - b, y0, z0 + b), (x1, y1, z1 - b), rot, origin),
           el(f"{name}_l", bone, part, (x0, y0, z0 + b), (x0 + b, y1, z1 - b), rot, origin)]
    centre = [(lo[k] + hi[k]) / 2 for k in range(3)]
    half = [(hi[k] - lo[k]) / 2 for k in range(3)]
    for e in out:
        e.update(extra, tube=(centre, half))
    return out


def limb(name, base, rx, rz, length, width, b, **extra):
    """A bevelled branch standing on base, turned rx (towards +z) and rz
    (negative leans to +x) degrees, reaching 4 px back into what it grows
    from. Returns its boxes and where its tip is."""
    x, y, z = base
    w = width / 2
    a, c = math.radians(rx), math.radians(rz)
    d = (-math.sin(c) * math.cos(a), math.cos(c) * math.cos(a), math.sin(a))
    boxes = rbox(name, "trunk", "bark", (x - w, y - 4, z - w), (x + w, y + length, z + w), b,
                 rot=(rx, 0, rz), origin=base, axis=1, **extra)
    return boxes, tuple(base[k] + length * d[k] for k in range(3))


def blob(name, centre, size, b):
    """A rounded leaf cluster: a core, a slab each side, a cap top and bottom."""
    (cx, cy, cz), (sx, sy, sz) = centre, size
    x0, y0, z0 = cx - sx / 2, cy - sy / 2, cz - sz / 2
    x1, y1, z1 = cx + sx / 2, cy + sy / 2, cz + sz / 2
    boxes = [el(name, "crown", "leaves", (x0 + b, y0 + b, z0), (x1 - b, y1 - b, z1)),
             el(f"{name}_r", "crown", "leaves", (x1 - b, y0 + b, z0 + b), (x1, y1 - b, z1 - b)),
             el(f"{name}_l", "crown", "leaves", (x0, y0 + b, z0 + b), (x0 + b, y1 - b, z1 - b)),
             el(f"{name}_top", "crown", "leaves", (x0 + b, y1 - b, z0 + b), (x1 - b, y1, z1 - b)),
             el(f"{name}_bot", "crown", "leaves", (x0 + b, y0, z0 + b), (x1 - b, y0 + b, z1 - b))]
    rng = random.Random(name)
    ball = (centre, (sx / 2, sy / 2, sz / 2))
    # Tufts: small clumps pushing out of the sides (and the top of the low
    # clusters), so the outline is lumpy instead of a clean box.
    sides = ["east", "west", "north", "south"] + (["up"] if cy < 170 else [])
    for k in range(4):
        side = sides[(k + rng.randrange(len(sides))) % len(sides)]
        tw, th, td = rng.choice((10, 12, 14)), rng.choice((8, 10, 12)), rng.choice((10, 12, 14))
        out = rng.choice((3, 4, 5))
        u = rng.uniform(-0.25, 0.25)
        v = rng.uniform(-0.2, 0.25)
        if side in ("east", "west"):
            s = 1 if side == "east" else -1
            fx = cx + s * (sx / 2 + out - td / 2)
            lo = (fx - td / 2, cy + v * sy - th / 2, cz + u * sz - tw / 2)
            hi = (fx + td / 2, cy + v * sy + th / 2, cz + u * sz + tw / 2)
        elif side in ("north", "south"):
            s = 1 if side == "south" else -1
            fz = cz + s * (sz / 2 + out - td / 2)
            lo = (cx + u * sx - tw / 2, cy + v * sy - th / 2, fz - td / 2)
            hi = (cx + u * sx + tw / 2, cy + v * sy + th / 2, fz + td / 2)
        else:
            fy = y1 + out - th / 2
            lo = (cx + u * sx - tw / 2, fy - th / 2, cz + v * sz - td / 2)
            hi = (cx + u * sx + tw / 2, fy + th / 2, cz + v * sz + td / 2)
        # Snap the corner to half px and keep the size whole.
        lo = [round(c * 2) / 2 for c in lo]
        hi = [lo[i] + round(hi[i] - lo[i]) for i in range(3)]
        boxes.append(el(f"{name}_tuft{k}", "crown", "leaves", lo, hi))
    # Clumps hanging under the bottom cap.
    for k in range(2):
        w = rng.choice((8, 10, 12))
        hang = rng.choice((5, 6, 8))
        ux = cx + rng.uniform(-0.3, 0.3) * (sx - 2 * b)
        uz = cz + rng.uniform(-0.3, 0.3) * (sz - 2 * b)
        lo = (round(ux - w / 2), y0 - hang, round(uz - w / 2))
        boxes.append(el(f"{name}_hang{k}", "crown", "leaves", lo, (lo[0] + w, y0 + 3, lo[2] + w)))
    for e in boxes:
        e["ball"] = ball
    return boxes


TRUNK = [
    *rbox("trunk_base", "trunk", "bark", (-16, 0, -16), (16, 28, 16), 6, axis=1),
    *rbox("trunk_mid", "trunk", "bark", (-14, 28, -14), (14, 62, 14), 5, axis=1),
    *rbox("trunk_top", "trunk", "bark", (-12, 62, -12), (12, 100, 12), 4, axis=1),
    *rbox("leader", "trunk", "bark", (-9, 96, -9), (9, 170, 9), 3, axis=1),
]


def root(name, length, height, ry, inner=8, width=8):
    """A root along +x turned ry degrees about the trunk, in two steps that
    drop toward the ground."""
    w = width / 2
    return [el(name, "trunk", "bark", (inner, 0, -w), (inner + length, height, w), (0, ry, 0), (0, 0, 0)),
            el(f"{name}_end", "trunk", "bark", (inner + length, 0, -w + 1),
               (inner + length + length // 2, height // 2, w - 1), (0, ry, 0), (0, 0, 0)),
            el(f"{name}_top", "trunk", "bark", (inner, height, -w + 2),
               (inner + length // 2 + 2, height + 4, w - 2), (0, ry, 0), (0, 0, 0))]


ROOTS = [b for r in (root("root_e", 22, 12, 0, width=12), root("root_n", 20, 11, 90, width=12),
                     root("root_w", 18, 10, 180, width=10), root("root_s", 20, 12, -90, width=12),
                     root("root_ne", 18, 8, 45, width=10), root("root_sw", 20, 9, -135, width=10))
         for b in r]
for _e in ROOTS:
    _e["axis"] = 0

LIMBS, TIPS = [], {}
for _name, _base, _rx, _rz, _len, _w, _b in (
        ("limb_e", (6, 88, 2), 0, -48, 60, 14, 3),
        ("limb_w", (-6, 92, -2), 0, 44, 58, 13, 3),
        ("limb_n", (2, 90, -6), -46, 0, 58, 12, 3),
        ("limb_s", (-2, 94, 6), 42, 6, 56, 12, 3),
        ("limb_se", (6, 98, 6), 40, -42, 56, 9, 2),
        ("limb_nw", (-6, 100, -6), -42, 40, 54, 9, 2),
        ("branch_low", (-8, 62, 4), 8, 62, 60, 8, 2)):
    _boxes, TIPS[_name] = limb(_name, _base, _rx, _rz, _len, _w, _b)
    LIMBS += _boxes
# A sawn-off stub low on the north side, its end grain showing.
_stub, _ = limb("stub", (2, 40, -8), -70, -10, 14, 8, 2, stub=True)
LIMBS += _stub

CROWN = [b for args in (
    ("crown_top", (0, 192, 2), (104, 60, 98), 12),
    ("crown_e", (54, 152, 8), (82, 56, 80), 11),
    ("crown_w", (-52, 150, -6), (80, 54, 76), 11),
    ("crown_n", (6, 154, -50), (86, 56, 70), 11),
    ("crown_s", (-8, 156, 48), (82, 58, 72), 11),
    ("crown_ne", (42, 172, -40), (58, 46, 56), 9),
    ("crown_sw", (-42, 174, 40), (60, 44, 56), 9),
    ("crown_nw", (-46, 132, -44), (52, 40, 50), 8),
    ("crown_se", (46, 130, 44), (54, 40, 50), 8),
    ("crown_low", (-74, 96, 12), (34, 26, 32), 6)) for b in blob(*args)]

ELEMENTS = TRUNK + ROOTS + LIMBS + CROWN

BONES = {
    "oak": (None, (0, 0, 0), (0, 0, 0)),
    "trunk": ("oak", (0, 0, 0), (0, 0, 0)),
    "crown": ("trunk", (0, 100, 0), (0, 0, 0)),
}

# Bark features, in world px: knots (centre, radius) and the hollow.
KNOTS = [((-5, 47, -14), 3.2), ((12, 80, 3), 2.6), ((-16, 17, -4), 3.0), ((4, 118, 9), 2.2)]
HOLLOW = ((3, 76, 12), (4.2, 6.0))


# ---------------------------------------------------------------- noise

def hash3(x, y, z, seed=0.0):
    """Deterministic noise in 0..1, vectorised."""
    v = np.sin(x * 12.9898 + y * 78.233 + z * 37.719 + seed * 4.581) * 43758.5453
    return v - np.floor(v)


def vnoise2(x, y, seed=0.0):
    ix, iy = np.floor(x), np.floor(y)
    fx, fy = x - ix, y - iy
    ux, uy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = hash3(ix, iy, seed), hash3(ix + 1, iy, seed)
    c, d = hash3(ix, iy + 1, seed), hash3(ix + 1, iy + 1, seed)
    return (a + (b - a) * ux) * (1 - uy) + (c + (d - c) * ux) * uy


def vnoise3(q, seed=0.0):
    x, y, z = q[:, 0], q[:, 1], q[:, 2]
    i = [np.floor(x), np.floor(y), np.floor(z)]
    f = [x - i[0], y - i[1], z - i[2]]
    u = [t * t * (3 - 2 * t) for t in f]
    out = 0.0
    for dx in (0, 1):
        for dy in (0, 1):
            for dz in (0, 1):
                w = ((u[0] if dx else 1 - u[0]) * (u[1] if dy else 1 - u[1]) * (u[2] if dz else 1 - u[2]))
                out = out + w * hash3(i[0] + dx, i[1] + dy, i[2] + dz + seed * 17.0, seed)
    return out


def fbm3(q, seed=0.0, octaves=3):
    v, a, s = 0.0, 0.5, 1.0
    for k in range(octaves):
        v = v + a * vnoise3(q * s, seed + k)
        a, s = a * 0.5, s * 2.03
    return v / (1 - 0.5 ** octaves)


def grad(stops, v):
    """Colours at v (0..1) along a ramp, interpolated, vectorised."""
    v = np.clip(v, 0.0, 1.0) * (len(stops) - 1)
    k = np.minimum(v.astype(int), len(stops) - 2)
    t = (v - k)[:, None]
    return stops[k] + (stops[k + 1] - stops[k]) * t


def light(n):
    """Baked light from world normals (N, 3): from the top, slightly front-left."""
    return 0.38 + 0.32 * n[:, 1] - 0.16 * n[:, 2] - 0.16 * n[:, 0]


def unit(v):
    return v / np.maximum(np.linalg.norm(v, axis=-1, keepdims=True), 1e-6)


def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0.0, 1.0)
    return t * t * (3 - 2 * t)


# ---------------------------------------------------------------- painting

class Face:
    """Everything the painters need about the texels of one face, as arrays."""


def leaf_layer(a, b, cell, seed, hanging):
    """Overlapping lobed oak leaves on a jittered grid in face coordinates
    (a, b) px. Returns covered, leaf id (0..1), t (-1 stem .. 1 tip), lv / half
    width (-1..1 across) and lv in px."""
    n = a.shape[0]
    best = np.full(n, -1.0)
    lid, tt, across, lvpx = np.zeros(n), np.zeros(n), np.zeros(n), np.zeros(n)
    ia, ib = np.floor(a / cell), np.floor(b / cell)
    for da in (-1, 0, 1):
        for db in (-1, 0, 1):
            ca, cb = ia + da, ib + db
            h = [hash3(ca, cb, seed + 3.1 * k, seed) for k in range(6)]
            cx = (ca + 0.15 + 0.7 * h[0]) * cell
            cy = (cb + 0.15 + 0.7 * h[1]) * cell
            s = cell * (1.3 + 0.45 * h[2])
            th = (-math.pi / 2 + (h[3] - 0.5) * 2.0) if hanging else h[3] * 2 * math.pi
            dx, dy = a - cx, b - cy
            lu = dx * np.cos(th) + dy * np.sin(th)
            lv = -dx * np.sin(th) + dy * np.cos(th)
            t = lu / (0.5 * s)
            # Wider toward the tip, five rounded lobes down each side.
            hw = s * 0.29 * np.sqrt(np.clip(1 - t * t, 0, 1)) * (0.82 + 0.18 * t) \
                * (1 + 0.3 * np.cos(t * math.pi * 3.2 + 0.6))
            inside = (np.abs(t) < 1) & (np.abs(lv) < hw)
            upd = inside & (h[4] > best)
            best = np.where(upd, h[4], best)
            lid = np.where(upd, h[5], lid)
            tt = np.where(upd, t, tt)
            across = np.where(upd, lv / np.maximum(hw, 1e-6), across)
            lvpx = np.where(upd, lv, lvpx)
    return best >= 0, lid, tt, across, lvpx


def face_coords(F):
    """2D world coordinates on a face, b up the face for side faces."""
    q, k = F.q, int(np.argmax(np.abs(F.n)))
    if k == 1:
        return q[:, 0], q[:, 2], False
    return (q[:, 2] if k == 0 else q[:, 0]), q[:, 1], True


def paint_leaves(F):
    q = F.q
    c, r = F.e["ball"]
    bn = unit((q - np.array(c)) / np.array(r) ** 2)
    nmix = unit(0.62 * bn + 0.38 * np.array(F.n))
    v = light(nmix) + 0.06
    v -= 0.5 * F.ao
    v += 0.1 * np.clip((q[:, 1] - 150) / 70, -1, 1)          # the lower crown sits in shade
    v += 0.07 * F.edge
    if F.f == "down":
        v -= 0.12
    a, b, side = face_coords(F)
    # Low-frequency patches: sunny warm areas and deeper cool ones.
    patch = fbm3(q * 0.035, 7.0, 2)
    warm_patch = smooth(0.55, 0.75, patch + 0.15 * np.array(F.n)[1])

    # The deep layer behind: bigger, darker leaves that show through the gaps.
    dcov, did, dt, dac, _ = leaf_layer(a, b, 8.0, 11.0, side)
    deep = v - 0.3 + 0.05 * (did - 0.5) - 0.06 * (np.abs(dac) > 0.8)
    deep = np.where(dcov, deep, v - 0.42)
    # The front layer.
    cov, lid, t, ac, lvpx = leaf_layer(a, b, 5.0, 3.0, side)
    fv = v + 0.12 * (lid - 0.5)
    fv += np.where(ac > 0, 0.045, -0.045)                     # each leaf folds: one half lit
    fv -= 0.08 * ((np.abs(lvpx) < 0.3) & (np.abs(t) < 0.85))  # the midrib
    fv -= 0.1 * (np.abs(ac) > 0.8)                            # a darker rim
    fv += 0.035 * (t > 0.45)                                  # tips catch the light
    v = np.where(cov, fv, deep)
    v += 0.02 * (hash3(q[:, 0] * 2, q[:, 1] * 2, q[:, 2] * 2) - 0.5)
    col = grad(LEAF, v)
    # Some warmer leaves: whole leaves at random, more in the sunny patches.
    warm = np.where(cov, (lid < 0.14) * 0.55 + warm_patch * 0.35, warm_patch * 0.15)
    col = col * (1 - warm[:, None]) + grad(LEAF_WARM, v - 0.02) * warm[:, None]

    # Acorns, now and then, hanging on the side faces.
    if side:
        cell = 13.0
        ca, cb = np.floor(a / cell), np.floor(b / cell)
        pick = hash3(ca, cb, 41.0) < 0.1
        ax = (ca + 0.3 + 0.4 * hash3(ca, cb, 42.0)) * cell
        ay = (cb + 0.3 + 0.4 * hash3(ca, cb, 43.0)) * cell
        for off in (0.0, 2.6 * (hash3(ca, cb, 44.0) > 0.5)):  # sometimes a pair
            dx, dy = a - ax - off, b - ay + 0.6 * (off > 0)
            nut = pick & ((dx / 1.25) ** 2 + ((dy + 0.4) / 1.6) ** 2 <= 1) & (dy < 0.4)
            cap = pick & ((dx / 1.45) ** 2 + ((dy - 0.5) / 1.0) ** 2 <= 1) & (dy >= 0.2)
            av = 0.5 + 0.25 * (-dx / 1.25) + 0.15 * (dy / 1.6) - 0.5 * F.ao
            col = np.where(nut[:, None], grad(ACORN, av), col)
            cv = 0.45 + 0.12 * np.sin(dx * 5.0) * np.sin(dy * 5.0) - 0.5 * F.ao
            col = np.where(cap[:, None], grad(CAP, cv), col)
    return col


def bark_frame(F):
    """(along, around) px for the bark pattern, in the box's own frame."""
    p, ax = F.p, F.e["axis"]
    nl = NORMAL[F.f]
    others = [k for k in range(3) if k != ax]
    if nl[ax]:                                     # an end face: no long axis on it
        return p[:, others[1]], p[:, others[0]]
    around = [k for k in others if not nl[k]][0]
    return p[:, ax], p[:, around]


def tube_normal(F):
    """Normals of the round trunk or limb a bevelled box stands for."""
    centre, half = F.e["tube"]
    ax = F.e["axis"]
    nl = np.array(NORMAL[F.f], float)
    if nl[ax]:
        return np.repeat(np.array(F.n)[None, :], len(F.p), 0)
    d = (F.p - np.array(centre)) / np.maximum(np.array(half), 1)
    d[:, ax] = 0
    d = d + 0.6 * nl
    return unit(d @ F.e["M"][:3, :3].T)


def paint_bark(F):
    q, e = F.q, F.e
    n = np.array(F.n)
    nn = tube_normal(F) if "tube" in e else np.repeat(n[None, :], len(q), 0)
    base = light(nn)
    base -= 0.45 * F.ao
    base += 0.06 * F.edge
    base -= 0.2 * np.clip(1 - q[:, 1] / 8, 0, 1)            # into the ground
    along, around = bark_frame(F)
    seed = hash3(np.array(float(F.ei)), 1.0, 2.0) * 50
    around = around + seed

    if e.get("stub") and NORMAL[F.f][1] == 1:
        # Sawn end grain: rings round the pith, a bark rim, a crack.
        lo, hi = e["lo"], e["hi"]
        r = np.hypot(F.p[:, 0] - (lo[0] + hi[0]) / 2, F.p[:, 2] - (lo[2] + hi[2]) / 2)
        rim = r > (hi[0] - lo[0]) / 2 - 1.0
        v = 0.55 + 0.1 * np.sin(r * 3.4) - 0.12 * (r < 0.6) - 0.3 * F.ao
        v -= 0.25 * ((np.abs(F.p[:, 0] - (lo[0] + hi[0]) / 2 - 0.3 * (F.p[:, 2] - lo[2])) < 0.35) & (r > 1))
        col = grad(WOOD, v)
        return np.where(rim[:, None], grad(BARK, base - 0.05), col)

    # Oak bark: ridges up the trunk split by deep fissures, broken into plates.
    warp = 2.2 * (vnoise2(along * 0.06, around * 0.12, 5.0) - 0.5) + \
        0.8 * (vnoise2(along * 0.2, around * 0.3, 6.0) - 0.5)
    sw = around + warp
    W = 3.8
    col_i = np.floor(sw / W)
    fr = sw / W - col_i
    L = 8 + 8 * hash3(col_i, 3.0, seed)
    off = hash3(col_i, 4.0, seed) * L
    segf = (along + off) / L
    seg = np.floor(segf)
    g = segf - seg
    fiss = np.minimum(fr, 1 - fr)
    width = 0.12 + 0.07 * hash3(col_i, seg, seed + 1)
    v = base + 0.11 * (np.sin(fr * math.pi) - 0.6)           # rounded ridges
    v += 0.07 * (g - 0.5)                                     # each plate lit along its top
    v += 0.05 * (hash3(col_i, seg, seed + 2) - 0.5)           # plates differ a little
    v -= np.where(fiss < width, 0.26, 0.0) + np.where(fiss < width * 0.45, 0.1, 0.0)
    v -= np.where((g < 0.08) & (hash3(col_i, seg, seed + 5) < 0.55) & (fiss >= width), 0.2, 0.0)
    v += np.where((g > 0.08) & (g < 0.16) & (fiss >= width), 0.04, 0.0)   # lit lip over a crack
    v += 0.05 * (vnoise2(around * 1.6, along * 0.15, 9.0) - 0.5)  # fibres
    v += 0.03 * (hash3(q[:, 0] * 2, q[:, 1] * 2, q[:, 2] * 2, 3.0) - 0.5)

    # Knots: a dark eye in rings, the bark lifting round it.
    for (k, rad) in KNOTS:
        dq = q - np.array(k, float)
        d = np.sqrt(dq[:, 0] ** 2 + (dq[:, 1] / 1.35) ** 2 + dq[:, 2] ** 2)
        inner = d < rad * 0.45
        ring = (d >= rad * 0.45) & (d < rad)
        v = np.where(inner, base - 0.32 + 0.12 * (dq[:, 1] / rad), v)
        v = np.where(ring, base + 0.02 + 0.07 * np.sin(d * 4.0), v)
        v = np.where((d >= rad) & (d < rad * 1.35), v + 0.05, v)
    # The hollow: a dark hole, lit inside its lower lip, a raised rim.
    (hx, hy, hz), (rw, rh) = HOLLOW
    dq = q - np.array((hx, hy, hz), float)
    d = np.sqrt((dq[:, 0] / rw) ** 2 + (dq[:, 1] / rh) ** 2 + (dq[:, 2] / rw) ** 2)
    hole = d < 1
    v = np.where(hole, 0.03 + 0.1 * np.clip(-dq[:, 1] / rh, 0, 1), v)
    v = np.where((d >= 1) & (d < 1.3), base + 0.1 - 0.1 * (dq[:, 1] < 0), v)
    col = grad(BARK, v)

    # Moss: low on the trunk, on the north side and on anything facing up.
    # Only roots and limbs count as facing up: the trunk's ledges are 2 px
    # wide and would ring it with bright lines.
    up = np.clip(nn[:, 1], 0, 1) * (e["axis"] != 1 or "rot" in e)
    m = fbm3(q * 0.09, 2.0) + 0.3 * np.clip(1 - q[:, 1] / 40, 0, 1) \
        + 0.12 * (nn[:, 2] < -0.4) + 0.16 * up - 0.1 * (q[:, 1] > 90)
    moss = (m > 0.92) & ~hole
    mv = light(nn) - 0.04 + 0.18 * (fbm3(q * 0.5, 4.0, 2) - 0.5) - 0.4 * F.ao
    mv += 0.12 * smooth(0.92, 1.1, m)                        # thicker, brighter in the middle
    mv -= 0.08 * (hash3(np.floor(q[:, 0] * 1.5), np.floor(q[:, 1] * 1.5), np.floor(q[:, 2] * 1.5), 8.0) < 0.3)
    col = np.where(moss[:, None], grad(MOSS, mv), col)
    # Lichen: small pale rosettes higher up.
    lc = np.floor(q / 6.0)
    pick = hash3(lc[:, 0], lc[:, 1], lc[:, 2], 12.0) < 0.07
    lp = (lc + 0.5) * 6.0
    lr = 0.8 + 1.4 * hash3(lc[:, 0], lc[:, 1], lc[:, 2], 13.0)
    lich = pick & (np.linalg.norm(q - lp, axis=1) < lr) & (q[:, 1] > 20) & ~moss & ~hole
    col = np.where(lich[:, None], grad(LICHEN, base + 0.25 + 0.1 * np.sin(q[:, 0] * 3 + q[:, 1] * 2)), col)
    return col


PAINTERS = {"bark": paint_bark, "leaves": paint_leaves}


class Oak(Creature):
    """An HD model painted with numpy, a face at a time."""

    def __init__(self, *args, **kw):
        super().__init__(*args, **kw)
        self.WLO, self.WHI = [], []
        for e in self.elements:
            w = np.array([self.world(e, c) for c in corners(e)])
            self.WLO.append(w.min(0))
            self.WHI.append(w.max(0))
        self.WLO, self.WHI = np.array(self.WLO), np.array(self.WHI)

    def near(self, pts, pad):
        lo, hi = pts.min(0) - pad, pts.max(0) + pad
        return np.nonzero(np.all((self.WHI > lo) & (self.WLO < hi), axis=1))[0]

    def inside(self, Q, idx, eps=1e-6):
        """For world points Q (N, 3): inside any of the elements idx."""
        out = np.zeros(len(Q), bool)
        if len(idx) == 0:
            return out
        Mi = self.MINV[idx]
        lo, hi = self.LO[idx][:, None, :] + eps, self.HI[idx][:, None, :] - eps
        for s in range(0, len(Q), 8192):
            ql = np.einsum("kij,nj->kni", Mi[:, :3, :3], Q[s:s + 8192]) + Mi[:, None, :3, 3]
            out[s:s + 8192] = np.all((ql > lo) & (ql < hi), axis=2).any(0)
        return out

    def grid(self, e, f, sub):
        """Texel centres of a face: local (N, 3), world (N, 3), width, height."""
        o, u, v, w, h = face_frame(e, f)
        jj, ii = np.mgrid[0:int(h) * sub, 0:int(w) * sub]
        P = (np.array(o, float) + ((ii + 0.5) / sub)[..., None] * np.array(u, float)
             + ((jj + 0.5) / sub)[..., None] * np.array(v, float)).reshape(-1, 3)
        M = e["M"]
        return P, P @ M[:3, :3].T + M[:3, 3], int(w), int(h)

    def hidden(self, ei, f, P, Q):
        e = self.elements[ei]
        nw = self.world_dir(e, NORMAL[f])
        if nw[1] < -0.99 and Q[:, 1].max() < 0.01:
            return np.ones(len(Q), bool)                       # flat on the ground
        idx = self.near(Q, 1)
        idx = idx[idx != ei]
        return self.inside(Q + 0.25 * nw, idx)

    def visible_faces(self):
        vis = {}
        for ei, e in enumerate(self.elements):
            for f in bbcreature.FACES:
                P, Q, w, h = self.grid(e, f, 1)
                if not self.hidden(ei, f, P, Q).all():
                    vis[(ei, f)] = (w, h)
        return vis

    def occlusion(self, e, f, Q):
        """Ambient occlusion: how many short rays off the face hit geometry."""
        nw = np.array(self.world_dir(e, NORMAL[f]))
        ts = [np.array(self.world_dir(e, t)) for t in tangents(f)]
        rays = [(nw, 3.0, 1.0), (nw, 8.0, 0.8), (nw, 16.0, 0.6)]
        for t in ts:
            for s in (-1, 1):
                d = unit(nw + 0.75 * s * t)
                rays += [(d, 3.0, 0.8), (d, 8.0, 0.6)]
        idx = self.near(Q, 17)
        hit = np.zeros(len(Q))
        for d, dist, wt in rays:
            hit += wt * self.inside(Q + dist * d, idx)
        return hit / sum(wt for _, _, wt in rays)

    def edges(self, e, f, P, Q):
        """Lit edge one texture pixel wide where the solid falls away: on
        top faces in any direction, on side faces only upward."""
        nl = np.array(NORMAL[f], float)
        nw = self.world_dir(e, NORMAL[f])
        M = e["M"]
        idx = self.near(Q, 2)
        out = np.zeros(len(P), bool)
        step = 1 / SUB
        for t in tangents(f):
            for s in (-1, 1):
                d = s * step * np.array(t, float)
                dw = M[:3, :3] @ d
                if nw[1] < 0.7 and dw[1] < 0.7 * step:
                    continue
                test = (P + d - 0.25 * nl) @ M[:3, :3].T + M[:3, 3]
                out |= ~self.inside(test, idx)
        return out

    def paint(self, sizes=(256, 512, 1024)):
        t0 = time.time()
        self.visible = self.visible_faces()
        rects = [(k, w, h) for k, (w, h) in self.visible.items()]
        for tex in sizes:
            try:
                self.places = pack(rects, tex)
                break
            except SystemExit:
                continue
        self.tex = tex
        img = np.zeros((tex * SUB, tex * SUB, 4), np.uint8)
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            P, Q, w, h = self.grid(e, f, SUB)
            F = Face()
            F.e, F.ei, F.f, F.p, F.q = e, ei, f, P, Q
            F.n = tuple(self.world_dir(e, NORMAL[f]))
            F.ao = self.occlusion(e, f, Q)
            F.edge = self.edges(e, f, P, Q).astype(float)
            col = self.painters[e["part"]](F)
            rgba = np.concatenate([np.clip(np.round(col), 0, 255), np.full((len(col), 1), 255)], 1)
            img[oy * SUB:(oy + h) * SUB, ox * SUB:(ox + w) * SUB] = rgba.reshape(h * SUB, w * SUB, 4)
        self.img = Image.fromarray(img, "RGBA")
        print(f"painted in {time.time() - t0:.0f} s")
        return self.img

    # --- previews, vectorised
    def render(self, yaw, pitch, scale, size, silhouette=False, anchor=0.85):
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))
        R = np.array([[cy, 0, -sy], [-sy * sp, cp, -cy * sp], [sy * cp, sp, cy * cp]])
        img = np.asarray(self.img)
        polys, depths, cols = [], [], []
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            if (R @ self.world_dir(e, NORMAL[f]))[2] <= 0:
                continue                                   # faces away
            o, u, v, w, h = face_frame(e, f)
            W, H = int(w) * SUB, int(h) * SUB
            jj, ii = np.mgrid[0:H + 1, 0:W + 1]
            G = (np.array(o, float) + (ii / SUB)[..., None] * np.array(u, float)
                 + (jj / SUB)[..., None] * np.array(v, float))
            G = G @ e["M"][:3, :3].T + e["M"][:3, 3]
            G = G @ R.T
            quad = np.stack([G[:-1, :-1], G[:-1, 1:], G[1:, 1:], G[1:, :-1]], 2).reshape(-1, 4, 3)
            polys.append(quad[..., :2])
            depths.append(quad[..., 2].mean(1))
            cols.append(img[oy * SUB:oy * SUB + H, ox * SUB:ox * SUB + W].reshape(-1, 4))
        polys, depths, cols = np.concatenate(polys), np.concatenate(depths), np.concatenate(cols)
        order = np.argsort(depths, kind="stable")
        out = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(out)
        cx, cyy = size[0] / 2, size[1] * anchor
        xy = np.stack([cx + polys[..., 0] * scale, cyy - polys[..., 1] * scale], -1)
        for k in order:
            col = (20, 20, 24, 255) if silhouette else tuple(int(c) for c in cols[k])
            d.polygon([tuple(p) for p in xy[k]], fill=col)
        return out

    def write_bbmodel(self, out_dir, imp_height_px=IMP_HEIGHT_PX):
        """As Creature.write_bbmodel; the image is SUB times the UV size."""
        super().write_bbmodel(out_dir, imp_height_px)
        path = Path(out_dir) / f"{self.name}.bbmodel"
        model = json.loads(path.read_text())
        for tx in model["textures"]:
            tx["width"] = tx["height"] = self.tex * SUB
        path.write_text(json.dumps(model, indent="	"))

    def backdrop(self, w, h, tile):
        top, bot = np.array((150, 196, 236)), np.array((214, 232, 240))
        yy, _ = np.mgrid[0:h, 0:w]
        rgb = (top + (bot - top) * (yy / h)[..., None]).astype(np.uint8)
        return Image.fromarray(np.dstack([rgb, np.full((h, w), 255, np.uint8)]), "RGBA")

    def hero(self, path, views, tile=900, scale=3.4, ss=2):
        bg = self.backdrop(tile * len(views), tile, tile)
        for i, (yaw, pitch) in enumerate(views):
            shadow = Image.new("RGBA", (tile, tile), (0, 0, 0, 0))
            ImageDraw.Draw(shadow).ellipse((tile * 0.22, tile * 0.88, tile * 0.78, tile * 0.97),
                                           fill=(30, 50, 40, 110))
            bg.alpha_composite(shadow.filter(ImageFilter.GaussianBlur(tile / 50)), (i * tile, 0))
            big = self.render(yaw, pitch, scale * ss, (tile * ss, tile * ss), anchor=0.92)
            bg.alpha_composite(big.resize((tile, tile), Image.LANCZOS), (i * tile, 0))
        bg.convert("RGB").save(path)


OAK = Oak("oak", ELEMENTS, BONES, PAINTERS, {})

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    out.mkdir(parents=True, exist_ok=True)
    bbcreature.PX = PX_HD
    m = OAK
    top = max(m.world(e, c)[1] for e in m.elements for c in corners(e))
    assert abs(top - HEIGHT_PX) < 1e-6, f"height {top} px, want {HEIGHT_PX}"
    m.paint()
    m.previews(out, scale=1.5, tile=(440, 400), anchor=0.94)
    m.write_bbmodel(out)
    m.hero(out / "oak_render.png", [(-145, 12), (35, 12), (180, 2)])
    print(f"boxes: {len(m.elements)}  visible faces: {len(m.visible)}  "
          f"texture: {m.tex * SUB}x{m.tex * SUB} (uv {m.tex})  "
          f"texels used: {sum(w * h for w, h in m.visible.values()) * SUB * SUB}/{(m.tex * SUB) ** 2}  "
          f"height: {top:.1f} px = {top / 64:.3f} m")
