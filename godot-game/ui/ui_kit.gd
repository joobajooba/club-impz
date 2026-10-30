class_name UIKit
## Shared look for the game's menus and HUD. Menus are 2D pixel art (D-015), so every frame, slot,
## button and bar is a tiny pixel picture drawn here in code, blown up PX times so its pixels stay
## chunky, and cached. The font is Pixelify Sans (ui/fonts, SIL Open Font Licence), set as the
## project's default font in project.godot.
## - panel: a menu window: dark outline, a bevelled gold frame with a stud in each corner,
## - slot: a recessed square for items and tools (gold and thicker for the held tool),
## - button: raised, with a lip that disappears when pressed,
## - bar: a recessed track with a shaded fill (energy, HP).

const PX := 3                     # screen pixels per art pixel

const BG := Color(0.11, 0.12, 0.15, 0.96)
const SLOT := Color(0.18, 0.19, 0.23, 0.95)
const BORDER := Color(0.85, 0.82, 0.7, 0.6)
const GOLD := Color("#c99a4a")    # the frame metal
const OUTLINE := Color("#0b0c10")
const MUTED := Color(0.75, 0.74, 0.68)
const SHORT := Color(0.95, 0.45, 0.4)
const GOOD := Color(0.55, 0.9, 0.5)
const RARE := Color(1.0, 0.86, 0.4)
const ENERGY := Color(0.98, 0.78, 0.25)
const KEY := Color(0.95, 0.93, 0.85)

## 8 × 8 pixel icons: k outline, Y highlight, y body, o shade.
const COIN := ["..kkkk..", ".kyyyyk.", "kyYYyyok", "kyYyyyok", "kyyyyyok", "kyyyyook", ".kooook.", "..kkkk.."]
const BOLT := ["....kkk.", "...kYyk.", "..kYyk..", ".kYyyyk.", "kkkyyk..", "..kyok..", ".kyok...", ".kkk...."]

static var _cache := {}


# --- frames ---------------------------------------------------------------------------

## A menu window. `small` drops the corner studs and thins the frame (HUD boxes, pickup lines).
static func panel(fill := BG, edge := GOLD, margin := 26.0, small := false) -> StyleBoxTexture:
	var key := "panel|%s|%s|%s|%s" % [fill, edge, margin, small]
	if not _cache.has(key):
		var w := 11 if small else 15
		var inner := 4 if small else 5        # first ring of fill
		var light := edge.lightened(0.4)
		var dark := edge.darkened(0.5)
		var tex := _art(w, w, func(x: int, y: int) -> Color:
			var cut := _cut(x, y, w, w, 2)
			if cut == 0:
				return Color.TRANSPARENT
			var ring := mini(mini(x, y), mini(w - 1 - x, w - 1 - y))
			if cut == 1 or ring == 0:
				return OUTLINE
			var lit := x + y < w - 1          # the top-left half catches the light
			var cx := mini(x, w - 1 - x)
			var cy := mini(y, w - 1 - y)
			if not small and cx in [2, 3] and cy in [2, 3]:
				return Color("#fff2c4") if cx == 2 and cy == 2 else light   # corner stud
			if ring == 1:
				return light if lit else dark
			if ring < inner - 1:
				return edge
			if ring == inner - 1:
				return OUTLINE.lerp(fill, 0.35)
			if ring == inner and y == inner:
				return fill.lightened(0.07)       # a faint shine under the top edge
			return fill)
		_cache[key] = _nine(tex, inner + 1, margin)
	return _cache[key]


## A recessed slot. `thick` 2 doubles the rim (the held tool).
static func slot(fill := SLOT, edge := OUTLINE, thick := 1, margin := 4.0) -> StyleBoxTexture:
	var key := "slot|%s|%s|%s|%s" % [fill, edge, thick, margin]
	if not _cache.has(key):
		var w := 9
		var tex := _art(w, w, func(x: int, y: int) -> Color:
			var cut := _cut(x, y, w, w, 1)
			if cut == 0:
				return Color.TRANSPARENT
			var ring := mini(mini(x, y), mini(w - 1 - x, w - 1 - y))
			if ring < thick:
				return edge.lightened(0.3) if ring == 1 and x + y < w - 1 else edge
			if ring == thick:                 # light from the top-left: shadow inside the top and left
				return fill.darkened(0.5) if (x == thick or y == thick) and x + y < w else fill.lightened(0.15)
			return fill)
		_cache[key] = _nine(tex, thick + 2, margin)
	return _cache[key]


## A raised button: "normal", "hover", "pressed" or "disabled".
static func button_box(state: String, fill := SLOT, margin := 8.0) -> StyleBoxTexture:
	var key := "button|%s|%s|%s" % [state, fill, margin]
	if not _cache.has(key):
		var f := fill
		match state:
			"hover": f = fill.lightened(0.15)
			"pressed": f = fill.darkened(0.15)
			"disabled": f = fill.darkened(0.35)
		var lip := 1 if state == "pressed" else 2
		var w := 9
		var h := 9 + lip
		var tex := _art(w, h, func(x: int, y: int) -> Color:
			var cut := _cut(x, y, w, h, 1)
			if cut == 0:
				return Color.TRANSPARENT
			if cut == 1 or x == 0 or y == 0 or x == w - 1 or y == h - 1:
				return OUTLINE if state != "disabled" else OUTLINE.lerp(f, 0.4)
			if y >= h - 1 - lip:
				return f.darkened(0.5)            # the lip under the button
			if y == 1:
				return f.lightened(0.3)
			return f)
		var s := _nine(tex, 3, margin)
		s.texture_margin_bottom = (2 + lip) * PX
		s.content_margin_top = margin + (PX if state == "pressed" else 0.0)
		s.content_margin_bottom = margin + lip * PX
		_cache[key] = s
	return _cache[key]


## A bar's coloured fill: outlined, light top row, shaded bottom row. 18 px tall.
static func bar(color: Color) -> StyleBoxTexture:
	var key := "bar|%s" % color
	if not _cache.has(key):
		var tex := _art(3, 6, func(x: int, y: int) -> Color:
			if x != 1 or y == 0 or y == 5:
				return OUTLINE
			return [OUTLINE, color.lightened(0.35), color, color, color.darkened(0.35)][y])
		_cache[key] = _nine(tex, 1, 0.0)
	return _cache[key]


## A bar's track, recessed. 18 px tall.
static func bar_track() -> StyleBoxTexture:
	var key := "track"
	if not _cache.has(key):
		var tex := _art(5, 6, func(x: int, y: int) -> Color:
			if x == 0 or y == 0 or x == 4 or y == 5:
				return OUTLINE
			return SLOT.darkened(0.5) if x == 1 or y == 1 else SLOT.darkened(0.2))
		_cache[key] = _nine(tex, 2, 0.0)
	return _cache[key]


## A key cap, for "F Mine Tin".
static func key_cap() -> StyleBoxTexture:
	return button_box("normal", KEY, 6.0)


# --- pieces -------------------------------------------------------------------------

static func button(text: String, enabled := true, on_press := Callable()) -> Button:
	var b := Button.new()
	b.text = text
	b.disabled = not enabled
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = Vector2(70, 38)
	for state in ["normal", "hover", "pressed", "disabled"]:
		b.add_theme_stylebox_override(state, button_box(state))
	b.add_theme_color_override("font_disabled_color", MUTED * Color(1, 1, 1, 0.6))
	if on_press.is_valid():
		b.pressed.connect(on_press)
	return b


static func label(text := "", color := Color.WHITE, size := 15) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_color_override("font_color", color)
	l.add_theme_font_size_override("font_size", size)
	return l


## A menu title: gold, with a hard pixel shadow.
static func title(text := "", size := 28) -> Label:
	var l := label(text, RARE, size)
	l.add_theme_color_override("font_shadow_color", OUTLINE)
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	return l


## A gold rule with a diamond in the middle, under titles and between sections.
static func divider() -> HBoxContainer:
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 0)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var line := _art(1, 2, func(_x: int, y: int) -> Color: return [GOLD.darkened(0.15), OUTLINE][y])
	var gem := _art(5, 5, func(x: int, y: int) -> Color:
		var d := absi(x - 2) + absi(y - 2)
		return Color.TRANSPARENT if d > 2 else (OUTLINE if d == 2 else (RARE if d == 0 else GOLD)))
	for part in [line, gem, line]:
		var t := TextureRect.new()
		t.texture = part
		t.stretch_mode = TextureRect.STRETCH_TILE if part == line else TextureRect.STRETCH_KEEP_CENTERED
		t.size_flags_horizontal = Control.SIZE_EXPAND_FILL if part == line else Control.SIZE_SHRINK_CENTER
		t.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		t.mouse_filter = Control.MOUSE_FILTER_IGNORE
		box.add_child(t)
	return box


## An 8 × 8 pixel icon from COIN or BOLT, in `color`.
static func pixel_icon(rows: Array, color: Color) -> TextureRect:
	var key := "icon|%s|%s" % [rows, color]
	if not _cache.has(key):
		var palette := {"k": OUTLINE, "Y": color.lightened(0.5), "y": color, "o": color.darkened(0.35)}
		_cache[key] = _art(rows[0].length(), rows.size(), func(x: int, y: int) -> Color:
			return palette.get(rows[y][x], Color.TRANSPARENT))
	var t := icon(_cache[key], 8 * PX)
	t.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	return t


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


# --- drawing --------------------------------------------------------------------------

## A w × h art-pixel picture, `paint(x, y)` giving each pixel's colour, each pixel PX × PX on screen.
static func _art(w: int, h: int, paint: Callable) -> ImageTexture:
	var img := Image.create_empty(w * PX, h * PX, false, Image.FORMAT_RGBA8)
	for y in h:
		for x in w:
			var c: Color = paint.call(x, y)
			if c.a > 0.0:
				img.fill_rect(Rect2i(x * PX, y * PX, PX, PX), c)
	return ImageTexture.create_from_image(img)


## For a corner cut `size` pixels deep: 0 outside it, 1 on its edge, 2 inside the shape.
static func _cut(x: int, y: int, w: int, h: int, size: int) -> int:
	var d := mini(x, w - 1 - x) + mini(y, h - 1 - y)
	return 0 if d < size else (1 if d == size else 2)


## A nine-slice box whose corners are `corner` art pixels.
static func _nine(tex: Texture2D, corner: int, margin: float) -> StyleBoxTexture:
	var s := StyleBoxTexture.new()
	s.texture = tex
	s.set_texture_margin_all(corner * PX)
	s.set_content_margin_all(maxf(margin, 0.0))
	return s
