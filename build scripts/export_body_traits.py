"""Copy the approved Imp bodies into the repo as body_<colour>. Paint and geometry are copied as they are, not rebuilt."""
import base64, io, json, os, shutil, uuid
import numpy as np
from pathlib import Path
from PIL import Image
from build_imp_bodies import OUT as SRC, REPO as ASSETS

MODELS = ASSETS + 'models/impz/bodies/'
TEXTURES = ASSETS + 'textures/impz/bodies/'
COLOURS = ['blue', 'cyan', 'diamond', 'gold', 'green', 'khaki', 'pink', 'purple', 'red', 'silver']
REL = '../../../textures/impz/bodies/'

os.makedirs(MODELS, exist_ok=True)
os.makedirs(TEXTURES, exist_ok=True)
for c in COLOURS:
    d = json.load(open(f'{SRC}{c}_imp.bbmodel', encoding='utf8'))
    fn = 'body_' + c
    d['name'] = fn
    t = d['textures'][0]
    t.update(name=fn + '.png', relative_path=REL + fn + '.png', uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/bodies/' + fn)))
    with open(MODELS + fn + '.bbmodel', 'w', encoding='utf8', newline='') as f:
        json.dump(d, f, separators=(',', ':'))
    shutil.copyfile(f'{SRC}{c}_imp.png', TEXTURES + fn + '.png')

# ---------- verify from what is on disk
ref = None
for c in COLOURS:
    fn = 'body_' + c
    new = json.load(open(MODELS + fn + '.bbmodel', encoding='utf8'))
    old = json.load(open(f'{SRC}{c}_imp.bbmodel', encoding='utf8'))
    assert new['elements'] == old['elements'] and new['groups'] == old['groups'] and new['outliner'] == old['outliner'], c
    t = new['textures'][0]
    assert t['source'] == old['textures'][0]['source'], c
    embedded = np.array(Image.open(io.BytesIO(base64.b64decode(t['source'].split(',', 1)[1]))).convert('RGBA'))
    png = TEXTURES + fn + '.png'
    assert np.array_equal(embedded, np.array(Image.open(png).convert('RGBA'))), c
    assert os.path.exists(os.path.normpath(os.path.join(MODELS, t['relative_path']))), c
    assert new['name'] == fn and t['name'] == fn + '.png', c
    # the customizer's contract: every body is the same rig, only the texture differs
    rig = (new['elements'], new['groups'], new['outliner'], new['resolution'], new['meta'])
    ref = ref or rig
    assert rig == ref, c + ' rig differs'
    print(f"{fn}.bbmodel  {len(new['elements'])} cubes  {len(new['groups'])} groups  texture ok")
print('all', len(COLOURS), 'bodies share one identical rig and UV layout')
horns = [e['name'] for e in ref[0] if e['name'].startswith('horn_')]
print(sorted(horns))
