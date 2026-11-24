extends Node3D
## A fishing spot on the resource world's water (resource_gathering.md section 7.3, Proposed): rings on the
## surface and the shadow of its one fish circling under them. Placed by resource_landmarks.gd, fished by
## scripts/player/fisher.gd. Spots are shared and never run out (section 9). The origin is on the water
## surface; there is no collider. The meta "stand" is a shore point to fish from (tests, --goto_fish).

var fish := ""                   # fish id (GameData.tiers.fishing row id)
var row: Dictionary
var water := ""                  # the layout water body's name
var pull := 0.0                  # 0..1: how close the fish has come (the fisher sets it from the catch bar)

var _t := 0.0
var _phase := 0.0
var _nibble := 0.0
var _bite := 0.0
var _fish: Node3D
var _rings: Array[Node3D] = []


func setup(fish_id: String) -> void:
	fish = fish_id
	for r in GameData.tiers["fishing"]:
		if r.id == fish_id:
			row = r
	add_to_group("fish_spot")
	var art := NodeArt.fishing_spot(row)
	art.scale = Vector3.ONE * 1.5
	add_child(art)
	_fish = art.find_child("Fish", true, false) as Node3D
	for ring in art.find_children("Ring", "", true, false):
		_rings.append(ring as Node3D)
	_phase = float(absi(hash(name)) % 628) / 100.0


func label() -> String:
	return str(row.get("label", fish))


func tier() -> int:
	return int(row.get("tier", 1))


## A twitch on the line before the bite, so it never comes out of nowhere.
func nibble() -> void:
	_nibble = 0.35


## The fish takes the bait: it darts to the middle and the rings jump.
func bite() -> void:
	_bite = 0.6


func _process(delta: float) -> void:
	var cam := get_viewport().get_camera_3d()
	if cam and cam.global_position.distance_squared_to(global_position) > 3600.0:
		return                                         # nobody sees ripples 60 m away
	_t += delta
	if _fish:
		var a := _t * (1.0 + pull * 0.8) + _phase
		var r := 0.32 * (1.0 - 0.75 * pull) * (1.0 - clampf(_bite / 0.6, 0.0, 1.0))
		_fish.position = Vector3(cos(a) * r, -0.08, sin(a) * r)   # just under the surface: the swamp is shallow
		_fish.rotation.y = -a
	for i in _rings.size():
		var pulse := 1.0 + 0.06 * sin(_t * 2.0 + _phase + i) + _bite * 0.6 + _nibble * 0.25
		_rings[i].scale = Vector3(pulse, 0.3, pulse)
	_bite = maxf(0.0, _bite - delta)
	_nibble = maxf(0.0, _nibble - delta)
