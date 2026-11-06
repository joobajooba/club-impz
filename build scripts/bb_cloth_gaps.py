"""Real Blockbench gap test: turn the covered torso magenta, hide head and tail, and count magenta pixels from many angles.
Only outfits that close over the torso are tested; the stand-in stops short of the neck and hem, where skin is meant to end."""
import base64, io, json, math
import numpy as np
from PIL import Image
from bb import BB

D = r'C:\Users\lucas\blockbench_models\impz\clothing'
b = BB()
b.wait_ready()
b.load_plugin()
members = json.load(open('cloth_members.json'))
# name: lowest pelvis y that the outfit covers
TEST = {'white_tee': 30, 'blue_skull_tee': 30, 'skelly_tee': 30, 'robinhood_tee': 30, 'robinhood_hoodie': 30, 'demon_hoodie': 30, 'puffer': 30, 'pyjamas': 30, 'gi': 28,
        'elegant': 30, 'waterproof_coat': 28, 'polka_dress': 28, 'ragged_vest': 28, 'worker_vest': 28, 'armour': 28, 'battle_armour': 30}
VIEWS = [(0, 0), (90, 0), (-90, 0), (180, 0), (35, 25), (-35, 25), (145, 25), (-145, 25), (60, 8), (-60, 8), (120, 8), (-120, 8)]


def viewport():
    r = b.call('Page.captureScreenshot', format='png')
    im = Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')
    x, y, w, h = b.js("const r = Preview.selected.canvas.getBoundingClientRect(); return [r.x, r.y, r.width, r.height];")
    return im.crop((int(x), int(y), int(x + w), int(y + h)))


total = 0
shots = []
for n, low in TEST.items():
    m = members[n]
    ox, _, oz = m['off']
    ids = json.dumps(m['ids'])
    body = json.dumps(m['body'])
    b.open(D + r'\clothing_showcase.bbmodel')
    res = b.js(f"""const ids = new Set({ids}), body = new Set({body});
        window.__sw = [];
        Cube.all.forEach(c => {{
            c.visibility = ids.has(c.uuid);
            if (!body.has(c.uuid)) return;
            const wide = c.to[0] - c.from[0];
            
            if ((c.name == 'Chest' || (c.name == 'Pelvis' && wide > 20))) {{
                window.__sw.push({{c, from: c.from.slice(), to: c.to.slice(), stretch: c.stretch.slice(), mat: c.mesh.material}});
                if (c.name == 'Chest') c.to[1] = c.from[1] + {5 if n in ('polka_dress', 'ragged_vest', 'worker_vest') else 16};          // stops below the neck hole, y about 59
                else c.from[1] = {low};
                c.stretch.splice(0, 3, 1, 1, 1);
                c.preview_controller.updateGeometry(c);
                c.mesh.material = new THREE.MeshBasicMaterial({{color: 0xff00ff}});
            }}
        }});
        Canvas.updateVisibility(); Preview.selected.render(); return window.__sw.length;""")
    # control: with the outfit hidden, the magenta stand-in must show, or the test proves nothing
    b.js(f"const body = new Set({body}); window.__o = Cube.all.filter(c => c.visibility && !body.has(c.uuid)); window.__o.forEach(c => c.visibility = false); Canvas.updateVisibility(); return 1;")
    ctl = (ox, 44, oz + 3)
    b.camera((ctl[0], ctl[1], ctl[2] + 110), ctl)
    arr = np.array(viewport()).astype(int)
    control = int(((arr[..., 0] > 245) & (arr[..., 1] < 12) & (arr[..., 2] > 245)).sum())
    b.js("window.__o.forEach(c => c.visibility = true); Canvas.updateVisibility(); return 1;")
    assert control > 500, (n, 'control failed', control)
    worst, at, img = 0, None, None
    for ya, pi in VIEWS:
        a_, p_ = math.radians(ya), math.radians(pi)
        c = (ox, 44, oz + 3)
        d = 110
        b.camera((c[0] + d * math.sin(a_) * math.cos(p_), c[1] + d * math.sin(p_), c[2] + d * math.cos(a_) * math.cos(p_)), c)
        v = viewport()
        arr = np.array(v).astype(int)
        cnt = int(((arr[..., 0] > 245) & (arr[..., 1] < 12) & (arr[..., 2] > 245)).sum())
        if cnt > worst:
            worst, at, img = cnt, (ya, pi), v
    b.js("""window.__sw.forEach(s => { s.c.from.splice(0, 3, ...s.from); s.c.to.splice(0, 3, ...s.to); s.c.stretch.splice(0, 3, ...s.stretch); s.c.preview_controller.updateGeometry(s.c); s.c.mesh.material = s.mat; }); return 1;""")
    total += worst
    print(f'{n:18s} control {control:6d}  shows {worst}' + (f'  worst from {at}' if worst else ''))
    if worst and img is not None:
        s_ = min(img.size)
        shots.append(img.crop(((img.width - s_) // 2, (img.height - s_) // 2, (img.width + s_) // 2, (img.height + s_) // 2)).resize((400, 400), Image.LANCZOS))
print('total', total)
if shots:
    o = Image.new('RGB', (404 * min(4, len(shots)), 404 * ((len(shots) + 3) // 4)), (40, 40, 40))
    for i, s_ in enumerate(shots):
        o.paste(s_, ((i % 4) * 404, (i // 4) * 404))
    o.save('cloth_sheets/real_gaps.png')
