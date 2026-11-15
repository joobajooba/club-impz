"""White Imp body (J00BA, 2026-11-14): the base model for players without traits. Same geometry, rig and UV layout as the
ten collection bodies (build_imp_bodies.py); only the skin ramp is new. White is not a collection colour
(implingz_collection.md section 3 has ten); J00BA asked for it as the default look.
Ramp: main is an off-white (never pure white, doc 1.5 rule 3), shading into cool blue-grey, as the house style wants
shadows deeper and slightly saturated rather than flat grey. Output: OUT/white_imp.bbmodel + .png (padded)."""
import copy
from PIL import Image
import numpy as np
import build_imp_bodies as b

b.FLAT['white'] = ('#dedcd5', '#9097ab', '#4a5064')   # main, mid, deep: main below the eye white, so the eyes still read
# J00BA (2026-11-15): the front looked flat. The shared tone map keeps most of the skin near the main colour, which on a
# saturated body still shows the shading through hue, but on an off-white it all reads as one flat tone. White gets a
# wider map: mid-tones pulled further into the cool shadow and brighter highlights, so the muscle and belly shading
# reads as clearly as on the coloured bodies.
_map_flat = b.map_flat


def _white_map(L, an, main, mid, deep):
    if not np.array_equal(main, b.hx(b.FLAT['white'][0])):
        return _map_flat(L, an, main, mid, deep)
    ts = [an['lo'] * .8, an['lo'], an['q1'], an['med'], an['lit'], an['hi']]
    cs = [deep, mid * .85 + deep * .15, mid * .6 + main * .4, mid * .32 + main * .68, main, b.lighten(main, .38)]
    return np.stack([np.interp(L, ts, [c[k] for c in cs]) for k in range(3)], -1)


b.map_flat = _white_map

d = copy.deepcopy(b.BASE)
src = b.base_texture()
im = b.paint('white', src)
# J00BA: the mouth didn't show. On a near-white ramp the mouth's small dip in value nearly vanishes, so darken it from
# the Green paint's own mouth shape: a soft cool grey, darkest in the middle (the face is the Head's south face).
e = [e for e in b.BASE['elements'] if e['name'] == 'Head'][0]
u = [int(v) for v in e['faces']['south']['uv']]
fx, fy = min(u[0], u[2]), min(u[1], u[3])
import numpy as np
box = (slice(fy + 22, fy + 26), slice(fx + 10, fx + 20))       # the mouth area, below the eyes and nose
gL = src[box][..., :3].astype(float).mean(-1)
k = np.clip((134.0 - gL) / 26.0, 0, 1) ** 0.6                   # 1 at the mouth's darkest pixel, 0 on the skin around it
mouth = np.array([58, 60, 78], float)                           # deep cool charcoal: reads at play distance, never black
# J00BA (2026-11-15): the mouth must be clearly visible, so the grey from 2026-11-14 is now a deep charcoal with a firmer edge
patch = im[box][..., :3].astype(float)
im[box[0], box[1], :3] = np.clip(patch * (1 - k[..., None]) + mouth * k[..., None], 0, 255).round().astype(np.uint8)
fn = 'white_imp'
d['name'] = fn
b.texture_entry(d, fn, im)
Image.fromarray(im).save(b.OUT + fn + '.png')
b.save(d, fn)
print('wrote', b.OUT + fn + '.bbmodel')
