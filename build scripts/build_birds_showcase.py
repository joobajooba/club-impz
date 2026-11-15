"""birds_showcase: all the birds, smallest first in one row, one root group and one texture each."""
import json, copy, uuid, random
T = r"C:/Users/lucas/blockbench_models/mobs/birds"
rng = random.Random(10)
def nu(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))
kinds = ["robin", "pigeon", "crow", "duck", "seagull", "owl", "snowy_owl", "swan", "eagle", "heron"]
out = None; x = 0; gap = 8
for ti, k in enumerate(kinds):
    d = json.load(open(rf"{T}\{k}.bbmodel", encoding="utf8"))
    xs = [v for e in d["elements"] for v in (e["from"][0], e["to"][0])]
    half = max(abs(min(xs)), max(xs))
    x += half if ti else 0
    if out is None:
        out = copy.deepcopy(d); out["name"] = "birds_showcase"; out["elements"] = []; out["groups"] = []; out["outliner"] = []; out["textures"] = []
    for e in d["elements"]:
        e["from"][0] += x; e["to"][0] += x; e["origin"][0] += x
        for f in e["faces"].values():
            if f.get("texture") is not None: f["texture"] = ti
        out["elements"].append(e)
    for g in d["groups"]:
        g["origin"][0] += x; out["groups"].append(g)
    out["outliner"] += d["outliner"]
    t = d["textures"][0]; t["id"] = str(ti); t["uuid"] = nu(); out["textures"].append(t)
    x += half + gap
json.dump(out, open(rf"{T}\birds_showcase.bbmodel", "w", encoding="utf8"), indent="\t")
print("elements", len(out["elements"]), "width", x)
