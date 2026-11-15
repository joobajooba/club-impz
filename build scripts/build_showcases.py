"""lamps_showcase and town_decor_showcase: every model of each set in one file, textures stitched into a 2048 atlas.
Rebuilds every model first (so they are current)."""
import os, sys, json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import build_lamps as L, build_town_decor as T
from foliage_lib import showcase
sys.path.insert(0, r"C:\Users\lucas\club-impz\build scripts")
import fix_texture_bleed


def make(mod, layout, name):
    models = []
    for n, ox, oz in layout:
        H = mod.build(n); models.append((H.m, (ox, oz)))
    S = showcase(models, name, mod.OUT, tex=2048, seed=99)
    p = os.path.join(mod.OUT, name + ".bbmodel")
    d = json.load(open(p)); json.dump(d, open(p, "w"), indent="\t"); fix_texture_bleed.pad_file(p)
    print(name, "cubes", len(S.elements) - 1)


make(L, [("street_lamp", -40, 0), ("street_lamp_double", -10, 0), ("plaza_lamp", 25, 0), ("wall_lantern", 50, 0),
         ("path_lantern", 68, 0)], "lamps_showcase")
make(T, [("planter_square_flowers", -60, 0), ("planter_trough_flowers", -30, 0), ("urn_planter", 0, 0),
         ("topiary_ball_planter", 22, 0), ("topiary_tiered_planter", 44, 0), ("hedge_segment", -40, 35),
         ("blossom_tree_planter", 5, 40)], "town_decor_showcase")
