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
  market_stall_merchant the merchant's stall at the end of Market Street: walnut and cream plaster booth, red clay
                       tile roof, a cross gable with a round coin sign, three-part indigo / cream awning; it buys
                       ore, ingots, gems, hides, logs and herbs, and sells bags, energy refills, hilts and cosmetics
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


# ==================================================================== 5. the merchant's stall (the market's focal piece)
def market_stall_merchant():
    """The merchant's stall at the east end of Market Street (J00BA, 2026-11-15; prompts/merchant_stall_blockbench_prompt.md):
    walnut and cream plaster timber booth on a cobble plinth, red clay tile roof with a front cross gable holding a round
    coin sign, a three-part indigo and cream awning, three bays. Customer's left (+x) bay_buy shows what the merchant buys
    (ore, ingots, gems, hides, logs, herbs, leather, seeds, trophies), the centre bay_coin is the merchant's desk (scale,
    coins, ledger) with room behind it for the merchant NPC, and the customer's right (-x) bay_sell shows what the
    merchant sells (bags, energy refills, wood hilts, cosmetics), as in docs/02-resources.md D-073 to D-077."""
    from stall_lib import DIMS
    A, B = R["awn_indigo"], R["canvas"]
    mats = stall_mats(post="walnut", plank="oak", top="walnut", trim="gold",
              trim_kind="carved", extra={
                  "plinth": {"kind": "cobble", "ramp": R["cobble"], "side": (80, 8), "top": (80, 64), "no_lit2": True},
                  "roof": {"kind": "shingle", "ramp": R["tile_red"], "side": (96, 40), "top": (96, 48), "under": (96, 48),
                           "no_lit2": True, "extra": {"style": "clay_curved"}},
                  "wall": {"kind": "plaster", "ramp": R["plaster"], "side": (64, 24), "top": (16, 16), "no_lit2": True},
                  "plain": flat_mat("plaster", (72, 48)),
                  "cloth_a": flat_mat("awn_indigo"),
                  "moss": flat_mat("moss", (24, 8)),
              })
    del mats["stone"]                                            # the post bases use the plinth's cobble instead
    H = Stall("market_stall_merchant", 3505, mats)
    g = {k: H.group(k, [0, 0, 0]) for k in ("booth", "roofs", "awning", "counter", "bay_buy", "bay_coin", "bay_sell", "sign",
                                            "details")}
    bo, ro, aw, cn, bb, bc, bs, sg, dt = (g[k] for k in ("booth", "roofs", "awning", "counter", "bay_buy", "bay_coin", "bay_sell",
                                                          "sign", "details"))
    FACES6 = ("north", "east", "south", "west", "up", "down")

    def panel(name, grp, frm, to, painted, plain=()):
        """A cream plaster panel set between timbers: painted faces darken toward the frame; `plain` faces get the
        back swatch; every other face is pressed against a timber and hidden."""
        frm = [float(v) for v in frm]; to = [float(v) for v in to]
        fs = {f: None for f in FACES6}
        for f, cat in painted.items():
            a, b = DIMS[f]; w, h = px(to[a] - frm[a]), px(to[b] - frm[b])
            fs[f] = F(H.rect(f"panel_{cat}_{w}x{h}", w, h, lambda W, Hh, c=cat: H.P.panel(R["plaster"], W, Hh, c)))
        for f in plain:
            a, b = DIMS[f]; fs[f] = H.crop("plain_shade", px(to[a] - frm[a]), px(to[b] - frm[b]))
        return H.m.cube(name, grp, frm, to, fs)

    def form_item(name, grp, frm, to, rm, base=3.4, hl=False, hide=("down",), rot=(0, 0, 0), origin=None, tag=None):
        return H.item(name, grp, frm, to, tag or f"form_{rm}_{base}", lambda W, Hh, c: H.P.form(R[rm], W, Hh, c, base, hl=hl),
                      hide=hide, rot=rot, origin=origin)

    def rod(name, grp, p, q, mat="iron", wdt=0.5):
        """A thin bar from p to q (both (x, y, z) with the same x): a box along -z rotated about x."""
        dy, dz = q[1] - p[1], q[2] - p[2]
        L = h2(math.hypot(dy, dz)); ang = math.degrees(math.atan2(dy, -dz))
        H.box(name, grp, [p[0] - wdt / 2, p[1] - wdt / 2, p[2] - L], [p[0] + wdt / 2, p[1] + wdt / 2, p[2]], mat, (), f"rod_{name}",
              rot=(ang, 0, 0), origin=list(p))

    # ---------------------------------------------------------------- booth: plinth, timber frame, plaster panels
    for k, (x1, x2) in enumerate(((-39, -13), (-13, 13), (13, 39))):
        H.box(f"plinth_{k + 1}", bo, [x1, 0, -14], [x2, 2, 16], "plinth", ("down",), f"plinth{k}", place="ground")
    H.box("plinth_step", bo, [-20, 0, -16], [20, 1, -14], "plinth", ("down", "south"), "pstep", place="ground")
    # back wall: three walnut posts, a sill, a mid rail at y 24, a top beam; plaster panels 0.5 back between them
    back = {"south": "plain"}
    H.box("back_sill", bo, [-37, 2, 12], [37, 4, 16], "top", ("down",), "bsill", over=back)
    for s, (x1, x2) in (("right", (-37, -34)), ("centre", (-1.5, 1.5)), ("left", (34, 37))):
        H.box(f"back_post_{s}", bo, [x1, 4, 12], [x2, 42, 16], "post", ("down", "up"), f"bp{s}", over=back)
    for s, (x1, x2) in (("right", (-34, -1.5)), ("left", (1.5, 34))):
        H.box(f"back_rail_{s}", bo, [x1, 23, 12], [x2, 25, 16], "top", (), f"br{s}", over=back)
        for r_, (y1, y2) in (("low", (4, 23)), ("high", (25, 42))):
            panel(f"back_panel_{s}_{r_}", bo, [x1, y1, 12.5], [x2, y2, 16], {"north": "lit"}, plain=("south",))
    H.box("back_beam", bo, [-37, 42, 12], [37, 46, 16], "top", (), "bbeam", over=back)
    # side walls (x 35..37 and -37..-35, z -4..12): a front corner post, sill, rail, top beam, panels, an arched window
    for s, sx in (("left", 1), ("right", -1)):
        out_lo, out_hi = (34.5, 37.5) if sx > 0 else (-37.5, -34.5)
        outer, inner = ("east", "west") if sx > 0 else ("west", "east")
        H.box(f"side_post_{s}", bo, [out_lo, 2, -4.5], [out_hi, 46, -1.5], "post", ("down",), f"sp{s}")
        H.box(f"side_sill_{s}", bo, [out_lo, 2, -1.5], [out_hi, 4, 12], "top", ("down",), f"ss{s}")
        H.box(f"side_rail_{s}", bo, [out_lo + 0.25, 23, -1.5], [out_hi - 0.25, 25, 12], "top", (), f"sr{s}")
        H.box(f"side_beam_{s}", bo, [out_lo, 42, -1.5], [out_hi, 46, 12], "top", (), f"sb{s}")
        pl_lo, pl_hi = (35, 37) if sx > 0 else (-37, -35)
        for r_, (y1, y2) in (("low", (4, 23)), ("high", (25, 42))):
            panel(f"side_panel_{s}_{r_}", bo, [pl_lo, y1, -1.5], [pl_hi, y2, 12], {outer: "lit", inner: "shade"})
        H.window(f"side_window_{s}", bo, outer, 37 * sx, 5.25, 28, 6, 10, frame_ramp=R["paint_cream"], style="leaded",
                 arch=True, sill="trim", lintel="trim", shutters="awn_indigo", glow=True)
    # four front posts on stone bases with gold carved capitals: they split the front into three bays
    for s, x in (("right_outer", -36), ("right_inner", -13), ("left_inner", 13), ("left_outer", 36)):
        H.box(f"front_post_{s}", bo, [x - 1.5, 2, -12], [x + 1.5, 44, -9], "post", ("down",), f"fp{s}")
        H.box(f"front_post_{s}_base", bo, [x - 2, 2, -12.5], [x + 2, 4, -8.5], "plinth", ("down",), "fpb")
        H.box(f"front_post_{s}_capital", bo, [x - 2, 40, -12.5], [x + 2, 41.5, -8.5], "trim", (), "fpc")
    H.box("front_beam", bo, [-38, 42, -12.5], [38, 46, -8.5], "top", (), "fbeam")
    H.box("front_beam_band", bo, [-38, 43, -13], [38, 45, -12.5], "trim", ("south", "down"), "fband")

    # ---------------------------------------------------------------- roofs: red clay tiles, a front cross gable, the crest
    prof = [(0, 2)] + [(2.5, 2.5)] * 6
    H.roof("roof_main", ro, -40, 40, -12.5, 16, 46, prof, "roof", "post", axis="x", eave=3, ridge=("gold", 3, 1.5),
           finials=("gold", 4))
    for e in H.m.elements:                                       # the back slope against the town wall: the plain swatch
        if e["name"].startswith("roof_main_layer") and e["faces"]["south"].get("_spec"):
            w, h = px(e["to"][0] - e["from"][0]), px(e["to"][1] - e["from"][1])
            e["faces"]["south"]["_spec"] = H.crop("plain_shade", w, h)
    H.box("roof_moss_patch_1", ro, [28, 48, -15.5], [34, 48.5, -13], "moss", ("down",), "rmoss")         # moss on two
    H.box("roof_moss_patch_2", ro, [29, 50.5, -13], [32.5, 51, -10.5], "moss", ("down",), "rmoss")       # steps near one eave
    gprof = [(0, 3)] + [(2, 3)] * 7
    top = H.roof("roof_gable", ro, -14, 14, -15.5, 2, 46, gprof, "roof", "wall", axis="z", eave=1.5, ridge=("gold", 2, 1.5),
                 crest=("gold", 4))
    H.box("crest_finial", ro, [-0.5, top, -16.25], [0.5, top + 4.5, -15.25], "gold", ("down",), "cfin")
    ck = H.rect("crest_coin", 8, 8, lambda W, Hh: H.P.coin_face(W, Hh))
    H.card("crest_coin", ro, [-2, 74, -16.5], [2, 78, -16.5], ck)

    # ---------------------------------------------------------------- the round coin sign on the cross gable's plaster face
    sy = 53
    H.card("coin_sign_backing", sg, [-7.5, sy - 7.5, -15.75], [7.5, sy + 7.5, -15.75],
           H.rect("coin_sign_ring", 30, 30, lambda W, Hh: H.P.coin_badge(W, Hh, ring=True)), faces=("north",))
    H.card("coin_sign_board", sg, [-7, sy - 7, -16], [7, sy + 7, -16],
           H.rect("coin_sign_face", 28, 28, lambda W, Hh: H.P.coin_badge(W, Hh)), faces=("north",))
    H.card("coin_sign_coin", sg, [-3.5, sy - 3.5, -16.5], [3.5, sy + 3.5, -16.5],
           H.rect("coin_sign_coin", 14, 14, lambda W, Hh: H.P.coin_face(W, Hh)), faces=("north",))

    # ---------------------------------------------------------------- awning: three indigo / cream panels, one per bay
    y0, z0, t, ang, L = 42, -12.5, 0.5, 30.0, 16
    top_k, und_k = awning_rects(H, "awn", A, B, 49, px(L), 6, pin=R["gold"])
    vk = H.rect("valance_front", 49, 8, lambda Ww, Hh: H.P.valance(A, B, Ww, Hh, 6, 0, "scallop", trim=R["gold"]))
    sk = H.rect("valance_side", px(L), 5, lambda Ww, Hh: H.P.valance(A, B, Ww, Hh, 6, 0, "scallop", trim=R["gold"], cut=2))
    for s, (x1, x2) in (("right", (-38, -13.5)), ("centre", (-12.25, 12.25)), ("left", (13.5, 38))):
        yf, zf = H.slab(f"awning_{s}", aw, x1, x2, y0, z0, L, ang, t, top_k, und_k, "cloth_a")
        H.card(f"awning_{s}_valance", aw, [x1, yf - 4, zf - 0.05], [x2, yf, zf - 0.05], vk)
        for e_, x in (("a", x1 - 0.05), ("b", x2 + 0.05)):
            H.card(f"awning_{s}_cheek_{e_}", aw, [x, y0 - t - 2.5, z0 - L], [x, y0 - t, z0], sk, faces=("east", "west"),
                   rot=(-ang, 0, 0), origin=[x, y0, z0])
    for s, x in (("right", -12.875), ("left", 12.875)):                          # iron rods from the posts up to the edge
        rod(f"awning_rod_{s}", aw, (x, 30, -12), (x, 34.0, -24.5))

    # ---------------------------------------------------------------- counter: oak boards in three sections, walnut tops
    for s, (x1, x2, t1, t2) in (("sell", (-35, -14.5, -36, -14.5)), ("coin", (-11.5, 11.5, -11.5, 11.5)),
                                ("buy", (14.5, 35, 14.5, 36))):
        H.box(f"counter_{s}_body", cn, [x1, 2, -11], [x2, 13, -6], "plank", ("down", "up"), f"cb{s}", place="ground")
        H.box(f"counter_{s}_top", cn, [t1, 13, -12], [t2, 14, -5], "top", (), f"ct{s}")
        H.box(f"counter_{s}_band", cn, [x1, 9.5, -11.5], [x2, 11, -11], "trim", ("south", "down"), f"cband{s}")
        H.box(f"counter_{s}_base", cn, [x1, 2, -11.5], [x2, 3.5, -11], "trim", ("south",), f"cbase{s}")
    pk = H.rect("coin_panel", px(8), px(6), lambda W, Hh: H.P.sign(R["walnut"], W, Hh, "lit", "coin", frame=R["gold"]))
    fs = H.faces([-4, 3.5, -12], [4, 9.5, -11], "trim", ("south", "down"), "cpan"); fs["north"] = F(pk)
    H.m.cube("counter_coin_panel", cn, [-4, 3.5, -12], [4, 9.5, -11], fs)
    # back shelves on iron brackets: two rows (y 22, y 32) in bay_buy and in bay_sell (the mirror shares bay_sell's wall)
    for bay, grp, (x1, x2) in (("buy", bb, (16, 33)), ("sell", bs, (-33, -24))):
        for r_, ys in (("low", 22), ("high", 32)):
            H.box(f"shelf_{bay}_{r_}", grp, [x1, ys - 1, 9], [x2, ys, 12], "top", (), f"sh{bay}")
            for e_, x in (("a", x1 + 1.5), ("b", x2 - 1.5)):
                H.box(f"shelf_{bay}_{r_}_bracket_{e_}", grp, [x - 0.5, ys - 3, 11], [x + 0.5, ys - 1, 12], "iron", (), "sbr")

    # ---------------------------------------------------------------- bay_buy (+x): what the merchant buys
    # an open crate of ore nuggets: copper, tin and iron side by side, a few loose nuggets on top
    H.item("ore_crate", bb, [15.5, 14, -11], [22.5, 17, -6], "crate_oak", lambda W, Hh, c: H.P.crate(R["oak"], W, Hh, c))
    for i, (rm, x) in enumerate((("ore_copper", 16), ("ore_tin", 18.5), ("iron", 20))):
        H.item(f"ore_pile_{i + 1}", bb, [x, 16, -10.5], [x + 2.5 if i < 2 else 22, 17.5, -6.5], f"pile_{rm}",
               lambda W, Hh, c, r_=rm: H.P.pile(R[r_], W, Hh, c, r=1.0, stem=False, gap=R["oak"]))
    for i, (rm, x, z, yaw) in enumerate((("ore_copper", 17, -9, 22.5), ("ore_tin", 19.25, -7.5, -22.5), ("iron", 21, -9.5, 45))):
        form_item(f"ore_nugget_{i + 1}", bb, [x - 0.75, 17.5, z - 0.75], [x + 0.75, 18.5, z + 0.75], rm, 3.6, hl=True,
                  rot=(0, yaw, 0), origin=[x, 17.5, z])
    # a criss-cross stack of seven ingots: copper, iron and gold (light top bevel)
    ingot = lambda rm: (lambda W, Hh, c: H.P.ingot(R[rm], W, Hh, c))
    stack = [("x", 24, 30, -10.5, -8.5, 14, "ingot_copper"), ("x", 24, 30, -8, -6, 14, "ingot_iron"),
             ("z", 24.5, 26.5, -10.75, -5.75, 15.5, "ingot_gold"), ("z", 27.5, 29.5, -10.75, -5.75, 15.5, "ingot_copper"),
             ("x", 24, 30, -10.25, -8.25, 17, "ingot_iron"), ("x", 24, 30, -8.25, -6.25, 17, "ingot_gold"),
             ("z", 26, 28, -10.5, -5.5, 18.5, "ingot_gold")]
    for i, (_, x1, x2, z1, z2, y, rm) in enumerate(stack):
        H.item(f"ingot_{i + 1}", bb, [x1, y, z1], [x2, y + 1.5, z2], f"ingot_{rm}", ingot(rm))
    # a small open box of cut gems on red velvet
    H.item("gem_box", bb, [31, 14, -10.5], [35, 15.5, -7], "gem_box", lambda W, Hh, c: H.P.form(R["walnut"], W, Hh, c, 3.6))
    H.item("gem_box_velvet", bb, [31.5, 15.5, -10], [34.5, 16, -7.5], "velvet", lambda W, Hh, c: H.P.form(R["awn_red"], W, Hh, c, 2.8),
           hide=("down", "north", "south", "east", "west"))
    for i, (rm, x, z) in enumerate((("gem_ruby", 32, -9.25), ("gem_sapphire", 33.5, -9), ("gem_emerald", 32.75, -8),
                                    ("gem_ruby", 34, -8))):
        H.item(f"gem_{i + 1}", bb, [x - 0.5, 16, z - 0.5], [x + 0.5, 17, z + 0.5], f"gem_{rm}",
               lambda W, Hh, c, r_=rm: H.P.gem(R[r_], W, Hh, c), rot=(0, 45, 0), origin=[x, 16, z])
    # hides on pegs: wolf and boar on the left side wall, fox draped over the counter front
    for i, (rm, z1, z2, y1, y2) in enumerate((("hide_wolf", -1, 5.5, 8, 21), ("hide_boar", 5.5, 11.5, 9, 21))):
        key = H.rect(f"pelt_{rm}", px(z2 - z1), px(y2 - y1), lambda W, Hh, r_=rm: H.P.pelt(R[r_], W, Hh, "lit", belly=r_ != "hide_boar"))
        H.card(f"hide_{rm.split('_')[1]}", bb, [37.75, y1, z1], [37.75, y2, z2], key, faces=("east", "west"))
        zc = (z1 + z2) / 2
        H.box(f"hide_{rm.split('_')[1]}_peg", bb, [37.5, y2 - 1, zc - 0.5], [38.5, y2, zc + 0.5], "top", ("west",), "hpeg")
    key = H.rect("pelt_hide_fox", 14, 18, lambda W, Hh: H.P.pelt(R["hide_fox"], W, Hh, "lit"))
    H.card("hide_fox", bb, [26.5, 5, -12.1], [33.5, 14, -12.1], key)
    # on the floor beside the bay: three logs (oak, ash) with painted end rings, a sack spilling ore
    rk = H.rect("log_ring_6x6", 6, 6, lambda W, Hh: H.P.log_ring(W, Hh, "lit"))
    for i, (rm, x, y) in enumerate((("bark_oak", 40.5, 0), ("bark_ash", 44, 0), ("bark_oak", 42.25, 3))):
        H.item(f"log_{i + 1}", bb, [x - 1.5, y, -8], [x + 1.5, y + 3, 1], f"log_{rm}",
               lambda W, Hh, c, r_=rm: H.P.log_side(R[r_], W, Hh, c), hide=("down",) if y == 0 else (),
               over={"north": F(rk), "south": F(rk, mirror=True)})
    H.item("ore_sack", bb, [40, 0, -13.5], [44, 5, -10], "sack", lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c),
           rot=(0, 0, 11.25), origin=[40, 0, -11.75])
    for i, (rm, x, z) in enumerate((("ore_copper", 39.25, -14.5), ("iron", 40.75, -15.25), ("ore_tin", 42.5, -14.75))):
        form_item(f"ore_spilled_{i + 1}", bb, [x - 0.75, 0, z - 0.75], [x + 0.75, 1, z + 0.75], rm, 3.4, hl=True,
                  rot=(0, 30 * i, 0), origin=[x, 0, z])
    # two dried herb bundles hanging from the front beam (nettle and marigold, bundle_ icons)
    for i, (x, rm) in enumerate(((21, "herb_nettle"), (29, "herb_marigold"))):
        hg = H.group(f"herb_bundle_{i + 1}", [x, 42, -10.5], bb)
        drop = 3.5 + i
        H.box(f"herb_bundle_{i + 1}_string", hg, [x - 0.25, 42 - drop, -10.75], [x + 0.25, 42, -10.25], "iron", (), "hstr")
        form_item(f"herb_bundle_{i + 1}_tie", hg, [x - 0.75, 41 - drop, -11.25], [x + 0.75, 42 - drop, -9.75], "burlap", 3.6, hide=())
        H.item(f"herb_bundle_{i + 1}_leaves", hg, [x - 1.25, 36.5 - drop, -11.5], [x + 1.25, 41 - drop, -9.5], f"herbs_{rm}",
               lambda W, Hh, c, r_=rm: H.P.form(R[r_], W, Hh, c, 3.4, noise=0.35, vert=0.8), hide=())
    # on the back shelves: rolled leather, a jar of seeds, a wolf fang and a golden antler (trophy_ icons)
    for i, (x, ys) in enumerate(((18, 22), (24.5, 32))):
        H.item(f"leather_roll_{i + 1}", bb, [x, ys, 9.5], [x + 6, ys + 2.5, 12], "leather_roll",
               lambda W, Hh, c: H.P.form(R["hide_boar"], W, Hh, c, 3.4, vert=0.8),
               over={"east": F(H.rect("leather_roll_end", 5, 5, lambda W, Hh: H.P.log_ring(W, Hh, "lit")))})
    H.item("seed_jar", bb, [26, 22, 9.5], [29, 26, 12], "seed_jar", lambda W, Hh, c: H.P.glass(R["glass"], W, Hh, c, glow=False))
    H.item("seed_jar_seeds", bb, [26.5, 22.5, 10], [28.5, 24.5, 11.5], "seed_pile",
           lambda W, Hh, c: H.P.pile(R["seed_gold"], W, Hh, c, r=0.75, stem=False, gap=R["seed_gold"]), hide=("down",))
    form_item("seed_jar_lid", bb, [25.75, 26, 9.25], [29.25, 26.5, 12.25], "cork", 3.6)
    fg = H.group("trophy_wolf_fang", [19, 32, 10.5], bb)
    form_item("trophy_wolf_fang_tooth", fg, [18.5, 32, 10], [19.5, 35.5, 11], "fang", 4.2, hl=True, rot=(0, 0, -22.5),
              origin=[19, 32, 10.5])
    form_item("trophy_wolf_fang_cord", fg, [17, 32, 10.25], [21, 32.5, 10.75], "hide_boar", 3.4)
    ag = H.group("trophy_golden_antler", [31, 32, 10.5], bb)
    form_item("trophy_golden_antler_beam", ag, [30.5, 32, 10], [31.5, 38, 11], "seed_gold", 4.0, hl=True, rot=(0, 0, 11.25),
              origin=[31, 32, 10.5])
    for k, (yb_, roll) in enumerate(((34, -45), (36, -40))):
        form_item(f"trophy_golden_antler_tine_{k + 1}", ag, [30.25, yb_, 10.25], [30.75, yb_ + 2.5, 10.75], "seed_gold", 4.4,
                  rot=(0, 0, roll), origin=[30.5, yb_, 10.5])

    # ---------------------------------------------------------------- bay_coin (centre): the merchant's desk
    for i, (x, z, hh) in enumerate(((7.5, -10.75, 3.5), (9.5, -10.5, 2), (11, -9.5, 4.5), (7.75, -8.75, 1.5), (9.75, -8.5, 3))):
        H.item(f"coin_stack_{i + 1}", bc, [x - 0.75, 14, z - 0.75], [x + 0.75, 14 + hh, z + 0.75], "coins",
               lambda W, Hh, c: H.P.coins(W, Hh, c))
    chg = H.group("coin_chest", [4, 14, -7], bc)
    H.item("coin_chest_box", chg, [1.5, 14, -8], [6.5, 17, -5.5], "chest", lambda W, Hh, c: H.P.crate(R["walnut"], W, Hh, c))
    H.item("coin_chest_heap", chg, [2, 16.5, -7.5], [6, 17.5, -6], "coin_heap",
           lambda W, Hh, c: H.P.pile(R["gold"], W, Hh, c, r=0.75, stem=False, gap=R["gold"]))
    H.box("coin_chest_lid", chg, [1.5, 17, -5.5], [6.5, 17.5, -2.5], "top", (), "clid", rot=(-67.5, 0, 0), origin=[4, 17, -5.5])
    H.box("ledger_cover", bc, [-2.5, 14, -11.5], [3.5, 14.5, -8], "top", ("down",), "lcover")
    bk = H.rect("ledger_pages", px(5), px(3), lambda W, Hh: H.P.pages(W, Hh, "up"))
    fs = H.faces([-2, 14.5, -11.25], [3, 15, -8.25], "top", ("down",), "lpages"); fs["up"] = F(bk)
    pg = H.rect("ledger_edge", 10, 1, lambda W, Hh: H.P.form(R["paper"], W, Hh, "lit", 4.0))
    for f in ("north", "south"): fs[f] = F(pg)
    pe = H.rect("ledger_edge_side", 6, 1, lambda W, Hh: H.P.form(R["paper"], W, Hh, "lit", 4.0))
    for f in ("east", "west"): fs[f] = F(pe)
    H.m.cube("ledger_pages", bc, [-2, 14.5, -11.25], [3, 15, -8.25], fs)
    form_item("ink_pot", bc, [-1, 14, -7.5], [0.5, 15.5, -6], "awn_indigo", 2.4)
    form_item("ink_pot_quill", bc, [-0.5, 15.5, -7], [0, 20, -6.5], "canvas", 4.6, hide=(), rot=(0, 0, -22.5),
              origin=[-0.25, 15.5, -6.75])
    # the brass balance scale: iron post, gold beam and pans on chains, the customer's left pan lower under an ingot
    scg = H.group("balance_scale", [-6.5, 14, -9], bc)
    H.box("balance_scale_base", scg, [-8, 14, -10.5], [-5, 15, -7.5], "iron", ("down",), "scbase")
    H.box("balance_scale_post", scg, [-6.75, 15, -9.25], [-6.25, 21, -8.75], "iron", (), "scpost")
    tilt = -8.0; dy = 3.5 * math.sin(math.radians(-tilt))
    H.box("balance_scale_beam", scg, [-10, 21, -9.25], [-3, 21.5, -8.75], "gold", (), "scbeam", rot=(0, 0, tilt), origin=[-6.5, 21.25, -9])
    for s, x, sy_ in (("left", -3.5, 21.25 - dy), ("right", -9.5, 21.25 + dy)):
        ch_lo = h2(sy_ - 4)
        H.box(f"balance_scale_chain_{s}", scg, [x - 0.25, ch_lo, -9.25], [x + 0.25, h2(sy_), -8.75], "iron", (), "scchain")
        H.box(f"balance_scale_pan_{s}", scg, [x - 1.5, ch_lo - 0.5, -10.5], [x + 1.5, ch_lo, -7.5], "gold", (), "scpan")
    H.item("balance_scale_ingot", scg, [-4.5, h2(21.25 - dy - 4), -9.75], [-2.5, h2(21.25 - dy - 4) + 1, -8.25], "ingot_ingot_gold",
           ingot("ingot_gold"))

    # ---------------------------------------------------------------- bay_sell (-x): what the merchant sells
    # bags for inventory space: a satchel on the counter, a backpack and a satchel hanging from hooks on the posts
    bag = lambda rm: (lambda W, Hh, c: H.P.bag(R[rm], W, Hh, c))
    H.item("satchel_counter", bs, [-20, 14, -10.5], [-15.5, 17.5, -7.5], "bag_hide_boar", bag("hide_boar"))
    form_item("satchel_counter_strap", bs, [-19.5, 17.5, -9.25], [-16, 18, -8.75], "hide_boar", 2.8, hide=())
    for s, (x, y1, y2, w_, rm) in (("backpack", (-36, 24, 31, 4, "hide_boar")), ("satchel", (-13, 26, 30, 3.5, "hide_boar"))):
        H.item(f"{s}_hanging", bs, [x - w_ / 2, y1, -14.5], [x + w_ / 2, y2, -12], f"bag_{rm}", bag(rm))
        H.box(f"{s}_hook", bs, [x - 0.25, y2, -12.5], [x + 0.25, y2 + 1.5, -12], "iron", (), "hook")
    # energy refills: a little rack of five stoppered flasks with a glowing warm gold drink (*_glow: emissive in Godot)
    H.box("flask_rack_base", bs, [-34, 14, -11], [-26, 15, -7.5], "top", ("down",), "frbase")
    H.box("flask_rack_back", bs, [-34, 15, -8], [-26, 19, -7.5], "top", (), "frback")
    for i, x in enumerate((-33, -31.5, -30, -28.5, -27)):
        H.item(f"energy_flask_{i + 1}_glow", bs, [x - 0.75, 15, -10.25], [x + 0.75, 18, -8.75], "energy_flask",
               lambda W, Hh, c: H.P.glass(R["glow"], W, Hh, c))
        form_item(f"energy_flask_{i + 1}_cork", bs, [x - 0.5, 18, -10], [x + 0.5, 18.5, -9], "cork", 3.6, hide=("down",))
    # wood hilts (hilt_ash_hilt, hilt_oak_hilt) on a small rack on the inside of the right side wall
    H.box("hilt_rack", bs, [-35, 25, 1], [-34.5, 32, 10], "top", ("west",), "hrack")
    for i, (rm, y) in enumerate((("hilt_ash", 26.5), ("hilt_oak", 29.5))):
        hg = H.group(f"hilt_{rm.split('_')[1]}", [-33.75, y, 5.5], bs)
        form_item(f"hilt_{rm.split('_')[1]}_grip", hg, [-34.5, y, 2], [-33.5, y + 1, 8.5], rm, 3.6, hide=("west",))
        form_item(f"hilt_{rm.split('_')[1]}_pommel", hg, [-34.5, y - 0.25, 8.5], [-33, y + 1.25, 10], "pommel", 3.8, hide=("west",))
        form_item(f"hilt_{rm.split('_')[1]}_collar", hg, [-34.5, y - 0.25, 1.5], [-33, y + 1.25, 2], "pommel", 3.4, hide=("west",))
    # cosmetics: a hat stand with a feathered cap and a top hat, a folded cloak on the counter, a mirror on the back wall
    hs = H.group("hat_stand", [-30, 2, 6], bs)
    H.box("hat_stand_base", hs, [-32, 2, 4], [-28, 3, 8], "top", ("down",), "hsb")
    H.box("hat_stand_pole", hs, [-30.5, 3, 5.5], [-29.5, 20, 6.5], "post", (), "hsp")
    H.box("hat_stand_arm", hs, [-34, 17, 5.75], [-29.5, 17.5, 6.25], "post", (), "hsa")
    form_item("hat_cap_crown", hs, [-32, 20.5, 4], [-28, 22.5, 8], "awn_red", 3.6)
    form_item("hat_cap_brim", hs, [-32.5, 20, 3], [-27.5, 20.5, 8.5], "awn_red", 3.0)
    form_item("hat_cap_feather", hs, [-28.75, 21.5, 5.75], [-28.25, 25.5, 6.25], "seed_gold", 4.4, hide=(), rot=(0, 0, -22.5),
              origin=[-28.5, 21.5, 6])
    form_item("hat_top_crown", hs, [-35.25, 14, 4.75], [-32.75, 17, 7.25], "awn_indigo", 3.4, hide=())
    form_item("hat_top_band", hs, [-35.5, 14, 4.5], [-32.5, 14.5, 7.5], "gold", 4.2)
    form_item("hat_top_brim", hs, [-36, 13.5, 4], [-32, 14, 8], "awn_indigo", 3.0, hide=())
    cloak = lambda W, Hh, c: H.P.cloth(R["emerald"], W, Hh, c, "damask", R["gold"], 3, hem=True)
    H.item("cloak_folded_1", bs, [-25, 14, -10.5], [-21, 15.5, -7], "cloak_1", cloak)
    H.item("cloak_folded_2", bs, [-24.5, 15.5, -10], [-21.5, 16.5, -7.5], "cloak_2", cloak)
    H.box("mirror_frame", bs, [-21, 24, 11.5], [-16.5, 32, 12], "gold", ("south",), "mframe")
    mk = H.rect("mirror_glass", 7, 14, lambda W, Hh: H.P.glass(R["glass"], W, Hh, "lit", glow=False))
    H.card("mirror_glass", bs, [-20.5, 24.5, 11.4], [-17, 31.5, 11.4], mk, faces=("north",))
    # spare stock on bay_sell's shelves: two pouches below, a folded cloth and a spare refill above
    for i, x in enumerate((-32, -28)):
        H.item(f"pouch_{i + 1}", bs, [x, 22, 9.5], [x + 3, 24.5, 11.5], "bag_hide_fox", bag("hide_fox"))
    H.item("cloth_folded_shelf", bs, [-32.5, 32, 9.5], [-28.5, 33.5, 11.5], "cloak_1", cloak)
    H.item("energy_flask_spare_glow", bs, [-26.75, 32, 10], [-25.25, 35, 11.5], "energy_flask", lambda W, Hh, c: H.P.glass(R["glow"], W, Hh, c))
    # the price board: a small chalkboard leaning back against the sell counter, coin marks for prices
    H.item("price_board", bs, [-34, 2, -13.5], [-28, 10, -13], "price_board", lambda W, Hh, c: H.P.chalk_coins(W, Hh, c),
           rot=(15, 0, 0), origin=[-31, 2, -13.25])

    # ---------------------------------------------------------------- details: lanterns, the ends, moss, ivy
    for s, x in (("left", 33), ("right", -33)):
        H.lantern_hang(f"lantern_{s}", dt, x, 42, -10.5, chain=3.0)
    H.item("rolled_rug", dt, [-42.5, 0, 3.5], [-40, 18, 6], "rug_awn_red", lambda W, Hh, c: H.P.bolt(R["awn_red"], W, Hh, c, "diamond"),
           rot=(0, 0, -11.25), origin=[-41.25, 0, 4.75])
    barrel(H, "barrel", dt, -42, 10, 5, 7)
    H.item("crate_stack_1", dt, [39, 0, 4.5], [45, 6, 10.5], "crate_oak", lambda W, Hh, c: H.P.crate(R["oak"], W, Hh, c))
    H.item("crate_stack_2", dt, [39.5, 6, 5], [44.5, 10, 10], "crate_oak", lambda W, Hh, c: H.P.crate(R["oak"], W, Hh, c),
           rot=(0, 22.5, 0), origin=[42, 6, 7.5])
    H.box("moss_corner_1", dt, [-39, 2, -14], [-35, 2.5, -12.5], "moss", ("down",), "mc1")
    H.box("moss_corner_2", dt, [35, 2, 13.5], [39, 2.5, 16], "moss", ("down",), "mc2")
    for i, (x, z) in enumerate(((-40.5, -15), (40, -16.5), (-39.5, 16.5))):
        H.box(f"loose_cobble_{i + 1}", dt, [x - 0.75, 0, z - 0.75], [x + 0.75, 1, z + 0.75], "plinth", ("down",), "lcob",
              rot=(0, 22.5 * (i + 1), 0), origin=[x, 0, z])
    ik = H.rect("ivy_wall", 14, 48, lambda W, Hh: H.P.ivy(W, Hh, "lit"))
    H.card("ivy_side_wall", dt, [-37.75, 2, 5], [-37.75, 26, 12], ik, faces=("west", "east"))
    # pivots at the base centre of each top-level group (section 8 of the prompt)
    by_id = {e["uuid"]: e for e in H.m.elements}

    def cubes_in(name):
        out = []
        for kind, ch in H.m.groups[name]["children"]:
            out += cubes_in(ch) if kind == "g" else [by_id[ch]]
        return out
    for name in g.values():
        es = cubes_in(name)
        xs = [v for e in es for v in (e["from"][0], e["to"][0])]; zs = [v for e in es for v in (e["from"][2], e["to"][2])]
        H.m.groups[name]["origin"] = [round((min(xs) + max(xs)) / 2, 2), round(min(e["from"][1] for e in es), 2),
                                      round((min(zs) + max(zs)) / 2, 2)]
    return H


BUILDERS = {f.__name__: f for f in (market_stall_fruit, market_stall_bakery, market_stall_potion, market_stall_cloth,
                                         market_stall_merchant)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        BUILDERS[n]().finish([OUT])
