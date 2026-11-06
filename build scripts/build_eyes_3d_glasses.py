"""3D Glasses Eyes trait (implingz_collection.md section 7): a model that sits on the Imp's face.
The shape comes from docs/imp-traits/layers/eyes_3d_glasses.png, scaled to the model's eye band.
Root group is `Head`, same name and pivot as the body's bone, so a customizer can attach it there.
Red lens on the viewer's left (-X), blue on the viewer's right (+X)."""
import base64, copy, io, json, os, uuid
import numpy as np
from PIL import Image
from fix_texture_bleed import pad_file

ASSETS = 'C:/Users/lucas/club-impz/godot-game/assets/'
OUT = 'C:/Users/lucas/blockbench_models/impz/eyes/'
NAME = 'eyes_3d_glasses'
PREVIEW_BODY = 'body_green'
HALF = [  # +X half, top row first. col c covers x in [c, c+1]. F = frame, L = lens
    'FFFFFFFFFFFFFFFF',  # y82
    'FFFFFFFFFFFFFFFF',  # y81
    'FFLLLLLLLLLLLLFF',  # y80
    'FFLLLLLLLLLLLLFF',  # y79
    'FFLLLLLLLLLLLLFF',  # y78
    'FFLLLLLLLLLLLLFF',  # y77
    'FFLLLLLLLLLLLLFF',  # y76
    'FFLLLLLLLLLLLLFF',  # y75
    '.FLLLLLLLLLLLLFF',  # y74  nose notch starts
    '..FLLLLLLLLLLLFF',  # y73
    '...FLLLLLLLLLLF.',  # y72
    '....FLLLLLLLLF..',  # y71
    '.....FFFFFFFF...',  # y70
]
TOP = 83
FACE_Z = 19
FRAME_Z = (18.5, 20.5)   # sunk 0.5 into the face so no coplanar faces fight
LENS_Z = (19, 20)        # recessed 0.5 behind the frame's front
ARM = dict(x=(15, 16), y=(78, 80), z=(5.5, 18.5))
FRAME_RAMP = ['#6e6d72', '#868588', '#b0acab', '#c6c6c5', '#d6d5d2']
LENS_RAMP = {'red': ['#6e1d22', '#8b2a2b', '#aa3a35', '#c2524a', '#e29a88'],
             'blue': ['#14246e', '#2138a6', '#2a49b6', '#4768cf', '#9bb2ee']}


def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], float)


def ramp(t, stops):
    xs = np.linspace(0, 1, len(stops))
    cs = [hx(c) for c in stops]
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, xs, [c[k] for c in cs]) for k in range(3)], -1)


# ---------- shape: full-width material grid, then merge it into few boxes
half = np.array([list(r) for r in HALF])
GRID = np.concatenate([half[:, ::-1], half], 1)  # col 0 = x -16
H, W = GRID.shape
X0 = -16


def merge(mask):
    """Greedy: widest run, then extend down while the row matches."""
    mask = mask.copy()
    out = []
    for r in range(H):
        c = 0
        while c < W:
            if not mask[r, c]:
                c += 1
                continue
            e = c
            while e < W and mask[r, e]:
                e += 1
            b = r + 1
            while b < H and mask[b, c:e].all() and (c == 0 or not mask[b, c - 1]) and (e == W or not mask[b, e]):
                b += 1
            mask[r:b, c:e] = False
            out.append((c, e, r, b))
            c = e
    return out


def dist_to_edge(mask):
    """Chebyshev-free 4-neighbour distance from each cell to the outside of the mask."""
    d = np.where(mask, 99, 0)
    for _ in range(4):
        p = np.pad(d, 1, constant_values=0)
        d = np.where(mask, np.minimum(d, np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]) + 1), 0)
    return d


# ---------- paint the front as one picture, so merged boxes show no seams
Y, Xc = np.mgrid[0:H, 0:W]
v = (Y + .5) / H
h = (Xc + .5) / W
frame = GRID == 'F'
lens = GRID == 'L'
de = dist_to_edge(frame)
t = .70 - .26 * v - .10 * h + np.where(de >= 2, .10, 0) - np.where(de == 1, .06, 0)
FRONT_MAP = ramp(t, FRAME_RAMP)
for colour, side in (('red', Xc < W // 2), ('blue', Xc >= W // 2)):
    m = lens & side
    ys, xs = np.where(m)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    lx, ly = (Xc + .5 - x0) / (x1 - x0), (Y + .5 - y0) / (y1 - y0)
    d = dist_to_edge(m)
    # lighter centre, dark under the frame's top lip, and one soft sheen across the upper left
    tt = .50 - .18 * np.abs(lx - .5) * 2 + .10 * ly - np.where(Y == y0, .24, 0) - np.where(d == 1, .06, 0)
    tt = tt + .26 * np.exp(-((lx + ly * .75 - .55) / .13) ** 2) * np.clip(1.15 - ly * 1.1, 0, 1)
    FRONT_MAP = np.where(m[..., None], ramp(tt, LENS_RAMP[colour]), FRONT_MAP)


def side_paint(w, h_, kind):
    """Frame edges: top catches the light, underside is darkest, sides between."""
    base = {'up': .92, 'east': .46, 'west': .60, 'north': .40, 'south': .62, 'down': .22}[kind]
    yy, xx = np.mgrid[0:h_, 0:w]
    grad = -.10 * (yy + .5) / h_ + .05 * (1 - np.abs((xx + .5) / w - .5) * 2)
    return ramp(base + grad, FRAME_RAMP)


# ---------- cubes
cubes = []
for c, e, r, b in merge(frame):
    cubes.append(dict(kind='frame', fr=[X0 + c, TOP - b, FRAME_Z[0]], to=[X0 + e, TOP - r, FRAME_Z[1]], crop=(c, e, r, b)))
for c, e, r, b in merge(lens):
    colour = 'red' if c < W // 2 else 'blue'
    cubes.append(dict(kind='lens_' + colour, fr=[X0 + c, TOP - b, LENS_Z[0]], to=[X0 + e, TOP - r, LENS_Z[1]], crop=(c, e, r, b)))
for side, sx in (('l', 1), ('r', -1)):
    x = sorted((sx * ARM['x'][0], sx * ARM['x'][1]))
    cubes.append(dict(kind='arm_' + side, fr=[x[0], ARM['y'][0], ARM['z'][0]], to=[x[1], ARM['y'][1], ARM['z'][1]], crop=None))


def uid(s):
    return str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/eyes/3d_glasses/' + s))


# which faces exist, and their pixels
FACE_SIZE = {'north': (0, 1), 'south': (0, 1), 'east': (2, 1), 'west': (2, 1), 'up': (0, 2), 'down': (0, 2)}
requests = []
for i, c in enumerate(cubes):
    size = [int(round(b - a)) for a, b in zip(c['fr'], c['to'])]
    c['size'] = size
    if c['kind'].startswith('lens'):
        wanted = ['south']                     # its edges sit inside the frame, its back on the face
    elif c['kind'] == 'frame':
        wanted = ['south', 'east', 'west', 'up', 'down']  # the back is against the face
    else:
        wanted = ['north', 'south', 'east', 'west', 'up', 'down']
    for fn in wanted:
        a, b = FACE_SIZE[fn]
        w, h_ = size[a], size[b]
        if fn == 'south' and c['crop']:
            ce, cf, cr, cb = c['crop']
            px = FRONT_MAP[cr:cb, ce:cf]
        else:
            px = side_paint(w, h_, fn)
        requests.append((i, fn, w, h_, px))

# shelf-pack, tallest first, with a 1 px gap
requests.sort(key=lambda q: (-q[3], -q[2]))
TEX = 64
atlas = np.zeros((TEX, TEX, 4), np.uint8)
x = y = shelf = 0
uvs = {}
for i, fn, w, h_, px in requests:
    if x + w > TEX:
        x, y, shelf = 0, y + shelf + 1, 0
    assert y + h_ <= TEX, 'texture too small'
    atlas[y:y + h_, x:x + w, :3] = np.clip(px, 0, 255).round().astype(np.uint8)
    atlas[y:y + h_, x:x + w, 3] = 255
    uvs[i, fn] = [x, y, x + w, y + h_]
    x += w + 1
    shelf = max(shelf, h_)
print('texture', TEX, 'used height', y + shelf, 'cubes', len(cubes))


# ---------- bbmodel, built from the body's own file so format fields stay identical
def data_url(im):
    b = io.BytesIO()
    Image.fromarray(im).save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


body = json.load(open(ASSETS + f'models/impz/bodies/{PREVIEW_BODY}.bbmodel', encoding='utf8'))
TEMPLATE = {k: v for k, v in body['elements'][0].items() if k not in ('name', 'from', 'to', 'origin', 'rotation', 'faces', 'uuid')}
TEMPLATE['autouv'] = 0
TEMPLATE['stretch'] = [1, 1, 1]
HEAD = next(g for g in body['groups'] if g['name'] == 'Head')
counts = {}


def cube_json(i, c, uoff=0, utex=0, tag=''):
    k = c['kind'].split('_')
    if c['kind'] == 'frame':
        counts[tag + 'f'] = counts.get(tag + 'f', 0) + 1
        name = f"frame_{counts[tag + 'f']}"
    elif k[0] == 'lens':
        counts[tag + k[1]] = counts.get(tag + k[1], 0) + 1
        name = f"lens_{k[1]}_{counts[tag + k[1]]}"
    else:
        name = c['kind']
    faces = {}
    for fn in ('north', 'east', 'south', 'west', 'up', 'down'):
        a, b = FACE_SIZE[fn]
        if (i, fn) in uvs:
            u1, v1, u2, v2 = uvs[i, fn]
            faces[fn] = {'uv': [u1 + uoff, v1, u2 + uoff, v2], 'texture': utex}
        else:
            faces[fn] = {'uv': [0, 0, c['size'][a], c['size'][b]], 'texture': None}
    e = copy.deepcopy(TEMPLATE)
    e.update({'name': name, 'from': c['fr'], 'to': c['to'], 'autouv': 0, 'origin': [(p + q) / 2 for p, q in zip(c['fr'], c['to'])],
              'faces': faces, 'type': 'cube', 'uuid': uid(tag + name)})
    e['color'] = 2 if c['kind'] == 'frame' else (0 if 'red' in c['kind'] else 4 if 'blue' in c['kind'] else 2)
    return e


def group_json(name, uuid_, children=None):
    g = copy.deepcopy(HEAD)
    g.update(name=name, uuid=uuid_, children=[])
    return g


os.makedirs(OUT, exist_ok=True)
# the trait on its own
elements = [cube_json(i, c) for i, c in enumerate(cubes)]
trait = copy.deepcopy(body)
head_id, trait_id = uid('group/Head'), uid('group/' + NAME)
trait.update(name=NAME, elements=elements, groups=[group_json('Head', head_id), group_json(NAME, trait_id)])
trait['outliner'] = [{'uuid': head_id, 'isOpen': True, 'children': [{'uuid': trait_id, 'isOpen': True, 'children': [e['uuid'] for e in elements]}]}]
t = trait['textures'][0]
t.pop('relative_path', None)
t.update(name=NAME + '.png', internal=True, source=data_url(atlas), width=TEX, height=TEX, uv_width=TEX, uv_height=TEX, uuid=uid('texture'))
Image.fromarray(atlas).save(OUT + NAME + '.png')
with open(OUT + NAME + '.bbmodel', 'w', encoding='utf8', newline='') as fh:
    json.dump(trait, fh, separators=(',', ':'))
# 2 px gaps and a 1 px border of each face's own colour, so cube edges don't sample the gutter
pad_file(OUT + NAME + '.bbmodel', [OUT + NAME + '.png'])

# preview: the same cubes inside the body's real Head bone, on one stitched texture
prev = copy.deepcopy(body)
body_tex = np.array(Image.open(ASSETS + f'textures/impz/bodies/{PREVIEW_BODY}.png').convert('RGBA'))
stitched = np.zeros((256, 512, 4), np.uint8)
stitched[:256, :256] = body_tex
stitched[:TEX, 256:256 + TEX] = atlas
counts.clear()
pe = [cube_json(i, c, uoff=256, tag='p/') for i, c in enumerate(cubes)]
prev['elements'] += pe
pg_id = uid('p/group')
prev['groups'].append(group_json(NAME, pg_id))


def add(nodes):
    for n in nodes:
        if isinstance(n, dict):
            if n['uuid'] == HEAD['uuid']:
                n['children'].append({'uuid': pg_id, 'isOpen': True, 'children': [e['uuid'] for e in pe]})
            add(n.get('children', []))


add(prev['outliner'])
pn = NAME + '_on_body'
prev['name'] = pn
pt = prev['textures'][0]
pt.pop('relative_path', None)
pt.update(name=pn + '.png', internal=True, source=data_url(stitched), width=512, height=256, uv_width=512, uv_height=256, uuid=uid('p/texture'))
Image.fromarray(stitched).save(OUT + pn + '.png')
json.dump(prev, open(OUT + pn + '.bbmodel', 'w', encoding='utf8', newline=''), separators=(',', ':'))
