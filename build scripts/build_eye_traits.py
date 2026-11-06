"""The Eyes traits (implingz_collection.md section 7), shapes taken from docs/imp-traits/layers/eyes_*.png and scaled to the model's face.
Eye colours are texture overlays (same UV layout as the bodies). Eyewear is a model on the face. 3D Glasses has its own script.
Viewer's left is -X, viewer's right is +X. The model's eyes sit at y 72-80, x +-3 to +-13, and the face is at z = 19."""
import math
import numpy as np
from PIL import Image
from eye_lib import *
from fix_texture_bleed import fix_overlays

SUNK = 18.5        # back of anything on the face, so nothing is coplanar with it
FRAME = (SUNK, 20.5)
LENS = (19, 20)
DARK = ['#141311', '#1c1b18', '#262420', '#34312b', '#4a463e']


def polygon_mask(points):
    """Even-odd test on cell centres."""
    inside = np.zeros(CX.shape, bool)
    n = len(points)
    for i in range(n):
        x1, y1 = points[i]
        x2, y2 = points[(i + 1) % n]
        cond = (y1 > CY) != (y2 > CY)
        inside ^= cond & (CX < (x2 - x1) * (CY - y1) / (y2 - y1 + 1e-9) + x1)
    return inside


def shades():
    t = Trait('eyes_shades')
    # same silhouette as the 3D Glasses: wide, with the nose notch and tapered lower corners
    lens = (AX >= 2) & (AX < 14) & (CY > 71) & (CY < 81)
    lens &= ~((CY < 75) & (AX < 2 + (75 - CY)))
    lens &= ~((CY < 72.5) & (AX >= 13))
    frame = dilate(lens) & ~lens
    frame |= (AX < 16) & (CY > 81) & (CY < 83)
    frame |= (AX >= 14) & (AX < 16) & (CY > 73) & (CY < 83)
    frame |= (AX < 2) & (CY > 75) & (CY < 83)
    fr_r = ['#191515', '#2a2424', '#423a3a', '#544b4b', '#6e6463']
    t.layer('frame', frame, FRAME, fr_r, tone=frame_tone(frame, base=.62))
    t.layer('lens', lens, LENS, ['#21100a', '#33190c', '#441e12', '#4b3124', '#8a6a55'], tone=lens_tone(lens, base=.48), alpha=232, sides=False)
    t.arms(fr_r)
    return t


def bug_eye():
    t = Trait('eyes_bug_eye')
    lens = np.abs((AX - 8) / 7.6) ** 2.7 + np.abs((CY - 76) / 5.8) ** 2.7 < 1   # rounder corners, no one-cell knobs
    lens |= (AX > 9.5) & (AX < 15.5) & (CY > 78) & (CY < 82.2) & (CY < 81.2 + (AX - 13) * .5)   # the cat-eye lift
    frame = dilate(lens) & ~lens
    frame |= (AX < 1.5) & (CY > 76.5) & (CY < 78.5)
    t.plate('lens', frame, lens, FRAME, DARK, ['#384e23', '#616d27', '#798b56', '#798f64', '#b5c79d'], lens_tone_=lens_tone(lens, base=.42), lens_alpha=238)
    t.arms(DARK)
    return t


def glasses():
    t = Trait('eyes_glasses')
    lens = (AX >= 2.5) & (AX < 15) & (CY > 70.5) & (CY < 81.5)
    lens &= ~((CY < 71.5) & ((AX < 4) | (AX > 13.5)))
    lens &= ~((CY > 80.5) & ((AX < 3) | (AX > 14.5)))
    frame = dilate(lens) & ~lens
    frame |= (AX < 2.5) & (CY > 76.5) & (CY < 78.5)
    t.layer('frame', frame, FRAME, DARK)
    # nearly clear, with a faint warm sheen: the eyes show through
    t.layer('lens', lens, LENS, ['#c0c0c0', '#d4d0c8', '#e8e0d4', '#faefe6', '#fff8f0'], tone=lens_tone(lens, base=.6, lip=0), alpha=70, sides=False)
    t.arms(DARK)
    return t


def hearts():
    t = Trait('eyes_hearts')
    u, w = (AX - 8.5) / 7.2, (CY - 75) / 6.6
    lens = (u * u + w * w - 1) ** 3 - u * u * w ** 3 <= 0
    rim = dilate(lens) & ~lens
    rim |= (AX < 2) & (CY > 76.5) & (CY < 78.5)
    rim_r = ['#5a1616', '#862424', '#ac3232', '#c44343', '#d95763']
    t.plate('heart', rim, lens, FRAME, rim_r, ['#862424', '#ac3232', '#d95763', '#ed7580', '#ffb7c5'], lens_tone_=lens_tone(lens, base=.52, shine=.40, lip=.1), lens_alpha=205)
    t.arms(rim_r)
    return t


def stars():
    t = Trait('eyes_stars')
    outline = np.zeros(CX.shape, bool)
    for sx in (-1, 1):
        pts = []
        for i in range(10):
            r = 10.6 if i % 2 == 0 else 5.6
            a = math.pi / 2 + i * math.pi / 5
            pts.append((sx * 9.5 + r * math.cos(a), 75.5 + r * math.sin(a)))
        outline |= polygon_mask(pts)
    lens = erode(outline)
    rim = outline & ~lens
    rim |= (AX < 2) & (CY > 76) & (CY < 78)
    gold = ['#7f6404', '#b48f06', '#d4ab08', '#e8c80a', '#f5dc4a']
    t.plate('star', rim, lens, FRAME, gold, ['#c9a807', '#e6cb08', '#fbe10a', '#fce94f', '#fef39f'], lens_tone_=lens_tone(lens, base=.58, shine=.42, lip=.04))
    t.arms(gold)
    return t


def goggles():
    t = Trait('eyes_goggles')
    outer = (AX < 17) & (CY > 66) & (CY < 88)
    outer &= ~((CY > 87) & (AX > 14)) & ~((CY > 86) & (AX > 16)) & ~((CY < 67) & (AX > 13)) & ~((CY < 69) & (AX > 15.5))
    outer &= ~(CY < 73.5 - AX * 1.1)   # nose notch
    lens = erode(outer, 3)
    rim = outer & ~lens
    rim_r = ['#444c52', '#5d6569', '#75858f', '#8d9ca5', '#b4c0c7']
    t.layer('rim', rim, (SUNK, 21.5), rim_r, tone=frame_tone(rim, base=.62, drop=.30))
    lx, ly = norm_coords(lens)
    # mirrored red-to-orange: bright at the upper left, deep at the lower right, diagonal shine streaks
    tone = .86 - .62 * (lx * .62 + ly * .68)
    streak = ((lx * 30 + ly * 13) % 9)
    tone = tone + np.where((streak < 2) & (ly < .8), .17, 0) - np.where(dist_to_edge(lens) == 1, .08, 0) - np.where(ly < .08, .14, 0)
    t.layer('lens', lens, (SUNK, 20.5), ['#770423', '#ac110e', '#d34627', '#ed7947', '#f8b98c'], tone=tone, sides=False)
    t.arms(['#23262a', '#2f3337', '#3d4247', '#4c5258', '#5d6569'], y=(76, 82), name='strap')
    return t


def mask():
    t = Trait('eyes_mask')
    top = np.where(AX < 13, 81.5 + AX * .22, 84.3 + (AX - 13) * .95)        # dips at the middle, pointed flaps at the sides
    bot = np.where(AX < 5, 74.8 - AX * .95, np.where(AX < 12, 69.6, 69.6 + (AX - 12) * 1.25))
    plate = (AX < 18.5) & (CY < top) & (CY > bot)
    hole_top = 73.6 + (AX - 3.5) * .58     # the angry slant, down toward the nose
    hole = (AX > 3.5) & (AX < 12.5) & (CY < hole_top) & (CY > 72 + np.abs(AX - 8) * .14)
    plate_r = ['#141d20', '#222f34', '#304248', '#3f565e', '#5f7a84']
    t.plate('mask', plate & ~hole, hole, (SUNK, 20.5), plate_r, ['#c9dde4', '#deebef', '#eef6f8', '#f8fcfc', '#fbfefb'],
            rim_tone=frame_tone(plate, base=.62, drop=.32), lens_tone_=.95 - .45 * norm_coords(hole)[1])
    t.arms(plate_r, name='tie')
    return t


def robo():
    t = Trait('eyes_robo')
    bar = (AX < 16) & (CY > 69) & (CY < 83) & ~((CY > 82) & (AX > 15)) & ~((CY < 70) & (AX > 15))
    slit = (AX < 12) & (CY > 75) & (CY < 79)
    steel = ['#2e2e30', '#4c4c4c', '#515152', '#79797c', '#a9a9ad']
    tone = frame_tone(bar, base=.60, drop=.30)
    tone = tone - np.where((CY < 74) & (np.floor(CX + 16) % 7 == 0), .16, 0)     # painted panel lines
    tone = tone + np.where((CY > 81) & (CX < -13), .32, 0)                        # the art's lit corner
    t.layer('visor', bar & ~slit, (SUNK, 21.5), steel, tone=tone)
    glow = 1 - np.abs(CY - 77) / 2.4
    t.layer('slit', slit, (19, 20.5 - .5), ['#1f8f8e', '#3fd4d0', '#8effff', '#c5ffff', '#f0ffff'], tone=.22 + .42 * glow, sides=False, glow=True)
    t.arms(steel, y=(74, 80), name='side')
    return t


def eye_patch():
    t = Trait('eyes_eye_patch')
    patch = ((CX - 8.5) / 7.2) ** 2 + ((CY - 75.2) / 6.8) ** 2 < 1
    strap = ['#0d0c16', '#14121f', '#191728', '#1d1a30', '#2a2744']
    t.layer('patch', patch, FRAME, ['#0f0d1e', '#191728', '#1d1a30', '#201d39', '#3b3762'], tone=frame_tone(patch, base=.58, drop=.34))
    # thin strap: diagonally up across the forehead, toward the viewer's left, then over the top of the head
    p0, p1 = (10.0, 78.0), (-15.0, 88.0)
    dx, dy = p1[0] - p0[0], p1[1] - p0[1]
    L = round(math.hypot(dx, dy))
    rz = math.degrees(math.atan2(-dx, dy))
    t.box('strap_front', (p0[0] - .5, p0[1], 18.5), (p0[0] + .5, p0[1] + L, 19.5), strap, rot=(0, 0, rz), origin=(p0[0], p0[1], 19))
    t.box('strap_temple', (-16, 87.5, 10.5), (-15, 88.5, 18.5), strap)
    # and a short one to the side of the head on the patch's own side
    t.box('strap_side_front', (12, 79, 18.5), (13, 86, 19.5), strap, rot=(0, 0, -28), origin=(12.5, 79, 19))
    t.box('strap_side', (15, 84.5, 10.5), (16, 85.5, 18.5), strap)   # stops short of the horn root
    return t


def monacle():
    t = Trait('eyes_monacle')
    r = np.hypot(CX - 8, CY - 76)
    lens = r < 6.2
    rim = (r < 8.4) & ~lens
    brass = ['#2f230f', '#483619', '#70572d', '#947239', '#c9a35c']
    t.plate('monocle', rim, lens, (SUNK, 21.5), brass, ['#6f6d86', '#9794ac', '#b3b1c6', '#d2d0e0', '#ece9f5'], rim_tone=frame_tone(rim, base=.68, drop=.40, side=.16),
            lens_tone_=lens_tone(lens, base=.42, shine=.40, lip=.1), lens_alpha=178)
    t.box('tab', (14, 67, 18.5), (16, 70, 20.5), brass)
    return t


def tracker(colour, stops):
    t = Trait('eyes_tracker_' + colour)
    side = CX < 0
    lens = side & (AX >= 2.5) & (AX < 14.5) & (CY > 70.5) & (CY < 81.5)
    lens &= ~((CY < 72) & (AX < 4)) & ~((CY < 71.5) & (AX > 13))
    frame = dilate(lens) & ~lens
    case = ['#1a1a1a', '#272727', '#353232', '#696868', '#8d8b8b']
    t.layer('frame', frame, FRAME, case)
    t.layer('lens', lens, LENS, stops, tone=lens_tone(lens, base=.45, shine=.34, lip=.1), alpha=150, sides=False)
    # the housing clipped on beside the viewer's-left ear, with its arm to the lens and a small light
    t.box('housing', (-20, 70, 12), (-16, 85, 21), case)
    t.box('clip', (-17, 76, 4), (-16, 78, 12), case)
    t.box('arm', (-16, 77, SUNK), (-15, 80, 20.5), case)
    t.box('light', (-19, 80, 21), (-17, 82, 22), ['#3f1251', '#76428a', '#a64fd0', '#c88ae8', '#ecd2f8'], wanted=('south', 'up', 'east', 'west', 'down'), glow=True)
    return t


def beams(name, stops, core):
    t = Trait(name)
    L, WIDE = 80, 5

    def paint(w, h, fn):
        """Across the beam: colour, bright, white-hot core, bright, colour. Fades out at the far end. v=0 is at the eye."""
        yy, xx = np.mgrid[0:h, 0:w]
        if fn in ('up', 'down'):
            return ramp(np.full((h, w), 1.), stops), np.full((h, w), 255)
        across = np.array([.25, .5, 1., .5, .25])[np.clip(xx, 0, 4)]
        al = np.clip(255 * (1 - (yy + .5 - h * .86) / (h * .14)), 40, 255)
        return ramp(across, stops), al

    def eye_paint(w, h, fn):
        yy, xx = np.mgrid[0:h, 0:w]
        r = np.hypot((xx + .5) / w - .5, (yy + .5) / h - .5) * 2
        return ramp(.98 - .55 * r, stops), np.clip(235 - 215 * r, 0, 255)

    for sx, s_ in ((1, 'l'), (-1, 'r')):
        ex, ey, ez = sx * 8, 76, 20
        dx, dy, dz = sx * 20, -74, 22
        n = math.sqrt(dx * dx + dy * dy + dz * dz)
        rx = math.degrees(math.asin(-dz / n))
        rz = math.degrees(math.atan2(dx, -dy))
        t.box(f'beam_{s_}', (ex - WIDE / 2, ey - L, ez - WIDE / 2), (ex + WIDE / 2, ey, ez + WIDE / 2), stops, rot=(rx, 0, rz), origin=(ex, ey, ez),
              paint=paint, group='beams', glow=True, wanted=('north', 'east', 'south', 'west', 'down'))
        t.box(f'eye_{s_}', (ex - 4, 73, 19), (ex + 4, 79, 20), stops, wanted=('south',), paint=eye_paint, glow=True)
    return t


LASER = ['#a80000', '#ff0000', '#ff8080', '#f29d9d', '#fff4f4']
NEON = ['#4f9600', '#7be900', '#86ff00', '#a1fb3e', '#f6fff0']


# ---------- texture overlays: same UV layout as the bodies, transparent except for the eye pixels
BODY_MODEL = ASSETS + 'models/impz/bodies/body_green.bbmodel'


def head_front():
    """Top-left texel of the head's front (south) face in the body texture. The overlays follow it,
    so they stay on the eyes when the body's texture layout changes (it was 0,29 before the
    texture-bleed padding, now 33,1)."""
    d = json.load(open(BODY_MODEL, encoding='utf8'))
    u = next(e for e in d['elements'] if e['name'] == 'Head')['faces']['south']['uv']
    return int(min(u[0], u[2])), int(min(u[1], u[3]))


FX, FY = head_front()


def save_overlay(out, name):
    """Write an overlay with the body's 1 px island border (uv_padding), like the body texture."""
    Image.fromarray(out).save(OUT + name + '.png')
    fix_overlays(BODY_MODEL, [OUT + name + ".png"], quiet=True)


def eye_pixels():
    src = np.array(Image.open(ASSETS + 'textures/impz/bodies/body_green.png').convert('RGB')).astype(float)
    mx, mn = src.max(-1), src.min(-1)
    neutral = (mx - mn) < 14
    box = np.zeros(neutral.shape, bool)
    box[FY + 11:FY + 19, FX + 1:FX + 29] = True   # both eyes on the head's front face
    eye = neutral & box
    return src.mean(-1), eye


def overlay(name, pupil, glow, glint='#fff7f2'):
    L, eye = eye_pixels()
    pup = eye & (L < 170)
    ring = eye & dilate(pup) & ~pup
    out = np.zeros(L.shape + (4,), np.uint8)
    p0, p1, g0, g1 = [hx(c) for c in (pupil[0], pupil[1], glow[0], glow[1])]
    t = np.clip((L - 25) / 110, 0, 1)[..., None]
    col = (p0 * .72) * (1 - t) + p1 * t
    out[pup, :3] = col[pup].round()
    t2 = np.clip((L - 170) / 70, 0, 1)[..., None]
    col2 = g1 * (1 - t2) + g0 * t2
    out[ring, :3] = col2[ring].round()
    out[pup | ring, 3] = 255
    for u, v in ((FX + 6, FY + 13), (FX + 29 - 6, FY + 13)):
        out[v, u] = list(hx(glint).astype(int)) + [255]
    save_overlay(out, name)
    print(f'{name:22s} overlay, {int((pup | ring).sum())} px')


def ghostly():
    L, eye = eye_pixels()
    out = np.zeros(L.shape + (4,), np.uint8)
    # no pupils: plain white, icy blue toward the bottom. Pupil pixels take the white of the row they sit on
    v = np.clip((Yi2 - (FY + 12)) / 6, 0, 1)
    tone = ramp(1 - v, ['#aec3cf', '#cce2ed', '#edf9ff', '#fbfefb'])
    shade = np.clip((L - 150) / 90, .82, 1)[..., None]
    pup = eye & (L < 200)
    col = np.where(pup[..., None], tone, tone * shade)
    out[eye, :3] = col[eye].round()
    out[eye, 3] = 255
    save_overlay(out, 'eyes_ghostly')
    print(f"{'eyes_ghostly':22s} overlay, {int(eye.sum())} px")


def beam_eyes(name, stops):
    """Both eyes glow: the eye goes bright with a near-white centre where the pupil was."""
    L, eye = eye_pixels()
    out = np.zeros(L.shape + (4,), np.uint8)
    pup = eye & (L < 170)
    white = ramp(np.full(L.shape, .5), stops)
    centre = ramp(np.full(L.shape, 1.), stops)
    out[eye, :3] = white[eye].round()
    out[pup, :3] = centre[pup].round()
    out[eye, 3] = 255
    save_overlay(out, name)
    print(f'{name:22s} overlay, {int(eye.sum())} px')


Yi2 = np.mgrid[0:256, 0:256][0]

if __name__ == '__main__':
    os.makedirs(OUT, exist_ok=True)
    overlay('eyes_red_pupils', ('#d02b06', '#d83a39'), ('#fbdfcd', '#f3c5a5'))
    overlay('eyes_gold_pupils', ('#a17713', '#ffbe22'), ('#ffeec7', '#ffe6a9'))
    overlay('eyes_purple_pupils', ('#3f1251', '#76428a'), ('#ebcef6', '#e4adfb'))
    ghostly()
    beam_eyes('eyes_lazer_glow', LASER)
    beam_eyes('eyes_neon_beam_glow', NEON)
    for t in (shades(), bug_eye(), glasses(), hearts(), stars(), goggles(), mask(), robo(), eye_patch(), monacle(),
              tracker('blue', ['#1d4650', '#285f6a', '#467396', '#6c98b5', '#a8cade']),
              tracker('purple', ['#5c1d75', '#7a2a99', '#8b30ae', '#a757c8', '#d7a6e8']),
              beams('eyes_lazer', LASER, '#ff8080'), beams('eyes_neon_beam', NEON, '#a1fb3e')):
        t.save()
