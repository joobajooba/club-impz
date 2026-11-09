"""Workshop props for the hub crafters' yard (J00BA, 2026-11-09: "add more detail to the crafting stations, make
each one its own small area, make blockbench decoration if required"). Each station gets a plot with a lean-to
shelter, a fence, a trade sign and the props of its trade.

  workshop_shelter_timber   lean-to: walnut posts, plank back wall with battens, wooden shake roof, hanging lantern
  workshop_shelter_forge    lean-to: rubble stone back wall with quoins, slate roof, iron lantern
  workshop_shelter_apothecary  lean-to: plaster back wall with timber framing, teal scale roof, lantern
  fence_rail, fence_rail_short, fence_post   post-and-rail fence 2 m and 1.1875 m long (post on the west end,
                            exact post-to-end pitch) and a lone end post
  log_pile                  stacked logs between stakes, chopping block with an axe, chips
  lumber_stack              sawn planks in layers on bearers with stickers
  coal_ore_bins             two plank bins of coal and ore, a shovel, a lump or two on the ground
  tool_rack                 smith's rack: hammers, tongs, a sword, an axe, horseshoes
  quench_trough             stone trough of water, bucket, ladle
  crate_stack               crates, sacks, a barrel, a coil of rope
  tannery_vats              two tanning vats, a stack of folded hides, a scraping beam with a hide over it
  potion_shelf              tall shelf of glowing bottles, jars, books and a candle
  herb_bed                  raised bed of herbs and flowers with a watering can
  sign_<trade>              signpost with a hanging board: smelter (flame), blacksmith (anvil), carpenter (saw),
                            sawyer (logs), tanner (hide), herbalist (leaf), brewer (potion)
House style (deco_lib / station_lib), 2 px per unit, front = north (-z). Lantern groups are named light_N.
Usage: py build_workshop_props.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from deco_lib import Deco, deco_mats, R, F, px, h2, C
from stall_lib import ICONS, _disk, _shade, grid
from build_stalls import barrel, hang_sign, tag
import build_town_decor as TD
import plant_paint as PP

OUT = r"C:\Users\lucas\blockbench_models\props\workshop"
TEX = [256]


def M(kind, rm, side=(48, 32), top=(32, 32), **extra):
    d = {"kind": kind, "ramp": R[rm], "side": side, "top": top, "no_lit2": True}
    if extra: d["extra"] = extra
    return d


def mats(extra=None):
    d = deco_mats({
        "beam": M("boards", "walnut", (64, 8), (48, 8), bw=3, nails=False, shadow_top=False),      # long along x
        "beam_z": M("boards", "walnut", (64, 8), (8, 64), bw=3, nails=False, shadow_top=False),    # rafters, side beams
        "beam_v": M("boards", "walnut", (8, 64), (8, 8), orient="v", bw=3, nails=False, shadow_top=False),  # studs, braces
        "wood": M("boards", "oak", (48, 16), (48, 16), bw=2, shadow_top=False),
        "pine": M("boards", "pine_wood", (64, 16), (48, 16), bw=2, shadow_top=False),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
        "rubble": M("cobble", "cobble", (64, 48), (32, 16)),
    })
    d.update(extra or {})
    return d


def new(name, seed, extra=None):
    return Deco(name, seed, mats(extra), tex=TEX[0])


def fin(H):
    H.finish([OUT]); return H


# ---------------------------------------------------------------- sign icons (procedural pixel art, house style)
def icon_flame(w, h):
    yy, xx = grid(w, h); cx = w / 2
    t = (yy + 0.5) / h
    half = (w * 0.42) * np.clip(np.sin(np.clip(t, 0, 1) * math.pi * 0.7), 0, 1)
    sway = np.sin(t * 5) * w * 0.06
    d = np.abs(xx + 0.5 - cx - sway)
    m = d <= half
    core = 1 - d / np.maximum(half, 0.5)
    col = C(R["glow"], 1.6 + core * 3.5 + t * 1.0)
    base = m & (t > 0.86); col[base] = C(R["coal"], np.full((h, w), 3.0))[base]
    return m, col


def icon_anvil(w, h):
    yy, xx = grid(w, h)
    face = (yy > h * 0.22) & (yy < h * 0.42) & (xx > w * 0.18) & (xx < w * 0.9)
    horn = (yy > h * 0.24) & (yy < h * 0.24 + (xx - w * 0.02) / (w * 0.18) * h * 0.16) & (xx >= w * 0.02) & (xx <= w * 0.2)
    waist = (yy >= h * 0.42) & (yy < h * 0.66) & (xx > w * 0.36) & (xx < w * 0.7)
    foot = (yy >= h * 0.66) & (yy < h * 0.82) & (xx > w * 0.22) & (xx < w * 0.84)
    m = face | horn | waist | foot
    col = C(R["steel"], 3.4 + 1.6 * (1 - (yy + 0.5) / h) - 0.3 * ((xx + 0.5) / w))
    col[face & (yy < h * 0.27)] = R["steel"][6]
    return m, col


def icon_saw(w, h):
    yy, xx = grid(w, h)
    blade = (yy > h * 0.3) & (yy < h * 0.62) & (xx > w * 0.08) & (xx < w * 0.74)
    blade &= ~((yy > h * 0.3) & (yy < h * 0.3 + (w * 0.74 - xx) * 0.0))
    teeth = (yy >= h * 0.62) & (yy < h * 0.7) & (xx > w * 0.08) & (xx < w * 0.74) & (xx % 2 == 0)
    handle = (yy > h * 0.22) & (yy < h * 0.74) & (xx >= w * 0.74) & (xx < w * 0.95)
    hole = (yy > h * 0.36) & (yy < h * 0.56) & (xx >= w * 0.8) & (xx < w * 0.88)
    m = blade | teeth | (handle & ~hole)
    col = C(R["steel"], 4.6 - (yy + 0.5) / h * 1.6)
    col[handle] = C(R["oak"], np.full((h, w), 4.0))[handle]
    return m, col


def icon_logs(w, h):
    m = np.zeros((h, w), bool); col = np.zeros((h, w, 3), np.uint8)
    yy, xx = grid(w, h)
    r = min(w, h) * 0.2
    for cx, cy in ((w * 0.3, h * 0.66), (w * 0.7, h * 0.66), (w * 0.5, h * 0.3)):
        d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
        mm = d <= r
        c = C(R["logend"], 4.4 - d / r * 1.5 + 0.6 * (np.sin(d * 2.4) > 0.3))
        c[mm & (d > r - 0.9)] = R["bark"][2]
        col[mm] = c[mm]; m |= mm
    return m, col


def icon_hide(w, h):
    yy, xx = grid(w, h)
    u = (xx + 0.5) / w - 0.5; t = (yy + 0.5) / h - 0.5
    body = (np.abs(u) / 0.3) ** 2 + (np.abs(t) / 0.36) ** 2 <= 1
    legs = (np.abs(np.abs(u) - 0.32) < 0.09) & (np.abs(np.abs(t) - 0.28) < 0.12)
    neck = (np.abs(u) < 0.1) & (t < -0.28) & (t > -0.46)
    m = body | legs | neck
    col = C(R["hide"], 4.2 - np.hypot(u * 2, t * 2) * 1.6)
    return m, col


def icon_leaf(w, h):
    yy, xx = grid(w, h); cx = w / 2
    t = 1 - (yy + 0.5) / h
    half = (w * 0.36) * np.sin(np.clip(t, 0, 1) * math.pi) ** 0.8
    d = xx + 0.5 - cx - (t - 0.5) * w * 0.15
    m = (np.abs(d) <= half) & (t > 0.06)
    col = C(R["box_leaf"], 3.2 + 2.2 * t + np.where(d < 0, 0.6, -0.2))
    rib = m & (np.abs(d) < 0.6); col[rib] = R["box_leaf"][2]
    stem = (np.abs(xx + 0.5 - cx + w * 0.07) < 0.6) & (t <= 0.08)
    col[stem] = R["oak"][2]
    return m | stem, col


ICONS.update({"flame": icon_flame, "anvil": icon_anvil, "saw": icon_saw, "logs": icon_logs, "hide": icon_hide, "leaf": icon_leaf})


# ---------------------------------------------------------------- shared bits
def plank_box(H, name, grp, frm, to, tag_="plankbox", wood="pine_wood", hide=("down",)):
    return H.item(name, grp, frm, to, f"{tag_}_{wood}", lambda W, Hh, c: H.P.boards(R[wood], W, Hh, 0.2 if c != "down" else -1,
                  orient="h" if W >= Hh else "v", bw=2, nails=True, shadow_top=False) if c not in ("up",) else
                  H.P.boards(R[wood], W, Hh, 0.6, orient="h", bw=2, nails=False, shadow_top=False), hide)


def light_lantern(H, grp, x, y, z, chain=3.0):
    """Hanging lantern (glass *_glow) inside a light_N group, so the town gives it an OmniLight at night."""
    H.n_light += 1
    lg = H.group(f"light_{H.n_light}", [x, y - chain - 2.5, z], grp)
    H.lantern_hang("lantern", lg, x, y, z, chain)


def roof_slab(H, name, grp, x1, x2, y0, z0, L, ang, t, top_key, under_key, edge_mat):
    """Stall.slab toward the north, but the edge material is only cropped for the four edges (Stall.slab crops it
    for the top and bottom too, which grows that swatch to the whole roof size for nothing)."""
    frm, to = [x1, y0 - t, z0 - L], [x2, y0, z0]
    fs = H.faces(frm, to, edge_mat, ("south", "up", "down"), f"{name}e")
    fs["up"] = F(top_key); fs["down"] = F(under_key)
    H.m.cube(name, grp, frm, to, fs, (-abs(ang), 0, 0), [(x1 + x2) / 2, y0, z0])


def shake_mat():
    return {"kind": "shingle", "ramp": R["walnut"], "side": (48, 24), "top": (32, 32), "no_lit2": True, "extra": {"style": "shake"}}


# ==================================================================== shelters
def _shelter(name, seed, roof, wall, roof_ramp, roof_style):
    extra = {"roofing": {"kind": "shingle", "ramp": R[roof_ramp], "side": (48, 24), "top": (32, 32), "no_lit2": True,
                         "extra": {"style": roof_style}}}
    H = new(name, seed, extra)
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "back_wall", "roof", "details")}
    fr = g["frame"]
    Xh, Zf, Zb = 46.0, -30.0, 30.0
    for side, x in (("right", Xh), ("left", -Xh)):
        H.box(f"post_front_{side}", fr, [x - 1.5, 0, Zf - 1.5], [x + 1.5, 44, Zf + 1.5], "post", ("down",), "pfront")
        H.box(f"post_back_{side}", fr, [x - 1.5, 0, Zb - 1.5], [x + 1.5, 56, Zb + 1.5], "post", ("down",), "pback")
        H.box(f"post_front_{side}_pad", fr, [x - 2.5, 0, Zf - 2.5], [x + 2.5, 1.5, Zf + 2.5], "stone", ("down",), "pad")
        H.box(f"post_back_{side}_pad", fr, [x - 2.5, 0, Zb - 2.5], [x + 2.5, 1.5, Zb + 2.5], "stone", ("down",), "pad")
        H.rotbar(f"side_beam_{side}", fr, [x, 44.5, Zf - 1], [x, 56.5, Zb + 1], 2.5, "beam_z")
        H.rotbar(f"knee_front_{side}", fr, [x, 34, Zf], [x - (8 if x > 0 else -8), 42.5, Zf], 1.5, "beam_v")
        H.rotbar(f"knee_side_{side}", fr, [x, 34, Zf], [x, 43.5, Zf + 9], 1.5, "beam_v")
    H.box("front_beam", fr, [-49, 42, Zf - 2], [49, 45, Zf + 1.5], "beam", (), "fbeam")
    H.box("back_beam", fr, [-49, 54, Zb - 1.5], [49, 57, Zb + 2], "beam", (), "bbeam")
    for i, x in enumerate((-34.5, -11.5, 11.5, 34.5)):
        H.rotbar(f"rafter_{i + 1}", fr, [x, 57.5, Zb + 2], [x, 45.5, Zf - 2], 2, "beam_z")
    # back wall
    bw = g["back_wall"]
    if wall == "planks":
        H.item("wall_planks", bw, [-Xh + 1.5, 0, Zb - 1], [Xh - 1.5, 36, Zb + 1], "wallpl",
               lambda W, Hh, c: H.P.boards(R["oak"], W, Hh, 0.1, orient="v", bw=4, lap=False, nails=True, shadow_top=False))
        for i, x in enumerate((-22, 0, 22)):
            H.box(f"wall_batten_{i + 1}", bw, [x - 1, 0, Zb - 1.5], [x + 1, 36, Zb - 1], "beam_v", ("down", "south"), "batten")
        H.box("wall_cap", bw, [-Xh, 36, Zb - 1.5], [Xh, 38, Zb + 1.5], "beam", (), "wcap")
        for i, x in enumerate((-30, -8, 15, 32)):                       # pegs on the wall
            H.box(f"wall_peg_{i + 1}", bw, [x - 0.5, 26, Zb - 3], [x + 0.5, 27, Zb - 1], "wood", (), "peg")
        H.item("wall_rope_coil", bw, [-11, 18, Zb - 2.5], [-5, 25, Zb - 1], "ropec", lambda W, Hh, c: H.P.rope(W, Hh, c))
    elif wall == "stone":
        H.box("wall_stone", bw, [-Xh + 1.5, 0, Zb - 2], [Xh - 1.5, 44, Zb + 2], "rubble", ("down",), "wstone", place="ground")
        for i, y in enumerate(range(0, 44, 6)):                         # quoins at both ends
            for s in (-1, 1):
                w = 6 if i % 2 else 4
                x1, x2 = sorted((s * (Xh - 1.5), s * (Xh - 1.5 - w)))
                H.box(f"quoin_{'r' if s > 0 else 'l'}_{i + 1}", bw, [x1, y, Zb - 2.5], [x2, y + 6, Zb + 2.5], "stone", ("down",), f"q{i % 2}")
        H.box("wall_coping", bw, [-Xh, 44, Zb - 2.5], [Xh, 46, Zb + 2.5], "stone", (), "coping")
        for i, (x, y) in enumerate(((-20, 22), (18, 30))):                # iron hooks with a horseshoe and a ring
            H.box(f"wall_hook_{i + 1}", bw, [x - 0.5, y, Zb - 4], [x + 0.5, y + 1, Zb - 2], "iron", (), "hook")
            H.box(f"wall_hook_{i + 1}_ring", bw, [x - 1.5, y - 3, Zb - 3.5], [x + 1.5, y, Zb - 3], "iron", (), "ring")
    else:  # plaster panels in a timber frame
        H.item("wall_plaster", bw, [-Xh + 1.5, 0, Zb - 1], [Xh - 1.5, 54, Zb + 1], "wplaster",
               lambda W, Hh, c: H.P.plaster(R["plaster"], W, Hh, 0.2 if c != "shade" else -0.4) if min(W, Hh) >= 8
               else H.P.form(R["plaster"], W, Hh, c, 4.0))
        for i, x in enumerate((-23, 0, 23)):
            H.box(f"wall_stud_{i + 1}", bw, [x - 1, 0, Zb - 1.5], [x + 1, 54, Zb - 1], "beam_v", ("down", "south"), "stud")
        H.box("wall_rail", bw, [-Xh, 26, Zb - 1.5], [Xh, 28, Zb - 1], "beam", ("south",), "wrail")
        for i, (x1, x2) in enumerate(((-21, -2), (2, 21))):
            H.rotbar(f"wall_brace_{i + 1}", bw, [x1, 2, Zb - 1.25], [x2, 25, Zb - 1.25], 1.5, "beam_v")
        for i, x in enumerate((-34, -12, 12, 34)):                       # a shelf of jars along the wall
            H.box(f"wall_jar_{i + 1}", bw, [x - 1.5, 30, Zb - 4], [x + 1.5, 33.5, Zb - 1.5], "gold" if i % 2 else "iron", (), f"jar{i % 2}")
        H.box("wall_shelf", bw, [-40, 28.5, Zb - 4.5], [40, 30, Zb - 1], "wood", ("down",), "wshelf")
    # roof: a sloping slab over the rafters, then a ridge board and a fascia
    rf = g["roof"]
    L, ang, t = 70.0, 11.0, 1.5
    # two halves share one texture (half the atlas space); the shingle rows still line up across the join
    top = H.rect("roof_top", px(51), px(L), lambda W, Hh: H.P.shingle(R[roof_ramp], W, Hh, 0.6, style=roof_style,
                                                                      moss=roof_style == "shake"))
    und = H.rect("roof_under", px(51), px(L), lambda W, Hh: H.P.boards(R["walnut"], W, Hh, -1.0, orient="v", bw=4, lap=False,
                                                                       nails=False, shadow_top=False))
    roof_slab(H, "roof_slab_left", rf, -51, 0, 59.5, Zb + 4, L, ang, t, top, und, "beam")
    roof_slab(H, "roof_slab_right", rf, 0, 51, 59.5, Zb + 4, L, ang, t, top, und, "beam")
    H.box("roof_ridge", rf, [-52, 59, Zb + 2.5], [52, 61, Zb + 5], "beam", (), "ridge")
    fz = Zb + 4 - L * math.cos(math.radians(ang))
    fy = 59.5 - L * math.sin(math.radians(ang))
    H.box("roof_fascia", rf, [-51.5, h2(fy - 3), h2(fz - 1)], [51.5, h2(fy), h2(fz + 0.5)], "beam", (), "fascia")
    d = g["details"]
    light_lantern(H, d, 0, 42, Zf - 0.5, chain=4)
    return fin(H)


def workshop_shelter_timber(): return _shelter("workshop_shelter_timber", 9101, "shake", "planks", "walnut", "shake")
def workshop_shelter_forge(): return _shelter("workshop_shelter_forge", 9102, "slate", "stone", "tile_slate", "slate")
def workshop_shelter_apothecary(): return _shelter("workshop_shelter_apothecary", 9103, "teal", "plaster", "tile_teal", "scale")


# ==================================================================== fence
def _fence_rail(name, seed, L):
    """A rail length with its one post on the west end. The post is centred at -L/2 and the rails run from there to
    +L/2, so post-to-end is exactly L units: rails laid end to end put every post on an exact pitch (2 m for the
    32 unit rail). fence_rail used to centre its post at -15 with rails to +16 (1.9375 m), which left every rail
    end 1/16 m short of the next post."""
    H = new(name, seed)
    g = H.group("fence", [0, 0, 0])
    h = L / 2
    H.box("post", g, [-h - 1, 0, -1], [-h + 1, 15, 1], "post", ("down",), "fpost")
    H.box("post_cap", g, [-h - 1.5, 15, -1.5], [-h + 1.5, 16, 1.5], "beam", (), "fcap")
    for i, (y, rz) in enumerate(((5, 1.5), (10.5, -1.0))):
        H.box(f"rail_{i + 1}", g, [-h, y, -0.75], [h, y + 1.5, 0.75], "wood", (), f"frail{i}", rot=(0, 0, rz), origin=[0, y + 0.75, 0])
    sx = -h + 9.5                                                     # an iron strap on the rails near the post
    H.box("strap_1", g, [sx - 0.5, 4.5, -1.5], [sx + 0.5, 12.5, -1], "iron", ("down",), "strap")
    H.tufts("tuft", g, [(-h + 1, -1.6, 3, 3), (-h + 2, 1.8, 2, 3), (h - 10, -1.4, 2, 3)])
    return fin(H)


def fence_rail(): return _fence_rail("fence_rail", 9201, 32)          # 2 m
def fence_rail_short(): return _fence_rail("fence_rail_short", 9203, 19)   # 19 units = 1.1875 m: the short rail that
                                                                        # takes a side fence from 8 m to the front line


def fence_post():
    H = new("fence_post", 9202)
    g = H.group("fence", [0, 0, 0])
    H.box("post", g, [-1, 0, -1], [1, 15, 1], "post", ("down",), "fpost")
    H.box("post_cap", g, [-1.5, 15, -1.5], [1.5, 16, 1.5], "beam", (), "fcap")
    H.tufts("tuft", g, [(-1.6, -1.2, 3, 3), (1.4, 1.6, 2, 3)])
    return fin(H)


# ==================================================================== props
def log_pile():
    H = new("log_pile", 9301)
    g = {k: H.group(k, [0, 0, 0]) for k in ("logs", "stakes", "chopping_block")}
    # logs 5 thick on a 6.5 grid, each layer sitting in the gaps of the one below, ends staggered, so every log
    # and its ring end reads on its own
    layers = [(0.0, (-9.75, -3.25, 3.25, 9.75)), (4.5, (-6.5, 0.0, 6.5)), (9.0, (-3.25, 3.25)), (13.5, (0.0,))]
    i = 0
    for y, zs in layers:
        for z in zs:
            i += 1
            L = 38 + (i * 7 % 5) * 1.0; x0 = -20 + (i * 3 % 5) * 1.0
            th = 5.0 if i % 3 else 4.5
            H.log(f"log_{i}", g["logs"], [x0, y, z - th / 2], [x0 + L, y + th, z + th / 2], axis="x")
    for s in (-1, 1):
        for z in (-12.5, 12.5):
            H.box(f"stake_{'e' if s > 0 else 'w'}_{'n' if z < 0 else 's'}", g["stakes"], [s * 23 - 1, 0, z - 1], [s * 23 + 1, 15, z + 1],
                  "post", ("down",), "stake")
    c = g["chopping_block"]
    H.log("block", c, [27, 0, -4.5], [36, 7, 4.5], axis="y", hide=("down",))
    H.rotbar("axe_handle", c, [31.5, 7, 0], [33.5, 15, 3], 1, None, "axh",
             lambda W, Hh, cat: H.P.boards(R["oak"], W, Hh, 0.2, orient="v" if Hh > W else "h", bw=2, nails=False, shadow_top=False))
    H.box("axe_head", c, [29.5, 6, -1], [33, 8.5, 1], "steel", (), "axhead", rot=(0, 0, -20), origin=[31.5, 7, 0])
    for k, (x, z, r) in enumerate(((25, -8, 30), (37, 6, -50), (34, -7, 10), (23, 7, 70), (38, -3, -20))):
        H.box(f"chip_{k + 1}", c, [x - 1, 0, z - 0.5], [x + 1, 0.5, z + 0.5], "pine", ("down",), "chip", rot=(0, r, 0), origin=[x, 0, z])
    H.item("split_log_1", c, [24, 0, 9], [28, 3, 17], "split", lambda W, Hh, cat: H.P.ring_end(W, Hh, cat) if cat == "up" else H.P.bark(R["bark"], W, Hh, cat))
    return fin(H)


def lumber_stack():
    H = new("lumber_stack", 9302)
    g = {k: H.group(k, [0, 0, 0]) for k in ("bearers", "planks", "loose")}
    for i, x in enumerate((-16, 0, 16)):
        H.log(f"bearer_{i + 1}", g["bearers"], [x - 2, 0, -11], [x + 2, 4, 11], axis="z")
    pk = lambda W, Hh, c: H.P.boards(R["pine_wood"], W, Hh, 0.3 if c == "up" else (0.0 if c == "lit" else -0.5), orient="h",
                                     bw=2, lap=False, nails=False, shadow_top=False)
    y = 4.0
    for layer in range(6):
        for j, z in enumerate((-9, -4.5, 0, 4.5, 9)):
            off = ((layer * 5 + j) % 3 - 1) * 0.5
            H.item(f"plank_{layer + 1}_{j + 1}", g["planks"], [-22 + off, y, z - 2], [22 + off, y + 1.5, z + 2], "plank", pk)
        y += 1.5
        if layer < 5:
            for i, x in enumerate((-16, 0, 16)):
                H.box(f"sticker_{layer + 1}_{i + 1}", g["planks"], [x - 1, y, -11], [x + 1, y + 0.5, 11], "wood", (), "stick")
            y += 0.5
    H.item("loose_plank_1", g["loose"], [-18, y, -6], [20, y + 1.5, -2], "plank", pk, rot=(0, 8, 0), origin=[0, y, -4])
    H.item("loose_plank_2", g["loose"], [-24, 0, 12], [-20, 26, 13.5], "plankv", pk, rot=(-12, 0, 0), origin=[-22, 0, 12.5])
    H.item("loose_plank_3", g["loose"], [-19, 0, 12], [-15, 22, 13.5], "plankv2", pk, rot=(-15, 0, 4), origin=[-17, 0, 12.5])
    return fin(H)


def coal_ore_bins():
    H = new("coal_ore_bins", 9303)
    g = {k: H.group(k, [0, 0, 0]) for k in ("bins", "coal", "ore", "tools")}
    for b, x0 in enumerate((-17.0, 1.0)):
        x1 = x0 + 16
        for side, (f, t) in enumerate((([x0, 0, -8], [x1, 10, -7]), ([x0, 0, 7], [x1, 12, 8]), ([x0, 0, -7], [x0 + 1, 11, 7]),
                                        ([x1 - 1, 0, -7], [x1, 11, 7]))):
            plank_box(H, f"bin_{b + 1}_wall_{side + 1}", g["bins"], f, t)
        for cx in (x0 + 0.5, x1 - 0.5):
            for cz in (-7.5, 7.5):
                H.box(f"bin_{b + 1}_corner_{'e' if cx > x0 + 1 else 'w'}_{'n' if cz < 0 else 's'}", g["bins"], [cx - 1, 0, cz - 1], [cx + 1, 12.5, cz + 1], "post", ("down",), "bcorner")
    H.item("coal_heap", g["coal"], [-16, 6, -7], [-2, 10.5, 7], "coalheap", lambda W, Hh, c: H.P.coal(W, Hh, c))
    H.item("coal_top", g["coal"], [-13, 10.5, -4], [-5, 12, 4], "coaltop", lambda W, Hh, c: H.P.coal(W, Hh, c))
    ore = lambda W, Hh, c: H.P.pile(R["copper"], W, Hh, c, r=1.2, stem=False, gap=R["cobble"])
    H.item("ore_heap", g["ore"], [2, 6, -7], [16, 10, 7], "oreheap", ore)
    H.item("ore_top", g["ore"], [5, 10, -4], [13, 11.5, 3], "oretop", ore)
    for k, (x, z, s, rm) in enumerate(((-6, -11, 2, "coal"), (-3, -10, 1.5, "coal"), (6, -11, 2, "copper"), (10, -10.5, 1.5, "iron"))):
        H.item(f"lump_{k + 1}", g["tools"], [x - s / 2, 0, z - s / 2], [x + s / 2, s, z + s / 2], f"lump{rm}",
               lambda W, Hh, c, rm=rm: H.P.form(R[rm], W, Hh, c, 3.2, hl=True), rot=(0, k * 23, 0), origin=[x, 0, z])
    H.rotbar("shovel_handle", g["tools"], [20, 0.5, -2], [17.5, 22, 3], 1, "wood")
    H.box("shovel_blade", g["tools"], [18.5, 0, -5.5], [22.5, 5, -4.5], "iron", (), "sblade", rot=(-12, 0, 0), origin=[20, 0, -5])
    H.box("shovel_grip", g["tools"], [16, 21.5, 2], [19.5, 22.5, 3.5], "wood", (), "sgrip")
    return fin(H)


def tool_rack():
    H = new("tool_rack", 9304)
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "tools")}
    f = g["frame"]
    for i, x in enumerate((-15, 15)):
        H.box(f"leg_{i + 1}", f, [x - 1, 0, -1], [x + 1, 28, 1], "post", ("down",), "rleg")
        H.box(f"foot_{i + 1}", f, [x - 1.5, 0, -5], [x + 1.5, 1.5, 5], "beam", ("down",), "rfoot")
        H.rotbar(f"brace_{i + 1}", f, [x, 1.5, -4], [x, 8, -1], 1, "beam")
    H.box("top_bar", f, [-17, 25, -1.5], [17, 27.5, 1.5], "beam", (), "rtop")
    H.box("shelf", f, [-16, 9, -3], [16, 10.5, 2], "wood", (), "rshelf")
    t = g["tools"]
    st = lambda W, Hh, c: H.P.metal(R["steel"], W, Hh, 3.2 + (0.8 if c == "lit" else 0))
    for i, (x, hd) in enumerate(((-12, "steel"), (-8.5, "iron"))):        # hammers hanging head down
        H.box(f"hammer_{i + 1}_handle", t, [x - 0.5, 15, -2], [x + 0.5, 25, -1.5], "wood", (), "hh")
        H.box(f"hammer_{i + 1}_head", t, [x - 1.75, 13, -2.75], [x + 1.75, 15, -0.75], hd, (), f"hd{i}")
    for i, rz in enumerate((8, -8)):                                       # tongs
        H.box(f"tongs_{i + 1}", t, [-4.75, 13, -2], [-4.25, 25, -1.5], "iron", (), "tong", rot=(0, 0, rz), origin=[-4.5, 24, -1.75])
    H.item("sword_blade", t, [-0.75, 11.5, -2.25], [0.75, 22.5, -1.75], "sblade", st)  # sword, point down
    H.box("sword_guard", t, [-2.5, 22.5, -2.5], [2.5, 23.5, -1.5], "gold", (), "sguard")
    H.box("sword_grip", t, [-0.5, 23.5, -2.5], [0.5, 26.5, -1.5], "wood", (), "sgrip")
    H.box("sword_pommel", t, [-1, 26.5, -2.75], [1, 27.5, -1.25], "gold", (), "spom")
    H.box("axe_handle", t, [5.5, 12, -2], [6.5, 26, -1.5], "wood", (), "axh")       # axe
    H.item("axe_head", t, [3, 21, -2.5], [6, 25, -1], "axhd", st)
    for i, x in enumerate((9.5, 12.5)):                                    # horseshoes on pegs
        H.box(f"peg_{i + 1}", t, [x - 0.25, 24, -2.5], [x + 0.25, 24.5, -1.5], "iron", (), "peg")
        H.box(f"horseshoe_{i + 1}_a", t, [x - 1.5, 20.5, -2.25], [x - 1, 24, -1.75], "iron", (), "hs")
        H.box(f"horseshoe_{i + 1}_b", t, [x + 1, 20.5, -2.25], [x + 1.5, 24, -1.75], "iron", (), "hs")
        H.box(f"horseshoe_{i + 1}_c", t, [x - 1.5, 20, -2.25], [x + 1.5, 20.5, -1.75], "iron", (), "hsb")
    for i, (x, rm) in enumerate(((-11, "iron"), (-7, "copper"), (-3, "gold"), (2, "iron"), (6, "steel"))):   # ingots on the shelf
        H.item(f"ingot_{i + 1}", t, [x - 1.5, 10.5, -1.5], [x + 1.5, 11.5, 0], f"ing{rm}",
               lambda W, Hh, c, rm=rm: H.P.metal(R[rm], W, Hh, 3.2 + (0.8 if c == "up" else 0)))
    return fin(H)


def quench_trough():
    H = new("quench_trough", 9305)
    g = {k: H.group(k, [0, 0, 0]) for k in ("trough", "details")}
    tr = g["trough"]
    H.box("trough_floor", tr, [-14, 0, -6], [14, 2, 6], "rubble", ("down",), "tfloor", place="ground")
    for i, (f, t) in enumerate((([-14, 2, -6], [14, 9, -4]), ([-14, 2, 4], [14, 9, 6]), ([-14, 2, -4], [-12, 9, 4]), ([12, 2, -4], [14, 9, 4]))):
        H.box(f"trough_wall_{i + 1}", tr, f, t, "stone", ("down",), f"tw{i // 2}")
    H.item("water", tr, [-12, 7.5, -4], [12, 7.5, 4], "water", lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    H.box("rim_band", tr, [-14.5, 9, -6.5], [14.5, 10, 6.5], "iron", ("down",), "rim") if False else None
    d = g["details"]
    barrel(H, "bucket", d, 19, -2, 5, 5, wood="oak")
    H.item("bucket_water", d, [17, 4.5, -4], [21, 4.5, 0], "water", lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    H.box("bucket_handle", d, [16.5, 5, -2.25], [21.5, 7.5, -1.75], "iron", (), "bh")
    H.rotbar("ladle_handle", d, [-10, 9, 0], [-17, 13, -1], 0.5, "iron")
    H.box("ladle_cup", d, [-12, 8, -1], [-10, 9.5, 1], "iron", (), "lcup")
    H.box("tongs_on_rim", d, [3, 9, -5.25], [11, 9.5, -4.75], "iron", (), "trim", rot=(0, 10, 0), origin=[7, 9, -5])
    return fin(H)


def crate_stack():
    H = new("crate_stack", 9306)
    g = {k: H.group(k, [0, 0, 0]) for k in ("crates", "sacks", "barrel", "rope")}
    cr = lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c)
    for i, (f, t, ry) in enumerate((([-16, 0, -6], [-4, 12, 6], 0), ([-3, 0, -5], [7, 10, 5], 8), ([-14, 12, -5], [-4, 22, 5], -6))):
        H.item(f"crate_{i + 1}", g["crates"], f, t, f"crate{i}", cr, rot=(0, ry, 0), origin=[(f[0] + t[0]) / 2, 0, (f[2] + t[2]) / 2])
    sk = lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c)
    for i, (x, z, y) in enumerate(((10, -4, 0), (14, 2, 0), (11, -1, 7))):
        H.item(f"sack_{i + 1}", g["sacks"], [x - 3.5, y, z - 3], [x + 3.5, y + 7, z + 3], f"sack{i}", sk,
               rot=(0, i * 25, 0), origin=[x, y, z])
        H.item(f"sack_{i + 1}_neck", g["sacks"], [x - 1.5, y + 7, z - 1.5], [x + 1.5, y + 9, z + 1.5], "sackneck", sk)
    barrel(H, "barrel", g["barrel"], -10, 12, 8, 12, wood="oak")
    H.octo_item("rope_coil", g["rope"], 4, 11, 7, 0, 2, "ropecoil", lambda W, Hh, c: H.P.rope(W, Hh, c))
    H.octo_item("rope_coil_top", g["rope"], 4, 11, 5, 2, 3, "ropecoil2", lambda W, Hh, c: H.P.rope(W, Hh, c))
    return fin(H)


def tannery_vats():
    H = new("tannery_vats", 9307)
    g = {k: H.group(k, [0, 0, 0]) for k in ("vats", "hides", "beam")}
    for i, (x, z, lq) in enumerate(((-14, -2, "tan_liquor"), (-2, 4, "water"))):
        barrel(H, f"vat_{i + 1}", g["vats"], x, z, 11, 9, wood="walnut")
        H.item(f"vat_{i + 1}_liquid", g["vats"], [x - 4.5, 8.5, z - 4.5], [x + 4.5, 8.5, z + 4.5], f"liq{lq}",
               lambda W, Hh, c, lq=lq: H.P.liquid(R[lq], W, Hh, c), hide=("down", "north", "south", "east", "west"))
    H.rotbar("vat_paddle", g["vats"], [-14, 6, -2], [-11, 18, -6], 1, "wood")
    for k, (y, rm, ry) in enumerate(((0, "hide", 0), (1.5, "leather", 8), (3, "hide", -5), (4.5, "leather", 12))):
        H.item(f"hide_fold_{k + 1}", g["hides"], [8, y, -11], [18, y + 1.5, -3], f"fold{rm}",
               lambda W, Hh, c, rm=rm: H.P.hide(R[rm], W, Hh, c, shape=False), rot=(0, ry, 0), origin=[13, y, -7])
    b = g["beam"]
    for i, z in enumerate((5, 13)):
        H.box(f"beam_leg_{i + 1}", b, [15, 0, z - 1], [17, 10, z + 1], "post", ("down",), "bleg")
    H.log("scraping_beam", b, [6, 9, 7], [26, 12.5, 11], axis="x")
    H.item("draped_hide", b, [9, 3, 6.5], [21, 12.5, 11.5], "drape", lambda W, Hh, c: H.P.hide(R["hide"], W, Hh, c, shape=False),
           hide=("down",))
    return fin(H)


def potion_shelf():
    H = new("potion_shelf", 9308)
    g = {k: H.group(k, [0, 0, 0]) for k in ("shelf", "bottles", "things")}
    s = g["shelf"]
    for i, x in enumerate((-16, 14)):
        H.box(f"side_{i + 1}", s, [x, 0, -4], [x + 2, 34, 4], "beam", ("down",), "sside")
    H.item("back", s, [-14, 0, 3], [14, 34, 4], "sback", lambda W, Hh, c: H.P.boards(R["walnut"], W, Hh, -0.3, orient="v", bw=3,
                                                                                  lap=False, nails=False, shadow_top=False))
    shelves = (1.0, 11.0, 21.0, 31.0)
    for i, y in enumerate(shelves):
        H.box(f"shelf_{i + 1}", s, [-15, y, -4], [15, y + 1.5, 3], "wood", (), "board")
    H.box("crown", s, [-17, 34, -5], [17, 36, 5], "beam", (), "crown")
    gl = ["glow_green", "glow_pink", "glow_cyan", "glow_violet"]
    b = g["bottles"]; n = 0
    for row, y in enumerate((2.5, 12.5, 22.5)):
        x = -13.0
        while x < 11.5:
            n += 1
            w = 2.5 if n % 3 else 3.0; hgt = 4.0 + (n % 2) * 1.5
            rm = gl[n % 4]
            if (n + row) % 5 == 0:                                    # a jar of herbs instead
                H.item(f"jar_{n}", b, [x, y, -2], [x + 3, y + 3.5, 1], "jar", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 3.6, hl=True))
                H.item(f"jar_{n}_lid", b, [x - 0.25, y + 3.5, -2.25], [x + 3.25, y + 4.5, 1.25], "jarlid", lambda W, Hh, c: H.P.form(R["cork"], W, Hh, c, 3.6))
                x += 4.0; continue
            H.item(f"bottle_{n}_glow", b, [x, y, -1.5], [x + w, y + hgt, 1], f"bot_{rm}_{w}_{hgt}", lambda W, Hh, c, rm=rm: H.P.glass(R[rm], W, Hh, c))
            H.box(f"bottle_{n}_neck", b, [x + w / 2 - 0.5, y + hgt, -0.75], [x + w / 2 + 0.5, y + hgt + 1.5, 0.25], "gold" if n % 2 else "iron", (), "neck")
            x += w + 1.0
    t = g["things"]
    bk = [("indigo", 5), ("berry", 6), ("emerald", 5.5)]
    for i, (rm, hgt) in enumerate(bk):
        H.item(f"book_{i + 1}", t, [-13 + i * 2, 32.5, -2.5], [-11 + i * 2, 32.5 + hgt, 2.5], f"book{rm}", lambda W, Hh, c, rm=rm: H.P.book(R[rm], W, Hh, c))
    H.item("candle", t, [6, 32.5, -1], [7.5, 36.5, 0.5], "candle", lambda W, Hh, c: H.P.form(R["candle"], W, Hh, c, 4.0))
    H.item("candle_flame_glow", t, [6.25, 36.5, -0.75], [7.25, 38, 0.25], "cflame", lambda W, Hh, c: H.P.form(R["glow"], W, Hh, c, 5.2, noise=0), hide=())
    H.item("skull_jar", t, [9, 32.5, -2], [12.5, 36, 1.5], "jar", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 3.6, hl=True))
    for i, (x, z) in enumerate(((-19, -6), (19, -5))):                   # crates of ingredients at the foot
        H.item(f"ingredient_crate_{i + 1}", t, [x - 3.5, 0, z - 3], [x + 3.5, 5, z + 3], "icrate", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c))
        H.item(f"ingredient_{i + 1}", t, [x - 3, 4, z - 2.5], [x + 3, 5.5, z + 2.5], f"ingr{i}",
               lambda W, Hh, c, i=i: H.P.pile(R["berry" if i else "cabbage"], W, Hh, c, r=1.0))
    return fin(H)


def herb_bed():
    H = new("herb_bed", 9309)
    g = {k: H.group(k, [0, 0, 0]) for k in ("bed", "herbs", "can")}
    bd = g["bed"]
    for i, (f, t) in enumerate((([-20, 0, -8], [20, 6, -7]), ([-20, 0, 7], [20, 6, 8]), ([-20, 0, -7], [-19, 6, 7]), ([19, 0, -7], [20, 6, 7]))):
        plank_box(H, f"bed_side_{i + 1}", bd, f, t, wood="oak")
    for cx in (-19.5, 19.5):
        for cz in (-7.5, 7.5):
            H.box(f"bed_corner_{'e' if cx > 0 else 'w'}_{'n' if cz < 0 else 's'}", bd, [cx - 1, 0, cz - 1], [cx + 1, 7, cz + 1], "post", ("down",), "bcorner")
    H.item("bed_soil", bd, [-19, 5, -7], [19, 6, 7], "soil", lambda W, Hh, c: H.P.soil(W, Hh, c), hide=("down", "north", "south", "east", "west"))
    hb = g["herbs"]
    TD.lavender(H, hb, -14, 6, 0, 8)
    TD.flower_clump(H, hb, -6, 6, -3, "daisy", n=3, height=(2.5, 3.5))
    TD.flower_clump(H, hb, -5, 6, 3.5, "pansy", n=2, height=(1.5, 2))
    lk = H.leaf_keys(R["box_leaf"], "herb", ((2, 3, 0.2), (2.5, 3.5, -0.2), (2, 2.5, 0.0)), serrate=True)
    for x, z in ((3, -3), (3, 3.5), (9, 0), (15, -3.5), (15, 3)):
        H.rosette("herb", hb, x, 6, z, lk, n=7, tilt=(25, 70))
    TD.flower_clump(H, hb, 10, 6, -4, "marigold", n=2, height=(2.5, 3.5))
    c = g["can"]
    H.item("can_body", c, [22, 0, -10], [27, 5, -6], "can", lambda W, Hh, cat: H.P.metal(R["copper"], W, Hh, 3.2))
    H.rotbar("can_spout", c, [22, 2, -8], [18.5, 6, -8], 1, None, "spout", lambda W, Hh, cat: H.P.metal(R["copper"], W, Hh, 3.4))
    H.box("can_handle", c, [23.5, 5, -8.25], [26.5, 7.5, -7.75], "iron", (), "chandle")
    return fin(H)


# ==================================================================== trade signs
def _sign(trade, icon, seed, wood="walnut"):
    H = new(f"sign_{trade}", seed)
    g = H.group("signpost", [0, 0, 0])
    H.box("base_stone", g, [-3, 0, -3], [3, 2, 3], "stone", ("down",), "sbase", place="ground")
    H.box("post", g, [-1.25, 2, -1.25], [1.25, 42, 1.25], "post", ("down",), "spost")
    H.box("post_cap", g, [-2, 42, -2], [2, 43.5, 2], "beam", (), "scap")
    H.box("post_knob", g, [-1, 43.5, -1], [1, 45, 1], "gold", (), "sknob")
    hang_sign(H, "sign", g, 13.25, 1.25, 0, 38, icon, board=(11, 8), wood=wood)
    H.tufts("tuft", g, [(-3.6, -2.5, 3, 3), (3.4, 2.6, 2, 3)])
    return fin(H)


SIGNS = {"smelter": "flame", "blacksmith": "anvil", "carpenter": "saw", "sawyer": "logs", "tanner": "hide", "herbalist": "leaf",
         "brewer": "potion"}
BUILDERS = {f.__name__: f for f in (workshop_shelter_timber, workshop_shelter_forge, workshop_shelter_apothecary, fence_rail, fence_rail_short, fence_post,
                                     log_pile, lumber_stack, coal_ore_bins, tool_rack, quench_trough, crate_stack, tannery_vats,
                                     potion_shelf, herb_bed)}
for i, (trade, icon) in enumerate(SIGNS.items()):
    BUILDERS[f"sign_{trade}"] = (lambda trade=trade, icon=icon, i=i: _sign(trade, icon, 9400 + i))


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
