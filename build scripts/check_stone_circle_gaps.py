"""check_stone_circle_gaps.py: narrow gaps between stones of stone_circle_ruins at a given game scale (metres).
Each stone = its cubes' corners (low part, y < 30 units) turned by the group rotation (ZYX) about the group origin,
projected on the ground. Gap = closest distance between the 2D convex hulls of two stones."""
import json, math, sys
import numpy as np

SKIP = ("grass_tuft", "heather", "pebble", "rubble")
d = json.load(open(r"C:\Users\lucas\blockbench_models\buildings\ruins\stone_circle_ruins.bbmodel", encoding="utf8"))
els = {e["uuid"]: e for e in d["elements"]}
groups = {g["uuid"]: g for g in d["groups"]}


def rot(rx, ry, rz):
    rx, ry, rz = (math.radians(v) for v in (rx, ry, rz))
    X = np.array([[1, 0, 0], [0, math.cos(rx), -math.sin(rx)], [0, math.sin(rx), math.cos(rx)]])
    Y = np.array([[math.cos(ry), 0, math.sin(ry)], [0, 1, 0], [-math.sin(ry), 0, math.cos(ry)]])
    Z = np.array([[math.cos(rz), -math.sin(rz), 0], [math.sin(rz), math.cos(rz), 0], [0, 0, 1]])
    return Z @ Y @ X


stones = {}


def walk(node, chain):
    if isinstance(node, str):
        return
    g = groups[node["uuid"]]
    chain = chain + [g]
    pts = []
    for c in node["children"]:
        if isinstance(c, str):
            e = els[c]
            if any(s in e["name"] for s in SKIP) or not e.get("export", True):
                continue
            f, t = e["from"], e["to"]
            for x in (f[0], t[0]):
                for y in (f[1], min(t[1], max(f[1], 30))):
                    for z in (f[2], t[2]):
                        p = np.array([x, y, z], float)
                        for gg in reversed(chain):
                            o = np.array(gg["origin"], float)
                            p = rot(*gg["rotation"]) @ (p - o) + o
                        if p[1] < 30:
                            pts.append(p[[0, 2]])
        else:
            walk(c, chain)
    if pts:
        stones[g["name"]] = np.array(pts)


for root in d["outliner"]:
    walk(root, [])


def hull(p):
    p = sorted(map(tuple, p))
    def half(pp):
        h = []
        for q in pp:
            while len(h) >= 2 and ((h[-1][0]-h[-2][0])*(q[1]-h[-2][1]) - (h[-1][1]-h[-2][1])*(q[0]-h[-2][0])) <= 0:
                h.pop()
            h.append(q)
        return h
    lo, hi = half(p), half(p[::-1])
    return np.array(lo[:-1] + hi[:-1])


def seg_pt(a, b, p):
    ab = b - a; t = np.clip(np.dot(p - a, ab) / max(1e-9, ab @ ab), 0, 1)
    return np.linalg.norm(a + t * ab - p)


def poly_dist(A, B):
    best = 1e9
    for P, Q in ((A, B), (B, A)):
        for i in range(len(Q)):
            a, b = Q[i], Q[(i + 1) % len(Q)]
            for p in P:
                best = min(best, seg_pt(a, b, p))
    return best


H = {k: hull(v) for k, v in stones.items() if len(v) >= 3}
scale = float(sys.argv[1]) if len(sys.argv) > 1 else 1.6
names = sorted(H)
narrow = []
for i, a in enumerate(names):
    for b in names[i + 1:]:
        if a.split("_upright")[0] == b.split("_upright")[0] and "lintel" in a + b:
            pass
        dist = poly_dist(H[a], H[b]) * scale / 16
        if dist < 1.1:
            narrow.append((dist, a, b))
for dist, a, b in sorted(narrow):
    print(f"{dist:5.2f} m  {a}  <->  {b}")
