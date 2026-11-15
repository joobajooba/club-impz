extends Node
## Tamed animals. Loaded as the Stable autoload.
## Taming (D-071): feed an animal a dried bundle of its tier; the bundle is used up either way; no
## energy. The stable has 6 slots to start, more can be bought (D-095). One animal follows the
## player (D-071) and raises trophy chances for its tier and below (D-072). Any 3 make the battle
## team (D-088). Levels, XP, stats and fish as food are Proposed (05-skirmish) and built as a TEST.
## Like the inventory, the stable is kept on this device by the Save autoload until the server is connected (G6).

signal changed

var animals: Array = []      # {uid, id, level, xp}
var follower := -1           # uid of the animal that follows the player, or -1
var team: Array = []         # up to 3 uids
var extra_slots := 0
var wins_period := -1        # the reset period the paid-win count belongs to (D-092)
var paid_wins := 0
var _next_uid := 1


func slots() -> int:
	return GameData.STABLE_SLOTS + extra_slots


func get_animal(uid: int) -> Dictionary:
	for a in animals:
		if a.uid == uid:
			return a
	return {}


func row(animal: Dictionary) -> Dictionary:
	return GameData.tier_row("hunting", animal.id)


func label(animal: Dictionary) -> String:
	return "%s (Lv %d)" % [row(animal).label, animal.level]


## The follower's tier, or 0 with no follower: trophy chances rise for animals up to this tier.
func tracker_tier() -> int:
	var a := get_animal(follower)
	return row(a).tier if a else 0


# --- taming (D-071) ----------------------------------------------------------------

func tame_blocker(r: Dictionary) -> String:
	if Inventory.count(r.tame_with) < 1:
		return "Needs a " + GameData.item_label(r.tame_with) + " to tame"
	if animals.size() >= slots():
		return "Stable full"
	return ""


## Returns true if the animal was tamed. The bundle is used up either way.
func tame(r: Dictionary) -> bool:
	if tame_blocker(r) != "":
		return false
	Inventory.remove(r.tame_with, 1)
	if randf() >= r.tame_chance:
		Inventory.message.emit("The %s ate the %s and ran off. Not tamed." % [r.label, GameData.item_label(r.tame_with)])
		return false
	var a := {uid = _next_uid, id = r.id, level = 1, xp = 0}
	_next_uid += 1
	animals.append(a)
	if follower == -1:
		follower = a.uid
	if team.size() < 3:
		team.append(a.uid)
	Inventory.message.emit("Tamed a %s! It's in your stable." % r.label)
	changed.emit()
	return true


func set_follower(uid: int) -> void:
	follower = uid if follower != uid else -1
	changed.emit()


func toggle_team(uid: int) -> void:
	if uid in team:
		team.erase(uid)
	elif team.size() < 3:
		team.append(uid)
	changed.emit()


func slot_price() -> int:
	return GameData.ROW_PRICE << extra_slots


func buy_slot() -> void:
	if extra_slots < GameData.EXTRA_SLOTS_MAX and Inventory.spend(slot_price()):
		extra_slots += 1
		changed.emit()


# --- levels and stats (Proposed in 05, TEST numbers) ------------------------------

static func xp_to_next(level: int) -> int:
	return 50 * level


func add_xp(uid: int, xp: int) -> int:
	var a := get_animal(uid)
	if a.is_empty():
		return 0
	var levels := 0
	a.xp += xp
	while a.level < GameData.MAX_LEVEL and a.xp >= xp_to_next(a.level):
		a.xp -= xp_to_next(a.level)
		a.level += 1
		levels += 1
	changed.emit()
	return levels


## Cooked fish is battle-animal food (D-111); it gives XP (Proposed): 15 per fish tier.
func feed(uid: int, cooked_id: String) -> void:
	if Inventory.count(cooked_id) < 1 or get_animal(uid).is_empty():
		return
	Inventory.remove(cooked_id, 1)
	var gained := add_xp(uid, 15 * GameData.items[cooked_id].tier)
	if gained > 0:
		Inventory.message.emit("%s grew to level %d!" % [row(get_animal(uid)).label, get_animal(uid).level])


## Base stats grow with tier, a tier 16 animal about 3 times a tier 1 (Proposed). Each level adds 4%
## of the base. TEST numbers.
static func stats(tier: int, level: int) -> Dictionary:
	var m := 1.0 + (tier - 1) * 2.0 / 15.0
	var l := 1.0 + 0.04 * (level - 1)
	return {hp = roundi(30 * m * l), atk = roundi(10 * m * l), def = roundi(8 * m * l), spd = roundi(8 * m * l)}


## The moves known at this level, best 4 (Proposed: learned at 1, 10, 20, 35).
static func moves(type: String, level: int) -> Array:
	var out := []
	for i in GameData.MOVE_LEVELS.size():
		if level >= GameData.MOVE_LEVELS[i]:
			out.append(GameData.MOVES[type][i])
	return out.slice(-4)


# --- paid wins (D-092) --------------------------------------------------------------

func paid_wins_left() -> int:
	if wins_period != Inventory.period():
		return GameData.PAID_WINS
	return GameData.PAID_WINS - paid_wins


func count_paid_win() -> bool:
	if wins_period != Inventory.period():
		wins_period = Inventory.period()
		paid_wins = 0
	if paid_wins >= GameData.PAID_WINS:
		return false
	paid_wins += 1
	return true


# --- TEST: tame one of each of the first animals, for trying battles quickly ---------

func test_tame_starters() -> void:
	for id in ["hare", "fox", "boar"]:
		if animals.size() < slots():
			var a := {uid = _next_uid, id = id, level = 5, xp = 0}
			_next_uid += 1
			animals.append(a)
			if team.size() < 3:
				team.append(a.uid)
	if follower == -1 and animals.size() > 0:
		follower = animals[0].uid
	changed.emit()
