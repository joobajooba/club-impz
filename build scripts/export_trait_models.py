"""Copy the approved Head, Back, Clothing and Eyes traits into the repo, as export_body_traits.py did for bodies.
Geometry and paint are copied as they are. Each texture stays embedded and also gets a relative_path to its PNG.
Showcases and the eyes_3d_glasses_on_body preview stay out: they only view traits that are already here."""
import base64, io, json, os, shutil, glob
import numpy as np
from PIL import Image

SRC = 'C:/Users/lucas/blockbench_models/impz/'
ASSETS = 'C:/Users/lucas/club-impz/godot-game/assets/'
TYPES = ['head', 'back', 'clothing', 'eyes']

for ty in TYPES:
    models, textures = f'{ASSETS}models/impz/{ty}/', f'{ASSETS}textures/impz/{ty}/'
    os.makedirs(models, exist_ok=True); os.makedirs(textures, exist_ok=True)
    rel = f'../../../textures/impz/{ty}/'
    names = sorted(os.path.basename(p)[:-8] for p in glob.glob(f'{SRC}{ty}/*.bbmodel'))
    names = [n for n in names if not n.endswith(('_showcase', '_on_body'))]
    for n in names:
        d = json.load(open(f'{SRC}{ty}/{n}.bbmodel', encoding='utf8'))
        assert d['name'] == n and len(d['textures']) == 1, n
        d['textures'][0]['relative_path'] = rel + n + '.png'
        with open(models + n + '.bbmodel', 'w', encoding='utf8', newline='') as f:
            json.dump(d, f, separators=(',', ':'))
    # every PNG of a model, plus texture-only traits (pupil colours) and glow masks
    pngs = sorted(os.path.basename(p) for p in glob.glob(f'{SRC}{ty}/*.png'))
    pngs = [p for p in pngs if not p[:-4].endswith(('_showcase', '_on_body'))]
    for p in pngs:
        shutil.copyfile(f'{SRC}{ty}/{p}', textures + p)
    # verify from disk
    for n in names:
        new = json.load(open(models + n + '.bbmodel', encoding='utf8'))
        old = json.load(open(f'{SRC}{ty}/{n}.bbmodel', encoding='utf8'))
        assert new['elements'] == old['elements'] and new['outliner'] == old['outliner'], n
        t = new['textures'][0]
        emb = np.array(Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA'))
        assert np.array_equal(emb, np.array(Image.open(textures + n + '.png').convert('RGBA'))), n
        assert os.path.exists(os.path.normpath(os.path.join(models, t['relative_path']))), n
    extra = [p for p in pngs if p[:-4] not in names]
    print(f'{ty}: {len(names)} models, {len(pngs)} textures, texture-only: {extra}')
