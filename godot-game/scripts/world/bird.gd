extends Node3D
## A bird in the resource world: one of the Blockbench birds in assets/models/mobs/birds (pigeon, seagull,
## eagle, heron, swan, crow, owl, snowy owl, duck, robin), using its rig (wings fold and spread at the
## shoulders and wrists) and its idle / walk / fly / glide / swim animations. Placed by resource_landmarks.gd.
##
## Like the mobs (mob.gd), where a bird is comes from the clock and its seed, not a simulation, so every
## player's game shows the same bird in the same place with nothing sent over the network.
##   soar    (eagle, seagull)  circles high over its home, the circle drifting slowly; it mostly glides, with
##                             a few beats of the wings now and then, and banks into the turn
##   hop     (pigeon, crow, robin, owls, heron)  time is cut into legs; on a ground leg it potters about
##                             (idle, a few steps), on a flight leg it takes off, flies an arc to the next spot
##                             and lands (staying up if the next leg is a flight too)
##   swim    (duck, swan)      paddles about on the water (swim), and now and then flies off and lands on it again
## Far from the camera (ACTIVE) a bird is hidden and paused.

const MOB := preload("res://scripts/world/mob.gd")
const ACTIVE := 200.0
## style, how often a leg is a flight, flight / ground speed (m/s), cruise height (m), home radius (m), leg (s)
const KINDS := {
	"eagle": {style = "soar", speed = 7.0, height = 34.0, radius = 38.0},
	"seagull": {style = "soar", speed = 6.0, height = 16.0, radius = 26.0},
	"pigeon": {style = "hop", air = 0.45, speed = 5.0, walk = 0.35, height = 7.0, radius = 22.0, leg = 12.0},
	"crow": {style = "hop", air = 0.5, speed = 5.5, walk = 0.35, height = 9.0, radius = 28.0, leg = 12.0},
	"robin": {style = "hop", air = 0.4, speed = 4.0, walk = 0.25, height = 4.0, radius = 14.0, leg = 10.0},
	"owl": {style = "hop", air = 0.35, speed = 4.5, walk = 0.2, height = 8.0, radius = 24.0, leg = 16.0},
	"snowy_owl": {style = "hop", air = 0.35, speed = 4.5, walk = 0.2, height = 8.0, radius = 26.0, leg = 16.0},
	"heron": {style = "hop", air = 0.25, speed = 4.0, walk = 0.25, height = 6.0, radius = 30.0, leg = 18.0, shore = true},
	"duck": {style = "swim", air = 0.15, speed = 6.0, walk = 0.35, height = 6.0, radius = 16.0, leg = 14.0},
	"swan": {style = "swim", air = 0.08, speed = 6.0, walk = 0.3, height = 7.0, radius = 18.0, leg = 18.0},
}

@export var kind := "pigeon"
var home := Vector3.ZERO
var bird_seed := 1
var data: WorldData
var view: Node3D
var water := {}                   # for swimmers and waders: {rect, level}
var range_scale := 1.0            # shrinks (or grows) the kind's home radius (the hub keeps birds round the spawn)
var spot_ok := Callable()         # optional func(x, z) -> bool: where a bird may land (the hub: not on a stall)

var _body: Node3D
var _anim: AnimationPlayer
var _playing := ""
var _spots := {}
var _last_pos := Vector3.ZERO


func _ready() -> void:
	_body = MOB._template("birds/" + kind).instantiate() as Node3D
	add_child(_body)
	_anim = _body.find_children("*", "AnimationPlayer", true, false).front() as AnimationPlayer
	_update(true)


func _process(_delta: float) -> void:
	_update(false)


func _update(force: bool) -> void:
	var near := not is_instance_valid(view) or view.global_position.distance_to(global_position) < ACTIVE
	if not near and not force:
		if _body.visible:
			_body.visible = false
			if _anim:
				_anim.pause()
		return
	_body.visible = true
	var t := Time.get_unix_time_from_system() + float(bird_seed % 997)
	var k: Dictionary = KINDS[kind]
	var res: Array = _soar(t, k) if k.style == "soar" else _legs(t, k)
	var pos: Vector3 = res[0]
	var anim: String = res[1]
	var bank: float = res[2]
	# face along the way it is going
	var d := pos - _last_pos
	if d.length() > 0.002 and not force:
		var yaw := atan2(-d.x, -d.z)
		rotation.y = lerp_angle(rotation.y, yaw, 0.2)
	_last_pos = pos
	global_position = pos
	rotation.z = lerp(rotation.z, bank, 0.1)
	if _anim and anim != _playing and _anim.has_animation(anim):
		_playing = anim
		_anim.play(anim, 0.25)


## Eagles and gulls: a circle round a slowly drifting centre, gliding, a few wing beats every so often.
func _soar(t: float, k: Dictionary) -> Array:
	var r: float = k.radius * range_scale * (0.7 + 0.3 * _hash01(0, 1))
	var w: float = k.speed / r * (1.0 if _hash01(0, 2) < 0.5 else -1.0)
	var c := home + Vector3(cos(t * 0.013 + bird_seed) * 12.0, 0, sin(t * 0.017 + bird_seed) * 12.0)
	var a := t * w + _hash01(0, 3) * TAU
	var p := c + Vector3(cos(a) * r, 0, sin(a) * r)
	var ground := maxf(data.height(p.x, p.z), data.water_level(p.x, p.z))
	p.y = maxf(ground + 6.0, home.y + float(k.height) + sin(t * 0.21 + bird_seed) * 3.0)
	var flap := fmod(t + bird_seed * 1.7, 9.0) < 1.6
	return [p, "fly" if flap else "glide", -0.32 * signf(w)]


## Ground / water birds: legs of `leg` seconds, each on the ground (or water) or a flight to the next spot.
func _legs(t: float, k: Dictionary) -> Array:
	var L: float = k.leg
	var leg := floori(t / L)
	var f := (t - leg * L) / L
	var a := _spot(leg)
	var b := _spot(leg + 1)
	var swim: bool = k.style == "swim"
	if _flies(leg):
		var up_before := _flies(leg - 1)
		var up_after := _flies(leg + 1)
		var s := smoothstep(0.0, 1.0, f)
		var p := a.lerp(b, s)
		var side := Vector3(-(b.z - a.z), 0, b.x - a.x).normalized() * sin(PI * f) * a.distance_to(b) * 0.25
		p += side
		var climb := 1.0 if up_before else smoothstep(0.0, 0.22, f)
		var fall := 1.0 if up_after else 1.0 - smoothstep(0.8, 1.0, f)
		var alt: float = float(k.height) * minf(climb, fall)
		var ground := maxf(data.height(p.x, p.z), data.water_level(p.x, p.z) if swim else -1000.0)
		p.y = ground + alt
		var anim := "glide"
		if (not up_before and f < 0.25) or (not up_after and f > 0.75) or fmod(t + bird_seed, 5.0) < 1.5:
			anim = "fly"
		if alt < 0.15:
			anim = "swim" if swim else "idle"
		return [p, anim, -0.25 * sin(PI * f) * signf(side.dot(Vector3(1, 0, 0)) + 0.001)]
	# on the ground / water: stand a while, then walk (paddle) a few steps toward a nearby point
	var walk_to := a + Vector3(cos(_hash01(leg, 9) * TAU), 0, sin(_hash01(leg, 9) * TAU)) * minf(2.5, k.walk * L * 0.4)
	var moving := f > 0.4 and f < 0.75
	var p := a.lerp(walk_to, smoothstep(0.4, 0.75, f))
	if swim:
		p.y = water.get("level", data.water_level(p.x, p.z)) - 0.05
		return [p, "swim", 0.0]
	p.y = data.height(p.x, p.z)
	return [p, "walk" if moving else "idle", 0.0]


func _flies(leg: int) -> bool:
	return _hash01(leg, 5) < float(KINDS[kind].get("air", 0.0))


## The spot for leg k: on dry ground, on the water (swimmers) or on the shore (waders), within the home radius.
func _spot(k: int) -> Vector3:
	if _spots.has(k):
		return _spots[k]
	if _spots.size() > 8:
		_spots.clear()
	var r: float = KINDS[kind].radius * range_scale
	var out := home
	var swim: bool = KINDS[kind].style == "swim"
	var shore: bool = KINDS[kind].get("shore", false)
	for i in 10:
		var ang := _hash01(k, 11 + i) * TAU
		var d := sqrt(_hash01(k, 31 + i)) * r
		var x := home.x + cos(ang) * d
		var z := home.z + sin(ang) * d
		if not data.in_bounds(x, z, 4.0):
			continue
		if spot_ok.is_valid() and not spot_ok.call(x, z):
			continue
		var h := data.height(x, z)
		var wl := data.water_level(x, z)
		var ok := false
		if swim:
			ok = h < wl - 0.3
		elif shore:
			ok = h > wl - 0.2 and h < wl + 0.8 and data.normal(x, z).y > 0.8
		else:
			ok = h > wl + 0.25 and data.normal(x, z).y > 0.8
		if ok:
			out = Vector3(x, h, z)
			break
	_spots[k] = out
	return out


func _hash01(k: int, salt: int) -> float:
	return float(hash([bird_seed, k, salt]) & 0xffffff) / float(0x1000000)
