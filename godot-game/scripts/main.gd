extends Node
## Game root. Keeps the player, fade layer and debug overlay alive and swaps world scenes in and out.
## Every player starts in the hub (game_worlds.md section 1).
##
## Command line (after `--`), used by the screenshot tool and for quick testing:
##   --world=hub|resource|test   start world          --biome=forest|mountain|frost|plains|swamp   jump to a biome
##   --shot=res://path.png       save a screenshot     --shot_delay=6   seconds before the screenshot   --yaw=0.5 --pitch=-0.3 --zoom=10

const WORLDS := {
	"hub": "res://scenes/hub/hub_world.tscn",
	"resource": "res://scenes/resource/resource_world.tscn",
	"test": "res://scenes/test/flat_test_world.tscn",
	"lineup": "res://scenes/test/model_lineup.tscn",
}

@onready var world_holder: Node3D = $world_holder
@onready var player: CharacterBody3D = $imp_player
@onready var fade_rect: ColorRect = $fade_layer/fade_rect

## Camera mode (key 7) lets you fly around without the imp. It is a dev / screenshot tool: in an MMO a free
## camera in the shipped game would let anyone scout the whole map, so release builds only get it when this is on.
@export var camera_mode_in_release := false

var current_world: Node = null
const FREE_CAMERA := preload("res://scripts/player/free_camera.gd")
var free_cam: Camera3D = null
var current_world_name := ""
var busy := false
var args := {}


func _ready() -> void:
	add_to_group("game_main")
	print("club impz: start args ", OS.get_cmdline_user_args())
	var user_args := OS.get_cmdline_user_args()
	# web builds take the same flags from the url query: ?world=resource&biome=frost
	if OS.has_feature("web"):
		var query: String = str(JavaScriptBridge.eval("window.location.search")).trim_prefix("?")
		if query != "":
			user_args = PackedStringArray(Array(query.split("&")))
	for a in user_args:
		var kv := a.trim_prefix("--").split("=", true, 1)
		args[kv[0]] = kv[1] if kv.size() > 1 else "1"
	var start: String = args.get("world", "hub")
	_load_world(start, "spawn_point")
	if args.has("biome") and current_world.has_method("biome_centre"):
		await get_tree().process_frame
		player.place_at(current_world.biome_centre(args["biome"]))
	if args.has("yaw"): player.cam_yaw = float(args["yaw"])
	if args.has("pitch"): player.cam_pitch = float(args["pitch"])
	if args.has("zoom"): player.target_zoom = float(args["zoom"])
	fade_rect.color.a = 0.0
	if args.has("shot"):
		_take_screenshot(args["shot"], float(args.get("shot_delay", "6")))
	if args.has("perf"):
		_perf_probe(float(args["perf"]))
	if args.has("portal_test"):
		_portal_test()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_camera_mode") and not busy:
		if OS.is_debug_build() or camera_mode_in_release:
			set_camera_mode(free_cam == null)
			get_viewport().set_input_as_handled()


func set_camera_mode(on: bool) -> void:
	## Swap the view between the imp's follow camera and a free flying camera. The imp is frozen in place meanwhile.
	if on and free_cam == null:
		free_cam = FREE_CAMERA.new()
		free_cam.name = "free_camera"
		free_cam.transform = player.camera.global_transform  # main is a plain Node, so this is the world transform
		free_cam.fov = player.camera.fov
		add_child(free_cam)
		free_cam.make_current()
		player.frozen = true
		if current_world and current_world.has_method("set_view_focus"):
			current_world.set_view_focus(free_cam)
	elif not on and free_cam != null:
		player.camera.make_current()
		free_cam.queue_free()
		free_cam = null
		player.frozen = false
		if current_world and current_world.has_method("set_view_focus"):
			current_world.set_view_focus(player)


func change_world(world_name: String, spawn_name: String) -> void:
	## Fade to black, swap the world scene, place the player at the target spawn, fade back in.
	if busy:
		return
	set_camera_mode(false)
	busy = true
	player.frozen = true
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", 1.0, 0.5)
	await tw.finished
	_load_world(world_name, spawn_name)
	await get_tree().process_frame
	await get_tree().process_frame
	var tw2 := create_tween()
	tw2.tween_property(fade_rect, "color:a", 0.0, 0.6)
	await tw2.finished
	player.frozen = false
	busy = false


func _load_world(world_name: String, spawn_name: String) -> void:
	if current_world:
		world_holder.remove_child(current_world)
		current_world.queue_free()
	var packed: PackedScene = load(WORLDS[world_name])
	current_world = packed.instantiate()
	current_world_name = world_name
	world_holder.add_child(current_world)
	if current_world.has_method("set_player"):
		current_world.set_player(player)
	var marker := current_world.find_child(spawn_name, true, false) as Node3D
	var xform := marker.global_transform if marker else Transform3D(Basis(), Vector3(0, 5, 0))
	if current_world.has_method("ground_height"):
		xform.origin.y = current_world.ground_height(xform.origin.x, xform.origin.z) + 0.2
	player.place_at(xform)


func biome_name_at(pos: Vector3) -> String:
	if current_world and current_world.has_method("biome_at"):
		return current_world.biome_at(pos)
	return current_world_name


func _take_screenshot(path: String, delay: float) -> void:
	await get_tree().create_timer(delay).timeout
	await RenderingServer.frame_post_draw
	var img := get_viewport().get_texture().get_image()
	var abs_path := ProjectSettings.globalize_path(path) if path.begins_with("res://") else path
	DirAccess.make_dir_recursive_absolute(abs_path.get_base_dir())
	img.save_png(abs_path)
	print("screenshot saved: ", abs_path)
	get_tree().quit()


func _perf_probe(seconds: float) -> void:
	## Prints average FPS and draw calls after the world has settled, then quits (used for the performance pass).
	await get_tree().create_timer(6.0).timeout
	var frames := 0
	var draws := 0
	var t0 := Time.get_ticks_msec()
	while Time.get_ticks_msec() - t0 < seconds * 1000.0:
		await get_tree().process_frame
		frames += 1
		draws += RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME)
	var secs := (Time.get_ticks_msec() - t0) / 1000.0
	print("PERF %s %s: %.1f fps, %d draw calls, %d objects" % [current_world_name, args.get("biome", "-"), frames / secs, draws / max(frames, 1),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_OBJECTS_IN_FRAME)])
	if current_world.get("scatter"):
		var sc = current_world.scatter
		var fm := 0
		var tm := 0
		for c in sc.foliage_cells.values(): fm += c.get_child_count()
		for c in sc.tree_cells.values(): tm += c.get_child_count()
		print("PERF   foliage cells %d (%d multimeshes), tree cells %d (%d multimeshes), terrain chunks %d" % [
			sc.foliage_cells.size(), fm, sc.tree_cells.size(), tm, current_world.terrain.chunks.size()])
	get_tree().quit()


# debug: walk the player into the nearest portal twice (there and back) and log each world
func _portal_test() -> void:
	for i in 2:
		await get_tree().create_timer(4.0).timeout
		var portal: Node3D = null
		for n in current_world.find_children("*", "Node3D", true, false):
			if "target_world" in n:
				portal = n
				break
		if portal == null:
			print("PORTAL_TEST no portal in ", current_world_name)
			return
		player.place_at(Transform3D(Basis(), portal.global_position))
		await get_tree().create_timer(3.0).timeout
		print("PORTAL_TEST now in ", current_world_name)
	get_tree().quit()
