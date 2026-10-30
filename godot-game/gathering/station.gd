class_name Station
extends StaticBody3D
## A place the player uses with F: the five processing stations (furnace, drying rack, tanning rack,
## sawbench, campfire), the blacksmith's anvil, and the camp's merchant, stable, battle board and
## treasure dig. GameData.STATIONS has their names. Built from simple shapes until they have proper
## models: TEST art.

var kind := ""
var label := ""
var verb := ""
var radius := 0.5
var _glow: OmniLight3D


func setup(station_kind: String) -> void:
	kind = station_kind
	var def: Dictionary = GameData.STATIONS[kind]
	label = def.label
	verb = def.verb
	name = label.replace(" ", "")
	add_to_group("gather_target")
	call("_build_" + kind)
	var shape := CylinderShape3D.new()
	shape.radius = radius
	shape.height = 1.2
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position.y = 0.6
	add_child(cs)
	var tag := Label3D.new()
	tag.text = label
	tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	tag.pixel_size = 0.004
	tag.font_size = 40
	tag.outline_size = 10
	tag.position.y = NodeArt.bounds(self).end.y + 0.25
	tag.visibility_range_end = 9.0
	tag.visibility_range_end_margin = 1.0
	tag.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	add_child(tag)


func prompt() -> String:
	return verb


func _process(_delta: float) -> void:
	if _glow:
		_glow.light_energy = 1.2 + randf() * 0.5


# --- building blocks ----------------------------------------------------------------

func _mat(color: String, metal := 0.0, rough := 0.9) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(color)
	m.metallic = metal
	m.roughness = rough
	return m


func _glowing(color: String, glow: String) -> StandardMaterial3D:
	var m := _mat(color)
	m.emission_enabled = true
	m.emission = Color(glow)
	m.emission_energy_multiplier = 2.2
	return m


func _part(mesh: PrimitiveMesh, mat: Material, pos: Vector3, rot := Vector3.ZERO) -> void:
	mesh.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	mi.rotation = rot
	add_child(mi)


func _box(size: Vector3) -> BoxMesh:
	var b := BoxMesh.new()
	b.size = size
	return b


func _cylinder(top: float, bottom: float, height: float, sides: int) -> CylinderMesh:
	var c := CylinderMesh.new()
	c.top_radius = top
	c.bottom_radius = bottom
	c.height = height
	c.radial_segments = sides
	c.rings = 1
	return c


func _fire(pos: Vector3) -> void:
	_glow = OmniLight3D.new()
	_glow.light_color = Color("#ff7a2a")
	_glow.omni_range = 2.6
	_glow.position = pos
	add_child(_glow)


# --- the stations --------------------------------------------------------------------

func _build_furnace() -> void:
	var stone := _mat("#6f675e", 0.0, 0.95)
	var dark := _mat("#3d3732", 0.0, 0.95)
	_part(_box(Vector3(0.86, 0.62, 0.78)), stone, Vector3(0, 0.31, 0))
	_part(_box(Vector3(0.94, 0.08, 0.86)), dark, Vector3(0, 0.66, 0))
	_part(_cylinder(0.13, 0.19, 0.55, 8), stone, Vector3(0, 0.97, -0.12))
	_part(_cylinder(0.16, 0.16, 0.06, 8), dark, Vector3(0, 1.25, -0.12))
	_part(_box(Vector3(0.42, 0.3, 0.06)), dark, Vector3(0, 0.27, 0.37))
	_part(_box(Vector3(0.34, 0.22, 0.01)), _glowing("#ff8a30", "#ff5a12"), Vector3(0, 0.25, 0.401))
	_fire(Vector3(0, 0.32, 0.65))


func _build_blacksmith() -> void:
	radius = 0.32
	var wood := _mat("#6b4a2c")
	var iron := _mat("#3e434b", 0.85, 0.38)
	_part(_cylinder(0.25, 0.3, 0.4, 10), wood, Vector3(0, 0.2, 0))
	_part(_box(Vector3(0.34, 0.07, 0.24)), iron, Vector3(0, 0.435, 0))
	_part(_box(Vector3(0.18, 0.12, 0.13)), iron, Vector3(0, 0.53, 0))
	_part(_box(Vector3(0.46, 0.09, 0.2)), iron, Vector3(0, 0.635, 0))
	_part(_cylinder(0.0, 0.075, 0.24, 10), iron, Vector3(0.35, 0.645, 0), Vector3(0, 0, -PI / 2))
	_part(_cylinder(0.018, 0.018, 0.3, 6), wood, Vector3(-0.05, 0.42, 0.2), Vector3(0, 0.5, PI / 2))
	_part(_box(Vector3(0.06, 0.06, 0.12)), iron, Vector3(-0.18, 0.43, 0.27), Vector3(0, 0.5, 0))


## An A-frame of poles with bundles of herbs hanging from the top bar.
func _build_drying_rack() -> void:
	var wood := _mat("#7a5a38")
	for x in [-0.5, 0.5]:
		for z in [-1, 1]:
			_part(_cylinder(0.03, 0.03, 1.2, 6), wood, Vector3(x, 0.58, z * 0.2), Vector3(z * 0.35, 0, 0))
	_part(_cylinder(0.03, 0.03, 1.15, 6), wood, Vector3(0, 1.12, 0), Vector3(0, 0, PI / 2))
	var herbs := ["#6cb454", "#fc9c3c", "#4c7cf0", "#fccc3c"]
	for i in 4:
		_part(_cylinder(0.05, 0.02, 0.35, 6), _mat(herbs[i]), Vector3(-0.36 + i * 0.24, 0.9, 0))


## A wooden frame with a hide stretched across it.
func _build_tanning_rack() -> void:
	var wood := _mat("#6b4a2c")
	for x in [-0.45, 0.45]:
		_part(_cylinder(0.035, 0.035, 1.3, 6), wood, Vector3(x, 0.65, 0))
	for y in [0.35, 1.15]:
		_part(_cylinder(0.03, 0.03, 0.95, 6), wood, Vector3(0, y, 0), Vector3(0, 0, PI / 2))
	_part(_box(Vector3(0.7, 0.7, 0.02)), _mat("#b4846c"), Vector3(0, 0.75, 0), Vector3(0, 0, 0.05))


## A saw horse with a log on it and a saw resting against it.
func _build_sawbench() -> void:
	var wood := _mat("#8a6a44")
	_part(_box(Vector3(1.1, 0.08, 0.3)), wood, Vector3(0, 0.55, 0))
	for x in [-0.45, 0.45]:
		for z in [-1, 1]:
			_part(_box(Vector3(0.06, 0.6, 0.06)), wood, Vector3(x, 0.28, z * 0.14), Vector3(z * 0.25, 0, 0))
	_part(_cylinder(0.12, 0.12, 0.9, 10), _mat("#84543c"), Vector3(0, 0.72, 0), Vector3(0, 0, PI / 2))
	_part(_box(Vector3(0.45, 0.14, 0.01)), _mat("#b8bcc4", 0.8, 0.3), Vector3(0.3, 0.45, 0.2), Vector3(0, 0, 0.5))


## A ring of stones, crossed logs and a fire.
func _build_campfire() -> void:
	var stone := _mat("#6f6a64", 0.0, 0.95)
	for i in 8:
		var a := i * TAU / 8.0
		_part(_box(Vector3(0.16, 0.12, 0.14)), stone, Vector3(cos(a) * 0.38, 0.06, sin(a) * 0.38), Vector3(0, -a, 0))
	for a in [0.4, -0.4, 1.6]:
		_part(_cylinder(0.06, 0.06, 0.6, 6), _mat("#6b4a2c"), Vector3(0, 0.1, 0), Vector3(0, a, PI / 2))
	_part(_cylinder(0.0, 0.16, 0.36, 6), _glowing("#ff8a30", "#ff5a12"), Vector3(0, 0.3, 0))
	_fire(Vector3(0, 0.5, 0))


## A market stall: a counter under a striped awning.
func _build_merchant() -> void:
	radius = 0.8
	var wood := _mat("#7a5a38")
	_part(_box(Vector3(1.4, 0.8, 0.5)), wood, Vector3(0, 0.4, 0))
	for x in [-0.65, 0.65]:
		_part(_cylinder(0.04, 0.04, 1.9, 6), wood, Vector3(x, 0.95, -0.2))
	for i in 6:
		var c := "#d84a3a" if i % 2 == 0 else "#f4ead8"
		_part(_box(Vector3(0.25, 0.04, 0.8)), _mat(c), Vector3(-0.62 + i * 0.25, 1.9, 0.05), Vector3(0.25, 0, 0))
	_part(_box(Vector3(0.3, 0.25, 0.3)), _mat("#a8873f"), Vector3(-0.4, 0.92, 0))      # a crate of goods
	_part(_cylinder(0.12, 0.12, 0.2, 10), _mat("#e9a92f", 0.9, 0.3), Vector3(0.35, 0.9, 0))   # a coin pile


## A small pen of fence posts with a roof at the back.
func _build_stable() -> void:
	radius = 1.0
	var wood := _mat("#6b4a2c")
	for i in 7:
		var a := PI * 0.15 + i * PI * 0.7 / 6.0
		_part(_box(Vector3(0.08, 0.7, 0.08)), wood, Vector3(cos(a) * 0.9, 0.35, sin(a) * 0.9))
	_part(_box(Vector3(1.9, 0.06, 0.06)), wood, Vector3(0, 0.55, 0.85))
	_part(_box(Vector3(1.8, 0.08, 1.0)), _mat("#8a4a2c"), Vector3(0, 1.5, -0.55), Vector3(0.3, 0, 0))
	for x in [-0.85, 0.85]:
		_part(_box(Vector3(0.1, 1.5, 0.1)), wood, Vector3(x, 0.75, -0.9))
	_part(_box(Vector3(0.9, 0.3, 0.5)), _mat("#e4cc54"), Vector3(0, 0.15, -0.6))       # hay


## A notice board on two posts, with crossed swords.
func _build_arena() -> void:
	var wood := _mat("#6b4a2c")
	for x in [-0.45, 0.45]:
		_part(_box(Vector3(0.08, 1.5, 0.08)), wood, Vector3(x, 0.75, 0))
	_part(_box(Vector3(1.1, 0.7, 0.05)), _mat("#a8875a"), Vector3(0, 1.1, 0.03))
	for a in [0.7, -0.7]:
		_part(_box(Vector3(0.05, 0.6, 0.02)), _mat("#c8ccd4", 0.8, 0.3), Vector3(0, 1.1, 0.07), Vector3(0, 0, a))


## A dirt mound with a shovel stuck in it.
func _build_dig_site() -> void:
	_part(_cylinder(0.3, 0.7, 0.3, 10), _mat("#6b4a2c", 0.0, 1.0), Vector3(0, 0.15, 0))
	_part(_cylinder(0.025, 0.025, 0.9, 6), _mat("#8a6a44"), Vector3(0.15, 0.6, 0), Vector3(0, 0, -0.25))
	_part(_box(Vector3(0.22, 0.28, 0.03)), _mat("#8a8e96", 0.8, 0.4), Vector3(0.07, 0.25, 0), Vector3(0, 0, -0.25))
