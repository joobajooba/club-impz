"""Find faces whose edge can sample the wrong texel (texture bleeding).

For every .bbmodel with one texture, and each textured face: take its UV rectangle in texture
pixels, look at the 1 px ring just outside it, and flag the face if a ring texel next to an
opaque edge texel
  * is more transparent than that edge texel (a see-through gutter), or
  * lies inside another face that is not the face joined to it across that cube edge
    (another island's paint; a face whose rectangle overlaps this one is the same painting and
    counts as continuous), or
  * lies outside every face and is a clearly different colour from that edge texel.
A face edge that is transparent on purpose (a cut-out) is not flagged. Ring texels outside the
texture are fine: the textures use clamp wrapping.

Usage: python check_texture_bleed.py [paths or folders ...] [--faces] [--json out.json]
With no paths it checks godot-game/assets/models. Multi-texture models are only listed.
"""
import base64, glob, io, json, os, sys
from collections import defaultdict
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uv_padding import pixel_rect, inside_mask, _islands, _merge_overlaps

ROOT = os.path.normpath(os.path.join(os.path.dirname(os.path.abspath(__file__)), '..'))
DEFAULT = os.path.join(ROOT, 'godot-game', 'assets', 'models')
COLOUR_TOL = 24

# face -> (top-left, top-right, bottom-left) corners as fractions of the cube box, as Blockbench maps UV
CORNERS = {
    'south': ((0, 1, 1), (1, 1, 1), (0, 0, 1)), 'north': ((1, 1, 0), (0, 1, 0), (1, 0, 0)),
    'east': ((1, 1, 1), (1, 1, 0), (1, 0, 1)), 'west': ((0, 1, 0), (0, 1, 1), (0, 0, 0)),
    'up': ((0, 1, 0), (1, 1, 0), (0, 1, 1)), 'down': ((0, 0, 1), (1, 0, 1), (0, 0, 0)),
}
FACE_OF = {(0, 0): 'west', (0, 1): 'east', (1, 0): 'down', (1, 1): 'up', (2, 0): 'north', (2, 1): 'south'}
NORMAL_AXIS = {'west': 0, 'east': 0, 'down': 1, 'up': 1, 'north': 2, 'south': 2}


def load_texture(path, d):
    t = d['textures'][0]
    src = t.get('source', '')
    if src.startswith('data:'):
        im = Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1])))
    else:
        rel = t.get('relative_path') or ''
        cand = [os.path.normpath(os.path.join(os.path.dirname(path), rel))] if rel else []
        cand += [t.get('path') or '']
        f = next((c for c in cand if c and os.path.exists(c)), None)
        if not f:
            return None
        im = Image.open(f)
    return np.array(im.convert('RGBA'))


def tex_to_box(face, uv, u, v):
    """Texture point (u, v) in uv units on this face -> point on the unit cube (fractions)."""
    u1, v1, u2, v2 = uv
    ss = (u - u1) / (u2 - u1) if u2 != u1 else 0.5
    qq = (v - v1) / (v2 - v1) if v2 != v1 else 0.5
    rt = face.get('rotation', 0) or 0
    s, q = {0: (ss, qq), 90: (1 - qq, ss), 180: (1 - ss, 1 - qq), 270: (qq, 1 - ss)}[rt]
    tl, tr, bl = (np.array(p, float) for p in CORNERS[face['_name']])
    return tl + s * (tr - tl) + q * (bl - tl)


def box_to_tex(face, uv, p):
    """Point on the unit cube, on this face's plane -> texture point (uv units)."""
    tl, tr, bl = (np.array(c, float) for c in CORNERS[face['_name']])
    ex, ey = tr - tl, bl - tl
    s = float((p - tl) @ ex) / float(ex @ ex)
    q = float((p - tl) @ ey) / float(ey @ ey)
    rt = face.get('rotation', 0) or 0
    ss, qq = {0: (s, q), 90: (q, 1 - s), 180: (1 - s, 1 - q), 270: (1 - q, s)}[rt]
    u1, v1, u2, v2 = uv
    return u1 + (u2 - u1) * ss, v1 + (v2 - v1) * qq


def faces_of(d):
    out = []
    for ei, e in enumerate(d.get('elements', [])):
        if e.get('type', 'cube') != 'cube' or 'faces' not in e:
            continue
        for fn, f in e['faces'].items():
            if f.get('texture') is None or fn not in CORNERS:
                continue
            uv = f.get('uv')
            if not uv or (uv[0] == uv[2] or uv[1] == uv[3]):
                continue
            f = dict(f, _name=fn)
            out.append((ei, fn, f))
    return out


def check_model(path, faces_out=None):
    d = json.load(open(path, encoding='utf8'))
    texs = d.get('textures', [])
    if len(texs) != 1:
        return {'status': 'multi' if len(texs) > 1 else 'none'}
    T = load_texture(path, d)
    if T is None:
        return {'status': 'missing'}
    H, W = T.shape[:2]
    t = d['textures'][0]
    sx = W / float(t.get('uv_width') or d.get('resolution', {}).get('width') or W)
    sy = H / float(t.get('uv_height') or d.get('resolution', {}).get('height') or H)
    faces = faces_of(d)
    rects = [pixel_rect(f['uv'], sx, sy) for _, _, f in faces]
    owner = np.full((H, W), -1, int)
    for k, (x0, y0, x1, y1) in enumerate(rects):
        owner[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = k
    # shared paintings: faces whose rectangles overlap (directly or through others) are windows into
    # one painting; its bounding box is continuous paint for all of them
    isl, of = _islands(rects)
    groups, gof = _merge_overlaps(isl, of)
    by_elem = defaultdict(dict)
    for k, (ei, fn, f) in enumerate(faces):
        by_elem[ei][fn] = k
    A = T[..., 3].astype(int)
    rgb = T[..., :3].astype(int)
    flagged = 0
    reasons = defaultdict(int)
    for k, (ei, fn, f) in enumerate(faces):
        x0, y0, x1, y1 = rects[k]
        if x1 <= x0 or y1 <= y0:
            continue
        ring = []  # (ring texel, inner texel)
        for x in range(x0, x1):
            ring += [((x, y0 - 1), (x, y0)), ((x, y1), (x, y1 - 1))]
        for y in range(y0, y1):
            ring += [((x0 - 1, y), (x0, y)), ((x1, y), (x1 - 1, y))]
        ring += [((x0 - 1, y0 - 1), (x0, y0)), ((x1, y0 - 1), (x1 - 1, y0)),
                 ((x0 - 1, y1), (x0, y1 - 1)), ((x1, y1), (x1 - 1, y1 - 1))]
        bad = None
        for (rx, ry), (ix, iy) in ring:
            if not (0 <= rx < W and 0 <= ry < H) or not (0 <= ix < W and 0 <= iy < H):
                continue
            if A[iy, ix] == 0:
                continue  # transparent on purpose: its outside may stay transparent
            o = owner[ry, rx]
            g = groups[gof[k]]
            if g != rects[k] and g[0] - 1 <= rx <= g[2] and g[1] - 1 <= ry <= g[3]:
                # inside this face's shared painting, or its border: the painting's own edge texel
                cx, cy = min(max(rx, g[0]), g[2] - 1), min(max(ry, g[1]), g[3] - 1)
                if (T[ry, rx] == T[cy, cx]).all():
                    continue
            if o >= 0 and o != k:
                if not joined(faces, by_elem, k, o, (rx, ry), (ix, iy), sx, sy):
                    bad = 'other island'
                    break
                continue
            if o == k:
                continue
            if A[ry, rx] < A[iy, ix]:
                bad = 'transparent gutter'
                break
            if np.abs(rgb[ry, rx] - rgb[iy, ix]).max() > COLOUR_TOL:
                bad = 'wrong colour'
                break
        if bad:
            flagged += 1
            reasons[bad] += 1
            if faces_out is not None:
                faces_out.append((path, d['elements'][ei].get('name'), fn, bad))
    return {'status': 'ok', 'faces': len(faces), 'flagged': flagged, 'reasons': dict(reasons), 'size': (W, H)}


def overlaps(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def joined(faces, by_elem, k, o, ring_px, inner_px, sx, sy):
    """Is ring texel ring_px (inside face o) where face k's edge continues onto its neighbour?"""
    ei, fn, f = faces[k]
    ej, gn, g = faces[o]
    if ei != ej:
        return False
    # the cube point at the shared edge, from the middle of the inner texel pushed to the edge
    ix, iy = inner_px
    rx, ry = ring_px
    u = (ix + 0.5 + (rx - ix) * 0.5) / sx
    v = (iy + 0.5 + (ry - iy) * 0.5) / sy
    p = tex_to_box(f, f['uv'], u, v)
    axis = NORMAL_AXIS[gn]
    side = 1 if g['_name'] in ('east', 'up', 'south') else 0
    if abs(p[axis] - side) > 1e-3:
        return False  # that edge does not touch face o
    gu, gv = box_to_tex(g, g['uv'], p)
    # the matching texel on o sits just inside o's edge at that point
    tx, ty = int(np.floor(gu * sx)), int(np.floor(gv * sy))
    return abs(tx - rx) <= 1 and abs(ty - ry) <= 1


def collect(args):
    paths = []
    for a in args or [DEFAULT]:
        if os.path.isdir(a):
            paths += glob.glob(os.path.join(a, '**', '*.bbmodel'), recursive=True)
        else:
            paths.append(a)
    return sorted(os.path.normpath(p) for p in paths)


def main():
    argv = sys.argv[1:]
    show_faces = '--faces' in argv
    out_json = None
    if '--json' in argv:
        out_json = argv[argv.index('--json') + 1]
        argv = [a for i, a in enumerate(argv) if a != '--json' and argv[i - 1] != '--json']
    argv = [a for a in argv if a != '--faces']
    rows = defaultdict(lambda: [0, 0, 0])
    listed = []
    face_log = [] if show_faces else None
    results = {}
    for p in collect(argv):
        r = check_model(p, face_log)
        results[os.path.relpath(p, ROOT).replace('\\', '/')] = r
        folder = os.path.relpath(os.path.dirname(p), ROOT).replace('\\', '/')
        if r['status'] != 'ok':
            listed.append((p, r['status']))
            continue
        row = rows[folder]
        row[0] += 1
        row[1] += r['flagged'] > 0
        row[2] += r['flagged']
    print('| Folder | Models checked | Models with flagged faces | Flagged faces |')
    print('|---|---:|---:|---:|')
    tot = [0, 0, 0]
    for folder in sorted(rows):
        a, b, c = rows[folder]
        tot = [tot[0] + a, tot[1] + b, tot[2] + c]
        print(f'| {folder} | {a} | {b} | {c} |')
    print(f'| **Total** | {tot[0]} | {tot[1]} | {tot[2]} |')
    if listed:
        print('\nNot checked (listed only):')
        for p, s in listed:
            print(f'  {os.path.relpath(p, ROOT)}: {s} texture(s)' if s in ('multi', 'none') else f'  {os.path.relpath(p, ROOT)}: {s}')
    if face_log:
        print('\nFlagged faces:')
        for p, n, fn, why in face_log:
            print(f'  {os.path.relpath(p, ROOT)}  {n}.{fn}: {why}')
    if out_json:
        json.dump(results, open(out_json, 'w'), indent=1)


if __name__ == '__main__':
    main()
