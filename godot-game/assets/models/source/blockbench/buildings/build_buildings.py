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

Writes godot-game/assets/models/buildings/<id>.bbmodel (+ textures/buildings/) and
buildings_lineup.bbmodel.
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

    def __init__(self, name):
        self.m = Model(name, ppu=PPU, max_texture=512)
        self.root = self.m.group(name)
        self.g = {k: self.m.group(k, (0, 0, 0), self.root) for k in
                  ("foundation", "walls", "towers", "roofs", "openings", "details")}
        self.n = {}

    def name(self, base):
        self.n[base] = self.n.get(base, 0) + 1
        return f"{base}_{self.n[base]}"

    def c(self, group, base, frm, to, mat, **kw):
        return self.m.cube(self.name(base), frm, to, M[mat] if isinstance(mat, str) else mat, self.g[group], **kw)

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

    def done(self):
        self.m.scale_dummy((0, 0, -40))
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


BUILDINGS = {"cottage": cottage, "smithy": smithy, "general_store": general_store, "tavern": tavern,
             "watchtower": watchtower}


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
