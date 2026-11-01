class_name Modal
extends CanvasLayer
## A centred menu with a title, a Close button and a scrolling list. The player doesn't move while
## one is open (the "modal" group, see Player.ui_open). Esc or F closes it.
## Subclasses list the station kinds they open for in `kinds` and fill `_list` in `_render()`.

var kinds: Array = []
var kind := ""
var _title: Label
var _list: VBoxContainer
var _panel: PanelContainer


func _ready() -> void:
	layer = 15
	add_to_group("modal")
	for k in kinds:
		add_to_group("menu_" + k)
	_build()
	visible = false
	Inventory.changed.connect(_refresh)
	Inventory.coins_changed.connect(func(_c): _refresh())
	Stable.changed.connect(_refresh)


func open(station_kind: String) -> void:
	kind = station_kind
	_title.text = GameData.STATIONS[kind].label if GameData.STATIONS.has(kind) else kind
	visible = true
	_refresh()


func close() -> void:
	visible = false


func _refresh() -> void:
	if not visible:
		return
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	_render()


func _render() -> void:
	pass


func _unhandled_input(event: InputEvent) -> void:
	if visible and event is InputEventKey and event.pressed and not event.echo \
			and (event.keycode == KEY_ESCAPE or event.is_action("interact")):
		close()
		get_viewport().set_input_as_handled()


func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.35)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	_panel = PanelContainer.new()
	_panel.custom_minimum_size = Vector2(700, 0)
	_panel.add_theme_stylebox_override("panel", UIKit.style(UIKit.BG, UIKit.BORDER, 10, 20))
	center.add_child(_panel)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 12)
	_panel.add_child(vbox)
	var head := HBoxContainer.new()
	vbox.add_child(head)
	_title = UIKit.label("", Color.WHITE, 26)
	head.add_child(_title)
	head.add_child(UIKit.spacer())
	head.add_child(UIKit.button("Close", true, close))
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 480)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	vbox.add_child(scroll)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_theme_constant_override("separation", 8)
	scroll.add_child(_list)


func _heading(text: String) -> void:
	_list.add_child(UIKit.label(text, Color.WHITE, 18))


func _note(text: String) -> void:
	var l := UIKit.label(text, UIKit.MUTED, 13)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_list.add_child(l)
