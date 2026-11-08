"""Bring an exported Blockbench .glb up to date after fix_texture_bleed.py padded its .bbmodel, without
re-exporting: geometry, normals, indices, nodes and animations stay byte for byte; only the embedded
texture is swapped for the padded one and each face's UVs move by the same whole pixels its island moved.

Checked against real Blockbench 5.2.2 glTF exports of the padded models (binary, texture embedded):
same JSON, same geometry and animation data, same UVs, same visible texture pixels.

Usage: python repad_glb.py <old.glb> <old.bbmodel> <new.bbmodel> <out.glb>
"""
import base64, io, json, struct, sys
import numpy as np
from PIL import Image

from uv_padding import pixel_rect, textured_faces

CT = {5120: np.int8, 5121: np.uint8, 5122: np.int16, 5123: np.uint16, 5125: np.uint32, 5126: np.float32}
NC = {'SCALAR': 1, 'VEC2': 2, 'VEC3': 3, 'VEC4': 4, 'MAT4': 16}


def read_glb(path):
    b = open(path, 'rb').read()
    n = struct.unpack_from('<I', b, 12)[0]
    js = json.loads(b[20:20 + n])
    off = 20 + n
    bl = struct.unpack_from('<I', b, off)[0]
    return js, bytearray(b[off + 8: off + 8 + bl])


def write_glb(path, js, views):
    """views: the bytes of every bufferView, in order. Lays them out again, 4-byte aligned."""
    binc = bytearray()
    for v, data in zip(js['bufferViews'], views):
        while len(binc) % 4:
            binc.append(0)
        v['byteOffset'] = len(binc)
        v['byteLength'] = len(data)
        binc += data
    while len(binc) % 4:
        binc.append(0)
    js['buffers'][0]['byteLength'] = len(binc)
    j = json.dumps(js, separators=(',', ':')).encode()
    j += b' ' * (-len(j) % 4)
    out = struct.pack('<III', 0x46546C67, 2, 12 + 8 + len(j) + 8 + len(binc))
    out += struct.pack('<II', len(j), 0x4E4F534A) + j + struct.pack('<II', len(binc), 0x004E4942) + bytes(binc)
    open(path, 'wb').write(out)


def texture(d):
    s = d['textures'][0]['source']
    return np.array(Image.open(io.BytesIO(base64.b64decode(s.split(',', 1)[1]))).convert('RGBA'))


def glb_png(T):
    """What Blockbench's exporter embeds: the texture drawn through a canvas (colour of fully clear texels lost)."""
    T = T.copy()
    T[T[..., 3] == 0] = 0
    b = io.BytesIO()
    Image.fromarray(T).save(b, 'PNG')
    return b.getvalue()


def repad(old_glb, old_model, new_model, out_glb):
    a = json.load(open(old_model, encoding='utf8'))
    b = json.load(open(new_model, encoding='utf8'))
    Ta, Tb = texture(a), texture(b)
    sa = (Ta.shape[1] / float(a['textures'][0].get('uv_width') or Ta.shape[1]), Ta.shape[0] / float(a['textures'][0].get('uv_height') or Ta.shape[0]))
    sb = (Tb.shape[1] / float(b['textures'][0].get('uv_width') or Tb.shape[1]), Tb.shape[0] / float(b['textures'][0].get('uv_height') or Tb.shape[0]))
    move = {}
    for (_, _, fa), (_, _, fb) in zip(textured_faces(a), textured_faces(b)):
        ra, rb = pixel_rect(fa['uv'], *sa), pixel_rect(fb['uv'], *sb)
        d = (rb[0] - ra[0], rb[1] - ra[1])
        assert move.setdefault(tuple(ra), d) == d, f'{old_model}: one UV rectangle moved two ways'
    js, binc = read_glb(old_glb)
    views = [bytes(binc[v.get('byteOffset', 0): v.get('byteOffset', 0) + v['byteLength']]) for v in js['bufferViews']]
    done = set()
    Wa, Ha = Ta.shape[1], Ta.shape[0]
    Wb, Hb = Tb.shape[1], Tb.shape[0]
    for mesh in js['meshes']:
        for prim in mesh['primitives']:
            i = prim['attributes'].get('TEXCOORD_0')
            if i is None or i in done:
                continue
            done.add(i)
            acc = js['accessors'][i]
            assert acc['componentType'] == 5126 and acc['type'] == 'VEC2' and js['bufferViews'][acc['bufferView']].get('byteStride', 8) == 8
            raw = bytearray(views[acc['bufferView']])
            off = acc.get('byteOffset', 0)
            uv = np.frombuffer(bytes(raw[off: off + acc['count'] * 8]), np.float32).reshape(-1, 2).astype(np.float64)
            px = uv * [Wa, Ha]
            out = uv.copy()
            assert len(uv) % 4 == 0, f'{old_glb}: vertices are not in quads'
            for q in range(0, len(uv), 4):
                p = px[q:q + 4]
                rect = (int(round(p[:, 0].min())), int(round(p[:, 1].min())), int(round(p[:, 0].max())), int(round(p[:, 1].max())))
                if rect not in move:
                    if rect[0] == rect[2] or rect[1] == rect[3] or rect == (0, 0, Wa, Ha):
                        continue  # an untextured face: Blockbench writes 0..1 or nothing, at any texture size
                    raise ValueError(f'{old_glb}: quad UV {rect} is not a face of {old_model}')
                dx, dy = move[rect]
                out[q:q + 4] = (p + [dx, dy]) / [Wb, Hb]
            o32 = out.astype(np.float32)
            raw[off: off + acc['count'] * 8] = o32.tobytes()
            views[acc['bufferView']] = bytes(raw)
            if 'min' in acc:
                acc['min'] = [float(x) for x in o32.min(0)]
                acc['max'] = [float(x) for x in o32.max(0)]
    assert len(js.get('images', [])) == 1, f'{old_glb}: expected one embedded image'
    views[js['images'][0]['bufferView']] = glb_png(Tb)
    write_glb(out_glb, js, views)


if __name__ == '__main__':
    repad(*sys.argv[1:5])
