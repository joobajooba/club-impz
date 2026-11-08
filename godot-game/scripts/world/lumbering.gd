class_name Lumbering
extends RefCounted
## Chopping the world's trees with the axe (resource_gathering.md section 5, tool rules in section 2).
## The trees are the scatter's MultiMesh trees (scripts/world/scatter.gd); tree_chopper.gd on the player
## does the chopping. A felled tree leaves its stump and grows back after `regrow` seconds.
##
## Felled trees and chop progress are kept here (not in the world scene), so a tree you felled is still
## a stump if you go to the hub and come back within the 5 minutes. Client side only for now: other
## players still see the tree standing.

static var regrow := 300.0        # seconds a stump stays before its tree grows back (J00BA, 2026-11-08; --regrow=)
const SPEED_PER_TIER := 0.05      # each axe tier above the minimum chops 5% faster (section 2.3)
const REACH := 1.5                # metres from the Imp to the bark to start chopping

## Lumbering table, resource_gathering.md section 5. time = seconds to chop with the minimum axe.
## axe = the minimum axe's metal (game_data.gd _METALS ids; the doc's Voidstone axe is `void_axe`).
const TREES := {
	"pine": {label = "Pine", tier = 1, time = 30.0, axe = "stone", log = "pine_log", xp = 22},
	"birch": {label = "Birch", tier = 2, time = 45.0, axe = "stone", log = "birch_log", xp = 38},
	"oak": {label = "Oak", tier = 3, time = 45.0, axe = "stone", log = "oak_log", xp = 48},
	"maple": {label = "Maple", tier = 4, time = 60.0, axe = "bronze", log = "maple_log", xp = 75},
	"hickory": {label = "Hickory", tier = 5, time = 120.0, axe = "iron", log = "hickory_log", xp = 165},
	"frostbark": {label = "Frostbark", tier = 6, time = 240.0, axe = "gold", log = "frostbark_log", xp = 355},
	"titanwood": {label = "Titanwood", tier = 7, time = 300.0, axe = "obsidian", log = "titanwood_log", xp = 480},
	"runewood": {label = "Runewood", tier = 8, time = 300.0, axe = "titanite", log = "runewood_log", xp = 540},
	"gembark": {label = "Gembark", tier = 9, time = 600.0, axe = "dreadstone", log = "gembark_log", xp = 1190},
	"worldbark": {label = "Worldbark", tier = 10, time = 1000.0, axe = "void", log = "worldbark_log", xp = 2160},
}

## Which tree each scatter rule (data/scatter.json) is. "" = by the mesh alias (the forest's pine, oak and
## birch). Rules not listed (the hub's trees) can't be chopped.
const RULE_TREE := {
	"forest_tree": "",
	"frost_green_pine": "pine",
	"maple_tree": "maple",
	"hickory_tree_placeholder": "hickory",
	"frostbark_tree_placeholder": "frostbark",
	"titanwood_tree_placeholder": "titanwood",
	"runewood_tree_placeholder": "runewood",
	"gembark_tree_placeholder": "gembark",
	"worldbark_tree_placeholder": "worldbark",
}

## Per tree mesh: its stump model and its trunk's half width (Blockbench units, trunk_1 of the model).
const MESHES := {
	"pine": {stump = "pine", trunk = 5.0},
	"birch": {stump = "birch", trunk = 2.5},
	"oak": {stump = "oak", trunk = 7.0},
	"maple": {stump = "maple", trunk = 5.5},
	"maple_2": {stump = "maple", trunk = 6.0},
	"maple_3": {stump = "maple", trunk = 6.0},
}
## Trees with a stump of their own, whatever mesh stands in for the tree (frostbark is a recoloured pine).
const OWN_STUMP := {"frostbark": "frostbark"}
const STUMP_PATH := "res://assets/models/trees/%s_stump.glb"
const UNITS := 1.0 / 16.0         # Blockbench units to metres

static var felled := {}           # tree key -> Time.get_ticks_msec() when it grows back
static var progress := {}         # tree key -> seconds chopped so far (kept if the player stops)


static func tree_for(rule_id: String, alias: String) -> String:
	if not RULE_TREE.has(rule_id):
		return ""
	var t: String = RULE_TREE[rule_id]
	if t == "":
		t = alias.get_slice("_", 0)
	return t if TREES.has(t) else ""


static func is_felled(key: String) -> bool:
	if not felled.has(key):
		return false
	if Time.get_ticks_msec() >= int(felled[key]):
		felled.erase(key)
		return false
	return true


static func fell(key: String) -> void:
	felled[key] = Time.get_ticks_msec() + int(regrow * 1000.0)
	progress.erase(key)


## The axe the player holds, as an index into the axe tiers (0 = stone).
static func axe_index(axe_id: String) -> int:
	var list: Array = GameData.tools_of.get("axe", [])
	for i in list.size():
		if list[i].id == axe_id:
			return i
	return -1


static func min_axe_index(tree: String) -> int:
	return axe_index(TREES[tree].axe + "_axe")


## Why this axe can't chop the tree ("Needs a Bronze axe"), or "".
static func blocker(tree: String, axe_id: String) -> String:
	if axe_index(axe_id) >= min_axe_index(tree):
		return ""
	var need: Dictionary = GameData.tools_of["axe"][min_axe_index(tree)]
	return "Needs a " + need.label


## Seconds to chop this tree with this axe: the doc's time, 5% less per axe tier above the minimum.
static func chop_time(tree: String, axe_id: String) -> float:
	var above := maxi(0, axe_index(axe_id) - min_axe_index(tree))
	return float(TREES[tree].time) * maxf(0.2, 1.0 - SPEED_PER_TIER * above)
