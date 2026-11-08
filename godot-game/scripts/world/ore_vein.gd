extends Node3D
## An ore vein in the resource world: the Blockbench model assets/models/ores/<ore>_vein.glb
## (blockbench_detailed_prompts.md section 3.2). Placed by resource_landmarks.gd.
##
## A vein is about 55 to 80 cubes, and the glb has one mesh per cube, so each ore's cubes are merged once
## into two meshes (cached for every vein of that ore): the stone and ore, and the parts whose names end
## in `_glow` (dreadstone fissures, void and stellarite crystals, star sparkles), which get an emissive
## copy of the material. One or two draw calls per vein, hidden past VIEW metres like the old placeholders.
## A box round the stone mound blocks the player (layer 4, like trees and the placeholders).

@export_enum("coal", "tin", "copper", "iron", "gold", "obsidian", "titanite", "dreadstone", "void", "stellarite") var ore := "coal"

const PATH := "res://assets/models/ores/%s_vein.glb"
const VIEW := 140.0
const GLOW_ENERGY := 0.55

static var _merged := {}          # ore -> {plain: ArrayMesh, glow: ArrayMesh or null, aabb: AABB}


func _ready() -> void:
	var m := _meshes(ore)
	for key in ["plain", "glow"]:
		if m[key] == null:
			continue
		var mi := MeshInstance3D.new()
		mi.name = key
		mi.mesh = m[key]
		mi.visibility_range_end = VIEW
		add_child(mi)
	var box: AABB = m.aabb
	var body := StaticBody3D.new()
	body.collision_layer = 4
	body.collision_mask = 0
	var cs := CollisionShape3D.new()
	var sh := BoxShape3D.new()
	# the stone mound, not the loose fragments round it or the tips of the crystals
	sh.size = Vector3(box.size.x * 0.62, box.size.y * 0.55, box.size.z * 0.62)
	cs.shape = sh
	cs.position = Vector3(box.get_center().x, sh.size.y / 2.0, box.get_center().z)
	body.add_child(cs)
	add_child(body)


## Metres from the vein's centre to the side of its stone mound (where a pickaxe lands), and the centre.
func mound_radius() -> float:
	var box: AABB = _meshes(ore).aabb
	return maxf(box.size.x, box.size.z) * 0.31 * global_basis.get_scale().x


func centre() -> Vector3:
	var box: AABB = _meshes(ore).aabb
	return global_transform * Vector3(box.get_center().x, 0.0, box.get_center().z)


static func _meshes(id: String) -> Dictionary:
	if _merged.has(id):
		return _merged[id]
	var scene := (load(PATH % id) as PackedScene).instantiate() as Node3D
	var tools := {"plain": null, "glow": null}
	var mats := {"plain": null, "glow": null}
	var aabb := AABB()
	var first := true
	for mi: MeshInstance3D in scene.find_children("*", "MeshInstance3D", true, false):
		var key := "glow" if _is_glow(mi, scene) else "plain"
		var xf := _local_xf(scene, mi)
		for si in mi.mesh.get_surface_count():
			if tools[key] == null:
				tools[key] = SurfaceTool.new()
				(tools[key] as SurfaceTool).begin(Mesh.PRIMITIVE_TRIANGLES)
				mats[key] = mi.get_active_material(si)
			(tools[key] as SurfaceTool).append_from(mi.mesh, si, xf)
		if key == "plain":
			var b := xf * mi.mesh.get_aabb()
			aabb = b if first else aabb.merge(b)
			first = false
	var out := {"plain": null, "glow": null, "aabb": aabb}
	for key in ["plain", "glow"]:
		if tools[key] == null:
			continue
		var mat := mats[key] as BaseMaterial3D
		if mat and key == "glow":
			mat = mat.duplicate() as BaseMaterial3D
			mat.emission_enabled = true
			mat.emission_texture = mat.albedo_texture
			mat.emission = Color.WHITE
			mat.emission_energy_multiplier = GLOW_ENERGY
		var st := tools[key] as SurfaceTool
		st.set_material(mat)
		out[key] = st.commit()
	scene.free()
	_merged[id] = out
	return out


static func _is_glow(n: Node, root: Node) -> bool:
	while n != null and n != root:
		if String(n.name).ends_with("_glow"):
			return true
		n = n.get_parent()
	return false


static func _local_xf(root: Node3D, n: Node3D) -> Transform3D:
	var xf := n.transform
	var p := n.get_parent()
	while p != null and p != root:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf
