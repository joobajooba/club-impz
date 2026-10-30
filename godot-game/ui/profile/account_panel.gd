extends VBoxContainer
## The account part of the Profile menu: sign up and log in with email (D-041), through Api.
## While the game has no server configured it says so, and that progress stays on this device.
## Built with the Profile menu's own buttons and labels, so it matches.

var ui: Node                 # the ProfileUI that owns this panel, for its _button and _label
var status: Label
var form: VBoxContainer
var email: LineEdit
var password: LineEdit
var username: LineEdit
var log_in: Button
var sign_up: Button
var log_out: Button


func _init(owner_ui: Node) -> void:
	ui = owner_ui


func _ready() -> void:
	add_theme_constant_override("separation", 8)
	add_child(ui._label("Account", Color.WHITE, 18))
	status = ui._label("", ui.MUTED, 13)
	add_child(status)
	form = VBoxContainer.new()
	form.add_theme_constant_override("separation", 6)
	add_child(form)
	email = _field("Email")
	password = _field("Password")
	password.secret = true
	username = _field("Username (sign up only)")
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	form.add_child(row)
	log_in = ui._button("Log in")
	sign_up = ui._button("Sign up")
	for b in [log_in, sign_up]:
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		row.add_child(b)
	log_in.pressed.connect(_on_log_in)
	sign_up.pressed.connect(_on_sign_up)
	log_out = ui._button("Log out")
	log_out.pressed.connect(_on_log_out)
	add_child(log_out)
	Api.session_changed.connect(func(_on): _show())
	_show()


func _field(hint: String) -> LineEdit:
	var e := LineEdit.new()
	e.placeholder_text = hint
	e.custom_minimum_size = Vector2(0, 34)
	form.add_child(e)
	return e


func _show(message := "") -> void:
	if not Api.is_configured():
		status.text = "Offline: accounts arrive when the game is connected to its server. Your progress is saved on this device."
		form.visible = false
		log_out.visible = false
		return
	form.visible = not Api.is_logged_in()
	log_out.visible = Api.is_logged_in()
	status.text = message if message != "" else \
			("Logged in as %s." % Api.email() if Api.is_logged_in() else "Log in, or sign up with your email.")


func _busy(on: bool) -> void:
	for b in [log_in, sign_up, log_out]:
		b.disabled = on


func _on_log_in() -> void:
	if email.text.strip_edges() == "" or password.text == "":
		_show("Enter your email and password.")
		return
	_busy(true)
	var r: Dictionary = await Api.log_in(email.text.strip_edges(), password.text)
	_busy(false)
	password.text = ""
	_show("" if r.ok else "Couldn't log in: %s" % r.error)


func _on_sign_up() -> void:
	var wanted := username.text.strip_edges()
	if email.text.strip_edges() == "" or password.text.length() < 8 or wanted.length() < 3:
		_show("Enter an email, a password of at least 8 characters and a username of at least 3.")
		return
	_busy(true)
	var r: Dictionary = await Api.sign_up(email.text.strip_edges(), password.text, wanted)
	_busy(false)
	password.text = ""
	if not r.ok:
		_show("Couldn't sign up: %s" % r.error)
	elif r.data is Dictionary and r.data.get("confirm", false):
		_show("Check your email and click the link, then log in here.")
	else:
		_show()


func _on_log_out() -> void:
	_busy(true)
	await Api.log_out()
	_busy(false)
