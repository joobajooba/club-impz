"""Draws the 48x48 inventory icons for sickles, axes, bows and rods (tool_<id>.png) and the four
hilts (hilt_<id>.png), in the style of the other item icons: 5-colour ramps lit from the top left,
a dark edge where a part meets another, and a dark outline. Python because Aseprite isn't needed
for these; the look follows pixel_icons.lua.

Colours come from the game itself, so icon and 3D model match (ART-DIRECTION, section 2):
  - tool_icon_colours.json (next to this script): each tool's head and handle colour, exported from GameData
    (game/autoload/game_data.gd: metals from models/mining/pickaxe-skins.json, bows from the
    animal's leather, rods from the tree's wood).
  - the hilts take their ramps from the plank, ingot and gem icons they are made from (D-058, D-107).

Run from the repo root (needs Pillow):
  python godot-game/assets/sprites/source/build_tool_icons.py              writes source/items/ and godot-game/sprites/items/
  python godot-game/assets/sprites/source/build_tool_icons.py preview.png  also writes a 4x contact sheet
"""
import json
import math
import os
import sys

from PIL import Image

N = 48
INK = (18, 10, 24)
STRING = (232, 224, 204)
LX, LY = -0.6, -0.8                      # light from the top left (y grows downwards)
ROOT = os.path.dirname(os.path.abspath(__file__))


# --- colours -------------------------------------------------------------------------------

def hexc(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def mix(a, b, k):
    return tuple(round(a[i] + (b[i] - a[i]) * k) for i in range(3))


def ramp(base):
    """Five shades from one colour: shadows shift to purple-blue, highlights to warm white."""
    c = hexc(base) if isinstance(base, str) else base
    return [mix(c, (26, 16, 46), 0.55), mix(c, (34, 24, 60), 0.28), c,
            mix(c, (255, 244, 214), 0.28), mix(c, (255, 250, 232), 0.55)]


def ramp_from_icon(name):
    """Five shades sampled from a drawn icon: the non-outline pixels sorted by brightness."""
    img = Image.open(os.path.join(ROOT, "items", name)).convert("RGBA")
    cols = sorted((p[:3] for p in img.getdata() if p[3] > 0 and sum(p[:3]) > 90),
                  key=lambda c: c[0] * 0.3 + c[1] * 0.59 + c[2] * 0.11)
    return [cols[int(len(cols) * q)] for q in (0.06, 0.25, 0.5, 0.75, 0.94)]


def pick(r, t):
    return r[max(0, min(len(r) - 1, int(t * len(r))))]


# --- a canvas with the pixel_icons.lua rules ---------------------------------------------------

class Icon:
    def __init__(self):
        self.px = {}

    def commit(self, shape, r, edge=True):
        """Writes a shape; where it borders an earlier one, its border gets a dark line."""
        out = {}
        for (x, y), c in shape.items():
            if edge:
                for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                    q = (x + dx, y + dy)
                    if q not in shape and q in self.px:
                        c = mix(r[0], INK, 0.45)
                        break
            out[(x, y)] = c
        self.px.update(out)

    def stroke(self, pts, radii, r, edge=True, lift=0.0, rim=True):
        """A thick round-ended line through `pts`, its radius going from radii[0] to radii[1],
        shaded as a cylinder lit from the top left."""
        lens = [math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1)]
        total = sum(lens) or 1.0
        shape = {}
        best = {}
        acc = 0.0
        for i in range(len(pts) - 1):
            (ax, ay), (bx, by) = pts[i], pts[i + 1]
            L = lens[i] or 1e-6
            dx, dy = (bx - ax) / L, (by - ay) / L
            rmax = max(radii) + 1
            for y in range(int(min(ay, by) - rmax), int(max(ay, by) + rmax) + 1):
                for x in range(int(min(ax, bx) - rmax), int(max(ax, bx) + rmax) + 1):
                    px, py = x + 0.5 - ax, y + 0.5 - ay
                    u = max(0.0, min(L, px * dx + py * dy))
                    ox, oy = px - u * dx, py - u * dy
                    d = math.hypot(ox, oy)
                    k = (acc + u) / total
                    rad = radii[0] + (radii[1] - radii[0]) * k
                    if d <= rad and 0 <= x < N and 0 <= y < N and d / rad < best.get((x, y), 9):
                        best[(x, y)] = d / rad
                        nx, ny = (ox / rad, oy / rad) if d > 0 else (0.0, 0.0)
                        t = 0.5 + 0.42 * (nx * LX + ny * LY) + (24 - y) / 48 * 0.16 + lift
                        if rim and d / rad > 0.8:
                            t -= 0.12
                        shape[(x, y)] = pick(r, t)
            acc += L
        self.commit(shape, r, edge)
        return shape

    def poly(self, pts, r, edge=True, lift=0.0):
        """A filled polygon, lighter towards the top left and with a lit top-left border."""
        xs, ys = [p[0] for p in pts], [p[1] for p in pts]
        cx, cy = sum(xs) / len(xs), sum(ys) / len(ys)
        span = max(max(xs) - min(xs), max(ys) - min(ys)) / 2 or 1
        shape = {}
        for y in range(int(min(ys)), int(max(ys)) + 2):
            for x in range(int(min(xs)), int(max(xs)) + 2):
                if 0 <= x < N and 0 <= y < N and inside(x + 0.5, y + 0.5, pts):
                    nx, ny = (x + 0.5 - cx) / span, (y + 0.5 - cy) / span
                    t = 0.55 + 0.35 * (nx * LX + ny * LY) + lift
                    shape[(x, y)] = pick(r, t)
        for (x, y) in list(shape):                    # lit and shaded borders
            if (x - 1, y) not in shape or (x, y - 1) not in shape:
                shape[(x, y)] = r[4] if (x, y - 1) not in shape else r[3]
            elif (x + 1, y) not in shape or (x, y + 1) not in shape:
                shape[(x, y)] = r[1]
        self.commit(shape, r, edge)
        return shape

    def dot(self, x, y, c):
        if 0 <= x < N and 0 <= y < N:
            self.px[(int(x), int(y))] = c

    def line(self, a, b, c, only_empty=False):
        steps = int(max(abs(b[0] - a[0]), abs(b[1] - a[1]))) + 1
        for i in range(steps + 1):
            x = round(a[0] + (b[0] - a[0]) * i / steps)
            y = round(a[1] + (b[1] - a[1]) * i / steps)
            if not only_empty or (x, y) not in self.px:
                self.dot(x, y, c)

    def outline(self):
        add = {}
        for y in range(N):
            for x in range(N):
                if (x, y) in self.px:
                    continue
                if any((x + dx, y + dy) in self.px for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1))):
                    add[(x, y)] = INK
        self.px.update(add)

    def image(self):
        img = Image.new("RGBA", (N, N), (0, 0, 0, 0))
        for (x, y), c in self.px.items():
            img.putpixel((x, y), (*c, 255))
        return img


def inside(x, y, pts):
    hit = False
    j = len(pts) - 1
    for i in range(len(pts)):
        (xi, yi), (xj, yj) = pts[i], pts[j]
        if (yi > y) != (yj > y) and x < (xj - xi) * (y - yi) / (yj - yi) + xi:
            hit = not hit
        j = i
    return hit


def along(a, b, u, off=0.0):
    """The point a fraction u from a to b, pushed `off` pixels to the right of the line."""
    dx, dy = b[0] - a[0], b[1] - a[1]
    L = math.hypot(dx, dy)
    return (a[0] + dx * u - dy / L * off, a[1] + dy * u + dx / L * off)


# --- the tools ---------------------------------------------------------------------------------

def axe(t):
    ic, wood, metal = Icon(), ramp(t["handle"]), ramp(t["head"])
    a, b = (10, 42), (33, 11)
    ic.stroke([a, b], (1.7, 1.7), wood)
    ic.stroke([along(a, b, -0.02), along(a, b, 0.03)], (2.4, 2.4), wood, lift=0.1)   # the knob
    c = along(a, b, 0.82)
    ux, uy = (b[0] - a[0]) / 38.3, (b[1] - a[1]) / 38.3        # along the handle
    px, py = -uy, ux                                           # out to the right of it
    P = lambda s, o: (c[0] + ux * s + px * o, c[1] + uy * s + py * o)
    blade = [P(-2.5, -2.5), P(2.5, -2.5), P(3, 3), P(8.5, 8), P(9.5, 11.5), P(6, 13.5), P(-1, 14),
             P(-8, 12.5), P(-10, 9), P(-4, 4.5), P(-3, 0)]
    shape = ic.poly(blade, metal)
    for (x, y) in shape:                                       # the bright cutting edge
        o = (x + 0.5 - c[0]) * px + (y + 0.5 - c[1]) * py
        if o > 9 and (round(x + px * 1.2), round(y + py * 1.2)) not in shape:
            ic.dot(x, y, metal[4])
    ic.stroke([P(-3.8, 0), P(3.8, 0)], (2.2, 2.2), metal, lift=-0.15)    # the socket band
    ic.outline()
    return ic


def sickle(t):
    ic, wood, metal = Icon(), ramp(t["handle"]), ramp(t["head"])
    a, b = (9, 43), (18, 32)
    ic.stroke([a, b], (2.0, 2.0), wood)
    ic.stroke([along(a, b, -0.05), along(a, b, 0.05)], (2.6, 2.6), wood, lift=0.1)
    arc = []
    cx, cy, R = 29.0, 25.0, 12.5
    for i in range(23):
        ang = math.radians(162 + i * 8.5)                       # up and over to the right
        arc.append((cx + math.cos(ang) * R, cy + math.sin(ang) * R * 0.85))
    blade = ic.stroke(arc, (3.4, 0.6), metal)
    for (x, y) in blade:                                        # the sharp inner edge
        k = math.hypot(cx - x - 0.5, cy - y - 0.5) or 1
        ix, iy = round(x + (cx - x - 0.5) / k * 1.3), round(y + (cy - y - 0.5) / k * 1.3)
        if (ix, iy) not in blade:
            ic.dot(x, y, metal[4])
    ic.stroke([along(a, b, 0.88), along(a, b, 1.05)], (2.5, 2.5), metal, lift=-0.1)   # the ferrule
    ic.outline()
    return ic


def bow(t):
    ic, limb, grip = Icon(), ramp(t["head"]), ramp(t["handle"])
    p0, ctl, p2 = (41, 8), (1, 1), (8, 41)
    pts = []
    for i in range(33):
        u = i / 32
        pts.append(((1 - u) ** 2 * p0[0] + 2 * (1 - u) * u * ctl[0] + u * u * p2[0],
                    (1 - u) ** 2 * p0[1] + 2 * (1 - u) * u * ctl[1] + u * u * p2[1]))
    half = len(pts) // 2
    ic.stroke(pts[:half + 1], (1.0, 2.4), limb)
    ic.stroke(pts[half:], (2.4, 1.0), limb)
    ic.stroke(pts[half - 3:half + 4], (3.0, 3.0), grip)                     # the leather grip
    for k in (-2, 0, 2):                                                    # its wraps
        x, y = pts[half + k]
        ic.dot(round(x), round(y), grip[0])
        ic.dot(round(x) + 1, round(y) - 1, grip[0])
    for tip in (pts[0], pts[-1]):                                           # the nocks
        ic.stroke([tip, tip], (1.6, 1.6), ramp("#e8dcc0"))
    ic.outline()
    ic.line(pts[1], pts[-2], STRING, only_empty=True)                       # the string
    return ic


def rod(t):
    ic, wood, cork = Icon(), ramp(t["head"]), ramp(t["handle"])
    a, b = (6, 44), (41, 6)
    ic.stroke([along(a, b, 0.2), b], (1.5, 0.6), wood)
    ic.stroke([a, along(a, b, 0.24)], (2.3, 2.1), cork)
    for u in (0.08, 0.16):                                                  # cork rings
        x, y = along(a, b, u)
        ic.dot(round(x), round(y), cork[1])
    reel = along(a, b, 0.27, 3.2)
    ic.stroke([reel, reel], (3.0, 3.0), ramp("#9aa0a8"))
    ic.dot(round(reel[0]), round(reel[1]), ramp("#9aa0a8")[0])
    for u in (0.5, 0.75):                                                   # line guides
        x, y = along(a, b, u, 1.4)
        ic.dot(round(x), round(y), ramp("#9aa0a8")[3])
    ic.stroke([(41.5, 28.5), (41.5, 28.5)], (2.6, 2.6), ramp("#e83a2e"))   # the bobber
    for x in range(40, 44):
        if (x, 27) in ic.px:
            ic.dot(x, 27, (246, 242, 236))
    ic.outline()
    ic.line((41, 7), (41, 25), STRING, only_empty=True)                     # the line
    return ic


# --- the hilts (D-058, D-107) ------------------------------------------------------------------

def hilt(wood, band, pommel_gem=None, motif=None):
    ic = Icon()
    a, b = (13, 38), (32, 16)
    ic.stroke([a, b], (3.0, 3.0), wood)
    for u in (0.3, 0.45, 0.6):                                  # the wrap
        p, q = along(a, b, u, -3), along(a, b, u + 0.06, 3)
        ic.line((round(p[0]), round(p[1])), (round(q[0]), round(q[1])), wood[0], only_empty=False)
    ic.stroke([along(a, b, 0.97), along(a, b, 1.07)], (4.2, 4.2), band, lift=0.05)   # the collar
    ic.stroke([along(a, b, -0.1), along(a, b, -0.1)], (4.0, 4.0), band)              # the pommel
    if pommel_gem:
        x, y = along(a, b, -0.1)
        ic.stroke([(x - 0.3, y - 0.3), (x - 0.3, y - 0.3)], (2.1, 2.1), pommel_gem, edge=False, lift=0.15)
    if motif == "spiral":
        for i in range(10):
            ang = i * 0.9
            x, y = along(a, b, 0.48)
            ic.dot(round(x + math.cos(ang) * i * 0.22), round(y + math.sin(ang) * i * 0.22), band[4])
    if motif == "stars":
        for u, o in ((0.35, -1), (0.6, 1), (0.8, 0)):
            x, y = along(a, b, u, o)
            ic.dot(round(x), round(y), (255, 246, 176))
    ic.outline()
    if motif == "stars":                                        # a sparkle off the collar
        x, y = along(a, b, 1.15, -5)
        for dx, dy in ((0, 0), (1, 0), (-1, 0), (0, 1), (0, -1)):
            ic.dot(round(x) + dx, round(y) + dy, (255, 246, 176) if (dx, dy) != (0, 0) else (255, 255, 255))
    return ic


def main():
    outs = [os.path.join(ROOT, "items"), os.path.join(ROOT, "..", "..", "..", "sprites", "items")]
    tools = json.load(open(os.path.join(ROOT, "tool_icon_colours.json")))
    draw = {"axe": axe, "sickle": sickle, "bow": bow, "rod": rod}
    icons = [("tool_" + t["id"], draw[t["kind"]](t)) for t in tools]
    gold_band = ramp("#c89a2a")
    icons += [
        ("hilt_ash_hilt", hilt(ramp_from_icon("plank_ash.png"), ramp("#7a6a5a"))),
        ("hilt_oak_hilt", hilt(ramp_from_icon("plank_oak.png"), ramp("#6a6470"))),
        ("hilt_void_hilt", hilt(ramp_from_icon("ingot_void.png"), ramp("#3e2860"),
                                ramp_from_icon("gemstone_arcanium.png"), "spiral")),
        ("hilt_cosmic_hilt", hilt(ramp_from_icon("ingot_stellarite.png"), gold_band,
                                  ramp_from_icon("gemstone_eclipsium.png"), "stars")),
    ]
    for out in outs:
        os.makedirs(out, exist_ok=True)
        for name, ic in icons:
            ic.image().save(os.path.join(out, name + ".png"))
    print(len(icons), "icons")
    if len(sys.argv) > 1:
        cols = 10
        rows = math.ceil(len(icons) / cols)
        sheet = Image.new("RGBA", (cols * N * 4, rows * N * 4), (58, 58, 70, 255))
        for i, (name, ic) in enumerate(icons):
            big = ic.image().resize((N * 4, N * 4), Image.NEAREST)
            sheet.paste(big, ((i % cols) * N * 4, (i // cols) * N * 4), big)
        sheet.save(sys.argv[1])


if __name__ == "__main__":
    main()
