class_name ImpBuilder
## Builds an Imp from the body and trait Blockbench models exported to res://data/impz/
## (`build scripts/export_imp_customizer.py`). A GDScript port of impz.club's src/lib/impRig.js, so the
## game and the website's Imp Customization page put the same Imp together.
##
## A body supplies the skeleton: one Node3D per Blockbench group (bone), named as in Blockbench
## (Head, Chest, R-Arm, ...). Each trait file repeats the body's bone names down to where it attaches,
## so its cubes are merged into the body's bones by name and move with them.
## Cubes are baked into one mesh per bone and texture. Units are Blockbench units (the caller scales).

const MANIFEST := "res://data/impz/manifest.json"
const SLOTS := ["body", "head", "eyes", "clothing", "back"]
const DEFAULT := {body = "body_green", head = "", eyes = "", clothing = "", back = ""}

static var _manifest := {}
static var _models := {}
static var _textures := {}
static var _materials := {}

## Blockbench face -> its 4 corners (unit cube, ±1) in the order top-left, top-right, bottom-left,
## bottom-right of the face's UV rectangle (the same corners three.js BoxGeometry uses), and its normal.
const FACES := {
	east = [[Vector3(1, 1, 1), Vector3(1, 1, -1), Vector3(1, -1, 1), Vector3(1, -1, -1)], Vector3.RIGHT],
	west = [[Vector3(-1, 1, -1), Vector3(-1, 1, 1), Vector3(-1, -1, -1), Vector3(-1, -1, 1)], Vector3.LEFT],
	up = [[Vector3(-1, 1, -1), Vector3(1, 1, -1), Vector3(-1, 1, 1), Vector3(1, 1, 1)], Vector3.UP],
	down = [[Vector3(-1, -1, 1), Vector3(1, -1, 1), Vector3(-1, -1, -1), Vector3(1, -1, -1)], Vector3.DOWN],
	south = [[Vector3(-1, 1, 1), Vector3(1, 1, 1), Vector3(-1, -1, 1), Vector3(1, -1, 1)], Vector3.BACK],
	north = [[Vector3(1, 1, -1), Vector3(-1, 1, -1), Vector3(1, -1, -1), Vector3(-1, -1, -1)], Vector3.FORWARD],
}


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var text := FileAccess.get_file_as_string(MANIFEST)
		var data = JSON.parse_string(text)
		if data is Dictionary:
			_manifest = data
		else:
			push_error("ImpBuilder: could not read " + MANIFEST)
	return _manifest


static func entry(slot: String, id: String) -> Dictionary:
	for e in manifest().get(slot, []):
		if e.id == id:
			return e
	return {}


static func name_of(slot: String, id: String) -> String:
	return entry(slot, id).get("name", "None") if id != "" else "None"


## Builds the Imp for `look` ({body, head, eyes, clothing, back} of manifest ids, "" = none).
## Returns a Node3D in Blockbench units with the Imp facing +z, as in Blockbench.
static func build(look: Dictionary) -> Node3D:
	var root := Node3D.new()
	root.name = "imp_model"
	var body := entry("body", look.get("body", DEFAULT.body))
	if body.is_empty():
		body = entry("body", DEFAULT.body)
	var eyes := entry("eyes", look.get("eyes", ""))
	var bones := {}
	_add_model(_model(body.model), _body_material(body, eyes.get("overlay", "")), root, bones)
	for slot in ["head", "clothing", "back", "eyes"]:
		var e := entry(slot, look.get(slot, ""))
		if e.has("model"):
			_add_model(_model(e.model), _material(e.texture, e.get("blend", false)), root, bones)
	return root


static func _model(path: String) -> Dictionary:
	if not _models.has(path):
		var data = JSON.parse_string(FileAccess.get_file_as_string(path))
		_models[path] = data if data is Dictionary else {}
		if not data is Dictionary:
			push_error("ImpBuilder: could not read " + path)
	return _models[path]


static func _texture(path: String) -> Texture2D:
	if not _textures.has(path):
		_textures[path] = load(path)
	return _textures[path]


## The body's texture with an eyes overlay (pupil colours, beam glow) painted over its face.
static func _body_material(body: Dictionary, overlay: String) -> Array:
	if overlay == "":
		return _material(body.texture, false)
	var cache_key: String = body.texture + "+" + overlay
	if not _materials.has(cache_key):
		var img := _texture(body.texture).get_image()
		img.decompress()
		img.convert(Image.FORMAT_RGBA8)
		var over := _texture(overlay).get_image()
		over.decompress()
		over.convert(Image.FORMAT_RGBA8)
		if over.get_size() != img.get_size():
			over.resize(img.get_width(), img.get_height(), Image.INTERPOLATE_NEAREST)
		img.blend_rect(over, Rect2i(Vector2i.ZERO, over.get_size()), Vector2i.ZERO)
		_materials[cache_key] = _make_materials(ImageTexture.create_from_image(img), false)
	return _materials[cache_key]


static func _material(path: String, blend: bool) -> Array:
	if not _materials.has(path):
		_materials[path] = _make_materials(_texture(path), blend)
	return _materials[path]


## [lit, glow]: glow is for cubes named *glow* (lazer beams, golem cracks), unshaded and additive-looking.
static func _make_materials(tex: Texture2D, blend: bool) -> Array:
	var lit := StandardMaterial3D.new()
	lit.albedo_texture = tex
	lit.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	lit.roughness = 1.0
	lit.specular_mode = BaseMaterial3D.SPECULAR_DISABLED
	if blend:
		lit.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_DEPTH_PRE_PASS
	else:
		lit.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
		lit.alpha_scissor_threshold = 0.05
	var glow := StandardMaterial3D.new()
	glow.albedo_texture = tex
	glow.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	glow.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	glow.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	glow.cull_mode = BaseMaterial3D.CULL_DISABLED
	return [lit, glow]


## Blockbench rotates Z, then Y, then X (three.js order "ZYX").
static func _basis(rot) -> Basis:
	if rot == null:
		return Basis()
	var r := Vector3(rot[0], rot[1], rot[2]) * (PI / 180.0)
	return Basis(Vector3.BACK, r.z) * Basis(Vector3.UP, r.y) * Basis(Vector3.RIGHT, r.x)


static func _vec(a) -> Vector3:
	return Vector3(a[0], a[1], a[2])


static func _add_model(model: Dictionary, mats: Array, root: Node3D, bones: Dictionary) -> void:
	if model.is_empty():
		return
	var tex_size := Vector2(model.texture[0], model.texture[1])
	# per bone node: [lit SurfaceTool, glow SurfaceTool], filled while walking, committed at the end
	var tools := {}
	for node in model.bones:
		_walk(node, root, Vector3.ZERO, model, tex_size, bones, tools)
	for bone: Node3D in tools:
		for i in 2:
			var st: SurfaceTool = tools[bone][i]
			if st == null:
				continue
			var mi := MeshInstance3D.new()
			mi.name = "mesh" if i == 0 else "glow"
			mi.mesh = st.commit()
			mi.material_override = mats[i]
			if i == 1:
				mi.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
			bone.add_child(mi)


static func _walk(node, parent: Node3D, parent_origin: Vector3, model: Dictionary, tex_size: Vector2, bones: Dictionary, tools: Dictionary) -> void:
	if node is float or node is int:
		var el: Dictionary = model.elements[int(node)]
		var glow := 1 if "glow" in String(el.name).to_lower() else 0
		if not tools.has(parent):
			tools[parent] = [null, null]
		if tools[parent][glow] == null:
			var st := SurfaceTool.new()
			st.begin(Mesh.PRIMITIVE_TRIANGLES)
			tools[parent][glow] = st
		_add_cube(tools[parent][glow], el, parent_origin, tex_size)
		return
	var bone_name: String = node.name
	if not bones.has(bone_name):
		var b := Node3D.new()
		b.name = bone_name
		b.position = _vec(node.origin) - parent_origin
		b.basis = _basis(node.get("rotation"))
		parent.add_child(b)
		bones[bone_name] = {node = b, origin = _vec(node.origin)}
	var bone: Dictionary = bones[bone_name]
	for child in node.children:
		_walk(child, bone.node, bone.origin, model, tex_size, bones, tools)


## One cube, baked into the bone's mesh: pivot at the cube's origin, rotated, centred on the cube.
## A negative stretch mirrors the cube about its centre (the winding flips with it).
static func _add_cube(st: SurfaceTool, el: Dictionary, bone_origin: Vector3, tex_size: Vector2) -> void:
	var from := _vec(el.from)
	var to := _vec(el.to)
	var stretch := _vec(el.get("stretch", [1, 1, 1]))
	var half := Vector3(
		max(abs((to.x - from.x) * stretch.x), 0.001),
		max(abs((to.y - from.y) * stretch.y), 0.001),
		max(abs((to.z - from.z) * stretch.z), 0.001)) * 0.5
	var mirror := Vector3(signf(stretch.x) if stretch.x != 0 else 1.0, signf(stretch.y) if stretch.y != 0 else 1.0, signf(stretch.z) if stretch.z != 0 else 1.0)
	var flipped := mirror.x * mirror.y * mirror.z < 0
	var origin := _vec(el.origin)
	var rot := _basis(el.get("rotation"))
	var centre := (from + to) * 0.5 - origin
	var pivot := origin - bone_origin
	for face_name in el.faces:
		var face: Dictionary = el.faces[face_name]
		var def: Array = FACES[face_name]
		var uv: Array = face.uv
		var p := []
		var t := []
		for k in 4:
			var c: Vector3 = def[0][k] * half * mirror
			p.append(pivot + rot * (centre + c))
			t.append(Vector2(uv[2] if k % 2 else uv[0], uv[3] if k >= 2 else uv[1]) / tex_size)
		var n: Vector3 = (rot * (def[1] * mirror)).normalized()
		# Godot draws clockwise triangles as the front: (tl, tr, bl) and (bl, tr, br), seen from outside
		var order := [0, 1, 2, 2, 1, 3] if not flipped else [0, 2, 1, 2, 3, 1]
		for i in order:
			st.set_normal(n)
			st.set_uv(t[i])
			st.add_vertex(p[i])
