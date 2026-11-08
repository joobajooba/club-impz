extends Node3D
## A mob wandering in the resource world: one of the Blockbench mobs in assets/models/mobs (cow, highland cow,
## pig, wolf, ogre, stone golem, dragon, pale dragon, ember dragon), with its idle / walk / run animations.
## Placed by resource_landmarks.gd (game_worlds.md section 4.8 mob ideas). No combat or hunting yet.
##
## Wandering is worked out from the clock, not simulated: time is cut into legs of LEG seconds, and leg k goes
## from spot k to spot k+1 round the mob's home (spots come from its seed, on dry walkable ground). Each leg the
## mob idles, then walks (sometimes runs) to the next spot. Every player's game computes the same thing from the
## same seed and the same clock, so everyone sees the same mob in the same place, with nothing sent over the
## network. The walk and run cycles cover exactly the ground speeds below, so the feet don't slide
## (build scripts/build_mob_anims.py measured them).
##
## Cheap enough to have a few dozen: each mob kind's glb (one mesh per cube) is merged once per bone into a
## template, the mobs are copies of it, and a mob far from the camera is hidden and its animation stopped.

const PATH := "res://assets/models/mobs/%s.glb"
const ACTIVE := 130.0            # metres from the view: closer mobs animate and move
const KINDS := {  # walk / run in m/s (build_mob_anims.py), how often a leg is a run, home radius (m)
	"cow": {walk = 0.37, run = 1.68, run_chance = 0.08, radius = 9.0},
	"highland_cow": {walk = 0.32, run = 1.53, run_chance = 0.06, radius = 9.0},
	"pig": {walk = 0.24, run = 0.91, run_chance = 0.15, radius = 6.0},
	"wolf": {walk = 0.49, run = 2.59, run_chance = 0.35, radius = 16.0},
	"ogre": {walk = 0.82, run = 2.85, run_chance = 0.1, radius = 12.0},
	"stone_golem": {walk = 0.64, run = 2.17, run_chance = 0.0, radius = 10.0},
	"dragon": {walk = 0.5, run = 2.0, run_chance = 0.12, radius = 18.0},
	"pale_dragon": {walk = 0.5, run = 2.0, run_chance = 0.12, radius = 18.0},
	"ember_dragon": {walk = 1.1, run = 4.32, run_chance = 0.12, radius = 22.0},
}

@export var kind := "cow"
var home := Vector3.ZERO
var mob_seed := 1
var data: WorldData
var view: Node3D                 # what "far away" is measured from (the player)

var _body: Node3D
var _anim: AnimationPlayer
var _playing := ""
var _leg_len := 12.0
var _spots := {}                 # leg index -> Vector3 (cached)
var _yaw := 0.0

static var _templates := {}      # kind -> PackedScene (the glb merged per bone)


func _ready() -> void:
	_body = _template(kind).instantiate() as Node3D
	add_child(_body)
	_anim = _body.find_children("*", "AnimationPlayer", true, false).front() as AnimationPlayer
	var k: Dictionary = KINDS[kind]
	# a leg is long enough to walk across the home area and still idle a while
	_leg_len = maxf(10.0, 2.0 * float(k.radius) / float(k.walk) / 0.7)
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
	_body.visible = near
	var k: Dictionary = KINDS[kind]
	var t := Time.get_unix_time_from_system() + float(mob_seed % 997)
	var leg := floori(t / _leg_len)
	var f := t - leg * _leg_len
	var a := _spot(leg)
	var b := _spot(leg + 1)
	var running := _hash01(leg, 7) < float(k.run_chance)
	var speed: float = k.run if running else k.walk
	var dist := Vector2(b.x - a.x, b.z - a.z).length()
	var travel := dist / speed
	if travel > _leg_len * 0.9:                        # never late for the next leg
		travel = _leg_len * 0.9
	var pause := _leg_len - travel
	var pos := a
	var anim := "idle"
	if f >= pause and dist > 0.05:
		var s := clampf((f - pause) / travel, 0.0, 1.0)
		pos = a.lerp(b, s)
		anim = "run" if running else "walk"
		_yaw = atan2(-(b.x - a.x), -(b.z - a.z))      # the models face -z
	pos.y = data.height(pos.x, pos.z) - 0.05
	global_position = pos
	rotation.y = lerp_angle(rotation.y, _yaw, 0.15) if not force else _yaw
	if _anim and near and anim != _playing:
		_playing = anim
		_anim.play(anim, 0.3)


## Spot of leg k: a dry, gentle spot within the home radius, the same on every client.
func _spot(k: int) -> Vector3:
	if _spots.has(k):
		return _spots[k]
	if _spots.size() > 8:
		_spots.clear()
	var r: float = KINDS[kind].radius
	var out := home
	for i in 8:
		var ang := _hash01(k, 11 + i) * TAU
		var d := sqrt(_hash01(k, 31 + i)) * r
		var x := home.x + cos(ang) * d
		var z := home.z + sin(ang) * d
		var h := data.height(x, z)
		if h > data.water_level(x, z) + 0.25 and data.normal(x, z).y > 0.8 and data.in_bounds(x, z, 4.0):
			out = Vector3(x, h, z)
			break
	_spots[k] = out
	return out


func _hash01(k: int, salt: int) -> float:
	return float(hash([mob_seed, k, salt]) & 0xffffff) / float(0x1000000)


## The glb with its cubes merged per bone (each bone node keeps one mesh), and its loops set. Built once per kind.
static func _template(id: String) -> PackedScene:
	if _templates.has(id):
		return _templates[id]
	var root := (load(PATH % id) as PackedScene).instantiate() as Node3D
	var by_parent := {}
	for mi: MeshInstance3D in root.find_children("*", "MeshInstance3D", true, false):
		by_parent.get_or_add(mi.get_parent(), []).append(mi)
	for parent: Node in by_parent:
		var list: Array = by_parent[parent]
		if list.size() < 2:
			continue
		var tools := {}
		for mi: MeshInstance3D in list:
			for si in mi.mesh.get_surface_count():
				var mat := mi.get_active_material(si)
				if not tools.has(mat):
					tools[mat] = SurfaceTool.new()
					(tools[mat] as SurfaceTool).begin(Mesh.PRIMITIVE_TRIANGLES)
					(tools[mat] as SurfaceTool).set_material(mat)
				(tools[mat] as SurfaceTool).append_from(mi.mesh, si, mi.transform)
		var merged := ArrayMesh.new()
		for mat in tools:
			merged = (tools[mat] as SurfaceTool).commit(merged)
		var out := MeshInstance3D.new()
		out.name = "merged"
		out.mesh = merged
		parent.add_child(out)
		out.owner = root
		for mi: MeshInstance3D in list:
			parent.remove_child(mi)
			mi.free()
	var anim := root.find_children("*", "AnimationPlayer", true, false)
	if not anim.is_empty():
		var ap := anim[0] as AnimationPlayer
		for n in ["idle", "walk", "run", "look", "glide", "hover", "fly"]:
			if ap.has_animation(n):
				ap.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	var packed := PackedScene.new()
	packed.pack(root)
	root.free()
	_templates[id] = packed
	return packed
