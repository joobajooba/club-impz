"""Sickles, swords and fishing rods, as siblings of build_pickaxes.py / build_axes.py (same painter, metal finish,
glow extras, animations and K scale, so all held items fit the Imp's fist and sit together as one set).

docs/blockbench_detailed_prompts.md 3.5 (tools: "rod, foraging tool ... same tier rules") and 3.6 (weapons: sword =
blade of 3 to 6 tapering cubes with fuller and tip, guard with curled ends at higher tiers, gem, wrapped grip, pommel).
- Sickles follow sprites/items/tool_<id>_sickle.png (10 metal tiers).
- Swords have no sprite: they use the same 10 metal tiers and colours as the other tools.
- Rods follow sprites/items/tool_<wood>_rod.png: 10 wood tiers (game_data.gd: driftwood, then the trees).
Usage: py build_more_tools.py [sickle|sword|rod ...]
"""
import colorsys, math, sys
import numpy as np
import build_pickaxes as bp
from build_pickaxes import Pick, TIERS, RAMPS, col, smooth, R_, K

# ---- extra ramps ---------------------------------------------------------------------------------------------
RAMPS.update({
    "leather":     R_("#22120a", "#3a1f12", "#52301c", "#6a4026", "#835232", "#9c6842", "#b88456"),
    "red_wrap":    R_("#2e0808", "#4c0e10", "#6e1818", "#902424", "#b03434", "#cc5048", "#e07a66"),
    "black_wrap":  R_("#0a090e", "#15131c", "#221e2a", "#302a3a", "#40384c", "#544a62"),
    "pale_wrap":   R_("#4a4060", "#6a5e86", "#8c80aa", "#ada2c8", "#cbc2e0", "#e4def2"),
    "bone":        R_("#4a3020", "#715a3e", "#94805f", "#b5a27e", "#cfc0a0", "#e3d8bc", "#f2ebd4"),
    "violet_wrap": R_("#1a0c2c", "#2c1648", "#422266", "#5a3286", "#7448a6", "#9466c4"),
    "white_wrap":  R_("#5a5878", "#7e7ca0", "#a4a4c4", "#c8cade", "#e2e6f2", "#f4f6fc"),
    "cork":        R_("#5e5240", "#7a6c56", "#988a72", "#b4a68c", "#ccbfa6", "#ded3bc", "#ece4d2"),
    "cork_dark":   R_("#1c1814", "#2a241e", "#3a322a", "#4a4036", "#5c5044"),
    "line":        R_("#8e8678", "#aaa294", "#c4bcae", "#dcd6c8", "#eeeae0"),
    "bobber_red":  R_("#3c0606", "#640c0c", "#8e1414", "#b42020", "#d23636", "#ea5c50", "#f68a78"),
    "bobber_white": R_("#6e6a66", "#96928c", "#bab6ae", "#d6d2ca", "#ebe8e2", "#f6f4f0"),
})


def make_ramp(hexcol, n=7):
    """A hue shifted ramp around one colour: darker shades deeper and more saturated, lighter ones warmer."""
    r, g, b = [int(hexcol[i:i + 2], 16) / 255 for i in (1, 3, 5)]
    h, s, v = colorsys.rgb_to_hsv(r, g, b)
    out = []
    for k in range(n):
        t = k / (n - 1) * 2 - 1                         # -1 dark .. +1 light
        vv = np.clip(v * (1 + .55 * t) if t > 0 else v * (1 + .72 * t), .06, .97)
        ss = np.clip(s * (1 + .25 * -t) if t < 0 else s * (1 - .35 * t), 0, 1)
        hh = (h + (-.02 * t if t > 0 else .015 * t)) % 1      # lights lean warm, darks lean cool
        rr, gg, bb = colorsys.hsv_to_rgb(hh, ss, vv)
        out.append([rr * 255, gg * 255, bb * 255])
    return np.array(out)

# grip wraps per metal tier (doc 3.5/3.6 tier table)
WRAP = {"stone": "rope", "bronze": "leather", "iron": "leather", "steel": "black_wrap", "gold": "red_wrap",
        "obsidian": "black_wrap", "titanite": "pale_wrap", "dreadstone": "bone", "void": "violet_wrap",
        "stellarite": "white_wrap"}


def glow_panels(tool, cubes, kind, glow, **extra):
    for body in cubes:
        for zsign, fname in ((1, "south"), (-1, "north")):
            z = zsign * (body["t"][2] + .05)
            tool.box("details", f"{kind}_{body['name']}_{'front' if zsign < 0 else 'back'}_glow", glow,
                     (body["f"][0], body["f"][1], z), (body["t"][0], body["t"][1], z), rot=body["rot"], origin=body["o"],
                     scaled=True, panel=kind, panel_face=fname, parent=body, **{k: body[k] for k in ("arm",) if k in body}, **extra)


def sparkles(tool, points):
    for k, (x, y) in enumerate(points, 1):
        tool.box(f"sparkle_{k}", f"sparkle_{k}_v_glow", "star_glow", (x - .125, y - .875, -.125), (x + .125, y + .875, .125),
                 share="spark_v", sparkle=True)
        tool.box(f"sparkle_{k}", f"sparkle_{k}_h_glow", "star_glow", (x - .875, y - .125, -.0625), (x + .875, y + .125, .0625),
                 share="spark_h", sparkle=True)


# =============================================================================================================
class Sickle(Pick):
    """A crescent blade rising from a short handle and curling over to a point, like the sprites."""
    grip_y = 3.5
    shine = 2.3

    def __init__(self, tid, cfg):
        super().__init__(tid, cfg)
        self.name = f"{tid}_sickle"
        self.rng = np.random.default_rng(sum(map(ord, tid)) * 151)

    def build(self):
        c = self.cfg; stone = c.get("chunky", False)
        wood, head = c["wood"], c["head"]
        self.box("handle", "handle", wood, (-.75, 1, -.75), (.75, 7.5, .75), wood_part="shaft")
        self.box("handle", "end_knob", c.get("bands") or wood, (-1, 0, -1), (1, 1.25, 1),
                 **({"band": True} if c.get("bands") else {"wood_part": "end"}))
        if stone:
            self.box("details", "ferrule", "rope", (-1, 7.25, -1), (1, 9.0, 1), rope=True)
        else:
            self.box("details", "ferrule", c["collar"], (-1, 7.25, -1), (1, 9.0, 1), socket=True)
        # the crescent: centre C, radius R, from the handle top clockwise over to a down-turned tip
        C, R = np.array([3.6, 11.25]), 4.25
        self.arc = (C, R)
        phis = [205, 182, 156, 128, 100, 72, 45, 20, 0]
        ws = [1.75, 1.75, 1.625, 1.5, 1.375, 1.25, 1.0, .75] if not stone else [2.25, 2.25, 2.0, 1.875, 1.75, 1.5, 1.25, 1.0]
        d0 = .75 if not stone else 1.0
        n = len(phis) - 1
        self.arms = []
        for i in range(n):
            p0 = C + R * np.array([math.cos(math.radians(phis[i])), math.sin(math.radians(phis[i]))])
            if i == 0:
                p0 = np.array([0.0, 8.6])                       # rooted inside the ferrule
            p1 = C + R * np.array([math.cos(math.radians(phis[i + 1])), math.sin(math.radians(phis[i + 1]))])
            d = max(.375, d0 - i * .05)
            cube = self.bar("head", f"blade_{i + 1}", head, p0, p1, ws[i], d, over=0 if i == n - 1 else .35,
                            arm=(1, i, n, ws[i]), inner_edge=True)
            self.arms.append(cube)
        if "emblem" in c and not stone:
            em_r, em = c["emblem"]
            self.box("emblem" if c.get("anim") else "details", "emblem_glow" if em_r.endswith("glow") else "emblem", em_r,
                     (-.5, 7.625, -1.25), (.5, 8.625, 1.25), emblem=em)
        if c.get("shard"):
            self.box("shard", "shard_glow", "void_glow", (3.125, 18.0, -.375), (3.875, 19.25, .375), rot=(0, 45, 0),
                     origin=(3.5, 18.6, 0))
        if c.get("sparkles"):
            sparkles(self, ((8.4, 9.6), (3.5, 17.6), (-1.6, 2.5)))
        glow = c.get("cracks") or c.get("core") or c.get("edges")
        if glow:
            kind = "crack" if c.get("cracks") else ("core" if c.get("core") else "edge")
            glow_panels(self, self.arms[1:-1], kind, glow)
        return self

    def extra_shade(self, c, face, W, h, w):
        if not c.get("inner_edge") or face not in ("north", "south"):
            return 0.0
        C, R = self.arc
        rho = (np.hypot(W[..., 0] - C[0], W[..., 1] - C[1]) - R) / (c["arm"][3] / 2)
        edge = 1.3 * smooth(-.45, -.9, rho)                                 # the cutting edge is the inner side
        if self.cfg["style"] != "chrome":
            return edge                                                     # stone stays plain flint
        streak = 2.2 * np.exp(-((rho - .3) / .14) ** 2)                     # a mirror band along the curve
        return 1.5 * edge + streak - .8 * np.exp(-((rho + .1) / .12) ** 2)

    def paint_panel(self, c, W, h, w):
        if c["panel"] != "edge":
            return super().paint_panel(c, W, h, w)
        C, R = self.arc
        rho = (np.hypot(W[..., 0] - C[0], W[..., 1] - C[1]) - R) / (c["arm"][3] / 2)
        m = rho < -.6                                     # glow along the inner, cutting edge
        a = np.where(m, 255, 0).astype(np.uint8)
        return self.rgba(col(c["mat"], 3.2 + (-.6 - rho) * 4), a)


# =============================================================================================================
SPIKY_GUARD = ("obsidian", "titanite", "dreadstone", "void", "stellarite")
GEMMED = ("gold", "obsidian", "titanite", "dreadstone", "void", "stellarite")


class Sword(Pick):
    grip_y = 3.25
    shine = 2.3

    def __init__(self, tid, cfg):
        super().__init__(tid, cfg)
        self.name = f"{tid}_sword"
        self.rng = np.random.default_rng(sum(map(ord, tid)) * 173)
        self.arc = (np.array([0.0, 0.0]), 1.0)

    def build(self):
        c = self.cfg; stone = c.get("chunky", False)
        head = c["head"]; wrap = WRAP[self.id]
        metal = c.get("collar") or "iron"
        # pommel and grip
        self.box("pommel", "pommel", metal if not stone else "flint", (-.875, 0, -.875), (.875, 1.25, .875), pommel=True, socket=not stone)
        self.box("pommel", "pommel_cap", c.get("pin", metal) if not stone else "flint", (-.5, -.25, -.5), (.5, 0, .5), pin=True)
        self.box("grip", "grip", wrap, (-.625, 1.25, -.625), (.625, 5.5, .625), wrap=True)
        self.box("grip", "grip_ring", metal if not stone else "rope", (-.75, 4.875, -.75), (.75, 5.5, .75),
                 **({"socket": True} if not stone else {"rope": True}))
        # guard
        gw = 3.5 if not stone else 2.75
        self.box("guard", "guard", metal if not stone else "rope", (-gw, 5.5, -.875), (gw, 6.75, .875),
                 **({"socket": True} if not stone else {"rope": True}))
        if self.id in SPIKY_GUARD:   # curled ends (doc: higher tiers)
            for s, sn in ((1, "right"), (-1, "left")):
                self.bar("guard", f"guard_curl_{sn}_1", metal, (s * (gw - .25), 6.25), (s * (gw + .75), 7.5), .875, 1.25, over=.2)
                self.bar("guard", f"guard_curl_{sn}_2", metal, (s * (gw + .7), 7.4), (s * (gw + .6), 8.6), .5, .875)
        # blade: tapering cubes, a fuller, then a two-cube point
        widths = [2.25, 2.125, 2.0, 1.75] if not stone else [2.75, 2.5, 2.25, 1.875]
        ys = [6.5, 11.0, 15.0, 18.5, 21.0]
        zt = .5 if not stone else .75
        self.blade = []
        for i in range(4):
            w = widths[i]
            cube = self.box("blade", f"blade_{i + 1}", head, (-w / 2, ys[i], -zt), (w / 2, ys[i + 1] + .25, zt),
                            blade=True, bw=w / 2, sword=True)
            self.blade.append(cube)
        tipw = widths[-1]
        # the point: a square turned 45 degrees, its top corner is the tip
        s = tipw / math.sqrt(2)
        self.box("blade", "blade_tip", head, (-s / 2, 21.0 - s / 2 + .2, -zt + .125), (s / 2, 21.0 + s / 2 + .2, zt - .125),
                 rot=(0, 0, 45), origin=(0, 21.2, 0), blade=True, bw=s / 2, sword=True)
        # gem / emblem in the guard
        if self.id in GEMMED or c.get("anim"):
            em_r, em = c["emblem"]
            self.box("emblem" if c.get("anim") else "guard", "emblem_glow" if em_r.endswith("glow") else "emblem", em_r,
                     (-.5, 5.625, -1.125), (.5, 6.625, 1.125), emblem=em)
        if c.get("shard"):
            self.box("shard", "shard_glow", "void_glow", (-.375, 23.0, -.375), (.375, 24.25, .375), rot=(0, 45, 0),
                     origin=(0, 23.6, 0))
        if c.get("sparkles"):
            sparkles(self, ((0.0, 23.2), (gw + 1.2, 9.2), (-(gw + 1.2), 9.2)))
        glow = c.get("cracks") or c.get("core") or c.get("edges")
        if glow:
            kind = "crack" if c.get("cracks") else ("core" if c.get("core") else "edge")
            glow_panels(self, self.blade, kind, glow)
        return self

    def extra_shade(self, c, face, W, h, w):
        if not c.get("sword") or face not in ("north", "south"):
            return 0.0
        X, Y = W[..., 0], W[..., 1]
        bw = c["bw"]
        out = .9 * smooth(6.5, 21, Y) - .45                           # darker at the guard, lighter toward the tip
        out = out + 1.1 * (np.abs(X) < .2) - .6 * ((np.abs(X) > .2) & (np.abs(X) < .45))   # light fuller, darker spine beside it
        out = out + 1.0 * smooth(bw - .45, bw - .1, np.abs(X))       # bright honed edges
        if self.cfg["style"] != "chrome":
            return out                                              # stone stays plain flint
        out = out + 2.2 * np.exp(-((X + .38 * bw) / .13) ** 2)      # a mirror streak down one bevel
        out = out - .9 * np.exp(-((X - .45 * bw) / .2) ** 2)        # and a dark reflection down the other
        out = out + .8 * smooth(bw - .3, bw - .05, np.abs(X))       # brighter honed edges
        return out

    def paint(self, c, face):
        if c.get("wrap") and face not in ("up", "down"):
            w, h = self.fsize(c, face)
            L, W, uu, vv = self.texels(c, face, w, h)
            W, L = W / K, L / K
            nx = uu * 2 - 1
            band = ((W[..., 1] * 2.2 + (L[..., 0] + L[..., 2]) * 1.6) % 1.0)   # diagonal wrap
            v = 3.0 - .9 * np.abs(nx) ** 2 + 1.0 * (band < .55) - .5 * (band > .85)
            v -= .5 * smooth(4.5, 5.5, W[..., 1]) + .5 * smooth(2.0, 1.25, W[..., 1])   # shadow under guard and above pommel
            a = np.full((h, w), 255, np.uint8)
            return self.rgba(col(c["mat"], v), a)
        return super().paint(c, face)

    def paint_panel(self, c, W, h, w):
        X, Y = W[..., 0], W[..., 1]
        bw = c["parent"]["bw"]; kind = c["panel"]
        if kind == "crack":
            path = .35 * np.sin(Y * 1.9) + .2 * np.sin(Y * 4.3)
            m = np.abs(X - path) < .17
            br = (np.abs(X - path - (Y % 3.0 - 1.5) * .6) < .14) & ((Y % 3.0) > 1.6)
            m |= br
            v = 4.6 - 6 * np.abs(X - path)
        elif kind == "core":           # rune line down the middle with notches
            m = (np.abs(X) < .16) | ((np.abs(X) < .45) & ((Y % 1.6) < .22))
            v = 4.4 - np.abs(X) * 5
        else:
            m = np.abs(X) > bw - .3
            v = 3.4 + (np.abs(X) - bw + .3) * 3
        a = np.where(m, 255, 0).astype(np.uint8)
        return self.rgba(col(c["mat"], v), a)


# =============================================================================================================
# rods: tier, wood id, rod-blank colour (game_data.gd _TREES / driftwood), accents
ROD_TIERS = [
    ("driftwood", "#8a7a62", "iron", None),
    ("ash", "#8a8478", "iron", None),
    ("birch", "#e4e4e4", "iron", None),
    ("oak", "#84543c", "iron", None),
    ("pine", "#543c24", "steel", None),
    ("goldleaf", "#9c6c24", "gold", None),
    ("ebony", "#2a2030", "steel", None),
    ("silverbark", "#d8d0f0", "titanite", None),
    ("bloodwood", "#5a1414", "dread", "ember"),
    ("voidwood", "#24183c", "void", "void_glow"),
]
ROD_CFG = {}
for wid, hexc, reel, glow in ROD_TIERS:
    RAMPS[f"{wid}_blank"] = make_ramp(hexc)
    ROD_CFG[wid] = dict(wood=f"{wid}_blank", reel=reel, glow=glow, style="chrome", head=reel, collar=reel)


RAMPS["thread"] = R_("#0a0a0c", "#141418", "#202026", "#2e2e36", "#40404a", "#565662")      # guide wraps


def _hash2(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h & 0xffff) / 65535.0


def vnoise(x, y, seed=0):
    """Smooth value noise, about one feature per unit of x and y."""
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash2(ix, iy, seed), _hash2(ix + 1, iy, seed)
    c_, d = _hash2(ix, iy + 1, seed), _hash2(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c_ * (1 - fx) + d * fx) * fy


def lerp_ramp(name, t):
    """A smooth (not banded) colour from a ramp, t from 0 (darkest) to 1 (lightest)."""
    r = RAMPS[name]
    v = np.clip(t, 0, 1) * (len(r) - 1)
    i = np.floor(v).astype(int); j = np.minimum(i + 1, len(r) - 1); f = (v - i)[..., None]
    return r[i] * (1 - f) + r[j] * f


class Rod(Pick):
    """Fishing rods in HD (J00BA, 2026-11-15): painted at 16 texels per unit on a 1/16 unit grid, with smooth
    (unbanded) shading. Every round part is two crossed boxes so it reads round: a rubber butt cap, a cork grip with
    ring seams, a reel seat with locking rings, a cork fore grip and winding check, a blank that tapers in 12 steps,
    thread wraps and ring guides, a round reel with side plates, a spool of line, crank and knob, and a round float."""
    PX_ = 16
    grip_y = 3.0
    LEAN = -35.0         # the rod leans forward like the sprite; the line hangs straight down

    def __init__(self, wid, cfg):
        super().__init__(wid, cfg)
        self.name = f"{wid}_rod"
        self.rng = np.random.default_rng(sum(map(ord, wid)) * 191)
        self.arc = (np.array([0.0, 0.0]), 1.0)

    def lean(self, group, name, mat, f, t, **kw):
        piv = (0.0, self.grip_y, 0.0)
        return self.box(group, name, mat, f, t, rot=(0, 0, self.LEAN), origin=piv, **kw)

    def round_y(self, group, name, mat, r, y0, y1, cx=0.0, cz=0.0, lean=True, **kw):
        """A round part along y: two crossed boxes, the second a hair shorter so their end caps never overlap."""
        put = self.lean if lean else self.box
        e = .1
        a = put(group, name, mat, (cx - r, y0, cz - r * .7), (cx + r, y1, cz + r * .7), axis="y", ctr=(cx, cz), rad=r, **kw)
        b = put(group, name + "_x", mat, (cx - r * .7, y0 + e, cz - r), (cx + r * .7, y1 - e, cz + r), axis="y", ctr=(cx, cz), rad=r, **kw)
        return a, b

    def round_x(self, group, name, mat, r, x0, x1, cy, cz, **kw):
        """A round disc or drum across x (the reel)."""
        e = .1
        self.lean(group, name, mat, (x0, cy - r, cz - r * .7), (x1, cy + r, cz + r * .7), axis="x", ctr=(cy, cz), rad=r, **kw)
        self.lean(group, name + "_x", mat, (x0 + e, cy - r * .7, cz - r), (x1 - e, cy + r * .7, cz + r), axis="x", ctr=(cy, cz), rad=r, **kw)

    def build(self):
        c = self.cfg; wood = c["wood"]; reel = c["reel"]
        # handle: rubber butt cap, cork grip, reel seat with locking rings, cork fore grip, winding check
        self.round_y("handle", "butt_cap", "cork_dark", .95, 0, .75, kind="cap")
        self.round_y("handle", "grip", "cork", .875, .75, 5.5, kind="cork")
        self.round_y("handle", "reel_seat", reel, .65, 5.5, 7.25, kind="metal")
        self.round_y("handle", "seat_ring_lo", reel, .78, 5.5, 5.875, kind="metal")
        self.round_y("handle", "seat_ring_hi", reel, .78, 6.875, 7.25, kind="metal")
        self.round_y("handle", "fore_grip", "cork", .7, 7.25, 8.25, kind="cork")
        self.round_y("handle", "fore_grip_taper", "cork", .6, 8.25, 9.0, kind="cork")
        self.round_y("handle", "winding_check", reel, .56, 9.0, 9.375, kind="metal")
        # the blank: 12 steps from 0.48 to 0.16 radius, so the taper reads smooth
        n = 12
        ys = np.linspace(9.25, 27.25, n + 1)
        for i in range(n):
            r = .48 - (.48 - .17) * i / (n - 1)
            self.round_y("handle", f"blank_{i + 1}", wood, r, ys[i], ys[i + 1] + .1, kind="wood")
        # line guides: a thread wrap on the blank and a ring standing under it, smaller toward the tip
        for k, y in enumerate((12.0, 17.0, 21.75, 25.5), 1):
            rb = .48 - (.48 - .17) * (y - 9.25) / 18.0
            s = 1 - .14 * (k - 1)
            self.round_y("details", f"guide_wrap_{k}", "thread", rb + .08, y - .35, y + .85, kind="wrap")
            self.lean("details", f"guide_foot_{k}", reel, (-.12, y, rb), (.12, y + .5, rb + .3), kind="metal")
            z0 = rb + .3; z1 = z0 + .75 * s; hw = .4 * s
            self.lean("details", f"guide_ring_{k}_a", reel, (-hw, y + .1, z0), (-hw + .12, y + .3, z1), kind="metal")
            self.lean("details", f"guide_ring_{k}_b", reel, (hw - .12, y + .1, z0), (hw, y + .3, z1), kind="metal")
            self.lean("details", f"guide_ring_{k}_c", reel, (-hw, y + .1, z1 - .12), (hw, y + .3, z1), kind="metal")
            self.lean("details", f"guide_ring_{k}_d", reel, (-hw, y + .1, z0), (hw, y + .3, z0 + .12), kind="metal")
        if c.get("glow"):
            self.round_y("handle", "tip_top_glow", c["glow"], .24, 27.25, 27.75, kind="glow")
        else:
            self.round_y("handle", "tip_top", reel, .24, 27.25, 27.75, kind="metal")
        # the reel hangs under the rod (+z side): a foot, two round side plates, a spool of line, crank and knob
        cy, cz = 6.375, 2.0
        self.lean("details", "reel_foot", reel, (-.3, 5.75, .5), (.3, 7.0, 1.0), kind="metal")
        self.lean("details", "reel_stem", reel, (-.2, 6.0, .9), (.2, 6.75, 1.1), kind="metal")
        self.round_x("details", "reel_plate_l", reel, 1.15, -.95, -.65, cy, cz, kind="metal")
        self.round_x("details", "reel_plate_r", reel, 1.15, .65, .95, cy, cz, kind="metal")
        self.round_x("details", "reel_spool", "line", .85, -.65, .65, cy, cz, kind="spool")
        self.round_x("details", "reel_hub", reel, .35, .95, 1.2, cy, cz, kind="metal")
        self.lean("details", "reel_crank", reel, (1.2, cy - .15, cz - .15), (1.45, cy + .15, cz + 1.0), kind="metal")
        self.round_x("details", "reel_knob", "cork_dark", .26, 1.45, 2.05, cy, cz + .95, kind="cap")
        # the line from the tip straight down to a round float
        a = math.radians(self.LEAN)
        tip = np.array([-math.sin(a) * (27.75 - self.grip_y), self.grip_y + math.cos(a) * (27.75 - self.grip_y)])
        self.group_origins = {"line": [round(tip[0] * K, 4), round(tip[1] * K, 4), 0.0]}
        x = tip[0]
        self.box("line", "line", "line", (x - .1, 10.75, -.1), (x + .1, tip[1], .1), kind="line")
        self.round_y("line", "float_bottom", "bobber_red", .75, 8.0, 9.6, cx=x, lean=False, kind="bobber")
        self.round_y("line", "float_band", "black_wrap", .66, 9.6, 9.85, cx=x, lean=False, kind="wrap")
        self.round_y("line", "float_top", "bobber_white", .62, 9.85, 10.6, cx=x, lean=False, kind="bobber")
        self.round_y("line", "float_stem", "bobber_red", .2, 10.6, 11.2, cx=x, lean=False, kind="bobber")
        return self

    def paint(self, c, face):
        w, h = self.fsize(c, face)
        L, W, uu, vv = self.texels(c, face, w, h)
        n = c["R"] @ np.array(bp.NORM[face], float)
        light = float(n @ bp.LIGHT)
        Ld = L / K                                                          # design units
        cx, cz = c["ctr"] if "ctr" in c else (0.0, 0.0)
        r = c.get("rad", .5)
        if c.get("axis") == "x":
            if face in ("north", "south"): a = (Ld[..., 1] - cx) / r
            elif face in ("up", "down"): a = (Ld[..., 2] - cz) / r
            else: a = np.hypot(Ld[..., 1] - cx, Ld[..., 2] - cz) / r
            along = Ld[..., 0]
        else:
            if face in ("east", "west"): a = (Ld[..., 2] - cz) / r
            elif face in ("north", "south"): a = (Ld[..., 0] - cx) / r
            else: a = np.hypot(Ld[..., 0] - cx, Ld[..., 2] - cz) / r
            along = Ld[..., 1]
        a = np.clip(a, -1, 1)
        roundv = np.sqrt(np.clip(1 - a * a, 0, 1))
        end = face in (("east", "west") if c.get("axis") == "x" else ("up", "down"))
        kind = c.get("kind", "metal")
        mat = c["mat"]
        t = .32 + .3 * roundv + .16 * light
        if end:
            t = .4 + .16 * light + .12 * (1 - np.abs(a))
        if kind == "wood":
            g = a * 3 + 1.2 * vnoise(a * 2, along * .35, 41)
            t = t + .1 * np.sin(g * 6.3) * (.5 + .5 * vnoise(a * 3, along * 1.2, 43)) - .1 * (vnoise(a * 18, along * 4, 47) > .8)
            t = t + .26 * np.exp(-((a + .35) / .14) ** 2) + .06 * np.exp(-((a - .5) / .2) ** 2)   # varnish shine
            t = t - .12 * np.clip((14 - along) / 5, 0, 1)                    # darker toward the grip
        elif kind == "cork":
            t = t + .12 * (vnoise(a * 6, along * 6, 51) - .5) - .1 * np.clip((vnoise(a * 12, along * 12, 53) - .62) * 5, 0, 1)   # soft cork pitting
            t = t - .2 * (np.abs((along % .55) - .275) > .25)                 # the seams between cork rings
        elif kind == "metal":
            t = t + .32 * np.exp(-((a + .3) / .16) ** 2) - .14 * np.exp(-((a - .25) / .1) ** 2) + .04 * (vnoise(a * 20, along * 3, 61) - .5)
            if end:
                t = t + .2 * (np.abs(a) > .75)
        elif kind == "wrap":
            t = t + .12 * (np.sin(along * 60) > 0) + .18 * np.exp(-((a + .3) / .2) ** 2)
        elif kind == "spool":
            t = .35 + .25 * roundv + .12 * light + .1 * np.sin(along * 40)          # turns of line
        elif kind == "bobber":
            t = t + .45 * np.exp(-((a + .35) / .2) ** 2) * (1 if not end else .3)
        elif kind == "glow":
            t = .75 + .25 * roundv
        elif kind == "cap":
            t = t + .1 * np.exp(-((a + .3) / .2) ** 2)
        elif kind == "line":
            t = .55 + .2 * light + 0 * a
        rgb = lerp_ramp(mat, t)
        return self.rgba(rgb, np.full((h, w), 255, np.uint8))


def run(kind, only=()):
    paths = []
    if kind == "rod":
        items = [(w, ROD_CFG[w]) for w, *_ in ROD_TIERS]
        cls = Rod
    else:
        items = list(TIERS.items())
        cls = Sickle if kind == "sickle" else Sword
    for tid, cfg in items:
        if only and tid not in only: continue
        r = cls(tid, cfg).build().write()
        paths.append(r.pop("path"))
        print(r)
    if not only:
        print("showcase", bp.showcase(paths, {"sickle": "sickles_showcase", "sword": "swords_showcase", "rod": "rods_showcase"}[kind]))


if __name__ == "__main__":
    kinds = [a for a in sys.argv[1:] if a in ("sickle", "sword", "rod")] or ["sickle", "sword", "rod"]
    only = [a for a in sys.argv[1:] if a not in ("sickle", "sword", "rod")]
    for k in kinds:
        run(k, only)
