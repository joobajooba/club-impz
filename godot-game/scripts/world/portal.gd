extends Node3D
## World portal (game_worlds.md section 5): the obsidian arch model (assets/models/props/portal.glb, built by
## `build scripts/build_portal.py`) with its looping `idle` animation of red swirls, plus an Area3D in the opening.
## Walking in fades to black, changes world and places the player at the target spawn point.

const MODEL := "res://assets/models/props/portal.glb"
const GLOW_ENERGY := 0.15         # the swirls, runes, gem and embers (cubes named *_glow)
const BACKDROP_ENERGY := 0.05    # the solid surface behind the swirls (stronger washes it out to white)
const OPENING := Vector3(3.0, 2.6, 1.2)   # trigger box in metres: the arch opening is 3.25 wide, 2.75 tall
const BASE_TOP := 0.25            # the stepped base is 4 units (0.25 m) tall

@export var target_world := "resource"
@export var target_spawn := "spawn_point"

var armed := false
var _anim: AnimationPlayer


func _ready() -> void:
	var model := (load(MODEL) as PackedScene).instantiate() as Node3D
	model.name = "model"
	add_child(model)
	_set_materials(model)
	var found := model.find_children("*", "AnimationPlayer", true, false)
	if not found.is_empty():
		_anim = found[0] as AnimationPlayer
		if _anim.has_animation("idle"):
			_anim.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
			_anim.play("idle")
	_add_pillar_colliders()
	var area := Area3D.new()
	area.name = "trigger"
	area.collision_layer = 8
	area.collision_mask = 2
	var cs := CollisionShape3D.new()
	var shape := BoxShape3D.new()
	shape.size = OPENING
	cs.shape = shape
	cs.position = Vector3(0, BASE_TOP + OPENING.y / 2.0, 0)
	area.add_child(cs)
	add_child(area)
	area.body_entered.connect(_on_body_entered)
	# don't fire for a player who arrives standing in it
	await get_tree().create_timer(1.5).timeout
	armed = true


## Hard alpha everywhere (the swirls, runes and shards are alpha cards, seen from both sides); parts named *_glow
## are emissive from their own texture, so the portal lights up at dusk.
func _set_materials(model: Node) -> void:
	var cache := {}
	for mi: MeshInstance3D in model.find_children("*", "MeshInstance3D", true, false):
		var glow := _is_glow(mi, model)
		var backdrop := _has_ancestor_named(mi, model, "portal_backdrop")
		for si in mi.mesh.get_surface_count():
			var src := mi.get_active_material(si) as BaseMaterial3D
			if src == null:
				continue
			var key := [src, glow, backdrop]
			if not cache.has(key):
				var m := src.duplicate() as BaseMaterial3D
				m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA_SCISSOR
				m.alpha_scissor_threshold = 0.5
				m.cull_mode = BaseMaterial3D.CULL_DISABLED
				if glow:
					m.emission_enabled = true
					m.emission_texture = m.albedo_texture
					m.emission = Color.WHITE
					m.emission_energy_multiplier = BACKDROP_ENERGY if backdrop else GLOW_ENERGY
				cache[key] = m
			mi.set_surface_override_material(si, cache[key])


static func _has_ancestor_named(n: Node, root: Node, prefix: String) -> bool:
	while n != null and n != root:
		if String(n.name).begins_with(prefix):
			return true
		n = n.get_parent()
	return false


static func _is_glow(n: Node, root: Node) -> bool:
	while n != null and n != root:
		if String(n.name).ends_with("_glow"):
			return true
		n = n.get_parent()
	return false


## Solid pillars either side of the opening (the arch is overhead, the base is low enough to walk onto).
func _add_pillar_colliders() -> void:
	var body := StaticBody3D.new()
	body.name = "pillars"
	body.collision_layer = 4
	body.collision_mask = 0
	for side in [-1.0, 1.0]:
		var cs := CollisionShape3D.new()
		var box := BoxShape3D.new()
		box.size = Vector3(0.6, 3.4, 0.8)
		cs.shape = box
		cs.position = Vector3(side * (1.625 + 0.3), 1.7, 0)
		body.add_child(cs)
	add_child(body)


func _on_body_entered(body: Node) -> void:
	if not armed or not body is CharacterBody3D:
		return
	var main := get_tree().get_first_node_in_group("game_main")
	if main:
		main.change_world(target_world, target_spawn)
