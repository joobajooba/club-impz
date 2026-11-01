"""Analyse tree .bbmodel files for stray blocks on the trunk and branches, and optionally remove them.

Usage:
    python3 tools/clean_tree_trunks.py                       # analyse every tree under godot-game/assets/models/trees/
    python3 tools/clean_tree_trunks.py path/a.bbmodel ...    # analyse just these
    python3 tools/clean_tree_trunks.py --fix [paths ...]     # remove leaf core blocks, then re-export with bbmodel_to_gltf.py

The rule (docs/blockbench_detailed_prompts.md section 3.1, "Clean trunks and branches"): a tree has no solid leaf
core cubes. J00BA's hand fixed frostbark_tree.bbmodel is the reference: the trunk is only stacked `trunk_*` sections
plus flush `bark_strip_*` cubes, and the canopy is only thin alpha cards. Solid `*_core*` cubes end up wrapped round
the trunk like random blocks, so they are removed.

The report lists, per model:
- core:     leaf core cubes (any cube whose name ends in `core` or `core_<n>`). --fix deletes these.
- wraps:    any other solid (thicker than 0.6) cube that the trunk or a branch runs through. Check these by hand.
- floating: branch cubes where neither end touches the trunk or another branch. Check these by hand.
- step:     trunk sections that leave a gap or stick out past the section below. Check these by hand.
"""
import json, math, re, sys
from pathlib import Path

import numpy as np

ROOT = Path(__file__).resolve().parents[1]
TREES = ROOT / "godot-game" / "assets" / "models" / "trees"

WOOD = ("trunk", "limb", "side_branch", "branch", "stub_branch", "leader")
SMALL_DETAILS = ("root", "bark", "stone", "fallen", "acorn", "mushroom", "pine_cone", "needle", "frostbark_cone",
                 "snow_drift", "ice_crystal", "bracket", "moss")
CORE = re.compile(r"(^|_)core(_\d+)?$")


def rot(r):
    if not r:
        return np.eye(3)
    x, y, z = (math.radians(a) for a in r)
    rx = np.array([[1, 0, 0], [0, math.cos(x), -math.sin(x)], [0, math.sin(x), math.cos(x)]])
    ry = np.array([[math.cos(y), 0, math.sin(y)], [0, 1, 0], [-math.sin(y), 0, math.cos(y)]])
    rz = np.array([[math.cos(z), -math.sin(z), 0], [math.sin(z), math.cos(z), 0], [0, 0, 1]])
    return rz @ ry @ rx  # Blockbench applies X, then Y, then Z


def box(e):
    return np.array(e["from"], float), np.array(e["to"], float), np.array(e.get("origin", [0, 0, 0]), float)


def axis_ends(e):
    """World positions of the two ends of a cube's longest axis."""
    f, t, o = box(e)
    a = int(np.argmax(t - f))
    p0, p1 = (f + t) / 2, (f + t) / 2
    p0[a], p1[a] = f[a], t[a]
    m = rot(e.get("rotation"))
    return m @ (p0 - o) + o, m @ (p1 - o) + o


def inside(p, e, tol=0.0):
    f, t, o = box(e)
    q = rot(e.get("rotation")).T @ (p - o) + o
    return all(f[i] - tol <= q[i] <= t[i] + tol for i in range(3))


def runs_through(w, e):
    a, b = axis_ends(w)
    return any(inside(a + (b - a) * s, e) for s in np.linspace(0, 1, 25))


def analyse(d):
    els = d["elements"]
    wood = [e for e in els if e["name"].startswith(WOOD)]
    trunks = sorted((e for e in els if e["name"].startswith("trunk")), key=lambda e: e["from"][1])
    out = {"core": [], "wraps": [], "floating": [], "step": []}
    for e in els:
        if CORE.search(e["name"]):
            out["core"].append(e["name"])
            continue
        size = np.array(e["to"]) - np.array(e["from"])
        if e in wood or min(size) <= 0.6 or e["name"].startswith(SMALL_DETAILS):
            continue
        hit = sorted({w["name"] for w in wood if runs_through(w, e)})
        if hit:
            out["wraps"].append(f"{e['name']} ({', '.join(hit)})")
    for e in wood:
        if e["name"].startswith(("trunk", "leader")):
            continue
        ends = axis_ends(e)
        if not any(inside(p, o, tol=0.75) for p in ends for o in wood if o is not e):
            out["floating"].append(e["name"])
    for lo, hi in zip(trunks, trunks[1:]):
        if abs(hi["from"][1] - lo["to"][1]) > 0.01:
            out["step"].append(f"{hi['name']} starts at y {hi['from'][1]}, {lo['name']} ends at y {lo['to'][1]}")
        over = max(max(lo["from"][i] - hi["from"][i], hi["to"][i] - lo["to"][i]) for i in (0, 2))
        if over > 0.01:
            out["step"].append(f"{hi['name']} overhangs {lo['name']} by {over:g}")
    return out


def remove_cores(d):
    gone = {e["uuid"] for e in d["elements"] if CORE.search(e["name"])}
    d["elements"] = [e for e in d["elements"] if e["uuid"] not in gone]

    def prune(children):
        kept = []
        for c in children:
            if isinstance(c, str):
                if c not in gone:
                    kept.append(c)
                continue
            c["children"] = prune(c.get("children", []))
            if c["children"]:
                kept.append(c)
            else:
                gone.add(c["uuid"])  # group left empty, e.g. lobe_cores or centre_core
        return kept

    d["outliner"] = prune(d["outliner"])
    if "groups" in d:
        d["groups"] = [g for g in d["groups"] if g["uuid"] not in gone]
    for anim in d.get("animations", []):
        for uid in list(anim.get("animators", {})):
            if uid in gone:
                del anim["animators"][uid]
    return len(gone)


def main(argv):
    fix = "--fix" in argv
    paths = [Path(a) for a in argv if a != "--fix"] or sorted(TREES.glob("*.bbmodel"))
    for p in paths:
        d = json.loads(p.read_text())
        rep = analyse(d)
        print(f"== {p.name}: {len(d['elements'])} cubes")
        for k, v in rep.items():
            print(f"   {k:9s}{len(v):3d}  {'; '.join(v[:6])}{' ...' if len(v) > 6 else ''}")
        if fix and rep["core"]:
            n = remove_cores(d)
            p.write_text(json.dumps(d, separators=(",", ":"), ensure_ascii=False))
            print(f"   fixed: removed {n} core cubes and empty groups")


if __name__ == "__main__":
    main(sys.argv[1:])
