"""Mining and lumbering item models (J00BA, 2026-11-15): every ore (nugget_), gem (gemstone_) and amber / sap (sap_)
as a Blockbench model, in the house style (centre light, darker edges, a glint), colours sampled once from each sprite
in godot-game/sprites/items/ and kept in gem_ramps.json (the sprites are then replaced by renders of these models).
Usage: py build_gem_items.py [name ...]   writes C:/Users/lucas/blockbench_models/items/<name>.bbmodel + .png"""
import os, sys, json, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from stall_lib import Stall, R, F, px, LO, grid
from house_lib import C
from build_wood_items import _ramp_from, _sprite_px

OUT = r"C:\Users\lucas\blockbench_models\items"
CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "gem_ramps.json")
AMBERS = ["ash", "birch", "bloodwood", "ebony", "goldleaf", "oak", "pine", "silverbark", "starwood", "voidwood"]
ORES = ["adamantite", "coal", "copper", "gold", "iron", "mithril", "obsidian", "stellarite", "tin", "void"]
GEMS = {"amethyst": "oval", "arcanium": "star", "diamond": "brilliant", "eclipsium": "orb", "emerald": "emerald_cut",
        "jade": "pebble", "painite": "cluster", "ruby": "cushion", "sapphire": "oval", "topaz": "round"}


FIXED = {   # sampling these sprites gives grey (eclipsium: a black orb with a white glint) or brown (painite: dark
            # red crystals with a heavy outline), so their ramps are set by hand from the sprites' main colours
    "gemstone_eclipsium": "#08060e #120e1c #1e182c #2c2440 #463c60 #7a70a0 #d8d4f0",
    "gemstone_painite": "#2a0408 #4a0810 #741018 #a01c24 #c8343a #e45a5a #f49090",
}


def ramp_of(sprite):
    if sprite in FIXED:
        return [np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float) for c in FIXED[sprite].split()]
    cache = json.load(open(CACHE)) if os.path.exists(CACHE) else {}
    if sprite not in cache:
        cache[sprite] = [list(map(int, c)) for c in _ramp_from(_sprite_px(sprite))]
        json.dump(cache, open(CACHE, "w"), indent=1)
    return [np.array(c, float) for c in cache[sprite]]


# ---------------------------------------------------------------- painters
def glossy(H, Rm, w, h, cat, glint=True, sparkle=False):
    """Polished stone / glass / resin: bright centre and upper left, darker rim and base, a near white glint."""
    yy, xx = grid(w, h)
    dx = (xx + 0.5) / w - 0.4; dy = (yy + 0.5) / h - 0.35
    v = 4.4 + LO[cat] * 0.7 - np.clip(np.hypot(dx, dy) * 2.2, 0, 2.4) + H.P.noise(w, h, 0.05)
    rgb = C(Rm, v)
    if glint and cat in ("lit", "up") and w >= 3 and h >= 3:
        rgb[max(0, int(h * 0.25)), max(0, int(w * 0.3))] = np.minimum(np.array(Rm[-1]) + 30, 250)
    if sparkle:
        r = H.nr.random((h, w)) < 0.06
        rgb[r] = np.minimum(np.array(Rm[-1]) + 40, 252)
    return rgb, np.ones((h, w), bool)


def rock(H, Rm, w, h, cat, sparkle=False):
    """An ore chunk: faceted shading, darker cracks, a few light flecks of the metal (stars for stellarite)."""
    yy, xx = grid(w, h)
    v = 3.4 + LO[cat] - np.clip(np.maximum(np.abs((xx + 0.5) / w - 0.5), np.abs((yy + 0.5) / h - 0.5)) * 2 - 0.4, 0, 1) * 1.2
    v += H.P.blotches(w, h, max(1, w * h // 40), 0.5, 1, 3) + H.P.noise(w, h, 0.12)
    crack = ((xx * 3 + yy * 5) % 11 == 0) | ((xx * 5 - yy * 2) % 13 == 0)
    v = v - 1.1 * crack
    rgb = C(Rm, v)
    fl = H.nr.random((h, w)) < (0.08 if sparkle else 0.04)
    rgb[fl] = np.minimum(np.array(Rm[-1]) + (50 if sparkle else 10), 252)
    return rgb, np.ones((h, w), bool)


def swirl(H, Rm, w, h, cat):
    """Void stone: a dark spiral on the face."""
    rgb, a = rock(H, Rm, w, h, cat)
    if cat in ("lit", "up"):
        yy, xx = grid(w, h); cx, cy = w / 2, h / 2
        ang = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx); r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
        arm = np.abs(((ang + r * 0.9) % (math.pi)) - math.pi / 2) < 0.35
        rgb[arm & (r < min(w, h) * 0.45)] = Rm[-1]
    return rgb, a


# ---------------------------------------------------------------- shapes
def octo_stack(H, g, name, tiers, tag, paint, cx=0.0, cz=0.0):
    """A rounded solid along y: per tier (y0, y1, width) two crossed boxes (an octagon)."""
    for k, (y0, y1, wd) in enumerate(tiers):
        a, b = wd / 2, math.floor(wd * 0.35 * 2) / 2
        H.item(f"{name}_{k + 1}_a", g, [cx - a, y0, cz - b], [cx + a, y1, cz + b], f"{tag}{k}a", paint, hide=())
        H.item(f"{name}_{k + 1}_b", g, [cx - b, y0, cz - a], [cx + b, y1, cz + a], f"{tag}{k}b", paint, hide=())


def make_amber(wood, seed):
    """An amber / sap teardrop: a round glossy body narrowing to a drawn-out tip."""
    import foliage_lib; foliage_lib.PPU = 2
    Rm = ramp_of(f"sap_{wood}")
    H = Stall(f"{wood}_sap", seed, tex=128, mats={})
    g = H.group("drop", [0, 0, 0])
    paint = lambda W, Hh, c: glossy(H, Rm, W, Hh, c, sparkle=wood in ("starwood", "voidwood"))
    octo_stack(H, g, "drop", [(0, 1, 6), (1, 3, 9), (3, 6, 10), (6, 8, 9), (8, 9.5, 6.5), (9.5, 11, 4), (11, 13, 2.5),
                              (13, 15.5, 1.5)], "d", paint)
    return H


# ---------------------------------------------------------------- v2 (J00BA, 2026-11-15): "triple the detail, metallic ores,
# shiny gems, arcanium a glowing purple star". 4 px per unit (the doc's density for close-up items), many more pieces.
import foliage_lib
HI_PPU = 4
SKY = [.26, .40, .34, .10, .22, .46, .52, .64, .78, .90]          # the stalls' gold reflection: dark horizon, bright sky


def _env(N):
    """Reflected studio sky for polished metal: a hard dark horizon, a warm ground, a bright sky, a hot spot."""
    x, y = N[..., 0], N[..., 1] - 0.55 * N[..., 0] ** 2
    t = np.interp(y, [-1.6, -1.1, -0.18, -0.06, -0.02, 0.03, .05, .3, .55, 1], SKY)
    t = t + .17 * np.exp(-((x - .40) / .09) ** 2) - .10 * np.exp(-((x + .36) / .12) ** 2)
    L = np.array([-0.45, 1.0, 0.55]); L = L / np.linalg.norm(L)
    h = np.clip(N @ L, 0, 1)
    return t + .17 * h ** 9 + .42 * h ** 60


BASE_N = {"up": (0.0, 1.0, 0.0), "lit": (-0.45, 0.25, 0.85), "shade": (0.55, 0.15, -0.8), "down": (0.0, -1.0, 0.0)}


def _cells(H, w, h, size):
    """A hammered-facet field: per pixel a cell id, a random tilt per cell, and the distance to the cell's edge."""
    yy, xx = grid(w, h)
    n = max(2, int(w * h / (size * size)))
    pts = H.nr.random((n, 2)) * [w, h]
    d = np.full((h, w), 1e9); d2 = d.copy(); cid = np.zeros((h, w), int)
    for i, (px_, py_) in enumerate(pts):
        di = np.hypot(xx + 0.5 - px_, yy + 0.5 - py_)
        closer = di < d
        d2 = np.where(closer, d, np.minimum(d2, di)); cid = np.where(closer, i, cid); d = np.where(closer, di, d)
    tilt = (H.nr.random((n, 2)) - 0.5) * 0.9
    return cid, tilt, d2 - d


def metal(H, Rm, w, h, cat, flecks=0.0):
    """Polished ore metal: each face domed, broken into hammered facets with their own tilt, mirrored against a
    studio sky (dark horizon line, bright top, hot highlight); dark seams between the facets; optional star flecks."""
    yy, xx = grid(w, h)
    nx, ny = (xx + 0.5) / w * 2 - 1, (yy + 0.5) / h * 2 - 1
    cid, tilt, edge = _cells(H, w, h, 6)
    b = np.array(BASE_N[cat], float)
    U = np.array([1.0, 0, 0]) if cat in ("up", "down") else np.array([1.0, 0, 0.3])
    V = np.array([0, 0, 1.0]) if cat in ("up", "down") else np.array([0, -1.0, 0])
    tx, ty = tilt[cid, 0], tilt[cid, 1]
    N = b + (0.45 * nx + tx)[..., None] * U + (0.45 * ny + ty)[..., None] * V
    N = N / np.linalg.norm(N, axis=-1, keepdims=True)
    v = _env(N) * (len(Rm) - 1) * 1.05
    v = v - 1.6 * (edge < 0.9) - 0.6 * ((edge >= 0.9) & (edge < 1.6))    # seams between facets, a soft lip
    v = v + 0.25 * LO[cat]
    rgb = C(Rm, v)
    if flecks:
        f = H.nr.random((h, w)) < flecks
        rgb[f] = np.minimum(np.array(Rm[-1]) + 60, 252)
    return rgb, np.ones((h, w), bool)


def facets(H, Rm, w, h, cat, glow=False):
    """A cut gem face: kite facets fanning from the centre at different brightness, bright facet edges, a calmer
    table in the middle, a dark rim, a star glint, and (glow) a light core."""
    yy, xx = grid(w, h)
    cx, cy = w / 2, h / 2
    dx, dy = (xx + 0.5 - cx) / (w / 2), (yy + 0.5 - cy) / (h / 2)
    r = np.maximum(np.abs(dx), np.abs(dy)) * 0.6 + np.hypot(dx, dy) * 0.4
    ang = (np.arctan2(dy, dx) + math.pi) / (2 * math.pi)
    seg = np.floor(ang * 8).astype(int) % 8
    shade = np.array([0.9, 0.2, -0.5, -0.9, -0.4, 0.3, 1.1, 0.6])[seg]
    v = 3.6 + LO[cat] * 0.6 + shade * 0.9 * np.clip(r * 1.6, 0, 1) - np.clip(r - 0.8, 0, 1) * 3.5
    table = r < 0.42
    v = np.where(table, 4.6 + LO[cat] * 0.4 - dy * 0.8, v)
    frac = (ang * 8) % 1
    v = v + 1.3 * (((frac < 0.06) | (frac > 0.94)) & (r > 0.42) & (r < 0.92))     # facet edges catch the light
    v = v + 1.1 * (np.abs(r - 0.42) < 0.05)                                         # the table's rim
    if glow:
        v = v + 1.2 * np.clip(1 - r * 1.8, 0, 1)
    rgb = C(Rm, v + H.P.noise(w, h, 0.04))
    if cat in ("lit", "up") and w >= 6 and h >= 6:                                  # a four-point glint, upper left
        gx, gy = int(w * 0.32), int(h * 0.28)
        hot = np.minimum(np.array(Rm[-1]) * 0.4 + 160, 252)
        for k in range(-2, 3):
            for (ax, ay) in ((gx + k, gy), (gx, gy + k)):
                if 0 <= ax < w and 0 <= ay < h:
                    rgb[ay, ax] = hot if abs(k) < 2 else np.minimum(np.array(Rm[-1]) + 30, 250)
    return rgb, np.ones((h, w), bool)


def make_ore(ore, seed):
    """An ore chunk of 9 to 10 polished pieces round a core: metal ores mirror like polished metal; coal and
    obsidian are glassy black facets; stellarite carries star flecks; void stone a glowing swirl on its core."""
    foliage_lib.PPU = HI_PPU
    Rm = ramp_of(f"nugget_{ore}")
    H = Stall(f"{ore}_ore", seed, tex=256, mats={})
    g = H.group("ore", [0, 0, 0])
    if ore in ("coal", "obsidian"):
        paint = lambda W, Hh, c: facets(H, Rm, W, Hh, c)
    else:
        paint = lambda W, Hh, c: metal(H, Rm, W, Hh, c, flecks=0.05 if ore == "stellarite" else 0.0)
    rng = H.rng
    pieces = [(0, 0, 0, 8, 7, 7, 0, 0)]                            # the core, then pieces round it
    for k in range(9):
        a = k / 9 * 2 * math.pi + rng.uniform(-0.3, 0.3)
        rad = rng.uniform(3.5, 5.5)
        w_ = rng.choice([3, 3.5, 4, 4.5, 5]); h_ = rng.choice([2.5, 3, 3.5, 4, 5]); d_ = rng.choice([3, 3.5, 4, 4.5])
        y = rng.choice([0, 0, 1, 2.5, 3.5]) if k % 3 else rng.choice([4, 5])
        pieces.append((round(math.cos(a) * rad * 2) / 2, y, round(math.sin(a) * rad * 0.8 * 2) / 2, w_, h_, d_,
                       rng.choice([0, 11.25, 22.5, 33.75, -22.5]), rng.choice([0, 0, 11.25, -11.25, 22.5])))
    for k, (x, y, z, w_, h_, d_, yaw, tilt) in enumerate(pieces):
        H.item(f"piece_{k + 1}", g, [x - w_ / 2, y, z - d_ / 2], [x + w_ / 2, y + h_, z + d_ / 2], f"pc{k}", paint,
               hide=("down",) if y == 0 else (), rot=(tilt, yaw, -tilt / 2), origin=[x, y, z])
    if ore == "void":                                               # a swirl of glowing void on the front of the core
        sk = H.rect("void_swirl", 24, 24, lambda W, Hh: _swirl(Rm, W, Hh))
        H.card("void_swirl_glow", g, [-3, 1, -3.55], [3, 7, -3.55], sk, faces=("north",))
    return H


def _swirl(Rm, w, h):
    yy, xx = grid(w, h); cx, cy = w / 2, h / 2
    ang = np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx); r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / (w / 2)
    arm = np.abs(((ang + r * 6) % math.pi) - math.pi / 2) < 0.45
    a = arm & (r < 1.0) & (r > 0.08)
    return C(R["glow_violet"], 4.8 - r * 2.5), a


def _face_layers(H, g, paint, w, h, d, glow=False):
    """An upright cut gem facing the viewer (-z): a rounded octagon girdle of three stepped boxes, a crown of two
    bevel layers and the table in front, a pavilion of two layers behind."""
    b = math.floor(min(w, h) * 0.3 * 2) / 2; c = math.floor(b)
    H.item("girdle_a", g, [-w / 2, b, -d / 2], [w / 2, h - b, d / 2], "ga", paint, hide=())
    H.item("girdle_b", g, [-w / 2 + b, 0, -d / 2], [w / 2 - b, h, d / 2], "gb", paint, hide=())
    H.item("girdle_c", g, [-w / 2 + c / 2, c / 2, -d / 2], [w / 2 - c / 2, h - c / 2, d / 2], "gc", paint, hide=())
    for k, (ins, dep) in enumerate(((1, 1), (2, 1), (3.5, 0.5))):   # crown bevels to the table
        z0 = -d / 2 - sum(x[1] for x in ((1, 1), (2, 1), (3.5, 0.5))[:k])
        H.item(f"crown_{k + 1}", g, [-w / 2 + ins, ins, z0 - dep], [w / 2 - ins, h - ins, z0], f"cr{k}", paint, hide=("south",))
    for k, (ins, dep) in enumerate(((2.5, 1), (4.5, 1))):            # pavilion behind, tucked inside the outline
        z0 = d / 2 + (1 if k else 0)
        H.item(f"pavilion_{k + 1}", g, [-w / 2 + ins, ins, z0], [w / 2 - ins, h - ins, z0 + dep], f"pv{k}", paint, hide=("north",))


def make_gem(gem, seed):
    """A cut gem in its sprite's cut, with stacked bevels and faceted, glinting faces. Arcanium is a glowing star."""
    foliage_lib.PPU = HI_PPU
    Rm = ramp_of(f"gemstone_{gem}")
    cut = GEMS[gem]
    H = Stall(f"{gem}_gem", seed, tex=512 if cut in ("brilliant", "orb", "pebble", "cluster") else 256, mats={})
    g = H.group("gem", [0, 0, 0])
    paint = lambda W, Hh, c: facets(H, Rm, W, Hh, c, glow=gem in ("eclipsium",))
    if cut in ("oval", "emerald_cut"):
        _face_layers(H, g, paint, 10, 16, 4)
    elif cut == "cushion":
        _face_layers(H, g, paint, 14, 14, 4)
    elif cut == "round":
        _face_layers(H, g, paint, 14, 14, 5)
    elif cut == "brilliant":                                       # a tall pavilion to a point, a stepped crown, the table
        octo_stack(H, g, "pavilion", [(0, 1, 1.5), (1, 2.5, 3.5), (2.5, 4, 5.5), (4, 5.5, 8), (5.5, 7, 10.5), (7, 8.5, 13),
                                      (8.5, 10, 15)], "pv", paint)
        octo_stack(H, g, "crown", [(10, 11, 15), (11, 12.5, 12.5), (12.5, 13.5, 10)], "cr", paint)
    elif cut == "orb":
        octo_stack(H, g, "orb", [(0, 1, 5), (1, 2.5, 8.5), (2.5, 4.5, 11), (4.5, 8.5, 12.5), (8.5, 10.5, 11), (10.5, 12, 8.5),
                                 (12, 13, 5)], "ob", paint)
    elif cut == "pebble":
        octo_stack(H, g, "pebble", [(0, 1, 9), (1, 3, 12.5), (3, 5.5, 14), (5.5, 7.5, 12.5), (7.5, 9, 10), (9, 10, 6)], "pb", paint)
    elif cut == "cluster":                                          # seven crystals fanning up, each with a two-step tip
        for k, (x, z, hh, rz, rx) in enumerate(((0, 0, 15, 0, 0), (-3.5, 1, 11, 22.5, 5), (3.5, 1, 10, -22.5, -5),
                                                 (-1.5, -2.5, 8, 15, -15), (2, -2, 8, -15, -12), (-4.5, -1, 7, 33.75, 0),
                                                 (4.5, -0.5, 6, -33.75, 8))):
            H.item(f"crystal_{k + 1}", g, [x - 1.5, 0, z - 1.5], [x + 1.5, hh, z + 1.5], f"cy{k}", paint, hide=(),
                   rot=(rx, 45, rz), origin=[x, 0, z])
            H.item(f"crystal_{k + 1}_tip_a", g, [x - 1, hh, z - 1], [x + 1, hh + 1.5, z + 1], f"ta{k}", paint, hide=(),
                   rot=(rx, 45, rz), origin=[x, 0, z])
            H.item(f"crystal_{k + 1}_tip_b", g, [x - 0.5, hh + 1.5, z - 0.5], [x + 0.5, hh + 3, z + 0.5], f"tb{k}", paint, hide=(),
                   rot=(rx, 45, rz), origin=[x, 0, z])
    elif cut == "star":
        _glow_star(H, g)
    return H


def _glow_star(H, g):
    """Arcanium: a glowing purple star. Four long points (up, down, left, right) of five tapering steps, four shorter
    diagonal points, a white-hot core. Every cube is *_glow, so Godot makes the whole star emissive."""
    Rs = [np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float) for c in
          "#2a0458 #48108a #6a1cc0 #9030f0 #b45cff #dca4ff #fbf0ff".split()]
    def glowp(W, Hh, c):
        yy, xx = grid(W, Hh)
        dd = np.minimum(np.abs((xx + 0.5) / W - 0.5), np.abs((yy + 0.5) / Hh - 0.5)) * 2
        v = 5.0 - dd * 3.2 - np.maximum(np.abs((xx + 0.5) / W - 0.5), np.abs((yy + 0.5) / Hh - 0.5)) * 2.2   # white core, deep violet edges
        return C(Rs, v + H.P.noise(W, Hh, 0.05)), np.ones((Hh, W), bool)
    cy = 10
    for k, ang in enumerate((0, 90, 180, 270)):                    # long points
        for s, (wd, y0, y1) in enumerate(((6, 0, 2), (5, 2, 4), (4, 4, 6), (3, 6, 8), (2, 8, 10), (1, 10, 12))):
            H.item(f"point_{k + 1}_{s + 1}_glow", g, [-wd / 2, cy + 1.5 + y0, -2 + s * 0.25], [wd / 2, cy + 1.5 + y1, 2 - s * 0.25],
                   f"lp{s}", glowp, hide=(), rot=(0, 0, ang), origin=[0, cy, 0])
    for k, ang in enumerate((45, 135, 225, 315)):                  # short diagonal points
        for s, (wd, y0, y1) in enumerate(((4, 0, 2), (3, 2, 4), (2, 4, 5.5), (1, 5.5, 7))):
            H.item(f"diag_{k + 1}_{s + 1}_glow", g, [-wd / 2, cy + 1.5 + y0, -1], [wd / 2, cy + 1.5 + y1, 1],
                   f"dp{s}", glowp, hide=(), rot=(0, 0, ang), origin=[0, cy, 0])
    octo_stack(H, g, "core_glow", [(cy - 3.5, cy - 2, 5), (cy - 2, cy + 2, 8), (cy + 2, cy + 3.5, 5)], "core", glowp)


BUILDERS = {}
for n, w in enumerate(AMBERS):
    BUILDERS[f"{w}_sap"] = (lambda w=w, n=n: make_amber(w, 4300 + n))
for n, o in enumerate(ORES):
    BUILDERS[f"{o}_ore"] = (lambda o=o, n=n: make_ore(o, 4400 + n))
for n, gm in enumerate(GEMS):
    BUILDERS[f"{gm}_gem"] = (lambda gm=gm, n=n: make_gem(gm, 4500 + n))

if __name__ == "__main__":
    for nm in sys.argv[1:] or list(BUILDERS):
        BUILDERS[nm]().finish([OUT])
