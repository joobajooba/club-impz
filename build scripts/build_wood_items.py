"""Lumbering item models (J00BA, 2026-11-15): the inventory items that are still sprites, as Blockbench models.
Every wood type: a log for each of the 17 woods and a tied plank bundle for the 10 that have planks; colours
sampled from each wood's sprite (godot-game/sprites/items/log_<wood>.png, plank_<wood>.png), or for the trees that
only drop a log, from their bark colour (scripts/world/lumbering.gd). Built with stall_lib (house style: centre light, darker edges, grain on top), 2 px per unit.
Usage: py build_wood_items.py [name ...]   writes C:/Users/lucas/blockbench_models/items/<name>.bbmodel + .png"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from stall_lib import Stall, R, F, px, LO, grid
from foliage_lib import ramp
from house_lib import C

OUT = r"C:\Users\lucas\blockbench_models\items"
R.update({
    "pine_bark": ramp("#3a1c12 #5c3020 #7e4630 #a05e40 #c07a56 #d6966e #e8b48a"),     # log_pine.png bark
    "pine_end": ramp("#6a4a26 #8a6a3a #ae8a50 #c6a466 #d8b878 #e2c286 #f0dcac"),      # log_pine.png cut end
    "twine": ramp("#24160c #382414 #4e341e #664428 #7e5634 #966a42 #ae8256"),          # tied twine, darker than the wood so it reads
    "pine_wood": ramp("#4e3a1e #6e5430 #8a6a3a #ae8a50 #cca66a #e2c286 #f4dca6"),     # plank_pine.png
})


def twine_paint(self, w, h, cat):
    """Twisted twine: diagonal strands, lighter on top, darker in the twist grooves."""
    yy, xx = grid(w, h)
    v = 3.6 + LO[cat] + 0.7 * (((xx + yy) % 3) == 0) - 0.6 * (((xx + yy) % 3) == 2) + self.noise(w, h, 0.06)
    return C(R["twine"], v), np.ones((h, w), bool)


import stall_lib
stall_lib.StallPainter.twine = twine_paint


SPRITES = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "godot-game", "sprites", "items")
# the woods with log and plank items (GameData._TREES) and the trees that only drop a log (Lumbering.TREES: their
# sprite is the oak log recoloured, so the bark comes from the tree's bark colour)
TABLE = ["ash", "birch", "oak", "pine", "goldleaf", "ebony", "silverbark", "bloodwood", "voidwood", "starwood"]
LOG_ONLY = {"maple": "#9a4e2c", "hickory": "#7a6248", "frostbark": "#a8c8e0", "titanwood": "#6c7280", "runewood": "#5a3c8c",
            "gembark": "#2c9c84", "worldbark": "#4a3424"}


def _hx(c): return np.array([int(c[i:i + 2], 16) for i in (1, 3, 5)], float)
def _hex(v): return "#%02x%02x%02x" % tuple(int(round(x)) for x in np.clip(v, 0, 255))
def _lum(c): return float(np.asarray(c) @ [0.3, 0.59, 0.11])


def _ramp_from(px_):
    """7 shades, dark to light, from a sprite's pixels (outline dropped), forced to step up in brightness."""
    px_ = px_[(px_ @ [0.3, 0.59, 0.11]) > 38]
    px_ = px_[np.argsort(px_ @ [0.3, 0.59, 0.11])]
    out = [px_[int(q * (len(px_) - 1))] for q in (0.04, 0.18, 0.34, 0.5, 0.66, 0.82, 0.96)]
    for k in range(1, 7):                                           # no flat steps: nudge each shade above the last
        if _lum(out[k]) < _lum(out[k - 1]) + 6:
            out[k] = np.minimum(out[k - 1] * 1.08 + 6, 255)
    return ramp(" ".join(_hex(c) for c in out))


def _ramp_from_colour(c):
    """7 hue shifted shades round one colour: deeper and more saturated in the shadows, paler in the light."""
    c = _hx(c); grey = np.full(3, c.mean())
    shades = []
    for t in (0.32, 0.48, 0.64, 0.82, 1.0, 1.16, 1.32):
        v = c * t if t <= 1 else c + (255 - c) * (t - 1) * 0.9
        if t < 1:
            v = v + (v - grey * t) * 0.25                          # shadows a little more saturated
        shades.append(v)
    return ramp(" ".join(_hex(v) for v in shades))


def _sprite_px(name, region=None):
    from PIL import Image
    a = np.array(Image.open(os.path.join(SPRITES, name + ".png")).convert("RGBA")).astype(float)
    m = a[..., 3] > 200
    if region is not None:
        m &= region(a.shape[0], a.shape[1])
    return a[m][:, :3]


def _end_region(h, w):
    yy, xx = np.mgrid[0:h, 0:w]
    return (xx < w * 0.42) & (yy > h * 0.52)                        # the log sprites show the cut end lower left


RAMP_CACHE = os.path.join(os.path.dirname(os.path.abspath(__file__)), "wood_ramps.json")


def wood_ramps(wood):
    """The wood's ramps, sampled once from the original sprites and kept in wood_ramps.json: the sprites are then
    replaced by renders of these models, so sampling them again would feed the models their own output."""
    import json
    cache = json.load(open(RAMP_CACHE)) if os.path.exists(RAMP_CACHE) else {}
    if wood not in cache:
        cache[wood] = [None if r is None else [list(map(int, c)) for c in r] for r in _sample_ramps(wood)]
        json.dump(cache, open(RAMP_CACHE, "w"), indent=1)
    return tuple(None if r is None else [np.array(c, float) for c in r] for r in cache[wood])


def _sample_ramps(wood):
    """(bark, end, plank) ramps: pine keeps its hand-set ramps; the table woods sample their sprites; the log-only
    woods build the bark from the tree's bark colour and tint a pale end grain toward it."""
    if wood == "pine":
        return R["pine_bark"], R["pine_end"], R["pine_wood"]
    if wood in LOG_ONLY:
        bark = _ramp_from_colour(LOG_ONLY[wood])
        end = ramp(" ".join(_hex(_hx(c) * 0.8 + _hx(LOG_ONLY[wood]) * 0.2) for c in
                            "#6a4a26 #8a6a3a #ae8a50 #c6a466 #d8b878 #e2c286 #f0dcac".split()))
        return bark, end, None
    bark = _ramp_from(_sprite_px("log_" + wood, lambda h, w: ~_end_region(h, w)))
    end = _ramp_from(_sprite_px("log_" + wood, _end_region))
    plank = _ramp_from(_sprite_px("plank_" + wood))
    return bark, end, plank


def ring(H, w, h, bark, end):
    """A round cut log end (hard alpha disk): growth rings round an off-centre heart, a crack, the bark rim."""
    yy, xx = grid(w, h); r = np.hypot(xx + 0.5 - w * 0.48, yy + 0.5 - h * 0.52) / (min(w, h) / 2)
    v = 5.0 - r * 1.2 - 1.3 * (np.sin(r * 10) > 0.45) - 1.2 * (r < 0.12) + H.P.noise(w, h, 0.08)
    rgb = C(end, v)
    rim = r > 0.8
    rgb[rim] = C(bark, 2.4 + 0.6 * (1 - r[rim]))
    rgb[(np.abs(xx + 0.5 - w * 0.48) < 0.6) & (yy + 0.5 > h * 0.55) & (r < 0.8)] = end[1]   # a radial crack
    return rgb, r <= 1.0


def make_log(wood, seed):
    """A chunky log lying along x: an octagonal trunk of two crossed boxes, round cut ends with rings, a snapped-off
    branch stub and a strip of loose bark."""
    bark, end, _ = wood_ramps(wood)
    H = Stall(f"{wood}_log", seed, tex=128, mats={"bark": {"kind": "flat", "ramp": bark, "side": (8, 8), "top": (8, 8), "no_lit2": True}})
    g = H.group("log", [0, 0, 0])
    L, D = 10, 4                                      # half length, radius
    side = lambda W, Hh, c: H.P.log_side(bark, W, Hh, c)
    H.item("log_body_a", g, [-L, 0, -D + 1.5], [L, 2 * D, D - 1.5], "bark_a", side, hide=("east", "west"))
    H.item("log_body_b", g, [-L + 0.5, 1.5, -D], [L - 0.5, 2 * D - 1.5, D], "bark_b", side, hide=("east", "west"))
    ek = H.rect("log_end", px(2 * D), px(2 * D), lambda W, Hh: ring(H, W, Hh, bark, end))
    for s_, x in (("east", L + 0.05), ("west", -L - 0.05)):
        H.card(f"log_end_{s_}", g, [x, 0, -D], [x, 2 * D, D], ek, faces=("east", "west"))
    H.item("branch_stub", g, [2, 2 * D - 1, -1], [4, 2 * D + 2.5, 1], "stub", side, rot=(0, 0, -22.5), origin=[3, 2 * D - 1, 0])
    H.item("bark_flake", g, [-6, 2 * D - 0.5, -2.5], [-2, 2 * D, 0.5], "flake", side, rot=(0, 11.25, 0), origin=[-4, 2 * D, -1])
    return H


def make_plank(wood, seed):
    """A bundle of four planks stacked on each other, each a little offset so the boards read, tied with twine near
    both ends: a band round the stack, a knot on top and two loose ends (J00BA, 2026-11-15)."""
    _, _, wood_r = wood_ramps(wood)
    H = Stall(f"{wood}_plank", seed, tex=128, mats={"wood": {"kind": "boards", "ramp": wood_r, "side": (40, 8), "top": (40, 12),
                                            "no_lit2": True, "extra": {"bw": 6, "nails": False, "shadow_top": False}}})
    g = H.group("planks", [0, 0, 0])
    for k, dx in enumerate((0, 0.5, -0.5, 0.5)):                 # four boards, 2 thick, nudged so the seams show
        H.box(f"plank_{k + 1}", g, [-9 + dx, 2 * k, -2.5], [9 + dx, 2 * k + 2, 2.5], "wood", ("down",) if k == 0 else (), f"p{k}")
    twine = lambda W, Hh, c: H.P.twine(W, Hh, c)
    for s_, x in (("left", -6), ("right", 6)):
        tg = H.group(f"twine_{s_}", [x, 0, 0], g)
        H.item(f"twine_{s_}_band", tg, [x - 0.5, 0, -3], [x + 0.5, 8.5, 3], "twine_band", twine, hide=("down",))
        H.item(f"twine_{s_}_knot", tg, [x - 1, 8.5, -1], [x + 1, 9.5, 1], "twine_knot", twine, hide=("down",))
        for e, rz in (("a", 30), ("b", -30)):
            H.item(f"twine_{s_}_end_{e}", tg, [x - 0.25, 8.5, -0.25], [x + 0.25, 11, 0.25], "twine_end", twine, hide=(),
                   rot=(rz / 2, 0, rz), origin=[x, 9, 0])
    return H


BUILDERS = {}
for n, w in enumerate(TABLE + list(LOG_ONLY)):
    BUILDERS[f"{w}_log"] = (lambda w=w, n=n: make_log(w, 4100 + n))
for n, w in enumerate(TABLE):
    BUILDERS[f"{w}_plank"] = (lambda w=w, n=n: make_plank(w, 4200 + n))

if __name__ == "__main__":
    for n in sys.argv[1:] or list(BUILDERS):
        BUILDERS[n]().finish([OUT])
