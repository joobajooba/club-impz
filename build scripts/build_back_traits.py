"""The Back traits (implingz_collection.md section 5), shapes from docs/imp-traits/layers/back_*.png, scaled to the model.
None has no file. All on the Chest bone, behind z -16 so they clear every outfit (hoods reach z -15.5) and Blonde hair.
Each wing and the cape has a bone of its own, so it can move. Viewer's left is -X; art x maps to about 1.6 units per pixel."""
import math
import numpy as np
from cloth_lib import *


class Back(Cloth):
    KIND, FOLDER = 'back', 'C:/Users/lucas/blockbench_models/impz/back/'


def seg(t, name, A, B, w, z0, z1, sh, sub=None, **kw):
    """A cube from A toward B in the XY plane (local +Y points at B), whole-unit sized."""
    dx, dy = B[0] - A[0], B[1] - A[1]
    L = max(1, round(math.hypot(dx, dy)))
    th = round(math.degrees(math.atan2(-dx, dy)), 2)
    t.box(name, (A[0] - w / 2, A[1], z0), (A[0] + w / 2, A[1] + L, z1), sh, rot=(0, 0, th), origin=(A[0], A[1], (z0 + z1) / 2), sub=sub, **kw)


def inpoly(x, y, pts):
    inside = np.zeros(x.shape, bool)
    n = len(pts)
    for i in range(n):
        x1, y1 = pts[i]
        x2, y2 = pts[(i + 1) % n]
        cross = (y1 > y) != (y2 > y)
        with np.errstate(divide='ignore', invalid='ignore'):
            xc = x1 + (y - y1) * (x2 - x1) / (y2 - y1 + 1e-9)
        inside ^= cross & (x < xc)
    return inside


def membrane(t, name, s, pts, z0, pal, sub, mods=(), **kw):
    """A thin sheet cut to a polygon given for the +X side. Painted on both big faces only."""
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    x0, x1, y0, y1 = math.floor(min(xs)), math.ceil(max(xs)), math.floor(min(ys)), math.ceil(max(ys))
    cut = lambda P, N: inpoly(np.abs(P[..., 0]), P[..., 1], pts)
    sh = S(pal, c=(s * (x0 + x1) / 2, (y0 + y1) / 2, z0), r=((x1 - x0) * .7, (y1 - y0) * .7, 30), base=.5, gain=.36, face=.03, cut=cut, mods=list(mods), **kw)
    fr, to = (x0, y0, z0), (x1, y1, z0 + 1)
    if s < 0:
        fr, to = (-x1, y0, z0), (-x0, y1, z0 + 1)
    t.box(name, fr, to, sh, faces=('north', 'south'), sub=sub, solid=False)


def sheen(amp=.2):
    return lambda P, N, t: t + amp * np.sin(P[..., 0] * .33 + P[..., 1] * .24)


def rib_lines(lines, w, amt):
    """Soft darker lines across a membrane, along its finger bones."""
    def f(P, N, t):
        x, y = np.abs(P[..., 0]), P[..., 1]
        out = t
        for (ax, ay), (bx, by) in lines:
            dx, dy = bx - ax, by - ay
            u = np.clip(((x - ax) * dx + (y - ay) * dy) / (dx * dx + dy * dy), 0, 1)
            d = np.hypot(x - ax - u * dx, y - ay - u * dy)
            out = out - amt * np.clip(1 - d / w, 0, 1)
        return out
    return f


SIDES = ((1, 'l'), (-1, 'r'))


def bat(name, mem, spar, shine=None):
    """Imp Wings and Golden Wings share one shape: an arch, its outer tip hanging lowest, three scalloped points."""
    t = Back(name)
    extra = [shine] if shine else []
    for s, n in SIDES:
        sb = f'wing_{n}'
        t.own_bone(sb, (s * 12, 62, -16))
        X = lambda p: (s * p[0], p[1])
        root, peak, tip = (12, 63), (30, 83), (50, 55)
        sp = S(spar, base=.55, gain=.34, mods=extra)
        seg(t, f'root_{n}', X((10, 57)), X((13, 67)), 6, -19, -11, sp, sb)
        seg(t, f'spar_in_{n}', X(root), X(peak), 5, -19, -16, sp, sb)
        seg(t, f'spar_out_{n}', X(peak), X((39, 72)), 4, -19, -16, sp, sb)
        seg(t, f'spar_tip_{n}', X((39, 72)), X(tip), 3, -19, -16, sp, sb)
        seg(t, f'thumb_{n}', X(peak), X((27, 90)), 2, -19, -17, sp, sb)
        seg(t, f'finger_1_{n}', X(peak), X((38, 52)), 2, -19, -17, sp, sb)
        seg(t, f'finger_2_{n}', X(peak), X((26, 53)), 2, -19, -17, sp, sb)
        pts = [(11, 64), (30, 83), (39, 74), (50, 55), (44, 61), (38, 52), (32, 61), (26, 53), (20, 62), (14, 56), (11, 60)]
        membrane(t, f'membrane_{n}', s, pts, -18, mem, sb, mods=extra + [rib_lines([((30, 83), (38, 52)), ((30, 83), (26, 53))], 2.5, .1)])
    t.save()


def imp_wings():
    bat('back_imp_wings', ['#191a19', '#232423', '#313130', '#474847', '#575957'], ['#313130', '#474847', '#575957', '#6e706e', '#848684'])


def golden_wings():
    bat('back_golden_wings', ['#5e4712', '#7d611d', '#9d7d33', '#c99d32', '#e0b95c'], ['#7d611d', '#c99d32', '#e0b95c', '#f6f398', '#fbf9c4'], shine=sheen(.2))


def feather(pal):
    """Rounded tip and a soft quill line, worked out in the cube's own coordinates (the tip is local +Y)."""
    def cut(P, N):
        p, fr, to = LOC['p'], LOC['fr'], LOC['to']
        hw = (to[0] - fr[0]) / 2
        lx = (p[..., 0] - (fr[0] + to[0]) / 2) / hw
        ly = (to[1] - p[..., 1]) / (hw * 1.5)
        return (ly >= 1) | (lx ** 2 + (1 - ly) ** 2 <= 1.02)

    def quill(P, N, t):
        p, fr, to = LOC['p'], LOC['fr'], LOC['to']
        return t - .12 * (np.abs(p[..., 0] - (fr[0] + to[0]) / 2) < .6) + .08 * ((to[1] - p[..., 1]) / (to[1] - fr[1]) - .5)
    return S(pal, base=.6, gain=.3, cut=cut, mods=[quill])


def angel_wings():
    t = Back('back_angel_wings')
    pal = ['#8c92a6', '#b2b6c8', '#bdc3d5', '#dee7ef', '#e9f1f4']
    fe = feather(pal)
    rim = S(['#b2b6c8', '#cccfd4', '#dee7ef', '#e9f1f4', '#f4f8fa'], base=.66, gain=.3)
    long_ = [((40, 76), (47, 33), 7), ((37, 78), (41, 37), 7), ((33, 79), (35, 41), 7), ((28, 79), (29, 45), 7), ((23, 76), (23, 48), 7), ((18, 72), (17, 50), 6)]
    mid = [((40, 76), (44, 53), 7), ((36, 79), (38, 55), 7), ((31, 80), (31, 57), 7), ((26, 78), (25, 59), 7), ((20, 74), (19, 59), 6)]
    short_ = [((36, 79), (38, 65), 6), ((30, 81), (30, 67), 6), ((24, 78), (23, 67), 6), ((18, 73), (18, 64), 5)]
    for s, n in SIDES:
        sb = f'wing_{n}'
        t.own_bone(sb, (s * 12, 62, -16))
        X = lambda p: (s * p[0], p[1])
        seg(t, f'root_{n}', X((10, 57)), X((13, 67)), 6, -20, -11, rim, sb)
        seg(t, f'arm_1_{n}', X((12, 64)), X((25, 80)), 6, -20, -16, rim, sb)
        seg(t, f'arm_2_{n}', X((25, 80)), X((39, 80)), 6, -20, -16, rim, sb)
        seg(t, f'arm_3_{n}', X((39, 80)), X((43, 70)), 5, -20, -16, rim, sb)
        # three layers, the long primaries furthest back; every feather its own depth so none z-fight
        z = -22.5
        for row, group in (('long', long_), ('mid', mid), ('short', short_)):
            for i, (a, b_, w) in enumerate(group):
                seg(t, f'{row}_{i + 1}_{n}', X(a), X(b_), w, z, z + 1, fe, sb, solid=False)
                z += .25
    t.save()


def bone_wings():
    t = Back('back_bone_wings')
    bone = S(['#9a9ca2', '#c9ccd2', '#e3e7ec', '#f0f5fa', '#f5f7f8'], base=.62, gain=.3)
    mem = ['#6e6d72', '#8b8b8e', '#adadae', '#b1b2b3', '#c3c4c6']
    wrist = (34, 100)
    fingers = [((50, 70), (52, 44)), ((43, 66), (44, 40)), ((34, 68), (34, 46)), ((24, 72), (20, 56))]
    for s, n in SIDES:
        sb = f'wing_{n}'
        t.own_bone(sb, (s * 12, 62, -16))
        X = lambda p: (s * p[0], p[1])
        seg(t, f'root_{n}', X((10, 57)), X((13, 67)), 6, -20, -11, bone, sb)
        seg(t, f'arm_1_{n}', X((12, 63)), X((24, 88)), 5, -20, -16, bone, sb)
        seg(t, f'arm_2_{n}', X((24, 88)), X(wrist), 4, -20, -16, bone, sb)
        # the claw hook, curling in above the horns
        seg(t, f'claw_1_{n}', X(wrist), X((31, 110)), 3, -20, -17, bone, sb)
        seg(t, f'claw_2_{n}', X((31, 110)), X((24, 115)), 2, -20, -17, bone, sb)
        seg(t, f'claw_3_{n}', X((24, 115)), X((20, 112)), 1, -19, -18, bone, sb)
        for i, (k, tip) in enumerate(fingers):
            seg(t, f'finger_{i + 1}_a_{n}', X(wrist), X(k), 3, -20, -17, bone, sb)
            seg(t, f'finger_{i + 1}_b_{n}', X(k), X(tip), 2, -20, -17, bone, sb)
        pts = [(13, 64), (24, 88), (34, 100), (50, 70), (52, 45), (47, 60), (44, 41), (39, 62), (34, 47), (28, 66), (20, 56), (16, 62)]
        lines = [(wrist, k) for k, _ in fingers] + list(fingers)
        membrane(t, f'membrane_{n}', s, pts, -19, mem, sb, mods=[rib_lines(lines, 3, .12)])
    t.save()


def mechanical_wings():
    t = Back('back_mechanical_wings')
    pl = ['#4d4e55', '#868890', '#9196a2', '#a8adb7', '#b4bbc3']
    fr = S(['#5f3a2a', '#7d4c36', '#995d43', '#8e766e', '#a98f86'], base=.55, gain=.34)

    def rivets(P, N):
        p, a, b = LOC['p'], LOC['fr'], LOC['to']
        cx = (a[0] + b[0]) / 2
        return (np.abs(np.abs(p[..., 0] - cx) - (b[0] - a[0]) / 2 + 1.5) < .6) & (((p[..., 1] - a[1]) % 6) < 1)
    plate = S(pl, base=.56, gain=.34, decals=[(trim(1), ['#4d4e55', '#4d4e55'], .5), (rivets, ['#4d4e55', '#2f3036'], .5)])
    panels = [((27, 78), (46, 37), 8), ((25, 76), (38, 40), 8), ((23, 74), (30, 44), 8), ((21, 72), (24, 48), 7), ((19, 68), (19, 52), 6)]
    for s, n in SIDES:
        sb = f'wing_{n}'
        t.own_bone(sb, (s * 12, 62, -16))
        X = lambda p: (s * p[0], p[1])
        seg(t, f'root_{n}', X((10, 56)), X((13, 66)), 6, -24, -11, fr, sb)
        for i, (a, b_, w) in enumerate(panels):
            z = -18.5 - i
            seg(t, f'panel_{i + 1}_{n}', X(a), X(b_), w, z, z + 1, plate, sb, solid=False)
        # the copper frame, in front of the panels and behind them
        for lay, (z0, z1) in (('f', (-17.5, -15.5 - .5)), ('b', (-25, -23))):
            seg(t, f'strut_in_{lay}_{n}', X((12, 62)), X((28, 82)), 3, z0, z1 if lay == 'b' else -16.5, fr, sb)
            seg(t, f'strut_out_{lay}_{n}', X((28, 82)), X((49, 36)), 3, z0, z1 if lay == 'b' else -16.5, fr, sb)
        seg(t, f'brace_{n}', X((36, 64)), X((17, 62)), 2, -17.5, -16.5, fr, sb)
        joint = S(['#2f3036', '#4d4e55', '#6b6c74', '#868890', '#9196a2'], base=.5, gain=.3)
        t.box(f'joint_{n}', (s * 28 - 3, 79, -26), (s * 28 + 3, 85, -16), joint, sub=sb)
        t.box(f'light_{n}', (s * 28 - 1, 81, -16), (s * 28 + 1, 83, -15), S(['#6e1211', '#a71f1e', '#d33630', '#db4540', '#f07a75'], base=.7, gain=.2), sub=sb)
    t.save()


def cape():
    t = Back('back_cape')
    t.own_bone('cape', (0, 62, -17))
    red = ['#3d0413', '#640720', '#8a1128', '#a81830', '#ae1e2f']
    lining = ['#3d0413', '#4f0519', '#640720', '#6d0721', '#7d0c2a']
    folds = lambda P, N, t_: t_ + .16 * np.sin(P[..., 0] * .55 + np.sin(P[..., 1] * .08))
    lin = (lambda P, N: N[..., 2] > .5, lining, lambda P, N: .5 + .22 * np.sin(P[..., 0] * .55))
    sh = S(red, c=(0, 32, -22), r=(44, 48, 40), base=.6, gain=.3, mods=[folds, fall(3, 40, .14)], decals=[lin])
    rot = (6, 0, 0)
    org = (0, 62, -17)
    t.box('collar', (-17, 56, -19), (17, 70, -16), S(red, base=.62, gain=.3, decals=[lin]), sub='cape')
    t.mirror('collar_side', (15, 57, -16), (18, 66, -8), S(red, base=.6, gain=.3), sub='cape')
    t.box('fall_1', (-27, 40, -19), (27, 62, -16), sh, rot=rot, origin=org, sub='cape')
    t.box('fall_2', (-36, 20, -21), (36, 42, -18), sh, rot=rot, origin=org, sub='cape')
    hem = lambda P, N: P[..., 1] > 4 + 1.2 * np.abs(np.sin(P[..., 0] * .4)) * 2
    t.box('fall_3', (-41, 3, -23), (41, 22, -20), S(red, c=(0, 32, -22), r=(44, 48, 40), base=.6, gain=.3, mods=[folds, fall(3, 40, .14)], decals=[lin], cut=hem), rot=rot, origin=org, sub='cape', solid=False)
    t.save()


class Prop:
    """A straight prop: all its cubes share one rotation about A. u runs across it, v along it, +v toward its head."""

    def __init__(self, t, A, th, sub=None):
        self.t, self.A, self.th, self.sub = t, A, th, sub

    def b(self, name, u0, v0, u1, v1, z0, z1, sh, **kw):
        ax, ay = self.A
        self.t.box(name, (ax + u0, ay + v0, z0), (ax + u1, ay + v1, z1), sh, rot=(0, 0, self.th), origin=(ax, ay, -18), sub=self.sub, **kw)


METAL = ['#2f2f30', '#4e4e4f', '#666768', '#7f8884', '#97a99a']


def sword():
    t = Back('back_sword')
    p = Prop(t, (-20, 63), 50)
    metal = S(METAL, base=.55, gain=.34)
    grip = S(['#141a0a', '#242e12', '#36431c', '#475528', '#5a6a36'], base=.5, gain=.3, mods=[lambda P, N, t_: t_ - .14 * ((LOC['p'][..., 1] % 3) < 1)])
    fuller = lambda P, N: np.abs(LOC['p'][..., 0] - (LOC['fr'][0] + LOC['to'][0]) / 2) < 1
    blade = S(METAL, base=.6, gain=.3, decals=[(fuller, METAL[:3], .55)])
    p.b('pommel', -4, 19, 4, 26, -20, -16, metal)
    p.b('grip', -2.5, 2, 2.5, 19, -19.5, -16.5, grip)
    p.b('guard', -8, -2, 8, 2, -20, -16, metal)
    p.b('blade', -3.5, -52, 3.5, -2, -19, -17, blade)
    p.b('blade_tip_1', -2.5, -58, 2.5, -52, -19, -17, S(METAL, base=.6, gain=.3))
    p.b('blade_tip_2', -1, -62, 1, -58, -19, -17, S(METAL, base=.6, gain=.3))
    t.save()


def samurai():
    t = Back('back_samurai')
    plum = ['#241526', '#3b243d', '#4b2e4f', '#5c3861', '#704a76']
    brass = S(['#3f2e0a', '#5c4410', '#80662b', '#a08440', '#b89c58'], base=.55, gain=.34)
    dark = S(['#14181b', '#252b30', '#343c43', '#454e56', '#566069'], base=.5, gain=.3)
    wrap = lambda P, N, t_: t_ - .18 * (((LOC['p'][..., 1] + np.abs(LOC['p'][..., 0] - (LOC['fr'][0] + LOC['to'][0]) / 2)) % 5) < 1.2)
    sc = S(plum, base=.55, gain=.34)
    hilt = S(plum, base=.5, gain=.3, mods=[wrap])
    for n, th, z in (('a', 42, -20), ('b', -42, -25)):
        p = Prop(t, (0, 44), th)
        zz = (z, z + 4)
        p.b(f'chape_{n}', -3.5, -28, 3.5, -22, *zz, brass)
        p.b(f'scabbard_{n}', -3, -22, 3, 22, z + .5, z + 3.5, sc)
        p.b(f'mouth_{n}', -3.5, 22, 3.5, 25, *zz, brass)
        p.b(f'tsuba_{n}', -5.5, 25, 5.5, 27, *zz, dark)
        p.b(f'hilt_{n}', -2.5, 27, 2.5, 45, z + .5, z + 3.5, hilt)
        p.b(f'cap_{n}', -3, 45, 3, 49, *zz, brass)
    t.save()


def scythe():
    t = Back('back_scythe')
    gun = ['#1b2224', '#2c3639', '#41524f', '#4d5f5c', '#5c6f6c']
    shaft = S(gun, base=.5, gain=.34)
    p = Prop(t, (29, 8), 37)
    p.b('butt', -2.5, -4, 2.5, 2, -20, -16, S(gun, base=.4, gain=.3))
    p.b('shaft', -1.5, 2, 1.5, 96, -19, -16, shaft)
    p.b('socket', -3, 88, 3, 96, -20, -16, S(gun, base=.62, gain=.3))
    edge = lambda P, N: LOC['p'][..., 0] < LOC['fr'][0] + 1.2
    bl = S(['#21292b', '#2c3639', '#434847', '#4d4f4f', '#5a5e5e'], base=.55, gain=.3, decals=[(edge, ['#5f6a6e', '#798488'], .8)])
    arc = [(-26, 83), (-39, 83), (-47, 73), (-50, 60), (-47, 49), (-43, 43)]
    for i, w in enumerate((7, 6, 5, 4, 2)):
        seg(t, f'blade_{i + 1}', arc[i], arc[i + 1], w, -19, -17, bl)
    t.save()


def trident():
    t = Back('back_trident')
    navy = ['#14121f', '#222034', '#353346', '#45435a', '#575570']
    red = S(['#6e1211', '#a71f1e', '#d33630', '#db4540', '#e8706b'], base=.56, gain=.34)
    p = Prop(t, (38, 12), 44)
    p.b('butt_cap', -3, -6, 3, 2, -20, -16, S(navy, base=.42, gain=.34))
    p.b('shaft', -1.5, 2, 1.5, 94, -19, -16, S(navy, base=.5, gain=.34))
    p.b('collar', -11, 94, 11, 98, -20, -16, red)
    # the centre prong: barbed like an arrow
    for i, (w, v0, v1) in enumerate(((5, 98, 110), (11, 110, 113), (7, 113, 117), (4, 117, 122), (2, 122, 127))):
        p.b(f'prong_c_{i + 1}', -w / 2, v0, w / 2, v1, -19, -17, red)
    for s, n in ((1, 'a'), (-1, 'b')):
        for i, (u0, u1, v0, v1) in enumerate(((7, 11, 98, 106), (6, 13, 106, 108), (7.5, 11.5, 108, 113), (8.5, 10.5, 113, 118))):
            lo, hi = (u0, u1) if s > 0 else (-u1, -u0)
            p.b(f'prong_{n}_{i + 1}', lo, v0, hi, v1, -19, -17, red)
    t.save()


ALL = (imp_wings, golden_wings, angel_wings, bone_wings, mechanical_wings, cape, sword, samurai, scythe, trident)
if __name__ == '__main__':
    for f in ALL:
        f()
