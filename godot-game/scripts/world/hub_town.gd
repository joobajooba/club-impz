class_name HubTown
extends Node3D
## The hub town (J00BA, 2026-11-09): a flat square of castle walls with the castle, gardens, town square, market,
## crafters' yard, houses, orchard and the portal plaza. The plan is data/hub_town.json, made by
## `build scripts/build_hub_town.py` (also the terrain bake's streets). This script builds it:
##   - every model type is merged into one mesh and drawn as one MultiMesh (one or two draw calls per type),
##     cubes named *_glow on a second, emissive surface
##   - box colliders from each model's ground footprint (overhangs and awnings don't block)
##   - warm OmniLights on the lamps, faded in with the night (BiomeEnvironment.night); lamp glass glows brighter
##   - Marker3D nodes under npc_spots/ where vendor and crafter NPCs can stand (meta "role")
## The castle keeps its own scene (hub_castle.tscn, with its colliders) and the portal is scenes/shared/portal.tscn.

const PLAN := "res://data/hub_town.json"
const GLOW_DAY := 0.25           # lamp glass emission by day
const GLOW_NIGHT := 0.9          # and at full night
const LIGHT_ENERGY := 3.0
const LIGHT_RANGE := 9.0
const LIGHT_COLOR := Color("#ffc878")
const LIGHT_FADE_BEGIN := 38.0   # lights further than this from the camera fade out (Compatibility renderer budget)

var world: GameWorld
var glow_mats: Array[StandardMaterial3D] = []
var lamp_lights: Array[OmniLight3D] = []
var _night := -1.0
var birds: Array[Node3D] = []
var _rects: Array = []          # placement footprints (plan "no_scatter"): birds don't land on them
var _walls := 75.0

## Birds round the spawn (scripts/world/bird.gd, clock driven so every player sees the same flock):
## [kind, home x, home z, how many, range scale]. Soarers circle over the portal plaza and the avenue; pigeons
## potter about the plaza, crows along the avenue, robins by the plaza hedges.
const BIRDS := [
	["eagle", 0.0, 40.0, 1, 0.8], ["seagull", 0.0, 60.0, 2, 0.6], ["seagull", 10.0, 48.0, 1, 0.7],
	["pigeon", 0.0, 62.0, 6, 0.5], ["crow", 0.0, 42.0, 2, 0.6], ["robin", -12.0, 60.0, 1, 0.5], ["robin", 12.0, 60.0, 1, 0.5],
]


func populate(w: GameWorld) -> void:
	world = w
	var plan: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(PLAN))
	var t0 := Time.get_ticks_msec()
	var by_alias := {}
	for p in plan["placements"]:
		if p[0] == "castle":
			_place_castle(p)
			continue
		if not by_alias.has(p[0]):
			by_alias[p[0]] = []
		by_alias[p[0]].append(p)
	var models_root := Node3D.new()
	models_root.name = "models"
	add_child(models_root)
	for alias in by_alias:
		var mesh := _merged_mesh(plan["models"][alias]["path"])
		var mm := MultiMesh.new()
		mm.transform_format = MultiMesh.TRANSFORM_3D
		mm.mesh = mesh
		mm.instance_count = by_alias[alias].size()
		for i in by_alias[alias].size():
			mm.set_instance_transform(i, _xf(by_alias[alias][i]))
		var mmi := MultiMeshInstance3D.new()
		mmi.name = alias
		mmi.multimesh = mm
		models_root.add_child(mmi)
	_make_colliders(plan["colliders"])
	_make_lights(plan["lights"])
	_make_npc_spots(plan["npc_spots"])
	_place_portal(plan["landmarks"]["portal"])
	_rects = plan["no_scatter"]
	_walls = float(plan["walls"])
	_place_birds()
	print("hub town: %d placements, %d types, %d colliders, %d lights in %d ms" % [plan["placements"].size(), by_alias.size(),
		plan["colliders"].size(), lamp_lights.size(), Time.get_ticks_msec() - t0])


func _xf(p: Array) -> Transform3D:
	var x: float = p[1]
	var z: float = p[3]
	var basis := Basis(Vector3.UP, deg_to_rad(p[4])).scaled(Vector3.ONE * float(p[5]))
	return Transform3D(basis, Vector3(x, world.ground_height(x, z) + float(p[2]), z))


## A Blockbench glb is one mesh per cube: merge them into one ArrayMesh, with a plain surface and (when the model
## has *_glow cubes) an emissive one. Hard alpha and no culling everywhere, for the cards (leaves, flowers, ivy).
func _merged_mesh(path: String) -> ArrayMesh:
	var inst := (load(path) as PackedScene).instantiate() as Node3D
	var tools := [null, null]
	var tex: Texture2D = null
	for m: MeshInstance3D in inst.find_children("*", "MeshInstance3D", true, false):
		var xf := _local_xf(inst, m)
		var k := 1 if _is_glow(m, inst) else 0
		for si in m.mesh.get_surface_count():
			var src := m.get_active_material(si) as BaseMaterial3D
			if tex == null and src != null:
				tex = src.albedo_texture
			if tools[k] == null:
				tools[k] = SurfaceTool.new()
				(tools[k] as SurfaceTool).begin(Mesh.PRIMITIVE_TRIANGLES)
			(tools[k] as SurfaceTool).append_from(m.mesh, si, xf)
	inst.free()
	var mesh := ArrayMesh.new()
	for k in 2:
		if tools[k] == null:
			continue
		var st := tools[k] as SurfaceTool
		st.set_material(_material(tex, k == 1))
		mesh = st.commit(mesh)
	return mesh


func _material(tex: Texture2D, glow: bool) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_texture = tex
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	if glow:
		mat.emission_enabled = true
		mat.emission_texture = tex
		mat.emission = Color("#ffd9a0")  # warm the pale glass texture
		mat.emission_energy_multiplier = GLOW_DAY
		glow_mats.append(mat)
	return mat


static func _local_xf(root: Node3D, n: Node3D) -> Transform3D:
	var xf := n.transform
	var p := n.get_parent()
	while p != null and p != root:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf


static func _is_glow(n: Node, root: Node) -> bool:
	while n != null and n != root:
		if String(n.name).ends_with("_glow"):
			return true
		n = n.get_parent()
	return false


func _make_colliders(list: Array) -> void:
	var body := StaticBody3D.new()
	body.name = "colliders"
	body.collision_layer = 4
	body.collision_mask = 0
	add_child(body)
	for c in list:
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(c[3], c[4], c[5])
		cs.shape = box
		var x: float = c[0]
		var z: float = c[2]
		cs.position = Vector3(x, world.ground_height(x, z) + float(c[1]), z)
		cs.rotation.y = deg_to_rad(c[6])
		body.add_child(cs)


func _make_lights(list: Array) -> void:
	var root := Node3D.new()
	root.name = "lamp_lights"
	add_child(root)
	for l in list:
		var light := OmniLight3D.new()
		var x: float = l[0]
		var z: float = l[2]
		light.position = Vector3(x, world.ground_height(x, z) + float(l[1]), z)
		var many: int = l[3]
		light.omni_range = LIGHT_RANGE * (1.35 if many > 1 else 1.0)
		light.light_color = LIGHT_COLOR
		light.light_energy = 0.0
		light.shadow_enabled = false
		light.distance_fade_enabled = true
		light.distance_fade_begin = LIGHT_FADE_BEGIN
		light.distance_fade_length = 10.0
		light.visible = false
		light.set_meta("energy", LIGHT_ENERGY * (1.3 if many > 1 else 1.0))
		root.add_child(light)
		lamp_lights.append(light)


func _make_npc_spots(list: Array) -> void:
	var root := Node3D.new()
	root.name = "npc_spots"
	add_child(root)
	for n in list:
		var m := Marker3D.new()
		m.name = n["name"]
		var x: float = n["pos"][0]
		var z: float = n["pos"][2]
		m.position = Vector3(x, world.ground_height(x, z), z)
		m.rotation.y = deg_to_rad(n["yaw"])
		m.set_meta("role", n["role"])
		root.add_child(m)


func _place_castle(p: Array) -> void:
	var castle := (load("res://scenes/hub/hub_castle.tscn") as PackedScene).instantiate() as Node3D
	castle.name = "castle"
	add_child(castle)
	castle.transform = _xf(p)


func _place_portal(xz: Array) -> void:
	var portal := (load("res://scenes/shared/portal.tscn") as PackedScene).instantiate() as Node3D
	portal.name = "portal_to_resource_world"
	portal.set("target_world", "resource")
	portal.set("target_spawn", "spawn_point")
	add_child(portal)
	var x: float = xz[0]
	var z: float = xz[1]
	portal.global_position = Vector3(x, world.ground_height(x, z), z)


func _place_birds() -> void:
	var root := Node3D.new()
	root.name = "birds"
	add_child(root)
	var n := 0
	for spec in BIRDS:
		for i in int(spec[3]):
			n += 1
			var b: Node3D = load("res://scripts/world/bird.gd").new()
			var x: float = spec[1] + (i % 3 - 1) * 1.5
			var z: float = spec[2] + (i / 3) * 1.5
			b.set("kind", spec[0])
			b.set("home", Vector3(x, world.ground_height(x, z), z))
			b.set("bird_seed", 7000 + n)
			b.set("data", world.data())
			b.set("view", world.player)
			b.set("range_scale", spec[4])
			b.set("spot_ok", _bird_spot_ok)
			b.name = "%s_%d" % [spec[0], n]
			root.add_child(b)
			birds.append(b)


## Open ground inside the walls, not on a building, stall, hedge or planter.
func _bird_spot_ok(x: float, z: float) -> bool:
	if absf(x) > _walls - 3.0 or absf(z) > _walls - 3.0:
		return false
	for r in _rects:
		if x > r[0] - 0.5 and x < r[2] + 0.5 and z > r[1] - 0.5 and z < r[3] + 0.5:
			return false
	return true


func set_player(p: Node3D) -> void:
	for b in birds:
		b.set("view", p)


func _process(_delta: float) -> void:
	if world == null or world.environment == null:
		return
	var n := clampf(world.environment.night, 0.0, 1.0)
	if absf(n - _night) < 0.005:
		return
	_night = n
	var e := lerpf(GLOW_DAY, GLOW_NIGHT, n)
	for m in glow_mats:
		m.emission_energy_multiplier = e
	var on := n > 0.02
	for l in lamp_lights:
		l.visible = on
		l.light_energy = float(l.get_meta("energy")) * n
