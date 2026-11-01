extends Modal
## The merchant (D-073 to D-077). It buys every gathered item: raw = base x tier, made = the raw
## items it took plus 25%, rare = 10 x the tier's raw item (D-074). It sells energy refills (one per
## reset, D-076), inventory rows (D-077) and stable slots (D-095). It no longer sells wood hilts,
## because lumbering is in (D-107). Cosmetics aren't designed yet. Every price is TEST: the base
## price waits on the size of the staked balances (02-resources).


func _init() -> void:
	kinds = ["merchant"]


func _render() -> void:
	_note("TEST prices: the real ones are set once staked balances are known. Coins: %d" % Inventory.coins)
	_heading("Buy")
	var r := UIKit.row(_list)
	r.add_child(UIKit.label("Energy refill to %d" % GameData.ENERGY_MAX))
	r.add_child(UIKit.label("one per reset" if Inventory.refill_period != Inventory.period() else "bought this reset", UIKit.MUTED, 13))
	r.add_child(UIKit.spacer())
	r.add_child(UIKit.label("%d coins" % GameData.REFILL_PRICE, UIKit.RARE))
	r.add_child(UIKit.button("Buy", Inventory.can_refill(), Inventory.buy_refill))
	r = UIKit.row(_list)
	r.add_child(UIKit.label("Inventory row (+%d slots)" % GameData.INVENTORY_COLUMNS))
	r.add_child(UIKit.label("%d of %d bought" % [Inventory.extra_rows, GameData.EXTRA_ROWS_MAX], UIKit.MUTED, 13))
	r.add_child(UIKit.spacer())
	var row_left := Inventory.extra_rows < GameData.EXTRA_ROWS_MAX
	r.add_child(UIKit.label("%d coins" % Inventory.row_price() if row_left else "-", UIKit.RARE))
	r.add_child(UIKit.button("Buy", row_left and Inventory.coins >= Inventory.row_price(), Inventory.buy_row))
	r = UIKit.row(_list)
	r.add_child(UIKit.label("Stable slot"))
	r.add_child(UIKit.label("%d of %d bought" % [Stable.extra_slots, GameData.EXTRA_SLOTS_MAX], UIKit.MUTED, 13))
	r.add_child(UIKit.spacer())
	var slot_left := Stable.extra_slots < GameData.EXTRA_SLOTS_MAX
	r.add_child(UIKit.label("%d coins" % Stable.slot_price() if slot_left else "-", UIKit.RARE))
	r.add_child(UIKit.button("Buy", slot_left and Inventory.coins >= Stable.slot_price(), Stable.buy_slot))

	_heading("Sell")
	if Inventory.items.is_empty():
		_note("Nothing to sell yet.")
	for id in Inventory.items.keys():
		var price := GameData.sell_price(id)
		if price <= 0:
			continue
		var n: int = Inventory.items[id]
		r = UIKit.row(_list)
		var tex := GameData.item_icon(id)
		if tex:
			r.add_child(UIKit.icon(tex, 32))
		r.add_child(UIKit.label("%s × %d" % [GameData.item_label(id), n]))
		r.add_child(UIKit.spacer())
		r.add_child(UIKit.label("%d each" % price, UIKit.RARE, 14))
		r.add_child(UIKit.button("Sell 1", true, Inventory.sell.bind(id, 1)))
		r.add_child(UIKit.button("All (%d)" % (price * n), true, Inventory.sell.bind(id, n)))
