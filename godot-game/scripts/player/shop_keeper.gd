extends Node
## Shops (J00BA, 2026-11-15). A child of the player (imp_player.gd), checked before chopping and mining.
##
## Walk up to a shop counter and the prompt shows "E  Shop: Merchant"; press E and its menu opens (for the
## merchant: ui/merchant_menu.gd, buy refills, inventory rows and stable slots, sell what you gathered).
## E, F or Esc closes it again (ui/modal.gd). A shop counter is any Node3D in the "shop" group with the meta
## "kind" (the menu it opens: the menu is in the group "menu_<kind>") and "label"; hub_town.gd puts one at
## the merchant's stall. Crate chests are in the group too (kind "crate", meta "prompt" and "crate"; hub_town.gd).

const REACH := 2.6               # metres from the counter marker (behind the counter) to the Imp

var player: CharacterBody3D
var target: Node3D               # the shop in reach, for the prompt and E
var _prompt := []


func _ready() -> void:
	player = get_parent()


func _physics_process(_delta: float) -> void:
	target = null
	if not player.frozen and not player.menu_open():
		var best := REACH
		for s: Node3D in get_tree().get_nodes_in_group("shop"):
			var off := player.global_position - s.global_position
			if off.dot(-s.global_basis.z) < 0.0:           # only from the customers' side (the marker faces them)
				continue
			var d := Vector2(off.x, off.z).length()
			if d < best:
				best = d
				target = s
	if target:
		_set_prompt("E", String(target.get_meta("prompt", "Shop: %s" % String(target.get_meta("label", "Shop")))))
	else:
		_set_prompt("", "")


## E (use_tool): open the shop in reach. Returns false if there is none, so E chops, mines or swings.
func use() -> bool:
	if target == null:
		return false
	var kind := String(target.get_meta("kind", "merchant"))
	var menu := get_tree().get_first_node_in_group("menu_" + kind)
	if menu == null:
		push_warning("shop: no menu for %s" % kind)
		return false
	if menu.has_method("open_for"):                     # a crate menu wants the chest itself (which crate, its lid)
		menu.open_for(target)
	else:
		menu.open(kind)
	return true


func _set_prompt(key: String, text: String) -> void:
	var p := [key, text]
	if p == _prompt:
		return
	_prompt = p
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_prompt(key, text)
