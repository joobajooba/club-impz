@tool
extends Node3D
## Scatters a dense stylized meadow: grass, clover and flower patches, drawn with MultiMesh chunks.
## The world is too big to fill at once, so chunks stream in around the camera (in the editor and
## in-game) and are freed again behind it. Grass follows the world generator's terrain, stays out of
## the water, avoids trees and rocks, and the plains biome gets far more flowers.
## Nothing it creates is saved into the scene, so to change the meadow edit the settings in the
## Inspector (tick "Regenerate" to refresh).

@export var world: NodePath = ^"../../World"   ## the world generator
@export var random_seed := 1234
@export_range(0.1, 3.0, 0.05) var density := 1.0
@export_range(0.1, 1.5, 0.01) var grass_min_height := 0.3
@export_range(0.1, 1.5, 0.01) var grass_max_height := 0.6
@export_range(0.0, 1.0, 0.01) var flower_amount := 0.5   ## how much of the meadow is flower patches
@export_range(0.0, 8.0, 0.1) var plains_flower_boost := 3.0   ## extra flowers in the plains biome
@export var wind_strength := 0.1
@export var wind_speed := 1.4
@export var chunk_size := 16.0
@export var view_distance := 55.0
@export var chunks_per_frame := 2
@export var avoid_root: NodePath = ^".."   ## grass avoids every StaticBody3D under this node
@export var regenerate := false:
	set(v):
		if v and is_inside_tree():
			_reset()

const SHADER := preload("res://meadow/foliage_wind.gdshader")
const GRASS := [["Grass_Wispy_Short", 3.0], ["Grass_Common_Short", 2.0], ["Grass_Wispy_Tall", 1.0], ["Grass_Common_Tall", 1.0]]
const CLOVER := [["Clover_1", 1.0], ["Clover_2", 1.0]]
const CELL := 4.0

var _world: Node
var _cache := {}
var _obstacles := {}   # grid cell -> Array of Vector3(x, z, radius), hand-placed bodies only
var _chunks := {}      # Vector2i -> Node3D
var _hn: FastNoiseLite
var _fn: FastNoiseLite
var _tn: FastNoiseLite

func _ready() -> void:
	_world = get_node_or_null(world)
	if _world and not _world.is_connected("generated", _reset):
		_world.connect("generated", _reset)
	_reset()

func _reset() -> void:
	for c in get_children():
		if c.owner == null:
			remove_child(c)
			c.queue_free()
	_chunks.clear()
	_cache.clear()
	_hn = _noise(random_seed, 0.06)       # grass height patches
	_fn = _noise(random_seed + 1, 0.08)   # flower patches
	_tn = _noise(random_seed + 2, 0.045)  # which flower species
	_collect_obstacles()
	_stream(true)

func _process(_delta: float) -> void:
	_stream(false)

func _stream(fill_near: bool) -> void:
	if _world == null or not _world.is_generated:
		return
	var cam = _camera_position()
	if cam == null:
		return
	var p := to_local(cam)
	var here := Vector2(p.x, p.z)
	var r := int(ceil(view_distance / chunk_size))
	var cc := Vector2i(int(floor(here.x / chunk_size)), int(floor(here.y / chunk_size)))
	var lim: float = _world.half

	# Free chunks that fell behind.
	for c in _chunks.keys():
		if _chunk_centre(c).distance_to(here) > view_distance + chunk_size:
			_chunks[c].queue_free()
			_chunks.erase(c)

	# Build the missing ones, nearest first. On (re)load everything close to the camera is built at once.
	var missing := []
	for dz in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var c := cc + Vector2i(dx, dz)
			if _chunks.has(c):
				continue
			var d := _chunk_centre(c).distance_to(here)
			if d > view_distance or absf(c.x * chunk_size) > lim + chunk_size or absf(c.y * chunk_size) > lim + chunk_size:
				continue
			missing.append(Vector3(c.x, c.y, d))
	missing.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.z < b.z)
	var budget := chunks_per_frame
	for m in missing:
		if budget <= 0 and not (fill_near and m.z < 30.0):
			break
		_build_chunk(Vector2i(int(m.x), int(m.y)))
		budget -= 1

func _camera_position() -> Variant:
	var cam: Camera3D
	if Engine.is_editor_hint():
		var ei = Engine.get_singleton("EditorInterface")
		if ei:
			var vp = ei.get_editor_viewport_3d(0)
			if vp:
				cam = vp.get_camera_3d()
	else:
		cam = get_viewport().get_camera_3d()
	if cam == null:
		return null
	return cam.global_position

func _chunk_centre(c: Vector2i) -> Vector2:
	return (Vector2(c) + Vector2(0.5, 0.5)) * chunk_size

func _build_chunk(c: Vector2i) -> void:
	var root := Node3D.new()
	root.name = "Chunk_%d_%d" % [c.x, c.y]
	add_child(root)
	_chunks[c] = root
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(Vector3i(c.x, c.y, random_seed))
	var x0 := c.x * chunk_size
	var z0 := c.y * chunk_size
	var area := chunk_size * chunk_size
	var lim: float = _world.half - 1.0
	var buckets := {}
	var plains_max := 0.0
	for corner in [Vector2(0, 0), Vector2(1, 0), Vector2(0, 1), Vector2(1, 1), Vector2(0.5, 0.5)]:
		plains_max = maxf(plains_max, _world.plains_at(x0 + corner.x * chunk_size, z0 + corner.y * chunk_size))

	# Grass, a little taller in the plains
	for i in int(9.0 * density * area):
		var x := x0 + rng.randf() * chunk_size
		var z := z0 + rng.randf() * chunk_size
		if absf(x) > lim or absf(z) > lim or _blocked(x, z):
			continue
		var pl: float = _world.plains_at(x, z) if plains_max > 0.0 else 0.0
		var h := lerpf(grass_min_height, grass_max_height, _n01(_hn, x, z)) * rng.randf_range(0.85, 1.15) * (1.0 + 0.2 * pl)
		_put(buckets, _pick(rng, GRASS), x, z, h, rng, "grass")

	# Clover ground cover
	for i in int(1.2 * density * area):
		var x := x0 + rng.randf() * chunk_size
		var z := z0 + rng.randf() * chunk_size
		if absf(x) > lim or absf(z) > lim or _blocked(x, z):
			continue
		_put(buckets, _pick(rng, CLOVER), x, z, rng.randf_range(0.14, 0.24), rng, "clover")

	# Flowers: dense patches of one species plus a light sprinkle everywhere; the plains get
	# (1 + plains_flower_boost) times as many and bigger patches.
	var patch_cut := lerpf(0.85, 0.45, flower_amount)
	var boost_max := 1.0 + plains_flower_boost * plains_max
	for i in int(4.0 * density * area * boost_max):
		var x := x0 + rng.randf() * chunk_size
		var z := z0 + rng.randf() * chunk_size
		var pl: float = _world.plains_at(x, z) if plains_max > 0.0 else 0.0
		if rng.randf() * boost_max > 1.0 + plains_flower_boost * pl:
			continue
		var p := _n01(_fn, x, z)
		if p < lerpf(patch_cut, 0.2, pl) and rng.randf() > lerpf(0.03, 0.4, pl):
			continue
		if absf(x) > lim or absf(z) > lim or _blocked(x, z):
			continue
		var grass_h := lerpf(grass_min_height, grass_max_height, _n01(_hn, x, z))
		var h := grass_h * rng.randf_range(1.12, 1.3)
		var species := "3" if _tn.get_noise_2d(x, z) > 0.0 else "4"
		var form := "Group" if rng.randf() < 0.6 else "Single"
		_put(buckets, "Flower_%s_%s" % [species, form], x, z, h, rng, "flower")

	for model in buckets:
		var info: Dictionary = _cache[model]
		var arr: Array = buckets[model]
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = info.mesh
		mm.instance_count = arr.size()
		for j in arr.size():
			mm.set_instance_transform(j, arr[j])
		var mmi := MultiMeshInstance3D.new()
		mmi.name = model
		mmi.multimesh = mm
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mmi)

func _put(buckets: Dictionary, model: String, x: float, z: float, h: float, rng: RandomNumberGenerator, kind: String) -> void:
	var info := _prepare(model, kind)
	if info.is_empty():
		return
	var y: float = _world.ground_height(x, z)
	if y < _world.water_level + 0.05:
		return
	var s: float = h / info.height
	var tilt := Basis(Vector3(rng.randf_range(-1, 1), 0, rng.randf_range(-1, 1)).normalized(), rng.randf_range(0.0, 0.12))
	var b := tilt * Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * s)
	var t: Transform3D = Transform3D(b, Vector3(x, y - 0.02, z)) * info.local
	if not buckets.has(model):
		buckets[model] = []
	buckets[model].append(t)

func _prepare(model: String, kind: String) -> Dictionary:
	if _cache.has(model):
		return _cache[model]
	var ps := load("res://glTF/%s.gltf" % model) as PackedScene
	if ps == null:
		push_warning("Meadow: could not load %s" % model)
		_cache[model] = {}
		return {}
	var root := ps.instantiate()
	var found := root.find_children("*", "MeshInstance3D", true, false)
	if found.is_empty():
		root.free()
		_cache[model] = {}
		return {}
	var mi := found[0] as MeshInstance3D
	var local := Transform3D.IDENTITY
	var n: Node = mi
	while n != root and n is Node3D:
		local = (n as Node3D).transform * local
		n = n.get_parent()
	var mesh := mi.mesh.duplicate() as Mesh
	var aabb := mesh.get_aabb()
	for s in mesh.get_surface_count():
		var orig := mi.get_active_material(s) as BaseMaterial3D
		var m := ShaderMaterial.new()
		m.shader = SHADER
		if orig != null:
			m.set_shader_parameter("albedo_tex", orig.albedo_texture)
			m.set_shader_parameter("albedo_col", orig.albedo_color)
			m.set_shader_parameter("use_scissor", orig.transparency != BaseMaterial3D.TRANSPARENCY_DISABLED)
		m.set_shader_parameter("height_ref", aabb.end.y)
		m.set_shader_parameter("wind_strength", wind_strength)
		m.set_shader_parameter("wind_speed", wind_speed)
		match kind:
			"grass":
				m.set_shader_parameter("normal_up", 1.0)
				m.set_shader_parameter("tint_a", Color(0.78, 0.86, 0.52))
				m.set_shader_parameter("tint_b", Color(1.0, 1.05, 0.9))
			"clover":
				m.set_shader_parameter("normal_up", 0.8)
				m.set_shader_parameter("base_darken", 0.3)
			_:
				m.set_shader_parameter("normal_up", 0.4)
				m.set_shader_parameter("base_darken", 0.35)
		mesh.surface_set_material(s, m)
	var height := (local * aabb).end.y
	root.free()
	_cache[model] = {"mesh": mesh, "local": local, "height": maxf(height, 0.01)}
	return _cache[model]

func _collect_obstacles() -> void:
	_obstacles.clear()
	var root := get_node_or_null(avoid_root)
	if root == null:
		return
	for body in root.find_children("*", "StaticBody3D", true, false):
		for node in body.find_children("*", "CollisionShape3D", false, false):
			var cs := node as CollisionShape3D
			var shape := cs.shape
			var r := 0.0
			if shape is CylinderShape3D:
				r = (shape as CylinderShape3D).radius * 0.9
			elif shape is BoxShape3D:
				var bs := (shape as BoxShape3D).size
				r = maxf(bs.x, bs.z) * 0.42
			else:
				continue
			var p := to_local(cs.global_position)
			var o := Vector3(p.x, p.z, r)
			for gx in range(int(floor((p.x - r) / CELL)), int(floor((p.x + r) / CELL)) + 1):
				for gz in range(int(floor((p.z - r) / CELL)), int(floor((p.z + r) / CELL)) + 1):
					var k := Vector2i(gx, gz)
					if not _obstacles.has(k):
						_obstacles[k] = []
					_obstacles[k].append(o)

func _blocked(x: float, z: float) -> bool:
	if _world.is_blocked(x, z):
		return true
	var k := Vector2i(int(floor(x / CELL)), int(floor(z / CELL)))
	if not _obstacles.has(k):
		return false
	for o in _obstacles[k]:
		if (x - o.x) * (x - o.x) + (z - o.y) * (z - o.y) < o.z * o.z:
			return true
	return false

func _pick(rng: RandomNumberGenerator, list: Array) -> String:
	var total := 0.0
	for e in list:
		total += e[1]
	var r := rng.randf() * total
	for e in list:
		r -= e[1]
		if r <= 0.0:
			return e[0]
	return list[0][0]

func _noise(s: int, f: float) -> FastNoiseLite:
	var n := FastNoiseLite.new()
	n.seed = s
	n.frequency = f
	return n

func _n01(n: FastNoiseLite, x: float, z: float) -> float:
	return clampf(n.get_noise_2d(x, z) * 0.7 + 0.5, 0.0, 1.0)
