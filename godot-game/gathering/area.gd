extends Node3D
## One area of the world: a gathering skill's nodes and its station, or the camp. Everything stands
## on the World's terrain, so the node's own height doesn't matter. The World keeps a matching
## clearing (its `clearings` setting) free of grass and props; move both together. TEST layouts:
## - mining: the Three.js test's layout, low tiers in the middle, plus the furnace and anvil,
## - foraging, lumbering, hunting: the tiers in a spiral from the middle out, station in the middle,
## - fishing: spots on the water along the nearest shore (this node stands on it), and the campfire
##   on clear land nearby, away from the spots so F there doesn't open it,
## - camp: the merchant, stable, battle board and treasure dig.

@export_enum("mining", "foraging", "hunting", "lumbering", "fishing", "camp") var skill := "mining"
@export var world_path: NodePath
@export var radius := 7.0

## Mining: where each ore's veins stand, [x, z, turn, size]. A TEST layout.
const MINING_SPOTS := {
	"tin": [[1.55, -1.05, 0.0, 1.0], [-2.6, -2.4, 1.9, 0.85], [-3.2, 1.8, 4.1, 1.1], [3.1, 2.7, 2.7, 0.9], [0.4, 3.4, 5.3, 0.75]],
	"copper": [[3.0, -2.6, 0.3, 0.85], [-4.6, 4.6, 2.2, 0.85]],
	"iron": [[-5.6, -0.6, 1.2, 0.9]],
	"coal": [[-5.2, -5.0, 4.0, 0.9]],
	"gold": [[-1.4, -6.0, 0.6, 0.9]],
	"obsidian": [[2.6, -6.0, 5.2, 0.9]],
	"titanite": [[6.0, -4.2, 3.1, 0.9]],
	"dreadstone": [[6.2, 0.6, 1.7, 0.95]],
	"void": [[5.4, 5.2, 4.6, 1.0]],
	"stellarite": [[0.2, 6.4, 0.9, 1.05]],
}
## Stations by area, [kind, x, z, turn].
const STATIONS := {
	"mining": [["furnace", -1.7, 0.9, 0.5], ["blacksmith", 1.5, 1.2, -0.4]],
	"foraging": [["drying_rack", 0.0, 0.0, 0.3]],
	"hunting": [["tanning_rack", 0.0, 0.0, 0.0]],
	"lumbering": [["sawbench", 0.0, 0.0, 0.6]],
	"fishing": [],   # the campfire is placed after the spots, see _fishing_spots
	"camp": [["merchant", -2.5, -2.0, 0.5], ["stable", 3.0, -2.2, -0.4], ["arena", -2.6, 2.6, 2.4], ["dig_site", 2.6, 2.6, 0.0]],
}
const GOLDEN_ANGLE := 2.39996
const FISH_SPACING := 3.0

var _world: Node


func _ready() -> void:
	_world = get_node_or_null(world_path)
	if _world and not _world.get("is_generated"):
		await _world.generated
	for s in STATIONS[skill]:
		var station := Station.new()
		station.setup(s[0])
		_place(station, s[1], s[2], s[3])
	match skill:
		"mining":
			for row in GameData.tiers.mining:
				for spot in MINING_SPOTS[row.id]:
					var node := GatherNode.new()
					var model := NodeArt.vein(row)
					model.scale *= spot[3]
					node.setup("mining", row, model)
					_place(node, spot[0], spot[1], spot[2])
		"foraging", "lumbering", "hunting":
			_spiral()
		"fishing":
			_fishing_spots()


## A node for each tier, with a second of tiers 1 and 2, in a spiral from the middle out.
func _spiral() -> void:
	var rows: Array = GameData.tiers[skill]
	var order: Array = [rows[0], rows[0], rows[1], rows[1]] + rows.slice(2)
	var c := (radius - 1.2) / sqrt(order.size() + 1.5)
	for i in order.size():
		var r := c * sqrt(i + 1.5)
		var a := i * GOLDEN_ANGLE
		var row: Dictionary = order[i]
		var node: GatherNode
		match skill:
			"foraging":
				node = GatherNode.new()
				node.setup("foraging", row, NodeArt.plant(row))
			"lumbering":
				node = GatherNode.new()
				node.setup("lumbering", row, NodeArt.tree(row), 0.35)
			"hunting":
				node = Animal.new()
				node.setup_animal(row)
				if _world:
					node.ground_at = Callable(_world, "ground_height")
		_place(node, cos(a) * r, sin(a) * r, randf() * TAU)


## Spots on the water 2.2 m out from dry land, nearest this node first, one per fish tier.
func _fishing_spots() -> void:
	if not _world:
		return
	var level: float = _world.water_level
	var me := Vector2(global_position.x, global_position.z)
	var found: Array = []
	for dz in range(-24, 25):
		for dx in range(-24, 25):
			var p := me + Vector2(dx, dz)
			if _world.ground_height(p.x, p.y) < level + 0.15 or _world.is_blocked(p.x, p.y, 0.5):
				continue
			for k in 16:
				var q := p + Vector2.from_angle(k * TAU / 16.0) * 2.2
				if _world.ground_height(q.x, q.y) < level - 0.25:
					found.append([q.distance_to(me), q])
					break
	found.sort_custom(func(a, b): return a[0] < b[0])
	var chosen: Array = []
	for f in found:
		if chosen.size() >= GameData.tiers.fishing.size():
			break
		if chosen.all(func(c): return c.distance_to(f[1]) >= FISH_SPACING):
			chosen.append(f[1])
	for i in chosen.size():
		var spot := FishingSpot.new()
		spot.setup_spot(GameData.tiers.fishing[i])
		spot.position = to_local(Vector3(chosen[i].x, level, chosen[i].y))
		add_child(spot, true)
	await get_tree().physics_frame   # so the scene's colliders can be queried
	var fire := _clear_land(me, chosen)
	var campfire := Station.new()
	campfire.setup("campfire")
	_place(campfire, fire.x - me.x, fire.y - me.y, 0.0)


## Dry land 3 to 6 m from `me`, at least 3.5 m from every fishing spot, with nothing solid on it
## (a sphere check from knee height up, above the terrain).
func _clear_land(me: Vector2, spots: Array) -> Vector2:
	var space := get_world_3d().direct_space_state
	var ball := SphereShape3D.new()
	ball.radius = 0.7
	var query := PhysicsShapeQueryParameters3D.new()
	query.shape = ball
	for r in [3.0, 4.0, 5.0, 6.0]:
		for k in 16:
			var p: Vector2 = me + Vector2.from_angle(k * TAU / 16.0) * r
			var h: float = _world.ground_height(p.x, p.y)
			if h < _world.water_level + 0.2 or _world.is_blocked(p.x, p.y, 1.0):
				continue
			if not spots.all(func(s): return s.distance_to(p) >= 3.5):
				continue
			query.transform = Transform3D(Basis.IDENTITY, Vector3(p.x, h + 1.0, p.y))
			if space.intersect_shape(query, 1).is_empty():
				return p
	return me


## Placed before it joins the tree, so a node's _ready sees where it stands.
func _place(node: Node3D, x: float, z: float, turn: float) -> void:
	var p := global_position + Vector3(x, 0.0, z)
	if _world and _world.has_method("ground_height"):
		p.y = _world.ground_height(p.x, p.z) - 0.03   # sink a little so no gap shows on slopes
	node.position = to_local(p)
	node.rotation.y = turn
	add_child(node, true)
