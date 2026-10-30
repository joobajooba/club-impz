"""Builds the armour, to docs/blockbench_detailed_prompts.md section 3.7.

    python build_armour.py

Seven pieces (helmet, chestplate, shoulders, gauntlets, belt, leggings, boots) in ten tiers. The
first tier is Leather (the guide: "low tiers are leather and simple"); the rest follow the tool
ladder, Bronze to Stellarite. Every piece fits the imp in
`source/blockbench/creatures/impling.bbmodel`: it sits 0.25 to 0.5 units outside the body cubes,
and its groups are named after the imp bone they follow, with that bone's pivot, so Godot can
attach each group to the bone. The big eyes and the ears stay free; helmets stop above the brows
and leave the ears and horns out. 2 px per unit, like the imp.

Writes godot-game/assets/models/armour/<tier>_<piece>.bbmodel (+ textures/armour/), and
armour_sets_lineup.bbmodel: the imp wearing each full set, Leather to Stellarite.
"""
import json
import math
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
sys.path.insert(0, str(HERE.parent / "weapons"))
from bbkit import Mat, Model, put, ramp, stretch  # noqa: E402
from build_weapons import TIERS as WEAPON_TIERS, LEATHER, VOID_GLOW, STAR_GLOW  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "armour"
TEX = GAME / "assets" / "textures" / "armour"
IMP = HERE.parent / "creatures" / "impling.bbmodel"
PPU = 2

# Imp bone pivots, from impling.bbmodel.
BONES = {
    "head": (0, 7.5, -0.25), "chest": (0, 5.0, -0.25), "body": (0, 3.5, -0.25),
    "arm_right": (3.25, 6.75, -0.25), "arm_left": (-3.25, 6.75, -0.25),
    "forearm_right": (3.25, 5.5, -0.25), "forearm_left": (-3.25, 5.5, -0.25),
    "hand_right": (3.25, 4.0, -0.25), "hand_left": (-3.25, 4.0, -0.25),
    "thigh_right": (1.5, 3.5, -0.25), "thigh_left": (-1.5, 3.5, -0.25),
    "leg_right": (1.5, 2.0, -0.25), "leg_left": (-1.5, 2.0, -0.25),
    "foot_right": (1.5, 1.0, -0.25), "foot_left": (-1.5, 1.0, -0.25),
}

LEATHER_T = dict(id="leather", metal=stretch(ramp("2a160e", "422416", "5c3420", "78462a", "965c36", "b8804e")),
                 wood=None, wrap=LEATHER, gem=None, level=0, soft=True,
                 trim=stretch(ramp("4f2f18", "795331", "915237", "c67734", "ec9966")))
TIERS = [LEATHER_T] + WEAPON_TIERS[1:]
CLOTH = {"gold": stretch(ramp("3a0c10", "5c141a", "801e24", "a42c2c", "c84a3c")),
         "stellarite": stretch(ramp("1a2048", "243064", "30408a", "4a5cae", "6e82cc"))}


def mats(T):
    L = T["level"]
    M = {}
    if T.get("soft"):
        M["plate"] = Mat("plate", T["metal"], "leather", base=3)
    else:
        M["plate"] = Mat("plate", T["metal"], "metal", base=3, bevel=True, polish=L >= 4, scratch_area=45)
    M["dark"] = Mat("dark", T["metal"], "metal" if not T.get("soft") else "leather", base=2, bevel=True)
    M["trim"] = Mat("trim", T.get("trim", T["metal"]), "metal", base=4, bevel=True)
    M["strap"] = Mat("strap", LEATHER, "leather", base=2)
    if T["id"] in CLOTH:
        M["cloth"] = Mat("cloth", CLOTH[T["id"]], "cloth", base=3, fold=3)
    if T["gem"]:
        M["gem"] = Mat("gem", T["gem"], "gem", base=3)
    if T.get("glow"):
        M["glow"] = Mat("glow", T["glow"], "glow", base=4)
    return M


def rivets(T):
    """Rivet pixels in the corners of plates (metal tiers)."""
    r = T["metal"]

    def d(area, f, w, h, c, rng):
        if f in ("up", "down") or w < 5 or h < 4:
            return
        for x, y in ((1, 1), (w - 2, 1)):
            put(area, x, y, r[-1])
            put(area, x, y + 1, r[1])
    return None if T.get("soft") else d


class Fit:
    """Builds one armour piece: groups per bone, helpers for plates and mirrored pairs."""

    def __init__(self, T, piece):
        self.T, self.M, self.L, self.tid = T, mats(T), T["level"], T["id"]
        self.m = Model(f"{T['id']}_{piece}", ppu=PPU, ground=True)
        self.root = self.m.group(self.m.name, (0, 0, 0))
        self.groups = {}

    def g(self, bone):
        if bone not in self.groups:
            self.groups[bone] = self.m.group(bone, BONES[bone], self.root)
        return self.groups[bone]

    def c(self, bone, name, frm, to, mat, **kw):
        return self.m.cube(name, frm, to, self.M[mat] if isinstance(mat, str) else mat, self.g(bone), **kw)

    def pair(self, bone_r, name, frm, to, mat, **kw):
        """A cube on the right side (x > 0) and its mirror on the left bone."""
        a = self.c(bone_r, name + "_right", frm, to, mat, **kw)
        bone_l = bone_r.replace("_right", "_left")
        rot = kw.get("rotation")
        org = kw.get("origin")
        kw2 = dict(kw)
        if rot:
            kw2["rotation"] = (rot[0], -rot[1], -rot[2])
        if org:
            kw2["origin"] = (-org[0], org[1], org[2])
        b = self.c(bone_l, name + "_left", (-to[0], frm[1], frm[2]), (-frm[0], to[1], to[2]), mat, **kw2)
        return a, b

    def spike(self, bone, name, base, length, angle_z, mat="dark", s=0.5, angle_x=0):
        x, y, z = base
        return self.c(bone, name, (x - s / 2, y, z - s / 2), (x + s / 2, y + length, z + s / 2), mat,
                      rotation=(angle_x, 0, angle_z), origin=(x, y, z))

    def save(self):
        self.m.scale_dummy((9, 0, 0))
        return self.m.save(OUT, TEX)


# ---------------------------------------------------------------- pieces

def helmet(T):
    f = Fit(T, "helmet")
    L, tid = f.L, f.tid
    b = "head"
    # Stepped dome over the forehead and crown; it starts above the brows (y 12.75) so the eyes stay free.
    f.c(b, "brim", (-4.75, 12.75, -4.5), (4.75, 13.75, 4.25), "trim" if L >= 1 else "plate", decal=rivets(T))
    f.c(b, "dome_low", (-4.5, 13.75, -4.25), (4.5, 15.25, 4.0), "plate")
    f.c(b, "dome_mid", (-3.75, 15.25, -3.5), (3.75, 16.5, 3.25), "plate")
    f.c(b, "dome_top", (-2.75, 16.5, -2.5), (2.75, 17.25, 2.25), "plate")
    # Back guard down the neck, behind the ears.
    f.c(b, "neck_guard", (-3.75, 9.75, 1.0), (3.75, 12.75, 4.25), "plate")
    f.c(b, "neck_guard_flare", (-4.0, 9.25, 2.5), (4.0, 10.0, 4.5), "dark")
    if L >= 2:   # nasal guard between the eyes
        f.c(b, "nasal", (-0.5, 10.25, -4.75), (0.5, 12.75, -4.25), "trim")
    if L >= 3:   # cheek guards behind the ears' front edge (ears stay free)
        f.pair(b, "cheek", (3.25, 8.5, 0.75), (4.25, 12.75, 2.5), "plate")
    if tid == "leather":
        f.c(b, "cap_band", (-4.75, 13.75, -4.5), (4.75, 14.25, -4.0), "strap")
    if tid in ("iron", "steel", "obsidian", "titanite"):
        f.c(b, "crest_ridge", (-0.5, 17.25, -2.75), (0.5, 18.0, 2.5), "trim")
    if tid == "steel":
        f.c(b, "crest_plume", (-0.5, 18.0, -1.5), (0.5, 19.75, 2.75), Mat("plume", stretch(ramp("4a0c10", "801e24", "b02c2c", "d8504a", "f08a6a")), "fur", base=3))
    if tid == "bronze":
        f.c(b, "top_knob", (-0.75, 17.25, -0.75), (0.75, 18.25, 0.75), "trim")
    if tid == "gold":   # crown spikes with an emerald at the front
        for i, x in enumerate((-2.25, -0.75, 0.75, 2.25)):
            f.c(b, f"crown_spike_{i + 1}", (x - 0.4, 17.25, -2.75), (x + 0.4, 18.5 + 0.5 * (i in (1, 2)), -2.0), "trim")
        f.c(b, "front_gem", (-0.75, 13.75, -4.75), (0.75, 14.75, -4.25), "gem")
        f.c(b, "plume", (-0.5, 17.25, -0.5), (0.5, 19.75, 2.5), "cloth")
    if tid == "obsidian":   # knapped shards along the top
        for i, (z, hgt, a) in enumerate(((-2.0, 1.5, -15), (0.0, 2.0, 0), (2.0, 1.25, 15))):
            f.c(b, f"shard_{i + 1}", (-0.5, 17.0, z - 0.5), (0.5, 17.0 + hgt, z + 0.5), "dark", rotation=(a, 0, 0), origin=(0, 17.0, z))
        f.c(b, "front_gem", (-0.5, 13.75, -4.75), (0.5, 14.75, -4.25), "gem")
    if tid == "titanite":   # crystals sprouting from the crown
        for i, (x, z, hgt, a) in enumerate(((-1.75, 0.5, 2.0, 20), (1.75, 0.5, 2.0, -20), (0, -1.0, 2.75, 0))):
            f.c(b, f"crystal_{i + 1}", (x - 0.5, 16.75, z - 0.5), (x + 0.5, 16.75 + hgt, z + 0.5), "gem", rotation=(0, 0, a),
                origin=(x, 16.75, z))
    if tid == "dreadstone":   # curled horns and a painite brow gem
        for s in (1, -1):
            x0, y0 = s * 2.0, 16.25
            for i in range(4):
                a = 25 + i * 22
                ln = 1.25 - 0.15 * i
                dx = math.cos(math.radians(a))
                f.c(b, f"horn_{'right' if s > 0 else 'left'}_{i + 1}", (x0 - 0.5, y0, 1.0), (x0 + 0.5, y0 + ln + 0.25, 2.0), "dark",
                    rotation=(0, 0, -s * (60 - i * 25)), origin=(x0, y0, 1.5))
                x0 += s * ln * 0.8
                y0 += ln * 0.6
        f.c(b, "front_gem", (-0.75, 13.75, -4.75), (0.75, 14.75, -4.25), "gem")
    if tid == "void":
        f.c(b, "seam_glow", (-4.75, 13.75, -4.5), (4.75, 14.25, -4.25), "glow")
        for i, (x, y) in enumerate(((-2.5, 19.0), (1.5, 19.75), (3.0, 18.5))):
            f.c(b, f"fragment_{i + 1}_glow", (x - 0.4, y - 0.4, -0.4), (x + 0.4, y + 0.4, 0.4), "glow", rotation=(0, 0, 45), origin=(x, y, 0))
    if tid == "stellarite":   # halo of light and a star at the front
        f.c(b, "halo_front_glow", (-3.0, 19.0, -2.75), (3.0, 19.5, -2.25), "glow")
        f.c(b, "halo_back_glow", (-3.0, 19.0, 2.25), (3.0, 19.5, 2.75), "glow")
        f.c(b, "halo_right_glow", (2.5, 19.0, -2.25), (3.0, 19.5, 2.25), "glow")
        f.c(b, "halo_left_glow", (-3.0, 19.0, -2.25), (-2.5, 19.5, 2.25), "glow")
        f.c(b, "star_glow", (-0.75, 13.5, -4.75), (0.75, 15.0, -4.25), "glow")
        f.c(b, "trim_band", (-4.5, 15.0, -4.5), (4.5, 15.5, -4.0), "trim")
    return f.save()


def chestplate(T):
    f = Fit(T, "chestplate")
    L, tid = f.L, f.tid
    b = "chest"
    f.c(b, "shell", (-2.75, 4.75, -2.25), (2.75, 7.25, 1.75), "plate", decal=rivets(T))
    f.c(b, "front_plate", (-2.25, 4.75, -2.75), (2.25, 7.0, -2.25), "plate")
    f.c(b, "back_plate", (-2.25, 5.0, 1.75), (2.25, 7.0, 2.25), "plate")
    f.c(b, "gorget", (-2.25, 7.25, -1.75), (2.25, 7.75, 1.25), "trim")
    if L >= 1:   # raised centre ridge
        f.c(b, "ridge", (-0.5, 5.0, -3.0), (0.5, 7.0, -2.75), "trim")
    if tid == "leather":   # cross straps and a buckle
        f.c(b, "strap_front", (-2.25, 5.75, -2.75 - 0.25), (2.25, 6.25, -2.75), "strap")
        f.c(b, "buckle", (-0.5, 5.5, -3.25), (0.5, 6.5, -3.0), "trim")
    if L >= 3:   # belly plates (lames) below the chest
        f.c(b, "lame_1", (-2.75, 4.25, -2.5), (2.75, 4.75, 1.75), "dark")
    if "gem" in f.M:
        f.c(b, "chest_gem", (-0.75, 5.75, -3.25), (0.75, 6.75, -2.75), "gem" if L < 8 else "glow")
    if tid == "gold":
        f.c(b, "tabard", (-1.5, 3.0, -2.75), (1.5, 5.25, -2.5), "cloth")
    if tid == "stellarite":
        f.c(b, "cape", (-2.5, 2.0, 2.25), (2.5, 7.25, 2.75), "cloth")
    if tid == "titanite":
        for s in (1, -1):
            f.c(b, f"crystal_{'right' if s > 0 else 'left'}", (s * 1.75 - 0.4, 7.0, 0.75), (s * 1.75 + 0.4, 9.0, 1.55), "gem",
                rotation=(0, 0, -s * 25), origin=(s * 1.75, 7.0, 1.15))
    if tid == "dreadstone":
        for i, y in enumerate((5.25, 6.5)):
            f.spike(b, f"back_spike_{i + 1}", (0, y, 2.25), 1.5, 0, s=0.5, angle_x=60)
    if tid == "void":
        f.c(b, "seam_glow", (-0.25, 4.75, -2.8), (0.25, 7.0, -2.7), "glow")
    return f.save()


def shoulders(T):
    f = Fit(T, "shoulders")
    L, tid = f.L, f.tid
    b = "arm_right"
    layers = 2 if L < 3 else 3
    f.pair(b, "pad_top", (2.0, 6.5, -1.5), (4.75, 7.5, 1.0), "plate", decal=rivets(T))
    f.pair(b, "pad_mid", (2.5, 5.75, -1.5), (5.0, 6.5, 1.0), "plate")
    if layers == 3:
        f.pair(b, "pad_low", (3.0, 5.0, -1.5), (5.25, 5.75, 1.0), "dark")
    f.pair(b, "pad_rim", (4.75, 6.25, -1.75), (5.25, 7.5, 1.25), "trim")
    if tid == "leather":
        f.pair(b, "strap", (2.5, 5.0, -1.25), (3.0, 6.5, 0.75), "strap")
    if tid in ("steel", "obsidian"):
        f.pair(b, "ridge", (3.0, 7.5, -0.5), (4.5, 8.25, 0.0), "trim" if tid == "steel" else "dark")
    if tid == "gold":
        f.pair(b, "gem", (4.75, 6.25, -1.25), (5.5, 7.0, -0.5), "gem")
        f.pair(b, "fringe", (3.0, 4.25, -1.25), (5.0, 5.0, 0.75), "cloth")
    if tid == "titanite":
        f.pair(b, "crystal", (3.25, 7.25, -0.75), (4.25, 9.25, 0.25), "gem", rotation=(0, 0, -20), origin=(3.75, 7.25, -0.25))
    if tid == "dreadstone":
        f.pair(b, "spike_1", (3.25, 7.25, -1.0), (3.75, 9.5, -0.5), "dark", rotation=(0, 0, -30), origin=(3.5, 7.25, -0.75))
        f.pair(b, "spike_2", (4.0, 7.0, 0.0), (4.5, 8.75, 0.5), "dark", rotation=(0, 0, -45), origin=(4.25, 7.0, 0.25))
        f.pair(b, "gem", (4.75, 6.5, -1.0), (5.5, 7.25, -0.25), "gem")
    if tid == "void":
        f.pair(b, "edge_glow", (5.25, 5.75, -1.5), (5.5, 7.25, 1.0), "glow")
        f.pair(b, "fragment_glow", (4.5, 8.75, -0.5), (5.25, 9.5, 0.25), "glow", rotation=(0, 0, 45), origin=(4.85, 9.1, -0.1))
    if tid == "stellarite":
        f.pair(b, "star_glow", (3.5, 7.5, -0.5), (4.5, 8.5, 0.5), "glow")
        f.pair(b, "trim_band", (2.0, 7.5, -1.5), (4.75, 7.75, -1.0), "trim")
    return f.save()


def gauntlets(T):
    f = Fit(T, "gauntlets")
    L, tid = f.L, f.tid
    f.pair("forearm_right", "cuff", (2.25, 3.75, -1.5), (4.75, 5.5, 1.0), "plate", decal=rivets(T))
    f.pair("forearm_right", "cuff_flare", (2.0, 5.25, -1.75), (5.0, 5.75, 1.25), "trim" if L >= 1 else "strap")
    f.pair("hand_right", "back_plate", (4.25, 2.75, -1.75), (4.75, 4.0, 1.25), "plate")
    f.pair("hand_right", "knuckles", (3.0, 2.25, -2.25), (4.25, 3.0, -1.75), "dark")
    if tid == "leather":
        f.pair("forearm_right", "lace", (4.75, 4.0, -0.75), (5.0, 5.25, 0.25), "strap")
    if L >= 4 and "gem" in f.M:
        f.pair("forearm_right", "gem", (4.75, 4.25, -0.75), (5.25, 5.0, 0.0), "gem")
    if tid == "dreadstone":
        f.pair("forearm_right", "spike", (4.5, 4.5, -0.5), (5.0, 6.25, 0.0), "dark", rotation=(0, 0, -50), origin=(4.75, 4.5, -0.25))
    if tid == "titanite":
        f.pair("forearm_right", "crystal", (4.5, 4.25, -0.25), (5.25, 6.0, 0.5), "gem", rotation=(0, 0, -30), origin=(4.85, 4.25, 0.1))
    if tid == "void":
        f.pair("forearm_right", "seam_glow", (2.25, 4.5, -1.6), (4.75, 4.75, -1.5), "glow")
    if tid == "stellarite":
        f.pair("forearm_right", "star_glow", (4.75, 4.25, -0.75), (5.25, 5.0, 0.0), "glow")
    return f.save()


def belt(T):
    f = Fit(T, "belt")
    L, tid = f.L, f.tid
    b = "body"
    f.c(b, "band", (-3.0, 4.5, -3.0), (3.0, 5.25, 2.5), "strap" if L < 4 else "dark")
    f.c(b, "buckle", (-0.75, 4.25, -3.5), (0.75, 5.5, -3.0), "trim")
    if tid == "leather":
        f.c(b, "pouch", (1.25, 3.25, -3.25), (2.5, 4.5, -2.25), "strap")
    if L >= 2:   # tassets
        f.c(b, "tasset_front_right", (0.5, 2.75, -3.25), (2.75, 4.5, -2.75), "plate", decal=rivets(T))
        f.c(b, "tasset_front_left", (-2.75, 2.75, -3.25), (-0.5, 4.5, -2.75), "plate", decal=rivets(T))
    if L >= 4 and "gem" in f.M:
        f.c(b, "buckle_gem", (-0.4, 4.6, -3.75), (0.4, 5.15, -3.5), "gem" if L < 8 else "glow")
    if tid == "gold":
        f.c(b, "loincloth", (-1.0, 1.75, -3.25), (1.0, 4.5, -3.0), "cloth")
    if tid == "stellarite":
        f.c(b, "loincloth", (-1.0, 1.75, -3.25), (1.0, 4.5, -3.0), "cloth")
    if tid == "dreadstone":
        f.c(b, "skull_buckle", (-1.0, 4.0, -3.75), (1.0, 5.75, -3.5), "dark")
    return f.save()


def leggings(T):
    f = Fit(T, "leggings")
    L, tid = f.L, f.tid
    f.pair("thigh_right", "thigh_plate", (0.25, 2.25, -1.5), (2.75, 4.25, 1.0), "plate", decal=rivets(T))
    f.pair("leg_right", "shin_guard", (0.5, 1.0, -1.5), (2.5, 2.25, 0.75), "plate")
    f.pair("leg_right", "knee_cop", (0.75, 1.75, -1.75), (2.25, 2.75, -1.25), "trim" if L >= 1 else "strap")
    if tid == "dreadstone":
        f.pair("leg_right", "knee_spike", (1.25, 2.25, -2.25), (1.75, 3.5, -1.75), "dark", rotation=(-40, 0, 0), origin=(1.5, 2.25, -1.75))
    if tid == "titanite":
        f.pair("thigh_right", "crystal", (2.5, 3.0, -0.5), (3.25, 4.75, 0.25), "gem", rotation=(0, 0, -25), origin=(2.85, 3.0, -0.1))
    if tid == "void":
        f.pair("thigh_right", "seam_glow", (2.75, 2.5, -1.25), (2.85, 4.0, 0.75), "glow")
    if tid == "stellarite":
        f.pair("leg_right", "star_glow", (1.25, 1.25, -1.75), (1.75, 1.75, -1.5), "glow")
    if L >= 4 and "gem" in f.M and tid != "stellarite":
        f.pair("leg_right", "knee_gem", (1.25, 2.0, -2.0), (1.75, 2.5, -1.75), "gem" if L < 8 else "glow")
    return f.save()


def boots(T):
    f = Fit(T, "boots")
    L, tid = f.L, f.tid
    f.pair("foot_right", "boot", (0.0, 0.0, -2.0), (3.0, 1.25, 1.0), "plate", decal=rivets(T))
    f.pair("foot_right", "toe_cap", (0.25, 0.0, -2.5), (2.75, 1.0, -2.0), "dark")
    f.pair("foot_right", "cuff", (0.25, 1.25, -1.5), (2.75, 1.75, 1.0), "trim" if L >= 1 else "strap")
    f.pair("foot_right", "sole", (-0.25, 0.0, -2.75), (3.25, 0.25, 1.25), "strap" if L < 2 else "dark")
    if tid == "leather":
        f.pair("foot_right", "lace", (1.0, 0.75, -2.25), (2.0, 1.25, -2.0), "trim")
    if tid in ("gold", "stellarite"):
        f.pair("foot_right", "wing", (2.75, 0.75, 0.0), (3.25, 1.75, 1.25), "trim", rotation=(0, 0, -20), origin=(3.0, 0.75, 0.5))
    if tid == "dreadstone":
        f.pair("foot_right", "toe_spike", (1.25, 0.25, -3.5), (1.75, 0.75, -2.5), "dark")
    if tid == "titanite":
        f.pair("foot_right", "crystal", (2.5, 1.0, 0.0), (3.25, 2.5, 0.75), "gem", rotation=(0, 0, -25), origin=(2.85, 1.0, 0.4))
    if tid == "void":
        f.pair("foot_right", "seam_glow", (0.25, 0.25, -2.6), (2.75, 0.5, -2.5), "glow")
    if tid == "stellarite":
        f.pair("foot_right", "star_glow", (1.25, 0.25, -2.75), (1.75, 0.75, -2.5), "glow")
    return f.save()


PIECES = {"helmet": helmet, "chestplate": chestplate, "shoulders": shoulders, "gauntlets": gauntlets,
          "belt": belt, "leggings": leggings, "boots": boots}


def sets_lineup(paths_by_tier, out, spacing=16, per_row=5):
    """The imp wearing each full set: one imp plus the seven pieces per tier, side by side."""
    imp = json.load(open(IMP, encoding="utf-8"))
    elements, groups, outliner, textures = [], [], [], []
    rows = (len(paths_by_tier) + per_row - 1) // per_row
    for k, (tier, paths) in enumerate(paths_by_tier):
        dx = (k % per_row - (per_row - 1) / 2) * spacing
        dy = (rows - 1 - k // per_row) * 26
        ids = []
        for src in [imp] + [json.load(open(p, encoding="utf-8")) for p in paths]:
            ti = len(textures)
            for t in src["textures"]:
                textures.append(dict(t, uuid=str(uuid.uuid4()), id=str(len(textures)), path="", relative_path=None))
            for e in src["elements"]:
                if e.get("export", True) is False or e["name"].startswith("scale_dummy"):
                    continue
                e = json.loads(json.dumps(e))
                e["uuid"] = str(uuid.uuid4())
                for key in ("from", "to", "origin"):
                    e[key] = [e[key][0] + dx, e[key][1] + dy, e[key][2]]
                for fc in e.get("faces", {}).values():
                    if fc.get("texture") is not None:
                        fc["texture"] += ti
                elements.append(e)
                ids.append(e["uuid"])
        g = {"name": f"{tier}_set", "uuid": str(uuid.uuid4()), "export": True, "locked": False, "scope": 0,
             "selected": False, "visibility": True, "origin": [dx, dy, 0], "rotation": [0, 0, 0], "color": 0,
             "children": [], "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": False}
        groups.append(g)
        outliner.append({"uuid": g["uuid"], "isOpen": False, "children": ids})
    res = max(t.get("uv_width", 64) for t in textures)
    doc = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
           "name": Path(out).stem, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
           "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
           "resolution": {"width": res, "height": res}, "elements": elements, "groups": groups,
           "outliner": outliner, "textures": textures}
    json.dump(doc, open(out, "w", encoding="utf-8"))
    print(out, len(elements), "boxes")


def main():
    by_tier = []
    for T in TIERS:
        paths = []
        for name, fn in PIECES.items():
            p, n, size = fn(T)
            paths.append(p)
            print(f"{Path(p).name}: {n} cubes, texture {size}")
        by_tier.append((T["id"], paths))
    sets_lineup(by_tier, OUT / "armour_sets_lineup.bbmodel")


if __name__ == "__main__":
    main()
