"""Builds the hub village buildings, to docs/blockbench_detailed_prompts.md section 3.11 and the
hub castle reference J00BA approved (club-impz PR #21, sections 3.11.1 to 3.11.4).

    python build_buildings.py            # all buildings
    python build_buildings.py tavern     # one

Decorative buildings round the castle (game_worlds.md section 3): a smithy, a general store, a
cottage, a tavern and a watchtower. They copy the castle's moves: a darker base course, a ledge
at every storey, corner quoins, recessed windows and doors (frames proud of the wall), hipped
slate roofs built from stepped tiers, stepped spires with iron finials, dormers and chimneys.
Doors are 16 x 28 next to the 18 unit imp. Backs are finished but simpler. No animation, no glow
except lit windows on the tavern. 2 px per unit; big wall and roof faces crop shared swatches.

Second set (2026-11-08), to the same guide: a guild hall (challenges and trophies) with a crow-stepped
frontispiece and clock tower, a market hall on an open arcade, a stable with a hay loft, a gatehouse
over the road, a narrow townhouse with crow-stepped gables, and a windmill. They add gable roofs
(B.gable_roof), and with B(name, split=True) cut faces bigger than a shared swatch into pieces and
share the paint of repeated small parts, so each still fits one 512 texture after the 2 px island
padding of build scripts/fix_texture_bleed.py.

    python build_buildings.py guild_hall market_hall stable gatehouse townhouse windmill

Writes godot-game/assets/models/buildings/<id>.bbmodel (+ textures/buildings/) and, when every
building is built, buildings_lineup.bbmodel.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bbkit import Mat, Model, put, ramp  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "buildings"
TEX = GAME / "assets" / "textures" / "buildings"
PPU = 2

# The building ramps from section 3.11.1.
LIME = ramp("#4a4036", "#66594b", "#82735f", "#9c8c74", "#b5a58a", "#cbbda0", "#e0d4ba")
SLATE = ramp("#1e2329", "#2c333b", "#3c444e", "#4e5762", "#646d78", "#7f8892")
DOOR = ramp("#2a1a12", "#3e281a", "#563824", "#6e4a30", "#8a603e")
IRON = ramp("#1c1f24", "#30353c", "#4a5059", "#6a717b")
GLASS = ramp("#1a2230", "#263244", "#3a4a60", "#5a6e86")
TIMBER = ramp("#1e1410", "#2e1e16", "#40291c", "#523624", "#66442e")
PLASTER = ramp("#8a7e68", "#a89a80", "#c4b698", "#d8ccb0", "#e8dec6", "#f2ead6")
WARMLIGHT = ramp("#6a3a10", "#a8641a", "#e09a30", "#f4c25a", "#fce08c", "#fff2c0")

SW = (128, 136)
M = dict(
    wall=Mat("wall", LIME, "brick", base=4, block=(8, 4), mortar=2, noise=0.02, edges=False, swatch=SW),
    plaster=Mat("plaster", PLASTER, "cloth", base=3, fold=9, noise=0.05, edges=False, swatch=SW),
    base=Mat("base", LIME, "brick", base=2, block=(10, 5), mortar=0, noise=0.02, edges=False, swatch=(128, 48)),
    ledge=Mat("ledge", LIME, "stone", base=5, cracks=0.2, noise=0.04),
    quoin=Mat("quoin", LIME, "stone", base=5, cracks=0.1, noise=0.03),
    slate=Mat("slate", SLATE, "slate", base=3, tile_h=3, tile_w=4, edges=False, swatch=(136, 104), swatch_faces=("lit", "shade", "up")),
    eave=Mat("eave", SLATE, "slate", base=2, tile_h=3, tile_w=4),
    door=Mat("door", DOOR, "plank", base=3, plank=2.5, grain_dir="v", nails=False),
    frame=Mat("frame", LIME, "stone", base=5, cracks=0.1, noise=0.02),
    recess=Mat("recess", LIME, "plain", base=1, noise=0.0, edges=False),
    glass=Mat("glass", GLASS, "glass", base=1),
    lit=Mat("window_glow", WARMLIGHT, "glow", base=3),
    iron=Mat("iron", IRON, "metal", base=2, bevel=True, noise=0.02),
    timber=Mat("timber", TIMBER, "wood", base=2, grain_step=3),
    plank=Mat("plank", DOOR, "plank", base=3, plank=3.0),
    cloth=Mat("banner", ramp("#3a0c10", "#5c141a", "#801e24", "#a42c2c", "#c84a3c"), "cloth", base=3, fold=3),
    sign=Mat("sign", DOOR, "plank", base=4, plank=6.0, nails=False),
)


class B:
    """Building helper: groups (section 3.11.2) and the castle's repeated parts."""

    def __init__(self, name, split=False):
        """split: cut oversized swatch faces into pieces (see c); used by the second set."""
        self.split = split
        self.m = Model(name, ppu=PPU, max_texture=512)
        self.root = self.m.group(name)
        self.g = {k: self.m.group(k, (0, 0, 0), self.root) for k in
                  ("foundation", "walls", "towers", "roofs", "openings", "details")}
        self.n = {}

    def name(self, base):
        self.n[base] = self.n.get(base, 0) + 1
        return f"{base}_{self.n[base]}"

    # repeated small parts that share one painted rect per size and face (second set only), so a big
    # building's atlas still fits 512 once every island gets its 2 px padding
    SHARED = {"quoin", "corbel", "merlon", "window_frame", "window_sill", "window_lintel", "window_mullion",
              "window_transom", "window_arch", "window_arch_key", "window_glass", "shutter", "timber_post",
              "pillar", "pillar_base", "pillar_capital", "arch", "portcullis_bar", "portcullis_spike", "door_bar",
              "hay_bale", "sail_spar", "sail", "sail_bar", "crate"}

    def c(self, group, base, frm, to, mat, **kw):
        mat = M[mat] if isinstance(mat, str) else mat
        if self.split and base in self.SHARED and "share" not in kw:
            kw["share"] = base
        sw = mat.opts.get("swatch")
        if self.split and sw and not kw.get("decal") and not kw.get("rotation"):
            # a face bigger than the shared swatch would get its own texture area; cut the cube into
            # pieces that each fit, so every face still crops the swatch (the paint follows world
            # position and these materials have no edge lines, so the cuts don't show)
            d = [to[i] - frm[i] for i in range(3)]
            lim = (sw[0] / PPU, sw[1] / PPU, min(sw) / PPU)
            n = [max(1, -int(-d[0] // lim[0])), max(1, -int(-d[1] // lim[1])), max(1, -int(-d[2] // lim[2]))]
            if n != [1, 1, 1]:
                first = None
                for i in range(n[0]):
                    for j in range(n[1]):
                        for k in range(n[2]):
                            a = (frm[0] + d[0] * i / n[0], frm[1] + d[1] * j / n[1], frm[2] + d[2] * k / n[2])
                            b = (frm[0] + d[0] * (i + 1) / n[0], frm[1] + d[1] * (j + 1) / n[1], frm[2] + d[2] * (k + 1) / n[2])
                            cube = self.m.cube(self.name(base), a, b, mat, self.g[group], **kw)
                            first = first or cube
                return first
        return self.m.cube(self.name(base), frm, to, mat, self.g[group], **kw)

    def ring(self, group, base, x0, x1, z0, z1, y0, y1, out, mat, into=0.5):
        """A band round a block as four strips (out past the wall, `into` back into it), so the
        texture holds only the visible ledge, not the whole slab hidden under the wall."""
        X0, X1, Z0, Z1 = x0 - out, x1 + out, z0 - out, z1 + out
        self.c(group, base, (X0, y0, Z0), (X1, y1, z0 + into), mat)
        self.c(group, base, (X0, y0, z1 - into), (X1, y1, Z1), mat)
        self.c(group, base, (X0, y0, z0 + into), (x0 + into, y1, z1 - into), mat)
        self.c(group, base, (x1 - into, y0, z0 + into), (X1, y1, z1 - into), mat)

    # -- body
    def block(self, x0, x1, z0, z1, y0, y1, storeys, mat="wall", base_h=3, quoins=True):
        """A wall block on a base course, with a ledge at every storey and corner quoins."""
        self.ring("foundation", "base_course", x0, x1, z0, z1, y0, y0 + base_h, 1, "base", into=2)
        self.c("walls", "wall", (x0, y0 + base_h, z0), (x1, y1, z1), mat, hide=("up", "down"))
        sh = (y1 - y0 - base_h) / storeys
        for i in range(1, storeys):
            y = y0 + base_h + i * sh
            self.ring("walls", "string_course", x0, x1, z0, z1, y - 1, y, 1, "ledge")
        self.ring("walls", "cornice", x0, x1, z0, z1, y1 - 1, y1, 1.5, "ledge")
        if quoins:
            for x in (x0, x1):
                for z in (z0, z1):
                    y = y0 + base_h
                    k = 0
                    while y + 3 <= y1 - 1:
                        h = 3
                        wx, wz = (3, 2) if k % 2 == 0 else (2, 3)
                        sx = 1 if x == x1 else -1
                        sz = 1 if z == z1 else -1
                        a = (x - wx if sx > 0 else x - 0.5, y, z - wz if sz > 0 else z - 0.5)
                        b = (x + 0.5 if sx > 0 else x + wx, y + h, z + 0.5 if sz > 0 else z + wz)
                        self.c("walls", "quoin", a, b, "quoin")
                        y += h + 0.5
                        k += 1
        return sh

    def hip_roof(self, x0, x1, z0, z1, y, tiers=None, step=2.0, tier_h=2.5, overhang=2.5):
        """A hipped slate roof of stepped tiers; the first is a wide eave over the wall."""
        self.ring("roofs", "eave", x0, x1, z0, z1, y, y + 1.5, overhang, "eave", into=step + 1)
        x0, x1, z0, z1 = x0 - overhang, x1 + overhang, z0 - overhang, z1 + overhang
        y += 1.5
        i = 0
        while x1 - x0 > 2 * step + 1 and z1 - z0 > 2 * step + 1 and (tiers is None or i < tiers):
            x0, x1, z0, z1 = x0 + step, x1 - step, z0 + step, z1 - step
            self.c("roofs", "roof_tier", (x0, y, z0), (x1, y + tier_h, z1), "slate", hide=("down",))
            y += tier_h
            i += 1
        self.c("roofs", "ridge", (x0 + 0.5, y, z0 + 0.5), (x1 - 0.5, y + 1, z1 - 0.5), "iron")
        return y + 1

    def spire(self, cx, cz, w, y, tiers=12, tier_h=2.5, step=1.0):
        """Stepped spire: square tiers each a step smaller, a wide eave, then an iron spike and cross bar."""
        h = w / 2 + 2
        self.c("roofs", "spire_eave", (cx - h, y, cz - h), (cx + h, y + 1.5, cz + h), "eave")
        y += 1.5
        for i in range(tiers):
            s = w / 2 - i * step
            if s < 1.0:
                break
            self.c("roofs", "spire_tier", (cx - s, y, cz - s), (cx + s, y + tier_h, cz + s), "slate", hide=("down",))
            y += tier_h
        self.c("roofs", "finial", (cx - 0.5, y, cz - 0.5), (cx + 0.5, y + 6, cz + 0.5), "iron")
        self.c("roofs", "finial_bar", (cx - 1.5, y + 3.5, cz - 0.4), (cx + 1.5, y + 4.25, cz + 0.4), "iron")
        self.c("roofs", "finial_ball", (cx - 0.75, y + 5.5, cz - 0.75), (cx + 0.75, y + 6.75, cz + 0.75), "iron")
        return y + 6.75

    def corbels(self, x0, x1, z0, z1, y, every=4):
        """A corbel band: small blocks under a ledge that overhangs 1.5."""
        self.ring("towers", "corbel_ledge", x0, x1, z0, z1, y, y + 1.5, 1.5, "ledge")
        for side in ("n", "s", "e", "w"):
            if side in ("n", "s"):
                z = z0 - 1 if side == "n" else z1
                xx = x0 + 1
                while xx + 1.5 <= x1:
                    self.c("towers", "corbel", (xx, y - 2, z), (xx + 1.5, y, z + 1), "quoin")
                    xx += every
            else:
                x = x0 - 1 if side == "w" else x1
                zz = z0 + 1
                while zz + 1.5 <= z1:
                    self.c("towers", "corbel", (x, y - 2, zz), (x + 1, y, zz + 1.5), "quoin")
                    zz += every

    def crenels(self, x0, x1, z0, z1, y, h=3, merlon=3, gap=2):
        self.c("towers", "parapet", (x0 - 1.5, y, z0 - 1.5), (x1 + 1.5, y + 1.5, z1 + 1.5), "wall")
        for side in ("n", "s"):
            z = (z0 - 1.5, z0) if side == "n" else (z1, z1 + 1.5)
            xx = x0 - 1.5
            while xx + merlon <= x1 + 1.5:
                self.c("towers", "merlon", (xx, y + 1.5, z[0]), (xx + merlon, y + 1.5 + h, z[1]), "wall")
                xx += merlon + gap
        for side in ("w", "e"):
            x = (x0 - 1.5, x0) if side == "w" else (x1, x1 + 1.5)
            zz = z0
            while zz + merlon <= z1:
                self.c("towers", "merlon", (x[0], y + 1.5, zz), (x[1], y + 1.5 + h, zz + merlon), "wall")
                zz += merlon + gap

    # -- openings: frames proud of the wall round a darker recess (never painted flat)
    def window(self, face, along, y, w=8, h=12, at=0.0, lit=False, shutters=False, arched=False):
        """face: 'n','s','e','w'; along: x for n/s, z for e/w; at: the wall plane."""
        out = -1 if face in ("n", "w") else 1

        def box(a0, a1, y0, y1, d0, d1, mat, base="window"):
            if face in ("n", "s"):
                return self.c("openings", base, (a0, y0, at + out * d0 if out > 0 else at + out * d1),
                              (a1, y1, at + out * d1 if out > 0 else at + out * d0), mat)
            return self.c("openings", base, (at + out * d0 if out > 0 else at + out * d1, y0, a0),
                          (at + out * d1 if out > 0 else at + out * d0, y1, a1), mat)

        a0, a1 = along - w / 2, along + w / 2
        box(a0, a1, y, y + h, 0, 0.25, "lit" if lit else "glass", "window_glass" if not lit else "window_glass_glow")
        box(a0 - 1, a0, y, y + h, 0, 1, "frame", "window_frame")
        box(a1, a1 + 1, y, y + h, 0, 1, "frame", "window_frame")
        box(a0 - 1.5, a1 + 1.5, y - 1, y, 0, 1.5, "ledge", "window_sill")
        if arched:
            box(a0 - 1, a1 + 1, y + h, y + h + 1, 0, 1, "frame", "window_lintel")
            box(a0, a1, y + h + 1, y + h + 2, 0, 1, "frame", "window_arch")
            box(a0 + 1.5, a1 - 1.5, y + h + 2, y + h + 3, 0, 1, "frame", "window_arch_key")
        else:
            box(a0 - 1.5, a1 + 1.5, y + h, y + h + 1.5, 0, 1.25, "frame", "window_lintel")
        box(along - 0.5, along + 0.5, y, y + h, 0, 0.6, "frame", "window_mullion")
        box(a0, a1, y + h / 2 - 0.5, y + h / 2, 0, 0.6, "frame", "window_transom")
        if shutters:
            box(a0 - 4, a0 - 1, y, y + h, 0, 0.75, "plank", "shutter")
            box(a1 + 1, a1 + 4, y, y + h, 0, 0.75, "plank", "shutter")

    def door(self, face, along, y, at, w=16, h=28, steps=0, porch=False):
        out = -1 if face in ("n", "w") else 1

        def box(a0, a1, y0, y1, d0, d1, mat, base):
            lo, hi = (at + out * d0, at + out * d1) if out > 0 else (at + out * d1, at + out * d0)
            if face in ("n", "s"):
                return self.c("openings", base, (a0, y0, lo), (a1, y1, hi), mat)
            return self.c("openings", base, (lo, y0, a0), (hi, y1, a1), mat)

        a0, a1 = along - w / 2, along + w / 2
        box(a0, a1, y, y + h, 0, 0.25, "door", "door")
        box(a0 - 2, a0, y, y + h + 2, 0, 1.5, "frame", "door_frame")
        box(a1, a1 + 2, y, y + h + 2, 0, 1.5, "frame", "door_frame")
        box(a0 - 2, a1 + 2, y + h, y + h + 2, 0, 1.5, "frame", "door_lintel")
        box(a0 + 2, a1 - 2, y + h + 2, y + h + 3.5, 0, 1.5, "frame", "door_arch")
        box(along - 1.5, along + 1.5, y + h + 3.5, y + h + 5, 0, 1.75, "quoin", "keystone")
        for i, yy in enumerate((y + 6, y + h - 7)):
            box(a0 + 1, a1 - 1, yy, yy + 1, 0.25, 0.6, "iron", "door_bar")
        box(along + 3, along + 4, y + 13, y + 15, 0.25, 0.9, "iron", "door_ring")
        for i in range(steps):
            box(a0 - 3 - i * 1.5, a1 + 3 + i * 1.5, 0, y - i * 1.5, 1 + i * 3, 1 + (i + 1) * 3, "base", "step")
        if porch:
            box(a0 - 4, a1 + 4, y + h + 6, y + h + 7.5, 0, 6, "eave", "porch_roof")
            box(a0 - 3.5, a0 - 2, y, y + h + 6, 4.5, 6, "timber", "porch_post")
            box(a1 + 2, a1 + 3.5, y, y + h + 6, 4.5, 6, "timber", "porch_post")

    def chimney(self, x, z, y0, y1, w=5):
        self.c("details", "chimney", (x - w / 2, y0, z - w / 2), (x + w / 2, y1, z + w / 2), "wall")
        self.c("details", "chimney_band", (x - w / 2 - 0.5, y1 - 3, z - w / 2 - 0.5), (x + w / 2 + 0.5, y1 - 2, z + w / 2 + 0.5), "ledge")
        self.c("details", "chimney_cap", (x - w / 2 - 0.75, y1, z - w / 2 - 0.75), (x + w / 2 + 0.75, y1 + 1, z + w / 2 + 0.75), "ledge")
        self.c("details", "chimney_pot", (x - 1, y1 + 1, z - 1), (x + 1, y1 + 3, z + 1), "iron")

    def gable_roof(self, x0, x1, z0, z1, y, axis="x", step=2.0, tier_h=2.5, overhang=2.0, core="wall", crow=()):
        """A gabled slate roof of stepped tiers with its ridge along `axis`. Each tier is two slate strips
        (the slopes) and a core of `core` between them, so the gable ends read as a stepped wall flush
        with the wall below. crow: the ends ("start" = x0/z0, "end" = x1/z1) that get crow steps, a stepped
        gable wall standing proud above the slate with a coping ledge on each step."""
        U0, U1, V0, V1 = (x0, x1, z0, z1) if axis == "x" else (z0, z1, x0, x1)

        def cube(base, u0, u1, yy0, yy1, v0, v1, mat, group="roofs", **kw):
            if axis == "x":
                return self.c(group, base, (u0, yy0, v0), (u1, yy1, v1), mat, **kw)
            return self.c(group, base, (v0, yy0, u0), (v1, yy1, u1), mat, **kw)

        e0 = 0 if "start" in crow else 1.5
        e1 = 0 if "end" in crow else 1.5
        a, b = V0 - overhang, V1 + overhang
        cube("eave", U0 - e0, U1 + e1, y, y + 1.5, a, V0 + 0.5, "eave")
        cube("eave", U0 - e0, U1 + e1, y, y + 1.5, V1 - 0.5, b, "eave")
        y += 1.5
        while b - a > 2 * step + 1:
            a, b = a + step, b - step
            cube("roof_tier", U0 - e0, U1 + e1, y, y + tier_h, a, min(a + step + 0.5, (a + b) / 2), "slate", hide=("down",))
            cube("roof_tier", U0 - e0, U1 + e1, y, y + tier_h, max(b - step - 0.5, (a + b) / 2), b, "slate", hide=("down",))
            if b - a > 2 * step + 1:
                cube("gable", U0, U1, y, y + tier_h, a + step + 0.5, b - step - 0.5, core, hide=("down",))
            for end in crow:
                u0, u1 = (U0 - 1, U0 + 1.5) if end == "start" else (U1 - 1.5, U1 + 1)
                cube("crow_step", u0, u1, y, y + tier_h + 1, a + 0.5, b - 0.5, "wall", group="walls")
                cube("crow_coping", u0 - 0.5, u1 + 0.5, y + tier_h + 1, y + tier_h + 1.75, a, b, "ledge", group="walls")
            y += tier_h
        m = (a + b) / 2
        cube("ridge", U0 - e0, U1 + e1, y, y + 1.5, m - 1.5, m + 1.5, "slate", hide=("down",))
        cube("ridge_crest", U0 - e0 + 1, U1 + e1 - 1, y + 1.5, y + 2.25, m - 0.5, m + 0.5, "iron")
        return y + 2.25

    def dormer(self, face, along, y, at):
        """Stone dormer on the roof line: box, stepped little gable, window."""
        out = -1 if face == "n" else 1
        z0, z1 = sorted((at, at + out * 7))
        self.c("details", "dormer", (along - 5, y, z0), (along + 5, y + 10, z1), "wall")
        for i in range(3):
            self.c("details", "dormer_roof", (along - 6 + i * 2, y + 10 + i * 1.75, z0 - 0.75), (along + 6 - i * 2, y + 11.75 + i * 1.75, z1 + 0.75), "slate")
        self.window(face, along, y + 2, 5, 7, at=at + out * 7)

    def banner(self, face, along, y, at, w=6, h=14):
        out = -1 if face == "n" else 1
        z0, z1 = sorted((at, at + out * 0.5))
        self.c("details", "banner_rod", (along - w / 2 - 1, y + h, z0 - 0.25), (along + w / 2 + 1, y + h + 0.75, z1 + 0.25), "iron")
        self.c("details", "banner", (along - w / 2, y, z0), (along + w / 2, y + h, z1), "cloth")
        self.c("details", "banner_tip", (along - w / 2 + 1.5, y - 2, z0), (along + w / 2 - 1.5, y, z1), "cloth")

    def done(self, dummy=(0, 0, -40)):
        self.m.scale_dummy(dummy)
        return self.m


# ---------------------------------------------------------------- buildings

def cottage():
    b = B("cottage")
    x0, x1, z0, z1 = -20, 20, -14, 14
    top = 3 + 32
    b.block(x0, x1, z0, z1, 0, top, 1, mat="plaster")
    # half-timbering on the plaster: posts and a rail on every face
    for x in (-12, 12):
        b.c("walls", "timber_post", (x - 1, 3, z0 - 0.5), (x + 1, top - 1, z0), "timber")
        b.c("walls", "timber_post", (x - 1, 3, z1), (x + 1, top - 1, z1 + 0.5), "timber")
    b.c("walls", "timber_rail", (x0, 22, z0 - 0.5), (x1, 23.5, z0), "timber")
    b.c("walls", "timber_rail", (x0, 22, z1), (x1, 23.5, z1 + 0.5), "timber")
    b.door("n", 0, 3, z0, w=14, h=26, steps=1)
    b.window("n", -16, 9, 5, 10, at=z0, shutters=False)
    b.window("n", 16, 9, 5, 10, at=z0, shutters=False)
    b.c("details", "flower_box", (-19.5, 7, z0 - 2.5), (-12.5, 9, z0 - 0.5), "plank")
    b.c("details", "flowers", (-19, 9, z0 - 2.25), (-13, 10.5, z0 - 0.75), Mat("flowers", ramp("#5a0a1a", "#8a1428", "#c02040", "#e04a6a", "#f88aa0"), "fur", base=3))
    b.window("s", -8, 10, 8, 12, at=z1)
    b.window("s", 8, 10, 8, 12, at=z1)
    b.window("e", 0, 10, 8, 12, at=x1)
    b.window("w", 0, 10, 8, 12, at=x0)
    ry = b.hip_roof(x0, x1, z0, z1, top, step=2.25)
    b.chimney(12, 6, top, ry + 2)
    return b.done()


def smithy():
    b = B("smithy")
    x0, x1, z0, z1 = -24, 24, -18, 18
    top = 3 + 34
    b.block(x0, x1, z0, z1, 0, top, 1)
    b.door("n", -10, 3, z0, steps=1)
    b.window("n", 12, 10, 8, 12, at=z0)
    b.window("s", 0, 10, 8, 12, at=z1)
    b.window("w", 0, 10, 8, 12, at=x0)
    # open forge lean-to on the east side: timber posts, slate slope, glowing hearth
    lx = x1 + 16
    for z in (-12, 12):
        b.c("details", "leanto_post", (lx - 2, 0, z - 1), (lx, 26, z + 1), "timber")
    b.c("details", "leanto_beam", (x1, 25, -14), (lx + 1, 27, -12), "timber")
    b.c("details", "leanto_beam", (x1, 25, 12), (lx + 1, 27, 14), "timber")
    for i in range(4):
        b.c("roofs", "leanto_roof", (x1 + i * 4, 30 - i * 1.5, -15), (lx + 2, 31.5 - i * 1.5, 15), "slate" if i else "eave")
    b.c("details", "hearth", (x1 + 2, 0, -6), (x1 + 10, 8, 6), "base")
    b.c("details", "hearth_fire_glow", (x1 + 3, 8, -4), (x1 + 9, 9.5, 4), Mat("fire_glow", ramp("#7a1a06", "#c43e0a", "#ec7a16", "#f8b030", "#fce070", "#fff4c0"), "glow", base=3))
    b.c("details", "hood", (x1 + 1, 18, -7), (x1 + 11, 22, 7), "wall")
    ry = b.hip_roof(x0, x1, z0, z1, top, step=2.25)
    b.chimney(x1 - 6, 0, top, ry + 4, w=7)
    b.c("details", "sign_bracket", (x0 + 8, 30, z0 - 6), (x0 + 9, 31, z0), "iron")
    b.c("details", "sign_board", (x0 + 4, 22, z0 - 6), (x0 + 13, 29, z0 - 5.25), "sign",
        decal=lambda a, f, w, h, c, rng: _anvil_sign(a, f, w, h))
    return b.done()


def _anvil_sign(a, f, w, h):
    if f not in ("north", "south"):
        return
    ink = (40, 42, 48)
    cx, cy = w // 2, h // 2
    for x in range(cx - 5, cx + 5):
        put(a, x, cy - 2, ink)
        put(a, x, cy - 1, ink)
    for x in range(cx - 2, cx + 2):
        put(a, x, cy, ink)
        put(a, x, cy + 1, ink)
    for x in range(cx - 4, cx + 4):
        put(a, x, cy + 2, ink)
    put(a, cx + 5, cy - 2, ink)
    put(a, cx + 6, cy - 2, ink)


def general_store():
    b = B("general_store")
    x0, x1, z0, z1 = -26, 26, -20, 20
    top = 3 + 64
    sh = b.block(x0, x1, z0, z1, 0, top, 2)
    b.door("n", 0, 3, z0, steps=1, porch=True)
    for x in (-17, 17):
        b.window("n", x, 9, 10, 16, at=z0)
    for x in (-15, -5, 5, 15):
        b.window("n", x, 3 + sh + 6, 7, 13, at=z0, arched=True)
        b.window("s", x, 3 + sh + 6, 7, 13, at=z1, arched=True)
    for z in (-8, 8):
        b.window("e", z, 3 + sh + 6, 7, 13, at=x1)
        b.window("w", z, 3 + sh + 6, 7, 13, at=x0)
    b.window("s", 0, 9, 8, 14, at=z1)
    ry = b.hip_roof(x0, x1, z0, z1, top, step=2.0)
    b.dormer("n", -12, top + 4, z0 + 5)
    b.dormer("n", 12, top + 4, z0 + 5)
    b.chimney(-18, 10, top, ry + 3)
    # shop sign across the front and a striped awning on the right window
    b.c("details", "shop_sign", (-11, 3 + sh - 5, z0 - 1.25), (11, 3 + sh - 0.5, z0 - 0.5), "sign")
    aw = Mat("awning", ramp("#1a3a1a", "#24522a", "#2e6a36", "#3e8446", "#5aa05e"), "cloth", base=3, fold=3,
             bands=(ramp("#a89a80", "#c4b698", "#d8ccb0", "#e8dec6", "#f2ead6"), 6))
    for x in (-17, 17):
        b.c("details", "awning", (x - 7, 27, z0 - 6), (x + 7, 28, z0), aw, rotation=(-25, 0, 0), origin=(x, 28, z0))
    return b.done()


def tavern():
    b = B("tavern")
    x0, x1, z0, z1 = -30, 30, -22, 22
    top = 3 + 64
    sh = b.block(x0, x1, z0, z1, 0, top, 2)
    # upper storey jettied out in timber and plaster over the stone ground floor
    yj = 3 + sh
    b.c("walls", "jetty_beam", (x0 - 2, yj - 1, z0 - 2.5), (x1 + 2, yj + 1, z0 + 1), "timber")
    b.c("walls", "upper_front", (x0 - 1.5, yj + 1, z0 - 2), (x1 + 1.5, top - 1, z0), "plaster")
    for x in range(-28, 29, 8):
        b.c("walls", "timber_post", (x - 0.75, yj + 1, z0 - 2.5), (x + 0.75, top - 1, z0 - 2), "timber")
    b.c("walls", "timber_rail", (x0 - 1.5, yj + 14, z0 - 2.5), (x1 + 1.5, yj + 15, z0 - 2), "timber")
    b.door("n", 0, 3, z0, steps=2, porch=True)
    for x in (-20, -10, 10, 20):
        b.window("n", x, 9, 7, 14, at=z0, lit=True)
    for x in (-21, -7, 7, 21):
        b.window("n", x, yj + 5, 6, 10, at=z0 - 2, lit=x in (-7, 21))
    for x in (-15, 0, 15):
        b.window("s", x, 9, 7, 14, at=z1)
        b.window("s", x, yj + 5, 7, 12, at=z1)
    for z in (-8, 8):
        b.window("e", z, 9, 7, 14, at=x1, lit=True)
        b.window("w", z, yj + 5, 7, 12, at=x0)
    ry = b.hip_roof(x0, x1, z0 - 2, z1, top, step=2.0)
    for x in (-16, 0, 16):
        b.dormer("n", x, top + 4, z0 + 4)
    b.chimney(-22, 12, top, ry + 3)
    b.chimney(22, 12, top, ry + 1)
    # hanging sign: a mug on a board, on an iron bracket
    b.c("details", "sign_bracket", (x1 - 6, yj - 4, z0 - 10), (x1 - 5, yj - 3, z0 - 2), "iron")
    b.c("details", "sign_chain", (x1 - 6, yj - 7, z0 - 9), (x1 - 5, yj - 4, z0 - 8.5), "iron")
    b.c("details", "sign_board", (x1 - 10, yj - 16, z0 - 9.25), (x1 - 1, yj - 7, z0 - 8.25), "sign",
        decal=lambda a, f, w, h, c, rng: _mug_sign(a, f, w, h))
    for x in (-8.5, 8.5):
        b.c("details", "lantern", (x - 1.25, 20, z0 - 3), (x + 1.25, 23.5, z0 - 0.5), Mat("lamp_glow", WARMLIGHT, "glow", base=3))
        b.c("details", "lantern_cap", (x - 1.5, 23.5, z0 - 3.25), (x + 1.5, 24.25, z0 - 0.25), "iron")
    for i, (x, z) in enumerate(((-26, -27), (-22, -26.5))):
        b.c("details", "barrel", (x - 2.5, 0, z - 2.5), (x + 2.5, 7, z + 2.5), "plank")
        b.c("details", "barrel_hoop", (x - 2.75, 1.5, z - 2.75), (x + 2.75, 2.25, z + 2.75), "iron")
        b.c("details", "barrel_hoop", (x - 2.75, 5, z - 2.75), (x + 2.75, 5.75, z + 2.75), "iron")
    return b.done()


def _mug_sign(a, f, w, h):
    if f not in ("north", "south", "east", "west"):
        return
    gold, foam = (232, 176, 64), (240, 232, 214)
    cx, cy = w // 2 - 1, h // 2
    for y in range(cy - 3, cy + 4):
        for x in range(cx - 3, cx + 2):
            put(a, x, y, gold)
    for x in range(cx - 3, cx + 2):
        put(a, x, cy - 4, foam)
    for y in range(cy - 2, cy + 2):
        put(a, cx + 3, y, gold)
    put(a, cx + 2, cy - 2, gold)
    put(a, cx + 2, cy + 1, gold)


def watchtower():
    b = B("watchtower")
    x0, x1, z0, z1 = -12, 12, -12, 12
    top = 3 + 84
    sh = b.block(x0, x1, z0, z1, 0, top, 3)
    b.door("n", 0, 3, z0, w=12, h=24, steps=1)
    for i in range(1, 3):
        y = 3 + i * sh + 8
        for face, at in (("n", z0), ("s", z1)):
            b.window(face, 0, y, 4, 10, at=at, arched=True)
        for face, at in (("e", x1), ("w", x0)):
            b.window(face, 0, y, 4, 10, at=at, arched=True)
    b.corbels(x0, x1, z0, z1, top)
    b.crenels(x0, x1, z0, z1, top + 1.5)
    # the spire rises from inside the parapet, with a small turret spire at one corner
    b.c("towers", "spire_drum", (-8, top + 1.5, -8), (8, top + 8, 8), "wall")
    b.c("towers", "spire_drum_ledge", (-9, top + 8, -9), (9, top + 9, 9), "ledge")
    b.spire(0, 0, 18, top + 9, tiers=12, step=0.75)
    b.c("towers", "turret", (x1 - 2, top - 12, z0 - 2), (x1 + 4, top + 6, z0 + 4), "wall")
    b.c("towers", "turret_corbel", (x1 - 2.5, top - 14, z0 - 2.5), (x1 + 4.5, top - 12, z0 + 4.5), "ledge")
    b.spire(x1 + 1, z0 + 1, 6, top + 6, tiers=6, step=0.5)
    b.banner("s", 0, 9, z1 + 0.25, w=6, h=14)      # on the plain ground storey at the back, clear of the windows
    return b.done()


# ---------------------------------------------------------------- second set (2026-11-08)

HAY = Mat("hay", ramp("#5a4214", "#7a5a1c", "#9c7826", "#bc9634", "#d6b24a", "#ead070"), "fur", base=3)
CANVAS = Mat("sail_canvas", ramp("#6e6456", "#8a7f6e", "#a89c88", "#c2b6a0", "#d8ceb8", "#e8e0cc"), "cloth", base=4, fold=4)
GOLD = Mat("gilt", ramp("#4a3410", "#7a5818", "#a87c24", "#d0a238", "#ecc45a", "#f8e090"), "metal", base=3, bevel=True)


def _clock_face(a, f, w, h):
    if f != "north":
        return
    rim, tick, hand = (214, 166, 64), (60, 52, 44), (36, 34, 38)
    cx, cy, r = (w - 1) / 2, (h - 1) / 2, min(w, h) / 2 - 1.5
    for y in range(h):
        for x in range(w):
            d = ((x - cx) ** 2 + (y - cy) ** 2) ** 0.5
            if abs(d - r) < 0.75:
                put(a, x, y, rim)
    for x, y in ((cx, cy - r + 2), (cx, cy + r - 2), (cx - r + 2, cy), (cx + r - 2, cy)):
        put(a, round(x), round(y), tick)
    for i in range(int(r) - 2):        # hands at ten past two
        put(a, round(cx), round(cy - i), hand)
    for i in range(int(r * 0.6)):
        put(a, round(cx + i), round(cy - i * 0.5), hand)


def guild_hall():
    """The challenge hall (game_direction.md section 7): challenge givers and trophies. A two storey
    stone hall with a crow-stepped frontispiece over a grand stair, and a clock tower with a stepped spire."""
    b = B("guild_hall", split=True)
    x0, x1, z0, z1 = -44, 44, -22, 22
    top = 3 + 60
    sh = b.block(x0, x1, z0, z1, 0, top, 2)
    for x in (-36, -25, 25, 36):
        b.window("n", x, 9, 8, 16, at=z0, arched=True)
        b.window("n", x, 3 + sh + 6, 8, 16, at=z0, arched=True)
    for x in (-30, -10, 10, 30):
        b.window("s", x, 9, 8, 16, at=z1, arched=True)
    for face, at in (("e", x1), ("w", x0)):
        b.window(face, 0, 9, 8, 16, at=at, arched=True)
        b.window(face, 0, 3 + sh + 6, 8, 16, at=at, arched=True)
    # frontispiece: a projecting block over the stair, crow-stepped gable, one tall window
    fz = z0 - 8
    b.block(-13, 13, fz, z0 + 1, 0, top + 14, 2, quoins=False)
    b.door("n", 0, 6, fz, w=18, h=30, steps=4)
    b.window("n", 0, 3 + sh + 8, 10, 22, at=fz, arched=True)
    for x in (-9.5, 9.5):
        b.banner("n", x, 3 + sh + 6, fz - 0.25, w=5, h=18)
    b.gable_roof(-13, 13, fz, z0 + 1, top + 14, axis="z", step=2.0, tier_h=2.5, crow=("start",))
    b.hip_roof(x0, x1, z0, z1, top, step=2.5, tier_h=2.0)
    for x in (-30, 30):
        b.dormer("n", x, top + 3, z0 + 5)
    b.chimney(-34, 12, top, top + 22)
    b.chimney(34, 12, top, top + 22)
    # clock tower rising through the roof
    tz0, tz1 = -4, 16
    tt = top + 30
    b.block(-10, 10, tz0, tz1, top - 2, tt, 2, base_h=1.5, quoins=False)
    b.c("details", "clock_face", (-4.5, tt - 11, tz0 - 0.75), (4.5, tt - 2, tz0), GOLD.variant("clock", ramp=LIME, kind="stone", base=6, noise=0.0),
        decal=lambda a, f, w, h, c, rng: _clock_face(a, f, w, h))
    b.c("details", "clock_frame", (-5.5, tt - 12, tz0 - 0.5), (5.5, tt - 1, tz0), "frame")
    b.corbels(-10, 10, tz0, tz1, tt)
    b.crenels(-10, 10, tz0, tz1, tt + 1.5)
    b.c("towers", "spire_drum", (-7, tt + 1.5, tz0 + 3), (7, tt + 7, tz1 - 3), "wall")
    b.c("towers", "spire_drum_ledge", (-8, tt + 7, tz0 + 2), (8, tt + 8, tz1 - 2), "ledge")
    b.spire(0, (tz0 + tz1) / 2, 16, tt + 8, tiers=9, step=0.85)
    return b.done(dummy=(0, 0, -50))


def market_hall():
    """A covered market (game_worlds.md section 3.3, market stalls): an open stone arcade on the ground
    floor with stall counters under it, a jettied plaster storey above and a bell cupola on the ridge."""
    b = B("market_hall", split=True)
    x0, x1, z0, z1 = -36, 36, -18, 18
    fy, cy = 1.5, 28
    # smaller shared swatches than the default, so this wide, open building fits one 512 texture
    wall_s = M["wall"].variant("wall_small", swatch=(64, 64))
    plaster_s = M["plaster"].variant("plaster_small", swatch=(64, 72))
    b.c("foundation", "paving", (x0 - 2, 0, z0 - 2), (x1 + 2, fy, z1 + 2), "base")
    b.c("walls", "back_wall", (x0, fy, z1 - 3), (x1, cy, z1), wall_s)

    def pillar(x, z):
        b.c("walls", "pillar_base", (x - 2.75, fy, z - 2.75), (x + 2.75, fy + 2, z + 2.75), "base")
        b.c("walls", "pillar", (x - 2, fy + 2, z - 2), (x + 2, cy - 2, z + 2), "quoin")
        b.c("walls", "pillar_capital", (x - 2.75, cy - 2, z - 2.75), (x + 2.75, cy, z + 2.75), "ledge")

    xs = [-34, -22.5, -11.5, 0, 11.5, 22.5, 34]
    for x in xs:
        pillar(x, z0 + 2)
    for z in (-6, 6):
        pillar(x0 + 2, z)
        pillar(x1 - 2, z)
    # arches: two steps in each corner of every bay, front and sides
    for xa, xb in zip(xs, xs[1:]):
        b.c("walls", "arch", (xa + 2, cy - 3, z0 + 0.5), (xa + 4.5, cy, z0 + 3.5), "frame")
        b.c("walls", "arch", (xb - 4.5, cy - 3, z0 + 0.5), (xb - 2, cy, z0 + 3.5), "frame")
        b.c("walls", "arch", (xa + 4.5, cy - 1.5, z0 + 0.5), (xa + 6.5, cy, z0 + 3.5), "frame")
        b.c("walls", "arch", (xb - 6.5, cy - 1.5, z0 + 0.5), (xb - 4.5, cy, z0 + 3.5), "frame")
    for x in (x0 + 0.5, x1 - 3.5):
        for za, zb in ((z0 + 2, -6), (-6, 6), (6, z1 - 3)):
            b.c("walls", "arch", (x, cy - 3, za + 2), (x + 3, cy, za + 4.5), "frame")
            b.c("walls", "arch", (x, cy - 3, zb - 4.5), (x + 3, cy, zb - 2), "frame")
    b.c("walls", "ceiling", (x0, cy, z0), (x1, cy + 1.5, z1), "plank", hide=("up",))
    # upper storey, jettied out by 1, timber framed plaster
    uy = cy + 1.5
    top = uy + 26
    b.block(x0 - 1, x1 + 1, z0 - 1, z1 + 1, uy, top, 1, mat=plaster_s, base_h=2, quoins=False)
    for x in range(-33, 34, 11):
        for z, d in ((z0 - 1.5, z0 - 1), (z1 + 1, z1 + 1.5)):
            b.c("walls", "timber_post", (x - 0.75, uy + 2, z), (x + 0.75, top - 1, d), "timber")
    for z, d in ((z0 - 1.5, z0 - 1), (z1 + 1, z1 + 1.5)):
        b.c("walls", "timber_rail", (x0 - 1, uy + 14, z), (x1 + 1, uy + 15, d), "timber")
    for x in (-27.5, -5.5, 5.5, 27.5):
        b.window("n", x, uy + 6, 6, 10, at=z0 - 1.5, shutters=True)
        b.window("s", x, uy + 6, 6, 10, at=z1 + 1.5)
    for face, at in (("e", x1 + 1), ("w", x0 - 1)):
        b.window(face, 0, uy + 6, 6, 10, at=at)
    b.hip_roof(x0 - 1, x1 + 1, z0 - 1, z1 + 1, top, step=2.25)
    # bell cupola on the ridge
    ry = top + 1.5 + 2.5 * 8
    b.c("details", "cupola", (-4, ry - 6, -4), (4, ry + 4, 4), "timber")
    for x in (-4.5, 3.5):
        b.c("details", "cupola_post", (x, ry - 6, -4.5), (x + 1, ry + 4, 4.5), "frame")
    b.c("details", "bell", (-1.75, ry - 2, -4.25), (1.75, ry + 2, -3.75), GOLD)
    b.spire(0, 0, 10, ry + 4, tiers=5, step=1.0)
    # stalls under the arcade: counters with goods and crates
    goods = [Mat("apples", ramp("#4a0c0c", "#7a1614", "#a8241c", "#cc3a26", "#e86244"), "fur", base=3),
             Mat("cabbages", ramp("#1a3a12", "#2a5a1c", "#3e7a28", "#5a9a3a", "#80b85a"), "fur", base=3),
             Mat("loaves", ramp("#5a3410", "#7e4c1a", "#a06828", "#c08a3c", "#dcae5c"), "fur", base=3)]
    for (xa, xb), g in zip(((-30, -16), (-6, 6), (16, 30)), goods):
        b.c("details", "stall_counter", (xa, fy, z1 - 12), (xb, fy + 8, z1 - 7), "plank")
        b.c("details", "stall_top", (xa - 0.5, fy + 8, z1 - 12.5), (xb + 0.5, fy + 9, z1 - 6.5), "timber")
        b.c("details", "stall_goods", (xa + 1, fy + 9, z1 - 11.5), (xb - 1, fy + 11, z1 - 7.5), g)
        b.c("details", "crate", (xb - 4, fy, z1 - 6.5), (xb, fy + 4, z1 - 3), "plank")
    return b.done(dummy=(0, 0, -30))


def stable():
    """The stable (D-095, the stable menu): a stone ground floor with wide double doors and half doors,
    a timber framed hay loft under a gabled roof, a hoist beam on the gable, hay bales and a trough."""
    b = B("stable", split=True)
    x0, x1, z0, z1 = -36, 36, -18, 18
    gt = 3 + 30
    b.block(x0, x1, z0, z1, 0, gt, 1)
    top = gt + 16
    b.block(x0, x1, z0, z1, gt, top, 1, mat="plaster", base_h=1, quoins=False)
    for x in range(-32, 33, 8):
        for z, d in ((z0 - 0.5, z0), (z1, z1 + 0.5)):
            b.c("walls", "timber_post", (x - 0.75, gt + 1, z), (x + 0.75, top - 1, d), "timber")
    b.door("n", 0, 3, z0, w=24, h=24)
    b.c("openings", "door_split", (-0.5, 3, z0 - 0.6), (0.5, 27, z0 - 0.25), "timber")
    for cx in (-6, 6):
        for ang in (63.4, -63.4):
            b.c("openings", "door_brace", (cx - 12, 14.25, z0 - 0.7), (cx + 12, 15.75, z0 - 0.3), "timber",
                rotation=(0, 0, ang), origin=(cx, 15, z0 - 0.5))
    for x in (-24, 24):
        b.door("n", x, 3, z0, w=10, h=18)
        b.c("openings", "half_door_rail", (x - 5, 11, z0 - 0.7), (x + 5, 12, z0 - 0.3), "timber")
    for x in (-20, 20):
        b.window("n", x, gt + 4, 6, 8, at=z0 - 0.5, shutters=True)
    for x in (-22, 0, 22):
        b.window("s", x, 12, 6, 8, at=z1)
    b.window("w", 0, 12, 6, 8, at=x0)
    # hay loft door and hoist beam on the east gable
    b.door("e", 0, gt + 2, x1, w=12, h=12)
    b.c("details", "hoist_beam", (x1, top + 6, -1), (x1 + 9, top + 8, 1), "timber")
    b.c("details", "hoist_rope", (x1 + 7.5, top - 4, -0.25), (x1 + 8, top + 6, 0.25), "iron")
    b.c("details", "hoist_bale", (x1 + 5, top - 9, -2.5), (x1 + 10.5, top - 4, 2.5), HAY)
    b.gable_roof(x0, x1, z0, z1, top, axis="x", step=2.5, tier_h=2.5, core="plaster")
    ry = top + 1.5 + 2.5 * 7
    b.c("details", "vane_post", (-0.5, ry, -0.5), (0.5, ry + 9, 0.5), "iron")
    b.c("details", "vane_arrow", (-4, ry + 6, -0.25), (4, ry + 7, 0.25), "iron")
    b.c("details", "vane_tail", (-4.5, ry + 5, -0.3), (-2.5, ry + 8, 0.3), "iron")
    # hay bales stacked by the front left, a water trough on the right
    for (bx, by, bz) in ((-33, 0, -26), (-25, 0, -26), (-29, 5, -26)):
        b.c("details", "hay_bale", (bx - 4, by, bz - 3), (bx + 4, by + 5, bz + 3), HAY)
    b.c("details", "trough", (16, 0, -27), (30, 5, -22), "plank")
    b.c("details", "trough_water", (16.75, 4.25, -26.25), (29.25, 4.75, -22.75), "glass")
    return b.done(dummy=(0, 0, -34))


def gatehouse():
    """The village gate: two crenellated towers with stepped spires either side of an arched road
    passage, a half raised portcullis, banners over the arch. The road runs through (z)."""
    b = B("gatehouse", split=True)
    gx, gz = 16, 14
    gt = 3 + 52
    # piers and the span over the passage (the passage is open, front to back)
    for s in (-1, 1):       # base course on the piers only, so it doesn't make a kerb across the road
        xa, xb = sorted((s * (gx + 1), s * 11))
        b.c("foundation", "base_course", (xa, 0, -gz - 1), (xb, 3, gz + 1), "base")
    b.c("walls", "pier", (-gx, 3, -gz), (-11, gt, gz), "wall")
    b.c("walls", "pier", (11, 3, -gz), (gx, gt, gz), "wall")
    b.c("walls", "span", (-11, 34, -gz), (11, gt, gz), "wall", hide=("up",))
    b.c("walls", "parapet_floor", (-11, gt - 0.5, -gz), (11, gt, gz), "base")
    for s in (-1, 1):
        xa, xb = sorted((s * 11, s * 8))
        b.c("walls", "arch", (xa, 30, -gz), (xb, 34, gz), "frame")
        xa, xb = sorted((s * 8, s * 6))
        b.c("walls", "arch", (xa, 32.5, -gz), (xb, 34, gz), "frame")
    b.c("walls", "keystone", (-1.5, 33, -gz - 0.75), (1.5, 36, -gz), "quoin")
    b.c("walls", "keystone", (-1.5, 33, gz), (1.5, 36, gz + 0.75), "quoin")
    b.ring("walls", "string_course", -gx, gx, -gz, gz, 36, 37, 1, "ledge")
    b.ring("walls", "cornice", -gx, gx, -gz, gz, gt - 1, gt, 1.5, "ledge")
    b.crenels(-gx, gx, -gz, gz, gt)
    b.c("foundation", "road", (-11, 0, -24), (11, 0.5, 24), "base")
    for x in range(-9, 10, 3):
        b.c("openings", "portcullis_bar", (x - 0.5, 22, -gz + 1), (x + 0.5, 34, -gz + 2), "iron")
    for y in (24, 29):
        b.c("openings", "portcullis_rail", (-10.5, y, -gz + 0.75), (10.5, y + 1, -gz + 2.25), "iron")
    for x in range(-9, 10, 3):
        b.c("openings", "portcullis_spike", (x - 0.4, 20.5, -gz + 1.1), (x + 0.4, 22, -gz + 1.9), "iron")
    b.banner("n", 0, 39, -gz - 0.25, w=8, h=12)
    b.banner("s", 0, 39, gz + 0.25, w=8, h=12)
    # towers
    tt = 3 + 66
    for s in (-1, 1):
        x0, x1 = sorted((s * gx, s * 40))
        b.block(x0, x1, -16, 16, 0, tt, 3)
        cx = (x0 + x1) / 2
        b.window("n", cx, 26, 3, 9, at=-16, arched=True)
        b.window("n", cx, 47, 3, 9, at=-16, arched=True)
        b.window("e" if s > 0 else "w", 0, 36, 3, 9, at=x1 if s > 0 else x0, arched=True)
        b.corbels(x0, x1, -16, 16, tt)
        b.crenels(x0, x1, -16, 16, tt + 1.5)
        b.c("towers", "spire_drum", (cx - 8, tt + 1.5, -8), (cx + 8, tt + 7, 8), "wall")
        b.c("towers", "spire_drum_ledge", (cx - 9, tt + 7, -9), (cx + 9, tt + 8, 9), "ledge")
        b.spire(cx, 0, 18, tt + 8, tiers=11 if s > 0 else 10, step=0.8)
    return b.done(dummy=(0, 0, -28))


def townhouse():
    """A narrow three storey townhouse with crow-stepped gables front and back, a shop window under a
    striped awning, shuttered windows. Several can stand in a row along a street."""
    b = B("townhouse", split=True)
    x0, x1, z0, z1 = -15, 15, -14, 14
    top = 3 + 63
    sh = b.block(x0, x1, z0, z1, 0, top, 3)
    b.door("n", -7, 3, z0, w=12, h=24, steps=1)
    b.window("n", 7, 8, 9, 14, at=z0)
    aw = Mat("awning", ramp("#3a0c10", "#5c141a", "#801e24", "#a42c2c", "#c84a3c"), "cloth", base=3, fold=3,
             bands=(ramp("#a89a80", "#c4b698", "#d8ccb0", "#e8dec6", "#f2ead6"), 6))
    b.c("details", "awning", (1, 24, z0 - 6), (13, 25, z0), aw, rotation=(-25, 0, 0), origin=(7, 25, z0))
    for i in (1, 2):
        y = 3 + i * sh + 5
        for x in (-7, 7):
            b.window("n", x, y, 6, 11, at=z0, shutters=True)
            b.window("s", x, y, 6, 11, at=z1)
        b.window("e", 0, y, 6, 11, at=x1)
        b.window("w", 0, y, 6, 11, at=x0)
    b.window("s", 0, 9, 8, 12, at=z1)
    for x in (-7, 7):
        b.c("details", "flower_box", (x - 4.5, 3 + sh + 3, z0 - 2.5), (x + 4.5, 3 + sh + 5, z0 - 0.5), "plank")
        b.c("details", "flowers", (x - 4, 3 + sh + 5, z0 - 2.25), (x + 4, 3 + sh + 6.5, z0 - 0.75),
            Mat("flowers", ramp("#4a2a5a", "#6a3a8a", "#8a52b0", "#a874cc", "#c8a0e4"), "fur", base=3))
    ry = b.gable_roof(x0, x1, z0, z1, top, axis="z", step=2.0, tier_h=3.0, crow=("start", "end"))
    b.window("n", 0, top + 6, 4, 7, at=z0 - 1, arched=True)
    b.chimney(x1 - 4, 0, top, ry + 1, w=5)
    return b.done(dummy=(0, 0, -32))


def windmill():
    """A stone tower mill on the edge of the village: three tapering stages with ledges, a stepped cap,
    and four canvas sails on a hub facing the front."""
    b = B("windmill", split=True)
    b.block(-16, 16, -16, 16, 0, 3 + 30, 1)
    b.block(-13, 13, -13, 13, 33, 60, 1, base_h=1.5, quoins=False)
    b.block(-10, 10, -10, 10, 60, 82, 1, base_h=1.5, quoins=False)
    b.door("n", 0, 3, -16, w=12, h=22, steps=1)
    b.window("e", 0, 12, 6, 10, at=16)
    b.window("w", 0, 12, 6, 10, at=-16)
    b.window("n", 0, 42, 5, 9, at=-13, arched=True)
    for face, at in (("e", 13), ("w", -13), ("s", 13)):
        b.window(face, 0, 42, 5, 9, at=at, arched=True)
    b.window("s", 0, 66, 4, 8, at=10, arched=True)
    b.spire(0, 0, 22, 82, tiers=6, step=2.0, tier_h=2.5)
    # hub and sails
    hy, hz = 72, -10
    b.c("details", "axle", (-1.5, hy - 1.5, hz - 4), (1.5, hy + 1.5, hz), "timber")
    b.c("details", "hub", (-2.75, hy - 2.75, hz - 5.5), (2.75, hy + 2.75, hz - 3), "iron")
    for ang in (45, 135, 225, 315):
        r = dict(rotation=(0, 0, ang), origin=(0, hy, hz - 4.5))
        b.c("details", "sail_spar", (-1, hy + 2, hz - 5), (1, hy + 46, hz - 3.5), "timber", **r)
        b.c("details", "sail", (1, hy + 9, hz - 4.75), (8, hy + 45, hz - 4), CANVAS, **r)
        for k in (18, 30, 42):
            b.c("details", "sail_bar", (-1, hy + k, hz - 5.5), (8.5, hy + k + 1, hz - 4.5), "timber", **r)
    for x in (-11, -7):
        b.c("details", "flour_sack", (x - 2, 0, -21), (x + 2, 5, -18), CANVAS.variant("sack", fold=2))
    return b.done(dummy=(0, 0, -30))


BUILDINGS = {"cottage": cottage, "smithy": smithy, "general_store": general_store, "tavern": tavern,
             "watchtower": watchtower, "guild_hall": guild_hall, "market_hall": market_hall,
             "stable": stable, "gatehouse": gatehouse, "townhouse": townhouse, "windmill": windmill}
NEW = ["guild_hall", "market_hall", "stable", "gatehouse", "townhouse", "windmill"]


def main():
    names = sys.argv[1:] or list(BUILDINGS)
    paths = []
    for n in names:
        m = BUILDINGS[n]()
        p, cubes, size = m.save(OUT, TEX)
        paths.append(p)
        print(f"{Path(p).name}: {cubes} cubes, texture {size}")
    if len(names) == len(BUILDINGS):
        subprocess.run([sys.executable, str(HERE.parent / "make_lineup.py"), str(OUT / "buildings_lineup.bbmodel"), "100", "5", *paths], check=True)


if __name__ == "__main__":
    main()
