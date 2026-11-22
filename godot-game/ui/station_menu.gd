extends Modal
## The processing stations, the blacksmith and the workbench, opened by F next to a Station.
## Furnace (D-054, D-055), drying rack (D-062), tanning rack (D-068), sawbench (D-107) and campfire
## (D-111) turn raw items into made ones, with no energy (D-056).
## Tool parts (D-125 to D-128) are made at the station of their material: hilts (D-058, D-107), heads,
## blades and reels at the anvil; rod blanks and bow staves at the sawbench; bow wraps and leather strips at
## the tanning rack; Nettle Cord at the drying rack. Every tool but the sword is put together at the
## workbench, whose one Craft button makes any missing part first (D-131). The workbench shows one mechanic
## at a time (E1, Proposed): part rows, then Re-haft and Take apart, then the socket.

const NOTES := {
	"furnace": "Ore into ingots. Gold and up also burn Coal.",
	"drying_rack": "Plants into dried bundles. No fuel. Nettle bundles also make Nettle Cord, for tools.",
	"tanning_rack": "Hides into leather. No fuel. Bow wraps are made from the leather of the tier below.",
	"sawbench": "Logs into planks. Rod blanks are made from the planks of the tier below.",
	"campfire": "Fish into cooked fish, food for battle animals. Catfish and up burn logs (Proposed): any log, lowest tier first.",
	"blacksmith": "Hilts, heads, blades and reels. Tools are put together at the workbench.",
	"workbench": "Every tool is put together here from its parts. Craft makes any part you're missing from the ingots, planks, leather and bundles in your bag, then puts the tool together.",
}
## What each kind's fitting is called on the tool (TOOL-CRAFTING-ROADMAP 2.1), for the Re-haft line.
const USED_UP := {pickaxe = "head and binding", axe = "head and binding", sickle = "blade and binding",
		rod = "blank and line", bow = "wrap and string"}

var _show_parts := false     # "Show parts" pressed this visit (E1)
var _list_for := ""          # the tool whose shopping list is showing (D-131)
var _list_rehaft := false


func _init() -> void:
	kinds = ["furnace", "drying_rack", "tanning_rack", "sawbench", "campfire", "blacksmith", "workbench"]


func _ready() -> void:
	super()
	add_to_group("station_menu")


func open(station_kind: String) -> void:
	_list_for = ""
	super.open(station_kind)


func _render() -> void:
	_note(NOTES[kind] + " No energy needed.")
	match kind:
		"blacksmith":
			_heading("Hilts")
			for id in GameData.HILTS:
				_make_row(id)
			_parts_here()
			return
		"workbench":
			_render_workbench()
			return
	var skill: String = GameData.STATIONS[kind].skill
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
	_parts_here()


# --- parts at their stations (D-127) ----------------------------------------------------

## The parts made here: fittings first, in batches (M5), then each kind's working parts, one at a time.
func _parts_here() -> void:
	var fittings := GameData.FITTINGS.keys().filter(func(id): return GameData.FITTINGS[id].station == kind)
	if not fittings.is_empty():
		_heading("Fittings")
		for id in fittings:
			_make_row(id, true)
	for tool_kind in GameData.PARTS_OF:
		var p: Dictionary = GameData.PARTS_OF[tool_kind]
		if p.station != kind:
			continue
		_heading("%s %ss" % [GameData.TOOL_KINDS[tool_kind].label, p.suffix])
		for t in GameData.tools_of[tool_kind]:
			if GameData.is_assembled(t):
				_make_row(t.part)


## A hilt or part: its picture, how many you have, what it takes, and Make (plus x5 and All for fittings).
func _make_row(id: String, batch := false) -> void:
	var r := UIKit.row(_list)
	var tex := GameData.item_icon(id)
	if tex:
		r.add_child(UIKit.icon(tex, 32))
	var name_box := VBoxContainer.new()
	name_box.add_theme_constant_override("separation", 0)
	name_box.add_child(UIKit.label(GameData.item_label(id)))
	name_box.add_child(UIKit.label("Have %d" % Inventory.count(id), UIKit.MUTED, 12))
	var lock := Inventory.part_lock(id)
	if lock != "":
		name_box.add_child(UIKit.label(lock, UIKit.SHORT, 12))
	r.add_child(name_box)
	r.add_child(UIKit.spacer())
	var cost := GameData.part_cost(id)
	for item in cost:
		r.add_child(UIKit.cost_part(item, cost[item]))
	var n := Inventory.makeable(id)
	r.add_child(UIKit.button("Locked" if lock != "" else "Make", n > 0, Inventory.make.bind(id, 1)))
	if batch:
		r.add_child(UIKit.button("×5", n >= 5, Inventory.make.bind(id, 5)))
		r.add_child(UIKit.button("All (%d)" % n if n > 1 else "All", n > 0, func(): Inventory.make(id, Inventory.makeable(id))))


# --- the workbench (D-125 to D-136; E1 Proposed) ----------------------------------------

func _render_workbench() -> void:
	var parts_open := Inventory.parts_unfolded() or _show_parts
	if not parts_open:
		var r := UIKit.row(_list)
		r.add_child(UIKit.spacer())
		r.add_child(UIKit.button("Show parts", true, _open_parts))
	for tool_kind in GameData.PARTS_OF:
		_heading(GameData.TOOL_KINDS[tool_kind].label + "s")
		for t in GameData.tools_of[tool_kind]:
			if GameData.is_assembled(t):
				_tool_row(t, parts_open)


func _open_parts() -> void:
	_show_parts = true
	_refresh()


## One tool: what it reaches, then either what it takes and Craft (and Re-haft), or, once owned, its socket
## and Take apart. Lines under the row: what Re-haft moves, the parts still to make, the shopping list.
func _tool_row(t: Dictionary, parts_open: bool) -> void:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	_list.add_child(box)
	var r := UIKit.row(box)
	r.add_child(UIKit.icon(Inventory.icon_of(t.id), 36))
	var skill: String = GameData.TOOL_KINDS[t.kind].skill
	var name_box := VBoxContainer.new()
	name_box.add_theme_constant_override("separation", 0)
	name_box.add_child(UIKit.label(t.label))
	name_box.add_child(UIKit.label("Up to " + GameData.row_by_tier(skill, t.reach).label, UIKit.MUTED, 12))
	var lock := Inventory.recipe_lock(t)
	if lock != "":
		name_box.add_child(UIKit.label(lock, UIKit.SHORT, 12))
	r.add_child(name_box)
	r.add_child(UIKit.spacer())
	if Inventory.owns(t.id):
		_owned_row(r, t)
		return
	var cost: Dictionary = t.parts if parts_open else Inventory.flat_cost(t)
	for item in cost:
		r.add_child(UIKit.cost_part(item, cost[item]))
	var from := Inventory.rehaft_from(t)
	if from != "" and lock == "":
		Inventory.unfold("take_apart")
		var b := UIKit.button("Re-haft", true, _craft.bind(t, true))
		b.tooltip_text = "Uses the %s from your %s" % [GameData.item_label(GameData.tools[from].returns), GameData.tools[from].label]
		r.add_child(b)
	r.add_child(UIKit.button("Locked" if lock != "" else "Craft", lock == "", _craft.bind(t, false)))
	if from != "" and lock == "":
		var old: Dictionary = GameData.tools[from]
		_sub(box, "Re-haft takes your %s apart and moves its %s across. Its %s%s are used up." % [old.label,
				GameData.item_label(old.returns), USED_UP[old.kind], ", and its inlay," if Inventory.sockets.has(from) else ""])
	if parts_open:
		for p in t.parts:
			if Inventory.count(p) < t.parts[p]:
				_part_line(box, p)
	if _list_for == t.id:
		var moved: String = GameData.tools[from].returns if _list_rehaft and from != "" else ""
		_sub(box, "Still needed:", UIKit.SHORT)
		for line in Inventory.shopping_list(t, moved):
			_sub(box, "  " + line, UIKit.SHORT)


## An owned tool: its inlay (or the empty socket, once a gem or pearl fits, E1) and Take apart (E1).
func _owned_row(r: HBoxContainer, t: Dictionary) -> void:
	r.add_child(UIKit.label("Owned", UIKit.GOOD, 14))
	var gem: String = Inventory.sockets.get(t.id, "")
	var boost := Inventory.tool_boost(t)
	if gem != "":
		var l := UIKit.label("%s  ·  rare drops ×%s%s" % [GameData.item_label(gem), snappedf(boost, 0.01),
				" (at cap)" if boost >= GameData.RARE_BOOST_CAP else ""], UIKit.RARE, 13)
		r.add_child(l)
	else:
		var choice := Inventory.inlay_choice(t)
		if choice != "" or Inventory.unfolded.has("socket"):
			Inventory.unfold("socket")
			var b := UIKit.button("Inlay " + GameData.item_label(choice) if choice != "" else "Inlay", choice != "",
					Inventory.inlay.bind(t.id, choice))
			b.tooltip_text = "A gem or pearl of tier %d or higher: rare drops ×%s. It can't be taken out, and is lost if the tool is taken apart." \
					% [mini(t.tier - 1, 10), GameData.INLAY_BOOST]
			r.add_child(b)
	if Inventory.unfolded.has("take_apart"):
		var why := Inventory.take_apart_blocker(t.id)
		var b := UIKit.button("Take apart", why == "", Inventory.take_apart.bind(t.id))
		b.tooltip_text = why if why != "" else "Gives back its %s. The rest%s is used up." % [GameData.item_label(t.returns),
				", and its inlay," if gem != "" else ""]
		r.add_child(b)


## A part still to make (M1): where it's made and what from.
func _part_line(box: VBoxContainer, part: String) -> void:
	var r := UIKit.row(box)
	r.add_child(UIKit.label("    %s, at the %s:" % [GameData.item_label(part), _station_name(GameData.items[part].station)], UIKit.MUTED, 12))
	var cost := GameData.part_cost(part)
	for item in cost:
		r.add_child(UIKit.cost_part(item, cost[item]))


func _sub(box: VBoxContainer, text: String, color := UIKit.MUTED) -> void:
	var l := UIKit.label("    " + text, color, 12)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	box.add_child(l)


func _station_name(station: String) -> String:
	return "anvil" if station == "blacksmith" else GameData.STATIONS[station].label.to_lower()


## Craft, or the shopping list in its place when something is short (D-131).
func _craft(t: Dictionary, rehaft: bool) -> void:
	var from := Inventory.rehaft_from(t) if rehaft else ""
	var moved: String = GameData.tools[from].returns if from != "" else ""
	if Inventory.craft_blocker(t, moved) == "Missing materials":
		_list_for = t.id
		_list_rehaft = rehaft
		_refresh()
		return
	_list_for = ""
	Inventory.craft(t, rehaft)
