"""Builds a Blockbench pickaxe from every sprite in godot-game/assets/sprites/pickaxes/.

J00BA's 48x48 sprites are the design (blockbench_detailed_prompts.md, section 3.5 and the
item picture rule in docs/CLAUDE.md): this script keeps every one of their pixels and gives
them real depth, so the model in the Imp's hand is the sprite, solid.

How a sprite becomes a model:
  1. The sprite is drawn on the diagonal (handle bottom left, head top right). It is smoothed
     (Scale2x twice) and turned 45 degrees so the handle stands up, sampled at the size that
     makes the pickaxe LENGTH units long at PX texture pixels per unit.
  2. The handle is the straight band at the bottom. It becomes a square shaft (as deep as it
     is wide), cut into one box per band of the sprite (end cap, wraps, wood), wider where
     the sprite is wider (caps and collars).
  3. The head is everything above. It is built in two layers by greedy rectangles: the whole
     outline as a thin plate, and the outline eroded by EDGE pixels as a thicker core, so the
     head is thick in the middle and thin at the edges, like a forged head.
  4. The collar (where the head meets the handle) is one box deeper than the shaft.
  5. One texture, 256x256: the turned sprite for the front and back, and four shaded copies
     for the tops, bottoms and the two sides (light from the top front left), so the model
     reads as solid even under flat light. No colour is invented: every texel comes from the
     sprite, lightened or darkened.

Writes, for every sprite <name>_pickaxe.png:
  godot-game/assets/models/tools/<name>_pickaxe.bbmodel   (texture embedded)
  godot-game/assets/textures/tools/<name>_pickaxe.png
and godot-game/assets/models/tools/pickaxes_lineup.bbmodel with all of them side by side.

Frame: handle along +Y from y = 0, head along X, centred on x = 0 and z = 0, so the game's
hand code (characters/gatherer.gd, GRIPS) holds it like the earlier tools. Pivot at the grip.

Run: python godot-game/assets/models/source/blockbench/tools/build_pickaxes_from_sprites.py
Needs Pillow and numpy.
"""
import base64
import io
import json
import math
import uuid
from pathlib import Path

import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
GAME = HERE.parents[4]                                 # godot-game/
SPRITES = GAME / "assets" / "sprites" / "pickaxes"
OUT_MODELS = GAME / "assets" / "models" / "tools"
OUT_TEX = GAME / "assets" / "textures" / "tools"

PX = 4              # texture pixels per unit for held tools (blockbench_detailed_prompts 1.4)
LENGTH = 16.0       # units from the end cap to the top of the head (section 3.5: 16 to 20)
ATLAS = 256         # texture size
EDGE = 2            # sprite pixels of thin edge round the head before the thick core
HEAD_DEPTH = (0.75, 1.5)   # units: the thin outline plate, the thick core
GRIP = 2.75         # units up the handle where the hand holds it (gatherer.gd grip 0.18 m)
SPACING = 22.0      # units between pickaxes in the lineup


# --- turning the sprite upright ----------------------------------------------------------

def scale2x(a):
    """EPX / Scale2x on an (h, w, 4) array: doubles the size and rounds diagonal steps."""
    h, w, _ = a.shape
    p = np.pad(a, ((1, 1), (1, 1), (0, 0)), mode="edge")
    B, D, E, F, H = p[:-2, 1:-1], p[1:-1, :-2], p[1:-1, 1:-1], p[1:-1, 2:], p[2:, 1:-1]
    eq = lambda x, y: np.all(x == y, axis=2)
    out = np.zeros((h * 2, w * 2, 4), dtype=a.dtype)
    c = (~eq(B, H)) & (~eq(D, F))
    out[0::2, 0::2] = np.where((c & eq(D, B))[..., None], D, E)
    out[0::2, 1::2] = np.where((c & eq(B, F))[..., None], F, E)
    out[1::2, 0::2] = np.where((c & eq(D, H))[..., None], D, E)
    out[1::2, 1::2] = np.where((c & eq(H, F))[..., None], F, E)
    return out


def upright(sprite):
    """Turns the diagonal sprite 45 degrees so the handle points up, trying both diagonals (most
    sprites hold the handle bottom left, some bottom right) and keeping the one whose lower part is
    the narrow handle. Returns an RGBA array LENGTH * PX texels high."""
    a = np.array(sprite.convert("RGBA"))
    best = None
    for flip in (False, True):
        img = _turn(a[:, ::-1] if flip else a)
        h = img.shape[0]
        low = [r[1] - r[0] for r in (spans(img[j]) for j in range(int(h * 0.6), h)) if r]
        score = sorted(low)[len(low) // 2] if low else 1e9
        if best is None or score < best[0]:
            best = (score, img[:, ::-1] if flip else img)
    return best[1]


def _turn(a):
    big = scale2x(scale2x(a))                             # 4x, smooth diagonals
    ys, xs = np.nonzero(a[..., 3] > 0)
    cx, cy = xs + 0.5, ys + 0.5
    ra = (cx + cy) / math.sqrt(2)                         # across: along the head
    rb = (cx - cy) / math.sqrt(2)                         # up: along the handle
    s = LENGTH * PX / (rb.max() - rb.min())               # texels per sprite pixel
    w = int(math.ceil((ra.max() - ra.min()) * s)) + 2
    h = int(round(LENGTH * PX))
    out = np.zeros((h, w, 4), dtype=np.uint8)
    for j in range(h):
        b = rb.max() - (j + 0.5) / s
        for i in range(w):
            r = ra.min() + (i - 1 + 0.5) / s
            x, y = (r + b) / math.sqrt(2), (r - b) / math.sqrt(2)
            bx, by = int(x * 4), int(y * 4)
            if 0 <= bx < big.shape[1] and 0 <= by < big.shape[0]:
                out[j, i] = big[by, bx]
    out[out[..., 3] < 128] = 0
    out[..., 3] = np.where(out[..., 3] > 0, 255, 0)
    return out


# --- splitting it into handle, collar and head ------------------------------------------

def spans(row):
    xs = np.nonzero(row[:, 3] > 0)[0]
    return (xs.min(), xs.max() + 1) if len(xs) else None


def split(img):
    h, w, _ = img.shape
    rows = [spans(img[j]) for j in range(h)]
    low = [r for r in rows[int(h * 0.62):] if r]
    widths = sorted(r[1] - r[0] for r in low)
    hw = widths[len(widths) // 2]                         # the shaft's usual width
    centre = sorted((r[0] + r[1]) / 2 for r in low)[len(low) // 2]
    left = int(round(centre - hw / 2))
    # the head is the wide block round the widest row; it ends where the rows narrow to the shaft
    width = [r[1] - r[0] if r else 0 for r in rows]
    j = max(range(h), key=lambda k: width[k])
    while j + 1 < h and width[j + 1] > hw + 3:
        j += 1
    return left, hw, j + 1


# --- boxes -------------------------------------------------------------------------------

def rectangles(mask):
    """Greedy rectangles covering a boolean mask: [(x0, y0, x1, y1)] in texels."""
    m = mask.copy()
    out = []
    h, w = m.shape
    for y in range(h):
        x = 0
        while x < w:
            if not m[y, x]:
                x += 1
                continue
            x1 = x
            while x1 < w and m[y, x1]:
                x1 += 1
            y1 = y + 1
            while y1 < h and m[y1, x:x1].all():
                y1 += 1
            m[y:y1, x:x1] = False
            out.append((x, y, x1, y1))
            x = x1
    return out


def fewest(mask):
    by_rows = rectangles(mask)
    by_cols = [(y0, x0, y1, x1) for x0, y0, x1, y1 in rectangles(mask.T)]
    return by_rows if len(by_rows) <= len(by_cols) else by_cols


def coarse(mask, n):
    """Rectangles on an n texel grid, covering only blocks that are wholly inside the mask."""
    h, w = mask.shape
    m = mask[:h - h % n, :w - w % n].reshape(h // n, n, w // n, n).all(axis=(1, 3))
    return [(x0 * n, y0 * n, x1 * n, y1 * n) for x0, y0, x1, y1 in fewest(m)]


def erode(mask, n):
    m = mask.copy()
    for _ in range(n):
        p = np.pad(m, 1)
        m = m & p[:-2, 1:-1] & p[2:, 1:-1] & p[1:-1, :-2] & p[1:-1, 2:]
    return m


def fill_holes(img, rect):
    """Gives every clear texel inside a box's front a colour from its row (or the nearest row),
    so no box shows a hole."""
    x0, y0, x1, y1 = rect
    for y in range(y0, y1):
        for x in range(x0, x1):
            if img[y, x, 3]:
                continue
            for d in range(1, 12):
                for yy, xx in ((y, x - d), (y, x + d), (y - d, x), (y + d, x)):
                    if 0 <= yy < img.shape[0] and 0 <= xx < img.shape[1] and img[yy, xx, 3]:
                        img[y, x] = img[yy, xx]
                        break
                else:
                    continue
                break


def build_boxes(img):
    """Returns (boxes, the front texture). A box is (name, x0, y0, x1, y1, depth in units)."""
    img = img.copy()
    h, w, _ = img.shape
    left, hw, top = split(img)
    boxes = []
    # handle: one box per run of rows with the same width round the shaft's centre
    # A row is a band (cap, collar, wrap) if it stands out 2 px on a side, or 1 px on both sides
    # for at least two rows. A single 1 px step is the staircase the turn leaves on the edges.
    out_l = [left - (spans(img[j]) or (left, 0))[0] for j in range(h)]
    out_r = [(spans(img[j]) or (0, left + hw))[1] - left - hw for j in range(h)]
    both = [out_l[j] >= 1 and out_r[j] >= 1 for j in range(h)]
    band = [max(out_l[j], out_r[j]) >= 2 or (both[j] and ((j > 0 and both[j - 1]) or (j + 1 < h and both[j + 1])))
            for j in range(h)]
    run = None
    for j in range(top, h):
        wide = band[j]
        l0, r0 = (left - 1, left + hw + 1) if wide else (left, left + hw)
        if run and run[0] == l0 and run[1] == r0:
            run[3] = j + 1
        else:
            if run:
                boxes.append(("handle", run[0], run[2], run[1], run[3]))
            run = [l0, r0, j, j + 1]
    if run:
        boxes.append(("handle", run[0], run[2], run[1], run[3]))
    shaft = hw / PX
    out = []
    for k, (n, x0, y0, x1, y1) in enumerate(boxes):
        fill_holes(img, (x0, y0, x1, y1))
        wide = (x1 - x0) > hw
        out.append((("end_cap" if k == len(boxes) - 1 else "band_%d" % k) if wide else "handle_%d" % k,
                    x0, y0, x1, y1, shaft + (0.5 if wide else 0.0)))
    # head: a thin plate over the whole outline, a thick core inside it
    head = img[..., 3] > 0
    head[top:] = False
    for k, r in enumerate(fewest(head)):
        out.append(("head_plate_%d" % k, *r, HEAD_DEPTH[0]))
    for k, r in enumerate(coarse(erode(head, EDGE), 2)):    # inside the outline, so a 2 texel grid is enough
        out.append(("head_core_%d" % k, *r, HEAD_DEPTH[1]))
    # collar: where the head crosses the shaft, one step deeper than the shaft
    cols = head[:, left:left + hw].any(axis=1)
    rows = np.nonzero(cols)[0]
    if len(rows):
        y0, y1 = rows.min(), rows.max() + 1
        mid = [j for j in range(y0, y1) if head[j, left:left + hw].all()]
        if mid:
            out.append(("collar", left - 1, min(mid), left + hw + 1, max(mid) + 1, shaft + 0.75))
            fill_holes(img, (left - 1, min(mid), left + hw + 1, max(mid) + 1))
    return out, img, left + hw / 2, h, top


# --- texture -----------------------------------------------------------------------------

def shade(img, k, warm=0.0):
    """Lightens (k > 0) towards a warm white or darkens (k < 0) towards a cool blue."""
    a = img[..., :3].astype(float)
    if k >= 0:
        target = np.array([255, 244, 214])
        a = a + (target - a) * k
    else:
        target = np.array([24, 22, 46])
        a = a + (target - a) * (-k)
    out = img.copy()
    out[..., :3] = np.clip(a, 8, 247).astype(np.uint8)    # no pure black or white
    return out


def front_paint(img, top):
    """The sprite for the front, with a 1 px highlight along the top edges of the head and
    no pure black or white."""
    out = img.copy()
    a = out[..., 3] > 0
    up = np.pad(a, ((1, 0), (0, 0)))[:-1]
    edge = a & ~up
    edge[top:] = False
    lit = shade(out, 0.18)
    out[edge] = lit[edge]
    out[..., :3] = np.clip(out[..., :3], 8, 247)
    return out


def no_outline(img):
    """The sprite without its dark outline: each edge pixel takes the colour just inside it when that
    is lighter. Used for the tops, bottoms and sides, where the box itself now draws the edge."""
    out = img.copy()
    a = img[..., 3] > 0
    inner = erode(a, 1)
    luma = img[..., :3].astype(float) @ np.array([0.3, 0.59, 0.11])
    h, w = a.shape
    for y, x in zip(*np.nonzero(a & ~inner)):
        best = None
        for dy, dx in ((0, 1), (0, -1), (1, 0), (-1, 0), (1, 1), (1, -1), (-1, 1), (-1, -1)):
            for step in (1, 2):
                yy, xx = y + dy * step, x + dx * step
                if 0 <= yy < h and 0 <= xx < w and inner[yy, xx] and luma[yy, xx] > luma[y, x] + 18:
                    if best is None or luma[yy, xx] > luma[best]:
                        best = (yy, xx)
                    break
        if best:
            out[y, x] = img[best]
    return out


PANELS = ["front", "up", "down", "west", "east"]   # left to right, top to bottom in the atlas


def atlas(img, top):
    h, w, _ = img.shape
    slot_w, slot_h = w, h
    per_row = ATLAS // slot_w
    assert per_row * (ATLAS // slot_h) >= len(PANELS), "sprite too big for the atlas"
    flat = no_outline(img)
    variants = {"front": front_paint(img, top), "up": shade(flat, 0.22), "down": shade(flat, -0.45),
                "west": shade(flat, -0.10), "east": shade(flat, -0.28)}
    sheet = np.zeros((ATLAS, ATLAS, 4), dtype=np.uint8)
    offset = {}
    for k, name in enumerate(PANELS):
        ox, oy = (k % per_row) * slot_w, (k // per_row) * slot_h
        sheet[oy:oy + h, ox:ox + w] = variants[name]
        offset[name] = (ox, oy)
    return Image.fromarray(sheet, "RGBA"), offset


# --- Blockbench file ---------------------------------------------------------------------

def uid():
    return str(uuid.uuid4())


def cube(name, frm, to, faces, origin):
    return {"name": name, "box_uv": False, "render_order": "default", "locked": False, "export": True,
            "scope": 0, "allow_mirror_modeling": True, "from": frm, "to": to, "autouv": 0, "color": 0,
            "origin": origin, "faces": faces, "type": "cube", "uuid": uid()}


def faces_for(x0, y0, x1, y1, off, tex):
    fo, up, dn, we, ea = (off[p] for p in PANELS)
    f = lambda o, a, b, c, d: [o[0] + a, o[1] + b, o[0] + c, o[1] + d]
    return {
        "south": {"uv": f(fo, x0, y0, x1, y1), "texture": tex},
        "north": {"uv": f(fo, x1, y0, x0, y1), "texture": tex},
        "up": {"uv": f(up, x0, y0, x1, y0 + 1), "texture": tex},
        "down": {"uv": f(dn, x0, y1 - 1, x1, y1), "texture": tex},
        "west": {"uv": f(we, x0, y0, x0 + 1, y1), "texture": tex},
        "east": {"uv": f(ea, x1 - 1, y0, x1, y1), "texture": tex},
    }


def model_parts(sprite_path, tex_index=0, shift=0.0):
    img = upright(Image.open(sprite_path))
    boxes, img, centre, h, top = build_boxes(img)
    sheet, off = atlas(img, top)
    elements = []
    for name, x0, y0, x1, y1, depth in boxes:
        x0, y0, x1, y1, depth, centre = int(x0), int(y0), int(x1), int(y1), float(depth), float(centre)
        frm = [round((x0 - centre) / PX + shift, 4), round((h - y1) / PX, 4), -depth / 2]
        to = [round((x1 - centre) / PX + shift, 4), round((h - y0) / PX, 4), depth / 2]
        elements.append(cube(name, frm, to, faces_for(x0, y0, x1, y1, off, tex_index), [shift, GRIP, 0]))
    return elements, sheet


def texture_entry(name, sheet, index):
    buf = io.BytesIO()
    sheet.save(buf, "PNG")
    return {"name": name + ".png", "path": "", "folder": "", "namespace": "", "id": str(index), "group": "",
            "scope": 0, "width": ATLAS, "height": ATLAS, "uv_width": ATLAS, "uv_height": ATLAS,
            "particle": False, "use_as_default": False, "layers_enabled": False, "sync_to_project": "",
            "file_format": "png", "render_mode": "default", "render_sides": "auto", "wrap_mode": "limited",
            "pbr_channel": "color", "fps": 7, "force_translucent": False, "frame_time": 1,
            "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False, "visible": True,
            "internal": True, "saved": True, "uuid": uid(),
            "source": "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()}


def group(name, origin, children):
    g = {"name": name, "uuid": uid(), "export": True, "locked": False, "scope": 0, "selected": False,
         "visibility": True, "origin": origin, "rotation": [0, 0, 0], "color": 0, "children": [],
         "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": True,
         "primary_selected": False}
    return g, {"uuid": g["uuid"], "isOpen": True, "children": children}


def scale_dummy(x):
    blank = {f: {"uv": [0, 0, 0, 0], "texture": None} for f in ("north", "east", "south", "west", "up", "down")}
    d = cube("scale_dummy_imp", [x - 2, 0, -2], [x + 2, 18.5, 2], blank, [x, 0, 0])
    d["export"] = False
    d["visibility"] = False
    g, o = group("scale_dummy", [x, 0, 0], [d["uuid"]])
    g["export"] = False
    g["visibility"] = False
    return d, g, o


def bbmodel(name, elements, groups, outliner, textures, size):
    return {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
            "name": name, "model_identifier": "", "visible_box": [1, 1, 0], "variable_placeholders": "",
            "variable_placeholder_buttons": [], "timeline_setups": [], "unhandled_root_fields": {},
            "resolution": {"width": size, "height": size}, "elements": elements, "groups": groups,
            "outliner": outliner, "textures": textures}


def main():
    OUT_MODELS.mkdir(parents=True, exist_ok=True)
    OUT_TEX.mkdir(parents=True, exist_ok=True)
    sprites = sorted(SPRITES.glob("*_pickaxe.png"))
    lineup_el, lineup_groups, lineup_out, lineup_tex = [], [], [], []
    for k, path in enumerate(sprites):
        name = path.stem                                   # e.g. iron_pickaxe
        elements, sheet = model_parts(path)
        sheet.save(OUT_TEX / (name + ".png"))
        g, o = group(name, [0, GRIP, 0], [e["uuid"] for e in elements])
        d, dg, do = scale_dummy(12)
        doc = bbmodel(name, elements + [d], [g, dg], [o, do], [texture_entry(name, sheet, 0)], ATLAS)
        (OUT_MODELS / (name + ".bbmodel")).write_text(json.dumps(doc), encoding="utf-8")
        # the same pickaxe again, moved along X and pointing at its own texture, for the lineup
        row = k // 6                                       # two rows, so one view shows them all large
        x = (k % 6 - 2.5) * SPACING
        moved, _ = model_parts(path, tex_index=k, shift=x)
        for e in moved:
            e["from"][1] += (1 - row) * 24
            e["to"][1] += (1 - row) * 24
            e["origin"][1] += (1 - row) * 24
        lineup_el += moved
        lg, lo = group(name, [x, GRIP + (1 - row) * 24, 0], [e["uuid"] for e in moved])
        lineup_groups.append(lg)
        lineup_out.append(lo)
        lineup_tex.append(texture_entry(name, sheet, k))
        print("%-22s %3d boxes" % (name, len(elements)))
    d, dg, do = scale_dummy(-3.5 * SPACING)
    doc = bbmodel("pickaxes_lineup", lineup_el + [d], lineup_groups + [dg], lineup_out + [do], lineup_tex, ATLAS)
    (OUT_MODELS / "pickaxes_lineup.bbmodel").write_text(json.dumps(doc), encoding="utf-8")
    print("lineup: %d pickaxes" % len(sprites))


if __name__ == "__main__":
    main()
