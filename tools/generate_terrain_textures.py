"""Generate the tiling terrain textures for Club Impz.

Spec: docs/terrain_textures.md (built from blockbench_detailed_prompts.md
sections 1.5, 3.12 and 5, and game_worlds.md section 4.8).

Every texture is 128 x 128 (4 m at 32 px per metre) and tiles seamlessly in
both directions: all noise, cells and strokes wrap around the edges.

Usage:
    python3 tools/generate_terrain_textures.py            # writes the PNGs
    python3 tools/generate_terrain_textures.py --preview  # also writes 3 x 3 previews (tools/previews/)
                                                          # and the contact sheet in docs/images/

Change a colour or a seed below and run it again to tune a texture.
"""

import argparse
import math
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

S = 128
ROOT = Path(__file__).resolve().parent.parent
OUT_DIR = ROOT / "godot-game" / "assets" / "textures" / "terrain"
PREVIEW_DIR = ROOT / "tools" / "previews"  # git ignored
SHEET_PATH = ROOT / "docs" / "images" / "terrain_textures_preview.png"
# Warm tint pushes red up and blue down, cool tint the opposite (hue shift, not brightness)
TINT = np.array([0.035, 0.012, -0.035])


# ---------------------------------------------------------------- helpers


def ramp(*hexes):
    return np.array([[int(h[i:i + 2], 16) for i in (1, 3, 5)] for h in hexes], float)


def value_noise(cx, cy, seed):
    """Periodic value noise with cx x cy cells across the tile."""
    g = np.random.default_rng(seed).random((cy, cx))
    tx = np.arange(S) / S * cx
    ty = np.arange(S) / S * cy
    x0 = np.floor(tx).astype(int)
    y0 = np.floor(ty).astype(int)
    fx = tx - x0
    fy = ty - y0
    fx = fx * fx * (3 - 2 * fx)
    fy = fy * fy * (3 - 2 * fy)
    x1 = (x0 + 1) % cx
    y1 = (y0 + 1) % cy
    a = g[np.ix_(y0, x0)]
    b = g[np.ix_(y0, x1)]
    c = g[np.ix_(y1, x0)]
    d = g[np.ix_(y1, x1)]
    fx = fx[None, :]
    fy = fy[:, None]
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def fbm(cells, octaves, seed, cy=None):
    cy = cy or cells
    n = np.zeros((S, S))
    amp = 1.0
    for o in range(octaves):
        n += amp * value_noise(min(cells << o, S), min(cy << o, S), seed + o * 101)
        amp *= 0.5
    return (n - n.min()) / (n.max() - n.min())


def clusters(seed):
    """Small 2 to 4 px clusters of shade change, centred on 0."""
    n = 0.5 * value_noise(32, 32, seed) + 0.5 * value_noise(64, 64, seed + 7)
    return n - 0.5


def shade(h, k):
    """Light from the top left: slopes facing up-left get lighter."""
    gx = (np.roll(h, -1, 1) - np.roll(h, 1, 1)) / 2
    gy = (np.roll(h, -1, 0) - np.roll(h, 1, 0)) / 2
    return (gx + gy) * k


def voronoi(n, seed, sx=1.0, sy=1.0, warp=0.0):
    r = np.random.default_rng(seed)
    pts = r.random((n, 2)) * S
    yy, xx = np.mgrid[0:S, 0:S].astype(float)
    if warp:
        xx = xx + warp * (fbm(4, 2, seed + 1) - 0.5) * 2
        yy = yy + warp * (fbm(4, 2, seed + 2) - 0.5) * 2
    dx = np.abs(xx[None] - pts[:, 0, None, None]) % S
    dy = np.abs(yy[None] - pts[:, 1, None, None]) % S
    dx = np.minimum(dx, S - dx) * sx
    dy = np.minimum(dy, S - dy) * sy
    d = np.sqrt(dx * dx + dy * dy)
    ids = np.argmin(d, 0)
    part = np.partition(d, 1, axis=0)
    return part[0], part[1], ids


class Tex:
    def __init__(self, name, seed):
        self.name = name
        self.r = np.random.default_rng(seed)
        self.img = np.zeros((S, S, 3))
        t = fbm(4, 3, self.seed())
        self.tint = np.digitize(t, [0.25, 0.42, 0.58, 0.75]) / 2.0 - 1.0  # 5 steps, -1 to 1

    def seed(self):
        return int(self.r.integers(1 << 30))

    def colour(self, rmp, level, y=None, x=None):
        idx = np.clip(np.rint(np.asarray(level) * (len(rmp) - 1)), 0, len(rmp) - 1).astype(int)
        tint = self.tint if y is None else self.tint[y % S, x % S]
        return rmp[idx] * (1 + np.asarray(tint)[..., None] * TINT)

    def fill(self, rmp, level, mask=None):
        col = self.colour(rmp, level)
        if mask is None:
            self.img[:] = col
        else:
            self.img[mask] = col[mask]

    def px(self, x, y, rmp, level):
        y %= S
        x %= S
        self.img[y, x] = self.colour(rmp, level, y, x)

    def darken(self, x, y, f=0.78):
        self.img[y % S, x % S] *= np.array([f - 0.03, f - 0.01, f + 0.05])

    def save(self, out_dir):
        arr = np.clip(np.rint(self.img), 10, 248).astype(np.uint8)
        Image.fromarray(arr, "RGB").save(out_dir / f"{self.name}.png", optimize=True)
        return arr


# ---------------------------------------------------------------- shapes


def blades(t, rmp, count, length=(2, 5), base=0.25, rise=0.4, under=None, lean=0.3, shadow=True):
    """Short grass blades seen from above: dark root pixel, lighter tip."""
    r = t.r
    rows = []
    for _ in range(count):
        rows.append((int(r.integers(S)), int(r.integers(S))))
    rows.sort(key=lambda p: p[1])
    for x, y in rows:
        n = int(r.integers(length[0], length[1] + 1))
        b = base + r.uniform(-0.08, 0.08) + (0.2 * under[y, x] if under is not None else 0)
        dx = 0.0
        slope = r.uniform(-lean, lean)
        if shadow:
            t.darken(x + 1, y + 1, 0.82)
        for i in range(n):
            t.px(x + int(round(dx)), y - i, rmp, b + rise * i / max(n - 1, 1))
            dx += slope


def pebble(t, x, y, w, h, rmp, base=0.45, contrast=0.35, shadow=True):
    for j in range(-h, h + 1):
        for i in range(-w, w + 1):
            u = i / (w + 0.5)
            v = j / (h + 0.5)
            q = u * u + v * v
            if q <= 1:
                light = (-u - v) * 0.5
                t.px(x + i, y + j, rmp, base + contrast * light + (1 - q) * 0.1)
            elif shadow and q <= 1.9 and i >= 0 and j >= 0:
                t.darken(x + i, y + j, 0.8)


def flower(t, x, y, rmp, centre_rmp=None, size=1):
    if size == 1:
        t.px(x, y, rmp, 0.85)
        t.darken(x + 1, y + 1, 0.85)
        return
    for i, j, lv in ((0, -1, 0.95), (-1, 0, 0.85), (1, 0, 0.7), (0, 1, 0.6)):
        t.px(x + i, y + j, rmp, lv)
    t.px(x, y, centre_rmp if centre_rmp is not None else rmp, 0.9)
    t.darken(x + 1, y + 2, 0.8)
    t.darken(x + 2, y + 1, 0.8)


def leaf(t, x, y, length, width, angle, rmp):
    ca, sa = math.cos(angle), math.sin(angle)
    reach = int(length) + 1
    for j in range(-reach, reach + 1):
        for i in range(-reach, reach + 1):
            u = (i * ca + j * sa) / length
            v = (-i * sa + j * ca) / width
            q = u * u + v * v * (1 + 0.6 * u)
            if q <= 1:
                lv = 0.55 + 0.25 * (-v) - 0.15 * abs(u)
                if abs(v) < 0.22 and abs(u) < 0.8:
                    lv -= 0.2
                t.px(x + i, y + j, rmp, lv)
    t.darken(x + 1, y + int(width) + 1, 0.82)


def stones(t, n, rmp, seed, sx=1.0, sy=1.0, warp=3.0, gap=1.2, radius=5.0, var=0.18, k=2.4, flat=False):
    f1, f2, ids = voronoi(n, seed, sx, sy, warp)
    edge = f2 - f1
    inside = edge > gap
    hgt = np.clip((edge - gap) / radius, 0, 1)
    hgt = np.clip(hgt * 2.2, 0, 1) if flat else np.sqrt(hgt)
    off = np.random.default_rng(seed + 9).uniform(-var, var, n)[ids]
    lvl = 0.42 + off + shade(hgt, k) + 0.1 * hgt + 0.12 * clusters(seed + 3)
    t.fill(rmp, lvl, inside)
    return inside, edge, ids


def cracks(t, n, seed, width=0.9, warp=4.0, sx=1.0, sy=1.0, strength=0.72, mask=None):
    f1, f2, _ = voronoi(n, seed, sx, sy, warp)
    c = (f2 - f1) < width
    if mask is not None:
        c &= mask
    lit = np.roll(c, (1, 1), (0, 1)) & ~c
    t.img[lit] *= 1.12
    t.img[c] *= np.array([strength - 0.04, strength - 0.02, strength + 0.06])
    return c


def bubble(t, x, y, rad, rmp):
    for j in range(-rad - 1, rad + 2):
        for i in range(-rad - 1, rad + 2):
            d = math.hypot(i, j)
            if abs(d - rad) < 0.6:
                lv = 0.9 if (i + j) < 0 else 0.35
                t.px(x + i, y + j, rmp, lv)
            elif d < rad - 0.4:
                t.px(x + i, y + j, rmp, 0.6)
    t.px(x - rad // 2, y - rad // 2, rmp, 1.0)


def scatter(t, count):
    return [(int(t.r.integers(S)), int(t.r.integers(S))) for _ in range(count)]


# ---------------------------------------------------------------- ramps (dark to light, hue shifted)

R = {
    "forest_grass": ramp("#283f10", "#33500b", "#3f5e0c", "#4d6f0d", "#587e0e", "#648f10", "#70a017", "#7aad1d"),
    "dry_grass": ramp("#463c14", "#5e5418", "#76691e", "#8e7f26", "#a8952e", "#c0aa3c", "#d4bf52", "#e4d26e"),
    "forest_dirt": ramp("#2a1a14", "#3a2618", "#4c321f", "#5e4028", "#714f31", "#86603c", "#9a7249"),
    "forest_path": ramp("#3a2a20", "#523c28", "#684e34", "#7e6040", "#94744e", "#a8885e", "#ba9a6e"),
    "grey_stone": ramp("#1c1e26", "#2c2f38", "#3e424c", "#545862", "#6c707a", "#8a8e96", "#aeb2b8"),
    "warm_stone": ramp("#2a2220", "#3e332e", "#554740", "#6e5e54", "#8a786a", "#a89484", "#c0ae9c"),
    "moss": ramp("#1e3014", "#2e481a", "#42621f", "#5c7e28", "#7a9a34", "#94b444"),
    "root": ramp("#1a100c", "#2a1a12", "#3c2618", "#523422", "#6a4630"),
    "leaf_green": ramp("#1f3a14", "#2e521a", "#3f6c20", "#548a28", "#6ca832", "#88c040"),
    "leaf_yellow": ramp("#5a4210", "#7a5c14", "#a07c1a", "#c49e26", "#e0bc3a", "#f0d460"),
    "leaf_brown": ramp("#3a1e10", "#542c16", "#70401e", "#8c5628", "#a86e34", "#c08848"),
    "leaf_red": ramp("#4a1410", "#78201a", "#a8361e", "#d2582a", "#ec8436"),
    "flower_white": ramp("#8a90a8", "#b8bccc", "#dcdee6", "#eef0f2", "#f8f6ec"),
    "flower_blue": ramp("#28306a", "#3a4c9a", "#5a74c8", "#86a0e4", "#b4c8f4"),
    "flower_pink": ramp("#6a2448", "#9a3a68", "#c85a8c", "#e888b0", "#f8b8d0"),
    "flower_yellow": ramp("#7a5008", "#b07c10", "#dca81c", "#f4cc3c", "#fce478"),
    "mountain_grass": ramp("#262e14", "#38441a", "#4a5620", "#5c6a28", "#6e7c30", "#84903c", "#9aa44c"),
    "heather": ramp("#3a1e52", "#52286e", "#6a3a8a", "#8a52a8", "#b878d0"),
    "mountain_rock": ramp("#1c2030", "#2c3240", "#3c4352", "#4e5666", "#626a7a", "#7a8292", "#959cab", "#b0b6c2"),
    "lichen": ramp("#4a5420", "#6a7a2c", "#8a9a3a", "#a8b44a", "#c4c860"),
    "lichen_orange": ramp("#6a3410", "#9a5018", "#c07028", "#dc9040", "#ecb060"),
    "mountain_snow": ramp("#8296b6", "#a0b2cc", "#bccadc", "#d0dcea", "#e2eaf4", "#eef3f9", "#f6f8fb"),
    "frost_snow": ramp("#7088be", "#8ea6d2", "#aac0e2", "#c4d4ee", "#d8e4f5", "#e8f0f9", "#f4f7fc"),
    "packed_snow": ramp("#66748e", "#8492aa", "#9caac0", "#b4c0d2", "#c8d2e0", "#dae2ec", "#e8eef4"),
    "ice": ramp("#1a3048", "#244462", "#2e5070", "#3c6288", "#4874a0", "#6c9cc8", "#9cc8e8", "#d0ecf8"),
    "frost_rock": ramp("#343c4c", "#4a5464", "#606a7c", "#7a8496", "#949eae", "#aeb8c6", "#c8d0da"),
    "tundra": ramp("#28342e", "#3a483e", "#4c5a4c", "#5e6c5c", "#727e6c", "#86927c", "#9ca890"),
    "tundra_orange": ramp("#5a2c12", "#8a4a1a", "#b0602a", "#d07a36", "#e8a050"),
    "plains_grass": ramp("#54441a", "#74601f", "#8e7826", "#a8902e", "#c0a63a", "#d6bc4c", "#e6d066", "#f0e08a"),
    "plains_green": ramp("#264214", "#3a5e1c", "#4a7424", "#5c8a2c", "#70a036", "#86b444", "#9cc658"),
    "plains_dirt": ramp("#381a14", "#52261a", "#6a3420", "#82442a", "#9a5634", "#b06a40", "#c4804e"),
    "plains_rock": ramp("#46302a", "#644630", "#7e5a3c", "#987048", "#b08658", "#c49c6a", "#d6b27e", "#e4c492"),
    "plains_path": ramp("#584230", "#765a3e", "#90704e", "#a8865e", "#bc9a6e", "#ceae80", "#dcc092"),
    "swamp_mud": ramp("#1a1814", "#26221a", "#342e20", "#423a28", "#504830", "#5e5638", "#6c6644"),
    "swamp_water": ramp("#10181a", "#16221e", "#1e2e26", "#2a3c30", "#3a4e3a", "#56684a"),
    "swamp_moss": ramp("#18261a", "#22341c", "#2e4622", "#3a5828", "#486a30", "#587c3a", "#6c9046"),
    "swamp_grass": ramp("#1a2012", "#262e16", "#343c1c", "#424a22", "#50582a", "#606832", "#70783c"),
    "slime": ramp("#163416", "#20501a", "#2c6c22", "#3a8a2a", "#52a834", "#78c644", "#a2dc5c", "#c8ee84"),
    "board": ramp("#22191a", "#32261e", "#443424", "#56422e", "#685238", "#7a6244", "#8c7252", "#9c8262"),
    "board_gap": ramp("#0e1410", "#141c16", "#1c261c"),
    "nail": ramp("#2a2c34", "#4a4e58", "#767c88", "#a4aab4"),
    "hub_grass": ramp("#284a14", "#346018", "#42741c", "#508822", "#5e9c2a", "#70b034", "#86c444"),
    "hub_path": ramp("#3a2a1e", "#503826", "#664830", "#7c5a3c", "#926c48", "#a67e56", "#b89066"),
    "cobble": ramp("#2a2828", "#3c3834", "#504a44", "#665e56", "#7c736a", "#928a80", "#aaa298", "#c0b8ac"),
    "mortar": ramp("#1e1814", "#2a2218", "#3a3022", "#4a3e2c"),
}


# ---------------------------------------------------------------- textures


def grass_base(t, rmp, cells=8, low=0.22, span=0.35, jitter=0.14):
    base = fbm(cells, 3, t.seed())
    t.fill(rmp, low + span * base + jitter * clusters(t.seed()))
    return base


def hub_grass(t):
    base = grass_base(t, R["hub_grass"], low=0.28)
    blades(t, R["hub_grass"], 2600, (2, 4), base=0.3, rise=0.5, under=base)
    for x, y in scatter(t, 10):
        flower(t, x, y, R["flower_white"], R["flower_yellow"], size=2)
    for x, y in scatter(t, 30):
        flower(t, x, y, R["flower_white"])


def hub_dirt_path(t):
    path(t, R["hub_path"], R["warm_stone"], gravel=200, flat_stones=14, grass_rmp=R["hub_grass"])


def hub_cobblestone(t):
    t.fill(R["mortar"], 0.4 + 0.5 * fbm(16, 2, t.seed()))
    inside, edge, _ = stones(t, 64, R["cobble"], t.seed(), warp=2.5, gap=1.6, radius=3.5, var=0.16, flat=True)
    moss = (~inside) & (fbm(4, 3, t.seed()) > 0.58)
    t.fill(R["moss"], 0.3 + 0.5 * fbm(32, 1, t.seed()), moss)
    for x, y in scatter(t, 14):
        if not inside[y, x]:
            blades(t, R["hub_grass"], 3, (2, 3), base=0.35, rise=0.4)


def forest_grass(t):
    base = grass_base(t, R["forest_grass"])
    blades(t, R["forest_grass"], 2800, (2, 5), base=0.25, rise=0.55, under=base)
    dry = fbm(4, 2, t.seed()) > 0.7
    for x, y in scatter(t, 400):
        if dry[y, x]:
            blades(t, R["dry_grass"], 1, (3, 5), base=0.3, rise=0.4)
    for x, y in scatter(t, 6):
        flower(t, x, y, R["flower_white"])
    for x, y in scatter(t, 4):
        flower(t, x, y, R["flower_yellow"])


def forest_grass_dry(t):
    base = grass_base(t, R["dry_grass"], low=0.2)
    blades(t, R["dry_grass"], 2400, (3, 6), base=0.25, rise=0.6, under=base, lean=0.5)
    green = fbm(8, 2, t.seed()) > 0.6
    for x, y in scatter(t, 700):
        if green[y, x]:
            blades(t, R["forest_grass"], 1, (2, 4), base=0.35, rise=0.45)
    for x, y in scatter(t, 5):
        flower(t, x, y, R["flower_blue"], R["flower_yellow"], size=2)


def forest_dirt(t):
    base = fbm(8, 3, t.seed())
    t.fill(R["forest_dirt"], 0.25 + 0.4 * base + 0.14 * clusters(t.seed()))
    # roots: wandering lines with a lit top edge
    for _ in range(5):
        x, y = float(t.r.integers(S)), float(t.r.integers(S))
        ang = t.r.uniform(0, math.tau)
        for _ in range(int(t.r.integers(14, 30))):
            t.px(int(x), int(y), R["root"], 0.25)
            t.px(int(x), int(y) - 1, R["root"], 0.75)
            ang += t.r.uniform(-0.4, 0.4)
            x += math.cos(ang)
            y += math.sin(ang)
    for x, y in scatter(t, 40):
        pebble(t, x, y, int(t.r.integers(1, 3)), int(t.r.integers(1, 2)), R["grey_stone"], base=t.r.uniform(0.4, 0.6))
    for x, y in scatter(t, 120):
        t.px(x, y, R["forest_dirt"], 0.95)
    for x, y in scatter(t, 6):
        leaf(t, x, y, 2.5, 1.5, t.r.uniform(0, math.pi), R["leaf_brown"])


def forest_leaf_litter(t):
    base = fbm(8, 3, t.seed())
    t.fill(R["forest_dirt"], 0.15 + 0.3 * base + 0.1 * clusters(t.seed()))
    ramps = [R["leaf_green"], R["leaf_yellow"], R["leaf_brown"], R["leaf_brown"], R["leaf_yellow"]]
    for x, y in scatter(t, 520):
        leaf(t, x, y, t.r.uniform(2.2, 4.2), t.r.uniform(1.2, 2.2), t.r.uniform(0, math.pi), ramps[int(t.r.integers(len(ramps)))])
    for _ in range(6):
        x, y = int(t.r.integers(S)), int(t.r.integers(S))
        for i in range(int(t.r.integers(5, 10))):
            t.px(x + i, y + i // 3, R["root"], 0.55)
            t.darken(x + i, y + i // 3 + 1, 0.8)


def path(t, rmp, gravel_rmp, gravel=220, flat_stones=10, grass_rmp=None):
    """Packed, trodden earth: lighter worn streaks, grit, gravel and a few flat stones."""
    base = fbm(16, 3, t.seed())
    worn = fbm(8, 2, t.seed(), cy=2)  # long streaks along the path direction (v)
    t.fill(rmp, 0.28 + 0.3 * base + 0.18 * worn + 0.16 * clusters(t.seed()))
    for x, y in scatter(t, 500):
        t.px(x, y, rmp, t.r.choice([0.15, 0.85]))
    for x, y in scatter(t, gravel):
        t.px(x, y, gravel_rmp, t.r.uniform(0.35, 0.85))
        t.darken(x + 1, y + 1, 0.86)
    for x, y in scatter(t, flat_stones):
        pebble(t, x, y, int(t.r.integers(2, 5)), int(t.r.integers(1, 3)), gravel_rmp, base=t.r.uniform(0.45, 0.6), contrast=0.25)
    if grass_rmp is not None:
        for x, y in scatter(t, 40):
            blades(t, grass_rmp, 1, (2, 3), base=0.35, rise=0.4)


def forest_path(t):
    path(t, R["forest_path"], R["grey_stone"], grass_rmp=R["forest_grass"])


def mountain_grass(t):
    base = grass_base(t, R["mountain_grass"])
    blades(t, R["mountain_grass"], 2500, (2, 5), base=0.25, rise=0.55, under=base, lean=0.5)
    for x, y in scatter(t, 60):
        blades(t, R["dry_grass"], 1, (3, 5), base=0.25, rise=0.4)
    heather = fbm(8, 2, t.seed()) > 0.72
    for x, y in scatter(t, 600):
        if heather[y, x]:
            flower(t, x, y, R["heather"])
    for x, y in scatter(t, 5):
        pebble(t, x, y, 2, 1, R["mountain_rock"], base=0.5)


def mountain_rock(t):
    s = t.seed()
    stones(t, 26, R["mountain_rock"], s, sx=0.55, sy=1.5, warp=6, gap=0.7, radius=7, var=0.14, k=3.0)
    strata = np.sin(2 * math.pi * 7 * np.arange(S)[:, None] / S + 6 * fbm(4, 2, t.seed())) > 0.55
    t.img[strata] *= 0.93
    cracks(t, 60, t.seed(), width=0.6, warp=5, sx=0.7, sy=1.3)
    lich = fbm(16, 2, t.seed()) > 0.8
    t.fill(R["lichen"], 0.15 + 0.5 * fbm(32, 1, t.seed()), lich)
    for x, y in scatter(t, 12):
        for i, j in ((0, 0), (1, 0), (0, 1)):
            t.px(x + i, y + j, R["lichen_orange"], 0.5 + 0.2 * i)


def mountain_scree(t):
    t.fill(R["mountain_rock"], 0.1 + 0.15 * fbm(16, 2, t.seed()))
    stones(t, 230, R["mountain_rock"], t.seed(), warp=2.0, gap=1.0, radius=2.5, var=0.22, k=2.2)
    for x, y in scatter(t, 12):
        pebble(t, x, y, int(t.r.integers(3, 6)), int(t.r.integers(2, 4)), R["mountain_rock"], base=t.r.uniform(0.45, 0.65))
    for x, y in scatter(t, 25):
        t.px(x, y, R["lichen"], 0.6)


def snow(t, rmp, k=(3, 1), ripple=0.12, sparkles=50, warp=1.6):
    yy, xx = np.mgrid[0:S, 0:S]
    w = warp * math.tau * (fbm(4, 3, t.seed()) - 0.5)
    phase = math.tau * (k[0] * xx + k[1] * yy) / S + w
    h = 0.5 + 0.5 * np.sin(phase)
    h = h ** 2.5  # sharp crests, wide troughs like wind ripples
    drift = fbm(4, 3, t.seed())
    lvl = 0.5 + 0.3 * drift + ripple * (h - 0.5) + shade(h * 4, 0.9) + 0.05 * clusters(t.seed())
    t.fill(rmp, lvl)
    for x, y in scatter(t, sparkles):
        t.px(x, y, rmp, 1.0)
    return drift


def mountain_snow(t):
    snow(t, R["mountain_snow"], k=(2, 1), ripple=0.08, sparkles=35)
    for x, y in scatter(t, 8):
        pebble(t, x, y, int(t.r.integers(1, 3)), 1, R["mountain_rock"], base=0.4)


def mountain_path(t):
    path(t, R["warm_stone"], R["mountain_rock"], gravel=260, flat_stones=16, grass_rmp=R["mountain_grass"])


def frost_snow(t):
    snow(t, R["frost_snow"], k=(4, 2), ripple=0.16, sparkles=70)
    for x, y in scatter(t, 6):
        blades(t, R["tundra_orange"], 1, (2, 3), base=0.35, rise=0.4)


def frost_ice(t):
    lvl = 0.25 + 0.45 * fbm(4, 3, t.seed()) + 0.06 * clusters(t.seed())
    t.fill(R["ice"], lvl)
    deep = fbm(8, 2, t.seed()) < 0.3
    t.fill(R["ice"], lvl - 0.15, deep)
    frost = fbm(8, 3, t.seed()) > 0.68
    t.fill(R["ice"], 0.8 + 0.2 * fbm(64, 1, t.seed()), frost)
    f1, f2, _ = voronoi(9, t.seed(), warp=8)
    big = (f2 - f1) < 0.9
    t.img[np.roll(big, (1, 1), (0, 1)) & ~big] *= np.array([0.78, 0.82, 0.9])
    t.fill(R["ice"], np.full((S, S), 1.0), big)
    cracks(t, 40, t.seed(), width=0.5, warp=4, strength=0.85)
    for x, y in scatter(t, 30):
        t.px(x, y, R["ice"], 0.95)
        t.px(x + 1, y + 1, R["ice"], 0.6)
    for x, y in scatter(t, 25):
        t.px(x, y, R["ice"], 1.0)


def frost_packed_snow(t):
    base = fbm(8, 3, t.seed())
    t.fill(R["packed_snow"], 0.35 + 0.35 * base + 0.08 * clusters(t.seed()))
    tracks = fbm(16, 2, t.seed(), cy=2)  # trodden streaks along the path direction (v)
    t.fill(R["packed_snow"], 0.25 + 0.3 * base + 0.25 * tracks + 0.1 * clusters(t.seed()))
    for x, y in scatter(t, 14):
        pebble(t, x, y, int(t.r.integers(2, 4)), int(t.r.integers(1, 3)), R["packed_snow"], base=0.45, contrast=-0.3, shadow=False)
    for x, y in scatter(t, 300):
        t.px(x, y, R["packed_snow"], t.r.choice([0.2, 0.9]))
    for x, y in scatter(t, 20):
        t.px(x, y, R["forest_dirt"], 0.35)
    for x, y in scatter(t, 30):
        t.px(x, y, R["ice"], 0.85)


def frost_rock(t):
    stones(t, 40, R["frost_rock"], t.seed(), sx=0.8, sy=1.2, warp=5, gap=0.9, radius=6, var=0.15, k=2.6)
    cracks(t, 50, t.seed(), width=0.6, warp=4)
    snowcap = fbm(16, 3, t.seed()) > 0.64
    t.fill(R["frost_snow"], 0.6 + 0.3 * fbm(32, 1, t.seed()), snowcap)
    edge = snowcap & ~np.roll(snowcap, (-1, -1), (0, 1))
    t.fill(R["frost_snow"], np.full((S, S), 0.3), edge)


def frost_tundra(t):
    base = grass_base(t, R["tundra"])
    blades(t, R["tundra"], 2200, (2, 4), base=0.25, rise=0.5, under=base, lean=0.4)
    orange = fbm(8, 2, t.seed()) > 0.62
    for x, y in scatter(t, 900):
        if orange[y, x]:
            blades(t, R["tundra_orange"], 1, (3, 5), base=0.3, rise=0.5)
    patches = fbm(16, 2, t.seed()) > 0.8
    t.fill(R["frost_snow"], 0.55 + 0.35 * fbm(32, 2, t.seed()), patches)
    for x, y in scatter(t, 8):
        pebble(t, x, y, 1, 1, R["frost_rock"], base=0.45)


def plains_grass(t):
    base = grass_base(t, R["plains_grass"], low=0.18)
    blades(t, R["plains_grass"], 2400, (4, 7), base=0.22, rise=0.65, under=base, lean=0.6)
    for x, y in scatter(t, 140):
        blades(t, R["plains_green"], 1, (3, 4), base=0.35, rise=0.35)
    for x, y in scatter(t, 6):
        flower(t, x, y, R["flower_white"], R["flower_yellow"], size=2)
    for x, y in scatter(t, 6):
        flower(t, x, y, R["heather"])


def plains_grass_green(t):
    base = grass_base(t, R["plains_green"])
    blades(t, R["plains_green"], 2700, (2, 5), base=0.25, rise=0.55, under=base, lean=0.4)
    for x, y in scatter(t, 150):
        blades(t, R["plains_grass"], 1, (3, 5), base=0.35, rise=0.4)
    for x, y in scatter(t, 8):
        flower(t, x, y, R["flower_yellow"], size=2)


def plains_dirt(t):
    base = fbm(8, 3, t.seed())
    t.fill(R["plains_dirt"], 0.3 + 0.35 * base + 0.1 * clusters(t.seed()))
    dust = fbm(4, 2, t.seed()) > 0.6
    t.fill(R["plains_dirt"], 0.6 + 0.25 * base + 0.05 * clusters(t.seed()), dust)
    cracks(t, 34, t.seed(), width=0.8, warp=5, strength=0.68)
    for x, y in scatter(t, 80):
        t.px(x, y, R["plains_rock"], t.r.uniform(0.4, 0.8))
    for x, y in scatter(t, 10):
        pebble(t, x, y, int(t.r.integers(1, 3)), 1, R["plains_rock"], base=0.5)
    for x, y in scatter(t, 10):
        blades(t, R["plains_grass"], 1, (2, 4), base=0.3, rise=0.4)


def plains_rock(t):
    yy = np.mgrid[0:S, 0:S][0].astype(float)
    wob = 8 * (fbm(4, 2, t.seed()) - 0.5)
    band = np.floor((yy + wob) / 8).astype(int) % 16
    offs = t.r.uniform(-0.2, 0.2, 16)
    grain = fbm(8, 3, t.seed(), cy=32)
    h = ((yy + wob) % 8) / 8
    lvl = 0.45 + offs[band] + 0.2 * (grain - 0.5) + 0.12 * (0.5 - h) + 0.08 * clusters(t.seed())
    t.fill(R["plains_rock"], lvl)
    ledge = ((yy + wob) % 8) < 1
    t.fill(R["plains_rock"], np.full((S, S), 0.15), ledge)
    t.fill(R["plains_rock"], np.full((S, S), 0.9), np.roll(ledge, 1, 0) & ~ledge)
    cracks(t, 20, t.seed(), width=0.5, warp=3, sx=1.6, sy=0.5)
    for x, y in scatter(t, 40):
        t.px(x, y, R["plains_rock"], 1.0)


def plains_path(t):
    path(t, R["plains_path"], R["plains_rock"], gravel=120, flat_stones=6, grass_rmp=R["plains_grass"])


def swamp_mud(t):
    base = fbm(8, 3, t.seed())
    lvl = 0.2 + 0.45 * base + 0.12 * clusters(t.seed())
    t.fill(R["swamp_mud"], lvl)
    wet = fbm(8, 3, t.seed())
    pools = wet < 0.22
    t.fill(R["swamp_water"], 0.25 + 0.3 * fbm(16, 2, t.seed()), pools)
    rim = pools & ~np.roll(pools, (-1, -1), (0, 1))
    t.fill(R["swamp_water"], np.full((S, S), 0.95), rim)
    cracks(t, 28, t.seed(), width=0.7, warp=5, strength=0.7, mask=wet > 0.55)
    for x, y in scatter(t, 70):
        if not pools[y, x]:
            t.px(x, y, R["swamp_water"], 1.0)
    for x, y in scatter(t, 14):
        if pools[y, x]:
            bubble(t, x, y, 1, R["swamp_water"])
    for x, y in scatter(t, 8):
        for i in range(int(t.r.integers(3, 7))):
            t.px(x + i, y, R["root"], 0.5)


def swamp_moss(t):
    base = grass_base(t, R["swamp_moss"], cells=16, low=0.15, span=0.3, jitter=0.2)
    # spongy cushions: soft overlapping domes
    for x, y in scatter(t, 160):
        pebble(t, x, y, int(t.r.integers(2, 5)), int(t.r.integers(2, 4)), R["swamp_moss"], base=t.r.uniform(0.35, 0.6), contrast=0.3)
    blades(t, R["swamp_moss"], 900, (1, 2), base=0.4, rise=0.4, under=base, shadow=False)
    for x, y in scatter(t, 300):
        t.px(x, y, R["swamp_moss"], t.r.uniform(0.7, 1.0))
    for x, y in scatter(t, 40):
        t.px(x, y, R["flower_yellow"], 0.2)
        t.px(x, y - 1, R["lichen"], 0.8)


def swamp_grass(t):
    base = grass_base(t, R["swamp_grass"], low=0.18)
    blades(t, R["swamp_grass"], 2400, (3, 6), base=0.22, rise=0.55, under=base, lean=0.6)
    damp = fbm(8, 2, t.seed()) < 0.24
    t.fill(R["swamp_mud"], 0.2 + 0.4 * fbm(16, 2, t.seed()), damp)
    for x, y in scatter(t, 600):
        if damp[y, x]:
            blades(t, R["swamp_grass"], 1, (2, 4), base=0.25, rise=0.5)
    for x, y in scatter(t, 60):
        t.px(x, y, R["swamp_moss"], 0.8)


def swamp_slime(t):
    w = fbm(4, 3, t.seed())
    swirl = fbm(8, 3, t.seed())
    v = 0.5 + 0.5 * np.sin(math.tau * (2 * swirl + 1.5 * w))
    t.fill(R["slime"], 0.22 + 0.4 * v + 0.08 * clusters(t.seed()))
    mud = fbm(8, 2, t.seed()) < 0.28
    t.fill(R["swamp_mud"], 0.2 + 0.4 * fbm(32, 2, t.seed()), mud)
    for x, y in scatter(t, 26):
        if not mud[y, x]:
            bubble(t, x, y, int(t.r.integers(1, 4)), R["slime"])
    for x, y in scatter(t, 80):
        if not mud[y, x]:
            t.px(x, y, R["slime"], 1.0)


def swamp_boardwalk(t):
    plank_h = 16
    grain = fbm(4, 3, t.seed(), cy=32)
    t.fill(R["board"], 0.3 + 0.4 * grain + 0.1 * clusters(t.seed()))
    for p in range(S // plank_h):
        y0 = p * plank_h
        rows = slice(y0, y0 + plank_h)
        seams = sorted(int(v) for v in t.r.integers(0, S, int(t.r.integers(1, 3))))
        off = t.r.uniform(-0.15, 0.15)
        t.img[rows] *= 1 + off
        t.fill(R["board_gap"], np.full((S, S), 0.3), np.isin(np.arange(S), [y0, y0 + 1])[:, None] & np.ones((1, S), bool))
        t.img[y0 + 2] *= 1.14
        t.img[y0 + plank_h - 1] *= 0.82
        for sx in seams:
            for y in range(y0 + 2, y0 + plank_h):
                t.px(sx, y, R["board_gap"], 0.2)
                t.darken(sx + 1, y, 0.85)
            for dx in (-3, 3):
                for ny in (y0 + 5, y0 + plank_h - 4):
                    t.px(sx + dx, ny, R["nail"], 0.8)
                    t.px(sx + dx + 1, ny + 1, R["nail"], 0.2)
        for _ in range(int(t.r.integers(0, 2))):
            kx, ky = int(t.r.integers(S)), y0 + int(t.r.integers(5, plank_h - 4))
            pebble(t, kx, ky, 2, 1, R["board"], base=0.2, contrast=0.2, shadow=False)
    moss = fbm(8, 3, t.seed()) > 0.76
    t.fill(R["moss"], 0.2 + 0.5 * fbm(32, 2, t.seed()), moss)


TEXTURES = [
    ("hub", "hub_grass", hub_grass),
    ("hub", "hub_dirt_path", hub_dirt_path),
    ("hub", "hub_cobblestone", hub_cobblestone),
    ("forest", "forest_grass", forest_grass),
    ("forest", "forest_grass_dry", forest_grass_dry),
    ("forest", "forest_dirt", forest_dirt),
    ("forest", "forest_leaf_litter", forest_leaf_litter),
    ("forest", "forest_path", forest_path),
    ("mountain", "mountain_grass", mountain_grass),
    ("mountain", "mountain_rock", mountain_rock),
    ("mountain", "mountain_scree", mountain_scree),
    ("mountain", "mountain_snow", mountain_snow),
    ("mountain", "mountain_path", mountain_path),
    ("frost", "frost_snow", frost_snow),
    ("frost", "frost_ice", frost_ice),
    ("frost", "frost_packed_snow", frost_packed_snow),
    ("frost", "frost_rock", frost_rock),
    ("frost", "frost_tundra", frost_tundra),
    ("plains", "plains_grass", plains_grass),
    ("plains", "plains_grass_green", plains_grass_green),
    ("plains", "plains_dirt", plains_dirt),
    ("plains", "plains_rock", plains_rock),
    ("plains", "plains_path", plains_path),
    ("swamp", "swamp_mud", swamp_mud),
    ("swamp", "swamp_moss", swamp_moss),
    ("swamp", "swamp_grass", swamp_grass),
    ("swamp", "swamp_slime", swamp_slime),
    ("swamp", "swamp_boardwalk", swamp_boardwalk),
]


def contact_sheet(images, path):
    cell = 2 * S
    cols = 5
    biomes = []
    for biome, name, arr in images:
        if not biomes or biomes[-1][0] != biome:
            biomes.append((biome, []))
        biomes[-1][1].append((name, arr))
    sheet = Image.new("RGB", (cols * (cell + 16) + 16, len(biomes) * (cell + 36) + 16), (24, 26, 32))
    draw = ImageDraw.Draw(sheet)
    for row, (biome, items) in enumerate(biomes):
        for col, (name, arr) in enumerate(items):
            x = 16 + col * (cell + 16)
            y = 16 + row * (cell + 36)
            sheet.paste(Image.fromarray(np.tile(arr, (2, 2, 1))), (x, y))
            draw.text((x, y + cell + 6), name, fill=(220, 224, 232))
    sheet.save(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", type=Path, default=OUT_DIR)
    ap.add_argument("--preview", action="store_true",
                    help="also write 3 x 3 tile previews to tools/previews/ and the contact sheet to docs/images/")
    args = ap.parse_args()
    args.out.mkdir(parents=True, exist_ok=True)
    images = []
    for i, (biome, name, fn) in enumerate(TEXTURES):
        t = Tex(name, 1000 + i * 37)
        fn(t)
        arr = t.save(args.out)
        colours = len(np.unique(arr.reshape(-1, 3), axis=0))
        print(f"{name:22s} {colours:4d} colours")
        images.append((biome, name, arr))
    if args.preview:
        PREVIEW_DIR.mkdir(parents=True, exist_ok=True)
        SHEET_PATH.parent.mkdir(parents=True, exist_ok=True)
        for _, name, arr in images:
            Image.fromarray(np.tile(arr, (3, 3, 1))).save(PREVIEW_DIR / f"{name}_3x3.png")
        contact_sheet(images, SHEET_PATH)
        print(f"previews in {PREVIEW_DIR}, contact sheet at {SHEET_PATH}")


if __name__ == "__main__":
    main()
