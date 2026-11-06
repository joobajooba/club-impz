"""Visible-gap test: put a marker box where the upper skull is, render the trait from many angles, and count marker pixels that show.
This tests what you would actually see, so a slit in the paint can't slip through."""
import copy, json
import numpy as np
from PIL import Image
from render_bb import load_tex, render, yaw

OUT = 'C:/Users/lucas/blockbench_models/impz/head/'
# bald on purpose per the doc: fez, crown, halo, geezer, hawk, tiara. Spiky and the Straw Hat only cover the top.
FULL = ['afro', 'blonde', 'bob', 'slick', 'clown', 'cap', 'mayc_brim', 'sea_captain', 'soldier']
TOP_ONLY = ['spiky', 'straw_hat']
VIEWS = [(90, 0), (-90, 0), (180, 0), (35, 55), (-35, 55), (145, 35), (-145, 35), (0, 80), (90, 30), (-90, 30), (180, 40), (60, 20), (-60, 20), (120, 20), (-120, 20)]
TOP_VIEWS = [(35, 55), (-35, 55), (145, 45), (-145, 45), (0, 80), (90, 60), (-90, 60), (180, 60)]


def marker(d, name, fr, to):
    """A box painted from one opaque texel of the trait's own texture. It is told apart by tinting."""
    T = load_tex(d)[0]
    ys, xs = np.where(T[..., 3] == 255)
    u, v = int(xs[0]), int(ys[0])
    faces = {f: {'uv': [u, v, u + 1, v + 1], 'texture': 0} for f in ('north', 'east', 'south', 'west', 'up', 'down')}
    e = {'name': name, 'from': fr, 'to': to, 'origin': [(a + b) / 2 for a, b in zip(fr, to)], 'faces': faces, 'type': 'cube', 'uuid': 'marker-' + name}
    d['elements'].append(e)
    d['outliner'].append(e['uuid'])
    return e['uuid']


def test(n, boxes, views):
    base = json.load(open(f'{OUT}head_{n}.bbmodel', encoding='utf8'))
    d = copy.deepcopy(base)
    ids = [marker(d, f'm{i}', *b) for i, b in enumerate(boxes)]
    tex = load_tex(d)
    tint = {i: (255, 0, 255) for i in ids}
    worst = 0
    hit = None
    for ya, pi in views:
        v = yaw(ya, pi)
        bd = (-70, 70, -70, 140)
        if pi:
            bd = (-70, 70, -120, 170)
        a = np.array(render(base, tex, v, 4, bd)).astype(int)
        b = np.array(render(d, tex, v, 4, bd, tint=tint)).astype(int)
        # pixels the marker changed, ignoring soft differences
        show = (np.abs(a - b).sum(-1) > 12).sum()
        if show > worst:
            worst, hit = int(show), (ya, pi)
    return worst, hit


total = 0
for n in FULL:
    # the crown of the head, and the sides and back above the hairline. Stops short of the face so hairline cut-outs don't count
    w, h = test(n, [([-14.8, 89, -8.8], [14.8, 90.8, 18.6]), ([-14.8, 84.5, -8.8], [14.8, 89, 10.0])], VIEWS)
    total += w
    print(f'{n:12s} marker pixels showing: {w}' + (f'  worst from yaw/pitch {h}' if w else ''))
for n in TOP_ONLY:
    w, h = test(n, [([-14.8, 90.6, -8.8], [14.8, 90.9, 18.6])], TOP_VIEWS)
    total += w
    print(f'{n:12s} marker pixels showing: {w}' + (f'  worst from yaw/pitch {h}' if w else ''))
print('total marker pixels showing:', total)
