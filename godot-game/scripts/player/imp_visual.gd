extends Node3D
## Placeholder base imp (blockbench_detailed_prompts.md section 1.2): big cube head, giant dark eyes with
## light highlight pixels, pointy ears sticking out sideways, a small leafy tuft, a short green body and
## stubby limbs. 18 Blockbench units tall (1.125 m). Faces -z. Replace this node with the real imp model later.

const U := 1.0 / 16.0  # one Blockbench unit in metres
# imp green skin ramp (blockbench_detailed_prompts.md section 5)
const SKIN := [Color("#1e3a2a"), Color("#2c523a"), Color("#3e6c4a"), Color("#548a5c"), Color("#6ea672"), Color("#90c08c")]
const EYE := Color("#14141c")
const EYE_HI := Color("#e8ecf0")
const LEAF := [Color("#2e481a"), Color("#5c7e28"), Color("#7a9a34")]


func _ready() -> void:
	var body_root := Node3D.new()
	body_root.name = "body_root"
	add_child(body_root)
	# legs (3 units), body (5 units), head (9 units), tuft on top (1 unit) = 18 units
	_box(body_root, "leg_left", Vector3(-1.6, 0, 0), Vector3(2.2, 3, 2.4), SKIN[1])
	_box(body_root, "leg_right", Vector3(1.6, 0, 0), Vector3(2.2, 3, 2.4), SKIN[1])
	_box(body_root, "body", Vector3(0, 3, 0), Vector3(6, 5, 4.2), SKIN[3])
	_box(body_root, "belly", Vector3(0, 3.6, -2.1), Vector3(4, 3.4, 0.4), SKIN[4])
	_box(body_root, "arm_left", Vector3(-3.8, 4.4, 0), Vector3(1.6, 3.4, 1.8), SKIN[2])
	_box(body_root, "arm_right", Vector3(3.8, 4.4, 0), Vector3(1.6, 3.4, 1.8), SKIN[2])
	var head := Node3D.new()
	head.name = "head"
	head.position = Vector3(0, 8 * U, 0)
	body_root.add_child(head)
	_box(head, "head_box", Vector3(0, 0, 0), Vector3(9, 9, 8.5), SKIN[4])
	_box(head, "head_top", Vector3(0, 8.4, 0), Vector3(8.4, 0.6, 7.9), SKIN[5])
	_box(head, "jaw_shade", Vector3(0, 0, 0), Vector3(9.1, 1.2, 8.6), SKIN[3])
	for side in [-1.0, 1.0]:
		var sname := "left" if side < 0 else "right"
		# giant dark eyes on the front (-z) with two highlight pixels each
		_box(head, "eye_" + sname, Vector3(side * 2.3, 3.2, -4.3), Vector3(3.2, 3.8, 0.3), EYE)
		_box(head, "eye_" + sname + "_highlight", Vector3(side * 2.3 - 0.7, 5.6, -4.5), Vector3(0.9, 0.9, 0.1), EYE_HI)
		_box(head, "eye_" + sname + "_highlight_small", Vector3(side * 2.3 + 0.8, 3.7, -4.5), Vector3(0.5, 0.5, 0.1), EYE_HI)
		# pointy ears sticking out sideways: three stepped boxes getting smaller
		_box(head, "ear_" + sname + "_1", Vector3(side * 5.4, 4.6, 0), Vector3(1.8, 2.6, 1.6), SKIN[3])
		_box(head, "ear_" + sname + "_2", Vector3(side * 6.9, 5.2, 0), Vector3(1.4, 1.8, 1.2), SKIN[3])
		_box(head, "ear_" + sname + "_3", Vector3(side * 8.1, 5.8, 0), Vector3(1.2, 1.0, 0.8), SKIN[4])
	# small leafy tuft
	_box(head, "tuft_1", Vector3(0, 9, 0), Vector3(1.4, 1.0, 1.4), LEAF[1])
	_box(head, "tuft_2", Vector3(-0.9, 9.4, 0.3), Vector3(1.2, 0.6, 0.8), LEAF[2])
	_box(head, "tuft_3", Vector3(0.8, 9.3, -0.3), Vector3(1.0, 0.7, 0.9), LEAF[0])


func _box(parent: Node3D, box_name: String, base: Vector3, size: Vector3, color: Color) -> void:
	## base = centre of the bottom face, in Blockbench units.
	var mi := MeshInstance3D.new()
	mi.name = box_name
	var mesh := BoxMesh.new()
	mesh.size = size * U
	var mat := StandardMaterial3D.new()
	mat.albedo_color = color
	mat.roughness = 0.9
	mesh.material = mat
	mi.mesh = mesh
	mi.position = (base + Vector3(0, size.y / 2.0, 0)) * U
	parent.add_child(mi)
