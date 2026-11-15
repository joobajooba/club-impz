"""Hub town plan (J00BA, 2026-11-09): a flat hub inside a square of castle walls, laid out as a small walled town.

Writes godot-game/data/hub_town.json, read by the terrain bake (scripts/tools/bake_world_data.gd: streets and
squares painted into hub_mask.png, flat ground) and by scripts/world/hub_town.gd (models, colliders, lights, NPC
spots). Also renders a top-down plan to --preview <png>.

Coordinates: metres, x east, z south (north = -z). Every Blockbench model faces north (-z); yaw turns it
(Godot rotation.y): N = 0, W = 90, S = 180, E = -90.

Layout (walls at +-75, 150 m square):
  north   castle (2.5x) with a cobbled forecourt; formal gardens either side (hedges, topiary, blossom trees)
  centre  town square on the grand avenue, blossom tree centrepiece, plaza lamps, urns
  east    market square: eight stalls facing each other across Market Street (vendor NPC spots)
  west    crafters' yard: smithing, carpentry, leather and herb drying, brewing (NPC spots at each station)
  south   two residential lanes of houses, an orchard strip, and the portal plaza at the south gate
Streets are cobbled (mask B); garden and orchard walks are dirt (mask R). Main routes are straight and wide:
portal -> avenue -> square -> castle, and Market Street west <-> east through the square.
Usage: py "build scripts/build_hub_town.py" [--preview out.png]"""
import json, math, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAME = os.path.join(ROOT, "godot-game")
U = 1.0 / 16.0
W = 75.0                 # wall line (inner face is at W - 0.6)

MODELS = {
    # alias: (res path, bbmodel path relative to godot-game, default scale)
    "castle": ("res://assets/models/buildings/hub_castle.glb", "assets/models/buildings/hub_castle.bbmodel", 2.5),
    "wall": ("res://assets/models/buildings/walls/hub_wall_segment.glb", "assets/models/buildings/walls/hub_wall_segment.bbmodel", 2.5),
    "wall_half": ("res://assets/models/buildings/walls/hub_wall_segment_half.glb", "assets/models/buildings/walls/hub_wall_segment_half.bbmodel", 2.5),
    "pillar": ("res://assets/models/buildings/walls/hub_wall_pillar.glb", "assets/models/buildings/walls/hub_wall_pillar.bbmodel", 2.5),
}
for n in ("brick_bluebell_house", "brick_honey_townhouse", "brick_rose_cottage", "wood_cherry_manor", "wood_oak_lodge", "wood_timber_house"):
    MODELS[n] = (f"res://assets/models/buildings/houses/{n}.glb", f"assets/models/buildings/houses/{n}.bbmodel", 1.5)
for n in ("fruit", "bakery", "potion", "cloth"):
    MODELS[f"stall_{n}"] = (f"res://assets/models/buildings/stalls/market_stall_{n}.glb", f"assets/models/buildings/stalls/market_stall_{n}.bbmodel", 1.0)
for n in ("furnace", "anvil", "workbench", "sawbench", "drying_rack", "tanning_rack", "cauldron"):
    MODELS[n] = (f"res://assets/models/props/stations/{n}.glb", f"assets/models/props/stations/{n}.bbmodel", 1.0)
for n in ("street_lamp", "street_lamp_double", "plaza_lamp", "wall_lantern", "path_lantern"):
    MODELS[n] = (f"res://assets/models/props/lamps/{n}.glb", f"assets/models/props/lamps/{n}.bbmodel", 1.0)
for n in ("planter_square_flowers", "planter_trough_flowers", "urn_planter", "topiary_ball_planter", "topiary_tiered_planter",
          "hedge_segment", "blossom_tree_planter"):
    MODELS[n] = (f"res://assets/models/foliage/town/{n}.glb", f"assets/models/foliage/town/{n}.bbmodel", 1.0)

for n in ("workshop_shelter_timber", "workshop_shelter_forge", "workshop_shelter_apothecary", "fence_rail", "fence_rail_short", "fence_post", "log_pile",
          "lumber_stack", "coal_ore_bins", "tool_rack", "quench_trough", "crate_stack", "tannery_vats", "potion_shelf", "herb_bed",
          "sign_smelter", "sign_blacksmith", "sign_carpenter", "sign_sawyer", "sign_tanner", "sign_herbalist", "sign_brewer"):
    MODELS[n] = (f"res://assets/models/props/workshop/{n}.glb", f"assets/models/props/workshop/{n}.bbmodel", 1.0)

MODELS["rose"] = ("res://assets/models/foliage/rose_flower.glb", "assets/models/foliage/rose_flower.bbmodel", 1.0)
MODELS["wizard_tower"] = ("res://assets/models/buildings/wizard_tower.glb", "assets/models/buildings/wizard_tower.bbmodel", 1.5)
for n in ("arcane_circle", "crystal_cluster", "crystal_cluster_small", "spellbook_lectern", "arcane_lamp"):
    MODELS[n] = (f"res://assets/models/props/arcane/{n}.glb", f"assets/models/props/arcane/{n}.bbmodel", 1.0)

HOUSES = ["brick_rose_cottage", "wood_timber_house", "brick_bluebell_house", "wood_oak_lodge", "brick_honey_townhouse", "wood_cherry_manor"]
FACE = {"N": 0.0, "W": 90.0, "S": 180.0, "E": -90.0}


# ---------------------------------------------------------------- model metrics from the .bbmodel files
def metrics(bb_rel):
    d = json.load(open(os.path.join(GAME, bb_rel), encoding="utf8"))
    E = [e for e in d["elements"] if e.get("export", True)]
    solid = [e for e in E if all(e["to"][i] - e["from"][i] > 0.01 for i in range(3)) and not e.get("rotation")]
    ground = [e for e in solid if e["from"][1] <= 1.01] or solid or E   # all-card models (the rose): every cube
    fp = [min(e["from"][0] for e in ground) * U, min(e["from"][2] for e in ground) * U,
          max(e["to"][0] for e in ground) * U, max(e["to"][2] for e in ground) * U]
    full = [min(e["from"][0] for e in E) * U, min(e["from"][2] for e in E) * U, max(e["to"][0] for e in E) * U, max(e["to"][2] for e in E) * U]
    h = max(e["to"][1] for e in E) * U
    lights = [[round(g["origin"][0] * U, 3), round(g["origin"][1] * U, 3), round(g["origin"][2] * U, 3)]
              for g in d["groups"] if g["name"].startswith("light_")]
    glow = any(e["name"].endswith("_glow") for e in E)
    parts = [[round(e["from"][0] * U, 3), round(e["from"][2] * U, 3), round(e["to"][0] * U, 3), round(e["to"][2] * U, 3),
              round(e["to"][1] * U, 3)] for e in ground if (e["to"][1] - e["from"][1]) * U >= 0.5]
    return {"footprint": [round(v, 3) for v in fp], "extent": [round(v, 3) for v in full], "height": round(h, 3), "lights": lights,
            "glow": glow, "parts": parts, "animated": bool(d.get("animations"))}


INFO = {}
for a, (res, bb, s) in MODELS.items():
    INFO[a] = {"path": res, "scale": s, **metrics(bb)}


# ---------------------------------------------------------------- plan state
placements, colliders, no_scatter, npc_spots, lights = [], [], [], [], []
cobble, dirt, dirt_rects, landmarks = [], [], [], {}


def rot(lx, lz, yaw):
    t = math.radians(yaw)
    return math.cos(t) * lx + math.sin(t) * lz, -math.sin(t) * lx + math.cos(t) * lz


def world_rect(alias, x, z, yaw, s, which="footprint", pad=0.0):
    x1, z1, x2, z2 = INFO[alias][which]
    pts = [rot(px * s, pz * s, yaw) for px, pz in ((x1, z1), (x2, z1), (x2, z2), (x1, z2))]
    return [round(min(p[0] for p in pts) + x - pad, 2), round(min(p[1] for p in pts) + z - pad, 2),
            round(max(p[0] for p in pts) + x + pad, 2), round(max(p[1] for p in pts) + z + pad, 2)]


def place(alias, x, z, yaw=0.0, s=None, collide=True, y=0.0, light=True, max_h=6.0):
    """Place a model. Colliders are the model's ground footprint (solid cubes touching the ground), so overhangs,
    awnings and roofs don't block, up to max_h tall."""
    s = INFO[alias]["scale"] if s is None else s
    yaw = FACE.get(yaw, yaw) if isinstance(yaw, str) else yaw
    placements.append([alias, round(x, 3), round(y, 3), round(z, 3), round(yaw, 2), s])
    if y == 0.0:
        no_scatter.append(world_rect(alias, x, z, yaw, s, "extent" if alias.startswith(("stall_", "hedge")) else "footprint", 0.3))
    # collide: True = one box round the ground footprint; "parts" = a box per solid ground cube (open shelters: the
    # posts and back wall block, the space under the roof doesn't); "extent" = the whole model's plan (fences)
    if collide == "parts":
        boxes = [(p[0], p[1], p[2], p[3], min(p[4], max_h)) for p in INFO[alias]["parts"]]
    elif collide == "extent":
        x1, z1, x2, z2 = INFO[alias]["extent"]; boxes = [(x1, z1, x2, z2, min(INFO[alias]["height"], max_h))]
    elif collide:
        x1, z1, x2, z2 = INFO[alias]["footprint"]; boxes = [(x1, z1, x2, z2, min(INFO[alias]["height"], max_h))]
    else:
        boxes = []
    for x1, z1, x2, z2, hh in boxes:
        cx, cz = rot((x1 + x2) / 2 * s, (z1 + z2) / 2 * s, yaw)
        h = min(hh * s, max_h)
        colliders.append([round(x + cx, 3), round(y + h / 2, 3), round(z + cz, 3), round(max(0.2, (x2 - x1) * s), 3), round(h, 3),
                          round(max(0.2, (z2 - z1) * s), 3), round(yaw, 2)])
    if light and INFO[alias]["lights"] and alias != "path_lantern":       # path lanterns only glow
        L = INFO[alias]["lights"]
        # one light per lamp at the mean of its lanterns (multi-lantern lamps get one brighter light)
        mx = sum(p[0] for p in L) / len(L); my = sum(p[1] for p in L) / len(L); mz = sum(p[2] for p in L) / len(L)
        lx, lz = rot(mx * s, mz * s, yaw)
        lights.append([round(x + lx, 2), round(y + my * s, 2), round(z + lz, 2), len(L), alias])
    return placements[-1]


def npc(name, x, z, yaw, role):
    npc_spots.append({"name": name, "pos": [round(x, 2), 0.0, round(z, 2)], "yaw": FACE.get(yaw, yaw) if isinstance(yaw, str) else yaw, "role": role})


def local_to_world(x, z, yaw, lx, lz):
    dx, dz = rot(lx, lz, yaw)
    return x + dx, z + dz


def street(x1, z1, x2, z2):
    cobble.append([x1, z1, x2, z2])


# ---- hedges and roses in order (J00BA, 2026-11-09: "make the bushes more symmetrical and have order ... make them
# connect up where possible"). Hedges are laid as unbroken straight runs of whole segments, gaps only where a walk
# goes through (centred on it), corners meeting flush; roses stand in even rows along the hedges.
HEDGE_S = 1.5
HEDGE_LEN = 3.0                                                   # one hedge_segment at 1.5x (2 m model)
HEDGE_HALF = 0.6                                                  # half its thickness, for flush corners


def hedge_run(a, b):
    """Hedge segments end to end from a to b (a straight line along x or z, a whole number of segments)."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = round(L / HEDGE_LEN)
    assert abs(n * HEDGE_LEN - L) < 0.01 and n > 0, f"hedge run {a} -> {b}: {L} m is not whole segments"
    along_x = abs(b[1] - a[1]) < 1e-6
    for k in range(n):
        t = (k + 0.5) / n
        place("hedge_segment", a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t, 0 if along_x else 90, s=HEDGE_S)


def rose_row(a, b, step=1.5, skip=()):
    """Rose bushes evenly along a line (half a step in from each end), leaving out any within 0.9 m of a skip point."""
    L = math.hypot(b[0] - a[0], b[1] - a[1]); n = max(1, round(L / step))
    for k in range(n):
        t = (k + 0.5) / n
        x, z = a[0] + (b[0] - a[0]) * t, a[1] + (b[1] - a[1]) * t
        if any(math.hypot(x - q[0], z - q[1]) < 0.9 for q in skip):
            continue
        place("rose", x, z, (k * 47) % 360, collide=False)


def earth(x1, z1, x2, z2):
    """A packed-earth floor (mask R, the dirt path layer) for a rectangle."""
    dirt_rects.append([x1, z1, x2, z2])


def walk(pts, r=1.3):
    dirt.append({"points": pts, "radius": r})


# ================================================================ 1. town walls (castle wall kit at 2.5x)
SEG = 5.0                                # 32 units x 2.5 / 16
for side in ("N", "S", "E", "W"):
    for i in range(30):
        u = -W + SEG / 2 + i * SEG
        if side == "N": place("wall", u, -W, 0, collide=False)
        elif side == "S": place("wall", u, W, 180, collide=False)
        elif side == "E": place("wall", W, u, -90, collide=False)
        else: place("wall", -W, u, 90, collide=False)
for i in range(11):
    u = -W + i * 15.0
    for (x, z) in ((u, -W), (u, W), (-W, u), (W, u)):
        if (x, z) not in [tuple(p[1:4:2]) for p in placements if p[0] == "pillar"]:
            place("pillar", x, z, 0, collide=False)
# wall colliders: one long box per side (taller than the wall so nobody hops the coping)
for (x, z, sx, sz) in ((0, -W, 2 * W + 2, 1.4), (0, W, 2 * W + 2, 1.4), (-W, 0, 1.4, 2 * W + 2), (W, 0, 1.4, 2 * W + 2)):
    colliders.append([x, 3.0, z, sx, 6.0, sz, 0.0])
# wall lanterns on the inner face of every pillar except the corners and the ones behind buildings
for i in range(1, 10):
    u = -W + i * 15.0
    for side, (x, z, yaw) in (("N", (u, -W + 0.95, 180)), ("S", (u, W - 0.95, 0)), ("E", (W - 0.95, u, 90)), ("W", (-W + 0.95, u, -90))):
        if side == "N" and abs(u) < 25: continue            # behind the castle
        place("wall_lantern", x, z, yaw, s=1.6, y=1.6, collide=False, light=False)

# ================================================================ 2. castle and forecourt (north)
CZ = -60.0
place("castle", 0, CZ, "S", collide=False)
landmarks["castle"] = [0, CZ]
FC = (-17.0, -50.5, 17.0, -36.0)                       # forecourt
street(*FC)
npc("castle_herald", 3.2, -48.6, "S", "herald / quest giver at the castle steps")
for sx in (-1, 1):
    place("topiary_tiered_planter", sx * 6.5, -48.5, "S", s=1.4)
    place("plaza_lamp", sx * 14.5, -38.5, "S")
    place("urn_planter", sx * 14.5, -48.5, "S", s=1.3)
    place("planter_trough_flowers", sx * 10.0, -51.8, "S")

# ================================================================ 3. grand avenue and town square (centre)
street(-4.5, -36.0, 4.5, 56.0)                          # avenue: castle -> square -> portal plaza
SQ = (-17.0, -30.0, 17.0, -2.0)
street(*SQ)
landmarks["town_square"] = [0, -16]
place("blossom_tree_planter", 0, -16, 0, s=2.2)
for sx in (-1, 1):
    for sz in (-1, 1):
        place("plaza_lamp", sx * 14.5, -16 + sz * 11.5, "N")
        place("urn_planter", sx * 6.5, -16 + sz * 6.5, "N", s=1.2)
for sx in (-1, 1):                                       # flower troughs along the square's quiet edges
    for z in (-26.5, -5.5):
        place("planter_trough_flowers", sx * 11.0, z + (-1.6 if z < -16 else 1.6) * 0, 0 if z > -16 else 180)

# ================================================================ 4. Market Street (east-west through the square)
street(-64.0, -20.0, 64.0, -12.0)
for x in (-24.0, 24.0):
    place("street_lamp_double", x, -21.6, "S")
    place("street_lamp_double", x, -10.4, "N")

# ================================================================ 5 + 6. market square (east) and crafters' yard (west)
# Both squares straddle Market Street: one row on each side, fronts facing the street, so shoppers and crafters
# walk straight along it. Hedges close the back edges (a gap where the lane connector comes in), flower troughs
# sit between the stalls, lamps on the corners, a blossom tree where the street meets the wall.
ROW_N, ROW_S = -24.0, -8.0
XS = (37.0, 44.0, 51.0, 58.0)


def vendor_spot(a, x, z, yaw, name, role, extent=True):
    fx1, fz1, fx2, fz2 = INFO[a]["extent" if extent else "footprint"]
    if extent:   # beside the counter's right end, facing the customers
        vx, vz = local_to_world(x, z, yaw, fx2 + 0.55, fz1 + 0.55)
        npc(name, vx, vz, yaw, role)
    else:        # in front of the station, facing it (working)
        vx, vz = local_to_world(x, z, yaw, 0.0, fz1 - 0.9)
        npc(name, vx, vz, (yaw + 180.0) % 360.0, role)


def square(sx, north, south, kind):
    x1, x2 = sorted((sx * 32.5, sx * 63.5))
    street(x1, -29.5, x2, -2.5)
    for i, x in enumerate(XS):
        for row, z, yaw in ((north, ROW_N, 180.0), (south, ROW_S, 0.0)):
            if i >= len(row) or row[i] is None: continue
            a, role = row[i]
            place(a, sx * x, z, yaw)
            stall = a.startswith("stall_")
            vendor_spot(a, sx * x, z, yaw, f"{'vendor' if stall else 'crafter'}_{role.replace(' ', '_')}",
                        f"{'market vendor' if stall else 'crafting station'} ({role})", extent=stall)
    for xm in (40.5, 54.5):                                   # troughs in the gaps, in line with the rows
        place("planter_trough_flowers", sx * xm, ROW_N - 0.6, 180)
        place("planter_trough_flowers", sx * xm, ROW_S + 0.6, 0)
    for (x, z) in ((33.5, -28.5), (62.5, -28.5), (33.5, -3.5), (62.5, -3.5)):
        place("street_lamp", sx * x, z, "N")
    for hz in (-30.6, -1.4):                                  # back hedges: gap centred on the garden walk / connector
        hedge_run((sx * 32.5, hz), (sx * 41.5, hz))
        hedge_run((sx * 46.5, hz), (sx * 64.5, hz))
    for x in (31.4, 65.6):                                    # topiary balls finishing the north hedge's ends
        place("topiary_ball_planter", sx * x, -30.6, "S")
    place("blossom_tree_planter", sx * 69.5, -16.0, 0, s=1.6)   # Market Street ends at a blossom tree by the wall
    for z in (-22.0, -10.0):
        place("urn_planter", sx * 66.5, z, "W" if sx > 0 else "E", s=1.2)
    for x in (31.0, 52.0, 62.0):                              # blossom trees on the lawn towards Rose Lane
        place("blossom_tree_planter", sx * x, 7.0, 0, s=1.2)


# ---- fences (J00BA, 2026-11-09: every run connects to another fence or ends in a post, never two posts in one spot)
# fence_rail is one rail length with its post on the west end (local -x); its open east end is closed by the next
# rail's post or by a fence_post. The pitches (post to open end) come from the models: 2 m and 1.1875 m.
def _rail_geom(alias):
    d = json.load(open(os.path.join(GAME, MODELS[alias][1]), encoding="utf8"))
    post = next(e for e in d["elements"] if e["name"] == "post")
    pc = (post["from"][0] + post["to"][0]) / 2 * U
    end = max(e["to"][0] for e in d["elements"] if e["name"].startswith("rail_")) * U
    return pc, end - pc                                          # post x (local), pitch


FENCE_SEGS = []                                                   # straight segments [(x, z), (x, z)]


def fence_run(points):
    """A fence along the corner points (a straight line per pair). Rails are laid when build_fences() runs, after
    every run is known, so shared corners and T joints get exactly one post."""
    for a, b in zip(points[:-1], points[1:]):
        FENCE_SEGS.append((tuple(map(float, a)), tuple(map(float, b))))


def _pieces(a, b):
    """Whole rails from a to b: as many full rails as fit, then one short rail for the rest (must fit exactly)."""
    full_x, full_p = _rail_geom("fence_rail")
    short_x, short_p = _rail_geom("fence_rail_short")
    L = math.hypot(b[0] - a[0], b[1] - a[1])
    n = int(L / full_p + 1e-6); rest = L - n * full_p
    kinds = ["fence_rail"] * n
    if rest > 1e-3:
        assert abs(rest - short_p) < 1e-3, f"fence {a} -> {b}: {L} m is not whole rails ({full_p} / {short_p})"
        kinds.append("fence_rail_short")
    ux, uz = (b[0] - a[0]) / L, (b[1] - a[1]) / L
    out, t = [], 0.0
    for k in kinds:
        px_, pt = _rail_geom(k)
        out.append((k, (a[0] + ux * t, a[1] + uz * t), (a[0] + ux * (t + pt), a[1] + uz * (t + pt)), px_))
        t += pt
    return out


def build_fences():
    """Lay every fence run: turn segments so no two rails put their post on the same point, then put a fence_post on
    every end that no rail's post covers."""
    key = lambda p: (round(p[0], 3), round(p[1], 3))
    flip = [False] * len(FENCE_SEGS)

    def pieces(i):
        a, b = FENCE_SEGS[i]
        return _pieces(b, a) if flip[i] else _pieces(a, b)

    def starts():
        c = {}
        for i in range(len(FENCE_SEGS)):
            for _, p0, _, _ in pieces(i):
                c[key(p0)] = c.get(key(p0), 0) + 1
        return c

    def clash():
        return sum(v - 1 for v in starts().values() if v > 1)
    # Each segment's first post goes on one of its two ends; a point can hold one post. Points inside a segment
    # (its rail joints) are already taken. Pick the ends by bipartite matching (augmenting paths), so T joints
    # and corners always find a free arrangement if there is one.
    taken = set()
    for i in range(len(FENCE_SEGS)):
        for _, p0, _, _ in _pieces(*FENCE_SEGS[i])[1:]:
            taken.add(key(p0))
    owner = {}                                                    # point -> segment whose first post stands there

    def assign(i, seen):
        a, b = FENCE_SEGS[i]
        for end, fl in ((key(a), False), (key(b), True)):
            if end in taken or end in seen:
                continue
            seen.add(end)
            if end not in owner or assign(owner[end], seen):
                owner[end] = i; flip[i] = fl
                return True
        return False
    for i in range(len(FENCE_SEGS)):
        if not assign(i, set()):
            raise SystemExit(f"fences: segment {FENCE_SEGS[i]} has no free end for its post")
    assert clash() == 0, f"fences: {clash()} doubled posts left"
    st = starts()
    ends = set()
    for i in range(len(FENCE_SEGS)):
        for alias, p0, p1, px_ in pieces(i):
            ux, uz = p1[0] - p0[0], p1[1] - p0[1]
            n = math.hypot(ux, uz); ux, uz = ux / n, uz / n
            yaw = math.degrees(math.atan2(-uz, ux))               # local +x (the open end) along the run
            ox, oz = p0[0] - ux * px_, p0[1] - uz * px_          # model origin: the post sits at local px_
            place(alias, ox, oz, round(yaw, 3), collide="extent")
            ends.add(key(p1))
    for e in sorted(ends):
        if e not in st:
            place("fence_post", e[0], e[1], 0.0, collide=False)


# ---- the crafters' yard: eight small workshops along Market Street, each its own plot (J00BA, 2026-11-09)
# Plot: 7.75 m along the street, 9.5 m deep. A lean-to shelter at the back (its lantern lights at night), the
# station under its front edge facing the street, the trade's props round it, fences between the plots and a
# short front fence each side of a 3.75 m gateway with the trade sign. Forge plots are cobbled, the rest earth.
# Local plot coordinates: lx along the street (east), d = metres from the back of the plot toward the street.
YARD_X = (-60.0, -52.0, -44.0, -36.0)       # 8 m plots: every plot edge is on the fences' 2 m post grid
PLOT_W, PLOT_D = 8.0, 9.5
# The front fence line: four 2 m rails and one short rail from the back of the plot (8 + 1.1875 = 9.1875 m). The
# gate sign stands at d = PLOT_D - 0.6 with a 0.19 m base, so a line at 9.0 would run through it; 9.1875 clears it.
FRONT_D = None
yard_plots, yard_rows = [], {}
YARD_PLOTS = {
    "north": [  # backs at z -29.5, fronts on Market Street (z -20)
        ("smelter", "furnace", -1.0, 3.4, "forge", True, [("coal_ore_bins", 1.4, 6.6, 0), ("crate_stack", 2.0, 1.3, 0)]),
        ("blacksmith", "anvil", -0.9, 3.6, "forge", True, [("tool_rack", 1.7, 0.9, 0), ("quench_trough", 0.9, 6.7, 0)]),
        ("carpenter", "workbench", -0.9, 3.3, "timber", False, [("lumber_stack", 0.8, 6.7, 0), ("crate_stack", 2.2, 1.3, 0)]),
        ("sawyer", "sawbench", -1.1, 3.4, "timber", False, [("log_pile", 0.4, 6.8, 0)]),
    ],
    "south": [  # backs at z -2.5, fronts on Market Street (z -12)
        ("tanner", "tanning_rack", -0.6, 3.3, "timber", False, [("tannery_vats", 0.6, 6.7, 0)]),
        ("herbalist", "drying_rack", -0.6, 3.4, "apothecary", False, [("herb_bed", 0.4, 6.8, 0)]),
        ("passage", None, 0.0, 0.0, None, True, []),      # open: Market Street -> the lane connector to Rose Lane
        ("brewer", "cauldron", -1.6, 3.5, "apothecary", True, [("potion_shelf", 1.8, 0.9, 0), ("stall_potion", 1.7, 7.0, 0)]),
    ],
}


def yard():
    global FRONT_D
    sx = -1
    FRONT_D = 4 * _rail_geom("fence_rail")[1] + _rail_geom("fence_rail_short")[1]
    landmarks["crafting_area"] = [-48.0, -16.0]
    x_edges = [YARD_X[0] - PLOT_W / 2] + [x + PLOT_W / 2 for x in YARD_X]
    for row, back_z, face in (("north", -29.5, 180.0), ("south", -2.5, 0.0)):
        dz = 1 if row == "north" else -1                       # direction from the back toward the street

        def at(cx, lx, d):
            return (cx + lx if row == "north" else cx - lx), back_z + dz * d

        for (trade, station, slx, sd, shelter, cob, props), cx in zip(YARD_PLOTS[row], YARD_X):
            x1, x2 = cx - PLOT_W / 2, cx + PLOT_W / 2
            z1, z2 = sorted((back_z, back_z + dz * PLOT_D))
            (street if cob else earth)(x1, z1, x2, z2)
            if trade == "passage":
                yard_plots.append({"name": trade, "rect": [x1, z1, x2, z2], "gate": [x1, x2], "front_z": back_z + dz * FRONT_D,
                                   "passage": True})
                continue
            if shelter:
                hx, hz = at(cx, 0.0, 2.2)
                place(f"workshop_shelter_{shelter}", hx, hz, face, collide="parts")
            if station:
                wx, wz = at(cx, slx, sd)
                place(station, wx, wz, face)
                vendor_spot(station, wx, wz, face, f"crafter_{trade}", f"crafting station ({trade})", extent=False)
                gx, gz = at(cx, -PLOT_W / 2 + 0.75, PLOT_D - 0.6)
                place(f"sign_{trade}", gx, gz, face + 180.0, collide=False)   # arm points into the gateway
            for a, lx, d, yl in props:
                px_, pz_ = at(cx, lx, d)
                place(a, px_, pz_, face + yl)
                if a.startswith("stall_"):                     # the brewer sells what they brew
                    vendor_spot(a, px_, pz_, face + yl, "vendor_potion_brewer", "potion seller at the brewery")
            # front fences: one 2 m rail from each plot corner to its side of the gateway
            for lx0, lx1 in ((-PLOT_W / 2, -PLOT_W / 2 + 2.0), (PLOT_W / 2, PLOT_W / 2 - 2.0)):
                fence_run([at(cx, lx0, FRONT_D), at(cx, lx1, FRONT_D)])
            gl, gr = sorted((at(cx, -PLOT_W / 2 + 2.0, 0)[0], at(cx, PLOT_W / 2 - 2.0, 0)[0]))
            yard_plots.append({"name": trade, "rect": [x1, z1, x2, z2], "gate": [gl, gr], "front_z": back_z + dz * FRONT_D})
        # side fences between the plots and at the yard ends, back to the front line (four 2 m rails and one short
        # rail), and a back fence behind the shelters closing each plot (open behind the passage)
        front_z = back_z + dz * FRONT_D
        for xe in x_edges:
            fence_run([(xe, back_z), (xe, front_z)])
        runs, cur = [], [x_edges[0]]
        for (trade, *_), xa, xb in zip(YARD_PLOTS[row], x_edges[:-1], x_edges[1:]):
            if trade == "passage":
                runs.append(cur); cur = [xb]
            else:
                cur.append(xb)
        runs.append(cur)
        for r_ in runs:
            if len(r_) > 1:
                fence_run([(r_[0], back_z), (r_[-1], back_z)])
        yard_rows[row] = {"back": back_z, "front": front_z}
    build_fences()
    place("blossom_tree_planter", -69.5, -16.0, 0, s=1.6)
    for z in (-22.0, -10.0):
        place("urn_planter", -66.5, z, "E", s=1.2)


landmarks["market"] = [47.5, -16]
square(1, [("stall_fruit", "fruit"), ("stall_bakery", "baker"), ("stall_cloth", "tailor"), ("stall_potion", "apothecary")],
       [("stall_cloth", "weaver"), ("stall_potion", "alchemist"), ("stall_fruit", "greengrocer"), ("stall_bakery", "pie seller")], "market")
yard()

# ================================================================ 7. castle gardens (north-west and north-east)
# The east garden is a formal garden. The west one is the wizard's garden (J00BA, 2026-11-09): the wizard tower
# stands at the head of its walk, behind the crafters' yard and its brewer, herbalist and potion stall, with a
# rune circle, glowing crystals, a spellbook lectern and violet arcane lamps round it.
WIZ = (-44.0, -60.5)                                             # the tower: door to the south, up the garden walk


def garden_common(sx, gx1, gx2, gz1, gz2, cx, cz):
    walk([[gx1 + 2, cz], [gx2 - 2, cz]], 1.4)
    walk([[sx * 17.0, -45.0], [sx * 21.0, -45.0], [gx1 + 2 if sx > 0 else gx2 - 2, cz]], 1.4)   # from the forecourt
    for k in range(-5, 6):                                        # path lanterns along the long walk
        if k == 0 or abs(k) == 1: continue
        place("path_lantern", cx + k * 4.0, cz - 2.4 if k % 2 else cz + 2.4, 0)
    # the garden's border: an L of hedge. Along the forecourt (x = +-20) with a gap for the forecourt walk, and along
    # the town side (z = -39) with a gap for the walk down to the market / yard; the two meet flush at the corner.
    hz = gz2 + 1.0                                                # -39
    xi = sx * 20.0                                                # the forecourt side
    hedge_run((xi, -51.0), (xi, -48.0))
    hedge_run((xi, hz - 3.0 + HEDGE_HALF), (xi, hz + HEDGE_HALF))
    x0 = xi + sx * HEDGE_HALF                                     # town side: from the corner, gap centred on the walk
    hedge_run((x0, hz), (x0 + sx * 21.0, hz))
    hedge_run((2 * cx - x0 - sx * 21.0, hz), (2 * cx - x0, hz))   # the first run mirrored about the walk (x = cx)
    for a_, b_ in (((x0, hz - 1.2), (x0 + sx * 21.0, hz - 1.2)),
                   ((2 * cx - x0 - sx * 21.0, hz - 1.2), (2 * cx - x0, hz - 1.2))):
        rose_row(a_, b_)                                          # roses along the hedge, on the garden side


for sx in (-1, 1):
    gx1, gx2 = (20.0, 68.0) if sx > 0 else (-68.0, -20.0)
    gz1, gz2 = -71.0, -40.0
    cx, cz = (gx1 + gx2) / 2, (gz1 + gz2) / 2
    landmarks[f"garden_{'east' if sx > 0 else 'west'}"] = [cx, cz]
    garden_common(sx, gx1, gx2, gz1, gz2, cx, cz)
    if sx > 0:                                                    # ---- the formal east garden
        walk([[cx, gz1 + 2], [cx, gz2 + 4]], 1.4)
        walk([[cx, gz2 + 4], [cx, -29.5]], 1.6)                   # into the market through its hedge gap
        place("blossom_tree_planter", cx, cz, 0, s=1.8)
        for ox in (-1, 1):
            for oz in (-1, 1):
                px, pz = cx + ox * 13.0, cz + oz * 8.0
                place("blossom_tree_planter" if (ox == oz) else "topiary_tiered_planter", px, pz, 0, s=1.3 if ox == oz else 1.2)
                place("planter_square_flowers", cx + ox * 4.5, cz + oz * 4.0, 0)
        for (bx, bz) in ((gx1 + 3, gz1 + 3), (gx2 - 3, gz1 + 3)):
            place("urn_planter", bx, bz, 0, s=1.2)
        continue
    # ---- the wizard's garden (west)
    wx, wz = WIZ
    landmarks["wizard_tower"] = [wx, wz]
    walk([[cx, cz], [cx, gz2 + 4]], 1.4)                          # the walk up to the tower door
    walk([[cx, gz2 + 4], [cx, -33.0], [-29.0, -33.0], [-29.0, -20.0]], 1.6)   # behind the workshops to Market Street
    place("wizard_tower", wx, wz, "S", max_h=8)
    npc("wizard", wx + 1.6, wz + 3.9, "S", "the wizard, at the tower door")
    place("spellbook_lectern", wx + 4.5, wz + 2.3, "S")
    for x, z in ((wx - 2.5, -53.2), (wx + 2.5, -53.2), (wx - 6.0, wz), (wx + 6.0, wz)):   # violet lamps: approach, flanks
        place("arcane_lamp", x, z, "S")
    for x in (wx - 5.0, wx + 5.0):                                # flowers either side of the approach
        place("planter_square_flowers", x, -51.5, 0)
    place("arcane_circle", -58.5, -64.0, 0)                       # the rune circle in the north-west corner
    for a, x, z, yaw in (("crystal_cluster", -62.0, -50.0, 30), ("crystal_cluster", -34.0, -67.0, -40), ("crystal_cluster_small", -35.5, -61.0, 75),
                         ("crystal_cluster_small", -52.5, -67.5, 10), ("crystal_cluster_small", -53.5, -61.5, -60), ("crystal_cluster_small", -64.0, -58.5, 130)):
        place(a, x, z, yaw)
    place("blossom_tree_planter", cx + 13.0, cz + 8.0, 0, s=1.3)  # the garden's blossom tree and topiary stay
    place("topiary_tiered_planter", cx - 13.0, cz + 8.0, 0, s=1.2)
    place("topiary_tiered_planter", cx + 13.0, cz - 8.0, 0, s=1.2)
    for (bx, bz) in ((gx2 - 3, gz1 + 3),):
        place("urn_planter", bx, bz, 0, s=1.2)


# ================================================================ 8. residential lanes (south)
L1 = (20.0, 26.0)     # Rose Lane
L2 = (42.0, 48.0)     # Orchard Lane
street(-66.0, L1[0], 66.0, L1[1])
street(-66.0, L2[0], 66.0, L2[1])
for sx in (-1, 1):                                        # connectors: market / yard down to the lanes
    street(sx * 44.0 - 3.0, -2.5, sx * 44.0 + 3.0, L1[0])
    street(sx * 62.0 - 3.0, L1[1], sx * 62.0 + 3.0, L2[0])
hi = 0


def house(x, z, yaw):
    global hi
    a = HOUSES[hi % len(HOUSES)]; hi += 1
    place(a, x, z, yaw, s=1.5, max_h=8)
    # a flower planter beside the door, on the side away from the neighbour
    fx1, fz1, fx2, fz2 = INFO[a]["footprint"]
    px, pz = local_to_world(x, z, yaw, fx2 * 1.5 + 0.8, fz1 * 1.5 - 0.2)
    place("planter_square_flowers", px, pz, yaw, s=0.8)


for sx in (-1, 1):
    # Rose Lane: houses both sides, gaps at the connectors
    for x in (10.0, 19.0, 28.0, 37.0, 53.0):
        house(sx * x, L1[0] - 4.6, 180)
    for x in (10.0, 19.0, 28.0, 37.0, 46.0):
        house(sx * x, L1[1] + 4.6, 0)
    # Orchard Lane: north side only (the orchard and its walks are south of it)
    for x in (22.0, 31.0, 40.0, 49.0):
        house(sx * x, L2[0] - 4.6, 180)
    # street lamps along both lanes, alternating sides
    for i, x in enumerate((14.5, 32.5, 50.5)):
        place("street_lamp", sx * x, L1[0] - 1.2 if i % 2 == 0 else L1[1] + 1.2, "S" if i % 2 == 0 else "N")
    for i, x in enumerate((26.5, 44.5, 60.0)):
        place("street_lamp", sx * x, L2[0] - 1.2 if i % 2 else L2[1] + 1.2, "S" if i % 2 else "N")
    # orchard: blossom trees in rows south of Orchard Lane, a walk through them
    walk([[sx * 20.0, 55.0], [sx * 66.0, 55.0]], 1.3)
    walk([[sx * 20.0, 66.0], [sx * 66.0, 66.0]], 1.3)
    for row, z in enumerate((51.5, 60.5, 70.5)):
        for k, x in enumerate((24.0, 33.0, 42.0, 51.0, 60.0, 69.0)):
            if row == 2 and k == 5: continue
            place("blossom_tree_planter", sx * (x + (4.5 if row == 1 else 0)), z, 0, s=1.1)
    for x in (28.5, 46.5, 64.5):
        place("path_lantern", sx * x, 55.0 + 2.2, 0)
        place("path_lantern", sx * x, 66.0 - 2.2, 0)
    # the lane ends at the wall: a little turning circle with an urn
    place("urn_planter", sx * 70.5, (L1[0] + L1[1]) / 2, 0, s=1.2)
    place("urn_planter", sx * 70.5, (L2[0] + L2[1]) / 2, 0, s=1.2)
    # houses facing Market Street from the south, between the square and the market / yard
    for x in (22.5,):
        house(sx * x, -12.0 + 4.6, 0)
        house(sx * x, -20.0 - 4.6, 180)

# avenue between the square and the lanes: lamps, hedged flower beds
for z in (4.0, 14.0, 32.0):
    for sx in (-1, 1):
        place("street_lamp", sx * 6.0, z, "W" if sx > 0 else "E")
for sx in (-1, 1):
    hedge_run((sx * 7.6, 5.5), (sx * 7.6, 17.5))
    rose_row((sx * 6.5, 5.5), (sx * 6.5, 17.5), skip=[(sx * 6.0, 14.0)])
    for z in (29.5, 35.5):
        place("planter_square_flowers", sx * 7.0, z, 0)

# ================================================================ 9. portal plaza (south gate)
PP = (-17.0, 52.0, 17.0, 73.0)
street(*PP)
landmarks["portal"] = [0.0, 68.5]
landmarks["spawn_point"] = [0.0, 58.0]
for sx in (-1, 1):
    place("plaza_lamp", sx * 13.5, 55.0, "N")
    place("topiary_tiered_planter", sx * 5.5, 70.0, "N", s=1.4)
    place("street_lamp_double", sx * 9.5, 70.5, "N")
    place("stall_bakery" if sx < 0 else "stall_fruit", sx * 13.0, 63.5, 90 if sx > 0 else -90)
    a = "stall_bakery" if sx < 0 else "stall_fruit"
    fx1, fz1, fx2, fz2 = INFO[a]["extent"]
    yaw = 90 if sx > 0 else -90
    vx, vz = local_to_world(sx * 13.0, 63.5, yaw, fx2 + 0.55, fz1 + 0.55)
    npc(f"vendor_traveller_{'east' if sx > 0 else 'west'}", vx, vz, yaw, "provisions for travellers at the portal")
    hedge_run((sx * 18.0, 53.5), (sx * 18.0, 71.5))
    rose_row((sx * 16.9, 53.5), (sx * 16.9, 71.5))

# ================================================================ output
for k, v in list(landmarks.items()):
    landmarks[k] = [float(v[0]), float(v[1])]
plan = {
    "_doc": "Built by build scripts/build_hub_town.py. placements: [alias, x, y, z, yaw_deg, scale]. colliders: [x, y, z, sx, sy, sz, yaw_deg]. "
            "lights: [x, y, z, lanterns, alias]. ground.cobble: rects [x1, z1, x2, z2]; ground.dirt: walks {points, radius}. "
            "npc_spots: where vendor / crafter NPCs can stand (yaw: which way they face). no_scatter: rects with no grass or flowers.",
    "walls": W, "ground_height": 2.0,
    "models": {a: {k: INFO[a][k] for k in ("path", "glow", "height", "animated")} for a in INFO},
    "placements": placements, "colliders": colliders, "lights": lights, "npc_spots": npc_spots,
    "landmarks": landmarks, "spawn_point": landmarks["spawn_point"],
    "ground": {"cobble": cobble, "dirt": dirt, "dirt_rects": dirt_rects}, "no_scatter": no_scatter,
    "yard_rows": yard_rows, "yard_plots": yard_plots,
}
out = os.path.join(GAME, "data", "hub_town.json")
with open(out, "w") as f:
    json.dump(plan, f, indent=1)
from collections import Counter
print("placements", len(placements), dict(Counter(p[0] for p in placements)))
print("colliders", len(colliders), "lights", len(lights), "npc spots", len(npc_spots))

if "--preview" in sys.argv:
    from PIL import Image, ImageDraw
    S = 6; N = 200 * S
    img = Image.new("RGB", (N, N), (106, 138, 74)); d = ImageDraw.Draw(img)
    P = lambda x, z: ((x + 100) * S, (z + 100) * S)
    for w in dirt:
        pts = w["points"]
        for a, b in zip(pts[:-1], pts[1:]):
            d.line([P(*a), P(*b)], fill=(170, 135, 90), width=int(w["radius"] * 2 * S))
    for r in cobble: d.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=(150, 146, 136))
    col = {"house": (180, 90, 70), "stall": (220, 180, 60), "wall": (210, 200, 170), "pillar": (230, 220, 190), "castle": (200, 190, 160),
           "lamp": (255, 230, 120), "hedge": (40, 100, 40), "blossom": (230, 140, 180), "topiary": (30, 120, 50), "planter": (120, 170, 80),
           "urn": (200, 200, 190), "station": (120, 90, 200), "lantern": (255, 220, 100)}
    st = {"furnace", "anvil", "workbench", "sawbench", "drying_rack", "tanning_rack", "cauldron"}
    for a, x, y, z, yaw, s in placements:
        k = "house" if a in HOUSES else "station" if a in st else next((c for c in col if c in a), "planter")
        r = world_rect(a, x, z, yaw, s, "extent")
        d.rectangle([P(r[0], r[1]), P(r[2], r[3])], fill=col[k], outline=(30, 30, 30))
        fx, fz = rot(0, -1.2 * max(1, s), yaw)                 # front direction tick
        if k in ("house", "stall", "station", "castle"):
            d.line([P(x, z), P(x + fx, z + fz)], fill=(0, 0, 0), width=3)
    for c in colliders:
        pass
    for n in npc_spots:
        x, _, z = n["pos"]; d.ellipse([P(x - 0.6, z - 0.6), P(x + 0.6, z + 0.6)], fill=(255, 0, 255))
    for l in lights:
        d.ellipse([P(l[0] - 0.4, l[2] - 0.4), P(l[0] + 0.4, l[2] + 0.4)], fill=(255, 255, 255))
    sp = landmarks["spawn_point"]; d.ellipse([P(sp[0] - 1, sp[1] - 1), P(sp[0] + 1, sp[1] + 1)], fill=(0, 200, 255))
    img.save(sys.argv[sys.argv.index("--preview") + 1])
