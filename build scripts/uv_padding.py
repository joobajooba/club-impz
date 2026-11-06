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
