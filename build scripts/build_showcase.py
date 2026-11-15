"""All ten Imps in one file: stitched 1024 atlas, each Imp under its own root group. Then validate the set."""
import json, copy, uuid
import numpy as np
from PIL import Image
from build_imp_bodies import main, ORDER, OUT, REPO, FLAT, GOLD, ICE, hx, data_url, texture_entry, save, base_texture
import base64, io
from fix_texture_bleed import strip_uv
from render_bb import load_tex, render, FRONT, yaw

base, texes = main()
TILE, COLS = 256, 4
atlas = np.zeros((1024, 1024, 4), np.uint8)
SPACE_X, SPACE_Z = 72, 110
FIRST_ROW = 5


def uid(tag, old):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, f'club-impz/showcase/{tag}/{old}'))


def place(i):
    row = 0 if i < FIRST_ROW else 1
    col = i - FIRST_ROW * row
    # front row nearest the viewer (+Z is the front), back row staggered so nobody is hidden
    return (col - 2) * SPACE_X + (SPACE_X / 2 if row else 0) - SPACE_X / 4, 0, (55 if row == 0 else -55)


def shift(p, off):
    return [round(a + b, 5) for a, b in zip(p, off)]


out = copy.deepcopy(base)
out.update(name='imp_bodies_showcase', elements=[], groups=[], outliner=[])
for i, n in enumerate(ORDER):
    tu, tv = (i % COLS) * TILE, (i // COLS) * TILE
    atlas[tv:tv + TILE, tu:tu + TILE] = texes[n]
    off = place(i)
    for e in base['elements']:
        c = copy.deepcopy(e)
        c['uuid'] = uid(n, e['uuid'])
        c['from'], c['to'], c['origin'] = shift(e['from'], off), shift(e['to'], off), shift(e['origin'], off)
        for f in c['faces'].values():
            u1, v1, u2, v2 = f['uv']
            f['uv'] = [u1 + tu, v1 + tv, u2 + tu, v2 + tv]
        out['elements'].append(c)
    for g in base['groups']:
        c = copy.deepcopy(g)
        c['uuid'] = uid(n, g['uuid'])
        c['origin'] = shift(g['origin'], off)
        c['name'] = f'{n}_imp' if g['name'] == 'Origin' else f"{g['name']}_{n}"
        out['groups'].append(c)

    def walk(node):
        if isinstance(node, str):
            return uid(n, node)
        c = copy.deepcopy(node)
        c['uuid'] = uid(n, node['uuid'])
        c['children'] = [walk(k) for k in node.get('children', [])]
        c['isOpen'] = False
        return c

    out['outliner'] += [walk(k) for k in base['outliner']]

fn = 'imp_bodies_showcase'
texture_entry(out, fn, atlas)
out['textures'][0].update(width=1024, height=1024, uv_width=1024, uv_height=1024)
Image.fromarray(atlas).save(OUT + fn + '.png')
save(out, fn, pad=False)  # a view-only sheet on the working folder, not a game model

# ---------- validation
src = base_texture()
padded = json.load(open(REPO + 'models/impz/green_imp.bbmodel', encoding='utf8'))
geo = lambda d: [(e['uuid'], e['name'], e['from'], e['to'], e['origin'], e.get('rotation'), e['faces']) for e in d['elements']]
for n in ORDER:
    d = json.load(open(OUT + n + '_imp.bbmodel', encoding='utf8'))
    # saved bodies are padded (uv_padding.py): same rig as base, same UVs as the committed green_imp
    assert strip_uv(d)['elements'] == strip_uv(base)['elements'] and d['outliner'] == base['outliner'] and d['groups'] == base['groups'], n
    assert geo(d) == geo(padded), n + ': UV layout differs from the committed green_imp'
    t = texes[n]
    assert (t[..., 3] == src[..., 3]).all(), n
    emb = np.array(Image.open(io.BytesIO(base64.b64decode(d['textures'][0]['source'].split(',', 1)[1]))).convert('RGBA'))
    assert np.array_equal(np.array(Image.open(OUT + n + '_imp.png').convert('RGBA')), emb), n
    main_c = hx(FLAT[n][0]) if n in FLAT else hx(GOLD[4] if n == 'gold' else ICE[4])
    near = (np.abs(t[..., :3].astype(float) - main_c).max(-1) <= 6) & (t[..., 3] > 32)
    op = t[t[..., 3] > 32][:, :3]
    print(f"{n:8s} main-colour texels {int(near.sum()):6d}  pure white {int((op == 255).all(1).sum()):3d}  pure black {int((op == 0).all(1).sum()):3d}  tones {len(np.unique(op, axis=0))}")
sc = json.load(open(OUT + fn + '.bbmodel', encoding='utf8'))
ids = [e['uuid'] for e in sc['elements']] + [g['uuid'] for g in sc['groups']]
assert len(ids) == len(set(ids))
names = [g['name'] for g in sc['groups']]
assert len(names) == len(set(names))
print('showcase cubes', len(sc['elements']), 'groups', len(sc['groups']), 'roots', [r['uuid'][:4] and sc['groups'][0]['name'] for r in sc['outliner']][:1], 'uids unique, group names unique')
# renders
tex = load_tex(sc)
render(sc, tex, yaw(0), 2, (-230, 230, -4, 112)).save(OUT + 'showcase_front.png')
render(sc, tex, yaw(28, 16), 2, (-250, 250, -60, 120)).save(OUT + 'showcase_q.png')
# NFT next to each model, for the side-by-side check
cells = []
for n in ORDER:
    art = {'green': 'green_53', 'red': 'red_1083', 'blue': 'blue_275', 'cyan': 'cyan_111', 'purple': 'purple_1095', 'pink': 'pink_442',
           'khaki': 'khaki_371', 'silver': 'silver_1870', 'gold': 'gold_408', 'diamond': 'diamond_158'}[n]
    a = Image.open(f'{REPO}../../docs/imp-traits/bodies/body_{art}.png').convert('RGB').resize((192, 192), Image.NEAREST)
    d = json.load(open(OUT + n + '_imp.bbmodel', encoding='utf8'))
    m = render(d, load_tex(d), FRONT, 2.6, (-36, 36, -2, 72 + 34))
    m = m.resize((int(m.width * 192 / m.height), 192))
    c = Image.new('RGB', (192 + m.width + 4, 192), (15, 15, 15))
    c.paste(a, (0, 0))
    c.paste(m, (196, 0))
    cells.append(c)
W, H = cells[0].size
sheet = Image.new('RGB', (W * 3 + 8, H * 4 + 12), (15, 15, 15))
for i, c in enumerate(cells):
    sheet.paste(c, ((i % 3) * (W + 4), (i // 3) * (H + 4)))
sheet.save(OUT + 'imp_bodies_vs_nft.png')
print(sheet.size)
