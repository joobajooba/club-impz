"""Town greenery for the hub, in the castle's limestone (deco_lib.py): flower planters, an urn, clipped topiary, a
hedge and a blossom tree in a raised bed. Plants are alpha cards (doc 3.4.2); clipped topiary and hedges are solid
clipped forms painted as tiny leaves, softened by leaf cards poking out of them.
Usage: py build_town_decor.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from deco_lib import Deco, deco_mats, R, F, px, h2
import plant_paint as PP

OUT = r"C:\Users\lucas\blockbench_models\foliage\town"
TEX = [256]


def new(name, seed):
    return Deco(name, seed, deco_mats(), tex=TEX[0])


# ---------------------------------------------------------------- shared pieces
def planter(H, g, x1, x2, z1, z2, ytop, split=1):
    """Limestone planter: a moulded plinth, a body with sunk carved panels (split into `split` bays along x), a rim
    of four coping stones overhanging by 1, and soil inside. Returns the soil top height."""
    H.box("planter_plinth", g, [x1 - 1, 0, z1 - 1], [x2 + 1, 2, z2 + 1], "stone", ("down",), "plinth", place="ground")
    bay = (x2 - x1) / split
    for i in range(split):
        a, b = x1 + i * bay, x1 + (i + 1) * bay
        hide = ["down", "up"] + (["west"] if i > 0 else []) + (["east"] if i < split - 1 else [])
        H.item(f"planter_body_{i + 1}" if split > 1 else "planter_body", g, [a, 2, z1], [b, ytop, z2], f"panel_{b - a}_{z2 - z1}",
               lambda W, Hh, c: H.P.panel(R["stone"], W, Hh, c), hide=tuple(hide))
    rims = {"north": ([x1 - 1, ytop, z1 - 1], [x2 + 1, ytop + 1.5, z1 + 1]), "south": ([x1 - 1, ytop, z2 - 1], [x2 + 1, ytop + 1.5, z2 + 1]),
            "west": ([x1 - 1, ytop, z1 + 1], [x1 + 1, ytop + 1.5, z2 - 1]), "east": ([x2 - 1, ytop, z1 + 1], [x2 + 1, ytop + 1.5, z2 - 1])}
    for k, (f, t) in rims.items():
        H.box(f"planter_rim_{k}", g, f, t, "stone", (), f"rim_{k}")
    H.item("planter_soil", g, [x1 + 1, ytop, z1 + 1], [x2 - 1, ytop + 1, z2 - 1], "soil",
           lambda W, Hh, c: H.P.soil(W, Hh, c), hide=("down", "north", "south", "east", "west"))
    return ytop + 1


def rim_points(x1, x2, z1, z2, y, step, rng, sides=("north", "south", "east", "west")):
    """Points along the rim tops with their outward direction, for trailing ivy."""
    out = []
    for s in sides:
        if s in ("north", "south"):
            z = z1 if s == "north" else z2; o = (0, -1) if s == "north" else (0, 1)
            n = max(1, int((x2 - x1) // step))
            for i in range(n):
                out.append(((x1 + (i + 0.5) * (x2 - x1) / n + rng.uniform(-0.8, 0.8), y, z), o))
        else:
            x = x1 if s == "west" else x2; o = (-1, 0) if s == "west" else (1, 0)
            n = max(1, int((z2 - z1) // step))
            for i in range(n):
                out.append(((x, y, z1 + (i + 0.5) * (z2 - z1) / n + rng.uniform(-0.8, 0.8)), o))
    return out


def ivy_rim(H, g, pts, lengths):
    for p, o in pts:
        if H.rng.random() < 0.85:
            H.ivy_over_edge("rim", g, [p], o, lengths=lengths)


def lavender(H, g, x, y, z, n=9):
    ks = [H.rect(f"lav_{L}_{i}", px(1.5), px(L), lambda W, Hh, sh=sh: H.P.lavender_spike(W, Hh, sh))
          for i, (L, sh) in enumerate(((6, 0.0), (7, 0.3), (8, -0.2)))]
    Ls = (6, 7, 8)
    bl = H.rect("lav_leaf", px(1), px(3.5), lambda W, Hh: PP.paint_blade(H.nr, R["sage"], W, Hh, 0.2, 0.2, 1, 1))
    for j in range(n):
        k = j % 3
        H.m.card(H.nid("lavender_spike"), g, [x + H.rng.uniform(-0.6, 0.6), y, z + H.rng.uniform(-0.6, 0.6)], ks[k], 1.5, Ls[k],
                 j * 137.5 + H.rng.uniform(-15, 15), H.rng.uniform(4, 28), H.rng.uniform(-30, 30), sink=0.3)
    for j in range(5):
        H.m.card(H.nid("lavender_leaf"), g, [x, y, z], bl, 1, 3.5, j * 72 + H.rng.uniform(-20, 20), H.rng.uniform(35, 65), 0, sink=0.3)


def flower_clump(H, g, x, y, z, kind, n=3, height=(3, 4.5)):
    """A few flowers of one kind from a leaf rosette."""
    spec = {"geranium": (R["geranium"], R["yolk"], "pompom", 2.5, R["box_leaf"]),
            "marigold": (R["marigold"], R["marigold"], "pompom", 2.5, R["box_leaf"]),
            "daisy": (R["daisy"], R["yolk"], "daisy", 3, R["stem_green"]),
            "pansy": (R["pansy"], R["yolk"], "pansy", 2.5, R["box_leaf"])}[kind]
    Rp, Rc, form, s, Rl = spec
    hk = [H.rect(f"{kind}_head_{v}", px(s), px(s), lambda W, Hh, sh=sh: H.P.flower_disc(Rp, Rc, W, Hh, form, sh))
          for v, sh in enumerate((0.0, 0.4))]
    lk = H.leaf_keys(Rl, kind, ((2, 2.5, 0.2), (2.5, 3, -0.2)))
    H.rosette(kind, g, x, y, z, lk, n=5, tilt=(55, 82))
    for j in range(n):
        hh = H.rng.choice([h2(v) for v in np.arange(height[0], height[1] + 0.01, 0.5)])
        H.flower(kind, g, x + H.rng.uniform(-0.8, 0.8), y, z + H.rng.uniform(-0.8, 0.8), hh, hk[j % 2], s,
                 stem_lean=H.rng.uniform(5, 25), yaw=j * 120 + H.rng.uniform(-30, 30),
                 pitch=H.rng.uniform(60, 80) if kind == "pansy" else None)


def ground_cover(H, g, x1, x2, z1, z2, y, step=3.5):
    lk = H.leaf_keys(R["box_leaf"], "cover", ((2, 3, 0.3), (2.5, 3.5, -0.3), (2, 2.5, 0.0)))
    xs = np.arange(x1 + step / 2, x2, step); zs = np.arange(z1 + step / 2, z2, step)
    for x in xs:
        for z in zs:
            H.rosette("cover", g, x + H.rng.uniform(-0.8, 0.8), y, z + H.rng.uniform(-0.8, 0.8), lk, n=3, tilt=(60, 84))


def clipped(H, name, g, cx, cy, cz, hx, hy, hz, cut=1.5, tag="hedge", bloom=None, rate=0.0):
    """A clipped green form: the main box plus caps on top and bottom and two crossed side boxes cut back by
    `cut`, so the corners are rounded."""
    hp = lambda W, Hh, c: H.P.hedge(R["box_leaf"], W, Hh, c, bloom, rate)
    H.item(f"{name}_x", g, [cx - hx, cy - hy + cut, cz - hz + cut], [cx + hx, cy + hy - cut, cz + hz - cut], tag, hp, hide=())
    H.item(f"{name}_z", g, [cx - hx + cut, cy - hy + cut, cz - hz], [cx + hx - cut, cy + hy - cut, cz + hz], tag, hp, hide=())
    H.item(f"{name}_y", g, [cx - hx + cut, cy - hy, cz - hz + cut], [cx + hx - cut, cy + hy, cz + hz - cut], tag, hp, hide=())


def fin(H):
    H.finish([OUT]); return H


# ==================================================================== 1. square flower planter
def planter_square_flowers():
    H = new("planter_square_flowers", 8101)
    g = {k: H.group(k, [0, 0, 0]) for k in ("planter", "flowers", "ivy")}
    y = planter(H, g["planter"], -7, 7, -7, 7, 8)
    ground_cover(H, g["flowers"], -6, 6, -6, 6, y)
    lavender(H, g["flowers"], 0, y, 0, 11)
    for (x, z, k) in ((-3.5, -3.5, "geranium"), (3.5, -3.5, "daisy"), (3.5, 3.5, "geranium"), (-3.5, 3.5, "daisy"),
                      (0, -4.5, "pansy"), (4.5, 0, "pansy"), (0, 4.5, "pansy"), (-4.5, 0, "pansy")):
        flower_clump(H, g["flowers"], x, y, z, k, n=2 if k == "pansy" else 3, height=(1.5, 2) if k == "pansy" else (3, 5))
    ivy_rim(H, g["ivy"], rim_points(-7, 7, -7, 7, y + 0.5, 3.5, H.rng), (6, 8))
    return fin(H)


# ==================================================================== 2. long trough planter
def planter_trough_flowers():
    H = new("planter_trough_flowers", 8202)
    g = {k: H.group(k, [0, 0, 0]) for k in ("planter", "flowers", "ivy")}
    y = planter(H, g["planter"], -16, 16, -5, 5, 7, split=2)
    ground_cover(H, g["flowers"], -15, 15, -4, 4, y, step=4)
    xs = [-12.5, -7.5, -2.5, 2.5, 7.5, 12.5]
    kinds = ["marigold", "lavender", "daisy", "lavender", "marigold", "daisy"]
    for x, k in zip(xs, kinds):
        if k == "lavender": lavender(H, g["flowers"], x, y, 0, 8)
        else: flower_clump(H, g["flowers"], x, y, H.rng.uniform(-1, 1), k, n=3, height=(3, 4.5))
    for x in (-10, 0, 10):
        flower_clump(H, g["flowers"], x, y, -2.5, "pansy", n=2, height=(1.5, 2))
    ivy_rim(H, g["ivy"], rim_points(-16, 16, -5, 5, y + 0.5, 3.5, H.rng, ("north", "south")), (6, 8, 10))
    return fin(H)


# ==================================================================== 3. urn planter on a pedestal
def urn_planter():
    H = new("urn_planter", 8303)
    g = {k: H.group(k, [0, 0, 0]) for k in ("pedestal", "urn", "plants", "ivy")}
    p, u = g["pedestal"], g["urn"]
    H.box("base", p, [-6, 0, -6], [6, 1.5, 6], "stone", ("down",), "base", place="ground")
    H.item("die", p, [-4.5, 1.5, -4.5], [4.5, 9.5, 4.5], "panel9", lambda W, Hh, c: H.P.panel(R["stone"], W, Hh, c), hide=("down", "up"))
    H.box("cap", p, [-5.5, 9.5, -5.5], [5.5, 11, 5.5], "stone", ("down",), "cap")
    gd = lambda W, Hh, c: H.P.gadroon(R["stone"], W, Hh, c)
    H.octo("urn_foot", u, 0, 0, 6, 11, 12, "stone")
    H.octo("urn_stem", u, 0, 0, 3.5, 12, 14, "stone", hide=("down", "up"))
    H.octo("urn_knop", u, 0, 0, 5, 14, 15, "stone")
    H.octo("urn_bowl_1", u, 0, 0, 7, 15, 16.5, "stone")
    H.octo_item("urn_bowl_2", u, 0, 0, 10, 16.5, 18, "gad10", gd)
    H.octo_item("urn_bowl_3", u, 0, 0, 12, 18, 21.5, "gad12", gd, hide=("down", "up"))
    H.octo("urn_lip", u, 0, 0, 13, 21.5, 23, "stone", hide=("down",))
    H.octo_item("urn_soil", u, 0, 0, 11, 23, 23.5, "soil_urn", lambda W, Hh, c: H.P.soil(W, Hh, c), hide=("down",))
    for side, d in (("right", 1), ("left", -1)):
        H.curve(f"urn_handle_{side}", u, [0, 0, 0], (d, 0), [(5.6, 21.5), (7.0, 21.9), (7.8, 20.8), (7.4, 19.4), (6.2, 18.6)], 1, "stone")
    pl = g["plants"]
    spk = [H.rect(f"spike_{i}", px(1.5), px(L), lambda W, Hh, sh=sh, b=b: PP.paint_blade(H.nr, R["berry"], W, Hh, sh, b, 3, 1))
           for i, (L, sh, b) in enumerate(((9, 0.2, 0.2), (11, 0.0, -0.3), (8, 0.4, 0.5)))]
    for j in range(13):
        k = j % 3
        H.m.card(H.nid("cordyline_leaf"), pl, [H.rng.uniform(-0.5, 0.5), 23.5, H.rng.uniform(-0.5, 0.5)], spk[k], 1.5, (9, 11, 8)[k],
                 j * 137.5, H.rng.uniform(8, 42), H.rng.uniform(-20, 20), sink=0.3)
    for j in range(5):
        a = math.radians(j * 72 + 20)
        flower_clump(H, pl, math.cos(a) * 3.6, 23.5, math.sin(a) * 3.6, "geranium", n=2, height=(2.5, 3.5))
    pts = []
    for j in range(12):
        a = math.radians(j * 30 + H.rng.uniform(-8, 8)); r = 6.2
        pts.append(((math.cos(a) * r, 23.2, math.sin(a) * r), (math.cos(a), math.sin(a))))
    ivy_rim(H, g["ivy"], pts, (8, 10, 12))
    return fin(H)


# ==================================================================== 4. clipped ball topiary
def topiary_ball_planter():
    H = new("topiary_ball_planter", 8404)
    g = {k: H.group(k, [0, 0, 0]) for k in ("planter", "trunk", "ball", "underplanting")}
    y = planter(H, g["planter"], -6, 6, -6, 6, 8)
    H.item("trunk", g["trunk"], [-0.75, y - 0.5, -0.75], [0.75, 20, 0.75], "bark_t", lambda W, Hh, c: H.P.bark(R["bark"], W, Hh, c), hide=("down", "up"))
    H.item("trunk_collar", g["trunk"], [-1.25, y, -1.25], [1.25, y + 1, 1.25], "bark_c", lambda W, Hh, c: H.P.bark(R["bark"], W, Hh, c), hide=("down",))
    cy = 25.5
    clipped(H, "ball", g["ball"], 0, cy, 0, 6.5, 6.5, 6.5, cut=3)
    H.item("ball_core", g["ball"], [-4.5, cy - 4.5, -4.5], [4.5, cy + 4.5, 4.5], "hedge_core",
           lambda W, Hh, c: H.P.hedge(R["box_leaf"], W, Hh, c), hide=())
    lk = H.leaf_keys(R["box_leaf"], "fuzz", ((1.5, 2.5, 0.2), (1.5, 2, -0.2), (2, 2.5, 0.0)))
    H.fuzz("ball", g["ball"], [0, cy, 0], [6.2, 6.2, 6.2], lk, 64)
    for (x, z) in ((-3.5, -3.5), (3.5, 3.5), (3.5, -3.5), (-3.5, 3.5)):
        flower_clump(H, g["underplanting"], x, y, z, "pansy", n=2, height=(1.5, 2))
    ivy_rim(H, g["underplanting"], rim_points(-6, 6, -6, 6, y + 0.5, 4, H.rng), (6, 8))
    return fin(H)


# ==================================================================== 5. tiered (pom-pom) topiary
def topiary_tiered_planter():
    H = new("topiary_tiered_planter", 8505)
    g = {k: H.group(k, [0, 0, 0]) for k in ("planter", "trunk", "tiers", "underplanting")}
    y = planter(H, g["planter"], -6.5, 6.5, -6.5, 6.5, 8)
    H.item("trunk", g["trunk"], [-0.75, y - 0.5, -0.75], [0.75, 39, 0.75], "bark_t", lambda W, Hh, c: H.P.bark(R["bark"], W, Hh, c), hide=("down", "up"))
    lk = H.leaf_keys(R["box_leaf"], "fuzz", ((1.5, 2.5, 0.2), (1.5, 2, -0.2), (2, 2.5, 0.0)))
    for i, (cy, hx, hy, cut, n) in enumerate(((16, 6.5, 3.5, 2.5, 40), (25.5, 5, 3, 2, 28), (33.5, 3.5, 2.5, 1.5, 18), (39.5, 2, 2, 1, 8))):
        clipped(H, f"tier_{i + 1}", g["tiers"], 0, cy, 0, hx, hy, hx, cut=cut)
        H.fuzz(f"tier_{i + 1}", g["tiers"], [0, cy, 0], [hx - 0.3, hy - 0.3, hx - 0.3], lk, n)
    ivy_rim(H, g["underplanting"], rim_points(-6.5, 6.5, -6.5, 6.5, y + 0.5, 4, H.rng), (6, 8))
    for (x, z) in ((-4, 0), (4, 0), (0, -4), (0, 4)):
        flower_clump(H, g["underplanting"], x, y, z, "daisy", n=2, height=(2.5, 3.5))
    return fin(H)


# ==================================================================== 6. hedge segment (32 long, tiles end to end)
def hedge_segment():
    H = new("hedge_segment", 8606)
    g = {k: H.group(k, [0, 0, 0]) for k in ("kerb", "hedge", "edge_plants")}
    H.box("kerb", g["kerb"], [-16, 0, -5.5], [16, 2, 5.5], "stone", ("down",), "kerb", place="ground")
    H.box("kerb_cap_north", g["kerb"], [-16, 2, -5.5], [16, 2.5, -4.5], "stone", ("down",), "kcap")
    H.box("kerb_cap_south", g["kerb"], [-16, 2, 4.5], [16, 2.5, 5.5], "stone", ("down",), "kcap")
    hp = lambda W, Hh, c: H.P.hedge(R["box_leaf"], W, Hh, c)
    H.item("hedge_body", g["hedge"], [-16, 2, -4], [16, 12.5, 4], "hedge_b", hp, hide=("down",))
    H.item("hedge_top", g["hedge"], [-16, 12.5, -3], [16, 14, 3], "hedge_t", hp, hide=("down",))
    for i, (x, w) in enumerate(((-11, 6), (2, 8), (12, 5))):                # slight uneven growth on the top
        H.item(f"hedge_lump_{i + 1}", g["hedge"], [x - w / 2, 14, -2], [x + w / 2, 14.5, 2], "hedge_l", hp, hide=("down",))
    lk = H.leaf_keys(R["box_leaf"], "fuzz", ((1.5, 2.5, 0.2), (1.5, 2, -0.2), (2, 2.5, 0.0)))
    H.fuzz("hedge", g["hedge"], [0, 8, 0], [15.0, 5.8, 3.8], lk, 90, ymin=3.5)
    for x in (-12, -3, 7, 13):
        flower_clump(H, g["edge_plants"], x + H.rng.uniform(-1, 1), 2.5, -4.8, "daisy" if x % 2 else "pansy", n=2, height=(1.5, 2.5))
    H.tufts("tuft", g["edge_plants"], [(-8, -6, 3, 3), (4, -6, 3, 3), (-14, 6, 3, 3), (10, 6, 3, 3)])
    return fin(H)


# ==================================================================== 7. blossom tree in a raised octagonal bed
def blossom_tree_planter():
    H = new("blossom_tree_planter", 8707)
    g = {k: H.group(k, [0, 0, 0]) for k in ("bed", "tree", "blossom", "bed_plants")}
    bed = g["bed"]
    for i, ang in enumerate(range(0, 360, 45)):
        a = math.radians(ang); cx, cz = math.sin(a) * 13, -math.cos(a) * 13
        rot = (0, (-45 if ang in (45, 225) else 45), 0) if ang % 90 else (0, 0, 0)
        L = 11 if ang % 90 == 0 else 12
        if ang % 180 == 0:
            frm, to = [cx - L / 2, 0, cz - 1], [cx + L / 2, 6, cz + 1]; cf, ct = [cx - 6, 6, cz - 1.5], [cx + 6, 7.5, cz + 1.5]
        elif ang % 90 == 0:
            frm, to = [cx - 1, 0, cz - L / 2], [cx + 1, 6, cz + L / 2]; cf, ct = [cx - 1.5, 6, cz - 6], [cx + 1.5, 7.5, cz + 6]
        else:
            frm, to = [cx - L / 2, 0, cz - 1], [cx + L / 2, 6, cz + 1]; cf, ct = [cx - 6, 6, cz - 1.5], [cx + 6, 7, cz + 1.5]
        H.box(f"bed_wall_{i + 1}", bed, frm, to, "stone", ("down",), f"bw{i % 2}", rot=rot, origin=[cx, 3, cz], place="ground")
        H.box(f"bed_cap_{i + 1}", bed, cf, ct, "stone", ("down",), f"bc{i % 2}", rot=rot, origin=[cx, 6.5, cz])
    H.octo_item("bed_soil", bed, 0, 0, 24, 4.5, 5.5, "soil_bed", lambda W, Hh, c: H.P.soil(W, Hh, c, R["blossom"]), hide=("down",), inset=10)
    # ---- tree: root flare, a leaning trunk in three pieces, branches and twigs (bark bars)
    t = g["tree"]
    bk = lambda W, Hh, c: H.P.bark(R["cherry_bark"], W, Hh, c)
    for i, (dx, dz) in enumerate(((3.5, 1.0), (-3.0, 2.0), (-1.0, -3.5), (2.5, -2.5))):
        H.rotbar(f"root_{i + 1}", t, [0, 7.5, 0], [dx, 5.0, dz], 1.5, None, "bark_root", bk)
    trunk = [(0, 5, 0), (0.6, 14, 0.3), (-0.4, 22, 0.8), (0.3, 28, 0.2)]
    for i, (a, b, th) in enumerate(zip(trunk[:-1], trunk[1:], (3, 2.5, 2))):
        H.rotbar(f"trunk_{i + 1}", t, a, b, th, None, f"bark_tr{i}", bk)
    branches = [((-0.3, 20, 0.7), (-7, 28.5, 2), 1.5), ((0.3, 23, 0.6), (7.5, 30, -2), 1.5), ((0, 25.5, 0.5), (-3, 31.5, -6.5), 1.5),
                ((0.2, 26.5, 0.4), (3, 33, 6.5), 1.5), ((0.3, 27.5, 0.2), (0.5, 35.5, -0.5), 1.5)]
    tips = []
    for i, (a, b, th) in enumerate(branches):
        H.rotbar(f"branch_{i + 1}", t, a, b, th, None, "bark_br", bk)
        tw = (b[0] + (b[0] - a[0]) * 0.35, b[1] + 2.5, b[2] + (b[2] - a[2]) * 0.35)
        H.rotbar(f"branch_{i + 1}_twig", t, b, tw, 1, None, "bark_tw", bk)
        tips.append(np.array(b, float))
    # ---- blossom canopy: clusters of sprig cards on two shells round each branch tip (no solid core, doc 7)
    sk = []
    for i, (w, L) in enumerate(((4, 4.5), (3.5, 4), (4, 5))):
        for band, sh in (("lo", -1.0), ("mid", 0.0), ("hi", 0.8)):
            sk.append((H.rect(f"sprig_{i}_{band}", px(w), px(L), lambda W, Hh, sh=sh: H.P.blossom_sprig(W, Hh, sh)), w, L, band))
    centres = [(tips[0] + [-1, 2.5, 0.5], 6.0, 26), (tips[1] + [1, 2.5, -0.5], 6.0, 26), (tips[2] + [-0.5, 2.5, -1], 5.0, 20),
               (tips[3] + [0.5, 2.5, 1], 5.0, 20), (tips[4] + [0, 3.5, 0], 6.0, 26), (np.array([0, 31, 2.5]), 4.5, 14),
               (np.array([-3.5, 33, 2]), 4.5, 14), (np.array([3.5, 33.5, -2.5]), 4.5, 14)]
    golden = 137.508
    for ci, (c, r, n) in enumerate(centres):
        for j in range(n):
            u = (j + 0.5) / n                                                # 0 top .. 1 bottom of the cluster
            el = math.radians(80 - u * 150)                                   # from straight up to drooping
            az = math.radians(j * golden + ci * 40)
            d = np.array([math.cos(el) * math.sin(az), math.sin(el), math.cos(el) * math.cos(az)])
            inner = j % 3 == 2
            base = c + d * r * (0.25 if inner else 0.55) * np.array([1, 0.7, 1])
            band = "lo" if (u > 0.65 or inner) else ("hi" if u < 0.35 else "mid")
            k, w, L, _ = [s for s in sk if s[3] == band][H.rng.randrange(3)]
            dd = d + np.array([H.rng.uniform(-.25, .25), 0.15, H.rng.uniform(-.25, .25)])
            H.dir_card(H.nid(f"blossom_{ci + 1}"), g["blossom"], list(base), k, w, L, dd, roll=H.rng.uniform(-45, 45))
    # ---- the bed: fallen petals, grass, daisies and pansies
    bp = g["bed_plants"]
    pk = H.rect("petals", px(6), px(6), lambda W, Hh: H.P.petal_scatter(W, Hh))
    for i, (x, y, z) in enumerate(((-5, 5.6, 3), (4, 5.6, -5), (6, 5.6, 5), (-6, 5.6, -4), (0, 7.6, -13), (12.5, 7.6, 0), (-9, 7.1, 9))):
        H.head_card(f"fallen_petals_{i + 1}", bp, [x, y, z], pk, 6, i * 50, 90)
    H.tufts("bed_tuft", bp, [(-8, -3, 4, 4.5), (8, 2, 4, 4.5), (-3, 8, 3, 3.5), (3, -8, 3, 3.5), (-6, -8, 3, 3)], )
    for (x, z, k) in ((-8.5, 4.5, "daisy"), (8.5, -4, "daisy"), (5, 8.5, "pansy"), (-4.5, -8.5, "pansy"), (9, 6, "pansy"), (-9, -5, "daisy")):
        flower_clump(H, bp, x, 5.5, z, k, n=2, height=(1.5, 2) if k == "pansy" else (2.5, 3.5))
    # tufts were placed on y = 0: lift the bed ones onto the soil
    for e in H.m.elements:
        if e["name"].startswith("bed_tuft"):
            e["from"][1] += 5.5; e["to"][1] += 5.5; e["origin"][1] += 5.5
    return fin(H)


def build(n):
    for t in (256, 512, 1024):
        TEX[0] = t
        try:
            return BUILDERS[n]()
        except SystemExit as e:
            if "overflow" not in str(e): raise
            print(f"  {n}: {e}; trying a bigger texture")


BUILDERS = {f.__name__: f for f in (planter_square_flowers, planter_trough_flowers, urn_planter, topiary_ball_planter,
                                     topiary_tiered_planter, hedge_segment, blossom_tree_planter)}

if __name__ == "__main__":
    for n in (sys.argv[1:] or BUILDERS):
        build(n)
