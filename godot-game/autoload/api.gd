extends Node
## Every call to the game's server, as the Api autoload (ACCOUNTS-AND-DATA, section 10): sign up,
## log in, keep the session fresh, and call server functions in the `game` schema.
## The server is Supabase. Its address and public key come from res://config/supabase.cfg; while
## they are empty the game is offline and every call returns {ok = false, error = "offline"}.
## Only the public anon key is ever used here (section 9). The session is kept in user://, which
## is the browser's own storage in the web build, so the player stays logged in.
##
## Calls are coroutines: `var r: Dictionary = await Api.log_in(email, password)`.
## Each returns {ok, code, data, error}.

signal session_changed(logged_in: bool)

const CONFIG := "res://config/supabase.cfg"
const SESSION_FILE := "user://session.json"
const SCHEMA := "game"
const TIMEOUT := 15.0

var url := ""
var anon_key := ""
var session := {}            # {access_token, refresh_token, expires_at, user_id, email}


func _ready() -> void:
	var cfg := ConfigFile.new()
	if cfg.load(CONFIG) == OK:
		url = str(cfg.get_value("supabase", "url", "")).strip_edges().trim_suffix("/")
		anon_key = str(cfg.get_value("supabase", "anon_key", "")).strip_edges()
	if not is_configured():
		return
	var saved = JSON.parse_string(FileAccess.get_file_as_string(SESSION_FILE)) if FileAccess.file_exists(SESSION_FILE) else null
	if saved is Dictionary and saved.get("refresh_token", "") != "":
		session = saved
		refresh()


func is_configured() -> bool:
	return url != "" and anon_key != ""


func is_logged_in() -> bool:
	return is_configured() and session.get("access_token", "") != ""


func email() -> String:
	return session.get("email", "")


# --- accounts (D-041) -------------------------------------------------------------------

## Signs up with email and password. The username travels with the sign-up, and the database
## creates the player row from it (trigger game.on_sign_up), so it works whether or not the
## project asks for email confirmation first. Without a session yet, data.confirm = true.
func sign_up(address: String, password: String, username: String) -> Dictionary:
	var free := await _call(HTTPClient.METHOD_POST, "/rest/v1/rpc/username_free", {p_username = username}, false)
	if not free.ok:
		return free
	if free.data != true:
		return _fail("that username is taken")
	var r := await _call(HTTPClient.METHOD_POST, "/auth/v1/signup",
			{email = address, password = password, data = {username = username}}, false)
	if r.ok and r.data is Dictionary and r.data.has("access_token"):
		_take_session(r.data)
	elif r.ok:
		r.data = {confirm = true}
	return r


func log_in(address: String, password: String) -> Dictionary:
	var r := await _call(HTTPClient.METHOD_POST, "/auth/v1/token?grant_type=password",
			{email = address, password = password}, false)
	if r.ok:
		_take_session(r.data)
	return r


func refresh() -> Dictionary:
	if session.get("refresh_token", "") == "":
		return _fail("not logged in")
	var r := await _call(HTTPClient.METHOD_POST, "/auth/v1/token?grant_type=refresh_token",
			{refresh_token = session.refresh_token}, false)
	if r.ok:
		_take_session(r.data)
	elif r.code == 400 or r.code == 401:   # the refresh token is no longer valid
		_drop_session()
	return r


func log_out() -> void:
	if is_logged_in():
		await _call(HTTPClient.METHOD_POST, "/auth/v1/logout", {})
	_drop_session()


# --- server functions (section 9: every write goes through one) ---------------------------

## Calls a Postgres function in the `game` schema, for example rpc_call("load_state").
func rpc_call(fn: String, args := {}) -> Dictionary:
	if is_configured() and float(session.get("expires_at", 0)) - Time.get_unix_time_from_system() < 60.0:
		await refresh()
	return await _call(HTTPClient.METHOD_POST, "/rest/v1/rpc/" + fn, args)


# --- HTTP ---------------------------------------------------------------------------------

func _call(method: int, path: String, body: Dictionary, auth := true) -> Dictionary:
	if not is_configured():
		return _fail("offline")
	var headers := PackedStringArray([
		"apikey: " + anon_key,
		"Content-Type: application/json",
		"Content-Profile: " + SCHEMA,
		"Accept-Profile: " + SCHEMA,
	])
	var token: String = session.get("access_token", "") if auth else ""
	headers.append("Authorization: Bearer " + (token if token != "" else anon_key))
	var http := HTTPRequest.new()
	http.timeout = TIMEOUT
	add_child(http)
	var err := http.request(url + path, headers, method, JSON.stringify(body))
	if err != OK:
		http.queue_free()
		return _fail("could not reach the server")
	var res: Array = await http.request_completed
	http.queue_free()
	var code: int = res[1]
	var text: String = (res[3] as PackedByteArray).get_string_from_utf8()
	var data = JSON.parse_string(text) if text != "" else null
	if res[0] != HTTPRequest.RESULT_SUCCESS:
		return _fail("could not reach the server")
	if code < 200 or code >= 300:
		return {ok = false, code = code, data = data, error = _message(data, code)}
	return {ok = true, code = code, data = data, error = ""}


## Supabase reports errors under different keys depending on the service.
func _message(data, code: int) -> String:
	if data is Dictionary:
		for k in ["error_description", "msg", "message", "error"]:
			if data.get(k) is String and data[k] != "":
				return data[k]
	return "server error %d" % code


func _fail(error: String) -> Dictionary:
	return {ok = false, code = 0, data = null, error = error}


func _take_session(data: Dictionary) -> void:
	var user: Dictionary = data.get("user", {}) if data.get("user") is Dictionary else {}
	session = {
		access_token = data.get("access_token", ""),
		refresh_token = data.get("refresh_token", ""),
		expires_at = Time.get_unix_time_from_system() + float(data.get("expires_in", 3600)),
		user_id = user.get("id", session.get("user_id", "")),
		email = user.get("email", session.get("email", "")),
	}
	var f := FileAccess.open(SESSION_FILE, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(session))
	session_changed.emit(true)


func _drop_session() -> void:
	session = {}
	if FileAccess.file_exists(SESSION_FILE):
		DirAccess.remove_absolute(ProjectSettings.globalize_path(SESSION_FILE))
	session_changed.emit(false)
