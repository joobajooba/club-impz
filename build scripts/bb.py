"""Drive a throwaway Blockbench (own profile, own debug port) so models can be tested in the real app.
Never touches the user's window, settings or plugins folder."""
import base64, json, os, subprocess, time, urllib.request, sys
import websocket

EXE = r'C:\Users\lucas\AppData\Local\Programs\Blockbench\Blockbench.exe'
PLUGIN = r'C:\Users\lucas\AppData\Roaming\Blockbench\plugins\hytale_plugin.js'
HERE = os.path.dirname(os.path.abspath(__file__))
PROFILE = os.path.join(HERE, 'bb_profile')
PORT = 9444


class BB:
    def __init__(self):
        self.proc = None
        self.ws = self._connect(1.0)
        if not self.ws:
            os.makedirs(PROFILE, exist_ok=True)
            self.proc = subprocess.Popen([EXE, f'--user-data-dir={PROFILE}', f'--remote-debugging-port={PORT}', '--remote-allow-origins=*'])
            self.ws = self._connect(60)
        assert self.ws, 'could not connect'
        self.n = 0

    def _connect(self, wait):
        end = time.time() + wait
        while time.time() < end:
            try:
                targets = json.load(urllib.request.urlopen(f'http://127.0.0.1:{PORT}/json/list', timeout=2))
                pages = [t for t in targets if t.get('type') == 'page' and 'webSocketDebuggerUrl' in t]
                if pages:
                    return websocket.create_connection(pages[0]['webSocketDebuggerUrl'], timeout=120, suppress_origin=True)
            except Exception:
                pass
            time.sleep(.5)
        return None

    def call(self, method, **params):
        self.n += 1
        self.ws.send(json.dumps({'id': self.n, 'method': method, 'params': params}))
        while True:
            r = json.loads(self.ws.recv())
            if r.get('id') == self.n:
                return r

    def js(self, code):
        r = self.call('Runtime.evaluate', expression=f'(async()=>{{{code}}})()', awaitPromise=True, returnByValue=True)
        if 'exceptionDetails' in r.get('result', {}):
            raise RuntimeError(json.dumps(r['result']['exceptionDetails'])[:800])
        return r['result']['result'].get('value')

    def wait_ready(self):
        for _ in range(120):
            try:
                if self.js("return typeof Blockbench !== 'undefined' && typeof Cube !== 'undefined' && !!Interface.data && document.readyState === 'complete'"):
                    return True
            except Exception:
                pass
            time.sleep(.5)
        return False

    def load_plugin(self):
        p = json.dumps(PLUGIN)
        return self.js(f"""
            if (typeof Formats !== 'undefined' && Formats.hytale_character) return 'already';
            const plugin = new Plugin('hytale_plugin');
            await plugin.loadFromFile({{path: {p}}}, false);
            return Object.keys(Formats).filter(k => k.includes('hytale')).join(',');""")

    def open(self, path):
        p = json.dumps(path)
        content = json.dumps(open(path, encoding='utf8').read())
        return self.js(f"""
            for (const pr of [...ModelProject.all]) {{ pr.saved = true; await pr.close(true); }}
            loadModelFile({{content: {content}, path: {p}, name: {p}.split(/[\\/]/).pop()}});
            await new Promise(r => setTimeout(r, 1500));
            return {{format: Format.id, cubes: Cube.all.length, textures: Texture.all.map(t => [t.name, t.width, t.height, t.uv_width, t.uv_height, t.loaded, !!t.error])}};""")

    def shot(self, out):
        r = self.call('Page.captureScreenshot', format='png')
        with open(out, 'wb') as f:
            f.write(base64.b64decode(r['result']['data']))

    def camera(self, pos, target):
        return self.js(f"""
            const p = Preview.selected;
            p.setProjectionMode && p.setProjectionMode(false);
            p.camera.position.set({pos[0]},{pos[1]},{pos[2]});
            p.controls.target.set({target[0]},{target[1]},{target[2]});
            p.controls.update(); p.render();
            await new Promise(r => setTimeout(r, 400));
            return true;""")
