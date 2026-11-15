class_name NodeArt
## Builds the 3D look of every gathering node from its tier row in GameData. Apart from the veins,
## it is TEST art until each tier has its own model:
## - ore veins: copper uses its drawn model; every other tier is built by VeinArt,
## - plants and trees: Quaternius kit models (game/glTF, CC0) recoloured from the plant or log picture,
## - animals: simple box creatures with a slight voxel feel (D-047) in the hide picture's colours,
##   until the Blockbench creatures exist (MODELS-BLOCKBENCH),
## - fishing spots: rings on the water with the fish circling underneath.
## Every model stands on y = 0 and faces +Z.

const VEIN_MODEL := "res://models/mining/copper_vein.glb"
const TINT := preload("res://gathering/tint.gdshader")


## The model's bounds in its parent's space, from its meshes. Works before it is in the tree.
static func bounds(root: Node3D) -> AABB:
	var box := AABB()
	var first := true
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = _local_to(root, mi) * (mi as MeshInstance3D).get_aabb()
		box = b if first else box.merge(b)
		first = false
	return root.transform * box


## `node`'s transform relative to `root`, not counting root's own.
static func _local_to(root: Node3D, node: Node3D) -> Transform3D:
	var xf := Transform3D.IDENTITY
	var n: Node = node
	while n != root and n is Node3D:
		xf = (n as Node3D).transform * xf
		n = n.get_parent()
	return xf


## Scales a model so its largest side is `size` metres (or its height, with `by_height`), stands it
## on y = 0 and centres it. Drops any lights or cameras. Returns a holder node around it.
static func fit(model: Node3D, size: float, by_height := false) -> Node3D:
	for n in model.find_children("*", "Light3D", true, false) + model.find_children("*", "Camera3D", true, false):
		n.free()
	var box := bounds(model)
	var side := box.size.y if by_height else maxf(box.size.x, maxf(box.size.y, box.size.z))
	model.scale *= size / maxf(side, 0.001)
	box = bounds(model)
	model.position -= Vector3(box.get_center().x, box.position.y, box.get_center().z)
	var holder := Node3D.new()
	holder.add_child(model)
	return holder


static func _flat(colour: String, metal := 0.0, rough := 0.85, glow := "") -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(colour)
	m.metallic = metal
	m.roughness = rough
	if glow:
		m.emission_enabled = true
		m.emission = Color(glow)
	return m


## Swaps each textured kit material for the tint shader, coloured by `pick(material name)`
## ("" leaves the material as it is).
static func _tint(model: Node3D, pick: Callable, glow := 0.0) -> void:
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var src := mi.get_active_material(i)
			if not src is BaseMaterial3D:
				continue
			var colour: String = pick.call(src.resource_name)
			if colour == "":
				continue
			var m := ShaderMaterial.new()
			m.shader = TINT
			m.set_shader_parameter("tex", (src as BaseMaterial3D).albedo_texture)
			m.set_shader_parameter("tint", Color(colour))
			m.set_shader_parameter("glow", glow)
			mi.set_surface_override_material(i, m)


# --- ore veins --------------------------------------------------------------------

static func vein(row: Dictionary, variant := 0) -> Node3D:
	if row.id != "copper" and not row.look.is_empty():
		return VeinArt.build(row, variant)
	var model: Node3D = load(VEIN_MODEL).instantiate()
	if not row.look.is_empty():
		_recolour_vein(model, row.look)
	return model


## The copper vein has Rock_Side, Rock_Top and Copper (the crystals); the rock1, rock2 and metall names
## were the old tin model's.
static func _vein_part(material_name: String) -> String:
	if material_name == "Rock_Side" or material_name.begins_with("rock1"):
		return "side"
	if material_name == "Rock_Top" or material_name.begins_with("rock2"):
		return "top"
	if material_name == "Copper" or material_name.begins_with("metall"):
		return "ore"
	return ""


static func _recolour_vein(model: Node3D, look: Dictionary) -> void:
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var src := mi.get_active_material(i)
			var part := _vein_part(src.resource_name) if src is BaseMaterial3D else ""
			if part == "":
				continue
			var mat: BaseMaterial3D = src.duplicate()
			mat.albedo_color = Color(look[part])
			if part == "ore":
				mat.metallic = look.metal
				mat.roughness = look.rough
				if look.has("glow"):
					mat.emission_enabled = true
					mat.emission = Color(look.glow)
			mi.set_surface_override_material(i, mat)


# --- plants -----------------------------------------------------------------------

static func plant(row: Dictionary) -> Node3D:
	var model: Node3D = load("res://glTF/%s.gltf" % row.model).instantiate()
	var flowered := false
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		for i in mi.mesh.get_surface_count():
			var m := mi.get_active_material(i)
			if m and m.resource_name in ["Flowers", "Mushrooms"]:
				flowered = true
	_tint(model, func(n: String) -> String: return row.flower if n in ["Flowers", "Mushrooms"] else row.stem,
			0.35 if row.tier >= 9 else 0.0)
	var size := 0.6 if row.model.begins_with("Mushroom") else 1.0
	var holder := fit(model, size)
	if not flowered:   # leaf-only models get a few berries or specks in the plant's colour
		var box := bounds(holder)
		var dot := SphereMesh.new()
		dot.radius = 0.045
		dot.height = 0.09
		dot.material = _flat(row.flower, 0.0, 0.5, row.flower if row.tier >= 7 else "")
		for k in 6:
			var mi := MeshInstance3D.new()
			mi.mesh = dot
			var a := k * 2.4
			mi.position = Vector3(cos(a) * box.size.x * 0.25, box.end.y * (0.7 + 0.05 * (k % 3)), sin(a) * box.size.z * 0.25)
			holder.add_child(mi)
	return holder


# --- trees ------------------------------------------------------------------------

static func tree(row: Dictionary) -> Node3D:
	var model: Node3D = load("res://glTF/%s.gltf" % row.model).instantiate()
	_tint(model, func(n: String) -> String: return row.bark if n.begins_with("Bark") else row.leaves,
			0.3 if row.tier >= 9 else 0.0)
	return fit(model, 3.6 + row.tier * 0.12, true)


# --- animals ----------------------------------------------------------------------

## A box creature: body, head, legs, tail, ears, and a few marks for its kind. Sized by tier.
## The legs are tagged "leg" so the Animal can swing them while it wanders.
static func animal(row: Dictionary) -> Node3D:
	var root := Node3D.new()
	var body := _flat(row.body, 0.0, 0.9)
	var mark := _flat(row.mark, 0.0, 0.6, row.mark if row.tier >= 6 else "")
	var eye := _flat("#101014", 0.0, 0.3)
	var s: float = 0.55 + (row.tier - 1) * 0.09
	match row.shape:
		"hopper":
			_quad(root, body, mark, eye, Vector3(0.32, 0.26, 0.42), 0.12, 0.22)
			_box(root, body, Vector3(0.06, 0.24, 0.04), Vector3(-0.06, 0.62, 0.22))   # long ears
			_box(root, body, Vector3(0.06, 0.24, 0.04), Vector3(0.06, 0.62, 0.22))
			_box(root, mark, Vector3(0.1, 0.1, 0.1), Vector3(0, 0.3, -0.25))           # tail puff
		"quad", "horned":
			_quad(root, body, mark, eye, Vector3(0.36, 0.32, 0.7), 0.3, 0.28)
			_box(root, mark, Vector3(0.1, 0.1, 0.32), Vector3(0, 0.5, -0.48), Vector3(0.5, 0, 0))   # tail
			if row.shape == "horned":
				for side in [-1, 1]:
					_box(root, mark, Vector3(0.05, 0.3, 0.05), Vector3(side * 0.12, 0.92, 0.38), Vector3(-0.3, 0, side * 0.5))
					_box(root, mark, Vector3(0.04, 0.16, 0.04), Vector3(side * 0.2, 1.02, 0.36), Vector3(0, 0, side * 1.1))
			else:
				for side in [-1, 1]:
					_box(root, body, Vector3(0.08, 0.12, 0.05), Vector3(side * 0.1, 0.84, 0.4))   # ears
		"biped":
			_box(root, body, Vector3(0.6, 0.7, 0.45), Vector3(0, 0.75, 0))
			_box(root, mark, Vector3(0.4, 0.4, 0.05), Vector3(0, 0.75, 0.23))                     # chest
			_box(root, body, Vector3(0.42, 0.36, 0.38), Vector3(0, 1.28, 0.04))                   # head
			_eyes(root, eye, 1.32, 0.24, 0.1)
			for side in [-1, 1]:
				_box(root, body, Vector3(0.18, 0.6, 0.18), Vector3(side * 0.4, 0.75, 0.05))       # arms
				_leg(root, body, Vector3(0.2, 0.42, 0.22), Vector3(side * 0.16, 0.21, 0))
		"lizard":
			_box(root, body, Vector3(0.36, 0.2, 0.8), Vector3(0, 0.26, 0))
			_box(root, body, Vector3(0.28, 0.2, 0.3), Vector3(0, 0.3, 0.52))                      # head
			_eyes(root, eye, 0.36, 0.67, 0.08)
			_box(root, body, Vector3(0.16, 0.12, 0.6), Vector3(0, 0.24, -0.66), Vector3(0.15, 0, 0))   # tail
			for k in 4:                                                                           # back spikes
				_box(root, mark, Vector3(0.08, 0.12, 0.08), Vector3(0, 0.42, 0.25 - k * 0.2), Vector3(0.6, 0, 0))
			for x in [-1, 1]:
				for z in [-1, 1]:
					_leg(root, body, Vector3(0.1, 0.18, 0.1), Vector3(x * 0.22, 0.09, z * 0.26))
		"serpent":
			for k in 7:
				var z := 0.6 - k * 0.2
				var y := 0.12 + (0.45 if k == 0 else 0.0) + (0.2 if k == 1 else 0.0)
				_box(root, mark if k % 2 else body, Vector3(0.26, 0.22, 0.24), Vector3(sin(k * 1.1) * 0.15, y, z))
			_eyes(root, eye, 0.62, 0.72, 0.07)
		"winged":
			_quad(root, body, mark, eye, Vector3(0.4, 0.34, 0.75), 0.32, 0.3)
			_box(root, body, Vector3(0.12, 0.1, 0.5), Vector3(0, 0.52, -0.58), Vector3(0.4, 0, 0))   # tail
			for side in [-1, 1]:
				_box(root, mark, Vector3(0.7, 0.04, 0.4), Vector3(side * 0.5, 0.78, -0.02), Vector3(0, 0, side * 0.35))
	root.scale = Vector3.ONE * s
	var holder := Node3D.new()
	holder.add_child(root)
	return holder


## A four-legged body: torso, head at +Z, belly mark, eyes and four tagged legs.
static func _quad(root: Node3D, body: Material, mark: Material, eye: Material, size: Vector3, leg: float, head: float) -> void:
	_box(root, body, size, Vector3(0, leg + size.y * 0.5, 0))
	_box(root, mark, Vector3(size.x * 0.7, 0.04, size.z * 0.6), Vector3(0, leg + 0.01, 0))
	var hy := leg + size.y * 0.85
	var hz := size.z * 0.5 + head * 0.35
	_box(root, body, Vector3(head, head, head), Vector3(0, hy, hz))
	_box(root, mark, Vector3(head * 0.55, head * 0.4, head * 0.3), Vector3(0, hy - head * 0.15, hz + head * 0.55))   # snout
	_eyes(root, eye, hy + head * 0.15, hz + head * 0.5, head * 0.28)
	for x in [-1, 1]:
		for z in [-1, 1]:
			_leg(root, body, Vector3(0.09, leg, 0.09), Vector3(x * size.x * 0.32, leg * 0.5, z * size.z * 0.34))


static func _eyes(root: Node3D, eye: Material, y: float, z: float, spread: float) -> void:
	for side in [-1, 1]:
		_box(root, eye, Vector3(0.05, 0.05, 0.02), Vector3(side * spread, y, z))


static func _leg(root: Node3D, mat: Material, size: Vector3, pos: Vector3) -> void:
	var pivot := Node3D.new()                # swings at the hip
	pivot.position = pos + Vector3(0, size.y * 0.5, 0)
	pivot.add_to_group("leg")
	root.add_child(pivot)
	_box(pivot, mat, size, Vector3(0, -size.y * 0.5, 0))


static func _box(root: Node3D, mat: Material, size: Vector3, pos: Vector3, rot := Vector3.ZERO) -> void:
	var b := BoxMesh.new()
	b.size = size
	b.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = b
	mi.position = pos
	mi.rotation = rot
	root.add_child(mi)


# --- fishing spots ------------------------------------------------------------------

## Two rings on the water and the fish's shape circling just under it. y = 0 is the water surface.
static func fishing_spot(row: Dictionary) -> Node3D:
	var root := Node3D.new()
	var ring_mat := _flat("#e8f6ff", 0.0, 0.2)
	ring_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	ring_mat.albedo_color.a = 0.7
	for r in [0.32, 0.55]:
		var t := TorusMesh.new()
		t.inner_radius = r
		t.outer_radius = r + 0.04
		t.rings = 24
		t.ring_segments = 4
		t.material = ring_mat
		var mi := MeshInstance3D.new()
		mi.mesh = t
		mi.name = "Ring"
		mi.position.y = 0.02
		mi.scale = Vector3(1, 0.3, 1)
		root.add_child(mi)
	var fish_mat := _flat(row.colour, 0.2, 0.4)
	fish_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	fish_mat.albedo_color.a = 0.75
	var fish := MeshInstance3D.new()
	var body := SphereMesh.new()
	body.radius = 0.1
	body.height = 0.12
	body.material = fish_mat
	fish.mesh = body
	fish.scale = Vector3(0.8, 0.5, 2.2)
	fish.name = "Fish"
	fish.position = Vector3(0.3, -0.12, 0)
	root.add_child(fish)
	return root
