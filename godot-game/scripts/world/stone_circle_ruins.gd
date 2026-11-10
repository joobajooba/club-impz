extends Node3D
## The stone circle ruins (assets/models/buildings/stone_circle_ruins.glb, from J00BA's stone_circle_ruins.bbmodel):
## a ruined Stonehenge-style ring with Scottish standing stones. It replaces the old standing_stones and pillar_ring
## block-outs in the resource world.
## - Every stone (and every tuft, heather clump and pebble) is lowered or raised onto the terrain under it, so the
##   ring sits on uneven ground (the mountain site isn't flattened).
## - One convex collider per stone cube; ground cover and rubble don't collide.
## - The ~450 cubes are merged into one mesh with one pixel-crisp material (hard alpha for the grass and heather).

const MODEL := preload("res://assets/models/buildings/stone_circle_ruins.glb")
const SCALE := 1.6                    # 1.6x the Blockbench size: sarsens about 5 m tall, the ring about 17 m across
const NO_COLLIDE := ["grass_tuft", "heather", "pebble", "rubble"]
const FOOT := 0.6                     # metres round a stone's base sampled for the lowest ground

## World terrain height (x, z) -> y, set by resource_landmarks.gd before this enters the tree. Unset: flat ground.
var ground: Callable


func _ready() -> void:
	var model := MODEL.instantiate() as Node3D
	model.scale = Vector3.ONE * SCALE
	add_child(model)
	var meshes: Array[MeshInstance3D] = []
	for n in model.find_children("*", "MeshInstance3D", true, false):
		meshes.append(n as MeshInstance3D)
	if ground.is_valid():
		_fit_to_ground(meshes)
	var body := StaticBody3D.new()
	body.name = "collision"
	body.collision_layer = 4
	add_child(body)
	var inv := global_transform.affine_inverse()
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var src_mat: BaseMaterial3D = null
	for mi in meshes:
		var xf := inv * mi.global_transform
		for si in mi.mesh.get_surface_count():
			st.append_from(mi.mesh, si, xf)
			if src_mat == null:
				src_mat = mi.get_active_material(si) as BaseMaterial3D
		if not _skip_collider(mi):
			var shape := ConvexPolygonShape3D.new()
			var pts := PackedVector3Array()
			for v in mi.mesh.get_faces():
				pts.append(xf * v)
			shape.points = pts
			var cs := CollisionShape3D.new()
			cs.shape = shape
			body.add_child(cs)
	var mat := StandardMaterial3D.new()
	if src_mat:
		mat.albedo_texture = src_mat.albedo_texture
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST_WITH_MIPMAPS
	mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
	mat.alpha_scissor_threshold = 0.5
	mat.cull_mode = BaseMaterial3D.CULL_DISABLED
	mat.roughness = 1.0
	mat.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	st.set_material(mat)
	var out := MeshInstance3D.new()
	out.name = "merged"
	out.mesh = st.commit()
	add_child(out)
	model.queue_free()


func _skip_collider(mi: MeshInstance3D) -> bool:
	for word in NO_COLLIDE:
		if String(mi.name).contains(word):
			return true
	return false


func _fit_to_ground(meshes: Array[MeshInstance3D]) -> void:
	## Each stone is a glb node holding its cubes, with its origin at the stone's base. Ground cover cubes are loose
	## meshes. Each moves by the difference between the lowest ground round its base and the ground at the ring's
	## centre. Lintels move with the two uprights nearest them, so they stay on top.
	var movers := {}
	for mi in meshes:
		var p := mi.get_parent()
		movers[mi if String(p.name) == "ground_cover" else p] = true
	var y0 := global_position.y
	var shift := {}
	var lintels: Array[Node3D] = []
	for n: Node3D in movers:
		if String(n.name).contains("lintel") and not String(n.name).contains("fallen"):
			lintels.append(n)
			continue
		var g := n.global_position
		var h: float = ground.call(g.x, g.z)
		for o in [Vector2(FOOT, 0), Vector2(-FOOT, 0), Vector2(0, FOOT), Vector2(0, -FOOT)]:
			h = minf(h, ground.call(g.x + o.x, g.z + o.y))
		shift[n] = h - y0
	for l in lintels:
		var near: Array = shift.keys().filter(func(n): return String(n.name).contains("sarsen") or String(n.name).contains("upright"))
		var lp := Vector2(l.global_position.x, l.global_position.z)
		near.sort_custom(func(a, b): return lp.distance_squared_to(Vector2(a.global_position.x, a.global_position.z)) 			< lp.distance_squared_to(Vector2(b.global_position.x, b.global_position.z)))
		shift[l] = (shift[near[0]] + shift[near[1]]) / 2.0
	for n: Node3D in shift:
		n.position.y += shift[n] / SCALE
