extends SceneTree
## Bakes the world layout images and JSON from fixed-seed noise, so every load is the same.
## Run from godot-game/:   godot --headless --path . --script res://scripts/tools/bake_world_data.gd
##
## Outputs (docs/world_build_notes.md explains the formats; J00BA can repaint the masks):
##   data/resource_terrain.png  641 x 257, 2 m per pixel. RG = height (16 bit), BA = warped depth "s" (16 bit)
##   data/resource_mask.png     1280 x 512, 1 m per pixel. R path, G wet / low ground, B special patch, A leaf litter / tree clusters
##   data/resource_layout.json  path lines, landmarks, water planes, river, ore spots
##   data/hub_terrain.png, data/hub_mask.png, data/hub_layout.json   same for the 200 x 200 m hub

const STEP := 2.0
const H_OFFSET := 20.0      # height encoding: value = (h + 20) * 200
const H_SCALE := 200.0
const S_SCALE := 50.0       # depth encoding: value = s * 50

# ---------------------------------------------------------------- resource world (x = depth 0..1280, z = -256..256)
const RW := 1280.0
const RD := 512.0
const BAND := 256.0
const BLEND := 22.5
const WATER := [
	{"name": "forest_river", "rect": [0, 40, 214, 120], "level": 3.0, "biome": "forest"},
	{"name": "forest_upper_pool", "rect": [214, 40, 262, 120], "level": 10.0, "biome": "forest"},
	{"name": "frost_open_pool", "rect": [690, -56, 722, -24], "level": 6.4, "biome": "frost"},
	{"name": "plains_watering_hole", "rect": [880, 40, 920, 80], "level": 9.0, "biome": "plains"},
	{"name": "swamp_water", "rect": [1010, -256, 1280, 256], "level": 1.75, "biome": "swamp"}
]

var n_warp := FastNoiseLite.new()
var n_hill := FastNoiseLite.new()
var n_ridge := FastNoiseLite.new()
var n_detail := FastNoiseLite.new()
var n_mesa := FastNoiseLite.new()
var n_island := FastNoiseLite.new()
var n_litter := FastNoiseLite.new()

var landmarks := {}
var main_path := PackedVector2Array()
var branches := []
var path_dist := PackedFloat32Array()  # coarse distance to the main path at 2 m (used to flatten the mountain pass)


func _init() -> void:
	_setup_noise()
	_build_resource_layout()
	_bake_resource()
	_bake_hub()
	print("bake done")
	quit()


func _setup_noise() -> void:
	var seeds := [101, 202, 303, 404, 505, 606, 707]
	var all := [n_warp, n_hill, n_ridge, n_detail, n_mesa, n_island, n_litter]
	for i in all.size():
		all[i].seed = seeds[i]
		all[i].noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n_warp.frequency = 1.0 / 90.0
	n_hill.frequency = 1.0 / 140.0
	n_hill.fractal_octaves = 4
	n_ridge.frequency = 1.0 / 110.0
	n_ridge.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	n_ridge.fractal_octaves = 4
	n_detail.frequency = 1.0 / 28.0
	n_mesa.frequency = 1.0 / 70.0
	n_island.frequency = 1.0 / 45.0
	n_litter.frequency = 1.0 / 40.0


# ---------------------------------------------------------------- layout
func river_z(x: float) -> float:
	return 80.0 + 25.0 * sin(x / 55.0)


func path_z(x: float) -> float:
	return 24.0 * sin(x / 110.0) + 12.0 * sin(x / 47.0 + 1.0)


func _build_resource_layout() -> void:
	landmarks = {
		"portal_clearing": Vector2(36, 0),
		"worldbark_grove": Vector2(150, 160), "waterfall": Vector2(214, river_z(214)), "stone_ruin": Vector2(110, -140),
		"highest_peak": Vector2(392, -168), "standing_stones": Vector2(330, 118), "obsidian_cave": Vector2(468, 172),
		"frozen_waterfall": Vector2(604, -186), "ice_spire": Vector2(712, 150), "frozen_lake": Vector2(650, 52),
		"stone_arch": Vector2(880, -64), "pillar_ring": Vector2(946, 138), "giant_titanwood": Vector2(820, 176),
		"gembark_grove": Vector2(990, -176),
		"hollow_tree": Vector2(1150, 70), "dreadstone_pit": Vector2(1200, -150), "sunken_ruins": Vector2(1086, -116),
	}
	var x := 36.0
	while x <= 1240.0:
		main_path.append(Vector2(x, path_z(x) * clamp((x - 36.0) / 40.0, 0.0, 1.0)))
		x += 4.0
	for key in ["worldbark_grove", "stone_ruin", "standing_stones", "obsidian_cave", "frozen_waterfall", "ice_spire",
			"frozen_lake", "stone_arch", "pillar_ring", "gembark_grove", "hollow_tree", "dreadstone_pit", "sunken_ruins"]:
		var target: Vector2 = landmarks[key]
		var start := Vector2(target.x, path_z(target.x))
		var pts := PackedVector2Array()
		var steps := int(start.distance_to(target) / 4.0) + 1
		for i in steps + 1:
			var t := float(i) / steps
			var p := start.lerp(target, t)
			p.x += sin(t * PI) * 14.0 * (1.0 if int(target.y) % 2 == 0 else -1.0)  # gentle curve
			pts.append(p)
		branches.append({"to": key, "points": pts})


func biome_blend(s: float) -> Array:
	## -> [biome index a (0..4), biome index b, weight of b]
	var band := s / BAND
	var i := clampi(int(floor(band)), 0, 4)
	var f := s - i * BAND
	if f > BAND - BLEND and i < 4:
		return [i, i + 1, clamp((f - (BAND - BLEND)) / (2.0 * BLEND), 0.0, 1.0)]
	if f < BLEND and i > 0:
		return [i, i - 1, clamp((BLEND - f) / (2.0 * BLEND), 0.0, 1.0)]
	return [i, i, 0.0]


func warped_s(x: float, z: float) -> float:
	return x + n_warp.get_noise_2d(x * 0.3, z) * 26.0


func g2(x: float, z: float, c: Vector2, sigma: float) -> float:
	var d2 := (x - c.x) * (x - c.x) + (z - c.y) * (z - c.y)
	return exp(-d2 / (2.0 * sigma * sigma))


func h_forest(x: float, z: float) -> float:
	var h := 6.0 + n_hill.get_noise_2d(x, z) * 7.0 + n_detail.get_noise_2d(x, z) * 0.8
	h += g2(x, z, landmarks["stone_ruin"], 22.0) * 9.0
	h += smoothstep(195.0, 226.0, x) * 7.0  # rises towards the mountain; the river falls off it (waterfall)
	# winding river: lower river (water 3.0) below the waterfall, upper pool (water 10.0) above it
	var dz := absf(z - river_z(x))
	var water := 3.0 if x < 214.0 else 10.0
	var bed := water - 1.3
	var strength := 1.0 - smoothstep(246.0, 268.0, x)
	if strength > 0.0 and dz < 18.0:
		var k := smoothstep(4.5, 11.0, dz)
		var carved: float = lerp(bed, maxf(h, water + 1.2), k)
		h = lerp(h, carved, strength * (1.0 - smoothstep(12.0, 18.0, dz)))
	return h


func h_mountain(x: float, z: float) -> float:
	var h := 18.0 + (n_ridge.get_noise_2d(x, z) * 0.5 + 0.5) * 58.0 + n_detail.get_noise_2d(x, z) * 2.0
	h += g2(x, z, landmarks["highest_peak"], 46.0) * 105.0
	h += g2(x, z, Vector2(470, -60), 30.0) * 40.0
	h -= g2(x, z, landmarks["obsidian_cave"], 18.0) * 14.0  # volcanic hollow round the obsidian cave
	return h


func h_frost(x: float, z: float) -> float:
	var h := 9.0 + n_hill.get_noise_2d(x, z) * 4.0 + n_detail.get_noise_2d(x * 2.0, z) * 0.6
	# ice cliffs along the south side, with the frozen waterfall on their face
	h += smoothstep(-150.0, -175.0, z) * 24.0
	# frozen lake (flat ice) and a small open pool
	var dl := Vector2(x, z).distance_to(landmarks["frozen_lake"])
	h = lerp(6.0, h, smoothstep(44.0, 62.0, dl))
	var dp := Vector2(x, z).distance_to(Vector2(706, -40))
	h = lerp(5.2, h, smoothstep(8.0, 16.0, dp))
	h += g2(x, z, landmarks["ice_spire"], 14.0) * 10.0
	return h


func h_plains(x: float, z: float) -> float:
	var h := 10.0 + n_hill.get_noise_2d(x * 0.8, z * 0.8) * 5.0
	var mesa := smoothstep(0.42, 0.5, n_mesa.get_noise_2d(x, z))
	h += mesa * 17.0
	# dry riverbed
	var rz := -120.0 + 40.0 * sin(x / 70.0)
	h -= (1.0 - smoothstep(3.0, 9.0, absf(z - rz))) * 1.8
	# watering hole
	var dw := Vector2(x, z).distance_to(Vector2(900, 60))
	h = lerp(8.0, h, smoothstep(10.0, 22.0, dw))
	# keep the arch and pillar ring sites flat
	for key in ["stone_arch", "pillar_ring"]:
		var d := Vector2(x, z).distance_to(landmarks[key])
		h = lerp(10.0, h, smoothstep(20.0, 34.0, d))
	return h


func h_swamp(x: float, z: float) -> float:
	var h := 1.9 + n_hill.get_noise_2d(x * 1.5, z * 1.5) * 1.1 + n_detail.get_noise_2d(x, z) * 0.3
	h += smoothstep(0.25, 0.45, n_island.get_noise_2d(x, z)) * 2.2
	h += g2(x, z, landmarks["hollow_tree"], 22.0) * 2.5
	h -= g2(x, z, landmarks["dreadstone_pit"], 16.0) * 2.0
	return h


func height_at(x: float, z: float, s: float, d_path: float) -> float:
	var bb := biome_blend(s)
	var ha := _h_biome(bb[0], x, z)
	var h := ha if bb[2] <= 0.0 else lerp(ha, _h_biome(bb[1], x, z), smoothstep(0.0, 1.0, bb[2]))
	# main path: keep it walkable (mountain pass, mesa edges)
	var ph := 8.0 + smoothstep(240.0, 300.0, x) * 14.0 - smoothstep(470.0, 530.0, x) * 12.0 - smoothstep(1000.0, 1050.0, x) * 8.0
	if x > 200.0 and x < 560.0:
		h = lerp(maxf(ph, minf(h, ph + 4.0)), h, smoothstep(7.0, 48.0, d_path))
	elif x > 760.0 and x < 1030.0:
		h = lerp(minf(h, 14.0), h, smoothstep(6.0, 20.0, d_path))
	# portal clearing: flat
	h = lerp(6.0, h, smoothstep(12.0, 26.0, Vector2(x, z).distance_to(landmarks["portal_clearing"])))
	# ring of tall mountains round the edge
	var e := minf(minf(z + RD / 2.0, RD / 2.0 - z), minf(x + 10.0, RW - x))
	h += (1.0 - smoothstep(6.0, 46.0, e)) * (60.0 + n_detail.get_noise_2d(x, z) * 12.0)
	return h


func _h_biome(i: int, x: float, z: float) -> float:
	match i:
		0: return h_forest(x, z)
		1: return h_mountain(x, z)
		2: return h_frost(x, z)
		3: return h_plains(x, z)
		_: return h_swamp(x, z)


func _bake_resource() -> void:
	var nx := int(RW / STEP) + 1
	var nz := int(RD / STEP) + 1
	# coarse distance to the main path on the 2 m grid
	path_dist.resize(nx * nz)
	path_dist.fill(9999.0)
	var path_pts := PackedVector2Array(main_path)
	for br in branches:
		path_pts.append_array(br["points"])
	for p in path_pts:
		var r := 50.0
		for gz in range(maxi(0, int((p.y + RD / 2.0 - r) / STEP)), mini(nz, int((p.y + RD / 2.0 + r) / STEP) + 1)):
			for gx in range(maxi(0, int((p.x - r) / STEP)), mini(nx, int((p.x + r) / STEP) + 1)):
				var d := Vector2(gx * STEP, gz * STEP - RD / 2.0).distance_to(p)
				var k := gz * nx + gx
				if d < path_dist[k]:
					path_dist[k] = d
	var hs := PackedFloat32Array()
	var ss := PackedFloat32Array()
	hs.resize(nx * nz)
	ss.resize(nx * nz)
	for gz in nz:
		for gx in nx:
			var x := gx * STEP
			var z := gz * STEP - RD / 2.0
			var s := warped_s(x, z)
			ss[gz * nx + gx] = s
			hs[gz * nx + gx] = height_at(x, z, s, path_dist[gz * nx + gx])
	_post_process(hs, nx, nz)
	var img := Image.create(nx, nz, false, Image.FORMAT_RGBA8)
	for k in nx * nz:
		var hv := clampi(int(round((hs[k] + H_OFFSET) * H_SCALE)), 0, 65535)
		var sv := clampi(int(round(ss[k] * S_SCALE)), 0, 65535)
		img.set_pixel(k % nx, k / nx, Color8(hv >> 8, hv & 255, sv >> 8, sv & 255))
	img.save_png(ProjectSettings.globalize_path("res://data/resource_terrain.png"))

	# mask, 1 m per pixel
	var mw := int(RW)
	var md := int(RD)
	var mask := Image.create(mw, md, false, Image.FORMAT_RGBA8)
	for mz in md:
		for mx in mw:
			var x := mx + 0.5
			var z := mz + 0.5 - RD / 2.0
			var s := warped_s(x, z)
			var b: int = biome_blend(s)[0]
			var wet := 0.0
			var special := 0.0
			if x < 262.0:
				wet = 1.0 - smoothstep(6.0, 10.0, absf(z - river_z(x)))
			var dl := Vector2(x, z).distance_to(landmarks["frozen_lake"])
			wet = maxf(wet, 1.0 - smoothstep(48.0, 54.0, dl))
			wet = maxf(wet, 1.0 - smoothstep(10.0, 13.0, Vector2(x, z).distance_to(Vector2(706, -40))))
			if x > 760.0 and x < 1030.0:
				wet = maxf(wet, 1.0 - smoothstep(4.0, 7.0, absf(z - (-120.0 + 40.0 * sin(x / 70.0)))))
				special = 1.0 - smoothstep(18.0, 30.0, Vector2(x, z).distance_to(Vector2(900, 60)))
			special = maxf(special, 1.0 - smoothstep(24.0, 38.0, Vector2(x, z).distance_to(landmarks["dreadstone_pit"])))
			var litter := clampf(n_litter.get_noise_2d(x, z) * 1.6 + 0.1, 0.0, 1.0) if b == 0 else 0.0
			mask.set_pixel(mx, mz, Color(0.0, wet, special, litter))
	# paths stamped along the main line and the branches
	_stamp_path(mask, main_path, 2.6, Vector2(0, RD / 2.0))
	for br in branches:
		_stamp_path(mask, br["points"], 1.7, Vector2(0, RD / 2.0))
	mask.save_png(ProjectSettings.globalize_path("res://data/resource_mask.png"))

	var layout := {
		"size": [RW, RD], "origin": [0.0, -RD / 2.0], "step": STEP, "h_offset": H_OFFSET, "h_scale": H_SCALE, "s_scale": S_SCALE,
		"landmarks": _v2dict(landmarks), "main_path": _pts(main_path),
		"branches": branches.map(func(b): return {"to": b["to"], "points": _pts(b["points"])}),
		"water": WATER,
		"waterfall": {"x": 214.0, "z": river_z(214), "top": 10.0, "bottom": 3.0},
		"spawn_point": [36.0, 0.0],
	}
	var f := FileAccess.open("res://data/resource_layout.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(layout, "  "))
	f.close()


func _stamp_path(mask: Image, pts: PackedVector2Array, radius: float, offset: Vector2) -> void:
	for i in pts.size() - 1:
		var a := pts[i]
		var b := pts[i + 1]
		var n := int(a.distance_to(b)) + 1
		for k in n + 1:
			var p := a.lerp(b, float(k) / n) + offset
			for dz in range(-int(radius) - 2, int(radius) + 3):
				for dx in range(-int(radius) - 2, int(radius) + 3):
					var px := int(p.x) + dx
					var pz := int(p.y) + dz
					if px < 0 or pz < 0 or px >= mask.get_width() or pz >= mask.get_height():
						continue
					var d := Vector2(px + 0.5, pz + 0.5).distance_to(p)
					var v := 1.0 - smoothstep(radius - 0.8, radius + 0.8, d)
					var c := mask.get_pixel(px, pz)
					if v > c.r:
						c.r = v
						mask.set_pixel(px, pz, c)


func _pts(a: PackedVector2Array) -> Array:
	var out := []
	for p in a:
		out.append([snappedf(p.x, 0.1), snappedf(p.y, 0.1)])
	return out


func _v2dict(d: Dictionary) -> Dictionary:
	var out := {}
	for k in d:
		out[k] = [snappedf(d[k].x, 0.1), snappedf(d[k].y, 0.1)]
	return out


# ---------------------------------------------------------------- hub (200 x 200 m, centred on 0, 0)
const HW := 200.0

func _bake_hub() -> void:
	var lm := {
		"spawn_point": Vector2(0, 46), "village_square": Vector2(0, 8), "castle": Vector2(0, -52),
		"market": Vector2(40, 12), "crafting_area": Vector2(-40, 12), "portal": Vector2(58, 58),
	}
	var paths := [
		[lm["spawn_point"], lm["village_square"]], [lm["village_square"], lm["castle"]],
		[lm["village_square"], lm["market"]], [lm["village_square"], lm["crafting_area"]],
		[lm["spawn_point"], Vector2(30, 52), lm["portal"]], [lm["market"], Vector2(52, 36), lm["portal"]],
	]
	var nx := int(HW / STEP) + 1
	var img := Image.create(nx, nx, false, Image.FORMAT_RGBA8)
	for gz in nx:
		for gx in nx:
			var x := gx * STEP - HW / 2.0
			var z := gz * STEP - HW / 2.0
			var h := 2.0 + n_hill.get_noise_2d(x * 2.0, z * 2.0) * 1.6
			for key in ["village_square", "market", "crafting_area", "spawn_point", "portal"]:
				h = lerp(2.0, h, smoothstep(14.0, 26.0, Vector2(x, z).distance_to(lm[key])))
			h = lerp(2.5, h, smoothstep(30.0, 44.0, Vector2(x, z).distance_to(lm["castle"])))
			var e := minf(minf(x + HW / 2.0, HW / 2.0 - x), minf(z + HW / 2.0, HW / 2.0 - z))
			h += (1.0 - smoothstep(4.0, 22.0, e)) * (14.0 + n_detail.get_noise_2d(x, z) * 4.0)  # green hills round the edge
			var hv := clampi(int(round((h + H_OFFSET) * H_SCALE)), 0, 65535)
			img.set_pixel(gx, gz, Color8(hv >> 8, hv & 255, 0, 0))
	img.save_png(ProjectSettings.globalize_path("res://data/hub_terrain.png"))
	var mask := Image.create(int(HW), int(HW), false, Image.FORMAT_RGBA8)
	mask.fill(Color(0, 0, 0, 0))
	for p in paths:
		var pts := PackedVector2Array(p)
		_stamp_path(mask, pts, 2.2, Vector2(HW / 2.0, HW / 2.0))
	# cobblestone: village square, castle approach, crafting area
	for mz in int(HW):
		for mx in int(HW):
			var x := mx + 0.5 - HW / 2.0
			var z := mz + 0.5 - HW / 2.0
			var cob := 1.0 - smoothstep(15.0, 16.5, Vector2(x, z).distance_to(lm["village_square"]))
			if absf(x) < 7.0 and z < -4.0 and z > -36.0:
				cob = 1.0
			cob = maxf(cob, 1.0 - smoothstep(9.0, 10.5, Vector2(x, z).distance_to(lm["crafting_area"])))
			if cob > 0.0:
				var c := mask.get_pixel(mx, mz)
				c.b = cob
				mask.set_pixel(mx, mz, c)
	mask.save_png(ProjectSettings.globalize_path("res://data/hub_mask.png"))
	var layout := {"size": [HW, HW], "origin": [-HW / 2.0, -HW / 2.0], "step": STEP, "h_offset": H_OFFSET, "h_scale": H_SCALE,
		"landmarks": _v2dict(lm), "paths": paths.map(func(p): return _pts(PackedVector2Array(p))),
		"water": [], "spawn_point": [lm["spawn_point"].x, lm["spawn_point"].y]}
	var f := FileAccess.open("res://data/hub_layout.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(layout, "  "))
	f.close()


# ---- post-process: smooth, limit slopes, enclose water ----

func _edge_e(x: float, z: float) -> float:
	return minf(minf(z + RD / 2.0, RD / 2.0 - z), minf(x + 10.0, RW - x))


func _post_process(hs: PackedFloat32Array, nx: int, nz: int) -> void:
	var wf: Vector2 = landmarks["waterfall"]
	# per-cell rules: 0 normal, 1 path corridor, 2 exempt (edge ring, ice cliffs, waterfall)
	var kind := PackedByteArray()
	kind.resize(nx * nz)
	for gz in nz:
		for gx in nx:
			var x := gx * STEP
			var z := gz * STEP - RD / 2.0
			var k := gz * nx + gx
			if Vector2(x, z).distance_to(wf) < 6.0:
				kind[k] = 2
			elif path_dist[k] < 6.0:
				kind[k] = 1  # paths win over the cliff and edge exceptions so every branch stays walkable
			elif _edge_e(x, z) < 46.0 or (x >= 512.0 and x <= 768.0 and z < -150.0):
				kind[k] = 2
	# 3 passes of a 5x5 box blur, skipping the edge ring
	for pass_i in 3:
		var src := hs.duplicate()
		for gz in range(2, nz - 2):
			for gx in range(2, nx - 2):
				if _edge_e(gx * STEP, gz * STEP - RD / 2.0) < 46.0:
					continue
				var sum := 0.0
				for dz in range(-2, 3):
					var row := (gz + dz) * nx + gx
					for dx in range(-2, 3):
						sum += src[row + dx]
				hs[gz * nx + gx] = sum / 25.0
	var floor_h := PackedFloat32Array()
	floor_h.resize(nx * nz)
	floor_h.fill(-1000.0)
	_slope_limit(hs, kind, floor_h, nx, nz)
	# water: sink the bed under each plane and wall it in with banks above the level
	var lip_z := river_z(214.0)
	for w in WATER:
		var r: Array = w["rect"]
		var lvl: float = w["level"]
		var x0 := int(r[0] / STEP)
		var x1 := int(r[2] / STEP)
		var z0 := int((r[1] + RD / 2.0) / STEP)
		var z1 := int((r[3] + RD / 2.0) / STEP)
		for gz in range(maxi(0, z0 - 2), mini(nz, z1 + 3)):
			for gx in range(maxi(0, x0 - 2), mini(nx, x1 + 3)):
				var k := gz * nx + gx
				var inside := gx >= x0 and gx <= x1 and gz >= z0 and gz <= z1
				var x := gx * STEP
				var z := gz * STEP - RD / 2.0
				if w["name"] == "forest_upper_pool" and absf(x - 214.0) <= 2.0 and absf(z - lip_z) <= 5.0:
					hs[k] = lvl - 0.05  # the lip the waterfall pours over
					continue
				if inside and path_dist[k] < 3.5:  # paths through water (the swamp) stay dry and walkable
					hs[k] = maxf(hs[k], lvl + 0.25)
					floor_h[k] = maxf(floor_h[k], lvl + 0.25)
					continue
				if inside:
					if hs[k] < lvl + 0.3:
						hs[k] = minf(hs[k], lvl - 0.5)
					if gx == x0 or gx == x1 or gz == z0 or gz == z1:
						hs[k] = maxf(hs[k], lvl + 0.4)
						floor_h[k] = maxf(floor_h[k], lvl + 0.4)
				elif not _in_lower_water(x, z, lvl):
					hs[k] = maxf(hs[k], lvl + 0.4)
					floor_h[k] = maxf(floor_h[k], lvl + 0.4)
	# dry land next to a raised bank can sit far below it: raise it on a slope cone out from the banks
	var is_water := PackedByteArray()
	is_water.resize(nx * nz)
	for w in WATER:
		var r: Array = w["rect"]
		for gz in range(maxi(0, int((r[1] + RD / 2.0) / STEP)), mini(nz, int((r[3] + RD / 2.0) / STEP) + 1)):
			for gx in range(maxi(0, int(r[0] / STEP)), mini(nx, int(r[2] / STEP) + 1)):
				if hs[gz * nx + gx] < w["level"]:
					is_water[gz * nx + gx] = 1
	for pass_i in 20:
		var changed := 0
		for gz in range(1, nz - 1):
			for gx in range(1, nx - 1):
				var k := gz * nx + gx
				if is_water[k] == 1 or kind[k] == 2:
					continue
				var c := maxf(maxf(floor_h[k - 1], floor_h[k + 1]), maxf(floor_h[k - nx], floor_h[k + nx])) - 1.4
				if c > floor_h[k] + 0.001:
					floor_h[k] = c
					changed += 1
		if changed == 0:
			break
	for k in nx * nz:
		if is_water[k] == 0:
			hs[k] = maxf(hs[k], floor_h[k])
	_slope_limit(hs, kind, floor_h, nx, nz)
	_validate(hs, kind, nx, nz)


func _in_lower_water(x: float, z: float, lvl: float) -> bool:
	## true if (x, z) sits inside another water rect whose level is lower (the river below the waterfall)
	for w in WATER:
		var r: Array = w["rect"]
		if w["level"] < lvl and x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]:
			return true
	return false


func _slope_limit(hs: PackedFloat32Array, kind: PackedByteArray, floor_h: PackedFloat32Array, nx: int, nz: int) -> void:
	for pass_i in 40:
		var changed := 0
		for gz in nz:
			for gx in nx:
				var k := gz * nx + gx
				if kind[k] == 2 or hs[k] > 70.0:
					continue
				var rise := 2.0 * (0.36 if kind[k] == 1 else 0.70)
				var lo := hs[k]
				if gx > 0: lo = minf(lo, hs[k - 1] + rise)
				if gx < nx - 1: lo = minf(lo, hs[k + 1] + rise)
				if gz > 0: lo = minf(lo, hs[k - nx] + rise)
				if gz < nz - 1: lo = minf(lo, hs[k + nx] + rise)
				lo = maxf(lo, floor_h[k])
				if lo < hs[k] - 0.001:
					hs[k] = lo
					changed += 1
		if changed == 0:
			break


func _validate(hs: PackedFloat32Array, kind: PackedByteArray, nx: int, nz: int) -> void:
	var steep := 0
	var max_path := 0.0
	var lim := 2.0 * tan(deg_to_rad(44.0))
	for gz in nz - 1:
		for gx in nx - 1:
			var k := gz * nx + gx
			for n in [k + 1, k + nx]:
				var d := absf(hs[k] - hs[n])
				if kind[k] != 2 and kind[n] != 2 and maxf(hs[k], hs[n]) <= 70.0 and d > lim:
					steep += 1
					print("  steep at ", gx * STEP, ", ", gz * STEP - RD / 2.0, " h ", snappedf(hs[k], 0.1), "/", snappedf(hs[n], 0.1))
				if path_dist[k] < 3.0 and path_dist[n] < 3.0:
					var g := rad_to_deg(atan(d / 2.0))
					if g > 22.0:
						print("  steep path at ", gx * STEP, ", ", gz * STEP - RD / 2.0, " grade ", snappedf(g, 0.1), " kind ", kind[k], "/", kind[n], " h ", snappedf(hs[k], 0.1), "/", snappedf(hs[n], 0.1))
					max_path = maxf(max_path, g)
	var leaks := 0
	for w in WATER:
		var r: Array = w["rect"]
		var lvl: float = w["level"]
		for gz in range(maxi(0, int((r[1] + RD / 2.0) / STEP)), mini(nz, int((r[3] + RD / 2.0) / STEP) + 1)):
			for gx in range(maxi(0, int(r[0] / STEP)), mini(nx, int(r[2] / STEP) + 1)):
				var k := gz * nx + gx
				if hs[k] >= lvl or kind[k] == 2:
					continue
				for o in [[1, 0], [-1, 0], [0, 1], [0, -1]]:
					var ax: int = gx + o[0]
					var az: int = gz + o[1]
					if ax < 0 or az < 0 or ax >= nx or az >= nz:
						continue
					var x := ax * STEP
					var z := az * STEP - RD / 2.0
					var out: bool = x < r[0] or x > r[2] or z < r[1] or z > r[3]
					if out and hs[az * nx + ax] < lvl and not _in_lower_water(x, z, lvl):
						leaks += 1
	print("BAKE CHECK steep cells >44 deg: %d (target 0), max path grade: %.1f deg (target <= 22), water leaks: %d (target 0)" % [steep, max_path, leaks])
