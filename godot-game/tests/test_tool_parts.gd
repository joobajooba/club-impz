extends Node
## Headless test for tool parts (TOOL-CRAFTING-ROADMAP B5). Run from the repo root:
##   godot --headless --path godot-game res://tests/test_tool_parts.tscn
## Exits with the number of failed checks (0 = all passed). It never writes the player's save (Save.enabled).
##
## The decided recipes are written out here again, from DECISIONS.md, so the check doesn't just read back
## GameData: each crafted tool must cost its decided material and hilt (D-006, D-058, D-060, D-063, D-069,
## D-106, D-107, D-110) plus its fitting (D-125), nothing more.

const METALS := ["bronze", "iron", "steel", "gold", "obsidian", "titanite", "dreadstone", "void", "stellarite"]
const PICKAXE_INGOTS := [{tin_ingot = 5, copper_ingot = 5}, {iron_ingot = 5}, {iron_ingot = 10}, {gold_ingot = 10},
		{obsidian_ingot = 10}, {titanite_ingot = 10}, {dreadstone_ingot = 10}, {void_ingot = 10}, {stellarite_ingot = 10}]
const HILT := ["ash_hilt", "ash_hilt", "ash_hilt", "ash_hilt", "oak_hilt", "oak_hilt", "oak_hilt", "void_hilt", "cosmic_hilt"]

var _fails := 0


func _ready() -> void:
	Save.enabled = false
	GameData._test_levels_read = true
	_check_recipes()
	_check_prices()
	_check_craft()
	_check_lock()
	_check_make()
	_check_rehaft_and_take_apart()
	_check_inlays()
	_check_save()
	_check_menus()
	print("tool parts: %s" % ("all passed" if _fails == 0 else "%d failed" % _fails))
	get_tree().quit(_fails)


func _ok(cond: bool, what: String) -> void:
	if not cond:
		_fails += 1
		print("FAIL ", what)


func _reset() -> void:
	GameData._test_levels = {}
	Inventory.items = {}
	Inventory.sockets = {}
	Inventory.unfolded = {}
	for kind in GameData.TOOL_KINDS:
		var first: String = GameData.tools_of[kind][0].id
		Inventory.owned[kind] = [first]
		Inventory.held[kind] = first


func _give(cost: Dictionary) -> void:
	for k in cost:
		Inventory.items[k] = Inventory.count(k) + int(cost[k])


static func _sum(a: Dictionary, b: Dictionary) -> Dictionary:
	var out := a.duplicate()
	for k in b:
		out[k] = out.get(k, 0) + b[k]
	return out


# --- recipes --------------------------------------------------------------------------

func _expected(t: Dictionary) -> Dictionary:
	var i: int = t.tier - 2
	var cord := {nettle_bundle = 1}
	match t.kind:
		"pickaxe", "sickle":
			return _sum(_sum(PICKAXE_INGOTS[i], {HILT[i]: 1}), cord if t.tier <= 5 else {hare_leather = 1})
		"axe":
			var half := {}
			for k in PICKAXE_INGOTS[i]:
				half[k] = ceili(PICKAXE_INGOTS[i][k] / 2.0)
			return _sum(_sum(half, {HILT[i]: 1}), cord if t.tier <= 5 else {hare_leather = 1})
		"rod":
			var reel: Dictionary = {tin_ingot = 1} if t.tier <= 4 else ({copper_ingot = 1} if t.tier <= 7 else {tin_ingot = 1, copper_ingot = 1})
			return _sum(_sum({GameData.tiers.lumbering[t.tier - 2].made: 10}, reel), cord)
		"bow":
			return _sum(_sum({GameData.tiers.hunting[t.tier - 2].made: 10}, {ash_plank = 2}), cord)
	return {}


func _check_recipes() -> void:
	var counts := {pickaxe = 9, axe = 9, sickle = 9, rod = 9, bow = 15}
	for kind in counts:
		var n := 0
		for t in GameData.tools_of[kind]:
			if t.tier == 1:
				_ok(not GameData.is_assembled(t), "%s is a starter tool with no parts (P7)" % t.id)
				continue
			n += 1
			_ok(GameData.is_assembled(t), "%s has parts" % t.id)
			_ok(t.parts.size() == 3, "%s has three parts (P1)" % t.id)
			_ok(GameData.items.has(t.part) and GameData.items[t.part].kind == "part", "%s's part %s is a bag item (D-126)" % [t.id, t.part])
			var flat := Inventory.flat_cost(t)
			var want := _expected(t)
			_ok(flat == want, "%s costs its decided recipe plus its fitting: %s, want %s" % [t.id, flat, want])
		_ok(n == counts[kind], "%d crafted %ss" % [counts[kind], kind])
	_ok(not GameData.is_assembled(GameData.tools.bronze_sword), "swords keep their old recipe")
	var ids := ["bronze_pickaxe_head", "stellarite_axe_head", "gold_sickle_blade", "ash_rod_blank", "voidwood_rod_blank",
			"fox_bow_wrap", "eclipse_dragon_bow_wrap", "nettle_cord", "hare_leather_strip", "tin_reel", "copper_reel", "bronze_reel", "bow_stave"]
	for id in ids:
		_ok(GameData.items.has(id), "item %s exists (6.1)" % id)
	var parts := GameData.items.keys().filter(func(id): return GameData.items[id].kind == "part")
	_ok(parts.size() == 57, "57 new bag items (6.1), got %d" % parts.size())
	for id in parts:
		_ok(GameData.item_icon(id) != null, "%s has an icon" % id)


# --- prices (D-132) -----------------------------------------------------------------------

func _check_prices() -> void:
	_ok(GameData.sell_price("tin_ingot") == 5, "Tin ingot still 5 (2 ore x 2, +25%)")
	_ok(GameData.sell_price("gold_ingot") == 48, "Gold ingot still 48 (3 ore, 1 Coal, +25%)")
	_ok(GameData.sell_price("nettle_cord") == 5, "Nettle Cord = 2 Nettle +25%% = 5, got %d" % GameData.sell_price("nettle_cord"))
	_ok(GameData.sell_price("ash_hilt") == 25, "Ash hilt = 10 Ash logs +25%% = 25, got %d" % GameData.sell_price("ash_hilt"))
	_ok(GameData.sell_price("bronze_pickaxe_head") == 75, "Bronze head = 10 Tin + 10 Copper ore, +25%% once = 75, got %d" % GameData.sell_price("bronze_pickaxe_head"))
	_ok(GameData.sell_price("void_hilt") == roundi((2 * GameData.raw_worth("void_ingot") + GameData.sell_price("arcanium")) * 1.25), "Void hilt counts its gem once")
	_ok(GameData.buy_price("nettle_cord") == 0 and GameData.buy_price("ash_hilt") == 0, "the merchant doesn't sell parts or hilts")
	_ok(GameData.sell_price("bronze_pickaxe") == 0, "crafted tools still can't be sold")


# --- Craft (M4, D-131, E1) -----------------------------------------------------------------

func _check_craft() -> void:
	_reset()
	var t: Dictionary = GameData.tools.bronze_pickaxe
	_ok(Inventory.craft_blocker(t) == "Missing materials", "short with an empty bag")
	var list := Inventory.shopping_list(t)
	_ok(list.size() == 4, "shopping list has the 4 materials: %s" % [list])
	_ok(list.any(func(l): return "drying rack" in l and "Nettle" in l), "the list says where the cord's bundle comes from")
	_give(Inventory.flat_cost(t))
	_ok(Inventory.craft(t), "Craft makes the parts and assembles")
	_ok(Inventory.owns("bronze_pickaxe") and Inventory.held.pickaxe == "bronze_pickaxe", "the new tool is equipped")
	_ok(Inventory.items.keys() == ["stone_pickaxe"], "nothing left over but the old pickaxe: %s" % [Inventory.items])
	_ok(not Inventory.unfolded.has("parts"), "Craft alone never unfolds the part rows")
	_ok(not Inventory.craft(t), "can't make a second copy (M3)")


func _check_lock() -> void:
	_reset()
	GameData._test_levels = {mining = 4}
	var t: Dictionary = GameData.tools.bronze_pickaxe
	_give(t.parts)
	_ok(Inventory.craft_blocker(t) == "Unlocks at Mining 5", "bought parts can't skip the level (M6): %s" % Inventory.craft_blocker(t))
	_ok(not Inventory.craft(t), "Craft refuses below the level")
	_give(t.cost)
	_ok(Inventory.part_lock(t.part) != "" and Inventory.makeable(t.part) == 0, "the head's recipe unlocks with the tool (P6)")
	_give({nettle_bundle = 1})
	_ok(Inventory.part_lock("nettle_cord") == "" and Inventory.makeable("nettle_cord") == 1, "fittings are always open")
	GameData._test_levels = {mining = 5}
	_ok(Inventory.craft(t), "Craft works at the level")
	_ok(Inventory.count(t.part) == 0 and Inventory.count("ash_hilt") == 0, "the parts in the bag were used first")


func _check_make() -> void:
	_reset()
	_give({nettle_bundle = 7, tin_ingot = 1, copper_ingot = 1})
	_ok(Inventory.makeable("nettle_cord") == 7, "7 cords from 7 bundles")
	Inventory.make("nettle_cord", 5)
	_ok(Inventory.count("nettle_cord") == 5 and Inventory.count("nettle_bundle") == 2, "x5 batch (M5)")
	_ok(Inventory.unfolded.has("parts"), "a part in the bag unfolds the part rows (E1)")
	Inventory.make("bronze_reel")
	_ok(Inventory.count("bronze_reel") == 1 and Inventory.count("tin_ingot") == 0, "a Bronze Reel takes a Tin and a Copper ingot")


# --- re-haft and take apart (M7, M8, D-129) ------------------------------------------------

func _check_rehaft_and_take_apart() -> void:
	_reset()
	var bronze: Dictionary = GameData.tools.bronze_pickaxe
	var iron: Dictionary = GameData.tools.iron_pickaxe
	_give(Inventory.flat_cost(bronze))
	Inventory.craft(bronze)
	_give({topaz = 1})
	Inventory.inlay("bronze_pickaxe", "topaz")
	_ok(Inventory.sockets.get("bronze_pickaxe") == "topaz", "Topaz fits the Bronze pickaxe")
	_give({iron_ingot = 5, nettle_bundle = 1})
	_ok(Inventory.craft_blocker(iron) == "Missing materials", "without a hilt, a plain Craft is short")
	_ok(Inventory.rehaft_from(iron) == "bronze_pickaxe", "Re-haft offers the Bronze pickaxe's hilt")
	_ok(Inventory.craft(iron, true), "Re-haft assembles the Iron pickaxe")
	_ok(not Inventory.owns("bronze_pickaxe") and Inventory.held.pickaxe == "iron_pickaxe", "the Bronze one is gone, the Iron one in hand")
	_ok(not Inventory.sockets.has("bronze_pickaxe"), "its inlay went with it")
	_ok(Inventory.count("ash_hilt") == 0 and Inventory.count("iron_ingot") == 0, "the hilt moved straight across")
	_ok(Inventory.unfolded.has("take_apart"), "Re-haft unfolds Take apart (E1)")
	_ok(Inventory.rehaft_from(GameData.tools.obsidian_pickaxe) == "", "no Re-haft when the hilt doesn't carry over")
	var steel: Dictionary = GameData.tools.steel_pickaxe
	_give(Inventory.flat_cost(steel))
	Inventory.craft(steel)
	_ok(Inventory.take_apart_blocker("steel_pickaxe") != "", "the tool in its tool-bar slot can't be taken apart")
	_ok(Inventory.take_apart_blocker("stone_pickaxe") != "", "a starter tool can't be taken apart")
	Inventory.take_apart("iron_pickaxe")
	_ok(not Inventory.owns("iron_pickaxe") and not Inventory.items.has("iron_pickaxe"), "Take apart removes the tool")
	_ok(Inventory.count("ash_hilt") == 1, "and gives back its hilt")
	var rod: Dictionary = GameData.tools.ash_rod
	_give(Inventory.flat_cost(rod))
	Inventory.craft(rod)
	Inventory.hold("driftwood_rod")
	Inventory.take_apart("ash_rod")
	_ok(Inventory.count("tin_reel") == 1, "a rod gives back its reel")


# --- inlays and the cap (D-130, D-133, D-134) ---------------------------------------------

func _check_inlays() -> void:
	var T := GameData.tools
	_ok(Inventory.socket_fits(T.bronze_pickaxe, "topaz"), "tier 2 takes a tier 1 gem")
	_ok(not Inventory.socket_fits(T.iron_pickaxe, "topaz"), "tier 3 doesn't take a tier 1 gem")
	_ok(Inventory.socket_fits(T.iron_pickaxe, "sapphire"), "tier 3 takes a tier 2 gem")
	_ok(Inventory.socket_fits(T.ash_rod, "river_pearl"), "pearls fit (D-134)")
	_ok(not Inventory.socket_fits(T.bronze_axe, "ash_sap"), "sap doesn't fit")
	_ok(not Inventory.socket_fits(T.fox_bow, "lucky_foot"), "trophies don't fit")
	_ok(Inventory.socket_fits(T.eclipse_dragon_bow, "eclipsium") and Inventory.socket_fits(T.eclipse_dragon_bow, "star_pearl"), "tier 16 bows take the top gem and pearl")
	_ok(not Inventory.socket_fits(T.eclipse_dragon_bow, "arcanium"), "but nothing below")
	_ok(not Inventory.socket_fits(T.stone_pickaxe, "eclipsium"), "starter tools have no socket")
	_reset()
	_ok(is_equal_approx(Inventory.rare_boost("mining"), 1.0), "no boost with the Stone pickaxe")
	Inventory.owned.pickaxe.append("stellarite_pickaxe")
	Inventory.held.pickaxe = "stellarite_pickaxe"
	_ok(is_equal_approx(Inventory.rare_boost("mining"), 2.0), "Stellarite pickaxe x2 (D-059)")
	_give({eclipsium = 1})
	Inventory.inlay("stellarite_pickaxe", "eclipsium")
	_ok(is_equal_approx(Inventory.rare_boost("mining"), 2.5), "with an inlay: x2.5, at the cap (D-133)")
	_ok(is_equal_approx(Inventory.tool_boost(T.stellarite_pickaxe), GameData.RARE_BOOST_CAP), "the workbench shows it at cap")
	_ok(is_equal_approx(Inventory.rare_boost("foraging"), 1.0), "an inlay only helps its own tool's skill")
	_give({sapphire = 1, topaz = 1, river_pearl = 1})
	_ok(Inventory.inlay_choice(T.bronze_sickle) in ["topaz", "river_pearl"], "the cheapest fitting stone is offered")


# --- saving (B4) ----------------------------------------------------------------------------

func _check_save() -> void:
	_reset()
	Inventory.owned.axe.append("iron_axe")
	Inventory.sync_tools()
	Inventory.sockets = {iron_axe = "sapphire", gold_axe = "emerald"}   # gold_axe isn't owned: dropped
	Inventory.unfolded = {parts = true, socket = true}
	var data = JSON.parse_string(JSON.stringify(Save.state()))
	_reset()
	Save._apply_inventory(data.inventory)
	_ok(Inventory.sockets == {iron_axe = "sapphire"}, "inlays load back, only on owned tools: %s" % [Inventory.sockets])
	_ok(Inventory.unfolded.has("parts") and Inventory.unfolded.has("socket") and not Inventory.unfolded.has("take_apart"), "E1 flags load back")
	_ok(Inventory.icon_of("iron_axe") != null, "an inlaid tool has an icon with its pip")


# --- menus: each one draws, in each E1 state (script errors show in the log) -------------------

func _check_menus() -> void:
	_reset()
	var menu: Modal = load("res://ui/station_menu.gd").new()
	add_child(menu)
	for k in menu.kinds:
		menu.open(k)
		_ok(menu._list.get_child_count() > 0, "the %s menu draws" % k)
	_ok(_has_text(menu._list, "Show parts"), "a new player's workbench keeps parts folded (E1)")
	var bronze: Dictionary = GameData.tools.bronze_pickaxe
	_give(Inventory.flat_cost(bronze))
	Inventory.craft(bronze)
	_give({nettle_cord = 1, topaz = 1})
	menu.open("workbench")
	_ok(not _has_text(menu._list, "Show parts"), "a part in the bag unfolds the part rows")
	_ok(_has_text(menu._list, "Inlay Topaz"), "the socket appears once a gem fits (E1)")
	_ok(_has_text(menu._list, "Re-haft takes your Bronze pickaxe apart"), "Re-haft says what moves over")
	menu._craft(GameData.tools.iron_pickaxe, true)
	_ok(_has_text(menu._list, "Still needed:"), "Re-haft when short shows the shopping list (D-131)")
	Inventory.inlay("bronze_pickaxe", "topaz")
	menu._refresh()
	_ok(_has_text(menu._list, "rare drops ×1.25"), "the inlay shows on its row")
	_ok(_has_text(menu._list, "Take apart"), "Take apart shows once Re-haft has been offered")
	menu.queue_free()
	var shop: Modal = load("res://ui/merchant_menu.gd").new()
	add_child(shop)
	shop.open("merchant")
	_ok("nettle_cord" in shop._items_for("foraging"), "a held part is in the merchant's tab (D-132)")
	_ok(not "hare_leather_strip" in shop._items_for("hunting"), "parts the player doesn't hold aren't")
	shop.queue_free()


func _has_text(node: Node, text: String) -> bool:
	if (node is Label or node is Button) and text in node.text:
		return true
	for c in node.get_children():
		if _has_text(c, text):
			return true
	return false
