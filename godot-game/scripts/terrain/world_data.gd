class_name WorldData
extends RefCounted
## Loads the baked world images and layout (scripts/tools/bake_world_data.gd) and answers height, depth,
## mask and biome queries. The PNGs are imported with "keep", so they ship as-is and load in the web build.

const BIOMES := ["hub", "forest", "mountain", "frost", "plains", "swamp"]

var layout: Dictionary
var biome_data: Dictionary
var nx := 0
var nz := 0
var step := 2.0
var origin := Vector2.ZERO
var size := Vector2.ZERO
var heights := PackedFloat32Array()
var depths := PackedFloat32Array()
var mask: Image
var fixed_biome := -1
var band := 256.0
var blend_half := 22.5
# skirt (resource world): cliffs and mountains outside the world, from data/<prefix>_skirt.png (bake_world_data.gd)
var has_skirt := false
var sk_origin := Vector2.ZERO
var sk_step := 4.0
var sk_nx := 0
var sk_nz := 0
var sk_heights := PackedFloat32Array()


func _init(prefix: String, biome_fixed := -1) -> void:
	fixed_biome = biome_fixed
	biome_data = JSON.parse_string(FileAccess.get_file_as_string("res://data/biomes.json"))
	band = biome_data["band_depth"]
	blend_half = biome_data["blend_half_width"]
	layout = JSON.parse_string(FileAccess.get_file_as_string("res://data/%s_layout.json" % prefix))
	step = layout["step"]
	origin = Vector2(layout["origin"][0], layout["origin"][1])
	size = Vector2(layout["size"][0], layout["size"][1])
	var img := _load_png("res://data/%s_terrain.png" % prefix)
	mask = _load_png("res://data/%s_mask.png" % prefix)
	nx = img.get_width()
	nz = img.get_height()
	heights.resize(nx * nz)
	depths.resize(nx * nz)
	var data := img.get_data()  # RGBA8
	var ho: float = layout["h_offset"]
	var hs: float = layout["h_scale"]
	var ss: float = layout.get("s_scale", 50.0)
	for i in nx * nz:
		heights[i] = (data[i * 4] * 256 + data[i * 4 + 1]) / hs - ho
		depths[i] = (data[i * 4 + 2] * 256 + data[i * 4 + 3]) / ss
	if layout.has("skirt"):
		var sk: Dictionary = layout["skirt"]
		var simg := _load_png("res://data/%s_skirt.png" % prefix)
		has_skirt = true
		sk_origin = Vector2(sk["origin"][0], sk["origin"][1])
		sk_step = sk["step"]
		sk_nx = simg.get_width()
		sk_nz = simg.get_height()
		var sdata := simg.get_data()
		var so: float = sk["h_offset"]
		var sc: float = sk["h_scale"]
		sk_heights.resize(sk_nx * sk_nz)
		for i in sk_nx * sk_nz:
			sk_heights[i] = (sdata[i * 4] * 256 + sdata[i * 4 + 1]) / sc - so


static func _load_png(path: String) -> Image:
	var img := Image.new()
	var err := img.load_png_from_buffer(FileAccess.get_file_as_bytes(path))
	assert(err == OK, "could not load " + path)
	img.convert(Image.FORMAT_RGBA8)
	return img


func _grid(x: float, z: float) -> Vector2:
	return Vector2(clamp((x - origin.x) / step, 0.0, nx - 1.001), clamp((z - origin.y) / step, 0.0, nz - 1.001))


func _bilinear(arr: PackedFloat32Array, x: float, z: float) -> float:
	var g := _grid(x, z)
	var ix := int(g.x)
	var iz := int(g.y)
	var fx := g.x - ix
	var fz := g.y - iz
	var i := iz * nx + ix
	var a: float = lerp(arr[i], arr[i + 1], fx)
	var b: float = lerp(arr[i + nx], arr[i + nx + 1], fx)
	return lerp(a, b, fz)


func height(x: float, z: float) -> float:
	if has_skirt and not in_bounds(x, z):
		return skirt_height(x, z)
	return _bilinear(heights, x, z)


func skirt_height(x: float, z: float) -> float:
	## Outside the world: Catmull-Rom (smooth, no 4 m creases) through the skirt samples, corrected over the first
	## 8 m so it meets the world's own border height exactly.
	var cx := clampf(x, origin.x, origin.x + size.x)
	var cz := clampf(z, origin.y, origin.y + size.y)
	var d := Vector2(x - cx, z - cz).length()
	var h := _skirt_cubic(x, z)
	if d < 8.0:
		h += (_bilinear(heights, cx, cz) - _skirt_cubic(cx, cz)) * (1.0 - smoothstep(0.0, 8.0, d))
	return h


func skirt_sample(i: int, j: int) -> float:
	## Raw skirt height at sample (i, j), clamped to the image (the far mesh reads these directly).
	return sk_heights[clampi(j, 0, sk_nz - 1) * sk_nx + clampi(i, 0, sk_nx - 1)]


func _skirt_cubic(x: float, z: float) -> float:
	var gx := (x - sk_origin.x) / sk_step
	var gz := (z - sk_origin.y) / sk_step
	var ix := floori(gx)
	var iz := floori(gz)
	var tx := gx - ix
	var tz := gz - iz
	var rows := PackedFloat32Array([0.0, 0.0, 0.0, 0.0])
	for r in 4:
		var j := iz - 1 + r
		rows[r] = _cr(skirt_sample(ix - 1, j), skirt_sample(ix, j), skirt_sample(ix + 1, j), skirt_sample(ix + 2, j), tx)
	return _cr(rows[0], rows[1], rows[2], rows[3], tz)


static func _cr(p0: float, p1: float, p2: float, p3: float, t: float) -> float:
	return p1 + 0.5 * t * (p2 - p0 + t * (2.0 * p0 - 5.0 * p1 + 4.0 * p2 - p3 + t * (3.0 * (p1 - p2) + p3 - p0)))


func depth(x: float, z: float) -> float:
	return _bilinear(depths, x, z)


func normal(x: float, z: float) -> Vector3:
	var hl := height(x - step, z)
	var hr := height(x + step, z)
	var hd := height(x, z - step)
	var hu := height(x, z + step)
	return Vector3(hl - hr, 2.0 * step, hd - hu).normalized()


func mask_at(x: float, z: float) -> Color:
	var px := clampi(int(x - origin.x), 0, mask.get_width() - 1)
	var pz := clampi(int(z - origin.y), 0, mask.get_height() - 1)
	return mask.get_pixel(px, pz)


func biome_index(x: float, z: float) -> int:
	## Dominant biome (0 hub, 1 forest ... 5 swamp).
	if fixed_biome >= 0:
		return fixed_biome
	return 1 + clampi(int(floor(depth(x, z) / band)), 0, 4)


func biome_name(x: float, z: float) -> String:
	return BIOMES[biome_index(x, z)]


func in_bounds(x: float, z: float, margin := 0.0) -> bool:
	return x >= origin.x + margin and z >= origin.y + margin and x <= origin.x + size.x - margin and z <= origin.y + size.y - margin


func biome_pick(x: float, z: float, r: float) -> int:
	## Same border rule as the terrain shader: inside a border zone pick one of the two biomes with the blend weight.
	if fixed_biome >= 0:
		return fixed_biome
	var s := depth(x, z)
	var i := clampi(int(floor(s / band)), 0, 4)
	var f := s - i * band
	if f > band - blend_half and i < 4 and r < (f - (band - blend_half)) / (2.0 * blend_half):
		return i + 2
	if f < blend_half and i > 0 and r < (blend_half - f) / (2.0 * blend_half):
		return i
	return i + 1


func water_level(x: float, z: float) -> float:
	## Highest water plane over this point, or -1000 if there is none.
	var lvl := -1000.0
	for w in layout.get("water", []):
		var r: Array = w["rect"]
		if x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]:
			lvl = maxf(lvl, float(w["level"]))
	return lvl
