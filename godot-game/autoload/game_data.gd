extends Node
## The game's tables, as data (docs/GODOT.md section 6). Loaded as the GameData autoload.
## Five gathering skills share one shape: each tier has a raw item you gather, a made item a station
## turns it into, and a rare drop. Every number is decided in docs/DECISIONS.md (D-numbers next to
## each table) unless it says Proposed or TEST. Battle data and prices are Proposed or TEST only:
## the user asked for playable versions before deciding them (2026-10-22).

const ENERGY_MAX := 100
const GATHER_ENERGY := 5          # every gathering action, shared pool (D-008, D-061)
const RESET_SECONDS := 12 * 3600  # energy refills at 00:00 and 12:00 UTC (D-057)
const RESPAWN := 10.0             # veins, plants, animals, trees and fishing spots (D-007, D-064, D-067, D-105, D-109)
const INVENTORY_COLUMNS := 6      # a 6 x 8 grid (D-008), plus bought rows of 6 (D-077)
const INVENTORY_ROWS := 8
const STABLE_SLOTS := 6           # D-095

# --- gathering skills ----------------------------------------------------------

## verb: the prompt ("Mine Tin"). tool: the tool kind. station: where raw becomes made.
const SKILLS := {
	"mining": {label = "Mining", verb = "Mine", tool = "pickaxe", station = "furnace"},
	"foraging": {label = "Foraging", verb = "Pick", tool = "sickle", station = "drying_rack"},
	"hunting": {label = "Hunting", verb = "Hunt", tool = "bow", station = "tanning_rack"},
	"lumbering": {label = "Lumbering", verb = "Chop", tool = "axe", station = "sawbench"},
	"fishing": {label = "Fishing", verb = "Fish", tool = "rod", station = "campfire"},
}

## Mining (D-005, D-012, D-020, D-054, D-055): [id, label, file, gem, ore per ingot, coal per ingot].
## Coal (smelt 0) has no ingot. Titanite and Dreadstone pictures still use the old file names.
const _ORES := [
	["tin", "Tin", "tin", "topaz", 2, 0], ["copper", "Copper", "copper", "sapphire", 2, 0],
	["iron", "Iron", "iron", "amethyst", 3, 0], ["coal", "Coal", "coal", "ruby", 0, 0],
	["gold", "Gold", "gold", "emerald", 3, 1], ["obsidian", "Obsidian", "obsidian", "jade", 4, 1],
	["titanite", "Titanite", "mithril", "diamond", 4, 1], ["dreadstone", "Dreadstone", "adamantite", "painite", 5, 2],
	["void", "Void Stone", "void", "arcanium", 5, 2], ["stellarite", "Stellarite", "stellarite", "eclipsium", 5, 2],
]
const GEMS := {
	topaz = "Topaz", sapphire = "Sapphire", amethyst = "Amethyst", ruby = "Ruby", emerald = "Emerald",
	jade = "Jade", diamond = "Diamond", painite = "Painite", arcanium = "Arcanium", eclipsium = "Eclipsium",
}
## Vein colours from each ore picture: TEST art until each tier has its own vein.
const ORE_LOOKS := {
	"tin": {ore = "#9eaab6", metal = 0.8, rough = 0.3, top = "#8f939e", side = "#676768"},
	"iron": {ore = "#aab0ba", metal = 0.9, rough = 0.3, top = "#6a625a", side = "#4e5158"},
	"coal": {ore = "#1c1c21", metal = 0.1, rough = 0.55, top = "#4c4742", side = "#3a3836"},
	"gold": {ore = "#ffb21f", metal = 0.95, rough = 0.25, top = "#a8873f", side = "#8a7a62"},
	"obsidian": {ore = "#251b33", metal = 0.3, rough = 0.06, top = "#3e3449", side = "#2c2830"},
	"titanite": {ore = "#d9caff", metal = 0.8, rough = 0.2, top = "#8f87a8", side = "#9c97ad", glow = "#2c2058"},
	"dreadstone": {ore = "#8c2629", metal = 0.75, rough = 0.3, top = "#6b3b31", side = "#5a3a36"},
	"void": {ore = "#4d2a91", metal = 0.3, rough = 0.3, top = "#2b2337", side = "#2a2234", glow = "#3a167a"},
	"stellarite": {ore = "#4a8bea", metal = 0.5, rough = 0.2, top = "#2b3b5c", side = "#27324a", glow = "#1b4bb0"},
}

## Foraging (D-022 to D-026, D-062): [id, label, plants per bundle, model, stem colour, flower colour].
## The model is a kit plant recoloured from the plant picture: TEST art.
const _PLANTS := [
	["nettle", "Nettle", 2, "Fern_1", "#3c8a34", "#6cb454"],
	["marigold", "Marigold", 2, "Flower_4_Group", "#4f8a2c", "#fc9c3c"],
	["bluebell", "Bluebell", 3, "Flower_3_Group", "#3f7d3a", "#4c7cf0"],
	["thornroot", "Thornroot", 3, "Plant_7", "#845424", "#d9c49a"],
	["sunpetal", "Sunpetal", 4, "Flower_4_Group", "#5d7d22", "#fccc3c"],
	["nightshade", "Nightshade", 4, "Plant_1", "#3c843c", "#6a2c8a"],
	["frostbloom", "Frostbloom", 5, "Flower_3_Group", "#6a87a8", "#d6ecff"],
	["bloodcap", "Bloodcap", 5, "Mushroom_Common", "#ccb49c", "#e43c3c"],
	["voidlily", "Voidlily", 5, "Flower_4_Single", "#2c2440", "#7a3cd8"],
	["starmoss", "Starmoss", 5, "Clover_2", "#24549c", "#ffd84a"],
]

## Hunting (D-032, D-033, D-068, D-071): [id, label, hides per leather, trophy id, trophy label,
## body colour, mark colour, shape]. The shape picks a simple box creature: TEST art until the
## Blockbench creatures exist (MODELS-BLOCKBENCH).
const _ANIMALS := [
	["hare", "Hare", 2, "lucky_foot", "Lucky Foot", "#b4846c", "#e8d8c8", "hopper"],
	["fox", "Fox", 2, "brush_tail", "Brush Tail", "#e4843c", "#f4f0e8", "quad"],
	["boar", "Boar", 2, "boar_tusk", "Boar Tusk", "#6c543c", "#3c240c", "quad"],
	["wolf", "Wolf", 3, "wolf_fang", "Wolf Fang", "#6c6c84", "#c8c8d8", "quad"],
	["goldhorn_stag", "Goldhorn Stag", 3, "golden_antler", "Golden Antler", "#b4843c", "#ffd04a", "horned"],
	["shadowcat", "Shadowcat", 3, "shadow_claw", "Shadow Claw", "#3c2454", "#9a6cff", "quad"],
	["frostmane_yeti", "Frostmane Yeti", 4, "frozen_heart", "Frozen Heart", "#cce4fc", "#8484cc", "biped"],
	["cinder_salamander", "Cinder Salamander", 4, "ember_scale", "Ember Scale", "#b42424", "#ff9a3c", "lizard"],
	["voidstalker", "Voidstalker", 4, "void_eye", "Void Eye", "#2a1838", "#8a4cff", "quad"],
	["starwyrm", "Starwyrm", 4, "star_horn", "Star Horn", "#24549c", "#ffd84a", "lizard"],
	["stormhorn_ram", "Stormhorn Ram", 5, "thunder_curl", "Thunder Curl", "#6c8484", "#e8e070", "horned"],
	["tidecrest_serpent", "Tidecrest Serpent", 5, "abyss_pearl", "Abyss Pearl", "#249c9c", "#e8f4f0", "serpent"],
	["mossmane_behemoth", "Mossmane Behemoth", 5, "verdant_mane", "Verdant Mane", "#24843c", "#7a5a34", "biped"],
	["crystalback_basilisk", "Crystalback Basilisk", 5, "prism_shard", "Prism Shard", "#840c6c", "#ff9ae4", "lizard"],
	["sunfeather_griffin", "Sunfeather Griffin", 5, "sun_feather", "Sun Feather", "#cc9c54", "#fce4b4", "winged"],
	["eclipse_dragon", "Eclipse Dragon", 5, "eclipse_crown", "Eclipse Crown", "#24243c", "#fce4b4", "winged"],
]

## Lumbering (D-105, D-107, D-108): [id, label, logs per plank, rare label, model, bark, leaves].
## The model is a kit tree recoloured from the log picture; leaves of tiers 5 to 10 use that mining
## tier's colour (02-resources). TEST art.
const _TREES := [
	["ash", "Ash", 2, "Ash Sap", "CommonTree_1", "#8a8478", "#5e9a3a"],
	["birch", "Birch", 2, "Birch Sap", "CommonTree_2", "#e4e4e4", "#8cc04a"],
	["oak", "Oak", 3, "Oak Resin", "CommonTree_3", "#84543c", "#3f7d2a"],
	["pine", "Pine", 3, "Pine Resin", "Pine_1", "#543c24", "#2c5a34"],
	["goldleaf", "Goldleaf", 4, "Golden Amber", "CommonTree_4", "#9c6c24", "#ffc23a"],
	["ebony", "Ebony", 4, "Ebony Amber", "TwistedTree_1", "#2a2030", "#4a2f66"],
	["silverbark", "Silverbark", 5, "Silver Amber", "CommonTree_5", "#d8d0f0", "#c8b8f8"],
	["bloodwood", "Bloodwood", 5, "Blood Amber", "TwistedTree_2", "#5a1414", "#c83030"],
	["voidwood", "Voidwood", 5, "Void Amber", "TwistedTree_3", "#24183c", "#6a32c0"],
	["starwood", "Starwood", 5, "Star Amber", "Pine_3", "#1c2c54", "#4a8bea"],
]

## Fishing (D-109, D-111, D-112): [id, label, fish per cooked, logs burnt per cooked (Proposed),
## pearl id, pearl label, colour].
const _FISH := [
	["minnow", "Minnow", 2, 0, "river", "River Pearl", "#b4b4cc"],
	["perch", "Perch", 2, 0, "sand", "Sand Pearl", "#b4b454"],
	["trout", "Trout", 3, 0, "moss", "Moss Pearl", "#b4b484"],
	["catfish", "Catfish", 3, 1, "black", "Black Pearl", "#6c6c54"],
	["goldfin_carp", "Goldfin Carp", 4, 1, "golden", "Golden Pearl", "#e4cc54"],
	["shadow_eel", "Shadow Eel", 4, 1, "shadow", "Shadow Pearl", "#6c3c9c"],
	["frostscale_pike", "Frostscale Pike", 5, 1, "frost", "Frost Pearl", "#cce4fc"],
	["bloodfin_snapper", "Bloodfin Snapper", 5, 2, "blood", "Blood Pearl", "#cc3c3c"],
	["void_angler", "Void Angler", 5, 2, "void", "Void Pearl", "#3c246c"],
	["starfin_koi", "Starfin Koi", 5, 2, "star", "Star Pearl", "#24549c"],
]
const ANY_LOG := "any_log"   # campfire fuel: any kind of log, lowest tier first (Proposed in 02)

# --- tools ---------------------------------------------------------------------

## The metal tools: pickaxes (D-006, D-060), sickles (D-063: same cost as that pickaxe) and axes
## (D-106: half the pickaxe's ingots, rounded up (Proposed), plus its hilt).
## [id, label, skin file, pickaxe ingots, hilt]. Stone has no recipe: every player starts with it.
const _METALS := [
	["stone", "Stone", "stone", {}, ""],
	["bronze", "Bronze", "bronze", {tin_ingot = 5, copper_ingot = 5}, "ash_hilt"],
	["iron", "Iron", "iron", {iron_ingot = 5}, "ash_hilt"],
	["steel", "Steel", "steel", {iron_ingot = 10}, "ash_hilt"],
	["gold", "Gold", "gold", {gold_ingot = 10}, "ash_hilt"],
	["obsidian", "Obsidian", "obsidian", {obsidian_ingot = 10}, "oak_hilt"],
	["titanite", "Titanite", "mithril", {titanite_ingot = 10}, "oak_hilt"],
	["dreadstone", "Dreadstone", "adamantite", {dreadstone_ingot = 10}, "oak_hilt"],
	["void", "Void", "void", {void_ingot = 10}, "void_hilt"],
	["stellarite", "Stellarite", "stellarite", {stellarite_ingot = 10}, "cosmic_hilt"],
]
## Highest ore tier each pickaxe mines: its named ore (D-006) and every ore below (D-011).
const _PICKAXE_REACH := [2, 3, 4, 5, 6, 7, 8, 9, 10, 10]
const GEM_BOOST_TOOL := "stellarite_pickaxe"   # doubles gem chances while held (D-059)

## Where each tool kind is crafted. Bows at the tanning rack and rods at the sawbench are Proposed:
## the docs say what they cost (D-069, D-110) but not where.
const TOOL_KINDS := {
	"pickaxe": {label = "Pickaxe", skill = "mining", station = "blacksmith"},
	"sickle": {label = "Sickle", skill = "foraging", station = "blacksmith"},
	"axe": {label = "Axe", skill = "lumbering", station = "blacksmith"},
	"bow": {label = "Bow", skill = "hunting", station = "tanning_rack"},
	"rod": {label = "Rod", skill = "fishing", station = "sawbench"},
}

## Hilts (D-058, D-107), made at the blacksmith.
const HILTS := {
	"ash_hilt": {label = "Ash Wood Hilt", cost = {ash_plank = 5}},
	"oak_hilt": {label = "Oak Wood Hilt", cost = {oak_plank = 5}},
	"void_hilt": {label = "Void Hilt", cost = {void_ingot = 2, arcanium = 1}},
	"cosmic_hilt": {label = "Cosmic Hilt", cost = {stellarite_ingot = 2, eclipsium = 1}},
}

# --- stations and the camp -----------------------------------------------------

const STATIONS := {
	"furnace": {label = "Furnace", verb = "Use furnace", skill = "mining"},
	"drying_rack": {label = "Drying Rack", verb = "Use drying rack", skill = "foraging"},
	"tanning_rack": {label = "Tanning Rack", verb = "Use tanning rack", skill = "hunting"},
	"sawbench": {label = "Sawbench", verb = "Use sawbench", skill = "lumbering"},
	"campfire": {label = "Campfire", verb = "Cook at campfire", skill = "fishing"},
	"blacksmith": {label = "Blacksmith", verb = "Use anvil", skill = ""},
	"merchant": {label = "Merchant", verb = "Trade with merchant", skill = ""},
	"stable": {label = "Stable", verb = "Open stable", skill = ""},
	"arena": {label = "Battle Board", verb = "Find a battle", skill = ""},
	"dig_site": {label = "Treasure Dig", verb = "Dig for treasure", skill = ""},
}

# --- battles (05-skirmish: Proposed, built as a TEST) -----------------------------

const TYPES := ["Beast", "Fire", "Water", "Nature", "Frost", "Storm", "Shadow", "Light"]
## Each animal's type, by hunting tier 1 to 16 (Proposed in 05).
const ANIMAL_TYPES := ["Beast", "Fire", "Nature", "Beast", "Light", "Shadow", "Frost", "Fire",
		"Shadow", "Light", "Storm", "Water", "Nature", "Frost", "Storm", "Shadow"]
## Attacking type -> [strong against (x2), resisted by (x0.5)] (Proposed in 05).
const TYPE_CHART := {
	"Beast": [[], []], "Fire": [["Nature", "Frost"], ["Water"]], "Water": [["Fire"], ["Nature", "Storm"]],
	"Nature": [["Water"], ["Fire"]], "Frost": [["Storm"], ["Fire"]], "Storm": [["Water"], ["Frost"]],
	"Shadow": [["Light"], ["Shadow"]], "Light": [["Shadow"], ["Light"]],
}
## Four moves per type, learned at levels 1, 10, 20 and 35 (Proposed in 05; the moves are TEST).
## [name, power, effect]: effect "" / "heal" (30% of max health) / "slow" / "weaken" (lower the
## target's Speed or Attack by 20% for the battle).
const MOVE_LEVELS := [1, 10, 20, 35]
const MOVES := {
	"Beast": [["Tackle", 40, ""], ["Bite", 55, ""], ["Pounce", 70, ""], ["Rampage", 90, ""]],
	"Fire": [["Ember", 40, ""], ["Flame Dash", 55, ""], ["Scorch", 50, "weaken"], ["Inferno", 90, ""]],
	"Water": [["Splash", 40, ""], ["Bubble Jet", 55, ""], ["Tide Slam", 70, ""], ["Torrent", 90, ""]],
	"Nature": [["Vine Lash", 40, ""], ["Leaf Storm", 55, ""], ["Regrow", 0, "heal"], ["Thornquake", 90, ""]],
	"Frost": [["Chill", 40, ""], ["Ice Fang", 55, ""], ["Frost Bite", 50, "slow"], ["Blizzard", 90, ""]],
	"Storm": [["Spark", 40, ""], ["Gust", 55, ""], ["Thunderclap", 70, ""], ["Tempest", 90, ""]],
	"Shadow": [["Shade", 40, ""], ["Night Claw", 55, ""], ["Dread", 40, "weaken"], ["Eclipse Beam", 90, ""]],
	"Light": [["Glimmer", 40, ""], ["Radiant Horn", 55, ""], ["Mend", 0, "heal"], ["Sunburst", 90, ""]],
}
const MAX_LEVEL := 50
const PAID_WINS := 10            # PvE wins per energy reset that pay coins (D-092)

# --- prices (D-074 rules, TEST numbers: the base price is not decided) ----------

const BASE_PRICE := 2            # TEST: coins for a tier 1 raw item
const REFILL_PRICE := 600        # TEST: must stay above what 100 energy earns by selling (D-076)
const ROW_PRICE := 100           # TEST: first extra inventory row or stable slot; each costs twice the last (D-077, D-095)
const EXTRA_ROWS_MAX := 4        # TEST cap
const EXTRA_SLOTS_MAX := 4       # TEST cap

# --- built at start-up ------------------------------------------------------------

## skill id -> Array of tier rows: {skill, id, label, tier, raw, made, rare, rare_chance, per,
## fuel, fuel_count, ...look fields}.
var tiers := {}
## item id -> {label, icon (path or ""), tier, skill, kind ("raw" / "made" / "rare" / "hilt")}.
var items := {}
## tool id -> {id, kind, label, tier, reach, cost, hilt, colour fields}; tools_of[kind] is in tier order.
var tools := {}
var tools_of := {}


func _init() -> void:
	_build_mining()
	_build_foraging()
	_build_hunting()
	_build_lumbering()
	_build_fishing()
	for id in HILTS:
		items[id] = {label = HILTS[id].label, icon = "res://sprites/items/hilt_%s.png" % id, tier = 0, skill = "", kind = "hilt"}
	_build_tools()


## The gem/seed/sap/pearl ladder (D-012, D-025, D-108, D-112): 10% falling 1% per tier.
static func _ladder(tier: int) -> float:
	return 0.11 - tier * 0.01


func _add_tier(skill: String, row: Dictionary) -> void:
	row.skill = skill
	if not tiers.has(skill):
		tiers[skill] = []
	tiers[skill].append(row)


func _item(id: String, label: String, icon: String, tier: int, skill: String, kind: String) -> void:
	items[id] = {label = label, icon = "res://sprites/items/%s.png" % icon, tier = tier, skill = skill, kind = kind}


func _build_mining() -> void:
	for i in _ORES.size():
		var o: Array = _ORES[i]
		var row := {id = o[0], label = o[1], tier = i + 1, raw = o[0] + "_ore", made = o[0] + "_ingot" if o[4] > 0 else "",
				rare = o[3], rare_chance = _ladder(i + 1), per = o[4], fuel = "coal_ore", fuel_count = o[5],
				look = ORE_LOOKS.get(o[0], {})}
		_add_tier("mining", row)
		_item(row.raw, o[1] + " ore", "nugget_" + o[2], i + 1, "mining", "raw")
		if row.made:
			_item(row.made, o[1] + " ingot", "ingot_" + o[2], i + 1, "mining", "made")
		_item(row.rare, GEMS[o[3]], "gemstone_" + o[3], i + 1, "mining", "rare")


func _build_foraging() -> void:
	for i in _PLANTS.size():
		var p: Array = _PLANTS[i]
		var row := {id = p[0], label = p[1], tier = i + 1, raw = p[0], made = p[0] + "_bundle", rare = p[0] + "_seed",
				rare_chance = _ladder(i + 1), per = p[2], fuel = "", fuel_count = 0, model = p[3], stem = p[4], flower = p[5]}
		_add_tier("foraging", row)
		_item(row.raw, p[1], "plant_" + p[0], i + 1, "foraging", "raw")
		_item(row.made, p[1] + " bundle", "bundle_" + p[0], i + 1, "foraging", "made")
		_item(row.rare, p[1] + " seed", "seed_" + p[0], i + 1, "foraging", "rare")


func _build_hunting() -> void:
	for i in _ANIMALS.size():
		var a: Array = _ANIMALS[i]
		var t := i + 1
		var row := {id = a[0], label = a[1], tier = t, raw = a[0] + "_hide", made = a[0] + "_leather", rare = a[3],
				rare_chance = 0.10 - 0.006 * i,                         # D-033
				per = a[2], fuel = "", fuel_count = 0, body = a[5], mark = a[6], shape = a[7],
				tame_with = (_PLANTS[i][0] if t <= 10 else "starmoss") + "_bundle",   # D-071
				tame_chance = 0.50 - 0.03 * i, type = ANIMAL_TYPES[i]}
		_add_tier("hunting", row)
		_item(row.raw, a[1] + " hide", "hide_" + a[0], t, "hunting", "raw")
		_item(row.made, a[1] + " leather", "leather_" + a[0], t, "hunting", "made")
		_item(row.rare, a[4], "trophy_" + a[3], t, "hunting", "rare")


func _build_lumbering() -> void:
	for i in _TREES.size():
		var w: Array = _TREES[i]
		var row := {id = w[0], label = w[1], tier = i + 1, raw = w[0] + "_log", made = w[0] + "_plank", rare = w[0] + "_sap",
				rare_chance = _ladder(i + 1), per = w[2], fuel = "", fuel_count = 0, model = w[4], bark = w[5], leaves = w[6]}
		_add_tier("lumbering", row)
		_item(row.raw, w[1] + " log", "log_" + w[0], i + 1, "lumbering", "raw")
		_item(row.made, w[1] + " plank", "plank_" + w[0], i + 1, "lumbering", "made")
		_item(row.rare, w[3], "sap_" + w[0], i + 1, "lumbering", "rare")


func _build_fishing() -> void:
	for i in _FISH.size():
		var f: Array = _FISH[i]
		var row := {id = f[0], label = f[1], tier = i + 1, raw = f[0], made = "cooked_" + f[0], rare = f[4] + "_pearl",
				rare_chance = _ladder(i + 1), per = f[2], fuel = ANY_LOG, fuel_count = f[3], colour = f[6]}
		_add_tier("fishing", row)
		_item(row.raw, f[1], "fish_" + f[0], i + 1, "fishing", "raw")
		_item(row.made, "Cooked " + f[1], "cooked_" + f[0], i + 1, "fishing", "made")
		_item(row.rare, f[5], "pearl_" + f[4], i + 1, "fishing", "rare")


func _build_tools() -> void:
	for kind in TOOL_KINDS:
		tools_of[kind] = []
	var skins: Dictionary = (load("res://models/mining/pickaxe-skins.json") as JSON).data
	for i in _METALS.size():
		var m: Array = _METALS[i]
		var head: Dictionary = skins.get(m[2], {}).get("parts", {}).get("Head", {})
		var handle: Dictionary = skins.get(m[2], {}).get("parts", {}).get("Handle", {})
		var colours := {head = head.get("color", "#888888"), metal = head.get("metalness", 0.0),
				rough = head.get("roughness", 0.8), handle = handle.get("color", "#76644a"), skin = m[2]}
		var half := {}
		for ingot in m[3]:
			half[ingot] = ceili(m[3][ingot] / 2.0)
		_add_tool("pickaxe", m[0], m[1] + " pickaxe", i + 1, _PICKAXE_REACH[i], m[3], m[4], colours)
		_add_tool("sickle", m[0], m[1] + " sickle", i + 1, i + 1, m[3], m[4], colours)
		_add_tool("axe", m[0], m[1] + " axe", i + 1, i + 1, half, m[4], colours)
	for i in _ANIMALS.size():   # D-069: bow N = 10 leather of tier N-1; names Proposed
		var cost := {} if i == 0 else {_ANIMALS[i - 1][0] + "_leather": 10}
		_add_tool("bow", _ANIMALS[i][0], _ANIMALS[i][1] + " Bow", i + 1, i + 1, cost, "",
				{head = _ANIMALS[i][5], handle = "#6b4a2c", metal = 0.0, rough = 0.8})
	for i in _FISH.size():      # D-110: rod N = 10 planks of tree tier N-1; names Proposed
		var wood: String = "driftwood" if i == 0 else _TREES[i - 1][0]
		var label: String = "Driftwood" if i == 0 else _TREES[i - 1][1]
		var cost := {} if i == 0 else {wood + "_plank": 10}
		_add_tool("rod", wood, label + " Rod", i + 1, i + 1, cost, "",
				{head = "#8a7a62" if i == 0 else _TREES[i - 1][5], handle = "#d8d0c0", metal = 0.0, rough = 0.8})


func _add_tool(kind: String, metal: String, label: String, tier: int, reach: int, cost: Dictionary, hilt: String, colours: Dictionary) -> void:
	var id := metal + "_" + kind
	var t := {id = id, kind = kind, label = label, tier = tier, reach = reach, cost = cost, hilt = hilt}
	t.merge(colours)
	tools[id] = t
	tools_of[kind].append(t)


# --- lookups ----------------------------------------------------------------------

func item_label(id: String) -> String:
	return items[id].label if items.has(id) else (tools[id].label if tools.has(id) else id)


func item_icon(id: String) -> Texture2D:
	if tools.has(id):
		return tool_icon(id)
	var path: String = items[id].icon if items.has(id) else ""
	return load(path) if path != "" and ResourceLoader.exists(path) else null


func tier_row(skill: String, id: String) -> Dictionary:
	for row in tiers[skill]:
		if row.id == id:
			return row
	return {}


func row_by_tier(skill: String, tier: int) -> Dictionary:
	return tiers[skill][tier - 1] if tier >= 1 and tier <= tiers[skill].size() else {}


## The weakest tool of this kind that reaches this tier (D-011, D-024, D-034 and the same rule for
## axes and rods).
func tool_for_tier(kind: String, tier: int) -> Dictionary:
	for t in tools_of[kind]:
		if t.reach >= tier:
			return t
	return {}


## Pickaxes use their drawn sprites. The other tools have no pictures yet, so a small pixel icon
## is drawn in code from the tool's colours: TEST art.
var _icon_cache := {}

func tool_icon(id: String) -> Texture2D:
	var t: Dictionary = tools[id]
	if t.kind == "pickaxe":
		return load("res://sprites/pickaxes/%s_pickaxe.png" % t.skin)
	var path := "res://sprites/items/tool_%s.png" % id   # drawn by sprites/build_tool_icons.py
	if ResourceLoader.exists(path):
		return load(path)
	if not _icon_cache.has(id):
		_icon_cache[id] = ToolArt.icon(t)
	return _icon_cache[id]


# --- prices (TEST) ------------------------------------------------------------------

## What the merchant pays for one of an item (D-074 rules, BASE_PRICE is TEST): raw = base x tier;
## made = the raw items it took (and its fuel) plus 25%; rare = 10 x that tier's raw item.
func sell_price(id: String) -> int:
	if not items.has(id) or items[id].kind == "hilt":
		return 0
	var it: Dictionary = items[id]
	var raw_price: int = BASE_PRICE * it.tier
	match it.kind:
		"raw":
			return raw_price
		"rare":
			return raw_price * 10
		_:
			for row in tiers[it.skill]:
				if row.made == id:
					var fuel_price := 0
					if row.fuel_count > 0:
						fuel_price = row.fuel_count * BASE_PRICE * (4 if row.fuel == "coal_ore" else 1)
					return roundi((row.per * raw_price + fuel_price) * 1.25)
	return raw_price
