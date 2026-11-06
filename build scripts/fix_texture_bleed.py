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
import base64, copy, decimal, io, json, os, re, sys
import numpy as np
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from uv_padding import pad_model, pixel_rect, inside_mask, textured_faces
import check_texture_bleed as chk


def png_bytes(arr):
    b = io.BytesIO()
    Image.fromarray(arr).save(b, 'PNG', optimize=True)
    return b.getvalue()


def decode(src):
    return np.array(Image.open(io.BytesIO(base64.b64decode(src.split(',', 1)[1]))).convert('RGBA'))


def js_numbers(text):
    """Blockbench (JavaScript) writes 6e-05 as 0.00006: match it."""
    def dec(m):
        return format(decimal.Decimal(m.group(0)), 'f')
    return re.sub(r'(?<![\w."])-?\d+(?:\.\d+)?e-0?[1-6](?![\d])', dec, text)


def json_writer(d, raw):
    """A function that writes d in the same layout as raw (separators, indent, number style)."""
    target = raw.rstrip('\n')
    for kw in (dict(separators=(',', ':')), dict(), dict(indent='\t'), dict(indent=1), dict(indent=2), dict(indent=4),
               dict(indent='\t', separators=(',', ': '))):
        for ea in (True, False):
            for post in (lambda x: x, js_numbers):
                f = lambda o, kw=kw, ea=ea, post=post: post(json.dumps(o, ensure_ascii=ea, **kw))
                if f(d) == target:
                    return f
    return None


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
    dump = json_writer(d, raw)
    assert dump is not None, f'{path}: cannot round-trip the JSON byte for byte'

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
    size_before = (W, H)
    info = {}
    T_new, moves = pad_model(d, T, info)
    repacked = bool(moves)
    written = int(((T_new[..., 3] > 0) & ~inside_mask(T_new.shape, [pixel_rect(f['uv'], sx, sy) for _, _, f in textured_faces(d)])).sum())

    # paint inside every face is unchanged
    new_faces = textured_faces(d)
    for (ei, fn, f0), (_, _, f1) in zip(textured_faces(orig), new_faces):
        a = pixel_rect(f0['uv'], sx, sy)
        b = pixel_rect(f1['uv'], sx, sy)
        assert (T[a[1]:a[3], a[0]:a[2]] == T_new[b[1]:b[3], b[0]:b[2]]).all(), f'{path}: paint changed in {fn}'
    assert strip_uv(orig) == strip_uv(d), f'{path}: something other than uv / texture size changed'

    if dry:
        return {'shared_paint': info.get('shared_paint', False), 'repacked': repacked, 'size': (size_before, T_new.shape[1::-1]), 'dilated': written}
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
    return {'shared_paint': info.get('shared_paint', False), 'repacked': repacked, 'size': (size_before, T_new.shape[1::-1]), 'dilated': written}


def fix_overlays(body_path, pngs, quiet=False):
    """Overlays painted in a body's texture layout (eye pupils, glow masks) get the body's moves and
    border. Run before the body itself is fixed (afterwards the moves are empty: border only)."""
    from uv_padding import pad_model as _pad, pad_overlay
    d = json.load(open(body_path, encoding='utf8'))
    T = decode(d['textures'][0]['source'])
    t = d['textures'][0]
    sx = T.shape[1] / float(t.get('uv_width') or T.shape[1])
    sy = T.shape[0] / float(t.get('uv_height') or T.shape[0])
    T_new, moves = _pad(d, T)
    islands = [[x, y, x + r[2] - r[0], y + r[3] - r[1]] for r, x, y in moves] if moves else \
        sorted({tuple(pixel_rect(f['uv'], sx, sy)) for _, _, f in textured_faces(d)})
    size = T_new.shape[0]
    for p in pngs:
        im = np.array(Image.open(p).convert('RGBA'))
        assert im.shape == T.shape, f'{p} is not in {body_path} layout'
        out = pad_overlay(im, [list(r) for r in islands], moves, size)
        # every overlay texel that was painted is still there, moved with its face
        assert (out[..., 3] > 0).sum() >= (im[..., 3] > 0).sum()
        with open(p, 'wb') as fh:
            fh.write(png_bytes(out))
        if not quiet:
            print(f'{os.path.basename(p):40s} overlay moved with {os.path.basename(body_path)}')


def pad_file(path, extra_pngs=()):
    """For the build scripts: pad a .bbmodel they have just written, exactly as the fix pass does,
    and write the padded texture to any extra PNG copies (the PNG next to the working file)."""
    r = fix(path)
    d = json.load(open(path, encoding='utf8'))
    t = d['textures'][0]
    if t.get('source', '').startswith('data:'):
        data = base64.b64decode(t['source'].split(',', 1)[1])
    else:
        data = open(os.path.normpath(os.path.join(os.path.dirname(path), t['relative_path'])), 'rb').read()
    for png in extra_pngs:
        with open(png, 'wb') as fh:
            fh.write(data)
    return r


if __name__ == '__main__':
    if sys.argv[1:2] == ['--overlays']:
        fix_overlays(sys.argv[2], sys.argv[3:])
        sys.exit()
    args = [a for a in sys.argv[1:] if a != '--dry']
    failed = []
    for p in args:
        try:
            r = fix(p, dry='--dry' in sys.argv)
        except (AssertionError, ValueError) as ex:
            failed.append((p, str(ex)))
            print(f'{os.path.basename(p):40s} NOT FIXED: {ex}')
            continue
        (w0, h0), (w1, h1) = r['size']
        print(f'{os.path.basename(p):40s} repacked={"yes" if r["repacked"] else "no ":3s} {w0}x{h0} -> {w1}x{h1}  border texels {r["dilated"]}{"  (shared-paint islands kept whole)" if r["shared_paint"] else ""}')
    if failed:
        print(f'\n{len(failed)} model(s) not fixed')
        sys.exit(1)
