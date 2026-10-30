"""Builds every weapon in every tier, to docs/blockbench_detailed_prompts.md section 3.6.

    python build_weapons.py            # all weapons
    python build_weapons.py sword      # one kind

Weapons follow the tool ladder (Stone to Stellarite, the tiers the tools are built in) and the
tool themes from the pickaxes: low tiers plain and practical, high tiers ornate and magical, each
tier's gem from its ore (D-012 pairings). Held items: 4 px per unit, upright along +y with the
blade or head up, flat in x, pivot at the centre of the grip. Glowing parts are cubes named
`*_glow` (Void and Stellarite).

Writes godot-game/assets/models/weapons/<tier>_<kind>.bbmodel, the texture to
godot-game/assets/textures/weapons/, and <kind>s_lineup.bbmodel with the ten tiers side by side.
"""
import math
import os
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bbkit import Mat, Model, from_base, put, ramp, stretch  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "weapons"
TEX = GAME / "assets" / "textures" / "weapons"
PPU = 4

# Metal ramps from the tool tiers (sampled from the tier icons), stretched to 7 shades.
STONE = ramp("#1c1e26", "#2c2f38", "#3e424c", "#545862", "#6c707a", "#8a8e96", "#aeb2b8")
ASH = stretch(ramp("301e14", "45271c", "604029", "795331", "9a7550"))
OAK = stretch(ramp("2a170c", "392011", "482916", "56321b", "6e4a2c"))
LEATHER = ramp("#2a160e", "#422416", "#5c3420", "#78462a", "#965c36", "#b07648")
VOID_GLOW = ramp("#120424", "#2a0c4a", "#4a1878", "#7428b0", "#a448e0", "#d06cff", "#f0c8ff")
STAR_GLOW = ramp("#2a2050", "#4a3c80", "#8070b0", "#c8b080", "#f0d890", "#fff6c8")

TIERS = [
    dict(id="stone", metal=STONE, kind="stone", wood=ASH, wrap=LEATHER, gem=None, level=0),
    dict(id="bronze", metal=stretch(ramp("4f2f18", "795331", "915237", "c67734", "ec9966", "f8ea95")),
         wood=ASH, wrap=LEATHER, gem=None, level=1,
         trim=stretch(ramp("5a2c14", "8a4a24", "b8683a", "d88a50", "f0b070"))),
    dict(id="iron", metal=stretch(ramp("3a3440", "4d444c", "5a5d69", "7c899b", "aea7b5", "f8f5f0")),
         wood=ASH, wrap=LEATHER, gem=None, level=2),
    dict(id="steel", metal=stretch(ramp("23283f", "333a5b", "424461", "545461", "656c81", "91aad5", "c8d8f0")),
         wood=ASH, wrap=stretch(ramp("1a1c28", "262a3c", "343a52", "48506c", "5e6a8a")), gem=None, level=3),
    dict(id="gold", metal=stretch(ramp("8a3e14", "ce6825", "e38a23", "f19f26", "f9d369", "f9f47d")),
         wood=ASH, wrap=stretch(ramp("3a0c10", "5c141a", "801e24", "a42c2c", "c84a3c")),
         gem=stretch(ramp("044a24", "067739", "1d874c", "24cb3f", "8dfa68")), level=4),
    dict(id="obsidian", metal=stretch(ramp("1a1420", "2b2332", "382e43", "483b50", "6b5690", "b49dd2")),
         wood=OAK, wrap=stretch(ramp("10141a", "1a2028", "262e38", "34404c", "465462")),
         gem=stretch(ramp("1c4a3a", "296952", "3c8e62", "67bc94", "acf0d3")), level=5),
    dict(id="titanite", metal=stretch(ramp("4a3a6a", "6b5690", "9b7db3", "b49dd2", "cec3e3", "e9d3f3")),
         wood=OAK, wrap=stretch(ramp("24203a", "322c50", "443c68", "5a5084", "7468a0")),
         gem=stretch(ramp("244e8a", "3c81cd", "74b7e3", "b5f2fc", "f3fbfe")), level=6),
    dict(id="dreadstone", metal=stretch(ramp("2a0c14", "431420", "5c2c35", "762d35", "98323e", "c4644a")),
         wood=OAK, wrap=stretch(ramp("1a0a0c", "2a1014", "3c181c", "502226", "6a3030")),
         gem=stretch(ramp("3a0208", "62040e", "a10e25", "dd3543", "f07080")), level=7),
    dict(id="void", metal=stretch(ramp("1a1028", "2b1d3b", "301f4d", "3c2c57", "5e4867", "818190")),
         wood=stretch(ramp("1c1228", "2b1d3b", "382658", "49355b", "5e4867")),
         wrap=stretch(ramp("2a2034", "3c3048", "54445e", "6c5c78", "8a7a96")),
         gem=VOID_GLOW, glow=VOID_GLOW, level=8),
    dict(id="stellarite", metal=stretch(ramp("2a3a64", "3b5083", "4c6893", "4f99d0", "85b2c3", "d8eef8")),
         wood=stretch(ramp("2a3050", "3b5083", "4a5270", "557e9f", "959da3")),
         wrap=stretch(ramp("e0d8c0", "f0e8d0", "c8c0a8", "a8a088", "807860")[::-1]),
         gem=stretch(ramp("1d1e24", "1f283e", "3a3a50", "7b6e71", "d8d0e8")), glow=STAR_GLOW, level=9),
]


def mats(T):
    m = {}
    if T.get("kind") == "stone":
        m["blade"] = Mat("blade", T["metal"], "stone", base=4, cracks=0.6, edges=False)
    else:
        m["blade"] = Mat("blade", T["metal"], "metal", base=4, polish=T["level"] >= 4, scratch_area=90, edges=False)
    m["metal"] = Mat("metal", T["metal"], "metal", base=3, scratch_area=60)
    m["dark"] = Mat("dark", T["metal"], "metal", base=2, scratch_area=60)
    m["trim"] = Mat("trim", T.get("trim", T["metal"]), "metal", base=4, bevel=True)
    m["wood"] = Mat("wood", T["wood"], "wood", base=3, grain_step=2)
    m["wrap"] = Mat("wrap", T["wrap"], "wrap", base=3, period=4)
    m["rope"] = Mat("rope", stretch(ramp("4a3820", "6a5432", "8c7448", "ae9460", "ccb27c")), "rope", base=3)
    if T["gem"]:
        m["gem"] = Mat("gem", T["gem"], "gem", base=3)
    if T.get("glow"):
        m["glow"] = Mat("glow", T["glow"], "glow", base=4)
    return m


def blade_decal(T, fuller=True):
    """Blades: a bright edge on both sides and a light fuller line down the middle (front and back)."""
    r = T["metal"]

    def d(area, f, w, h, c, rng):
        if f not in ("north", "south") or w < 3:
            return
        for y in range(h):
            put(area, 0, y, r[-1])
            put(area, w - 1, y, r[-1])
            if w >= 8:
                put(area, 1, y, r[-2])
                put(area, w - 2, y, r[-2])
        if fuller and w >= 6 and T.get("kind") != "stone":
            mid = w // 2
            for y in range(h):
                put(area, mid - 1, y, r[1])
                put(area, mid, y, r[-2])
                if w >= 10:
                    put(area, mid + 1, y, r[1])
    return d


def rune_decal(T):
    """Void and Stellarite: rune or star marks down the blade core."""
    g = T.get("glow")

    def d(area, f, w, h, c, rng):
        if f not in ("north", "south") or w < 4:
            return
        mid = w // 2
        for y in range(2, h - 2, 5):
            pat = [(0, 0), (0, 1), (-1, 1), (1, 1), (0, 2)] if T["id"] == "stellarite" else [(0, 0), (1, 1), (0, 2), (-1, 1)]
            for dx, dy in pat:
                put(area, mid + dx, y + dy, g[-1] if (dx, dy) == (0, 1) else g[-2])
    return d


def face_decal(T):
    """Dreadstone: a small demon face, painite eyes and teeth, on the front of the guard."""
    r, gem = T["metal"], T["gem"]

    def d(area, f, w, h, c, rng):
        if f not in ("north", "south") or w < 8 or h < 6:
            return
        cx, cy = w // 2, h // 2
        for x in (cx - 2, cx + 1):
            put(area, x, cy - 1, gem[-1])
            put(area, x + 1, cy - 1, gem[-2])
        for x in range(cx - 2, cx + 2):
            put(area, x, cy + 1, r[0])
        for x in (cx - 2, cx, cx + 1 if w % 2 else cx - 1):
            put(area, x, cy + 2 if cy + 2 < h else cy + 1, r[-1])
        put(area, cx - 3, cy - 2, r[0])
        put(area, cx + 2, cy - 2, r[0])
    return d


# ---------------------------------------------------------------- parts

def taper(m, g, name, y0, y1, w0, w1, thick, mat, segs, decal=None, shape=None, z=0.0):
    """A blade or point from stacked segments, w0 wide at y0 to w1 at y1. shape(t) can bend the
    width (leaf blades swell, knapped blades chip)."""
    out = []
    for i in range(segs):
        t0, t1 = i / segs, (i + 1) / segs
        wa = w0 + (w1 - w0) * (t0 + t1) / 2
        if shape:
            wa *= shape((t0 + t1) / 2, i)
        wa = max(0.5, round(wa * 4) / 4)
        th = max(0.5, thick * (1 - 0.35 * t0)) if thick > 0.75 else thick
        ya, yb = y0 + (y1 - y0) * t0, y0 + (y1 - y0) * t1
        out.append(m.cube(f"{name}_{i + 1}", (-wa / 2, ya, z - th / 2), (wa / 2, yb, z + th / 2), mat, g, decal=decal))
    return out


def tip(m, g, name, y, w, thick, mat, steps=3, decal=None):
    out = []
    for i in range(steps):
        ww = max(0.25, w * (steps - i) / (steps + 1))
        th = max(0.25, thick * 0.8)
        out.append(m.cube(f"{name}_{i + 1}", (-ww / 2, y + i * 0.75, -th / 2), (ww / 2, y + (i + 1) * 0.75, th / 2), mat, g,
                          decal=decal))
    return y + steps * 0.75


def grip(m, g, M, y0, y1, w=1.25, rings=True, T=None):
    m.cube("grip_box", (-w / 2, y0, -w / 2), (w / 2, y1, w / 2), M["wrap"], g)
    if rings:
        m.cube("grip_ring_top", (-w / 2 - 0.25, y1 - 0.5, -w / 2 - 0.25), (w / 2 + 0.25, y1, w / 2 + 0.25), M["trim"], g)
        m.cube("grip_ring_bottom", (-w / 2 - 0.25, y0, -w / 2 - 0.25), (w / 2 + 0.25, y0 + 0.5, w / 2 + 0.25), M["trim"], g)


def gem(m, g, M, name, c, s=1.0, depth=None, glow=False):
    if "gem" not in M:
        return None
    mat = M["glow"] if glow and "glow" in M else M["gem"]
    d = depth if depth is not None else s
    return m.box(name + ("_glow" if mat.kind == "glow" else ""), c, (s, s, d), mat, g)


def curl(m, g, name, base, side, mat, segs=3, size=0.75, start=20, step=35, up=True):
    """A curled guard end or horn: chained, rotated segments."""
    x, y = base
    ang = start
    out = []
    for i in range(segs):
        a = math.radians(ang)
        dx, dy = math.cos(a) * size * 1.1, math.sin(a) * size * 1.1 * (1 if up else -1)
        cx, cy = x + side * dx / 2, y + dy / 2
        s = size * (1 - 0.18 * i)
        out.append(m.cube(f"{name}_{i + 1}", (cx - s / 2, cy - s / 2, -s / 2), (cx + s / 2, cy + s / 2, s / 2), mat, g,
                          rotation=(0, 0, side * ang * (1 if up else -1)), origin=(cx, cy, 0)))
        x, y = x + side * dx, y + dy
        ang += step
    return out


def guard(m, g, T, M, y, width, thick=1.5, height=1.25):
    """Cross guard with tier ornaments."""
    L = T["level"]
    tid = T["id"]
    c = m.cube("guard_box", (-width / 2, y, -thick / 2), (width / 2, y + height, thick / 2), M["metal"], g,
               decal=face_decal(T) if tid == "dreadstone" else None)
    m.cube("guard_collar", (-0.875, y + height, -0.75), (0.875, y + height + 0.5, 0.75), M["trim"], g)
    if tid == "steel":       # angled tips
        for s in (1, -1):
            m.cube(f"guard_tip_{'right' if s > 0 else 'left'}", (s * width / 2 - 0.5, y - 0.75, -0.6),
                   (s * width / 2 + 0.5, y + 0.5, 0.6), M["metal"], g, rotation=(0, 0, s * 20),
                   origin=(s * width / 2, y, 0))
    if tid in ("gold", "stellarite"):
        for s in (1, -1):
            curl(m, g, f"guard_curl_{'right' if s > 0 else 'left'}", (s * width / 2, y + height / 2), s, M["trim"], segs=3,
                 size=0.9, start=10, step=45)
    if tid == "obsidian":
        for s in (1, -1):
            m.cube(f"guard_shard_{'right' if s > 0 else 'left'}", (s * width / 2 - 0.5, y, -0.5), (s * width / 2 + 0.5, y + 2.25, 0.5),
                   M["blade"], g, rotation=(0, 0, -s * 30), origin=(s * width / 2, y + 0.5, 0))
    if tid == "titanite":
        for s in (1, -1):
            for k, (dx, hh, a) in enumerate(((0.6, 2.0, 25), (1.6, 1.4, 45))):
                m.cube(f"guard_crystal_{'right' if s > 0 else 'left'}_{k + 1}", (s * (width / 2 - dx) - 0.4, y + height - 0.25, -0.4),
                       (s * (width / 2 - dx) + 0.4, y + height + hh, 0.4), M["gem"], g, rotation=(0, 0, -s * a),
                       origin=(s * (width / 2 - dx), y + height, 0))
    if tid == "dreadstone":
        for s in (1, -1):
            curl(m, g, f"guard_horn_{'right' if s > 0 else 'left'}", (s * width / 2, y + height), s, M["dark"], segs=4,
                 size=0.9, start=50, step=22)
    if tid == "void":
        for s in (1, -1):
            m.cube(f"guard_spike_{'right' if s > 0 else 'left'}", (s * width / 2 - 0.4, y + 0.25, -0.4), (s * width / 2 + 0.4, y + 2.5, 0.4),
                   M["dark"], g, rotation=(0, 0, -s * 40), origin=(s * width / 2, y + 0.5, 0))
            m.cube(f"guard_spike_low_{'right' if s > 0 else 'left'}", (s * width / 2 - 0.3, y - 1.75, -0.3), (s * width / 2 + 0.3, y + 0.25, 0.3),
                   M["dark"], g, rotation=(0, 0, s * 35), origin=(s * width / 2, y, 0))
    if L >= 4:
        gem(m, g, M, "guard_gem", (0, y + height / 2, -thick / 2 - 0.25), 1.0, 0.75, glow=L >= 8)
        gem(m, g, M, "guard_gem_back", (0, y + height / 2, thick / 2 + 0.25), 1.0, 0.75, glow=L >= 8)
    return c


def pommel(m, g, T, M, y):
    tid, L = T["id"], T["level"]
    if tid == "stone":
        m.cube("pommel_box", (-0.875, y - 1.25, -0.875), (0.875, y, 0.875), M["blade"], g)
        return y - 1.25
    if tid == "stellarite":       # floating star under a cap
        m.cube("pommel_cap", (-0.875, y - 0.75, -0.875), (0.875, y, 0.875), M["trim"], g)
        star(m, g, "pommel_star_glow", (0, y - 2.25, 0), 0.6, M["glow"])
        return y - 3
    s = 1.5 + 0.1 * L
    m.cube("pommel_box", (-s / 2, y - s, -s / 2), (s / 2, y, s / 2), M["trim"], g)
    if tid == "steel":
        m.cube("pommel_point", (-0.5, y - s - 0.75, -0.5), (0.5, y - s, 0.5), M["metal"], g)
    if L >= 4:
        gem(m, g, M, "pommel_gem", (0, y - s / 2, -s / 2 - 0.2), 0.75, 0.5, glow=L >= 8)
    return y - s


def star(m, g, name, c, s, mat):
    x, y, z = c
    m.box(name + "_core", (x, y, z), (s * 2, s * 2, s * 2), mat, g)
    m.box(name + "_up", (x, y + s * 1.6, z), (s, s * 1.2, s), mat, g)
    m.box(name + "_down", (x, y - s * 1.6, z), (s, s * 1.2, s), mat, g)
    m.box(name + "_right", (x + s * 1.6, y, z), (s * 1.2, s, s), mat, g)
    m.box(name + "_left", (x - s * 1.6, y, z), (s * 1.2, s, s), mat, g)


def fragments(m, g, M, y, n=3):
    mat = M["glow"]
    for i, (dx, dy, s, a) in enumerate(((1.8, 0, 0.75, 20), (-1.6, 2.2, 0.5, -35), (1.2, 4.0, 0.5, 45))[:n]):
        m.cube(f"fragment_{i + 1}_glow", (dx - s / 2, y + dy - s / 2, -s / 2), (dx + s / 2, y + dy + s / 2, s / 2), mat, g,
               rotation=(0, 0, a), origin=(dx, y + dy, 0))


def lashing(m, g, M, y, w=1.75, rows=3):
    for i in range(rows):
        m.cube(f"lashing_{i + 1}", (-w / 2, y + i * 0.5, -w / 2), (w / 2, y + i * 0.5 + 0.5, w / 2), M["rope"], g,
               rotation=(0, 0, 8 if i % 2 else -8), origin=(0, y + i * 0.5 + 0.25, 0))


# ---------------------------------------------------------------- blade shapes per tier

def blade_shape(T):
    tid = T["id"]
    if tid == "stone":
        return lambda t, i: 1.0 + (0.18 if i % 2 else -0.08)
    if tid == "bronze":
        return lambda t, i: 0.9 + 0.35 * math.sin(math.pi * min(1, t * 1.1))
    if tid == "gold":
        return lambda t, i: 1.1 - 0.15 * t
    if tid == "dreadstone":
        return lambda t, i: 1.0 + 0.2 * t
    return None


# ---------------------------------------------------------------- weapons

def sword(T, dagger=False):
    kind = "dagger" if dagger else "sword"
    m = Model(f"{T['id']}_{kind}", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 3.0 if not dagger else 2.0, 0))
    gl = 6 if not dagger else 4
    grip_g = m.group("grip", (0, gl / 2 + 1.5, 0), root)
    blade_g = m.group("blade", (0, gl + 2.5, 0), root)
    guard_g = m.group("guard", (0, gl + 1.5, 0), root)
    pommel_g = m.group("pommel", (0, 1.5, 0), root)
    y_grip0 = 1.5
    grip(m, grip_g, M, y_grip0, y_grip0 + gl - 0.5, 1.25 if not dagger else 1.0, rings=L >= 1)
    pommel(m, pommel_g, T, M, y_grip0)
    gy = y_grip0 + gl - 0.5
    gw = (7 + 0.4 * L) if not dagger else (4.5 + 0.2 * L)
    if tid == "stone":
        lashing(m, guard_g, M, gy, 2.0, 3)
        by = gy + 1.5
    else:
        guard(m, guard_g, T, M, gy, gw)
        by = gy + 1.75
    length = (12.5 + 0.35 * L) if not dagger else (5.5 + 0.15 * L)
    width = (2.75 + 0.1 * L) if not dagger else 2.0
    if tid == "gold":
        width += 0.5
    if tid == "steel" and not dagger:     # ricasso
        m.cube("ricasso", (-width / 2 + 0.25, by, -0.4), (width / 2 - 0.25, by + 1.25, 0.4), M["dark"], blade_g)
        by += 1.25
        length -= 1.25
    segs = 5 if not dagger else 3
    M["blade"] = M["blade"].variant("blade", grad_y=(by, by + length, 2.0))   # darker at the guard, lighter at the tip
    deco = blade_decal(T, fuller=not dagger)
    thick = 0.75 if tid != "titanite" else 1.0
    cubes = taper(m, blade_g, "blade", by, by + length, width, width * 0.7, thick, M["blade"], segs, deco, blade_shape(T))
    top = tip(m, blade_g, "blade_tip", by + length, width * 0.7, thick, M["blade"], 3 if not dagger else 2, deco)
    if tid == "titanite":       # raised facet ridge
        m.cube("blade_ridge", (-0.5, by, -0.75), (0.5, by + length, 0.75), M["metal"], blade_g)
    if tid == "obsidian":       # serrated teeth along both edges
        n = 4 if not dagger else 2
        for i in range(n):
            yy = by + 1 + i * (length - 2) / max(1, n - 1)
            wa = width * (1 - 0.3 * (yy - by) / length) / 2
            for s in (1, -1):
                m.cube(f"tooth_{'right' if s > 0 else 'left'}_{i + 1}", (s * wa - 0.35, yy, -0.25), (s * wa + 0.35, yy + 0.7, 0.25),
                       M["blade"], blade_g, rotation=(0, 0, s * 45), origin=(s * wa, yy + 0.35, 0))
    if tid == "dreadstone":     # backward barbs
        for i, frac in enumerate((0.35, 0.7)):
            yy = by + length * frac
            wa = width * (1 + 0.2 * frac) / 2
            for s in (1, -1):
                m.cube(f"barb_{'right' if s > 0 else 'left'}_{i + 1}", (s * wa - 0.4, yy - 1.4, -0.3), (s * wa + 0.4, yy, 0.3),
                       M["blade"], blade_g, rotation=(0, 0, -s * 35), origin=(s * wa, yy, 0))
    if tid in ("void", "stellarite"):
        g = M["glow"]
        for s in (1, -1):
            m.cube(f"blade_edge_{'right' if s > 0 else 'left'}_glow", (s * width * 0.27 - 0.25, by + 0.5, -0.45),
                   (s * width * 0.27 + 0.25, by + length * 0.92, 0.45), g, blade_g)
        cubes[len(cubes) // 2].decal = rune_decal(T)
        if tid == "void":
            fragments(m, blade_g, M, top + 0.75, 3 if not dagger else 2)
        else:
            star(m, blade_g, "tip_star_glow", (0, top + 1.25, 0), 0.4, g)
    if L >= 6 and tid not in ("void", "stellarite") and not dagger:
        cubes[0].decal = blade_decal(T)
    m.scale_dummy((10, 0, 0))
    return m


def battle_axe(T):
    m = Model(f"{T['id']}_battle_axe", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 4, 0))
    haft = m.group("haft", (0, 4, 0), root)
    head = m.group("head", (0, 16, 0), root)
    H = 19 + 0.3 * L
    m.cube("haft_box", (-0.625, 0.5, -0.625), (0.625, H, 0.625), M["wood"], haft)
    m.cube("grip_wrap", (-0.75, 1.5, -0.75), (0.75, 6.5, 0.75), M["wrap"], haft)
    m.cube("butt_cap", (-0.875, 0, -0.875), (0.875, 1.0, 0.875), M["trim"], haft)
    hy = H - 5.5
    m.cube("head_socket", (-1.25, hy, -1.0), (1.25, hy + 4.5, 1.0), M["metal"], head, decal=face_decal(T) if tid == "dreadstone" else None)
    if L >= 1:
        m.cube("socket_band_top", (-1.375, hy + 4.0, -1.125), (1.375, hy + 4.5, 1.125), M["trim"], head)
        m.cube("socket_band_low", (-1.375, hy, -1.125), (1.375, hy + 0.5, 1.125), M["trim"], head)
    # two bits: stepped crescents, bigger and more flared each tier
    reach = 4.5 + 0.25 * L
    tall = 5.0 + 0.35 * L
    sides = (1, -1) if tid != "stone" else (1,)
    for s in sides:
        nm = "right" if s > 0 else "left"
        steps = 4
        for i in range(steps):
            x0 = 1.25 + i * reach / steps
            x1 = 1.25 + (i + 1) * reach / steps
            hh = tall * (0.45 + 0.55 * (i + 1) / steps)
            if tid == "stone":
                hh *= 1.0 + (0.15 if i % 2 else 0)
            cy = hy + 2.25
            mat = M["blade"]
            xa, xb = sorted((s * x0, s * x1))
            dec = blade_decal(T, fuller=False) if i == steps - 1 else None
            m.cube(f"bit_{nm}_{i + 1}", (xa, cy - hh / 2, -0.4 + 0.05 * i), (xb, cy + hh / 2, 0.4 - 0.05 * i), mat, head, decal=dec)
        # bright edge
        ex = s * (1.25 + reach)
        if tid in ("void", "stellarite"):
            m.cube(f"bit_edge_{nm}_glow", (min(ex, ex + s * 0.5), hy + 2.25 - tall / 2, -0.3), (max(ex, ex + s * 0.5), hy + 2.25 + tall / 2, 0.3),
                   M["glow"], head)
        if tid in ("gold", "dreadstone", "titanite"):
            for k, a in enumerate((1, -1)):
                yb = hy + 2.25 + a * tall / 2
                m.cube(f"bit_horn_{nm}_{k + 1}", (ex - 0.4, yb - 0.4 if a > 0 else yb - 1.6, -0.3),
                       (ex + 0.4, yb + 1.6 if a > 0 else yb + 0.4, 0.3),
                       M["blade"] if tid != "titanite" else M["gem"], head, rotation=(0, 0, -s * a * 30), origin=(ex, yb, 0))
    if tid == "stone":
        lashing(m, head, M, hy - 0.5, 1.75, 3)
    # top spike
    if L >= 3:
        m.cube("top_spike", (-0.5, H, -0.5), (0.5, H + 2.0 + 0.2 * L, 0.5), M["metal"], head)
    if L >= 4:
        gem(m, head, M, "head_gem", (0, hy + 2.25, -1.2), 1.0, 0.5, glow=L >= 8)
    if tid == "void":
        fragments(m, head, M, H + 1, 2)
    if tid == "stellarite":
        star(m, head, "top_star_glow", (0, H + 4.5, 0), 0.5, M["glow"])
    m.scale_dummy((12, 0, 0))
    return m


def mace(T):
    m = Model(f"{T['id']}_mace", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 3, 0))
    haft = m.group("haft", (0, 3, 0), root)
    head = m.group("head", (0, 13, 0), root)
    H = 12 + 0.2 * L
    m.cube("haft_box", (-0.5, 0.75, -0.5), (0.5, H, 0.5), M["wood"] if L < 2 else M["dark"], haft)
    m.cube("grip_wrap", (-0.7, 1.0, -0.7), (0.7, 5.0, 0.7), M["wrap"], haft)
    m.cube("butt_knob", (-0.875, 0, -0.875), (0.875, 1.0, 0.875), M["trim"], haft)
    s = 3.0 + 0.15 * L
    hy = H
    if tid == "stone":
        m.cube("head_rock", (-1.75, hy - 0.5, -1.5), (1.75, hy + 3.25, 1.75), M["blade"], head)
        m.cube("head_rock_top", (-1.25, hy + 3.25, -1.0), (1.0, hy + 4.0, 1.25), M["blade"], head)
        m.cube("head_rock_side", (1.5, hy + 0.5, -1.0), (2.25, hy + 2.5, 1.0), M["blade"], head)
        lashing(m, head, M, hy - 1.5, 1.5, 2)
    else:
        m.cube("head_core", (-s / 2, hy, -s / 2), (s / 2, hy + s, s / 2), M["metal"], head)
        m.cube("head_collar", (-s / 2 + 0.5, hy - 0.75, -s / 2 + 0.5), (s / 2 - 0.5, hy, s / 2 - 0.5), M["trim"], head)
        if tid == "bronze":       # studs
            for i, (x, z) in enumerate(((1, 0), (-1, 0), (0, 1), (0, -1))):
                m.box(f"stud_{i + 1}", (x * (s / 2 + 0.25), hy + s / 2, z * (s / 2 + 0.25)), (0.75 if x else 1, 1, 0.75 if z else 1),
                      M["trim"], head)
        else:                     # flanges round the head
            n = 4 if L < 5 else 6
            for i in range(n):
                a = 360 * i / n
                fh = s + 0.5 + 0.1 * L
                fw = 1.25 + 0.1 * L
                ox = math.cos(math.radians(a)) * (s / 2 + fw / 2 - 0.25)
                oz = math.sin(math.radians(a)) * (s / 2 + fw / 2 - 0.25)
                m.cube(f"flange_{i + 1}", (ox - fw / 2, hy + s / 2 - fh / 2, oz - 0.3), (ox + fw / 2, hy + s / 2 + fh / 2, oz + 0.3),
                       M["blade"], head, rotation=(0, -a, 0), origin=(ox, hy + s / 2, oz))
        if L >= 3:
            m.cube("top_spike", (-0.5, hy + s, -0.5), (0.5, hy + s + 1.75 + 0.15 * L, 0.5), M["blade"], head)
        if L >= 4:
            gem(m, head, M, "head_gem", (0, hy + s / 2, -s / 2 - 0.2), 1.0, 0.5, glow=L >= 8)
        if tid == "dreadstone":
            for sd in (1, -1):
                curl(m, head, f"horn_{'right' if sd > 0 else 'left'}", (sd * s / 2, hy + s), sd, M["dark"], 3, 0.8, 60, 25)
        if tid == "void":
            fragments(m, head, M, hy + s + 1.5, 3)
        if tid == "stellarite":
            star(m, head, "top_star_glow", (0, hy + s + 4.5, 0), 0.5, M["glow"])
    m.scale_dummy((10, 0, 0))
    return m


def spear(T):
    m = Model(f"{T['id']}_spear", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 12, 0))
    shaft = m.group("shaft", (0, 12, 0), root)
    head = m.group("head", (0, 30, 0), root)
    H = 30 + 0.4 * L
    m.cube("shaft_box", (-0.5, 1.0, -0.5), (0.5, H, 0.5), M["wood"], shaft)
    m.cube("grip_wrap", (-0.625, 10, -0.625), (0.625, 15, 0.625), M["wrap"], shaft)
    m.cube("butt_spike", (-0.625, 0, -0.625), (0.625, 1.25, 0.625), M["trim"], shaft)
    if tid == "stone":
        lashing(m, head, M, H - 1, 1.25, 3)
    else:
        m.cube("socket", (-0.75, H - 1.5, -0.75), (0.75, H + 0.5, 0.75), M["trim"], head)
    by = H + 0.5
    length = 6 + 0.25 * L
    width = 2.25 + 0.1 * L
    deco = blade_decal(T, fuller=False)
    shape = (lambda t, i: 0.6 + 0.6 * math.sin(math.pi * min(1, 0.25 + t))) if tid != "stone" else blade_shape(T)
    taper(m, head, "blade", by, by + length, width, width * 0.6, 0.75, M["blade"], 4, deco, shape)
    tip(m, head, "blade_tip", by + length, width * 0.5, 0.75, M["blade"], 3, deco)
    if tid in ("gold", "titanite", "dreadstone", "stellarite"):   # side wings / prongs
        for s in (1, -1):
            mat = M["gem"] if tid == "titanite" else M["blade"]
            m.cube(f"wing_{'right' if s > 0 else 'left'}", (s * 1.0 - 0.4, by - 0.5, -0.3), (s * 1.0 + 0.4, by + 2.5, 0.3), mat, head,
                   rotation=(0, 0, -s * (40 if tid != "dreadstone" else 60)), origin=(s * 0.75, by - 0.5, 0))
    if L >= 4:
        gem(m, head, M, "socket_gem", (0, H - 0.5, -0.9), 0.75, 0.4, glow=L >= 8)
    if tid in ("void", "stellarite"):
        m.cube("blade_core_glow", (-0.25, by + 0.5, -0.45), (0.25, by + length - 0.5, 0.45), M["glow"], head)
    if tid == "void":
        fragments(m, head, M, by + length + 1.5, 2)
    if tid == "stellarite":
        star(m, head, "tip_star_glow", (0, by + length + 4.0, 0), 0.4, M["glow"])
    if L >= 1:
        # pennant ribbon below the head for gold and up, a binding ring for the rest
        m.cube("binding", (-0.625, H - 3.0, -0.625), (0.625, H - 2.25, 0.625), M["trim"], shaft)
    m.scale_dummy((10, 0, 0))
    return m


def staff(T):
    m = Model(f"{T['id']}_staff", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 10, 0))
    shaft = m.group("shaft", (0, 10, 0), root)
    top = m.group("top", (0, 24, 0), root)
    H = 22 + 0.3 * L
    # slightly crooked shaft from three offset pieces
    m.cube("shaft_low", (-0.6, 0.5, -0.6), (0.6, H * 0.4, 0.6), M["wood"], shaft)
    m.cube("shaft_mid", (-0.55, H * 0.4, -0.55), (0.55, H * 0.75, 0.55), M["wood"], shaft, rotation=(0, 0, 3), origin=(0, H * 0.4, 0))
    m.cube("shaft_high", (-0.6, H * 0.75 - 0.2, -0.6), (0.6, H, 0.6), M["wood"], shaft)
    m.cube("foot_cap", (-0.75, 0, -0.75), (0.75, 1.0, 0.75), M["trim"], shaft)
    m.cube("grip_wrap", (-0.75, H * 0.45, -0.75), (0.75, H * 0.45 + 3.5, 0.75), M["wrap"], shaft)
    # carved top: prongs (claws) holding the orb
    oy = H + 2.25
    orb_s = 2.0 + 0.1 * L
    m.cube("top_collar", (-1.0, H - 0.5, -1.0), (1.0, H + 0.5, 1.0), M["trim"] if L else M["wood"], top)
    for i in range(4):
        a = 90 * i + 45
        ox, oz = math.cos(math.radians(a)) * (orb_s / 2 + 0.55), math.sin(math.radians(a)) * (orb_s / 2 + 0.55)
        # claws rise round the orb and lean in over it
        m.cube(f"claw_{i + 1}", (ox - 0.3, H + 0.25, oz - 0.3), (ox + 0.3, oy + orb_s / 2 + 0.25, oz + 0.3), M["trim"] if L else M["wood"], top,
               rotation=(math.sin(math.radians(a)) * 10, 0, -math.cos(math.radians(a)) * 10), origin=(ox, H + 0.25, oz))
    if tid == "stone":
        m.box("orb_stone", (0, oy, 0), (orb_s, orb_s, orb_s), M["blade"], top)
    else:
        mat = M["glow"] if "glow" in M else (M["gem"] if "gem" in M else Mat("orb", from_base("#7ab0d8"), "gem", base=3))
        nm = "orb_glow" if mat.kind == "glow" else "orb"
        if mat.kind != "glow" and L >= 1 and "gem" not in M:
            mat = Mat("orb", T["metal"], "gem", base=4)
        m.box(nm, (0, oy, 0), (orb_s, orb_s, orb_s), mat, top)
        m.box(nm + "_inner", (0, oy, 0), (orb_s + 0.5, orb_s - 0.75, orb_s - 0.75), mat, top)
    if tid == "dreadstone":
        for s in (1, -1):
            curl(m, top, f"horn_{'right' if s > 0 else 'left'}", (s * 1.0, H + 0.5), s, M["dark"], 4, 0.8, 70, 20)
    if tid == "void":
        fragments(m, top, M, oy + 1.0, 3)
    if tid == "stellarite":
        star(m, top, "crown_star_glow", (0, oy + 3.5, 0), 0.45, M["glow"])
    if tid in ("gold", "titanite"):
        for s in (1, -1):
            m.cube(f"wing_{'right' if s > 0 else 'left'}", (s * 1.2 - 0.3, H - 1.5, -0.3), (s * 1.2 + 0.3, H + 1.5, 0.3),
                   M["trim"] if tid == "gold" else M["gem"], top, rotation=(0, 0, -s * 30), origin=(s * 1.0, H - 1.5, 0))
    m.scale_dummy((10, 0, 0))
    return m


def shield(T):
    m = Model(f"{T['id']}_shield", ppu=PPU, ground=False)
    M = mats(T)
    L, tid = T["level"], T["id"]
    root = m.group(m.name, (0, 8, 0))
    W = 13 + 0.3 * L
    H = 15 + 0.3 * L
    plate_g = m.group("plate", (0, H / 2, 0), root)
    if L <= 1:
        planks = Mat("planks", T["wood"], "plank", base=3, plank=2.5, grain_dir="v")
        face = planks
    else:
        face = M["metal"].variant("face", kind="metal", base=3, noise=0.05, scratch_area=160, polish=L >= 4)
    # body: centre plate plus stepped shoulders to round the outline (heater shape for higher tiers)
    m.cube("plate_main", (-W / 2 + 1, 2.5, -0.5), (W / 2 - 1, H, 0.5), face, plate_g)
    m.cube("plate_right", (W / 2 - 1, 4.5, -0.5), (W / 2, H - 0.75, 0.5), face, plate_g)
    m.cube("plate_left", (-W / 2, 4.5, -0.5), (-W / 2 + 1, H - 0.75, 0.5), face, plate_g)
    m.cube("plate_low", (-W / 2 + 2.5, 0.75, -0.5), (W / 2 - 2.5, 2.5, 0.5), face, plate_g)
    m.cube("plate_point", (-1.5, 0, -0.5), (1.5, 0.75, 0.5), face, plate_g)
    # rim (front)
    rim = M["trim"]
    m.cube("rim_top", (-W / 2, H, -0.75), (W / 2, H + 0.75, 0.75), rim, plate_g)
    m.cube("rim_right", (W / 2, 4.0, -0.75), (W / 2 + 0.75, H + 0.75, 0.75), rim, plate_g)
    m.cube("rim_left", (-W / 2 - 0.75, 4.0, -0.75), (-W / 2, H + 0.75, 0.75), rim, plate_g)
    # boss and emblem on the front (north, -z)
    bs = 3 + 0.1 * L
    cy = H * 0.58
    m.cube("boss", (-bs / 2, cy - bs / 2, -1.25), (bs / 2, cy + bs / 2, -0.5), M["trim"] if L <= 1 else M["dark"], plate_g)
    if L >= 4:
        gem(m, plate_g, M, "boss_gem", (0, cy, -1.5), 1.25, 0.5, glow=L >= 8)
    elif L >= 1:
        m.cube("boss_cap", (-0.75, cy - 0.75, -1.75), (0.75, cy + 0.75, -1.25), M["metal"], plate_g)
    if L >= 2:   # cross bands
        m.cube("band_v", (-0.5, 1.0, -0.75), (0.5, H, -0.5), rim, plate_g)
        m.cube("band_h", (-W / 2 + 0.5, cy - 0.5, -0.75), (W / 2 - 0.5, cy + 0.5, -0.5), rim, plate_g)
    if tid == "dreadstone":
        for s in (1, -1):
            curl(m, plate_g, f"horn_{'right' if s > 0 else 'left'}", (s * (W / 2), H), s, M["dark"], 4, 1.0, 60, 22)
    if tid == "titanite":
        for i, x in enumerate((-W / 4, 0, W / 4)):
            m.cube(f"crystal_{i + 1}", (x - 0.5, H + 0.5, -0.5), (x + 0.5, H + 2.5 + (i == 1), 0.5), M["gem"], plate_g,
                   rotation=(0, 0, (i - 1) * -20), origin=(x, H + 0.5, 0))
    if tid == "gold":
        for i, x in enumerate((-W / 4, 0, W / 4)):
            m.cube(f"crown_{i + 1}", (x - 0.5, H + 0.5, -0.5), (x + 0.5, H + 1.75 + 0.75 * (i == 1), 0.5), rim, plate_g)
    if tid in ("void", "stellarite"):
        m.cube("rim_top_glow", (-W / 2 + 1, H + 0.75, -0.4), (W / 2 - 1, H + 1.0, 0.4), M["glow"], plate_g)
        if tid == "stellarite":
            star(m, plate_g, "emblem_star_glow", (0, cy, -2.0), 0.5, M["glow"])
        else:
            fragments(m, plate_g, M, H + 1.5, 2)
    # handle at the back
    m.cube("handle", (-0.5, cy - 2.5, 0.5), (0.5, cy + 2.5, 1.75), M["wrap"], plate_g)
    m.cube("strap", (-W / 2 + 2, cy + 1.5, 0.5), (W / 2 - 2, cy + 2.25, 0.9), Mat("strap", LEATHER, "leather", base=3), plate_g)
    m.scale_dummy((14, 0, 0))
    return m


KINDS = {"sword": sword, "dagger": lambda T: sword(T, dagger=True), "battle_axe": battle_axe, "mace": mace,
         "spear": spear, "staff": staff, "shield": shield}


def main():
    kinds = sys.argv[1:] or list(KINDS)
    for k in kinds:
        paths = []
        for T in TIERS:
            m = KINDS[k](T)
            p, n, size = m.save(OUT, TEX)
            paths.append(p)
            print(f"{os.path.basename(p)}: {n} cubes, texture {size}")
        lineup = OUT / f"{k}s_lineup.bbmodel"
        spacing = {"sword": 12, "dagger": 8, "battle_axe": 16, "mace": 10, "spear": 9, "staff": 9, "shield": 20}[k]
        subprocess.run([sys.executable, str(HERE.parent / "make_lineup.py"), str(lineup), str(spacing), "5", *paths], check=True)


if __name__ == "__main__":
    main()
