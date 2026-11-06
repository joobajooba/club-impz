"""One rule for UV islands, used by the atlas packers and by the texture-bleed fix pass.

When a GPU draws a face, the pixels right on its edge can sample the texel just outside the face's
UV rectangle. If that texel is a transparent gutter or another face's paint, a thin line shows along
the cube edge. So:

  * islands sit GAP (2) texels apart and MARGIN (1) texel in from the texture border, so every
    island gets a 1 px border of its own;
  * dilate() copies each island's edge texels one texel outward (sides, plus the corner texel
    diagonally), exactly as they are: an opaque edge texel gives an opaque border texel, an edge
    texel that is transparent on purpose gives a transparent one. It never writes inside a face.

Texel density never changes: pack() only moves islands by whole pixels and grows the atlas to the
next power of two when they no longer fit.
"""
import numpy as np

GAP = 2
MARGIN = 1
SIZES = (64, 128, 256, 512, 1024, 2048)


def pack(sizes, gap=GAP, margin=MARGIN, square_sizes=SIZES):
    """Shelf-pack (w, h) islands, tallest first (then widest; ties keep their order).
    Returns (positions, size): positions[i] = (x, y) of island i in a size x size atlas."""
    order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0]))
    for size in square_sizes:
        pos = {}
        x = y = margin
        shelf = 0
        ok = True
        for i in order:
            w, h = sizes[i]
            if x + w + margin > size:
                x, y, shelf = margin, y + shelf + gap, 0
            if y + h + margin > size or w + 2 * margin > size:
                ok = False
                break
            pos[i] = (x, y)
            x += w + gap
            shelf = max(shelf, h)
        if ok:
            return [pos[i] for i in range(len(sizes))], size
    raise ValueError('islands do not fit in %d px' % square_sizes[-1])


def pixel_rect(uv, sx=1.0, sy=1.0):
    """A face's uv [u1, v1, u2, v2] (either direction) as whole texels [x0, y0, x1, y1) of the image."""
    u1, v1, u2, v2 = uv
    a, b = sorted((u1 * sx, u2 * sx))
    c, d = sorted((v1 * sy, v2 * sy))
    e = 1e-6
    return [int(np.floor(a + e)), int(np.floor(c + e)), int(np.ceil(b - e)), int(np.ceil(d - e))]


def inside_mask(shape, rects):
    m = np.zeros(shape[:2], bool)
    for x0, y0, x1, y1 in rects:
        m[max(y0, 0):max(y1, 0), max(x0, 0):max(x1, 0)] = True
    return m


def dilate(atlas, rects):
    """Give every island a 1 px border copied from its own edge texels. Writes only texels outside
    every rectangle; returns the number written."""
    H, W = atlas.shape[:2]
    taken = inside_mask(atlas.shape, rects)
    n = 0
    for x0, y0, x1, y1 in rects:
        if x1 <= x0 or y1 <= y0:
            continue
        # (destination, source) strips: four sides, then the four corners diagonally
        jobs = []
        for x in range(x0, x1):
            jobs += [((x, y0 - 1), (x, y0)), ((x, y1), (x, y1 - 1))]
        for y in range(y0, y1):
            jobs += [((x0 - 1, y), (x0, y)), ((x1, y), (x1 - 1, y))]
        jobs += [((x0 - 1, y0 - 1), (x0, y0)), ((x1, y0 - 1), (x1 - 1, y0)),
                 ((x0 - 1, y1), (x0, y1 - 1)), ((x1, y1), (x1 - 1, y1 - 1))]
        for (dx, dy), (sx, sy) in jobs:
            if 0 <= dx < W and 0 <= dy < H and not taken[dy, dx]:
                atlas[dy, dx] = atlas[sy, sx]
                taken[dy, dx] = True
                n += 1
    return n


def textured_faces(d):
    """(element index, face name, face dict) of every drawn face, in file order (the packers' order)."""
    out = []
    for ei, e in enumerate(d.get('elements', [])):
        for fn, f in e.get('faces', {}).items():
            uv = f.get('uv')
            if f.get('texture') is None or not uv or uv[0] == uv[2] or uv[1] == uv[3]:
                continue
            out.append((ei, fn, f))
    return out


def _islands(rects):
    """Each distinct face rectangle is one island; faces with the same rectangle share it.
    Rectangles that only partly overlap (a horn tip reusing horn paint) become separate islands,
    each with its own copy of the shared pixels, so every face keeps exactly its paint and its
    edge never touches another face. Returns (island rects, island index of each face)."""
    islands = []
    for r in rects:
        if list(r) not in islands:
            islands.append(list(r))
    return islands, [islands.index(list(r)) for r in rects]


def _overlap(a, b):
    return a[0] < b[2] and b[0] < a[2] and a[1] < b[3] and b[1] < a[3]


def _merge_overlaps(islands, island_of):
    """Shared-paint islands: rectangles that overlap become one island (their bounding box)."""
    g = [list(r) for r in islands]
    owner = list(range(len(g)))
    changed = True
    while changed:
        changed = False
        live = sorted(set(owner))
        for i in live:
            for j in live:
                if j > i and _overlap(g[i], g[j]):
                    a, b = g[i], g[j]
                    g[i] = [min(a[0], b[0]), min(a[1], b[1]), max(a[2], b[2]), max(a[3], b[3])]
                    owner = [i if o == j else o for o in owner]
                    changed = True
                    break
            if changed:
                break
    keys = sorted(set(owner))
    return [g[k] for k in keys], [keys.index(owner[k]) for k in island_of]


def needs_repack(islands, W, H):
    for i, a in enumerate(islands):
        if a[0] < MARGIN or a[1] < MARGIN or a[2] > W - MARGIN or a[3] > H - MARGIN:
            return True
        for b in islands[i + 1:]:
            if max(b[0] - a[2], a[0] - b[2], b[1] - a[3], a[1] - b[3]) < GAP:
                return True
    return False


def pad_model(d, T, info=None):
    """Give a one-texture .bbmodel dict d (texture pixels T, RGBA) padded, dilated UV islands.
    Changes only face uv values and the texture's width/height/uv_width/uv_height, in place.
    Returns (new texture, moves) where moves = [(src rect, dst x, dst y)] (empty if not repacked);
    apply_moves() repeats the same move on another image painted in the same layout."""
    t = d['textures'][0]
    H, W = T.shape[:2]
    sx = W / float(t.get('uv_width') or W)
    sy = H / float(t.get('uv_height') or H)
    faces = textured_faces(d)
    for ei, fn, f in faces:
        for v, s in zip(f['uv'], (sx, sy, sx, sy)):
            if abs(v * s - round(v * s)) > 1e-6:
                raise ValueError(f'{d["elements"][ei].get("name")}.{fn}: uv {f["uv"]} is not on whole texels')
    rects = [[max(0, min(c, lim)) for c, lim in zip(pixel_rect(f['uv'], sx, sy), (W, H, W, H))] for _, _, f in faces]
    islands, island_of = _islands(rects)
    moves = []
    overlapping = any(_overlap(a, b) for i, a in enumerate(islands) for b in islands[i + 1:])
    if needs_repack(islands, W, H) or overlapping:
        fits = [s for s in SIZES if s >= max(W, H)]
        sizes = [(r[2] - r[0], r[3] - r[1]) for r in islands]
        pos, size = pack(sizes, square_sizes=fits)
        if overlapping:
            # Faces that are windows into one shared painting: copying every window out keeps each
            # face's edge clean but can blow the atlas up (hub_castle: 512 -> 2048). If keeping each
            # shared painting whole gives a smaller atlas, do that: the edge then reads the next
            # texel of the same painting, never a gutter or another island.
            m_islands, m_of = _merge_overlaps(islands, island_of)
            m_pos, m_size = pack([(r[2] - r[0], r[3] - r[1]) for r in m_islands], square_sizes=fits)
            if m_size < size:
                islands, island_of, pos, size = m_islands, m_of, m_pos, m_size
                if info is not None:
                    info['shared_paint'] = True
        moves = [(r, x, y) for r, (x, y) in zip(islands, pos)]
        for (ei, fn, f), k in zip(faces, island_of):
            r, x, y = moves[k]
            dx, dy = (x - r[0]) / sx, (y - r[1]) / sy
            f['uv'] = [_num(v + o) for v, o in zip(f['uv'], (dx, dy, dx, dy))]
        t['width'] = t['height'] = size
        t['uv_width'], t['uv_height'] = _num(size / sx), _num(size / sy)
        T = apply_moves(T, moves, size)
        islands = [[x, y, x + r[2] - r[0], y + r[3] - r[1]] for r, x, y in moves]
    else:
        T = T.copy()
    dilate(T, islands)
    return T, moves


def apply_moves(img, moves, size):
    out = np.zeros((size, size, 4), np.uint8)
    for (x0, y0, x1, y1), x, y in moves:
        out[y:y + y1 - y0, x:x + x1 - x0] = img[y0:y1, x0:x1]
    return out


def pad_overlay(img, islands_after, moves, size):
    """An overlay painted in a model's texture layout (eye pupils, glow masks): same moves, same border."""
    out = apply_moves(img, moves, size) if moves else img.copy()
    dilate(out, islands_after)
    return out


def _num(v):
    return int(round(v)) if abs(v - round(v)) < 1e-9 else v
