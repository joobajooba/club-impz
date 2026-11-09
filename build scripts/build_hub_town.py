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

HOUSES = ["brick_rose_cottage", "wood_timber_house", "brick_bluebell_house", "wood_oak_lodge", "brick_honey_townhouse", "wood_cherry_manor"]
FACE = {"N": 0.0, "W": 90.0, "S": 180.0, "E": -90.0}


# ---------------------------------------------------------------- model metrics from the .bbmodel files
def metrics(bb_rel):
    d = json.load(open(os.path.join(GAME, bb_rel), encoding="utf8"))
    E = [e for e in d["elements"] if e.get("export", True)]
    solid = [e for e in E if all(e["to"][i] - e["from"][i] > 0.01 for i in range(3)) and not e.get("rotation")]
    ground = [e for e in solid if e["from"][1] <= 1.01] or solid
    fp = [min(e["from"][0] for e in ground) * U, min(e["from"][2] for e in ground) * U,
          max(e["to"][0] for e in ground) * U, max(e["to"][2] for e in ground) * U]
    full = [min(e["from"][0] for e in E) * U, min(e["from"][2] for e in E) * U, max(e["to"][0] for e in E) * U, max(e["to"][2] for e in E) * U]
    h = max(e["to"][1] for e in E) * U
    lights = [[round(g["origin"][0] * U, 3), round(g["origin"][1] * U, 3), round(g["origin"][2] * U, 3)]
              for g in d["groups"] if g["name"].startswith("light_")]
    glow = any(e["name"].endswith("_glow") for e in E)
    return {"footprint": [round(v, 3) for v in fp], "extent": [round(v, 3) for v in full], "height": round(h, 3), "lights": lights, "glow": glow}


INFO = {}
for a, (res, bb, s) in MODELS.items():
    INFO[a] = {"path": res, "scale": s, **metrics(bb)}


# ---------------------------------------------------------------- plan state
placements, colliders, no_scatter, npc_spots, lights = [], [], [], [], []
cobble, dirt, landmarks = [], [], {}


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
    if collide:
        x1, z1, x2, z2 = INFO[alias]["footprint"]
        cx, cz = rot((x1 + x2) / 2 * s, (z1 + z2) / 2 * s, yaw)
        h = min(INFO[alias]["height"] * s, max_h)
        colliders.append([round(x + cx, 3), round(y + h / 2, 3), round(z + cz, 3), round((x2 - x1) * s, 3), round(h, 3), round((z2 - z1) * s, 3), round(yaw, 2)])
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
    for k in range(4):                                  # low hedges framing the forecourt (gap for the garden walk)
        if k == 1: continue
        place("hedge_segment", sx * 18.2, -48.0 + k * 3.0, 90 if sx < 0 else -90, s=1.5)
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
    for k in range(9):                                        # back hedges
        hx = sx * (35.5 + k * 3.0)
        if abs(abs(hx) - 44.0) > 3.6:                         # gaps for the garden walk and the lane connector
            place("hedge_segment", hx, -30.6, 0, s=1.5)
            place("hedge_segment", hx, -1.4, 0, s=1.5)
    for x in (34.0, 61.5):
        place("topiary_ball_planter", sx * x, -31.6 + 0.0, "S")
    place("blossom_tree_planter", sx * 69.5, -16.0, 0, s=1.6)   # Market Street ends at a blossom tree by the wall
    for z in (-22.0, -10.0):
        place("urn_planter", sx * 66.5, z, "W" if sx > 0 else "E", s=1.2)
    for x in (31.0, 52.0, 62.0):                              # blossom trees on the lawn towards Rose Lane
        place("blossom_tree_planter", sx * x, 7.0, 0, s=1.2)


landmarks["market"] = [47.5, -16]
landmarks["crafting_area"] = [-47.5, -16]
square(1, [("stall_fruit", "fruit"), ("stall_bakery", "baker"), ("stall_cloth", "tailor"), ("stall_potion", "apothecary")],
       [("stall_cloth", "weaver"), ("stall_potion", "alchemist"), ("stall_fruit", "greengrocer"), ("stall_bakery", "pie seller")], "market")
square(-1, [("sawbench", "sawyer"), ("workbench", "carpenter"), ("anvil", "blacksmith"), ("furnace", "smelter")],
       [("stall_potion", "potion_brewer"), ("cauldron", "brewer"), ("drying_rack", "herbalist"), ("tanning_rack", "tanner")], "yard")

# ================================================================ 7. castle gardens (north-west and north-east)
for sx in (-1, 1):
    gx1, gx2 = (20.0, 68.0) if sx > 0 else (-68.0, -20.0)
    gz1, gz2 = -71.0, -40.0
    cx, cz = (gx1 + gx2) / 2, (gz1 + gz2) / 2
    landmarks[f"garden_{'east' if sx > 0 else 'west'}"] = [cx, cz]
    # walks: a cross through the middle, a ring round the lawn, and a link down to the market / yard
    walk([[gx1 + 2, cz], [gx2 - 2, cz]], 1.4)
    walk([[cx, gz1 + 2], [cx, gz2 + 4]], 1.4)
    walk([[cx, gz2 + 4], [cx, -29.5]], 1.6)
    walk([[sx * 17.0, -45.0], [sx * 21.0, -45.0], [gx1 + 2 if sx > 0 else gx2 - 2, cz]], 1.4)   # from the forecourt
    place("blossom_tree_planter", cx, cz, 0, s=1.8)
    for ox in (-1, 1):
        for oz in (-1, 1):
            px, pz = cx + ox * 13.0, cz + oz * 8.0
            place("blossom_tree_planter" if (ox == oz) else "topiary_tiered_planter", px, pz, 0, s=1.3 if ox == oz else 1.2)
            place("planter_square_flowers", cx + ox * 4.5, cz + oz * 4.0, 0)
    for k in range(-5, 6):                                # path lanterns along the long walk
        if k == 0 or abs(k) == 1: continue
        place("path_lantern", cx + k * 4.0, cz - 2.4 if k % 2 else cz + 2.4, 0)
    # hedge border along the garden's town side, gaps where the walks come through
    for k in range(16):
        hx = gx1 + 1.5 + k * 3.0
        if abs(hx - cx) < 3.5: continue
        place("hedge_segment", hx, gz2 + 1.0, 0, s=1.5)
    for k in range(9):
        hz = gz1 + 2.0 + k * 3.0
        if abs(hz - cz) < 3.0 or abs(hz + 45.0) < 2.6: continue     # gaps: the cross walk and the forecourt walk
        place("hedge_segment", gx1 if sx > 0 else gx2, hz, 90, s=1.5)
    for (bx, bz) in ((gx1 + 3, gz1 + 3), (gx2 - 3, gz1 + 3)):
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
    for z in (7.0, 10.0, 13.0, 16.0):
        place("hedge_segment", sx * 7.6, z, 90, s=1.5)
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
    for k in range(5):
        place("hedge_segment", sx * 18.0, 54.0 + k * 3.6, 90, s=1.5)

# ================================================================ output
for k, v in list(landmarks.items()):
    landmarks[k] = [float(v[0]), float(v[1])]
plan = {
    "_doc": "Built by build scripts/build_hub_town.py. placements: [alias, x, y, z, yaw_deg, scale]. colliders: [x, y, z, sx, sy, sz, yaw_deg]. "
            "lights: [x, y, z, lanterns, alias]. ground.cobble: rects [x1, z1, x2, z2]; ground.dirt: walks {points, radius}. "
            "npc_spots: where vendor / crafter NPCs can stand (yaw: which way they face). no_scatter: rects with no grass or flowers.",
    "walls": W, "ground_height": 2.0,
    "models": {a: {k: INFO[a][k] for k in ("path", "glow", "height")} for a in INFO},
    "placements": placements, "colliders": colliders, "lights": lights, "npc_spots": npc_spots,
    "landmarks": landmarks, "spawn_point": landmarks["spawn_point"],
    "ground": {"cobble": cobble, "dirt": dirt}, "no_scatter": no_scatter,
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
