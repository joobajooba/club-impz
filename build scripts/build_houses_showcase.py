"""houses_showcase: the six houses in one file (bricks in front, wood behind), textures stitched into one atlas."""
import os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_houses as B
from foliage_lib import showcase
sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
import fix_texture_bleed
layout = [("brick_rose_cottage", -100, 0), ("brick_bluebell_house", 0, 0), ("brick_honey_townhouse", 100, 0),
          ("wood_oak_lodge", -100, 110), ("wood_cherry_manor", 0, 110), ("wood_timber_house", 100, 110)]
models = []
for name, ox, oz in layout:
    H = B.BUILDERS[name]()
    H.finish([B.OUT])
    models.append((H.m, (ox, oz)))
S = showcase(models, "houses_showcase", B.OUT, tex=2048, seed=77)
p = os.path.join(B.OUT, "houses_showcase.bbmodel")
import json
d = json.load(open(p)); json.dump(d, open(p, "w"), indent="\t")
fix_texture_bleed.pad_file(p)
print("showcase cubes", len(S.elements) - 1)
