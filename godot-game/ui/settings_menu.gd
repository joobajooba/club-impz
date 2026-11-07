extends CanvasLayer
## Settings (game_menus.md section 3.4), as the Settings autoload: the gear button left of Profile in
## the top-right corner, and a window with three tabs:
## - Options: fullscreen, shadows, camera field of view, mouse sensitivity, invert camera up/down,
## - Sound: a volume slider per audio bus (Master, Music, Effects, Ambient, Interface) and Mute all,
## - Controls: help listing every key, read from the Input Map so it always matches the real bindings.
## Esc opens it when no other menu is open, and closes it. Values save to user://settings.cfg (this device).
##
## The game has no sound files yet. The buses are made here so every future sound only has to pick its
## bus (biome ambience already plays on "Ambient"), and these sliders will control it.

signal changed

const FILE := "user://settings.cfg"
const BUSES := ["Master", "Music", "Effects", "Ambient", "Interface"]
const BUS_HELP := {
	"Master": "Everything", "Music": "Songs", "Effects": "Mining, crafting, footsteps",
	"Ambient": "Wind, birds, water", "Interface": "Menu clicks and pickups",
}
const TABS := [{key = "options", label = "Options"}, {key = "sound", label = "Sound"}, {key = "controls", label = "Controls"}]
## Keys shown on the Controls tab: [what it does, actions]. Esc and the mouse buttons are added in _render_controls.
const CONTROLS := [
	["Move", ["move_forward", "move_left", "move_back", "move_right"]],
	["Jump", ["jump"]],
	["Sprint (hold)", ["sprint"]],
	["Turn the camera (hold and drag)", ["camera_orbit"]],
	["Zoom in / out", ["camera_zoom_in", "camera_zoom_out"]],
	["Customize your Imp", ["customize"]],
]
const TEST_KEYS := [
	["Show FPS and position", ["toggle_debug"]],
	["Next biome (resource world)", ["debug_next_biome"]],
	["Day / night", ["toggle_day_night"]],
	["Very fast sprint", ["toggle_fast_sprint"]],
	["Free camera (debug builds)", ["toggle_camera_mode"]],
]

var fullscreen := false
var shadows := true
var fov := 62.0
var mouse_sensitivity := 1.0      # times the controller's own orbit_sensitivity
var invert_y := false
var volume := {"Master": 0.8, "Music": 0.8, "Effects": 0.8, "Ambient": 0.8, "Interface": 0.8}
var muted := false

var tab := "options"
var gear_button: Button
var _window: CanvasLayer          # the window, in the "modal" group (the gear button's layer always shows)
var _tab_buttons := {}
var _list: VBoxContainer


func _ready() -> void:
	layer = 20
	_make_buses()
	_load()
	_build()
	_window.visible = false
	get_tree().node_added.connect(_on_node_added)
	_apply()


# --- values -------------------------------------------------------------------------------

func _make_buses() -> void:
	for bus in BUSES:
		if AudioServer.get_bus_index(bus) == -1:
			AudioServer.add_bus()
			var i := AudioServer.bus_count - 1
			AudioServer.set_bus_name(i, bus)
			AudioServer.set_bus_send(i, "Master")


func _apply() -> void:
	for bus in BUSES:
		var i := AudioServer.get_bus_index(bus)
		var v: float = volume.get(bus, 0.8)
		AudioServer.set_bus_volume_db(i, linear_to_db(maxf(v, 0.0001)))
		AudioServer.set_bus_mute(i, v <= 0.0 or (muted and bus == "Master"))
	var mode := DisplayServer.window_get_mode()
	var full := mode == DisplayServer.WINDOW_MODE_FULLSCREEN or mode == DisplayServer.WINDOW_MODE_EXCLUSIVE_FULLSCREEN
	if fullscreen != full:
		DisplayServer.window_set_mode(DisplayServer.WINDOW_MODE_FULLSCREEN if fullscreen else DisplayServer.WINDOW_MODE_WINDOWED)
	for sun in get_tree().root.find_children("*", "DirectionalLight3D", true, false):
		_apply_shadows(sun)
	changed.emit()          # the player's camera reads fov, mouse_sensitivity and invert_y (imp_player.gd)


func _on_node_added(node: Node) -> void:
	if node is DirectionalLight3D:      # a world just loaded: its sun follows the Shadows option
		_apply_shadows.call_deferred(node)


func _apply_shadows(light: DirectionalLight3D) -> void:
	if not is_instance_valid(light) or light.get_viewport() != get_viewport():
		return              # leave lights in other viewports alone (the customizer's preview)
	if not light.has_meta("had_shadow"):
		light.set_meta("had_shadow", light.shadow_enabled)
	light.shadow_enabled = shadows and light.get_meta("had_shadow")


func set_value(key: String, value) -> void:
	set(key, value)
	_apply()
	_save()


func set_volume(bus: String, value: float) -> void:
	volume[bus] = value
	_apply()
	_save()


func reset() -> void:
	fullscreen = false
	shadows = true
	fov = 62.0
	mouse_sensitivity = 1.0
	invert_y = false
	for bus in BUSES:
		volume[bus] = 0.8
	muted = false
	_apply()
	_save()
	_refresh()


func _load() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(FILE) != OK:
		return
	fullscreen = bool(cfg.get_value("options", "fullscreen", fullscreen))
	shadows = bool(cfg.get_value("options", "shadows", shadows))
	fov = clampf(float(cfg.get_value("options", "fov", fov)), 45.0, 90.0)
	mouse_sensitivity = clampf(float(cfg.get_value("options", "mouse_sensitivity", mouse_sensitivity)), 0.25, 3.0)
	invert_y = bool(cfg.get_value("options", "invert_y", invert_y))
	muted = bool(cfg.get_value("sound", "muted", muted))
	for bus in BUSES:
		volume[bus] = clampf(float(cfg.get_value("sound", bus, volume[bus])), 0.0, 1.0)


func _save() -> void:
	var cfg := ConfigFile.new()
	for key in ["fullscreen", "shadows", "fov", "mouse_sensitivity", "invert_y"]:
		cfg.set_value("options", key, get(key))
	cfg.set_value("sound", "muted", muted)
	for bus in BUSES:
		cfg.set_value("sound", bus, volume[bus])
	cfg.save(FILE)


# --- opening -------------------------------------------------------------------------------

func open() -> void:
	_window.visible = true
	_refresh()


func close() -> void:
	_window.visible = false


func toggle() -> void:
	if _window.visible:
		close()
	elif _others_open():
		return
	else:
		open()


func _others_open() -> bool:
	for n in get_tree().get_nodes_in_group("modal"):
		if n != _window and n.visible:
			return true
	var profile_menu = ProfileUI.get("menu")
	return profile_menu != null and profile_menu.visible


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo and event.keycode == KEY_ESCAPE):
		return
	if _window.visible:
		close()
		get_viewport().set_input_as_handled()
	elif not _others_open():
		var main := get_tree().get_first_node_in_group("game_main")
		if main and main.get("free_cam") != null:
			return
		open()
		get_viewport().set_input_as_handled()


# --- tabs ----------------------------------------------------------------------------------

func _refresh() -> void:
	if not _window.visible:
		return
	for key in _tab_buttons:
		_tab_buttons[key].button_pressed = key == tab
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	match tab:
		"options": _render_options()
		"sound": _render_sound()
		"controls": _render_controls()


func _render_options() -> void:
	_heading("Display")
	_toggle_row("Fullscreen", "fullscreen")
	_toggle_row("Shadows", "shadows", "Turn off for more speed on slow computers.")
	_slider_row("Field of view", fov, 45.0, 90.0, 1.0, func(v): set_value("fov", v), func(v): return "%d°" % int(v))
	_heading("Camera")
	_slider_row("Mouse sensitivity", mouse_sensitivity, 0.25, 3.0, 0.05, func(v): set_value("mouse_sensitivity", v),
		func(v): return "%.2fx" % v)
	_toggle_row("Invert camera up / down", "invert_y")
	var r := UIKit.row(_list)
	r.add_child(UIKit.spacer())
	r.add_child(UIKit.button("Reset to defaults", true, reset))


func _render_sound() -> void:
	_heading("Volume")
	for bus in BUSES:
		_slider_row(bus, volume[bus], 0.0, 1.0, 0.05, func(v): set_volume(bus, v),
			func(v): return "Off" if v <= 0.0 else "%d%%" % roundi(v * 100.0), BUS_HELP[bus])
	_toggle_row("Mute all", "muted")
	_note("The game has no sounds yet. These sliders are ready for them, and your choice is kept.")


func _render_controls() -> void:
	_heading("Keys")
	for row in CONTROLS:
		_key_row(row[0], _keys_for(row[1]))
	_key_row("Settings, or close a menu", ["Esc"])
	_heading("Test keys")
	for row in TEST_KEYS:
		_key_row(row[0], _keys_for(row[1]))
	_note("Keys can't be changed yet. Mining, the inventory and stations (I, F, Q, T) come back to the hub and resource world later.")


## Every key bound to these actions, in order, without repeats ("W", "Up", "Right mouse").
func _keys_for(actions: Array) -> Array:
	var out := []
	for action in actions:
		if not InputMap.has_action(action):
			continue
		for ev in InputMap.action_get_events(action):
			var text := _event_text(ev)
			if text != "" and not text in out:
				out.append(text)
	# movement reads better as "W A S D" then "Up Left Down Right": letters first
	out.sort_custom(func(a, b): return a.length() == 1 and b.length() > 1)
	return out


static func _event_text(ev: InputEvent) -> String:
	if ev is InputEventKey:
		var code: int = ev.physical_keycode if ev.physical_keycode != 0 else ev.keycode
		return OS.get_keycode_string(code)
	if ev is InputEventMouseButton:
		match ev.button_index:
			MOUSE_BUTTON_LEFT: return "Left mouse"
			MOUSE_BUTTON_RIGHT: return "Right mouse"
			MOUSE_BUTTON_MIDDLE: return "Middle mouse"
			MOUSE_BUTTON_WHEEL_UP: return "Wheel up"
			MOUSE_BUTTON_WHEEL_DOWN: return "Wheel down"
	return ""


# --- rows ----------------------------------------------------------------------------------

func _heading(text: String) -> void:
	_list.add_child(UIKit.title(text, 19))


func _note(text: String) -> void:
	var l := UIKit.label(text, UIKit.MUTED, 13)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_child(l)


func _name_box(text: String, help := "") -> VBoxContainer:
	var box := VBoxContainer.new()
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_constant_override("separation", 0)
	box.add_child(UIKit.label(text, Color.WHITE, 16))
	if help != "":
		box.add_child(UIKit.label(help, UIKit.MUTED, 12))
	return box


func _toggle_row(text: String, key: String, help := "") -> void:
	var r := UIKit.row(_list)
	r.add_child(_name_box(text, help))
	var on: bool = get(key)
	var b := UIKit.button("On" if on else "Off", true, func(): set_value(key, not get(key)); _refresh())
	b.custom_minimum_size.x = 80
	if on:
		b.add_theme_color_override("font_color", UIKit.GOOD)
		b.add_theme_color_override("font_hover_color", UIKit.GOOD)
	r.add_child(b)


func _slider_row(text: String, value: float, lo: float, hi: float, step: float, on_change: Callable, fmt: Callable, help := "") -> void:
	var r := UIKit.row(_list)
	r.add_child(_name_box(text, help))
	var s := HSlider.new()
	s.min_value = lo
	s.max_value = hi
	s.step = step
	s.value = value
	s.custom_minimum_size = Vector2(220, 28)
	s.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	s.focus_mode = Control.FOCUS_NONE
	# a slider draws its track as tall as the box's content margins, so give the bar boxes some
	s.add_theme_stylebox_override("slider", _thick(UIKit.bar_track()))
	s.add_theme_stylebox_override("grabber_area", _thick(UIKit.bar(UIKit.GOLD)))
	s.add_theme_stylebox_override("grabber_area_highlight", _thick(UIKit.bar(UIKit.RARE)))
	var knob := UIKit.pixel_texture(KNOB, UIKit.KEY)
	s.add_theme_icon_override("grabber", knob)
	s.add_theme_icon_override("grabber_highlight", knob)
	r.add_child(s)
	var shown := UIKit.label(fmt.call(value), UIKit.KEY, 15)
	shown.custom_minimum_size.x = 56
	shown.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	r.add_child(shown)
	s.value_changed.connect(func(v: float):
		shown.text = fmt.call(v)
		on_change.call(v))


static func _thick(box: StyleBox) -> StyleBox:
	var b := box.duplicate() as StyleBox
	b.content_margin_top = 7.0
	b.content_margin_bottom = 7.0
	return b


const KNOB := [".kkkk.", "kYYyyk", "kYyyok", "kYyyok", "kyyook", ".kkkk."]


func _key_row(text: String, keys: Array) -> void:
	var r := UIKit.row(_list)
	r.add_child(_name_box(text))
	for k in keys:
		var cap := Label.new()
		cap.text = k
		cap.add_theme_stylebox_override("normal", UIKit.key_cap())
		cap.add_theme_color_override("font_color", UIKit.OUTLINE)
		cap.add_theme_font_size_override("font_size", 14)
		cap.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		cap.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		cap.custom_minimum_size.x = 30
		r.add_child(cap)


# --- layout --------------------------------------------------------------------------------

func _build() -> void:
	gear_button = UIKit.icon_button(UIKit.GEAR, "Settings (Esc)")
	gear_button.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	gear_button.offset_left = -16 - UIKit.ICON_BUTTON   # the top-right corner, right of the Profile button
	gear_button.offset_top = 16                          # (ui/profile/profile_ui.gd)
	gear_button.offset_right = -16
	gear_button.offset_bottom = 16 + UIKit.ICON_BUTTON
	gear_button.pressed.connect(toggle)
	add_child(gear_button)

	_window = CanvasLayer.new()
	_window.name = "window"
	_window.layer = 18                     # under the Profile and gear buttons (20), over the customizer (16)
	_window.add_to_group("modal")          # the player stands still while it is open
	add_child(_window)
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_window.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_window.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel())
	center.add_child(panel)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 10)
	panel.add_child(vbox)
	var head := HBoxContainer.new()
	vbox.add_child(head)
	head.add_child(UIKit.title("Settings"))
	head.add_child(UIKit.spacer())
	head.add_child(UIKit.button("Close", true, close))
	vbox.add_child(UIKit.divider())
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	vbox.add_child(tabs)
	for t in TABS:
		var b := UIKit.button(t.label, true, func(): tab = t.key; _refresh())
		b.toggle_mode = true
		_tab_buttons[t.key] = b
		tabs.add_child(b)
	var well := PanelContainer.new()
	well.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 12.0))
	vbox.add_child(well)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(640, 400)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	well.add_child(scroll)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_theme_constant_override("separation", 10)
	scroll.add_child(_list)
