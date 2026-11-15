extends Node
## Chopping trees with the axe (resource_gathering.md section 5). A child of the player (imp_player.gd).
##
## With the axe in hand, walk up to a tree: the prompt shows "E  Chop Pine". Press E and the Imp steps to
## the trunk, faces it and keeps swinging the axe; every swing that lands shakes the tree and throws wood
## chips. After the tree's chop time (Lumbering.chop_time: the doc's time, faster with a better axe) the
## next hit fells it: the tree topples away from the Imp and its stump is left (scatter.gd), growing back
## after Lumbering.regrow seconds (5 minutes).
## E again, moving, or putting the axe away stops chopping; the tree keeps its progress.

const ToolFx := preload("res://scripts/player/tool_fx.gd")
## Where the axe head lands, in the Imp's own space at the hit of the "axe" use animation (metres:
## forward of the Imp's origin, and to its right). Measured with --chop_measure.
const HIT_FWD := 0.33
const HIT_SIDE := -0.36
const BITE := 0.8                 # the head lands this fraction of the trunk's radius from its centre

var player: CharacterBody3D
var visual: Node3D
var target := {}                  # tree in reach (for the prompt)
var chop := {}                    # tree being chopped
var live: Node3D                  # the chopped tree, lifted out of its MultiMesh
var need := 0.0                   # seconds this tree takes with this axe
var time_override := 0.0          # testing (--chop_time): every tree takes this long
var measure := false              # testing (--chop_measure): print where the axe head lands
var _away := Vector3.FORWARD      # from the Imp to the tree, flat
var _prompt := []


func _ready() -> void:
	player = get_parent()
	visual = player.get_node("visual")
	visual.struck.connect(_on_struck)


func _scatter() -> Scatter:
	return get_tree().get_first_node_in_group("scatter") as Scatter


func is_chopping() -> bool:
	return not chop.is_empty()


## E (use_tool): start or stop chopping. Returns false if there is nothing to chop, so the Imp just swings.
func use() -> bool:
	if is_chopping():
		stop()
		return true
	if Inventory.in_hand != "axe" or target.is_empty():
		return false
	var why := _blocker(target)
	if why != "":
		Inventory.message.emit(why)
		return false
	start(target)
	return true


func start(t: Dictionary) -> void:
	var sc := _scatter()
	if sc == null or t.is_empty():
		return
	chop = t
	live = sc.lift_tree(t)
	need = time_override if time_override > 0.0 else Lumbering.chop_time(t.tree, Inventory.held.axe)
	_step_up()
	visual.play_action("axe")


func stop() -> void:
	if measure:
		print("CHOP stopped")
	var sc := _scatter()
	if sc and not chop.is_empty():
		sc.drop_tree(chop, live)
	chop = {}
	live = null


## Steps the Imp to where its axe meets the bark, facing the tree.
func _step_up() -> void:
	var c: Vector3 = chop.xform.origin
	var u := Vector3(player.global_position.x - c.x, 0, player.global_position.z - c.z)
	if u.length() < 0.01:
		u = visual.global_basis.z
		u.y = 0
	u = u.normalized()
	_away = -u
	var right := _away.cross(Vector3.UP)
	var p := c + u * (float(chop.trunk) * BITE + HIT_FWD) - right * HIT_SIDE
	p.y = player.global_position.y
	if p.distance_to(player.global_position) < 1.6:
		player.velocity = Vector3.ZERO
		player.create_tween().tween_property(player, "global_position", p, 0.22).set_trans(Tween.TRANS_SINE)
	visual.rotation.y = atan2(-_away.x, -_away.z)


func _process(delta: float) -> void:
	if not is_chopping():
		_look_for_tree()
		return
	if not is_instance_valid(live) or not is_instance_valid(chop.mmi):
		chop = {}                 # the world changed under us; the progress is kept
		live = null
		return
	var moving := Input.get_vector("move_left", "move_right", "move_forward", "move_back").length() > 0.1 \
		or Input.is_action_pressed("jump")
	if moving or Inventory.in_hand != "axe" or player.frozen or player.menu_open():
		stop()
		return
	var done: float = Lumbering.progress.get(chop.key, 0.0) + delta
	Lumbering.progress[chop.key] = done
	visual.rotation.y = lerp_angle(visual.rotation.y, atan2(-_away.x, -_away.z), clampf(delta * 12.0, 0.0, 1.0))
	if not visual.is_busy():
		visual.play_action("axe")
	var pct := clampi(int(done / need * 100.0), 0, 100)
	_set_prompt("", "Chopping %s  %d%%" % [Lumbering.TREES[chop.tree].label, pct], "E", "Stop")


func _look_for_tree() -> void:
	var sc := _scatter()
	target = {}
	if sc and Inventory.in_hand == "axe" and not player.frozen and not player.menu_open():
		target = sc.find_tree(player.global_position, Lumbering.REACH)
	if target.is_empty():
		_set_prompt("", "")
		return
	var why := _blocker(target)
	if why != "":
		_set_prompt("", why)
	else:
		var secs := Lumbering.chop_time(target.tree, Inventory.held.axe)
		var done: float = Lumbering.progress.get(target.key, 0.0)
		var left := maxi(1, int(ceil(secs - done)))
		_set_prompt("E", "Chop %s  (%s)" % [Lumbering.TREES[target.tree].label, _clock(left)])


## Why this tree can't be chopped now ("Needs a Bronze axe", "Inventory full"), or "".
func _blocker(t: Dictionary) -> String:
	var why := Lumbering.blocker(t.tree, Inventory.held.axe)
	if why == "" and not Inventory.has_room(Lumbering.TREES[t.tree].log):
		why = "Inventory full"
	return why


static func _clock(s: int) -> String:
	return "%ds" % s if s < 60 else "%dm %02ds" % [s / 60, s % 60]


func _set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	var p := [key, text, key2, text2]
	if p == _prompt:
		return
	_prompt = p
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_prompt(key, text, key2, text2)


func _on_struck(kind: String, pos: Vector3) -> void:
	if measure:
		var l: Vector3 = visual.to_local(pos)
		print("CHOP head at hit: forward %.3f  right %.3f  up %.3f" % [-l.z, l.x, l.y])
	if kind != "axe" or not is_chopping() or not is_instance_valid(live):
		return
	if float(Lumbering.progress.get(chop.key, 0.0)) >= need:
		_fell()
	else:
		_shake()


## A short shake away from the Imp, settling back (the doc's 0.4 s tree `hit`).
func _shake() -> void:
	var node := live
	var xf: Transform3D = chop.xform
	var axis := Vector3.UP.cross(_away).normalized()
	var tilt := func(deg: float):
		if is_instance_valid(node):
			node.global_transform = Transform3D(Basis(axis, deg_to_rad(deg)) * xf.basis, xf.origin)
	var tw := node.create_tween()
	tw.tween_method(tilt, 0.0, 3.0, 0.05).set_ease(Tween.EASE_OUT)
	tw.tween_method(tilt, 3.0, -1.8, 0.11).set_trans(Tween.TRANS_SINE)
	tw.tween_method(tilt, -1.8, 0.8, 0.1).set_trans(Tween.TRANS_SINE)
	tw.tween_method(tilt, 0.8, 0.0, 0.14).set_trans(Tween.TRANS_SINE)


## The tree comes down: the stump appears, the tree topples away from the Imp and sinks out of sight.
func _fell() -> void:
	var t := chop
	var node := live
	if measure:
		print("CHOP felled %s after %.1f s" % [t.key, Lumbering.progress.get(t.key, 0.0)])
	chop = {}
	live = null
	var sc := _scatter()
	if sc:
		sc.fell(t)
	var xf: Transform3D = t.xform
	var s: float = t.scale
	var away := _away
	var axis := Vector3.UP.cross(away).normalized()
	var host := get_tree().current_scene
	ToolFx.burst(host, xf.origin + Vector3.UP * 0.55 * s, [Color(0.55, 0.37, 0.2), Color(0.8, 0.62, 0.4), Color(0.4, 0.26, 0.14)], 26, 3.4, 0.07)
	var fall := func(deg: float):
		if is_instance_valid(node):
			node.global_transform = Transform3D(Basis(axis, deg_to_rad(deg)) * xf.basis, xf.origin)
	var sink := func(f: float):
		if is_instance_valid(node):
			var b := Basis(axis, deg_to_rad(86.0)) * xf.basis
			node.global_transform = Transform3D(b.scaled_local(Vector3.ONE * maxf(f, 0.001)), xf.origin - Vector3.UP * (1.0 - f) * 0.6)
	var tw := node.create_tween()
	tw.tween_method(fall, 0.0, 6.0, 0.35).set_ease(Tween.EASE_OUT)                    # creaks over
	tw.tween_method(fall, 6.0, 86.0, 1.1).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(func():
		var land := xf.origin + away * 3.0 * s + Vector3.UP * 0.3
		ToolFx.burst(host, land, [Color(0.36, 0.5, 0.24), Color(0.5, 0.42, 0.3), Color(0.62, 0.58, 0.46)], 30, 2.6, 0.08))
	tw.tween_method(fall, 86.0, 82.0, 0.12).set_ease(Tween.EASE_OUT)                 # a little bounce
	tw.tween_method(fall, 82.0, 86.0, 0.12).set_ease(Tween.EASE_IN)
	tw.tween_interval(0.5)
	tw.tween_method(sink, 1.0, 0.0, 0.6).set_trans(Tween.TRANS_QUAD).set_ease(Tween.EASE_IN)
	tw.tween_callback(node.queue_free)
	Inventory.gain(Lumbering.TREES[t.tree].log)        # one log per tree (resource_gathering.md section 5)
	Inventory.message.emit("%s chopped down. It grows back in %d minutes." % [Lumbering.TREES[t.tree].label, int(Lumbering.regrow / 60.0)])
