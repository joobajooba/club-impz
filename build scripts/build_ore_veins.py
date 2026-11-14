"""Ore veins for every ore (blockbench_detailed_prompts.md section 3.2, ore tier table), built the way
copper_vein was (build_copper_vein.py): a lumpy stone mound painted in world space (ore veins, moss, snow,
stains and cracks run over the edges and from stone to stone), ore pieces pushed into it at angles, loose
fragments on the ground, the tier's gem as a small accent and the home biome's extras.

Each ore varies in size, stone, the shape of its ore (lumps, nuggets, crystal columns, glass shards,
jagged spikes), its signature stone detail and its biome extras (game_worlds.md 4.4 / 4.6):

  coal       T1 forest    low wide mound, matte black lumps with a dark grey sheen, sooty streaks, moss, grass
  tin        T2 forest    light grey stone, dull silver nuggets, pale speckles, moss, grass
  iron       T4 mountain  grey brown stone, silver steel chunks with bright bare metal, dark stains running down, lichen
  gold       T5 frost     warm grey stone, bright nuggets, glittering flecks, snow cap and drift
  obsidian   T6 mountain  dark basalt columns, glassy black purple shards with bright edges, scorched ash
  titanite   T7 plains    pale stone, tall steel blue crystal columns, dry grass
  dreadstone T8 swamp     wet swamp stone, dark red black jagged spikes, red glowing fissures (_glow), slime
  void       T9 void      black stone, glowing purple crystals (_glow), stone pieces floating above it
  stellarite T10 stellar  star dusted stone, white gold glowing crystals, star sparkles, floating fragments

2 px/unit, one embedded 256 texture each (J00BA chose 256 over the doc's 128 for copper_vein, 2026-11-08),
no animations (ore veins don't shake).
Usage: py -3 build_ore_veins.py [coal tin iron ...]   (no args = all but copper; copper_vein stays as built)
"""
import base64, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import ore_metal as OM

OUT = r"C:\Users\lucas\blockbench_models\ores"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
TEX = 256
PPU = 2

R = lambda s: s.split()
STONES = {  # 12 shades, dark -> light
    "mid_grey":   R("#191b21 #20232a #282b33 #30333c #393d46 #434750 #4e525b #5a5e67 #676b74 #757982 #858991 #979ba2"),
    "light_grey": R("#2a2d34 #34373f #3f434b #4b4f57 #585c64 #666a72 #747880 #83878e #92969c #a2a6ab #b3b6ba #c4c7ca"),
    "grey_brown": R("#1e1916 #27201c #312822 #3b3029 #463931 #52433a #5e4d43 #6b584d #786458 #867164 #957f71 #a58e80"),
    "warm_grey":  R("#211c1a #2a2421 #342d29 #3f3732 #4a413b #564c45 #625750 #6f645c #7c7068 #8a7e75 #998c83 #a99c92"),
    "basalt":     R("#0e0d13 #131219 #18171f #1e1c26 #24222d #2b2934 #33303c #3b3845 #44414e #4e4b58 #595663 #66636f"),
    "pale":       R("#3e4048 #4b4e56 #595c64 #686b72 #777a81 #878a90 #979a9f #a7aaae #b6b9bc #c5c8ca #d3d5d6 #e0e1e1"),
    "swamp":      R("#0f120e #141812 #1a1f17 #20261c #272e22 #2e3628 #363f2e #3f4835 #48523c #525c44 #5c674c #677255"),
    "void_black": R("#0b0810 #100c17 #15101e #1a1425 #20192d #261e35 #2d243e #352a47 #3d3150 #46385a #504064 #5a486e"),
    "star_dust":  R("#090d1c #0d1224 #11182e #161e38 #1b2542 #212c4c #273457 #2e3c62 #35456c #3d4e76 #455881 #4e628b"),
}
ORE = {  # ore ramps from the doc table, widened to 8 to 10 shades with hue shifted ends
    "coal":       R("#0e0e14 #14141b #1a1a22 #22232c #2a2c36 #343742 #3e4250 #4a4e5c #5a6070"),
    "tin":        R("#3a3e44 #4a4f56 #5c6268 #6e757c #828990 #969ca3 #aab0b6 #c0c6cb #d6dbe0 #e8ecef"),
    "iron":       R("#1c1f24 #2a2e34 #3a3f46 #4c525a #60676f #767e87 #8e969f #aab1b9 #ccd2d8"),   # silver steel (J00BA, 2026-11-14; was rusty orange)
    "gold":       R("#3e2400 #6b4100 #8c5a06 #ad760e #cc9418 #e6b22a #f5cc48 #ffe27a #fff2b8"),
    "obsidian":   R("#07040c #0d0814 #150e20 #1f162e #2b1f40 #3a2a55 #4c376e #5e4486 #6a4c9c #8a6cc0"),
    "titanite":   R("#121e2e #1e3248 #28425e #345474 #42688a #547ea2 #6896ba #82b0d2 #a8d4f0 #d2ecfa"),
    "dreadstone": R("#0e0304 #1c0608 #2c0a0e #3e0e14 #54121a #6c1820 #861e26 #b0242c #d4483c"),
    "void":       R("#120424 #1e0838 #2a0c4a #3a1262 #4a1878 #5e2094 #7428b0 #8c38c8 #a448e0 #d06cff #f0c8ff"),
    "stellarite": R("#4a3008 #6a460c #8c6010 #b07c16 #d09c20 #ecbc2c #fad43e #ffe45c #fff08c #fffbd0"),   # glowing yellow (J00BA, no purple)
}
EXTRA = {
    "moss":    R("#1e3014 #2e481a #42621f #5c7e28 #7a9a34 #94b23e"),
    "lichen":  R("#5a4a1c #7a6424 #a0842e #c4a648 #dcc678 #ece0a8"),
    "snow":    R("#8ea4bc #a6bccf #bed0de #d2e0ea #e2ecf2 #eef4f8"),
    "slime":   R("#16260c #213a10 #2e5214 #3e6c18 #52881c #6aa424 #8cc23a"),
    "grass":   R("#1a3412 #264c18 #33661e #447f26 #5a9a30 #78b440"),
    "dry":     R("#4a3a1a #64502a #806838 #9c8248 #b89e5c #d0b874"),
    "ash":     R("#141214 #1e1a1c #2a2426 #383032 #4a4042"),
    "rust":    R("#26282c #303338 #3b3f45 #474b52 #53585f"),   # iron: dark steel-grey stains (was orange rust)
    "metal":   R("#2c323a #444c56 #606a76 #848e9a #b0b8c2 #dfe4ea"),
    "patina":  R("#163a34 #1f5246 #2c6c58 #3f8a6c #5ca684 #84c2a0"),
    "sheen":   R("#1c1c1e #242426 #2c2c2f"),       # coal: a very dark grey graphite sheen (J00BA, 2026-11-14; was blue)
    "glow_red":  R("#5a0c0c #8c1414 #c42a1a #f05a28 #ff9a4a #ffd08a"),
    "glow_star": R("#c8b080 #f0d890 #fff6c8 #fffbe8"),
    "nebula_void": R("#1c0a30 #2c1048 #3e1660 #561e7c #722a98 #8e3cb4"),
    "nebula_star": R("#6e5414 #8e6c18 #b48a20 #d8aa2c #f2c83c #ffe26a"),   # glowing golden swirls
}
GEMS = {  # dark -> light
    "diamond":   R("#4a6a7a #6e94a6 #96bccc #bcdce6 #def2f6 #f4fcfd"),
    "topaz":     R("#5a2c06 #8a4a0c #ba6e14 #e09a24 #f6c24a #fde08c"),
    "sapphire":  R("#0c1a40 #13296a #1c3c96 #2a58c0 #4682de #78b0f0 #b4d8fa"),
    "amethyst":  R("#24103e #3a1a62 #562a8a #7444b0 #9466d0 #b892ea"),
    "ruby":      R("#3a0610 #620a1a #8e1226 #ba1e36 #de3a50 #f47284"),
    "emerald":   R("#06301c #0c4e2c #12703e #1c9452 #38b86c #74dc98"),
    "jade":      R("#1e3e2a #2c5a3c #3e7a52 #569a6a #78b888 #a4d4ac"),
    "painite":   R("#3a0c06 #5e160a #84260e #a83c18 #c85a2c #e6844c"),
    "arcanium":  R("#3a0636 #5e0c58 #8a1680 #b428a8 #da52cc #f69aea"),
    "eclipsium": R("#0e0c08 #1e1a10 #3a2e14 #6e5418 #c49a2a #f8dc6a"),   # black with a gold rim
}

# size: target footprint (mound) and height. shape: ore piece style. paint: how the ore pieces are painted.
CFG = {
    "coal": dict(tier=1, seed=1101, stone="mid_grey", gem="diamond", s=0.86, hs=0.7, shape="lump", paint="matte",
                 n_ore=7, details=["soot"], top="moss", ground="grass", extras=[], tall=False, stone_v=4.8),
    "tin": dict(tier=2, seed=2202, stone="light_grey", gem="topaz", s=0.86, hs=0.78, shape="nugget", paint="dull",
                n_ore=6, details=["speckle"], top="moss", ground="grass", extras=[], tall=True, stone_v=4.4),
    "iron": dict(tier=4, seed=4404, stone="grey_brown", gem="amethyst", s=1.04, hs=0.92, shape="nugget", paint="rusty",
                 n_ore=7, details=["rust"], top="lichen", ground="pebbles", extras=[], tall=True, stone_v=5.0),
    "gold": dict(tier=5, seed=5505, stone="warm_grey", gem="ruby", s=1.04, hs=1.0, shape="nugget", paint="shiny",
                 n_ore=6, details=["flecks"], top="snow", ground="none", extras=["snow_drift"], tall=True, stone_v=5.0),
    "obsidian": dict(tier=6, seed=6606, stone="basalt", gem="emerald", s=1.1, hs=1.15, shape="shard", paint="glass",
                     n_ore=7, details=["joints"], top="ash", ground="pebbles", extras=[], tall=True, columns=True, stone_v=5.4),
    "titanite": dict(tier=7, seed=7707, stone="pale", gem="jade", s=1.18, hs=1.0, shape="crystal", paint="crystal",
                     n_ore=8, details=["veins"], top="none", ground="dry", extras=[], tall=False, stone_v=4.8, ore_h=1.4),
    "dreadstone": dict(tier=8, seed=8808, stone="swamp", gem="painite", s=1.18, hs=1.0, shape="spike", paint="spike",
                       n_ore=8, details=["wet"], top="slime", ground="slime_puddle", extras=["glow_cracks", "drips"],
                       tall=True, stone_v=5.6),
    "void": dict(tier=9, seed=9909, stone="void_black", gem="arcanium", s=1.24, hs=1.0, shape="crystal", paint="glow_crystal",
                 n_ore=7, details=["glints"], top="none", ground="none", extras=["float_stones"], tall=False,
                 stone_v=5.6, ore_h=1.25, rich=True),
    "stellarite": dict(tier=10, seed=10010, stone="star_dust", gem="eclipsium", s=1.32, hs=1.05, shape="crystal",
                       paint="glow_crystal", n_ore=8, details=["stars"], top="none", ground="none",
                       extras=["orbit", "sparkles"], tall=False, stone_v=5.6, ore_h=1.35, rich=True),
}
for k, c in CFG.items():
    c.setdefault("columns", False); c.setdefault("ore_h", 1.0)

FACES = ("north", "east", "south", "west", "up", "down")
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0), "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}
TANGENTS = {"north": ((1, 0, 0), (0, 1, 0)), "south": ((1, 0, 0), (0, 1, 0)), "east": ((0, 0, 1), (0, 1, 0)),
            "west": ((0, 0, 1), (0, 1, 0)), "up": ((1, 0, 0), (0, 0, 1)), "down": ((1, 0, 0), (0, 0, 1))}
FACE_LIGHT = {"up": 1.6, "north": 0.5, "west": 0.6, "south": -0.1, "east": -0.3, "down": -1.8}


def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


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
    u = (np.arange(w) + 0.5) / w; v = (np.arange(h) + 0.5) / h
    U, V = np.meshgrid(u, v)
    if face == "north": X, Y, Z = x1 - U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z0)
    elif face == "south": X, Y, Z = x0 + U * (x1 - x0), y1 - V * (y1 - y0), np.full_like(U, z1)
    elif face == "east": X, Y, Z = np.full_like(U, x1), y1 - V * (y1 - y0), z1 - U * (z1 - z0)
    elif face == "west": X, Y, Z = np.full_like(U, x0), y1 - V * (y1 - y0), z0 + U * (z1 - z0)
    elif face == "up": X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y1), z0 + V * (z1 - z0)
    else: X, Y, Z = x0 + U * (x1 - x0), np.full_like(U, y0), z1 - V * (z1 - z0)
    return X, Y, Z


def uvgrid(w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    edge = np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)
    return U, V, edge


def dither(v, w, h):
    bayer = np.array([[0, 2], [3, 1]]) / 4.0 - 0.375
    return v + np.tile(bayer, (h // 2 + 1, w // 2 + 1))[:h, :w] * 0.5


def build(ore):
    C = CFG[ore]
    NAME = f"{ore}_vein"
    rng = random.Random(C["seed"])
    nrng = np.random.default_rng(C["seed"])
    RAMPS = {"stone": STONES[C["stone"]], "ore": ORE[ore], "gem": GEMS[C["gem"]], **EXTRA}
    RAMPS["nebula"] = EXTRA["nebula_star" if ore == "stellarite" else "nebula_void"]
    RAMPS = {k: [hexc(c) for c in v] for k, v in RAMPS.items()}

    def ramp_colour(name, v):
        r = RAMPS[name]; n = len(r)
        q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
        lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
        a = np.array(r)[lo]; b = np.array(r)[hi]
        return (a * (1 - f) + b * f).round().astype(np.uint8)

    # ---- 3D value noise, seeded per ore
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

    # ---- scaffolding
    elements, groups = [], {}

    def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

    def group(name, parent=None, origin=(0, 0, 0)):
        groups[name] = {"name": name, "uuid": new_uuid(), "origin": list(origin), "children": []}
        if parent: groups[parent]["children"].append(("g", name))
        return name

    def cube(name, grp, frm, to, rotation=(0, 0, 0), origin=None, kind="stone", hidden=("down",), data=None):
        origin = origin or [(frm[i] + to[i]) / 2 for i in range(3)]
        e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
             "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
             "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": {}, "type": "cube",
             "uuid": new_uuid(), "_kind": kind, "_hidden": set(hidden), "_data": data or {}}
        if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(v, 3) for v in rotation]
        elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
        return e

    def box(cx, cz, y0, w, d, h):
        w, d, h = max(0.5, h2(w)), max(0.5, h2(d)), max(0.5, h2(h))
        x0, z0 = h2(cx - w / 2), h2(cz - d / 2)
        return [x0, y0, z0], [x0 + w, h2(y0 + h), z0 + d]

    root = group(NAME)
    g_base = group("base", root); g_stone = group("stone", root); g_ore = group("ore", root)
    g_frag = group("fragments", root); g_det = group("details", root)
    s, hs = C["s"], C["hs"]

    # ---- base and stone mound (rings that get smaller and higher, jittered; basalt = narrow tall columns)
    cube("base_1", g_base, [h2(-9.5 * s), -1, h2(-7.5 * s)], [h2(8.5 * s), 1.5, h2(7.0 * s)])
    cube("base_2", g_base, [h2(-6.0 * s), -1, h2(-9.0 * s)], [h2(6.5 * s), 1.0, h2(9.5 * s)])
    stones = []
    cols = C["columns"]
    rings = [(10, 7.6, 6.6, (0.0, 0.5), (4.5, 7.0), (4.0, 6.5)),
             (8, 4.8, 4.2, (3.5, 5.0), (4.5, 6.5), (4.0, 6.0)),
             (5, 2.4, 2.2, (7.5, 9.0), (4.0, 5.5), (3.5, 5.0)),
             (2, 0.9, 0.9, (11.0, 12.0), (3.5, 4.5), (3.0, 4.0))]
    for ri, (n, rx, rz, yr, sr, hr) in enumerate(rings):
        a0 = rng.uniform(0, math.tau)
        for i in range(n):
            a = a0 + i * math.tau / n + rng.uniform(-0.25, 0.25)
            cx, cz = (rx * math.cos(a) + rng.uniform(-0.6, 0.6)) * s, (rz * math.sin(a) + rng.uniform(-0.6, 0.6)) * s
            sw, sd = rng.uniform(*sr) * s, rng.uniform(*sr) * s
            sh = rng.uniform(*hr) * hs
            y0 = h2(rng.uniform(*yr) * hs)
            if cols:                                     # basalt: narrower, taller, flat topped columns
                sw, sd, sh = sw * 0.72, sd * 0.72, sh * rng.uniform(1.15, 1.6)
                y0 = h2(y0 * 0.85)
            frm, to = box(cx, cz, y0, sw, sd, sh)
            stones.append((f"stone_{len(stones) + 1}", frm, to))
    # silhouette breaker: a tall stone at a random side (or a low long ledge for the low veins)
    a = rng.uniform(0, math.tau)
    if C["tall"]:
        cx, cz = 3.0 * s * math.cos(a), 2.6 * s * math.sin(a)
        frm, to = box(cx, cz, h2(6.0 * hs), 4.0 * s, 4.0 * s, 11.0 * hs * (1.15 if cols else 1.0))
    else:
        cx, cz = 7.0 * s * math.cos(a), 6.0 * s * math.sin(a)
        frm, to = box(cx, cz, 0.0, 6.5 * s, 4.5 * s, 4.5 * hs)
    stones.append((f"stone_{len(stones) + 1}", frm, to))
    for k in range(3):                                   # cubes sticking out of the sides
        a = rng.uniform(0, math.tau)
        cx, cz = 9.0 * s * math.cos(a), 8.0 * s * math.sin(a)
        frm, to = box(cx, cz, 0.0, rng.uniform(3, 4) * s, rng.uniform(3, 4) * s, rng.uniform(2.5, 3.5) * hs)
        stones.append((f"stone_{len(stones) + 1}", frm, to))
    for name, frm, to in stones:
        cube(name, g_stone, frm, to)
    SOLIDS = [(e["from"], e["to"]) for e in elements]

    def inside(X, Y, Z, skip=None):
        m = np.zeros(np.shape(X), bool)
        for k, (f, t) in enumerate(SOLIDS):
            if k == skip: continue
            m |= (X > f[0]) & (X < t[0]) & (Y > f[1]) & (Y < t[1]) & (Z > f[2]) & (Z < t[2])
        return m

    def top_at(x, z):
        best = 0.0
        for f, t in SOLIDS:
            if f[0] <= x <= t[0] and f[2] <= z <= t[2]: best = max(best, t[1])
        return best

    mound_top = max(t[1] for f, t in SOLIDS)

    # ---- ore pieces
    shape, n_ore, oh = C["shape"], C["n_ore"], C["ore_h"]
    glow = C["paint"] == "glow_crystal"
    for i in range(n_ore):
        big = i < max(2, n_ore // 3)                       # the first few are the big ones near the top
        ang = rng.uniform(0, math.tau)
        dist = (rng.uniform(0.0, 2.5) if big else rng.uniform(3.5, 7.0)) * s
        cx, cz = dist * math.cos(ang), dist * 0.85 * math.sin(ang)
        base_y = top_at(cx, cz)
        lean = rng.uniform(10, 22) if big else rng.uniform(22, 40)     # side pieces lean outward more
        rxl, rzl = lean * math.sin(ang), -lean * math.cos(ang)
        if dist < 0.8: rxl, rzl = rng.uniform(-15, 15), rng.uniform(-15, 15)
        nm = f"{ore}_{'crystal' if shape == 'crystal' else shape}_{i + 1}"
        sfx = "_glow" if glow else ""
        kind = f"ore_{i}"
        if shape in ("nugget", "lump"):
            w = (rng.uniform(3.8, 5.0) if big else rng.uniform(2.5, 3.6)) * (1.15 if shape == "lump" else 1.0)
            h = (rng.uniform(4.0, 5.0) if big else rng.uniform(2.8, 3.8)) * (0.7 if shape == "lump" else 1.0)
            d = w * rng.uniform(0.8, 1.0)
            if shape == "lump": rxl, rzl = rxl * 0.5, rzl * 0.5
            sink = h * 0.55
            frm, to = box(cx, cz, h2(base_y - sink), w, d, h)
            org = [h2(cx), h2(base_y - sink), h2(cz)]
            yaw = rng.uniform(-35, 35)
            cube(nm, g_ore, frm, to, rotation=(rxl, yaw, rzl), origin=org, kind=kind)
            if big or rng.random() < 0.4:
                f2, t2 = box(cx + w * 0.15, cz - d * 0.1, to[1] - 1.0, w * 0.6, d * 0.65, 2.0 if shape == "lump" else 2.5)
                cube(nm + "_top", g_ore, f2, t2, rotation=(rxl, yaw, rzl), origin=org, kind=kind + "t")
        elif shape == "crystal":                            # tall column + a narrower pointed tip
            w = rng.uniform(2.0, 3.0) if big else rng.uniform(1.5, 2.0)
            h = (rng.uniform(7.0, 9.0) if big else rng.uniform(4.0, 6.0)) * oh
            sink = 2.0
            org = [h2(cx), h2(base_y - sink), h2(cz)]
            frm, to = box(cx, cz, org[1], w, w, h)
            yaw = rng.choice([0, 22.5, 45])
            cube(nm + sfx, g_ore, frm, to, rotation=(rxl, yaw, rzl), origin=org, kind=kind)
            f2, t2 = box(cx, cz, to[1], w * 0.55, w * 0.55, max(1.0, h * 0.18))
            cube(nm + "_tip" + sfx, g_ore, f2, t2, rotation=(rxl, yaw, rzl), origin=org, kind=kind + "t")
        elif shape == "shard":                              # thin glassy slab + a narrower top step
            w = rng.uniform(3.0, 4.0) if big else rng.uniform(2.0, 3.0)
            h = rng.uniform(6.0, 8.0) if big else rng.uniform(3.5, 5.0)
            d = rng.choice([1.0, 1.5])
            sink = 1.5
            org = [h2(cx), h2(base_y - sink), h2(cz)]
            frm, to = box(cx, cz, org[1], w, d, h)
            yaw = math.degrees(-ang) + rng.uniform(-20, 20)  # broad side faces outward
            cube(nm, g_ore, frm, to, rotation=(rxl, yaw, rzl), origin=org, kind=kind)
            f2, t2 = box(cx - w * 0.15, cz, to[1], w * 0.5, d * 0.5 if d > 1 else 0.5, h * 0.25)
            cube(nm + "_tip", g_ore, f2, t2, rotation=(rxl, yaw, rzl), origin=org, kind=kind + "t")
        elif shape == "spike":                              # jagged: three stacked tapering cubes
            w = rng.uniform(2.5, 3.2) if big else rng.uniform(1.8, 2.4)
            h = rng.uniform(7.5, 9.5) if big else rng.uniform(4.5, 6.0)
            sink = 2.0
            org = [h2(cx), h2(base_y - sink), h2(cz)]
            yaw = rng.uniform(-30, 30)
            y = org[1]
            for k, (fw, fh) in enumerate([(1.0, 0.45), (0.66, 0.33), (0.36, 0.25)]):
                off = (0.5 if k == 1 else -0.5 if k == 2 else 0) * (1 if i % 2 else -1)
                f_, t_ = box(cx + off, cz, h2(y), w * fw, w * fw, h * fh)
                cube(nm + ("" if k == 0 else f"_{['', 'mid', 'tip'][k]}"), g_ore, f_, t_, rotation=(rxl, yaw, rzl),
                     origin=org, kind=kind + "s" * k)
                y = t_[1]

    # gem accent: one small rotated crystal on a random side
    ga = rng.uniform(0, math.tau)
    gx, gz = 6.5 * s * math.cos(ga), 5.5 * s * math.sin(ga)
    gy = top_at(gx - 0.5 * math.cos(ga), gz - 0.5 * math.sin(ga)) - 1.5
    cube(f"{C['gem']}_gem", g_ore, [h2(gx) - 0.5, h2(gy), h2(gz) - 0.5], [h2(gx) + 1.0, h2(gy) + 2.5, h2(gz) + 1.0],
         rotation=(rng.uniform(-25, 25), 30, rng.uniform(-25, 25)), origin=[h2(gx), h2(gy), h2(gz)], kind="gem")

    # loose fragments on the ground (stone, and ore of the vein's shape)
    for k in range(7):
        a = rng.uniform(0, math.tau); r = rng.uniform(9.5, 11.0) * s
        x, z = r * math.cos(a), r * 0.9 * math.sin(a)
        is_ore = k >= 4
        w = rng.choice([1.0, 1.5]) if is_ore else rng.choice([1.5, 2.0])
        hgt = (rng.choice([1.5, 2.0]) if shape in ("crystal", "shard", "spike") else 1.0) if is_ore else rng.choice([1.0, 1.5])
        frm, to = box(x, z, 0.0, w, w, hgt)
        rot = (0, rng.uniform(-60, 60), rng.uniform(-25, 25) if is_ore and shape != "nugget" else 0)
        nm = f"{ore}_fragment_{k - 3}" if is_ore else f"stone_fragment_{k + 1}"
        cube(nm + ("_glow" if is_ore and glow else ""), g_frag, frm, to, rotation=rot, origin=[h2(x), 0, h2(z)],
             kind="frag_ore" if is_ore else "frag_stone")

    # ---- biome details and extras
    tops = sorted(stones, key=lambda st: -st[2][1])
    if C["top"] in ("moss", "snow", "slime"):               # cushions on two of the highest stones
        for k, (name, frm, to) in enumerate([tops[1], tops[3]]):
            w, d = to[0] - frm[0], to[2] - frm[2]
            f = [h2(frm[0] + w * 0.15), to[1], h2(frm[2] + d * 0.2)]
            t = [h2(f[0] + max(1.5, w * (0.8 if C["top"] == "snow" else 0.55))), to[1] + (1.0 if C["top"] == "snow" else 0.5),
                 h2(f[2] + max(1.5, d * (0.7 if C["top"] == "snow" else 0.5)))]
            cube(f"{C['top']}_{'cap' if C['top'] == 'snow' else 'cushion'}_{k + 1}", g_det, f, t, kind=C["top"])
    if C["ground"] in ("grass", "dry"):
        for k in range(3 if C["ground"] == "grass" else 4):
            a = rng.uniform(0, math.tau); r = rng.uniform(8.0, 9.5) * s
            x, z = h2(r * math.cos(a)), h2(r * 0.9 * math.sin(a))
            hgt = 3.0 if C["ground"] == "grass" else 4.0
            for j, yaw in enumerate((45, -45)):
                cube(f"{C['ground']}_grass_tuft_{k + 1}_{j + 1}", g_det, [x - 2.0, 0, z], [x + 2.0, hgt, z], rotation=(0, yaw, 0),
                     origin=[x, 0, z], kind=C["ground"] + "_card", hidden=("down", "up", "east", "west"))
    if C["ground"] == "pebbles":
        for k in range(5):
            a = rng.uniform(0, math.tau); r = rng.uniform(10.0, 12.0) * s
            x, z = r * math.cos(a), r * 0.9 * math.sin(a)
            frm, to = box(x, z, 0.0, 1.0, 1.0, 0.5)
            cube(f"pebble_{k + 1}", g_det, frm, to, rotation=(0, rng.uniform(0, 90), 0), origin=[h2(x), 0, h2(z)], kind="frag_stone")
    if C["ground"] == "slime_puddle":
        for k, (a, w, d) in enumerate([(rng.uniform(0, 3), 6.0, 3.5), (rng.uniform(3, 6), 4.0, 3.0)]):
            r = 9.5 * s; x, z = r * math.cos(a), r * 0.9 * math.sin(a)
            frm, to = box(x, z, 0.0, w, d, 0.5)
            cube(f"slime_puddle_{k + 1}", g_det, frm, to, rotation=(0, rng.uniform(-30, 30), 0), origin=[h2(x), 0, h2(z)], kind="slime")
    if "snow_drift" in C["extras"]:                         # drift on the north side
        for k, (x, w, h) in enumerate([(-4.0, 7.0, 2.0), (2.5, 6.0, 1.5), (-0.5, 4.0, 3.0)]):
            zf = -top_at(x * s, 0) * 0 - 8.0 * s
            frm, to = box(x * s, zf - (0.5 if k == 2 else 0), 0.0, w * s, 3.5 if k < 2 else 2.5, h)
            cube(f"snow_drift_{k + 1}", g_det, frm, to, kind="snow")
    if "drips" in C["extras"]:                              # slime dripping from stone edges
        cand = [st for st in stones if st[2][1] > 4]
        for k in range(5):
            name, frm, to = cand[rng.randrange(len(cand))]
            side = rng.choice(["n", "s", "e", "w"])
            x = rng.uniform(frm[0] + 0.5, to[0] - 1.0); z = rng.uniform(frm[2] + 0.5, to[2] - 1.0)
            if side == "n": z = frm[2] - 0.5
            if side == "s": z = to[2]
            if side == "e": x = to[0]
            if side == "w": x = frm[0] - 0.5
            L = rng.choice([1.5, 2.0, 2.5])
            f_ = [h2(x), h2(to[1] - L), h2(z)]
            cube(f"slime_drip_{k + 1}", g_det, f_, [f_[0] + 0.5, h2(to[1]) + 0.5, f_[2] + 0.5], kind="slime")
    if "glow_cracks" in C["extras"]:                        # red glowing fissure panels just off side faces
        cand = [st for st in stones if (st[2][0] - st[1][0]) >= 3.5 and (st[2][1] - st[1][1]) >= 3.5]
        rng.shuffle(cand)
        for k, (name, frm, to) in enumerate(cand[:6]):
            face = rng.choice(["north", "south", "east", "west"])
            if face in ("north", "south"):
                z = frm[2] - 0.05 if face == "north" else to[2] + 0.05
                f_, t_ = [frm[0], frm[1], z], [to[0], to[1], z]
                hid = ("down", "up", "east", "west")
            else:
                x = frm[0] - 0.05 if face == "west" else to[0] + 0.05
                f_, t_ = [x, frm[1], frm[2]], [x, to[1], to[2]]
                hid = ("down", "up", "north", "south")
            cube(f"fissure_{k + 1}_glow", g_det, f_, t_, kind="crack", hidden=hid, data={"seed": k})
    if "float_stones" in C["extras"]:                       # stone pieces floating above the node
        for k in range(4):
            a = rng.uniform(0, math.tau); r = rng.uniform(1.5, 6.0) * s
            x, z = r * math.cos(a), r * math.sin(a)
            y = h2(top_at(x, z) + rng.uniform(2.5, 5.0))
            w = rng.choice([2.0, 2.5, 3.0])
            frm, to = box(x, z, y, w, w * 0.9, w * 0.7)
            cube(f"floating_stone_{k + 1}", g_det, frm, to, rotation=(rng.uniform(-20, 20), rng.uniform(0, 90), rng.uniform(-20, 20)),
                 hidden=(), kind="frag_stone")
            if k < 2:
                f2, t2 = box(x, z, to[1] - 0.5, 1.0, 1.0, 2.0)
                cube(f"floating_crystal_{k + 1}_glow", g_det, f2, t2, rotation=(rng.uniform(-20, 20), 45, rng.uniform(-20, 20)),
                     origin=[h2(x), to[1] - 0.5, h2(z)], kind="frag_ore")
    if "orbit" in C["extras"]:                              # small fragments floating in a ring round the vein
        n = 7; a0 = rng.uniform(0, math.tau)
        for k in range(n):
            a = a0 + k * math.tau / n
            r = 12.0 * s; x, z = r * math.cos(a), r * 0.9 * math.sin(a)
            y = h2(8.0 * hs + 3.0 * math.sin(a * 2))
            w = rng.choice([1.0, 1.5])
            frm, to = box(x, z, y, w, w, w)
            ore_piece = k % 2 == 0
            cube(f"orbit_fragment_{k + 1}" + ("_glow" if ore_piece else ""), g_det, frm, to,
                 rotation=(rng.uniform(-35, 35), rng.uniform(0, 90), rng.uniform(-35, 35)), hidden=(),
                 kind="frag_ore" if ore_piece else "frag_stone")
    if "sparkles" in C["extras"]:                           # star sparkle crosses (two crossed cards)
        for k in range(5):
            a = rng.uniform(0, math.tau); r = rng.uniform(2.0, 9.0) * s
            x, z = h2(r * math.cos(a)), h2(r * math.sin(a))
            y = h2(top_at(x, z) + rng.uniform(1.0, 4.0))
            for j, yaw in enumerate((0, 90)):
                cube(f"star_sparkle_{k + 1}_{j + 1}_glow", g_det, [x - 1.0, y, z], [x + 1.0, y + 2.0, z], rotation=(0, yaw, 0),
                     origin=[x, y, z], kind="sparkle", hidden=("down", "up", "east", "west"))

    # ---- painters
    def vein_lines(X, Y, Z, sc=1.0):
        def crossings(f):
            s_ = f > 0
            m = np.zeros(f.shape, bool)
            m[:, :-1] |= s_[:, :-1] != s_[:, 1:]
            m[:-1, :] |= s_[:-1, :] != s_[1:, :]
            return m
        a = fbm(X * 0.13 * sc + 3.1, Y * 0.17 * sc + 1.7, Z * 0.13 * sc + 5.3) - 0.5
        b = fbm(X * 0.27 * sc + 11.0, Y * 0.27 * sc + 7.0, Z * 0.27 * sc + 2.0) - 0.5
        patch = fbm(X * 0.1 + 40.0, Y * 0.1, Z * 0.1 + 17.0) > 0.52
        line = crossings(a) | (crossings(b) & patch)
        bed = np.zeros(line.shape, bool)
        bed[:, 1:] |= line[:, :-1]; bed[1:, :] |= line[:-1, :]
        return line, bed & ~line

    def visible(X, Y, Z, face, skip):
        n = np.array(NORMAL[face], float); t1, t2 = (np.array(t, float) for t in TANGENTS[face])
        dirs = [n] + [n + sg * t for t in (t1, t2) for sg in (1.2, -1.2)]
        out = np.zeros(np.shape(X), bool)
        for d in dirs:
            d = d / np.linalg.norm(d)
            free = np.ones(np.shape(X), bool)
            for step in np.arange(0.3, 12.0, 0.5):
                free &= ~inside(X + d[0] * step, Y + d[1] * step, Z + d[2] * step, skip=skip) & (Y + d[1] * step > -0.2)
            out |= free
        return out

    sv = C["stone_v"]
    det = C["details"]

    def paint_stone(e, face, w, h):
        frm, to = e["from"], e["to"]
        X, Y, Z = face_points(frm, to, face, w, h)
        nx, ny, nz = NORMAL[face]
        k = SOLIDS.index((frm, to)) if (frm, to) in SOLIDS else None
        covered = inside(X + nx * 0.2, Y + ny * 0.2, Z + nz * 0.2, skip=k) | ((Y < 0.05) & (face != "up"))
        if covered.all() or not (visible(X, Y, Z, face, k) & ~covered).any():
            return None
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), sv + FACE_LIGHT[face] * 1.3) + np.clip(Y / (17.0 * hs), 0, 1) * 1.2
        v -= np.clip(1.0 - edge / 3.0, 0, 1) * 1.4
        if face not in ("up", "down"):
            v -= V * 0.9
            v += np.clip(1.0 - V * h / 2.0, 0, 1) * 0.6
        near1 = inside(X + nx * 0.9, Y + ny * 0.9, Z + nz * 0.9, skip=k)
        near2 = inside(X + nx * 1.8, Y + ny * 1.8, Z + nz * 1.8, skip=k)
        v -= near1 * 1.6 + near2 * 0.8
        v -= np.clip(1.0 - Y / 2.0, 0, 1) * 1.2 * (face != "up")
        v += (fbm(X * 0.35, Y * 0.35, Z * 0.35) - 0.5) * 2.4
        if "joints" in det and face != "up":                # basalt: horizontal joints every few units
            v -= ((np.floor(Y * 2) % 7) == 0) * 1.2
        if "soot" in det:                                   # sooty streaks running down
            soot = fbm(X * 0.7 + 3, Y * 0.06, Z * 0.7 + 8) > 0.56
            v -= soot * 1.4 * (face != "up")
        if "wet" in det:                                    # wet: glossy upper edges, darker soaked base
            v -= np.clip(1.0 - Y / 4.0, 0, 1) * 1.0
        v = dither(v, w, h)
        rgb = ramp_colour("stone", v)
        # cracks
        for _ in range(max(0, (w * h) // 90)):
            x, y = int(nrng.integers(1, max(2, w - 1))), int(nrng.integers(1, max(2, h - 1)))
            for _s in range(int(nrng.integers(3, 7))):
                if 0 <= x < w and 0 <= y < h and not covered[y, x]:
                    rgb[y, x] = ramp_colour("stone", v[y, x] - 2.0)
                    if x + 1 < w: rgb[y, x + 1] = ramp_colour("stone", v[y, x + 1] + 1.0)
                x += int(nrng.choice([-1, 0, 1])); y += int(nrng.choice([0, 1, 1]))
        # ore veins (world space, wrap over edges)
        core, rim = vein_lines(X, Y, Z, 1.25 if "veins" in det else 1.0)
        n_ore = len(RAMPS["ore"]); top_ore = n_ore - 1
        cv = n_ore * 0.5 + FACE_LIGHT[face] * 0.8 + (fbm(X * 0.5, Y * 0.5, Z * 0.5) - 0.5) * 2.0 - near1 * 1.5
        if C["paint"] in ("glow_crystal",): cv = cv + 1.5
        rgb[rim] = ramp_colour("stone", v - 1.0)[rim]
        rgb[core] = ramp_colour("ore", cv)[core]
        if "rust" in det and face != "up":                  # rust stains running down from the veins
            stain = np.zeros((h, w), bool); fade = np.zeros((h, w))
            for dy in np.arange(0.5, 2.6, 0.5):
                l, _ = vein_lines(X, Y + dy, Z)
                new = l & ~stain
                fade[new] = dy; stain |= l
            stain &= ~core & (fbm(X * 0.9, 0, Z * 0.9 + 4) > 0.6)
            rv = 3.4 - fade * 0.7 + FACE_LIGHT[face] * 0.4
            rgb[stain] = ramp_colour("rust", rv)[stain]
        if "speckle" in det:                                # pale speckles: soft 2 to 3 px clusters
            sp = (fbm(X * 1.6 + 9, Y * 1.6, Z * 1.6 + 2) > 0.66) & ~core
            rgb[sp] = ramp_colour("stone", v + 2.0)[sp]
        if "flecks" in det:                                 # gold flecks glittering in the stone
            fl = (fbm(X * 2.2 + 1, Y * 2.2 + 5, Z * 2.2) > 0.7) & ~core
            rgb[fl] = ramp_colour("ore", np.full((h, w), 6.5 + FACE_LIGHT[face] * 0.6))[fl]
        if "glints" in det:                                 # tiny purple glints
            fl = (fbm(X * 2.0 + 1, Y * 2.0 + 5, Z * 2.0) > 0.72) & ~core
            rgb[fl] = ramp_colour("ore", np.full((h, w), 7.0))[fl]
        if C.get("rich"):
            # polished stone: a soft baked reflection, then colour swirls (void: violet bloom, stellar: nebula)
            gloss = OM.tone(None, face, w, h, "metal", dome=.5, seed=3) - 0.5
            lift = np.where(covered, 0, gloss * 3.0)
            plain = (rgb == ramp_colour("stone", v)).all(-1)   # only plain stone texels, not cracks or veins
            rgb2 = ramp_colour("stone", dither(v + lift, w, h))
            rgb[plain] = rgb2[plain]
            neb = fbm(X * 0.18 + 5, Y * 0.18 + 2, Z * 0.18 + 9)
            nm = (neb > (0.6 if ore == "stellarite" else 0.56)) & ~core & plain
            rgb[nm] = ramp_colour("nebula", np.clip((neb - 0.56) * 22 + FACE_LIGHT[face] + lift * 0.3, 0, 5))[nm]
            if ore == "void":                                 # glowing crystal grit in the stone
                grit = (fbm(X * 3.0, Y * 3.0, Z * 3.0) > 0.7) & ~core
                rgb[grit] = ramp_colour("ore", np.full((h, w), top_ore - 1.0))[grit]
            if ore == "stellarite":                           # constellations: bright stars joined by faint lines
                for _ in range(max(1, w * h // 160)):
                    x0_, y0_ = int(nrng.integers(1, max(2, w - 1))), int(nrng.integers(1, max(2, h - 1)))
                    x1_ = int(np.clip(x0_ + nrng.integers(-6, 7), 0, w - 1)); y1_ = int(np.clip(y0_ + nrng.integers(-6, 7), 0, h - 1))
                    steps = max(abs(x1_ - x0_), abs(y1_ - y0_), 1)
                    for k_ in range(steps + 1):
                        xx = int(round(x0_ + (x1_ - x0_) * k_ / steps)); yy = int(round(y0_ + (y1_ - y0_) * k_ / steps))
                        if k_ % 2 == 0 and not covered[yy, xx]: rgb[yy, xx] = RAMPS["nebula"][4]
                    for (xx, yy) in ((x0_, y0_), (x1_, y1_)):
                        if not covered[yy, xx]: rgb[yy, xx] = RAMPS["glow_star"][-1]
            hl = np.zeros((h, w), bool); hl[:-1, :] = core[1:, :] & ~core[:-1, :]   # veins shine along their top
            hl &= ~covered
            rgb[hl] = ramp_colour("ore", np.full((h, w), top_ore))[hl]
        if "stars" in det:                                  # star dust: bright points, a few with a cross
            st = (fbm(X * 2.4 + 3, Y * 2.4 + 1, Z * 2.4 + 7) > 0.73) & ~core
            rgb[st] = ramp_colour("glow_star", 1.5 + nrng.random((h, w)) * 1.5)[st]
        if "wet" in det and face != "down":                 # wet sheen on the top rows
            sheen = (np.clip(1.0 - V * h / 2.5, 0, 1) > 0.5) & (fbm(X * 0.8, Y * 0.8, Z * 0.8) > 0.5) & (face != "up")
            rgb[sheen] = ramp_colour("stone", v + 2.5)[sheen]
        # top cover (moss / lichen / snow / slime / ash), spilling over the edge
        top = C["top"]
        if top != "none" and Y.max() > 4.0 * hs:
            mf = fbm(X * 0.22 + 20.0, 0.0, Z * 0.22 + 9.0)
            top_y = to[1]
            up_open = not inside(np.array([(frm[0] + to[0]) / 2]), np.array([top_y + 0.3]), np.array([(frm[2] + to[2]) / 2]), skip=k)[0]
            thr = {"moss": 0.5, "lichen": 0.6, "snow": 0.36, "slime": 0.58, "ash": 0.5}[top]
            spill = {"moss": 1.0, "lichen": 0.5, "snow": 1.5, "slime": 1.0, "ash": 0.5}[top]
            ramp = {"moss": "moss", "lichen": "lichen", "snow": "snow", "slime": "slime", "ash": "ash"}[top]
            if face == "up":
                mm = (mf > thr) & ~covered
                if top == "lichen": mm &= fbm(X * 1.2, 0, Z * 1.2) > 0.5   # lichen: spots, not a carpet
            else:
                mm = (mf > thr + 0.02) & (Y > top_y - spill + (mf - thr) * 3.0) & ~covered & up_open
            if top == "slime" and face != "up":              # slime runs a little further down in streaks
                mm |= (mf > thr + 0.04) & (Y > top_y - spill - 2.0 * (fbm(X * 1.5, 0, Z * 1.5) > 0.66)) & ~covered & up_open
            nmax = len(RAMPS[ramp]) - 1
            mv = nmax * 0.6 + (mf - thr) * 6 + FACE_LIGHT[face] * 0.6
            rgb[mm] = ramp_colour(ramp, mv)[mm]
        return rgb, np.ones((h, w), bool)

    def paint_ore(e, face, w, h, seed, frag=False):
        """Ore pieces get a polished metal or cut-gem finish (ore_metal.tone: a baked reflection that follows
        the piece's own tilt), then the ore's own detail on top."""
        r = np.random.default_rng(seed)
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS["ore"]); top = n - 1
        p = C["paint"]
        rot_ = e.get("rotation")
        rich = C.get("rich", False)
        side = face not in ("up", "down")
        if p in ("crystal", "glow_crystal", "spike", "glass"):
            kind = "glass" if p == "glass" else "gem"
            t = OM.tone(rot_, face, w, h, kind, dome=.45, facet=(.3 if frag else .6), seed=seed, cell=3.5)
            v = t * top if ore != "stellarite" else 3.0 + t * (top - 3.0)   # stellarite stays a bright glowing yellow
            v -= V * (0.5 if frag else 1.1) * side            # darker toward the root
            if p == "spike": v = v * 0.8 - V * 0.6 * side
            if p == "glow_crystal":                           # a glowing core inside the crystal
                v += 1.4 * np.clip(1.0 - np.abs(U - 0.5) * 2.4, 0, 1) * (1 - V * 0.6) * side
            if rich and side:                                 # growth bands across the crystal
                v -= ((np.floor(V * h + U * 1.5) % 5) == 0) * 0.9
            rgb = ramp_colour("ore", dither(v, w, h))
            if p == "glass" and side:                         # glass: bright cut edges
                rgb[0, :] = ramp_colour("ore", top - 0.5 if face in ("west", "north") else top - 2.0)
                rgb[:, 0] = ramp_colour("ore", top - 1.5)
            if rich:                                          # inner glints / starry flecks
                fl = r.random((h, w)) < 0.06
                rgb[fl] = ramp_colour("ore", np.clip(v + 3.0, 0, top))[fl]
                if ore == "stellarite":
                    for _ in range(max(1, w * h // 28)):
                        x, y = int(r.integers(1, max(2, w - 1))), int(r.integers(1, max(2, h - 1)))
                        rgb[y, x] = RAMPS["glow_star"][-1]
                        for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                            if 0 <= x + dx < w and 0 <= y + dy < h: rgb[y + dy, x + dx] = RAMPS["glow_star"][1]
            if face in ("up", "west", "north") and w >= 2:    # the tip catches a hard highlight
                rgb[0:1, max(0, w // 2 - 1):w // 2 + 1] = RAMPS["ore"][-1]
            return rgb, np.ones((h, w), bool)
        # metal pieces: polished reflection, darker where they sink into the stone, soft lumps
        contrast = {"shiny": 1.0, "dull": 0.82, "rusty": 0.85, "matte": 0.6}.get(p, 0.9)
        t = OM.tone(rot_, face, w, h, "metal", dome=.62, seed=seed)
        v = top * 0.5 + (t - 0.5) * top * contrast * 1.25
        if p == "matte": v += 0.6
        v -= V * 1.2 * side
        for _ in range(2):
            cx, cy, rr = r.uniform(0.2, 0.8), r.uniform(0.2, 0.8), r.uniform(0.15, 0.3)
            v += np.clip(1.0 - np.hypot(U - cx, V - cy) / rr, 0, 1) * r.choice([-0.6, 0.5])
        rgb = ramp_colour("ore", dither(v, w, h))
        if p == "rusty":                                      # bright polished steel patches on the silver chunks
            mp = np.hypot(U - r.uniform(0.3, 0.7), V - r.uniform(0.2, 0.5)) < 0.3
            mt = t * 5.0
            rgb[mp] = ramp_colour("metal", dither(mt, w, h))[mp]
        if p == "matte":                                      # coal: a very dark grey graphite sheen where it is lit
            sh = (t > 0.62) & (r.random((h, w)) < 0.5)
            rgb[sh] = ramp_colour("sheen", np.clip((t - 0.62) * 8, 0, 2))[sh]
        if p in ("shiny", "dull", "rusty") and face in ("up", "west", "north"):
            hot = t > 0.9                                     # the hot spot goes nearly white
            rgb[hot] = RAMPS["ore"][-1]
        return rgb, np.ones((h, w), bool)

    def paint_gem(face, w, h):
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), 2.8 + FACE_LIGHT[face]) + np.where(U + V < 1.0, 1.0, -0.6) - V * 0.8
        rgb = ramp_colour("gem", v)
        if face in ("up", "west", "north") and w >= 2 and h >= 2:
            rgb[0, 0] = RAMPS["gem"][-1]; rgb[min(1, h - 1), min(1, w - 1)] = RAMPS["gem"][-2]
        return rgb, np.ones((h, w), bool)

    def paint_frag_stone(face, w, h):
        U, V, edge = uvgrid(w, h)
        v = np.full((h, w), sv + 0.4 + FACE_LIGHT[face]) - (V * 1.2 if face not in ("up", "down") else 0)
        v -= np.clip(1.0 - edge / 2, 0, 1) * 0.8
        return ramp_colour("stone", dither(v, w, h)), np.ones((h, w), bool)

    def paint_cover(ramp, face, w, h):
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS[ramp])
        v = np.full((h, w), n * 0.55 + FACE_LIGHT[face] * 0.8) - (V * 0.8 if face not in ("up", "down") else 0)
        v += np.clip(1.0 - np.hypot(U - 0.45, V - 0.4) * 2.2, 0, 1) * 1.0
        v -= np.clip(1.0 - edge / 2, 0, 1) * 0.6
        return ramp_colour(ramp, dither(v, w, h)), np.ones((h, w), bool)

    def paint_blades(ramp, face, w, h, seed):
        r = np.random.default_rng(seed)
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        for k in range(4):
            x = (k + r.uniform(0.2, 0.8)) * w / 4; top = int(r.integers(0, h // 2)); lean = r.uniform(-0.25, 0.25)
            for y in range(h - 1, top - 1, -1):
                xi = int(round(x + lean * (h - 1 - y)))
                if 0 <= xi < w:
                    t = (h - 1 - y) / max(1, h - 1 - top)
                    rgb[y, xi] = ramp_colour(ramp, 1.0 + t * 4.0 + (0.5 if face == "north" else 0)); a[y, xi] = True
        return rgb, a

    def paint_crack(face, w, h, seed):
        """Glowing fissures: a jagged crack line from the top edge down, bright core, red halo."""
        r = np.random.default_rng(seed + 77)
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        x = int(r.integers(w // 4, max(w // 4 + 1, 3 * w // 4)))
        for y in range(0, int(h * r.uniform(0.6, 0.95))):
            x = int(np.clip(x + r.choice([-1, 0, 0, 1]), 1, w - 2))
            rgb[y, x] = ramp_colour("glow_red", 4.5 + r.random()); a[y, x] = True
            if r.random() < 0.18:                            # a short branch
                bx = x
                for by in range(y, min(h, y + 3)):
                    bx = int(np.clip(bx + r.choice([-1, 1]), 0, w - 1)); rgb[by, bx] = ramp_colour("glow_red", 3.0); a[by, bx] = True
        return rgb, a

    def paint_sparkle(face, w, h):
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        c = w // 2
        for i in range(w):
            for j in range(h):
                if i == c - 1 or i == c or j == h // 2 - 1 or j == h // 2:
                    d = max(abs(i - c + 0.5), abs(j - h / 2 + 0.5))
                    rgb[j, i] = ramp_colour("glow_star", 3.0 - d * 0.8); a[j, i] = True
        return rgb, a

    # ---- atlas
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
                key = add_rect(f"{e['name']}:{face}", w, h, lambda e=e, face=face, w=w, h=h: paint_stone(e, face, w, h))
            elif kind.startswith("ore_"):
                key = add_rect(f"{kind}:{face}", w, h, lambda e=e, face=face, w=w, h=h, s_=len(rects): paint_ore(e, face, w, h, 50 + s_))
            elif kind == "gem":
                key = add_rect(f"gem:{face}", w, h, lambda face=face, w=w, h=h: paint_gem(face, w, h))
            elif kind == "frag_stone":
                key = add_rect(f"fs:{face}:{w}x{h}", w, h, lambda face=face, w=w, h=h: paint_frag_stone(face, w, h))
            elif kind == "frag_ore":
                key = add_rect(f"fo:{face}:{w}x{h}", w, h, lambda e=e, face=face, w=w, h=h: paint_ore(e, face, w, h, 9, frag=True))
            elif kind in ("moss", "snow", "slime"):
                key = add_rect(f"{kind}:{face}:{w}x{h}", w, h, lambda kind=kind, face=face, w=w, h=h: paint_cover(kind, face, w, h))
            elif kind in ("grass_card", "dry_card"):
                ramp = "grass" if kind == "grass_card" else "dry"
                key = add_rect(f"{kind}:{e['name'][-3]}:{face}", w, h, lambda ramp=ramp, face=face, w=w, h=h, s_=len(rects): paint_blades(ramp, face, w, h, s_))
            elif kind == "crack":
                key = add_rect(f"crack:{e['_data']['seed']}:{face}", w, h, lambda face=face, w=w, h=h, sd=e["_data"]["seed"]: paint_crack(face, w, h, sd))
            elif kind == "sparkle":
                key = add_rect(f"sparkle:{face}", w, h, lambda face=face, w=w, h=h: paint_sparkle(face, w, h))
            e["faces"][face] = key

    GAP = 2
    x = y = shelf = 0
    for k, r in sorted(rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
        if x + r["w"] > TEX: x, y, shelf = 0, y + shelf + GAP, 0
        r["x"], r["y"] = x, y; x += r["w"] + GAP; shelf = max(shelf, r["h"])
    used = y + shelf
    if used > TEX: raise SystemExit(f"{NAME}: atlas overflow {used}px of {TEX}")
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
        for k in ("_kind", "_hidden", "_data"): e.pop(k)

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
    fix_texture_bleed.pad_file(out, [os.path.join(OUT, f"{NAME}.png")])
    colours = len({tuple(c) for c in img[img[..., 3] > 0][:, :3]})
    xs = [v for e in elements for v in (e["from"][0], e["to"][0])]
    zs = [v for e in elements for v in (e["from"][2], e["to"][2])]
    print(f"{NAME:16s} cubes={len(elements):3d} atlas={used:3d}/{TEX} colours={colours:3d} "
          f"w={max(xs) - min(xs):.1f} d={max(zs) - min(zs):.1f} mound_top={mound_top:.1f} top={max(e['to'][1] for e in elements):.1f}")


if __name__ == "__main__":
    for k in (sys.argv[1:] or list(CFG)):
        build(k)
