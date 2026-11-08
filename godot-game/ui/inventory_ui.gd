extends CanvasLayer
## The inventory screen (I). Across the top, the equipped tools: one slot per kind (pickaxe, sickle,
## axe, bow, rod, sword), the same size as the item slots; the one in the Imp's hand is outlined, a
## click takes it out. Only one tool of a kind is equipped: every other tool the player owns sits in
## the grid below, one slot each (Inventory.hold). To swap, drag a tool from the grid onto its slot
## (or the equipped one onto a tool of the same kind in the grid); the old one takes its place in the grid.
## Items fill a 6 x 8 grid (D-008), plus any rows bought from the merchant (D-077), in pickup order
## with their counts; right click a slot to drop it (shift: drop one). Below are the TEST tools, for reviewers. Remove before launch.

const HELD := Color(1.0, 0.86, 0.4)
const SLOT_SIZE := 52
const GAP := 6                     # between slots, the grid's h_separation
const TOOL_ORDER := ["pickaxe", "sickle", "axe", "bow", "rod", "sword"]

@onready var vbox: VBoxContainer = $Center/Panel/VBox
@onready var slots: GridContainer = $Center/Panel/VBox/Slots
var _tools: HBoxContainer
var _tool_slots := {}            # tool kind -> Button
var _scroll: ScrollContainer
var _buttons: Array[Button] = []


func _ready() -> void:
	slots.columns = GameData.INVENTORY_COLUMNS
	$Center/Panel.add_theme_stylebox_override("panel", UIKit.panel())
	var title: Label = $Center/Panel/VBox/Title
	title.add_theme_color_override("font_color", UIKit.RARE)
	title.add_theme_color_override("font_shadow_color", UIKit.OUTLINE)
	title.add_theme_constant_override("shadow_offset_x", 2)
	title.add_theme_constant_override("shadow_offset_y", 2)
	var rule := UIKit.divider()
	vbox.add_child(rule)
	vbox.move_child(rule, title.get_index() + 1)
	var tools_head := UIKit.label("Equipped tools  ·  drag a tool from your bag onto its slot to swap", UIKit.MUTED, 12)
	tools_head.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	vbox.add_child(tools_head)
	vbox.move_child(tools_head, slots.get_index())
	_tools = HBoxContainer.new()
	_tools.add_theme_constant_override("separation", GAP)
	_tools.alignment = BoxContainer.ALIGNMENT_CENTER
	vbox.add_child(_tools)
	vbox.move_child(_tools, slots.get_index())
	_build_tool_slots()
	var bag_rule := UIKit.divider()
	vbox.add_child(bag_rule)
	vbox.move_child(bag_rule, slots.get_index())
	# The grid scrolls when it is taller than the window (bought rows, small screens).
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_scroll.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	vbox.add_child(_scroll)
	vbox.move_child(_scroll, slots.get_index())
	slots.reparent(_scroll)
	_build_test_tools()
	Inventory.changed.connect(_render)
	visibility_changed.connect(_render)
	_render()


func _slot(size: int) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(size, size)
	b.focus_mode = Control.FOCUS_NONE
	b.expand_icon = true
	b.icon_alignment = HORIZONTAL_ALIGNMENT_CENTER
	b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	b.add_theme_font_size_override("font_size", 11)
	var count := Label.new()
	count.name = "Count"
	count.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_RIGHT)
	count.grow_horizontal = Control.GROW_DIRECTION_BEGIN
	count.grow_vertical = Control.GROW_DIRECTION_BEGIN
	count.offset_right = -4
	count.offset_bottom = -1
	count.add_theme_font_size_override("font_size", 13)
	count.add_theme_constant_override("outline_size", 4)
	count.add_theme_color_override("font_outline_color", Color.BLACK)
	b.add_child(count)
	return b


func _style_slot(b: Button, held := false) -> void:
	var s := UIKit.slot(UIKit.SLOT, HELD, 2) if held else UIKit.slot()
	for state in ["normal", "pressed", "disabled"]:
		b.add_theme_stylebox_override(state, s)
	b.add_theme_stylebox_override("hover", UIKit.slot(UIKit.SLOT.lightened(0.1), HELD if held else UIKit.GOLD, 2 if held else 1))


func _render() -> void:
	if not visible:
		return
	_render_tools()
	while _buttons.size() < Inventory.slots():
		var b := _slot(SLOT_SIZE)
		var i := _buttons.size()
		b.set_drag_forwarding(_drag_from_grid.bind(b, i), _can_drop_on_grid.bind(i), _drop_on_grid.bind(i))
		b.gui_input.connect(_on_slot_input.bind(i))
		slots.add_child(b)
		_buttons.append(b)
	var rows := Inventory.slots() / GameData.INVENTORY_COLUMNS
	var room := get_viewport().get_visible_rect().size.y - 330.0   # the title, tools, TEST row and frame
	_scroll.custom_minimum_size = Vector2(GameData.INVENTORY_COLUMNS * (SLOT_SIZE + GAP) + 12, minf(rows * (SLOT_SIZE + 6), maxf(room, 160.0)))
	var ids := Inventory.items.keys()
	for i in _buttons.size():
		var b := _buttons[i]
		var id: String = ids[i] if i < ids.size() else ""
		_style_slot(b)
		var tex := GameData.item_icon(id) if id else null
		b.icon = tex
		b.text = "" if tex or not id else GameData.item_label(id)   # hilts have no picture yet
		var tool := id != "" and Inventory.is_tool(id)
		if tool:
			b.tooltip_text = "%s\nDrag onto the %s slot to equip it" % [GameData.item_label(id), GameData.TOOL_KINDS[GameData.tools[id].kind].label.to_lower()]
		else:
			b.tooltip_text = ("%s × %d\nRight click: drop  ·  Shift + right click: drop one" % [GameData.item_label(id), Inventory.items[id]]) if id else ""
		(b.get_node("Count") as Label).text = str(Inventory.items[id]) if id and not tool else ""


# --- dropping items: right click a slot ----------------------------------------------------------------

const DROPPED := preload("res://scripts/world/dropped_item.gd")
const DROP_SOUND := "res://assets/sounds/item_drop.wav"


## Right click drops the whole stack, shift + right click drops one. Tools can't be dropped (a lost pickaxe
## could only come back by crafting it again).
func _on_slot_input(event: InputEvent, i: int) -> void:
	var mb := event as InputEventMouseButton
	if mb == null or not mb.pressed or mb.button_index != MOUSE_BUTTON_RIGHT:
		return
	var id := _grid_id(i)
	if id == "":
		return
	if Inventory.is_tool(id):
		Inventory.message.emit("Tools can't be dropped")
		return
	drop(id, 1 if mb.shift_pressed else Inventory.count(id))


func drop(id: String, n: int) -> void:
	var main := get_tree().get_first_node_in_group("game_main")
	var player: Node3D = main.get("player") if main else null
	if player == null or n < 1:
		return
	Inventory.remove(id, n)
	var item: Node3D = DROPPED.new()
	item.set("id", id)
	item.set("count", n)
	var world: Node = main.get("current_world")
	(world if world else main).add_child(item)
	var fwd := -(player.get_node("visual") as Node3D).global_basis.z
	var p := player.global_position + Vector3(fwd.x, 0, fwd.z).normalized() * 1.3 + Vector3(randf_range(-0.3, 0.3), 0, randf_range(-0.3, 0.3))
	if world and world.has_method("ground_height"):
		p.y = world.ground_height(p.x, p.z)
	item.global_position = p
	var snd := AudioStreamPlayer.new()
	snd.stream = load(DROP_SOUND)
	snd.volume_db = -6.0
	add_child(snd)
	snd.finished.connect(snd.queue_free)
	snd.play()
	Inventory.message.emit("Dropped %s%s" % [GameData.item_label(id), (" × %d" % n) if n > 1 else ""])


func _build_tool_slots() -> void:
	for kind in TOOL_ORDER:
		var col := VBoxContainer.new()
		col.add_theme_constant_override("separation", 2)
		_tools.add_child(col)
		var b := _slot(SLOT_SIZE)
		b.pressed.connect(Inventory.take_out.bind(kind))
		b.set_drag_forwarding(_drag_from_tool.bind(b, kind), _can_drop_on_tool.bind(kind), _drop_on_tool.bind(kind))
		col.add_child(b)
		var name := UIKit.label(GameData.TOOL_KINDS[kind].label, UIKit.MUTED, 11)
		name.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		name.custom_minimum_size = Vector2(SLOT_SIZE, 0)
		col.add_child(name)
		_tool_slots[kind] = b


func _render_tools() -> void:
	for kind in _tool_slots:
		var b: Button = _tool_slots[kind]
		var id: String = Inventory.held[kind]
		_style_slot(b, kind == Inventory.in_hand)
		b.icon = GameData.tool_icon(id)
		b.tooltip_text = "%s%s" % [GameData.tools[id].label, "  (in hand)" if kind == Inventory.in_hand else ""]


# --- dragging tools: grid <-> equipped slots ------------------------------------------------------

func _grid_id(i: int) -> String:
	var ids := Inventory.items.keys()
	return ids[i] if i < ids.size() else ""


func _drag_preview(b: Button, id: String) -> void:
	var tr := TextureRect.new()
	tr.texture = GameData.tool_icon(id)
	tr.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	tr.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
	tr.size = Vector2(SLOT_SIZE, SLOT_SIZE)
	tr.position = -tr.size / 2.0
	tr.modulate.a = 0.85
	var holder := Control.new()
	holder.add_child(tr)
	b.set_drag_preview(holder)


func _drag_from_grid(_at: Vector2, b: Button, i: int) -> Variant:
	var id := _grid_id(i)
	if id == "" or not Inventory.is_tool(id):
		return null                                   # only tools are dragged (to equip them)
	_drag_preview(b, id)
	return {tool = id, from = "grid"}


func _drag_from_tool(_at: Vector2, b: Button, kind: String) -> Variant:
	var id: String = Inventory.held[kind]
	_drag_preview(b, id)
	return {tool = id, from = "equipped"}


func _kind_of(data: Variant) -> String:
	if data is Dictionary and data.has("tool") and GameData.tools.has(data.tool):
		return GameData.tools[data.tool].kind
	return ""


## A tool from the grid onto the equipped slot of its kind: equip it (the old one goes to its grid slot).
func _can_drop_on_tool(_at: Vector2, data: Variant, kind: String) -> bool:
	return data is Dictionary and data.get("from") == "grid" and _kind_of(data) == kind


func _drop_on_tool(_at: Vector2, data: Variant, _kind: String) -> void:
	Inventory.hold(data.tool)


## The equipped tool onto a tool of the same kind in the grid: the same swap.
func _can_drop_on_grid(_at: Vector2, data: Variant, i: int) -> bool:
	var id := _grid_id(i)
	return data is Dictionary and data.get("from") == "equipped" and id != "" and Inventory.is_tool(id) 		and GameData.tools[id].kind == _kind_of(data)


func _drop_on_grid(_at: Vector2, _data: Variant, i: int) -> void:
	Inventory.hold(_grid_id(i))


func _build_test_tools() -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 6)
	vbox.add_child(row)
	row.add_child(UIKit.label("TEST:", UIKit.MUTED, 13))
	for t in [["Refill energy", Inventory.test_refill_energy], ["+20 every raw item", Inventory.test_add_raw],
			["Unlock all tools", Inventory.test_unlock_tools], ["+1000 coins", Inventory.test_add_coins],
			["Tame 3 starters", Stable.test_tame_starters]]:
		var b := UIKit.button(t[0], true, t[1])
		b.custom_minimum_size = Vector2(0, 30)
		b.add_theme_font_size_override("font_size", 12)
		row.add_child(b)
