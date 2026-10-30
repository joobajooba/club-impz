class_name BiomeEnvironment
extends Node3D
## One environment preset per biome (game_worlds.md section 4.8 Sky and light / Fog rows, values in
## data/biomes.json). Fades the WorldEnvironment and the sun to a new biome over a few seconds.
## Depth fog only (no volumetric fog in web builds). One ambient CPUParticles3D emitter per biome follows the
## player, and an empty AudioStreamPlayer per biome is the hook for ambient sound.

@export var fade_time := 3.0

var biome_data: Dictionary
var env: Environment
var sky_mat: ProceduralSkyMaterial
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
	sky_mat = ProceduralSkyMaterial.new()
	sky_mat.sky_curve = 0.12
	sky_mat.ground_curve = 0.05
	sky_mat.sun_angle_max = 20.0
	var sky := Sky.new()
	sky.sky_material = sky_mat
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
	sun.directional_shadow_mode = DirectionalLight3D.SHADOW_PARALLEL_2_SPLITS
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
	sky_mat.sky_top_color = v["sky_top"]
	sky_mat.sky_horizon_color = v["sky_horizon"]
	sky_mat.ground_horizon_color = v["sky_horizon"]
	sky_mat.ground_bottom_color = v["ground"]
	sun.light_color = v["sun"]
	sun.light_energy = v["sun_energy"]
	sun.rotation_degrees = Vector3(v["sun_pitch"], v["sun_yaw"], 0)
	env.ambient_light_color = v["ambient"]
	env.ambient_light_energy = v["ambient_energy"]
	env.fog_light_color = v["fog"]
	env.fog_density = v["fog_density"]
	env.fog_sky_affect = v["fog_sky_affect"]


func _process(delta: float) -> void:
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
