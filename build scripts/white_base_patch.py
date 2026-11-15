"""J00BA (2026-11-14): the White Imp is the base model for players without traits. They wear it until they pick traits
their wallet holds. One-off patch: copies body_white into the repo, names it in the manifest export, and switches the
game's and the server's base look from body_green to body_white. Green becomes an ordinary held body."""
import json, shutil, uuid
from pathlib import Path
import numpy as np
from PIL import Image

REPO = Path(__file__).resolve().parent.parent
G = REPO / 'godot-game'
SRC = Path.home() / 'blockbench_models' / 'impz'


def edit(path, pairs):
    t = path.read_text(encoding='utf8')
    for a, b in pairs:
        assert t.count(a) == 1, (path.name, a[:70])
        t = t.replace(a, b)
    path.write_text(t, encoding='utf8', newline='\n')


# ---- the model and texture, named like the other bodies (same rig and UVs as body_green)
d = json.load(open(SRC / 'white_imp.bbmodel', encoding='utf8'))
green = json.load(open(G / 'assets/models/impz/bodies/body_green.bbmodel', encoding='utf8'))
assert d['elements'] == [dict(e) for e in d['elements']]
for k in ('elements', 'groups', 'outliner'):
    a = json.dumps([{kk: vv for kk, vv in e.items() if kk not in ('faces',)} for e in d[k]] if k == 'elements' else d[k], sort_keys=True)
    b = json.dumps([{kk: vv for kk, vv in e.items() if kk not in ('faces',)} for e in green[k]] if k == 'elements' else green[k], sort_keys=True)
    assert a == b, f'white rig differs from green in {k}'
d['name'] = 'body_white'
t = d['textures'][0]
t.update(name='body_white.png', relative_path='../../../textures/impz/bodies/body_white.png',
         uuid=str(uuid.uuid5(uuid.NAMESPACE_URL, 'club-impz/bodies/body_white')))
with open(G / 'assets/models/impz/bodies/body_white.bbmodel', 'w', encoding='utf8', newline='') as f:
    json.dump(d, f, separators=(',', ':'))
shutil.copyfile(SRC / 'white_imp.png', G / 'assets/textures/impz/bodies/body_white.png')

# ---- the manifest export: White has no row in the collection doc's trait tables, so it is named here
edit(REPO / 'build scripts/export_imp_customizer.py', [
    ("""        names[(section, key(m.group(1)))] = m.group(1)
""", """        names[(section, key(m.group(1)))] = m.group(1)
# White is not a collection body: it is the base Imp every player wears until they pick held traits (J00BA, 2026-11-14)
names[('body', 'white')] = 'White'
"""),
])

# ---- the game: the base look is the White body
edit(G / 'scripts/impz/imp_builder.gd', [
    ('const DEFAULT := {body = "body_green", head = "", eyes = "", clothing = "", back = ""}',
     '## The base Imp every player wears until they pick traits their wallet holds: the White body (J00BA, 2026-11-14).\n'
     'const DEFAULT := {body = "body_white", head = "", eyes = "", clothing = "", back = ""}'),
])
edit(G / 'scripts/player/imp_visual.gd', [
    ('_look().get("body", "body_green")', '_look().get("body", ImpBuilder.DEFAULT.body)'),
])
edit(G / 'autoload/look.gd', [
    ("## swapped for the base imp's (Green body, no traits), so selling an Imp locks its traits again.",
     "## swapped for the base imp's (White body, no traits), so selling an Imp locks its traits again. The White body is\n"
     "## everyone's; Green and the other collection bodies are held traits like any other."),
])

# ---- the server: guests and anything not held fall back to the White body
S = REPO / 'game-server'
edit(S / 'server.mjs', [
    ('const BASE_LOOK = { body: "body_green", head: "", eyes: "", clothing: "", back: "" };',
     '// The base Imp: the White body, which every player has (J00BA, 2026-11-14). Green is a held trait like the others.\n'
     'const BASE_LOOK = { body: "body_white", head: "", eyes: "", clothing: "", back: "" };'),
])
edit(S / 'test/smoke.mjs', [
    ('check(wa?.look.body === "body_green" && wa?.look.head === "", "guests wear the base Imp, made-up traits refused");',
     'check(wa?.look.body === "body_white" && wa?.look.head === "", "guests wear the base (White) Imp, made-up traits refused");'),
])

# ---- the doc
edit(REPO / 'docs/game_direction.md', [
    ("- **Anyone can play for free.** Every player gets a **base imp** to play as. No wallet or NFT is needed.",
     "- **Anyone can play for free.** Every player gets a **base imp** to play as: the **White Imp** (decided by J00BA,\n"
     "  2026-11-14). Players wear it until they pick traits from Impz they hold. No wallet or NFT is needed."),
])
print('white base patch applied')
