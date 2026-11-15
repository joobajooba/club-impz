"""Builds the ten game pickaxes as Blockbench models, one per sprite in godot-game/sprites/pickaxes/.

docs/blockbench_detailed_prompts.md section 3.5 (Tools): 4 px/unit, stepped curved head of rotated cubes tapering
to points, square socket with an emblem, cap pin, carved handle, pivot at the grip. Colours are sampled from the
sprites (J00BA: "based upon the sprites"); the doc's tier extras are added where the sprite leaves room for them.

Ids follow the game (autoload/game_data.gd _METALS): titanite uses the mithril sprite, dreadstone the adamantite one.
Output: C:\\Users\\lucas\\blockbench_models\\tools\\<id>_pickaxe.bbmodel (+ .png) and pickaxes_showcase.bbmodel.
"""
import base64, json, math, os, sys, uuid
import numpy as np
from PIL import Image

sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
import fix_texture_bleed  # noqa: E402

OUT = r"C:\Users\lucas\blockbench_models\tools"
PX = 4
TS = 128

def hx(s): return [int(s[i:i + 2], 16) for i in (1, 3, 5)]
def R_(*a): return np.array([hx(c) for c in a], float)

# ---- ramps, dark -> light, sampled from the sprites and hue shifted (doc 1.5 rule 2) ----------------
RAMPS = {
    # woods
    "branch":    R_("#2a1d12", "#3f2c1c", "#534333", "#6a573e", "#7b674b", "#907e62", "#b39462"),
    "wood_mid":  R_("#24120c", "#3a2016", "#4f2e1d", "#604029", "#795331", "#8f6640", "#a87c50"),
    "wood_dark": R_("#180b06", "#26140a", "#341d0f", "#422513", "#56321b", "#643b21", "#7a4a2a"),
    "void_wood": R_("#140c20", "#1f1530", "#2b1d3b", "#382658", "#49355b", "#5e4867", "#786087"),
    "star_wood": R_("#16204a", "#25356a", "#3b5083", "#4c6893", "#557e9f", "#4f99d0", "#85b2c3"),
    # heads
    "flint":     R_("#1c1618", "#2a2526", "#3a3634", "#4d4a4c", "#5a5d69", "#7a7c82", "#9a9a9a", "#bdb7b3"),
    "rope":      R_("#2e1f10", "#4a3520", "#5d4f3e", "#7e6a48", "#907e62", "#b39462", "#d7bd84"),
    "bronze":    R_("#2e1006", "#4e2414", "#743a22", "#915237", "#b5603c", "#d27a4a", "#ec9966", "#f6c49a"),
    "brass":     R_("#3a1e0c", "#5c3414", "#82501e", "#a36d3f", "#c88e40", "#e2b060", "#f4d48c"),
    "iron":      R_("#18161e", "#262330", "#38343c", "#4d444c", "#5a5d69", "#7c899b", "#aea7b5", "#d6d2dc"),
    "steel":     R_("#0e0d18", "#1b1923", "#2a2e48", "#333a5b", "#424461", "#545a78", "#68749a", "#91aad5", "#c4d4ee"),
    "gold":      R_("#4a1e06", "#7a3410", "#ae5018", "#ce6825", "#e38a23", "#f19f26", "#f9d369", "#fdf0b4"),
    "obsidian":  R_("#06050c", "#0f0c18", "#1b1923", "#2b2332", "#382e43", "#483b50", "#684985", "#9a7cc2"),
    "titanite":  R_("#251c3a", "#3c2f5c", "#55467c", "#6b5690", "#8a6eb0", "#a68dcc", "#cec3e3", "#f1e6f8"),
    "dread":     R_("#140a0e", "#2a0e16", "#431420", "#5c2c35", "#762d35", "#98323e", "#b8504e", "#d47a6a"),
    "void":      R_("#0a0614", "#150e24", "#221634", "#2b1d3b", "#382658", "#49355b", "#5e4867", "#8a7aa6"),
    "stellar":   R_("#0c1230", "#18245a", "#22305e", "#3b5083", "#4c6893", "#557e9f", "#4f99d0", "#85b2c3", "#cdeef6", "#f4fbff"),
    # glows (doc 5: Void glow, Stellar glow; dreadstone ember)
    "ember":     R_("#4a0f04", "#8e2206", "#d0480a", "#ff8014", "#ffb83c", "#ffe68c", "#fff6cc"),
    "void_glow": R_("#2a0c4a", "#4a1878", "#7428b0", "#a448e0", "#d06cff", "#f0c8ff"),
    "star_glow": R_("#4a3c80", "#8070b0", "#c8b080", "#f0d890", "#fff6c8", "#fffbe6"),
}

# ---- tiers -------------------------------------------------------------------------------------------------
#  head: head ramp; collar: socket ramp; wood: handle ramp; style: how the head is painted
TIERS = {
    "stone":      dict(sprite="stone", head="flint", collar=None, wood="branch", style="flint", chunky=True, rope=True),
    "bronze":     dict(sprite="bronze", head="bronze", collar="bronze", wood="branch", style="chrome", bands="brass",
                       rivets="brass", emblem=("brass", "ring")),
    "iron":       dict(sprite="iron", head="iron", collar="iron", wood="wood_mid", style="chrome", finish="scratched", rivets="iron",
                       emblem=("iron", "anvil"), pin="iron"),
    "steel":      dict(sprite="steel", head="steel", collar="steel", wood="wood_mid", style="chrome", finish="scratched", rivets="steel",
                       emblem=("steel", "diamond"), pin="steel"),
    "gold":       dict(sprite="gold", head="gold", collar="gold", wood="wood_mid", style="chrome", engrave=True,
                       emblem=("gold", "crown"), pin="gold"),
    "obsidian":   dict(sprite="obsidian", head="obsidian", collar="obsidian", wood="wood_dark", style="chrome", finish="glass",
                       emblem=("obsidian", "facet"), pin="iron"),
    "titanite":   dict(sprite="mithril", head="titanite", collar="titanite", wood="wood_dark", style="chrome",
                       inlay=True, emblem=("titanite", "crystal"), pin="titanite"),
    "dreadstone": dict(sprite="adamantite", head="dread", collar="dread", wood="wood_dark", style="chrome", finish="jagged",
                       cracks="ember", emblem=("dread", "fang"), pin="dread"),
    "void":       dict(sprite="void", head="void", collar="void", wood="void_wood", style="chrome", metal_handle=True, core="void_glow",
                       shard=True, anim="void", emblem=("void_glow", "glow"), pin="void"),
    "stellarite": dict(sprite="stellarite", head="stellar", collar="stellar", wood="star_wood", style="chrome", metal_handle=True, anim="stellar", sparkles=True,
                       flecks=True, edges="star_glow", emblem=("star_glow", "star"), pin="stellar"),
}

def smooth(a, b, x):
    t = np.clip((x - a) / (b - a), 0, 1); return t * t * (3 - 2 * t)
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + .5) / 16 - .5
def bayer(h, w): return BAYER[np.ix_(np.arange(h) % 4, np.arange(w) % 4)]

def col(ramp, v):
    r = RAMPS[ramp]; h, w = v.shape
    q = np.clip(np.round((v + bayer(h, w) * .3) * 4) / 4, 0, len(r) - 1)       # quarter ramp steps, dithered
    i = np.floor(q).astype(int); j = np.minimum(i + 1, len(r) - 1); t = (q - i)[..., None]
    return r[i] * (1 - t) + r[j] * t

def rx(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def ry(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def rz(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])
def q4(x): return round(x * 4) / 4

NORM = dict(north=(0, 0, -1), south=(0, 0, 1), east=(1, 0, 0), west=(-1, 0, 0), up=(0, 1, 0), down=(0, -1, 0))
def corners(f, t, face):
    x1, y1, z1 = f; x2, y2, z2 = t
    return {"north": [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
            "south": [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
            "east":  [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
            "west":  [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
            "up":    [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
            "down":  [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)]}[face]

def blur(a, n=2):
    for _ in range(n):
        p = np.pad(a, 1, mode="edge")
        a = (p[1:-1, 1:-1] * 2 + p[:-2, 1:-1] + p[2:, 1:-1] + p[1:-1, :-2] + p[1:-1, 2:]) / 6
    return a

LIGHT = np.array((-.3, .88, .35)); LIGHT /= np.linalg.norm(LIGHT)   # from the top, slightly front left (doc 1.5 rule 4)
YH = 16.0          # top of the head's arc, on the handle line (design units)
# Built at K x the design: 12 units long (0.75 m at 16 units/m), about two thirds of the 1.15 m Imp, with a
# 1 unit (6 cm) handle that sits inside the Imp's fist (12 x 12 x 16 units at 101 units/1.15 m = 14 x 14 x 18 cm).
K = 0.64


class Pick:
    def __init__(self, tid, cfg):
        self.id, self.cfg = tid, cfg
        self.name = f"{tid}_pickaxe"
        self.cubes = []
        self.rng = np.random.default_rng(abs(hash(tid)) % 2**32 if False else sum(map(ord, tid)) * 97)

    # -- geometry helpers ----------------------------------------------------
    def box(self, group, name, mat, f, t, rot=(0, 0, 0), origin=None, scaled=False, **kw):
        f, t = np.array(f, float), np.array(t, float)
        o = np.array(origin if origin is not None else (f + t) / 2, float)
        if not scaled:                      # design units -> built size, sizes kept on the 1 px (0.25) grid
            cen = (f + t) / 2 * K
            size = np.maximum(np.round((t - f) * K * 4) / 4, .25)
            f, t, o = cen - size / 2, cen + size / 2, o * K
        self.cubes.append(dict(group=group, name=name, mat=mat, f=f, t=t, rot=rot, o=o,
                               R=rz(rot[2]) @ ry(rot[1]) @ rx(rot[0]), **kw))
        return self.cubes[-1]

    def bar(self, group, name, mat, p1, p2, w, d, over=0.0, zc=0.0, **kw):
        """A cube whose long (local y) axis runs p1 -> p2 in the xy plane."""
        p1, p2 = np.array(p1, float), np.array(p2, float); v = p2 - p1
        L = q4(np.hypot(*v) + 2 * over); c = (p1 + p2) / 2
        a = round(math.degrees(math.atan2(-v[0], v[1])), 1)
        return self.box(group, name, mat, (c[0] - w / 2, c[1] - L / 2, zc - d / 2), (c[0] + w / 2, c[1] + L / 2, zc + d / 2),
                        rot=(0, 0, a), origin=(c[0], c[1], zc), **kw)

    def inside_any(self, P, me):
        res = np.zeros(P.shape[:-1], bool)
        for o in self.cubes:
            if o is me or o.get("panel") or o is me.get("parent"): continue
            q = (P - o["o"]) @ o["R"] + o["o"]
            res |= np.all((q > o["f"] + 1e-3) & (q < o["t"] - 1e-3), axis=-1)
        return res

    # -- the model -------------------------------------------------------------
    def build(self):
        c = self.cfg
        chunky = c.get("chunky", False)
        wood, head = c["wood"], c["head"]
        # handle, grip on the pivot (doc: pivot at the grip point)
        self.box("handle", "handle", wood, (-.75, 1, -.75), (.75, 14.5, .75), wood_part="shaft")
        if c.get("bands"):
            self.box("handle", "end_cap", c["bands"], (-1, 0, -1), (1, 1.25, 1), band=True)
            self.box("handle", "handle_band", c["bands"], (-1, 8.25, -1), (1, 9.0, 1), band=True)
        else:
            self.box("handle", "end_knob", wood, (-.875, 0, -.875), (.875, 1, .875), wood_part="end")
        if chunky:   # a stub where a twig was cut off the branch (stone: "plain branch with bark")
            self.bar("handle", "twig_stub", wood, (.5, 9.0), (1.4, 9.9), .5, .5, wood_part="stub")

        # head: two arms of five stepped, rotated cubes on an arc, tapering to points
        R = 8.0 if chunky else 9.0
        thetas = [0, 11, 23, 34, 45, 55] if not chunky else [0, 12, 25, 37, 48]
        ws = [2.5, 2.25, 1.75, 1.25, .75] if not chunky else [3.25, 3.0, 2.5, 1.75]
        ds = [1.75, 1.5, 1.25, 1.0, .5] if not chunky else [2.25, 2.0, 1.75, 1.25]
        self.arc = (np.array([0.0, YH - R]), R)
        self.arms = []
        for side, sname in ((1, "right"), (-1, "left")):
            for i in range(len(thetas) - 1):
                a0, a1 = math.radians(thetas[i]), math.radians(thetas[i + 1])
                p0 = (side * R * math.sin(a0), YH - R * (1 - math.cos(a0)))
                p1 = (side * R * math.sin(a1), YH - R * (1 - math.cos(a1)))
                last = i == len(thetas) - 2
                cube = self.bar("head", f"head_{sname}_{i + 1}", head, p0, p1, ws[i] * .85 if (chunky and side < 0) else ws[i],
                                ds[i], over=0 if last else .45, arm=(side, i, len(thetas) - 1, ws[i]))
                self.arms.append(cube)
        if chunky:   # chipped lumps on the flint (rough edges)
            for side, sname in ((1, "right"), (-1, "left")):
                th = math.radians(20 if side > 0 else 30)
                p = np.array((side * (R + 1.2) * math.sin(th), YH - R + (R + 1.2) * math.cos(th)))
                self.bar("head", f"chip_{sname}", head, p - (side * .6, -.2), p + (side * .6, -.2), 1.0, 1.5,
                         arm=(side, 1, 4, 1.0), chip=True)
        # socket, emblem, rivets, cap pin
        if c.get("rope"):
            for k, y in enumerate((14.25, 16.75), 1):
                self.box("details", f"lashing_{k}", "rope", (-1.25, y, -1.375), (1.25, y + .75, 1.375), rope=True)
            self.bar("details", "lashing_cross_1", "rope", (-1.6, 13.9), (1.6, 17.9), .5, 2.75, rope=True)
            self.bar("details", "lashing_cross_2", "rope", (1.6, 13.9), (-1.6, 17.9), .5, 2.875, rope=True)
            self.box("details", "cap_pin", wood, (-.625, 17.5, -.625), (.625, 18.5, .625), wood_part="cap")
        else:
            col_r = c["collar"]
            self.box("details", "socket", col_r, (-1.5, 14.5, -1.25), (1.5, 17.5, 1.25), socket=True)
            em_r, em = c["emblem"]
            gl = em_r.endswith("glow")
            self.box("emblem" if c.get("anim") else "details", "emblem_glow" if gl else "emblem", em_r, (-.625, 15.375, -1.5), (.625, 16.625, 1.5),
                     emblem=em)
            if c.get("rivets"):
                for k, (x, y) in enumerate(((-1.0, 15.0), (1.0, 15.0), (-1.0, 17.0), (1.0, 17.0)), 1):
                    self.box("details", f"rivet_{k}", c["rivets"], (x - .25, y - .25, -1.5), (x + .25, y + .25, 1.5),
                             share="rivet", rivet=True)
            self.box("details", "cap_pin", wood, (-.625, 17.5, -.625), (.625, 18.25, .625), wood_part="cap")
            self.box("details", "cap_pin_head", c.get("pin", col_r), (-.5, 18.25, -.5), (.5, 18.75, .5), pin=True)
        if c.get("shard"):   # voidstone: a small shard floating over the cap pin (doc 3.5 tier extras)
            self.box("shard", "shard_glow", "void_glow", (-.375, 19.5, -.375), (.375, 20.75, .375), rot=(0, 45, 0),
                     origin=(0, 20.1, 0), glowpart=True)
        if c.get("sparkles"):   # stellarite: twinkling star sparkles at the tips and over the head (animated)
            for k, (x, y) in enumerate(((7.6, 11.7), (-7.6, 11.7), (0.0, 20.0)), 1):
                self.box(f"sparkle_{k}", f"sparkle_{k}_v_glow", "star_glow", (x - .125, y - .875, -.125), (x + .125, y + .875, .125),
                         share="spark_v", sparkle=True)
                self.box(f"sparkle_{k}", f"sparkle_{k}_h_glow", "star_glow", (x - .875, y - .125, -.0625), (x + .875, y + .125, .0625),
                         share="spark_h", sparkle=True)
        # glow panels: hard-alpha cards floating just off the arm faces (dreadstone cracks, void core, stellar edges)
        glow = c.get("cracks") or c.get("core") or c.get("edges")
        if glow:
            kind = "crack" if c.get("cracks") else ("core" if c.get("core") else "edge")
            for arm in list(self.arms):
                side, i, n, w = arm["arm"]
                if i == 0 or i == n - 1: continue
                for zsign, fname in ((1, "south"), (-1, "north")):
                    z = zsign * (arm["t"][2] + .05)
                    sn = "right" if side > 0 else "left"
                    self.box("details", f"{kind}_{sn}_{i + 1}_{'front' if zsign < 0 else 'back'}_glow", glow,
                             (arm["f"][0], arm["f"][1], z), (arm["t"][0], arm["t"][1], z), rot=arm["rot"], origin=arm["o"], scaled=True,
                             panel=kind, panel_face=fname, parent=arm, arm=arm["arm"])
        return self

    # -- painting ----------------------------------------------------------------
    def fsize(self, c, face):
        s = (c["t"] - c["f"]) * PX
        w, h = {"north": (s[0], s[1]), "south": (s[0], s[1]), "east": (s[2], s[1]), "west": (s[2], s[1]),
                "up": (s[0], s[2]), "down": (s[0], s[2])}[face]
        return int(round(w)), int(round(h))

    def texels(self, c, face, w, h):
        TL, TR, BR, BL = [np.array(p, float) for p in corners(c["f"], c["t"], face)]
        uu, vv = np.meshgrid((np.arange(w) + .5) / w, (np.arange(h) + .5) / h)
        L = TL + (TR - TL) * uu[..., None] + (BL - TL) * vv[..., None]
        W = (L - c["o"]) @ c["R"].T + c["o"]
        return L, W, uu, vv

    def noise(self, h, w, r):
        n = self.rng.normal(0, 1, (h + 8, w + 8))
        for _ in range(max(1, int(round(r * 2)))):
            n = (n + np.roll(n, 1, 0) + np.roll(n, -1, 0) + np.roll(n, 1, 1) + np.roll(n, -1, 1)) / 5
        n = n[4:4 + h, 4:4 + w]
        return (n - n.mean()) / (n.std() + 1e-6)

    def paint(self, c, face):
        """RGBA for one face."""
        w, h = self.fsize(c, face)
        L, W, uu, vv = self.texels(c, face, w, h)
        n = c["R"] @ np.array(NORM[face], float)
        light = float(n @ LIGHT)
        nx, ny = uu * 2 - 1, vv * 2 - 1
        edge = smooth(.3, 1.1, (np.abs(nx) ** 3 + np.abs(ny) ** 3) ** (1 / 3))
        aoi = np.zeros((h, w))
        for dd, wt in ((.12, .5), (.35, .3), (.7, .2)):
            aoi += wt * self.inside_any(W + n * dd, c)
        ao = blur(aoi, 3)
        W, L = W / K, L / K                                                   # patterns work in design units
        alpha = np.full((h, w), 255, np.uint8)
        mat = c["mat"]
        if c.get("panel"):
            return self.paint_panel(c, W, h, w)
        if mat in ("ember", "void_glow", "star_glow"):
            if c.get("emblem") == "star":
                d = np.abs(nx) ** .7 + np.abs(ny) ** .7
                v = 5.4 - 3.6 * np.clip(d - .25, 0, 2)
            else:
                d = np.maximum(np.abs(nx), np.abs(ny))
                v = len(RAMPS[mat]) - 1.4 - 2.6 * d ** 2
            return self.rgba(col(mat, v), alpha)
        if c.get("rope"):
            v = 3.2 + .9 * light + .5 * (1 - edge) - .7 * edge - 1.6 * ao
            s = (L[..., 0] + L[..., 1] + L[..., 2]) * 2.2                       # twisted strands
            v += .9 * (np.sin(s * math.pi) > .2) - .45
            return self.rgba(col("rope", v), alpha)
        if "wood_part" in c and self.cfg.get("metal_handle"):
            return self.rgba(self.paint_metal(c, face, W, L, w, h, light, edge, ao, nx, ny, n), alpha)
        if "wood_part" in c:
            return self.rgba(self.paint_wood(c, face, W, L, w, h, light, edge, ao, nx, ny), alpha)
        if c.get("band") and self.cfg["style"] == "chrome":
            return self.rgba(self.paint_chrome(c, face, W, w, h, ao, nx, ny, n), alpha)
        if c.get("band"):
            v = 3.0 + 1.0 * light + .7 * (1 - edge) - .8 * edge - 1.5 * ao + .3 * self.noise(h, w, 2)
            if abs(n[1]) < .5 and h >= 3: v[0] += .9                             # crisp lit top edge
            return self.rgba(col(mat, v), alpha)
        if c.get("rivet") or c.get("pin"):
            d = np.hypot(nx + .25, ny + .25)
            v = 3.0 + .8 * light + 1.6 * (1 - smooth(.1, .95, d)) - .6
            return self.rgba(col(mat, v), alpha)
        if c.get("emblem"):
            return self.rgba(self.paint_emblem(c, face, W, w, h, light, edge, nx, ny, n), alpha)
        return self.rgba(self.paint_metal(c, face, W, L, w, h, light, edge, ao, nx, ny, n), alpha)

    def rgba(self, rgb, a):
        return np.dstack([np.clip(np.round(rgb), 0, 255), a]).astype(np.uint8)

    def paint_wood(self, c, face, W, L, w, h, light, edge, ao, nx, ny):
        part = c["wood_part"]; r = c["mat"]
        v = 3.0 + .9 * light + .55 * (1 - edge) - .6 * edge - 1.8 * ao
        Y = W[..., 1]
        if part == "shaft":
            v -= .45 * smooth(9, 1, Y)                                      # darker toward the bottom (doc 1.5.1 pass 2)
            across = L[..., 0] + L[..., 2]
            grain = np.sin(across * 9.5 + np.sin(Y * 1.3 + across * 2) * 1.6)
            v += .5 * (grain > .55) - .35 * (grain < -.7)                    # long grain streaks
            if self.cfg.get("chunky"):                                       # bark strips on the branch
                v -= .8 * (np.sin(across * 6 + Y * .4) > .78)
            for y0 in (1.6, 8.0, 11.5):                                     # carved rings, clear of the grip
                v -= 1.1 * (np.abs(Y - y0) < .14) - .45 * (np.abs(Y - y0 - .28) < .14)
            yy, xx = np.mgrid[:h, :w]
            if h > 20 and w >= 4:                                            # a knot
                ky = int(h * (.38 + .1 * self.rng.random())); kx = w // 2
                d = np.hypot((xx - kx) * 1.2, (yy - ky) * .8)
                v -= 1.0 * np.exp(-d ** 2 / 3) - .4 * np.exp(-(d - 2.2) ** 2)
        elif part in ("end", "cap"):
            v += .3 * (1 - edge)
            if face in ("up", "down"):
                d = np.hypot(nx, ny); v -= .55 * (np.sin(d * 9) > .4)          # growth rings on the cut end
        else:
            v -= .3
        v += .2 * self.noise(h, w, 1.5)
        return col(r, v)

    def paint_metal(self, c, face, W, L, w, h, light, edge, ao, nx, ny, n):
        cfg = self.cfg; r = c["mat"]; top = len(RAMPS[r]) - 1
        style = cfg["style"]
        if style == "chrome":
            return self.paint_chrome(c, face, W, w, h, ao, nx, ny, n)
        base = top * .52
        if "arm" in c and face in ("north", "south", "up", "down"):
            C0, R0 = self.arc
            rad0 = np.hypot(W[..., 0] - C0[0], W[..., 1] - C0[1])
            side0, i0, n0, w0 = c["arm"]
            across = np.clip(np.abs(rad0 - R0) / (w0 / 2 + 1e-6), 0, 1) if face in ("north", "south") else np.abs(ny)
            edge = smooth(.45, 1.05, across)
            if i0 == n0 - 1:                                                     # only the tip darkens at its end
                edge = np.maximum(edge, smooth(.6, 1.0, np.abs(W[..., 0]) / (np.abs(W[..., 0]).max() + 1e-6)) * .5)
        v = base + 1.0 * light + .6 * (1 - edge) - .7 * edge - 1.9 * ao
        if "arm" in c:
            C, Rr = self.arc
            side, i, nseg, wseg = c["arm"]
            rad = np.hypot(W[..., 0] - C[0], W[..., 1] - C[1])
            rho = np.clip((rad - Rr) / (wseg / 2 + 1e-6), -1.2, 1.2)        # +1 outer (top) edge, -1 inner
            t = np.clip(np.abs(W[..., 0]) / 8.5, 0, 1)                      # 0 at the socket, 1 at the tips
            v += .9 * (t - .35)                                              # dark base -> light tip (doc 1.5.1 tools)
            v += .55 * rho                                                   # bevel: lit upper edge, darker underside
            if face in ("north", "south"):
                v += 1.0 * smooth(.55, .9, rho) * (style != "flint")         # crisp highlight along the top edge
                v -= .7 * smooth(-.6, -1.0, rho)
        elif c.get("socket"):
            v += .25
            if face in ("north", "south"):
                d = np.maximum(np.abs(nx), np.abs(ny))
                v += .55 * (d > .78) * (ny < 0) - .55 * (d > .78) * (ny > 0)   # raised rim: lit top, shaded bottom
        if style == "flint":
            v += .55 * self.noise(h, w, 1.2)                                 # mottled flint
            yy, xx = np.mgrid[:h, :w]
            for _ in range(max(1, w * h // 55)):                             # conchoidal chips: soft scallops
                x0, y0, rr = self.rng.uniform(0, w), self.rng.uniform(0, h), self.rng.uniform(1.5, 3)
                d = np.hypot(xx - x0, yy - y0)
                v += .6 * np.exp(-(d / rr) ** 2) - .5 * np.exp(-((d - rr) / .7) ** 2)
            v = v + self.extra_shade(c, face, W, h, w)
            rgb = col(r, v)
            # warm sandy stains like the sprite's brown flecks
            m = (self.noise(h, w, 2.5) > 1.1)
            return np.where(m[..., None], col("rope", v * .8 - .2), rgb)
        # metals ------------------------------------------------------------
        v += .22 * self.noise(h, w, 3)
        yy, xx = np.mgrid[:h, :w]
        nsc = w * h // (60 if style in ("metal", "jagged") else 140)
        for _ in range(nsc):                                                 # scratches, following the shading
            x, y = self.rng.uniform(0, w), self.rng.uniform(0, h); a = self.rng.uniform(-.6, .6) + (math.pi / 2 if w < h else 0)
            for s in range(int(self.rng.integers(3, 7))):
                ix, iy = int(x + s * math.cos(a)), int(y + s * math.sin(a))
                if 0 <= ix < w and 0 <= iy < h: v[iy, ix] += .5
        if style == "shiny":                                                 # broad soft sheen band
            band = np.sin((L[..., 0] - L[..., 1]) * .9 + .4)
            v += .7 * smooth(.6, .95, band)
        if style == "glass":                                                 # faceted volcanic glass: hard-edged bright facets
            f1 = ((L[..., 0] * .8 + L[..., 1] * 1.3 + L[..., 2] * .5) % 2.6) < .35
            v += 1.6 * f1 * (light > -.2)
            v -= .3
        if style == "crystal" or cfg.get("inlay"):                           # crystal inlays: pale veins
            vv = np.abs(np.sin(L[..., 0] * 1.7 + np.sin(L[..., 1] * 2.1) * 1.4))
            v += 1.2 * (vv < .09)
        if style == "jagged":                                                # dark red-black, pitted
            v -= .4 * smooth(.8, 1.6, self.noise(h, w, 1.5))
        if cfg.get("engrave") and face in ("north", "south") and "arm" in c:  # gold: engraved line along the arm
            C, Rr = self.arc
            rad = np.hypot(W[..., 0] - C[0], W[..., 1] - C[1])
            line = np.abs(rad - Rr - .15) < .14
            v -= 1.3 * line
        v = np.minimum(v, top + .2)
        rgb = col(r, v)
        if cfg.get("flecks") and "arm" in c:                                 # star flecks like the sprite
            m = self.noise(h, w, .6) > 2.0
            rgb = np.where(m[..., None], col("star_glow", np.full((h, w), 4.0)), rgb)
        return rgb

    def extra_shade(self, c, face, W, h, w):
        """Tool-specific shading added on top of the metal (sickle edges, sword fullers). 0 for pickaxes."""
        return 0.0

    def paint_chrome(self, c, face, W, w, h, ao, nx, ny, n):
        """Polished metal: a studio reflection baked per texel from a domed pseudo-normal (build scripts/metal.py)."""
        r = c["mat"]
        top = len(RAMPS[r]) - 1
        TL, TR, BR, BL = [np.array(p, float) for p in corners(c["f"], c["t"], face)]
        U = c["R"] @ (TR - TL); U /= np.linalg.norm(U) + 1e-9
        V = c["R"] @ (BL - TL); V /= np.linalg.norm(V) + 1e-9
        if (c.get("sword") or c.get("inner_edge")) and face in ("north", "south"):
            ny = ny * 0                                                     # one long blade, not a stack of domes
        N = n + .62 * (nx[..., None] * U + ny[..., None] * V)
        if "arm" in c and face in ("north", "south"):                      # the arm's bevel tilts its normal outward
            C, Rr = self.arc
            dv = W[..., :2] - C; rad = np.linalg.norm(dv, axis=-1)
            rho = np.clip((rad - Rr) / (c["arm"][3] / 2 + 1e-6), -1, 1)
            N[..., :2] += .5 * rho[..., None] * dv / (rad[..., None] + 1e-6)
        N = N / np.linalg.norm(N, axis=-1, keepdims=True)
        x = N[..., 0]; y = N[..., 1] - .55 * x * x; hz = -.3
        sky = [.22, .38, .32, .06, .20, .46, .54, .66, .78, .88]
        tt = np.interp(y, [-1.6, -1.1, hz - .16, hz - .04, hz, hz + .05, .05, .3, .55, 1], sky)
        tt = tt + .17 * np.exp(-((x + .40) / .09) ** 2) - .10 * np.exp(-((x - .36) / .12) ** 2) - .34 * np.clip(np.abs(x) - .42, 0, 1)
        L_KEY = np.array([-.38, .62, .69]); L_KEY /= np.linalg.norm(L_KEY)
        hh = np.clip(N @ L_KEY, 0, 1)
        tt = tt + .17 * hh ** 9 + .42 * hh ** 60
        s = getattr(self, "shine", 1.0)                                     # >1: more mirror-like (swords, sickles)
        if s != 1.0:
            tt = .5 + (tt - .5) * s                                         # brighter sky, deeper horizon band
            tt = tt + (s - 1) * (.35 * hh ** 24 + .5 * hh ** 120)           # a bigger, hotter specular spot
            tt = np.clip(tt, -.05, 1.08)
        if "wood_part" in c: tt = tt * .82                                  # the handle is a little darker than the head
        v = tt * top * 1.05 - 1.4 * ao + .12 * self.noise(h, w, 2)
        if c.get("edge_bit"):                                               # a sharpened edge catches more light
            v += 1.1
        fin = self.cfg.get("finish")
        X, Y, Z = W[..., 0], W[..., 1], W[..., 2]
        if fin == "glass":                                                  # obsidian: hard bright facet lines
            v += 1.5 * ((((X * .8 + Y * 1.3 + Z * .5) % 2.6) < .3) & (tt > .3))
        if fin == "jagged":                                                 # dreadstone: dark pits
            v -= .9 * smooth(1.0, 1.8, self.noise(h, w, 1.5))
        if fin == "scratched":                                              # iron, steel: a few bright scratches
            for _ in range(w * h // 90):
                x0, y0 = self.rng.uniform(0, w), self.rng.uniform(0, h); a = self.rng.uniform(-.6, .6) + (math.pi / 2 if w < h else 0)
                for s in range(int(self.rng.integers(3, 7))):
                    ix, iy = int(x0 + s * math.cos(a)), int(y0 + s * math.sin(a))
                    if 0 <= ix < w and 0 <= iy < h: v[iy, ix] += .7
        if self.cfg.get("inlay") and ("arm" in c or c.get("blade")):                            # titanite: pale crystal veins
            vv = np.abs(np.sin(X * 1.7 + np.sin(Y * 2.1) * 1.4))
            v += 1.6 * (vv < .09)
        if self.cfg.get("engrave") and "arm" in c and face in ("north", "south"):   # gold: engraved line
            C, Rr = self.arc
            v -= 1.6 * (np.abs(np.hypot(X - C[0], Y - C[1]) - Rr - .15) < .16)
        v = v + self.extra_shade(c, face, W, h, w)
        rgb = col(r, np.clip(v, 0, top))
        if self.cfg.get("flecks") and ("arm" in c or c.get("socket") or c.get("blade")):      # star flecks like the sprite
            m = self.noise(h, w, .6) > 2.0
            rgb = np.where(m[..., None], col("star_glow", np.full((h, w), 4.0)), rgb)
        return rgb

    def paint_emblem(self, c, face, W, w, h, light, edge, nx, ny, n):
        r = c["mat"]; top = len(RAMPS[r]) - 1; em = c["emblem"]
        v = top * .55 + .8 * light + .5 * (1 - edge) - .6 * edge
        if face in ("north", "south"):
            ax, ay = np.abs(nx), np.abs(ny)
            if em == "ring":
                d = np.hypot(nx, ny); v += 1.4 * (np.abs(d - .55) < .2) - .8 * (d < .3)
            elif em == "anvil":
                shape = ((ny < -.1) & (ay < .45) & (ax < .8)) | ((ny >= -.1) & (ax < .3)) | ((ny > .5) & (ax < .65))
                v += 1.3 * shape - .7
            elif em in ("diamond", "facet", "crystal"):
                dia = ax + ay
                v += 1.5 * (dia < .7) - .8 + .8 * (dia < .35) * (nx < 0)
            elif em == "crown":
                spikes = (ny > .2) | ((ny > -.6) & ((np.abs(nx * 3) % 2) < .6))
                v += 1.4 * (spikes & (ax < .85)) - .7
            elif em == "fang":
                v += 1.3 * ((ay < .8) & (ax < .55 * (1 - ny) / 1.8)) - .7
        return col(r, v)

    def paint_panel(self, c, W, h, w):
        """Hard-alpha glow pattern for a floating panel over an arm face."""
        C, Rr = self.arc
        side, i, nseg, wseg = c["arm"]
        rad = np.hypot(W[..., 0] - C[0], W[..., 1] - C[1])
        rho = (rad - Rr) / (wseg / 2)
        X = np.abs(W[..., 0])
        kind = c["panel"]
        if kind == "crack":           # zig-zag crack running along the arm
            path = .1 * np.sin(X * 3.1 + i) + .25 * np.sin(X * 1.3 + side)
            m = np.abs(rho - path) < .2
            br = (np.abs(rho - path - .35 * np.sin(X * 7)) < .14) & (np.sin(X * 2.3 + i * 2) > .55)
            m |= br
            v = 4.6 - 2.5 * np.abs(rho - path) * 3
        elif kind == "core":          # a glowing seam down the middle of the arm
            m = np.abs(rho) < .2
            v = 4.4 - np.abs(rho) * 6
        else:                         # a glowing edge along the arm's top
            m = rho > .62
            v = 3.2 + (rho - .62) * 4
        rgb = col(c["mat"], v)
        a = np.where(m, 255, 0).astype(np.uint8)
        return self.rgba(rgb, a)

    # -- file --------------------------------------------------------------------------------------------
    def write(self):
        faces = []
        for c in self.cubes:
            c["faces"] = {}
            for face in NORM:
                w, h = self.fsize(c, face)
                if c.get("panel"):
                    if face != c["panel_face"]:
                        c["faces"][face] = None; continue
                    if w == 0 or h == 0: c["faces"][face] = None; continue
                elif w == 0 or h == 0:
                    c["faces"][face] = None; continue
                L, W, *_ = self.texels(c, face, w, h)
                n = c["R"] @ np.array(NORM[face], float)
                if not c.get("panel") and self.inside_any(W + n * .02, c).all():
                    c["faces"][face] = None; continue
                key = (c["share"], face) if "share" in c else (c["name"], face)
                faces.append((c, face, key, w, h))
        order = {}
        for c, face, key, w, h in faces: order.setdefault(key, (w, h, c, face))
        items = sorted(order.items(), key=lambda kv: (-kv[1][1], -kv[1][0]))
        size = TS
        while True:
            rects = {}; x = y = 1; rowh = 0; ok = True
            for key, (w, h, c, face) in items:
                if x + w + 1 > size: x = 1; y += rowh + 1; rowh = 0
                rects[key] = (x, y, w, h); x += w + 1; rowh = max(rowh, h)
            if y + rowh + 1 <= size: break
            size *= 2
        tex = np.zeros((size, size, 4), np.uint8)
        for key, (w, h, c, face) in items:
            x0, y0, _, _ = rects[key]
            tex[y0:y0 + h, x0:x0 + w] = self.paint(c, face)
        for c, face, key, w, h in faces:
            x0, y0, *_ = rects[key]
            c["faces"][face] = [x0, y0, x0 + w, y0 + h]
        self.tex = tex
        os.makedirs(OUT, exist_ok=True)
        png = os.path.join(OUT, self.name + ".png"); Image.fromarray(tex, "RGBA").save(png)
        b64 = base64.b64encode(open(png, "rb").read()).decode()
        GRIP = [0.0, getattr(self, "grip_y", 4.5) * K, 0.0]                    # the middle of the fist
        ORIG = {"handle": GRIP, "head": [0.0, (YH - 1) * K, 0.0], "details": [0.0, 16.0 * K, 0.0]}
        ORIG.update(getattr(self, "group_origins", {}))                   # pivots a tool asks for (the rod's line)
        for cc in self.cubes:                                              # animated parts: pivot at their centre
            if cc["group"] not in ORIG:
                mine = [k for k in self.cubes if k["group"] == cc["group"]]
                ORIG[cc["group"]] = (sum((k["f"] + k["t"]) / 2 for k in mine) / len(mine)).round(4).tolist()
        U = lambda: str(uuid.uuid4())
        elements = []; gch = {g: [] for g in ORIG}
        for c in self.cubes:
            u = U(); gch[c["group"]].append(u); fd = {}
            for face in ("north", "east", "south", "west", "up", "down"):
                r = c["faces"].get(face)
                fd[face] = {"uv": r, "texture": 0} if r else {"uv": [0, 0, 0, 0], "texture": None}
            e = {"name": c["name"], "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
                 "allow_mirror_modeling": True, "from": c["f"].tolist(), "to": c["t"].tolist(), "autouv": 0, "color": 0,
                 "origin": c["o"].tolist(), "faces": fd, "type": "cube", "uuid": u}
            if c.get("panel"): e["render_order"] = "in_front"
            if any(c["rot"]): e["rotation"] = list(c["rot"])
            elements.append(e)
        def grp(name, origin, children):
            u = U()
            return ({"name": name, "uuid": u, "export": True, "locked": False, "scope": 0, "selected": False, "visibility": True,
                     "origin": origin, "rotation": [0, 0, 0], "color": 0, "children": [], "reset": False, "shade": True,
                     "mirror_uv": False, "autouv": 0, "isOpen": True, "primary_selected": False},
                    {"uuid": u, "isOpen": True, "children": children})
        groups = []; kids = []
        guid = {}
        for g in ORIG:
            a, b = grp(g, ORIG[g], gch[g]); groups.append(a); kids.append(b); guid[g] = a["uuid"]
        anims = self.animations(guid)
        ra, rb = grp(self.name, GRIP, kids); groups.insert(0, ra)
        model = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": self.name,
                 "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
                 "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
                 "resolution": {"width": size, "height": size}, "elements": elements, "groups": groups, "outliner": [rb],
                 "textures": [{"name": self.name + ".png", "folder": "", "namespace": "", "id": "0",
                               "group": "", "scope": 0, "width": size, "height": size, "uv_width": size, "uv_height": size,
                               "particle": False, "use_as_default": False, "layers_enabled": False, "sync_to_project": "",
                               "file_format": "png", "render_mode": "default", "render_sides": "auto", "wrap_mode": "limited",
                               "pbr_channel": "color", "fps": 7, "force_translucent": False, "frame_time": 1,
                               "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False, "visible": True,
                               "internal": True, "saved": True, "uuid": U(), "source": "data:image/png;base64," + b64}],
                 "animations": anims}
        path = os.path.join(OUT, self.name + ".bbmodel")
        json.dump(model, open(path, "w"), indent="	")
        fix_texture_bleed.pad_file(path, extra_pngs=[png])
        # checks
        t2 = np.array(Image.open(png).convert("RGBA"))
        ops = t2[t2[..., 3] > 0][:, :3]
        allp = np.concatenate([np.array([(np.array(p) - c["o"]) @ c["R"].T + c["o"] for f in NORM for p in corners(c["f"], c["t"], f)])
                               for c in self.cubes])
        return dict(name=self.name, cubes=len(self.cubes), colours=len(np.unique(ops, axis=0)), tex=t2.shape[0],
                    black_white=int(((ops == 0).all(1) | (ops == 255).all(1)).sum()),
                    lo=allp.min(0).round(2).tolist(), hi=allp.max(0).round(2).tolist(), path=path)


def _kf(channel, time, xyz, interp="linear"):
    return {"channel": channel, "data_points": [{"x": str(xyz[0]), "y": str(xyz[1]), "z": str(xyz[2])}],
            "uuid": str(uuid.uuid4()), "time": round(time, 4), "color": -1, "interpolation": interp}


def _anim(name, length, animators):
    return {"uuid": str(uuid.uuid4()), "name": name, "loop": "loop", "override": False, "length": length, "snapping": 24,
            "selected": False, "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
            "animators": animators}


def _animations(self, guid):
    kind = self.cfg.get("anim")
    if kind == "void":     # 2 s loop: the shard bobs and spins, the emblem pulses
        A = {guid["shard"]: {"name": "shard", "type": "bone", "keyframes": [
                 _kf("position", 0, (0, 0, 0), "catmullrom"), _kf("position", 1, (0, .5, 0), "catmullrom"),
                 _kf("position", 2, (0, 0, 0), "catmullrom"),
                 _kf("rotation", 0, (0, 0, 0)), _kf("rotation", 2, (0, 360, 0))]},
             guid["emblem"]: {"name": "emblem", "type": "bone", "keyframes": [
                 _kf("scale", 0, (1, 1, 1), "catmullrom"), _kf("scale", 1, (1.18, 1.18, 1), "catmullrom"),
                 _kf("scale", 2, (1, 1, 1), "catmullrom")]}}
        return [_anim("idle", 2, A)]
    if kind == "stellar":  # 3 s loop: the star emblem turns a quarter and pulses; three sparkles twinkle in turn
        A = {guid["emblem"]: {"name": "emblem", "type": "bone", "keyframes": [
                 _kf("rotation", 0, (0, 0, 0)), _kf("rotation", 3, (0, 0, 90)),
                 _kf("scale", 0, (1, 1, 1), "catmullrom"), _kf("scale", 1.5, (1.2, 1.2, 1), "catmullrom"),
                 _kf("scale", 3, (1, 1, 1), "catmullrom")]}}
        for k in (1, 2, 3):
            o = (k - 1) * 1.0
            keys = [_kf("scale", 0, (.01, .01, .01))]
            if o > 0: keys.append(_kf("scale", o, (.01, .01, .01)))
            keys += [_kf("scale", o + .3, (1, 1, 1)), _kf("scale", o + .6, (.01, .01, .01))]
            if o + .6 < 3: keys.append(_kf("scale", 3, (.01, .01, .01)))
            keys += [_kf("rotation", o, (0, 0, 0)), _kf("rotation", o + .6, (0, 0, 45))]
            A[guid[f"sparkle_{k}"]] = {"name": f"sparkle_{k}", "type": "bone", "keyframes": keys}
        return [_anim("idle", 3, A)]
    return []


Pick.animations = _animations


def showcase(paths, name="pickaxes_showcase"):
    """All ten side by side, stone to stellarite, each with its own texture."""
    U = lambda: str(uuid.uuid4())
    elements, groups, outliner, textures, anims = [], [], [], [], []
    for k, p in enumerate(paths):
        d = json.load(open(p))
        dx = (k - (len(paths) - 1) / 2) * 20
        t = dict(d["textures"][0]); t["uuid"] = U(); t["id"] = str(k); textures.append(t)
        old = {}
        for e in d["elements"]:
            e = json.loads(json.dumps(e)); nu = U(); old[e["uuid"]] = nu; e["uuid"] = nu
            e["from"][0] += dx; e["to"][0] += dx; e["origin"][0] += dx
            for f in e["faces"].values():
                if f.get("texture") is not None: f["texture"] = k
            elements.append(e)
        gmap = {}
        for g in d["groups"]:
            g = dict(g); nu = U(); gmap[g["uuid"]] = nu; g["uuid"] = nu; g["origin"] = [g["origin"][0] + dx] + g["origin"][1:]
            groups.append(g)
        def walk(n):
            return {"uuid": gmap[n["uuid"]], "isOpen": False,
                    "children": [old[c] if isinstance(c, str) else walk(c) for c in n["children"]]}
        outliner += [walk(n) for n in d["outliner"]]
        for an in d.get("animations", []):
            an = json.loads(json.dumps(an)); an["uuid"] = U(); an["name"] = d["name"].replace("_pickaxe", "").replace("_axe", "") + "_" + an["name"]
            an["animators"] = {gmap[k]: v for k, v in an["animators"].items()}
            anims.append(an)
    size = max(t["width"] for t in textures)
    model = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": name,
             "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "", "variable_placeholder_buttons": [],
             "timeline_setups": [], "unhandled_root_fields": {}, "resolution": {"width": size, "height": size},
             "elements": elements, "groups": groups, "outliner": outliner, "textures": textures, "animations": anims}
    path = os.path.join(OUT, name + ".bbmodel")
    json.dump(model, open(path, "w"), indent="	")
    return path


if __name__ == "__main__":
    only = sys.argv[1:]
    paths = []
    for tid, cfg in TIERS.items():
        if only and tid not in only: continue
        r = Pick(tid, cfg).build().write()
        paths.append(r.pop("path"))
        print(r)
    if not only:
        print("showcase", showcase(paths))
