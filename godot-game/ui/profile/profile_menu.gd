extends CanvasLayer
## The player profile (game_direction.md section 9, game_menus.md sections 1, 3 "Profile", 3.5, 4 and 5), as the
## ProfileMenu autoload. P opens and closes it, Esc closes it, and so does clicking the HUD's player card. Layout from
## J00BA's mockup (docs/images/player_profile_menu/mockup.png); the look is the shared UI kit (section 5.2).
##
## Left panel (Decided, section 9): the username, the prestige icon (half size, J00BA) and player level, the Imp as it
## is worn (a turning 3D view like the customizer's: drag to turn, wheel to zoom), and the equipped emblem and title.
## Clicking the emblem or the title opens its picker where the tabs' content goes: slots like the trophies (titles two
## to a row), None first; locked ones say which challenge gives them. Picking equips it at once (Save.profile).
## Tabs (Decided, section 9), clicked (no number keys, J00BA): Stats (the five skills, each with an XP bar and a
## Skill Tree button that opens that skill's tree in a popup, J00BA 2026-11-14), Trophies, Collection (the pictures of the Impz in the linked wallet, J00BA) and Information.
##
## Real today: the username, joined date, Imp Coins and wallet (AccountPanel), the worn look and the traits the player
## can use (Look), the Impz in the wallet (impz.club), the skill names (GameData.SKILLS). Everything else (player level,
## prestige, skill XP and trees, trophies, titles, emblems, prestige badges) is not built: debug builds show the TEST
## values of data/profile_test.json with a "TEST data" tag in the title bar, release builds show "Not built yet".
##
## Everything is drawn from one profile dictionary and an is_self flag (show_profile), so the same window can show
## another player's card (Proposed, game_menus.md section 3). Getting their profile from the server is not built:
## see request_player_profile().
## Collection pictures: each Imp's metadata (impz.club/api/metadata/<id>, the same the marketplaces read) gives its name
## (IMPLINGZ #12) and its ipfs:// image, loaded through a public IPFS gateway (or the game's own copy of the picture,
## when it has one) and kept for the session.

const AccountPanel := preload("res://ui/profile/account_panel.gd")
const TEST_FILE := "res://data/profile_test.json"
const TABS := [
	{key = "stats", label = "Stats"}, {key = "trophies", label = "Trophies"},
	{key = "collection", label = "Collection"}, {key = "information", label = "Information"},
]
const SKILL_ORDER := ["mining", "lumbering", "fishing", "foraging", "hunting"]   # the mockup's order
const PREVIEW_SIZE := Vector2i(300, 330)
const TARGET := Vector3(0, 52, 0)
const MIN_TAP := 44                     # every button and slot at least 44 screen pixels (section 4.5)
const NOT_BUILT := "Not built yet"
const METADATA := "https://www.impz.club/api/metadata/"
const IPFS_GATEWAY := "https://gateway.pinata.cloud/ipfs/"
const LOCAL_PICTURES := "res://assets/sprites/implingz_generations/%d.png"
const LOADERS := 4
const IMP_PICTURE := 128                # the 640 px NFT picture at 1/5: each of its pixels stays whole
const LOCK := ["..kkkk..", ".k....k.", ".k....k.", "kkkkkkkk", "kYyyyyok", "kyyooyok", "kyyyyyok", "kkkkkkkk"]
const TREE_ROW := 5                     # skill tree popup: five nodes to a row, read left to right (J00BA, 2026-11-14)
const TREE_NODE := Vector2(150, 56)     # skill tree node size (px)
const ARROW_SMALL := ["k....", "kk...", "kYk..", "kyyk.", "kok..", "kk...", "k...."]
const ARROW := ["....k...", "....kk..", "kkkkkYk.", "kYYYYYyk", "kyyyyyok", "kkkkkok.", "....kk..", "....k..."]

var tab := "stats"                      # remembered between openings
var skill := "mining"
var _tree_skill := ""                   # the skill whose tree popup is open, "" = none
var _tree_layer: Control
var _tree_detail := ""
var profile := {}                       # what the window shows (see _self_profile)
var is_self := true
var spin := true

var _test := {}                         # data/profile_test.json, debug builds only
var _picker := ""                       # "", "title" or "emblem"
var _detail := {}                       # per tab: the text under the line (selected node / trophy)
var _panel: PanelContainer
var _test_tag: Label
var _name_label: Label
var _level_box: HBoxContainer
var _emblem_button: Button
var _title_button: Button
var _customize_button: Button
var _rotate_button: Button
var _stopped_label: Label
var _tab_buttons := {}
var _tabs_row: HBoxContainer
var _well: PanelContainer
var _content: VBoxContainer
var _holder: Node3D
var _camera: Camera3D
var _yaw := 0.4
var _pitch := 0.1
var _dist := 250.0
var _dragging := false
var _imp_pictures := {}                 # Imp id -> Texture2D, or "loading" / "failed"
var _imp_names := {}                    # Imp id -> "IMPLINGZ #12" from its metadata
var _imp_queue: Array = []              # Imp ids waiting for their metadata and picture
var _imp_loading := 0                   # Imps loading right now (at most LOADERS)


func _ready() -> void:
	layer = 16
	add_to_group("modal")
	if OS.is_debug_build() and FileAccess.file_exists(TEST_FILE):
		var data = JSON.parse_string(FileAccess.get_file_as_string(TEST_FILE))
		_test = data if data is Dictionary else {}
	_build()
	visible = false
	Look.changed.connect(_on_look_changed)
	Look.wallet_changed.connect(func(): _refresh_if_open())
	Save.profile_changed.connect(func(): _refresh_if_open())
	if ProfileUI.account:
		ProfileUI.account.changed.connect(func(): _refresh_if_open())


# --- opening and closing (section 4.1) ----------------------------------------------------

## The player's own profile.
func open() -> void:
	Look.sync_wallet()
	show_profile(_self_profile(), true)


## Show a profile dictionary (see _self_profile for the keys). is_self false hides every edit control.
func show_profile(p: Dictionary, self_view: bool) -> void:
	_close_other_menus()
	profile = p
	is_self = self_view
	_picker = ""
	visible = true
	_refresh()
	_rebuild_preview()
	# open with a quick 95% -> 100% scale and fade (section 5.2, Motion)
	_panel.pivot_offset = _panel.size / 2.0
	_panel.scale = Vector2(0.95, 0.95)
	_panel.modulate.a = 0.0
	var tw := create_tween().set_parallel()
	tw.tween_property(_panel, "scale", Vector2.ONE, 0.1)
	tw.tween_property(_panel, "modulate:a", 1.0, 0.1)


## Another player's card (Proposed, game_menus.md section 3). NOT BUILT: the server has no message for a player's
## profile yet. It needs one (for example {t: "profile", id}) answering with the dictionary _self_profile() builds,
## then show_profile(answer, false). Until then this only says so.
func request_player_profile(player_id: int) -> void:
	push_warning("ProfileMenu.request_player_profile(%d): other players' profiles are not built yet" % player_id)


func close() -> void:
	_close_tree()
	visible = false
	_dragging = false
	_picker = ""
	_clear_preview()


func toggle() -> void:
	if visible:
		close()
	elif _can_open():
		open()


## Opening a menu over another replaces it (section 4.1).
func _close_other_menus() -> void:
	for n in get_tree().get_nodes_in_group("modal"):
		if n != self and n.visible:
			if n.has_method("close"):
				n.close()
			else:
				n.visible = false


func _can_open() -> bool:
	var main := get_tree().get_first_node_in_group("game_main")
	if main and (main.get("free_cam") != null or main.get("busy")):
		return false
	return not (Chat.is_typing() if Chat else false)


func _input(event: InputEvent) -> void:
	# _input, not _unhandled_input: while open, P and Esc belong to this menu
	var k := event as InputEventKey
	if not visible or k == null or not k.pressed or k.echo or k.alt_pressed or k.ctrl_pressed:
		return
	if k.keycode == KEY_ESCAPE:
		if _tree_skill != "":
			_close_tree()
		elif _picker != "":
			_close_picker()
		else:
			close()
		get_viewport().set_input_as_handled()
	elif k.is_action("profile"):
		close()
		get_viewport().set_input_as_handled()


func _unhandled_input(event: InputEvent) -> void:
	var k := event as InputEventKey
	if k and k.pressed and not k.echo and not visible and k.is_action("profile") and _can_open():
		open()
		get_viewport().set_input_as_handled()


func _toggle_spin() -> void:
	spin = not spin
	_stopped_label.visible = not spin


func _process(delta: float) -> void:
	if not visible or _camera == null:
		return
	if spin and not _dragging:
		_yaw += delta * 0.5
	var dir := Vector3(sin(_yaw) * cos(_pitch), sin(_pitch), cos(_yaw) * cos(_pitch))
	_camera.position = TARGET + dir * _dist
	_camera.look_at(TARGET)


# --- the profile data ------------------------------------------------------------------------

## The player's own profile. Keys: name, level and prestige (-1 = not built), look, title, emblem, skills
## ({skill: {level, xp, need}}, empty = not built), earned (trophy ids), joined, coins, wallet, imps, tiers.
func _self_profile() -> Dictionary:
	var acct = ProfileUI.account
	var player: Dictionary = _test.get("player", {})
	return {
		name = acct.saved_name() if acct else "",
		level = int(player.get("level", -1)), prestige = int(player.get("prestige", -1)),
		look = Look.shown(),
		title = Save.profile.title, emblem = Save.profile.emblem,
		skills = _test.get("skills", {}),
		earned = _test.get("trophies", []).filter(func(t): return t.get("earned", false)).map(func(t): return t.id),
		joined = acct.joined() if acct else "",
		coins = acct.coin_balance() if acct and acct.wallet != "" else -1.0,
		wallet = Look.wallet, imps = Look.imps, tiers = Look.tiers,
	}


func _testing() -> bool:
	return not _test.is_empty()


func _titles() -> Array:
	return _test.get("titles", [])


func _emblems() -> Array:
	return _test.get("emblems", [])


func _trophies() -> Array:
	return _test.get("trophies", [])


## The trophy that gives a title or emblem ({} if none).
func _trophy_for(kind: String, id: String) -> Dictionary:
	for t in _trophies():
		if t.get(kind, "") == id:
			return t
	return {}


func _unlocked(kind: String, id: String) -> bool:
	var t := _trophy_for(kind, id)
	return not t.is_empty() and t.id in profile.get("earned", [])


func _find(list: Array, id: String) -> Dictionary:
	for e in list:
		if e.id == id:
			return e
	return {}


## The name of an equipped title, "" when none or unknown (the HUD's player card uses this too).
func title_name(id: String) -> String:
	return str(_find(_titles(), id).get("name", "")) if id != "" else ""


func _equip(kind: String, id: String) -> void:
	if not is_self or (id != "" and not _unlocked(kind, id)):
		return
	Save.equip(kind, id)
	profile[kind] = id
	_close_picker()


# --- refresh ---------------------------------------------------------------------------------

func _refresh_if_open() -> void:
	if visible and is_self:
		profile = _self_profile()
		_refresh()


func _on_look_changed() -> void:
	if visible and is_self:
		profile.look = Look.shown()
		_rebuild_preview()
		_refresh()


func _set_tab(key: String) -> void:
	tab = key
	_picker = ""
	_refresh()


func _close_picker() -> void:
	_picker = ""
	_refresh()


func _refresh() -> void:
	if not visible:
		return
	_test_tag.visible = _testing()
	_refresh_left()
	for key in _tab_buttons:
		_style_tab(_tab_buttons[key], key == tab and _picker == "")
	for c in _content.get_children():
		_content.remove_child(c)
		c.queue_free()
	if _picker != "":
		_render_picker(_picker)
		return
	match tab:
		"stats": _render_stats()
		"trophies": _render_trophies()
		"collection": _render_collection()
		"information": _render_information()


func _refresh_left() -> void:
	var nick: String = profile.get("name", "")
	_name_label.text = nick if nick != "" else "No username yet"
	_name_label.add_theme_color_override("font_color", Color.WHITE if nick != "" else UIKit.MUTED)
	for c in _level_box.get_children():
		_level_box.remove_child(c)
		c.queue_free()
	var prestige: int = profile.get("prestige", -1)
	var level: int = profile.get("level", -1)
	if level < 0:
		_level_box.add_child(UIKit.label(NOT_BUILT, UIKit.MUTED, 12))
		_level_box.tooltip_text = "Player level and prestige: not built yet"
	else:
		var tex := load("res://sprites/items/prestige_%d.png" % clampi(prestige, 0, 5)) as Texture2D
		if tex:
			_level_box.add_child(UIKit.icon(tex, 24))          # half size (J00BA, 2026-11-08)
		_level_box.add_child(UIKit.label(str(level), UIKit.RARE, 18))
		_level_box.tooltip_text = "Player level %d · prestige %d" % [level, prestige]
	for c in _level_box.get_children():
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	# emblem and title boxes
	_fill_box(_emblem_button, _emblem_art(profile.get("emblem", ""), 48), "No emblem")
	var tname := title_name(profile.get("title", ""))
	var tl := UIKit.label(tname, UIKit.RARE, 17) if tname != "" else null
	_fill_box(_title_button, tl, "No title")
	_emblem_button.disabled = not is_self
	_title_button.disabled = not is_self
	_emblem_button.tooltip_text = "Pick an emblem" if is_self else ""
	_title_button.tooltip_text = "Pick a title" if is_self else ""
	_customize_button.visible = is_self


func _fill_box(b: Button, art: Control, empty_text: String) -> void:
	for c in b.get_children():
		b.remove_child(c)
		c.queue_free()
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(center)
	var shown: Control = art if art else UIKit.label(empty_text, UIKit.MUTED, 13)
	shown.mouse_filter = Control.MOUSE_FILTER_IGNORE
	center.add_child(shown)


## TEST emblem placeholder: a 48x48 slot with the first letter of its name (real art comes from J00BA).
func _emblem_art(id: String, size: int) -> Control:
	var e := _find(_emblems(), id)
	if e.is_empty():
		return null
	var box := PanelContainer.new()
	box.custom_minimum_size = Vector2(size, size)
	box.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.GOLD, 1, 2.0))
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	var l := UIKit.label(str(e.name).trim_prefix("TEST ").left(1), UIKit.RARE, 22)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(l)
	return box


# --- Stats -----------------------------------------------------------------------------------

func _render_stats() -> void:
	# the five skills, each with its XP bar and a button opening its skill tree in a popup (J00BA, 2026-11-14:
	# the tree no longer sits beside the list)
	var list := VBoxContainer.new()
	list.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	list.add_theme_constant_override("separation", 8)
	_content.add_child(list)
	list.add_child(UIKit.label("Skill Levels", Color.WHITE, 18))
	var skills: Dictionary = profile.get("skills", {})
	for key in SKILL_ORDER:
		var line := HBoxContainer.new()
		line.add_theme_constant_override("separation", 10)
		list.add_child(line)
		var row := _skill_row(key, skills.get(key, {}))
		row.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		line.add_child(row)
		var tree := UIKit.button("Skill Tree", true, _open_tree.bind(key))
		tree.custom_minimum_size = Vector2(130, MIN_TAP)
		tree.size_flags_vertical = Control.SIZE_SHRINK_CENTER
		line.add_child(tree)


# --- the skill tree popup --------------------------------------------------------------------

## The nodes of a skill's tree: one every 5 levels up to 100. Each is {level, name, buff, recipe (tool or {})}.
## The buffs are TEST (skill_trees.md isn't written: data/profile_test.json in debug builds); the recipe unlocks
## are real (GameData.recipe_at).
func _tree_nodes(key: String) -> Array:
	var test: Array = _test.get("skill_trees", {}).get(key, [])
	var out := []
	for level in range(GameData.RECIPE_EVERY, GameData.SKILL_TREE_MAX + 1, GameData.RECIPE_EVERY):
		var n := {level = level, name = "", buff = "", recipe = GameData.recipe_at(key, level)}
		for t in test:
			if int(t.level) == level:
				n.name = t.name
				n.buff = t.buff
		if n.name == "":
			n.name = "TEST Level %d" % level if _testing() else "Level %d" % level
			n.buff = "TEST: +2% speed" if _testing() else "Buff: " + NOT_BUILT
		out.append(n)
	return out


func _open_tree(key: String) -> void:
	_tree_skill = key
	_tree_detail = ""
	_render_tree()


func _close_tree() -> void:
	_tree_skill = ""
	if is_instance_valid(_tree_layer):
		_tree_layer.queue_free()
	_tree_layer = null


## The popup over the Profile window: the skill's tree read left to right like text, five nodes to a row, with an
## arrow between nodes; a node every 5 levels. Locked nodes are greyed with a lock. Nodes that unlock a recipe
## show the tool. Clicking a node shows what it gives under the tree.
func _render_tree() -> void:
	if is_instance_valid(_tree_layer):
		_tree_layer.queue_free()
	var key := _tree_skill
	var label: String = GameData.SKILLS[key].label
	var s: Dictionary = profile.get("skills", {}).get(key, {})
	var level := int(s.get("level", -1)) if not s.is_empty() else -1
	_tree_layer = Control.new()
	_tree_layer.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(_tree_layer)
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.45)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	dim.gui_input.connect(func(e: InputEvent):   # a click outside the popup closes it
		if e is InputEventMouseButton and e.pressed and e.button_index == MOUSE_BUTTON_LEFT:
			_close_tree())
	_tree_layer.add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_tree_layer.add_child(center)
	var panel := PanelContainer.new()
	panel.add_theme_stylebox_override("panel", UIKit.panel())
	center.add_child(panel)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 10)
	panel.add_child(vbox)
	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	vbox.add_child(head)
	head.add_child(UIKit.title(label + " Skill Tree", 24))
	var lv := UIKit.label(("Level %d" % level) if level >= 0 else "Level: " + NOT_BUILT, UIKit.RARE if level >= 0 else UIKit.MUTED, 16)
	lv.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	head.add_child(lv)
	if _testing():
		head.add_child(UIKit.label("TEST data", UIKit.SHORT, 13))
	head.add_child(UIKit.spacer())
	var close_button := UIKit.button("Close", true, _close_tree)
	close_button.custom_minimum_size = Vector2(90, MIN_TAP)
	head.add_child(close_button)
	vbox.add_child(UIKit.divider())
	var nodes := _tree_nodes(key)
	var rows := VBoxContainer.new()
	rows.add_theme_constant_override("separation", 10)
	vbox.add_child(rows)
	var chain: HBoxContainer
	for i in nodes.size():
		var n: Dictionary = nodes[i]
		if i % TREE_ROW == 0:
			chain = HBoxContainer.new()
			chain.add_theme_constant_override("separation", 8)
			rows.add_child(chain)
			var span := UIKit.label("Lv %d-%d" % [int(n.level), int(n.level) + GameData.RECIPE_EVERY * (TREE_ROW - 1)], UIKit.MUTED, 12)
			span.custom_minimum_size.x = 64
			span.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			chain.add_child(span)
		else:
			var arrow := UIKit.pixel_icon(ARROW_SMALL, Color.WHITE)
			arrow.size_flags_vertical = Control.SIZE_SHRINK_CENTER
			chain.add_child(arrow)
		chain.add_child(_tree_node(key, n, level >= 0 and level >= int(n.level)))
	vbox.add_child(UIKit.divider())
	var info := UIKit.label(_tree_detail if _tree_detail != "" else "Click a node to see what it gives. Read left to right: a new node every %d levels." % GameData.RECIPE_EVERY,
		Color.WHITE if _tree_detail != "" else UIKit.MUTED, 14)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.custom_minimum_size = Vector2(0, 44)
	vbox.add_child(info)


func _tree_node(key: String, n: Dictionary, open: bool) -> Button:
	var recipe: Dictionary = n.recipe
	var lines := [n.name, n.buff]
	if not recipe.is_empty():
		lines.append("Unlocks the %s recipe" % recipe.label)
	lines.append("Unlocked" if open else "Unlocks at %s %d" % [GameData.SKILLS[key].label, int(n.level)])
	var tip := "\n".join(lines)
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = TREE_NODE
	b.tooltip_text = tip
	for state in ["normal", "hover", "pressed", "disabled"]:
		var fill := UIKit.SLOT.lightened(0.08) if state == "hover" else UIKit.SLOT
		var edge := UIKit.GOLD if open and not recipe.is_empty() else UIKit.OUTLINE
		b.add_theme_stylebox_override(state, UIKit.slot(fill, edge, 2 if edge == UIKit.GOLD else 1, 4.0))
	b.pressed.connect(func(): _tree_detail = "  ·  ".join(lines); _render_tree())
	var box := HBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	box.offset_left = 6
	box.offset_right = -6
	box.alignment = BoxContainer.ALIGNMENT_CENTER
	box.add_theme_constant_override("separation", 6)
	b.add_child(box)
	if not recipe.is_empty():
		var ic := UIKit.icon(GameData.tool_icon(recipe.id), 32)
		ic.modulate = Color.WHITE if open else Color(0.45, 0.45, 0.5)
		box.add_child(ic)
	elif not open:
		box.add_child(UIKit.pixel_icon(LOCK, UIKit.MUTED))
	var text := VBoxContainer.new()
	text.alignment = BoxContainer.ALIGNMENT_CENTER
	text.add_theme_constant_override("separation", 0)
	box.add_child(text)
	text.add_child(UIKit.label("Lv %d" % int(n.level), UIKit.RARE if open else UIKit.MUTED, 16))
	var sub: String = recipe.label if not recipe.is_empty() else str(n.name).trim_prefix("TEST ")
	var sl := UIKit.label(sub, Color.WHITE if open else UIKit.MUTED, 11)
	sl.clip_text = true
	sl.custom_minimum_size.x = TREE_NODE.x - (52 if not recipe.is_empty() else 34)
	text.add_child(sl)
	for c in b.find_children("*", "Control", true, false):
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


func _skill_row(key: String, s: Dictionary) -> Button:
	var selected := key == skill
	var b := _plain_button(func(): skill = key; _open_tree(key))
	b.custom_minimum_size = Vector2(0, 70 if selected else 52)
	b.add_theme_stylebox_override("normal", UIKit.slot(UIKit.SLOT, UIKit.GOLD, 2, 6.0) if selected else UIKit.button_box("normal", UIKit.SLOT, 6.0))
	var box := VBoxContainer.new()
	box.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	box.offset_left = 10
	box.offset_right = -10
	box.offset_top = 5
	box.offset_bottom = -5
	box.add_theme_constant_override("separation", 3)
	box.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(box)
	var top := HBoxContainer.new()
	top.mouse_filter = Control.MOUSE_FILTER_IGNORE
	box.add_child(top)
	top.add_child(UIKit.label(GameData.SKILLS[key].label, Color.WHITE, 15))
	top.add_child(UIKit.spacer())
	var built := not s.is_empty()
	top.add_child(UIKit.label(str(int(s.level)) if built else NOT_BUILT, UIKit.RARE if built else UIKit.MUTED, 15 if built else 12))
	var bar := ProgressBar.new()
	bar.custom_minimum_size = Vector2(0, 12)
	bar.show_percentage = false
	bar.max_value = maxf(1.0, float(s.get("need", 1)))
	bar.value = float(s.get("xp", 0))
	bar.add_theme_stylebox_override("background", UIKit.bar_track())
	bar.add_theme_stylebox_override("fill", UIKit.bar(Color.WHITE))
	box.add_child(bar)
	var xp := "%d / %d XP · %d to level %d" % [int(s.xp), int(s.need), int(s.need) - int(s.xp), int(s.level) + 1] if built else "XP: " + NOT_BUILT
	b.tooltip_text = "%s\n%s" % [GameData.SKILLS[key].label, xp]
	if selected:
		box.add_child(UIKit.label(xp, UIKit.MUTED, 12))         # click shows what hover shows (section 4.5)
	for c in box.find_children("*", "Control", true, false):
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


# --- Trophies --------------------------------------------------------------------------------

func _render_trophies() -> void:
	var list := _trophies()
	if list.is_empty():
		_content.add_child(UIKit.label("Trophies: " + NOT_BUILT, UIKit.MUTED, 16))
		return
	var earned: Array = profile.get("earned", [])
	_content.add_child(UIKit.label("Trophies %d / %d" % [earned.size(), list.size()], Color.WHITE, 18))
	var grid := GridContainer.new()
	grid.columns = 8
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	_content.add_child(grid)
	for t in list:
		var got: bool = t.id in earned
		var tip := _trophy_text(t, got)
		grid.add_child(_slot_button(str(t.name).trim_prefix("TEST ").left(1), not got, "", tip,
			func(): _detail["trophies"] = tip.replace("\n", "  ·  "); _refresh()))
	_content.add_child(_vspace())
	_content.add_child(UIKit.divider())
	var info := UIKit.label(_detail.get("trophies", "Click a trophy to see where it comes from."),
		Color.WHITE if _detail.has("trophies") else UIKit.MUTED, 14)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.custom_minimum_size.y = 44
	_content.add_child(info)


## Tooltip order (section 4.3): name, kind, what it gives, where it comes from.
func _trophy_text(t: Dictionary, got: bool) -> String:
	var reward := "no reward"
	if t.has("title"):
		reward = "the title \"%s\"" % title_name(t.title)
	elif t.has("emblem"):
		reward = "the emblem \"%s\"" % _find(_emblems(), t.emblem).get("name", "")
	return "%s\nTrophy · %s\nGives %s\nFrom the challenge: %s" % [t.name, "earned" if got else "not earned yet", reward, t.challenge]


# --- Collection ------------------------------------------------------------------------------

func _render_collection() -> void:
	var wallet: String = profile.get("wallet", "")
	var imps: Array = profile.get("imps", [])
	if wallet == "":
		_content.add_child(_note("Connect a wallet in the Profile menu to see your Impz"))
		if is_self:
			_content.add_child(_left(UIKit.button("Open Profile menu", true, func(): close(); ProfileUI.open_menu())))
		return
	if Look.state == "loading" and is_self:
		_content.add_child(_note("Checking your wallet..."))
		return
	if imps.is_empty():
		_content.add_child(_note("No Impz in this wallet"))
		return
	_content.add_child(_heading("Your Impz (%d)" % imps.size()))
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	_content.add_child(scroll)
	var grid := GridContainer.new()
	grid.columns = 4
	grid.add_theme_constant_override("h_separation", 12)
	grid.add_theme_constant_override("v_separation", 12)
	scroll.add_child(grid)
	for n in imps:
		grid.add_child(_imp_card(int(n)))
	_load_imp_pictures(imps)


## One Imp: its NFT picture in a recessed slot and its number from the metadata under it.
func _imp_card(id: int) -> Control:
	var card := VBoxContainer.new()
	card.add_theme_constant_override("separation", 4)
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 4.0))
	card.add_child(frame)
	var pic = _imp_pictures.get(id)
	if pic is Texture2D:
		var t := TextureRect.new()
		t.texture = pic
		t.custom_minimum_size = Vector2(IMP_PICTURE, IMP_PICTURE)
		t.stretch_mode = TextureRect.STRETCH_KEEP_CENTERED
		t.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
		frame.add_child(t)
	else:
		var wait := UIKit.label("Can't load" if pic == "failed" else "Loading...", UIKit.MUTED, 13)
		wait.custom_minimum_size = Vector2(IMP_PICTURE, IMP_PICTURE)
		wait.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
		wait.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
		frame.add_child(wait)
	var label := UIKit.label(str(_imp_names.get(id, "IMPLINGZ #%d" % id)), UIKit.RARE, 15)
	label.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	card.add_child(label)
	return card


## Fetch the metadata and picture of every Imp not loaded yet, LOADERS at a time.
func _load_imp_pictures(imps: Array) -> void:
	for n in imps:
		var id := int(n)
		if not _imp_pictures.has(id) and not id in _imp_queue:
			_imp_pictures[id] = "loading"
			_imp_queue.append(id)
	while _imp_loading < LOADERS and not _imp_queue.is_empty():
		_load_imp(_imp_queue.pop_front())


## One Imp: its name and image from the metadata. The picture comes from the game's own copy of the collection
## (assets/sprites/implingz_generations, the same pictures) when it has it, otherwise from IPFS.
func _load_imp(id: int) -> void:
	_imp_loading += 1
	var http := HTTPRequest.new()
	http.timeout = 30.0
	add_child(http)
	var meta := await _fetch(http, METADATA + str(id))
	var data = JSON.parse_string(meta.get_string_from_utf8()) if not meta.is_empty() else null
	var image_url := ""
	if data is Dictionary:
		_imp_names[id] = str(data.get("name", "IMPLINGZ #%d" % id))
		image_url = str(data.get("image", "")).replace("ipfs://", IPFS_GATEWAY)
	var img := Image.new()
	var ok := false
	var local := ProjectSettings.globalize_path(LOCAL_PICTURES % id)
	if FileAccess.file_exists(local):
		ok = img.load(local) == OK
	if not ok and image_url != "":
		var bytes := await _fetch(http, image_url)
		ok = not bytes.is_empty() and img.load_png_from_buffer(bytes) == OK
	http.queue_free()
	if ok:
		img.resize(IMP_PICTURE, IMP_PICTURE, Image.INTERPOLATE_NEAREST)
	_imp_pictures[id] = ImageTexture.create_from_image(img) if ok else "failed"
	_imp_loading -= 1
	if visible and tab == "collection" and _picker == "":
		_refresh()
	_load_imp_pictures([])


func _fetch(http: HTTPRequest, url: String) -> PackedByteArray:
	if http.request(url) != OK:
		return PackedByteArray()
	var res: Array = await http.request_completed
	return res[3] if res[0] == HTTPRequest.RESULT_SUCCESS and res[1] == 200 else PackedByteArray()


func _open_customizer() -> void:
	close()
	Customizer.open()


# --- Information -----------------------------------------------------------------------------

func _render_information() -> void:
	var grid := GridContainer.new()
	grid.columns = 2
	grid.add_theme_constant_override("h_separation", 24)
	grid.add_theme_constant_override("v_separation", 10)
	_content.add_child(grid)
	var level: int = profile.get("level", -1)
	var coins: float = profile.get("coins", -1.0)
	var wallet: String = profile.get("wallet", "")
	var rows := [
		["Username", profile.get("name", "") if profile.get("name", "") != "" else "No username yet"],
		["Player level", str(level) if level >= 0 else NOT_BUILT],
		["Prestige", str(profile.get("prestige", -1)) if level >= 0 else NOT_BUILT],
		["Joined", profile.get("joined", "") if profile.get("joined", "") != "" else "-"],
		["Imp Coins", AccountPanel.format_coins(coins) if coins >= 0.0 else "Connect a wallet"],
		["Wallet", _short(wallet) if wallet != "" else "Not connected"],
		["Impz held", str(profile.get("imps", []).size()) if wallet != "" else "-"],
	]
	for r in rows:
		grid.add_child(UIKit.label(r[0], UIKit.MUTED, 15))
		grid.add_child(UIKit.label(str(r[1]), UIKit.RARE if r[0] == "Imp Coins" and coins >= 0.0 else Color.WHITE, 15))
	if is_self:
		_content.add_child(_vspace())
		var b := UIKit.button("Change username", true, func(): close(); ProfileUI.open_menu())
		b.custom_minimum_size = Vector2(200, MIN_TAP)
		b.tooltip_text = "Opens the Profile menu, where the username is saved on impz.club"
		_content.add_child(_left(b))


static func _short(address: String) -> String:
	return address.substr(0, 6) + "..." + address.right(4) if address.length() > 12 else address


# --- the title / emblem picker -----------------------------------------------------------------

func _open_picker(kind: String) -> void:
	if not is_self:
		return
	_picker = kind
	_refresh()


func _render_picker(kind: String) -> void:
	var head := HBoxContainer.new()
	_content.add_child(head)
	head.add_child(UIKit.label("Titles" if kind == "title" else "Emblems", Color.WHITE, 18))
	head.add_child(UIKit.spacer())
	var back := UIKit.button("Back", true, _close_picker)
	back.custom_minimum_size = Vector2(90, MIN_TAP)
	head.add_child(back)
	var items := _titles() if kind == "title" else _emblems()
	if items.is_empty():
		_content.add_child(_note(NOT_BUILT))
		return
	var grid := GridContainer.new()
	grid.columns = 2 if kind == "title" else 8
	grid.add_theme_constant_override("h_separation", 8)
	grid.add_theme_constant_override("v_separation", 8)
	grid.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	var scroll := ScrollContainer.new()
	scroll.size_flags_vertical = Control.SIZE_EXPAND_FILL
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.add_child(grid)
	_content.add_child(scroll)
	grid.add_child(_pick_slot(kind, {id = "", name = "None"}, true))
	for e in items:
		grid.add_child(_pick_slot(kind, e, _unlocked(kind, e.id)))
	_content.add_child(UIKit.divider())
	var info := UIKit.label(_detail.get(kind, "Click one to equip it. Locked ones come from trophies."),
		Color.WHITE if _detail.has(kind) else UIKit.MUTED, 14)
	info.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	info.custom_minimum_size.y = 44
	_content.add_child(info)


## A title or emblem in a slot: unlocked in full colour (click equips it), locked greyed with a lock (click says
## which challenge gives it). The equipped one has the gold rim.
func _pick_slot(kind: String, e: Dictionary, open: bool) -> Button:
	var on: bool = profile.get(kind, "") == e.id
	var from := "" if open else "From: " + str(_trophy_for(kind, e.id).get("challenge", "?"))
	var tip := "%s\n%s" % [e.name, "Equipped" if on else ("Click to equip" if open else from)]
	var size := Vector2(0, 56) if kind == "title" else Vector2(64, 64)
	var on_click := func():
		if open:
			_detail.erase(kind)
			_equip(kind, e.id)
		else:
			_detail[kind] = "%s  ·  %s" % [e.name, from]
			_refresh()
	var b := _slot_button("", false, "", tip, on_click, size)
	if kind == "title":
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	if on:
		for state in ["normal", "hover", "pressed"]:
			b.add_theme_stylebox_override(state, UIKit.slot(UIKit.SLOT, UIKit.GOLD, 2, 4.0))
	var center: Control = b.get_child(0)
	for c in center.get_children():
		center.remove_child(c)
		c.queue_free()
	var row := HBoxContainer.new()
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	center.add_child(row)
	if not open:
		row.add_child(UIKit.pixel_icon(LOCK, UIKit.MUTED))
	if kind == "emblem" and e.id != "":
		var art := _emblem_art(e.id, 40)
		art.modulate.a = 1.0 if open else 0.35
		if open:
			row.add_child(art)
	else:
		row.add_child(UIKit.label(e.name, (UIKit.RARE if e.id != "" else Color.WHITE) if open else UIKit.MUTED,
			15 if kind == "title" else 13))
	for c in row.find_children("*", "Control", true, false) + [row]:
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return b


# --- pieces ----------------------------------------------------------------------------------

func _plain_button(on_press: Callable) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	for state in ["normal", "hover", "pressed", "disabled"]:
		b.add_theme_stylebox_override(state, UIKit.button_box(state, UIKit.SLOT, 6.0))
	b.pressed.connect(on_press)
	return b


## A recessed slot you can click: unlocked in full colour, locked greyed with a lock (and `under`, e.g. "Lv 25").
func _slot_button(text: String, locked: bool, under: String, tip: String, on_press: Callable, size := Vector2(64, 64)) -> Button:
	var b := Button.new()
	b.focus_mode = Control.FOCUS_NONE
	b.custom_minimum_size = size
	b.tooltip_text = tip
	for state in ["normal", "hover", "pressed", "disabled"]:
		var fill := UIKit.SLOT.lightened(0.08) if state == "hover" else UIKit.SLOT
		b.add_theme_stylebox_override(state, UIKit.slot(fill, UIKit.OUTLINE, 1, 4.0))
	if on_press.is_valid():
		b.pressed.connect(on_press)
	var center := VBoxContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	center.alignment = BoxContainer.ALIGNMENT_CENTER
	center.add_theme_constant_override("separation", 2)
	center.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(center)
	if locked:
		var lock := UIKit.pixel_icon(LOCK, UIKit.MUTED)
		lock.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		center.add_child(lock)
		if under != "":
			center.add_child(UIKit.label(under, UIKit.MUTED, 12))
	else:
		center.add_child(UIKit.label(text, UIKit.RARE, 18))
	for c in center.get_children():
		c.mouse_filter = Control.MOUSE_FILTER_IGNORE
		if c is Label:
			c.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	return b


## A tab: clicked, no key (J00BA, 2026-11-08).
func _tab_button(text: String, on_press: Callable) -> Button:
	var b := _plain_button(on_press)
	var l := UIKit.label(text, Color.WHITE, 15)
	l.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	l.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(l)
	b.set_meta("label", l)
	b.custom_minimum_size = Vector2(120, MIN_TAP)
	return b


## A button that shows its key (section 4.1: "show the key on every button").
func _key_button(key: String, text: String, on_press: Callable) -> Button:
	var b := _plain_button(on_press)
	var row := HBoxContainer.new()
	row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	row.alignment = BoxContainer.ALIGNMENT_CENTER
	row.add_theme_constant_override("separation", 8)
	row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	b.add_child(row)
	row.add_child(_key_cap(key))
	var l := UIKit.label(text, Color.WHITE, 15)
	l.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	l.mouse_filter = Control.MOUSE_FILTER_IGNORE
	row.add_child(l)
	b.set_meta("label", l)
	b.custom_minimum_size = Vector2(maxi(MIN_TAP, 44 + text.length() * 9 + 24), MIN_TAP)
	return b


func _key_cap(key: String) -> Label:
	var cap := UIKit.label(key, Color.BLACK, 14)
	cap.add_theme_stylebox_override("normal", UIKit.key_cap())
	cap.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	cap.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return cap


func _style_tab(b: Button, open: bool) -> void:
	# the open tab: pressed, with the held tool's thick gold rim (not green: green means "can")
	b.add_theme_stylebox_override("normal", UIKit.slot(UIKit.SLOT, UIKit.GOLD, 2, 6.0) if open else UIKit.button_box("normal", UIKit.SLOT, 6.0))
	b.add_theme_stylebox_override("hover", UIKit.slot(UIKit.SLOT, UIKit.GOLD, 2, 6.0) if open else UIKit.button_box("hover", UIKit.SLOT, 6.0))
	var l: Label = b.get_meta("label")
	l.add_theme_color_override("font_color", UIKit.RARE if open else Color.WHITE)


func _heading(text: String) -> Label:
	var l := UIKit.label(text, UIKit.RARE, 17)
	l.add_theme_color_override("font_shadow_color", UIKit.OUTLINE)
	l.add_theme_constant_override("shadow_offset_x", 2)
	l.add_theme_constant_override("shadow_offset_y", 2)
	return l


func _note(text: String, color := UIKit.MUTED) -> Label:
	var l := UIKit.label(text, color, 14)
	l.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	l.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	return l


func _left(c: Control) -> HBoxContainer:
	var r := HBoxContainer.new()
	r.add_child(c)
	return r


func _vspace() -> Control:
	var s := Control.new()
	s.size_flags_vertical = Control.SIZE_EXPAND_FILL
	return s


func _vline() -> ColorRect:
	# a 1-art-pixel line in the frame colour between the two halves (the mockup's divider)
	var r := ColorRect.new()
	r.color = UIKit.GOLD.darkened(0.15)
	r.custom_minimum_size = Vector2(UIKit.PX, 0)
	r.mouse_filter = Control.MOUSE_FILTER_IGNORE
	return r


# --- the 3D Imp ------------------------------------------------------------------------------

func _clear_preview() -> void:
	if _holder == null:
		return
	for c in _holder.get_children():
		_holder.remove_child(c)
		c.queue_free()


func _rebuild_preview() -> void:
	_clear_preview()
	_holder.add_child(ImpBuilder.build(profile.get("look", Look.shown())))


func _on_preview_input(event: InputEvent) -> void:
	if event is InputEventMouseButton:
		if event.button_index == MOUSE_BUTTON_LEFT:
			_dragging = event.pressed
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_UP:
			_dist = maxf(130.0, _dist - 18.0)
		elif event.pressed and event.button_index == MOUSE_BUTTON_WHEEL_DOWN:
			_dist = minf(480.0, _dist + 18.0)
	elif event is InputEventMouseMotion and _dragging:
		_yaw -= event.relative.x * 0.01
		_pitch = clampf(_pitch + event.relative.y * 0.006, -0.35, 0.9)


# --- layout ----------------------------------------------------------------------------------

func _build() -> void:
	var dim := ColorRect.new()
	dim.color = Color(0, 0, 0, 0.35)            # the world keeps running and stays visible (section 4.1)
	dim.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(dim)
	var center := CenterContainer.new()
	center.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	add_child(center)
	_panel = PanelContainer.new()
	_panel.add_theme_stylebox_override("panel", UIKit.panel())
	center.add_child(_panel)
	var vbox := VBoxContainer.new()
	vbox.add_theme_constant_override("separation", 8)
	_panel.add_child(vbox)

	var head := HBoxContainer.new()
	head.add_theme_constant_override("separation", 10)
	vbox.add_child(head)
	head.add_child(UIKit.title("Profile"))
	head.add_child(_key_cap("P"))
	_test_tag = UIKit.label("TEST data", UIKit.SHORT, 13)
	_test_tag.size_flags_vertical = Control.SIZE_SHRINK_CENTER
	_test_tag.tooltip_text = "Values from data/profile_test.json (debug builds only)"
	_test_tag.mouse_filter = Control.MOUSE_FILTER_STOP
	head.add_child(_test_tag)
	head.add_child(UIKit.spacer())
	var close_button := UIKit.button("Close", true, close)
	close_button.custom_minimum_size = Vector2(90, MIN_TAP)
	head.add_child(close_button)
	vbox.add_child(UIKit.divider())

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 16)
	vbox.add_child(body)

	# left panel: name and level, the Imp, emblem and title
	var left := VBoxContainer.new()
	left.custom_minimum_size.x = PREVIEW_SIZE.x + 12
	left.add_theme_constant_override("separation", 8)
	body.add_child(left)
	var top := HBoxContainer.new()
	top.add_theme_constant_override("separation", 6)
	left.add_child(top)
	var name_box := PanelContainer.new()
	name_box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	name_box.custom_minimum_size.y = 60
	name_box.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 10.0))
	top.add_child(name_box)
	_name_label = UIKit.label("", Color.WHITE, 18)
	_name_label.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_name_label.clip_text = true
	_name_label.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
	name_box.add_child(_name_label)
	var level_panel := PanelContainer.new()
	level_panel.custom_minimum_size = Vector2(56, 60)        # half the first width (J00BA): the name gets the room
	level_panel.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 4.0))
	top.add_child(level_panel)
	_level_box = HBoxContainer.new()
	_level_box.alignment = BoxContainer.ALIGNMENT_CENTER
	_level_box.add_theme_constant_override("separation", 4)
	_level_box.mouse_filter = Control.MOUSE_FILTER_STOP
	level_panel.add_child(_level_box)

	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIKit.slot(Color(0.16, 0.2, 0.26, 1.0), UIKit.OUTLINE, 1, 3.0))
	left.add_child(frame)
	var container := SubViewportContainer.new()
	container.stretch = true
	container.custom_minimum_size = PREVIEW_SIZE
	container.mouse_default_cursor_shape = Control.CURSOR_DRAG
	container.tooltip_text = "Drag to turn · wheel to zoom"
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
	_camera = Camera3D.new()
	_camera.fov = 32.0
	_camera.near = 1.0
	_camera.far = 2000.0
	vp.add_child(_camera)
	_holder = Node3D.new()
	vp.add_child(_holder)

	var under := HBoxContainer.new()
	left.add_child(under)
	under.add_theme_constant_override("separation", 6)
	_rotate_button = _plain_button(_toggle_spin)       # turns the Imp; click to stop, "(Stopped)" in red (J00BA)
	_rotate_button.custom_minimum_size = Vector2(0, MIN_TAP)
	_rotate_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	_rotate_button.tooltip_text = "Click to stop or start the turning. Drag the Imp to turn it, wheel to zoom."
	var rot_row := HBoxContainer.new()
	rot_row.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	rot_row.alignment = BoxContainer.ALIGNMENT_CENTER
	rot_row.add_theme_constant_override("separation", 5)
	rot_row.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_rotate_button.add_child(rot_row)
	var rot_label := UIKit.label("Rotate model", Color.WHITE, 14)
	rot_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	rot_row.add_child(rot_label)
	_stopped_label = UIKit.label("(Stopped)", UIKit.SHORT, 14)
	_stopped_label.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_stopped_label.visible = not spin
	rot_row.add_child(_stopped_label)
	under.add_child(_rotate_button)
	_customize_button = _key_button("C", "Customize", _open_customizer)
	under.add_child(_customize_button)

	var boxes := HBoxContainer.new()
	boxes.add_theme_constant_override("separation", 6)
	left.add_child(boxes)
	_emblem_button = _plain_button(func(): _open_picker("emblem"))
	_emblem_button.custom_minimum_size = Vector2(72, 72)
	boxes.add_child(_emblem_button)
	_title_button = _plain_button(func(): _open_picker("title"))
	_title_button.custom_minimum_size = Vector2(0, 72)
	_title_button.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	boxes.add_child(_title_button)

	# right: the tabs, and the open tab (or a picker) in a recessed well
	var right := VBoxContainer.new()
	right.custom_minimum_size = Vector2(700, 0)
	right.add_theme_constant_override("separation", 8)
	body.add_child(right)
	_tabs_row = HBoxContainer.new()
	_tabs_row.add_theme_constant_override("separation", 6)
	right.add_child(_tabs_row)
	for i in TABS.size():
		var t: Dictionary = TABS[i]
		var b := _tab_button(t.label, func(): _set_tab(t.key))
		b.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		_tab_buttons[t.key] = b
		_tabs_row.add_child(b)
	_well = PanelContainer.new()
	_well.size_flags_vertical = Control.SIZE_EXPAND_FILL
	_well.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, UIKit.OUTLINE, 1, 12.0))
	right.add_child(_well)
	_content = VBoxContainer.new()
	_content.add_theme_constant_override("separation", 8)
	_well.add_child(_content)
