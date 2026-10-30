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

var current_world: Node = null
var current_world_name := ""
var busy := false
var args := {}


func _ready() -> void:
	add_to_group("game_main")
	print("club impz: start args ", OS.get_cmdline_user_args())
	for a in OS.get_cmdline_user_args():
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


func change_world(world_name: String, spawn_name: String) -> void:
	## Fade to black, swap the world scene, place the player at the target spawn, fade back in.
	if busy:
		return
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
