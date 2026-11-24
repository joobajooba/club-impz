extends Node
## Headless test for the Imp's animation (scripts/player/imp_visual.gd). Run from the repo root:
##   godot --headless --path godot-game res://tests/test_imp_animation.tscn
## Every ACTIONS entry has its keys in order from t = 0 to t = 1, every tool kind has one, every swing plays to
## its end in its own time (plus the hit-stop), fires `struck` once per hit key, and leaves no broken pose;
## the walk fires `stepped` about three times a second; a jump and a held pose blend in. Exits with the failures.

const ImpVisual := preload("res://scripts/player/imp_visual.gd")


class FakeBody:
	extends Node3D
	var velocity := Vector3.ZERO
	var grounded := true

	func is_on_floor() -> bool:
		return grounded


var _fails := 0


func _ready() -> void:
	Save.enabled = false
	for kind in ImpVisual.ACTIONS:
		var keys: Array = ImpVisual.ACTIONS[kind].keys
		_ok(is_equal_approx(keys[0].t, 0.0) and is_equal_approx(keys[-1].t, 1.0), "%s runs from t = 0 to t = 1" % kind)
		for i in keys.size() - 1:
			_ok(keys[i].t < keys[i + 1].t, "%s key %d comes before key %d" % [kind, i, i + 1])
	for kind in ["pickaxe", "axe", "sickle", "sword", "rod"]:
		_ok(ImpVisual.ACTIONS.has(kind), "the %s has a use animation" % kind)
	var body := FakeBody.new()
	add_child(body)
	Inventory.in_hand = "pickaxe"
	var v: Node3D = ImpVisual.new()
	v.name = "visual"
	body.add_child(v)
	await get_tree().process_frame
	var strikes := [0]
	v.struck.connect(func(_k, _p): strikes[0] += 1)
	for kind in ["pickaxe", "axe", "sickle", "sword"]:
		Inventory.in_hand = kind
		v._attach_tool()
		strikes[0] = 0
		var hits := 0
		for k in ImpVisual.ACTIONS[kind].keys:
			hits += 1 if k.get("hit", false) else 0
		v.play_action(kind)
		_ok(v.is_busy(), "the %s swing starts" % kind)
		var start := Time.get_ticks_msec()
		while v.is_busy() and Time.get_ticks_msec() - start < 4000:
			await get_tree().process_frame
		var took := (Time.get_ticks_msec() - start) / 1000.0
		var want: float = ImpVisual.ACTIONS[kind].time + hits * ImpVisual.HIT_STOP
		_ok(not v.is_busy() and took < want + 0.5, "the %s swing ends in about %.2f s (took %.2f s)" % [kind, want, took])
		_ok(strikes[0] == hits, "the %s swing strikes %d time(s) (got %d)" % [kind, hits, strikes[0]])
		_ok(_pose_ok(v), "the %s swing leaves a clean pose" % kind)
	# walking: about two footfalls a second, and the hips and knees move
	var steps := [0]
	v.stepped.connect(func(_s): steps[0] += 1)
	body.velocity = Vector3(0, 0, -4.0)
	var thigh: Node3D = v._model.find_child("R-Thigh", true, false)
	var rest := thigh.transform
	await _seconds(2.0)
	_ok(steps[0] >= 4 and steps[0] <= 8, "walking makes 4 to 8 footfalls in 2 s (got %d)" % steps[0])
	_ok(not thigh.transform.is_equal_approx(rest), "the legs move while walking")
	_ok(_pose_ok(v), "walking leaves a clean pose")
	# a jump tucks the legs; a held pose blends in and out
	body.velocity = Vector3(0, 3.0, 0)
	body.grounded = false
	await _seconds(0.6)
	_ok(v._air > 0.9, "a jump blends in the air pose")
	body.grounded = true
	body.velocity = Vector3.ZERO
	await _seconds(0.6)
	_ok(v._air < 0.1, "landing blends it out")
	Inventory.in_hand = "rod"
	v._attach_tool()
	v.set_hold("rod_wait")
	await _seconds(0.8)
	_ok(v._over_w > 0.95, "the fishing pose blends in")
	v.set_hold("")
	await _seconds(0.8)
	_ok(v._over_w < 0.05, "and back out")
	_ok(_pose_ok(v), "no broken pose at the end")
	print("imp animation: %s" % ("all passed" if _fails == 0 else "%d failed" % _fails))
	get_tree().quit(_fails)


## Every bone transform is finite (no NaN from a bad blend).
func _pose_ok(v: Node3D) -> bool:
	for n in v.find_children("*", "Node3D", true, false):
		var t: Transform3D = (n as Node3D).transform
		if not (t.origin.is_finite() and t.basis.x.is_finite() and t.basis.y.is_finite() and t.basis.z.is_finite()):
			return false
	return true


func _seconds(s: float) -> void:
	var end := Time.get_ticks_msec() + int(s * 1000.0)
	while Time.get_ticks_msec() < end:
		await get_tree().process_frame


func _ok(cond: bool, what: String) -> void:
	if not cond:
		_fails += 1
		print("FAIL ", what)
