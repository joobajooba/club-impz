extends SceneTree
## Bakes the world layout images and JSON from fixed-seed noise, so every load is the same.
## Run from godot-game/:   godot --headless --path . --script res://scripts/tools/bake_world_data.gd
##
## Outputs (docs/world_build_notes.md explains the formats; J00BA can repaint the masks):
##   data/resource_terrain.png  641 x 257, 2 m per pixel. RG = height (16 bit), BA = warped depth "s" (16 bit)
##   data/resource_mask.png     1280 x 512, 1 m per pixel. R path, G wet / low ground, B special patch, A leaf litter / tree clusters
##   data/resource_layout.json  path lines, landmarks, water planes, river, ore spots
##   data/resource_skirt.png    577 x 385, 4 m per pixel, RG = height (16 bit, its own scale): the cliffs and mountains
##                              round the outside of the world (512 m each side), so its edge is a wall, not a drop
##   data/hub_terrain.png, data/hub_mask.png, data/hub_layout.json   the flat 200 x 200 m hub, from data/hub_town.json
## Hub only:   godot --headless --path . --script res://scripts/tools/bake_world_data.gd -- --hub_only

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
	{"name": "forest_river", "rect": [0, 40, 211, 120], "level": 3.0, "biome": "forest"},
	{"name": "forest_upper_pool", "rect": [211, 40, 262, 120], "level": 10.0, "biome": "forest"},
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
var n_crag := FastNoiseLite.new()     # skirt: cliff height and width along the border
var n_massif := FastNoiseLite.new()   # skirt: the mountain range behind the cliffs

var landmarks := {}
var main_path := PackedVector2Array()
var branches := []
var path_dist := PackedFloat32Array()  # coarse distance to the main path at 2 m (used to flatten the mountain pass)


func _init() -> void:
	if "--hub_only" in OS.get_cmdline_user_args():  # the hub alone (the resource world bake is slow)
		_bake_hub()
		print("bake done (hub)")
		quit()
		return
	_setup_noise()
	_build_resource_layout()
	_bake_resource()
	_bake_hub()
	print("bake done")
	quit()


func _setup_noise() -> void:
	var seeds := [101, 202, 303, 404, 505, 606, 707, 808, 909]
	var all := [n_warp, n_hill, n_ridge, n_detail, n_mesa, n_island, n_litter, n_crag, n_massif]
	for i in all.size():
		all[i].seed = seeds[i]
		all[i].noise_type = FastNoiseLite.TYPE_SIMPLEX_SMOOTH
	n_warp.frequency = 1.0 / 90.0
	n_hill.frequency = 1.0 / 140.0
	n_hill.fractal_octaves = 3
	n_ridge.frequency = 1.0 / 160.0
	n_ridge.fractal_type = FastNoiseLite.FRACTAL_FBM  # was RIDGED: knife edged ridges
	n_ridge.fractal_octaves = 3
	n_detail.frequency = 1.0 / 60.0
	n_mesa.frequency = 1.0 / 70.0
	n_island.frequency = 1.0 / 45.0
	n_litter.frequency = 1.0 / 40.0
	n_crag.frequency = 1.0 / 110.0
	n_crag.fractal_octaves = 2
	n_massif.frequency = 1.0 / 210.0
	n_massif.fractal_type = FastNoiseLite.FRACTAL_RIDGED
	n_massif.fractal_octaves = 3


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
	var h := 6.0 + n_hill.get_noise_2d(x, z) * 4.0 + n_detail.get_noise_2d(x, z) * 0.3
	h += g2(x, z, landmarks["stone_ruin"], 30.0) * 5.0
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
	var h := 18.0 + (n_ridge.get_noise_2d(x, z) * 0.5 + 0.5) * 34.0 + n_detail.get_noise_2d(x, z) * 0.5
	h += g2(x, z, landmarks["highest_peak"], 70.0) * 70.0
	h += g2(x, z, Vector2(470, -60), 40.0) * 24.0
	h -= g2(x, z, landmarks["obsidian_cave"], 24.0) * 8.0  # volcanic hollow round the obsidian cave
	return h


func h_frost(x: float, z: float) -> float:
	var h := 9.0 + n_hill.get_noise_2d(x, z) * 4.0 + n_detail.get_noise_2d(x * 2.0, z) * 0.6
	# ice cliffs along the south side, with the frozen waterfall on their face
	h += smoothstep(-140.0, -190.0, z) * 14.0
	# frozen lake (flat ice) and a small open pool
	var dl := Vector2(x, z).distance_to(landmarks["frozen_lake"])
	h = lerp(6.0, h, smoothstep(40.0, 72.0, dl))
	var dp := Vector2(x, z).distance_to(Vector2(706, -40))
	h = lerp(5.2, h, smoothstep(8.0, 22.0, dp))
	h += g2(x, z, landmarks["ice_spire"], 20.0) * 6.0
	return h


func h_plains(x: float, z: float) -> float:
	var h := 10.0 + n_hill.get_noise_2d(x * 0.8, z * 0.8) * 3.0
	var mesa := smoothstep(0.3, 0.62, n_mesa.get_noise_2d(x, z))
	h += mesa * 7.0
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
	h += smoothstep(0.15, 0.5, n_island.get_noise_2d(x, z)) * 1.6
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
		h = lerp(smax(ph, smin(h, ph + 4.0, 3.0), 3.0), h, smoothstep(7.0, 48.0, d_path))  # smooth, no crease lines
	elif x > 760.0 and x < 1030.0:
		h = lerp(smin(h, 14.0, 2.0), h, smoothstep(6.0, 20.0, d_path))
	# portal clearing: flat
	h = lerp(6.0, h, smoothstep(12.0, 26.0, Vector2(x, z).distance_to(landmarks["portal_clearing"])))
	# foothills that level off along the border; the cliffs and mountains beyond it are the skirt (_bake_skirt)
	h += _edge_ring(x, z)
	return h


func _edge_ring(x: float, z: float) -> float:
	## Rounded foothills (at most about 20 deg) rising to a level shelf at the border, where the skirt's cliffs start.
	## North, south and east are 48 / 48 / 36 m deep; the west one is narrow because the portal clearing is near it.
	var n := n_hill.get_noise_2d(x * 0.5, z * 0.5)
	var rn := 1.0 - smoothstep(6.0, 48.0, z + RD / 2.0)
	var rs := 1.0 - smoothstep(6.0, 48.0, RD / 2.0 - z)
	var re := 1.0 - smoothstep(6.0, 36.0, RW - x)
	var outer := (1.0 - (1.0 - rn) * (1.0 - rs) * (1.0 - re)) * (9.0 + 4.0 * n)  # soft union: no crease in the corners
	var west := (1.0 - smoothstep(4.0, 22.0, x)) * (5.0 + 2.0 * n)
	return smax(outer, west, 3.0)


static func smin(a: float, b: float, k: float) -> float:
	## Smooth minimum (polynomial): like minf but rounded over k metres, so clamps leave no crease.
	var hh := clampf(0.5 + 0.5 * (b - a) / k, 0.0, 1.0)
	return lerpf(b, a, hh) - k * hh * (1.0 - hh)


static func smax(a: float, b: float, k: float) -> float:
	return -smin(-a, -b, k)


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
	_bake_skirt(hs, nx, nz)
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
			# the waterfall cliff reads as rock (forest special = mountain_rock): its steep cells, grown by 1.5 m
			# and broken up with noise so the edge is ragged; the flat top and gentle slopes stay grass
			if b == 0 and _in_fall_cliff(x, z):
				var sl := _slope_at(hs, nx, nz, x, z)
				for o in [Vector2(1.5, 0), Vector2(-1.5, 0), Vector2(0, 1.5), Vector2(0, -1.5)]:
					sl = maxf(sl, _slope_at(hs, nx, nz, x + o.x, z + o.y))
				special = maxf(special, smoothstep(0.3, 0.4, sl + n_detail.get_noise_2d(x * 3.0, z * 3.0) * 0.08))
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
		"skirt": {"origin": [-SKIRT, -RD / 2.0 - SKIRT], "step": SKIRT_STEP, "size": [RW + 2.0 * SKIRT, RD + 2.0 * SKIRT],
			"h_offset": H_OFFSET, "h_scale": SKIRT_H_SCALE},
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


# ---------------------------------------------------------------- skirt: cliffs and mountains round the world
const SKIRT := 512.0          # how far the skirt reaches past each side
const SKIRT_STEP := 4.0
const SKIRT_H_SCALE := 100.0  # value = (h + 20) * 100, up to 635 m


func _skirt_rise(x: float, z: float, d: float) -> float:
	## Height added above the border at distance d outside it: a level shelf of 2 to 4.5 m, then a cliff of 46 to
	## 76 m whose steepest part is 60 to 70 deg (the Imp can climb 46 deg), then a ridged range rising up to 170 m more.
	var crag := n_crag.get_noise_2d(x, z) * 0.5 + 0.5
	var nd := n_detail.get_noise_2d(x * 1.7, z * 1.7)
	# buttresses and gullies: ridges of rock that stand out of the cliff every 15 to 30 m, ravines between them
	var gully := absf(n_detail.get_noise_2d(x * 2.6 + 400.0, z * 2.6 - 300.0))
	var foot := 2.0 + 2.5 * (nd * 0.5 + 0.5) + gully * 6.0
	var wall := (46.0 + 30.0 * crag - gully * 10.0) * smoothstep(foot, foot + 24.0 + 10.0 * crag, d)
	# ledges: the cliff climbs in uneven steps (each still too steep to stand on between them)
	wall += sin(wall * 0.42 + nd * 2.0) * 1.6 * smoothstep(foot, foot + 6.0, d) * (1.0 - smoothstep(foot + 30.0, foot + 44.0, d))
	var massif := (50.0 + 120.0 * (n_massif.get_noise_2d(x, z) * 0.5 + 0.5)) * smoothstep(24.0, 300.0, d)
	var rough := n_detail.get_noise_2d(x * 3.0, z * 3.0) * 2.5 * smoothstep(8.0, 40.0, d)
	return wall + massif + rough


func _bake_skirt(hs: PackedFloat32Array, nx: int, nz: int) -> void:
	var sw := int((RW + 2.0 * SKIRT) / SKIRT_STEP) + 1
	var sd := int((RD + 2.0 * SKIRT) / SKIRT_STEP) + 1
	var img := Image.create(sw, sd, false, Image.FORMAT_RGBA8)
	var top := 0.0
	for j in sd:
		for i in sw:
			var x := -SKIRT + i * SKIRT_STEP
			var z := -RD / 2.0 - SKIRT + j * SKIRT_STEP
			var cx := clampf(x, 0.0, RW)
			var cz := clampf(z, -RD / 2.0, RD / 2.0)
			var d := Vector2(x - cx, z - cz).length()
			var h := _h_at(hs, nx, nz, cx, cz)  # inside: the world itself, so interpolation near the border is right
			if d > 0.0:
				h += _skirt_rise(x, z, d)
			top = maxf(top, h)
			var hv := clampi(int(round((h + H_OFFSET) * SKIRT_H_SCALE)), 0, 65535)
			img.set_pixel(i, j, Color8(hv >> 8, hv & 255, 0, 255))
	img.save_png(ProjectSettings.globalize_path("res://data/resource_skirt.png"))
	print("BAKE CHECK skirt: %d x %d, highest %.1f m" % [sw, sd, top])


# ---------------------------------------------------------------- hub (200 x 200 m, centred on 0, 0)
## The hub is a flat walled town (J00BA, 2026-11-09). Its plan comes from data/hub_town.json, made by
## `build scripts/build_hub_town.py`: cobbled streets and squares go in mask B (the hub's cobblestone layer),
## garden and orchard walks in mask R (dirt path). The ground is level everywhere, outside the walls too.
const HW := 200.0

func _bake_hub() -> void:
	var town: Dictionary = JSON.parse_string(FileAccess.get_file_as_string("res://data/hub_town.json"))
	var ground_h: float = town.get("ground_height", 2.0)
	var nx := int(HW / STEP) + 1
	var img := Image.create(nx, nx, false, Image.FORMAT_RGBA8)
	var hv := clampi(int(round((ground_h + H_OFFSET) * H_SCALE)), 0, 65535)
	img.fill(Color8(hv >> 8, hv & 255, 0, 0))
	img.save_png(ProjectSettings.globalize_path("res://data/hub_terrain.png"))
	var mask := Image.create(int(HW), int(HW), false, Image.FORMAT_RGBA8)
	mask.fill(Color(0, 0, 0, 0))
	for w in town["ground"]["dirt"]:
		var pts := PackedVector2Array()
		for q in w["points"]:
			pts.append(Vector2(q[0], q[1]))
		_stamp_path(mask, pts, float(w["radius"]), Vector2(HW / 2.0, HW / 2.0))
	for r in town["ground"].get("dirt_rects", []):  # packed-earth floors (the crafters' yard workshops)
		for mz in range(maxi(0, int(r[1] + HW / 2.0)), mini(int(HW), int(r[3] + HW / 2.0))):
			for mx in range(maxi(0, int(r[0] + HW / 2.0)), mini(int(HW), int(r[2] + HW / 2.0))):
				var c := mask.get_pixel(mx, mz)
				c.r = 1.0
				mask.set_pixel(mx, mz, c)
	for r in town["ground"]["cobble"]:
		# 1 px soft edge so the cobbles meet the grass with a dithered border, not a ruler line
		for mz in range(maxi(0, int(r[1] + HW / 2.0) - 1), mini(int(HW), int(r[3] + HW / 2.0) + 2)):
			for mx in range(maxi(0, int(r[0] + HW / 2.0) - 1), mini(int(HW), int(r[2] + HW / 2.0) + 2)):
				var x := mx + 0.5 - HW / 2.0
				var z := mz + 0.5 - HW / 2.0
				var d := maxf(maxf(r[0] - x, x - r[2]), maxf(r[1] - z, z - r[3]))
				var cob := 1.0 - smoothstep(-0.5, 0.7, d)
				var c := mask.get_pixel(mx, mz)
				if cob > c.b:
					c.b = cob
					c.r = minf(c.r, 1.0 - cob)
					mask.set_pixel(mx, mz, c)
	mask.save_png(ProjectSettings.globalize_path("res://data/hub_mask.png"))
	var layout := {"size": [HW, HW], "origin": [-HW / 2.0, -HW / 2.0], "step": STEP, "h_offset": H_OFFSET, "h_scale": H_SCALE,
		"landmarks": town["landmarks"], "walls": town["walls"], "no_scatter": town["no_scatter"],
		"water": [], "spawn_point": town["spawn_point"]}
	var f := FileAccess.open("res://data/hub_layout.json", FileAccess.WRITE)
	f.store_string(JSON.stringify(layout, "  "))
	f.close()


# ---- post-process: smooth, limit slopes, enclose water ----

func _edge_e(x: float, z: float) -> float:
	return minf(minf(z + RD / 2.0, RD / 2.0 - z), minf(x + 10.0, RW - x))


func _post_process(hs: PackedFloat32Array, nx: int, nz: int) -> void:
	var wf: Vector2 = landmarks["waterfall"]
	# per-cell rules: 0 normal, 1 path corridor, 2 exempt (waterfall only), 3 rugged (high mountain band, edge ring)
	var kind := PackedByteArray()
	kind.resize(nx * nz)
	for gz in nz:
		for gx in nx:
			var x := gx * STEP
			var z := gz * STEP - RD / 2.0
			var k := gz * nx + gx
			var s := warped_s(x, z)
			if _at_waterfall(x, z):
				kind[k] = 2
			elif path_dist[k] < 6.0:
				kind[k] = 1  # paths win over the rugged areas so every branch stays walkable
			elif (s >= 256.0 and s <= 512.0 and hs[k] > 40.0) or _in_fall_cliff(x, z):
				kind[k] = 3
	var carved := hs.duplicate()  # riverbed, swamp hollows and pools before the blur fills them in
	_blur5(hs, nx, nz, 5)
	_slope_limit(hs, kind, nx, nz)
	_blur5(hs, nx, nz, 2)  # round off the creases the limiter leaves
	_slope_limit(hs, kind, nx, nz)  # the blur can push rugged slopes into the normal cells next to them
	_recarve(hs, carved, nx, nz)
	_shape_water(hs, kind, nx, nz)


func _recarve(hs: PackedFloat32Array, carved: PackedFloat32Array, nx: int, nz: int) -> void:
	## Inside each water rect, cells that were under water before smoothing get their carved height back
	## (lightly blurred among themselves), so the river and the swamp keep their water. _shape_water then
	## softens the shores.
	for w in WATER:
		var r: Array = w["rect"]
		var lvl: float = w["level"]
		var c := _rect_cells(r, nx, nz)
		for gz in range(c[2], c[3] + 1):
			for gx in range(c[0], c[1] + 1):
				var k := gz * nx + gx
				if carved[k] < lvl:
					var sum := 0.0
					var cnt := 0
					for dz in range(-1, 2):
						for dx in range(-1, 2):
							var j := clampi(gz + dz, 0, nz - 1) * nx + clampi(gx + dx, 0, nx - 1)
							sum += minf(carved[j], lvl)
							cnt += 1
					hs[k] = minf(hs[k], sum / cnt)


func _h_at(hs: PackedFloat32Array, nx: int, nz: int, x: float, z: float) -> float:
	## bilinear height from the 2 m grid
	var fx := clampf(x / STEP, 0.0, nx - 1.001)
	var fz := clampf((z + RD / 2.0) / STEP, 0.0, nz - 1.001)
	var ix := int(fx)
	var iz := int(fz)
	var tx := fx - ix
	var tz := fz - iz
	var a := lerpf(hs[iz * nx + ix], hs[iz * nx + ix + 1], tx)
	var b := lerpf(hs[(iz + 1) * nx + ix], hs[(iz + 1) * nx + ix + 1], tx)
	return lerpf(a, b, tz)


func _slope_at(hs: PackedFloat32Array, nx: int, nz: int, x: float, z: float) -> float:
	## 1 - normal.y, the same measure as the terrain shader's slope
	var dx := (_h_at(hs, nx, nz, x + 1.0, z) - _h_at(hs, nx, nz, x - 1.0, z)) / 2.0
	var dz := (_h_at(hs, nx, nz, x, z + 1.0) - _h_at(hs, nx, nz, x, z - 1.0)) / 2.0
	return 1.0 - 1.0 / sqrt(1.0 + dx * dx + dz * dz)


func _at_waterfall(x: float, z: float) -> bool:
	## The waterfall notch only: the 10 m wide fall (channel, crest, face and plunge pool, step e of _shape_water)
	## plus 1 m each side. Exempt from the slope and shore rules; the rest of the cliff line is rugged (_in_fall_cliff).
	var wf: Vector2 = landmarks["waterfall"]
	return absf(z - wf.y) <= 6.0 and x >= 200.0 and x <= 218.0


func _in_fall_cliff(x: float, z: float) -> bool:
	## The cliff line either side of the waterfall where the lower forest (river, 3 m) steps up to the upper pool
	## (10 m) along their shared rect border: rugged (37 deg) instead of the 24 deg / gentle shore rules.
	var wf: Vector2 = landmarks["waterfall"]
	return x > 199.0 and x < 222.0 and absf(z - wf.y) < 30.0  # covers the bank's west slope (step e of _shape_water)


func _blur5(hs: PackedFloat32Array, nx: int, nz: int, passes: int) -> void:
	## 5x5 box blur over the whole grid (edge ring included), clamped at the grid border.
	for pass_i in passes:
		var src := hs.duplicate()
		for gz in nz:
			for gx in nx:
				var sum := 0.0
				for dz in range(-2, 3):
					var row := clampi(gz + dz, 0, nz - 1) * nx
					for dx in range(-2, 3):
						sum += src[row + clampi(gx + dx, 0, nx - 1)]
				hs[gz * nx + gx] = sum / 25.0


func _rect_cells(r: Array, nx: int, nz: int) -> Array:
	return [maxi(0, int(ceil(r[0] / STEP))), mini(nx - 1, int(floor(r[2] / STEP))),
		maxi(0, int(ceil((r[1] + RD / 2.0) / STEP))), mini(nz - 1, int(floor((r[3] + RD / 2.0) / STEP)))]


func _side_free(w: Dictionary, px: float, pz: float, other_water := true) -> bool:
	## A rect side needs no shore margin when it runs into the edge ring or (other_water) into another water rect.
	if _edge_e(px, pz) < 46.0:
		return true
	if not other_water:
		return false
	for o in WATER:
		if o["name"] == w["name"]:
			continue
		var r: Array = o["rect"]
		if px >= r[0] and px <= r[2] and pz >= r[1] and pz <= r[3]:
			return true
	return false


func _shape_water(hs: PackedFloat32Array, kind: PackedByteArray, nx: int, nz: int) -> void:
	## Soft shores: gentle 1:8 shelf under the water, a rising bank on land, noisy margins so no straight edges.
	var n := nx * nz
	# a. paths through water (the swamp) rise smoothly to just above the level
	for w in WATER:
		var c := _rect_cells(w["rect"], nx, nz)
		var target: float = w["level"] + 0.35
		for gz in range(c[2], c[3] + 1):
			for gx in range(c[0], c[1] + 1):
				var k := gz * nx + gx
				var wgt := 1.0 - smoothstep(2.5, 7.0, path_dist[k])
				if wgt > 0.0:
					hs[k] = maxf(hs[k], lerp(hs[k], target, wgt))
	# b. wet mask: inside the rect, below the level, and further than a noisy margin from the rect border
	var label := PackedInt32Array()
	label.resize(n)
	label.fill(-1)
	var order := range(WATER.size())
	order.sort_custom(func(a, b): return WATER[a]["level"] < WATER[b]["level"])
	for wi in order:
		var w: Dictionary = WATER[wi]
		var r: Array = w["rect"]
		var lvl: float = w["level"]
		var cx: float = (r[0] + r[2]) / 2.0
		var cz: float = (r[1] + r[3]) / 2.0
		var free_w := _side_free(w, r[0] - 3.0, cz)
		var free_e := _side_free(w, r[2] + 3.0, cz)
		var free_n := _side_free(w, cx, r[1] - 3.0)
		var free_s := _side_free(w, cx, r[3] + 3.0)
		# sides shared with water at another level are only open at the waterfall itself; elsewhere land
		# separates the two (a 7 m step between the river and the upper pool otherwise)
		var edge_w := _side_free(w, r[0] - 3.0, cz, false)
		var edge_e := _side_free(w, r[2] + 3.0, cz, false)
		var wf: Vector2 = landmarks["waterfall"]
		var c := _rect_cells(r, nx, nz)
		for gz in range(c[2], c[3] + 1):
			for gx in range(c[0], c[1] + 1):
				var k := gz * nx + gx
				if label[k] >= 0 or hs[k] >= lvl:
					continue
				var x := gx * STEP
				var z := gz * STEP - RD / 2.0
				var margin := 6.0 + n_detail.get_noise_2d(x, z) * 4.0
				var d := 1e9
				var at_fall := _at_waterfall(x, z)
				if not (edge_w or (free_w and at_fall)): d = minf(d, x - r[0])
				if not (edge_e or (free_e and at_fall)): d = minf(d, r[2] - x)
				if not free_n: d = minf(d, z - r[1])
				if not free_s: d = minf(d, r[3] - z)
				if d > margin:
					label[k] = wi
	# c. two pass chamfer distance (metres): dist_in for wet cells to the nearest dry cell, dist_out for dry cells
	#    to the nearest wet cell, carrying the label of that nearest wet cell
	var dist_in := _chamfer(label, nx, nz, true, PackedInt32Array())
	var near := PackedInt32Array()
	near.resize(n)
	var dist_out := _chamfer(label, nx, nz, false, near)
	# d. shelf under the water, rising bank on land
	for k in n:
		if label[k] >= 0:
			var lvl: float = WATER[label[k]]["level"]
			hs[k] = minf(hs[k], lvl - minf(1.4, 0.12 + dist_in[k] * 0.12))
		elif dist_out[k] < 12.0:
			var lvl: float = WATER[near[k]]["level"]
			var bank: float = lerp(lvl + 0.12 + dist_out[k] * 0.12, hs[k], smoothstep(0.0, 12.0, dist_out[k]))
			hs[k] = maxf(hs[k], bank)
			if _needs_bank(k, near[k], dist_out[k], nx):
				hs[k] = maxf(hs[k], lvl + 0.12)
	# f. 2 passes of a 3x3 blur near the shores, then re-clamp each side of the waterline
	for pass_i in 2:
		var src := hs.duplicate()
		for gz in range(1, nz - 1):
			for gx in range(1, nx - 1):
				var k := gz * nx + gx
				if (label[k] >= 0 and dist_in[k] < 12.0) or (label[k] < 0 and dist_out[k] < 12.0):
					var sum := 0.0
					for dz in range(-1, 2):
						for dx in range(-1, 2):
							sum += src[k + dz * nx + dx]
					hs[k] = sum / 9.0
	# gentle shore band: within 12 m of the water the land rises at most 0.3 m per 2 m cell (high banks are cut
	# back into a beach), and the first wet cells come up to meet it; each side stays clear of the waterline
	for pass_i in 80:
		var changed := 0
		for gz in nz:
			for gx in nx:
				var k := gz * nx + gx
				if kind[k] == 2:
					continue
				var wet := label[k] >= 0
				var shore := wet or dist_out[k] < 12.0  # every wet cell: the whole bed is a smooth bowl
				var rise := 0.3 if shore and kind[k] != 3 else 2.0 * (0.30 if kind[k] == 1 else 0.75 if kind[k] == 3 else 0.45)
				var lo := hs[k]
				var hi := -1e9
				for j in [k - 1, k + 1, k - nx, k + nx]:
					if (j == k - 1 and gx == 0) or (j == k + 1 and gx == nx - 1) or j < 0 or j >= n:
						continue
					lo = minf(lo, hs[j] + rise)
					hi = maxf(hi, hs[j] - rise)
				var v := lo
				if wet:
					var lvl: float = WATER[label[k]]["level"]
					if shore:
						v = maxf(v, hi)
					v = minf(v, lvl - 0.1)
				elif dist_out[k] < 12.0 and _needs_bank(k, near[k], dist_out[k], nx):
					v = maxf(v, WATER[near[k]]["level"] + 0.1)
				if absf(v - hs[k]) > 0.001:
					hs[k] = v
					changed += 1
		if changed == 0:
			break
	# e. the waterfall notch, cut into a bank that closes the upper pool off from the cliff everywhere else:
	#    channel x 213..218 (bed 9.4, the pool runs on to the crest), crest x 211..213 (9.7, 0.3 m of water),
	#    face x 207..211 (9.7 down to 1.6 in about 4 m), plunge pool x 201..207 (a bowl at most 1.6, 1.4 m under
	#    the river, rising back to the river bed over 6 m). The notch is 10 m wide (|z - lip_z| <= 5), its sides
	#    feathered into the bank. The bank: at least 10.5 over x 209..216 along the whole shared border, falling
	#    west to the river at the rugged 37 deg, so the pool only leaves through the notch.
	var lip_z := river_z(214.0)
	for gz in nz:
		for gx in nx:
			var x := gx * STEP
			var z := gz * STEP - RD / 2.0
			if x < 190.0 or x > 224.0 or z < 30.0 or z > 130.0:
				continue
			var k := gz * nx + gx
			var h := hs[k]
			var dz := absf(z - lip_z)
			var bank := h
			if x <= 216.0:
				var top := 10.5 if x >= 209.0 else 10.5 - (209.0 - x) * 0.75  # the rugged 37 deg
				var zw := smoothstep(36.0, 40.0, z) * (1.0 - smoothstep(120.0, 124.0, z))
				bank = maxf(h, lerp(h, top, zw))
			var notch := bank
			if x >= 213.0:
				notch = 9.4 if x <= 218.0 else h
			elif x >= 211.0:
				notch = 9.7
			elif x >= 207.0:
				notch = lerp(9.7, 1.6, (211.0 - x) / 4.0)
			else:
				notch = h  # below the face: the plunge pool bowl (next) shapes the river bed
			hs[k] = lerp(bank, notch, 1.0 - smoothstep(5.0, 6.5, dz))
			# the plunge pool bowl
			if x > 207.0:
				continue  # the face is above; the bowl does not climb the cliff
			var bx := maxf(0.0, 201.0 - x) * 3.0  # downstream the bowl meets the river bed within 2 m (x 199)
			var bz := maxf(0.0, dz - 7.0)
			var out := Vector2(bx, bz).length()
			var inner := 1.0 - maxf(absf(x - 204.0) / 3.0, dz / 7.0)
			var bowl := 1.6 - 0.5 * clampf(inner, 0.0, 1.0)
			hs[k] = minf(hs[k], lerp(bowl, hs[k], smoothstep(0.0, 6.0, out)))
	_soften(hs, kind, label, dist_out, near, nx, nz)
	_validate(hs, kind, label, dist_in, dist_out, nx, nz)


func _soften(hs: PackedFloat32Array, kind: PackedByteArray, label: PackedInt32Array, dist_out: PackedFloat32Array,
		near: PackedInt32Array, nx: int, nz: int) -> void:
	## Rounds off creases and pits: cells that stick out of (or sink into) their 3 x 3 neighbourhood by more than
	## 8 cm move most of the way to its average. Gentle ground and fine detail are left alone. The waterfall stays
	## as it is, and each side of every waterline is clamped again so no water leaks.
	for pass_i in 8:
		var src := hs.duplicate()
		var moved := 0
		for gz in range(1, nz - 1):
			for gx in range(1, nx - 1):
				var k := gz * nx + gx
				var x := gx * STEP
				var z := gz * STEP - RD / 2.0
				if kind[k] == 2 or (x > 188.0 and x < 226.0 and z > 30.0 and z < 130.0):
					continue
				if label[k] >= 0 or dist_out[k] < 12.0:
					continue  # shores and beds are already shaped (and checked) by _shape_water
				var sum := 0.0
				for dz in range(-1, 2):
					for dx in range(-1, 2):
						sum += src[k + dz * nx + dx]
				var dev := sum / 9.0 - src[k]
				if absf(dev) < 0.08:
					continue
				var v := src[k] + dev * 0.6
				# stay inside the slope limits (_slope_limit) with each normal or path neighbour
				if kind[k] < 2:
					for j in [k - 1, k + 1, k - nx, k + nx]:
						if kind[j] < 2:
							var rise := 2.0 * (0.30 if kind[k] == 1 or kind[j] == 1 else 0.45)
							v = clampf(v, src[j] - rise, src[j] + rise)
				if label[k] >= 0:
					v = minf(v, WATER[label[k]]["level"] - 0.1)
				elif dist_out[k] < 12.0 and _needs_bank(k, near[k], dist_out[k], nx):
					v = maxf(v, WATER[near[k]]["level"] + 0.1)
				hs[k] = v
				moved += 1
		if moved == 0:
			break


func _needs_bank(k: int, wi: int, d_out: float, nx: int) -> bool:
	## Dry land must stay above a water level only where that water's plane is (inside its rect) or right at the
	## waterline; further out the bank just blends back into the land (no wall where the 12 m band ends).
	if d_out < 4.0:
		return true
	var r: Array = WATER[wi]["rect"]
	var x := (k % nx) * STEP
	var z := (k / nx) * STEP - RD / 2.0
	return x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]


func _chamfer(label: PackedInt32Array, nx: int, nz: int, inside: bool, near: PackedInt32Array) -> PackedFloat32Array:
	## Two pass chamfer distance on the 2 m grid. inside: distance from wet cells to the nearest dry cell.
	## Otherwise distance from dry cells to the nearest wet cell, with that cell's label written to near.
	var n := nx * nz
	var d := PackedFloat32Array()
	d.resize(n)
	var track := near.size() == n
	for k in n:
		var wet := label[k] >= 0
		var src := (not wet) if inside else wet
		d[k] = 0.0 if src else 1e9
		if track:
			near[k] = label[k]
	var a := STEP
	var b := STEP * 1.41421
	var fwd := [[-1, 0, a], [0, -1, a], [-1, -1, b], [1, -1, b]]
	var bwd := [[1, 0, a], [0, 1, a], [1, 1, b], [-1, 1, b]]
	for pass_dir in [fwd, bwd]:
		var zs := range(nz) if pass_dir == fwd else range(nz - 1, -1, -1)
		var xs := range(nx) if pass_dir == fwd else range(nx - 1, -1, -1)
		for gz in zs:
			for gx in xs:
				var k: int = gz * nx + gx
				if d[k] == 0.0:
					continue
				for o in pass_dir:
					var ax: int = gx + o[0]
					var az: int = gz + o[1]
					if ax < 0 or az < 0 or ax >= nx or az >= nz:
						continue
					var j := az * nx + ax
					var v: float = d[j] + o[2]
					if v < d[k]:
						d[k] = v
						if track:
							near[k] = near[j]
	return d


func _in_lower_water(x: float, z: float, lvl: float) -> bool:
	## true if (x, z) sits inside another water rect whose level is lower (the river below the waterfall)
	for w in WATER:
		var r: Array = w["rect"]
		if w["level"] < lvl and x >= r[0] and x <= r[2] and z >= r[1] and z <= r[3]:
			return true
	return false


func _slope_limit(hs: PackedFloat32Array, kind: PackedByteArray, nx: int, nz: int) -> void:
	## Max rise per 2 m cell: normal 24 deg, path 17 deg, rugged 37 deg. The waterfall (kind 2) is exempt.
	for pass_i in 400:  # big mountains need many passes; it stops once nothing moves
		var changed := 0
		for gz in nz:
			for gx in nx:
				var k := gz * nx + gx
				if kind[k] == 2:
					continue
				var rise := 2.0 * (0.30 if kind[k] == 1 else 0.75 if kind[k] == 3 else 0.45)
				var lo := hs[k]
				if gx > 0: lo = minf(lo, hs[k - 1] + rise)
				if gx < nx - 1: lo = minf(lo, hs[k + 1] + rise)
				if gz > 0: lo = minf(lo, hs[k - nx] + rise)
				if gz < nz - 1: lo = minf(lo, hs[k + nx] + rise)
				if lo < hs[k] - 0.001:
					hs[k] = lo
					changed += 1
		if changed == 0:
			break


func _validate(hs: PackedFloat32Array, kind: PackedByteArray, label: PackedInt32Array, dist_in: PackedFloat32Array,
		dist_out: PackedFloat32Array, nx: int, nz: int) -> void:
	var steep := 0
	var max_path := 0.0
	var max_shore := 0.0
	var shore_at := Vector2.ZERO
	var lim := 2.0 * tan(deg_to_rad(30.0))
	for gz in nz - 1:
		for gx in nx - 1:
			var k := gz * nx + gx
			for nb in [k + 1, k + nx]:
				var d := absf(hs[k] - hs[nb])
				if kind[k] < 2 and kind[nb] < 2 and d > lim:
					steep += 1
					if steep <= 5:
						print("  steep at ", gx * STEP, ", ", gz * STEP - RD / 2.0, " h ", snappedf(hs[k], 0.1), "/", snappedf(hs[nb], 0.1))
				if path_dist[k] < 3.0 and path_dist[nb] < 3.0:
					max_path = maxf(max_path, rad_to_deg(atan(d / 2.0)))
				var shore_k := (dist_in[k] < 8.0) if label[k] >= 0 else (dist_out[k] < 8.0)
				var cliff := kind[k] == 3 or kind[nb] == 3  # rugged (incl. the waterfall cliff line) may be steeper
				if shore_k and not cliff and kind[k] != 2 and kind[nb] != 2 and d > max_shore:
					max_shore = d
					shore_at = Vector2(gx * STEP, gz * STEP - RD / 2.0)
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
	# the waterfall notch and bank
	var lip_z := river_z(214.0)
	var hat := func(x: float, z: float) -> float:
		return hs[clampi(int(round((z + RD / 2.0) / STEP)), 0, nz - 1) * nx + clampi(int(round(x / STEP)), 0, nx - 1)]
	var bank_min := 1e9
	var bank_at := Vector2.ZERO
	for gz in nz:
		for gx in nx:
			var x := gx * STEP
			var z := gz * STEP - RD / 2.0
			if x >= 209.0 and x <= 216.0 and z >= 40.0 and z <= 120.0 and absf(z - lip_z) > 6.0 and hs[gz * nx + gx] < bank_min:
				bank_min = hs[gz * nx + gx]
				bank_at = Vector2(x, z)
	print("BAKE CHECK waterfall: crest %.2f (target 9.7), plunge pool %.2f (target <= 1.6), lowest bank %.2f at %s (target >= 10.5)" % [
		hat.call(212.0, lip_z), hat.call(204.0, lip_z), bank_min, bank_at])
	# edge leaks: cells on each water rect's border ring with the terrain under the water (the plane's edge would
	# show as a straight cut), except the notch and sides that run into the edge ring
	var edge_leaks := 0
	var worst := []
	for w in WATER:
		var r: Array = w["rect"]
		var lvl: float = w["level"]
		var c := _rect_cells(r, nx, nz)
		for gz in range(c[2], c[3] + 1):
			for gx in range(c[0], c[1] + 1):
				if gx != c[0] and gx != c[1] and gz != c[2] and gz != c[3]:
					continue
				var x := gx * STEP
				var z := gz * STEP - RD / 2.0
				var h := hs[gz * nx + gx]
				if h >= lvl - 0.05 or _at_waterfall(x, z):
					continue
				var ox := -3.0 if gx == c[0] else 3.0 if gx == c[1] else 0.0
				var oz := -3.0 if gz == c[2] else 3.0 if gz == c[3] else 0.0
				if _edge_e(x + ox, z + oz) < 46.0:
					continue
				edge_leaks += 1
				worst.append([lvl - h, w["name"], Vector2(x, z)])
	worst.sort_custom(func(a, b): return a[0] > b[0])
	print("BAKE CHECK edge leaks: %d (target 0) worst %s" % [edge_leaks, str(worst.slice(0, 8))])
	print("BAKE CHECK water leaks: %d (target 0), steep cells >30 deg outside waterfall/rugged: %d (target 0), max path grade: %.1f deg (target <= 18), max shore step: %.2f m at %s (target <= 0.3)" % [
		leaks, steep, max_path, max_shore, shore_at])
