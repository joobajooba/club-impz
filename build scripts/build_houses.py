"""Fantasy houses for the hub, world decoration (J00BA, 2026-11-08): "similar to the castle in the hub, different
variations, fantasy style with decorative roofs and coloured bricks, then houses made of fancy wood, very detailed
textures". Built with house_lib.py the castle's way (swatches + crops, stepped roofs). Section 3.11 + 1.7: buildings
100 to 500 cubes, 512 texture, 2 px per unit. Door 16 x 28, imp 18 tall (section 1.3). Front = north (-z).

  brick_rose_cottage    red brick, crow-stepped gables, teal fish-scale roof, gold crest, dormers, flower boxes
  brick_bluebell_house  blue painted brick with glazed accents, purple scale roof, a corner turret with a witch-hat cone
  brick_honey_townhouse tall honey brick with plum glazed bricks, red clay tiles, iron balcony, round gable window
  wood_oak_lodge        log lodge, crossed log corners, mossy shake roof over a porch with carved posts, stone chimney
  wood_cherry_manor     cherry clapboard, jettied upper floor, white gingerbread trim, front bay with a balcony
  wood_timber_house     stone ground floor, half-timbered upper floor, slate roof, an oriel turret
Usage: py build_houses.py [name ...]   (default: all)"""
import os, sys, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from house_lib import House, R, F, px, OPP

OUT = r"C:\Users\lucas\blockbench_models\buildings\houses"


def mats(wall, roof, roof_style, wall_kind="brick", wall_extra=None, roof_extra=None, trim="stone", trim_kind="ashlar",
         wood="oak", extra=None):
    d = {
        "wall": {"kind": wall_kind, "ramp": R[wall], "side": (112, 72), "top": (32, 32), "extra": wall_extra or {}},
        "roof": {"kind": "shingle", "ramp": R[roof], "side": (112, 48), "top": (64, 64), "under": (64, 64), "no_lit2": True,
                 "extra": dict(style=roof_style, **(roof_extra or {}))},
        "trim": {"kind": trim_kind, "ramp": R[trim], "side": (96, 48), "top": (48, 48), "no_lit2": True,
                 "extra": {} if trim_kind != "carved" else {"motif": "diamond"}},
        "plinth": {"kind": "cobble", "ramp": R["cobble"], "side": (96, 16), "top": (48, 48), "no_lit2": True},
        "wood": {"kind": "boards", "ramp": R[wood], "side": (64, 48), "top": (64, 48), "no_lit2": True,
                 "extra": {"bw": 3, "shadow_top": False}},
        "iron": {"kind": "metal", "ramp": R["iron"], "side": (24, 16), "top": (16, 16), "no_lit2": True},
        "gold": {"kind": "metal", "ramp": R["gold"], "side": (24, 16), "top": (16, 16), "no_lit2": True},
        "pot": {"kind": "flat", "ramp": R["clay_pot"], "side": (8, 8), "top": (8, 8), "no_lit2": True},
    }
    d.update(extra or {})
    return d


def dormer(H, name, grp, side, plane_in, plane_out, u, y0, w, h, wall, roof, frame_ramp, shutters=None):
    """A dormer on an east/west roof slope: a wall box from inside the roof out to the eave line, a window on its face
    and a little gable roof whose ridge runs across the main ridge."""
    g = H.group(name, [plane_out, y0, u], grp)
    a, b = sorted((plane_in, plane_out))
    H.box(f"{name}_body", g, [a, y0, u - w / 2], [b, y0 + h, u + w / 2], wall, ("down", "up"), f"{name}b")
    H.window(f"{name}_window", g, side, plane_out, u, y0 + 2.5, w - 5, h - 5, style="leaded", arch=True,
             frame_ramp=frame_ramp, sill="trim", lintel=None, shutters=shutters)
    prof = [(0, 1.5), (1.5, 2), (1.5, 2), (1.5, 2), (1, 2), (1, 1.5)]
    H.roof(f"{name}_roof", g, a, b + (1 if side == "east" else 0), u - w / 2, u + w / 2, y0 + h, prof, roof, wall,
           axis="x", eave=1.5, caps=("trim", 0.5))


def storey_walls(H, prefix, grp, x1, x2, z1, z2, y1, y2, mat="wall"):
    H.box(f"{prefix}_walls", grp, [x1, y1, z1], [x2, y2, z2], mat, ("down", "up"), f"{prefix}w",
          place="ground" if y1 <= 4 else "top")


def plinth(H, grp, x1, x2, z1, z2, h=3):
    H.box("plinth", grp, [x1 - 1, 0, z1 - 1], [x2 + 1, h, z2 + 1], "plinth", ("down",), "plinth", place="ground")


def band(H, name, grp, x1, x2, z1, z2, y, h=1.5, out=1, mat="trim"):
    H.box(name, grp, [x1 - out, y, z1 - out], [x2 + out, y + h, z2 + out], mat, ("down",), name)


# ==================================================================== 1. rose cottage (red brick)
def brick_rose_cottage():
    H = House("brick_rose_cottage", 1101, mats("brick_red", "tile_teal", "scale",
              wall_extra={"accent": R["brick_plum"]}, roof_extra={"accent": R["tile_purple"]}, wood="walnut"))
    root = H.root
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "openings", "roofs", "details")}
    X1, X2, Z1, Z2 = -26, 26, -20, 20
    plinth(H, g["walls"], X1, X2, Z1, Z2)
    storey_walls(H, "ground", g["walls"], X1, X2, Z1, Z2, 3, 36)
    band(H, "floor_band", g["walls"], X1, X2, Z1, Z2, 36)
    storey_walls(H, "upper", g["walls"], X1, X2, Z1, Z2, 37.5, 66)
    band(H, "eave_band", g["walls"], X1, X2, Z1, Z2, 64.5, 1.5, 1)
    H.quoins("quoin", g["walls"], X1, X2, Z1, Z2, 3, 36)
    H.quoins("quoin_up", g["walls"], X1, X2, Z1, Z2, 37.5, 63)
    # front: arched door with a canopy, two windows below, three above
    H.door("front_door", g["openings"], "north", Z1, 0, 3, 14, 26, wood="walnut", arch=True, canopy=("roof", "wood"))
    for i, u in enumerate((-16, 16)):
        H.window(f"front_window_{i + 1}", g["openings"], "north", Z1, u, 12, 8, 14, arch=True, shutters="paint_teal",
                 flowerbox="wood", frame_ramp=R["paint_cream"])
    for i, u in enumerate((-16, 0, 16)):
        H.window(f"upper_window_{i + 1}", g["openings"], "north", Z1, u, 44, 8, 12, arch=False, shutters="paint_teal",
                 flowerbox="wood" if u else None, frame_ramp=R["paint_cream"])
    for side, plane in (("east", X2), ("west", X1)):
        for i, u in enumerate((-8, 8)):
            H.window(f"{side}_window_{i + 1}", g["openings"], side, plane, u, 13, 8, 12, arch=True, shutters="paint_teal",
                     frame_ramp=R["paint_cream"])
            H.window(f"{side}_upper_window_{i + 1}", g["openings"], side, plane, u, 44, 8, 12, frame_ramp=R["paint_cream"])
    for i, u in enumerate((-14, 14)):
        H.window(f"back_window_{i + 1}", g["openings"], "south", Z2, u, 13, 8, 12, arch=True, frame_ramp=R["paint_cream"])
    H.door("back_door", g["openings"], "south", Z2, 0, 3, 12, 24, wood="walnut", arch=False, canopy=None)
    # steep crow-stepped roof, ridge front to back
    prof = [(0, 3)] + [(3, 4)] * 6 + [(2.5, 4)] * 2 + [(2, 4)]
    top = H.roof("roof", g["roofs"], X1, X2, Z1, Z2, 66, prof, "roof", "wall", axis="z", eave=3,
                 caps=("trim", 1), ridge=("gold", 2, 1.5), crest=("gold", 4), finials=("gold", 6))
    # round gable windows front and back
    rk = H.rect("round_window_10", px(10), px(10), lambda W, Hh: H.P.round_window(R["stone"], W, Hh))
    for side, plane in (("north", Z1), ("south", Z2)):
        f2, t2 = H.plane_box(side, plane, -5, 5, 76, 86, 1)
        fs = H.faces(f2, t2, "trim", (OPP[side], side), "roundw"); fs[side] = F(rk)
        H.m.cube(f"gable_round_window_{side}", g["openings"], f2, t2, fs)
    for side, xin, xout in (("east", 10, 24), ("west", -10, -24)):
        dormer(H, f"dormer_{side}", g["roofs"], side, xin, xout, 0, 76, 10, 13, "wall", "roof", R["paint_cream"], None)
    H.chimney("chimney", g["roofs"], 13, 12, 6, 6, 60, top - 6, "wall")
    H.lantern("lantern", g["details"], "north", Z1, -9, 24)
    return H


# ==================================================================== 2. bluebell house (blue brick + turret)
def brick_bluebell_house():
    H = House("brick_bluebell_house", 2202, mats("brick_blue", "tile_purple", "scale",
              wall_extra={"accent": R["tile_teal"]}, wood="cherry"))
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "openings", "roofs", "turret", "details")}
    X1, X2, Z1, Z2 = -22, 26, -18, 18
    plinth(H, g["walls"], X1, X2, Z1, Z2)
    storey_walls(H, "ground", g["walls"], X1, X2, Z1, Z2, 3, 34)
    band(H, "floor_band", g["walls"], X1, X2, Z1, Z2, 34)
    storey_walls(H, "upper", g["walls"], X1, X2, Z1, Z2, 35.5, 62)
    band(H, "eave_band", g["walls"], X1, X2, Z1, Z2, 60.5)
    H.quoins("quoin", g["walls"], X1, X2, Z1, Z2, 3, 33)
    H.quoins("quoin_up", g["walls"], X1, X2, Z1, Z2, 35.5, 59.5)
    H.door("front_door", g["openings"], "north", Z1, 10, 3, 14, 26, wood="cherry", arch=True, canopy=("roof", "wood"))
    H.window("front_window_1", g["openings"], "north", Z1, -6, 12, 10, 14, arch=True, frame_ramp=R["paint_white"],
             flowerbox="wood", shutters="paint_white")
    for i, u in enumerate((-6, 10)):
        H.window(f"upper_window_{i + 1}", g["openings"], "north", Z1, u, 42, 9, 13, arch=True, frame_ramp=R["paint_white"],
                 flowerbox="wood")
    for side, plane in (("east", X2), ("west", X1)):
        H.window(f"{side}_window", g["openings"], side, plane, 4, 12, 9, 13, arch=True, frame_ramp=R["paint_white"])
        H.window(f"{side}_upper_window", g["openings"], side, plane, 4, 42, 9, 13, arch=True, frame_ramp=R["paint_white"])
    for i, u in enumerate((-8, 12)):
        H.window(f"back_window_{i + 1}", g["openings"], "south", Z2, u, 12, 9, 13, frame_ramp=R["paint_white"])
        H.window(f"back_upper_window_{i + 1}", g["openings"], "south", Z2, u, 42, 9, 13, frame_ramp=R["paint_white"])
    # roof: ridge east-west (eaves face the street), gable ends east and west
    prof = [(0, 3)] + [(3, 4)] * 4 + [(2.5, 4)] * 2 + [(2, 3.5)] * 2
    top = H.roof("roof", g["roofs"], X1, X2, Z1, Z2, 62, prof, "roof", "wall", axis="x", eave=3,
                 caps=("trim", 1), ridge=("gold", 2, 1.5), crest=("gold", 4), finials=("gold", 6))
    H.chimney("chimney", g["roofs"], 18, 8, 6, 6, 56, top - 4, "wall")
    # front dormer on the north slope
    gd = H.group("dormer_front", [10, 66, -18], g["roofs"])
    H.box("dormer_front_body", gd, [5, 66, -16], [15, 78, -4], "wall", ("down", "up"), "dfb")
    H.window("dormer_front_window", gd, "north", -16, 10, 68.5, 6, 8, arch=True, frame_ramp=R["paint_white"], lintel=None)
    H.roof("dormer_front_roof", gd, 5, 15, -17, -4, 78, [(0, 1.5), (1.5, 2), (1.5, 2), (1.5, 2), (1, 2), (1, 1.5)],
           "roof", "wall", axis="z", eave=1.5, caps=("trim", 0.5))
    # corner turret, front left
    T = g["turret"]; cx, cz, D = -24, -18, 18
    H.octo("turret_plinth", T, cx, cz, D + 2, 0, 3, "plinth", place="ground")
    H.octo("turret_body_1", T, cx, cz, D, 3, 34, "wall", ("down", "up"), "tb1", place="ground")
    H.octo("turret_band_1", T, cx, cz, D + 2, 34, 35.5, "trim", ("down",), "tbd1")
    H.octo("turret_body_2", T, cx, cz, D, 35.5, 70, "wall", ("down", "up"), "tb2", place="top")
    H.octo("turret_band_2", T, cx, cz, D + 2, 70, 72, "trim", ("down",), "tbd2")
    H.octo("turret_body_3", T, cx, cz, D - 1, 72, 80, "wall", ("down", "up"), "tb3", place="top")
    for i, (side, plane, u) in enumerate((("north", cz - D / 2, cx), ("west", cx - D / 2, cz))):
        H.window(f"turret_window_{i + 1}", T, side, plane, u, 14, 6, 12, arch=True, frame_ramp=R["paint_white"], sill="trim")
        H.window(f"turret_upper_window_{i + 1}", T, side, plane, u, 44, 6, 12, arch=True, frame_ramp=R["paint_white"])
        H.window(f"turret_top_window_{i + 1}", T, side, cx - (D - 1) / 2 if side == "west" else cz - (D - 1) / 2, u, 73.5,
                 4, 5, arch=True, frame_ramp=R["paint_white"], sill=None, lintel=None)
    H.cone("turret_cone", H.group("turret_roof", [cx, 80, cz], T), cx, cz, D + 6, 80, 132, "roof", n=9, finial="gold")
    # weather vane on the cone
    H.box("vane_arrow", T, [cx - 4, 138.5, cz - 0.25], [cx + 4, 139.5, cz + 0.25], "gold", (), "vane")
    H.box("vane_tail", T, [cx + 3, 138, cz - 0.25], [cx + 5, 140, cz + 0.25], "gold", (), "vanet")
    H.lantern("lantern", g["details"], "north", Z1, 0, 24)
    return H


# ==================================================================== 3. honey townhouse (honey brick, 3 storeys)
def brick_honey_townhouse():
    H = House("brick_honey_townhouse", 3303, mats("brick_honey", "tile_red", "clay",
              wall_extra={"accent": R["brick_plum"]}, wood="walnut"))
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "openings", "roofs", "balcony", "extension", "details")}
    X1, X2, Z1, Z2 = -18, 18, -20, 20
    plinth(H, g["walls"], X1, X2, Z1, Z2)
    ys = [(3, 34), (35.5, 62), (63.5, 88)]
    for i, (a, b) in enumerate(ys):
        storey_walls(H, f"storey_{i + 1}", g["walls"], X1, X2, Z1, Z2, a, b)
        if i < 2: band(H, f"band_{i + 1}", g["walls"], X1, X2, Z1, Z2, b)
        H.quoins(f"quoin_{i + 1}", g["walls"], X1, X2, Z1, Z2, a, b - 1)
    band(H, "eave_band", g["walls"], X1, X2, Z1, Z2, 86.5)
    H.door("front_door", g["openings"], "north", Z1, -6, 3, 14, 26, wood="walnut", arch=True, canopy=None)
    H.window("shop_window", g["openings"], "north", Z1, 10, 10, 10, 16, style="panes", frame_ramp=R["paint_teal"],
             flowerbox="wood")
    for i, u in enumerate((-8, 8)):
        H.window(f"second_window_{i + 1}", g["openings"], "north", Z1, u, 40, 8, 16, arch=True, frame_ramp=R["paint_teal"])
        H.window(f"third_window_{i + 1}", g["openings"], "north", Z1, u, 68, 8, 13, arch=True, frame_ramp=R["paint_teal"],
                 flowerbox="wood", shutters="paint_teal")
    for side, plane in (("east", X2), ("west", X1)):
        for j, y in enumerate((12, 41, 69)):
            for i, u in enumerate((-9, 9)):
                if side == "east" and j == 0: continue          # the extension covers it
                H.window(f"{side}_window_{j + 1}_{i + 1}", g["openings"], side, plane, u, y, 7, 12, frame_ramp=R["paint_teal"])
    for j, y in enumerate((12, 41, 69)):
        H.window(f"back_window_{j + 1}", g["openings"], "south", Z2, 0, y, 8, 13, frame_ramp=R["paint_teal"])
    # balcony on the second storey, iron rails
    B = g["balcony"]
    H.box("balcony_floor", B, [-14, 35.5, -26], [14, 37, -20], "trim", (), "bfloor")
    for i in range(3):
        H.box(f"balcony_corbel_{i + 1}", B, [-11 + i * 10.5, 31, -24], [-9 + i * 10.5, 35.5, -20], "trim", (), "bcorb")
    H.box("balcony_rail", B, [-14, 44, -26], [14, 45, -25.5], "iron", (), "brail")
    for s, x in (("left", -14), ("right", 13.5)):
        H.box(f"balcony_side_rail_{s}", B, [x, 44, -26], [x + 0.5, 45, -20], "iron", (), "bsr")
    for i in range(15):
        x = -13.5 + i * 2
        H.box(f"balcony_baluster_{i + 1}", B, [x - 0.25, 37, -25.75], [x + 0.25, 44, -25.25], "iron", ("down",), "bal")
    # roof: ridge front to back, crow-stepped gables with stone coping
    prof = [(0, 3)] + [(2.5, 4)] * 4 + [(2, 4)] * 3 + [(1.5, 3.5)] * 2
    top = H.roof("roof", g["roofs"], X1, X2, Z1, Z2, 88, prof, "roof", "wall", axis="z", eave=2.5,
                 caps=("trim", 1), ridge=("trim", 2, 1.5), finials=("gold", 5))
    rk = H.rect("round_window_9", px(9), px(9), lambda W, Hh: H.P.round_window(R["stone"], W, Hh))
    for side, plane in (("north", Z1), ("south", Z2)):
        f2, t2 = H.plane_box(side, plane, -4.5, 4.5, 96, 105, 1)
        fs = H.faces(f2, t2, "trim", (OPP[side], side), "roundw"); fs[side] = F(rk)
        H.m.cube(f"gable_round_window_{side}", g["openings"], f2, t2, fs)
    for i, z in enumerate((-12, 12)):
        H.chimney(f"chimney_{i + 1}", g["roofs"], -13 if i == 0 else 13, z, 5, 5, 84, top - 2, "wall")
    # one storey extension on the east side with a lean-to roof
    E = g["extension"]
    H.box("extension_plinth", E, [18, 0, -12], [31, 3, 15], "plinth", ("down",), "eplinth", place="ground")
    H.box("extension_walls", E, [18, 3, -11], [30, 28, 14], "wall", ("down", "up"), "ewalls", place="ground")
    H.window("extension_window", E, "east", 30, 1, 10, 8, 12, arch=True, frame_ramp=R["paint_teal"], flowerbox="wood")
    H.door("extension_door", E, "north", -11, 24, 3, 10, 22, wood="walnut", arch=False, steps="trim")
    H.roof("extension_roof", E, 6, 30, -11, 14, 28, [(0, 2)] + [(2.5, 2.5)] * 4, "roof", "wall", axis="z", eave=2,
           caps=("trim", 0.5))
    H.lantern("lantern", g["details"], "north", Z1, 3, 22)
    return H


# ==================================================================== wood helpers
def log_corners(H, grp, x1, x2, z1, z2, y1, y2, step=3.5):
    """Crossed log ends sticking out at the corners (each course alternates direction), with cut ring ends."""
    ek = H.rect("log_end", px(3), px(3), lambda W, Hh: H.P.log_end(W, Hh))
    k, y = 0, y1
    while y + 3 <= y2:
        for ci, (cx, cz) in enumerate(((x1, z1), (x2, z1), (x1, z2), (x2, z2))):
            sx, sz = (1 if cx > 0 else -1), (1 if cz > 0 else -1)
            if k % 2 == 0:   # runs along x, end faces east / west
                a, b = sorted((cx - sx * 3, cx + sx * 4)); c, d = cz - 1.5, cz + 1.5
                over = {"east": F(ek), "west": F(ek)}
            else:
                a, b = cx - 1.5, cx + 1.5; c, d = sorted((cz - sz * 3, cz + sz * 4))
                over = {"north": F(ek), "south": F(ek)}
            H.box(f"log_corner_{k + 1}_{ci + 1}", grp, [a, y, c], [b, y + 3, d], "wall", (), f"lc{k % 2}", over=over)
        y += 3.5; k += 1


def timber_frame(H, prefix, grp, x1, x2, z1, z2, y1, y2, beam="beam"):
    """Half timbering: rails top and bottom, posts, and X braces between the windows, 0.5 proud of the plaster."""
    for side, plane, u0, u1 in (("north", z1, x1, x2), ("south", z2, x1, x2), ("east", x2, z1, z2), ("west", x1, z1, z2)):
        for r, y in (("sill", y1), ("mid", (y1 + y2) / 2 - 0.75), ("head", y2 - 1.5)):
            f, t = H.plane_box(side, plane, u0 - 0.5, u1 + 0.5, y, y + 1.5, 1)
            H.box(f"{prefix}_{side}_rail_{r}", grp, f, t, beam, (OPP[side],), f"rail{r}")
        n = int((u1 - u0) // 12)
        posts = [u0 + (u1 - u0) * i / n for i in range(n + 1)]
        for i, u in enumerate(posts):
            f, t = H.plane_box(side, plane, u - 0.75, u + 0.75, y1 + 1.5, y2 - 1.5, 1)
            H.box(f"{prefix}_{side}_post_{i + 1}", grp, f, t, beam, (OPP[side],), "post")
        for i in range(n):
            if i % 2: continue                                   # braces every other bay (windows go in the others)
            a, b = posts[i], posts[i + 1]
            cu, cy = (a + b) / 2, (y1 + 1.5 + (y1 + y2) / 2 - 0.75) / 2
            L = round((math.hypot(b - a - 1.5, (y2 - y1) / 2 - 2.25) - 0.5) * 2) / 2
            ang = math.degrees(math.atan2((y2 - y1) / 2 - 2.25, b - a - 1.5))
            for s in (1, -1):
                f, t = H.plane_box(side, plane, cu - L / 2, cu + L / 2, cy - 0.5, cy + 0.5, 0.5)
                cen = [(f[k] + t[k]) / 2 for k in range(3)]
                rot = (0, 0, s * ang) if side in ("north", "south") else (s * ang, 0, 0)
                H.box(f"{prefix}_{side}_brace_{i + 1}_{'a' if s > 0 else 'b'}", grp, f, t, beam, (OPP[side],), "brace",
                      rot=rot, origin=cen)


# ==================================================================== 4. oak lodge (logs)
def wood_oak_lodge():
    H = House("wood_oak_lodge", 4404, mats("oak", "tile_moss", "shake", wall_kind="logs", roof_extra={"moss": True},
              trim="walnut", trim_kind="carved", wood="oak",
              extra={"gable": {"kind": "boards", "ramp": R["walnut"], "side": (144, 64), "top": (48, 48), "no_lit2": True,
                               "extra": {"orient": "v", "bw": 4, "lap": False}},
                     "deck": {"kind": "boards", "ramp": R["oak"], "side": (96, 24), "top": (120, 40), "no_lit2": True,
                              "extra": {"bw": 3, "shadow_top": False}},
                     "teal": {"kind": "carved", "ramp": R["paint_teal"], "side": (96, 16), "top": (24, 24), "no_lit2": True,
                              "extra": {"motif": "scallop"}},
                     "chimstone": {"kind": "cobble", "ramp": R["stone"], "side": (40, 112), "top": (24, 24), "no_lit2": True}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "openings", "roofs", "porch", "details")}
    X1, X2, Z1, Z2 = -26, 26, -18, 18
    plinth(H, g["walls"], X1, X2, Z1, Z2, 3)
    H.box("log_walls", g["walls"], [X1, 3, Z1], [X2, 40, Z2], "wall", ("down", "up"), "logwalls", place="any")
    log_corners(H, g["walls"], X1, X2, Z1, Z2, 3, 40)
    H.door("front_door", g["openings"], "north", Z1, 0, 3, 14, 26, wood="walnut", frame="trim", arch=False, steps=None)
    for i, u in enumerate((-15, 15)):
        H.window(f"front_window_{i + 1}", g["openings"], "north", Z1, u, 13, 9, 12, style="panes", frame_ramp=R["paint_teal"],
                 shutters="paint_teal", flowerbox="wood", lintel="trim", sill="trim")
    for side, plane in (("east", X2), ("west", X1)):
        H.window(f"{side}_window", g["openings"], side, plane, -6 if side == "east" else 6, 13, 9, 12, style="panes",
                 frame_ramp=R["paint_teal"], shutters="paint_teal", lintel="trim", sill="trim")
    for i, u in enumerate((-12, 12)):
        H.window(f"back_window_{i + 1}", g["openings"], "south", Z2, u, 13, 9, 12, style="panes", frame_ramp=R["paint_teal"],
                 lintel="trim", sill="trim")
    # porch: deck, steps, carved posts, rail
    P = g["porch"]
    H.box("porch_deck", P, [-24, 0, -30], [24, 3, -18], "deck", ("down",), "deck", place="ground")
    H.box("porch_step_1", P, [-6, 0, -33], [6, 1.5, -30], "deck", ("down",), "pstep0", place="ground")
    H.box("porch_step_2", P, [-5, 1.5, -31.5], [5, 3, -30], "deck", ("down",), "pstep1")
    for i, x in enumerate((-23, -8, 8, 23)):
        H.box(f"porch_post_{i + 1}", P, [x - 1, 3, -29.5], [x + 1, 40, -27.5], "trim", ("down",), "ppost")
        for s in (-1, 1):
            H.box(f"porch_bracket_{i + 1}_{'a' if s < 0 else 'b'}", P, [x + (1 if s > 0 else -4), 35, -29.5],
                  [x + (4 if s > 0 else -1), 37, -27.5], "trim", (), "pbr")
    for i, (a, b) in enumerate(((-22, -9), (9, 22))):
        H.box(f"porch_rail_{i + 1}", P, [a, 11, -29], [b, 12.5, -28], "trim", (), "prail")
        for j in range(6):
            x = a + 1 + j * (b - a - 2) / 5
            H.box(f"porch_baluster_{i + 1}_{j + 1}", P, [x - 0.5, 3, -28.75], [x + 0.5, 11, -28.25], "trim", ("down",), "pbal")
    H.box("porch_beam", P, [-25, 40, -30], [25, 42, -27], "trim", (), "pbeam")
    # roof: ridge east-west, deep eave over the porch, carved teal bargeboards on the gables
    prof = [(0, 2.5), (3, 3), (3, 3), (3, 3.5), (3, 3.5), (3, 4), (2.5, 4), (2.5, 4), (2, 4), (2, 4)]
    top = H.roof("roof", g["roofs"], X1, X2, -28, Z2, 40, prof, "roof", "gable", axis="x", eave=3,
                 caps=("teal", 1.5), ridge=("trim", 2.5, 1.5), finials=("trim", 5))
    # sun emblem on the front gables
    sk = H.rect("sun_disc", px(8), px(8), lambda W, Hh: H.P.round_window(R["gold"], W, Hh))
    for side, plane in (("east", X2), ("west", X1)):
        f2, t2 = H.plane_box(side, plane, -4 - 5, 4 - 5, 56, 64, 1)
        fs = H.faces(f2, t2, "gold", (OPP[side], side), "sun"); fs[side] = F(sk)
        H.m.cube(f"gable_sun_{side}", g["details"], f2, t2, fs)
    # stone chimney against the west gable
    C_ = H.group("chimney", [-30, 0, 8], g["roofs"])
    H.box("chimney_base", C_, [-32, 0, 3], [-26, 30, 13], "chimstone", ("down",), "chb", place="ground")
    H.box("chimney_shoulder", C_, [-31, 30, 4], [-26, 36, 12], "chimstone", ("down",), "chs")
    H.box("chimney_stack", C_, [-30.5, 36, 5.5], [-25.5, top + 4, 10.5], "chimstone", ("down",), "chst")
    H.box("chimney_cap", C_, [-31.5, top + 4, 4.5], [-24.5, top + 5.5, 11.5], "trim", ("down",), "chc")
    H.lantern("lantern", g["details"], "north", Z1, -9, 24)
    # firewood stack by the east wall
    for i in range(3):
        for j in range(3 - i):
            z = -12 + j * 3 + i * 1.5
            H.box(f"firewood_{i + 1}_{j + 1}", g["details"], [27, i * 3, z], [32, i * 3 + 3, z + 3], "wall", ("down",),
                  "fw", over={"east": F(H.rect("log_end", px(3), px(3), None)), "west": F("log_end")})
    return H


# ==================================================================== 5. cherry manor (clapboard + gingerbread)
def wood_cherry_manor():
    H = House("wood_cherry_manor", 5505, mats("cherry", "tile_slate", "scale", wall_kind="boards",
              wall_extra={"bw": 6, "lap": True},
              trim="paint_white", trim_kind="carved", wood="walnut",
              extra={"stone": {"kind": "ashlar", "ramp": R["stone"], "side": (128, 24), "top": (48, 48), "no_lit2": True},
                     "lace": {"kind": "carved", "ramp": R["paint_white"], "side": (96, 16), "top": (24, 24), "no_lit2": True,
                              "extra": {"motif": "scallop"}}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "openings", "roofs", "bay", "details")}
    X1, X2, Z1, Z2 = -28, 28, -18, 20
    plinth(H, g["walls"], X1, X2, Z1, Z2)
    storey_walls(H, "ground", g["walls"], X1, X2, Z1, Z2, 3, 34)
    # jettied upper floor: 2 units out on every side, joist ends underneath
    band(H, "floor_band", g["walls"], X1, X2, Z1, Z2, 34, 2, 2.5)
    storey_walls(H, "upper", g["walls"], X1 - 2, X2 + 2, Z1 - 2, Z2 + 2, 36, 62)
    for i in range(12):
        x = X1 + 2 + i * (X2 - X1 - 4) / 11
        H.box(f"joist_{i + 1}", g["walls"], [x - 0.75, 32, Z1 - 2], [x + 0.75, 34, Z1], "wood", (), "joist")
    for side, (a, b, c, d) in (("ne", (X2 + 1.5, X2 + 3, Z1 - 3, Z1 - 1.5)), ("nw", (X1 - 3, X1 - 1.5, Z1 - 3, Z1 - 1.5)),
                               ("se", (X2 + 1.5, X2 + 3, Z2 + 1.5, Z2 + 3)), ("sw", (X1 - 3, X1 - 1.5, Z2 + 1.5, Z2 + 3))):
        H.box(f"corner_board_{side}", g["walls"], [a, 36, c], [b, 62, d], "trim", ("down",), "cb")
    for side, (a, b, c, d) in (("ne", (X2 - 0.5, X2 + 1, Z1 - 1, Z1 + 0.5)), ("nw", (X1 - 1, X1 + 0.5, Z1 - 1, Z1 + 0.5)),
                               ("se", (X2 - 0.5, X2 + 1, Z2 - 0.5, Z2 + 1)), ("sw", (X1 - 1, X1 + 0.5, Z2 - 0.5, Z2 + 1))):
        H.box(f"corner_board_low_{side}", g["walls"], [a, 3, c], [b, 34, d], "trim", ("down",), "cbl")
    band(H, "eave_band", g["walls"], X1 - 2, X2 + 2, Z1 - 2, Z2 + 2, 60.5, 1.5, 0.75, "lace")
    H.door("front_door", g["openings"], "north", Z1, 18, 3, 14, 26, wood="walnut", frame="trim", arch=True,
           canopy=("roof", "trim"), steps="stone")
    for side, plane in (("east", X2), ("west", X1)):
        for i, u in enumerate((-8, 8)):
            H.window(f"{side}_window_{i + 1}", g["openings"], side, plane, u, 12, 8, 15, style="panes",
                     frame_ramp=R["paint_white"], lintel="trim", sill="trim")
            H.window(f"{side}_upper_window_{i + 1}", g["openings"], side, plane + (2 if side == "east" else -2), u, 41, 8, 14,
                     style="panes", frame_ramp=R["paint_white"], lintel="trim", sill="trim", flowerbox="wood")
    for i, u in enumerate((-16, 0, 16)):
        H.window(f"back_window_{i + 1}", g["openings"], "south", Z2, u, 12, 8, 15, style="panes", frame_ramp=R["paint_white"],
                 lintel="trim")
        H.window(f"back_upper_window_{i + 1}", g["openings"], "south", Z2 + 2, u, 41, 8, 14, style="panes",
                 frame_ramp=R["paint_white"], lintel="trim")
    H.window("front_window_left", g["openings"], "north", Z1, -20, 12, 9, 15, style="panes", frame_ramp=R["paint_white"],
             lintel="trim", shutters="paint_teal", flowerbox="wood")
    H.window("front_upper_window_right", g["openings"], "north", Z1 - 2, 18, 41, 9, 14, style="panes",
             frame_ramp=R["paint_white"], lintel="trim", shutters="paint_teal")
    # front bay: a projecting block with a balcony and its own gable
    B = g["bay"]
    H.box("bay_plinth", B, [-11, 0, -27], [11, 3, -18], "plinth", ("down",), "bpl", place="ground")
    H.box("bay_walls", B, [-10, 3, -26], [10, 34, -18], "wall", ("down", "up"), "bw", place="ground")
    H.window("bay_window", B, "north", -26, 0, 10, 14, 17, style="panes", frame_ramp=R["paint_white"], lintel="trim",
             flowerbox="wood")
    for side, plane in (("east", 10), ("west", -10)):
        H.window(f"bay_side_window_{side}", B, side, plane, -22, 12, 5, 14, style="panes", frame_ramp=R["paint_white"],
                 lintel=None)
    H.box("balcony_floor", B, [-11, 34, -28], [11, 36, -18], "trim", (), "bf")
    H.box("bay_upper", B, [-9, 36, -24], [9, 62, -20], "wall", ("down", "up"), "bu", place="top")
    H.window("bay_upper_door", B, "north", -24, 0, 36, 8, 18, style="panes", frame_ramp=R["paint_white"], lintel="trim",
             sill=None, arch=True)
    H.box("balcony_rail", B, [-11, 43, -28], [11, 44, -27], "trim", (), "brl")
    for s, x in (("left", -11), ("right", 10)):
        H.box(f"balcony_side_rail_{s}", B, [x, 43, -28], [x + 1, 44, -24], "trim", (), "bsr")
    for i in range(10):
        x = -10 + i * 2.2
        H.box(f"balcony_baluster_{i + 1}", B, [x - 0.5, 36, -28], [x + 0.5, 43, -27], "trim", ("down",), "bbal")
    # roofs: main ridge east-west, a cross gable over the bay, white lace bargeboards and a gold crest
    prof = [(0, 3)] + [(3, 4)] * 5 + [(2.5, 4)] * 2 + [(2, 3.5)]
    top = H.roof("roof", g["roofs"], X1 - 2, X2 + 2, Z1 - 2, Z2 + 2, 62, prof, "roof", "wall", axis="x", eave=3,
                 caps=("lace", 1.5), ridge=("trim", 2, 1.5), crest=("gold", 4), finials=("gold", 6))
    H.roof("bay_roof", B, -11, 11, -27, -10, 62, [(0, 2.5), (2.5, 3.5), (2.5, 3.5), (2.5, 3.5), (2, 3.5), (2, 3.5), (1.5, 3)],
           "roof", "wall", axis="z", eave=2, caps=("lace", 1.5), ridge=("trim", 1.5, 1), finials=("gold", 5))
    H.chimney("chimney", g["roofs"], -18, 10, 6, 6, 56, top - 4, "stone", cap="trim")
    H.lantern("lantern", g["details"], "north", Z1, 9, 24)
    return H


# ==================================================================== 6. timber house (stone + half timbering)
def wood_timber_house():
    H = House("wood_timber_house", 6606, mats("plaster", "tile_slate", "slate", wall_kind="plaster",
              roof_extra={"moss": True}, trim="walnut", trim_kind="carved", wood="walnut",
              extra={"stone": {"kind": "ashlar", "ramp": R["stone"], "side": (144, 80), "top": (48, 48)},
                     "beam": {"kind": "boards", "ramp": R["walnut"], "side": (64, 16), "top": (24, 24), "no_lit2": True,
                              "extra": {"bw": 3, "lap": False, "nails": False, "shadow_top": False}},
                     "brick": {"kind": "brick", "ramp": R["brick_red"], "side": (24, 96), "top": (24, 24), "no_lit2": True}}))
    g = {k: H.group(k, [0, 0, 0]) for k in ("walls", "frame", "openings", "roofs", "oriel", "details")}
    X1, X2, Z1, Z2 = -24, 24, -18, 18
    plinth(H, g["walls"], X1, X2, Z1, Z2)
    H.box("ground_walls", g["walls"], [X1, 3, Z1], [X2, 32, Z2], "stone", ("down", "up"), "gw", place="ground")
    band(H, "floor_band", g["walls"], X1, X2, Z1, Z2, 32, 2, 2.5, "beam")
    U1, U2, W1, W2 = X1 - 2, X2 + 2, Z1 - 2, Z2 + 2
    H.box("upper_walls", g["walls"], [U1, 34, W1], [U2, 62, W2], "wall", ("down", "up"), "uw", place="top")
    timber_frame(H, "frame", g["frame"], U1, U2, W1, W2, 34, 62)
    for i in range(10):
        x = X1 + 2 + i * (X2 - X1 - 4) / 9
        H.box(f"joist_{i + 1}", g["frame"], [x - 0.75, 31, Z1 - 2], [x + 0.75, 32, Z1], "beam", (), "joist")
    H.door("front_door", g["openings"], "north", Z1, -6, 3, 14, 26, wood="oak", frame="stone", arch=True, canopy=None,
           steps="stone")
    H.window("front_window", g["openings"], "north", Z1, 12, 11, 10, 14, style="leaded", arch=True,
             frame_ramp=R["paint_cream"], sill="stone", lintel="stone", flowerbox="beam")
    # upper windows sit in the bays without braces (bays 2, 4 on the long sides)
    for side, plane, us in (("north", W1, (-7.5, 15.5)), ("south", W2, (-7.5, 15.5)), ("east", U2, (0,)), ("west", U1, (0,))):
        for i, u in enumerate(us):
            H.window(f"{side}_upper_window_{i + 1}", g["openings"], side, plane, u, 40, 7, 12, style="leaded",
                     frame_ramp=R["paint_cream"], sill="beam", lintel=None, shutters=None,
                     flowerbox="beam" if side == "north" else None)
    for side, plane in (("east", X2), ("west", X1)):
        H.window(f"{side}_window", g["openings"], side, plane, 0, 12, 8, 13, style="leaded", arch=True,
                 frame_ramp=R["paint_cream"], sill="stone", lintel="stone")
    H.window("back_window", g["openings"], "south", Z2, 0, 12, 8, 13, style="leaded", arch=True, frame_ramp=R["paint_cream"],
             sill="stone", lintel="stone")
    # steep slate roof, ridge front to back, plaster gables with carved bargeboards
    prof = [(0, 3)] + [(3, 4.5)] * 5 + [(2.5, 4.5)] * 2 + [(2, 4)] * 2
    top = H.roof("roof", g["roofs"], U1, U2, W1, W2, 62, prof, "roof", "wall", axis="z", eave=3,
                 caps=("trim", 1.5), ridge=("trim", 2, 1.5), finials=("trim", 5))
    for side, plane in (("north", W1), ("south", W2)):
        H.window(f"gable_window_{side}", g["openings"], side, plane, 0, 72, 6, 9, style="leaded", arch=True,
                 frame_ramp=R["paint_cream"], sill="beam", lintel=None)
    # oriel turret on the front right corner of the upper floor
    O = g["oriel"]; cx, cz, D = 29, -23, 10      # on the front right corner, outside the jettied wall
    H.octo("oriel_corbel", O, cx, cz, D - 4, 28, 31, "stone", (), "oc1")
    H.octo("oriel_corbel_2", O, cx, cz, D - 2, 31, 34, "stone", (), "oc2")
    H.octo("oriel_body", O, cx, cz, D, 34, 58, "wall", ("down", "up"), "ob", place="top")
    H.octo("oriel_band", O, cx, cz, D + 1.5, 58, 60, "beam", ("down",), "oband")
    H.window("oriel_window", O, "north", cz - D / 2, cx, 42, 4, 9, style="leaded", arch=True, frame_ramp=R["paint_cream"],
             sill="beam", lintel=None)
    H.window("oriel_window_east", O, "east", cx + D / 2, cz, 42, 4, 9, style="leaded", arch=True, frame_ramp=R["paint_cream"],
             sill="beam", lintel=None)
    H.cone("oriel_cone", O, cx, cz, D + 4, 60, 92, "roof", n=7, finial="gold")
    H.chimney("chimney", g["roofs"], -12, 10, 6, 6, 56, top - 4, "brick", cap="stone")
    H.lantern("lantern", g["details"], "north", Z1, 6, 22)
    return H


BUILDERS = {f.__name__: f for f in (brick_rose_cottage, brick_bluebell_house, brick_honey_townhouse, wood_oak_lodge,
                                    wood_cherry_manor, wood_timber_house)}

if __name__ == "__main__":
    names = sys.argv[1:] or list(BUILDERS)
    for n in names:
        BUILDERS[n]().finish([OUT])
