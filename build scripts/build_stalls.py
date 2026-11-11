"""Market stalls for the hub village (J00BA, 2026-11-09): "like the houses, market stalls, variation in colours, size
and appeal, 4 different ones, lots of detail". Section 3.11 (props: wood planks with grain and nails, cloth awnings
with folds, patterns and hard alpha edges), 2 px per unit, Imp 18 tall, front = north (-z, the customer side).

  market_stall_fruit   small rustic orchard stall: red / cream sloped awning, crates of apples, oranges, pears,
                       melons, grapes and lemons, hanging scale, baskets, pumpkins, barrel, apple sign
  market_stall_bakery  bakery cart: sage green cart on two big wheels, honey / cream barrel-vault canopy with a
                       scalloped fringe, bread, pies, a frosted cake, cupcakes, flour sacks, A-frame chalkboard
  market_stall_potion  apothecary booth: plum boards on a cobble plinth, teal scale gable roof with gold crest, moon
                       emblem, shelves of glowing potions, bubbling cauldron, crystal ball, herb bundles, mushrooms
  market_stall_cloth   grand cloth merchant: teal / gold peaked tent on a deck, flag poles, bunting, tied curtains,
                       folded fabric stacks, bolts, rolled rugs, hanging fabrics, a dress form
Usage: py build_stalls.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from stall_lib import Stall, stall_mats, R, F, px, h2, OPP, BLOOMS
import numpy as np

OUT = r"C:\Users\lucas\blockbench_models\buildings\stalls"


def flat_mat(rm, side=(24, 8)):
    return {"kind": "flat", "ramp": R[rm], "side": side, "top": (16, 16), "no_lit2": True}


def floor2(v): return math.floor(v * 2) / 2


def fruit_cube(H, name, grp, x, y, z, s, kind, rm, hs=None):
    hs = hs or s
    H.item(name, grp, [x - s / 2, y, z - s / 2], [x + s / 2, y + hs, z + s / 2], f"fr_{rm}_{kind}",
           lambda W, Hh, c: H.P.fruit(R[rm], W, Hh, c, kind))


def crate_with_pile(H, name, grp, x1, x2, z1, z2, y, ch, rm, r=1.5, fruits=(), kind="round", fs=1.5, stripes=False,
                    wood="pine_wood"):
    g = H.group(name, [(x1 + x2) / 2, y, (z1 + z2) / 2], grp)
    H.item(f"{name}_box", g, [x1, y, z1], [x2, y + ch, z2], f"crate_{wood}", lambda W, Hh, c: H.P.crate(R[wood], W, Hh, c))
    H.item(f"{name}_pile", g, [x1 + 0.5, y + ch - 1, z1 + 0.5], [x2 - 0.5, y + ch + 1, z2 - 0.5], f"pile_{rm}_{r}",
           lambda W, Hh, c: H.P.pile(R[rm], W, Hh, c, r=r, stripes=stripes))
    for i, (fx, fz) in enumerate(fruits):
        fruit_cube(H, f"{name}_fruit_{i + 1}", g, x1 + fx, y + ch + 1, z1 + fz, fs, kind, rm)
    return g


def tag(H, name, grp, x, y, z, w=2, h=1.5):
    H.item(name, grp, [x - w / 2, y, z - 0.25], [x + w / 2, y + h, z + 0.25], "tag", lambda W, Hh, c: H.P.tag(W, Hh, c), hide=("down", "south"))


def basket(H, name, grp, x, z, w, d, hgt, rm, r=1.5, fruits=(), y=0, handle=True):
    g = H.group(name, [x, y, z], grp)
    H.item(f"{name}_body", g, [x - w / 2, y, z - d / 2], [x + w / 2, y + hgt, z + d / 2], "wicker",
           lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c))
    H.item(f"{name}_pile", g, [x - w / 2 + 0.5, y + hgt - 1, z - d / 2 + 0.5], [x + w / 2 - 0.5, y + hgt + 0.5, z + d / 2 - 0.5],
           f"pile_{rm}_{r}", lambda W, Hh, c: H.P.pile(R[rm], W, Hh, c, r=r))
    for i, (fx, fz) in enumerate(fruits):
        fruit_cube(H, f"{name}_fruit_{i + 1}", g, x + fx, y + hgt + 0.5, z + fz, 1.5, "round", rm)
    if handle:
        H.item(f"{name}_handle_a", g, [x - w / 2 + 0.5, y + hgt, z - 0.25], [x - w / 2 + 1, y + hgt + 3, z + 0.25], "wickerh",
               lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c), hide=())
        H.item(f"{name}_handle_b", g, [x + w / 2 - 1, y + hgt, z - 0.25], [x + w / 2 - 0.5, y + hgt + 3, z + 0.25], "wickerh",
               lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c), hide=())
        H.item(f"{name}_handle_top", g, [x - w / 2 + 0.5, y + hgt + 3, z - 0.25], [x + w / 2 - 0.5, y + hgt + 3.5, z + 0.25], "wickerh",
               lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c), hide=())
    return g


def barrel(H, name, grp, x, z, w, hgt, y=0, wood="oak"):
    return H.item(name, grp, [x - w / 2, y, z - w / 2], [x + w / 2, y + hgt, z + w / 2], f"barrel_{wood}",
                  lambda W, Hh, c: H.P.barrel(R[wood], W, Hh, c))


def hang_sign(H, name, grp, side_x, post_x, z, y_arm, icon, board=(7, 5), wood="walnut", frame=None):
    """Iron bracket out sideways from a post with a curl, two chains, a painted board (icon both sides)."""
    g = H.group(name, [post_x, y_arm, z], grp)
    s = 1 if side_x > post_x else -1
    a, b = sorted((post_x, side_x))
    H.box(f"{name}_arm", g, [a, y_arm, z - 0.5], [b, y_arm + 1, z + 0.5], "iron", (), "sarm")
    bx = (post_x + side_x) / 2 + s * 0.5
    H.box(f"{name}_brace", g, [post_x + (0 if s > 0 else -3.5), y_arm - 2.5, z - 0.25], [post_x + (3.5 if s > 0 else 0), y_arm - 2, z + 0.25],
          "iron", (), "sbrace", rot=(0, 0, 45 * s), origin=[post_x, y_arm - 2.25, z])
    H.box(f"{name}_curl", g, [side_x - 0.5, y_arm + 1, z - 0.5], [side_x + 0.5, y_arm + 2, z + 0.5], "iron", (), "scurl")
    bw, bh = board
    y1 = y_arm - 2 - bh
    for i, cx in enumerate((bx - bw / 2 + 1, bx + bw / 2 - 1)):
        H.box(f"{name}_chain_{i + 1}", g, [cx - 0.25, y1 + bh, z - 0.25], [cx + 0.25, y_arm, z + 0.25], "iron", (), "schain")
    key = H.rect(f"sign_{icon}_{wood}", px(bw), px(bh), lambda W, Hh: H.P.sign(R[wood], W, Hh, "lit", icon, frame=frame))
    bg = H.group(f"{name}_board", [bx, y1 + bh, z], g)
    fs = H.faces([bx - bw / 2, y1, z - 0.25], [bx + bw / 2, y1 + bh, z + 0.25], "top", ())
    fs["north"] = F(key); fs["south"] = F(key, mirror=True)
    H.m.cube(f"{name}_board_panel", bg, [bx - bw / 2, y1, z - 0.25], [bx + bw / 2, y1 + bh, z + 0.25], fs)
    return g


def awning_rects(H, tag, A, B, w, h, sw, off=0, pin=None, light=0.5):
    rowv = -np.abs((np.arange(h) + 0.5) / h - 0.5) * 0.7
    top = H.rect(f"{tag}_top", w, h, lambda W, Hh: H.P.stripes(A, B, W, Hh, sw, off, light, pin, rowv))
    und = H.rect(f"{tag}_under", w, h, lambda W, Hh: H.P.stripes(A, B, W, Hh, sw, off, -1.2, pin, rowv))
    return top, und


# ==================================================================== 1. fruit stall (small, rustic, red and cream)
def market_stall_fruit():
    A, B = R["awn_red"], R["canvas"]
    H = Stall("market_stall_fruit", 3101, stall_mats(post="walnut", plank="oak", top="walnut", trim="paint_cream",
              extra={"cloth_a": flat_mat("awn_red"), "cobble": {"kind": "cobble", "ramp": R["cobble"], "side": (24, 4),
                                                                   "top": (16, 16), "no_lit2": True}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "counter", "awning", "goods", "sign", "details")}
    y0, z0, t, ang, L = 36.5, 10.5, 0.5, 22.5, 23
    X1, X2 = -16.5, 16.5
    # posts with stone footings
    for side, x in (("left", -15), ("right", 15)):
        for end, z in (("front", -9), ("back", 9)):
            top = floor2(H.under_y(y0, z0, z, ang, t) + 0.1)
            H.box(f"post_{end}_{side}", g["frame"], [x - 1, 1, z - 1], [x + 1, top, z + 1], "post", ("down",), f"p{end}{side}")
            H.box(f"footing_{end}_{side}", g["frame"], [x - 1.5, 0, z - 1.5], [x + 1.5, 1, z + 1.5], "cobble", ("down",), "foot")
    yb = floor2(H.under_y(y0, z0, -9, ang, t) + 0.1)
    H.box("front_beam", g["frame"], [-16, yb - 1.5, -9.5], [16, yb, -8.5], "post", (), "fbeam")
    yb2 = floor2(H.under_y(y0, z0, 9, ang, t) + 0.1)
    H.box("back_beam", g["frame"], [-16, yb2 - 1.5, 8.5], [16, yb2, 9.5], "post", (), "bbeam")
    for side, x, s in (("left", -14, 1), ("right", 14, -1)):
        H.box(f"corner_brace_{side}", g["frame"], [x - 2.5, yb - 3.5, -9.25], [x + 2.5, yb - 2.5, -8.75], "post", (), "brace",
              rot=(0, 0, -45 * s), origin=[x, yb - 3, -9])
    # counter: plank front, a middle stile, kick board, walnut top
    H.box("counter_body", g["counter"], [-14, 0, -9.5], [14, 9, -3], "plank", ("up", "down", "south"), "cbody", place="ground")
    H.box("counter_stile", g["counter"], [-0.75, 0, -10], [0.75, 9, -9.5], "post", ("down", "south"), "stile")
    H.box("counter_kick", g["counter"], [-14.5, 0, -10.5], [14.5, 1.5, -9.5], "post", ("down", "south"), "kick")
    H.box("counter_top", g["counter"], [-15, 9, -10.5], [15, 10, -2.5], "top", ("south",), "ctop")
    H.box("counter_trim", g["counter"], [-14, 7, -10.5], [14, 8.5, -9.5], "trim", ("down", "south", "up"), "ctrim")
    # back shelf (higher row)
    H.box("shelf_body", g["counter"], [-14, 0, -2.5], [14, 13, 3], "plank", ("up", "down", "north"), "sbody")
    H.box("shelf_front", g["counter"], [-14, 10, -3], [14, 13, -2.5], "plank", ("down", "south"), "sfront")
    H.box("shelf_top", g["counter"], [-14.5, 13, -3.5], [14.5, 14, 3.5], "top", (), "stop")
    # goods: front row crates
    gd = g["goods"]
    crate_with_pile(H, "crate_apples", gd, -13.5, -5, -9.5, -3.5, 10, 3, "apple", 1.5,
                    fruits=((2, 2), (4.5, 1.5), (6.5, 3), (3, 4.5)))
    crate_with_pile(H, "crate_oranges", gd, -4.25, 4.25, -9.5, -3.5, 10, 3, "orange", 1.5,
                    fruits=((2, 2.5), (5, 1.5), (6.5, 4), (3.5, 4.5)))
    crate_with_pile(H, "crate_pears", gd, 5, 13.5, -9.5, -3.5, 10, 3, "pear", 1.5, kind="pear",
                    fruits=((2.5, 2), (6, 2.5), (4, 4.5)))
    for i, x in enumerate((-9.25, 0, 9.25)):
        tag(H, f"price_tag_{i + 1}", gd, x, 11, -9.75)
    # back row: melons, grapes basket, lemons
    crate_with_pile(H, "crate_melons", gd, -13.5, -4.5, -3, 3, 14, 3, "melon", 2.5, stripes=True)
    for i, (x, z) in enumerate(((-11, -1), (-7, 0.5))):
        H.item(f"melon_{i + 1}", gd, [x - 1.5, 18, z - 1.5], [x + 1.5, 20.5, z + 1.5], "melon_big",
               lambda W, Hh, c: H.P.fruit(R["melon"], W, Hh, c, "melon"))
    basket(H, "basket_grapes", gd, 0, 0, 7, 5, 2.5, "grape", 1.0, y=14, handle=True)
    for i, (x, z) in enumerate(((-1.5, -0.5), (1.5, 0.5))):
        H.item(f"grape_bunch_{i + 1}", gd, [x - 1, 16.5, z - 1], [x + 1, 18.5, z + 1], "grape_bunch",
               lambda W, Hh, c: H.P.pile(R["grape"], W, Hh, c, r=1.0, stem=False))
    crate_with_pile(H, "crate_lemons", gd, 4.5, 13.5, -3, 3, 14, 3, "lemon", 1.5, fruits=((2, 2), (5, 3), (7, 1.5)), kind="round")
    # hanging scale from the front beam
    sc = H.group("hanging_scale", [0, yb - 1.5, -9], g["details"])
    H.box("scale_chain", sc, [-0.25, yb - 4.5, -9.25], [0.25, yb - 1.5, -8.75], "iron", (), "schn")
    H.box("scale_beam", sc, [-3.5, yb - 5, -9.25], [3.5, yb - 4.5, -8.75], "gold", (), "sbeam")
    for s, x in (("left", -3), ("right", 3)):
        H.box(f"scale_string_{s}", sc, [x - 0.25, yb - 7.5, -9.25], [x + 0.25, yb - 5, -8.75], "iron", (), "sstr")
        H.box(f"scale_pan_{s}", sc, [x - 1.5, yb - 8, -10.5], [x + 1.5, yb - 7.5, -7.5], "gold", (), "span")
    fruit_cube(H, "scale_apple", sc, -3, yb - 7.5, -9, 1.5, "round", "apple")
    # awning: red and cream stripes, 11 stripes of 6 px, scalloped valance with gold braid, side cheeks
    W = px(X2 - X1)
    top, und = awning_rects(H, "awn", A, B, W, px(L), 6)
    yf, zf = H.slab("awning_cloth", g["awning"], X1, X2, y0, z0, L, ang, t, top, und, "cloth_a")
    vk = H.rect("valance_front", W, 8, lambda Ww, Hh: H.P.valance(A, B, Ww, Hh, 6, 0, "scallop", trim=R["gold"]))
    H.card("awning_valance", g["awning"], [X1, yf - 4, zf - 0.05], [X2, yf, zf - 0.05], vk)
    ck = H.rect("valance_side", px(L), 5, lambda Ww, Hh: H.P.valance(A, B, Ww, Hh, 6, 0, "scallop", trim=R["gold"], cut=2))
    for s, x in (("left", X1 - 0.05), ("right", X2 + 0.05)):
        H.card(f"awning_cheek_{s}", g["awning"], [x, y0 - t - 2.5, z0 - L], [x, y0 - t, z0], ck, faces=("east", "west"),
               rot=(-ang, 0, 0), origin=[x, y0, z0])
    H.box("awning_rail", g["awning"], [X1 - 0.5, y0 - 0.5, z0 - 0.5], [X2 + 0.5, y0 + 0.5, z0 + 0.5], "post", (), "arail")
    # sign on the left post
    hang_sign(H, "apple_sign", g["sign"], -24, -16, -9, yb - 3, "apple", board=(7, 6))
    # ground: baskets, pumpkins, crate stack, barrel of apples
    dt = g["details"]
    basket(H, "basket_apples", dt, 9, -14, 5, 4, 3, "apple", 1.5, fruits=((-1, 0),), handle=True)
    basket(H, "basket_oranges", dt, -8, -13.5, 4, 4, 2.5, "orange", 1.5, handle=False)
    for i, (x, z, s, hs) in enumerate(((20, -6, 4, 3.5), (22.5, -2, 3, 2.5), (19.5, -1.5, 2.5, 2))):
        H.item(f"pumpkin_{i + 1}", dt, [x - s / 2, 0, z - s / 2], [x + s / 2, hs, z + s / 2], f"pumpkin",
               lambda W, Hh, c: H.P.fruit(R["pumpkin"], W, Hh, c, "pumpkin"))
        H.box(f"pumpkin_{i + 1}_stem", dt, [x - 0.25, hs, z - 0.25], [x + 0.25, hs + 1, z + 0.25], "post", (), "pstem")
    crate_with_pile(H, "ground_crate_cabbages", dt, -23, -17, 0, 6, 0, 4, "cabbage", 2.0)
    H.item("ground_crate_empty", dt, [-22.5, 0, 6.5], [-17.5, 4, 11.5], "crate_pine_wood", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c),
           rot=(0, 22.5, 0), origin=[-20, 0, 9])
    H.item("ground_crate_top", dt, [-22, 4, 7], [-18, 7, 11], "crate_pine_wood", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c),
           rot=(0, 22.5, 0), origin=[-20, 4, 9])
    barrel(H, "barrel", dt, 19.5, 6, 5, 7)
    H.item("barrel_apples", dt, [17.5, 6.5, 4], [21.5, 7.5, 8], "pile_apple_1.5", lambda W, Hh, c: H.P.pile(R["apple"], W, Hh, c, r=1.5))
    for i, (x, z) in enumerate(((18.5, 5), (20.5, 7))):
        fruit_cube(H, f"barrel_apple_{i + 1}", dt, x, 7.5, z, 1.5, "round", "apple")
    H.item("sack_lean", dt, [13, 0, 4], [16.5, 5, 7], "sack", lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c),
           rot=(0, 0, -11.25), origin=[16.5, 0, 5.5])
    return H


# ==================================================================== 2. bakery cart (wheels, barrel-vault canopy)
def market_stall_bakery():
    A, B = R["awn_honey"], R["canvas"]
    H = Stall("market_stall_bakery", 3202, stall_mats(post="paint_cream", plank="sage", top="walnut", trim="gold",
              trim_kind="carved", extra={
                  "wheel": {"kind": "boards", "ramp": R["walnut"], "side": (24, 16), "top": (16, 16), "no_lit2": True,
                            "extra": {"bw": 2, "shadow_top": False}},
                  "chassis": {"kind": "boards", "ramp": R["oak"], "side": (80, 8), "top": (80, 24), "no_lit2": True,
                              "extra": {"bw": 2, "shadow_top": False}},
                  "cloth_a": flat_mat("awn_honey"),
                  "panel": {"kind": "carved", "ramp": R["paint_cream"], "side": (24, 16), "top": (16, 16), "no_lit2": True, "extra": {"motif": "diamond"}}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("cart", "wheels", "canopy", "goods", "sign", "details")}
    c = g["cart"]
    # body: chassis, sage plank body with cream panels and gold trim, walnut top
    H.box("chassis", c, [-18, 7, -9.5], [18, 8, 9.5], "chassis", (), "chas")
    H.box("cart_body", c, [-17, 8, -9], [17, 16, 9], "plank", ("down", "up"), "body", place="any")
    for i, (a, b) in enumerate(((-15.5, -6), (-4.5, 4.5), (6, 15.5))):
        H.box(f"front_panel_{i + 1}", c, [a, 9.5, -9.5], [b, 14.5, -9], "panel", ("south", "down"), f"pan{i}")
    wk = H.rect("sign_wheat_panel", px(5), px(4), lambda W, Hh: H.P.sign(R["paint_cream"], W, Hh, "lit", "wheat", frame=R["gold"]))
    fs = {f: None for f in ("north", "east", "south", "west", "up", "down")}; fs["north"] = F(wk)
    H.m.cube("front_panel_wheat", c, [-2.5, 10, -9.75], [2.5, 14, -9.75], fs)
    H.box("trim_top", c, [-17.5, 15, -9.5], [17.5, 16, 9.5], "trim", ("down", "up"), "ttop")
    H.box("trim_bottom", c, [-17.5, 8, -9.5], [17.5, 9, 9.5], "trim", ("up",), "tbot")
    H.box("cart_top", c, [-18, 16, -10], [18, 17, 10], "top", (), "ctop")
    # wheels on the sides, axle, back legs and handles
    for s, (x1, x2) in (("left", (-20, -18.5)), ("right", (18.5, 20))):
        H.wheel(f"wheel_{s}", g["wheels"], x1, x2, 6.75, 0, 6.0)
    H.box("axle", g["wheels"], [-18.5, 6.25, -0.5], [18.5, 7.25, 0.5], "iron", (), "axle")
    for s, x in (("left", -15), ("right", 15)):
        H.box(f"leg_{s}", c, [x - 0.75, 0, 7.5], [x + 0.75, 7, 9], "chassis", ("down",), "leg")
        H.box(f"leg_{s}_foot", c, [x - 1.25, 0, 7], [x + 1.25, 0.5, 9.5], "iron", ("down",), "foot")
        H.box(f"handle_{s}", c, [x - 0.75, 7, 9.5], [x + 0.75, 8, 23], "chassis", (), "hdl", rot=(11.25, 0, 0), origin=[x, 7.5, 9.5])
        H.box(f"handle_{s}_grip", c, [x - 1, 5.5, 21], [x + 1, 7, 24], "wheel", (), "grip")
    H.box("handle_bar", c, [-15, 5.5, 22], [15, 6.5, 23], "chassis", (), "hbar")
    # canopy: barrel vault of 9 rotated slats (15 degree steps), honey and cream stripes, gold piping, fringes
    R0, cy0, n, step = 16.0, 24.0, 9, 15.0
    seg_len = 4.5
    Wp = px(42) + 2
    top = H.rect("vault_top", Wp, n * px(seg_len),
                 lambda W, Hh: H.P.stripes(A, B, W, Hh, 12, 1, 0.5, R["gold"], -np.abs((np.arange(Hh) + 0.5) / Hh - 0.5) * 1.2))
    und = H.rect("vault_under", Wp, n * px(seg_len),
                 lambda W, Hh: H.P.stripes(A, B, W, Hh, 12, 1, -1.3, R["gold"], None))
    for k in range(n):
        th = (k - (n - 1) / 2) * step
        yc = cy0 + R0 * math.cos(math.radians(th)); zc = R0 * math.sin(math.radians(th))
        wide = k % 2 == 1
        x1, x2 = (-21.5, 21.5) if wide else (-21, 21)
        sub = (0 if wide else 1, k * px(seg_len), px(x2 - x1), px(seg_len))
        frm, to = [x1, yc - 0.25, zc - seg_len / 2], [x2, yc + 0.25, zc + seg_len / 2]
        fs = H.faces(frm, to, "cloth_a", (), f"vault{k}")
        fs["up"] = F(top, sub=sub); fs["down"] = F(und, sub=sub)
        H.m.cube(f"canopy_slat_{k + 1}", g["canopy"], frm, to, fs, (th, 0, 0), [0, yc, zc])
        # side fringe under each slat (east and west), following the arc
        fk = H.rect("vault_fringe", px(seg_len), 4, lambda W, Hh: H.P.valance(A, A, W, Hh, 9, 0, "scallop", trim=R["gold"], cut=2))
        for s, x in (("left", x1 - 0.05), ("right", x2 + 0.05)):
            H.card(f"canopy_fringe_{k + 1}_{s}", g["canopy"], [x, yc - 0.25 - 2, zc - seg_len / 2], [x, yc - 0.25, zc + seg_len / 2],
                   fk, faces=("east", "west"), rot=(th, 0, 0), origin=[x, yc, zc])
    # end valances front and back
    th_end = ((n - 1) / 2 + 0.5) * step
    ze = R0 * math.sin(math.radians(th_end)); ye = cy0 + R0 * math.cos(math.radians(th_end))
    yv = floor2(ye)
    vk = H.rect("vault_valance", px(42), 9, lambda W, Hh: H.P.valance(A, B, W, Hh, 12, 0, "scallop", trim=R["gold"], pin=R["gold"]))
    H.card("canopy_valance_front", g["canopy"], [-21, yv - 4.5, -ze - 0.1], [21, yv, -ze - 0.1], vk)
    H.card("canopy_valance_back", g["canopy"], [-21, yv - 4.5, ze + 0.1], [21, yv, ze + 0.1], vk, faces=("south", "north"))
    # turned posts with gold rings
    for s, x in (("left", -16.5), ("right", 16.5)):
        for e, z in (("front", -8.5), ("back", 8.5)):
            th = math.degrees(math.asin(abs(z) / R0))
            ytop = floor2(cy0 + R0 * math.cos(math.radians(th)) - 0.4)
            H.box(f"post_{e}_{s}", g["canopy"], [x - 0.75, 17, z - 0.75], [x + 0.75, ytop, z + 0.75], "post", ("down",), f"po{e}{s}")
            for i, yr in enumerate((18, 26.5)):
                H.box(f"post_{e}_{s}_ring_{i + 1}", g["canopy"], [x - 1.25, yr, z - 1.25], [x + 1.25, yr + 1, z + 1.25], "gold", (), "ring")
    # crest sign on the vault peak
    ck = H.rect("crest_loaf", px(12), px(7), lambda W, Hh: H.P.sign(R["walnut"], W, Hh, "lit", "loaf", arch=True, frame=R["gold"]))
    fs = H.faces([-6, 40, -0.25], [6, 47, 0.25], "top", ("down",), "crest")
    fs["north"] = F(ck); fs["south"] = F(ck, mirror=True); fs["up"] = None
    H.m.cube("crest_board", g["sign"], [-6, 39.5, -0.25], [6, 46.5, 0.25], fs)
    for s, x in (("left", -6.5), ("right", 6.5)):
        H.box(f"crest_knob_{s}", g["sign"], [x - 0.75, 39.5, -0.75], [x + 0.75, 41, 0.75], "gold", (), "cknob")
    # goods on the cart top (y 17): tiered rack at the back, cake, pies, loaves, cupcakes, baguette basket
    gd = g["goods"]
    H.box("rack_tier_1", gd, [-15, 17, 1.5], [15, 20, 8.5], "plank", ("down",), "rack1")
    H.box("rack_tier_2", gd, [-15, 20, 5], [15, 23, 8.5], "plank", ("down",), "rack2")
    H.box("rack_lip", gd, [-15, 20, 1.5], [15, 20.5, 2], "trim", ("down",), "rlip")
    crust = lambda W, Hh, c, **kw: H.P.crust(R["crust"], W, Hh, c, **kw)
    for i, x in enumerate((-12, -7.5, -3, 1.5, 6, 10.5)):                     # round loaves on tier 1
        H.item(f"boule_{i + 1}", gd, [x - 1.5, 20, 2.5], [x + 1.5, 21.5, 4.5], "boule", crust)
    for i, x in enumerate((-11, -4, 3, 10)):                                  # long loaves on tier 2
        H.item(f"batard_{i + 1}", gd, [x - 2.5, 23, 5.5], [x + 2.5, 24.5, 7.5], "batard", lambda W, Hh, c: H.P.crust(R["crust"], W, Hh, c, scores=4))
    H.item("braid_loaf", gd, [-14, 17, -8], [-9, 18.5, -5.5], "braid", lambda W, Hh, c: H.P.crust(R["crust"], W, Hh, c, braid=True))
    # cake stand with a two tier frosted cake and a cherry
    cg = H.group("cake_stand", [-3, 17, -4.5], gd)
    H.box("cake_stand_base", cg, [-4.5, 17, -6], [-1.5, 17.5, -3], "gold", (), "cbase")
    H.box("cake_stand_stem", cg, [-3.5, 17.5, -5], [-2.5, 19, -4], "gold", (), "cstem")
    H.box("cake_stand_plate", cg, [-5.5, 19, -7], [-0.5, 19.5, -2], "gold", (), "cplate")
    H.item("cake_tier_1", cg, [-5, 19.5, -6.5], [-1, 21.5, -2.5], "cake_pink", lambda W, Hh, c: H.P.frosting(R["frost_pink"], W, Hh, c))
    H.item("cake_tier_2", cg, [-4, 21.5, -5.5], [-2, 23, -3.5], "cake_cream", lambda W, Hh, c: H.P.frosting(R["canvas"], W, Hh, c, sprinkles=False))
    fruit_cube(H, "cake_cherry", cg, -3, 23, -4.5, 1, "round", "berry")
    # pies on boards
    for i, (x, fill) in enumerate(((3, "berry"), (7.5, "pumpkin"))):
        H.box(f"pie_board_{i + 1}", gd, [x - 2, 17, -8.5], [x + 2, 17.5, -4.5], "chassis", (), "pboard")
        H.item(f"pie_{i + 1}", gd, [x - 1.5, 17.5, -8], [x + 1.5, 18.5, -5], f"pie_{fill}", lambda W, Hh, c, f=fill: H.P.pie(W, Hh, c, f))
    # cupcakes row
    for i, (x, fr) in enumerate(((11.5, "frost_pink"), (13.5, "canvas"), (15.5, "glow_violet"))):
        H.item(f"cupcake_{i + 1}", gd, [x - 0.75, 17, -8.5], [x + 0.75, 18, -7], "cup_base", lambda W, Hh, c: H.P.wicker(R["paper"], W, Hh, c))
        H.item(f"cupcake_{i + 1}_top", gd, [x - 0.75, 18, -8.5], [x + 0.75, 19, -7], f"cup_{fr}",
               lambda W, Hh, c, f=fr: H.P.form(R[f], W, Hh, c, 3.8, hl=True))
    # baguette basket at the right end
    bg = H.group("baguette_basket", [13, 17, -3], gd)
    H.item("baguette_basket_body", bg, [11, 17, -5], [15, 20, -1.5], "wicker", lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c))
    for i, (x, z, rx, rz) in enumerate(((12, -4, 0, 11.25), (13.5, -3.5, -11.25, 0), (12.5, -2.5, 11.25, -11.25), (14, -2.5, 0, -11.25))):
        H.item(f"baguette_{i + 1}", bg, [x - 0.5, 18, z - 0.5], [x + 0.5, 25, z + 0.5], "baguette",
               lambda W, Hh, c: H.P.crust(R["crust"], W, Hh, c, scores=1), rot=(rx, 0, rz), origin=[x, 18, z])
    # lantern under the front right of the canopy, flour sacks, chalkboard
    dt = g["details"]
    H.lantern_hang("lantern", dt, 14, 36.5, -9.5, chain=2.5)
    for i, (x, z, w, hh, ry) in enumerate(((-23, 4, 4, 5, 22.5), (-24, -2, 3.5, 4, -11.25))):
        sg = H.group(f"flour_sack_{i + 1}", [x, 0, z], dt)
        H.item(f"flour_sack_{i + 1}_body", sg, [x - w / 2, 0, z - w / 2 + 0.5], [x + w / 2, hh, z + w / 2 - 0.5], "sack",
               lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c), rot=(0, ry, 0), origin=[x, 0, z])
        H.item(f"flour_sack_{i + 1}_neck", sg, [x - 1, hh, z - 0.75], [x + 1, hh + 1, z + 0.75], "sackneck",
               lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c), rot=(0, ry, 0), origin=[x, 0, z])
        H.box(f"flour_sack_{i + 1}_tie", sg, [x - 1.25, hh, z - 1], [x + 1.25, hh + 0.5, z + 1], "gold", (), "tie", rot=(0, ry, 0), origin=[x, 0, z])
    ab = H.group("chalkboard", [-12, 0, -15], dt)
    chk = H.rect("chalk_board", px(7), px(9), lambda W, Hh: H.P.chalkboard(W, Hh, "lit", "loaf"))
    for s, sgn in (("front", -1), ("back", 1)):
        fs = H.faces([-15.5, 0, -15.25], [-8.5, 9, -14.75], "chassis", ("down",), "chk")
        fs["north" if sgn < 0 else "south"] = F(chk)
        H.m.cube(f"chalkboard_{s}", ab, [-15.5, 0, -15.25 + sgn * 1.5], [-8.5, 9, -14.75 + sgn * 1.5], fs,
                 (sgn * -11.25, 0, 0), [-12, 0, -15 + sgn * 1.5])
    H.box("chalkboard_hinge", ab, [-15.5, 8.5, -15.5], [-8.5, 9.5, -14.5], "chassis", (), "chinge")
    return H


# ==================================================================== 3. potion stall (apothecary booth, roofed)
def market_stall_potion():
    H = Stall("market_stall_potion", 3303, stall_mats(post="walnut", plank="plum_paint", top="walnut", trim="gold",
              trim_kind="carved", extra={
                  "wall": {"kind": "boards", "ramp": R["plum_paint"], "side": (80, 80), "top": (16, 16), "no_lit2": True,
                           "extra": {"orient": "v", "bw": 3, "lap": False}},
                  "roof": {"kind": "shingle", "ramp": R["tile_teal"], "side": (96, 40), "top": (48, 48), "under": (48, 48),
                           "no_lit2": True, "extra": {"style": "scale", "accent": R["tile_purple"]}},
                  "plinth": {"kind": "cobble", "ramp": R["cobble"], "side": (96, 8), "top": (96, 64), "no_lit2": True},
                  "shelf": {"kind": "boards", "ramp": R["walnut"], "side": (72, 4), "top": (72, 8), "no_lit2": True,
                            "extra": {"bw": 2, "shadow_top": False}},
                  "cauldron": {"kind": "metal", "ramp": R["iron"], "side": (24, 16), "top": (16, 16), "no_lit2": True}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("booth", "roofs", "counter", "shelves", "goods", "sign", "details")}
    b = g["booth"]
    H.box("plinth", b, [-21, 0, -13], [21, 2, 13], "plinth", ("down",), "plinth", place="ground")
    H.box("back_wall", b, [-19, 2, 9], [19, 40, 11], "wall", ("down", "up"), "bwall", place="top")
    for s, (a, c) in (("left", (-19, -17)), ("right", (17, 19))):
        H.box(f"side_wall_{s}", b, [a, 2, -3], [c, 40, 9], "wall", ("down", "up"), f"sw{s}", place="top")
        H.box(f"front_post_{s}", b, [a - 0.5, 2, -12], [c + 0.5, 40, -9], "post", ("down",), f"fp{s}")
        H.box(f"front_post_{s}_base", b, [a - 1, 2, -12.5], [c + 1, 4, -8.5], "stone", ("down",), "fpb")
        H.box(f"front_post_{s}_capital", b, [a - 1, 36, -12.5], [c + 1, 37.5, -8.5], "trim", (), "fpc")
        side = "west" if s == "left" else "east"
        plane = a if s == "left" else c
        H.window(f"side_window_{s}", b, side, plane, 3, 20, 6, 9, style="leaded", arch=True, frame_ramp=R["paint_cream"],
                 sill="trim", lintel="trim", shutters="paint_teal")
    H.box("header", b, [-19, 37.5, -12], [19, 40, -9], "trim", ("down",), "header")
    H.box("header_under", b, [-17, 36, -11], [17, 37.5, -9.5], "post", (), "hunder")
    for s, a in (("left", -17), ("right", 15)):
        H.box(f"header_bracket_{s}", b, [a, 32, -11], [a + 2, 36, -9.5], "post", (), "hbr")
    # roof: ridge front to back, plum board gables, gold crest and finials, moon emblem in the front gable
    prof = [(0, 2)] + [(3, 3)] * 5 + [(2.5, 3)] * 2
    top = H.roof("roof", g["roofs"], -19, 19, -12, 11, 40, prof, "roof", "wall", axis="z", eave=3,
                 caps=("trim", 1), ridge=("gold", 2, 1.5), crest=("gold", 4), finials=("gold", 6))
    mk = H.rect("moon_emblem", px(10), px(10), lambda W, Hh: H.P.sign(R["plum_paint"], W, Hh, "lit", "moon", frame=R["gold"]))
    fs = H.faces([-5, 44, -13], [5, 54, -12], "trim", ("south", "down"), "moon")
    fs["north"] = F(mk)
    H.m.cube("gable_moon_emblem", g["roofs"], [-5, 44, -13], [5, 54, -12], fs)
    # counter: plum boards, gold carved band, potion panel, walnut top
    cn = g["counter"]
    H.box("counter_body", cn, [-16.5, 2, -11], [16.5, 12, -6], "plank", ("down", "up"), "cbody")
    H.box("counter_band", cn, [-16.75, 9.5, -11.25], [16.75, 11, -10.75], "trim", ("south", "down"), "cband")
    H.box("counter_base", cn, [-16.75, 2, -11.25], [16.75, 3.5, -10.75], "trim", ("south",), "cbase")
    pk = H.rect("potion_panel", px(8), px(5), lambda W, Hh: H.P.sign(R["walnut"], W, Hh, "lit", "potion", frame=R["gold"]))
    fs = H.faces([-4, 4, -11.5], [4, 9, -11], "trim", ("south", "down"), "ppan"); fs["north"] = F(pk)
    H.m.cube("counter_potion_panel", cn, [-4, 4, -11.5], [4, 9, -11], fs)
    H.box("counter_top", cn, [-17.5, 12, -12], [17.5, 13, -5.5], "top", (), "ctop")
    # shelves with brackets and bottles
    sh = g["shelves"]
    glows = ["glow_green", "glow_pink", "glow_cyan", "glow_violet", "glow"]
    rnd = H.rng
    bottle_n = [0]

    def bottle(grp, x, y, z, kind, gl):
        bottle_n[0] += 1; n = bottle_n[0]
        bg = H.group(f"bottle_{n}", [x, y, z], grp)
        G = R[gl] if gl != "glow" else R["glow"]
        if kind == "flask":
            H.item(f"bottle_{n}_body_glow", bg, [x - 1, y, z - 1], [x + 1, y + 2, z + 1], f"glass_{gl}_f", lambda W, Hh, c: H.P.glass(G, W, Hh, c))
            H.item(f"bottle_{n}_neck", bg, [x - 0.5, y + 2, z - 0.5], [x + 0.5, y + 3, z + 0.5], "neck", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 4.2))
            H.item(f"bottle_{n}_cork", bg, [x - 0.5, y + 3, z - 0.5], [x + 0.5, y + 3.5, z + 0.5], "cork", lambda W, Hh, c: H.P.form(R["cork"], W, Hh, c, 3.6))
        elif kind == "tall":
            H.item(f"bottle_{n}_body_glow", bg, [x - 0.75, y, z - 0.75], [x + 0.75, y + 3.5, z + 0.75], f"glass_{gl}_t", lambda W, Hh, c: H.P.glass(G, W, Hh, c))
            H.item(f"bottle_{n}_neck", bg, [x - 0.5, y + 3.5, z - 0.5], [x + 0.5, y + 4.5, z + 0.5], "neck", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 4.2))
            H.item(f"bottle_{n}_cork", bg, [x - 0.5, y + 4.5, z - 0.5], [x + 0.5, y + 5, z + 0.5], "cork", lambda W, Hh, c: H.P.form(R["cork"], W, Hh, c, 3.6))
        elif kind == "round":
            H.octo_item = None
            H.item(f"bottle_{n}_body_glow", bg, [x - 1.5, y, z - 1], [x + 1.5, y + 2.5, z + 1], f"glass_{gl}_r", lambda W, Hh, c: H.P.glass(G, W, Hh, c))
            H.item(f"bottle_{n}_body_b_glow", bg, [x - 1, y, z - 1.5], [x + 1, y + 2, z + 1.5], f"glass_{gl}_rb", lambda W, Hh, c: H.P.glass(G, W, Hh, c))
            H.item(f"bottle_{n}_neck", bg, [x - 0.5, y + 2.5, z - 0.5], [x + 0.5, y + 3.5, z + 0.5], "neck", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 4.2))
            H.item(f"bottle_{n}_stopper", bg, [x - 0.75, y + 3.5, z - 0.75], [x + 0.75, y + 4.5, z + 0.75], "stopper", lambda W, Hh, c: H.P.form(R["gold"], W, Hh, c, 3.8, hl=True))
        else:  # jar of herbs with an iron lid
            H.item(f"jar_{n}_body", bg, [x - 1.25, y, z - 1.25], [x + 1.25, y + 2.5, z + 1.25], "jar", lambda W, Hh, c: H.P.leafy(R["cabbage"], W, Hh, c, R["glow_violet"]))
            H.box(f"jar_{n}_lid", bg, [x - 1.5, y + 2.5, z - 1.5], [x + 1.5, y + 3, z + 1.5], "iron", (), "jlid")

    kinds = ["flask", "tall", "round", "jar", "flask", "tall", "round", "flask"]
    for si, ys in enumerate((16, 23, 30)):
        H.box(f"shelf_{si + 1}", sh, [-16.5, ys - 1, 5.5], [16.5, ys, 9], "shelf", (), f"sh{si}")
        for s, x in (("left", -14), ("right", 14)):
            H.box(f"shelf_{si + 1}_bracket_{s}", sh, [x - 0.5, ys - 3, 7.5], [x + 0.5, ys - 1, 9], "iron", (), "sbr")
        xs = np.linspace(-14.5, 14.5, 8 if si != 1 else 7)
        for j, x in enumerate(xs):
            k = kinds[(j + si * 3) % len(kinds)]
            if si == 1 and j == 3:                                              # a stack of books in the middle
                for bi, (rm, hh) in enumerate((("indigo", 1), ("rose", 1), ("emerald", 1))):
                    H.item(f"book_{bi + 1}", sh, [x - 2 + bi * 0.25, ys + bi, 6], [x + 2 - bi * 0.25, ys + bi + hh, 8.5], f"book_{rm}",
                           lambda W, Hh, c, r_=rm: H.P.book(R[r_], W, Hh, c))
                H.item("skull_candle", sh, [x - 0.5, ys + 3, 6.75], [x + 0.5, ys + 5, 7.75], "candle", lambda W, Hh, c: H.P.form(R["candle"], W, Hh, c, 4.0))
                H.item("skull_candle_flame_glow", sh, [x - 0.25, ys + 5, 7], [x + 0.25, ys + 6, 7.5], "flame", lambda W, Hh, c: H.P.form(R["glow"], W, Hh, c, 4.8, noise=0))
                continue
            bottle(sh, float(round(x * 2) / 2), ys, 7.25, k, glows[(j * 2 + si) % len(glows)])
    # counter top: cauldron, crystal ball, open book, flasks, mortar
    gd = g["goods"]
    cg = H.group("cauldron", [-10, 13, -8.5], gd)
    H.octo("cauldron_body", cg, -10, -8.5, 6, 14, 18, "cauldron", ("down",), "cbody")
    H.octo("cauldron_belly", cg, -10, -8.5, 7, 15, 17, "cauldron", (), "cbelly")
    H.octo("cauldron_rim", cg, -10, -8.5, 6.5, 18, 18.5, "cauldron", ("down",), "crim")
    H.item("cauldron_brew_glow", cg, [-12.5, 18.25, -11], [-7.5, 18.75, -6], "brew", lambda W, Hh, c: H.P.pile(R["glow_green"], W, Hh, c, r=1.0, stem=False, gap=R["glow_green"]), hide=("down",))
    for i, (dx, dz, s) in enumerate(((-1, 0.5, 1), (1, -1, 0.5), (0.5, 1, 0.5))):
        H.item(f"cauldron_bubble_{i + 1}_glow", cg, [-10 + dx - s / 2, 19 + i * 0.75, -8.5 + dz - s / 2], [-10 + dx + s / 2, 19 + i * 0.75 + s, -8.5 + dz + s / 2],
               "bubble", lambda W, Hh, c: H.P.form(R["glow_green"], W, Hh, c, 4.6, noise=0), hide=())
    for i, (dx, dz) in enumerate(((-2, -2), (2, -2), (0, 2))):
        H.box(f"cauldron_leg_{i + 1}", cg, [-10 + dx - 0.5, 13, -8.5 + dz - 0.5], [-10 + dx + 0.5, 14, -8.5 + dz + 0.5], "cauldron", ("down",), "cleg")
    bg = H.group("crystal_ball", [10, 13, -8.5], gd)
    H.box("crystal_ball_stand", bg, [8.5, 13, -10], [11.5, 14, -7], "gold", ("down",), "cbst")
    H.box("crystal_ball_claws", bg, [9, 14, -9.5], [11, 14.5, -7.5], "gold", ("down",), "cbcl")
    ball = lambda W, Hh, c: H.P.pile(R["glow_violet"], W, Hh, c, r=2.5, stem=False, gap=R["glow_violet"])
    H.item("crystal_ball_a_glow", bg, [8.5, 14.5, -9.5], [11.5, 17.5, -7.5], "ball", ball, hide=())
    H.item("crystal_ball_b_glow", bg, [9, 14.25, -10], [11, 17.75, -7], "ball_b", ball, hide=())
    H.item("crystal_ball_c_glow", bg, [8.75, 14.75, -9.75], [11.25, 17.25, -7.25], "ball_c", ball, hide=())
    bk = H.rect("open_book_pages", px(5), px(3.5), lambda W, Hh: H.P.pages(W, Hh, "up"))
    H.box("spellbook_cover", gd, [-3, 13, -10], [3, 13.5, -6], "plank", ("down",), "bcover")
    fs = H.faces([-2.5, 13.5, -9.75], [2.5, 14, -6.25], "top", ("down",), "pages"); fs["up"] = F(bk)
    fs["north"] = F("open_book_pages", sub=(0, 0, 10, 1)); fs["south"] = F("open_book_pages", sub=(0, 0, 10, 1))
    fs["east"] = F("open_book_pages", sub=(0, 0, 7, 1)); fs["west"] = F("open_book_pages", sub=(0, 0, 7, 1))
    H.m.cube("spellbook_pages", gd, [-2.5, 13.5, -9.75], [2.5, 14, -6.25], fs)
    bottle(gd, 4.5, 13, -9.5, "flask", "glow_pink")
    bottle(gd, 6, 13, -7, "tall", "glow_cyan")
    bottle(gd, -5, 13, -7.5, "flask", "glow")
    H.item("mortar", gd, [13.5, 13, -10.5], [16, 14.5, -8], "mortar", lambda W, Hh, c: H.P.form(R["stone"], W, Hh, c, 3.6))
    H.item("pestle", gd, [14.5, 14, -10], [15.5, 17, -9], "pestle", lambda W, Hh, c: H.P.form(R["stone"], W, Hh, c, 4.0), rot=(0, 0, -22.5), origin=[15, 14, -9.5])
    # hanging herb bundles under the header
    for i, x in enumerate((-12, -6.5, -1, 4.5, 11)):
        hg = H.group(f"herb_bundle_{i + 1}", [x, 36, -10.25], g["details"])
        drop = 1.5 + (i % 2) * 1.0
        H.box(f"herb_bundle_{i + 1}_string", hg, [x - 0.25, 36 - drop, -10.5], [x + 0.25, 36, -10], "iron", (), "hstr")
        H.item(f"herb_bundle_{i + 1}_tie", hg, [x - 0.75, 35 - drop, -11], [x + 0.75, 36 - drop, -9.5], "htie", lambda W, Hh, c: H.P.form(R["burlap"], W, Hh, c, 3.6))
        fl = [None, R["glow_violet"], BLOOMS[1], None, BLOOMS[3]][i]
        H.item(f"herb_bundle_{i + 1}_leaves", hg, [x - 1, 31.5 - drop, -11.25], [x + 1, 35 - drop, -9.25], f"herbs_{i % 3}",
               lambda W, Hh, c, f=fl: H.P.leafy(R["moss"], W, Hh, c, f))
    # hanging sign on the left, lantern on the right
    hang_sign(H, "potion_sign", g["sign"], -27, -19.5, -10.5, 33, "potion", board=(7, 7), wood="walnut")
    H.lantern("lantern", g["details"], "north", -12, 16, 24)
    # glowing mushrooms at the front left corner of the plinth, a crate of spare bottles at the right
    dt = g["details"]
    for i, (x, z, hgt, cap) in enumerate(((-23, -11, 3, 3), (-24.5, -8.5, 2, 2), (-22, -7.5, 1.5, 1.5))):
        H.item(f"mushroom_{i + 1}_stem", dt, [x - 0.5, 0, z - 0.5], [x + 0.5, hgt, z + 0.5], "mstem", lambda W, Hh, c: H.P.form(R["candle"], W, Hh, c, 4.0))
        H.item(f"mushroom_{i + 1}_cap_glow", dt, [x - cap / 2, hgt, z - cap / 2], [x + cap / 2, hgt + 1, z + cap / 2], "mcap",
               lambda W, Hh, c: H.P.pile(R["glow_cyan"], W, Hh, c, r=0.5, stem=False, gap=R["glow_cyan"]), hide=())
    H.item("crate_bottles", dt, [21.5, 0, -9], [26.5, 4, -4], "crate_pine_wood", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c))
    for i, (x, z, gl) in enumerate(((23, -7.5, "glow_pink"), (25, -6, "glow_green"), (23.5, -5.5, "glow_cyan"))):
        bottle(dt, x, 3.5, z, "flask", gl)
    barrel(H, "barrel", dt, 24, 4, 5, 7, wood="walnut")
    return H


# ==================================================================== 4. cloth stall (grand teal and gold tent)
def market_stall_cloth():
    A, B = R["teal_cloth"], R["canvas"]
    H = Stall("market_stall_cloth", 3404, stall_mats(post="paint_teal", plank="oak", top="walnut", trim="gold",
              trim_kind="carved", extra={
                  "deck": {"kind": "boards", "ramp": R["oak"], "side": (120, 4), "top": (120, 64), "no_lit2": True,
                           "extra": {"bw": 3, "shadow_top": False}},
                  "cloth_a": flat_mat("teal_cloth"),
                  "pole": {"kind": "boards", "ramp": R["paint_teal"], "side": (16, 112), "top": (8, 8), "no_lit2": True,
                           "extra": {"orient": "v", "bw": 2, "lap": False, "shadow_top": False}},
                  "rope": flat_mat("burlap", (16, 8))}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("deck", "frame", "tent", "counter", "goods", "rack", "sign", "details")}
    d = g["deck"]
    H.box("deck_boards", d, [-29, 0, -15], [29, 2, 15], "deck", ("down",), "deck", place="ground")
    for i, (zf, zb, hh) in enumerate(((-17, -15, 1), (-16, -15, 2))):
        pass
    H.box("deck_step", d, [-7, 0, -17.5], [7, 1, -15], "deck", ("down",), "step", place="ground")
    for s, x in (("left", -29), ("right", 28)):
        H.box(f"deck_rim_{s}", d, [x, 0, -15.5], [x + 1, 2.5, 15.5], "top", ("down",), "drim")
    # tent geometry: ridge at y 46, panels slope 30 degrees to the front and back
    yR, t, ang, L = 46.0, 0.5, 30.0, 17.0
    X1, X2 = -30, 30
    fr = g["frame"]
    for s, x in (("left", -27), ("right", 27)):
        for e, z in (("front", -13), ("back", 13)):
            top = floor2(H.under_y(yR, 0, z, ang, t) + 0.1)
            H.box(f"post_{e}_{s}", fr, [x - 1, 2, z - 1], [x + 1, top, z + 1], "post", ("down",), f"po{e}{s}")
            for i, yr in enumerate((2, top - 2)):
                H.box(f"post_{e}_{s}_ring_{i + 1}", fr, [x - 1.5, yr, z - 1.5], [x + 1.5, yr + 1, z + 1.5], "gold", (), "ring")
        H.box(f"pole_{s}", fr, [x - 1 + (-2 if x < 0 else 2) * 0 - 0.75 + (0 if x < 0 else 0), 2, -0.75], [x + 0.75, 56, 0.75], "pole", ("down",), "pole")
        H.box(f"pole_{s}_knob", fr, [x - 1.5, 56, -1.25], [x + 1, 58, 1.25], "gold", (), "pknob")
        H.box(f"pole_{s}_ring", fr, [x - 1.25, yR - 1.5, -1], [x + 0.75, yR + 1, 1], "gold", (), "pring")
        fk = H.rect(f"flag_{s}", px(8), px(4), lambda W, Hh: H.P.flag(R["rose"] if True else A, R["gold"], W, Hh, "lit"))
        fx = x + (0.75 if x > 0 else -0.25)
        H.card(f"flag_{s}", fr, [fx - (0 if x > 0 else 8), 51, 0], [fx + (8 if x > 0 else 0), 55, 0], fk,
               mirror_back=True if x > 0 else False)
    H.box("ridge_cap", fr, [X1 - 0.5, yR, -1.5], [X2 + 0.5, yR + 1.5, 1.5], "cloth_a", (), "rcap")
    H.box("ridge_pole", fr, [-28.25, yR - 0.5, -0.75], [28.25, yR + 1, 0.75], "top", (), "ridge")
    # tent panels: teal and cream stripes (gold pinstripe on the cream), zigzag valances with tassels
    tn = g["tent"]
    W = px(X2 - X1)
    topk, undk = awning_rects(H, "tent", A, B, W, px(L), 8, pin=R["gold"])
    yf, zf = H.slab("tent_front", tn, X1, X2, yR + 0.5, 0, L, ang, t, topk, undk, "cloth_a", toward=-1)
    yb_, zb_ = H.slab("tent_back", tn, X1, X2, yR + 0.5, 0.5, L, ang, 1.0, topk, undk, "cloth_a", toward=+1,
                      top_sub=None)
    vk = H.rect("tent_valance", W, 9, lambda Ww, Hh: H.P.valance(A, B, Ww, Hh, 8, 0, "zigzag", trim=R["gold"], pin=R["gold"]))
    H.card("valance_front", tn, [X1, yf - 4.5, zf - 0.05], [X2, yf, zf - 0.05], vk)
    H.card("valance_back", tn, [X1, yb_ - 4.5, zb_ + 0.6], [X2, yb_, zb_ + 0.6], vk, faces=("south", "north"))
    # gable drapes: stepped triangles of patterned teal cloth at both ends
    for s, x in (("left", X1 + 0.75), ("right", X2 - 0.75)):
        for k in range(4):
            hw = (zf * -1) * (1 - k / 4) - 0.5
            y1 = yf - 1 + k * (yR - yf) / 4; y2 = y1 + (yR - yf) / 4 + 0.5
            y1, y2, hw = h2(y1), h2(y2), h2(hw)
            H.item(f"gable_drape_{s}_{k + 1}", tn, [x - 0.25, y1, -hw], [x + 0.25, y2, hw], "gable_cloth",
                   lambda Ww, Hh, c: H.P.cloth(A, Ww, Hh, c, "damask", R["gold"], 6, hem=False), hide=())
    # tied-back curtains at the front posts
    for s, x, sg in (("left", -27, 1), ("right", 27, -1)):
        cg = H.group(f"curtain_{s}", [x, 38, -13], tn)
        top = floor2(H.under_y(yR, 0, -13, ang, t))
        H.item(f"curtain_{s}_upper", cg, [x + sg * 1 - (4 if sg < 0 else 0), 18, -14.75], [x + sg * 1 + (4 if sg > 0 else 0), top, -13.75], "curtain_up",
               lambda Ww, Hh, c: H.P.cloth(A, Ww, Hh, c, "damask", R["gold"], 4, hem=False))
        H.box(f"curtain_{s}_tie", cg, [x + sg * 1 - (3.5 if sg < 0 else 0) - 0.25, 17, -15], [x + sg * 1 + (3.5 if sg > 0 else 0) + 0.25, 18.5, -13.5], "gold", (), "tie")
        H.item(f"curtain_{s}_lower", cg, [x + sg * 1 - (5 if sg < 0 else 0), 2.5, -14.75], [x + sg * 1 + (5 if sg > 0 else 0), 17, -13.75], "curtain_low",
               lambda Ww, Hh, c: H.P.cloth(A, Ww, Hh, c, "damask", R["gold"], 3, fringe=True))
    # bunting from each pole top down to the front corner post
    for s, x in (("left", -27), ("right", 27)):
        p0 = np.array([x, 54.0, -0.5]); p1 = np.array([x, floor2(H.under_y(yR, 0, -13, ang, t)) - 1.5, -13.0])
        dv = p1 - p0; Ld = float(np.linalg.norm(dv)); a = math.degrees(math.atan2(-dv[1], -dv[2]))
        mid = (p0 + p1) / 2
        Lr = h2(Ld)
        H.box(f"bunting_{s}_rope", tn, [x - 0.25, mid[1] - 0.25, mid[2] - Lr / 2], [x + 0.25, mid[1] + 0.25, mid[2] + Lr / 2], "rope", (),
              "rope", rot=(-a, 0, 0), origin=list(mid))
        cols = ["rose", "awn_honey", "indigo", "emerald", "coral"]
        for i in range(5):
            f = (i + 0.7) / 5.6
            p = p0 + dv * f
            pk = H.rect(f"pennant_{cols[i]}", 4, 5, lambda Ww, Hh, r_=cols[i]: H.P.pennant(R[r_], Ww, Hh, "lit"))
            H.card(f"bunting_{s}_pennant_{i + 1}", tn, [x, p[1] - 2.5, p[2] - 1], [x, p[1], p[2] + 1], pk, faces=("east", "west"))
    # counter: draped table with legs, fabric stacks and spools
    cn = g["counter"]
    for s, x in (("left", -20.5), ("right", 20.5)):
        for e, z in (("front", -11), ("back", -7.5)):
            H.box(f"table_leg_{e}_{s}", cn, [x - 0.5, 2, z - 0.5], [x + 0.5, 6, z + 0.5], "top", ("down",), "tleg")
    H.item("tablecloth", cn, [-22.5, 6, -12.5], [22.5, 11.5, -6.5], "tablecloth",
           lambda Ww, Hh, c: H.P.cloth(R["rose"], Ww, Hh, c, "diamond", R["gold"], 5, fringe=True))
    H.box("tablecloth_band", cn, [-22.75, 9.5, -12.75], [22.75, 10.5, -6.25], "gold", ("up", "down"), "tband")
    gd = g["goods"]
    stacks = [(-18, ["indigo", "awn_honey", "rose", "emerald"]), (-10.5, ["coral", "canvas", "indigo"]),
              (-3, ["emerald", "rose", "awn_honey", "glow_violet", "canvas"]), (4.5, ["teal_cloth", "coral", "awn_honey"]),
              (12, ["grape", "canvas", "rose", "indigo"])]
    for si, (x, cols) in enumerate(stacks):
        y = 11.5
        for li, col in enumerate(cols):
            dx = ((li * 37 + si * 11) % 3 - 1) * 0.5
            hh = 1.0 if li % 2 else 1.5
            H.item(f"fabric_stack_{si + 1}_{li + 1}", gd, [x - 3 + dx, y, -11.5], [x + 3 + dx, y + hh, -7.5], f"fold_{col}_{hh}",
                   lambda Ww, Hh, c, r_=col: H.P.cloth(R[r_], Ww, Hh, c, "stripe" if c == "lit" else None, R["gold"], 3, hem=False))
            y += hh
    for i, (x, col) in enumerate(((17, "rose"), (19, "awn_honey"), (21, "indigo"))):
        sp = H.group(f"spool_{i + 1}", [x, 11.5, -9.5], gd)
        H.box(f"spool_{i + 1}_base", sp, [x - 0.75, 11.5, -10.25], [x + 0.75, 12, -8.75], "plank", (), "spl")
        H.item(f"spool_{i + 1}_thread", sp, [x - 0.5, 12, -10], [x + 0.5, 13.5, -9], f"thread_{col}",
               lambda Ww, Hh, c, r_=col: H.P.bolt(R[r_], Ww, Hh, c), hide=("down", "up"))
        H.box(f"spool_{i + 1}_top", sp, [x - 0.75, 13.5, -10.25], [x + 0.75, 14, -8.75], "plank", (), "spl")
    # back: bolt rack with upright bolts, rail of hanging fabrics
    rk = g["rack"]
    H.box("rack_base", rk, [-21, 2, 8], [21, 4, 12], "plank", ("down",), "rbase")
    H.box("rack_back", rk, [-21, 4, 11], [21, 20, 12], "plank", ("down",), "rback")
    H.box("rack_rail", rk, [-21, 14, 7.5], [21, 15, 8], "top", (), "rrail")
    bcols = ["rose", "awn_honey", "indigo", "emerald", "coral", "grape", "teal_cloth", "canvas", "awn_red"]
    motifs = ["damask", None, "stripe", "polka", None, "check", "damask", "stripe", None]
    for i, col in enumerate(bcols):
        x = -18 + i * 4.5
        lean = [3.75, -3.75, 0, 3.75, 0, -3.75, 3.75, 0, -3.75][i]
        H.item(f"bolt_{i + 1}", rk, [x - 1.5, 4, 8.5], [x + 1.5, 18 + (i % 3) * 1.0, 11], f"bolt_{col}_{i % 3}",
               lambda Ww, Hh, c, r_=col, m=motifs[i]: H.P.bolt(R[r_], Ww, Hh, c, m), rot=(0, 0, lean), origin=[x, 4, 9.75])
    hr = H.group("fabric_rail", [0, 34, 12], rk)
    H.box("fabric_rail_bar", hr, [-27, 33.5, 12.5], [27, 34.5, 13.5], "top", (), "frail")
    for i, (x, col, mot) in enumerate(((-21, "indigo", "damask"), (-13, "awn_honey", "check"), (-5, "rose", "polka"),
                                       (3, "emerald", "diamond"), (11, "coral", "stripe"), (19, "grape", "damask"))):
        hw = 3.5; hgt = 12 + (i % 2) * 2.5
        fk = H.rect(f"hanging_{col}", px(2 * hw), px(hgt), lambda Ww, Hh, r_=col, m=mot: H.P.cloth(R[r_], Ww, Hh, "lit", m, R["gold"], 4, fringe=True))
        H.card(f"hanging_fabric_{i + 1}", hr, [x - hw, 33.5 - hgt, 12.75], [x + hw, 33.5, 12.75], fk)
    # rolled rugs leaning in the left corner
    for i, (x, z, col, lean) in enumerate(((-24, 8, "awn_red", 15), (-24.5, 4.5, "indigo", 11.25), (-23.5, 1, "emerald", 18))):
        H.item(f"rug_{i + 1}", gd, [x - 1.25, 2, z - 1.25], [x + 1.25, 20, z + 1.25], f"rug_{col}",
               lambda Ww, Hh, c, r_=col: H.P.bolt(R[r_], Ww, Hh, c, "diamond"), rot=(0, 0, -lean), origin=[x, 2, z])
    # dress form with a gown at the front right
    dg = H.group("dress_form", [23, 2, -4], gd)
    H.box("dress_form_base", dg, [21, 2, -6], [25, 3, -2], "top", ("down",), "dfb")
    H.box("dress_form_pole", dg, [22.75, 3, -4.25], [23.25, 9, -3.75], "gold", (), "dfp")
    gown = lambda Ww, Hh, c: H.P.cloth(R["glow_violet"], Ww, Hh, c, "damask", R["gold"], 3, hem=True)
    for k, (w_, y1, y2) in enumerate(((7, 7, 10), (6, 10, 13), (5, 13, 15.5))):
        H.item(f"gown_skirt_{k + 1}", dg, [23 - w_ / 2, y1, -4 - w_ / 2 + 0.5], [23 + w_ / 2, y2, -4 + w_ / 2 - 0.5], f"gown_{k}", gown,
               hide=("down",) if k else ())
    H.box("gown_belt", dg, [20.75, 15.5, -5.75], [25.25, 16.5, -2.25], "gold", ("down",), "belt")
    H.item("gown_bodice", dg, [21, 16.5, -5.5], [25, 21, -2.5], "gown_b", gown)
    H.item("dress_form_neck", dg, [22.5, 21, -4.5], [23.5, 22.5, -3.5], "neck_form", lambda Ww, Hh, c: H.P.form(R["canvas"], Ww, Hh, c, 3.8))
    H.item("dress_form_cap", dg, [22, 22.5, -5], [24, 23.5, -3], "neck_cap", lambda Ww, Hh, c: H.P.form(R["walnut"], Ww, Hh, c, 3.6))
    # hanging shop sign under the front valance and lanterns on the back posts
    sg = g["sign"]
    sk = H.rect("sign_spool", px(10), px(6), lambda Ww, Hh: H.P.sign(R["walnut"], Ww, Hh, "lit", "spool", frame=R["gold"]))
    for i, xx in enumerate((-3.5, 3.5)):
        H.box(f"sign_chain_{i + 1}", sg, [xx - 0.25, yf - 6.5, -13.75], [xx + 0.25, yf - 2, -13.25], "iron", (), "sch")
    fs = H.faces([-5, yf - 12.5, -13.75], [5, yf - 6.5, -13.25], "top", ())
    fs["north"] = F(sk); fs["south"] = F(sk, mirror=True)
    H.m.cube("shop_sign", sg, [-5, yf - 12.5, -13.75], [5, yf - 6.5, -13.25], fs)
    for s, x in (("left", -27), ("right", 27)):
        H.lantern(f"lantern_{s}", g["details"], "north", 12, x, 22)
    return H


BUILDERS = {f.__name__: f for f in (market_stall_fruit, market_stall_bakery, market_stall_potion, market_stall_cloth)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        BUILDERS[n]().finish([OUT])
