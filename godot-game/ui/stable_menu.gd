extends Modal
## The stable (D-095): the tamed animals, which one follows the player (D-071, D-072), the battle
## team of 3 (D-088), and feeding cooked fish for XP (D-111; XP as its effect is Proposed).
## Animals have no portraits yet, so each shows its hide picture.


func _init() -> void:
	kinds = ["stable"]


func _render() -> void:
	_note("%d of %d slots used. Tame animals with T while hunting: feed them a dried bundle of their tier. More slots at the merchant." % [Stable.animals.size(), Stable.slots()])
	if Stable.animals.is_empty():
		_note("No animals yet.")
		return
	var fish := _best_fish()
	for a in Stable.animals:
		var row := Stable.row(a)
		var s := Stable.stats(row.tier, a.level)
		var r := UIKit.row(_list)
		r.add_child(UIKit.icon(GameData.item_icon(row.raw), 40))
		var info := VBoxContainer.new()
		info.add_theme_constant_override("separation", 0)
		info.add_child(UIKit.label("%s  ·  %s" % [Stable.label(a), row.type]))
		info.add_child(UIKit.label("XP %d/%d   HP %d  Atk %d  Def %d  Spd %d" % [a.xp, Stable.xp_to_next(a.level), s.hp, s.atk, s.def, s.spd], UIKit.MUTED, 12))
		r.add_child(info)
		r.add_child(UIKit.spacer())
		var following: bool = Stable.follower == a.uid
		r.add_child(UIKit.button("Following" if following else "Follow", true, Stable.set_follower.bind(a.uid)))
		var in_team: bool = a.uid in Stable.team
		r.add_child(UIKit.button("In team" if in_team else "Add to team", in_team or Stable.team.size() < 3, Stable.toggle_team.bind(a.uid)))
		var feed := UIKit.button("Feed", fish != "" and a.level < GameData.MAX_LEVEL, Stable.feed.bind(a.uid, fish))
		feed.tooltip_text = ("Feed a " + GameData.item_label(fish)) if fish else "Cook fish at the campfire first"
		r.add_child(feed)


## The highest-tier cooked fish the player has, or "".
func _best_fish() -> String:
	var rows: Array = GameData.tiers.fishing.duplicate()
	rows.reverse()
	for row in rows:
		if Inventory.count(row.made) > 0:
			return row.made
	return ""
