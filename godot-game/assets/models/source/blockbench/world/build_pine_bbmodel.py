"""Build the pine: a world tree as a Blockbench model, at the HD Imp's scale and
texture density (D-117, D-118). The oak's companion; it reuses the oak's
geometry helpers and numpy painter (build_oak_bbmodel.py).

- 3 times the Imp's height: 222 px = 3.47 m, like the oak. Geometry in px of
  0.25 units, 64 per metre; the texture 8 pixels per unit, 128 per metre.
- A triangular conifer: nine tiers of branches, each a stepped pyramid (a
  wide skirt, a middle layer, a top layer), every layer two squares turned
  45 degrees on each other so it reads as an octagon. The tiers shrink and
  turn as they climb, to a spire. Branch tips droop over the edge of each
  skirt, cones hang under the middle tiers.
- A tapering trunk with root flares, dead twigs and a broken stub low down,
  where a pine sheds its shaded branches.
- Painted detail: dark green needle sprays (a twig with needles in a
  herringbone down each side, a deeper darker layer between), lighter fresh
  growth at the branch tips, scaly pine bark (plates split by deep fissures,
  flaking in layers, red-brown below and turning orange up the trunk), resin
  runs, lichen, grey weathered dead wood, end grain on the stub, scaled cones.
  Baked light from the cone the tree stands for, ambient occlusion sampled
  from the real geometry, lit top edges.

Usage: python build_pine_bbmodel.py [out_dir]   (writes pine.bbmodel,
pine.png, pine_preview.png, pine_silhouette.png and pine_render.png)
"""

import math
import random
import sys
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent))
from build_oak_bbmodel import (HEIGHT_PX, PX_HD, SUB, WOOD, LICHEN, Oak, bark_frame,  # noqa: E402
                               face_coords, fbm3, grad, hash3, light, limb, ramp, rbox, root,
                               smooth, tube_normal, unit, vnoise2)
import bbcreature  # noqa: E402  (build_oak_bbmodel put it on the path)
from bbcreature import NORMAL, corners, el  # noqa: E402

# Ramps, darkest first.
NEEDLE = ramp("#081a14", "#0e2a1c", "#163a24", "#1f4d2d", "#2a6036", "#367440", "#47894c",
              "#62a05c", "#86ba72")
NEEDLE_COOL = ramp("#081a1a", "#0e2a26", "#163a32", "#1f4c3e", "#2a5f4c", "#38735c", "#4b8a6e",
                   "#66a184", "#88bb9c")
FRESH = ramp("#08200f", "#15381b", "#245226", "#376c30", "#52893c", "#73a44c", "#9cc263")
BARK = ramp("#140c0e", "#24151a", "#3b2020", "#562c24", "#74392a", "#954a30", "#b6603a", "#d47e4c")
ORANGE = ramp("#2a1410", "#53261a", "#7f3a22", "#a8532c", "#cb6e38", "#e48f50", "#f2b276")
RESIN = ramp("#4a2408", "#8a4a10", "#c77a1c", "#eaa93a", "#ffe08a", "#fff6d0")
CONE = ramp("#1e110a", "#3c2414", "#5e3a20", "#82552e", "#a6743f", "#c99a5c", "#e2bd84")
DEAD = ramp("#2a2622", "#4a433b", "#6d645a", "#918878", "#b5ad9b", "#d6cfbd")


# ---------------------------------------------------------------- geometry

TRUNK = [
    *rbox("trunk_base", "trunk", "bark", (-11, 0, -11), (11, 22, 11), 4, axis=1),
    *rbox("trunk_low", "trunk", "bark", (-9, 22, -9), (9, 70, 9), 3, axis=1),
    *rbox("trunk_mid", "trunk", "bark", (-7, 70, -7), (7, 140, 7), 2, axis=1),
    *rbox("trunk_top", "trunk", "bark", (-5, 140, -5), (5, 200, 5), 2, axis=1),
]

ROOTS = [b for r in (root("root_e", 12, 9, 10, inner=6, width=10), root("root_n", 10, 8, 85, inner=6, width=10),
                     root("root_w", 12, 8, 190, inner=6, width=8), root("root_s", 10, 9, -80, inner=6, width=10),
                     root("root_sw", 9, 6, -140, inner=6, width=8))
         for b in r]
for _e in ROOTS:
    _e["axis"] = 0

# Dead twigs and a broken stub on the bare lower trunk.
DEADWOOD = []
for _name, _base, _rx, _rz, _len, _w in (
        ("twig_dead_e", (6, 30, 1), 6, -72, 16, 4),
        ("twig_dead_n", (-1, 26, -6), -68, 8, 13, 4),
        ("twig_dead_w", (-6, 36, -1), -4, 66, 11, 4)):
    _boxes, _ = limb(_name, _base, _rx, _rz, _len, _w, 1)
    for _e in _boxes:
        _e["part"] = "deadwood"
    DEADWOOD += _boxes
_stub, _ = limb("stub", (2, 16, 8), 62, -12, 9, 6, 1, stub=True)
DEADWOOD += _stub

TIERS = 9
CROWN, TIER_INFO = [], []


def tier(i, y0, H, R, spin):
    """One tier of branches: a stepped pyramid of three layers, each two
    squares turned 45 degrees on each other, with branch tips drooping over
    the skirt."""
    rng = random.Random(f"pine{i}")
    info = {"tier": i, "y0": y0, "H": H, "R": R}
    out = []
    for lname, ya, yb, k in (("skirt", 0, 6, 1.0), ("mid", 5, round(0.6 * H), 0.74),
                             ("top", round(0.55 * H), H, 0.44)):
        for c, (turn, shrink, inset) in enumerate(((0, 1.0, 0.0), (45, 0.95, 0.5))):
            r = max(2, round(R * k * shrink))
            out.append(el(f"tier{i}_{lname}_{'ab'[c]}", "crown", "needles",
                          (-r, y0 + ya + inset, -r), (r, y0 + yb - inset, r), (0, spin + turn, 0), (0, 0, 0)))
    # Drooping branch tips round the skirt, a lower tip beyond each.
    n = max(5, round(R / 7))
    for k in range(n):
        ang = spin + 22.5 + 360 * k / n + rng.uniform(-10, 10)
        w = 10 if R > 30 else 8
        reach = R + rng.choice((2, 3, 4))
        out.append(el(f"tier{i}_droop{k}", "crown", "needles", (round(R * 0.7), y0 - 3, -w / 2),
                      (reach, y0 + 3, w / 2), (0, ang, 0), (0, 0, 0)))
        w2 = w - 4
        tip = el(f"tier{i}_tip{k}", "crown", "needles", (reach - 5, y0 - 6, -w2 / 2),
                 (reach + 3, y0 - 1, w2 / 2), (0, ang + rng.uniform(-6, 6), 0), (0, 0, 0))
        tip["tip"] = True
        out.append(tip)
    for e in out:
        e.update(info)
    # Cones hanging under the middle tiers.
    cones = []
    if 2 <= i <= 6:
        for k in range(2 if i < 6 else 1):
            ang = rng.uniform(0, 360)
            d = round(R * rng.uniform(0.5, 0.62))
            cones.append(el(f"cone{i}_{k}", "crown", "cone", (d - 2, y0 - 7, -2), (d + 2, y0, 2),
                            (0, ang, 0), (0, 0, 0)))
    return out, cones, info


_y0 = 44.0
CONES = []
for _i in range(TIERS):
    _f = _i / (TIERS - 1)
    _H = round(36 - 16 * _f)
    _R = round(62 - 48 * _f)
    _boxes, _cones, _info = tier(_i, round(_y0), _H, _R, (_i * 19) % 45)
    CROWN += _boxes
    CONES += _cones
    TIER_INFO.append(_info)
    _y0 += 0.6 * _H

# The spire above the last tier.
_last = TIER_INFO[-1]
SPIRE = [el("spire", "crown", "needles", (-4, _last["y0"] + _last["H"] - 6, -4), (4, 214, 4)),
         el("spire_tip", "crown", "needles", (-2, 212, -2), (2, HEIGHT_PX, 2))]
for _e in SPIRE:
    _e.update(tier=TIERS, y0=_last["y0"] + _last["H"] - 6, H=HEIGHT_PX - _last["y0"] - _last["H"] + 6,
              R=6, tip=True)

ELEMENTS = TRUNK + ROOTS + DEADWOOD + CROWN + SPIRE + CONES

BONES = {
    "pine": (None, (0, 0, 0), (0, 0, 0)),
    "trunk": ("pine", (0, 0, 0), (0, 0, 0)),
    "crown": ("trunk", (0, 30, 0), (0, 0, 0)),
}

# Resin runs on the trunk, in world px: where each starts and how far it runs.
RESIN_RUNS = [((11, 13, 2), 6.0), ((-3, 48, -9), 8.0), ((-9, 34, 3), 5.0), ((6, 58, 9), 7.0)]


# ---------------------------------------------------------------- painting

def spray_layer(a, b, cell, seed, theta):
    """Needle sprays on a jittered grid in face coordinates (a, b) px, each a
    twig pointing theta (radians, per texel) with needles fanning forward off
    both sides. Returns covered, spray id (0..1), t (-1 base .. 1 tip), across
    (-1..1), along and across in px."""
    n = a.shape[0]
    best = np.full(n, -1.0)
    lid, tt, across, lupx, lvpx = (np.zeros(n) for _ in range(5))
    ia, ib = np.floor(a / cell), np.floor(b / cell)
    for da in (-1, 0, 1):
        for db in (-1, 0, 1):
            ca, cb = ia + da, ib + db
            h = [hash3(ca, cb, seed + 3.1 * k, seed) for k in range(6)]
            cx = (ca + 0.15 + 0.7 * h[0]) * cell
            cy = (cb + 0.15 + 0.7 * h[1]) * cell
            s = cell * (1.5 + 0.5 * h[2])
            th = theta + (h[3] - 0.5) * 1.1
            dx, dy = a - cx, b - cy
            lu = dx * np.cos(th) + dy * np.sin(th)
            lv = -dx * np.sin(th) + dy * np.cos(th)
            t = lu / (0.5 * s)
            hw = s * 0.3 * np.sqrt(np.clip(1 - t * t, 0, 1)) * (1.05 - 0.3 * t)
            inside = (np.abs(t) < 1) & (np.abs(lv) < hw)
            upd = inside & (h[4] > best)
            best = np.where(upd, h[4], best)
            lid = np.where(upd, h[5], lid)
            tt = np.where(upd, t, tt)
            across = np.where(upd, lv / np.maximum(hw, 1e-6), across)
            lupx = np.where(upd, lu, lupx)
            lvpx = np.where(upd, lv, lvpx)
    return best >= 0, lid, tt, across, lupx, lvpx


def paint_needles(F):
    q, e = F.q, F.e
    rad = np.hypot(q[:, 0], q[:, 2])
    radial = np.stack([q[:, 0], np.zeros(len(q)), q[:, 2]], 1) / np.maximum(rad, 1e-6)[:, None]
    cone_n = unit(radial + np.array((0, 0.55, 0)))
    nmix = unit(0.55 * cone_n + 0.45 * np.array(F.n))
    v = light(nmix) + 0.04
    v -= 0.5 * F.ao
    v += 0.07 * F.edge
    v += 0.06 * np.clip((q[:, 1] - 120) / 100, -1, 1)          # the crown lightens upward
    frac = np.clip((q[:, 1] - e["y0"]) / e["H"], 0, 1)
    v -= 0.08 * (1 - frac) * (abs(F.n[1]) < 0.7)               # in the shade of the layer above
    if F.n[1] < -0.7:
        v -= 0.14
    a, b, side = face_coords(F)
    theta = -math.pi / 2 if side else np.arctan2(b, a)          # sides: hanging; top: radiating out

    # The deep layer: bigger, darker sprays showing through the gaps.
    dcov, did, dt, dac, _, _ = spray_layer(a, b, 6.5, 21.0, theta)
    deep = v - 0.27 + 0.05 * (did - 0.5) - 0.05 * (np.abs(dac) > 0.8)
    deep = np.where(dcov, deep, v - 0.4)
    # The front layer: a twig, needles in a herringbone, a darker rim.
    cov, lid, t, ac, lu, lv = spray_layer(a, b, 4.0, 5.0, theta)
    g = (lu - 1.15 * np.abs(lv)) / 1.1
    needle = (g - np.floor(g)) < 0.5
    fv = v + 0.09 * (lid - 0.5)
    fv += np.where(needle, 0.05, -0.06)
    fv -= 0.12 * ((np.abs(lv) < 0.3) & (np.abs(t) < 0.9))      # the twig
    fv -= 0.07 * (np.abs(ac) > 0.82)
    fv += 0.05 * (t > 0.5)                                      # tips catch the light
    v = np.where(cov, fv, deep)
    v += 0.02 * (hash3(q[:, 0] * 2, q[:, 1] * 2, q[:, 2] * 2) - 0.5)

    col = grad(NEEDLE, v)
    # Cooler blue-green patches.
    cool = smooth(0.5, 0.72, fbm3(q * 0.03, 31.0, 2))[:, None] * 0.55
    col = col * (1 - cool) + grad(NEEDLE_COOL, v) * cool
    # Fresh growth at the ends of the branches: lighter, yellower.
    rr = rad / max(e["R"], 1)
    fresh = smooth(0.96, 1.1, rr)
    if e.get("tip"):
        fresh = np.maximum(fresh, 0.6)
    fresh = fresh * cov * (t > 0.1) * (0.35 + 0.4 * (hash3(lid, 7.0, 3.0) > 0.5))
    col = col * (1 - fresh[:, None]) + grad(FRESH, v - 0.04) * fresh[:, None]
    return col


def voronoi(x, y, seed):
    """Nearest and second-nearest distances and the nearest cell's id."""
    ix, iy = np.floor(x), np.floor(y)
    d1, d2, cid = np.full(len(x), 9.0), np.full(len(x), 9.0), np.zeros(len(x))
    for dx in (-1, 0, 1):
        for dy in (-1, 0, 1):
            cx, cy = ix + dx, iy + dy
            px = cx + 0.1 + 0.8 * hash3(cx, cy, seed)
            py = cy + 0.1 + 0.8 * hash3(cx, cy, seed + 1)
            d = np.hypot(x - px, y - py)
            closer = d < d1
            d2 = np.where(closer, d1, np.minimum(d2, d))
            cid = np.where(closer, hash3(cx, cy, seed + 2), cid)
            d1 = np.where(closer, d, d1)
    return d1, d2, cid


def end_grain(F, base):
    """Sawn or broken end of a branch: rings round the pith, a bark rim."""
    e = F.e
    lo, hi = e["lo"], e["hi"]
    r = np.hypot(F.p[:, 0] - (lo[0] + hi[0]) / 2, F.p[:, 2] - (lo[2] + hi[2]) / 2)
    rim = r > (hi[0] - lo[0]) / 2 - 0.8
    v = 0.55 + 0.1 * np.sin(r * 3.4) - 0.12 * (r < 0.6) - 0.3 * F.ao
    return np.where(rim[:, None], grad(BARK, base - 0.05), grad(WOOD, v))


def paint_bark(F):
    q, e = F.q, F.e
    n = np.array(F.n)
    nn = tube_normal(F) if "tube" in e else np.repeat(n[None, :], len(q), 0)
    base = light(nn)
    base -= 0.45 * F.ao
    base += 0.06 * F.edge
    base -= 0.2 * np.clip(1 - q[:, 1] / 8, 0, 1)               # into the ground
    if e.get("stub") and NORMAL[F.f][1] == 1:
        return end_grain(F, base)
    along, around = bark_frame(F)
    around = around + hash3(np.array(float(F.ei)), 1.0, 2.0) * 50
    upper = smooth(60, 130, q[:, 1])                             # thinner, orange bark up high

    # Scaly plates, taller than wide, split by fissures that close up higher.
    warp = 0.35 * (vnoise2(along * 0.08, around * 0.15, 5.0) - 0.5)
    sx = around / (3.6 - 1.2 * upper) + warp
    sy = along / (7.0 - 3.0 * upper)
    d1, d2, cid = voronoi(sx, sy, 3.0)
    gap = d2 - d1
    width = 0.16 - 0.08 * upper
    v = base + 0.1 * (cid - 0.5)
    v += 0.05 * np.minimum(np.floor(gap * 4 + 0.6 * vnoise2(sx * 3, sy * 3, 7.0)), 3)  # flaking layers
    v += 0.06 * (sy - np.floor(sy) > 0.75) * (gap > width)      # lit upper lips
    v += 0.04 * (vnoise2(around * 2.0, along * 0.4, 9.0) - 0.5)
    v += 0.03 * (hash3(q[:, 0] * 2, q[:, 1] * 2, q[:, 2] * 2, 3.0) - 0.5)
    fissure = gap < width
    v = np.where(fissure, base - 0.32 + 0.12 * (gap / width), v)
    col = grad(BARK, v)
    flake = (upper * (0.45 + 0.4 * (cid > 0.5)) * ~fissure)[:, None]
    col = col * (1 - flake) + grad(ORANGE, v + 0.04) * flake

    # Resin: amber runs down from a wound, a bead at the bottom, a highlight.
    for (p, length) in RESIN_RUNS:
        dq = q - np.array(p, float)
        hor = np.hypot(dq[:, 0], dq[:, 2])
        wobble = 0.25 * np.sin(dq[:, 1] * 1.3)
        run = (np.abs(hor - np.abs(wobble)) < 0.9 - 0.25 * (-dq[:, 1] / length)) & \
            (dq[:, 1] < 0.8) & (dq[:, 1] > -length)
        bead = np.hypot(hor, dq[:, 1] + length) < 1.2
        rv = 0.5 + 0.3 * (dq[:, 1] > -1.5) - 0.25 * F.ao + 0.3 * (np.abs(hor - 0.3) < 0.25)
        col = np.where((run | bead)[:, None], grad(RESIN, rv), col)
    # Lichen low on the shaded north side.
    lc = np.floor(q / 5.0)
    pick = hash3(lc[:, 0], lc[:, 1], lc[:, 2], 12.0) < 0.12
    lp = (lc + 0.5) * 5.0
    lr = 0.7 + 1.2 * hash3(lc[:, 0], lc[:, 1], lc[:, 2], 13.0)
    lich = pick & (np.linalg.norm(q - lp, axis=1) < lr) & (q[:, 1] > 4) & (q[:, 1] < 60) & (nn[:, 2] < 0.2)
    col = np.where(lich[:, None], grad(LICHEN, base + 0.2 + 0.1 * np.sin(q[:, 0] * 3 + q[:, 1] * 2)), col)
    return col


def paint_deadwood(F):
    """Dead twigs, bark long gone: grey weathered wood split along the grain."""
    nn = tube_normal(F)
    base = light(nn) - 0.45 * F.ao + 0.06 * F.edge
    along, around = bark_frame(F)
    v = base + 0.12 * (vnoise2(around * 2.5, along * 0.3, 21.0) - 0.5)
    v -= 0.2 * (vnoise2(around * 3.0, along * 0.15, 22.0) > 0.75)   # cracks
    if NORMAL[F.f][1] == 1:
        v = base + 0.12 - 0.1 * (vnoise2(F.p[:, 0] * 3, F.p[:, 2] * 3, 23.0) > 0.7)  # the broken end
    return grad(DEAD, v)


def paint_cone(F):
    """A pine cone: rows of woody scales, each lit along its lower lip."""
    e = F.e
    p = F.p
    n = np.array(F.n)
    lo, hi = e["lo"], e["hi"]
    cx, cz = (lo[0] + hi[0]) / 2, (lo[2] + hi[2]) / 2
    base = light(np.repeat(n[None, :], len(p), 0)) - 0.45 * F.ao + 0.05 * F.edge
    nl = NORMAL[F.f]
    if nl[1]:
        r = np.hypot(p[:, 0] - cx, p[:, 2] - cz)
        v = base + 0.08 * np.cos(r * 4.0) - (0.2 if nl[1] > 0 else 0.05) * (r < 0.8)
        return grad(CONE, v)
    around = p[:, 2] if nl[0] else p[:, 0]
    row = np.floor((p[:, 1] - lo[1]) / 1.25)
    fy = (p[:, 1] - lo[1]) / 1.25 - row
    col_ = (around + 0.75 * (row % 2)) / 1.5
    fx = col_ - np.floor(col_)
    v = base + 0.05
    v += 0.13 * (fy < 0.4) - 0.14 * (fy > 0.8)                  # lit lip, shadow under the next row
    v -= 0.16 * (np.minimum(fx, 1 - fx) < 0.17)
    v -= 0.12 * ((p[:, 1] - lo[1]) / (hi[1] - lo[1]) > 0.85)    # dark where it hangs from the twig
    return grad(CONE, v)


PAINTERS = {"bark": paint_bark, "needles": paint_needles, "deadwood": paint_deadwood, "cone": paint_cone}

PINE = Oak("pine", ELEMENTS, BONES, PAINTERS, {})

if __name__ == "__main__":
    out = Path(sys.argv[1] if len(sys.argv) > 1 else Path(__file__).resolve().parent)
    out.mkdir(parents=True, exist_ok=True)
    bbcreature.PX = PX_HD
    m = PINE
    top = max(m.world(e, c)[1] for e in m.elements for c in corners(e))
    assert abs(top - HEIGHT_PX) < 1e-6, f"height {top} px, want {HEIGHT_PX}"
    m.paint()
    m.previews(out, scale=1.5, tile=(440, 400), anchor=0.94)
    m.write_bbmodel(out)
    m.hero(out / "pine_render.png", [(-145, 12), (35, 12), (180, 2)])
    print(f"boxes: {len(m.elements)}  visible faces: {len(m.visible)}  "
          f"texture: {m.tex * SUB}x{m.tex * SUB} (uv {m.tex})  "
          f"texels used: {sum(w * h for w, h in m.visible.values()) * SUB * SUB}/{(m.tex * SUB) ** 2}  "
          f"height: {top:.1f} px = {top / 64:.3f} m")
