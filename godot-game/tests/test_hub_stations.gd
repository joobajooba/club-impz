extends Node
## Headless test for the hub's working stations (hub_town.gd STATIONS). Run from the repo root:
##   godot --headless --path godot-game res://tests/test_hub_stations.tscn
## Loads the real game (scenes/main.tscn) into the hub, then checks that the anvil, workbench and the other
## crafting props carry a "shop" marker, that standing next to one gives the "Use" prompt target from the
## street side and from behind, that E opens the station menu, and that each menu draws rows.
## Exits with the number of failed checks (0 = all passed). It never writes the player's save (Save.enabled).

const KINDS := {anvil = "blacksmith", workbench = "workbench", furnace = "furnace", sawbench = "sawbench",
		tanning_rack = "tanning_rack", drying_rack = "drying_rack"}

var _fails := 0


func _ready() -> void:
	Save.enabled = false
	GameData._test_levels_read = true
	var main: Node = load("res://scenes/main.tscn").instantiate()
	add_child(main)
	var spots := {}
	for i in 1800:                       # the hub loads over a few hundred frames
		await get_tree().process_frame
		for m in get_tree().get_nodes_in_group("shop"):
			if m.get_meta("any_side", false):
				spots[String(m.name)] = m
		if spots.size() >= KINDS.size():
			break
	for alias in KINDS:
		_ok(spots.has(alias), "a station marker on the hub's %s" % alias)
	if spots.size() < KINDS.size():
		return _done()
	var player: CharacterBody3D = main.player
	var shop: Node = player.get_node("shop_keeper")
	for _i in 120:                       # let the loading screen finish and unfreeze the Imp
		if not player.frozen:
			break
		await get_tree().process_frame
	for alias in KINDS:
		var m: Node3D = spots[alias]
		_ok(String(m.get_meta("kind")) == KINDS[alias], "%s opens the %s menu" % [alias, KINDS[alias]])
		for side in [Vector3(0, 0, 1.6), Vector3(0, 0, -1.6), Vector3(1.6, 0, 0)]:
			player.global_position = m.global_position + side
			await get_tree().physics_frame
			await get_tree().physics_frame
			_ok(shop.target == m, "standing %s from the %s targets it" % [side, alias])
		player.global_position = m.global_position + Vector3(0, 0, 4.0)
		await get_tree().physics_frame
		await get_tree().physics_frame
		_ok(shop.target != m, "4 m from the %s is out of reach" % alias)
		player.global_position = m.global_position + Vector3(0, 0, 1.6)
		await get_tree().physics_frame
		await get_tree().physics_frame
		_ok(shop.use(), "E at the %s opens a menu" % alias)
		var menu: Modal = get_tree().get_first_node_in_group("menu_" + KINDS[alias])
		_ok(menu != null and menu.visible and menu.kind == KINDS[alias], "the %s menu is open" % KINDS[alias])
		if menu:
			_ok(menu._list.get_child_count() > 1, "the %s menu draws its rows" % KINDS[alias])
			menu.close()
	_done()


func _done() -> void:
	print("hub stations: %s" % ("all passed" if _fails == 0 else "%d failed" % _fails))
	get_tree().quit(_fails)


func _ok(cond: bool, what: String) -> void:
	if not cond:
		_fails += 1
		print("FAIL ", what)
