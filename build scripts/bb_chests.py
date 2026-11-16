import sys, os
sys.path.insert(0, "C:/Users/lucas/club-impz/build scripts")
HERE = os.path.dirname(os.path.abspath(__file__)); os.chdir(HERE)
from bb import BB
from PIL import Image
names = sys.argv[1:] or ["red", "blue", "green", "yellow", "purple"]
b = BB(); assert b.wait_ready(); b.load_plugin()
shots = []
for k in names:
    r = b.open(rf"C:\Users\lucas\blockbench_models\props\chests\{k}_chest.bbmodel"); print(k, r["cubes"], r["textures"])
    b.js("Modes.options.edit.select(); return 1")
    b.camera((-24, 20, -30), (0, 8, 0)); o = f"bbs_{k}_front.png"; b.shot(o); shots.append(o)
    b.camera((26, 18, 26), (0, 8, 0)); o = f"bbs_{k}_back.png"; b.shot(o); shots.append(o)
    b.js("""Modes.options.animate.select(); const a = Animation.all.find(a=>a.name=='open'); a.select();
            Timeline.setTime(0.6); Animator.preview(); await new Promise(r=>setTimeout(r,500)); return 1""")
    b.camera((-20, 28, -28), (0, 8, 0)); o = f"bbs_{k}_open.png"; b.shot(o); shots.append(o)
crop = (330, 110, 1530, 940)
ims = [Image.open(s).crop(crop) for s in shots]
w, h = ims[0].size; sw, sh = w // 3, h // 3
sheet = Image.new("RGB", (3 * sw, len(names) * sh))
for i, im in enumerate(ims):
    sheet.paste(im.resize((sw, sh)), ((i % 3) * sw, (i // 3) * sh))
sheet.save("bbs_sheet.png"); print(sheet.size)
