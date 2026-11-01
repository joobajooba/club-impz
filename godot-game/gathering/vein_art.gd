class_name VeinArt
## Ore veins for every tier but Copper, built in code in the Stylized Ore look (D-019, ART-DIRECTION 9.1):
## a calm, faceted rock body, lighter on top, with the tier's ore set into it as the bright accent.
## Each tier has its own silhouette, so tiers read by shape as well as colour:
##   Tin: a small, low pile with pale nuggets · Iron: a low mound with metal nuggets · Coal: stacked slabs with black lumps
##   Gold: a round mound studded with gold · Obsidian: glassy black shards
##   Titanite: a lilac crystal cluster · Dreadstone: jagged red-veined spires
##   Void Stone: orbs spiralling up a rock (its icon is a spiral) · Stellarite: twin spires with blue crystals
## Colours come from GameData.ORE_LOOKS, which were taken from each ore picture. Veins get bigger
## with the tier. Every vein stands on y = 0, about a metre across.

const ROCK_SIDES := 6


static func build(row: Dictionary) -> Node3D:
	var look: Dictionary = row.look
	var rng := RandomNumberGenerator.new()
	rng.seed = hash(row.id)
	var root := Node3D.new()
	var top := Color(look.top)
	var side := Color(look.side)
	var ore := _ore_mat(look)
	var s := 0.75 + (int(row.tier) - 3) * 0.04
	match row.id:
		"tin":                              # the smallest vein: two low rocks with a few nuggets
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.42, 0.3, 0.38), 0.6)
			_rock(root, rng, top, side, Vector3(0.3, 0, 0.16), Vector3(0.22, 0.18, 0.2), 0.65)
			for k in 9:
				_nugget(root, rng, ore, _on_mound(rng, Vector3(0.42, 0.3, 0.38), 0.6, k), 0.09 + rng.randf() * 0.04)
		"iron":
			_rock(root, rng, top, side, Vector3(0, 0, 0), Vector3(0.5, 0.42, 0.45), 0.55)
			_rock(root, rng, top, side, Vector3(0.36, 0, -0.12), Vector3(0.28, 0.26, 0.26), 0.6)
			_rock(root, rng, top, side, Vector3(-0.3, 0, 0.2), Vector3(0.22, 0.2, 0.22), 0.6)
			for k in 10:
				_nugget(root, rng, ore, _on_mound(rng, Vector3(0.5, 0.42, 0.45), 0.55, k), 0.08 + rng.randf() * 0.05)
		"coal":
			for k in 4:                     # flat slabs stacked a little off-centre
				var w := 0.55 - k * 0.1
				_rock(root, rng, top, side, Vector3(rng.randf_range(-0.06, 0.06), k * 0.15, rng.randf_range(-0.06, 0.06)),
						Vector3(w, 0.17, w * 0.85), 0.92, rng.randf() * TAU)
			for k in 8:
				var a := rng.randf() * TAU
				var y := rng.randf_range(0.05, 0.55)
				var r := 0.55 - y * 0.55
				_nugget(root, rng, ore, Vector3(cos(a) * r, y, sin(a) * r), 0.07 + rng.randf() * 0.05)
		"gold":
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.52, 0.5, 0.5), 0.45)
			_rock(root, rng, top, side, Vector3(-0.32, 0, -0.2), Vector3(0.26, 0.3, 0.26), 0.5)
			for k in 13:
				_nugget(root, rng, ore, _on_mound(rng, Vector3(0.52, 0.5, 0.5), 0.45, k), 0.08 + rng.randf() * 0.05)
		"obsidian":
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.5, 0.3, 0.45), 0.6)
			for k in 6:                     # glassy shards leaning out
				var a := k * TAU / 6.0 + rng.randf() * 0.4
				var lean := Vector3(cos(a), 0, sin(a)) * rng.randf_range(0.25, 0.5)
				_crystal(root, rng, look.ore, look.top, Vector3(cos(a) * 0.15, 0.18, sin(a) * 0.15), lean,
						rng.randf_range(0.35, 0.6), rng.randf_range(0.06, 0.09), 4, look)
			_crystal(root, rng, look.ore, look.top, Vector3(0, 0.2, 0), Vector3.ZERO, 0.75, 0.1, 4, look)
		"titanite":
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.45, 0.28, 0.42), 0.6)
			_rock(root, rng, top, side, Vector3(0.3, 0, 0.2), Vector3(0.2, 0.18, 0.2), 0.6)
			for k in 7:                     # a cluster of two-tone crystals (ART-DIRECTION 5)
				var a := k * TAU / 7.0 + rng.randf() * 0.5
				var out := 0.0 if k == 0 else rng.randf_range(0.08, 0.22)
				_crystal(root, rng, look.top, look.ore, Vector3(cos(a) * out, 0.15, sin(a) * out),
						Vector3(cos(a), 0, sin(a)) * out * 1.4, 0.75 - out * 1.6, 0.075, 6, look)
		"dreadstone":
			for k in 4:                     # jagged spires of different heights
				var a := k * TAU / 4.0 + 0.4
				var r := 0.0 if k == 0 else 0.26
				_rock(root, rng, top, side, Vector3(cos(a) * r, 0, sin(a) * r),
						Vector3(0.24, 0.95 - k * 0.15, 0.24), 0.15, rng.randf() * TAU, 5)
			for k in 12:
				var a := rng.randf() * TAU
				var y := rng.randf_range(0.1, 0.65)
				_nugget(root, rng, ore, Vector3(cos(a) * 0.24, y, sin(a) * 0.24), 0.07 + rng.randf() * 0.04)
		"void":
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.42, 0.95, 0.4), 0.35)
			_rock(root, rng, top, side, Vector3(0.3, 0, -0.25), Vector3(0.22, 0.32, 0.22), 0.5)
			for k in 14:                    # orbs spiralling up the rock, like its icon
				var u := k / 13.0
				var a := u * TAU * 1.6
				var r := 0.4 * (1.0 - u * 0.62)
				_orb(root, ore, Vector3(cos(a) * r, 0.08 + u * 0.85, sin(a) * r), 0.05 + 0.03 * (1.0 - u))
		"stellarite":
			_rock(root, rng, top, side, Vector3(-0.14, 0, 0), Vector3(0.3, 1.05, 0.3), 0.2, 0.0, 5)
			_rock(root, rng, top, side, Vector3(0.2, 0, 0.1), Vector3(0.26, 0.8, 0.26), 0.2, 1.0, 5)
			_rock(root, rng, top, side, Vector3(0.05, 0, -0.25), Vector3(0.3, 0.3, 0.3), 0.5)
			for k in 6:
				var a := k * TAU / 6.0
				_crystal(root, rng, look.top, look.ore, Vector3(cos(a) * 0.3, 0.05, sin(a) * 0.3),
						Vector3(cos(a), 0.2, sin(a)) * 0.5, rng.randf_range(0.3, 0.45), 0.07, 6, look)
			for k in 3:
				_crystal(root, rng, look.top, look.ore, Vector3(-0.14 + k * 0.17, 0.6 + k * 0.1, 0.12),
						Vector3(0, 0, 1.0), 0.28, 0.06, 6, look)
		_:
			_rock(root, rng, top, side, Vector3.ZERO, Vector3(0.5, 0.5, 0.5), 0.5)
	root.scale = Vector3.ONE * s
	var holder := Node3D.new()
	holder.add_child(root)
	return holder


## A point on the face of a rock built by _rock with this size and top width, spread around by k,
## so a nugget sits half in, half out of the rock.
static func _on_mound(rng: RandomNumberGenerator, size: Vector3, top_k: float, k: int) -> Vector3:
	var a := k * 2.4 + rng.randf() * 0.5
	var h := rng.randf_range(0.15, 0.85)
	var r := lerpf(1.0, top_k, h) * 0.95
	return Vector3(cos(a) * size.x * r, h * size.y, sin(a) * size.z * r)


# --- rock ----------------------------------------------------------------------------

## A faceted rock: `sides` around, three rings up, narrowing to `top_k` of its width at the top.
## Vertex colours run from the side colour at the base to the top colour, with the facing-up faces
## lightest (the painted top-to-bottom gradient). Facets stay crisp but slightly softened.
static func _rock(root: Node3D, rng: RandomNumberGenerator, top: Color, side: Color, pos: Vector3,
		size: Vector3, top_k: float, turn := 0.0, sides := ROCK_SIDES) -> void:
	var rings := [[0.0, 1.0], [0.45, 0.92], [0.8, lerpf(0.92, top_k, 0.6)], [1.0, top_k]]
	var pts := []                                 # [ring][side] -> Vector3
	for ring in rings:
		var row := []
		for i in sides:
			var a := turn + TAU * i / sides + rng.randf_range(-0.2, 0.2)
			var r: float = ring[1] * rng.randf_range(0.85, 1.08)
			var y: float = ring[0] * size.y + (rng.randf_range(-0.04, 0.04) if ring[0] > 0.0 else 0.0)
			row.append(Vector3(cos(a) * size.x * r, y, sin(a) * size.z * r))
		pts.append(row)
	var apex := Vector3(rng.randf_range(-0.05, 0.05), size.y * 1.04, rng.randf_range(-0.05, 0.05))
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for r in rings.size() - 1:
		for i in sides:
			var j := (i + 1) % sides
			_quad(st, pts[r][i], pts[r][j], pts[r + 1][j], pts[r + 1][i], top, side, size.y)
	for i in sides:                               # the top cap
		_tri(st, pts[-1][i], apex, pts[-1][(i + 1) % sides], top, side, size.y)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.roughness = 0.9
	mi.material_override = m
	mi.position = pos
	root.add_child(mi)


static func _quad(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, d: Vector3, top: Color, side: Color, h: float) -> void:
	_tri(st, a, c, b, top, side, h)
	_tri(st, a, d, c, top, side, h)


static func _tri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, top: Color, side: Color, h: float) -> void:
	var n := (b - a).cross(c - a).normalized()
	var mid := (a + b + c) / 3.0
	for v: Vector3 in _front(a, b, c, n):
		# the face normal, softened a little towards the vertex direction so facets look bevelled
		var soft := (n * 0.75 + Vector3(v.x, maxf(v.y - h * 0.4, 0.0), v.z).normalized() * 0.25).normalized()
		var up := clampf(n.y * 0.6 + v.y / maxf(h, 0.01) * 0.6, 0.0, 1.0)
		var col := side.darkened(0.1).lerp(top.lightened(0.22), up)
		col = col.lerp(Color("#3a3a6a"), 0.12 * (1.0 - up))   # cool, coloured shadow at the base
		if v.distance_to(mid) > 0.0 and n.y > 0.6:
			col = col.lightened(0.06)
		st.set_color(col)
		st.set_normal(soft)
		st.add_vertex(v)


## The triangle's corners in the order Godot draws as the front face (clockwise seen from outside),
## for a face whose outside is towards `n`.
static func _front(a: Vector3, b: Vector3, c: Vector3, n: Vector3) -> Array:
	return [a, c, b] if (b - a).cross(c - a).dot(n) > 0.0 else [a, b, c]


# --- ore -----------------------------------------------------------------------------

static func _ore_mat(look: Dictionary) -> StandardMaterial3D:
	var m := StandardMaterial3D.new()
	m.albedo_color = Color(look.ore)
	m.metallic = look.metal
	m.roughness = look.rough
	if look.has("glow"):
		m.emission_enabled = true
		m.emission = Color(look.glow)
		m.emission_energy_multiplier = 1.4
	return m


## A chunky nugget sunk partly into the rock: a squashed, jittered octahedron.
static func _nugget(root: Node3D, rng: RandomNumberGenerator, mat: Material, pos: Vector3, r: float) -> void:
	var dirs := [Vector3.UP, Vector3.DOWN, Vector3.LEFT, Vector3.RIGHT, Vector3.FORWARD, Vector3.BACK]
	var v := []
	for d: Vector3 in dirs:
		v.append(d * r * rng.randf_range(0.75, 1.2))
	var faces := [[0, 2, 4], [0, 4, 3], [0, 3, 5], [0, 5, 2], [1, 4, 2], [1, 3, 4], [1, 5, 3], [1, 2, 5]]
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	for f in faces:
		var a: Vector3 = v[f[0]]
		var b: Vector3 = v[f[1]]
		var c: Vector3 = v[f[2]]
		var n := (b - a).cross(c - a).normalized()
		if n.dot(a + b + c) < 0.0:
			n = -n
		for p: Vector3 in _front(a, b, c, n):
			st.set_normal((n * 0.6 + p.normalized() * 0.4).normalized())
			st.add_vertex(p)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	mi.material_override = mat
	mi.position = pos
	mi.rotation = Vector3(rng.randf() * TAU, rng.randf() * TAU, 0)
	root.add_child(mi)


## A crystal: a prism with a pointed tip, `sides` faces round, two-tone from `base` to `tip`
## colour, brightest at the tip. It grows from `pos` leaning towards `lean`.
static func _crystal(root: Node3D, rng: RandomNumberGenerator, base: String, tip: String, pos: Vector3,
		lean: Vector3, length: float, r: float, sides: int, look: Dictionary) -> void:
	var st := SurfaceTool.new()
	st.begin(Mesh.PRIMITIVE_TRIANGLES)
	var cb := Color(base)
	var ct := Color(tip).lightened(0.15)
	var body := length * 0.78
	var ring0 := []
	var ring1 := []
	for i in sides:
		var a := TAU * i / sides
		ring0.append(Vector3(cos(a) * r, 0, sin(a) * r))
		ring1.append(Vector3(cos(a) * r * 0.92, body, sin(a) * r * 0.92))
	var point := Vector3(0, length, 0)
	for i in sides:
		var j := (i + 1) % sides
		_ctri(st, ring0[i], ring1[j], ring0[j], cb, cb.lerp(ct, 0.7), length)
		_ctri(st, ring0[i], ring1[i], ring1[j], cb, cb.lerp(ct, 0.7), length)
		_ctri(st, ring1[i], point, ring1[j], cb, ct, length)
	var mi := MeshInstance3D.new()
	mi.mesh = st.commit()
	var m := StandardMaterial3D.new()
	m.vertex_color_use_as_albedo = true
	m.vertex_color_is_srgb = true
	m.metallic = minf(look.metal, 0.4)
	m.roughness = 0.15
	if look.has("glow"):
		m.emission_enabled = true
		m.emission = Color(look.glow)
		m.emission_energy_multiplier = 1.6
	mi.material_override = m
	mi.position = pos
	var up := (Vector3.UP + lean).normalized()
	var axis := Vector3.UP.cross(up)
	if axis.length() > 0.001:
		mi.basis = Basis(axis.normalized(), Vector3.UP.angle_to(up))
	mi.rotate_object_local(Vector3.UP, rng.randf() * TAU)
	root.add_child(mi)


static func _ctri(st: SurfaceTool, a: Vector3, b: Vector3, c: Vector3, cb: Color, ct: Color, length: float) -> void:
	var n := (b - a).cross(c - a).normalized()
	var mid := (a + b + c) / 3.0
	if n.dot(Vector3(mid.x, 0.0, mid.z)) < 0.0:
		n = -n
	for v: Vector3 in _front(a, b, c, n):
		st.set_color(cb.lerp(ct, clampf(v.y / length, 0.0, 1.0)))
		st.set_normal(n)
		st.add_vertex(v)


## A glowing orb (Void Stone).
static func _orb(root: Node3D, mat: StandardMaterial3D, pos: Vector3, r: float) -> void:
	var mesh := SphereMesh.new()
	mesh.radius = r
	mesh.height = r * 2.0
	mesh.radial_segments = 8
	mesh.rings = 4
	mesh.material = mat
	var mi := MeshInstance3D.new()
	mi.mesh = mesh
	mi.position = pos
	root.add_child(mi)
