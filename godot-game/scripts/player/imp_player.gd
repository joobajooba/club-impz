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


func _ready() -> void:
	floor_max_angle = deg_to_rad(46.0)
	floor_snap_length = 0.4
	camera_pivot.top_level = true
	camera_pivot.global_position = global_position + Vector3(0, 0.9, 0)
	spring_arm.add_excluded_object(get_rid())
	spring_arm.spring_length = target_zoom


func place_at(xform: Transform3D) -> void:
	## Teleport (used by portals and spawn points). Camera looks the way the marker faces.
	global_position = xform.origin
	velocity = Vector3.ZERO
	var fwd := -xform.basis.z
	cam_yaw = atan2(-fwd.x, -fwd.z)
	visual.rotation.y = cam_yaw
	camera_pivot.global_position = global_position + Vector3(0, 0.9, 0)


func _unhandled_input(event: InputEvent) -> void:
	if frozen:
		return  # world change fade or camera mode: the free camera owns the mouse and keys
	if event.is_action_pressed("toggle_fast_sprint"):
		fast_sprint = not fast_sprint
	if event is InputEventMouseMotion and Input.is_action_pressed("camera_orbit"):
		cam_yaw -= event.relative.x * orbit_sensitivity
		cam_pitch = clamp(cam_pitch - event.relative.y * orbit_sensitivity, -1.25, 0.45)
	elif event.is_action_pressed("camera_zoom_in"):
		target_zoom = max(zoom_min, target_zoom - 1.0)
	elif event.is_action_pressed("camera_zoom_out"):
		target_zoom = min(zoom_max, target_zoom + 1.0)


func _physics_process(delta: float) -> void:
	var input := Vector2.ZERO if frozen else Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var dir := (Basis(Vector3.UP, cam_yaw) * Vector3(input.x, 0, input.y))
	if dir.length() > 1.0:
		dir = dir.normalized()
	var speed := (sprint_speed * (5.0 if fast_sprint else 1.0)) if Input.is_action_pressed("sprint") else walk_speed
	var accel := acceleration if is_on_floor() else air_control
	var target := dir * speed
	velocity.x = move_toward(velocity.x, target.x, accel * speed * delta)
	velocity.z = move_toward(velocity.z, target.z, accel * speed * delta)
	if not is_on_floor():
		velocity.y -= gravity * delta
	elif Input.is_action_just_pressed("jump") and not frozen:
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
