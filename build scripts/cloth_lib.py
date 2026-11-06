"""Toolkit for the Imp's Clothing traits (implingz_collection.md section 6, 8): shells slightly larger than the body parts,
each following its real bone. A file keeps the body's bone chain with the same names, origins and rotations, so a sleeve
cube uses the arm's own coordinates and lands on the arm exactly. Painted in world space at 1 px per unit, like the bodies."""
import base64, copy, io, json, os, uuid
import numpy as np
from PIL import Image
from render_bb import affine, face_corners
from head_lib import S, ramp, hx, L_KEY, BODY, TEMPLATE, FACE_SIZE, ALL_FACES
from fix_texture_bleed import pad_file

OUT = 'C:/Users/lucas/blockbench_models/impz/clothing/'
GROUPS = {g['uuid']: g for g in BODY['groups']}
ELS = {e['uuid']: e for e in BODY['elements']}
BONE_M, BONE_PATH, BODY_SOLIDS, PART = {}, {}, [], {}
PART_NAMES = {'Pelvis/Pelvis': 'pelvis', 'Chest/Chest': 'chest', 'R-Arm/R-Arm': 'arm_r', 'L-Arm/L-Arm': 'arm_l',
              'R-Forearm/R-Forearm': 'fore_r', 'L-Forearm/L-Forearm': 'fore_l', 'R-Hand/R-Hand': 'hand_r', 'L-Hand/L-Hand': 'hand_l'}


def _walk(node, M, path):
    if isinstance(node, str):
        e = ELS[node]
        # only the torso: the limbs, tail and head move, so a hole cut for them would show when they do
        if path[-1] in ('Pelvis', 'Chest') and e['name'] in ('Pelvis', 'Chest'):
            BODY_SOLIDS.append((M @ affine(e.get('rotation'), e['origin']), e))
        key = f"{path[-1]}/{e['name']}"
        if key in PART_NAMES and PART_NAMES[key] not in PART:
            PART[PART_NAMES[key]] = dict(fr=e['from'], to=e['to'], rot=e.get('rotation'), origin=e['origin'], bone=path[-1])
        if e['name'].endswith('Calf'):       # two cubes per leg: the upper is the thigh shape, the lower the shin
            side = 'l' if e['name'][0] == 'L' else 'r'
            PART['thigh_' + side if abs(e.get('rotation', [0])[0]) > 20 else 'shin_' + side] = dict(fr=e['from'], to=e['to'], rot=e.get('rotation'), origin=e['origin'], bone=path[-1])
        return
    g = GROUPS[node['uuid']]
    M2 = M @ affine(g.get('rotation'), g['origin'])
    BONE_M[g['name']] = M2
    BONE_PATH[g['name']] = path + [g['name']]
    for k in node['children']:
        _walk(k, M2, path + [g['name']])


for n in BODY['outliner']:
    _walk(n, np.eye(4), [])

LOC = {}      # the texel positions in the cube's own coordinates, for shaders that need them


def edge_dist(N=None):
    """Distance from each texel to the nearest edge of its face, in units."""
    fr, to, p, n = LOC['fr'], LOC['to'], LOC['p'], LOC['n']
    d = np.full(p.shape[:-1], 1e9)
    for k in range(3):
        if abs(n[k]) < .5:
            d = np.minimum(d, np.minimum(p[..., k] - fr[k], to[k] - p[..., k]))
    return d


def trim(w=1.):
    return lambda P, N: edge_dist() < w


def front(P, N):
    return N[..., 2] > .5


def back(P, N):
    return N[..., 2] < -.5


def fall(y0, y1, amt):
    """Darker toward the hem (y0), as the style rules ask."""
    return lambda P, N, t: t - amt * np.clip((y1 - P[..., 1]) / (y1 - y0), 0, 1)


def bands(step, amt, y0=0.):
    """Soft dark line at the bottom of each padded band, lighter at its top."""
    return lambda P, N, t: t + amt * (((P[..., 1] - y0) % step) / step - .5)


def bitmap(rows, cx, top, palette):
    """Decals from ASCII art on the front faces, centred on cx, first row at world y = top."""
    w = max(len(r) for r in rows)
    x0 = int(round(cx - w / 2))
    out = []
    grid = np.array([list(r.ljust(w, '.')) for r in rows])
    for ch, col in palette.items():
        def mask(P, N, ch=ch):
            i = np.floor(top - P[..., 1]).astype(int)
            j = np.floor(P[..., 0] - x0).astype(int)
            ok = (i >= 0) & (i < grid.shape[0]) & (j >= 0) & (j < w) & (N[..., 2] > .5)
            r = np.zeros(ok.shape, bool)
            r[ok] = grid[i[ok], j[ok]] == ch
            return r
        out.append((mask, [col, col], .5))
    return out


class Cloth:
    KIND, FOLDER = 'clothing', OUT

    def __init__(self, name):
        self.name, self.cubes, self.subs = name, [], {}

    def own_bone(self, sub, pivot):
        """A bone of this trait's own inside the body bone, so the piece can move: a wing flaps about its pivot."""
        self.subs[sub] = [float(v) for v in pivot]

    def box(self, name, fr, to, shader, bone='Chest', rot=None, origin=None, faces=ALL_FACES, solid=True, sub=None):
        assert not any(c['name'] == name for c in self.cubes), name
        self.cubes.append(dict(name=name, fr=[float(v) for v in fr], to=[float(v) for v in to], shader=shader, rot=rot, origin=origin, faces=list(faces), solid=solid, bone=bone, sub=sub))

    def mirror(self, name, fr, to, shader, rot=None, origin=None, **kw):
        """Same cube on +X (_l) and -X (_r)."""
        o = origin or [(a + b) / 2 for a, b in zip(fr, to)]
        self.box(name + '_l', fr, to, shader, rot=rot, origin=o, **kw)
        r2 = (rot[0], -rot[1], -rot[2]) if rot else None
        self.box(name + '_r', (-to[0], fr[1], fr[2]), (-fr[0], to[1], to[2]), shader, rot=r2, origin=(-o[0], o[1], o[2]), **kw)

    def wrap(self, name, part, shader, g=.5, skip_top=0, skip_bot=0, gz=None, **kw):
        """A shell over a body part, in that part's own coordinates. g: how far outside it. skip_*: leave off whole units."""
        p = PART[part]
        gz = g if gz is None else gz
        fr = [p['fr'][0] - g, p['fr'][1] - g + skip_bot, p['fr'][2] - gz]
        to = [p['to'][0] + g, p['to'][1] + g - skip_top, p['to'][2] + gz]
        self.box(name, fr, to, shader, bone=p['bone'], rot=p['rot'], origin=p['origin'], **kw)

    def both(self, name, part, shader, **kw):
        self.wrap(name + '_l', part + '_l', shader, **kw)
        self.wrap(name + '_r', part + '_r', shader, **kw)

    def uid(self, s):
        return str(uuid.uuid5(uuid.NAMESPACE_URL, f'club-impz/{self.KIND}/{self.name}/{s}'))

    def _m(self, c):
        o = c['origin'] or [(a + b) / 2 for a, b in zip(c['fr'], c['to'])]
        return BONE_M[c['bone']] @ affine(c['rot'] or [0, 0, 0], o)

    def _inside(self, pts, skip):
        pts4 = np.concatenate([pts, np.ones(pts.shape[:-1] + (1,))], -1)
        inside = np.zeros(pts.shape[:-1], bool)
        for M, e in (() if self.cubes[skip].get('sub') else BODY_SOLIDS):
            lp = (pts4 @ np.linalg.inv(M).T)[..., :3]
            fr, to = np.array(e['from']), np.array(e['to'])
            c, h = (fr + to) / 2, (to - fr) / 2 * np.abs(np.array(e.get('stretch') or [1, 1, 1]))
            inside |= (np.abs(lp - c) <= h).all(-1)
        for j, o in enumerate(self.cubes):
            if j == skip or not o['solid'] or (o['bone'], o.get('sub')) != (self.cubes[skip]['bone'], self.cubes[skip].get('sub')):     # pieces on other bones move apart
                continue
            lp = (pts4 @ np.linalg.inv(self._m(o)).T)[..., :3]
            inside |= ((lp >= np.array(o['fr'])) & (lp <= np.array(o['to']))).all(-1)
        return inside

    def build(self):
        reqs, seen = [], set()
        for i, c in enumerate(self.cubes):
            size = [b - a for a, b in zip(c['fr'], c['to'])]
            assert all(abs(s - round(s)) < 1e-6 and s > 0 for s in size), (self.name, c['name'], size)
            c['size'] = [int(round(s)) for s in size]
            M = self._m(c)
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
                LOC.update(fr=c['fr'], to=c['to'], p=loc, n=n)
                rgb, al = c['shader'](P, N, c)
                du, dv = R @ ((tr - tl) / w), R @ ((bl - tl) / h)
                hidden = np.ones((h, w), bool)      # only if all of the texel is covered, or it leaves a slit
                for sa in (-.45, 0, .45):
                    for sb in (-.45, 0, .45):
                        hidden &= self._inside(P + N * .06 + sa * du + sb * dv, i)
                al = np.where(hidden, 0, al)
                keys = np.round(P * 2).astype(int)
                wn = R @ np.array(n, float)
                # a duplicate only if truly coplanar: same direction and same plane
                nk = tuple(np.round(wn, 2)) + (round(float(P[0, 0] @ wn), 2),)
                for y_ in range(h):
                    for x_ in range(w):
                        if al[y_, x_] > 0:
                            k = (nk, tuple(keys[y_, x_]))
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
            uvs, ok = {}, True
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
            e.pop('rotation', None)
            if c['rot']:
                e['rotation'] = [round(float(v), 3) for v in c['rot']]
            elements.append(e)
        bones = {c['bone'] for c in self.cubes}
        keep = set()
        for b in bones:
            keep |= set(BONE_PATH[b])
        keep.discard('Origin')
        groups = []

        def node(body_node):
            """The body's chain, pruned to the bones this outfit uses. Each bone holds one <trait>_<bone> group of cubes."""
            out = []
            for k in body_node['children']:
                if isinstance(k, str):
                    continue
                g = GROUPS[k['uuid']]
                if g['name'] not in keep:
                    continue
                cp = copy.deepcopy(g)
                cp.update(uuid=self.uid('bone/' + g['name']))
                groups.append(cp)
                kids = node(k)
                if g['name'] in bones:
                    for sb in sorted({c.get('sub') or '' for c in self.cubes if c['bone'] == g['name']}):
                        inner = copy.deepcopy(g)
                        iname = f"{self.name}_{sb or g['name'].lower().replace('-', '_')}"
                        inner.update(name=iname, uuid=self.uid('group/' + (sb or g['name'])), rotation=[0, 0, 0])
                        if sb:
                            inner['origin'] = self.subs[sb]
                        groups.append(inner)
                        kids.append({'uuid': inner['uuid'], 'isOpen': True, 'children': [e['uuid'] for e, c in zip(elements, self.cubes) if c['bone'] == g['name'] and (c.get('sub') or '') == sb]})
                out.append({'uuid': cp['uuid'], 'isOpen': True, 'children': kids})
            return out

        outliner = []
        for root in BODY['outliner']:
            outliner += node(root)
        d.update(name=self.name, elements=elements, groups=groups, outliner=outliner)
        b = io.BytesIO()
        Image.fromarray(atlas).save(b, 'PNG', optimize=True)
        d['textures'][0].pop('relative_path', None)
        d['textures'][0].update(name=self.name + '.png', internal=True, source='data:image/png;base64,' + base64.b64encode(b.getvalue()).decode(),
                                width=size, height=size, uv_width=size, uv_height=size, uuid=self.uid('texture'))
        os.makedirs(self.FOLDER, exist_ok=True)
        Image.fromarray(atlas).save(self.FOLDER + self.name + '.png')
        with open(self.FOLDER + self.name + '.bbmodel', 'w', encoding='utf8', newline='') as f:
            json.dump(d, f, separators=(',', ':'))
        # 2 px gaps and a 1 px border of each face's own colour, so cube edges don't sample the gutter
        pad_file(self.FOLDER + self.name + '.bbmodel', [self.FOLDER + self.name + '.png'])
        print(f'{self.name:28s} {len(elements):3d} cubes  {size}px texture')
