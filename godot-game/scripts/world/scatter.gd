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
## - Trees can be chopped down (lumbering.gd, tree_chopper.gd): a felled tree's instance is shrunk away,
##   its trunk collider is switched off and its stump stands in its place until it grows back.

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
var tree_places := {}         # Vector3i(cell x, cell z, rule) -> _place result of a built tree cell
var queued_total := 0          # cells queued at the start (for the loading screen's bar)
var patch_noise := FastNoiseLite.new()
var wind_shader: Shader
var trunk_shapes := {}         # tree key -> its trunk CollisionShape3D (cells next to the player only)
var stumps := {}               # tree key -> stump Node3D
var stump_scenes := {}         # stump name -> PackedScene


## z of the waterfall ribbon's centre line (game_world.gd _make_waterfall); no scatter inside its footprint.
var fall_z := 1e9


func setup(w: Node, d: WorldData) -> void:
	fall_z = float(d.layout.get("waterfall", {}).get("z", 1e9))
	world = w
	data = d
	add_to_group("scatter")
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
	_regrow_due()
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
			for key in collider_cells[c].get_meta("keys", []):
				trunk_shapes.erase(key)
			collider_cells[c].queue_free()
			collider_cells.erase(c)
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var c := pc + Vector2i(dx, dz)
			if not collider_cells.has(c):
				collider_cells[c] = _build_colliders(c)
				return


## Loading screen (main.gd): builds queued cells, and the trunk colliders round the player, until
## `budget_usec` is spent. Returns the share of the world built (0 to 1).
func load_some(budget_usec: int) -> float:
	if queued_total == 0:
		queued_total = maxi(build_queue.size(), 1)
	var view := player.global_position if player else Vector3.ZERO
	_build_queued(view, budget_usec)
	if build_queue.is_empty() and player:
		var pc := Vector2i(floori(view.x / TREE_CELL), floori(view.z / TREE_CELL))
		for dz in range(-1, 2):
			for dx in range(-1, 2):
				var c := pc + Vector2i(dx, dz)
				if not collider_cells.has(c):
					collider_cells[c] = _build_colliders(c)
	return 1.0 - float(build_queue.size()) / queued_total


func _build_queued(view: Vector3, budget_usec := BUILD_BUDGET_USEC) -> void:
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
		if Time.get_ticks_usec() - t0 > budget_usec:
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
		if trees:
			tree_places[Vector3i(c.x, c.y, ri)] = per_alias   # the trunk colliders reuse it
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
			if trees:
				mmi.set_meta("rule", ri)
				mmi.set_meta("alias", alias)
				mmi.set_meta("cell", c)
				mmi.set_meta("xforms", xforms)
				for i in xforms.size():
					var key := tree_key(rule, alias, c, i)
					if Lumbering.is_felled(key):
						mm.set_instance_transform(i, _hidden(xforms[i]))
						_add_stump(key, rule, alias, xforms[i])
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
	if not _cell_biomes(c, cell).has(rule["biomes"]):
		return out                     # none of the rule's biomes reach this cell: every spot would fail
	var sc: Array = rule.get("scale", [1.0, 1.0])
	var avoid: Array = rule.get("avoid", [])
	var req: Dictionary = rule.get("require", {})
	var biomes: Array = rule["biomes"]
	var trees: bool = rule.get("kind", "foliage") == "tree"
	# Everything that is the same for every spot, looked up once (this loop builds the whole world).
	var x_end := c.x * cell + cell
	var z_end := c.y * cell + cell
	var no_path := avoid.has("path")
	var path_max := float(rule.get("path_max", 0.2))
	var no_wet := avoid.has("wet")
	var no_special := avoid.has("special")
	var no_steep := avoid.has("steep")
	var water_gap := 0.35 if avoid.has("water") else 0.05
	var need_litter := float(req.get("litter", -1.0))
	var need_wet := float(req.get("wet", -1.0))
	var need_special := float(req.get("special", -1.0))
	var near_path := float(req.get("near_path", -1.0))
	var h_range: Array = rule.get("height", [])
	var patch: Dictionary = rule.get("patch", {})
	var patch_cut := float(patch.get("threshold", 0.0)) + 0.25
	if not patch.is_empty():
		patch_noise.frequency = patch["freq"]
	var litter_mask: bool = rule.get("patch_mask", "") == "litter"
	var near_lm := Vector2(1e9, 1e9)
	var near_r := -1.0
	var near_min := -1.0
	if rule.has("near"):
		var lm: Array = data.layout["landmarks"].get(rule["near"][0], [1e9, 1e9])
		near_lm = Vector2(lm[0], lm[1])
		near_r = float(rule["near"][1])
		near_min = float(rule["near"][2]) if rule["near"].size() > 2 else -1.0   # a ring: [landmark, max, min]
	var waters := _cell_waters(c, cell)
	var clears := [] if rule.has("near") else _cell_exclusions(c, cell, float(rule.get("clear", 0.0)), trees, rule.get("exclude", {}))
	for gz in n:
		for gx in n:
			var x := c.x * cell + (gx + rng.randf()) * spacing
			var z := c.y * cell + (gz + rng.randf()) * spacing
			var pick := rng.randf() * total
			var yaw := rng.randf() * TAU
			var s := rng.randf_range(sc[0], sc[1])
			var roll := rng.randf()
			if x >= x_end or z >= z_end:
				continue
			if not data.in_bounds(x, z, 2.0):
				continue
			if not biomes.has(WorldData.BIOMES[data.biome_pick(x, z, roll)]):
				continue
			var m := data.mask_at(x, z)
			if no_path and m.r > path_max: continue
			if no_wet and m.g > 0.3: continue
			if no_special and m.b > 0.25: continue
			var h := data.height(x, z)
			var up := data.normal(x, z).y
			if no_steep and up < 0.8: continue
			if up < 0.62: continue
			var wl := -1000.0
			for w in waters:
				if x >= w[0] and x <= w[2] and z >= w[1] and z <= w[3]:
					wl = maxf(wl, w[4])
			if h < wl + water_gap: continue
			if need_litter >= 0.0 and m.a < need_litter: continue
			if need_wet >= 0.0 and m.g < need_wet: continue
			if need_special >= 0.0 and m.b < need_special: continue
			if near_path >= 0.0 and not _near_path(x, z, near_path): continue
			if not h_range.is_empty() and (h < h_range[0] or h > h_range[1]): continue
			if not patch.is_empty() and patch_noise.get_noise_2d(x + ri * 97.0, z) * 0.5 + 0.5 > patch_cut: continue
			if litter_mask and roll > 0.3 + m.a * 0.9: continue
			if absf(z - fall_z) <= 5.5 and x >= 200.0 and x <= 218.0: continue  # nothing pokes through the waterfall
			if near_r >= 0.0:
				var dl := Vector2(x, z).distance_to(near_lm)
				if dl > near_r or dl < near_min: continue
			elif _in_clearing(clears, x, z): continue
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


## The biome names that can come up anywhere in a cell (biome_pick), as a set with a has(Array) test.
## Found from the warped depth on a coarse grid, widened by the border blend and a safety margin, so a
## skipped rule is one that could not have placed anything there: the world is the same, built faster.
var _biome_sets := {}

class BiomeSet:
	var names := {}
	func has(biomes: Array) -> bool:
		for b in biomes:
			if names.has(b):
				return true
		return false


func _cell_biomes(c: Vector2i, cell: float) -> BiomeSet:
	var key := Vector3i(c.x, c.y, int(cell))
	if _biome_sets.has(key):
		return _biome_sets[key]
	var bs := BiomeSet.new()
	if data.fixed_biome >= 0:
		bs.names[WorldData.BIOMES[data.fixed_biome]] = true
	else:
		var lo := 1e9
		var hi := -1e9
		var n := int(cell / 8.0)
		for j in n + 1:
			for i in n + 1:
				var d := data.depth(c.x * cell + cell * i / n, c.y * cell + cell * j / n)
				lo = minf(lo, d)
				hi = maxf(hi, d)
		var margin: float = data.blend_half + 16.0
		var i0 := clampi(int(floor((lo - margin) / data.band)), 0, 4)
		var i1 := clampi(int(floor((hi + margin) / data.band)), 0, 4)
		for i in range(i0, i1 + 1):
			bs.names[WorldData.BIOMES[i + 1]] = true
	_biome_sets[key] = bs
	return bs


## The water planes over a cell: [x0, z0, x1, z1, level] (WorldData.water_level, for this cell only).
func _cell_waters(c: Vector2i, cell: float) -> Array:
	var out := []
	for w in data.layout.get("water", []):
		var r: Array = w["rect"]
		if r[2] >= c.x * cell and r[0] <= c.x * cell + cell and r[3] >= c.y * cell and r[1] <= c.y * cell + cell:
			out.append([r[0], r[1], r[2], r[3], float(w["level"])])
	return out


## The landmark clearings (_excluded) that reach into a cell: [centre, radius].
func _cell_exclusions(c: Vector2i, cell: float, extra: float, trees: bool, override: Dictionary) -> Array:
	var out := []
	var rect := Rect2(c.x * cell, c.y * cell, cell, cell)
	for e in exclusions:
		var r: float = float(override.get(e[2], e[1]))
		if trees:
			r = maxf(r, extra)
		var p: Vector2 = e[0]
		var nearest := Vector2(clampf(p.x, rect.position.x, rect.end.x), clampf(p.y, rect.position.y, rect.end.y))
		if nearest.distance_to(p) < r + 1.0:
			out.append([p, r])
	return out


static func _in_clearing(clears: Array, x: float, z: float) -> bool:
	for e in clears:
		if Vector2(x, z).distance_to(e[0]) < e[1]:
			return true
	return false
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
	var keys := []
	for ri in rules.size():
		var rule: Dictionary = rules[ri]
		if rule.get("kind", "foliage") != "tree":
			continue
		var k := Vector3i(c.x, c.y, ri)
		var per_alias: Dictionary = tree_places[k] if tree_places.has(k) else _place(rule, ri, c, TREE_CELL)
		var sizes: Dictionary = rule.get("collider", {})   # alias -> [radius, height] in metres (rocks)
		for alias in per_alias:
			if not sizes.is_empty() and not sizes.has(alias):
				continue                                 # small rocks: walk over them
			for i in per_alias[alias].size():
				var xf: Transform3D = per_alias[alias][i]
				var key := tree_key(rule, alias, c, i)
				var s: float = xf.basis.get_scale().x
				var shape := CylinderShape3D.new()
				shape.radius = (float(sizes[alias][0]) if sizes.has(alias) else 0.32) * s
				shape.height = (float(sizes[alias][1]) if sizes.has(alias) else 4.0) * s
				var cs := CollisionShape3D.new()
				cs.shape = shape
				cs.position = xf.origin + Vector3(0, shape.height / 2.0, 0)
				cs.disabled = Lumbering.is_felled(key)
				body.add_child(cs)
				trunk_shapes[key] = cs
				keys.append(key)
	body.set_meta("keys", keys)
	return body


func _base_mesh(alias: String) -> Dictionary:
	if base_meshes.has(alias):
		return base_meshes[alias]
	var scene: PackedScene = load(mesh_paths[alias])
	var inst := scene.instantiate() as Node3D
	var found := inst.find_children("*", "MeshInstance3D", true, false)
	var mesh: Mesh = (found[0] as MeshInstance3D).mesh
	if found.size() > 1:                       # one mesh per cube (the rocks): merge them, one surface per material
		var tools := {}                        # material -> SurfaceTool
		for m: MeshInstance3D in found:
			var xf := _local_xf(inst, m)
			for si in m.mesh.get_surface_count():
				var mat := m.get_active_material(si)
				if not tools.has(mat):
					tools[mat] = SurfaceTool.new()
					(tools[mat] as SurfaceTool).begin(Mesh.PRIMITIVE_TRIANGLES)
					(tools[mat] as SurfaceTool).set_material(mat)
				(tools[mat] as SurfaceTool).append_from(m.mesh, si, xf)
		var merged := ArrayMesh.new()
		for mat in tools:
			merged = (tools[mat] as SurfaceTool).commit(merged)
		mesh = merged
	var info := {"mesh": mesh, "height": mesh.get_aabb().end.y}
	inst.free()
	base_meshes[alias] = info
	return info


static func _local_xf(root: Node3D, n: Node3D) -> Transform3D:
	var xf := n.transform
	var p := n.get_parent()
	while p != null and p != root:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


func _prepared_mesh(rule: Dictionary, alias: String) -> Mesh:
	var key := "%s|%s" % [rule["id"], alias]
	if prepared.has(key):
		return prepared[key]
	var info := _base_mesh(alias)
	var src: Mesh = info["mesh"]
	var mesh: Mesh = src.duplicate()
	var trees: bool = rule.get("kind", "foliage") == "tree"
	var wind: float = data.biome_data["biomes"][rule["biomes"][0]].get("wind", 0.6)
	if rule.get("still", false):              # rocks: no wind, a plain material (hard alpha for their grass cards)
		for i in mesh.get_surface_count():
			var orig := src.surface_get_material(i) as BaseMaterial3D
			var mat := StandardMaterial3D.new()
			if orig:
				mat.albedo_texture = orig.albedo_texture
			mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
			mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
			mat.alpha_scissor_threshold = 0.5
			mat.cull_mode = BaseMaterial3D.CULL_DISABLED
			mat.roughness = 1.0
			mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
			mesh.surface_set_material(i, mat)
		prepared[key] = mesh
		return mesh
	for i in mesh.get_surface_count():
		var orig := src.surface_get_material(i) as BaseMaterial3D
		var card := orig != null and orig.cull_mode == BaseMaterial3D.CULL_DISABLED
		var mat := ShaderMaterial.new()
		mat.shader = wind_shader
		if orig:
			mat.set_shader_parameter("albedo_tex", orig.albedo_texture)
		mat.set_shader_parameter("sway_height", maxf(0.3, info["height"]))
		mat.set_shader_parameter("wind_strength", 0.0 if rule.get("still", false) else
			((0.45 if trees else 1.0) * wind if card else (0.08 * wind if not trees else 0.0)))
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


# --- chopping (lumbering.gd, tree_chopper.gd) ---------------------------------------------------------------

## A tree's id for chopping: the same on every load (same rule, mesh, cell and index in the cell).
static func tree_key(rule: Dictionary, alias: String, c: Vector2i, i: int) -> String:
	return "%s|%s|%d|%d|%d" % [rule["id"], alias, c.x, c.y, i]


static func _hidden(xf: Transform3D) -> Transform3D:
	return Transform3D(Basis.from_scale(Vector3.ONE * 0.0001), xf.origin)


## The nearest standing tree that can be chopped, whose bark is within `reach` metres of `pos`, or {}.
## {key, tree, rule, alias, mmi, index, xform, scale, trunk (bark radius in metres)}
func find_tree(pos: Vector3, reach: float) -> Dictionary:
	var best := {}
	var best_d := reach
	var pc := Vector2i(floori(pos.x / TREE_CELL), floori(pos.z / TREE_CELL))
	for dz in range(-1, 2):
		for dx in range(-1, 2):
			var cell_node: Node3D = tree_cells.get(pc + Vector2i(dx, dz))
			if cell_node == null:
				continue
			for mmi in cell_node.get_children():
				if not mmi.has_meta("rule"):
					continue
				var rule: Dictionary = rules[int(mmi.get_meta("rule"))]
				var alias: String = mmi.get_meta("alias")
				var tree := Lumbering.tree_for(rule["id"], alias)
				if tree == "" or not Lumbering.MESHES.has(alias):
					continue
				var xforms: Array = mmi.get_meta("xforms")
				for i in xforms.size():
					var xf: Transform3D = xforms[i]
					var s := xf.basis.get_scale().x
					var trunk: float = Lumbering.MESHES[alias].trunk * Lumbering.UNITS * s
					var d := Vector2(xf.origin.x - pos.x, xf.origin.z - pos.z).length() - trunk
					if d >= best_d or absf(xf.origin.y - pos.y) > 2.5:
						continue
					var key := tree_key(rule, alias, mmi.get_meta("cell"), i)
					if Lumbering.is_felled(key):
						continue
					best_d = d
					best = {key = key, tree = tree, rule = rule, alias = alias, mmi = mmi, index = i, xform = xf,
						scale = s, trunk = trunk}
	return best


## Swaps the tree's MultiMesh instance for a node of its own, so it can shake and fall. Returns the node.
func lift_tree(t: Dictionary) -> Node3D:
	var mi := MeshInstance3D.new()
	mi.name = "tree_" + String(t.key).replace("|", "_")
	mi.mesh = _prepared_mesh(t.rule, t.alias)
	add_child(mi)
	mi.global_transform = t.xform
	(t.mmi as MultiMeshInstance3D).multimesh.set_instance_transform(t.index, _hidden(t.xform))
	return mi


## Puts a lifted tree back in its MultiMesh (the player stopped chopping).
func drop_tree(t: Dictionary, node: Node3D) -> void:
	if is_instance_valid(t.mmi):
		(t.mmi as MultiMeshInstance3D).multimesh.set_instance_transform(t.index, t.xform)
	if is_instance_valid(node):
		node.queue_free()


## The tree is chopped down: its stump appears and its trunk stops blocking until it grows back.
## The caller animates the lifted tree node falling.
func fell(t: Dictionary) -> void:
	Lumbering.fell(t.key)
	if trunk_shapes.has(t.key) and is_instance_valid(trunk_shapes[t.key]):
		trunk_shapes[t.key].set_deferred("disabled", true)
	_add_stump(t.key, t.rule, t.alias, t.xform)


func _add_stump(key: String, rule: Dictionary, alias: String, xf: Transform3D) -> void:
	if stumps.has(key):
		return
	var tree := Lumbering.tree_for(rule["id"], alias)
	var stump_name: String = Lumbering.OWN_STUMP.get(tree, Lumbering.MESHES.get(alias, {}).get("stump", "oak"))
	if not stump_scenes.has(stump_name):
		stump_scenes[stump_name] = load(Lumbering.STUMP_PATH % stump_name)
	var stump: Node3D = (stump_scenes[stump_name] as PackedScene).instantiate()
	stump.name = "stump_" + key.replace("|", "_")
	add_child(stump)
	stump.global_transform = xf
	# placeholder trees (a recoloured oak, pine or maple) get their trunk colour on the stump too
	var tint := Color.WHITE
	if rule.has("trunk_tint") and not Lumbering.OWN_STUMP.has(tree):
		tint = Color(rule["trunk_tint"])
	for mi: MeshInstance3D in stump.find_children("*", "MeshInstance3D", true, false):
		if tint == Color.WHITE:
			continue
		for si in mi.mesh.get_surface_count():
			var src := mi.mesh.surface_get_material(si) as BaseMaterial3D
			if src:
				var mat := src.duplicate() as BaseMaterial3D
				mat.albedo_color = tint
				mi.set_surface_override_material(si, mat)
	# the stump still blocks the way, low down
	var s := xf.basis.get_scale().x
	var body := StaticBody3D.new()
	body.collision_layer = 4
	body.collision_mask = 0
	var shape := CylinderShape3D.new()
	shape.radius = float(Lumbering.MESHES.get(alias, {}).get("trunk", 5.0)) * Lumbering.UNITS * s
	shape.height = 0.6 * s
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position.y = shape.height * 0.5
	body.add_child(cs)
	stump.add_child(body)
	stump.set_meta("rule", rule)
	stump.set_meta("alias", alias)
	stump.set_meta("xform", xf)
	stumps[key] = stump


## Stumps whose time is up: the tree grows back out of the ground where the stump was.
func _regrow_due() -> void:
	for key in stumps.keys():
		if Lumbering.is_felled(key):
			continue
		var stump: Node3D = stumps[key]
		stumps.erase(key)
		var rule: Dictionary = stump.get_meta("rule")
		var alias: String = stump.get_meta("alias")
		var xf: Transform3D = stump.get_meta("xform")
		stump.queue_free()
		if trunk_shapes.has(key) and is_instance_valid(trunk_shapes[key]):
			trunk_shapes[key].disabled = false
		var parts: PackedStringArray = String(key).split("|")
		var cell_node: Node3D = tree_cells.get(Vector2i(int(parts[2]), int(parts[3])))
		var mmi: MultiMeshInstance3D = null
		if cell_node:
			mmi = cell_node.get_node_or_null("%s_%s" % [rule["id"], alias])
		if mmi == null:
			continue  # its cell isn't built yet: it will be built standing
		var index := int(parts[4])
		var grow := MeshInstance3D.new()
		grow.mesh = _prepared_mesh(rule, alias)
		add_child(grow)
		grow.global_transform = _hidden(xf)
		var tw := grow.create_tween()
		tw.tween_method(func(f: float): grow.global_transform = Transform3D(xf.basis.scaled_local(Vector3.ONE * maxf(f, 0.001)), xf.origin),
			0.05, 1.0, 1.4).set_trans(Tween.TRANS_BACK).set_ease(Tween.EASE_OUT)
		tw.tween_callback(func():
			if is_instance_valid(mmi):
				mmi.multimesh.set_instance_transform(index, xf)
			grow.queue_free())
