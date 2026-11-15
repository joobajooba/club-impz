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

# --- held tools and their use animations -------------------------------------------------------------
## The local player's Imp holds the tool in hand (scripts/tools/held_tool.gd) in its right fist.
## Tools are in Blockbench units at 16 per metre; the Imp model is SCALE metres per unit.
const HeldTool := preload("res://scripts/tools/held_tool.gd")
const ToolFx := preload("res://scripts/player/tool_fx.gd")
const TOOL_SCALE := 1.0 / 16.0 / SCALE
const CARRY_WRIST := -50.0        # degrees: at rest the tool points forward and up from the fist
## How each kind sits in the fist: the axe's blade and the sickle's hook face away from the Imp.
const HOLD_ROLL := {"axe": 180.0, "sickle": 180.0}
## Points on each tool (tool units from the grip, before HOLD_ROLL): the head that strikes, and a point
## further in. The swing trail runs between them; chips fly from the head.
const HEADS := {
	"pickaxe": [Vector3(-4.6, 5.0, 0), Vector3(-1.5, 6.6, 0)],
	"axe": [Vector3(4.2, 6.3, 0), Vector3(1.6, 6.3, 0)],
	"sickle": [Vector3(4.8, 5.0, 0), Vector3(2.4, 7.0, 0)],
	"sword": [Vector3(0, 11.6, 0), Vector3(0, 5.0, 0)],
	"rod": [Vector3(5.6, 10.6, 0), Vector3(2.0, 4.6, 0)],
}

## Use animations, one per tool kind. Each key is a pose at time t (0..1 of `time` seconds); between two
## keys the pose eases ("in": speeds up into the next key, a strike; "out": slows into it, a wind-up;
## default: in and out). All angles in degrees, in the Imp's own space:
##   arm   [pitch, yaw, roll] of the right arm, turning about the top of the arm (pitch < 0 lifts it
##         forward and up; yaw > 0 swings it across to the Imp's left)
##   wrist the tool's angle in the fist (0: handle points straight along the swing)   roll: about the handle
##   chest [twist, lean] of the upper body (twist > 0 turns to the left, lean > 0 leans back)
##   larm  the left arm swinging back (< 0) or forward (> 0) for balance   dip: metres the body sinks
##   hit   the moment of impact: chips fly from the head
## `trail`: the part of the swing that leaves a trail.
const ACTIONS := {
	"pickaxe": {time = 0.95, trail = [0.5, 0.7], keys = [
		{t = 0.0},
		{t = 0.12, arm = [-25, 0, 0], wrist = -62, chest = [0, 6], ease = "out"},
		{t = 0.42, arm = [-168, -8, -10], wrist = -18, chest = [-10, 14], larm = -30, ease = "out"},
		{t = 0.5, arm = [-174, -8, -10], wrist = -12, chest = [-10, 16], larm = -32},
		{t = 0.62, arm = [-42, 0, 0], wrist = 50, chest = [4, -16], larm = 22, dip = 0.06, ease = "in", hit = true},
		{t = 0.7, arm = [-52, 0, 0], wrist = 46, chest = [3, -12], larm = 16, dip = 0.04},
		{t = 1.0, ease = "out"},
	]},
	"axe": {time = 0.9, trail = [0.47, 0.66], keys = [
		{t = 0.0},
		{t = 0.1, arm = [-28, -20, -10], wrist = -58, chest = [-8, 4], ease = "out"},
		{t = 0.4, arm = [-158, -38, -38], wrist = -22, chest = [-28, 10], larm = -26, ease = "out"},
		{t = 0.48, arm = [-162, -40, -40], wrist = -16, chest = [-30, 11], larm = -28},
		{t = 0.6, arm = [-62, 26, 18], wrist = 66, chest = [22, -16], larm = 24, dip = 0.06, ease = "in", hit = true},
		{t = 0.7, arm = [-66, 30, 22], wrist = 60, chest = [24, -13], larm = 18, dip = 0.04},
		{t = 1.0, ease = "out"},
	]},
	"sword": {time = 0.72, trail = [0.28, 0.62], keys = [
		{t = 0.0},
		{t = 0.24, arm = [-78, -88, 6], wrist = 72, roll = -90, chest = [-32, 4], larm = 14, ease = "out"},
		{t = 0.3, arm = [-80, -92, 6], wrist = 76, roll = -90, chest = [-34, 4], larm = 16},
		{t = 0.5, arm = [-84, 70, -4], wrist = 84, roll = -90, chest = [30, -6], larm = -20, dip = 0.03, ease = "in", hit = true},
		{t = 0.64, arm = [-68, 96, -10], wrist = 62, roll = -80, chest = [36, -4], larm = -24},
		{t = 1.0, ease = "out"},
	]},
	"sickle": {time = 1.05, trail = [0.14, 0.8], keys = [
		{t = 0.0},
		{t = 0.16, arm = [-42, -62, 0], wrist = 42, roll = 90, chest = [-22, -12], larm = 10, dip = 0.04, ease = "out"},
		{t = 0.34, arm = [-50, 58, 0], wrist = 48, roll = 90, chest = [20, -14], larm = -12, dip = 0.05, ease = "in", hit = true},
		{t = 0.52, arm = [-42, -52, 0], wrist = 40, roll = 90, chest = [-18, -12], larm = 10, dip = 0.04},
		{t = 0.7, arm = [-50, 54, 0], wrist = 48, roll = 90, chest = [18, -14], larm = -12, dip = 0.05, ease = "in", hit = true},
		{t = 0.8, arm = [-46, 60, 0], wrist = 44, roll = 90, chest = [20, -12], larm = -10, dip = 0.04},
		{t = 1.0, ease = "out"},
	]},
	"rod": {time = 1.45, trail = [0.46, 0.64], keys = [
		{t = 0.0},
		{t = 0.15, arm = [-62, 0, 0], wrist = 18, ease = "out"},
		{t = 0.38, arm = [-176, -6, -4], wrist = -28, chest = [-10, 14], larm = -18, ease = "out"},
		{t = 0.46, arm = [-180, -6, -4], wrist = -32, chest = [-10, 16], larm = -20},
		{t = 0.58, arm = [-68, 6, 0], wrist = 46, chest = [6, -12], larm = 16, dip = 0.03, ease = "in"},
		{t = 0.68, arm = [-60, 4, 0], wrist = 34, chest = [4, -8], larm = 10},
		{t = 0.9, arm = [-58, 0, 0], wrist = 28, chest = [0, -4], larm = 4},
		{t = 1.0, ease = "out"},
	]},
}

var held_tool: Node3D
var _arm: Node3D                  # R-Arm: the use animations turn it
var _arm_rest: Transform3D
var _arm_parent := Basis()        # the arm's parent, in the Imp's own space, at rest
var _arm_pivot := Vector3.ZERO    # top of the arm cube, in the arm's parent's space
var _hand: Node3D                 # R-Hand: the tool hangs off it
var _hand_fix := Basis()          # undoes the arm chain's rest rotation, so the tool lines up with the Imp
var _chest: Node3D
var _chest_rest := Basis()
var _larm: Node3D
var _larm_rest := Basis()
var _action := ""
var _action_t := 0.0
var _trail: Node3D

## The tool's head struck at `pos` (the "hit" key of a use animation). tree_chopper.gd shakes the tree on it.
signal struck(kind: String, pos: Vector3)


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
	_end_action()
	_find_arm()
	if _custom_look == null:
		_attach_tool()


func _look() -> Dictionary:
	return _custom_look if _custom_look != null else Look.shown()


func _body_data() -> Dictionary:
	return ImpBuilder._model(ImpBuilder.entry("body", _look().get("body", "body_green")).get("model", ""))


## The arm, hand, chest and left arm bones, and where they rest, read before anything moves them.
func _find_arm() -> void:
	held_tool = null
	_arm = _model.find_child("R-Arm", true, false) as Node3D
	_hand = _model.find_child("R-Hand", true, false) as Node3D
	_chest = _model.find_child("Chest", true, false) as Node3D
	_larm = _model.find_child("L-Arm", true, false) as Node3D
	if _chest:
		_chest_rest = _chest.basis
	if _larm:
		_larm_rest = _larm.basis
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


func _kind() -> String:
	return Inventory.in_hand if _custom_look == null else ""


## Wrist angle and roll about the tool's own handle, in degrees. With the wrist at 0 the tool's handle
## (+y) points forward and its head (+x) points up; HOLD_ROLL turns the axe and sickle round.
func _pose_tool(wrist: float, roll: float) -> void:
	if held_tool == null:
		return
	var b0 := Basis(Vector3(0, 1, 0), Vector3(0, 0, 1), Vector3(1, 0, 0))
	var r: float = roll + float(HOLD_ROLL.get(_kind(), 0.0))
	var b := _hand_fix * Basis(Vector3.RIGHT, deg_to_rad(wrist)) * b0 * Basis(Vector3.UP, deg_to_rad(r))
	held_tool.basis = b * Basis.from_scale(Vector3.ONE * TOOL_SCALE)


# --- use animations -------------------------------------------------------------------------------------

## Plays the use animation for a tool kind (pickaxe, axe, sword, sickle, rod). Ignored while one plays.
func play_action(kind: String) -> void:
	if _arm == null or _action != "" or not ACTIONS.has(kind):
		return
	_action = kind
	_action_t = 0.0
	if held_tool and HEADS.has(kind):
		_trail = ToolFx.Trail.new()
		_trail.color = _trail_colour()
		get_tree().current_scene.add_child(_trail)


func is_busy() -> bool:
	return _action != ""


func _trail_colour() -> Color:
	var id: String = held_tool.id if held_tool else ""
	if id.begins_with("void"):
		return Color(0.78, 0.45, 1.0, 0.6)
	if id.begins_with("stellarite"):
		return Color(0.7, 0.9, 1.0, 0.65)
	if id.begins_with("dreadstone"):
		return Color(1.0, 0.55, 0.25, 0.55)
	return Color(1.0, 1.0, 0.95, 0.42)


func _end_action() -> void:
	_action = ""
	position.y = 0.0
	if _trail and is_instance_valid(_trail):
		var t := _trail
		get_tree().create_timer(0.3).timeout.connect(t.queue_free)
	_trail = null
	if _arm:
		_arm.transform = _arm_rest
	if _chest:
		_chest.basis = _chest_rest
	_pose_tool(CARRY_WRIST, 0.0)


func _run_action(delta: float) -> void:
	var a: Dictionary = ACTIONS[_action]
	var before := _action_t
	_action_t += delta / a.time
	if _action_t >= 1.0:
		_end_action()
		return
	var keys: Array = a.keys
	var i := 0
	while i < keys.size() - 2 and _action_t > keys[i + 1].t:
		i += 1
	var k0: Dictionary = keys[i]
	var k1: Dictionary = keys[i + 1]
	var f := clampf((_action_t - k0.t) / maxf(k1.t - k0.t, 0.001), 0.0, 1.0)
	match k1.get("ease", ""):
		"in": f = pow(f, 2.2)                         # speeds up into the strike
		"out": f = 1.0 - pow(1.0 - f, 2.2)            # slows into the wind-up
		_: f = f * f * (3.0 - 2.0 * f)
	# the right arm, about the top of the arm
	var q := _arm_q(k0).slerp(_arm_q(k1), f)
	var m := _arm_parent.inverse() * Basis(q) * _arm_parent
	_arm.transform = Transform3D(m * _arm_rest.basis, m * (_arm_rest.origin - _arm_pivot) + _arm_pivot)
	_pose_tool(lerpf(k0.get("wrist", CARRY_WRIST), k1.get("wrist", CARRY_WRIST), f), lerpf(k0.get("roll", 0.0), k1.get("roll", 0.0), f))
	# the body follows the swing
	if _chest:
		var c0: Array = k0.get("chest", [0, 0])
		var c1: Array = k1.get("chest", [0, 0])
		var tw := deg_to_rad(lerpf(c0[0], c1[0], f))
		var ln := deg_to_rad(lerpf(c0[1], c1[1], f))
		_chest.basis = _chest_rest * Basis(Vector3.UP, tw) * Basis(Vector3.RIGHT, -ln)
	if _larm:
		_larm.basis = _larm_rest * Basis(Vector3.RIGHT, deg_to_rad(-lerpf(k0.get("larm", 0.0), k1.get("larm", 0.0), f)))
	position.y = -lerpf(k0.get("dip", 0.0), k1.get("dip", 0.0), f)
	# trail and impact
	if held_tool and HEADS.has(_action):
		var head: Array = HEADS[_action]
		var tr: Array = a.trail
		if _trail and _action_t >= tr[0] and _action_t <= tr[1]:
			_trail.add(held_tool.to_global(head[0]), held_tool.to_global(head[1]))
		for k in keys:
			if k.get("hit", false) and before < k.t and _action_t >= k.t:
				_impact(held_tool.to_global(head[0]))


## Chips at the moment of impact.
func _impact(pos: Vector3) -> void:
	struck.emit(_action, pos)
	var host := get_tree().current_scene
	match _action:
		"pickaxe":
			ToolFx.burst(host, pos, [Color(0.42, 0.4, 0.38), Color(0.62, 0.6, 0.56), Color(0.5, 0.45, 0.38)], 16, 3.2, 0.06)
			ToolFx.burst(host, pos, [Color(1.0, 0.85, 0.4), Color(1.0, 0.6, 0.2)], 10, 4.5, 0.025, true)
		"axe":
			ToolFx.burst(host, pos, [Color(0.55, 0.37, 0.2), Color(0.78, 0.6, 0.38), Color(0.4, 0.26, 0.14)], 14, 3.0, 0.055)
		"sickle":
			ToolFx.burst(host, pos, [Color(0.3, 0.62, 0.22), Color(0.48, 0.78, 0.3), Color(0.7, 0.75, 0.3)], 12, 2.4, 0.045)
		"sword":
			ToolFx.burst(host, pos, [Color(1.0, 0.95, 0.75), Color(0.9, 0.95, 1.0)], 6, 2.0, 0.02, true)


## Yaw, then roll, then pitch of the arm, in the Imp's space (+z forward, +y up).
static func _arm_q(k: Dictionary) -> Quaternion:
	var a: Array = k.get("arm", [0, 0, 0])
	var b := Basis(Vector3.UP, deg_to_rad(a[1])) * Basis(Vector3.BACK, deg_to_rad(a[2])) * Basis(Vector3.RIGHT, deg_to_rad(a[0]))
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
		if _action != "" and (bone == _arm or bone == _larm):
			continue
		var rest: Basis = _limbs[bone][0]
		bone.basis = rest * Basis(Vector3.RIGHT, swing * _limbs[bone][1])
	if _action != "":
		_run_action(delta)
