extends Node3D
## Test scene: every converted model in a row next to the spawn point, to check scale against the imp.

const GROUPS := ["foliage", "trees", "mobs"]


func _ready() -> void:
	var x := -6.0
	for g in GROUPS:
		var dir := DirAccess.open("res://assets/models/%s" % g)
		if dir == null:
			continue
		for f in dir.get_files():
			if not f.ends_with(".glb"):
				continue
			var scene: PackedScene = load("res://assets/models/%s/%s" % [g, f])
			var inst := scene.instantiate() as Node3D
			add_child(inst)
			var aabb := _aabb(inst)
			x += aabb.size.x * 0.5 + 0.6
			inst.position = Vector3(x, 0, -6)
			x += aabb.size.x * 0.5


func _aabb(n: Node) -> AABB:
	var box := AABB()
	for c in n.find_children("*", "MeshInstance3D", true, false):
		box = box.merge((c as MeshInstance3D).get_aabb())
	return box
