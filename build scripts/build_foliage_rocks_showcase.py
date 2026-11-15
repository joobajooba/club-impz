"""rocks_showcase: every biome's rocks, one row per biome (small, medium, large), one texture per biome."""
import json, copy, uuid, random
T = r"C:\Users\lucas\blockbench_models\rocks"
rng = random.Random(11)
def nu(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))
biomes = ["forest", "mountain", "frost", "plains", "swamp"]
xs = {"small": 0.0, "medium": 18.0, "large": 50.0}
out = None
for ti, b in enumerate(biomes):
    z = ti * 40.0
    for s in ["small", "medium", "large"]:
        d = json.load(open(rf"{T}\{b}_rock_{s}.bbmodel", encoding="utf8"))
        if out is None:
            out = copy.deepcopy(d); out["name"] = "rocks_showcase"
            for k in ("elements", "groups", "outliner", "textures"): out[k] = []
        if s == "small":
            t = d["textures"][0]; t["id"] = str(ti); t["uuid"] = nu(); out["textures"].append(t)
        for e in d["elements"]:
            for k in ("from", "to", "origin"):
                e[k][0] += xs[s]; e[k][2] += z
            for f in e["faces"].values():
                if f.get("texture") is not None: f["texture"] = ti
            out["elements"].append(e)
        for g in d["groups"]:
            g["origin"][0] += xs[s]; g["origin"][2] += z; out["groups"].append(g)
        out["outliner"] += d["outliner"]
json.dump(out, open(rf"{T}\rocks_showcase.bbmodel", "w", encoding="utf8"), indent="\t")
print("elements", len(out["elements"]), "textures", len(out["textures"]))
