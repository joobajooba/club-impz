extends Node3D
## The tamed animal that follows the player (D-071), chosen in the stable. It trails a little behind
## and to the side, and its tier raises trophy chances while it follows (D-072, see Inventory.gather).

const DISTANCE := 1.4
const SPEED := 4.0

var _uid := -1
var _model: Node3D
var _legs: Array = []
var _step := 0.0


func _ready() -> void:
	Stable.changed.connect(_refresh)
	_refresh()


func _refresh() -> void:
	if Stable.follower == _uid:
		return
	_uid = Stable.follower
	if _model:
		_model.queue_free()
		_model = null
	var a := Stable.get_animal(_uid)
	if a.is_empty():
		return
	_model = NodeArt.animal(Stable.row(a))
	_model.scale = Vector3.ONE * 0.75
	add_child(_model)
	_legs = _model.find_children("*", "", true, false).filter(func(n): return n.is_in_group("leg"))
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if player:
		global_position = player.global_position + player.global_basis * Vector3(0.8, 0, -1.0)


func _physics_process(delta: float) -> void:
	var player := get_tree().get_first_node_in_group("player") as Node3D
	if _model == null or player == null:
		return
	var goal := player.global_position
	var to := goal - global_position
	to.y = 0.0
	var moving := to.length() > DISTANCE
	if moving:
		global_position += to.normalized() * minf(SPEED * delta, to.length() - DISTANCE)
		rotation.y = lerp_angle(rotation.y, atan2(to.x, to.z), 1.0 - exp(-8.0 * delta))
		_step += delta * 12.0
	global_position.y = lerpf(global_position.y, player.global_position.y, 1.0 - exp(-10.0 * delta))
	if to.length() > 25.0:   # left far behind: catch up
		global_position = player.global_position - to.normalized() * DISTANCE
	for i in _legs.size():
		(_legs[i] as Node3D).rotation.x = sin(_step + i * PI) * 0.5 if moving else 0.0
