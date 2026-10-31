class_name BiomeEnvironment
extends Node3D
## One environment preset per biome (game_worlds.md section 4.8 Sky and light / Fog rows, values in
## data/biomes.json). Fades the WorldEnvironment and the sun to a new biome over a few seconds.
## Depth fog only (no volumetric fog in web builds). One ambient CPUParticles3D emitter per biome follows the
## player, and an empty AudioStreamPlayer per biome is the hook for ambient sound.

@export var fade_time := 3.0

var biome_data: Dictionary
var env: Environment
var sky_mat: ShaderMaterial
## Day and night: 30 minutes of day, then 30 of night, fading over the last 60 s of each half.
## Key 5 (toggle_day_night) flips straight away with a 2 s fade and restarts the timer.
const HALF_CYCLE := 1800.0
const AUTO_FADE := 60.0
const MOON_COLOR := Color("#9fb4ff")
var night := 0.0
var is_night := false
var cycle_t := 0.0
var night_from := 0.0
var night_to := 0.0
var night_t := 1.0
var night_len := AUTO_FADE
var auto_fading := false
var cur := {}
var sun: DirectionalLight3D
var player: Node3D
var current := ""
var from := {}
var to := {}
var t := 1.0
var emitters := {}
var sounds := {}


func setup(d: Dictionary, start_biome: String) -> void:
	biome_data = d
	if "--night" in OS.get_cmdline_user_args():  # debug: start at night
		night = 1.0
		is_night = true
	sky_mat = ShaderMaterial.new()
	sky_mat.shader = load("res://shaders/sky_day_night.gdshader")
	var sky := Sky.new()
	sky.sky_material = sky_mat
	sky.radiance_size = Sky.RADIANCE_SIZE_32  # the sky animates, keep its radiance update cheap
	sky.process_mode = Sky.PROCESS_MODE_INCREMENTAL
	env = Environment.new()
	env.background_mode = Environment.BG_SKY
	env.sky = sky
	env.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.tonemap_mode = Environment.TONE_MAPPER_LINEAR
	env.fog_enabled = true
	env.fog_mode = Environment.FOG_MODE_EXPONENTIAL
	env.glow_enabled = false
	var we := WorldEnvironment.new()
	we.name = "world_environment"
	we.environment = env
	add_child(we)
	sun = DirectionalLight3D.new()
	sun.name = "sun"
	sun.shadow_enabled = true
	sun.directional_shadow_max_distance = 70.0
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_ORTHOGONAL  # one shadow pass for the web build
	add_child(sun)
	for b in biome_data["biomes"]:
		var e := _make_emitter(b, biome_data["biomes"][b].get("particles", ""))
		if e:
			emitters[b] = e
		var s := AudioStreamPlayer.new()
		s.name = "ambient_%s" % b       # hook: assign an ambient loop here later
		add_child(s)
		sounds[b] = s
	set_biome(start_biome, true)


func set_player(p: Node3D) -> void:
	player = p


func set_biome(b: String, instant := false) -> void:
	if b == current or not biome_data["biomes"].has(b):
		return
	current = b
	from = _snapshot()
	to = _preset(biome_data["biomes"][b]["env"])
	t = 1.0 if instant else 0.0
	if instant:
		_apply(to)
	for k in emitters:
		emitters[k].emitting = k == b


func _preset(e: Dictionary) -> Dictionary:
	return {
		"sky_top": Color(e["sky_top"]), "sky_horizon": Color(e["sky_horizon"]), "ground": Color(e["ground"]),
		"sun": Color(e["sun"]), "sun_energy": float(e["sun_energy"]), "sun_pitch": float(e["sun_pitch"]), "sun_yaw": float(e["sun_yaw"]),
		"ambient": Color(e["ambient"]), "ambient_energy": float(e["ambient_energy"]), "fog": Color(e["fog"]),
		"fog_density": float(e["fog_density"]), "fog_sky_affect": float(e["fog_sky_affect"]),
	}


func _snapshot() -> Dictionary:
	if to.is_empty():
		return _preset(biome_data["biomes"].values()[0]["env"])
	var cur := {}
	for k in to:
		cur[k] = _lerp_val(from.get(k, to[k]), to[k], clampf(t, 0.0, 1.0))
	return cur


func _lerp_val(a, b, f: float):
	if a is Color:
		return (a as Color).lerp(b, f)
	return lerpf(a, b, f)


func _apply(v: Dictionary) -> void:
	## Biome preset v, with the night blended on top (so biome fades and day/night mix freely).
	cur = v
	var n := smoothstep(0.0, 1.0, night)
	var sun_rot := Vector3(v["sun_pitch"], v["sun_yaw"], 0)
	var moon_rot := Vector3(v["sun_pitch"], v["sun_yaw"] + 180.0, 0)  # the moon sits opposite the sun
	sky_mat.set_shader_parameter("sky_top", v["sky_top"])
	sky_mat.set_shader_parameter("sky_horizon", v["sky_horizon"])
	sky_mat.set_shader_parameter("ground", v["ground"])
	sky_mat.set_shader_parameter("sun_color", v["sun"])
	sky_mat.set_shader_parameter("sun_dir", _to_body(sun_rot))
	sky_mat.set_shader_parameter("moon_dir", _to_body(moon_rot))
	sky_mat.set_shader_parameter("night", n)
	# one DirectionalLight3D (one shadow pass): sunlight by day, moonlight by night
	sun.light_color = (v["sun"] as Color).lerp(MOON_COLOR, n)
	sun.light_energy = lerpf(v["sun_energy"], 0.18, n)
	sun.rotation_degrees = sun_rot if n < 0.5 else moon_rot
	env.ambient_light_color = v["ambient"]
	env.ambient_light_energy = v["ambient_energy"] * lerpf(1.0, 0.45, n)
	env.fog_light_color = (v["fog"] as Color).lerp(Color("#141c33"), 0.75 * n)
	env.fog_density = v["fog_density"]
	env.fog_sky_affect = v["fog_sky_affect"]


func _to_body(rot_deg: Vector3) -> Vector3:
	## direction from the camera towards the light's sun or moon (the light shines along its -Z)
	return Basis.from_euler(rot_deg * PI / 180.0).z


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_day_night"):
		is_night = not is_night
		cycle_t = 0.0
		auto_fading = false
		_start_night_fade(1.0 if is_night else 0.0, 2.0)


func _start_night_fade(target: float, length: float) -> void:
	night_from = night
	night_to = target
	night_len = length
	night_t = 0.0


func _update_day_night(delta: float) -> bool:
	## advances the cycle; true when the night amount changed this frame
	cycle_t += delta
	if not auto_fading and cycle_t >= HALF_CYCLE - AUTO_FADE:
		auto_fading = true
		_start_night_fade(0.0 if is_night else 1.0, AUTO_FADE)
	if cycle_t >= HALF_CYCLE:
		is_night = not is_night
		cycle_t = 0.0
		auto_fading = false
	if night_t >= 1.0:
		return false
	night_t = minf(1.0, night_t + delta / night_len)
	night = lerpf(night_from, night_to, night_t)
	return true


func _process(delta: float) -> void:
	var night_changed := _update_day_night(delta)
	if t >= 1.0 and night_changed and not cur.is_empty():
		_apply(cur)
	if t < 1.0:
		t = minf(1.0, t + delta / fade_time)
		var f := smoothstep(0.0, 1.0, t)
		var v := {}
		for k in to:
			v[k] = _lerp_val(from[k], to[k], f)
		_apply(v)
	if player:
		for k in emitters:
			emitters[k].global_position = player.global_position + Vector3(0, 4, 0)


func _make_emitter(b: String, kind: String) -> CPUParticles3D:
	if kind == "":
		return null
	var p := CPUParticles3D.new()
	p.name = "particles_%s" % b
	p.emitting = false
	p.local_coords = false
	p.emission_shape = CPUParticles3D.EMISSION_SHAPE_BOX
	var quad := QuadMesh.new()
	quad.size = Vector2(0.08, 0.08)
	var mat := StandardMaterial3D.new()
	mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	mat.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	mat.vertex_color_use_as_albedo = true
	mat.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	quad.material = mat
	p.mesh = quad
	match kind:
		"pollen":   # floating pollen and dandelion seeds
			p.amount = 90; p.lifetime = 9.0; p.emission_box_extents = Vector3(22, 5, 22)
			p.gravity = Vector3(0.05, 0.04, 0.02); p.initial_velocity_min = 0.05; p.initial_velocity_max = 0.25
			p.direction = Vector3(1, 0.3, 0.2); p.spread = 60.0; p.color = Color("#fff4c0")
		"mist_leaves":  # falling maple leaves drifting in the wind
			p.amount = 60; p.lifetime = 7.0; p.emission_box_extents = Vector3(20, 3, 20)
			p.gravity = Vector3(0.6, -0.7, 0.2); p.initial_velocity_max = 0.4; p.color = Color("#e8763a")
			quad.size = Vector2(0.14, 0.1)
		"snow":
			p.amount = 420; p.lifetime = 6.0; p.emission_box_extents = Vector3(24, 4, 24)
			p.gravity = Vector3(0.3, -1.6, 0.1); p.initial_velocity_max = 0.3; p.color = Color("#f4f8ff")
			p.position = Vector3(0, 6, 0)
		"dust":     # dust and grass seeds blowing in the wind
			p.amount = 140; p.lifetime = 6.0; p.emission_box_extents = Vector3(24, 3, 24)
			p.gravity = Vector3(1.6, -0.05, 0.2); p.initial_velocity_min = 0.5; p.initial_velocity_max = 1.4
			p.direction = Vector3(1, 0, 0); p.color = Color("#e8d8a0")
		"fireflies":
			p.amount = 70; p.lifetime = 8.0; p.emission_box_extents = Vector3(18, 3, 18)
			p.gravity = Vector3.ZERO; p.initial_velocity_min = 0.1; p.initial_velocity_max = 0.35; p.spread = 180.0
			p.color = Color("#d8ff6a"); quad.size = Vector2(0.1, 0.1)
	add_child(p)
	return p
