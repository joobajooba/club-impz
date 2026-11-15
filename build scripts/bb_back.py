"""Look at the clothing set in REAL Blockbench (throwaway copy): file facts, then four views of each outfit. Args: outfit names (default all)."""
import base64, io, json, math, sys
import numpy as np
from PIL import Image, ImageDraw
from bb import BB

D = r'C:\Users\lucas\blockbench_models\impz\back'
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
    b.camera((c[0] + dist * math.sin(a) * math.cos(p), c[1] + dist * math.sin(p), c[2] + dist * math.cos(a) * math.cos(p)), c)


members = json.load(open('back_members.json'))
want = sys.argv[1:] or list(members)
print(b.open(D + r'\back_showcase.bbmodel'))
cells = []
for n in want:
    m = members[n]
    ox, _, oz = m['off']
    ids = json.dumps(sorted(m['ids']))
    b.js(f"const s = new Set({ids}); Cube.all.forEach(c => c.visibility = s.has(c.uuid)); Canvas.updateVisibility(); return 1;")
    row = []
    for ya, pi in ((0, 6), (38, 18), (180, 10), (-90, 6)):
        orbit([ox, 58, oz - 4], ya, pi, 175)
        v = viewport()
        s = min(v.width, v.height)
        row.append(v.crop(((v.width - s) // 2, (v.height - s) // 2, (v.width + s) // 2, (v.height + s) // 2)).resize((250, 250), Image.LANCZOS))
    c = Image.new('RGB', (250 * 4 + 12, 250), (15, 15, 15))
    for i, v in enumerate(row):
        c.paste(v, (i * 254, 0))
    ImageDraw.Draw(c).text((4, 2), n, fill=(255, 255, 0))
    cells.append(c)
W, H = cells[0].size
tag = '_'.join(sys.argv[1:])[:40] or 'all'
for p in range(0, len(cells), 6):
    g = cells[p:p + 6]
    o = Image.new('RGB', (W * 2 + 6, (H + 4) * ((len(g) + 1) // 2)), (40, 40, 40))
    for i, c in enumerate(g):
        o.paste(c, ((i % 2) * (W + 6), (i // 2) * (H + 4)))
    o.save(f'cloth_sheets/back_{tag}_{p // 6 + 1}.png')
    print('page', p // 6 + 1, o.size)
