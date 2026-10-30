extends Node3D
## Places the hub landmarks (game_worlds.md section 3.3) at the baked layout positions: the castle centrepiece,
## the market stalls, the crafting area (smelter, workbenches, anvil) and the portal to the resource world.
## No resource nodes and no combat in the hub (section 3.1).


## The castle model is built at imp scale (about 16 m wide); the hub shows it larger so the centrepiece reads
## from across the village. Set to 1.0 for true imp scale.
const CASTLE_SCALE := 2.5


func populate(world: GameWorld) -> void:
	var lm: Dictionary = world.data().layout["landmarks"]
	var castle := _place(world, "res://scenes/hub/hub_castle.tscn", lm["castle"], PI)  # model faces -z; turn it to face the square
	castle.name = "castle"
	castle.scale = Vector3.ONE * CASTLE_SCALE
	var m: Array = lm["market"]
	for i in 4:
		var a := i * TAU / 4.0 + PI / 4.0
		var s := _place(world, "res://scenes/hub/market_stall_placeholder.tscn", [m[0] + cos(a) * 7.5, m[1] + sin(a) * 7.5], -a + PI / 2.0)
		s.set("colour_seed", i)
		s.name = "market_stall_%d" % (i + 1)
	var c: Array = lm["crafting_area"]
	_place(world, "res://scenes/hub/smelter_placeholder.tscn", [c[0] - 4.0, c[1] - 3.0], 0.3).name = "smelter"
	_place(world, "res://scenes/hub/workbench_placeholder.tscn", [c[0] + 3.5, c[1] - 2.0], -0.2).name = "workbench_1"
	_place(world, "res://scenes/hub/workbench_placeholder.tscn", [c[0] + 3.0, c[1] + 3.5], 0.4).name = "workbench_2"
	_place(world, "res://scenes/hub/anvil_placeholder.tscn", [c[0] - 2.5, c[1] + 3.0], 0.8).name = "anvil"
	var portal := _place(world, "res://scenes/shared/portal.tscn", lm["portal"], -PI / 4.0)
	portal.name = "portal_to_resource_world"
	portal.set("target_world", "resource")
	portal.set("target_spawn", "spawn_point")


func _place(world: GameWorld, path: String, xz: Array, yaw: float) -> Node3D:
	var n := (load(path) as PackedScene).instantiate() as Node3D
	add_child(n)
	var x: float = xz[0]
	var z: float = xz[1]
	n.global_position = Vector3(x, world.ground_height(x, z) - 0.1, z)
	n.rotation.y = yaw
	return n
