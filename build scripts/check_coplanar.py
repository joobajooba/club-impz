"""Find z-fighting faces in Blockbench models (J00BA, 2026-11-09: the cauldron's striped brew was two faces in one
plane). For every pair of visible faces (a texture, not hidden) on unrotated cubes (no rotation on the cube or any
group above it) that lie in the same plane, face the same way and overlap by more than 0.01 units in both
directions, it reports the pair: the GPU draws both and switches between them pixel by pixel.

  --opposite   also list touching faces that face each other in the same plane (the game draws both sides of every
               face, so these can flicker too where both are visible; most are hidden inside the model)

Usage: py "build scripts/check_coplanar.py" <file.bbmodel | folder> [...] [--opposite]"""
import glob, json, os, sys

AX = {"east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1), "south": (2, 1), "north": (2, -1)}


def faces(path):
    d = json.load(open(path, encoding="utf8"))
    grp = {g["uuid"]: g for g in d.get("groups", [])}
    rotated_groups = set()

    def walk(nodes, rotated):
        for c in nodes:
            if isinstance(c, str):
                if rotated:
                    rotated_groups.add(c)
            else:
                g = grp.get(c["uuid"], {})
                walk(c.get("children", []), rotated or any(abs(v) > 1e-6 for v in g.get("rotation", [0, 0, 0])))
    walk(d.get("outliner", []), False)
    out = []
    for e in d["elements"]:
        if e.get("type", "cube") != "cube" or not e.get("export", True) or e.get("visibility") is False:
            continue
        if any(abs(v) > 1e-6 for v in e.get("rotation", [0, 0, 0])) or e["uuid"] in rotated_groups:
            continue
        a, b = e["from"], e["to"]
        for f, (ax, sgn) in AX.items():
            fd = e["faces"].get(f)
            if not fd or fd.get("texture") is None:
                continue
            plane = b[ax] if sgn > 0 else a[ax]
            o = [i for i in range(3) if i != ax]
            out.append({"cube": e["name"], "face": f, "ax": ax, "sgn": sgn, "plane": plane,
                        "r": (a[o[0]], b[o[0]], a[o[1]], b[o[1]])})
    return out


def check(path, opposite=False):
    F = faces(path)
    same, opp = [], []
    by = {}
    for f in F:
        by.setdefault((f["ax"], round(f["plane"], 4)), []).append(f)
    for fs in by.values():
        for i in range(len(fs)):
            for j in range(i + 1, len(fs)):
                p, q = fs[i], fs[j]
                ox = min(p["r"][1], q["r"][1]) - max(p["r"][0], q["r"][0])
                oy = min(p["r"][3], q["r"][3]) - max(p["r"][2], q["r"][2])
                if ox > 0.01 and oy > 0.01:
                    if p["sgn"] == q["sgn"]:
                        same.append((p, q, ox, oy))
                    elif p["cube"] != q["cube"]:          # a zero-thickness card against itself is fine
                        opp.append((p, q, ox, oy))
    return same, opp


def main():
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    opposite = "--opposite" in sys.argv
    files = []
    for a in args:
        files += sorted(glob.glob(os.path.join(a, "**", "*.bbmodel"), recursive=True)) if os.path.isdir(a) else [a]
    total, flagged = 0, []
    for path in files:
        same, opp = check(path, opposite)
        if same or (opposite and opp):
            flagged.append((path, len(same), len(opp)))
        name = os.path.relpath(path)
        if same:
            print(f"{name}: {len(same)} same-facing coplanar overlaps")
            for p, q, ox, oy in same:
                print(f"   {p['cube']} {p['face']} / {q['cube']} {q['face']} at {'xyz'[p['ax']]} = {p['plane']} ({ox:g} x {oy:g})")
        if opposite and opp:
            print(f"{name}: {len(opp)} facing-each-other touching faces")
            for p, q, ox, oy in opp:
                print(f"   {p['cube']} {p['face']} / {q['cube']} {q['face']} at {'xyz'[p['ax']]} = {p['plane']} ({ox:g} x {oy:g})")
        total += len(same)
    print(f"\n{len(files)} models, {total} same-facing coplanar overlaps in {sum(1 for f in flagged if f[1])} models")
    return total


if __name__ == "__main__":
    sys.exit(1 if main() else 0)
