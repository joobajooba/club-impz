"""Fit checks for every Head model, then each one rendered from the showcase next to its art."""
import json, os
import numpy as np
from PIL import Image, ImageDraw
import render_bb
from render_bb import load_tex, cube_world, FRONT, SIDE, yaw

OUT = 'C:/Users/lucas/blockbench_models/impz/head/'
A = 'C:/Users/lucas/club-impz/'
body = json.load(open(A + 'godot-game/assets/models/impz/bodies/body_green.bbmodel', encoding='utf8'))
Wb = cube_world(body)
Tb = load_tex(body)[0]
# solid bases over the skull: horns and ears are meant to come out through these, so they don't count as clipping
PIERCED = ('crown', 'hood', 'hair', 'dome', 'band', 'wig', 'curtain', 'back', 'rim_side', 'sides', 'cheek', 'pad', 'brim', 'droop', 'behind_ear', 'forehead', 'mass', 'top')
# which skull faces must be fully covered. Bald on purpose per the doc: fez, crown, halo, geezer, hawk, tiara.
COVER = {'afro': 'top left right back', 'blonde': 'top left right back', 'bob': 'top left right back', 'slick': 'top left right back', 'clown': 'top left right back',
         'cap': 'top left right back', 'mayc_brim': 'top left right back', 'sea_captain': 'top left right back', 'soldier': 'top left right back', 'spiky': 'top', 'straw_hat': 'top'}
NAMES = ['afro', 'blonde', 'bob', 'cap', 'clown', 'crown', 'fez', 'geezer', 'halo', 'hawk', 'mayc_brim', 'sea_captain', 'slick', 'soldier', 'spiky', 'straw_hat', 'tiara']


def ear_points():
    pts = []
    for u8 in ('fc7c5ec5', '2e79580e'):
        ear = next(e for e in body['elements'] if e['uuid'].startswith(u8))
        M = Wb[ear['uuid']]
        u1, v1, u2, v2 = ear['faces']['south']['uv']
        a, c = ear['from'], ear['to']
        for i in range(0, 211, 2):
            for j in range(0, 141, 2):
                s, q = i / 210, j / 140
                if Tb[min(255, int(v1 + (v2 - v1) * q)), min(255, int(u1 + (u2 - u1) * s)), 3] > 32:
                    pts.append(M @ np.array([a[0] + s * (c[0] - a[0]), c[1] - q * (c[1] - a[1]), a[2], 1]))
    return np.array(pts)


def horn_points():
    pts = []
    for e in body['elements']:
        if e['name'].startswith('horn_'):
            M = Wb[e['uuid']]
            for x in np.linspace(e['from'][0], e['to'][0], 7):
                for y in np.linspace(e['from'][1], e['to'][1], 9):
                    for z in np.linspace(e['from'][2], e['to'][2], 7):
                        pts.append(M @ np.array([x, y, z, 1]))
    return np.array(pts)


EARS, HORNS = ear_points(), horn_points()
# the face: eyes, the brows' lower part, and the mouth must stay clear
FACE = np.array([[x, y, 20.0, 1.0] for x in np.arange(-13.5, 14, 1) for y in np.arange(66.5, 81.5, 1)])
flags = 0
for n in NAMES:
    d = json.load(open(f'{OUT}head_{n}.bbmodel', encoding='utf8'))
    E = d['elements']
    W = cube_world(d)
    roots = [g['name'] for g in d['groups'][::2]]
    for r, g in zip(roots, d['groups'][::2]):
        assert g['origin'] == next(b for b in body['groups'] if b['name'] == r)['origin'], (n, r)
    for e in E:
        s = [b - a for a, b in zip(e['from'], e['to'])]
        assert all(abs(v - round(v)) < 1e-6 and v > 0 for v in s), (n, e['name'], s)
    ear, horn, face = 0, 0, 0
    bad = set()
    for e in E:
        Mi = np.linalg.inv(W[e['uuid']])
        a, b = np.array(e['from']), np.array(e['to'])
        lo = (Mi @ EARS.T).T[:, :3]
        k = int(((lo >= a) & (lo <= b)).all(1).sum())
        if k and not e['name'].startswith(PIERCED):
            ear += k
            bad.add('ear:' + e['name'])
        lo = (Mi @ HORNS.T).T[:, :3]
        k = int(((lo >= a) & (lo <= b)).all(1).sum())
        if k and not e['name'].startswith(PIERCED):
            horn += k
            bad.add('horn:' + e['name'])
        # does any cube in front of the face reach down over the eyes or mouth? (bare x,y test on what's forward of the face)
        cs = np.array([(W[e['uuid']] @ np.array([x, y, z, 1]))[:3] for x in (e['from'][0], e['to'][0]) for y in (e['from'][1], e['to'][1]) for z in (e['from'][2], e['to'][2])])
        if cs[:, 2].max() > 19 and cs[:, 1].min() < 81 and cs[:, 0].min() < 13 and cs[:, 0].max() > -13 and not e['name'].endswith('_glow'):
            face += 1
            bad.add('face:' + e['name'])
    # GAP TEST 1: walk outward from every unit of skull above the hairline. Anything no cube reaches is bare skull showing.
    inv = {e['uuid']: np.linalg.inv(W[e['uuid']]) for e in E}

    def covered(p, nrm):
        for dist in np.arange(.05, 40, .5):
            q = np.array([*(p + nrm * dist), 1.])
            for e in E:
                lq = inv[e['uuid']] @ q
                if all(e['from'][k] <= lq[k] <= e['to'][k] for k in range(3)):
                    return True
        return False

    sk = {'top': (np.array([0, 1., 0]), [(x, 91, z) for x in np.arange(-14.5, 15) for z in np.arange(-8.5, 19)]),
          'left': (np.array([-1., 0, 0]), [(-15, y, z) for y in np.arange(84.5, 91) for z in np.arange(-8.5, 19)]),
          'right': (np.array([1., 0, 0]), [(15, y, z) for y in np.arange(84.5, 91) for z in np.arange(-8.5, 19)]),
          'back': (np.array([0, 0, -1.]), [(x, y, -9) for x in np.arange(-14.5, 15) for y in np.arange(84.5, 91)])}
    gaps = {}
    for fc in COVER.get(n, '').split():
        nrm, pts = sk[fc]
        miss = sum(not covered(np.array(p, float), nrm) for p in pts)
        if miss:
            gaps[fc] = miss
    # GAP TEST 2: every cube must touch another cube or the body. Sampled on a grid, so rotated cubes count too.
    samples = {}
    for e in E:
        g = [np.linspace(e['from'][k], e['to'][k], max(2, int((e['to'][k] - e['from'][k])) + 1)) for k in range(3)]
        pts = np.array([[x, y, z, 1.] for x in g[0] for y in g[1] for z in g[2]])
        samples[e['name']] = (W[e['uuid']] @ pts.T).T[:, :3]
    names = list(samples)
    linked = {nm: set() for nm in names}
    grounded = set()
    sf, st = np.array([-15, 63, -9.]), np.array([15, 91, 19.])
    bf, bt = np.array([-16, 27, -12.]), np.array([16, 66, 12.])
    for nm in names:
        if ((samples[nm] >= sf - .8) & (samples[nm] <= st + .8)).all(1).any() or ((samples[nm] >= bf - .8) & (samples[nm] <= bt + .8)).all(1).any():
            grounded.add(nm)
    for i, p in enumerate(names):
        for q in names[i + 1:]:
            A_, B_ = samples[p], samples[q]
            if len(A_) * len(B_) > 3e6:
                A_, B_ = A_[::4], B_[::4]
            if np.min(np.linalg.norm(A_[:, None] - B_[None], axis=-1)) <= 1.1:
                linked[p].add(q)
                linked[q].add(p)
    stack, seen = list(grounded), set(grounded)
    while stack:
        for q in linked[stack.pop()]:
            if q not in seen:
                seen.add(q)
                stack.append(q)
    floating = [nm for nm in names if nm not in seen and not nm.startswith(('ember', 'ring'))]
    over = len(E) > 40
    flag = ear or horn or face or over or gaps or floating
    if gaps:
        bad.add('bare skull ' + str(gaps))
    if floating:
        bad.add('floating ' + str(floating))
    flags += bool(flag)
    print(f"{n:12s} cubes {len(E):3d} roots {roots} ear {ear} horn {horn} face {face}" + (' <-- CHECK ' + ','.join(sorted(bad))[:150] if flag else ''))
print('traits to look at:', flags)

sc = json.load(open(OUT + 'head_showcase.bbmodel', encoding='utf8'))
members = json.load(open('head_members.json'))
all_ids = {e['uuid'] for e in sc['elements']}
tex = load_tex(sc)
base = Image.open(A + 'docs/imp-traits/bodies/body_silver_1870.png').convert('RGBA')
ch = 300
cells = []
for name, m in members.items():
    ox, _, oz = m['off']
    hide = all_ids - set(m['ids'])
    art = base.copy()
    p = f'{A}docs/imp-traits/layers/head_{name}.png'
    if os.path.exists(p):
        art.alpha_composite(Image.open(p).convert('RGBA'))
    tall = name == 'blonde'
    art = art.crop((0, 0, 64, 64) if tall else (4, 0, 60, 44)).convert('RGB')
    art = art.resize((int(art.width * ch / art.height), ch), Image.NEAREST)
    y0, y1 = (20, 122) if tall else (58, 122)
    ppu = ch / (y1 - y0)
    hw = 36
    views = [render_bb.render(sc, tex, FRONT, ppu, (ox - hw, ox + hw, y0, y1), hide=hide),
             render_bb.render(sc, tex, SIDE, ppu, (oz - 34, oz + 40, y0, y1), hide=hide)]
    rq = yaw(35, 12) @ np.eye(3)
    p3 = np.array([ox, 0, oz])
    # 3/4 and back: move the bounds to where this Imp lands in the rotated view
    c3 = rq @ p3
    views.append(render_bb.render(sc, tex, rq, ppu, (c3[0] - hw, c3[0] + hw, c3[1] + y0, c3[1] + y1), hide=hide))
    rb = yaw(180, 0)
    cb = rb @ p3
    views.append(render_bb.render(sc, tex, rb, ppu, (cb[0] - hw, cb[0] + hw, y0, y1), hide=hide))
    w = art.width + sum(v.width for v in views) + 4 * len(views)
    c = Image.new('RGB', (w, ch), (15, 15, 15))
    c.paste(art, (0, 0))
    x = art.width + 4
    for v in views:
        c.paste(v, (x, 0))
        x += v.width + 4
    ImageDraw.Draw(c).text((4, 2), name, fill=(255, 255, 0))
    cells.append(c)
os.makedirs('head_sheets', exist_ok=True)
for page, group in enumerate([cells[:6], cells[6:12], cells[12:]]):
    o = Image.new('RGB', (max(c.width for c in group), (ch + 6) * len(group)), (40, 40, 40))
    for i, c in enumerate(group):
        o.paste(c, (0, i * (ch + 6)))
    o.save(f'head_sheets/page{page + 1}.png')
    print('page', page + 1, o.size)
render_bb.render(sc, tex, yaw(24, 14), 1.4, (-340, 340, -110, 150)).save('head_sheets/lineup.png')
