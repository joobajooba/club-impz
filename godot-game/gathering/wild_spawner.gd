class_name WildSpawner
extends Node3D
## Spreads ore veins and plants across the open world, outside the gathering sites. A TEST layout:
## the user asked for it on 2026-10-30, and where wild nodes grow is not decided yet.
## - Same world on every load: everything is rolled from the World's seed plus `seed_offset`, so
##   every player will see the same veins in the same places (ACCOUNTS-AND-DATA, shared server).
## - Ore veins come in outcrops of 2 to 4 of one ore, on hills and never in the flat plains.
## - Plants come in patches of 3 to 6 of one plant. Flowers and clover grow in the plains and the
##   woods; ferns, leafy plants and mushrooms only in the woods.
## - Tiers rise with distance from the middle: only the two lowest near the start, every tier by
##   the edge of the map, and each tier up is rarer than the one below (RARITY) everywhere.
## - Variation: each vein uses one of VEIN_VARIANTS shapes of its ore (VeinArt), and every node
##   gets its own size, stretch, turn and lean. Plants swap between the kit's single and group models.
## Gathering, energy and respawn work exactly as at the sites (GatherNode).

@export var world_path: NodePath
@export var seed_offset := 77
@export var outcrops := 50                ## groups of ore veins
@export var patches := 80                 ## groups of plants
@export var inner_radius := 34.0          ## nothing spawns closer to the middle of the map
@export var view_distance := 70.0         ## models further away are hidden (browser performance)

const VEIN_VARIANTS := 4
const RARITY := 0.8
const PLAINS_PATCHES := 0.3               # share of plant patches placed in the plains
## Kit models a plant may swap to, for variety. Same plant, same colours.
const ALT_MODELS := {
	"Flower_3_Group": "Flower_3_Single", "Flower_4_Group": "Flower_4_Single",
	"Flower_4_Single": "Flower_4_Group", "Plant_7": "Plant_7_Big", "Clover_2": "Clover_1",
}

var _world: Node
var _rng := RandomNumberGenerator.new()
var _built := {}                          # "skill|id|variant" -> model, copied for each node


func _ready() -> void:
	_world = get_node_or_null(world_path)
	if _world == null:
		return
	if not _world.get("is_generated"):
		await _world.generated
	_rng.seed = int(_world.random_seed) + seed_offset
	for i in outcrops:
		_outcrop()
	for i in patches:
		_patch()


func _exit_tree() -> void:
	for model in _built.values():
		model.free()
	_built.clear()


func _outcrop() -> void:
	var centre := _spot(func(p: Vector2) -> bool: return _world.plains_at(p.x, p.y) < 0.3)
	if centre == Vector2.INF:
		return
	var row := _pick_tier(GameData.tiers.mining, centre, func(_r: Dictionary) -> bool: return true)
	_group(row, centre, _rng.randi_range(2, 4), 1.6, 3.4)


func _patch() -> void:
	var in_plains := _rng.randf() < PLAINS_PATCHES
	var centre := _spot(func(p: Vector2) -> bool: return (_world.plains_at(p.x, p.y) > 0.5) == in_plains)
	if centre == Vector2.INF:
		return
	var row := _pick_tier(GameData.tiers.foraging, centre,
			func(r: Dictionary) -> bool: return not in_plains or _flowering(r.model))
	if not row.is_empty():
		_group(row, centre, _rng.randi_range(3, 6), 0.9, 2.6)


## Places up to `count` nodes of one tier around `centre`, the first on it.
func _group(row: Dictionary, centre: Vector2, count: int, near: float, far: float) -> void:
	var placed := 0
	for k in count * 3:
		if placed >= count:
			return
		var p := centre if k == 0 else centre + Vector2.from_angle(_rng.randf() * TAU) * _rng.randf_range(near, far)
		if k > 0 and not _open(p, 0.8):
			continue
		var node := GatherNode.new()
		node.setup(row.skill, row, _model(row))
		_place(node, p)
		placed += 1


## A model for one node: a shared build of its tier (and shape), copied, then sized and turned.
func _model(row: Dictionary) -> Node3D:
	var mining: bool = row.skill == "mining"
	var variant := _rng.randi() % VEIN_VARIANTS if mining else 0
	var look := row
	if not mining and ALT_MODELS.has(row.model) and _rng.randf() < 0.5:
		look = row.duplicate()
		look.model = ALT_MODELS[row.model]
	var key := "%s|%s|%s" % [row.skill, row.id, variant if mining else look.model]
	if not _built.has(key):
		_built[key] = NodeArt.vein(row, variant + 1) if mining else NodeArt.plant(look)
		_hide_far(_built[key])
	# Without DUPLICATE_USE_INSTANTIATION, so kit models keep their tinted materials.
	var model: Node3D = _built[key].duplicate(Node.DUPLICATE_SIGNALS | Node.DUPLICATE_GROUPS | Node.DUPLICATE_SCRIPTS)
	var size := _rng.randf_range(0.8, 1.15) if mining else _rng.randf_range(0.8, 1.25)
	model.scale = Vector3(_rng.randf_range(0.9, 1.1), _rng.randf_range(0.9, 1.1), _rng.randf_range(0.9, 1.1)) * size
	if not mining:
		model.rotation = Vector3(_rng.randf_range(-0.08, 0.08), 0.0, _rng.randf_range(-0.08, 0.08))
	return model


func _hide_far(model: Node3D) -> void:
	for g: GeometryInstance3D in model.find_children("*", "GeometryInstance3D", true, false):
		g.visibility_range_end = view_distance
		g.visibility_range_end_margin = 5.0


## Which tier grows at `p`: only tiers 1 and 2 at the inner edge, every tier by the map's edge,
## each tier RARITY times as common as the one below. Only rows that pass `fits` are picked.
func _pick_tier(rows: Array, p: Vector2, fits: Callable) -> Dictionary:
	var out := clampf((p.length() - inner_radius) / (_world.half - 10.0 - inner_radius), 0.0, 1.0)
	var top := 2 + roundi(out * (rows.size() - 2))
	var pool: Array = rows.slice(0, top).filter(fits)
	var total := 0.0
	for row in pool:
		total += pow(RARITY, row.tier - 1)
	var r := _rng.randf() * total
	for row in pool:
		r -= pow(RARITY, row.tier - 1)
		if r <= 0.0:
			return row
	return pool.back() if not pool.is_empty() else {}


## A random open spot that passes `fits`, or Vector2.INF after 40 tries.
func _spot(fits: Callable) -> Vector2:
	var half: float = _world.half
	for attempt in 40:
		var p := Vector2(_rng.randf_range(-half, half), _rng.randf_range(-half, half))
		if p.length() >= inner_radius and _open(p, 2.5) and fits.call(p):
			return p
	return Vector2.INF


## Dry, fairly flat land inside the map, with nothing within `room` metres.
func _open(p: Vector2, room: float) -> bool:
	var half: float = _world.half
	if maxf(absf(p.x), absf(p.y)) > half - 10.0 or _world.near_water(p.x, p.y, 1.5) or _world.is_blocked(p.x, p.y, room):
		return false
	var h: float = _world.ground_height(p.x, p.y)
	for d in [Vector2(1, 0), Vector2(-1, 0), Vector2(0, 1), Vector2(0, -1)]:
		if absf(_world.ground_height(p.x + d.x, p.y + d.y) - h) > 0.45:
			return false
	return true


func _flowering(model: String) -> bool:
	return model.begins_with("Flower") or model.begins_with("Clover")


## Stands the node on the terrain, turned at random, and keeps everything else out of its spot.
func _place(node: GatherNode, p: Vector2) -> void:
	node.position = to_local(Vector3(p.x, _world.ground_height(p.x, p.y) - 0.03, p.y))
	node.rotation.y = _rng.randf() * TAU
	add_child(node, true)
	_world.reserve(p.x, p.y, node.radius + (0.4 if node.skill == "mining" else 0.6))   # plants clear more grass, to be seen
