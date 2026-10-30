"""Puts several Blockbench models side by side in one file, each with its own texture.
python make_lineup.py <out.bbmodel> <spacing> <per_row> <model.bbmodel>..."""
import json
import sys
import uuid


def main():
    out, spacing, per_row, paths = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4:]
    doc = None
    elements, groups, outliner, textures = [], [], [], []
    rows = (len(paths) + per_row - 1) // per_row
    for k, p in enumerate(paths):
        m = json.load(open(p, encoding="utf-8"))
        doc = doc or m
        dx = (k % per_row - (per_row - 1) / 2) * spacing
        dy = (rows - 1 - k // per_row) * spacing * 1.1
        ti = len(textures)
        for t in m["textures"]:
            t = dict(t, uuid=str(uuid.uuid4()), id=str(len(textures)))
            textures.append(t)
        ids = []
        for e in m["elements"]:
            if not e.get("export", True):
                continue
            e = json.loads(json.dumps(e))
            e["uuid"] = str(uuid.uuid4())
            e["from"] = [e["from"][0] + dx, e["from"][1] + dy, e["from"][2]]
            e["to"] = [e["to"][0] + dx, e["to"][1] + dy, e["to"][2]]
            e["origin"] = [e["origin"][0] + dx, e["origin"][1] + dy, e["origin"][2]]
            for f in e.get("faces", {}).values():
                if f.get("texture") is not None:
                    f["texture"] += ti
            elements.append(e)
            ids.append(e["uuid"])
        name = p.replace("\\", "/").split("/")[-1][:-8]
        g = {"name": name, "uuid": str(uuid.uuid4()), "export": True, "locked": False, "scope": 0, "selected": False,
             "visibility": True, "origin": [dx, dy, 0], "rotation": [0, 0, 0], "color": 0, "children": [],
             "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": False}
        groups.append(g)
        outliner.append({"uuid": g["uuid"], "isOpen": False, "children": ids})
    res = max(t.get("uv_width", 64) for t in textures)
    lineup = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False},
              "name": out.replace("\\", "/").split("/")[-1][:-8], "model_identifier": "", "visible_box": [1, 1, 0],
              "variable_placeholders": "", "variable_placeholder_buttons": [], "timeline_setups": [],
              "unhandled_root_fields": {}, "resolution": {"width": res, "height": res}, "elements": elements,
              "groups": groups, "outliner": outliner, "textures": textures}
    json.dump(lineup, open(out, "w", encoding="utf-8"))
    print(out, len(paths), "models,", len(elements), "boxes")


if __name__ == "__main__":
    main()
