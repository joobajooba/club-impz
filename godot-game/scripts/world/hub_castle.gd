extends Node3D
## The hub castle (assets/models/buildings/hub_castle.glb, converted from J00BA's Blockbench model) with simple
## colliders built from the model's own block sizes. Scenery only: players can't go inside.
## Sizes below are Blockbench units (16 = 1 m), straight from hub_castle.bbmodel.

const U := 1.0 / 16.0
const BOXES := [
	[Vector3(34, 0, -28), Vector3(88, 50, 18)],      # left wing
	[Vector3(-88, 0, -28), Vector3(-34, 50, 18)],    # right wing
	[Vector3(-13, 0, -34), Vector3(13, 61, 18)],     # centre block
	[Vector3(-11, 0, -40), Vector3(11, 46, -34)],    # porch and closed door
]
const TOWERS := [  # centre x, centre z, radius, height
	[106, -10, 19, 76], [-106, -10, 19, 76], [24, -28, 10.5, 64], [-24, -28, 10.5, 64],
	[50, 20, 11, 80], [-64, 20, 11, 80],
]


func _ready() -> void:
	var body := StaticBody3D.new()
	body.name = "collision"
	body.collision_layer = 4
	add_child(body)
	for b in BOXES:
		var a: Vector3 = b[0] * U
		var c: Vector3 = b[1] * U
		_shape(body, _box(c - a), (a + c) / 2.0)
	for t in TOWERS:
		var cyl := CylinderShape3D.new()
		cyl.radius = t[2] * U
		cyl.height = t[3] * U
		_shape(body, cyl, Vector3(t[0], t[3] / 2.0, t[1]) * U)
	for k in 6:  # the six front steps
		var w := 15.0 - k * 0.5
		var a := Vector3(-w, 0, -56 + k * 2.5) * U
		var c := Vector3(w, 1.5 * (k + 1), -40) * U
		_shape(body, _box(c - a), (a + c) / 2.0)


func _box(size: Vector3) -> BoxShape3D:
	var s := BoxShape3D.new()
	s.size = size
	return s


func _shape(body: StaticBody3D, shape: Shape3D, pos: Vector3) -> void:
	var cs := CollisionShape3D.new()
	cs.shape = shape
	cs.position = pos
	body.add_child(cs)
