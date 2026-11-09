"""Check the hub's fences (J00BA, 2026-11-09: no rail may stop in mid-air, no doubled posts, side fences reach the
front fence line).

Reads godot-game/data/hub_town.json and the fence .bbmodel files. The post and rail-end positions come from the
models themselves: a cube named "post" (its centre) and the cubes named "rail_*" (their east end, local +x).
Every fence model (an alias starting with "fence_") is checked; aliases with rails are rails, the rest are lone posts.

Reports:
  1. rail ends with no post within 0.05 m (the rail's own post, another rail's post or a fence_post)
  2. pairs of posts closer than 0.1 m (doubled posts, which flicker)
  3. side fence ends (runs across the yard rows, yaw +-90) that are not on the front fence line or the back of
     their plot (the rows are taken from the plan's "yard_rows" when it has them, else from the plot depth)
  4. plot closure (when the plan has "yard_rows"): flood fill on a 5 cm grid of every collider (the player is a 0.3 m
     radius capsule) from each plot's middle; a plot is closed if the fill only leaves it through its gateway

Usage: py "build scripts/check_fences.py" [hub_town.json]"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "godot-game")
U = 1.0 / 16.0


def model_geometry(path):
    d = json.load(open(path, encoding="utf8"))
    post, rail_end = None, None
    for e in d["elements"]:
        if e["name"] == "post":
            post = ((e["from"][0] + e["to"][0]) / 2 * U, (e["from"][2] + e["to"][2]) / 2 * U)
        if e["name"].startswith("rail_"):
            rail_end = max(rail_end or -1e9, e["to"][0] * U)
    return post, rail_end


def rot(lx, lz, yaw):
    t = math.radians(yaw)
    return math.cos(t) * lx + math.sin(t) * lz, -math.sin(t) * lx + math.cos(t) * lz


def main():
    plan_path = sys.argv[1] if len(sys.argv) > 1 else os.path.join(GAME, "data", "hub_town.json")
    plan = json.load(open(plan_path, encoding="utf8"))
    geo = {}
    for alias, m in plan["models"].items():
        if alias.startswith("fence_"):
            bb = m["path"].replace("res://", GAME + "/").replace(".glb", ".bbmodel")
            geo[alias] = model_geometry(bb)
    posts, ends, rails = [], [], []
    for alias, x, y, z, yaw, s in plan["placements"]:
        if alias not in geo:
            continue
        (px_, pz_), rend = geo[alias]
        wx, wz = rot(px_ * s, pz_ * s, yaw)
        posts.append((x + wx, z + wz, alias))
        if rend is not None:
            ex, ez = rot(rend * s, 0.0, yaw)
            ends.append((x + ex, z + ez, alias))
            rails.append(((x + wx, z + wz), (x + ex, z + ez), yaw))
    print(f"fence pieces: {sum(1 for p in plan['placements'] if p[0] in geo)} "
          f"({len(rails)} rails, {len(posts) - len(rails)} lone posts), models: "
          + ", ".join(f"{a} post {g[0][0]:+.4f},{g[0][1]:+.4f} rail end {g[1]}" for a, g in sorted(geo.items())))
    # 1. open rail ends
    open_ends = [(ex, ez, a) for ex, ez, a in ends if min(math.hypot(ex - px_, ez - pz_) for px_, pz_, _ in posts) > 0.05]
    print(f"\n1. rail ends with no post within 0.05 m: {len(open_ends)}")
    for ex, ez, a in open_ends:
        d = min(math.hypot(ex - px_, ez - pz_) for px_, pz_, _ in posts)
        print(f"   {a} end at x {ex:.4f} z {ez:.4f} (nearest post {d:.4f} m)")
    # 2. doubled posts
    dbl = []
    for i in range(len(posts)):
        for j in range(i + 1, len(posts)):
            d = math.hypot(posts[i][0] - posts[j][0], posts[i][1] - posts[j][1])
            if d < 0.1:
                dbl.append((posts[i], posts[j], d))
    print(f"\n2. posts closer than 0.1 m: {len(dbl)}")
    for a, b, d in dbl:
        print(f"   {a[2]} at {a[0]:.4f},{a[1]:.4f} and {b[2]} at {b[0]:.4f},{b[1]:.4f} ({d:.4f} m)")
    # 3. side fences short of the front line / back
    rows = plan.get("yard_rows")
    if rows is None:  # older plans: the rows from the plot layout the yard used (back of the plot, 9.5 m deep)
        rows = {"north": {"back": -29.5, "front": -29.5 + 9.2}, "south": {"back": -2.5, "front": -2.5 - 9.2}}
        print("\n   (plan has no yard_rows: front line taken as the front fences' line, plot depth 9.5 - 0.3)")
    lines = {}
    for (p, e, yaw) in rails:
        if abs(abs(yaw) - 90) < 1:                           # a rail running along z: part of a side fence
            key = round(p[0], 2)
            lines.setdefault(key, []).extend([p[1], e[1]])
    for px_, pz_, a in posts:
        if a.startswith("fence_post") and round(px_, 2) in lines:
            lines[round(px_, 2)].append(pz_)
    bad = []
    for x, zs in sorted(lines.items()):
        for row in rows.values():
            lo, hi = sorted((row["back"], row["front"]))
            seg = [z for z in zs if lo - 1.0 <= z <= hi + 1.0]
            if not seg:
                continue
            for zend, want in ((min(seg), lo), (max(seg), hi)):
                if abs(zend - want) > 0.05:
                    bad.append((x, zend, want))
    print(f"\n3. side fence ends not on the front fence line or the back of the plot: {len(bad)}")
    for x, z, want in bad:
        print(f"   side fence at x {x:.4f} ends at z {z:.4f}, line is at z {want:.4f} ({abs(z - want):.4f} m short)")
    # 4. plot closure
    if "yard_plots" in plan:
        closure(plan)
    return len(open_ends) + len(dbl) + len(bad)


def closure(plan, r=0.3, cell=0.05):
    """Flood fill from each plot's middle over free cells (more than the player radius from every collider box).
    The fill may leave the plot only through its gateway (the front line between the two gate posts) or, for the
    passage, its front and back. Reports any other escape."""
    boxes = []
    for c in plan["colliders"]:
        cx, cy, cz, sx, sy, sz, yaw = c
        if cy - sy / 2 > 1.0:                                 # above the player's head: no block
            continue
        boxes.append((cx, cz, sx / 2 + r, sz / 2 + r, math.radians(yaw)))
    bad = 0
    print("\n4. plot closure (player radius 0.3 m):")
    for p in plan["yard_plots"]:
        x1, z1, x2, z2 = p["rect"]
        gx1, gx2 = p["gate"]
        gz = p["front_z"]
        X1, Z1, X2, Z2 = x1 - 1.5, z1 - 1.5, x2 + 1.5, z2 + 1.5
        nx, nz = int((X2 - X1) / cell), int((Z2 - Z1) / cell)
        near = [b for b in boxes if X1 - 3 < b[0] < X2 + 3 and Z1 - 3 < b[1] < Z2 + 3]

        def free(i, j):
            x, z = X1 + (i + 0.5) * cell, Z1 + (j + 0.5) * cell
            for cx, cz, hx, hz, a in near:
                dx, dz = x - cx, z - cz
                lx = math.cos(a) * dx - math.sin(a) * dz
                lz = math.sin(a) * dx + math.cos(a) * dz
                if abs(lx) < hx and abs(lz) < hz:
                    return False
            return True
        si, sj = int(((x1 + x2) / 2 - X1) / cell), int((z1 + (z2 - z1) * (0.5 if p["front_z"] > z1 else 0.5) - Z1) / cell)
        seen = {(si, sj)} if free(si, sj) else set()
        stack = list(seen)
        leaks = set()
        while stack:
            i, j = stack.pop()
            x, z = X1 + (i + 0.5) * cell, Z1 + (j + 0.5) * cell
            outside = not (x1 < x < x2 and z1 < z < z2)
            if outside:
                through_gate = gx1 - 0.01 <= x <= gx2 + 0.01 and abs(z - gz) < 1.6
                if p.get("passage"):
                    through_gate = gx1 - 0.01 <= x <= gx2 + 0.01
                if not through_gate:
                    leaks.add((round(x, 1), round(z, 1)))
                continue
            for di, dj in ((1, 0), (-1, 0), (0, 1), (0, -1)):
                k = (i + di, j + dj)
                if k not in seen and 0 <= k[0] < nx and 0 <= k[1] < nz and free(*k):
                    seen.add(k); stack.append(k)
        if not seen:
            print(f"   {p['name']}: start cell blocked (move the start)"); bad += 1; continue
        if leaks:
            bad += 1
            xs = sorted(leaks)
            print(f"   {p['name']}: OPEN, {len(leaks)} escape cells, e.g. {xs[:3]}")
        else:
            print(f"   {p['name']}: closed except its {'front and back (passage)' if p.get('passage') else 'gateway'}")
    print(f"   plots open elsewhere: {bad}")


if __name__ == "__main__":
    n = main()
    print(f"\ntotal problems (1-3): {n}")
