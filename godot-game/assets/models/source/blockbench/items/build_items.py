"""Builds the items in the world (MODELS-BLOCKBENCH section 2, "Items in the world"):

    python build_items.py

Dropped ore for every ore (D-005), an ingot for every metal (D-054), a hide for every animal
(D-029, D-032), a dried bundle for every plant (D-022, D-062), a log and a plank for every wood
(D-105, D-107), every gem (D-012) and a small pile of IMP coins. Each item's colours are sampled
from its own inventory icon in godot-game/assets/sprites/source/items/, so the world model and
the icon always match. World assets: 2 px per unit, lying on y = 0.

Writes godot-game/assets/models/items/<id>.bbmodel (+ textures/items/) and one lineup per kind.
"""
import math
import subprocess
import sys
from pathlib import Path

import numpy as np

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bbkit import Mat, Model, from_base, icon_ramp, put, ramp, stretch  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "items"
TEX = GAME / "assets" / "textures" / "items"
ICONS = GAME / "assets" / "sprites" / "source" / "items"
PPU = 2

STONE = ramp("#2c2f38", "#3e424c", "#545862", "#6c707a", "#8a8e96", "#aeb2b8")
TWINE = ramp("#4a3820", "#6a5432", "#8c7448", "#ae9460", "#ccb27c")

# [id, icon file] from GameData (Titanite and Dreadstone pictures still use the old names, D-020).
ORES = [("tin", "tin"), ("copper", "copper"), ("iron", "iron"), ("coal", "coal"), ("gold", "gold"),
        ("obsidian", "obsidian"), ("titanite", "mithril"), ("dreadstone", "adamantite"), ("void", "void"),
        ("stellarite", "stellarite")]
GEMS = ["topaz", "sapphire", "amethyst", "ruby", "emerald", "jade", "diamond", "painite", "arcanium", "eclipsium"]
ANIMALS = ["hare", "fox", "boar", "wolf", "goldhorn_stag", "shadowcat", "frostmane_yeti", "cinder_salamander",
           "voidstalker", "starwyrm", "stormhorn_ram", "tidecrest_serpent", "mossmane_behemoth",
           "crystalback_basilisk", "sunfeather_griffin", "eclipse_dragon"]
PLANTS = ["nettle", "marigold", "bluebell", "thornroot", "sunpetal", "nightshade", "frostbloom", "bloodcap",
          "voidlily", "starmoss"]
WOODS = ["ash", "birch", "oak", "pine", "goldleaf", "ebony", "silverbark", "bloodwood", "voidwood", "starwood"]


def icon(name):
    return icon_ramp(ICONS / f"{name}.png", 7)


def chip_lines(r):
    """Ore veins: short bright lines across the stone chips."""
    def d(area, f, w, h, c, rng):
        for _ in range(max(1, w * h // 18)):
            x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
            for k in range(int(rng.integers(2, 4))):
                put(area, x + k, y, r[5])
                put(area, x + k, y + 1, r[2])
    return d


def ore(oid, ic):
    m = Model("coal" if oid == "coal" else f"{oid}_ore", ppu=PPU)
    root = m.group(m.name)
    r = icon(f"nugget_{ic}")
    chunk = Mat("ore", r, "gem" if oid in ("obsidian", "titanite", "void", "stellarite") else "metal", base=4, scratch_area=30)
    stone = Mat("stone", STONE if oid != "coal" else ramp("#0e0e12", "#1a1a20", "#26262e", "#34343e", "#44444e"), "stone", base=3)
    for i, (x, z, s, a) in enumerate(((0, 0, 3.0, 25), (2.25, 1.0, 2.0, -35), (-1.75, 1.5, 2.25, 50), (0.75, -2.0, 1.5, 10))):
        m.cube(f"chunk_{i + 1}", (x - s / 2, 0, z - s / 2), (x + s / 2, s * 0.85, z + s / 2), chunk if i != 3 else stone, root,
               rotation=(0, a, 0), origin=(x, 0, z), decal=chip_lines(r) if i == 3 else None)
    if oid != "coal":
        m.cube("chunk_top", (-0.75, 2.5, -0.75), (0.75, 3.5, 0.75), chunk, root, rotation=(15, 30, 10), origin=(0, 2.5, 0))
    return m


def ingot(oid, ic):
    m = Model(f"{oid}_ingot", ppu=PPU)
    root = m.group(m.name)
    r = icon(f"ingot_{ic}")
    metal = Mat("metal", r, "metal", base=3, polish=True, bevel=True, scratch_area=40)
    m.cube("base", (-3.5, 0, -1.75), (3.5, 1.5, 1.75), metal, root)
    m.cube("top", (-2.75, 1.5, -1.25), (2.75, 2.25, 1.25), metal.variant("top", base=4), root,
           decal=lambda a, f, w, h, c, rng: [put(a, x, y, r[1]) for (x, y) in ((w // 2 - 1, h // 2), (w // 2, h // 2), (w // 2 + 1, h // 2))] if f == "up" else None)
    return m


def hide(aid):
    m = Model(f"{aid}_hide", ppu=PPU)
    root = m.group(m.name)
    r = icon(f"hide_{aid}")
    fur = Mat("fur", r, "fur", base=4)
    skin = Mat("skin", r, "leather", base=2, stitch=False)
    m.cube("pelt", (-4, 0, -5), (4, 0.75, 5), fur, root)
    m.cube("pelt_hump", (-2.5, 0.75, -3), (2.5, 1.25, 3), fur, root)
    for i, (x, z, a) in enumerate(((4.5, -4, 30), (-4.5, -4, -30), (4.5, 4, -30), (-4.5, 4, 30))):
        m.cube(f"leg_{i + 1}", (x - 1.25, 0, z - 0.75), (x + 1.25, 0.5, z + 0.75), fur, root, rotation=(0, a, 0), origin=(x, 0, z))
    m.cube("neck", (-1.5, 0, -6.5), (1.5, 0.6, -5), fur, root)
    m.cube("tail", (-0.5, 0, 5), (0.5, 0.5, 7), fur, root)
    m.cube("edge_curl", (-3.5, 0.75, 4.5), (3.5, 1.0, 5.0), skin, root)
    return m


def bundle(pid):
    m = Model(f"{pid}_bundle", ppu=PPU)
    root = m.group(m.name)
    r = icon(f"bundle_{pid}")
    plant = icon(f"plant_{pid}")
    stems = Mat("stems", r, "fur", base=3)
    heads = Mat("heads", plant[1:] + plant[-1:], "gem", base=4)
    twine = Mat("twine", TWINE, "rope", base=2)
    m.cube("stems", (-4, 0, -1.0), (2.5, 1.25, 1.0), stems, root, rotation=(0, 10, 0), origin=(0, 0, 0))
    m.cube("stems_spread", (2.0, 0, -2.25), (4.5, 1.75, 2.25), stems, root, rotation=(0, 10, 0), origin=(0, 0, 0))
    for i, (x, z, s) in enumerate(((5.0, -2.0, 1.5), (5.75, 0.0, 2.0), (5.0, 2.0, 1.5), (4.0, -0.75, 1.25), (4.25, 1.0, 1.25),
                                   (6.25, -1.25, 1.0))):
        m.cube(f"head_{i + 1}", (x - s / 2, 1.0, z - s / 2), (x + s / 2, 1.0 + s, z + s / 2), heads, root, rotation=(0, 10, 0),
               origin=(0, 0, 0), share="head")
    m.cube("tie", (-0.5, -0.0, -1.5), (0.75, 2.0, 1.5), twine, root, rotation=(0, 10, 0), origin=(0, 0, 0))
    return m


def log(wid):
    m = Model(f"{wid}_log", ppu=PPU)
    root = m.group(m.name)
    r = icon(f"log_{wid}")
    bark = Mat("bark", r, "wood", base=3, grain_dir="h")
    ring_r = icon(f"plank_{wid}") if (ICONS / f"plank_{wid}.png").exists() else r
    rings = Mat("rings", ring_r, "plain", base=4)

    def ring_decal(area, f, w, h, c, rng):
        if f not in ("east", "west"):
            return
        cx, cy = (w - 1) / 2, (h - 1) / 2
        for y in range(h):
            for x in range(w):
                d = math.hypot(x - cx, y - cy)
                if int(d) % 2 == 1:
                    put(area, x, y, ring_r[2])
        put(area, int(cx), int(cy), ring_r[1])

    # an eight-sided log from crossed boxes, lying along x
    m.cube("core", (-6, 0.5, -1.5), (6, 4.5, 1.5), bark, root)
    m.cube("side", (-6, 1, -2), (6, 4, 2), bark, root)
    m.cube("end_right", (6, 1, -1.5), (6.5, 4, 1.5), rings, root, decal=ring_decal)
    m.cube("end_left", (-6.5, 1, -1.5), (-6, 4, 1.5), rings, root, decal=ring_decal)
    m.cube("knot", (-1, 4.5, -0.75), (0.5, 5, 0.5), bark.variant("knot", base=2), root)
    m.cube("stub_branch", (2, 3.5, -2.5), (3, 4.5, -2), bark, root)
    return m


def plank(wid):
    m = Model(f"{wid}_plank", ppu=PPU)
    root = m.group(m.name)
    name = f"plank_{wid}" if (ICONS / f"plank_{wid}.png").exists() else f"log_{wid}"
    r = icon(name)
    wood = Mat("wood", r, "wood", base=4, grain_dir="h", grain_step=2)
    m.cube("board_1", (-6, 0, -2.5), (6, 0.75, -0.25), wood, root)
    m.cube("board_2", (-5.5, 0, 0.25), (6.5, 0.75, 2.5), wood, root)
    m.cube("board_3", (-5.75, 0.75, -1.25), (5.75, 1.5, 1.25), wood.variant("top", base=4), root, rotation=(0, 6, 0), origin=(0, 0.75, 0))
    return m


def gem(gid):
    m = Model(gid, ppu=PPU)
    root = m.group(m.name)
    r = icon(f"gemstone_{gid}")
    g = Mat("gem", r, "gem", base=4)
    if gid in ("arcanium", "eclipsium"):
        g = Mat("gem_glow", r, "glow", base=4)
    nm = "_glow" if g.kind == "glow" else ""
    m.cube("crown" + nm, (-1.5, 1.25, -1.5), (1.5, 3.25, 1.5), g, root, rotation=(0, 45, 0), origin=(0, 2, 0))
    m.cube("girdle" + nm, (-2, 1.75, -1), (2, 2.75, 1), g, root)
    m.cube("girdle_z" + nm, (-1, 1.75, -2), (1, 2.75, 2), g, root)
    m.cube("table" + nm, (-0.75, 3.25, -0.75), (0.75, 3.75, 0.75), g, root, rotation=(0, 45, 0), origin=(0, 3.5, 0))
    m.cube("pavilion" + nm, (-1, 0.25, -1), (1, 1.25, 1), g, root, rotation=(0, 45, 0), origin=(0, 0.75, 0))
    m.cube("point" + nm, (-0.4, 0, -0.4), (0.4, 0.25, 0.4), g, root)
    return m


def coins():
    m = Model("imp_coins", ppu=PPU)
    root = m.group(m.name)
    gold = Mat("gold", stretch(ramp("8a3e14", "ce6825", "e38a23", "f19f26", "f9d369", "f9f47d")), "metal", base=4, polish=True)
    for i, (x, z, y) in enumerate(((0, 0, 0), (0.25, 0.25, 0.5), (-0.25, 0, 1.0), (0, -0.25, 1.5), (2.75, 1.5, 0), (-2.5, 1.75, 0), (1.75, -2.25, 0))):
        m.cube(f"coin_{i + 1}", (x - 1.25, y, z - 1.25), (x + 1.25, y + 0.5, z + 1.25), gold, root, share="coin",
               rotation=(0, i * 17, 0), origin=(x, y, z))
    return m


def main():
    groups = {
        "ores": [ore(o, i) for o, i in ORES],
        "ingots": [ingot(o, i) for o, i in ORES if o != "coal"],
        "hides": [hide(a) for a in ANIMALS],
        "bundles": [bundle(p) for p in PLANTS],
        "logs": [log(w) for w in WOODS],
        "planks": [plank(w) for w in WOODS],
        "gems": [gem(g) for g in GEMS] + [coins()],
    }
    for kind, models in groups.items():
        paths = []
        for m in models:
            p, n, size = m.save(OUT, TEX)
            paths.append(p)
            print(f"{Path(p).name}: {n} cubes, texture {size}")
        spacing = {"hides": 16, "logs": 16, "planks": 16, "bundles": 14}.get(kind, 9)
        subprocess.run([sys.executable, str(HERE.parent / "make_lineup.py"), str(OUT / f"{kind}_lineup.bbmodel"), str(spacing), "5", *paths],
                       check=True)


if __name__ == "__main__":
    main()
