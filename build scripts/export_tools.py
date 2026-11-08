"""Copies the held tools from C:\\Users\\lucas\\blockbench_models\\tools into the game.

- .bbmodel sources -> godot-game/assets/models/tools/ (swords: assets/models/weapons/), as the doc's folders say
- textures         -> godot-game/assets/textures/tools/ (swords: textures/weapons/)
- slim models      -> godot-game/data/tools/models/<id>.json (same format ImpBuilder reads), plus
                      data/tools/manifest.json: id -> {model, texture, grip, kind}
- sword icons      -> godot-game/sprites/items/tool_<metal>_sword.png, rendered from the models (there are no
                      sword sprites), 48 x 48 like the other tool icons

Run after rebuilding any tool (build_pickaxes.py, build_axes.py, build_more_tools.py).
"""
import json, shutil, sys
from pathlib import Path
import numpy as np
from PIL import Image

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import render_bb as rb  # noqa: E402

SRC = Path(r"C:\Users\lucas\blockbench_models\tools")
GAME = HERE.parent / "godot-game"
METALS = "stone bronze iron steel gold obsidian titanite dreadstone void stellarite".split()
WOODS = "driftwood ash birch oak pine goldleaf ebony silverbark bloodwood voidwood".split()
KEEP = ("name", "from", "to", "origin", "rotation", "stretch", "faces")


def slim(model):
    elements = [{k: e[k] for k in KEEP if k in e} for e in model["elements"]]
    for e in elements:
        e["faces"] = {f: {"uv": fc["uv"]} for f, fc in e["faces"].items() if fc.get("texture") is not None}
    groups = {g["uuid"]: {"name": g["name"], "origin": g["origin"], "rotation": g.get("rotation", [0, 0, 0])}
              for g in model["groups"]}
    index = {e["uuid"]: i for i, e in enumerate(model["elements"])}

    def tree(n):
        if isinstance(n, str):
            return index[n]
        return {**groups[n["uuid"]], "children": [tree(k) for k in n["children"]]}
    t = model["textures"][0]
    return {"texture": [t["uv_width"], t["uv_height"]], "elements": elements, "bones": [tree(n) for n in model["outliner"]]}


def sword_icon(model, out):
    """Front view, turned so the tip points up and right like the other tool icons, with a dark outline."""
    tex = rb.load_tex(model)
    im = rb.render(model, tex, np.eye(3), ppu=8, bounds=(-5, 5, -1, 17))
    a = np.array(im).astype(int)
    mask = (np.abs(a - np.array([40, 42, 48])).sum(-1) > 6)
    rgba = np.dstack([a, mask * 255]).astype(np.uint8)
    img = Image.fromarray(rgba, "RGBA").rotate(-45, resample=Image.NEAREST, expand=True)
    img = img.crop(img.getbbox())
    s = 44 / max(img.size)
    img = img.resize((max(1, round(img.width * s)), max(1, round(img.height * s))), Image.NEAREST)
    can = Image.new("RGBA", (48, 48), (0, 0, 0, 0))
    can.alpha_composite(img, ((48 - img.width) // 2, (48 - img.height) // 2))
    arr = np.array(can)
    al = arr[..., 3] > 0
    ring = np.zeros_like(al)
    for dx, dy in ((1, 0), (-1, 0), (0, 1), (0, -1)):
        ring |= np.roll(np.roll(al, dy, 0), dx, 1)
    ring &= ~al
    arr[ring] = (11, 12, 16, 255)
    Image.fromarray(arr, "RGBA").save(out)


def main():
    items = [(f"{m}_{k}", k) for k in ("pickaxe", "axe", "sickle", "sword") for m in METALS] + [(f"{w}_rod", "rod") for w in WOODS]
    (GAME / "data/tools/models").mkdir(parents=True, exist_ok=True)
    manifest = {}
    for tid, kind in items:
        src = SRC / f"{tid}.bbmodel"
        model = json.loads(src.read_text(encoding="utf8"))
        group = "weapons" if kind == "sword" else "tools"
        mdir, tdir = GAME / "assets/models" / group, GAME / "assets/textures" / group
        mdir.mkdir(parents=True, exist_ok=True); tdir.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(src, mdir / src.name)
        shutil.copyfile(SRC / f"{tid}.png", tdir / f"{tid}.png")
        (GAME / f"data/tools/models/{tid}.json").write_text(json.dumps(slim(model), separators=(",", ":")), encoding="utf8")
        root = next(g for g in model["groups"] if g["uuid"] == model["outliner"][0]["uuid"])
        manifest[tid] = {"kind": kind, "model": f"res://data/tools/models/{tid}.json",
                         "texture": f"res://assets/textures/{group}/{tid}.png", "grip": root["origin"]}
        if kind == "sword":
            sword_icon(model, GAME / f"sprites/items/tool_{tid}.png")
    (GAME / "data/tools/manifest.json").write_text(json.dumps(manifest, indent=1), encoding="utf8")
    print(len(manifest), "tools exported")


if __name__ == "__main__":
    main()
