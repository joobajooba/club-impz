extends Node
## Fishing with the rod in the resource world (resource_gathering.md section 7, the rules in scripts/world/fishing.gd).
## A child of the player (imp_player.gd), next to ore_miner.gd.
##
## Stand on the shore by the rings with a rod in hand: the prompt shows "E  Fish for Trout (45s)", or what is
## missing ("Needs a Birch Rod"). E or F casts: D-109 says F, the live world gathers with E, so both work.
## - The float lands in the rings and the bar fills over the fish's time to catch while its shadow circles in.
## - Just before the bite the float twitches (a nibble), so the bite never comes out of nowhere. Then it dips:
##   E or F inside the bite window (D-135) lands the fish, the pearl may come with it, and the Imp casts again.
## - A missed bite drops the bar to half (section 7) and the fish comes round again; nothing else is lost.
## E or F while waiting, moving, or putting the rod away reels in. The bar on that spot is kept.

const ToolFx := preload("res://scripts/player/tool_fx.gd")
const NIBBLE := 1.6              # seconds of warning before the bite
const CAST_RELEASE := 0.84       # seconds into the rod swing (imp_visual ACTIONS.rod) when the line flies out
const FLIGHT := 0.45             # seconds the float is in the air
const SPLASH := [Color("#e8f6ff"), Color("#bfe3f2"), Color("#8cc6dc")]
const SOUNDS := ["fish_plop", "fish_nibble", "fish_splash"]

var player: CharacterBody3D
var visual: Node3D
var target = null               # fish_spot.gd in reach (for the prompt)
var spot = null                 # the fish_spot.gd being fished
var state := ""                  # "" | "cast" | "wait" | "bite"
var time_override := 0.0         # testing (--fish_time=3): every fish takes this long
var window_override := 0.0       # testing: the bite window in seconds
var caught := 0                  # fish landed from this spot so far (shown in the prompt)
var _t := 0.0                    # seconds in the current state
var _need := 0.0                 # seconds for this fish (its catch time, a little sooner or later)
var _window := 0.0
var _nibbles := 0
var _nibble_t := 0.0
var _released := false           # the line has left the tip this cast
var _from := Vector3.ZERO        # where the float starts a cast from
var _float: MeshInstance3D
var _line: MeshInstance3D
var _prompt := []
var _audio: AudioStreamPlayer3D
var _sounds := {}


func _ready() -> void:
	player = get_parent()
	visual = player.get_node("visual")
	for s in SOUNDS:
		var p := "res://assets/sounds/%s.wav" % s
		if ResourceLoader.exists(p):
			_sounds[s] = load(p)
	_audio = AudioStreamPlayer3D.new()
	_audio.unit_size = 5.0
	_audio.max_distance = 30.0
	add_child(_audio)
	_float = MeshInstance3D.new()
	_float.name = "cast_float"
	var ball := SphereMesh.new()
	ball.radius = 0.055
	ball.height = 0.1
	ball.radial_segments = 10
	ball.rings = 5
	var fm := StandardMaterial3D.new()
	fm.albedo_color = Color("#e83a2e")
	fm.roughness = 0.6
	ball.material = fm
	_float.mesh = ball
	_float.visible = false
	add_child(_float)
	_line = MeshInstance3D.new()
	_line.name = "cast_line"
	_line.mesh = ImmediateMesh.new()
	var lm := StandardMaterial3D.new()
	lm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	lm.albedo_color = Color(0.94, 0.94, 0.9, 0.85)
	lm.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	_line.material_override = lm
	_line.cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
	add_child(_line)


func is_fishing() -> bool:
	return state != "" and is_instance_valid(spot)


## E or F: cast, land a biting fish, or reel in. Returns false if there is nothing to fish, so the Imp just swings.
func use() -> bool:
	if is_fishing():
		if state == "bite":
			_land()
		elif state == "wait":
			stop()
		return true                                    # mid-cast: the swing finishes first
	if Inventory.in_hand != "rod" or not is_instance_valid(target):
		return false
	var why := Fishing.blocker(target.row, Inventory.held.rod)
	if why != "":
		Inventory.message.emit(why)
		return false
	spot = target
	caught = 0
	_face()
	_cast(_tip())
	return true


func stop() -> void:
	if is_instance_valid(spot):
		spot.pull = 0.0
	spot = null
	state = ""
	_float.visible = false
	(_line.mesh as ImmediateMesh).clear_surfaces()
	_show_held_float(true)


func catch_time() -> float:
	return time_override if time_override > 0.0 else Fishing.catch_time(spot.row, Inventory.held.rod)


func _face() -> void:
	var u := Vector3(player.global_position.x - spot.global_position.x, 0, player.global_position.z - spot.global_position.z)
	if u.length() > 0.01:
		visual.rotation.y = atan2(u.x, u.z)


func _cast(from: Vector3) -> void:
	state = "cast"
	_t = 0.0
	_released = false
	_from = from
	_float.visible = true
	_float.global_position = from
	_show_held_float(false)
	visual.play_action("rod")


func _tip() -> Vector3:
	var h = visual.get("held_tool")
	if h and is_instance_valid(h) and h.has_method("rod_tip") and h.rod_tip():
		return (h.rod_tip() as Node3D).global_position
	return player.global_position + Vector3.UP * 1.3 - visual.global_basis.z * 0.9


func _show_held_float(on: bool) -> void:
	var h = visual.get("held_tool")
	if h and is_instance_valid(h) and h.has_method("show_float"):
		h.show_float(on)


func _surface() -> Vector3:
	return spot.global_position + Vector3(0, 0.03, 0)


func _process(delta: float) -> void:
	if not is_fishing():
		if state != "":
			stop()
		_look_for_spot()
		return
	var moving := Input.get_vector("move_left", "move_right", "move_forward", "move_back").length() > 0.1 \
		or Input.is_action_pressed("jump")
	if moving or Inventory.in_hand != "rod" or player.frozen or player.menu_open():
		stop()
		return
	_t += delta
	var key := String(spot.name)
	var label: String = spot.label()
	var got := ("  (%d caught)" % caught) if caught > 0 else ""
	match state:
		"cast":
			if _t < CAST_RELEASE:                          # the float comes back to the tip and rides the swing
				_float.global_position = _from.lerp(_tip(), smoothstep(0.0, 0.3, _t))
			else:
				if not _released:
					_released = true
					_from = _tip()
				var u := clampf((_t - CAST_RELEASE) / FLIGHT, 0.0, 1.0)
				var p := _from.lerp(_surface(), u)
				p.y += sin(u * PI) * 1.1
				_float.global_position = p
				if u >= 1.0:
					_play("fish_plop", _surface())
					ToolFx.burst(get_tree().current_scene, _surface(), SPLASH, 6, 1.4, 0.04)
					state = "wait"
					_t = 0.0
					_nibbles = 0
					_need = catch_time() * randf_range(1.0 - Fishing.JITTER, 1.0 + Fishing.JITTER)
			_set_prompt("", "Casting for %s%s" % [label, got], "E", "Stop")
		"wait":
			var done: float = Fishing.progress.get(key, 0.0) + delta / maxf(_need, 0.1)
			var left := (1.0 - done) * _need
			if _nibbles < 2 and left <= NIBBLE * (1.0 if _nibbles == 0 else 0.45):
				_nibbles += 1                              # two little twitches before the bite
				_nibble_t = 0.0
				spot.nibble()
				_play("fish_nibble", _surface())
			_nibble_t += delta
			var bob := sin(_t * 2.2) * 0.012
			if _nibbles > 0:
				bob -= 0.035 * absf(sin(_nibble_t * 18.0)) * exp(-_nibble_t * 7.0)
			_float.global_position = _surface() + Vector3(0, bob, 0)
			spot.pull = clampf(done, 0.0, 1.0)
			if done >= 1.0:
				done = 1.0
				state = "bite"
				_t = 0.0
				_window = window_override if window_override > 0.0 else Fishing.bite_window(spot.row, Inventory.held.rod)
				spot.bite()
				_play("fish_splash", _surface(), 0.8)
				ToolFx.burst(get_tree().current_scene, _surface(), SPLASH, 8, 1.8, 0.04)
			Fishing.progress[key] = done
			if state == "wait":
				var text := "Something's nibbling…" if _nibbles > 0 else "Fishing %s  %d%%" % [label, int(done * 100.0)]
				_set_prompt("", text + got, "E", "Reel in")
		"bite":
			_float.global_position = _surface() + Vector3(randf_range(-0.02, 0.02), -0.09, randf_range(-0.02, 0.02))
			_set_prompt("E", "A bite! Reel it in!" + got)
			if _t >= _window:
				Fishing.progress[key] = Fishing.MISS_KEEP
				Inventory.message.emit("The %s got away. It'll be back: reel in when the float dips." % label.to_lower())
				state = "wait"
				_t = 0.0
				_nibbles = 0
				spot.pull = Fishing.MISS_KEEP
	_draw_line()


## Inside the bite window: the fish comes out with a splash, then the Imp casts again.
func _land() -> void:
	var row: Dictionary = spot.row
	Fishing.give(row)
	caught += 1
	Fishing.progress[String(spot.name)] = 0.0
	spot.pull = 0.0
	_play("fish_splash", _surface(), 1.1)
	ToolFx.burst(get_tree().current_scene, _surface() + Vector3.UP * 0.1, SPLASH, 18, 2.6, 0.05)
	var why := Fishing.blocker(row, Inventory.held.rod)
	if why != "":
		Inventory.message.emit(why)
		stop()
		return
	_cast(_float.global_position)


## The cast line: from the rod tip to the float, sagging while it waits, tight on a bite.
func _draw_line() -> void:
	var mesh := _line.mesh as ImmediateMesh
	mesh.clear_surfaces()
	if not _float.visible:
		return
	var a := _tip()
	var b := _float.global_position
	var sag := 0.0 if state == "bite" or (state == "cast" and _t < CAST_RELEASE) else minf(0.35, a.distance_to(b) * 0.08)
	mesh.surface_begin(Mesh.PRIMITIVE_LINE_STRIP)
	for i in 13:
		var u := i / 12.0
		mesh.surface_add_vertex(a.lerp(b, u) + Vector3.DOWN * sag * 4.0 * u * (1.0 - u))
	mesh.surface_end()


func _play(sound: String, at: Vector3, pitch := 1.0) -> void:
	if not _sounds.has(sound):
		return
	_audio.global_position = at
	_audio.stream = _sounds[sound]
	_audio.pitch_scale = pitch * randf_range(0.94, 1.06)
	_audio.play()


func _look_for_spot() -> void:
	target = null
	if not player.frozen and not player.menu_open():
		var best := INF
		var me := player.global_position
		for s: Node3D in get_tree().get_nodes_in_group("fish_spot"):
			var o := s.global_position
			if absf(o.x - me.x) > 8.0 or absf(o.z - me.z) > 8.0 or me.y < o.y - 0.4 or me.y > o.y + 4.0:
				continue
			var d := Vector2(me.x - o.x, me.z - o.z).length()
			if d < Fishing.REACH and d < best:
				best = d
				target = s
	if target == null:
		_set_prompt("", "")
		return
	var label: String = target.label()
	if Inventory.in_hand != "rod":
		_set_prompt("", "%s here: take out a rod (5) to fish" % label)
		return
	var why := Fishing.blocker(target.row, Inventory.held.rod)
	if why != "":
		_set_prompt("", why)
		return
	var t := time_override if time_override > 0.0 else Fishing.catch_time(target.row, Inventory.held.rod)
	var left := maxi(1, int(ceil(t * (1.0 - float(Fishing.progress.get(String(target.name), 0.0))))))
	_set_prompt("E", "Fish for %s  (%ds)" % [label, left])


func _set_prompt(key: String, text: String, key2 := "", text2 := "") -> void:
	var p := [key, text, key2, text2]
	if p == _prompt:
		return
	_prompt = p
	var hud := get_tree().get_first_node_in_group("hud")
	if hud:
		hud.set_prompt(key, text, key2, text2)
