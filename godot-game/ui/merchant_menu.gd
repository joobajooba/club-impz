extends Modal
## The merchant's shop (J00BA, 2026-11-15; D-124). Opened with E at the merchant's stall in the hub
## (scripts/player/shop_keeper.gd) and at the camp's merchant.
##
## Tabs across the top, one per gathering skill: Ores (mining), Lumber (lumbering), Plants (foraging),
## Fish (fishing) and Hunting. Each shows that skill's items (raw, processed and rare, by tier) in a grid laid
## out like the inventory, with how many the player holds in each slot. Clicking an item fills the right side:
## its picture and name, what the merchant buys it for and sells it for, how many the player has, a quantity
## and Buy / Sell buttons.
##
## Prices: the merchant pays GameData.sell_price (D-074 rules, TEST base price) and sells for
## GameData.buy_price (BUY_MARKUP x that). It no longer sells energy refills, inventory rows or stable slots
## (D-124 replaces those parts of D-075, D-077 and D-095).

const TABS := [["Ores", "mining"], ["Lumber", "lumbering"], ["Plants", "foraging"], ["Fish", "fishing"], ["Hunting", "hunting"]]
const KIND_LABEL := {raw = "Raw", made = "Processed", rare = "Rare", hilt = "Hilt", part = "Tool part"}
const KIND_ORDER := {raw = 0, made = 1, rare = 2, hilt = 3, part = 4}
const SLOT_SIZE := 56
const COLUMNS := 6

var _tab := 0
var _selected := ""
var _qty := 1


func _init() -> void:
	kinds = ["merchant"]


func _ready() -> void:
	super._ready()
	_panel.custom_minimum_size = Vector2(900, 0)
	var scroll := _list.get_parent() as ScrollContainer           # Modal's list: a little taller, so it never scrolls
	if scroll:
		scroll.custom_minimum_size.y = 540


func open(station_kind: String) -> void:
	_qty = 1
	super.open(station_kind)


## The tab's items: the skill's items that the merchant trades, by tier, then raw, processed, rare. Hilts
## and tool parts show only while the player has some: the merchant buys them back (D-132) but doesn't sell them.
func _items_for(skill: String) -> Array:
	var out := []
	for id in GameData.items:
		var it: Dictionary = GameData.items[id]
		if it.kind in ["hilt", "part"] and Inventory.count(id) == 0:
			continue
		if it.skill == skill and GameData.sell_price(id) > 0:
			out.append(id)
	out.sort_custom(func(a, b):
		var ia: Dictionary = GameData.items[a]
		var ib: Dictionary = GameData.items[b]
		if ia.tier != ib.tier:
			return ia.tier < ib.tier
		return KIND_ORDER.get(ia.kind, 3) < KIND_ORDER.get(ib.kind, 3))
	return out


func _render() -> void:
	var items := _items_for(TABS[_tab][1])
	if _selected == "" or not items.has(_selected):
		_selected = items[0] if not items.is_empty() else ""

	# coins, then the category tabs
	var top := UIKit.row(_list)
	top.add_child(UIKit.label("Prices are TEST until the base price is set.", UIKit.MUTED, 13))
	top.add_child(UIKit.spacer())
	top.add_child(UIKit.pixel_icon(UIKit.COIN, UIKit.RARE))
	top.add_child(UIKit.label("%d coins" % Inventory.coins, UIKit.RARE, 17))
	var tabs := UIKit.row(_list)
	for i in TABS.size():
		var b := UIKit.button(TABS[i][0], true, _pick_tab.bind(i))
		b.custom_minimum_size = Vector2(110, 38)
		if i == _tab:
			for state in ["normal", "hover", "pressed"]:
				b.add_theme_stylebox_override(state, UIKit.slot(Color("#3a3526"), UIKit.GOLD, 2, 8.0))
			b.add_theme_color_override("font_color", UIKit.RARE)
			b.add_theme_color_override("font_hover_color", UIKit.RARE)
		tabs.add_child(b)

	var body := HBoxContainer.new()
	body.add_theme_constant_override("separation", 18)
	_list.add_child(body)
	body.add_child(_build_grid(items))
	body.add_child(_build_info())


# --- the grid, like the inventory -----------------------------------------------------------

func _build_grid(items: Array) -> Control:
	var scroll := ScrollContainer.new()
	scroll.horizontal_scroll_mode = ScrollContainer.SCROLL_MODE_DISABLED
	scroll.custom_minimum_size = Vector2(COLUMNS * (SLOT_SIZE + 6) + 14, 372)
	var grid := GridContainer.new()
	grid.columns = COLUMNS
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	scroll.add_child(grid)
	for id in items:
		grid.add_child(_slot(id))
	return scroll


func _slot(id: String) -> Button:
	var b := Button.new()
	b.custom_minimum_size = Vector2(SLOT_SIZE, SLOT_SIZE)
	b.focus_mode = Control.FOCUS_NONE
	b.tooltip_text = GameData.item_label(id)
	var picked := id == _selected
	var s := UIKit.slot(Color("#3a3526"), UIKit.GOLD, 2) if picked else UIKit.slot()
	for state in ["normal", "pressed", "disabled"]:
		b.add_theme_stylebox_override(state, s)
	b.add_theme_stylebox_override("hover", UIKit.slot(UIKit.SLOT.lightened(0.1), UIKit.GOLD, 2 if picked else 1))
	b.pressed.connect(_pick_item.bind(id))
	var tex := GameData.item_icon(id)
	if tex:
		var ic := UIKit.icon(tex, SLOT_SIZE - 12)
		ic.position = Vector2(6, 6)
		ic.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(ic)
	else:
		b.text = GameData.item_label(id).left(3)
	var have := Inventory.count(id)
	if have > 0:                                   # how many the player holds, like the inventory's counts
		var n := UIKit.label(str(have), Color.WHITE, 13)
		n.add_theme_color_override("font_outline_color", UIKit.OUTLINE)
		n.add_theme_constant_override("outline_size", 4)
		n.position = Vector2(4, SLOT_SIZE - 20)
		n.mouse_filter = Control.MOUSE_FILTER_IGNORE
		b.add_child(n)
	return b


# --- the item's info, prices and the buy / sell controls ---------------------------------------

func _build_info() -> Control:
	var box := PanelContainer.new()
	box.custom_minimum_size = Vector2(390, 372)
	box.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	box.add_theme_stylebox_override("panel", UIKit.slot(Color(0.14, 0.15, 0.19, 0.95), UIKit.OUTLINE, 1, 14.0))
	var v := VBoxContainer.new()
	v.add_theme_constant_override("separation", 8)
	box.add_child(v)
	if _selected == "":
		v.add_child(UIKit.label("Nothing to trade here yet.", UIKit.MUTED))
		return box
	var id := _selected
	var it: Dictionary = GameData.items[id]
	var head := UIKit.row(v)
	var tex := GameData.item_icon(id)
	if tex:
		head.add_child(UIKit.icon(tex, 72))
	var names := VBoxContainer.new()
	names.add_child(UIKit.title(GameData.item_label(id), 22))
	names.add_child(UIKit.label("%s  ·  %s  ·  tier %d" % [TABS[_tab][0], KIND_LABEL.get(it.kind, it.kind), it.tier], UIKit.MUTED, 13))
	head.add_child(names)
	v.add_child(UIKit.divider())

	var have := Inventory.count(id)
	var sell := GameData.sell_price(id)
	var buy := GameData.buy_price(id)
	_info_row(v, "You have", str(have), Color.WHITE)
	_info_row(v, "Merchant buys for", "%d coins each" % sell, UIKit.GOOD)
	_info_row(v, "Merchant sells for", ("%d coins each" % buy) if buy > 0 else "Doesn't sell these", UIKit.RARE)
	v.add_child(UIKit.divider())

	# quantity: -10 -1 [n] +1 +10, and Max (as many as you can sell, or else afford)
	var q := UIKit.row(v)
	q.add_child(UIKit.label("Quantity", UIKit.MUTED))
	q.add_child(UIKit.spacer())
	for d in [-10, -1]:
		q.add_child(_small_button(str(d), _change_qty.bind(d)))
	var n := UIKit.label(str(_qty), Color.WHITE, 20)
	n.custom_minimum_size = Vector2(52, 0)
	n.horizontal_alignment = HORIZONTAL_ALIGNMENT_CENTER
	q.add_child(n)
	for d in [1, 10]:
		q.add_child(_small_button("+%d" % d, _change_qty.bind(d)))
	q.add_child(_small_button("Max", _max_qty))

	var can_buy := buy > 0 and Inventory.coins >= buy * _qty and Inventory.has_room(id)
	var can_sell := have >= _qty
	var bb := UIKit.button("Buy %d for %d coins" % [_qty, buy * _qty], can_buy, _buy)
	bb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(bb)
	var sb := UIKit.button("Sell %d for %d coins" % [_qty, sell * _qty], can_sell, _sell)
	sb.size_flags_horizontal = Control.SIZE_EXPAND_FILL
	v.add_child(sb)
	var why := ""
	if not can_sell and not can_buy:
		why = "You have %d and can't afford %d." % [have, _qty]
	elif not Inventory.has_room(id):
		why = "No free inventory slot for a new item."
	elif not can_buy:
		why = "Not enough coins to buy %d." % _qty
	elif not can_sell:
		why = "You only have %d to sell." % have
	if why != "":
		v.add_child(UIKit.label(why, UIKit.SHORT, 13))
	return box


func _info_row(parent: Control, what: String, value: String, color: Color) -> void:
	var r := UIKit.row(parent)
	r.add_child(UIKit.label(what, UIKit.MUTED))
	r.add_child(UIKit.spacer())
	r.add_child(UIKit.label(value, color, 17))


func _small_button(text: String, on_press: Callable) -> Button:
	var b := UIKit.button(text, true, on_press)
	b.custom_minimum_size = Vector2(46, 34)
	return b


# --- actions ---------------------------------------------------------------------------------

func _pick_tab(i: int) -> void:
	_tab = i
	_selected = ""
	_qty = 1
	_refresh()


func _pick_item(id: String) -> void:
	_selected = id
	_qty = 1
	_refresh()


func _change_qty(d: int) -> void:
	_qty = clampi(_qty + d, 1, 999)
	_refresh()


## Max: everything you hold (to sell it all); if you hold none, as many as your coins buy.
func _max_qty() -> void:
	var have := Inventory.count(_selected)
	var price := GameData.buy_price(_selected)
	_qty = clampi(have if have > 0 else (Inventory.coins / price if price > 0 else 1), 1, 999)
	_refresh()


func _buy() -> void:
	Inventory.buy(_selected, _qty)      # Inventory.changed / coins_changed refresh the menu


func _sell() -> void:
	Inventory.sell(_selected, _qty)
