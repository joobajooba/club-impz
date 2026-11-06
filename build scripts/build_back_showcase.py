"""All 11 Back values in one file: one green Imp per value, each item inside that Imp's real bones, on one stitched texture."""
import base64, copy, io, json, uuid
import numpy as np
from PIL import Image
from head_lib import ASSETS
OUT = 'C:/Users/lucas/blockbench_models/impz/back/'

BODY = json.load(open(ASSETS + 'models/impz/bodies/body_green.bbmodel', encoding='utf8'))
BODY_TEX = np.array(Image.open(ASSETS + 'textures/impz/bodies/body_green.png').convert('RGBA'))
LINEUP = ['none', 'imp_wings', 'golden_wings', 'angel_wings', 'bone_wings', 'mechanical_wings', 'cape', 'sword', 'samurai', 'scythe', 'trident']
ROWS = [4, 4, 3]
SPACE_X, SPACE_Z = 135, 150


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/back/showcase/' + '/'.join(p)))


def shift(p, off):
    return [round(a + b, 5) for a, b in zip(p, off)]


def place(i):
    r = 0
    while i >= ROWS[r]:
        i -= ROWS[r]
        r += 1
    return (i - (ROWS[r] - 1) / 2) * SPACE_X, 0, (1 - r) * SPACE_Z


traits = {n: json.load(open(f'{OUT}back_{n}.bbmodel', encoding='utf8')) for n in LINEUP if n != 'none'}
texs = {n: np.array(Image.open(f'{OUT}back_{n}.png').convert('RGBA')) for n in traits}
SIZE = 2048
atlas = np.zeros((SIZE, SIZE, 4), np.uint8)
atlas[:256, :256] = BODY_TEX
x, y, shelf = 256, 0, 256
slot = {}
for n in sorted(traits, key=lambda n: -texs[n].shape[0]):
    h, w = texs[n].shape[:2]
    if x + w > SIZE:
        x, y, shelf = 0, y + shelf, 0
    assert y + h <= SIZE, 'atlas full'
    atlas[y:y + h, x:x + w] = texs[n]
    slot[n] = (x, y)
    x += w
    shelf = max(shelf, h)
print('atlas used to y', y + shelf)

out = copy.deepcopy(BODY)
out.update(name='back_showcase', elements=[], groups=[], outliner=[])
members = {}
body_names = {g['uuid']: g['name'] for g in BODY['groups']}
for i, n in enumerate(LINEUP):
    off = place(i)
    ids = []
    for e in BODY['elements']:
        c = copy.deepcopy(e)
        c['uuid'] = uid(n, 'b', e['uuid'])
        c['from'], c['to'], c['origin'] = shift(e['from'], off), shift(e['to'], off), shift(e['origin'], off)
        out['elements'].append(c)
        ids.append(c['uuid'])
    for g in BODY['groups']:
        c = copy.deepcopy(g)
        c['uuid'] = uid(n, 'b', g['uuid'])
        c['origin'] = shift(g['origin'], off)
        c['name'] = f'{n}_imp' if g['name'] == 'Origin' else f"{g['name']}_{n}"
        out['groups'].append(c)
    extras = {}
    if n != 'none':
        tr = traits[n]
        su, sv = slot[n]
        tr_ids = []
        for e in tr['elements']:
            c = copy.deepcopy(e)
            c['uuid'] = uid(n, 't', e['uuid'])
            c['from'], c['to'], c['origin'] = shift(e['from'], off), shift(e['to'], off), shift(e['origin'], off)
            for f in c['faces'].values():
                if f.get('texture') is not None:
                    u1, v1, u2, v2 = f['uv']
                    f['uv'] = [u1 + su, v1 + sv, u2 + su, v2 + sv]
            out['elements'].append(c)
            tr_ids.append(c['uuid'])
        gm = {g['uuid']: g for g in tr['groups']}

        def collect(node):
            g = gm[node['uuid']]
            for k in node['children']:
                if isinstance(k, str):
                    continue
                if gm[k['uuid']]['name'].startswith(tr['name'] + '_'):     # the group of cubes inside this bone
                    c = copy.deepcopy(gm[k['uuid']])
                    c['uuid'] = uid(n, 't', k['uuid'])
                    c['origin'] = shift(c['origin'], off)
                    out['groups'].append(c)
                    extras.setdefault(g['name'], []).append({'uuid': c['uuid'], 'isOpen': False, 'children': [uid(n, 't', e) for e in k['children']]})
                else:
                    collect(k)
        for root in tr['outliner']:
            collect(root)
        members[n] = dict(ids=ids + tr_ids, off=off, body=list(ids))
    else:
        members[n] = dict(ids=ids, off=off, body=list(ids))

    def walk(node):
        if isinstance(node, str):
            return uid(n, 'b', node)
        c = copy.deepcopy(node)
        c['uuid'] = uid(n, 'b', node['uuid'])
        c['children'] = [walk(k) for k in node.get('children', [])]
        c['isOpen'] = False
        if body_names[node['uuid']] in extras:
            c['children'] += extras[body_names[node['uuid']]]
        return c

    out['outliner'] += [walk(k) for k in BODY['outliner']]

b = io.BytesIO()
Image.fromarray(atlas).save(b, 'PNG', optimize=True)
out['textures'][0].pop('relative_path', None)
out['textures'][0].update(name='back_showcase.png', internal=True, source='data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(),
                          width=SIZE, height=SIZE, uv_width=SIZE, uv_height=SIZE, uuid=uid('texture'))
Image.fromarray(atlas).save(OUT + 'back_showcase.png')
with open(OUT + 'back_showcase.bbmodel', 'w', encoding='utf8', newline='') as f:
    json.dump(out, f, separators=(',', ':'))
json.dump(members, open('back_members.json', 'w'))
ids = [e['uuid'] for e in out['elements']] + [g['uuid'] for g in out['groups']]
names = [g['name'] for g in out['groups']]
assert len(ids) == len(set(ids)) and len(names) == len(set(names)), 'duplicates'
print('showcase', len(out['elements']), 'cubes', len(out['groups']), 'groups')
