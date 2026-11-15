"""pine_tree v2: docs/blockbench_detailed_prompts.md draft v3 -- leaves the Hytale way
(dark leaf cores + drooping alpha needle-spray cards, 50% tier overlap, pointed leader, smooth gradient)."""
import base64, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image

OUT_DIR = sys.argv[1]
NAME = "pine_tree"
TEX = 256
PPU = 2
rng = random.Random(2203)
nrng = np.random.default_rng(2203)

def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))

RAMPS = {
    "leaf":  [hexc(c) for c in "#0f2a24 #173d2c #1f5233 #2a6b3a #3d8544 #5ea04e #8cbf5e".split()],
    "bark":  [hexc(c) for c in "#1a1218 #24140e #3a2216 #52321e #6c4428 #885834 #a67244".split()],
    "moss":  [hexc(c) for c in "#1e3014 #2e481a #42621f #5c7e28 #7a9a34".split()],
    "ring":  [hexc(c) for c in "#5a3a22 #7a5432 #9a7046 #b88c5c #d2a874".split()],
    "cone":  [hexc(c) for c in "#2a160e #422416 #5c3420 #7a4a2a #9a6438 #b8804a".split()],
    "dry":   [hexc(c) for c in "#3a2416 #5a3a1e #7a5228 #9a6a34 #b8843e".split()],
    "cap":   [hexc(c) for c in "#3e1418 #6a2219 #963420 #bc4a28 #d86a38 #ea8c4c".split()],
    "stem":  [hexc(c) for c in "#5a4c48 #7e6e62 #a4927c #c4b498 #ddd0b4".split()],
    "spot":  [hexc(c) for c in "#c8bca0 #e8dcb8 #f4ecd4".split()],
}
LEAF_MAX = 5.5  # lightest leaf value used: halfway #5ea04e -> #8cbf5e, a soft green, never neon

def ramp_colour(name, v):
    """Value -> colour in half steps (half steps blend neighbours, so the ramp has small steps)."""
    r = RAMPS[name]; n = len(r)
    q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
    lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
    a = np.array(r)[lo]; b = np.array(r)[hi]
    return (a * (1 - f) + b * f).round().astype(np.uint8)

# ---------------------------------------------------------------- bark / detail painters (unchanged from v1)
FACE_LIGHT = {"up": 1.0, "north": 0.35, "west": 0.35, "south": -0.25, "east": -0.25, "down": -1.6}

def noise(w, h, amp=1.0, count=None):
    f = np.zeros((h, w))
    count = count or max(1, (w * h) // 5)
    for _ in range(count):
        x, y = nrng.integers(0, w), nrng.integers(0, h)
        d = nrng.choice([-1, -0.5, 0.5, 1]) * amp
        cw, ch = nrng.integers(1, 3), nrng.integers(1, 3)
        f[y:y + ch, x:x + cw] += d
    return f

def edge_light(f, amt=1.0):
    f[0, :] += amt; return f

def ao_edge(f, rows=2, amt=1.2):
    for i in range(min(rows, f.shape[0])):
        f[-1 - i, :] -= amt * (rows - i) / rows
    return f

def grain(w, h):
    f = np.zeros((h, w))
    for x in range(w):
        f[:, x] += np.cumsum(nrng.normal(0, 0.15, h)) * 0.5 + nrng.choice([-0.4, 0, 0, 0.3])
    x = int(nrng.integers(1, 4))
    while x < w:
        on = np.ones(h, bool)
        for _ in range(max(1, h // 14)):
            s = int(nrng.integers(0, h)); on[s:s + int(nrng.integers(1, 3))] = False
        f[on, x] -= 1.8
        if x + 1 < w: f[on, x + 1] += 0.6
        x += int(nrng.integers(3, 6))
    return f

def knot(f, cx, cy):
    h, w = f.shape
    for y in range(cy - 2, cy + 3):
        for x in range(cx - 2, cx + 2):
            if 0 <= x < w and 0 <= y < h:
                d = math.hypot((x - cx + 0.5) * 1.2, y - cy)
                if d < 0.9: f[y, x] = 0.2
                elif d < 1.8: f[y, x] = 1.5
                elif d < 2.5: f[y, x] += 1.0

def paint_bark(w, h, face, moss_rows=0, knots=0, base_ao=True):
    light = FACE_LIGHT[face]
    if face == "up":
        f = np.full((h, w), 4.3) + noise(w, h, 0.6) + grain(w, h) * 0.3
    else:
        f = np.full((h, w), 3.2 + light) + grain(w, h) + noise(w, h, 0.5)
        f += np.linspace(0.5, -0.6, h)[:, None]
        edge_light(f, 0.9)
        if base_ao: ao_edge(f, 2, 1.2)
        for _ in range(knots):
            knot(f, int(nrng.integers(2, max(3, w - 2))), int(nrng.integers(4, max(5, h - 8))))
    rgb = ramp_colour("bark", f)
    if moss_rows:
        mv = np.full((h, w), 2.4 + light * 0.6) + noise(w, h, 0.9)
        if face == "up":
            m = nrng.random((h, w)) < 0.55
        else:
            m = np.zeros((h, w), bool)
            for x in range(w):
                m[max(0, h - moss_rows + int(nrng.integers(-2, 3))):, x] = True
            m &= nrng.random((h, w)) < 0.85
        rgb[m] = ramp_colour("moss", mv)[m]
    return rgb, np.ones((h, w), bool)

def paint_rings(w, h):
    cx, cy = (w - 1) / 2, (h - 1) / 2
    yy, xx = np.mgrid[0:h, 0:w]
    f = 2.5 + np.sin(np.hypot(xx - cx, yy - cy) * 2.4) * 1.0 + noise(w, h, 0.3)
    rgb = ramp_colour("ring", f)
    edge = (xx == 0) | (yy == 0) | (xx == w - 1) | (yy == h - 1)
    rgb[edge] = ramp_colour("bark", np.full((h, w), 2.0))[edge]
    return rgb, np.ones((h, w), bool)

def paint_scales(ramp, w, h, face):
    yy, xx = np.mgrid[0:h, 0:w]
    f = np.full((h, w), 2.6 + FACE_LIGHT[face]) + noise(w, h, 0.4)
    f += np.where(((xx + (yy // 2) % 2) % 2 == 0) & (yy % 2 == 0), 1.2, 0)
    f -= np.where(yy % 2 == 1, 0.7, 0)
    if face not in ("up", "down"): edge_light(f, 0.6)
    return ramp_colour(ramp, f), np.ones((h, w), bool)

def stroke_field(w, h, lo, hi, density):
    f = np.full((h, w), (lo + hi) / 2 - 0.6) + noise(w, h, 0.3)
    for _ in range(int(w * h * density / 2.5)):
        x, y = int(nrng.integers(0, w)), int(nrng.integers(0, h))
        L = int(nrng.integers(2, 5)); dx = int(nrng.choice([-1, 1])); val = nrng.uniform(lo, hi)
        for i in range(L):
            xx, yy = x + i * dx, y - i
            if 0 <= xx < w and 0 <= yy < h: f[yy, xx] = max(f[yy, xx], val - i * 0.25)
    return f

def paint_plain(ramp, w, h, face, base=2.5, detail=None):
    f = np.full((h, w), base + FACE_LIGHT[face]) + noise(w, h, 0.5)
    if face not in ("up", "down"): edge_light(f, 0.7); ao_edge(f, 1, 0.8)
    rgb = ramp_colour(ramp, f)
    if detail == "spots":
        for _ in range(max(1, w * h // 14)):
            x, y = int(nrng.integers(0, w)), int(nrng.integers(0, h))
            rgb[y:y + 2, x:x + 1 + int(nrng.integers(0, 2))] = RAMPS["spot"][int(nrng.integers(0, 3))]
    if detail == "gills":
        for x in range(0, w, 2): rgb[:, x] = ramp_colour("cap", np.full(h, 0.6))
    if detail == "needles":
        rgb = ramp_colour(ramp, stroke_field(w, h, 1.5, 4.0, 0.8) + FACE_LIGHT[face] * 0.5)
        return rgb, nrng.random((h, w)) > 0.15
    return rgb, np.ones((h, w), bool)

# ---------------------------------------------------------------- leaf painters (Hytale way)
def paint_card(w, h, shade, sprays, accents=True, cone=False):
    """Needle spray card. Base (trunk end) at the top row, tip at the bottom row.
    shade: offset for the whole card (lower tiers darker, upper tiers lighter)."""
    val = np.full((h, w), -9.0)  # -9 = transparent

    def put(x, y, v):
        if 0 <= x < w and 0 <= y < h and v > val[y, x]: val[y, x] = v

    def spray(x0, y0, x1, y1):
        n = max(2, int(math.hypot(x1 - x0, y1 - y0)))
        dirx, diry = (x1 - x0) / n, (y1 - y0) / n
        for s in range(n + 1):
            t = s / n
            cx, cy = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            along = (cy / (h - 1))  # gradient: dark at the trunk end, light at the tip
            put(int(round(cx)), int(round(cy)), 0.9 + along * 1.2 + shade)  # twig, 1 px
            if s % 2 == 0 and s < n:
                reach = 2 + int(round((1 - abs(t - 0.45)) * 3)) - (1 if t > 0.85 else 0)
                for side in (-1, 1):
                    # needle: 1 px diagonal stroke angled towards the tip, dark base -> light end
                    nx, ny = -diry * side, dirx * side
                    for k in range(1, reach + 1):
                        px_ = cx + nx * k + dirx * k * 0.8
                        py_ = cy + ny * k + diry * k * 0.8
                        v = 1.3 + along * 2.4 + (k / reach) * 1.3 + shade
                        put(int(round(px_)), int(round(py_)), v)
    for sp in sprays:
        spray(*sp)
    a = val > -5
    # soft highlights only on the outer tips (bottom 3 rows of painted pixels in each column) and top-lit needle ends
    hi = np.zeros_like(a)
    for x in range(w):
        ys = np.nonzero(a[:, x])[0]
        if len(ys): hi[ys[-3:], x] = True
    val = np.where(hi, val + 0.6, val)
    val = np.clip(val, 0, LEAF_MAX)
    rgb = ramp_colour("leaf", val)
    if accents:  # <= 3%: rust dead needles, odd brown cone pixel
        idx = np.argwhere(a)
        k = max(1, int(len(idx) * 0.008))
        for j in nrng.choice(len(idx), k, replace=False):
            y, x = idx[j]; rgb[y, x] = RAMPS["dry"][int(nrng.integers(1, 3))]
    if cone:  # small brown cone hanging under the twig, 2 x 3 px with a light top pixel
        cx, cy = w // 2 + 1, int(h * 0.55)
        for dy in range(3):
            for dx in range(2):
                rgb[cy + dy, cx + dx] = RAMPS["cone"][4 - dy - dx]; a[cy + dy, cx + dx] = True
    return rgb, a

def card_sprays(w, h, seed):
    """3 to 5 overlapping sprays fanning from the trunk end to the tip."""
    r = random.Random(seed)
    cx = (w - 1) / 2
    sp = [(cx + r.uniform(-0.5, 0.5), 0, cx + r.uniform(-1, 1), h - 1)]  # main spray, full length
    for i in range(r.randint(2, 4)):
        side = -1 if i % 2 == 0 else 1
        y0 = r.uniform(0.1, 0.45) * h
        sp.append((cx + side * r.uniform(0, 1.5), y0, cx + side * r.uniform(w * 0.22, w * 0.42), y0 + r.uniform(0.45, 0.6) * h))
    return sp

def paint_core(w, h):
    """Core swatch: two darkest leaf shades with soft needle shapes painted in."""
    f = stroke_field(w, h, 0.4, 1.3, 0.7)
    return ramp_colour("leaf", np.clip(f, 0, 1)), np.ones((h, w), bool)

# ---------------------------------------------------------------- atlas
class Atlas:
    def __init__(self): self.rects = {}
    def add(self, key, w, h, painter):
        if key not in self.rects: self.rects[key] = {"w": w, "h": h, "paint": painter}
        return key
    def pack(self):
        x = y = shelf = 0
        for k, r in sorted(self.rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
            if x + r["w"] > TEX: x, y, shelf = 0, y + shelf, 0
            r["x"], r["y"] = x, y; x += r["w"]; shelf = max(shelf, r["h"])
        if y + shelf > TEX: raise SystemExit(f"atlas overflow: {y + shelf}px")
        img = np.zeros((TEX, TEX, 4), np.uint8)
        for k, r in self.rects.items():
            rgb, a = r["paint"](r["w"], r["h"])
            img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], :3] = rgb
            img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], 3] = np.where(a, 255, 0)
        return img, y + shelf
    def uv(self, key, mirror=False, sub=None):
        r = self.rects[key]; x1, y1 = r["x"], r["y"]
        if sub:  # sub rectangle of a shared swatch (same pixel density, no stretching)
            ox, oy, sw, sh = sub; x1, y1 = x1 + ox, y1 + oy; x2, y2 = x1 + sw, y1 + sh
        else:
            x2, y2 = x1 + r["w"], y1 + r["h"]
        return [x2, y1, x1, y2] if mirror else [x1, y1, x2, y2]

atlas = Atlas()

def face_dims(frm, to, face):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]

def px(u):
    v = u * PPU
    assert abs(v - round(v)) < 1e-6, f"non integer pixel size {u}"
    return int(round(v))

def h2(v): return round(v * 2) / 2  # snap to half units (1 pixel)

# ---------------------------------------------------------------- rotation helpers
def Rx(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])

def bb_euler(M):
    """Decompose M into Blockbench's element rotation (matrix = Rz * Ry * Rx)."""
    b = math.asin(max(-1, min(1, -M[2, 0])))
    a = math.atan2(M[2, 1], M[2, 2]); c = math.atan2(M[1, 0], M[0, 0])
    return [math.degrees(a), math.degrees(b), math.degrees(c)]

def card_rotation(yaw, droop, twist):
    """Twist about the card's own length, then droop down, then yaw round the trunk."""
    return bb_euler(Ry(yaw) @ Rx(droop) @ Rz(twist))

# ---------------------------------------------------------------- model
elements, groups = [], {}
def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

def group(name, origin, parent=None):
    groups[name] = {"name": name, "uuid": new_uuid(), "origin": [round(v, 3) for v in origin], "children": []}
    if parent: groups[parent]["children"].append(("g", name))
    return name

def cube(name, grp, frm, to, faces, rotation=(0, 0, 0), origin=None):
    """faces: face -> None (hidden) or dict(key, mirror=False, sub=None, rot=0)."""
    origin = origin or [(frm[i] + to[i]) / 2 for i in range(3)]
    fj = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        spec = faces.get(f)
        fj[f] = {"uv": [0, 0, 0, 0], "texture": None} if spec is None else {"_spec": spec, "texture": 0}
    e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
         "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
         "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": fj, "type": "cube",
         "uuid": new_uuid()}
    if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(v, 3) for v in rotation]
    elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
    return e

def F(key, mirror=False, sub=None, rot=0): return {"key": key, "mirror": mirror, "sub": sub, "rot": rot}

def rects_for(prefix, frm, to, painter_for, hidden=(), share_sides=True):
    faces = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        if f in hidden: faces[f] = None; continue
        w, h = (px(v) for v in face_dims(frm, to, f))
        if share_sides and f in ("east", "west"):
            faces[f] = F(atlas.add(f"{prefix}:side", w, h, painter_for("east")), mirror=(f == "west"))
        else:
            faces[f] = F(atlas.add(f"{prefix}:{f}", w, h, painter_for(f)))
    return faces

LEAN = 1.5
def lean(y): return LEAN * y / 144

root = group(NAME, [0, 0, 0])
g_roots = group("roots", [0, 0, 0], root)
g_trunk = group("trunk", [0, 0, 0], root)
g_canopy = group("canopy", [0, 20, 0], root)
g_details = group("details", [0, 0, 0], root)

# ---- roots (6, stepping out to ~18 wide, moss on 3)
ROOT_T = {"a": {"inner": ([-1.5, -0.5, 3], [1.5, 5, 7.5]), "outer": ([-1.25, -0.5, 6.5], [1.25, 2.5, 9.5])},
          "b": {"inner": ([-1.25, -0.5, 3], [1.25, 4, 7]), "outer": ([-1, -0.5, 6], [1, 2, 8.5])}}
for i, ang in enumerate([12, 68, 131, 188, 236, 302]):
    t = "a" if i % 2 == 0 else "b"; m = i in (0, 2, 4)
    yaw = ang + rng.uniform(-6, 6)
    for part in ("inner", "outer"):
        frm, to = ROOT_T[t][part]
        faces = rects_for(f"root_{t}_{part}_{'moss' if m else 'bare'}", frm, to,
                          lambda f, m=m, part=part: (lambda w, h: paint_bark(w, h, f, moss_rows=(4 if part == "outer" else 6) if m else 0)),
                          hidden=("north", "down"))
        cube(f"root_{i + 1}_{part}", g_roots, frm, to, faces, rotation=(0, yaw, 0), origin=[0, 0, 0])

# ---- trunk (5 sections 10 -> 4, lean north east)
sections = [(10, 0, 16), (8, 16, 38), (7, 38, 70), (5, 70, 104), (4, 104, 136)]
for i, (w, y1, y2) in enumerate(sections):
    off = h2(lean((y1 + y2) / 2)); cx, cz = off, -off
    frm = [cx - w / 2, y1, cz - w / 2]; to = [cx + w / 2, y2, cz + w / 2]
    def pf(f, i=i):
        return lambda W, H: paint_bark(W, H, f, moss_rows=6 if i == 0 else 0, knots=1 if i < 2 else 0, base_ao=(i == 0))
    faces = rects_for(f"trunk_{i + 1}", frm, to, pf, hidden=("down",), share_sides=False)
    if i >= 2:  # hidden inside the canopy apart from small glimpses: one shared bark rect on all sides
        k = faces["north"]["key"]
        for f in ("east", "south", "west"):
            atlas.rects.pop(faces[f]["key"], None); faces[f] = F(k, mirror=f in ("south", "west"))
    cube(f"trunk_{i + 1}", g_trunk, frm, to, faces)

strips = [(0, "north", 1.0, 0.5, 13), (0, "east", -2.0, 1, 11), (0, "west", 0.5, 0, 14),
          (1, "south", -1.5, 17, 33), (1, "north", -2.0, 19, 31), (1, "east", 1.5, 18, 35)]
for i, (s, side, a, y1, y2) in enumerate(strips):
    w, sy1, sy2 = sections[s]; off = h2(lean((sy1 + sy2) / 2)); cx, cz = off, -off; hw = w / 2
    sw, d = (1.5, 1.0) if i % 2 == 0 else (1.0, 1.0)
    if side == "north": frm, to = [cx + a, y1, cz - hw - d], [cx + a + sw, y2, cz - hw]
    if side == "south": frm, to = [cx + a, y1, cz + hw], [cx + a + sw, y2, cz + hw + d]
    if side == "east":  frm, to = [cx + hw, y1, cz + a], [cx + hw + d, y2, cz + a + sw]
    if side == "west":  frm, to = [cx - hw - d, y1, cz + a], [cx - hw, y2, cz + a + sw]
    opp = {"north": "south", "south": "north", "east": "west", "west": "east"}[side]
    faces = rects_for(f"bark_strip_{i + 1}", frm, to,
                      lambda f, s=s: (lambda W, H: paint_bark(W, H, f, moss_rows=3 if s == 0 else 0, base_ao=(s == 0))),
                      hidden=(opp, "down"), share_sides=False)
    cube(f"bark_strip_{i + 1}", g_trunk, frm, to, faces)

for i, (y, yaw, tilt, L, r0) in enumerate([(12, 222, -32, 4.5, 4), (18, 78, -40, 3.5, 3.5)]):
    frm, to = [-0.75, y - 0.75, r0], [0.75, y + 0.75, r0 + L]
    faces = rects_for(f"stub_{i + 1}", frm, to,
                      lambda f: (lambda W, H: paint_rings(W, H)) if f == "south" else (lambda W, H: paint_bark(W, H, f, base_ao=False)),
                      hidden=("north",))
    cube(f"stub_branch_{i + 1}", g_trunk, frm, to, faces, rotation=(tilt, yaw, 0), origin=[0, y, 0])

# ---- canopy: 13 drooping skirt tiers, dark cores + alpha needle-spray cards
# 5 card variants (width, length in units). Lower tiers darker, upper tiers lighter (section 3.1 gradient rule).
VARIANTS = {"v1": (9, 16, -0.7), "v2": (8, 14, -0.4), "v3": (7, 12, -0.1), "v4": (6, 9, 0.2), "v5": (5, 7, 0.45)}
for k, (w, L, shade) in VARIANTS.items():
    W, H = px(w), px(L)
    atlas.add(f"card_{k}", W, H, lambda W2, H2, shade=shade, seed=k: paint_card(W2, H2, shade, card_sprays(W2, H2, seed), cone=seed in ("v2", "v4")))
CORE_SW = 58  # one shared core swatch (px); every core face uses a sub rectangle of it
atlas.add("core", CORE_SW, CORE_SW, paint_core)

def core_face(w_u, h_u):
    W, H = px(w_u), px(h_u)
    assert W <= CORE_SW and H <= CORE_SW, (W, H)
    return F("core", sub=(int(nrng.integers(0, CORE_SW - W + 1)), int(nrng.integers(0, CORE_SW - H + 1)), W, H))

NT = 13
def tier_variant(i): return ["v1", "v1", "v1", "v2", "v2", "v2", "v3", "v3", "v3", "v4", "v4", "v5", "v5"][i]
def smaller(k): return {"v1": "v2", "v2": "v3", "v3": "v4", "v4": "v5", "v5": "v5"}[k]

# tier heights shrink going up; each tier's tips sit at half the height of the tier below (50% overlap)
hs = [26.5 - 1.54 * i for i in range(NT)]
Rs = [28 - i * (22.0 / (NT - 1)) for i in range(NT)]
y_top = [20 + hs[0]]
for i in range(1, NT):
    y_top.append(y_top[i - 1] - hs[i - 1] / 2 + hs[i])
skirt_n = [11, 11, 10, 10, 10, 10, 9, 9, 9, 8, 8, 8, 8]
inner_n = [5, 5, 4, 4, 3, 0, 0, 0, 0, 0, 0, 0, 0]  # inner ring from the trunk on the wide tiers
crossed_n = [2] * NT
GLIMPSE = {4: 205.0, 8: 25.0}  # tier -> yaw (deg) of a small gap showing the trunk
T20, T25 = math.tan(math.radians(20)), math.tan(math.radians(25))

def pick_variant(length):
    """Card variant whose length best matches the span needed."""
    return min(VARIANTS, key=lambda v: abs(VARIANTS[v][1] - length))

def add_card(name, g, k, P0, yaw, droop, twist):
    cw, cL, _ = VARIANTS[k]
    rot = card_rotation(yaw, droop, twist)
    cube(name, g, [P0[0] - cw / 2, P0[1], P0[2]], [P0[0] + cw / 2, P0[1], P0[2] + cL], {"up": F(f"card_{k}")}, rotation=rot, origin=P0)
    return rot

def at(lx, lz, r, yaw, y): return [lx + r * math.sin(math.radians(yaw)), y, lz + r * math.cos(math.radians(yaw))]

def in_gap(yaw, gl, n): return gl is not None and abs(((yaw - gl + 180) % 360) - 180) < 360 / n * 0.6

for i in range(NT):
    k = tier_variant(i); cw, cL, _ = VARIANTS[k]
    R, h, yt = Rs[i], hs[i], y_top[i]; yb = yt - h
    lx, lz = lean(yt - h / 2), -lean(yt - h / 2)
    g = group(f"tier_{i + 1}", [lx, yt, lz], g_canopy)
    gl = GLIMPSE.get(i)
    rs_nom = max(0.5, R - cL * math.cos(math.radians(25)))  # where the outer skirt cards start
    ys_nom = yb + cL * math.sin(math.radians(25))
    has_inner = inner_n[i] > 0
    # ---- leaf cores: dark solid inside, sitting just under where the cards start (stepped, never a big box)
    if has_inner:
        cores = [(rs_nom - 0.5, ys_nom - 3, ys_nom + 0.5),            # wide low core under the outer ring
                 (0.62 * rs_nom, ys_nom, yt - 1 - (0.62 * rs_nom) * math.tan(math.radians(32)) - 1)]  # under the inner ring
    else:
        rc = max(4.5 if i < 10 else 3.5, rs_nom + 1.5)
        # fill up to just under the next tier's skirt, so no bare trunk shows between tiers
        if i + 1 < NT:
            yb_n = y_top[i + 1] - hs[i + 1]
            top = min(yt, yb_n + T20 * (Rs[i + 1] - rc) - 0.5)
        else:
            top = ys_nom + 1
        cores = [(rc, ys_nom - 4, top)]
    for ci, (rc, c1, c2) in enumerate(cores):
        a = max(1.5, h2(rc / math.sqrt(2))); c1, c2 = h2(c1), h2(c2)
        if c2 - c1 < 1.5: continue
        ox = oz = 0.0
        if gl is not None:  # pull the core away from the glimpse side so the trunk shows
            ox, oz = -math.sin(math.radians(gl)) * (a - 2.5), -math.cos(math.radians(gl)) * (a - 2.5)
        frm = [lx + ox - a, c1, lz + oz - a]; to = [lx + ox + a, c2, lz + oz + a]
        sz, hz = 2 * a, c2 - c1
        faces = {f: core_face(sz, hz) for f in ("north", "south", "east", "west")}
        faces["up"] = core_face(sz, sz); faces["down"] = core_face(sz, sz)
        cube(f"tier_{i + 1}_core_{ci + 1}", g, frm, to, faces,
             rotation=(0, (i * 29 + ci * 45) % 90, 0) if gl is None else (0, 0, 0), origin=[lx, yt, lz])
    # ---- outer skirt cards: radiate round the trunk, droop 20 to 30 degrees, twist 5 to 15 degrees
    n = skirt_n[i]
    cross_at = set(round(j * n / crossed_n[i]) + 1 for j in range(crossed_n[i]))
    for c in range(n):
        yaw = i * 17 + c * 360 / n + rng.uniform(-8, 8)
        if in_gap(yaw, gl, n): continue
        droop = rng.uniform(20, 30); twist = rng.choice([-1, 1]) * rng.uniform(5, 15)
        broken = rng.random() < 0.15  # 10 to 20% pushed further out / lower
        rs = max(0.5, R - cL * math.cos(math.radians(droop)) + rng.uniform(-1.0, 0.5) + (2.5 if broken else 0))
        ys = yb + cL * math.sin(math.radians(droop)) + rng.uniform(-1, 1) - (1.5 if broken else 0)
        P0 = at(lx, lz, rs, yaw, ys)
        rot = add_card(f"tier_{i + 1}_card_{c + 1}", g, k, P0, yaw, droop, twist)
        if c in cross_at:  # crossed pair at the tip: vertical card at 90 degrees
            k2 = smaller(k); w2, L2, _ = VARIANTS[k2]
            z1 = P0[2] + cL - L2 + 0.5
            cube(f"tier_{i + 1}_card_{c + 1}_cross", g, [P0[0], P0[1] - w2 / 2, z1], [P0[0], P0[1] + w2 / 2, z1 + L2],
                 {"east": F(f"card_{k2}", rot=90)}, rotation=rot, origin=P0)
    # ---- inner ring: steeper cards from the trunk out to the outer ring, so the inside of the skirt is covered
    if has_inner:
        span = (rs_nom + 1.5) / math.cos(math.radians(32))
        k_in = pick_variant(span)
        for c in range(inner_n[i]):
            yaw = i * 17 + (c + 0.5) * 360 / inner_n[i] + rng.uniform(-10, 10)
            if in_gap(yaw, gl, inner_n[i] * 2): continue
            add_card(f"tier_{i + 1}_inner_card_{c + 1}", g, k_in, at(lx, lz, 1.0, yaw, yt - 0.5), yaw,
                     rng.uniform(30, 35), rng.choice([-1, 1]) * rng.uniform(5, 15))
    # ---- 2 top cards, gently tilted, so the top of the tier isn't bare
    for t in range(2):
        k2 = smaller(k)
        yaw = i * 41 + t * 180 + rng.uniform(-30, 30)
        add_card(f"tier_{i + 1}_top_card_{t + 1}", g, k2, [lx, yt + 0.5, lz], yaw, rng.uniform(8, 14), rng.uniform(-10, 10))

# ---- pointed leader: thin vertical stem wrapped in 3 crossed cards that come to a point
lx, lz = lean(140), -lean(140)
ly0 = h2(y_top[-1] - 2)
cube("leader", "tier_13", [lx - 0.75, ly0, lz - 0.75], [lx + 0.75, 141, lz + 0.75],
     rects_for("leader", [0, ly0, 0], [1.5, 141, 1.5], lambda f: (lambda W, H: paint_bark(W, H, f, base_ao=False)), hidden=("down",)))
w5, L5, _ = VARIANTS["v5"]
for j, yaw in enumerate((0, 45, 90, 135)):
    y1 = 144 - L5 - j * 2
    frm = [lx, y1, lz - w5 / 2]; to = [lx, y1 + L5, lz + w5 / 2]
    cube(f"leader_card_{j + 1}", "tier_13", frm, to, {"east": F("card_v5", rot=180)}, rotation=(0, yaw, 0), origin=[lx, y1, lz])

# ---- ground details
def detail_cube(name, frm, to, painter, yaw=0, hidden=("down",), origin=None):
    faces = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        if f in hidden: faces[f] = None; continue
        W, H = (px(v) for v in face_dims(frm, to, f))
        faces[f] = F(atlas.add(f"{name}:{f}", W, H, lambda W2, H2, f=f: painter(W2, H2, f)))
    cube(name, g_details, frm, to, faces, rotation=(0, yaw, 0), origin=origin)

for i, (x, z, yaw) in enumerate([(11.5, -5, 32), (-9.5, 10, 118)]):
    detail_cube(f"pine_cone_{i + 1}", [x - 1, 0, z - 1.5], [x + 1, 2, z + 1.5], lambda W, H, f: paint_scales("cone", W, H, f), yaw=yaw, origin=[x, 0, z])
    detail_cube(f"pine_cone_{i + 1}_stem", [x - 0.5, 0.5, z + 1.5], [x + 0.5, 1.5, z + 2.5], lambda W, H, f: paint_plain("cone", W, H, f, 1.5), yaw=yaw, origin=[x, 0, z])
for i, (x, z, yaw) in enumerate([(13, 6, 15), (-12, -6, 70), (4, 13, 140), (-4, -13, 200)]):
    detail_cube(f"needle_litter_{i + 1}", [x - 1, 0, z - 1], [x + 1, 0.5, z + 1], lambda W, H, f: paint_plain("dry", W, H, f, 2.0, "needles"), yaw=yaw, origin=[x, 0, z])
mx, mz = -8, -8.5
detail_cube("mushroom_stem", [mx - 0.5, 0, mz - 0.5], [mx + 0.5, 2.5, mz + 0.5], lambda W, H, f: paint_plain("stem", W, H, f, 2.2), hidden=("down", "up"))
detail_cube("mushroom_cap", [mx - 1.5, 2.5, mz - 1.5], [mx + 1.5, 3.5, mz + 1.5], lambda W, H, f: paint_plain("cap", W, H, f, 2.6, "gills" if f == "down" else "spots"), hidden=())
detail_cube("mushroom_cap_top", [mx - 1, 3.5, mz - 1], [mx + 1, 4, mz + 1], lambda W, H, f: paint_plain("cap", W, H, f, 2.8, "spots"))

# ---------------------------------------------------------------- pack + resolve UVs
img, used_h = atlas.pack()
for e in elements:
    for f, fd in e["faces"].items():
        s = fd.pop("_spec", None)
        if s:
            fd["uv"] = atlas.uv(s["key"], s["mirror"], s["sub"])
            if s["rot"]: fd["rotation"] = s["rot"]

os.makedirs(OUT_DIR, exist_ok=True)
Image.fromarray(img, "RGBA").save(os.path.join(OUT_DIR, f"{NAME}.png"))
buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

def group_json(g):
    return {"name": g["name"], "uuid": g["uuid"], "export": True, "locked": False, "scope": 0, "selected": False,
            "visibility": True, "_static": {"properties": {}, "temp_data": {}}, "origin": g["origin"],
            "rotation": [0, 0, 0], "color": 0, "children": [], "reset": False, "shade": True, "mirror_uv": False,
            "autouv": 0, "isOpen": g["name"] in (NAME, "canopy"), "primary_selected": False}

def outliner(name):
    g = groups[name]
    return {"uuid": g["uuid"], "isOpen": g["name"] in (NAME, "canopy"),
            "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}

def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(x), "y": str(y), "z": str(z)}], "uuid": new_uuid(),
            "time": t, "color": -1, "interpolation": "linear"}
hit = {"uuid": new_uuid(), "name": "hit", "loop": "once", "override": False, "length": 0.4, "snapping": 24,
       "selected": False, "group_name": "", "scope": 0, "anim_time_update": "", "blend_weight": "",
       "start_delay": "", "loop_delay": "", "animators": {
           groups["canopy"]["uuid"]: {"name": "canopy", "type": "bone", "rotation_global": False, "quaternion_interpolation": False,
               "keyframes": [kf(0, 0, 0, 0), kf(0.06, 1.5, 0, 4), kf(0.14, -1.2, 0, -3), kf(0.24, 0.6, 0, 1.5), kf(0.32, -0.2, 0, -0.5), kf(0.4, 0, 0, 0)]},
           groups["trunk"]["uuid"]: {"name": "trunk", "type": "bone", "rotation_global": False, "quaternion_interpolation": False,
               "keyframes": [kf(0, 0, 0, 0), kf(0.06, 0, 0, 1), kf(0.18, 0, 0, -0.5), kf(0.4, 0, 0, 0)]}}}

model = {
    "meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
    "name": NAME, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
    "multi_file_ruleset": "", "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
    "resolution": {"width": TEX, "height": TEX},
    "elements": elements, "groups": [group_json(g) for g in groups.values()], "outliner": [outliner(NAME)],
    "textures": [{"name": f"{NAME}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                  "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                  "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                  "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                  "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                  "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": new_uuid(), "source": src}],
    "animations": [hit],
}
with open(os.path.join(OUT_DIR, f"{NAME}.bbmodel"), "w") as fh:
    json.dump(model, fh, separators=(",", ":"))

leafpx = img[..., 3] > 0
colours = len({tuple(p) for p in img.reshape(-1, 4) if p[3]})
ncards = sum(1 for e in elements if "card" in e["name"])
print(f"cubes={len(elements)} cards={ncards} groups={len(groups)} atlas_rows={used_h}/{TEX} colours={colours}")
print("tier tops:", [round(v, 1) for v in y_top], "bottoms:", [round(y_top[i] - hs[i], 1) for i in range(NT)])
