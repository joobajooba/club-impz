"""The Head traits (implingz_collection.md section 4), shapes from docs/imp-traits/layers/head_*.png, scaled to the model.
None is bald, so it has no file. Skull: x +-15, y 63-91, z -9 to 19 (front). Horn roots fill x >= 8.6, z 0-10 above y 83, so hats narrow there.
The brows reach y 83, so front edges stop at about that. Viewer's left is -X."""
import math
import numpy as np
from head_lib import *

HEAD_C = (0, 90, 5)


def shell(t, name, y0, y1, sh, W=15.5, zf=19.5, zb=-9.5):
    """One solid piece over the whole skull, so no green shows. The horns and ears come out through it."""
    t.box(name, (-W, y0, zb), (W, y1, zf), sh)


def step(t, name, y0, y1, W, Wmid, zf, zb, sh):
    """A narrower storey on top: wider in front of and behind the horns than between them."""
    t.box(name + '_front', (-W, y0, 10.5), (W, y1, zf), sh)
    t.box(name + '_back', (-W, y0, zb), (W, y1, -.5), sh)
    t.box(name + '_mid', (-Wmid, y0, -.5), (Wmid, y1, 10.5), sh)


def spike(t, name, base, w, d, heights, sh, rx=0, rz=0, **kw):
    """A stepped spike: each storey narrower, all rotated about the base."""
    x, y, z = base
    y0 = y
    for i, h in enumerate(heights):
        hw, hd = max(w - 2 * i, 1) / 2, max(d - 2 * i, 1) / 2
        t.box(f'{name}_{i + 1}', (x - hw, y0, z - hd), (x + hw, y0 + h, z + hd), sh, rot=(rx, 0, rz), origin=base, **kw)
        y0 += h


def fez():
    t = Trait('head_fez')
    red = ['#48070d', '#821c25', '#ce1d1d', '#e12a2a', '#f63535']
    sh = S(red, c=(0, 98, 5), r=(9, 11, 9), base=.46, gain=.40, face=.04)
    t.box('felt_a', (-8, 90.5, -3), (8, 106.5, 13), sh)
    t.box('felt_b', (-6, 90.5, -5), (6, 106.5, 15), sh)
    dark = S(['#2a0408', '#48070d', '#6b0f18', '#821c25', '#a02a33'], base=.5, gain=.15)
    t.box('tassel_cord', (0, 106.5, 4.5), (9, 107.5, 5.5), dark)
    t.box('tassel_drop', (8, 100.5, 4.5), (9, 106.5, 5.5), dark)
    t.box('tassel', (7, 95.5, 3.5), (10, 100.5, 6.5), dark)
    return t


def crown():
    t = Trait('head_crown')
    gold = ['#70571b', '#8a6b20', '#b38b26', '#d9ab3a', '#ffd467']
    gem = ['#6e1a1a', '#ac3232', '#c84646', '#d95763', '#ee9aa0']

    def top(u):
        """Five points, the middle one tallest."""
        peaks = np.abs(((u / 23 + .5) * 5) % 1 - .5) * 2           # 1 between points, 0 at a point
        centre = np.abs(u) < 2.3
        return 96.5 + (1 - peaks) * np.where(centre, 6.5, 3.6)

    def keep(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2] - 5, P[..., 0])
        return P[..., 1] < top(u)

    def gems(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2] - 5, P[..., 0])
        on_band = (np.abs(P[..., 1] - 93.5) < 1.1) & (np.abs(((u + 11.5) % 4.6) - 2.3) < 1.1)
        return on_band

    sh = S(gold, c=(0, 95, 5), r=(10, 7, 10), base=.56, gain=.24, cut=keep, decals=[(gems, gem, lambda P, N: .5 + .25 * (P[..., 1] > 93.5))],
           mods=[lambda P, N, t: t + .16 * (np.abs(P[..., 1] - 91.8) < .6) - .12 * (np.abs(P[..., 1] - 95.6) < .5)])
    faces = ('north', 'south', 'east', 'west')
    t.box('band_front', (-11.5, 90.5, 10.5), (11.5, 105.5, 11.5), sh, faces=('north', 'south'), solid=False)
    t.box('band_back', (-11.5, 90.5, -1.5), (11.5, 105.5, -.5), sh, faces=('north', 'south'), solid=False)
    t.mirror('band_side', (7.5, 90.5, -.5), (8.5, 105.5, 10.5), sh, faces=('east', 'west'), solid=False)
    return t


def halo():
    t = Trait('head_halo')
    gold = ['#9c6e00', '#ce9300', '#ffb600', '#ffd56d', '#ffe9a8']
    R_, Y = 13, 110
    # bright front edge, orange-gold back edge
    sh = lambda P, N, c: (ramp(.28 + .62 * ((P[..., 2] - 5) / (2 * R_) + .5) + .12 * (N[..., 1] > .5), gold), np.full(P.shape[:2], 255.))
    tilt = math.radians(14)
    cx_, sx_ = math.cos(tilt), math.sin(tilt)
    Rt = np.array([[1, 0, 0], [0, cx_, -sx_], [0, sx_, cx_]])
    for k in range(8):
        a = k * math.pi / 4
        Ry = np.array([[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]])
        R = Rt @ Ry
        ex = math.degrees(math.atan2(R[2, 1], R[2, 2]))      # Blockbench rotates Z, then Y, then X
        ey = math.degrees(math.asin(-R[2, 0]))
        ez = math.degrees(math.atan2(R[1, 0], R[0, 0]))
        p = Rt @ np.array([R_ * math.sin(a), 0, R_ * math.cos(a)])
        x, y, z = p[0], Y + p[1], 5 + p[2]
        t.box(f'ring_{k + 1}', (x - 5.5, y - 1, z - 1), (x + 5.5, y + 1, z + 1), sh, rot=(ex, ey, ez), origin=(x, y, z), solid=False)
    return t


def geezer():
    t = Trait('head_geezer')
    grey = ['#5c5757', '#9e9c9c', '#b4b4b4', '#cacaca', '#e0dddd']

    def hash2(P):
        i = np.floor(P[..., 0] * .5) * 12.9898 + np.floor(P[..., 1] * .5) * 78.233 + np.floor(P[..., 2] * .5) * 37.719
        return (np.sin(i) * 43758.5453) % 1

    mods = [lambda P, N, t: t + (hash2(P) - .5) * .9]       # the doc's speckled stubble, in 2 px patches
    top_keep = lambda P, N: (hash2(P) > .05) | (np.abs(P[..., 0]) < 6)
    fan = lambda P, N: np.abs(P[..., 0]) < (P[..., 1] - 81) * 1.35 - 1.6 * hash2(P)
    t.box('stubble_top', (-8.5, 90.5, -9.5), (8.5, 91.5, 19.5), S(grey, c=HEAD_C, r=(16, 10, 16), base=.55, gain=.05, mods=mods, cut=top_keep), faces=('up', 'east', 'west', 'north', 'south'), solid=False)
    t.box('stubble_front', (-13, 81, 18.5), (13, 91, 19.5), S(grey, c=HEAD_C, r=(16, 10, 16), base=.55, gain=.05, mods=mods, cut=fan), faces=('south',), solid=False)
    t.box('stubble_back', (-8, 84, -9.5), (8, 91, -8.5), S(grey, c=HEAD_C, r=(16, 10, 16), base=.5, gain=.05, mods=mods, cut=lambda P, N: np.abs(P[..., 0]) < 8 - 2 * hash2(P)), faces=('north',), solid=False)
    return t


def hawk():
    t = Trait('head_hawk')
    slate = ['#202430', '#323642', '#45474f', '#5a5d68', '#7f8390']
    sh = S(slate, base=.44, gain=.26, per_cube=True, mods=[lambda P, N, t: t + .02 * (P[..., 1] - 96)])
    t.box('strip', (-2.5, 90.5, -9.5), (2.5, 92.5, 19.5), sh)
    t.box('widow_peak', (-3, 82, 19), (3, 91, 20), S(slate, base=.40, gain=.2, cut=lambda P, N: np.abs(P[..., 0]) < (P[..., 1] - 81.5) * .42), faces=('south',), solid=False)
    for i, (z, rz, hs) in enumerate(((17, 26, (4, 4, 3)), (10.5, 13, (5, 5, 4)), (4, 0, (7, 6, 5)), (-2.5, -13, (5, 5, 4)), (-8, -26, (4, 4, 3)))):
        spike(t, f'spike_{i + 1}', (0, 92, z), 7, 6, hs, sh, rx=-3 * (2 - i), rz=rz)
    return t


def spiky():
    t = Trait('head_spiky')
    orange = ['#982e04', '#db5e00', '#ff6d00', '#ff8a33', '#ffac6d']
    tone = lambda P, N, t: t + .035 * (P[..., 1] - 100)     # dark between the spikes, pale at the tips
    sh = S(orange, base=.46, gain=.24, per_cube=True, mods=[tone])
    # a jagged fringe on the forehead, a pad on the crown between the horns
    zig = lambda P, N: P[..., 1] > 88.5 - 6.5 * (np.abs(((P[..., 0] + 9) / 6) % 1 - .5) * 2) * (1 - np.abs(P[..., 0]) / 13)
    t.box('fringe', (-9, 82, 19), (9, 92, 20), S(orange, base=.46, gain=.24, cut=zig), faces=('south',), solid=False)
    t.box('pad', (-15.5, 89, -9.5), (15.5, 93, 19.5), sh)
    for i, (x, z, rz, rx, hs) in enumerate(((-7, 12, 16, 6, (5, 5, 4)), (-3.5, 6, 8, 0, (7, 6, 5)), (0, 13, 2, 8, (8, 7, 6)), (3.5, 5, -7, 0, (7, 6, 4)), (7, 12, -15, 6, (5, 5, 3)),
                                          (-4, -5, 10, -10, (6, 5, 4)), (4, -5, -10, -10, (6, 5, 4)))):
        spike(t, f'spike_{i + 1}', (x, 92.5, z), 6, 6, hs, sh, rx=rx, rz=rz)
    return t


def hat_dome(t, sh, y0=83):
    shell(t, 'crown', y0, 92, sh)
    step(t, 'crown_2', 92, 95, 12, 9, 17.5, -7.5, sh)
    step(t, 'crown_3', 95, 98, 8, 8, 14.5, -4.5, sh)


def cap():
    t = Trait('head_cap')
    blue = ['#2d5f85', '#316a94', '#4285b7', '#80c9ff', '#b4e0ff']
    # the two white chevrons on the front panel
    chev = lambda P, N: (N[..., 2] > .5) & (np.abs(P[..., 1] - 89.2 + np.abs(np.abs(P[..., 0]) - 6) * .85) < .85) & (np.abs(np.abs(P[..., 0]) - 6) < 3.6)
    sh = S(blue, c=(0, 88, 5), r=(17, 13, 17), base=.58, gain=.26, face=.12, decals=[(chev, ['#dbe9f3', '#f6fbfe'], .9)],
           mods=[lambda P, N, t: t - .14 * ((N[..., 2] > .5) & (np.abs(P[..., 0]) < .5))])
    hat_dome(t, sh)
    edge = lambda P, N, t: t - .34 * (P[..., 2] > 29.5)      # the brim's dark edge
    t.box('brim', (-13, 83, 19), (13, 85, 31), S(['#16324a', '#1f4764', '#2c5f85', '#316a94', '#4285b7'], base=.62, gain=.18, per_cube=True, mods=[edge]), rot=(8, 0, 0), origin=(0, 84, 19))
    return t


def mayc():
    t = Trait('head_mayc_brim')
    red = ['#8a1b0e', '#bd2917', '#ff331b', '#ff5a3f', '#ff8f6b']
    patch = lambda P, N: (N[..., 2] > .5) & (((P[..., 0]) / 7.5) ** 2 + ((P[..., 1] - 88) / 3.4) ** 2 < 1)
    sh = S(red, c=(0, 88, 5), r=(17, 13, 17), base=.46, gain=.22, face=.08, decals=[(patch, ['#a24444', '#b74d4d', '#c06c6c', '#d48c8c'], lambda P, N: .62 - .05 * (P[..., 1] < 87))])
    hat_dome(t, sh)
    t.box('brim', (-13, 83, 19), (13, 85, 31), S(['#5e1109', '#8a1b0e', '#bd2917', '#d62d19', '#ff331b'], base=.5, gain=.22, per_cube=True), rot=(8, 0, 0), origin=(0, 84, 19))
    fire = ['#d44a0c', '#ff7f28', '#ffb028', '#f6c36c', '#fff0c0']

    def flame(cx, y0, y1, w):
        h = y1 - y0

        def keep(P, N):
            u = np.clip((P[..., 1] - y0) / h, 0, 1)
            wob = 1.2 * np.sin(P[..., 1] * .9 + cx)
            axis = np.where(np.abs(N[..., 2]) > .5, P[..., 0] - cx, P[..., 2] - 5)
            return np.abs(axis + wob * u) < w * (1 - u) ** .8 + .25

        def core(P, N, t):
            u = np.clip((P[..., 1] - y0) / h, 0, 1)
            axis = np.where(np.abs(N[..., 2]) > .5, P[..., 0] - cx, P[..., 2] - 5)
            return .95 - .85 * u - .5 * np.abs(axis) / (w + 1)
        return S(fire, base=0, gain=0, face=0, mods=[core], cut=keep)

    # rising from the top centre, as two crossed cards
    t.box('flame_top_a', (-7, 97, 4.5), (7, 118, 5.5), flame(0, 97, 118, 6.5), faces=('north', 'south'), solid=False, glow=True)
    t.box('flame_top_b', (-.5, 97, -2), (.5, 118, 12), flame(0, 97, 118, 6.5), faces=('east', 'west'), solid=False, glow=True)
    # flickering out from both sides at the brim
    for sx, s in ((1, 'l'), (-1, 'r')):
        cx = sx * 15.5
        x0, x1 = sorted((cx - 4, cx + 4))
        t.box(f'flame_side_{s}', (x0, 82, 19), (x1, 94, 20), flame(cx, 82, 94, 3.5), faces=('north', 'south'), solid=False, glow=True)
    for i, (x, y, z) in enumerate(((-9, 107, 5), (8, 110, 5), (-20, 92, 19), (20, 90, 19))):
        t.box(f'ember_{i + 1}', (x - .5, y - .5, z - .5), (x + .5, y + .5, z + .5), S(fire, base=.62, gain=.1, per_cube=True), solid=False, glow=True)
    return t


def sea_captain():
    t = Trait('head_sea_captain')
    white = ['#9d9999', '#bdb7b7', '#dbd1d1', '#efebeb', '#fbfbfb']
    gold = ['#a67708', '#d2990a', '#fbb812', '#ffd261', '#ffe59c']

    def anchor(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        front = N[..., 2] > .5
        stem = (x < 1) & (y > 95) & (y < 100)
        bar = (x < 3) & (y > 98) & (y < 99)
        base = (x < 4.2) & (y > 95 + (x > 2.2) * 1) & (y < 96 + (x > 2.2) * 1)
        return front & (stem | bar | base)

    sh = S(white, c=(0, 92, 5), r=(17, 14, 17), base=.56, gain=.30, face=.12, decals=[(anchor, gold, .55)])
    shell(t, 'band', 83, 92, S(white, c=(0, 90, 5), r=(17, 14, 17), base=.46, gain=.22,
                               decals=[(lambda P, N: (N[..., 2] > .5) & (np.abs(P[..., 1] - 87) < .9) | (N[..., 2] < -.5) & (np.abs(P[..., 1] - 87) < .9), gold, lambda P, N: .55)]))
    step(t, 'neck', 92, 95, 10, 8.5, 16.5, -6.5, sh)
    step(t, 'top', 95, 100, 12.5, 12.5, 18.5, -8.5, sh)
    step(t, 'cap', 100, 102, 10.5, 10.5, 15.5, -5.5, sh)
    visor = ['#2c2c2c', '#3d3d3d', '#4f4f4f', '#6b6b6b', '#a2a2a2']
    shine = lambda P, N, t: t + .32 * ((N[..., 1] > .5) & (np.abs(P[..., 2] - 22 + P[..., 0] * .4) < 1.3))
    t.box('visor', (-12, 84, 19), (12, 86, 27), S(visor, base=.5, gain=.2, per_cube=True, mods=[shine]), rot=(18, 0, 0), origin=(0, 85, 19))
    t.box('cord', (-12.5, 86, 19.5), (12.5, 87, 20.5), S(gold, base=.55, gain=.15, ))
    return t


def soldier():
    t = Trait('head_soldier')
    olive = ['#2f4a17', '#446723', '#6d9448', '#86ad62', '#a4c980']
    sh = S(olive, c=(0, 90, 5), r=(17, 15, 17), base=.46, gain=.34, face=.12)
    shell(t, 'dome', 83, 92, sh)
    step(t, 'dome_2', 92, 96, 13, 9, 18.5, -8.5, sh)
    step(t, 'dome_3', 96, 100, 10, 8.5, 15.5, -5.5, sh)
    t.box('dome_top', (-6, 100, 0), (6, 102, 10), sh)
    t.box('rim_front', (-16.5, 82, 19), (16.5, 84, 23), S(olive, base=.5, gain=.18, per_cube=True))
    t.box('rim_back', (-16.5, 82, -11.5), (16.5, 84, -8.5), S(olive, base=.42, gain=.18, per_cube=True))
    t.mirror('rim_side', (15.5, 82, -8.5), (16.5, 84, 19.5), S(olive, base=.46, gain=.18, per_cube=True))
    strap = S(['#5d2c13', '#7d3b1b', '#8f563b', '#a56a4d', '#bd8467'], base=.5, gain=.2, per_cube=True)
    # from the helmet, angled forward down the side of the face, then under the chin in front of the chest
    t.mirror('strap', (15, 61, 7), (16, 83, 9), strap, rot=(-24, 0, 0), origin=(15.5, 83, 8))
    t.box('strap_chin', (-16, 61.5, 14.5), (16, 63.5, 19.5), strap)
    return t


def slick():
    t = Trait('head_slick')
    brown = ['#3f1a09', '#7a401f', '#864a27', '#9c5b33', '#af6c41']
    hairline = lambda P, N: (N[..., 2] < .5) | (P[..., 1] > 83 + 2.2 * np.abs(np.sin(P[..., 0] * .35)) + 1.5 * (np.abs(P[..., 0]) < 2))
    sh = S(brown, c=(0, 90, 5), r=(17, 13, 17), base=.52, gain=.30, mods=[comb(.16)], cut=hairline)
    shell(t, 'hair', 82, 92, sh)
    step(t, 'hair_2', 92, 95, 12, 9, 17.5, -7.5, sh)
    step(t, 'hair_3', 95, 96, 8, 8, 13.5, -4.5, sh)
    t.box('hair_nape', (-15.5, 72, -9.5), (15.5, 82, -.5), sh)
    # one band from the sideburn round to the nape; the ear comes out through it
    t.mirror('curtain', (15, 75, -.5), (16, 82, 16.5), S(brown, base=.42, gain=.18, per_cube=True, mods=[comb(.14)]))
    return t


def bob():
    t = Trait('head_bob')
    pink = ['#590f2f', '#ce3677', '#ed5a99', '#f28ab6', '#f6b6d1']
    dash = lambda P, N: (N[..., 2] > .5) & (np.abs(P[..., 1] - 89.5) < .55) & ((P[..., 0] % 4) < 2.5) & (np.abs(P[..., 0]) < 14)
    sh = S(pink, c=(0, 84, 5), r=(19, 18, 19), base=.52, gain=.30, face=.10, decals=[(dash, pink, .98)], mods=[comb(.07, .5)])
    shell(t, 'hair', 82, 92, sh)
    step(t, 'hair_2', 92, 96, 13, 9, 17.5, -7.5, sh)
    step(t, 'hair_3', 96, 99, 9, 8.5, 13.5, -3.5, sh)
    t.mirror('curtain', (15, 68, -.5), (18, 92, 19.5), sh)
    t.box('back', (-18, 68, -11.5), (18, 92, -.5), sh)
    return t


def blonde():
    t = Trait('head_blonde')
    gold = ['#c19205', '#dfaf0b', '#eabc0e', '#f7d65b', '#fbe79a']
    # parted in the middle, framing the face in a rounded arch
    arch = lambda P, N: (N[..., 2] < .5) | (P[..., 1] > 83 + 5.5 * np.clip(1 - np.abs(P[..., 0]) / 13, 0, 1) ** .6)
    part = lambda P, N, t: t - .22 * (np.abs(P[..., 0]) < .6)
    sh = S(gold, c=(0, 84, 5), r=(19, 20, 19), base=.54, gain=.30, face=.10, mods=[part, comb(.05, .5)], cut=arch)
    hair = S(gold, c=(0, 84, 5), r=(19, 20, 19), base=.54, gain=.30, face=.10, mods=[comb(.05, .5)])
    shell(t, 'hood', 82, 92, sh)
    step(t, 'hood_2', 92, 96, 13, 9, 17.5, -7.5, S(gold, c=(0, 84, 5), r=(19, 20, 19), base=.54, gain=.30, face=.10, mods=[part]))
    step(t, 'hood_3', 96, 98, 8.5, 8.5, 13.5, -3.5, S(gold, c=(0, 84, 5), r=(19, 20, 19), base=.54, gain=.30, face=.10, mods=[part]))
    t.mirror('curtain', (15, 62, -.5), (19, 92, 19.5), hair)
    t.box('back', (-17, 62, -11.5), (17, 92, -.5), hair)
    # the long part follows the body: in front of the arms, ending in curls that turn inward
    low = S(gold, c=(0, 50, 5), r=(22, 30, 20), base=.52, gain=.30, face=.10, mods=[comb(.05, .5)])
    t.mirror('strand', (15, 38, 8.5), (20, 62, 12.5), low, bone='Chest')
    t.mirror('curl', (11, 33, 11.5), (19, 38, 15.5), low, bone='Chest')
    t.box('back_low', (-15, 40, -15.5), (15, 62, -11.5), low, bone='Chest')
    return t


def afro():
    t = Trait('head_afro')
    brown = ['#241413', '#3a211e', '#4a2e2a', '#5f3b34', '#84544b']
    sh = S(brown, c=(0, 90, -8), r=(30, 24, 26), base=.36, gain=.30, face=.06, mods=[curls(.07)])
    # the big round mass behind the horns: they stick out through its front, as in the art
    # the outer ears lean back to z -2.2 past x 23, so the mass beside them starts behind that
    t.box('mass_wide', (-27, 78, -22.5), (27, 98, -2.5), sh)
    t.box('mass_tall', (-23, 69, -19.5), (23, 104, -1.5), sh)
    t.box('mass_deep', (-17, 66, -27.5), (17, 108, -.5), sh)
    # over the top, above the horn tips, and down to the forehead between them
    t.box('top_wide', (-24, 102, -.5), (24, 107, 12.5), sh)
    t.box('top', (-17, 107, -13.5), (17, 111, 8.5), sh)
    t.box('crown', (-8.5, 91, -.5), (8.5, 102, 14.5), sh)
    t.box('sides', (-15.5, 83, -.5), (15.5, 102, 10.5), sh)
    # sideburns sit behind the ear root (ear z >= 1.4 there), not over it
    t.mirror('cheek', (15, 70, -9.5), (17, 83, .5), sh)
    t.box('forehead', (-15.5, 83, 10.5), (15.5, 100, 20.5), sh)
    t.box('forehead_top', (-11.5, 100, 12.5), (11.5, 104, 19.5), sh)
    return t


def clown():
    t = Trait('head_clown')
    red = ['#871023', '#b81a26', '#f23630', '#f65a50', '#fb8d80']
    blue = ['#143f8a', '#1c60b4', '#2390e8', '#4eaaf0', '#90cdf7']
    yellow = ['#c59e05', '#e2be14', '#fde230', '#fdeb6c', '#fef4a8']

    def band(P):
        return P[..., 0] * .8 - (P[..., 1] - 92) * .6      # diagonal, upper left to lower right

    def tuft(P, N, cube):
        s = band(P)
        cc = (np.array(cube['fr']) + np.array(cube['to'])) / 2
        rr = (np.array(cube['to']) - np.array(cube['fr'])) / 2 + .01
        n = (P - cc) / rr
        n = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6)
        t = .5 + .30 * (n @ L_KEY) + .08 * (N @ L_KEY)
        rgb = ramp(t, red)
        rgb = np.where(((s > -10.5) & (s < -3.5))[..., None], ramp(t, blue), rgb)
        rgb = np.where((s > 5.5)[..., None], ramp(t, yellow), rgb)
        rgb = np.where(((s > 12) & (s < 15))[..., None], ramp(t, blue), rgb)
        return rgb, np.full(P.shape[:2], 255.)

    shell(t, 'wig', 82, 92, tuft)
    step(t, 'wig_2', 92, 97, 13, 9, 18.5, -8.5, tuft)
    step(t, 'wig_3', 97, 102, 10, 8.5, 15.5, -5.5, tuft)
    t.box('wig_top', (-6, 102, -1), (6, 106, 11), tuft)
    t.mirror('temple', (15, 84, 11), (20, 90, 19), tuft)
    t.mirror('temple_back', (15, 83, -9), (20, 90, -1), tuft)
    t.mirror('ear_tuft', (15, 74, 8), (18, 78, 11), lambda P, N, c: (ramp(.5 + .3 * (N @ L_KEY), red), np.full(P.shape[:2], 255.)))
    return t


def straw_hat():
    t = Trait('head_straw_hat')
    straw = ['#9a7a45', '#bd9559', '#e3b872', '#ecca8f', '#f5dcae']
    rows = lambda P, N, t: t + .05 * np.sign(np.sin(np.where(np.abs(N[..., 1]) > .5, np.hypot(P[..., 0], P[..., 2] - 5), P[..., 1]) * 2.1))
    brim = S(straw, c=(0, 91, 5), r=(30, 8, 30), base=.56, gain=.20, face=.14, mods=[rows, lambda P, N, t: t - .012 * np.hypot(P[..., 0], P[..., 2] - 5)])
    # the brim sits on top of the skull (y 91), so it covers all of it; the horns come out through it
    t.box('brim_wide', (-26, 91, -9.5), (26, 93, 19.5), brim)
    t.box('brim_mid', (-22, 91, -17), (22, 93, 27), brim)
    t.box('brim_long', (-14, 91, -22), (14, 93, 32), brim)
    t.box('droop_front', (-16, 89, 24), (16, 91, 30), brim)
    t.box('droop_back', (-16, 89, -20), (16, 91, -14), brim)
    band = ['#7f1412', '#a51d1a', '#cb2924', '#dd403a', '#ef6f69']
    is_band = lambda P, N: P[..., 1] < 97
    crown = S(straw, c=(0, 100, 5), r=(12, 12, 14), base=.54, gain=.30, face=.03, mods=[rows], decals=[(is_band, band, lambda P, N: .5 + .25 * (N @ L_KEY))])
    t.box('crown_wide', (-8.5, 93, -4), (8.5, 107, 14), crown)
    t.box('crown_long', (-6, 93, -8), (6, 107, 18), crown)
    t.box('crown_top', (-6, 107, -3), (6, 110, 13), crown)
    return t


def tiara():
    t = Trait('head_tiara')
    mint = ['#6b7b79', '#7b9390', '#9fc5bf', '#bfdcd7', '#ddf3f0']
    gem = ['#5d0a12', '#8f1520', '#c7242f', '#e6434b', '#f59a9c']

    def keep(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        peak = 97.5 - x * 1.75
        side = 85.5 + 3.2 * (1 - np.abs(((x - 5) / 5.5) % 1 - .5) * 2) * (x > 5)
        return (y < np.maximum(np.maximum(peak, side), 85.5)) & (y > 82.6 + x * .05)

    sh = S(mint, c=(0, 88, 15), r=(18, 10, 8), base=.52, gain=.34, face=.1, cut=keep, mods=[lambda P, N, t: t + .2 * (np.abs(P[..., 1] - 84.6) < .5)])
    t.box('band', (-16, 82, 18.5), (16, 98, 19.5), sh, faces=('south',), solid=False)
    t.mirror('band_side', (15, 83, 11.5), (16, 85, 18.5), S(mint, base=.5, gain=.2, per_cube=True))
    t.box('gem', (-1.5, 85, 19.5), (1.5, 91, 20.5), S(gem, base=.52, gain=.34, per_cube=True), solid=False)
    return t


ALL = (afro, blonde, bob, cap, clown, crown, fez, geezer, halo, hawk, mayc, sea_captain, slick, soldier, spiky, straw_hat, tiara)
if __name__ == '__main__':
    for f in ALL:
        f().save()
