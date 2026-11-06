"""All 19 Eyes traits in one file: one green Imp per trait, in lineup order, on one stitched 1024 texture.
Overlays are composited into that Imp's copy of the body texture. Model traits sit inside that Imp's real Head bone."""
import base64, copy, io, json, uuid
import numpy as np
from PIL import Image
from eye_lib import ASSETS, OUT

BODY = json.load(open(ASSETS + 'models/impz/bodies/body_green.bbmodel', encoding='utf8'))
BODY_TEX = np.array(Image.open(ASSETS + 'textures/impz/bodies/body_green.png').convert('RGBA'))
# trait, its model (or None), its overlay (or None)
LINEUP = [
    ('eyes_red_pupils', None, 'eyes_red_pupils'), ('eyes_gold_pupils', None, 'eyes_gold_pupils'), ('eyes_purple_pupils', None, 'eyes_purple_pupils'),
    ('eyes_ghostly', None, 'eyes_ghostly'), ('eyes_3d_glasses', 'eyes_3d_glasses', None), ('eyes_shades', 'eyes_shades', None),
    ('eyes_bug_eye', 'eyes_bug_eye', None), ('eyes_glasses', 'eyes_glasses', None), ('eyes_hearts', 'eyes_hearts', None), ('eyes_stars', 'eyes_stars', None),
    ('eyes_goggles', 'eyes_goggles', None), ('eyes_mask', 'eyes_mask', None), ('eyes_robo', 'eyes_robo', None),
    ('eyes_eye_patch', 'eyes_eye_patch', 'eyes_red_pupils'), ('eyes_monacle', 'eyes_monacle', 'eyes_red_pupils'),
    ('eyes_tracker_blue', 'eyes_tracker_blue', 'eyes_red_pupils'), ('eyes_tracker_purple', 'eyes_tracker_purple', 'eyes_red_pupils'),
    ('eyes_lazer', 'eyes_lazer', 'eyes_lazer_glow'), ('eyes_neon_beam', 'eyes_neon_beam', 'eyes_neon_beam_glow'),
]
ROWS = [7, 6, 6]
SPACE_X, SPACE_Z = 78, 125


def uid(*p):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/eyes/showcase/' + '/'.join(p)))


def shift(p, off):
    return [round(a + b, 5) for a, b in zip(p, off)]


def place(i):
    r = 0
    while i >= ROWS[r]:
        i -= ROWS[r]
        r += 1
    return (i - (ROWS[r] - 1) / 2 + (0, -.25, .25)[r]) * SPACE_X, 0, (1 - r) * SPACE_Z   # staggered, so no Imp hides another from the front


def overlaid(ov):
    im = Image.fromarray(BODY_TEX.copy())
    if ov:
        im.alpha_composite(Image.open(OUT + ov + '.png').convert('RGBA'))
    return np.array(im)


atlas = np.zeros((1024, 1024, 4), np.uint8)
tiles = {}
for _, _, ov in LINEUP:
    if ov not in tiles:
        i = len(tiles)
        tiles[ov] = ((i % 4) * 256, (i // 4) * 256)
        tu, tv = tiles[ov]
        atlas[tv:tv + 256, tu:tu + 256] = overlaid(ov)
print('body tiles', len(tiles))
slot_x, slot_y, row_h = 0, ((len(tiles) + 3) // 4) * 256, 0
trait_slot = {}
for name, model, _ in LINEUP:
    if not model:
        continue
    t = np.array(Image.open(OUT + model + '.png').convert('RGBA'))
    h, w = t.shape[:2]
    if slot_x + w > 1024:
        slot_x, slot_y, row_h = 0, slot_y + row_h, 0
    assert slot_y + h <= 1024, 'atlas full'
    atlas[slot_y:slot_y + h, slot_x:slot_x + w] = t
    trait_slot[model] = (slot_x, slot_y)
    slot_x += w
    row_h = max(row_h, h)

out = copy.deepcopy(BODY)
out.update(name='eyes_showcase', elements=[], groups=[], outliner=[])
members = {}
for i, (name, model, ov) in enumerate(LINEUP):
    off = place(i)
    tu, tv = tiles[ov]
    short = name[5:]
    ids = []
    for e in BODY['elements']:
        c = copy.deepcopy(e)
        c['uuid'] = uid(name, 'b', e['uuid'])
        c['from'], c['to'], c['origin'] = shift(e['from'], off), shift(e['to'], off), shift(e['origin'], off)
        for f in c['faces'].values():
            u1, v1, u2, v2 = f['uv']
            f['uv'] = [u1 + tu, v1 + tv, u2 + tu, v2 + tv]
        out['elements'].append(c)
        ids.append(c['uuid'])
    for g in BODY['groups']:
        c = copy.deepcopy(g)
        c['uuid'] = uid(name, 'b', g['uuid'])
        c['origin'] = shift(g['origin'], off)
        c['name'] = f'{short}_imp' if g['name'] == 'Origin' else f"{g['name']}_{short}"
        out['groups'].append(c)

    extra = None
    if model:
        tr = json.load(open(OUT + model + '.bbmodel', encoding='utf8'))
        su, sv = trait_slot[model]
        for e in tr['elements']:
            c = copy.deepcopy(e)
            c['uuid'] = uid(name, 't', e['uuid'])
            c['from'], c['to'], c['origin'] = shift(e['from'], off), shift(e['to'], off), shift(e['origin'], off)
            for f in c['faces'].values():
                if f.get('texture') is not None:
                    u1, v1, u2, v2 = f['uv']
                    f['uv'] = [u1 + su, v1 + sv, u2 + su, v2 + sv]
            out['elements'].append(c)
            ids.append(c['uuid'])
        sub = {g['uuid']: g for g in tr['groups']}
        for g in tr['groups'][1:]:
            c = copy.deepcopy(g)
            c['uuid'] = uid(name, 't', g['uuid'])
            c['origin'] = shift(c['origin'], off)
            c['name'] = g['name'] if g['name'].startswith('eyes_') else f"{g['name']}_{short}"
            out['groups'].append(c)

        def tw(n):
            if isinstance(n, str):
                return uid(name, 't', n)
            return {'uuid': uid(name, 't', n['uuid']), 'isOpen': False, 'children': [tw(k) for k in n['children']]}
        extra = tw(tr['outliner'][0]['children'][0])

    def walk(n):
        if isinstance(n, str):
            return uid(name, 'b', n)
        c = copy.deepcopy(n)
        c['uuid'] = uid(name, 'b', n['uuid'])
        c['children'] = [walk(k) for k in n.get('children', [])]
        c['isOpen'] = False
        if extra and n['uuid'] == next(g['uuid'] for g in BODY['groups'] if g['name'] == 'Head'):
            c['children'].append(extra)
        return c

    out['outliner'] += [walk(k) for k in BODY['outliner']]
    members[name] = ids

b = io.BytesIO()
Image.fromarray(atlas).save(b, 'PNG', optimize=True)
out['textures'][0].pop('relative_path', None)
out['textures'][0].update(name='eyes_showcase.png', internal=True, source='data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(),
                          width=1024, height=1024, uv_width=1024, uv_height=1024, uuid=uid('texture'))
Image.fromarray(atlas).save(OUT + 'eyes_showcase.png')
with open(OUT + 'eyes_showcase.bbmodel', 'w', encoding='utf8', newline='') as f:
    json.dump(out, f, separators=(',', ':'))
json.dump({k: dict(ids=v, off=place(i)) for i, (k, v) in enumerate(members.items())}, open('eye_members.json', 'w'))
print('showcase', len(out['elements']), 'cubes', len(out['groups']), 'groups, atlas used to y', slot_y + row_h)
