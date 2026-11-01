class_name Scatter
extends Node3D
## Deterministic, data driven scatter of foliage and trees (data/scatter.json + data/biomes.json).
## - Foliage: one MultiMeshInstance3D per plant per 64 m cell, no shadows. Trees: one per tree per 128 m cell.
## - persistent (default): every cell of the world is built once, nearest the view first and spread over frames,
##   and never unloaded or faded, so foliage is always visible (camera mode, other players far away). The old
##   streaming mode (build round the player, shrink out at the view distance) is kept behind persistent = false.
## - Cylinder trunk colliders only in the cells next to the local player (physics, not looks).
## - Fully client side and deterministic: same seed per cell and rule, so every client sees the same world and
##   nothing needs to be sent over the network.
## - Same seed per cell and rule, so the world looks the same every load.
## - Every plant and tree uses shaders/foliage_wind.gdshader (wind on the leaf cards, still trunks).

const FOLIAGE_CELL := 64.0
const TREE_CELL := 128.0

var world: Node
var data: WorldData
var rules: Array = []
var mesh_paths: Dictionary = {}
var base_meshes := {}          # alias -> {mesh, height}
var prepared := {}             # "rule|alias" -> ArrayMesh with wind materials
var spacing_words := {}
var foliage_view := 52.0
var tree_view := 240.0
var exclusions: Array = []     # [Vector2 centre, radius]
var foliage_cells := {}        # Vector2i -> Node3D
var tree_cells := {}
var collider_cells := {}
var player: Node3D
var focus: Node3D              # what the local view follows: the player, or the free camera
var persistent := true
var build_queue: Array = []    # [cell coord, cell size, trees?] still to build (persistent mode)
const BUILD_BUDGET_USEC := 6000
var patch_noise := FastNoiseLite.new()
var wind_shader: Shader


func setup(w: Node, d: WorldData) -> void:
	world = w
	data = d
	var js: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/scatter.json"))
	mesh_paths = js["meshes"]
	var biome_names: Array = WorldData.BIOMES
	for r in js["rules"]:
		var keep := false
		for b in r["biomes"]:
			if (d.fixed_biome >= 0 and b == biome_names[d.fixed_biome]) or (d.fixed_biome < 0 and b != "hub"):
				keep = true
		if keep:
			rules.append(r)
	spacing_words = d.biome_data["density_spacing"]
	foliage_view = d.biome_data["foliage_view_distance"]
	tree_view = d.biome_data["tree_view_distance"]
	patch_noise.seed = 4242
	patch_noise.noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	wind_shader = load("res://shaders/foliage_wind.gdshader")
	var radii: Dictionary = js.get("exclusion_radius", {})
	for key in d.layout.get("landmarks", {}):
		var p: Array = d.layout["landmarks"][key]
		exclusions.append([Vector2(p[0], p[1]), float(radii.get(key, 7.0)), key])
	if persistent:
		_queue_all(TREE_CELL, true)
		_queue_all(FOLIAGE_CELL, false)


func _queue_all(cell: float, trees: bool) -> void:
	var x0 := floori(data.origin.x / cell)
	var z0 := floori(data.origin.y / cell)
	var x1 := floori((data.origin.x + data.size.x) / cell)
	var z1 := floori((data.origin.y + data.size.y) / cell)
	for cz in range(z0, z1 + 1):
		for cx in range(x0, x1 + 1):
			if data.in_bounds((cx + 0.5) * cell, (cz + 0.5) * cell, -cell):
				build_queue.append([Vector2i(cx, cz), cell, trees])


func is_fully_built() -> bool:
	return build_queue.is_empty()


func set_player(p: Node3D) -> void:
	player = p


func set_focus(f: Node3D) -> void:
	focus = f


func _process(_delta: float) -> void:
	if player == null or data == null:
		return
	var p := player.global_position
	var view := (focus if is_instance_valid(focus) else player).global_position
	if persistent:
		_build_queued(view)
	else:
		_update_cells(view, FOLIAGE_CELL, foliage_view + FOLIAGE_CELL * 0.75, foliage_cells, false)
		_update_cells(view, TREE_CELL, tree_view + TREE_CELL * 0.5, tree_cells, true)
	# only the tree cells next to the view cast shadows (fewer draw calls in the shadow pass)
	var vc := Vector2i(floori(view.x / TREE_CELL), floori(view.z / TREE_CELL))
	for c in tree_cells:
		var near := absi(c.x - vc.x) <= 1 and absi(c.y - vc.y) <= 1
		for mmi in tree_cells[c].get_children():
			(mmi as GeometryInstance3D).cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if near else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	# trunk colliders round the local player only
	var pc := Vector2i(floori(p.x / TREE_CELL), floori(p.z / TREE_CELL))
	for c in collider_cells.keys():
		if absi(c.x - pc.x) > 1 or absi(c.y - pc.y) > 1:
			collider_cells[c].queue_free()
			collider_cells.erase(c)
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var c := pc + Vector2i(dx, dz)
			if not collider_cells.has(c):
				collider_cells[c] = _build_colliders(c)
				return


func _build_queued(view: Vector3) -> void:
	## Persistent mode: build queued cells nearest the view first, within a small time budget per frame
	## (at least one cell per frame), and keep them for the life of the world.
	if build_queue.is_empty():
		return
	var v := Vector2(view.x, view.z)
	build_queue.sort_custom(func(a, b):
		return Vector2((a[0].x + 0.5) * a[1], (a[0].y + 0.5) * a[1]).distance_squared_to(v) \
			< Vector2((b[0].x + 0.5) * b[1], (b[0].y + 0.5) * b[1]).distance_squared_to(v))
	var t0 := Time.get_ticks_usec()
	while not build_queue.is_empty():
		var job: Array = build_queue.pop_front()
		var store := tree_cells if job[2] else foliage_cells
		if not store.has(job[0]):
			store[job[0]] = _build_cell(job[0], job[1], job[2])
		if Time.get_ticks_usec() - t0 > BUILD_BUDGET_USEC:
			break


func _update_cells(p: Vector3, cell: float, radius: float, store: Dictionary, trees: bool) -> void:
	var pc := Vector2i(floori(p.x / cell), floori(p.z / cell))
	var r := int(ceil(radius / cell))
	var best := Vector2i(999999, 999999)
	var best_d := 1e12
	for dz in range(-r, r + 1):
		for dx in range(-r, r + 1):
			var c := pc + Vector2i(dx, dz)
			var centre := Vector2((c.x + 0.5) * cell, (c.y + 0.5) * cell)
			var d := centre.distance_to(Vector2(p.x, p.z))
			if d > radius or store.has(c):
				continue
			if not data.in_bounds(centre.x, centre.y, -cell):
				continue
			if d < best_d:
				best_d = d
				best = c
	if best_d < 1e11:
		store[best] = _build_cell(best, cell, trees)  # one new cell per frame keeps the frame time smooth
	for c in store.keys():
		var centre := Vector2((c.x + 0.5) * cell, (c.y + 0.5) * cell)
		if centre.distance_to(Vector2(p.x, p.z)) > radius + cell:
			store[c].queue_free()
			store.erase(c)


func _build_cell(c: Vector2i, cell: float, trees: bool) -> Node3D:
	var node := Node3D.new()
	node.name = "%s_%d_%d" % ["trees" if trees else "foliage", c.x, c.y]
	add_child(node)
	for ri in rules.size():
		var rule: Dictionary = rules[ri]
		if (rule.get("kind", "foliage") == "tree") != trees:
			continue
		var per_alias := _place(rule, ri, c, cell)
		for alias in per_alias:
			var xforms: Array = per_alias[alias]
			if xforms.is_empty():
				continue
			var mm := MultiMesh.new()
			mm.transform_format = MultiMesh.TRANSFORM_3D
			mm.mesh = _prepared_mesh(rule, alias)
			mm.instance_count = xforms.size()
			for i in xforms.size():
				mm.set_instance_transform(i, xforms[i])
			var mmi := MultiMeshInstance3D.new()
			mmi.name = "%s_%s" % [rule["id"], alias]
			mmi.multimesh = mm
			if not persistent:
				var view: float = rule.get("view", tree_view if trees else foliage_view)
				mmi.visibility_range_end = view + cell * 0.75
			mmi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_ON if trees else GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			node.add_child(mmi)
	return node


func _place(rule: Dictionary, ri: int, c: Vector2i, cell: float) -> Dictionary:
	## Jittered grid at the rule's spacing, filtered by biome, mask, slope, height and landmark rules.
	var spacing: float = rule.get("spacing", spacing_words.get(rule.get("density", "scattered"), 6.0))
	var n := int(ceil(cell / spacing))
	var rng := RandomNumberGenerator.new()
	rng.seed = hash([c.x, c.y, ri, int(rule.get("seed", 0))])
	var aliases: Array = rule["meshes"]
	var total := 0.0
	for a in aliases:
		total += float(a[1])
	var out := {}
	for a in aliases:
		out[a[0]] = []
	var sc: Array = rule.get("scale", [1.0, 1.0])
	var avoid: Array = rule.get("avoid", [])
	var req: Dictionary = rule.get("require", {})
	var biomes: Array = rule["biomes"]
	var trees: bool = rule.get("kind", "foliage") == "tree"
	for gz in n:
		for gx in n:
			var x := c.x * cell + (gx + rng.randf()) * spacing
			var z := c.y * cell + (gz + rng.randf()) * spacing
			var pick := rng.randf() * total
			var yaw := rng.randf() * TAU
			var s := rng.randf_range(sc[0], sc[1])
			var roll := rng.randf()
			if x >= c.x * cell + cell or z >= c.y * cell + cell:
				continue
			if not data.in_bounds(x, z, 2.0):
				continue
			if not biomes.has(WorldData.BIOMES[data.biome_pick(x, z, roll)]):
				continue
			var m := data.mask_at(x, z)
			if avoid.has("path") and m.r > float(rule.get("path_max", 0.2)): continue
			if avoid.has("wet") and m.g > 0.3: continue
			if avoid.has("special") and m.b > 0.25: continue
			var h := data.height(x, z)
			if avoid.has("steep") and data.normal(x, z).y < 0.8: continue
			if data.normal(x, z).y < 0.62: continue
			var wl := data.water_level(x, z)
			if h < wl + (0.35 if avoid.has("water") else 0.05): continue
			if req.has("litter") and m.a < float(req["litter"]): continue
			if req.has("wet") and m.g < float(req["wet"]): continue
			if req.has("special") and m.b < float(req["special"]): continue
			if req.has("near_path") and not _near_path(x, z, float(req["near_path"])): continue
			if rule.has("height") and (h < rule["height"][0] or h > rule["height"][1]): continue
			if rule.has("patch"):
				patch_noise.frequency = rule["patch"]["freq"]
				if patch_noise.get_noise_2d(x + ri * 97.0, z) * 0.5 + 0.5 > float(rule["patch"]["threshold"]) + 0.25: continue
			if rule.get("patch_mask", "") == "litter" and roll > 0.3 + m.a * 0.9: continue
			if rule.has("near"):
				var lm: Array = data.layout["landmarks"].get(rule["near"][0], [1e9, 1e9])
				if Vector2(x, z).distance_to(Vector2(lm[0], lm[1])) > float(rule["near"][1]): continue
			elif _excluded(x, z, float(rule.get("clear", 0.0)), trees, rule.get("exclude", {})): continue
			var alias: String = aliases[0][0]
			var acc := 0.0
			for a in aliases:
				acc += float(a[1])
				if pick <= acc:
					alias = a[0]
					break
			var basis := Basis(Vector3.UP, yaw).scaled(Vector3.ONE * s)
			out[alias].append(Transform3D(basis, Vector3(x, h - 0.06, z)))
	return out


func _excluded(x: float, z: float, extra: float, trees: bool, override: Dictionary = {}) -> bool:
	## override = per-rule {landmark: radius} replacing the global exclusion_radius (e.g. hub grass hugs the buildings).
	for e in exclusions:
		var r: float = float(override.get(e[2], e[1]))
		if trees:
			r = maxf(r, extra)
		if Vector2(x, z).distance_to(e[0]) < r:
			return true
	return false


func _near_path(x: float, z: float, r: float) -> bool:
	for k in 8:
		var a := k * TAU / 8.0
		if data.mask_at(x + cos(a) * r, z + sin(a) * r).r > 0.5:
			return true
	return false


func _build_colliders(c: Vector2i) -> Node3D:
	var body := StaticBody3D.new()
	body.name = "trunks_%d_%d" % [c.x, c.y]
	body.collision_layer = 4
	body.collision_mask = 0
	add_child(body)
	for ri in rules.size():
		var rule: Dictionary = rules[ri]
		if rule.get("kind", "foliage") != "tree":
			continue
		var per_alias := _place(rule, ri, c, TREE_CELL)
		for alias in per_alias:
			for xf in per_alias[alias]:
				var s: float = (xf as Transform3D).basis.get_scale().x
				var shape := CylinderShape3D.new()
				shape.radius = 0.32 * s
				shape.height = 4.0 * s
				var cs := CollisionShape3D.new()
				cs.shape = shape
				cs.position = xf.origin + Vector3(0, 2.0 * s, 0)
				body.add_child(cs)
	return body


func _base_mesh(alias: String) -> Dictionary:
	if base_meshes.has(alias):
		return base_meshes[alias]
	var scene: PackedScene = load(mesh_paths[alias])
	var inst := scene.instantiate()
	var mi := inst.find_children("*", "MeshInstance3D", true, false)[0] as MeshInstance3D
	var info := {"mesh": mi.mesh, "height": mi.mesh.get_aabb().end.y}
	inst.free()
	base_meshes[alias] = info
	return info


func _prepared_mesh(rule: Dictionary, alias: String) -> Mesh:
	var key := "%s|%s" % [rule["id"], alias]
	if prepared.has(key):
		return prepared[key]
	var info := _base_mesh(alias)
	var src: Mesh = info["mesh"]
	var mesh: Mesh = src.duplicate()
	var trees: bool = rule.get("kind", "foliage") == "tree"
	var wind: float = data.biome_data["biomes"][rule["biomes"][0]].get("wind", 0.6)
	for i in mesh.get_surface_count():
		var orig := src.surface_get_material(i) as BaseMaterial3D
		var card := orig != null and orig.cull_mode == BaseMaterial3D.CULL_DISABLED
		var mat := ShaderMaterial.new()
		mat.shader = wind_shader
		if orig:
			mat.set_shader_parameter("albedo_tex", orig.albedo_texture)
		mat.set_shader_parameter("sway_height", maxf(0.3, info["height"]))
		mat.set_shader_parameter("wind_strength", (0.45 if trees else 1.0) * wind if card else (0.08 * wind if not trees else 0.0))
		var view: float = rule.get("view", tree_view if trees else foliage_view)
		if persistent:  # always visible: no shrink-out at the view distance
			mat.set_shader_parameter("fade_start", 1.0e7)
			mat.set_shader_parameter("fade_end", 1.1e7)
		else:
			mat.set_shader_parameter("fade_start", view - 8.0 if not trees else view + 100.0)
			mat.set_shader_parameter("fade_end", view if not trees else view + 140.0)
		if rule.has("recolor") and card:
			mat.set_shader_parameter("recolor", 1.0)
			mat.set_shader_parameter("recolor_dark", Color(rule["recolor"][0]))
			mat.set_shader_parameter("recolor_light", Color(rule["recolor"][1]))
		if rule.has("petal"):
			mat.set_shader_parameter("petal", 1.0)
			mat.set_shader_parameter("petal_color", Color(rule["petal"]))
		if rule.has("tint"):
			mat.set_shader_parameter("tint", Color(rule["tint"]))
		if rule.has("trunk_tint") and not card:
			mat.set_shader_parameter("tint", Color(rule["trunk_tint"]))
		mesh.surface_set_material(i, mat)
	prepared[key] = mesh
	return mesh
