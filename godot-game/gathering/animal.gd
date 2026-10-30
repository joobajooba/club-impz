class_name Animal
extends GatherNode
## A wild animal (D-028, D-067): it wanders near its home, three arrows make it go "poof" in a
## cartoon way, and it comes back after 10 seconds. It doesn't run away or fight back. It holds
## still while the player aims at it. It can be tamed with a dried bundle (D-071, see Stable).

const WANDER := 1.8          # metres from home
const SPEED := 0.45

var held := false            # the player is aiming at it
var ground_at: Callable      # (x, z) -> terrain height, to keep its feet on slopes
var _spawn := Vector3.ZERO
var _goal := Vector3.ZERO
var _wait := 0.0
var _step := 0.0
var _legs: Array = []


func setup_animal(tier_row: Dictionary) -> void:
	setup("hunting", tier_row, NodeArt.animal(tier_row))
	reach = 4.5
	_legs = _holder.find_children("*", "", true, false).filter(func(n): return n.is_in_group("leg"))


func _ready() -> void:
	super()
	_spawn = position
	_goal = position
	_wait = randf_range(0.5, 3.0)


func prompt() -> String:
	return "Hunt " + row.label


func strike() -> void:
	var t := create_tween()   # a startled little hop
	t.tween_property(_holder, "position:y", 0.12, 0.08)
	t.tween_property(_holder, "position:y", 0.0, 0.12)


## The cartoon poof: a burst of white puffs and the animal is gone.
func _break() -> void:
	broken = true
	_shape.set_deferred("disabled", true)
	_label.visible = false
	_holder.scale = Vector3.ONE * 0.001
	_throw_chips()
	get_tree().create_timer(GameData.RESPAWN).timeout.connect(_respawn)


## Tamed: the wild one hops away in a puff, and a copy joins the stable.
func tamed() -> void:
	_break()


func _respawn() -> void:
	position = _spawn
	_home = _spawn
	super()


func _process(delta: float) -> void:
	super(delta)
	if broken or held:
		return
	var to := _goal - position
	to.y = 0.0
	if to.length() < 0.05:
		_wait -= delta
		if _wait <= 0.0:
			var a := randf() * TAU
			_goal = _spawn + Vector3(cos(a), 0, sin(a)) * randf_range(0.3, WANDER)
			_goal.y = _spawn.y
			_wait = randf_range(1.5, 4.0)
		_step = 0.0
	else:
		var move := to.normalized() * minf(SPEED * delta, to.length())
		position += move
		if ground_at.is_valid():
			var g := (get_parent() as Node3D).to_global(position)
			position.y = (get_parent() as Node3D).to_local(Vector3(g.x, ground_at.call(g.x, g.z) - 0.03, g.z)).y
		_home = position
		rotation.y = lerp_angle(rotation.y, atan2(to.x, to.z), 1.0 - exp(-6.0 * delta))
		_step += delta * 9.0
	for i in _legs.size():
		(_legs[i] as Node3D).rotation.x = sin(_step + i * PI) * 0.5 if _step > 0.0 else 0.0
