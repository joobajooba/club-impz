"""Fantasy houses for the hub (blockbench_detailed_prompts.md sections 1, 2, 3.11, 4, 5), built the same way as
hub_castle v2: every material is painted once as a few big swatches (lit / lit2 / shade / top / under), and each cube
face is a crop of the right swatch, so a 512 texture holds a whole house at 2 px per unit.

Painters follow the house style (section 1.5.1): ramps of 7 hue shifted shades, each brick / board / tile shaded
light on top and dark underneath, soft contact shadows, material detail (mortar, chips, grain, knots, nails, moss,
soot), low noise last. Front = north (-z); light from the top, front left (north and east faces are the lit ones)."""
import json, math, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from foliage_lib import Model, F, ramp, ramp_colour, px, h2

# ---------------------------------------------------------------- ramps (7 shades, hue shifted: shadows richer)
R = {
    "brick_red": ramp("#3a1214 #5c1c1a #7e2b22 #9e3d2c #b9533a #cd6c4c #de8a66"),
    "brick_blue": ramp("#141c3c #1d2d56 #283f72 #34548c #456ba4 #5f88ba #82a8d0"),
    "brick_honey": ramp("#4a2a10 #6c4016 #92591e #b4762a #cc923a #dfae56 #ecc87c"),
    "brick_plum": ramp("#2c1222 #461c34 #62284a #7e3860 #984c78 #b06890 #c88aac"),
    "mortar": ramp("#4e463e #6a6056 #857a6e #9e9486 #b6ac9e #cac2b4 #dcd6ca"),
    "stone": ramp("#4a4036 #66594b #82735f #9c8c74 #b5a58a #cbbda0 #e0d4ba"),
    "cobble": ramp("#2e2a28 #44403a #5a554e #706a62 #888076 #a0978a #b8ae9e"),
    "tile_teal": ramp("#0c2628 #133c40 #1b5658 #26716e #368c86 #4ea69c #70beb0"),
    "tile_red": ramp("#3a0e10 #581618 #7a2220 #9a3228 #b64632 #cc6244 #de8460"),
    "tile_purple": ramp("#1c1030 #2c1a48 #402862 #56397c #6e4e96 #8a6aae #a88cc6"),
    "tile_moss": ramp("#16220c #223414 #31481c #435f27 #577634 #708f46 #8ca85e"),
    "tile_slate": ramp("#1a2028 #262f3a #343f4c #455161 #586577 #6f7c8e #8b97a6"),
    "oak": ramp("#2a1608 #42240e #5c3416 #78461e #94592a #ad6e3a #c4884e"),
    "walnut": ramp("#1a0e0a #2a1812 #3c241a #503224 #66422e #7c543a #946a4a"),
    "cherry": ramp("#2a0e0c #461812 #64241a #823224 #9c4430 #b45a40 #c87656"),
    "paint_cream": ramp("#5e5648 #7a7262 #968e7c #b0a894 #c8c0aa #dad4c0 #e8e4d4"),
    "paint_teal": ramp("#0e2a2e #164046 #1f585e #2a7076 #3a8a8e #54a4a6 #78bcbc"),
    "paint_white": ramp("#4e5260 #6a6e7c #888c98 #a6aab4 #c0c4cc #d6d8de #e8eaee"),
    "plaster": ramp("#6a5c48 #85765e #a09078 #b8aa90 #cec2a8 #ded4bc #ebe4d0"),
    "log": ramp("#24140a #3a2210 #523218 #6a4422 #82562e #9a6a3c #b2824e"),
    "logend": ramp("#4a3018 #6a4824 #8a6234 #a67c46 #bc945a #d0ac74 #e0c290"),
    "iron": ramp("#16181e #252830 #363a44 #4a4f5a #626874 #7e8490 #9aa0aa"),
    "gold": ramp("#4a2c08 #6e460e #946416 #b8841e #d4a432 #e8c458 #f4dc8a"),
    "glass": ramp("#121c2c #1c2a40 #2a3c58 #3c5274 #546c90 #7088aa #92a8c4"),
    "glow": ramp("#7a3a0a #a8560e #d07a16 #ec9e2a #f8bc4c #fcd27a #fee6aa"),
    "moss": ramp("#1c2a10 #2a3e16 #3a541e #4c6a28 #608234 #789a44 #92b25a"),
    "soil": ramp("#1e140c #2c1e12 #3c2a1a #4e3824 #62482e"),
    "clay_pot": ramp("#4a1c10 #6a2a16 #8c3c1e #a8502a #c06a3a #d4874e #e2a46a"),
}
BLOOMS = [ramp("#5a0e1e #8a1a2c #b82c3c #dc4a52 #f07a78"), ramp("#6a4a08 #9a700e #c89a18 #e8c03a #f8de78"),
          ramp("#3a1a5a #56287e #7440a2 #9462c0 #b48ad8"), ramp("#6a2a4a #964068 #c05c88 #dc80a6 #f0aac6"),
          ramp("#5e5a66 #86828e #aaa8b2 #cac8d0 #e6e4ea")]


def C(Rm, v): return ramp_colour(Rm, np.clip(v, 0, len(Rm) - 1))


class Painter:
    def __init__(self, nr): self.nr = nr

    def noise(self, w, h, amp=0.15, density=40):
        f = np.zeros((h, w)); nr = self.nr
        for _ in range(max(1, w * h // density)):
            x, y = nr.integers(0, w), nr.integers(0, h)
            f[y:y + int(nr.integers(1, 3)), x:x + int(nr.integers(2, 4))] += nr.choice([-1, 1]) * amp
        return f

    def blotches(self, w, h, n, amp, rmin=3, rmax=9):
        """Soft round stains (soot, weathering, damp): a darker area with a smooth falloff."""
        f = np.zeros((h, w)); yy, xx = np.mgrid[0:h, 0:w]
        for _ in range(n):
            cx, cy, r = self.nr.uniform(0, w), self.nr.uniform(0, h), self.nr.uniform(rmin, rmax)
            f -= amp * np.clip(1 - np.hypot((xx - cx) / r, (yy - cy) / (r * 0.7)), 0, 1) ** 1.5
        return f

    @staticmethod
    def vfall(h, start=0.72, amt=0.7):
        yy = np.arange(h)[:, None] / max(1, h - 1)
        return -np.clip((yy - start) / (1 - start), 0, 1) * amt

    def moss_mask(self, w, h, from_bottom=True, amount=0.35):
        """Moss creeping up from the ground (or down from the ridge): clusters thinning out with distance."""
        m = np.zeros((h, w), bool); nr = self.nr
        for _ in range(int(w * amount)):
            x = int(nr.integers(0, w)); L = int(abs(nr.normal(0, h * 0.12))) + 1
            y0 = h - L if from_bottom else 0
            for y in range(y0, min(h, y0 + L)):
                if nr.random() < 0.75:
                    m[y, max(0, x - int(nr.integers(0, 2))):min(w, x + int(nr.integers(1, 3)))] = True
        return m

    # ------------------------------------------------------------ masonry
    def brick(self, Rm, w, h, light, top=False, shadow_top=True, accent=None, moss=True):
        """Running bond bricks 6x3 px (3 x 1.5 units) with 1 px mortar. Each brick its own shade, light top edge,
        darker bottom row, chipped corners, a few glazed accent bricks (fantasy) and burnt ones, soot stains, moss
        creeping up from the ground, a soft shadow band under the eaves."""
        nr = self.nr
        bw, bh = (8, 4) if top else (6, 3)
        base = (4.0 if top else 3.3) + light
        v = np.full((h, w), base); mortar = np.zeros((h, w), bool); acc = np.zeros((h, w), bool)
        for r, y0 in enumerate(range(0, h, bh + 1)):
            off = (bw + 1) // 2 if r % 2 else 0
            for x0 in range(-off, w, bw + 1):
                b = nr.normal(0, 0.28)
                burnt = nr.random() < 0.05
                glazed = accent is not None and nr.random() < 0.06
                xa, xb = max(0, x0), min(w, x0 + bw)
                if xa >= xb: continue
                for yy in range(y0, min(h, y0 + bh)):
                    t = (yy - y0) / max(1, bh - 1)
                    v[yy, xa:xb] = base + b + 0.4 - 0.75 * t - (0.9 if burnt else 0)
                if y0 < h: v[y0, xa:xb] += 0.35
                if x0 >= 0 and y0 < h: v[y0:min(h, y0 + bh), x0] += 0.15          # light left edge
                if glazed: acc[y0:min(h, y0 + bh), xa:xb] = True
                if nr.random() < 0.12 and y0 < h and x0 >= 0: mortar[y0, x0] = True  # chipped corner
                if nr.random() < 0.08 and y0 + bh - 1 < h and x0 + bw - 1 < w: mortar[y0 + bh - 1, x0 + bw - 1] = True
                if 0 <= x0 + bw < w: mortar[y0:min(h, y0 + bh + 1), x0 + bw] = True
            if y0 + bh < h: mortar[y0 + bh, :] = True
        v += self.noise(w, h, 0.12)
        if not top:
            v += self.blotches(w, h, max(1, w * h // 2400), 0.5)
            v += self.vfall(h, 0.7, 0.6)
            if shadow_top: v[:6, :] -= np.linspace(1.1, 0.1, 6)[:, None]
        rgb = C(Rm, v)
        mv = 2.4 + light * 0.4 + self.noise(w, h, 0.25, 20)
        if shadow_top and not top: mv[:6, :] -= np.linspace(1.0, 0.1, 6)[:, None]
        rgb[mortar] = C(R["mortar"], mv)[mortar]
        if accent is not None and acc.any():
            rgb[acc] = C(accent, v + 0.3)[acc]
        if moss and not top:
            mm = self.moss_mask(w, h, True, 0.18) & ~acc
            rgb[mm] = C(R["moss"], 3.2 + light + self.noise(w, h, 0.4, 10))[mm]
        return rgb, np.ones((h, w), bool)

    def ashlar(self, Rm, w, h, light, top=False, shadow_top=False):
        """Dressed stone trim: long blocks 10x5 px, crisp light top and left edges, darker base, 1 px joints."""
        nr = self.nr
        bw, bh = (12, 8) if top else (10, 5)
        base = (4.2 if top else 3.6) + light
        v = np.full((h, w), base); joint = np.zeros((h, w), bool)
        for r, y0 in enumerate(range(0, h, bh + 1)):
            off = (bw + 1) // 2 if r % 2 else 0
            for x0 in range(-off, w, bw + 1):
                b = nr.normal(0, 0.15); xa, xb = max(0, x0), min(w, x0 + bw)
                if xa >= xb: continue
                for yy in range(y0, min(h, y0 + bh)):
                    v[yy, xa:xb] = base + b + 0.35 - 0.7 * (yy - y0) / max(1, bh - 1)
                if y0 < h: v[y0, xa:xb] += 0.5
                if x0 >= 0: v[y0:min(h, y0 + bh), x0] += 0.25
                if 0 <= x0 + bw < w: joint[y0:min(h, y0 + bh + 1), x0 + bw] = True
            if y0 + bh < h: joint[y0 + bh, :] = True
        v += self.noise(w, h, 0.1)
        if shadow_top: v[:4, :] -= np.linspace(0.9, 0.1, 4)[:, None]
        rgb = C(Rm, v); rgb[joint] = C(Rm, np.full((h, w), base - 1.6))[joint]
        return rgb, np.ones((h, w), bool)

    def cobble(self, Rm, w, h, light):
        """Rounded field stones (Voronoi cells): each stone light in its upper middle, dark at its rim, mortar between,
        moss in the gaps near the ground."""
        nr = self.nr
        pts = np.array([(nr.uniform(-4, w + 4), nr.uniform(-4, h + 4)) for _ in range(max(6, w * h // 30))])
        yy, xx = np.mgrid[0:h, 0:w]
        d = np.stack([np.hypot(xx - x, (yy - y) * 1.3) for x, y in pts])
        o = np.sort(d, axis=0); idx = np.argmin(d, axis=0)
        edge = o[1] - o[0]
        cell_b = nr.normal(0, 0.35, len(pts))
        cy = pts[idx][..., 1]
        v = 3.4 + light + cell_b[idx] + np.clip(edge / 3, 0, 1) * 0.6 - np.clip((yy - cy) / 4, -1, 1) * 0.5
        v += self.noise(w, h, 0.12)
        gap = edge < 1.0
        v[gap] = 1.2 + light * 0.3
        rgb = C(Rm, v)
        mm = gap & (self.nr.random((h, w)) < 0.35) & (yy > h * 0.5)
        rgb[mm] = C(R["moss"], np.full((h, w), 2.6))[mm]
        return rgb, np.ones((h, w), bool)

    def plaster(self, Rm, w, h, light, shadow_top=True):
        """Lime plaster: smooth broad mottling, a few hairline cracks, damp darkening at the bottom."""
        v = np.full((h, w), 4.2 + light) + self.blotches(w, h, max(2, w * h // 900), 0.35, 4, 14) + self.noise(w, h, 0.1, 50)
        for _ in range(max(1, w * h // 3000)):                                 # hairline cracks
            x, y = int(self.nr.integers(2, w - 2)), int(self.nr.integers(2, h - 2))
            for _ in range(int(self.nr.integers(4, 10))):
                if 0 <= x < w and 0 <= y < h: v[y, x] -= 0.9
                x += int(self.nr.integers(-1, 2)); y += 1
        v += self.vfall(h, 0.75, 0.8)
        if shadow_top: v[:5, :] -= np.linspace(1.0, 0.1, 5)[:, None]
        return C(Rm, v), np.ones((h, w), bool)

    # ------------------------------------------------------------ roofs
    def shingle(self, Rm, w, h, light, style="scale", accent=None, moss=False):
        """Roof tiles in rows, lighter towards the ridge (top of the swatch).
        scale: fish-scale tiles 4 px wide with round bottoms; slate: 6x4 slates; clay: barrel tiles; shake: wood."""
        nr = self.nr
        v = np.zeros((h, w)); acc = np.zeros((h, w), bool); gap = np.zeros((h, w), bool)
        rh = 4 if style != "shake" else 5
        for r, y0 in enumerate(range(0, h, rh)):
            g = 1.0 - y0 / max(1, h)
            if style == "scale":
                off = 2 if r % 2 else 0
                for x0 in range(-off, w, 4):
                    b = 2.5 + light + g * 1.5 + nr.normal(0, 0.18); is_acc = accent is not None and nr.random() < 0.035
                    for dy in range(rh):
                        yy = y0 + dy
                        if yy >= h: break
                        for dx in range(4):
                            xx = x0 + dx
                            if not 0 <= xx < w: continue
                            if dy == rh - 1 and dx in (0, 3): v[yy, xx] = b - 1.5; gap[yy, xx] = True; continue
                            val = b - 1.1 if dy == 0 else (b + 0.8 if dy == rh - 2 and dx in (1, 2) else b + (0.35 if dx == 1 else 0) - (0.3 if dx == 3 else 0))
                            v[yy, xx] = val
                            if is_acc: acc[yy, xx] = True
            elif style == "slate":
                off = 3 if r % 2 else 0
                for x0 in range(-off, w, 6):
                    b = 2.4 + light + g * 1.6 + nr.normal(0, 0.15)
                    for dy in range(rh):
                        yy = y0 + dy
                        if yy >= h: break
                        v[yy, max(0, x0):min(w, x0 + 6)] = b - 1.4 if dy == 0 else (b + 0.75 if dy == rh - 1 else b)
                        if 0 <= x0 < w and dy > 0: v[yy, x0] = b - 0.7
            elif style == "clay":
                for x0 in range(0, w, 4):
                    b = 2.6 + light + g * 1.3 + nr.normal(0, 0.15)
                    prof = [-0.7, 0.4, 0.6, -0.2] if (x0 // 4) % 2 == 0 else [-1.2, -0.4, -0.2, -0.9]  # over / under tiles
                    for dy in range(rh):
                        yy = y0 + dy
                        if yy >= h: break
                        for dx in range(4):
                            if x0 + dx < w: v[yy, x0 + dx] = b + prof[dx] + (0.6 if dy == rh - 1 else -0.5 if dy == 0 else 0)
            else:  # shake: split wooden shingles of random width with grain
                x0 = -int(nr.integers(0, 3)) if r % 2 else 0
                while x0 < w:
                    sw = int(nr.integers(2, 5)); b = 2.4 + light + g * 1.4 + nr.normal(0, 0.25)
                    for dy in range(rh):
                        yy = y0 + dy
                        if yy >= h: break
                        for dx in range(sw):
                            xx = x0 + dx
                            if 0 <= xx < w:
                                v[yy, xx] = b - (1.2 if dy == 0 else 0) + (0.7 if dy == rh - 1 else 0) - (0.6 if dx == sw - 1 else 0) \
                                            + (0.25 if (xx * 7 + yy) % 5 == 0 else 0)
                    x0 += sw
        v += self.noise(w, h, 0.1)
        rgb = C(Rm, v)
        if accent is not None and acc.any(): rgb[acc] = C(accent, v + 0.2)[acc]
        if moss:
            mm = self.moss_mask(w, h, False, 0.25) | self.moss_mask(w, h, True, 0.12)
            mm &= ~gap
            rgb[mm] = C(R["moss"], 3.0 + light + self.noise(w, h, 0.5, 8))[mm]
        return rgb, np.ones((h, w), bool)

    # ------------------------------------------------------------ wood
    def boards(self, Rm, w, h, light, orient="h", bw=4, lap=True, nails=True, shadow_top=True):
        """Planks bw px wide: worn light lip, grain streaks, knots, nail heads near the joints, a lap shadow under
        each board (clapboard) or a groove between boards."""
        nr = self.nr
        L, S = (h, w) if orient == "h" else (w, h)       # L: across boards, S: along boards
        v = np.zeros((L, S))
        for i, a in enumerate(range(0, L, bw)):
            joints, j = [], int(nr.integers(8, 48))
            while j < S:                                            # long boards: a butt joint every 24 to 64 px
                joints.append(j); j += int(nr.integers(24, 64))
            seg = [0] + joints + [S]
            for s0, s1 in zip(seg[:-1], seg[1:]):
                b = 3.2 + light + nr.normal(0, 0.3)
                ph = nr.uniform(0, 6.28)
                for d in range(bw):
                    yy = a + d
                    if yy >= L: break
                    t = d / max(1, bw - 1)
                    prof = (0.55 if d == 0 else 0) + (0.2 - 0.6 * t) - (1.1 if (lap and d == bw - 1) else 0)
                    xs = np.arange(s0, s1)
                    grain = 0.28 * np.sin(xs * 0.35 + ph + d * 1.7) * np.sin(xs * 0.07 + d)
                    v[yy, s0:s1] = b + prof + grain
                if s1 < S: v[a:a + bw, s1 - 1] -= 1.0                       # butt joint
                if s1 - s0 > 14 and nr.random() < 0.5:                       # knot
                    kx = int(nr.integers(s0 + 4, s1 - 4)); ky = a + bw // 2
                    if ky < L:
                        v[ky, kx - 1:kx + 2] -= 1.1; v[max(0, ky - 1), kx] -= 0.6
                if nails and s1 < S and a + 1 < L:
                    v[a + 1, max(0, s1 - 3)] = 0.8; v[a + 1, min(S - 1, s0 + 2)] = 0.8
            if not lap and a + bw - 1 < L: v[a + bw - 1, :] -= 0.8
        if orient != "h": v = v.T
        v += self.noise(w, h, 0.1)
        if shadow_top: v[:5, :] -= np.linspace(1.0, 0.1, 5)[:, None]
        v += self.vfall(h, 0.8, 0.5)
        return C(Rm, v), np.ones((h, w), bool)

    def logs(self, Rm, w, h, light):
        """Stacked round logs 6 px tall: lit upper half, dark underside, bark streaks, pale chinking between."""
        nr = self.nr
        v = np.zeros((h, w)); chink = np.zeros((h, w), bool)
        for i, y0 in enumerate(range(0, h, 7)):
            b = 3.2 + light + nr.normal(0, 0.2); ph = nr.uniform(0, 6)
            for d in range(6):
                yy = y0 + d
                if yy >= h: break
                prof = [0.1, 0.7, 0.9, 0.5, -0.2, -1.0][d]
                xs = np.arange(w)
                v[yy] = b + prof + 0.3 * np.sin(xs * 0.5 + ph + d * 2.3) * (np.sin(xs * 0.13 + d) > 0.3)
            for _ in range(w // 18):
                kx = int(nr.integers(2, max(3, w - 2)))
                if y0 + 3 < h: v[y0 + 2:y0 + 4, kx] -= 1.0
            if y0 + 6 < h: chink[y0 + 6, :] = True
        v += self.noise(w, h, 0.12)
        v[:5, :] -= np.linspace(0.9, 0.1, 5)[:, None]
        rgb = C(Rm, v); rgb[chink] = C(R["plaster"], np.full((h, w), 3.0 + light))[chink]
        return rgb, np.ones((h, w), bool)

    def log_end(self, w, h):
        """Cut log end: growth rings around an off-centre heart, bark rim, a radial crack."""
        yy, xx = np.mgrid[0:h, 0:w]
        cx, cy = w / 2 - 0.3, h / 2 - 0.2
        r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy)
        v = 4.2 - (r / max(w, h)) * 2.5 + 0.5 * (np.sin(r * 2.6) > 0.4)
        v[r > min(w, h) / 2 - 0.6] = 1.0
        rgb = C(R["logend"], v)
        rgb[(np.abs(xx - cx) < 0.6) & (yy > cy)] = R["logend"][1]
        return rgb, np.ones((h, w), bool)

    def carved(self, Rm, w, h, light, motif="diamond"):
        """Carved trim: a repeating raised motif bevelled with a light top-left and a dark bottom-right."""
        yy, xx = np.mgrid[0:h, 0:w]
        if motif == "diamond":
            p = 8; u = (xx % p) - p / 2 + 0.5; t = (yy % max(4, h)) - h / 2 + 0.5
            bump = np.clip(1 - (np.abs(u) / (p / 2) + np.abs(t) / max(1, h / 2)), 0, 1)
        elif motif == "scallop":
            p = 6; u = (xx % p) - p / 2 + 0.5
            bump = ((yy / max(1, h - 1)) < 1 - (u / (p / 2)) ** 2 * 0.8).astype(float)
        else:  # rope / twist
            bump = 0.5 + 0.5 * np.sin((xx + yy) * 1.2)
        v = 3.3 + light + bump * 0.9
        gx = np.diff(bump, axis=1, prepend=bump[:, :1]); gy = np.diff(bump, axis=0, prepend=bump[:1, :])
        v += (gx + gy) * 0.9                                                    # bevel light from the top left
        v[0, :] += 0.5; v[-1, :] -= 0.7
        v += self.noise(w, h, 0.08)
        return C(Rm, v), np.ones((h, w), bool)

    def flat(self, Rm, w, h, base, edge=True):
        """A plain painted / under-eave surface: centre light, soft darker edges (form gradient)."""
        yy, xx = np.mgrid[0:h, 0:w]
        dx = np.abs((xx + 0.5) / w - 0.5) * 2; dy = np.abs((yy + 0.5) / h - 0.5) * 2
        v = np.full((h, w), float(base)) + self.noise(w, h, 0.1)
        if edge: v -= np.clip(np.maximum(dx, dy) - 0.5, 0, 1) * 1.2
        return C(Rm, v), np.ones((h, w), bool)

    def metal(self, Rm, w, h, base=3.0):
        """Polished metal: a bright band across the upper third, dark lower edge, one hot pixel."""
        yy = np.arange(h)[:, None] / max(1, h - 1)
        v = base + 1.4 * np.exp(-((yy - 0.3) / 0.18) ** 2) - yy * 1.0 + np.zeros((h, w)) + self.noise(w, h, 0.1)
        rgb = C(Rm, v)
        rgb[min(h - 1, h // 3), min(w - 1, w // 3)] = Rm[-1]
        return rgb, np.ones((h, w), bool)

    # ------------------------------------------------------------ openings
    def window(self, frame, w, h, style="leaded", arch=False, fw=2, glow=False):
        """A framed window. leaded: diamond lead lattice; panes: muntin grid. Glass is a cool gradient with a
        diagonal reflection streak and a warm lit lower part (someone is home)."""
        rgb, _ = self.flat(frame, w, h, 4.2)
        a = np.ones((h, w), bool)
        iw, ih = w - 2 * fw, h - 2 * fw
        r = iw / 2
        for y in range(ih):
            for x in range(iw):
                X, Y = fw + x, fw + y
                if arch and y < r:
                    dx_, dy_ = x + 0.5 - r, r - (y + 0.5)
                    if dx_ * dx_ + dy_ * dy_ > r * r: continue
                t = y / max(1, ih - 1)
                gv = 3.6 - t * 1.6 + (0.9 if 0 <= (x + y) - ih * 0.35 < 3 else 0)        # reflection streak
                col = C(R["glass"], gv)
                if glow and t > 0.55: col = C(R["glow"], 2.2 + (t - 0.55) * 4)          # warm light inside
                if style == "leaded" and ((x + y) % 5 == 0 or (x - y) % 5 == 0): col = R["iron"][2]
                if style == "panes" and (x == iw // 2 or y == ih // 2 or (ih > 14 and y in (ih // 4, 3 * ih // 4))):
                    col = C(frame, 3.0)
                if x == 0 or y == 0: col = (np.array(col) * 0.7).astype(np.uint8)       # shadow inside the frame
                rgb[Y, X] = col
        if arch:                                                                       # arched head: corners cut out
            yy, xx = np.mgrid[0:h, 0:w]
            R0 = w / 2
            a = ~((yy + 0.5 < R0) & (np.hypot(xx + 0.5 - w / 2, R0 - (yy + 0.5)) > R0))
        return rgb, a

    def door(self, Rm, w, h, arch=True):
        """Plank door: vertical boards with grooves and grain, two iron strap hinges with curled tips, studs, ring."""
        rgb, _ = self.boards(Rm, w, h, 0.0, orient="v", bw=5, lap=False, nails=False, shadow_top=False)
        I = R["iron"]
        for hy in (int(h * 0.22), int(h * 0.7)):
            rgb[hy:hy + 2, 1:w - 3] = I[3]; rgb[hy + 1, 1:w - 3] = I[2]
            rgb[hy - 1, w - 4] = I[3]; rgb[hy + 2, w - 4] = I[3]                        # curled tip
            for sx in range(3, w - 4, 4): rgb[hy, sx] = I[5]
        cy = int(h * 0.48); cx = int(w * 0.78)
        for dx, dy in ((0, -1), (1, 0), (0, 1), (-1, 0), (1, -1), (-1, 1)):
            if 0 <= cx + dx < w and 0 <= cy + dy < h: rgb[cy + dy, cx + dx] = I[4]
        a = np.ones((h, w), bool)
        if arch:
            yy, xx = np.mgrid[0:h, 0:w]; R0 = w / 2
            a = ~((yy + 0.5 < R0) & (np.hypot(xx + 0.5 - w / 2, R0 - (yy + 0.5)) > R0))
            edge = a & ((yy + 0.5 < R0 + 1) & (np.hypot(xx + 0.5 - w / 2, R0 - (yy + 0.5)) > R0 - 1.2))
            rgb[edge] = C(Rm, np.full((h, w), 1.0))[edge]
        return rgb, a

    def shutter(self, Rm, w, h):
        """Louvred shutter: a frame and slats every 2 px (light lip, dark gap), a heart cut-out near the top."""
        rgb, _ = self.flat(Rm, w, h, 3.8)
        for y in range(2, h - 2):
            if y % 2 == 0: rgb[y, 1:w - 1] = C(Rm, np.full(w - 2, 4.6))
            else: rgb[y, 1:w - 1] = C(Rm, np.full(w - 2, 2.2))
        hx, hy = w // 2, 3
        for dx, dy in ((-1, 0), (1, 0), (0, 1), (0, 0)):
            if 0 <= hx + dx < w and hy + dy < h: rgb[hy + dy, hx + dx] = Rm[0]
        return rgb, np.ones((h, w), bool)

    def flowers(self, w, h):
        """Soil with leaves and flower heads in clusters (top of a window box or planter)."""
        nr = self.nr
        rgb = C(R["soil"], 2.0 + self.noise(w, h, 0.4, 6))
        for _ in range(w * h // 5):
            x, y = int(nr.integers(0, w)), int(nr.integers(0, h)); rgb[y, x] = C(R["moss"], np.array(nr.uniform(2, 5.5)))
        for _ in range(max(2, w * h // 14)):
            x, y = int(nr.integers(0, w - 1)), int(nr.integers(0, h - 1)); B = BLOOMS[int(nr.integers(0, len(BLOOMS)))]
            rgb[y, x] = B[3]; rgb[y, min(w - 1, x + 1)] = B[2]; rgb[min(h - 1, y + 1), x] = B[1]
            if nr.random() < 0.5: rgb[y, x] = B[4]
        return rgb, np.ones((h, w), bool)

    def bloom(self, B, w, h):
        rgb = np.zeros((h, w, 3), np.uint8)
        for y in range(h):
            for x in range(w):
                rgb[y, x] = B[min(4, 2 + (1 if (x + y) % 2 == 0 else 0) + (1 if y == 0 else 0))]
        return rgb, np.ones((h, w), bool)

    def leaves(self, w, h):
        rgb = C(R["moss"], 3.2 + self.noise(w, h, 0.8, 4)); return rgb, np.ones((h, w), bool)

    def round_window(self, frame, w, h):
        """A round (oculus) window with spokes, set in a stone ring."""
        yy, xx = np.mgrid[0:h, 0:w]; cx, cy = w / 2, h / 2
        r = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy); R0 = min(w, h) / 2
        rgb, _ = self.flat(frame, w, h, 4.0)
        inner = r < R0 - 2
        g = C(R["glass"], 3.6 - (yy / h) * 1.8)
        rgb[inner] = g[inner]
        ang = np.degrees(np.arctan2(yy + 0.5 - cy, xx + 0.5 - cx)) % 45
        rgb[inner & ((ang < 6) | (r < 1.5))] = R["iron"][2]
        a = r < R0
        return rgb, a


# ---------------------------------------------------------------- the house builder
DIMS = {"north": (0, 1), "south": (0, 1), "east": (2, 1), "west": (2, 1), "up": (0, 2), "down": (0, 2)}
LIT = {"north", "east"}
OPP = {"north": "south", "south": "north", "east": "west", "west": "east"}


class House:
    """mats: name -> (kind, args, sizes). kind is a Painter method used for lit / lit2 / shade / top / under swatches.
    sizes: (side_w, side_h, top_w, top_h)."""

    def __init__(self, name, seed, mats, tex=512):
        self.name = name
        self.m = Model(name, tex, seed)
        self.rng, self.nr = self.m.rng, self.m.nrng
        self.P = Painter(self.nr)
        self.mats = mats
        self.sizes = {}
        self._off, self._var = {}, [0]
        self.grown = {}
        for mat, spec in mats.items():
            self._swatches(mat, spec)
        self.root = name

    # ---- swatches
    def _swatches(self, mat, spec):
        kind, Rm, sw, sh, tw, th = spec["kind"], spec["ramp"], spec["side"][0], spec["side"][1], spec["top"][0], spec["top"][1]
        P = self.P; extra = spec.get("extra", {})
        variants = {"lit": 0.35, "lit2": 0.25, "shade": -0.55}
        if spec.get("no_lit2"): variants.pop("lit2")
        for var, light in variants.items():
            key = f"{mat}_{var}"
            if kind == "brick": f = lambda w, h, l=light: P.brick(Rm, w, h, l, **extra)
            elif kind == "ashlar": f = lambda w, h, l=light: P.ashlar(Rm, w, h, l, **extra)
            elif kind == "cobble": f = lambda w, h, l=light: P.cobble(Rm, w, h, l)
            elif kind == "plaster": f = lambda w, h, l=light: P.plaster(Rm, w, h, l, **extra)
            elif kind == "shingle": f = lambda w, h, l=light: P.shingle(Rm, w, h, l, **extra)
            elif kind == "boards": f = lambda w, h, l=light: P.boards(Rm, w, h, l, **extra)
            elif kind == "logs": f = lambda w, h, l=light: P.logs(Rm, w, h, l)
            elif kind == "carved": f = lambda w, h, l=light: P.carved(Rm, w, h, l, **extra)
            elif kind == "flat": f = lambda w, h, l=light: P.flat(Rm, w, h, 3.8 + l)
            elif kind == "metal": f = lambda w, h, l=light: P.metal(Rm, w, h, 3.0 + l)
            else: raise ValueError(kind)
            self.m.rect(key, sw, sh, f); self.sizes[key] = (sw, sh)
        key = f"{mat}_top"
        if kind == "brick": f = lambda w, h: P.brick(Rm, w, h, 0.4, top=True, moss=False)
        elif kind == "ashlar": f = lambda w, h: P.ashlar(Rm, w, h, 0.4, top=True)
        elif kind == "shingle": f = lambda w, h: P.shingle(Rm, w, h, 0.8, **extra)
        elif kind == "boards": f = lambda w, h: P.boards(Rm, w, h, 0.5, orient=spec.get("top_orient", "h"), shadow_top=False)
        elif kind == "metal": f = lambda w, h: P.metal(Rm, w, h, 4.0)
        else: f = lambda w, h: P.flat(Rm, w, h, 4.4, edge=False)
        self.m.rect(key, tw, th, f); self.sizes[key] = (tw, th)
        key = f"{mat}_under"
        uw, uh = spec.get("under", (48, 48))
        if kind == "shingle":                                  # the eave soffit: dark rafters under the overhang
            f = lambda w, h: P.boards(R["walnut"], w, h, -1.2, orient="v", bw=4, lap=False, nails=False, shadow_top=False)
        else:
            f = lambda w, h: P.flat(Rm, w, h, 1.4, edge=False)
        self.m.rect(key, uw, uh, f); self.sizes[key] = (uw, uh)

    def rect(self, key, w, h, paint):
        """A dedicated painted rect (window, door, flowers...). w, h in pixels."""
        self.m.rect(key, w, h, paint); self.sizes[key] = (w, h)
        return key

    def crop(self, sw, w, h, place="any", var=0):
        SW_, SH_ = self.sizes[sw]
        if w > SW_ or h > SH_:                                    # the swatch grows to fit (it is painted at pack time,
            SW_, SH_ = max(SW_, w), max(SH_, h)                   # so earlier crops stay inside it); never stretched
            self.sizes[sw] = (SW_, SH_); self.m.rects[sw]["w"], self.m.rects[sw]["h"] = SW_, SH_
            self.grown[sw] = (SW_, SH_)
        k = (sw, w, h, str(place), var)
        if k not in self._off:
            ox = self.rng.randint(0, SW_ - w)
            if isinstance(place, tuple): oy = int(round((1 - place[1]) * (SH_ - h)))
            elif place == "ground": oy = SH_ - h
            elif place == "top": oy = 0
            else: oy = self.rng.randint(min(6, SH_ - h), max(min(6, SH_ - h), min(SH_ - h, int(SH_ * 0.66) - h)))
            self._off[k] = (ox, oy)
        ox, oy = self._off[k]
        return F(sw, sub=(ox, oy, w, h))

    def faces(self, frm, to, mat, hide=(), var=None, over=None, frac=None, place=None):
        if var is None: self._var[0] += 1; var = self._var[0]
        out = {}
        for f in ("north", "east", "south", "west", "up", "down"):
            if f in hide: out[f] = None; continue
            a, b = DIMS[f]
            w, h = px(to[a] - frm[a]), px(to[b] - frm[b])
            if w == 0 or h == 0: out[f] = None; continue
            mt = (over or {}).get(f, mat)
            if isinstance(mt, dict): out[f] = mt; continue                    # a ready F(...) spec
            if mt in self.mats:
                if f == "up": sw = f"{mt}_top"
                elif f == "down": sw = f"{mt}_under"
                elif f in LIT: sw = f"{mt}_lit2" if (f"{mt}_lit2" in self.sizes and hash(str(var)) % 2) else f"{mt}_lit"
                else: sw = f"{mt}_shade"
            else:
                sw = mt
            if f in ("up", "down"): pl = "any"
            elif frac is not None and self.mats.get(mt, {}).get("kind") == "shingle": pl = ("frac", frac)
            elif place: pl = place
            elif frm[1] <= 1: pl = "ground"
            else: pl = "any"
            out[f] = self.crop(sw, w, h, pl, var)
        return out

    def box(self, name, grp, frm, to, mat, hide=("down",), var=None, over=None, rot=(0, 0, 0), origin=None, frac=None, place=None):
        frm = [float(v) for v in frm]; to = [float(v) for v in to]
        try:
            fs = self.faces(frm, to, mat, hide, var, over, frac, place)
        except SystemExit as e:
            raise SystemExit(f"{name}: {e}")
        return self.m.cube(name, grp, frm, to, fs, rot, origin)

    def group(self, name, origin, parent=None):
        return self.m.group(name, origin, parent or self.root)

    # ---- pieces
    def plane_box(self, side, plane, u0, u1, y0, y1, out, inset=0.0):
        """The box sitting on a wall plane: `out` units proud of it (inset: sunk that much into the wall)."""
        if side == "north": return [u0, y0, plane - out], [u1, y1, plane + inset]
        if side == "south": return [u0, y0, plane - inset], [u1, y1, plane + out]
        if side == "east": return [plane - inset, y0, u0], [plane + out, y1, u1]
        return [plane - out, y0, u0], [plane + inset, y1, u1]

    def window(self, name, grp, side, plane, u, y, w, h, frame="trim", frame_ramp=None, style="leaded", arch=False,
               sill="trim", lintel="trim", shutters=None, flowerbox=None, glow=True, keystone=True):
        fr = frame_ramp or R["paint_white"]
        key = self.rect(f"win_{w}x{h}_{style}_{'a' if arch else 'r'}_{id(fr) % 997}", px(w), px(h),
                        lambda W, H: self.P.window(fr, W, H, style, arch, 2, glow))
        frm, to = self.plane_box(side, plane, u - w / 2, u + w / 2, y, y + h, 0.5)
        fs = self.faces(frm, to, frame, (OPP[side], "down", side), f"{name}e"); fs[side] = F(key)
        self.m.cube(name, grp, frm, to, fs)
        if sill:
            f2, t2 = self.plane_box(side, plane, u - w / 2 - 1, u + w / 2 + 1, y - 1.5, y, 1.5)
            self.box(f"{name}_sill", grp, f2, t2, sill, (OPP[side],), "sill")
        if lintel:
            if arch:
                f2, t2 = self.plane_box(side, plane, u - w / 2 - 1, u + w / 2 + 1, y + h, y + h + 1.5, 1)
                self.box(f"{name}_arch", grp, f2, t2, lintel, (OPP[side],), "arch")
                if keystone:
                    f2, t2 = self.plane_box(side, plane, u - 1, u + 1, y + h - 0.5, y + h + 2.5, 1.5)
                    self.box(f"{name}_keystone", grp, f2, t2, lintel, (OPP[side],), "key")
            else:
                f2, t2 = self.plane_box(side, plane, u - w / 2 - 1.5, u + w / 2 + 1.5, y + h, y + h + 2, 1)
                self.box(f"{name}_lintel", grp, f2, t2, lintel, (OPP[side],), "lintel")
        if shutters:
            sk = self.rect(f"shutter_{w}x{h}_{shutters}", px(w / 2), px(h), lambda W, H: self.P.shutter(R[shutters], W, H))
            for s, (a, b) in (("a", (u - w - 0.5, u - w / 2 - 0.5)), ("b", (u + w / 2 + 0.5, u + w + 0.5))):
                f2, t2 = self.plane_box(side, plane, a, b, y, y + h, 0.5)
                fs = self.faces(f2, t2, "trim", (OPP[side], side), f"{name}sh"); fs[side] = F(sk)
                self.m.cube(f"{name}_shutter_{s}", grp, f2, t2, fs)
        if flowerbox:
            f2, t2 = self.plane_box(side, plane, u - w / 2 - 0.5, u + w / 2 + 0.5, y - 4, y - 1.5, 2.5)
            fk = self.rect(f"flowers_{w}", px(w + 1), px(2.5), lambda W, H: self.P.flowers(W, H))
            self.box(f"{name}_flowerbox", grp, f2, t2, flowerbox, (OPP[side],), "fbox", over={"up": F(fk)})
            n = int(w // 2)
            for i in range(n):
                uu = u - w / 2 + 0.5 + (i + 0.5) * w / n + self.rng.uniform(-0.3, 0.3)
                hh = self.rng.choice([1.0, 1.5, 1.5, 2.0])
                f3, t3 = self.plane_box(side, plane, uu - 0.5, uu + 0.5, y - 1.5, y - 1.5 + hh, 2.0)
                f3[1 if True else 0] = f3[1]
                if side == "north": f3[2], t3[2] = plane - 2.0, plane - 1.0
                elif side == "south": f3[2], t3[2] = plane + 1.0, plane + 2.0
                elif side == "east": f3[0], t3[0] = plane + 1.0, plane + 2.0
                else: f3[0], t3[0] = plane - 2.0, plane - 1.0
                bk = self.rect(f"bloom_{i % len(BLOOMS)}", 2, 2, lambda W, H, B=BLOOMS[i % len(BLOOMS)]: self.P.bloom(B, W, H))
                lk = self.rect("leafy", 4, 4, lambda W, H: self.P.leaves(W, H))
                over = {f: F(lk, sub=(0, 0, *[px(d) for d in self._fd(f3, t3, f)])) for f in ("north", "south", "east", "west")}
                over["up"] = F(bk, sub=(0, 0, 2, 2))
                self.m.cube(f"{name}_flower_{i + 1}", grp, f3, t3, {**over, "down": None})

    @staticmethod
    def _fd(frm, to, f):
        a, b = DIMS[f]
        return to[a] - frm[a], to[b] - frm[b]

    def door(self, name, grp, side, plane, u, y, w, h, wood="oak", frame="trim", arch=True, steps="trim", canopy=None):
        Rm = R[wood]
        key = self.rect(f"door_{w}x{h}_{wood}_{'a' if arch else 'r'}", px(w), px(h), lambda W, H: self.P.door(Rm, W, H, arch))
        hinge = u - w / 2
        pivot = {"north": [hinge, y, plane], "south": [hinge, y, plane], "east": [plane, y, hinge], "west": [plane, y, hinge]}[side]
        dg = self.m.group(f"{name}", pivot, grp)
        frm, to = self.plane_box(side, plane, u - w / 2, u + w / 2, y, y + h, 0.5)
        fs = self.faces(frm, to, frame, (OPP[side], "down", side), f"{name}e"); fs[side] = F(key)
        self.m.cube(f"{name}_panel", dg, frm, to, fs)
        # surround: jambs and an arch / lintel, 1 proud
        for s, (a, b) in (("left", (u - w / 2 - 1.5, u - w / 2)), ("right", (u + w / 2, u + w / 2 + 1.5))):
            f2, t2 = self.plane_box(side, plane, a, b, y, y + h - (w / 2 if arch else 0) + 0.5, 1)
            self.box(f"{name}_jamb_{s}", grp, f2, t2, frame, (OPP[side],), "jamb")
        if arch:
            r = w / 2 + 0.75; cy = y + h - w / 2
            for i in range(5):                                         # voussoirs around the arch
                ang = math.radians(180 * (i + 0.5) / 5)
                cu, cyy = u - math.cos(ang) * r, cy + math.sin(ang) * r
                f2, t2 = self.plane_box(side, plane, cu - 1.25, cu + 1.25, cyy - 1.25, cyy + 1.25, 1)
                rot = {"north": (0, 0, -(180 * (i + 0.5) / 5 - 90)), "south": (0, 0, (180 * (i + 0.5) / 5 - 90)),
                       "east": ((180 * (i + 0.5) / 5 - 90), 0, 0), "west": (-(180 * (i + 0.5) / 5 - 90), 0, 0)}[side]
                cen = [(f2[k] + t2[k]) / 2 for k in range(3)]
                self.box(f"{name}_voussoir_{i + 1}", grp, f2, t2, frame, (OPP[side],), f"vous{i}", rot=rot, origin=cen)
        else:
            f2, t2 = self.plane_box(side, plane, u - w / 2 - 2, u + w / 2 + 2, y + h, y + h + 2, 1)
            self.box(f"{name}_lintel", grp, f2, t2, frame, (OPP[side],), "dlintel")
        if steps:
            for k in range(2):
                f2, t2 = self.plane_box(side, plane, u - w / 2 - 3 + k, u + w / 2 + 3 - k, k * 1.5, (k + 1) * 1.5, 5 - k * 2.5)
                self.box(f"{name}_step_{k + 1}", grp, f2, t2, steps, (OPP[side], "down"), f"step{k}", place="ground")
        if canopy:
            roof_mat, bracket = canopy
            for k in range(3):
                f2, t2 = self.plane_box(side, plane, u - w / 2 - 4 + k * 1.5, u + w / 2 + 4 - k * 1.5, y + h + 3 + k * 1.5,
                                        y + h + 4.5 + k * 1.5, 5 - k * 1.5)
                self.box(f"{name}_canopy_{k + 1}", grp, f2, t2, roof_mat, (OPP[side],), f"can{k}", frac=k / 3)
            for s, uu in (("left", u - w / 2 - 3), ("right", u + w / 2 + 2)):
                f2, t2 = self.plane_box(side, plane, uu, uu + 1, y + h - 1, y + h + 3, 4)
                self.box(f"{name}_bracket_{s}", grp, f2, t2, bracket, (OPP[side],), "brk")

    def quoins(self, prefix, grp, x1, x2, z1, z2, y1, y2, mat="trim", step=3.0):
        i, y = 0, y1
        while y + step <= y2 + 0.01:
            long_x = i % 2 == 0
            for cx, cz, sx, sz in ((x1, z1, 1, 1), (x2, z1, -1, 1), (x1, z2, 1, -1), (x2, z2, -1, -1)):
                lx, lz = (4, 2) if long_x else (2, 4)
                a, b = sorted((cx - sx * 0.5, cx + sx * lx)); c, d = sorted((cz - sz * 0.5, cz + sz * lz))
                self.box(f"{prefix}_{len(self.m.elements)}", grp, [a, y, c], [b, y + step - 0.01 if False else y + step, d], mat, ("down",),
                         f"q{i % 2}")
            y += step; i += 1

    def roof(self, prefix, grp, x1, x2, z1, z2, y0, profile, roof_mat, gable_mat, axis="z", eave=3.0,
             caps=None, ridge=None, crest=None, finials=None, gable_over=None):
        """Stepped gable roof (the castle's layered roofs). axis "z": the ridge runs along z, slopes face east and west,
        gable ends north and south. profile: [(inset, height), ...] per layer from the eave up; insets shrink each
        slope. caps: (material, out): a coping / verge strip on the outer step of every layer, `out` proud of the
        gable (crow steps in stone, or tile verges with a bargeboard). Returns the ridge height."""
        g = self.group(f"{prefix}", [(x1 + x2) / 2, y0, (z1 + z2) / 2], grp)
        if axis == "z": lo, hi, a1, a2 = x1 - eave, x2 + eave, z1, z2
        else: lo, hi, a1, a2 = z1 - eave, z2 + eave, x1, x2
        wall_lo, wall_hi = (x1, x2) if axis == "z" else (z1, z2)
        y = y0; n = len(profile)
        for k, (ins, hgt) in enumerate(profile):
            lo += ins if k else 0; hi -= ins if k else 0
            if hi - lo < 1: break
            frac = k / max(1, n - 1)
            beyond = lo < wall_lo - 0.01
            gm = gable_over if (gable_over and beyond) else (roof_mat if beyond else gable_mat)
            if axis == "z":
                frm, to = [lo, y, a1], [hi, y + hgt, a2]
                over = {"north": gm, "south": gm}
            else:
                frm, to = [a1, y, lo], [a2, y + hgt, hi]
                over = {"east": gm, "west": gm}
            hide = () if k == 0 else ("down",)
            self.box(f"{prefix}_layer_{k + 1}", g, frm, to, roof_mat, hide, f"{prefix}{k}", over=over, frac=frac,
                     place="any")
            if caps and not beyond:
                cm, out = caps
                nxt = profile[k + 1][0] if k + 1 < n else (hi - lo) / 2
                for s, (p, q) in (("a", (lo, lo + max(1.0, nxt))), ("b", (hi - max(1.0, nxt), hi))):
                    for e, (r1, r2) in (("front", (a1 - out, a1)), ("back", (a2, a2 + out))):
                        if axis == "z": f2, t2 = [p, y, r1], [q, y + hgt + 0.5, r2]
                        else: f2, t2 = [r1, y, p], [r2, y + hgt + 0.5, q]
                        self.box(f"{prefix}_cap_{k + 1}_{s}_{e}", g, f2, t2, cm, ("down",), f"cap{k}")
            y += hgt
        top = y
        if ridge:
            rm, rw, rh = ridge
            if axis == "z": f2, t2 = [(lo + hi) / 2 - rw / 2, top, a1 - 1], [(lo + hi) / 2 + rw / 2, top + rh, a2 + 1]
            else: f2, t2 = [a1 - 1, top, (lo + hi) / 2 - rw / 2], [a2 + 1, top + rh, (lo + hi) / 2 + rw / 2]
            self.box(f"{prefix}_ridge", g, f2, t2, rm, ("down",), f"{prefix}ridge")
            top += rh
        mid = (lo + hi) / 2
        if crest:
            cmat, every = crest
            L0, L1 = a1 + 2, a2 - 2
            k, t = 0, L0
            while t <= L1 + 0.01:
                tall = k % 2 == 0
                hh, ww = (3.0, 0.5) if tall else (1.5, 1.0)
                if axis == "z": f2, t2 = [mid - ww / 2, top, t - ww / 2], [mid + ww / 2, top + hh, t + ww / 2]
                else: f2, t2 = [t - ww / 2, top, mid - ww / 2], [t + ww / 2, top + hh, mid + ww / 2]
                self.box(f"{prefix}_crest_{k + 1}", g, f2, t2, cmat, ("down",), "crest_tall" if tall else "crest_ball")
                k += 1; t += every
        if finials:
            fmat, fh = finials
            for e, a in (("front", a1), ("back", a2)):
                if axis == "z": f2, t2 = [mid - 0.75, top - 1, a - 0.75], [mid + 0.75, top + fh, a + 0.75]
                else: f2, t2 = [a - 0.75, top - 1, mid - 0.75], [a + 0.75, top + fh, mid + 0.75]
                self.box(f"{prefix}_finial_{e}", g, f2, t2, fmat, ("down",), "finial")
                if axis == "z": f2, t2 = [mid - 1.25, top + fh - 2.5, a - 1.25], [mid + 1.25, top + fh - 0.5, a + 1.25]
                else: f2, t2 = [a - 1.25, top + fh - 2.5, mid - 1.25], [a + 1.25, top + fh - 0.5, mid + 1.25]
                self.box(f"{prefix}_finial_{e}_knob", g, f2, t2, fmat, (), "finial_knob")
        return top

    def chimney(self, name, grp, x, z, w, d, y0, y1, mat, cap="trim", pots=2):
        g = self.group(name, [x, y0, z], grp)
        self.box(f"{name}_stack", g, [x - w / 2, y0, z - d / 2], [x + w / 2, y1, z + d / 2], mat, ("down",), f"{name}s", place="top")
        self.box(f"{name}_cap", g, [x - w / 2 - 1, y1, z - d / 2 - 1], [x + w / 2 + 1, y1 + 1.5, z + d / 2 + 1], cap, ("down",), "ccap")
        for i in range(pots):
            px_ = x - w / 4 + i * (w / 2) if pots > 1 else x
            self.box(f"{name}_pot_{i + 1}", g, [px_ - 1, y1 + 1.5, z - 1], [px_ + 1, y1 + 4, z + 1], "pot", ("down",), "pot")

    def octo(self, name, grp, cx, cz, D, y1, y2, mat, hide=("down",), var=None, inset=None, place=None):
        inset = inset if inset is not None else h2(D * 0.3)
        a, b = D / 2, (D - inset) / 2
        self.box(f"{name}_a", grp, [cx - a, y1, cz - b], [cx + a, y2, cz + b], mat, hide, var, place=place)
        self.box(f"{name}_b", grp, [cx - b, y1, cz - a], [cx + b, y2, cz + a], mat, hide, var, place=place)

    def cone(self, name, grp, cx, cz, W0, y0, tip, roof_mat, n=7, finial="gold", flare=1.15):
        """Concave witch-hat cone: wide eave, tiers alternating 0/45 degrees, a point and a finial with a knob."""
        self.box(f"{name}_eave", grp, [cx - W0 / 2, y0, cz - W0 / 2], [cx + W0 / 2, y0 + 1, cz + W0 / 2], roof_mat, (), f"{name}e", frac=0.0)
        top = tip - 3
        for i in range(n):
            u0, u1 = i / n, (i + 1) / n
            w = h2(max(1.5, (W0 - 3) * (1 - u0) ** flare))
            if i % 2: w = h2(max(1.5, w * 0.88))
            ya, yb = h2(y0 + 1 + u0 * (top - y0 - 1)), h2(y0 + 1 + u1 * (top - y0 - 1))
            self.box(f"{name}_tier_{i + 1}", grp, [cx - w / 2, ya, cz - w / 2], [cx + w / 2, yb, cz + w / 2], roof_mat,
                     ("down",), f"{name}t{i}", rot=(0, 45 if i % 2 else 0, 0), origin=[cx, ya, cz], frac=(i + 0.5) / n)
        self.box(f"{name}_point", grp, [cx - 0.5, h2(top), cz - 0.5], [cx + 0.5, tip, cz + 0.5], roof_mat, ("down",), "point", frac=1.0)
        self.box(f"{name}_finial", grp, [cx - 0.5, tip, cz - 0.5], [cx + 0.5, tip + 4, cz + 0.5], finial, ("down",), "frod")
        self.box(f"{name}_finial_knob", grp, [cx - 1, tip + 1, cz - 1], [cx + 1, tip + 2.5, cz + 1], finial, (), "fknob")

    def lantern(self, name, grp, side, plane, u, y):
        g = self.group(name, [u, y, plane], grp)
        f2, t2 = self.plane_box(side, plane, u - 0.5, u + 0.5, y + 4, y + 5, 3)
        self.box(f"{name}_arm", g, f2, t2, "iron", (OPP[side],), "larm")
        f2, t2 = self.plane_box(side, plane, u - 1.5, u + 1.5, y, y + 4, 3.5, inset=-1.0)
        gk = self.rect("lantern_glow", 6, 8, lambda W, H: self.P.flat(R["glow"], W, H, 4.6))
        fs = self.faces(f2, t2, "iron", ("north", "south", "east", "west"), "lglass")
        for f in ("north", "south", "east", "west"): fs[f] = F(gk)
        self.m.cube(f"{name}_glow", g, f2, t2, fs)
        f2, t2 = self.plane_box(side, plane, u - 2, u + 2, y + 4, y + 5, 4, inset=-0.5)
        self.box(f"{name}_cap", g, f2, t2, "iron", (), "lcap")

    def finish(self, outs):
        sd = self.group("scale_dummy", [0, 0, 0]); self.m.groups[sd]["visible"] = False
        e = self.m.cube("scale_dummy_imp", sd, [-2, 0, -60], [2, 18.5, -56], {})
        e["export"] = False; e["visibility"] = False
        self.m.pack()
        op = self.m.img[self.m.img[..., 3] > 0][:, :3]
        n = len([e for e in self.m.elements if e.get("export", True)])
        ys = [e["to"][1] for e in self.m.elements if e.get("export", True)]
        xs = [v for e in self.m.elements if e.get("export", True) for v in (e["from"][0], e["to"][0])]
        zs = [v for e in self.m.elements if e.get("export", True) for v in (e["from"][2], e["to"][2])]
        if self.grown: print("  grown swatches:", self.grown)
        print(f"{self.name}: cubes={n} atlas_rows={self.m.used}/{self.m.TEX} colours={len({tuple(c) for c in op})} "
              f"size x {min(xs):.0f}..{max(xs):.0f} z {min(zs):.0f}..{max(zs):.0f} height {max(ys):.0f}")
        model = self.m.bbmodel()
        for out in outs:
            os.makedirs(out, exist_ok=True)
            from PIL import Image
            Image.fromarray(self.m.img, "RGBA").save(os.path.join(out, f"{self.name}.png"))
            p = os.path.join(out, f"{self.name}.bbmodel")
            with open(p, "w") as fh:
                json.dump(model, fh, indent="\t")
            sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
            import fix_texture_bleed
            fix_texture_bleed.pad_file(p)
        return self.m
