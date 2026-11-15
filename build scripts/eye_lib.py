"""Shared toolkit for the Imp's Eyes traits. A trait is a list of cubes painted at 1 px per unit (same as the bodies).
Shapes are drawn as cell masks on the front of the face, merged into few boxes, and painted as one picture so the
merged boxes show no seams. Root group is `Head`, same name and pivot as the body's bone."""
import base64, copy, io, json, os, uuid
import numpy as np
from PIL import Image
from fix_texture_bleed import pad_file

ASSETS = 'C:/Users/lucas/club-impz/godot-game/assets/'
OUT = 'C:/Users/lucas/blockbench_models/impz/eyes/'
BODY = json.load(open(ASSETS + 'models/impz/bodies/body_green.bbmodel', encoding='utf8'))
TEMPLATE = {k: v for k, v in BODY['elements'][0].items() if k not in ('name', 'from', 'to', 'origin', 'rotation', 'faces', 'uuid')}
TEMPLATE['autouv'] = 0
TEMPLATE['stretch'] = [1, 1, 1]   # the body cube's 0.98 would shrink every trait cube and open seams
HEAD = next(g for g in BODY['groups'] if g['name'] == 'Head')

GX0, GX1, GY0, GY1 = -30, 30, 60, 96
W, H = GX1 - GX0, GY1 - GY0
Yi, Xi = np.mgrid[0:H, 0:W]
CX = GX0 + Xi + .5   # cell centres, model units
CY = GY1 - Yi - .5
AX = np.abs(CX)
FACE_SIZE = {'north': (0, 1), 'south': (0, 1), 'east': (2, 1), 'west': (2, 1), 'up': (0, 2), 'down': (0, 2)}
ALL_FACES = ('north', 'east', 'south', 'west', 'up', 'down')


def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], float)


def ramp(t, stops):
    xs = np.linspace(0, 1, len(stops))
    cs = [hx(c) for c in stops]
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, xs, [c[k] for c in cs]) for k in range(3)], -1)


def neighbours(m):
    p = np.pad(m, 1)
    return p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]


def dilate(m, n=1):
    for _ in range(n):
        a, b, c, d = neighbours(m)
        m = m | a | b | c | d
    return m


def erode(m, n=1):
    for _ in range(n):
        a, b, c, d = neighbours(m)
        m = m & a & b & c & d
    return m


def dist_to_edge(mask, n=5):
    d = np.where(mask, 99, 0)
    for _ in range(n):
        p = np.pad(d, 1)
        d = np.where(mask, np.minimum(d, np.minimum.reduce([p[:-2, 1:-1], p[2:, 1:-1], p[1:-1, :-2], p[1:-1, 2:]]) + 1), 0)
    return d


def merge(mask):
    """Greedy: take the widest run on a row, then extend it down while the next rows match exactly."""
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


def norm_coords(mask):
    ys, xs = np.where(mask)
    x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
    return (Xi + .5 - x0) / (x1 - x0), (Yi + .5 - y0) / (y1 - y0)


def frame_tone(mask, base=.70, drop=.26, side=.10):
    """Top lit, lit side on the viewer's left, centres a touch lighter, soft fall-off at the edge. No dark rim."""
    lx, ly = norm_coords(mask)
    de = dist_to_edge(mask)
    return base - drop * ly - side * lx + np.where(de >= 2, .10, 0) - np.where(de == 1, .06, 0)


def lens_tone(mask, base=.50, shine=.26, lip=.24):
    """Per eye: lighter centre, dark under the frame's lip, one soft sheen across the upper left. As the 3D Glasses."""
    tone = np.zeros(mask.shape)
    for side in (CX < 0, CX >= 0):
        m = mask & side
        if not m.any():
            continue
        lx, ly = norm_coords(m)
        ys = np.where(m)[0]
        d = dist_to_edge(m)
        t = base - .18 * np.abs(lx - .5) * 2 + .10 * ly - np.where(d == 1, .06, 0)
        t = t - np.where(Yi == ys.min(), lip, 0)
        t = t + shine * np.exp(-((lx + ly * .75 - .55) / .13) ** 2) * np.clip(1.15 - ly * 1.1, 0, 1)
        tone = np.where(m, t, tone)
    return tone


def side_paint(w, h, kind, stops, alpha=255):
    base = {'up': .92, 'east': .46, 'west': .60, 'north': .40, 'south': .62, 'down': .22}[kind]
    yy, xx = np.mgrid[0:h, 0:w]
    t = base - .10 * (yy + .5) / h + .05 * (1 - np.abs((xx + .5) / w - .5) * 2)
    return ramp(t, stops), np.full((h, w), alpha)


class Trait:
    def __init__(self, name):
        self.name, self.cubes, self.count = name, [], {}

    def _uname(self, base, glow):
        self.count[base] = self.count.get(base, 0) + 1
        return f"{base}_{self.count[base]}" + ('_glow' if glow else '')

    def layer(self, name, mask, z, stops, tone=None, alpha=255, sides=True, back=False, glow=False, group=None, rgb=None):
        """A shape on the face plane. z is (back, front). Side pixels hidden against a neighbour in this layer are left
        out (transparent), so they can't show through a see-through lens; a face with nothing exposed gets no UV."""
        assert mask.any(), name
        if rgb is None:
            rgb = ramp(frame_tone(mask) if tone is None else tone, stops)
        al = np.full(mask.shape, alpha) if np.isscalar(alpha) else alpha
        side_alpha = alpha if np.isscalar(alpha) else 255
        depth = int(z[1] - z[0])
        for c, e, r, b in merge(mask):
            px = {'south': (rgb[r:b, c:e], al[r:b, c:e])}
            wanted = ['south'] + (['north'] if back else [])
            if sides:
                exposed = {'up': ~mask[r - 1, c:e] if r > 0 else np.ones(e - c, bool),
                           'down': ~mask[b, c:e] if b < H else np.ones(e - c, bool),
                           'east': ~mask[r:b, e] if e < W else np.ones(b - r, bool),
                           'west': ~mask[r:b, c - 1] if c > 0 else np.ones(b - r, bool)}
                for fn, ex in exposed.items():
                    if not ex.any():
                        continue
                    wanted.append(fn)
                    w_, h_ = (e - c, depth) if fn in ('up', 'down') else (depth, b - r)
                    col, a_ = side_paint(w_, h_, fn, stops, side_alpha)
                    a_ = a_ * (ex[None, :] if fn in ('up', 'down') else ex[:, None])
                    px[fn] = (col, a_)
            self.cubes.append(dict(name=self._uname(name, glow), fr=[GX0 + c, GY1 - b, z[0]], to=[GX0 + e, GY1 - r, z[1]],
                                   rot=None, origin=None, wanted=wanted, stops=stops, px=px, alpha=side_alpha, group=group))

    def plate(self, name, rim, lens, z, rim_stops, lens_stops, rim_tone=None, lens_tone_=None, lens_alpha=255):
        """Rim and lens as ONE silhouette with the rim painted on: keeps curved shapes within the cube budget."""
        rgb = np.where(lens[..., None], ramp(lens_tone(lens) if lens_tone_ is None else lens_tone_, lens_stops),
                       ramp(frame_tone(rim) if rim_tone is None else rim_tone, rim_stops))
        self.layer(name, rim | lens, z, rim_stops, rgb=rgb, alpha=np.where(lens, lens_alpha, 255))

    def box(self, name, fr, to, stops, rot=None, origin=None, wanted=ALL_FACES, alpha=255, paint=None, group=None, glow=False):
        """A free cube. paint(w, h, face) may return (rgb, alpha)."""
        self.cubes.append(dict(name=name + ('_glow' if glow else ''), fr=list(fr), to=list(to), rot=rot, origin=origin, wanted=list(wanted),
                               stops=stops, px={}, alpha=alpha, paint=paint, group=group))

    def arms(self, stops, y=(78, 80), x=(15, 16), z=(5.5, 18.5), name='arm'):
        """Run back along the head and stop before the ears, as on the 3D Glasses."""
        self.box(name + '_l', (x[0], y[0], z[0]), (x[1], y[1], z[1]), stops)
        self.box(name + '_r', (-x[1], y[0], z[0]), (-x[0], y[1], z[1]), stops)

    def build(self):
        reqs = []
        for i, c in enumerate(self.cubes):
            size = [b - a for a, b in zip(c['fr'], c['to'])]
            assert all(float(s).is_integer() and s > 0 for s in size), (self.name, c['name'], size)
            c['size'] = [int(s) for s in size]
            for fn in c['wanted']:
                a, b = FACE_SIZE[fn]
                w, h = c['size'][a], c['size'][b]
                if fn in c['px']:
                    rgb, al = c['px'][fn]
                elif c.get('paint'):
                    rgb, al = c['paint'](w, h, fn)
                else:
                    rgb, al = side_paint(w, h, fn, c['stops'], c['alpha'])
                reqs.append((i, fn, w, h, rgb, al))
        reqs.sort(key=lambda q: (-q[3], -q[2]))
        for size in (64, 128, 256):
            atlas = np.zeros((size, size, 4), np.uint8)
            x = y = shelf = 0
            uvs = {}
            ok = True
            for i, fn, w, h, rgb, al in reqs:
                if x + w > size:
                    x, y, shelf = 0, y + shelf + 1, 0
                if y + h > size or w > size:
                    ok = False
                    break
                atlas[y:y + h, x:x + w, :3] = np.clip(rgb, 0, 255).round().astype(np.uint8)
                atlas[y:y + h, x:x + w, 3] = np.clip(al, 0, 255).astype(np.uint8)
                uvs[i, fn] = [x, y, x + w, y + h]
                x += w + 1
                shelf = max(shelf, h)
            if ok:
                return atlas, uvs, size
        raise ValueError('texture too small: ' + self.name)

    def uid(self, s):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f'club-impz/eyes/{self.name}/{s}'))

    def save(self):
        atlas, uvs, size = self.build()
        elements = []
        for i, c in enumerate(self.cubes):
            faces = {}
            for fn in ALL_FACES:
                a, b = FACE_SIZE[fn]
                if (i, fn) in uvs:
                    faces[fn] = {'uv': uvs[i, fn], 'texture': 0}
                else:
                    faces[fn] = {'uv': [0, 0, c['size'][a], c['size'][b]], 'texture': None}
            e = copy.deepcopy(TEMPLATE)
            origin = c['origin'] or [(p + q) / 2 for p, q in zip(c['fr'], c['to'])]
            e.update({'name': c['name'], 'from': [round(v, 5) for v in c['fr']], 'to': [round(v, 5) for v in c['to']], 'origin': [round(v, 5) for v in origin],
                      'faces': faces, 'type': 'cube', 'uuid': self.uid(c['name'])})
            if c['rot']:
                e['rotation'] = [round(v, 3) for v in c['rot']]
            elements.append(e)
        names = [e['name'] for e in elements]
        assert len(names) == len(set(names)), self.name
        d = copy.deepcopy(BODY)

        def group(name):
            g = copy.deepcopy(HEAD)
            g.update(name=name, uuid=self.uid('group/' + name), children=[])
            return g

        extra = sorted({c['group'] for c in self.cubes if c['group']})
        d['groups'] = [group('Head'), group(self.name)] + [group(g) for g in extra]
        kids = [e['uuid'] for e, c in zip(elements, self.cubes) if not c['group']]
        kids += [{'uuid': self.uid('group/' + g), 'isOpen': True, 'children': [e['uuid'] for e, c in zip(elements, self.cubes) if c['group'] == g]} for g in extra]
        d['outliner'] = [{'uuid': self.uid('group/Head'), 'isOpen': True, 'children': [{'uuid': self.uid('group/' + self.name), 'isOpen': True, 'children': kids}]}]
        d.update(name=self.name, elements=elements)
        b = io.BytesIO()
        Image.fromarray(atlas).save(b, 'PNG', optimize=True)
        d['textures'][0].pop('relative_path', None)
        d['textures'][0].update(name=self.name + '.png', internal=True, source='data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(),
                                width=size, height=size, uv_width=size, uv_height=size, uuid=self.uid('texture'))
        os.makedirs(OUT, exist_ok=True)
        Image.fromarray(atlas).save(OUT + self.name + '.png')
        with open(OUT + self.name + '.bbmodel', 'w', encoding='utf8', newline='') as f:
            json.dump(d, f, separators=(',', ':'))
        # 2 px gaps and a 1 px border of each face's own colour, so cube edges don't sample the gutter
        pad_file(OUT + self.name + '.bbmodel', [OUT + self.name + '.png'])
        print(f'{self.name:22s} {len(elements):3d} cubes  {size}px texture')
        return json.load(open(OUT + self.name + '.bbmodel', encoding='utf8'))  # as padded
