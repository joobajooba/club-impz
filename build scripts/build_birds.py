"""Birds (blockbench_detailed_prompts.md section 3.9, bird rig; the eagle and pigeon references set the texture
bar): pigeon, seagull, eagle, heron, swan, crow, barn owl, snowy owl, mallard duck and robin.

Rig (the doc's bird row): <bird> > body > head (beak), wing_right > wing_tip_right, wing_left > wing_tip_left,
tail ; leg_right, leg_left ; scale_dummy. Long necks (heron, swan) are part of the head, pivoting at the neck base.

Wings fold and spread with one rig:
  folded (rest)  the inner wing is a slab hanging against the body side from the shoulder; the wing tip lies back
                 along the body from the wrist (the primaries cross over the tail, like a perched bird)
  spread         wing_right z +90 / wing_left z -90 swings the inner wing out flat; wing_tip x +90 unfolds the tip
                 so it carries the line on (Blockbench keyframes, measured: +x swings a hanging part forward)
The trailing edges are alpha feather fringes; eagle, heron and crow have separate primary "fingers".

Animations: idle, walk, run, attack (peck with wings half open), hit, fly (flap), glide, takeoff, land,
and swim for the swan, duck and seagull. 2 px/unit, one texture (128, or 256 for the big birds), faces
painted as overlapping feather rows (light tips, dark bases), eyes with a highlight pixel.
Usage: py -3 build_birds.py [pigeon ...]   (no args = all)
"""
import base64, io, json, math, os, random, sys, uuid
import numpy as np
from PIL import Image

OUT = r"C:\Users\lucas\blockbench_models\mobs\birds"
REPO_SCRIPTS = r"C:\Users\lucas\club-impz\build scripts"
PPU = 2
R = lambda s: s.split()


def hexc(h): h = h.lstrip("#"); return tuple(int(h[i:i + 2], 16) for i in (0, 2, 4))
def h2(v): return round(v * 2) / 2


# ------------------------------------------------------------------ species
# dims in Blockbench units (imp = 18 tall). body (w, h, l, y0); head (w, h, l); neck: [(dz, h, w, lean)] cubes from
# the body front up to the head; beak (len, w, h, hook); leg (len, thick); wing (inner height, chord, tip length,
# tip height, fingers); tail (w, len, fan). ramps dark -> light.
BIRDS = {
    "pigeon": dict(body=(5, 5, 8, 2.5), head=(3.5, 3.5, 3.5), neck=[(0, 2.0, 3.5, 0)], beak=(1.5, 1, 1, False), leg=(2.5, 1),
                   wing=(4.5, 6, 5, 3, 0), tail=(4, 4.5, False), eye="#ff8a2a", tex=128,
                   ramps=dict(body="#3c4458 #4e586e #626c84 #78829a #8e98b0 #a6aec4 #bec6d8", belly="#4a5266 #5e687e #747e96 #8c96ac #a4acc0",
                              head="#3c4458 #4e586e #626c84 #78829a #8e98b0", neck="#2c4a46 #3a6a5e #5a8a6e #7a5a8e #9a7aaa",
                              wing="#3a4256 #4c566c #606a82 #768098 #8c96ae #a6aec2", tip="#22262e #30343e #424854 #565c6a",
                              tail="#2a2e38 #3a404e #505868 #687082", beak="#2a2a30 #3c3c44 #e8e2dc #f4f0ec", leg="#7a3a44 #a84e5a #d06c78 #e68a94"),
                   features=["neck_sheen", "wing_bars", "tail_band"]),
    "seagull": dict(body=(6, 6, 10, 3), head=(4, 4, 4.5), neck=[(0, 1.5, 3.5, 0)], beak=(3, 1, 1.5, True), leg=(3, 1),
                    wing=(6, 7, 9, 3.5, 0), tail=(5, 4.5, False), eye="#f2d23a", tex=128, swim=True,
                    ramps=dict(body="#9aa2ac #b4bcc6 #ccd2da #dde2e8 #ebeef2 #f6f8fa", belly="#a8b0ba #c4cad2 #dce0e6 #eef0f4 #f8fafc",
                               head="#a8b0ba #c4cad2 #dce0e6 #eef0f4 #f8fafc", neck="#a8b0ba #c4cad2 #dce0e6 #eef0f4 #f8fafc",
                               wing="#5e6a78 #74808e #8a96a4 #a2acb8 #b8c0ca #ccd2da", tip="#141418 #20222a #30323c #464a56",
                               tail="#a8b0ba #c4cad2 #dce0e6 #eef0f4", beak="#a87a10 #d4a018 #f0c832 #f8e070", leg="#9a5a5a #c27a72 #e09a8e #f0b8aa"),
                    features=["tip_spots", "beak_spot"]),
    "eagle": dict(body=(8, 9, 13, 5), head=(5.5, 5.5, 6), neck=[(0, 2.5, 5, 0)], beak=(3, 2, 2.5, True), leg=(5, 1.5),
                  wing=(8.5, 10, 13, 5, 5), tail=(7, 7, True), eye="#f0c030", tex=256,
                  ramps=dict(body="#1e120a #2e1c10 #3e2616 #50321e #644028 #7a5032 #90623e", belly="#1a1008 #28180e #382214 #4a2e1a #5c3a22",
                             head="#a8a49a #c4c0b4 #dcd8cc #ece8de #f6f4ec", neck="#a8a49a #c4c0b4 #dcd8cc #ece8de #f6f4ec",
                             wing="#1c1008 #2a180c #3a2212 #4c2e18 #603c22 #76502e #8c6438", tip="#120a06 #1e120a #2c1a0e #3c2414 #4e301c",
                             tail="#a8a49a #c4c0b4 #dcd8cc #ece8de #f6f4ec", beak="#8a6008 #b88010 #e0a81c #f4cc48 #fae486",
                             leg="#8a6008 #b88010 #e0a81c #f4cc48", claw="#14100c #282018 #403428"),
                  features=["talons"]),
    "heron": dict(body=(6, 6, 11, 14), head=(3.5, 3.5, 4.5), neck=[(0, 4, 2.5, 0), (-1.5, 4, 2.5, 0), (-2.5, 3, 2.5, 0)], beak=(5, 1, 1.5, False),
                  leg=(14, 1), wing=(7, 9, 11, 4, 4), tail=(4, 4, False), eye="#f2e24a", tex=256,
                  ramps=dict(body="#5a6270 #6e7684 #848c9a #9aa2ae #b0b6c0 #c6cbd2", belly="#9aa0aa #b4b8c0 #ccd0d6 #e2e4e8 #f0f2f4",
                             head="#b4b8c0 #ccd0d6 #e2e4e8 #f0f2f4 #f8f9fa", neck="#b4b8c0 #ccd0d6 #e2e4e8 #f0f2f4 #f8f9fa",
                             wing="#4a5260 #5a6270 #6e7684 #848c9a #9aa2ae #b0b6c0", tip="#1c2026 #282c34 #363c46 #4a505c",
                             tail="#5a6270 #6e7684 #848c9a #9aa2ae", beak="#8a6a10 #b88c1a #dcb030 #f0cc5a", leg="#5a4a20 #7a6430 #9a8044 #b89c5a",
                             plume="#0c0c10 #18181e #24242c #34343e"),
                  features=["eye_stripe", "plume", "neck_streak"]),
    "swan": dict(body=(8, 7, 14, 2.5), head=(3.5, 3.5, 4.5), neck=[(0, 4, 3, 0), (-1, 4, 2.5, 0), (-2.5, 3, 2.5, 0)], beak=(3.5, 1.5, 1.5, False),
                 leg=(2, 1.5), wing=(7, 11, 11, 4.5, 0), tail=(5, 3, False), eye="#2a2018", tex=256, swim=True,
                 ramps=dict(body="#a8b4c4 #c0cad6 #d4dce6 #e4eaf0 #f0f4f6 #f8fafb", belly="#9aa6b6 #b4bec8 #ccd4dc #e0e6ec #eef2f4",
                            head="#b4bec8 #ccd4dc #e0e6ec #eef2f4 #f8fafb", neck="#b4bec8 #ccd4dc #e0e6ec #eef2f4 #f8fafb",
                            wing="#9aa6b6 #b4bec8 #ccd4dc #e0e6ec #eef2f4 #f8fafb", tip="#a8b4c4 #c0cad6 #d8e0e8 #ecf0f4",
                            tail="#b4bec8 #ccd4dc #e0e6ec #eef2f4", beak="#a83a10 #d0541a #ec7428 #f89a48", leg="#141416 #202024 #303036 #44444c",
                            knob="#0e0e10 #1a1a1e #2a2a30"),
                 features=["knob"]),
    "crow": dict(body=(5, 5.5, 9, 3), head=(4, 4, 4), neck=[(0, 1.5, 3.5, 0)], beak=(2.5, 1.5, 1.5, False), leg=(3, 1),
                 wing=(5, 7, 7, 3.5, 4), tail=(4, 5, False), eye="#1a1418", tex=128,
                 ramps=dict(body="#0a0a10 #12121c #1a1c2a #24283a #30364c #3e4660", belly="#08080c #101018 #181a24 #22263a #2e3448",
                            head="#0a0a10 #12121c #1a1c2a #24283a #30364c", neck="#0a0a10 #12121c #1a1c2a #24283a #30364c",
                            wing="#08080e #10121a #181c28 #222838 #2e364a #3c4660", tip="#06060a #0e1016 #161a24 #202636",
                            tail="#08080e #10121a #181c28 #222838", beak="#0e0e12 #1a1a20 #2a2a32 #3c3c46", leg="#0e0e12 #1a1a20 #2a2a32 #3c3c46"),
                 features=["sheen"]),
    "owl": dict(body=(7, 8, 7, 2.5), head=(7, 6, 6), neck=[], beak=(1, 1, 1.5, True), leg=(2.5, 1.5),
                wing=(6.5, 6, 6, 3.5, 0), tail=(5, 3, False), eye="#1a1210", tex=128, front_eyes=True,
                ramps=dict(body="#7a4a1c #9a6026 #b87a34 #cc9446 #dcac5e #e8c47e", belly="#c8b490 #dccaa8 #ece0c4 #f6eedc #fbf7ee",
                           head="#7a4a1c #9a6026 #b87a34 #cc9446 #dcac5e", neck="#7a4a1c #9a6026 #b87a34 #cc9446",
                           wing="#6a4018 #8a5622 #a86e2e #c08840 #d4a256 #e2bc74", tip="#5a3614 #7a4a1c #9a6026 #b87a34",
                           tail="#7a4a1c #9a6026 #b87a34 #cc9446", beak="#a89070 #c4ac8a #dcc8a8 #ece0c8", leg="#d8ccb4 #e8dec8 #f4ecdc",
                           disc="#c8b8a8 #dccec0 #ece4da #f6f2ec #fbf9f6", rim="#6a4018 #8a5622 #a86e2e"),
                features=["face_disc", "speckles"]),
    "snowy_owl": dict(body=(7.5, 8.5, 7.5, 2.5), head=(7, 6, 6), neck=[], beak=(1, 1, 1.5, True), leg=(2.5, 2),
                      wing=(7, 6.5, 6.5, 3.5, 0), tail=(5, 3, False), eye="#f2c41a", tex=128, front_eyes=True,
                      ramps=dict(body="#a8b0bc #c2c8d2 #d8dde4 #e8ecf0 #f4f6f8 #fbfcfd", belly="#b8c0ca #d2d8e0 #e6eaee #f4f6f8 #fcfdfe",
                                 head="#b8c0ca #d2d8e0 #e6eaee #f4f6f8 #fcfdfe", neck="#b8c0ca #d2d8e0 #e6eaee #f4f6f8",
                                 wing="#a0a8b4 #bac2cc #d2d8e0 #e6eaee #f4f6f8 #fbfcfd", tip="#9aa2ae #b4bcc6 #ccd2da #e2e6ea",
                                 tail="#b8c0ca #d2d8e0 #e6eaee #f4f6f8", beak="#1e1e22 #2c2c32 #3e3e46 #54545e", leg="#dce0e6 #ecf0f2 #f8fafb",
                                 disc="#d2d8e0 #e6eaee #f4f6f8 #fcfdfe", rim="#a0a8b4 #bac2cc #d2d8e0"),
                      features=["face_disc", "dark_bars"]),
    "duck": dict(body=(6, 5, 10, 2), head=(4, 4, 4.5), neck=[(0, 2, 3, 0)], beak=(3, 2, 1, False), leg=(2, 1),
                 wing=(5, 7, 6, 3, 0), tail=(4, 2.5, False), eye="#1c1410", tex=128, swim=True,
                 ramps=dict(body="#6a6a6e #808084 #96969a #acacb0 #c2c2c4 #d4d4d6", belly="#7a7a7e #929296 #aaaaae #c2c2c6 #d6d6d8",
                            head="#0a2a16 #10401e #186028 #228034 #3aa04a", neck="#c8c8cc #dcdce0 #eeeef0 #f8f8fa",
                            chest="#3a1a10 #5a2a18 #7a3c22 #9a5030 #b46640", wing="#4a4a50 #5e5e64 #74747a #8a8a90 #a0a0a6 #b4b4ba",
                            tip="#3a3a40 #4c4c52 #606066 #76767c", tail="#16161a #24242a #34343c #46464e", beak="#7a6a10 #a8901a #d0b42a #e8d050",
                            leg="#a84a10 #d0661a #ec8a2a #f8aa4a", spec="#10247a #1a3aa8 #2a5ad0 #4a80ec"),
                 features=["neck_ring", "chest", "speculum", "head_sheen"]),
    "robin": dict(body=(4, 4, 6, 2.5), head=(3.5, 3.5, 3.5), neck=[], beak=(1.5, 0.5, 0.5, False), leg=(2.5, 0.5),
                  wing=(3.5, 4.5, 3.5, 2, 0), tail=(3, 3.5, False), eye="#120c0a", tex=128,
                  ramps=dict(body="#3a2a1c #4e3a26 #644c32 #7a5e40 #907050 #a68462", belly="#c8beb0 #dcd2c6 #ece6dc #f6f2ec",
                             head="#3a2a1c #4e3a26 #644c32 #7a5e40 #907050", neck="#3a2a1c #4e3a26 #644c32 #7a5e40",
                             chest="#8a2a0e #b03e14 #d0581c #e6742c #f2944a", wing="#2e2014 #42301e #584028 #6e5234 #846440",
                             tip="#241810 #342418 #463222 #5a422e", tail="#2e2014 #42301e #584028 #6e5234", beak="#1a1612 #2a241e #3c342c",
                             leg="#3a2e26 #544438 #6e5c4c"),
                 features=["chest", "face_orange"]),
}

FACES = ("north", "east", "south", "west", "up", "down")
FACE_LIGHT = {"up": 1.2, "north": 0.4, "west": 0.5, "south": -0.1, "east": -0.2, "down": -1.4}


def face_dims(frm, to, face):
    dx, dy, dz = (to[i] - frm[i] for i in range(3))
    return {"north": (dx, dy), "south": (dx, dy), "east": (dz, dy), "west": (dz, dy), "up": (dx, dz), "down": (dx, dz)}[face]


def px(u):
    v = u * PPU
    assert abs(v - round(v)) < 1e-6, f"non integer pixel size {u}"
    return max(1, int(round(v)))


def uvgrid(w, h):
    U, V = np.meshgrid((np.arange(w) + 0.5) / w, (np.arange(h) + 0.5) / h)
    return U, V, np.minimum(np.minimum(U, 1 - U) * w, np.minimum(V, 1 - V) * h)


def dither(v, w, h):
    bayer = np.array([[0, 2], [3, 1]]) / 4.0 - 0.375
    return v + np.tile(bayer, (h // 2 + 1, w // 2 + 1))[:h, :w] * 0.5


def build(name):
    S = BIRDS[name]
    rng = random.Random(hash(name) & 0xffff)
    nrng = np.random.default_rng(hash(name) & 0xffff)
    RAMPS = {k: [hexc(c) for c in v.split()] for k, v in S["ramps"].items()}
    RAMPS["eye_white"] = [hexc(c) for c in "#c8c4b8 #e4e0d6 #f4f2ee".split()]
    RAMPS["iris"] = [hexc(S["eye"])]

    def rc(ramp, v):
        r = RAMPS[ramp]; n = len(r)
        q = np.clip(np.round(np.asarray(v, float) * 2) / 2, 0, n - 1)
        lo = np.floor(q).astype(int); hi = np.minimum(lo + 1, n - 1); f = (q - lo)[..., None]
        return (np.array(r)[lo] * (1 - f) + np.array(r)[hi] * f).round().astype(np.uint8)

    elements, groups = [], {}

    def nu(): return str(uuid.UUID(int=rng.getrandbits(128), version=4))

    def group(gname, origin, parent=None):
        groups[gname] = {"name": gname, "uuid": nu(), "origin": [round(v, 3) for v in origin], "children": []}
        if parent: groups[parent]["children"].append(("g", gname))
        return gname

    def cube(cname, grp, frm, to, mat, hidden=("down",), rotation=None, origin=None, feat=None):
        frm = [h2(v) for v in frm]; to = [h2(v) for v in to]
        e = {"name": cname, "box_uv": False, "render_order": "default", "locked": False, "export": True, "scope": 0,
             "allow_mirror_modeling": True, "from": frm, "to": to, "autouv": 0, "color": 0,
             "origin": origin or [(frm[i] + to[i]) / 2 for i in range(3)], "faces": {}, "type": "cube", "uuid": nu(),
             "_mat": mat, "_hidden": set(hidden), "_feat": feat or {}}
        if rotation: e["rotation"] = rotation
        elements.append(e); groups[grp]["children"].append(("e", e["uuid"]))
        return e

    bw, bh, bl, by = S["body"]
    hw, hh, hl = S["head"]
    feats = S["features"]
    root = group(name, [0, 0, 0])
    # ---- body: core, chest lump, back, rump
    g_body = group("body", [0, by + bh * 0.5, 0], root)
    z0, z1 = -bl / 2, bl / 2
    cube("body_box", g_body, [-bw / 2, by, z0], [bw / 2, by + bh, z1], "body", hidden=())
    chest_mat = "chest" if "chest" in feats else "belly"
    cube("chest", g_body, [-bw / 2 + 0.5, by + 0.5, z0 - 1], [bw / 2 - 0.5, by + bh * 0.75, z0 + 1.5], chest_mat, hidden=())
    cube("belly", g_body, [-bw / 2 + 0.5, by - 0.5, z0 + 1.5], [bw / 2 - 0.5, by + 1.0, z1 - 1.5], "belly")
    cube("back", g_body, [-bw / 2 + 1, by + bh, z0 + 1.5], [bw / 2 - 1, by + bh + 0.5, z1 - 1], "body")
    # ---- head (with the neck for long-necked birds), pivot at the neck base
    neck_base = [0, by + bh * 0.8, z0 + 0.5]
    g_head = group("head", neck_base, g_body)
    y, z = by + bh * 0.6, z0 + 0.5
    for i, (dz, nh, nw, _) in enumerate(S["neck"]):
        z += dz
        cube(f"neck_{i + 1}", g_head, [-nw / 2, y, z - nw / 2], [nw / 2, y + nh, z + nw / 2], "neck", hidden=())
        y += nh - 0.5
    if not S["neck"]:
        y = by + bh - 1.0
    hz = z - hl * 0.55 if S["neck"] else z0 - 0.5
    head = cube("head_box", g_head, [-hw / 2, y, hz - hl / 2], [hw / 2, y + hh, hz + hl / 2], "head", hidden=())
    head_front = hz - hl / 2
    if "face_disc" in feats:
        cube("face_disc", g_head, [-hw / 2 + 0.5, y + 0.5, head_front - 0.5], [hw / 2 - 0.5, y + hh - 0.5, head_front], "disc",
             hidden=("down", "up", "east", "west", "south"))
    if "plume" in feats:
        for k in range(2):
            cube(f"plume_{k + 1}", g_head, [-0.25, y + hh - 1.0 - k * 0.5, hz + hl / 2 - 0.5], [0.25, y + hh - 0.5 - k * 0.5, hz + hl / 2 + 3 + k],
                 "plume", hidden=("down",))
    if "neck_ring" in feats:
        nw = S["neck"][0][2]
        cube("neck_ring", g_head, [-nw / 2 - 0.25, by + bh * 0.6 + S["neck"][0][1] - 1.0, z0 + 0.5 - nw / 2 - 0.25],
             [nw / 2 + 0.25, by + bh * 0.6 + S["neck"][0][1] - 0.5, z0 + 0.5 + nw / 2 + 0.25], "neck", hidden=("down", "up"))
    head["_feat"] = {"eyes": True}
    # beak
    blen, bwid, bhgt, hook = S["beak"]
    beak_y = y + hh * (0.38 if not S.get("front_eyes") else 0.3)
    g_beak = group("beak", [0, beak_y, head_front], g_head)
    cube("beak_upper", g_beak, [-bwid / 2, beak_y, head_front - blen], [bwid / 2, beak_y + bhgt, head_front + 0.5], "beak",
         feat={"beak": True})
    if bhgt >= 1.5 and not hook:
        cube("beak_lower", g_beak, [-bwid / 2 + 0.25, beak_y - 0.5, head_front - blen + 0.5], [bwid / 2 - 0.25, beak_y, head_front + 0.5], "beak",
             hidden=("up",))
    if hook:
        cube("beak_hook", g_beak, [-bwid / 2 + 0.25, beak_y - 1.0, head_front - blen], [bwid / 2 - 0.25, beak_y, head_front - blen + 1.0], "beak",
             hidden=("up",))
    if "knob" in feats:
        cube("beak_knob", g_beak, [-0.5, beak_y + bhgt - 0.5, head_front - 1.0], [0.5, beak_y + bhgt + 0.5, head_front + 0.5], "knob")
    # ---- wings: inner slab hanging from the shoulder + feather fringe; tip folded back along the body
    hi, ch, lt, th, fingers = S["wing"]
    th = max(th, h2(ch * 0.75))                       # broad tips: spread, the wing keeps a bird's shape
    for side, sg in (("right", 1), ("left", -1)):
        sx = sg * bw / 2
        sh = [sx, by + bh - 0.5, z0 + 1.5]
        g_w = group("wing_" + side, sh, g_body)
        x_in, x_out = (sx, sx + sg * 1.0)
        xa, xb = min(x_in, x_out), max(x_in, x_out)
        cube(f"wing_{side}_box", g_w, [xa, sh[1] - hi, sh[2]], [xb, sh[1], sh[2] + ch], "wing", hidden=(), feat={"wing": side})
        cube(f"wing_{side}_coverts", g_w, [xa - 0.25 * (sg < 0), sh[1] - hi * 0.45, sh[2] - 0.5], [xb + 0.25 * (sg > 0), sh[1] + 0.5, sh[2] + ch * 0.55],
             "wing", hidden=("down",), feat={"coverts": True})
        fx = xb + 0.05 if sg > 0 else xa - 0.05
        cube(f"wing_{side}_fringe", g_w, [fx, sh[1] - hi, sh[2] + ch], [fx, sh[1], sh[2] + ch + 2.0], "wing",
             hidden=("down", "up", "north", "south"), feat={"fringe": True})
        wrist = [sx + sg * 0.5, sh[1] - hi, sh[2] + 0.5]
        g_t = group("wing_tip_" + side, wrist, g_w)
        ta, tb = (wrist[0] - 0.5, wrist[0] + 0.5)
        cube(f"wing_tip_{side}_box", g_t, [ta, wrist[1], wrist[2]], [tb, wrist[1] + th, wrist[2] + lt], "tip", hidden=(), feat={"tip": side})
        if fingers:
            for k in range(fingers):     # primaries spread like fingers along the tip's chord
                yk = wrist[1] + th * (k + 0.5) / fingers
                L = lt + 2.0 + 1.5 * (k if k < fingers - 1 else k - 2)
                cube(f"wing_tip_{side}_primary_{k + 1}", g_t, [wrist[0] - 0.25, yk - 0.25, wrist[2] + lt - 1.0], [wrist[0] + 0.25, yk + 0.5, wrist[2] + L],
                     "tip", hidden=("down",), feat={"primary": True})
        else:
            cube(f"wing_tip_{side}_fringe", g_t, [wrist[0], wrist[1], wrist[2] + lt], [wrist[0], wrist[1] + th, wrist[2] + lt + 2.0], "tip",
                 hidden=("down", "up", "north", "south"), feat={"fringe": True})
    # ---- tail
    tw, tlen, fan = S["tail"]
    tp = [0, by + bh * 0.55, z1 - 0.5]
    g_tail = group("tail", tp, g_body)
    cube("tail_box", g_tail, [-tw / 2, tp[1] - 0.5, tp[2]], [tw / 2, tp[1] + 0.5, tp[2] + tlen], "tail", feat={"tail": True})
    cube("tail_fringe", g_tail, [-tw / 2 - (1 if fan else 0), tp[1], tp[2] + tlen], [tw / 2 + (1 if fan else 0), tp[1], tp[2] + tlen + 2.0], "tail",
         hidden=("down", "north", "south", "east", "west"), feat={"fringe_up": True})
    if name == "duck":
        cube("tail_curl", g_tail, [-0.25, tp[1] + 0.5, tp[2] + 0.5], [0.25, tp[1] + 2.0, tp[2] + 1.0], "tail")
    # ---- legs
    ll, lth = S["leg"]
    for side, sg in (("right", 1), ("left", -1)):
        lx = sg * bw * 0.22
        hip = [lx, by + 0.5, 0.5]
        g_l = group("leg_" + side, hip, root)
        cube(f"leg_{side}_box", g_l, [lx - lth / 2, by - ll + 0.5, 0.5 - lth / 2], [lx + lth / 2, by + 0.5, 0.5 + lth / 2], "leg")
        if by - ll + 0.5 > 0.5:   # long legged: the leg starts above the ground
            pass
        foot_y = max(0.0, by - ll + 0.5)
        toe = max(1.5, ll * 0.35) if ll > 6 else max(1.5, lth * 2.5)
        web = name in ("duck", "swan", "seagull")
        tw_ = 2.0 if web else 0.5
        cube(f"foot_{side}_front", g_l, [lx - tw_ / 2, foot_y, 0.5 - toe], [lx + tw_ / 2, foot_y + 0.5, 0.5 + lth / 2], "leg")
        if not web:
            cube(f"foot_{side}_back", g_l, [lx - 0.25, foot_y, 0.5 + lth / 2], [lx + 0.25, foot_y + 0.5, 0.5 + lth / 2 + 1.0], "leg")
        if "talons" in feats:
            cube(f"talon_{side}", g_l, [lx - 0.5, foot_y, 0.5 - toe - 0.5], [lx + 0.5, foot_y + 1.0, 0.5 - toe], "claw")
    # ---- scale dummy (hidden)
    g_sd = group("scale_dummy", [0, 0, 0], root)
    sd = cube("scale_dummy_imp", g_sd, [bw / 2 + 6, 0, -2], [bw / 2 + 10, 18.5, 2], "body")
    sd["_dummy"] = True

    # ------------------------------------------------------------------ painting
    def feathers(ramp, w, h, face, scale=1.0, base=None, tips=True):
        """Rows of overlapping feathers: each a scallop, dark at the base, a light rim at its tip; the face rounded."""
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS[ramp])
        b = base if base is not None else n * 0.55
        v = np.full((h, w), b + FACE_LIGHT[face] * 0.9)
        v -= np.clip(1.0 - edge / 2.5, 0, 1) * 1.0
        if face not in ("up", "down"):
            v -= V * 0.9
        fw, fh = max(2, int(3 * scale)), max(2, int(3 * scale))
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        row = Y // fh
        off = (row % 2) * (fw // 2)
        cx = ((X + off) % fw) - (fw - 1) / 2
        cy = (Y % fh)
        if tips:
            scallop = cy + 0.6 * np.abs(cx) ** 1.4         # rounded feather tips pointing down
            v += np.where(scallop > fh - 0.8, 0.9, 0.0) - np.where(cy < 0.8, 0.6, 0.0)
        v += (nrng.random((h, w)) - 0.5) * 0.4
        return rc(ramp, dither(v, w, h))

    def flight(ramp, w, h, face, along_u=True, dark_end=0.0):
        """Long flight feathers: strips with a light shaft, darker toward the tips; for wing and tail slabs."""
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS[ramp])
        v = np.full((h, w), n * 0.55 + FACE_LIGHT[face] * 0.7)
        X, Y = np.meshgrid(np.arange(w), np.arange(h))
        k = Y if along_u else X
        v -= ((k % 3) == 0) * 1.1                          # the gap between feathers
        v += ((k % 3) == 1) * 0.5                          # the shaft
        t = U if along_u else V
        v -= t * dark_end
        v -= np.clip(1.0 - edge / 2.0, 0, 1) * 0.6
        return rc(ramp, dither(v, w, h))

    def plain(ramp, w, h, face, base=None):
        U, V, edge = uvgrid(w, h)
        n = len(RAMPS[ramp])
        v = np.full((h, w), (base if base is not None else n * 0.6) + FACE_LIGHT[face] * 0.8) - np.clip(1.0 - edge / 2.0, 0, 1) * 0.7
        return rc(ramp, dither(v, w, h))

    def eye(rgb, face, w, h):
        """A round eye: dark ring, iris, big pupil high toward the beak, a glint."""
        if S.get("front_eyes"):
            spots = [(0.3, 0.42), (0.7, 0.42)] if face == "north" else []
        else:
            spots = [(0.72, 0.36)] if face == "east" else ([(0.28, 0.36)] if face == "west" else [])
        for (u, v) in spots:
            cx, cy = int(u * w), int(v * h)
            big = S.get("front_eyes")
            r = 2 if big else 1
            for yy in range(cy - r, cy + r + 1):
                for xx in range(cx - r, cx + r + 1):
                    if 0 <= xx < w and 0 <= yy < h and (xx - cx) ** 2 + (yy - cy) ** 2 <= r * r + 1:
                        rgb[yy, xx] = (18, 16, 20)
            if 0 <= cx < w and 0 <= cy < h:
                rgb[cy, cx] = RAMPS["iris"][0]
                if big and cx + 1 < w: rgb[cy, cx + 1] = RAMPS["iris"][0]
                if big:
                    rgb[cy, cx] = (16, 14, 16)
                    for dx, dy in ((-1, 0), (1, 0), (0, -1), (0, 1)):
                        if 0 <= cx + dx < w and 0 <= cy + dy < h: rgb[cy + dy, cx + dx] = RAMPS["iris"][0]
                hx, hy = cx - (1 if big else 0), cy - (1 if big else 0)
                if 0 <= hx < w and 0 <= hy < h: rgb[hy, hx] = (251, 254, 251)
        return rgb

    def paint(e, face, w, h):
        mat, feat = e["_mat"], e["_feat"]
        a = np.ones((h, w), bool)
        if feat.get("fringe") or feat.get("fringe_up"):
            # feather tips cut with hard alpha: columns of rounded tips of different lengths
            rgb = flight(mat if mat in RAMPS else "wing", w, h, face, along_u=False, dark_end=0.6)
            X, Y = np.meshgrid(np.arange(w), np.arange(h))
            if feat.get("fringe_up"):
                L = (h * (0.55 + 0.45 * np.abs(np.sin(X * 1.7 + 0.3))))
                a = Y < L
            else:
                col = (X // 2)
                L = w * (0.55 + 0.45 * np.abs(np.sin(col * 1.9 + 0.4)))
                a = X < L if face == "west" else X >= (w - L)
            return rgb, a
        if mat in ("beak", "leg", "claw", "knob", "plume"):
            rgb = plain(mat, w, h, face)
            if feat.get("beak") and "beak_spot" in feats and face in ("east", "west"):
                c = int(w * (0.2 if face == "east" else 0.8)); rgb[max(0, h - 2):, max(0, c - 1):c + 1] = (200, 40, 30)
            return rgb, a
        if mat in ("wing", "tip"):
            if feat.get("coverts"):
                rgb = feathers("wing", w, h, face, 1.0)
            else:
                along = face in ("east", "west")
                rgb = flight(mat, w, h, face, along_u=along, dark_end=0.8 if mat == "tip" else 0.3)
            if mat == "tip" and "tip_spots" in feats and face in ("east", "west"):
                for k in range(0, h, 3):
                    xx = 1 if face == "east" else w - 2
                    if 0 <= xx < w: rgb[k:k + 1, xx] = (240, 242, 244)
            if mat == "wing" and "wing_bars" in feats and face in ("east", "west") and not feat.get("coverts"):
                for frac in (0.45, 0.7):
                    c = int(w * (1 - frac if face == "east" else frac))
                    c0, c1 = max(0, c - 1), min(w, c + 1)
                    rgb[:, c0:c1] = rc("tip", np.full((h, c1 - c0), 1.0))
            if mat == "wing" and "speculum" in feats and face in ("east", "west") and not feat.get("coverts"):
                c0, c1 = (int(w * 0.15), int(w * 0.45)) if face == "east" else (int(w * 0.55), int(w * 0.85))
                rgb[h // 3:, c0:c1] = rc("spec", 2.0 + np.zeros((h - h // 3, c1 - c0)) + np.linspace(0, 1.5, h - h // 3)[:, None])
                rgb[h // 3:, c0:c0 + 1] = (240, 240, 244); rgb[h // 3:, c1 - 1:c1] = (240, 240, 244)
            if "dark_bars" in feats:
                rgb[(np.arange(h) % 4 == 0)] = (rgb[(np.arange(h) % 4 == 0)] * 0.55).astype(np.uint8)
            return rgb, a
        if mat == "tail":
            rgb = flight("tail", w, h, face, along_u=face in ("east", "west"), dark_end=0.4)
            if "tail_band" in feats and face in ("up", "down"):
                rgb[-3:, :] = rc("tip", np.full((min(3, h), w), 1.0))
            return rgb, a
        if mat == "disc":
            U, V, edge = uvgrid(w, h)
            n = len(RAMPS["disc"])
            v = np.full((h, w), n - 1.5) - np.hypot(U - 0.5, (V - 0.45) * 1.2) * 2.5
            rgb = rc("disc", dither(v, w, h))
            rim = edge < 1.2
            rgb[rim] = rc("rim", np.full((h, w), 1.5))[rim]
            return eye(rgb, face, w, h), a
        # body, belly, chest, head, neck: feather rows
        rgb = feathers(mat if mat in RAMPS else "body", w, h, face, 1.0 if mat != "head" else 0.8)
        if mat == "neck" and "neck_sheen" in feats:
            U, V, _ = uvgrid(w, h)
            sheen = (np.sin(U * 6 + V * 3) > 0.3)
            rgb[sheen] = rc("neck", np.full((h, w), 3.5))[sheen]
        if mat == "head" and "head_sheen" in feats and face in ("east", "west", "up"):
            U, V, _ = uvgrid(w, h)
            sheen = (np.hypot(U - 0.5, V - 0.3) < 0.25)
            rgb[sheen] = rc("head", np.full((h, w), 4.0))[sheen]
        if "sheen" in feats and face in ("up", "east", "west"):
            U, V, _ = uvgrid(w, h)
            s_ = (nrng.random((h, w)) < 0.08)
            rgb[s_] = (60, 70, 120)
        if "speckles" in feats and mat in ("body", "head", "wing") and face != "down":
            s_ = (nrng.random((h, w)) < 0.06)
            rgb[s_] = (90, 92, 100)
            s2 = (nrng.random((h, w)) < 0.04)
            rgb[s2] = (240, 236, 228)
        if "dark_bars" in feats and mat in ("body", "belly") and face != "up":
            bars = (np.arange(h) % 5 == 2)[:, None] & (nrng.random((h, w)) < 0.5)
            rgb[bars] = (70, 74, 84)
        if mat == "head" and "eye_stripe" in feats and face in ("east", "west"):
            rgb[int(h * 0.3):int(h * 0.3) + 2, :] = rc("plume", np.full((2, w), 1.0))
        if mat == "neck" and "neck_streak" in feats and face == "north":
            rgb[:, w // 2 - 1:w // 2 + 1] = rc("plume", np.full((h, min(2, w)), 1.5))
        if mat == "head" and "face_orange" in feats and face in ("north", "east", "west"):
            U, V, _ = uvgrid(w, h)
            m = (V > 0.45) & ((U < 0.8) if face == "west" else (U > 0.2)) if face != "north" else (V > 0.35)
            rgb[m] = rc("chest", dither(np.full((h, w), 3.0) - V * 1.2, w, h))[m]
        if e["_feat"].get("eyes"):
            rgb = eye(rgb, face, w, h)
        return rgb, a

    rects = {}
    for e in elements:
        for face in FACES:
            if face in e["_hidden"] or e.get("_dummy"):
                e["faces"][face] = None; continue
            w, h = (px(v) for v in face_dims(e["from"], e["to"], face))
            if w <= 0 or h <= 0:
                e["faces"][face] = None; continue
            key = f"{e['uuid']}:{face}"
            rgb, a = paint(e, face, w, h)
            rects[key] = {"w": w, "h": h, "rgb": rgb, "a": a}
            e["faces"][face] = key
    TEX = S["tex"]
    while True:
        GAP = 2
        x = y_ = shelf = 0
        for k, r in sorted(rects.items(), key=lambda kv: (-kv[1]["h"], -kv[1]["w"])):
            if x + r["w"] > TEX: x, y_, shelf = 0, y_ + shelf + GAP, 0
            r["x"], r["y"] = x, y_; x += r["w"] + GAP; shelf = max(shelf, r["h"])
        if y_ + shelf <= TEX: break
        TEX *= 2
    img = np.zeros((TEX, TEX, 4), np.uint8)
    for r in rects.values():
        img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], :3] = r["rgb"]
        img[r["y"]:r["y"] + r["h"], r["x"]:r["x"] + r["w"], 3] = np.where(r["a"], 255, 0)
    for e in elements:
        for face in FACES:
            key = e["faces"][face]
            if key is None:
                e["faces"][face] = {"uv": [0, 0, 0, 0], "texture": None}
            else:
                r = rects[key]; e["faces"][face] = {"uv": [r["x"], r["y"], r["x"] + r["w"], r["y"] + r["h"]], "texture": 0}
        if e.pop("_dummy", False):
            e["export"] = False; e["visibility"] = False
            for f in FACES: e["faces"][f] = {"uv": [0, 0, 1, 1], "texture": None}
        for k in ("_mat", "_hidden", "_feat"): e.pop(k)

    anims = make_anims(S, groups, nu, name)

    buf = io.BytesIO(); Image.fromarray(img, "RGBA").save(buf, "PNG")
    src = "data:image/png;base64," + base64.b64encode(buf.getvalue()).decode()

    def group_json(g):
        vis = g["name"] != "scale_dummy"
        return {"name": g["name"], "uuid": g["uuid"], "export": vis, "locked": False, "scope": 0, "selected": False,
                "visibility": vis, "origin": g["origin"], "rotation": [0, 0, 0], "color": 0, "children": [],
                "reset": False, "shade": True, "mirror_uv": False, "autouv": 0, "isOpen": True, "primary_selected": False}

    def outliner(gname):
        g = groups[gname]
        return {"uuid": g["uuid"], "isOpen": True, "children": [c[1] if c[0] == "e" else outliner(c[1]) for c in g["children"]]}

    model = {"meta": {"format_version": "5.0", "model_format": "free", "box_uv": False}, "name": name, "model_identifier": "",
             "visible_box": [1, 1, 0], "variable_placeholders": "", "variable_placeholder_buttons": [], "timeline_setups": [],
             "unhandled_root_fields": {}, "resolution": {"width": TEX, "height": TEX}, "elements": elements,
             "groups": [group_json(g) for g in groups.values()], "outliner": [outliner(name)],
             "textures": [{"name": f"{name}.png", "path": "", "folder": "", "namespace": "", "id": "0", "group": "", "scope": 0,
                           "width": TEX, "height": TEX, "uv_width": TEX, "uv_height": TEX, "particle": False, "use_as_default": False,
                           "layers_enabled": False, "sync_to_project": "", "file_format": "png", "render_mode": "default",
                           "render_sides": "double", "wrap_mode": "limited", "pbr_channel": "color", "fps": 7, "force_translucent": False,
                           "frame_time": 1, "frame_order_type": "loop", "frame_order": "", "frame_interpolate": False, "visible": True,
                           "internal": True, "saved": True, "uuid": nu(), "source": src}],
             "animations": anims}
    os.makedirs(OUT, exist_ok=True)
    out = os.path.join(OUT, f"{name}.bbmodel")
    with open(out, "w", encoding="utf8") as fh:
        json.dump(model, fh, indent="\t")
    sys.path.insert(0, REPO_SCRIPTS)
    import fix_texture_bleed
    fix_texture_bleed.pad_file(out, [os.path.join(OUT, f"{name}.png")])
    ys = [e["to"][1] for e in elements if e.get("export", True)]
    colours = len({tuple(c) for c in img[img[..., 3] > 0][:, :3]})
    print(f"{name:10s} cubes={len(elements) - 1:3d} tex={TEX} tall={max(ys):.1f} span={2 * (S['wing'][0] + S['wing'][2]) + S['body'][0]:.0f} "
          f"colours={colours} anims={[a['name'] for a in anims]}")


# ------------------------------------------------------------------ animations
def make_anims(S, groups, nu, name):
    N = 16
    out = []
    by = S["body"][3]

    def anim(aname, length, loop, tracks):
        animators = {}
        for bone, chans in tracks.items():
            if bone not in groups: continue
            kfs = []
            for ch, keys in chans.items():
                for t, (x, y, z) in keys:
                    kfs.append({"channel": ch, "data_points": [{"x": f"{x:.3f}", "y": f"{y:.3f}", "z": f"{z:.3f}"}], "uuid": nu(),
                                "time": round(t, 4), "color": -1, "interpolation": "catmullrom"})
            animators[groups[bone]["uuid"]] = {"name": bone, "type": "bone", "rotation_global": False, "quaternion_interpolation": False,
                                               "keyframes": kfs}
        out.append({"uuid": nu(), "name": aname, "loop": "loop" if loop else "hold", "override": False, "length": length, "snapping": 24,
                    "selected": False, "group_name": "", "scope": 0, "anim_time_update": "", "blend_weight": "", "start_delay": "",
                    "loop_delay": "", "animators": animators})

    def sample(length, fn, n=N, loop=True):
        """fn(p) -> {bone: {channel: (x,y,z)}} for p in 0..1."""
        tracks = {}
        steps = n + (1 if loop else 0)
        for i in range(steps):
            p = i / n if loop else i / (n - 1)
            for bone, chans in fn(min(p, 1.0) % 1.0 if loop else min(p, 1.0)).items():
                for ch, v in chans.items():
                    tracks.setdefault(bone, {}).setdefault(ch, []).append((p * length, v))
        return tracks

    sw = lambda p, ph=0.0: math.sin(2 * math.pi * (p - ph))
    big = S["wing"][0] + S["wing"][2]                        # bigger birds flap slower
    flap_T = 0.35 + big * 0.022
    ll = S["leg"][0]
    walk_T = 0.45 + ll * 0.05

    def folded(p): return {}

    def spread(z_amp=0.0, p=0.0, base=88.0, tip_amp=12.0, lag=0.12):
        zz = base + z_amp * sw(p)
        tx = 88.0 + tip_amp * sw(p, lag)
        return {"wing_right": {"rotation": (0, 0, zz)}, "wing_left": {"rotation": (0, 0, -zz)},
                "wing_tip_right": {"rotation": (tx, 0, 0)}, "wing_tip_left": {"rotation": (tx, 0, 0)}}

    tuck = {"leg_right": {"rotation": (-70, 0, 0)}, "leg_left": {"rotation": (-70, 0, 0)}}

    # idle: breathing, looking about, a tail flick, a little wing shuffle
    def idle(p):
        look = 25 * math.sin(2 * math.pi * p) * (1 if p < 0.5 else 0.6)
        return {"body": {"position": (0, 0.15 * sw(2 * p), 0)},
                "head": {"rotation": (4 * sw(p, 0.3), look, 3 * sw(p, 0.1))},
                "tail": {"rotation": (6 * max(0, sw(3 * p)) , 0, 0)},
                "wing_right": {"rotation": (0, 0, 2 * max(0, sw(p, 0.4)))}, "wing_left": {"rotation": (0, 0, -2 * max(0, sw(p, 0.4)))}}
    anim("idle", 3.0, True, sample(3.0, idle))

    # walk / run: legs alternate, body sways and bobs, head thrusts (pigeon style), tail wags
    def gait(p, A, bob, run):
        d = {"leg_right": {"rotation": (A * sw(p), 0, 0), "position": (0, 0.3 * max(0, sw(p, -0.25)), 0)},
             "leg_left": {"rotation": (-A * sw(p), 0, 0), "position": (0, 0.3 * max(0, sw(p, 0.25)), 0)},
             "body": {"rotation": (0, 3 * sw(p), 5 * sw(p, 0.25)), "position": (0, -bob * (0.5 + 0.5 * math.cos(4 * math.pi * p)), 0)},
             "head": {"rotation": (5 * sw(2 * p, 0.1), -3 * sw(p), 0), "position": (0, 0, -0.6 * sw(2 * p, 0.2))},
             "tail": {"rotation": (4 * sw(2 * p), 6 * sw(p, 0.3), 0)}}
        if run:
            d.update({"wing_right": {"rotation": (0, 0, 25 + 10 * sw(2 * p))}, "wing_left": {"rotation": (0, 0, -25 - 10 * sw(2 * p))}})
        return d
    anim("walk", walk_T, True, sample(walk_T, lambda p: gait(p, 28, 0.3, False)))
    anim("run", walk_T * 0.6, True, sample(walk_T * 0.6, lambda p: gait(p, 40, 0.5, True)))

    # fly: wings spread and flapping (down stroke faster), body lifts on the down stroke, legs tucked
    def fly(p):
        d = spread(42, p, 85, 16, 0.1)
        d.update(tuck)
        d["body"] = {"position": (0, 0.8 * sw(p, 0.25), 0), "rotation": (-4 + 3 * sw(p, 0.3), 0, 0)}
        d["head"] = {"rotation": (4 - 3 * sw(p, 0.3), 0, 0)}
        d["tail"] = {"rotation": (-6 + 4 * sw(p, 0.4), 0, 0)}
        return d
    anim("fly", flap_T, True, sample(flap_T, fly))

    # glide: spread and still, slow banking, a breath of lift
    def glide(p):
        d = spread(4, p, 82, 5, 0.2)
        d.update(tuck)
        d["body"] = {"rotation": (-3, 0, 8 * sw(p)), "position": (0, 0.3 * sw(p, 0.25), 0)}
        d["head"] = {"rotation": (3, 0, -6 * sw(p))}
        d["tail"] = {"rotation": (-4, 0, 0)}
        return d
    anim("glide", 2.4, True, sample(2.4, glide))

    # takeoff: crouch, jump, wings unfold into strong flaps, legs tuck
    def takeoff(p):
        crouch = math.sin(math.pi * min(p / 0.25, 1)) if p < 0.25 else 0
        open_ = min(1.0, max(0.0, (p - 0.15) / 0.3))
        flap = sw(p * 2.2)
        zz = open_ * (80 + 45 * flap)
        tx = open_ * (88 + 15 * sw(p * 2.2, 0.1))
        legs = -70 * min(1.0, max(0.0, (p - 0.35) / 0.3))
        return {"body": {"position": (0, -1.2 * crouch + 2.5 * max(0, p - 0.25), 0), "rotation": (6 * crouch - 6 * open_, 0, 0)},
                "wing_right": {"rotation": (0, 0, zz)}, "wing_left": {"rotation": (0, 0, -zz)},
                "wing_tip_right": {"rotation": (tx, 0, 0)}, "wing_tip_left": {"rotation": (tx, 0, 0)},
                "leg_right": {"rotation": (legs + 20 * crouch, 0, 0)}, "leg_left": {"rotation": (legs + 20 * crouch, 0, 0)},
                "head": {"rotation": (-8 * crouch + 4 * open_, 0, 0)}, "tail": {"rotation": (10 * crouch - 8 * open_, 0, 0)}}
    anim("takeoff", 0.9, False, sample(0.9, takeoff, n=18, loop=False))

    # land: flare (body pitches up, wings forward and braking), legs reach down, then fold up
    def land(p):
        flare = math.sin(math.pi * min(1, p / 0.7))
        fold = min(1.0, max(0.0, (p - 0.6) / 0.4))
        zz = (1 - fold) * (80 + 20 * sw(p * 1.5))
        tx = (1 - fold) * 88
        legs = -70 * (1 - min(1.0, p / 0.45))
        return {"body": {"rotation": (12 * flare * (1 - fold), 0, 0), "position": (0, 1.5 * (1 - min(1.0, p / 0.6)), 0)},
                "wing_right": {"rotation": (-10 * flare, 0, zz)}, "wing_left": {"rotation": (-10 * flare, 0, -zz)},
                "wing_tip_right": {"rotation": (tx, 0, 0)}, "wing_tip_left": {"rotation": (tx, 0, 0)},
                "leg_right": {"rotation": (legs + 15 * flare, 0, 0)}, "leg_left": {"rotation": (legs + 15 * flare, 0, 0)},
                "tail": {"rotation": (-12 * flare * (1 - fold), 0, 0)}, "head": {"rotation": (-6 * flare, 0, 0)}}
    anim("land", 1.0, False, sample(1.0, land, n=18, loop=False))

    # attack: wings half open, a lunge and peck
    def attack(p):
        lunge = math.sin(math.pi * min(1, p / 0.5)) if p < 0.5 else 0
        half = math.sin(math.pi * p)
        return {"head": {"rotation": (-35 * lunge, 0, 0), "position": (0, -0.5 * lunge, -1.5 * lunge)},
                "body": {"rotation": (-10 * lunge, 0, 0), "position": (0, 0, -0.8 * lunge)},
                "wing_right": {"rotation": (0, 0, 50 * half)}, "wing_left": {"rotation": (0, 0, -50 * half)},
                "wing_tip_right": {"rotation": (30 * half, 0, 0)}, "wing_tip_left": {"rotation": (30 * half, 0, 0)},
                "tail": {"rotation": (12 * half, 0, 0)}}
    anim("attack", 0.7, False, sample(0.7, attack, n=12, loop=False))

    def hit(p):
        j = math.sin(math.pi * p) * (1 - p)
        return {"body": {"rotation": (10 * j, 0, 6 * j), "position": (0, 0.3 * j, 0.6 * j)},
                "head": {"rotation": (12 * j, 0, -8 * j)},
                "wing_right": {"rotation": (0, 0, 35 * j)}, "wing_left": {"rotation": (0, 0, -35 * j)},
                "tail": {"rotation": (14 * j, 0, 0)}}
    anim("hit", 0.45, False, sample(0.45, hit, n=10, loop=False))

    if S.get("swim"):
        def swim(p):
            return {"body": {"position": (0, -by + 0.5 + 0.2 * sw(p), 0), "rotation": (2 * sw(p, 0.2), 3 * sw(p), 2 * sw(p, 0.25))},
                    "leg_right": {"rotation": (-40 + 35 * sw(p), 0, 0), "position": (0, -by + 1.0, 0)},
                    "leg_left": {"rotation": (-40 - 35 * sw(p), 0, 0), "position": (0, -by + 1.0, 0)},
                    "head": {"rotation": (4 * sw(p, 0.3), 8 * sw(p * 0.5), 0)}, "tail": {"rotation": (5 * sw(p), 6 * sw(p, 0.4), 0)}}
        anim("swim", 1.6, True, sample(1.6, swim))
    return out


if __name__ == "__main__":
    for b in (sys.argv[1:] or list(BIRDS)):
        build(b)
