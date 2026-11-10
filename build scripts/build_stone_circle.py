"""stone_circle_ruins: a ruined Stonehenge-style stone circle with a Scottish feel (Callanish / Brodgar):
grey banded gneiss with quartz veins, crusty lichen, moss and heather.

blockbench_detailed_prompts.md: 3.11 (props and buildings, stone), 1.5 / 1.5.1 house texture style,
2 px per unit, building budget (100 to 500 cubes, 512 texture).

Every stone is built from a prototype in its own local frame (base centre at the origin, x along the ring,
z pointing out of the ring) and placed with a group: origin = its base, rotation = (lean, yaw, 0). Blockbench
rotates groups in ZYX order, so the lean (x) is applied first, about the stone's own x axis, then the yaw.
Stones of the same prototype share UV space (doc rule 11); the painting is done in the prototype's local space
so cracks, gneiss bands, quartz veins, lichen and moss run on over the edges of its cubes. Hidden faces (under
the ground, pressed against another cube of the same stone) get no UV.

Usage: py -3 build_stone_circle.py
"""
import base64, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image

OUT = r"C:\Users\lucas\blockbench_models\buildings\ruins"
NAME = "stone_circle_ruins"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
TEX = 512
PPU = 2
SEED = 4242


def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def R(s): return [hexc(c) for c in s.split()]
def h2(v): return round(v * 2) / 2


RAMPS = {
    # Lewisian gneiss: blue green shadows (deeper, more saturated), warm pale grey highlights
    "stone": R("#111a1f #162228 #1c2a31 #23323a #2b3b43 #34444c #3e4e55 #49585e #556268 #616c70 #6e7878 #7d8480 #8c9189 #9c9f95"),
    "moss": R("#162410 #1d3014 #253d18 #2e4a1c #385822 #436628 #50742f"),
    "lichen_g": R("#3a4840 #485850 #576860 #687870 #7a8a7e #8c9a8c"),
    "lichen_o": R("#5a3010 #7a4416 #a05e1e #c47c2c #dc9c44 #ecbc68"),
    "grass": R("#16300f #213f14 #2c5418 #3a6a1e #4c8226 #62992e #7cb03a"),
    "heather": R("#2a1232 #3e1a4a #562564 #70337e #8a4696 #a65eae #c07cc4"),
    "heath_leaf": R("#121e0e #192812 #213416 #2b421a #36521f"),
}

FACES = ("north", "east", "south", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
TANGENTS = {"north": ((1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)), "east": ((0, 0, 1), (0, 1, 0)),
            "west": ((0, 0, 1), (0, 1, 0)), "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1))}
FACE_LIGHT = {"up": 1.6, "north": 0.5, "west": 0.6, "south": -0.1, "east": -0.3, "down": -1.8}


def face_dims(frm, to, face):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]


def px(u):
    v = u * PPU
    assert abs(v - round(v)) < 1e-6, f"non integer pixel size {u}"
    return int(round(v))


def face_points(frm, to, face, w, h):
    (x0, y0, z0), (x1, y1, z1) = frm, to
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    if face == "north": X, Y, Z = x1 - U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z0)
    elif face == "south": X, Y, Z = x0 + U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z1)
    elif face == "east": X, Y, Z = np.full_like(U, x1), y1 - V * (y1 - y0), z1 - U * (z1 - z0)
    elif face == "west": X, Y, Z = np.full_like(U, x0), y1 - V * (y1 - y0), z0 + U * (z1 - z0)
    elif face == "up": X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y1), z0 + V * (z1 - z0)
    else: X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y0), z1 - V * (z1 - z0)
    return X, Y, Z


def uvgrid(w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    return U, V, np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)


def dither(v, w, h):
    bayer = np.array([[0, 2], [3, 1]]) / 4.0 - 0.375
    return v + np.tile(bayer, (h // 2 + 1, w // 2 + 1))[:h, :w] * 0.5


def ramp_colour(name, v):
    r = RAMPS[name]; n = len(r)
    q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
    lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
    return (np.array(r)[lo] * (1 - f) + np.array(r)[hi] * f).round().astype(np.uint8)


perm = np.arange(256); np.random.default_rng(SEED).shuffle(perm); perm = np.concatenate([perm, perm])
grad = np.random.default_rng(SEED + 1).random(256)


def vnoise3(x, y, z):
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    xi, yi, zi = (np.floor(a).astype(int) & 255 for a in (x, y, z))
    xf, yf, zf = x - np.floor(x), y - np.floor(y), z - np.floor(z)
    u, v, w = (t * t * (3 - 2 * t) for t in (xf, yf, zf))
    def g(i, j, k): return grad[perm[perm[perm[(xi + i) & 255] + ((yi + j) & 255)] + ((zi + k) & 255)]]
    l = lambda a, b, t: a + (b - a) * t
    return l(l(l(g(0, 0, 0), g(1, 0, 0), u), l(g(0, 1, 0), g(1, 1, 0), u), v),
             l(l(g(0, 0, 1), g(1, 0, 1), u), l(g(0, 1, 1), g(1, 1, 1), u), v), w)


def fbm(x, y, z, oct=3):
    s, a, f = 0.0, 0.5, 1.0
    for _ in range(oct):
        s = s + a * vnoise3(x * f, y * f, z * f); a *= 0.5; f *= 2.0
    return s


# ------------------------------------------------------------------ prototypes (local frames)

def B(name, frm, to):
    frm = [h2(v) for v in frm]; to = [h2(v) for v in to]
    for i in range(3):
        if to[i] - frm[i] < 0.5:
            to[i] = frm[i] + 0.5
    return (name, frm, to)


class Proto:
    def __init__(self, name, boxes, grounded=True, seed=0):
        self.name, self.boxes, self.grounded = name, boxes, grounded
        self.H = max(t[1] for _, f, t in boxes)
        self.seed = seed
        self.keys = {}          # (box index, face) -> rect key or None
        names = [b[0] for b in boxes]
        assert len(names) == len(set(names)), f"{name}: duplicate box names"


def add_lumps(boxes, r, hw, hd, y_lo, y_hi, n):
    """thin slabs on the side faces so no big face is flat"""
    for k in range(n):
        side = r.choice("nsew")
        y0 = r.uniform(y_lo, y_lo + (y_hi - y_lo) * 0.55)
        y1 = min(y_hi - 0.5, y0 + r.uniform(5, max(6, (y_hi - y_lo) * 0.45)))
        t = r.choice([0.5, 1.0])
        if side in "ns":
            a = r.uniform(-hw + 0.5, hw - 3.5); b = min(hw - 0.5, a + r.uniform(3, 6))
            z = -hd if side == "n" else hd
            frm, to = ([a, y0, z - t], [b, y1, z]) if side == "n" else ([a, y0, z], [b, y1, z + t])
        else:
            a = r.uniform(-hd + 0.5, hd - 2.5); b = min(hd - 0.5, a + r.uniform(2, 4.5))
            x = -hw if side == "w" else hw
            frm, to = ([x - t, y0, a], [x, y1, b]) if side == "w" else ([x, y0, a], [x + t, y1, b])
        boxes.append(B(f"lump_{k + 1}", frm, to))


def upright(name, seed, w, d, h, top="flat", lumps=3, tenon=False):
    r = random.Random(seed)
    hw, hd = w / 2, d / 2
    bx = []
    if top == "flat":
        core = h - 3
        bx.append(B("core", [-hw, -2, -hd], [hw, core, hd]))
        bx.append(B("crown", [-hw + 0.5, core, -hd + 0.5], [hw - 0.5, h, hd - 0.5]))
        if tenon:
            bx.append(B("tenon", [-1.5, h, -1.5], [1.5, h + 2.5, 1.5]))
    elif top == "rough":
        core = h - 7
        s = r.choice([-1, 1])
        bx.append(B("core", [-hw, -2, -hd], [hw, core, hd]))
        if s < 0:
            bx.append(B("shoulder", [-hw + 0.5, core, -hd + 0.5], [hw * 0.3, h - 2.5, hd - 0.5]))
            bx.append(B("crown", [-hw + 1.5, h - 2.5, -hd + 1], [-hw * 0.1, h, hd - 1]))
            bx.append(B("ledge", [hw * 0.3, core, -hd + 1], [hw - 1, core + 1.5, hd - 1]))
        else:
            bx.append(B("shoulder", [-hw * 0.3, core, -hd + 0.5], [hw - 0.5, h - 2.5, hd - 0.5]))
            bx.append(B("crown", [hw * 0.1, h - 2.5, -hd + 1], [hw - 1.5, h, hd - 1]))
            bx.append(B("ledge", [-hw + 1, core, -hd + 1], [-hw * 0.3, core + 1.5, hd - 1]))
    elif top == "point":                        # thin Scottish slab narrowing to an off-centre tip
        c1, c2 = h * 0.62, h * 0.85
        s = r.choice([-1, 1])
        bx.append(B("core", [-hw, -2, -hd], [hw, c1, hd]))
        bx.append(B("taper", [-hw + 0.5 + (0.5 if s > 0 else 0), c1, -hd + 0.5],
                    [hw - 0.5 - (0.5 if s < 0 else 0), c2, hd - 0.5]))
        tw = max(1.5, w * 0.35)
        cx = s * w * 0.15
        bx.append(B("tip", [cx - tw / 2, c2, -hd + 1], [cx + tw / 2, h, hd - 1]))
    elif top == "broken":
        core = h - 5
        s = r.choice([-1, 1])
        bx.append(B("core", [-hw, -2, -hd], [hw, core, hd]))
        if s < 0:
            bx.append(B("jag_1", [-hw + 0.5, core, -hd + 0.5], [hw * 0.15, h, hd - 0.5]))
            bx.append(B("jag_2", [hw * 0.15, core, -hd + 1], [hw - 1.0, core + 2.5, hd - 1.5]))
        else:
            bx.append(B("jag_1", [-hw * 0.15, core, -hd + 0.5], [hw - 0.5, h, hd - 0.5]))
            bx.append(B("jag_2", [-hw + 1.0, core, -hd + 1.5], [-hw * 0.15, core + 2.5, hd - 1]))
    add_lumps(bx, r, hw, hd, 1.0, bx[0][2][1], lumps)
    return Proto(name, bx, True, seed)


def lying(name, seed, L, d, h, lumps=2, broken=True):
    """a fallen stone or lintel on the ground, length along x, sunk 1 unit"""
    r = random.Random(seed)
    hl, hd = L / 2, d / 2
    bx = [B("core", [-hl, -1, -hd], [hl, h - 1.5, hd]),
          B("top", [-hl + 1, h - 1.5, -hd + 0.5], [hl - (2.5 if broken else 1), h, hd - 0.5])]
    if broken:
        bx.append(B("break_1", [hl, -1, -hd + 1], [hl + 2.5, h - 3, hd - 1.5]))
        bx.append(B("break_2", [hl + 2.5, -1, -hd + 2], [hl + 4, h - 4.5, 0]))
    for k in range(lumps):
        a = r.uniform(-hl + 1, hl - 7); b = a + r.uniform(4, 7)
        side = r.choice("ns")
        z = -hd if side == "n" else hd
        y1 = r.uniform(h * 0.5, h - 2)
        if side == "n":
            bx.append(B(f"lump_{k + 1}", [a, -1, z - 0.5], [b, y1, z]))
        else:
            bx.append(B(f"lump_{k + 1}", [a, -1, z], [b, y1, z + 0.5]))
    return Proto(name, bx, True, seed)


def lintel(name, seed, L, d, h):
    """a lintel resting on two uprights: base at y 0"""
    r = random.Random(seed)
    hl, hd = L / 2, d / 2
    bx = [B("core", [-hl, 0, -hd], [hl, h - 1, hd]),
          B("cap", [-hl + 0.5, h - 1, -hd + 0.5], [hl - 0.5, h, hd - 0.5])]
    a = r.uniform(-hl + 2, hl - 9)
    bx.append(B("lump_1", [a, 1, hd], [a + r.uniform(5, 8), h - 2, hd + 0.5]))
    a = r.uniform(-hl + 2, hl - 9)
    bx.append(B("lump_2", [a, 1.5, -hd - 0.5], [a + r.uniform(4, 7), h - 1.5, -hd]))
    return Proto(name, bx, False, seed)


def chunk(name, seed, s):
    r = random.Random(seed)
    bx = [B("core", [-s / 2, -0.5, -s * 0.4], [s / 2, s * 0.55, s * 0.4]),
          B("knob", [-s * 0.3, s * 0.55, -s * 0.25], [s * 0.2 + r.choice([0, 0.5]), s * 0.8, s * 0.25])]
    return Proto(name, bx, True, seed)


PROTOS = {
    # outer sarsen ring: carriers have flat tops at 50 (lintels sit on them)
    "sarsen_a": upright("sarsen_a", 11, 10, 7, 50, "flat", 3),
    "sarsen_b": upright("sarsen_b", 12, 10, 7, 50, "flat", 4),
    "sarsen_c": upright("sarsen_c", 13, 10, 7, 50, "flat", 3),
    "sarsen_rough": upright("sarsen_rough", 14, 10, 7, 47, "rough", 3),
    "sarsen_rough_2": upright("sarsen_rough_2", 15, 10, 7, 44, "rough", 3),
    "sarsen_stump": upright("sarsen_stump", 16, 10, 7, 18, "broken", 2),
    "sarsen_stump_2": upright("sarsen_stump_2", 17, 10, 7, 27, "broken", 2),
    "sarsen_fallen": lying("sarsen_fallen", 18, 44, 10, 7, 3),
    "lintel": lintel("lintel", 19, 26, 7, 6),
    "lintel_2": lintel("lintel_2", 20, 26, 7, 6),
    "lintel_fallen": lying("lintel_fallen", 21, 24, 7, 6, 1, broken=False),
    # trilithons
    "tri_a": upright("tri_a", 31, 12, 8, 64, "flat", 4),
    "tri_b": upright("tri_b", 32, 12, 8, 64, "flat", 4),
    "tri_great": upright("tri_great", 33, 13, 9, 74, "flat", 4, tenon=True),
    "tri_lintel": lintel("tri_lintel", 34, 32, 8, 8),
    "tri_lintel_fallen": lying("tri_lintel_fallen", 35, 30, 8, 7, 1, broken=False),
    "tri_great_fallen": lying("tri_great_fallen", 36, 56, 13, 8, 3),
    # bluestones: thin pointed Scottish slabs
    "blue_a": upright("blue_a", 41, 6, 4.5, 22, "point", 1),
    "blue_b": upright("blue_b", 42, 5, 4, 18, "rough", 1),
    "blue_c": upright("blue_c", 43, 7, 5, 26, "point", 1),
    "blue_stump": upright("blue_stump", 44, 6, 5, 9, "broken", 0),
    "blue_fallen": lying("blue_fallen", 45, 18, 6, 4, 1),
    # single stones
    "heel": upright("heel", 51, 16, 13, 42, "rough", 4),
    "altar": lying("altar", 52, 30, 10, 3.5, 2, broken=False),
    "slaughter": lying("slaughter", 53, 24, 9, 4.5, 2),
    "chunk_a": chunk("chunk_a", 61, 5),
    "chunk_b": chunk("chunk_b", 62, 3.5),
}


# ------------------------------------------------------------------ painting

def inside(P, X, Y, Z, skip=None):
    m = np.zeros(np.shape(X), bool)
    for k, (_, f, t) in enumerate(P.boxes):
        if k == skip: continue
        m |= (X > f[0]) & (X < t[0]) & (Y > f[1]) & (Y < t[1]) & (Z > f[2]) & (Z < t[2])
    return m


def visible(P, X, Y, Z, face, skip):
    n = np.array(NORMAL[face], float); t1, t2 = (np.array(t, float) for t in TANGENTS[face])
    out = np.zeros(np.shape(X), bool)
    for d in [n] + [n + sg * t for t in (t1, t2) for sg in (1.2, -1.2)]:
        d = d / np.linalg.norm(d)
        free = np.ones(np.shape(X), bool)
        for step in np.arange(0.3, 10.0, 0.5):
            Yd = Y + d[1] * step
            free &= ~inside(P, X + d[0] * step, Yd, Z + d[2] * step, skip)
            if P.grounded:
                free &= Yd > -0.2
        out |= free
    return out


def paint_stone(P, i, face, w, h):
    _, frm, to = P.boxes[i]
    X, Y, Z = face_points(frm, to, face, w, h)
    nx, ny, nz = NORMAL[face]
    covered = inside(P, X + nx * 0.2, Y + ny * 0.2, Z + nz * 0.2, i)
    if P.grounded:
        covered |= (Y < 0.05) & (face != "up")
    if covered.all() or not (visible(P, X, Y, Z, face, i) & ~covered).any():
        return None
    nrng = np.random.default_rng(P.seed * 100 + i * 7 + FACES.index(face))
    side = face not in ("up", "down")
    U, V, edge = uvgrid(w, h)
    H = P.H
    o = P.seed * 3.7                                  # every prototype gets its own patterns
    Xo, Zo = X + o, Z - o
    v = np.full((h, w), 6.6 + FACE_LIGHT[face] * 1.2) + np.clip(Y / H, 0, 1) * 1.2
    v -= np.clip(1.0 - edge / 3.5, 0, 1) * 1.3       # rounded form: darker toward each face's edges
    if side:
        v += np.clip(1.0 - np.abs(U - 0.5) * 2.0, 0, 1) * 0.5
        v += np.clip(1.0 - V * h / 3.0, 0, 1) * 0.5  # lit top lip
    near1 = inside(P, X + nx * 0.9, Y + ny * 0.9, Z + nz * 0.9, i)
    near2 = inside(P, X + nx * 1.8, Y + ny * 1.8, Z + nz * 1.8, i)
    v -= near1 * 1.5 + near2 * 0.7                   # soft contact shadows under shoulders and lumps
    if P.grounded and side:
        v -= np.clip(1.0 - Y / 4.0, 0, 1) * 1.6     # ground contact
    v += (fbm(Xo * 0.11, Y * 0.11, Zo * 0.11) - 0.5) * 2.0 + (fbm(Xo * 0.3, Y * 0.3, Zo * 0.3) - 0.5) * 0.6
    # gneiss: wavy, slightly diagonal light and dark bands
    band = np.sin(Y * 0.5 + Xo * 0.2 + Zo * 0.16 + fbm(Xo * 0.1 + 3, Y * 0.1, Zo * 0.1) * 7.0)
    v += band * 0.55
    if side:                                          # rain streaks running down from the top
        streak = fbm(Xo * 0.9 + 11, Y * 0.04, Zo * 0.9 + 4)
        v -= (streak > 0.6) * 0.7 * np.clip(Y / H, 0.3, 1)
    v = dither(v, w, h)
    rgb = ramp_colour("stone", v)
    # quartz veins: thin pale lines running through the bands
    q = (np.abs(fbm(Xo * 0.07 + 50, Y * 0.07 + Xo * 0.02, Zo * 0.07 + 20) - 0.5) < 0.008) & (fbm(Xo * 0.05, Y * 0.05 + 9, Zo * 0.05) > 0.5)
    rgb[q] = ramp_colour("stone", v + 2.0)[q]
    # cracks: a dark line with a lit pixel beside it, sparse
    for _ in range(max(0, (w * h) // 260)):
        x, y = int(nrng.integers(1, max(2, w - 1))), int(nrng.integers(1, max(2, h - 1)))
        for _s in range(int(nrng.integers(3, 9))):
            if 0 <= x < w and 0 <= y < h:
                rgb[y, x] = ramp_colour("stone", v[y, x] - 2.0)
                if x + 1 < w: rgb[y, x + 1] = ramp_colour("stone", v[y, x + 1] + 1.0)
            x += int(nrng.choice([-1, 0, 1])); y += int(nrng.choice([0, 1, 1]))
    if face != "down":
        # crusty grey green lichen rosettes, darker rim, paler centre
        lf = fbm(Xo * 0.28 + 7, Y * 0.28, Zo * 0.28 + 3, 2)
        lm = lf > 0.66
        lv = 1.8 + FACE_LIGHT[face] * 0.5 + np.clip((lf - 0.66) * 30, 0, 2.0) + np.clip(Y / H, 0, 1) * 0.8
        rgb[lm] = ramp_colour("lichen_g", lv)[lm]
        # small orange lichen on the upper stone
        om = (fbm(Xo * 0.5 + 19, Y * 0.5, Zo * 0.5 + 8, 2) > 0.76) & (Y > H * 0.45)
        rgb[om] = ramp_colour("lichen_o", np.full((h, w), 2.0 + FACE_LIGHT[face] * 0.5))[om]
    # moss: cushions on top faces, spilling a little over the top edge, and a damp band at the foot
    mf = fbm(Xo * 0.25 + 20.0, Y * 0.05, Zo * 0.25 + 9.0)
    up_open = not inside(P, np.array([(frm[0] + to[0]) / 2]), np.array([to[1] + 0.3]), np.array([(frm[2] + to[2]) / 2]), i)[0]
    if face == "up":
        mm = mf > 0.44
    elif side:
        mm = (mf > 0.47) & (Y > to[1] - 1.2 - (mf - 0.47) * 6.0) & up_open
        if P.grounded:
            mm |= (Y < 1.2 + (fbm(Xo * 0.4 + 5, 0, Zo * 0.4) - 0.3) * 5.0) & (mf > 0.38)
    else:
        mm = np.zeros((h, w), bool)
    rgb[mm] = ramp_colour("moss", 2.2 + np.clip((mf - 0.44) * 14, 0, 2.5) + FACE_LIGHT[face] * 0.6 + np.clip(Y / H, 0, 1) * 0.6)[mm]
    return rgb, np.ones((h, w), bool)


def paint_tuft(w, h, seed):
    r = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
    for kk in range(5):
        x = (kk + r.uniform(0.1, 0.9)) * w / 5; top = int(r.integers(0, h // 2)); lean = r.uniform(-0.35, 0.35)
        for y in range(h - 1, top - 1, -1):
            xi = int(round(x + lean * (h - 1 - y)))
            if 0 <= xi < w:
                t = (h - 1 - y) / max(1, h - 1 - top)
                rgb[y, xi] = ramp_colour("grass", 0.8 + t * 5.0); a[y, xi] = True
    return rgb, a


def paint_heather(w, h, seed):
    r = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
    tops = [h - 1 - int(round((h - 2) * (0.45 + 0.55 * math.sin(math.pi * (x + 0.5) / w)) + r.uniform(-1, 1))) for x in range(w)]
    for x in range(w):
        t0 = max(0, min(h - 1, tops[x]))
        for y in range(t0, h):
            depth = (y - t0) / max(1, h - t0)
            a[y, x] = True
            if depth < 0.6 and r.random() < 0.75 - depth:
                rgb[y, x] = ramp_colour("heather", 5.2 - depth * 5.0 - abs(x - w / 2) / w * 1.5 + r.uniform(-0.6, 0.6))
            else:
                rgb[y, x] = ramp_colour("heath_leaf", 3.2 - depth * 3.0)
    # a few stems poking out of the dome
    return rgb, a


def paint_pebble(face, w, h):
    U, V, edge = uvgrid(w, h)
    v = np.full((h, w), 6.4 + FACE_LIGHT[face]) - (V * 1.2 if face not in ("up", "down") else 0)
    v -= np.clip(1.0 - edge / 2, 0, 1) * 0.8
    rgb = ramp_colour("stone", dither(v, w, h))
    if face == "up" and w * h >= 4:
        rgb[0, 0] = ramp_colour("lichen_g", np.array(3.0))
    return rgb, np.ones((h, w), bool)


# ------------------------------------------------------------------ the model

rng = random.Random(SEED)
elements, groups, root_children = [], {}, []


def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def group(name, parent=None, origin=(0, 0, 0), rotation=(0, 0, 0)):
    assert name not in groups, name
    groups[name] = {"name": name, "uuid": new_uuid(), "origin": [round(v, 4) for v in origin],
                    "rotation": [round(v, 3) for v in rotation], "children": []}
    if parent: groups[parent]["children"].append(("g", name))
    return name


rects = {}


def add_rect(key, w, h, paint):
    if key not in rects:
        res = paint()
        if res is None:
            rects[key] = None
        else:
            rects[key] = {"w": w, "h": h, "rgb": res[0], "a": res[1]}
    return key if rects[key] is not None else None


def proto_keys(P):
    if not P.keys:
        for i, (_, frm, to) in enumerate(P.boxes):
            for face in FACES:
                if face == "down" and P.grounded:
                    P.keys[(i, face)] = None; continue
                w, h = (px(v) for v in face_dims(frm, to, face))
                P.keys[(i, face)] = add_rect(f"{P.name}:{i}:{face}", w, h, lambda i=i, face=face, w=w, h=h: paint_stone(P, i, face, w, h))
    return P.keys


def cube(name, grp, frm, to, faces, rotation=(0, 0, 0), origin=None):
    origin = origin or [(frm[i] + to[i]) / 2 for i in range(3)]
    e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
         "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
         "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": faces, "type": "cube", "uuid": new_uuid()}
    if any(abs(r_) > 1e-6 for r_ in rotation): e["rotation"] = [round(v, 3) for v in rotation]
    elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
    return e


placed = []      # (x, z, radius) of every stone footprint, to keep ground cover off them


def place(pname, parent, gname, base, yaw, lean=0.0, roll=0.0, foot=6.0):
    P = PROTOS[pname]
    keys = proto_keys(P)
    g = group(gname, parent, origin=base, rotation=(lean, yaw, roll))
    for i, (cn, frm, to) in enumerate(P.boxes):
        faces = {f: keys[(i, f)] for f in FACES}
        if all(k is None for k in faces.values()):
            continue
        cube(f"{gname}_{cn}", g, [frm[j] + base[j] for j in range(3)], [to[j] + base[j] for j in range(3)], faces)
    placed.append((base[0], base[2], foot))
    return g


def polar(r_, theta):          # theta in degrees, 0 = north (-z), clockwise seen from above
    t = math.radians(theta)
    return h2(r_ * math.sin(t)), h2(-r_ * math.cos(t))


def yaw_radial(theta): return 180.0 - theta      # local +z points out of the ring
def yaw_along(theta): return 90.0 - theta         # local +x points out of the ring


def local_to_world(cx, cz, yaw, lx, lz):
    p = math.radians(yaw)
    return cx + lx * math.cos(p) + lz * math.sin(p), cz - lx * math.sin(p) + lz * math.cos(p)


ROOT = group(NAME)
G_OUT = group("outer_circle", ROOT)
G_LIN = group("lintels", ROOT)
G_TRI = group("trilithons", ROOT)
G_BLUE = group("bluestones", ROOT)
G_SINGLE = group("single_stones", ROOT)
G_FALL = group("fallen_stones", ROOT)
G_GROUND = group("ground_cover", ROOT)

# ---- outer sarsen circle: 20 slots, intact arc with lintels over the north-east entrance
R_OUT = 84.0
OUTER = {0: "sarsen_a", 1: "sarsen_b", 2: "sarsen_c", 3: "sarsen_a", 4: "sarsen_b", 5: ("sarsen_rough", 9),
         6: "sarsen_stump", 8: "fallen", 9: "sarsen_rough_2", 10: "sarsen_c", 11: "sarsen_a", 12: "sarsen_stump_2",
         14: ("sarsen_rough", -7), 15: "sarsen_b", 16: "sarsen_stump", 17: "sarsen_c", 18: "sarsen_a", 19: "sarsen_stump_2"}
for k in range(20):
    if k not in OUTER: continue
    th = k * 18.0
    spec = OUTER[k]
    x, z = polar(R_OUT, th)
    if spec == "fallen":                         # toppled outward, lying in the grass
        fx, fz = polar(R_OUT + 24, th + 2)
        place("sarsen_fallen", G_FALL, f"outer_fallen_{k}", [fx, 0, fz], yaw_along(th) + 8, roll=3, foot=22)
        continue
    pname, lean = (spec, 0.0) if isinstance(spec, str) else spec
    jit = 0.0 if pname in ("sarsen_a", "sarsen_b", "sarsen_c") else rng.uniform(-6, 6)
    place(pname, G_OUT, f"sarsen_{k}", [x, 0, z], yaw_radial(th) + jit, lean=lean)
for k0, pn in ((0, "lintel"), (1, "lintel_2"), (2, "lintel"), (3, "lintel_2"), (10, "lintel"), (17, "lintel_2")):
    th = (k0 + 0.5) * 18.0
    x, z = polar(R_OUT * math.cos(math.radians(9)), th)
    place(pn, G_LIN, f"lintel_{k0}_{k0 + 1}", [x, 50, z], yaw_radial(th), foot=0)
for k0, dth, dr in ((6, 2.0, -9.0), (13, -3.0, 10.0)):        # lintels that fell with their stones
    x, z = polar(R_OUT + dr, k0 * 18.0 + 9 + dth)
    place("lintel_fallen", G_FALL, f"lintel_fallen_{k0}", [x, 0, z], yaw_radial(k0 * 18.0) + rng.uniform(-25, 25), roll=4, foot=13)

# ---- trilithon horseshoe, open to the north east
TRI = [  # theta, radius, upright proto(s), state
    (225, 30, "tri_great", "great"),
    (175, 40, ("tri_a", "tri_b"), "whole"),
    (275, 40, ("tri_b", "tri_a"), "whole"),
    (125, 46, ("tri_a", "tri_b"), "leaning"),
    (325, 46, ("tri_b", "tri_a"), "whole"),
]
for n_, (th, r_, pn, state) in enumerate(TRI):
    cx, cz = polar(r_, th)
    yw = yaw_radial(th)
    tg = group(f"trilithon_{n_ + 1}", G_TRI)
    if state == "great":
        # one tall upright still standing with its tenon bare; its partner and the lintel lie broken in front
        x, z = local_to_world(cx, cz, yw, -9.0, 0)
        place("tri_great", tg, f"trilithon_{n_ + 1}_upright_left", [h2(x), 0, h2(z)], yw, lean=-3, foot=9)
        x, z = local_to_world(cx, cz, yw, 10.0, -22.0)
        place("tri_great_fallen", tg, f"trilithon_{n_ + 1}_upright_fallen", [h2(x), 0, h2(z)], yw + 68, roll=-2, foot=28)
        x, z = local_to_world(cx, cz, yw, -20.0, -14.0)
        place("tri_lintel_fallen", tg, f"trilithon_{n_ + 1}_lintel_fallen", [h2(x), 0, h2(z)], yw - 32, roll=5, foot=16)
        continue
    hgt = 64.0
    for side, sx, p_ in (("left", -8.5, pn[0]), ("right", 8.5, pn[1])):
        x, z = local_to_world(cx, cz, yw, sx, 0)
        lean = 12.0 if (state == "leaning" and side == "right") else 0.0
        place(p_, tg, f"trilithon_{n_ + 1}_upright_{side}", [h2(x), 0, h2(z)], yw, lean=lean, foot=8)
    if state == "whole":
        place("tri_lintel", tg, f"trilithon_{n_ + 1}_lintel", [cx, hgt, cz], yw, foot=0)
    else:
        x, z = local_to_world(cx, cz, yw, 4.0, 15.0)
        place("tri_lintel_fallen", tg, f"trilithon_{n_ + 1}_lintel_fallen", [h2(x), 0, h2(z)], yw + 18, roll=-4, foot=16)

# ---- bluestones: an outer ring of thin pointed slabs and an inner horseshoe
BLUE_RING = ["blue_a", "blue_c", "blue_b", None, "blue_a", "blue_stump", "fallen", "blue_c", "blue_b", None,
             "blue_a", "blue_c", "blue_stump", None, "blue_b", "blue_a"]
for k, pn in enumerate(BLUE_RING):
    if pn is None: continue
    th = k * 22.5 + 11.25
    x, z = polar(64.0, th)
    if pn == "fallen":
        place("blue_fallen", G_FALL, f"bluestone_fallen_{k}", [x, 0, z], yaw_along(th) + 35, roll=6, foot=10)
        continue
    lean = rng.choice([0, 0, 0, 6, -8])
    place(pn, G_BLUE, f"bluestone_{k}", [x, 0, z], yaw_radial(th) + rng.uniform(-12, 12), lean=lean, foot=5)
for k, th in enumerate(range(115, 345, 30)):
    pn = ["blue_b", "blue_a", "blue_b", "blue_c", "blue_stump", "blue_b", "blue_a", "blue_b"][k]
    x, z = polar(19.0, th)
    place(pn, G_BLUE, f"inner_bluestone_{k + 1}", [x, 0, z], yaw_radial(th) + rng.uniform(-10, 10),
          lean=rng.choice([0, 0, 5, -5]), foot=5)

# ---- single stones on the north east axis
x, z = polar(12.0, 225)
place("altar", G_SINGLE, "altar_stone", [x, 0, z], yaw_radial(225) + 90 + 6, foot=16)
x, z = polar(108.0, 45)
place("slaughter", G_SINGLE, "slaughter_stone", [x, 0, z], yaw_along(45) + 70, roll=2, foot=14)
x, z = polar(150.0, 45)
place("heel", G_SINGLE, "heel_stone", [x, 0, z], yaw_radial(45) + 14, lean=-10, foot=12)

# ---- rubble around the broken and fallen stones
for k, (th, r_) in enumerate([(108, 90), (113, 79), (232, 92), (240, 80), (150, 88), (300, 92), (345, 76), (125, 54),
                              (218, 18), (236, 26), (200, 40), (95, 70)]):
    x, z = polar(r_ + rng.uniform(-3, 3), th + rng.uniform(-3, 3))
    place(rng.choice(["chunk_a", "chunk_b"]), G_FALL, f"rubble_{k + 1}", [x, 0, z], rng.uniform(0, 360), roll=rng.uniform(-8, 8), foot=3)

# ---- ground cover: grass tufts at the stone feet, heather clumps, pebbles
def clear(x, z, r_):
    return all((x - px_) ** 2 + (z - pz_) ** 2 > (r_ + f_) ** 2 for px_, pz_, f_ in placed)


def card_pair(name, x, z, w, h, key_fn, yaw):
    pw, ph = px(w), px(h)
    for j, dy in enumerate((0, 90)):
        key = key_fn(pw, ph)
        faces = {f: None for f in FACES}
        faces["north"] = key; faces["south"] = key
        cube(f"{name}_{j + 1}", G_GROUND, [x - w / 2, -0.5, z], [x + w / 2, h - 0.5, z], faces,
             rotation=(0, yaw + dy, 0), origin=[x, 0, z])


TUFT_KEYS = [f"tuft_{i}" for i in range(3)]
HEATH_KEYS = [f"heather_{i}" for i in range(2)]
n_tuft = n_heath = 0
tries = 0
while n_tuft < 24 and tries < 4000:
    tries += 1
    th = rng.uniform(0, 360); r_ = rng.choice([R_OUT, 64.0, 40.0, 19.0]) + rng.uniform(-9, 9)
    x, z = polar(r_, th)
    if not clear(x, z, 1.5): continue
    if all((x - px_) ** 2 + (z - pz_) ** 2 > (f_ + 6) ** 2 for px_, pz_, f_ in placed): continue   # keep them near stones
    i = rng.randrange(3)
    card_pair(f"grass_tuft_{n_tuft + 1}", x, z, 5.0, 5.0 if i else 6.5,
              lambda pw, ph, i=i: add_rect(f"{TUFT_KEYS[i]}:{pw}x{ph}", pw, ph, lambda: paint_tuft(pw, ph, 900 + i)), rng.uniform(0, 90))
    placed.append((x, z, 2.0)); n_tuft += 1
tries = 0
while n_heath < 22 and tries < 4000:
    tries += 1
    th = rng.uniform(0, 360); r_ = rng.uniform(70, 125) if rng.random() < 0.75 else rng.uniform(46, 58)
    x, z = polar(r_, th)
    if not clear(x, z, 3.0): continue
    i = rng.randrange(2)
    w = 10.0 if i else 8.0
    card_pair(f"heather_{n_heath + 1}", x, z, w, 6.0 if i else 5.0,
              lambda pw, ph, i=i: add_rect(f"{HEATH_KEYS[i]}:{pw}x{ph}", pw, ph, lambda: paint_heather(pw, ph, 950 + i)), rng.uniform(0, 90))
    placed.append((x, z, 3.0)); n_heath += 1
for k in range(22):
    for _ in range(200):
        th = rng.uniform(0, 360); r_ = rng.choice([R_OUT + 6, R_OUT - 8, 64.0, 30.0]) + rng.uniform(-5, 5)
        x, z = polar(r_, th)
        if clear(x, z, 1.0): break
    s = rng.choice([1.0, 1.0, 1.5, 2.0])
    hgt = rng.choice([0.5, 1.0]) if s < 2 else 1.5
    faces = {}
    for f in FACES:
        if f == "down": faces[f] = None; continue
        frm, to = [0, 0, 0], [s, hgt, h2(s * 0.8) if s > 1 else s]
        w, h = (px(v) for v in face_dims(frm, to, f))
        faces[f] = add_rect(f"pebble:{f}:{w}x{h}", w, h, lambda f=f, w=w, h=h: paint_pebble(f, w, h))
    cube(f"pebble_{k + 1}", G_GROUND, [x, -0.25, z], [x + s, hgt - 0.25, z + (h2(s * 0.8) if s > 1 else s)], faces,
         rotation=(0, rng.uniform(0, 90), 0), origin=[x, 0, z])
    placed.append((x, z, 1.0))

# ---- hidden scale dummy (an 18 unit Imp) by the heel stone, for size checks
G_DUMMY = group("scale_dummy")
x, z = polar(134.0, 52)
dummy = cube("scale_dummy_imp", G_DUMMY, [x - 2, 0, z - 2], [x + 2, 18.5, z + 2], {f: None for f in FACES})
dummy["export"] = False; dummy["visibility"] = False

# ------------------------------------------------------------------ atlas, texture and file
GAP = 2
real = {k: r_ for k, r_ in rects.items() if r_ is not None}
x = y = shelf = 0
for kk, r_ in sorted(real.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
    if x + r_["w"] > TEX: x, y, shelf = 0, y + shelf + GAP, 0
    r_["x"], r_["y"] = x, y; x += r_["w"] + GAP; shelf = max(shelf, r_["h"])
used = y + shelf
if used > TEX: raise SystemExit(f"atlas overflow {used}px of {TEX}")
img = np.zeros((TEX, TEX, 4), np.uint8)
for r_ in real.values():
    img[r_["y"]:r_["y"] + r_["h"], r_["x"]:r_["x"] + r_["w"], :3] = r_["rgb"]
    img[r_["y"]:r_["y"] + r_["h"], r_["x"]:r_["x"] + r_["w"], 3] = np.where(r_["a"], 255, 0)
for e in elements:
    for face in FACES:
        key = e["faces"][face]
        if key is None:
            e["faces"][face] = {"uv": [0, 0, 0, 0], "texture": None}
        else:
            r_ = real[key]
            e["faces"][face] = {"uv": [r_["x"], r_["y"], r_["x"] + r_["w"], r_["y"] + r_["h"]], "texture": 0}


def group_json(g):
    return {"name": g["name"], "uuid": g["uuid"], "export": g["name"] != "scale_dummy", "locked": False, "scope": 0,
            "selected": False, "visibility": g["name"] != "scale_dummy", "origin": g["origin"], "rotation": g["rotation"],
            "color": 0, "children": [], "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": False,
            "primary_selected": False}


def outliner(name):
    g = groups[name]
    return {"uuid": g["uuid"], "isOpen": name in (ROOT,), "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}


buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
model = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": NAME,
         "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
         "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
         "resolution": {"width": TEX, "height": TEX}, "elements": elements,
         "groups": [group_json(g) for g in groups.values()], "outliner": [outliner(ROOT), outliner(G_DUMMY)],
         "textures": [{"name": f"{NAME}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                       "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                       "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                       "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                       "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                       "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": new_uuid(),
                       "source": src}],
         "animations": []}
os.makedirs(OUT, exist_ok=True)
path = os.path.join(OUT, f"{NAME}.bbmodel")
png = os.path.join(OUT, f"{NAME}.png")
with open(path, "w", encoding="utf8") as fh:
    json.dump(model, fh, indent="\t")
sys.path.insert(0, REPO_SCRIPTS)
import fix_texture_bleed
fix_texture_bleed.pad_file(path, [png])
colours = len({tuple(c) for c in np.array(Image.open(png).convert("RGBA")).reshape(-1, 4) if c[3] > 0})
xs = [v for e in elements if e["export"] for v in (e["from"][0], e["to"][0])]
zs = [v for e in elements if e["export"] for v in (e["from"][2], e["to"][2])]
print(f"{NAME}: cubes={sum(1 for e in elements if e['export'])} groups={len(groups)} atlas={used}/{TEX} colours={colours}")
print(f"  span x {min(xs):.1f}..{max(xs):.1f}  z {min(zs):.1f}..{max(zs):.1f}  top {max(e['to'][1] for e in elements):.1f}")
print(f"  tufts={n_tuft} heather={n_heath} rects={len(real)}")
