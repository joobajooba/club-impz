extends CanvasLayer
## The chat box on the right of the screen (autoload "Chat"). Two channels, switched with the tabs at the top:
##   Global        everyone online, in every world: "username | message", the name in red and the text in white.
##                 Enter starts typing (the Imp stands still meanwhile), Enter sends, Esc stops. At most 100
##                 characters; ChatFilter refuses slurs and abuse and stars out swearing (the server checks again).
##   World events  the comms: ore events starting and running out (OreEvents), and anything sent to event().
## The × button closes the box; the Chat button on the right edge opens it again and counts what came in meanwhile.

const NAME_COLOR := Color("#ff4a4a")
const TEXT_COLOR := Color.WHITE
const SYSTEM_COLOR := Color(0.75, 0.74, 0.68)
const EVENT_COLOR := Color(1.0, 0.86, 0.4)
const KEEP := 100
const MIN_GAP_MS := 700

var channel := "global"
var _lines := {"global": [], "events": []}
var _unread := {"global": 0, "events": 0}
var _panel: PanelContainer
var _log: RichTextLabel
var _entry: LineEdit
var _count: Label
var _input_row: HBoxContainer
var _events_hint: Label
var _tabs := {}
var _open_button: Button
var _event_ore := {}            # event id -> {ore, until} (the end message needs the name)
var _last_sent := -100000
var _offline_noted := false
var _written := 0


func _ready() -> void:
	layer = 14                  # over the HUD, under the menus (15+) and the loading screen
	_build()
	OreEvents.started.connect(_on_ore_started)
	OreEvents.ended.connect(_on_ore_ended)
	_render()


func is_typing() -> bool:
	return _entry != null and _entry.has_focus()


func is_open() -> bool:
	return _panel.visible


# --- adding lines ------------------------------------------------------------------------------------

func add_chat(user: String, text: String) -> void:
	_add("global", {kind = "chat", name = user, text = text})


func system(text: String) -> void:
	_add("global", {kind = "system", text = text})


## A world event for the comms channel.
func event(text: String) -> void:
	_add("events", {kind = "event", text = text, at = Time.get_time_string_from_system().substr(0, 5)})


## The recent chat the server sends when we join.
func load_history(list: Array) -> void:
	_lines["global"] = _lines["global"].filter(func(l): return l.kind != "chat")
	for m in list:
		_lines["global"].append({kind = "chat", name = str(m.get("name", "")), text = str(m.get("text", ""))})
	_render()


func _add(ch: String, line: Dictionary) -> void:
	_lines[ch].append(line)
	if _lines[ch].size() > KEEP:
		_lines[ch].pop_front()
	if ch == channel and _panel.visible:
		_write(line)
	else:
		_unread[ch] += 1
		_refresh_buttons()


# --- sending -----------------------------------------------------------------------------------------

func _send(text: String) -> void:
	text = ChatFilter.clean(text)
	_entry.clear()
	_update_count("")
	if text == "":
		return
	if Time.get_ticks_msec() - _last_sent < MIN_GAP_MS:
		system("Slow down a little.")
		return
	var res := ChatFilter.check(text)
	if not res.ok:
		system("Message not sent: that kind of language isn't allowed in chat.")
		return
	_last_sent = Time.get_ticks_msec()
	if not Net.send_chat(res.text):
		add_chat(Net.my_name if Net.my_name != "" else "You", res.text)
		if not _offline_noted:
			_offline_noted = true
			system("You're offline, so only you can see this.")


## The server said no.
func refused(why: String) -> void:
	system("Slow down a little." if why == "slow" else "Message not sent: that kind of language isn't allowed in chat.")


# --- world events ------------------------------------------------------------------------------------

func _on_ore_started(ev: Dictionary) -> void:
	_event_ore[ev.id] = {ore = ev.ore, until = int(ev.until)}
	event("%s has spawned somewhere in the world, go mine it!" % OreEvents.label(ev.ore))


func _on_ore_ended(id: int) -> void:
	var e: Dictionary = _event_ore.get(id, {})
	_event_ore.erase(id)
	if e.is_empty():
		return
	if id < 0 and Time.get_ticks_msec() < e.until - 2000:
		return                  # this game's own offline event, replaced by the server's list on joining
	event("The %s has run out." % OreEvents.label(e.ore))


# --- input -------------------------------------------------------------------------------------------

func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k and k.pressed and not k.echo and (k.keycode == KEY_ENTER or k.keycode == KEY_KP_ENTER) and not _modal_open():
		open()
		_set_channel("global")
		_entry.grab_focus()
		get_viewport().set_input_as_handled()


func _input(event: InputEvent) -> void:
	# clicking anywhere outside the box stops typing, so the Imp can move again
	var mb := event as InputEventMouseButton
	if mb and mb.pressed and is_typing() and not _panel.get_global_rect().has_point(mb.position):
		_entry.release_focus()


func _on_input_key(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k and k.pressed and k.keycode == KEY_ESCAPE:
		_entry.release_focus()
		_entry.accept_event()


func _modal_open() -> bool:
	for n in get_tree().get_nodes_in_group("modal"):
		if n.visible:
			return true
	return false


func open() -> void:
	_panel.visible = true
	_open_button.visible = false
	_render()


func close() -> void:
	_entry.release_focus()
	_panel.visible = false
	_open_button.visible = true
	_refresh_buttons()


func _set_channel(ch: String) -> void:
	channel = ch
	_render()


# --- drawing -----------------------------------------------------------------------------------------

func _render() -> void:
	if _log == null:
		return
	_unread[channel] = 0
	_log.clear()
	_written = 0
	for line in _lines[channel]:
		_write(line)
	_input_row.visible = channel == "global"
	_events_hint.visible = channel == "events"
	_refresh_buttons()


func _write(line: Dictionary) -> void:
	# push_color / add_text, never BBCode: what players type is shown exactly as text
	if _written > 0:
		_log.newline()
	_written += 1
	match line.kind:
		"chat":
			_log.push_color(NAME_COLOR)
			_log.add_text(line.name)
			_log.pop()
			_log.push_color(TEXT_COLOR)
			_log.add_text(" | " + line.text)
			_log.pop()
		"event":
			_log.push_color(SYSTEM_COLOR)
			_log.add_text("[%s] " % line.at)
			_log.pop()
			_log.push_color(EVENT_COLOR)
			_log.add_text(line.text)
			_log.pop()
		_:
			_log.push_color(SYSTEM_COLOR)
			_log.add_text(line.text)
			_log.pop()


func _refresh_buttons() -> void:
	for ch in _tabs:
		var b: Button = _tabs[ch]
		var label := "Global" if ch == "global" else "World Events"
		b.text = label + (" (%d)" % _unread[ch] if _unread[ch] > 0 and ch != channel else "")
		b.add_theme_color_override("font_color", UIKit.RARE if ch == channel else UIKit.MUTED)
		b.add_theme_color_override("font_hover_color", UIKit.RARE if ch == channel else Color.WHITE)
		b.add_theme_stylebox_override("normal", UIKit.button_box("pressed" if ch == channel else "normal", UIKit.SLOT, 6.0))
	var total: int = _unread.global + _unread.events
	_open_button.text = "Chat" + (" (%d)" % total if total > 0 else "")


func _update_count(text: String) -> void:
	_count.text = "%d/%d" % [text.length(), ChatFilter.MAX]


func _build() -> void:
	var root := Control.new()
	root.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	root.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(root)

	_panel = PanelContainer.new()
	_panel.anchor_left = 1.0
	_panel.anchor_right = 1.0
	_panel.anchor_top = 0.5
	_panel.anchor_bottom = 0.5
	_panel.offset_left = -376
	_panel.offset_right = -16
	_panel.offset_top = -150
	_panel.offset_bottom = 210
	_panel.add_theme_stylebox_override("panel", UIKit.panel(Color(0.07, 0.08, 0.11, 0.78), UIKit.GOLD, 12.0, true))
	root.add_child(_panel)
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 6)
	_panel.add_child(box)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 4)
	box.add_child(head)
	for ch in ["global", "events"]:
		var t := UIKit.button("", true, _set_channel.bind(ch))
		t.custom_minimum_size = Vector2(0, 30)
		t.add_theme_font_size_override("font_size", 13)
		head.add_child(t)
		_tabs[ch] = t
	head.add_child(UIKit.spacer())
	var x := UIKit.button("×", true, close)
	x.custom_minimum_size = Vector2(30, 30)
	x.tooltip_text = "Close chat"
	head.add_child(x)

	_log = RichTextLabel.new()
	_log.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_log.scroll_following = true
	_log.selection_enabled = false
	_log.bbcode_enabled = false
	_log.add_theme_font_size_override("normal_font_size", 14)
	_log.add_theme_color_override("default_color", TEXT_COLOR)
	_log.add_theme_constant_override("outline_size", 4)
	_log.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.7))
	box.add_child(_log)

	_events_hint = UIKit.label("World events are posted here as they happen.", SYSTEM_COLOR, 12)
	box.add_child(_events_hint)

	_input_row = HBoxContainer.new()
	_input_row.add_theme_constant_override("separation", 4)
	box.add_child(_input_row)
	_entry = LineEdit.new()
	_entry.max_length = ChatFilter.MAX
	_entry.placeholder_text = "Press Enter to chat"
	_entry.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_entry.add_theme_font_size_override("font_size", 14)
	_entry.add_theme_stylebox_override("normal", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 6.0))
	_entry.add_theme_stylebox_override("focus", UIKit.slot(UIKit.SLOT, UIKit.GOLD, 1, 6.0))
	_entry.text_submitted.connect(func(t): _send(t); _entry.release_focus())
	_entry.text_changed.connect(_update_count)
	_entry.gui_input.connect(_on_input_key)
	_input_row.add_child(_entry)
	_count = UIKit.label("", SYSTEM_COLOR, 11)
	_count.custom_minimum_size = Vector2(44, 0)
	_count.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_input_row.add_child(_count)
	_update_count("")
	var send := UIKit.button("Send", true, func(): _send(_entry.text))
	send.custom_minimum_size = Vector2(58, 32)
	_input_row.add_child(send)

	_open_button = UIKit.button("Chat", true, open)
	_open_button.anchor_left = 1.0
	_open_button.anchor_right = 1.0
	_open_button.anchor_top = 0.5
	_open_button.anchor_bottom = 0.5
	_open_button.offset_left = -112
	_open_button.offset_right = -16
	_open_button.offset_top = 170
	_open_button.offset_bottom = 208
	_open_button.tooltip_text = "Open chat"
	_open_button.visible = false
	root.add_child(_open_button)
