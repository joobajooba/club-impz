extends Modal
## The teleport menu (J00BA, 2026-11-14), the TeleportMenu autoload. T opens it: a button for the hub and for each
## biome of The Wilds, and a button for each other player online, which takes you to their world and beside them.
## T or Esc closes it. T still tames when you are looking at an animal (characters/gatherer.gd takes the key first).
## This answers game_worlds.md's open question "can players return to the hub from anywhere": yes, from this menu.
## The server takes a teleport as a jump at most every 3 s (game-server "tp"), so the menu waits that long too.

const PLACES := [["hub", "Hub"], ["forest", "Forest"], ["mountain", "Mountain"], ["frost", "Frost"],
		["plains", "Plains"], ["swamp", "Swamp"]]
const WORLD_LABELS := {"hub": "Hub", "resource": "The Wilds"}
const COOLDOWN := 3.0            # seconds between teleports (game-server TP_EVERY_MS)
const BESIDE := 1.6              # metres from the player you teleport to

var _next_at := 0.0              # Time.get_ticks_msec() / 1000 when the next teleport is allowed
var _going := false
var _shown := ""                 # what the list showed last (players and the wait), to redraw only on a change


func _ready() -> void:
	super._ready()
	_title.text = "Teleport"
	Net.status_changed.connect(_refresh)


func open_menu() -> void:
	_title.text = "Teleport"
	visible = true
	_shown = ""
	_refresh()


func _main() -> Node:
	return get_tree().get_first_node_in_group("game_main")


func _can_open() -> bool:
	var main := _main()
	if main == null or main.get("free_cam") != null or main.get("busy") or str(main.get("joined_world")) == "":
		return false
	if Chat and Chat.is_typing():
		return false
	for n in get_tree().get_nodes_in_group("modal"):   # another menu is open
		if n != self and n.visible:
			return false
	return true


func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo or k.alt_pressed or k.ctrl_pressed:
		return
	if visible:
		if k.keycode == KEY_ESCAPE or k.is_action("teleport"):
			close()
			get_viewport().set_input_as_handled()
	elif k.is_action("teleport") and _can_open():
		open_menu()
		get_viewport().set_input_as_handled()


func _process(_delta: float) -> void:
	if visible and _signature() != _shown:   # a player joined, left or changed world, or the wait ended
		_refresh()


func _wait_left() -> float:
	return maxf(0.0, _next_at - Time.get_ticks_msec() / 1000.0)


func _signature() -> String:
	var parts := [str(ceili(_wait_left())), Net.state]
	for p in Net.others():
		parts.append("%d:%s:%s" % [p.id, p.name, p.world])
	return "|".join(parts)


func _render() -> void:
	_shown = _signature()
	var main := _main()
	if main == null:
		return
	var world: String = main.current_world_name
	var here: String = "hub" if world == "hub" else (main.biome_name_at(main.player.global_position) if world == "resource" else "")
	var wait := _wait_left()
	var can_go := wait <= 0.0 and not _going
	_note("Wait %d s before teleporting again." % ceili(wait) if wait > 0.0 else "Pick a place or a player.")
	_heading("Places")
	var grid := GridContainer.new()
	grid.columns = 3
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	_list.add_child(grid)
	for p in PLACES:
		var b := UIKit.button(p[1] + ("\nYou are here" if p[0] == here else ""), can_go, _go_place.bind(p[0]))
		b.custom_minimum_size = Vector2(212, 64)
		b.tooltip_text = "Teleport to the hub" if p[0] == "hub" else "Teleport to the middle of the %s biome in The Wilds" % p[1]
		grid.add_child(b)
	_list.add_child(UIKit.divider())
	_heading("Players")
	var others := Net.others()
	if Net.state != "online":
		_note("You're offline, so there are no other players to teleport to.")
	elif others.is_empty():
		_note("Nobody else is online right now.")
	for p in others:
		var line := HBoxContainer.new()
		line.add_theme_constant_override("separation", 10)
		_list.add_child(line)
		var name_label := UIKit.label(str(p.name), Color.WHITE, 16)
		name_label.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		name_label.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(name_label)
		var where: String = WORLD_LABELS.get(p.world, str(p.world).capitalize())
		if p.world == "resource" and world == "resource" and p.pos != null:
			where += " · " + str(main.biome_name_at(p.pos)).capitalize()
		var wl := UIKit.label(where, UIKit.MUTED, 14)
		wl.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(wl)
		var ok: bool = can_go and WORLD_LABELS.has(p.world)
		var b := UIKit.button("Teleport", ok, _go_player.bind(int(p.id)))
		b.custom_minimum_size = Vector2(130, 44)
		line.add_child(b)


# --- going -----------------------------------------------------------------------------------

func _start() -> Node:
	var main := _main()
	if main == null or _going or _wait_left() > 0.0 or main.busy:
		return null
	_going = true
	close()
	return main


func _done() -> void:
	_going = false
	_next_at = Time.get_ticks_msec() / 1000.0 + COOLDOWN
	Net.teleported()


func _go_place(place: String) -> void:
	var main := _start()
	if main == null:
		return
	if place == "hub":
		if main.current_world_name != "hub":
			await main.change_world("hub", "spawn_point")    # the hub's spawn, like walking through its portal
		else:
			var marker := main.current_world.find_child("spawn_point", true, false) as Node3D
			if marker:
				main.player.place_at(marker.global_transform)
	else:
		if main.current_world_name != "resource":
			await main.change_world("resource", "spawn_point")
		if main.current_world_name == "resource" and main.current_world.has_method("biome_centre"):
			main.player.place_at(main.current_world.biome_centre(place))
	_done()


func _go_player(id: int) -> void:
	var p := Net.other(id)
	var main := _start()
	if main == null:
		return
	if p.is_empty():
		_going = false
		return
	if p.world != main.current_world_name and WORLD_LABELS.has(p.world):
		await main.change_world(p.world, "spawn_point")
		for i in 20:                                        # their Imp appears and gets its first move
			if Net.has_remote(id):
				break
			await get_tree().create_timer(0.1).timeout
	var pos = Net.other(id).get("pos")
	if pos != null and main.current_world_name == p.world:
		var spot: Vector3 = pos + Vector3(BESIDE, 0.3, 0.0)
		if main.current_world.has_method("ground_height"):
			spot.y = maxf(spot.y, main.current_world.ground_height(spot.x, spot.z) + 0.2)
		var face := Vector3(pos.x, spot.y, pos.z)
		main.player.place_at(Transform3D(Basis(), spot).looking_at(face, Vector3.UP))
	_done()
