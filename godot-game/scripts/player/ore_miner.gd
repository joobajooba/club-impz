extends Node
## Mining the event ore veins (voidstone and stellarite, autoload/ore_events.gd) with the pickaxe.
## A child of the player (imp_player.gd), next to tree_chopper.gd.
##
## Walk up to an event vein with a pickaxe in hand: the prompt shows "E  Mine Voidstone". Press E and the
## Imp faces the vein and keeps swinging. The vein is never locked to one player: everyone near it mines
## at once, and every swing that lands has a chance to give the ore, about one ore per the doc's time to
## mine (resource_gathering.md 4.1: voidstone 600 s with a dreadstone pickaxe, stellarite 1000 s with a
## voidstone one; 5% faster for every pickaxe tier above that, section 2.3). An ore goes through
## Inventory.gather (5 energy, the raw ore and the gem roll: arcanium / eclipsium).
## E again, moving, or putting the pickaxe away stops. When the event ends the vein sinks away.

const ToolFx := preload("res://scripts/player/tool_fx.gd")
const TIME := {"void": 600.0, "stellarite": 1000.0}   # seconds per ore with the minimum pickaxe
const SPEED_PER_TIER := 0.05
const REACH := 2.0               # metres from the side of the mound to start mining
const CHIPS := {
	"void": [Color("#4a1878"), Color("#a448e0"), Color("#2a2234")],
	"stellarite": [Color("#ecbc2c"), Color("#fff08c"), Color("#273457")],
}

var player: CharacterBody3D
var visual: Node3D
var target: Node3D               # event vein in reach (for the prompt)
var vein: Node3D                 # the vein being mined
var chance_scale := 1.0          # testing (--mine_chance=20): multiplies the chance per swing
var mined := 0                   # ores from this vein so far (shown in the prompt)
var _last_hit := 0.0
var _prompt := []


func _ready() -> void:
	player = get_parent()
	visual = player.get_node("visual")
	visual.struck.connect(_on_struck)
	OreEvents.ended.connect(func(_id): call_deferred("_check_vein"))


func is_mining() -> bool:
	return is_instance_valid(vein)


func _row(v: Node3D) -> Dictionary:
	return GameData.tier_row("mining", str(v.get("ore")))


## E (use_tool): start or stop mining. Returns false if there is nothing to mine, so the Imp just swings.
func use() -> bool:
	if is_mining():
		stop()
		return true
	if Inventory.in_hand != "pickaxe" or not is_instance_valid(target):
		return false
	var why := Inventory.gather_blocker("mining", _row(target))
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
	if is_mining() and not vein.is_in_group("event_vein"):
		Inventory.message.emit("The %s vein sank back into the ground." % OreEvents.label(str(vein.get("ore"))).to_lower())
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


## Seconds per ore with the pickaxe in hand.
func mine_time(ore: String) -> float:
	var row := GameData.tier_row("mining", ore)
	var list: Array = GameData.tools_of["pickaxe"]
	var held := list.find(GameData.tools[Inventory.held.pickaxe])
	var need := list.find(GameData.tool_for_tier("pickaxe", int(row.tier)))
	return float(TIME.get(ore, 600.0)) * maxf(0.2, 1.0 - SPEED_PER_TIER * maxi(0, held - need))


func _process(_delta: float) -> void:
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
	var label := OreEvents.label(str(vein.get("ore")))
	_set_prompt("", "Mining %s%s" % [label, ("  (%d mined)" % mined) if mined > 0 else ""], "E", "Stop")


func _look_for_vein() -> void:
	target = null
	if not player.frozen and not player.menu_open():
		var best := INF
		for v: Node3D in get_tree().get_nodes_in_group("event_vein"):
			var c: Vector3 = v.call("centre")
			var d := Vector2(player.global_position.x - c.x, player.global_position.z - c.z).length() - float(v.call("mound_radius"))
			if d < REACH and d < best:
				best = d
				target = v
	if target == null:
		_set_prompt("", "")
		return
	var label := OreEvents.label(str(target.get("ore")))
	if Inventory.in_hand != "pickaxe":
		_set_prompt("", "%s vein: mine it with a pickaxe (1)" % label)
		return
	var why := Inventory.gather_blocker("mining", _row(target))
	if why != "":
		_set_prompt("", why)
	else:
		_set_prompt("E", "Mine %s" % label)


func _set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	var p := [key, text, key2, text2]
	if p == _prompt:
		return
	_prompt = p
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_prompt(key, text, key2, text2)


## Every swing that lands: chips fly, and a chance (the time since the last swing over the time per ore)
## to get the ore. Rolled by each player for themselves, so any number of players can mine one vein.
func _on_struck(kind: String, pos: Vector3) -> void:
	if kind != "pickaxe" or not is_mining():
		return
	var ore := str(vein.get("ore"))
	var now := Time.get_ticks_msec() / 1000.0
	var dt := clampf(now - _last_hit, 0.2, 3.0)
	_last_hit = now
	var host := get_tree().current_scene
	ToolFx.burst(host, pos, CHIPS.get(ore, [Color.GRAY]), 10, 2.4, 0.06)
	var row := _row(vein)
	var why := Inventory.gather_blocker("mining", row)
	if why != "":
		Inventory.message.emit(why)
		stop()
		return
	if randf() < minf(0.95, dt / mine_time(ore) * chance_scale):
		Inventory.gather("mining", row)
		mined += 1
		ToolFx.burst(host, pos + Vector3.UP * 0.2, CHIPS.get(ore, [Color.WHITE]), 26, 3.4, 0.08)
