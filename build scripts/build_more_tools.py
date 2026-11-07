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


class Rod(Pick):
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

    def build(self):
        c = self.cfg; wood = c["wood"]; reel = c["reel"]
        self.lean("handle", "butt_cap", "cork_dark", (-.875, 0, -.875), (.875, .75, .875), cap=True)
        self.lean("handle", "grip", "cork", (-.875, .75, -.875), (.875, 5.5, .875), cork=True)
        self.lean("handle", "reel_seat", reel, (-.625, 5.5, -.625), (.625, 7.25, .625), socket=True)
        self.lean("handle", "fore_grip", "cork", (-.625, 7.25, -.625), (.625, 9.0, .625), cork=True)
        # reel hangs under the rod (+z side)
        self.lean("details", "reel_foot", reel, (-.25, 5.75, .5), (.25, 7.0, 1.0), socket=True)
        self.lean("details", "reel_body", reel, (-.875, 5.25, 1.0), (.875, 7.5, 2.75), socket=True)
        self.lean("details", "reel_spool", "line", (-1.0, 5.75, 1.375), (1.0, 7.0, 2.375), cork=True)
        self.lean("details", "reel_crank", reel, (.875, 6.125, 1.625), (1.875, 6.625, 2.125), socket=True)
        self.lean("details", "reel_knob", "cork_dark", (1.625, 6.625, 1.625), (2.125, 7.375, 2.125), cap=True)
        # the blank, tapering
        segs = [(9.0, 14.25, 1.0), (14.0, 19.25, .875), (19.0, 23.75, .75), (23.5, 27.25, .5)]
        for i, (y0, y1, w) in enumerate(segs, 1):
            self.lean("handle", f"blank_{i}", wood, (-w / 2, y0, -w / 2), (w / 2, y1, w / 2), wood_part="shaft")
        self.lean("handle", "tip_top_glow" if c.get("glow") else "tip_top", c.get("glow") or reel,
                  (-.375, 27.25, -.375), (.375, 27.75, .375), **({} if c.get("glow") else {"socket": True}))
        for k, y in enumerate((12.0, 17.0, 21.75, 25.5), 1):     # line guides under the blank
            self.lean("details", f"guide_{k}", reel, (-.25, y, .375), (.25, y + .5, 1.0), share="guide", socket=True)
        # line from the tip straight down to the float
        a = math.radians(self.LEAN)
        tip = np.array([-math.sin(a) * (27.75 - self.grip_y), self.grip_y + math.cos(a) * (27.75 - self.grip_y)])
        self.group_origins = {"line": [round(tip[0] * K, 4), round(tip[1] * K, 4), 0.0]}   # the line hangs from the tip
        x = tip[0]
        self.box("line", "line", "line", (x - .125, 10.5, -.125), (x + .125, tip[1], .125), cork=True)
        self.box("line", "float_bottom", "bobber_red", (x - .75, 8.0, -.75), (x + .75, 9.5, .75), bobber=True)
        self.box("line", "float_top", "bobber_white", (x - .625, 9.5, -.625), (x + .625, 10.5, .625), bobber=True)
        self.box("line", "float_stem", "bobber_red", (x - .25, 10.5, -.25), (x + .25, 11.0, .25), bobber=True)
        return self

    def paint(self, c, face):
        w, h = self.fsize(c, face)
        if c.get("cork") or c.get("cap") or c.get("bobber"):
            L, W, uu, vv = self.texels(c, face, w, h)
            n = c["R"] @ np.array(bp.NORM[face], float)
            light = float(n @ bp.LIGHT)
            nx, ny = uu * 2 - 1, vv * 2 - 1
            edge = smooth(.3, 1.1, (np.abs(nx) ** 3 + np.abs(ny) ** 3) ** (1 / 3))
            top = len(RAMPS[c["mat"]]) - 1
            v = top * .55 + .9 * light + .6 * (1 - edge) - .7 * edge
            if c.get("cork"):
                v += .5 * self.noise(h, w, .8)                         # cork pitting
            if c.get("bobber"):
                v += 1.0 * np.exp(-((nx + .35) ** 2 + (ny + .35) ** 2) / .12)   # glossy highlight
            a = np.full((h, w), 255, np.uint8)
            return self.rgba(col(c["mat"], v), a)
        return super().paint(c, face)


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
