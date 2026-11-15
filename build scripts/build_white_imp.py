"""White Imp body (J00BA, 2026-11-14): the base model for players without traits. Same geometry, rig and UV layout as the
ten collection bodies (build_imp_bodies.py); only the skin ramp is new. White is not a collection colour
(implingz_collection.md section 3 has ten); J00BA asked for it as the default look.
Ramp: main is an off-white (never pure white, doc 1.5 rule 3), shading into cool blue-grey, as the house style wants
shadows deeper and slightly saturated rather than flat grey. Output: OUT/white_imp.bbmodel + .png (padded)."""
import copy
from PIL import Image
import build_imp_bodies as b

b.FLAT['white'] = ('#e6e5e1', '#a6aab8', '#545a6c')   # main, mid, deep: main below the eye white, so the eyes still read

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
