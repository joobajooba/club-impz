"""copper_vein: the T3 copper mining node (blockbench_detailed_prompts.md section 3.2).

A lumpy dark grey stone mound, big orange copper chunks pushed into it at angles (green patina on their
edges), copper veins running through the stone and wrapping over the edges, loose stone and copper
fragments on the ground, moss on top, grass tufts at the base and a small sapphire accent (the T3 gem).

Stone is painted in WORLD space: every texel knows where it is on the model, so the veins, moss and
crevice shadows continue across cube edges and from one cube onto the next. Texels pressed against
another stone are dark crevices; faces covered completely get no UV (section 1.5 rule 11).

2 px/unit, one embedded 256 texture (J00BA's choice over the doc's 128, so every stone is painted on its own), no animations (ore veins don't shake).
Usage: py -3 build_copper_vein.py
"""
import base64, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ore_metal as OM

OUT = r"C:\Users\lucas\blockbench_models\ores"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
NAME = "copper_vein"
TEX = 256                      # J00BA chose 256 over the doc's 128 (2026-11-08): unique world-space painting
PPU = 2
SEED = 3303
rng = random.Random(SEED)
nrng = np.random.default_rng(SEED)


def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


RAMPS = {
    # dark grey stone (doc grey stone ramp, cool shadows), copper (doc #5a2410 -> #f28c52, extended both ways)
    "stone":   "#16181f #1c1e26 #262931 #2c2f38 #353943 #3e424c #494d57 #545862 #60646e #6c707a #7b7f88 #8a8e96",
    "copper":  "#3a140a #5a2410 #7a3416 #9c461e #bc5c28 #d87034 #ea8344 #f28c52 #f6a66e #f9c08e",
    "patina":  "#163a34 #1f5246 #2c6c58 #3f8a6c #5ca684 #84c2a0",
    "moss":    "#1e3014 #2e481a #42621f #5c7e28 #7a9a34 #94b23e",
    "grass":   "#1a3412 #264c18 #33661e #447f26 #5a9a30 #78b440",
    "sapph":   "#0c1a40 #13296a #1c3c96 #2a58c0 #4682de #78b0f0 #b4d8fa",
    "soil":    "#2a1e16 #3a2a1e #4c3826 #5e4630",
}
RAMPS = {k: [hexc(c) for c in v.split()] for k, v in RAMPS.items()}


def ramp_colour(name, v):
    """Value -> colour in half steps (half steps blend neighbours: small, smooth steps)."""
    r = RAMPS[name]; n = len(r)
    q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
    lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
    a = np.array(r)[lo]; b = np.array(r)[hi]
    return (a * (1 - f) + b * f).round().astype(np.uint8)


def dither(v, w, h):
    """A little ordered dithering where two shades meet, so gradients step softly."""
    bayer = np.array([[0, 2], [3, 1]]) / 4.0 - 0.375
    return v + np.tile(bayer, (h // 2 + 1, w // 2 + 1))[:h, :w] * 0.5


# ---------------------------------------------------------------- 3D value noise (for world-space fields)
_PERM = np.arange(256); np.random.default_rng(SEED).shuffle(_PERM); _PERM = np.concatenate([_PERM, _PERM])
_GRAD = np.random.default_rng(SEED + 1).random(256)


def vnoise3(x, y, z):
    x, y, z = (np.asarray(a, float) for a in (x, y, z))
    xi, yi, zi = (np.floor(a).astype(int) & 255 for a in (x, y, z))
    xf, yf, zf = x - np.floor(x), y - np.floor(y), z - np.floor(z)
    u, v, w = (t * t * (3 - 2 * t) for t in (xf, yf, zf))

    def g(i, j, k): return _GRAD[_PERM[_PERM[_PERM[(xi + i) & 255] + ((yi + j) & 255)] + ((zi + k) & 255)]]
    l = lambda a, b, t: a + (b - a) * t
    return l(l(l(g(0, 0, 0), g(1, 0, 0), u), l(g(0, 1, 0), g(1, 1, 0), u), v),
             l(l(g(0, 0, 1), g(1, 0, 1), u), l(g(0, 1, 1), g(1, 1, 1), u), v), w)


def fbm(x, y, z, oct=3):
    s, a, f = 0.0, 0.5, 1.0
    for _ in range(oct):
        s = s + a * vnoise3(x * f, y * f, z * f); a *= 0.5; f *= 2.0
    return s


# ---------------------------------------------------------------- model scaffolding
FACES = ("north", "east", "south", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
FACE_LIGHT = {"up": 1.6, "north": 0.5, "west": 0.6, "south": -0.1, "east": -0.3, "down": -1.8}
elements, groups = [], {}


def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))


def group(name, parent=None, origin=(0, 0, 0)):
    groups[name] = {"name": name, "uuid": new_uuid(), "origin": list(origin), "children": []}
    if parent: groups[parent]["children"].append(("g", name))
    return name


def cube(name, grp, frm, to, rotation=(0, 0, 0), origin=None, kind="stone", hidden=("down",)):
    origin = origin or [(frm[i] + to[i]) / 2 for i in range(3)]
    e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
         "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
         "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": {}, "type": "cube",
         "uuid": new_uuid(), "_kind": kind, "_hidden": set(hidden)}
    if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(v, 3) for v in rotation]
    elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
    return e


def face_dims(frm, to, face):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]


def px(u):
    v = u * PPU
    assert abs(v - round(v)) < 1e-6, f"non integer pixel size {u}"
    return int(round(v))


def face_points(frm, to, face, w, h):
    """World position of every texel centre of an unrotated cube's face (Blockbench UV orientation:
    u left->right as seen from outside, v top->bottom)."""
    (x0, y0, z0), (x1, y1, z1) = frm, to
    u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    if face == "north": X, Y, Z = x1 - U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z0)
    elif face == "south": X, Y, Z = x0 + U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z1)
    elif face == "east": X, Y, Z = np.full_like(U, x1), y1 - V * (y1 - y0), z1 - U * (z1 - z0)
    elif face == "west": X, Y, Z = np.full_like(U, x0), y1 - V * (y1 - y0), z0 + U * (z1 - z0)
    elif face == "up": X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y1), z0 + V * (z1 - z0)
    else: X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y0), z1 - V * (z1 - z0)
    return X, Y, Z


# ---------------------------------------------------------------- shape
root = group(NAME)
g_base = group("base", root)
g_stone = group("stone", root)
g_ore = group("ore", root)
g_frag = group("fragments", root)
g_det = group("details", root)


def h2(v): return round(v * 2) / 2


def box(cx, cz, y0, w, d, h):
    w, d, h = h2(w), h2(d), h2(h)
    x0, z0 = h2(cx - w / 2), h2(cz - d / 2)
    return [x0, y0, z0], [x0 + w, h2(y0 + h), z0 + d]


# base: wide low slabs sunk into the ground
cube("base_1", g_base, [-9.5, -1, -7.5], [8.5, 1.5, 7.0])
cube("base_2", g_base, [-6.0, -1, -9.0], [6.5, 1.0, 9.5])

# stone mound: rings that get smaller and higher, jittered so the top is lumpy and uneven
stones = []
rings = [  # (count, radius x, radius z, y0 range, size range, height range)
    (10, 7.6, 6.6, (0.0, 0.5), (4.5, 7.0), (4.0, 6.5)),
    (8, 4.8, 4.2, (3.5, 5.0), (4.5, 6.5), (4.0, 6.0)),
    (5, 2.4, 2.2, (7.5, 9.0), (4.0, 5.5), (3.5, 5.0)),
    (2, 0.9, 0.9, (11.0, 12.0), (3.5, 4.5), (3.0, 4.0)),
]
for ri, (n, rx, rz, yr, sr, hr) in enumerate(rings):
    a0 = rng.uniform(0, math.tau)
    for i in range(n):
        a = a0 + i * math.tau / n + rng.uniform(-0.25, 0.25)
        cx, cz = rx * math.cos(a) + rng.uniform(-0.6, 0.6), rz * math.sin(a) + rng.uniform(-0.6, 0.6)
        frm, to = box(cx, cz, h2(rng.uniform(*yr)), rng.uniform(*sr), rng.uniform(*sr), rng.uniform(*hr))
        stones.append((f"stone_{len(stones) + 1}", frm, to))
# the tall stone at the back left (silhouette breaker), and a few cubes sticking out of the sides
for frm, to in ([[-5.0, 6.0, 1.0], [-1.0, 17.0, 5.0]], [[8.0, 0.0, -2.5], [11.0, 3.0, 1.5]],
                [[-11.0, 0.0, 0.5], [-8.0, 2.5, 3.5]], [[1.5, 0.0, 7.0], [5.0, 3.5, 10.0]]):
    stones.append((f"stone_{len(stones) + 1}", frm, to))
for name, frm, to in stones:
    cube(name, g_stone, frm, to)

SOLIDS = [(e["from"], e["to"]) for e in elements]          # the unrotated stone and base cubes


def inside(X, Y, Z, skip=None, pad=0.0):
    m = np.zeros(np.shape(X), bool)
    for k, (f, t) in enumerate(SOLIDS):
        if k == skip: continue
        m |= ((X > f[0] - pad) & (X < t[0] + pad) & (Y > f[1] - pad) & (Y < t[1] + pad) & (Z > f[2] - pad) & (Z < t[2] + pad))
    return m


def top_at(x, z):
    """Height of the mound at (x, z) (the highest stone top over that point)."""
    best = 0.0
    for f, t in SOLIDS:
        if f[0] <= x <= t[0] and f[2] <= z <= t[2]: best = max(best, t[1])
    return best


# ore chunks: big ones on top, smaller on the sides, rotated 10-40 degrees, half buried
ore_specs = [  # (angle round the mound, distance from centre, size w, h, d, rot x, rot z, yaw, two cubes?)
    (0.6, 1.5, 4.5, 5.0, 4.0, 24, -18, 20, True),
    (2.5, 3.5, 4.0, 4.5, 3.5, -20, 30, -15, False),
    (4.3, 4.0, 3.5, 4.5, 3.5, 32, 12, 40, True),
    (1.6, 6.5, 3.5, 4.0, 3.0, -14, -35, 10, False),
    (3.4, 7.0, 3.0, 3.5, 3.0, 18, 26, -30, False),
    (5.5, 6.8, 3.0, 3.0, 2.5, -28, -12, 25, False),
]
CHUNKS = []
for i, (ang, dist, w, h, d, rx, rz, yaw, two) in enumerate(ore_specs):
    cx, cz = dist * math.cos(ang), dist * 0.85 * math.sin(ang)
    base_y = top_at(cx, cz)
    sink = h * 0.55                                          # pushed about half into the stone
    frm, to = box(cx, cz, h2(base_y - sink), w, d, h)
    org = [h2(cx), h2(base_y - sink), h2(cz)]
    cube(f"copper_chunk_{i + 1}", g_ore, frm, to, rotation=(rx, yaw, rz), origin=org, kind=f"chunk_{i}")
    CHUNKS.append((frm, to))
    if two:                                                  # a second, smaller lump on top: a nugget shape
        f2, t2 = box(cx + w * 0.15, cz - d * 0.1, to[1] - 1.0, w * 0.6, d * 0.65, 2.5)
        cube(f"copper_chunk_{i + 1}_top", g_ore, f2, t2, rotation=(rx, yaw, rz), origin=org, kind=f"chunk_{i}t")

# sapphire accent on the east side (the T3 gem)
gx, gz = 7.0, -3.5
gy = top_at(gx - 1.0, gz) - 1.5
cube("sapphire_gem", g_ore, [gx - 0.5, gy, gz - 0.5], [gx + 1.0, gy + 2.5, gz + 1.0], rotation=(0, 30, -25),
     origin=[gx, gy, gz], kind="gem")

# loose fragments on the ground
frag_specs = [("stone_fragment_1", -10.5, -5.0, 2.0, 1.5, 2.0, 25, "frag_stone"),
              ("stone_fragment_2", 9.5, 5.5, 1.5, 1.0, 1.5, -40, "frag_stone"),
              ("stone_fragment_3", -3.0, -10.5, 2.0, 1.0, 1.5, 10, "frag_stone"),
              ("stone_fragment_4", 4.5, -10.0, 1.5, 1.5, 1.5, 55, "frag_stone"),
              ("copper_fragment_1", 10.5, -6.0, 1.5, 1.0, 1.5, 30, "frag_ore"),
              ("copper_fragment_2", -8.5, 7.5, 1.0, 1.0, 1.0, -20, "frag_ore"),
              ("copper_fragment_3", 6.5, 10.5, 1.5, 1.0, 1.0, 15, "frag_ore")]
for name, x, z, w, h, d, yaw, kind in frag_specs:
    frm, to = box(x, z, 0.0, w, d, h)
    cube(name, g_frag, frm, to, rotation=(0, yaw, 0), origin=[x, 0, z], kind=kind)

# moss cushions on two of the highest stones (moss is also painted on the top faces)
tops = sorted(stones, key=lambda s: -s[2][1])
for k, (name, frm, to) in enumerate([tops[1], tops[3]]):
    w, d = to[0] - frm[0], to[2] - frm[2]
    f = [h2(frm[0] + w * 0.15), to[1], h2(frm[2] + d * 0.2)]
    t = [h2(f[0] + max(1.5, w * 0.55)), to[1] + 0.5, h2(f[2] + max(1.5, d * 0.5))]
    cube(f"moss_cushion_{k + 1}", g_det, f, t, kind="moss")

# grass tufts at the base: two crossed alpha cards each
for k, (x, z) in enumerate([(-8.5, -7.0), (9.0, 2.5), (-2.0, 9.5)]):
    for j, yaw in enumerate((45, -45)):
        cube(f"grass_tuft_{k + 1}_{j + 1}", g_det, [x - 2.0, 0, z], [x + 2.0, 3.0, z], rotation=(0, yaw, 0),
             origin=[x, 0, z], kind="grass", hidden=("down", "up", "east", "west"))


# ---------------------------------------------------------------- visibility
TANGENTS = {"north": ((1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)), "east": ((0, 0, 1), (0, 1, 0)),
            "west": ((0, 0, 1), (0, 1, 0)), "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1))}


def visible(X, Y, Z, face, skip):
    """Texels that can be seen: a ray along the normal, or tilted 50 degrees toward any side, gets out
    of the mound (12 units) without passing through another stone or going under the ground."""
    n = np.array(NORMAL[face], float); t1, t2 = (np.array(t, float) for t in TANGENTS[face])
    dirs = [n] + [n + s * t for t in (t1, t2) for s in (1.2, -1.2)]
    out = np.zeros(np.shape(X), bool)
    for d in dirs:
        d = d / np.linalg.norm(d)
        free = np.ones(np.shape(X), bool)
        for step in np.arange(0.3, 12.0, 0.5):
            px_, py_, pz_ = X + d[0] * step, Y + d[1] * step, Z + d[2] * step
            free &= ~inside(px_, py_, pz_, skip=skip) & (py_ > -0.2)
        out |= free
    return out


# ---------------------------------------------------------------- painters
def vein_lines(X, Y, Z):
    """Copper veins as 1 px lines: where a smooth 3D noise crosses its middle value between neighbouring
    texels. The field is in world space, so a vein runs on over an edge onto the next face and stone.
    A second, finer family branches off in patches. Returns (line, bed): the vein and the darker bed beside it."""
    def crossings(f):
        s_ = f > 0
        m = np.zeros(f.shape, bool)
        m[:, :-1] |= s_[:, :-1] != s_[:, 1:]
        m[:-1, :] |= s_[:-1, :] != s_[1:, :]
        return m
    a = fbm(X * 0.13 + 3.1, Y * 0.17 + 1.7, Z * 0.13 + 5.3) - 0.5
    b = fbm(X * 0.27 + 11.0, Y * 0.27 + 7.0, Z * 0.27 + 2.0) - 0.5
    patch = fbm(X * 0.1 + 40.0, Y * 0.1, Z * 0.1 + 17.0) > 0.52
    line = crossings(a) | (crossings(b) & patch)
    bed = np.zeros(line.shape, bool)
    bed[:, 1:] |= line[:, :-1]; bed[1:, :] |= line[:-1, :]
    return line, bed & ~line


def moss_field(X, Z):
    return fbm(X * 0.22 + 20.0, 0.0, Z * 0.22 + 9.0)


def paint_stone(e, face, w, h):
    frm, to = e["from"], e["to"]
    X, Y, Z = face_points(frm, to, face, w, h)
    nx, ny, nz = NORMAL[face]
    k = SOLIDS.index((frm, to)) if (frm, to) in SOLIDS else None
    covered = inside(X + nx * 0.2, Y + ny * 0.2, Z + nz * 0.2, skip=k) | ((Y < 0.05) & (face != "up"))
    if covered.all() or not (visible(X, Y, Z, face, k) & ~covered).any():
        return None                                           # nothing of it can be seen: no UV
    # base value from the face direction, a slightly darker grey low on the mound
    v = np.full((h, w), 5.4 + FACE_LIGHT[face] * 1.3) + np.clip(Y / 17.0, 0, 1) * 1.2
    # rounded form: lighter centre, darker toward the face edges (most at the bottom and outer edges)
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    edge = np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)       # px from the nearest edge
    v -= np.clip(1.0 - edge / 3.0, 0, 1) * 1.4
    if face not in ("up", "down"):
        v -= V * 0.9                                          # darker toward the bottom of side faces
        v += np.clip(1.0 - V * h / 2.0, 0, 1) * 0.6           # the top edge catches the light
    # crevices: texels with another stone just in front of them are in shadow (soft, 2 steps)
    near1 = inside(X + nx * 0.9, Y + ny * 0.9, Z + nz * 0.9, skip=k)
    near2 = inside(X + nx * 1.8, Y + ny * 1.8, Z + nz * 1.8, skip=k)
    v -= near1 * 1.6 + near2 * 0.8
    v -= np.clip(1.0 - Y / 2.0, 0, 1) * 1.2 * (face != "up")  # contact shadow at the ground
    # big soft lumps across the stone, then low contrast noise in clusters
    v += (fbm(X * 0.35, Y * 0.35, Z * 0.35) - 0.5) * 2.4
    v = dither(v, w, h)
    rgb = ramp_colour("stone", v)
    # chiselled cracks: a 1 px dark line with a light pixel beside it
    for _ in range(max(0, (w * h) // 90)):
        x, y = int(nrng.integers(1, max(2, w - 1))), int(nrng.integers(1, max(2, h - 1)))
        for _s in range(int(nrng.integers(3, 7))):
            if 0 <= x < w and 0 <= y < h and not covered[y, x]:
                rgb[y, x] = ramp_colour("stone", v[y, x] - 2.0)
                if x + 1 < w: rgb[y, x + 1] = ramp_colour("stone", v[y, x + 1] + 1.0)
            x += int(nrng.choice([-1, 0, 1])); y += int(nrng.choice([0, 1, 1]))
    # copper veins wandering over the faces and on over the edges (world space)
    core, rim = vein_lines(X, Y, Z)
    cv = 4.0 + FACE_LIGHT[face] * 0.8 + (fbm(X * 0.5, Y * 0.5, Z * 0.5) - 0.5) * 2.0 - near1 * 1.5
    rgb[core] = ramp_colour("copper", cv)[core]
    rgb[rim] = ramp_colour("stone", v - 1.0)[rim]             # a soft darker bed under the vein
    # moss on the top faces of the upper stones, spilling 1 to 2 px over the edge
    if Y.max() > 6.0:
        mf = moss_field(X, Z)
        top_y = to[1]
        up_open = not inside(np.array([(frm[0] + to[0]) / 2]), np.array([top_y + 0.3]), np.array([(frm[2] + to[2]) / 2]), skip=k)[0]
        if face == "up":
            mm = (mf > 0.5) & ~covered
        else:
            mm = (mf > 0.52) & (Y > top_y - 1.0 + (mf - 0.52) * 3.0) & ~covered
            mm &= up_open
        mv = 3.4 + (mf - 0.5) * 6 + FACE_LIGHT[face] * 0.6
        rgb[mm] = ramp_colour("moss", mv)[mm]
    return rgb, np.ones((h, w), bool)


def paint_chunk(face, w, h, seed, rot_=None):
    """Copper nugget, polished: a baked metal reflection that follows the chunk's tilt (ore_metal.tone),
    darker where it sinks into the stone, soft lumps, a near-white hot spot and green patina on the edges."""
    r = np.random.default_rng(seed)
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    edge = np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)
    top = len(RAMPS["copper"]) - 1
    t = OM.tone(rot_, face, w, h, "metal", dome=.62, seed=seed)
    v = top * 0.5 + (t - 0.5) * top * 1.2
    if face not in ("up", "down"):
        v -= V * 1.2                                          # darkens toward where it sinks into the stone
    for _ in range(2):                                        # soft lumps of the nugget
        cx, cy, rr = r.uniform(0.2, 0.8), r.uniform(0.2, 0.8), r.uniform(0.15, 0.3)
        v += np.clip(1.0 - np.hypot(U - cx, V - cy) / rr, 0, 1) * r.choice([-0.6, 0.5])
    v = dither(v, w, h)
    rgb = ramp_colour("copper", v)
    if face in ("up", "west", "north"):
        rgb[t > 0.9] = RAMPS["copper"][-1]                    # the hot spot
    pat = (edge < 1.0) & (r.random((h, w)) < 0.16)            # green patina pixels on the edges
    pat |= (edge < 1.0) & (V > 0.75) & (r.random((h, w)) < 0.45)
    grow = pat.copy(); grow[1:, :] |= pat[:-1, :] & (r.random((h - 1, w)) < 0.3)
    pv = 2.8 + FACE_LIGHT[face] * 0.6 - V * 0.8 + r.random((h, w)) * 0.8
    rgb[grow] = ramp_colour("patina", pv)[grow]
    return rgb, np.ones((h, w), bool)


def paint_gem(face, w, h):
    """Sapphire: facet halves (diagonal light and dark), a bright glint."""
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    v = np.full((h, w), 3.6 + FACE_LIGHT[face]) + np.where(U + V < 1.0, 1.0, -0.6) - V * 0.8
    rgb = ramp_colour("sapph", v)
    if face in ("up", "west", "north") and w >= 2 and h >= 2:
        rgb[0, 0] = RAMPS["sapph"][-1]; rgb[min(1, h - 1), min(1, w - 1)] = RAMPS["sapph"][-2]
    return rgb, np.ones((h, w), bool)


def paint_frag_stone(face, w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    v = np.full((h, w), 4.0 + FACE_LIGHT[face]) - (V * 1.2 if face not in ("up", "down") else 0)
    v -= np.clip(1.0 - np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h) / 2, 0, 1) * 0.8
    return ramp_colour("stone", dither(v, w, h)), np.ones((h, w), bool)


def paint_moss(face, w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    v = np.full((h, w), 3.2 + FACE_LIGHT[face] * 0.8)
    v += np.clip(1.0 - np.hypot(U - 0.45, V - 0.4) * 2.2, 0, 1) * 1.2
    v += (np.random.default_rng(7).random((h, w)) - 0.5) * 0.9
    return ramp_colour("moss", dither(v, w, h)), np.ones((h, w), bool)


def paint_grass(face, w, h, seed):
    """One alpha card: 4 blades from the base, each darker at the root and lighter at the tip."""
    r = np.random.default_rng(seed)
    rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
    for k in range(4):
        x = (k + r.uniform(0.2, 0.8)) * w / 4; top = int(r.integers(0, h // 2)); lean = r.uniform(-0.25, 0.25)
        for y in range(h - 1, top - 1, -1):
            xi = int(round(x + lean * (h - 1 - y)))
            if 0 <= xi < w:
                t = (h - 1 - y) / max(1, h - 1 - top)
                rgb[y, xi] = ramp_colour("grass", 1.0 + t * 4.0 + (0.5 if face == "north" else 0))
                a[y, xi] = True
    return rgb, a


# ---------------------------------------------------------------- pack the faces into the atlas
rects = {}                                                    # key -> {w, h, rgb, a}


def add_rect(key, w, h, paint):
    if key not in rects:
        res = paint()
        if res is None: return None
        rects[key] = {"w": w, "h": h, "rgb": res[0], "a": res[1]}
    return key


for e in elements:
    kind, frm, to = e["_kind"], e["from"], e["to"]
    for face in FACES:
        if face in e["_hidden"]:
            e["faces"][face] = None; continue
        w, h = (px(v) for v in face_dims(frm, to, face))
        if kind == "stone":
            key = add_rect(f"{e['name']}:{face}", w, h, lambda e=e, face=face, w=w, h=h: paint_stone(e, face, w, h))
        elif kind.startswith("chunk"):
            key = add_rect(f"{kind}:{face}", w, h, lambda e=e, face=face, w=w, h=h, s=len(rects): paint_chunk(face, w, h, 50 + s, e.get('rotation')))
        elif kind == "gem":
            key = add_rect(f"gem:{face}", w, h, lambda face=face, w=w, h=h: paint_gem(face, w, h))
        elif kind == "frag_stone":                            # fragments of one size share a swatch
            key = add_rect(f"fs:{face}:{w}x{h}", w, h, lambda face=face, w=w, h=h: paint_frag_stone(face, w, h))
        elif kind == "frag_ore":
            key = add_rect(f"fo:{face}:{w}x{h}", w, h, lambda e=e, face=face, w=w, h=h: paint_chunk(face, w, h, 9, e.get('rotation')))
        elif kind == "moss":
            key = add_rect(f"moss:{face}:{w}x{h}", w, h, lambda face=face, w=w, h=h: paint_moss(face, w, h))
        elif kind == "grass":
            key = add_rect(f"grass:{e['name'][-3]}:{face}", w, h, lambda face=face, w=w, h=h, s=len(rects): paint_grass(face, w, h, s))
        e["faces"][face] = key

# shelf packing, tallest first, with a 2 px gap (fix_texture_bleed pads the edges afterwards)
GAP = 2
x = y = shelf = 0
for k, r in sorted(rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
    if x + r["w"] > TEX: x, y, shelf = 0, y + shelf + GAP, 0
    r["x"], r["y"] = x, y; x += r["w"] + GAP; shelf = max(shelf, r["h"])
used = y + shelf
import collections
ar = collections.Counter()
for k, r in rects.items(): ar[k.split(":")[0].rstrip("0123456789_") if not k.startswith("chunk") else "chunk"] += r["w"] * r["h"]
print("AREA", dict(ar), sum(ar.values()), "of", TEX * TEX)
if used > TEX: raise SystemExit(f"atlas overflow: {used}px of {TEX}")
img = np.zeros((TEX, TEX, 4), np.uint8)
for r in rects.values():
    img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], :3] = r["rgb"]
    img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], 3] = np.where(r["a"], 255, 0)

for e in elements:
    for face in FACES:
        key = e["faces"][face]
        if key is None:
            e["faces"][face] = {"uv": [0, 0, 0, 0], "texture": None}
        else:
            r = rects[key]
            e["faces"][face] = {"uv": [r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]], "texture": 0}
    e.pop("_kind"); e.pop("_hidden")

# ---------------------------------------------------------------- write
buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()


def group_json(g):
    return {"name": g["name"], "uuid": g["uuid"], "export": True, "locked": False, "scope": 0, "selected": False,
            "visibility": True, "origin": g["origin"], "rotation": [0, 0, 0], "color": 0, "children": [],
            "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": True, "primary_selected": False}


def outliner(name):
    g = groups[name]
    return {"uuid": g["uuid"], "isOpen": True, "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}


model = {
    "meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
    "name": NAME, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
    "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
    "resolution": {"width": TEX, "height": TEX},
    "elements": elements, "groups": [group_json(g) for g in groups.values()], "outliner": [outliner(NAME)],
    "textures": [{"name": f"{NAME}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                  "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                  "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                  "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                  "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                  "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": new_uuid(),
                  "source": src}],
    "animations": [],
}
os.makedirs(OUT, exist_ok=True)
out = os.path.join(OUT, f"{NAME}.bbmodel")
with open(out, "w", encoding="utf8") as fh:
    json.dump(model, fh, indent="\t")
sys.path.insert(0, REPO_SCRIPTS)
import fix_texture_bleed
res = fix_texture_bleed.pad_file(out, [os.path.join(OUT, f"{NAME}.png")])
colours = len({tuple(c) for c in img[img[..., 3] > 0][:, :3]})
xs = [v for e in elements for v in (e["from"][0], e["to"][0])]
zs = [v for e in elements for v in (e["from"][2], e["to"][2])]
print(f"{NAME}: cubes={len(elements)} faces={len(rects)} atlas={used}/{TEX} -> {res['size']} colours={colours} "
      f"x {min(xs)}..{max(xs)} z {min(zs)}..{max(zs)} top {max(e['to'][1] for e in elements)}")
