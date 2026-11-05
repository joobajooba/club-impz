"""Metal paint for Gold and Diamond: a reflection baked into each texel, per face, in world orientation.
Every face is treated as slightly domed, so its pseudo-normal sweeps across a studio environment:
bright sky, a hard dark horizon, warm ground bounce, side reflection bands and one tight specular hot spot."""
import json
from pathlib import Path
import numpy as np
from render_bb import cube_world, face_corners

ORIG = Path(__file__).resolve().parent / 'green_imp_orig.bbmodel'
BONE = ('a17c5e4c', '6126654c', '211cb554', 'c0ce4266', 'c7bf925f', '9840f7a8', '9cc27eaf')
TAIL = ('8094d9c3', '78ba8b5a', 'a411ede4')
L_KEY = np.array([-.38, .62, .69])  # light from the upper left, as in the NFT art
L_KEY = L_KEY / np.linalg.norm(L_KEY)


def normals(base, shape, dome=.62, facet=0., seed=11, cell=11):
    """Texel -> world pseudo-normal. Rects come from the original UVs, so cropped horn paint is covered too.
    Rotations come from the current model."""
    orig = json.load(open(ORIG, encoding='utf8'))
    W = cube_world(base)
    h, w = shape
    N = np.zeros((h, w, 3))
    used = np.zeros((h, w), bool)
    rng = np.random.RandomState(seed)
    faces = []
    for e in orig['elements']:
        for fn, f in e['faces'].items():
            if f.get('texture') is None:
                continue
            u1, v1, u2, v2 = f['uv']
            x0, x1, y0, y1 = int(min(u1, u2)), int(max(u1, u2)), int(min(v1, v2)), int(max(v1, v2))
            if x1 > x0 and y1 > y0:
                faces.append(((x1 - x0) * (y1 - y0), e, fn, x0, y0, x1, y1))
    faces.sort(key=lambda r: -r[0])  # the tip horn shares UV space with the middle one: smaller paints last
    for _, e, fn, x0, y0, x1, y1 in faces:
        R = W[e['uuid']][:3, :3]
        tl, tr, bl, n = face_corners([0, 0, 0], [1, 1, 1])[fn]
        tl, tr, bl = [np.array(p, float) for p in (tl, tr, bl)]
        U, V, F = R @ (tr - tl), R @ (bl - tl), R @ np.array(n, float)
        X, Y = np.meshgrid(np.arange(x0, x1), np.arange(y0, y1))
        s = (X + .5 - x0) / (x1 - x0) * 2 - 1
        q = (Y + .5 - y0) / (y1 - y0) * 2 - 1
        nn = F + dome * (s[..., None] * U + q[..., None] * V)
        if facet:
            # cut-gem planes: each Voronoi cell tilts the surface, so it catches a different reflection
            c = int(np.clip((x1 - x0) * (y1 - y0) / cell ** 2, 2, 7))
            px, py = rng.uniform(x0, x1, c), rng.uniform(y0, y1, c)
            tilt = rng.uniform(-1, 1, (c, 3)) * facet
            nn = nn + tilt[((X[..., None] - px) ** 2 + (Y[..., None] - py) ** 2).argmin(-1)]
        N[y0:y1, x0:x1] = nn / np.linalg.norm(nn, axis=-1, keepdims=True)
        used[y0:y1, x0:x1] = True
    return N, used


def env(N, sky, horizon):
    """Tone 0..1 on the material ramp. The horizon curves with x, so it reads as a dome, not a painted stripe."""
    x, z = N[..., 0], N[..., 2]
    y = N[..., 1] - .55 * x * x
    t = np.interp(y, [-1.6, -1.1, horizon - .16, horizon - .04, horizon, horizon + .05, .05, .3, .55, 1], sky)
    t = t + .17 * np.exp(-((x + .40) / .09) ** 2)   # bright window band, lit side
    t = t - .10 * np.exp(-((x - .36) / .12) ** 2)   # dark band, shaded side
    t = t - .34 * np.clip(np.abs(x) - .42, 0, 1)    # edges fall off, as on a polished curve
    h = np.clip(N @ L_KEY, 0, 1)
    return t + .17 * h ** 9 + .42 * h ** 60         # broad sheen plus a tight hot spot


SKY = {
    'gold': [.26, .40, .34, .10, .22, .46, .52, .64, .78, .90],
    'diamond': [.22, .38, .32, .06, .20, .46, .54, .66, .78, .88],
}


MOUTH_DEPTH = {'gold': .38, 'diamond': .22}  # diamond's ramp falls into navy much faster


def mouth_mask(L):
    """1 on the painted mouth, fading to 0 on the skin around it. Box is on the head's front face (UV 0,29-30,57)."""
    m = np.zeros(L.shape)
    v0, v1, u0, u1 = 50, 55, 10, 20
    m[v0:v1, u0:u1] = np.clip((161 - L[v0:v1, u0:u1]) / (161 - 122), 0, 1)
    return m


def tone(N, L, an, tail, name):
    """Reflection plus the painted form: brows, mouth, muscle shading and folds stay readable."""
    painted = np.interp(L, [an['lo'] * .8, an['lo'], an['q1'], an['med'], an['lit'], an['hi']], [0, .16, .42, .55, .68, .78])
    t = env(N, SKY[name], -.48) + .70 * (painted - .55)
    t = t - MOUTH_DEPTH[name] * mouth_mask(L)
    return np.clip(np.where(tail, t * .72, t), 0, 1)


def horn_tone(N, L, bone_L, name):
    """Horns are mostly reflection, with their dark-at-the-skull paint kept as a gentle bias."""
    bias = np.interp(L, [np.percentile(bone_L, 2), np.percentile(bone_L, 98)], [-.10, .06])
    return np.clip(env(N, SKY[name], -.30) + .12 + bias, 0, 1)
