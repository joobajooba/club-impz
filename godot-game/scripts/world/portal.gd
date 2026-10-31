extends Node3D
## Portal placeholder: a glowing ring with an Area3D. Walking in fades to black, changes world and places the
## player at the target spawn point (game_worlds.md section 5).

@export var target_world := "resource"
@export var target_spawn := "spawn_point"
@export var ring_color := Color("#8a5cff")

var armed := false


func _ready() -> void:
	var ring := MeshInstance3D.new()
	ring.name = "ring"
	var torus := TorusMesh.new()
	torus.inner_radius = 1.55
	torus.outer_radius = 1.95
	torus.rings = 24
	torus.ring_segments = 8
	var mat := StandardMaterial3D.new()
	mat.albedo_color = ring_color
	mat.emission_enabled = true
	mat.emission = ring_color
	mat.emission_energy_multiplier = 1.6
	torus.material = mat
	ring.mesh = torus
	ring.rotation_degrees = Vector3(90, 0, 0)
	ring.position = Vector3(0, 2.05, 0)
	add_child(ring)
	var disc := MeshInstance3D.new()
	disc.name = "disc"
	var cyl := CylinderMesh.new()
	cyl.top_radius = 1.6
	cyl.bottom_radius = 1.6
	cyl.height = 0.05
	var dmat := StandardMaterial3D.new()
	dmat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	dmat.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
	dmat.albedo_color = Color(ring_color.r * 0.6 + 0.3, ring_color.g * 0.6 + 0.3, ring_color.b * 0.6 + 0.4, 0.55)
	cyl.material = dmat
	disc.mesh = cyl
	disc.rotation_degrees = Vector3(90, 0, 0)
	disc.position = Vector3(0, 2.05, 0)
	add_child(disc)
	for side in [-1.0, 1.0]:
		var base := MeshInstance3D.new()
		var b := BoxMesh.new()
		b.size = Vector3(0.7, 0.7, 0.9)
		var bm := StandardMaterial3D.new()
		bm.albedo_color = Color("#8a8480")
		b.material = bm
		base.mesh = b
		base.position = Vector3(side * 1.75, 0.3, 0)
		add_child(base)
	var sparks := CPUParticles3D.new()
	sparks.amount = 40
	sparks.lifetime = 2.0
	sparks.emission_shape = CPUParticles3D.EMISSION_SHAPE_RING
	sparks.emission_ring_axis = Vector3(0, 0, 1)
	sparks.emission_ring_radius = 1.75
	sparks.emission_ring_inner_radius = 1.5
	sparks.emission_ring_height = 0.1
	sparks.gravity = Vector3(0, 0.6, 0)
	sparks.position = Vector3(0, 2.05, 0)
	var q := QuadMesh.new()
	q.size = Vector2(0.09, 0.09)
	var qm := StandardMaterial3D.new()
	qm.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	qm.billboard_mode = BaseMaterial3D.BILLBOARD_ENABLED
	qm.albedo_color = ring_color.lightened(0.5)
	q.material = qm
	sparks.mesh = q
	add_child(sparks)
	var area := Area3D.new()
	area.name = "trigger"
	area.collision_layer = 8
	area.collision_mask = 2
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = Vector3(3.0, 3.6, 1.2)
	cs.shape = shape
	cs.position = Vector3(0, 1.8, 0)
	area.add_child(cs)
	add_child(area)
	area.body_entered.connect(_on_body_entered)
	# don't fire for a player who arrives standing in it
	await get_tree().create_timer(1.5).timeout
	armed = true


func _on_body_entered(body: Node) -> void:
	if not armed or not body is CharacterBody3D:
		return
	var main := get_tree().get_first_node_in_group("game_main")
	if main:
		main.change_world(target_world, target_spawn)
