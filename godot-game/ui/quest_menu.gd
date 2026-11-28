extends Modal
## The princess's quest board (J00BA, 2026-11-28). E at the princess by the castle opens it (her NPC in
## data/hub_npcs.json has menu "quests"; shop_keeper.gd). One card per quest in GameData.QUESTS: what she asks
## for (with how many you have), the reward (Imp Coins or a chest key) and Hand in. Each quest can be done once
## per reset (00:00 and 12:00 UTC); Inventory.hand_in takes the items and pays.

const ROYAL := Color("#ff8fd8")   # the princess's pink


func _init() -> void:
	kinds = ["quests"]


func open(station_kind: String) -> void:
	super.open(station_kind)
	_title.text = "The Princess's Quests"


func _render() -> void:
	var left := 0
	for q in GameData.QUESTS:
		if not Inventory.quest_done(q.id):
			left += 1
	var top := UIKit.row(_list)
	top.add_child(UIKit.label("\"Help the castle, brave Imp, and you shall be rewarded!\"", ROYAL, 15))
	top.add_child(UIKit.spacer())
	top.add_child(UIKit.pixel_icon(UIKit.COIN, UIKit.ENERGY))
	top.add_child(UIKit.label("%d" % Inventory.coins, UIKit.RARE, 17))
	var secs := Inventory.seconds_to_reset()
	_note("%d of %d quests open. They reset in %dh %02dm. TEST quests." % [left, GameData.QUESTS.size(), secs / 3600, (secs / 60) % 60])
	for q in GameData.QUESTS:
		_card(q)


func _card(q: Dictionary) -> void:
	var done := Inventory.quest_done(q.id)
	var card := PanelContainer.new()
	card.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.GOOD.darkened(0.3) if done else UIKit.OUTLINE, 2, 8.0))
	_list.add_child(card)
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 4)
	card.add_child(v)
	var head := HBoxContainer.new()
	v.add_child(head)
	head.add_child(UIKit.label(q.label, UIKit.GOOD if done else UIKit.KEY, 18))
	head.add_child(UIKit.spacer())
	var why := Inventory.quest_blocker(q.id)
	if done:
		head.add_child(UIKit.label("Completed", UIKit.GOOD, 15))
	else:
		head.add_child(UIKit.button("  Hand in  ", why == "", func(): Inventory.hand_in(q.id)))
	var text := UIKit.label(q.text, UIKit.MUTED, 13)
	text.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	v.add_child(text)
	var line := HBoxContainer.new()
	line.add_theme_constant_override("separation", 6)
	v.add_child(line)
	line.add_child(UIKit.label("Bring:", UIKit.MUTED, 13))
	for item in q.needs:
		var need := int(q.needs[item])
		var have := Inventory.count(item)
		line.add_child(UIKit.icon(GameData.item_icon(item), 24))
		var amount := ("x%d" % need) if done else ("%d/%d" % [mini(have, need), need])   # once handed in, just what it took
		line.add_child(UIKit.label("%s %s" % [GameData.item_label(item), amount], UIKit.GOOD if have >= need or done else UIKit.SHORT, 13))
	line.add_child(UIKit.spacer())
	line.add_child(UIKit.label("Reward:", UIKit.MUTED, 13))
	var r: Dictionary = q.reward
	if r.has("coins"):
		line.add_child(UIKit.label("%d Imp Coins" % int(r.coins), UIKit.RARE, 14))
	else:                                        # text only, in the key's chest colour: "Tier 1 Key" in green (J00BA, 2026-11-28)
		var crate := _crate_of(r.key)
		var n := int(r.get("n", 1))
		var key_text: String = String(crate.label).replace(" Chest", "") + " Key" + ("" if n == 1 else " x%d" % n)
		line.add_child(UIKit.label(key_text, crate.get("color", UIKit.RARE), 14))


static func _crate_of(key: String) -> Dictionary:
	for c in GameData.CRATES.values():
		if c.key == key:
			return c
	return {label = GameData.item_label(key)}
