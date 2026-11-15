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


## Loading screen (main.gd): builds the whole world before the player joins it, so nothing is built
## (and nothing hitches) while they play. Each call spends about `budget_usec`; returns the share done.
## Terrain is 30% of the bar, trees and plants the rest.
var _load_chunks: Array[Vector2i] = []

func load_step(budget_usec: int) -> float:
	if _load_chunks.is_empty():
		_load_chunks = terrain.load_list(player.global_position if player else _marker_pos("spawn_point"))
	var built := terrain.load_some(_load_chunks, budget_usec)
	var t := float(built) / maxf(_load_chunks.size(), 1)
	var s := scatter.load_some(budget_usec) if t >= 1.0 else 0.0
	return 0.3 * t + 0.7 * s


func set_view_focus(f: Node3D) -> void:
	## The local view (player, or the free camera in camera mode). Terrain meshes, the foliage build order, tree
	## shadows and weather particles follow it; colliders stay round the player.
	terrain.set_focus(f)
	scatter.set_focus(f)
	environment.set_focus(f)


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
		var size := Vector2(r[2] - r[0], r[3] - r[1])
		plane.size = size
		plane.subdivide_width = maxi(0, int(size.x / 2.0) - 1)  # 1 vertex per 2 m for the waves
		plane.subdivide_depth = maxi(0, int(size.y / 2.0) - 1)
		var deep := Color(terrain.data.biome_data["biomes"][w["biome"]]["water"])
		var mat := ShaderMaterial.new()
		mat.shader = shader
		mat.set_shader_parameter("deep_color", deep)
		mat.set_shader_parameter("shallow_color", deep.lerp(Color("#bff0e6"), 0.25))
		# depth under the plane, 2 px per metre (no depth texture in web builds)
		var dw := int(ceil(size.x * 2.0))
		var dd := int(ceil(size.y * 2.0))
		var img := Image.create(dw, dd, false, Image.FORMAT_RF)
		for pz in dd:
			for px in dw:
				var d: float = w["level"] - terrain.data.height(r[0] + (px + 0.5) / 2.0, r[1] + (pz + 0.5) / 2.0)
				img.set_pixel(px, pz, Color(maxf(d, 0.0), 0, 0))
		mat.set_shader_parameter("depth_map", ImageTexture.create_from_image(img))
		mat.set_shader_parameter("rect", Vector4(r[0], r[1], dw / 2.0, dd / 2.0))
		mat.set_shader_parameter("rect_size", size)  # the true rect (rect.zw is the rounded depth map size)
		mat.render_priority = 0  # the waterfall ribbon (priority 1) always draws over the pools
		mat.set_shader_parameter("use_depth", true)
		var mi := MeshInstance3D.new()
		mi.name = w["name"]
		mi.mesh = plane
		mi.material_override = mat
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		mi.position = Vector3((r[0] + r[2]) / 2.0, w["level"], (r[1] + r[3]) / 2.0)
		water_root.add_child(mi)
	var wf: Dictionary = terrain.data.layout.get("waterfall", {})
	if not wf.is_empty():
		_make_waterfall(shader, wf)


## The forest waterfall: a ribbon draped over the baked notch (bake_world_data.gd _shape_water step e) from the
## pool channel (x 216) over the crest and down the face into the river (x 202), a foam disc on the plunge pool
## and a little spray at the foot.
func _make_waterfall(shader: Shader, wf: Dictionary) -> void:
	var d := terrain.data
	var lip_z: float = wf["z"]
	var top: float = wf["top"]
	var bottom: float = wf["bottom"]
	const WIDTH := 9.0
	var cols := 10  # 9 columns across
	var xs := []
	var x := 216.0
	while x >= 201.99:
		xs.append(x)
		x -= 0.5
	var rows := []
	for xi in xs.size():
		var s := float(xi) / float(xs.size() - 1)
		var inset := 0.5 * cos(s * PI * 0.5)  # 0.5 m in on each side at the top, 0 at the bottom
		var row := []
		for c in cols:
			var u := float(c) / float(cols - 1)
			var z := lip_z - WIDTH / 2.0 + inset + u * (WIDTH - 2.0 * inset)
			var y := maxf(d.height(xs[xi], z) + 0.15, bottom + 0.03)
			if xs[xi] >= 211.0:
				y = maxf(y, top + 0.03)  # just above the pool plane over the channel and the crest
			row.append(Vector3(xs[xi], y, z))
		rows.append(row)
	# v: metres along the surface; travel: v divided by the flow speed (0.3x on the flat, 1x on the face)
	var v := PackedFloat32Array()
	var travel := PackedFloat32Array()
	v.resize(rows.size())
	travel.resize(rows.size())
	for ri in range(1, rows.size()):
		var a: Vector3 = rows[ri - 1][cols / 2]
		var b: Vector3 = rows[ri][cols / 2]
		var seg := a.distance_to(b)
		var speed := lerpf(0.3, 1.0, clampf(absf(b.y - a.y) / maxf(seg, 0.001) * 1.5, 0.0, 1.0))
		v[ri] = v[ri - 1] + seg
		travel[ri] = travel[ri - 1] + seg / speed
	var total := v[rows.size() - 1]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for ri in rows.size():
		for c in cols:
			st.set_uv(Vector2(float(c) / float(cols - 1) * WIDTH, v[ri]))
			st.set_uv2(Vector2(total - v[ri], travel[ri]))  # metres to the bottom end (fade), flow travel
			st.add_vertex(rows[ri][c])
	for ri in rows.size() - 1:
		for c in cols - 1:
			var i0 := ri * cols + c
			st.add_index(i0)
			st.add_index(i0 + 1)
			st.add_index(i0 + cols)
			st.add_index(i0 + 1)
			st.add_index(i0 + cols + 1)
			st.add_index(i0 + cols)
	st.generate_normals()
	var arrays := st.commit_to_arrays()
	var normals: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
	if normals[0].y < 0.0:  # whichever way the winding went, light it from above
		for i in normals.size():
			normals[i] = -normals[i]
		arrays[Mesh.ARRAY_NORMAL] = normals
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	var mat := ShaderMaterial.new()
	mat.shader = shader
	var forest_water := Color(d.biome_data["biomes"]["forest"]["water"])
	mat.set_shader_parameter("deep_color", forest_water.lightened(0.15))
	mat.set_shader_parameter("flow", 1.6)
	mat.set_shader_parameter("ribbon_width", WIDTH)
	mat.render_priority = 1
	var mi := MeshInstance3D.new()
	mi.name = "waterfall"
	mi.mesh = mesh
	mi.material_override = mat
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	water_root.add_child(mi)
	# foam on the plunge pool
	var foam := PlaneMesh.new()
	foam.size = Vector2(7.0, 7.0)
	foam.subdivide_width = 6
	foam.subdivide_depth = 6
	var fmat := ShaderMaterial.new()
	fmat.shader = shader
	fmat.set_shader_parameter("foam_only", true)
	fmat.set_shader_parameter("wave_height", 0.015)
	fmat.render_priority = 2
	var fm := MeshInstance3D.new()
	fm.name = "waterfall_foam"
	fm.mesh = foam
	fm.material_override = fmat
	fm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	fm.position = Vector3(205.0, bottom + 0.05, lip_z)
	water_root.add_child(fm)
	# spray at the foot (CPU particles: Compatibility and web safe)
	var spray := CPUParticles3D.new()
	spray.name = "waterfall_spray"
	spray.amount = 40
	spray.lifetime = 1.2
	spray.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	spray.emission_box_extents = Vector3(0.5, 0.2, 3.0)
	spray.direction = Vector3(-0.3, 1.0, 0.0)
	spray.spread = 25.0
	spray.initial_velocity_min = 2.0
	spray.initial_velocity_max = 4.0
	spray.gravity = Vector3(0.0, -6.0, 0.0)
	spray.scale_amount_min = 0.3
	spray.scale_amount_max = 0.6
	var ramp := Gradient.new()
	ramp.set_color(0, Color(1, 1, 1, 0.85))
	ramp.set_color(1, Color(1, 1, 1, 0.0))
	spray.color_ramp = ramp
	var q := QuadMesh.new()
	q.size = Vector2(0.6, 0.6)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	qm.vertex_color_use_as_albedo = true
	qm.albedo_color = Color.WHITE
	q.material = qm
	spray.mesh = q
	spray.position = Vector3(207.0, bottom + 0.2, lip_z)
	water_root.add_child(spray)
