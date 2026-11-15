extends Node3D
## Another player's Imp, made by Net (autoload/net.gd) for each player in the same world.
## It shows their look, with their name above, and moves smoothly between the positions the server
## sends (about 10 a second): it plays them back a little behind real time (DELAY) so there are always
## two to blend between, which hides the gaps between messages.
## It has no collider: players walk through each other (Proposed for the beta).

const ImpVisual := preload("res://scripts/player/imp_visual.gd")
const DELAY := 0.15               # seconds behind the newest position
const SNAP := 8.0                 # metres: a jump this big (a portal, a teleport) isn't blended

var id := 0
var velocity := Vector3.ZERO      # read by imp_visual.gd to swing the arms and legs
var visual: Node3D
var label: Label3D
var _states: Array = []           # [time, position, yaw, moving], oldest first
var _moving := 0
var _bob := 0.0


func _init(player_id: int, look: Dictionary, player_name: String) -> void:
	id = player_id
	name = "remote_%d" % player_id
	visual = ImpVisual.new()
	visual.name = "visual"
	visual.set_look(look)
	add_child(visual)
	label = Label3D.new()
	label.position = Vector3(0, 1.3, 0)  # moved to just over the head once the Imp is built (_fit_label)
	label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	# world sized (about 14 cm tall), so it is small but readable beside the Imp and gets smaller on screen
	# as the camera zooms out, never bigger
	label.fixed_size = false
	label.pixel_size = 0.0045
	label.font_size = 32
	label.outline_size = 8
	label.no_depth_test = false
	add_child(label)
	set_player_name(player_name, false)


func _ready() -> void:
	label.font = Settings.font()
	Settings.changed.connect(_on_settings_changed)
	_fit_label()


func _on_settings_changed() -> void:
	label.font = Settings.font()


## Puts the name just over the top of the Imp, whatever it wears (a tall hat or wings lift it).
func _fit_label() -> void:
	for i in 2:                             # the look is built over a frame
		await get_tree().process_frame
	if not is_inside_tree():
		return
	var top := 0.0
	var to_me := global_transform.affine_inverse()
	for m in visual.find_children("*", "VisualInstance3D", true, false):
		var box: AABB = (to_me * (m as VisualInstance3D).global_transform) * (m as VisualInstance3D).get_aabb()
		top = maxf(top, box.end.y)
	if top > 0.3:
		label.position.y = top + 0.14


func is_on_floor() -> bool:
	return _moving != 2


func set_look(look: Dictionary) -> void:
	visual.set_look(look)
	if is_inside_tree():
		_fit_label()


func set_player_name(player_name: String, guest: bool) -> void:
	label.text = player_name
	label.modulate = Color(0.85, 0.85, 0.85) if guest else Color(1.0, 0.86, 0.4)


## A position from the server. `now` is when it arrived, in seconds.
func push_state(now: float, pos: Vector3, yaw: float, moving: int) -> void:
	if _states.is_empty() or pos.distance_to(_states[-1][1]) > SNAP:
		_states = [[now - DELAY, pos, yaw, moving]]
		global_position = pos
		visual.rotation.y = yaw
	_states.append([now, pos, yaw, moving])
	if _states.size() > 20:
		_states.pop_front()


func _process(delta: float) -> void:
	if _states.is_empty():
		return
	var t := Time.get_ticks_msec() / 1000.0 - DELAY
	while _states.size() > 2 and _states[1][0] <= t:
		_states.pop_front()
	var a: Array = _states[0]
	var b: Array = _states[1] if _states.size() > 1 else a
	var span: float = b[0] - a[0]
	var k: float = clampf((t - a[0]) / span, 0.0, 1.0) if span > 0.0001 else 1.0
	var before := global_position
	global_position = (a[1] as Vector3).lerp(b[1], k)
	visual.rotation.y = lerp_angle(a[2], b[2], k)
	_moving = b[3]
	velocity = (global_position - before) / maxf(delta, 0.0001)
	if _moving == 0 and velocity.length() < 0.2:
		velocity = Vector3.ZERO
	_animate(delta)


## The same walk bob and squash as the local Imp (imp_player.gd).
func _animate(delta: float) -> void:
	var body := visual.get_node_or_null("body_root") as Node3D
	if body == null:
		return
	var speed := Vector2(velocity.x, velocity.z).length()
	if _moving == 1 and speed > 0.3:
		_bob += delta * speed * 3.2
		body.position.y = abs(sin(_bob)) * 0.05
		var squash := 1.0 + sin(_bob * 2.0) * 0.04
		body.scale = Vector3(1.0 / sqrt(squash), squash, 1.0 / sqrt(squash))
	else:
		_bob = 0.0
		body.position.y = lerp(body.position.y, 0.0, clampf(delta * 10.0, 0.0, 1.0))
		body.scale = body.scale.lerp(Vector3.ONE, clampf(delta * 10.0, 0.0, 1.0))
