class_name GatherNode
extends StaticBody3D
## One thing to gather: an ore vein, a plant or a tree (Animal and FishingSpot build on it).
## `row` is its tier row in GameData.tiers[skill]. The player's Gatherer strikes it; harvest() gives
## the raw item (Inventory.gather), then it breaks and grows back after GameData.RESPAWN seconds
## (D-007, D-064, D-067, D-105, D-109).

const BREAK_TIME := 0.35
const DEBRIS_TIME := 0.9
const CHIP_GRAVITY := 14.0
const COLLIDER_TIGHTEN := 0.85   # a rock's footprint is smaller than its bounding box
const CHIP_COLOURS := {mining = "#6f6a64", lumbering = "#8a6a44", hunting = "#f4f2ec", fishing = "#e8f6ff"}

var skill := ""
var row: Dictionary
var radius := 0.5                # used by the Gatherer for reach
var reach := 0.0                 # extra reach: hunting and fishing work from a distance
var broken := false
var _holder := Node3D.new()      # scaled when it breaks and grows back
var _shape := CollisionShape3D.new()
var _label := Label3D.new()
var _home := Vector3.ZERO
var _shake := 0.0
var _chips: Array = []           # [MeshInstance3D, velocity, spin, life, size]


## `trunk` > 0 collides only with a trunk of that radius (trees), 0 with the model's footprint,
## and < 0 not at all (fishing spots).
func setup(skill_id: String, tier_row: Dictionary, model: Node3D, trunk := 0.0) -> void:
	skill = skill_id
	row = tier_row
	name = "%s_%s" % [skill, row.id]
	add_to_group("gather_target")
	add_child(_holder)
	_holder.add_child(model)
	var box := NodeArt.bounds(model)
	radius = trunk if trunk > 0.0 else maxf(box.size.x, box.size.z) * 0.5 * COLLIDER_TIGHTEN
	if trunk >= 0.0:
		var cylinder := CylinderShape3D.new()
		cylinder.radius = radius
		cylinder.height = maxf(box.size.y, 0.3)
		_shape.shape = cylinder
		_shape.position.y = cylinder.height * 0.5
		add_child(_shape)
	_label.text = row.label
	_label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_label.pixel_size = 0.004
	_label.font_size = 40
	_label.outline_size = 10
	_label.position.y = minf(box.end.y, 2.2) + 0.25
	_label.visibility_range_end = 8.0
	_label.visibility_range_end_margin = 1.0
	_label.visibility_range_fade_mode = GeometryInstance3D.VISIBILITY_RANGE_FADE_SELF
	add_child(_label)


func _ready() -> void:
	_home = position


## The prompt word and name, for example "Mine Tin".
func prompt() -> String:
	return GameData.SKILLS[skill].verb + " " + row.label


## Where the Gatherer aims (arrows, the fishing line).
func aim_point() -> Vector3:
	return global_position + Vector3(0, _shape.position.y if _shape.shape else 0.0, 0)


func strike() -> void:
	_home = position
	_shake = 0.18


func harvest() -> void:
	Inventory.gather(skill, row)
	_break()


func _break() -> void:
	broken = true
	_shake = 0.0
	position = _home
	if _shape.shape:
		_shape.set_deferred("disabled", true)
	_label.visible = false
	_throw_chips()
	var t := create_tween()
	t.tween_property(_holder, "scale", Vector3.ONE * 0.001, BREAK_TIME).set_ease(Tween.EASE_IN).set_trans(Tween.TRANS_QUAD)
	get_tree().create_timer(GameData.RESPAWN).timeout.connect(_respawn)


func _respawn() -> void:
	broken = false
	if _shape.shape:
		_shape.disabled = false
	_label.visible = true
	var t := create_tween()
	t.tween_property(_holder, "scale", Vector3.ONE, BREAK_TIME).set_ease(Tween.EASE_OUT).set_trans(Tween.TRANS_QUAD)


func _chip_colour() -> String:
	return row.get("stem", "") if skill == "foraging" else CHIP_COLOURS.get(skill, "#6f6a64")


func _throw_chips() -> void:
	var mesh := SphereMesh.new()
	mesh.radius = 0.05
	mesh.height = 0.08
	mesh.radial_segments = 5
	mesh.rings = 2
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color(_chip_colour())
	mat.roughness = 0.95
	mesh.material = mat
	var centre := Vector3(0, maxf(_shape.position.y, 0.2), 0)
	for i in 10:
		var chip := MeshInstance3D.new()
		chip.mesh = mesh
		chip.position = centre
		add_child(chip)
		var angle := i / 10.0 * TAU + randf() * 0.5
		var speed := randf_range(0.9, 2.0)
		var vel := Vector3(cos(angle) * speed, randf_range(1.8, 3.4), sin(angle) * speed)
		_chips.append([chip, vel, Vector3(randf(), randf(), randf()) * 10.0, 0.0, randf_range(0.6, 1.5)])


func _process(delta: float) -> void:
	if _shake > 0.0:
		_shake = maxf(0.0, _shake - delta)
		position = _home + Vector3(randf() - 0.5, 0.0, randf() - 0.5) * _shake * 0.25
		if _shake == 0.0:
			position = _home
	for i in range(_chips.size() - 1, -1, -1):
		var c: Array = _chips[i]
		var chip: MeshInstance3D = c[0]
		c[3] += delta
		c[1].y -= CHIP_GRAVITY * delta
		chip.position += c[1] * delta
		if chip.position.y < 0.04:
			chip.position.y = 0.04
			c[1] = Vector3(c[1].x * 0.5, absf(c[1].y) * 0.3, c[1].z * 0.5)
		chip.rotation += c[2] * delta
		chip.scale = Vector3.ONE * c[4] * clampf((DEBRIS_TIME - c[3]) / 0.25, 0.001, 1.0)
		if c[3] >= DEBRIS_TIME:
			chip.queue_free()
			_chips.remove_at(i)
