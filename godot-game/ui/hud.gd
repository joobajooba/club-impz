extends CanvasLayer
## The game HUD.
## - Top left, the player card: the Imp's head (drawn from the look it wears), the impz.club username
##   and Imp Coin balance (the account in the Profile menu, ui/profile/account_panel.gd), and the energy
##   bar. Clicking it opens the Profile menu.
## - Under it, the tool bar: five square slots, one per tool kind (pickaxe, sickle, axe, bow, rod),
##   each showing the tool of that kind the player uses. The one in hand is lit; 1 to 5 or a click
##   takes one out, Q switches to the next tier of the same kind.
## - At the bottom, the "F Mine Tin" prompt, a short "+1 Tin ore" line for every pickup (rare drops and
##   new tools are highlighted) and short notices such as "Inventory full".
## Colours from UIKit.

const LINE_TIME := 2.6
const ImpVisual := preload("res://scripts/player/imp_visual.gd")
const AccountPanel := preload("res://ui/profile/account_panel.gd")
const WalletBridge := preload("res://ui/profile/wallet_bridge.gd")
const PORTRAIT := 62                          # px on screen
const PORTRAIT_FOV := 31.0
const PORTRAIT_EYE := Vector3(0, 1.02, -1.6)  # the Imp faces -z
const PORTRAIT_AIM := Vector3(0, 0.95, 0)
const SLOT_SIZE := 50
const SLOT_GAP := 6
const CARD_WIDTH := 5 * SLOT_SIZE + 4 * SLOT_GAP   # the card is as wide as the tool bar

var _card: PanelContainer
var _energy_bar: ProgressBar
var _energy_text: Label
var _name: Label
var _coins: Label
var _portrait: SubViewport
var _slots := {}             # tool kind -> {box, icon, key}
var _tool_name: Label
var _prompt: PanelContainer
var _keys: Array = []        # [key label, text label] x 2
var _loot: VBoxContainer


func _ready() -> void:
	layer = 5
	add_to_group("hud")
	_build()
	_on_energy(Inventory.energy)
	_on_held("")
	_on_account()
	Inventory.energy_changed.connect(_on_energy)
	Inventory.held_changed.connect(_on_held)
	Inventory.changed.connect(_on_held.bind(""))
	Inventory.looted.connect(_on_looted)
	Inventory.message.connect(_on_message)
	Look.changed.connect(_redraw_portrait)
	if ProfileUI.account:
		ProfileUI.account.changed.connect(_on_account)
	Net.status_changed.connect(_on_account)


func _process(_delta: float) -> void:
	var s := Inventory.seconds_to_reset()
	_energy_bar.tooltip_text = "Energy %d / %d. Refills in %dh %dm (00:00 and 12:00 UTC)" % [
		Inventory.energy, GameData.ENERGY_MAX, s / 3600, s / 60 % 60]


## 1 to 5: take out the tool in that slot of the tool bar (Alt+3 to Alt+7 are the debug keys).
func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k == null or not k.pressed or k.echo or k.alt_pressed or k.ctrl_pressed or k.meta_pressed:
		return
	var n := int(k.physical_keycode) - KEY_1
	if n >= 0 and n < GameData.TOOL_KINDS.size():
		Inventory.take_out(GameData.TOOL_KINDS.keys()[n])
		get_viewport().set_input_as_handled()


## A key and its text; a second pair for a second action (T Tame). `key` "" shows the text alone
## (for "Needs a Bronze pickaxe"); `text` "" hides the prompt.
func set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	_prompt.visible = text != ""
	for i in 2:
		var k: String = [key, key2][i]
		var t: String = [text, text2][i]
		_keys[i][0].visible = k != ""
		_keys[i][0].text = k
		_keys[i][1].visible = t != ""
		_keys[i][1].text = t


func _build() -> void:
	var corner := VBoxContainer.new()
	corner.position = Vector2(16, 16)
	corner.add_theme_constant_override("separation", 8)
	corner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(corner)
	corner.add_child(_build_card())
	corner.add_child(_build_toolbar())

	var bottom := VBoxContainer.new()
	bottom.set_anchors_and_offsets_preset(Control.PRESET_CENTER_BOTTOM)
	bottom.grow_horizontal = Control.GROW_DIRECTION_BOTH
	bottom.grow_vertical = Control.GROW_DIRECTION_BEGIN
	bottom.offset_bottom = -40
	bottom.alignment = BoxContainer.ALIGNMENT_END
	bottom.add_theme_constant_override("separation", 8)
	bottom.mouse_filter = Control.MOUSE_FILTER_IGNORE
	add_child(bottom)
	_loot = VBoxContainer.new()
	_loot.alignment = BoxContainer.ALIGNMENT_END
	_loot.add_theme_constant_override("separation", 4)
	_loot.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bottom.add_child(_loot)
	_prompt = PanelContainer.new()
	_prompt.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_prompt.add_theme_stylebox_override("panel", UIKit.panel(UIKit.BG, UIKit.GOLD, 14.0, true))
	_prompt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	bottom.add_child(_prompt)
	var prow := HBoxContainer.new()
	prow.add_theme_constant_override("separation", 10)
	_prompt.add_child(prow)
	for i in 2:
		var key := UIKit.label("", Color.BLACK, 15)
		key.add_theme_stylebox_override("normal", UIKit.key_cap())
		var text := UIKit.label("", Color.WHITE, 16)
		prow.add_child(key)
		prow.add_child(text)
		_keys.append([key, text])
	_prompt.visible = false


# --- the player card --------------------------------------------------------------------

func _build_card() -> Control:
	_card = PanelContainer.new()
	_card.add_theme_stylebox_override("panel", UIKit.panel(UIKit.BG, UIKit.GOLD, 10.0, true))
	_card.custom_minimum_size.x = CARD_WIDTH
	_card.mouse_filter = Control.MOUSE_FILTER_STOP
	_card.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
	_card.gui_input.connect(func(e: InputEvent):
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			ProfileUI.open_menu()
			_card.accept_event())
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 10)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_card.add_child(row)
	row.add_child(_build_portrait())

	var col := VBoxContainer.new()
	col.add_theme_constant_override("separation", 3)
	col.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	col.alignment = BoxContainer.ALIGNMENT_CENTER
	col.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(col)
	_name = UIKit.label("", Color.WHITE, 16)
	_name.add_theme_color_override("font_shadow_color", UIKit.OUTLINE)
	_name.add_theme_constant_override("shadow_offset_x", 1)
	_name.add_theme_constant_override("shadow_offset_y", 1)
	_name.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	_name.clip_text = true
	_name.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(_name)

	var coin_row := HBoxContainer.new()
	coin_row.add_theme_constant_override("separation", 6)
	coin_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(coin_row)
	var coin := UIKit.pixel_icon(UIKit.COIN, UIKit.ENERGY)
	coin.mouse_filter = Control.MOUSE_FILTER_IGNORE
	coin_row.add_child(coin)
	_coins = UIKit.label("", UIKit.RARE, 14)
	_coins.mouse_filter = Control.MOUSE_FILTER_IGNORE
	coin_row.add_child(_coins)

	var energy_row := HBoxContainer.new()
	energy_row.add_theme_constant_override("separation", 6)
	energy_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	col.add_child(energy_row)
	var bolt := UIKit.pixel_icon(UIKit.BOLT, UIKit.ENERGY)
	bolt.mouse_filter = Control.MOUSE_FILTER_IGNORE
	energy_row.add_child(bolt)
	_energy_bar = ProgressBar.new()
	_energy_bar.custom_minimum_size = Vector2(0, 14)
	_energy_bar.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_energy_bar.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_energy_bar.max_value = GameData.ENERGY_MAX
	_energy_bar.show_percentage = false
	_energy_bar.mouse_filter = Control.MOUSE_FILTER_PASS
	_energy_bar.add_theme_stylebox_override("background", UIKit.bar_track())
	_energy_bar.add_theme_stylebox_override("fill", UIKit.bar(UIKit.ENERGY))
	energy_row.add_child(_energy_bar)
	_energy_text = UIKit.label("", Color.WHITE, 12)
	_energy_text.custom_minimum_size.x = 26
	_energy_text.horizontal_alignment = HORIZONTAL_ALIGNMENT_RIGHT
	_energy_text.mouse_filter = Control.MOUSE_FILTER_IGNORE
	energy_row.add_child(_energy_text)
	return _card


## The Imp's head: the player's own Imp, built from the look it wears, in a little 3D scene of its
## own, drawn again only when the look changes (so it costs nothing in between).
func _build_portrait() -> Control:
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIKit.slot(Color("#2a2d36"), UIKit.GOLD.darkened(0.2), 2, 2.0))
	frame.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var view := SubViewportContainer.new()
	view.stretch = true
	view.custom_minimum_size = Vector2(PORTRAIT, PORTRAIT)
	view.mouse_filter = Control.MOUSE_FILTER_IGNORE
	frame.add_child(view)
	_portrait = SubViewport.new()
	_portrait.own_world_3d = true
	_portrait.transparent_bg = true
	_portrait.render_target_update_mode = SubViewport.UPDATE_ONCE
	view.add_child(_portrait)

	var env := Environment.new()
	env.background_mode = Environment.BG_CLEAR_COLOR
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.ambient_light_color = Color(0.85, 0.85, 0.9)
	env.ambient_light_energy = 0.55
	var world_env := WorldEnvironment.new()
	world_env.environment = env
	_portrait.add_child(world_env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, 160, 0)     # from the front, above and to one side
	sun.light_energy = 1.1
	_portrait.add_child(sun)
	var imp := ImpVisual.new()                    # the player's own look: it rebuilds on Look.changed
	imp.rotation.y = deg_to_rad(-18)              # a three-quarter view
	_portrait.add_child(imp)
	var cam := Camera3D.new()
	cam.fov = PORTRAIT_FOV
	_portrait.add_child(cam)
	cam.look_at_from_position(PORTRAIT_EYE, PORTRAIT_AIM)
	_redraw_portrait()
	return frame


func _redraw_portrait() -> void:
	# a couple of frames later, once ImpVisual has rebuilt the model for the new look
	await get_tree().process_frame
	await get_tree().process_frame
	if is_instance_valid(_portrait):
		_portrait.render_target_update_mode = SubViewport.UPDATE_ONCE


## The username and Imp Coins of the impz.club account in the Profile menu.
func _on_account() -> void:
	var acct = ProfileUI.account
	var wallet: String = str(acct.wallet) if acct else ""
	var nick: String = acct.saved_name() if acct else ""
	if nick != "":
		_name.text = nick
	elif wallet != "":
		_name.text = WalletBridge.short_address(wallet)
	elif Net.my_name != "":
		_name.text = Net.my_name
	else:
		_name.text = "Guest"
	var tip := "Your profile: click to open it"
	if wallet == "":
		_coins.text = "Connect a wallet"
		_coins.add_theme_color_override("font_color", UIKit.MUTED)
		tip += "\nConnect your wallet to use your impz.club account and Imp Coins"
	else:
		_coins.text = AccountPanel.format_coins(acct.coin_balance())
		_coins.add_theme_color_override("font_color", UIKit.RARE)
		tip += "\nImp Coins on your impz.club account"
		if acct.unclaimed > 0.0:
			tip += "\n%s more to claim in the Profile menu" % AccountPanel.format_coins(acct.unclaimed)
		if nick == "":
			tip += "\nNo username yet: pick one in the Profile menu"
	_card.tooltip_text = tip


func _on_energy(value: int) -> void:
	_energy_bar.value = value
	_energy_text.text = str(value)


# --- the tool bar --------------------------------------------------------------------------

func _build_toolbar() -> Control:
	var box := VBoxContainer.new()
	box.add_theme_constant_override("separation", 3)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var bar := HBoxContainer.new()
	bar.add_theme_constant_override("separation", SLOT_GAP)
	bar.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(bar)
	var n := 0
	for kind in GameData.TOOL_KINDS:
		n += 1
		var slot := PanelContainer.new()
		slot.custom_minimum_size = Vector2(SLOT_SIZE, SLOT_SIZE)
		slot.mouse_filter = Control.MOUSE_FILTER_STOP
		slot.mouse_default_cursor_shape = Control.CURSOR_POINTING_HAND
		slot.gui_input.connect(func(e: InputEvent):
			if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
				Inventory.take_out(kind)
				slot.accept_event())
		bar.add_child(slot)
		var icon := UIKit.icon(null, SLOT_SIZE - 14)
		icon.mouse_filter = Control.MOUSE_FILTER_IGNORE
		slot.add_child(icon)
		var key := UIKit.label(str(n), UIKit.MUTED, 11)       # the slot's key, in its top-left corner
		key.add_theme_color_override("font_outline_color", UIKit.OUTLINE)
		key.add_theme_constant_override("outline_size", 4)
		key.mouse_filter = Control.MOUSE_FILTER_IGNORE
		var key_box := Control.new()                          # lets the number sit over the icon
		key_box.mouse_filter = Control.MOUSE_FILTER_IGNORE
		key_box.add_child(key)
		key.position = Vector2(1, -2)
		slot.add_child(key_box)
		_slots[kind] = {box = slot, icon = icon, key = key}

	_tool_name = UIKit.label("", Color.WHITE, 13)
	_tool_name.add_theme_color_override("font_outline_color", UIKit.OUTLINE)
	_tool_name.add_theme_constant_override("outline_size", 4)
	_tool_name.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(_tool_name)
	var hint := UIKit.label("1-5 tools  ·  Q next tier  ·  I inventory", UIKit.MUTED, 12)
	hint.add_theme_color_override("font_outline_color", UIKit.OUTLINE)
	hint.add_theme_constant_override("outline_size", 4)
	hint.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(hint)
	return box


func _on_held(_id: String) -> void:
	for kind in _slots:
		var s: Dictionary = _slots[kind]
		var id: String = Inventory.held[kind]
		var lit: bool = kind == Inventory.in_hand
		s.icon.texture = GameData.tool_icon(id)
		s.icon.modulate = Color.WHITE if lit else Color(1, 1, 1, 0.7)
		s.box.add_theme_stylebox_override("panel", UIKit.slot(Color("#3a3526") if lit else UIKit.SLOT,
				UIKit.RARE if lit else UIKit.OUTLINE, 2 if lit else 1, 5.0))
		s.key.add_theme_color_override("font_color", UIKit.RARE if lit else UIKit.MUTED)
		s.box.tooltip_text = "%s  (key %s)" % [GameData.tools[id].label, s.key.text]
	_tool_name.text = GameData.tools[Inventory.held[Inventory.in_hand]].label


# --- pickups and notices ----------------------------------------------------------------------

func _line(content: Control, rare: bool) -> void:
	var line := PanelContainer.new()
	line.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	line.add_theme_stylebox_override("panel", UIKit.panel(UIKit.BG, UIKit.RARE if rare else UIKit.GOLD.darkened(0.25), 12.0, true))
	line.mouse_filter = Control.MOUSE_FILTER_IGNORE
	line.add_child(content)
	_loot.add_child(line)
	var shown := _loot.get_children().filter(func(c): return c.visible)
	for i in shown.size() - 6:   # keep the newest six; each frees itself when its time is up
		shown[i].visible = false
	get_tree().create_timer(LINE_TIME).timeout.connect(line.queue_free)


## `id` is an item id or a tool id (a newly crafted tool).
func _on_looted(id: String, count: int, rare: bool) -> void:
	var row := HBoxContainer.new()
	row.add_theme_constant_override("separation", 8)
	var tex := GameData.item_icon(id)
	if tex:
		row.add_child(UIKit.icon(tex, 28))
	row.add_child(UIKit.label("+%d %s" % [count, GameData.item_label(id)], UIKit.RARE if rare else Color.WHITE, 15))
	_line(row, rare)


func _on_message(text: String) -> void:
	_line(UIKit.label(text, UIKit.MUTED, 15), false)
