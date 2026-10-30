class_name TerrainWorld
extends Node3D
## Chunked heightmap terrain for the Compatibility renderer.
## - 64 x 64 m chunks with 2 m vertex spacing and smooth normals, built a few per frame around the player.
## - A HeightMapShape3D collider for the chunks next to the player.
## - A low detail far mesh (8 m spacing) of the whole world, hidden close to the camera, so distant peaks and
##   landmarks stay visible (fog hides most of it).
## - One Texture2DArray with the 28 ground textures (terrain_textures.md section 2) and the terrain shader.

signal chunk_built(coord: Vector2i)

const CHUNK := 64.0
const STEP := 2.0
const VERTS := 33  # CHUNK / STEP + 1

@export var data_prefix := "resource"
@export var fixed_biome := -1          # 0 = hub; -1 = biome from the warped depth map
@export var view_chunks := 4           # chunk radius kept visible (64 m each)
@export var build_per_frame := 2
@export var far_mesh := true

var data: WorldData
var material: ShaderMaterial
var far_material: ShaderMaterial
var chunks := {}                       # Vector2i -> MeshInstance3D
var colliders := {}                    # Vector2i -> StaticBody3D
var queue: Array[Vector2i] = []
var player: Node3D
var _layer_array: Texture2DArray


func setup() -> void:
	data = WorldData.new(data_prefix, fixed_biome)
	_layer_array = _build_layer_array()
	material = _make_material(0.0, 0.0)
	if far_mesh:
		far_material = _make_material(150.0, 1.2)
		_build_far_mesh()


func _build_layer_array() -> Texture2DArray:
	var images: Array[Image] = []
	for id in data.biome_data["layer_files"]:
		# imported as Image resources (no GPU texture, so no GPU readback when building the array)
		var img: Image = (load("res://assets/textures/terrain/%s.png" % id) as Image).duplicate()
		if img.is_compressed():
			img.decompress()
		img.clear_mipmaps()
		img.convert(Image.FORMAT_RGBA8)
		img.generate_mipmaps()
		images.append(img)
	var arr := Texture2DArray.new()
	arr.create_from_images(images)
	return arr


func _make_material(near_cut: float, drop: float) -> ShaderMaterial:
	var mat := ShaderMaterial.new()
	mat.shader = load("res://shaders/terrain.gdshader")
	mat.set_shader_parameter("layers", _layer_array)
	mat.set_shader_parameter("mask_map", ImageTexture.create_from_image(data.mask))
	mat.set_shader_parameter("mask_rect", Vector4(data.origin.x, data.origin.y, data.mask.get_width(), data.mask.get_height()))
	mat.set_shader_parameter("fixed_biome", fixed_biome)
	mat.set_shader_parameter("band_depth", data.band)
	mat.set_shader_parameter("blend_half", data.blend_half)
	mat.set_shader_parameter("near_cut", near_cut)
	mat.set_shader_parameter("far_drop", drop)
	var ints := {"r_base": "base", "r_patch": "patch", "r_litter": "litter", "r_steep": "steep", "r_mid": "mid",
		"r_high": "high", "r_wet": "wet", "r_special": "special", "r_path": "path"}
	var floats := {"patch_threshold": ["patch_threshold", 1.0], "steep_slope": ["steep_slope", 0.45],
		"mid_slope": ["mid_slope", 9.0], "high_y": ["high_y", 9999.0], "border_patch": ["border_patch", 0.0]}
	for u in ints:
		var arr := PackedInt32Array()
		for b in WorldData.BIOMES:
			arr.append(int(data.biome_data["biomes"][b]["terrain"].get(ints[u], -1)))
		mat.set_shader_parameter(u, arr)
	for u in floats:
		var arr := PackedFloat32Array()
		for b in WorldData.BIOMES:
			arr.append(float(data.biome_data["biomes"][b]["terrain"].get(floats[u][0], floats[u][1])))
		mat.set_shader_parameter(u, arr)
	return mat


func set_player(p: Node3D) -> void:
	player = p


func _process(_delta: float) -> void:
	if data == null or player == null:
		return
	var pc := Vector2i(floori((player.global_position.x - data.origin.x) / CHUNK), floori((player.global_position.z - data.origin.y) / CHUNK))
	var max_x := int(ceil(data.size.x / CHUNK))
	var max_z := int(ceil(data.size.y / CHUNK))
	# queue missing chunks, nearest first
	var want := {}
	for dz in range(-view_chunks, view_chunks + 1):
		for dx in range(-view_chunks, view_chunks + 1):
			var c := pc + Vector2i(dx, dz)
			if c.x < 0 or c.y < 0 or c.x >= max_x or c.y >= max_z:
				continue
			if dx * dx + dz * dz > (view_chunks + 0.5) * (view_chunks + 0.5):
				continue
			want[c] = true
			if not chunks.has(c) and not queue.has(c):
				queue.append(c)
	queue.sort_custom(func(a, b): return (a - pc).length_squared() < (b - pc).length_squared())
	var built := 0
	while not queue.is_empty() and built < build_per_frame:
		var c: Vector2i = queue.pop_front()
		if want.has(c) and not chunks.has(c):
			_build_chunk(c)
			built += 1
	# drop chunks that are far away
	for c in chunks.keys():
		if not want.has(c) and (c - pc).length() > view_chunks + 1.5:
			chunks[c].queue_free()
			chunks.erase(c)
	# colliders only next to the player
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var c := pc + Vector2i(dx, dz)
			if c.x >= 0 and c.y >= 0 and c.x < max_x and c.y < max_z and not colliders.has(c):
				_build_collider(c)
	for c in colliders.keys():
		if absi(c.x - pc.x) > 2 or absi(c.y - pc.y) > 2:
			colliders[c].queue_free()
			colliders.erase(c)


func build_now_around(pos: Vector3, radius_chunks := 1) -> void:
	## Build the chunks and colliders round a point straight away (used before placing the player).
	var pc := Vector2i(floori((pos.x - data.origin.x) / CHUNK), floori((pos.z - data.origin.y) / CHUNK))
	for dz in range(-radius_chunks, radius_chunks + 1):
		for dx in range(-radius_chunks, radius_chunks + 1):
			var c := pc + Vector2i(dx, dz)
			if c.x < 0 or c.y < 0 or c.x * CHUNK >= data.size.x or c.y * CHUNK >= data.size.y:
				continue
			if not chunks.has(c):
				_build_chunk(c)
			if not colliders.has(c):
				_build_collider(c)


func _build_chunk(c: Vector2i) -> void:
	var x0 := data.origin.x + c.x * CHUNK
	var z0 := data.origin.y + c.y * CHUNK
	var mesh := _grid_mesh(x0, z0, VERTS, STEP)
	var mi := MeshInstance3D.new()
	mi.name = "chunk_%d_%d" % [c.x, c.y]
	mi.mesh = mesh
	mi.material_override = material
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON
	add_child(mi)
	chunks[c] = mi
	chunk_built.emit(c)


func _grid_mesh(x0: float, z0: float, n: int, spacing: float) -> ArrayMesh:
	var verts := PackedVector3Array()
	var norms := PackedVector3Array()
	var uvs := PackedVector2Array()
	verts.resize(n * n)
	norms.resize(n * n)
	uvs.resize(n * n)
	for j in n:
		for i in n:
			var x := x0 + i * spacing
			var z := z0 + j * spacing
			var k := j * n + i
			verts[k] = Vector3(x, data.height(x, z), z)
			norms[k] = data.normal(x, z)
			uvs[k] = Vector2(data.depth(x, z), 0.0)
	var idx := PackedInt32Array()
	idx.resize((n - 1) * (n - 1) * 6)
	var t := 0
	for j in n - 1:
		for i in n - 1:
			var a := j * n + i
			idx[t] = a; idx[t + 1] = a + 1; idx[t + 2] = a + n
			idx[t + 3] = a + 1; idx[t + 4] = a + n + 1; idx[t + 5] = a + n
			t += 6
	var arrays := []
	arrays.resize(Mesh.ARRAY_MAX)
	arrays[Mesh.ARRAY_VERTEX] = verts
	arrays[Mesh.ARRAY_NORMAL] = norms
	arrays[Mesh.ARRAY_TEX_UV] = uvs
	arrays[Mesh.ARRAY_INDEX] = idx
	var mesh := ArrayMesh.new()
	mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
	return mesh


func _build_collider(c: Vector2i) -> void:
	var x0 := data.origin.x + c.x * CHUNK
	var z0 := data.origin.y + c.y * CHUNK
	var shape := HeightMapShape3D.new()
	shape.map_width = VERTS
	shape.map_depth = VERTS
	var hd := PackedFloat32Array()
	hd.resize(VERTS * VERTS)
	for j in VERTS:
		for i in VERTS:
			hd[j * VERTS + i] = data.height(x0 + i * STEP, z0 + j * STEP) / STEP
	shape.map_data = hd
	var body := StaticBody3D.new()
	body.name = "collider_%d_%d" % [c.x, c.y]
	body.collision_layer = 1
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	cs.shape = shape
	body.add_child(cs)
	add_child(body)
	# HeightMapShape3D is centred and has 1 unit spacing: scale it by the vertex spacing
	body.transform = Transform3D(Basis().scaled(Vector3(STEP, STEP, STEP)), Vector3(x0 + CHUNK / 2.0, 0, z0 + CHUNK / 2.0))
	colliders[c] = body


func _build_far_mesh() -> void:
	var spacing := 8.0
	var n_x := int(data.size.x / spacing) + 1
	var n_z := int(data.size.y / spacing) + 1
	# build as several strips so each stays under the 16 bit index friendly size
	var strip := 32
	var zi := 0
	while zi < n_z - 1:
		var rows: int = min(strip, n_z - 1 - zi) + 1
		var verts := PackedVector3Array()
		var norms := PackedVector3Array()
		var uvs := PackedVector2Array()
		for j in rows:
			for i in n_x:
				var x := data.origin.x + i * spacing
				var z := data.origin.y + (zi + j) * spacing
				verts.append(Vector3(x, data.height(x, z), z))
				norms.append(data.normal(x, z))
				uvs.append(Vector2(data.depth(x, z), 0))
		var idx := PackedInt32Array()
		for j in rows - 1:
			for i in n_x - 1:
				var a := j * n_x + i
				idx.append_array([a, a + 1, a + n_x, a + 1, a + n_x + 1, a + n_x])
		var arrays := []
		arrays.resize(Mesh.ARRAY_MAX)
		arrays[Mesh.ARRAY_VERTEX] = verts
		arrays[Mesh.ARRAY_NORMAL] = norms
		arrays[Mesh.ARRAY_TEX_UV] = uvs
		arrays[Mesh.ARRAY_INDEX] = idx
		var mesh := ArrayMesh.new()
		mesh.add_surface_from_arrays(Mesh.PRIMITIVE_TRIANGLES, arrays)
		var mi := MeshInstance3D.new()
		mi.name = "far_terrain_%d" % zi
		mi.mesh = mesh
		mi.material_override = far_material
		mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		add_child(mi)
		zi += rows - 1
