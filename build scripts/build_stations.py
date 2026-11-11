"""Crafting stations for the hub crafting area (J00BA, 2026-11-09: "the crafting stations from the md documents, very
detailed"). The list is MODELS-BLOCKBENCH.md section 2 (furnace, anvil, drying rack, tanning rack, sawbench,
workbench) plus the brewing cauldron of 02-resources.md (potions are "brewed at a cauldron"). What each does:
furnace = ore to ingots with coal fuel (D-054, D-055); drying rack = plants to dried bundles (D-062); tanning rack =
hides to leather (D-029); sawbench = logs to planks; workbench = tools, hilts (D-058); anvil = smithing.
Section 3.11: wood planks with grain and nails, stone blocks with mortar and moss, metal bands and rivets, cloth with
folds; interactable parts get their own group with a pivot. Glow parts end in _glow. 2 px per unit, Imp 18 tall,
front = north (-z).
Usage: py build_stations.py [name ...]"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from station_lib import Station, station_mats, R, F, px, h2
from build_stalls import crate_with_pile, barrel, basket, fruit_cube, flat_mat, floor2

OUT = r"C:\Users\lucas\blockbench_models\props\stations"


def M(kind, rm, side=(48, 32), top=(32, 32), **extra):
    d = {"kind": kind, "ramp": R[rm], "side": side, "top": top, "no_lit2": True}
    if extra: d["extra"] = extra
    return d


def ingot(H, name, grp, x, y, z, rm, along="x", glow=False):
    s = (3, 1, 1.5) if along == "x" else (1.5, 1, 3)
    tag = f"ingot_{rm}_{along}"
    return H.item(name + ("_glow" if glow else ""), grp, [x - s[0] / 2, y, z - s[2] / 2], [x + s[0] / 2, y + s[1], z + s[2] / 2], tag,
                  lambda W, Hh, c: H.P.metal(R[rm], W, Hh, 3.2 + (0.8 if c == "up" else 0)))


def hammer(H, name, grp, x, y, z, yaw=0.0, head="steel", L=6):
    g = H.group(name, [x, y, z], grp)
    H.item(f"{name}_handle", g, [x - 0.5, y, z - L / 2], [x + 0.5, y + 1, z + L / 2], "hhandle",
           lambda W, Hh, c: H.P.boards(R["oak"], W, Hh, 0.2, orient="h" if W > Hh else "v", bw=2, nails=False, shadow_top=False),
           rot=(0, yaw, 0), origin=[x, y, z])
    hz = z - L / 2
    H.item(f"{name}_head", g, [x - 1.5, y - 0.5, hz - 1], [x + 1.5, y + 1.5, hz + 0.5], f"hhead_{head}",
           lambda W, Hh, c: H.P.metal(R[head], W, Hh, 3.4), rot=(0, yaw, 0), origin=[x, y, z])
    return g


# ---- z-fight free octagons (J00BA, 2026-11-09: the cauldron's brew flickered green and grey)
# house_lib.octo() makes an octagon from two crossed boxes; their tops and bottoms overlap in one plane with different
# paint, which flickers. These helpers cut the same octagon (or a ring of it) into rectangles that only meet edge to
# edge, and hide every side face that a neighbour covers completely.
def octo_cells(D, inset=None):
    """Half-unit cells (i, j) of house_lib.octo()'s outline, centred on 0 (cell i covers x = i/2 .. i/2 + 0.5)."""
    inset = inset if inset is not None else h2(D * 0.3)
    a, b = D / 2, (D - inset) / 2
    cells = set()
    for i in range(int(-a * 2), int(a * 2)):
        for j in range(int(-a * 2), int(a * 2)):
            x, z = (i + 0.5) / 2, (j + 0.5) / 2
            if (abs(x) < a and abs(z) < b) or (abs(x) < b and abs(z) < a):
                cells.add((i, j))
    return cells


def cell_rects(cells):
    """Greedy split of a cell set into non-overlapping rectangles (i0, j0, i1, j1), half-open."""
    left, rects = set(cells), []
    for j in sorted({c[1] for c in cells}):
        for i in sorted(i for i, jj in cells if jj == j):
            if (i, j) not in left:
                continue
            i1 = i
            while (i1 + 1, j) in left:
                i1 += 1
            j1 = j
            while all((k, j1 + 1) in left for k in range(i, i1 + 1)):
                j1 += 1
            for k in range(i, i1 + 1):
                for m in range(j, j1 + 1):
                    left.discard((k, m))
            rects.append((i, j, i1 + 1, j1 + 1))
    return rects


def octo_solid(H, name, grp, cells, y1, y2, mat, var, hide=()):
    """Boxes for a cell set between y1 and y2. A side face is hidden when the cells just past it are all filled
    (it's inside the solid); `hide` hides up / down on every box."""
    for k, (i0, j0, i1, j1) in enumerate(cell_rects(cells)):
        h = set(hide)
        if all((i1, m) in cells for m in range(j0, j1)): h.add("east")
        if all((i0 - 1, m) in cells for m in range(j0, j1)): h.add("west")
        if all((n, j1) in cells for n in range(i0, i1)): h.add("south")
        if all((n, j0 - 1) in cells for n in range(i0, i1)): h.add("north")
        H.box(f"{name}_{k + 1}", grp, [i0 / 2, y1, j0 / 2], [i1 / 2, y2, j1 / 2], mat, tuple(h), var)


# ==================================================================== 1. furnace
def furnace():
    H = Station("furnace", 4101, station_mats(extra={
        "brick": {"kind": "brick", "ramp": R["fire_brick"], "side": (64, 48), "top": (32, 32), "no_lit2": True, "extra": {"moss": False}},
        "cobble": {"kind": "cobble", "ramp": R["cobble"], "side": (96, 8), "top": (64, 48), "no_lit2": True},
        "wood": M("boards", "oak", (48, 16), (48, 16), bw=2, shadow_top=False),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
    }, post="walnut", plank="oak", trim="stone", trim_kind="ashlar"))
    g = {k: H.group(k, [0, 0, 0]) for k in ("base", "body", "fire", "chimney", "door", "bellows", "work", "details")}
    b = g["body"]
    H.box("plinth", g["base"], [-14, 0, -11], [14, 3, 11], "stone", ("down",), "plinth", place="ground")
    H.box("plinth_skirt", g["base"], [-15, 0, -12], [15, 1, 12], "cobble", ("down",), "skirt", place="ground")
    # body around the fire mouth (x -5..5, y 5..16 on the north face)
    H.box("body_left", b, [-12, 3, -9], [-5, 21, 9], "brick", ("down", "up"), "bl", place="ground")
    H.box("body_right", b, [5, 3, -9], [12, 21, 9], "brick", ("down", "up"), "br", place="ground")
    H.box("body_over_mouth", b, [-5, 16, -9], [5, 21, 9], "brick", ("up",), "bm")
    H.box("body_back", b, [-5, 3, -1], [5, 16, 9], "brick", ("down",), "bb")
    H.box("hearth", b, [-5, 3, -9.5], [5, 5, -1], "stone", ("down",), "hearth")
    for s, (a, c) in (("left", (-7, -5)), ("right", (5, 7))):
        H.box(f"jamb_{s}", b, [a, 3, -10], [c, 13, -9], "stone", ("down", "south"), "jamb")
    r, n = 5.75, 7
    for i in range(n):
        a = 180 * (i + 0.5) / n; ar = math.radians(a)
        cx, cy = -math.cos(ar) * r, 13 + math.sin(ar) * r
        H.box(f"arch_stone_{i + 1}", b, [cx - 1.25, cy - 1.25, -10.5], [cx + 1.25, cy + 1.25, -9], "stone", ("south",), f"arch{i % 2}",
              rot=(0, 0, 90 - a), origin=[cx, cy, -9.75])
    H.box("band_stone", b, [-12.5, 21, -9.5], [12.5, 23, 9.5], "stone", (), "band")
    for i, (w, d, y1, y2) in enumerate(((22, 16, 23, 26), (18, 13, 26, 29), (14, 10, 29, 31))):
        H.box(f"dome_{i + 1}", b, [-w / 2, y1, -d / 2], [w / 2, y2, d / 2], "brick", ("down",), f"dome{i}", place="top")
    for s, x in (("left", -12.05), ("right", 12.05)):
        vk = H.rect("vent_glow", 6, 2, lambda W, Hh: H.P.form(R["glow"], W, Hh, "lit", 4.4, noise=0.05))
        H.card(f"vent_{s}_glow", b, [x, 11, -1.5], [x, 12, 1.5], vk, faces=("east", "west"))
        H.box(f"vent_{s}_lintel", b, [x - 0.75 if x > 0 else x - 0.25, 12, -2.25], [x + 0.25 if x < 0 else x + 0.75, 13, 2.25], "stone", (), "vlint")
    # the fire: glowing back wall, coal bed with embers, crossed flames, a crucible of molten metal
    f = g["fire"]
    bk = H.rect("mouth_back", 20, 22, lambda W, Hh: H.P.flame(W, Hh, "lit") if False else H.P.form(R["glow"], W, Hh, "lit", 3.6, noise=0.2, vert=-2.0))
    H.card("mouth_back_glow", f, [-5, 5, -1.05], [5, 16, -1.05], bk)
    H.item("coal_bed_glow", f, [-4.5, 5, -8.5], [4.5, 6.5, -1.5], "coalbed", lambda W, Hh, c: H.P.coal(W, Hh, c, embers=0.35))
    for i, (x, z, w, hh) in enumerate(((-2.5, -4, 3, 6), (2, -5, 3, 5), (0, -3, 4, 8))):
        H.flame_cards(f"flame_{i + 1}", f, x, 6.5, z, w, hh)
    H.item("crucible", f, [-1.5, 6.5, -7.5], [1.5, 9.5, -4.5], "crucible", lambda W, Hh, c: H.P.form(R["clay_pot"], W, Hh, c, 3.2))
    H.item("crucible_melt_glow", f, [-1, 9.5, -7], [1, 10, -5], "melt", lambda W, Hh, c: H.P.liquid(R["glow"], W, Hh, c, glow=True))
    # chimney with iron band and cap
    c = g["chimney"]
    H.box("chimney_stack", c, [-3.5, 31, -3.5], [3.5, 46, 3.5], "brick", ("down",), "stack", place="top")
    H.box("chimney_band", c, [-4, 38, -4], [4, 39, 4], "iron", (), "cband")
    H.box("chimney_cap", c, [-4.5, 46, -4.5], [4.5, 47.5, 4.5], "stone", ("up",), "ccap")
    for i, (a, b2) in enumerate(((-4.5, -2.5), (2.5, 4.5))):
        H.box(f"chimney_lip_{i + 1}", c, [a, 47.5, -4.5], [b2, 48.5, 4.5], "stone", ("down",), "clip")
    sk = H.rect("chimney_soot", 10, 10, lambda W, Hh: H.P.coal(W, Hh, "up", embers=0.08))
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["up"] = F(sk)
    H.m.cube("chimney_soot", c, [-2.5, 47.5, -4.5], [2.5, 47.5, 4.5], fs)
    # iron door, hinged on the left jamb and swung open
    dg = H.group("furnace_door", [-6.5, 5, -10], g["door"])
    door = lambda W, Hh, c: H.P.metal(R["iron"], W, Hh, 3.0) if c != "lit" else H.P.mould(W, Hh, "up", 3)
    H.item("door_panel", dg, [-6.5, 5, -10.5], [-0.5, 14, -10], "door_iron", lambda W, Hh, c: H.P.form(R["iron"], W, Hh, c, 3.3), rot=(0, 115, 0), origin=[-6.5, 5, -10])
    for i, y in enumerate((6.5, 11.5)):
        H.box(f"door_strap_{i + 1}", dg, [-6.5, y, -11], [-1, y + 1, -10.5], "steel", ("south",), "strap", rot=(0, 115, 0), origin=[-6.5, 5, -10])
    H.box("door_handle", dg, [-2.5, 9, -11.5], [-1.5, 10, -10.5], "steel", (), "dhandle", rot=(0, 115, 0), origin=[-6.5, 5, -10])
    for i, y in enumerate((6, 12)):
        H.box(f"door_hinge_{i + 1}", dg, [-7.5, y, -10.75], [-6, y + 1.5, -9.75], "iron", (), "dhinge")
    # bellows on the east side (pivot at the nozzle so the top board can pump)
    bw = H.group("bellows_pump", [13, 8, 1], g["bellows"])
    for i, x in enumerate((15, 19.5)):
        H.box(f"bellows_leg_{i + 1}", bw, [x - 0.5, 0, -1.5], [x + 0.5, 6, -0.5], "wood", ("down",), "bleg")
        H.box(f"bellows_leg_{i + 4}", bw, [x - 0.5, 0, 2.5], [x + 0.5, 6, 3.5], "wood", ("down",), "bleg")
    H.box("bellows_board_low", bw, [14, 6, -2], [21.5, 7, 4], "wood", (), "bboard")
    for i, (x1, x2, z1, z2, y1, y2) in enumerate(((14.5, 21, -1.5, 3.5, 7, 8), (14.5, 20.5, -1, 3, 8, 9))):
        H.item(f"bellows_leather_{i + 1}", bw, [x1, y1, z1], [x2, y2, z2], f"bel{i}", lambda W, Hh, c: H.P.bellows(W, Hh, c), hide=("down", "up"))
    H.box("bellows_board_top", bw, [14, 9, -2], [21.5, 10, 4], "wood", (), "bboard", rot=(0, 0, 7.5), origin=[14, 9, 1])
    H.box("bellows_nozzle", bw, [12, 7, 0.5], [14.5, 8, 1.5], "steel", (), "nozzle")
    H.box("bellows_handle", bw, [21.5, 9.5, 0.5], [24.5, 10.5, 1.5], "wood", (), "bhandle", rot=(0, 0, 7.5), origin=[14, 9, 1])
    H.box("bellows_grip", bw, [24, 9.5, -0.5], [25, 10.5, 2.5], "wood", (), "bgrip", rot=(0, 0, 7.5), origin=[14, 9, 1])
    # work ledge with an ingot mould of molten metal
    w = g["work"]
    H.box("ledge_corbel", w, [7, 6, -11], [11, 8, -9], "stone", (), "corbel")
    H.box("ledge", w, [6, 8, -13], [12, 9.5, -9], "stone", (), "ledge")
    H.item("ingot_mould", w, [6.5, 9.5, -12.5], [11.5, 10.5, -9.5], "mould", lambda W, Hh, c: H.P.mould(W, Hh, c, 3))
    for i, x in enumerate((7.5, 9, 10.5)):
        H.item(f"mould_ingot_{i + 1}_glow", w, [x - 0.5, 10.25, -12], [x + 0.5, 10.75, -10], "moltenbar",
               lambda W, Hh, c: H.P.liquid(R["glow"], W, Hh, c, glow=True))
    # details: coal bin with shovel, ingot stack, hanging tongs, soot bucket
    d = g["details"]
    crate_with_pile(H, "coal_bin", d, -21.5, -15.5, -7, 1, 0, 5, "coal", 1.0, wood="walnut")
    for i, (x, z) in enumerate(((-19, -4), (-17.5, -2.5))):
        H.item(f"coal_lump_{i + 1}", d, [x - 0.75, 6, z - 0.75], [x + 0.75, 7, z + 0.75], "lump", lambda W, Hh, c: H.P.form(R["coal"], W, Hh, c, 3.8, hl=True))
    H.rotbar("shovel_handle", d, [-15, 0.5, -9], [-14.5, 13, -10], 1.0, "wood")
    H.item("shovel_blade", d, [-16.5, 0, -9.75], [-13.5, 3.5, -9.25], "shovel", lambda W, Hh, c: H.P.metal(R["iron"], W, Hh, 3.0),
           rot=(-11.25, 0, 0), origin=[-15, 0, -9.5])
    H.box("ingot_pallet", d, [-21.5, 0, 3], [-15.5, 1, 10], "wood", ("down",), "pallet")
    for i, (x, y, z, rm, al) in enumerate(((-20, 1, 4.5, "copper", "x"), (-17, 1, 4.5, "copper", "x"), (-20, 1, 6.5, "iron", "x"),
                                          (-17, 1, 6.5, "iron", "x"), (-20, 1, 8.5, "gold", "x"), (-17, 1, 8.5, "gold", "x"),
                                          (-19, 2, 6.5, "steel", "z"), (-17.5, 2, 6.5, "copper", "z"), (-18.25, 3, 6.5, "gold", "x"))):
        ingot(H, f"ingot_{i + 1}", d, x, y, z, rm, al)
    H.box("tong_hook", d, [-12.5, 17, -4.5], [-11.5, 18, -3.5], "iron", (), "thook")
    for i, (zo, rz) in enumerate(((-4.25, 6), (-3.75, -6))):
        H.box(f"tongs_arm_{i + 1}", d, [-13, 8.5, zo - 0.25], [-12.5, 17.5, zo + 0.25], "steel", (), "tong", rot=(rz, 0, 0), origin=[-12.75, 17, -4])
    barrel(H, "quench_bucket", d, 17, -9, 4, 4, wood="oak")
    H.item("quench_water", d, [15.5, 3.5, -10.5], [18.5, 3.75, -7.5] if False else [18.5, 4, -7.5], "water",
           lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c), hide=("down", "north", "south", "east", "west"))
    return H


# ==================================================================== 2. anvil
def anvil():
    H = Station("anvil", 4202, station_mats(extra={
        "steel": M("metal", "steel", (32, 16), (32, 16)),
        "wood": M("boards", "oak", (48, 16), (48, 16), bw=2, shadow_top=False),
        "stone": M("ashlar", "stone", (40, 12), (24, 24)),
    }))
    g = {k: H.group(k, [0, 0, 0]) for k in ("stump", "anvil_body", "work", "grindstone", "details")}
    st = g["stump"]
    H.log("stump", st, [-5.5, 0, -5], [5.5, 9, 5], axis="y", hide=("down",))
    for i, (frm, to) in enumerate((([-7, 0, -2], [-5.5, 2.5, 2]), ([5.5, 0, -3], [7.5, 2, 1]), ([-2, 0, -6.5], [2.5, 3, -5]),
                                   ([-1, 0, 5], [3, 2, 6.5]))):
        H.item(f"root_{i + 1}", st, frm, to, "root", lambda W, Hh, c: H.P.bark(R["bark"], W, Hh, c if c in ("lit", "shade") else "lit"))
    a = g["anvil_body"]
    steel = lambda W, Hh, c: H.P.metal(R["steel"], W, Hh, 2.6 + (1.2 if c == "up" else 0) + (0.3 if c == "lit" else -0.3))
    H.item("anvil_feet", a, [-4.5, 9, -3.5], [4.5, 10.5, 3.5], "afeet", steel)
    H.item("anvil_base", a, [-3.5, 10.5, -2.5], [3.5, 11.5, 2.5], "abase", steel)
    H.item("anvil_waist", a, [-2, 11.5, -1.5], [2, 13, 1.5], "awaist", steel)
    H.item("anvil_face", a, [-5, 13, -2.5], [5, 15.5, 2.5], "aface", steel)
    for i, (x1, x2, hw, y1) in enumerate(((-8, -5, 2, 13.5), (-10, -8, 1.5, 14), (-11.5, -10, 1, 14.5), (-12.5, -11.5, 0.5, 14.75))):
        H.item(f"anvil_horn_{i + 1}", a, [x1, y1, -hw], [x2, 15.5 if i < 3 else 15.25, hw], f"ahorn{i}", steel)
    H.item("anvil_heel", a, [5, 14, -2], [7.5, 15.5, 2], "aheel", steel)
    hk = H.rect("hardy_hole", 2, 2, lambda W, Hh: H.P.form(R["coal"], W, Hh, "down", 2.0))
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["up"] = F(hk)
    H.m.cube("anvil_hardy_hole", a, [5.5, 15.55, -0.5], [6.5, 15.55, 0.5], fs)
    w = g["work"]
    H.item("hot_ingot_glow", w, [-2, 15.5, -1], [1, 16, 0.5], "hotbar", lambda W, Hh, c: H.P.liquid(R["glow"], W, Hh, c, glow=True))
    for i, (x, y, z, s) in enumerate(((-1, 17.5, -2, 0.5), (1.5, 18.5, -1.5, 0.5), (0, 19.5, 0.5, 0.5), (-2.5, 18, 1, 0.5))):
        H.item(f"spark_{i + 1}_glow", w, [x, y, z], [x + s, y + s, z + s], "spark", lambda W, Hh, c: H.P.form(R["glow"], W, Hh, c, 5.5, noise=0), hide=())
    hammer(H, "forge_hammer", w, 3.5, 15.5, 1, yaw=-60, L=7)
    for i, (dz, ry) in enumerate(((-0.25, 8), (0.25, -8))):
        H.box(f"tongs_{i + 1}", w, [-7, 0.5, -7 + dz - 0.25], [-6.5, 12, -7 + dz + 0.25], "steel", (), "tongs",
              rot=(0, 0, -16 + ry), origin=[-6.75, 0.5, -7])
    # grindstone on a frame with a crank
    gs = H.group("grindstone_wheel", [14, 9, 0], g["grindstone"])
    for i, z in enumerate((-3, 3)):
        H.box(f"grind_frame_{i + 1}", gs, [11, 0, z - 0.75], [17, 1.5, z + 0.75], "wood", ("down",), "gfr")
        H.box(f"grind_post_{i + 1}", gs, [13.25, 1.5, z - 0.75], [14.75, 9.5, z + 0.75], "wood", (), "gpost")
    H.wheel("grind_wheel", gs, 13.5, 14.5, 9, 0, 3.5, rim="stone", spoke="stone", hub="iron") if False else None
    ws = lambda W, Hh, c: H.P.form(R["stone"], W, Hh, c, 3.6)
    for k, (ang, th) in enumerate(((0, 1.5), (45, 1.0), (90, 2.0), (-45, 0.5))):
        H.item(f"grind_wheel_{k + 1}", gs, [14 - th / 2, 5, -1.5], [14 + th / 2, 13, 1.5], f"gwheel{k}", ws, hide=(),
               rot=(ang, 0, 0), origin=[14, 9, 0])
    H.box("grind_axle", gs, [14, 8.5, -4], [15, 9.5, 4], "iron", (), "gaxle", origin=[14.5, 9, 0]) if False else \
        H.box("grind_axle", gs, [13.5, 8.5, -4], [14.5, 9.5, 4], "iron", (), "gaxle")
    H.box("grind_crank", gs, [13.5, 8.5, 4], [14.5, 12, 5], "iron", (), "gcrank")
    H.box("grind_crank_grip", gs, [13.5, 11, 5], [14.5, 12, 7], "wood", (), "ggrip")
    H.box("grind_trough", gs, [12, 1.5, -2], [16, 4, 2], "wood", ("down",), "gtrough")
    H.item("grind_trough_water", gs, [12.5, 3.5, -1.5], [15.5, 3.5, 1.5], "water", lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    # details: quench bucket, tool rack with hammers and a horseshoe, scrap and ingots on the ground
    d = g["details"]
    barrel(H, "quench_bucket", d, -11, -6, 5, 5, wood="oak")
    H.item("quench_water", d, [-13, 4.5, -8], [-9, 4.5, -4], "water", lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    rk = H.group("tool_rack", [0, 0, 9], d)
    for i, x in enumerate((-6, 6)):
        H.box(f"rack_post_{i + 1}", rk, [x - 0.75, 0, 8.5], [x + 0.75, 16, 10], "wood", ("down",), "rpost")
    H.box("rack_bar", rk, [-7, 14, 8.5], [7, 15.5, 10], "wood", (), "rbar")
    for i, x in enumerate((-4, -1, 2, 4.5)):
        H.box(f"rack_peg_{i + 1}", rk, [x - 0.25, 13, 7.5], [x + 0.25, 13.5, 8.5], "iron", (), "rpeg")
    for i, (x, hd) in enumerate(((-4, "steel"), (-1, "iron"))):
        H.box(f"rack_hammer_{i + 1}_handle", rk, [x - 0.5, 6, 7.5], [x + 0.5, 13, 8.5], "wood", (), "rhh")
        H.box(f"rack_hammer_{i + 1}_head", rk, [x - 1.5, 5, 7.25], [x + 1.5, 6.5, 8.75], hd, (), f"rhd{i}")
    hs = [([1, 10, 7.75], [1.5, 13, 8.25]), ([3, 10, 7.75], [3.5, 13, 8.25]), ([1, 9.5, 7.75], [3.5, 10, 8.25])]
    for i, (fr, to) in enumerate(hs):
        H.box(f"horseshoe_{i + 1}", rk, fr, to, "iron", (), "hshoe")
    H.box("rack_tongs", rk, [4.25, 5, 7.75], [4.75, 13, 8.25], "steel", (), "rtong")
    for i, (x, z, rm, al) in enumerate(((-9, 4, "iron", "x"), (-9, 5.5, "iron", "x"), (-9, 4.75, "copper", "z"))):
        ingot(H, f"ground_ingot_{i + 1}", d, x, 0 if i < 2 else 1, z, rm, al)
    for i, (x, z, ry) in enumerate(((8, -7, 20), (10, -5, -35), (7, -4.5, 60))):
        H.box(f"scrap_{i + 1}", d, [x - 1, 0, z - 0.5], [x + 1, 0.5, z + 0.5], "iron", ("down",), "scrap", rot=(0, ry, 0), origin=[x, 0, z])
    return H


# ==================================================================== 3. workbench
def workbench():
    H = Station("workbench", 4303, station_mats(extra={
        "wood": M("boards", "oak", (64, 24), (64, 24), bw=2, shadow_top=False),
        "dark": M("boards", "walnut", (64, 24), (64, 24), bw=2, shadow_top=False),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
        "peg": M("boards", "pine_wood", (64, 32), (16, 16), bw=3, orient="v", lap=False, shadow_top=False),
    }, plank="pine_wood", top="oak"))
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "top", "vise", "drawer", "pegboard", "tools", "details")}
    fr = g["frame"]
    for s, x in (("left", -13), ("right", 13)):
        for e, z in (("front", -3.5), ("back", 3.5)):
            H.box(f"leg_{e}_{s}", fr, [x - 1, 0, z - 1], [x + 1, 12, z + 1], "dark", ("down",), f"leg{e}")
        H.box(f"side_rail_{s}", fr, [x - 0.75, 2, -3], [x + 0.75, 3.5, 3], "dark", (), "srail")
    for e, z in (("front", -3.5), ("back", 3.5)):
        H.box(f"long_rail_{e}", fr, [-12, 2, z - 0.75], [12, 3.5, z + 0.75], "dark", (), "lrail")
    H.box("shelf", fr, [-12, 3.5, -3], [12, 4, 3], "plank", ("down",), "shelf")
    H.box("apron_front", fr, [-12, 9.5, -4.5], [12, 12, -3.5], "dark", ("south",), "apron")
    H.box("apron_back", fr, [-12, 9.5, 3.5], [12, 12, 4.5], "dark", ("north",), "apronb")
    t = g["top"]
    for i, z in enumerate((-5.5, -3, -0.5, 2)):
        H.box(f"top_plank_{i + 1}", t, [-15, 12, z], [15, 13.5, z + 2.5], "top", ("down",), f"tp{i}")
    for s, x in (("left", -16), ("right", 15)):
        H.box(f"breadboard_{s}", t, [x, 12, -6], [x + 1, 14, 5], "dark", ("down",), "bread")
    for i, x in enumerate((-10, 0, 10)):
        H.box(f"dog_hole_{i + 1}", t, [x - 0.5, 13.5, -5], [x + 0.5, 13.5, -4], "dark", (), "dog") if False else None
    # front vise on the left end (the jaw slides: pivot at the screw)
    v = H.group("front_vise", [-12, 11, -7], g["vise"])
    H.box("vise_jaw", v, [-15, 8.5, -7.5], [-9, 13.5, -6], "dark", (), "vjaw")
    H.box("vise_screw", v, [-12.5, 10.5, -10], [-11.5, 11.5, -6], "steel", (), "vscrew")
    H.box("vise_bar", v, [-15, 10.75, -10.5], [-9, 11.25, -10], "wood", (), "vbar")
    for s, x in (("left", -15.5), ("right", -9)):
        H.box(f"vise_knob_{s}", v, [x, 10.5, -10.75], [x + 0.5, 11.5, -9.75], "dark", (), "vknob")
    H.box("vise_guide", v, [-14, 9.5, -6], [-13, 10.5, -4.5], "wood", (), "vguide")
    # drawer (slides out: pivot at its back)
    dr = H.group("tool_drawer", [2, 10.5, -4], g["drawer"])
    H.box("drawer_front", dr, [-3, 9.75, -5.5], [7, 12, -4.5], "wood", ("south",), "dfront") if False else \
        H.box("drawer_front", dr, [-3, 9.5, -5.5], [7, 12, -4.5], "wood", ("south",), "dfront")
    H.box("drawer_pull", dr, [1, 10.5, -6], [3, 11, -5.5], "gold", (), "dpull")
    # tools on the top
    tl = g["tools"]
    pg = H.group("hand_plane", [6, 13.5, -1], tl)
    H.box("plane_body", pg, [4, 13.5, -2], [9, 15, 0], "dark", (), "pbody")
    H.box("plane_tote", pg, [7.5, 15, -1.5], [8.5, 17, -0.5], "wood", (), "ptote")
    H.box("plane_knob", pg, [4.5, 15, -1.5], [5.5, 16, -0.5], "wood", (), "pknob")
    H.box("plane_blade", pg, [6, 15, -2], [6.5, 16.5, 0], "steel", (), "pblade", rot=(0, 0, -30), origin=[6.25, 15, -1])
    for i, (x, z, ry) in enumerate(((10, -1.5, 10), (11, 0.5, -30), (9.5, 1, 50), (12, -2.5, 75), (3, 1.5, -20))):
        H.item(f"shaving_{i + 1}", tl, [x - 1, 13.5, z - 0.5], [x + 1, 14, z + 0.5], "shaving", lambda W, Hh, c: H.P.sawdust(W, Hh, c),
               rot=(0, ry, 0), origin=[x, 13.5, z])
    hammer(H, "claw_hammer", tl, -4, 13.5, -1.5, yaw=75, L=5)
    sq = H.group("try_square", [-9, 13.5, 1], tl)
    H.box("square_stock", sq, [-11, 13.5, 0], [-10, 14, 5], "dark", (), "sqs")
    H.box("square_blade", sq, [-10, 13.5, 4], [-5, 14, 4.5], "steel", (), "sqb")
    for i, (x, z) in enumerate(((-2, 2.5), (-0.5, 3))):
        H.box(f"chisel_{i + 1}_handle", tl, [x - 0.5, 13.5, z - 2], [x + 0.5, 14.5, z], "wood", (), "chh")
        H.box(f"chisel_{i + 1}_blade", tl, [x - 0.25, 13.5, z - 4], [x + 0.25, 14, z - 2], "steel", (), "chb")
    hg = H.group("hilt_blank", [0, 13.5, -3], tl)
    H.box("hilt_grip", hg, [-3, 13.5, -4], [1, 14.5, -3], "wood", (), "hgrip")
    H.box("hilt_guard", hg, [1, 13.5, -5], [1.5, 15, -2], "gold", (), "hguard")
    H.box("hilt_pommel", hg, [-4, 13.5, -4.25], [-3, 15, -2.75], "gold", (), "hpommel") if False else \
        H.box("hilt_pommel", hg, [-4, 13.5, -4.5], [-3, 15, -2.5], "gold", (), "hpommel")
    H.item("nail_jar", tl, [12, 13.5, 2], [14, 16, 4], "nailjar", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 3.6, hl=True))
    H.item("nail_jar_nails", tl, [12.5, 16, 2.5], [13.5, 16.5, 3.5], "nails", lambda W, Hh, c: H.P.coal(W, Hh, c))
    H.box("pencil", tl, [-7, 13.5, -4.5], [-3, 14, -4], "gold", (), "pencil", rot=(0, 15, 0), origin=[-5, 13.5, -4.25])
    # pegboard with hung tools and a small top shelf
    p = g["pegboard"]
    for s, x in (("left", -14.5), ("right", 14.5)):
        H.box(f"board_post_{s}", p, [x - 1, 13.5, 4.5], [x + 1, 30, 6.5], "dark", ("down",), "bpost")
    H.box("pegboard", p, [-13.5, 13.5, 5], [13.5, 27, 6], "peg", ("down",), "pboard")
    H.box("board_shelf", p, [-14, 27, 3], [14, 28, 6.5], "dark", (), "bshelf")
    H.box("board_cap", p, [-16, 30, 4], [16, 31.5, 7], "dark", (), "bcap")
    sw = H.group("hung_saw", [-9, 25, 4.5], p)
    sk = H.rect("saw_blade", 14, 7, lambda W, Hh: H.P.blade(W, Hh, "lit"))
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["north"] = F(sk); fs["south"] = F(sk, mirror=True)
    H.m.cube("saw_blade", sw, [-12, 17.5, 4.75], [-5, 21, 4.75], fs, (0, 0, -8), [-8.5, 19, 4.75])
    H.box("saw_handle", sw, [-5.5, 19, 4.25], [-3, 22, 5], "wood", (), "shandle", rot=(0, 0, -8), origin=[-8.5, 19, 4.75]) if False else \
        H.box("saw_handle", sw, [-5.5, 19, 4], [-3, 22, 5], "wood", (), "shandle", rot=(0, 0, -8), origin=[-8.5, 19, 4.75])
    H.box("peg_saw", p, [-6, 22, 4], [-5.5, 22.5, 5], "wood", (), "peg")
    ag = H.group("hung_axe", [1, 25, 4.5], p)
    H.box("axe_handle", ag, [0.5, 15, 4], [1.5, 25, 5], "wood", (), "ahandle")
    H.box("axe_head", ag, [-1.5, 22, 4], [0.5, 25, 5], "steel", (), "ahead")
    H.box("axe_edge", ag, [-2, 21.5, 4.25], [-1.5, 25.5, 4.75], "steel", (), "aedge")
    H.box("peg_axe", p, [0.5, 25.5, 4], [1.5, 26, 5], "wood", (), "peg")
    for i, x in enumerate((5, 7, 9)):
        H.box(f"peg_{i + 1}", p, [x - 0.25, 24, 4], [x + 0.25, 24.5, 5], "wood", (), "peg")
        H.box(f"hung_chisel_{i + 1}_handle", p, [x - 0.5, 21, 4.25], [x + 0.5, 24, 4.75], "wood", (), "hch")
        H.box(f"hung_chisel_{i + 1}_blade", p, [x - 0.25, 18 + i * 0.5, 4.25], [x + 0.25, 21, 4.75], "steel", (), f"hcb{i}")
    rg = H.group("rope_coil", [11, 22, 4.5], p)
    for k, (w_, h_) in enumerate(((4, 4), (3, 3))):
        H.item(f"rope_coil_{k + 1}", rg, [11 - w_ / 2, 22 - h_ / 2, 4], [11 + w_ / 2, 22 + h_ / 2, 5 - k * 0.5], f"rope{k}",
               lambda W, Hh, c: H.P.rope(W, Hh, c), rot=(0, 0, 45 * k), origin=[11, 22, 4.5])
    for i, (x, rm) in enumerate(((-10, "glow_green"), (-7.5, "cork"), (8, "copper"))):
        H.item(f"shelf_jar_{i + 1}", p, [x - 1, 28, 4], [x + 1, 30.5, 6], f"sjar{i}", lambda W, Hh, c, r_=rm: H.P.form(R[r_], W, Hh, c, 3.4, hl=True))
    H.lantern_hang("lantern", p, 13, 30, 3.5, chain=2) if False else H.lantern("lantern", p, "north", 4.5, 12.5, 18)
    # details: planks and offcuts on the shelf, shavings and a sawn log on the floor
    d = g["details"]
    for i in range(3):
        H.box(f"shelf_plank_{i + 1}", d, [-11 + i * 0.5, 4 + i, -2.5], [11 - i * 0.5, 5 + i, 2.5 - (i % 2) * 0.5], "plank", ("down",), f"spl{i}")
    for i, (x, z, w_) in enumerate(((-18, -6, 3), (-19, -2, 2), (17.5, -5, 2.5))):
        H.item(f"offcut_{i + 1}", d, [x - w_ / 2, 0, z - 1], [x + w_ / 2, 2, z + 1], "offcut",
               lambda W, Hh, c: H.P.ring_end(W, Hh, c) if c in ("lit",) else H.P.form(R["pine_wood"], W, Hh, c, 3.6))
    for i, (x, z) in enumerate(((-6, -8), (4, -7.5), (8, -9))):
        H.item(f"floor_shavings_{i + 1}", d, [x - 1.5, 0, z - 1], [x + 1.5, 0.5, z + 1], "fshave", lambda W, Hh, c: H.P.sawdust(W, Hh, c))
    H.log("small_log", d, [16, 0, -1], [23, 4, 3], axis="x", hide=("down",))
    return H


# ==================================================================== 4. sawbench
def sawbench():
    H = Station("sawbench", 4404, station_mats(extra={
        "wood": M("boards", "oak", (64, 24), (64, 24), bw=2, shadow_top=False),
        "plankp": M("boards", "pine_wood", (72, 16), (72, 24), bw=3, shadow_top=False),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
    }))
    g = {k: H.group(k, [0, 0, 0]) for k in ("sawbucks", "log", "saw", "planks", "chopping", "details")}
    sb = g["sawbucks"]
    for s, x in (("left", -9), ("right", 9)):
        for k, a in enumerate((25, -25)):
            H.box(f"sawbuck_{s}_leg_{k + 1}", sb, [x - 0.75 + (k - 0.5) * 1.5, -1, -1], [x + 0.75 + (k - 0.5) * 1.5, 17, 1], "wood", (),
                  f"sbleg{k}", rot=(a, 0, 0), origin=[x, 9, 0])
        H.box(f"sawbuck_{s}_peg", sb, [x - 2, 8.5, -0.5], [x + 2, 9.5, 0.5], "wood", (), "sbpeg")
    H.box("sawbuck_stretcher", sb, [-10, 4, -0.75], [10, 5.5, 0.75], "wood", (), "stretch")
    lg = g["log"]
    H.log("log_main", lg, [-16, 10, -3], [4.5, 16, 3], axis="x")
    H.log("log_cut_piece", lg, [5, 10, -3], [12, 16, 3], axis="x")
    sd = H.rect("kerf", 2, 12, lambda W, Hh: H.P.form(R["coal"], W, Hh, "lit", 2.6))
    H.card("saw_kerf", lg, [4.75, 10, -3.05], [4.75, 16, 3.05], sd, faces=("east", "west"))
    # crosscut saw sitting in the cut (pivot at the cut so it can rock)
    sw = H.group("crosscut_saw", [4.75, 14, 0], g["saw"])
    bk = H.rect("saw_long", 36, 9, lambda W, Hh: H.P.blade(W, Hh, "lit"))
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["east"] = F(bk); fs["west"] = F(bk, mirror=True)
    H.m.cube("saw_blade", sw, [4.75, 13.5, -10], [4.75, 18, 8], fs, (12, 0, 0), [4.75, 15, 0])
    for i, (z1, z2) in enumerate(((-12, -10), (8, 10))):
        H.box(f"saw_handle_{i + 1}", sw, [4, 15, z1], [5.5, 18.5, z2], "wood", (), "shan", rot=(12, 0, 0), origin=[4.75, 15, 0])
        H.box(f"saw_handle_{i + 1}_cap", sw, [3.75, 18.5, z1 - 0.5], [5.75, 19.5, z2 + 0.5], "wood", (), "shcap", rot=(12, 0, 0), origin=[4.75, 15, 0])
    # plank stack on bearers
    pl = g["planks"]
    for i, z in enumerate((9, 15)):
        H.box(f"bearer_{i + 1}", pl, [-12, 0, z - 0.75], [12, 1.5, z + 0.75], "wood", ("down",), "bearer")
    for k in range(4):
        for j in range(3 - (k // 2)):
            z0 = 8 + j * 3.5 + (k % 2) * 0.5
            H.box(f"plank_{k + 1}_{j + 1}", pl, [-14 + k * 0.5, 1.5 + k, z0], [14 - k * 0.5, 2.5 + k, z0 + 3], "plankp", ("down",), f"pl{k}{j}")
    # chopping block with an axe in it
    ch = g["chopping"]
    H.log("chopping_block", ch, [-23, 0, -9], [-17, 6, -3], axis="y", hide=("down",))
    ag = H.group("chop_axe", [-20, 6, -6], ch)
    H.box("chop_axe_handle", ag, [-20.5, 6, -6.5], [-19.5, 14, -5.5], "wood", (), "cah", rot=(0, 0, 25), origin=[-20, 6, -6])
    H.box("chop_axe_head", ag, [-21.5, 5, -6.75], [-18.5, 7.5, -5.25], "steel", (), "cahd", rot=(0, 0, 25), origin=[-20, 6, -6])
    # log pile and splits
    d = g["details"]
    for i, (z, y, x0) in enumerate(((-12, 0, 12), (-8, 0, 12), (-10, 4, 12.5))):
        H.log(f"pile_log_{i + 1}", d, [x0, y, z - 2], [x0 + 9, y + 4, z + 2], axis="x", hide=("down",) if y == 0 else ())
    for i, (x, z, ry) in enumerate(((-22, 1, 20), (-19, 2, -40), (-21, -1, 75))):
        H.item(f"split_{i + 1}", d, [x - 1, 0, z - 2], [x + 1, 1.5, z + 2], "split", lambda W, Hh, c: H.P.form(R["logend"], W, Hh, c, 3.6),
               rot=(0, ry, 0), origin=[x, 0, z])
    for i, (x, z, w_, d_, hh) in enumerate(((5, -4, 6, 5, 1), (5, -4, 3, 3, 1.5), (-7, -6, 4, 3, 0.5), (2, 5, 4, 3, 0.5))):
        H.item(f"sawdust_{i + 1}", d, [x - w_ / 2, 0, z - d_ / 2], [x + w_ / 2, hh, z + d_ / 2], f"sdust{i}", lambda W, Hh, c: H.P.sawdust(W, Hh, c))
    bg = H.group("plank_bundle", [-16, 0, 8], d)
    for k in range(3):
        H.box(f"bundle_plank_{k + 1}", bg, [-22 + k * 0.5, k * 1.0, 6 + (k % 2) * 0.5], [-10 + k * 0.5, 1 + k * 1.0, 9 + (k % 2) * 0.5], "plankp", ("down",) if k == 0 else (), f"bp{k}")
    for k, x in enumerate((-19, -13)):
        H.item(f"bundle_rope_{k + 1}", bg, [x - 0.5, -0.25 + 0.25, 5.5], [x + 0.5, 3.5, 10], "rope_band", lambda W, Hh, c: H.P.rope(W, Hh, c), hide=("down",))
    for i, (x, z, ry) in enumerate(((-3, -8, 15), (8, 4, -40), (-12, 3, 70), (14, -3, 30), (0, 8, -10))):
        H.item(f"bark_chip_{i + 1}", d, [x - 1, 0, z - 0.5], [x + 1, 0.5, z + 0.5], "chip", lambda W, Hh, c: H.P.bark(R["bark"], W, Hh, "lit" if c == "up" else c if c in ("lit", "shade") else "shade"),
               rot=(0, ry, 0), origin=[x, 0, z])
    H.item("wedge", d, [-14, 0, -8], [-12, 1.5, -5], "wedge", lambda W, Hh, c: H.P.metal(R["iron"], W, Hh, 3.0))
    mg = H.group("mallet", [-11, 0, -10], d)
    H.box("mallet_head", mg, [-12, 0, -11], [-9, 2, -9], "wood", ("down",), "mhead")
    H.box("mallet_handle", mg, [-9, 0.5, -10.5], [-4, 1.5, -9.5], "wood", (), "mhan")
    return H


# ==================================================================== 5. drying rack
PLANTS = [("nettle", "nettle", None), ("marigold", "orange", None), ("bluebell", "bluebell", None), ("thornroot", "berry", None),
          ("sunpetal", "sunpetal", None), ("nightshade", "grape", None), ("frostbloom", "frostbloom", None),
          ("bloodcap", "apple", None), ("voidlily", "glow_violet", "glow"), ("starmoss", "lemon", "glow")]


def drying_rack():
    H = Station("drying_rack", 4505, station_mats(extra={
        "wood": M("boards", "oak", (64, 24), (64, 24), bw=2, shadow_top=False),
        "pole": M("boards", "walnut", (16, 64), (16, 16), bw=2, orient="v", lap=False, shadow_top=False),
        "roof": {"kind": "shingle", "ramp": R["tile_moss"], "side": (64, 24), "top": (64, 40), "under": (48, 48), "no_lit2": True,
                 "extra": {"style": "shake", "moss": True}},
        "rope": flat_mat("rope", (32, 8)),
    }))
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "roof_g", "bundles", "tray", "details")}
    fr = g["frame"]
    yR = 26.0
    for s, x in (("left", -14), ("right", 14)):
        for k, a in enumerate((-15, 15)):
            H.box(f"aframe_{s}_leg_{k + 1}", fr, [x - 0.75 + (k - 0.5) * 1.5, 0, -1], [x + 0.75 + (k - 0.5) * 1.5, yR + 1, 1], "pole", ("down",),
                  f"afl{k}", rot=(a, 0, 0), origin=[x, 0, 0]) if False else None
    # legs as bars from the ground to the ridge
    for s, x in (("left", -14), ("right", 14)):
        for e, z in (("front", -7), ("back", 7)):
            H.rotbar(f"leg_{e}_{s}", fr, [x, 0, z], [x, yR, 0], 1.5, "pole")
        H.box(f"foot_{s}", fr, [x - 1, 0, -8.5], [x + 1, 1, 8.5], "wood", ("down",), "foot")
        H.box(f"crossbar_{s}", fr, [x - 0.5, 15, -3.5], [x + 0.5, 16, 3.5], "wood", (), "cross")
    H.box("ridge_pole", fr, [-16, yR - 0.5, -1], [16, yR + 1, 1], "pole", (), "ridge") if False else \
        H.box("ridge_pole", fr, [-16, yR - 0.5, -1], [16, yR + 1, 1], "wood", (), "ridge")
    rail_z = []
    for e, z in (("front", -3.5), ("back", 3.5)):
        H.box(f"rail_{e}", fr, [-15, 18.5, z - 0.5], [15, 19.5, z + 0.5], "wood", (), "rail"); rail_z.append(z)
    # little shake roof
    rf = g["roof_g"]
    rk = H.rect("roof_top", px(36), px(11), lambda W, Hh: H.P.shingle(R["tile_moss"], W, Hh, 0.6, style="shake", moss=True))
    ru = H.rect("roof_under", px(36), px(11), lambda W, Hh: H.P.boards(R["walnut"], W, Hh, -1.2, orient="v", bw=3, lap=False, nails=False, shadow_top=False))
    H.slab("roof_front", rf, -18, 18, yR + 1.5, 0, 11, 35, 1.0, rk, ru, "wood", toward=-1)
    H.slab("roof_back", rf, -18, 18, yR + 1.5, 0.5, 11, 35, 1.5, rk, ru, "wood", toward=+1)
    H.box("roof_ridge_cap", rf, [-18.5, yR + 1, -1.5], [18.5, yR + 2.5, 2], "wood", (), "rcap")
    # bundles hanging upside down from the rails: twine, tie, stems, the leafy / flowered head in the plant's colour
    b = g["bundles"]
    for i, (pid, rm, glow) in enumerate(PLANTS):
        z = rail_z[i // 5]; x = -12 + (i % 5) * 6 + (1 if i // 5 else 0)
        drop = [1.5, 2.5, 1.5, 3, 2][i % 5]
        bg = H.group(f"bundle_{pid}", [x, 18.5, z], b)
        H.box(f"bundle_{pid}_twine", bg, [x - 0.25, 18.5 - drop, z - 0.25], [x + 0.25, 18.5, z + 0.25], "rope", (), "twine")
        y = 18.5 - drop
        H.item(f"bundle_{pid}_stems", bg, [x - 0.75, y - 2.5, z - 0.75], [x + 0.75, y, z + 0.75], "stems",
               lambda W, Hh, c: H.P.leafy(R["sage"], W, Hh, c))
        H.item(f"bundle_{pid}_tie", bg, [x - 1, y - 1.5, z - 1], [x + 1, y - 0.5, z + 1], "btie", lambda W, Hh, c: H.P.rope(W, Hh, c))
        name = f"bundle_{pid}_head" + ("_glow" if glow else "")
        H.item(name, bg, [x - 1.5, y - 6, z - 1.5], [x + 1.5, y - 2.5, z + 1.5], f"bhead_{pid}",
               lambda W, Hh, c, r_=rm: H.P.leafy(R["nettle"], W, Hh, c, R[r_]) if r_ != "nettle" else H.P.leafy(R["nettle"], W, Hh, c))
        H.item(f"bundle_{pid}_tips", bg, [x - 1, y - 7, z - 1], [x + 1, y - 6, z + 1], f"btip_{pid}",
               lambda W, Hh, c, r_=rm: H.P.leafy(R[r_], W, Hh, c), hide=())
    # drying tray on trestles in front with petals laid out
    t = g["tray"]
    for i, x in enumerate((-8, 8)):
        H.rotbar(f"trestle_{i + 1}_a", t, [x - 2.5, 0, -12], [x, 7, -12], 1.0, "wood")
        H.rotbar(f"trestle_{i + 1}_b", t, [x + 2.5, 0, -12], [x, 7, -12], 1.0, "wood")
    H.box("tray_frame", t, [-11, 7, -15], [11, 8, -9], "wood", (), "tframe")
    pk = H.rect("petal_bed", px(20), px(5), lambda W, Hh: H.P.pile(R["orange"], W, Hh, "up", r=1.0, stem=False, gap=R["sage"]))
    pk2 = H.rect("petal_bed_2", px(9), px(5), lambda W, Hh: H.P.pile(R["bluebell"], W, Hh, "up", r=1.0, stem=False, gap=R["sage"]))
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["up"] = F(pk, sub=(0, 0, 22, 10))
    H.m.cube("tray_petals_marigold", t, [-10, 8.05, -14.5], [1, 8.05, -9.5], fs)
    fs2 = dict(fs); fs2["up"] = F(pk2)
    H.m.cube("tray_petals_bluebell", t, [1.5, 8.05, -14.5], [10.5, 8.05, -9.5], fs2)
    # details: basket of fresh plants, twine spool, sickle, a sack of bundles
    d = g["details"]
    basket(H, "basket_fresh", d, 18, -6, 6, 5, 3, "nettle", 1.0, handle=True)
    for i, (x, z, rm) in enumerate(((17, -6.5, "sunpetal"), (19, -5.5, "apple"))):
        H.item(f"fresh_flower_{i + 1}", d, [x - 0.75, 3.5, z - 0.75], [x + 0.75, 5, z + 0.75], f"ff{i}", lambda W, Hh, c, r_=rm: H.P.leafy(R[r_], W, Hh, c))
    H.item("twine_spool", d, [16, 0, 4], [18.5, 2.5, 6.5], "spool", lambda W, Hh, c: H.P.rope(W, Hh, c))
    sg = H.group("sack_bundles", [-19, 0, 4], d)
    H.item("sack_body", sg, [-21, 0, 2], [-17, 5, 6], "sack", lambda W, Hh, c: H.P.sack(R["burlap"], W, Hh, c))
    for i, (x, rm) in enumerate(((-20, "frostbloom"), (-18.5, "grape"))):
        H.item(f"sack_bundle_{i + 1}", sg, [x - 0.75, 5, 3.25], [x + 0.75, 7.5, 4.75], f"sb{i}", lambda W, Hh, c, r_=rm: H.P.leafy(R[r_], W, Hh, c))
    H.box("sickle_handle", d, [-19, 0, -6], [-14, 1, -5], "wood", ("down",), "skh")
    H.box("sickle_blade", d, [-21, 0, -8], [-19, 0.5, -4], "steel", ("down",), "skb") if "steel" in H.mats else \
        H.box("sickle_blade", d, [-21, 0, -8], [-19, 0.5, -4], "iron", ("down",), "skb")
    return H


# ==================================================================== 6. tanning rack
def tanning_rack():
    H = Station("tanning_rack", 4606, station_mats(extra={
        "wood": M("boards", "oak", (64, 24), (64, 24), bw=2, shadow_top=False),
        "pole": M("boards", "walnut", (16, 64), (16, 16), bw=2, orient="v", lap=False, shadow_top=False),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
        "rope": flat_mat("rope", (32, 8)),
    }))
    g = {k: H.group(k, [0, 0, 0]) for k in ("frame", "hide_g", "vat", "line", "details")}
    fr = g["frame"]
    for s, x in (("left", -12), ("right", 12)):
        H.box(f"post_{s}", fr, [x - 1, 0, -1], [x + 1, 25, 1], "pole", ("down",), "post")
        H.box(f"post_{s}_cap", fr, [x - 1.5, 25, -1.5], [x + 1.5, 26, 1.5], "wood", (), "pcap")
        for k, z in enumerate((-4, 4)):
            H.rotbar(f"brace_{s}_{k + 1}", fr, [x, 0, z], [x, 9, 0], 1.0, "wood")
        H.box(f"foot_{s}", fr, [x - 1, 0, -5], [x + 1, 1, 5], "wood", ("down",), "foot")
    for e, y in (("top", 22), ("bottom", 3)):
        H.box(f"bar_{e}", fr, [-13, y, -0.75], [13, y + 1.5, 0.75], "wood", (), "bar")
    # stretched hide in the frame (alpha outline), with laces to the frame
    hg = g["hide_g"]
    hk = H.rect("hide_stretched", px(18), px(16), lambda W, Hh: H.P.hide(R["hide"], W, Hh, "lit"))
    H.card("hide_stretched", hg, [-9, 5, 0], [9, 21, 0], hk)
    for i, (p0, p1) in enumerate((([-5, 20, 0], [-5, 22, 0]), ([0, 20.5, 0], [0, 22, 0]), ([5, 20, 0], [5, 22, 0]),
                                  ([-5, 6, 0], [-5, 4.5, 0]), ([0, 5.5, 0], [0, 4.5, 0]), ([5, 6, 0], [5, 4.5, 0]),
                                  ([-8.5, 9, 0], [-11, 10, 0]), ([-8, 17, 0], [-11, 18, 0]), ([8.5, 9, 0], [11, 10, 0]),
                                  ([8, 17, 0], [11, 18, 0]), ([-7.5, 13, 0], [-11, 13.5, 0]), ([7.5, 13, 0], [11, 13.5, 0]))):
        H.rotbar(f"lace_{i + 1}", hg, p0, p1, 0.5, "rope")
    # fleshing beam leaning, scraper resting on it
    H.rotbar("fleshing_beam", hg, [16, 0, -6], [13, 10, -2], 2.0, "wood")
    sg = H.group("scraper", [14, 9, -4], hg)
    H.box("scraper_blade", sg, [12, 8.5, -6], [16, 9, -5.5], "steel", (), "sblade", rot=(0, 30, 0), origin=[14, 8.75, -5.75])
    for s, x in (("left", 11.5), ("right", 16)):
        H.box(f"scraper_grip_{s}", sg, [x - 0.5, 8.5, -6.5], [x + 0.5, 9, -4.5], "wood", (), "sgrip", rot=(0, 30, 0), origin=[14, 8.75, -5.75])
    # tanning vat: a wide tub of bark liquor with a paddle
    v = g["vat"]
    H.item("vat_tub", v, [-24, 0, -6], [-16, 7, 2], "vat", lambda W, Hh, c: H.P.barrel(R["oak"], W, Hh, c), hide=("down", "up"))
    H.item("vat_liquor", v, [-23.5, 6, -5.5], [-16.5, 6, 1.5], "liquor", lambda W, Hh, c: H.P.liquid(R["tan_liquor"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    H.item("vat_hide_soaking", v, [-22.5, 5.5, -4], [-18, 6.5, 0], "soak", lambda W, Hh, c: H.P.hide(R["leather"], W, Hh, c, shape=False))
    H.rotbar("vat_paddle", v, [-20, 3, -2], [-15, 13, 1], 1.0, "wood")
    H.box("vat_paddle_blade", v, [-21, 2, -3], [-19, 6, -2.5], "wood", (), "pblade")
    # drying line with draped hides between the post and a pole
    ln = g["line"]
    H.box("line_pole", ln, [21, 0, 5], [23, 22, 7], "pole", ("down",), "lpole")
    H.rotbar("drying_line", ln, [12, 21, 0.5], [22, 21, 6], 0.5, "rope")
    for i, (x, z, rm) in enumerate(((15, 2.2, "hide"), (19, 4.4, "leather"))):
        ang = math.degrees(math.atan2(10, 5.5))
        hk2 = H.rect(f"draped_{rm}", 8, 18, lambda W, Hh, r_=rm: H.P.hide(R[r_], W, Hh, "lit", shape=False))
        H.card(f"draped_hide_{i + 1}", ln, [x - 2, 12, z], [x + 2, 21, z], hk2, rot=(0, -ang + 90, 0), origin=[x, 21, z])
    # details: stack of finished leather on a crate, stool, a bucket
    d = g["details"]
    H.item("leather_crate", d, [-23, 0, 6], [-17, 5, 12], "crate_pine_wood", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c))
    for i, rm in enumerate(("leather", "hide", "leather", "hide")):
        H.item(f"leather_sheet_{i + 1}", d, [-22.5 + (i % 2) * 0.5, 5 + i * 0.5, 6.5], [-17.5 + (i % 2) * 0.5, 5.5 + i * 0.5, 11.5], f"lsheet_{rm}",
               lambda W, Hh, c, r_=rm: H.P.form(R[r_], W, Hh, c, 3.6))
    H.box("stool_seat", d, [5, 6, -10], [10, 7, -6], "wood", (), "seat")
    for i, (x, z) in enumerate(((5.5, -9.5), (9.5, -9.5), (7.5, -6.5))):
        H.box(f"stool_leg_{i + 1}", d, [x - 0.5, 0, z - 0.5], [x + 0.5, 6, z + 0.5], "wood", ("down",), "sleg")
    barrel(H, "bucket", d, -8, -8, 4, 4, wood="oak")
    H.item("bucket_water", d, [-9.5, 3.5, -9.5], [-6.5, 3.5, -6.5], "water", lambda W, Hh, c: H.P.liquid(R["water"], W, Hh, c),
           hide=("down", "north", "south", "east", "west"))
    return H


# ==================================================================== 7. brewing cauldron
def cauldron():
    H = Station("cauldron", 4707, station_mats(extra={
        "wood": M("boards", "oak", (64, 24), (64, 24), bw=2, shadow_top=False),
        "pole": M("boards", "walnut", (16, 64), (16, 16), bw=2, orient="v", lap=False, shadow_top=False),
        "cauldron": M("metal", "iron", (48, 16), (32, 32)),
        "steel": M("metal", "steel", (24, 16), (16, 16)),
        "cobble": {"kind": "cobble", "ramp": R["cobble"], "side": (16, 8), "top": (16, 16), "no_lit2": True},
    }))
    g = {k: H.group(k, [0, 0, 0]) for k in ("fire", "tripod", "pot", "ladle", "table", "details")}
    f = g["fire"]
    for k in range(8):
        a = math.radians(k * 45 + 10); x, z = math.cos(a) * 9, math.sin(a) * 9
        s = 3 if k % 2 else 2.5
        H.box(f"ring_stone_{k + 1}", f, [x - s / 2, 0, z - s / 2], [x + s / 2, 2 if k % 2 else 2.5, z + s / 2], "cobble", ("down",), f"rs{k % 2}",
              rot=(0, k * 45, 0), origin=[x, 0, z])
    H.item("ember_bed_glow", f, [-6, 0, -6], [6, 0.5, 6], "embers", lambda W, Hh, c: H.P.coal(W, Hh, c, embers=0.4))
    for i, (p0, p1) in enumerate((([-6, 0.5, -3], [6, 2, 3]), ([-5, 0.5, 4], [5, 2, -4]), ([2, 2, -6], [-2, 2.5, 6]))):
        p0 = np.array(p0, float); p1 = np.array(p1, float); d = p1 - p0; L = h2(float(np.linalg.norm(d)))
        mid = (p0 + p1) / 2; yaw = math.degrees(math.atan2(d[0], d[2]))
        H.log(f"firewood_{i + 1}", f, [mid[0] - 1, mid[1] - 1, mid[2] - L / 2], [mid[0] + 1, mid[1] + 1, mid[2] + L / 2], axis="z")
        H.m.elements[-1]["rotation"] = [0, round(yaw, 3), 0]; H.m.elements[-1]["origin"] = [round(v, 4) for v in mid]
    for i, (x, z, w_, hh) in enumerate(((-2, -1, 3, 6), (2, 1, 3, 5), (0, -3, 2.5, 4), (-1, 3, 2.5, 4.5))):
        H.flame_cards(f"flame_{i + 1}", f, x, 1, z, w_, hh)
    # tripod of poles with a chain down to the pot's bail
    tp = g["tripod"]
    top = np.array([0, 36, 0.0])
    for k in range(3):
        a = math.radians(90 + k * 120); foot = np.array([math.cos(a) * 14, 0, math.sin(a) * 14])
        H.rotbar(f"tripod_pole_{k + 1}", tp, foot, top + (top - foot) * 0.08, 1.5, "pole")
    H.box("tripod_lashing", tp, [-1.5, 34.5, -1.5], [1.5, 37, 1.5], "rope" if "rope" in H.mats else "wood", (), "lash")
    H.box("chain", tp, [-0.25, 21, -0.25], [0.25, 34.5, 0.25], "steel", ("up", "down"), "chain")
    H.box("chain_hook", tp, [-0.75, 20, -0.75], [0.75, 21, 0.75], "steel", (), "hook")
    # the pot: octagonal iron belly, rim, glowing brew, bubbles, a bail handle, little legs. Every octagon is cut into
    # edge-to-edge boxes (octo_solid), the rim is a ring open in the middle, and the brew sits 0.5 below the rim top,
    # so no two faces share a plane anywhere (the old rim was a solid lid level with the brew).
    p = g["pot"]
    body, belly, base = octo_cells(12), octo_cells(13), octo_cells(9)
    rim = octo_cells(13) - octo_cells(10, inset=4)                # 1.5 wide ring round the opening
    octo_solid(H, "pot_body", p, body, 5, 13, "cauldron", "pbody", hide=("down", "up"))   # top: under the brew and rim
    octo_solid(H, "pot_belly", p, belly, 6.5, 11.5, "cauldron", "pbelly")
    octo_solid(H, "pot_base", p, base, 4, 5, "cauldron", "pbase", hide=("up",))           # top: under the body
    octo_solid(H, "pot_rim", p, rim, 13, 14, "cauldron", "prim", hide=("down",))
    H.item("brew_glow", p, [-5, 13, -5], [5, 13.5, 5], "brew", lambda W, Hh, c: H.P.pile(R["glow_green"], W, Hh, c, r=1.5, stem=False, gap=R["glow_green"]),
           hide=("down", "north", "south", "east", "west"))
    for i, (x, z, s_, y) in enumerate(((-2, 1, 1.5, 13.5), (2, -1.5, 1, 14), (0.5, 2.5, 1, 15), (-1, -2, 0.5, 16))):
        H.item(f"bubble_{i + 1}_glow", p, [x - s_ / 2, y, z - s_ / 2], [x + s_ / 2, y + s_, z + s_ / 2], f"bub{s_}",
               lambda W, Hh, c: H.P.form(R["glow_green"], W, Hh, c, 4.6, noise=0), hide=("down",) if y <= 13.5 else ())
    for i, (x, z) in enumerate(((-3.5, -3.5), (3.5, -3.5), (0, 4))):
        H.box(f"pot_leg_{i + 1}", p, [x - 0.75, 2, z - 0.75], [x + 0.75, 4, z + 0.75], "cauldron", ("down", "up"), "pleg")
    for s_, x, inner in (("left", -7, "east"), ("right", 6.5, "west")):
        H.box(f"bail_lug_{s_}", p, [x, 12, -0.75], [x + 0.5, 14, 0.75], "steel", (inner,), "lug")
    H.rotbar("bail_left", p, [-6.75, 14, 0], [0, 20.5, 0], 0.5, "steel")
    H.rotbar("bail_right", p, [6.75, 14, 0], [0, 20.5, 0], 0.5, "steel")
    # ladle resting in the brew (pivot at the rim)
    lg = H.group("brew_ladle", [4, 14, -3], g["ladle"])
    H.rotbar("ladle_handle", lg, [2, 12, -2], [8, 22, -5], 0.5, "wood")
    H.item("ladle_cup", lg, [1, 11.5, -2.5], [3, 13, -0.5], "lcup", lambda W, Hh, c: H.P.metal(R["copper"], W, Hh, 3.2))
    # side table with ingredients and bottles
    t = g["table"]
    for i, (x, z) in enumerate(((15, -5), (23, -5), (15, 3), (23, 3))):
        H.box(f"table_leg_{i + 1}", t, [x - 0.75, 0, z - 0.75], [x + 0.75, 9, z + 0.75], "wood", ("down", "up"), "tleg")
    H.box("table_top", t, [14, 9, -6], [24, 10, 4], "top", (), "ttop")
    for i, (x, z, gl) in enumerate(((16, -4, "glow_pink"), (18.5, -4.5, "glow_cyan"), (16.5, -1.5, "glow_violet"))):
        bg = H.group(f"bottle_{i + 1}", [x, 10, z], t)
        H.item(f"bottle_{i + 1}_body_glow", bg, [x - 1, 10, z - 1], [x + 1, 12, z + 1], f"gl_{gl}", lambda W, Hh, c, r_=gl: H.P.glass(R[r_], W, Hh, c))
        H.item(f"bottle_{i + 1}_neck", bg, [x - 0.5, 12, z - 0.5], [x + 0.5, 13, z + 0.5], "neck", lambda W, Hh, c: H.P.form(R["glass"], W, Hh, c, 4.2))
        H.item(f"bottle_{i + 1}_cork", bg, [x - 0.5, 13, z - 0.5], [x + 0.5, 13.5, z + 0.5], "cork", lambda W, Hh, c: H.P.form(R["cork"], W, Hh, c, 3.6))
    H.item("mortar", t, [20, 10, -5], [22.5, 11.5, -2.5], "mortar", lambda W, Hh, c: H.P.form(R["stone"], W, Hh, c, 3.6))
    H.item("pestle", t, [21, 11, -4.25], [22, 14, -3.25], "pestle", lambda W, Hh, c: H.P.form(R["stone"], W, Hh, c, 4.0),
           rot=(0, 0, -22.5), origin=[21.5, 11, -3.75])
    for i, (x, rm) in enumerate(((17, "nettle"), (19.5, "sunpetal"), (22, "frostbloom"))):
        H.item(f"table_bundle_{i + 1}", t, [x - 1, 10, 0.5], [x + 1, 11.5, 3.5], f"tb_{rm}", lambda W, Hh, c, r_=rm: H.P.leafy(R[r_], W, Hh, c))
    bk = H.rect("recipe_pages", px(5), px(3.5), lambda W, Hh: H.P.pages(W, Hh, "up"))
    H.box("recipe_cover", t, [15, 10, -0.5], [21, 10.5, -0.5 + 0.5], "top", (), "rcov") if False else None
    fs = {k: None for k in ("north", "east", "south", "west", "up", "down")}; fs["up"] = F(bk)
    H.box("recipe_book_cover", t, [18.5, 10, -2.5], [24, 10.5, 1], "top", (), "rbc") if False else None
    # details: crate of bundles, firewood stack, a stool
    d = g["details"]
    H.item("bundle_crate", d, [-23, 0, -4], [-17, 5, 2], "crate_pine_wood", lambda W, Hh, c: H.P.crate(R["pine_wood"], W, Hh, c))
    for i, (x, z, rm) in enumerate(((-21.5, -2.5, "bluebell"), (-19, -2, "apple"), (-21, 0.5, "orange"), (-18.5, 0.5, "glow_violet"))):
        H.item(f"crate_bundle_{i + 1}", d, [x - 1, 4, z - 1], [x + 1, 7, z + 1], f"cb_{rm}", lambda W, Hh, c, r_=rm: H.P.leafy(R[r_], W, Hh, c))
    for i, (y, z0) in enumerate(((0, 5), (0, 8.5), (3, 6.75))):
        H.log(f"wood_stack_{i + 1}", d, [-24, y, z0 - 1.5], [-16, y + 3, z0 + 1.5], axis="x", hide=("down",))   # the top log rests on the two below
    return H


BUILDERS = {f.__name__: f for f in (furnace, anvil, workbench, sawbench, drying_rack, tanning_rack, cauldron)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        BUILDERS[n]().finish([OUT])
