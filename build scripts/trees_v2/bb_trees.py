"""Screenshots of the new trees in a throwaway Blockbench (build scripts/bb.py: own profile, port 9444).
Usage: py -3 bb_trees.py <out_dir> <tree> [<tree> ...]
For each tree: a front view, a 3/4 view from the other side, and a view with the leaf cards hidden (trunk check)."""
import json, os, sys, time
sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
from bb import BB

out_dir = sys.argv[1]
os.makedirs(out_dir, exist_ok=True)
b = BB(); b.wait_ready(); b.load_plugin()
b.js("Interface.Panels && Object.values(Interface.Panels).forEach(p => {}); return 1")
for t in sys.argv[2:]:
    path = rf"C:\Users\lucas\blockbench_models\trees\{t}_tree.bbmodel"
    info = b.open(path)
    H = b.js("let m=0; Cube.all.forEach(c=>{m=Math.max(m,c.to[1])}); return m")
    W = b.js("let m=0; Cube.all.forEach(c=>{m=Math.max(m,Math.abs(c.to[0]),Math.abs(c.from[0]),Math.abs(c.to[2]),Math.abs(c.from[2]))}); return m")
    d = max(H, W * 2) * 1.9
    views = {"front": ([d * 0.55, H * 0.6, d * 0.85], [0, H * 0.48, 0]),
             "back": ([-d * 0.8, H * 0.75, -d * 0.55], [0, H * 0.48, 0]),
             "low": ([d * 0.35, H * 0.05, d * 0.45], [0, H * 0.45, 0])}
    for name, (pos, tgt) in views.items():
        b.camera(pos, tgt); time.sleep(0.3)
        b.shot(os.path.join(out_dir, f"{t}_{name}.png"))
    b.js("Cube.all.forEach(c => { if (c.name.includes('card')) c.visibility = false; }); Canvas.updateVisibility(); return 1")
    b.camera([d * 0.45, H * 0.45, d * 0.7], [0, H * 0.42, 0]); time.sleep(0.3)
    b.shot(os.path.join(out_dir, f"{t}_nocards.png"))
    print(t, info, "H", H, flush=True)
