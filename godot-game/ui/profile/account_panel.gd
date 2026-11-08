extends VBoxContainer
## The account part of the Profile menu: the player's impz.club account, the same one the website uses.
## An account is a row in the site's Supabase `profiles` table, keyed by wallet, so connecting a wallet
## with Glyph finds it. Username, email and wallet address are shown here; usernames are unique.
##
## Everything goes through the site's own server, https://www.impz.club/api/profile (impz-club repo,
## api/profile.js), never straight to Supabase: the server holds the secret key and checks the rules.
## - Reading the username is public. The email is private: it comes from `?me=1` with a session.
## - A session comes from signing a free message with the wallet (the site's own sign-in, 7 days),
##   and is kept in user://impz_sessions.cfg (the browser's storage in the web build).
## - Saving makes the account if the wallet has none yet, so a new player's account lands in the
##   database at once and shows on the website too.
## - Live: while the menu is open the account is read again every few seconds, so a change made on the
##   website (or a name someone else took) shows up here without reloading.

const WalletBridge := preload("res://ui/profile/wallet_bridge.gd")
const SITE := "https://www.impz.club"
const SESSIONS := "user://impz_sessions.cfg"
const REFRESH := 10.0                       # seconds between reads while the menu is open
const GOOD := Color(0.55, 0.85, 0.5)
const BAD := Color(0.95, 0.5, 0.45)

var ui: Node                 # the ProfileUI that owns this panel, for its _button, _label and wallet
var wallet := ""             # the connected wallet, lower case ("" = none)
var session := ""
var profile = null           # the profiles row, or null when the wallet has no account yet
var email_text := ""         # the email as saved

var status: Label
var fields: GridContainer
var username: LineEdit
var name_note: Label
var email: LineEdit
var wallet_label: Label
var sign_in: Button
var save: Button
var _name_timer: Timer
var _refresh_timer: Timer
var _busy := false
var _note_gap: Control


func _init(owner_ui: Node) -> void:
	ui = owner_ui


func _ready() -> void:
	add_theme_constant_override("separation", 8)
	add_child(UIKit.title("Account", 20))
	status = ui._label("", ui.MUTED, 13)
	add_child(status)

	fields = GridContainer.new()
	fields.columns = 2
	fields.add_theme_constant_override("h_separation", 10)
	fields.add_theme_constant_override("v_separation", 6)
	add_child(fields)
	username = _field("Username", "3 to 24 letters or numbers")
	username.max_length = 24
	username.text_changed.connect(func(_t): _name_timer.start())
	_note_gap = Control.new()
	fields.add_child(_note_gap)
	name_note = ui._label("", ui.MUTED, 12)
	name_note.custom_minimum_size.x = 190     # wraps inside the field's column
	fields.add_child(name_note)
	email = _field("Email", "you@example.com")
	email.max_length = 254
	fields.add_child(_cell("Wallet"))
	wallet_label = _cell("", Color.WHITE)
	wallet_label.mouse_filter = Control.MOUSE_FILTER_PASS   # shows the full address on hover
	fields.add_child(wallet_label)

	sign_in = ui._button("Sign in with your wallet")
	sign_in.tooltip_text = "Sign a free message in Glyph. It sends nothing and costs nothing."
	sign_in.pressed.connect(_on_sign_in)
	add_child(sign_in)
	save = ui._button("Save")
	save.pressed.connect(_on_save)
	add_child(save)

	_name_timer = Timer.new()
	_name_timer.one_shot = true
	_name_timer.wait_time = 0.4
	_name_timer.timeout.connect(_check_name)
	add_child(_name_timer)
	_refresh_timer = Timer.new()
	_refresh_timer.wait_time = REFRESH
	_refresh_timer.timeout.connect(_on_refresh_tick)
	add_child(_refresh_timer)
	_refresh_timer.start()
	_note("")
	_show()


## A one-line label for the grid (ui._label wraps, which squeezes a grid column to nothing).
func _cell(text: String, color: Color = Color(0.75, 0.74, 0.68)) -> Label:
	var l: Label = ui._label(text, color, 14)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


func _field(label: String, hint: String) -> LineEdit:
	fields.add_child(_cell(label))
	var e := LineEdit.new()
	e.placeholder_text = hint
	e.custom_minimum_size = Vector2(190, 32)
	e.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	fields.add_child(e)
	return e


# --- state ------------------------------------------------------------------------

## ProfileUI calls this when a wallet connects, switches account or disconnects ("").
func set_wallet(address: String) -> void:
	address = address.to_lower()
	if address == wallet:
		return
	wallet = address
	session = _stored_session(wallet)
	profile = null
	email_text = ""
	username.text = ""
	email.text = ""
	_note("")
	_show("Loading your impz.club account…" if wallet != "" else "")
	if wallet != "":
		refresh()


## Reads the account again: with the email when signed in, otherwise the public part.
## ProfileUI also calls this when the menu opens.
func refresh() -> void:
	if wallet == "" or _busy:
		return
	var asked := wallet
	var r: Dictionary
	if session != "":
		r = await _request(HTTPClient.METHOD_GET, "?me=1&wallet=" + wallet)
		if asked != wallet:
			return
		if r.code == 401:                     # the session ran out: back to the public part
			_forget_session()
		elif r.ok and r.data is Dictionary and r.data.has("profile"):
			_take(r.data.profile, str(r.data.get("email", "")))
			return
	r = await _request(HTTPClient.METHOD_GET, "?wallet=" + wallet)
	if asked != wallet:
		return
	if r.ok:
		_take(r.data if r.data is Dictionary else null, email_text)
	else:
		_show("Couldn't reach impz.club: %s" % r.error, BAD)


func _take(row, private_email: String) -> void:
	var typed_name := username.text.strip_edges() != _saved_name()
	var typed_email := email.text.strip_edges().to_lower() != email_text
	profile = row
	if not username.has_focus() and not typed_name:     # never overwrite what the player is typing
		username.text = _saved_name()
	if not email.has_focus() and not typed_email:
		email.text = private_email
	email_text = private_email
	var nick := _saved_name()
	ui.profile_button.tooltip_text = "Profile: " + (nick if nick != "" else WalletBridge.short_address(wallet))
	_show()


func _edited() -> bool:
	return username.text.strip_edges() != _saved_name() or email.text.strip_edges().to_lower() != email_text


func _saved_name() -> String:
	return str(profile.get("username", "")) if profile is Dictionary and profile.get("username") != null else ""


func _show(message := "", color: Color = Color(0.75, 0.74, 0.68)) -> void:
	var linked := wallet != ""
	fields.visible = linked
	sign_in.visible = linked and session == ""
	save.visible = linked and session != ""
	username.editable = session != ""
	email.editable = session != ""
	email.placeholder_text = "you@example.com" if session != "" else "Sign in to see it"
	username.placeholder_text = "3 to 24 letters or numbers" if session != "" else "No username yet"
	wallet_label.text = WalletBridge.short_address(wallet)
	wallet_label.tooltip_text = wallet
	for b in [sign_in, save]:
		b.disabled = _busy
	status.add_theme_color_override("font_color", color)
	if message != "":
		status.text = message
	elif not linked:
		status.text = "Connect with Glyph to use your impz.club account, with the same username as on the website."
	elif profile == null:
		status.text = "This wallet has no impz.club account yet. Sign in and pick a username to make one."
	elif session == "":
		status.text = "Your impz.club account. Sign in to change your username or email."
	else:
		status.text = "Signed in to your impz.club account."


# --- actions ------------------------------------------------------------------------

func _on_sign_in() -> void:
	if wallet == "" or _busy:
		return
	_busy = true
	_show("Getting the sign-in message…")
	var asked := wallet
	var r := await _request(HTTPClient.METHOD_GET, "?challenge=1&wallet=" + wallet)
	if not r.ok or not r.data is Dictionary or not r.data.has("message"):
		_busy = false
		_show("Couldn't start signing in: %s" % r.error, BAD)
		return
	var message := str(r.data.message)
	_show("Check Glyph and sign the message. It's free and sends nothing.")
	var signed: Dictionary = await ui.wallet.sign_message(wallet, message)
	if asked != wallet:
		_busy = false
		return
	if not signed.get("ok", false):
		_busy = false
		_show(str(signed.get("error", "The signature didn't go through.")), BAD)
		return
	r = await _request(HTTPClient.METHOD_POST, "", {wallet = wallet, action = "sign-in",
			message = message, signature = str(signed.signature)})
	_busy = false
	if not r.ok or not r.data is Dictionary or str(r.data.get("session", "")) == "":
		_show("Couldn't sign in: %s" % r.error, BAD)
		return
	session = str(r.data.session)
	_store_session(wallet, session)
	_show("Signed in.", GOOD)
	refresh()


func _on_save() -> void:
	if wallet == "" or session == "" or _busy:
		return
	var nick := username.text.strip_edges()
	var mail := email.text.strip_edges().to_lower()
	if nick.length() < 3:
		_show("Pick a username of at least 3 characters.", BAD)
		return
	var body := {wallet = wallet, username = nick}
	if mail != email_text:
		body.email = mail
	if profile == null:
		body.account_age = Time.get_datetime_string_from_system(true) + "Z"   # a new account starts today
	_busy = true
	_show("Saving…")
	var r := await _request(HTTPClient.METHOD_POST, "", body)
	_busy = false
	if r.code == 401:
		_forget_session()
		_show("Your sign-in ran out. Sign in again, then save.", BAD)
		return
	if not r.ok:
		_show(r.error, BAD)
		return
	if r.data is Dictionary:
		profile = r.data
	if body.has("email"):
		email_text = mail
	username.text = _saved_name()
	_note("")
	_show("Saved to your impz.club account.", GOOD)
	refresh()


## Says whether the typed username is free, as the player types.
func _check_name() -> void:
	var nick := username.text.strip_edges()
	if session == "" or nick == "" or nick.to_lower() == _saved_name().to_lower():
		_note("")
		return
	var r := await _request(HTTPClient.METHOD_GET, "?username_free=%s&wallet=%s" % [nick.uri_encode(), wallet])
	if nick != username.text.strip_edges():
		return                                  # they kept typing
	if not r.ok or not r.data is Dictionary or not r.data.has("free"):
		_note("")
	elif r.data.free:
		_note("Available", GOOD)
	else:
		_note(str(r.data.get("error", "Taken: someone already has this name.")), BAD)


## The line under the username field ("Available", "Taken…"); hidden while empty.
func _note(text: String, color := GOOD) -> void:
	name_note.text = text
	name_note.add_theme_color_override("font_color", color)
	name_note.visible = text != ""
	_note_gap.visible = name_note.visible


func _on_refresh_tick() -> void:
	if is_visible_in_tree() and not _busy and not _edited():
		refresh()


# --- sessions ------------------------------------------------------------------------

func _stored_session(address: String) -> String:
	var cfg := ConfigFile.new()
	if address == "" or cfg.load(SESSIONS) != OK:
		return ""
	var token := str(cfg.get_value("sessions", address, ""))
	return token if _expires(token) > Time.get_unix_time_from_system() + 60 else ""


func _store_session(address: String, token: String) -> void:
	var cfg := ConfigFile.new()
	cfg.load(SESSIONS)
	if token != "":
		cfg.set_value("sessions", address, token)
	elif cfg.has_section_key("sessions", address):
		cfg.erase_section_key("sessions", address)
	cfg.save(SESSIONS)


func _forget_session() -> void:
	session = ""
	_store_session(wallet, "")


## The session token is "<base64url JSON {w, exp}>.<signature>"; exp is in milliseconds.
static func _expires(token: String) -> float:
	var body := token.get_slice(".", 0).replace("-", "+").replace("_", "/")
	if body == "":
		return 0.0
	while body.length() % 4 != 0:
		body += "="
	var data = JSON.parse_string(Marshalls.base64_to_utf8(body))
	return float(data.get("exp", 0)) / 1000.0 if data is Dictionary else 0.0


# --- the site's server -----------------------------------------------------------------

## Desktop builds ask impz.club. Web builds ask their own site's /api/profile, because impz.club sends no
## CORS header (web-wallet/scripts/serve.mjs forwards it when testing on localhost).
static func _api() -> String:
	if OS.has_feature("web"):
		return str(JavaScriptBridge.eval("window.location.origin")) + "/api/profile"
	return SITE + "/api/profile"


## {ok, code, data, error}. Sends the session when there is one.
func _request(method: int, query: String, body = null) -> Dictionary:
	var http := HTTPRequest.new()
	http.timeout = 20.0
	add_child(http)
	var headers := ["Accept: application/json", "Content-Type: application/json"]
	if session != "":
		headers.append("x-impz-session: " + session)
	var err := http.request(_api() + query, headers, method, JSON.stringify(body) if body != null else "")
	if err != OK:
		http.queue_free()
		return {ok = false, code = 0, data = null, error = "couldn't send the request (%d)" % err}
	var res: Array = await http.request_completed
	http.queue_free()
	if res[0] != HTTPRequest.RESULT_SUCCESS:
		return {ok = false, code = 0, data = null, error = "no answer from impz.club"}
	var data = JSON.parse_string((res[3] as PackedByteArray).get_string_from_utf8())
	var code: int = res[1]
	if code < 200 or code >= 300:
		var message := str(data.get("error", "")) if data is Dictionary else ""
		return {ok = false, code = code, data = data, error = message if message != "" else "impz.club answered %d" % code}
	return {ok = true, code = code, data = data, error = ""}
