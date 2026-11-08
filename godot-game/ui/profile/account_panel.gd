extends VBoxContainer
## The account part of the Profile menu: the player's impz.club account, the same one the website uses.
## An account is a row in the site's Supabase `profiles` table, keyed by wallet, so connecting a wallet
## with Glyph finds it. It holds:
## - the username: picked here (or on the website), unique across all accounts, any case;
## - the wallet address;
## - when the account was made (`account_age`), set once when the account is first saved;
## - the Imp Coin balance (`imp_coins`): the coins the wallet already has on impz.club. A wallet that
##   earned coins through Chapter 1 Staking and hasn't claimed them yet gets a Claim button, the same
##   claim as the website's Coin Claim page, which adds them to the account.
## The HUD's player card (ui/hud.gd) shows the same account: it listens to `changed`.
##
## Everything goes through the site's own server, https://www.impz.club/api/profile (impz-club repo,
## api/profile.js), never straight to Supabase: the server holds the secret key and checks the rules.
## - Reading an account is public. Changing the username needs a session.
## - A session comes from signing a free message with the wallet (the site's own sign-in, 7 days),
##   and is kept in user://impz_sessions.cfg (the browser's storage in the web build).
## - Saving makes the account if the wallet has none yet, so a new player's account lands in the
##   database at once and shows on the website too.
## - Live: the account is read again every 10 seconds while the menu is open, and every 30 while it's
##   shut (for the HUD), so a change made on the website shows up here without reloading.

signal changed               # the wallet, the account, the sign-in or the coins changed

const WalletBridge := preload("res://ui/profile/wallet_bridge.gd")
const SITE := "https://www.impz.club"
const SESSIONS := "user://impz_sessions.cfg"
const REFRESH := 10.0                       # seconds between reads while the menu is open
const REFRESH_SHUT := 30.0                  # … and while it's shut
const GOOD := Color(0.55, 0.85, 0.5)
const BAD := Color(0.95, 0.5, 0.45)
const MONTHS := ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"]

var ui: Node                 # the ProfileUI that owns this panel, for its _button, _label and wallet
var wallet := ""             # the connected wallet, lower case ("" = none)
var session := ""
var profile = null           # the profiles row, or null when the wallet has no account yet
var unclaimed := 0.0         # staking coins this wallet can still claim (0 once claimed)

var status: Label
var fields: GridContainer
var username: LineEdit
var name_note: Label
var wallet_label: Label
var joined_label: Label
var coins_label: Label
var claim: Button
var sign_in: Button
var save: Button
var _name_timer: Timer
var _busy := false
var _reading := false
var _note_gap: Control
var _since_read := 0.0


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
	fields.add_child(_cell("Username"))
	username = LineEdit.new()
	username.placeholder_text = "3 to 24 letters or numbers"
	username.custom_minimum_size = Vector2(190, 32)
	username.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	username.max_length = 24
	username.text_changed.connect(func(_t): _name_timer.start())
	username.text_submitted.connect(func(_t): _on_save())
	fields.add_child(username)
	_note_gap = Control.new()
	fields.add_child(_note_gap)
	name_note = ui._label("", ui.MUTED, 12)
	name_note.custom_minimum_size.x = 190     # wraps inside the field's column
	fields.add_child(name_note)
	wallet_label = _row("Wallet")
	wallet_label.mouse_filter = Control.MOUSE_FILTER_PASS   # shows the full address on hover
	joined_label = _row("Joined")
	coins_label = _row("Imp Coins")
	coins_label.add_theme_color_override("font_color", UIKit.RARE)

	claim = ui._button("Claim Imp Coins")
	claim.tooltip_text = "Adds the Imp Coins this wallet earned through Chapter 1 Staking to your account."
	claim.pressed.connect(_on_claim)
	add_child(claim)
	sign_in = ui._button("Sign in with your wallet")
	sign_in.tooltip_text = "Sign a free message in Glyph. It sends nothing and costs nothing."
	sign_in.pressed.connect(_on_sign_in)
	add_child(sign_in)
	save = ui._button("Save username")
	save.pressed.connect(_on_save)
	add_child(save)

	_name_timer = Timer.new()
	_name_timer.one_shot = true
	_name_timer.wait_time = 0.4
	_name_timer.timeout.connect(_check_name)
	add_child(_name_timer)
	_note("")
	_show()


func _process(delta: float) -> void:
	_since_read += delta
	if wallet != "" and not _busy and not _edited() \
			and _since_read >= (REFRESH if is_visible_in_tree() else REFRESH_SHUT):
		refresh()


## A one-line label for the grid (ui._label wraps, which squeezes a grid column to nothing).
func _cell(text: String, color: Color = Color(0.75, 0.74, 0.68)) -> Label:
	var l: Label = ui._label(text, color, 14)
	l.autowrap_mode = TextServer.AUTOWRAP_OFF
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	return l


## A name and a value in the grid; returns the value's label.
func _row(name_text: String) -> Label:
	fields.add_child(_cell(name_text))
	var value := _cell("", Color.WHITE)
	value.custom_minimum_size.y = 24
	fields.add_child(value)
	return value


# --- what the HUD reads ---------------------------------------------------------------

## The account's username, "" without one.
func saved_name() -> String:
	if profile is Dictionary and profile.get("username") != null:
		return str(profile.username).strip_edges()
	return ""


## The Imp Coin balance on the account (0 without an account).
func coin_balance() -> float:
	if profile is Dictionary and profile.get("imp_coins") != null:
		return str(profile.imp_coins).to_float()
	return 0.0


## "7 Nov 2026", or "" when the account has no date yet.
func joined() -> String:
	if not profile is Dictionary or profile.get("account_age") == null:
		return ""
	var when := str(profile.account_age)
	if when.length() < 10:
		return ""
	var d := Time.get_datetime_dict_from_datetime_string(when.substr(0, 19), false)
	if int(d.get("year", 0)) < 2000:
		return ""
	return "%d %s %d" % [d.day, MONTHS[clampi(int(d.month) - 1, 0, 11)], d.year]


## 12,345 or 12,345.5
static func format_coins(value: float) -> String:
	var whole := int(floor(absf(value)))
	var digits := str(whole)
	var out := ""
	while digits.length() > 3:
		out = "," + digits.right(3) + out
		digits = digits.left(digits.length() - 3)
	out = ("-" if value < 0.0 else "") + digits + out
	var frac := absf(value) - float(whole)
	if frac >= 0.005:
		out += ("%.2f" % frac).substr(1).trim_suffix("0")
	return out


# --- state ------------------------------------------------------------------------

## ProfileUI calls this when a wallet connects, switches account or disconnects ("").
func set_wallet(address: String) -> void:
	address = address.to_lower()
	if address == wallet:
		return
	wallet = address
	session = _stored_session(wallet)
	profile = null
	unclaimed = 0.0
	username.text = ""
	_note("")
	_show("Loading your impz.club account…" if wallet != "" else "")
	changed.emit()
	if wallet != "":
		refresh()


## Reads the account again, and what the wallet can still claim. ProfileUI also calls this when
## the menu opens.
func refresh() -> void:
	if wallet == "" or _busy or _reading:
		return
	_reading = true
	_since_read = 0.0
	var asked := wallet
	var r := await _request(HTTPClient.METHOD_GET, "?wallet=" + wallet)
	var c := await _request(HTTPClient.METHOD_GET, "?coins=1&wallet=" + wallet)
	_reading = false
	if asked != wallet:
		return
	if c.ok and c.data is Dictionary:
		unclaimed = 0.0 if bool(c.data.get("imp_coin_claimed", false)) else float(c.data.get("portable_imp_coin", 0))
	if r.ok:
		_take(r.data if r.data is Dictionary else null)
	else:
		_show("Couldn't reach impz.club: %s" % r.error, BAD)


func _take(row) -> void:
	var typed := _edited()
	profile = row
	if not username.has_focus() and not typed:          # never overwrite what the player is typing
		username.text = saved_name()
	var nick := saved_name()
	ui.profile_button.tooltip_text = "Profile: " + (nick if nick != "" else WalletBridge.short_address(wallet))
	_show()
	changed.emit()


func _edited() -> bool:
	return username != null and username.text.strip_edges() != saved_name()


func _show(message := "", color: Color = Color(0.75, 0.74, 0.68)) -> void:
	var linked := wallet != ""
	fields.visible = linked
	sign_in.visible = linked and session == ""
	save.visible = linked and session != ""
	claim.visible = linked and unclaimed > 0.0
	claim.text = "Claim %s Imp Coins" % format_coins(unclaimed)
	username.editable = session != ""
	username.placeholder_text = "3 to 24 letters or numbers" if session != "" else "No username yet"
	wallet_label.text = WalletBridge.short_address(wallet)
	wallet_label.tooltip_text = wallet
	var date := joined()
	joined_label.text = date if date != "" else ("Not yet: save a username" if profile == null else "—")
	coins_label.text = format_coins(coin_balance())
	for b in [sign_in, save, claim]:
		b.disabled = _busy
	status.add_theme_color_override("font_color", color)
	if message != "":
		status.text = message
	elif not linked:
		status.text = "Connect with Glyph to use your impz.club account, with the same username and Imp Coins as on the website."
	elif profile == null:
		status.text = "This wallet has no impz.club account yet. Sign in and pick a username to make one."
	elif session == "":
		status.text = "Your impz.club account. Sign in to change your username."
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
	_show("Signed in. Pick a username and save it." if saved_name() == "" else "Signed in.", GOOD)
	changed.emit()
	refresh()


func _on_save() -> void:
	if wallet == "" or session == "" or _busy:
		return
	var nick := username.text.strip_edges()
	if nick.length() < 3:
		_show("Pick a username of at least 3 characters.", BAD)
		return
	var body := {wallet = wallet, username = nick}
	if profile == null or profile.get("account_age") == null:
		body.account_age = Time.get_datetime_string_from_system(true) + "Z"   # the account starts today
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
		if r.code == 409:
			_note("Taken: someone already has this name.", BAD)
		return
	if r.data is Dictionary:
		profile = r.data
	username.text = saved_name()
	_note("")
	_show("Saved to your impz.club account.", GOOD)
	changed.emit()
	refresh()


## Claims the wallet's staking coins onto the account (the website's Coin Claim, same rules).
func _on_claim() -> void:
	if wallet == "" or _busy or unclaimed <= 0.0:
		return
	_busy = true
	_show("Claiming your Imp Coins…")
	var r := await _request(HTTPClient.METHOD_POST, "", {wallet = wallet, action = "claim-imp-coins"})
	_busy = false
	if r.ok and r.data is Dictionary:
		unclaimed = 0.0
		profile = r.data
		_show("Imp Coins claimed: they're on your account.", GOOD)
		changed.emit()
	else:
		if r.code == 409 or r.code == 404:
			unclaimed = 0.0
		_show(r.error, BAD)
	refresh()


## Says whether the typed username is free, as the player types.
func _check_name() -> void:
	var nick := username.text.strip_edges()
	if session == "" or nick == "" or nick.to_lower() == saved_name().to_lower():
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
	changed.emit()


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
## CORS header (the beta server, game-server/server.mjs, forwards it).
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
