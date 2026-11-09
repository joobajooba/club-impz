"""High-detail hub cobblestone (J00BA, 2026-11-09: "increase the detail of the stone texture floor").

256 x 256 for 4 m, so 64 px per metre: twice the other terrain layers. The terrain loader
(scripts/terrain/terrain_world.gd) scales the 128 px layers up with nearest filtering to match, so they look
the same. Tiles seamlessly: every distance and noise wraps round the edges.

About 240 rounded cobbles (~25 cm), relaxed so they're evenly sized, in three stones: grey, warm limestone
(the castle's stone) and cool slate. Each stone is domed and lit from the top left, lighter in the middle and
darker at its rim (house style), with its own shade, fine grain, a worn polished top, the odd crack and chipped
corner. The joints are dark soil with sand grains, small pebbles, moss and a few grass blades.
Colours are snapped to 8 shade ramps with ordered dithering, so it stays crisp pixel art.

Usage: python tools/generate_hub_cobblestone.py [--preview out_3x3.png]"""
import sys
from pathlib import Path

import numpy as np
from PIL import Image

S = 256
SEED = 9061
OUT = Path(__file__).resolve().parent.parent / "godot-game" / "assets" / "textures" / "terrain" / "hub_cobblestone.png"


def ramp(s):
    return np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in s.split()], float)


STONE_RAMPS = [
    ramp("#24221f #34302b #47423b #5b554c #706960 #877f74 #9f978a #b8b0a2"),     # grey
    ramp("#2e271f #433a2e #5a4e3e #726450 #8a7b64 #a2927a #b9a98f #cdbfa4"),     # warm limestone
    ramp("#222429 #313439 #43474d #575b61 #6c7075 #82868a #9a9da0 #b2b4b5"),     # cool slate (muted)
]
SOIL = ramp("#16120d #211a13 #2c2319 #382d20 #45382a #534436")
SAND = ramp("#5a4e3c #6e604a #84755c #9a8a6e")
MOSS = ramp("#1a2a10 #253a15 #324c1b #416022 #52752b #668a36")
GRASS = ramp("#2a4a0e #3a6212 #4d7a18 #63921f #7aad1d")
BAYER = np.array([[0, 8, 2, 10], [12, 4, 14, 6], [3, 11, 1, 9], [15, 7, 13, 5]]) / 16.0 - 0.47


def periodic_noise(cells, seed):
    g = np.random.default_rng(seed).random((cells, cells))
    t = np.arange(S) / S * cells
    i0 = np.floor(t).astype(int); f = t - i0; f = f * f * (3 - 2 * f); i1 = (i0 + 1) % cells
    a, b, c, d = g[np.ix_(i0, i0)], g[np.ix_(i0, i1)], g[np.ix_(i1, i0)], g[np.ix_(i1, i1)]
    fx, fy = f[None, :], f[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(cells, octaves, seed):
    n = sum(0.5 ** o * periodic_noise(min(cells << o, S), seed + 31 * o) for o in range(octaves))
    return (n - n.min()) / (n.max() - n.min())


def wrap_d(a, b):
    d = np.abs(a - b) % S
    return np.minimum(d, S - d)


def voronoi(pts, warp):
    yy, xx = np.mgrid[0:S, 0:S].astype(np.float32)
    xx = xx + warp[0]; yy = yy + warp[1]
    d = np.sqrt(wrap_d(xx[None], pts[:, 0, None, None].astype(np.float32)) ** 2 +
                wrap_d(yy[None], pts[:, 1, None, None].astype(np.float32)) ** 2)
    ids = np.argmin(d, 0)
    part = np.partition(d, 1, axis=0)
    return part[0], part[1], ids


def relax(pts, iters=3):
    """Lloyd relaxation on the torus: even stone sizes, still irregular."""
    yy, xx = np.mgrid[0:S, 0:S]
    for _ in range(iters):
        _, _, ids = voronoi(pts, (0, 0))
        new = pts.copy()
        for k in range(len(pts)):
            m = ids == k
            if not m.any(): continue
            ax = xx[m] / S * 2 * np.pi; ay = yy[m] / S * 2 * np.pi
            new[k, 0] = (np.arctan2(np.sin(ax).mean(), np.cos(ax).mean()) / (2 * np.pi) * S) % S
            new[k, 1] = (np.arctan2(np.sin(ay).mean(), np.cos(ay).mean()) / (2 * np.pi) * S) % S
        pts = new
    return pts


def to_ramp(R, v, yy, xx):
    """v in ramp steps (0 .. len-1), ordered dither between neighbours, snapped to the ramp."""
    q = np.clip(np.floor(v + 0.5 + BAYER[yy % 4, xx % 4] * 0.4), 0, len(R) - 1).astype(int)
    return R[q]


def main():
    rng = np.random.default_rng(SEED)
    n = 240
    pts = relax(rng.random((n, 2)) * S)
    warp = ((fbm(8, 2, SEED + 1) - 0.5) * 3.0, (fbm(8, 2, SEED + 2) - 0.5) * 3.0)
    f1, f2, ids = voronoi(pts, warp)
    edge = f2 - f1
    yy, xx = np.mgrid[0:S, 0:S]
    gap = 1.5 + 1.1 * fbm(16, 2, SEED + 3)                               # joints 1.5 to 2.6 px wide
    inside = edge > gap
    # ---- stone height: a dome per stone, with a little lumpiness
    t = np.clip((edge - gap) / 5.0, 0, 1)
    h = 1 - (1 - t) ** 2.2
    tilt = rng.uniform(-0.25, 0.25, (n, 2))
    lump = fbm(32, 2, SEED + 4) - 0.5
    h = h + 0.18 * lump * t
    # ---- lighting from the top left (house style: light centre, darker rim), plus a soft ambient term
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    light = -(gx * 0.75 + gy * 0.75) * 6.0
    kind = rng.choice(3, n, p=[0.58, 0.27, 0.15])
    base = rng.uniform(2.6, 3.9, n) - (kind == 2) * 0.2
    v = base[ids] + 1.3 * h + light - 1.1 * (1 - t) ** 2                       # domed, darker rim
    v = v + 0.55 * ((light > 0.35) & (t > 0.25) & (t < 0.75))              # a highlight on the lit shoulder
    v += 0.45 * (fbm(64, 1, SEED + 5) - 0.5) * 2 * t                      # fine grain, low contrast
    worn = (t > 0.62) & (fbm(16, 2, SEED + 6) > 0.55)                      # polished tops where feet wear them
    v = v + worn * 0.6
    # cracks across some stones: a dark line with a light lip under it
    crack_noise = fbm(24, 3, SEED + 7)
    crack = (np.abs(crack_noise - 0.5) < 0.012) & (t > 0.25) & (rng.random(n) < 0.35)[ids]
    lip = np.roll(crack, 1, 0) & ~crack
    v = np.where(crack, v - 2.0, v)
    v = np.where(lip & inside, v + 0.6, v)
    # chipped rims: a few bites out of stone edges become joint
    chips = (t < 0.18) & (fbm(48, 1, SEED + 8) > 0.78)
    inside = inside & ~chips
    img = np.zeros((S, S, 3))
    tint = rng.integers(-2, 3, n)[ids][..., None] * np.array([0.022, 0.006, -0.022])   # per stone warm / cool hue
    for k in range(3):
        m = inside & (kind[ids] == k)
        img[m] = (to_ramp(STONE_RAMPS[k], v, yy, xx) * (1 + tint))[m]
    # ---- joints: dark soil (darker deep in the joint), sand grains, pebbles, moss, grass
    jd = np.clip(edge / np.maximum(gap, 0.1), 0, 1)                       # 0 centre of the joint, 1 at the stone
    sv = 1.0 + 1.6 * jd + 1.0 * (fbm(32, 2, SEED + 9) - 0.5)
    joint = ~inside
    img[joint] = to_ramp(SOIL, sv, yy, xx)[joint]
    grains = joint & (rng.random((S, S)) < 0.12)
    img[grains] = SAND[rng.integers(0, 4, (S, S))][grains]
    moss_zone = fbm(6, 3, SEED + 10) > 0.56
    moss = joint & moss_zone & (rng.random((S, S)) < 0.8)
    mv = 1.2 + 2.8 * fbm(48, 1, SEED + 11) + 0.8 * jd
    img[moss] = to_ramp(MOSS, mv, yy, xx)[moss]
    creep = inside & moss_zone & (t < 0.2) & (rng.random((S, S)) < 0.35)  # moss creeping onto the rims
    img[creep] = to_ramp(MOSS, mv - 0.6, yy, xx)[creep]
    for _ in range(70):                                                    # pebbles sitting in the joints
        cand = np.argwhere(joint & (edge < 1.0))
        y, x = cand[rng.integers(len(cand))]
        R = STONE_RAMPS[rng.integers(3)]
        img[y % S, x % S] = R[5]; img[y % S, (x + 1) % S] = R[4]; img[(y + 1) % S, x % S] = R[2]
    for _ in range(26):                                                    # grass blades from the joints
        cand = np.argwhere(joint & moss_zone)
        if not len(cand): break
        y, x = cand[rng.integers(len(cand))]
        L = int(rng.integers(2, 5)); lean = rng.choice([-1, 0, 1])
        for i in range(L):
            yy_, xx_ = (y - i) % S, (x + (lean if i >= L // 2 else 0)) % S
            img[yy_, xx_] = GRASS[min(4, 1 + i)]
    out = np.clip(np.rint(img), 10, 248).astype(np.uint8)
    Image.fromarray(out, "RGB").save(OUT, optimize=True)
    print(OUT, out.shape, len(np.unique(out.reshape(-1, 3), axis=0)), "colours")
    if "--preview" in sys.argv:
        Image.fromarray(np.tile(out, (3, 3, 1))).save(sys.argv[sys.argv.index("--preview") + 1])


if __name__ == "__main__":
    main()
