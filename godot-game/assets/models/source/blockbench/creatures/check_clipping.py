"""Check a Blockbench creature for clipping, in its rest pose and in every
frame of every animation, using Blockbench's own animator for the poses.

Run Blockbench with remote debugging first:
    Blockbench.exe --remote-debugging-port=9333
then:
    python check_clipping.py chicken.bbmodel --spec build_chicken_bbmodel.py

What it checks, on sample points every texture pixel over every face (plus
the corners and edges) of every exported box:
- Pass-through: a point on a visible face goes inside a box of another bone
  (a leg through the belly, a wing into the body, the head into the neck
  ring). Boxes of the same bone never move apart, so they are not compared.
- Exposed: a point that is hidden inside another bone at rest comes out (a
  leg top poking through the side of the body, a hole where a face was
  removed because it was hidden).
- Z-fighting: two visible faces on the same plane, facing the same way.
- Ground: anything visible below y = 0.
At a joint, the skin of a child bone may fold into its parent within the
joint radius of the child's pivot (default 1.5 px): that is a crease, not a
clip. A build script's JOINTS table can widen a joint (a bending snake) or
declare one between bones that aren't parent and child (a leg and the body
it hangs from, both children of the root): {child: [(other bone, px)]},
or (other bone, px, deepest fold in px) to keep a wide joint shallow.
Removed faces never get this allowance.

Exit code 0 means clean. Needs: websocket-client, numpy.
"""

import argparse
import importlib.util
import json
import sys
import urllib.request
from collections import defaultdict
from pathlib import Path

import numpy as np
import websocket

PX = 0.5          # units per texture pixel
TOL = 0.05        # units (0.1 px): touching is fine, deeper is a clip

JS = r"""
(async () => {
  Modes.options.edit.select();
  const cubes = Cube.all.filter(c => c.export !== false);
  const groups = Group.all;
  const v = new THREE.Vector3();
  function grab() {
    scene.updateMatrixWorld(true);
    return {
      m: cubes.map(c => Array.from(c.mesh.matrixWorld.elements)),
      g: groups.map(g => { g.mesh.getWorldPosition(v); return [v.x, v.y, v.z]; }),
    };
  }
  const info = {
    cubes: cubes.map(c => {
      c.mesh.geometry.computeBoundingBox();
      const b = c.mesh.geometry.boundingBox;
      return {name: c.name, bone: c.parent.name, min: [b.min.x, b.min.y, b.min.z],
              max: [b.max.x, b.max.y, b.max.z], from: c.from, to: c.to,
              faces: Object.fromEntries(Object.entries(c.faces).map(([k, f]) => [k, f.texture !== null && f.texture !== undefined && f.texture !== false]))};
    }),
    groups: groups.map(g => ({name: g.name, parent: g.parent && g.parent.name ? g.parent.name : null})),
  };
  Modes.options.animate.select();
  if (Animator.showDefaultPose) Animator.showDefaultPose();
  const rest = grab();
  const anims = {};
  for (const a of Animation.all) {
    a.select();
    const frames = [];
    const n = Math.round(a.length * 24);
    for (let k = 0; k <= n; k++) {
      Timeline.setTime(k / 24);
      Animator.preview();
      frames.push(grab());
    }
    anims[a.name] = frames;
  }
  Animation.all.forEach(a => a.selected = false);
  if (Animator.showDefaultPose) Animator.showDefaultPose();
  Modes.options.edit.select();
  return {info, rest, anims};
})()
"""

FACE_AXIS = {"north": (2, -1), "south": (2, 1), "east": (0, 1), "west": (0, -1), "up": (1, 1), "down": (1, -1)}


def cdp_eval(expr, port=9333):
    targets = json.load(urllib.request.urlopen(f"http://127.0.0.1:{port}/json"))
    page = [t for t in targets if t["type"] == "page"][0]
    ws = websocket.create_connection(page["webSocketDebuggerUrl"], timeout=600, suppress_origin=True)
    ws.send(json.dumps({"id": 1, "method": "Runtime.evaluate",
                        "params": {"expression": expr, "awaitPromise": True, "returnByValue": True}}))
    while True:
        m = json.loads(ws.recv())
        if m.get("id") == 1:
            break
    r = m["result"]
    if "exceptionDetails" in r:
        raise SystemExit("Blockbench error: " + json.dumps(r["exceptionDetails"])[:2000])
    return r["result"]["value"]


def load(path, port):
    p = str(Path(path).resolve()).replace("\\", "/")
    content = Path(path).read_text(encoding="utf8")
    expr = ("(()=>{for (const pr of [...ModelProject.all]) pr.close(true);"
            f"loadModelFile({{path:{json.dumps(p)},name:{json.dumps(Path(p).name)},"
            f"content:{json.dumps(content)}}});return Cube.all.length}})()")
    return cdp_eval(expr, port)


def samples(c):
    """Sample points in the box's own (unrotated) units, with the face each
    lies on (None for corner/edge points) and whether that face is kept."""
    lo, hi = np.array(c["from"], float), np.array(c["to"], float)
    pts, kept, face = [], [], []
    for f, (ax, s) in FACE_AXIS.items():
        a, b = [k for k in range(3) if k != ax]
        ua = np.arange(lo[a] + PX / 2, hi[a], PX)
        ub = np.arange(lo[b] + PX / 2, hi[b], PX)
        for x in ua:
            for y in ub:
                p = np.zeros(3)
                p[ax] = hi[ax] if s > 0 else lo[ax]
                p[a], p[b] = x, y
                pts.append(p)
                kept.append(c["faces"][f])
                face.append(f)
    # corners and edges, every half pixel: these poke out first
    for ax in range(3):
        a, b = [k for k in range(3) if k != ax]
        for va in (lo[a], hi[a]):
            for vb in (lo[b], hi[b]):
                for t in np.arange(lo[ax], hi[ax] + 1e-9, PX / 2):
                    p = np.zeros(3)
                    p[ax], p[a], p[b] = t, va, vb
                    pts.append(p)
                    kept.append(True)
                    face.append("")
    pts = np.array(pts)
    span = np.where(hi - lo == 0, 1, hi - lo)
    local = np.array(c["min"]) + (pts - lo) / span * (np.array(c["max"]) - np.array(c["min"]))
    return local, np.array(kept), np.array(face)


def face_normals_local():
    out = {}
    for f, (ax, s) in FACE_AXIS.items():
        n = np.zeros(3)
        n[ax] = s
        out[f] = n
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("model")
    ap.add_argument("--port", type=int, default=9333)
    ap.add_argument("--joint", type=float, default=1.5, help="joint radius in px")
    ap.add_argument("--spec", help="the build script, for its JOINTS table")
    ap.add_argument("--show", type=int, default=40)
    args = ap.parse_args()

    load(args.model, args.port)
    data = cdp_eval(JS, args.port)
    info = data["info"]
    cubes = info["cubes"]
    gnames = [g["name"] for g in info["groups"]]
    parent = {g["name"]: g["parent"] for g in info["groups"]}
    # (bone, bone) -> (the bone whose pivot is the joint, radius, deepest fold), in units
    joints = {}
    for g in gnames:
        if parent.get(g):
            joints[(g, parent[g])] = joints[(parent[g], g)] = (g, args.joint * PX, np.inf)
    if args.spec:
        spec = importlib.util.spec_from_file_location("spec", args.spec)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        for child, pairs in getattr(mod, "JOINTS", {}).items():
            for other, r, *cap in pairs:
                joints[(child, other)] = joints[(other, child)] = (
                    child, r * PX, cap[0] * PX if cap else np.inf)

    N = len(cubes)
    bone_of = [c["bone"] for c in cubes]
    MN = np.array([c["min"] for c in cubes])
    MX = np.array([c["max"] for c in cubes])
    pts, owner, kept, face = [], [], [], []
    for ci, c in enumerate(cubes):
        p, k, fc = samples(c)
        pts.append(p)
        owner.append(np.full(len(p), ci))
        kept.append(k)
        face.append(fc)
    P = np.vstack(pts)
    P4 = np.hstack([P, np.ones((len(P), 1))])
    owner = np.concatenate(owner)
    kept = np.concatenate(kept)
    face = np.concatenate(face)
    owner_bone = np.array([bone_of[o] for o in owner])
    same_bone = np.array([[bone_of[a] == bone_of[b] for b in range(N)] for a in range(N)])
    print(f"{info['cubes'].__len__()} boxes, {len(gnames)} bones, {len(P)} sample points, "
          f"{sum(len(f) for f in data['anims'].values())} animation frames")

    def frame_mats(fr):
        return np.array([np.array(m).reshape(4, 4).T for m in fr["m"]])

    def depths(W):
        """World points, and for every point the deepest other-bone box it is
        inside (depth in units, negative = outside) and which box."""
        world = np.einsum("pij,pj->pi", W[owner], P4)
        Winv = np.linalg.inv(W)
        best = np.full(len(P), -np.inf)
        arg = np.full(len(P), -1)
        hidden = np.full(len(P), -np.inf)     # deepest inside any other box, any bone
        for b in range(N):
            q = (world @ Winv[b].T)[:, :3]
            d = np.minimum(q - MN[b], MX[b] - q).min(axis=1)
            d[owner == b] = -np.inf
            hidden = np.maximum(hidden, d)
            d[same_bone[owner, b]] = -np.inf
            better = d > best
            best[better] = d[better]
            arg[better] = b
        return world, best, arg, hidden

    nloc = face_normals_local()
    face_pts = np.where(kept & (face != ""))[0]

    def zfight(W, world, cross_only):
        """Visible face texels lying on another box's visible face that faces
        the same way."""
        hits = set()
        Winv = np.linalg.inv(W)
        for b in range(N):
            q = (world[face_pts] @ Winv[b].T)[:, :3]
            for f, (ax, s) in FACE_AXIS.items():
                if not cubes[b]["faces"][f]:
                    continue
                plane = MX[b][ax] if s > 0 else MN[b][ax]
                on = np.abs(q[:, ax] - plane) < 1e-3
                for k in range(3):
                    if k != ax:
                        on &= (q[:, k] > MN[b][k] + 1e-3) & (q[:, k] < MX[b][k] - 1e-3)
                idx = face_pts[on & (owner[face_pts] != b)]
                if cross_only:
                    idx = idx[~same_bone[owner[idx], b]]
                nb = W[b][:3, :3] @ nloc[f]
                for pi in idx:
                    a = owner[pi]
                    if np.dot(W[a][:3, :3] @ nloc[face[pi]], nb) > 0.99:
                        hits.add((a, b))
        return hits

    W0 = frame_mats(data["rest"])
    world0, d0, a0, h0 = depths(W0)
    embedded = d0 > TOL       # inside another bone at rest
    hidden0 = h0 > TOL        # inside anything at rest
    problems = defaultdict(lambda: [0.0, set(), None])

    def note(kind, anim, t, a, b, depth, pi=None):
        key = (kind, cubes[a]["name"], cubes[b]["name"] if b is not None else "")
        if depth >= problems[key][0]:
            problems[key][0] = depth
            if pi is not None:   # where on the box, in its own px coordinates
                lo, hi = np.array(cubes[a]["from"]), np.array(cubes[a]["to"])
                mn, mx = MN[a], MX[a]
                p = lo + (P[pi] - mn) / np.where(mx - mn == 0, 1, mx - mn) * (hi - lo)
                problems[key][2] = "at " + ",".join(f"{v / PX:g}" for v in p)
        problems[key][1].add(f"{anim}@{t:.2f}")

    for a, b in zfight(W0, world0, cross_only=False):
        note("z-fighting", "rest", 0, a, b, 0)
    low = (world0[:, 1] < -TOL) & kept
    for pi in np.where(low)[0]:
        note("below ground", "rest", 0, owner[pi], None, -world0[pi, 1] / PX)

    for anim, frames in data["anims"].items():
        for k, fr in enumerate(frames):
            t = k / 24
            W = frame_mats(fr)
            world, d, arg, hid = depths(W)
            gpos = {g: np.array(p) for g, p in zip(gnames, fr["g"])}

            def exempt(pi, other_bone, depth):
                if not kept[pi]:
                    return False
                j = joints.get((owner_bone[pi], other_bone))
                if j is None:
                    return False
                return depth <= j[2] and np.linalg.norm(world[pi, :3] - gpos[j[0]]) <= j[1]

            # visible surface (a kept face, not hidden at rest) going into another bone
            for pi in np.where(kept & ~hidden0 & (d > TOL))[0]:
                if not exempt(pi, bone_of[arg[pi]], d[pi]):
                    note("pass-through", anim, t, owner[pi], arg[pi], d[pi] / PX, pi)
            for pi in np.where(embedded & hidden0 & (hid < -TOL))[0]:
                if not exempt(pi, bone_of[a0[pi]], -hid[pi]):
                    note("exposed" if kept[pi] else "hole (removed face shows)", anim, t,
                         owner[pi], a0[pi], -d[pi] / PX, pi)
            for pi in np.where((world[:, 1] < -TOL) & kept)[0]:
                note("below ground", anim, t, owner[pi], None, -world[pi, 1] / PX)
            if k % 2 == 0:
                for a, b in zfight(W, world, cross_only=True):
                    note("z-fighting", anim, t, a, b, 0)

    if not problems:
        print("CLEAN: no pass-through, exposed parts, holes, z-fighting or ground clipping "
              f"in the rest pose or any frame of: {', '.join(data['anims'])}")
        return 0
    rows = sorted(problems.items(), key=lambda kv: -kv[1][0])
    print(f"{len(rows)} problems (depth in px):")
    for (kind, a, b), (depth, when, where) in rows[:args.show]:
        w = sorted(when)
        print(f"  {kind:26s} {a:24s} {b:24s} {depth:5.2f}  {where or ''}  "
              f"{', '.join(w[:4])}{' ...' if len(w) > 4 else ''}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
