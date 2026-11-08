extends Node
## Game root. Keeps the player, fade layer and debug overlay alive and swaps world scenes in and out.
## Every player starts in the hub (game_worlds.md section 1).
##
## Command line (after `--`), used by the screenshot tool and for quick testing:
##   --world=hub|resource|test   start world          --biome=forest|mountain|frost|plains|swamp   jump to a biome
##   --shot=res://path.png       save a screenshot     --shot_delay=6   seconds before the screenshot   --yaw=0.5 --pitch=-0.3 --zoom=10
##   --bot=40                    walk in a circle in front of the spawn for 40 s, then quit (a second player
##                               for testing multiplayer: run one with --headless next to a normal game)
##   --tool=sword --swing_at=5.8 take out a tool kind and swing it after that many seconds (with --shot)
##   --chop_at=5 --chop_time=4 --regrow=12   step up to the nearest choppable tree and chop it after 5 s, with
##                               every tree taking 4 s and growing back after 12 s   --chop_measure  print where
##                               the axe head lands   --axe=bronze_axe  hold that axe (testing: owned or not)
##   --shot_loading              also save loading_screen.png next to --shot, half way through loading
##   --inventory_open            open the inventory (I) once the world has loaded   --give=maple_log,pine_log  add 3 of each
##   --ore_event=void  start an ore event   --pickaxe=void_pickaxe  hold that pickaxe   --mine_chance=50  x50 per swing   --mine_time=3
##   --mine_at=4  start mining the vein in reach after 4 s
##   --goto_mob=wolf  stand 7 m from the first mob of that kind   --follow --follow_dist=4 --follow_h=0.7  keep beside it   --look_at  a free camera on it
##   --goto_scatter=rock_swamp_l  stand by the first scattered mesh of that alias
##   --goto_ore=gold  stand next to the first vein of that ore (void / stellarite: the event vein)   --unlock_tools  own every tool   --equip=iron_axe  equip a tool from the grid
##   --wallet=0x…                desktop only: show that wallet's impz.club account (read only) in the HUD and
##                               Profile menu, as if it had connected   --profile_open   open the Profile menu too

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
## The world the player is in once it has finished loading ("" on the loading screen). Net (autoload/net.gd)
## sends this one, so other players only see this Imp, and this player only sees theirs, once it's loaded.
var joined_world := ""
var busy := false
var args := {}
const LOAD_BUDGET_USEC := 25000           # world building per frame on the loading screen (the bar still moves)
const LOADING_TITLES := {"hub": "Returning to the Hub", "resource": "Entering The Wilds"}
var loading: CanvasLayer                  # ui/loading_screen.gd
var inventory_ui: CanvasLayer             # ui/inventory_ui.tscn, I


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
	loading = preload("res://ui/loading_screen.gd").new()
	loading.name = "loading_screen"
	add_child(loading)
	inventory_ui = preload("res://ui/inventory_ui.tscn").instantiate()
	inventory_ui.visible = false
	inventory_ui.add_to_group("modal")                 # the Imp stands still while it is open
	add_child(inventory_ui)
	var start: String = args.get("world", "hub")
	busy = true
	player.frozen = true
	await _enter_world(start, "spawn_point")
	if args.has("biome") and current_world.has_method("biome_centre"):
		player.place_at(current_world.biome_centre(args["biome"]))
	if args.has("ore_event"):                              # testing: --ore_event=void starts an event here
		OreEvents.start_local(args["ore_event"])
		await get_tree().process_frame
	if args.has("pickaxe"):                                # testing: hold any pickaxe
		Inventory.held["pickaxe"] = args["pickaxe"]
		Inventory.sync_tools()
		Inventory.take_out("pickaxe")
	if args.has("mine_time"):                              # testing: every ore takes this many seconds
		player.miner.time_override = float(args["mine_time"])
	if args.has("mine_chance"):                            # testing: multiply the chance per swing
		player.miner.chance_scale = float(args["mine_chance"])
	if args.has("mob_list"):                               # testing: where every mob is
		print("SPAWN ", player.global_position)
		for n in current_world.find_children("*", "Node3D", true, false):
			if n.get("mob_seed") != null:
				print("MOBPOS ", n.get("kind"), " ", n.global_position)
			if n.get("bird_seed") != null:
				print("BIRDPOS ", n.get("kind"), " ", n.global_position, " ", n.get("_playing"))
	if args.has("goto_mob"):                               # testing: --goto_mob=wolf stands 7 m from the first wolf
		for n in current_world.find_children(args["goto_mob"] + "_*", "Node3D", true, false):
			if n.get_script() == null:
				continue
			var p: Vector3 = n.global_position + Vector3(0, 0, 7.0)
			p.y = current_world.ground_height(p.x, p.z) + 0.3
			player.place_at(Transform3D(Basis(), p))
			print("MOB at ", n.name, " ", n.global_position)
			if args.has("follow"):                         # keep standing beside it (for screenshots of it walking)
				_follow(n, float(args.get("follow_dist", "4.5")))
			if args.has("look_at"):                        # a free camera that keeps 8 m from it (for birds in the air)
				_look_at(n, float(args.get("follow_dist", "8")))
			break
	if args.has("goto_scatter"):                           # testing: --goto_scatter=rock_swamp_l stands by the first of those
		var sc := get_tree().get_first_node_in_group("scatter") as Scatter
		for cell in (sc.tree_cells.values() if sc else []):
			var found := false
			for mmi in cell.get_children():
				if String(mmi.name).ends_with(args["goto_scatter"]) and mmi.has_meta("xforms") and not mmi.get_meta("xforms").is_empty():
					var xf: Transform3D = mmi.get_meta("xforms")[0]
					var p: Vector3 = xf.origin + Vector3(0, 0, 4.0)
					p.y = current_world.ground_height(p.x, p.z) + 0.3
					player.place_at(Transform3D(Basis(), p))
					print("SCATTER at ", mmi.name, " ", xf.origin)
					found = true
					break
			if found:
				break
	if args.has("goto_ore"):                               # testing: --goto_ore=gold stands by the first gold vein
		for n in current_world.find_children(args["goto_ore"] + "_vein_*", "Node3D", true, false):
			var p: Vector3 = n.global_position + Vector3(0, 0, 1.8)
			p.y = current_world.ground_height(p.x, p.z) + 0.3
			player.place_at(Transform3D(Basis(), p))
			print("ORE at ", n.name, " ", n.global_position)
			break
	if args.has("yaw"): player.cam_yaw = float(args["yaw"])
	if args.has("pitch"): player.cam_pitch = float(args["pitch"])
	if args.has("zoom"): player.target_zoom = float(args["zoom"])
	player.frozen = false
	busy = false
	if args.has("give"):                                   # testing: --give=maple_log,pine_log
		for id in args["give"].split(","):
			Inventory.gain(id, 3)
	if args.has("unlock_tools"):                           # testing: own every tool (the spare ones go in the grid)
		Inventory.test_unlock_tools()
	if args.has("equip"):                                  # testing: --equip=iron_axe, as if dragged onto its slot
		Inventory.hold(args["equip"])
		print("EQUIP held ", Inventory.held, " grid ", Inventory.items.keys().slice(0, 12))
	if args.has("drop_test"):                              # testing: drop 3 pine logs, walk onto them, report
		Inventory.gain("pine_log", 3)
		inventory_ui.drop("pine_log", 3)
		print("DROP after drop: ", Inventory.count("pine_log"))
		get_tree().create_timer(2.0).timeout.connect(func():
			for n in current_world.get_children():
				if n.get("id") == "pine_log":
					player.global_position = n.global_position + Vector3.UP * 0.3
			await get_tree().create_timer(0.5).timeout
			print("DROP after walking onto it: ", Inventory.count("pine_log")))
	if args.has("inventory_open"):                         # testing: open the inventory (with --shot)
		inventory_ui.visible = true
	if args.has("shot"):
		_take_screenshot(args["shot"], float(args.get("shot_delay", "6")))
	if args.has("perf"):
		_perf_probe(float(args["perf"]))
	if args.has("portal_test"):
		_portal_test()
	if args.has("bot"):
		_bot(float(args["bot"]))
	if args.has("tool"):                                   # testing: take out a tool kind, swing it at a moment
		Inventory.take_out(args["tool"])
		if args.has("swing_at"):
			get_tree().create_timer(float(args["swing_at"])).timeout.connect(func(): player.visual.play_action(args["tool"]))
	if args.has("regrow"):
		Lumbering.regrow = float(args["regrow"])
	if args.has("chop_time"):
		player.chopper.time_override = float(args["chop_time"])
	if args.has("chop_measure"):
		player.chopper.measure = true
	if args.has("axe"):                                    # testing: hold any axe
		Inventory.held["axe"] = args["axe"]
		Inventory.sync_tools()
	if args.has("mine_at"):
		get_tree().create_timer(float(args["mine_at"])).timeout.connect(func():
			Inventory.take_out("pickaxe")
			await get_tree().process_frame
			Inventory.looted.connect(func(id, n, rare): print("MINE got ", id, " x", n, " rare" if rare else ""))
			Inventory.message.connect(func(t): print("MINE message: ", t))
			print("MINE use -> ", player.miner.use(), " target ", player.miner.target))
	if args.has("chop_at"):
		get_tree().create_timer(float(args["chop_at"])).timeout.connect(_chop_test)
	if args.has("wallet") and not OS.has_feature("web"):   # desktop testing only: read that wallet's account
		ProfileUI.account.set_wallet(args["wallet"])
		if args.has("profile_open"):
			ProfileUI.open_menu()


func _unhandled_input(event: InputEvent) -> void:
	if event.is_action_pressed("inventory") and not event.is_echo():
		if inventory_ui.visible:
			inventory_ui.visible = false
		elif ProfileMenu.visible and not busy and free_cam == null:
			ProfileMenu.close()                                # opening a menu over another replaces it
			inventory_ui.visible = true
		elif not busy and free_cam == null and not player.menu_open():
			inventory_ui.visible = true
		get_viewport().set_input_as_handled()
		return
	if inventory_ui.visible and event is InputEventKey and event.pressed and event.keycode == KEY_ESCAPE:
		inventory_ui.visible = false
		get_viewport().set_input_as_handled()
		return
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
	## Fade to black, then the loading screen while the new world is built, then fade in to it.
	if busy:
		return
	set_camera_mode(false)
	inventory_ui.visible = false
	busy = true
	player.frozen = true
	player.chopper.stop()
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", 1.0, 0.4)
	await tw.finished
	await _enter_world(world_name, spawn_name)
	player.frozen = false
	busy = false


## The loading screen: load the world scene, build all of it (GameWorld.load_step) and only then join
## it, so it is not being built (and stuttering) while the player plays and other players see them.
func _enter_world(world_name: String, spawn_name: String) -> void:
	var t0 := Time.get_ticks_msec()
	joined_world = ""
	loading.open(LOADING_TITLES.get(world_name, "Loading"))
	fade_rect.color.a = 0.0
	await get_tree().process_frame                     # draw the loading screen before the heavy work
	await get_tree().process_frame
	var path: String = WORLDS[world_name]
	var packed: PackedScene = null
	if ResourceLoader.load_threaded_request(path) == OK:
		var p := []
		while ResourceLoader.load_threaded_get_status(path, p) == ResourceLoader.THREAD_LOAD_IN_PROGRESS:
			loading.set_progress(0.05 * float(p[0]) if p.size() > 0 else 0.0, "Loading the world")
			await get_tree().process_frame
		packed = ResourceLoader.load_threaded_get(path) as PackedScene
	loading.set_progress(0.05, "Shaping the land")
	await get_tree().process_frame
	_load_world(world_name, spawn_name, packed)        # the world's terrain data and spawn area
	var yaw: float = player.cam_yaw
	if current_world.has_method("load_step"):
		while true:
			var f: float = current_world.load_step(LOAD_BUDGET_USEC)
			loading.set_progress(0.05 + 0.9 * f, "Building the terrain" if f < 0.3 else "Growing trees and plants")
			player.cam_yaw += 0.4                      # turn the hidden camera: every material is compiled now
			if args.has("shot_loading") and f > 0.5:   # testing: a picture of the loading screen
				args.erase("shot_loading")
				await RenderingServer.frame_post_draw
				get_viewport().get_texture().get_image().save_png(ProjectSettings.globalize_path(args.get("shot", "res://loading.png")).get_base_dir() + "/loading_screen.png")
			await get_tree().process_frame
			if f >= 1.0:
				break
	player.cam_yaw = yaw
	for i in 4:                                        # settle: colliders, shaders of the last cells
		loading.set_progress(0.95 + 0.0125 * i, "Joining")
		await get_tree().process_frame
	loading.set_progress(1.0, "Joining")
	print("world %s: loaded in %d ms" % [world_name, Time.get_ticks_msec() - t0])
	joined_world = world_name
	fade_rect.color.a = 1.0
	loading.close()
	var tw := create_tween()
	tw.tween_property(fade_rect, "color:a", 0.0, 0.5)
	await tw.finished


func _load_world(world_name: String, spawn_name: String, packed: PackedScene = null) -> void:
	if current_world:
		world_holder.remove_child(current_world)
		current_world.queue_free()
	if packed == null:
		packed = load(WORLDS[world_name])
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
	for i in 3:                                   # frame_post_draw never fires while the window is hidden
		await get_tree().process_frame
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
		await get_tree().create_timer(1.0).timeout
		while busy:                                # the loading screen
			await get_tree().process_frame
		print("PORTAL_TEST now in ", joined_world)
	get_tree().quit()


func _bot(seconds: float) -> void:
	player.frozen = true
	await get_tree().create_timer(2.0).timeout
	var centre: Vector3 = player.global_position + (-player.visual.global_transform.basis.z) * 4.0
	var t := 0.0
	while t < seconds:
		await get_tree().physics_frame
		t += get_physics_process_delta_time()
		var d: Vector3 = centre + Vector3(cos(t * 0.8), 0, sin(t * 0.8)) * 1.5 - player.global_position
		d.y = 0.0
		player.velocity = Vector3(d.x * 4.0, player.velocity.y - 9.8 * get_physics_process_delta_time(), d.z * 4.0)
		player.move_and_slide()
		player.visual.rotation.y = atan2(-d.x, -d.z)
	print("bot: net ", Net.state, " as ", Net.my_name, ", ", Net.online, " online")
	get_tree().quit()


## Testing (--chop_at): walk up to the nearest choppable tree and start chopping it.
func _chop_test() -> void:
	Inventory.take_out("axe")
	var sc := get_tree().get_first_node_in_group("scatter") as Scatter
	var t := sc.find_tree(player.global_position, 60.0) if sc else {}
	if t.is_empty():
		print("CHOP no tree near the player")
		return
	var c: Vector3 = t.xform.origin
	var u := Vector3(player.global_position.x - c.x, 0, player.global_position.z - c.z).normalized()
	player.global_position = c + u * (float(t.trunk) + 1.0) + Vector3.UP * 0.5
	await get_tree().physics_frame
	await get_tree().physics_frame
	print("CHOP chopping %s (%s) at %s, %.1f s" % [t.tree, t.key, c, Lumbering.chop_time(t.tree, Inventory.held.axe)])
	player.chopper.start(t)


## Testing (--goto_mob with --follow): the player keeps standing beside the mob, to watch it walk.
func _follow(n: Node3D, dist: float) -> void:
	while is_instance_valid(n):
		var p := n.global_position + Vector3(dist * 0.5, 0, dist)
		p.y = current_world.ground_height(p.x, p.z) + 0.3
		player.global_position = p
		player.velocity = Vector3.ZERO
		player.cam_yaw = atan2(-(n.global_position.x - p.x), -(n.global_position.z - p.z)) + 0.35
		var mid: float = n.global_position.y + float(args.get("follow_h", "0.8"))   # aim at the mob's middle
		player.cam_pitch = clampf(-atan2(p.y + 2.0 - mid, Vector2(n.global_position.x - p.x, n.global_position.z - p.z).length() + float(player.target_zoom)), -1.2, 0.4)
		await get_tree().process_frame


## Testing (--goto_mob with --look_at): a free camera stays a few metres from the mob or bird, looking at it.
func _look_at(n: Node3D, dist: float) -> void:
	set_camera_mode(true)
	while is_instance_valid(n) and free_cam:
		var c := n.global_position + Vector3(dist * 0.6, dist * 0.35, dist * 0.75)
		free_cam.global_transform = Transform3D(Basis(), c).looking_at(n.global_position + Vector3.UP * 0.3, Vector3.UP)
		await get_tree().process_frame
