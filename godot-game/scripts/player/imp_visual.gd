extends Node3D
## The player's Imp: the body and traits the player wears (Look.shown(), picked in the character
## customizer, game_menus.md section 3.5), built from the Blockbench trait models by ImpBuilder.
## Rebuilt whenever the look changes. Faces -z like the player controller expects.
## imp_player.gd bobs and squashes `body_root`; this script swings the arms and legs while walking.
## Other players' Imps (remote_imp.gd) use it too, with their own look (`set_look`) and speed: the parent
## only needs a `velocity` and an `is_on_floor()`.

## Blockbench units to metres: the body is about 101 units tall and the Imp stands 1.15 m.
const SCALE := 1.15 / 101.0
const SWING := {"R-Thigh": 1.0, "L-Thigh": -1.0, "R-Arm": -0.8, "L-Arm": 0.8}
const SWING_MAX := 0.55           # radians at full walking speed

var body_root: Node3D
var _model: Node3D
var _limbs := {}                  # Node3D -> [rest basis, swing sign]
var _phase := 0.0
var _amount := 0.0
var _custom_look = null           # another player's look; null = the local player's (Look.shown())

## Held tools (scripts/tools/held_tool.gd): the local player's Imp holds the tool in hand in its right fist.
## Tools are in Blockbench units at 16 per metre; the Imp model is SCALE metres per unit.
const HeldTool := preload("res://scripts/tools/held_tool.gd")
const TOOL_SCALE := 1.0 / 16.0 / SCALE
const CARRY_WRIST := -50.0        # degrees: at rest the tool points forward and up from the fist
## Use animations, one per tool kind: keyframes [time 0..1, arm pitch, arm yaw, arm roll, wrist, tool roll]
## in degrees, in the Imp's own space (pitch < 0 lifts the arm forward and up). The arm turns about the top
## of the arm; the wrist turns the tool in the fist.
const ACTIONS := {
	"pickaxe": {time = 0.75, keys = [[0, 0, 0, 0, -50, 0], [0.38, -165, 0, -8, -20, 0], [0.56, -40, 0, 0, 80, 0],
		[0.7, -35, 0, 0, 70, 0], [1, 0, 0, 0, -50, 0]]},
	"axe": {time = 0.7, keys = [[0, 0, 0, 0, -50, 0], [0.36, -150, 25, -30, -20, 0], [0.56, -55, -20, 15, 75, 0],
		[0.7, -50, -20, 10, 65, 0], [1, 0, 0, 0, -50, 0]]},
	"sword": {time = 0.55, keys = [[0, 0, 0, 0, -50, 0], [0.3, -85, 75, 0, 80, 90], [0.62, -85, -70, 0, 80, 90],
		[0.75, -70, -60, 0, 60, 60], [1, 0, 0, 0, -50, 0]]},
	"sickle": {time = 0.8, keys = [[0, 0, 0, 0, -50, 0], [0.22, -45, 60, 0, 45, 90], [0.45, -50, -55, 0, 45, 90],
		[0.62, -45, 40, 0, 45, 90], [0.8, -50, -40, 0, 45, 90], [1, 0, 0, 0, -50, 0]]},
	"rod": {time = 1.1, keys = [[0, 0, 0, 0, -50, 0], [0.32, -175, 0, 0, -10, 0], [0.48, -70, 0, 0, 40, 0],
		[0.85, -75, 0, 0, 35, 0], [1, 0, 0, 0, -50, 0]]},
}

var held_tool: Node3D
var _arm: Node3D                  # R-Arm: the use animations turn it
var _arm_rest: Transform3D
var _arm_parent := Basis()        # the arm's parent, in the Imp's own space, at rest
var _arm_pivot := Vector3.ZERO    # top of the arm cube, in the arm's parent's space
var _hand: Node3D                 # R-Hand: the tool hangs off it
var _hand_fix := Basis()          # undoes the arm chain's rest rotation, so the tool lines up with the Imp
var _action := ""
var _action_t := 0.0


func _ready() -> void:
	body_root = Node3D.new()
	body_root.name = "body_root"
	add_child(body_root)
	if _custom_look == null:
		Look.changed.connect(rebuild)
		Inventory.held_changed.connect(func(_id): _attach_tool())
	rebuild()


## Shows this look instead of the local player's (for other players). Call before or after adding.
func set_look(look: Dictionary) -> void:
	_custom_look = look
	if body_root:
		rebuild()


func rebuild() -> void:
	if _model:
		body_root.remove_child(_model)
		_model.queue_free()
	_model = ImpBuilder.build(_custom_look if _custom_look != null else Look.shown())
	_model.scale = Vector3.ONE * SCALE
	_model.rotation.y = PI                    # Blockbench's front is +z, the controller's is -z
	body_root.add_child(_model)
	_limbs.clear()
	for bone_name in SWING:
		var bone := _model.find_child(bone_name, true, false) as Node3D
		if bone:
			_limbs[bone] = [bone.basis, SWING[bone_name]]
	_action = ""
	_find_arm()
	if _custom_look == null:
		_attach_tool()


func _look() -> Dictionary:
	return _custom_look if _custom_look != null else Look.shown()


func _body_data() -> Dictionary:
	return ImpBuilder._model(ImpBuilder.entry("body", _look().get("body", "body_green")).get("model", ""))


## The arm and hand bones, and where they rest, read before anything moves them.
func _find_arm() -> void:
	held_tool = null
	_arm = _model.find_child("R-Arm", true, false) as Node3D
	_hand = _model.find_child("R-Hand", true, false) as Node3D
	if _arm == null or _hand == null:
		return
	_arm_rest = _arm.transform
	_arm_parent = _chain(_arm.get_parent())
	_hand_fix = _chain(_hand).inverse()
	var body := _body_data()
	var arm_box := _element(body, "R-Arm")
	var arm_bone = _bone_origin(body.get("bones", []), "R-Arm")
	if not arm_box.is_empty() and arm_bone != null:
		var top := Vector3((arm_box.from[0] + arm_box.to[0]) * 0.5, arm_box.to[1], (arm_box.from[2] + arm_box.to[2]) * 0.5)
		_arm_pivot = _arm_rest.origin + _arm_rest.basis * (top - arm_bone)


## The rest rotation of a bone, in the Imp model's own space.
func _chain(node: Node) -> Basis:
	var b := Basis()
	while node != null and node != _model:
		if node is Node3D:
			b = (node as Node3D).basis.orthonormalized() * b
		node = node.get_parent()
	return b


static func _element(model: Dictionary, el_name: String) -> Dictionary:
	for e in model.get("elements", []):
		if e.name == el_name:
			return e
	return {}


static func _bone_origin(nodes: Array, bone_name: String):
	for n in nodes:
		if n is Dictionary:
			if n.name == bone_name:
				return Vector3(n.origin[0], n.origin[1], n.origin[2])
			var found = _bone_origin(n.children, bone_name)
			if found != null:
				return found
	return null


## Puts the tool in hand (Inventory.in_hand) in the right fist.
func _attach_tool() -> void:
	if held_tool and is_instance_valid(held_tool):
		held_tool.queue_free()
	held_tool = null
	if _hand == null or not Inventory.held.has(Inventory.in_hand):
		return
	held_tool = HeldTool.make(Inventory.held[Inventory.in_hand])
	if held_tool == null:
		return
	_hand.add_child(held_tool)
	var body := _body_data()
	var fist := _element(body, "R-Hand")
	var hand_bone = _bone_origin(body.get("bones", []), "R-Hand")
	if not fist.is_empty() and hand_bone != null:
		held_tool.position = (Vector3(fist.from[0], fist.from[1], fist.from[2]) + Vector3(fist.to[0], fist.to[1], fist.to[2])) * 0.5 - hand_bone
	_pose_tool(CARRY_WRIST, 0.0)


## Wrist angle and roll about the tool's own handle, in degrees. With the wrist at 0 the tool's handle
## (+y) points forward and its head (+x) points up.
func _pose_tool(wrist: float, roll: float) -> void:
	if held_tool == null:
		return
	var b0 := Basis(Vector3(0, 1, 0), Vector3(0, 0, 1), Vector3(1, 0, 0))
	var b := _hand_fix * Basis(Vector3.RIGHT, deg_to_rad(wrist)) * b0 * Basis(Vector3.UP, deg_to_rad(roll))
	held_tool.basis = b * Basis.from_scale(Vector3.ONE * TOOL_SCALE)


## Plays the use animation for a tool kind (pickaxe, axe, sword, sickle, rod). Ignored while one plays.
func play_action(kind: String) -> void:
	if _arm == null or _action != "" or not ACTIONS.has(kind):
		return
	_action = kind
	_action_t = 0.0


func is_busy() -> bool:
	return _action != ""


func _run_action(delta: float) -> void:
	var a: Dictionary = ACTIONS[_action]
	_action_t += delta / a.time
	if _action_t >= 1.0:
		_action = ""
		_arm.transform = _arm_rest
		_pose_tool(CARRY_WRIST, 0.0)
		return
	var keys: Array = a.keys
	var i := 0
	while i < keys.size() - 2 and _action_t > keys[i + 1][0]:
		i += 1
	var k0: Array = keys[i]
	var k1: Array = keys[i + 1]
	var f := clampf((_action_t - k0[0]) / maxf(k1[0] - k0[0], 0.001), 0.0, 1.0)
	f = f * f * (3.0 - 2.0 * f)                                   # ease in and out
	var q := _pose_q(k0).slerp(_pose_q(k1), f)
	var m := _arm_parent.inverse() * Basis(q) * _arm_parent        # the turn, in the arm's parent's space
	_arm.transform = Transform3D(m * _arm_rest.basis, m * (_arm_rest.origin - _arm_pivot) + _arm_pivot)
	_pose_tool(lerpf(k0[4], k1[4], f), lerpf(k0[5], k1[5], f))


## Yaw, then roll, then pitch, in the Imp's space (+z forward, +y up).
static func _pose_q(k: Array) -> Quaternion:
	var b := Basis(Vector3.UP, deg_to_rad(k[2])) * Basis(Vector3.BACK, deg_to_rad(k[3])) * Basis(Vector3.RIGHT, deg_to_rad(k[1]))
	return b.get_rotation_quaternion()


func _process(delta: float) -> void:
	var body = get_parent()          # untyped: CharacterBody3D or remote_imp.gd
	if body == null or _limbs.is_empty() or not "velocity" in body:
		return
	var speed: float = Vector2(body.velocity.x, body.velocity.z).length()
	var target: float = clampf(speed / 4.0, 0.0, 1.0) if body.is_on_floor() else 0.3
	_amount = lerpf(_amount, target, clampf(delta * 8.0, 0.0, 1.0))
	_phase += delta * (3.0 + speed * 1.6)
	var swing := sin(_phase) * SWING_MAX * _amount
	for bone: Node3D in _limbs:
		if bone == _arm and _action != "":
			continue
		var rest: Basis = _limbs[bone][0]
		bone.basis = rest * Basis(Vector3.RIGHT, swing * _limbs[bone][1])
	if _action != "":
		_run_action(delta)
