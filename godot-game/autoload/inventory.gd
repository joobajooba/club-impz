extends Node
## The player's items, tools, energy and coins, and the rules that change them: gathering,
## processing at stations, crafting and the merchant. Loaded as the Inventory autoload.
## Energy is kept in user:// on this device; the Save autoload keeps the rest there too (TEST, until
## the server is connected, GODOT.md G6). Later the server decides drops (ACCOUNTS-AND-DATA
## section 8); for now they are rolled here.

signal changed                                   # items, tools, room
signal energy_changed(value: int)
signal coins_changed(value: int)
signal held_changed(id: String)                  # the tool in the Imp's hand
signal looted(id: String, count: int, rare: bool)
signal message(text: String)                     # short notices: "Inventory full", "It got away"

const ENERGY_FILE := "user://energy.json"

var items := {}              # item id -> count, in pickup order
var owned := {}              # tool kind -> Array of tool ids, tier order
var held := {}               # tool kind -> the tool of that kind the player uses
var in_hand := "pickaxe"     # which kind the Imp is holding
var energy := GameData.ENERGY_MAX
var coins := 0               # TEST: coins from staking arrive with accounts (G6)
var extra_rows := 0          # bought inventory rows (D-077)
var refill_period := -1      # the reset period of the last bought refill (D-076: one per reset)
var _period := 0


func _ready() -> void:
	for kind in GameData.TOOL_KINDS:   # everyone starts with each kind's tier 1 tool
		var first: String = GameData.tools_of[kind][0].id
		owned[kind] = [first]
		held[kind] = first
	_period = period()
	var saved = null
	if FileAccess.file_exists(ENERGY_FILE):
		saved = JSON.parse_string(FileAccess.get_file_as_string(ENERGY_FILE))
	if saved is Dictionary and int(saved.get("period", -1)) == _period:
		energy = clampi(int(saved.get("value", GameData.ENERGY_MAX)), 0, GameData.ENERGY_MAX)


func _process(_delta: float) -> void:
	if period() != _period:
		_period = period()
		_set_energy(GameData.ENERGY_MAX)


# --- items and room -------------------------------------------------------------

func count(id: String) -> int:
	return items.get(id, 0)


func slots() -> int:
	return (GameData.INVENTORY_ROWS + extra_rows) * GameData.INVENTORY_COLUMNS


## A new kind of item needs a free slot; more of one already held always fits.
func has_room(id: String) -> bool:
	return items.has(id) or items.size() < slots()


## Adds what fits. Returns false (and says so) if a new item had no slot.
func add(id: String, n := 1) -> bool:
	if not has_room(id):
		message.emit("Inventory full: no room for " + GameData.item_label(id))
		return false
	items[id] = count(id) + n
	changed.emit()
	return true


func remove(id: String, n: int) -> void:
	var left := count(id) - n
	if left > 0:
		items[id] = left
	else:
		items.erase(id)
	changed.emit()


func has_all(cost: Dictionary) -> bool:
	for id in cost:
		if count(id) < cost[id]:
			return false
	return true


func _pay(cost: Dictionary) -> void:
	for id in cost:
		remove(id, cost[id])


# --- energy (D-008, D-057, D-061) -------------------------------------------------

## 12-hour blocks counted from the Unix epoch, which starts at 00:00 UTC, so a new block starts at
## 00:00 and 12:00 UTC for every player.
func period() -> int:
	return int(Time.get_unix_time_from_system()) / GameData.RESET_SECONDS


func seconds_to_reset() -> int:
	return GameData.RESET_SECONDS - int(Time.get_unix_time_from_system()) % GameData.RESET_SECONDS


func _set_energy(value: int) -> void:
	energy = clampi(value, 0, GameData.ENERGY_MAX)
	var f := FileAccess.open(ENERGY_FILE, FileAccess.WRITE)
	if f:
		f.store_string(JSON.stringify({value = energy, period = _period}))
	energy_changed.emit(energy)


# --- tools ----------------------------------------------------------------------

func held_tool(kind: String) -> Dictionary:
	return GameData.tools[held[kind]]


func owns(tool_id: String) -> bool:
	return tool_id in owned[GameData.tools[tool_id].kind]


## Puts a tool of this kind in the Imp's hand (the held one unless `id` is given).
func hold(id: String) -> void:
	var kind: String = GameData.tools[id].kind
	if not owns(id):
		return
	held[kind] = id
	in_hand = kind
	held_changed.emit(id)
	changed.emit()


func take_out(kind: String) -> void:
	if in_hand != kind:
		hold(held[kind])


## Q: the next owned tool of the kind in hand, in tier order.
func cycle_held() -> void:
	var list: Array = owned[in_hand]
	hold(list[(list.find(held[in_hand]) + 1) % list.size()])


# --- gathering (D-006 to D-012, D-024, D-034, D-059, D-061, D-072) ---------------

## Why the player can't gather this now, or "" if they can.
func gather_blocker(skill: String, row: Dictionary) -> String:
	var kind: String = GameData.SKILLS[skill].tool
	if held_tool(kind).reach < row.tier:
		var best = _best_owned(kind, row.tier)
		return ("Switch to your " + best.label) if best else ("Needs a " + GameData.tool_for_tier(kind, row.tier).label)
	if energy < GameData.GATHER_ENERGY:
		return "Not enough energy"
	if not has_room(row.raw):
		return "Inventory full"
	return ""


func _best_owned(kind: String, tier: int):
	for id in owned[kind]:
		if GameData.tools[id].reach >= tier:
			return GameData.tools[id]
	return null


## Uses the weakest owned tool of this kind that reaches the tier, if the held one doesn't.
func pick_tool_for(skill: String, row: Dictionary) -> void:
	var kind: String = GameData.SKILLS[skill].tool
	if held_tool(kind).reach < row.tier:
		var best = _best_owned(kind, row.tier)
		if best:
			hold(best.id)
	take_out(kind)


## One gathering action finished: take the energy, give the raw item and roll the rare drop.
func gather(skill: String, row: Dictionary) -> void:
	_set_energy(energy - GameData.GATHER_ENERGY)
	if add(row.raw):
		looted.emit(row.raw, 1, false)
	var chance: float = row.rare_chance
	if skill == "mining" and held.pickaxe == GameData.GEM_BOOST_TOOL:
		chance *= 2.0                                    # D-059
	if skill == "hunting" and Stable.tracker_tier() >= row.tier:
		chance *= 1.5                                    # D-072
	if randf() < chance and add(row.rare):
		looted.emit(row.rare, 1, true)


# --- stations: furnace, drying rack, tanning rack, sawbench, campfire -----------

## Fuel this row needs for `n` made items, as {item: count}. Campfire logs can be any log,
## lowest tier first (Proposed in 02).
func fuel_for(row: Dictionary, n: int) -> Dictionary:
	var need: int = row.fuel_count * n
	if need <= 0:
		return {}
	if row.fuel != GameData.ANY_LOG:
		return {row.fuel: need}
	var out := {}
	for tree in GameData.tiers.lumbering:
		var take := mini(count(tree.raw), need)
		if take > 0:
			out[tree.raw] = take
			need -= take
		if need == 0:
			break
	return out if need == 0 else {"": need}   # "" marks fuel that is missing


func _fuel_total(row: Dictionary) -> int:
	if row.fuel != GameData.ANY_LOG:
		return count(row.fuel)
	var total := 0
	for tree in GameData.tiers.lumbering:
		total += count(tree.raw)
	return total


## How many made items the player can make now.
func processable(row: Dictionary) -> int:
	if row.per <= 0 or not row.made:
		return 0
	var n: int = count(row.raw) / row.per
	if row.fuel_count > 0:
		n = mini(n, _fuel_total(row) / row.fuel_count)
	return n if has_room(row.made) else 0


func process(row: Dictionary, n: int) -> void:
	n = mini(n, processable(row))
	if n < 1:
		return
	_pay(fuel_for(row, n))
	remove(row.raw, n * row.per)
	add(row.made, n)
	looted.emit(row.made, n, false)


# --- crafting (D-006, D-058, D-060, D-063, D-069, D-106, D-107, D-110) -----------

func can_craft_hilt(id: String) -> bool:
	return has_all(GameData.HILTS[id].cost) and has_room(id)


func craft_hilt(id: String) -> void:
	if can_craft_hilt(id):
		_pay(GameData.HILTS[id].cost)
		add(id)
		looted.emit(id, 1, false)


## A tool's full cost: its materials plus its hilt.
func tool_cost(t: Dictionary) -> Dictionary:
	var cost: Dictionary = t.cost.duplicate()
	if t.hilt:
		cost[t.hilt] = 1
	return cost


func can_craft_tool(t: Dictionary) -> bool:
	return not t.cost.is_empty() and not owns(t.id) and has_all(tool_cost(t))


func craft_tool(t: Dictionary) -> void:
	if not can_craft_tool(t):
		return
	_pay(tool_cost(t))
	owned[t.kind].append(t.id)
	owned[t.kind].sort_custom(func(a, b): return GameData.tools[a].tier < GameData.tools[b].tier)
	hold(t.id)
	looted.emit(t.id, 1, true)


# --- the merchant (D-073 to D-077; prices are TEST) -------------------------------

func _set_coins(value: int) -> void:
	coins = value
	coins_changed.emit(coins)


func sell(id: String, n: int) -> void:
	n = mini(n, count(id))
	var price := GameData.sell_price(id)
	if n < 1 or price <= 0:
		return
	remove(id, n)
	_set_coins(coins + price * n)


func row_price() -> int:
	return GameData.ROW_PRICE << extra_rows


func buy_row() -> void:
	if extra_rows < GameData.EXTRA_ROWS_MAX and coins >= row_price():
		_set_coins(coins - row_price())
		extra_rows += 1
		changed.emit()


func can_refill() -> bool:
	return refill_period != period() and energy < GameData.ENERGY_MAX and coins >= GameData.REFILL_PRICE


## D-076: at most one per reset. Mint tokens (G8) must never roll on refilled energy.
func buy_refill() -> void:
	if can_refill():
		_set_coins(coins - GameData.REFILL_PRICE)
		refill_period = period()
		_set_energy(GameData.ENERGY_MAX)


func earn(n: int) -> void:
	_set_coins(coins + n)


func spend(n: int) -> bool:
	if coins < n:
		return false
	_set_coins(coins - n)
	return true


# --- TEST tools, for reviewers to try every tier quickly. Remove before launch. ---

func test_refill_energy() -> void:
	_set_energy(GameData.ENERGY_MAX)


## 20 of every raw item of every skill.
func test_add_raw(n := 20) -> void:
	for skill in GameData.tiers:
		for row in GameData.tiers[skill]:
			items[row.raw] = count(row.raw) + n
	extra_rows = maxi(extra_rows, 20)   # room for all of it and what it makes (past the TEST cap)
	changed.emit()


func test_unlock_tools() -> void:
	for kind in owned:
		owned[kind] = GameData.tools_of[kind].map(func(t): return t.id)
	changed.emit()


func test_add_coins(n := 1000) -> void:
	_set_coins(coins + n)
