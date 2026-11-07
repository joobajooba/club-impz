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

signal status_changed            # connecting / online / offline, or the player count changed

const CONFIG := "res://config/server.cfg"
const SEND_EVERY := 0.1
const RemoteImp := preload("res://scripts/player/remote_imp.gd")

var url := ""
var state := "offline"           # offline | connecting | online | full
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
var _hud: Label


func _ready() -> void:
	url = _pick_url()
	_make_hud()
	Look.changed.connect(func(): _send({t = "look", look = Look.worn}))
	if url != "":
		_connect()
	_show()


func _pick_url() -> String:
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--server="):
			return a.trim_prefix("--server=")
	if OS.has_feature("web"):
		var origin := str(JavaScriptBridge.eval("window.location.origin"))
		return origin.replace("https://", "wss://").replace("http://", "ws://") + "/ws"
	var cfg := ConfigFile.new()
	return str(cfg.get_value("server", "url", "")).strip_edges() if cfg.load(CONFIG) == OK else ""


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
	_ws = null
	my_id = 0
	state = "full" if was_full else "offline"
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
		if url != "":
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


func _send(msg: Dictionary) -> void:
	if _ws and _ws.get_ready_state() == WebSocketPeer.STATE_OPEN and (state == "online" or msg.t == "hello"):
		_ws.send_text(JSON.stringify(msg))


# --- what this game sends ----------------------------------------------------------------------

func _main() -> Node:
	return get_tree().get_first_node_in_group("game_main")


## [world, position, yaw, moving] of the local Imp, or [] outside the game scene.
func _me() -> Array:
	var main = _main()
	if main == null or main.get("player") == null or main.current_world_name == "":
		return []
	var p = main.player
	var moving: int = 2 if not p.is_on_floor() else (1 if Vector2(p.velocity.x, p.velocity.z).length() > 0.3 else 0)
	return [main.current_world_name, p.global_position, p.visual.rotation.y, moving]


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
			m = me[3] if me else 0, look = Look.worn, wallet = acct[0], session = acct[1]})


func _send_moves() -> void:
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
	var world: String = main.current_world_name
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


func _show() -> void:
	match state:
		"online":
			_hud.text = "Beta · %d online · you are %s" % [online, my_name]
		"connecting", "joining":
			_hud.text = "Beta · connecting…"
		"full":
			_hud.text = "Beta · the server is full, trying again soon"
		_:
			_hud.text = "Beta · offline, playing alone" if url != "" else ""
	status_changed.emit()
