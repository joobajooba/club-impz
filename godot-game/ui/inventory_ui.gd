extends CanvasLayer
## The inventory screen (I). Items fill a 6 x 8 grid (D-008), plus any rows bought from the merchant
## (D-077), in pickup order with their counts. Tools sit above the grid, one row per kind; click one
## to hold it, the held one of each kind is outlined. (D-008 puts pickaxes in the grid; with five
## kinds of tools, a separate strip is Proposed.) Below are the TEST tools, for reviewers. Remove
## before launch.

const HELD := Color(1.0, 0.86, 0.4)
const SLOT_SIZE := 52
const TOOL_SIZE := 30

@onready var vbox: VBoxContainer = $Center/Panel/VBox
@onready var slots: GridContainer = $Center/Panel/VBox/Slots
var _tools: VBoxContainer
var _scroll: ScrollContainer
var _buttons: Array[Button] = []


func _ready() -> void:
	slots.columns = GameData.INVENTORY_COLUMNS
	_tools = VBoxContainer.new()
	_tools.add_theme_constant_override("separation", 4)
	vbox.add_child(_tools)
	vbox.move_child(_tools, slots.get_index())
	# The grid scrolls when it is taller than the window (bought rows, small screens).
	_scroll = ScrollContainer.new()
	_scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(_scroll)
	vbox.move_child(_scroll, slots.get_index())
	slots.reparent(_scroll)
	_build_test_tools()
	Inventory.changed.connect(_render)
	visibility_changed.connect(_render)
	_render()


func _thick(border: Color, width: int) -> StyleBoxFlat:
	var s := UIKit.style(UIKit.SLOT, border, 6, 4)
	s.set_border_width_all(width)
	return s


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


func _style_slot(b: Button, border: Color, width := 2) -> void:
	var s := _thick(border, width)
	for state in ["normal", "hover", "pressed", "disabled"]:
		b.add_theme_stylebox_override(state, s)


func _render() -> void:
	if not visible:
		return
	_render_tools()
	while _buttons.size() < Inventory.slots():
		var b := _slot(SLOT_SIZE)
		slots.add_child(b)
		_buttons.append(b)
	var rows := Inventory.slots() / GameData.INVENTORY_COLUMNS
	var room := get_viewport().get_visible_rect().size.y - 330.0
	_scroll.custom_minimum_size = Vector2(GameData.INVENTORY_COLUMNS * (SLOT_SIZE + 6) + 12, minf(rows * (SLOT_SIZE + 6), maxf(room, 160.0)))
	var ids := Inventory.items.keys()
	for i in _buttons.size():
		var b := _buttons[i]
		var id: String = ids[i] if i < ids.size() else ""
		_style_slot(b, UIKit.BORDER * Color(1, 1, 1, 0.6))
		var tex := GameData.item_icon(id) if id else null
		b.icon = tex
		b.text = "" if tex or not id else GameData.item_label(id)   # hilts have no picture yet
		b.tooltip_text = "%s × %d" % [GameData.item_label(id), Inventory.items[id]] if id else ""
		(b.get_node("Count") as Label).text = str(Inventory.items[id]) if id else ""


func _render_tools() -> void:
	for c in _tools.get_children():
		_tools.remove_child(c)
		c.queue_free()
	for kind in GameData.TOOL_KINDS:
		var r := UIKit.row(_tools)
		r.add_theme_constant_override("separation", 4)
		var name := UIKit.label(GameData.TOOL_KINDS[kind].label + "s", UIKit.MUTED, 13)
		name.custom_minimum_size = Vector2(64, 0)
		r.add_child(name)
		for id in Inventory.owned[kind]:
			var b := _slot(TOOL_SIZE)
			var held: bool = Inventory.held[kind] == id
			_style_slot(b, HELD if held else UIKit.BORDER * Color(1, 1, 1, 0.5), 3 if held else 2)
			b.icon = GameData.tool_icon(id)
			b.tooltip_text = GameData.tools[id].label
			b.pressed.connect(Inventory.hold.bind(id))
			r.add_child(b)


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
