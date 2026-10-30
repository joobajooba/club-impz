extends Modal
## The processing stations and the blacksmith, opened by F next to a Station.
## Furnace (D-054, D-055), drying rack (D-062), tanning rack (D-068), sawbench (D-107) and campfire
## (D-111) turn raw items into made ones, with no energy (D-056). The blacksmith makes hilts (D-058,
## D-107), pickaxes (D-006, D-060), sickles (D-063) and axes (D-106). Bows are made at the tanning
## rack (D-069) and rods at the sawbench (D-110): where is Proposed.

const NOTES := {
	"furnace": "Ore into ingots. Gold and up also burn Coal.",
	"drying_rack": "Plants into dried bundles. No fuel.",
	"tanning_rack": "Hides into leather. No fuel. Bows are made from the leather of the tier below.",
	"sawbench": "Logs into planks. Rods are made from the planks of the tier below.",
	"campfire": "Fish into cooked fish, food for battle animals. Catfish and up burn logs (Proposed): any log, lowest tier first.",
}


func _init() -> void:
	kinds = ["furnace", "drying_rack", "tanning_rack", "sawbench", "campfire", "blacksmith"]


func _ready() -> void:
	super()
	add_to_group("station_menu")


func _render() -> void:
	if kind == "blacksmith":
		_render_smith()
		return
	var skill: String = GameData.STATIONS[kind].skill
	_note(NOTES[kind] + " No energy needed.")
	for row in GameData.tiers[skill]:
		if row.per <= 0 or not row.made:
			continue
		var r := UIKit.row(_list)
		r.add_child(UIKit.cost_part(row.raw, row.per))
		if row.fuel_count > 0:
			if row.fuel == GameData.ANY_LOG:
				r.add_child(UIKit.label("+ %d log%s" % [row.fuel_count, "s" if row.fuel_count > 1 else ""], UIKit.MUTED, 13))
			else:
				r.add_child(UIKit.cost_part(row.fuel, row.fuel_count))
		r.add_child(UIKit.label("→", UIKit.MUTED, 18))
		r.add_child(UIKit.icon(GameData.item_icon(row.made), 32))
		r.add_child(UIKit.label(GameData.item_label(row.made)))
		r.add_child(UIKit.spacer())
		var n := Inventory.processable(row)
		r.add_child(UIKit.button("Make", n > 0, Inventory.process.bind(row, 1)))
		r.add_child(UIKit.button("All (%d)" % n if n > 1 else "All", n > 0,
				func(): Inventory.process(row, Inventory.processable(row))))
	match kind:
		"tanning_rack":
			_tools("bow", "Bows")
		"sawbench":
			_tools("rod", "Rods")


func _render_smith() -> void:
	_heading("Hilts")
	for id in GameData.HILTS:
		var hilt: Dictionary = GameData.HILTS[id]
		var r := UIKit.row(_list)
		r.add_child(UIKit.label(hilt.label))
		r.add_child(UIKit.label("Have %d" % Inventory.count(id), UIKit.MUTED, 13))
		r.add_child(UIKit.spacer())
		for item in hilt.cost:
			r.add_child(UIKit.cost_part(item, hilt.cost[item]))
		r.add_child(UIKit.button("Craft", Inventory.can_craft_hilt(id), Inventory.craft_hilt.bind(id)))
	_tools("pickaxe", "Pickaxes")
	_tools("sickle", "Sickles")
	_tools("axe", "Axes")


## Every craftable tool of a kind: what it reaches, what it costs, and Craft or Owned.
func _tools(tool_kind: String, heading: String) -> void:
	_heading(heading)
	var skill: String = GameData.TOOL_KINDS[tool_kind].skill
	for t in GameData.tools_of[tool_kind]:
		if t.cost.is_empty():
			continue
		var r := UIKit.row(_list)
		r.add_child(UIKit.icon(GameData.tool_icon(t.id), 36))
		var name_box := VBoxContainer.new()
		name_box.add_theme_constant_override("separation", 0)
		name_box.add_child(UIKit.label(t.label))
		name_box.add_child(UIKit.label("Up to " + GameData.row_by_tier(skill, t.reach).label, UIKit.MUTED, 12))
		r.add_child(name_box)
		r.add_child(UIKit.spacer())
		var cost := Inventory.tool_cost(t)
		for item in cost:
			r.add_child(UIKit.cost_part(item, cost[item]))
		var owned := Inventory.owns(t.id)
		r.add_child(UIKit.button("Owned" if owned else "Craft", Inventory.can_craft_tool(t), Inventory.craft_tool.bind(t)))
