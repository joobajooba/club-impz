"""Hub NPCs (J00BA, 2026-11-14): name the copied NPC models for the repo (texture embedded, png beside in textures/npcs)
and write the glb export jobs. Run after copying the .bbmodel/.png files from ~/blockbench_models/npcs.
The green-robed merchant becomes hooded_merchant_npc: the repo already has an older, unused merchant_npc."""
import json, sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
M = REPO / 'godot-game/assets/models/npcs'
NAMES = ['skeleton_king_npc', 'hooded_merchant_npc', 'princess_merchant_npc', 'princess_imp_npc', 'jester_imp_npc',
         'potion_seller_imp_npc', 'lumberjack_imp_npc', 'miner_imp_npc']
for n in NAMES:
    p = M / f'{n}.bbmodel'
    d = json.load(open(p, encoding='utf8'))
    d['name'] = n
    t = d['textures'][0]
    t['name'] = n + '.png'
    t.pop('relative_path', None)
    json.dump(d, open(p, 'w', encoding='utf8'), indent='\t')
jobs = [[(M / f'{n}.bbmodel').as_posix(), (M / f'{n}.glb').as_posix(), True] for n in NAMES]
out = Path(sys.argv[1])
out.write_text(json.dumps(jobs), encoding='utf8')
print('jobs', len(jobs), '->', out)
