"""Shared builder for the Blockbench creatures written from data tables.

Used by build_chicken_bbmodel.py, build_highland_cow_bbmodel.py and
build_snake_bbmodel.py. It does what the cow and ogre scripts do inline,
plus three things those creatures didn't need:

- Element rotation (a box turned on its own origin), for the snake.
- Hidden-face removal and painted contact shadow tested in rest-pose world
  space, so they work across rotated boxes and bones.
- Edge highlights found from the surface itself (the texel sits on a convex
  edge of the solid), not from the box outline, so boxes that continue into
  each other show no seam.

Units: everything is designed in texture pixels ("px", 1 px = 0.5 Blockbench
units at D-053). y = 0 is the ground, the creature faces north (-z), its
right side is +x. Faces are lit from the top, slightly front-left
(MODELS-BLOCKBENCH 4.3).
"""

import base64
import io
import json
import math
import sys
import uuid
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "tools"))
from build_pickaxe_bbmodel import FACES, NORMAL, face_frame, pack, texels  # noqa: E402,F401

PX = 0.5   # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


def ramp(*cs):
    return [hexrgb(c) for c in cs]


def clamp(v, lo=0, hi=4):
    return max(lo, min(hi, v))


def fi(v):
    return math.floor(v)


# ---------------------------------------------------------------- geometry

def el(name, bone, part, lo, hi, rot=None, origin=None):
    """A box from lo to hi (px). rot/origin turn the box on its own origin."""
    e = {"name": name, "bone": bone, "part": part, "lo": list(lo), "hi": list(hi)}
    if rot is not None:
        e["rot"], e["origin"] = tuple(rot), tuple(origin)
    return e


def mirror(name, bone, part, lo, hi, rot=None, origin=None):
    """A right-side box and its mirror on the left. A mirrored rotation keeps
    x and flips y and z."""
    right = el(name.replace("*", "right"), bone.replace("*", "right"), part, lo, hi, rot, origin)
    left = el(name.replace("*", "left"), bone.replace("*", "left"), part,
              (-hi[0], lo[1], lo[2]), (-lo[0], hi[1], hi[2]),
              None if rot is None else (rot[0], -rot[1], -rot[2]),
              None if origin is None else (-origin[0], origin[1], origin[2]))
    return [right, left]


def rot_matrix(rx, ry, rz):
    """Blockbench/three.js Euler order ZYX: R = Rz . Ry . Rx."""
    a, b, c = (math.radians(v) for v in (rx, ry, rz))
    Rx = np.array([[1, 0, 0], [0, math.cos(a), -math.sin(a)], [0, math.sin(a), math.cos(a)]])
    Ry = np.array([[math.cos(b), 0, math.sin(b)], [0, 1, 0], [-math.sin(b), 0, math.cos(b)]])
    Rz = np.array([[math.cos(c), -math.sin(c), 0], [math.sin(c), math.cos(c), 0], [0, 0, 1]])
    return Rz @ Ry @ Rx


def turn_about(r, piv):
    M = np.eye(4)
    R = rot_matrix(*r)
    M[:3, :3] = R
    M[:3, 3] = np.array(piv, float) - R @ np.array(piv, float)
    return M


# ---------------------------------------------------------------- animation

def kf(channel, t, x, y, z, interp="catmullrom"):
    return {"channel": channel, "data_points": [{"x": x, "y": y, "z": z}],
            "uuid": str(uuid.uuid4()), "time": t, "color": -1, "interpolation": interp}


def track(channel, keys, interp="catmullrom"):
    return [kf(channel, t, *v, interp=interp) for t, v in keys]


def rot(*keys):
    return track("rotation", keys)


def sway(length, amp, phase, axis, cycles=1, bias=(0, 0, 0)):
    """A looping sine sway in keys every 1/8 cycle, phase in cycles (for lag)."""
    n = 8 * cycles
    out = []
    for k in range(n + 1):
        v = list(bias)
        v[axis] = round(bias[axis] + amp * math.sin(2 * math.pi * (k / 8 - phase)), 2)
        out.append((round(length * k / n, 4), tuple(v)))
    return track("rotation", out)


# ---------------------------------------------------------------- the model

class Texel:
    """Everything a painter needs to know about one texel."""
    __slots__ = ("e", "f", "p", "q", "n", "i", "j", "w", "h", "light", "edge", "contact")

    @property
    def shade(self):
        return self.light + (1 if self.edge else 0) - (1 if self.contact else 0)


class Creature:
    def __init__(self, name, elements, bones, painters, animations, light_bias=None):
        self.name = name
        self.elements = elements
        self.bones = bones            # name -> (parent, pivot px, rest rotation deg)
        self.painters = painters      # part -> painter(Texel) -> RGBA
        self.animations = animations
        self.light_bias = light_bias or {}
        names = [e["name"] for e in elements]
        assert len(set(names)) == len(names), "element names must be unique"
        for e in elements:
            for k in range(3):
                size = e["hi"][k] - e["lo"][k]
                assert size > 0 and abs(size - round(size)) < 1e-9, \
                    f"{e['name']}: sizes must be whole texture pixels"
        self.bone_m = {b: self._bone_matrix(b) for b in bones}
        for e in elements:
            M = self.bone_m[e["bone"]]
            if "rot" in e:
                M = M @ turn_about(e["rot"], e["origin"])
            e["M"] = M
            e["Minv"] = np.linalg.inv(M)
        self.LO = np.array([e["lo"] for e in elements], float)
        self.HI = np.array([e["hi"] for e in elements], float)
        self.MINV = np.array([e["Minv"] for e in elements])
        self.index = {id(e): k for k, e in enumerate(elements)}

    def _bone_matrix(self, b):
        M = np.eye(4)
        while b:
            parent, piv, r = self.bones[b]
            if any(r):
                M = turn_about(r, piv) @ M
            b = parent
        return M

    # --- rest-pose space
    def world(self, e, p):
        return (e["M"] @ np.array([p[0], p[1], p[2], 1.0]))[:3]

    def world_dir(self, e, d):
        return e["M"][:3, :3] @ np.array(d, float)

    def inside_any(self, q, skip=None, eps=1e-6):
        """True if the world point q is inside an element (other than skip)."""
        ql = np.einsum("nij,j->ni", self.MINV, np.array([q[0], q[1], q[2], 1.0]))[:, :3]
        ins = np.all((ql > self.LO + eps) & (ql < self.HI - eps), axis=1)
        if skip is not None:
            ins[self.index[id(skip)]] = False
        return bool(ins.any())

    def covered(self, e, f, p):
        n = NORMAL[f]
        return self.inside_any(self.world(e, [p[k] + 0.25 * n[k] for k in range(3)]), skip=e)

    def contact(self, e, f, p):
        """Painted shadow: the texel sits right next to another part."""
        n = NORMAL[f]
        q = [p[k] + 0.5 * n[k] for k in range(3)]
        for t in tangents(f):
            for s in (-1, 1):
                if self.inside_any(self.world(e, [q[k] + s * t[k] for k in range(3)]), skip=e):
                    return True
        return False

    def edge(self, e, f, p, nw):
        """Edge highlight: the solid falls away one pixel over, on a top face
        in any direction, on a side face only upward."""
        n = NORMAL[f]
        for t in tangents(f):
            for s in (-1, 1):
                d = [s * t[k] for k in range(3)]
                dw = self.world_dir(e, d)
                if nw[1] < 0.7 and dw[1] < 0.7:
                    continue
                q = [p[k] + d[k] - 0.25 * n[k] for k in range(3)]
                if not self.inside_any(self.world(e, q)):
                    return True
        return False

    def light(self, nw):
        """Top 3, front and left 2, back and right 1, bottom 0 (FACE_SHADE of
        the cow and ogre), interpolated for turned faces."""
        return clamp(math.floor(1.5 + 1.5 * nw[1] - 0.5 * nw[2] - 0.5 * nw[0] + 0.5))

    # --- texture
    def visible_faces(self):
        vis = {}
        for ei, e in enumerate(self.elements):
            for f in FACES:
                if all(self.covered(e, f, p) for _, _, p in texels(e, f)):
                    continue
                _, _, _, w, h = face_frame(e, f)
                vis[(ei, f)] = (int(w), int(h))
        return vis

    def paint(self, sizes=(64, 128, 256, 512)):
        self.visible = self.visible_faces()
        rects = [(k, w, h) for k, (w, h) in self.visible.items()]
        for tex in sizes:
            try:
                self.places = pack(rects, tex)
                break
            except SystemExit:
                continue
        self.tex = tex
        img = Image.new("RGBA", (tex, tex), (0, 0, 0, 0))
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            w, h = self.visible[(ei, f)]
            nw = self.world_dir(e, NORMAL[f])
            for i, j, p in texels(e, f):
                t = Texel()
                t.e, t.f, t.p, t.i, t.j, t.w, t.h = e, f, p, i, j, w, h
                t.q = self.world(e, p)
                t.n = nw
                t.light = self.light(nw) + self.light_bias.get(e["part"], 0)
                t.edge = self.edge(e, f, p, nw)
                t.contact = self.contact(e, f, p)
                img.putpixel((ox + i, oy + j), self.painters[e["part"]](t))
        self.img = img
        return img

    # --- previews
    def render(self, yaw, pitch, scale, size, silhouette=False, anchor=0.85):
        """Orthographic painter's render of every visible texel (rest pose)."""
        cy, sy = math.cos(math.radians(yaw)), math.sin(math.radians(yaw))
        cp, sp = math.cos(math.radians(pitch)), math.sin(math.radians(pitch))

        def proj(q):
            x, y, z = q
            x1, z1 = x * cy - z * sy, x * sy + z * cy
            return x1, y * cp - z1 * sp, y * sp + z1 * cp

        quads = []
        for (ei, f), (ox, oy) in self.places.items():
            e = self.elements[ei]
            o, u, v, w, h = face_frame(e, f)
            for j in range(int(h)):
                for i in range(int(w)):
                    corners = []
                    for di, dj in ((0, 0), (1, 0), (1, 1), (0, 1)):
                        q = [o[k] + (i + di) * u[k] + (j + dj) * v[k] for k in range(3)]
                        corners.append(proj(self.world(e, q)))
                    depth = sum(c[2] for c in corners) / 4
                    col = (20, 20, 24, 255) if silhouette else self.img.getpixel((ox + i, oy + j))
                    quads.append((depth, corners, col))
        out = Image.new("RGBA", size, (0, 0, 0, 0))
        d = ImageDraw.Draw(out)
        cx, cyy = size[0] / 2, size[1] * anchor
        for depth, corners, col in sorted(quads, key=lambda q: q[0]):
            d.polygon([(cx + c[0] * scale, cyy - c[1] * scale) for c in corners], fill=col)
        return out

    def previews(self, out_dir, scale, tile=(420, 360), anchor=0.85):
        # Front-left, front-right, back-left, left side, front (faces -z).
        views = [(-145, 22), (145, 22), (-35, 22), (-90, 0), (180, 0)]
        tiles = [self.render(yw, pt, scale, tile, anchor=anchor) for yw, pt in views]
        sheet = Image.new("RGBA", (tile[0] * len(tiles), tile[1]), (176, 196, 222, 255))
        for k, t in enumerate(tiles):
            sheet.alpha_composite(t, (tile[0] * k, 0))
        sheet.save(Path(out_dir) / f"{self.name}_preview.png")
        sil = Image.new("RGBA", (tile[0] * 2, tile[1]), (235, 235, 235, 255))
        sil.alpha_composite(self.render(-145, 22, scale, tile, True, anchor), (0, 0))
        sil.alpha_composite(self.render(-90, 0, scale, tile, True, anchor), (tile[0], 0))
        sil.save(Path(out_dir) / f"{self.name}_silhouette.png")

    # --- .bbmodel
    def write_bbmodel(self, out_dir, imp_height_px=37):
        out_dir = Path(out_dir)
        tex_png = out_dir / f"{self.name}.png"
        self.img.save(tex_png)

        def uid():
            return str(uuid.uuid4())

        def u(v):
            return round(v * PX, 4)

        bone_uuid = {b: uid() for b in self.bones}
        children = {b: [] for b in self.bones}
        elements = []
        for ei, e in enumerate(self.elements):
            faces = {}
            for f in FACES:
                if (ei, f) in self.places:
                    ox, oy = self.places[(ei, f)]
                    w, h = self.visible[(ei, f)]
                    faces[f] = {"uv": [ox, oy, ox + w, oy + h], "texture": 0}
                else:
                    faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
            x = {
                # A box named like its bone gets "_box", so Godot's nodes stay unique.
                "name": e["name"] + ("_box" if e["name"] in self.bones else ""),
                "box_uv": False, "rescale": False, "locked": False,
                "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
                "from": [u(v) for v in e["lo"]], "to": [u(v) for v in e["hi"]],
                "autouv": 0, "color": 0,
                "origin": [u(v) for v in (e["origin"] if "rot" in e else self.bones[e["bone"]][1])],
                "faces": faces, "type": "cube", "uuid": uid(),
            }
            if "rot" in e:
                x["rotation"] = [round(v, 3) for v in e["rot"]]
            elements.append(x)
            children[e["bone"]].append(x["uuid"])

        # Scale dummy: hidden and never exported, the Imp's height measured in
        # Godot (1.16 m, the pig/wolf/cow/ogre PRs), rounded to whole pixels.
        dummy = {
            "name": "scale_dummy_imp", "box_uv": False, "rescale": False,
            "locked": True, "light_emission": 0, "render_order": "default",
            "allow_mirror_modeling": True, "export": False, "visibility": False,
            "from": [-2, 0, -2], "to": [2, u(imp_height_px), 2], "autouv": 0, "color": 1,
            "origin": [0, 0, 0],
            "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
            "type": "cube", "uuid": uid(),
        }
        elements.append(dummy)

        def group(name):
            _, piv, r = self.bones[name]
            kids = [group(b) for b, (parent, _, _) in self.bones.items() if parent == name]
            return {"name": name, "origin": [u(v) for v in piv], "rotation": list(r),
                    "color": 0, "uuid": bone_uuid[name], "export": True, "mirror_uv": False,
                    "isOpen": True, "locked": False, "visibility": True, "autouv": 0,
                    "children": children[name] + kids}

        root = [b for b, (parent, _, _) in self.bones.items() if parent is None][0]
        outliner = [
            group(root),
            {"name": "scale_dummy", "origin": [0, 0, 0], "rotation": [0, 0, 0], "color": 0,
             "uuid": uid(), "export": False, "mirror_uv": False, "isOpen": False,
             "locked": False, "visibility": False, "autouv": 0, "children": [dummy["uuid"]]},
        ]

        animations = []
        for name, a in self.animations.items():
            animators = {}
            for bone, keys in a["bones"].items():
                keys = json.loads(json.dumps(keys))
                for k in keys:
                    if k["channel"] == "position":   # authored in px, stored in units
                        k["data_points"] = [{ax: round(val * PX, 4)
                                             for ax, val in k["data_points"][0].items()}]
                animators[bone_uuid[bone]] = {"name": bone, "type": "bone", "keyframes": keys}
            animations.append({
                "uuid": uid(), "name": name, "loop": a["loop"], "override": False,
                "length": a["length"], "snapping": 24, "selected": False,
                "anim_time_update": "", "blend_weight": "", "start_delay": "", "loop_delay": "",
                "animators": animators,
            })

        buf = io.BytesIO()
        self.img.save(buf, "PNG")
        tex = self.tex
        texture = {
            "path": str(tex_png.resolve()), "name": tex_png.name, "folder": "",
            "namespace": "", "id": "0", "group": "", "width": tex, "height": tex,
            "uv_width": tex, "uv_height": tex, "particle": False,
            "use_as_default": False, "layers_enabled": False, "sync_to_project": "",
            "render_mode": "default", "render_sides": "auto", "pbr_channel": "color",
            "frame_time": 1, "frame_order_type": "loop", "frame_order": "",
            "frame_interpolate": False, "visible": True, "internal": True,
            "saved": True, "uuid": uid(),
            "relative_path": tex_png.name,
            "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode(),
        }
        model = {
            "meta": {"format_version": "4.10", "model_format": "free", "box_uv": False},
            "name": self.name, "model_identifier": "", "visible_box": [1, 1, 0],
            "variable_placeholders": "", "variable_placeholder_buttons": [],
            "timeline_setups": [], "unhandled_root_fields": {},
            "resolution": {"width": tex, "height": tex},
            "elements": elements, "outliner": outliner, "textures": [texture],
            "animations": animations,
        }
        (out_dir / f"{self.name}.bbmodel").write_text(json.dumps(model, indent="\t"))

    def build(self, out_dir, preview_scale, tile=(420, 360), anchor=0.85, sizes=(64, 128, 256, 512)):
        out_dir = Path(out_dir)
        out_dir.mkdir(parents=True, exist_ok=True)
        self.paint(sizes)
        self.previews(out_dir, preview_scale, tile, anchor)
        self.write_bbmodel(out_dir)
        used = sum(w * h for w, h in self.visible.values())
        top = max(self.world(e, c)[1] for e in self.elements for c in corners(e))
        print(f"boxes: {len(self.elements)}  bones: {len(self.bones)}  "
              f"visible faces: {len(self.visible)}  texture: {self.tex}x{self.tex}  "
              f"texels used: {used}/{self.tex ** 2}  height: {top:.1f} px = {top / 32:.3f} m  "
              f"animations: {', '.join(self.animations)}")


def tangents(f):
    n = NORMAL[f]
    return [t for t in ((1, 0, 0), (0, 1, 0), (0, 0, 1)) if not any(t[k] and n[k] for k in range(3))]


def corners(e):
    lo, hi = e["lo"], e["hi"]
    return [(x, y, z) for x in (lo[0], hi[0]) for y in (lo[1], hi[1]) for z in (lo[2], hi[2])]
