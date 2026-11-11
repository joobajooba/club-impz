"""Wizard tower for the hub (J00BA, 2026-11-09: "a very very tall wizard tower, in the same brick, have a point roof,
make it detailed and very fantasy like"). "The same brick" = the hub castle's limestone ashlar (hub_castle v2 STONE ramp,
its 8x5 px block painter), the material used by the castle portal and the castle-style lamps.

blockbench_detailed_prompts.md sections 1, 2, 3.11 (props and buildings), 4, 5. 2 px per unit, 512 texture, front =
north (-z), light from the top front left. Built on station_lib -> stall_lib -> house_lib (the swatch method).

Layout, bottom to top (all stages are true octagons made of 4 crossed bars, so every side is a flat face):
  plinth (cobble + ashlar step), front stairs, 4 diagonal buttresses
  stage 1  arched door with voussoirs, two lanterns (light_1, light_2), windows, ivy
  cornice + corbels
  stage 2  arched windows, oculus, violet banners
  balcony 1 on stepped corbels, crenellated parapet; a side turret with its own witch-hat cone stands on it
  stage 3  arched windows; a spiral of slit windows runs up stages 1 to 3 (the stair inside)
  flared corbel rings + brackets carrying the overhanging top chamber
  top chamber: big arched windows lit violet (a wizard silhouette in the front one), glowing rune band, a front
               balcony with an iron railing and a brass telescope on a tripod
  eave + a tall crooked witch-hat cone in midnight-blue scale tiles with gold star tiles, two dormers
  finial: gold rod, collars, a glowing orb and a gold crescent moon
  four floating crystals round the top chamber (idle animation: they bob and spin, the orb turns)
"""
import math, os, sys, uuid
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import numpy as np
from station_lib import Station, StationPainter, station_mats, R, C, F, px, h2, LO, CAT, grid
from foliage_lib import ramp
from house_lib import OPP

OUT = r"C:\Users\lucas\blockbench_models\buildings"
T225 = math.tan(math.radians(22.5))

R.update({
    "tile_midnight": ramp("#0c0c26 #14183c #1e2656 #2a3672 #3a4a8e #5262aa #7282c4"),
    "arcane": ramp("#2a0c5a #461a8a #6630b8 #8a52dc #ac80f0 #ceb4f8 #ece0fc"),
    "banner": ramp("#1e0a34 #2e1250 #42206c #58308a #7044a6 #8c60c0 #aa82d6"),
    "ivy": ramp("#0a1e14 #102e1c #184226 #225832 #2e6e3c #3e864a #56a05c"),
    "brass": ramp("#3a240c #5a3a12 #7c561c #9e7428 #be943a #d8b458 #ecd284"),
    "rune_stone": ramp("#14141e #1c1c2a #262636 #323244 #404054 #505066 #62627a"),
    "crystal": ramp("#06303e #0c5468 #148090 #26aab4 #4ccad0 #8ce4e4 #cef6f4"),
})


class TowerPainter(StationPainter):
    def ashlar(self, Rm, w, h, light, top=False, shadow_top=False):
        """hub_castle v2's ashlar: blocks 8x5 px (12x8 on tops), 1 px mortar, a smooth gradient down each block, light
        top edge, darker bottom edge, soft weather stains running down, darker lower courses."""
        nr = self.nr
        bw, bh = (12, 8) if top else (8, 5)
        base = (4.4 if top else 3.5) + light
        v = np.full((h, w), base); mortar = np.zeros((h, w), bool)
        for r, y0 in enumerate(range(0, h, bh + 1)):
            off = (bw + 1) // 2 if r % 2 else 0
            for x0 in range(-off, w, bw + 1):
                b = nr.normal(0, 0.18)
                for yy in range(y0, min(h, y0 + bh)):
                    t = (yy - y0) / max(1, bh - 1)
                    v[yy, max(0, x0):min(w, x0 + bw)] = base + b + 0.45 - 0.9 * t
                if y0 < h: v[y0, max(0, x0):min(w, x0 + bw)] += 0.55
                if y0 + bh - 1 < h: v[y0 + bh - 1, max(0, x0):min(w, x0 + bw)] -= 0.35
                if 0 <= x0 + bw < w: mortar[y0:min(h, y0 + bh + 1), x0 + bw] = True
            if y0 + bh < h: mortar[y0 + bh, :] = True
        v += self.noise(w, h, 0.15)
        if not top:
            for _ in range(max(1, w * h // 900)):
                x = int(nr.integers(0, max(1, w - 2))); y = int(nr.integers(0, max(1, h - 8))); L = int(nr.integers(8, 22))
                n = len(range(y, min(h, y + L)))
                v[y:y + n, x:x + int(nr.integers(1, 3))] -= np.linspace(0.45, 0.05, n)[:, None]
            v += self.vfall(h, 0.8, 0.5)
            if shadow_top: v[:6, :] -= np.linspace(1.0, 0.1, 6)[:, None]
        rgb = C(Rm, v)
        rgb[mortar] = C(Rm, np.full(mortar.sum(), base - 1.9))
        return rgb, np.ones((h, w), bool)

    def arcane_pane(self, w, h, arch=True, figure=False):
        """Magic window glass: violet light brightest low in the middle, dark violet lead cames in a diamond lattice,
        a soft darker top; optionally the wizard's silhouette (pointed hat, robe) standing inside."""
        yy, xx = grid(w, h)
        u = (xx + 0.5) / w - 0.5; t = (yy + 0.5) / h
        v = 2.3 + 3.4 * np.clip(1 - np.hypot(u * 1.5, (t - 0.64) * 1.05) * 1.55, 0, 1) - np.clip(0.25 - t, 0, 1) * 3
        v += self.noise(w, h, 0.12, 30)
        rgb = C(R["arcane"], v)
        if figure:
            cx = w * 0.5
            for y in range(h):
                tt = (y + 0.5) / h
                if 0.3 < tt <= 0.52:                                   # hat: a leaning cone
                    half = (tt - 0.3) / 0.22 * w * 0.16
                    c = cx + (0.52 - tt) * w * 0.35
                    xs = [x for x in range(w) if abs(x + 0.5 - c) <= half + 0.3]
                elif 0.52 < tt <= 0.56:                                # brim
                    xs = [x for x in range(w) if abs(x + 0.5 - cx) <= w * 0.24]
                elif tt > 0.56:                                        # head and shoulders, then the robe widening
                    half = w * (0.1 if tt < 0.64 else 0.14 + (tt - 0.64) * 0.45)
                    xs = [x for x in range(w) if abs(x + 0.5 - cx) <= half]
                else:
                    xs = []
                for x in xs: rgb[y, x] = C(R["arcane"], np.array(0.6 + tt * 0.4))
        lead = (xx == 0) | (xx == w - 1) | (yy == h - 1)
        if w >= 6 and not figure:
            lead |= ((xx + yy) % 5 == 0) | ((xx - yy) % 5 == 0)
        rgb[lead] = C(R["rune_stone"], np.full((h, w), 1.5))[lead]
        a = np.ones((h, w), bool)
        if arch:
            R0 = w / 2
            a = ~((yy + 0.5 < R0) & (np.hypot(xx + 0.5 - w / 2, R0 - (yy + 0.5)) > R0))
            rim = a & (np.hypot(xx + 0.5 - w / 2, R0 - (yy + 0.5)) > R0 - 1.1) & (yy + 0.5 < R0)
            rgb[rim] = C(R["rune_stone"], np.full((h, w), 1.5))[rim]
        return rgb, a

    def runes(self, w, h, cat):
        """Rune band: dark slate strip, centre lighter; glowing glyphs (strokes, dots, crossed bars) every 6 px."""
        yy, xx = grid(w, h)
        if cat in ("up", "down"): return self.form(R["rune_stone"], w, h, cat, 2.6)
        v = 2.4 + LO[cat] - np.abs((yy + 0.5) / h - 0.5) * 1.2 + self.noise(w, h, 0.1)
        rgb = C(R["rune_stone"], v)
        glyph = np.zeros((h, w), bool)
        for x0 in range(1, w - 3, 6):
            k = int(self.nr.integers(0, 6)); y0 = max(0, (h - 3) // 2)
            pts = {0: [(0, 0), (0, 1), (0, 2), (1, 1), (2, 0), (2, 2)], 1: [(1, 0), (0, 1), (2, 1), (1, 2), (1, 1)],
                   2: [(0, 0), (1, 1), (2, 2), (0, 2), (2, 0)], 3: [(0, 0), (1, 0), (2, 0), (1, 1), (1, 2)],
                   4: [(0, 2), (1, 1), (2, 0), (0, 0), (1, 2)], 5: [(0, 0), (0, 1), (0, 2), (1, 2), (2, 2), (2, 1)]}[k]
            for dx, dy in pts:
                if 0 <= x0 + dx < w and 0 <= y0 + dy < h: glyph[y0 + dy, x0 + dx] = True
        rgb[glyph] = C(R["arcane"], 5.2 + self.noise(w, h, 0.4, 4))[glyph]
        halo = ~glyph & (np.roll(glyph, 1, 1) | np.roll(glyph, -1, 1) | np.roll(glyph, 1, 0) | np.roll(glyph, -1, 0))
        rgb[halo] = C(R["arcane"], np.full((h, w), 2.0))[halo]
        return rgb, np.ones((h, w), bool)

    def banner(self, w, h):
        """Violet banner: soft vertical folds, gold border and top band, a gold crescent moon and star, swallowtail."""
        yy, xx = grid(w, h)
        u = (xx + 0.5) / w - 0.5; t = (yy + 0.5) / h
        v = 3.4 + 0.55 * np.sin((xx + 0.5) / w * math.pi * 3) - np.abs(u) * 1.2 - t * 0.6 + self.noise(w, h, 0.1)
        rgb = C(R["banner"], v)
        G = R["gold"]
        border = (xx == 1) | (xx == w - 2) | (yy == 2) | (yy == 3)
        rgb[border] = C(G, 4.2 - t * 1.6 + np.zeros((h, w)))[border]
        cx, cy, r = w / 2, h * 0.3, w * 0.27
        d1 = np.hypot(xx + 0.5 - cx, yy + 0.5 - cy); d2 = np.hypot(xx + 0.5 - cx - r * 0.55, yy + 0.5 - cy + r * 0.25)
        moon = (d1 <= r) & (d2 > r * 0.85)
        rgb[moon] = C(G, 4.6 - (yy - cy) / max(1, r) * 0.8)[moon]
        sx, sy = int(w / 2), int(h * 0.56)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1), (0, -2), (0, 2), (2, 0), (-2, 0)):
            if 0 <= sx + dx < w and 0 <= sy + dy < h: rgb[sy + dy, sx + dx] = G[5] if (dx, dy) == (0, 0) else G[4]
        notch = w * 0.55
        a = ~(yy + 0.5 > h - notch * (1 - np.abs(u) * 2))
        tail = a & (yy + 0.5 > h - notch * (1 - np.abs(u) * 2) - 1.2) & (t > 0.6)
        rgb[tail] = C(G, np.full((h, w), 3.2))[tail]
        return rgb, a

    def ivy(self, w, h):
        """Ivy: stems wandering up from the bottom with 2-3 px leaves, thick at the foot, thinning out higher up."""
        nr = self.nr
        rgb = np.zeros((h, w, 3), np.uint8); a = np.zeros((h, w), bool)
        I = R["ivy"]
        for s in range(max(2, w // 4)):
            x = float(nr.uniform(1, w - 1)); top = int(h * nr.uniform(0.05, 0.6))
            for y in range(h - 1, top, -1):
                x += nr.normal(0, 0.45); x = min(w - 1.0, max(0.0, x)); xi = int(x)
                a[y, xi] = True; rgb[y, xi] = I[1]
                p = 0.55 * (0.35 + 0.65 * y / h)
                if nr.random() < p:
                    lx = xi + int(nr.choice([-2, -1, 1])); ly = y
                    for dx, dy in ((0, 0), (1, 0), (0, -1), (1, -1)):
                        X, Y = lx + dx, ly + dy
                        if 0 <= X < w and 0 <= Y < h:
                            a[Y, X] = True
                            rgb[Y, X] = I[int(np.clip(3 + (1 if dy < 0 else 0) + (1 if dx == 0 else 0) + nr.integers(-1, 2) - (y > h * 0.8), 1, 6))]
        return rgb, a

    def slit(self, w, h):
        """Arrow-slit window in an ashlar surround: a narrow dark opening with an arched top and warm light low down."""
        yy, xx = grid(w, h)
        v = 4.0 - np.clip(np.maximum(np.abs((xx + .5) / w - .5), np.abs((yy + .5) / h - .5)) * 2 - 0.5, 0, 1) * 1.2
        v += self.noise(w, h, 0.1)
        rgb = C(R["stone"], v)
        cx = w / 2
        op = (np.abs(xx + 0.5 - cx) < 0.9) & (yy >= 2) & (yy <= h - 2)
        t = (yy - 2) / max(1, h - 4)
        rgb[op] = C(R["rune_stone"], 1.0 + t * 0.6)[op]
        warm = op & (t > 0.55); rgb[warm] = C(R["glow"], 2.0 + (t - 0.55) * 5)[warm]
        lip = (yy == h - 1) | (yy == 0); rgb[lip] = C(R["stone"], np.full((h, w), 4.6))[lip]
        return rgb, np.ones((h, w), bool)

    def crystal(self, w, h, cat):
        """Glowing crystal: pale centre, deeper cyan edges, a bright facet streak and a white-cyan tip row."""
        yy, xx = grid(w, h)
        v = 4.3 + (0.6 if cat == "up" else 0) - np.abs((xx + .5) / w - .5) * 2.4 + (0.5 - (yy + .5) / h) * 1.2
        v[:, max(0, w // 3)] += 1.0
        return C(R["crystal"], v + self.noise(w, h, 0.1)), np.ones((h, w), bool)

    def orb(self, w, h, cat):
        yy, xx = grid(w, h)
        d = np.hypot((xx + .5) / w - .38, (yy + .5) / h - .35)
        v = 5.6 - d * 4.2 + 0.4 * np.sin((xx + yy) * 1.3)
        return C(R["arcane"], v), np.ones((h, w), bool)


class Tower(Station):
    def __init__(self, name, seed, mats, tex=512):
        super().__init__(name, seed, mats, tex)
        self.P = TowerPainter(self.nr)
        self._mat_painters_fix()
        self.n = {}

    def nid(self, base):
        self.n[base] = self.n.get(base, 0) + 1
        return f"{base}_{self.n[base]}"

    # ---- placing things on an octagon side. phi: 0 north, 90 east, 180 south, 270 west, 45 north-east...
    @staticmethod
    def place(phi, A, u0, u1, y0, y1, out, inset=0.0, cx=0.0, cz=0.0):
        """Box on the side at angle phi of an octagon (apothem A, centre cx, cz): u along the side, `out` proud of
        it, `inset` into it. Returns frm, to, rotation, origin, outward face, inward face."""
        phi %= 360
        lf, lt = [u0, y0, -A - out], [u1, y1, -A + inset]
        if phi % 90 == 0:
            a = math.radians(-phi); c, s = round(math.cos(a)), round(math.sin(a))
            pts = [(x * c + z * s, -x * s + z * c) for x in (lf[0], lt[0]) for z in (lf[2], lt[2])]
            xs, zs = [p[0] for p in pts], [p[1] for p in pts]
            of = {0: "north", 90: "east", 180: "south", 270: "west"}[int(phi)]
            return [cx + min(xs), y0, cz + min(zs)], [cx + max(xs), y1, cz + max(zs)], (0, 0, 0), None, of, OPP[of]
        rot = -phi if phi <= 180 else 360 - phi
        return [cx + lf[0], y0, cz + lf[2]], [cx + lt[0], y1, cz + lt[2]], (0, rot, 0), [cx, y0, cz], "north", "south"

    def side_box(self, name, grp, phi, A, u0, u1, y0, y1, out, mat, inset=0.0, cx=0.0, cz=0.0, hide_in=True,
                 hide=("down",), over=None, var=None):
        frm, to, rot, org, of, inf = self.place(phi, A, u0, u1, y0, y1, out, inset, cx, cz)
        hd = set(hide) | ({inf} if hide_in else set())
        ov = dict(over or {})
        if of in ov: pass
        if rot != (0, 0, 0) and phi % 360 in (135, 225) and mat in self.mats:
            ov.setdefault("north", f"{mat}_shade")                    # south-facing diagonals are in shade
        ov2 = {}
        for k, val in ov.items():
            ov2[of if k == "out" else (inf if k == "in" else k)] = val
        return self.box(name, grp, frm, to, mat, tuple(hd), var, over=ov2, rot=rot, origin=org)

    def side_card(self, name, grp, phi, A, u0, u1, y0, y1, out, key, cx=0.0, cz=0.0, thick=0.0):
        frm, to, rot, org, of, inf = self.place(phi, A, u0, u1, y0, y1, out, -out + thick if thick else -out + 0.0, cx, cz)
        fs = {f: None for f in ("north", "east", "south", "west", "up", "down")}
        fs[of] = F(key)
        return self.m.cube(name, grp, frm, to, fs, rot, org)

    # ---- octagon prisms and rings
    def oct_prism(self, name, grp, A, y1, y2, mat, cx=0.0, cz=0.0, top=False, bottom=False, var=None, place=None, frac=None):
        """True octagon (apothem A) from four crossed bars A x b; interior faces hidden. The two diagonal bars are
        kept 0.05 inside at visible tops / bottoms so no two faces share a plane."""
        b = h2(A * T225)
        var = var or name
        hide_tb = tuple(f for f, show in (("up", top), ("down", bottom)) if not show)
        e = 0.05
        self.box(f"{name}_a", grp, [cx - A, y1, cz - b], [cx + A, y2, cz + b], mat, ("north", "south") + hide_tb,
                 f"{var}a", place=place, frac=frac)
        self.box(f"{name}_b", grp, [cx - b, y1, cz - A], [cx + b, y2, cz + A], mat, ("east", "west") + hide_tb,
                 f"{var}b", place=place, frac=frac)
        ya, yb = y1 + (e if bottom else 0), y2 - (e if top else 0)
        ec = self.box(f"{name}_c", grp, [cx - A, y1, cz - b], [cx + A, y2, cz + b], mat, ("north", "south") + hide_tb,
                 f"{var}c", rot=(0, 45, 0), origin=[cx, y1, cz], place=place, frac=frac)
        sh = {"east": f"{mat}_shade", "west": f"{mat}_lit"} if mat in self.mats and self.mats[mat]["kind"] != "flat" else None
        ed = self.box(f"{name}_d", grp, [cx - A, y1, cz - b], [cx + A, y2, cz + b], mat, ("north", "south") + hide_tb,
                 f"{var}d", rot=(0, -45, 0), origin=[cx, y1, cz], over=sh, place=place, frac=frac)
        for e in (ec, ed):                      # nudge after the UVs are sized, so pixels stay on the grid
            e["from"][1], e["to"][1] = round(ya, 4), round(yb, 4)

    def oct_ring(self, name, grp, A, y1, y2, t, mat, merlons=0, mh=2.5, cx=0.0, cz=0.0, skip=()):
        """Parapet: eight wall segments round an octagon (outer apothem A, thickness t), optional merlons on top."""
        b = h2(A * T225)
        for i in range(8):
            phi = i * 45
            if phi in skip: continue
            dy = 0.05 if i % 2 else 0.0
            e = self.side_box(f"{name}_{i + 1}", grp, phi, A, -b, b, y1, y2, 0, mat, inset=t, cx=cx, cz=cz,
                              hide_in=False, var=f"{name}{i % 2}")
            e["to"][1] = round(y2 - dy, 4)
            for k in range(merlons):
                u = -b + (k + 0.5) * 2 * b / merlons
                self.side_box(f"{name}_merlon_{i + 1}_{k + 1}", grp, phi, A, u - 1.25, u + 1.25, y2 - dy, y2 - dy + mh,
                              0.25, mat, inset=t + 0.25, cx=cx, cz=cz, hide_in=False, var="merlon")

    def arch_window(self, name, grp, phi, A, u, y, w, h, cx=0.0, cz=0.0, magic=True, figure=False, frame="trim"):
        """A stone-framed arched window on any octagon side: pane (glowing `_glow` if magic) 0.25 proud, jambs, sill,
        arch head and keystone 1 proud."""
        key = f"apane_{px(w)}x{px(h)}_{int(figure)}"
        if magic:
            self.rect(key, px(w), px(h), lambda W, H, f=figure: self.P.arcane_pane(W, H, True, f))
        else:
            key = self.rect(f"wpane_{px(w)}x{px(h)}", px(w), px(h), lambda W, H: self.P.window(R["stone"], W, H, "leaded", True, 0, True))
        self.side_card(f"{name}_pane_glow" if magic else f"{name}_pane", grp, phi, A, u - w / 2, u + w / 2, y, y + h, 0.25, key,
                       cx, cz)
        jh = h - w / 2 + 0.5
        for s, (a, b) in (("left", (u - w / 2 - 1.5, u - w / 2)), ("right", (u + w / 2, u + w / 2 + 1.5))):
            self.side_box(f"{name}_jamb_{s}", grp, phi, A, a, b, y - 0.5, y + jh, 1.0, frame, cx=cx, cz=cz, var="jamb")
        self.side_box(f"{name}_sill", grp, phi, A, u - w / 2 - 2, u + w / 2 + 2, y - 2, y - 0.5, 1.5, frame, cx=cx, cz=cz,
                      hide=(), var="sill")
        r = w / 2 + 0.75; cy = y + h - w / 2
        nv = 0 if w <= 4 else 3
        for i in range(nv):
            ang = 180 * (i + 0.5) / nv
            cu, cyy = u - math.cos(math.radians(ang)) * r, cy + math.sin(math.radians(ang)) * r
            if phi % 90 == 0:
                frm, to, _, _, of, inf = self.place(phi, A, cu - 1.0, cu + 1.0, cyy - 1.0, cyy + 1.0, 1.0, 0, cx, cz)
                zr = -(ang - 90)
                rot = {"north": (0, 0, zr), "south": (0, 0, -zr), "east": (-zr, 0, 0), "west": (zr, 0, 0)}[of]
                cen = [(frm[k] + to[k]) / 2 for k in range(3)]
                self.box(f"{name}_voussoir_{i + 1}", grp, frm, to, frame, (inf,), "vous", rot=rot, origin=cen)
            else:
                self.side_box(f"{name}_voussoir_{i + 1}", grp, phi, A, cu - 1.0, cu + 1.0, cyy - 1.0, cyy + 1.0, 1.0, frame,
                              cx=cx, cz=cz, var="vous")
        self.side_box(f"{name}_keystone", grp, phi, A, u - 1, u + 1, y + h - 0.5, y + h + 2.5, 1.5, frame, cx=cx, cz=cz,
                      var="key")

    def slit(self, name, grp, phi, A, u, y, cx=0.0, cz=0.0):
        k = self.rect("slit_6x14", 6, 14, lambda W, H: self.P.slit(W, H))
        self.side_box(name, grp, phi, A, u - 1.5, u + 1.5, y, y + 7, 0.5, "trim", cx=cx, cz=cz, over={"out": F(k)}, var="slit")

    def corbels(self, name, grp, A, y0, h, n, out, cx=0.0, cz=0.0, step=True):
        """n stepped corbels on every side, just under a band at y0 + h."""
        b = h2(A * T225); ys = h2(y0 + h * 0.45); out = h2(out); lo = max(0.5, h2(out * 0.5))
        for i in range(8):
            phi = i * 45
            for k in range(n):
                u = -b + (k + 0.5) * 2 * b / n
                self.side_box(f"{name}_{i + 1}_{k + 1}", grp, phi, A, u - 0.75, u + 0.75, ys, y0 + h, out, "trim",
                              cx=cx, cz=cz, hide=(), var="corbel")
                if step:
                    self.side_box(f"{name}_{i + 1}_{k + 1}_low", grp, phi, A, u - 0.5, u + 0.5, y0, ys, lo,
                                  "trim", cx=cx, cz=cz, hide=(), var="corbel_low")


def tower_mats():
    return station_mats(extra={
        "stone": {"kind": "ashlar", "ramp": R["stone"], "side": (96, 150), "top": (48, 48), "no_lit2": True},
        "trim": {"kind": "ashlar", "ramp": R["stone"], "side": (64, 24), "top": (48, 48), "no_lit2": True},
        "plinth": {"kind": "cobble", "ramp": R["cobble"], "side": (112, 8), "top": (56, 56), "no_lit2": True},
        "roof": {"kind": "shingle", "ramp": R["tile_midnight"], "side": (112, 96), "top": (64, 64), "under": (56, 56),
                 "no_lit2": True, "extra": {"style": "scale", "accent": R["gold"]}},
        "wood": {"kind": "boards", "ramp": R["walnut"], "side": (32, 32), "top": (32, 32), "no_lit2": True,
                 "extra": {"bw": 2, "shadow_top": False, "orient": "v", "lap": False}},
        "brass": {"kind": "metal", "ramp": R["brass"], "side": (16, 24), "top": (16, 16), "no_lit2": True},
        "iron": {"kind": "metal", "ramp": R["iron"], "side": (16, 16), "top": (16, 16), "no_lit2": True},
        "gold": {"kind": "metal", "ramp": R["gold"], "side": (16, 16), "top": (16, 16), "no_lit2": True},
    }, trim="stone", trim_kind="ashlar")


def wizard_tower():
    H = Tower("wizard_tower", 7707, tower_mats())
    P = H.P
    g = {k: H.group(k, [0, 0, 0]) for k in ("base", "stage_1", "stage_2", "balcony", "turret", "stage_3", "chamber",
                                             "roof", "finial", "crystals", "details")}

    # ------------------------------------------------ base: plinth, stairs, buttresses
    H.oct_prism("plinth", g["base"], 27, 0, 2, "plinth", top=True, place="ground")
    H.oct_prism("plinth_step", g["base"], 25, 2, 4, "trim", top=True, place="ground")
    for k, (z0, y1, x) in enumerate(((-34, 1.5, 8), (-31, 3.0, 7.5), (-28, 4.0, 7))):
        H.box(f"stair_{k + 1}", g["base"], [-x, 0, z0], [x, y1, -24.5 if k == 2 else -26], "trim", ("down",), f"stair{k}",
              place="ground")
    for i, phi in enumerate((45, 135, 225, 315)):
        n = f"buttress_{i + 1}"
        H.side_box(f"{n}_foot", g["base"], phi, 20, -3.5, 3.5, 4, 26, 9, "stone", inset=2, hide=("down",), var="bf")
        H.side_box(f"{n}_mid", g["base"], phi, 20, -3, 3, 26, 46, 6, "stone", inset=2, hide=("down",), var="bm")
        H.side_box(f"{n}_cap", g["base"], phi, 20, -3.5, 3.5, 46, 48, 6.5, "trim", inset=2, hide=(), var="bc")
        H.side_box(f"{n}_set", g["base"], phi, 20, -3.5, 3.5, 26, 27.5, 9.5, "trim", inset=2, hide=(), var="bs")

    # ------------------------------------------------ stage 1
    S1 = g["stage_1"]
    H.oct_prism("stage_1_wall", S1, 20, 4, 64, "stone", place="ground")
    H.door("front_door", S1, "north", -20, 0, 4, 12, 22, wood="walnut", frame="trim", arch=True, steps=None)
    H.box("front_door_hood", S1, [-9, 31, -21.5], [9, 32.5, -20], "trim", ("south",), "hood")
    for s, u in (("left", -11), ("right", 11)):
        H.lantern(f"light_{1 if s == 'left' else 2}", S1, "north", -20, u, 17)
    for phi in (90, 180, 270):
        H.arch_window(f"stage_1_window_{phi}", S1, phi, 20, 0, 30, 6, 12, magic=False)
    # ivy creeping up the north-west and west sides
    for i, (phi, u0, u1, y1) in enumerate(((315, -8, 2, 40), (270, -7, 6, 30), (0, -8, -6.5, 20), (225, -2, 7, 22))):
        k = H.rect(f"ivy_{i}", px(u1 - u0), px(y1 - 4), lambda W, Hh: P.ivy(W, Hh))
        H.side_card(f"ivy_{i + 1}", S1, phi, 20, u0, u1, 4, y1, 0.3, k)
    H.oct_prism("cornice_1", S1, 22, 64, 66.5, "trim", top=True, bottom=True)
    H.corbels("corbel_1", S1, 20, 60.5, 3.5, 3, 2.0, step=False)

    # ------------------------------------------------ stage 2
    S2 = g["stage_2"]
    H.oct_prism("stage_2_wall", S2, 18, 66.5, 128, "stone", place="top")
    for phi in (0, 90, 180, 270):
        H.arch_window(f"stage_2_window_{phi}", S2, phi, 18, 0, 80, 6, 13, magic=False)
    k = H.rect("oculus", 16, 16, lambda W, Hh: P.round_window(R["stone"], W, Hh))
    H.side_card("oculus_glass", S2, 0, 18, -4, 4, 104, 112, 0.3, k)
    H.side_box("oculus_ring_top", S2, 0, 18, -3, 3, 112, 113.5, 1, "trim", hide=(), var="oc")
    H.side_box("oculus_ring_bottom", S2, 0, 18, -3, 3, 102.5, 104, 1, "trim", hide=(), var="oc")
    H.side_box("oculus_ring_left", S2, 0, 18, -5.5, -4, 104, 112, 1, "trim", hide=(), var="ocs")
    H.side_box("oculus_ring_right", S2, 0, 18, 4, 5.5, 104, 112, 1, "trim", hide=(), var="ocs")
    bk = H.rect("banner", 14, 60, lambda W, Hh: P.banner(W, Hh))
    for phi in (90, 270, 45, 315):
        H.side_card(f"banner_{phi}", S2, phi, 18, -3.5, 3.5, 94, 124, 0.6, bk)
        H.side_box(f"banner_rod_{phi}", S2, phi, 18, -5, 5, 124, 125, 1.5, "iron", hide=(), var="rod")
        for s, u in ((("left", -5.5), ("right", 5.5)) if phi in (90, 270) else ()):
            H.side_box(f"banner_knob_{phi}_{s}", S2, phi, 18, u - 0.75, u + 0.75, 123.75, 125.25, 2.0, "gold", hide=(), var="knob")

    # ------------------------------------------------ balcony 1 + parapet
    B = g["balcony"]
    H.oct_prism("balcony_corbel_1", B, 20, 124, 126.5, "trim", bottom=True, top=True)
    H.oct_prism("balcony_corbel_2", B, 22, 126.5, 129.5, "trim", bottom=True, top=True)
    H.oct_prism("balcony_floor", B, 24.5, 129.5, 132.5, "trim", bottom=True, top=True)
    H.oct_ring("balcony_parapet", B, 24.5, 132.5, 136, 1.5, "trim", merlons=1)

    # ------------------------------------------------ side turret standing on the balcony (north east)
    Tg = g["turret"]
    tr = 19.5; tcx, tcz = tr * math.sin(math.radians(45)), -tr * math.cos(math.radians(45))
    tcx, tcz = h2(tcx), h2(tcz)
    H.oct_prism("turret_body", Tg, 4.5, 132.5, 176, "stone", cx=tcx, cz=tcz, place="top")
    H.oct_prism("turret_band", Tg, 5.5, 176, 177.5, "trim", cx=tcx, cz=tcz, top=True, bottom=True)
    H.oct_prism("turret_base_band", Tg, 5.5, 132.5, 134, "trim", cx=tcx, cz=tcz, top=True)
    H.arch_window("turret_window", Tg, 45, 4.5, 0, 158, 3, 7, cx=tcx, cz=tcz, magic=True)
    H.slit("turret_slit", Tg, 0, 4.5, 0, 142, cx=tcx, cz=tcz)
    H.cone("turret_cone", H.group("turret_roof", [tcx, 177.5, tcz], Tg), tcx, tcz, 14, 177.5, 196, "roof", n=7,
           finial="gold")

    # ------------------------------------------------ stage 3
    S3 = g["stage_3"]
    H.oct_prism("stage_3_wall", S3, 15.5, 132.5, 200, "stone", place="top")
    for phi in (0, 270, 180):
        H.arch_window(f"stage_3_window_{phi}", S3, phi, 15.5, 0, 152, 5, 12, magic=False)
    # spiral of slit windows (the stair inside winds up stages 1 to 3)
    spiral = [(45, 20, 14), (90, 20, 22), (135, 20, 44), (180, 20, 50), (225, 20, 40), (315, 20, 52),
              (45, 18, 74), (90, 18, 96), (135, 18, 108), (225, 18, 92), (315, 18, 116),
              (90, 15.5, 140), (225, 15.5, 172), (315, 15.5, 186)]
    for i, (phi, A, y) in enumerate(spiral):
        grp = S1 if y < 64 else (S2 if y < 128 else S3)
        u = 0 if phi % 90 else 5.5
        if phi in (45, 315) and A == 20: u = 0
        H.slit(f"slit_{i + 1}", grp, phi, A, u, y)

    # ------------------------------------------------ top chamber on flared corbels
    Ch = g["chamber"]
    H.oct_prism("chamber_corbel_1", Ch, 17, 196, 199, "trim", bottom=True, top=True)
    H.oct_prism("chamber_corbel_2", Ch, 19, 199, 202, "trim", bottom=True, top=True)
    H.oct_prism("chamber_corbel_3", Ch, 21, 202, 205, "trim", bottom=True, top=True)
    for i in range(8):
        phi = i * 45
        H.side_box(f"chamber_bracket_{i + 1}", Ch, phi, 15.5, -1, 1, 186, 196, 1.5, "trim", hide=(), var="brk")
    H.oct_prism("chamber_wall", Ch, 20, 205, 244, "stone", place="top")
    bb_ = h2(20 * T225)
    rk = H.rect("runes", px(2 * bb_), 4, lambda W, Hh: P.runes(W, Hh, "lit"))
    for i in range(8):                                   # glowing rune band, one painted strip per side
        e = H.side_box(f"rune_band_{i + 1}_glow", Ch, i * 45, 20, -bb_, bb_, 207, 209, 0.5, "trim",
                       hide=("down",), over={"out": F(rk)}, var="rune")
        if i % 2:                               # diagonal strips sit a hair further out than the cardinal ones
            e["from"][2] = round(e["from"][2] - 0.05, 4)
    for phi in (0, 90, 180, 270):
        H.arch_window(f"chamber_window_{phi}", Ch, phi, 20, 0, 212, 8, 16, magic=True, figure=(phi == 0))
    for phi in (45, 135, 225, 315):
        H.arch_window(f"chamber_window_{phi}", Ch, phi, 20, 0, 218, 4, 9, magic=True)
    H.oct_prism("chamber_cornice", Ch, 22, 244, 246, "trim", top=True, bottom=True)
    H.corbels("chamber_corbel", Ch, 20, 241, 3, 2, 1.5, step=False)

    # front balcony with an iron railing and a telescope
    Dt = g["details"]
    H.box("telescope_balcony_floor", Dt, [-8, 202, -29], [8, 205, -20], "trim", (), "tbf")
    for s, x in (("left", -6), ("right", 6)):
        H.box(f"telescope_balcony_corbel_{s}", Dt, [x - 1, 196, -27], [x + 1, 202, -21], "trim", (), "tbc")
    for k in range(7):
        x = -7.25 + k * 14.5 / 6
        H.box(f"railing_post_front_{k + 1}", Dt, [x - 0.25, 205, -28.5], [x + 0.25, 210, -28], "iron", ("down",), "rp")
    for s, x in (("left", -7.5), ("right", 7.5)):
        for k in range(3):
            z = -27 + k * 2.5
            H.box(f"railing_post_{s}_{k + 1}", Dt, [x - 0.25, 205, z - 0.25], [x + 0.25, 210, z + 0.25], "iron", ("down",), "rp")
        H.box(f"railing_rail_{s}", Dt, [x - 0.5, 210, -29], [x + 0.5, 211, -20], "iron", (), "rr")
    H.box("railing_rail_front", Dt, [-8, 210, -29], [8, 211, -28], "iron", (), "rrf")
    tg = H.group("telescope", [2, 205, -25], Dt)
    for i, (dx, dz) in enumerate(((-2.5, 1.5), (2.5, 1.5), (0, -2.5))):
        H.rotbar(f"telescope_leg_{i + 1}", tg, [2 + dx, 205, -25 + dz], [2, 212, -25], 1.0, "wood")
    H.box("telescope_head", tg, [1, 211.5, -26], [3, 213, -24], "brass", (), "thead")
    H.rotbar("telescope_tube", tg, [-1.5, 210.5, -21.5], [6.5, 218, -30], 2.0, "brass")
    H.rotbar("telescope_eyepiece", tg, [-2.5, 209.5, -20.5], [-1, 211, -22], 1.0, "brass")
    H.rotbar("telescope_lens_ring", tg, [6, 217.5, -29.5], [7, 218.5, -30.5], 2.5, "gold")

    # ------------------------------------------------ the witch-hat roof (crooked) + dormers
    Rf = g["roof"]
    H.oct_prism("roof_eave", Rf, 26, 246, 248, "roof", top=True, bottom=True, frac=0.0)
    y0, tip, n = 248.0, 352.0, 15
    tiers = []
    for i in range(n):
        u0, u1 = i / n, (i + 1) / n
        A = h2(max(2.0, 23.5 * (1 - u0) ** 1.45))
        bend = max(0.0, (u0 - 0.3) / 0.7) ** 2
        cx, cz = h2(-12 * bend), h2(4 * bend)
        ya, yb = h2(y0 + u0 * (tip - y0)), h2(y0 + u1 * (tip - y0))
        tiers.append((A, cx, cz, ya, yb))
        if A >= 3:
            H.oct_prism(f"roof_tier_{i + 1}", Rf, A, ya, yb, "roof", cx=cx, cz=cz, top=True, frac=(i + 0.5) / n)
        else:
            H.box(f"roof_tier_{i + 1}", Rf, [cx - A, ya, cz - A], [cx + A, yb, cz + A], "roof", ("down",), f"rt{i}",
                  rot=(0, 45 * (i % 2), 0), origin=[cx, ya, cz], frac=(i + 0.5) / n)
    A, cx, cz, ya, yb = tiers[-1]
    H.box("roof_point", Rf, [cx - 0.75, yb, cz - 0.75], [cx + 0.75, yb + 4, cz + 0.75], "roof", ("down",), "rpt", frac=1.0)
    ytop = yb + 4
    # dormers on the north and east slopes
    for phi in (0, 90):
        dg = H.group(f"dormer_{phi}", [0, 252, 0], Rf)
        Ad = tiers[1][0]
        H.side_box(f"dormer_{phi}_body", dg, phi, Ad, -4, 4, 251, 262, 4, "stone", inset=6, hide=("down", "up"), var="db")
        H.arch_window(f"dormer_{phi}_window", dg, phi, Ad + 4, 0, 253, 4, 7, magic=True)
        frm, to, _, _, of, _ = H.place(phi, Ad, -4, 4, 262, 263, 4, 6)
        dcx, dcz = (frm[0] + to[0]) / 2, (frm[2] + to[2]) / 2
        H.cone(f"dormer_{phi}_cone", dg, dcx, dcz, 11, 262, 276, "roof", n=5, finial="gold")

    # ------------------------------------------------ finial: rod, collars, glowing orb, crescent moon
    Fg = g["finial"]
    H.box("finial_rod", Fg, [cx - 0.5, ytop - 1, cz - 0.5], [cx + 0.5, ytop + 16, cz + 0.5], "gold", ("down",), "frod")
    H.box("finial_collar_1", Fg, [cx - 1.25, ytop, cz - 1.25], [cx + 1.25, ytop + 1.5, cz + 1.25], "gold", (), "fc1")
    H.box("finial_collar_2", Fg, [cx - 1, ytop + 3, cz - 1], [cx + 1, ytop + 4, cz + 1], "gold", (), "fc2")
    oy = ytop + 7
    og = H.group("orb", [cx, oy, cz], Fg)
    H.item("orb_glow", og, [cx - 2, oy - 2, cz - 2], [cx + 2, oy + 2, cz + 2], "orb", lambda W, Hh, c: P.orb(W, Hh, c), hide=())
    H.item("orb_halo_glow", og, [cx - 1.5, oy - 2.5, cz - 1.5], [cx + 1.5, oy + 2.5, cz + 1.5], "orbh",
           lambda W, Hh, c: P.orb(W, Hh, c), hide=(), rot=(0, 45, 0), origin=[cx, oy, cz])
    my = ytop + 13
    for i in range(7):
        ang = math.radians(-100 + i * 200 / 6)
        r = 3.0
        x, y = cx + math.sin(ang) * r * 0.9 - 0.8, my + math.cos(ang) * r
        s = 1.0 if i in (0, 6) else (1.5 if i in (1, 5) else 2.0)
        H.box(f"moon_{i + 1}", Fg, [x - s / 2, y - 0.5, cz - 0.5], [x + s / 2, y + 0.5, cz + 0.5], "gold", (),
              "moon", rot=(0, 0, round(-math.degrees(ang), 1)), origin=[x, y, cz])

    # ------------------------------------------------ floating crystals round the top chamber
    Cr = g["crystals"]
    crystals = []
    for i, (deg, y, r) in enumerate(((30, 226, 31), (125, 238, 30), (215, 222, 32), (300, 240, 30))):
        x, z = h2(r * math.sin(math.radians(deg))), h2(-r * math.cos(math.radians(deg)))
        cg = H.group(f"crystal_{i + 1}", [x, y, z], Cr)
        H.item(f"crystal_{i + 1}_core_glow", cg, [x - 1.25, y - 4, z - 1.25], [x + 1.25, y + 4, z + 1.25], "crys",
               lambda W, Hh, c: P.crystal(W, Hh, c), hide=(), rot=(0, 45, 0), origin=[x, y, z])
        H.item(f"crystal_{i + 1}_tip_glow", cg, [x - 0.75, y + 4, z - 0.75], [x + 0.75, y + 6, z + 0.75], "crys_t",
               lambda W, Hh, c: P.crystal(W, Hh, c), hide=(), rot=(0, 45, 0), origin=[x, y, z])
        H.item(f"crystal_{i + 1}_foot_glow", cg, [x - 0.75, y - 6, z - 0.75], [x + 0.75, y - 4, z + 0.75], "crys_t",
               lambda W, Hh, c: P.crystal(W, Hh, c), hide=(), rot=(0, 45, 0), origin=[x, y, z])
        H.item(f"crystal_{i + 1}_shard_glow", cg, [x + 2.5, y - 1, z - 0.5], [x + 3.5, y + 2, z + 0.5], "crys_s",
               lambda W, Hh, c: P.crystal(W, Hh, c), hide=(), rot=(0, 0, 22.5), origin=[x + 3, y, z])
        crystals.append(cg)

    # ------------------------------------------------ idle animation: crystals bob and spin, the orb turns (6 s loop)
    def kf(channel, t, xyz, interp="linear"):
        return {"channel": channel, "data_points": [{"x": str(xyz[0]), "y": str(xyz[1]), "z": str(xyz[2])}],
                "uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "time": t, "color": -1, "interpolation": interp}
    T = 6.0
    animators = {}
    for i, cg in enumerate(crystals):
        sgn = 1 if i % 2 == 0 else -1
        keys = [kf("rotation", round(T * k / 4, 3), (0, sgn * 90 * k, 0)) for k in range(5)]
        keys += [kf("position", t, (0, v, 0), "catmullrom") for t, v in
                 ((0, 0), (T / 4, 2 * sgn), (T / 2, 0), (3 * T / 4, -2 * sgn), (T, 0))]
        animators[H.m.groups[cg]["uuid"]] = {"name": cg, "type": "bone", "keyframes": keys}
    keys = [kf("rotation", round(T * k / 4, 3), (0, -90 * k, 0)) for k in range(5)]
    keys += [kf("scale", t, (s, s, s), "catmullrom") for t, s in ((0, 1), (T / 2, 1.12), (T, 1))]
    animators[H.m.groups["orb"]["uuid"]] = {"name": "orb", "type": "bone", "keyframes": keys}
    anim = {"uuid": str(uuid.UUID(int=H.rng.getrandbits(128), version=4)), "name": "idle", "loop": "loop", "override": False,
            "length": T, "snapping": 24, "selected": False, "anim_time_update": "", "blend_weight": "", "start_delay": "",
            "loop_delay": "", "animators": animators}
    orig = H.m.bbmodel

    def with_anim():
        d = orig(); d["animations"] = [anim]; return d
    H.m.bbmodel = with_anim
    return H


if __name__ == "__main__":
    H = wizard_tower()
    H.finish([OUT])
