extends Node
## Multiplayer for the live beta, as the Net autoload: everyone who opens the game joins one shared room
## on the beta server (game-server/server.mjs) and sees the other Imps in the same world.
##
## - Web builds connect to their own site: https://<site> -> wss://<site>/ws, so whoever serves the game
##   also runs the room (localhost:8060 when testing, the beta site when live).
## - Desktop builds use [server] url in res://config/server.cfg, or `-- --server=ws://…/ws`.
##   An empty url = play alone.
## - About 10 times a second the game sends where its Imp is. The server checks it and passes it on.
## - The server decides names and looks: a signed-in impz.club account (Profile menu) shows its
##   username and the traits its wallet holds; everyone else is "Guest 1234" in the base Imp.
## If the server can't be reached the game carries on alone and tries again every few seconds.
## - One game per player: the hello carries this browser's device id (and the wallet when signed in). A
##   newer game with the same id or wallet replaces this one, which then stops (state "replaced") and
##   doesn't reconnect until the page is reloaded, so two tabs never fight over the account.

signal status_changed            # connecting / online / offline, or the player count changed

const CONFIG := "res://config/server.cfg"
const DEVICE_FILE := "user://device_id"   # the browser's storage on the web: shared by its tabs
const SEND_EVERY := 0.1
const RemoteImp := preload("res://scripts/player/remote_imp.gd")

var url := ""
var state := "offline"           # offline | connecting | joining | online | full | replaced
var my_id := 0
var my_name := ""
var online := 0

var _ws: WebSocketPeer
var _retry_in := 0.0
var _retry_wait := 2.0
var _send_timer := 0.0
var _last_sent := []             # [position, yaw, moving] last sent
var _world := ""
var _auth := ["", ""]            # [wallet, session] last sent
var _remotes := {}               # id -> RemoteImp
var _info := {}                  # id -> {name, guest, look, world, s}
var _holder: Node3D
var _shown_world := ""           # the world _refresh_visible last placed Imps for
var _hud: Label
var _notice: Label                 # the big "playing in another window" line
var _device := ""


func _ready() -> void:
	url = _pick_url()
	_device = _device_id()
	_make_hud()
	Look.changed.connect(func(): _send({t = "look", look = Look.worn}))
	_show()                               # _process connects once the first world has loaded


func _pick_url() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--server="):
			return a.trim_prefix("--server=")
	if OS.has_feature("web"):
		var origin := str(JavaScriptBridge.eval("window.location.origin"))
		return origin.replace("https://", "wss://").replace("http://", "ws://") + "/ws"
	var cfg := ConfigFile.new()
	return str(cfg.get_value("server", "url", "")).strip_edges() if cfg.load(CONFIG) == OK else ""


## A random id kept in user://, the same for every tab of this browser.
func _device_id() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--bot"):           # a test player beside a normal game on this computer
			return Crypto.new().generate_random_bytes(16).hex_encode()
	var id := FileAccess.get_file_as_string(DEVICE_FILE).strip_edges() if FileAccess.file_exists(DEVICE_FILE) else ""
	if id.length() != 32:
		var c := Crypto.new()
		id = c.generate_random_bytes(16).hex_encode()
		var f := FileAccess.open(DEVICE_FILE, FileAccess.WRITE)
		if f:
			f.store_string(id)
	return id


# --- connection ---------------------------------------------------------------------------

func _connect() -> void:
	_ws = WebSocketPeer.new()
	_ws.inbound_buffer_size = 1 << 20
	state = "connecting"
	if _ws.connect_to_url(url) != OK:
		_lost()
	_show()


func _lost() -> void:
	var was_full := state == "full"
	var replaced := state == "replaced" or (_ws != null and _ws.get_close_code() == 4001)
	_ws = null
	my_id = 0
	state = "replaced" if replaced else ("full" if was_full else "offline")
	_auth = ["", ""]
	for id in _remotes.keys():
		_remove(id)
	_info.clear()
	online = 0
	_retry_in = _retry_wait * (5.0 if was_full else 1.0)
	_retry_wait = minf(_retry_wait * 1.6, 30.0)
	_show()


func _process(delta: float) -> void:
	if _ws == null:
		if state == "replaced":
			return                        # another window has this player now: stay out until a reload
		# Join only once a world has loaded, so the hello carries the real spawn spot: the server takes
		# the hello's position as given and holds every later move to running speed (anti-cheat).
		if url != "" and not _me().is_empty():
			_retry_in -= delta
			if _retry_in <= 0.0:
				_connect()
		return
	_ws.poll()
	match _ws.get_ready_state():
		WebSocketPeer.STATE_OPEN:
			if state == "connecting":
				state = "joining"
				_retry_wait = 2.0
				_hello()
			while _ws.get_available_packet_count() > 0:
				var msg = JSON.parse_string(_ws.get_packet().get_string_from_utf8())
				if msg is Dictionary:
					_on_message(msg)
			if state == "online":
				_send_timer -= delta
				if _send_timer <= 0.0:
					_send_timer = SEND_EVERY
					_send_moves()
		WebSocketPeer.STATE_CLOSED:
			_lost()


## Global chat: false when not online (the chat box then shows it locally).
func send_chat(text: String) -> bool:
	if state != "online":
		return false
	_send({t = "chat", text = text})
	return true


func _send(msg: Dictionary) -> void:
	if _ws and _ws.get_ready_state() == WebSocketPeer.STATE_OPEN and (state == "online" or msg.t == "hello"):
		_ws.send_text(JSON.stringify(msg))


# --- what this game sends ----------------------------------------------------------------------

func _main() -> Node:
	return get_tree().get_first_node_in_group("game_main")


## [world, position, yaw, moving] of the local Imp, or [] outside the game scene.
func _me() -> Array:
	var main = _main()
	if main == null or main.get("player") == null or str(main.get("joined_world")) == "":
		return []
	var p = main.player
	var moving: int = 2 if not p.is_on_floor() else (1 if Vector2(p.velocity.x, p.velocity.z).length() > 0.3 else 0)
	return [main.joined_world, p.global_position, p.visual.rotation.y, moving]


func _account() -> Array:
	var panel = ProfileUI.get("account")
	return [str(panel.wallet), str(panel.session)] if panel else ["", ""]


func _hello() -> void:
	var me := _me()
	var acct := _account()
	_auth = acct
	_world = me[0] if me else "hub"
	var pos: Vector3 = me[1] if me else Vector3.ZERO
	_send({t = "hello", v = 1, world = _world, p = [pos.x, pos.y, pos.z], y = me[2] if me else 0.0,
			m = me[3] if me else 0, look = Look.worn, wallet = acct[0], session = acct[1], device = _device})


func _send_moves() -> void:
	var main = _main()
	if main != null and str(main.get("joined_world")) != _shown_world:
		_refresh_visible()                # finished loading: the players the welcome listed can be placed now
	var acct := _account()
	if acct != _auth:                     # signed in or out in the Profile menu
		_auth = acct
		_send({t = "auth", wallet = acct[0], session = acct[1], look = Look.worn})
	var me := _me()
	if me.is_empty():
		return
	var pos: Vector3 = me[1]
	if me[0] != _world:
		_world = me[0]
		_send({t = "world", world = _world, p = [pos.x, pos.y, pos.z], y = me[2]})
		_last_sent = [pos, me[2], me[3]]
		_refresh_visible()
		return
	if _last_sent.size() == 3 and pos.distance_to(_last_sent[0]) < 0.01 \
			and absf(angle_difference(me[2], _last_sent[1])) < 0.01 and me[3] == _last_sent[2]:
		return                            # standing still: nothing new to say
	_last_sent = [pos, me[2], me[3]]
	_send({t = "s", p = [snappedf(pos.x, 0.01), snappedf(pos.y, 0.01), snappedf(pos.z, 0.01)],
			y = snappedf(me[2], 0.001), m = me[3]})


# --- what the server sends ---------------------------------------------------------------------

func _on_message(msg: Dictionary) -> void:
	match str(msg.get("t", "")):
		"welcome":
			state = "online"
			my_id = int(msg.id)
			my_name = str(msg.name)
			online = int(msg.online)
			for p in msg.players:
				_add(p)
			OreEvents.on_welcome(msg.get("events", []))
			Chat.load_history(msg.get("chat", []))
			_show()
		"join":
			_add(msg.player)
		"leave":
			_remove(int(msg.id))
			_info.erase(int(msg.id))
		"update":
			var id := int(msg.id)
			if id == my_id:
				if msg.has("name"):
					my_name = str(msg.name)
					_show()
				return
			if not _info.has(id):
				return
			for key in ["name", "guest", "look", "world", "s"]:
				if msg.has(key):
					_info[id][key] = msg[key]
			if msg.has("world"):
				_refresh_visible()
			var r: Node = _remotes.get(id)
			if r:
				if msg.has("look"):
					r.set_look(msg.look)
				if msg.has("name"):
					r.set_player_name(str(msg.name), bool(msg.get("guest", true)))
				if msg.has("s"):
					_push(r, msg.s)
		"states":
			for row in msg.s:
				var r: Node = _remotes.get(int(row[0]))
				if r:
					_push(r, row)
		"online":
			online = int(msg.n)
			_show()
		"full":
			state = "full"
			_show()
		"replaced":                                    # the same player joined from another window
			state = "replaced"
			_show()
		"ore_event":                                   # a voidstone / stellarite vein appeared (OreEvents)
			OreEvents.on_server_event(msg.get("ev", {}))
		"ore_event_end":
			OreEvents.on_server_end(int(msg.get("id", 0)))
		"chat":                                        # global chat (ui/chat.gd), already filtered by the server
			Chat.add_chat(str(msg.get("name", "")), str(msg.get("text", "")))
		"chat_blocked":
			Chat.refused(str(msg.get("why", "")))


func _add(p: Dictionary) -> void:
	var id := int(p.id)
	if id == my_id:
		return
	_info[id] = p
	_refresh_visible()


func _push(r: Node, row: Array) -> void:
	r.push_state(Time.get_ticks_msec() / 1000.0, Vector3(row[1], row[2], row[3]), float(row[4]), int(row[5]))


func _remove(id: int) -> void:
	var r: Node = _remotes.get(id)
	if r:
		r.queue_free()
	_remotes.erase(id)


## Only players in this game's world get an Imp in the scene.
func _refresh_visible() -> void:
	var main = _main()
	if main == null:
		return
	if _holder == null or not is_instance_valid(_holder):
		_holder = Node3D.new()
		_holder.name = "remote_players"
		main.add_child(_holder)
	var world: String = main.joined_world
	_shown_world = world
	for id in _info:
		var p: Dictionary = _info[id]
		var here: bool = str(p.get("world", "")) == world
		if here and not _remotes.has(id):
			var r := RemoteImp.new(id, p.get("look", {}), str(p.get("name", "")))
			_holder.add_child(r)
			r.set_player_name(str(p.get("name", "")), bool(p.get("guest", true)))
			_remotes[id] = r
			if p.get("s") is Array:
				_push(r, p.s)
		elif not here and _remotes.has(id):
			_remove(id)


# --- the little line in the corner ----------------------------------------------------------------

func _make_hud() -> void:
	var layer := CanvasLayer.new()
	layer.layer = 15
	add_child(layer)
	_hud = Label.new()
	_hud.set_anchors_and_offsets_preset(Control.PRESET_BOTTOM_LEFT)   # the debug overlay is top left
	_hud.offset_left = 16
	_hud.offset_top = -34
	_hud.offset_bottom = -12
	_hud.grow_vertical = Control.GROW_DIRECTION_BEGIN
	_hud.add_theme_font_size_override("font_size", 14)
	_hud.add_theme_color_override("font_color", Color(1, 1, 1, 0.9))
	_hud.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.8))
	_hud.add_theme_constant_override("outline_size", 5)
	_hud.mouse_filter = Control.MOUSE_FILTER_IGNORE
	layer.add_child(_hud)
	_notice = Label.new()
	_notice.set_anchors_and_offsets_preset(Control.PRESET_CENTER_TOP)
	_notice.offset_top = 90
	_notice.grow_horizontal = Control.GROW_DIRECTION_BOTH
	_notice.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_notice.add_theme_font_size_override("font_size", 22)
	_notice.add_theme_color_override("font_color", Color(1.0, 0.86, 0.4))
	_notice.add_theme_color_override("font_outline_color", Color(0, 0, 0, 0.9))
	_notice.add_theme_constant_override("outline_size", 8)
	_notice.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_notice.text = "You're playing in another window.
Reload this page to play here instead."
	_notice.visible = false
	layer.add_child(_notice)


func _show() -> void:
	match state:
		"online":
			_hud.text = "Beta · %d online · you are %s" % [online, my_name]
		"connecting", "joining":
			_hud.text = "Beta · connecting…"
		"full":
			_hud.text = "Beta · the server is full, trying again soon"
		"replaced":
			_hud.text = "Beta · playing in another window"
		_:
			_hud.text = "Beta · offline, playing alone" if url != "" else ""
	_notice.visible = state == "replaced"
	status_changed.emit()
