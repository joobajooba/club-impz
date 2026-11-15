"""The Clothing traits (implingz_collection.md section 6), shapes from docs/imp-traits/layers/clothing_*.png, fitted to the model.
None is the bare body, so it has no file. Viewer's left is -X (lit); the Imp's own left is +X.
Grid to model: y38->65, y55->27 (crotch), y63->0. Thighs reach x +-18.1, z 16.9 down to y 17, so skirts clear them."""
import math
import sys
import numpy as np
from cloth_lib import *

TORSO = dict(c=(0, 46, 0), r=(19, 28, 15))


def hip(t, sh, hem=27.5, name='hip'):
    """The thighs push out through the pelvis below y 37 (to x +-18.1, z 14), so anything over them needs this."""
    t.box(name, (-18.5, hem, -9.5), (18.5, 37.5, 14.5), sh, bone='Pelvis')


def top(t, sh, hem=28.5, g=.5, **kw):
    t.wrap('body_top', 'chest', sh, g=g, **kw)
    t.wrap('body_low', 'pelvis', sh, g=g, skip_bot=int(round(hem - (27 - g))), **kw)
    hip(t, sh, hem)


def ring(t, name, sh, g, drop, h):
    """A band round the chest, h tall, starting drop below the chin (the head starts at y 63)."""
    skip = int(round(65.12 + g - 63.6)) + drop
    t.wrap(name, 'chest', sh, g=g, skip_top=skip, skip_bot=int(round(22 + 2 * g - skip - h)))


def collar(t, sh, g=1.5, h=4):
    ring(t, 'collar', sh, g, 0, h)


def short(t, sh, g=.5):
    t.both('sleeve', 'arm', sh, g=g)


def long(t, sh, g=.5):
    t.both('sleeve', 'arm', sh, g=g, skip_bot=4)
    t.both('forearm', 'fore', sh, g=g)


def hood(t, sh, ring=None):
    collar(t, ring or sh, g=2, h=5)
    t.box('hood', (-11, 54.5, -15.5), (11, 67.5, -9.5), sh)
    t.mirror('hood_end', (9, 59.5, -11.5), (14, 64.5, 2.5), sh)


FEATHER_MASK = lambda cx, cy: (lambda P, N: (N[..., 2] > .5) & (np.abs(((P[..., 0] - cx) * .77 - (P[..., 1] - cy) * .64)) < 2.6 - np.abs((P[..., 0] - cx) * .64 + (P[..., 1] - cy) * .77) * .34))
QUILL = lambda cx, cy: (lambda P, N: (N[..., 2] > .5) & (np.abs((P[..., 0] - cx) * .77 - (P[..., 1] - cy) * .64) < .55) & (np.abs((P[..., 0] - cx) * .64 + (P[..., 1] - cy) * .77) < 9.5))


def white_tee():
    t = Cloth('clothing_white_tee')
    w = ['#8e969b', '#b4bdc3', '#bdc4c8', '#e8eaec', '#fdfdfd']
    sh = S(w, **TORSO, base=.62, gain=.42, mods=[fall(28, 40, .12)])
    top(t, sh)
    short(t, S(w, base=.62, gain=.36))
    collar(t, S(w, base=.5, gain=.3), g=1, h=2)
    t.save()


def blue_skull_tee():
    t = Cloth('clothing_blue_skull_tee')
    b = ['#0d2f6e', '#13449d', '#3f76d8', '#639bff', '#86b3ff']
    px = ['..sssssss..', '.ssswwwwww.', 'sswwwwwwwww', 'sswwwwwwwww', 'sw..www..ww', 'sw..www..ww', 'sswwwwwwwww', '.wwww.wwww.', '..swwwwww..', '..s.w.w.w..', '..s.w.w.w..']
    dec = bitmap(px, 0, 59, {'w': '#fdfdfd', 's': '#9badb7'})
    # the eye and nose holes show as dark blue
    holes = [''.join('d' if (c == '.' and 0 < i < 8 and 0 < j < 10) else '.' for j, c in enumerate(r)) for i, r in enumerate(px)]
    dec += bitmap(holes, 0, 59, {'d': '#1a2a4e'})
    sh = S(b, **TORSO, base=.56, gain=.42, mods=[fall(28, 40, .12)], decals=dec)
    top(t, sh)
    short(t, S(b, base=.58, gain=.36))
    collar(t, S(b, base=.34, gain=.3), g=1, h=2)
    t.save()


def skelly_tee():
    t = Cloth('clothing_skelly_tee')
    d = ['#12181a', '#1d2528', '#2d3a3f', '#3b4a50', '#4a5a61']

    def ribs(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        f = N[..., 2] > .5
        spine = (x < 1.2) & (y > 30) & (y < 60)
        rib = (x >= 1.2) & (x < 9.5 - np.maximum(0, 48 - y) * .22) & (((y + x * .28) % 4) < 2) & (y > 41) & (y < 60)
        hip = (x >= 1.2) & (x < 4.5) & (y > 31) & (y < 34)
        return f & (spine | rib | hip)
    sh = S(d, **TORSO, base=.56, gain=.4, mods=[fall(28, 40, .1)], decals=[(ribs, ['#dbd6d6', '#fdfdfd'], lambda P, N: np.where(P[..., 0] < 1, .95, .35))])
    top(t, sh, hem=26.5)
    short(t, S(d, base=.56, gain=.34))
    collar(t, S(d, base=.3, gain=.25), g=1, h=2)
    t.save()


LIME = ['#3e7410', '#529416', '#66b71b', '#8bfb25', '#a6ff55']


def robinhood_tee():
    t = Cloth('clothing_robinhood_tee')
    logo = [(FEATHER_MASK(1, 49), ['#242424', '#242424'], .5), (QUILL(1, 49), ['#3f3f3f', '#3f3f3f'], .5)]
    sh = S(LIME, **TORSO, base=.58, gain=.42, mods=[fall(28, 40, .14)], decals=logo)
    top(t, sh)
    short(t, S(LIME, base=.6, gain=.34))
    collar(t, S(LIME, base=.36, gain=.28), g=1, h=2)
    t.save()


def pocket(t, sh, y0=28.5, y1=38.5):
    t.box('pocket', (-9, y0, 14.5), (9, 37.5, 16.5), sh, bone='Pelvis')


def robinhood_hoodie():
    t = Cloth('clothing_robinhood_hoodie')
    logo = [(FEATHER_MASK(2, 52), ['#222034', '#222034'], .5), (QUILL(2, 52), ['#3a3850', '#3a3850'], .5)]
    sh = S(LIME, **TORSO, base=.58, gain=.42, mods=[fall(28, 40, .14)], decals=logo)
    top(t, sh)
    long(t, S(LIME, base=.58, gain=.34))
    hood(t, S(LIME, base=.5, gain=.34))
    pocket(t, S(LIME, base=.44, gain=.3))
    t.save()


def demon_hoodie():
    t = Cloth('clothing_demon_hoodie')
    g = ['#2d2830', '#403a43', '#575159', '#827986', '#9a91a0']
    face = ['r.......r',
            'rr.....rr',
            'rrrRRRrrr',
            'rRRRRRRRr',
            'RRdRRRdRR',
            'RRRdRdRRR',
            'RRRRRRRRR',
            '.RdRdRdR.',
            '..RRRRR..',
            '...DDD...']
    dec = bitmap(face, 0, 58, {'r': '#ed3838', 'R': '#b71a1a', 'D': '#940e0e', 'd': '#3a0a0a'})
    sh = S(g, **TORSO, base=.56, gain=.42, mods=[fall(28, 40, .12)], decals=dec)
    top(t, sh)
    long(t, S(g, base=.56, gain=.34))
    hood(t, S(g, base=.48, gain=.34))
    pocket(t, S(g, base=.4, gain=.28))
    t.save()


def vest():
    t = Cloth('clothing_vest')
    w = ['#7f898c', '#a5afb2', '#d1dbe1', '#eef2f4', '#fcfdfd']

    def neck(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        scoop = (y > 54) & (x < 3.5 + (y - 54) * .55) & (np.abs(N[..., 2]) > .5)
        return ~(scoop | ((y > 62.4) & (N[..., 1] > .5)))
    # lit white on the viewer's left half, pale grey on the right (the art's hard split)
    half = lambda P, N, t: t - .3 * (P[..., 0] > 2.5)
    sh = S(w, **TORSO, base=.72, gain=.26, mods=[half, fall(30, 40, .1)], cut=neck)
    t.wrap('body_top', 'chest', sh, solid=False)
    t.wrap('body_low', 'pelvis', sh, skip_bot=4)
    hip(t, sh, 30.5)
    t.save()


def bikini():
    t = Cloth('clothing_bikini')
    p = ['#7a0f57', '#bc1b89', '#e23aa9', '#ff5bcb', '#ff8fdd']

    def top_keep(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        fr, bk = N[..., 2] > .5, N[..., 2] < -.5
        cup = fr & (y > 49.5) & (y < 60) & (np.abs(x - 6) < (60 - y) * .62)
        band = (y > 49.5) & (y < 52.5) & (np.abs(N[..., 1]) < .5)
        strap = (fr | bk) & (np.abs(x - 6) < 1.1) & (y > 52)
        return cup | band | strap

    def low_keep(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        fr, bk = N[..., 2] > .5, N[..., 2] < -.5
        vee = fr & (y < 36.5) & (y > 27 + x * .5)
        side = (np.abs(N[..., 0]) > .5) & (y > 33) & (y < 37)
        rear = bk & (y < 37) & (y > 27 + x * .3)
        under = N[..., 1] < -.5
        return vee | side | rear | under
    flower = lambda cx, top_: bitmap(['.b.b.', 'bbbbb', '.bcb.', 'bbbbb', '.b.b.'], cx, top_, {'b': '#639bff', 'c': '#bbd0f6'})
    dec_top = flower(-6, 56) + flower(6, 56)
    t.wrap('top', 'chest', S(p, **TORSO, base=.62, gain=.4, cut=top_keep, decals=dec_top), g=.5, solid=False)
    t.box('bottom', (-18.5, 26.5, -9.5), (18.5, 36.5, 14.5), S(p, **TORSO, base=.6, gain=.4, cut=low_keep, decals=flower(0, 35)), bone='Pelvis', solid=False)
    t.save()


def polka_dress():
    t = Cloth('clothing_polka_dress')
    r = ['#430807', '#650f0d', '#9e1d18', '#b82a24', '#cf3a33']

    def dots(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0])
        v = P[..., 1]
        row = np.floor(v / 4)
        return (np.abs(N[..., 1]) < .5) & (((u + row * 2) % 4) < 1.1) & ((v % 4) < 1.1)

    def neck(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        scoop = (y > 55) & (x < 4 + (y - 55) * .55) & (np.abs(N[..., 2]) > .5)
        return ~(scoop | ((y > 62.4) & (N[..., 1] > .5)))
    sh = S(r, **TORSO, base=.56, gain=.42, decals=[(dots, ['#fdfdfd', '#fdfdfd'], .5)], cut=neck, mods=[fall(14, 44, .16)])
    t.wrap('bodice', 'chest', sh, solid=False)
    sk = S(r, c=(0, 30, 3), r=(26, 36, 22), base=.56, gain=.42, decals=[(dots, ['#fdfdfd', '#fdfdfd'], .5)], mods=[fall(14, 44, .16)])
    t.wrap('waist', 'pelvis', sk)
    hip(t, sk)
    t.box('skirt_1', (-17.5, 20.5, -11.5), (17.5, 27.5, 17.5), sk, bone='Pelvis')
    t.box('skirt_2', (-19, 14.5, -12), (19, 20.5, 19), sk, bone='Pelvis')
    t.save()


def puffer():
    t = Cloth('clothing_puffer')
    n = ['#10132a', '#171b34', '#21284e', '#313866', '#455085']
    pad = lambda P, N, t: t + .16 * (np.abs(((P[..., 1] + .5) % 4) - 2) < 1.2) - .14 * (((P[..., 1] + .5) % 4) < .9)
    rg = S(n, **TORSO, base=.52, gain=.42, mods=[pad])
    under = S(n[:3], base=.3, gain=.1)
    t.wrap('under_top', 'chest', under)
    t.wrap('under_low', 'pelvis', under, skip_bot=2)
    # alternating padded rings: real depth, not paint
    for i, (drop, g) in enumerate(((3, 1.5), (7, 1), (11, 1.5), (15, 1))):
        ring(t, f'chest_{i + 1}', rg, g, drop, 4)
    for i, (y1, g) in enumerate(((48.5, 1), (44.5, 1.5), (40.5, 1))):
        p_top = 48 + g
        t.wrap(f'belly_{i + 1}', 'pelvis', rg, g=g, skip_top=int(round(p_top - y1)), skip_bot=int(round((y1 - 4) - (27 - g))))
    t.box('hip_1', (-18.5, 32.5, -11), (18.5, 36.5, 15), rg, bone='Pelvis')
    t.box('hip_2', (-18.5, 28.5, -10), (18.5, 32.5, 14), rg, bone='Pelvis')
    limb = S(n, base=.56, gain=.34, mods=[lambda P, N, t: t - .16 * ((P[..., 1] % 5) < 1)])
    t.both('sleeve', 'arm', limb, g=1, skip_bot=4)
    t.both('forearm', 'fore', limb, g=1)
    collar(t, S(n, base=.46, gain=.34), g=2, h=5)
    t.box('zip', (-1, 28.5, 12), (1, 62.5, 16), S(['#0d0f22', '#10132a', '#171b34', '#21284e', '#313866'], base=.4, gain=.1), bone='Pelvis')
    t.save()


def gi():
    t = Cloth('clothing_gi')
    o = ['#5e1403', '#7f1b05', '#c1491b', '#f07219', '#f7933c']
    nv = ['#0b1a33', '#12274c', '#1c3a6c', '#25497f', '#2f5a96']

    def vneck(P, N):
        return (N[..., 2] > .5) & (np.abs(P[..., 0]) < (P[..., 1] - 50) * .62)

    def cross(P, N):
        return (N[..., 2] > .5) & (np.abs((P[..., 0] + (P[..., 1] - 50) * .62)) < .7) & (P[..., 1] > 40) & (P[..., 1] < 50)

    def emblem(P, N):
        return (N[..., 2] > .5) & (((P[..., 0] - 7.5) ** 2 + (P[..., 1] - 54) ** 2) < 11)

    def emblem_core(P, N):
        return (N[..., 2] > .5) & (((P[..., 0] - 7.5) ** 2 + (P[..., 1] - 54) ** 2) < 3)
    sh = S(o, **TORSO, base=.56, gain=.42, decals=[(vneck, nv, .55), (cross, o, .1), (emblem, ['#17140f', '#17140f'], .5), (emblem_core, ['#f4e7c9', '#f4e7c9'], .5)])
    top(t, sh, hem=26.5)
    short(t, S(o, base=.58, gain=.36))
    t.both('wrist', 'fore', S(nv, base=.56, gain=.32), g=.5, skip_top=9, skip_bot=2)
    # navy sash, its knot and hanging ends
    t.box('sash', (-19.5, 33.5, -10.5), (19.5, 38.5, 15.5), S(nv, **TORSO, base=.58, gain=.36), bone='Pelvis')
    t.box('knot', (-3, 32.5, 15.5), (3, 39.5, 17.5), S(nv, base=.62, gain=.3), bone='Pelvis')
    t.mirror('sash_end', (.5, 18.5, 15.5), (4.5, 33.5, 16.5), S(nv, base=.48, gain=.3), bone='Pelvis', rot=(-6, 0, 6), origin=(2.5, 33.5, 16))
    # baggy trousers, gathered at the ankle
    baggy = S(o, base=.56, gain=.4, mods=[lambda P, N, t: t - .1 * ((P[..., 0] * .6 + P[..., 1]) % 7 < 1.4)])
    t.both('thigh', 'thigh', baggy, g=1.5)
    t.both('shin', 'shin', baggy, g=1, skip_bot=5)
    t.save()


def trench():
    t = Cloth('clothing_trench')
    k = ['#111014', '#19181d', '#1f2729', '#2c3638', '#3a4749']

    def opening(P, N):
        return ~((N[..., 2] > .5) & (np.abs(P[..., 0]) < 5.5 + np.maximum(0, 45 - P[..., 1]) * .05))
    sh = S(k, **TORSO, base=.56, gain=.42, cut=opening)
    t.wrap('body_top', 'chest', sh, solid=False)
    t.wrap('body_low', 'pelvis', sh, skip_bot=1, solid=False)
    long(t, S(k, base=.56, gain=.34))
    tail = S(k, base=.58, gain=.34, mods=[fall(10, 30, .16)])
    t.mirror('tail_front', (5.5, 8.5, 11), (18.5, 33.5, 14), tail, bone='Pelvis', rot=(-22, 0, 0), origin=(12, 33.5, 12.5))
    t.mirror('tail_side', (16, 8.5, -11), (19, 33.5, 12), tail, bone='Pelvis', rot=(0, 0, 10), origin=(17.5, 33.5, 1))
    t.box('tail_back', (-19, 8.5, -12), (19, 33.5, -9), tail, bone='Pelvis', rot=(5, 0, 0), origin=(0, 33.5, -9.5))
    # wide lapels flaring at the shoulders, a collar behind the neck
    lap = S(k, base=.7, gain=.3)
    t.mirror('lapel', (5, 49, 8.5), (10, 63, 11.5), lap, rot=(-5, 0, 0), origin=(7.5, 56, 10))
    t.mirror('lapel_peak', (9, 57, 6), (18, 62, 10), lap, rot=(0, 0, -18), origin=(11, 59.5, 8))
    t.box('collar_back', (-13, 56, -15), (13, 70, -10), lap)
    # grey belt across the bare torso, with its buckle
    g = ['#3f3f42', '#5b5b5f', '#7a7a7f', '#96969b', '#b0b0b5']
    t.box('belt', (-16.5, 37.5, -10), (16.5, 41.5, 12), S(g, **TORSO, base=.55, gain=.36), bone='Pelvis')
    t.box('buckle', (-3, 36.5, 12), (3, 42.5, 13), S(['#3b3320', '#6d5d30', '#9c8748', '#c2ab62', '#dcc87e'], base=.56, gain=.3), bone='Pelvis')
    t.save()


def waterproof_coat():
    t = Cloth('clothing_waterproof_coat')
    y = ['#626200', '#98980b', '#d6d600', '#ffff00', '#ffff79']

    def quilt(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0])
        v = P[..., 1]
        return (np.abs(N[..., 1]) < .5) & ((((u + v) % 12) < 1) | (((u - v) % 12) < 1))

    def seam(P, N):
        return (N[..., 2] > .5) & (np.abs(P[..., 0]) < 1)
    dec = [(quilt, ['#98980b', '#98980b'], .5), (seam, ['#626200', '#626200'], .5)]
    sh = S(y, **TORSO, base=.62, gain=.34, decals=dec)
    t.wrap('body_top', 'chest', sh)
    t.wrap('body_low', 'pelvis', S(y, c=(0, 30, 3), r=(26, 36, 22), base=.62, gain=.34, decals=dec))
    hip(t, S(y, c=(0, 30, 3), r=(26, 36, 22), base=.62, gain=.34, decals=dec))
    sk = S(y, c=(0, 30, 3), r=(26, 36, 22), base=.6, gain=.36, decals=dec, mods=[fall(16, 30, .16)])
    t.box('hem_1', (-17.5, 22.5, -11.5), (17.5, 27.5, 17.5), sk, bone='Pelvis')
    t.box('hem_2', (-19, 16.5, -12.5), (19, 22.5, 18.5), sk, bone='Pelvis')
    long(t, S(y, base=.62, gain=.32))
    ruff = S(y, base=.66, gain=.32, mods=[lambda P, N, t: t - .14 * ((P[..., 0] % 6) < 1)])
    collar(t, ruff, g=4, h=5)
    t.mirror('ruff_tip', (12, 58, -2), (21, 62, 5), ruff, rot=(0, 0, -22), origin=(14, 60, 1.5))
    t.save()


def elegant():
    t = Cloth('clothing_elegant')
    s_ = ['#2f2c29', '#484541', '#696a6a', '#7b777f', '#94909a']

    def shirt(P, N):
        return (N[..., 2] > .5) & (np.abs(P[..., 0]) < (P[..., 1] - 44) * .42)
    btn = [(lambda P, N, yy=yy: (N[..., 2] > .5) & ((P[..., 0] - 1.5) ** 2 + (P[..., 1] - yy) ** 2 < 1.1), ['#24211f', '#24211f'], .5) for yy in (38, 43)]
    pkt = [(lambda P, N: (N[..., 2] > .5) & (np.abs(np.abs(P[..., 0]) - 9) < 3.5) & (np.abs(P[..., 1] - 35) < .55), ['#2f2c29', '#2f2c29'], .5)]
    closure = [(lambda P, N: (N[..., 2] > .5) & (np.abs(P[..., 0] - .5) < .55) & (P[..., 1] < 44), ['#2f2c29', '#2f2c29'], .5)]
    sh = S(s_, **TORSO, base=.56, gain=.4, decals=[(shirt, ['#dfe1e2', '#f6f6f6'], .7)] + closure + btn + pkt)
    top(t, sh)
    long(t, S(s_, base=.56, gain=.34))
    t.mirror('lapel', (3, 45, 8.5), (8, 62, 11.5), S(s_, base=.72, gain=.28), rot=(-5, 0, -14), origin=(5.5, 62, 10))
    tie = ['#b7b69c', '#dbdabc', '#edecdc', '#fbf9dd', '#fdfce9']
    t.box('cravat_knot', (-2.5, 56.5, 9.5), (2.5, 62.5, 12.5), S(tie, base=.6, gain=.3), rot=(-5, 0, 0), origin=(0, 58, 11))
    t.box('cravat', (-2, 47.5, 9.5), (2, 56.5, 11.5), S(tie, base=.5, gain=.3), rot=(-5, 0, 0), origin=(0, 52, 10.5))
    # matching trousers, down to the feet
    tr = S(['#2f2c29', '#3e3b38', '#575556', '#6b686d', '#7f7b83'], base=.56, gain=.36)
    t.both('thigh', 'thigh', tr)
    t.both('shin', 'shin', tr)
    t.save()


def pyjamas():
    t = Cloth('clothing_pyjamas')
    b = ['#34497c', '#4c69a7', '#7b98d7', '#90abe2', '#a9c0ee']

    def cell(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0])
        v = P[..., 1]
        side = np.abs(N[..., 1]) < .5
        return u, v, side

    def moon(P, N):
        u, v, side = cell(P, N)
        row = np.floor(v / 12)
        uu = (u + row * 6) % 12 - 6
        vv = v % 12 - 6
        return side & ((uu ** 2 + vv ** 2) < 7.5) & (((uu - 1.3) ** 2 + (vv - .6) ** 2) >= 4)

    def star(P, N):
        u, v, side = cell(P, N)
        row = np.floor((v + 6) / 12)
        uu = (u + row * 6) % 12 - 6
        vv = (v + 6) % 12 - 6
        return side & (((np.abs(uu) < 1.5) & (np.abs(vv) < .5)) | ((np.abs(uu) < .5) & (np.abs(vv) < 1.5)))
    dec = [(moon, ['#b4dbff', '#b4dbff'], .5), (star, ['#f7eaa0', '#f7eaa0'], .5)]
    top(t, S(b, **TORSO, base=.56, gain=.4, decals=dec), hem=28.5)
    short(t, S(b, base=.56, gain=.34, decals=dec))
    collar(t, S(b, base=.34, gain=.28), g=1, h=2)
    t.both('shorts', 'thigh', S(b, base=.54, gain=.36, decals=dec), g=.5)
    t.save()


def ragged_vest():
    t = Cloth('clothing_ragged_vest')
    b = ['#2b120e', '#3f1b15', '#663931', '#8f563b', '#a56b4e']

    def wear(P, N, t_):
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        return t_ - .14 * (np.sin(x * .7 + np.sin(y * .5) * 2) * np.sin(y * .6 + z * .4) > .55)

    def vcut(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        v = (N[..., 2] > .5) & (x < (y - 49) * .7)
        return ~(v | ((y > 62.4) & (N[..., 1] > .5)))

    def jag(P, N):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0])
        return P[..., 1] > 14 + np.abs((u % 8) - 4) * 2.1
    t.wrap('body_top', 'chest', S(b, **TORSO, base=.56, gain=.4, mods=[wear], cut=vcut), solid=False)
    sk = dict(c=(0, 30, 3), r=(26, 36, 22))
    t.wrap('body_low', 'pelvis', S(b, **sk, base=.56, gain=.4, mods=[wear]))
    hip(t, S(b, **sk, base=.56, gain=.4, mods=[wear]))
    t.box('tatters', (-18, 13.5, -11), (18, 27.5, 18), S(b, **sk, base=.54, gain=.4, mods=[wear, fall(14, 27, .12)], cut=jag), bone='Pelvis', faces=('north', 'east', 'south', 'west', 'up'), solid=False)
    t.save()


def worker_vest():
    t = Cloth('clothing_worker_vest')
    l = ['#1d1614', '#2d2321', '#4c413a', '#5b483d', '#6f5a4c']

    def mottle(P, N, t_):
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        return t_ + .07 * np.sin(x * .55 + y * .2) * np.sin(y * .45 - z * .3 + x * .15)

    def vcut(P, N):
        x, y = np.abs(P[..., 0]), P[..., 1]
        v = (N[..., 2] > .5) & (x < (y - 54) * .7)
        return ~(v | ((y > 62.4) & (N[..., 1] > .5)))
    t.wrap('body_top', 'chest', S(l, **TORSO, base=.56, gain=.4, mods=[mottle], cut=vcut), solid=False)
    t.wrap('body_low', 'pelvis', S(l, **TORSO, base=.56, gain=.4, mods=[mottle]))
    hip(t, S(l, **TORSO, base=.52, gain=.4, mods=[mottle]))
    # short caps on the shoulders
    t.both('cap', 'arm', S(l, base=.58, gain=.36, mods=[mottle]), g=1, skip_bot=9)
    # the bottom ends in a V between the legs, in front and behind
    vee = lambda P, N: P[..., 1] > 13 + np.abs(P[..., 0]) * .85
    apron = S(l, base=.5, gain=.34, mods=[mottle, fall(14, 30, .12)], cut=vee)
    t.box('apron_front', (-15, 13, 11), (15, 33, 14), apron, bone='Pelvis', rot=(-16, 0, 0), origin=(0, 33, 12.5), solid=False)
    t.box('apron_back', (-15, 13, -12), (15, 33, -9), apron, bone='Pelvis', rot=(14, 0, 0), origin=(0, 33, -10.5), solid=False)
    # grey belt, square bronze buckle
    g = ['#2c2c2e', '#47474a', '#606064', '#7a7a7e', '#94949a']
    t.box('belt', (-19.5, 33.5, -10.5), (19.5, 38.5, 15.5), S(g, **TORSO, base=.52, gain=.34), bone='Pelvis')
    t.box('buckle', (-4, 32, 15.5), (4, 40, 16.5), S(['#4f3412', '#7d5620', '#a97a33', '#c8984a', '#e0b868'], base=.56, gain=.3, decals=[(lambda P, N: (N[..., 2] > .5) & (np.abs(P[..., 0]) < 1.6) & (np.abs(P[..., 1] - 36) < 1.6), ['#2d2321', '#2d2321'], .5)]), bone='Pelvis')
    t.save()


def armour():
    t = Cloth('clothing_armour')
    a = ['#282e3a', '#3d4962', '#7d8baa', '#a7b3ce', '#cbdbfc']
    sh = S(a, **TORSO, base=.6, gain=.42)
    t.wrap('breast', 'chest', sh)
    t.wrap('waist', 'pelvis', sh, skip_bot=11)
    # moulded pecs and a six-pack: real plates
    plate = S(a, base=.66, gain=.34, per_cube=True)
    t.mirror('pec', (.5, 50, 9.5), (11.5, 59, 11.5), plate, rot=(-5, 0, 0), origin=(6, 55, 10.5))
    for i, y in enumerate((48.5, 45, 41.5)):
        t.mirror(f'ab_{i + 1}', (.5, y - 3, 11.5), (6.5, y, 12.5), plate, bone='Pelvis')
    # checkered skirt, small blue and white check
    check = lambda P, N: ((np.floor(np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0]) / 2) + np.floor(P[..., 1] / 2)) % 2) < 1
    ck = S(['#3d5a9e', '#4e6fb5', '#6a8ac7', '#7d9bd6', '#90aee2'], c=(0, 25, 3), r=(26, 30, 22), base=.56, gain=.36, decals=[(check, ['#c6cfe2', '#f2f5fb'], lambda P, N: .5 - .4 * P[..., 0] / 20)])
    hip(t, ck, name='skirt_top')
    t.box('skirt', (-18, 17.5, -11.5), (18, 27.5, 17.5), ck, bone='Pelvis')
    t.save()


def battle_armour():
    t = Cloth('clothing_battle_armour')
    b = ['#1a2c39', '#273f50', '#506f96', '#567c94', '#7296b0']
    g = ['#7f6414', '#c89e1f', '#ddc062', '#ecd588', '#f6e8ae']
    w = ['#8f8f8a', '#b5b5b0', '#d1d1cd', '#eeede8', '#fdfcf8']
    gold = (trim(1.5), g, lambda P, N: .62 - .25 * (P[..., 0] > 0))
    seg = (lambda P, N: (N[..., 2] > .5) & ((P[..., 1] % 5) < 1) & (P[..., 1] < 58), b[:2], .6)
    vgold = (lambda P, N: (N[..., 2] > .5) & (np.abs(np.abs(P[..., 0]) - (P[..., 1] - 46) * .55) < 1) & (P[..., 1] > 46), g, .6)
    sh = S(b, **TORSO, base=.56, gain=.42, decals=[seg, vgold])
    t.wrap('plate_top', 'chest', sh)
    t.wrap('plate_low', 'pelvis', S(b, **TORSO, base=.56, gain=.42, decals=[seg]), skip_bot=2)
    hip(t, S(b, **TORSO, base=.5, gain=.42), 28.5)
    # gold waist band
    t.box('band', (-19.5, 34.5, -10.5), (19.5, 38.5, 15.5), S(g, **TORSO, base=.56, gain=.36), bone='Pelvis')
    # big white flared shoulder pads, gold edged, sticking out sideways like wings
    pad = S(w, base=.62, gain=.34, decals=[gold])
    t.mirror('pad', (9, 58, -9), (33, 62, 9), pad, rot=(0, 0, 18), origin=(9, 60, 0))
    t.mirror('pad_low', (10, 53, -7), (28, 57, 7), pad, rot=(0, 0, 22), origin=(10, 55, 0))
    t.mirror('pad_neck', (6, 60, -9), (13, 64, 10), S(g, base=.56, gain=.32))
    # white pointed hip flaps
    t.mirror('flap', (14, 26, -6), (20, 41, 8), S(w, base=.6, gain=.34, decals=[gold]), bone='Pelvis', rot=(0, 0, 18), origin=(15, 40, 1))
    # blue-grey tasset at the front, to y 17
    point = lambda P, N: P[..., 1] > 17 + np.abs(P[..., 0]) * .9
    t.box('tasset', (-10, 17, 14.5), (10, 35, 16.5), S(b, base=.58, gain=.36, decals=[(lambda P, N: (np.abs(P[..., 1] - (17 + np.abs(P[..., 0]) * .9)) < 1.8) | (np.abs(P[..., 0]) > 8.5), g, .6)], cut=point), bone='Pelvis', rot=(-8, 0, 0), origin=(0, 35, 15.5), solid=False)
    t.save()


ALL = (armour, battle_armour, bikini, blue_skull_tee, demon_hoodie, elegant, gi, polka_dress, puffer, pyjamas, ragged_vest, robinhood_hoodie, robinhood_tee, skelly_tee, trench, vest, waterproof_coat, white_tee, worker_vest)

if __name__ == '__main__':
    for f in ALL:
        f()
