"""The Back traits (implingz_collection.md section 5), shapes from docs/imp-traits/layers/back_*.png, scaled to the model.
None has no file. All on the Chest bone. Wings and cape sit behind z -16 so they clear every outfit (hoods reach z -15.5) and Blonde hair;
the Sword, Scythe and Trident are pressed onto the bare back instead (J00BA, 2026-11-06), so thick outfits cover part of them.
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


def back_z(x, y):
    """The body's back surface: for each world (x, y), the furthest-back z inside the torso (Chest and Pelvis cubes). NaN where there is no torso."""
    zs = np.arange(-16, 4, .05)
    P = np.stack(np.broadcast_arrays(x[..., None], y[..., None], zs), -1)
    P4 = np.concatenate([P, np.ones(P.shape[:-1] + (1,))], -1)
    inside = np.zeros(P.shape[:-1], bool)
    for M, e in BODY_SOLIDS:
        lp = (P4 @ np.linalg.inv(M).T)[..., :3]
        fr, to = np.array(e['from']), np.array(e['to'])
        c, h = (fr + to) / 2, (to - fr) / 2 * np.abs(np.array(e.get('stretch') or [1, 1, 1]))
        inside |= (np.abs(lp - c) <= h).all(-1)
    first = np.where(inside.any(-1), zs[np.argmax(inside, -1)], np.nan)
    return first


def press_to_back(t, sink=.3):
    """Slide a prop straight forward until its front rests on the body's back, sunk in by `sink` so no gap shows.
    The props only rotate about Z, so moving every cube by the same z keeps the prop's shape."""
    gaps = []
    for c in t.cubes:
        M = t._m(c)
        (x0, y0, _), (x1, y1, z1) = c['fr'], c['to']
        u, v = np.meshgrid(np.linspace(x0, x1, max(2, int(x1 - x0) * 2 + 1)), np.linspace(y0, y1, max(2, int(y1 - y0) * 2 + 1)))
        P = np.stack([u, v, np.full_like(u, z1), np.ones_like(u)], -1) @ M.T
        zb = back_z(P[..., 0], P[..., 1])
        gaps.append(np.nanmin(zb - P[..., 2]) if np.isfinite(zb).any() else np.inf)
    dz = round(float(min(gaps)) + sink, 2)
    assert np.isfinite(dz), t.name + ' does not cross the torso'
    for c in t.cubes:
        c['fr'][2] += dz
        c['to'][2] += dz
        if c['origin']:
            c['origin'] = [c['origin'][0], c['origin'][1], c['origin'][2] + dz]
    print(f'{t.name}: moved {dz:+.2f} toward the back')


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


RED = ['#22010a', '#33030f', '#460515', '#5a071c', '#6d0a22', '#800e27', '#94142c', '#a81830', '#b61f33', '#c42c3d', '#d6434f']
LINING = ['#1a0108', '#2a020d', '#3a0412', '#4f0519', '#5e0620', '#6d0721', '#7d0c2a']
GOLD = ['#3f2e0a', '#5c4410', '#80662b', '#a08440', '#c4a95e', '#e2cb83']
CAPE_LIGHT = np.array([.35, .55, -.76]) / np.linalg.norm([.35, .55, -.76])     # from above and behind: the cape is seen from the back


def hem_y(x):
    """The cape's lower edge: a soft wave from the pleats, rising a little toward the sides."""
    return 4 + 1.3 * np.sin(x * .45) + .0016 * x * x


def cape_shader(edge_trim=False, flat=False):
    """Crimson outside, wine lining inside. Each pleat rolls darker toward its long edges, so the strips read as one folded cloth."""
    def f(P, N, cube):
        x, y = P[..., 0], P[..., 1]
        lp, fr, to = LOC['p'], np.array(LOC['fr']), np.array(LOC['to'])
        w = to[0] - fr[0]
        across = np.clip(np.minimum(lp[..., 0] - fr[0], to[0] - lp[..., 0]) / (w / 2), 0, 1)     # 0 at a pleat edge, 1 in its middle
        roll = 0 if flat else -.11 * (1 - across) ** 1.6
        lit = N @ CAPE_LIGHT
        t = .56 + .22 * lit + roll
        t = t - .2 * np.clip((40 - y) / 36, 0, 1)                   # darker toward the hem
        t = t - .16 * np.clip((y - 56) / 8, 0, 1)                   # shade under the collar
        t = t + .05 * np.exp(-((x * .06) ** 2 + ((y - 46) * .05) ** 2))    # broad light across the shoulder blades
        t = t + .015 * np.sin(y * 2.6)                               # faint weave
        rgb = ramp(t, RED)
        inner = N[..., 2] > .5
        side = np.abs(N[..., 0]) > .5
        rgb = np.where((inner | side)[..., None], ramp(t - .12, LINING), rgb)
        h = hem_y(x)
        trim = (y - h < 2.2) & ~inner
        rgb = np.where(trim[..., None], ramp(.45 + .3 * lit + .25 * (y - h) / 2.2, GOLD), rgb)
        stitch = (y - h > 3) & (y - h < 3.6) & ((np.floor(x * 1.2) % 2) == 0) & ~inner
        rgb = np.where(stitch[..., None], ramp(t - .16, RED), rgb)
        if edge_trim:
            et = (y - h > 0) & (edge_dist() < 1) & ~inner & (lp[..., 1] > fr[1] + 1)
            rgb = np.where(et[..., None], ramp(.5 + .3 * lit, GOLD), rgb)
        al = np.where(y >= h, 255., 0.)
        return rgb, al
    return f


def collar_shader(P, N, cube):
    lit = N @ CAPE_LIGHT
    lp, fr, to = LOC['p'], np.array(LOC['fr']), np.array(LOC['to'])
    t = .6 + .2 * lit - .14 * np.clip((fr[1] + 3 - lp[..., 1]) / 3, 0, 1)
    rgb = ramp(t, RED)
    rgb = np.where((N[..., 2] > .5)[..., None], ramp(t - .14, LINING), rgb)
    top = to[1] - lp[..., 1] < 1.2                                   # gold piping along the top edge
    return np.where(top[..., None], ramp(.5 + .3 * lit, GOLD), rgb), np.full(P.shape[:2], 255.)


def cape():
    """A long crimson cape from the doc: a raised collar behind the neck, a yoke over the upper back so it hangs from the shoulders,
    then 14 pleats that fan from the shoulders to the feet, flaring past the arms and wrapping forward at the sides."""
    t = Back('back_cape')
    top, L, n, w = 64, 61, 14, 9
    t.own_bone('cape', (0, top, -17))
    for i in range(n):
        s_ = i / (n - 1) * 2 - 1
        xt, xb = 15 * s_, 42 * s_
        zt = -16.3 + (.7 if i % 2 else -.7)                          # ridge, valley, ridge ...
        zb = -27 + 15 * s_ * s_                                       # centre falls away from the legs, sides wrap forward
        rx = math.degrees(math.asin(np.clip(-(zb - zt) / L, -1, 1)))
        ry = -math.degrees(math.atan(.62 * s_)) + (10 if i % 2 else -10)
        rz = math.degrees(math.atan2(xb - xt, L))
        t.box(f'pleat_{i + 1:02d}', (xt - w / 2, top - L, zt - 1), (xt + w / 2, top, zt), cape_shader(edge_trim=i in (0, n - 1)),
              rot=(round(rx, 2), round(ry, 2), round(rz, 2)), origin=(xt, top, zt - .5), sub='cape', solid=False)
    # the yoke: the cape's top lies on the upper back, so it hangs from the shoulders instead of floating behind
    t.box('yoke', (-15, 59, -16.5), (15, 66, -10.5), cape_shader(flat=True), sub='cape')
    t.mirror('yoke_shoulder', (12, 60, -13.5), (18, 67, -9.5), cape_shader(flat=True), sub='cape')
    # raised collar standing behind the neck, wrapping forward at the sides
    t.box('collar', (-8, 63, -18), (8, 77, -16), collar_shader, rot=(-12, 0, 0), origin=(0, 63, -17), sub='cape')
    t.box('collar_l', (8, 62, -18), (16, 75, -16), collar_shader, rot=(-10, -38, 0), origin=(8, 62, -17), sub='cape')
    t.box('collar_r', (-16, 62, -18), (-8, 75, -16), collar_shader, rot=(-10, 38, 0), origin=(-8, 62, -17), sub='cape')
    # gold clasps where the collar meets the shoulders
    clasp = S(GOLD, base=.5, gain=.36, per_cube=True)
    t.mirror('clasp', (14, 61, -11), (18, 65, -9), clasp, sub='cape')
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
    """The Sword in HD (J00BA, 2026-11-15): a longsword painted at 8 texels per unit. Polished steel blade with a
    fuller, bevelled edges and an ogive point; a blackened steel crossguard with gold trim, flared quillons and a
    ruby set in its centre; a black leather grip bound in criss-cross silver wire; a faceted pommel with a ruby.
    Later the same day: the trim is dark silver, the gems are emeralds and the grip is plain wrapped leather."""
    t = Back('back_sword')
    t.PPU = 8
    t.HIDE_IN_BODY = False
    A = (-20, 63)
    p = Prop(t, A, 50)
    BLACK = ['#0b0c0f', '#14161a', '#1d2025', '#272b31', '#333840', '#424851', '#565d67', '#737b85', '#9aa2ab']
    GOLDT = ['#1c1e21', '#2a2d31', '#3a3e43', '#4d5258', '#62686f', '#7d838a', '#9ea4aa']   # dark silver trim (J00BA, 2026-11-15)
    RUBY = ['#021a0c', '#063c1c', '#0c6630', '#14924a', '#3cc472', '#9ef0bc', '#effff4']   # an emerald (J00BA, 2026-11-15)
    WIRE = ['#3c4148', '#69717a', '#a0a8b0', '#d4dade', '#f6f9fa']
    LEATH = ['#060607', '#0d0d0f', '#151518', '#1e1e22', '#28282d', '#34343a']

    def local_uv():
        q = LOC['p']
        return q[..., 0] - A[0], q[..., 1] - A[1]

    def blade_tone(u_abs, v, hw, lit):
        """Steel across a blade of half width hw: fuller in the middle, flats, bevels to a bright edge."""
        a = u_abs / hw
        t_ = .60 + .14 * lit + .08 * (vnoise(a * 3 + 20, v * .12, 7) - .5) + .07 * (vnoise(a * 18, v * .9, 11) - .5)
        t_ = t_ + .2 * np.exp(-((a - .5) / .14) ** 2)                       # sheen along each flat
        return a, t_

    def blade_shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = local_uv()
        lit = _light(N)
        if abs(n[2]) < .5:                                                  # the edges: a thin bright line
            t_ = .78 + .12 * lit + .05 * (vnoise(v * .9, u, 13) - .5)
            return ramp(np.clip(t_, 0, 1), STEEL), np.full(u.shape, 255.)
        a, t_ = blade_tone(np.abs(u), v, 3.5, lit)
        fl_end = -44.0
        in_fuller = (a < .24) & (v > fl_end) & (v < -7)
        rnd = (v <= fl_end + 1.2) & (np.hypot(a / .24, (v - fl_end - 1.2) / 1.2) < 1)   # the fuller's rounded end
        fuller = in_fuller | rnd
        tf = .44 + .25 * np.clip(u / (3.5 * .24), -1, 1) * .5 + .1 * lit + .05 * (vnoise(u * 9, v * .7, 17) - .5)
        t_ = np.where(fuller, tf, t_)
        lip = (~fuller) & (np.abs(a - .24) < .045) & (v > fl_end - .2) & (v < -7)
        t_ = np.where(lip, t_ + .25, t_)
        rgb = ramp(np.clip(t_, 0, 1), STEEL)
        bev = a > .72
        tb = .62 + .3 * (a - .72) / .28 + .1 * lit
        rgb = np.where(bev[..., None], ramp(np.clip(tb, 0, 1), EDGE), rgb)
        rgb = np.where((np.abs(a - .72) < .035)[..., None], ramp(np.full(a.shape, .22), STEEL), rgb)
        return rgb, np.full(u.shape, 255.)

    def tip_shader(P, N, cube):
        u, v = local_uv()
        lit = _light(N)
        s = np.clip((v - (-62)) / 12.0, 0, 1)                              # 0 at the point, 1 where the blade starts
        hw = 3.5 * np.sin(s * np.pi / 2) ** .75 + 1e-3                     # an ogive point
        a, t_ = blade_tone(np.abs(u), v, np.maximum(hw, .3), lit)
        rgb = ramp(np.clip(t_, 0, 1), STEEL)
        bev = (hw - np.abs(u)) < 1.0
        tb = .65 + .3 * np.clip(1 - (hw - np.abs(u)), 0, 1) + .1 * lit
        rgb = np.where(bev[..., None], ramp(np.clip(tb, 0, 1), EDGE), rgb)
        ridge = np.abs(u) < .09                                              # the point's centre ridge
        rgb = np.where(ridge[..., None], ramp(np.full(u.shape, .82), STEEL), rgb)
        return rgb, np.where(np.abs(u) <= hw, 255., 0.)

    def black_steel(gem=0., trim=.45, engrave=True):
        """Blackened steel with a gold inlaid rim, a fine engraved line inside it and an optional cut ruby."""
        def shader(P, N, cube):
            n = np.array(LOC['n'], float)
            u, v = _across(n)
            lit = _light(N)
            t_ = .38 + .3 * np.sqrt(np.clip(1 - u * u, 0, 1)) + .16 * lit + .05 * (vnoise(u * 10, v * 3, 23) - .5)
            rgb = ramp(np.clip(t_, 0, 1), BLACK)
            d = edge_dist()
            rgb = np.where((d < trim)[..., None], ramp(np.clip(.5 + .3 * lit + .25 * (1 - d / trim), 0, 1), GOLDT), rgb)
            if engrave:
                rgb = np.where((np.abs(d - trim - .35) < .06)[..., None], ramp(np.full(d.shape, .55), GOLDT), rgb)
            if gem and abs(n[2]) > .5:
                q = LOC['p']
                fr, to = np.array(LOC['fr']), np.array(LOC['to'])
                c = (fr + to) / 2
                r = np.hypot(q[..., 0] - c[0], q[..., 1] - c[1]) / gem
                ang = np.arctan2(q[..., 1] - c[1], q[..., 0] - c[0])
                facet = .5 + .25 * np.cos(ang * 4 + .6) * (r > .45) + .3 * np.clip(1 - np.hypot((q[..., 0] - c[0]) / gem + .3, (q[..., 1] - c[1]) / gem - .3) / .35, 0, 1)
                rgb = np.where((r < 1)[..., None], ramp(np.clip(facet, 0, 1), RUBY), rgb)
                rgb = np.where(((r >= 1) & (r < 1.3))[..., None], ramp(np.full(r.shape, .75), GOLDT), rgb)   # the setting
            return rgb, np.full(u.shape, 255.)
        return shader

    def grip_shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        lit = _light(N)
        t_ = .35 + .35 * np.sqrt(np.clip(1 - u * u, 0, 1)) + .15 * lit + .06 * (vnoise(u * 16, v * 8, 29) - .5)
        rgb = ramp(np.clip(t_, 0, 1), LEATH)
        band = (v % 1.5) / 1.5                                             # simple wrapped bands, a soft groove between
        rgb = np.where((band < .12)[..., None], rgb * .55, rgb)
        return rgb, np.full(u.shape, 255.)

    # pommel and grip
    p.b('pommel_cap', -2, 27, 2, 29, -19.5, -16.5, black_steel(trim=.3, engrave=False))
    p.b('pommel', -4, 20, 4, 27, -20.5, -15.5, black_steel(gem=1.6))
    p.b('pommel_neck', -2.5, 18, 2.5, 20, -20, -16, black_steel(trim=.3, engrave=False))
    p.b('grip', -2, 4, 2, 18, -19.5, -16.5, grip_shader)
    p.b('grip_ferrule', -2.5, 2, 2.5, 4, -20, -16, black_steel(trim=.3, engrave=False))
    # the crossguard: a bar, flared quillon ends and a centre block holding a ruby
    p.b('guard_bar', -10, -1, 10, 2, -19.5, -16.5, black_steel())
    for s_, nm in ((1, 'l'), (-1, 'r')):
        lo, hi = (10, 13) if s_ > 0 else (-13, -10)
        p.b(f'quillon_{nm}', lo, -2, hi, 4, -20, -16, black_steel(trim=.35))
    p.b('guard_centre', -4, -4, 4, 3, -20.5, -15.5, black_steel(gem=1.5))
    # the blade: ricasso, the main blade with its fuller and the ogive point
    p.b('ricasso', -3, -7, 3, -4, -19, -17, black_steel(trim=.25, engrave=False))
    p.b('blade', -3.5, -50, 3.5, -7, -19, -17, blade_shader)
    p.b('blade_point', -3.5, -62, 3.5, -50, -18.5, -17.5, tip_shader, faces=('north', 'south'), solid=False)
    press_to_back(t)
    t.save()


def samurai():
    """Two crossed katana in their scabbards, in HD (J00BA, 2026-11-15): painted at 8 texels per unit, every face kept.
    Glossy plum lacquer scabbards with a silk cord band, dark silver fittings (end cap, mouth, collar, pommel cap), a
    dark iron tsuba with a pierced pattern and a dark silver rim, plain wrapped hilts, a small emerald on each cap."""
    t = Back('back_samurai')
    t.PPU = 8
    t.HIDE_IN_BODY = False
    LACQ = ['#0b050c', '#170b19', '#241226', '#331a37', '#442349', '#5a305f', '#764080', '#9a5ca6', '#c58fd0']
    DSILV = ['#1c1e21', '#2a2d31', '#3a3e43', '#4d5258', '#62686f', '#7d838a', '#9ea4aa', '#c4c9cd']
    IRON = ['#08090a', '#111214', '#1a1c1f', '#24272b', '#2f3338', '#3c4147', '#4c525a']
    CORD = ['#0d0710', '#1a0e1f', '#2a1630', '#3a1f42', '#4c2a56']
    WRAP = ['#060607', '#0d0d0f', '#151518', '#1e1e22', '#28282d', '#34343a']
    EMER = ['#021a0c', '#063c1c', '#0c6630', '#14924a', '#3cc472', '#9ef0bc', '#effff4']

    def round_tone(n, u, lit, base=.36, roundness=.3):
        return base + roundness * np.sqrt(np.clip(1 - u * u, 0, 1)) + .16 * lit

    def lacquer(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        lit = _light(N)
        t_ = round_tone(n, u, lit, .30, .32) + .04 * (vnoise(u * 6, v * .3, 71) - .5)
        t_ = t_ + .34 * np.exp(-((u - .35) / .1) ** 2) + .14 * np.exp(-((u + .45) / .16) ** 2)   # glossy reflections
        return ramp(np.clip(t_, 0, 1), LACQ), np.full(u.shape, 255.)

    def dsilver(gem=0.):
        def shader(P, N, cube):
            n = np.array(LOC['n'], float)
            u, v = _across(n)
            lit = _light(N)
            t_ = round_tone(n, u, lit, .34, .3) + .05 * (vnoise(u * 10, v * 4, 73) - .5)
            d = edge_dist()
            t_ = t_ + np.where(d < .3, .16, 0) - np.where(np.abs(d - .45) < .06, .2, 0)   # a raised rim and a fine line
            rgb = ramp(np.clip(t_, 0, 1), DSILV)
            if gem and abs(n[2]) > .5:
                q = LOC['p']
                c = (np.array(LOC['fr']) + np.array(LOC['to'])) / 2
                r = np.hypot(q[..., 0] - c[0], q[..., 1] - c[1]) / gem
                ang = np.arctan2(q[..., 1] - c[1], q[..., 0] - c[0])
                fc = .5 + .25 * np.cos(ang * 4 + .6) * (r > .45) + .3 * np.clip(1 - np.hypot((q[..., 0] - c[0]) / gem + .3, (q[..., 1] - c[1]) / gem - .3) / .35, 0, 1)
                rgb = np.where((r < 1)[..., None], ramp(np.clip(fc, 0, 1), EMER), rgb)
                rgb = np.where(((r >= 1) & (r < 1.3))[..., None], ramp(np.full(r.shape, .8), DSILV), rgb)
            return rgb, np.full(u.shape, 255.)
        return shader

    def tsuba(P, N, cube):
        """Dark iron guard: a dark silver rim, hammered texture, pierced crescent windows on the broad faces."""
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        lit = _light(N)
        t_ = .36 + .16 * lit + .1 * (vnoise(u * 7, v * 7, 79) - .5) + .06 * (vnoise(u * 20, v * 20, 83) - .5)
        rgb = ramp(np.clip(t_, 0, 1), IRON)
        d = edge_dist()
        rgb = np.where((d < .35)[..., None], ramp(np.clip(.55 + .25 * lit, 0, 1), DSILV), rgb)
        if abs(n[1]) > .5:                                               # the guard's broad faces (along the sword)
            q = LOC['p']
            fr, to = np.array(LOC['fr']), np.array(LOC['to'])
            c = (fr + to) / 2
            x, z = q[..., 0] - c[0], q[..., 2] - c[2]
            for s_ in (-1, 1):
                r1 = np.hypot(x - s_ * 2.6, z)
                win = (r1 < 1.1) & (np.hypot(x - s_ * 2.1, z) > .8)
                rgb = np.where(win[..., None], ramp(np.full(x.shape, .02), IRON), rgb)
        return rgb, np.full(u.shape, 255.)

    def cord(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        lit = _light(N)
        ph = (v * 2.2 + u * .8) % 1
        t_ = .3 + .3 * np.sin(ph * np.pi) + .15 * lit + .15 * np.sqrt(np.clip(1 - u * u, 0, 1))
        return ramp(np.clip(t_, 0, 1), CORD), np.full(u.shape, 255.)

    def hilt(P, N, cube):
        """A plain wrapped hilt: black cord in even bands, a soft groove between them."""
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        lit = _light(N)
        t_ = round_tone(n, u, lit, .3, .35) + .06 * (vnoise(u * 16, v * 8, 89) - .5)
        rgb = ramp(np.clip(t_, 0, 1), WRAP)
        band = (v % 1.5) / 1.5
        rgb = np.where((band < .12)[..., None], rgb * .55, rgb)
        return rgb, np.full(u.shape, 255.)

    for nm, th, z in (('a', 42, -20), ('b', -42, -25)):
        p = Prop(t, (0, 44), th)
        zz, zi = (z, z + 4), (z + .5, z + 3.5)
        p.b(f'chape_{nm}', -3.5, -30, 3.5, -26, *zz, dsilver())
        p.b(f'scabbard_{nm}', -3, -26, 3, 21, *zi, lacquer)
        p.b(f'cord_{nm}', -3.5, 13, 3.5, 16, *zz, cord)
        p.b(f'mouth_{nm}', -3.5, 21, 3.5, 23, *zz, dsilver())
        p.b(f'collar_{nm}', -3, 23, 3, 24, *zi, dsilver())
        p.b(f'tsuba_{nm}', -5.5, 24, 5.5, 26, z - 1, z + 5, tsuba)
        p.b(f'fuchi_{nm}', -3, 26, 3, 28, *zi, dsilver())
        p.b(f'hilt_{nm}', -2.5, 28, 2.5, 45, *zi, hilt)
        p.b(f'cap_{nm}', -3, 45, 3, 48, *zz, dsilver(gem=1.1))
    t.save()


# ---- the Scythe in HD (J00BA, 2026-11-15): painted at 8 texels per unit, a curved forged blade with a polished
# edge and a spine, a wooden snath with leather grips and two nibs, steel fittings with brass rivets.
def _hash(ix, iy, seed):
    h = (ix * 374761393 + iy * 668265263 + seed * 2147483647) & 0xffffffff
    h = ((h ^ (h >> 13)) * 1274126177) & 0xffffffff
    return (h & 0xffff) / 65535.0


def vnoise(x, y, seed=0):
    """Smooth value noise, about one feature per unit of x and y."""
    ix, iy = np.floor(x).astype(np.int64), np.floor(y).astype(np.int64)
    fx, fy = x - ix, y - iy
    fx, fy = fx * fx * (3 - 2 * fx), fy * fy * (3 - 2 * fy)
    a, b = _hash(ix, iy, seed), _hash(ix + 1, iy, seed)
    c, d = _hash(ix, iy + 1, seed), _hash(ix + 1, iy + 1, seed)
    return (a * (1 - fx) + b * fx) * (1 - fy) + (c * (1 - fx) + d * fx) * fy


def _across(n):
    """(u from -1 to 1 across the face, v along the cube's length in units). Across is depth on the side faces."""
    p, fr, to = LOC['p'], np.array(LOC['fr']), np.array(LOC['to'])
    k = 2 if abs(n[0]) > .5 else 0
    c, hw = (fr[k] + to[k]) / 2, (to[k] - fr[k]) / 2
    return (p[..., k] - c) / hw, p[..., 1]


def _light(N):
    return N @ L_KEY


STEEL = ['#0f1316', '#1d2328', '#2e363d', '#465058', '#66727b', '#8c98a0', '#b9c3c9', '#e4ebee', '#ffffff']
EDGE = ['#3a454c', '#6e7c85', '#a6b3ba', '#d6dfe3', '#f4f8f9', '#ffffff']
WOOD = ['#0d0d0e', '#151516', '#1d1d1f', '#262628', '#303032', '#3b3b3d', '#48484a']   # charcoal (J00BA, 2026-11-15)
LEATHER = ['#4a4c4f', '#66686b', '#818386', '#9c9ea1', '#b6b8bb', '#cfd1d3']   # light grey wraps (J00BA, 2026-11-15)
DARK = ['#121314', '#1b1c1e', '#242628', '#2e3033', '#383b3e', '#44474b', '#53575b', '#686c70', '#83878b']   # the blade: dark grey steel (J00BA, 2026-11-15)
DARK_EDGE = ['#3a3d41', '#4c5055', '#62666b', '#7a7e83', '#93979b', '#a8abaf']
BRASS = ['#2e1d06', '#55380c', '#806018', '#ab8a30', '#d6b65a', '#f4e08e', '#fff6cc']


def steel_shader(edge_side=None, spine=False, etched=False, cube_tone=0., stops=None):
    """Forged steel: brushed streaks along the length, a broad specular band, a bright polished edge with a fine
    grind line on one side (edge_side -1: local -x), small scratches, an optional etched vine."""
    def shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        big = abs(n[2]) > .5                                    # the blade's flat faces
        lit = _light(N)
        t = .46 + .16 * lit + cube_tone
        t = t + .10 * (vnoise(u * 2.5 + 40, v * .15, 3) - .5)    # long soft tone drift
        t = t + .07 * (vnoise(u * 9 + 7, v * .6, 5) - .5)        # brushed streaks along the length
        t = t + .04 * (vnoise(u * 30, v * 2.5, 9) - .5)
        if big:
            t = t + .22 * np.exp(-((u - .15 * np.sin(v * .21)) / .32) ** 2)   # anisotropic highlight band
            if spine:
                t = t - .10 * np.clip(u, 0, 1)
        else:
            t = t + .18 * np.exp(-(u / .45) ** 2) - .08          # a rounded bevel catching the light
        sx, sy = P[..., 0], P[..., 1]
        scratch = np.abs(((sx * .83 + sy * .55 + vnoise(sx, sy, 21) * 2) % 7.3) - 3.6) < .05
        t = t + np.where(scratch & (vnoise(sx * .4, sy * .4, 17) > .62), .14, 0)
        rgb = ramp(np.clip(t, 0, 1), stops or STEEL)
        if big and edge_side is not None:
            d = (1 + u * -edge_side) * (np.array(LOC['to'])[0] - np.array(LOC['fr'])[0]) / 2   # units from the edge
            e = d < 1.4
            grind = (d >= 1.4) & (d < 1.6)
            te = .55 + .3 * np.clip(1 - d / 1.4, 0, 1) + .15 * lit + .12 * (vnoise(v * .8, d * 6, 31) - .5)
            rgb = np.where(e[..., None], ramp(np.clip(te, 0, 1), EDGE), rgb)
            rgb = np.where(grind[..., None], ramp(np.full(t.shape, .18), STEEL), rgb)
        if big and etched:
            line = .35 * np.sin(v * .9)
            leaf = (np.abs(((v * .9) % (2 * np.pi)) - np.pi / 2) < .35) & (np.abs(u - line - .18) < .12)
            m = (np.abs(u - line) < .07) | leaf
            rgb = np.where(m[..., None], rgb * .62, rgb)
        return rgb, np.full(t.shape, 255.)
    return shader


def wood_shader():
    """The snath: a round-looking dark walnut pole. Wandering grain, pores, a few small knots, lit down the middle."""
    def shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        round_ = np.sqrt(np.clip(1 - u * u, 0, 1))
        t = .30 + .30 * round_ + .12 * _light(N) - (.12 if abs(n[1]) > .5 else 0)
        g = u * 3 + .9 * vnoise(u * 2, v * .08, 41) + .25 * np.sin(v * .05)
        t = t + .13 * np.sin(g * 6.3) * (vnoise(u * 3, v * .3, 43) * .6 + .4)
        t = t - .10 * (vnoise(u * 20, v * 1.4, 47) > .78)
        for kv in (24.0, 47.0, 76.0):
            r = np.hypot((v - kv) * .55, (u - .2) * 2.2)
            t = t - .22 * np.clip(1 - r, 0, 1) + .08 * np.sin(r * 9) * np.clip(1.6 - r, 0, 1)
        return ramp(np.clip(t, 0, 1), WOOD), np.full(t.shape, 255.)
    return shader


def leather_shader():
    """A leather grip wrapped on a slant: each turn rounded and lit, a dark gap between turns, pale stitches."""
    def shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        ph = (v * .9 + u * .55) % 1.6 / 1.6
        t = .22 + .22 * np.sin(ph * np.pi) + .12 * _light(N) + .2 * np.sqrt(np.clip(1 - u * u, 0, 1))
        t = t + .06 * (vnoise(u * 14, v * 6, 51) - .5)
        rgb = ramp(np.clip(t, 0, 1), LEATHER)
        gap = (ph < .08) | (ph > .95)
        rgb = np.where(gap[..., None], ramp(np.full(t.shape, .02), LEATHER), rgb)
        stitch = (np.abs(ph - .5) < .05) & (((v * 4) % 1) < .5)
        rgb = np.where(stitch[..., None], np.array([52, 54, 58], float) * (.75 + .25 * _light(N))[..., None], rgb)
        return rgb, np.full(t.shape, 255.)
    return shader


def fitting_shader(rivets=0, band=True):
    """Steel rings and caps: polished, a rolled lip at each end, brass rivets down the face."""
    def shader(P, N, cube):
        n = np.array(LOC['n'], float)
        u, v = _across(n)
        fr, to = np.array(LOC['fr']), np.array(LOC['to'])
        tv = (v - fr[1]) / max(to[1] - fr[1], 1e-6)
        t = .40 + .30 * np.sqrt(np.clip(1 - u * u, 0, 1)) + .16 * _light(N)
        t = t + .05 * (vnoise(u * 12, v * 4, 61) - .5)
        if band:
            t = t + np.where((tv < .14) | (tv > .86), .14, 0) - np.where((np.abs(tv - .14) < .04) | (np.abs(tv - .86) < .04), .25, 0)
        rgb = ramp(np.clip(t, 0, 1), STEEL)
        if rivets and abs(n[1]) < .5:
            hw = (to[2] - fr[2]) / 2 if abs(n[0]) > .5 else (to[0] - fr[0]) / 2
            for k in range(rivets):
                cv = fr[1] + (to[1] - fr[1]) * (k + .5) / rivets
                r = np.hypot(u * hw, v - cv) / .6
                tr = .4 + .5 * np.clip(1 - np.hypot(u * hw + .25, v - cv - .2) / .6, 0, 1)
                rgb = np.where((r < 1)[..., None], ramp(np.clip(tr, 0, 1), BRASS), rgb)
                rgb = np.where(((r >= 1) & (r < 1.3))[..., None], rgb * .45, rgb)
        return rgb, np.full(t.shape, 255.)
    return shader


def arc_points(n=11):
    """The blade's back curve: a cubic from the heel at the socket, out to the left and down to the tip."""
    P0, P1, P2, P3 = np.array([-24., 86.]), np.array([-50., 94.]), np.array([-62., 64.]), np.array([-44., 36.])
    ts = np.linspace(0, 1, n + 1)
    return [tuple(float(c) for c in ((1 - s) ** 3) * P0 + 3 * ((1 - s) ** 2) * s * P1 + 3 * (1 - s) * s * s * P2 + s ** 3 * P3) for s in ts]


def seg_off(t, name, A, B, u0, u1, z0, z1, sh, extra=0):
    """A cube from A toward B (local +y toward B) spanning u0..u1 across it; `extra` units past B close the joints."""
    dx, dy = B[0] - A[0], B[1] - A[1]
    L = max(1, round(math.hypot(dx, dy) + extra))
    th = round(math.degrees(math.atan2(-dx, dy)), 2)
    t.box(name, (A[0] + u0, A[1], z0), (A[0] + u1, A[1] + L, z1), sh, rot=(0, 0, th), origin=(A[0], A[1], (z0 + z1) / 2))


def scythe():
    t = Back('back_scythe')
    t.PPU = 8
    t.HIDE_IN_BODY = False       # every fitting stays a closed ring when the scythe is viewed on its own
    p = Prop(t, (29, 8), 37)
    wood, grip, ring = wood_shader(), leather_shader(), fitting_shader()
    # the snath, butt to socket, with a spiked steel butt cap
    p.b('butt_spike', -1, -10, 1, -7, -18.5, -16.5, steel_shader())
    p.b('butt_cap', -2.5, -7, 2.5, 1, -20, -15, fitting_shader(rivets=1))
    p.b('shaft', -1.5, 1, 1.5, 88, -19, -16, wood)
    for i, v0 in enumerate((12, 52)):                           # two leather grips, a steel ring at each end
        p.b(f'grip_{i + 1}', -2, v0, 2, v0 + 14, -19.5, -15.5, grip)
        p.b(f'grip_ring_{i + 1}a', -2.5, v0 - 2, 2.5, v0, -20, -15, ring)
        p.b(f'grip_ring_{i + 1}b', -2.5, v0 + 14, 2.5, v0 + 16, -20, -15, ring)
    for i, v0 in enumerate((32, 70)):                           # the nibs: short pegs standing off the snath
        p.b(f'nib_{i + 1}', -1, v0, 1, v0 + 2, -26, -19, wood)
        p.b(f'nib_cap_{i + 1}', -1.5, v0 - .5, 1.5, v0 + 2.5, -28, -26, ring)
    p.b('ferrule_mid', -2.5, 42, 2.5, 45, -20, -15, ring)
    p.b('socket', -3, 84, 3, 94, -20.5, -14.5, fitting_shader(rivets=2))
    p.b('socket_cap', -2, 94, 2, 97, -20, -15, fitting_shader(band=False))
    # the blade: one plate cut to a smooth crescent (outline painted at 8 texels per unit, so the curve is clean),
    # shaded along the curve: dark forged steel at the spine, a broad sheen, a polished inner edge and a grind line.
    # A raised 3D spine runs along its back.
    n = 18
    pts = arc_points(n)
    dense = np.array(arc_points(400))
    seglen = np.hypot(*np.diff(dense, axis=0).T)
    arclen = np.concatenate([[0], np.cumsum(seglen)])
    width = lambda s: 2 + 10 * (1 - s) ** .8 - 2 * s ** 4            # 12 units at the heel to a point at the tip
    d_ = np.diff(dense, axis=0)
    d_ = np.vstack([d_, d_[-1:]])
    d_ /= np.linalg.norm(d_, axis=1, keepdims=True)
    inward = np.stack([-d_[:, 1], d_[:, 0]], 1)                      # local -x of a cube along the curve: the inner side
    ss = np.linspace(0, 1, len(dense))
    inner = dense + inward * np.array([width(s) for s in ss])[:, None]
    poly = np.vstack([dense, inner[::-1]])

    def blade_shader(P, N, cube):
        xy = P[..., :2]
        flat = xy.reshape(-1, 2)
        best_d = np.full(len(flat), 1e9)
        best_i = np.zeros(len(flat), int)
        for k in range(0, len(dense), 4):                             # nearest point on the spine curve
            dd = np.hypot(flat[:, 0] - dense[k, 0], flat[:, 1] - dense[k, 1])
            m = dd < best_d
            best_d[m], best_i[m] = dd[m], k
        sh = xy.shape[:-1]
        s = (best_i / (len(dense) - 1)).reshape(sh)
        dist = best_d.reshape(sh)
        v = arclen[best_i].reshape(sh)
        w = width(s)
        a = np.clip(dist / np.maximum(w, .5), 0, 1)                   # 0 at the spine, 1 at the edge
        lit = _light(N)
        band = a - .45 - .08 * np.sin(v * .12)
        t = .32 + .12 * lit + .42 * np.exp(-(band / .2) ** 2) - .12 * np.clip(.25 - a, 0, 1) * 4
        t = t + .22 * np.exp(-((band - .17) / .03) ** 2)                # a sharp reflected line beside the sheen
        t = t + .08 * (vnoise(a * 3 + 40, v * .12, 3) - .5) + .06 * (vnoise(a * 14, v * .9, 5) - .5) + .03 * (vnoise(a * 40, v * 3, 9) - .5)
        sx, sy = P[..., 0], P[..., 1]
        scratch = np.abs(((sx * .83 + sy * .55 + vnoise(sx, sy, 21) * 2) % 7.3) - 3.6) < .05
        t = t + np.where(scratch & (vnoise(sx * .4, sy * .4, 17) > .6), .12, 0)
        rgb = ramp(np.clip(t, 0, 1), DARK)
        to_edge = w - dist
        e = to_edge < 1.6
        te = .5 + .35 * np.clip(1 - to_edge / 1.6, 0, 1) + .12 * lit + .1 * (vnoise(v * .7, to_edge * 5, 31) - .5)
        rgb = np.where(e[..., None], ramp(np.clip(te, 0, 1), DARK_EDGE), rgb)
        rgb = np.where(((to_edge >= 1.6) & (to_edge < 1.85))[..., None], ramp(np.full(t.shape, .1), DARK), rgb)
        keep = inpoly(sx, sy, [tuple(q) for q in poly])
        return rgb, np.where(keep, 255., 0.)

    x0, y0 = np.floor(poly.min(0)).astype(int)
    x1, y1 = np.ceil(poly.max(0)).astype(int)
    t.box('blade', (x0, y0, -18.5), (x1, y1, -17.5), blade_shader, faces=('north', 'south'), solid=False)
    for i in range(n - 3):
        seg_off(t, f'spine_{i + 1}', pts[i], pts[i + 1], 0, 1, -19.5, -16.5, steel_shader(cube_tone=-.08, stops=DARK), extra=1)
    press_to_back(t)
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
    press_to_back(t)
    t.save()


ALL = (imp_wings, golden_wings, angel_wings, bone_wings, mechanical_wings, cape, sword, samurai, scythe, trident)
if __name__ == '__main__':
    for f in ALL:
        f()
