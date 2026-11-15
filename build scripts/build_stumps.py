"""Tree stumps: what is left after a tree is chopped down.

One stump per tree type, built from that tree's own .bbmodel (same roots, same trunk_1 footprint, same
low bark strips) and painted with that tree's own bark painter and ramps (exec'd from its build script),
so the stump swaps in for the tree in place.

Doc: blockbench_detailed_prompts.md section 3.1 (roots / trunk / details groups, bark recipe,
"end grain (the top of cut faces) shows rings"), 2 px/unit, one embedded texture.

Usage: py -3 build_stumps.py [pine|birch|oak|maple|frostbark ...]   (no args = all)
"""
import json, math, os, sys, copy

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = r"C:\Users\lucas\blockbench_models\trees"
TREES = r"C:\Users\lucas\blockbench_models\trees"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
S1 = r"C:\Users\lucas\AppData\Local\Temp\claude\C--WINDOWS-System32\cfb66cb2-4830-4225-a54a-a5d7ef69b6d9\scratchpad"
S2 = r"C:\Users\lucas\AppData\Local\Temp\claude\C--WINDOWS-System32\fdc2906e-0a3a-4405-a0ff-ac1ae8fe713c\scratchpad"
MODEL = "# ---------------------------------------------------------------- model"

CFG = {
    # cut: height of the main cut face; lip: depth (z) of the raised back lip, as a fraction of the trunk depth
    "pine":      dict(src=(S1, "build_pine_tree_v2.py", MODEL), cut=8, lip=0.40, seed=7101,
                      wood="#4a2e1a #6a4628 #8c6038 #ac7c4c #c89a62 #dcb47a"),
    "birch":     dict(src=(S1, "build_birch_tree.py", MODEL + " scaffolding"), cut=6, lip=0.45, seed=7202,
                      wood="#6a5844 #8e7858 #b09a74 #cab490 #e0cca8 #eedcbc"),
    "oak":       dict(src=(S1, "build_oak_tree.py", MODEL + " scaffolding"), cut=9, lip=0.38, seed=7303,
                      wood="#3e2416 #5a3622 #7a4e30 #9a6840 #b88452 #d0a068"),
    "maple":     dict(src=(S1, "build_maple_tree.py", MODEL + " scaffolding"), cut=8, lip=0.40, seed=7404,
                      wood="#5a2e1c #7c4428 #a05e36 #be7a48 #d8985c #e8b474"),
    "frostbark": dict(src=(S2, "build_frostbark_tree.py", MODEL), cut=8, lip=0.42, seed=7505,
                      wood="#5a5650 #7a746c #9a9288 #b8b0a4 #d2cabe #e4ded4"),
}


def build(kind):
    cfg = CFG[kind]
    d_tree = json.load(open(os.path.join(TREES, f"{kind}_tree.bbmodel"), encoding="utf8"))
    TE = {e["name"]: e for e in d_tree["elements"]}

    # ---- the tree's own helpers and painters
    sdir, sname, marker = cfg["src"]
    path = os.path.join(sdir, sname)
    src = open(path, encoding="utf8").read()
    ns = {"__file__": path, "__name__": "tree_helpers"}
    argv = sys.argv; sys.argv = [path, os.path.join(HERE, "_unused")]
    try:
        exec(src[:src.index(marker)], ns)
    finally:
        sys.argv = argv
    import random, uuid
    import numpy as np
    rng = random.Random(cfg["seed"]); ns["rng"] = rng
    nrng = np.random.default_rng(cfg["seed"]); ns["nrng"] = nrng
    hexc, RAMPS, ramp_colour, FACE_LIGHT = ns["hexc"], ns["RAMPS"], ns["ramp_colour"], ns["FACE_LIGHT"]
    noise, px, face_dims = ns["noise"], ns["px"], ns["face_dims"]
    RAMPS["wood"] = [hexc(c) for c in cfg["wood"].split()]
    if "moss" not in RAMPS:
        RAMPS["moss"] = [hexc(c) for c in "#1e3014 #2e481a #42621f #5c7e28 #7a9a34".split()]

    if kind in ("oak", "maple"):
        def bark(w, h, face, moss=0, knots=0, base_ao=True):
            return ns["paint_oak_bark"](w, h, face, moss_rows=moss, knots=knots, base_ao=base_ao)
        bark_ramp, bark_dark = "darkbark", 1.0
    elif kind == "birch":
        def bark(w, h, face, moss=0, knots=0, base_ao=True):
            return ns["paint_birch_bark"](w, h, face, moss_rows=moss, base=base_ao and face != "up")
        bark_ramp, bark_dark = "darkbark", 1.5
    elif kind == "frostbark":
        def bark(w, h, face, moss=0, knots=0, base_ao=True):
            return ns["paint_bark"](w, h, face, moss_rows=moss, knots=knots, base_ao=base_ao, ice=1)
        bark_ramp, bark_dark = "bark", 1.5
    else:
        def bark(w, h, face, moss=0, knots=0, base_ao=True):
            return ns["paint_bark"](w, h, face, moss_rows=moss, knots=knots, base_ao=base_ao)
        bark_ramp, bark_dark = "bark", 1.5

    NAME = f"{kind}_stump"
    TEX = 128
    atlas = ns["Atlas"]()
    elements, groups = [], {}

    def new_uuid(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

    def group(name, origin, parent=None):
        groups[name] = {"name": name, "uuid": new_uuid(), "origin": [round(v, 3) for v in origin], "children": []}
        if parent: groups[parent]["children"].append(("g", name))
        return name

    def cube(name, grp, frm, to, faces, rotation=(0, 0, 0), origin=None):
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

    def F(key, mirror=False): return {"key": key, "mirror": mirror}

    def faces_of(name, frm, to, painter, hidden=("down",)):
        """painter(w, h, face) -> (rgb, alpha); one atlas rect per visible face."""
        out = {}
        for f in ("north", "east", "south", "west", "up", "down"):
            if f in hidden: out[f] = None; continue
            w, h = (px(v) for v in face_dims(frm, to, f))
            out[f] = F(atlas.add(f"{name}:{f}", w, h, lambda W, H, f=f: painter(W, H, f)))
        return out

    root = group(NAME, [0, 0, 0])
    g_roots = group("roots", [0, 0, 0], root)
    g_trunk = group("trunk", [0, 0, 0], root)
    g_details = group("details", [0, 0, 0], root)

    # ---- trunk footprint = the tree's trunk_1
    t1 = TE["trunk_1"]
    X0, _, Z0 = t1["from"]; X1, _, Z1 = t1["to"]
    W, D = X1 - X0, Z1 - Z0
    CUT = cfg["cut"]
    LIP_Z = Z0 + round(D * cfg["lip"] * 2) / 2
    LIP_H = 1.5
    CX, CZ = (X0 + X1) / 2 + 0.25 * W / 10, (Z0 + Z1) / 2 + 0.5 * D / 10  # heart sits a little off centre
    cracks = [rng.uniform(0, 360) for _ in range(2)]
    axe = [(rng.uniform(-0.3, 0.3) + 0.6, rng.uniform(-W / 4, W / 4)) for _ in range(3)]  # (slope, offset)
    snow_seed = rng.uniform(0, 6.28)

    def wood_value(x, z):
        """End grain at world (x, z): rings round the heart, 2 radial checks, faint axe marks."""
        dx, dz = x - CX, z - CZ
        r = 0.55 * max(abs(dx), abs(dz)) * 1.12 + 0.45 * math.hypot(dx, dz)
        a = math.atan2(dz, dx)
        r += 0.22 * math.sin(3 * a + cfg["seed"] % 7)
        v = 2.7 + 0.85 * math.cos(2 * math.pi * r / 1.15) - 0.06 * r
        if r < 0.7: v = 1.6
        R = min(W, D) / 2
        for c in cracks:
            da = abs(((math.degrees(a) - c + 180) % 360) - 180)
            if 1.0 < r < R - 1.2 and math.radians(da) * r < 0.3: v = 0.6
        for s, o in axe:
            dist = abs((z - CZ) - s * (x - CX) - o) / math.hypot(1, s)
            if dist < 0.25: v -= 0.5
        e = min(x - X0, X1 - x, z - Z0, Z1 - z)
        if e < 1.5: v += 0.5  # paler sapwood band
        return v, e

    def endgrain(frm, to):
        def p(w, h, face):
            f = np.zeros((h, w)); edge = np.zeros((h, w))
            for j in range(h):
                for i in range(w):
                    f[j, i], edge[j, i] = wood_value(frm[0] + (i + .5) / 2, frm[2] + (j + .5) / 2)
            f += noise(w, h, 0.25)
            rgb = ramp_colour("wood", f)
            br = edge < 0.5
            rgb[br] = ramp_colour(bark_ramp, np.full((h, w), bark_dark) + noise(w, h, 0.4))[br]
            if kind == "frostbark":  # snow drifted onto the back of the cut, against the lip
                snow = np.zeros((h, w), bool)
                for j in range(h):
                    for i in range(w):
                        x, z = frm[0] + (i + .5) / 2, frm[2] + (j + .5) / 2
                        reach = LIP_Z + 1.5 + 1.2 * math.sin(x * 0.9 + snow_seed) + 0.6 * math.sin(x * 2.3)
                        snow[j, i] = z < reach or (frm[1] > CUT and z < LIP_Z - 0.5 + math.sin(x * 1.7) * 0.8)
                sv = np.full((h, w), 3.0) + noise(w, h, 0.5) + np.linspace(0.6, -0.6, h)[:, None]
                rgb[snow] = ramp_colour("snow", sv)[snow]
            return rgb, np.ones((h, w), bool)
        return p

    def torn(w, h, face, bark_face=False):
        """Raw split wood: vertical fibres, lighter at the top, dark seams."""
        if bark_face: return bark(w, h, face, base_ao=False)
        light = FACE_LIGHT[face] * 0.6
        f = np.full((h, w), 3.0 + light) + noise(w, h, 0.4)
        for x in range(w):
            f[:, x] += nrng.choice([-0.8, -0.2, 0, 0.3, 0.6])
        f += np.linspace(0.7, -0.5, h)[:, None]
        for x in range(int(nrng.integers(0, 2)), w, int(nrng.integers(3, 5))):
            f[:, x] -= 1.2
        return ramp_colour("wood", f), np.ones((h, w), bool)

    # ---- roots: copied from the tree, repainted (moss on every other root)
    roots = sorted([e for e in d_tree["elements"] if e["name"].startswith("root_")], key=lambda e: e["name"])
    idx = {}
    for e in roots:
        n = int(e["name"].split("_")[1]); idx.setdefault(n, []).append(e)
    for n, parts in sorted(idx.items()):
        moss = n % 2 == 1
        for e in parts:
            outer = e["name"].endswith("outer")
            mr = (4 if outer else 6) if moss else 0
            fc = faces_of(e["name"], e["from"], e["to"], lambda w, h, f, mr=mr: bark(w, h, f, moss=mr))
            cube(e["name"], g_roots, e["from"], e["to"], fc, rotation=e.get("rotation", (0, 0, 0)), origin=e.get("origin"))

    # ---- trunk: the cut body, a raised back lip of unbroken wood, splinters along the lip
    body_f, body_t = [X0, 0, Z0], [X1, CUT, Z1]
    fc = faces_of("stump_body", body_f, body_t, lambda w, h, f: bark(w, h, f, moss=5, knots=1), hidden=("down", "up"))
    fc["up"] = F(atlas.add("stump_body:up", px(W), px(D), lambda w, h: endgrain(body_f, body_t)(w, h, "up")))
    cube("stump_body", g_trunk, body_f, body_t, fc)

    lip_f, lip_t = [X0, CUT, Z0], [X1, CUT + LIP_H, LIP_Z]
    def lip_paint(w, h, f):
        if f == "south": return torn(w, h, f)
        return bark(w, h, f, base_ao=False)
    fc = faces_of("hinge_lip", lip_f, lip_t, lip_paint, hidden=("down", "up"))
    fc["up"] = F(atlas.add("hinge_lip:up", px(W), px(LIP_Z - Z0), lambda w, h: endgrain(lip_f, lip_t)(w, h, "up")))
    cube("hinge_lip", g_trunk, lip_f, lip_t, fc)

    # splinters: torn fibres sticking up where the tree broke off, ragged heights, slight lean toward the fall
    n_spl = max(3, min(6, int(W // 2.2)))
    slots = sorted(rng.sample(range(int((X1 - X0 - 1) * 2)), n_spl))
    for i, sl in enumerate(slots):
        x = X0 + sl / 2
        sw = rng.choice([1.0, 1.5, 1.5, 2.0]) if W >= 7 else 1.0
        x = min(x, X1 - sw)
        sd = rng.choice([1.0, 1.5])
        z0 = round((Z0 + rng.uniform(0, max(0, LIP_Z - Z0 - sd))) * 2) / 2
        hgt = rng.choice([1.0, 1.5, 2, 2.5, 3, 4]) * (0.7 if W < 7 else 1)
        hgt = max(1.0, round(hgt * 2) / 2)
        tip = rng.choice([1.0, 1.5, 2.0, 2.5]) * (0.7 if W < 7 else 1)
        tip = max(1.0, round(tip * 2) / 2)
        lean_x, lean_z = rng.uniform(6, 22), rng.uniform(-12, 12)
        piv = [x + sw / 2, CUT + LIP_H, z0 + sd / 2]
        on_edge = abs(z0 - Z0) < 1e-6
        frm = [x, CUT + 1, z0]; to = [x + sw, CUT + LIP_H + hgt, z0 + sd]
        fc = faces_of(f"splinter_{i + 1}", frm, to, lambda w, h, f, oe=on_edge: torn(w, h, f, bark_face=(oe and f == "north")))
        cube(f"splinter_{i + 1}", g_trunk, frm, to, fc, rotation=(lean_x, 0, lean_z), origin=piv)
        # thinner tip on top, set to one side, starting inside the base piece
        tx = x + rng.choice([0, sw - 0.5]) if sw > 0.5 else x
        tfrm = [tx, to[1] - 0.5, z0 + (sd - 0.5 if rng.random() < 0.5 else 0)]
        tto = [tx + 0.5, to[1] + tip, tfrm[2] + 0.5]
        fc = faces_of(f"splinter_{i + 1}_tip", tfrm, tto, lambda w, h, f: torn(w, h, f))
        cube(f"splinter_{i + 1}_tip", g_trunk, tfrm, tto, fc, rotation=(lean_x, 0, lean_z), origin=piv)

    # bark strips from the tree that start at the ground, cut to below the stump top
    for e in sorted([e for e in d_tree["elements"] if e["name"].startswith("bark_strip_") and e["from"][1] < 2],
                    key=lambda e: e["name"]):
        frm = list(e["from"]); to = list(e["to"])
        to[1] = min(to[1], CUT - rng.choice([0.5, 1, 1.5]))
        if to[1] - frm[1] < 2: continue
        fc = faces_of(e["name"], frm, to, lambda w, h, f: bark(w, h, f, moss=3), hidden=("down",))
        cube(e["name"], g_trunk, frm, to, fc)

    # ---- details
    def chip_paint(w, h, f):
        if f == "up" and rng.random() < 0.15: return bark(w, h, f, base_ao=False)
        return torn(w, h, f)
    R_out = max(W, D) / 2 + 4
    for i in range(6):  # wood chips flung out by the axe
        a = math.radians(rng.uniform(0, 360)); r = R_out + rng.uniform(0, 5)
        x, z = round(CX + r * math.cos(a), 1), round(CZ + r * math.sin(a), 1)
        cw, cd = rng.choice([(1, 2), (1.5, 2.5), (1, 1.5), (2, 1)])
        frm = [x - cw / 2, 0, z - cd / 2]; to = [x + cw / 2, 0.5, z + cd / 2]
        cube(f"wood_chip_{i + 1}", g_details, frm, to, faces_of(f"wood_chip_{i + 1}", frm, to, chip_paint),
             rotation=(0, rng.uniform(0, 180), 0), origin=[x, 0, z])

    def plain(ramp, base, detail=None):
        return lambda w, h, f: ns["paint_plain"](ramp, w, h, f, base, detail)

    if kind == "pine":
        for i, (x, z, yaw) in enumerate([(X1 + 4, Z0 + 1, 32), (X0 - 2, Z1 + 3, 118)]):
            frm, to = [x - 1, 0, z - 1.5], [x + 1, 2, z + 1.5]
            cube(f"pine_cone_{i + 1}", g_details, frm, to,
                 faces_of(f"pine_cone_{i + 1}", frm, to, lambda w, h, f: ns["paint_scales"]("cone", w, h, f)),
                 rotation=(0, yaw, 0), origin=[x, 0, z])
        for i, (x, z, yaw) in enumerate([(X1 + 6, Z1, 15), (X0 - 5, Z0 - 1, 70), (X0 + 2, Z1 + 6, 140)]):
            frm, to = [x - 1, 0, z - 1], [x + 1, 0.5, z + 1]
            cube(f"needle_litter_{i + 1}", g_details, frm, to,
                 faces_of(f"needle_litter_{i + 1}", frm, to, plain("dry", 2.0, "needles")), rotation=(0, yaw, 0), origin=[x, 0, z])
    if kind in ("pine", "oak"):  # a small red mushroom in the moss at the foot
        mx, mz = X1 + 1.5, Z1 + 1.5
        for nm, frm, to, p, hid in [
                ("mushroom_stem", [mx - 0.5, 0, mz - 0.5], [mx + 0.5, 2.5, mz + 0.5], plain("stem", 2.2), ("down", "up")),
                ("mushroom_cap", [mx - 1.5, 2.5, mz - 1.5], [mx + 1.5, 3.5, mz + 1.5],
                 lambda w, h, f: ns["paint_plain"]("cap", w, h, f, 2.6, "gills" if f == "down" else "spots"), ()),
                ("mushroom_cap_top", [mx - 1, 3.5, mz - 1], [mx + 1, 4, mz + 1], plain("cap", 2.8, "spots"), ("down",))]:
            cube(nm, g_details, frm, to, faces_of(nm, frm, to, p, hidden=hid))
    if kind == "oak":
        for i, (x, z) in enumerate([(X0 - 3, Z1 + 2), (X1 + 5, Z0 - 2)]):
            frm, to = [x - 0.5, 0, z - 0.5], [x + 0.5, 1.5, z + 0.5]
            cube(f"acorn_{i + 1}", g_details, frm, to, faces_of(f"acorn_{i + 1}", frm, to, plain("acorn", 2.6)), rotation=(0, 30 + 40 * i, 0))
            frm, to = [x - 1, 1.5, z - 1], [x + 1, 2, z + 1]
            cube(f"acorn_{i + 1}_cap", g_details, frm, to, faces_of(f"acorn_{i + 1}_cap", frm, to, plain("acorn", 1.4)), rotation=(0, 30 + 40 * i, 0))
        # moss cushion creeping over one corner of the cut
        frm, to = [X0, CUT, Z1 - 3], [X0 + 3.5, CUT + 0.5, Z1]
        cube("moss_cap", g_details, frm, to, faces_of("moss_cap", frm, to, lambda w, h, f: (ramp_colour("moss", np.full((h, w), 2.6 + FACE_LIGHT[f] * 0.6) + noise(w, h, 0.8)), np.ones((h, w), bool))))
    if kind == "birch":  # bracket fungus on the side, like the tree
        for i, (y, z) in enumerate([(3, Z0 + 1), (4.5, Z0 + 2.5)]):
            frm, to = [X1, y, z], [X1 + 1.5, y + 0.5, z + 2]
            cube(f"bracket_fungus_{i + 1}", g_details, frm, to, faces_of(f"bracket_fungus_{i + 1}", frm, to, plain("fungus", 2.4), hidden=()))
            frm, to = [X1, y + 0.5, z + 0.5], [X1 + 1, y + 1, z + 1.5]
            cube(f"bracket_fungus_{i + 1}_top", g_details, frm, to, faces_of(f"bracket_fungus_{i + 1}_top", frm, to, plain("fungus", 2.9)))
    if kind == "maple":  # fallen five point leaves around the stump (flat alpha leaves on 1 px cubes)
        def leaf(w, h, f, shade):
            yy, xx = np.mgrid[0:h, 0:w]; c = (w - 1) / 2
            a = np.arctan2(yy - c, xx - c); r = np.hypot(yy - c, xx - c)
            m = r < (c - 0.2) * (0.62 + 0.38 * np.abs(np.cos(2.5 * (a + 0.3))))
            m |= (np.abs(xx - c) < 0.6) & (yy > c)  # stalk
            ramp = "fallen_orange" if shade else "fallen"
            fv = 2.6 - r / c + noise(w, h, 0.4)
            return ramp_colour(ramp, fv), m
        for i in range(5):
            a = math.radians(rng.uniform(0, 360)); r = R_out + rng.uniform(-1, 6)
            x, z = round(CX + r * math.cos(a), 1), round(CZ + r * math.sin(a), 1)
            frm, to = [x - 1.5, 0, z - 1.5], [x + 1.5, 0.5, z + 1.5]
            fc = faces_of(f"fallen_leaf_{i + 1}", frm, to, lambda w, h, f, s=i % 2: leaf(w, h, f, s),
                          hidden=("down", "north", "south", "east", "west"))
            cube(f"fallen_leaf_{i + 1}", g_details, frm, to, fc, rotation=(0, rng.uniform(0, 360), 0), origin=[x, 0, z])
    if kind == "frostbark":
        # ice crystals in the bark (the tree's signature), and a snow cap on the lip
        for i, (frm, to, rot) in enumerate([([X1 - 0.5, 2, Z0 + 2], [X1 + 1, 4.5, Z0 + 3], (0, 0, -18)),
                                            ([X0 + 3, 3, Z1 - 0.5], [X0 + 4, 5, Z1 + 1], (20, 0, 0))]):
            cube(f"ice_crystal_bark_{i + 1}", g_details, frm, to,
                 faces_of(f"ice_crystal_bark_{i + 1}", frm, to, plain("ice", 3.4)), rotation=rot)
        frm, to = [X0, CUT + LIP_H, Z0], [X1, CUT + LIP_H + 0.5, LIP_Z - 0.5]
        cube("snow_cap", g_details, frm, to, faces_of("snow_cap", frm, to, plain("snow", 3.0)))

    # ---- pack, write, pad
    ns["TEX"] = TEX
    img, used_h = atlas.pack()
    for e in elements:
        for f, fd in e["faces"].items():
            s = fd.pop("_spec", None)
            if s: fd["uv"] = atlas.uv(s["key"], s["mirror"])

    import base64, io
    from PIL import Image
    buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
    srcb64 = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    def group_json(g):
        return {"name": g["name"], "uuid": g["uuid"], "export": True, "locked": False, "scope": 0, "selected": False,
                "visibility": True, "origin": g["origin"], "rotation": [0, 0, 0], "color": 0, "children": [],
                "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": True, "primary_selected": False}

    def outliner(name):
        g = groups[name]
        return {"uuid": g["uuid"], "isOpen": True,
                "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}

    model = {
        "meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
        "name": NAME, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
        "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": TEX, "height": TEX},
        "elements": elements, "groups": [group_json(g) for g in groups.values()], "outliner": [outliner(NAME)],
        "textures": [{"name": f"{NAME}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                      "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False,
                      "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                      "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                      "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                      "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": new_uuid(),
                      "source": srcb64}],
        "animations": [],
    }
    out = os.path.join(OUT, f"{NAME}.bbmodel")
    with open(out, "w", encoding="utf8") as fh:
        json.dump(model, fh, indent="\t")
    sys.path.insert(0, REPO_SCRIPTS)
    import fix_texture_bleed
    r = fix_texture_bleed.pad_file(out, [os.path.join(OUT, f"{NAME}.png")])
    ys = [e["to"][1] for e in elements]
    print(f"{NAME:16s} cubes={len(elements)} atlas_rows={used_h}/{TEX} -> {r['size'][1]} footprint={W}x{D} cut={CUT} top={max(ys):.1f}")


if __name__ == "__main__":
    for k in (sys.argv[1:] or list(CFG)):
        build(k)
