extends Node3D
## The hologram over a crate chest in the hub (J00BA, 2026-11-21): the crate's name ("Daily Crate") in gold and,
## under it, how many of its keys this player owns. Facing the camera, bobbing gently. hub_town.gd puts one on
## each chest in GameData.CRATES. The title is in the crate's own colour (gold, green, blue, red).

const TOP := 2.0                 # metres over the chest's base
const BOB := 0.06

var crate := ""
var title := ""
var color := Color("#ffc94a")
var key := ""                    # the key item counted under the title; a crate's own key when crate is set
var _title: Label3D
var _keys: Label3D
var _t := 0.0


func _ready() -> void:
	if crate != "":
		title = GameData.CRATES[crate].label
		key = GameData.CRATES[crate].key
		color = GameData.CRATES[crate].get("color", color)
	_title = _label(title, color, 48, 0.0)
	_keys = _label("", Color("#e8f4ff"), 30, -0.4)
	Inventory.changed.connect(_update)
	_update()


func _label(text: String, tint: Color, size: int, y: float) -> Label3D:
	var l := Label3D.new()
	l.text = text
	l.font = Settings.font()
	l.font_size = size
	l.pixel_size = 0.009
	l.modulate = tint
	l.outline_size = 10
	l.outline_modulate = Color(0.04, 0.04, 0.08, 0.9)
	l.billboard = BaseMaterial3D.BILLBOARD_FIXED_Y
	l.shaded = false
	l.position = Vector3(0, y, 0)
	add_child(l)
	return l


func _update() -> void:
	var n := Inventory.count(key)
	_keys.text = "You have %d key%s" % [n, "" if n == 1 else "s"]
	_keys.modulate = Color("#9cf09a") if n > 0 else Color("#e8f4ff")


func _process(delta: float) -> void:
	_t += delta
	position.y = TOP + sin(_t * 1.6) * BOB
	_title.modulate.a = 0.85 + 0.15 * sin(_t * 3.1)    # a soft hologram flicker
