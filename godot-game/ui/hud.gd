extends CanvasLayer
## The game HUD: energy, coins and the tool in hand in the top-left corner; the "F Mine Tin" prompt
## at the bottom; a short "+1 Tin ore" line for every pickup (rare drops and new tools are
## highlighted) and short notices such as "Inventory full". Colours from UIKit.

const LINE_TIME := 2.6

var _energy_bar: ProgressBar
var _energy_text: Label
var _coins: Label
var _tool_icon: TextureRect
var _tool_name: Label
var _prompt: PanelContainer
var _keys: Array = []        # [key label, text label] x 2
var _loot: VBoxContainer


func _ready() -> void:
	layer = 5
	add_to_group("hud")
	_build()
	_on_energy(Inventory.energy)
	_on_coins(Inventory.coins)
	_on_held(Inventory.held[Inventory.in_hand])
	Inventory.energy_changed.connect(_on_energy)
	Inventory.coins_changed.connect(_on_coins)
	Inventory.held_changed.connect(_on_held)
	Inventory.looted.connect(_on_looted)
	Inventory.message.connect(_on_message)


func _process(_delta: float) -> void:
	var s := Inventory.seconds_to_reset()
	_energy_bar.tooltip_text = "Energy refills to %d in %dh %dm (00:00 and 12:00 UTC)" % [GameData.ENERGY_MAX, s / 3600, s / 60 % 60]


## A key and its text; a second pair for a second action (T Tame). `key` "" shows the text alone
## (for "Needs a Bronze pickaxe"); `text` "" hides the prompt.
func set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	_prompt.visible = text != ""
	for i in 2:
		var k: String = [key, key2][i]
		var t: String = [text, text2][i]
		_keys[i][0].visible = k != ""
		_keys[i][0].text = k
		_keys[i][1].visible = t != ""
		_keys[i][1].text = t


func _build() -> void:
	var stats := PanelContainer.new()
	stats.add_theme_stylebox_override("panel", UIKit.style(UIKit.BG, UIKit.BORDER, 10, 10))
	stats.position = Vector2(16, 16)
	add_child(stats)
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 12)
	stats.add_child(row)
	var tool_box := PanelContainer.new()
	tool_box.add_theme_stylebox_override("panel", UIKit.style(UIKit.SLOT, UIKit.BORDER * Color(1, 1, 1, 0.6), 6, 4))
	row.add_child(tool_box)
	_tool_icon = UIKit.icon(null, 44)
	tool_box.add_child(_tool_icon)
	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 4)
	row.add_child(col)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 14)
	col.add_child(top)
	_tool_name = UIKit.label("", Color.WHITE, 14)
	top.add_child(_tool_name)
	top.add_child(UIKit.spacer())
	_coins = UIKit.label("", UIKit.RARE, 14)
	_coins.tooltip_text = "Coins (TEST: earned at the merchant, the battle board and the dig)"
	_coins.mouse_filter = Control.MOUSE_FILTER_STOP
	top.add_child(_coins)
	var energy_row := HBoxContainer.new()
	energy_row.add_theme_constant_override("separation", 8)
	col.add_child(energy_row)
	energy_row.add_child(UIKit.label("Energy", UIKit.MUTED, 13))
	_energy_bar = ProgressBar.new()
	_energy_bar.custom_minimum_size = Vector2(130, 14)
	_energy_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_energy_bar.max_value = GameData.ENERGY_MAX
	_energy_bar.show_percentage = false
	_energy_bar.mouse_filter = Control.MOUSE_FILTER_STOP
	_energy_bar.add_theme_stylebox_override("background", UIKit.style(UIKit.SLOT, UIKit.BORDER * Color(1, 1, 1, 0.4), 4, 0))
	_energy_bar.add_theme_stylebox_override("fill", UIKit.style(UIKit.ENERGY, UIKit.ENERGY, 4, 0))
	energy_row.add_child(_energy_bar)
	_energy_text = UIKit.label("", Color.WHITE, 13)
	energy_row.add_child(_energy_text)
	col.add_child(UIKit.label("I inventory  ·  Q switch tool", UIKit.MUTED, 12))

	var bottom := VBoxContainer.new()
	bottom.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	bottom.grow_horizontal = Control.GROW_DIRECTION_BOTH
	bottom.grow_vertical = Control.GROW_DIRECTION_BEGIN
	bottom.offset_bottom = -40
	bottom.alignment = BoxContainer.ALIGNMENT_END
	bottom.add_theme_constant_override("separation", 8)
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bottom)
	_loot = VBoxContainer.new()
	_loot.alignment = BoxContainer.ALIGNMENT_END
	_loot.add_theme_constant_override("separation", 4)
	_loot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bottom.add_child(_loot)
	_prompt = PanelContainer.new()
	_prompt.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_prompt.add_theme_stylebox_override("panel", UIKit.style(UIKit.BG, UIKit.BORDER, 8, 8))
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bottom.add_child(_prompt)
	var prow := HBoxContainer.new()
	prow.add_theme_constant_override("separation", 10)
	_prompt.add_child(prow)
	for i in 2:
		var key := UIKit.label("", Color.BLACK, 15)
		var key_bg := UIKit.style(Color(0.95, 0.93, 0.85), Color(0.95, 0.93, 0.85), 4, 0)
		key_bg.content_margin_left = 8
		key_bg.content_margin_right = 8
		key.add_theme_stylebox_override("normal", key_bg)
		var text := UIKit.label("", Color.WHITE, 16)
		prow.add_child(key)
		prow.add_child(text)
		_keys.append([key, text])
	_prompt.visible = false


func _on_energy(value: int) -> void:
	_energy_bar.value = value
	_energy_text.text = "%d / %d" % [value, GameData.ENERGY_MAX]


func _on_coins(value: int) -> void:
	_coins.text = "%d coins" % value


func _on_held(id: String) -> void:
	_tool_icon.texture = GameData.tool_icon(id)
	_tool_name.text = GameData.tools[id].label


func _line(content: Control, rare: bool) -> void:
	var line := PanelContainer.new()
	line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	line.add_theme_stylebox_override("panel", UIKit.style(UIKit.BG, UIKit.RARE if rare else UIKit.BORDER * Color(1, 1, 1, 0.5), 6, 6))
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(content)
	_loot.add_child(line)
	var shown := _loot.get_children().filter(func(c): return c.visible)
	for i in shown.size() - 6:   # keep the newest six; each frees itself when its time is up
		shown[i].visible = false
	get_tree().create_timer(LINE_TIME).timeout.connect(line.queue_free)


## `id` is an item id or a tool id (a newly crafted tool).
func _on_looted(id: String, count: int, rare: bool) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var tex := GameData.item_icon(id)
	if tex:
		row.add_child(UIKit.icon(tex, 28))
	row.add_child(UIKit.label("+%d %s" % [count, GameData.item_label(id)], UIKit.RARE if rare else Color.WHITE, 15))
	_line(row, rare)


func _on_message(text: String) -> void:
	_line(UIKit.label(text, UIKit.MUTED, 15), false)
