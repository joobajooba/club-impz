class_name Fishing
extends RefCounted
## Fishing in the resource world (resource_gathering.md section 7, Proposed; D-109, D-112, D-135). The spots
## are scripts/world/fish_spot.gd; scripts/player/fisher.gd on the player does the fishing.
##
## Like a vein, a spot never runs out (section 9): every landed fish starts the bar again. The bar fills over
## the fish's time to catch (section 7.2, the mining ladder), then the fish bites and a short window opens.
## Like mining in the live world, fishing spends no energy yet (energy only limits mint token rolls, D-123,
## which aren't built).

const SPEED_PER_TIER := 0.05     # each rod tier above the fish's tier catches 5% faster (sections 2.3, 7.1)
const REACH := 4.5               # metres from where the Imp stands to the middle of a spot
const BITE_WINDOW := 1.5         # D-135's W: seconds to react to a tier 1 bite with no reel (Proposed)
const WINDOW_PER_TIER := 0.04    # D-135: the window narrows 4% a fish tier
const REELS := {"": 1.0, "tin_reel": 1.1, "copper_reel": 1.25, "bronze_reel": 1.4}   # D-135
const MISS_KEEP := 0.5           # a missed bite drops the bar to half (section 7)
const JITTER := 0.15             # each fish comes a little sooner or later, by up to 15% (same average)
## Section 7.2: seconds to catch each fish with its minimum rod.
const TIMES := {"minnow": 30.0, "perch": 45.0, "trout": 45.0, "catfish": 60.0, "goldfin_carp": 120.0,
		"shadow_eel": 240.0, "frostscale_pike": 300.0, "bloodfin_snapper": 300.0, "void_angler": 600.0,
		"starfin_koi": 1000.0}

static var progress := {}         # spot node name -> 0..1 of the bar toward the next bite


static func _article(label: String) -> String:
	return ("an " if "AEIOU".contains(label.left(1)) else "a ") + label


## Why this rod can't fish the spot's fish ("Needs an Oak Rod", "Inventory full"), or "".
static func blocker(row: Dictionary, rod_id: String) -> String:
	if int(GameData.tools[rod_id].reach) < int(row.tier):
		return "Needs " + _article(GameData.tool_for_tier("rod", row.tier).label)
	if not Inventory.has_room(row.raw):
		return "Inventory full"
	return ""


## Seconds to catch with this rod: the doc's time, 5% less per rod tier above the fish's.
static func catch_time(row: Dictionary, rod_id: String) -> float:
	var above := maxi(0, int(GameData.tools[rod_id].tier) - int(row.tier))
	return float(TIMES.get(row.id, 30.0)) * maxf(0.2, 1.0 - SPEED_PER_TIER * above)


## Seconds to press after the bite (D-135): W, 4% narrower a fish tier, wider with the rod's reel.
static func bite_window(row: Dictionary, rod_id: String) -> float:
	var reel: String = GameData.tools[rod_id].get("returns", "")
	return BITE_WINDOW * (1.0 - WINDOW_PER_TIER * (int(row.tier) - 1)) * float(REELS.get(reel, 1.0))


## One fish into the inventory, and the pearl roll (D-112: the fish is still received). The chance takes the
## same capped boosts as every rare drop (Inventory.rare_boost: an inlaid gem or pearl on the rod, D-133/D-134).
static func give(row: Dictionary) -> void:
	Inventory.gain(row.raw)
	if randf() < float(row.rare_chance) * Inventory.rare_boost("fishing", row.tier) and Inventory.has_room(row.rare):
		Inventory.gain(row.rare, 1, true)
