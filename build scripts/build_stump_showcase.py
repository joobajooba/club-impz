"""stumps_showcase: all five stumps in a row, one root group each, one texture each."""
import json, copy, uuid, random
T = r"C:\Users\lucas\blockbench_models\trees"
rng = random.Random(9)
def nu(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))
kinds = ["birch", "pine", "maple", "frostbark", "oak"]
out = None; x = 0; gap = 14
for ti, k in enumerate(kinds):
    d = json.load(open(rf"{T}\{k}_stump.bbmodel", encoding="utf8"))
    xs = [v for e in d["elements"] for v in (e["from"][0], e["to"][0])]
    half = max(abs(min(xs)), max(xs))
    x += half if ti else 0
    if out is None:
        out = copy.deepcopy(d); out["name"] = "stumps_showcase"; out["elements"] = []; out["groups"] = []; out["outliner"] = []; out["textures"] = []
    for e in d["elements"]:
        e["from"][0] += x; e["to"][0] += x; e["origin"][0] += x
        for f in e["faces"].values():
            if f.get("texture") is not None: f["texture"] = ti
        out["elements"].append(e)
    for g in d["groups"]:
        g["origin"][0] += x; out["groups"].append(g)
    out["outliner"] += d["outliner"]
    t = d["textures"][0]; t["id"] = str(ti); t["uuid"] = nu(); out["textures"].append(t)
    out["resolution"] = {"width": max(out["resolution"]["width"], t["width"]), "height": max(out["resolution"]["height"], t["height"])}
    x += half + gap
json.dump(out, open(rf"{T}\stumps_showcase.bbmodel", "w", encoding="utf8"), indent="\t")
print("elements", len(out["elements"]))
