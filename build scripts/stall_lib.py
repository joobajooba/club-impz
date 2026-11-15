"""Market stalls for the hub (blockbench_detailed_prompts.md sections 1, 2, 3.11, 4, 5). Built on house_lib.py (the
fantasy houses): materials are painted once as swatches and faces are crops of them, plus new painters for the market
goods: striped awnings and valances, fruit piles, bread, cakes, bottles, cloth, wicker, barrels, sacks and signs.

House style (section 1.5.1): 7 shade hue shifted ramps, every face lighter in the centre and darker at its edges, soft
contact shadows, material detail on top, low noise last. Front = north (-z): customers stand north of the counter."""
import math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from house_lib import House, Painter, R, C, BLOOMS, OPP, DIMS
from foliage_lib import F, ramp, px, h2, Rx

R.update({
    "awn_red": ramp("#3e0c12 #5e141a #821f22 #a42e2a #c2443a #d8604e #e8826a"),
    "canvas": ramp("#5a5040 #766a56 #92866e #ada088 #c6baa0 #d8cfb8 #e8e2d0"),
    "awn_honey": ramp("#4e2c06 #74440c #9c6214 #c08220 #daa034 #ecbe52 #f6d67e"),
    "sage": ramp("#1a2a1e #263c2a #345238 #466a48 #5c845a #789e70 #98b88c"),
    "teal_cloth": ramp("#08262c #0e3a42 #15525a #1f6c72 #2e8a8c #48a6a2 #6ec0b8"),
    "plum_paint": ramp("#24102a #3a1a44 #522660 #6c347a #864896 #a062ae #ba82c4"),
    "pine_wood": ramp("#3a2410 #5a3a18 #7c5424 #9c6e32 #b88a44 #cfa45c #e0bc78"),
    "apple": ramp("#3a0810 #5e0e16 #8a1a1e #b42a26 #d4443a #e86e58 #f4a088"),
    "orange": ramp("#5a2006 #8a360a #b8520e #dc7016 #f08e2a #f8ae50 #fcca80"),
    "pear": ramp("#2a3a08 #42560e #5e7414 #7c921e #9cae30 #bcc84c #d6dc78"),
    "grape": ramp("#1c0a26 #2e1240 #461c5c #602a78 #7c3e94 #9a5aae #b67ec8"),
    "lemon": ramp("#5a4a06 #84700a #ae9612 #d2ba1e #eed43a #f8e66a #fcf2a4"),
    "melon": ramp("#0c2410 #133818 #1c5022 #286a2c #38843a #52a04e #74b868"),
    "pumpkin": ramp("#4a1a06 #74300a #a04a0e #c86614 #e48424 #f4a444 #fac276"),
    "cabbage": ramp("#1e3a14 #2c5418 #3e6e20 #56882c #74a23e #98bc5a #bcd47e"),
    "crust": ramp("#3a1a08 #5c2c0e #864616 #ac6420 #ca8432 #e0a450 #eec47c"),
    "sponge": ramp("#6a4a20 #8c6a34 #ae8a4a #caa864 #dec282 #ecd8a2 #f6eac6"),
    "frost_pink": ramp("#5a1e36 #84304e #b04a6a #d06a88 #e48ea6 #f0b2c2 #f8d4de"),
    "berry": ramp("#2a0814 #460e20 #681630 #8c2240 #ae3452 #c85068 #dc7488"),
    "cork": ramp("#3a2614 #56391e #74502a #926a3a #ae844e #c49e66 #d6b880"),
    "glow_green": ramp("#0e3a14 #186a20 #2a9a2a #4ac63a #7ce45a #b4f48a #e2fcc4"),
    "glow_pink": ramp("#4a0a34 #7a1456 #ac2a7e #d84aa4 #f07ac4 #f8acdc #fcdcf0"),
    "glow_cyan": ramp("#06303e #0c5468 #148090 #26aab4 #4ccad0 #8ce4e4 #cef6f4"),
    "glow_violet": ramp("#1e0a3a #361464 #52228e #7438b4 #9858d4 #be86ea #e2c0f8"),
    "slate_board": ramp("#121a1a #1a2626 #223232 #2c3e3e #384c4a #465a58 #546a66"),
    "chalk": ramp("#7a8480 #98a29e #b4bcb8 #ccd2ce #e0e4e0 #eceeea #f4f6f2"),
    "wicker": ramp("#3e2a12 #5c4020 #7c5a2e #9c763e #b89252 #ceac6c #e0c690"),
    "burlap": ramp("#4a3a24 #665234 #826a46 #9c845a #b49e72 #c8b68c #d8caa6"),
    "rose": ramp("#4a0e22 #721a36 #9a2a4c #c04064 #da5e80 #ec88a0 #f6b4c4"),
    "indigo": ramp("#0e1238 #18205a #24307c #34449c #4a5cb8 #6c7ed0 #96a4e2"),
    "emerald": ramp("#06261a #0c3e2a #12583c #1c7450 #2a9066 #44ac80 #6cc69e"),
    "coral": ramp("#4e1a12 #7a2a1c #a6402a #cc5a3a #e47a52 #f29c74 #f8c09e"),
    "candle": ramp("#6a5a40 #8a7a5a #aa9a76 #c8b894 #ded2b0 #ece4c8 #f6f0de"),
    "paper": ramp("#6a5e48 #8a7c60 #a89a7c #c4b696 #d8ccae #e6dcc4 #f0eada"),
})
LO = {"up": 0.6, "lit": 0.15, "shade": -0.4, "down": -1.2}
CAT = {"north": "lit", "east": "lit", "south": "shade", "west": "shade", "up": "up", "down": "down"}


def grid(w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    return yy, xx


class StallPainter(Painter):
    # ------------------------------------------------------------ simple forms
    def form(self, Rm, w, h, cat, base=3.4, hl=False, noise=0.1, vert=0.4):
        """Centre light, edges 1 to 1.5 steps darker, a little lighter towards the top, optional highlight pixel."""
        yy, xx = grid(w, h)
        dx = np.abs((xx + 0.5) / w - 0.5) * 2; dy = np.abs((yy + 0.5) / h - 0.5) * 2
        v = base + LO[cat] + 0.6 - np.clip(np.maximum(dx, dy) ** 2, 0, 1) * 1.3
        if cat not in ("up", "down"): v += vert * (0.5 - (yy + 0.5) / h)
        v += self.noise(w, h, noise)
        rgb = C(Rm, v)
        if hl and w >= 3 and h >= 3 and cat != "down":
            rgb[max(0, int(h * 0.3) - (0 if h < 4 else 0)), int(w * 0.3)] = Rm[-1]
        return rgb, np.ones((h, w), bool)

    def fruit(self, Rm, w, h, cat, kind="round"):
        rgb, a = self.form(Rm, w, h, cat, 3.3, hl=True, noise=0.05)
        if kind == "melon" and cat != "down":                       # dark green stripes
            for x in range(1, w, 3): rgb[:, x] = C(Rm, np.full(h, 1.6 + LO[cat]))
        if kind == "pumpkin" and cat != "up":                        # ribs
            for x in range(0, w, 2): rgb[:, x] = C(Rm, np.full(h, 2.4 + LO[cat]))
        if cat == "up" and kind in ("round", "pear", "pumpkin") and w >= 2:
            rgb[h // 2, w // 2] = R["oak"][1]                          # stem dimple
        return rgb, a

    def pile(self, Rm, w, h, cat, r=1.5, leaf=0.12, stem=True, stripes=False, gap=None):
        """A heap of round fruit: hex packed disks, each lit from the top left with a highlight pixel, darkest
        in the gaps; a few leaves and stems."""
        nr = self.nr; yy, xx = grid(w, h)
        v = np.full((h, w), 0.6); owner = -np.ones((h, w), int)
        d = 2 * r; cents = []
        for j, cy in enumerate(np.arange(r - 0.5, h + r, d * 0.87)):
            off = r if j % 2 else 0
            for cx in np.arange(-off + r - 0.5, w + r, d):
                cents.append((cx + nr.uniform(-0.35, 0.35), cy + nr.uniform(-0.3, 0.3)))
        order = nr.permutation(len(cents))
        lit = LO[cat] * 0.6
        for i in order:
            cx, cy = cents[i]
            dd = np.hypot(xx + 0.5 - cx - 0.5, yy + 0.5 - cy - 0.5)
            m = dd < r + 0.35
            b = nr.normal(0, 0.25)
            val = 3.2 + lit + b + 1.0 * (1 - dd / (r + 0.35)) - 0.55 * ((xx + 0.5 - cx) + (yy + 0.5 - cy)) / max(1, r)
            v[m] = val[m]; owner[m] = i
        if cat != "up": v += np.clip((yy + 0.5) / h - 0.5, 0, 1) * -0.6
        rgb = C(Rm, v + self.noise(w, h, 0.06))
        if stripes:
            sm = (owner >= 0) & ((xx % 3) == 0); rgb[sm] = C(Rm, v - 1.3)[sm]
        gm = owner < 0; rgb[gm] = C(gap or R["walnut"], np.full((h, w), 1.0))[gm]
        for i in range(len(cents)):
            cx, cy = cents[i]; hx, hy = int(cx - r * 0.35), int(cy - r * 0.35)
            if 0 <= hx < w and 0 <= hy < h and owner[hy, hx] == i: rgb[hy, hx] = Rm[-1]
            sx, sy = int(round(cx)), int(round(cy - r + 0.2))
            if stem and r >= 1.5 and 0 <= sx < w and 0 <= sy < h and owner[sy, sx] == i and nr.random() < 0.5:
                rgb[sy, sx] = R["oak"][1]
                if nr.random() < leaf * 3 and sx + 1 < w: rgb[sy, sx + 1] = R["cabbage"][4]
        return rgb, np.ones((h, w), bool)

    def crate(self, Rm, w, h, cat):
        """Slatted crate: horizontal slats with dark gaps, end posts, nail heads, a stencilled band."""
        if cat in ("up", "down"):
            return self.form(Rm, w, h, cat, 3.6)
        yy, xx = grid(w, h); v = np.full((h, w), 3.4 + LO[cat])
        for y0 in range(0, h, 3):
            b = self.nr.normal(0, 0.25)
            for d in range(3):
                if y0 + d < h: v[y0 + d] = 3.4 + LO[cat] + b + (0.45 if d == 0 else 0) - (1.6 if d == 2 else 0)
        v += 0.25 * np.sin(xx * 0.7 + yy * 3.1) * (np.sin(xx * 0.2) > 0)
        v[:, :2] = 3.0 + LO[cat] + np.array([0.4, 0.0]); v[:, -2:] = 3.0 + LO[cat] + np.array([-0.2, -0.6])
        for y0 in range(0, h, 3):
            for xn in (0, w - 2):
                if y0 + 1 < h: v[y0 + 1, xn + 1 if xn == 0 else xn] = 1.0
        v += self.vfall(h, 0.6, 0.6)
        return C(Rm, v), np.ones((h, w), bool)

    def wicker(self, Rm, w, h, cat):
        yy, xx = grid(w, h)
        if cat == "up":
            v = 3.6 + 0.6 * ((xx + yy) % 2 == 0) - np.clip(np.maximum(np.abs(xx + 0.5 - w / 2) / (w / 2),
                                                                   np.abs(yy + 0.5 - h / 2) / (h / 2)) - 0.7, 0, 1) * 2
            return C(Rm, v), np.ones((h, w), bool)
        row = yy // 2; ph = (xx + row * 2) % 4
        v = 3.3 + LO[cat] + np.where(ph < 2, 0.5, -0.3) + np.where(yy % 2 == 0, 0.25, -0.2)
        v[:2, :] = 4.3 + LO[cat] - (np.arange(min(2, h))[:, None] * 0.6)                         # rim
        v += self.vfall(h, 0.5, 0.8) + self.noise(w, h, 0.1)
        return C(Rm, v), np.ones((h, w), bool)

    def barrel(self, Rm, w, h, cat):
        yy, xx = grid(w, h)
        if cat in ("up", "down"):
            r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) / (min(w, h) / 2)
            v = 3.8 + LO[cat] - r * 1.0 + 0.4 * ((xx // 3) % 2) - (r > 0.85) * 0.8
            return C(Rm, v + self.noise(w, h, 0.1)), np.ones((h, w), bool)
        bulge = 1 - np.abs((yy + 0.5) / h - 0.5) * 2
        v = 2.8 + LO[cat] + bulge * 0.8 + np.where(xx % 3 == 0, -0.9, 0) + 0.2 * np.sin(yy * 0.9 + xx * 2.0)
        v -= np.abs((xx + 0.5) / w - 0.5) * 1.4
        rgb = C(Rm, v + self.noise(w, h, 0.1))
        for f in (0.18, 0.78):
            y0 = int(h * f)
            rgb[y0:y0 + 2] = C(R["iron"], np.full((min(2, h - y0), w), 3.6 + LO[cat]) - np.arange(min(2, h - y0))[:, None])
            if y0 < h: rgb[y0, ::4] = R["iron"][5]
        return rgb, np.ones((h, w), bool)

    def sack(self, Rm, w, h, cat):
        yy, xx = grid(w, h)
        rgb, a = self.form(Rm, w, h, cat, 3.4, noise=0.0)
        v = 3.4 + LO[cat] + 0.6 - (np.maximum(np.abs((xx + 0.5) / w - 0.5), np.abs((yy + 0.5) / h - 0.5)) * 2) ** 2 * 1.3
        v += np.where((xx + yy) % 2 == 0, 0.2, -0.15) + 0.35 * np.sin(xx * 0.9 + yy * 0.2)       # weave + folds
        if cat == "lit" and w > 6 and h > 6:                                                     # stamped wheat
            cx = w // 2
            for y in range(h // 3, h - h // 4): v[y, cx] -= 1.2
            for y in range(h // 3, h // 2, 2): v[y, cx - 1] -= 1.0; v[y, cx + 1] -= 1.0
        return C(Rm, v + self.noise(w, h, 0.1)), a

    def crust(self, Rm, w, h, cat, scores=3, flour=True, braid=False):
        rgb, a = self.form(Rm, w, h, cat, 3.6, noise=0.05)
        yy, xx = grid(w, h)
        v = np.zeros((h, w))
        if cat == "up":
            if braid:
                v += np.where(((xx + (yy % 2) * 2) // 2) % 2 == 0, 0.6, -0.6)
            else:
                for k in range(scores):
                    x0 = (k + 0.5) * w / scores
                    m = np.abs((xx + 0.5 - x0) - (yy + 0.5 - h / 2) * 0.6) < 0.7
                    v[m] += 1.2
                    m2 = np.abs((xx + 1.5 - x0) - (yy + 0.5 - h / 2) * 0.6) < 0.6
                    v[m2 & ~m] -= 0.7
        rgb = C(Rm, 3.6 + LO[cat] + 0.6 - np.clip(np.maximum(np.abs((xx + 0.5) / w - .5), np.abs((yy + .5) / h - .5)) * 2, 0, 1) ** 2 * 1.4
                + v + self.noise(w, h, 0.06) + (0 if cat == "up" else -np.clip((yy + 0.5) / h - 0.6, 0, 1) * 1.5))
        if flour and cat == "up":
            for _ in range(max(1, w * h // 12)):
                x, y = int(self.nr.integers(0, w)), int(self.nr.integers(0, h)); rgb[y, x] = R["sponge"][6]
        return rgb, a

    def pie(self, w, h, cat, filling="berry"):
        Rc, Rf = R["crust"], R[filling]
        if cat != "up":
            return self.crust(Rc, w, h, cat, flour=False)
        yy, xx = grid(w, h)
        edge = (xx < 1) | (yy < 1) | (xx >= w - 1) | (yy >= h - 1)
        lattice = ((xx % 3) == 1) | ((yy % 3) == 1)
        rgb = C(Rf, 3.0 + 0.5 * np.sin(xx + yy * 1.7) + self.noise(w, h, 0.2))
        lv = 4.2 - 0.3 * ((xx + yy) % 3 == 0)
        rgb[lattice] = C(Rc, np.full((h, w), lv))[lattice]
        rgb[edge] = C(Rc, 4.8 - ((xx + yy) % 2) * 0.8)[edge]
        return rgb, np.ones((h, w), bool)

    def frosting(self, Rm, w, h, cat, sponge="sponge", sprinkles=True):
        """Cake tier: frosting top, sponge sides with a frosted rim and drips."""
        if cat == "up":
            rgb, a = self.form(Rm, w, h, cat, 4.0, noise=0.06)
            if sprinkles:
                for _ in range(max(2, w * h // 8)):
                    x, y = int(self.nr.integers(0, w)), int(self.nr.integers(0, h))
                    rgb[y, x] = BLOOMS[int(self.nr.integers(0, len(BLOOMS)))][3]
            return rgb, a
        rgb, a = self.form(R[sponge], w, h, cat, 3.4)
        fr, _ = self.form(Rm, w, h, cat, 3.8)
        yy, xx = grid(w, h)
        drip = (yy < 1 + ((np.sin(xx * 1.9) + 1) * 0.9).astype(int)) | (yy >= h - 1)
        rgb[drip] = fr[drip]
        return rgb, a

    def glass(self, Rm, w, h, cat, glow=True):
        """Potion bottle body: the whole liquid glows (bright, near white centre), a glass reflection streak, a
        darker meniscus line at the top."""
        yy, xx = grid(w, h)
        if cat in ("up", "down"):
            r = np.hypot(xx + 0.5 - w / 2, yy + 0.5 - h / 2) / (max(w, h) / 2)
            return C(Rm, 5.0 - r * 2 + LO[cat] * 0.5), np.ones((h, w), bool)
        cx = np.abs((xx + 0.5) / w - 0.5) * 2
        v = (4.6 if glow else 3.4) - cx ** 2 * 1.6 - (yy + 0.5) / h * 0.9 + LO[cat] * 0.5
        rgb = C(Rm, v)
        if h >= 3: rgb[0] = C(Rm, np.full(w, 2.4))
        if w >= 3: rgb[1:max(2, h - 1), max(0, w // 4)] = R["chalk"][6]
        return rgb, np.ones((h, w), bool)

    def book(self, Rm, w, h, cat):
        rgb, a = self.form(Rm, w, h, cat, 3.2)
        yy, xx = grid(w, h)
        if cat == "lit" and h >= 2:                                    # gold bands on the spine
            for x in (1, w - 2):
                if 0 <= x < w: rgb[:, x] = R["gold"][4]
        if cat == "shade":
            rgb[:, :] = C(R["paper"], 4.0 - (yy % 2) * 0.7 - np.abs((xx + .5) / w - .5))
        return rgb, a

    def pages(self, w, h, cat):
        """An open book seen from above: two cream pages with lines of writing and a gutter shadow."""
        yy, xx = grid(w, h)
        v = 4.6 - np.abs((xx + 0.5) / w - 0.5) * -1.0 - (np.abs(xx + 0.5 - w / 2) < 1) * 1.6
        rgb = C(R["paper"], v + self.noise(w, h, 0.08))
        for y in range(1, h - 1, 2):
            for x in range(1, w - 1):
                if abs(x + 0.5 - w / 2) > 1.2 and self.nr.random() < 0.6: rgb[y, x] = R["plum_paint"][2]
        return rgb, np.ones((h, w), bool)

    def cloth(self, Rm, w, h, cat, motif=None, Rb=None, fold=5, hem=True, fringe=False):
        """Fabric: soft vertical folds, a pattern following the folds, a darker hem, optional hard alpha fringe."""
        yy, xx = grid(w, h); Rb = Rb or R["gold"]
        fv = 0.45 * np.cos((xx + 0.5) * 2 * math.pi / fold)
        v = 3.4 + LO[cat] + fv - np.abs((xx + 0.5) / w - 0.5) * 0.8 + self.vfall(h, 0.7, 0.6) + self.noise(w, h, 0.08)
        if cat == "up": v = 3.9 + 0.3 * np.cos(xx * 1.3) + self.noise(w, h, 0.08)
        rgb = C(Rm, v)
        pm = np.zeros((h, w), bool)
        if motif == "damask":
            pm = (((xx + (yy // 4) * 2) % 4 == 0) & (yy % 4 == 1)) | (((xx + (yy // 4) * 2) % 4 == 1) & (yy % 4 == 2))
        elif motif == "stripe":
            pm = (xx % 6) < 2
        elif motif == "check":
            pm = ((xx // 2) % 2 == 0) ^ ((yy // 2) % 2 == 0)
        elif motif == "polka":
            pm = ((xx + (yy // 3 % 2) * 2) % 4 == 1) & (yy % 3 == 1)
        elif motif == "diamond":
            u = (xx % 6) - 2.5; t = (yy % 6) - 2.5; pm = np.abs(np.abs(u) + np.abs(t) - 2) < 0.6
        if pm.any():
            rgb[pm] = C(Rb, v + 0.4)[pm] if motif != "check" else C(Rm, v - 1.0)[pm]
        if hem and cat in ("lit", "shade") and h >= 4:
            rgb[-2:] = C(Rb, v[-2:] + 0.2)
        a = np.ones((h, w), bool)
        if fringe and cat in ("lit", "shade") and h >= 4:
            a[-1, 1::2] = False
        return rgb, a

    def bolt(self, Rm, w, h, cat, motif=None):
        """Bolt of cloth standing up: wound layers on the sides, a spiral of layers round a card core on the ends."""
        yy, xx = grid(w, h)
        if cat in ("up", "down"):
            r = np.maximum(np.abs(xx + 0.5 - w / 2), np.abs(yy + 0.5 - h / 2))
            v = 3.6 + LO[cat] * 0.5 + np.where(np.floor(r) % 2 == 0, 0.5, -0.5)
            rgb = C(Rm, v); rgb[r < 0.9] = R["paper"][2]
            return rgb, np.ones((h, w), bool)
        return self.cloth(Rm, w, h, cat, motif, fold=w, hem=False)

    def leafy(self, Rm, w, h, cat, flower=None):
        rgb = C(Rm, 3.0 + LO[cat] + self.noise(w, h, 0.9, 3))
        if flower is not None:
            for _ in range(max(1, w * h // 6)):
                x, y = int(self.nr.integers(0, w)), int(self.nr.integers(0, h)); rgb[y, x] = flower[min(len(flower) - 1, int(self.nr.integers(3, 6)))]
        return rgb, np.ones((h, w), bool)

    def chalkboard(self, w, h, cat, doodle="loaf"):
        """Slate in a wood frame with chalk writing (squiggle words) and a doodle; chalk dust smudges."""
        if cat not in ("lit", "shade"):
            return self.form(R["oak"], w, h, cat, 3.4)
        yy, xx = grid(w, h)
        rgb, _ = self.form(R["oak"], w, h, cat, 3.6)
        inner = (xx >= 1) & (xx < w - 1) & (yy >= 1) & (yy < h - 1)
        sv = 3.0 + self.blotches(w, h, 3, -0.6, 2, 5) + self.noise(w, h, 0.15)
        rgb[inner] = C(R["slate_board"], sv)[inner]
        ch = R["chalk"]
        for y in range(3, h - 3, 3):                                               # words
            x = 2
            while x < w - 3:
                L = int(self.nr.integers(2, 5))
                for k in range(L):
                    if x + k < w - 2: rgb[y + (k % 2) * (1 if self.nr.random() < 0.3 else 0), x + k] = ch[int(self.nr.integers(3, 6))]
                x += L + 1
        if doodle and h > 12:
            cy, cx = 2, w // 2
            for dx in range(-3, 4): rgb[cy + 1, cx + dx] = ch[5]
            rgb[cy, cx - 2:cx + 3] = ch[4]
        return rgb, np.ones((h, w), bool)

    def tag(self, w, h, cat):
        rgb, a = self.form(R["paper"], w, h, cat, 4.0)
        if cat in ("lit", "shade") and w >= 3:
            rgb[h // 2, 1:w - 1] = R["walnut"][2]
        return rgb, a

    # ------------------------------------------------------------ awnings
    def stripes(self, A, B, w, h, sw, off, light, pin=None, rowv=None):
        """Awning cloth: stripes `sw` px wide starting at px `off`; each stripe bulges (light centre, darker seams)
        with stitch dashes along the seams; soft wrinkles; rowv (h,) adds a gradient along the length."""
        yy, xx = grid(w, h)
        u = xx - off; si = np.floor(u / sw).astype(int); loc = ((u % sw) + 0.5) / sw
        v = 3.3 + light + 0.55 * np.sin(math.pi * loc) - 0.3
        v -= 0.8 * ((u % sw) == 0)
        v -= 0.4 * (((u % sw) == 1) & (yy % 3 == 0))
        v += 0.18 * np.sin(yy * 0.55 + si * 1.7) * np.sin(xx * 0.25 + si)
        if rowv is not None: v += rowv[:, None]
        v += self.blotches(w, h, max(1, w * h // 1600), 0.25, 3, 10) + self.noise(w, h, 0.08)
        rgb = C(A, v); bm = (si % 2) == 1
        rgb[bm] = C(B, v)[bm]
        if pin is not None:
            pm = bm & ((u % sw) == sw // 2); rgb[pm] = C(pin, v + 0.3)[pm]
        return rgb, np.ones((h, w), bool)

    def valance(self, A, B, w, h, sw, off, style="scallop", trim=None, pin=None, light=0.1, cut=3):
        """Hanging valance: a braided trim band on top, stripes matching the awning, and a hard alpha hem:
        scallops (one per stripe), zigzag points, or flat with tassels."""
        yy, xx = grid(w, h)
        rowv = -np.clip((np.arange(h) - 2) / max(1, h - 2), 0, 1) * 0.9
        rgb, _ = self.stripes(A, B, w, h, sw, off, light, pin, rowv)
        u = xx - off; loc = ((u % sw) + 0.5) / sw
        if style == "scallop": depth = cut * (1 - np.sqrt(np.clip(1 - (2 * loc - 1) ** 2, 0, 1)))
        elif style == "zigzag": depth = cut * np.abs(2 * loc - 1)
        else: depth = np.zeros_like(loc)
        depth = np.round(depth).astype(int)
        a = yy < h - depth
        edge = a & (yy >= h - depth - 1)
        rgb[edge] = (rgb[edge] * 0.82).astype(np.uint8)
        if trim is not None:
            tr = C(trim, 4.0 + np.where((xx + yy) % 3 == 0, 0.9, 0) - yy * 0.6)
            rgb[:2] = tr[:2]
            tm = ((u % sw) == 0) & (yy >= h - cut - 1)                               # tassels at the seams
            if style != "scallop": tm = ((u % sw) == sw // 2) & (yy >= h - 2)
            rgb[tm] = C(trim, 4.4 - (yy - (h - cut)) * 0.5)[tm]; a = a | tm
        return rgb, a

    def pennant(self, Rm, w, h, cat, motif=True):
        """Bunting triangle pointing down, hard alpha, centre light with a cream dot."""
        yy, xx = grid(w, h)
        half = (1 - (yy + 0.5) / h) * w / 2
        a = np.abs(xx + 0.5 - w / 2) <= half + 0.25
        v = 3.6 + LO[cat] - np.abs(xx + 0.5 - w / 2) / max(1, w / 2) * 0.9 - (yy + 0.5) / h * 0.6
        rgb = C(Rm, v)
        if motif and h >= 4: rgb[h // 3, w // 2 - 1:w // 2 + 1] = R["canvas"][6]
        return rgb, a

    def flag(self, Rm, Rb, w, h, cat):
        """Swallowtail flag: wave shading, a stripe, the tail cut out with hard alpha."""
        yy, xx = grid(w, h)
        v = 3.5 + LO[cat] + 0.6 * np.sin(xx * 0.8) - np.abs((yy + 0.5) / h - 0.5) * 0.8
        rgb = C(Rm, v)
        sm = np.abs(yy + 0.5 - h / 2) < h / 6; rgb[sm] = C(Rb, v + 0.3)[sm]
        a = ~((xx > w * 0.7) & (np.abs(yy + 0.5 - h / 2) < (xx - w * 0.7) * 0.9))
        return rgb, a

    # ------------------------------------------------------------ signs
    def sign(self, Rm, w, h, cat, icon="apple", arch=False, frame=None):
        """Painted shop sign: boards, a raised lighter frame, the icon with a soft drop shadow."""
        if cat not in ("lit", "shade"):
            return self.form(Rm, w, h, cat, 3.4)
        rgb, _ = self.boards(Rm, w, h, LO[cat], orient="h", bw=3, nails=False, shadow_top=False)
        yy, xx = grid(w, h)
        fr = frame or R["gold"]
        rim = ((xx == 1) | (yy == 1) | (xx == w - 2) | (yy == h - 2)) & (xx >= 1) & (yy >= 1) & (xx <= w - 2) & (yy <= h - 2)
        rgb[rim] = C(fr, 4.2 - (yy[rim] / h) * 1.2)
        mask, col = ICONS[icon](w - 6, h - 6)
        ih, iw = mask.shape; oy, ox = (h - ih) // 2, (w - iw) // 2
        sh = np.zeros((h, w), bool); sh[oy + 1:oy + 1 + ih, ox + 1:ox + 1 + iw] = mask
        rgb[sh] = (rgb[sh] * 0.7).astype(np.uint8)
        sub = rgb[oy:oy + ih, ox:ox + iw]; sub[mask] = col[mask]
        a = np.ones((h, w), bool)
        if arch:
            r0 = w / 2; a = ~((yy + 0.5 < r0 * 0.5) & (np.hypot((xx + 0.5 - w / 2) / (w / 2), (r0 * 0.5 - yy - 0.5) / (r0 * 0.5)) > 1))
        return rgb, a

    def wheel_face(self, Rm, w, h, cat):
        return self.form(Rm, w, h, cat, 3.3)


# ---------------------------------------------------------------- icons (procedural pixel art)
def _disk(w, h, cx, cy, rx, ry):
    yy, xx = grid(w, h); return ((xx + 0.5 - cx) / rx) ** 2 + ((yy + 0.5 - cy) / ry) ** 2 <= 1


def _shade(Rm, w, h, mask, cx, cy, r, base=3.6):
    yy, xx = grid(w, h)
    d = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy) / r
    v = base + 1.2 * (1 - d) - 0.5 * ((xx + 0.5 - cx) + (yy + 0.5 - cy)) / r
    return C(Rm, v)


def icon_apple(w, h):
    s = min(w, h); w = h = s
    r = s * 0.38; cx, cy = s / 2, s * 0.58
    m = _disk(w, h, cx - r * 0.35, cy, r * 0.75, r) | _disk(w, h, cx + r * 0.35, cy, r * 0.75, r)
    col = _shade(R["apple"], w, h, m, cx - r * 0.3, cy - r * 0.3, r * 1.3)
    hx, hy = int(cx - r * 0.45), int(cy - r * 0.4); col[hy, hx] = R["apple"][6]
    st = np.zeros((h, w), bool); st[int(cy - r - 1.5):int(cy - r + 1), int(cx)] = True
    lf = _disk(w, h, cx + 2.0, cy - r - 0.5, 1.8, 1.0)
    m2 = m | st | lf
    col[st] = R["oak"][1]; col[lf & ~m] = R["cabbage"][4]
    return m2, col


def icon_loaf(w, h):
    rx, ry = w * 0.45, h * 0.32; cx, cy = w / 2, h * 0.55
    m = _disk(w, h, cx, cy, rx, ry)
    yy, xx = grid(w, h)
    col = C(R["crust"], 3.8 + 1.0 * (1 - np.hypot((xx + .5 - cx) / rx, (yy + .5 - cy + ry * 0.3) / ry)) - (yy + .5 - cy) / ry * 0.8)
    for k in (-1, 0, 1):
        sm = np.abs((xx + 0.5 - cx - k * rx * 0.55) - (yy + 0.5 - cy) * 0.7) < 0.6
        col[sm & m] = R["crust"][6]
    base = m & (yy + 0.5 > cy + ry * 0.55); col[base] = R["crust"][2]
    return m, col


def icon_potion(w, h):
    s = min(w, h); W = H = s
    yy, xx = grid(W, H)
    cx = W / 2; r = s * 0.34; cy = H - r - 0.5
    body = _disk(W, H, cx, cy, r, r)
    neck = (np.abs(xx + 0.5 - cx) < max(1, s * 0.1)) & (yy + 0.5 > cy - r - s * 0.22) & (yy + 0.5 < cy)
    cork = (np.abs(xx + 0.5 - cx) < max(1, s * 0.13)) & (yy + 0.5 > cy - r - s * 0.34) & (yy + 0.5 <= cy - r - s * 0.2)
    m = body | neck | cork
    col = _shade(R["glow_violet"], W, H, body, cx - r * 0.3, cy + r * 0.2, r * 1.2, 3.8)
    lvl = body & (yy + 0.5 < cy - r * 0.15); col[lvl] = C(R["glass"], np.full((H, W), 4.6))[lvl]
    col[neck] = R["glass"][5]; col[cork] = R["cork"][4]
    hx, hy = int(cx - r * 0.5), int(cy); col[hy, hx] = R["chalk"][6]
    return m, col


def icon_spool(w, h):
    yy, xx = grid(w, h)
    cx = w / 2; tw, th = w * 0.36, h * 0.8
    top = h / 2 - th / 2
    thread = (np.abs(xx + 0.5 - cx) < tw / 2) & (yy + 0.5 > top + 1) & (yy + 0.5 < top + th - 1)
    flange = (np.abs(xx + 0.5 - cx) < tw / 2 + 1.2) & ((np.abs(yy + 0.5 - top - 0.5) < 1) | (np.abs(yy + 0.5 - top - th + 0.5) < 1))
    needle = (np.abs((xx + 0.5) - (w - 1 - (yy + 0.5) * 0.8)) < 0.6) & (yy > h * 0.1) & (yy < h * 0.95)
    m = thread | flange | needle
    col = C(R["rose"], 3.8 + np.where(yy % 2 == 0, 0.6, -0.4) - np.abs(xx + .5 - cx) / tw)
    col[flange] = C(R["oak"], np.full((h, w), 4.4))[flange]
    col[needle & ~thread & ~flange] = R["iron"][6]
    return m, col


def icon_moon(w, h):
    s = min(w, h); W = H = s
    yy, xx = grid(W, H)
    m = _disk(W, H, W * 0.45, H / 2, s * 0.42, s * 0.42) & ~_disk(W, H, W * 0.62, H * 0.42, s * 0.36, s * 0.36)
    col = C(R["gold"], 4.6 - np.hypot(xx - W * 0.3, yy - H * 0.5) / s * 2)
    for sx, sy in ((0.78, 0.7), (0.85, 0.3)):
        x, y = int(W * sx), int(H * sy)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            if 0 <= x + dx < W and 0 <= y + dy < H: m[y + dy, x + dx] = True; col[y + dy, x + dx] = R["gold"][6 if (dx, dy) == (0, 0) else 5]
    return m, col


def icon_wheat(w, h):
    yy, xx = grid(w, h); cx = w / 2
    stalk = (np.abs(xx + 0.5 - cx) < 0.6) & (yy > h * 0.35)
    m = stalk.copy(); col = C(R["awn_honey"], np.full((h, w), 4.0))
    for i, y in enumerate(range(1, int(h * 0.6), 2)):
        for sdx in (-1, 1):
            x = int(cx + sdx * 1.0 - (0 if sdx < 0 else 1))
            if 0 <= x < w: m[y, x] = True; col[y, x] = R["awn_honey"][5 if sdx < 0 else 4]
        m[y, int(cx)] = True; col[y, int(cx)] = R["awn_honey"][6]
    return m, col


ICONS = {"apple": icon_apple, "loaf": icon_loaf, "potion": icon_potion, "spool": icon_spool, "moon": icon_moon,
         "wheat": icon_wheat}


# ---------------------------------------------------------------- the stall builder
class Stall(House):
    def __init__(self, name, seed, mats, tex=512):
        super().__init__(name, seed, mats, tex)
        self.P = StallPainter(self.nr)
        self._mat_painters_fix()

    def _mat_painters_fix(self):
        # House swatch lambdas captured the old Painter; it is the same class family, so rebuild them on the new one
        old = self.P
        self.m.rects.clear(); self.sizes.clear()
        for mat, spec in self.mats.items():
            self._swatches(mat, spec)

    # ---- small painted items: every face gets a rect keyed by tag, face category and size (shared when equal)
    def item(self, name, grp, frm, to, tag, painter, hide=("down",), rot=(0, 0, 0), origin=None, over=None):
        frm = [float(v) for v in frm]; to = [float(v) for v in to]
        fs = {}
        for f in ("north", "east", "south", "west", "up", "down"):
            if f in hide: fs[f] = None; continue
            if over and f in over: fs[f] = over[f]; continue
            a, b = DIMS[f]
            w, h = px(to[a] - frm[a]), px(to[b] - frm[b])
            if w == 0 or h == 0: fs[f] = None; continue
            cat = CAT[f]
            key = f"{tag}_{cat}_{w}x{h}"
            self.rect(key, w, h, lambda W, H, c=cat: painter(W, H, c))
            fs[f] = F(key)
        return self.m.cube(name, grp, frm, to, fs, rot, origin)

    def card(self, name, grp, frm, to, key, faces=("north", "south"), rot=(0, 0, 0), origin=None, mirror_back=True):
        """Zero thickness card with a dedicated painted rect on its two faces (hard alpha)."""
        fs = {f: None for f in ("north", "east", "south", "west", "up", "down")}
        for i, f in enumerate(faces):
            fs[f] = F(key, mirror=(mirror_back and i == 1))
        return self.m.cube(name, grp, [float(v) for v in frm], [float(v) for v in to], fs, rot, origin)

    # ---- awning slab: a thin rotated cloth slab hinged at (y0, z0); toward -1 = north, +1 = south
    def slab(self, name, grp, x1, x2, y0, z0, L, ang, t, top_key, under_key, edge_mat, toward=-1, top_sub=None, under_sub=None):
        a = -abs(ang) if toward < 0 else abs(ang)
        if toward < 0: frm, to = [x1, y0 - t, z0 - L], [x2, y0, z0]
        else: frm, to = [x1, y0 - t, z0], [x2, y0, z0 + L]
        fs = self.faces(frm, to, edge_mat, ("south" if toward < 0 else "north",), f"{name}e")
        fs["up"] = F(top_key, sub=top_sub); fs["down"] = F(under_key, sub=under_sub)
        self.m.cube(name, grp, frm, to, fs, (a, 0, 0), [(x1 + x2) / 2, y0, z0])
        s, c = math.sin(math.radians(abs(ang))), math.cos(math.radians(abs(ang)))
        return y0 - L * s, z0 + toward * L * c                      # front edge (top surface)

    @staticmethod
    def under_y(y0, z0, z, ang, t):
        """Underside height of a slab hinged at (y0, z0) sloping down by ang, at depth z."""
        a = math.radians(ang)
        return y0 - abs(z0 - z) * math.tan(a) - t / math.cos(a)

    def lantern_hang(self, name, grp, x, y, z, chain=3.0):
        """Hanging lantern: chain, cap with a ring, glowing cage, base."""
        g = self.group(name, [x, y, z], grp)
        self.box(f"{name}_chain", g, [x - 0.25, y - chain, z - 0.25], [x + 0.25, y, z + 0.25], "iron", (), "lchain")
        yb = y - chain
        self.box(f"{name}_cap", g, [x - 1.5, yb - 1, z - 1.5], [x + 1.5, yb, z + 1.5], "iron", (), "lcap2")
        gk = self.rect("lantern_glow_hang", 4, 6, lambda W, H: self.P.form(R["glow"], W, H, "lit", 4.3, noise=0.05, vert=-0.6))
        fs = {f: F(gk) for f in ("north", "east", "south", "west")}; fs["up"] = None; fs["down"] = None
        self.m.cube(f"{name}_glow", g, [x - 1, yb - 4, z - 1], [x + 1, yb - 1, z + 1], fs)
        for i, (dx, dz) in enumerate(((-1, -1), (1, -1), (-1, 1), (1, 1))):
            self.box(f"{name}_bar_{i + 1}", g, [x + dx * 1.0 - 0.25, yb - 4, z + dz * 1.0 - 0.25],
                     [x + dx * 1.0 + 0.25, yb - 1, z + dz * 1.0 + 0.25], "iron", ("up", "down"), "lbar")
        self.box(f"{name}_base", g, [x - 1.5, yb - 5, z - 1.5], [x + 1.5, yb - 4, z + 1.5], "iron", (), "lbase")
        return g

    def wheel(self, name, grp, x1, x2, cy, cz, Rr, rim="wheel", spoke="wheel", hub="iron"):
        """Cart wheel: 8 rim planks round a circle (alternating thickness so overlaps never share a plane),
        4 crossed spokes, a hub with an iron cap."""
        g = self.group(name, [(x1 + x2) / 2, cy, cz], grp)
        seg = h2(2 * Rr * math.tan(math.radians(22.5)) + 1.0)
        for k in range(8):
            phi = k * 45.0
            yc, zc = cy + Rr * math.cos(math.radians(phi)), cz + Rr * math.sin(math.radians(phi))
            ins = 0.0 if k % 2 == 0 else 0.25
            frm = [x1 + ins, yc - 0.75, zc - seg / 2]; to = [x2 - ins, yc + 0.75, zc + seg / 2]
            rot = ((phi + 90) % 180) - 90
            self.box(f"{name}_rim_{k + 1}", g, frm, to, rim, (), f"{name}rim{k % 2}", rot=(rot, 0, 0), origin=[(x1 + x2) / 2, yc, zc])
        for k in range(4):
            ang = k * 45.0 - (90 if k >= 2 else 0) if False else [0, 45, 90, -45][k]
            ins = 0.25 + 0.125 * 0
            self.box(f"{name}_spoke_{k + 1}", g, [x1 + 0.25 + (0.25 if k % 2 else 0), cy - 0.5, cz - Rr + 0.5],
                     [x2 - 0.25 - (0.25 if k % 2 else 0), cy + 0.5, cz + Rr - 0.5], spoke, (), f"{name}sp",
                     rot=(ang, 0, 0), origin=[(x1 + x2) / 2, cy, cz])
        self.box(f"{name}_hub", g, [x1 - 0.5, cy - 1.5, cz - 1.5], [x2 + 0.5, cy + 1.5, cz + 1.5], spoke, (), "hub")
        xm = x2 + 0.5 if x1 > 0 else x1 - 1.5
        self.box(f"{name}_hub_cap", g, [xm, cy - 1, cz - 1], [xm + 1, cy + 1, cz + 1], hub, (), "hubcap")
        return g


def stall_mats(post="walnut", plank="oak", top="walnut", trim="paint_cream", trim_kind="carved", extra=None):
    d = {
        "post": {"kind": "boards", "ramp": R[post], "side": (48, 80), "top": (16, 16), "no_lit2": True,
                 "extra": {"orient": "v", "bw": 2, "lap": False, "shadow_top": False}},
        "plank": {"kind": "boards", "ramp": R[plank], "side": (72, 40), "top": (64, 40), "no_lit2": True,
                  "extra": {"bw": 3, "shadow_top": False}},
        "top": {"kind": "boards", "ramp": R[top], "side": (72, 8), "top": (80, 32), "no_lit2": True,
                "extra": {"bw": 3, "shadow_top": False}},
        "trim": {"kind": trim_kind, "ramp": R[trim], "side": (72, 12), "top": (32, 12), "no_lit2": True,
                 "extra": {"motif": "diamond"} if trim_kind == "carved" else {}},
        "iron": {"kind": "metal", "ramp": R["iron"], "side": (24, 16), "top": (16, 16), "no_lit2": True},
        "gold": {"kind": "metal", "ramp": R["gold"], "side": (24, 16), "top": (16, 16), "no_lit2": True},
        "stone": {"kind": "ashlar", "ramp": R["stone"], "side": (40, 12), "top": (24, 24), "no_lit2": True},
    }
    d.update(extra or {})
    return d
