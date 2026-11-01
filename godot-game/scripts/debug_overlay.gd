extends CanvasLayer
## Tiny debug overlay. Key 3 toggles it. Shows FPS, draw calls, player position and the current biome.
## Key 4 (debug_next_biome) cycles teleports to each biome centre in the resource world.

@onready var label: Label = $label

var biome_index := -1


func _ready() -> void:
	visible = true


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("toggle_debug"):
		visible = not visible
	elif event.is_action_pressed("debug_next_biome"):
		var main := get_tree().get_first_node_in_group("game_main")
		if main and main.current_world and main.current_world.has_method("biome_centre"):
			var names: Array = main.current_world.biome_names()
			biome_index = (biome_index + 1) % names.size()
			main.player.place_at(main.current_world.biome_centre(names[biome_index]))


func _process(_delta: float) -> void:
	if not visible:
		return
	var main := get_tree().get_first_node_in_group("game_main")
	if main == null:
		return
	var cam_mode: bool = main.free_cam != null
	var p: Vector3 = main.free_cam.global_position if cam_mode else main.player.global_position
	var mode := "\nCAMERA MODE  WASD move, Space/C up/down, Shift fast, right drag look, wheel speed %.0f" % main.free_cam.speed if cam_mode else ""
	label.text = "FPS %d   draw calls %d\npos %.1f, %.1f, %.1f\nbiome: %s\n3 overlay  4 next biome  5 day/night  6 fast sprint  7 camera mode%s" % [
		Engine.get_frames_per_second(),
		RenderingServer.get_rendering_info(RenderingServer.RENDERING_INFO_TOTAL_DRAW_CALLS_IN_FRAME),
		p.x, p.y, p.z, main.biome_name_at(p), mode]
