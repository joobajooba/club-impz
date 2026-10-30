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
	return _bilinear(heights, x, z)


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
