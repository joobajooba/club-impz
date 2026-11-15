import sys
sys.path.insert(0, "C:/Users/lucas/club-impz/build scripts")
from bb import BB
from PIL import Image
names = sys.argv[1:] or ["brick_rose_cottage", "brick_bluebell_house", "brick_honey_townhouse", "wood_oak_lodge", "wood_cherry_manor", "wood_timber_house"]
b = BB(); assert b.wait_ready(); print(b.load_plugin())
shots = []
for k in names:
    print(k, b.open(rf"C:\Users\lucas\blockbench_models\buildings\houses\{k}.bbmodel"))
    b.camera((120, 95, -160), (0, 48, 0))
    o = f"bbshot_{k}.png"; b.shot(o); shots.append(o)
    b.camera((-110, 70, 150), (0, 45, 0))
    o = f"bbshot_{k}_back.png"; b.shot(o); shots.append(o)
ims = [Image.open(s) for s in shots]
w, h = ims[0].size
cols = 4
sheet = Image.new("RGB", (cols * w // 2, ((len(ims) + cols - 1) // cols) * h // 2))
for i, im in enumerate(ims): sheet.paste(im.resize((w // 2, h // 2)), ((i % cols) * w // 2, (i // cols) * h // 2))
sheet.save("bb_houses_sheet.png"); print(sheet.size)
