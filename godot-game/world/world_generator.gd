@tool
extends Node3D
## Builds the big open world around the hand-made demo area: rolling terrain, a river with two
## tributaries, ponds, a flat flower "plains" biome (no trees) and scattered forests, rocks,
## bushes, plants, mushrooms and pebbles.
## Everything is generated when the scene loads (in the editor too) and nothing is saved into the
## scene, so to change the world edit the settings in the Inspector and tick "Regenerate".
## The original 44 m demo area (its terrain and hand-placed foliage) stays in the middle.
## Bushes have no collision, so the player can walk through them.

signal generated

@export var world_size := 440.0
@export var random_seed := 2026
@export var hill_height := 7.0
@export var water_level := -0.446
@export_group("Biomes")
@export var plains_center := Vector2(130.0, -120.0)
@export var plains_radius := 80.0
@export var pond_count := 8
@export_range(0.0, 3.0, 0.05) var tree_density := 1.0
@export_range(0.0, 3.0, 0.05) var prop_density := 1.0   ## rocks, bushes, plants, mushrooms, pebbles
@export var clearings: Array[Vector3] = []   ## (x, z, radius) circles kept free of props and grass, e.g. the mining site
@export_group("Rendering")
@export var ground_material: Material
@export var water_material: Material
@export var centre_mesh: Mesh   ## the original hand-made terrain, blended into the middle of the map
@export var tree_view_distance := 260.0
@export var small_view_distance := 70.0
@export_group("")
@export var regenerate := false:
	set(v):
		if v and is_inside_tree():
			generate()

const CHUNK := 55            # terrain chunk size in metres (1 m grid)
const CENTRE_HALF := 22.0    # half size of the original demo area
const CELL := 4.0            # obstacle lookup cell

const TREES := [["CommonTree_1", 1.0], ["CommonTree_2", 1.0], ["CommonTree_3", 1.0], ["CommonTree_4", 1.0],
		["CommonTree_5", 1.0], ["Pine_1", 0.8], ["Pine_2", 0.8], ["Pine_3", 0.8], ["Pine_4", 0.8], ["Pine_5", 0.8],
		["TwistedTree_1", 0.06], ["TwistedTree_2", 0.06], ["TwistedTree_3", 0.06], ["TwistedTree_4", 0.06], ["TwistedTree_5", 0.06]]
const ROCKS := [["Rock_Medium_1", 1.0], ["Rock_Medium_2", 1.0], ["Rock_Medium_3", 1.0]]
const BUSHES := [["Bush_Common", 1.0], ["Bush_Common_Flowers", 0.6]]
const PLANTS := [["Plant_1", 1.0], ["Plant_1_Big", 0.5], ["Plant_7", 1.0], ["Plant_7_Big", 0.6], ["Fern_1", 0.8]]
const SHROOMS := [["Mushroom_Common", 1.0], ["Mushroom_Laetiporus", 0.6]]
const PEBBLES := [["Pebble_Round_1", 1.0], ["Pebble_Round_2", 1.0], ["Pebble_Round_3", 1.0], ["Pebble_Round_4", 1.0],
		["Pebble_Round_5", 1.0], ["Pebble_Square_1", 1.0], ["Pebble_Square_2", 1.0], ["Pebble_Square_3", 1.0],
		["Pebble_Square_4", 1.0], ["Pebble_Square_5", 1.0], ["Pebble_Square_6", 1.0]]

var is_generated := false
var half := 0.0
var _n := 0                           # vertices per side
var _h := PackedFloat32Array()        # terrain heights, 1 m grid
var _plains := PackedFloat32Array()   # 0..1 plains biome mask
var _river_d := PackedFloat32Array()  # distance to the nearest river centre line
var _river_w := PackedFloat32Array()  # half width of that river
var _centre := PackedFloat32Array()
var _centre_n := 0
var _ponds: Array[Vector4] = []       # x, z, radius, rim noise offset
var _obstacles := {}                  # grid cell -> Array of Vector3(x, z, radius)
var _models := {}
var _instances := {}                  # "model|cx|cz" -> Array[Transform3D]
var _collision: StaticBody3D

func _ready() -> void:
	generate()

func generate() -> void:
	is_generated = false
	for c in get_children():
		if c.owner == null:
			remove_child(c)
			c.queue_free()
	_obstacles.clear()
	_instances.clear()
	_ponds.clear()
	half = world_size * 0.5
	_n = int(round(world_size)) + 1
	var rng := RandomNumberGenerator.new()
	rng.seed = random_seed
	_load_centre()
	_build_heights(rng)
	_build_terrain()
	_build_walls()
	_scatter(rng)
	is_generated = true
	generated.emit()

# ---------------------------------------------------------------- queries (used by the meadow)

func ground_height(x: float, z: float) -> float:
	var gx := clampf(x + half, 0.0, _n - 1.001)
	var gz := clampf(z + half, 0.0, _n - 1.001)
	var ix := int(gx)
	var iz := int(gz)
	var fx := gx - ix
	var fz := gz - iz
	var i := iz * _n + ix
	return lerpf(lerpf(_h[i], _h[i + 1], fx), lerpf(_h[i + _n], _h[i + _n + 1], fx), fz)

func plains_at(x: float, z: float) -> float:
	return _plains[_idx(x, z)]

func near_water(x: float, z: float, margin: float) -> bool:
	var i := _idx(x, z)
	if _river_d[i] < _river_w[i] + margin:
		return true
	for p in _ponds:
		if Vector2(x - p.x, z - p.y).length() < p.z * 1.25 + margin:
			return true
	return ground_height(x, z) < water_level + 0.25

func is_blocked(x: float, z: float, radius := 0.0) -> bool:
	var k := Vector2i(int(floor(x / CELL)), int(floor(z / CELL)))
	for dx in range(-1, 2):
		for dz in range(-1, 2):
			var list = _obstacles.get(k + Vector2i(dx, dz))
			if list == null:
				continue
			for o in list:
				var r: float = o.z + radius
				if (x - o.x) * (x - o.x) + (z - o.y) * (z - o.y) < r * r:
					return true
	return false

## Marks a circle as taken, so later props, the meadow's grass and other spawns keep out of it.
func reserve(x: float, z: float, radius: float) -> void:
	_add_obstacle(x, z, radius)

func _idx(x: float, z: float) -> int:
	var ix := clampi(roundi(x + half), 0, _n - 1)
	var iz := clampi(roundi(z + half), 0, _n - 1)
	return iz * _n + ix

# ---------------------------------------------------------------- terrain

func _load_centre() -> void:
	_centre = PackedFloat32Array()
	_centre_n = int(round(CENTRE_HALF * 4.0)) + 1   # 0.5 m grid
	if centre_mesh == null:
		return
	_centre.resize(_centre_n * _centre_n)
	var verts: PackedVector3Array = centre_mesh.surface_get_arrays(0)[Mesh.ARRAY_VERTEX]
	for p in verts:
		var i := roundi((p.x + CENTRE_HALF) * 2.0)
		var j := roundi((p.z + CENTRE_HALF) * 2.0)
		if i >= 0 and j >= 0 and i < _centre_n and j < _centre_n:
			_centre[j * _centre_n + i] = p.y

func _centre_height(x: float, z: float) -> float:
	var gx := clampf((x + CENTRE_HALF) * 2.0, 0.0, _centre_n - 1.001)
	var gz := clampf((z + CENTRE_HALF) * 2.0, 0.0, _centre_n - 1.001)
	var ix := int(gx)
	var iz := int(gz)
	var fx := gx - ix
	var fz := gz - iz
	var i := iz * _centre_n + ix
	return lerpf(lerpf(_centre[i], _centre[i + 1], fx), lerpf(_centre[i + _centre_n], _centre[i + _centre_n + 1], fx), fz)

## x position of the original stream at a given z (its lowest point across the demo area).
func _creek_x(z: float) -> float:
	if _centre.is_empty():
		return -14.5
	var j := clampi(roundi((z + CENTRE_HALF) * 2.0), 0, _centre_n - 1)
	var best := INF
	var best_i := 0
	for i in _centre_n >> 1:   # the stream runs through the west half
		var v := _centre[j * _centre_n + i]
		if v < best:
			best = v
			best_i = i
	return best_i * 0.5 - CENTRE_HALF

func _build_heights(rng: RandomNumberGenerator) -> void:
	var count := _n * _n
	_h.resize(count)
	_plains.resize(count)
	_river_d.resize(count)
	_river_w.resize(count)
	_river_d.fill(1.0e9)
	_river_w.fill(0.0)
	var hills := _noise(random_seed, 0.0055, 5)
	var detail := _noise(random_seed + 1, 0.04, 2)
	var edge := _noise(random_seed + 2, 0.02, 1)
	var has_centre := not _centre.is_empty()

	# Base terrain: flat near the demo area, rolling hills further out, flattened in the plains,
	# and a ridge along the map edge.
	for j in _n:
		var z := j - half
		for i in _n:
			var x := i - half
			var r := sqrt(x * x + z * z)
			var m := maxf(absf(x), absf(z))
			var pd := Vector2(x, z).distance_to(plains_center) / (plains_radius * (1.0 + 0.22 * edge.get_noise_2d(x, z)))
			var pl := 1.0 - smoothstep(0.85, 1.05, pd)
			var amp := hill_height * smoothstep(24.0, 110.0, r) * lerpf(1.0, 0.12, pl)
			var h := 0.15 + _n01(hills, x, z) * amp + detail.get_noise_2d(x, z) * 0.25 * smoothstep(20.0, 40.0, r)
			h += smoothstep(half - 30.0, half, m) * 9.0
			if has_centre and m < CENTRE_HALF:
				h = lerpf(h, _centre_height(x, z), 1.0 - smoothstep(16.0, CENTRE_HALF, m))
			var k := j * _n + i
			_h[k] = h
			_plains[k] = pl

	for river in _make_rivers(rng):
		_stamp_river(river)
	_place_ponds(rng)

	# Carve river channels and ponds, with a flat valley floor around them.
	for j in _n:
		var z := j - half
		for i in _n:
			var x := i - half
			var k := j * _n + i
			var keep := 0.0   # how much of the original demo terrain to keep untouched
			if has_centre:
				keep = 1.0 - smoothstep(16.0, CENTRE_HALF, maxf(absf(x), absf(z)))
			if keep >= 1.0:
				continue
			var h := _h[k]
			var c := h
			if _river_d[k] < _river_w[k] + 21.0:
				c = _carve(c, _river_d[k], _river_w[k], 18.0, 1.2)
			for p in _ponds:
				var d := Vector2(x - p.x, z - p.y).length()
				if d < p.z * 1.3 + 14.0:
					var wob := 1.0 + 0.18 * sin(atan2(z - p.y, x - p.x) * 3.0 + p.w) + 0.1 * sin(atan2(z - p.y, x - p.x) * 5.0 + p.w * 2.0)
					c = _carve(c, d / wob, p.z, 10.0, 1.6)
			_h[k] = lerpf(c, h, keep)

## Lowers the terrain into a channel of half width hw, with a 3 m bank and a valley that blends
## back into the hills.
func _carve(h: float, d: float, hw: float, valley: float, depth: float) -> float:
	var shore := water_level + 0.3
	var target: float
	if d < hw:
		var k := d / hw
		target = water_level - 0.15 - depth * (1.0 - k * k)
	elif d < hw + 3.0:
		target = lerpf(water_level - 0.15, shore, smoothstep(hw, hw + 3.0, d))
	else:
		target = lerpf(shore, maxf(h, shore), smoothstep(0.0, valley, d - hw - 3.0))
	return minf(h, target)

## Rivers as points (x, z, half width). The main river follows the original stream through the
## demo area and meanders to the north and south edges; two tributaries join it from east and west.
func _make_rivers(rng: RandomNumberGenerator) -> Array:
	var rivers := []
	var meander := _noise(random_seed + 10, 0.009, 2)
	var main := PackedVector3Array()
	var south_x := _creek_x(-CENTRE_HALF)
	var north_x := _creek_x(CENTRE_HALF)
	var z := -half - 12.0
	while z <= half + 12.0:
		if absf(z) <= CENTRE_HALF:
			main.append(Vector3(_creek_x(z), z, 1.0))
		else:
			var t := smoothstep(CENTRE_HALF, 80.0, absf(z))
			var anchor := south_x if z < 0.0 else north_x
			main.append(Vector3(anchor + meander.get_noise_1d(z) * 75.0 * t, z, lerpf(1.0, 4.5, t)))
		z += 2.0
	rivers.append(main)

	for side: float in [1.0, -1.0]:
		var z0 := rng.randf_range(70.0, 130.0) * side
		var join_x := 0.0
		var best := INF
		for p in main:
			if absf(p.y - z0) < best:
				best = absf(p.y - z0)
				join_x = p.x
		var trib := PackedVector3Array()
		var start := (half + 12.0) * side
		var x := start
		var wiggle := _noise(random_seed + 11 + int(side), 0.012, 2)
		while (x - join_x) * side >= 0.0:
			var t := smoothstep(0.0, 40.0, absf(x - join_x))
			trib.append(Vector3(x, z0 + wiggle.get_noise_1d(x) * 50.0 * t, lerpf(2.5, 3.5, absf(x - join_x) / absf(start - join_x))))
			x -= 2.0 * side
		rivers.append(trib)
	return rivers

func _stamp_river(points: PackedVector3Array) -> void:
	var reach := 26.0
	var i := 0
	while i < points.size() - 1:
		var j := mini(i + 3, points.size() - 1)   # 6 m segments
		var a := Vector2(points[i].x, points[i].y)
		var b := Vector2(points[j].x, points[j].y)
		var wa := points[i].z
		var wb := points[j].z
		var ab := b - a
		var len2 := maxf(ab.length_squared(), 0.0001)
		var x0 := clampi(int(floor(minf(a.x, b.x) - reach + half)), 0, _n - 1)
		var x1 := clampi(int(ceil(maxf(a.x, b.x) + reach + half)), 0, _n - 1)
		var z0 := clampi(int(floor(minf(a.y, b.y) - reach + half)), 0, _n - 1)
		var z1 := clampi(int(ceil(maxf(a.y, b.y) + reach + half)), 0, _n - 1)
		for gz in range(z0, z1 + 1):
			for gx in range(x0, x1 + 1):
				var p := Vector2(gx - half, gz - half)
				var t := clampf((p - a).dot(ab) / len2, 0.0, 1.0)
				var d := p.distance_to(a + ab * t)
				var k := gz * _n + gx
				if d < _river_d[k]:
					_river_d[k] = d
					_river_w[k] = lerpf(wa, wb, t)
		i = j

func _place_ponds(rng: RandomNumberGenerator) -> void:
	var candidates := []
	for attempt in 300:
		var x := rng.randf_range(-half + 40.0, half - 40.0)
		var z := rng.randf_range(-half + 40.0, half - 40.0)
		if Vector2(x, z).length() < 55.0:
			continue
		var k := _idx(x, z)
		if _river_d[k] < 35.0:
			continue
		candidates.append(Vector3(x, z, _h[k] + rng.randf() * 2.0))
	candidates.sort_custom(func(a: Vector3, b: Vector3) -> bool: return a.z < b.z)   # prefer low ground
	for c in candidates:
		if _ponds.size() >= pond_count:
			break
		var ok := true
		for p in _ponds:
			if Vector2(c.x - p.x, c.y - p.y).length() < 60.0:
				ok = false
				break
		if ok:
			_ponds.append(Vector4(c.x, c.y, rng.randf_range(6.0, 13.0), rng.randf() * TAU))

func _build_terrain() -> void:
	var terrain := Node3D.new()
	terrain.name = "Terrain"
	add_child(terrain)
	var water_root := Node3D.new()
	water_root.name = "Water"
	add_child(water_root)
	var plane := PlaneMesh.new()
	plane.size = Vector2(CHUNK, CHUNK)
	plane.subdivide_width = CHUNK >> 1
	plane.subdivide_depth = CHUNK >> 1
	var chunks := int((_n - 1) / float(CHUNK))
	var vn := CHUNK + 1
	for cz in chunks:
		for cx in chunks:
			var verts := PackedVector3Array()
			var normals := PackedVector3Array()
			var uvs := PackedVector2Array()
			var idx := PackedInt32Array()
			verts.resize(vn * vn)
			normals.resize(vn * vn)
			uvs.resize(vn * vn)
			var lowest := INF
			for j in vn:
				var gj := cz * CHUNK + j
				for i in vn:
					var gi := cx * CHUNK + i
					var y := _h[gj * _n + gi]
					var x := gi - half
					var z := gj - half
					var v := j * vn + i
					verts[v] = Vector3(x, y, z)
					normals[v] = _normal(gi, gj)
					uvs[v] = Vector2(x, z) / 44.0   # same 4 m texture tiling as the original ground
					lowest = minf(lowest, y)
			idx.resize(CHUNK * CHUNK * 6)
			var w := 0
			for j in CHUNK:
				for i in CHUNK:
					var a := j * vn + i
					idx[w] = a; idx[w + 1] = a + 1; idx[w + 2] = a + vn
					idx[w + 3] = a + 1; idx[w + 4] = a + vn + 1; idx[w + 5] = a + vn
					w += 6
			var arrays := []
			arrays.resize(Mesh.ARRAY_MAX)
			arrays[Mesh.ARRAY_VERTEX] = verts
			arrays[Mesh.ARRAY_NORMAL] = normals
			arrays[Mesh.ARRAY_TEX_UV] = uvs
			arrays[Mesh.ARRAY_INDEX] = idx
			var mesh := ArrayMesh.new()
			mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
			var mi := MeshInstance3D.new()
			mi.name = "Chunk_%d_%d" % [cx, cz]
			mi.mesh = mesh
			mi.material_override = ground_material
			terrain.add_child(mi)
			if lowest < water_level:
				var wm := MeshInstance3D.new()
				wm.name = "Water_%d_%d" % [cx, cz]
				wm.mesh = plane
				wm.material_override = water_material
				wm.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
				wm.position = Vector3(cx * CHUNK + CHUNK * 0.5 - half, water_level, cz * CHUNK + CHUNK * 0.5 - half)
				water_root.add_child(wm)

	var body := StaticBody3D.new()
	body.name = "TerrainCollision"
	add_child(body)
	var shape := HeightMapShape3D.new()
	shape.map_width = _n
	shape.map_depth = _n
	shape.map_data = _h
	var cs := CollisionShape3D.new()
	cs.shape = shape
	body.add_child(cs)

func _normal(i: int, j: int) -> Vector3:
	var l := _h[j * _n + maxi(i - 1, 0)]
	var r := _h[j * _n + mini(i + 1, _n - 1)]
	var d := _h[maxi(j - 1, 0) * _n + i]
	var u := _h[mini(j + 1, _n - 1) * _n + i]
	return Vector3(l - r, 2.0, d - u).normalized()

func _build_walls() -> void:
	var body := StaticBody3D.new()
	body.name = "Boundary"
	add_child(body)
	for s in [Vector3(1, 0, 0), Vector3(-1, 0, 0), Vector3(0, 0, 1), Vector3(0, 0, -1)]:
		var box := BoxShape3D.new()
		box.size = Vector3(1.0 if s.x != 0.0 else world_size, 60.0, 1.0 if s.z != 0.0 else world_size)
		var cs := CollisionShape3D.new()
		cs.shape = box
		cs.position = s * (half - 2.0) + Vector3(0, 20, 0)
		body.add_child(cs)

# ---------------------------------------------------------------- foliage and props

func _scatter(rng: RandomNumberGenerator) -> void:
	_collision = StaticBody3D.new()
	_collision.name = "PropCollision"
	add_child(_collision)
	var forest := _noise(random_seed + 20, 0.011, 3)
	var area := world_size * world_size

	# Trees on a jittered grid, dense in forests and sparse elsewhere. None in the plains.
	var g := 5.5
	var cells := int(world_size / g)
	for gz in cells:
		for gx in cells:
			var x := -half + (gx + rng.randf()) * g
			var z := -half + (gz + rng.randf()) * g
			var dens := (smoothstep(0.42, 0.68, _n01(forest, x, z)) * 0.9 + 0.05) * tree_density
			if rng.randf() > dens or not _land_ok(x, z, 4.0) or plains_at(x, z) > 0.05 or is_blocked(x, z, 1.5):
				continue
			var model := _pick(rng, TREES)
			var s := rng.randf_range(0.6, 0.8) if model.begins_with("Twisted") else rng.randf_range(0.85, 1.25)
			var t := _place(model, x, z, s, rng, 110.0)
			var info: Dictionary = _models[model]
			var trunk := (0.6 if model.begins_with("Twisted") else 0.35) * s
			_add_cylinder(t.origin, trunk, info.height * s * 0.7)
			_add_obstacle(x, z, trunk + 0.4)

	# Rocks
	for i in int(area / 450.0 * prop_density):
		var x := rng.randf_range(-half, half)
		var z := rng.randf_range(-half, half)
		if not _land_ok(x, z, 1.0) or plains_at(x, z) > 0.3 or is_blocked(x, z, 1.5):
			continue
		var s := rng.randf_range(0.7, 1.6)
		var model := _pick(rng, ROCKS)
		var t := _place(model, x, z, s, rng, 110.0)
		var info: Dictionary = _models[model]
		var box := BoxShape3D.new()
		box.size = info.size * s * 0.8
		var cs := CollisionShape3D.new()
		cs.shape = box
		cs.transform = Transform3D(t.basis.orthonormalized(), t * info.center)
		_collision.add_child(cs)
		_add_obstacle(x, z, maxf(info.size.x, info.size.z) * s * 0.42)

	# Bushes (no collision), mostly around forests
	for i in int(area / 140.0 * prop_density):
		var x := rng.randf_range(-half, half)
		var z := rng.randf_range(-half, half)
		if rng.randf() > 0.25 + 0.75 * _n01(forest, x, z) or not _land_ok(x, z, 1.5) or plains_at(x, z) > 0.2 or is_blocked(x, z, 0.6):
			continue
		_place(_pick(rng, BUSHES), x, z, rng.randf_range(0.8, 1.2), rng, 110.0)

	# Plants, ferns and mushrooms on the forest floor
	for i in int(area / 90.0 * prop_density):
		var x := rng.randf_range(-half, half)
		var z := rng.randf_range(-half, half)
		if rng.randf() > 0.15 + 0.85 * smoothstep(0.4, 0.7, _n01(forest, x, z)) or not _land_ok(x, z, 1.0) or plains_at(x, z) > 0.2 or is_blocked(x, z, 0.4):
			continue
		var model := _pick(rng, PLANTS)
		var s := rng.randf_range(0.42, 0.62)
		if model == "Fern_1":
			s = rng.randf_range(0.3, 0.45)
		elif model.begins_with("Plant_7"):
			s = rng.randf_range(0.8, 1.2)
		var t := _place(model, x, z, s, rng, 55.0)
		if model == "Plant_1_Big":
			_add_cylinder(t.origin, 1.2 * s, 2.0 * s)
			_add_obstacle(x, z, 1.2 * s)
	for i in int(area / 350.0 * prop_density):
		var x := rng.randf_range(-half, half)
		var z := rng.randf_range(-half, half)
		if _n01(forest, x, z) < 0.5 or not _land_ok(x, z, 1.0) or plains_at(x, z) > 0.2 or is_blocked(x, z, 0.3):
			continue
		_place(_pick(rng, SHROOMS), x, z, rng.randf_range(0.9, 1.2), rng, 55.0)

	# Pebbles, mostly along the water
	for i in int(area / 100.0 * prop_density):
		var x := rng.randf_range(-half, half)
		var z := rng.randf_range(-half, half)
		var by_water := near_water(x, z, 5.0)
		if rng.randf() > (0.8 if by_water else 0.12) or not _land_ok(x, z, 0.3) or is_blocked(x, z, 0.2):
			continue
		_place(_pick(rng, PEBBLES), x, z, rng.randf_range(0.8, 2.0), rng, 55.0)

	_apply_clearings()
	_build_multimeshes()

## Takes the props out of each clearing and marks it blocked, so the meadow leaves it bare too.
## Done after scattering, not by blocking it first, so the rest of the world comes out the same.
func _apply_clearings() -> void:
	for c in clearings:
		for key in _instances.keys():
			_instances[key] = _instances[key].filter(func(t: Transform3D) -> bool:
				return Vector2(t.origin.x - c.x, t.origin.z - c.y).length() > c.z)
			if _instances[key].is_empty():
				_instances.erase(key)
		_add_obstacle(c.x, c.y, c.z)

## True where props may go: outside the hand-made demo area, inside the map, above the water.
func _land_ok(x: float, z: float, water_margin: float) -> bool:
	var m := maxf(absf(x), absf(z))
	if m < CENTRE_HALF + 1.0 or m > half - 6.0:
		return false
	return not near_water(x, z, water_margin)

func _place(model: String, x: float, z: float, s: float, rng: RandomNumberGenerator, chunk: float) -> Transform3D:
	var info := _prepare(model)
	var t := Transform3D(Basis(Vector3.UP, rng.randf() * TAU).scaled(Vector3.ONE * s), Vector3(x, ground_height(x, z) - 0.03, z))
	if info.is_empty():
		return t
	var key := "%s|%d|%d|%d" % [model, int(floor((x + half) / chunk)), int(floor((z + half) / chunk)), int(chunk)]
	if not _instances.has(key):
		_instances[key] = []
	_instances[key].append(t * info.local)
	return t

func _add_cylinder(base: Vector3, radius: float, height: float) -> void:
	var cyl := CylinderShape3D.new()
	cyl.radius = radius
	cyl.height = height
	var cs := CollisionShape3D.new()
	cs.shape = cyl
	cs.position = base + Vector3(0, height * 0.5, 0)
	_collision.add_child(cs)

func _add_obstacle(x: float, z: float, r: float) -> void:
	for gx in range(int(floor((x - r) / CELL)), int(floor((x + r) / CELL)) + 1):
		for gz in range(int(floor((z - r) / CELL)), int(floor((z + r) / CELL)) + 1):
			var k := Vector2i(gx, gz)
			if not _obstacles.has(k):
				_obstacles[k] = []
			_obstacles[k].append(Vector3(x, z, r))

func _build_multimeshes() -> void:
	var root := Node3D.new()
	root.name = "Props"
	add_child(root)
	for key in _instances:
		var parts: PackedStringArray = key.split("|")
		var model := parts[0]
		var chunk := float(parts[3])
		var info: Dictionary = _models[model]
		var arr: Array = _instances[key]
		# Position each chunk at its centre so visibility range is measured from there.
		var centre := Vector3((int(parts[1]) + 0.5) * chunk - half, 0.0, (int(parts[2]) + 0.5) * chunk - half)
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = info.mesh
		mm.instance_count = arr.size()
		for j in arr.size():
			var t: Transform3D = arr[j]
			t.origin -= centre
			mm.set_instance_transform(j, t)
		var mmi := MultiMeshInstance3D.new()
		mmi.name = "%s_%s_%s" % [model, parts[1], parts[2]]
		mmi.multimesh = mm
		mmi.position = centre
		var big := chunk > 60.0
		mmi.visibility_range_end = tree_view_distance if big else small_view_distance
		mmi.visibility_range_end_margin = 10.0
		mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if big else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		root.add_child(mmi)

func _prepare(model: String) -> Dictionary:
	if _models.has(model):
		return _models[model]
	var ps := load("res://glTF/%s.gltf" % model) as PackedScene
	if ps == null:
		push_warning("World: could not load %s" % model)
		_models[model] = {}
		return {}
	var root := ps.instantiate()
	var found := root.find_children("*", "MeshInstance3D", true, false)
	if found.is_empty():
		root.free()
		_models[model] = {}
		return {}
	var mi := found[0] as MeshInstance3D
	var local := Transform3D.IDENTITY
	var n: Node = mi
	while n != root and n is Node3D:
		local = (n as Node3D).transform * local
		n = n.get_parent()
	if n == root and root is Node3D:
		local = (root as Node3D).transform * local
	var mesh := mi.mesh
	for s in mesh.get_surface_count():
		if mi.get_surface_override_material(s) != null:
			mesh = mesh.duplicate()
			for k in mesh.get_surface_count():
				mesh.surface_set_material(k, mi.get_active_material(k))
			break
	var aabb := local * mesh.get_aabb()
	root.free()
	_models[model] = {"mesh": mesh, "local": local, "height": maxf(aabb.end.y, 0.1),
			"size": aabb.size, "center": aabb.get_center()}
	return _models[model]

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

func _noise(s: int, f: float, octaves: int) -> FastNoiseLite:
	var n := FastNoiseLite.new()
	n.seed = s
	n.frequency = f
	n.fractal_octaves = octaves
	return n

func _n01(n: FastNoiseLite, x: float, z: float) -> float:
	return clampf(n.get_noise_2d(x, z) * 0.7 + 0.5, 0.0, 1.0)
