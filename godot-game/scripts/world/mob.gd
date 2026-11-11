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
## Close up, a nametag floats over the mob ("Cow", "Ember Dragon"), and now and then it calls (a moo, a
## howl, a roar: assets/sounds, made by build scripts/make_sounds.py) when the player is in earshot.
##
## Cheap enough to have a few dozen: each mob kind's glb (one mesh per cube) is merged once per bone into a
## template, the mobs are copies of it, and a mob far from the camera is hidden and its animation stopped.

const PATH := "res://assets/models/mobs/%s.glb"
const ACTIVE := 180.0            # metres from the view: closer mobs show, animate and move
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
var size := 1.0                   # scale of the model (the pale dragon is half size); speeds scale with it
var radius := -1.0                # home radius in metres (-1 = the kind's own)
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

## Name shown over the mob, its height in metres (model top, for the nametag), and its calls.
const INFO := {
	"cow": {name = "Cow", height = 1.47, calls = ["cow_moo_1", "cow_moo_2"]},
	"highland_cow": {name = "Highland Cow", height = 1.69, calls = ["highland_cow_moo_1"]},
	"pig": {name = "Pig", height = 0.6, calls = ["pig_oink_1", "pig_oink_2"]},
	"wolf": {name = "Wolf", height = 0.94, calls = ["wolf_howl_1", "wolf_bark_1"]},
	"ogre": {name = "Ogre", height = 2.5, calls = ["ogre_grunt_1", "ogre_grunt_2"]},
	"stone_golem": {name = "Stone Golem", height = 4.75, calls = ["golem_rumble_1"]},
	"dragon": {name = "Dark Dragon", height = 1.63, calls = ["dragon_roar_1"]},
	"pale_dragon": {name = "Pale Dragon", height = 1.63, calls = ["pale_screech_1"]},
	"ember_dragon": {name = "Ember Dragon", height = 3.5, calls = ["ember_roar_1"]},
}
const TAG_NEAR := 10.0            # nametag fully shown within this many metres, gone by TAG_FAR
const TAG_FAR := 14.0
const EARSHOT := 45.0             # the player hears its calls within this many metres
var _tag: Label3D
var _voice: AudioStreamPlayer3D
var _calls: Array[AudioStream] = []
var _next_call := 0.0


func _ready() -> void:
	scale = Vector3.ONE * size
	_body = _template(kind).instantiate() as Node3D
	add_child(_body)
	var info: Dictionary = INFO.get(kind, {name = kind.capitalize(), height = 1.5, calls = []})
	_tag = Label3D.new()
	_tag.name = "nametag"
	_tag.text = info.name
	_tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
	_tag.no_depth_test = true
	_tag.fixed_size = false
	_tag.pixel_size = 0.0068
	_tag.font_size = 44
	_tag.outline_size = 14
	_tag.modulate = Color(1.0, 0.93, 0.7, 0.0)
	_tag.outline_modulate = Color(0.04, 0.04, 0.06, 0.0)
	_tag.position = Vector3(0, float(info.height) + 0.35 / size, 0)
	_tag.scale = Vector3.ONE / size                    # the same size over every mob, whatever its scale
	_tag.visible = false
	_tag.font = Settings.font()
	Settings.changed.connect(_on_settings_changed)
	add_child(_tag)
	for c in info.calls:
		var path := "res://assets/sounds/%s.wav" % c
		if ResourceLoader.exists(path):
			_calls.append(load(path))
	_voice = AudioStreamPlayer3D.new()
	_voice.name = "voice"
	_voice.unit_size = clampf(float(info.height) * size * 3.0, 2.5, 12.0)
	_voice.max_distance = EARSHOT + 15.0
	_voice.position = Vector3(0, float(info.height) * 0.7, 0)
	add_child(_voice)
	_next_call = Time.get_ticks_msec() / 1000.0 + _hash01(mob_seed, 3) * 12.0
	_anim = _body.find_children("*", "AnimationPlayer", true, false).front() as AnimationPlayer
	var k: Dictionary = KINDS[kind]
	# a leg is long enough to walk across the home area and still idle a while
	_leg_len = maxf(10.0, 2.0 * (radius if radius > 0.0 else float(k.radius)) * maxf(size, 0.6) / (float(k.walk) * size) / 0.7)
	_update(true)


func _process(_delta: float) -> void:
	_update(false)


func _update(force: bool) -> void:
	var near := not is_instance_valid(view) or view.global_position.distance_to(global_position) < ACTIVE
	if not near and not force:
		if _body.visible:
			_body.visible = false
			_tag.visible = false
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
	var speed: float = (k.run if running else k.walk) * size
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
	if near and is_instance_valid(view):
		_near_player(view.global_position.distance_to(global_position))


## Spot of leg k: a dry, gentle spot within the home radius, the same on every client.
func _spot(k: int) -> Vector3:
	if _spots.has(k):
		return _spots[k]
	if _spots.size() > 8:
		_spots.clear()
	var r: float = (radius if radius > 0.0 else float(KINDS[kind].radius)) * maxf(size, 0.6)
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
		for n in ["idle", "walk", "run", "look", "glide", "hover", "fly", "swim"]:
			if ap.has_animation(n):
				ap.get_animation(n).loop_mode = Animation.LOOP_LINEAR
	var packed := PackedScene.new()
	packed.pack(root)
	root.free()
	_templates[id] = packed
	return packed



func _on_settings_changed() -> void:
	_tag.font = Settings.font()           # Text style (Settings, Options)


## Close to the player: the nametag fades in, and now and then the mob calls.
func _near_player(d: float) -> void:
	var a := clampf((TAG_FAR - d) / (TAG_FAR - TAG_NEAR), 0.0, 1.0)
	_tag.visible = a > 0.0
	if _tag.visible:
		_tag.modulate.a = a
		_tag.outline_modulate.a = a
	var now := Time.get_ticks_msec() / 1000.0
	if d < EARSHOT and now >= _next_call and not _calls.is_empty():
		_voice.stream = _calls[randi() % _calls.size()]
		_voice.pitch_scale = randf_range(0.92, 1.08) / sqrt(maxf(size, 0.25)) if size < 1.0 else randf_range(0.92, 1.08)
		_voice.play()
		_next_call = now + randf_range(9.0, 24.0)

