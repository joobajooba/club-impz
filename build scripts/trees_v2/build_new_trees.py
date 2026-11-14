"""The five trees from docs/blockbench_detailed_prompts.md section 3.1 (tree tier table) that had no model yet:
hickory (T5), titanwood (T7), runewood (T8), gembark (T9) and worldbark (T10).

Built the way the doc's leaves-the-Hytale-way and clean-trunk rules say (frostbark_tree is the reference):
- trunk = stacked trunk_<n> sections that each sit inside the one below, flush bark strips, a few low stubs and the
  tree's small signature details; branches are chains of rotated cubes that start inside what they grow from;
- canopy = alpha cards only (no solid leaf cores): outer cards, crossed pairs at the edges, dark inner cards, top cards;
- one embedded texture, 2 px per unit, shared UVs for repeated cards; `hit` animation (canopy + trunk shake);
- `_glow` cubes for the glowing signature details (runes, gem crystals, sap cracks, leaf motes).

The bark/needle painters, the atlas and the rotation helpers are the pine_tree v2 ones (pine_v2_source.py, the
script pine_tree was built with), so the new trees match the existing set.

Usage: py -3 build_new_trees.py <hickory|titanwood|runewood|gembark|worldbark|all>
Output: C:\\Users\\lucas\\blockbench_models\\trees\\<tree>_tree.bbmodel + .png
"""
import os, sys, subprocess
HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\lucas\blockbench_models\trees"
TREES = ["hickory", "titanwood", "runewood", "gembark", "worldbark"]

if __name__ == "__main__" and (len(sys.argv) < 2 or sys.argv[1] == "all"):
    for t in TREES:
        subprocess.run([sys.executable, os.path.abspath(__file__), t], check=True)
    sys.exit()

KIND = sys.argv[1]
_src = open(os.path.join(HERE, "pine_v2_source.py"), encoding="utf8").read()
_argv = sys.argv
sys.argv = [_argv[0], OUT]
exec(_src[:_src.index("# ---------------------------------------------------------------- model")])  # helpers, atlas, ramps
sys.argv = _argv
sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
import fix_texture_bleed

NAME = f"{KIND}_tree"


def R_(s): return [hexc(c) for c in s.split()]


def reseed(s):
    global rng, nrng
    rng = random.Random(s)
    nrng = np.random.default_rng(s)


# ================================================================ scaffolding (as oak_tree / pine_tree)
elements, groups = [], {}
def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

def group(name, origin, parent=None):
    assert name not in groups, name
    groups[name] = {"name": name, "uuid": new_uuid(), "origin": [round(float(v), 3) for v in origin], "children": []}
    if parent: groups[parent]["children"].append(("g", name))
    return name

def cube(name, grp, frm, to, faces, rotation=(0, 0, 0), origin=None):
    origin = origin if origin is not None else [(frm[i] + to[i]) / 2 for i in range(3)]
    fj = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        spec = faces.get(f)
        fj[f] = {"uv": [0, 0, 0, 0], "texture": None} if spec is None else {"_spec": spec, "texture": 0}
    e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
         "allow_mirror_modeling": True, "from": [round(float(v), 4) for v in frm], "to": [round(float(v), 4) for v in to],
         "autouv": 0, "color": 0, "origin": [round(float(v), 4) for v in origin], "faces": fj, "type": "cube",
         "uuid": new_uuid()}
    if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(float(v), 3) for v in rotation]
    elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
    return e

def F(key, mirror=False, sub=None, rot=0): return {"key": key, "mirror": mirror, "sub": sub, "rot": rot}

def rects_for(prefix, frm, to, painter_for, hidden=(), share_sides=True, all_sides=False):
    faces = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        if f in hidden: faces[f] = None; continue
        w, h = (px(v) for v in face_dims(frm, to, f))
        if all_sides and f in ("north", "east", "south", "west") and face_dims(frm, to, "north") == face_dims(frm, to, "east"):
            faces[f] = F(atlas.add(f"{prefix}:side4", w, h, painter_for("north")), mirror=f in ("south", "west"))
        elif share_sides and f in ("east", "west"):
            faces[f] = F(atlas.add(f"{prefix}:side", w, h, painter_for("east")), mirror=(f == "west"))
        else:
            faces[f] = F(atlas.add(f"{prefix}:{f}", w, h, painter_for(f)))
    return faces

def unit(v):
    v = np.asarray(v, float); n = np.linalg.norm(v)
    return v / n if n > 1e-9 else np.array([0.0, 1.0, 0.0])

def dir_rotation(d):
    """Rotation taking local +z onto direction d (yaw round y, then pitch)."""
    d = unit(d)
    yaw = math.degrees(math.atan2(d[0], d[2])); pitch = -math.degrees(math.asin(max(-1, min(1, d[1]))))
    return bb_euler(Ry(yaw) @ Rx(pitch))

def frame_rotation(n, t):
    """Card frame: local y -> normal n, local z -> length t, local x -> n x t."""
    n, t = unit(n), unit(t)
    return bb_euler(np.column_stack([np.cross(n, t), n, t]))

def rand_perp(d):
    a = np.cross(d, unit([rng.uniform(-1, 1), rng.uniform(-1, 1), rng.uniform(-1, 1)]))
    return unit(a)


# ================================================================ painters
def bark(ramp, w, h, face, base=None, moss_rows=0, knots=0, ao=True, extra=None, moss_ramp="moss"):
    """Bark on any ramp: vertical grain, grooves every 3 to 5 px, knots, rounded-form shading (lighter centre,
    darker sides and bottom), soft contact shadow at the base, moss creeping up."""
    n = len(RAMPS[ramp]); b = n * 0.5 if base is None else base
    L = FACE_LIGHT[face] * 0.75
    if face == "up":
        f = np.full((h, w), b + 1.0) + noise(w, h, 0.5) + grain(w, h) * 0.25
    elif face == "down":
        f = np.full((h, w), b - 1.4) + noise(w, h, 0.4)
    else:
        f = np.full((h, w), b + L) + grain(w, h) * 0.85 + noise(w, h, 0.4)
        f += np.linspace(0.35, -0.45, h)[:, None]
        if w > 3:
            xs = np.arange(w); c = (w - 1) / 2
            f -= ((np.abs(xs - c) / c) ** 2 * 0.7)[None, :]
        if ao: ao_edge(f, 2, 1.0)
        for _ in range(knots):
            if w > 5 and h > 12:
                knot(f, int(nrng.integers(2, w - 2)), int(nrng.integers(4, h - 8)))
    if extra is not None: f = extra(f, w, h, face)
    f = np.clip(f, 0, n - 1)
    rgb = ramp_colour(ramp, f)
    if moss_rows and face != "down":
        mv = np.full((h, w), 2.4 + L * 0.6) + noise(w, h, 0.9)
        if face == "up":
            m = nrng.random((h, w)) < 0.5
        else:
            m = np.zeros((h, w), bool)
            for x in range(w):
                m[max(0, h - moss_rows + int(nrng.integers(-3, 3))):, x] = True
            m &= nrng.random((h, w)) < 0.85
        rgb[m] = ramp_colour(moss_ramp, mv)[m]
    return rgb, np.ones((h, w), bool)

def plain(ramp, w, h, face, base=2.5, spots=None):
    f = np.full((h, w), base + FACE_LIGHT[face]) + noise(w, h, 0.45)
    if face not in ("up", "down"):
        f += np.linspace(0.4, -0.5, h)[:, None]
    rgb = ramp_colour(ramp, np.clip(f, 0, len(RAMPS[ramp]) - 1))
    if spots:
        for _ in range(max(1, w * h // 14)):
            x, y = int(nrng.integers(0, w)), int(nrng.integers(0, h))
            rgb[y:y + 2, x:x + 1 + int(nrng.integers(0, 2))] = RAMPS[spots][int(nrng.integers(0, len(RAMPS[spots])))]
    return rgb, np.ones((h, w), bool)

def gem(ramp, w, h, face):
    """Glowing crystal face: facet split, bright upper-left, an almost white centre streak."""
    n = len(RAMPS[ramp])
    yy, xx = np.mgrid[0:h, 0:w]
    U = (xx + 0.5) / w; V = (yy + 0.5) / h
    f = np.full((h, w), n * 0.55 + FACE_LIGHT[face] * 0.6) + np.where(U + V < 1.0, 0.9, -0.5) - V * 0.6
    f += np.clip(1 - np.abs(U - 0.5) * 3, 0, 1) * 1.2
    rgb = ramp_colour(ramp, np.clip(f, 0, n - 1))
    if face in ("up", "north", "west") and w >= 2 and h >= 3:
        rgb[1, w // 2] = RAMPS[ramp][-1]
    return rgb, np.ones((h, w), bool)

def stamp(val, x, y, L, W, th, body):
    """One pointed oval leaf: shadow under it, body, 1 px light top edge, a darker vein."""
    h, w = val.shape
    ct, st = math.cos(th), math.sin(th)
    ys, xs = np.mgrid[0:h, 0:w]
    du = (xs - x) * ct + (ys - y) * st; dv = -(xs - x) * st + (ys - y) * ct
    wid = (W / 2) * np.clip(1 - np.abs(du) / (L / 2), 0, 1) ** 0.6
    inside = (np.abs(du) <= L / 2) & (np.abs(dv) <= wid + 0.35)
    if not inside.any(): return
    below = np.roll(inside, 1, 0) & ~inside & (val > -5)
    val[below] = np.maximum(val[below] - 1.0, 0.4)
    val[inside] = body
    top = inside & ~np.roll(inside, 1, 0)
    val[top] = body + 1.0
    vein = inside & (np.abs(dv) < 0.4) & (np.abs(du) < L / 2 - 1)
    val[vein] = body - 0.5

def finish(val, ramp, vmax=None):
    n = len(RAMPS[ramp])
    a = val > -5
    v = np.clip(val, 0, (n - 1) if vmax is None else vmax)
    return ramp_colour(ramp, v), a

def clump_card(w, h, ramp, shade, seed, vmax=None, size=(3, 6), accents=None):
    """Broadleaf clump card: 3 to 6 px leaves in a lumpy rounded outline, dark base (top rows) to light tip."""
    r = random.Random(seed)
    val = np.full((h, w), -9.0)
    cx, cy = (w - 1) / 2, (h - 1) / 2
    pts = []
    for _ in range(int(w * h / 9)):
        ang = r.uniform(0, 2 * math.pi); rad = math.sqrt(r.random()) * 0.92
        pts.append((cy + math.sin(ang) * rad * (h / 2 - 1.5), cx + math.cos(ang) * rad * (w / 2 - 1.5)))
    pts.sort()
    for (y, x) in pts:
        along = y / (h - 1)
        stamp(val, x, y, r.uniform(*size), r.uniform(2, 3.2), r.uniform(-0.9, 0.9) + math.pi / 2,
              3.0 + along * 1.4 + shade + r.uniform(-0.3, 0.3))
    rgb, a = finish(val, ramp, vmax)
    if accents: accents(rgb, a, r)
    return rgb, a

def pinnate_card(w, h, ramp, shade, seed, vmax=None, accents=None):
    """Compound leaves (hickory): 2 to 3 stems from the base, each with pairs of pointed leaflets angled to the tip."""
    r = random.Random(seed)
    val = np.full((h, w), -9.0)
    cx = (w - 1) / 2
    stems = []
    for i in range(r.randint(2, 3)):
        x0 = cx + r.uniform(-1, 1); x1 = cx + (i - 1) * w * 0.28 + r.uniform(-1, 1)
        stems.append((x0, 0.5, x1, h - 1.5 - r.uniform(0, h * 0.15)))
    for (x0, y0, x1, y1) in stems:
        n = int(y1 - y0)
        for s in range(n + 1):  # stem, 1 px
            t = s / max(1, n); x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            xi, yi = int(round(x)), int(round(y))
            if 0 <= xi < w and 0 <= yi < h: val[yi, xi] = max(val[yi, xi], 1.4 + t * 1.2 + shade)
        ang = math.atan2(y1 - y0, x1 - x0)
        k = 2.5
        while k < n - 1:
            t = k / n; x, y = x0 + (x1 - x0) * t, y0 + (y1 - y0) * t
            body = 2.8 + t * 1.6 + shade + r.uniform(-0.3, 0.3)
            for side in (-1, 1):
                th = ang + side * r.uniform(0.6, 0.9)
                Lf = r.uniform(3.5, 5.5) * (0.75 + 0.25 * math.sin(math.pi * t))
                stamp(val, x + math.cos(th) * Lf * 0.45, y + math.sin(th) * Lf * 0.45, Lf, r.uniform(1.8, 2.6), th, body)
            k += r.uniform(2.6, 3.4)
        stamp(val, x1, y1, 4.5, 2.4, ang, 3.0 + 1.6 + shade)  # end leaflet
    rgb, a = finish(val, ramp, vmax)
    if accents: accents(rgb, a, r)
    return rgb, a

def strand_card(w, h, ramp, seed, flower=None, shade=0.0):
    """Hanging strands (runewood): vines from the top edge down, small leaves alternating, darker at the top."""
    r = random.Random(seed)
    val = np.full((h, w), -9.0)
    xs = sorted(r.uniform(1, w - 2) for _ in range(max(2, w // 3)))
    for x0 in xs:
        L = int(h * r.uniform(0.6, 1.0)) - 1
        x = x0; side = r.choice([-1, 1])
        for y in range(L):
            x += r.uniform(-0.35, 0.35); x = min(max(x, 0.5), w - 1.5)
            t = y / max(1, h - 1)
            xi = int(round(x))
            val[y, xi] = max(val[y, xi], 1.2 + t * 1.6 + shade)
            if y % 3 == 1:
                lx = xi + side; side = -side
                for dy, dv in ((0, 0.0), (1, 0.5), (-1, -0.6)):
                    yy = y + dy
                    if 0 <= lx < w and 0 <= yy < h:
                        val[yy, lx] = max(val[yy, lx], 2.4 + t * 2.0 + shade + dv)
                lx2 = lx + (1 if lx > xi else -1)
                if 0 <= lx2 < w: val[y, lx2] = max(val[y, lx2], 2.0 + t * 2.0 + shade)
        val[L, int(round(x))] = 3.6 + shade  # leaf at the tip
    rgb, a = finish(val, ramp)
    if flower:
        idx = np.argwhere(a)
        for j in nrng.choice(len(idx), max(1, len(idx) // 40), replace=False):
            y, x = idx[j]; rgb[y, x] = RAMPS[flower][int(nrng.integers(2, len(RAMPS[flower])))]
    return rgb, a

def glyph_card(w, h, ramp, seed):
    """A carved, glowing rune: a stave with 2 to 3 strokes and a dot, a 1 px dim halo round the strokes."""
    r = random.Random(seed)
    core = np.zeros((h, w), bool)
    cx = w // 2
    core[1:h - 1, cx] = True
    for _ in range(r.randint(2, 3)):
        y0 = r.randint(1, h - 4); d = r.choice([-1, 1]); up = r.choice([-1, 1])
        for k in range(1, r.randint(2, max(3, w // 2)) + 1):
            x, y = cx + d * k, y0 + up * k
            if 0 <= x < w and 0 <= y < h: core[y, x] = True
    core[h - 2 if r.random() < 0.5 else 1, max(0, cx - 2)] = True
    halo = np.zeros_like(core)
    for dy in (-1, 0, 1):
        for dx in (-1, 0, 1):
            halo |= np.roll(np.roll(core, dy, 0), dx, 1)
    halo &= ~core
    n = len(RAMPS[ramp])
    v = np.where(core, n - 1.5, 1.0)
    v[core & (np.arange(h)[:, None] % 3 == 0)] = n - 1
    rgb = ramp_colour(ramp, v)
    return rgb, core | halo

def crack_card(w, h, ramp, seed):
    """Glowing sap crack: a zigzag down the card with short side forks, bright core, dim 1 px halo."""
    r = random.Random(seed)
    core = np.zeros((h, w), bool)
    x = w / 2
    for y in range(h):
        x += r.choice([-1, 0, 0, 1]) * 0.8; x = min(max(x, 1), w - 2)
        core[y, int(round(x))] = True
        if r.random() < 0.08:
            d = r.choice([-1, 1]); xx = int(round(x))
            for k in range(1, r.randint(2, 4)):
                if 0 <= xx + d * k < w and y + k < h: core[y + k, xx + d * k] = True
    halo = np.zeros_like(core)
    for dx in (-1, 1):
        halo |= np.roll(core, dx, 1)
    halo &= ~core
    n = len(RAMPS[ramp])
    v = np.where(core, n - 1.5, 1.5)
    v[core & (nrng.random((h, w)) < 0.3)] = n - 1
    return ramp_colour(ramp, v), core | halo

def detailed_leaf_card(w, h, ramp, shade, seed, style="blade", glint=None):
    """A twig of individual, detailed leaves. The twig runs from the base (top row) to the tip; leaves alternate
    along it on short stalks, pointing towards the tip, each painted on its own:
    - blade: a pointed leaf with a serrated edge, a pale midrib, paired side veins, the upper half lit and the
      lower half in shadow, a light rim on the lit edge;
    - fan: a fan-shaped leaf with a wavy outer edge and a notch in the middle, radiating veins, lighter towards
      the rim. Dark at the base of the card, light at the tip; everything else is transparent."""
    r = random.Random(seed)
    n = len(RAMPS[ramp])
    val = np.full((h, w), -9.0)
    ys, xs = np.mgrid[0:h, 0:w]
    cx = (w - 1) / 2 + r.uniform(-1, 1)
    tip = (cx + r.uniform(-w * 0.12, w * 0.12), h * 0.92)
    def twig_at(t): return cx + (tip[0] - cx) * t, 0.5 + (tip[1] - 0.5) * t
    leaves = []
    t, side = 0.08, r.choice([-1, 1])
    while t < 0.95:
        leaves.append((t, side)); side = -side
        t += r.uniform(0.055, 0.085)
    leaves.append((1.0, 0))
    # twig
    for k in range(int(h * 1.2)):
        x, y = twig_at(k / (h * 1.2))
        xi, yi = int(round(x)), int(round(y))
        if 0 <= xi < w and 0 <= yi < h: val[yi, xi] = max(val[yi, xi], 1.0 + shade + 0.8 * k / (h * 1.2))
    for (t, side) in leaves:
        ax, ay = twig_at(t)
        ang = math.radians(90 - side * r.uniform(35, 60))           # out to the side, pointing to the tip
        L = h * r.uniform(0.24, 0.32) * (0.8 + 0.4 * math.sin(math.pi * min(t, 0.95)))
        if side == 0: ang, L = math.radians(90), h * 0.22
        stalk = 2.0
        sx, sy = ax + math.cos(ang) * stalk, ay + math.sin(ang) * stalk
        for k in range(int(stalk * 2) + 1):                          # leaf stalk
            xi, yi = int(round(ax + math.cos(ang) * k / 2)), int(round(ay + math.sin(ang) * k / 2))
            if 0 <= xi < w and 0 <= yi < h: val[yi, xi] = max(val[yi, xi], 1.4 + shade + t)
        ca, sa = math.cos(ang), math.sin(ang)
        u = (xs - sx) * ca + (ys - sy) * sa                          # along the leaf
        v = -(xs - sx) * sa + (ys - sy) * ca                         # across it
        body = 2.6 + t * 1.8 + shade + r.uniform(-0.25, 0.25)
        if style == "blade":
            W = L * r.uniform(0.4, 0.48)
            q = np.clip(u / L, 0, 1)
            half = (W / 2) * np.sin(np.pi * q ** 0.75) ** 0.9
            serr = ((np.floor(u) % 3) == 0) & (np.abs(v) > half - 1.2)   # notches along the edge
            inside = (u >= 0) & (u <= L) & (np.abs(v) <= half) & ~serr
            f = body + np.where(v < 0, 0.6, -0.5)                     # upper half lit, lower half shaded
            f = f - (np.abs(v) / np.maximum(half, 0.5)) * 0.4
            side_vein = (np.abs(((u - np.abs(v) * 1.3) % 4.0) - 0.5) < 0.5) & (np.abs(v) > 0.8)
            f = np.where(side_vein, f - 0.7, f)
            f = np.where(np.abs(v) < 0.5, body + 1.1, f)               # pale midrib
            rim = inside & (np.abs(v) > half - 1.0) & (v < 0)
            f = np.where(rim, body + 1.2, f)
        else:  # fan
            R = L * 0.62
            rho = np.hypot(u, v); phi = np.arctan2(v, u)
            spread = math.radians(r.uniform(44, 56))
            edge = R * (1 + 0.06 * np.sin(phi * 9))
            notch = (rho > R * 0.7) & (np.abs(phi) < 0.11)
            inside = (rho <= edge) & (np.abs(phi) <= spread) & (u > 0) & ~notch
            f = body - 0.6 + (rho / R) * 1.4 + np.where(phi < 0, 0.3, -0.3)
            vein = (np.abs(((phi / 0.16) % 1.0) - 0.5) < 0.17) & (rho > 2)
            f = np.where(vein, f - 0.7, f)
            f = np.where(inside & (rho > edge - 1.2), body + 1.4, f)     # bright rim
        below = np.roll(inside, 1, 0) & ~inside & (val > -5)
        val[below] = np.maximum(val[below] - 0.8, 0.4)                # soft shadow under the leaf
        val[inside] = f[inside]
    a = val > -5
    rgb = ramp_colour(ramp, np.clip(val, 0, n - 1))
    if glint:
        idx = np.argwhere(a)
        for j in nrng.choice(len(idx), max(1, len(idx) // 90), replace=False):
            y, x = idx[j]; rgb[y, x] = RAMPS[glint][-1]
    return rgb, a

def sparkles(ramp_name, frac=0.012):
    """Accent: a few crystal sparkles (a bright pixel with a dimmer plus round it)."""
    def acc(rgb, a, r):
        idx = np.argwhere(a)
        h, w = a.shape
        for _ in range(max(1, int(len(idx) * frac / 5))):
            y, x = idx[r.randrange(len(idx))]
            rgb[y, x] = RAMPS[ramp_name][-1]
            for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0)):
                yy, xx = y + dy, x + dx
                if 0 <= yy < h and 0 <= xx < w and a[yy, xx]: rgb[yy, xx] = RAMPS[ramp_name][-2]
    return acc

def dots(ramp_name, frac=0.01, size=2):
    def acc(rgb, a, r):
        idx = np.argwhere(a[:-size, :-size])
        for _ in range(max(1, int(len(idx) * frac / (size * size)))):
            y, x = idx[r.randrange(len(idx))]
            for dy in range(size):
                for dx in range(size):
                    rgb[y + dy, x + dx] = RAMPS[ramp_name][min(len(RAMPS[ramp_name]) - 1, 1 + dy + dx)]
    return acc


# ================================================================ parts
VAR = {}  # card key -> (width, length) in units

def card_variant(k, w, L, painter):
    VAR[k] = (w, L)
    atlas.add(f"card_{k}", px(w), px(L), painter)

def nearest(keys, length):
    return min(keys, key=lambda k: abs(VAR[k][1] - length))

def card(name, g, k, p, n, t):
    """Zero-thickness alpha card centred at p, facing n, its length along t (base at p - t L/2, tip at p + t L/2)."""
    w, L = VAR[k]
    n = unit(n); t = np.asarray(t, float); t = unit(t - np.dot(t, n) * n)
    p = np.asarray(p, float)
    return cube(name, g, [p[0] - w / 2, p[1], p[2] - L / 2], [p[0] + w / 2, p[1], p[2] + L / 2],
                {"up": F(f"card_{k}")}, rotation=frame_rotation(n, t), origin=list(p))

def radial_card(name, g, k, P0, yaw, droop, twist):
    """Card from its base P0 outward at this yaw, drooping down and twisted about its length (pine_tree's skirt card)."""
    w, L = VAR[k]
    rot = card_rotation(yaw, droop, twist)
    cube(name, g, [P0[0] - w / 2, P0[1], P0[2]], [P0[0] + w / 2, P0[1], P0[2] + L], {"up": F(f"card_{k}")}, rotation=rot, origin=list(P0))
    return rot

def cross_card(name, g, k, P0, rot, base_len):
    """Vertical card at 90 degrees to a radial card, at its tip (crossed pair)."""
    w2, L2 = VAR[k]
    z1 = P0[2] + base_len - L2 + 0.5
    cube(name, g, [P0[0], P0[1] - w2 / 2, z1], [P0[0], P0[1] + w2 / 2, z1 + L2], {"east": F(f"card_{k}", rot=90)}, rotation=rot, origin=list(P0))

def at(c, r, yaw, y): return [c[0] + r * math.sin(math.radians(yaw)), y, c[2] + r * math.cos(math.radians(yaw))]

WILD_PIECES = []   # (start, direction, length, height, half width) of every wandering root piece

def add_wild_roots(g, ramp, n_roots, templates, fork_templates, moss_idx, trunk_r, base=None, seed_yaw=0.0):
    """Roots that wander like real ones: each piece turns 10 to 35 degrees off the one before (mostly curving one
    way, sometimes doubling back), dips or rises a few degrees, and starts just inside the end of the piece before.
    Roots differ in length (4 to 6 pieces), in which size template each piece takes, and some fork into a side root.
    Pieces of the same template and moss share their paint."""
    yaws = sorted((seed_yaw + k * 360 / n_roots + rng.uniform(-14, 14)) % 360 for k in range(n_roots))
    def piece(name, P, heading, pitch, tmpl, key, moss_rows):
        hw, ht, L = tmpl
        d = np.array([math.sin(math.radians(heading)) * math.cos(math.radians(pitch)), math.sin(math.radians(pitch)),
                      math.cos(math.radians(heading)) * math.cos(math.radians(pitch))])
        frm, to = [P[0] - hw, P[1] - 0.5, P[2]], [P[0] + hw, P[1] + ht, P[2] + L]
        faces = rects_for(key, frm, to, lambda f: (lambda W, H: bark(ramp, W, H, f, base=base, moss_rows=moss_rows)), hidden=("north", "down"))
        cube(name, g, frm, to, faces, rotation=dir_rotation(d), origin=list(P))
        WILD_PIECES.append((np.array(P, float), d, L, ht, hw))
        return np.array(P, float) + d * (L - 1.5)
    names = ["inner", "outer", "tip", "end", "reach", "tail"]
    for i, a in enumerate(yaws):
        m = i in moss_idx
        heading = a
        bend = rng.choice([-1, 1]) * rng.uniform(10, 26)
        P = [math.sin(math.radians(a)) * trunk_r, 0.0, math.cos(math.radians(a)) * trunk_r]
        n = rng.choice([4, 5, 5, 6])
        fork_at = rng.choice([1, 2, 2, 3]) if rng.random() < 0.6 else -1
        for j in range(n):
            t = rng.randrange(len(templates[j]))
            tmpl = templates[j][t]
            pitch = 0.0 if j == 0 else rng.uniform(-5, 3)
            key = f"wroot_{j}_{t}_{'moss' if m else 'bare'}"
            mr = (14, 9, 6, 4, 3, 2)[j] if m else 0
            start = np.array(P, float)
            P = piece(f"root_{i + 1}_{names[j]}", P, heading, pitch, tmpl, key, mr)
            P[1] = min(0.0, P[1])                       # the next piece starts at or under the ground
            if j == fork_at:                             # a side root splitting off this piece
                fh = heading + rng.choice([-1, 1]) * rng.uniform(40, 65)
                fb = rng.choice([-1, 1]) * rng.uniform(10, 25)
                FP = list(start + (P - start) * rng.uniform(0.45, 0.7)); FP[1] = 0.0
                for fj, ft in enumerate(fork_templates):
                    FP = piece(f"root_{i + 1}_fork_{fj + 1}", FP, fh, rng.uniform(-5, 2), ft, f"wfork_{fj}_{'moss' if m else 'bare'}", 4 if m else 0)
                    FP[1] = min(0.0, FP[1])
                    fh += fb
            # meander: keep curving the same way, now and then double back
            if rng.random() < 0.3: bend = -bend
            heading += bend * rng.uniform(0.6, 1.3)

ROOT_PIECES = []

def add_roots(g, ramp, angles, pieces, moss_idx, centre=(0, 0), moss_rows=(7, 5, 3, 2), base=None):
    """Roots flaring from the trunk base, each a chain of pieces stepping down; even/odd roots differ in size,
    and roots of a kind share their paint."""
    ox, oz = centre
    for i, ang in enumerate(angles):
        t = "a" if i % 2 == 0 else "b"; s = 1.0 if t == "a" else 0.85; m = i in moss_idx
        yaw = ang + rng.uniform(-7, 7)
        prev_end = 0.0
        for j, (hw, ht, z0, z1) in enumerate(pieces):
            hw2, ht2 = max(0.5, h2(hw * s)), max(1.0, h2(ht * s))
            z0b = z0 if j == 0 else prev_end - 1.0         # each piece starts inside the one before
            z1b = z0b + max(1.0, h2((z1 - z0) * s))
            prev_end = z1b
            frm, to = [ox - hw2, -0.5, oz + z0b], [ox + hw2, ht2, oz + z1b]
            part = ["inner", "outer", "tip", "end", "reach", "tail"][j]
            faces = rects_for(f"root_{t}_{part}_{'moss' if m else 'bare'}", frm, to,
                              lambda f, m=m, j=j: (lambda W, H: bark(ramp, W, H, f, base=base, moss_rows=moss_rows[min(j, 3)] if m else 0)),
                              hidden=("north", "down"))
            cube(f"root_{i + 1}_{part}", g, frm, to, faces, rotation=(0, yaw, 0), origin=[ox, 0, oz])
            ROOT_PIECES.append((i, j, yaw, z0b, z1b, ht2, hw2, (ox, oz)))

def add_trunk(g, secs, painter_for, share_from=99):
    """secs: [(width, y1, y2, cx, cz)]. Each section starts where the one below ends and fits inside its footprint."""
    for i, (w, y1, y2, cx, cz) in enumerate(secs):
        if i:
            pw, _, py2, pcx, pcz = secs[i - 1]
            assert abs(py2 - y1) < 1e-6, ("gap", i)
            assert abs(cx - pcx) + w / 2 <= pw / 2 + 1e-6 and abs(cz - pcz) + w / 2 <= pw / 2 + 1e-6, ("lip", i)
        frm = [cx - w / 2, y1, cz - w / 2]; to = [cx + w / 2, y2, cz + w / 2]
        hidden = ("down",) + (("up",) if i < len(secs) - 1 else ())
        cube(f"trunk_{i + 1}", g, frm, to,
             rects_for(f"trunk_{i + 1}", frm, to, lambda f, i=i, y2=y2: painter_for(i, f, y2), hidden=hidden,
                       share_sides=False, all_sides=i >= share_from))

def add_strips(g, secs, strips, painter_for, d=1.0):
    """Flush bark strips: (section, side, offset along the face, y1, y2, width)."""
    for i, (s, side, a, y1, y2, sw) in enumerate(strips):
        w, _, _, cx, cz = secs[s]; hw = w / 2
        if side == "north": frm, to = [cx + a, y1, cz - hw - d], [cx + a + sw, y2, cz - hw]
        if side == "south": frm, to = [cx + a, y1, cz + hw], [cx + a + sw, y2, cz + hw + d]
        if side == "east":  frm, to = [cx + hw, y1, cz + a], [cx + hw + d, y2, cz + a + sw]
        if side == "west":  frm, to = [cx - hw - d, y1, cz + a], [cx - hw, y2, cz + a + sw]
        opp = {"north": "south", "south": "north", "east": "west", "west": "east"}[side]
        cube(f"bark_strip_{i + 1}", g, frm, to,
             rects_for(f"bark_strip_{i + 1}", frm, to, lambda f, s=s, y2=y2: painter_for(s, f, y2), hidden=(opp, "down"), share_sides=False))

def face_point(secs, s, side, a, y, out=0.05):
    """A point on a trunk section's face (a along the face from its centre), `out` units off it, and the face normal."""
    w, _, _, cx, cz = secs[s]; hw = w / 2 + out
    return {"north": (np.array([cx + a, y, cz - hw]), np.array([0, 0, -1.0])),
            "south": (np.array([cx + a, y, cz + hw]), np.array([0, 0, 1.0])),
            "east": (np.array([cx + hw, y, cz + a]), np.array([1.0, 0, 0])),
            "west": (np.array([cx - hw, y, cz + a]), np.array([-1.0, 0, 0]))}[side]

def branch(name, g, start, end, thick, ramp, base=None):
    """One rotated branch piece from start to end (its near end hidden inside what it grows from)."""
    start, end = np.array(start, float), np.array(end, float)
    d = end - start; L = max(1.0, h2(np.linalg.norm(d)))
    frm = [start[0] - thick / 2, start[1] - thick / 2, start[2]]; to = [start[0] + thick / 2, start[1] + thick / 2, start[2] + L]
    key = f"branch_{thick}_{L}"
    faces = rects_for(key, [0, 0, 0], [thick, thick, L],
                      lambda f: (lambda W, H: paint_rings(W, H)) if f == "south" else (lambda W, H: bark(ramp, W, H, f, base=base, ao=False)),
                      hidden=("north",), share_sides=True)
    cube(name, g, frm, to, faces, rotation=dir_rotation(d), origin=list(start))
    return start + unit(d) * L

def branch_chain(name, g, pts, thicks, ramp, base=None):
    """A branch of several pieces through the points; each piece starts just inside the end of the one before."""
    p = np.array(pts[0], float)
    for j in range(len(pts) - 1):
        q = np.array(pts[j + 1], float)
        end = branch(f"{name}_{j + 1}" if len(pts) > 2 else name, g, p, q, thicks[j], ramp, base)
        p = end - unit(q - p) * min(1.0, thicks[j] * 0.4)
    return p

def fib_dirs(n):
    out = []
    for i in range(n):
        y = 1 - 2 * (i + 0.5) / n; r = math.sqrt(1 - y * y); a = i * 2.39996
        out.append(np.array([r * math.cos(a), y, r * math.sin(a)]))
    return out

def dome(g_canopy, clusters, dome_c, core_r, keys, cross_key, inner_key, n_cards=8, n_cross=1, n_inner=2, hang=None):
    """Round dome of clusters (oak_tree's layout), cards only: outer cards on each cluster's open side,
    crossed pairs at the silhouette edge, dark inner cards from the cluster centre. keys = (top, side, under)."""
    for ci, (c, rho) in enumerate(clusters):
        c = np.asarray(c, float)
        g = group(f"cluster_{ci + 1}", list(np.round(c, 2)), g_canopy)
        out = unit(c - dome_c)
        cands = []
        rot0 = rng.uniform(0, 2 * math.pi)
        for d in fib_dirs(16):
            d = unit(np.array([d[0] * math.cos(rot0) - d[2] * math.sin(rot0), d[1], d[0] * math.sin(rot0) + d[2] * math.cos(rot0)])
                     + np.array([rng.uniform(-0.15, 0.15) for _ in range(3)]))
            p = c + d * (rho * 0.8 + rng.uniform(-0.8, 1.2))
            ok = np.linalg.norm(p - dome_c) > core_r and all(
                np.linalg.norm(p - np.asarray(c2)) >= r2 * 0.88 for j, (c2, r2) in enumerate(clusters) if j != ci)
            if ok: cands.append((float(np.dot(d, out) + 0.4 * d[1]), d, p))
        cands.sort(key=lambda x: -x[0])
        cards = cands[:n_cards] if len(cands) >= 4 else cands[:4]
        edge = sorted(cards, key=lambda x: abs(x[1][1]))[:n_cross]
        for k_, (_, n, p) in enumerate(cards):
            key = keys[0] if n[1] > 0.3 else keys[1] if n[1] > -0.35 else keys[2]
            t = out + np.array([0, 0.6, 0]) + np.array([rng.uniform(-0.5, 0.5) for _ in range(3)])
            n2 = unit(n + np.array([rng.uniform(-0.25, 0.25) for _ in range(3)]))
            t = t - np.dot(t, n2) * n2
            if np.linalg.norm(t) < 1e-3: t = np.cross(n2, [1, 0, 0])
            t = unit(t)
            card(f"cluster_{ci + 1}_card_{k_ + 1}", g, key, p, n2, t)
            if any(n is e[1] for e in edge):
                L = VAR[key][1]; L2 = VAR[cross_key][1]
                q = p + n * 1.5 + t * (L / 2 - L2 / 2 + 1)
                card(f"cluster_{ci + 1}_card_{k_ + 1}_cross", g, cross_key, q, np.cross(n2, t), t)
        for j in range(n_inner):
            d = unit(out * 0.6 + np.array([rng.uniform(-1, 1), rng.uniform(-0.4, 0.8), rng.uniform(-1, 1)]))
            L = VAR[inner_key][1]
            card(f"cluster_{ci + 1}_inner_card_{j + 1}", g, inner_key, c + d * (L / 2 - 1.5), rand_perp(d), d)
        if hang: hang(g, ci, c, rho, out)

def pad(name, g_parent, c, R, ring_key, top_key, inner_key, cross_key, n_cross=3, rim_key=None, gold=None, gold_frac=0.0, spacing=0.8, curtains=0, curtain_key=None):
    """Layered-crown pad (gembark, worldbark): a thick umbrella of leaf cards, never a flat disc. Rings of cards
    go out from the centre, each ring starting inside the one before and drooping more (about 8, 22, 34 degrees),
    so the rim curls down and the pad is several units deep. A raised top layer covers the top, dark inner
    cards angle down underneath, crossed pairs stand on the rim."""
    g = group(name, list(np.round(c, 2)), g_parent)
    c = np.asarray(c, float)
    cnt = [0]
    def nm(kind):
        cnt[0] += 1; return f"{name}_{kind}_{cnt[0]}"
    yaw0 = rng.uniform(0, 360)
    w, L = VAR[ring_key]
    droops = [(5, 11), (18, 26), (30, 38), (38, 46)]
    r, y, k = 1.0, c[1] + 1.5, 0
    while r < R - 2:
        last = r + L * 0.85 >= R - 2
        key = rim_key if (last and rim_key) else ring_key
        wk, Lk = VAR[key]
        lo, hi = droops[min(k, 3)]
        n = max(6, math.ceil(2 * math.pi * (r + Lk / 2) / (wk * (spacing + 0.2 if last else spacing))))
        cross_at = set(round(j * n / n_cross) for j in range(n_cross)) if last else set()
        for j in range(n):
            yaw = yaw0 + (j + 0.5 * k) * 360 / n + rng.uniform(-7, 7)
            broken = last and rng.random() < 0.18
            droop = rng.uniform(lo, hi) + (6 if broken else 0)
            rr = r + rng.uniform(-0.8, 0.8) + (1.5 if broken else 0)
            P0 = at(c, rr, yaw, y + rng.uniform(-0.6, 0.6))
            if gold and rng.random() < gold_frac:       # glowing gold leaves among the green
                rot = radial_card(nm("gold_card") + "_glow", g, gold[1] if last else gold[0], P0, yaw, droop, rng.choice([-1, 1]) * rng.uniform(4, 12))
            else:
                rot = radial_card(nm("card"), g, key, P0, yaw, droop, rng.choice([-1, 1]) * rng.uniform(4, 12))
            if j in cross_at:
                cross_card(nm("card_cross"), g, cross_key, P0, rot, Lk)
        mid = (lo + hi) / 2
        rim_r, rim_y = r + Lk * math.cos(math.radians(mid)), y - Lk * math.sin(math.radians(mid))
        y -= Lk * 0.8 * math.sin(math.radians(mid))
        r += Lk * 0.8 * math.cos(math.radians(mid))
        k += 1
    for j in range(curtains):                      # sweeping curtains of golden leaves hanging from the rim
        yaw = math.radians(yaw0 + (j + rng.uniform(-0.3, 0.3)) * 360 / curtains)
        d = np.array([math.sin(yaw), 0, math.cos(yaw)])
        Lc = VAR[curtain_key][1]
        q = c + d * (rim_r - 1.5) + np.array([0, rim_y - c[1] + 0.5, 0])
        tdir = unit(np.array([0, -1.0, 0]) + d * 0.18)
        card(nm("curtain") + "_glow", g, curtain_key, q + tdir * Lc / 2, d, tdir)
    nb = 5
    for j in range(nb):
        yaw = yaw0 + 30 + j * 360 / nb + rng.uniform(-10, 10)
        gt = gold and rng.random() < gold_frac
        radial_card(nm("gold_top_card") + "_glow" if gt else nm("top_card"), g, gold[0] if gt else top_key,
                    at(c, 0.5, yaw, c[1] + 3.0 + rng.uniform(-0.3, 0.3)), yaw, rng.uniform(8, 14), rng.choice([-1, 1]) * rng.uniform(4, 12))
    for j in range(4):
        yaw = yaw0 + j * 90 + rng.uniform(-15, 15)
        radial_card(nm("inner_card"), g, inner_key, at(c, 0.5, yaw, c[1] - 0.5), yaw, rng.uniform(40, 52), rng.choice([-1, 1]) * rng.uniform(4, 12))
    return g

def detail(g, name, frm, to, painter, yaw=0, hidden=("down",), origin=None, key=None):
    faces = {}
    for f in ("north", "east", "south", "west", "up", "down"):
        if f in hidden: faces[f] = None; continue
        W, H = (px(v) for v in face_dims(frm, to, f))
        faces[f] = F(atlas.add(f"{key or name}:{f}", W, H, lambda W2, H2, f=f: painter(W2, H2, f)))
    return cube(name, g, frm, to, faces, rotation=(0, yaw, 0), origin=origin)

def crystal(name, g, base, d, size, L, ramp):
    """A glowing crystal: a rotated box from `base` (inside the wood) out along d, with a pointed tip box."""
    d = unit(d)
    frm = [base[0] - size / 2, base[1] - size / 2, base[2]]; to = [base[0] + size / 2, base[1] + size / 2, base[2] + L]
    key = f"gem_{ramp}_{size}_{L}"
    faces = rects_for(key, [0, 0, 0], [size, size, L], lambda f: (lambda W, H: gem(ramp, W, H, f)), hidden=("north",))
    rot = dir_rotation(d)
    cube(f"{name}_glow", g, frm, to, faces, rotation=rot, origin=list(base))
    s2 = max(0.5, h2(size * 0.5)); tb = np.asarray(base) + d * (L - 0.25)
    frm2 = [tb[0] - s2 / 2, tb[1] - s2 / 2, tb[2]]; to2 = [tb[0] + s2 / 2, tb[1] + s2 / 2, tb[2] + 1.0]
    faces2 = rects_for(f"gemtip_{ramp}_{s2}", [0, 0, 0], [s2, s2, 1.0], lambda f: (lambda W, H: gem(ramp, W, H, f)), hidden=("north",))
    cube(f"{name}_tip_glow", g, frm2, to2, faces2, rotation=rot, origin=list(tb))

def face_card(name, g, k, secs, s, side, a, y, out=0.05):
    """A card lying on a trunk face (runes, sap cracks), its length running down the trunk."""
    p, n = face_point(secs, s, side, a, y, out)
    card(name, g, k, p, n, [0, -1, 0])


# ================================================================ output
def kf(t, x, y, z):
    return {"channel": "rotation", "data_points": [{"x": str(x), "y": str(y), "z": str(z)}], "uuid": new_uuid(),
            "time": t, "color": -1, "interpolation": "linear"}

def write(canopy="canopy", trunk="trunk", scale=1):
    img, used_h = atlas.pack()
    if scale != 1:
        for e in elements:
            for k in ("from", "to", "origin"):
                e[k] = [round(v * scale, 4) for v in e[k]]
        for g in groups.values():
            g["origin"] = [round(v * scale, 3) for v in g["origin"]]
    for e in elements:
        for f, fd in e["faces"].items():
            s = fd.pop("_spec", None)
            if s:
                fd["uv"] = atlas.uv(s["key"], s["mirror"], s["sub"])
                if s["rot"]: fd["rotation"] = s["rot"]
    os.makedirs(OUT, exist_ok=True)
    png = os.path.join(OUT, f"{NAME}.png")
    Image.fromarray(img, "RGBA").save(png)
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

    hit = {"uuid": new_uuid(), "name": "hit", "loop": "once", "override": False, "length": 0.4, "snapping": 24,
           "selected": False, "group_name": "", "scope": 0, "anim_time_update": "", "blend_weight": "",
           "start_delay": "", "loop_delay": "", "animators": {
               groups[canopy]["uuid"]: {"name": canopy, "type": "bone", "rotation_global": False, "quaternion_interpolation": False,
                   "keyframes": [kf(0, 0, 0, 0), kf(0.06, 1.5, 0, 4), kf(0.14, -1.2, 0, -3), kf(0.24, 0.6, 0, 1.5), kf(0.32, -0.2, 0, -0.5), kf(0.4, 0, 0, 0)]},
               groups[trunk]["uuid"]: {"name": trunk, "type": "bone", "rotation_global": False, "quaternion_interpolation": False,
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
    out = os.path.join(OUT, f"{NAME}.bbmodel")
    with open(out, "w", encoding="utf8") as fh:
        json.dump(model, fh, indent="\t")
    r = fix_texture_bleed.pad_file(out, [png])
    colours = len({tuple(p) for p in img.reshape(-1, 4) if p[3]})
    ys = [y for e in elements for y in (e["from"][1], e["to"][1])]
    xs = [x for e in elements for x in (e["from"][0], e["to"][0])]
    glow = sum(e["name"].endswith("_glow") for e in elements)
    print(f"{NAME:18s} cubes={len(elements)} cards={sum('card' in e['name'] for e in elements)} glow={glow} "
          f"atlas_rows={used_h}/{TEX} padded={r['size'][1]} colours={colours} height={max(ys):.1f} width~{max(xs) - min(xs):.1f}")


def standard_groups(canopy_y, branches_y=None):
    root = group(NAME, [0, 0, 0])
    return (root, group("roots", [0, 0, 0], root), group("trunk", [0, 0, 0], root),
            group("branches", [0, branches_y if branches_y is not None else canopy_y, 0], root),
            group("canopy", [0, canopy_y, 0], root), group("details", [0, 0, 0], root))


# ================================================================ the trees
def build_hickory():
    """T5, mountain and frost. Tall dome, 96 to 128. Shaggy grey bark with peeling strips; deep olive green
    compound leaves; peeling bark plates sticking out; hickory nuts."""
    global TEX
    TEX = 256
    reseed(5150)
    RAMPS["shag"] = R_("#1a1816 #26231f #34302a #433d36 #544c44 #675e54 #7c7266 #93897b")
    RAMPS["olive"] = R_("#151c0c #1e2810 #283414 #334218 #40521c #4f6422 #61782a #748c34")
    RAMPS["husk"] = R_("#26280e #383a14 #4e501c #666826 #7e8032 #969642")
    RAMPS["nut"] = R_("#36241a #4e3624 #684a30 #82603e #9c7850")
    RAMPS["stone"] = R_("#2a2a2c #3c3c40 #505056 #66666c #7e7e84 #96969c")
    root, g_roots, g_trunk, g_br, g_can, g_det = standard_groups(62, 44)

    add_roots(g_roots, "shag", [10, 66, 122, 178, 236, 298], [(1.75, 6.5, 4.5, 10.5), (1.25, 3.5, 0, 5)], (0, 2, 4))
    secs = [(12, 0, 14, 0, 0), (10.5, 14, 32, 0.5, 0), (9, 32, 50, 0.5, -0.5), (8, 50, 66, 1, -0.5), (6.5, 66, 82, 1, -0.5)]
    def shag_extra(f, w, h, face):
        # shaggy: long light plate edges with a dark gap under them, staggered
        if face in ("up", "down"): return f
        for x in range(1, w - 1, 3):
            y0 = int(nrng.integers(0, max(1, h - 6)))
            ln = int(nrng.integers(4, 10))
            f[y0:y0 + ln, x] += 1.1
            if y0 + ln < h: f[y0 + ln:y0 + ln + 1, x] -= 1.0
        return f
    tp = lambda i, f, y2: (lambda W, H: bark("shag", W, H, f, moss_rows=7 if i == 0 else 0, knots=1 if i in (1, 2) else 0, ao=i == 0, extra=shag_extra))
    add_trunk(g_trunk, secs, tp, share_from=3)
    add_strips(g_trunk, secs, [(0, "north", -4, 0, 12, 2), (0, "east", 1, 0, 11, 1.5), (1, "south", -2, 15, 30, 1.5), (2, "west", -1, 33, 47, 2)],
               lambda s, f, y2: (lambda W, H: bark("shag", W, H, f, moss_rows=4 if s == 0 else 0, ao=s == 0, extra=shag_extra)))
    # peeling bark plates (signature): thin plates hinged at the top, their bottom edge curling away from the trunk
    plate_p = lambda f: (lambda W, H: bark("shag", W, H, f, base=5.0 if f in ("north", "south", "east", "west") else 3.0, ao=False, extra=shag_extra))
    plates = [(0, "south", 2.5, 13, 7), (1, "north", -1, 29, 9), (1, "east", 2, 27, 8), (1, "west", -2.5, 31, 9), (2, "south", 1, 46, 8),
              (2, "east", -2, 44, 7), (3, "north", 1.5, 62, 8), (3, "west", 1, 60, 7)]
    for i, (s, side, a, ytop, ln) in enumerate(plates):
        p, n = face_point(secs, s, side, a, ytop, out=0.0)
        tilt = rng.uniform(9, 15)
        # plate: 2.5 wide, 0.5 thick, ln tall, hanging down from p, rotated outward about its top edge
        if side in ("north", "south"):
            frm = [p[0] - 1.25, ytop - ln, p[2] - (0.5 if side == "south" else 0)]; to = [p[0] + 1.25, ytop, p[2] + (0.5 if side == "south" else 0)]
            frm[2], to[2] = (p[2], p[2] + 0.5) if side == "south" else (p[2] - 0.5, p[2])
            rot = (-tilt if side == "south" else tilt, 0, 0)
        else:
            frm = [p[0] if side == "east" else p[0] - 0.5, ytop - ln, p[2] - 1.25]; to = [p[0] + 0.5 if side == "east" else p[0], ytop, p[2] + 1.25]
            rot = (0, 0, tilt if side == "east" else -tilt)
        cube(f"bark_plate_{i + 1}", g_trunk, frm, to, rects_for(f"plate_{ln}_{side in ('north', 'south')}", frm, to, plate_p, hidden=()),
             rotation=rot, origin=[p[0], ytop, p[2]])
    # stub branch low down
    frm, to = [-0.75, 20 - 0.75, 4.5], [0.75, 20 + 0.75, 9]
    cube("stub_branch_1", g_trunk, frm, to, rects_for("stub", frm, to, lambda f: (lambda W, H: paint_rings(W, H)) if f == "south" else (lambda W, H: bark("shag", W, H, f, ao=False)), hidden=("north",)),
         rotation=(-30, 205, 0), origin=[0.5, 20, 0])

    # canopy: tall dome, 16 clusters, packed so they overlap into one mass
    cl = []
    for k in range(5):
        yaw = math.radians(k * 72 + rng.uniform(-10, 10)); Rr = 14 + rng.uniform(-1.5, 1.5)
        cl.append((np.array([1 + Rr * math.sin(yaw), 66 + rng.uniform(-2, 2), -0.5 + Rr * math.cos(yaw)]), 12 + rng.uniform(-1, 1)))
    for k in range(5):
        yaw = math.radians(k * 72 + 36 + rng.uniform(-10, 10)); Rr = 19 + rng.uniform(-1.5, 1.5)
        cl.append((np.array([1 + Rr * math.sin(yaw), 81 + rng.uniform(-3, 3), -0.5 + Rr * math.cos(yaw)]), 13 + rng.uniform(-1, 1)))
    for k in range(4):
        yaw = math.radians(k * 90 + 15 + rng.uniform(-12, 12)); Rr = 12 + rng.uniform(-1.5, 1.5)
        cl.append((np.array([1 + Rr * math.sin(yaw), 96 + rng.uniform(-2, 2), -0.5 + Rr * math.cos(yaw)]), 12 + rng.uniform(-0.5, 1)))
    cl.append((np.array([3, 106, 2]), 11)); cl.append((np.array([-2, 105, -4]), 10.5))
    dome_c = np.array([1, 86, -0.5])
    # branches to a cluster in each ring
    for j, ci in enumerate((0, 3, 6, 8, 11)):
        c = cl[ci][0]; yawr = math.atan2(c[0] - 1, c[2] + 0.5)
        y0 = 40 + j * 5
        s = np.array([1 + 3 * math.sin(yawr), y0, -0.5 + 3 * math.cos(yawr)])
        mid = s + (c - s) * 0.5 + np.array([0, 3, 0])
        branch_chain(f"limb_{j + 1}", g_br, [s, mid, c - np.array([0, 2, 0])], [2.5, 2.0], "shag")

    nuts = lambda rgb, a, r: dots("husk", 0.012, 2)(rgb, a, r)
    card_variant("big_light", 10, 16, lambda W, H: pinnate_card(W, H, "olive", 1.2, 51))
    card_variant("big_mid", 10, 16, lambda W, H: pinnate_card(W, H, "olive", 0.5, 52, accents=nuts))
    card_variant("med_light", 9, 13, lambda W, H: pinnate_card(W, H, "olive", 1.4, 53))
    card_variant("med_dark", 9, 13, lambda W, H: pinnate_card(W, H, "olive", -0.6, 54))
    card_variant("small_light", 6, 9, lambda W, H: pinnate_card(W, H, "olive", 1.5, 55))
    card_variant("inner", 8, 12, lambda W, H: clump_card(W, H, "olive", -2.2, 56, vmax=1.5))
    big = [c for c in cl if c[1] >= 11.5]
    dome(g_can, cl, dome_c, 10.0, ("big_light", "big_mid", "med_dark"), "small_light", "inner", n_cards=9, n_cross=1, n_inner=3)

    # ground: hickory nuts (husk splitting open), fallen leaflets, a stone, a peeled bark plate
    for i, (x, z) in enumerate([(15, -5), (-13, 9), (6, 16)]):
        detail(g_det, f"hickory_nut_{i + 1}", [x - 0.75, 0, z - 0.75], [x + 0.75, 1.5, z + 0.75], lambda W, H, f: plain("husk", W, H, f, 2.6), key="nut")
        detail(g_det, f"hickory_nut_{i + 1}_shell", [x - 0.5, 1.5, z - 0.5], [x + 0.5, 2.0, z + 0.5], lambda W, H, f: plain("nut", W, H, f, 2.5), key="nutshell")
    for i, (x, z, yaw) in enumerate([(17, 6, 20), (-16, -6, 75), (-5, 18, 130), (9, -16, 200)]):
        detail(g_det, f"fallen_leaf_{i + 1}", [x - 1.5, 0, z - 1], [x + 1.5, 0.5, z + 1], lambda W, H, f: plain("olive", W, H, f, 3.4), yaw=yaw, origin=[x, 0, z], key="fallen")
    detail(g_det, "stone_1", [-16, 0, 1], [-13.5, 2, 3.5], lambda W, H, f: plain("stone", W, H, f, 2.6), yaw=25, origin=[-14.75, 0, 2.25])
    write()


def build_titanwood():
    """T7, plains and swamp. Very tall cone/column, 160 to 192. Steel grey bark with silver bands; deep teal
    needles; huge root buttresses; metal-like sheen lines in the bark."""
    global TEX, LEAF_MAX
    TEX = 256
    reseed(7170)
    RAMPS["steel"] = R_("#14171c #1e232a #2a3039 #373e49 #464e5a #57606d #6a7483 #7f8a99")
    RAMPS["silver"] = R_("#5d6672 #7a8490 #98a2ad #b8c0c8 #d4dadf")
    RAMPS["leaf"] = R_("#08181a #0c2426 #113234 #174242 #1e5350 #27645e #33776c #428a7a")
    RAMPS["dry"] = R_("#3a3e44 #565c64 #767e88 #98a0aa #b8c0c8")       # silver dead needles as the accent
    RAMPS["cone"] = R_("#22262c #343a42 #4a525c #646e7a #808a96 #a0aab4")
    RAMPS["stone"] = R_("#2a2c30 #3c3f44 #50545a #666a70 #7e8288 #96999e")
    LEAF_MAX = 6.0
    root, g_roots, g_trunk, g_br, g_can, g_det = standard_groups(44)

    def metal(y_top):
        def ex(f, w, h, face):
            if face in ("up", "down"): return f
            ys = y_top - (np.arange(h) + 0.5) / PPU
            band = (ys % 21.0) < 1.5                         # silver bands round the trunk, level all the way round
            f[band, :] = np.maximum(f[band, :], 6.0) + 0.6
            f[np.roll(band, 1), :] -= 0.6                     # soft shadow under each band
            for x in range(1, w - 1):                         # sheen lines: broken light streaks along the grain
                if nrng.random() < 0.16:
                    y0 = int(nrng.integers(0, max(1, h - 4))); ln = int(nrng.integers(3, 12))
                    f[y0:y0 + ln, x] += 1.6
            return f
        return ex
    # huge root buttresses: thin tall fins stepping down
    add_roots(g_roots, "steel", [15, 78, 140, 200, 262, 320], [(1.0, 24, 5, 12), (1.0, 13, 0, 7), (0.75, 6, 0, 6), (0.5, 2.5, 0, 4)], (1, 3, 5))
    secs = [(16, 0, 20, 0, 0), (14, 20, 46, 0.5, 0), (12, 46, 76, 0.5, 0.5), (10, 76, 106, 1, 0.5), (8, 106, 134, 1, 1), (6, 134, 160, 1.5, 1), (4, 160, 176, 1.5, 1)]
    tp = lambda i, f, y2: (lambda W, H: bark("steel", W, H, f, moss_rows=6 if i == 0 else 0, knots=1 if i < 2 else 0, ao=i == 0, extra=metal(y2)))
    add_trunk(g_trunk, secs, tp, share_from=2)
    add_strips(g_trunk, secs, [(0, "north", 1, 0, 17, 1.5), (0, "east", -3, 0.5, 15, 1), (0, "south", -4, 0, 18, 1.5), (0, "west", 2, 1, 16, 1),
                               (1, "north", -3, 22, 42, 1.5), (1, "east", 2, 24, 44, 1)],
               lambda s, f, y2: (lambda W, H: bark("steel", W, H, f, moss_rows=3 if s == 0 else 0, ao=s == 0, extra=metal(y2))))
    for i, (y, yaw, tilt, L) in enumerate([(30, 222, -32, 5), (38, 78, -40, 4)]):
        frm, to = [-0.75, y - 0.75, 5.5], [0.75, y + 0.75, 5.5 + L]
        cube(f"stub_branch_{i + 1}", g_trunk, frm, to, rects_for(f"stub_{L}", frm, to, lambda f: (lambda W, H: paint_rings(W, H)) if f == "south" else (lambda W, H: bark("steel", W, H, f, ao=False)), hidden=("north",)),
             rotation=(tilt, yaw, 0), origin=[0.5, y, 0])

    # canopy: tall column cone of drooping needle tiers (pine_tree's skirt), cards only
    VARS = {"v1": (8, 16, -0.6), "v2": (8, 14, -0.3), "v3": (7, 12, 0.0), "v4": (6, 10, 0.25), "v5": (5, 7, 0.5)}
    for k, (w, L, shade) in VARS.items():
        card_variant(k, w, L, lambda W2, H2, shade=shade, seed=k: paint_card(W2, H2, shade, card_sprays(W2, H2, seed), cone=seed in ("v2", "v4")))
    card_variant("inner", 8, 14, lambda W2, H2: paint_card(W2, H2, -1.6, card_sprays(W2, H2, "in"), accents=False))
    NT = 14
    hs = [19 - 0.55 * i for i in range(NT)]
    Rs = [24.0 - 17.0 * (i / (NT - 1)) ** 1.4 for i in range(NT)]
    y_top = [44 + hs[0]]
    for i in range(1, NT): y_top.append(y_top[i - 1] - hs[i - 1] / 2 + hs[i])
    lean = lambda y: 1.5 * y / 176
    glimpse = {3: 200.0, 8: 30.0}
    for i in range(NT):
        k = ["v1", "v1", "v1", "v2", "v2", "v2", "v2", "v3", "v3", "v3", "v4", "v4", "v5", "v5"][i]
        cw, cL = VAR[k]
        R, h, yt = Rs[i], hs[i], y_top[i]; yb = yt - h
        c = [lean(yt), yt, lean(yt) * 0.6]
        g = group(f"tier_{i + 1}", c, g_can)
        n = [13, 13, 12, 12, 12, 11, 11, 10, 10, 9, 9, 8, 8, 7][i]
        gl = glimpse.get(i)
        for j in range(n):
            yaw = i * 23 + j * 360 / n + rng.uniform(-8, 8)
            if gl is not None and abs(((yaw - gl + 180) % 360) - 180) < 360 / n * 0.6: continue
            droop = rng.uniform(20, 30); twist = rng.choice([-1, 1]) * rng.uniform(5, 15)
            broken = rng.random() < 0.15
            rs = max(0.5, R - cL * math.cos(math.radians(droop)) + rng.uniform(-1, 0.5) + (2.0 if broken else 0))
            ys = yb + cL * math.sin(math.radians(droop)) + rng.uniform(-1, 1) - (1.5 if broken else 0)
            P0 = at(c, rs, yaw, ys)
            rot = radial_card(f"tier_{i + 1}_card_{j + 1}", g, k, P0, yaw, droop, twist)
            if j in (1, n // 2 + 1):
                cross_card(f"tier_{i + 1}_card_{j + 1}_cross", g, "v5", P0, rot, cL)
        for j in range(3):  # dark inner cards from the trunk, steeper
            yaw = i * 23 + (j + 0.5) * 120 + rng.uniform(-15, 15)
            radial_card(f"tier_{i + 1}_inner_card_{j + 1}", g, "inner", at(c, 1.0, yaw, yt - 0.5), yaw, rng.uniform(30, 36), rng.uniform(-10, 10))
        for j in range(2):  # top cards
            yaw = i * 23 + 60 + j * 180 + rng.uniform(-20, 20)
            radial_card(f"tier_{i + 1}_top_card_{j + 1}", g, "v4" if i < 10 else "v5", at(c, 0.8, yaw, yt + 0.3), yaw, rng.uniform(8, 16), rng.uniform(-10, 10))
    # leader: thin silver-banded spire with small crossed cards to a point
    top = y_top[-1]
    lx, lz = lean(top), lean(top) * 0.6
    frm, to = [lx - 0.75, top - 4, lz - 0.75], [lx + 0.75, top + 10, lz + 0.75]
    cube("leader", g_trunk, frm, to, rects_for("leader", frm, to, lambda f: (lambda W, H: bark("steel", W, H, f, base=4.5, ao=False, extra=metal(top + 10))), hidden=("down",), all_sides=True))
    for j in range(4):
        yaw = j * 90 + 20
        radial_card(f"leader_card_{j + 1}", g_can, "v5", at([lx, 0, lz], 0.3, yaw, top + 9), yaw, 62 + j * 3, rng.uniform(-8, 8))
    # ground
    for i, (x, z, yaw) in enumerate([(14, 8, 30), (-15, -5, 110), (5, -17, 200), (-8, 15, 290)]):
        detail(g_det, f"needle_litter_{i + 1}", [x - 2, 0, z - 1.5], [x + 2, 0.5, z + 1.5], lambda W, H, f: plain("leaf", W, H, f, 3.0), yaw=yaw, origin=[x, 0, z], key="litter")
    for i, (x, z) in enumerate([(19, -3), (-12, 14)]):
        detail(g_det, f"titanwood_cone_{i + 1}", [x - 1, 0, z - 1], [x + 1, 2.5, z + 1], lambda W, H, f: paint_scales("cone", W, H, f), key="tcone")
    detail(g_det, "stone_1", [-19, 0, 2], [-16, 2, 5], lambda W, H, f: plain("stone", W, H, f, 2.6), yaw=20, origin=[-17.5, 0, 3.5])
    write()


def build_runewood():
    """T8, swamp. Drooping, 112 to 160. Near black purple bark; murky green leaves with violet; glowing runes
    carved in the trunk (_glow); hanging vines."""
    global TEX
    TEX = 256
    reseed(8180)
    RAMPS["rune"] = R_("#0c0810 #140e1a #1c1424 #251b2e #2f2339 #3a2c45 #463652 #53405f")
    RAMPS["murk"] = R_("#0f150e #161f13 #1f2a18 #28351d #324023 #3d4b2a #495634 #566240")
    RAMPS["violet"] = R_("#2a1040 #4a1c6a #7030a0 #9a50c8 #c080e8")
    RAMPS["runeglow"] = R_("#2e0c4e #4e1880 #7a30b8 #a650e8 #cc80ff #e8c0ff")
    RAMPS["swampmoss"] = R_("#141c10 #1e2a14 #2a3a18 #38481e #465626")
    RAMPS["cap"] = R_("#2a1040 #3e1860 #582486 #7432a8 #9048c4 #ac68dc")
    RAMPS["stem"] = R_("#3a3440 #504858 #686070 #807888 #9890a0")
    RAMPS["stone"] = R_("#1c1c22 #2a2a32 #3a3a44 #4c4c56 #5e5e6a #727280")
    root, g_roots, g_trunk, g_br, g_can, g_det = standard_groups(68, 46)

    add_roots(g_roots, "rune", [5, 52, 104, 150, 205, 252, 310], [(2.0, 7, 4.5, 11), (1.5, 4, 0, 6), (1.0, 2, 0, 4.5)], (0, 3, 5), moss_rows=(8, 5, 3, 2))
    secs = [(13, 0, 14, 0, 0), (11.5, 14, 30, -0.5, 0.5), (10, 30, 46, -1, 1), (8.5, 46, 62, -1, 1.5), (7, 62, 76, -0.5, 1.5)]
    tp = lambda i, f, y2: (lambda W, H: bark("rune", W, H, f, moss_rows=8 if i == 0 else 0, knots=1 if i in (1, 2) else 0, ao=i == 0, moss_ramp="swampmoss"))
    add_trunk(g_trunk, secs, tp, share_from=3)
    add_strips(g_trunk, secs, [(0, "north", -4, 0, 12, 2), (0, "south", 2, 0, 13, 1.5), (0, "west", -2, 0, 11, 1.5), (1, "east", 1, 15, 28, 1.5), (2, "north", 1.5, 31, 44, 1.5)],
               lambda s, f, y2: (lambda W, H: bark("rune", W, H, f, moss_rows=4 if s == 0 else 0, ao=s == 0, moss_ramp="swampmoss")))
    # glowing runes carved into the trunk (signature)
    for k in range(4):
        card_variant(f"rune_{k + 1}", 3, 5, lambda W, H, k=k: glyph_card(W, H, "runeglow", 900 + k))
    for i, (s, side, a, y, k) in enumerate([(1, "north", -1.5, 24, 1), (1, "east", 1.5, 21, 2), (2, "south", 0.5, 40, 3), (3, "west", -1, 56, 4), (0, "south", -3.5, 9, 2)]):
        face_card(f"rune_{i + 1}_glow", g_trunk, f"rune_{k}", secs, s, side, a, y)

    # drooping canopy: wide dome plus hanging strands along the edges
    cl = []
    for k in range(6):
        yaw = math.radians(k * 60 + rng.uniform(-10, 10)); Rr = 22 + rng.uniform(-2, 2)
        cl.append((np.array([-0.5 + Rr * math.sin(yaw), 78 + rng.uniform(-3, 2), 1.5 + Rr * math.cos(yaw)]), 11 + rng.uniform(-1, 1)))
    for k in range(5):
        yaw = math.radians(k * 72 + 30 + rng.uniform(-10, 10)); Rr = 14 + rng.uniform(-2, 2)
        cl.append((np.array([-0.5 + Rr * math.sin(yaw), 92 + rng.uniform(-2, 2), 1.5 + Rr * math.cos(yaw)]), 11.5 + rng.uniform(-1, 1)))
    cl.append((np.array([1, 104, 3]), 11)); cl.append((np.array([-3, 102, -1]), 10))
    dome_c = np.array([-0.5, 86, 1.5])
    for j, ci in enumerate((0, 2, 4, 7, 9)):
        c = cl[ci][0]; yawr = math.atan2(c[0] + 0.5, c[2] - 1.5)
        s = np.array([-0.5 + 3 * math.sin(yawr), 50 + j * 4, 1.5 + 3 * math.cos(yawr)])
        mid = s + (c - s) * 0.55 + np.array([0, 1.5, 0])
        branch_chain(f"limb_{j + 1}", g_br, [s, mid, c - np.array([0, 2, 0])], [2.5, 2.0], "rune")
    card_variant("big_light", 10, 16, lambda W, H: clump_card(W, H, "murk", 1.0, 81, size=(3, 5), accents=dots("violet", 0.01, 1)))
    card_variant("big_mid", 10, 16, lambda W, H: clump_card(W, H, "murk", 0.4, 82, size=(3, 5)))
    card_variant("med_dark", 9, 13, lambda W, H: clump_card(W, H, "murk", -0.5, 83, size=(3, 5), accents=dots("violet", 0.012, 1)))
    card_variant("small_light", 6, 9, lambda W, H: clump_card(W, H, "murk", 1.3, 84, size=(3, 5)))
    card_variant("inner", 8, 12, lambda W, H: clump_card(W, H, "murk", -2.2, 85, vmax=1.5))
    card_variant("strand_long", 6, 12, lambda W, H: strand_card(W, H, "murk", 86, flower="violet"))
    card_variant("strand_short", 5, 8, lambda W, H: strand_card(W, H, "murk", 87, flower="violet", shade=0.3))

    def hang(g, ci, c, rho, out):
        oh = unit([out[0], 0, out[2]])
        if ci >= 11: return                      # none from the crown
        for j in range(2 if ci < 6 else 1):
            yaw = math.atan2(oh[0], oh[2]) + rng.uniform(-0.7, 0.7)
            d = np.array([math.sin(yaw), 0, math.cos(yaw)])
            k = "strand_long" if rng.random() < 0.65 else "strand_short"
            L = VAR[k][1]
            q = c + d * rho * rng.uniform(0.55, 0.8) - np.array([0, rho * rng.uniform(0.25, 0.5), 0])
            t = unit(np.array([0, -1, 0]) + d * 0.12)
            card(f"cluster_{ci + 1}_hanging_card_{j + 1}", g, k, q + t * L / 2, d, t)
    dome(g_can, cl, dome_c, 12.0, ("big_light", "big_mid", "med_dark"), "small_light", "inner", n_cards=8, n_cross=1, n_inner=2, hang=hang)
    # vines hanging from the limbs, under the canopy
    for i, (x, z, y) in enumerate([(9, 6, 64), (-8, -6, 66), (4, -11, 63), (-6, 10, 65)]):
        q = np.array([x, y, z]); d = unit([x, 0, z])
        card(f"vine_{i + 1}", g_br, "strand_long", q + np.array([0, -6, 0]), d, [0, -1, 0])
    # ground: violet mushrooms, stones, fallen leaves
    for i, (x, z, s) in enumerate([(12, -9, 1.0), (-14, 7, 0.8)]):
        detail(g_det, f"mushroom_{i + 1}_stem", [x - 0.5, 0, z - 0.5], [x + 0.5, 2.5, z + 0.5], lambda W, H, f: plain("stem", W, H, f, 2.2), hidden=("down", "up"), key="mstem")
        detail(g_det, f"mushroom_{i + 1}_cap", [x - 1.5, 2.5, z - 1.5], [x + 1.5, 3.5, z + 1.5], lambda W, H, f: plain("cap", W, H, f, 2.8, spots="violet"), hidden=(), key="mcap")
    for i, (x, z, yaw) in enumerate([(17, 5, 20), (-16, -8, 75), (-4, 17, 130)]):
        detail(g_det, f"fallen_leaf_{i + 1}", [x - 1.5, 0, z - 1], [x + 1.5, 0.5, z + 1], lambda W, H, f: plain("murk", W, H, f, 3.4), yaw=yaw, origin=[x, 0, z], key="fallen")
    for i, (x, z, s) in enumerate([(-17, -2, 2.5), (15, 12, 2)]):
        detail(g_det, f"stone_{i + 1}", [x - s / 2, 0, z - s / 2], [x + s / 2, h2(s * 0.8), z + s / 2], lambda W, H, f: plain("stone", W, H, f, 2.4), yaw=rng.uniform(0, 90), origin=[x, 0, z], key=f"stone{s}")
    write()


def build_gembark():
    """T9, plains. Layered crown, 128 to 176. Dark bark with gem crystals growing out; jewel green leaves with
    crystal sparkles; rotated gem crystal cubes on trunk and branches (_glow)."""
    global TEX
    TEX = 256
    reseed(9190)
    RAMPS["gemb"] = R_("#0e0b12 #16111c #1f1826 #292030 #34293c #403248 #4d3c55 #5b4763")
    RAMPS["jewel"] = R_("#06221a #0a3224 #0f442e #165838 #1e6e44 #288652 #36a064 #4cba7a")
    RAMPS["spark"] = R_("#8ae8c8 #c8fff0 #f0fffa")
    RAMPS["emer"] = R_("#0a4a3a #12735a #1ea07e #3cc8a2 #7ae8c8 #c8fff0")
    RAMPS["amet"] = R_("#3a1658 #5a2484 #8040b0 #a868d8 #d0a0f4 #f0dcff")
    RAMPS["stone"] = R_("#26242a #36343c #48464e #5c5a62 #727078 #8a888e")
    root, g_roots, g_trunk, g_br, g_can, g_det = standard_groups(70, 56)

    def flecks(f, w, h, face):
        return f
    add_roots(g_roots, "gemb", [8, 64, 118, 176, 232, 296], [(1.75, 6, 4.5, 10.5), (1.25, 3, 0, 5)], (0, 2, 4))
    secs = [(12, 0, 16, 0, 0), (10.5, 16, 40, 0.5, 0), (9, 40, 64, 0.5, 0.5), (7.5, 64, 88, 1, 0.5), (6, 88, 112, 1, 1), (5, 112, 136, 1, 1)]
    def gem_flecks(rgb_painter):
        def p(W, H):
            rgb, a = rgb_painter(W, H)
            for _ in range(max(1, W * H // 160)):  # tiny gem chips in the bark (about 1%)
                x, y = int(nrng.integers(0, W - 1)), int(nrng.integers(0, H - 1))
                ramp = RAMPS["emer" if nrng.random() < 0.6 else "amet"]
                rgb[y, x] = ramp[3]; rgb[y, x + 1] = ramp[2]
            return rgb, a
        return p
    tp = lambda i, f, y2: gem_flecks(lambda W, H: bark("gemb", W, H, f, moss_rows=6 if i == 0 else 0, knots=1 if i in (1, 2) else 0, ao=i == 0))
    add_trunk(g_trunk, secs, tp, share_from=4)
    add_strips(g_trunk, secs, [(0, "north", -3.5, 0, 13, 2), (0, "east", 1, 0, 12, 1.5), (1, "south", -2, 18, 36, 1.5), (2, "west", 0.5, 42, 60, 1.5), (3, "north", -1, 66, 84, 1.5)],
               lambda s, f, y2: (lambda W, H: bark("gemb", W, H, f, moss_rows=4 if s == 0 else 0, ao=s == 0)))
    # gem crystals growing out of the trunk (signature)
    for i, (s, side, a, y, ramp, size, L, tilt) in enumerate([(0, "south", 2, 11, "emer", 1.5, 4, 25), (1, "west", -2, 26, "amet", 1.5, 3.5, 35),
                                                              (2, "north", 1.5, 50, "emer", 1.5, 4, 30), (3, "east", -1, 74, "emer", 1.0, 3, 40)]):
        p, n = face_point(secs, s, side, a, y, out=-0.8)
        crystal(f"gem_crystal_{i + 1}", g_trunk, p, n + np.array([0, math.tan(math.radians(tilt)), 0]), size, L, ramp)

    # thick branches to five layered pads, a top pad on the leader
    pads = [((19, 78, 5), 20), ((-17, 92, -8), 20), ((4, 104, 19), 19), ((-6, 116, -17), 18), ((14, 128, -6), 17), ((1, 142, 1), 20)]
    for j, (c, R) in enumerate(pads[:-1]):
        c = np.array(c, float)
        yawr = math.atan2(c[0] - 1, c[2] - 1)
        y0 = c[1] - 16 if j < 4 else c[1] - 12
        s = np.array([1 + 2.5 * math.sin(yawr), y0, 1 + 2.5 * math.cos(yawr)])
        mid = s + (c - s) * 0.5 + np.array([0, 2, 0])
        end = branch_chain(f"limb_{j + 1}", g_br, [s, mid, c - np.array([0, 1.5, 0])], [3.0, 2.5], "gemb")
        bd = unit(mid - s); up = unit(np.array([0, 1, 0]) - bd * bd[1])
        mp = s + (mid - s) * 0.7 + up * 1.3                  # on top of the branch (3 thick), not through it
        crystal(f"gem_crystal_{5 + j}", g_br, mp, unit(up + bd * 0.3), 1.0, 2.5, "emer" if j % 2 == 0 else "amet")
    # crown limb up the leader
    branch(f"limb_6", g_br, [1, 132, 1], [1, 145, 1], 3.0, "gemb")
    card_variant("pad", 10, 12, lambda W, H: clump_card(W, H, "jewel", 0.8, 91, accents=sparkles("spark", 0.015)))
    card_variant("pad_rim", 9, 11, lambda W, H: clump_card(W, H, "jewel", 0.3, 92, accents=sparkles("spark", 0.012)))
    card_variant("pad_small", 6, 7, lambda W, H: clump_card(W, H, "jewel", 1.4, 93, accents=sparkles("spark", 0.02)))
    card_variant("pad_top", 9, 11, lambda W, H: clump_card(W, H, "jewel", 1.6, 94, accents=sparkles("spark", 0.02)))
    card_variant("inner", 9, 11, lambda W, H: clump_card(W, H, "jewel", -2.2, 95, vmax=1.5))
    for j, (c, R) in enumerate(pads):
        pad(f"pad_{j + 1}", g_can, c, R, "pad", "pad_top", "inner", "pad_small", n_cross=2, rim_key="pad_rim")
    # ground: fallen gem shards, stones, fallen leaves
    for i, (x, z, ramp) in enumerate([(13, -7, "emer"), (-11, 10, "amet"), (8, 14, "emer")]):
        crystal(f"gem_shard_{i + 1}", g_det, np.array([x, -0.3, z]), [rng.uniform(-0.4, 0.4), 1, rng.uniform(-0.4, 0.4)], 1.0, 2.0, ramp)
    for i, (x, z, yaw) in enumerate([(17, 4, 20), (-16, -7, 75), (-4, 18, 130)]):
        detail(g_det, f"fallen_leaf_{i + 1}", [x - 1.5, 0, z - 1], [x + 1.5, 0.5, z + 1], lambda W, H, f: plain("jewel", W, H, f, 3.6), yaw=yaw, origin=[x, 0, z], key="fallen")
    detail(g_det, "stone_1", [-17, 0, 1], [-14.5, 2, 3.5], lambda W, H, f: plain("stone", W, H, f, 2.6), yaw=25, origin=[-15.75, 0, 2.25])
    write()


def build_worldbark():
    """T10, forest. Layered crown, giant. J00BA asked for it twice as large (about 450 tall), with more glowing
    gold lines and more branches: built at the doc's size, then scaled 2x (1024 texture, 20x32 cards, approved). Ancient grey brown bark with huge grooves; deep emerald
    leaves with gold light; enormous roots, glowing sap cracks, tiny floating leaf particles as cubes."""
    global TEX, PPU
    TEX = 1024
    PPU = 4          # painted at 4 px per unit, then scaled 2x on write: 2 px per unit like every other model
    reseed(10200)
    RAMPS["world"] = R_("#14100e #1e1814 #29211b #352b23 #42362c #504236 #604f41 #715e4e")
    RAMPS["emerald"] = R_("#05201a #082c22 #0c3a2a #124a32 #1a5c3a #256e40 #3a8446 #5c9a4c #8aae58")
    RAMPS["sap"] = R_("#5a3a0c #8a5c14 #b8861e #e0ae34 #f8d064 #fff0b0")
    RAMPS["goldleaf"] = R_("#5a3c08 #7e5610 #a8781a #cc9a28 #e8bc40 #f8d868 #fff0a8")
    RAMPS["oldmoss"] = R_("#16261a #203622 #2c4828 #3a5c30 #4a7038")
    RAMPS["stone"] = R_("#2a2a2a #3c3b3a #504e4c #666360 #7e7a76 #96928c")
    RAMPS["cap"] = R_("#4a2a10 #6e4018 #965a22 #ba7a34 #d89c4c")
    RAMPS["stem"] = R_("#5a4c48 #7e6e62 #a4927c #c4b498 #ddd0b4")
    RAMPS["spot"] = R_("#c8bca0 #e8dcb8 #f4ecd4")
    root, g_roots, g_trunk, g_br, g_can, g_det = standard_groups(132, 110)

    def grooves(f, w, h, face):
        # huge grooves: deep dark channels every 8 to 12 px with a lit ridge beside each
        if face in ("up", "down"): return f
        x = int(nrng.integers(2, 6))
        while x < w - 2:
            f[:, x:x + 2] -= 1.6
            f[:, x + 2] += 0.8
            x += int(nrng.integers(8, 13))
        return f
    add_wild_roots(g_roots, "world", 8,
                   [[(4, 22, 28), (3.5, 18, 24)], [(3.5, 13, 18), (3, 11, 15)], [(2.5, 7, 16), (2.5, 8, 19)],
                    [(2, 4, 15), (2, 5, 12)], [(1.5, 2.5, 14), (1.5, 3, 11)], [(1, 2, 10), (1, 1.5, 12)]],
                   [(2, 5, 14), (1.5, 3, 11), (1, 2, 9)], (0, 1, 3, 4, 6), trunk_r=11.0, base=3.6, seed_yaw=8.0)
    secs = [(36, 0, 30, 0, 0), (32, 30, 70, 1, 0), (28, 70, 110, 1, 1), (25, 110, 150, 2, 1), (22, 150, 190, 2, 2), (20, 190, 230, 2, 2),
            (18, 230, 270, 3, 2), (16, 270, 310, 3, 3), (14, 310, 350, 3, 3), (12, 350, 390, 3, 4), (10, 390, 440, 3, 4)]
    def sec_at(y):
        for sec in secs:
            if sec[1] <= y < sec[2]: return sec
        return secs[-1]
    tp = lambda i, f, y2: (lambda W, H: bark("world", W, H, f, base=3.6, moss_rows=16 if i == 0 else 0, knots=2 if i < 3 else 0, ao=i == 0, extra=grooves, moss_ramp="oldmoss"))
    add_trunk(g_trunk, secs, tp, share_from=3)
    add_strips(g_trunk, secs, [(0, "north", -12, 0, 26, 3), (0, "east", 4, 0, 24, 3), (0, "south", 8, 0, 27, 2.5), (0, "west", -6, 0, 25, 3),
                               (1, "north", 6, 32, 64, 2.5), (2, "east", -6, 72, 104, 2.5)],
               lambda s, f, y2: (lambda W, H: bark("world", W, H, f, base=3.6, moss_rows=8 if s == 0 else 0, ao=s == 0, extra=grooves, moss_ramp="oldmoss")), d=1.5)
    # braided bark strands twisting up the trunk: one per face per section, all rising the same way round
    strand_n = 0
    for si in range(len(secs) - 2):
        w, y1, y2, cx, cz = secs[si]
        hw = w / 2
        for side, nrm in (("north", (0, 0, -1.0)), ("east", (1.0, 0, 0)), ("south", (0, 0, 1.0)), ("west", (-1.0, 0, 0))):
            nrm = np.array(nrm); e = np.cross(nrm, [0, 1.0, 0])
            base = np.array([cx, 0, cz]) + nrm * (hw + 0.75)
            p0 = base + e * -(hw - 2.5) + np.array([0, y1 + 2, 0])
            p1 = base + e * (hw - 2.5) + np.array([0, y2 - 2, 0])
            L = 4 * round(np.linalg.norm(p1 - p0) / 4)              # lengths in steps of 4 so strands share paint
            p1 = p0 + unit(p1 - p0) * L
            strand_n += 1
            branch(f"bark_strand_{strand_n}", g_trunk, p0, p1, 2.5, "world", base=4.0)

    # glowing gold sap cracks (signature): many, on every side of the lower five sections
    SAP = {"sap_1": (4, 16), "sap_2": (3, 12), "sap_3": (5, 20), "sap_4": (4, 14)}
    for k, (w, L) in SAP.items():
        card_variant(k, w, L, lambda W, H, k=k: crack_card(W, H, "sap", 700 + int(k[-1])))
    crack_n = 0
    for si in range(len(secs) - 1):
        w, y1, y2, cx, cz = secs[si]
        for side in ("north", "east", "south", "west"):
            for _ in range(2 if si < 3 else 1):
                if rng.random() < 0.2 and si > 0: continue
                k = rng.choice(list(SAP)); L = SAP[k][1]
                if y2 - y1 < L + 3: k = "sap_2"; L = SAP[k][1]
                y = rng.uniform(y1 + L / 2 + 1, y2 - L / 2 - 1)
                a_ = rng.uniform(-w / 2 + 3, w / 2 - 3)
                crack_n += 1
                face_card(f"sap_crack_{crack_n}_glow", g_trunk, k, secs, si, side, a_, y)

    vein_n = [0]
    def gold_vein(g, a, b, thick):
        """A glowing gold vein card along the top of a branch piece from a to b."""
        a, b = np.asarray(a, float), np.asarray(b, float)
        d = unit(b - a); up = unit(np.array([0, 1.0, 0]) - d * d[1])
        span = np.linalg.norm(b - a) * 0.8
        fits = [k for k in SAP if SAP[k][1] <= span]
        if not fits: return
        k = max(fits, key=lambda k: SAP[k][1])
        vein_n[0] += 1
        card(f"gold_vein_{vein_n[0]}_glow", g, k, (a + b) / 2 + up * (thick / 2 + 0.05), up, d)
    def glow_chain(name, pts, thicks):
        branch_chain(name, g_br, pts, thicks, "world", base=3.6)
        for j in range(len(pts) - 1):
            gold_vein(g_br, pts[j], pts[j + 1], thicks[j])

    # thick limbs to six layered pads
    pads = [((52, 140, 14), 48), ((-50, 170, -16), 48), ((12, 200, 50), 46), ((-18, 230, -46), 44), ((46, 262, -16), 42),
            ((-42, 294, 22), 40), ((16, 326, 40), 36), ((-22, 358, -34), 34), ((30, 390, 8), 30), ((-18, 414, 18), 26), ((3, 446, 4), 40)]
    for j, (c, R) in enumerate(pads[:-1]):
        c = np.array(c, float)
        yawr = math.atan2(c[0] - 2, c[2] - 2)
        y0 = c[1] - 30
        sw, _, _, scx, scz = sec_at(y0)
        rr = min(6.0, sw / 2 - 2)                       # start inside the trunk at that height
        s = np.array([scx + rr * math.sin(yawr), y0, scz + rr * math.cos(yawr)])
        m1 = s + (c - s) * 0.35 + np.array([0, 4, 0])
        m2 = s + (c - s) * 0.72 + np.array([0, 3, 0])
        glow_chain(f"limb_{j + 1}", [s, m1, m2, c - np.array([0, 2, 0])], [7.0, 5.0, 3.5])
    glow_chain("limb_crown", [[3, 430, 4], [3, 438, 4], [3, 445, 4]], [7.0, 5.0])
    nb = len(pads)
    for j, (c, R) in enumerate(pads[:4]):          # a second limb into each lower pad, from another height and angle
        c = np.array(c, float)
        yawr = math.atan2(c[0] - 2, c[2] - 2) + rng.choice([-1, 1]) * 0.5
        tgt = c + np.array([math.sin(yawr) * R * 0.35, -2, math.cos(yawr) * R * 0.35])
        s0 = np.array([2 + 5 * math.sin(yawr), c[1] - 46, 2 + 5 * math.cos(yawr)])
        mid = s0 + (tgt - s0) * 0.5 + np.array([0, 5, 0])
        nb += 1
        glow_chain(f"limb_{nb}", [s0, mid, tgt], [5.0, 3.5])
    low_pads = []
    for j, (yaw, y, L, rise) in enumerate([(25, 64, 38, 16), (140, 78, 34, 18), (215, 92, 36, 14), (300, 104, 32, 20)]):
        yr = math.radians(yaw)
        sec = secs[1] if y < 70 else secs[2]
        hw = sec[0] / 2 - 2
        s0 = np.array([sec[3] + hw * math.sin(yr), y, sec[4] + hw * math.cos(yr)])
        d = np.array([math.sin(yr), 0, math.cos(yr)])
        m = s0 + d * L * 0.55 + np.array([0, rise * 0.4, 0])
        e = s0 + d * L + np.array([0, rise, 0])
        nb += 1
        glow_chain(f"limb_{nb}", [s0, m, e], [5.0, 3.5])
        # a forked twig off the bough
        fd = unit(d + np.array([math.cos(yr) * 0.8, 0.9, -math.sin(yr) * 0.8]))
        branch(f"limb_{nb}_twig", g_br, m, m + fd * 12, 2.0, "world", base=3.6)
        if j == 0:
            low_pads.append((tuple(e + np.array([0, 2, 0])), 20))
    def gold_light(rgb, a, r):  # warm gold light on the upper leaf edges
        h, w = a.shape
        top = a & ~np.roll(a, 1, 0)
        sel = top & (nrng.random((h, w)) < 0.35)
        rgb[sel] = RAMPS["emerald"][-1]
    card_variant("pad", 13, 20, lambda W, H: detailed_leaf_card(W, H, "emerald", 0.6, 101, "blade", glint="goldleaf"))
    card_variant("pad_rim", 13, 18, lambda W, H: detailed_leaf_card(W, H, "emerald", 0.2, 102, "blade"))
    card_variant("pad_small", 8, 12, lambda W, H: detailed_leaf_card(W, H, "goldleaf", 0.8, 103, "fan"))
    card_variant("pad_top", 13, 20, lambda W, H: detailed_leaf_card(W, H, "emerald", 1.6, 104, "blade", glint="goldleaf"))
    card_variant("inner", 13, 20, lambda W, H: clump_card(W, H, "emerald", -2.2, 105, vmax=1.5, size=(4, 7)))
    card_variant("pad_gold", 13, 20, lambda W, H: detailed_leaf_card(W, H, "goldleaf", 0.6, 106, "fan"))
    card_variant("rim_gold", 13, 18, lambda W, H: detailed_leaf_card(W, H, "goldleaf", 0.3, 107, "fan"))
    card_variant("gold_curtain", 9, 26, lambda W, H: strand_card(W, H, "goldleaf", 108, shade=0.6))
    card_variant("falling_leaf", 3, 3, lambda W, H: detailed_leaf_card(W, H, "goldleaf", 1.4, 109, "fan"))
    for j, (c, R) in enumerate(pads + low_pads):
        pad(f"pad_{j + 1}", g_can, c, R, "pad", "pad_top", "inner", "pad_small", n_cross=3, rim_key="pad_rim",
            gold=("pad_gold", "rim_gold"), gold_frac=0.55, spacing=0.8, curtains=4 if R >= 30 else 2, curtain_key="gold_curtain")
    # gold veins running along the top of the roots, out from the trunk
    for (P, d, L, ht, hw) in WILD_PIECES:
        if hw < 1.5: continue
        fits = [k for k in SAP if SAP[k][1] <= L * 0.85 and SAP[k][0] <= hw * 2]
        if not fits: continue
        k = max(fits, key=lambda k: SAP[k][1])
        up = unit(np.array([0, 1.0, 0]) - d * d[1])
        cpos = P + d * L / 2 + up * (ht + 0.05)
        vein_n[0] += 1
        card(f"gold_vein_{vein_n[0]}_glow", g_roots, k, cpos, up, d)
    # glowing amber resin drops oozing from the bark
    for i in range(20):
        si = rng.randrange(0, len(secs) - 1); side = rng.choice(["north", "east", "south", "west"])
        w, y1, y2, cx, cz = secs[si]
        p, n = face_point(secs, si, side, rng.uniform(-w / 2 + 3, w / 2 - 3), rng.uniform(y1 + 4, y2 - 6), out=0.0)
        hx = 1.0 if side in ("north", "south") else 0.25
        hz = 0.25 if side in ("north", "south") else 1.0
        q = p + n * 0.25
        detail(g_trunk, f"amber_resin_{i + 1}_glow", [q[0] - hx, q[1] - 2, q[2] - hz], [q[0] + hx, q[1], q[2] + hz],
               lambda W, H, f: plain("sap", W, H, f, 3.6), hidden=(), key=f"resin_{side in ('north', 'south')}")
        detail(g_trunk, f"amber_resin_{i + 1}_drip_glow", [q[0] - hx / 2, q[1] - 3.5, q[2] - hz / 2], [q[0] + hx / 2, q[1] - 2, q[2] + hz / 2],
               lambda W, H, f: plain("sap", W, H, f, 4.2), hidden=(), key=f"drip_{side in ('north', 'south')}")
    # tiny floating leaf particles round the crown (glowing gold-green motes)
    for i in range(32):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(20, 66); y = rng.uniform(130, 460)
        x, z = 2 + r * math.sin(a), 2 + r * math.cos(a)
        detail(g_can, f"leaf_mote_{i + 1}_glow", [x - 0.5, y, z - 0.5], [x + 0.5, y + 0.5, z + 0.5],
               lambda W, H, f: plain("sap", W, H, f, 3.8), yaw=rng.uniform(0, 90), hidden=(), origin=[x, y, z], key="mote")
    # golden leaves falling from the crown
    for i in range(24):
        a = rng.uniform(0, 2 * math.pi); r = rng.uniform(26, 70); y = rng.uniform(40, 260)
        q = np.array([2 + r * math.sin(a), y, 2 + r * math.cos(a)])
        nrm = unit([rng.uniform(-1, 1), rng.uniform(0.3, 1), rng.uniform(-1, 1)])
        card(f"falling_leaf_{i + 1}_glow", g_can, "falling_leaf", q, nrm, rand_perp(nrm))
    # ground: big stones, mushrooms, fallen leaves
    for i, (x, z, s) in enumerate([(-46, 8, 5), (40, -30, 4), (24, 44, 3.5), (-30, -42, 4.5)]):
        detail(g_det, f"stone_{i + 1}", [x - s / 2, 0, z - s / 2], [x + s / 2, h2(s * 0.7), z + s / 2], lambda W, H, f: plain("stone", W, H, f, 2.6), yaw=rng.uniform(0, 90), origin=[x, 0, z], key=f"stone{s}")
    for i, (x, z) in enumerate([(-24, 22), (30, 16)]):
        detail(g_det, f"mushroom_{i + 1}_stem", [x - 0.75, 0, z - 0.75], [x + 0.75, 3.5, z + 0.75], lambda W, H, f: plain("stem", W, H, f, 2.2), hidden=("down", "up"), key="mstem")
        detail(g_det, f"mushroom_{i + 1}_cap", [x - 2, 3.5, z - 2], [x + 2, 5, z + 2], lambda W, H, f: plain("cap", W, H, f, 2.6, spots="spot"), hidden=(), key="mcap")
    for i, (x, z, yaw) in enumerate([(50, 12, 20), (-10, 52, 130), (18, -50, 200)]):
        detail(g_det, f"fallen_leaf_{i + 1}", [x - 2, 0, z - 1.5], [x + 2, 0.5, z + 1.5], lambda W, H, f: plain("emerald", W, H, f, 4.2), yaw=yaw, origin=[x, 0, z], key="fallen")
    write(scale=2)


{"hickory": build_hickory, "titanwood": build_titanwood, "runewood": build_runewood,
 "gembark": build_gembark, "worldbark": build_worldbark}[KIND]()
