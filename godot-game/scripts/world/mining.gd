class_name Mining
extends RefCounted
## Mining the ore veins with the pickaxe (resource_gathering.md section 4, tool rules in section 2).
## The veins are scripts/world/ore_vein.gd; scripts/player/ore_miner.gd on the player does the mining.
##
## A vein never runs out (section 9): every time the bar fills, the player gets one ore (and may find the
## ore's gem, section 4.2), and the bar starts again while they keep mining. Any number of players can
## mine one vein at once. Voidstone and stellarite veins are world events (autoload/ore_events.gd): on those,
## every swing has a chance to give the ore instead of a bar, so nobody holds the vein.

const SPEED_PER_TIER := 0.05      # each pickaxe tier above the minimum mines 5% faster (section 2.3)
const REACH := 2.0                # metres from the side of the mound to start mining

## Section 4.1 (ore, time to mine with the minimum pickaxe, minimum pickaxe metal) and 4.2 (gem, 1 in N).
## Item ids are the game's (game_data.gd): coal is `coal_ore`, voidstone `void_ore` (the doc's `coal`, `voidstone_ore`).
const ORES := {
	"coal": {label = "Coal", time = 30.0, pick = "stone", item = "coal_ore", gem = "diamond", gem_in = 50},
	"tin": {label = "Tin", time = 45.0, pick = "stone", item = "tin_ore", gem = "topaz", gem_in = 10},
	"copper": {label = "Copper", time = 45.0, pick = "stone", item = "copper_ore", gem = "sapphire", gem_in = 12},
	"iron": {label = "Iron", time = 60.0, pick = "bronze", item = "iron_ore", gem = "amethyst", gem_in = 15},
	"gold": {label = "Gold", time = 120.0, pick = "iron", item = "gold_ore", gem = "ruby", gem_in = 20},
	"obsidian": {label = "Obsidian", time = 240.0, pick = "gold", item = "obsidian_ore", gem = "emerald", gem_in = 25},
	"titanite": {label = "Titanite", time = 300.0, pick = "obsidian", item = "titanite_ore", gem = "jade", gem_in = 30},
	"dreadstone": {label = "Dreadstone", time = 300.0, pick = "titanite", item = "dreadstone_ore", gem = "painite", gem_in = 50},
	"void": {label = "Voidstone", time = 600.0, pick = "dreadstone", item = "void_ore", gem = "arcanium", gem_in = 60},
	"stellarite": {label = "Stellarite", time = 1000.0, pick = "void", item = "stellarite_ore", gem = "eclipsium", gem_in = 75},
}

static var progress := {}         # vein node name -> seconds mined toward the next ore


static func pick_index(pick_id: String) -> int:
	var list: Array = GameData.tools_of.get("pickaxe", [])
	for i in list.size():
		if list[i].id == pick_id:
			return i
	return -1


static func min_index(ore: String) -> int:
	return pick_index(ORES[ore].pick + "_pickaxe")


## Why this pickaxe can't mine the ore ("Needs a Bronze pickaxe", "Inventory full"), or "".
static func blocker(ore: String, pick_id: String) -> String:
	if pick_index(pick_id) < min_index(ore):
		return "Needs a " + GameData.tools_of["pickaxe"][min_index(ore)].label
	if not Inventory.has_room(ORES[ore].item):
		return "Inventory full"
	return ""


## Seconds per ore with this pickaxe: the doc's time, 5% less per pickaxe tier above the minimum.
static func mine_time(ore: String, pick_id: String) -> float:
	var above := maxi(0, pick_index(pick_id) - min_index(ore))
	return float(ORES[ore].time) * maxf(0.2, 1.0 - SPEED_PER_TIER * above)


## One ore into the inventory, and the gem roll (section 4.2: the ore is still received).
static func give(ore: String) -> void:
	var o: Dictionary = ORES[ore]
	Inventory.gain(o.item)
	if randi() % int(o.gem_in) == 0 and Inventory.has_room(o.gem):
		Inventory.gain(o.gem, 1, true)
