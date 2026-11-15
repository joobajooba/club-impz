extends CanvasLayer
## Profile button (a person icon) in the top-right corner, left of the Settings gear. Opens a menu to
## connect a wallet with Glyph and use the impz.club account of that wallet (account_panel.gd): the same
## username, email and wallet as on the website.
## Loaded as an autoload (ProfileUI in project.godot), so it sits on top of every scene.
## The wallet connection itself isn't kept: after reloading the page, connect again (the sign-in is kept).

const WalletBridge := preload("res://ui/profile/wallet_bridge.gd")
const AccountPanel := preload("res://ui/profile/account_panel.gd")

const BG := Color(0.11, 0.12, 0.15, 0.94)
const SLOT := Color(0.18, 0.19, 0.23, 0.95)
const BORDER := Color(0.85, 0.82, 0.7, 0.6)
const MUTED := Color(0.75, 0.74, 0.68)

var wallet: WalletBridge
var profile_button: Button
var menu: PanelContainer
var status_label: Label
var connect_button: Button
var wallet_list: VBoxContainer
var connected_box: VBoxContainer
var address_label: Label
var chain_label: Label
var address := ""
var account: AccountPanel


func _ready() -> void:
	layer = 20
	wallet = WalletBridge.new()
	add_child(wallet)
	wallet.wallets_listed.connect(_on_wallets_listed)
	wallet.connected.connect(_on_connected)
	wallet.connect_failed.connect(_on_connect_failed)
	wallet.account_changed.connect(_on_account_changed)
	wallet.chain_changed.connect(_on_chain_changed)
	_build()
	_show_disconnected()


func _unhandled_input(event: InputEvent) -> void:
	if menu.visible and event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		menu.visible = false
		get_viewport().set_input_as_handled()


# --- UI -----------------------------------------------------------------------

func _button(text: String) -> Button:
	var b := Button.new()
	b.text = text
	b.custom_minimum_size = Vector2(0, 40)
	for state in ["normal", "hover", "pressed", "disabled"]:   # pixel-art boxes from UIKit (D-015)
		b.add_theme_stylebox_override(state, UIKit.button_box(state, SLOT))
	b.add_theme_stylebox_override("focus", StyleBoxEmpty.new())
	return b


func _label(text := "", color := Color.WHITE, size := 15) -> Label:
	var l := Label.new()
	l.text = text
	l.add_theme_color_override("font_color", color)
	l.add_theme_font_size_override("font_size", size)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	return l


func _build() -> void:
	# a person icon on the black HUD button; the Settings gear sits to its right (ui/settings_menu.gd)
	var side := UIKit.ICON_BUTTON
	profile_button = UIKit.icon_button(UIKit.PERSON, "Profile")
	profile_button.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	profile_button.offset_left = -16 - side - 8 - side
	profile_button.offset_top = 16
	profile_button.offset_right = -16 - side - 8
	profile_button.offset_bottom = 16 + side
	profile_button.pressed.connect(_toggle_menu)
	add_child(profile_button)

	menu = PanelContainer.new()
	menu.add_theme_stylebox_override("panel", UIKit.panel(BG))
	menu.set_anchors_and_offsets_preset(Control.PRESET_TOP_RIGHT)
	menu.offset_left = -336
	menu.offset_top = 16 + UIKit.ICON_BUTTON + 8
	menu.offset_right = -16
	menu.visible = false
	add_child(menu)

	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 12)
	menu.add_child(box)
	box.add_child(UIKit.title("Profile", 24))
	box.add_child(UIKit.divider())

	status_label = _label("", MUTED, 14)
	box.add_child(status_label)

	connect_button = _button("Connect wallet")
	connect_button.pressed.connect(_on_connect_pressed)
	box.add_child(connect_button)

	wallet_list = VBoxContainer.new()
	wallet_list.add_theme_constant_override("separation", 8)
	box.add_child(wallet_list)

	connected_box = VBoxContainer.new()
	connected_box.add_theme_constant_override("separation", 8)
	box.add_child(connected_box)
	address_label = _label("", Color.WHITE, 18)
	connected_box.add_child(address_label)
	address_label.visible = false            # the Account part below shows the wallet
	chain_label = _label("", MUTED, 14)
	connected_box.add_child(chain_label)
	var copy := _button("Copy address")
	copy.pressed.connect(_copy_address)
	connected_box.add_child(copy)
	var disconnect_button := _button("Disconnect")
	disconnect_button.pressed.connect(_on_disconnect_pressed)
	connected_box.add_child(disconnect_button)

	box.add_child(HSeparator.new())
	account = AccountPanel.new(self)
	box.add_child(account)


## Opens the menu (the HUD's player card).
func open_menu() -> void:
	if not menu.visible:
		_toggle_menu()


func _toggle_menu() -> void:
	menu.visible = not menu.visible
	if menu.visible:
		account.refresh()                    # pick up changes made on the website


func _clear_wallet_list() -> void:
	for child in wallet_list.get_children():
		child.queue_free()


func _show_disconnected(message := "No wallet connected.") -> void:
	address = ""
	profile_button.tooltip_text = "Profile"
	if account:
		account.set_wallet("")
	status_label.text = message
	connect_button.visible = true
	connect_button.disabled = false
	connected_box.visible = false
	_clear_wallet_list()


# --- Wallet flow ----------------------------------------------------------------

func _on_connect_pressed() -> void:
	if not WalletBridge.is_supported():
		status_label.text = "Glyph connects in the browser version of the game. Run `npm start` in web-wallet, then open http://localhost:8060."
		return
	connect_button.disabled = true
	status_label.text = "Looking for wallets…"
	wallet.list_wallets()


func _on_wallets_listed(wallets: Array) -> void:
	connect_button.disabled = false
	_clear_wallet_list()
	if wallets.is_empty():
		status_label.text = "No wallet found. Install MetaMask or Rabby in this browser, then reload the page."
		return
	if wallets.size() == 1:
		_start_connect(wallets[0])
		return
	status_label.text = "Choose a wallet:"
	connect_button.visible = false
	for w in wallets:
		var b := _button(str(w.name))
		b.pressed.connect(_start_connect.bind(w))
		wallet_list.add_child(b)


func _start_connect(w: Dictionary) -> void:
	_clear_wallet_list()
	connect_button.visible = true
	connect_button.disabled = true
	status_label.text = "Check %s to approve the connection…" % str(w.name)
	wallet.connect_wallet(str(w.id))


func _on_connected(new_address: String, chain_id: int) -> void:
	address = new_address
	profile_button.tooltip_text = "Profile: " + WalletBridge.short_address(address)
	status_label.text = "Wallet connected."
	address_label.text = WalletBridge.short_address(address)
	address_label.tooltip_text = address
	chain_label.text = "Network: %s" % WalletBridge.chain_name(chain_id)
	connect_button.visible = false
	connected_box.visible = true
	account.set_wallet(address)


func _on_connect_failed(message: String) -> void:
	_show_disconnected(message)


func _on_account_changed(new_address: String) -> void:
	if new_address == "":
		_show_disconnected("Your wallet disconnected.")
	elif address != "":
		address = new_address
		profile_button.tooltip_text = "Profile: " + WalletBridge.short_address(address)
		address_label.text = WalletBridge.short_address(address)
		address_label.tooltip_text = address
		status_label.text = "Switched to another account."
		account.set_wallet(address)


func _on_chain_changed(chain_id: int) -> void:
	if address != "":
		chain_label.text = "Network: %s" % WalletBridge.chain_name(chain_id)


func _copy_address() -> void:
	DisplayServer.clipboard_set(address)
	status_label.text = "Address copied."


func _on_disconnect_pressed() -> void:
	wallet.disconnect_wallet()
	_show_disconnected("Wallet disconnected.")
