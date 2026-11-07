extends RefCounted
## Effects for the tool use animations (imp_visual.gd ACTIONS): a fading swing trail that follows the
## tool's head, and bursts of chips at the moment of impact (stone chips and sparks for a pickaxe, wood
## chips for an axe, grass for a sickle). Everything here is plain cubes and an unshaded ribbon, so it
## stays cheap in the web build.


## A ribbon between two points on the tool (near the head and further in), drawn over the last
## `life` seconds and fading out behind the swing. Lives in world space (top level).
class Trail extends MeshInstance3D:
	var life := 0.16
	var color := Color(1, 1, 1, 0.55)
	var _samples: Array = []          # [time, outer point, inner point]
	var _im := ImmediateMesh.new()

	func _init() -> void:
		mesh = _im
		top_level = true
		cast_shadow = GeometryInstance3D.SHADOW_CASTING_SETTING_OFF
		var m := StandardMaterial3D.new()
		m.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
		m.vertex_color_use_as_albedo = true
		m.transparency = BaseMaterial3D.TRANSPARENCY_ALPHA
		m.cull_mode = BaseMaterial3D.CULL_DISABLED
		m.no_depth_test = false
		material_override = m

	func add(outer: Vector3, inner: Vector3) -> void:
		_samples.append([Time.get_ticks_msec() / 1000.0, outer, inner])

	func _process(_delta: float) -> void:
		var now := Time.get_ticks_msec() / 1000.0
		while not _samples.is_empty() and now - _samples[0][0] > life:
			_samples.pop_front()
		_im.clear_surfaces()
		global_transform = Transform3D.IDENTITY
		if _samples.size() < 2:
			return
		_im.surface_begin(Mesh.PRIMITIVE_TRIANGLE_STRIP)
		for s in _samples:
			var k := clampf(1.0 - (now - s[0]) / life, 0.0, 1.0)
			var c := color
			c.a *= k * k
			_im.surface_set_color(c)
			_im.surface_add_vertex(s[1])
			c.a *= 0.15
			_im.surface_set_color(c)
			_im.surface_add_vertex(s[2])
		_im.surface_end()


## A one-shot burst of little cubes at `pos` (world space), thrown up and out, falling and shrinking.
## `colors`: the colours to pick from. `glow`: unshaded (sparks).
static func burst(host: Node, pos: Vector3, colors: Array, count := 14, speed := 3.0, size := 0.05, glow := false) -> void:
	if host == null:
		return
	var p := CPUParticles3D.new()
	p.one_shot = true
	p.explosiveness = 0.95
	p.amount = count
	p.lifetime = 0.55 if glow else 0.8
	p.local_coords = false
	var m := BoxMesh.new()
	m.size = Vector3.ONE * size
	var mat := StandardMaterial3D.new()
	mat.vertex_color_use_as_albedo = true
	if glow:
		mat.shading_mode = BaseMaterial3D.SHADING_MODE_UNSHADED
	m.material = mat
	p.mesh = m
	p.direction = Vector3.UP
	p.spread = 70.0
	p.initial_velocity_min = speed * 0.45
	p.initial_velocity_max = speed
	p.gravity = Vector3(0, -9.8, 0)
	p.scale_amount_min = 0.5
	p.scale_amount_max = 1.3
	var shrink := Curve.new()
	shrink.add_point(Vector2(0, 1))
	shrink.add_point(Vector2(0.7, 0.8))
	shrink.add_point(Vector2(1, 0))
	p.scale_amount_curve = shrink
	var g := Gradient.new()
	g.offsets = PackedFloat32Array()
	g.colors = PackedColorArray()
	for i in colors.size():
		g.add_point(float(i) / maxf(colors.size() - 1, 1), colors[i])
	if g.get_point_count() > colors.size():
		g.remove_point(0)
	p.color_initial_ramp = g
	host.add_child(p)
	p.global_position = pos
	p.emitting = true
	host.get_tree().create_timer(1.6).timeout.connect(p.queue_free)
