"""Arcane props for the wizard's garden beside the wizard tower (J00BA, 2026-11-09: "add in the wizard tower
somewhere, add some cool other things next to it which makes sense with the current layout").

  arcane_circle          a ring of six rune-cut standing stones round a flagstone circle with glowing rune inlays, a
                         stepped pedestal in the middle with a floating crystal (light_1)
  crystal_cluster        glowing arcane crystals growing out of a rubble mound (large)
  crystal_cluster_small  the same, small
  spellbook_lectern      stone lectern with an open spellbook, glowing glyphs floating over it, candles
  arcane_lamp            rune-stone column with iron crescent arms holding a glowing violet orb (light_1)

Same materials as the wizard tower (castle limestone, rune stone, the tower's arcane violet and crystal ramps).
House style, 2 px per unit, front = north (-z). Glowing parts end in _glow.
Usage: py build_arcane_props.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from deco_lib import Deco, deco_mats, R, F, px, h2, C
from stall_lib import grid
from foliage_lib import ramp

OUT = r"C:\Users\lucas\blockbench_models\props\arcane"
TEX = [256]

R.update({   # the wizard tower's ramps (build_wizard_tower.py)
    "arcane": ramp("#2a0c5a #461a8a #6630b8 #8a52dc #ac80f0 #ceb4f8 #ece0fc"),
    "rune_stone": ramp("#14141e #1c1c2a #262636 #323244 #404054 #505066 #62627a"),
    "crystal": ramp("#06303e #0c5468 #148090 #26aab4 #4ccad0 #8ce4e4 #cef6f4"),
    "brass": ramp("#3a240c #5a3a12 #7c561c #9e7428 #be943a #d8b458 #ecd284"),
})


def M(kind, rm, side=(48, 32), top=(32, 32), **extra):
    d = {"kind": kind, "ramp": R[rm], "side": side, "top": top, "no_lit2": True}
    if extra: d["extra"] = extra
    return d


def new(name, seed):
    return Deco(name, seed, deco_mats({"runestone": M("ashlar", "rune_stone", (48, 32), (32, 32)),
                                       "rubble": M("cobble", "rune_stone", (48, 24), (32, 32)),
                                       "brass": M("metal", "brass", (24, 16), (16, 16))}), tex=TEX[0])


def fin(H):
    H.finish([OUT]); return H


# ---------------------------------------------------------------- painters
def rune_glyph(nr, w, h, seed):
    """A rune: 1 px strokes on a hard alpha card, bright violet core, a softer violet edge pixel here and there."""
    rng = np.random.default_rng(seed)
    a = np.zeros((h, w), bool)
    cx = w // 2
    a[1:h - 1, cx] = True                                             # stave
    for _ in range(2 + int(rng.integers(0, 2))):                      # branches
        y = int(rng.integers(1, h - 2)); d = int(rng.choice([-1, 1])); L = int(rng.integers(2, max(3, w // 2)))
        for k in range(L):
            x, yy = cx + d * k, y + (k if rng.random() < 0.5 else -k) // 2
            if 0 <= x < w and 0 <= yy < h: a[yy, x] = True
    if rng.random() < 0.5:                                            # a little ring
        r = max(1, w // 4); yy, xx = grid(w, h)
        a |= (np.abs(np.hypot(xx - cx, yy - h * 0.3) - r) < 0.6)
    rgb = C(R["arcane"], np.full((h, w), 5.4))
    edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0))
    rgb[edge] = C(R["arcane"], np.full((h, w), 4.4))[edge]
    return rgb, a


def crystal_face(H, w, h, cat):
    """Crystal column: a bright core band, darker facet edges, a glint (glows)."""
    yy, xx = grid(w, h)
    u = (xx + 0.5) / w - 0.5
    v = 3.6 + 2.2 * (1 - np.abs(u) * 2) ** 1.5 + 0.6 * (1 - (yy + 0.5) / h) + (0.6 if cat in ("up", "lit") else 0)
    rgb = C(R["crystal"], v)
    if w >= 3 and h >= 4: rgb[int(h * 0.25), int(w * 0.3)] = R["crystal"][6]
    return rgb, np.ones((h, w), bool)


def orb_face(H, w, h, cat, rm="arcane"):
    yy, xx = grid(w, h)
    r = np.hypot((xx + 0.5) / w - 0.4, (yy + 0.5) / h - 0.38)
    return C(R[rm], 6.2 - r * 4.0), np.ones((h, w), bool)


def crystal(H, name, grp, base, h, w, tilt, yaw, rm="crystal"):
    """A crystal column (a square prism rotated 45 about its axis) with a pointed tip, tilted out from its base."""
    bx, by, bz = base
    body = lambda W, Hh, c: crystal_face(H, W, Hh, c) if rm == "crystal" else orb_face(H, W, Hh, c, rm)
    rot = (tilt * math.cos(math.radians(yaw)), 45 + yaw, tilt * math.sin(math.radians(yaw)))
    H.item(f"{name}_glow", grp, [bx - w / 2, by - 1, bz - w / 2], [bx + w / 2, by + h, bz + w / 2], f"cry{rm}{w}x{h}", body,
           hide=("down",), rot=rot, origin=[bx, by, bz])
    tw = h2(max(0.5, w * 0.55)); th = h2(max(1.0, w * 0.9))
    H.item(f"{name}_tip_glow", grp, [bx - tw / 2, by + h, bz - tw / 2], [bx + tw / 2, by + h + th, bz + tw / 2], f"crt{rm}{tw}x{th}", body,
           hide=("down",), rot=rot, origin=[bx, by, bz])


def octo_stack(H, name, grp, layers, mat):
    """Stepped round pedestal: (D, y1, y2) layers of crossed boxes; the upper layer sits inside the lower one."""
    for i, (D, y1, y2) in enumerate(layers):
        H.octo(f"{name}_{i + 1}", grp, 0, 0, D, y1, y2, mat, ("down",) if i == 0 else ("down",))


# ==================================================================== arcane circle
def arcane_circle():
    H = new("arcane_circle", 9501)
    g = {k: H.group(k, [0, 0, 0]) for k in ("flagstones", "runes", "stones", "pedestal", "crystal")}
    n = 12; r = 34.0
    for k in range(n):                                               # a ring of flagstones, every other one raised a little
        a = k * 360 / n
        x, z = math.sin(math.radians(a)) * r, -math.cos(math.radians(a)) * r
        hgt = 1.0 if k % 2 else 1.5
        H.box(f"flagstone_{k + 1}", g["flagstones"], [x - 8, 0, z - 5], [x + 8, hgt, z + 5], "runestone", ("down",), f"flag{k % 2}",
              rot=(0, -a, 0), origin=[x, 0, z], place="ground")
        key = H.rect(f"rune_{k % 6}", 8, 10, lambda W, Hh, s=k % 6: rune_glyph(H.nr, W, Hh, 77 + s))
        H.card(f"rune_inlay_{k + 1}_glow", g["runes"], [x - 2, hgt + 0.05, z - 2.5], [x + 2, hgt + 0.05, z + 2.5], key,
               faces=("up", "down"), rot=(0, -a, 0), origin=[x, hgt, z])
    for k in range(6):                                               # six standing stones round the ring
        a = k * 60 + 30
        x, z = math.sin(math.radians(a)) * 44, -math.cos(math.radians(a)) * 44
        hgt = (36, 30, 40, 32, 38, 28)[k]
        sg = H.group(f"standing_stone_{k + 1}", [x, 0, z], g["stones"])
        lean = (-3, 2, -2, 4, -4, 3)[k]
        H.box(f"standing_stone_{k + 1}_body", sg, [x - 4, 0, z - 3], [x + 4, hgt, z + 3], "runestone", ("down",), f"ss{k % 3}",
              rot=(lean, -a, 0), origin=[x, 0, z], place="ground")
        H.box(f"standing_stone_{k + 1}_cap", sg, [x - 3, hgt, z - 2], [x + 3, hgt + 3, z + 2], "runestone", ("down",), "sscap",
              rot=(lean, -a, 0), origin=[x, 0, z])
        key = H.rect(f"srune_{k}", 8, 14, lambda W, Hh, s=k: rune_glyph(H.nr, W, Hh, 300 + s))
        H.card(f"standing_stone_{k + 1}_rune_glow", sg, [x - 2, hgt * 0.45, z + 3.05], [x + 2, hgt * 0.45 + 7, z + 3.05], key,
               faces=("south", "north"), rot=(lean, -a, 0), origin=[x, 0, z])
    p = g["pedestal"]
    octo_stack(H, "pedestal", p, [(14, 0, 2), (10, 2, 4), (6, 4, 14), (9, 14, 16)], "stone")
    H.n_light += 1
    lg = H.group(f"light_{H.n_light}", [0, 22, 0], g["crystal"])
    crystal(H, "floating_crystal", lg, [0, 18.5, 0], 6, 3, 0, 0)
    H.box("floating_crystal_lower_glow", lg, [-1, 16.5, -1], [1, 18.5, 1], "gold", (), "fclow", rot=(0, 45, 0), origin=[0, 17.5, 0])
    for k in range(4):                                              # small shards orbiting the crystal
        a = math.radians(k * 90 + 20); x, z = math.cos(a) * 6, math.sin(a) * 6
        crystal(H, f"shard_{k + 1}", lg, [x, 19 + (k % 2) * 2, z], 2, 1, 25, k * 90)
    # idle: the crystal and its shards turn and bob (looping, 4 s)
    import uuid
    def kf(ch, t, xyz):
        return {"channel": ch, "data_points": [{"x": str(xyz[0]), "y": str(xyz[1]), "z": str(xyz[2])}],
                "uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "time": t, "color": -1, "interpolation": "catmullrom"}
    keys = [kf("rotation", t, (0, deg, 0)) for t, deg in ((0, 0), (1, 90), (2, 180), (3, 270), (4, 360))]
    keys += [kf("position", t, (0, y, 0)) for t, y in ((0, 0), (1, 1), (2, 0), (3, 1), (4, 0))]
    anim = {"uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "name": "idle", "loop": "loop", "override": False,
            "length": 4, "snapping": 24, "selected": False, "anim_time_update": "", "blend_weight": "", "start_delay": "",
            "loop_delay": "", "animators": {H.m.groups[lg]["uuid"]: {"name": lg, "type": "bone", "keyframes": keys}}}
    orig = H.m.bbmodel
    H.m.bbmodel = lambda: {**orig(), "animations": [anim]}
    return fin(H)


# ==================================================================== crystal clusters
def _cluster(name, seed, big):
    H = new(name, seed)
    g = {k: H.group(k, [0, 0, 0]) for k in ("rock", "crystals")}
    s = 1.0 if big else 0.55
    rocks = [((-8, -6), (8, 5), 6), ((-3, -9), (9, 3), 4), ((-11, -2), (-3, 8), 5), ((2, 0), (12, 9), 3.5)]
    for i, ((x1, z1), (x2, z2), hgt) in enumerate(rocks):
        H.box(f"rock_{i + 1}", g["rock"], [h2(x1 * s), 0, h2(z1 * s)], [h2(x2 * s), h2(hgt * s) if hgt * s >= 1 else 1, h2(z2 * s)],
              "rubble", ("down",), f"rk{i}", place="ground")
    spec = [((0, 6, -1), 22, 4, 6, 0), ((-4, 5, 2), 15, 3, 22, 150), ((4, 4, -4), 13, 3, 25, 40), ((-5, 4, -4), 10, 2.5, 30, 250),
            ((5, 3, 4), 9, 2, 32, 100), ((1, 4, 5), 7, 2, 35, 200), ((-8, 2, 0), 6, 1.5, 45, 280)]
    for i, ((x, y, z), hgt, w, tilt, yaw) in enumerate(spec[:7 if big else 5]):
        crystal(H, f"crystal_{i + 1}", g["crystals"], [x * s, y * s, z * s], h2(max(2, hgt * s)), h2(max(1, w * s)), tilt, yaw)
    H.tufts("tuft", g["rock"], [(-10 * s, 7 * s, 3, 3), (10 * s, -6 * s, 2, 3)])
    return fin(H)


def crystal_cluster(): return _cluster("crystal_cluster", 9511, True)
def crystal_cluster_small(): return _cluster("crystal_cluster_small", 9512, False)


# ==================================================================== spellbook lectern
def spellbook_lectern():
    H = new("spellbook_lectern", 9521)
    g = {k: H.group(k, [0, 0, 0]) for k in ("lectern", "book", "glyphs", "candles")}
    l = g["lectern"]
    H.box("base", l, [-6, 0, -6], [6, 2, 6], "runestone", ("down",), "lbase", place="ground")
    H.box("foot", l, [-4.5, 2, -4.5], [4.5, 3.5, 4.5], "stone", ("down",), "lfoot")
    H.octo("column", l, 0, 0, 5, 3.5, 15, "stone", ("down", "up"))
    H.box("collar", l, [-3.5, 15, -3.5], [3.5, 16.5, 3.5], "runestone", ("down",), "lcollar")
    H.box("desk", l, [-6, 16.5, -4.5], [6, 18, 4.5], "stone", (), "ldesk", rot=(-20, 0, 0), origin=[0, 17, 0])
    H.box("desk_lip", l, [-6, 17.5, -5.5], [6, 19, -4.5], "brass", (), "llip", rot=(-20, 0, 0), origin=[0, 17, 0])
    b = g["book"]
    pg = H.rect("pages_open", px(9), px(6), lambda W, Hh: H.P.pages(W, Hh, "up"))
    fs = H.faces([-4.5, 18, -3], [4.5, 19, 3], "brass", ("down",)); fs["up"] = F(pg)
    for f in ("north", "south", "east", "west"):
        fs[f] = H.faces([-4.5, 18, -3], [4.5, 19, 3], "brass", ("down",))[f]
    H.m.cube("book_pages", b, [-4.5, 18, -3], [4.5, 19, 3], fs, (-20, 0, 0), [0, 17, 0])
    H.item("book_cover", b, [-5, 17.5, -3.5], [5, 18, 3.5], "bcover", lambda W, Hh, c: H.P.book(R["indigo"], W, Hh, c), rot=(-20, 0, 0), origin=[0, 17, 0])
    gk = [H.rect(f"glyph_{i}", 6, 8, lambda W, Hh, s=i: rune_glyph(H.nr, W, Hh, 500 + s)) for i in range(4)]
    for i, (x, y, z) in enumerate(((-3, 22, -1), (0, 24.5, 0), (3, 22.5, 1), (0.5, 27, -1))):
        H.card(f"glyph_{i + 1}_glow", g["glyphs"], [x - 1.5, y, z], [x + 1.5, y + 4, z], gk[i], faces=("north", "south"),
               rot=(0, (i - 1.5) * 25, 0), origin=[x, y, z])
    c = g["candles"]
    for i, (x, z, hh) in enumerate(((-8, -3, 5), (8, 2, 7), (-7.5, 3.5, 3.5))):
        H.item(f"candle_{i + 1}", c, [x - 0.75, 0, z - 0.75], [x + 0.75, hh, z + 0.75], f"cand{hh}", lambda W, Hh, cat: H.P.form(R["candle"], W, Hh, cat, 4.0))
        H.item(f"candle_{i + 1}_flame_glow", c, [x - 0.5, hh, z - 0.5], [x + 0.5, hh + 1.5, z + 0.5], "cflame",
               lambda W, Hh, cat: H.P.form(R["glow"], W, Hh, cat, 5.2, noise=0), hide=())
    return fin(H)


# ==================================================================== arcane lamp
def arcane_lamp():
    H = new("arcane_lamp", 9531)
    g = {k: H.group(k, [0, 0, 0]) for k in ("base", "column", "arms")}
    H.box("plinth", g["base"], [-5, 0, -5], [5, 2, 5], "runestone", ("down",), "aplinth", place="ground")
    H.box("plinth_step", g["base"], [-4, 2, -4], [4, 3.5, 4], "stone", ("down",), "astep")
    H.octo("column", g["column"], 0, 0, 3.5, 3.5, 36, "runestone", ("down", "up"))
    for i, y in enumerate((12, 24)):
        H.box(f"band_{i + 1}", g["column"], [-2.25, y, -2.25], [2.25, y + 1, 2.25], "brass", (), "aband")
    key = H.rect("lamp_rune", 4, 12, lambda W, Hh: rune_glyph(H.nr, W, Hh, 900))
    H.card("column_rune_glow", g["column"], [-1, 15, -1.8], [1, 21, -1.8], key, faces=("north", "south"))
    H.box("capital", g["column"], [-3, 36, -3], [3, 37.5, 3], "stone", (), "acap")
    for s in (-1, 1):                                                # iron crescent arms cradling the orb
        H.curve(f"arm_{'r' if s > 0 else 'l'}", g["arms"], [0, 37.5, 0], (s, 0),
                [(0.5, 0.0), (2.4, 1.2), (3.6, 3.4), (3.8, 6.0), (3.0, 8.4), (1.6, 9.8)], 0.5, "iron")
    H.n_light += 1
    lg = H.group(f"light_{H.n_light}", [0, 42, 0], g["arms"])
    H.item("orb_glow", lg, [-2.5, 39.5, -2.5], [2.5, 44.5, 2.5], "orb", lambda W, Hh, c: orb_face(H, W, Hh, c), hide=())
    H.item("orb_core_glow", lg, [-1.75, 39, -1.75], [1.75, 45, 1.75], "orbcore", lambda W, Hh, c: orb_face(H, W, Hh, c), hide=(),
           rot=(0, 45, 0), origin=[0, 42, 0])
    crystal(H, "tip", g["arms"], [0, 47.5, 0], 3, 1.5, 0, 0)
    return fin(H)


BUILDERS = {f.__name__: f for f in (arcane_circle, crystal_cluster, crystal_cluster_small, spellbook_lectern, arcane_lamp)}


def build(n):
    for t in (256, 512):
        TEX[0] = t
        try:
            return BUILDERS[n]()
        except SystemExit as e:
            if "overflow" not in str(e): raise
            print(f"  {n}: {e}; trying a bigger texture")


if __name__ == "__main__":
    for n in (sys.argv[1:] or BUILDERS):
        build(n)
