class_name GameWorld
extends Node3D
## Shared world script for the hub and the resource world: terrain, water, spawn markers, and the queries main.gd
## and the debug overlay use (ground_height, biome_at, biome_centre). Scatter and environment hook in from here.

@export var data_prefix := "resource"
@export var fixed_biome := -1
@export var view_chunks := 4

var terrain: TerrainWorld
var player: Node3D
var water_root: Node3D
var environment: BiomeEnvironment
var scatter: Scatter


func _ready() -> void:
	terrain = TerrainWorld.new()
	terrain.name = "terrain"
	terrain.data_prefix = data_prefix
	terrain.fixed_biome = fixed_biome
	terrain.view_chunks = view_chunks
	terrain.far_mesh = fixed_biome < 0
	add_child(terrain)
	var t0 := Time.get_ticks_msec()
	terrain.setup()
	print("world %s: terrain setup %d ms" % [data_prefix, Time.get_ticks_msec() - t0])
	_make_markers()
	_make_water()
	terrain.build_now_around(_marker_pos("spawn_point"), 1)
	environment = BiomeEnvironment.new()
	environment.name = "environment"
	add_child(environment)
	environment.setup(terrain.data.biome_data, WorldData.BIOMES[fixed_biome] if fixed_biome >= 0 else "forest")
	scatter = Scatter.new()
	scatter.name = "scatter"
	add_child(scatter)
	scatter.setup(self, terrain.data)
	if fixed_biome < 0:
		_make_biome_areas()
	for c in get_children():
		if c.has_method("populate"):
			c.populate(self)
	print("world %s: ready %d ms" % [data_prefix, Time.get_ticks_msec() - t0])


func _make_biome_areas() -> void:
	## One Area3D per biome band; entering one fades the environment to that biome (game_worlds.md section 4.9).
	var root := Node3D.new()
	root.name = "biome_areas"
	add_child(root)
	var band: float = terrain.data.band
	var names := biome_names()
	for i in names.size():
		var area := Area3D.new()
		area.name = "area_%s" % names[i]
		area.collision_layer = 8
		area.collision_mask = 2
		var cs := CollisionShape3D.new()
		var shape := BoxShape3D.new()
		shape.size = Vector3(band, 400.0, terrain.data.size.y)
		cs.shape = shape
		area.add_child(cs)
		area.position = Vector3(band * (i + 0.5), 100.0, terrain.data.origin.y + terrain.data.size.y / 2.0)
		root.add_child(area)
		area.body_entered.connect(func(b): if b == player: environment.set_biome(names[i]))


func data() -> WorldData:
	return terrain.data


func set_player(p: Node3D) -> void:
	player = p
	terrain.set_player(p)
	for c in get_children():
		if c != terrain and c.has_method("set_player"):
			c.set_player(p)


func ground_height(x: float, z: float) -> float:
	return terrain.data.height(x, z)


func biome_at(pos: Vector3) -> String:
	return terrain.data.biome_name(pos.x, pos.z)


func biome_names() -> Array:
	return ["forest", "mountain", "frost", "plains", "swamp"]


func biome_centre(biome: String) -> Transform3D:
	## Centre of a biome band, on the main path, facing deeper into the world.
	var i := biome_names().find(biome)
	var x := 128.0 + 256.0 * maxi(i, 0)
	var z := _path_z_near(x)
	terrain.build_now_around(Vector3(x, 0, z), 1)
	var xf := Transform3D(Basis(Vector3.UP, -PI / 2.0), Vector3(x, terrain.data.height(x, z) + 0.3, z))
	return xf


func _path_z_near(x: float) -> float:
	var best := 0.0
	var bd := 1e9
	for p in terrain.data.layout.get("main_path", []):
		if absf(p[0] - x) < bd:
			bd = absf(p[0] - x)
			best = p[1]
	return best


func _marker_pos(marker_name: String) -> Vector3:
	var m := find_child(marker_name, true, false) as Node3D
	return m.global_position if m else Vector3.ZERO


func _make_markers() -> void:
	## Spawn and portal arrival markers come from the baked layout (unless the scene already has one).
	var sp: Array = terrain.data.layout.get("spawn_point", [0, 0])
	if find_child("spawn_point", true, false) == null:
		var m := Marker3D.new()
		m.name = "spawn_point"
		add_child(m)
		var x: float = sp[0]
		var z: float = sp[1]
		m.global_position = Vector3(x, terrain.data.height(x, z) + 0.2, z)
		if fixed_biome < 0:
			m.rotation.y = -PI / 2.0  # resource world: face deeper into the world (+x)


func _make_water() -> void:
	water_root = Node3D.new()
	water_root.name = "water"
	add_child(water_root)
	var shader: Shader = load("res://shaders/water.gdshader")
	for w in terrain.data.layout.get("water", []):
		var r: Array = w["rect"]
		var plane := PlaneMesh.new()
		plane.size = Vector2(r[2] - r[0], r[3] - r[1])
		plane.subdivide_width = 0
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("water_color", Color(terrain.data.biome_data["biomes"][w["biome"]]["water"]))
		var mi := MeshInstance3D.new()
		mi.name = w["name"]
		mi.mesh = plane
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = Vector3((r[0] + r[2]) / 2.0, w["level"], (r[1] + r[3]) / 2.0)
		water_root.add_child(mi)
	var wf: Dictionary = terrain.data.layout.get("waterfall", {})
	if not wf.is_empty():
		var top: float = wf["top"]
		var bottom: float = wf["bottom"]
		var quad := QuadMesh.new()
		quad.size = Vector2(10.0, top - bottom + 0.6)
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("water_color", Color("#5ab0e8"))
		mat.set_shader_parameter("flow", 1.6)
		var mi := MeshInstance3D.new()
		mi.name = "waterfall"
		mi.mesh = quad
		mi.material_override = mat
		mi.position = Vector3(wf["x"], (top + bottom) / 2.0, wf["z"])
		mi.rotation.y = PI / 2.0
		water_root.add_child(mi)
