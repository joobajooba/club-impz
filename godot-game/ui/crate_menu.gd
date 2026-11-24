extends Modal
## A crate chest's menu (J00BA, 2026-11-21), like a Minecraft server crate. E at a crate chest in the hub opens it
## (shop_keeper.gd calls open_for with the chest). The top is the reel; under it, every drop with its count,
## rarity and chance (GameData.CRATES). Open spends one of the crate's keys (Inventory.open_crate, which gives the
## item at once) and spins the reel CS:GO style: a strip of random weighted items slides under a centre line,
## slowing down, and stops on the prize. The chest's lid opens with it and shuts when the menu closes.

const TILE := 104.0               # one reel tile
const GAP := 6.0
const VIEW_W := 700.0            # the reel window
const STRIP := 44                # tiles on the strip
const WIN_AT := 37               # the tile the reel stops on
const SPIN_TIME := 5.6

var crate := ""
var chest: Node3D
var _reel_clip: Control
var _strip: HBoxContainer
var _result: Label
var _spinning := false
var _tween: Tween
var _last_tick := -1
var _tick: AudioStreamPlayer


func _init() -> void:
	kinds = ["crate"]


func _ready() -> void:
	super._ready()
	_tick = AudioStreamPlayer.new()
	_tick.stream = _tick_sound()
	_tick.volume_db = -10.0
	add_child(_tick)


func open_for(target: Node3D) -> void:
	chest = target
	crate = String(target.get_meta("crate"))
	kind = "crate"
	_title.text = GameData.CRATES[crate].label
	_result.text = "Spin to see what you win"
	_result.add_theme_color_override("font_color", UIKit.MUTED)
	_fill_strip([], -1)
	visible = true
	_refresh()


func close() -> void:
	if _spinning:                    # let the reel land first (the prize is already in the inventory)
		return
	if visible:
		_lid("close")
	visible = false


func _process(_delta: float) -> void:
	if not _spinning:
		return
	var i := int((-_strip.position.x + VIEW_W * 0.5) / (TILE + GAP))   # the tile under the centre line
	if i != _last_tick:
		_last_tick = i
		_tick.pitch_scale = randf_range(0.95, 1.08)
		_tick.play()


# --- the list ---------------------------------------------------------------------

func _render() -> void:
	var c: Dictionary = GameData.CRATES[crate]
	var keys := Inventory.count(c.key)
	var top := UIKit.row(_list)
	top.add_child(UIKit.icon(GameData.item_icon(c.key), 32))
	top.add_child(UIKit.label("%s: %d" % [c.key_label, keys], UIKit.GOOD if keys > 0 else UIKit.SHORT, 17))
	top.add_child(UIKit.spacer())
	top.add_child(UIKit.button("+1 key (TEST)", not _spinning, func(): Inventory.test_add_keys(crate)))
	var why := Inventory.crate_blocker(crate)
	top.add_child(UIKit.button("  Open  (1 key)  ", why == "" and not _spinning, _spin))
	if why != "" and not _spinning:
		_note(why + ". Keys open this chest for free.")
	_heading("Contents")
	var grid := HBoxContainer.new()                  # one card per drop, like a CS:GO case's contents
	grid.add_theme_constant_override("separation", 8)
	_list.add_child(grid)
	for d in c.drops:
		var rar: Array = GameData.CRATE_RARITY[d.rarity]
		var card := PanelContainer.new()
		card.size_flags_horizontal = Control.SIZE_EXPAND_FILL
		card.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, rar[1].darkened(0.2), 2, 6.0))
		card.tooltip_text = "%s x%d\n%s, %s%% chance" % [GameData.item_label(d.id), d.n, rar[0], _pct(GameData.crate_chance(crate, d))]
		grid.add_child(card)
		var v := VBoxContainer.new()
		v.add_theme_constant_override("separation", 0)
		card.add_child(v)
		var ic := UIKit.icon(GameData.item_icon(d.id), 48)
		ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
		v.add_child(ic)
		for part in [["%s x%d" % [GameData.item_label(d.id), d.n], Color.WHITE, 13], [rar[0], rar[1], 12],
				["%s%%" % _pct(GameData.crate_chance(crate, d)), rar[1], 20]]:
			var l := UIKit.label(part[0], part[1], part[2])
			l.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
			l.text_overrun_behavior = TextServer.OVERRUN_TRIM_ELLIPSIS
			v.add_child(l)


static func _pct(p: float) -> String:
	var v := p * 100.0
	return ("%.0f" % v) if is_equal_approx(v, roundf(v)) else ("%.1f" % v)


# --- the reel ---------------------------------------------------------------------

func _spin() -> void:
	if _spinning:
		return
	var drop := Inventory.open_crate(crate)
	if drop.is_empty():
		return
	var tiles := []
	for i in STRIP:
		tiles.append(drop if i == WIN_AT else GameData.crate_roll(crate))
	_fill_strip(tiles, WIN_AT)
	_result.text = "..."
	_result.add_theme_color_override("font_color", UIKit.MUTED)
	_spinning = true
	_last_tick = -1
	_lid("open")
	_refresh()
	# stop with the centre line somewhere inside the winning tile (not always dead centre, like the real thing)
	var step := TILE + GAP
	var inside := randf_range(-TILE * 0.42, TILE * 0.42)
	var end_x := -(WIN_AT * step + TILE * 0.5 + inside - VIEW_W * 0.5)
	_strip.position.x = 0.0
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_property(_strip, "position:x", end_x, SPIN_TIME).set_trans(Tween.TRANS_QUINT).set_ease(Tween.EASE_OUT)
	_tween.tween_property(_strip, "position:x", -(WIN_AT * step + TILE * 0.5 - VIEW_W * 0.5), 0.35) \
			.set_trans(Tween.TRANS_SINE).set_ease(Tween.EASE_IN_OUT)   # settle onto the tile's centre
	_tween.tween_callback(_landed.bind(drop))


func _landed(drop: Dictionary) -> void:
	_spinning = false
	var rar: Array = GameData.CRATE_RARITY[drop.rarity]
	_result.text = "You won %s x%d!  (%s)" % [GameData.item_label(drop.id), drop.n, rar[0]]
	_result.add_theme_color_override("font_color", rar[1])
	var win := _strip.get_child(WIN_AT) as Control
	var flash := create_tween().set_loops(3)
	flash.tween_property(win, "modulate", Color(1.8, 1.8, 1.8), 0.12)
	flash.tween_property(win, "modulate", Color.WHITE, 0.12)
	Inventory.looted.emit(drop.id, drop.n, drop.rarity in ["epic", "legendary"])   # the HUD's "+1 Ruby" line
	_refresh()


## Lays out the strip: `tiles` are drops, or none for a resting reel of the crate's drops repeated.
func _fill_strip(tiles: Array, _win: int) -> void:
	for c in _strip.get_children():
		_strip.remove_child(c)
		c.queue_free()
	if tiles.is_empty():
		var drops: Array = GameData.CRATES[crate].drops if crate != "" else []
		for i in 9:
			if not drops.is_empty():
				tiles.append(drops[i % drops.size()])
	for d in tiles:
		_strip.add_child(_tile(d))
	_strip.reset_size()
	_strip.position.x = 0.0
	if not _spinning and tiles.size() == 9:      # centre the resting reel on its middle tile
		_strip.position.x = -(4 * (TILE + GAP) + TILE * 0.5 - VIEW_W * 0.5)


func _tile(d: Dictionary) -> Control:
	var rar: Array = GameData.CRATE_RARITY[d.rarity]
	var p := PanelContainer.new()
	p.custom_minimum_size = Vector2(TILE, TILE)
	p.add_theme_stylebox_override("panel", UIKit.slot(UIKit.SLOT, rar[1].darkened(0.1), 2))
	var v := VBoxContainer.new()
	v.alignment = BoxContainer.ALIGNMENT_CENTER
	v.add_theme_constant_override("separation", 0)
	p.add_child(v)
	var ic := UIKit.icon(GameData.item_icon(d.id), 48)
	ic.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	v.add_child(ic)
	var bar := ColorRect.new()                   # the rarity stripe along the bottom, as on CS:GO cases
	bar.color = rar[1]
	bar.custom_minimum_size = Vector2(0, 5)
	v.add_child(bar)
	var n := UIKit.label("x%d" % d.n, Color.WHITE, 12)
	n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	v.add_child(n)
	return p


func _build() -> void:
	super._build()
	_panel.custom_minimum_size = Vector2(780, 0)
	var vbox := _panel.get_child(0) as VBoxContainer
	var holder := VBoxContainer.new()
	holder.add_theme_constant_override("separation", 6)
	vbox.add_child(holder)
	vbox.move_child(holder, 2)                   # under the title and its divider, above the list
	var frame := PanelContainer.new()
	frame.add_theme_stylebox_override("panel", UIKit.slot(Color(0.07, 0.07, 0.09, 1.0), UIKit.OUTLINE, 2, 6.0))
	frame.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	holder.add_child(frame)
	_reel_clip = Control.new()
	_reel_clip.clip_contents = true
	_reel_clip.custom_minimum_size = Vector2(VIEW_W, TILE + 8)
	frame.add_child(_reel_clip)
	_strip = HBoxContainer.new()
	_strip.add_theme_constant_override("separation", int(GAP))
	_strip.position = Vector2(0, 4)
	_reel_clip.add_child(_strip)
	var line := ColorRect.new()                  # the centre marker
	line.color = UIKit.RARE
	line.size = Vector2(3, TILE + 8)
	line.position = Vector2(VIEW_W * 0.5 - 1.5, 0)
	_reel_clip.add_child(line)
	for up in [true, false]:                     # little gold notches top and bottom of the line
		var n := ColorRect.new()
		n.color = UIKit.RARE
		n.size = Vector2(11, 4)
		n.position = Vector2(VIEW_W * 0.5 - 5.5, 0 if up else TILE + 4)
		_reel_clip.add_child(n)
	_result = UIKit.label("", UIKit.MUTED, 18)
	_result.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	holder.add_child(_result)
	(vbox.get_child(vbox.get_child_count() - 1) as Control).custom_minimum_size = Vector2(0, 250)   # the list's scroll


func _lid(anim: String) -> void:
	if chest == null or not is_instance_valid(chest) or not chest.has_meta("anim"):
		return
	var ap := chest.get_meta("anim") as AnimationPlayer
	if ap and ap.has_animation(anim):
		ap.play(anim)
		if anim == "close" and ap.has_animation("idle"):
			ap.queue("idle")


## A short wooden click for each tile passing the line.
static func _tick_sound() -> AudioStreamWAV:
	var rate := 22050
	var n := int(rate * 0.035)
	var data := PackedByteArray()
	data.resize(n * 2)
	for i in n:
		var t := float(i) / rate
		var v := sin(TAU * 1900.0 * t) * 0.6 + sin(TAU * 900.0 * t) * 0.4
		v *= exp(-t * 140.0)
		data.encode_s16(i * 2, int(clampf(v, -1.0, 1.0) * 26000.0))
	var w := AudioStreamWAV.new()
	w.format = AudioStreamWAV.FORMAT_16_BITS
	w.mix_rate = rate
	w.data = data
	return w
