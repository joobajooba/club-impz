class_name FreeCamera
extends Camera3D
## Camera mode (key 7): fly around the map without the character.
## Local only: it moves this client's view, nothing else. The imp stays where it was (other players, and later the
## server, still see it standing there) and gets its controls back when camera mode is turned off.
##
## Move: W A S D. Up: Space. Down: C or Ctrl. Faster: hold Shift. Look: hold the right mouse button and drag.
## Mouse wheel: change the fly speed.

@export var speed := 18.0
@export var fast_multiplier := 4.0
@export var look_sensitivity := 0.004
@export var accel := 10.0

var yaw := 0.0
var pitch := 0.0
var velocity := Vector3.ZERO


func _ready() -> void:
	far = 2500.0  # the whole map fits when flying high
	var e := global_transform.basis.get_euler()
	pitch = e.x
	yaw = e.y
	rotation = Vector3(pitch, yaw, 0)


func _unhandled_input(event: InputEvent) -> void:
	if event is InputEventMouseMotion and Input.is_action_pressed("camera_orbit"):
		yaw -= event.relative.x * look_sensitivity
		pitch = clamp(pitch - event.relative.y * look_sensitivity, -1.55, 1.55)
		rotation = Vector3(pitch, yaw, 0)
	elif event.is_action_pressed("camera_zoom_in"):
		speed = minf(speed * 1.25, 400.0)
	elif event.is_action_pressed("camera_zoom_out"):
		speed = maxf(speed / 1.25, 2.0)


func _process(delta: float) -> void:
	var input := Input.get_vector("move_left", "move_right", "move_forward", "move_back")
	var up := Input.get_action_strength("jump") - Input.get_action_strength("camera_mode_down")
	var dir := global_transform.basis * Vector3(input.x, 0.0, input.y) + Vector3.UP * up
	if dir.length() > 1.0:
		dir = dir.normalized()
	var s := speed * (fast_multiplier if Input.is_action_pressed("sprint") else 1.0)
	velocity = velocity.lerp(dir * s, clampf(accel * delta, 0.0, 1.0))
	global_position += velocity * delta
