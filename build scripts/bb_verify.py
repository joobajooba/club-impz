"""Verify the trait sets in REAL Blockbench (fresh throwaway copy): file state, a gap test against a stand-in skull, and close-up sheets."""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from bb import BB

HEAD = r'C:\Users\lucas\blockbench_models\impz\head'
EYES = r'C:\Users\lucas\blockbench_models\impz\eyes'
b = BB()
b.wait_ready()
b.load_plugin()


def viewport():
    r = b.call('Page.captureScreenshot', format='png')
    im = Image.open(io.BytesIO(base64.b64decode(r['result']['data']))).convert('RGB')
    x, y, w, h = b.js("const r = Preview.selected.canvas.getBoundingClientRect(); return [r.x, r.y, r.width, r.height];")
    return im.crop((int(x), int(y), int(x + w), int(y + h)))


def orbit(c, ya, pi, dist):
    a, p = math.radians(ya), math.radians(pi)
    pos = (c[0] + dist * math.sin(a) * math.cos(p), c[1] + dist * math.sin(p), c[2] + dist * math.cos(a) * math.cos(p))
    b.camera(pos, c)


def only(ids):
    ids = json.dumps(sorted(ids))
    b.js(f"const s = new Set({ids}); Cube.all.forEach(c => c.visibility = s.has(c.uuid)); Canvas.updateVisibility(); Preview.selected.render(); return 1;")


# --- 1. file-level facts as Blockbench loaded them
print('--- individual trait files')
names = ['afro', 'blonde', 'bob', 'cap', 'clown', 'crown', 'fez', 'geezer', 'halo', 'hawk', 'mayc_brim', 'sea_captain', 'slick', 'soldier', 'spiky', 'straw_hat', 'tiara']
bad = 0
for n in names:
    b.open(f'{HEAD}\\head_{n}.bbmodel')
    r = b.js("return {cubes: Cube.all.length, internal: Texture.all.every(t => t.internal), err: Texture.all.some(t => t.error), stretched: Cube.all.filter(c => c.stretch.some(v => v != 1)).length, fmt: Format.id};")
    ok = r['internal'] and not r['err'] and r['stretched'] == 0 and r['fmt'] == 'hytale_character' and r['cubes'] <= 40
    bad += not ok
    print(f"{n:12s} {r}" + ('' if ok else '  <-- PROBLEM'))
print('file problems:', bad)

# --- 2. gap test in real Blockbench, against a stand-in skull, from many angles
members = json.load(open('head_members.json'))
b.open(f'{HEAD}\\head_showcase.bbmodel')
print(b.js("return {cubes: Cube.all.length, internal: Texture.all[0].internal};"))
skulls = b.js("return Cube.all.filter(c => c.name == 'Head' && c.to[0]-c.from[0] > 28).map(c => [c.uuid, c.from[0], c.to[0], c.from[1], c.to[1], c.from[2], c.to[2]]);")
FULL = ['afro', 'blonde', 'bob', 'slick', 'clown', 'cap', 'mayc_brim', 'sea_captain', 'soldier']
TOP = ['spiky', 'straw_hat']
VIEWS = [(90, 0), (-90, 0), (180, 0), (35, 55), (-35, 55), (145, 35), (-145, 35), (0, 80), (90, 30), (-90, 30), (180, 40), (60, 20), (-60, 20), (120, 20), (-120, 20)]
TOPV = [(35, 55), (-35, 55), (145, 45), (-145, 45), (0, 80), (90, 60), (-90, 60), (180, 60)]
total = 0
print('--- gap test: bright stand-in skull pixels that show')
for n in FULL + TOP:
    ox, _, oz = members[n]['off']
    sk = next(s for s in skulls if s[0] in members[n]['ids'])
    lo, hi = ([ox - 14.8, 85, oz - 8.8], [ox + 14.8, 90.8, oz + 18]) if n in FULL else ([ox - 14.8, 90.6, oz - 8.8], [ox + 14.8, 90.9, oz + 18.6])
    # stand-in skull, in pure magenta so nothing else can be mistaken for it
    trait_ids = set(members[n]['ids'])
    body_ids = json.load(open('head_body_ids.json'))[n]
    keep = (trait_ids - set(body_ids)) | {sk[0]}
    only(keep)
    b.js(f"""const c = Cube.all.find(c => c.uuid == {json.dumps(sk[0])});
        window.__keep = {{from: c.from.slice(), to: c.to.slice(), stretch: c.stretch.slice(), mat: null}};
        c.from.splice(0, 3, ...{json.dumps(lo)}); c.to.splice(0, 3, ...{json.dumps(hi)}); c.stretch.splice(0, 3, 1, 1, 1);
        c.preview_controller.updateGeometry(c);
        const m = new THREE.MeshBasicMaterial({{color: 0xff00ff}}); window.__mat = c.mesh.material; c.mesh.material = m;
        Preview.selected.render(); return 1;""")
    worst, at = 0, None
    for ya, pi in (VIEWS if n in FULL else TOPV):
        orbit([ox, 88, oz + 5], ya, pi, 130)
        a = np.array(viewport()).astype(int)
        cnt = int(((a[..., 0] > 200) & (a[..., 1] < 70) & (a[..., 2] > 200)).sum())
        if cnt > worst:
            worst, at = cnt, (ya, pi)
    b.js(f"""const c = Cube.all.find(c => c.uuid == {json.dumps(sk[0])});
        c.mesh.material = window.__mat; c.from.splice(0, 3, ...window.__keep.from); c.to.splice(0, 3, ...window.__keep.to); c.stretch.splice(0, 3, ...window.__keep.stretch);
        c.preview_controller.updateGeometry(c); return 1;""")
    total += worst
    print(f'{n:12s} {worst}' + (f'  worst from {at}' if worst else ''))
print('total stand-in skull pixels showing:', total)

# --- 3. close-ups of every head trait, from real Blockbench
cells = []
for n, m in members.items():
    ox, _, oz = m['off']
    only(m['ids'])
    row = []
    tall = n == 'blonde'
    for ya, pi in ((0, 8), (40, 22), (140, 22), (-90, 8)):
        orbit([ox, 62 if tall else 84, oz + 5], ya, pi, 150 if tall else 105)
        v = viewport()
        s = min(v.width, v.height)
        v = v.crop(((v.width - s) // 2, (v.height - s) // 2, (v.width + s) // 2, (v.height + s) // 2)).resize((210, 210), Image.LANCZOS)
        row.append(v)
    c = Image.new('RGB', (210 * 4 + 12, 210), (15, 15, 15))
    for i, v in enumerate(row):
        c.paste(v, (i * 214, 0))
    ImageDraw.Draw(c).text((4, 2), n, fill=(255, 255, 0))
    cells.append(c)
W, H = cells[0].size
for page, group in enumerate((cells[:9], cells[9:])):
    o = Image.new('RGB', (W * 2 + 6, (H + 4) * ((len(group) + 1) // 2)), (40, 40, 40))
    for i, c in enumerate(group):
        o.paste(c, ((i % 2) * (W + 6), (i // 2) * (H + 4)))
    o.save(f'head_sheets/real_page{page + 1}.png')
    print('real page', page + 1, o.size)
b.js("Cube.all.forEach(c => c.visibility = true); Canvas.updateVisibility(); return 1;")
orbit([0, 60, 0], 28, 22, 520)
viewport().save('head_sheets/real_lineup.png')

# --- 4. the eye set, with the same checks
print('--- eye files')
for f in ['3d_glasses', 'shades', 'bug_eye', 'glasses', 'hearts', 'stars', 'goggles', 'mask', 'robo', 'eye_patch', 'monacle', 'tracker_blue', 'tracker_purple', 'lazer', 'neon_beam']:
    b.open(f'{EYES}\\eyes_{f}.bbmodel')
    r = b.js("return {cubes: Cube.all.length, internal: Texture.all.every(t => t.internal), stretched: Cube.all.filter(c => c.stretch.some(v => v != 1)).length};")
    print(f"{f:15s} {r}" + ('' if r['internal'] and not r['stretched'] else '  <-- PROBLEM'))
print(b.open(f'{EYES}\\eyes_showcase.bbmodel'))
orbit([0, 60, 0], 24, 18, 520)
viewport().save('head_sheets/real_eyes_lineup.png')
