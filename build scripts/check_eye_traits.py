"""Fit checks for every Eyes model, then each trait rendered from the showcase file next to its art."""
import itertools, json, os, sys
import numpy as np
from PIL import Image, ImageDraw
import render_bb
from render_bb import load_tex, cube_world, FRONT, SIDE, yaw

OUT = 'C:/Users/lucas/blockbench_models/impz/eyes/'
A = 'C:/Users/lucas/club-impz/'
body = json.load(open(A + 'godot-game/assets/models/impz/bodies/body_green.bbmodel', encoding='utf8'))
Wb = cube_world(body)
Tb = load_tex(body)[0]
MODELS = ['3d_glasses', 'shades', 'bug_eye', 'glasses', 'hearts', 'stars', 'goggles', 'mask', 'robo', 'eye_patch', 'monacle', 'tracker_blue', 'tracker_purple', 'lazer', 'neon_beam']
HIDES_EYES = {'3d_glasses', 'shades', 'bug_eye', 'goggles', 'mask', 'robo', 'stars'}


def corners(e, W):
    M = W[e['uuid']]
    return np.array([(M @ np.array([x, y, z, 1]))[:3] for x in (e['from'][0], e['to'][0]) for y in (e['from'][1], e['to'][1]) for z in (e['from'][2], e['to'][2])])


# sample points of what the trait must not cut into
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
face = np.array(Image.open(A + 'godot-game/assets/textures/impz/bodies/body_green.png').convert('RGB')).astype(int)[29:57, 0:30]
ey, ex = np.where((face.max(-1) - face.min(-1) < 14) & (np.arange(28)[:, None] >= 9) & (np.arange(28)[:, None] <= 19))
fails = 0
for name in MODELS:
    d = json.load(open(f'{OUT}eyes_{name}.bbmodel', encoding='utf8'))
    E = d['elements']
    W = cube_world(d)
    assert d['groups'][0]['name'] == 'Head' and d['groups'][0]['origin'] == next(g for g in body['groups'] if g['name'] == 'Head')['origin']
    for e in E:
        s = [b - a for a, b in zip(e['from'], e['to'])]
        assert all(abs(v - round(v)) < 1e-6 and v > 0 for v in s), (name, e['name'], s)
    # cube-in-cube overlaps between unrotated cubes
    un = [e for e in E if not e.get('rotation')]
    ov = [(a['name'], b['name']) for a, b in itertools.combinations(un, 2)
          if all(min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]) > 1e-6 for k in range(3))]
    ear = horn = 0
    for e in E:
        Mi = np.linalg.inv(W[e['uuid']])
        for pts, tag in ((EARS, 'ear'), (HORNS, 'horn')):
            lp = (Mi @ pts.T).T[:, :3]
            n = int(((lp >= np.array(e['from']) - 1e-6) & (lp <= np.array(e['to']) + 1e-6)).all(1).sum())
            if tag == 'ear':
                ear += n
            else:
                horn += n
    miss = None
    if name in HIDES_EYES:
        flat = [e for e in E if not e.get('rotation') and e['from'][2] > 10 and not e['name'].startswith(('arm', 'strap', 'tie', 'side'))]
        miss = sum(1 for y, x in zip(ey, ex) if not any(e['from'][0] <= x - 15 + .5 <= e['to'][0] and e['from'][1] <= 91 - y - .5 <= e['to'][1] for e in flat))
    glow = sum(1 for e in E if e['name'].endswith('_glow'))
    flag = ' <-- CHECK' if ov or ear or horn or miss else ''
    fails += bool(flag)
    print(f"{name:15s} cubes {len(E):3d} glow {glow}  overlaps {len(ov)} ear {ear} horn {horn} eye-pixels-uncovered {miss}{flag}")
    if ov:
        print('   ', ov[:6])
print('checks to look at:', fails)

# ---------- renders from the showcase itself
sc = json.load(open(OUT + 'eyes_showcase.bbmodel', encoding='utf8'))
members = json.load(open('eye_members.json'))
all_ids = {e['uuid'] for e in sc['elements']}
tex = load_tex(sc)
art_dir = A + 'docs/imp-traits/layers/'
base = Image.open(A + 'docs/imp-traits/bodies/body_silver_1870.png').convert('RGBA')
cell_h = 300
cells = []
for name, m in members.items():
    ox, _, oz = m['off']
    hide = all_ids - set(m['ids'])
    beam = 'lazer' in name or 'neon' in name
    art = base.copy()
    art.alpha_composite(Image.open(f'{art_dir}{name}.png').convert('RGBA'))
    art = art.crop((4, 8, 60, 64) if beam else (8, 12, 56, 44)).convert('RGB')
    art = art.resize((int(art.width * cell_h / art.height), cell_h), Image.NEAREST)
    bf = (ox - 44, ox + 44, -6, 106) if beam else (ox - 26, ox + 26, 62, 96)
    ppu = cell_h / (bf[3] - bf[2])
    fr = render_bb.render(sc, tex, FRONT, ppu, bf, hide=hide)
    side_v = SIDE
    bs = (oz - 42, oz + 62, -6, 106) if beam else (oz - 14, oz + 30, 62, 96)
    sd = render_bb.render(sc, tex, SIDE, ppu, bs, hide=hide)
    c = Image.new('RGB', (art.width + fr.width + sd.width + 8, cell_h), (15, 15, 15))
    c.paste(art, (0, 0))
    c.paste(fr, (art.width + 4, 0))
    c.paste(sd, (art.width + fr.width + 8, 0))
    ImageDraw.Draw(c).text((4, 2), name[5:], fill=(255, 255, 0))
    cells.append(c)
os.makedirs('eye_sheets', exist_ok=True)
for page, group in enumerate([cells[:6], cells[6:12], cells[12:]]):
    cols = 2
    w = max(c.width for c in group)
    rows = (len(group) + 1) // 2
    o = Image.new('RGB', (w * cols + 6, (cell_h + 6) * rows), (40, 40, 40))
    for i, c in enumerate(group):
        o.paste(c, ((i % cols) * (w + 6), (i // cols) * (cell_h + 6)))
    o.save(f'eye_sheets/page{page + 1}.png')
    print('page', page + 1, o.size)
render_bb.render(sc, tex, yaw(24, 14), 1.5, (-330, 330, -100, 150)).save('eye_sheets/lineup.png')
