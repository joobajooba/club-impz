"""Rocks and boulders for every biome (blockbench_detailed_prompts.md section 3.3): <biome>_rock_<size>
for small, medium and large, the three sizes of a biome sharing one texture (the doc's rule).

Shapes per biome (the doc's "rounded boulder | flat slab | jagged spire | rock pile"):
  forest    rounded mossy boulder, grey green stone, moss cushions and grass, pale lichen
  mountain  jagged stepped crag, blue grey stone, orange lichen, pebbles
  frost     rounded boulder, pale icy stone, snow caps spilling over, ice shards
  plains    flat layered slabs, sandy stone in strata bands, dry grass
  swamp     low sunken boulder, dark wet stone, moss, slime drips, small mushrooms
  void      jagged spire, black purple stone with glints, chips floating above
  stellar   rock pile, dark blue stone dusted with yellow stars, star sparkles (_glow)

Built like the ore veins (build_ore_veins.py): the stone is painted in world space (moss, snow, strata,
cracks and stars run over the edges), crevices where stones meet are shaded, faces nobody can see get no
UV. 2 px/unit, one 256 texture per biome (J00BA chose 256 over the doc's 64/128, 2026-11-08), no animations.
Each biome's three sizes are built in one temporary file, padded once (fix_texture_bleed), then split.
Usage: py -3 build_rocks.py [forest mountain ...]   (no args = all seven)
"""
import base64, copy, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image

OUT = r"C:\Users\lucas\blockbench_models\rocks"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
TEX = 256
PPU = 2
R = lambda s: s.split()

STONE = {
    "forest":   R("#151a17 #1c231e #232c25 #2b352d #343f36 #3e4a40 #48554a #536155 #5f6d60 #6b7a6c #788778 #869585"),
    "mountain": R("#14171f #1a1e28 #212632 #282e3c #303747 #384152 #414b5d #4b5668 #566174 #626d80 #6f7a8c #7d8899"),
    "frost":    R("#3a4552 #46525f #535f6d #606d7b #6e7b89 #7c8a97 #8b98a5 #9aa7b2 #a9b5bf #b8c3cc #c7d0d8 #d5dde3"),
    "plains":   R("#3a2a1c #4a3624 #5a432c #6b5135 #7c603f #8d6f4a #9e7e56 #ae8e63 #bd9e72 #cbad82 #d8bd93 #e3cca5"),
    "swamp":    R("#0e120e #131812 #191f17 #1f261c #252e22 #2c3628 #333e2e #3b4735 #43503c #4c5944 #55634c #5f6d55"),
    "void":     R("#0a070f #0f0b16 #140f1d #1a1325 #20182d #271d35 #2e233e #362947 #3e3050 #47375a #503f64 #5a476e"),
    "stellar":  R("#090d1c #0d1224 #11182e #161e38 #1b2542 #212c4c #273457 #2e3c62 #35456c #3d4e76 #455881 #4e628b"),
}
EXTRA = {
    "moss":     R("#1e3014 #2e481a #42621f #5c7e28 #7a9a34 #94b23e"),
    "lichen_o": R("#5a3010 #7a4416 #a05e1e #c47c2c #dc9c44 #ecbc68"),
    "lichen_g": R("#4a5a3a #63744c #7e8f60 #98a876 #b2c08e #cad6a8"),
    "snow":     R("#8ea4bc #a6bccf #bed0de #d2e0ea #e2ecf2 #eef4f8"),
    "ice":      R("#2e5070 #4874a0 #6c9cc8 #9cc8e8 #d0ecf8 #eef8fc"),
    "slime":    R("#16260c #213a10 #2e5214 #3e6c18 #52881c #6aa424 #8cc23a"),
    "grass":    R("#1a3412 #264c18 #33661e #447f26 #5a9a30 #78b440"),
    "dry":      R("#4a3a1a #64502a #806838 #9c8248 #b89e5c #d0b874"),
    "reed":     R("#1c2a14 #28381a #364a20 #465c28 #587032 #6e863c"),
    "cap":      R("#3e1418 #6a2219 #963420 #bc4a28 #d86a38 #ea8c4c"),
    "stem":     R("#5a4c48 #7e6e62 #a4927c #c4b498 #ddd0b4"),
    "glint":    R("#4a1878 #7428b0 #a448e0 #d06cff #f0c8ff"),
    "star":     R("#c89a2a #ecbc2c #fad43e #ffe45c #fff08c #fffbd0"),
}
# style: shape generator. top: cover painted on the up faces. size: (width, height) per size.
CFG = {
    "forest":   dict(seed=101, style="rounded", top="moss", lichen="lichen_g", base="grass", extras=["moss_cushion", "pebbles"]),
    "mountain": dict(seed=202, style="jagged", top="none", lichen="lichen_o", base="none", extras=["pebbles", "strata_faint"]),
    "frost":    dict(seed=303, style="rounded", top="snow", lichen=None, base="none", extras=["snow_cap", "ice", "pebbles"]),
    "plains":   dict(seed=404, style="slab", top="none", lichen="lichen_o", base="dry", extras=["strata", "pebbles"]),
    "swamp":    dict(seed=505, style="sunken", top="moss", lichen=None, base="reed", extras=["moss_cushion", "drips", "mushrooms", "wet"]),
    "void":     dict(seed=606, style="spire", top="none", lichen=None, base="none", extras=["glints", "float"]),
    "stellar":  dict(seed=707, style="pile", top="none", lichen=None, base="none", extras=["stars", "sparkles"]),
}
# warm / cool drift per biome (r, g, b multipliers, +-): forest moss green vs bare grey, plains red vs yellow sand...
TINT = {"forest": (-0.4, 0.5, -0.2), "mountain": (-0.3, -0.1, 0.5), "frost": (-0.3, 0.0, 0.4), "plains": (0.5, 0.1, -0.5),
        "swamp": (-0.2, 0.5, -0.3), "void": (0.4, -0.3, 0.6), "stellar": (-0.3, 0.0, 0.6)}
SIZES = {"small": (7.0, 4.5), "medium": (15.0, 9.0), "large": (28.0, 17.0)}
OFFSET = {"small": -40.0, "medium": 0.0, "large": 50.0}    # where each size sits in the temporary file

FACES = ("north", "east", "south", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
TANGENTS = {"north": ((1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)), "east": ((0, 0, 1), (0, 1, 0)),
            "west": ((0, 0, 1), (0, 1, 0)), "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1))}
FACE_LIGHT = {"up": 1.6, "north": 0.5, "west": 0.6, "south": -0.1, "east": -0.3, "down": -1.8}


def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def h2(v): return round(v * 2) / 2


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


def build(biome):
    C = CFG[biome]
    rng = random.Random(C["seed"])
    nrng = np.random.default_rng(C["seed"])
    RAMPS = {"stone": STONE[biome], **EXTRA}
    RAMPS = {k: [hexc(c) for c in v] for k, v in RAMPS.items()}

    def ramp_colour(name, v):
        r = RAMPS[name]; n = len(r)
        q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
        lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
        return (np.array(r)[lo] * (1 - f) + np.array(r)[hi] * f).round().astype(np.uint8)

    perm = np.arange(256); np.random.default_rng(C["seed"]).shuffle(perm); perm = np.concatenate([perm, perm])
    grad = np.random.default_rng(C["seed"] + 1).random(256)

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

    elements, groups = [], {}

    def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

    def group(name, parent=None):
        groups[name] = {"name": name, "uuid": new_uuid(), "origin": [0, 0, 0], "children": []}
        if parent: groups[parent]["children"].append(("g", name))
        return name

    def cube(size, name, grp, frm, to, rotation=(0, 0, 0), origin=None, kind="stone", hidden=("down",)):
        origin = origin or [(frm[i] + to[i]) / 2 for i in range(3)]
        e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
             "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
             "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": {}, "type": "cube",
             "uuid": new_uuid(), "_kind": kind, "_hidden": set(hidden), "_size": size}
        if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(v, 3) for v in rotation]
        elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
        return e

    def box(cx, cz, y0, w, d, h):
        w, d, h = max(0.5, h2(w)), max(0.5, h2(d)), max(0.5, h2(h))
        x0, z0 = h2(cx - w / 2), h2(cz - d / 2)
        return [x0, y0, z0], [x0 + w, h2(y0 + h), z0 + d]

    SOLIDS = {}                                     # size -> list of (from, to) stone cubes (world, offset)

    for size, (W, H) in SIZES.items():
        ox = OFFSET[size]
        name = f"{biome}_rock_{size}"
        root = group(name)
        g_base = group(f"{size}:base", root); g_stone = group(f"{size}:stone", root); g_det = group(f"{size}:details", root)
        stones = []
        k = W / 15.0                                 # 1 = the medium rock
        style = C["style"]

        def add(cx, cz, y0, w, d, h):
            stones.append(box(ox + cx, cz, y0, w, d, h))

        def mound(cx, cz, r, hgt, levels, shrink=0.62, ring=7, jitter=0.25, y0=0.0, tall=1.0, profile=None):
            """Rings of boxes, one ring per level: a lumpy mound. profile = each level's radius (x r), so a
            boulder can bulge out in the middle; without one each level shrinks by `shrink`."""
            y = y0
            prof = profile or [shrink ** li for li in range(levels)]
            levels = len(prof)
            for li in range(levels):
                rr = r * prof[li]
                n = max(1, int(round(ring * min(1.0, prof[li]) * (0.6 if size == "small" else 1.0))))
                lh = hgt / levels * rng.uniform(1.1, 1.5) * tall
                a0 = rng.uniform(0, math.tau)
                for i in range(n):
                    a = a0 + i * math.tau / n + rng.uniform(-jitter, jitter)
                    dist = rr * (0.55 if n > 1 else 0.0)
                    bw = rr * rng.uniform(0.9, 1.3); bd = rr * rng.uniform(0.8, 1.2)
                    add(cx + dist * math.cos(a), cz + dist * 0.9 * math.sin(a), h2(y), bw, bd, lh * rng.uniform(0.8, 1.15))
                y += hgt / levels * 0.85

        if style == "rounded":                       # a boulder: narrower foot, wide belly, rounded crown
            mound(0, 0, W * 0.42, H, 0, profile=[0.86, 1.0, 0.8, 0.46] if size != "small" else [0.95, 0.8, 0.45])
        elif style == "sunken":                      # half sunk into the mud: low and wide, belly at the ground
            mound(0, 0, W * 0.48, H * 0.7, 0, profile=[1.0, 0.82, 0.5], y0=-0.5)
        elif style == "jagged":                      # stepped crag: tall offset blocks, a cliff face on one side
            mound(0, 0, W * 0.4, H * 0.75, 3, shrink=0.7, ring=6, jitter=0.4, tall=1.3)
            for i in range(2 if size == "small" else 3):
                a = rng.uniform(0, math.tau)
                add(W * 0.15 * math.cos(a), W * 0.12 * math.sin(a), 0.0, W * rng.uniform(0.16, 0.24), W * rng.uniform(0.14, 0.2),
                    H * rng.uniform(0.85, 1.15))
        elif style == "spire":                       # one tall leaning spire of stacked blocks on a jagged base
            mound(0, 0, W * 0.38, H * 0.45, 2, shrink=0.7, ring=6, jitter=0.4)
            y, cx, cz, w = 0.0, 0.0, 0.0, W * 0.3
            for i in range(4 if size != "small" else 3):
                hh = H * 0.32
                add(cx, cz, h2(y), w, w * 0.85, hh)
                y += hh * 0.9; cx += W * 0.04 * rng.choice([-1, 1]); cz += W * 0.03; w *= 0.74
        elif style == "slab":                        # flat layered slabs: wide, low, each layer offset
            y = 0.0
            for li in range(3 if size != "small" else 2):
                n = 3 if size != "small" else 2
                for i in range(n):
                    a = rng.uniform(0, math.tau)
                    off = W * 0.12 * (li + 0.5)
                    add(off * math.cos(a) * 0.6, off * math.sin(a) * 0.6, h2(y), W * rng.uniform(0.55, 0.8) * (0.82 ** li),
                        W * rng.uniform(0.4, 0.6) * (0.85 ** li), H * rng.uniform(0.26, 0.34))
                y += H * 0.28
        elif style == "pile":                        # several boulders heaped together
            n = 2 if size == "small" else (3 if size == "medium" else 5)
            for b in range(n):
                a = b * math.tau / n + rng.uniform(-0.3, 0.3)
                dist = 0 if b == 0 else W * 0.26
                sc = 1.0 if b == 0 else rng.uniform(0.55, 0.75)
                mound(dist * math.cos(a), dist * math.sin(a), W * 0.3 * sc, H * sc, 0, ring=5, y0=0.0,
                      profile=[0.9, 1.0, 0.55] if size == "large" else [1.0, 0.6])
        if size != "small":                          # a low base slab, sunk into the ground (doc: base)
            cube(size, f"base_1", g_base, [h2(ox - W * 0.4), -1.0, h2(-W * 0.32)], [h2(ox + W * 0.4), 1.0, h2(W * 0.32)])
        for i, (frm, to) in enumerate(stones):
            cube(size, f"stone_{i + 1}", g_stone, frm, to)
        SOLIDS[size] = [(e["from"], e["to"]) for e in elements if e["_size"] == size and e["_kind"] == "stone"]

        def top_at(x, z):
            best = 0.0
            for f, t in SOLIDS[size]:
                if f[0] <= x <= t[0] and f[2] <= z <= t[2]: best = max(best, t[1])
            return best

        tops = sorted(SOLIDS[size], key=lambda st: -st[1][1])
        ex = C["extras"]
        cushion = "moss" if "moss_cushion" in ex else ("snow" if "snow_cap" in ex else None)
        if cushion:
            for i, (frm, to) in enumerate(tops[:(1 if size == "small" else 2)]):
                w, d = to[0] - frm[0], to[2] - frm[2]
                f = [h2(frm[0] + w * 0.12), to[1], h2(frm[2] + d * 0.15)]
                t = [h2(f[0] + max(1.0, w * (0.8 if cushion == "snow" else 0.55))), to[1] + (1.0 if cushion == "snow" else 0.5),
                     h2(f[2] + max(1.0, d * (0.7 if cushion == "snow" else 0.5)))]
                cube(size, f"{cushion}_{'cap' if cushion == 'snow' else 'cushion'}_{i + 1}", g_det, f, t, kind=cushion)
        if "ice" in ex and size != "small":
            for i in range(2 if size == "medium" else 3):
                a = rng.uniform(0, math.tau); r = W * 0.36
                x, z = ox + r * math.cos(a), r * math.sin(a)
                y = h2(max(0.0, top_at(x, z) - 1.5))
                f, t = box(x, z, y, 1.0, 1.0, rng.choice([2.0, 2.5, 3.0]))
                cube(size, f"ice_shard_{i + 1}", g_det, f, t, rotation=(rng.uniform(-30, 30), 45, rng.uniform(-30, 30)),
                     origin=[h2(x), y, h2(z)], kind="ice")
        if "pebbles" in ex:
            for i in range({"small": 2, "medium": 3, "large": 5}[size]):
                a = rng.uniform(0, math.tau); r = W * rng.uniform(0.5, 0.62)
                x, z = ox + r * math.cos(a), r * 0.9 * math.sin(a)
                s_ = rng.choice([1.0, 1.0, 1.5]) * (1.0 if size != "large" else 1.4)
                f, t = box(x, z, 0.0, s_, s_ * 0.8, max(0.5, s_ * 0.6))
                cube(size, f"pebble_{i + 1}", g_det, f, t, rotation=(0, rng.uniform(0, 90), 0), origin=[h2(x), 0, h2(z)], kind="pebble")
        if C["base"] != "none":
            for i in range({"small": 1, "medium": 2, "large": 3}[size]):
                a = rng.uniform(0, math.tau); r = W * rng.uniform(0.42, 0.55)
                x, z = h2(ox + r * math.cos(a)), h2(r * 0.9 * math.sin(a))
                hgt = {"grass": 3.0, "dry": 4.0, "reed": 5.0}[C["base"]]
                for j, yaw in enumerate((45, -45)):
                    cube(size, f"{C['base']}_tuft_{i + 1}_{j + 1}", g_det, [x - 2.0, 0, z], [x + 2.0, hgt, z], rotation=(0, yaw, 0),
                         origin=[x, 0, z], kind="card_" + C["base"], hidden=("down", "up", "east", "west"))
        if "drips" in ex:
            for i in range({"small": 1, "medium": 3, "large": 5}[size]):
                frm, to = tops[rng.randrange(min(len(tops), 4))]
                side = rng.choice("nsew")
                x = rng.uniform(frm[0] + 0.5, max(frm[0] + 0.5, to[0] - 1.0)); z = rng.uniform(frm[2] + 0.5, max(frm[2] + 0.5, to[2] - 1.0))
                if side == "n": z = frm[2] - 0.5
                if side == "s": z = to[2]
                if side == "e": x = to[0]
                if side == "w": x = frm[0] - 0.5
                L = rng.choice([1.5, 2.0, 2.5])
                cube(size, f"slime_drip_{i + 1}", g_det, [h2(x), h2(to[1] - L), h2(z)], [h2(x) + 0.5, h2(to[1]) + 0.5, h2(z) + 0.5], kind="slime")
        if "mushrooms" in ex and size != "small":
            for i in range(2 if size == "medium" else 3):
                a = rng.uniform(0, math.tau); r = W * 0.5
                x, z = h2(ox + r * math.cos(a)), h2(r * 0.9 * math.sin(a))
                cube(size, f"mushroom_{i + 1}_stem", g_det, [x, 0, z], [x + 0.5, 1.5, z + 0.5], kind="stem")
                cube(size, f"mushroom_{i + 1}_cap", g_det, [x - 0.5, 1.5, z - 0.5], [x + 1.0, 2.0, z + 1.0], kind="cap")
        if "float" in ex:                            # stone chips hanging in the air above the spire
            for i in range({"small": 1, "medium": 2, "large": 4}[size]):
                a = rng.uniform(0, math.tau); r = W * rng.uniform(0.15, 0.4)
                x, z = ox + r * math.cos(a), r * math.sin(a)
                y = h2(top_at(x, z) + rng.uniform(1.5, 3.5) * (1.4 if size == "large" else 1.0))
                s_ = 1.0 if size == "small" else rng.choice([1.0, 1.5, 2.0])
                f, t = box(x, z, y, s_, s_, s_ * 0.8)
                cube(size, f"floating_chip_{i + 1}", g_det, f, t, rotation=(rng.uniform(-25, 25), rng.uniform(0, 90), rng.uniform(-25, 25)),
                     kind="pebble", hidden=())
        if "sparkles" in ex:
            for i in range({"small": 1, "medium": 2, "large": 4}[size]):
                a = rng.uniform(0, math.tau); r = W * rng.uniform(0.1, 0.4)
                x, z = h2(ox + r * math.cos(a)), h2(r * math.sin(a))
                y = h2(top_at(x, z) + rng.uniform(0.5, 2.5))
                for j, yaw in enumerate((0, 90)):
                    cube(size, f"star_sparkle_{i + 1}_{j + 1}_glow", g_det, [x - 1.0, y, z], [x + 1.0, y + 2.0, z], rotation=(0, yaw, 0),
                         origin=[x, y, z], kind="sparkle", hidden=("down", "up", "east", "west"))

    # ---- painting
    def inside(size, X, Y, Z, skip=None):
        m = np.zeros(np.shape(X), bool)
        for k, (f, t) in enumerate(SOLIDS[size]):
            if k == skip: continue
            m |= (X > f[0]) & (X < t[0]) & (Y > f[1]) & (Y < t[1]) & (Z > f[2]) & (Z < t[2])
        return m

    def visible(size, X, Y, Z, face, skip):
        n = np.array(NORMAL[face], float); t1, t2 = (np.array(t, float) for t in TANGENTS[face])
        out = np.zeros(np.shape(X), bool)
        for d in [n] + [n + sg * t for t in (t1, t2) for sg in (1.2, -1.2)]:
            d = d / np.linalg.norm(d)
            free = np.ones(np.shape(X), bool)
            for step in np.arange(0.3, 12.0, 0.5):
                free &= ~inside(size, X + d[0] * step, Y + d[1] * step, Z + d[2] * step, skip) & (Y + d[1] * step > -0.2)
            out |= free
        return out

    ex = C["extras"]

    def paint_stone(e, face, w, h):
        size = e["_size"]; Hs = SIZES[size][1]
        frm, to = e["from"], e["to"]
        X, Y, Z = face_points(frm, to, face, w, h)
        nx, ny, nz = NORMAL[face]
        key = (frm, to)
        k = SOLIDS[size].index(key) if key in SOLIDS[size] else None
        covered = inside(size, X + nx * 0.2, Y + ny * 0.2, Z + nz * 0.2, k) | ((Y < 0.05) & (face != "up"))
        if covered.all() or not (visible(size, X, Y, Z, face, k) & ~covered).any():
            return None
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), 5.0 + FACE_LIGHT[face] * 1.3) + np.clip(Y / Hs, 0, 1) * 1.2
        v -= np.clip(1.0 - edge / 3.0, 0, 1) * 1.4
        if face not in ("up", "down"):
            v -= V * 0.9
            v += np.clip(1.0 - V * h / 2.0, 0, 1) * 0.6
        near1 = inside(size, X + nx * 0.9, Y + ny * 0.9, Z + nz * 0.9, k)
        near2 = inside(size, X + nx * 1.8, Y + ny * 1.8, Z + nz * 1.8, k)
        v -= near1 * 1.6 + near2 * 0.8
        v -= np.clip(1.0 - Y / 2.0, 0, 1) * 1.2 * (face != "up")
        v += (fbm(X * 0.3, Y * 0.3, Z * 0.3) - 0.5) * 2.6
        if "strata" in ex and face != "up":          # sandstone bands
            v += np.sin(Y * 1.6 + fbm(X * 0.2, 0, Z * 0.2) * 4.0) * 0.9
        if "strata_faint" in ex and face != "up":
            v += np.sin(Y * 1.1 + fbm(X * 0.2, 0, Z * 0.2) * 3.0) * 0.45
        if "wet" in ex:
            v -= np.clip(1.0 - Y / 3.0, 0, 1) * 1.0
        v = dither(v, w, h)
        rgb = ramp_colour("stone", v)
        drift = (fbm(X * 0.12 + 31, Y * 0.12, Z * 0.12 + 5) - 0.5) * 2.0 + (fbm(X * 0.6, Y * 0.6, Z * 0.6) - 0.5) * 0.6
        tint = np.array(TINT[biome], float)
        drift = np.clip(np.round(drift * 1.3), -1, 1) * 0.7      # three steps: keeps the palette to the doc's 40 to 120
        rgb = np.clip(rgb.astype(float) * (1.0 + drift[..., None] * tint * 0.22), 0, 255).astype(np.uint8)
        for _ in range(max(0, (w * h) // 80)):       # cracks: a dark line with a light pixel beside it
            x, y = int(nrng.integers(1, max(2, w - 1))), int(nrng.integers(1, max(2, h - 1)))
            for _s in range(int(nrng.integers(3, 8))):
                if 0 <= x < w and 0 <= y < h and not covered[y, x]:
                    rgb[y, x] = ramp_colour("stone", v[y, x] - 2.0)
                    if x + 1 < w: rgb[y, x + 1] = ramp_colour("stone", v[y, x + 1] + 1.0)
                x += int(nrng.choice([-1, 0, 1])); y += int(nrng.choice([0, 1, 1]))
        if C["lichen"]:                              # lichen spots in soft clusters
            lm = (fbm(X * 0.9 + 7, Y * 0.9, Z * 0.9 + 3) > 0.64) & ~covered & (face != "down")
            rgb[lm] = ramp_colour(C["lichen"], 2.5 + FACE_LIGHT[face] * 0.6 + (fbm(X * 2, Y * 2, Z * 2) - 0.5) * 3)[lm]
        if "glints" in ex:
            gl = (fbm(X * 2.2 + 1, Y * 2.2 + 5, Z * 2.2) > 0.71) & ~covered
            rgb[gl] = ramp_colour("glint", np.full((h, w), 3.0))[gl]
            ln = (np.abs(fbm(X * 0.2 + 9, Y * 0.2, Z * 0.2 + 1) - 0.5) < 0.012) & ~covered   # faint purple seams
            rgb[ln] = ramp_colour("glint", np.full((h, w), 1.5))[ln]
        if "stars" in ex:
            st = (fbm(X * 2.4 + 3, Y * 2.4 + 1, Z * 2.4 + 7) > 0.665) & ~covered
            rgb[st] = ramp_colour("star", 2.5 + nrng.random((h, w)) * 3.0)[st]
        if "wet" in ex and face not in ("up", "down"):  # wet sheen near the top of each face
            sh = (np.clip(1.0 - V * h / 2.5, 0, 1) > 0.5) & (fbm(X * 0.8, Y * 0.8, Z * 0.8) > 0.5)
            rgb[sh] = ramp_colour("stone", v + 2.5)[sh]
        top = C["top"]
        if top != "none" and Y.max() > Hs * 0.3:
            mf = fbm(X * 0.22 + 20.0, 0.0, Z * 0.22 + 9.0)
            up_open = not inside(size, np.array([(frm[0] + to[0]) / 2]), np.array([to[1] + 0.3]), np.array([(frm[2] + to[2]) / 2]), k)[0]
            thr = {"moss": 0.47, "snow": 0.34}[top]
            spill = {"moss": 1.0, "snow": 1.5}[top]
            if face == "up":
                mm = (mf > thr) & ~covered
            else:
                mm = (mf > thr + 0.02) & (Y > to[1] - spill + (mf - thr) * 3.0) & ~covered & up_open
            nmax = len(RAMPS[top]) - 1
            rgb[mm] = ramp_colour(top, nmax * 0.6 + (mf - thr) * 6 + FACE_LIGHT[face] * 0.6)[mm]
        return rgb, np.ones((h, w), bool)

    def paint_plain(ramp, face, w, h, base=0.55):
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS[ramp])
        v = np.full((h, w), n * base + FACE_LIGHT[face] * 0.8) - (V * 0.8 if face not in ("up", "down") else 0)
        v += np.clip(1.0 - np.hypot(U - 0.45, V - 0.4) * 2.2, 0, 1) * 1.0
        v -= np.clip(1.0 - edge / 2, 0, 1) * 0.6
        return ramp_colour(ramp, dither(v, w, h)), np.ones((h, w), bool)

    def paint_ice(face, w, h):
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), 3.0 + FACE_LIGHT[face]) + np.where(U + (1 - V) * 0.3 < 0.65, 0.8, -0.6) - V * 0.8
        rgb = ramp_colour("ice", dither(v, w, h))
        if face in ("up", "west", "north"): rgb[0:1, :] = RAMPS["ice"][-1]
        return rgb, np.ones((h, w), bool)

    def paint_blades(ramp, face, w, h, seed):
        r = np.random.default_rng(seed)
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        for kk in range(4):
            x = (kk + r.uniform(0.2, 0.8)) * w / 4; top = int(r.integers(0, h // 2)); lean = r.uniform(-0.25, 0.25)
            for y in range(h - 1, top - 1, -1):
                xi = int(round(x + lean * (h - 1 - y)))
                if 0 <= xi < w:
                    t = (h - 1 - y) / max(1, h - 1 - top)
                    rgb[y, xi] = ramp_colour(ramp, 1.0 + t * 4.0 + (0.5 if face == "north" else 0)); a[y, xi] = True
        return rgb, a

    def paint_sparkle(face, w, h):
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool); c = w // 2
        for i in range(w):
            for j in range(h):
                if i in (c - 1, c) or j in (h // 2 - 1, h // 2):
                    rgb[j, i] = ramp_colour("star", 5.0 - max(abs(i - c + 0.5), abs(j - h / 2 + 0.5)) * 0.9); a[j, i] = True
        return rgb, a

    def paint_pebble(face, w, h):
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), 5.4 + FACE_LIGHT[face]) - (V * 1.2 if face not in ("up", "down") else 0)
        v -= np.clip(1.0 - edge / 2, 0, 1) * 0.8
        rgb = ramp_colour("stone", dither(v, w, h))
        if "stars" in ex and w * h > 3: rgb[h // 2, w // 2] = RAMPS["star"][-1]
        if "glints" in ex and w * h > 3: rgb[h // 2, w // 2] = RAMPS["glint"][-2]
        return rgb, np.ones((h, w), bool)

    rects = {}

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
                key = add_rect(f"{e['uuid']}:{face}", w, h, lambda e=e, face=face, w=w, h=h: paint_stone(e, face, w, h))
            elif kind in ("moss", "snow", "slime", "stem", "cap"):
                ramp = kind
                key = add_rect(f"{kind}:{face}:{w}x{h}", w, h, lambda ramp=ramp, face=face, w=w, h=h: paint_plain(ramp, face, w, h))
            elif kind == "ice":
                key = add_rect(f"ice:{face}:{w}x{h}", w, h, lambda face=face, w=w, h=h: paint_ice(face, w, h))
            elif kind == "pebble":
                key = add_rect(f"pb:{face}:{w}x{h}", w, h, lambda face=face, w=w, h=h: paint_pebble(face, w, h))
            elif kind.startswith("card_"):
                ramp = kind[5:]
                key = add_rect(f"{kind}:{e['name'][-3]}:{face}", w, h, lambda ramp=ramp, face=face, w=w, h=h, s_=len(rects): paint_blades(ramp, face, w, h, s_))
            elif kind == "sparkle":
                key = add_rect(f"sparkle:{face}", w, h, lambda face=face, w=w, h=h: paint_sparkle(face, w, h))
            e["faces"][face] = key

    GAP = 2
    x = y = shelf = 0
    for kk, r in sorted(rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
        if x + r["w"] > TEX: x, y, shelf = 0, y + shelf + GAP, 0
        r["x"], r["y"] = x, y; x += r["w"] + GAP; shelf = max(shelf, r["h"])
    used = y + shelf
    if used > TEX: raise SystemExit(f"{biome}: atlas overflow {used}px of {TEX}")
    img = np.zeros((TEX, TEX, 4), np.uint8)
    for r in rects.values():
        img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], :3] = r["rgb"]
        img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], 3] = np.where(r["a"], 255, 0)
    sizes_of = {}
    for e in elements:
        for face in FACES:
            key = e["faces"][face]
            if key is None:
                e["faces"][face] = {"uv": [0, 0, 0, 0], "texture": None}
            else:
                r = rects[key]
                e["faces"][face] = {"uv": [r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]], "texture": 0}
        sizes_of[e["uuid"]] = e.pop("_size")
        e.pop("_kind"); e.pop("_hidden")

    # ---- write the combined file, pad it once, then split it into the three rocks
    def group_json(g):
        return {"name": g["name"].split(":")[-1], "uuid": g["uuid"], "export": True, "locked": False, "scope": 0,
                "selected": False, "visibility": True, "origin": g["origin"], "rotation": [0, 0, 0], "color": 0,
                "children": [], "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": True,
                "primary_selected": False}

    def outliner(name):
        g = groups[name]
        return {"uuid": g["uuid"], "isOpen": True, "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}

    def texture_json(name, src):
        return {"name": name, "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": new_uuid(), "source": src}

    def model(name, els, grps, outl, src):
        return {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": name,
                "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
                "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
                "resolution": {"width": TEX, "height": TEX}, "elements": els, "groups": grps, "outliner": outl,
                "textures": [texture_json(f"{biome}_rock.png", src)], "animations": []}

    buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
    src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
    os.makedirs(OUT, exist_ok=True)
    tmp = os.path.join(OUT, f"_{biome}_rocks_all.bbmodel")
    roots = [f"{biome}_rock_{s}" for s in SIZES]
    with open(tmp, "w", encoding="utf8") as fh:
        json.dump(model(f"{biome}_rocks_all", elements, [group_json(g) for g in groups.values()], [outliner(r) for r in roots], src),
                  fh, indent="\t")
    sys.path.insert(0, REPO_SCRIPTS)
    import fix_texture_bleed
    png = os.path.join(OUT, f"{biome}_rock.png")
    fix_texture_bleed.pad_file(tmp, [png])
    d = json.load(open(tmp, encoding="utf8"))
    os.remove(tmp)
    padded_src = d["textures"][0]["source"]
    gj = {g["uuid"]: g for g in d["groups"]}
    colours = len({tuple(c) for c in np.array(Image.open(png).convert("RGBA")).reshape(-1, 4) if c[3] > 0})
    for size in SIZES:
        ox = OFFSET[size]
        els = [copy.deepcopy(e) for e in d["elements"] if sizes_of[e["uuid"]] == size]
        for e in els:                                # back to the origin
            e["from"][0] -= ox; e["to"][0] -= ox; e["origin"][0] -= ox
        root = groups[f"{biome}_rock_{size}"]
        sub = [root["uuid"]] + [groups[c[1]]["uuid"] for c in root["children"] if c[0] == "g"]
        grps = [copy.deepcopy(gj[u]) for u in sub]
        out = os.path.join(OUT, f"{biome}_rock_{size}.bbmodel")
        with open(out, "w", encoding="utf8") as fh:
            json.dump(model(f"{biome}_rock_{size}", els, grps, [outliner(f"{biome}_rock_{size}")], padded_src), fh, indent="\t")
        xs = [v for e in els for v in (e["from"][0], e["to"][0])]
        print(f"{biome}_rock_{size:7s} cubes={len(els):3d} w={max(xs) - min(xs):5.1f} top={max(e['to'][1] for e in els):5.1f}")
    print(f"{biome}_rock.png atlas={used}/{TEX} colours={colours}")


if __name__ == "__main__":
    for b in (sys.argv[1:] or list(CFG)):
        build(b)
