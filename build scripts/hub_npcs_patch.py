"""Adds the hub NPCs to hub_town.gd: each one from data/hub_npcs.json, at its npc spot, idle looping, with a collider."""
from pathlib import Path
p = Path(__file__).resolve().parent.parent / 'godot-game/scripts/world/hub_town.gd'
s = p.read_text(encoding='utf8')


def rep(a, b):
    global s
    assert s.count(a) == 1, a[:60]
    s = s.replace(a, b)


rep('''const PLAN := "res://data/hub_town.json"''', '''const PLAN := "res://data/hub_town.json"
const NPCS := "res://data/hub_npcs.json"   # the NPCs at the stores (J00BA, 2026-11-14)''')
rep('''##   - Marker3D nodes under npc_spots/ where vendor and crafter NPCs can stand (meta "role")''',
    '''##   - Marker3D nodes under npc_spots/ where vendor and crafter NPCs can stand (meta "role"), and the NPCs of
##     data/hub_npcs.json standing on them, idle looping''')
rep('''	_make_npc_spots(plan["npc_spots"])
''', '''	_make_npc_spots(plan["npc_spots"])
	_place_npcs(plan["npc_spots"])
''')
rep('''## A model with a Blockbench animation:''', '''## The store NPCs: each glb at its spot (offset in the spot's frame), with the hub's hard-alpha materials, *_glow parts
## emissive, "idle" looping, and a body-sized collider so players walk round them.
func _place_npcs(spots: Array) -> void:
	var by_name := {}
	for s in spots:
		by_name[s["name"]] = s
	var data: Dictionary = JSON.parse_string(FileAccess.get_file_as_string(NPCS))
	var root := Node3D.new()
	root.name = "npcs"
	add_child(root)
	var body := StaticBody3D.new()
	body.name = "npc_colliders"
	body.collision_layer = 4
	body.collision_mask = 0
	root.add_child(body)
	for n in data["npcs"]:
		if not by_name.has(n["spot"]) or not ResourceLoader.exists(n["model"]):
			push_warning("hub npc skipped: %s at %s" % [n["model"], n["spot"]])
			continue
		var spot: Dictionary = by_name[n["spot"]]
		var yaw := deg_to_rad(float(spot["yaw"]))
		var off := Vector3(n["offset"][0], 0, n["offset"][1]).rotated(Vector3.UP, yaw)
		var x: float = spot["pos"][0] + off.x
		var z: float = spot["pos"][2] + off.z
		var inst := (load(n["model"]) as PackedScene).instantiate() as Node3D
		inst.name = String(n["model"]).get_file().get_basename()
		root.add_child(inst)
		inst.transform = Transform3D(Basis(Vector3.UP, yaw + deg_to_rad(float(n["turn"]))).scaled(Vector3.ONE * float(n["scale"])),
			Vector3(x, world.ground_height(x, z), z))
		var cache := {}
		for mi: MeshInstance3D in inst.find_children("*", "MeshInstance3D", true, false):
			var glow := _is_glow(mi, inst)
			for si in mi.mesh.get_surface_count():
				var src := mi.get_active_material(si) as BaseMaterial3D
				if src == null:
					continue
				var key := [src.albedo_texture, glow]
				if not cache.has(key):
					cache[key] = _material(src.albedo_texture, glow)
				mi.set_surface_override_material(si, cache[key])
		var players := inst.find_children("*", "AnimationPlayer", true, false)
		if not players.is_empty():
			var ap := players[0] as AnimationPlayer
			if ap.has_animation("idle"):
				ap.get_animation("idle").loop_mode = Animation.LOOP_LINEAR
				ap.play("idle")
				ap.seek(randf() * ap.current_animation_length, true)   # not all breathing in step
		var cs := CollisionShape3D.new()
		var cap := CapsuleShape3D.new()
		cap.radius = 0.4
		cap.height = 1.6
		cs.shape = cap
		cs.position = Vector3(x, world.ground_height(x, z) + 0.8, z)
		body.add_child(cs)


## A model with a Blockbench animation:''')
p.write_text(s, encoding='utf8', newline='\n')
print('hub_town.gd patched')
