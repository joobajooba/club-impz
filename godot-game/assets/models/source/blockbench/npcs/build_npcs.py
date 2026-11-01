"""Builds the hub NPCs, to docs/blockbench_detailed_prompts.md section 3.8.

    python build_npcs.py

Each NPC keeps a job that a decided system needs: the blacksmith (furnace, anvil, hilts: D-013,
D-054), the merchant (selling: D-073), the tanner (D-029), the herbalist (drying rack: D-022),
the carpenter (sawbench and wood hilts: D-107), the fisher (fishing: D-110), a castle guard and a
quest giver for challenges (game_worlds.md section 3). They are animal folk like the guide's
fennec NPC reference, not imps, because the Implingz get no new art (D-016).

Rig (section 3.8): <id> > body (hips) > chest > head (neck), arm_right, arm_left (shoulders) >
hand_right > prop; leg_right, leg_left (hips); plus the hidden scale_dummy. Animations: idle,
talk, wave, work, walk. 2 px per unit, facing north (-z).

Writes godot-game/assets/models/npcs/<role>_npc.bbmodel (+ textures/npcs/) and npcs_lineup.bbmodel.
"""
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent))
from bbkit import Mat, Model, from_base, put, ramp, stretch  # noqa: E402

GAME = HERE.parents[4]
OUT = GAME / "assets" / "models" / "npcs"
TEX = GAME / "assets" / "textures" / "npcs"
PPU = 2

IRON = ramp("#1c1f24", "#30353c", "#4a5059", "#6a717b", "#8a929c", "#aab2bc")
WOOD = ramp("#24140e", "#3a2216", "#52321e", "#6c4428", "#885834", "#a67244")
LEATHER = ramp("#2a160e", "#422416", "#5c3420", "#78462a", "#965c36", "#b07648")
GOLD = stretch(ramp("8a3e14", "ce6825", "e38a23", "f19f26", "f9d369", "f9f47d"))
PAPER = ramp("#8a7c62", "#a8987a", "#c4b494", "#dacca8", "#ece2c4")
STRAW = ramp("#5a4418", "#7a5e22", "#9c7c30", "#bc9c44", "#d8bc60", "#ecd684")


def fur(hexcol):
    return Mat("fur", from_base(hexcol, 7, 0.5), "fur", base=3)


def cloth(hexcol, **kw):
    return Mat("cloth", from_base(hexcol, 7, 0.55), "cloth", base=3, fold=3, **kw)


# role: species look, colours, outfit, hat, prop
NPCS = [
    dict(role="blacksmith", species="badger", height=1.15, fur="#5a5a62", face="#e8e4dc", stripe="#1e1e24",
         ears="round", snout=1.5, eye="#6a3a1a", shirt="#7a3a1a", apron="leather", hat="bandana", hat_col="#b8401c",
         prop="hammer", burly=True),
    dict(role="merchant", species="fennec", height=1.0, fur="#e0a860", face="#f6ead4", ears="tall", snout=2.0,
         eye="#3a6a2a", shirt="#5a2a7a", coat="#5a2a7a", trim="#e0b040", hat="fez", hat_col="#8a1a2a", prop="scroll",
         satchel=True),
    dict(role="tanner", species="bear", height=1.15, fur="#6a4428", face="#a87850", ears="round", snout=2.0,
         eye="#2a1a10", shirt="#4a5a3a", apron="hide", hat=None, prop="scraper", burly=True),
    dict(role="herbalist", species="rabbit", height=1.0, fur="#d8ccc0", face="#f4eee6", ears="long", snout=1.0,
         eye="#4a2a5a", shirt="#3e6e3a", robe="#3e6e3a", trim="#c8b060", hat="straw", prop="basket"),
    dict(role="carpenter", species="beaver", height=1.0, fur="#7a4a28", face="#a8784a", ears="round", snout=1.5,
         eye="#2a1a10", shirt="#3a5a8a", apron="leather", hat="cap", hat_col="#3a3a42", prop="saw", teeth=True),
    dict(role="fisher", species="otter", height=0.95, fur="#5a3e2a", face="#c8a888", ears="round", snout=1.5,
         eye="#1a2a3a", shirt="#c8a030", coat="#c8a030", trim="#6a5020", hat="bucket", hat_col="#d8b030", prop="rod"),
    dict(role="guard", species="fox", height=1.1, fur="#c86428", face="#f4ece0", ears="tall", snout=2.0,
         eye="#5a3a10", shirt="#2a4a8a", tabard="#2a4a8a", trim="#e0b040", hat="helmet", prop="spear"),
    dict(role="quest_giver", species="owl", height=1.0, fur="#7a6450", face="#d8c8a8", ears="tufts", snout=0,
         eye="#e8a020", shirt="#4a3a6a", robe="#4a3a6a", trim="#e0b040", hat=None, prop="book", beak=True, specs=True),
]


def eyes_decal(N, eye_w=3):
    """Big shiny eyes (section 3.8): dark pupil, coloured iris, two highlight pixels, darker lid line."""
    iris = from_base(N["eye"], 5, 0.5)

    def d(area, f, w, h, c, rng):
        if f != "north":
            return
        y0 = h // 2 - 3
        if N["species"] == "badger":       # dark mask band round the eyes, painted under them
            st = from_base(N["stripe"], 5)
            for y in range(y0 - 1, y0 + 5):
                for x in range(1, w - 1):
                    put(area, x, y, st[1] if (x + y) % 5 else st[2])
        for cx in (w // 2 - 2 - eye_w * 2 + 2, w // 2 + 2):
            ew = eye_w * 2 - 1
            for y in range(4):
                for x in range(ew):
                    put(area, cx + x, y0 + y, iris[1] if y < 2 else iris[3])
            for x in range(ew):
                put(area, cx + x, y0 - 1, (40, 28, 26))           # lid line
            put(area, cx + ew // 2, y0 + 1, (22, 18, 24))         # pupil
            put(area, cx + ew // 2, y0 + 2, (22, 18, 24))
            put(area, cx + ew // 2 + 1, y0 + 1, (22, 18, 24))
            put(area, cx + 1, y0, (240, 238, 228))                # highlights
            put(area, cx + 2, y0 + 1, (220, 222, 230))
            if N.get("specs"):
                for x in range(-1, ew + 1):
                    put(area, cx + x, y0 - 2, (200, 160, 60))
                    put(area, cx + x, y0 + 4, (200, 160, 60))
                put(area, cx - 1, y0 + 1, (200, 160, 60))
                put(area, cx + ew, y0 + 1, (200, 160, 60))
        if N["species"] == "badger":       # the white stripe down the face, dark mask round the eyes
            st = from_base(N["face"], 5)
            for y in range(0, y0 - 1):
                for x in range(w // 2 - 1, w // 2 + 1):
                    put(area, x, y, st[3])
    return d


def snout_decal(N):
    def d(area, f, w, h, c, rng):
        if f != "north":
            return
        nose = (34, 24, 26)
        for x in range(w // 2 - 1, w // 2 + 1):
            put(area, x, 0, nose)
            put(area, x, 1, nose)
        put(area, w // 2 - 1, 0, (90, 80, 86))
        if h >= 4:
            put(area, w // 2 - 1, h - 1, (60, 30, 30))
            put(area, w // 2, h - 1, (60, 30, 30))
        if N.get("teeth") and h >= 3:
            put(area, w // 2 - 1, h - 1, (238, 230, 200))
            put(area, w // 2, h - 1, (238, 230, 200))
    return d


def buttons_decal(trim):
    t = from_base(trim, 5)

    def d(area, f, w, h, c, rng):
        if f != "north":
            return
        for y in range(2, h - 1, 3):
            put(area, w // 2, y, t[4])
            put(area, w // 2, y + 1, t[1])
    return d


def build(N):
    m = Model(f"{N['role']}_npc", ppu=PPU)
    k = N["height"]
    burly = N.get("burly", False)
    F = fur(N["fur"])
    FACE = Mat("face", from_base(N["face"], 7, 0.4), "skin", base=3)
    shirt = cloth(N["shirt"])
    leatherm = Mat("leather", LEATHER, "leather", base=3)
    iron = Mat("iron", IRON, "metal", base=2, bevel=True)
    wood = Mat("wood", WOOD, "wood", base=3)
    trim = Mat("trim", from_base(N.get("trim", "#c8a040"), 6), "metal", base=3, bevel=True)
    tw = 4.5 if burly else 3.75      # half widths
    td = 2.75 if burly else 2.25

    root = m.group(m.name, (0, 0, 0))
    body = m.group("body", (0, 5 * k, 0), root)
    chest = m.group("chest", (0, 8 * k, 0), body)
    hy = 12.5 * k                       # neck
    head = m.group("head", (0, hy, 0), chest)
    arm_r = m.group("arm_right", (tw + 0.75, 11.5 * k, 0), chest)
    arm_l = m.group("arm_left", (-tw - 0.75, 11.5 * k, 0), chest)
    hand_r = m.group("hand_right", (tw + 1.25, 6 * k, -0.5), arm_r)
    prop = m.group("prop", (tw + 1.25, 6 * k, -0.5), hand_r)
    leg_r = m.group("leg_right", (1.75, 5 * k, 0), body)
    leg_l = m.group("leg_left", (-1.75, 5 * k, 0), body)

    # legs and feet
    for g, s, nm in ((leg_r, 1, "right"), (leg_l, -1, "left")):
        m.cube(f"leg_{nm}_box", (s * 1.75 - 1.5, 1.0, -1.5), (s * 1.75 + 1.5, 5 * k + 0.5, 1.5), cloth("#4a3a30") if not N.get("robe") else F, g)
        m.cube(f"foot_{nm}", (s * 1.75 - 1.75, 0, -2.75), (s * 1.75 + 1.75, 1.25, 1.75), Mat("boot", LEATHER, "leather", base=2), g)
    # torso: hips, belly, chest
    m.cube("hips", (-tw + 0.5, 4.5 * k, -td + 0.25), (tw - 0.5, 7 * k, td - 0.25), shirt, body)
    m.cube("torso", (-tw, 7 * k, -td), (tw, 11.75 * k, td), shirt, chest,
           decal=buttons_decal(N.get("trim", "#c8a040")) if N.get("coat") else None)
    m.cube("belly", (-tw + 0.75, 6 * k, -td - 0.75), (tw - 0.75, 9.5 * k, -td), shirt, body)
    m.cube("collar", (-tw + 1, 11.75 * k, -td + 0.5), (tw - 1, 12.5 * k, td - 0.5), F, chest)
    m.cube("belt", (-tw - 0.25, 6.75 * k, -td - 0.5), (tw + 0.25, 7.5 * k, td + 0.25), leatherm, body)
    m.cube("buckle", (-0.75, 6.5 * k, -td - 1.0), (0.75, 7.75 * k, -td - 0.5), trim, body)
    # outfit layers
    if N.get("apron"):
        am = leatherm if N["apron"] == "leather" else Mat("hide", from_base("#a87040", 6), "leather", base=3, stitch=False)
        m.cube("apron", (-tw + 0.5, 2.5 * k, -td - 1.25), (tw - 0.5, 10.5 * k, -td - 0.75), am, body)
        m.cube("apron_strap", (-tw + 1.0, 10.5 * k, -td - 0.5), (tw - 1.0, 11.75 * k, -td), am, chest)
        m.cube("apron_pocket", (-1.5, 5 * k, -td - 1.5), (1.5, 6.5 * k, -td - 1.25), am.variant("pocket", base=2), body)
    if N.get("coat"):
        c = cloth(N["coat"], trim=1)
        m.cube("coat_tail_right", (0.25, 3 * k, -td - 0.5), (tw + 0.25, 7 * k, td + 0.25), c, body)
        m.cube("coat_tail_left", (-tw - 0.25, 3 * k, -td - 0.5), (-0.25, 7 * k, td + 0.25), c, body)
        m.cube("lapel_right", (0.25, 9 * k, -td - 0.4), (1.75, 11.75 * k, -td), trim, chest)
        m.cube("lapel_left", (-1.75, 9 * k, -td - 0.4), (-0.25, 11.75 * k, -td), trim, chest)
    if N.get("robe"):
        r = cloth(N["robe"], trim=1)
        m.cube("robe_skirt", (-tw - 0.5, 1.0, -td - 0.5), (tw + 0.5, 7 * k, td + 0.5), r, body)
        m.cube("robe_hem", (-tw - 0.75, 0.75, -td - 0.75), (tw + 0.75, 1.75, td + 0.75), trim, body)
        m.cube("sash", (-tw - 0.3, 8.5 * k, -td - 0.4), (tw + 0.3, 9.25 * k, td + 0.3), trim, chest, rotation=(0, 0, -12), origin=(0, 8.9 * k, 0))
    if N.get("tabard"):
        t = cloth(N["tabard"], trim=1)
        m.cube("tabard", (-tw + 0.75, 2.5 * k, -td - 0.75), (tw - 0.75, 11.5 * k, -td - 0.25), t, body,
               decal=lambda a, f, w, h, c, rng: [put(a, x, y, (224, 176, 64)) for y in range(h // 3, h // 3 + 5) for x in range(w // 2 - 1, w // 2 + 1)] +
               [put(a, x, h // 3 + 1, (224, 176, 64)) for x in range(w // 2 - 3, w // 2 + 3)] if f == "north" else None)
        m.cube("pauldron_right", (tw - 0.5, 10.5 * k, -td - 0.25), (tw + 1.75, 12.25 * k, td + 0.25), iron, chest)
        m.cube("pauldron_left", (-tw - 1.75, 10.5 * k, -td - 0.25), (-tw + 0.5, 12.25 * k, td + 0.25), iron, chest)
    if N.get("satchel"):
        m.cube("satchel_strap", (-tw - 0.3, 7 * k, -td - 0.3), (tw + 0.3, 7.75 * k, td + 0.3), leatherm, chest, rotation=(0, 0, 35), origin=(0, 9.5 * k, 0))
        m.cube("satchel", (-tw - 1.75, 5 * k, -1.5), (-tw - 0.25, 7.5 * k, 1.5), leatherm, body)
    # arms: upper sleeve, forearm, paw
    for g, s, nm in ((arm_r, 1, "right"), (arm_l, -1, "left")):
        aw = 1.5 if burly else 1.25
        cx = s * (tw + 1.25)
        m.cube(f"sleeve_{nm}", (cx - aw, 8.5 * k, -aw), (cx + aw, 12 * k, aw), shirt, g)
        m.cube(f"forearm_{nm}", (cx - aw + 0.25, 6.5 * k, -aw + 0.25), (cx + aw - 0.25, 8.75 * k, aw - 0.25), F, g)
        m.cube(f"cuff_{nm}", (cx - aw - 0.25, 8.25 * k, -aw - 0.25), (cx + aw + 0.25, 9 * k, aw + 0.25), trim if N.get("trim") else shirt, g)
        paw_g = hand_r if s > 0 else g
        m.cube(f"paw_{nm}", (cx - aw, 5 * k, -aw), (cx + aw, 6.75 * k, aw), F, paw_g)
    # head: big, wider than the torso
    hw, hd, hh = (5.0, 4.25, 8.5) if not burly else (5.25, 4.5, 8.25)
    ytop = hy + hh
    m.cube("head_box", (-hw, hy + 0.25, -hd), (hw, ytop, hd), F, head)
    m.cube("face_plate", (-hw + 0.75, hy + 1.0, -hd - 0.5), (hw - 0.75, ytop - 1.5, -hd), FACE, head, decal=eyes_decal(N))
    m.cube("cheek_right", (hw - 0.25, hy + 1.0, -hd + 1), (hw + 0.5, hy + 4.0, hd - 1.5), F, head)
    m.cube("cheek_left", (-hw - 0.5, hy + 1.0, -hd + 1), (-hw + 0.25, hy + 4.0, hd - 1.5), F, head)
    m.cube("brow", (-hw + 0.5, ytop - 1.75, -hd - 0.75), (hw - 0.5, ytop - 1.0, -hd), F, head)
    if N["snout"]:
        sl = N["snout"]
        m.cube("snout", (-1.75, hy + 1.0, -hd - 0.5 - sl), (1.75, hy + 3.5, -hd - 0.5), FACE, head, decal=snout_decal(N))
        m.cube("nose", (-0.75, hy + 3.0, -hd - 0.75 - sl), (0.75, hy + 3.75, -hd - 0.25 - sl), Mat("nose", ramp("#1a1218", "#2a2026", "#3a2e34", "#544650"), "plain", base=2), head)
        if N.get("teeth"):
            m.cube("teeth", (-0.75, hy + 0.25, -hd - 0.25 - sl), (0.75, hy + 1.0, -hd + 0.25 - sl), Mat("teeth", ramp("#c8b890", "#e0d4b0", "#f0e8cc"), "plain", base=1), head)
    if N.get("beak"):
        m.cube("beak", (-0.75, hy + 2.0, -hd - 2.0), (0.75, hy + 3.75, -hd - 0.5), Mat("beak", GOLD, "metal", base=4), head)
        m.cube("beak_tip", (-0.5, hy + 1.25, -hd - 1.75), (0.5, hy + 2.0, -hd - 1.0), Mat("beak", GOLD, "metal", base=3), head)
    # ears
    e = N["ears"]
    ear_in = Mat("ear_in", from_base("#d89090", 6), "skin", base=3)
    for s, nm in ((1, "right"), (-1, "left")):
        if e == "tall":
            m.cube(f"ear_{nm}", (s * 3.0 - 1.5, ytop - 0.5, -0.75), (s * 3.0 + 1.5, ytop + 5.5, 0.75), F, head, rotation=(0, 0, -s * 18), origin=(s * 3.0, ytop, 0))
            m.cube(f"ear_{nm}_inner", (s * 3.0 - 0.75, ytop + 0.5, -1.0), (s * 3.0 + 0.75, ytop + 4.5, -0.75), ear_in, head, rotation=(0, 0, -s * 18), origin=(s * 3.0, ytop, 0))
            m.cube(f"ear_{nm}_tip", (s * 3.0 - 0.75, ytop + 5.5, -0.5), (s * 3.0 + 0.75, ytop + 6.75, 0.5), F, head, rotation=(0, 0, -s * 18), origin=(s * 3.0, ytop, 0))
        elif e == "long":
            m.cube(f"ear_{nm}", (s * 2.25 - 1.0, ytop - 0.5, -0.5), (s * 2.25 + 1.0, ytop + 7.0, 0.75), F, head, rotation=(-10, 0, -s * 8), origin=(s * 2.25, ytop, 0))
            m.cube(f"ear_{nm}_inner", (s * 2.25 - 0.5, ytop + 0.5, -0.75), (s * 2.25 + 0.5, ytop + 6.0, -0.5), ear_in, head, rotation=(-10, 0, -s * 8), origin=(s * 2.25, ytop, 0))
        elif e == "round":
            m.cube(f"ear_{nm}", (s * 3.75 - 1.25, ytop - 1.0, -0.5), (s * 3.75 + 1.25, ytop + 1.25, 0.75), F, head)
            m.cube(f"ear_{nm}_inner", (s * 3.75 - 0.75, ytop - 0.5, -0.75), (s * 3.75 + 0.75, ytop + 0.75, -0.5), ear_in, head)
        elif e == "tufts":
            m.cube(f"tuft_{nm}", (s * 3.5 - 0.75, ytop - 0.5, -1.0), (s * 3.5 + 0.75, ytop + 2.5, 0.0), F, head, rotation=(0, 0, -s * 25), origin=(s * 3.5, ytop, 0))
    # hats
    hat = N.get("hat")
    hc = cloth(N.get("hat_col", "#5a5a5a"))
    if hat == "bandana":
        m.cube("bandana", (-hw - 0.25, ytop - 2.0, -hd - 0.25), (hw + 0.25, ytop + 0.5, hd + 0.25), hc, head)
        m.cube("bandana_knot", (-0.75, ytop - 2.0, hd + 0.25), (0.75, ytop - 0.5, hd + 1.5), hc, head)
    elif hat == "fez":
        m.cube("fez", (-2.25, ytop - 0.25, -2.25), (2.25, ytop + 3.0, 2.25), hc, head)
        m.cube("fez_tassel", (2.25, ytop + 0.5, -0.25), (2.75, ytop + 3.0, 0.25), trim, head)
    elif hat == "straw":
        m.cube("hat_brim", (-hw - 1.75, ytop - 0.25, -hd - 1.75), (hw + 1.75, ytop + 0.5, hd + 1.75), Mat("straw", STRAW, "wood", base=3, grain_step=2), head)
        m.cube("hat_crown", (-3.0, ytop + 0.5, -2.75), (3.0, ytop + 2.75, 2.75), Mat("straw", STRAW, "wood", base=3, grain_step=2), head)
        m.cube("hat_band", (-3.25, ytop + 0.5, -3.0), (3.25, ytop + 1.25, 3.0), cloth("#8a2a2a"), head)
        m.cube("hat_flower", (2.5, ytop + 0.75, -3.25), (3.5, ytop + 1.75, -2.75), Mat("flower", from_base("#e8c040"), "gem", base=4), head)
    elif hat == "cap":
        m.cube("cap", (-hw + 0.25, ytop - 0.5, -hd + 0.25), (hw - 0.25, ytop + 1.5, hd - 0.25), hc, head)
        m.cube("cap_peak", (-2.5, ytop - 0.25, -hd - 2.0), (2.5, ytop + 0.25, -hd + 0.25), hc, head)
    elif hat == "bucket":
        m.cube("hat_crown", (-hw + 0.5, ytop - 0.5, -hd + 0.5), (hw - 0.5, ytop + 2.5, hd - 0.5), hc, head)
        m.cube("hat_brim", (-hw - 1.0, ytop - 0.75, -hd - 1.0), (hw + 1.0, ytop - 0.25, hd + 1.0), hc, head)
        m.cube("hat_lure", (hw - 1.5, ytop + 0.5, -hd + 0.25), (hw - 0.5, ytop + 1.5, -hd + 0.75), Mat("lure", from_base("#d83a2a"), "gem", base=4), head)
    elif hat == "helmet":
        m.cube("helmet", (-hw - 0.25, ytop - 2.5, -hd - 0.25), (hw + 0.25, ytop + 1.0, hd + 0.25), iron, head)
        m.cube("helmet_crest", (-0.5, ytop + 1.0, -hd), (0.5, ytop + 2.5, hd), cloth("#b02a2a"), head)
        m.cube("helmet_nasal", (-0.5, hy + 4.5, -hd - 0.75), (0.5, ytop - 2.5, -hd - 0.25), iron, head)
    # tail
    tail = m.group("tail", (0, 5 * k, td), body)
    if N["species"] in ("fennec", "fox"):
        m.cube("tail_base", (-1.25, 3.5 * k, td), (1.25, 6 * k, td + 3), F, tail, rotation=(-30, 0, 0), origin=(0, 5 * k, td))
        m.cube("tail_tip", (-1.0, 3.0 * k, td + 3), (1.0, 4.5 * k, td + 5), FACE, tail, rotation=(-30, 0, 0), origin=(0, 5 * k, td))
    elif N["species"] == "beaver":
        m.cube("tail_paddle", (-1.75, 0.5, td), (1.75, 1.25, td + 5), Mat("scales", from_base("#3a2a24", 6), "leather", base=3), tail)
    elif N["species"] == "rabbit":
        m.cube("tail_puff", (-1.0, 4.5 * k, td), (1.0, 6 * k, td + 1.5), FACE, tail)
    # props held in the right paw (hand at x = tw + 1.25, y = 5.5k)
    px, py = tw + 1.25, 5.5 * k
    p = N["prop"]
    if p == "hammer":
        m.cube("hammer_handle", (px - 0.4, py - 1.5, -4.5), (px + 0.4, py - 0.75, 1.0), wood, prop)
        m.cube("hammer_head", (px - 1.25, py - 2.25, -6.5), (px + 1.25, py + 0.25, -4.5), iron, prop)
    elif p == "scroll":
        m.cube("scroll", (px - 0.75, py - 3, -1.5), (px + 0.75, py + 2, 0), Mat("paper", PAPER, "cloth", base=3, fold=6), prop)
        m.cube("scroll_ribbon", (px - 0.9, py - 0.75, -1.6), (px + 0.9, py - 0.25, 0.1), cloth("#a42a2a"), prop)
    elif p == "scraper":
        m.cube("scraper_handle", (px - 0.4, py - 1.25, -3.0), (px + 0.4, py - 0.5, 0.5), wood, prop)
        m.cube("scraper_blade", (px - 1.5, py - 1.5, -4.0), (px + 1.5, py - 0.25, -3.0), iron, prop)
    elif p == "basket":
        b = Mat("wicker", STRAW, "rope", base=3)
        m.cube("basket", (px - 1.5, py - 4.5, -2), (px + 1.5, py - 1.75, 2), b, prop)
        m.cube("basket_handle", (px - 0.25, py - 1.75, -1.5), (px + 0.25, py + 0.75, 1.5), b, prop)
        m.cube("herbs", (px - 1.25, py - 2.0, -1.75), (px + 1.25, py - 1.0, 1.75), Mat("herbs", from_base("#4a8a2a"), "fur", base=3), prop)
    elif p == "saw":
        m.cube("saw_handle", (px - 0.5, py - 1.5, -1.0), (px + 0.5, py + 0.25, 1.0), wood, prop)
        m.cube("saw_blade", (px - 0.2, py - 1.25, -8.0), (px + 0.2, py + 0.25, -1.0), iron.variant("blade", base=3, polish=True), prop)
    elif p == "rod":
        m.cube("rod", (px - 0.3, py - 1.5, -0.3), (px + 0.3, py + 16, 0.3), wood, prop, rotation=(-25, 0, 0), origin=(px, py - 1, 0))
        m.cube("reel", (px - 0.75, py, -0.75), (px + 0.75, py + 1, 0.75), iron, prop, rotation=(-25, 0, 0), origin=(px, py - 1, 0))
    elif p == "spear":
        m.cube("spear_shaft", (px - 0.4, 0.5, -0.4), (px + 0.4, py + 16, 0.4), wood, prop)
        m.cube("spear_head", (px - 0.9, py + 16, -0.3), (px + 0.9, py + 19, 0.3), iron.variant("blade", base=3, polish=True), prop)
        m.cube("spear_tip", (px - 0.4, py + 19, -0.25), (px + 0.4, py + 20.25, 0.25), iron.variant("blade", base=4, polish=True), prop)
    elif p == "book":
        m.cube("book", (px - 1.5, py - 3.0, -2.25), (px + 0.5, py, 0.75), Mat("cover", from_base("#6a2a2a"), "leather", base=3), prop)
        m.cube("book_pages", (px + 0.5, py - 2.75, -2.0), (px + 0.75, py - 0.25, 0.5), Mat("paper", PAPER, "plain", base=3), prop)

    m.scale_dummy((12, 0, 0))
    animate(m, N, k, tw)
    return m


def animate(m, N, k, tw):
    """idle, talk, wave, work, walk (section 3.8). Rotations in degrees about each bone's pivot."""
    m.anim("idle", 2.4, {
        "chest": {"scale": [(0, (1, 1, 1)), (1.2, (1.02, 1.03, 1.02)), (2.4, (1, 1, 1))]},
        "head": {"rotation": [(0, (0, 0, 0)), (0.8, (3, -4, 0)), (1.6, (-2, 3, 2)), (2.4, (0, 0, 0))]},
        "arm_right": {"rotation": [(0, (0, 0, 2)), (1.2, (0, 0, 5)), (2.4, (0, 0, 2))]},
        "arm_left": {"rotation": [(0, (0, 0, -2)), (1.2, (0, 0, -5)), (2.4, (0, 0, -2))]},
    })
    m.anim("talk", 1.6, {
        "head": {"rotation": [(0, (0, 0, 0)), (0.4, (-6, 0, 3)), (0.8, (4, 0, -2)), (1.2, (-4, 4, 0)), (1.6, (0, 0, 0))]},
        "arm_left": {"rotation": [(0, (0, 0, -5)), (0.4, (35, 0, -15)), (0.8, (20, 10, -10)), (1.2, (40, -10, -20)), (1.6, (0, 0, -5))]},
        "chest": {"rotation": [(0, (0, 0, 0)), (0.8, (0, 5, 0)), (1.6, (0, 0, 0))]},
    })
    m.anim("wave", 1.2, {
        "arm_left": {"rotation": [(0, (0, 0, -150)), (0.3, (0, 0, -125)), (0.6, (0, 0, -155)), (0.9, (0, 0, -125)), (1.2, (0, 0, -150))]},
        "head": {"rotation": [(0, (0, 0, 6)), (0.6, (0, 0, 10)), (1.2, (0, 0, 6))]},
    })
    m.anim("work", 1.0, {
        "arm_right": {"rotation": [(0, (110, 0, 0)), (0.45, (110, 0, 0), "catmullrom"), (0.6, (-10, 0, 0), "linear"), (0.75, (0, 0, 0)), (1.0, (110, 0, 0))]},
        "chest": {"rotation": [(0, (-4, 0, 0)), (0.6, (6, 0, 0)), (1.0, (-4, 0, 0))]},
        "head": {"rotation": [(0, (-4, 0, 0)), (0.6, (8, 0, 0)), (1.0, (-4, 0, 0))]},
    })
    sw = 25
    m.anim("walk", 1.0, {
        "leg_right": {"rotation": [(0, (sw, 0, 0)), (0.5, (-sw, 0, 0)), (1.0, (sw, 0, 0))]},
        "leg_left": {"rotation": [(0, (-sw, 0, 0)), (0.5, (sw, 0, 0)), (1.0, (-sw, 0, 0))]},
        "arm_right": {"rotation": [(0, (-20, 0, 0)), (0.5, (20, 0, 0)), (1.0, (-20, 0, 0))]},
        "arm_left": {"rotation": [(0, (20, 0, 0)), (0.5, (-20, 0, 0)), (1.0, (20, 0, 0))]},
        "body": {"position": [(0, (0, 0, 0)), (0.25, (0, 0.5, 0)), (0.5, (0, 0, 0)), (0.75, (0, 0.5, 0)), (1.0, (0, 0, 0))]},
    })


def main():
    paths = []
    for N in NPCS:
        m = build(N)
        p, n, size = m.save(OUT, TEX)
        paths.append(p)
        print(f"{Path(p).name}: {n} cubes, texture {size}")
    subprocess.run([sys.executable, str(HERE.parent / "make_lineup.py"), str(OUT / "npcs_lineup.bbmodel"), "18", "4", *paths], check=True)


if __name__ == "__main__":
    main()
