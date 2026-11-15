extends Node3D
## A tool or weapon held in the Imp's hand: one of the Blockbench models in res://data/tools/
## (`build scripts/export_tools.py`, from build_pickaxes.py, build_axes.py and build_more_tools.py),
## built the same way ImpBuilder builds the Imp. Units are Blockbench units (16 per metre); the grip
## point sits at this node's origin, so the hand holds it there.
## A fishing rod's line (group "line", pivot at the rod tip) always hangs straight down, so the float dangles.
## Void and Stellarite pieces play their idle animation from the Blockbench files: the void shard bobs
## and spins and its emblem pulses; the stellarite star emblem turns and three sparkles twinkle.

const MANIFEST := "res://data/tools/manifest.json"

static var _manifest := {}

var id := ""
var _t := 0.0
var _parts := {}             # group name -> [node, rest position, rest basis]
var _line: Node3D
var _hang := Vector3.DOWN    # where the line points, in world space (a damped pendulum)
var _hang_v := Vector3.ZERO
var _tip_prev := Vector3.ZERO
var _tip_vel := Vector3.ZERO
var _tip_seen := false


## The line hangs from the rod tip like a pendulum: when the tip speeds up (a cast, a turn, walking)
## the float lags behind, swings past and settles straight down again.
func _swing_line(delta: float) -> void:
	if delta <= 0.0:
		return
	var tip := _line.global_position
	var accel := Vector3.ZERO
	if _tip_seen:
		var vel := (tip - _tip_prev) / delta
		accel = ((vel - _tip_vel) / delta).limit_length(60.0)
		_tip_vel = vel
	_tip_prev = tip
	_tip_seen = true
	var want := (Vector3(0, -9.8, 0) - accel).normalized()       # gravity as felt from the moving tip
	_hang_v += (want - _hang) * 55.0 * delta
	_hang_v *= exp(-5.0 * delta)
	_hang = (_hang + _hang_v * delta).normalized()
	var y := -_hang
	var x := y.cross(Vector3.FORWARD)
	if x.length() < 0.01:
		x = Vector3.RIGHT
	x = x.normalized()
	var z := x.cross(y).normalized()
	var s := _line.global_basis.get_scale()
	_line.global_basis = Basis(x * s.x, y * s.y, z * s.z)


static func manifest() -> Dictionary:
	if _manifest.is_empty():
		var data = JSON.parse_string(FileAccess.get_file_as_string(MANIFEST))
		_manifest = data if data is Dictionary else {}
	return _manifest


static func has_model(tool_id: String) -> bool:
	return manifest().has(tool_id)


## The held model for a tool id (e.g. "iron_pickaxe"), or null when it has none.
static func make(tool_id: String) -> Node3D:
	var e: Dictionary = manifest().get(tool_id, {})
	if e.is_empty():
		return null
	var h = load("res://scripts/tools/held_tool.gd").new()
	h.id = tool_id
	h.name = "held_tool"
	var inner := Node3D.new()
	inner.name = "model"
	var g: Array = e.grip
	inner.position = -Vector3(g[0], g[1], g[2])
	h.add_child(inner)
	ImpBuilder._add_model(ImpBuilder._model(e.model), ImpBuilder._material(e.texture, false), inner, {})
	for part in ["shard", "emblem", "sparkle_1", "sparkle_2", "sparkle_3"]:
		var n := inner.find_child(part, true, false) as Node3D
		if n:
			h._parts[part] = [n, n.position, n.basis]
	h._line = inner.find_child("line", true, false) as Node3D
	h.set_process(not h._parts.is_empty() or h._line != null)
	return h


func _process(delta: float) -> void:
	_t += delta
	if _line:
		_swing_line(delta)
	var stellar := id.begins_with("stellarite")
	for part in _parts:
		var n: Node3D = _parts[part][0]
		var pos: Vector3 = _parts[part][1]
		var rest: Basis = _parts[part][2]
		match part:
			"shard":                                   # 2 s: bob half a unit and spin once
				var k := fmod(_t, 2.0) / 2.0
				n.position = pos + Vector3(0, 0.5 * sin(k * PI), 0)
				n.basis = rest * Basis(Vector3.UP, k * TAU)
			"emblem":
				if stellar:                            # 3 s: a quarter turn and a pulse
					var k := fmod(_t, 3.0) / 3.0
					var s := 1.0 + 0.2 * sin(k * PI)
					n.basis = (rest * Basis(Vector3.BACK, k * PI * 0.5)).scaled_local(Vector3(s, s, 1))
				else:                                  # 2 s pulse
					var s := 1.0 + 0.18 * sin(fmod(_t, 2.0) / 2.0 * PI)
					n.basis = rest.scaled_local(Vector3(s, s, 1))
			_:                                         # sparkles twinkle in turn, one a second
				var i := int(part.right(1)) - 1
				var k := fmod(_t, 3.0) - i
				var s := 0.0
				if k >= 0.0 and k < 0.6:
					s = sin(k / 0.6 * PI)
				s = maxf(s, 0.01)
				n.basis = (rest * Basis(Vector3.BACK, clampf(k / 0.6, 0, 1) * PI / 4)).scaled_local(Vector3(s, s, s))
