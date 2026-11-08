extends CanvasLayer
## The loading screen shown while a world is built (main.gd change_world). The whole world (terrain,
## trees, plants, colliders round the spawn) is built behind it, so nothing is built while the player
## is in the world and other players' Imps only appear once it is done. Colours from UIKit.

const TIPS := [
	"Press I to open your inventory.",
	"Hold an axe and press E by a tree to chop it.",
	"A better axe chops faster: 5% for every tier above the one a tree needs.",
	"A chopped tree leaves its stump and grows back after 5 minutes.",
	"Press 1 to 5 to take out a tool. To swap a tool, drag one from your inventory onto its tool slot.",
]

var _title: Label
var _bar: ProgressBar
var _text: Label
var _tip: Label


func _ready() -> void:
	layer = 20                                   # over the HUD, menus and the fade
	visible = false
	var bg := ColorRect.new()
	bg.color = Color(0.06, 0.065, 0.08)
	bg.set_anchors_preset(Control.PRESET_FULL_RECT)
	bg.mouse_filter = Control.MOUSE_FILTER_STOP   # nothing behind it can be clicked
	add_child(bg)
	var centre := CenterContainer.new()
	centre.set_anchors_preset(Control.PRESET_FULL_RECT)
	add_child(centre)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel())
	panel.custom_minimum_size = Vector2(460, 0)
	centre.add_child(panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 12)
	panel.add_child(box)
	_title = UIKit.title("", 26)
	_title.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_title)
	box.add_child(UIKit.divider())
	_bar = ProgressBar.new()
	_bar.custom_minimum_size = Vector2(400, 22)
	_bar.max_value = 1.0
	_bar.step = 0.0
	_bar.show_percentage = false
	_bar.add_theme_stylebox_override("fill", UIKit.bar(UIKit.RARE))
	_bar.add_theme_stylebox_override("background", UIKit.bar_track())
	box.add_child(_bar)
	_text = UIKit.label("", UIKit.MUTED, 14)
	_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	box.add_child(_text)
	_tip = UIKit.label("", UIKit.KEY, 13)
	_tip.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_tip.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_tip.custom_minimum_size = Vector2(400, 0)
	box.add_child(_tip)


func open(title: String) -> void:
	_title.text = title
	_tip.text = "Tip: " + TIPS[randi() % TIPS.size()]
	set_progress(0.0, "Loading...")
	visible = true


func set_progress(f: float, text: String) -> void:
	_bar.value = clampf(f, 0.0, 1.0)
	_text.text = "%s  %d%%" % [text, int(clampf(f, 0.0, 1.0) * 100.0)]


func close() -> void:
	visible = false
