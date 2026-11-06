"""Find exactly where the stand-in skull shows in real Blockbench, keeping the face (and hairline) out of the test."""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from bb import BB

HEAD = r'C:\Users\lucas\blockbench_models\impz\head'
b = BB()
b.wait_ready()
b.load_plugin()
members = json.load(open('head_members.json'))
body_ids = json.load(open('head_body_ids.json'))


def viewport():
    r = b.call('Page.captureScreenshot', format='png')
    im = Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')
    x, y, w, h = b.js("const r = Preview.selected.canvas.getBoundingClientRect(); return [r.x, r.y, r.width, r.height];")
    return im.crop((int(x), int(y), int(x + w), int(y + h)))


def orbit(c, ya, pi, dist):
    a, p = math.radians(ya), math.radians(pi)
    b.camera((c[0] + dist * math.sin(a) * math.cos(p), c[1] + dist * math.sin(p), c[2] + dist * math.cos(a) * math.cos(p)), c)


b.open(f'{HEAD}\\head_showcase.bbmodel')
skulls = b.js("return Cube.all.filter(c => c.name == 'Head' && c.to[0]-c.from[0] > 28).map(c => c.uuid);")
FULL = ['afro', 'blonde', 'bob', 'slick', 'clown', 'cap', 'mayc_brim', 'sea_captain', 'soldier']
TOP = ['spiky', 'straw_hat']
VIEWS = [(90, 0), (-90, 0), (180, 0), (35, 55), (-35, 55), (145, 35), (-145, 35), (0, 80), (90, 30), (-90, 30), (180, 40), (60, 20), (-60, 20), (120, 20), (-120, 20)]
TOPV = [(35, 55), (-35, 55), (145, 45), (-145, 45), (0, 80), (90, 60), (-90, 60), (180, 60)]
shots = []
total = 0
for n in FULL + TOP:
    ox, _, oz = members[n]['off']
    sk = next(s for s in skulls if s in members[n]['ids'])
    keep = (set(members[n]['ids']) - set(body_ids[n])) | {sk}
    b.js(f"const s = new Set({json.dumps(sorted(keep))}); Cube.all.forEach(c => c.visibility = s.has(c.uuid)); Canvas.updateVisibility(); return 1;")
    # behind the forehead only (z up to 10), so the hairline cut-outs that show the face don't count
    lo, hi = ([ox - 14.8, 85, oz - 8.8], [ox + 14.8, 90.8, oz + 10]) if n in FULL else ([ox - 14.8, 90.6, oz - 8.8], [ox + 14.8, 90.9, oz + 18.6])
    b.js(f"""const c = Cube.all.find(c => c.uuid == {json.dumps(sk)});
        window.__keep = {{from: c.from.slice(), to: c.to.slice(), stretch: c.stretch.slice()}};
        c.from.splice(0, 3, ...{json.dumps(lo)}); c.to.splice(0, 3, ...{json.dumps(hi)}); c.stretch.splice(0, 3, 1, 1, 1);
        c.preview_controller.updateGeometry(c);
        window.__mat = c.mesh.material; c.mesh.material = new THREE.MeshBasicMaterial({{color: 0xff00ff}});
        Preview.selected.render(); return 1;""")
    worst, at, img = 0, None, None
    for ya, pi in (VIEWS if n in FULL else TOPV):
        orbit([ox, 88, oz + 5], ya, pi, 130)
        v = viewport()
        a = np.array(v).astype(int)
        cnt = int(((a[..., 0] > 245) & (a[..., 1] < 12) & (a[..., 2] > 245)).sum())
        if cnt > worst:
            worst, at, img = cnt, (ya, pi), v
    b.js(f"""const c = Cube.all.find(c => c.uuid == {json.dumps(sk)});
        c.mesh.material = window.__mat; c.from.splice(0, 3, ...window.__keep.from); c.to.splice(0, 3, ...window.__keep.to); c.stretch.splice(0, 3, ...window.__keep.stretch);
        c.preview_controller.updateGeometry(c); return 1;""")
    total += worst
    print(f'{n:12s} {worst}' + (f'  worst from {at}' if worst else ''))
    if img is not None:
        s = min(img.size)
        im = img.crop(((img.width - s) // 2, (img.height - s) // 2, (img.width + s) // 2, (img.height + s) // 2)).resize((420, 420), Image.LANCZOS)
        ImageDraw.Draw(im).text((4, 4), f'{n} {at}: {worst}', fill=(255, 255, 0))
        shots.append(im)
print('total:', total)
if shots:
    o = Image.new('RGB', (424 * min(4, len(shots)), 424 * ((len(shots) + 3) // 4)), (40, 40, 40))
    for i, s in enumerate(shots):
        o.paste(s, ((i % 4) * 424, (i // 4) * 424))
    o.save('head_sheets/real_gaps.png')
