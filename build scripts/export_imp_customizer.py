"""Export the Imp body and trait Blockbench models for the in-game character customizer.

Run from the repo root:  python "build scripts/export_imp_customizer.py"
Writes godot-game/data/impz/manifest.json and godot-game/data/impz/models/<id>.json (geometry only).
The textures stay where they are (godot-game/assets/textures/impz/<type>/<id>.png) and Godot imports them.

This mirrors impz-club's scripts/export_impz_models.py (the website's Imp Customization page), so trait ids
and names match the website exactly: <slot>_<name>, e.g. head_afro, with display names from the trait tables
in docs/implingz_collection.md. Re-run it after any change to a body or trait model.
"""
import json, re, shutil
from pathlib import Path
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
GAME = REPO / 'godot-game'
ASSETS = GAME / 'assets'
OUT = GAME / 'data/impz'
TYPES = ['body', 'head', 'eyes', 'clothing', 'back']
FOLDER = {'body': 'bodies', 'head': 'head', 'eyes': 'eyes', 'clothing': 'clothing', 'back': 'back'}
# Eyes traits that are only a face texture, and the face texture each eyewear model sits over (as on the website)
EYE_OVERLAYS = ['red_pupils', 'gold_pupils', 'purple_pupils', 'ghostly']
EYE_BASE = {'eye_patch': 'red_pupils', 'monacle': 'red_pupils', 'tracker_blue': 'red_pupils', 'tracker_purple': 'red_pupils',
            'lazer': 'lazer_glow', 'neon_beam': 'neon_beam_glow'}
KEEP = ('name', 'from', 'to', 'origin', 'rotation', 'stretch', 'faces')


def key(s):
    return re.sub(r'[^a-z0-9]+', '_', s.lower()).strip('_')


def res(path):
    return 'res://' + path.relative_to(GAME).as_posix()


def has_soft_alpha(png):
    """True if the texture has see-through pixels that are not fully clear (lenses), so it needs blending."""
    hist = Image.open(png).convert('RGBA').getchannel('A').histogram()
    return sum(hist[10:246]) > 0


names = {}
section = None
for line in (REPO / 'docs/implingz_collection.md').read_text(encoding='utf8').splitlines():
    m = re.match(r'## \d+\. (\w+)', line)
    if m:
        section = m.group(1).lower()
    m = re.match(r'\| ([^|]+?) \| [\d,]+ \(', line)
    if m and section in TYPES:
        names[(section, key(m.group(1)))] = m.group(1)


def slim(model):
    elements = [{k: e[k] for k in KEEP if k in e} for e in model['elements']]
    for e in elements:
        e['faces'] = {f: {'uv': fc['uv']} for f, fc in e['faces'].items() if fc.get('texture') is not None}
    groups = {g['uuid']: {'name': g['name'], 'origin': g['origin'], 'rotation': g.get('rotation', [0, 0, 0])} for g in model['groups']}
    index = {e['uuid']: i for i, e in enumerate(model['elements'])}

    def tree(n):
        if isinstance(n, str):
            return index[n]
        return {**groups[n['uuid']], 'children': [tree(k) for k in n['children']]}
    t = model['textures'][0]
    return {'texture': [t['uv_width'], t['uv_height']], 'elements': elements, 'bones': [tree(n) for n in model['outliner']]}


if OUT.exists():
    shutil.rmtree(OUT)
(OUT / 'models').mkdir(parents=True)

manifest = {t: [] for t in TYPES}
for ty in TYPES:
    tex_dir = ASSETS / 'textures/impz' / FOLDER[ty]
    for src in sorted((ASSETS / 'models/impz' / FOLDER[ty]).glob('*.bbmodel')):
        fid = src.stem                                   # body_green, head_afro, eyes_lazer ...
        short = fid.split('_', 1)[1]
        model = json.loads(src.read_text(encoding='utf8'))
        (OUT / 'models' / f'{fid}.json').write_text(json.dumps(slim(model), separators=(',', ':')), encoding='utf8')
        png = tex_dir / f'{fid}.png'
        entry = {'id': fid, 'name': names.get((ty, short), short.replace('_', ' ').title()),
                 'model': res(OUT / 'models' / f'{fid}.json'), 'texture': res(png), 'blend': has_soft_alpha(png)}
        if ty == 'eyes' and short in EYE_BASE:
            entry['overlay'] = res(tex_dir / f'eyes_{EYE_BASE[short]}.png')
        manifest[ty].append(entry)
    if ty == 'eyes':
        for short in EYE_OVERLAYS:
            manifest[ty].append({'id': f'eyes_{short}', 'name': names[(ty, short)], 'overlay': res(tex_dir / f'eyes_{short}.png')})
    manifest[ty].sort(key=lambda e: e['name'].lower())
    unnamed = [e['id'] for e in manifest[ty] if (ty, e['id'].split('_', 1)[1]) not in names]
    assert not unnamed, f'no doc name for {unnamed}'
    missing = [p for e in manifest[ty] for p in (e.get('texture'), e.get('overlay')) if p and not (GAME / p[6:]).exists()]
    assert not missing, f'missing textures {missing}'
    print(f'{ty}: {len(manifest[ty])} options')

(OUT / 'manifest.json').write_text(json.dumps(manifest, indent=1), encoding='utf8')
size = sum(f.stat().st_size for f in OUT.rglob('*') if f.is_file())
print(f'wrote {OUT}  ({size / 1024:.0f} KB)')
