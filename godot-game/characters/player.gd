extends CharacterBody3D
## Simple third-person controller.
## WASD to walk (relative to the camera). Hold right mouse button to orbit the camera, wheel to zoom.
## Shift ("sprint") doubles speed, Space ("jump") jumps, I ("inventory") toggles the inventory screen.
## Gathering (F, T, Q, the tools and their poses) is in the Gatherer child node (gatherer.gd).
## The impling.glb has no animations, so the walk cycle is procedural: legs, knees and arms swing via the skeleton.

@export var speed := 2.6
@export var sprint_multiplier := 2.0
@export var jump_velocity := 7.0      # ~1.2 m jump with gravity 20 (about 1.1 player-heights)
@export var turn_speed := 12.0
@export var gravity := 20.0
@export var stride_rate := 11.0       # how fast the legs cycle while walking
@export var leg_swing := 0.6          # radians
@export var knee_bend := 0.9
@export var arm_swing := 0.5
@export var bob_height := 0.03
@export var mouse_sensitivity := 0.005

@onready var model: Node3D = $Model
@onready var cam_pivot: Node3D = $CameraPivot
@onready var spring: SpringArm3D = $CameraPivot/SpringArm3D
@onready var anim: AnimationPlayer = $AnimationPlayer

var skel: Skeleton3D
var limbs: Array = []
var phase := 0.0
var walk_amount := 0.0
var model_base_y := 0.0
var spawn_point := Vector3.ZERO
var orbiting := false
var was_on_floor := true
var inventory_ui: Node
var inventory_open := false
var prev_mouse_mode := Input.MOUSE_MODE_VISIBLE

func _ready() -> void:
	spawn_point = global_position
	inventory_ui = get_tree().get_first_node_in_group("inventory_ui")
	if inventory_ui:
		inventory_ui.set("visible", false)
	spring.add_excluded_object(get_rid())
	model_base_y = model.position.y
	var found := model.find_children("*", "Skeleton3D", true, false)
	if found.is_empty():
		push_warning("Player: no Skeleton3D found in model, walk animation disabled.")
		return
	skel = found[0] as Skeleton3D
	# [bone, child bone (for direction), kind, phase offset]
	for spec in [
		["thigh_l", "calf_l", "leg", 0.0], ["thigh_r", "calf_r", "leg", PI],
		["calf_l", "foot_l", "knee", 0.0], ["calf_r", "foot_r", "knee", PI],
		["upperarm_l", "lowerarm_l", "arm", PI], ["upperarm_r", "lowerarm_r", "arm", 0.0],
	]:
		_add_limb(spec[0], spec[1], spec[2], spec[3])

func _add_limb(bone_name: String, child_name: String, kind: String, offset: float) -> void:
	var idx := skel.find_bone(bone_name)
	var child := skel.find_bone(child_name)
	if idx == -1 or child == -1:
		return
	var g := skel.get_bone_global_rest(idx)
	var dir := (skel.get_bone_global_rest(child).origin - g.origin).normalized()
	# Character forward (+Z of the model) expressed in skeleton space.
	var fwd := (skel.global_transform.basis.inverse() * model.global_transform.basis * Vector3.BACK).normalized()
	var axis_skel := dir.cross(fwd).normalized()   # rotating +angle about this swings the limb forward
	var axis_local := (g.basis.orthonormalized().inverse() * axis_skel).normalized()
	limbs.append({
		"idx": idx, "kind": kind, "offset": offset, "axis": axis_local,
		"rest": skel.get_bone_rest(idx).basis.get_rotation_quaternion(),
	})

func _toggle_inventory() -> void:
	inventory_open = not inventory_open
	if inventory_ui:
		inventory_ui.set("visible", inventory_open)
	if inventory_open:
		prev_mouse_mode = Input.mouse_mode
		Input.mouse_mode = Input.MOUSE_MODE_VISIBLE
		orbiting = false
	else:
		Input.mouse_mode = prev_mouse_mode

## True while a menu that takes the mouse and keys is open: the inventory or a "modal" menu
## (the stations, merchant, stable, battle board and dig).
func ui_open() -> bool:
	if inventory_open:
		return true
	if get_viewport().gui_get_focus_owner() is LineEdit:   # typing in a text box, e.g. the account form
		return true
	for m in get_tree().get_nodes_in_group("modal"):
		if m.visible:
			return true
	return false

func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("inventory") and not event.is_echo():
		_toggle_inventory()
		return
	if ui_open():
		return
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_RIGHT:
			orbiting = event.pressed
		elif event.button_index == MOUSE_BUTTON_WHEEL_UP and event.pressed:
			spring.spring_length = maxf(2.0, spring.spring_length - 0.4)
		elif event.button_index == MOUSE_BUTTON_WHEEL_DOWN and event.pressed:
			spring.spring_length = minf(12.0, spring.spring_length + 0.4)
	elif event is InputEventMouseMotion and orbiting:
		cam_pivot.rotation.y -= event.relative.x * mouse_sensitivity
		spring.rotation.x = clampf(spring.rotation.x - event.relative.y * mouse_sensitivity, -1.3, 0.2)

func _physics_process(delta: float) -> void:
	var locked := ui_open()
	var input := Vector2.ZERO
	if not locked:
		if Input.is_physical_key_pressed(KEY_W): input.y -= 1.0
		if Input.is_physical_key_pressed(KEY_S): input.y += 1.0
		if Input.is_physical_key_pressed(KEY_A): input.x -= 1.0
		if Input.is_physical_key_pressed(KEY_D): input.x += 1.0
	input = input.normalized()
	var cur_speed := speed
	if not locked and Input.is_action_pressed("sprint"):
		cur_speed = speed * sprint_multiplier

	var dir := Basis(Vector3.UP, cam_pivot.rotation.y) * Vector3(input.x, 0.0, input.y)
	if not is_on_floor():
		velocity.y -= gravity * delta
	elif not locked and Input.is_action_just_pressed("jump"):
		velocity.y = jump_velocity
		anim.play("jump")
	velocity.x = dir.x * cur_speed
	velocity.z = dir.z * cur_speed
	move_and_slide()

	var on_floor := is_on_floor()
	if on_floor and not was_on_floor and anim.current_animation == "jump":
		anim.play("RESET")   # landed: back to idle / walk
	was_on_floor = on_floor

	if dir.length() > 0.01:
		model.rotation.y = lerp_angle(model.rotation.y, atan2(dir.x, dir.z), turn_speed * delta)

	if global_position.y < -20.0:   # safety net
		global_position = spawn_point
		velocity = Vector3.ZERO

	var hspeed := Vector2(velocity.x, velocity.z).length()
	var moving := hspeed > 0.1 and on_floor
	walk_amount = move_toward(walk_amount, 1.0 if moving else 0.0, delta * 6.0)
	if moving:
		phase = fmod(phase + delta * stride_rate * (hspeed / speed), TAU)   # legs keep pace when sprinting
	elif walk_amount <= 0.0:
		phase = 0.0
	_animate()

func _animate() -> void:
	if skel == null:
		return
	for l in limbs:
		var p: float = phase + l.offset
		var a := 0.0
		match l.kind:
			"leg": a = leg_swing * sin(p)
			"knee": a = -knee_bend * maxf(0.0, cos(p))
			"arm": a = arm_swing * sin(p)
		skel.set_bone_pose_rotation(l.idx, l.rest * Quaternion(l.axis, a * walk_amount))
	model.position.y = model_base_y + abs(sin(phase)) * bob_height * walk_amount
