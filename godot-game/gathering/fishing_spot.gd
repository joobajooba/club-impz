class_name FishingSpot
extends GatherNode
## A fishing spot on the water (D-109): one fish tier per spot, cast from the shore with F, then
## press F again when the fish bites. It refreshes 10 seconds after a catch. Its origin is on the
## water surface; it has no collider.

var _t := 0.0
var _bite := 0.0


func setup_spot(tier_row: Dictionary) -> void:
	setup("fishing", tier_row, NodeArt.fishing_spot(tier_row), -1.0)
	radius = 0.5
	reach = 2.0


func prompt() -> String:
	return "Fish for " + row.label


func aim_point() -> Vector3:
	return global_position


## The fish takes the bait: a splash in the middle.
func bite() -> void:
	_bite = 0.6


func _process(delta: float) -> void:
	super(delta)
	_t += delta
	var fish: Node3D = _holder.find_child("Fish", true, false)
	if fish:
		var a := _t * 1.3
		var r := 0.3 * (1.0 - clampf(_bite / 0.6, 0.0, 1.0))
		fish.position = Vector3(cos(a) * r, -0.12, sin(a) * r)
		fish.rotation.y = -a
	for ring in _holder.find_children("Ring", "", true, false):
		var pulse := 1.0 + 0.06 * sin(_t * 2.5) + _bite * 0.6
		(ring as Node3D).scale = Vector3(pulse, 0.3, pulse)
	_bite = maxf(0.0, _bite - delta)
