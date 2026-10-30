extends Node3D
## Clean block-out placeholders in the right size and colour, each used by its own scene so the real Blockbench
## model can replace it later (docs/world_build_notes.md lists them all). Built from boxes, cylinders and cones,
## with simple box colliders for the solid parts.

@export_enum("castle", "market_stall", "smelter", "workbench", "anvil", "standing_stones", "stone_arch", "stone_ruin",
	"ice_spire", "frozen_waterfall", "pillar_ring", "hollow_tree", "dreadstone_pit", "log_bridge", "obsidian_vent",
	"sunken_ruins", "giant_stone_peak_cairn") var kind := "castle"
@export var colour_seed := 0

const STONE := Color("#8a8a90")
const STONE_DARK := Color("#6a6a72")
const ROOF := Color("#3c6a6a")
const WOOD := Color("#7a5232")
const WOOD_DARK := Color("#4e3220")

var body: StaticBody3D


func _ready() -> void:
	body = StaticBody3D.new()
	body.name = "collision"
	body.collision_layer = 4
	add_child(body)
	call("_build_" + kind)


func box(size: Vector3, pos: Vector3, col: Color, collide := true, rot_y := 0.0, emissive := 0.0) -> MeshInstance3D:
	## pos = centre of the bottom face.
	var mi := MeshInstance3D.new()
	var m := BoxMesh.new()
	m.size = size
	m.material = _mat(col, emissive)
	mi.mesh = m
	mi.position = pos + Vector3(0, size.y / 2.0, 0)
	mi.rotation.y = rot_y
	add_child(mi)
	if collide:
		var cs := CollisionShape3D.new()
		var sh := BoxShape3D.new()
		sh.size = size
		cs.shape = sh
		cs.position = mi.position
		cs.rotation.y = rot_y
		body.add_child(cs)
	return mi


func cyl(r_bottom: float, r_top: float, h: float, pos: Vector3, col: Color, collide := true, sides := 10) -> MeshInstance3D:
	var mi := MeshInstance3D.new()
	var m := CylinderMesh.new()
	m.bottom_radius = r_bottom
	m.top_radius = r_top
	m.height = h
	m.radial_segments = sides
	m.rings = 1
	m.material = _mat(col)
	mi.mesh = m
	mi.position = pos + Vector3(0, h / 2.0, 0)
	add_child(mi)
	if collide:
		var cs := CollisionShape3D.new()
		var sh := CylinderShape3D.new()
		sh.radius = maxf(r_bottom, r_top) * 0.9
		sh.height = h
		cs.shape = sh
		cs.position = mi.position
		body.add_child(cs)
	return mi


func _mat(col: Color, emissive := 0.0) -> StandardMaterial3D:
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.roughness = 0.95
	if emissive > 0.0:
		mat.emission_enabled = true
		mat.emission = col
		mat.emission_energy_multiplier = emissive
	return mat


# ---------------------------------------------------------------- hub
func _build_castle() -> void:
	## Hub centrepiece (scenery only): keep, gatehouse, curtain walls with merlons, four round towers with cones.
	box(Vector3(20, 22, 16), Vector3(0, 0, -4), STONE)                       # keep
	box(Vector3(21, 1, 17), Vector3(0, 22, -4), STONE_DARK)
	cyl(15, 0.4, 12, Vector3(0, 23, -4), ROOF, false, 4).rotation.y = PI / 4.0  # keep roof
	for x in [-18.0, 18.0]:
		box(Vector3(2, 9, 26), Vector3(x, 0, 0), STONE)                       # side walls
	box(Vector3(38, 9, 2), Vector3(0, 0, -13), STONE)                        # back wall
	box(Vector3(12, 9, 2), Vector3(-12, 0, 12), STONE)                       # front walls either side of the gate
	box(Vector3(12, 9, 2), Vector3(12, 0, 12), STONE)
	box(Vector3(12, 13, 4), Vector3(0, 0, 13), STONE_DARK)                   # gatehouse
	box(Vector3(5, 7, 0.4), Vector3(0, 0, 15.1), Color("#4a3020"), false)    # closed gate
	for i in 7:
		box(Vector3(1.2, 1.2, 4.2), Vector3(-5.4 + i * 1.8, 13, 13), STONE_DARK, false)
	for x in [-23.0, -17.0, -11.0, 11.0, 17.0, 23.0]:
		if absf(x) < 18.5:
			for k in 3:
				box(Vector3(1.2, 1.2, 2.2), Vector3(x + k * 2.0 - 2.0, 9, 12), STONE_DARK, false)
	for p in [Vector2(-19, -13), Vector2(19, -13), Vector2(-19, 13), Vector2(19, 13)]:
		cyl(4.0, 3.6, 17, Vector3(p.x, 0, p.y), STONE)
		cyl(4.6, 4.6, 1.5, Vector3(p.x, 17, p.y), STONE_DARK, false)
		cyl(5.2, 0.2, 10, Vector3(p.x, 18.5, p.y), ROOF, false, 8)
	cyl(3.0, 2.8, 30, Vector3(10, 0, -9), STONE)                             # tall keep tower
	cyl(4.0, 0.2, 12, Vector3(10, 30, -9), ROOF, false, 8)


func _build_market_stall() -> void:
	var cloth: Color = [Color("#c23a42"), Color("#2e58a8"), Color("#e2a830"), Color("#3a8a5a")][colour_seed % 4]
	for p in [Vector2(-1.6, -1.1), Vector2(1.6, -1.1), Vector2(-1.6, 1.1), Vector2(1.6, 1.1)]:
		box(Vector3(0.22, 2.6, 0.22), Vector3(p.x, 0, p.y), WOOD_DARK, false)
	box(Vector3(3.4, 1.0, 1.0), Vector3(0, 0, 1.0), WOOD)                    # counter
	box(Vector3(3.6, 0.12, 1.2), Vector3(0, 1.0, 1.0), WOOD_DARK, false)
	var roof := box(Vector3(3.9, 0.12, 2.9), Vector3(0, 2.6, 0), cloth, false)
	roof.rotation.x = deg_to_rad(-12)
	for i in 4:
		box(Vector3(0.48, 0.3, 0.05), Vector3(-1.45 + i * 0.97, 2.18, 1.5), cloth.lightened(0.35) if i % 2 else cloth, false)
	box(Vector3(0.6, 0.6, 0.6), Vector3(-1.0, 0, -0.4), WOOD, true, 0.3)      # crates
	box(Vector3(0.5, 0.5, 0.5), Vector3(1.1, 0, -0.5), WOOD.darkened(0.15), true, -0.2)


func _build_smelter() -> void:
	box(Vector3(2.6, 2.2, 2.4), Vector3.ZERO, STONE_DARK)
	box(Vector3(1.0, 0.8, 0.1), Vector3(0, 0.4, 1.21), Color("#ff8a2a"), false, 0.0, 2.5)
	cyl(0.55, 0.45, 2.4, Vector3(0.6, 2.2, -0.5), STONE, false, 8)
	box(Vector3(2.8, 0.3, 2.6), Vector3(0, 2.2, 0), STONE, false)


func _build_workbench() -> void:
	box(Vector3(2.4, 0.15, 1.0), Vector3(0, 0.85, 0), WOOD, false)
	for p in [Vector2(-1.05, -0.38), Vector2(1.05, -0.38), Vector2(-1.05, 0.38), Vector2(1.05, 0.38)]:
		box(Vector3(0.14, 0.85, 0.14), Vector3(p.x, 0, p.y), WOOD_DARK, false)
	box(Vector3(2.4, 1.0, 1.0), Vector3(0, 0, 0), WOOD, true).visible = false  # collider only
	box(Vector3(0.5, 0.12, 0.25), Vector3(-0.5, 1.0, 0), Color("#6a717b"), false)
	box(Vector3(0.3, 0.3, 0.3), Vector3(0.6, 1.0, 0.1), WOOD_DARK, false)


func _build_anvil() -> void:
	box(Vector3(0.6, 0.5, 0.6), Vector3.ZERO, WOOD_DARK)
	box(Vector3(1.0, 0.35, 0.45), Vector3(0, 0.5, 0), Color("#4a5059"), false)
	box(Vector3(0.35, 0.2, 0.3), Vector3(0.6, 0.62, 0), Color("#4a5059"), false)


# ---------------------------------------------------------------- resource world landmarks
func _build_standing_stones() -> void:
	for i in 9:
		var a := i * TAU / 9.0
		var h := 4.5 + (i % 3) * 1.2
		var s := box(Vector3(1.4, h, 0.8), Vector3(cos(a) * 9.0, 0, sin(a) * 9.0), Color("#7a7e8a"), true, -a)
		s.rotation.z = deg_to_rad(((i * 37) % 9) - 4)
	box(Vector3(3, 1.0, 1.6), Vector3(0, 0, 0), Color("#6a6e7a"))


func _build_stone_arch() -> void:
	var col := Color("#c49a6a")
	box(Vector3(6, 26, 7), Vector3(-12, 0, 0), col)
	box(Vector3(6, 26, 7), Vector3(12, 0, 0), col)
	box(Vector3(32, 6, 7), Vector3(0, 26, 0), col)
	box(Vector3(20, 2.5, 6), Vector3(0, 23.5, 0), col.darkened(0.12), false)
	box(Vector3(8, 3, 7.5), Vector3(-12, 0, 0), col.darkened(0.2))
	box(Vector3(8, 3, 7.5), Vector3(12, 0, 0), col.darkened(0.2))


func _build_stone_ruin() -> void:
	var col := Color("#9a9a8a")
	box(Vector3(10, 6, 1.2), Vector3(0, 0, -5), col)
	box(Vector3(1.2, 4, 8), Vector3(-5, 0, -1), col)
	box(Vector3(1.2, 2.2, 5), Vector3(5, 0, -2.5), col.darkened(0.1))
	for i in 4:
		cyl(0.6, 0.6, 3.0 + i, Vector3(-3 + i * 2.2, 0, 4), col.lightened(0.05), true, 8)


func _build_ice_spire() -> void:
	var ice := Color("#9cc8e8")
	cyl(7, 0.5, 46, Vector3.ZERO, ice, true, 6)
	cyl(3, 0.3, 22, Vector3(6, 0, 3), ice.lightened(0.2), true, 5)
	cyl(2.5, 0.2, 16, Vector3(-5, 0, -4), ice.darkened(0.1), true, 5)


func _build_frozen_waterfall() -> void:
	var ice := Color("#b8e0f8")
	for i in 7:
		box(Vector3(2.4, 22 - (i % 3) * 3, 2.0), Vector3(-7 + i * 2.3, 0, (i % 2) * 0.8), ice.darkened(0.05 * (i % 3)), true)
	box(Vector3(20, 2, 8), Vector3(0, 0, 3), Color("#d0ecf8"))


func _build_pillar_ring() -> void:
	var col := Color("#d8c098")
	for i in 10:
		var a := i * TAU / 10.0
		var h := 12.0 if i % 3 else 7.0
		cyl(1.4, 1.2, h, Vector3(cos(a) * 15, 0, sin(a) * 15), col, true, 8)
		if i % 2 == 0 and h > 10:
			box(Vector3(4, 1.4, 3), Vector3(cos(a) * 15, h, sin(a) * 15), col.darkened(0.1), false, -a)


func _build_hollow_tree() -> void:
	var bark := Color("#4a3a2a")
	cyl(9, 6.5, 40, Vector3.ZERO, bark, true, 10)
	box(Vector3(5, 7, 4), Vector3(0, 0, 8.5), Color("#1a120c"), false)          # hollow opening
	for y in [14.0, 24.0, 33.0]:
		box(Vector3(14, 0.6, 6), Vector3(6, y, 6), Color("#7a5a3a"), true, 0.4)   # platforms
		box(Vector3(0.6, 0.6, 0.6), Vector3(11, y + 0.6, 8), Color("#ffcc66"), false, 0.0, 3.0)  # lanterns
	cyl(14, 4, 14, Vector3(0, 38, 0), Color("#3a5a30"), false, 9)
	cyl(10, 2, 10, Vector3(3, 47, -2), Color("#4a6a38"), false, 8)


func _build_dreadstone_pit() -> void:
	box(Vector3(16, 1.0, 16), Vector3(0, -0.6, 0), Color("#1c0608"), false)
	for i in 8:
		var a := i * TAU / 8.0
		var s := box(Vector3(1.2, 3.5 + (i % 3), 1.2), Vector3(cos(a) * 6.5, 0, sin(a) * 6.5), Color("#3a1014"), true, a)
		s.rotation.z = deg_to_rad(18 * (1 if i % 2 else -1))
	box(Vector3(9, 0.2, 9), Vector3(0, -0.05, 0), Color("#b0242c"), false, 0.0, 1.6)


func _build_log_bridge() -> void:
	var trunk := cyl(0.7, 0.7, 18, Vector3(0, 0.9, 0), Color("#6a4a2a"), true, 8)
	trunk.rotation.x = PI / 2.0
	trunk.position = Vector3(0, 0.9, 0)
	box(Vector3(1.2, 0.3, 17.5), Vector3(0, 1.5, 0), Color("#7a5a3a"))


func _build_obsidian_vent() -> void:
	for i in 7:
		var a := i * TAU / 7.0
		box(Vector3(3, 2 + (i % 3) * 1.5, 3), Vector3(cos(a) * 7, 0, sin(a) * 7), Color("#2a2030"), true, a)
	box(Vector3(5, 0.3, 5), Vector3(0, 0, 0), Color("#ff6a20"), false, 0.0, 2.2)
	box(Vector3(10, 7, 3), Vector3(0, 0, -9), Color("#3a3238"))               # cave mouth rock
	box(Vector3(4, 4.5, 0.4), Vector3(0, 0, -7.4), Color("#0e0a10"), false)


func _build_sunken_ruins() -> void:
	var col := Color("#5a6a5a")
	for i in 6:
		cyl(0.9, 0.8, 2.0 + (i % 3) * 2.2, Vector3(-8 + i * 3.2, -0.5, (i % 2) * 4.0), col, true, 8)
	box(Vector3(9, 2.5, 1.2), Vector3(0, -0.5, -4), col.darkened(0.1))


func _build_giant_stone_peak_cairn() -> void:
	box(Vector3(2.5, 1.2, 2.5), Vector3.ZERO, Color("#8a8e98"))
	box(Vector3(1.8, 1.0, 1.8), Vector3(0, 1.2, 0), Color("#9a9ea8"), true, 0.4)
	box(Vector3(1.1, 0.9, 1.1), Vector3(0, 2.2, 0), Color("#aab0b8"), true, 0.9)
