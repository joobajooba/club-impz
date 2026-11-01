"""Repaints the texture of an existing Blockbench model to the texture recipe in
docs/blockbench_detailed_prompts.md (sections 1.5, 3.5, 3.9), keeping its boxes, UV layout,
groups and animations exactly as they are.

  python enrich_textures.py tool  <in.bbmodel> <out.bbmodel> <out.png>   doubles the texture (4 px per unit)
  python enrich_textures.py mob   <in.bbmodel> <out.bbmodel> [out.png]   same size (2 px per unit)

For every face area in the texture (from the faces' UVs):
  - small clusters of noise, one shade either way, in 2x2 groups, never single-pixel static,
  - wood (tools): grain lines along the long side of the face, a darker groove every few pixels,
  - metal and stone (tools): a few short diagonal scratches, light with a dark pixel beside,
  - fur and skin (mobs): short strands, one pixel wide, running down the face,
  - a one-shade highlight along the top edge and a contact shadow along the bottom edge,
  - no pure black or white.
Tiny areas (eyes, gems, pupils: under 3 texels a side before doubling) and near-black or very
bright saturated texels (outlines, glows) are left alone, so faces keep their character.
The result is deterministic: the same model always gets the same pixels.
"""
import base64
import colorsys
import io
import json
import sys
import zlib

import numpy as np
from PIL import Image


def load_texture(src):
    data = base64.b64decode(src.split(",", 1)[1])
    return np.array(Image.open(io.BytesIO(data)).convert("RGBA")).astype(np.int16)


def rects_of(model, tex_index, uv_scale):
    """Unique face areas of one texture, in texture pixels: (x0, y0, x1, y1, face)."""
    seen = {}
    for e in model["elements"]:
        for face, f in e.get("faces", {}).items():
            if f.get("texture") != tex_index or "uv" not in f:
                continue
            u0, v0, u1, v1 = (c * uv_scale for c in f["uv"])
            r = (int(round(min(u0, u1))), int(round(min(v0, v1))), int(round(max(u0, u1))), int(round(max(v0, v1))))
            if r[2] - r[0] >= 1 and r[3] - r[1] >= 1:
                seen.setdefault(r, face)
    return [(*r, face) for r, face in seen.items()]


def hsv(px):
    return colorsys.rgb_to_hsv(*(c / 255.0 for c in px[:3]))


def is_wood(px):
    h, s, v = hsv(px)
    return 0.03 <= h <= 0.13 and 0.25 <= s <= 0.8 and 0.12 <= v <= 0.72


def protected(px):
    h, s, v = hsv(px)
    return v < 0.09 or (v > 0.9 and s > 0.45)            # outlines and glowing bits


def nudge(px, k):
    """One shade lighter (k > 0, warmer) or darker (k < 0, cooler)."""
    r, g, b = px[:3]
    if k > 0:
        r, g, b = r + (255 - r) * 0.10 * k + 4 * k, g + (244 - g) * 0.10 * k + 2 * k, b + (214 - b) * 0.08 * k
    else:
        k = -k
        r, g, b = r * (1 - 0.11 * k), g * (1 - 0.11 * k), b * (1 - 0.07 * k) + 3 * k
    return [int(min(247, max(8, c))) for c in (r, g, b)] + [px[3]]


def rng_for(*key):
    return np.random.default_rng(zlib.crc32(repr(key).encode()))


def paint(img, rects, mode, min_side):
    out = img.copy()
    for x0, y0, x1, y1, face in rects:
        w, h = x1 - x0, y1 - y0
        if w < min_side and h < min_side:
            continue
        rng = rng_for(x0, y0, x1, y1, face)
        area = img[y0:y1, x0:x1]
        opaque = area[..., 3] > 0
        if not opaque.any():
            continue
        wood = sum(is_wood(area[j, i]) for j, i in zip(*np.nonzero(opaque))) > opaque.sum() * 0.5
        long_v = h >= w                                   # grain and strands run along the long side
        # 1. noise in 2x2 clusters, sparse: detail, not speckle
        chance = 0.14 if mode == "tool" else 0.05
        for cy in range(0, h, 2):
            for cx in range(0, w, 2):
                roll = rng.random()
                if roll < chance or roll > 1 - chance:
                    k = 1 if roll > 0.5 else -1
                    for yy in range(cy, min(cy + 2, h)):
                        for xx in range(cx, min(cx + 2, w)):
                            p = out[y0 + yy, x0 + xx]
                            if p[3] and not protected(p):
                                out[y0 + yy, x0 + xx] = nudge(p, k)
        # 2. material detail
        if mode == "tool" and wood:
            step = 3
            lines = range(rng.integers(0, step), w if long_v else h, step)
            for t in lines:
                for s in range(h if long_v else w):
                    if rng.random() < 0.82:
                        yy, xx = (s, t) if long_v else (t, s)
                        p = out[y0 + yy, x0 + xx]
                        if p[3] and not protected(p):
                            out[y0 + yy, x0 + xx] = nudge(p, -1)
        elif mode == "tool":
            for _ in range(max(1, (w * h) // 60)):
                sx, sy, ln = rng.integers(0, max(1, w)), rng.integers(0, max(1, h)), rng.integers(2, 5)
                for d in range(ln):
                    xx, yy = sx + d, sy + d
                    if xx < w and yy < h:
                        p = out[y0 + yy, x0 + xx]
                        if p[3] and not protected(p):
                            out[y0 + yy, x0 + xx] = nudge(p, 2)
                        if xx + 1 < w and out[y0 + yy, x0 + xx + 1][3] and not protected(out[y0 + yy, x0 + xx + 1]):
                            out[y0 + yy, x0 + xx + 1] = nudge(out[y0 + yy, x0 + xx + 1], -1)
        else:
            for _ in range((w * h) // 48):
                sx, sy, ln = rng.integers(0, max(1, w)), rng.integers(0, max(1, h)), rng.integers(2, 4)
                for d in range(ln):
                    xx, yy = (sx, sy + d) if long_v or face in ("up", "down") else (sx + d, sy)
                    if xx < w and yy < h:
                        p = out[y0 + yy, x0 + xx]
                        if p[3] and not protected(p):
                            out[y0 + yy, x0 + xx] = nudge(p, -1 if d else 1)
        # 3. light along the top edge, contact shadow along the bottom (side faces)
        if face not in ("up", "down") and h >= 3:
            for xx in range(w):
                p = out[y0, x0 + xx]
                if p[3] and not protected(p):
                    out[y0, x0 + xx] = nudge(p, 1)
                p = out[y1 - 1, x0 + xx]
                if p[3] and not protected(p):
                    out[y1 - 1, x0 + xx] = nudge(p, -1)
    return out


def main():
    mode, src, dst = sys.argv[1], sys.argv[2], sys.argv[3]
    png = sys.argv[4] if len(sys.argv) > 4 else None
    scale = 2 if mode == "tool" else 1
    model = json.load(open(src, encoding="utf-8"))
    for ti, t in enumerate(model["textures"]):
        img = load_texture(t["source"])
        uv_scale = img.shape[1] / t.get("uv_width", img.shape[1])
        if scale > 1:
            img = np.repeat(np.repeat(img, scale, axis=0), scale, axis=1)
        img = paint(img, rects_of(model, ti, uv_scale * scale), mode, min_side=3 * scale)
        buf = io.BytesIO()
        Image.fromarray(img.astype(np.uint8), "RGBA").save(buf, "PNG")
        t["source"] = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        t["path"] = ""                       # use the embedded texture, never an old file on disk
        t["relative_path"] = None
        if png and ti == 0:
            t["name"] = png.replace("\\", "/").split("/")[-1]
        for k in ("width", "height", "uv_width", "uv_height"):
            if k in t:
                t[k] = int(t[k] * scale)
        if png and ti == 0:
            open(png, "wb").write(buf.getvalue())
    if scale > 1:
        model["resolution"] = {k: v * scale for k, v in model["resolution"].items()}
        for e in model["elements"]:
            for f in e.get("faces", {}).values():
                if "uv" in f:
                    f["uv"] = [c * scale for c in f["uv"]]
    json.dump(model, open(dst, "w", encoding="utf-8"))


if __name__ == "__main__":
    main()
