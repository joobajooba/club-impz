"""Shared kit for building Blockbench models from Python, to docs/blockbench_detailed_prompts.md.

A model is a list of cubes in named groups. Every visible face gets its own area in one texture
at the model's texel density (2 px per unit for world assets and armour, 4 for held weapons), and
is painted by its material: a hue-shifted ramp, face lighting (top light, sides mid, bottoms dark),
2x2 noise clusters, edge light and contact shadow, then the material's own detail (grain, planks,
bricks, slate rows, scratches, stitching, folds, facets, glow). Patterns that should line up across
cubes (bricks, planks, slate) are painted from world coordinates.

Faces pressed flat against another cube, or sunk inside one, and faces on the ground are hidden
(no UV, no texture), as section 1.5 rule 10 asks.

    m = Model("iron_sword", ppu=4)
    g = m.group("blade", origin=(0, 6, 0))
    m.cube("blade_box", (-1, 6, -0.25), (1, 20, 0.25), METAL, g)
    m.save(model_dir, texture_dir)
"""
import base64
import colorsys
import io
import json
import math
import os
import uuid as _uuid
import zlib

import numpy as np
from PIL import Image

FACES = ("north", "east", "south", "west", "up", "down")
# Light from the top, slightly front left (section 1.5 rule 4).
FACE_SHIFT = {"up": 1, "north": 0, "west": 0, "east": -1, "south": -1, "down": -2}


# ---------------------------------------------------------------- colour

def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))


def clamp_rgb(c):
    """No pure black or white (rule 1.5.3)."""
    return tuple(int(min(246, max(10, v))) for v in c)


def ramp(*hexes):
    return [clamp_rgb(hexrgb(h)) for h in hexes]


def shift_hue(c, dh, ds=0.0, dv=0.0):
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in c))
    r, g, b = colorsys.hsv_to_rgb((h + dh) % 1, min(1, max(0, s + ds)), min(1, max(0, v + dv)))
    return clamp_rgb((r * 255, g * 255, b * 255))


def stretch(r, n=7):
    """Resample a ramp to n shades, then hue shift: shadows cooler, lights warmer (rule 1.5.2)."""
    out = []
    for i in range(n):
        t = i * (len(r) - 1) / (n - 1)
        a, b = int(math.floor(t)), min(len(r) - 1, int(math.floor(t)) + 1)
        f = t - a
        c = tuple(r[a][k] * (1 - f) + r[b][k] * f for k in range(3))
        k = i / (n - 1)
        # Cool the bottom of the ramp towards blue/purple and warm the top towards yellow.
        c = (c[0] + (k - 0.5) * 10, c[1] + (k - 0.5) * 4, c[2] - (k - 0.5) * 12)
        out.append(clamp_rgb(c))
    return out


def from_base(hexcol, n=7, spread=0.55):
    """A ramp built round one colour: darker and cooler down, lighter and warmer up."""
    base = hexrgb(hexcol)
    h, s, v = colorsys.rgb_to_hsv(*(x / 255 for x in base))
    out = []
    for i in range(n):
        k = (i - (n - 1) / 2) / ((n - 1) / 2)          # -1 .. 1
        vv = min(0.97, max(0.06, v * (1 + k * spread)))
        ss = min(1, max(0, s * (1 - 0.25 * k)))
        hh = (h + (-0.035 * k if h > 0.08 else 0.01 * k)) % 1
        r, g, b = colorsys.hsv_to_rgb(hh, ss, vv)
        out.append(clamp_rgb((r * 255, g * 255, b * 255)))
    return out


# ---------------------------------------------------------------- materials

class Mat:
    """A material: a ramp (dark to light), a base index into it and a painter kind.

    kinds: metal, wood, plank, leather, cloth, stone, brick, slate, glass, gem, glow, fur, skin,
    wrap, rope, plain. Extra keyword options are read by the painters (see paint_face)."""

    def __init__(self, name, ramp_, kind="plain", base=None, **opts):
        self.name, self.ramp, self.kind = name, list(ramp_), kind
        self.base = base if base is not None else len(self.ramp) // 2
        self.opts = opts

    def variant(self, name, **opts):
        o = dict(self.opts)
        o.update(opts)
        base = o.pop("base", self.base)
        kind = o.pop("kind", self.kind)
        r = o.pop("ramp", self.ramp)
        return Mat(name, r, kind, base, **o)


# ---------------------------------------------------------------- model

def _u():
    return str(_uuid.uuid4())


class Group:
    def __init__(self, name, origin, rotation, parent):
        self.name, self.origin, self.rotation, self.parent = name, list(origin), list(rotation), parent
        self.uuid = _u()
        self.children = []        # Group or Cube, in order


class Cube:
    def __init__(self, name, frm, to, mat, group, rotation, origin, hide, decal, share, inflate, light):
        self.name = name
        self.frm = [min(a, b) for a, b in zip(frm, to)]
        self.to = [max(a, b) for a, b in zip(frm, to)]
        self.mat, self.group = mat, group
        self.rotation = list(rotation) if rotation else [0, 0, 0]
        self.origin = list(origin) if origin else list(group.origin if group else (0, 0, 0))
        self.hide, self.decal, self.share, self.inflate, self.light = set(hide or ()), decal, share, inflate, light
        self.uuid = _u()
        self.visible_export = True

    @property
    def rotated(self):
        return any(abs(r) > 1e-6 for r in self.rotation)


class Model:
    def __init__(self, name, ppu=2, ground=True, seed=None, max_texture=512, cull=True):
        self.name, self.ppu, self.ground, self.max_texture, self.cull = name, ppu, ground, max_texture, cull
        self.root = Group(name, (0, 0, 0), (0, 0, 0), None)
        self.cubes = []
        self.anims = []
        self.seed = zlib.crc32(name.encode()) if seed is None else seed
        self.dummy = None

    # -- building
    def group(self, name, origin=(0, 0, 0), parent=None, rotation=(0, 0, 0)):
        p = parent or self.root
        g = Group(name, origin, rotation, p)
        p.children.append(g)
        return g

    def cube(self, name, frm, to, mat, group=None, rotation=None, origin=None, hide=(), decal=None,
             share=None, inflate=0, light=None):
        g = group or self.root
        c = Cube(name, frm, to, mat, g, rotation, origin, hide, decal, share, inflate, light)
        g.children.append(c)
        self.cubes.append(c)
        return c

    def box(self, name, center, size, mat, group=None, **kw):
        """A cube from its centre and size."""
        frm = [center[i] - size[i] / 2 for i in range(3)]
        to = [center[i] + size[i] / 2 for i in range(3)]
        return self.cube(name, frm, to, mat, group, **kw)

    def mirror_x(self, cubes, rename=("_right", "_left"), group=None):
        """Copies cubes mirrored across x = 0 (names swap _right/_left)."""
        out = []
        for c in cubes:
            n = c.name.replace(rename[0], "\0").replace(rename[1], rename[0]).replace("\0", rename[1])
            if n == c.name:
                n = c.name + "_m"
            rot = [c.rotation[0], -c.rotation[1], -c.rotation[2]]
            org = [-c.origin[0], c.origin[1], c.origin[2]]
            out.append(self.cube(n, (-c.to[0], c.frm[1], c.frm[2]), (-c.frm[0], c.to[1], c.to[2]), c.mat,
                                 group or c.group, rotation=rot, origin=org, hide=_mirror_hide(c.hide),
                                 decal=c.decal, share=c.share, inflate=c.inflate, light=c.light))
        return out

    def scale_dummy(self, at=(0, 0, 0)):
        g = self.group("scale_dummy", (0, 0, 0))
        c = self.cube("scale_dummy_imp", (at[0] - 2, at[1], at[2] - 2), (at[0] + 2, at[1] + 18.5, at[2] + 2), None, g)
        c.visible_export = False
        self.dummy = g
        return c

    def anim(self, name, length, tracks, loop="loop"):
        """tracks: {bone_name: {"rotation"|"position"|"scale": [(time, (x, y, z)), ...]}}.
        Keys are catmullrom unless the tuple has a 3rd item 'linear' or 'step'."""
        self.anims.append((name, length, tracks, loop))

    # -- culling
    def _hidden_faces(self, c):
        hide = set(c.hide)
        if c.mat is None:
            return set(FACES)
        if self.ground and c.frm[1] <= 0.001 and not c.rotated:
            hide.add("down")
        if not self.cull or c.rotated or c.inflate:
            return hide
        for f in FACES:
            if f in hide:
                continue
            ax, side = {"east": (0, 1), "west": (0, 0), "up": (1, 1), "down": (1, 0), "south": (2, 1), "north": (2, 0)}[f]
            plane = c.to[ax] if side else c.frm[ax]
            o = [i for i in range(3) if i != ax]
            for d in self.cubes:
                if d is c or d.rotated or d.inflate or d.mat is None or not d.visible_export:
                    continue
                if d.mat.opts.get("alpha") or d.mat.kind == "glow" and c.mat.kind != "glow":
                    continue
                # d must contain the face's plane (touching or sunk into it) ...
                if side and not (d.frm[ax] - 1e-4 <= plane < d.to[ax] - 1e-4):
                    continue
                if not side and not (d.frm[ax] + 1e-4 < plane <= d.to[ax] + 1e-4):
                    continue
                # ... and cover the face's whole rectangle.
                if all(d.frm[i] - 1e-4 <= c.frm[i] and c.to[i] <= d.to[i] + 1e-4 for i in o):
                    hide.add(f)
                    break
        return hide

    # -- writing
    def save(self, model_dir, texture_dir=None, png_name=None):
        os.makedirs(model_dir, exist_ok=True)
        img, faces_uv, tex_size = self._paint()
        buf = io.BytesIO()
        Image.fromarray(img, "RGBA").save(buf, "PNG")
        png_name = png_name or self.name + ".png"
        if texture_dir:
            os.makedirs(texture_dir, exist_ok=True)
            with open(os.path.join(texture_dir, png_name), "wb") as fh:
                fh.write(buf.getvalue())
        doc = self._doc(faces_uv, tex_size, buf.getvalue(), png_name)
        path = os.path.join(model_dir, self.name + ".bbmodel")
        with open(path, "w", encoding="utf-8") as fh:
            json.dump(doc, fh)
        return path, len([c for c in self.cubes if c.visible_export]), tex_size

    # -- texture
    def _face_px(self, c, f):
        dx, dy, dz = (c.to[i] - c.frm[i] for i in range(3))
        w, h = {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy),
                "up": (dx, dz), "down": (dx, dz)}[f]
        return max(1, int(round(w * self.ppu))), max(1, int(round(h * self.ppu)))

    def _paint(self):
        rects = []          # (w, h, key, [(cube, face)])
        keyed = {}
        for c in self.cubes:
            if c.mat is None:
                continue
            hidden = self._hidden_faces(c)
            for f in FACES:
                if f in hidden:
                    continue
                w, h = self._face_px(c, f)
                if c.share is not None:
                    k = (c.share, f, w, h)
                    if k in keyed:
                        keyed[k][3].append((c, f))
                        continue
                    keyed[k] = [w, h, k, [(c, f)]]
                    rects.append(keyed[k])
                else:
                    rects.append([w, h, None, [(c, f)]])
        size, places = None, None
        for s in (16, 32, 64, 128, 256, 512, 1024, 2048):
            if s > self.max_texture:
                break
            places = _shelf_pack([(r[0], r[1]) for r in rects], s)
            if places is not None:
                size = s
                break
        if size is None:
            raise ValueError(f"{self.name}: faces do not fit a {self.max_texture} texture")
        img = np.zeros((size, size, 4), np.int16)
        faces_uv = {}
        for (w, h, key, users), (x, y) in zip(rects, places):
            c, f = users[0]
            rng = np.random.default_rng(zlib.crc32(f"{self.seed}:{c.name}:{f}".encode()))
            area = paint_face(c, f, w, h, self.ppu, rng)
            if c.decal:
                c.decal(area, f, w, h, c, rng)
            img[y:y + h, x:x + w] = area
            for cu, fa in users:
                faces_uv[(cu.uuid, fa)] = (x, y, x + w, y + h)
        return np.clip(img, 0, 255).astype(np.uint8), faces_uv, size

    def _doc(self, faces_uv, size, png, png_name):
        elements = []
        for c in self.cubes:
            faces = {}
            for f in FACES:
                if (c.uuid, f) in faces_uv:
                    faces[f] = {"uv": list(faces_uv[(c.uuid, f)]), "texture": 0}
                else:
                    faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
            e = {"name": c.name, "box_uv": False, "rescale": False, "locked": False, "light_emission": 0,
                 "render_order": "default", "allow_mirror_modeling": True,
                 "from": [round(v, 4) for v in c.frm], "to": [round(v, 4) for v in c.to],
                 "autouv": 0, "color": 0, "origin": [round(v, 4) for v in c.origin], "faces": faces,
                 "type": "cube", "uuid": c.uuid}
            if c.inflate:
                e["inflate"] = c.inflate
            if c.rotated:
                e["rotation"] = [round(v, 4) for v in c.rotation]
            if not c.visible_export:
                e["export"] = False
                e["visibility"] = False
            elements.append(e)
        groups, outliner = [], []

        def walk(g):
            node = {"uuid": g.uuid, "isOpen": g is self.root, "children": []}
            groups.append({"name": g.name, "uuid": g.uuid, "export": g is not self.dummy, "locked": False, "scope": 0,
                           "selected": False, "visibility": g is not self.dummy, "origin": [round(v, 4) for v in g.origin],
                           "rotation": g.rotation, "color": 0, "children": [], "reset": False, "shade": True,
                           "mirror_uv": False, "autouv": 0, "isOpen": g is self.root})
            for ch in g.children:
                node["children"].append(walk(ch) if isinstance(ch, Group) else ch.uuid)
            return node

        outliner.append(walk(self.root))
        if self.dummy is not None:            # keep the dummy at the top level, beside the model
            self.root.children.remove(self.dummy)
            groups.clear()
            outliner = [walk(self.root), walk(self.dummy)]
            self.root.children.append(self.dummy)
        tex = {"path": "", "name": png_name, "folder": "", "namespace": "", "id": "0", "group": "",
               "width": size, "height": size, "uv_width": size, "uv_height": size, "particle": False,
               "use_as_default": False, "layers_enabled": False, "sync_to_project": "", "render_mode": "default",
               "render_sides": "auto", "pbr_channel": "color", "frame_time": 1, "frame_order_type": "loop",
               "frame_order": "", "frame_interpolate": False, "visible": True, "internal": True, "saved": True,
               "uuid": _u(), "relative_path": None,
               "source": "data:image/png;base64," + base64.b64encode(png).decode()}
        doc = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": self.name,
               "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
               "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
               "resolution": {"width": size, "height": size}, "elements": elements, "groups": groups,
               "outliner": outliner, "textures": [tex]}
        if self.anims:
            doc["animations"] = [self._anim_doc(*a) for a in self.anims]
        return doc

    def _anim_doc(self, name, length, tracks, loop):
        by_name = {}

        def collect(g):
            by_name[g.name] = g
            for ch in g.children:
                if isinstance(ch, Group):
                    collect(ch)

        collect(self.root)
        animators = {}
        for bone, channels in tracks.items():
            g = by_name[bone]
            kfs = []
            for ch, keys in channels.items():
                for k in keys:
                    t, v = k[0], k[1]
                    interp = k[2] if len(k) > 2 else "catmullrom"
                    kfs.append({"channel": ch, "data_points": [{"x": str(round(v[0], 3)), "y": str(round(v[1], 3)),
                                                                 "z": str(round(v[2], 3))}],
                                "uuid": _u(), "time": round(t, 4), "color": -1, "interpolation": interp})
            animators[g.uuid] = {"name": bone, "type": "bone", "rotation_global": False,
                                 "quaternion_interpolation": False, "keyframes": kfs}
        return {"uuid": _u(), "name": name, "loop": loop, "override": False, "length": length, "snapping": 24,
                "selected": False, "group_name": "", "scope": 0, "anim_time_update": "", "blend_weight": "",
                "start_delay": "", "loop_delay": "", "animators": animators}


def _mirror_hide(h):
    sw = {"east": "west", "west": "east"}
    return {sw.get(f, f) for f in h}


def _shelf_pack(sizes, S):
    order = sorted(range(len(sizes)), key=lambda i: (-sizes[i][1], -sizes[i][0]))
    places = [None] * len(sizes)
    x = y = shelf = 0
    for i in order:
        w, h = sizes[i]
        if w > S or h > S:
            return None
        if x + w > S:
            x, y, shelf = 0, y + shelf, 0
        if y + h > S:
            return None
        places[i] = (x, y)
        x += w
        shelf = max(shelf, h)
    return places


# ---------------------------------------------------------------- painting

def world_of(c, f, w, h, ppu):
    """World coordinates of each texel centre on a face: (along, up) arrays of shape (h, w).
    'along' is the horizontal world axis as seen from outside (x, z), 'up' is world y for side
    faces and world z for up/down faces."""
    us = (np.arange(w) + 0.5) / ppu
    vs = (np.arange(h) + 0.5) / ppu
    fx, fy, fz = c.frm
    tx, ty, tz = c.to
    if f == "north":
        along = tx - us
    elif f == "south":
        along = fx + us
    elif f == "east":
        along = tz - us
    elif f == "west":
        along = fz + us
    else:
        along = fx + us
    if f in ("up", "down"):
        up = fz + vs
    else:
        up = ty - vs
    return np.broadcast_to(along[None, :], (h, w)), np.broadcast_to(up[:, None], (h, w))


def shade(mat, idx):
    r = mat.ramp
    return r[int(min(len(r) - 1, max(0, idx)))]


def paint_face(c, f, w, h, ppu, rng):
    """Paints one face into an (h, w, 4) array of ramp colours."""
    mat = c.mat
    o = mat.opts
    side = f not in ("up", "down")
    shift = FACE_SHIFT[f] if c.light is None else c.light.get(f, FACE_SHIFT[f])
    if o.get("flat_light"):
        shift = {"up": 0, "down": -1}.get(f, 0)
    idx = np.full((h, w), float(mat.base + shift))
    along, up = world_of(c, f, w, h, ppu)
    long_v = h >= w
    kind = mat.kind

    # gradient along world y (blades darker at the guard, lighter at the tip)
    if "grad_y" in o and side:
        y0, y1, amount = o["grad_y"]
        idx += np.clip((up - y0) / max(1e-6, y1 - y0), 0, 1) * amount - amount / 2

    noise = o.get("noise", {"metal": 0.10, "brick": 0.03, "slate": 0.03, "glass": 0.0, "glow": 0.04,
                            "gem": 0.0, "cloth": 0.08, "plank": 0.10, "wood": 0.10}.get(kind, 0.14))

    if kind in ("wood", "plank", "wrap", "rope"):
        _grain(idx, w, h, long_v, rng, kind, along, up, c, f, ppu, o)
    elif kind == "metal":
        _metal(idx, w, h, rng, o)
    elif kind == "brick":
        _brick(idx, along, up, f, ppu, rng, o)
    elif kind == "slate":
        _slate(idx, along, up, f, ppu, rng, o)
    elif kind == "stone":
        _cracks(idx, w, h, rng, o)
    elif kind == "cloth":
        _cloth(idx, w, h, along, up, f, ppu, rng, o)
    elif kind == "leather":
        _leather(idx, w, h, rng, o)
    elif kind == "fur":
        _fur(idx, w, h, rng, f)
    elif kind == "gem":
        _facets(idx, w, h)
    elif kind == "glow":
        _glow(idx, w, h, mat)
    elif kind == "glass":
        _glass(idx, w, h)
    elif kind == "skin":
        _skin(idx, w, h, rng, f)

    # noise clusters (2x2, one shade either way)
    if noise > 0 and w * h >= 4:
        for cy in range(0, h, 2):
            for cx in range(0, w, 2):
                roll = rng.random()
                if roll < noise / 2:
                    idx[cy:cy + 2, cx:cx + 2] -= 1
                elif roll > 1 - noise / 2:
                    idx[cy:cy + 2, cx:cx + 2] += 1

    # edge light and contact shadow
    if o.get("edges", True) and kind not in ("glow", "gem", "glass"):
        if side and h >= 3:
            idx[0, :] += 1
            idx[-1, :] -= 1 if not o.get("soft_bottom") else 0.5
        if o.get("bevel") and w >= 3 and h >= 3:
            idx[:, 0] += 0.6
            idx[:, -1] -= 0.6

    out = np.zeros((h, w, 4), np.int16)
    r = mat.ramp
    ii = np.clip(np.round(idx), 0, len(r) - 1).astype(int)
    lut = np.array(r, np.int16)
    out[..., :3] = lut[ii]
    if o.get("bands"):
        # two-colour bands across the face (awnings, banners): every other band uses the second ramp
        alt, width = o["bands"]
        band = (np.floor(along * ppu / width) % 2 == 1)
        lut2 = np.array(alt, np.int16)
        ii2 = np.clip(np.round(idx) - mat.base + len(alt) // 2, 0, len(alt) - 1).astype(int)
        out[..., :3] = np.where(band[..., None], lut2[ii2], out[..., :3])
    out[..., 3] = 255
    if o.get("alpha_fn"):
        o["alpha_fn"](out, f, w, h, rng)
    return out


def _grain(idx, w, h, long_v, rng, kind, along, up, c, f, ppu, o):
    if kind == "wrap":
        # diagonal wrap bands
        yy, xx = np.mgrid[0:h, 0:w]
        period = o.get("period", 4)
        band = ((yy + xx) % period)
        idx[band == 0] -= 2
        idx[band == 1] -= 1
        idx[band == period - 1] += 1
        return
    if kind == "rope":
        yy, xx = np.mgrid[0:h, 0:w]
        band = (yy * 2 + xx) % 4 if long_v else (xx * 2 + yy) % 4
        idx[band == 0] -= 1
        idx[band == 2] += 1
        return
    vertical_grain = o.get("grain_dir", "long")
    if vertical_grain == "long":
        gv = long_v if f not in ("up", "down") else (w < h)
    else:
        gv = vertical_grain == "v"
    n = w if gv else h
    m = h if gv else w
    step = o.get("grain_step", 3)
    for t in range(int(rng.integers(0, step)), n, step):
        for s in range(m):
            if rng.random() < 0.78:
                if gv:
                    idx[s, t] -= 1
                else:
                    idx[t, s] -= 1
    if kind == "plank" and f not in ("up", "down") or kind == "plank" and o.get("plank_top"):
        # plank seams across the grain, from world coordinates so they line up across cubes
        pw = o.get("plank", 3.0)          # plank width in units
        coord = along if gv else up
        seam = np.floor(coord / pw)
        edge = np.diff(seam, axis=1 if gv else 0, prepend=seam[:, :1] if gv else seam[:1, :]) != 0
        idx[edge] -= 2
        # each plank a slightly different shade
        idx += ((seam * 7919) % 3 - 1) * 0.5
        # nail pixels near both ends of each plank
        if o.get("nails", True) and min(w, h) >= 4:
            if gv:
                ys = [1, h - 2]
                for x in np.nonzero(edge[0])[0]:
                    for y in ys:
                        if x + 1 < w:
                            idx[y, x + 1] = 0.6
            else:
                for y in np.nonzero(edge[:, 0])[0]:
                    for x in (1, w - 2):
                        if y + 1 < h:
                            idx[y + 1, x] = 0.6
    # knots
    if kind in ("wood", "plank") and w * h > 60 and rng.random() < 0.5:
        ky, kx = int(rng.integers(1, max(2, h - 1))), int(rng.integers(1, max(2, w - 1)))
        idx[max(0, ky - 1):ky + 1, max(0, kx - 1):kx + 1] -= 2


def _metal(idx, w, h, rng, o):
    # scratches: short diagonal light lines with a dark pixel beside
    for _ in range(max(0, int(w * h / o.get("scratch_area", 70)))):
        sx, sy, ln = int(rng.integers(0, w)), int(rng.integers(0, h)), int(rng.integers(2, 5))
        d = 1 if rng.random() < 0.5 else -1
        for k in range(ln):
            x, y = sx + k * d, sy + k
            if 0 <= x < w and 0 <= y < h:
                idx[y, x] += 1.5
                if 0 <= x + 1 < w:
                    idx[y, x + 1] -= 0.8
    if o.get("polish"):
        # a soft diagonal sheen band
        yy, xx = np.mgrid[0:h, 0:w]
        d = (xx - yy * 0.7) / max(1, w)
        idx += np.where(np.abs(d - 0.3) < 0.12, 1, 0)
    if o.get("rivets") and w >= 6 and h >= 6:
        for (x, y) in ((1, 1), (w - 2, 1), (1, h - 2), (w - 2, h - 2)):
            idx[y, x] = 6
            if y + 1 < h:
                idx[y + 1, x] -= 1.5


def _brick(idx, along, up, f, ppu, rng, o):
    bw, bh = o.get("block", (8, 4))            # in pixels at this density
    bwu, bhu = bw / ppu, bh / ppu
    if f in ("up", "down") and not o.get("brick_top"):
        _cracks(idx, idx.shape[1], idx.shape[0], rng, {"cracks": 0.3})
        return
    row = np.floor(up / bhu)
    off = (row % 2) * bwu / 2
    col = np.floor((along + off) / bwu)
    # mortar
    py = (up / bhu) - row
    px = ((along + off) / bwu) - col
    mortar = (py * bh < 1.0) | (px * bw < 1.0)
    # block gradient: light top row, dark bottom row; neighbours vary one shade
    var = ((row * 31 + col * 17) % 5)
    idx += np.where(var == 0, -1, np.where(var == 4, 1, 0)) * 0.7
    idx += np.where(py * bh > bh - 1, 1, 0)                 # top row of each block (y up)
    idx += np.where((py * bh >= 1) & (py * bh < 2), -0.7, 0)
    idx[mortar] = o.get("mortar", 1)
    # chipped corners
    for _ in range(int(idx.size / 400)):
        y, x = int(rng.integers(0, idx.shape[0])), int(rng.integers(0, idx.shape[1]))
        idx[y, x] -= 1


def _slate(idx, along, up, f, ppu, rng, o):
    th = o.get("tile_h", 3)
    tw = o.get("tile_w", 4)
    if f == "down":
        return
    coord = up if f != "up" else -up
    row = np.floor(coord * ppu / th)
    py = coord * ppu / th - row
    off = (row % 2) * tw / 2
    col = np.floor((along * ppu + off) / tw)
    px = (along * ppu + off) / tw - col
    idx += ((row * 13 + col * 7) % 3 - 1) * 0.5
    idx[py * th > th - 1] += 1                   # lighter top line
    idx[py * th < 1] -= 2                        # dark gap under the row
    idx[(px * tw < 1) & (py * th >= 1)] -= 1     # staggered joints


def _cracks(idx, w, h, rng, o):
    n = int(w * h / 90 * o.get("cracks", 1))
    for _ in range(n):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        for _ in range(int(rng.integers(2, 6))):
            if 0 <= x < w and 0 <= y < h:
                idx[y, x] -= 2
                if x + 1 < w:
                    idx[y, x + 1] += 1
            x += int(rng.integers(-1, 2))
            y += 1


def _cloth(idx, w, h, along, up, f, ppu, rng, o):
    if f not in ("up", "down"):
        # soft vertical folds
        period = o.get("fold", 4)
        xx = np.arange(w)
        ph = int(rng.integers(0, period))
        fold = (xx + ph) % period
        idx[:, fold == 0] -= 1
        idx[:, fold == 1] += 0.5
    pat = o.get("pattern")
    if pat == "stripes":
        period = o.get("stripe", 4)
        rows = np.floor(up * ppu) % period
        idx[rows == 0] += 2
    elif pat == "check":
        c = (np.floor(up * ppu / 3) + np.floor(along * ppu / 3)) % 2
        idx += c * 1.0
    trim = o.get("trim")
    if trim and f not in ("up", "down") and h >= 4:
        idx[-1, :] = trim
        idx[-2, :] = trim - 1
    if o.get("stitch") and f not in ("up", "down") and w >= 5 and h >= 5:
        idx[1, 1:-1:2] += 2


def _leather(idx, w, h, rng, o):
    # soft creases
    for _ in range(int(w * h / 50)):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        ln = int(rng.integers(2, 4))
        idx[y, x:x + ln] -= 1
    if o.get("stitch", True) and w >= 5 and h >= 5:
        idx[1, 1:-1:2] += 2.2
        idx[-2, 1:-1:2] += 2.2


def _fur(idx, w, h, rng, f):
    for _ in range((w * h) // 10):
        x, y, ln = int(rng.integers(0, w)), int(rng.integers(0, h)), int(rng.integers(2, 4))
        for d in range(ln):
            if y + d < h:
                idx[y + d, x] += 1 if d == 0 else -0.8
    if f not in ("up", "down"):
        yy = np.arange(h)[:, None]
        idx -= yy / max(1, h) * 1.2            # lighter on top, darker towards the belly


def _skin(idx, w, h, rng, f):
    if f not in ("up", "down"):
        yy = np.arange(h)[:, None]
        idx -= yy / max(1, h) * 0.8
    for _ in range((w * h) // 40):
        x, y = int(rng.integers(0, w)), int(rng.integers(0, h))
        idx[y, x] -= 0.8


def _facets(idx, w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    upper = (xx * h + yy * w) < (w * h)        # top-left half lighter
    idx += np.where(upper, 1.5, -1)
    idx[0, 0] = 99                              # highlight pixel
    if w > 2 and h > 2:
        idx[1, 1] = 99


def _glow(idx, w, h, mat):
    yy, xx = np.mgrid[0:h, 0:w]
    d = np.maximum(np.abs((xx + 0.5) / w - 0.5), np.abs((yy + 0.5) / h - 0.5)) * 2
    top = len(mat.ramp) - 1
    idx[:] = top - d * (top - mat.base) - 0.2


def _glass(idx, w, h):
    yy, xx = np.mgrid[0:h, 0:w]
    idx[:] = 1
    idx[(xx + yy) % max(3, w) == 1] = 3        # a glint
    if w >= 4 and h >= 4:
        idx[0, :] = 3
        idx[:, 0] = 2.5


# ---------------------------------------------------------------- decal helpers

def put(area, x, y, rgb, a=255):
    h, w = area.shape[:2]
    if 0 <= x < w and 0 <= y < h:
        area[y, x, :3] = rgb
        area[y, x, 3] = a


def draw(area, pattern, legend, x0=0, y0=0, center=False):
    """Draws an ASCII pattern on a face. legend maps characters to RGB; '.' is skipped."""
    h, w = area.shape[:2]
    ph, pw = len(pattern), max(len(r) for r in pattern)
    if center:
        x0, y0 = x0 + (w - pw) // 2, y0 + (h - ph) // 2
    for j, row in enumerate(pattern):
        for i, ch in enumerate(row):
            if ch in legend:
                put(area, x0 + i, y0 + j, legend[ch])


def clear_alpha(area, mask):
    area[mask, 3] = 0


# ---------------------------------------------------------------- icons

def icon_ramp(path, n=7, skip_dark=0.12):
    """A ramp sampled from a pixel-art icon: its opaque colours by brightness, outline left out."""
    a = np.array(Image.open(path).convert("RGBA")).reshape(-1, 4)
    a = a[a[:, 3] > 0][:, :3].astype(float)
    lum = a @ np.array([0.3, 0.59, 0.11]) / 255
    a, lum = a[lum > skip_dark], lum[lum > skip_dark]
    if len(a) == 0:
        return [(128, 128, 128)] * n
    order = np.argsort(lum)
    a = a[order]
    out = []
    for i in range(n):
        q = a[int(min(len(a) - 1, (i + 0.5) / n * len(a)))]
        out.append(clamp_rgb(q))
    return out
