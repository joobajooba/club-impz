extends CanvasLayer
## The character customizer (game_menus.md section 3.5), as the Customizer autoload: the in-game version
## of impz.club's Imp Customization page. C opens it; Esc, C or Cancel closes it and keeps the old look.
##
## Tabs Body, Head, Eyes, Clothing and Back list every trait (text only, like the website). Traits the
## player can't use are greyed with a lock (Look.owns). The right side is a turning 3D preview of the
## draft look: drag to turn, wheel to zoom. "Wear it" puts the draft on the player (Look.wear, saved).
## The Saved tab lists the builds the linked wallet saved on impz.club, each with Load.

const TABS := [
	{key = "body", label = "Body"}, {key = "head", label = "Head"}, {key = "eyes", label = "Eyes"},
	{key = "clothing", label = "Clothing"}, {key = "back", label = "Back"}, {key = "saved", label = "Saved"},
]
const PREVIEW_SIZE := Vector2i(380, 380)
const TARGET := Vector3(0, 56, 0)

var draft := {}
var tab := "body"
var spin := true

var _tab_buttons := {}
var _list: VBoxContainer
var _status: Label
var _test_toggle: CheckButton
var _holder: Node3D
var _camera: Camera3D
var _spin_button: Button
var _yaw := 0.5
var _pitch := 0.12
var _dist := 260.0
var _dragging := false


func _ready() -> void:
	layer = 16
	add_to_group("modal")
	_build()
	visible = false
	Look.changed.connect(_on_look_changed)
	Look.wallet_changed.connect(_refresh)


func open() -> void:
	draft = Look.shown()
	Look.sync_wallet()
	visible = true
	_refresh()
	_rebuild_preview()


func close() -> void:
	visible = false
	_dragging = false
	_clear_preview()


func wear() -> void:
	var look := draft.duplicate()
	close()
	Look.wear(look)


func _unhandled_input(event: InputEvent) -> void:
	if not (event is InputEventKey and event.pressed and not event.echo):
		return
	if visible and (event.keycode == KEY_ESCAPE or event.is_action("customize")):
		close()
		get_viewport().set_input_as_handled()
	elif not visible and event.is_action("customize") and _can_open():
		open()
		get_viewport().set_input_as_handled()


func _can_open() -> bool:
	for n in get_tree().get_nodes_in_group("modal"):
		if n != self and n.visible:
			return false
	var main := get_tree().get_first_node_in_group("game_main")
	if main and (main.get("free_cam") != null or main.get("busy")):
		return false          # C moves the free camera down in camera mode (key 7); world changes fade
	return true


func _process(delta: float) -> void:
	if not visible or _camera == null:
		return
	if spin and not _dragging:
		_yaw += delta * 0.5
	var dir := Vector3(sin(_yaw) * cos(_pitch), sin(_pitch), cos(_yaw) * cos(_pitch))
	_camera.position = TARGET + dir * _dist
	_camera.look_at(TARGET)


# --- choosing ---------------------------------------------------------------------------

func _pick(slot: String, id: String) -> void:
	draft[slot] = id
	_refresh()
	_rebuild_preview()


func _randomize() -> void:
	for slot in ImpBuilder.SLOTS:
		var options := []
		for e in ImpBuilder.manifest().get(slot, []):
			if Look.owns(slot, e.id):
				options.append(e.id)
		if slot != "body":
			options.append("")
		draft[slot] = options.pick_random()
	_refresh()
	_rebuild_preview()


func _reset() -> void:
	draft = Look.BASE.duplicate()
	_refresh()
	_rebuild_preview()


func _load_saved(build: Dictionary) -> void:
	for slot in ImpBuilder.SLOTS:
		var v = build.get(slot)
		draft[slot] = Look.BASE[slot] if v == null else str(v)
	tab = "body"
	_refresh()
	_rebuild_preview()
	_status.text = "Loaded \"%s\". Press Wear it to put it on." % build.get("name", "build")


func _on_look_changed() -> void:
	if not visible:
		return
	# ownership changed while open (wallet linked, test switch): drop anything now locked
	for slot in ImpBuilder.SLOTS:
		if not Look.owns(slot, draft.get(slot, "")):
			draft[slot] = Look.BASE[slot]
	_refresh()
	_rebuild_preview()


# --- list -------------------------------------------------------------------------------

func _refresh() -> void:
	if not visible:
		return
	for key in _tab_buttons:
		_tab_buttons[key].button_pressed = key == tab
	for c in _list.get_children():
		_list.remove_child(c)
		c.queue_free()
	if tab == "saved":
		_render_saved()
	else:
		_render_slot(tab)
	_status.text = _status_text()
	if _test_toggle:
		_test_toggle.set_pressed_no_signal(Look.test_all)


func _render_slot(slot: String) -> void:
	if slot != "body":
		_list.add_child(_option_row(slot, "", "None", true))
	for e in ImpBuilder.manifest().get(slot, []):
		_list.add_child(_option_row(slot, e.id, e.name, Look.owns(slot, e.id)))


func _option_row(slot: String, id: String, label: String, unlocked: bool) -> Button:
	var chosen: bool = draft.get(slot, "") == id
	var b := UIKit.button(("> " if chosen else "   ") + label + ("" if unlocked else "   (locked)"), unlocked,
		func(): _pick(slot, id))
	b.alignment = HORIZONTAL_ALIGNMENT_LEFT
	b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	b.custom_minimum_size.y = 34
	if chosen:
		b.add_theme_color_override("font_color", UIKit.RARE)
		b.add_theme_color_override("font_hover_color", UIKit.RARE)
	var from := Look.sources(slot, id)
	if not unlocked:
		b.tooltip_text = "None of your Impz has this trait."
	elif not from.is_empty():
		b.tooltip_text = "From Imp " + ", ".join(from.map(func(n): return "#%d" % int(n)))
	return b


func _render_saved() -> void:
	if Look.wallet == "":
		_note("Link your wallet in the Profile panel (top right) to see the Impz you saved on impz.club.")
		return
	if Look.state == "loading":
		_note("Checking your wallet...")
		return
	if Look.saved.is_empty():
		_note("No saved Impz yet. Build one on impz.club/imp-customization and press Save there.")
		return
	for build in Look.saved:
		var row := HBoxContainer.new()
		row.add_theme_constant_override("separation", 10)
		var text := VBoxContainer.new()
		text.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		text.add_child(UIKit.label(str(build.get("name", "Imp")), Color.WHITE, 16))
		var parts := []
		var usable := true
		for slot in ImpBuilder.SLOTS:
			var v = build.get(slot)
			if v != null and str(v) != "":
				parts.append(ImpBuilder.name_of(slot, str(v)))
				usable = usable and Look.owns(slot, str(v))
		var line := UIKit.label(" · ".join(parts), UIKit.MUTED, 13)
		line.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
		text.add_child(line)
		if not usable:
			text.add_child(UIKit.label("Uses a trait from an Imp no longer in this wallet", UIKit.SHORT, 12))
		row.add_child(text)
		row.add_child(UIKit.button("Load", usable, func(): _load_saved(build)))
		_list.add_child(row)


func _note(text: String) -> void:
	var l := UIKit.label(text, UIKit.MUTED, 14)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_child(l)


func _status_text() -> String:
	var test := "   TEST: all traits unlocked." if Look.test_all else ""
	match Look.state:
		"loading":
			return "Checking the Impz in %s..." % _short(Look.wallet) + test
		"ready":
			var n := Look.imps.size()
			if n == 0:
				return "%s holds no Impz, so you have the base imp." % _short(Look.wallet) + test
			return "%s · %d Imp%s · traits from your Impz are unlocked." % [_short(Look.wallet), n, "" if n == 1 else "z"] + test
		"error":
			return Look.error + test
	return "No wallet linked: you have the base imp. Link one in Profile (top right) to unlock your Impz' traits." + test


static func _short(address: String) -> String:
	return address.substr(0, 6) + "..." + address.right(4) if address.length() > 12 else address


# --- preview ----------------------------------------------------------------------------

func _clear_preview() -> void:
	if _holder == null:
		return
	for c in _holder.get_children():
		_holder.remove_child(c)
		c.queue_free()


func _rebuild_preview() -> void:
	_clear_preview()
	_holder.add_child(ImpBuilder.build(draft))


func _on_preview_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_dist = maxf(110.0, _dist - 18.0)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_dist = minf(480.0, _dist + 18.0)
	elif event is InputEventMouseMotion and _dragging:
		_yaw -= event.relative.x * 0.01
		_pitch = clampf(_pitch + event.relative.y * 0.006, -0.35, 0.9)


func _toggle_spin() -> void:
	spin = not spin
	_spin_button.text = "Stop spin" if spin else "Spin"


# --- layout -----------------------------------------------------------------------------

func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel())
	center.add_child(panel)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	panel.add_child(vbox)

	var head := HBoxContainer.new()
	vbox.add_child(head)
	head.add_child(UIKit.title("Customize your Imp"))
	head.add_child(UIKit.spacer())
	head.add_child(UIKit.button("Close", true, close))
	vbox.add_child(UIKit.divider())

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 18)
	vbox.add_child(body)

	# left: tabs, the option list, the wallet line
	var left := VBoxContainer.new()
	left.custom_minimum_size = Vector2(520, 0)
	left.add_theme_constant_override("separation", 10)
	body.add_child(left)
	var tabs := HBoxContainer.new()
	tabs.add_theme_constant_override("separation", 6)
	left.add_child(tabs)
	for t in TABS:
		var b := UIKit.button(t.label, true, func(): tab = t.key; _refresh())
		b.toggle_mode = true
		_tab_buttons[t.key] = b
		tabs.add_child(b)
	var well := PanelContainer.new()
	well.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 8.0))
	well.size_flags_vertical = Control.SIZE_EXPAND_FILL
	left.add_child(well)
	var scroll := ScrollContainer.new()
	scroll.custom_minimum_size = Vector2(0, 300)
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	well.add_child(scroll)
	_list = VBoxContainer.new()
	_list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_list.add_theme_constant_override("separation", 4)
	scroll.add_child(_list)
	_status = UIKit.label("", UIKit.MUTED, 13)
	_status.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_status.custom_minimum_size = Vector2(520, 36)
	left.add_child(_status)

	# right: the 3D preview in its own little world
	var right := VBoxContainer.new()
	right.add_theme_constant_override("separation", 8)
	body.add_child(right)
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIKit.slot(Color(0.16, 0.2, 0.26, 1.0), UIKit.OUTLINE, 1, 3.0))
	right.add_child(frame)
	var container := SubViewportContainer.new()
	container.stretch = true
	container.custom_minimum_size = PREVIEW_SIZE
	container.mouse_default_cursor_shape = Control.CURSOR_DRAG
	container.gui_input.connect(_on_preview_input)
	frame.add_child(container)
	var vp := SubViewport.new()
	vp.own_world_3d = true
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.size = PREVIEW_SIZE
	container.add_child(vp)
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.78, 0.8, 0.9)
	env.environment.ambient_light_energy = 0.9
	vp.add_child(env)
	var key := DirectionalLight3D.new()
	key.light_energy = 1.1
	vp.add_child(key)
	key.look_at_from_position(Vector3(60, 140, 120), Vector3.ZERO)
	var rim := DirectionalLight3D.new()
	rim.light_energy = 0.5
	vp.add_child(rim)
	rim.look_at_from_position(Vector3(-80, 60, -120), Vector3.ZERO)
	var floor_disc := MeshInstance3D.new()
	var disc := CylinderMesh.new()
	disc.top_radius = 46.0
	disc.bottom_radius = 46.0
	disc.height = 0.5
	disc.radial_segments = 48
	var disc_mat := StandardMaterial3D.new()
	disc_mat.albedo_color = Color(1, 1, 1, 0.1)
	disc_mat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	disc_mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	disc.material = disc_mat
	floor_disc.mesh = disc
	floor_disc.position.y = -0.3
	vp.add_child(floor_disc)
	_camera = Camera3D.new()
	_camera.fov = 32.0
	_camera.near = 1.0
	_camera.far = 2000.0
	vp.add_child(_camera)
	_holder = Node3D.new()
	vp.add_child(_holder)
	var under := HBoxContainer.new()
	right.add_child(under)
	under.add_child(UIKit.label("Drag to turn · wheel to zoom", UIKit.MUTED, 13))
	under.add_child(UIKit.spacer())
	_spin_button = UIKit.button("Stop spin", true, _toggle_spin)
	under.add_child(_spin_button)

	var foot := HBoxContainer.new()
	foot.add_theme_constant_override("separation", 8)
	vbox.add_child(foot)
	foot.add_child(UIKit.button("Random", true, _randomize))
	foot.add_child(UIKit.button("Reset", true, _reset))
	if OS.is_debug_build():
		_test_toggle = CheckButton.new()
		_test_toggle.text = "All traits (TEST)"
		_test_toggle.focus_mode = Control.FOCUS_NONE
		_test_toggle.add_theme_color_override("font_color", UIKit.MUTED)
		_test_toggle.toggled.connect(func(on: bool): Look.test_all = on)
		foot.add_child(_test_toggle)
	foot.add_child(UIKit.spacer())
	foot.add_child(UIKit.button("Cancel", true, close))
	var wear_button := UIKit.button("Wear it", true, wear)
	wear_button.custom_minimum_size.x = 120
	wear_button.add_theme_color_override("font_color", UIKit.RARE)
	foot.add_child(wear_button)
