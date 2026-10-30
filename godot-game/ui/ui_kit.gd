class_name UIKit
## Shared look for the game's menus and HUD: colours and building blocks matching
## ui/profile/profile_ui.gd.

const BG := Color(0.11, 0.12, 0.15, 0.94)
const SLOT := Color(0.18, 0.19, 0.23, 0.95)
const BORDER := Color(0.85, 0.82, 0.7, 0.6)
const MUTED := Color(0.75, 0.74, 0.68)
const SHORT := Color(0.95, 0.45, 0.4)
const GOOD := Color(0.55, 0.9, 0.5)
const RARE := Color(1.0, 0.86, 0.4)
const ENERGY := Color(0.98, 0.78, 0.25)


static func style(color: Color, border := BORDER, radius := 10, margin := 16.0) -> StyleBoxFlat:
	var s := StyleBoxFlat.new()
	s.bg_color = color
	s.border_color = border
	s.set_border_width_all(2)
	s.set_corner_radius_all(radius)
	s.set_content_margin_all(margin)
	return s


static func button(text: String, enabled := true, on_press := Callable()) -> Button:
	var b := Button.new()
	b.text = text
	b.disabled = not enabled
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(70, 34)
	b.add_theme_stylebox_override("normal", style(SLOT, BORDER * Color(1, 1, 1, 0.6), 6, 6))
	b.add_theme_stylebox_override("hover", style(SLOT.lightened(0.12), BORDER, 6, 6))
	b.add_theme_stylebox_override("pressed", style(SLOT.darkened(0.2), BORDER, 6, 6))
	b.add_theme_stylebox_override("disabled", style(SLOT.darkened(0.3), BORDER * Color(1, 1, 1, 0.25), 6, 6))
	if on_press.is_valid():
		b.pressed.connect(on_press)
	return b


static func label(text := "", color := Color.WHITE, size := 15) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_color_override("font_color", color)
	l.add_theme_font_size_override("font_size", size)
	return l


static func icon(tex: Texture2D, size := 32) -> TextureRect:
	var t := TextureRect.new()
	t.texture = tex
	t.custom_minimum_size = Vector2(size, size)
	t.expand_mode = TextureRect.EXPAND_IGNORE_SIZE
	t.stretch_mode = TextureRect.STRETCH_KEEP_ASPECT_CENTERED
	t.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST   # pixel art stays crisp
	return t


## An item with "have/need", red when short. Items without a picture (hilts) show their name.
static func cost_part(id: String, need: int) -> Control:
	var have := Inventory.count(id)
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 2)
	box.tooltip_text = GameData.item_label(id)
	var tex := GameData.item_icon(id)
	if tex:
		box.add_child(icon(tex, 28))
	else:
		box.add_child(label(GameData.item_label(id), MUTED, 13))
	box.add_child(label("%d/%d" % [have, need], Color.WHITE if have >= need else SHORT, 14))
	return box


static func spacer() -> Control:
	var s := Control.new()
	s.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return s


static func row(parent: Control) -> HBoxContainer:
	var r := HBoxContainer.new()
	r.add_theme_constant_override("separation", 10)
	parent.add_child(r)
	return r
