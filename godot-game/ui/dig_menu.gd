extends Modal
## The daily treasure dig (D-096: the first minigame). Free (D-098). Proposed rules, built as a TEST:
## once per energy reset, a 5 x 5 grid of soil; pick 3 squares; each shows coins, a raw item of tier
## 1 to 3 that the player can already gather, or nothing. At most 1 item prize per reset (D-097,
## Proposed cap). Item prizes never roll mint tokens (D-097). No cosmetics exist yet.
## The grid lives in this menu, so it resets with the game, like the inventory.

const SIZE := 5
const PICKS := 3
const COIN_SQUARES := 9       # TEST
const ITEM_SQUARES := 2       # TEST
const COINS := Vector2i(5, 20)   # TEST

var _period := -1
var _prizes: Array = []       # per square: {} (nothing), {coins}, or {item}
var _dug: Array = []          # indexes picked this reset
var _item_given := false


func _init() -> void:
	kinds = ["dig_site"]


func _new_grid() -> void:
	_period = Inventory.period()
	_dug = []
	_item_given = false
	_prizes = []
	for i in SIZE * SIZE:
		_prizes.append({})
	var order := range(SIZE * SIZE)
	order.shuffle()
	for k in COIN_SQUARES:
		_prizes[order[k]] = {coins = randi_range(COINS.x, COINS.y)}
	var pool := _item_pool()
	for k in ITEM_SQUARES:
		if not pool.is_empty():
			_prizes[order[COIN_SQUARES + k]] = {item = pool.pick_random()}


## Raw items of tiers 1 to 3 the player can gather with the tools they own.
func _item_pool() -> Array:
	var out := []
	for skill in GameData.SKILLS:
		var reach: int = 0
		for id in Inventory.owned[GameData.SKILLS[skill].tool]:
			reach = maxi(reach, GameData.tools[id].reach)
		for row in GameData.tiers[skill]:
			if row.tier <= mini(reach, 3):
				out.append(row.raw)
	return out


func _dig(i: int) -> void:
	if i in _dug or _dug.size() >= PICKS:
		return
	_dug.append(i)
	var p: Dictionary = _prizes[i]
	if p.has("item") and _item_given:   # the item cap: later item squares pay coins instead
		p = {coins = COINS.x}
		_prizes[i] = p
	if p.has("coins"):
		Inventory.earn(p.coins)
	elif p.has("item") and Inventory.add(p.item):
		_item_given = true
		Inventory.looted.emit(p.item, 1, true)
	_refresh()


func _render() -> void:
	if _period != Inventory.period():
		_new_grid()
	var left := PICKS - _dug.size()
	_note("TEST rules (Proposed in 03): pick %d squares once per energy reset. %s" % [PICKS,
			("%d pick%s left." % [left, "s" if left != 1 else ""]) if left > 0 else "All dug: come back after the next reset (00:00 or 12:00 UTC)."])
	var grid := GridContainer.new()
	grid.columns = SIZE
	grid.add_theme_constant_override("h_separation", 6)
	grid.add_theme_constant_override("v_separation", 6)
	grid.size_flags_horizontal = Control.SIZE_SHRINK_CENTER
	_list.add_child(grid)
	for i in SIZE * SIZE:
		var dug: bool = i in _dug
		var b := UIKit.button("", not dug and left > 0, _dig.bind(i))
		b.custom_minimum_size = Vector2(72, 72)
		for state in ["normal", "hover", "pressed", "disabled"]:   # a patch of earth
			b.add_theme_stylebox_override(state, UIKit.button_box(state, Color("#5a4028"), 4.0))
		if dug:
			var p: Dictionary = _prizes[i]
			if p.has("coins"):
				b.text = "%d\ncoins" % p.coins
			elif p.has("item"):
				b.icon = GameData.item_icon(p.item)
				b.expand_icon = true
				b.texture_filter = CanvasItem.TEXTURE_FILTER_NEAREST
				b.tooltip_text = GameData.item_label(p.item)
			else:
				b.text = "nothing"
		grid.add_child(b)
