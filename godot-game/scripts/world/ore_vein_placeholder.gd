extends Node3D
## Ore node placeholder (no ore models yet): a lumpy grey rock of a few boxes with chunky crystals in the ore
## colour from blockbench_detailed_prompts.md section 3.2. Replace with <ore>_vein.glb when it exists.

@export_enum("coal", "tin", "copper", "iron", "gold", "obsidian", "titanite", "dreadstone") var ore := "coal"

const RAMPS := {
	"coal": ["#1a1a22", "#4a4e5c"], "tin": ["#5c6268", "#d6dbe0"], "copper": ["#5a2410", "#f28c52"],
	"iron": ["#3e1c14", "#c47a5a"], "gold": ["#6b4100", "#ffe27a"], "obsidian": ["#0d0814", "#6a4c9c"],
	"titanite": ["#1e3248", "#a8d4f0"], "dreadstone": ["#1c0608", "#b0242c"],
}
const STONE := [Color("#5e626c"), Color("#6e727c"), Color("#7e828c")]


func _ready() -> void:
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(ore) + int(global_position.x * 13.0 + global_position.z * 7.0)
	var body := StaticBody3D.new()
	body.collision_layer = 4
	add_child(body)
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	sh.size = Vector3(1.6, 1.0, 1.4)
	cs.shape = sh
	cs.position = Vector3(0, 0.5, 0)
	body.add_child(cs)
	for i in 6:  # lumpy stone core
		var s := Vector3(rng.randf_range(0.5, 0.9), rng.randf_range(0.35, 0.8), rng.randf_range(0.5, 0.9))
		_part(s, Vector3(rng.randf_range(-0.5, 0.5), 0.0 if i < 4 else 0.4, rng.randf_range(-0.45, 0.45)), STONE[i % 3], Vector3(0, rng.randf() * PI, 0))
	var dark := Color(RAMPS[ore][0])
	var light := Color(RAMPS[ore][1])
	var glow := 0.6 if ore in ["gold", "titanite", "dreadstone"] else 0.0
	for i in 5:  # crystals at angles, biggest on top
		var big := i == 0
		var s := Vector3(0.28, 0.6, 0.28) * (1.5 if big else rng.randf_range(0.8, 1.15))
		var col := dark.lerp(light, 0.55 + 0.35 * rng.randf())
		_part(s, Vector3(rng.randf_range(-0.45, 0.45), 0.6 if big else rng.randf_range(0.2, 0.55), rng.randf_range(-0.4, 0.4)), col,
			Vector3(rng.randf_range(-0.6, 0.6), rng.randf() * PI, rng.randf_range(-0.6, 0.6)), glow)
	MeshMerge.merge_children(self, 120.0)  # one draw call per node, hidden past 120 m


func _part(size: Vector3, pos: Vector3, col: Color, rot: Vector3, emissive := 0.0) -> void:
	var mi := MeshInstance3D.new()
	var m := BoxMesh.new()
	m.size = size
	var mat := StandardMaterial3D.new()
	mat.albedo_color = col
	mat.roughness = 0.6 if emissive > 0.0 else 0.95
	if emissive > 0.0:
		mat.emission_enabled = true
		mat.emission = col
		mat.emission_energy_multiplier = emissive
	m.material = mat
	mi.mesh = m
	mi.position = pos + Vector3(0, size.y * 0.4, 0)
	mi.rotation = rot
	add_child(mi)
