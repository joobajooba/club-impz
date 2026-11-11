"""Plant card painters taken from build_forest_foliage.py (session fdc2906e)."""
import math
import numpy as np
from foliage_lib import ramp, ramp_colour
GRASS = ramp("#33500b #3f5e0c #4d6f0d #587e0e #608a10 #679411 #7aad1d")
SEED = ramp("#5e6a1c #7a8426 #98a034 #b4b44a #ccc468")

def make_noise(nr, w, h, amp, count):
    f = np.zeros((h, w))
    for _ in range(count):
        x, y = nr.integers(0, w), nr.integers(0, h)
        f[y:y + nr.integers(1, 3), x:x + nr.integers(1, 3)] += nr.choice([-1, 1]) * amp
    return f


# ---------------------------------------------------------------- card painters (tip / top of the card = row 0)
def paint_leaf(nr, R, w, h, shade=0.0, bend=0.0, petiole=0.14, widest=0.38, serrate=False, stem_col=None):
    """One pointed leaf: petiole, gradient base->tip, darker midrib, side veins, light upper edge, shadow base."""
    val = np.full((h, w), -9.0); stem = np.zeros((h, w), bool)
    c0 = (w - 1) / 2 - bend * (w / 2 - 1) * 0.5
    rows = []
    for y in range(h):
        t = 1 - (y + 0.5) / h  # 0 at base, 1 at tip
        cx = c0 + bend * t * t * (w / 2 - 1)
        if t < petiole:
            x = int(round(cx)); val[y, x] = 0.6 + shade; stem[y, x] = True; continue
        s = (t - petiole) / (1 - petiole)
        p = math.sin(s / widest * math.pi / 2) ** 0.6 if s < widest else math.cos((s - widest) / (1 - widest) * math.pi / 2) ** 0.85
        hw = max(0.5, p * w / 2)
        xs = [x for x in range(w) if abs(x - cx) <= hw - 0.3] or [int(round(cx))]
        if serrate and y % 2 == 0 and len(xs) > 3: xs = xs[1:-1]
        for x in xs:
            d = x - cx
            v = 1.0 + 3.6 * s + shade
            v += 0.5 if d < -0.5 else (-0.25 if d > 0.5 else 0)      # upper half lit, lower half shaded
            if abs(d) < 0.55 and s < 0.9: v -= 0.9                    # midrib
            elif abs(d) >= 1.4 and (y + int(abs(d))) % 3 == 0: v -= 0.35  # side veins angled to the tip
            if s < 0.25: v -= 0.9 * (1 - s / 0.25)                    # shadow at the base
            val[y, x] = v
        rows.append((y, min(xs), max(xs)))
    for y, a, b in rows:  # 1 px light edge on the upper side, darker lower edge
        val[y, a] += 0.8
        if b > a: val[y, b] -= 0.3
    a = val > -5
    for x in range(w):  # tip pixels a touch lighter
        ys = np.nonzero(a[:, x] & ~stem[:, x])[0]
        if len(ys): val[ys[0], x] += 0.4
    val += np.where(a, make_noise(nr, w, h, 0.3, max(1, w * h // 14)), 0)
    rgb = ramp_colour(R, np.clip(val, 0, len(R) - 1))
    if stem_col is not None: rgb[stem] = ramp_colour(stem_col, np.clip(val[stem] + 1.5, 0, len(stem_col) - 1))
    return rgb, a


def paint_blade(nr, R, w, h, shade=0.0, bend=0.0, base_w=3, tip_w=1, s0=0.0, s1=1.0, jag=True):
    """One grass blade (or a segment of one): tapers base_w -> tip_w px, bends sideways, dark base, light tip,
    light edge on one side. s0..s1 = which part of the full blade this card is (for chained segments)."""
    val = np.full((h, w), -9.0)
    c0 = (w - 1) / 2 - bend * (w / 2 - 0.5) * 0.5
    for y in range(h):
        t = 1 - (y + 0.5) / h
        s = s0 + (s1 - s0) * t
        cx = c0 + bend * t * t * (w / 2 - 0.5)
        bw = max(1, int(round(base_w + (tip_w - base_w) * t ** 0.8)))
        x0 = int(round(cx - (bw - 1) / 2))
        for k in range(bw):
            x = x0 + k
            if not 0 <= x < w: continue
            v = 0.7 + 4.6 * s + shade
            if k == 0: v += 0.7                        # light edge
            elif k == bw - 1 and bw > 1: v -= 0.4
            elif bw >= 3: v += 0.25                    # soft centre stripe
            if s < 0.22: v -= 1.0 * (1 - s / 0.22)     # shadow base
            val[y, x] = v
    if jag and s1 >= 0.99 and h > 3:  # stepped, slightly ragged tip
        ys = np.nonzero((val > -5).any(1))[0]
        if len(ys) and nr.random() < 0.5: val[ys[0]] = -9
    a = val > -5
    val += np.where(a, make_noise(nr, w, h, 0.25, max(1, w * h // 18)), 0)
    return ramp_colour(R, np.clip(val, 0, len(R) - 1)), a


def paint_seed_stalk(nr, w, h):
    """Thin grass stem with a nodding seed head of small spikelets."""
    val = np.full((h, w), -9.0); col = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
    cx = w // 2; head = int(h * 0.35)
    for y in range(h):
        t = 1 - (y + 0.5) / h
        x = cx + (1 if y < head // 2 else 0)
        a[y, x] = True; col[y, x] = ramp_colour(GRASS, np.array(1.2 + 3.5 * t))
        if y < head and y % 2 == 0:  # spikelets alternating left / right
            for side in ((-1,), (1,)) if y % 4 == 0 else ((1,), (-1,)):
                sx = x + side[0]
                if 0 <= sx < w:
                    a[y, sx] = True; col[y, sx] = ramp_colour(SEED, np.array(3.5 - y / head * 2 + (0.5 if side[0] < 0 else 0)))
            if y + 1 < h: col[y + 1, x] = SEED[2]
    return col, a


def paint_twig(nr, R, w, h, forks=2):
    """Stem / twig card: 2 px at the base, 1 px higher up, a couple of forks, light left side."""
    rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
    x = (w - 1) // 2
    pts = []
    for y in range(h - 1, -1, -1):
        t = 1 - (y + 0.5) / h
        if y % 5 == 0 and 0 < y < h - 3: x = int(np.clip(x + nr.choice([-1, 1]), 1, w - 2))
        for k in range(2 if t < 0.45 else 1):
            if x + k < w:
                a[y, x + k] = True; rgb[y, x + k] = ramp_colour(R, np.array(1.0 + 2.2 * t + (0.8 if k == 0 else -0.3)))
        pts.append((x, y))
    for _ in range(forks):  # side branch going up and out
        bx, by = pts[int(nr.integers(len(pts) // 4, len(pts) * 3 // 4))]
        d = int(nr.choice([-1, 1]))
        for k in range(1, int(nr.integers(3, 6))):
            xx, yy = bx + d * k, by - k
            if 0 <= xx < w and 0 <= yy < h:
                a[yy, xx] = True; rgb[yy, xx] = ramp_colour(R, np.array(2.6))
    return rgb, a


def paint_petal(nr, R, w, h, shade=0.0):
    """Rose petal: narrow base, wide rounded top with a small notch, bright rim, crease lines."""
    val = np.full((h, w), -9.0)
    for y in range(h):
        t = 1 - (y + 0.5) / h
        hw = (w / 2) * (0.5 + 0.55 * math.sin(min(1, t / 0.6) * math.pi / 2))
        if t > 0.85: hw *= 0.82
        for x in range(w):
            d = x - (w - 1) / 2
            if abs(d) <= hw - 0.2:
                v = 1.0 + 4.0 * t + shade
                if abs(abs(d) - w / 5) < 0.5 and t < 0.8: v -= 0.6   # creases
                if t < 0.3: v -= 0.8 * (1 - t / 0.3)
                if d < 0: v += 0.3
                val[y, x] = v
    if w >= 4: val[0, int(w // 2)] = -9  # notch
    a = val > -5
    for x in range(w):  # bright rim along the top edge
        ys = np.nonzero(a[:, x])[0]
        if len(ys): val[ys[0], x] += 1.2
    return ramp_colour(R, np.clip(val, 0, len(R) - 1)), a


# ---------------------------------------------------------------- solid painters (mushrooms, rose cores)
LIGHT = {"up": 0.9, "north": 0.25, "west": 0.25, "south": -0.25, "east": -0.25, "down": -1.0}

