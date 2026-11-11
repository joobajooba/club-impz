"""Crafting stations (MODELS-BLOCKBENCH.md section 2: furnace, anvil, drying rack, tanning rack, sawbench, workbench;
02-resources.md: brewing cauldron). Built on stall_lib / house_lib. Adds painters for bark, log ends, hides, water,
coal and embers, flames, saw blades, rope and leather bellows."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from stall_lib import Stall, StallPainter, stall_mats, R, C, F, px, h2, LO, CAT, grid, BLOOMS
from foliage_lib import ramp

R.update({
    "fire_brick": ramp("#2a1410 #44201a #5e2e24 #7a3e2e #96503a #ae684a #c28460"),
    "coal": ramp("#0e0c0e #1a171a #262226 #343036 #454048 #5a5460 #726c78"),
    "steel": ramp("#1a1e24 #2c323a #444c56 #606a76 #848e9a #b0b8c2 #dfe4ea"),
    "copper": ramp("#3a1608 #5c240e #843818 #ac5224 #cc7036 #e2924e #f2b674"),
    "bark": ramp("#24140e #3a2216 #52321e #6c4428 #885834 #a67244 #bc8a58"),
    "hide": ramp("#3e2412 #5a361c #784a28 #966036 #b07a48 #c8965e #dcb47e"),
    "leather": ramp("#2a160e #422416 #5c3420 #78462a #965c36 #ae7446 #c48e5a"),
    "water": ramp("#0c1e2a #12303e #1a4454 #245a6a #347482 #4e909c #74b0b8"),
    "tan_liquor": ramp("#1e0e06 #2e180a #42240e #583214 #70421c #8a5626 #a26c34"),
    "sawdust": ramp("#6a4e2a #8a6a3a #a8864c #c2a060 #d6b878 #e6ce96 #f0e0b4"),
    "rope": ramp("#3e2e18 #5a4424 #765c32 #927642 #ac9056 #c4aa70 #d8c48e"),
    "nettle": ramp("#14280c #1e3c12 #2a5218 #3a6a20 #4e862c #68a03c #88ba54"),
    "bluebell": ramp("#141c4a #1e2a6c #2c3c90 #3e52b0 #566ccc #7a8ee0 #a4b2ee"),
    "frostbloom": ramp("#2a4256 #3e5c74 #567a92 #7298ae #92b6c8 #b6d2de #dcecf2"),
    "sunpetal": ramp("#5a4206 #866208 #b08812 #d4ac20 #ecca3e #f8e070 #fcf0a8"),
})


class StationPainter(StallPainter):
    def bark(self, Rm, w, h, cat):
        """Bark: vertical plates split by dark grooves that wander, lighter ridges, a little moss low down."""
        yy, xx = grid(w, h)
        if cat in ("up", "down"):
            return self.ring_end(w, h, cat)
        ph = self.nr.uniform(0, 6)
        g = np.sin(xx * 1.3 + np.sin(yy * 0.35 + ph) * 1.4 + ph)
        v = 3.1 + LO[cat] + g * 0.6 - (g < -0.6) * 1.2 - np.abs((xx + .5) / w - .5) * 1.0
        v += 0.2 * np.sin(yy * 1.7 + xx) + self.noise(w, h, 0.15) + self.vfall(h, 0.75, 0.6)
        rgb = C(Rm, v)
        mm = self.moss_mask(w, h, True, 0.2); rgb[mm] = C(R["moss"], 3.0 + LO[cat] + self.noise(w, h, 0.4, 8))[mm]
        return rgb, np.ones((h, w), bool)

    def ring_end(self, w, h, cat="up"):
        """Cut wood: growth rings round an off-centre heart, bark rim, a radial crack, axe marks."""
        yy, xx = grid(w, h)
        cx, cy = w / 2 - 0.4, h / 2 + 0.3
        r = np.maximum(np.abs(xx + 0.5 - cx) / (w / 2), np.abs(yy + 0.5 - cy) / (h / 2)) * 0.6 + \
            np.hypot((xx + 0.5 - cx) / (w / 2), (yy + 0.5 - cy) / (h / 2)) * 0.4
        v = 4.4 + LO[cat] * 0.4 - r * 1.6 + 0.55 * (np.sin(r * min(w, h) * 1.3) > 0.5)
        rgb = C(R["logend"], v + self.noise(w, h, 0.08))
        rim = r > 0.9; rgb[rim] = C(R["bark"], np.full((h, w), 2.4))[rim]
        crack = (np.abs(xx + 0.5 - cx) < 0.55) & (yy + 0.5 > cy) & ~rim; rgb[crack] = R["logend"][1]
        return rgb, np.ones((h, w), bool)

    def hide(self, Rm, w, h, cat, shape=True):
        """Stretched hide: centre lighter (scraped), darker spine and edges, soft blotches, lace holes, an animal
        outline cut with hard alpha (neck, four legs, tail)."""
        yy, xx = grid(w, h)
        u = (xx + 0.5) / w - 0.5; t = (yy + 0.5) / h - 0.5
        v = 3.6 + LO[cat] + 0.8 * (1 - np.clip(np.hypot(u * 1.6, t * 1.3) * 2, 0, 1)) - (np.abs(u) < 0.04) * 0.6
        v += self.blotches(w, h, max(2, w * h // 120), 0.5, 2, 5) + self.noise(w, h, 0.15)
        rgb = C(Rm, v)
        a = np.ones((h, w), bool)
        if shape:
            body = (np.abs(u) / 0.36) ** 2 + (np.abs(t) / 0.42) ** 2 <= 1
            legs = ((np.abs(np.abs(u) - 0.36) < 0.1) & (np.abs(np.abs(t) - 0.3) < 0.12))
            legs |= ((np.abs(u) > 0.3) & (np.abs(u) < 0.5) & (np.abs(np.abs(t) - 0.36) < 0.08))
            neck = (np.abs(u) < 0.12) & (t < -0.3)
            tail = (np.abs(u) < 0.05) & (t > 0.3)
            a = body | legs | neck | tail
            edge = a & ~(np.roll(a, 1, 0) & np.roll(a, -1, 0) & np.roll(a, 1, 1) & np.roll(a, -1, 1))
            rgb[edge] = C(Rm, v - 1.0)[edge]
            holes = edge & ((xx + yy) % 4 == 0); rgb[holes] = Rm[0]
        return rgb, a

    def liquid(self, Rm, w, h, cat, glow=False):
        yy, xx = grid(w, h)
        v = (4.2 if glow else 3.0) + 0.5 * np.sin(np.hypot(xx - w * 0.4, yy - h * 0.45) * 1.4) * 0.6
        v -= np.clip(np.maximum(np.abs((xx + .5) / w - .5), np.abs((yy + .5) / h - .5)) * 2 - 0.6, 0, 1) * 1.2
        rgb = C(Rm, v + self.noise(w, h, 0.1))
        for _ in range(max(1, w * h // 30)):
            x, y = int(self.nr.integers(0, w - 1)), int(self.nr.integers(0, h))
            rgb[y, x:x + 2] = Rm[-1]
        return rgb, np.ones((h, w), bool)

    def coal(self, w, h, cat, embers=0.0):
        rgb, a = self.pile(R["coal"], w, h, cat, r=1.0, stem=False, gap=R["coal"])
        if embers:
            m = self.nr.random((h, w)) < embers
            rgb[m] = C(R["glow"], 2.5 + self.nr.random((h, w)) * 3)[m]
        return rgb, a

    def flame(self, w, h, cat):
        """Flame card: a tapering tongue (hard alpha), white-yellow core, orange then red at the edges."""
        yy, xx = grid(w, h)
        t = (yy + 0.5) / h                                           # 0 top .. 1 bottom
        half = (w / 2) * np.clip(np.sin(np.clip(t, 0, 1) * math.pi * 0.62) * 1.05, 0, 1)
        sway = np.sin(t * 5) * w * 0.08
        d = np.abs(xx + 0.5 - w / 2 - sway)
        a = d <= half
        core = 1 - d / np.maximum(half, 0.5)
        v = 2.2 + core * 3.0 + t * 1.2
        return C(R["glow"], v), a

    def blade(self, w, h, cat, teeth=True):
        """Saw blade: bright steel with a sheen band, teeth along the bottom edge (hard alpha)."""
        rgb, a = self.metal(R["steel"], w, h, 3.4)
        yy, xx = grid(w, h)
        if teeth and cat in ("lit", "shade"):
            a = ~((yy == h - 1) & (xx % 2 == 1))
        return rgb, a

    def rope(self, w, h, cat):
        yy, xx = grid(w, h)
        v = 3.5 + LO[cat] + np.where(((xx + yy) % 3) == 0, 0.8, -0.2) - np.abs((yy + .5) / h - .5) * 0.8
        return C(R["rope"], v), np.ones((h, w), bool)

    def bellows(self, w, h, cat):
        """Leather bellows side: accordion folds (light ridge, dark crease) with stitched edges."""
        yy, xx = grid(w, h)
        v = 3.4 + LO[cat] + np.where(yy % 2 == 0, 0.6, -0.7) - np.abs((xx + .5) / w - .5) * 1.0
        rgb = C(R["leather"], v + self.noise(w, h, 0.08))
        rgb[:, ::3][0::2] = rgb[:, ::3][0::2]
        return rgb, np.ones((h, w), bool)

    def sawdust(self, w, h, cat):
        rgb = C(R["sawdust"], 3.8 + LO[cat] + self.noise(w, h, 0.6, 3))
        return rgb, np.ones((h, w), bool)

    def mould(self, w, h, cat, slots=3):
        """Ingot mould top: dark iron with sunk slots."""
        rgb, a = self.form(R["iron"], w, h, cat, 3.4)
        if cat == "up":
            yy, xx = grid(w, h)
            for k in range(slots):
                x0 = 1 + k * ((w - 2) // slots)
                m = (xx >= x0) & (xx < x0 + (w - 2) // slots - 1) & (yy >= 1) & (yy < h - 1)
                rgb[m] = C(R["iron"], np.full((h, w), 1.2))[m]
        return rgb, a


class Station(Stall):
    def __init__(self, name, seed, mats, tex=512):
        super().__init__(name, seed, mats, tex)
        self.P = StationPainter(self.nr)
        self._mat_painters_fix()

    def paint(self, name, grp, frm, to, tag, fn, hide=("down",), rot=(0, 0, 0), origin=None, over=None):
        """item() with a painter method name + args: fn = (method, ramp or None, kwargs)."""
        return self.item(name, grp, frm, to, tag, fn, hide, rot, origin, over)

    def log(self, name, grp, frm, to, axis="x", hide=()):
        """A bark log lying along an axis, cut ends with rings."""
        P = self.P
        ends = {"x": ("east", "west"), "z": ("north", "south"), "y": ("up", "down")}[axis]

        def paint(W, H, c, _e=None):
            return P.bark(R["bark"], W, H, c)
        fs_over = {}
        for e in ends:
            a, b = {"east": (2, 1), "west": (2, 1), "north": (0, 1), "south": (0, 1), "up": (0, 2), "down": (0, 2)}[e]
            w, h = px(to[a] - frm[a]), px(to[b] - frm[b])
            k = self.rect(f"logend_{w}x{h}", w, h, lambda W, H: P.ring_end(W, H, "up"))
            fs_over[e] = F(k)
        tag = f"bark_{axis}"
        if axis == "y":
            return self.item(name, grp, frm, to, tag, paint, hide, over=fs_over)
        # side faces of a horizontal log: grain runs along the log, so rotate the bark sideways
        def paint_side(W, H, c):
            rgb, a = P.bark(R["bark"], H, W, c if c not in ("up", "down") else ("lit" if c == "up" else "shade"))
            return np.ascontiguousarray(np.transpose(rgb, (1, 0, 2))), a.T
        return self.item(name, grp, frm, to, tag, paint_side,
                         hide, over=fs_over)

    def flame_cards(self, name, grp, x, y, z, w, h):
        """Two crossed flame cards (hard alpha), named _glow."""
        k = self.rect(f"flame_{px(w)}x{px(h)}", px(w), px(h), lambda W, H: self.P.flame(W, H, "lit"))
        self.card(f"{name}_a_glow", grp, [x - w / 2, y, z], [x + w / 2, y + h, z], k)
        self.card(f"{name}_b_glow", grp, [x, y, z - w / 2], [x, y + h, z + w / 2], k, faces=("east", "west"))

    def rotbar(self, name, grp, p0, p1, thick, mat, painter_tag=None, painter=None):
        """A bar from p0 to p1 (any direction): a cube along z rotated to point at p1 (yaw then pitch)."""
        p0, p1 = np.array(p0, float), np.array(p1, float)
        d = p1 - p0; L = h2(float(np.linalg.norm(d))); mid = (p0 + p1) / 2
        yaw = math.degrees(math.atan2(d[0], d[2]))
        pitch = math.degrees(math.atan2(-d[1], math.hypot(d[0], d[2])))
        frm = [mid[0] - thick / 2, mid[1] - thick / 2, mid[2] - L / 2]; to = [mid[0] + thick / 2, mid[1] + thick / 2, mid[2] + L / 2]
        # Blockbench order Rz*Ry*Rx: pitch about x first, then yaw about y
        rot = (pitch, yaw, 0)
        if painter is not None:
            return self.item(name, grp, frm, to, painter_tag, painter, (), rot, list(mid))
        return self.box(name, grp, frm, to, mat, (), f"{name}rb", rot=rot, origin=list(mid))


def station_mats(extra=None, **kw):
    d = stall_mats(**kw)
    d.update(extra or {})
    return d
