"""Shared helpers for the Blockbench tools: pixel-sprite parts, painting and .bbmodel writing.

A tool is a handle, an optional socket, and **sprites**: flat pixel drawings in the front
plane, given as text, pushed out to a depth per pixel. This is the 3D-sprite technique of
the reference tools (BLOCKBENCH-STUDY section 2.1), and it lets any blade shape (a hook, a
hole, a jagged edge) be drawn as pixels and turned into as few boxes as possible.

Sprite legend, one character per texture pixel, top row first:
  #  metal, 3 deep        +  metal, 1 deep (thin edges)      %  metal, 5 deep
  0-4  a forced metal shade, 3 deep (0 darkest)
  , ; : !  a forced metal shade 0, 1, 3, 4, 1 deep
  e / E  the accent colour (glow), 3 / 1 deep
  a-d / A-D  the gem ramp (darkest a), 3 / 1 deep
  w  the string colour (a bowstring), 1 deep
  .  empty
Unforced pixels are lit from the top left by their outline: top edges light, the
top-left corners lightest, bottom and right edges dark, painted shadow next to the socket
and the handle.

Same rules as the pickaxes (docs/MODELS-BLOCKBENCH.md): 2 texture pixels per unit
(D-053), whole-pixel boxes, per-face UV, hidden faces removed.
"""

import copy
import json
from pathlib import Path

from PIL import Image

from build_pickaxe_bbmodel import FACES, NORMAL, PX, face_frame, pack, texels
from build_pickaxe_metal_bbmodel import (
    box, code_colour, covered, group, paint_float, paint_gem, paint_socket, paint_trim,
    paint_wood, project, texture_entry, u, uid)

LEGEND = {"#": (3, None), "+": (1, None), "%": (5, None),
          "0": (3, "0"), "1": (3, "1"), "2": (3, "2"), "3": (3, "3"), "4": (3, "4"),
          ",": (1, "0"), ";": (1, "1"), ":": (1, "3"), "!": (1, "4"),
          "e": (3, "e"), "E": (1, "e")}
LEGEND.update({g: (3, g) for g in "abcd"})
LEGEND.update({g.upper(): (1, g) for g in "abcd"})
LEGEND["w"] = (1, "w")


def sprite(name, x0, y_top, rows, part="sprite"):
    """Boxes for a pixel drawing whose top-left pixel is at column x0, row y_top.
    Each box carries the drawing so the painter can read the outline."""
    cells = {}
    for j, line in enumerate(rows):
        for i, ch in enumerate(line):
            if ch != ".":
                cells[(x0 + i, y_top - j)] = ch
    return sprite_cells(name, cells, part)


def sprite_cells(name, cells, part="sprite"):
    """Boxes for a pixel drawing given as {(column, row): legend character}."""
    shape = {"cells": cells}
    boxes = []
    for (c0, c1, r0, r1, depth) in _merge(cells):
        boxes.append(box(f"{name}_{len(boxes) + 1}", part, (c0, c1), (r0, r1 + 1), depth,
                         sprite=shape))
    return boxes


def _merge(cells):
    """Cover the cells with boxes of one depth each, trying runs along columns and along
    rows and keeping whichever needs fewer boxes."""
    def runs(by_col):
        out = []
        keyed = {}
        for (c, r), ch in cells.items():
            d = LEGEND[ch][0]
            a, b = (c, r) if by_col else (r, c)
            keyed.setdefault((a, d), []).append(b)
        segs = {}
        for (a, d), bs in keyed.items():
            bs.sort()
            start = prev = bs[0]
            for b in bs[1:] + [None]:
                if b is not None and b == prev + 1:
                    prev = b
                    continue
                segs.setdefault((start, prev, d), []).append(a)
                if b is not None:
                    start = prev = b
        for (s, e, d), lines in segs.items():
            lines.sort()
            first = last = lines[0]
            for a in lines[1:] + [None]:
                if a is not None and a == last + 1:
                    last = a
                    continue
                if by_col:
                    out.append((first, last, s, e, d))
                else:
                    out.append((s, e, first, last, d))
                if a is not None:
                    first = last = a
        return out
    a, b = runs(True), runs(False)
    return a if len(a) <= len(b) else b


# ---------------------------------------------------------------- painting

def paint_sprite(t, b, f, p, i, j):
    m = t["metal"]
    n = NORMAL[f]
    c, r = round(p[0] - 0.25 * n[0]), int((p[1] - 0.25 * n[1]) // 1)  # this box's cell
    cells = b["sprite"]["cells"]
    ch = cells.get((c, r), "#")
    role = LEGEND[ch][1]
    if role == "w":
        return t["string"]
    if role and not role.isdigit():
        return code_colour(t, role)  # gems and glow colour every face
    if f in ("north", "south") and role:
        return m[int(role)]
    up, down = (c, r + 1) in cells, (c, r - 1) in cells
    left, right = (c - 1, r) in cells, (c + 1, r) in cells
    if f == "up":
        return m[4 if not left else 3]
    if f == "down":
        return m[0]
    if f == "west":
        return m[3] if not up else m[2]
    if f == "east":
        return m[2] if not up else m[1]
    if not up:
        v = 4 if not left else 3
    elif not down:
        v = 1
    elif not left:
        v = 3
    elif not right:
        v = 1
    else:
        v = 2
    if f == "north":
        v = min(v, 3)  # the back face never gets the glint
    if near_join(t, c, r):
        v -= 1
    return m[max(v, 0)]


def near_join(t, c, r):
    """True for a sprite pixel next to the socket or the handle: painted shadow."""
    for b in t["_joins"]:
        x0, x1 = b["lo"][0] - 1, b["hi"][0] + 1
        y0, y1 = b["lo"][1] - 1, b["hi"][1] + 1
        if x0 < c < x1 and y0 < r < y1 - 0.5:
            return True
    return False


def paint_cord(t, b, f, p, i, j):
    """A lashing of cord: even wraps, two cord rows and a dark gap, lit on top and left."""
    w = t["cord"]
    r = int(p[1] // 1) - int(b["lo"][1])
    if f in ("up", "down"):
        return w[3 if f == "up" else 1]
    if r % 3 == 2:
        return w[0]
    lit = f in ("west", "south")
    return w[(3 if r % 3 == 1 else 2) - (0 if lit else 1)]


PAINTERS = {"sprite": paint_sprite, "socket": paint_socket, "wood": paint_wood,
            "trim": paint_trim, "gem": paint_gem, "float": paint_float, "cord": paint_cord}


# ---------------------------------------------------------------- .bbmodel

def write_model(out_dir, key, t, boxes, head_origin, handle_origin=4):
    """One tool: its texture and its .bbmodel. Returns (elements, image, texture size).
    The origins are rows: the head's pivot, and the grip's."""
    t = dict(t, _joins=[b for b in boxes if b["part"] in ("socket", "wood", "cord")])
    visible = {}
    for bi, b in enumerate(boxes):
        for f in FACES:
            if all(covered(boxes, p, f, b) for _, _, p in texels(b, f)):
                continue
            _, _, _, w, h = face_frame(b, f)
            visible[(bi, f)] = (int(w), int(h))
    rects = [(k, w, h) for k, (w, h) in visible.items()]
    size = 64
    while True:
        try:
            places = pack(rects, size)
            break
        except SystemExit:
            size *= 2

    img = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    for (bi, f), (ox, oy) in places.items():
        b = boxes[bi]
        for i, j, p in texels(b, f):
            img.putpixel((ox + i, oy + j), PAINTERS[b["part"]](t, b, f, p, i, j))
    path = out_dir / f"{key}.png"
    img.save(path)

    origins = {"handle": [0, u(handle_origin), 0], "head": [0, u(head_origin), 0]}
    children = {"handle": [], "head": []}
    elements = []
    for bi, b in enumerate(boxes):
        faces = {}
        for f in FACES:
            if (bi, f) in places:
                ox, oy = places[(bi, f)]
                w, h = visible[(bi, f)]
                faces[f] = {"uv": [ox, oy, ox + w, oy + h], "texture": 0}
            else:
                faces[f] = {"uv": [0, 0, 0, 0], "texture": None}
        g = b.get("group", "head")
        e = {
            "name": b["name"], "box_uv": False, "rescale": False, "locked": False,
            "light_emission": 0, "render_order": "default", "allow_mirror_modeling": True,
            "from": [u(v) for v in b["lo"]], "to": [u(v) for v in b["hi"]],
            "autouv": 0, "color": 0, "origin": origins[g],
            "faces": faces, "type": "cube", "uuid": uid(),
        }
        elements.append(e)
        children[g].append(e["uuid"])

    # Scale dummy: hidden and never exported, the same PLACEHOLDER Imp height as the
    # pickaxes (~1.13 m = 18 units) until the Imp's height is decided.
    dummy = {
        "name": "scale_dummy_imp_placeholder", "box_uv": False, "rescale": False,
        "locked": True, "light_emission": 0, "render_order": "default",
        "allow_mirror_modeling": True, "export": False, "visibility": False,
        "from": [12, 0, -2], "to": [16, 18, 2], "autouv": 0, "color": 1,
        "origin": [14, 0, 0],
        "faces": {f: {"uv": [0, 0, 0, 0], "texture": None} for f in FACES},
        "type": "cube", "uuid": uid(),
    }
    tool = key.split("_", 1)[-1] if "_" in key else key
    outliner = [
        group(tool, origins["handle"], [
            group("handle", origins["handle"], children["handle"]),
            group("head", origins["head"], children["head"]),
        ]),
        group("scale_dummy", [14, 0, 0], [dummy["uuid"]], export=False, visibility=False),
    ]
    model = project(key, elements + [dummy], outliner, [texture_entry(0, img, path)], size)
    (out_dir / f"{key}.bbmodel").write_text(json.dumps(model, indent="\t"))

    used = sum(w * h for w, h in visible.values())
    print(f"{key:<22} boxes: {len(boxes):>2}  visible faces: {len(visible):>3}  "
          f"texels used: {used}/{size * size}")
    return elements, img, size


def write_lineup(out_dir, name, sets, spacing=20):
    """Every tier of a tool side by side, each with its own texture, for review in
    Blockbench. All UVs are scaled onto the largest texture's grid."""
    size = max(s for _, _, _, s in sets)
    elements, outliner, textures = [], [], []
    for ti, (key, src, img, own) in enumerate(sets):
        dx = ti * spacing
        kids = []
        for e in src:
            e = copy.deepcopy(e)
            e["uuid"] = uid()
            e["from"][0] += dx
            e["to"][0] += dx
            e["origin"] = [e["origin"][0] + dx] + e["origin"][1:]
            for face in e["faces"].values():
                if face["texture"] is not None:
                    face["texture"] = ti
                    face["uv"] = [v * size // own for v in face["uv"]]
            elements.append(e)
            kids.append(e["uuid"])
        outliner.append(group(key, [dx, 2, 0], kids))
        tex = texture_entry(ti, img, out_dir / f"{key}.png")
        tex["uv_width"] = tex["uv_height"] = size
        textures.append(tex)
    model = project(name, elements, outliner, textures, size)
    (Path(out_dir) / f"{name}.bbmodel").write_text(json.dumps(model, indent="\t"))
