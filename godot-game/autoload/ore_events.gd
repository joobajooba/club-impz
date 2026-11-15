extends Node
## Ore events, as the OreEvents autoload. Voidstone and stellarite don't grow in the world like the other
## ores: a vein appears now and then as a world event, somewhere in the resource world, for a while.
## Every player gets "Voidstone has spawned somewhere in the world, go mine it!" in the middle of the
## screen for 5 seconds, and anyone with a good enough pickaxe can mine it at the same time: every swing
## has a chance to give the ore (scripts/player/ore_miner.gd), so it is never locked to one player.
##
## Online, the server (game-server/server.mjs) rolls the events and tells everyone, so every player has
## the same vein in the same place (one of resource_landmarks.gd's EVENT_SPOTS, picked by the server).
## Playing alone, the game rolls them itself with the same odds.

signal started(ev: Dictionary)   # {id, ore, spot, until (msec)}
signal ended(id: int)

const ORES := {  # the same odds as the server (ORE_EVENTS in server.mjs)
	"void": {label = "Voidstone", chance = 1.0 / 45.0, minutes = 15.0},
	"stellarite": {label = "Stellarite", chance = 1.0 / 120.0, minutes = 15.0},
}
const SPOTS := 48                 # resource_landmarks.gd EVENT_SPOTS has this many
const CHECK_SECONDS := 60.0
const SHOW_SECONDS := 5.0

var events := {}                  # id -> {id, ore, spot, until}
var _check := CHECK_SECONDS
var _local_id := -1               # events rolled offline get negative ids
var _layer: CanvasLayer
var _banner: Label
var _tween: Tween


func _ready() -> void:
	_build_banner()


func _process(delta: float) -> void:
	var now := Time.get_ticks_msec()
	for id in events.keys():
		if now >= int(events[id].until):
			_end(id)
	if Net.state == "online":
		return                    # the server rolls them
	_check -= delta
	if _check > 0.0:
		return
	_check = CHECK_SECONDS
	for ore in ORES:
		if not _running(ore) and randf() < float(ORES[ore].chance):
			start_local(ore)


func _running(ore: String) -> bool:
	for ev in events.values():
		if ev.ore == ore:
			return true
	return false


## From the server: a new event, or the ones already running when we joined.
func on_server_event(ev: Dictionary, announce := true) -> void:
	var id := int(ev.get("id", 0))
	var ore := str(ev.get("ore", ""))
	if not ORES.has(ore) or events.has(id):
		return
	_start({id = id, ore = ore, spot = int(ev.get("spot", 0)) % SPOTS,
		until = Time.get_ticks_msec() + int(ev.get("left", 0))}, announce)


func on_server_end(id: int) -> void:
	_end(id)


## Online again: the server's list replaces the events this game rolled alone.
func on_welcome(list: Array) -> void:
	for id in events.keys():
		if id < 0:
			_end(id)
	for ev in list:
		on_server_event(ev, false)


## Offline (and testing, --ore_event=void): this game rolls its own event.
func start_local(ore: String) -> void:
	var taken := events.values().map(func(e): return e.spot)
	var spot := randi() % SPOTS
	while spot in taken:
		spot = (spot + 1) % SPOTS
	_start({id = _local_id, ore = ore, spot = spot, until = Time.get_ticks_msec() + int(ORES[ore].minutes * 60000.0)}, true)
	_local_id -= 1


func _start(ev: Dictionary, announce: bool) -> void:
	events[ev.id] = ev
	started.emit(ev)
	if announce:
		show_banner("%s has spawned somewhere in the world, go mine it!" % ORES[ev.ore].label)


func _end(id: int) -> void:
	if events.erase(id):
		ended.emit(id)


func label(ore: String) -> String:
	return ORES[ore].label if ORES.has(ore) else ore.capitalize()


# --- the announcement in the middle of the screen --------------------------------------------------

func _build_banner() -> void:
	_layer = CanvasLayer.new()
	_layer.layer = 15                                  # over the HUD and menus, under the loading screen
	add_child(_layer)
	_banner = Label.new()
	_banner.set_anchors_and_offsets_preset(Control.PRESET_FULL_RECT)
	_banner.offset_bottom = -180.0                     # centred a little above the middle, clear of the Imp
	_banner.autowrap_mode = TextServer.AUTOWRAP_WORD_SMART
	_banner.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	_banner.vertical_alignment = VERTICAL_ALIGNMENT_CENTER
	_banner.mouse_filter = Control.MOUSE_FILTER_IGNORE
	_banner.add_theme_font_size_override("font_size", 30)
	_banner.add_theme_color_override("font_color", Color(1.0, 0.86, 0.4))
	_banner.add_theme_color_override("font_outline_color", Color("#0b0c10"))
	_banner.add_theme_constant_override("outline_size", 10)
	_banner.add_theme_color_override("font_shadow_color", Color(0, 0, 0, 0.6))
	_banner.add_theme_constant_override("shadow_offset_y", 3)
	_banner.modulate.a = 0.0
	_layer.add_child(_banner)


func show_banner(text: String) -> void:
	_banner.text = text
	if _tween:
		_tween.kill()
	_tween = create_tween()
	_tween.tween_property(_banner, "modulate:a", 1.0, 0.3)
	_tween.tween_interval(SHOW_SECONDS - 0.8)
	_tween.tween_property(_banner, "modulate:a", 0.0, 0.5)
