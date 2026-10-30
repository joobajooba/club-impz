"""Build the Blockbench pickaxe (Generic Model) with the Stone tier texture.

Follows docs/MODELS-BLOCKBENCH.md and docs/BLOCKBENCH-STUDY.md:
- 2 texture pixels per Blockbench unit (D-053), 16 units = 1 m.
- Box sizes in whole texture pixels (0.5 units). Odd widths for centred parts.
- Per-face UV, one 64x64 texture, hidden faces removed.
- Colours picked from sprites/pickaxes/stone_pickaxe.png.
- Lit from the top, slightly left; hue-shifted ramps, edge highlights,
  painted shadow where parts meet, clusters not noise.

Everything is designed on a pixel grid ("px", 1 px = 0.5 units). Columns in
x and z are centred on whole numbers, so an odd-width part centred on column
0 is centred on the origin. Rows in y start at 0 at the bottom of the handle.

Usage: python build_pickaxe_bbmodel.py <out_dir>
"""

import base64
import io
import json
import sys
import uuid
from pathlib import Path

from PIL import Image

TEX = 64  # texture size in pixels
PX = 0.5  # Blockbench units per texture pixel (D-053)


def hexrgb(h):
    h = h.lstrip("#")
    return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4)) + (255,)


# Ramps, darkest first. Every colour is taken from the stone_pickaxe sprite.
STONE = [hexrgb(c) for c in ("#4d444c", "#5a5d69", "#8c8f94", "#bdb7b3", "#daccbb")]
FLECK = [hexrgb(c) for c in ("#534333", "#7b674b", "#907e62", "#b39462", "#b39462")]
WOOD = [hexrgb(c) for c in ("#301e14", "#442f1e", "#5d4f3e", "#7b674b", "#907e62")]
CORD = [hexrgb(c) for c in ("#301e14", "#442f1e", "#907e62", "#b39462", "#f2d762")]


# ---------------------------------------------------------------- geometry

def box(name, group, part, cols, rows, depth):
    """cols: (first, last) column, inclusive. rows: (bottom, top) exclusive top.
    depth: odd number of columns in z, centred on 0."""
    c0, c1 = cols
    r0, r1 = rows
    h = (depth - 1) / 2
    return {
        "name": name, "group": group, "part": part,
        "lo": [c0 - 0.5, r0, -h - 0.5],
        "hi": [c1 + 0.5, r1, h + 0.5],
    }


BOXES = [
    # Handle: 3 px square, 26 px (13 units) long, top pokes out of the binding.
    # The cord wrap below the binding is painted on (rows 11-13), not modelled.
    box("handle", "handle", "wood", (-1, 1), (0, 26), 3),
    # Lashing that ties the head to the handle.
    box("binding", "head", "binding", (-2, 2), (15, 24), 5),
    # Pick arm (left): gentle curve down to a point, as in the sprite.
    box("pick_1", "head", "stone", (-5, -3), (17, 23), 3),
    box("pick_2", "head", "stone", (-8, -6), (16, 22), 3),
    box("pick_3", "head", "stone", (-10, -9), (15, 21), 3),
    box("pick_4", "head", "stone", (-11, -11), (14, 19), 3),
    box("pick_5", "head", "stone", (-12, -12), (13, 17), 1),
    box("pick_6", "head", "stone", (-13, -13), (12, 15), 1),
    # Blunt arm (right): broadens toward a rounded end.
    box("blunt_1", "head", "stone", (3, 5), (17, 23), 3),
    box("blunt_2", "head", "stone", (6, 8), (16, 22), 3),
    box("blunt_3", "head", "stone", (9, 10), (14, 21), 3),
    box("blunt_4", "head", "stone", (11, 11), (13, 20), 3),
    box("blunt_5", "head", "stone", (12, 12), (13, 19), 3),
    box("blunt_6", "head", "stone", (13, 13), (14, 18), 1),
]

FACES = ["north", "east", "south", "west", "up", "down"]
NORMAL = {"north": (0, 0, -1), "south": (0, 0, 1), "east": (1, 0, 0),
          "west": (-1, 0, 0), "up": (0, 1, 0), "down": (0, -1, 0)}


def face_frame(b, f):
    """Corner, u direction, v direction, width, height (px) of a face,
    in Blockbench's orientation (see js/util/three_custom.js setShape)."""
    (x0, y0, z0), (x1, y1, z1) = b["lo"], b["hi"]
    dx, dy, dz = x1 - x0, y1 - y0, z1 - z0
    return {
        "north": ((x1, y1, z0), (-1, 0, 0), (0, -1, 0), dx, dy),
        "south": ((x0, y1, z1), (1, 0, 0), (0, -1, 0), dx, dy),
        "east": ((x1, y1, z1), (0, 0, -1), (0, -1, 0), dz, dy),
        "west": ((x0, y1, z0), (0, 0, 1), (0, -1, 0), dz, dy),
        "up": ((x0, y1, z0), (1, 0, 0), (0, 0, 1), dx, dz),
        "down": ((x0, y0, z1), (1, 0, 0), (0, 0, -1), dx, dz),
    }[f]


def texels(b, f):
    """Yield (i, j, centre) for every texel of a face."""
    o, u, v, w, h = face_frame(b, f)
    for j in range(int(h)):
        for i in range(int(w)):
            yield i, j, tuple(o[k] + (i + 0.5) * u[k] + (j + 0.5) * v[k] for k in range(3))


def inside(p, b, eps=1e-6):
    return all(b["lo"][k] + eps < p[k] < b["hi"][k] - eps for k in range(3))


def covered(p, f, me):
    """True if the texel at p on face f of box `me` is buried in another box."""
    n = NORMAL[f]
    q = tuple(p[k] + 0.25 * n[k] for k in range(3))
    return any(inside(q, b) for b in BOXES if b is not me)


# Front-view outline of the stone head, per column.
HEAD_TOP, HEAD_BOT = {}, {}
for b in BOXES:
    if b["part"] != "stone":
        continue
    for c in range(int(b["lo"][0] + 0.5), int(b["hi"][0] + 0.5)):
        HEAD_TOP[c] = max(HEAD_TOP.get(c, -99), b["hi"][1])
        HEAD_BOT[c] = min(HEAD_BOT.get(c, 99), b["lo"][1])

# Hand-placed fleck clusters on the stone (column, row), different per side
# so the two faces don't mirror each other.
FLECKS = {
    "south": {(-5, 19), (-4, 19), (-4, 18), (-8, 18), (-7, 18), (-10, 16),
              (4, 19), (5, 19), (5, 18), (9, 16), (10, 16), (10, 15), (7, 20)},
    "north": {(-6, 19), (-6, 18), (-7, 18), (-9, 16), (-9, 17),
              (4, 18), (6, 19), (7, 19), (7, 18), (11, 16), (12, 15)},
}

# Gold glints on the top row of a wrap: the sprite's yellow pixels, the accent.
GLINTS = {"south": {(-1, 22), (1, 19)}, "north": {(1, 22), (-1, 16)},
          "west": {(0, 19)}, "east": set()}


def col(p):
    return round(p[0])


def zcol(p):
    return round(p[2])


def row(p):
    return int(p[1] // 1)


# ---------------------------------------------------------------- painting

def paint_stone(b, f, p, i, j):
    c, r = col(p), row(p)
    left = c < 0
    top, bot = HEAD_TOP.get(c), HEAD_BOT.get(c)
    if f in ("north", "south"):
        v = 2
        if r == top - 1 or (r == top - 2 and top - bot >= 6):
            v = 3  # lit upper band on the thick part of the head
        elif r == bot:
            v = 1
        if abs(c) == 3 and v < 3:  # painted shadow against the binding
            v -= 1
        if (c, r) in FLECKS[f] and v in (1, 2):
            return FLECK[v + 1]
        return STONE[v]
    if f == "up":
        w = int(b["hi"][0] - b["lo"][0])
        inner = (i == w - 1) if left else (i == 0)
        outer = (i == 0) if left else (i == w - 1)
        if w > 1 and inner:
            return STONE[2]
        if left and outer and b["name"] in ("pick_1", "pick_2", "pick_3"):
            return STONE[4]  # the brightest corner, facing the light
        return STONE[3]
    if f == "west":
        return STONE[3] if r == int(b["hi"][1]) - 1 else STONE[2 if left else 1]
    if f == "east":
        return STONE[2] if r == int(b["hi"][1]) - 1 else STONE[1]
    # down
    return STONE[0] if abs(c) <= 4 else STONE[1]


def paint_wood(b, f, p, i, j):
    c, z, r = col(p), zcol(p), row(p)
    if f == "up":
        return WOOD[2] if (c, z) == (0, 0) else WOOD[4]  # end grain, dark heart
    if f == "down":
        return WOOD[2] if (c, z) == (0, 0) else WOOD[1]
    if f == "west":
        v, k = 4, z
    elif f == "east":
        v, k = 2, -z
    else:
        k = c if f == "south" else -c
        v = 4 if c == -1 else 3  # lit edge on the left
    if 11 <= r <= 13:  # cord wrap painted below the binding
        top = r == 13
        gap, cord, cord_top = cord_tones(f)
        return CORD[cord_top if top else (gap if r == 11 else cord)]
    # Grain: short streaks running along the handle, staggered per column.
    phase = (r + 3 * k + (2 if f in ("north", "east") else 0)) % 7
    if phase in (0, 1):
        v -= 1
    elif phase == 4 and v < 4:
        v += 1
    # Painted shadow next to the cord, and a darker butt end.
    if r in (10, 14, 24) or r == 0:
        v -= 1
    return WOOD[max(v, 0)]


def cord_tones(f):
    # (gap, cord, cord top) per face: lit from the top and left.
    return {"west": (1, 3, 3), "up": (1, 3, 3), "north": (1, 2, 3),
            "south": (1, 2, 3), "east": (0, 2, 2), "down": (0, 1, 2)}[f]


def paint_binding(b, f, p, i, j):
    """Even wraps (two cord rows, one dark gap), rounded off toward the shaded
    side. Gold glints on a few wrap tops are the accent."""
    c, z, r = col(p), zcol(p), row(p)
    gap, cord, cord_top = cord_tones(f)
    if f in ("up", "down"):
        ring = max(abs(c), abs(z)) == 2
        return CORD[(cord_top if f == "up" else cord) if ring else gap]
    s = (r - 15) % 3
    if s == 2:
        return CORD[gap]
    lk = c if f in ("south", "north") else z
    if s == 1 and (lk, r) in GLINTS[f]:
        return CORD[4]
    v = cord_top if s == 1 else cord
    if f in ("north", "south") and c == 2 and v == 3:
        v = 2  # the wrap turns away from the light
    if r == 15:
        v -= 1  # bottom wrap sits in the shadow of the head
    return CORD[v]


PAINTERS = {"stone": paint_stone, "wood": paint_wood, "binding": paint_binding}


# ---------------------------------------------------------------- UV packing

def pack(rects, size):
    """Shelf-pack (key, w, h) into a size x size sheet. Returns key -> (x, y)."""
    out, x, y, shelf = {}, 0, 0, 0
    for key, w, h in sorted(rects, key=lambda r: (-r[2], -r[1])):
        if x + w > size:
            x, y, shelf = 0, y + shelf, 0
        if y + h > size:
            raise SystemExit(f"UVs don't fit in {size}x{size}")
        out[key] = (x, y)
        x += w
        shelf = max(shelf, h)
    return out


def build(out_dir):
    out_dir = Path(out_dir)
    out_dir.mkdir(parents=True, exist_ok=True)

    visible = {}
    for bi, b in enumerate(BOXES):
        for f in FACES:
            pts = list(texels(b, f))
            if all(covered(p, f, b) for _, _, p in pts):
                continue
            _, _, _, w, h = face_frame(b, f)
            visible[(bi, f)] = (int(w), int(h))

    places = pack([(k, w, h) for k, (w, h) in visible.items()], TEX)
    img = Image.new("RGBA", (TEX, TEX), (0, 0, 0, 0))
    for (bi, f), (ox, oy) in places.items():
        b = BOXES[bi]
        for i, j, p in texels(b, f):
            img.putpixel((ox + i, oy + j), PAINTERS[b["part"]](b, f, p, i, j))

    tex_png = out_dir / "pickaxe_stone.png"
    img.save(tex_png)

    # ------------------------------------------------------------ .bbmodel
    def uid():
        return str(uuid.uuid4())

    def u(v):
        return round(v * PX, 4)

    groups = {
        "handle": {"origin": [0, u(4), 0], "children": []},  # grip
        "head": {"origin": [0, u(19), 0], "children": []},   # centre of binding
    }
    elements = []
    for bi, b in enumerate(BOXES):
        faces = {}
        for f in FACES:
            if (bi, f) in places:
                ox, oy = places[(bi, f)]
                w, h = visible[(bi, f)]
                faces[f] = {"uv": [ox, oy, ox + w, oy + h], "texture": 0}
            else:
                faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
        e = {
            "name": b["name"], "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": [u(v) for v in b["lo"]], "to": [u(v) for v in b["hi"]],
            "autouv": 0, "color": 0, "origin": groups[b["group"]]["origin"],
            "faces": faces, "type": "cube", "uuid": uid(),
        }
        elements.append(e)
        groups[b["group"]]["children"].append(e["uuid"])

    # Scale dummy: hidden and never exported. Height is a PLACEHOLDER taken from
    # the Three.js test character (models/character.glb, ~1.13 m = 18 units)
    # until the Imp's height is decided (MODELS-BLOCKBENCH open question 1).
    dummy = {
        "name": "scale_dummy_imp_placeholder", "box_uv": False, "rescale": False,
        "locked": True, "light_emission": 0, "render_order": "default",
        "allow_mirror_modeling": True, "export": False, "visibility": False,
        "from": [8, 0, -2], "to": [12, 18, 2], "autouv": 0, "color": 1,
        "origin": [10, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    elements.append(dummy)

    def group(name, g, children):
        return {"name": name, "origin": g["origin"], "color": 0, "uuid": uid(),
                "export": True, "mirror_uv": False, "isOpen": True, "locked": False,
                "visibility": True, "autouv": 0, "children": children}

    outliner = [
        group("pickaxe", groups["handle"], [
            group("handle", groups["handle"], groups["handle"]["children"]),
            group("head", groups["head"], groups["head"]["children"]),
        ]),
        dict(group("scale_dummy", {"origin": [10, 0, 0]}, [dummy["uuid"]]),
             export=False, visibility=False),
    ]

    buf = io.BytesIO()
    img.save(buf, "PNG")
    texture = {
        "path": str(tex_png.resolve()), "name": tex_png.name, "folder": "",
        "namespace": "", "id": "0", "group": "", "width": TEX, "height": TEX,
        "uv_width": TEX, "uv_height": TEX, "particle": False,
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
        "name": "pickaxe", "model_identifier": "", "visible_box": [1, 1, 0],
        "variable_placeholders": "", "variable_placeholder_buttons": [],
        "timeline_setups": [], "unhandled_root_fields": {},
        "resolution": {"width": TEX, "height": TEX},
        "elements": elements, "outliner": outliner, "textures": [texture],
    }
    (out_dir / "pickaxe.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"boxes: {len(BOXES)}  visible faces: {len(visible)}  "
          f"texels used: {used}/{TEX * TEX}")
    return BOXES, places, visible, img


if __name__ == "__main__":
    build(sys.argv[1] if len(sys.argv) > 1 else ".")
