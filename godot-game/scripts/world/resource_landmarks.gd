extends Node3D
## Resource world landmarks (game_worlds.md section 4.8 Landmarks rows), ore veins (section 4.4: the Blockbench
## models in assets/models/ores via scripts/world/ore_vein.gd, placed where section 4.8 says) and the portal back
## to the hub. Everything is placed from the baked layout and a fixed seed, so it is the same every load.

const ORES := {  # biome -> ores (game_worlds.md section 4.4)
	"forest": ["coal", "tin", "copper"],
	"mountain": ["coal", "tin", "copper", "iron"],
	"frost": ["coal", "iron", "gold"],
	"plains": ["coal", "titanite"],
	"swamp": ["coal", "iron", "gold"],
}
## Veins of each ore in each of its biomes. Ores are kept far rarer than trees (a handful per biome, not
## thousands); coal, the fuel, is a little more common. Obsidian and dreadstone sit round
## their landmarks (RING). Voidstone and stellarite only appear as world events (EVENT_SPOTS).
const PER_ORE := 3
const PER_ORE_OF := {"coal": 4}
const RING := 3                  # obsidian round the volcanic cave, dreadstone round the toxic pit

const ORE_VEIN := preload("res://scripts/world/ore_vein.gd")
const MOB := preload("res://scripts/world/mob.gd")
## Mobs (game_worlds.md section 4.8 mob ideas): [kind, biome, groups, per group]. Herds of cows and pigs in the
## forest and plains, wolf packs at the forest edges, in the mountains and in the snow, ogres in the mountains and
## the swamp. The big ones live by a landmark of their own (MOB_LAIRS). No combat or hunting yet.
const MOBS := [
	["cow", "forest", 4, 3], ["pig", "forest", 3, 3], ["wolf", "forest", 2, 2],
	["highland_cow", "mountain", 3, 3], ["wolf", "mountain", 2, 3], ["ogre", "mountain", 3, 1],
	["wolf", "frost", 3, 2],
	["cow", "plains", 4, 4], ["highland_cow", "plains", 2, 3],
	["ogre", "swamp", 4, 1],
]
## Herds grazing beside the path just ahead of the arrival point (you arrive facing along it), so there are
## animals in sight as soon as you arrive: [kind, count, metres along the path, metres to the side].
const MOBS_AT_ARRIVAL := [["cow", 3, 26.0, 9.0], ["pig", 2, 40.0, -10.0]]
## [kind, landmark, metres away]: the ember dragon by the volcanic obsidian cave, the stone golem under the
## highest peak, the pale dragon by the ice spire.
const MOB_LAIRS := [["ember_dragon", "obsidian_cave", 34.0], ["stone_golem", "highest_peak", 24.0],
	["pale_dragon", "ice_spire", 30.0]]
## [kind, biome, metres into the biome, metres to the side of the path]: the dark dragon waits where the path
## enters the swamp (J00BA, 2026-11-08).
const MOBS_AT_BIOME_START := [["dragon", "swamp", 30.0, 22.0]]
const MOB_SIZE := {"pale_dragon": 0.5}   # J00BA: the pale dragon at half size
const BIRD := preload("res://scripts/world/bird.gd")
## Birds (scripts/world/bird.gd): [kind, biome, groups, per group, where] where = land / shore / water.
const BIRDS := [
	["pigeon", "forest", 3, 3, "land"], ["crow", "forest", 2, 2, "land"], ["robin", "forest", 4, 1, "land"],
	["owl", "forest", 2, 1, "land"],
	["eagle", "mountain", 3, 1, "land"], ["crow", "mountain", 1, 3, "land"],
	["snowy_owl", "frost", 3, 1, "land"], ["eagle", "frost", 1, 1, "land"],
	["crow", "plains", 2, 3, "land"], ["pigeon", "plains", 2, 3, "land"], ["eagle", "plains", 1, 1, "land"],
	["heron", "swamp", 3, 1, "shore"], ["duck", "swamp", 3, 3, "water"], ["seagull", "swamp", 2, 1, "water"],
]
## Birds on the named water bodies (layout "water"): [water name, kind, how many, where].
const WATER_BIRDS := [
	["forest_river", "swan", 2, "water"], ["forest_river", "duck", 3, "water"], ["forest_river", "heron", 1, "shore"],
	["forest_river", "seagull", 3, "water"], ["forest_upper_pool", "swan", 2, "water"],
	["plains_watering_hole", "duck", 2, "water"],
]
## Voidstone and stellarite veins are world events (autoload/ore_events.gd): they appear on one of these
## spots, the same list on every client (fixed seed, any biome), which the server picks by index.
const EVENT_SPOTS := 48

var world: GameWorld
var data: WorldData
var event_spots: Array[Vector2] = []
var _event_root: Node3D
var _event_veins := {}           # event id -> vein node


func populate(w: GameWorld) -> void:
	world = w
	data = w.data()
	var lm: Dictionary = data.layout["landmarks"]
	# portal back to the hub, just behind the arrival point in the portal clearing
	var pc: Array = lm["portal_clearing"]
	var portal := _place("res://scenes/shared/portal.tscn", pc[0] - 10.0, pc[1], PI / 2.0)
	portal.name = "portal_to_hub"
	portal.set("target_world", "hub")
	portal.set("target_spawn", "spawn_point")
	# landmarks (placeholders; each one is a scene so a real model can replace it)
	_landmark("stone_ruin", lm, 0.4)
	_landmark("standing_stones", lm, 0.0)
	_landmark("frozen_waterfall", lm, 0.0, -2.0)
	_landmark("ice_spire", lm, 0.3)
	_landmark("stone_arch", lm, 0.2)
	_landmark("pillar_ring", lm, 0.0)
	_landmark("hollow_tree", lm, 0.6)
	_landmark("dreadstone_pit", lm, 0.0)
	_landmark("sunken_ruins", lm, 0.3, -0.6)
	var ob: Array = lm["obsidian_cave"]
	_place("res://scenes/resource/obsidian_vent_placeholder.tscn", ob[0], ob[1], 0.5).name = "obsidian_cave"
	var pk: Array = lm["highest_peak"]
	_place("res://scenes/resource/giant_stone_peak_cairn_placeholder.tscn", pk[0], pk[1], 0.0).name = "highest_peak_cairn"
	_log_bridge()
	_giant_titanwood(lm["giant_titanwood"])
	_place_ores()
	_place_mobs()
	_place_birds()


func _landmark(key: String, lm: Dictionary, yaw: float, sink := 0.0) -> void:
	var p: Array = lm[key]
	var n := _place("res://scenes/resource/%s_placeholder.tscn" % key, p[0], p[1], yaw, sink)
	n.name = key


func _place(path: String, x: float, z: float, yaw: float, sink := 0.0) -> Node3D:
	var n := (load(path) as PackedScene).instantiate() as Node3D
	add_child(n)
	n.global_position = Vector3(x, data.height(x, z) + sink - 0.15, z)
	n.rotation.y = yaw
	return n


func _log_bridge() -> void:
	## Fallen log bridge where the path to the worldbark grove crosses the river (forest reference image).
	for b in data.layout["branches"]:
		if b["to"] != "worldbark_grove":
			continue
		var pts: Array = b["points"]
		for i in pts.size() - 1:
			var a := Vector2(pts[i][0], pts[i][1])
			if data.mask_at(a.x, a.y).g > 0.8:
				var nxt := Vector2(pts[i + 1][0], pts[i + 1][1])
				var bridge := _place("res://scenes/resource/log_bridge_placeholder.tscn", a.x, a.y, 0.0)
				bridge.global_position.y = 3.6
				bridge.look_at(Vector3(nxt.x, 3.6, nxt.y), Vector3.UP)
				bridge.name = "log_bridge"
				return


func _giant_titanwood(p: Array) -> void:
	## The biggest titanwood tree (plains landmark): a large pine placeholder with the titanwood recolour.
	var rule := {"id": "giant_titanwood_placeholder", "biomes": ["plains"], "kind": "tree", "trunk_tint": "#8a929c",
		"recolor": ["#0e2e2e", "#3a8a80"], "view": 900}
	var mi := MeshInstance3D.new()
	mi.name = "giant_titanwood"
	mi.mesh = world.scatter._prepared_mesh(rule, "pine")
	add_child(mi)
	var x: float = p[0]
	var z: float = p[1]
	mi.global_position = Vector3(x, data.height(x, z) - 0.3, z)
	mi.scale = Vector3.ONE * 5.0


func _place_ores() -> void:
	var root := Node3D.new()
	root.name = "ore_nodes"
	add_child(root)
	var rng := RandomNumberGenerator.new()
	rng.seed = 777
	var placed: Array[Vector2] = []
	var names := ["forest", "mountain", "frost", "plains", "swamp"]
	for bi in names.size():
		var biome: String = names[bi]
		for ore in ORES[biome]:
			var count := 0
			var tries := 0
			while count < int(PER_ORE_OF.get(ore, PER_ORE)) and tries < 6000:
				tries += 1
				var x := rng.randf_range(bi * 256.0 + 12.0, bi * 256.0 + 244.0)
				var z := rng.randf_range(-200.0, 200.0)
				if _ore_spot_ok(biome, x, z, tries > 4000, placed):
					_ore(root, ore, x, z, rng)
					placed.append(Vector2(x, z))
					count += 1
	# special nodes: obsidian round the volcanic cave, dreadstone in the most toxic swamp
	var lm: Dictionary = data.layout["landmarks"]
	for spec in [["obsidian", lm["obsidian_cave"], 14.0, RING], ["dreadstone", lm["dreadstone_pit"], 9.0, RING]]:
		var n: int = spec[3]
		var r: float = spec[2]
		var c: Array = spec[1]
		for i in n:
			var a := i * TAU / n + 0.4
			_ore(root, spec[0], c[0] + cos(a) * r, c[1] + sin(a) * r, rng)
	_event_spots(placed)
	_event_root = Node3D.new()
	_event_root.name = "ore_events"
	add_child(_event_root)
	OreEvents.started.connect(_on_event)
	OreEvents.ended.connect(_on_event_end)
	for ev in OreEvents.events.values():               # events already running when this world loaded
		_on_event(ev)


func _event_spots(placed: Array[Vector2]) -> void:
	## Open walkable ground anywhere in the world, away from the paths and the other veins.
	var rng := RandomNumberGenerator.new()
	rng.seed = 4242
	var names := ["forest", "mountain", "frost", "plains", "swamp"]
	var taken := placed.duplicate()
	var tries := 0
	while event_spots.size() < EVENT_SPOTS and tries < 20000:
		tries += 1
		var bi := event_spots.size() % names.size()     # spread evenly over the biomes
		var x := rng.randf_range(bi * 256.0 + 12.0, bi * 256.0 + 244.0)
		var z := rng.randf_range(-200.0, 200.0)
		if _ore_spot_ok(names[bi], x, z, true, taken):
			event_spots.append(Vector2(x, z))
			taken.append(Vector2(x, z))


func _on_event(ev: Dictionary) -> void:
	if _event_veins.has(ev.id) or event_spots.is_empty():
		return
	var p: Vector2 = event_spots[int(ev.spot) % event_spots.size()]
	var n: Node3D = ORE_VEIN.new()
	n.set("ore", ev.ore)
	n.name = "%s_vein_event_%d" % [ev.ore, absi(int(ev.id))]
	n.add_to_group("event_vein")
	n.set_meta("event_id", ev.id)
	_event_root.add_child(n)
	n.global_position = Vector3(p.x, data.height(p.x, p.y) - 0.15, p.y)
	n.rotation.y = float(absi(int(ev.spot)) * 37 % 360) * PI / 180.0
	_event_veins[ev.id] = n
	# it rises out of the ground
	var target := n.scale
	n.scale = target * 0.05
	n.create_tween().tween_property(n, "scale", target, 1.2).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)


func _on_event_end(id: int) -> void:
	var n: Node3D = _event_veins.get(id)
	_event_veins.erase(id)
	if not is_instance_valid(n):
		return
	n.remove_from_group("event_vein")
	var tw := n.create_tween()
	tw.tween_property(n, "scale", n.scale * 0.05, 0.8).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_IN)
	tw.tween_callback(n.queue_free)


func _ore_spot_ok(biome: String, x: float, z: float, relaxed: bool, placed: Array[Vector2]) -> bool:
	if data.biome_name(x, z) != biome or not data.in_bounds(x, z, 50.0):
		return false
	var m := data.mask_at(x, z)
	if m.r > 0.1:
		return false
	for p in placed:
		if p.distance_to(Vector2(x, z)) < 10.0:
			return false
	var h := data.height(x, z)
	if h < data.water_level(x, z) + 0.2:
		return false
	var slope := 1.0 - data.normal(x, z).y
	if slope > 0.3:  # walkable ground only
		return false
	for d in [Vector2(3, 0), Vector2(-3, 0), Vector2(0, 3), Vector2(0, -3)]:
		if 1.0 - data.normal(x + d.x, z + d.y).y > 0.45:  # not at the foot of a cliff
			return false
	if relaxed:
		return true
	match biome:
		"forest": return slope > 0.06 or m.g > 0.3          # rocky bumps and riverbanks
		"mountain": return h > 26.0                           # high ground
		"frost": return z < -120.0                            # near the ice cliffs
		"plains": return h > 14.0 or slope > 0.12             # mesa tops and edges
		"swamp": return h > data.water_level(x, z) + 0.1 and h < data.water_level(x, z) + 0.9  # muddy banks
	return true


func _ore(root: Node3D, ore: String, x: float, z: float, rng: RandomNumberGenerator) -> void:
	var n: Node3D = ORE_VEIN.new()
	n.set("ore", ore)
	n.name = "%s_vein_%d" % [ore, root.get_child_count() + 1]
	root.add_child(n)
	n.global_position = Vector3(x, data.height(x, z) - 0.15, z)
	n.rotation.y = rng.randf() * TAU
	n.scale = Vector3.ONE * rng.randf_range(0.9, 1.15)   # the models are already to scale (16 units = 1 m)



func _place_mobs() -> void:
	var root := Node3D.new()
	root.name = "mobs"
	add_child(root)
	var rng := RandomNumberGenerator.new()
	rng.seed = 9090
	var names := ["forest", "mountain", "frost", "plains", "swamp"]
	var homes: Array[Vector2] = []
	var n := 0
	for spec in MOBS:
		var bi := names.find(spec[1])
		for g in int(spec[2]):
			var home := Vector2.ZERO
			for tries in 3000:
				var x := rng.randf_range(bi * 256.0 + 20.0, bi * 256.0 + 236.0)
				var z := rng.randf_range(-180.0, 180.0)
				if tries < 2000:                       # most herds live 20 to 60 m off the main path, in view of it
					var pz := _path_z(x)
					z = pz + rng.randf_range(20.0, 60.0) * (1.0 if rng.randf() < 0.5 else -1.0)
				if _ore_spot_ok(spec[1], x, z, true, homes) and _clear_of_landmarks(x, z):
					home = Vector2(x, z)
					break
			if home == Vector2.ZERO:
				continue
			homes.append(home)
			for i in int(spec[3]):                    # a herd shares a home area, each with its own wander
				n += 1
				var off := Vector2(rng.randf_range(-3.0, 3.0), rng.randf_range(-3.0, 3.0))
				_mob(root, spec[0], home + off, 1000 + n)
	var sp: Array = data.layout.get("spawn_point", [0, 0])
	for spec in MOBS_AT_ARRIVAL:                      # herds in sight of the arrival point, beside the path ahead
		for tries in 24:
			var x: float = sp[0] + float(spec[2]) + tries * 2.0
			var side: float = float(spec[3]) * (1.0 + 0.1 * tries) * (1.0 if tries % 2 == 0 else -1.0)
			var c := Vector2(x, _path_z(x) + side)
			if _ore_spot_ok("forest", c.x, c.y, true, homes):
				homes.append(c)
				for i in int(spec[1]):
					n += 1
					_mob(root, spec[0], c + Vector2(rng.randf_range(-3.0, 3.0), rng.randf_range(-3.0, 3.0)), 1000 + n)
				break
	var biomes := ["forest", "mountain", "frost", "plains", "swamp"]
	for spec in MOBS_AT_BIOME_START:                  # by the path where it enters the biome
		var x0: float = biomes.find(spec[1]) * 256.0 + float(spec[2])
		for tries in 30:
			var x := x0 + tries * 3.0
			var side: float = float(spec[3]) * (1.0 if tries % 2 == 0 else -1.0)
			var c := Vector2(x, _path_z(x) + side)
			if data.biome_name(c.x, c.y) == spec[1] and _ore_spot_ok(spec[1], c.x, c.y, true, homes):
				homes.append(c)
				n += 1
				_mob(root, spec[0], c, 1000 + n)
				break
	var lm: Dictionary = data.layout["landmarks"]
	for lair in MOB_LAIRS:
		if not lm.has(lair[1]):
			continue
		var c := Vector2(lm[lair[1]][0], lm[lair[1]][1])
		for i in 24:                                  # walk round the landmark until the ground is good
			var a := i * TAU / 24.0 + 0.3
			var p := c + Vector2(cos(a), sin(a)) * float(lair[2])
			if data.in_bounds(p.x, p.y, 20.0) and data.height(p.x, p.y) > data.water_level(p.x, p.y) + 0.3 \
					and data.normal(p.x, p.y).y > 0.8:
				n += 1
				_mob(root, lair[0], p, 1000 + n)
				break


## z of the main path where it crosses x (the nearest point of the baked path).
func _path_z(x: float) -> float:
	var best := 0.0
	var bd := 1e9
	for pt in data.layout.get("main_path", []):
		if absf(pt[0] - x) < bd:
			bd = absf(pt[0] - x)
			best = pt[1]
	return best


func _clear_of_landmarks(x: float, z: float) -> bool:
	for key in data.layout["landmarks"]:
		var p: Array = data.layout["landmarks"][key]
		if Vector2(x, z).distance_to(Vector2(p[0], p[1])) < 24.0:
			return false
	return true


func _mob(root: Node3D, kind: String, p: Vector2, mob_seed: int) -> void:
	var m: Node3D = MOB.new()
	m.set("kind", kind)
	m.set("home", Vector3(p.x, data.height(p.x, p.y), p.y))
	m.set("mob_seed", mob_seed)
	m.set("data", data)
	m.set("view", world.player)
	m.set("size", float(MOB_SIZE.get(kind, 1.0)))
	m.name = "%s_%d" % [kind, mob_seed - 1000]
	root.add_child(m)



## GameWorld.set_player: the mobs measure "far away" from the player.
func set_player(p: Node3D) -> void:
	for rname in ["mobs", "birds"]:
		var root := get_node_or_null(rname)
		if root:
			for m in root.get_children():
				m.set("view", p)



func _place_birds() -> void:
	var root := Node3D.new()
	root.name = "birds"
	add_child(root)
	var rng := RandomNumberGenerator.new()
	rng.seed = 7171
	var names := ["forest", "mountain", "frost", "plains", "swamp"]
	var n := 0
	var waters: Array = data.layout.get("water", [])
	for spec in BIRDS:
		var bi := names.find(spec[1])
		for g in int(spec[2]):
			for tries in 4000:
				var x := rng.randf_range(bi * 256.0 + 16.0, bi * 256.0 + 240.0)
				var z := rng.randf_range(-190.0, 190.0)
				if data.biome_name(x, z) != spec[1] or not _bird_spot_ok(x, z, spec[4]):
					continue
				for i in int(spec[3]):
					n += 1
					_bird(root, spec[0], Vector2(x, z) + Vector2(rng.randf_range(-2, 2), rng.randf_range(-2, 2)), 3000 + n,
						_water_at(waters, x, z))
				break
	for spec in WATER_BIRDS:
		var w := {}
		for ww in waters:
			if ww["name"] == spec[0]:
				w = ww
		if w.is_empty():
			continue
		var r: Array = w["rect"]
		for i in int(spec[2]):
			for tries in 400:
				var x := rng.randf_range(r[0], r[2])
				var z := rng.randf_range(r[1], r[3])
				if _bird_spot_ok(x, z, spec[3]):
					n += 1
					_bird(root, spec[1], Vector2(x, z), 3000 + n, w)
					break


func _bird_spot_ok(x: float, z: float, where: String) -> bool:
	if not data.in_bounds(x, z, 10.0):
		return false
	var h := data.height(x, z)
	var wl := data.water_level(x, z)
	match where:
		"water": return h < wl - 0.4
		"shore": return h > wl - 0.2 and h < wl + 0.8 and data.normal(x, z).y > 0.8
	return h > wl + 0.3 and data.normal(x, z).y > 0.8


func _water_at(waters: Array, x: float, z: float) -> Dictionary:
	for w in waters:
		var r: Array = w["rect"]
		if x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]:
			return w
	return {}


func _bird(root: Node3D, kind: String, p: Vector2, bird_seed: int, water: Dictionary) -> void:
	var b: Node3D = BIRD.new()
	b.set("kind", kind)
	b.set("home", Vector3(p.x, data.height(p.x, p.y), p.y))
	b.set("bird_seed", bird_seed)
	b.set("data", data)
	b.set("view", world.player)
	b.set("water", water)
	b.name = "%s_%d" % [kind, bird_seed - 3000]
	root.add_child(b)

