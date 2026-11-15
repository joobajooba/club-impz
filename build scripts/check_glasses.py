import json, itertools
import numpy as np
from PIL import Image
from render_bb import load_tex, render, cube_world, FRONT, SIDE, yaw

OUT = 'C:/Users/lucas/blockbench_models/impz/eyes/'
A = 'C:/Users/lucas/club-impz/'
t = json.load(open(OUT + 'eyes_3d_glasses.bbmodel', encoding='utf8'))
p = json.load(open(OUT + 'eyes_3d_glasses_on_body.bbmodel', encoding='utf8'))
body = json.load(open(A + 'godot-game/assets/models/impz/bodies/body_green.bbmodel', encoding='utf8'))
E = t['elements']
print('cubes', len(E), [e['name'] for e in E])

# 1. integer sizes, unique uuids, body untouched in preview
for e in E:
    s = [b - a for a, b in zip(e['from'], e['to'])]
    assert all(float(v).is_integer() and v > 0 for v in s), e['name']
ids = [e['uuid'] for e in p['elements']] + [g['uuid'] for g in p['groups']]
assert len(ids) == len(set(ids))
assert p['elements'][:27] == body['elements'], 'preview altered the body'
assert t['groups'][0]['name'] == 'Head' and t['groups'][0]['origin'] == next(g for g in body['groups'] if g['name'] == 'Head')['origin']

# 2. mirror
geo = {(tuple(e['from']), tuple(e['to'])) for e in E}
for e in E:
    assert ((-e['to'][0], e['from'][1], e['from'][2]), (-e['from'][0], e['to'][1], e['to'][2])) in geo, e['name']
print('mirrored shape: yes')

# 3. no two cubes overlap (z-fighting / poke-through), except nothing allowed
def overlap(a, b):
    return all(min(a['to'][k], b['to'][k]) - max(a['from'][k], b['from'][k]) > 1e-6 for k in range(3))
bad = [(a['name'], b['name']) for a, b in itertools.combinations(E, 2) if overlap(a, b)]
print('overlapping cubes:', bad)

# 4. eyes fully covered: every white eye texel on the head front must be behind frame or lens
T = np.array(Image.open(A + 'godot-game/assets/textures/impz/bodies/body_green.png').convert('RGB')).astype(int)
face = T[29:57, 0:30]
ys, xs = np.where(face.min(-1) > 150)
miss = 0
for y, x in zip(ys, xs):
    wx, wy = x - 15 + .5, 91 - y - .5
    if not any(e['from'][0] <= wx <= e['to'][0] and e['from'][1] <= wy <= e['to'][1] for e in E if not e['name'].startswith('arm')):
        miss += 1
print('eye-white texels', len(ys), 'left uncovered', miss)
dark = np.where((face.sum(-1) < 200))
print('dark brow/pupil rows on head, model y:', 91 - dark[0].max() - 1, 'to', 91 - dark[0].min())

# 5. arms clear of the ears, against the head
W = cube_world(body)
Tb, _, _ = load_tex(body)
for uid8 in ('fc7c5ec5', '2e79580e'):
    ear = next(e for e in body['elements'] if e['uuid'].startswith(uid8))
    M = W[ear['uuid']]
    u1, v1, u2, v2 = ear['faces']['south']['uv']
    a, c = ear['from'], ear['to']
    pts = []
    for i in range(211):
        for j in range(141):
            s, q = i / 210, j / 140
            if Tb[min(255, int(v1 + (v2 - v1) * q)), min(255, int(u1 + (u2 - u1) * s)), 3] > 32:
                pts.append(M @ np.array([a[0] + s * (c[0] - a[0]), c[1] - q * (c[1] - a[1]), a[2], 1]))
    pts = np.array(pts)
    n = sum(int(((pts[:, :3] >= np.array(e['from'])) & (pts[:, :3] <= np.array(e['to']))).all(1).sum()) for e in E)
    print('ear', uid8, 'samples inside glasses:', n)
horns = [e for e in body['elements'] if e['name'].startswith('horn_')]
print('horn lowest y', round(min(e['from'][1] for e in horns), 1), '(glasses top y=83; horn roots sit inside the skull)')

# 6. renders next to the art
tex = load_tex(p)
art = Image.open(A + 'docs/imp-traits/layers/eyes_3d_glasses.png').convert('RGBA')
nft = Image.open(A + 'docs/imp-traits/bodies/body_silver_1870.png').convert('RGBA')
nft.alpha_composite(art)
H = 560
nft = nft.convert('RGB').resize((H, H), Image.NEAREST)
bd = (-40, 40, 52, 112)
ppu = H / (bd[3] - bd[2])
sb = (-30, 40, 52, 112)
ims = [nft, render(p, tex, FRONT, ppu, bd), render(p, tex, SIDE, ppu, sb), render(p, tex, yaw(35, 10), ppu, bd)]
o = Image.new('RGB', (sum(i.width for i in ims) + 18, H), (15, 15, 15))
x = 0
for i in ims:
    o.paste(i, (x, 0))
    x += i.width + 6
o.save('glasses_check.png')
print(o.size)
tt = load_tex(t)
render(t, tt, FRONT, 20, (-18, 18, 67, 86)).save('glasses_zoom.png')
Image.open(OUT + 'eyes_3d_glasses.png').resize((384, 384), Image.NEAREST).save('glasses_tex.png')
