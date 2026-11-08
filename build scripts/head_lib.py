"""Toolkit for the Imp's Head traits: free 3D cubes painted in world space at 1 px per unit (same as the bodies).
Stacked cubes share one form-shading function, so they read as one rounded shape. Texels that end up inside another
solid cube or the skull get no paint, and coplanar duplicates are removed, so nothing z-fights.
Root groups use the body's bone names (Head, and Chest for long hair)."""
import base64, copy, io, json, os, uuid
import numpy as np
from PIL import Image
from render_bb import affine, face_corners
from fix_texture_bleed import pad_file

ASSETS = 'C:/Users/lucas/club-impz/godot-game/assets/'
OUT = 'C:/Users/lucas/blockbench_models/impz/head/'
BODY = json.load(open(ASSETS + 'models/impz/bodies/body_green.bbmodel', encoding='utf8'))
TEMPLATE = {k: v for k, v in BODY['elements'][0].items() if k not in ('name', 'from', 'to', 'origin', 'rotation', 'faces', 'uuid')}
TEMPLATE['autouv'] = 0
TEMPLATE['stretch'] = [1, 1, 1]   # the body cube's 0.98 would shrink every trait cube and open seams
SKULL = next(e for e in BODY['elements'] if e['uuid'].startswith('5494bfa8'))
BONES = {g['name']: g for g in BODY['groups']}
FACE_SIZE = {'north': (0, 1), 'south': (0, 1), 'east': (2, 1), 'west': (2, 1), 'up': (0, 2), 'down': (0, 2)}
ALL_FACES = ('north', 'east', 'south', 'west', 'up', 'down')
L_KEY = np.array([-.38, .62, .69])
L_KEY = L_KEY / np.linalg.norm(L_KEY)


def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], float)


def ramp(t, stops):
    xs = np.linspace(0, 1, len(stops))
    cs = [hx(c) for c in stops]
    t = np.clip(t, 0, 1)
    return np.stack([np.interp(t, xs, [c[k] for c in cs]) for k in range(3)], -1)


def S(stops, c=None, r=None, base=.52, gain=.30, face=.08, mods=(), decals=(), cut=None, per_cube=False, alpha=255):
    """Shader factory. c, r: the rounded form the shading follows (per_cube: each cube is its own lump).
    mods(P, N, t) -> t. decals: (mask(P, N), stops, tone(P, N)). cut(P, N) -> keep."""
    def shader(P, N, cube):
        if per_cube or c is None:
            cc = (np.array(cube['fr']) + np.array(cube['to'])) / 2
            rr = (np.array(cube['to']) - np.array(cube['fr'])) / 2 + .01
        else:
            cc, rr = np.array(c, float), np.array(r, float)
        n = (P - cc) / rr
        n = n / (np.linalg.norm(n, axis=-1, keepdims=True) + 1e-6)
        t = base + gain * (n @ L_KEY) + face * (N @ L_KEY)
        for m in mods:
            t = m(P, N, t)
        rgb = ramp(t, stops)
        for mask, st, tone in decals:
            m_ = mask(P, N)
            rgb = np.where(m_[..., None], ramp(tone(P, N) if callable(tone) else np.full(t.shape, tone), st), rgb)
        al = np.full(t.shape, alpha, float)
        if cut is not None:
            al = np.where(cut(P, N), al, 0)
        return rgb, al
    return shader


def comb(amp=.14, freq=1.):
    """Comb lines: across x on the top and front, across z on the sides."""
    def f(P, N, t):
        u = np.where(np.abs(N[..., 0]) > .5, P[..., 2], P[..., 0])
        return t - amp * (((u * freq) % 3) < 1)
    return f


def curls(amp=.13):
    """Soft blobby curl shapes, not noise."""
    def f(P, N, t):
        x, y, z = P[..., 0], P[..., 1], P[..., 2]
        v = np.sin(x * .55 + 2.2 * np.sin(y * .32)) * np.sin(y * .55 + 2.2 * np.sin(z * .32 + x * .2))
        return t + amp * np.where(v > .35, 1, np.where(v < -.45, -1, 0))
    return f


class Trait:
    def __init__(self, name):
        self.name, self.cubes = name, []

    def box(self, name, fr, to, shader, rot=None, origin=None, faces=ALL_FACES, solid=True, glow=False, bone='Head'):
        assert not any(c['name'] == name + ('_glow' if glow else '') for c in self.cubes), name
        self.cubes.append(dict(name=name + ('_glow' if glow else ''), fr=[float(v) for v in fr], to=[float(v) for v in to], shader=shader, rot=rot, origin=origin,
                               faces=list(faces), solid=solid, bone=bone))

    def mirror(self, name, fr, to, shader, **kw):
        """Same cube on +X (_l) and -X (_r)."""
        self.box(name + '_l', fr, to, shader, **kw)
        self.box(name + '_r', (-to[0], fr[1], fr[2]), (-fr[0], to[1], to[2]), shader, **kw)

    def uid(self, s):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f'club-impz/head/{self.name}/{s}'))

    def _matrix(self, c):
        o = c['origin'] or [(a + b) / 2 for a, b in zip(c['fr'], c['to'])]
        return affine(c['rot'] or [0, 0, 0], o)

    def _inside(self, pts, skip):
        """Is each point inside the skull or another solid cube?"""
        pts4 = np.concatenate([pts, np.ones(pts.shape[:-1] + (1,))], -1)
        inside = ((pts >= np.array(SKULL['from'])) & (pts <= np.array(SKULL['to']))).all(-1)
        for j, o in enumerate(self.cubes):
            if j == skip or not o['solid']:
                continue
            lp = (pts4 @ np.linalg.inv(self._matrix(o)).T)[..., :3]
            inside |= ((lp >= np.array(o['fr'])) & (lp <= np.array(o['to']))).all(-1)
        return inside

    def build(self):
        reqs = []
        seen = set()
        for i, c in enumerate(self.cubes):
            size = [b - a for a, b in zip(c['fr'], c['to'])]
            assert all(abs(s - round(s)) < 1e-6 and s > 0 for s in size), (self.name, c['name'], size)
            c['size'] = [int(round(s)) for s in size]
            M = self._matrix(c)
            R = M[:3, :3]
            for fn in c['faces']:
                a, b = FACE_SIZE[fn]
                w, h = c['size'][a], c['size'][b]
                tl, tr, bl, n = face_corners(c['fr'], c['to'])[fn]
                tl, tr, bl = [np.array(p, float) for p in (tl, tr, bl)]
                yy, xx = np.mgrid[0:h, 0:w]
                s_, q_ = (xx + .5) / w, (yy + .5) / h
                loc = tl + s_[..., None] * (tr - tl) + q_[..., None] * (bl - tl)
                P = (loc @ R.T) + M[:3, 3]
                N = np.broadcast_to(R @ np.array(n, float), P.shape)
                rgb, al = c['shader'](P, N, c)
                # hide a texel only if ALL of it is covered: a half-covered texel must stay, or it leaves a slit
                du, dv = R @ ((tr - tl) / w), R @ ((bl - tl) / h)
                hidden = np.ones((h, w), bool)
                for sa in (-.45, 0, .45):
                    for sb in (-.45, 0, .45):
                        hidden &= self._inside(P + N * .06 + sa * du + sb * dv, i)
                al = np.where(hidden, 0, al)
                if c['solid'] and not c['rot']:
                    # coplanar duplicate from an earlier cube: keep only the first, so it can't z-fight
                    axis = int(np.argmax(np.abs(n)))
                    keys = np.round(P * 2).astype(int)
                    for y_ in range(h):
                        for x_ in range(w):
                            if al[y_, x_] > 0:
                                k = (fn, tuple(keys[y_, x_]))
                                if k in seen:
                                    al[y_, x_] = 0
                                else:
                                    seen.add(k)
                if (al <= 0).all():
                    continue
                reqs.append((i, fn, w, h, rgb, al))
        reqs.sort(key=lambda q: (-q[3], -q[2]))
        for size in (64, 128, 256, 512, 1024):
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
        raise ValueError('texture too small ' + self.name)

    def save(self):
        atlas, uvs, size = self.build()
        d = copy.deepcopy(BODY)
        elements = []
        for i, c in enumerate(self.cubes):
            faces = {}
            for fn in ALL_FACES:
                a, b = FACE_SIZE[fn]
                faces[fn] = {'uv': uvs[i, fn], 'texture': 0} if (i, fn) in uvs else {'uv': [0, 0, c['size'][a], c['size'][b]], 'texture': None}
            e = copy.deepcopy(TEMPLATE)
            origin = c['origin'] or [(p + q) / 2 for p, q in zip(c['fr'], c['to'])]
            e.update({'name': c['name'], 'from': [round(v, 5) for v in c['fr']], 'to': [round(v, 5) for v in c['to']], 'origin': [round(float(v), 5) for v in origin],
                      'faces': faces, 'type': 'cube', 'uuid': self.uid(c['name'])})
            if c['rot']:
                e['rotation'] = [round(float(v), 3) for v in c['rot']]
            elements.append(e)

        def group(name, like):
            g = copy.deepcopy(BONES[like])
            g.update(name=name, uuid=self.uid('group/' + name), children=[])
            return g

        d['groups'], d['outliner'] = [], []
        for bone in sorted({c['bone'] for c in self.cubes}, key=lambda b: b != 'Head'):
            inner = self.name if bone == 'Head' else f'{self.name}_{bone.lower()}'
            d['groups'] += [group(bone, bone), group(inner, bone)]
            kids = [e['uuid'] for e, c in zip(elements, self.cubes) if c['bone'] == bone]
            d['outliner'].append({'uuid': self.uid('group/' + bone), 'isOpen': True, 'children': [{'uuid': self.uid('group/' + inner), 'isOpen': True, 'children': kids}]})
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
        print(f'{self.name:18s} {len(elements):3d} cubes  {size}px texture')
