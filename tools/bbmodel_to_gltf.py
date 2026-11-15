"""Convert Blockbench .bbmodel files (format 5.0, "free", per-face UV) into .glb files Godot can import.

Usage:
    python3 tools/bbmodel_to_gltf.py                      # every .bbmodel under godot-game/assets/models/
    python3 tools/bbmodel_to_gltf.py path/a.bbmodel ...   # just these

What it does (see docs/world_build_notes.md):
- Every element is a cube: `from`, `to`, `origin` (pivot) and `rotation` in degrees. Blockbench applies X, then Y,
  then Z, so the matrix is Rz * Ry * Rx. Group transforms (origin + rotation) from the outliner are applied down the
  hierarchy on top of that.
- Faces north / east / south / west / up / down; faces whose texture is null are skipped. Face UVs are in texture
  pixels (the texture's uv_width / uv_height, or the project resolution) and honour the face `rotation`.
  glTF's UV origin is the top-left of the image, the same as Blockbench's, so V is NOT flipped.
- Zero thickness cubes are alpha cards (leaves, blades, banners): they go in a double sided "card" material.
- Cubes named *_glow get an emissive material (game_worlds.md section 4.9).
- 16 Blockbench units = 1 metre; the model keeps standing on y = 0.
- Elements with export false (the scale_dummy) and animations are skipped.
- Textures are embedded as PNG with a nearest-neighbour sampler, alpha mode MASK (hard alpha) where the texture has
  transparency.
"""
import base64, io, json, math, struct, sys
from pathlib import Path

import numpy as np
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MODELS = ROOT / "godot-game" / "assets" / "models"
TEXTURES = ROOT / "godot-game" / "assets" / "textures"
SCALE = 1.0 / 16.0


def rx(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[1, 0, 0], [0, c, -s], [0, s, c]])


def ry(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, 0, s], [0, 1, 0], [-s, 0, c]])


def rz(a):
    a = math.radians(a); c, s = math.cos(a), math.sin(a)
    return np.array([[c, -s, 0], [s, c, 0], [0, 0, 1]])


def euler(r):
    r = r or [0, 0, 0]
    return rz(r[2]) @ ry(r[1]) @ rx(r[0])


# face corners in order top-left, top-right, bottom-right, bottom-left as seen from outside the cube
def corners(f, t, face):
    x1, y1, z1 = f; x2, y2, z2 = t
    return {"north": [(x2, y2, z1), (x1, y2, z1), (x1, y1, z1), (x2, y1, z1)],
            "south": [(x1, y2, z2), (x2, y2, z2), (x2, y1, z2), (x1, y1, z2)],
            "east":  [(x2, y2, z2), (x2, y2, z1), (x2, y1, z1), (x2, y1, z2)],
            "west":  [(x1, y2, z1), (x1, y2, z2), (x1, y1, z2), (x1, y1, z1)],
            "up":    [(x1, y2, z1), (x2, y2, z1), (x2, y2, z2), (x1, y2, z2)],
            "down":  [(x1, y1, z2), (x2, y1, z2), (x2, y1, z1), (x1, y1, z1)]}[face]


def load_textures(model, path):
    texs = []
    for i, t in enumerate(model.get("textures", [])):
        img = None
        src = t.get("source", "")
        if src.startswith("data:image"):
            img = Image.open(io.BytesIO(base64.b64decode(src.split(",", 1)[1]))).convert("RGBA")
        else:
            cand = list(TEXTURES.rglob(t.get("name", f"{path.stem}.png")))
            if cand:
                img = Image.open(cand[0]).convert("RGBA")
        if img is None:
            raise SystemExit(f"{path}: texture {i} has no embedded source and no PNG in {TEXTURES}")
        res = model.get("resolution", {"width": img.width, "height": img.height})
        uw = t.get("uv_width") or res["width"]
        uh = t.get("uv_height") or res["height"]
        texs.append({"img": img, "uw": uw, "uh": uh, "alpha": bool((np.array(img)[..., 3] < 255).any())})
    return texs


def element_parents(model):
    """uuid of element -> list of groups from the innermost outwards."""
    groups = {g["uuid"]: g for g in model.get("groups", [])}
    parents = {}

    def walk(node, chain):
        if isinstance(node, str):
            parents[node] = list(reversed(chain)); return
        g = groups.get(node["uuid"], node)
        for ch in node.get("children", []):
            walk(ch, chain + [g])
    for n in model.get("outliner", []):
        walk(n, [])
    return parents


def convert(path: Path):
    model = json.loads(path.read_text())
    texs = load_textures(model, path)
    parents = element_parents(model)
    prims = {}  # (texture index, kind) -> lists
    for e in model["elements"]:
        if e.get("type", "cube") != "cube" or e.get("export", True) is False:
            continue
        f, t = e["from"], e["to"]
        card = any(abs(t[i] - f[i]) < 1e-6 for i in range(3))
        kind = "glow" if e["name"].endswith("_glow") else ("card" if card else "solid")
        R = euler(e.get("rotation")); o = np.array(e.get("origin", [0, 0, 0]), float)
        chain = parents.get(e["uuid"], [])
        for face, fd in e["faces"].items():
            ti = fd.get("texture")
            if ti is None:
                continue
            P = np.array(corners(f, t, face), float)
            P = (R @ (P - o).T).T + o
            for g in chain:
                if any(abs(v) > 1e-9 for v in g.get("rotation", [0, 0, 0])):
                    go = np.array(g.get("origin", [0, 0, 0]), float)
                    P = (euler(g["rotation"]) @ (P - go).T).T + go
            if card:  # a zero thickness card has two coincident faces; keep only one per card axis
                if face in ("south", "west", "down") and fd2_present(e, face):
                    continue
            n = np.cross(P[3] - P[0], P[1] - P[0])  # outward normal
            ln = np.linalg.norm(n)
            if ln < 1e-12:
                continue
            n /= ln
            tex = texs[int(ti)]
            u1, v1, u2, v2 = fd["uv"]
            uv = [(u1, v1), (u2, v1), (u2, v2), (u1, v2)]
            for _ in range(int(fd.get("rotation", 0)) // 90):
                uv = [uv[3], uv[0], uv[1], uv[2]]
            uv = [(a / tex["uw"], b / tex["uh"]) for a, b in uv]
            d = prims.setdefault((int(ti), kind), {"p": [], "n": [], "uv": [], "i": []})
            base = len(d["p"])
            for k in range(4):
                d["p"].append(P[k] * SCALE); d["n"].append(n); d["uv"].append(uv[k])
            d["i"] += [base, base + 3, base + 2, base, base + 2, base + 1]  # counter clockwise seen from outside
    if not prims:
        print(f"skip {path.name}: nothing to export"); return
    write_glb(path.with_suffix(".glb"), path.stem, prims, texs)
    tris = sum(len(d["i"]) // 3 for d in prims.values())
    print(f"{path.relative_to(ROOT)} -> .glb  ({tris} triangles, {len(prims)} primitives)")


def fd2_present(e, face):
    opp = {"south": "north", "west": "east", "down": "up"}[face]
    return e["faces"].get(opp, {}).get("texture") is not None


def write_glb(out: Path, name, prims, texs):
    bin_ = bytearray(); views, accessors, meshes_prims, materials, images, textures = [], [], [], [], [], []

    def add_view(data: bytes, target=None):
        while len(bin_) % 4: bin_.append(0)
        off = len(bin_); bin_.extend(data)
        v = {"buffer": 0, "byteOffset": off, "byteLength": len(data)}
        if target: v["target"] = target
        views.append(v); return len(views) - 1

    tex_index = {}
    for i, tx in enumerate(texs):
        buf = io.BytesIO(); tx["img"].save(buf, "PNG")
        images.append({"bufferView": add_view(buf.getvalue()), "mimeType": "image/png", "name": f"{name}_{i}"})
        textures.append({"sampler": 0, "source": len(images) - 1}); tex_index[i] = len(textures) - 1
    mat_index = {}
    for (ti, kind) in sorted(prims):
        m = {"name": f"{name}_{kind}_{ti}",
             "pbrMetallicRoughness": {"baseColorTexture": {"index": tex_index[ti]}, "metallicFactor": 0.0, "roughnessFactor": 1.0}}
        if kind == "card" or texs[ti]["alpha"]:
            m["alphaMode"] = "MASK"; m["alphaCutoff"] = 0.5
        if kind == "card":
            m["doubleSided"] = True
        if kind == "glow":
            m["emissiveTexture"] = {"index": tex_index[ti]}; m["emissiveFactor"] = [1.0, 1.0, 1.0]
        materials.append(m); mat_index[(ti, kind)] = len(materials) - 1
    for key, d in sorted(prims.items()):
        p = np.array(d["p"], np.float32); n = np.array(d["n"], np.float32); uv = np.array(d["uv"], np.float32)
        idx = np.array(d["i"], np.uint32)
        acc = {}
        for nm, arr, typ in (("POSITION", p, "VEC3"), ("NORMAL", n, "VEC3"), ("TEXCOORD_0", uv, "VEC2")):
            a = {"bufferView": add_view(arr.tobytes(), 34962), "componentType": 5126, "count": len(arr), "type": typ}
            if nm == "POSITION": a["min"] = p.min(0).tolist(); a["max"] = p.max(0).tolist()
            accessors.append(a); acc[nm] = len(accessors) - 1
        accessors.append({"bufferView": add_view(idx.tobytes(), 34963), "componentType": 5125, "count": len(idx), "type": "SCALAR"})
        meshes_prims.append({"attributes": acc, "indices": len(accessors) - 1, "material": mat_index[key]})
    gltf = {"asset": {"version": "2.0", "generator": "club-impz bbmodel_to_gltf.py"},
            "scene": 0, "scenes": [{"nodes": [0]}], "nodes": [{"name": name, "mesh": 0}],
            "meshes": [{"name": name, "primitives": meshes_prims}], "materials": materials,
            "textures": textures, "images": images,
            "samplers": [{"magFilter": 9728, "minFilter": 9984, "wrapS": 33071, "wrapT": 33071}],
            "buffers": [{"byteLength": len(bin_)}], "bufferViews": views, "accessors": accessors}
    js = json.dumps(gltf, separators=(",", ":")).encode()
    while len(js) % 4: js += b" "
    while len(bin_) % 4: bin_.append(0)
    with open(out, "wb") as fh:
        fh.write(struct.pack("<III", 0x46546C67, 2, 12 + 8 + len(js) + 8 + len(bin_)))
        fh.write(struct.pack("<II", len(js), 0x4E4F534A)); fh.write(js)
        fh.write(struct.pack("<II", len(bin_), 0x004E4942)); fh.write(bin_)


if __name__ == "__main__":
    paths = [Path(a) for a in sys.argv[1:]] or sorted(MODELS.rglob("*.bbmodel"))
    for p in paths:
        convert(p.resolve())
