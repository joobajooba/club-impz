extends Node
## Mining the ore veins with the pickaxe (resource_gathering.md section 4, the rules in scripts/world/mining.gd).
## A child of the player (imp_player.gd), next to tree_chopper.gd.
##
## Walk up to a vein with a pickaxe in hand: the prompt shows "E  Mine Copper (45s)", or what is missing
## ("Needs a Bronze pickaxe"). Press E and the Imp faces the vein and keeps swinging; every swing that lands
## throws chips.
## - An ordinary vein fills a bar over the doc's time to mine (faster with a better pickaxe). When it is full the
##   ore goes into the inventory, the gem may come with it, and the bar starts again: veins never run out.
## - Voidstone and stellarite event veins (autoload/ore_events.gd) are shared by everyone: every swing has a
##   chance to give the ore (about one per the time to mine), so no player holds the vein. When the event
##   ends the vein sinks away.
## E again, moving, or putting the pickaxe away stops. Progress on an ordinary vein is kept.

const ToolFx := preload("res://scripts/player/tool_fx.gd")
const CHIPS := {
	"coal": [Color("#1c1c22"), Color("#4a4e5c"), Color("#575b64")],
	"tin": [Color("#9ea4aa"), Color("#d6dbe0"), Color("#6b6f78")],
	"copper": [Color("#c4642e"), Color("#f28c52"), Color("#4e525b")],
	"iron": [Color("#60676f"), Color("#aab1b9"), Color("#5e4d43")],
	"gold": [Color("#e6b22a"), Color("#ffe27a"), Color("#6f645c")],
	"obsidian": [Color("#2b1f40"), Color("#6a4c9c"), Color("#24222d")],
	"titanite": [Color("#547ea2"), Color("#a8d4f0"), Color("#a7aaae")],
	"dreadstone": [Color("#6c1820"), Color("#b0242c"), Color("#2e3628")],
	"void": [Color("#4a1878"), Color("#a448e0"), Color("#2a2234")],
	"stellarite": [Color("#ecbc2c"), Color("#fff08c"), Color("#273457")],
}
const HIT_SOUNDS := ["res://assets/sounds/pick_hit_1.wav", "res://assets/sounds/pick_hit_2.wav", "res://assets/sounds/pick_hit_3.wav"]

var player: CharacterBody3D
var visual: Node3D
var target: Node3D               # vein in reach (for the prompt)
var vein: Node3D                 # the vein being mined
var chance_scale := 1.0          # testing (--mine_chance=20): multiplies the event veins' chance per swing
var time_override := 0.0         # testing (--mine_time=3): every ore takes this long
var mined := 0                   # ores from this vein so far (shown in the prompt)
var _last_hit := 0.0
var _prompt := []
var _hit_player: AudioStreamPlayer3D
var _hits: Array[AudioStream] = []


func _ready() -> void:
	player = get_parent()
	visual = player.get_node("visual")
	visual.struck.connect(_on_struck)
	OreEvents.ended.connect(func(_id): call_deferred("_check_vein"))
	for p in HIT_SOUNDS:
		if ResourceLoader.exists(p):
			_hits.append(load(p))
	_hit_player = AudioStreamPlayer3D.new()
	_hit_player.unit_size = 6.0
	_hit_player.max_distance = 40.0
	_hit_player.bus = "Master"
	add_child(_hit_player)


func is_mining() -> bool:
	return is_instance_valid(vein)


func _ore(v: Node3D) -> String:
	return str(v.get("ore"))


func _is_event(v: Node3D) -> bool:
	return v.is_in_group("event_vein")


## E (use_tool): start or stop mining. Returns false if there is nothing to mine, so the Imp just swings.
func use() -> bool:
	if is_mining():
		stop()
		return true
	if Inventory.in_hand != "pickaxe" or not is_instance_valid(target):
		return false
	var why := Mining.blocker(_ore(target), Inventory.held.pickaxe)
	if why != "":
		Inventory.message.emit(why)
		return false
	vein = target
	mined = 0
	_last_hit = Time.get_ticks_msec() / 1000.0
	_face()
	visual.play_action("pickaxe")
	return true


func stop() -> void:
	vein = null


func _check_vein() -> void:
	if is_mining() and _is_event(vein) == false and String(vein.name).contains("_event_"):
		Inventory.message.emit("The %s vein sank back into the ground." % Mining.ORES[_ore(vein)].label.to_lower())
		stop()


## Faces the vein and steps in so the pickaxe lands on the stone.
func _face() -> void:
	var c: Vector3 = vein.call("centre")
	var u := Vector3(player.global_position.x - c.x, 0, player.global_position.z - c.z)
	if u.length() < 0.01:
		u = Vector3.BACK
	u = u.normalized()
	var p: Vector3 = c + u * (float(vein.call("mound_radius")) + 0.45)
	p.y = player.global_position.y
	if p.distance_to(player.global_position) < 2.0:
		player.velocity = Vector3.ZERO
		player.create_tween().tween_property(player, "global_position", p, 0.22).set_trans(Tween.TRANS_SINE)
	visual.rotation.y = atan2(u.x, u.z)


func mine_time(ore: String) -> float:
	return time_override if time_override > 0.0 else Mining.mine_time(ore, Inventory.held.pickaxe)


func _process(delta: float) -> void:
	if not is_mining():
		_look_for_vein()
		return
	var moving := Input.get_vector("move_left", "move_right", "move_forward", "move_back").length() > 0.1 \
		or Input.is_action_pressed("jump")
	if moving or Inventory.in_hand != "pickaxe" or player.frozen or player.menu_open():
		stop()
		return
	if not visual.is_busy():
		visual.play_action("pickaxe")
	var ore := _ore(vein)
	var label: String = Mining.ORES[ore].label
	var got := ("  (%d mined)" % mined) if mined > 0 else ""
	if _is_event(vein):
		_set_prompt("", "Mining %s%s" % [label, got], "E", "Stop")
		return
	# an ordinary vein: the bar fills while mining; a full bar is one ore, then it starts again
	var key := String(vein.name)
	var done: float = Mining.progress.get(key, 0.0) + delta
	var need := mine_time(ore)
	if done >= need:
		var why := Mining.blocker(ore, Inventory.held.pickaxe)
		if why != "":
			Inventory.message.emit(why)
			stop()
			return
		done = 0.0
		Mining.give(ore)
		mined += 1
		ToolFx.burst(get_tree().current_scene, vein.call("centre") + Vector3.UP * 0.9, CHIPS.get(ore, [Color.WHITE]), 24, 3.2, 0.08)
	Mining.progress[key] = done
	_set_prompt("", "Mining %s  %d%%%s" % [label, int(done / need * 100.0), got], "E", "Stop")


func _look_for_vein() -> void:
	target = null
	if not player.frozen and not player.menu_open():
		var best := INF
		var me := player.global_position
		for v: Node3D in get_tree().get_nodes_in_group("ore_vein"):
			var o := v.global_position
			if absf(o.x - me.x) > 8.0 or absf(o.z - me.z) > 8.0:
				continue                                   # hundreds of veins: skip the far ones cheaply
			var c: Vector3 = v.call("centre")
			if absf(c.y - player.global_position.y) > 3.0:
				continue
			var d := Vector2(player.global_position.x - c.x, player.global_position.z - c.z).length() - float(v.call("mound_radius"))
			if d < Mining.REACH and d < best:
				best = d
				target = v
	if target == null:
		_set_prompt("", "")
		return
	var ore := _ore(target)
	var label: String = Mining.ORES[ore].label
	if Inventory.in_hand != "pickaxe":
		_set_prompt("", "%s vein: take out a pickaxe (1) to mine it" % label)
		return
	var why := Mining.blocker(ore, Inventory.held.pickaxe)
	if why != "":
		_set_prompt("", why)
	elif _is_event(target):
		_set_prompt("E", "Mine %s" % label)
	else:
		var left := maxi(1, int(ceil(mine_time(ore) - float(Mining.progress.get(String(target.name), 0.0)))))
		_set_prompt("E", "Mine %s  (%ds)" % [label, left])


func _set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	var p := [key, text, key2, text2]
	if p == _prompt:
		return
	_prompt = p
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_prompt(key, text, key2, text2)


## Every swing that lands: chips fly and the pick rings on the stone. On an event vein, a chance (the time
## since the last swing over the time per ore) to get the ore, rolled by each player for themselves.
func _on_struck(kind: String, pos: Vector3) -> void:
	if kind != "pickaxe" or not is_mining():
		return
	var ore := _ore(vein)
	var host := get_tree().current_scene
	ToolFx.burst(host, pos, CHIPS.get(ore, [Color.GRAY]), 10, 2.4, 0.06)
	if not _hits.is_empty():
		_hit_player.global_position = pos
		_hit_player.stream = _hits[randi() % _hits.size()]
		_hit_player.pitch_scale = randf_range(0.92, 1.08)
		_hit_player.play()
	if not _is_event(vein):
		return
	var now := Time.get_ticks_msec() / 1000.0
	var dt := clampf(now - _last_hit, 0.2, 3.0)
	_last_hit = now
	var why := Mining.blocker(ore, Inventory.held.pickaxe)
	if why != "":
		Inventory.message.emit(why)
		stop()
		return
	if randf() < minf(0.95, dt / mine_time(ore) * chance_scale):
		Mining.give(ore)
		mined += 1
		ToolFx.burst(host, pos + Vector3.UP * 0.2, CHIPS.get(ore, [Color.WHITE]), 26, 3.4, 0.08)
