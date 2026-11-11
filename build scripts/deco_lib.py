"""Town decoration library for the hub: castle style street lamps and town greenery (J00BA, 2026-11-09: "street lamps,
which can emit light for when the game goes to night ... similar style to the castle ... other decoration assets in
that style for foliage to make the hub area look more like a town ... very detailed").

Built on station_lib -> stall_lib -> house_lib (the hub_castle v2 swatch method). Castle materials: limestone ashlar
(the castle's STONE ramp), blue grey slate, cool dark iron, gold finials. blockbench_detailed_prompts.md sections 1, 2,
3.4 (plant cards), 3.11 (props), 4, 5. 2 px per unit, front = north (-z), light from the top front left.

Light: every lantern's glass is a cube named `*_glow` (emissive in Godot) inside a group `light_N` whose pivot is the
flame centre, so the game can hang an OmniLight3D on each `light_N` node and switch them on at night."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from station_lib import Station, StationPainter, station_mats, R, C, F, px, h2, LO, CAT, grid
from foliage_lib import ramp, ramp_colour, Ry, Rx, Rz, bb_euler, direction_to_yaw_tilt
import plant_paint as PP

R.update({
    # castle IRON (#1c1f24 .. #8c939c) with a deeper shadow and a cool highlight added (7 shades)
    "lamp_iron": ramp("#121418 #1c1f24 #2a2e35 #3b4049 #4e545e #666d78 #848b96"),
    "lamp_glass": ramp("#6a2e08 #9a4c0c #c86e14 #e8922a #f6b444 #fbcd70 #fee2a0 #fff2d0"),
    "box_leaf": ramp("#0c2210 #143218 #1d4520 #275a28 #337034 #448642 #5a9e50 #78b664"),
    "ivy": ramp("#0a1e14 #102e1c #184226 #225832 #2e6e3c #3e864a #56a05c"),
    "lavender": ramp("#22123c #341e58 #482c76 #5e3c92 #7852ac #946ec2 #b292d6"),
    "geranium": ramp("#3a060e #5c0c16 #82141e #a82028 #c83634 #e05a4a #ee8468"),
    "daisy": ramp("#8a8068 #a89f86 #c6bea6 #ddd8c4 #ebe8da #f3f2ea #f8f8f2"),
    "marigold": ramp("#5a2004 #883406 #b4500a #d86e12 #ee9022 #f8b040 #fcd070"),
    "pansy": ramp("#1e1048 #2e1a6a #42288c #5838a8 #7250c0 #9070d4 #b298e4"),
    "yolk": ramp("#6a4204 #9a6408 #c88a10 #e8ae22 #f6ca44 #fce07a #fdf0b0"),
    "blossom": ramp("#4a1430 #6e2048 #963462 #bc4e80 #d8709c #ec98ba #f6c2d6 #fbe0ea"),
    "cherry_bark": ramp("#180c0e #261416 #381e1e #4c2a28 #603832 #764840 #8c5a4e"),
    "soil": ramp("#1a110a #261810 #342218 #432e20 #543a28 #664834 #785840"),
    "stem_green": ramp("#122a0c #1c3c12 #285218 #346a20 #44822a #5a9a38"),
})


class DecoPainter(StationPainter):
    # ------------------------------------------------------------ lantern glass
    def pane(self, w, h, cat, flame=True, lattice=5):
        """Glowing lantern pane: warm light brightest round the flame, sooty top, a candle and flame silhouette,
        dark lead cames in a diamond lattice and round the edge."""
        yy, xx = grid(w, h)
        u = (xx + 0.5) / w - 0.5; t = (yy + 0.5) / h                       # t: 0 top .. 1 bottom
        fy = 0.6
        d = np.hypot(u * 1.5, (t - fy) * 1.15)
        v = 2.4 + 3.4 * np.clip(1 - d * 1.7, 0, 1) + t * 0.5
        v -= np.clip(0.22 - t, 0, 1) * 6                                     # soot under the cap
        v += self.noise(w, h, 0.12, 30)
        rgb = C(R["lamp_glass"], v)
        if flame:
            cw = max(1, round(w * 0.22))
            cx0 = (w - cw) // 2
            ct = int(round(h * 0.72))
            for y in range(ct, h - 1):                                      # candle
                rgb[y, cx0:cx0 + cw] = C(R["candle"], np.full(cw, 4.6 - (y - ct) * 0.35))
                if cw > 1: rgb[y, cx0 + cw - 1] = C(R["candle"], np.array(3.4))
            fh = max(3, int(round(h * 0.28)))
            for k in range(fh):                                             # flame: teardrop, white core
                y = ct - 1 - k
                if y < 0: break
                s = k / max(1, fh - 1)
                half = max(0, (cw + 1) / 2 * math.sin(min(1.0, (1 - s) * 1.25) * math.pi * 0.62))
                for x in range(w):
                    dx = abs(x + 0.5 - w / 2)
                    if dx <= half + 0.01 or (s > 0.8 and dx < 0.6):
                        rgb[y, x] = R["lamp_glass"][7] if dx < half * 0.5 + 0.3 and s < 0.75 else R["lamp_glass"][6]
        lead = (xx == 0) | (xx == w - 1) | (yy == 0) | (yy == h - 1)
        if lattice and w >= 6:                                              # a cross of cames above the flame
            lead |= (yy == int(h * 0.3))
            lead |= (np.abs(xx + 0.5 - w / 2) < 0.6) & (yy < int(h * 0.3))
        rgb[lead] = C(R["lamp_iron"], 1.4 + 0.6 * (1 - t))[lead]
        return rgb, np.ones((h, w), bool)

    # ------------------------------------------------------------ iron and stone
    def fluted(self, Rm, w, h, cat):
        """Fluted cast iron: a groove every 3 px, rounded across the face, a soft sheen streak, darker at the foot."""
        if cat in ("up", "down"): return self.form(Rm, w, h, cat, 3.2)
        yy, xx = grid(w, h)
        f = xx % 3
        v = 2.9 + LO[cat] + np.where(f == 0, 0.7, np.where(f == 1, 0.15, -0.75))
        v -= np.abs((xx + .5) / w - .5) * 1.2
        v += 0.9 * np.exp(-((((xx + .5) / w) - 0.32) / 0.14) ** 2)
        v += self.vfall(h, 0.8, 0.7) + self.noise(w, h, 0.08)
        return C(Rm, v), np.ones((h, w), bool)

    def panel(self, Rm, w, h, cat, emblem=True, moss=True):
        """Limestone die with a sunk panel: lit lip on the top and left, shadow inside the top left of the recess, a
        light inner bottom right edge, a carved rosette in the middle, soft weathering and moss at the foot."""
        if cat in ("up", "down"): return self.form(Rm, w, h, cat, 3.8)
        yy, xx = grid(w, h)
        base = 3.7 + LO[cat]
        dx = np.abs((xx + .5) / w - .5) * 2; dy = np.abs((yy + .5) / h - .5) * 2
        v = base + 0.5 - np.clip(np.maximum(dx, dy) - 0.45, 0, 1) * 1.4
        m = max(2, min(w, h) // 5)
        inside = (xx >= m) & (xx < w - m) & (yy >= m) & (yy < h - m)
        v[inside] -= 0.45
        v[(yy == m) & inside] -= 0.9; v[(xx == m) & inside] -= 0.7
        v[(yy == h - m - 1) & inside] += 0.6; v[(xx == w - m - 1) & inside] += 0.4
        v[0, :] += 0.5
        if emblem and w >= 10 and h >= 10:
            cx, cy = w / 2, h / 2
            r = np.hypot(xx + .5 - cx, yy + .5 - cy); ang = np.arctan2(yy + .5 - cy, xx + .5 - cx)
            R0 = min(w, h) / 2 - m - 1.2
            petal = r < R0 * (0.62 + 0.38 * np.abs(np.cos(ang * 2)))
            ring = petal & ~(np.roll(petal, 1, 0) & np.roll(petal, 1, 1))
            v[petal] += 0.55
            v[ring & ((xx + .5 - cx) + (yy + .5 - cy) < 0)] += 0.4                   # lit upper left rim
            v[ring & ((xx + .5 - cx) + (yy + .5 - cy) > 0)] -= 0.9                   # shadowed lower right
            v[r < 1.2] -= 0.6
        v += self.blotches(w, h, max(1, w * h // 700), 0.35, 2, 6) + self.vfall(h, 0.78, 0.6) + self.noise(w, h, 0.1)
        rgb = C(Rm, v)
        if moss:
            mm = self.moss_mask(w, h, True, 0.22); rgb[mm] = C(R["moss"], 3.1 + LO[cat] + self.noise(w, h, 0.4, 8))[mm]
        return rgb, np.ones((h, w), bool)

    def gadroon(self, Rm, w, h, cat):
        """Urn bowl: vertical lobes (gadroons) 4 px wide, lit left, shadowed right, rounded overall."""
        if cat in ("up", "down"): return self.form(Rm, w, h, cat, 3.6)
        yy, xx = grid(w, h)
        prof = np.array([0.55, 0.45, 0.0, -0.85])[xx % 4]
        v = 3.5 + LO[cat] + prof - np.abs((xx + .5) / w - .5) * 1.1
        v += 0.5 * (0.5 - (yy + .5) / h) + self.blotches(w, h, max(1, w * h // 400), 0.3, 2, 5) + self.noise(w, h, 0.08)
        return C(Rm, v), np.ones((h, w), bool)

    # ------------------------------------------------------------ greenery solids
    def hedge(self, Rm, w, h, cat, bloom=None, bloom_rate=0.0):
        """Clipped box hedge: hundreds of tiny leaves (light top left pixel, dark lower right), dark gaps between,
        lighter on top and toward the top of the sides, darker at the edges and foot. Optional tiny blossoms."""
        nr = self.nr
        lo = LO[cat] * 1.2
        v = np.full((h, w), 1.0 + lo)
        n = int(w * h / 2.0)
        pts = sorted(((int(nr.integers(-1, w)), int(nr.integers(-1, h))) for _ in range(n)), key=lambda p: p[1])
        pat = np.array([[0.65, 0.25, -0.1], [0.15, -0.2, -0.55]])
        for x, y in pts:
            b = 3.0 + lo + nr.normal(0, 0.32)
            lw = 3 if nr.random() < 0.4 else 2
            for j in range(2):
                for i in range(lw):
                    X, Y = x + i, y + j
                    if 0 <= X < w and 0 <= Y < h: v[Y, X] = b + pat[j, i]
        dx = np.abs((np.arange(w) + .5) / w - .5)[None, :] * 2
        dy = np.abs((np.arange(h) + .5) / h - .5)[:, None] * 2
        v -= np.clip(np.maximum(dx, dy) - 0.55, 0, 1) * 1.5
        if cat not in ("up", "down"):
            v += 0.8 * (0.5 - (np.arange(h)[:, None] + .5) / h)
        rgb = C(Rm, v)
        if bloom is not None and bloom_rate:
            m = (nr.random((h, w)) < bloom_rate) & (v > 2.4 + lo)
            rgb[m] = C(bloom, np.full((h, w), 5.0 + LO[cat]))[m]
        return rgb, np.ones((h, w), bool)

    def soil(self, w, h, cat="up", litter=None):
        nr = self.nr
        if cat != "up" or h < 3 or w < 3: return self.form(R["soil"], w, h, "shade", 3.0)
        v = 2.8 + self.noise(w, h, 0.45, 5) + self.blotches(w, h, max(1, w * h // 200), 0.5, 1.5, 4)
        rgb = C(R["soil"], v)
        for _ in range(w * h // 9):                                          # crumbs with a lit top pixel
            x, y = int(nr.integers(0, w)), int(nr.integers(0, h - 1))
            rgb[y, x] = R["soil"][5]; rgb[y + 1, x] = R["soil"][1]
        for _ in range(w * h // 14):                                         # moss and fallen leaf bits
            x, y = int(nr.integers(0, w)), int(nr.integers(0, h))
            rgb[y, x] = C(R["moss"], np.array(nr.uniform(2.5, 4.5)))
        if litter is not None:
            for _ in range(w * h // 18):
                x, y = int(nr.integers(0, w - 1)), int(nr.integers(0, h))
                rgb[y, x:x + 2] = C(litter, np.array(nr.uniform(3.5, 6)))
        return rgb, np.ones((h, w), bool)

    # ------------------------------------------------------------ plant cards (hard alpha; tip = top row)
    def ivy_strand(self, w, h, shade=0.0):
        """Trailing ivy: a wavy stem from the base (bottom row) to the tip (top row) with alternating three-lobed
        leaves, each lit on its upper left with a dark vein; smaller leaves toward the tip."""
        nr = self.nr
        val = np.full((h, w), -9.0); stem = np.zeros((h, w), bool)
        ph = nr.uniform(0, 6)
        side = 1
        for y in range(h):
            t = 1 - (y + 0.5) / h                                            # 0 base .. 1 tip
            cx = (w - 1) / 2 + math.sin(y * 0.55 + ph) * (w / 2 - 1.5) * 0.6
            x = int(round(cx)); val[y, x] = 1.2 + shade; stem[y, x] = True
            if y % 3 == 1 and y < h - 1:
                big = t < 0.7
                lx = x + side * (2 if big else 1)
                pts = [(0, 0), (-1, 0), (1, 0), (0, -1), (0, 1)] if big else [(0, 0), (0, -1), (side * -1, 0)]
                if big and nr.random() < 0.5: pts += [(-1, -1), (1, -1)]
                for ex, ey in pts:
                    X, Y = lx + ex, y + ey
                    if 0 <= X < w and 0 <= Y < h:
                        vv = 3.4 + shade + 1.2 * t * 0.5 + (0.8 if (ex < 0 or ey < 0) else 0) - (0.6 if ex > 0 and ey >= 0 else 0)
                        if (ex, ey) == (0, 0): vv -= 0.9                     # vein
                        val[Y, X] = vv
                side = -side
        a = val > -5
        rgb = C(R["ivy"], val)
        rgb[stem] = C(R["oak"], np.full((h, w), 2.4))[stem]
        return rgb, a

    def flower_disc(self, Rp, Rc, w, h, kind="daisy", shade=0.0):
        """A flower head seen from the front. daisy: rays with a yellow eye; pansy: five round petals with a dark
        blotch and a gold eye; pompom: a cluster of small florets (geranium, marigold)."""
        nr = self.nr
        yy, xx = grid(w, h)
        cx, cy = w / 2, h / 2
        r = np.hypot(xx + .5 - cx, yy + .5 - cy); ang = np.arctan2(yy + .5 - cy, xx + .5 - cx)
        R0 = min(w, h) / 2
        rgb = np.zeros((h, w, 3), np.uint8)
        if kind == "daisy":
            n = 10 if R0 >= 3.5 else 8
            a = (r <= R0) & ((np.cos(ang * n / 2) ** 2 > 0.25) | (r < R0 * 0.5))
            v = 4.4 + shade + (1 - r / R0) * 1.2 - (np.sin(ang) * 0.5)
            rgb[:] = C(Rp, v)
            eye = r < max(1.0, R0 * 0.36)
            rgb[eye] = C(Rc, 4.4 - (xx + yy - cx - cy) * 0.35)[eye]
        elif kind == "pansy":
            lobes = R0 * (0.78 + 0.22 * np.abs(np.cos(ang * 2.5)))
            a = r <= lobes
            v = 3.6 + shade + (r / R0) * 1.4 - np.sin(ang) * 0.5
            rgb[:] = C(Rp, v)
            blotch = r < R0 * 0.5
            rgb[blotch] = C(Rp, np.full((h, w), 0.6))[blotch]
            rays = (r < R0 * 0.7) & (np.cos(ang * 5) > 0.92); rgb[rays] = C(Rp, np.full((h, w), 1.2))[rays]
            eye = r < 0.9; rgb[eye] = R["yolk"][4]
        else:  # pompom
            a = np.zeros((h, w), bool); v = np.full((h, w), 0.0)
            for _ in range(int(R0 * R0 * 1.4) + 4):
                fr = nr.uniform(0, R0 - 1.0); fa = nr.uniform(0, 2 * math.pi)
                fx, fy = cx + math.cos(fa) * fr, cy + math.sin(fa) * fr
                d = np.hypot(xx + .5 - fx, yy + .5 - fy)
                m = d < 1.3
                a |= m
                v = np.where(m, 3.3 + shade + (1.3 - d) * 1.4 - (fy - cy) / R0 * 0.8, v)
            rgb[:] = C(Rp, v)
            dots = a & (nr.random((h, w)) < 0.08); rgb[dots] = C(Rc, np.full((h, w), 4.5))[dots]
        return rgb, a

    def lavender_spike(self, w, h, shade=0.0):
        """Lavender: a thin green stem, the top 55% stacked with paired purple buds, lighter toward the tip."""
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        cx = w // 2; top = int(h * 0.55)
        for y in range(h):
            t = 1 - (y + 0.5) / h
            if y >= top:
                a[y, cx] = True; rgb[y, cx] = C(R["stem_green"], np.array(1.2 + 3 * t + shade))
                continue
            k = y / max(1, top)
            v = 4.6 - k * 2.2 + shade
            xs = [cx - 1, cx + 1] if y % 2 == 0 else [cx]
            if y < 2: xs = [cx]
            for x in xs:
                if 0 <= x < w:
                    a[y, x] = True; rgb[y, x] = C(R["lavender"], np.array(v + (0.6 if x < cx else 0)))
        return rgb, a

    def blossom_sprig(self, w, h, shade=0.0, leaves=True):
        """Cherry blossom sprig: a dark twig from the bottom centre up and out, five-petal flowers along it (pale
        petals, a deep pink heart, a gold dot), a few small fresh leaves."""
        nr = self.nr
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        x = w // 2; path = []
        for y in range(h - 1, -1, -1):
            if y % 3 == 0 and y < h - 2: x = int(np.clip(x + nr.choice([-1, 0, 1]), 1, w - 2))
            a[y, x] = True; rgb[y, x] = C(R["cherry_bark"], np.array(2.0 + (1 - y / h) * 2)); path.append((x, y))
        nfl = max(3, (w * h) // 14)
        for i in range(nfl):
            bx, by = path[int(nr.integers(len(path) // 5, len(path)))]
            fx, fy = int(np.clip(bx + nr.integers(-2, 3), 1, w - 2)), int(np.clip(by + nr.integers(-1, 2), 1, h - 2))
            b = 5.0 + shade + nr.uniform(-0.6, 0.6) - (fy / h) * 0.8
            for ex, ey, dv in ((0, -1, 0.6), (-1, 0, 0.4), (1, 0, -0.2), (0, 1, -0.5), (0, 0, -1.6)):
                X, Y = fx + ex, fy + ey
                a[Y, X] = True; rgb[Y, X] = C(R["blossom"], np.array(b + dv))
            if nr.random() < 0.5: rgb[fy, fx] = R["yolk"][4]
        if leaves:
            for _ in range(2):
                bx, by = path[int(nr.integers(len(path) // 3, len(path)))]
                for ex, ey, dv in ((1, 0, 0.6), (2, -1, 0.2), (2, 0, -0.3)):
                    X, Y = bx + ex, by + ey
                    if 0 <= X < w and 0 <= Y < h and not a[Y, X]:
                        a[Y, X] = True; rgb[Y, X] = C(R["box_leaf"], np.array(5.0 + dv))
        return rgb, a

    def petal_scatter(self, w, h, R_=None):
        nr = self.nr; R_ = R_ or R["blossom"]
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        for _ in range(max(3, w * h // 7)):
            x, y = int(nr.integers(0, w - 1)), int(nr.integers(0, h))
            b = nr.uniform(4.2, 6.6)
            a[y, x] = True; rgb[y, x] = C(R_, np.array(b))
            if nr.random() < 0.5: a[y, x + 1] = True; rgb[y, x + 1] = C(R_, np.array(b - 0.8))
        return rgb, a


class Deco(Station):
    def __init__(self, name, seed, mats, tex=512):
        super().__init__(name, seed, mats, tex)
        self.P = DecoPainter(self.nr)
        self._mat_painters_fix()
        self.n_light = 0
        self._n = {}

    def nid(self, prefix):
        self._n[prefix] = self._n.get(prefix, 0) + 1
        return f"{prefix}_{self._n[prefix]}"

    # ------------------------------------------------------------ geometry helpers
    def curve(self, name, grp, origin, d, pts, thick=0.5, mat="iron"):
        """Wrought iron scroll: bars through 2D points (u along the horizontal direction d, v up) from origin.
        Each bar is stretched by its thickness so the joints close."""
        o = np.array(origin, float); d = np.array([d[0], 0, d[1]], float); d /= np.linalg.norm(d); up = np.array([0, 1.0, 0])
        P3 = [o + d * u + up * v for u, v in pts]
        for i in range(len(P3) - 1):
            a, b = P3[i], P3[i + 1]
            s = (b - a) / max(1e-6, np.linalg.norm(b - a)) * thick * 0.5
            self.rotbar(f"{name}_{i + 1}", grp, list(a - s), list(b + s), thick, mat)

    def octo_item(self, name, grp, cx, cz, D, y1, y2, tag, painter, hide=("down",), inset=None):
        """Rounded column / bowl section: two crossed boxes (an octagon in plan) painted with a painter."""
        inset = inset if inset is not None else h2(D * 0.3)
        a, b = D / 2, (D - inset) / 2
        self.item(f"{name}_a", grp, [cx - a, y1, cz - b], [cx + a, y2, cz + b], tag, painter, hide)
        self.item(f"{name}_b", grp, [cx - b, y1, cz - a], [cx + b, y2, cz + a], tag, painter, hide)

    def head_card(self, name, grp, centre, key, s, yaw, pitch, roll=0.0):
        """A square card centred on a point (flower heads): yaw about y, then pitched back by `pitch`."""
        cx, cy, cz = centre
        M = Ry(yaw) @ Rx(-pitch) @ Rz(roll)
        return self.m.cube(name, grp, [cx - s / 2, cy - s / 2, cz], [cx + s / 2, cy + s / 2, cz], {"north": F(key)},
                           rotation=bb_euler(M), origin=[cx, cy, cz])

    def dir_card(self, name, grp, base, key, w, L, direction, roll=0.0, sink=0.0):
        yaw, tilt = direction_to_yaw_tilt(direction)
        return self.m.card(name, grp, [round(v, 3) for v in base], key, w, L, yaw, tilt, roll, sink)

    # ------------------------------------------------------------ lanterns
    def lantern(self, name, grp, cx, y, cz, s=5.0, gh=7.0, roof_h=6.0, hang=False, corner_balls=True):
        """Castle lantern standing on a tray at height y: drip knob and stepped cups under the tray, a glowing
        leaded glass box (light_N group, pivot at the flame) with iron corner posts and bands, a slate witch-hat cap
        with a gold finial. hang=True adds a hanging ring on the finial. Returns the finial top."""
        g = self.group(name, [cx, y, cz], grp)
        hs = s / 2
        self.box(f"{name}_drip", g, [cx - 0.5, y - 3, cz - 0.5], [cx + 0.5, y - 2, cz + 0.5], "gold", (), "drip")
        self.box(f"{name}_cup_2", g, [cx - 1, y - 2, cz - 1], [cx + 1, y - 1, cz + 1], "iron", (), "cup2")
        self.box(f"{name}_cup_1", g, [cx - hs + 0.5, y - 1, cz - hs + 0.5], [cx + hs - 0.5, y, cz + hs - 0.5], "iron", (), f"cup1{s}")
        self.box(f"{name}_tray", g, [cx - hs - 1, y, cz - hs - 1], [cx + hs + 1, y + 1, cz + hs + 1], "iron", (), f"tray{s}")
        if corner_balls:
            for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
                bx, bz = cx + sx * (hs + 0.5), cz + sz * (hs + 0.5)
                self.box(f"{name}_tray_knob_{i + 1}", g, [bx - 0.5, y + 1, bz - 0.5], [bx + 0.5, y + 2, bz + 0.5], "gold", ("down",), "tknob")
        self.n_light += 1
        lg = self.group(f"light_{self.n_light}", [cx, y + 1 + gh * 0.45, cz], g)
        self.item(f"{name}_glass_glow", lg, [cx - hs + 0.5, y + 1, cz - hs + 0.5], [cx + hs - 0.5, y + 1 + gh, cz + hs - 0.5],
                  f"pane{s}x{gh}", lambda W, H, c: self.P.pane(W, H, c), hide=("up", "down"))
        for i, (sx, sz) in enumerate(((-1, -1), (1, -1), (1, 1), (-1, 1))):
            px0, pz0 = cx + sx * hs - (1 if sx > 0 else 0), cz + sz * hs - (1 if sz > 0 else 0)
            self.box(f"{name}_post_{i + 1}", g, [px0, y + 1, pz0], [px0 + 1, y + 1 + gh, pz0 + 1], "iron", ("up", "down"), f"lpost{gh}")
        self.box(f"{name}_band", g, [cx - hs - 0.5, y + 1 + gh, cz - hs - 0.5], [cx + hs + 0.5, y + 2 + gh, cz + hs + 0.5], "iron", (), f"band{s}")
        y0 = y + 2 + gh
        self.cone(f"{name}_cap", g, cx, cz, s + 3, y0, y0 + roof_h, "slate", n=5, finial="gold")
        top = y0 + roof_h + 4
        if hang:
            self.box(f"{name}_ring_a", g, [cx - 1, top, cz - 0.25], [cx + 1, top + 0.5, cz + 0.25], "iron", (), "ring_h")
            self.box(f"{name}_ring_b", g, [cx - 1, top + 1.5, cz - 0.25], [cx + 1, top + 2, cz + 0.25], "iron", (), "ring_h")
            for sx in (-1, 1):
                self.box(f"{name}_ring_{'l' if sx < 0 else 'r'}", g, [cx + sx * 1 - (0.5 if sx > 0 else 0), top, cz - 0.25],
                         [cx + sx * 1 + (0.5 if sx < 0 else 0), top + 2, cz + 0.25], "iron", (), "ring_v")
            top += 2
        return top

    def chain(self, name, grp, x, y_top, y_bot, z):
        """Hanging chain of alternating links (turned 90 degrees to each other)."""
        y = y_top; i = 0
        while y - 1.5 >= y_bot - 0.01:
            if i % 2 == 0:
                self.box(f"{name}_link_{i + 1}", grp, [x - 0.5, y - 1.5, z - 0.25], [x + 0.5, y, z + 0.25], "iron", (), "link_a")
            else:
                self.box(f"{name}_link_{i + 1}", grp, [x - 0.25, y - 1.5, z - 0.5], [x + 0.25, y, z + 0.5], "iron", (), "link_b")
            y -= 1.0; i += 1

    # ------------------------------------------------------------ greenery helpers
    def tufts(self, prefix, grp, spots, ramp_=None):
        """Grass tufts (crossed blade cards with the ground colours) at (x, z, n_blades, height) spots."""
        Rg = ramp_ or PP.GRASS
        keys = [self.rect(f"tuft_blade_{i}", px(w), px(L), lambda W, H, b=b, sh=sh: PP.paint_blade(self.nr, Rg, W, H, sh, b, 2, 1))
                for i, (w, L, b, sh) in enumerate(((1.5, 3.5, 0.3, -0.2), (1.5, 4.5, -0.4, 0.2), (1.5, 3, 0.6, 0.0), (2, 5, -0.2, 0.3)))]
        dims = [(1.5, 3.5), (1.5, 4.5), (1.5, 3), (2, 5)]
        for x, z, n, hh in spots:
            for j in range(n):
                k = int(self.rng.randrange(4)) if hh > 3.5 else int(self.rng.choice([0, 2]))
                w, L = dims[k]
                self.m.card(self.nid(f"{prefix}_blade"), grp, [x + self.rng.uniform(-0.5, 0.5), 0, z + self.rng.uniform(-0.5, 0.5)],
                            self.rects_key(k, keys), w, L, j * 137.5 + self.rng.uniform(-20, 20), self.rng.uniform(10, 55),
                            self.rng.uniform(-30, 30), sink=0.5)

    @staticmethod
    def rects_key(k, keys): return keys[k]

    def ivy_keys(self):
        return [self.rect(f"ivy_{L}_{i}", px(3), px(L), lambda W, H, sh=sh: self.P.ivy_strand(W, H, sh))
                for i, (L, sh) in enumerate(((6, 0.0), (8, -0.3), (10, 0.2), (12, -0.1)))]

    def ivy_over_edge(self, prefix, grp, edge_pts, outward, lengths=(6, 8, 10, 12), y=None):
        """Ivy strands hanging over a rim: each card starts on the rim top and hangs down just outside the wall.
        edge_pts: [(x, y, z)], outward: (dx, dz) unit vector away from the planter."""
        keys = self.ivy_keys(); Ls = [6, 8, 10, 12]
        for (x, yy, z) in edge_pts:
            k = self.rng.randrange(len(keys)) if lengths is None else Ls.index(self.rng.choice(lengths))
            L = Ls[k]
            d = (outward[0] * self.rng.uniform(0.08, 0.22), -1.0, outward[1] * self.rng.uniform(0.08, 0.22))
            d = (d[0] + self.rng.uniform(-0.08, 0.08), d[1], d[2] + self.rng.uniform(-0.08, 0.08))
            base = [x + outward[0] * 0.6, yy + 0.5, z + outward[1] * 0.6]
            # a short lip card over the rim, then the hanging strand
            self.dir_card(self.nid(f"{prefix}_ivy"), grp, base, keys[k], 3, L, d, roll=self.rng.uniform(-25, 25))

    def leaf_keys(self, Rm, tag, shapes=((2, 3.5, 0.2), (2.5, 4, -0.2), (2, 3, 0.0)), serrate=False):
        out = []
        for i, (w, L, bend) in enumerate(shapes):
            for band, sh in (("lo", -0.7), ("hi", 0.5)):
                k = self.rect(f"{tag}_leaf_{i}_{band}", px(w), px(L),
                              lambda W, H, sh=sh, b=bend: PP.paint_leaf(self.nr, Rm, W, H, sh, b, 0.14, 0.4, serrate, R["stem_green"]))
                out.append((k, w, L, band))
        return out

    def rosette(self, prefix, grp, x, y, z, keys, n=6, tilt=(55, 80)):
        """Leaves fanning out from a point, lower band drooping."""
        for j in range(n):
            k, w, L, band = keys[(j * 2 + (0 if j % 3 else 1)) % len(keys)]
            self.m.card(self.nid(f"{prefix}_leaf"), grp, [x, y, z], k, w, L, j * 360 / n + self.rng.uniform(-25, 25),
                        self.rng.uniform(*tilt), self.rng.uniform(-30, 30), sink=0.3)

    def flower(self, prefix, grp, x, y, z, height, head_key, head_s, stem_lean=12, yaw=None, pitch=None, stem_key=None):
        """One flower: a thin stem card from (x, y, z) leaning out, a head card on its tip facing up and out."""
        yaw = self.rng.uniform(0, 360) if yaw is None else yaw
        sk = stem_key or self.rect(f"stem_{height}", px(1), px(height), lambda W, H: PP.paint_twig(self.nr, R["stem_green"], W, H, 0))
        tip = self.m.card(self.nid(f"{prefix}_stem"), grp, [x, y, z], sk, 1, height, yaw, stem_lean, self.rng.uniform(-40, 40), sink=0.3)
        p = pitch if pitch is not None else self.rng.uniform(40, 75)
        self.head_card(self.nid(f"{prefix}_head"), grp, [round(v, 3) for v in tip], head_key, head_s, yaw + 180, p)
        return tip

    def fuzz(self, prefix, grp, centre, half, keys, n, ymin=None):
        """Leaf cards poking out of a clipped solid (box of half sizes `half` round `centre`) so its outline is soft:
        each card starts just inside a face and points outward."""
        cx, cy, cz = centre; hx, hy, hz = half
        for i in range(n):
            # pick a face weighted by area, never the bottom
            faces = [("x+", hy * hz), ("x-", hy * hz), ("z+", hx * hy), ("z-", hx * hy), ("y+", hx * hz * 1.3)]
            tot = sum(a for _, a in faces); r = self.rng.uniform(0, tot)
            for f, a in faces:
                r -= a
                if r <= 0: break
            u, v = self.rng.uniform(-0.85, 0.85), self.rng.uniform(-0.85, 0.85)
            if f[0] == "x": p = [cx + (hx - 0.4) * (1 if f[1] == "+" else -1), cy + v * hy, cz + u * hz]; d = [1 if f[1] == "+" else -1, 0.35 + v * 0.3, u * 0.5]
            elif f[0] == "z": p = [cx + u * hx, cy + v * hy, cz + (hz - 0.4) * (1 if f[1] == "+" else -1)]; d = [u * 0.5, 0.35 + v * 0.3, 1 if f[1] == "+" else -1]
            else: p = [cx + u * hx, cy + hy - 0.4, cz + v * hz]; d = [u * 0.6, 1.0, v * 0.6]
            if ymin is not None and p[1] < ymin: continue
            k, w, L, band = keys[self.rng.randrange(len(keys))]
            if f[0] == "y" or v > 0: k, w, L, band = next((kk for kk in keys if kk[3] == "hi" and kk[1] == w and kk[2] == L), (k, w, L, band))
            self.dir_card(self.nid(f"{prefix}_leaf"), grp, p, k, w, L, d, roll=self.rng.uniform(-40, 40))


def deco_mats(extra=None):
    d = station_mats(extra={
        "iron": {"kind": "metal", "ramp": R["lamp_iron"], "side": (24, 24), "top": (16, 16), "no_lit2": True},
        "slate": {"kind": "shingle", "ramp": R["tile_slate"], "side": (48, 24), "top": (32, 32), "no_lit2": True,
                  "extra": {"style": "slate"}},
        "stone": {"kind": "ashlar", "ramp": R["stone"], "side": (64, 32), "top": (40, 40), "no_lit2": True},
        "cobble": {"kind": "cobble", "ramp": R["cobble"], "side": (64, 8), "top": (48, 48), "no_lit2": True},
    }, trim="stone", trim_kind="ashlar")
    d.update(extra or {})
    return d
