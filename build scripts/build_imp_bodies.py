"""Ten Imp bodies from green_imp: same geometry, one texture per body (implingz_collection.md section 3).

Run order, from anywhere:
  python "build scripts/build_showcase.py"       paints all ten + the showcase file, validates, renders previews
  python "build scripts/export_body_traits.py"   copies them into the repo as body_<colour>
Working files go to ~/blockbench_models/impz, or to IMP_BODY_OUT if that is set.
green_imp_orig.bbmodel is green_imp before the horn edits. It holds the full horn UVs the paint masks need.
green_imp_unpadded.bbmodel is green_imp before the texture-bleed padding: its UV layout is the one the paint
masks are drawn in, so the bodies are painted on it and padded (uv_padding.py) when saved. The result is the
committed, padded green_imp layout.
fix_horns.py and shorten_horns.py are the one-off horn edits, already applied to green_imp: do not re-run them.
"""
import json, base64, io, os, uuid, copy, colorsys
import numpy as np
from pathlib import Path
from PIL import Image
import metal
from fix_texture_bleed import pad_file

HERE = Path(__file__).resolve().parent
REPO = str(HERE.parent / 'godot-game' / 'assets').replace(chr(92), '/') + '/'
OUT = os.environ.get('IMP_BODY_OUT', str(Path.home() / 'blockbench_models' / 'impz')).replace(chr(92), '/') + '/'


def hx(s):
    return np.array([int(s[i:i + 2], 16) for i in (1, 3, 5)], float)


# main, mid, deep: the first-listed value from section 3 where the doc gives two
FLAT = {
    'cyan': ('#48ffe1', '#07846f', '#033029'),
    'silver': ('#cfc9c9', '#919191', '#4f4f4f'),
    'khaki': ('#fffda9', '#d9e03b', '#80700a'),
    'blue': ('#686fff', '#111795', '#070a42'),
    'pink': ('#f4a8b8', '#d94a67', '#b1123a'),
    'purple': ('#9353ab', '#4f1765', '#280735'),
    'green': ('#4bd336', '#285800', '#224604'),
    'red': ('#ff3737', '#7b0000', '#420202'),
}
GOLD = ['#a35e08', '#b05a07', '#d07a10', '#e5901f', '#fbc650', '#fde06d', '#fef8d3']
ICE = ['#0e223b', '#4692cd', '#5a9ee6', '#83c5fe', '#b7e6ff', '#d3eafd', '#f3feff']
BASE = json.load(open(HERE / 'green_imp_unpadded.bbmodel', encoding='utf8'))
ORDER = ['green', 'red', 'blue', 'cyan', 'purple', 'pink', 'khaki', 'silver', 'gold', 'diamond']
BONE = ('a17c5e4c', '6126654c', '211cb554', 'c0ce4266', 'c7bf925f', '9840f7a8', '9cc27eaf')  # horns + spade tip
TAIL = ('8094d9c3', '78ba8b5a', 'a411ede4')


def lum(a):
    return .30 * a[..., 0] + .59 * a[..., 1] + .11 * a[..., 2]


def rects(d):
    out = []
    for e in d['elements']:
        for f in e['faces'].values():
            if f.get('texture') is None:
                continue
            u1, v1, u2, v2 = f['uv']
            x0, x1, y0, y1 = int(min(u1, u2)), int(max(u1, u2)), int(min(v1, v2)), int(max(v1, v2))
            if x1 > x0 and y1 > y0:
                out.append((e, x0, y0, x1, y1))
    return out


def masks(src):
    """Use the pre-crop UVs so the whole horn paint gets recoloured, not just the visible crop."""
    orig = json.load(open(HERE / 'green_imp_orig.bbmodel', encoding='utf8'))
    h, w = src.shape[:2]
    bone = np.zeros((h, w), bool)
    tail = np.zeros((h, w), bool)
    rid = np.full((h, w), -1)
    for i, (e, x0, y0, x1, y1) in enumerate(rects(orig)):
        rid[y0:y1, x0:x1] = i
        if e['uuid'][:8] in BONE:
            bone[y0:y1, x0:x1] = True
        if e['uuid'][:8] in TAIL:
            tail[y0:y1, x0:x1] = True
    return bone, tail & ~bone, rid


def sat(a):
    mx, mn = a.max(-1), a.min(-1)
    return np.where(mx > 0, (mx - mn) / np.maximum(mx, 1), 0)


def body_weight(a):
    """1 = skin, 0 = neutral eye white or pupil. Soft, so eye edges don't fringe green."""
    return np.clip((sat(a) - .10) / .20, 0, 1)


def tone_anchors(a, mask):
    L = lum(a)[mask]
    return dict(lo=np.percentile(L, .5), q1=np.percentile(L, 20), med=np.median(L), lit=np.percentile(L, 90), hi=np.percentile(L, 99.5))


def lighten(c, t):
    return np.minimum(c + (250 - c) * t, 250)


def map_flat(L, an, main, mid, deep):
    ts = [an['lo'] * .8, an['lo'], an['q1'], an['med'], an['lit'], an['hi']]
    cs = [deep, mid * .75 + deep * .25, mid * .34 + main * .66, mid * .14 + main * .86, main, lighten(main, .10)]
    return np.stack([np.interp(L, ts, [c[k] for c in cs]) for k in range(3)], -1)


def map_ramp(t, ramp):
    cs = [hx(c) for c in ramp]
    xs = np.linspace(0, 1, len(cs))
    return np.stack([np.interp(t, xs, [c[k] for c in cs]) for k in range(3)], -1)


def bone_tint(a, hue, amount=.7):
    """Keep the pale cream ramp, swap its green hint for a hint of the body hue."""
    L = lum(a)[..., None]
    chroma = np.abs(a - L).mean(-1, keepdims=True) * amount
    r, g, b = colorsys.hsv_to_rgb(hue, 1, 1)
    tint = np.array([r, g, b]) - (.30 * r + .59 * g + .11 * b)
    return np.clip(L + tint * chroma * 1.6, 0, 250)


def facets(rid, seed=7, cell=9):
    """Crystal planes for Diamond: one offset per Voronoi cell, per face."""
    rng = np.random.RandomState(seed)
    out = np.zeros(rid.shape)
    for r in np.unique(rid):
        if r < 0:
            continue
        ys, xs = np.where(rid == r)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        n = max(2, int((x1 - x0) * (y1 - y0) / cell ** 2))
        px, py = rng.uniform(x0, x1, n), rng.uniform(y0, y1, n)
        val = rng.uniform(-1, 1, n)
        X, Y = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        D = (X[..., None] - px) ** 2 + (Y[..., None] - py) ** 2
        out[y0:y1, x0:x1] = val[D.argmin(-1)]
    return out


def streaks(rid):
    """Soft diagonal glossy bands for Gold, per face."""
    out = np.zeros(rid.shape)
    for r in np.unique(rid):
        if r < 0:
            continue
        ys, xs = np.where(rid == r)
        x0, x1, y0, y1 = xs.min(), xs.max() + 1, ys.min(), ys.max() + 1
        X, Y = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        s = ((X - x0) + (Y - y0) * .6 + r * 5.3) / 34.0 * 2 * np.pi
        out[y0:y1, x0:x1] = ((np.sin(s) + 1) / 2) ** 3
    return out


def paint(name, src):
    a = src[..., :3].astype(float)
    alpha = src[..., 3]
    bone, tail, rid = masks(src)
    w = body_weight(a)
    skin = (rid >= 0) & ~bone & (alpha > 32) & (w > .9)
    an = tone_anchors(a, skin)
    L = lum(a)
    if name in FLAT:
        main, mid, deep = [hx(c) for c in FLAT[name]]
        # the tail is in the body's dark shade (collection doc, section 2)
        Lt = np.where(tail, an['lo'] + (L - an['lo']) * .45, L)
        body = map_flat(Lt, an, main, mid, deep)
        hue = colorsys.rgb_to_hsv(*(main / 255))[0]
        bt = bone_tint(a, hue, .25 if name == 'silver' else .7)
    else:
        ramp = GOLD if name == 'gold' else ICE
        N, _ = metal.normals(BASE, rid.shape, dome=.62, facet=0. if name == 'gold' else .15)
        body = map_ramp(metal.tone(N, L, an, tail, name), ramp)
        bt = map_ramp(metal.horn_tone(N, L, L[bone & (alpha > 32)], name), ramp)
    out = body * w[..., None] + L[..., None] * (1 - w[..., None])  # eye pixels go neutral, no green fringe
    out = np.where(bone[..., None], bt, out)
    return np.concatenate([np.clip(out, 0, 255).round().astype(np.uint8), src[..., 3:]], -1)


def data_url(im):
    b = io.BytesIO()
    Image.fromarray(im).save(b, 'PNG', optimize=True)
    return 'data:image/png;base64,' + base64.b64encode(b.getvalue()).decode()


def texture_entry(d, fn, im):
    t = d['textures'][0]
    t.update(name=fn + '.png', relative_path=fn + '.png', source=data_url(im),
             uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/' + fn)))
    t.pop('path', None)


def base_texture():
    t = BASE['textures'][0]['source']
    return np.array(Image.open(io.BytesIO(base64.b64decode(t.split(',', 1)[1]))).convert('RGBA'))


def save(d, fn, pad=True):
    with open(OUT + fn + '.bbmodel', 'w', encoding='utf8', newline='') as f:
        json.dump(d, f, separators=(',', ':'))
    if pad:
        # 2 px gaps and a 1 px border of each face's own colour; also rewrites OUT + fn + '.png'
        pad_file(OUT + fn + '.bbmodel')


def main():
    os.makedirs(OUT, exist_ok=True)
    base = copy.deepcopy(BASE)
    src = base_texture()
    texes = {}
    for n in ORDER:
        d = copy.deepcopy(base)
        im = paint(n, src)
        texes[n] = im
        fn = n + '_imp'
        d['name'] = fn
        texture_entry(d, fn, im)
        Image.fromarray(im).save(OUT + fn + '.png')
        save(d, fn)
    return base, texes


if __name__ == '__main__':
    main()
