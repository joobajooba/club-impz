class_name MeshMerge
extends RefCounted
## Merges a placeholder's many box / cylinder MeshInstance3D children into one mesh with vertex colours
## (plus one for emissive parts), so each placeholder costs one or two draw calls instead of dozens.


static func merge_children(root: Node3D, visibility_end := 0.0) -> void:
	var plain := SurfaceTool.new()
	var glow := SurfaceTool.new()
	plain.begin(Mesh.PRIMITIVE_TRIANGLES)
	glow.begin(Mesh.PRIMITIVE_TRIANGLES)
	var has := [false, false]
	var glow_col := Color.WHITE
	var to_free: Array[Node] = []
	for mi in root.find_children("*", "MeshInstance3D", true, false):
		var m := mi as MeshInstance3D
		if not m.visible or not (m.mesh is PrimitiveMesh):
			if not m.visible:
				to_free.append(m)
			continue
		var mat := (m.mesh as PrimitiveMesh).material as StandardMaterial3D
		var col := mat.albedo_color if mat else Color.WHITE
		var emissive := mat != null and mat.emission_enabled
		var xf := _local_xf(root, m)
		if emissive:
			glow_col = col
		var arrays: Array = m.mesh.get_mesh_arrays()
		var st := glow if emissive else plain
		has[1 if emissive else 0] = true
		var verts: PackedVector3Array = arrays[Mesh.ARRAY_VERTEX]
		var norms: PackedVector3Array = arrays[Mesh.ARRAY_NORMAL]
		var idx: PackedInt32Array = arrays[Mesh.ARRAY_INDEX]
		var basis := xf.basis.inverse().transposed()
		for i in idx:
			st.set_color(col)
			st.set_normal((basis * norms[i]).normalized())
			st.add_vertex(xf * verts[i])
		to_free.append(m)
	for k in 2:
		if not has[k]:
			continue
		var mat := StandardMaterial3D.new()
		mat.vertex_color_use_as_albedo = true
		mat.roughness = 0.95
		if k == 1:
			mat.emission_enabled = true
			mat.emission_energy_multiplier = 2.0
			mat.emission = glow_col
		var st := plain if k == 0 else glow
		st.set_material(mat)
		var out := MeshInstance3D.new()
		out.name = "merged_glow" if k == 1 else "merged"
		out.mesh = st.commit()
		if visibility_end > 0.0:
			out.visibility_range_end = visibility_end
		root.add_child(out)
	for n in to_free:
		n.queue_free()


static func _local_xf(root: Node3D, n: Node3D) -> Transform3D:
	var xf := n.transform
	var p := n.get_parent()
	while p != null and p != root:
		xf = (p as Node3D).transform * xf
		p = p.get_parent()
	return xf
