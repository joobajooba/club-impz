extends Node3D
## The player's Imp: the body and traits the player wears (Look.shown(), picked in the character
## customizer, game_menus.md section 3.5), built from the Blockbench trait models by ImpBuilder.
## Rebuilt whenever the look changes. Faces -z like the player controller expects.
## imp_player.gd bobs and squashes `body_root`; this script swings the arms and legs while walking.

## Blockbench units to metres: the body is about 101 units tall and the Imp stands 1.15 m.
const SCALE := 1.15 / 101.0
const SWING := {"R-Thigh": 1.0, "L-Thigh": -1.0, "R-Arm": -0.8, "L-Arm": 0.8}
const SWING_MAX := 0.55           # radians at full walking speed

var body_root: Node3D
var _model: Node3D
var _limbs := {}                  # Node3D -> [rest basis, swing sign]
var _phase := 0.0
var _amount := 0.0


func _ready() -> void:
	body_root = Node3D.new()
	body_root.name = "body_root"
	add_child(body_root)
	Look.changed.connect(rebuild)
	rebuild()


func rebuild() -> void:
	if _model:
		body_root.remove_child(_model)
		_model.queue_free()
	_model = ImpBuilder.build(Look.shown())
	_model.scale = Vector3.ONE * SCALE
	_model.rotation.y = PI                    # Blockbench's front is +z, the controller's is -z
	body_root.add_child(_model)
	_limbs.clear()
	for bone_name in SWING:
		var bone := _model.find_child(bone_name, true, false) as Node3D
		if bone:
			_limbs[bone] = [bone.basis, SWING[bone_name]]


func _process(delta: float) -> void:
	var body := get_parent() as CharacterBody3D
	if body == null or _limbs.is_empty():
		return
	var speed := Vector2(body.velocity.x, body.velocity.z).length()
	var target := clampf(speed / 4.0, 0.0, 1.0) if body.is_on_floor() else 0.3
	_amount = lerpf(_amount, target, clampf(delta * 8.0, 0.0, 1.0))
	_phase += delta * (3.0 + speed * 1.6)
	var swing := sin(_phase) * SWING_MAX * _amount
	for bone: Node3D in _limbs:
		var rest: Basis = _limbs[bone][0]
		bone.basis = rest * Basis(Vector3.RIGHT, swing * _limbs[bone][1])
