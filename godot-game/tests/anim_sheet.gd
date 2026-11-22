extends Node3D
## A pose sheet for checking the Imp's animation by eye (scripts/player/imp_visual.gd). Not a pass/fail test.
##   godot --path godot-game res://tests/anim_sheet.tscn -- --out=C:/path/sheet.png --at=1.3 --side
## Six Imps in a row: standing, walking, running, in a jump, mid-swing (pickaxe) and fishing (rod held out).
## They walk on the spot (their fake bodies don't move). After `--at` seconds it saves a screenshot and quits.
## --side: camera from the side (default: three-quarter view). --swing=0.45: how far into the swing (0..1).

const ImpVisual := preload("res://scripts/player/imp_visual.gd")


class FakeBody:
	extends Node3D
	var velocity := Vector3.ZERO
	var grounded := true

	func is_on_floor() -> bool:
		return grounded


var _args := {}


func _ready() -> void:
	Save.enabled = false
	for a in OS.get_cmdline_user_args():
		var kv := a.trim_prefix("--").split("=", true, 1)
		_args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_COLOR
	env.environment.background_color = Color("#9cc4e4")
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.75, 0.78, 0.85)
	env.environment.ambient_light_energy = 0.35
	add_child(env)
	for n in get_tree().root.get_children():             # the HUD, chat and menus from the autoloads
		for layer in n.find_children("*", "CanvasLayer", true, false) + ([n] if n is CanvasLayer else []):
			(layer as CanvasLayer).visible = false
	var sun := DirectionalLight3D.new()
	sun.light_energy = 0.8
	sun.rotation = Vector3(-0.9, 0.6, 0)
	sun.shadow_enabled = true
	add_child(sun)
	var ground := MeshInstance3D.new()
	var plane := PlaneMesh.new()
	plane.size = Vector2(40, 40)
	ground.mesh = plane
	var gm := StandardMaterial3D.new()
	gm.albedo_color = Color("#6f9a4c")
	ground.material_override = gm
	add_child(ground)
	var swing := float(_args.get("swing", "0.45"))
	var at := float(_args.get("at", "1.3"))
	var specs := [
		["standing", "pickaxe", Vector3.ZERO, true],
		["walking", "pickaxe", Vector3(0, 0, -4.0), true],
		["running", "pickaxe", Vector3(0, 0, -6.5), true],
		["jump", "pickaxe", Vector3(0, 2.0, -3.0), false],
		["swing", "pickaxe", Vector3.ZERO, true],
		["fishing", "rod", Vector3.ZERO, true],
	]
	if _args.has("only"):                                  # --only=walking,running: just those, bigger
		var keep: PackedStringArray = str(_args["only"]).split(",")
		specs = specs.filter(func(s): return s[0] in keep)
	for i in specs.size():
		var s: Array = specs[i]
		Inventory.in_hand = s[1]                       # each Imp takes the tool in hand when it is built
		var body := FakeBody.new()
		body.name = s[0]
		body.velocity = s[2]
		body.grounded = s[3]
		body.position = Vector3((i - (specs.size() - 1) * 0.5) * 1.4, 0, 0)
		add_child(body)
		var v: Node3D = ImpVisual.new()
		v.name = "visual"
		body.add_child(v)
		v.rotation.y = PI * 0.5 if _args.has("side") else 0.0   # side view: facing left across the screen
		match s[0]:
			"swing":
				get_tree().create_timer(maxf(0.01, at - swing * 0.95)).timeout.connect(func(): v.play_action("pickaxe"))
			"fishing":
				v.set_hold("rod_wait")
		var label := Label3D.new()
		label.text = s[0]
		label.position = Vector3(0, 1.75, 0)
		label.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		label.pixel_size = 0.004
		label.font_size = 48
		label.outline_size = 12
		body.add_child(label)
	var cam := Camera3D.new()
	cam.fov = 40
	add_child(cam)
	var dist := 1.6 + specs.size() * 1.2
	cam.position = Vector3(0, 1.0, dist) if _args.has("side") else Vector3(dist * 0.35, 1.5, dist)
	cam.look_at(Vector3(0, 0.75, 0))
	cam.current = true
	await get_tree().create_timer(at).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var out: String = _args.get("out", "user://anim_sheet.png")
	img.save_png(ProjectSettings.globalize_path(out))
	print("anim sheet saved: ", ProjectSettings.globalize_path(out))
	get_tree().quit()
