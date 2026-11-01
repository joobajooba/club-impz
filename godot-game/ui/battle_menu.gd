extends Modal
## The battle board: wild battles against animals of every tier the player can hunt (05-skirmish,
## Proposed, built as a TEST). Needs a team of 3 from the stable (D-088). No energy (D-092). A win
## pays XP and, for the first 10 wins per energy reset, coins (D-092, D-093); a loss pays XP only
## (D-094). Animals have no portraits yet, so each shows its hide picture.

var _battle: Battle
var _rewarded := false


func _init() -> void:
	kinds = ["arena"]


func open(station_kind: String) -> void:
	_battle = null
	super(station_kind)


func close() -> void:
	if _battle and not _battle.over:
		return   # finish or forfeit first
	super()


func _render() -> void:
	if _battle:
		_render_battle()
	else:
		_render_board()


func _render_board() -> void:
	_note("TEST battles (rules Proposed in 05-skirmish). Your team of 3 against wild animals. No energy. The first %d wins each reset pay coins: %d left." % [GameData.PAID_WINS, Stable.paid_wins_left()])
	var team := Stable.team.filter(func(uid): return not Stable.get_animal(uid).is_empty())
	var names := team.map(func(uid): return Stable.label(Stable.get_animal(uid)))
	_note("Your team: " + (", ".join(names) if names else "nobody yet") + ". Set it in the stable.")
	var ready := team.size() == 3
	if not ready:
		_note("You need 3 animals in your team. Tame them with T while hunting.")
	var reach := 0
	for id in Inventory.owned.bow:
		reach = maxi(reach, GameData.tools[id].reach)
	for row in GameData.tiers.hunting:
		if row.tier > reach:
			break
		var r := UIKit.row(_list)
		r.add_child(UIKit.icon(GameData.item_icon(row.raw), 32))
		r.add_child(UIKit.label("Wild %s and friends" % row.label))
		r.add_child(UIKit.label("Lv %d  ·  %s" % [Battle.wild_level(row.tier), row.type], UIKit.MUTED, 13))
		r.add_child(UIKit.spacer())
		r.add_child(UIKit.label("+%d coins" % (5 * GameData.BASE_PRICE * row.tier), UIKit.RARE, 13))
		r.add_child(UIKit.button("Fight", ready, _start.bind(team, row.tier)))
	_note("Stronger wild animals appear as you craft better bows.")


func _start(team: Array, tier: int) -> void:
	_battle = Battle.new(team, tier)
	_rewarded = false
	_refresh()


func _act(choice: Dictionary) -> void:
	_battle.play(choice)
	if _battle.over and not _rewarded:
		_rewarded = true
		var xp := _battle.xp_reward()
		for f in _battle.sides[0]:
			Stable.add_xp(f.uid, xp)
		var line := "You win! Each animal gets %d XP." % xp if _battle.won else "You lost. Each animal still gets %d XP." % xp
		if _battle.won:
			if Stable.count_paid_win():
				Inventory.earn(_battle.coin_reward())
				line += " +%d coins." % _battle.coin_reward()
			else:
				line += " No coins: this reset's %d paid wins are used." % GameData.PAID_WINS
		_battle.lines.append(line)
	_refresh()


func _forfeit() -> void:
	_battle.over = true
	_battle.won = false
	_battle.lines.append("You ran from the battle.")
	_rewarded = true
	_refresh()


func _fighter_box(f: Dictionary, mine: bool) -> Control:
	var box := HBoxContainer.new()
	box.add_theme_constant_override("separation", 10)
	box.add_child(UIKit.icon(GameData.item_icon(f.raw), 48))
	var col := VBoxContainer.new()
	col.add_child(UIKit.label("%s%s  Lv %d  ·  %s" % ["" if mine else "Wild ", f.name, f.level, f.type]))
	var bar := ProgressBar.new()
	bar.custom_minimum_size = Vector2(220, 14)
	bar.max_value = f.max_hp
	bar.value = f.hp
	bar.show_percentage = false
	bar.add_theme_stylebox_override("background", UIKit.style(UIKit.SLOT, UIKit.BORDER * Color(1, 1, 1, 0.4), 4, 0))
	bar.add_theme_stylebox_override("fill", UIKit.style(UIKit.GOOD, UIKit.GOOD, 4, 0))
	col.add_child(bar)
	col.add_child(UIKit.label("%d / %d HP" % [f.hp, f.max_hp], UIKit.MUTED, 12))
	box.add_child(col)
	return box


func _render_battle() -> void:
	var b := _battle
	var top := UIKit.row(_list)
	top.add_child(UIKit.spacer())
	top.add_child(_fighter_box(b.current(1), false))
	var bottom := UIKit.row(_list)
	bottom.add_child(_fighter_box(b.current(0), true))
	for line in b.lines.slice(-6):
		_note(line)
	if b.over:
		_list.add_child(UIKit.button("Back to the board", true, func():
			_battle = null
			_refresh()))
		return
	_heading("Moves")
	var moves := UIKit.row(_list)
	var me := b.current(0)
	for i in me.moves.size():
		var m: Array = me.moves[i]
		var desc: String = ("heal" if m[2] == "heal" else "power %d" % m[1]) + (", " + m[2] if m[2] in ["slow", "weaken"] else "")
		var btn := UIKit.button("%s\n(%s)" % [m[0], desc], true, _act.bind({kind = "move", index = i}))
		btn.custom_minimum_size = Vector2(140, 52)
		moves.add_child(btn)
	_heading("Swap")
	var swaps := UIKit.row(_list)
	for i in b.sides[0].size():
		var f: Dictionary = b.sides[0][i]
		swaps.add_child(UIKit.button("%s (%d HP)" % [f.name, f.hp], i != b.active[0] and f.hp > 0, _act.bind({kind = "swap", index = i})))
	swaps.add_child(UIKit.spacer())
	swaps.add_child(UIKit.button("Run", true, _forfeit))
