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
var sockets := {}            # tool id -> the gem or pearl inlaid in it (D-130, D-134)
var unfolded := {}           # crafting mechanics this player has met (E1, Proposed): "parts", "take_apart", "socket"
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
	if GameData.items.has(id) and GameData.items[id].kind == "part":
		unfolded["parts"] = true                      # E1: the workbench shows part rows from now on
	changed.emit()
	return true


## Something gathered in the world (a chopped tree's log; mining, foraging and fishing use this too):
## into the inventory, with the "+1 Pine log" line on the HUD. False (and "Inventory full") if no room.
func gain(id: String, n := 1, rare := false) -> bool:
	if not add(id, n):
		return false
	looted.emit(id, n, rare)
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


## One tool of each kind is equipped (held[kind], the tool bar). Every other tool the player owns is
## kept in the inventory grid, one slot each, as items[tool id] = 1. Equipping one from the grid
## (dragging it onto its tool slot) swaps it with the equipped one, which takes its place in the grid.
func is_tool(id: String) -> bool:
	return GameData.tools.has(id)


## Equips this owned tool (swapping it with the one equipped, which goes into its grid slot) and puts
## that kind in the Imp's hand.
func hold(id: String) -> void:
	var kind: String = GameData.tools[id].kind
	if not owns(id):
		return
	var old: String = held[kind]
	if old != id:
		_replace_item(id, old)
		held[kind] = id
	in_hand = kind
	held_changed.emit(id)
	changed.emit()


## Puts `new_id` in `old_id`'s place in the grid (the same slot), or just removes `old_id`.
func _replace_item(old_id: String, new_id: String) -> void:
	var out := {}
	for k in items:
		if k == old_id:
			if new_id != "":
				out[new_id] = 1
		else:
			out[k] = items[k]
	if not items.has(old_id) and new_id != "":
		out[new_id] = 1
	items = out


func take_out(kind: String) -> void:
	if in_hand != kind:
		in_hand = kind
		held_changed.emit(held[kind])
		changed.emit()


## Tools in the grid and equipped agree with `owned`: every owned tool that is not equipped has a grid
## slot (saves from before this rule had them all on the tool bar), and nothing else is a tool slot.
func sync_tools() -> void:
	for kind in GameData.TOOL_KINDS:
		if not held[kind] in owned[kind]:          # testing (--axe): an equipped tool counts as owned
			owned[kind].append(held[kind])
	for id in items.keys():
		if is_tool(id) and (not owns(id) or held[GameData.tools[id].kind] == id):
			items.erase(id)
	for kind in owned:
		for id in owned[kind]:
			if id != held[kind] and not items.has(id):
				items[id] = 1
	for id in sockets.keys():                     # an inlay goes with its tool
		if not GameData.tools.has(id) or not owns(id):
			sockets.erase(id)
	changed.emit()


## The next owned tool of the kind in hand, in tier order (the old demo's Q; it swaps like a drag).
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
	if randf() < row.rare_chance * rare_boost(skill, row.tier) and add(row.rare):
		looted.emit(row.rare, 1, true)


## How much the rare-drop chance is raised for this skill (D-133): the Stellarite pickaxe x2 for gems (D-059),
## a tracking animal x1.5 for trophies of its tier or below (D-072) and an inlay x1.25 on the tool in use
## (D-130), multiplied and capped at x2.5. Potions aren't built. Mint token chances never change (D-045).
func rare_boost(skill: String, tier := 0) -> float:
	var boost := 1.0
	if skill == "mining" and held.pickaxe == GameData.GEM_BOOST_TOOL:
		boost *= 2.0
	if skill == "hunting" and tier > 0 and Stable.tracker_tier() >= tier:
		boost *= 1.5
	if sockets.has(held[GameData.SKILLS[skill].tool]):
		boost *= GameData.INLAY_BOOST
	return minf(boost, GameData.RARE_BOOST_CAP)


## The boost a tool gives on its own while held (D-059, D-130), capped (D-133): what the workbench shows.
func tool_boost(t: Dictionary) -> float:
	var boost := 2.0 if t.id == GameData.GEM_BOOST_TOOL else 1.0
	if sockets.has(t.id):
		boost *= GameData.INLAY_BOOST
	return minf(boost, GameData.RARE_BOOST_CAP)


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


# --- crafting (D-006, D-058, D-060, D-063, D-069, D-106, D-107, D-110; parts D-125 to D-134) ---------
## Hilts and parts are made at the station of their material (D-127) and every tool except the sword is
## put together at the workbench from its parts (D-125). Nothing costs energy (D-056).

## Why this hilt or part can't be made yet ("Unlocks at Mining 5"), or "". A working part unlocks with its
## tool (P6, Proposed); hilts and fittings are always open.
func part_lock(id: String) -> String:
	var tool_id: String = GameData.items[id].get("tool", "")
	return recipe_lock(GameData.tools[tool_id]) if tool_id != "" else ""


## How many of this hilt or part the player can make now: 0 if it's locked or a new item has no slot.
func makeable(id: String) -> int:
	var cost := GameData.part_cost(id)
	if cost.is_empty() or part_lock(id) != "" or not has_room(id):
		return 0
	var n := 1 << 30
	for k in cost:
		n = mini(n, count(k) / int(cost[k]))
	return n


## Makes n of a hilt or part (fittings in batches of 1, 5 or all, M5; the menu offers the rest one at a time).
func make(id: String, n := 1) -> void:
	n = mini(n, makeable(id))
	if n < 1:
		return
	var cost := GameData.part_cost(id)
	for k in cost:
		remove(k, cost[k] * n)
	add(id, n)
	looted.emit(id, n, false)


## A tool's materials plus its hilt: the sword's whole recipe (it isn't assembled from parts).
func tool_cost(t: Dictionary) -> Dictionary:
	var cost: Dictionary = t.cost.duplicate()
	if t.hilt:
		cost[t.hilt] = 1
	return cost


## A tool's whole recipe as the workbench shows it before parts unfold (E1): its decided materials and
## hilt, as the menu showed them before parts, plus what its fittings are made from.
func flat_cost(t: Dictionary) -> Dictionary:
	if not GameData.is_assembled(t):
		return tool_cost(t)
	var out := {}
	for p in t.parts:
		var src: Dictionary = {p: 1} if GameData.items[p].kind == "hilt" else GameData.part_cost(p)
		for k in src:
			out[k] = out.get(k, 0) + src[k] * t.parts[p]
	return out


## What Craft takes from the bag (M4, D-131): the parts already in it, and for each missing part the
## processed materials it's made from (ingots, planks, leather, bundles; never raw ones). `moved` is a part
## that comes across by re-hafting (M7), so it isn't needed. {use, short}, both {item: count}.
func _plan(t: Dictionary, moved := "") -> Dictionary:
	var use := {}
	for p in t.parts:
		if p == moved:
			continue
		var need: int = t.parts[p]
		var have := mini(count(p), need)
		if have > 0:
			use[p] = have
		if need > have:
			var cost := GameData.part_cost(p)
			for k in cost:
				use[k] = use.get(k, 0) + cost[k] * (need - have)
	var short := {}
	for k in use:
		if count(k) < use[k]:
			short[k] = use[k] - count(k)
	return {use = use, short = short}


## Why Craft can't put this tool together now, or "". Assembly needs the tool's unlock level as well as its
## parts (M6), so a bought or traded part never skips a level.
func craft_blocker(t: Dictionary, moved := "") -> String:
	if not GameData.is_assembled(t):
		return "Not made at the workbench"
	if owns(t.id):
		return "Owned"
	var lock := recipe_lock(t)
	if lock != "":
		return lock
	if not _plan(t, moved).short.is_empty():
		return "Missing materials"
	if moved == "" and not has_room(t.id):        # a re-hafted tool takes the old one's place
		return "Inventory full"
	return ""


## The shopping list when something is short (D-131, E1): a line per missing material saying where it's made
## and from what, e.g. "1 Nettle bundle: drying rack, from 2 Nettle (Stone sickle)".
func shopping_list(t: Dictionary, moved := "") -> Array:
	var lines := []
	var short: Dictionary = _plan(t, moved).short
	for k in short:
		lines.append(_where_from(k, short[k]))
	return lines


func _where_from(id: String, n: int) -> String:
	var it: Dictionary = GameData.items[id]
	var text := "%d %s" % [n, it.label]
	if not GameData.SKILLS.has(it.skill):
		return text
	var skill: Dictionary = GameData.SKILLS[it.skill]
	var row := GameData.row_by_tier(it.skill, it.tier)
	match it.kind:
		"made":
			var from := "%d %s" % [n * row.per, GameData.item_label(row.raw)]
			if row.fuel_count > 0 and row.fuel != GameData.ANY_LOG:
				from += " and %d %s" % [n * row.fuel_count, GameData.item_label(row.fuel)]
			return "%s: %s, from %s (%s)" % [text, GameData.STATIONS[skill.station].label.to_lower(), from,
					GameData.tool_for_tier(skill.tool, row.tier).label]
		"rare":
			return "%s: a rare find when you %s %s" % [text, skill.verb.to_lower(), row.label]
		"raw":
			return "%s: %s %s (%s)" % [text, skill.verb.to_lower(), row.label, GameData.tool_for_tier(skill.tool, row.tier).label]
	return text


## The owned tool that Re-haft would take apart for this one (M7, D-129): the tier below, of the same kind,
## when the part it gives back (hilt, reel or stave) is one this tool takes. "" if there is none.
func rehaft_from(t: Dictionary) -> String:
	if not GameData.is_assembled(t) or owns(t.id) or t.tier < 3:
		return ""
	var below: Dictionary = GameData.tools_of[t.kind][t.tier - 2]
	if owns(below.id) and GameData.is_assembled(below) and t.parts.has(below.returns):
		return below.id
	return ""


## Craft (E1): makes any missing part from the processed materials in the bag (M4), then assembles the tool
## and equips it. With `rehaft`, the tool of the tier below is taken apart and its hilt, reel or stave goes
## straight into the new one (M7); the rest of it, and any inlay, is used up. False if it can't.
func craft(t: Dictionary, rehaft := false) -> bool:
	var from := rehaft_from(t) if rehaft else ""
	if rehaft and from == "":
		return false
	var moved: String = GameData.tools[from].returns if from != "" else ""
	var why := craft_blocker(t, moved)
	if why != "":
		message.emit(why)
		return false
	_pay(_plan(t, moved).use)
	owned[t.kind].append(t.id)
	owned[t.kind].sort_custom(func(a, b): return GameData.tools[a].tier < GameData.tools[b].tier)
	if from == "":
		items[t.id] = 1                              # into the grid, then equipped: the old one takes its slot
		hold(t.id)
	else:
		owned[t.kind].erase(from)
		sockets.erase(from)
		if held[t.kind] == from:                     # it was in hand: the new one takes its place there
			held[t.kind] = t.id
			in_hand = t.kind
			held_changed.emit(t.id)
			changed.emit()
		else:
			_replace_item(from, t.id)
			hold(t.id)
	if owned[t.kind].filter(func(id): return GameData.is_assembled(GameData.tools[id])).size() >= 2 or from != "":
		unfolded["take_apart"] = true
	looted.emit(t.id, 1, true)
	return true


## Why this tool can't be taken apart (M8), or "". Starter tools and swords have no parts, and the tool on
## the tool bar has to be swapped out first, so no one is ever left without a tool.
func take_apart_blocker(id: String) -> String:
	var t: Dictionary = GameData.tools[id]
	if not owns(id) or not GameData.is_assembled(t):
		return "It has no parts to take back"
	if held[t.kind] == id:
		return "Equip another %s first" % GameData.TOOL_KINDS[t.kind].label.to_lower()
	return ""


## Takes an owned tool apart (M8, D-129): its hilt, reel or stave goes back into the bag, into the tool's
## slot; the rest, and any inlay, is used up.
func take_apart(id: String) -> void:
	if take_apart_blocker(id) != "":
		return
	var t: Dictionary = GameData.tools[id]
	owned[t.kind].erase(id)
	sockets.erase(id)
	if items.has(t.returns):
		items.erase(id)
		items[t.returns] += 1
	else:
		_replace_item(id, t.returns)
	changed.emit()
	looted.emit(t.returns, 1, false)


## True if this gem (D-130) or pearl (D-134) fits the tool's socket: tier N-1 or higher, so bows from tier
## 11 take the top of each ladder (Eclipsium, Star Pearl).
func socket_fits(t: Dictionary, gem: String) -> bool:
	if not GameData.is_assembled(t) or not GameData.items.has(gem):
		return false
	var it: Dictionary = GameData.items[gem]
	return it.kind == "rare" and it.skill in ["mining", "fishing"] and it.tier >= mini(t.tier - 1, 10)


## The cheapest gem or pearl in the bag that fits this tool, or "". They all give the same x1.25.
func inlay_choice(t: Dictionary) -> String:
	var best := ""
	for id in items:
		if socket_fits(t, id) and (best == "" or GameData.sell_price(id) < GameData.sell_price(best)):
			best = id
	return best


## Sets a gem or pearl into an owned tool's empty socket (M9). It's used up and can't be taken out again.
func inlay(tool_id: String, gem: String) -> void:
	var t: Dictionary = GameData.tools[tool_id]
	if not owns(tool_id) or sockets.has(tool_id) or not socket_fits(t, gem) or count(gem) < 1:
		return
	sockets[tool_id] = gem
	unfolded["socket"] = true
	remove(gem, 1)
	if held[t.kind] == tool_id:
		held_changed.emit(tool_id)


## Marks a crafting mechanic as met (E1) when a menu first shows it. The change is announced next frame,
## so a menu can call this while it draws.
func unfold(flag: String) -> void:
	if not unfolded.has(flag):
		unfolded[flag] = true
		changed.emit.call_deferred()


## E1: the workbench shows part rows from the first time a part or fitting is in the bag, however it got there.
func parts_unfolded() -> bool:
	if not unfolded.has("parts"):
		for id in items:
			if GameData.items.has(id) and GameData.items[id].kind == "part":
				unfold("parts")
				break
	return unfolded.has("parts")


## An item's or tool's picture for menus; an inlaid tool shows its gem in the corner.
func icon_of(id: String) -> Texture2D:
	return GameData.tool_icon(id, sockets.get(id, "")) if is_tool(id) else GameData.item_icon(id)


## Why the recipe is still locked ("Unlocks at Mining 15"), or "". A pickaxe needs mining level 5 per tier above
## stone and an axe lumbering level 5 per tier (GameData.recipe_level); nothing is locked while levels aren't built.
func recipe_lock(t: Dictionary) -> String:
	var need := GameData.recipe_level(t)
	if need <= 0:
		return ""
	var skill: String = GameData.RECIPE_SKILL[t.kind]
	var have := GameData.skill_level(skill)
	if have < 0 or have >= need:
		return ""
	return "Unlocks at %s %d" % [GameData.SKILLS[skill].label, need]


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


## Buys n of an item from the merchant at GameData.buy_price (J00BA, 2026-11-15). False (with a message)
## if it costs more than the coins held or a new item has no free slot.
func buy(id: String, n: int) -> bool:
	var price := GameData.buy_price(id)
	if n < 1 or price <= 0:
		return false
	if coins < price * n:
		message.emit("Not enough coins")
		return false
	if not add(id, n):
		return false
	_set_coins(coins - price * n)
	return true


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
	extra_rows = maxi(extra_rows, 20)   # room for every tool in the grid (past the TEST cap)
	sync_tools()


## Empties the whole inventory grid: every item and every spare tool. Only the tools equipped on the tool
## bar are kept (one per kind), so the player can keep gathering with the grid free.
func test_clear_items() -> void:
	items.clear()
	for kind in owned:
		owned[kind] = [held[kind]]
	sync_tools()


func test_add_coins(n := 1000) -> void:
	_set_coins(coins + n)
