extends Node
## Gathering for the player, as a child of Player. F next to a node gathers it, next to a station
## opens it; T next to an animal tries to tame it (D-071); Q switches between the owned tools of
## the kind in hand. The Imp takes out the right tool for the job, and the weakest owned one that
## reaches the tier if the held one doesn't (Proposed). Moving or jumping stops any action.
## - Mining, chopping: three overhead swings, the third breaks the node (D-007, D-105).
## - Picking: one crouch and pick (Proposed: the docs set the cost, not the motion).
## - Hunting: three shots from the bow, from up to a few metres away (D-067).
## - Fishing: cast, wait for a bite, then F again inside a short window (D-109).
## Godot runs this after the Player's own _physics_process, so its poses go on top of the walk.

const REACH := 0.35          # metres between the player's edge and the target's
const CHAR_RADIUS := 0.3
const SWINGS := 3
const SWING_TIME := 0.8
const STRIKE_AT := 0.6       # how far through a swing the tool hits
const PICK_TIME := 1.2
const SHOT_TIME := 0.9
const RELEASE_AT := 0.65     # how far through a shot the arrow flies
const ARROW_TIME := 0.25
const CAST_TIME := 0.7
const BITE_WAIT := Vector2(1.5, 4.0)   # seconds before a bite (TEST)
const BITE_WINDOW := 1.0               # seconds to press F (TEST)
const FADE_IN := 0.2
const FADE_OUT := 0.25
const PICKAXE_MODEL := "res://models/mining/pickaxe.glb"
const TOOL_SCALE := 0.5
## How each kind sits in the hand, from the rest pose, in character space: which hand, where the
## head and the handle point, and how far up the handle the hand grips.
const GRIPS := {
	"pickaxe": {hand = "hand_r", head = Vector3(0, 0.8, -0.6), handle = Vector3(0, 0.6, 0.8), grip = 0.18},
	"axe": {hand = "hand_r", head = Vector3(0, 0.8, -0.6), handle = Vector3(0, 0.6, 0.8), grip = 0.18},
	"sickle": {hand = "hand_r", head = Vector3(0, 0.8, -0.6), handle = Vector3(0, 0.6, 0.8), grip = 0.08},
	"rod": {hand = "hand_r", head = Vector3(0, 0.87, -0.5), handle = Vector3(0, 0.5, 0.87), grip = 0.12},
	"bow": {hand = "hand_l", head = Vector3(0, 0, 1), handle = Vector3(0, 1, 0), grip = 0.0},
}
## Bones the poses move, parents first. Player poses the upper arms itself every frame; the rest go
## back to their rest pose before each posed frame.
const POSE_BONES := ["spine_01", "head", "upperarm_r", "lowerarm_r", "hand_r", "upperarm_l", "lowerarm_l", "hand_l"]
const PLAYER_BONES := ["upperarm_r", "upperarm_l"]

@onready var player: CharacterBody3D = get_parent()
@onready var model: Node3D = player.get_node("Model")
var skel: Skeleton3D
var action := {}             # while busy: {kind, target, t, hits, fade, ...}
var _holders := {}           # "hand_r" / "hand_l" -> BoneAttachment3D
var _tool: Node3D            # the model in hand
var _tip: Node3D             # the rod's tip, for the fishing line
var _bobber: MeshInstance3D
var _line: MeshInstance3D
var _posed := false


func _ready() -> void:
	player.add_to_group("player")
	var found := model.find_children("*", "Skeleton3D", true, false)
	if found.is_empty():
		push_warning("Gatherer: no Skeleton3D in the player model, no tools or poses.")
		return
	skel = found[0]
	for hand in ["hand_r", "hand_l"]:
		var holder := BoneAttachment3D.new()
		holder.bone_name = hand
		skel.add_child(holder)
		_holders[hand] = holder
	_build_line()
	_show_tool(Inventory.held[Inventory.in_hand])
	Inventory.held_changed.connect(_show_tool)


func _unhandled_input(event: InputEvent) -> void:
	if player.ui_open() or not (event is InputEventKey or event is InputEventAction):
		return
	if event.is_action_pressed("interact") and not event.is_echo():
		_interact()
		get_viewport().set_input_as_handled()   # so a menu it opens doesn't see the same F
	elif event.is_action_pressed("tame") and not event.is_echo():
		var target := _target()
		if action.is_empty() and target is Animal:
			if Stable.tame(target.row):
				target.tamed()
	elif event.is_action_pressed("cycle_tool") and not event.is_echo() and action.is_empty():
		Inventory.cycle_held()


func _physics_process(delta: float) -> void:
	var weight := _update_action(delta) if not action.is_empty() else 0.0
	_apply_pose(weight)
	_update_line()
	_update_prompt()


# --- tools in hand ------------------------------------------------------------------

## Puts the tool's model in the right hand (the bow in the left), placed from the hand's rest pose
## so it doesn't matter where the player is facing.
func _show_tool(id: String) -> void:
	if skel == null:
		return
	if _tool:
		_tool.queue_free()
	var t: Dictionary = GameData.tools[id]
	var g: Dictionary = GRIPS[t.kind]
	if t.kind == "pickaxe":
		_tool = load(PICKAXE_MODEL).instantiate()
		_skin_pickaxe(_tool, t)
	else:
		_tool = ToolArt.model(t)
	_holders[g.hand].add_child(_tool)
	_tip = null
	if t.kind == "rod":
		_tip = Node3D.new()
		_tip.position.y = 2.2
		_tool.add_child(_tip)
	var idx := skel.find_bone(g.hand)
	var hand := skel.global_transform * skel.get_bone_global_rest(idx)
	var facing := model.global_basis.orthonormalized()
	var head_dir: Vector3 = facing * g.head.normalized()
	var handle_dir: Vector3 = facing * g.handle.normalized()
	var placed := Transform3D(Basis(head_dir, handle_dir, head_dir.cross(handle_dir)), hand.origin) \
			* Transform3D(Basis.from_scale(Vector3.ONE * TOOL_SCALE), Vector3.ZERO) \
			* Transform3D(Basis.IDENTITY, Vector3(0.0, -g.grip, 0.0))
	_tool.transform = hand.affine_inverse() * placed


## Colours or hides each part of the pickaxe by its Pick_<Part> material, from the skins file.
func _skin_pickaxe(pickaxe: Node3D, t: Dictionary) -> void:
	var skins: Dictionary = (load("res://models/mining/pickaxe-skins.json") as JSON).data
	var parts: Dictionary = skins.get(t.skin, {}).get("parts", {})
	for mi: MeshInstance3D in pickaxe.find_children("*", "MeshInstance3D", true, false):
		var src := mi.mesh.surface_get_material(0)
		var spec: Dictionary = parts.get(src.resource_name.trim_prefix("Pick_") if src else "", {})
		mi.visible = spec.get("visible", true)
		if not mi.visible:
			continue
		var mat := StandardMaterial3D.new()
		mat.albedo_color = Color(spec.get("color", "#ffffff"))
		mat.metallic = spec.get("metalness", 0.0)
		mat.roughness = spec.get("roughness", 0.8)
		mi.material_override = mat


# --- targets and the prompt -----------------------------------------------------------

## The closest node or station in reach, or null. Hunting and fishing reach further.
func _target() -> Node3D:
	var best: Node3D = null
	var best_gap := INF
	for t: Node3D in get_tree().get_nodes_in_group("gather_target"):
		if t is GatherNode and t.broken:
			continue
		var d := Vector2(t.global_position.x - player.global_position.x, t.global_position.z - player.global_position.z)
		var gap: float = d.length() - t.radius - CHAR_RADIUS
		var extra: float = t.reach if t is GatherNode else 0.0
		if gap < REACH + extra and gap < best_gap:
			best_gap = gap
			best = t
	return best


func _update_prompt() -> void:
	var hud := get_tree().get_first_node_in_group("hud")
	if hud == null:
		return
	if action.get("kind") == "cast" and action.fade < 0.0:
		match action.phase:
			"wait": hud.set_prompt("F", "Reel in (waiting for a bite…)")
			"bite": hud.set_prompt("F", "A bite! Reel in now!")
			_: hud.set_prompt("", "")
		return
	var target := _target() if action.is_empty() and player.is_on_floor() and not player.ui_open() else null
	if target is Station:
		hud.set_prompt("F", target.prompt())
	elif target is GatherNode:
		var blocker := Inventory.gather_blocker(target.skill, target.row) if _owned_reach(target) else _needs(target)
		var key2 := ""
		var text2 := ""
		if target is Animal:
			key2 = "T"
			var tb := Stable.tame_blocker(target.row)
			text2 = tb if tb else "Tame (%s, %d%%)" % [GameData.item_label(target.row.tame_with), roundi(target.row.tame_chance * 100)]
		hud.set_prompt("" if blocker else "F", blocker if blocker else target.prompt(), key2, text2)
	else:
		hud.set_prompt("", "")


func _owned_reach(target: GatherNode) -> bool:
	var kind: String = GameData.SKILLS[target.skill].tool
	return Inventory.owned[kind].any(func(id): return GameData.tools[id].reach >= target.row.tier)


func _needs(target: GatherNode) -> String:
	return "Needs a " + GameData.tool_for_tier(GameData.SKILLS[target.skill].tool, target.row.tier).label


func _interact() -> void:
	if action.get("kind") == "cast" and action.fade < 0.0:
		_reel()
		return
	if not player.is_on_floor() or (not action.is_empty() and action.fade < 0.0):
		return
	var target := _target()
	if target is Station:
		var menu := get_tree().get_first_node_in_group("menu_" + target.kind)
		if menu == null:
			menu = get_tree().get_first_node_in_group("station_menu")
		if menu:
			menu.open(target.kind)
		return
	if not target is GatherNode or not _owned_reach(target):
		return
	Inventory.pick_tool_for(target.skill, target.row)
	if Inventory.gather_blocker(target.skill, target.row) != "":
		return
	var kind := "swing"
	match target.skill:
		"foraging": kind = "pick"
		"hunting": kind = "shoot"
		"fishing": kind = "cast"
	action = {kind = kind, target = target, t = 0.0, hits = 0, fade = -1.0, phase = "cast", wait = 0.0}
	if target is Animal:
		target.held = true


# --- the actions -------------------------------------------------------------------

func _end_action() -> void:
	if action.is_empty() or action.fade >= 0.0:
		return
	action.fade = 0.0
	if action.target is Animal:
		action.target.held = false
	_bobber.visible = false


## Advances the action; returns its pose weight (0..1).
func _update_action(delta: float) -> float:
	action.t += delta
	var weight := minf(1.0, action.t / FADE_IN)
	if action.fade >= 0.0:
		action.fade += delta
		if action.fade >= FADE_OUT:
			action = {}
			return 0.0
		return weight * (1.0 - action.fade / FADE_OUT)
	if Vector2(player.velocity.x, player.velocity.z).length() > 0.1 or not player.is_on_floor():
		_end_action()
		return weight
	var target: GatherNode = action.target
	if target.broken and action.kind != "cast":
		_end_action()
		return weight
	var to := target.global_position - player.global_position
	model.rotation.y = lerp_angle(model.rotation.y, atan2(to.x, to.z), 1.0 - exp(-12.0 * delta))
	match action.kind:
		"swing":
			if action.hits < SWINGS and action.t >= (action.hits + STRIKE_AT) * SWING_TIME:
				action.hits += 1
				if action.hits < SWINGS:
					target.strike()
				else:
					target.harvest()
			if action.t >= SWINGS * SWING_TIME:
				_end_action()
		"pick":
			if action.hits == 0 and action.t >= PICK_TIME * 0.6:
				action.hits = 1
				target.harvest()
			if action.t >= PICK_TIME:
				_end_action()
		"shoot":
			if action.hits < SWINGS and action.t >= (action.hits + RELEASE_AT) * SHOT_TIME:
				action.hits += 1
				_fire_arrow(target, action.hits == SWINGS)
			if action.t >= SWINGS * SHOT_TIME:
				_end_action()
		"cast":
			_update_fishing(delta, target)
	return weight


func _update_fishing(delta: float, spot: FishingSpot) -> void:
	match action.phase:
		"cast":
			if action.t >= CAST_TIME:
				action.phase = "wait"
				action.wait = randf_range(BITE_WAIT.x, BITE_WAIT.y)
				_bobber.global_position = spot.global_position + Vector3(0, 0.03, 0)
				_bobber.visible = true
		"wait":
			action.wait -= delta
			_bobber.position.y = spot.global_position.y + 0.03 + sin(action.t * 3.0) * 0.015
			if action.wait <= 0.0:
				action.phase = "bite"
				action.wait = BITE_WINDOW
				spot.bite()
		"bite":
			action.wait -= delta
			_bobber.position.y = spot.global_position.y - 0.05
			if action.wait <= 0.0:
				Inventory.message.emit("It got away! Press F when the fish bites.")
				_end_action()


## F while fishing: a catch inside the bite window, otherwise reeling in empty.
func _reel() -> void:
	if action.phase == "bite":
		action.target.harvest()
	_end_action()


## An arrow from the bow hand to the animal. The last one makes it go poof.
func _fire_arrow(target: GatherNode, last: bool) -> void:
	var arrow := MeshInstance3D.new()
	var shaft := CylinderMesh.new()
	shaft.top_radius = 0.012
	shaft.bottom_radius = 0.012
	shaft.height = 0.45
	shaft.radial_segments = 5
	var mat := StandardMaterial3D.new()
	mat.albedo_color = Color("#d8c8a0")
	shaft.material = mat
	arrow.mesh = shaft
	get_tree().current_scene.add_child(arrow)
	var from := _holders.hand_l.global_position as Vector3
	var to := target.aim_point()
	arrow.global_position = from
	arrow.look_at_from_position(from, to, Vector3.UP)
	arrow.rotate_object_local(Vector3.RIGHT, PI / 2)   # the cylinder runs along Y
	var t := arrow.create_tween()
	t.tween_property(arrow, "global_position", to, ARROW_TIME)
	t.tween_callback(func():
		arrow.queue_free()
		if not is_instance_valid(target) or target.broken:
			return
		if last:
			target.harvest()
		else:
			target.strike())


# --- the fishing line ----------------------------------------------------------------

func _build_line() -> void:
	_line = MeshInstance3D.new()
	_line.mesh = ImmediateMesh.new()
	_line.top_level = true
	var lm := StandardMaterial3D.new()
	lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	lm.albedo_color = Color(0.95, 0.95, 0.9)
	_line.material_override = lm
	player.add_child.call_deferred(_line)
	_bobber = MeshInstance3D.new()
	var ball := SphereMesh.new()
	ball.radius = 0.05
	ball.height = 0.1
	var bm := StandardMaterial3D.new()
	bm.albedo_color = Color("#e83a2e")
	ball.material = bm
	_bobber.mesh = ball
	_bobber.top_level = true
	_bobber.visible = false
	player.add_child.call_deferred(_bobber)


func _update_line() -> void:
	var mesh := _line.mesh as ImmediateMesh
	mesh.clear_surfaces()
	if _tip == null or not is_instance_valid(_tip) or Inventory.in_hand != "rod":
		return
	var a := _tip.global_position
	var b := _bobber.global_position if _bobber.visible else a + Vector3(0, -0.5, 0)
	mesh.surface_begin(Mesh.PRIMITIVE_LINES)
	mesh.surface_add_vertex(a)
	mesh.surface_add_vertex(b)
	mesh.surface_end()


# --- poses ----------------------------------------------------------------------------

## Angles in radians around the character's own axes (x pitches forward), as in the Three.js test.
func _pose() -> Dictionary:
	var t: float = action.t
	match action.kind:
		"swing":
			var u := fmod(t, SWING_TIME) / SWING_TIME
			var raise := smoothstep(0.0, STRIKE_AT * 0.85, u) if u < STRIKE_AT else 1.0 - smoothstep(STRIKE_AT, STRIKE_AT + 0.08, u)
			var hit := 1.0 - raise
			# The Imp's head is bigger than its reach, so the tool comes up beside the head on the
			# right (arm out, body turned) instead of straight overhead, where the head hid it.
			return {
				spine_01 = Vector3(0.3 * hit - 0.12 * raise, -0.1 * hit - 0.4 * raise, 0),
				head = Vector3(-0.15 * raise + 0.15 * hit, 0, 0),
				upperarm_r = Vector3(-0.9 - 1.3 * raise, 0, 0.1 + 0.7 * raise),
				lowerarm_r = Vector3(-0.5 * raise, 0, 0),
				hand_r = Vector3(1.2 * hit + 1.8 * raise, 0, 0),
				upperarm_l = Vector3(-0.7 - 0.5 * raise, -0.3, 0.2),
				lowerarm_l = Vector3(-0.5 * raise, 0, 0.4),
			}
		"pick":
			var reach := sin(PI * clampf(t / PICK_TIME, 0.0, 1.0))
			return {
				spine_01 = Vector3(0.8 * reach, 0, 0),
				head = Vector3(-0.3 * reach, 0, 0),
				upperarm_r = Vector3(-1.0 * reach, 0, -0.1),
				upperarm_l = Vector3(-0.9 * reach, 0, 0.15),
				lowerarm_r = Vector3(-0.3 * reach, 0, 0),
			}
		"shoot":
			var u := fmod(t, SHOT_TIME) / SHOT_TIME
			var draw := smoothstep(0.1, RELEASE_AT, u) if u < RELEASE_AT else 1.0 - smoothstep(RELEASE_AT, RELEASE_AT + 0.1, u)
			return {
				spine_01 = Vector3(0, 0.25, 0),
				upperarm_l = Vector3(-1.5, 0.2, -0.6),   # out to the left, so the head doesn't hide the bow
				hand_l = Vector3(1.5, 0, 0),             # keeps the bow upright with the arm raised
				upperarm_r = Vector3(-1.35, -0.2, -0.2),
				lowerarm_r = Vector3(-1.7 * draw, 0, 0),
			}
		"cast":
			var u := clampf(t / CAST_TIME, 0.0, 1.0)
			var back := smoothstep(0.0, 0.45, u) if u < 0.45 else 1.0 - smoothstep(0.45, 0.6, u)
			var lift := 0.4 if action.phase == "bite" else 0.0
			return {
				upperarm_r = Vector3(-1.1 - 1.5 * back - lift, 0, -0.15),
				lowerarm_r = Vector3(-0.4, 0, 0),
				upperarm_l = Vector3(-0.8, 0, 0.2),
			}
	return {}


func _apply_pose(weight: float) -> void:
	if skel == null or (weight <= 0.0 and not _posed):
		return
	for name in POSE_BONES:
		var idx := skel.find_bone(name)
		if idx != -1 and not name in PLAYER_BONES:
			skel.set_bone_pose_rotation(idx, skel.get_bone_rest(idx).basis.get_rotation_quaternion())
	_posed = weight > 0.0
	if not _posed:
		return
	var pose := _pose()
	# Character space -> skeleton space.
	var to_skel := skel.global_basis.get_rotation_quaternion().inverse() * model.global_basis.get_rotation_quaternion()
	for name in POSE_BONES:
		var idx := skel.find_bone(name)
		if idx == -1 or not pose.has(name):
			continue
		var turn := Basis.from_euler(pose[name] * weight, EULER_ORDER_ZXY).get_rotation_quaternion()
		var parent := skel.get_bone_parent(idx)
		var parent_q := skel.get_bone_global_pose(parent).basis.get_rotation_quaternion() if parent != -1 else Quaternion.IDENTITY
		var in_skel := to_skel * turn * to_skel.inverse()
		skel.set_bone_pose_rotation(idx, parent_q.inverse() * in_skel * parent_q * skel.get_bone_pose_rotation(idx))
