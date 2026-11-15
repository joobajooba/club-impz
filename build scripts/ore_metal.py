"""Metal / gem finish for ore pieces (the method of build scripts/metal.py, for any cube).

Each face is treated as slightly domed, so its pseudo-normal sweeps across a studio environment as you move
over the face: bright sky above, a hard dark horizon band, a warm ground bounce, a bright window band on the
lit side, and a tight specular hot spot from the key light. The cube's own rotation is applied, so tilted
chunks catch the light differently. `facet` tilts Voronoi cells of the face like the planes of a cut gem.
Returns a tone 0..1 per texel, to be mapped onto the material's ramp."""
import math
import numpy as np

L_KEY = np.array([-.38, .62, .69]); L_KEY = L_KEY / np.linalg.norm(L_KEY)   # upper left, toward the viewer


def rot(r):
    x, y, z = [math.radians(a) for a in (r or [0, 0, 0])]
    cx, sx, cy, sy, cz, sz = math.cos(x), math.sin(x), math.cos(y), math.sin(y), math.cos(z), math.sin(z)
    Rx = np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]]); Ry = np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]])
    Rz = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]])
    return Rz @ Ry @ Rx                                   # Blockbench: ZYX Euler


CORNERS = {  # top-left, top-right, bottom-left (as seen from outside, UV orientation), normal; unit cube
    'south': ((0, 1, 1), (1, 1, 1), (0, 0, 1), (0, 0, 1)), 'north': ((1, 1, 0), (0, 1, 0), (1, 0, 0), (0, 0, -1)),
    'east': ((1, 1, 1), (1, 1, 0), (1, 0, 1), (1, 0, 0)), 'west': ((0, 1, 0), (0, 1, 1), (0, 0, 0), (-1, 0, 0)),
    'up': ((0, 1, 0), (1, 1, 0), (0, 1, 1), (0, 1, 0)), 'down': ((0, 0, 1), (1, 0, 1), (0, 0, 0), (0, -1, 0))}

SKY = {  # tone at: deep ground, ground, below horizon, horizon, above horizon x2, low sky, sky, high sky, zenith
    'metal': [.22, .36, .30, .06, .20, .44, .52, .64, .78, .90],
    'gem':   [.20, .34, .28, .10, .26, .48, .56, .68, .80, .92],
    'glass': [.04, .08, .06, .02, .10, .22, .30, .44, .62, .86],
}


def env(N, sky, horizon=-.3):
    x = N[..., 0]
    y = N[..., 1] - .55 * x * x
    t = np.interp(y, [-1.6, -1.1, horizon - .16, horizon - .04, horizon, horizon + .05, .05, .3, .55, 1], sky)
    t = t + .17 * np.exp(-((x + .40) / .09) ** 2)        # bright window band, lit side
    t = t - .10 * np.exp(-((x - .36) / .12) ** 2)        # dark band, shaded side
    t = t - .30 * np.clip(np.abs(x) - .45, 0, 1)         # edges fall off, as on a polished curve
    h = np.clip(N @ L_KEY, 0, 1)
    return t + .17 * h ** 9 + .42 * h ** 60              # broad sheen plus a tight hot spot


def tone(rotation, face, w, h, kind='metal', dome=.62, facet=0., seed=1, cell=4.5, horizon=-.3):
    R = rot(rotation)
    tl, tr, bl, n = (np.array(p, float) for p in CORNERS[face])
    U, V, F = R @ (tr - tl), R @ (bl - tl), R @ n
    X, Y = np.meshgrid(np.arange(w), np.arange(h))
    s = (X + .5) / w * 2 - 1
    q = (Y + .5) / h * 2 - 1
    nn = F + dome * (s[..., None] * U + q[..., None] * V)
    if facet:
        r = np.random.RandomState(seed)
        c = int(np.clip(w * h / cell ** 2, 2, 7))
        px, py = r.uniform(0, w, c), r.uniform(0, h, c)
        tilt = r.uniform(-1, 1, (c, 3)) * facet
        nn = nn + tilt[((X[..., None] - px) ** 2 + (Y[..., None] - py) ** 2).argmin(-1)]
    N = nn / np.linalg.norm(nn, axis=-1, keepdims=True)
    return np.clip(env(N, SKY[kind], horizon), 0, 1)
