"""Export .bbmodel files to .glb in a throwaway Blockbench. args: jobs.json|json [--resume]
jobs: [[bbmodel, out_glb, animations(bool)], ...]. One project tab is reused: close it (awaited), then load."""
import json, sys, base64, os, time
sys.path.insert(0, "C:/Users/lucas/club-impz/build scripts")
from bb import BB
b = BB(); b.wait_ready(); b.load_plugin()
b.ws.settimeout(60)
jobs = json.loads(open(sys.argv[1]).read()) if sys.argv[1].endswith('.json') else json.loads(sys.argv[1])
for src, out, anim in jobs:
    if os.path.exists(out) and '--resume' in sys.argv:
        continue
    t0 = time.time()
    content = json.dumps(open(src, encoding='utf8').read())
    info = b.js(f'''
        const t = [performance.now()];
        for (const pr of [...ModelProject.all]) {{
            pr.saved = true; for (const tx of pr.textures || []) tx.saved = true;
            await pr.close(true);
        }}
        t.push(performance.now());
        loadModelFile({{content: {content}, path: {json.dumps(src)}, name: {json.dumps(src.split('/')[-1])}}});
        for (let i = 0; i < 200 && !(Project && Texture.all.length && Texture.all.every(t => t.img && t.img.complete && t.img.naturalWidth > 0)); i++) await new Promise(r => setTimeout(r, 25));
        t.push(performance.now());
        return [Format.id, Cube.all.length, Texture.all.length, ModelProject.all.length, t.map((x, i) => i ? Math.round(x - t[i - 1]) : 0)];''')
    r = b.js(f"""
        const t0 = performance.now();
        const opts = {{encoding: 'binary', embed_textures: true, animations: {str(bool(anim)).lower()}, armature: false, scale: Settings.get('model_export_scale')}};
        const res = await Codecs.gltf.compile(opts);
        const bytes = new Uint8Array(res);
        let s = ''; for (let i = 0; i < bytes.length; i += 32768) s += String.fromCharCode.apply(null, bytes.subarray(i, i + 32768));
        return [btoa(s), Cube.all.length, Math.round(performance.now() - t0)];""")
    open(out, 'wb').write(base64.b64decode(r[0]))
    print(out, len(r[0]) * 3 // 4, 'cubes', r[1], 'load', info, 'export ms', r[2], 'total s', round(time.time() - t0, 1), flush=True)
