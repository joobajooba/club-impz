"""Fix texture bleeding in committed .bbmodel files: repack every UV island with 2 px gaps and dilate
its edge by 1 px (uv_padding.py), without changing a single texel inside any face.

Usage: python fix_texture_bleed.py <model.bbmodel> ... [--dry]

For each model:
  * reads its one texture (embedded, and the PNG at relative_path if there is one; they must match);
  * if islands sit closer than 2 px (or touch the border), repacks them, moving each face's pixels
    and its uv together by whole pixels, in the same order the atlas packers use; the atlas grows
    to the next power of two only if needed (width, height, uv_width, uv_height follow);
  * dilates every island;
  * writes the texture back to the embedded source and to the PNG, then verifies:
    paint inside every face identical (through the new uv), everything but uv and texture size
    fields identical, and check_texture_bleed reports 0 flagged faces.
Geometry, groups, bones and animations are never touched.
"""
import base64, copy, io, json, os, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uv_padding import GAP, MARGIN, pack, dilate, pixel_rect
import check_texture_bleed as chk


def png_bytes(arr):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, 'PNG', optimize=True)
    return b.getvalue()


def decode(src):
    return np.array(Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA'))


def textured_faces(d):
    """(element index, face name, face dict) in file order, which is the packers' order."""
    out = []
    for ei, e in enumerate(d['elements']):
        for fn, f in e.get('faces', {}).items():
            uv = f.get('uv')
            if f.get('texture') is None or not uv or uv[0] == uv[2] or uv[1] == uv[3]:
                continue
            out.append((ei, fn, f))
    return out


def needs_repack(rects, W, H):
    for i, a in enumerate(rects):
        if a[0] < MARGIN or a[1] < MARGIN or a[2] > W - MARGIN or a[3] > H - MARGIN:
            return True
        for b in rects[i + 1:]:
            gx = max(b[0] - a[2], a[0] - b[2])
            gy = max(b[1] - a[3], a[1] - b[3])
            if max(gx, gy) < GAP:
                return True
    return False


def strip_uv(d):
    """The model with every uv and texture size/source field blanked, for the 'nothing else changed' check."""
    d = copy.deepcopy(d)
    for e in d['elements']:
        for f in e.get('faces', {}).values():
            f.pop('uv', None)
    for t in d.get('textures', []):
        for k in ('width', 'height', 'uv_width', 'uv_height', 'source'):
            t.pop(k, None)
    return d


def fix(path, dry=False):
    raw = open(path, encoding='utf8').read()
    d = json.loads(raw)
    # write the JSON back in the file's own layout, so only the changed values differ
    styles = [dict(separators=(',', ':')), dict(indent='\t'), dict(indent=2), dict(indent='\t', separators=(',', ': ')),
              dict(separators=(',', ':'), ensure_ascii=False), dict(indent='\t', ensure_ascii=False)]
    style = next((s for s in styles if json.dumps(d, **s) == raw.rstrip('\n')), None)
    assert style is not None, f'{path}: cannot round-trip the JSON byte for byte'
    dump = lambda o: json.dumps(o, **style)
    orig = copy.deepcopy(d)
    t = d['textures'][0]
    assert len(d['textures']) == 1, 'one texture only'
    emb = t.get('source', '').startswith('data:')
    png = os.path.normpath(os.path.join(os.path.dirname(path), t['relative_path'])) if t.get('relative_path') else None
    if png and not os.path.exists(png):
        png = None
    T = decode(t['source']) if emb else np.array(Image.open(png).convert('RGBA'))
    if emb and png:
        P = np.array(Image.open(png).convert('RGBA'))
        assert P.shape == T.shape and (P == T).all(), f'{path}: embedded texture and PNG differ before the fix'
    H, W = T.shape[:2]
    uw, uh = float(t.get('uv_width') or W), float(t.get('uv_height') or H)
    sx, sy = W / uw, H / uh
    faces = textured_faces(d)
    rects = [pixel_rect(f['uv'], sx, sy) for _, _, f in faces]
    # faces that share one rectangle are one island
    island_of, islands = [], []
    for r in rects:
        if r not in islands:
            islands.append(r)
        island_of.append(islands.index(r))
    for (ei, fn, f), r in zip(faces, rects):
        assert all(abs(v * s - round(v * s)) < 1e-6 for v, s in zip(f['uv'], (sx, sy, sx, sy))), \
            f'{path}: {d["elements"][ei]["name"]}.{fn} uv is not on whole texels'
    for i, a in enumerate(islands):
        for b in islands[i + 1:]:
            if a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]:
                raise ValueError(f'{path}: islands {a} and {b} overlap; not repacked automatically')

    repacked = needs_repack(islands, W, H)
    size_before = (W, H)
    if repacked:
        sizes = [(r[2] - r[0], r[3] - r[1]) for r in islands]
        start = [s for s in (64, 128, 256, 512, 1024, 2048) if s >= max(W, H)]
        pos, size = pack(sizes, square_sizes=start)
        N = np.zeros((size, size, 4), np.uint8)
        for (x0, y0, x1, y1), (nx, ny) in zip(islands, pos):
            N[ny:ny + y1 - y0, nx:nx + x1 - x0] = T[y0:y1, x0:x1]
        for (ei, fn, f), k in zip(faces, island_of):
            dx = (pos[k][0] - islands[k][0]) / sx
            dy = (pos[k][1] - islands[k][1]) / sy
            u1, v1, u2, v2 = f['uv']
            nu = [u1 + dx, v1 + dy, u2 + dx, v2 + dy]
            f['uv'] = [int(round(v)) if abs(v - round(v)) < 1e-9 else v for v in nu]
        # density stays the same: uv units per texel are unchanged
        t['width'] = t['height'] = size
        t['uv_width'], t['uv_height'] = size / sx, size / sy
        for k in ('uv_width', 'uv_height'):
            if float(t[k]).is_integer():
                t[k] = int(t[k])
        new_islands = [[nx, ny, nx + r[2] - r[0], ny + r[3] - r[1]] for r, (nx, ny) in zip(islands, pos)]
        T_new = N
    else:
        new_islands = islands
        T_new = T.copy()
    written = dilate(T_new, new_islands)

    # paint inside every face is unchanged
    new_faces = textured_faces(d)
    for (ei, fn, f0), (_, _, f1) in zip(textured_faces(orig), new_faces):
        a = pixel_rect(f0['uv'], sx, sy)
        b = pixel_rect(f1['uv'], sx, sy)
        assert (T[a[1]:a[3], a[0]:a[2]] == T_new[b[1]:b[3], b[0]:b[2]]).all(), f'{path}: paint changed in {fn}'
    assert strip_uv(orig) == strip_uv(d), f'{path}: something other than uv / texture size changed'

    if dry:
        return {'repacked': repacked, 'size': (size_before, T_new.shape[1::-1]), 'dilated': written}
    data = png_bytes(T_new)
    if emb:
        t['source'] = 'data:image/png;base64,' + base64.b64encode(data).decode()
    out = dump(d)
    with open(path, 'w', encoding='utf8', newline='') as fh:
        fh.write(out + ('\n' if raw.endswith('\n') else ''))
    if png:
        with open(png, 'wb') as fh:
            fh.write(data)
    # verify what is on disk
    d2 = json.load(open(path, encoding='utf8'))
    if emb:
        E = decode(d2['textures'][0]['source'])
        assert (E == T_new).all()
    if png:
        P = np.array(Image.open(png).convert('RGBA'))
        assert P.shape == T_new.shape and (P == T_new).all(), f'{path}: PNG differs from the embedded texture'
    r = chk.check_model(path)
    assert r['flagged'] == 0, f'{path}: still {r["flagged"]} flagged faces {r["reasons"]}'
    return {'repacked': repacked, 'size': (size_before, T_new.shape[1::-1]), 'dilated': written}


if __name__ == '__main__':
    args = [a for a in sys.argv[1:] if a != '--dry']
    for p in args:
        r = fix(p, dry='--dry' in sys.argv)
        (w0, h0), (w1, h1) = r['size']
        print(f'{os.path.basename(p):40s} repacked={"yes" if r["repacked"] else "no ":3s} {w0}x{h0} -> {w1}x{h1}  border texels {r["dilated"]}')
