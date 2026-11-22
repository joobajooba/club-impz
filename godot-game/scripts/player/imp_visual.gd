extends Node3D
## The player's Imp: the body and traits the player wears (Look.shown(), picked in the character
## customizer, game_menus.md section 3.5), built from the Blockbench trait models by ImpBuilder.
## Rebuilt whenever the look changes. Faces -z like the player controller expects.
## Other players' Imps (remote_imp.gd) use it too, with their own look (`set_look`) and speed: the parent
## only needs a `velocity` and an `is_on_floor()`.
##
## Everything moves in code, on the rig every body shares (no model changes):
## - Walk and run on one clock: hips, knees, arms and elbows swing with the steps, and the body's bounce and
##   squash land with each foot (`stepped` fires on each footfall for the footstep sounds). Speed blends the
##   walk into a run: longer strides, pumping arms, a forward lean.
## - Standing: breathing, glances around, and a tail that sways.
## - Follow-through: the head leads into turns, the body banks, the tail swings out and settles.
## - Jumps tuck the legs and lift the arms; landings squash and bend the knees.
## - Tool swings (ACTIONS) start from the pose the Imp is in, run on a smooth curve through their keys, hold
##   for HIT_STOP on each strike (D-137, off with Settings.reduce_motion) and blend back into the walk.
## - Held poses (HOLDS) for fishing: the rod out over the water, and tense on a bite.

## Blockbench units to metres: the body is about 101 units tall and the Imp stands 1.15 m.
const SCALE := 1.15 / 101.0
const WALK_SPEED := 4.0           # imp_player.gd walk_speed: above it the gait blends into a run
const RUN_SPEED := 6.5            # imp_player.gd sprint_speed
## The gait at a walk and at a run. Radians: hip swing, knee bend while the foot swings through, arm swing,
## elbow bend, forward lean; metres: bounce; squash: fraction of height.
const WALK := {hip = 0.5, knee = 0.62, arm = 0.42, elbow = 0.18, lean = 0.03, bob = 0.045, squash = 0.035}
const RUN := {hip = 0.8, knee = 1.2, arm = 0.62, elbow = 1.0, lean = 0.15, bob = 0.07, squash = 0.05}
const HIT_STOP := 0.05            # seconds a swing holds on each strike (D-137: 40 to 60 ms)

## A bone turned about a point on its own mesh: the rig's pivots don't sit at the joints on these bodies
## (the knee bone is half way down the shin), so knees and elbows bend about the top of their mesh.
class Joint:
	var node: Node3D
	var rest: Transform3D
	var pivot := Vector3.ZERO     # in the parent's space
	var into := Basis()           # the parent's rest rotation in the Imp's space

	## `b`: a rotation in the Imp model's own space (+z forward, +y up).
	func pose(b: Basis) -> void:
		var m := into.inverse() * b * into
		node.transform = Transform3D(m * rest.basis, m * (rest.origin - pivot) + pivot)

var body_root: Node3D
var _model: Node3D
var _custom_look = null           # another player's look; null = the local player's (Look.shown())
var _joints := {}                 # bone name -> Joint
var _phase := 0.0                 # the gait clock: one turn is two steps
var _amount := 0.0                # 0 standing .. 1 at walking speed and up
var _run := 0.0                   # 0 walking .. 1 running
var _t := 0.0
var _yaw_prev := 0.0
var _turn := 0.0                  # how fast the Imp is turning (radians a second, smoothed)
var _air := 0.0                   # 0 on the ground .. 1 in a jump
var _air_time := 0.0
var _vy := 0.0
var _land := 0.0                  # landing squash, 1 at touchdown
var _gaze := Vector2.ZERO         # head yaw, pitch (radians)
var _gaze_to := Vector2.ZERO
var _gaze_next := 0.0
var _tail := [0.0, 0.0, 0.0]      # each tail bone's swing, and its speed (a chain of springs)
var _tail_v := [0.0, 0.0, 0.0]
var _leg := 0.55                  # metres from the hip joint to the ground

## A footfall, for the footstep sounds (imp_player.gd).
signal stepped(speed: float)

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

## Use animations, one per tool kind. Each key is a pose at time t (0..1 of `time` seconds). Between keys the
## pose follows a smooth curve through them; "in" speeds up into the next key (a strike) and "out" slows into
## it (a wind-up), and the pose rests for a moment at those keys. The first key is wherever the Imp is when
## the swing starts. All angles in degrees, in the Imp's own space:
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
## Held poses (set_hold), in the same terms as an action key. The Imp eases into them and stays until cleared.
## `shake`: degrees the arm trembles (a fish pulling on the line).
const HOLDS := {
	"rod_wait": {arm = [-50, 6, -4], wrist = 54, chest = [4, -3], larm = 8},
	"rod_bite": {arm = [-86, 6, -4], wrist = 24, chest = [6, 8], larm = -6, shake = 3.0},
}

var held_tool: Node3D
var _hand: Node3D                 # R-Hand: the tool hangs off it
var _hand_fix := Basis()          # undoes the arm chain's rest rotation, so the tool lines up with the Imp
var _chest: Node3D
var _chest_rest := Basis()
var _action := ""
var _action_t := 0.0
var _hitstop := 0.0
var _trail: Node3D
var _hold := ""
var _over := {}                   # the action or held pose, as channels (_channels)
var _over_w := 0.0                # how much of it shows over the walk (0..1)
var _start := {}                  # the pose when the current action started (its first key)
var _final := {}                  # the pose shown last frame

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
	_yaw_prev = rotation.y


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
	_end_action()
	_over_w = 0.0
	_find_joints()
	if _custom_look == null:
		_attach_tool()


func _look() -> Dictionary:
	return _custom_look if _custom_look != null else Look.shown()


func _body_data() -> Dictionary:
	return ImpBuilder._model(ImpBuilder.entry("body", _look().get("body", ImpBuilder.DEFAULT.body)).get("model", ""))


## The bones that move and where they turn, read before anything moves them. Shoulders, hips, elbows and
## knees turn about the top of their own mesh, the neck about the bottom of the head, the tail about its bones.
func _find_joints() -> void:
	held_tool = null
	_joints.clear()
	for bone_name in ["R-Arm", "L-Arm", "R-Forearm", "L-Forearm", "R-Thigh", "L-Thigh", "R-Calf", "L-Calf"]:
		_joint(bone_name, "top")
	_joint("Head", "bottom")
	if _joints.has("R-Thigh"):
		_leg = maxf(0.2, (_joints["R-Thigh"] as Joint).pivot.y * SCALE)
	for bone_name in ["Tail", "Tail2", "Tail 3"]:
		_joint(bone_name, "origin")
	_hand = _model.find_child("R-Hand", true, false) as Node3D
	_chest = _model.find_child("Chest", true, false) as Node3D
	if _chest:
		_chest_rest = _chest.basis
	if _hand:
		_hand_fix = _chain(_hand).inverse()


func _joint(bone_name: String, where: String) -> void:
	var node := _model.find_child(bone_name, true, false) as Node3D
	if node == null:
		return
	var j := Joint.new()
	j.node = node
	j.rest = node.transform
	j.into = _chain(node.get_parent())
	j.pivot = j.rest.origin
	var mesh := node.get_node_or_null("mesh") as MeshInstance3D
	if mesh and where != "origin":
		var box := mesh.get_aabb()
		var c := box.get_center()
		var y := box.end.y - box.size.y * (0.0 if bone_name.ends_with("Arm") or bone_name.ends_with("Thigh") else 0.1)
		if where == "bottom":
			y = box.position.y
		j.pivot = j.rest * Vector3(c.x, y, c.z)
	_joints[bone_name] = j


func _pose(bone_name: String, b: Basis) -> void:
	var j: Joint = _joints.get(bone_name)
	if j:
		j.pose(b)


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


# --- use animations and held poses ------------------------------------------------------------------------

## Plays the use animation for a tool kind (pickaxe, axe, sword, sickle, rod). Ignored while one plays.
func play_action(kind: String) -> void:
	if _joints.is_empty() or _action != "" or not ACTIONS.has(kind):
		return
	_action = kind
	_action_t = 0.0
	_hitstop = 0.0
	_start = _final.duplicate() if not _final.is_empty() else _channels({})
	_over = _start.duplicate()
	_over_w = 1.0
	if held_tool and HEADS.has(kind):
		_trail = ToolFx.Trail.new()
		_trail.color = _trail_colour()
		get_tree().current_scene.add_child(_trail)


func is_busy() -> bool:
	return _action != ""


## Eases into a held pose (a HOLDS key, "" to let go). An action still plays over it.
func set_hold(hold_name: String) -> void:
	_hold = hold_name if HOLDS.has(hold_name) else ""


func _trail_colour() -> Color:
	var id: String = held_tool.id if held_tool else ""
	if id.begins_with("void"):
		return Color(0.78, 0.45, 1.0, 0.6)
	if id.begins_with("stellarite"):
		return Color(0.7, 0.9, 1.0, 0.65)
	if id.begins_with("dreadstone"):
		return Color(1.0, 0.55, 0.25, 0.55)
	return Color(1.0, 1.0, 0.95, 0.42)


## The swing is over: its last pose (at rest) blends back into the walk, or into the held pose.
func _end_action() -> void:
	_action = ""
	_hitstop = 0.0
	if _trail and is_instance_valid(_trail):
		var t := _trail
		get_tree().create_timer(0.3).timeout.connect(t.queue_free)
	_trail = null


## A key as channels: arm (pitch, yaw, roll), wrist, roll, chest (twist, lean), larm, dip.
static func _channels(k: Dictionary) -> Dictionary:
	var a: Array = k.get("arm", [0, 0, 0])
	var c: Array = k.get("chest", [0, 0])
	return {arm = Vector3(a[0], a[1], a[2]), wrist = float(k.get("wrist", CARRY_WRIST)), roll = float(k.get("roll", 0.0)),
			chest = Vector2(c[0], c[1]), larm = float(k.get("larm", 0.0)), dip = float(k.get("dip", 0.0))}


static func _mix(a: Dictionary, b: Dictionary, f: float) -> Dictionary:
	var out := {}
	for c in a:
		out[c] = lerp(a[c], b[c], f)
	return out


func _key(i: int) -> Dictionary:
	return _start if i == 0 else _channels(ACTIONS[_action].keys[i])


## The slope of the curve at key i (per unit of t): flat where the pose rests (the first and last keys, a
## wind-up, a strike), otherwise along the line from the key before to the key after.
func _slope(i: int) -> Dictionary:
	var keys: Array = ACTIONS[_action].keys
	var k: Dictionary = keys[i]
	var v := _key(i)
	var out := {}
	if i == 0 or i >= keys.size() - 1 or k.has("ease") or k.get("hit", false):
		for c in v:
			out[c] = v[c] * 0.0
		return out
	var a := _key(i - 1)
	var b := _key(i + 1)
	var dt: float = maxf(float(keys[i + 1].t) - float(keys[i - 1].t), 0.001)
	for c in v:
		out[c] = (b[c] - a[c]) / dt
	return out


## The action's pose now.
func _action_pose() -> Dictionary:
	var keys: Array = ACTIONS[_action].keys
	var i := 0
	while i < keys.size() - 2 and _action_t > keys[i + 1].t:
		i += 1
	var k1: Dictionary = keys[i + 1]
	var t0: float = keys[i].t
	var h: float = maxf(float(k1.t) - t0, 0.001)
	var f := clampf((_action_t - t0) / h, 0.0, 1.0)
	var v0 := _key(i)
	var v1 := _key(i + 1)
	match k1.get("ease", ""):
		"in": return _mix(v0, v1, pow(f, 2.2))                 # speeds up into the strike
		"out": return _mix(v0, v1, 1.0 - pow(1.0 - f, 2.2))    # slows into the wind-up
	var m0 := _slope(i)
	var m1 := _slope(i + 1)
	var f2 := f * f
	var f3 := f2 * f
	var out := {}
	for c in v0:
		out[c] = v0[c] * (2.0 * f3 - 3.0 * f2 + 1.0) + m0[c] * (h * (f3 - 2.0 * f2 + f)) \
			+ v1[c] * (3.0 * f2 - 2.0 * f3) + m1[c] * (h * (f3 - f2))
	return out


## Moves the action on. Returns true on the frame a strike lands (the swing then holds for HIT_STOP).
func _advance_action(delta: float) -> bool:
	if _hitstop > 0.0:
		_hitstop -= delta
		return false
	var a: Dictionary = ACTIONS[_action]
	var before := _action_t
	_action_t += delta / a.time
	for k in a.keys:
		if k.get("hit", false) and before < k.t and _action_t >= k.t:
			_action_t = k.t
			if not Settings.reduce_motion:
				_hitstop = HIT_STOP
			return true
	return false


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


## Yaw, then roll, then pitch of an arm, in degrees, in the Imp's space (+z forward, +y up).
static func _arm_basis(a: Vector3) -> Basis:
	return Basis(Vector3.UP, deg_to_rad(a.y)) * Basis(Vector3.BACK, deg_to_rad(a.z)) * Basis(Vector3.RIGHT, deg_to_rad(a.x))


# --- every frame ------------------------------------------------------------------------------------------

func _process(delta: float) -> void:
	var body = get_parent()          # untyped: CharacterBody3D or remote_imp.gd
	if body == null or _joints.is_empty() or not "velocity" in body:
		return
	var real_delta := delta                          # swings keep real time (rule A1); springs get a safe step
	delta = minf(delta, 0.05)
	_t += delta
	var v: Vector3 = body.velocity
	var speed := Vector2(v.x, v.z).length()
	var grounded: bool = body.is_on_floor()
	var calm := 0.5 if Settings.reduce_motion else 1.0
	_track_turn(delta)
	_track_air(delta, grounded, v.y)
	# the gait: one clock for the legs, the arms, the bounce and the footsteps
	var walking := clampf(speed / WALK_SPEED, 0.0, 1.0) if grounded and speed > 0.3 else 0.0
	_amount = lerpf(_amount, walking, 1.0 - exp(-delta * 10.0))
	if grounded:
		_run = lerpf(_run, clampf((speed - WALK_SPEED) / (RUN_SPEED - WALK_SPEED), 0.0, 1.0), 1.0 - exp(-delta * 6.0))
	var before := _phase
	if walking > 0.0:
		_phase += delta * (3.5 + 1.65 * speed)
	else:                                              # stopping: the legs come together
		_phase = lerpf(_phase, roundf(_phase / PI) * PI, 1.0 - exp(-delta * 8.0))
	if grounded and _amount > 0.3 and floorf((before - PI * 0.5) / PI) != floorf((_phase - PI * 0.5) / PI):
		stepped.emit(speed)
	var g := _mix(WALK, RUN, _run)
	var a := _amount
	var breath := sin(_t * 2.1)
	var tool_out := _kind() != "" and held_tool != null
	# legs: the knee bends as the foot swings through; in the air both tuck, on landing both give
	for side in [["R", 0.0, -0.4], ["L", PI, -0.1]]:
		var s := sin(_phase + side[1])
		var c := cos(_phase + side[1])
		var hip: float = -s * g.hip * a
		var knee: float = (g.knee * maxf(0.0, c) + 0.06) * a
		hip = lerpf(hip, side[2], _air) - _land * 0.35
		knee = lerpf(knee, 0.9, _air) + _land * 0.7
		_pose(side[0] + "-Thigh", Basis(Vector3.RIGHT, hip))
		_pose(side[0] + "-Calf", Basis(Vector3.RIGHT, knee))
	# arms swing against the legs; elbows bend more at a run; a tool in hand is carried in front
	var sr := sin(_phase)
	var loco := {
		arm = Vector3(rad_to_deg(sr * g.arm * a * (0.5 if tool_out else 1.0)) - 30.0 * _air, 0.0, -4.0 - breath * 1.5 - 28.0 * _air),
		wrist = CARRY_WRIST, roll = 0.0,
		chest = Vector2(-sr * 5.0 * a, breath * 1.2 * (1.0 - a)),
		larm = rad_to_deg(sr * g.arm * a) + 30.0 * _air, dip = 0.0,
	}
	var hit := false
	if _action != "":
		hit = _advance_action(real_delta)
		_over = _action_pose()
	else:
		var target := _channels(HOLDS[_hold]) if _hold != "" else {}
		if not target.is_empty():
			if _over_w < 0.01:
				_over = _final.duplicate() if not _final.is_empty() else loco.duplicate()
			_over = _mix(_over, target, 1.0 - exp(-delta * 9.0))
			_over_w = move_toward(_over_w, 1.0, delta * 8.0)
			var shake: float = HOLDS[_hold].get("shake", 0.0)
			if shake > 0.0:
				var arm: Vector3 = _over.arm
				arm.x = float(target.arm.x) + sin(_t * 38.0) * shake
				_over.arm = arm
		else:
			_over_w = move_toward(_over_w, 0.0, delta * 6.0)
	var pose: Dictionary = _mix(loco, _over, _over_w) if not _over.is_empty() else loco
	_final = pose
	_pose("R-Arm", _arm_basis(pose.arm))
	_pose("R-Forearm", Basis(Vector3.RIGHT, -(g.elbow * a + (0.35 if tool_out else 0.12) + 0.6 * _air) * (1.0 - _over_w)))
	_pose("L-Arm", Basis(Vector3.BACK, deg_to_rad(4.0 + breath * 1.5 + 28.0 * _air)) * Basis(Vector3.RIGHT, deg_to_rad(-pose.larm)))
	_pose("L-Forearm", Basis(Vector3.RIGHT, -(g.elbow * a + 0.12 + 0.6 * _air) * (1.0 - 0.6 * _over_w)))
	_pose_tool(pose.wrist, pose.roll)
	if _chest:
		var ch: Vector2 = pose.chest
		_chest.basis = _chest_rest * Basis(Vector3.UP, deg_to_rad(ch.x)) * Basis(Vector3.RIGHT, deg_to_rad(-ch.y))
	position.y = -float(pose.dip)
	if _action != "":
		_strike_fx(hit)
	_head(delta, a)
	_tail_follow(delta, a)
	# the body: the bounce lands with the feet, the squash with the bounce, a lean at a run and into turns
	var up := absf(cos(_phase))
	var stride: float = g.hip * a * absf(sin(_phase))
	var drop := _leg * (1.0 - cos(stride))            # the hips sink as the legs open, so the feet stay down
	body_root.position.y = g.bob * a * up * calm - drop
	var sy: float = 1.0 + (g.squash * a * (up * 2.0 - 1.0) + 0.012 * breath * (1.0 - a)) * calm - 0.22 * _land * calm \
		+ 0.06 * _air * clampf(_vy / 4.0, 0.0, 1.0) * calm
	body_root.scale = Vector3(1.0 / sqrt(sy), sy, 1.0 / sqrt(sy))
	body_root.rotation.x = -g.lean * a * calm
	body_root.rotation.z = clampf(_turn * speed * 0.03, -0.2, 0.2) * calm


## Trail and impact while a swing plays (`hit`: a strike landed this frame); ends the swing at its last key.
func _strike_fx(hit: bool) -> void:
	var a: Dictionary = ACTIONS[_action]
	if held_tool and HEADS.has(_action):
		var head: Array = HEADS[_action]
		var tr: Array = a.trail
		if _trail and _action_t >= tr[0] and _action_t <= tr[1]:
			_trail.add(held_tool.to_global(head[0]), held_tool.to_global(head[1]))
		if hit:
			_impact(held_tool.to_global(head[0]))
	if _action_t >= 1.0:
		_end_action()


func _track_turn(delta: float) -> void:
	var d := wrapf(rotation.y - _yaw_prev, -PI, PI)
	_yaw_prev = rotation.y
	_turn = lerpf(_turn, clampf(d / maxf(delta, 0.001), -8.0, 8.0), 1.0 - exp(-delta * 10.0))


## A jump: the pose blends in once the Imp has been off the ground a moment (not for every bump); landing
## after a real fall squashes the body.
func _track_air(delta: float, grounded: bool, vy: float) -> void:
	if grounded:
		if _air_time > 0.18:
			_land = clampf(-_vy / 7.0, 0.3, 1.0)
		_air_time = 0.0
	else:
		_air_time += delta
		_vy = vy
	var target := 1.0 if _air_time > 0.12 or (not grounded and absf(vy) > 2.0) else 0.0
	_air = move_toward(_air, target, delta * 7.0)
	_land = maxf(0.0, _land - delta * 4.5)


## The head: glances around while standing, looks ahead while walking, leads into turns and watches the
## work during a swing. It turns about the bottom of the head.
func _head(delta: float, a: float) -> void:
	if _action != "" or _hold != "":
		_gaze_to = Vector2(0.0, 0.14)
	elif a > 0.15:
		_gaze_to = Vector2.ZERO
		_gaze_next = _t + randf_range(1.5, 3.0)
	elif _t >= _gaze_next:
		_gaze_next = _t + randf_range(2.5, 5.5)
		_gaze_to = Vector2.ZERO if randf() < 0.35 else Vector2(randf_range(-0.45, 0.45), randf_range(-0.12, 0.08))
	_gaze = _gaze.lerp(_gaze_to, 1.0 - exp(-delta * 3.5))
	var yaw := _gaze.x + clampf(_turn * 0.1, -0.35, 0.35)
	var nod := _gaze.y + sin(_phase * 2.0) * 0.03 * a
	_pose("Head", Basis(Vector3.UP, yaw) * Basis(Vector3.RIGHT, nod))


## The tail: a chain of springs, each following the one before, so a swing runs down it and settles.
func _tail_follow(delta: float, a: float) -> void:
	var sway := sin(_t * 1.3) * 0.16 * (1.0 - a) + sin(_phase) * 0.12 * a - _turn * 0.16
	var lift := cos(_phase * 2.0) * 0.08 * a - 0.2 * _air
	var prev := 0.0
	for i in 3:
		var target := sway if i == 0 else float(_tail[i - 1])
		var acc := 70.0 * (target - float(_tail[i])) - 9.0 * float(_tail_v[i])
		_tail_v[i] = float(_tail_v[i]) + acc * delta
		_tail[i] = float(_tail[i]) + float(_tail_v[i]) * delta
		_pose(["Tail", "Tail2", "Tail 3"][i], Basis(Vector3.UP, float(_tail[i]) - prev) * Basis(Vector3.RIGHT, lift if i == 0 else 0.0))
		prev = float(_tail[i])
