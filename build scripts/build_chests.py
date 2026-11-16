"""Five coloured chests (blockbench_detailed_prompts.md 3.11 props): red, blue, green, yellow, purple.
Each has its own silhouette and fewer, bigger parts than treasure_chest; the detail is in the paint:
painted planks over wood grain, chipped edges showing bare wood, painted or carved motifs, bevelled trims.
2 px/unit, one 128 texture each, lid group pivoted on the hinge line with open/close/idle animations.
Run: py -3 build_chests.py [red|blue|green|yellow|purple ...]   (no args = all + showcase)"""
import sys, os, json, math, runpy
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from PIL import Image
from foliage_lib import Model, F, ramp, ramp_colour, face_dims, showcase

PPU = 2
OUT = r"C:/Users/lucas/blockbench_models/props/chests"
HERE = os.path.dirname(os.path.abspath(__file__))

R = {
    "wood": ramp("#2a1206 #3f1d0b #582b12 #74401c #8f5626 #a86d33 #bf8645 #d4a25e"),
    "red": ramp("#3a0a0c #5a1014 #7c1a1c #9e2624 #bc3a2e #d4573c #e47e54 #f0a878"),
    "blue": ramp("#0a1838 #10265a #18387e #224ea0 #3268bc #4c86d2 #74a8e4 #a6ccf2"),
    "green": ramp("#0c2210 #143418 #1e4a20 #2a6228 #3a7c32 #52963e #72b052 #9ccc72"),
    "yellow": ramp("#4a3006 #6e4a0a #966a10 #bc8c18 #dcac26 #eec844 #f8de74 #fcf0b0"),
    "purple": ramp("#1a0a2a #2a1040 #3c1858 #522274 #6a3092 #8444ae #a066c8 #c494e0"),
    "velvet": ramp("#200414 #34081e #4c0e2a #661638 #822046 #9c2e56 #b44468"),
    "green_leather": ramp("#0a1a0e #102618 #183622 #22482c #2e5c38 #3e7246 #528a58"),
    "gold": ramp("#3c2004 #5e3808 #86560f #ad7a1b #cf9f2e #e8c150 #f5db86 #fbedbd"),
    "silver": ramp("#1e2430 #323a48 #4a5464 #687282 #8a94a2 #aeb6c2 #d0d6de #e8ecf0"),
    "bronze": ramp("#2e1608 #4a260e #6a3a16 #8c5222 #ac6c30 #c88a44 #dcaa62 #ecc888"),
    "gunmetal": ramp("#121018 #1c1a26 #2a2836 #3a3848 #4e4c5e #666478 #828096 #a4a2b6"),
    "leather": ramp("#24120a #3a1e10 #522c18 #6c3c20 #88502a #a26636 #b88048"),
    "amber": ramp("#4a1e00 #7a3600 #a85406 #d27a12 #f0a22a #fcc858 #fee49a"),
    "void": ramp("#120424 #2a0c4a #4a1878 #7428b0 #a448e0 #d06cff #f0c8ff"),
    "ruby": ramp("#3a0410 #620a1c #921430 #c02846 #e65a6c #f6a0a8"),
    "sapph": ramp("#08143e #0e2466 #183a94 #2a58c0 #5486e0 #9cbcf2"),
    "emerald": ramp("#062a14 #0c4422 #146434 #20864a #3eaa66 #84d49a"),
}
LIGHT = {"up": 0.9, "north": 0.3, "west": 0.1, "east": -0.2, "south": -0.4, "down": -1.3}
BAYER = (np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) + 0.5) / 16 - 0.5
RNG = np.random.default_rng(5150)


# ------------------------------------------------------------------ helpers
def grid(w, h):
    return np.mgrid[0:h, 0:w]


def Q(Rm, v):
    h, w = v.shape
    yy, xx = grid(w, h)
    return ramp_colour(Rm, v + BAYER[yy % 4, xx % 4] * 0.3)


def form(w, h, amt=1.0, vert=0.35):
    yy, xx = grid(w, h)
    u = np.abs((xx + .5) / w * 2 - 1); t = np.abs((yy + .5) / h * 2 - 1)
    d = 0.6 * np.maximum(u, t) + 0.4 * np.hypot(u, t) / 1.414
    return -amt * np.clip((d - 0.35) / 0.65, 0, 1) ** 1.6 - vert * ((yy + .5) / h - 0.4)


def soft_noise(w, h, amp=0.2, n=None):
    v = np.zeros((h, w)); yy, xx = grid(w, h)
    for _ in range(n if n is not None else max(1, w * h // 40)):
        cx, cy = RNG.uniform(0, w), RNG.uniform(0, h); r = RNG.uniform(0.8, 1.8)
        v += np.where(np.hypot(xx + .5 - cx, (yy + .5 - cy) * 1.3) < r, RNG.choice([-1, 1]) * amp, 0)
    return np.clip(v, -0.5, 0.5)


def edge_band(n, k, amt):
    i = np.arange(n)
    return amt * np.clip(1 - (i + 0.5) / k, 0, 1) ** 1.3


def shift(m, dy, dx):
    """out[y, x] = m[y - dy, x - dx] (False outside)."""
    out = np.zeros_like(m)
    h, w = m.shape
    ys, yd = (slice(0, h - dy), slice(dy, h)) if dy >= 0 else (slice(-dy, h), slice(0, h + dy))
    xs, xd = (slice(0, w - dx), slice(dx, w)) if dx >= 0 else (slice(-dx, w), slice(0, w + dx))
    out[yd, xd] = m[ys, xs]
    return out


def shade_mask(rgb, mask, Rm, base, face, style="raised"):
    """Paint a motif mask with its own soft shading: raised = lit top edge, shaded bottom edge;
    carved = sunk a step or so, shadow along the top inside edge, lit lower lip."""
    if not mask.any(): return
    H, W = mask.shape
    v = np.full((H, W), base + LIGHT[face] * 0.6) + form(W, H, 0.6, 0.3) + soft_noise(W, H, 0.12, max(1, W * H // 80))
    top = mask & ~shift(mask, 1, 0); bot = mask & ~shift(mask, -1, 0)
    if style == "raised":
        v += 0.8 * top - 0.6 * bot
    else:
        v -= 0.5 * top - 0.4 * bot
    rgb[mask] = Q(Rm, v)[mask]


def ring_mask(W, H, inset):
    yy, xx = grid(W, H)
    d = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy])
    return d == inset


# ------------------------------------------------------------------ motifs: (W, H, face) -> [(mask, ramp, base, style)]
def m_scroll(W, H, Rm, base=4.6):
    """Symmetric gold scroll vine: a wave with curls, leaf dots and a centre rosette."""
    yy, xx = grid(W, H)
    if W < 16 or H < 9:
        return [((yy == H // 2) & (xx % 3 == 1) & (xx > 3) & (xx < W - 4), Rm, base, "raised")]
    cx = W / 2; x0 = 4.0
    amp = max(1.2, H * 0.17)
    ph = lambda x: (x + 0.5 - x0) / (cx - x0) * 2 * math.pi
    yc = H / 2 + amp * np.sin(ph(xx))
    m = (np.abs(yy + 0.5 - yc) < 0.6) & (xx >= x0) & (xx < cx - 2.5)
    for k, s in ((0.25, -1), (0.75, 1)):
        px_ = x0 + (cx - x0) * k
        py_ = H / 2 + amp * math.sin(2 * math.pi * k) - s * 2.0
        rho = np.hypot(xx + .5 - px_, yy + .5 - py_)
        m |= (np.abs(rho - 1.5) < 0.5) & ((yy + .5 - py_) * s <= 0.6)
    for x in range(int(x0) + 2, int(cx) - 3, 3):
        y = H / 2 + amp * math.sin(ph(x)); side = 1 if (x // 3) % 2 else -1
        yi = int(round(y + side * 1.6 - 0.5))
        if 0 <= yi < H: m[yi, x] = True
    m |= m[:, ::-1]
    ros = (np.abs(xx + .5 - cx) + np.abs(yy + .5 - H / 2)) <= 2.3
    return [(m, Rm, base, "raised"), (ros, Rm, base + 0.6, "raised")]


def m_stars(W, H, Rm, base=5.0, waves=True, seed=1):
    """A five point star in the middle, little four point sparkles round it, a wave line low down."""
    rng = np.random.default_rng(seed)
    yy, xx = grid(W, H)
    cx, cy = W / 2, H / 2 - (0.5 if waves else 0)
    Rr = min(W, H) * 0.3
    th = np.arctan2(xx + .5 - cx, -(yy + .5 - cy)); rho = np.hypot(xx + .5 - cx, yy + .5 - cy)
    tri = 1 - np.abs(((th * 5 / (2 * math.pi)) % 1) * 2 - 1)
    star = rho < Rr * (0.45 + 0.55 * tri)
    sp = np.zeros((H, W), bool)
    for _ in range(40 if W > 9 and H > 8 else 0):
        x, y = rng.integers(4, W - 4), rng.integers(3, H - 4)
        if math.hypot(x - cx, y - cy) < Rr + 3 or sp[max(0, y - 3):y + 4, max(0, x - 3):x + 4].any(): continue
        sp[y, x] = True; sp[y - 1, x] = sp[y + 1, x] = sp[y, x - 1] = sp[y, x + 1] = rng.random() < 0.6
        if sp.sum() > W * H / 40: break
    out = [(star, Rm, base, "raised"), (sp, Rm, base + 0.8, "raised")]
    if waves and H >= 12:
        wy = np.round(H - 4 + np.sin((xx + .5) * 0.75)).astype(int)
        wm = (yy == wy) & (xx >= 3) & (xx < W - 3)
        out.append((wm, Rm, base - 0.6, "raised"))
    return out


def m_leaves(W, H, Rm, base=2.6, seed=2):
    """Carved vine: a wandering stem with leaves on alternate sides."""
    rng = np.random.default_rng(seed)
    yy, xx = grid(W, H)
    yc = H * 0.55 + np.sin((xx + .5) / W * math.pi * 2 + seed) * H * 0.16
    m = (np.abs(yy + .5 - yc) < 0.55) & (xx >= 3) & (xx < W - 3)
    side = 1
    for x in range(5, W - 5, 4):
        y = H * 0.55 + math.sin((x + .5) / W * math.pi * 2 + seed) * H * 0.16
        cx, cy = x + 1.2, y - side * 2.0
        dx, dy = xx + .5 - cx, yy + .5 - cy
        u = (dx - dy * side) / 1.414; w_ = (dy + dx * side) / 1.414
        m |= (u / 2.2) ** 2 + (w_ / 1.0) ** 2 < 1
        side = -side
    m &= (xx >= 3) & (xx < W - 3) & (yy >= 3) & (yy < H - 3)
    return [(m, Rm, base, "carved")]


def m_sun(W, H, Rm, base=4.4, cy=0.5, n=12):
    """Sunburst: a disc with long and short rays, painted raised."""
    yy, xx = grid(W, H)
    cxp, cyp = W / 2, H * cy
    rho = np.hypot(xx + .5 - cxp, yy + .5 - cyp); th = np.arctan2(yy + .5 - cyp, xx + .5 - cxp)
    r0 = max(2.0, min(W, H) * 0.16)
    disk = rho < r0
    k = (th * n / (2 * math.pi)) % 1
    idx = np.floor(th * n / (2 * math.pi)).astype(int) % n
    r1 = np.where(idx % 2 == 0, min(W, H) * 0.46, min(W, H) * 0.34)
    rays = (np.abs(k - 0.5) < 0.18) & (rho > r0 + 1) & (rho < r1)
    inner = (np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy]) >= 3)
    return [(rays & inner, Rm, base, "raised"), (disk & inner, Rm, base + 0.7, "raised")]


def m_runering(W, H, Rm, base=1.8):
    """Carved rune ring: a circle, an inner ring of tick marks, a dot in the centre."""
    yy, xx = grid(W, H)
    cx, cy = W / 2, H / 2
    rho = np.hypot(xx + .5 - cx, yy + .5 - cy); th = np.arctan2(yy + .5 - cy, xx + .5 - cx)
    r = min(W, H) * 0.38
    ring = np.abs(rho - r) < 0.6
    ticks = (np.abs(rho - (r - 2.2)) < 1.0) & ((th * 8 / (2 * math.pi)) % 1 < 0.22)
    dot = rho < 1.3
    return [(ring | ticks | dot, Rm, base, "carved")]


GLYPHS = ["100 110 101 100 100", "010 010 111 010 010", "101 101 010 101 101", "100 110 101 110 100",
          "111 001 010 100 111", "010 101 010 101 010", "100 101 111 101 001", "110 101 110 100 100"]


def runes_card(W, H, face, seed=0):
    """Glow card: runes 3x5 px with 1 px gaps, centred; everything else is transparent."""
    rng = np.random.default_rng(seed)
    a = np.zeros((H, W), bool)
    n = max(1, (W + 1) // 4)
    x0 = (W - (n * 4 - 1)) // 2; y0 = (H - 5) // 2
    for i in range(n):
        g = GLYPHS[rng.integers(len(GLYPHS))].split()
        for r, row in enumerate(g):
            for c, ch in enumerate(row):
                if ch == "1" and 0 <= y0 + r < H: a[y0 + r, x0 + i * 4 + c] = True
    yy, xx = grid(W, H)
    v = 5.2 - np.abs((yy + .5) / H - .5) * 1.6
    return Q(R["void"], v), a


# ------------------------------------------------------------------ surface painters
def painted(W, H, face, P, pw=6, orient="h", chip=0.0, border=None, motif=None, seed=0, base=3.8,
            shadow_top=0.0, shadow_bot=0.0, inset=2, grain_amt=0.14, gloss=0.0):
    """Painted planks: plank seams, grain showing faintly through the paint, brush streaks, a painted
    border trim, a motif, and chipped edges where the bare wood shows through."""
    rng = np.random.default_rng(seed)
    if orient == "v":
        yy, xx = grid(W, H); across, along, N = xx, yy, W
    else:
        yy, xx = grid(W, H); across, along, N = yy, xx, H
    n = max(1, round(N / pw)); cuts = [round(i * N / n) for i in range(n + 1)]
    v = np.full((H, W), base + LIGHT[face]) + form(W, H, 1.0, 0.35)
    seam = np.zeros((H, W), bool)
    for i in range(n):
        a0, a1 = cuts[i], cuts[i + 1]
        m = (across >= a0) & (across < a1)
        c = (across - a0 + .5) / max(1, a1 - a0)
        p1, p2 = rng.uniform(0, 6.28, 2)
        grain = np.sin(along * 0.3 + 2.0 * np.sin(across * 0.9 + p1) + p2)
        pv = 0.28 * (1 - (2 * c - 1) ** 2) - 0.14 + rng.uniform(-0.15, 0.15) + grain_amt * grain - 0.3 * (grain > 0.9)
        pv += 0.08 * np.sin(along * 1.7 + p2) * (rng.random() < 0.5)      # brush streaks
        v = np.where(m, v + pv, v)
        if i > 0:
            seam |= across == a0
            v = np.where(across == a0, np.minimum(v, base + LIGHT[face] - 1.7), v)
            v = np.where(across == a0 - 1, v - 0.3, v)
    v -= edge_band(H, 4, shadow_top)[:, None]
    v -= edge_band(H, 4, shadow_bot)[::-1][:, None]
    v += soft_noise(W, H, 0.15)
    if gloss and face != "down":                       # lacquer: a soft diagonal sheen across the face
        u = (xx + .5) / W; t = (yy + .5) / H
        v += gloss * np.exp(-((u + t * 0.45 - 0.42) / 0.09) ** 2) + gloss * 0.5 * np.exp(-((u + t * 0.45 - 0.62) / 0.04) ** 2)
    rgb = Q(P, v)
    keep = np.zeros((H, W), bool)
    if border is not None and W > 2 * inset + 2 and H > 2 * inset + 2:
        bm = ring_mask(W, H, inset)
        shade_mask(rgb, bm, border, 4.3, face, "raised"); keep |= bm
    if motif is not None:
        for mk, Rm, b, st in motif(W, H, face):
            shade_mask(rgb, mk, Rm, b, face, st); keep |= mk
    # chips: bare wood showing at worn edges and along seams
    if chip > 0:
        d = np.minimum.reduce([xx, yy, W - 1 - xx, H - 1 - yy])
        ch = np.zeros((H, W), bool)
        # flakes run along the edge or seam they start from: 2-5 px long, 1 px deep, 2 px in the middle
        for kind, cand_m, n in (("edge", (d == 0) & ~keep, int(chip * (W + H) / 6)),
                                ("seam", seam & ~keep & (d > 1), int(chip * (W + H) / 14))):
            cand = np.argwhere(cand_m)
            for _ in range(n):
                if not len(cand): break
                y, x = cand[rng.integers(len(cand))]
                horiz = (y == 0 or y == H - 1) if kind == "edge" else (orient == "h")
                if kind == "edge" and (x == 0 or x == W - 1) and not (y == 0 or y == H - 1): horiz = False
                L = int(rng.integers(2, 6)); s0 = -int(rng.integers(0, L))
                for k in range(L):
                    yy_, xx_ = (y, x + s0 + k) if horiz else (y + s0 + k, x)
                    if 0 <= yy_ < H and 0 <= xx_ < W: ch[yy_, xx_] = True
                    if 0 < k < L - 1 and rng.random() < 0.5:
                        if horiz:
                            yi = yy_ + (1 if y < H / 2 else -1)
                            if 0 <= yi < H and 0 <= xx_ < W: ch[yi, xx_] = True
                        else:
                            xi = xx_ + (1 if x < W / 2 else -1)
                            if 0 <= xi < W and 0 <= yy_ < H: ch[yy_, xi] = True
        ch &= ~keep
        wv = np.full((H, W), 3.4 + LIGHT[face]) + form(W, H, 0.6) + 0.3 * np.sin(along * 0.5)
        rgb[ch] = Q(R["wood"], wv)[ch]
        rim = shift(ch, -1, 0) & ~ch & ~keep          # paint lip just above a chip catches light
        rgb[rim] = Q(P, v + 0.7)[rim]
    return rgb, np.ones((H, W), bool)


def metal(W, H, face, Rm, base=3.6, rivets=None, engrave=None, rust=False):
    """Metal trim: rounded form, crisp lit top edge, faint scratches, optional rivets or an engraved line."""
    yy, xx = grid(W, H)
    v = np.full((H, W), base + LIGHT[face]) + form(W, H, 1.0, 0.4)
    if H >= 2 and face not in ("up", "down"):
        v += 0.8 * (yy == 0) - 0.4 * (yy == H - 1)
    for _ in range(W * H // 120):
        x0, y0 = RNG.integers(0, W), RNG.integers(0, H); d = RNG.choice([-1, 1])
        for k in range(RNG.integers(2, 4)):
            x, y = x0 + k, y0 + d * k
            if 0 <= x < W and 0 <= y < H: v[y, x] += 0.5
    if engrave == "line" and W >= 6 and H >= 4:
        v -= 0.9 * (((yy == 1) | (yy == H - 2)) & (xx >= 1) & (xx <= W - 2))
    if engrave == "vline" and W >= 4 and H >= 6:
        v -= 0.9 * (((xx == 1) | (xx == W - 2)) & (yy >= 1) & (yy <= H - 2))
    v += soft_noise(W, H, 0.15, max(1, W * H // 60))
    rgb = Q(Rm, v)
    if rust and W * H >= 12:
        t = (yy + .5) / H; u = np.abs((xx + .5) / W * 2 - 1)
        rm = t + 0.5 * u + RNG.uniform(-0.25, 0.25, (H, W)) > 1.3
        rgb[rm] = Q(R["leather"], np.full((H, W), 2.5) + form(W, H, 0.6))[rm]
    pts = []
    if rivets == "x" and H >= 2: pts = [((H - 2) // 2, x) for x in range(1, W - 1, 6)]
    if rivets == "y" and W >= 2: pts = [(y, (W - 2) // 2) for y in range(1, H - 1, 5)]
    if rivets == "ends" and H >= 2 and W >= 2: pts = [((H - 2) // 2, (W - 2) // 2)] if max(W, H) < 6 else \
        ([((H - 2) // 2, 1), ((H - 2) // 2, W - 3)] if W >= H else [(1, (W - 2) // 2), (H - 3, (W - 2) // 2)])
    for y, x in pts:
        rgb[y, x] = Rm[6]; rgb[y, x + 1] = Rm[5]; rgb[y + 1, x] = Rm[4]; rgb[y + 1, x + 1] = Rm[3]
    return rgb, np.ones((H, W), bool)


def leather(W, H, face, base=3.6, Rm=None):
    Rm = Rm or R["green_leather"]
    """Leather strap: rounded, stitched 1 px in from both long edges, soft creases."""
    yy, xx = grid(W, H)
    v = np.full((H, W), base + LIGHT[face]) + form(W, H, 1.0, 0.3) + soft_noise(W, H, 0.2)
    vert = H >= W
    if face not in ("up", "down") or True:
        if vert and W >= 4:
            st = ((xx == 1) | (xx == W - 2)) & (yy % 3 != 0)
        elif not vert and H >= 4:
            st = ((yy == 1) | (yy == H - 2)) & (xx % 3 != 0)
        else:
            st = np.zeros((H, W), bool)
        v -= 0.5 * (((yy * 7 + xx * 3) % 11) == 0)
        rgb = Q(Rm, v)
        rgb[st] = Q(Rm, v + 1.3)[st]
    return rgb, np.ones((H, W), bool)


def plate(W, H, face, Rm, shape="round", emblem=None, keyhole=True):
    """Lock plate with a cut-out outline (hard alpha), bevelled rim, keyhole and an optional emblem."""
    yy, xx = grid(W, H)
    u = (xx + .5) / W * 2 - 1; t = (yy + .5) / H * 2 - 1
    if face != "north":
        return metal(W, H, face, Rm, 3.8)
    if shape == "round":
        a = u ** 2 + t ** 2 <= 1.08
    elif shape == "shield":
        a = (t < 0.2) | (np.abs(u) < 1 - (t - 0.2) / 0.8 * 0.95)
        a &= ~((t < -0.75) & (np.abs(u) > 0.8))
    else:
        a = np.ones((H, W), bool)
    edge = a & ~(shift(a, 1, 0) & shift(a, -1, 0) & shift(a, 0, 1) & shift(a, 0, -1))
    v = np.full((H, W), 4.2 + LIGHT[face] * 0.6) + form(W, H, 1.0, 0.5)
    lit = edge & (t < 0.1); v += 0.9 * lit - 0.8 * (edge & ~lit)
    rgb = Q(Rm, v)
    if emblem == "star":
        for mk, Rr, b, st in m_stars(W, H, Rm, 5.3, waves=False, seed=4)[:1]:
            mk &= ~edge; shade_mask(rgb, mk & (yy < H * 0.55), Rr, b, face, st)
    if emblem == "rays":
        th = np.arctan2(t, u)
        rays = a & ~edge & ((th * 8 / (2 * math.pi)) % 1 < 0.3) & (u ** 2 + t ** 2 > 0.35)
        rgb[rays] = Q(Rm, v + 1.0)[rays]
    if keyhole:
        cx = W // 2 - 1; ky = int(H * 0.52)
        rgb[ky:ky + 2, cx:cx + 2] = Rm[0]
        rgb[ky + 2:ky + 4, cx:cx + 2] = Rm[1]
        rgb[ky + 2:ky + 4, cx + 1] = Rm[0]
        rgb[ky - 1, cx:cx + 2] = Rm[2]
    return rgb, a


def latch(W, H, face, Rm):
    rgb, a = metal(W, H, face, Rm, 3.9, rivets="ends" if face == "north" else None)
    if face == "north" and H >= 5:
        rgb[H - 2, 1:W - 1] = Rm[1]
    return rgb, a


def gem(W, H, face, Rm, glow=False):
    """Cut gem: facets as diagonal bands, bright table in the middle, a hard glint."""
    yy, xx = grid(W, H)
    u = (xx + .5) / W - .5; t = (yy + .5) / H - .5
    v = (4.4 if glow else 3.6) + LIGHT[face] * 0.4 - 2.2 * np.maximum(np.abs(u), np.abs(t)) + 0.6 * ((xx + yy) % 3 == 0) * (np.abs(u) > 0.2)
    rgb = Q(Rm, v)
    if W >= 3 and H >= 3: rgb[1, 1] = Rm[-1]
    return rgb, np.ones((H, W), bool)


RIM = None


def interior(W, H, face, lining):
    """Inside of the body: wall tops in bare wood, cloth lining shading into the corners, a few coins."""
    yy, xx = grid(W, H)
    rim = (xx < 2) | (xx >= W - 2) | (yy < 2) | (yy >= H - 2)
    d = np.minimum.reduce([xx - 1.5, W - 2.5 - xx, yy - 1.5, H - 2.5 - yy]).astype(float)
    v = 1.0 + np.clip(d / 6, 0, 1) * 1.8 + 0.25 * np.sin(xx * 0.9) * np.sin(yy * 0.4)  # cloth folds
    rgb = Q(lining, v)
    rgb[rim] = Q(RIM, np.full((H, W), 4.6) + 0.3 * np.sin(xx * 0.5 + yy * 0.5))[rim]
    return rgb, np.ones((H, W), bool)


def coins(W, H, face, accent):
    yy, xx = grid(W, H)
    v = np.full((H, W), 4.4 + LIGHT[face] * 0.8) + form(W, H, 1.4, 0.3) + 0.4 * np.sin(xx * 1.7) * np.sin(yy * 1.3)
    rgb = Q(R["gold"], v)
    if H >= 2 and W >= 2:
        for _ in range(max(2, W * H // 12)):
            x, y = int(RNG.integers(0, W - 1)), int(RNG.integers(0, H - 1))
            rgb[y, x] = R["gold"][6]; rgb[y + 1, x] = R["gold"][3]
    if face == "up" and W > 8:
        gx, gy = W // 2 - 1, H // 2 - 1
        rgb[gy, gx] = accent[5]; rgb[gy, gx + 1] = accent[3]; rgb[gy + 1, gx] = accent[2]; rgb[gy + 1, gx + 1] = accent[1]
    return rgb, np.ones((H, W), bool)


def lining_under(W, H, face, lining):
    yy, xx = grid(W, H)
    rim = (xx < 2) | (xx >= W - 2) | (yy < 2) | (yy >= H - 2)
    v = 1.6 + form(W, H, 0.8) + 0.3 * np.sin(yy * 0.8)
    rgb = Q(lining, v)
    rgb[rim] = Q(RIM, np.full((H, W), 3.8) + form(W, H, 0.5))[rim]
    return rgb, np.ones((H, W), bool)


# ------------------------------------------------------------------ model plumbing
FACES6 = ("north", "south", "east", "west", "up", "down")


class Chest:
    def __init__(self, name, seed):
        self.M = Model(name, 128, seed)
        self.name = name

    def box(self, name, grp, frm, to, painter, share=None, hide=("down",)):
        M = self.M; key0 = share or name; faces = {}
        for f in FACES6:
            if f in hide: continue
            w, h = face_dims(frm, to, f)
            W, H = round(w * PPU), round(h * PPU)
            assert abs(w * PPU - W) < 1e-6 and abs(h * PPU - H) < 1e-6, (name, f, w, h)
            if W == 0 or H == 0: continue
            faces[f] = F(M.rect(f"{key0}_{f}", W, H, (lambda W_, H_, _f=f: painter(W_, H_, _f))))
        return M.cube(name, grp, frm, to, faces)

    def group(self, name, origin, parent=None):
        return self.M.group(name, origin, parent if parent else self.M.name)

    def finish(self, open_deg=95):
        M = self.M
        img = M.pack()
        g = M.groups["lid"]

        def anim(nm, length, keys, loop):
            kfs = [{"channel": "rotation", "data_points": [{"x": str(x), "y": "0", "z": "0"}], "uuid": M.uid(), "time": t,
                    "color": -1, "interpolation": "catmullrom"} for t, x in keys]
            return {"uuid": M.uid(), "name": nm, "loop": loop, "override": False, "length": length, "snapping": 24,
                    "selected": False, "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
                    "animators": {g["uuid"]: {"name": "lid", "type": "bone", "keyframes": kfs}}}
        data = M.bbmodel()
        data["animations"] = [anim("open", 0.6, [(0.0, 0), (0.35, open_deg * 1.06), (0.6, open_deg)], "hold"),
                              anim("close", 0.5, [(0.0, open_deg), (0.4, 0), (0.45, 3), (0.5, 0)], "hold"),
                              anim("idle", 0.1, [(0.0, 0)], "once")]
        os.makedirs(OUT, exist_ok=True)
        Image.fromarray(M.img, "RGBA").save(os.path.join(OUT, f"{M.name}.png"))
        with open(os.path.join(OUT, f"{M.name}.bbmodel"), "w") as fh:
            json.dump(data, fh, separators=(",", ":"))
        cols = len(np.unique(img[img[..., 3] > 0][:, :3], axis=0))
        print(f"{M.name}: cubes {len(M.elements)}, atlas rows used {M.used}/128, colours {cols}")
        return M


# ------------------------------------------------------------------ the five chests
def red_chest():
    """Lacquer chest: glossy red paint with gold painted borders and a symmetric gold scroll vine,
    gold corner strips, an overhanging lid with a raised scroll panel, a round gold lock plate."""
    C = Chest("red_chest", 101); P, G = R["red"], R["gold"]
    global RIM; RIM = P
    body = C.group("body", [0, 0, 0])
    C.box("plinth", body, [-9.5, 0, -8.5], [9.5, 1.5, 8.5],
          lambda W, H, f: painted(W, H, f, P, 3, base=2.6, chip=0, seed=1))
    sc = lambda W, H, f: m_scroll(W, H, G)
    C.box("body_box", body, [-9, 1.5, -8], [9, 10, 8],
          lambda W, H, f: interior(W, H, f, R["velvet"]) if f == "up" else
          painted(W, H, f, P, 6, border=G, motif=sc, seed=10 + FACES6.index(f), shadow_top=0.9, shadow_bot=0.8, gloss=0.8, chip=0))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 8.5, sx * 9.5)); z0, z1 = sorted((sz * 7.5, sz * 8.5))
            C.box(f"corner_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body,
                  [x0, 1.5, z0], [x1, 9.5, z1], lambda W, H, f: metal(W, H, f, G, 4.0, engrave="vline"), share="corner")
    C.box("lock_plate", body, [-2, 5, -8.5], [2, 9, -8], lambda W, H, f: plate(W, H, f, G, "round"))
    for sx in (-1, 1):
        C.box(f"hinge_{'left' if sx < 0 else 'right'}", body, [sx * 5 - 1.5, 9.5, 8.5], [sx * 5 + 1.5, 10.5, 9.5],
              lambda W, H, f: metal(W, H, f, G, 3.8), share="hinge", hide=())
    t = C.group("treasure", [0, 10, 0], body)
    C.box("coin_mound", t, [-5, 10, -4], [5, 10.5, 4], lambda W, H, f: coins(W, H, f, R["ruby"]))
    lid = C.group("lid", [0, 10, 9])
    C.box("lid_box", lid, [-9.5, 10, -8.5], [9.5, 13.5, 8.5],
          lambda W, H, f: lining_under(W, H, f, R["velvet"]) if f == "down" else
          painted(W, H, f, P, 7 if f != "up" else 6, border=G, inset=1, seed=20 + FACES6.index(f), gloss=0.8, chip=0,
                  motif=None if f in ("east", "west") else (lambda W_, H_, f_: m_scroll(W_, H_, G)) if f == "north" else None),
          hide=())
    C.box("lid_panel", lid, [-7.5, 13.5, -6.5], [7.5, 14, 6.5],
          lambda W, H, f: painted(W, H, f, P, 6, border=G, inset=1, motif=sc if f == "up" else None, seed=30, base=4.0, gloss=0.8, chip=0))
    C.box("latch", lid, [-1, 8.5, -9], [1, 11.5, -8.5], lambda W, H, f: latch(W, H, f, G), hide=("south",))
    return C.finish()


def blue_chest():
    """Domed sea chest: vertical blue painted boards, silver bands top and bottom, a three step barrel lid
    crossed by two silver straps, painted stars, sparkles and a wave line, a silver shield lock with a star."""
    C = Chest("blue_chest", 202); P, S = R["blue"], R["silver"]
    global RIM; RIM = P
    body = C.group("body", [0, 0, 0])
    C.box("plinth", body, [-9.5, 0, -8.5], [9.5, 1, 8.5], lambda W, H, f: painted(W, H, f, P, 2, base=2.4, chip=0, seed=1))
    st = lambda W, H, f: m_stars(W, H, S, 5.0, waves=f in ("north", "south"), seed=FACES6.index(f) + 3)
    C.box("body_box", body, [-9, 1, -8], [9, 9.5, 8],
          lambda W, H, f: interior(W, H, f, P) if f == "up" else
          painted(W, H, f, P, 4, "v", motif=st, seed=40 + FACES6.index(f), shadow_top=0.7, shadow_bot=0.7))
    C.box("band_low", body, [-9.25, 1, -8.25], [9.25, 2, 8.25], lambda W, H, f: metal(W, H, f, S, 3.8, rivets="x"), hide=("up", "down"))
    C.box("band_top", body, [-9.25, 8.5, -8.25], [9.25, 9.5, 8.25], lambda W, H, f: metal(W, H, f, S, 3.9, rivets="x"), hide=("up", "down"))
    C.box("lock_plate", body, [-2, 4, -8.5], [2, 8.5, -8], lambda W, H, f: plate(W, H, f, S, "shield", "star"))
    for sx in (-1, 1):
        C.box(f"hinge_{'left' if sx < 0 else 'right'}", body, [sx * 3 - 1.5, 9, 8.5], [sx * 3 + 1.5, 10, 9.5],
              lambda W, H, f: metal(W, H, f, S, 3.8), share="hinge", hide=())
    t = C.group("treasure", [0, 9.5, 0], body)
    C.box("coin_mound", t, [-5, 9.5, -4], [5, 10, 4], lambda W, H, f: coins(W, H, f, R["sapph"]))
    lid = C.group("lid", [0, 9.5, 9])
    tiers = [([-9, 9.5, -8], [9, 12, 8]), ([-9, 12, -6.5], [9, 13.5, 6.5]), ([-9, 13.5, -4], [9, 14.5, 4])]
    for i, (a, b) in enumerate(tiers):
        C.box(f"lid_tier_{i + 1}", lid, a, b,
              lambda W, H, f, i=i: lining_under(W, H, f, P) if f == "down" else
              painted(W, H, f, P, 4, "v" if f in ("north", "south") else "h", seed=50 + i * 7 + FACES6.index(f),
                      motif=(lambda W_, H_, f_: m_stars(W_, H_, S, 5.2, False, 9 + i)) if (f == "up" and i == 2) else None),
              hide=() if i == 0 else ("down",))
        for sx in (-1, 1):
            C.box(f"lid_strap_{i + 1}_{'left' if sx < 0 else 'right'}", lid, [sx * 6 - 1, a[1], a[2] - 0.25],
                  [sx * 6 + 1, b[1] + 0.5, b[2] + 0.25], lambda W, H, f: metal(W, H, f, S, 3.8, rivets="ends"),
                  share=f"lid_strap_{i + 1}", hide=("down",))
    C.box("latch", lid, [-1, 7.5, -9], [1, 11, -8], lambda W, H, f: latch(W, H, f, S), hide=("south",))
    return C.finish()


def green_chest():
    """Ranger chest: green stained wood (heavily worn), carved leafy vines in a carved frame, block feet,
    bronze corner caps, leather straps with brass buckles over the lid, a bronze lock plate."""
    C = Chest("green_chest", 303); P, B = R["green"], R["gold"]
    global RIM; RIM = P
    body = C.group("body", [0, 0, 0])
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 6.5, sx * 9)); z0, z1 = sorted((sz * 5.5, sz * 8))
            C.box(f"foot_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body, [x0, 0, z0], [x1, 1.5, z1],
                  lambda W, H, f: painted(W, H, f, P, 3, base=2.0, chip=0, seed=2), share="foot")
        C.box("body_box", body, [-9, 1.5, -8], [9, 10, 8],
          lambda W, H, f: interior(W, H, f, P) if f == "up" else
          painted(W, H, f, P, 6, chip=0, seed=60 + FACES6.index(f), motif=lambda W_, H_, f_: m_leaves(W_, H_, P, 1.7, FACES6.index(f) + 1)
                  + [(ring_mask(W_, H_, 2), P, 1.9, "carved")], shadow_top=0.9, shadow_bot=0.6))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 8.5, sx * 9.5)); z0, z1 = sorted((sz * 7.5, sz * 8.5))
            C.box(f"corner_cap_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body,
                  [x0, 1.5, z0], [x1, 4.5, z1], lambda W, H, f: metal(W, H, f, B, 3.8, rivets="ends"), share="corner_cap")
    C.box("lock_plate", body, [-2, 5, -8.5], [2, 9, -8], lambda W, H, f: plate(W, H, f, B, "rect"))
    for sx in (-1, 1):
        sd = "left" if sx < 0 else "right"
        C.box(f"strap_body_{sd}", body, [sx * 5.5 - 1, 3, -8.5], [sx * 5.5 + 1, 10, -8], lambda W, H, f: leather(W, H, f), share="strap_body")
        C.box(f"buckle_{sd}", body, [sx * 5.5 - 1.5, 6, -9], [sx * 5.5 + 1.5, 8, -8.5],
              lambda W, H, f: (lambda r: (r[0], r[1] & ~((np.mgrid[0:H, 0:W][0] >= 1) & (np.mgrid[0:H, 0:W][0] <= H - 2)
                                                         & (np.mgrid[0:H, 0:W][1] >= 1) & (np.mgrid[0:H, 0:W][1] <= W - 2))
                                                         if f in ("north", "south") else r[1]))(metal(W, H, f, R["gold"], 4.2)),
              share="buckle", hide=())
    t = C.group("treasure", [0, 10, 0], body)
    C.box("coin_mound", t, [-5, 10, -4], [5, 10.5, 4], lambda W, H, f: coins(W, H, f, R["emerald"]))
    lid = C.group("lid", [0, 10, 8.25])
    C.box("lid_box", lid, [-9.25, 10, -8.25], [9.25, 13, 8.25],
          lambda W, H, f: lining_under(W, H, f, P) if f == "down" else
          painted(W, H, f, P, 6, chip=0, seed=70 + FACES6.index(f), shadow_bot=0.5), hide=())
    C.box("lid_top", lid, [-8.25, 13, -7.25], [8.25, 13.5, 7.25],
          lambda W, H, f: painted(W, H, f, P, 6, chip=0, seed=80, base=4.0,
                                  motif=(lambda W_, H_, f_: m_leaves(W_, H_, P, 2.0, 7) + [(ring_mask(W_, H_, 2), P, 2.0, "carved")]) if f == "up" else None))
    for sx in (-1, 1):
        sd = "left" if sx < 0 else "right"
        C.box(f"strap_lid_front_{sd}", lid, [sx * 5.5 - 1, 9.5, -8.75], [sx * 5.5 + 1, 13, -8.25], lambda W, H, f: leather(W, H, f), share="strap_lid_front")
        C.box(f"strap_lid_top_{sd}", lid, [sx * 5.5 - 1, 13, -8.75], [sx * 5.5 + 1, 14, 8.25], lambda W, H, f: leather(W, H, f), share="strap_lid_top")
    C.box("latch", lid, [-1, 8, -8.75], [1, 11, -8.25], lambda W, H, f: latch(W, H, f, B), hide=("south",))
    return C.finish()


def yellow_chest():
    """Sun chest: bright yellow paint with a raised amber sunburst, bronze borders and corner posts, a wide
    base, a stepped hip lid like a little roof topped by an amber gem knob, a round bronze sun lock."""
    C = Chest("yellow_chest", 404); P, B, A = R["yellow"], R["gold"], R["amber"]
    global RIM; RIM = P
    body = C.group("body", [0, 0, 0])
    C.box("plinth", body, [-10, 0, -9], [10, 1.5, 9], lambda W, H, f: metal(W, H, f, B, 3.2, rivets="x") if f != "up"
          else painted(W, H, f, B, 4, base=3.0, chip=0, seed=1))
    C.box("body_box", body, [-9, 1.5, -8], [9, 9.5, 8],
          lambda W, H, f: interior(W, H, f, A) if f == "up" else
          painted(W, H, f, P, 6, border=B, seed=90 + FACES6.index(f), shadow_top=0.9, shadow_bot=0.8,
                  motif=lambda W_, H_, f_: m_sun(W_, H_, A, 2.9, cy=0.55 if f in ("north", "south") else 0.5)))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 8.5, sx * 9.5)); z0, z1 = sorted((sz * 7.5, sz * 8.5))
            C.box(f"corner_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body,
                  [x0, 1.5, z0], [x1, 9, z1], lambda W, H, f: metal(W, H, f, B, 3.8, rivets="y"), share="corner")
    C.box("lock_plate", body, [-2.5, 4, -8.5], [2.5, 9, -8], lambda W, H, f: plate(W, H, f, B, "round", "rays"))
    for sx in (-1, 1):
        C.box(f"hinge_{'left' if sx < 0 else 'right'}", body, [sx * 5 - 1.5, 9, 8.5], [sx * 5 + 1.5, 10, 9.5],
              lambda W, H, f: metal(W, H, f, B, 3.8), share="hinge", hide=())
    t = C.group("treasure", [0, 9.5, 0], body)
    C.box("coin_mound", t, [-5, 9.5, -4], [5, 10, 4], lambda W, H, f: coins(W, H, f, R["ruby"]))
    lid = C.group("lid", [0, 9.5, 9])
    tiers = [([-9.5, 9.5, -8.5], [9.5, 11.5, 8.5]), ([-8, 11.5, -7], [8, 13, 7]), ([-6, 13, -5], [6, 14, 5])]
    for i, (a, b) in enumerate(tiers):
        C.box(f"lid_tier_{i + 1}", lid, a, b,
              lambda W, H, f, i=i: lining_under(W, H, f, A) if f == "down" else
              painted(W, H, f, P, 5, border=B if f != "up" or i == 2 else None, inset=1, seed=100 + i * 7 + FACES6.index(f),
                      motif=(lambda W_, H_, f_: m_sun(W_, H_, A, 2.9, 0.5, 8)) if (f == "up" and i == 2) else None),
              hide=() if i == 0 else ("down",))
    C.box("knob_base", lid, [-2, 14, -2], [2, 14.5, 2], lambda W, H, f: metal(W, H, f, B, 3.8))
    C.box("knob_gem", lid, [-1.5, 14.5, -1.5], [1.5, 16, 1.5], lambda W, H, f: gem(W, H, f, A))
    C.box("latch", lid, [-1, 8, -9], [1, 11, -8.5], lambda W, H, f: latch(W, H, f, B), hide=("south",))
    return C.finish()


def purple_chest():
    """Arcane chest: dark purple boards with a faint gunmetal border and carved rune rings, gunmetal claw feet
    and corners, an arched two step lid, glowing rune bands (`_glow` cards) and a glowing crystal lock."""
    C = Chest("purple_chest", 505); P, Gm = R["purple"], R["gunmetal"]
    global RIM; RIM = P
    body = C.group("body", [0, 0, 0])
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 7.5, sx * 9.5)); z0, z1 = sorted((sz * 6, sz * 8.5))
            C.box(f"claw_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body, [x0, 0, z0], [x1, 1, z1],
                  lambda W, H, f: metal(W, H, f, Gm, 3.4), share="claw")
    C.box("plinth", body, [-9.5, 1, -8.5], [9.5, 2, 8.5], lambda W, H, f: painted(W, H, f, P, 2, base=2.2, chip=0, seed=3))
    C.box("body_box", body, [-9, 2, -8], [9, 10, 8],
          lambda W, H, f: interior(W, H, f, P) if f == "up" else
          painted(W, H, f, P, 4, "v", base=3.2, border=Gm, seed=110 + FACES6.index(f), shadow_top=0.9, shadow_bot=0.7,
                  motif=(lambda W_, H_, f_: m_runering(W_, H_, P, 1.6)) if f == "south" else None))
    for sx in (-1, 1):
        for sz in (-1, 1):
            x0, x1 = sorted((sx * 8.5, sx * 9.5)); z0, z1 = sorted((sz * 7.5, sz * 8.5))
            C.box(f"corner_{'front' if sz < 0 else 'back'}_{'left' if sx < 0 else 'right'}", body,
                  [x0, 2, z0], [x1, 9.5, z1], lambda W, H, f: metal(W, H, f, Gm, 3.6, rivets="y"), share="corner")
    C.box("lock_plate", body, [-2, 4.5, -8.5], [2, 9, -8], lambda W, H, f: plate(W, H, f, Gm, "shield", keyhole=False))
    C.box("crystal_glow", body, [-1, 5.5, -9], [1, 8, -8.5], lambda W, H, f: gem(W, H, f, R["void"], glow=True), hide=("south",))
    C.box("runes_front_left_glow", body, [-7.5, 4, -8.05], [-3, 7.5, -8.05], lambda W, H, f: runes_card(W, H, f, 1), hide=("south", "down", "up"))
    C.box("runes_front_right_glow", body, [3, 4, -8.05], [7.5, 7.5, -8.05], lambda W, H, f: runes_card(W, H, f, 2), hide=("south", "down", "up"))
    C.box("runes_right_glow", body, [9.05, 4, -6], [9.05, 7.5, 6], lambda W, H, f: runes_card(W, H, f, 3), hide=("west", "down", "up"))
    C.box("runes_left_glow", body, [-9.05, 4, -6], [-9.05, 7.5, 6], lambda W, H, f: runes_card(W, H, f, 4), hide=("east", "down", "up"))
    for sx in (-1, 1):
        C.box(f"hinge_{'left' if sx < 0 else 'right'}", body, [sx * 5 - 1.5, 9.5, 8.5], [sx * 5 + 1.5, 10.5, 9.5],
              lambda W, H, f: metal(W, H, f, Gm, 3.6), share="hinge", hide=())
    t = C.group("treasure", [0, 10, 0], body)
    C.box("coin_mound", t, [-5, 10, -4], [5, 10.5, 4], lambda W, H, f: coins(W, H, f, R["void"]))
    lid = C.group("lid", [0, 10, 9])
    tiers = [([-9.25, 10, -8.25], [9.25, 12.5, 8.25]), ([-9.25, 12.5, -6], [9.25, 14, 6]), ([-9.25, 14, -3], [9.25, 14.5, 3])]
    for i, (a, b) in enumerate(tiers):
        C.box(f"lid_tier_{i + 1}", lid, a, b,
              lambda W, H, f, i=i: lining_under(W, H, f, P) if f == "down" else
              painted(W, H, f, P, 4, "h", base=3.3, seed=120 + i * 7 + FACES6.index(f),
                      motif=(lambda W_, H_, f_: m_runering(W_, H_, P, 1.8)) if (f in ("east", "west") and i == 0) else None),
              hide=() if i == 0 else ("down",))
    for sx in (-1, 1):   # gunmetal end caps on the lid ends
        x0, x1 = sorted((sx * 9.25, sx * 9.75))
        C.box(f"lid_cap_{'left' if sx < 0 else 'right'}", lid, [x0, 10, -8.5], [x1, 12.5, 8.5],
              lambda W, H, f: metal(W, H, f, Gm, 3.6, rivets="x" if f in ("east", "west") else None), share="lid_cap",
              hide=("down", "west" if sx > 0 else "east"))
    C.box("latch", lid, [-1, 9, -8.75], [1, 11.5, -8.25], lambda W, H, f: latch(W, H, f, Gm), hide=("south",))
    return C.finish()


BUILDERS = {"red": red_chest, "blue": blue_chest, "green": green_chest, "yellow": yellow_chest, "purple": purple_chest}

if __name__ == "__main__":
    which = sys.argv[1:] or list(BUILDERS)
    models = [BUILDERS[k]() for k in which]
    if not sys.argv[1:]:
        tc = os.path.join(HERE, "..", "treasure_chest", "build_treasure_chest.py")   # outside the repo; optional
        offs = [(m, (-45 + 30 * i, 0)) for i, m in enumerate(models)]
        if os.path.exists(tc):
            offs = [(runpy.run_path(tc)["M"], (-75, 0))] + offs
        showcase(offs, "chests_showcase", OUT, tex=512, seed=9)
        print("showcase written")
