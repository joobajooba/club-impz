class_name TerrainWorld
extends Node3D
## Chunked heightmap terrain for the Compatibility renderer.
## - 64 x 64 m chunks with 2 m vertex spacing and smooth normals, built a few per frame nearest the view first
##   (the player, or the free camera). With keep_loaded every chunk of the world is built and kept.
## - A HeightMapShape3D collider for the chunks next to the local player.
## - A low detail far mesh (8 m spacing) of the whole world, hidden close to the camera, so distant peaks and
##   landmarks stay visible (fog hides most of it).
## - One Texture2DArray with the 31 ground textures (terrain_textures.md section 2) and the terrain shader.
## - Worlds with a skirt (the resource world): one ring of detailed chunks outside the border (the cliff face, with
##   colliders) and the far mesh stretched over the mountains beyond, so the world ends in cliffs, not a drop.
##   Tall invisible walls stand just behind the cliff tops in case anything gets up there.

signal chunk_built(coord: Vector2i)

const CHUNK := 64.0
const STEP := 2.0
const VERTS := 33  # CHUNK / STEP + 1

@export var data_prefix := "resource"
@export var fixed_biome := -1          # 0 = hub; -1 = biome from the warped depth map
@export var view_chunks := 4           # chunk radius kept visible (64 m each)
@export var build_per_frame := 2
@export var far_mesh := true
@export var keep_loaded := true        # build the whole world once and never drop chunks (always visible)

var data: WorldData
var material: ShaderMaterial
var far_material: ShaderMaterial
var chunks := {}                       # Vector2i -> MeshInstance3D
var colliders := {}                    # Vector2i -> StaticBody3D
var queue: Array[Vector2i] = []
var player: Node3D
var focus: Node3D                      # what the local view follows (player or free camera)
var _layer_array: Texture2DArray
var margin := 0                        # chunks built outside the border on each side (1 with a skirt)
const WALL_OUT := 34.0                 # the safety walls stand this far outside the border (past the cliff tops)


func _chunk_rect() -> Rect2i:
	## Chunk coordinates that exist: the world, plus `margin` chunks round it.
	var max_x := int(ceil(data.size.x / CHUNK))
	var max_z := int(ceil(data.size.y / CHUNK))
	return Rect2i(-margin, -margin, max_x + 2 * margin, max_z + 2 * margin)


func setup() -> void:
	data = WorldData.new(data_prefix, fixed_biome)
	margin = 1 if data.has_skirt else 0
	_layer_array = _build_layer_array()
	material = _make_material(0.0, 0.0)
	if far_mesh:
		far_material = _make_material(150.0, 1.2)
		_build_far_mesh()
	_build_walls()


func _build_walls() -> void:
	## Four tall invisible walls round the world: behind the skirt's cliff tops, or on the border without a skirt.
	var out := WALL_OUT if data.has_skirt else 0.0
	var body := StaticBody3D.new()
	body.name = "world_walls"
	body.collision_layer = 1
	body.collision_mask = 0
	var cx := data.origin.x + data.size.x / 2.0
	var cz := data.origin.y + data.size.y / 2.0
	var w := data.size.x + 2.0 * out
	var d := data.size.y + 2.0 * out
	for side in [[Vector3(w + 20.0, 2000.0, 10.0), Vector3(cx, 0.0, cz - d / 2.0 - 5.0)],
			[Vector3(w + 20.0, 2000.0, 10.0), Vector3(cx, 0.0, cz + d / 2.0 + 5.0)],
			[Vector3(10.0, 2000.0, d + 20.0), Vector3(cx - w / 2.0 - 5.0, 0.0, cz)],
			[Vector3(10.0, 2000.0, d + 20.0), Vector3(cx + w / 2.0 + 5.0, 0.0, cz)]]:
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = side[0]
		cs.shape = box
		cs.position = side[1]
		body.add_child(cs)
	add_child(body)


func _build_layer_array() -> Texture2DArray:
	var images: Array[Image] = []
	var size := 0
	for id in data.biome_data["layer_files"]:
		# imported as Image resources (no GPU texture, so no GPU readback when building the array)
		var img: Image = (load("res://assets/textures/terrain/%s.png" % id) as Image).duplicate()
		if img.is_compressed():
			img.decompress()
		img.clear_mipmaps()
		img.convert(Image.FORMAT_RGBA8)
		size = maxi(size, img.get_width())
		images.append(img)
	# Layers may differ in size (hub_cobblestone is 256 px, 64 px per metre; the rest 128): the array needs one
	# size, so smaller layers are scaled up with nearest filtering, which keeps their pixels exactly as they were.
	for img in images:
		if img.get_width() != size:
			img.resize(size, size, Image.INTERPOLATE_NEAREST)
		img.generate_mipmaps()
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
	var m := margin * CHUNK
	mat.set_shader_parameter("detail_rect", Vector4(data.origin.x - m, data.origin.y - m, data.origin.x + data.size.x + m,
		data.origin.y + data.size.y + m))
	var ints := {"r_base": "base", "r_patch": "patch", "r_litter": "litter", "r_steep": "steep", "r_mid": "mid",
		"r_high": "high", "r_wet": "wet", "r_special": "special", "r_path": "path", "r_cliff": "cliff", "r_cap": "cap"}
	var floats := {"patch_threshold": ["patch_threshold", 1.0], "steep_slope": ["steep_slope", 0.45],
		"mid_slope": ["mid_slope", 9.0], "high_y": ["high_y", 9999.0], "border_patch": ["border_patch", 0.0],
		"special_on_steep": ["special_on_steep", 0.0], "cap_y": ["cap_y", 9999.0]}
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


func set_focus(f: Node3D) -> void:
	focus = f


func _process(_delta: float) -> void:
	if data == null or player == null:
		return
	var view := (focus if is_instance_valid(focus) else player).global_position
	var vc := Vector2i(floori((view.x - data.origin.x) / CHUNK), floori((view.z - data.origin.y) / CHUNK))
	var pc := Vector2i(floori((player.global_position.x - data.origin.x) / CHUNK), floori((player.global_position.z - data.origin.y) / CHUNK))
	var rect := _chunk_rect()
	# queue missing chunks, nearest the view first
	var want := {}
	var r := maxi(rect.size.x, rect.size.y) if keep_loaded else view_chunks
	for dz in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var c := vc + Vector2i(dx, dz)
			if not rect.has_point(c):
				continue
			if not keep_loaded and dx * dx + dz * dz > (view_chunks + 0.5) * (view_chunks + 0.5):
				continue
			want[c] = true
			if not chunks.has(c) and not queue.has(c):
				queue.append(c)
	queue.sort_custom(func(a, b): return (a - vc).length_squared() < (b - vc).length_squared())
	var built := 0
	while not queue.is_empty() and built < build_per_frame:
		var c: Vector2i = queue.pop_front()
		if want.has(c) and not chunks.has(c):
			_build_chunk(c)
			built += 1
	# drop chunks that are far away
	for c in chunks.keys():
		if not keep_loaded and not want.has(c) and (c - vc).length() > view_chunks + 1.5:
			chunks[c].queue_free()
			chunks.erase(c)
	# colliders only next to the player
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var c := pc + Vector2i(dx, dz)
			if rect.has_point(c) and not colliders.has(c):
				_build_collider(c)
	for c in colliders.keys():
		if absi(c.x - pc.x) > 2 or absi(c.y - pc.y) > 2:
			colliders[c].queue_free()
			colliders.erase(c)


## Loading screen (main.gd): every chunk this world shows from `pos` (all of them with keep_loaded),
## nearest first.
func load_list(pos: Vector3) -> Array[Vector2i]:
	var pc := Vector2i(floori((pos.x - data.origin.x) / CHUNK), floori((pos.z - data.origin.y) / CHUNK))
	var rect := _chunk_rect()
	var out: Array[Vector2i] = []
	for z in range(rect.position.y, rect.end.y):
		for x in range(rect.position.x, rect.end.x):
			var c := Vector2i(x, z)
			if keep_loaded or (c - pc).length_squared() <= (view_chunks + 0.5) * (view_chunks + 0.5):
				out.append(c)
	out.sort_custom(func(a, b): return (a - pc).length_squared() < (b - pc).length_squared())
	return out


## Builds chunks of `list` that are missing until `budget_usec` is spent. Returns how many are built.
func load_some(list: Array[Vector2i], budget_usec: int) -> int:
	var t0 := Time.get_ticks_usec()
	var done := 0
	for c in list:
		if not chunks.has(c):
			if Time.get_ticks_usec() - t0 > budget_usec:
				continue
			_build_chunk(c)
		done += 1
	return done


func build_now_around(pos: Vector3, radius_chunks := 1) -> void:
	## Build the chunks and colliders round a point straight away (used before placing the player).
	var pc := Vector2i(floori((pos.x - data.origin.x) / CHUNK), floori((pos.z - data.origin.y) / CHUNK))
	for dz in range(-radius_chunks, radius_chunks + 1):
		for dx in range(-radius_chunks, radius_chunks + 1):
			var c := pc + Vector2i(dx, dz)
			if not _chunk_rect().has_point(c):
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
	mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF  # terrain only receives shadows (fewer draw calls)
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
	# heights with a one vertex border, so normals come from neighbouring heights (one lookup per point, not five)
	var m := n + 2
	var hs := PackedFloat32Array()
	hs.resize(m * m)
	for j in m:
		for i in m:
			hs[j * m + i] = data.height(x0 + (i - 1) * spacing, z0 + (j - 1) * spacing)
	for j in n:
		for i in n:
			var x := x0 + i * spacing
			var z := z0 + j * spacing
			var k := j * n + i
			var q := (j + 1) * m + i + 1
			verts[k] = Vector3(x, hs[q], z)
			norms[k] = Vector3(hs[q - 1] - hs[q + 1], 2.0 * spacing, hs[q - m] - hs[q + m]).normalized()
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


func _far_h(x: float, z: float) -> float:
	## Far mesh heights on its 8 m lattice: the world's own grid inside, the raw skirt samples outside.
	if data.has_skirt and not data.in_bounds(x, z):
		return data.skirt_sample(roundi((x - data.sk_origin.x) / data.sk_step), roundi((z - data.sk_origin.y) / data.sk_step))
	return data.height(x, z)


func _build_far_mesh() -> void:
	var spacing := 8.0
	var o := data.origin
	var sz := data.size
	if data.has_skirt:  # cover the whole skirt (the mountains round the world)
		o = data.sk_origin
		sz = Vector2(data.sk_nx - 1, data.sk_nz - 1) * data.sk_step
	var n_x := int(sz.x / spacing) + 1
	var n_z := int(sz.y / spacing) + 1
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
				var x := o.x + i * spacing
				var z := o.y + (zi + j) * spacing
				var h := _far_h(x, z)
				verts.append(Vector3(x, h, z))
				norms.append(Vector3(_far_h(x - spacing, z) - _far_h(x + spacing, z), 2.0 * spacing,
					_far_h(x, z - spacing) - _far_h(x, z + spacing)).normalized())
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
