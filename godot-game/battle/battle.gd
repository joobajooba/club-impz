class_name Battle
extends RefCounted
## One turn-based battle (05-skirmish), built as a TEST of the Proposed rules: a team of 3 tamed
## animals (D-088) against 3 wild ones, eight types and the type chart, four stats, moves by level.
## Each turn both sides pick an action; a swap goes first, then the faster animal moves (Speed).
## Later the server runs every battle (ACCOUNTS-AND-DATA section 8); for now it runs here.

var sides: Array = [[], []]   # [player's fighters, wild fighters]
var active := [0, 0]
var lines: Array[String] = []
var over := false
var won := false
var enemy_tier := 1


## A fighter from a hunting tier row and a level. uid is the stable animal's, or -1 for a wild one.
static func fighter(row: Dictionary, level: int, uid := -1) -> Dictionary:
	var s := Stable.stats(row.tier, level)
	return {name = row.label, type = row.type, tier = row.tier, level = level, uid = uid, raw = row.raw,
			hp = s.hp, max_hp = s.hp, atk = s.atk, def = s.def, spd = s.spd,
			moves = Stable.moves(row.type, level), atk_mod = 1.0, spd_mod = 1.0}


## Wild level for a tier (TEST): tier 1 is level 1, tier 16 level 46.
static func wild_level(tier: int) -> int:
	return tier * 3 - 2


func _init(team_uids: Array, tier: int) -> void:
	enemy_tier = tier
	for uid in team_uids:
		var a := Stable.get_animal(uid)
		sides[0].append(fighter(Stable.row(a), a.level, uid))
	# The chosen tier leads; two more from up to two tiers below.
	var tiers := [tier, maxi(1, tier - randi_range(0, 2)), maxi(1, tier - randi_range(0, 2))]
	for t in tiers:
		sides[1].append(fighter(GameData.row_by_tier("hunting", t), wild_level(t)))
	lines.append("A wild %s appears!" % sides[1][0].name)


func current(side: int) -> Dictionary:
	return sides[side][active[side]]


static func type_multiplier(attack: String, defend: String) -> float:
	var chart: Array = GameData.TYPE_CHART[attack]
	if defend in chart[0]:
		return 2.0
	if defend in chart[1]:
		return 0.5
	return 1.0


static func damage(att: Dictionary, def: Dictionary, move: Array, rand := 1.0) -> int:
	var power: float = move[1]
	if power <= 0.0:
		return 0
	var mult := type_multiplier(att.type, def.type)
	return maxi(1, roundi(power * att.atk * att.atk_mod / def.def * 0.25 * mult * rand))


## The wild side's choice: heal when low if it can, otherwise the move that hits hardest.
func _enemy_move() -> int:
	var me := current(1)
	var foe := current(0)
	var best := 0
	var best_value := -1.0
	for i in me.moves.size():
		var m: Array = me.moves[i]
		var value := float(damage(me, foe, m))
		if m[2] == "heal":
			value = me.max_hp * 0.3 if me.hp < me.max_hp * 0.4 else 0.0
		if value > best_value:
			best_value = value
			best = i
	return best


## The player's action: {kind = "move", index} or {kind = "swap", index}.
func play(choice: Dictionary) -> void:
	if over:
		return
	if choice.kind == "swap":
		if choice.index == active[0] or sides[0][choice.index].hp <= 0:
			return
		active[0] = choice.index
		lines.append("Go, %s!" % current(0).name)
		_use(1, _enemy_move())
	else:
		var enemy := _enemy_move()
		var mine := current(0)
		var theirs := current(1)
		var mine_at: int = active[0]
		var theirs_at: int = active[1]
		# A fainted animal's replacement doesn't get its move this turn.
		if mine.spd * mine.spd_mod >= theirs.spd * theirs.spd_mod:
			_use(0, choice.index)
			if not over and active[1] == theirs_at:
				_use(1, enemy)
		else:
			_use(1, enemy)
			if not over and active[0] == mine_at:
				_use(0, choice.index)
	_check_over()


func _use(side: int, index: int) -> void:
	var me := current(side)
	var foe := current(1 - side)
	if me.hp <= 0:
		return
	var m: Array = me.moves[index]
	var who: String = ("Your " if side == 0 else "Wild ") + me.name
	match m[2]:
		"heal":
			var healed := mini(roundi(me.max_hp * 0.3), me.max_hp - me.hp)
			me.hp += healed
			lines.append("%s used %s and healed %d." % [who, m[0], healed])
			return
	var dmg := damage(me, foe, m, randf_range(0.85, 1.0))
	foe.hp = maxi(0, foe.hp - dmg)
	var mult := type_multiplier(me.type, foe.type)
	var note := " It's super effective!" if mult > 1.0 else (" It's not very effective." if mult < 1.0 else "")
	lines.append("%s used %s for %d.%s" % [who, m[0], dmg, note])
	if m[2] == "slow":
		foe.spd_mod *= 0.8
	elif m[2] == "weaken":
		foe.atk_mod *= 0.8
	if foe.hp <= 0:
		lines.append("%s fainted!" % (("Your " if side == 1 else "Wild ") + foe.name))
		_next_alive(1 - side)


func _next_alive(side: int) -> void:
	for i in sides[side].size():
		if sides[side][i].hp > 0:
			active[side] = i
			if side == 1:
				lines.append("A wild %s joins in!" % current(1).name)
			else:
				lines.append("Go, %s!" % current(0).name)
			return
	_check_over()


func _check_over() -> void:
	for side in 2:
		if sides[side].all(func(f): return f.hp <= 0):
			over = true
			won = side == 1
			return


## XP for each animal on the team (TEST numbers): a win gives 15 x the leader's tier + 5 x its level;
## a loss gives half (D-094: losing costs only the reward).
func xp_reward() -> int:
	var lead: Dictionary = sides[1][0]
	var xp: int = 15 * lead.tier + 5 * lead.level
	return xp if won else xp / 2


## Coins for a win (D-093; amount Proposed): what 5 raw items of the opponent's tier sell for.
func coin_reward() -> int:
	return 5 * GameData.BASE_PRICE * enemy_tier if won else 0
