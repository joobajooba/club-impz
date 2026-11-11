"""Render the wizard tower in a throwaway Blockbench: py bb_tower.py -> tower_sheet.png + single shots."""
import sys
sys.path.insert(0, "C:/Users/lucas/club-impz/build scripts")
from bb import BB
from PIL import Image
P = "C:/Users/lucas/blockbench_models/buildings/wizard_tower.bbmodel"
views = [((330, 260, -470), (0, 180, 0)), ((-360, 240, 420), (0, 180, 0)),
         ((95, 300, -150), (0, 270, 0)), ((80, 50, -120), (0, 40, -10)),
         ((-90, 190, -110), (0, 160, 0)), ((70, 360, 90), (-4, 320, 0))]
b = BB(); assert b.wait_ready(); b.load_plugin()
r = b.open(P); print(r)
shots = []
for i, (pos, tgt) in enumerate(views):
    b.camera(pos, tgt); o = f"tw_{i}.png"; b.shot(o)
    Image.open(o).crop((370, 105, 1600, 1000)).save(o); shots.append(o)
ims = [Image.open(s) for s in shots]
w, h = ims[0].size
sheet = Image.new("RGB", (w, ((len(ims) + 1) // 2) * h // 2))
for i, im in enumerate(ims): sheet.paste(im.resize((w // 2, h // 2)), ((i % 2) * w // 2, (i // 2) * h // 2))
sheet.save("tower_sheet.png"); print(sheet.size)
