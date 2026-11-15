"""Builds the props and crafting stations, to docs/blockbench_detailed_prompts.md section 3.11.

    python build_props.py            # all props
    python build_props.py furnace    # one

Stations from the decided systems: furnace (D-054), anvil (blacksmith, D-013), drying rack (D-022),
tanning rack (D-029), sawbench (D-107) and a workbench. Hub props from game_worlds.md section 3:
market stall, notice board, bench, barrel, crate, lantern post, signpost, well, fence and the
portal. World assets: 2 px per unit, standing on y = 0, centred on x = 0, z = 0, front facing
north (-z). Wood is built from separate planks with gaps, stone from separate blocks; moving parts
(doors, lids) get their own group with the pivot at the hinge. Glowing parts end in `_glow`.

Writes godot-game/assets/models/props/<prop>.bbmodel, the texture to textures/props/, and
props_lineup.bbmodel.
"""
import math
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bbkit import Mat, Model, put, ramp, stretch  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "props"
TEX = GAME / "assets" / "textures" / "props"
PPU = 2

# Ramps from the guide (section 5 and 3.11.1).
BARK = ramp("#24140e", "#3a2216", "#52321e", "#6c4428", "#885834", "#a67244")
DOOR = ramp("#2a1a12", "#3e281a", "#563824", "#6e4a30", "#8a603e")
DARKWOOD = ramp("#1e1416", "#2c1e1e", "#3c2a26", "#503830", "#664838")
STONE = ramp("#1c1e26", "#2c2f38", "#3e424c", "#545862", "#6c707a", "#8a8e96", "#aeb2b8")
WARM = ramp("#2a2220", "#3e332e", "#554740", "#6e5e54", "#8a786a", "#a89484", "#c4b2a0")
LIME = ramp("#4a4036", "#66594b", "#82735f", "#9c8c74", "#b5a58a", "#cbbda0", "#e0d4ba")
IRON = ramp("#1c1f24", "#30353c", "#4a5059", "#6a717b", "#8a929c")
LEATHER = ramp("#2a160e", "#422416", "#5c3420", "#78462a", "#965c36", "#b07648")
HIDE = ramp("#4a2a16", "#6a3e22", "#8a5630", "#a87040", "#c48c56", "#dcaa72")
ROPE = ramp("#4a3820", "#6a5432", "#8c7448", "#ae9460", "#ccb27c")
STRAW = ramp("#5a4418", "#7a5e22", "#9c7c30", "#bc9c44", "#d8bc60", "#ecd684")
PAPER = ramp("#8a7c62", "#a8987a", "#c4b494", "#dacca8", "#ece2c4")
RED = ramp("#3a0c10", "#5c141a", "#801e24", "#a42c2c", "#c84a3c", "#e07a5a")
CREAM = ramp("#8a7a5a", "#a89470", "#c8b48a", "#e0d0a8", "#f0e6c8")
MOSS = ramp("#1e3014", "#2e481a", "#42621f", "#5c7e28", "#7a9a34")
HERB = ramp("#1e3a14", "#2c5218", "#3e6e20", "#548c2a", "#72aa38", "#98c650")
FIRE = ramp("#3a0a04", "#7a1a06", "#c43e0a", "#ec7a16", "#f8b030", "#fce070", "#fff4c0")
WATER = ramp("#0e2030", "#163450", "#204a6c", "#2e628a", "#4a80a8")
PORTAL = ramp("#04121c", "#0a2a3e", "#104a66", "#18708e", "#28a0b8", "#5ad0d8", "#b8f4f0")
SLATE = ramp("#1e2329", "#2c333b", "#3c444e", "#4e5762", "#646d78", "#7f8892")
GLASS = ramp("#1a2230", "#263244", "#3a4a60", "#5a6e86")

M = dict(
    plank=Mat("plank", BARK, "plank", base=3, plank=3.0),
    plank_v=Mat("plank_v", BARK, "plank", base=3, plank=3.0, grain_dir="v"),
    wood=Mat("wood", BARK, "wood", base=3),
    dark=Mat("dark", DARKWOOD, "wood", base=3),
    door=Mat("door", DOOR, "plank", base=2, plank=2.5, grain_dir="v"),
    stone=Mat("stone", STONE, "brick", base=3, block=(8, 4), mortar=1),
    rough=Mat("rough", STONE, "stone", base=3),
    warm=Mat("warm", WARM, "brick", base=4, block=(8, 4), mortar=1),
    lime=Mat("lime", LIME, "brick", base=4, block=(8, 4), mortar=1),
    iron=Mat("iron", IRON, "metal", base=2, bevel=True, scratch_area=50),
    leather=Mat("leather", LEATHER, "leather", base=3),
    hide=Mat("hide", HIDE, "leather", base=3, stitch=False),
    rope=Mat("rope", ROPE, "rope", base=2),
    straw=Mat("straw", STRAW, "wood", base=3, grain_step=2, grain_dir="v"),
    paper=Mat("paper", PAPER, "cloth", base=3, fold=6, noise=0.04, edges=False),
    awning=Mat("awning", RED, "cloth", base=3, fold=4, noise=0.05, bands=(CREAM, 6)),
    cloth=Mat("cloth", CREAM, "cloth", base=3, fold=3),
    moss=Mat("moss", MOSS, "stone", base=3, cracks=0),
    herb=Mat("herb", HERB, "fur", base=3),
    fire=Mat("fire_glow", FIRE, "glow", base=4),
    coal=Mat("coal", ramp("#0e0e12", "#1a1a20", "#26262e", "#34343e"), "stone", base=2),
    water=Mat("water", WATER, "glass", base=2, edges=False),
    portal=Mat("portal_glow", PORTAL, "glow", base=4),
    slate=Mat("slate", SLATE, "slate", base=3),
    glass=Mat("glass", GLASS, "glass", base=1),
    lamp=Mat("lamp_glow", ramp("#7a4a10", "#c07a1a", "#eca83a", "#f8d070", "#fff0b0", "#fffae0"), "glow", base=3),
)


def planks(m, g, name, frm, to, axis, n, mat=None, gap=0.0, jitter=0.0, seed=0):
    """Splits a board area into n planks along axis (0 = x, 2 = z), each slightly different."""
    mat = mat or M["plank"]
    out = []
    lo, hi = frm[axis], to[axis]
    step = (hi - lo) / n
    for i in range(n):
        a = list(frm)
        b = list(to)
        a[axis] = lo + i * step + gap / 2
        b[axis] = lo + (i + 1) * step - gap / 2
        if jitter:
            k = ((i * 7 + seed) % 3 - 1) * jitter
            b[1] += k
        out.append(m.cube(f"{name}_{i + 1}", a, b, mat, g))
    return out


def post(m, g, name, x, z, h, s=2.0, mat=None, y=0.0):
    return m.cube(name, (x - s / 2, y, z - s / 2), (x + s / 2, y + h, z + s / 2), mat or M["wood"], g)


def finish(m):
    m.scale_dummy((max(14, 0), 0, -12))
    return m


# ---------------------------------------------------------------- stations

def furnace():
    m = Model("furnace", ppu=PPU)
    root = m.group("furnace")
    base = m.group("base", (0, 0, 0), root)
    # stone body, stepped, with a plinth
    m.cube("plinth", (-11, 0, -9), (11, 2, 9), M["rough"], base)
    # the body is built round the mouth so the fire sits in a real recess
    m.cube("body", (-10, 2, -6), (10, 16, 8), M["stone"], base)
    m.cube("body_front_right", (4.5, 2, -8), (10, 16, -6), M["stone"], base)
    m.cube("body_front_left", (-10, 2, -8), (-4.5, 16, -6), M["stone"], base)
    m.cube("body_front_top", (-4.5, 12, -8), (4.5, 16, -6), M["stone"], base)
    m.cube("shoulder", (-9, 16, -7), (9, 19, 7), M["stone"], base)
    m.cube("ledge_low", (-10.5, 9, -8.5), (10.5, 10, 8.5), M["rough"], base)
    m.cube("ledge_top", (-9.5, 19, -7.5), (9.5, 20, 7.5), M["rough"], base)
    m.cube("chimney", (-3.5, 20, -2.5), (3.5, 30, 3.5), M["stone"], base)
    m.cube("chimney_cap", (-4.5, 30, -3.5), (4.5, 31.5, 4.5), M["rough"], base)
    m.cube("chimney_soot", (-2.5, 31.5, -1.5), (2.5, 32, 2.5), M["coal"], base)
    # mouth: recessed arch with fire, iron frame, coal pile, bellows
    m.cube("mouth_frame_top", (-6, 12, -9), (6, 13.5, -8), M["iron"], base)
    m.cube("mouth_frame_right", (4.5, 3, -9), (6, 12, -8), M["iron"], base)
    m.cube("mouth_frame_left", (-6, 3, -9), (-4.5, 12, -8), M["iron"], base)
    m.cube("mouth_back_glow", (-4.5, 3, -6.5), (4.5, 12, -6), M["fire"], base)
    m.cube("mouth_floor", (-4.5, 2, -8), (4.5, 3, -6), M["coal"], base)
    for i, (x, h) in enumerate(((-3, 2.5), (-0.5, 3.5), (2.5, 2.0))):
        m.cube(f"flame_{i + 1}_glow", (x - 1, 3, -7.5), (x + 1, 3 + h, -6.5), M["fire"], base)
    m.cube("ore_tray", (6.5, 10, -11), (10.5, 11, -8), M["iron"], base)
    m.cube("ingot_1", (7, 11, -10.5), (9.5, 12, -9.5), Mat("ingot", ramp("#5a3014", "#8a4e20", "#b86e2e", "#d88e44", "#eeb066"), "metal", base=3), base)
    # coal heap beside it
    for i, (x, z, s) in enumerate(((-13, -4, 3), (-12.5, -1, 2.5), (-14, -1.5, 2))):
        m.cube(f"coal_heap_{i + 1}", (x - s / 2, 0, z - s / 2), (x + s / 2, s * 0.6, z + s / 2), M["coal"], base)
    # iron door on the mouth (opens on its left hinge)
    door = m.group("door", (-6, 3, -9), root)
    m.cube("door_grate_1", (-6, 3, -9.5), (-5.25, 12, -9), M["iron"], door)
    # bellows on the right side
    bel = m.group("bellows", (10, 6, 0), root)
    m.cube("bellows_body", (10, 4, -3), (13, 8, 3), M["leather"], bel)
    m.cube("bellows_board_top", (10, 8, -3.5), (13.5, 8.5, 3.5), M["wood"], bel)
    m.cube("bellows_board_low", (10, 3.5, -3.5), (13.5, 4, 3.5), M["wood"], bel)
    m.cube("bellows_nozzle", (9, 5.5, -0.5), (10, 6.5, 0.5), M["iron"], bel)
    m.cube("bellows_handle", (13.5, 7.5, -0.5), (16, 8.25, 0.5), M["wood"], bel)
    m.cube("moss_1", (-9, 20, 3), (-5, 20.5, 7), M["moss"], base)
    return finish(m)


def anvil():
    m = Model("anvil", ppu=PPU)
    root = m.group("anvil")
    # stump
    m.cube("stump", (-5, 0, -4), (5, 7, 4), Mat("stump", BARK, "wood", base=2, grain_dir="v"), root)
    m.cube("stump_top", (-4.5, 7, -3.5), (4.5, 7.5, 3.5), Mat("rings", ramp("#6c4428", "#885834", "#a67244", "#c4905a", "#dcae76"), "wood", base=2, grain_step=2), root)
    for i, (x, z) in enumerate(((5, -2), (-5.5, 1.5), (2, 4.5))):
        m.cube(f"root_{i + 1}", (x - 1, 0, z - 1), (x + 1, 1.5, z + 1), M["wood"], root)
    # anvil: foot, waist, face, horn, heel
    a = M["iron"].variant("anvil", base=2, polish=True)
    m.cube("foot", (-4, 7.5, -2.5), (4, 9, 2.5), a, root)
    m.cube("waist", (-2.5, 9, -1.5), (2.5, 11, 1.5), a, root)
    m.cube("face", (-5, 11, -2.25), (5, 13.5, 2.25), a, root)
    m.cube("face_top", (-5, 13.5, -2), (5, 14, 2), M["iron"].variant("bright", base=3, polish=True), root)
    m.cube("horn_1", (5, 11.5, -1.75), (7.5, 13.75, 1.75), a, root)
    m.cube("horn_2", (7.5, 12.25, -1.25), (9.5, 13.5, 1.25), a, root)
    m.cube("horn_3", (9.5, 12.75, -0.5), (11, 13.25, 0.5), a, root)
    m.cube("heel", (-7, 12, -1.75), (-5, 14, 1.75), a, root)
    # hammer resting on top, tongs leaning on the stump
    m.cube("hammer_handle", (-3, 14, -0.4), (3, 14.75, 0.4), M["wood"], root, rotation=(0, 20, 0), origin=(0, 14.4, 0))
    m.cube("hammer_head", (2.5, 14, -1.25), (4, 15.5, 1.25), M["iron"], root, rotation=(0, 20, 0), origin=(0, 14.4, 0))
    m.cube("tongs_1", (-6.5, 0.5, -4.25), (-6, 9, -3.75), M["iron"], root, rotation=(0, 0, -12), origin=(-6.25, 0.5, -4))
    m.cube("tongs_2", (-5.5, 0.5, -4.25), (-5, 9, -3.75), M["iron"], root, rotation=(0, 0, -8), origin=(-5.25, 0.5, -4))
    return finish(m)


def drying_rack():
    m = Model("drying_rack", ppu=PPU)
    root = m.group("drying_rack")
    for s, nm in ((1, "right"), (-1, "left")):
        for z, zn in ((-4, "front"), (4, "back")):
            m.cube(f"leg_{nm}_{zn}", (s * 11 - 0.75, 0, z - 0.75), (s * 11 + 0.75, 22, z + 0.75), M["wood"], root,
                   rotation=(10 if z < 0 else -10, 0, 0), origin=(s * 11, 0, z))
        m.cube(f"brace_{nm}", (s * 11 - 0.5, 8, -4), (s * 11 + 0.5, 9, 4), M["wood"], root)
    m.cube("top_beam", (-13, 21, -1), (13, 23, 1), M["wood"], root)
    m.cube("rail_low", (-12, 12, -0.5), (12, 13, 0.5), M["wood"], root)
    # bundles of herbs hanging on twine
    colours = [HERB, ramp("#3a2a14", "#5c4220", "#7e5e30", "#a07c40", "#c09c58"), ramp("#2a1830", "#442a50", "#644070", "#865a94", "#a87ab4"),
               HERB, ramp("#5a4418", "#7a5e22", "#9c7c30", "#bc9c44", "#d8bc60")]
    for i, x in enumerate((-8, -4, 0, 4, 8)):
        g = m.group(f"bundle_{i + 1}", (x, 21, 0), root)
        m.cube(f"twine_{i + 1}", (x - 0.25, 18, -0.25), (x + 0.25, 21, 0.25), M["rope"], g)
        m.cube(f"tie_{i + 1}", (x - 1, 17, -1), (x + 1, 18, 1), M["rope"], g)
        mat = Mat(f"herb_{i}", colours[i], "fur", base=3)
        m.cube(f"stems_{i + 1}", (x - 1.25, 13.5 - (i % 2), -1.25), (x + 1.25, 17, 1.25), mat, g)
        m.cube(f"leaves_{i + 1}", (x - 1.75, 12.5 - (i % 2), -1.75), (x + 1.75, 14.5 - (i % 2), 1.75), mat, g)
    # basket underneath
    m.cube("basket", (-4, 0, -3), (4, 3, 3), M["straw"], root)
    m.cube("basket_rim", (-4.5, 3, -3.5), (4.5, 3.5, 3.5), M["rope"], root)
    return finish(m)


def tanning_rack():
    m = Model("tanning_rack", ppu=PPU)
    root = m.group("tanning_rack")
    m.cube("post_right", (8, 0, -1), (10, 22, 1), M["wood"], root)
    m.cube("post_left", (-10, 0, -1), (-8, 22, 1), M["wood"], root)
    m.cube("bar_top", (-11, 20, -1.25), (11, 22, 1.25), M["wood"], root)
    m.cube("bar_low", (-10, 3, -0.75), (10, 4.5, 0.75), M["wood"], root)
    m.cube("foot_right", (7, 0, -4), (11, 1.5, 4), M["wood"], root)
    m.cube("foot_left", (-11, 0, -4), (-7, 1.5, 4), M["wood"], root)
    # the hide, stretched, with lacing to the frame
    hide = m.group("hide", (0, 12, 0), root)
    m.cube("hide_main", (-6, 6, -0.25), (6, 18.5, 0.25), M["hide"], hide)
    m.cube("hide_leg_tr", (6, 16, -0.25), (7.5, 19, 0.25), M["hide"], hide)
    m.cube("hide_leg_tl", (-7.5, 16, -0.25), (-6, 19, 0.25), M["hide"], hide)
    m.cube("hide_leg_br", (6, 5, -0.25), (7.5, 8, 0.25), M["hide"], hide)
    m.cube("hide_leg_bl", (-7.5, 5, -0.25), (-6, 8, 0.25), M["hide"], hide)
    for i, (x0, y0, x1, y1) in enumerate(((7.5, 18, 8, 19), (-8, 18, -7.5, 19), (7.5, 6, 8, 7), (-8, 6, -7.5, 7),
                                          (-0.25, 18.5, 0.25, 20), (-0.25, 4.5, 0.25, 6))):
        m.cube(f"lace_{i + 1}", (x0, y0, -0.3), (x1, y1, 0.3), M["rope"], hide)
    # scraper tool and a stool of hides
    m.cube("scraper_blade", (11, 6, -3), (13, 7, -2), M["iron"], root)
    m.cube("scraper_handle", (13, 6.25, -2.75), (15, 6.75, -2.25), M["wood"], root)
    m.cube("hide_pile", (-14, 0, -3), (-9, 2, 3), M["hide"].variant("pile", base=2), root)
    m.cube("hide_pile_top", (-13.5, 2, -2.5), (-9.5, 2.75, 2.0), M["hide"], root)
    return finish(m)


def sawbench():
    m = Model("sawbench", ppu=PPU)
    root = m.group("sawbench")
    for x, nm in ((-8, "left"), (8, "right")):
        for z, zn in ((-3, "front"), (3, "back")):
            m.cube(f"leg_{nm}_{zn}", (x - 0.75, 0, z - 0.75), (x + 0.75, 10, z + 0.75), M["wood"], root,
                   rotation=(14 if z < 0 else -14, 0, 0), origin=(x, 10, z * 0.2))
    m.cube("beam", (-11, 9.5, -1.5), (11, 11.5, 1.5), M["plank"], root)
    # log on the bench, with cut rings at both ends
    log = Mat("log", BARK, "wood", base=2, grain_dir="h")
    rings = Mat("rings", ramp("#6c4428", "#885834", "#a67244", "#c4905a", "#dcae76"), "wood", base=2, grain_step=2)
    m.cube("log", (-10, 11.5, -2.5), (10, 16.5, 2.5), log, root)
    m.cube("log_end_right", (10, 12, -2), (10.5, 16, 2), rings, root)
    m.cube("log_end_left", (-10.5, 12, -2), (-10, 16, 2), rings, root)
    m.cube("saw_cut", (3, 15.5, -2.6), (3.5, 16.5, 2.6), M["dark"], root)
    # saw stuck in the cut
    saw = m.group("saw", (3.25, 16, 0), root)
    m.cube("saw_blade", (3, 15, -6), (3.5, 19, 2), M["iron"].variant("blade", base=3, polish=True), saw,
           rotation=(-20, 0, 0), origin=(3.25, 16, 0))
    m.cube("saw_handle", (2.75, 18, -8), (3.75, 21, -5.5), M["wood"], saw, rotation=(-20, 0, 0), origin=(3.25, 16, 0))
    # planks stacked beside
    for i in range(3):
        m.cube(f"plank_stack_{i + 1}", (-9 + i * 0.5, i * 1.0, 5), (9 - i * 0.5, i * 1.0 + 1.0, 9), M["plank"], root)
    m.cube("sawdust", (-1, 0, -4), (6, 0.5, 2), M["straw"].variant("dust", base=4), root)
    return finish(m)


def workbench():
    m = Model("workbench", ppu=PPU)
    root = m.group("workbench")
    for x in (-10.5, 10.5):
        for z in (-4.5, 4.5):
            post(m, root, f"leg_{'right' if x > 0 else 'left'}_{'front' if z < 0 else 'back'}", x, z, 11, 2.0)
    planks(m, root, "top", (-12, 11, -6), (12, 13, 6), 2, 4, M["plank"], gap=0.0, jitter=0.0)
    m.cube("apron_front", (-11, 9, -5.5), (11, 11, -4.5), M["wood"], root)
    m.cube("shelf", (-11, 3, -5), (11, 4, 5), M["plank"], root)
    m.cube("vice_body", (8, 13, -6.5), (11, 15, -3.5), M["iron"], root)
    m.cube("vice_screw", (9.25, 13.5, -8.5), (9.75, 14.5, -6.5), M["iron"], root)
    m.cube("vice_handle", (8.5, 13.75, -8.75), (10.5, 14.25, -8.25), M["iron"], root)
    # tools on top: hammer, chisel, a hilt in progress
    m.cube("hammer_handle", (-6, 13, -1), (0, 13.75, -0.25), M["wood"], root, rotation=(0, 25, 0), origin=(-3, 13.4, -0.6))
    m.cube("hammer_head", (-1, 13, -2), (0.75, 14.5, 0.75), M["iron"], root, rotation=(0, 25, 0), origin=(-3, 13.4, -0.6))
    m.cube("chisel", (2, 13, 2), (6, 13.5, 2.75), M["iron"], root)
    m.cube("hilt_blank", (-9, 13, 1), (-3, 14.25, 2.5), M["wood"], root)
    m.cube("shavings", (-9, 13, -4), (-5, 13.25, -1), M["straw"].variant("shavings", base=4), root)
    # tool rack on the back
    m.cube("rack_board", (-11, 13, 5), (11, 22, 6), M["plank_v"], root)
    for i, x in enumerate((-7, -2, 3)):
        m.cube(f"peg_{i + 1}", (x - 0.5, 19, 3.5), (x + 0.5, 19.75, 5), M["dark"], root)
    m.cube("hung_saw", (2, 14.5, 4.25), (8, 18.5, 5), M["iron"].variant("blade", base=3), root)
    m.cube("hung_axe_handle", (-7.4, 14, 4.25), (-6.6, 19.5, 4.9), M["wood"], root)
    m.cube("hung_axe_head", (-9, 17.5, 4.1), (-7.4, 19.5, 4.9), M["iron"], root)
    return finish(m)


# ---------------------------------------------------------------- hub props

def market_stall():
    m = Model("market_stall", ppu=PPU)
    root = m.group("market_stall")
    for x in (-13, 13):
        for z in (-7, 7):
            post(m, root, f"post_{'right' if x > 0 else 'left'}_{'front' if z < 0 else 'back'}", x, z, 24 if z > 0 else 22, 2)
    # counter
    planks(m, root, "counter_front", (-12, 1, -7.5), (12, 11, -6.5), 0, 6, M["plank_v"])
    planks(m, root, "counter_top", (-13, 11, -8), (13, 12.5, -2), 2, 3, M["plank"])
    m.cube("counter_side_right", (11, 1, -6.5), (12, 11, -2), M["plank"], root)
    m.cube("counter_side_left", (-12, 1, -6.5), (-11, 11, -2), M["plank"], root)
    # awning: sloped striped cloth with a scalloped edge
    aw = m.group("awning", (0, 24, 0), root)
    m.cube("awning_cloth", (-15, 23, -10), (15, 24, 9), M["awning"], aw, rotation=(-12, 0, 0), origin=(0, 24, 8))
    for i in range(7):
        x = -14 + i * 4.33
        m.cube(f"awning_flap_{i + 1}", (x - 1.75, 20.25, -10.6), (x + 1.75, 22.0, -10.1), M["awning"], aw)
    m.cube("awning_beam", (-15, 21.5, -8), (15, 22.5, -6.5), M["wood"], aw)
    # goods: crates with fruit, a basket, a hanging sign
    for i, (x, col) in enumerate(((-8, ramp("#5a0a0a", "#8a1414", "#b82020", "#d8402a", "#f07050")),
                                  (-2, ramp("#5a3a04", "#8a5c0a", "#c08010", "#e0a828", "#f8d050")),
                                  (4, ramp("#1e3a14", "#2c5218", "#3e6e20", "#548c2a", "#72aa38")))):
        m.cube(f"goods_crate_{i + 1}", (x - 2.5, 12.5, -7), (x + 2.5, 15, -3), M["plank"], root)
        fruit = Mat(f"goods_{i}", col, "gem", base=3)
        for j, (fx, fz, fy) in enumerate(((-1.25, -5.75, 0), (0.25, -5.75, 0), (1.5, -5.5, 0), (-1.0, -4.25, 0),
                                          (0.5, -4.25, 0), (-0.25, -5.0, 1.0))):
            m.cube(f"goods_{i + 1}_{j + 1}", (x + fx - 0.65, 14.5 + fy, fz - 0.65), (x + fx + 0.65, 15.8 + fy, fz + 0.65), fruit, root,
                   share=f"fruit_{i}")
    m.cube("scale_base", (8, 12.5, -6), (11, 13, -3), M["iron"], root)
    m.cube("scale_post", (9.25, 13, -4.75), (9.75, 16, -4.25), M["iron"], root)
    m.cube("scale_beam", (7.5, 16, -4.75), (11.5, 16.5, -4.25), M["iron"], root)
    m.cube("sign", (-6, 18, -8.5), (6, 21, -8), M["plank"].variant("sign", base=4), root)
    m.cube("sacks", (-12, 0, 2), (-6, 5, 7), M["cloth"], root)
    m.cube("sacks_top", (-11, 5, 3), (-7, 6, 6), M["rope"], root)
    return finish(m)


def notice_board():
    m = Model("notice_board", ppu=PPU)
    root = m.group("notice_board")
    post(m, root, "post_right", 9, 0, 26, 2)
    post(m, root, "post_left", -9, 0, 26, 2)
    planks(m, root, "board", (-8, 9, -0.5), (8, 22, 0.5), 0, 5, M["plank_v"])
    m.cube("frame_top", (-9, 22, -1), (9, 23, 1), M["wood"], root)
    m.cube("frame_low", (-9, 8, -1), (9, 9, 1), M["wood"], root)
    roof = m.group("roof", (0, 26, 0), root)
    m.cube("roof_right", (0, 25, -3), (11, 26, 3), M["slate"], roof, rotation=(0, 0, -20), origin=(0, 27, 0))
    m.cube("roof_left", (-11, 25, -3), (0, 26, 3), M["slate"], roof, rotation=(0, 0, 20), origin=(0, 27, 0))
    m.cube("roof_ridge", (-1, 26.5, -3.25), (1, 27.5, 3.25), M["wood"], roof)
    # notes, pinned at slight angles
    for i, (x, y, w, h, a) in enumerate(((-5, 17, 5, 4, -4), (1.5, 16.5, 4, 5, 3), (-4.5, 11, 4, 4, 2), (2, 10.5, 5, 4, -3))):
        m.cube(f"note_{i + 1}", (x, y, -0.75), (x + w, y + h, -0.5), M["paper"], root, rotation=(0, 0, a), origin=(x + w / 2, y + h / 2, -0.6),
               decal=_writing)
        m.cube(f"pin_{i + 1}", (x + w / 2 - 0.25, y + h - 1, -1.0), (x + w / 2 + 0.25, y + h - 0.5, -0.75), Mat("pin", RED, "plain", base=4), root)
    return finish(m)


def _writing(area, f, w, h, c, rng):
    if f != "north":
        return
    ink = (60, 52, 46)
    for y in range(2, h - 1, 2):
        x0, x1 = 1, max(2, w - 1 - int(rng.integers(0, 3)))
        for x in range(x0, x1):
            if rng.random() < 0.8:
                put(area, x, y, ink)


def bench():
    m = Model("bench", ppu=PPU)
    root = m.group("bench")
    for x in (-8, 8):
        m.cube(f"leg_{'right' if x > 0 else 'left'}", (x - 1, 0, -2.5), (x + 1, 5, 2.5), M["rough"].variant("seat_stone", kind="stone"), root)
    planks(m, root, "seat", (-11, 5, -3), (11, 6.5, 3), 2, 3, M["plank"])
    post(m, root, "back_post_right", 8, 3, 13, 1.5)
    post(m, root, "back_post_left", -8, 3, 13, 1.5)
    planks(m, root, "back", (-10.5, 8.5, 2.75), (10.5, 12.5, 3.75), 0, 1, M["plank"])
    m.cube("back_rail", (-10.5, 9, 2.75), (10.5, 10, 3.75), M["dark"], root)
    return finish(m)


def barrel():
    m = Model("barrel", ppu=PPU)
    root = m.group("barrel")
    staves = Mat("staves", BARK, "plank", base=3, plank=2.0, grain_dir="v", nails=False)
    m.cube("body", (-4.5, 0.5, -4.5), (4.5, 13.5, 4.5), staves, root)
    m.cube("bulge_x", (-5, 2.5, -3.5), (5, 11.5, 3.5), staves, root)
    m.cube("bulge_z", (-3.5, 2.5, -5), (3.5, 11.5, 5), staves, root)
    for i, y in enumerate((1.5, 11.0)):
        m.cube(f"hoop_{i + 1}", (-4.75, y, -4.75), (4.75, y + 1, 4.75), M["iron"], root)
    for i, y in enumerate((4.5, 8.5)):
        m.cube(f"hoop_mid_x_{i + 1}", (-5.25, y, -3.75), (5.25, y + 1, 3.75), M["iron"], root)
        m.cube(f"hoop_mid_z_{i + 1}", (-3.75, y, -5.25), (3.75, y + 1, 5.25), M["iron"], root)
    m.cube("foot", (-4, 0, -4), (4, 0.5, 4), M["dark"], root)
    lid = m.group("lid", (0, 13.5, -4), root)
    m.cube("lid", (-4, 13.5, -4), (4, 14, 4), Mat("lid", BARK, "plank", base=4, plank=2.0, plank_top=True), lid)
    m.cube("bung", (-0.75, 14, -0.75), (0.75, 14.5, 0.75), M["dark"], lid)
    return finish(m)


def crate():
    m = Model("crate", ppu=PPU)
    root = m.group("crate")
    s = 6
    planks(m, root, "front", (-s, 0, -s), (s, 2 * s, -s + 1), 0, 4, M["plank_v"])
    planks(m, root, "back", (-s, 0, s - 1), (s, 2 * s, s), 0, 4, M["plank_v"])
    planks(m, root, "right", (s - 1, 0, -s + 1), (s, 2 * s, s - 1), 2, 4, M["plank_v"])
    planks(m, root, "left", (-s, 0, -s + 1), (-s + 1, 2 * s, s - 1), 2, 4, M["plank_v"])
    frame = M["dark"]
    for i, (a, b) in enumerate((((-s - 0.5, 0, -s - 0.5), (-s + 1, 2 * s, -s + 1)), ((s - 1, 0, -s - 0.5), (s + 0.5, 2 * s, -s + 1)),
                                ((-s - 0.5, 0, s - 1), (-s + 1, 2 * s, s + 0.5)), ((s - 1, 0, s - 1), (s + 0.5, 2 * s, s + 0.5)))):
        m.cube(f"corner_{i + 1}", a, b, frame, root)
    m.cube("brace_front", (-s + 1, 0.5, -s - 0.4), (s - 1, 1.5, -s), frame, root, rotation=(0, 0, 40), origin=(0, s, -s - 0.2))
    lid = m.group("lid", (0, 2 * s, s), root)
    planks(m, lid, "lid", (-s, 2 * s, -s), (s, 2 * s + 1, s), 2, 4, M["plank"])
    m.cube("straw_tuft", (-3, 2 * s + 1, -2), (1, 2 * s + 1.75, 2), M["straw"], lid)
    return finish(m)


def lantern_post():
    m = Model("lantern_post", ppu=PPU)
    root = m.group("lantern_post")
    m.cube("base", (-2.5, 0, -2.5), (2.5, 3, 2.5), M["stone"], root)
    m.cube("base_cap", (-2, 3, -2), (2, 3.5, 2), M["rough"], root)
    m.cube("post", (-1, 3.5, -1), (1, 30, 1), M["dark"], root)
    m.cube("arm", (-1, 28, -1), (8, 29.5, 0.5), M["iron"], root)
    m.cube("arm_brace", (0, 24, -0.6), (5, 25, 0.1), M["iron"], root, rotation=(0, 0, 40), origin=(1, 24.5, -0.25))
    lamp = m.group("lantern", (7, 28, -0.25), root)
    m.cube("hook", (6.75, 26.5, -0.5), (7.25, 28, 0), M["iron"], lamp)
    m.cube("lantern_cap", (5, 25.5, -2.25), (9, 26.5, 1.75), M["iron"], lamp)
    m.cube("lantern_light_glow", (5.5, 21.5, -1.75), (8.5, 25.5, 1.25), M["lamp"], lamp)
    for i, (x, z) in enumerate(((5.25, -2.0), (8.25, -2.0), (5.25, 1.0), (8.25, 1.0))):
        m.cube(f"lantern_bar_{i + 1}", (x, 21.5, z), (x + 0.5, 25.5, z + 0.75), M["iron"], lamp)
    m.cube("lantern_base", (5, 21, -2.25), (9, 21.5, 1.75), M["iron"], lamp)
    return finish(m)


def signpost():
    m = Model("signpost", ppu=PPU)
    root = m.group("signpost")
    m.cube("post", (-1, 0, -1), (1, 24, 1), M["wood"], root)
    m.cube("cap", (-1.5, 24, -1.5), (1.5, 25, 1.5), M["dark"], root)
    for i, (y, a, d) in enumerate(((20, 10, 1), (15.5, -25, -1), (11, 70, 1))):
        g = m.group(f"sign_{i + 1}", (0, y, 0), root)
        m.cube(f"sign_board_{i + 1}", (1 if d > 0 else -11, y, -0.5), (11 if d > 0 else -1, y + 3, 0.5), M["plank"].variant("sign", base=4),
               g, rotation=(0, a, 0), origin=(0, y, 0), decal=_letters)
        tipx = 11 if d > 0 else -11
        m.cube(f"sign_tip_{i + 1}", (tipx - 1 if d > 0 else tipx, y + 0.5, -0.5), (tipx if d > 0 else tipx + 1, y + 2.5, 0.5),
               M["plank"].variant("sign", base=4), g, rotation=(0, a, 0), origin=(0, y, 0))
    m.cube("grass_tuft", (-2.5, 0, -2.5), (2.5, 1, 2.5), M["moss"], root)
    return finish(m)


def _letters(area, f, w, h, c, rng):
    if f not in ("north", "south") or h < 4:
        return
    ink = (58, 34, 22)
    x = 2
    while x < w - 3:
        for y in range(1, h - 1):
            if rng.random() < 0.7:
                put(area, x, y, ink)
        x += int(rng.integers(2, 4))


def well():
    m = Model("well", ppu=PPU)
    root = m.group("well")
    # octagonal stone ring from two crossed squares
    m.cube("ring_a", (-8, 0, -6), (8, 8, 6), M["stone"], root)
    m.cube("ring_b", (-6, 0, -8), (6, 8, 8), M["stone"], root)
    m.cube("ring_cap_a", (-8.5, 8, -6.5), (8.5, 9, 6.5), M["rough"], root)
    m.cube("ring_cap_b", (-6.5, 8, -8.5), (6.5, 9, 8.5), M["rough"], root)
    m.cube("water", (-6, 8.5, -4.5), (6, 9.1, 4.5), M["water"], root)
    m.cube("water_b", (-4.5, 8.5, -6), (4.5, 9.1, 6), M["water"], root)
    m.cube("moss_1", (-8.5, 0, -6.5), (-4, 2, -5.5), M["moss"], root)
    post(m, root, "post_right", 7.5, 0, 22, 1.75, y=9)
    post(m, root, "post_left", -7.5, 0, 22, 1.75, y=9)
    roof = m.group("roof", (0, 31, 0), root)
    m.cube("roof_front", (-10, 29, -7), (10, 30.5, 0.5), M["slate"], roof, rotation=(-30, 0, 0), origin=(0, 32, 0))
    m.cube("roof_back", (-10, 29, -0.5), (10, 30.5, 7), M["slate"], roof, rotation=(30, 0, 0), origin=(0, 32, 0))
    m.cube("ridge", (-10.5, 31.5, -1), (10.5, 32.5, 1), M["wood"], roof)
    winch = m.group("winch", (0, 24, 0), root)
    m.cube("axle", (-7, 23.5, -0.5), (7, 24.5, 0.5), M["wood"], winch)
    m.cube("rope_coil", (-2, 23, -1), (2, 25, 1), M["rope"], winch)
    m.cube("crank", (8.5, 22, -0.4), (9.25, 24.5, 0.4), M["iron"], winch)
    m.cube("rope", (-0.25, 15, -0.25), (0.25, 23, 0.25), M["rope"], root)
    m.cube("bucket", (-1.75, 12, -1.75), (1.75, 15, 1.75), Mat("bucket", BARK, "plank", base=3, plank=1.5, grain_dir="v", nails=False), root)
    m.cube("bucket_hoop", (-2, 13, -2), (2, 13.5, 2), M["iron"], root)
    return finish(m)


def fence():
    m = Model("fence", ppu=PPU)
    root = m.group("fence")
    for i, x in enumerate((-8, 8)):
        m.cube(f"post_{i + 1}", (x - 1, 0, -1), (x + 1, 12, 1), M["wood"], root)
        m.cube(f"post_cap_{i + 1}", (x - 0.75, 12, -0.75), (x + 0.75, 12.75, 0.75), M["wood"], root)
    m.cube("rail_top", (-9, 9, -0.5), (9, 10.5, 0.5), M["plank"], root, rotation=(0, 0, 2), origin=(0, 9.75, 0))
    m.cube("rail_low", (-9, 4, -0.5), (9, 5.5, 0.5), M["plank"], root, rotation=(0, 0, -1.5), origin=(0, 4.75, 0))
    m.cube("grass", (-9, 0, -1.5), (-5, 1.25, 1.5), M["moss"], root)
    return finish(m)


def portal():
    m = Model("portal", ppu=PPU)
    root = m.group("portal")
    m.cube("platform", (-18, 0, -8), (18, 2, 8), M["stone"], root)
    m.cube("step", (-12, 0, -11), (12, 1, -8), M["rough"], root)
    # pillars of stacked blocks
    for s, nm in ((1, "right"), (-1, "left")):
        for i in range(6):
            w = 5.5 - (i % 2) * 0.75
            m.cube(f"pillar_{nm}_{i + 1}", (s * 14 - w / 2, 2 + i * 5, -w / 2), (s * 14 + w / 2, 7 + i * 5, w / 2), M["warm"], root)
        m.cube(f"pillar_cap_{nm}", (s * 14 - 3.5, 32, -3.5), (s * 14 + 3.5, 33.5, 3.5), M["rough"], root)
        m.cube(f"rune_{nm}_glow", (s * 14 - 1, 12, -3.1), (s * 14 + 1, 20, -2.6), M["portal"], root)
    # arch from rotated blocks
    for i in range(7):
        a = math.radians(180 * (i + 0.5) / 7)
        x, y = math.cos(a) * 13, 33 + math.sin(a) * 6
        m.cube(f"arch_{i + 1}", (x - 2.75, y - 2, -3), (x + 2.75, y + 2, 3), M["warm"], root,
               rotation=(0, 0, math.degrees(a) - 90), origin=(x, y, 0))
    m.cube("keystone", (-2, 38, -3.5), (2, 42, 3.5), M["rough"], root)
    m.cube("keystone_gem_glow", (-1, 39, -4), (1, 41, -3.5), M["portal"], root)
    # the swirl: layered glowing panes
    for i, (w, h, z) in enumerate(((22, 30, 0), (18, 26, -0.75), (12, 20, -1.25), (6, 12, -1.6))):
        m.cube(f"swirl_{i + 1}_glow", (-w / 2, 2 + (30 - h) / 2 + 1, z - 0.25), (w / 2, 2 + (30 - h) / 2 + 1 + h, z + 0.25), M["portal"], root)
    for i, (x, y, a) in enumerate(((-9, 35, 20), (8, 37, -30), (10, 8, 45), (-11, 6, -15))):
        m.cube(f"spark_{i + 1}_glow", (x - 0.75, y - 0.75, -2.5), (x + 0.75, y + 0.75, -1), M["portal"], root, rotation=(0, 0, a), origin=(x, y, -1.75))
    m.cube("moss", (-18, 2, -8), (-12, 2.75, -2), M["moss"], root)
    return finish(m)


PROPS = {"furnace": furnace, "anvil": anvil, "drying_rack": drying_rack, "tanning_rack": tanning_rack,
         "sawbench": sawbench, "workbench": workbench, "market_stall": market_stall, "notice_board": notice_board,
         "bench": bench, "barrel": barrel, "crate": crate, "lantern_post": lantern_post, "signpost": signpost,
         "well": well, "fence": fence, "portal": portal}


def main():
    names = sys.argv[1:] or list(PROPS)
    paths = []
    for n in names:
        m = PROPS[n]()
        p, cubes, size = m.save(OUT, TEX)
        paths.append(p)
        print(f"{Path(p).name}: {cubes} cubes, texture {size}")
    if len(names) == len(PROPS):
        subprocess.run([sys.executable, str(HERE.parent / "make_lineup.py"), str(OUT / "props_lineup.bbmodel"), "44", "4", *paths], check=True)


if __name__ == "__main__":
    main()
