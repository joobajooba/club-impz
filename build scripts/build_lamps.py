"""Castle style street lamps for the hub town (deco_lib.py). Each lantern's glass is `*_glow` inside a `light_N`
group whose pivot is the flame, for an OmniLight3D at night.
Usage: py build_lamps.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from deco_lib import Deco, deco_mats, R, F, px, h2

OUT = r"C:\Users\lucas\blockbench_models\props\lamps"
TEX = [256]
TUFTS = [(-7.6, -5.0, 4, 4.5), (7.4, -6.6, 3, 3), (7.8, 3.5, 4, 4.5), (-6.0, 7.8, 3, 3), (1.5, -7.8, 2, 3)]
# S scroll in the plane of a bracket (u out from the post, v up): a curl at the post, a long sweep up to the tray
SCROLL = [(2.0, -1.0), (1.3, -1.5), (0.8, -0.6), (1.2, 0.5), (2.4, 1.3), (3.3, 2.7), (3.7, 4.5), (3.8, 6.2), (3.7, 7.6)]


def plinth(H, g, s=1.0, die_h=8.0, y=0.0):
    """Limestone pedestal: a moulded skirt and step, a die with sunk carved panels, a cap moulding."""
    a, b, c, d = 7 * s, 6 * s, 4.5 * s, 5 * s
    a, b, c, d = h2(a), h2(b), h2(c), h2(d)
    H.box("plinth_skirt", g, [-a, y, -a], [a, y + 1.5, a], "stone", ("down",), "pskirt", place="ground")
    H.box("plinth_step", g, [-b, y + 1.5, -b], [b, y + 3, b], "stone", ("down",), "pstep")
    H.box("pedestal_foot", g, [-d, y + 3, -d], [d, y + 4, d], "stone", ("down",), "pfoot")
    H.item("pedestal_die", g, [-c, y + 4, -c], [c, y + 4 + die_h, c], f"panel{c}", lambda W, Hh, cat: H.P.panel(R["stone"], W, Hh, cat),
           hide=("down", "up"))
    top = y + 4 + die_h
    H.box("pedestal_cap", g, [-(c + 1), top, -(c + 1)], [c + 1, top + 1.5, c + 1], "stone", ("down",), "pcap")
    H.box("pedestal_cap_top", g, [-(c - 0.5), top + 1.5, -(c - 0.5)], [c - 0.5, top + 2.5, c - 0.5], "stone", ("down",), "pcap2")
    return top + 2.5


def iron_post(H, g, y0, y1, collars=(), D=2.5):
    """Cast iron post on a stepped foot: fluted octagonal shaft, collar rings."""
    H.box("post_foot_1", g, [-2.5, y0, -2.5], [2.5, y0 + 1, 2.5], "iron", ("down",), "pf1")
    H.box("post_foot_2", g, [-2, y0 + 1, -2], [2, y0 + 2.5, 2], "iron", ("down",), "pf2")
    fl = lambda W, Hh, c: H.P.fluted(R["lamp_iron"], W, Hh, c)
    H.octo_item("post_bell", g, 0, 0, 3.5, y0 + 2.5, y0 + 4.5, "flute_bell", fl)
    H.octo_item("post_shaft", g, 0, 0, D, y0 + 4.5, y1, "flute_shaft", fl, hide=("down", "up"))
    for i, yc in enumerate(collars):
        H.box(f"post_collar_{i + 1}", g, [-1.75, yc, -1.75], [1.75, yc + 1, 1.75], "iron", (), "collar")
        H.box(f"post_collar_{i + 1}_bead", g, [-1.5, yc + 1, -1.5], [1.5, yc + 1.5, 1.5], "gold", ("down",), "bead")


def ladder_bar(H, g, y):
    """The lamplighter's ladder rest: a bar through the post with gold balls on the ends."""
    H.box("ladder_bar", g, [-4.5, y, -0.5], [4.5, y + 1, 0.5], "iron", (), "ladder")
    for s in (-1, 1):
        x0 = 4.5 if s > 0 else -6
        H.box(f"ladder_ball_{'right' if s > 0 else 'left'}", g, [x0, y - 0.5, -0.75], [x0 + 1.5, y + 1, 0.75], "gold", (), "lball")


def hang_y(bottom, gh, roof_h):
    """Tray height of a hanging lantern whose ring top meets a chain ending at `bottom`."""
    return bottom - (2 + gh + roof_h + 4 + 2)


def ground(H):
    """Lift the model so its lowest cube sits on y = 0 (doc 1.3)."""
    lo = min(e["from"][1] for e in H.m.elements if e.get("export", True))
    if lo < 0:
        for e in H.m.elements:
            e["from"][1] -= lo; e["to"][1] -= lo; e["origin"][1] -= lo
        for gr in H.m.groups.values(): gr["origin"][1] = round(gr["origin"][1] - lo, 3)


def finish_lamp(H):
    ground(H); H.finish([OUT]); return H


# ==================================================================== 1. street lamp (single)
def street_lamp():
    H = Deco("street_lamp", 7101, deco_mats(), tex=TEX[0])
    g = {k: H.group(k, [0, 0, 0]) for k in ("pedestal", "post", "brackets", "lantern_top", "grass")}
    top = plinth(H, g["pedestal"])                                          # 13.5
    iron_post(H, g["post"], top, 38, collars=(top + 6, 26, 33.5))
    ladder_bar(H, g["post"], 31)
    H.box("capital_1", g["post"], [-2, 38, -2], [2, 39, 2], "iron", ("down",), "cap1")
    H.box("capital_2", g["post"], [-1.5, 39, -1.5], [1.5, 41, 1.5], "iron", ("down",), "cap2")
    for i, (dx, dz) in enumerate(((1, 1), (-1, 1), (-1, -1), (1, -1))):
        H.curve(f"bracket_{i + 1}", g["brackets"], [0, 34.5, 0], (dx, dz), SCROLL)
    H.lantern("lantern", g["lantern_top"], 0, 43, 0, s=5, gh=7, roof_h=10)
    H.tufts("tuft", g["grass"], TUFTS)
    return finish_lamp(H)


# ==================================================================== 2. double street lamp
def street_lamp_double():
    H = Deco("street_lamp_double", 7202, deco_mats(), tex=TEX[0])
    g = {k: H.group(k, [0, 0, 0]) for k in ("pedestal", "post", "crossbar", "lanterns", "basket", "grass")}
    top = plinth(H, g["pedestal"], s=1.1)
    iron_post(H, g["post"], top, 46, collars=(top + 6, 27, 37))
    H.box("post_cap", g["post"], [-2, 46, -2], [2, 47, 2], "iron", ("down",), "pcap")
    H.box("post_neck", g["post"], [-1, 47, -1], [1, 48, 1], "iron", ("down",), "pneck")
    H.box("post_ball", g["post"], [-1.5, 48, -1.5], [1.5, 51, 1.5], "gold", ("down",), "pball")
    H.box("post_spike", g["post"], [-0.5, 51, -0.5], [0.5, 54, 0.5], "gold", ("down",), "pspike")
    cb = g["crossbar"]
    H.box("crossbar", cb, [-11, 42, -0.5], [11, 43, 0.5], "iron", (), "xbar")
    H.box("crossbar_top_rail", cb, [-9, 44.5, -0.25], [9, 45, 0.25], "iron", (), "xrail")
    for i, x in enumerate((-7.5, -4.5, 4.5, 7.5)):
        H.box(f"crossbar_spindle_{i + 1}", cb, [x - 0.25, 43, -0.25], [x + 0.25, 44.5, 0.25], "iron", (), "spind")
        H.box(f"crossbar_spindle_{i + 1}_knob", cb, [x - 0.5, 43.5, -0.5], [x + 0.5, 44, 0.5], "gold", (), "sknob")
    for side, s in (("right", 1), ("left", -1)):
        H.box(f"crossbar_end_{side}", cb, [s * 11 - 0.5 + (0 if s > 0 else 0), 41.5, -0.75], [s * 11 + 0.5, 43.5, 0.75], "iron", (), "xend")
        x0 = 11.5 if s > 0 else -13.5
        H.box(f"crossbar_ball_{side}", cb, [x0, 41.5, -1], [x0 + 2, 43.5, 1], "gold", (), "xball")
        H.curve(f"brace_{side}", cb, [0, 33.5, 0], (s, 0),
                [(1.0, 0.0), (2.6, 0.6), (4.4, 1.9), (5.9, 3.8), (6.9, 6.0), (7.3, 8.5)])
        ring = [(4.2 + 1.3 * math.cos(math.radians(a)), 6.6 + 1.3 * math.sin(math.radians(a))) for a in range(0, 361, 60)]
        H.curve(f"brace_{side}_ring", cb, [0, 33.5, 0], (s, 0), ring)
        H.box(f"hook_{side}", cb, [s * 9.5 - 0.25, 40.5, -0.25], [s * 9.5 + 0.25, 42, 0.25], "iron", (), "hook")
        H.chain(f"chain_{side}", g["lanterns"], s * 9.5, 40.5, 37.5, 0)
        H.lantern(f"lantern_{side}", g["lanterns"], s * 9.5, hang_y(37.5, 6, 7), 0, s=4, gh=6, roof_h=7, hang=True)
    # hanging flower basket on the north side of the post
    bk = g["basket"]
    H.rotbar("basket_arm", bk, [0, 31.5, -1], [0, 31.5, -6.5], 1, "iron")
    H.curve("basket_arm_brace", bk, [0, 28, -1], (0, -1), [(0.0, 0.0), (1.5, 0.4), (3.0, 1.4), (4.2, 3.0)])
    H.chain("basket_chain", bk, 0, 31, 27, -6)
    wk = lambda W, Hh, c: H.P.wicker(R["wicker"], W, Hh, c)
    H.item("basket_base", bk, [-1.5, 23, -7.5], [1.5, 24, -4.5], "wick_b", wk)
    H.item("basket_bowl", bk, [-2.5, 24, -8.5], [2.5, 26, -3.5], "wick_bowl", wk, hide=("up",))
    H.item("basket_soil", bk, [-2.5, 26, -8.5], [2.5, 26.5, -3.5], "soil5", lambda W, Hh, c: H.P.soil(W, Hh, c), hide=("down",))
    for i, (x1, z1, x2, z2) in enumerate(((-3, -9, 3, -8.5), (-3, -3.5, 3, -3), (-3, -8.5, -2.5, -3.5), (2.5, -8.5, 3, -3.5))):
        H.item(f"basket_rim_{i + 1}", bk, [x1, 26, z1], [x2, 27, z2], "wick_rim", wk)
    plant_basket(H, bk, 0, 26.5, -6, 2.5)
    H.tufts("tuft", g["grass"], [(x * 1.1, z * 1.1, n, hh) for x, z, n, hh in TUFTS])
    return finish_lamp(H)


def plant_basket(H, g, cx, y, cz, r):
    """Geraniums and trailing ivy filling a basket or small pot."""
    lk = H.leaf_keys(R["box_leaf"], "ger", ((2, 3, 0.2), (2.5, 3.5, -0.2)))
    H.rosette("basket", g, cx, y, cz, lk, n=7, tilt=(50, 80))
    hk = H.rect("geranium_head", px(2.5), px(2.5), lambda W, Hh: H.P.flower_disc(R["geranium"], R["yolk"], W, Hh, "pompom"))
    for j in range(4):
        a = math.radians(j * 90 + 30)
        H.flower("basket_geranium", g, cx + math.cos(a) * 0.8, y, cz + math.sin(a) * 0.8, 3, hk, 2.5, stem_lean=18,
                 yaw=j * 90 + 30)
    edge = []
    for j in range(8):
        a = j * 45 + H.rng.uniform(-10, 10)
        edge.append(((cx + math.cos(math.radians(a)) * r, y, cz + math.sin(math.radians(a)) * r),
                     (math.cos(math.radians(a)), math.sin(math.radians(a)))))
    for p, o in edge:
        H.ivy_over_edge("basket", g, [p], o, lengths=(6, 8))


# ==================================================================== 3. grand plaza lamp
def plaza_lamp():
    H = Deco("plaza_lamp", 7303, deco_mats(), tex=TEX[0])
    g = {k: H.group(k, [0, 0, 0]) for k in ("pedestal", "column", "candelabra", "lanterns", "grass")}
    p = g["pedestal"]
    H.box("plinth_skirt", p, [-10, 0, -10], [10, 1.5, 10], "stone", ("down",), "skirt", place="ground")
    H.box("plinth_step_1", p, [-8.5, 1.5, -8.5], [8.5, 3, 8.5], "stone", ("down",), "st1")
    H.box("plinth_step_2", p, [-7, 3, -7], [7, 4.5, 7], "stone", ("down",), "st2")
    H.item("pedestal_die", p, [-5, 4.5, -5], [5, 14, 5], "panel_big", lambda W, Hh, c: H.P.panel(R["stone"], W, Hh, c), hide=("down", "up"))
    H.box("pedestal_cap", p, [-6, 14, -6], [6, 15.5, 6], "stone", ("down",), "pcap")
    c = g["column"]
    H.box("column_base", c, [-4, 15.5, -4], [4, 17, 4], "stone", ("down",), "cbase")
    H.octo_item("column_shaft", c, 0, 0, 6, 17, 29, "gadroon6", lambda W, Hh, cat: H.P.gadroon(R["stone"], W, Hh, cat), hide=("down", "up"))
    H.box("column_necking", c, [-3.5, 29, -3.5], [3.5, 30, 3.5], "stone", ("down",), "neck")
    H.box("column_capital", c, [-4.5, 30, -4.5], [4.5, 31.5, 4.5], "stone", ("down",), "capit")
    H.box("column_abacus", c, [-5, 31.5, -5], [5, 32.5, 5], "stone", ("down",), "abacus")
    cd = g["candelabra"]
    iron_post(H, cd, 32.5, 46, collars=(39.5,))
    H.box("capital_1", cd, [-2, 46, -2], [2, 47, 2], "iron", ("down",), "cap1")
    H.box("capital_2", cd, [-1.5, 47, -1.5], [1.5, 49, 1.5], "iron", ("down",), "cap2")
    H.lantern("lantern_top", g["lanterns"], 0, 51, 0, s=5, gh=7, roof_h=10)
    rr = 10.5
    for i, ang in enumerate((45, 135, 225, 315)):
        dx, dz = math.cos(math.radians(ang)), math.sin(math.radians(ang))
        ex, ez = dx * rr, dz * rr
        H.rotbar(f"arm_{i + 1}", cd, [dx * 1.0, 40.5, dz * 1.0], [ex, 40.5, ez], 1, "iron")
        H.box(f"arm_{i + 1}_riser", cd, [ex - 0.5, 40, ez - 0.5], [ex + 0.5, 43, ez + 0.5], "iron", (), "riser")
        H.curve(f"arm_{i + 1}_brace", cd, [0, 35, 0], (dx, dz), [(1.0, 0.0), (2.8, 0.6), (4.8, 1.6), (6.6, 3.0), (8.0, 4.4), (8.8, 5.6)])
        H.curve(f"arm_{i + 1}_curl", cd, [0, 40.5, 0], (dx, dz), [(rr, 0.0), (rr + 0.9, -0.8), (rr + 0.5, -1.8), (rr - 0.4, -1.5)])
        H.lantern(f"lantern_{i + 1}", g["lanterns"], round(ex * 2) / 2, 46, round(ez * 2) / 2, s=4, gh=6, roof_h=7)
    H.tufts("tuft", g["grass"], [(-10.6, -6, 4, 4.5), (10.4, -8.5, 3, 3), (10.8, 5, 4, 4.5), (-8, 10.8, 3, 3), (3, -10.8, 3, 3.5), (-3, 10.6, 2, 3)])
    return finish_lamp(H)


# ==================================================================== 4. wall lantern (for castle and house walls)
def wall_lantern():
    """Mounts on a wall: the back plate sits on z = 0 and everything sticks out north (-z)."""
    H = Deco("wall_lantern", 7404, deco_mats(), tex=TEX[0])
    g = {k: H.group(k, [0, 0, 0]) for k in ("wall_plate", "bracket", "lantern_hang")}
    w = g["wall_plate"]
    H.box("plate", w, [-2, 13, -1], [2, 26, 0], "iron", ("south",), "plate")
    H.box("plate_frame_top", w, [-2.5, 25.5, -1.5], [2.5, 26.5, 0], "iron", ("south",), "pft")
    H.box("plate_frame_bottom", w, [-2.5, 12.5, -1.5], [2.5, 13.5, 0], "iron", ("south",), "pfb")
    for i, (yy, s) in enumerate(((14, 1), (24, 1))):
        for x in (-1, 1):
            H.box(f"plate_rivet_{i * 2 + (x > 0) + 1}", w, [x - 0.5, yy, -1.5], [x + 0.5, yy + 1, -1], "gold", ("south",), "rivet")
    H.box("plate_top_knob", w, [-1, 26.5, -1.5], [1, 28, 0], "gold", ("south",), "ptk")
    H.box("plate_bottom_drop", w, [-0.5, 10.5, -1.25], [0.5, 12.5, -0.25], "gold", ("south",), "pbd")
    for s, d in (("right", 1), ("left", -1)):
        H.curve(f"plate_curl_{s}", w, [0, 19.5, -0.75], (d, 0),
                [(2.0, 2.5), (3.4, 2.2), (3.8, 0.8), (3.0, -0.4), (2.2, 0.0)])
        H.curve(f"plate_curl_{s}_low", w, [0, 15.5, -0.75], (d, 0), [(2.0, 0.5), (3.0, 0.0), (3.2, -1.2), (2.4, -1.8)])
    b = g["bracket"]
    H.rotbar("arm", b, [0, 23, -1], [0, 23, -10], 1, "iron")
    H.box("arm_top_rail", b, [-0.25, 24.5, -9], [0.25, 25, -1], "iron", (), "atr")
    for i, z in enumerate((-3.5, -6.5)):
        H.box(f"arm_spindle_{i + 1}", b, [-0.25, 23.5, z - 0.25], [0.25, 24.5, z + 0.25], "iron", (), "aspin")
    H.box("arm_end", b, [-0.75, 22.5, -11], [0.75, 24, -9.5], "iron", (), "aend")
    H.box("arm_end_ball", b, [-1, 22.5, -13], [1, 24.5, -11], "gold", (), "aball")
    H.curve("arm_brace", b, [0, 15, -1], (0, -1), [(0.0, 0.0), (1.6, 0.6), (3.4, 2.0), (5.0, 4.0), (6.2, 6.2), (6.8, 8.0)])
    ring = [(3.0 + 1.2 * math.cos(math.radians(a)), 5.4 + 1.2 * math.sin(math.radians(a))) for a in range(0, 361, 60)]
    H.curve("arm_brace_ring", b, [0, 15, -1], (0, -1), ring)
    H.box("hook", b, [-0.25, 21.5, -9.25], [0.25, 23, -8.75], "iron", (), "hook")
    H.chain("chain", g["lantern_hang"], 0, 21.5, 19.5, -9)
    H.lantern("lantern", g["lantern_hang"], 0, hang_y(19.5, 6, 7), -9, s=4, gh=6, roof_h=7, hang=True)
    return finish_lamp(H)


# ==================================================================== 5. path lantern (short stone bollard)
def path_lantern():
    H = Deco("path_lantern", 7505, deco_mats(), tex=TEX[0])
    g = {k: H.group(k, [0, 0, 0]) for k in ("base", "chamber", "roof", "grass")}
    b = g["base"]
    H.box("base_skirt", b, [-5, 0, -5], [5, 1.5, 5], "stone", ("down",), "bskirt", place="ground")
    H.box("base_step", b, [-4, 1.5, -4], [4, 3, 4], "stone", ("down",), "bstep")
    H.item("shaft", b, [-3, 3, -3], [3, 10, 3], "panel6", lambda W, Hh, c: H.P.panel(R["stone"], W, Hh, c, emblem=True), hide=("down", "up"))
    H.box("sill", b, [-4, 10, -4], [4, 11, 4], "stone", ("down",), "sill")
    c = g["chamber"]
    H.n_light += 1
    lg = H.group(f"light_{H.n_light}", [0, 13.5, 0], c)
    H.item("chamber_glow", lg, [-2.5, 11, -2.5], [2.5, 16, 2.5], "pane_path", lambda W, Hh, cat: H.P.pane(W, Hh, cat, lattice=0), hide=("up", "down"))
    for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
        x0, z0 = (-3.5 if sx < 0 else 2), (-3.5 if sz < 0 else 2)
        H.box(f"pier_{i + 1}", c, [x0, 11, z0], [x0 + 1.5, 16, z0 + 1.5], "stone", ("down", "up"), "pier")
    for f, (ax, plane) in enumerate((("x", -2.5), ("x", 2.5), ("z", -2.5), ("z", 2.5))):
        for j, u in enumerate((-0.75, 0.75)):
            if ax == "x":
                frm, to = [u - 0.25, 11, plane - 0.5 if plane < 0 else plane], [u + 0.25, 16, plane if plane < 0 else plane + 0.5]
            else:
                frm, to = [plane - 0.5 if plane < 0 else plane, 11, u - 0.25], [plane if plane < 0 else plane + 0.5, 16, u + 0.25]
            H.box(f"grille_{f * 2 + j + 1}", c, frm, to, "iron", ("up", "down"), "grille")
    r = g["roof"]
    H.box("cap_slab", r, [-4.5, 16, -4.5], [4.5, 17.5, 4.5], "stone", (), "capslab")
    H.cone("roof", r, 0, 0, 8, 17.5, 25.5, "slate", n=4, finial="gold")
    H.tufts("tuft", g["grass"], [(-5.4, -3.5, 3, 3), (5.3, -5.0, 3, 3.5), (4.5, 5.4, 3, 3), (-5.0, 4.0, 2, 3)])
    return finish_lamp(H)


def build(n):
    """Smallest texture that fits (doc 1.5 rule 1): 256, else 512."""
    for t in (256, 512):
        TEX[0] = t
        try:
            return BUILDERS[n]()
        except SystemExit as e:
            if "overflow" not in str(e): raise
            print(f"  {n}: {e}; trying a bigger texture")


BUILDERS = {f.__name__: f for f in (street_lamp, street_lamp_double, plaza_lamp, wall_lantern, path_lantern)}

if __name__ == "__main__":
    for n in (sys.argv[1:] or BUILDERS):
        build(n)
