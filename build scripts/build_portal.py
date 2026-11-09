"""World portal (J00BA, 2026-11-09): "very large, 3 times the height of the player, wide enough to fit 4 Impz,
slightly rounded with a flat base, metallic obsidian rock; inside a red effect of animated swirls".
Imp = 18 tall and about 12.3 wide (ears included), so the opening is 52 wide x 44 tall and the arch top is at 57.
Frame: faceted metallic obsidian voussoirs on stepped pillars and a flat stepped base, with shards and red runes.
Inside: an opaque glowing backdrop shaped to the arch, then hard alpha swirl cards (front and back) in their own
groups, spun by a looping `idle` animation (90 degree keys so glTF slerp keeps the direction), a pulsing core and
rising embers. Glow parts end in _glow. Front = north (-z).
Usage: py build_portal.py"""
import os, sys, math, uuid, zlib
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from station_lib import Station, StationPainter, station_mats, R, C, F, px, h2, LO, grid
from foliage_lib import ramp

OUT = r"C:\Users\lucas\blockbench_models\props\portals"
R.update({
    "obsidian": ramp("#07040c #100a1a #1a1028 #261838 #34224c #462e64 #5e4482 #8a74b4 #c8bce6"),
    "portal_red": ramp("#2a0408 #4a080e #760e14 #a8181a #d42e22 #f05a34 #fc9a5a #fed2a0"),
})
HALF, Y0, SPRING, RISE = 26.0, 4.0, 36.0, 12.0          # opening: x +-26, y 4..48, arch from y 36
CY, RAD = 26.0, 22.0                                    # swirl centre and radius


class PortalPainter(StationPainter):
    def obsidian(self, w, h, cat, red=0.0):
        """Faceted volcanic glass with a metal finish: Voronoi facets each with its own tilted gradient, crisp
        light edges on the facets facing the light, a reflection band, dark centre-light form, and optionally the
        portal's red light bleeding onto faces that look into the opening."""
        nr = self.nr; yy, xx = grid(w, h)
        n = max(4, w * h // 45)
        pts = np.array([(nr.uniform(-2, w + 2), nr.uniform(-2, h + 2)) for _ in range(n)])
        d = np.stack([np.hypot(xx - x, yy - y) for x, y in pts]); o = np.sort(d, axis=0); idx = np.argmin(d, axis=0)
        edge = o[1] - o[0]
        gxy = nr.normal(0, 0.18, (n, 2)); base = nr.normal(0, 0.45, n)
        cx, cy = pts[idx][..., 0], pts[idx][..., 1]
        v = 3.0 + LO[cat] + base[idx] + gxy[idx, 0] * (xx - cx) + gxy[idx, 1] * (yy - cy)
        lit_edge = (edge < 1.0) & ((gxy[idx, 0] + gxy[idx, 1]) < 0)
        v[lit_edge] += 1.6
        v[(edge < 1.0) & ~lit_edge] -= 0.9
        if cat in ("lit", "shade", "up"):                       # metallic reflection band
            band = np.exp(-(((yy + 0.5) / h - 0.32 - 0.1 * np.sin(xx * 0.18)) / 0.1) ** 2)
            v += band * (1.6 if cat != "shade" else 0.9)
        v -= np.clip(np.maximum(np.abs((xx + .5) / w - .5), np.abs((yy + .5) / h - .5)) * 2 - 0.55, 0, 1) * 1.4
        v += self.noise(w, h, 0.08)
        rgb = C(R["obsidian"], v).astype(float)
        if cat == "lit":                                         # hot pin highlights on a few facet corners
            for _ in range(max(0, w * h // 500)):
                x, y = int(nr.integers(0, w)), int(nr.integers(0, h)); rgb[y, x] = R["obsidian"][8]
        if red:
            glow = C(R["portal_red"], 3.2 + np.clip(v - 2.5, 0, 3)).astype(float)
            t = red * np.clip(0.35 + 0.15 * (v - 3), 0.15, 0.6)
            rgb = rgb * (1 - t[..., None]) + glow * t[..., None]
        return rgb.round().astype(np.uint8), np.ones((h, w), bool)

    def backdrop(self, w, h):
        """The portal's surface behind the swirls: deep red, brightest in the middle, a few static spiral bands,
        a hot rim where it meets the stone; alpha cut to the arch."""
        yy, xx = grid(w, h)
        X = (xx + 0.5) / 2 - HALF; Y = (Y0 + (h - yy - 0.5) / 2)
        inside = (Y <= SPRING) | (((X / HALF) ** 2 + ((Y - SPRING) / RISE) ** 2) <= 1)
        r = np.hypot(X, (Y - CY) * 1.1) / RAD; th = np.arctan2(Y - CY, X)
        v = 5.2 - r * 2.6 + 0.6 * np.sin(3 * th + r * 9)
        ex = np.ones((h, w), bool); ex[1:-1, 1:-1] = inside[:-2, 1:-1] & inside[2:, 1:-1] & inside[1:-1, :-2] & inside[1:-1, 2:]
        rim = inside & ~ex | inside & ((xx < 2) | (xx >= w - 2) | (yy >= h - 2))
        v[rim] = 6.0
        return C(R["portal_red"], v + self.noise(w, h, 0.15)), inside

    def swirl(self, S, arms, twist, thr, r_in=0.0, gain=0.0):
        """Hard alpha spiral arms on a disk (the card spins, so only the arms show the motion)."""
        yy, xx = grid(S, S)
        X = (xx + 0.5) / S * 2 - 1; Y = (yy + 0.5) / S * 2 - 1
        r = np.hypot(X, Y); th = np.arctan2(Y, X)
        arm = np.sin(arms * th + twist * r * 2 * math.pi)
        a = (arm > thr) & (r < 0.98) & (r >= r_in)
        v = 4.0 + gain + (arm - thr) * 2.2 - r * 1.6 + (1 - r) * 1.2
        return C(R["portal_red"], v), a

    def core(self, S):
        yy, xx = grid(S, S)
        r = np.hypot((xx + 0.5) / S * 2 - 1, (yy + 0.5) / S * 2 - 1)
        th = np.arctan2((yy + .5) / S * 2 - 1, (xx + .5) / S * 2 - 1)
        a = r < 0.9 + 0.1 * np.sin(th * 7)
        return C(R["portal_red"], 7.0 - r * 3), a

    def rune(self, w, h, seed):
        """A red glowing rune: a stem with branches and a ring, hard alpha."""
        rng = np.random.default_rng(seed); yy, xx = grid(w, h)
        m = np.zeros((h, w), bool); cx = w // 2
        m[1:h - 1, cx] = True
        for _ in range(rng.integers(2, 4)):
            y0 = int(rng.integers(2, h - 3)); s = int(rng.choice([-1, 1])); L = int(rng.integers(2, w // 2))
            for k in range(L):
                y, x = y0 - k * (1 if rng.random() < 0.7 else 0), cx + s * (k + 1)
                if 0 <= y < h and 0 <= x < w: m[y, x] = True
        if rng.random() < 0.6:
            ry = int(rng.integers(3, h - 3))
            ring = np.abs(np.hypot(xx - cx, (yy - ry) * 1.0) - 1.6) < 0.6; m |= ring
        return C(R["portal_red"], np.full((h, w), 5.6) + (yy == 0) * 0.5), m


class Portal(Station):
    def __init__(self, *a, **k):
        super().__init__(*a, **k)
        self.P = PortalPainter(self.nr)
        self._mat_painters_fix()
        self.anims = []

    def obs(self, name, grp, frm, to, tag, red_faces=(), hide=("down",), rot=(0, 0, 0), origin=None):
        """An obsidian block; faces listed in red_faces get the portal's red light."""
        over = {}
        from stall_lib import CAT
        from house_lib import DIMS
        for f in red_faces:
            a, b = DIMS[f]; w, h = px(to[a] - frm[a]), px(to[b] - frm[b])
            if w and h:
                k = self.rect(f"{tag}_red_{f}_{w}x{h}", w, h, lambda W, H, c=CAT[f]: self.P.obsidian(W, H, c, red=1.0))
                over[f] = F(k)
        return self.item(name, grp, frm, to, tag, lambda W, H, c: self.P.obsidian(W, H, c), hide, rot, origin, over)


def ellipse_pt(t, a, b): return a * math.cos(t), SPRING + b * math.sin(t)


def portal():
    H = Portal("portal", 5101, station_mats())
    g = {k: H.group(k, [0, 0, 0]) for k in ("base", "pillars", "arch", "shards", "runes", "portal_surface", "embers")}
    # flat stepped base
    H.obs("base_step_1", g["base"], [-39, 0, -11], [39, 2, 11], "ob_base1")
    H.obs("base_step_2", g["base"], [-36, 2, -8.5], [36, 4, 8.5], "ob_base2")
    for s, sg in (("left", -1), ("right", 1)):
        x1, x2 = (-39.5, -35) if sg < 0 else (35, 39.5)
        H.obs(f"base_corner_{s}", g["base"], [x1, 0, -12], [x2, 3, -8], "ob_corner")
    # pillars: stacked irregular blocks, inner face on the opening
    heights = [7, 9, 8, 8]
    for s, sg in (("left", -1), ("right", 1)):
        y = Y0
        for i, hh in enumerate(heights):
            out = 35 + [0.5, -0.5, 1, 0][i] if sg > 0 else 35 + [0, 1, -0.5, 0.5][i]
            dz = 6
            x1, x2 = (HALF, out) if sg > 0 else (-out, -HALF)
            H.obs(f"pillar_{s}_{i + 1}", g["pillars"], [x1, y, -dz], [x2, y + hh, dz], f"ob_pil{i}",
                  red_faces=("west",) if sg > 0 else ("east",), hide=("down",) if i == 0 else ())
            y += hh
        # a plinth block and a capital that step out
        H.obs(f"pillar_{s}_foot", g["pillars"], [sg * HALF - (0 if sg > 0 else 11.5), Y0, -7] if sg < 0 else [HALF - 0.5, Y0, -7],
              [-HALF + 0.5, Y0 + 3, 7] if sg < 0 else [HALF + 11.5, Y0 + 3, 7], "ob_foot", red_faces=("west",) if sg > 0 else ("east",))
        H.obs(f"pillar_{s}_capital", g["pillars"], [-37.5, SPRING - 2.5, -7] if sg < 0 else [HALF - 0.5, SPRING - 2.5, -7],
              [-HALF + 0.5, SPRING, 7] if sg < 0 else [37.5, SPRING, 7], "ob_cap", red_faces=("west",) if sg > 0 else ("east",))
    # arch: voussoirs between the inner ellipse (26 x 12) and the outer (35 x 21)
    N = 11
    for i in range(N):
        t0, t1 = math.pi * i / N, math.pi * (i + 1) / N; tm = (t0 + t1) / 2
        xi, yi = ellipse_pt(tm, HALF, RISE); xo, yo = ellipse_pt(tm, 35, 21)
        rad_len = h2(math.hypot(xo - xi, yo - yi) + 1.0)
        p0, p1 = ellipse_pt(t0, 30.5, 16.5), ellipse_pt(t1, 30.5, 16.5)
        tan_len = h2(math.hypot(p1[0] - p0[0], p1[1] - p0[1]) * 1.12 + 0.5)
        cx, cy = (xi + xo) / 2, (yi + yo) / 2
        ang = math.degrees(math.atan2(yo - yi, xo - xi)) - 90
        dz = 7.0 if i % 2 else 6.5
        key = i == N // 2
        if key: dz, rad_len, tan_len = 7.5, rad_len + 2, tan_len + 1
        H.obs(f"arch_{'keystone' if key else 'stone_' + str(i + 1)}", g["arch"], [cx - tan_len / 2, cy - rad_len / 2, -dz],
              [cx + tan_len / 2, cy + rad_len / 2, dz], f"ob_arch{i % 2}{'k' if key else ''}", red_faces=("down",), hide=(),
              rot=(0, 0, ang), origin=[cx, cy, 0])
    # keystone gem front and back
    for s, z, f in (("front", -7.55, "north"), ("back", 7.55, "south")):
        gk = H.rect("gem_face", 8, 10, lambda W, Hh: H.P.core(max(W, Hh))[0][:Hh, :W] if False else H.P.form(R["portal_red"], W, Hh, "lit", 5.0, hl=True))
        H.item(f"keystone_gem_{s}_glow", g["arch"], [-2, 52, min(z, z + 0.5 * (1 if z > 0 else -1)) if False else (z - 0.5 if z < 0 else z)],
               [2, 57, (z if z < 0 else z + 0.5)], "gem", lambda W, Hh, c: H.P.form(R["portal_red"], W, Hh, c, 5.0, hl=True), hide=())
    # shards jutting from the arch's back edge, pillar sides and the base
    sh = [((-36, 44, 0), 3, 11, (0, 0, 35)), ((36, 44, 0), 3, 11, (0, 0, -35)), ((-21, 56, 1), 2.5, 9, (0, 0, 20)),
          ((22, 56, -1), 2.5, 8, (0, 0, -25)), ((0, 58.5, 0.5), 3, 7, (0, 0, -5)), ((-38, 12, 2), 3, 9, (0, 0, 40)),
          ((38, 18, -2), 3, 10, (0, 0, -45)), ((-37, 0, -12), 2.5, 7, (-30, 0, 20)), ((37, 0, 11), 3, 8, (30, 0, -25)),
          ((-30, 0, 12), 2, 5, (35, 0, 10)), ((31, 0, -12.5), 2, 6, (-35, 0, -15)), ((-12, 0, -12), 2, 4, (-40, 0, 0))]
    for i, ((x, y, z), w_, L, rot) in enumerate(sh):
        H.obs(f"shard_{i + 1}", g["shards"], [x - w_ / 2, y, z - w_ / 2], [x + w_ / 2, y + L, z + w_ / 2], f"ob_shard{i % 3}", hide=(),
              rot=rot, origin=[x, y, z])
        H.item(f"shard_{i + 1}_tip", g["shards"], [x - h2(w_ / 2) / 2, y + L, z - h2(w_ / 2) / 2], [x + h2(w_ / 2) / 2, y + L + 2, z + h2(w_ / 2) / 2], "shardtip",
               lambda W, Hh, c: H.P.obsidian(W, Hh, c), hide=(), rot=rot, origin=[x, y, z])
    # runes on the pillars, front and back
    for s, sg in (("left", -1), ("right", 1)):
        for j, y in enumerate((9, 18, 27)):
            for side, z in (("front", -6.05), ("back", 6.05)):
                k = H.rect(f"rune_{s}_{j}", 8, 12, lambda W, Hh, sd=zlib.crc32(f"{s}{j}".encode()) % 1000: H.P.rune(W, Hh, sd))
                x = sg * 30.5
                H.card(f"rune_{s}_{j + 1}_{side}_glow", g["runes"], [x - 2, y, z], [x + 2, y + 6, z], k,
                       faces=("north", "south") if side == "front" else ("south", "north"))
    # the portal surface: backdrop + spinning swirls front and back + pulsing core
    ps = g["portal_surface"]
    bk = H.rect("portal_backdrop", px(2 * HALF), px(SPRING + RISE - Y0), lambda W, Hh: H.P.backdrop(W, Hh))
    H.card("portal_backdrop_glow", ps, [-HALF, Y0, 0], [HALF, SPRING + RISE, 0], bk)
    S = px(2 * RAD)
    layers = [("swirl_large", 2 * RAD, 3, 0.9, 0.15, 0.0, 0.0, 360), ("swirl_mid", 32, 5, -1.3, 0.35, 0.1, 0.4, -720),
              ("swirl_small", 18, 4, 1.6, 0.25, 0.0, 0.8, 1080)]
    spins = []
    for li, (nm, D, arms, tw, thr, rin, gain, deg) in enumerate(layers):
        k = H.rect(nm, px(D), px(D), lambda W, Hh, a=arms, t=tw, th=thr, ri=rin, gn=gain: H.P.swirl(W, a, t, th, ri, gn))
        for side, sgn in (("front", -1), ("back", 1)):
            z = sgn * 0.4 * (li + 1)
            grp = H.group(f"{nm}_{side}", [0, CY, z], ps)
            H.card(f"{nm}_{side}_glow", grp, [-D / 2, CY - D / 2, z], [D / 2, CY + D / 2, z], k,
                   faces=("north", "south") if side == "front" else ("south", "north"))
            spins.append((grp, deg * (1 if side == "front" else -1)))
    ck = H.rect("portal_core", 16, 16, lambda W, Hh: H.P.core(W))
    pulses = []
    for side, sgn in (("front", -1), ("back", 1)):
        grp = H.group(f"core_{side}", [0, CY, sgn * 1.6], ps)
        H.card(f"core_{side}_glow", grp, [-4, CY - 4, sgn * 1.6], [4, CY + 4, sgn * 1.6], ck,
               faces=("north", "south") if side == "front" else ("south", "north"))
        pulses.append(grp)
    # embers drifting up in front of and behind the portal
    em = []
    for i, (x, z, y0) in enumerate(((-18, -3, 6), (-6, -4, 14), (9, -3.5, 9), (20, -2.5, 18), (-12, 3, 10), (4, 4, 5), (16, 3, 13), (-22, -2, 22))):
        grp = H.group(f"ember_{i + 1}", [x, y0, z], g["embers"])
        s = 0.5 if i % 3 else 1.0
        H.item(f"ember_{i + 1}_glow", grp, [x - s / 2, y0, z - s / 2], [x + s / 2, y0 + s, z + s / 2], f"ember{s}",
               lambda W, Hh, c: H.P.form(R["portal_red"], W, Hh, c, 4.6, noise=0), hide=())
        em.append((grp, y0))

    # ---- the idle animation (4 s loop)
    def kf(channel, t, xyz, interp="linear"):
        return {"channel": channel, "data_points": [{"x": str(xyz[0]), "y": str(xyz[1]), "z": str(xyz[2])}],
                "uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "time": t, "color": -1, "interpolation": interp}
    animators = {}
    T = 4.0
    for grp, deg in spins:
        steps = int(abs(deg) // 90)
        keys = [kf("rotation", round(T * k / steps, 4), (0, 0, round(deg * k / steps, 3))) for k in range(steps + 1)]
        animators[H.m.groups[grp]["uuid"]] = {"name": grp, "type": "bone", "keyframes": keys}
    for grp in pulses:
        keys = [kf("scale", t, (s, s, 1), "catmullrom") for t, s in ((0, 0.85), (1, 1.15), (2, 0.85), (3, 1.15), (4, 0.85))]
        animators[H.m.groups[grp]["uuid"]] = {"name": grp, "type": "bone", "keyframes": keys}
    for i, (grp, y0) in enumerate(em):
        rise = 34 - y0; off = (i * 0.37) % 1.0
        t_top = round(T * (1 - off), 3)
        keys = [kf("position", 0, (0, round(rise * off, 2), 0)), kf("position", t_top, (0, rise, 0)),
                kf("position", min(T, round(t_top + 0.05, 3)), (0, 0, 0)), kf("position", T, (0, round(rise * off, 2), 0))]
        keys += [kf("scale", 0, (1, 1, 1)), kf("scale", t_top, (0.2, 0.2, 0.2)), kf("scale", min(T, round(t_top + 0.05, 3)), (1, 1, 1))]
        animators[H.m.groups[grp]["uuid"]] = {"name": grp, "type": "bone", "keyframes": keys}
    anim = {"uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "name": "idle", "loop": "loop", "override": False,
            "length": T, "snapping": 24, "selected": False, "anim_time_update": "", "blend_weight": "", "start_delay": "",
            "loop_delay": "", "animators": animators}
    orig = H.m.bbmodel
    def with_anim():
        d = orig(); d["animations"] = [anim]; return d
    H.m.bbmodel = with_anim
    return H


if __name__ == "__main__":
    portal().finish([OUT])
