"""Shared helpers for building Hytale style foliage .bbmodel files (blockbench_detailed_prompts.md section 3.4)."""
import base64, copy, io, json, math, os, random, uuid
import numpy as np
from PIL import Image

PPU = 2


def hexc(h):
    h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def ramp(s): return [hexc(c) for c in s.split()]


def ramp_colour(r, v):
    """Value -> colour in half steps (half steps blend neighbours, so the ramp has small steps)."""
    n = len(r)
    q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
    lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
    a = np.array(r)[lo]; b = np.array(r)[hi]
    return (a * (1 - f) + b * f).round().astype(np.uint8)


def px(u):
    v = u * PPU
    assert abs(v - round(v)) < 1e-6, f"non integer pixel size {u}"
    return int(round(v))


def h2(v): return round(v * 2) / 2


def Rx(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])
def Ry(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])
def Rz(a): a = math.radians(a); c, s = math.cos(a), math.sin(a); return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def bb_euler(M):
    """Decompose M into Blockbench's element rotation (matrix = Rz * Ry * Rx)."""
    b = math.asin(max(-1, min(1, -M[2, 0])))
    a = math.atan2(M[2, 1], M[2, 2]); c = math.atan2(M[1, 0], M[0, 0])
    return [math.degrees(a), math.degrees(b), math.degrees(c)]


def card_matrix(yaw, tilt, roll=0.0):
    """Card stands in the x-y plane, base at its origin, growing up +y. Twist (roll) about its length, tilt outward
    (towards +z) by `tilt` degrees from vertical, then turn round the base by `yaw`."""
    return Ry(yaw) @ Rx(tilt) @ Ry(roll)


def direction_to_yaw_tilt(d):
    d = np.asarray(d, float); d = d / np.linalg.norm(d)
    tilt = math.degrees(math.acos(max(-1, min(1, d[1]))))
    yaw = math.degrees(math.atan2(d[0], d[2]))
    return yaw, tilt


FACES = ("north", "east", "south", "west", "up", "down")


def face_dims(frm, to, face):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]


class Model:
    def __init__(self, name, tex, seed):
        self.name, self.TEX = name, tex
        self.rng = random.Random(seed)
        self.nrng = np.random.default_rng(seed)
        self.rects, self.elements, self.groups, self.order = {}, [], {}, []
        self.group(name, [0, 0, 0])

    def uid(self): return str(uuid.UUID(int=self.rng.getrandbits(128), version=4))

    # ---- texture rectangles
    def rect(self, key, w, h, paint):
        if key not in self.rects:
            self.rects[key] = {"w": w, "h": h, "paint": paint}
        return key

    def pack(self):
        T = self.TEX; x = y = shelf = 0
        for k, r in sorted(self.rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"], kv[0])):
            if x + r["w"] > T: x, y, shelf = 0, y + shelf, 0
            r["x"], r["y"] = x, y; x += r["w"]; shelf = max(shelf, r["h"])
        if y + shelf > T: raise SystemExit(f"{self.name}: atlas overflow {y + shelf}px > {T}")
        img = np.zeros((T, T, 4), np.uint8)
        for k in sorted(self.rects):
            r = self.rects[k]
            rgb, a = r["paint"](r["w"], r["h"])
            assert rgb.shape[:2] == (r["h"], r["w"]), (k, rgb.shape, r["w"], r["h"])
            img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], :3] = rgb
            img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], 3] = np.where(a, 255, 0)
        self.img, self.used = img, y + shelf
        for e in self.elements:
            for f, fd in e["faces"].items():
                s = fd.pop("_spec", None)
                if s is None: continue
                r = self.rects[s["key"]]; x1, y1 = r["x"], r["y"]
                if s["sub"]:
                    ox, oy, sw, sh = s["sub"]; x1, y1 = x1 + ox, y1 + oy; x2, y2 = x1 + sw, y1 + sh
                else:
                    x2, y2 = x1 + r["w"], y1 + r["h"]
                fd["uv"] = [x2, y1, x1, y2] if s["mirror"] else [x1, y1, x2, y2]
                if s["rot"]: fd["rotation"] = s["rot"]
        return img

    # ---- outliner
    def group(self, name, origin, parent=None):
        assert name not in self.groups, f"duplicate group {name}"
        self.groups[name] = {"name": name, "uuid": self.uid(), "origin": [round(v, 3) for v in origin], "children": []}
        if parent is not None:
            self.groups[parent]["children"].append(("g", name))
        return name

    def cube(self, name, grp, frm, to, faces, rotation=(0, 0, 0), origin=None):
        """faces: face -> None (hidden) or F(...) spec."""
        assert all(n.islower() or n.isdigit() or n == "_" for n in name), name
        origin = origin if origin is not None else [(frm[i] + to[i]) / 2 for i in range(3)]
        fj = {}
        for f in FACES:
            spec = faces.get(f)
            fj[f] = {"uv": [0, 0, 0, 0], "texture": None} if spec is None else {"_spec": spec, "texture": 0}
        e = {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
             "allow_mirror_modeling": True, "from": [round(v, 4) for v in frm], "to": [round(v, 4) for v in to],
             "autouv": 0, "color": 0, "origin": [round(v, 4) for v in origin], "faces": fj, "type": "cube",
             "uuid": self.uid()}
        if any(abs(r) > 1e-6 for r in rotation): e["rotation"] = [round(v, 3) for v in rotation]
        self.elements.append(e); self.groups[grp]["children"].append(("e", e["uuid"]))
        return e

    def card(self, name, grp, base, key, w, L, yaw, tilt, roll=0.0, sink=0.0):
        """Flat alpha card (0 units thick): one painted leaf / blade / petal / twig. Tip at the top row of the rect."""
        bx, by, bz = base
        M = card_matrix(yaw, tilt, roll)
        frm = [bx - w / 2, by - sink, bz]; to = [bx + w / 2, by - sink + L, bz]
        self.cube(name, grp, frm, to, {"north": F(key)}, rotation=bb_euler(M), origin=[bx, by, bz])
        return np.array(base, float) + M @ np.array([0, L - sink, 0])  # tip position

    # ---- json
    def bbmodel(self):
        def group_json(g):
            return {"name": g["name"], "uuid": g["uuid"], "export": True, "locked": False, "scope": 0, "selected": False,
                    "visibility": g.get("visible", True), "_static": {"properties": {}, "temp_data": {}}, "origin": g["origin"],
                    "rotation": [0, 0, 0], "color": 0, "children": [], "reset": False, "shade": True, "mirror_uv": False,
                    "autouv": 0, "isOpen": g["name"] == self.name, "primary_selected": False}

        def outliner(name):
            g = self.groups[name]
            return {"uuid": g["uuid"], "isOpen": name == self.name,
                    "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}
        buf = io.BytesIO(); Image.fromarray(self.img, "RGBA").save(buf, "PNG")
        src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()
        T = self.TEX
        return {
            "meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
            "name": self.name, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
            "multi_file_ruleset": "", "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
            "resolution": {"width": T, "height": T},
            "elements": self.elements, "groups": [group_json(g) for g in self.groups.values()], "outliner": [outliner(self.name)],
            "textures": [{"name": f"{self.name}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                          "width": T, "height": T, "uv_width": T, "uv_height": T, "particle": False,
                          "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "file_format": "png",
                          "render_mode": "default", "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color",
                          "fps": 7, "force_translucent": False, "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
                          "frame_interpolate": False, "visible": True, "internal": True, "saved": True, "uuid": self.uid(), "source": src}],
            "animations": [],
        }

    def save(self, out_dir):
        os.makedirs(out_dir, exist_ok=True)
        Image.fromarray(self.img, "RGBA").save(os.path.join(out_dir, f"{self.name}.png"))
        with open(os.path.join(out_dir, f"{self.name}.bbmodel"), "w") as fh:
            json.dump(self.bbmodel(), fh, separators=(",", ":"))


def F(key, mirror=False, sub=None, rot=0): return {"key": key, "mirror": mirror, "sub": sub, "rot": rot}


def showcase(models_offsets, name, out_dir, tex=256, seed=1):
    """One file holding every model side by side: their textures are stitched into one atlas."""
    atlas = np.zeros((tex, tex, 4), np.uint8)
    x = y = shelf = 0; placed = {}
    for m, _ in sorted(models_offsets, key=lambda mo: -mo[0].TEX):
        if x + m.TEX > tex: x, y, shelf = 0, y + shelf, 0
        placed[m.name] = (x, y); atlas[y:y + m.TEX, x:x + m.TEX] = m.img; x += m.TEX; shelf = max(shelf, m.TEX)
    assert y + shelf <= tex, "showcase atlas overflow"
    S = Model(name, tex, seed); S.img = atlas
    for m, (ox, oz) in models_offsets:
        ux, uy = placed[m.name]
        g_map = {}

        def copy_group(gname, parent):
            g = m.groups[gname]
            nm = g["name"] if g["name"] not in S.groups else f"{m.name}_{g['name']}"
            new = S.group(nm, [g["origin"][0] + ox, g["origin"][1], g["origin"][2] + oz], parent)
            for kind, ref in g["children"]:
                if kind == "g":
                    copy_group(ref, new)
                else:
                    e = copy.deepcopy(next(el for el in m.elements if el["uuid"] == ref))
                    e["uuid"] = S.uid()
                    e["from"][0] += ox; e["to"][0] += ox; e["origin"][0] += ox
                    e["from"][2] += oz; e["to"][2] += oz; e["origin"][2] += oz
                    for fd in e["faces"].values():
                        if fd["texture"] is not None:
                            u1, v1, u2, v2 = fd["uv"]; fd["uv"] = [u1 + ux, v1 + uy, u2 + ux, v2 + uy]
                    S.elements.append(e); S.groups[new]["children"].append(("e", e["uuid"]))
        copy_group(m.name, name)
    # hidden imp scale dummy (18.5 units) so sizes can be checked against the player
    S.group("showcase_scale_dummy", [0, 0, 0], name); S.groups["showcase_scale_dummy"]["visible"] = False
    e = S.cube("scale_dummy_imp", "showcase_scale_dummy", [-2, 0, -10], [2, 18.5, -6], {})
    e["export"] = False; e["visibility"] = False
    S.save(out_dir)
    return S
