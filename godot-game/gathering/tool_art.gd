class_name ToolArt
## Art for the tools. The 3D model in the Imp's hand is the tool's Blockbench model (D-115,
## D-116): one GLB per tool, `models/blockbench/<kind>s/<kind>_<material>.glb`. A tool without
## one falls back to a simple model drawn here from its colours (TEST art).
## Stand-in icons for the tools that have no pictures yet (sickles, axes, bows, rods): a 24 x 24
## pixel icon for menus (pixel art, D-015). Pickaxes keep their drawn sprites.
## Models are laid out like the pickaxe: the handle along +Y from the grip, the head towards +X.

const OUTLINE := Color(0.08, 0.06, 0.07)
const STRING := Color(0.9, 0.88, 0.8)
const BLOCKBENCH_MODEL := "res://models/blockbench/%ss/%s_%s.glb"   # kind, kind, material


# --- icons ------------------------------------------------------------------------

static func icon(t: Dictionary) -> ImageTexture:
	var img := Image.create(24, 24, false, Image.FORMAT_RGBA8)
	var head := Color(t.head)
	var handle := Color(t.handle)
	match t.kind:
		"sickle":
			_line(img, Vector2(4, 20), Vector2(9, 15), handle, 2)
			for a in range(200, 381, 6):     # a crescent blade above the handle
				var p := Vector2(13, 10) + Vector2.from_angle(deg_to_rad(a)) * 7.0
				_dot(img, p, head, 2)
		"axe":
			_line(img, Vector2(5, 20), Vector2(16, 5), handle, 2)
			for y in range(3, 13):           # the blade: a wedge on the handle's top end
				var w := 6 - absi(y - 8) / 2
				for x in range(15, 15 + w):
					_px(img, x, y, head)
		"bow":
			for i in 21:                     # the limb: an arc bulging right
				var y := 2 + i
				var x := 7 + roundi(6.0 * sin(PI * i / 20.0))
				_dot(img, Vector2(x, y), head, 2)
			_line(img, Vector2(7, 2), Vector2(7, 22), STRING, 1)
			_line(img, Vector2(12, 11), Vector2(13, 13), handle, 2)   # the grip
		"rod":
			_line(img, Vector2(3, 21), Vector2(20, 3), head, 1)
			_line(img, Vector2(3, 21), Vector2(8, 16), handle, 2)
			_dot(img, Vector2(9, 18), Color(0.6, 0.6, 0.65), 2)        # the reel
			_line(img, Vector2(20, 3), Vector2(20, 14), STRING, 1)     # the line
	_outline(img)
	return ImageTexture.create_from_image(img)


static func _px(img: Image, x: int, y: int, c: Color) -> void:
	if x >= 0 and y >= 0 and x < img.get_width() and y < img.get_height():
		img.set_pixel(x, y, c)


static func _dot(img: Image, p: Vector2, c: Color, size: int) -> void:
	for dx in size:
		for dy in size:
			_px(img, roundi(p.x) + dx, roundi(p.y) + dy, c)


static func _line(img: Image, a: Vector2, b: Vector2, c: Color, size: int) -> void:
	var steps := int(maxf(absf(b.x - a.x), absf(b.y - a.y))) + 1
	for i in steps + 1:
		_dot(img, a.lerp(b, float(i) / steps), c, size)


## A 1-pixel dark outline around everything drawn, like the drawn item icons.
static func _outline(img: Image) -> void:
	var src := img.duplicate() as Image
	for y in img.get_height():
		for x in img.get_width():
			if src.get_pixel(x, y).a > 0.0:
				continue
			for d in [Vector2i(1, 0), Vector2i(-1, 0), Vector2i(0, 1), Vector2i(0, -1)]:
				var q: Vector2i = Vector2i(x, y) + d
				if q.x >= 0 and q.y >= 0 and q.x < img.get_width() and q.y < img.get_height() and src.get_pixel(q.x, q.y).a > 0.0:
					img.set_pixel(x, y, OUTLINE)
					break


# --- models -----------------------------------------------------------------------

static func model(t: Dictionary) -> Node3D:
	var path := BLOCKBENCH_MODEL % [t.kind, t.kind, (t.id as String).trim_suffix("_" + t.kind)]
	if ResourceLoader.exists(path):
		return (load(path) as PackedScene).instantiate()
	var root := Node3D.new()
	root.name = "Tool"
	var head := _mat(t.head, t.get("metal", 0.0), t.get("rough", 0.8))
	var handle := _mat(t.handle, 0.0, 0.85)
	match t.kind:
		"sickle":
			_cyl(root, handle, 0.035, 0.5, Vector3(0, 0.25, 0))
			for i in 9:                      # the crescent blade, curving out over +X
				var a := deg_to_rad(100.0 - i * 20.0)
				var p := Vector3(0.22 + cos(a) * 0.22, 0.5 + sin(a) * 0.22, 0)
				_box(root, head, Vector3(0.09, 0.03, 0.02), p, Vector3(0, 0, a + PI / 2))
		"axe":
			_cyl(root, handle, 0.035, 0.95, Vector3(0, 0.475, 0))
			_box(root, head, Vector3(0.24, 0.2, 0.04), Vector3(0.12, 0.82, 0))
			_box(root, head, Vector3(0.05, 0.28, 0.03), Vector3(0.25, 0.82, 0))   # the edge
		"bow":
			for i in 11:                     # the limbs, bulging towards +X
				var y := -0.6 + i * 0.12
				var x := 0.16 * cos(PI * (i - 5) / 10.0)
				var slope := atan2(-0.16 * PI / 10.0 * sin(PI * (i - 5) / 10.0), 0.12)
				_box(root, head, Vector3(0.05, 0.14, 0.05), Vector3(x, y, 0), Vector3(0, 0, slope))
			_cyl(root, _mat("#e6e0d0", 0.0, 0.9), 0.006, 1.2, Vector3(0, 0, 0))   # the string
			_box(root, handle, Vector3(0.07, 0.16, 0.07), Vector3(0.16, 0, 0))       # the grip
		"rod":
			_cyl(root, head, 0.022, 2.2, Vector3(0, 1.1, 0))
			_cyl(root, handle, 0.04, 0.35, Vector3(0, 0.12, 0))
			_cyl(root, _mat("#9aa0a8", 0.8, 0.3), 0.06, 0.05, Vector3(0.06, 0.3, 0), Vector3(0, 0, PI / 2))
	return root


static func _mat(colour: String, metal: float, rough: float) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(colour)
	m.metallic = metal
	m.roughness = rough
	return m


static func _box(root: Node3D, mat: Material, size: Vector3, pos: Vector3, rot := Vector3.ZERO) -> void:
	var b := BoxMesh.new()
	b.size = size
	b.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = b
	mi.position = pos
	mi.rotation = rot
	root.add_child(mi)


static func _cyl(root: Node3D, mat: Material, radius: float, height: float, pos: Vector3, rot := Vector3.ZERO) -> void:
	var c := CylinderMesh.new()
	c.top_radius = radius
	c.bottom_radius = radius
	c.height = height
	c.radial_segments = 8
	c.rings = 1
	c.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = c
	mi.position = pos
	mi.rotation = rot
	root.add_child(mi)
