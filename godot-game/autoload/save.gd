extends Node
## Keeps the player's progress between visits, as the Save autoload: items, tools, coins, bought
## rows and the stable. Energy already keeps itself (Inventory.ENERGY_FILE).
##
## TEST, on this device only: the file is user://save.json (the browser's storage in the web
## build), so a player can edit it. That is fine while nothing is worth anything. Once the server
## is connected (Api, ACCOUNTS-AND-DATA section 9), the server keeps the real copy and every change
## goes through a server function; this file is then only for playing offline.
## Ids the game no longer knows are dropped on load, so an old save never breaks a newer build.

const FILE := "user://save.json"
const VERSION := 1
const DELAY := 1.0           # seconds of quiet before writing, so a burst of changes is one write

var _timer := Timer.new()


func _ready() -> void:
	_timer.one_shot = true
	_timer.wait_time = DELAY
	_timer.timeout.connect(write)
	add_child(_timer)
	read()
	for s in [Inventory.changed, Inventory.coins_changed, Inventory.held_changed, Stable.changed]:
		s.connect(func(_a = null): _timer.start())


func _notification(what: int) -> void:
	if what == NOTIFICATION_WM_CLOSE_REQUEST or what == NOTIFICATION_EXIT_TREE:
		if not _timer.is_stopped():
			write()


func state() -> Dictionary:
	return {
		version = VERSION,
		inventory = {
			items = Inventory.items, owned = Inventory.owned, held = Inventory.held,
			in_hand = Inventory.in_hand, coins = Inventory.coins, extra_rows = Inventory.extra_rows,
			refill_period = Inventory.refill_period,
		},
		stable = {
			animals = Stable.animals, follower = Stable.follower, team = Stable.team,
			extra_slots = Stable.extra_slots, wins_period = Stable.wins_period,
			paid_wins = Stable.paid_wins, next_uid = Stable._next_uid,
		},
	}


func write() -> void:
	_timer.stop()
	var f := FileAccess.open(FILE, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify(state()))


func read() -> void:
	if not FileAccess.file_exists(FILE):
		return
	var json := JSON.new()
	if json.parse(FileAccess.get_file_as_string(FILE)) != OK:
		return
	var data = json.data
	if not data is Dictionary or int(data.get("version", 0)) != VERSION:
		return
	_apply_inventory(data.get("inventory", {}))
	_apply_stable(data.get("stable", {}))


func _apply_inventory(inv: Dictionary) -> void:
	var items := {}
	for id in inv.get("items", {}):
		if GameData.items.has(id) and int(inv.items[id]) > 0:
			items[id] = int(inv.items[id])
	Inventory.items = items
	for kind in GameData.TOOL_KINDS:
		var list: Array = Inventory.owned[kind]          # always keeps the free tier 1 tool
		for id in inv.get("owned", {}).get(kind, []):
			if GameData.tools.has(id) and GameData.tools[id].kind == kind and not id in list:
				list.append(id)
		list.sort_custom(func(a, b): return GameData.tools[a].tier < GameData.tools[b].tier)
		var held: String = inv.get("held", {}).get(kind, "")
		if held in list:
			Inventory.held[kind] = held
	if inv.get("in_hand", "") in GameData.TOOL_KINDS:
		Inventory.in_hand = inv.in_hand
	Inventory.coins = maxi(0, int(inv.get("coins", 0)))
	Inventory.extra_rows = clampi(int(inv.get("extra_rows", 0)), 0, GameData.EXTRA_ROWS_MAX)
	Inventory.refill_period = int(inv.get("refill_period", -1))


func _apply_stable(st: Dictionary) -> void:
	var animals := []
	for a in st.get("animals", []):
		if a is Dictionary and GameData.tier_row("hunting", str(a.get("id", ""))) != {}:
			animals.append({uid = int(a.uid), id = str(a.id), level = int(a.get("level", 1)), xp = int(a.get("xp", 0))})
	Stable.animals = animals
	var uids := animals.map(func(a): return a.uid)
	Stable.follower = int(st.get("follower", -1)) if int(st.get("follower", -1)) in uids else -1
	Stable.team = st.get("team", []).map(func(u): return int(u)).filter(func(u): return u in uids)
	Stable.extra_slots = clampi(int(st.get("extra_slots", 0)), 0, GameData.EXTRA_SLOTS_MAX)
	Stable.wins_period = int(st.get("wins_period", -1))
	Stable.paid_wins = int(st.get("paid_wins", 0))
	Stable._next_uid = maxi(int(st.get("next_uid", 1)), (uids.max() if not uids.is_empty() else 0) + 1)
