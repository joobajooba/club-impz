"""Floating-piece test for any .bbmodel: every cube must touch another cube, or the skull/body for traits. Rotated cubes count."""
import glob, json, os
import numpy as np
from render_bb import cube_world

SKULL = (np.array([-15, 63, -9.]), np.array([15, 91, 19.]))


def samples(d):
    W = cube_world(d)
    out = {}
    for e in d['elements']:
        g = [np.linspace(e['from'][k], e['to'][k], max(2, int(e['to'][k] - e['from'][k]) + 1)) for k in range(3)]
        pts = np.array([[x, y, z, 1.] for x in g[0] for y in g[1] for z in g[2]])
        out[e['uuid']] = (e['name'], (W[e['uuid']] @ pts.T).T[:, :3])
    return out


def floating(d, trait=True, skip=()):
    s = samples(d)
    ids = list(s)
    link = {i: set() for i in ids}
    for a, p in enumerate(ids):
        for q in ids[a + 1:]:
            A, B = s[p][1], s[q][1]
            if len(A) * len(B) > 3e6:
                A, B = A[::4], B[::4]
            if np.min(np.linalg.norm(A[:, None] - B[None], axis=-1)) <= 1.1:
                link[p].add(q)
                link[q].add(p)
    if trait:
        start = [i for i in ids if ((s[i][1] >= SKULL[0] - 1.1) & (s[i][1] <= SKULL[1] + 1.1)).all(1).any()]
    else:
        start = ids[:1]
    seen, stack = set(start), list(start)
    while stack:
        for q in link[stack.pop()]:
            if q not in seen:
                seen.add(q)
                stack.append(q)
    return [s[i][0] for i in ids if i not in seen and not s[i][0].startswith(skip)]


total = 0
for f in sorted(glob.glob('C:/Users/lucas/blockbench_models/impz/eyes/eyes_*.bbmodel')):
    n = os.path.basename(f)[:-8]
    if n.endswith(('showcase', 'on_body')):
        continue
    r = floating(json.load(open(f, encoding='utf8')), skip=('beam', ))
    total += len(r)
    print(f'{n:22s}', r or 'all joined')
body = json.load(open('C:/Users/lucas/club-impz/godot-game/assets/models/impz/bodies/body_green.bbmodel', encoding='utf8'))
r = floating(body, trait=False)
print('body (same on all 10):', r or 'all joined')
print('floating pieces in eye traits:', total)
