extends Node3D
## Resource world landmarks (game_worlds.md section 4.8 Landmarks rows), ore node placeholders (section 4.4,
## placed where section 4.8 says) and the portal back to the hub. Everything is placed from the baked layout and a
## fixed seed, so it is the same every load.

const ORES := {  # biome -> ores (game_worlds.md section 4.4)
	"forest": ["coal", "tin", "copper"],
	"mountain": ["coal", "tin", "copper", "iron"],
	"frost": ["coal", "iron", "gold"],
	"plains": ["coal", "titanite"],
	"swamp": ["coal", "iron", "gold"],
}
const PER_ORE := 4

var world: GameWorld
var data: WorldData


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
			while count < PER_ORE and tries < 6000:
				tries += 1
				var x := rng.randf_range(bi * 256.0 + 12.0, bi * 256.0 + 244.0)
				var z := rng.randf_range(-200.0, 200.0)
				if _ore_spot_ok(biome, x, z, tries > 4000, placed):
					_ore(root, ore, x, z, rng)
					placed.append(Vector2(x, z))
					count += 1
	# special nodes: obsidian round the volcanic cave, dreadstone in the most toxic swamp
	var lm: Dictionary = data.layout["landmarks"]
	for spec in [["obsidian", lm["obsidian_cave"], 14.0, 5], ["dreadstone", lm["dreadstone_pit"], 9.0, 5]]:
		var n: int = spec[3]
		var r: float = spec[2]
		var c: Array = spec[1]
		for i in n:
			var a := i * TAU / n + 0.4
			_ore(root, spec[0], c[0] + cos(a) * r, c[1] + sin(a) * r, rng)


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
	var n := (load("res://scenes/resource/ores/%s_vein_placeholder.tscn" % ore) as PackedScene).instantiate() as Node3D
	n.name = "%s_vein_%d" % [ore, root.get_child_count() + 1]
	root.add_child(n)
	n.global_position = Vector3(x, data.height(x, z) - 0.15, z)
	n.rotation.y = rng.randf() * TAU
	n.scale = Vector3.ONE * rng.randf_range(1.0, 1.35)
