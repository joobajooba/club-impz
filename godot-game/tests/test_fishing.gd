extends Node
## Headless test for fishing in the resource world (scripts/world/fishing.gd, fish_spot.gd, scripts/player/fisher.gd).
## Run from the repo root:
##   godot --headless --path godot-game res://tests/test_fishing.tscn
## Checks the rules (catch times, the bite window, rod blockers), then loads the real game into the resource
## world and checks the spots on each water, that standing on a spot's shore targets it, and a full cast:
## wait, bite, land (a fish in the bag, then a new cast), a missed bite (the bar drops to half) and reeling in.
## Exits with the number of failed checks (0 = all passed). It never writes the player's save (Save.enabled).

const SPOTS := {"forest_river": 4, "forest_upper_pool": 4, "frost_open_pool": 4, "plains_watering_hole": 4, "swamp_water": 8}

var _fails := 0


func _ready() -> void:
	Save.enabled = false
	GameData._test_levels_read = true
	_rules()
	var main: Node = load("res://scenes/main.tscn").instantiate()
	main.args["world"] = "resource"
	add_child(main)
	var loaded := func() -> bool:
		return get_tree().get_nodes_in_group("fish_spot").size() > 0 and not main.player.frozen
	if not await _until(loaded, 240.0):
		_ok(false, "the resource world loads with fishing spots")
		return _done()
	var spots: Array = get_tree().get_nodes_in_group("fish_spot")
	var per := {}
	for s in spots:
		per[s.water] = int(per.get(s.water, 0)) + 1
		var list: Array = []
		for spec in preload("res://scripts/world/resource_landmarks.gd").FISH_WATERS:
			if spec[0] == s.water:
				list = spec[2]
		_ok(s.fish in list, "%s holds a fish of its water (%s)" % [s.name, s.fish])
		var st: Vector3 = s.get_meta("stand")
		_ok(st.y > s.global_position.y, "%s has dry shore to stand on" % s.name)
	for w in SPOTS:
		_ok(int(per.get(w, 0)) == SPOTS[w], "%s has %d spots (got %d)" % [w, SPOTS[w], int(per.get(w, 0))])
	var player: CharacterBody3D = main.player
	var fisher: Node = player.fisher
	Inventory.test_unlock_tools()
	Inventory.hold("driftwood_rod")
	Inventory.take_out("rod")
	var minnow: Node3D = null
	var perch: Node3D = null
	for s in spots:
		if s.fish == "minnow" and minnow == null:
			minnow = s
		if s.fish == "perch" and perch == null:
			perch = s
	for s in spots:                      # a far teleport: the ground's collision there may take a few frames
		var on_shore := func() -> bool:
			player.global_position = s.get_meta("stand") + Vector3.UP * 0.05
			player.velocity = Vector3.ZERO
			return fisher.target == s
		await _until(on_shore, 3.0)
		_ok(fisher.target == s, "standing on %s's shore targets it" % s.name)
		if fisher.target != s:
			var me := player.global_position
			print("  stand ", s.get_meta("stand"), " now ", me, " spot ", s.global_position, " d ",
					Vector2(me.x - s.global_position.x, me.z - s.global_position.z).length(), " target ", fisher.target)
	if perch:
		_ok(Fishing.blocker(perch.row, "driftwood_rod") == "Needs an Ash Rod or better", "the starter rod can't catch perch")
	# a full cast on a minnow spot, with short test times
	var at_minnow := func() -> bool:
		player.global_position = minnow.get_meta("stand") + Vector3.UP * 0.05
		player.velocity = Vector3.ZERO
		return fisher.target == minnow
	await _until(at_minnow, 3.0)
	await _frames(30)                    # settle on the ground
	_ok(fisher.target == minnow, "still by the minnow spot after settling")
	fisher.time_override = 0.6
	fisher.window_override = 30.0
	var before := Inventory.count("minnow")
	_ok(fisher.use(), "E by the water with a rod casts")
	_ok(fisher.state == "cast", "the Imp casts")
	_ok(await _until(func(): return fisher.state == "wait", 5.0), "the float lands and the wait starts")
	_ok(await _until(func(): return fisher.state == "bite", 5.0), "a fish bites when the bar is full")
	_ok(fisher.use(), "E on the bite reels in")
	_ok(Inventory.count("minnow") == before + 1, "the minnow is in the bag")
	_ok(fisher.state == "cast" and fisher.caught == 1, "the Imp casts again after a catch")
	# a missed bite: the bar drops to half and the fish comes round again
	fisher.window_override = 0.1
	_ok(await _until(func(): return fisher.state == "bite", 6.0), "the next fish bites")
	_ok(await _until(func(): return fisher.state == "wait", 3.0), "a missed bite goes back to waiting")
	var key := String(minnow.name)
	_ok(absf(float(Fishing.progress.get(key, 0.0)) - Fishing.MISS_KEEP) < 0.1, "a miss drops the bar to half")
	# reeling in while waiting keeps the bar
	fisher.time_override = 30.0
	await _frames(5)
	var kept := float(Fishing.progress.get(key, 0.0))
	_ok(fisher.use() and fisher.state == "", "E while waiting reels in")
	_ok(absf(float(Fishing.progress.get(key, 0.0)) - kept) < 0.05, "the bar is kept after reeling in")
	# putting the rod away stops fishing
	fisher.time_override = 30.0
	fisher.use()
	Inventory.take_out("pickaxe")
	await _frames(3)
	_ok(fisher.state == "", "putting the rod away stops fishing")
	_done()


## The rules on their own (section 7.2, D-135).
func _rules() -> void:
	var rows := {}
	for r in GameData.tiers["fishing"]:
		rows[r.id] = r
	_ok(is_equal_approx(Fishing.catch_time(rows.minnow, "driftwood_rod"), 30.0), "a minnow takes 30 s with the starter rod")
	_ok(is_equal_approx(Fishing.catch_time(rows.minnow, "ash_rod"), 28.5), "a better rod is 5% faster a tier")
	_ok(is_equal_approx(Fishing.catch_time(rows.bloodfin_snapper, "silverbark_rod"), 300.0), "a snapper takes 300 s")
	_ok(is_equal_approx(Fishing.bite_window(rows.minnow, "driftwood_rod"), 1.5), "the tier 1 window is 1.5 s with no reel")
	_ok(is_equal_approx(Fishing.bite_window(rows.minnow, "ash_rod"), 1.65), "a Tin reel widens it x1.1")
	_ok(is_equal_approx(Fishing.bite_window(rows.bloodfin_snapper, "silverbark_rod"), 1.5 * 0.72 * 1.4), "tier 8 with a Bronze reel")
	_ok(Fishing.blocker(rows.trout, "birch_rod") in ["", "Inventory full"], "a Birch Rod catches trout")
	_ok(Fishing.blocker(rows.catfish, "birch_rod") == "Needs an Oak Rod or better", "a Birch Rod can't catch catfish")
	for t in GameData.tools_of["rod"]:      # any rod of the fish's tier or above works
		for r in GameData.tiers["fishing"]:
			var ok: bool = Fishing.blocker(r, t.id) in ["", "Inventory full"]
			_ok(ok == (int(t.tier) >= int(r.tier)), "%s on %s: %s" % [t.label, r.label, "fishes" if ok else "blocked"])
	var saved_held: String = Inventory.held.rod
	var saved_owned: Array = Inventory.owned.rod.duplicate()
	Inventory.owned.rod = ["driftwood_rod", "voidwood_rod", "oak_rod"]
	Inventory.held.rod = "driftwood_rod"
	_ok(Fishing.rod_for(rows.trout) == "oak_rod", "a weak equipped rod: the weakest owned rod that reaches is used")
	_ok(Fishing.rod_for(rows.minnow) == "driftwood_rod", "the equipped rod is kept when it reaches")
	Inventory.held.rod = "voidwood_rod"
	_ok(Fishing.rod_for(rows.minnow) == "voidwood_rod", "a top-tier rod fishes a tier 1 fish")
	Inventory.owned.rod = saved_owned
	Inventory.held.rod = saved_held
	for id in Fishing.TIMES:
		_ok(rows.has(id), "%s is a fish in GameData" % id)


func _frames(n: int) -> void:
	for i in n:
		await get_tree().physics_frame


## Waits (in real seconds) until cond() is true. False if it timed out.
func _until(cond: Callable, secs: float) -> bool:
	var end := Time.get_ticks_msec() + int(secs * 1000.0)
	while Time.get_ticks_msec() < end:
		if cond.call():
			return true
		await get_tree().process_frame
	return cond.call()


func _done() -> void:
	print("fishing: %s" % ("all passed" if _fails == 0 else "%d failed" % _fails))
	get_tree().quit(_fails)


func _ok(cond: bool, what: String) -> void:
	if not cond:
		_fails += 1
		print("FAIL ", what)
