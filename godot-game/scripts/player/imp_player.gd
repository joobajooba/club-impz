extends CharacterBody3D
## Third person imp controller: camera relative movement, smooth turning, gravity, jump,
## walk / sprint, slopes up to ~45 degrees, and a small walk bob. The camera rig is a
## top level SpringArm3D that follows smoothly, orbits with the right mouse button and zooms with the wheel.

@export var walk_speed := 4.0
@export var sprint_speed := 6.5
@export var acceleration := 14.0
@export var air_control := 4.0
@export var jump_velocity := 4.6
@export var turn_speed := 12.0
@export var zoom_min := 3.0
@export var zoom_max := 14.0
@export var orbit_sensitivity := 0.006

@onready var visual: Node3D = $visual
@onready var camera_pivot: Node3D = $camera_pivot
@onready var spring_arm: SpringArm3D = $camera_pivot/spring_arm
@onready var camera: Camera3D = $camera_pivot/spring_arm/camera

var gravity: float = ProjectSettings.get_setting("physics/3d/default_gravity")
var cam_yaw := 0.0
var cam_pitch := -0.32
var target_zoom := 7.5
var bob_time := 0.0
var frozen := false
var fast_sprint := false
var chopper: Node                 # scripts/player/tree_chopper.gd: chopping trees with the axe
var miner: Node                   # scripts/player/ore_miner.gd: mining the ore veins
## Footsteps (assets/sounds, made by build scripts/make_sounds.py): one per step of the walk bob, in the
## ground's sound for the biome underfoot; running steps are quicker, louder and a little higher.
const STEP_SOUNDS := {
	"grass": ["step_grass_1", "step_grass_2", "step_grass_3", "step_grass_4"],
	"snow": ["step_snow_1", "step_snow_2", "step_snow_3"],
	"stone": ["step_stone_1", "step_stone_2", "step_stone_3"],
}
const GROUND := {"frost": "snow", "mountain": "stone"}   # biome -> ground; everywhere else is grass
var _steps := {}                  # ground -> Array[AudioStream]
var _step_player: AudioStreamPlayer
var _last_step := 0


func _ready() -> void:
	floor_max_angle = deg_to_rad(46.0)
	floor_snap_length = 0.4
	camera_pivot.top_level = true
	camera_pivot.global_position = global_position + Vector3(0, 0.9, 0)
	spring_arm.add_excluded_object(get_rid())
	spring_arm.spring_length = target_zoom
	Settings.changed.connect(_apply_settings)
	_apply_settings()
	chopper = preload("res://scripts/player/tree_chopper.gd").new()
	chopper.name = "tree_chopper"
	add_child(chopper)
	miner = preload("res://scripts/player/ore_miner.gd").new()
	miner.name = "ore_miner"
	add_child(miner)
	for ground in STEP_SOUNDS:
		_steps[ground] = STEP_SOUNDS[ground].map(func(n): return load("res://assets/sounds/%s.wav" % n))
	_step_player = AudioStreamPlayer.new()
	_step_player.name = "footsteps"
	add_child(_step_player)


func _apply_settings() -> void:
	camera.fov = Settings.fov


func place_at(xform: Transform3D) -> void:
	## Teleport (used by portals and spawn points). Camera looks the way the marker faces.
	global_position = xform.origin
	velocity = Vector3.ZERO
	var fwd := -xform.basis.z
	cam_yaw = atan2(-fwd.x, -fwd.z)
	visual.rotation.y = cam_yaw
	camera_pivot.global_position = global_position + Vector3(0, 0.9, 0)


func menu_open() -> bool:
	## A modal menu (the character customizer, ...) is open: the imp stands still and the camera stays put.
	for n in get_tree().get_nodes_in_group("modal"):
		if n.visible:
			return true
	return false


func _unhandled_input(event: InputEvent) -> void:
	if frozen or menu_open():
		return  # world change fade or camera mode: the free camera owns the mouse and keys
	if event.is_action_pressed("toggle_fast_sprint"):
		fast_sprint = not fast_sprint
	if event.is_action_pressed("use_tool") and visual.has_method("play_action"):
		if not chopper.use() and not miner.use():        # E by a tree / event vein: chop it / mine it
			visual.play_action(Inventory.in_hand)        # left click or E: swing the tool in hand
	if event is InputEventMouseMotion and Input.is_action_pressed("camera_orbit"):
		var sens := orbit_sensitivity * Settings.mouse_sensitivity
		cam_yaw -= event.relative.x * sens
		cam_pitch = clamp(cam_pitch - event.relative.y * sens * (-1.0 if Settings.invert_y else 1.0), -1.25, 0.45)
	elif event.is_action_pressed("camera_zoom_in"):
		target_zoom = max(zoom_min, target_zoom - 1.0)
	elif event.is_action_pressed("camera_zoom_out"):
		target_zoom = min(zoom_max, target_zoom + 1.0)


func _physics_process(delta: float) -> void:
	var locked: bool = frozen or menu_open() or Chat.is_typing()   # typing in the chat box: stand still
	var input := Vector2.ZERO if locked else Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (Basis(Vector3.UP, cam_yaw) * Vector3(input.x, 0, input.y))
	if dir.length() > 1.0:
		dir = dir.normalized()
	var speed := (sprint_speed * (5.0 if fast_sprint else 1.0)) if Input.is_action_pressed("sprint") and not locked else walk_speed
	var accel := acceleration if is_on_floor() else air_control
	var target := dir * speed
	velocity.x = move_toward(velocity.x, target.x, accel * speed * delta)
	velocity.z = move_toward(velocity.z, target.z, accel * speed * delta)
	if not is_on_floor():
		velocity.y -= gravity * delta
	elif Input.is_action_just_pressed("jump") and not locked:
		velocity.y = jump_velocity
	move_and_slide()
	# safety net: never fall through the world
	if global_position.y < -60.0:
		global_position.y = 60.0
		velocity = Vector3.ZERO
	if dir.length() > 0.05:
		visual.rotation.y = lerp_angle(visual.rotation.y, atan2(-dir.x, -dir.z), clamp(turn_speed * delta, 0.0, 1.0))
	_animate(delta, Vector2(velocity.x, velocity.z).length())


func _animate(delta: float, ground_speed: float) -> void:
	var body := visual.get_node_or_null("body_root") as Node3D
	if body == null:
		return
	if is_on_floor() and ground_speed > 0.3:
		bob_time += delta * ground_speed * 3.2
		var step := floori(bob_time / TAU)                # one footstep every other bob (~2 a second walking)
		if step != _last_step:
			_last_step = step
			_footstep(ground_speed)
		body.position.y = abs(sin(bob_time)) * 0.05
		var squash := 1.0 + sin(bob_time * 2.0) * 0.04
		body.scale = Vector3(1.0 / sqrt(squash), squash, 1.0 / sqrt(squash))
	else:
		bob_time = 0.0
		body.position.y = lerp(body.position.y, 0.0, clamp(delta * 10.0, 0.0, 1.0))
		body.scale = body.scale.lerp(Vector3.ONE, clamp(delta * 10.0, 0.0, 1.0))


func _process(delta: float) -> void:
	var follow := global_position + Vector3(0, 0.9, 0)
	camera_pivot.global_position = camera_pivot.global_position.lerp(follow, clamp(delta * 12.0, 0.0, 1.0))
	camera_pivot.rotation = Vector3(cam_pitch, cam_yaw, 0)
	spring_arm.spring_length = lerp(spring_arm.spring_length, target_zoom, clamp(delta * 8.0, 0.0, 1.0))



func _footstep(ground_speed: float) -> void:
	var main := get_tree().get_first_node_in_group("game_main")
	var biome: String = main.biome_name_at(global_position) if main else "forest"
	var list: Array = _steps.get(GROUND.get(biome, "grass"), [])
	if list.is_empty():
		return
	var running := ground_speed > walk_speed * 1.25
	_step_player.stream = list[randi() % list.size()]
	_step_player.volume_db = -14.0 if running else -19.0
	_step_player.pitch_scale = randf_range(1.0, 1.08) if running else randf_range(0.94, 1.04)
	_step_player.play()

