extends SceneTree
## Renders Impz from their Blockbench models (ImpBuilder, the same rig the game uses) to transparent PNGs
## for posters. Needs a window (headless runs don't draw):
##   godot --path godot-game -s ../tools/posters/render_impz.gd -- --out=<folder>
## Writes <folder>/<name>.png, 1024 x 1024, the Imp turned a little to its right, lit from the front left.

const SIZE := 1024
const YAW := -22.0           # degrees: a three-quarter view shows the wings and the face
const IMPZ := {
	"cyan_111": {body = "body_cyan", head = "head_afro", eyes = "eyes_gold_pupils", clothing = "", back = ""},
	"gold_408": {body = "body_gold", head = "", eyes = "eyes_gold_pupils", clothing = "clothing_robinhood_hoodie", back = "back_bone_wings"},
	"diamond_158": {body = "body_diamond", head = "head_spiky", eyes = "eyes_robo", clothing = "", back = "back_imp_wings"},
}


func _initialize() -> void:
	_run.call_deferred()


func _run() -> void:
	var out := "user://poster_impz"
	for a in OS.get_cmdline_user_args():
		if a.begins_with("--out="):
			out = a.trim_prefix("--out=")
	DirAccess.make_dir_recursive_absolute(out)

	var vp := SubViewport.new()
	vp.size = Vector2i(SIZE, SIZE)
	vp.transparent_bg = true
	vp.msaa_3d = Viewport.MSAA_4X
	vp.render_target_update_mode = SubViewport.UPDATE_ALWAYS
	root.add_child(vp)

	var env := WorldEnvironment.new()
	env.environment = Environment.new()
	env.environment.background_mode = Environment.BG_CLEAR_COLOR
	env.environment.ambient_light_source = Environment.AMBIENT_SOURCE_COLOR
	env.environment.ambient_light_color = Color(0.85, 0.85, 0.95)
	env.environment.ambient_light_energy = 0.75
	vp.add_child(env)
	var sun := DirectionalLight3D.new()
	sun.rotation_degrees = Vector3(-35, -40, 0)
	sun.light_energy = 1.1
	vp.add_child(sun)
	var cam := Camera3D.new()
	cam.projection = Camera3D.PROJECTION_ORTHOGONAL
	vp.add_child(cam)

	for name in IMPZ:
		var imp := ImpBuilder.build(IMPZ[name])
		imp.rotation_degrees.y = YAW
		vp.add_child(imp)
		await process_frame
		var box := _bounds(imp)
		var centre := box.get_center()
		cam.size = maxf(box.size.y, box.size.x) * 1.04
		cam.position = Vector3(centre.x, centre.y, centre.z + 200.0)
		cam.near = 1.0
		cam.far = 500.0
		for i in 4:
			await process_frame
		await RenderingServer.frame_post_draw
		var img := vp.get_texture().get_image()
		img.save_png(out.path_join(name + ".png"))
		print("rendered ", name, " ", box)
		imp.queue_free()
		await process_frame
	quit()


func _bounds(node: Node) -> AABB:
	var box := AABB()
	var first := true
	for m in node.find_children("*", "MeshInstance3D", true, false):
		var b: AABB = m.global_transform * m.get_aabb()
		box = b if first else box.merge(b)
		first = false
	return box
