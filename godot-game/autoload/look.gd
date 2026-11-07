extends Node
## What the player's Imp wears, as the Look autoload (game_menus.md section 3.5).
##
## `worn` is the look the player picked: {body, head, eyes, clothing, back} of trait ids from
## res://data/impz/manifest.json, "" = none. Save keeps it in user://save.json.
## `shown()` is what the Imp actually wears: `worn` with every trait the player can't use right now
## swapped for the base imp's (Green body, no traits), so selling an Imp locks its traits again.
##
## Who can use what (game_direction.md section 2): every player has the base imp. An Imp holder can use
## each trait of every Imp in the linked wallet. Ownership comes from impz.club (/api/imps?wallet=), the
## same server check the website's Imp Customization page uses (it reads the Imp contract on chain).
## TEST: debug builds can unlock every trait (`test_all`) to try the customizer without a wallet.

signal changed                    # the shown look changed (worn look, ownership or the test switch)
signal wallet_changed             # ownership finished loading, failed, or the wallet went away

const API := "https://www.impz.club/api/imps?wallet="
const BASE := ImpBuilder.DEFAULT

var worn := BASE.duplicate()
## TEST, debug builds only: every trait unlocked. Never on in a release build.
var test_all := OS.is_debug_build():
	set(v):
		test_all = v and OS.is_debug_build()
		changed.emit()

var wallet := ""                  # the address ownership was read for ("" = no wallet linked)
var state := "none"               # none | loading | ready | error
var error := ""
var imps: Array = []              # token ids the wallet holds
var traits := {}                  # {slot: {trait_id: [token ids that have it]}}
var saved: Array = []             # builds saved on impz.club: {id, name, body, head, eyes, clothing, back}

var _http: HTTPRequest


func _ready() -> void:
	_http = HTTPRequest.new()
	_http.timeout = 30.0
	add_child(_http)
	_http.request_completed.connect(_on_response)
	var bridge = ProfileUI.get("wallet")
	if bridge:
		bridge.connected.connect(func(address: String, _chain: int): load_wallet(address))
		bridge.account_changed.connect(load_wallet)


## Can the player use this trait? "" (none) is always allowed except for the body.
func owns(slot: String, id: String) -> bool:
	if id == "":
		return slot != "body"
	if id == BASE.body or test_all:
		return true
	return traits.get(slot, {}).has(id)


## Which of the wallet's Impz give this trait (for the menu's "from Imp #12").
func sources(slot: String, id: String) -> Array:
	return traits.get(slot, {}).get(id, [])


func shown() -> Dictionary:
	var out := {}
	for slot in ImpBuilder.SLOTS:
		var id: String = worn.get(slot, BASE[slot])
		out[slot] = id if owns(slot, id) and (id == "" or not ImpBuilder.entry(slot, id).is_empty()) else BASE[slot]
	return out


func wear(look: Dictionary) -> void:
	var next := {}
	for slot in ImpBuilder.SLOTS:
		var v = look.get(slot, BASE[slot])          # saved builds from impz.club use null for none
		next[slot] = BASE[slot] if v == null or str(v) == "" else str(v)
	if next == worn:
		return
	worn = next
	changed.emit()


## Read the wallet's Impz and traits from impz.club. "" forgets the wallet.
func load_wallet(address: String) -> void:
	address = address.to_lower()
	if address == wallet and state in ["loading", "ready"]:
		return
	_http.cancel_request()
	wallet = address
	imps = []
	traits = {}
	saved = []
	error = ""
	if address == "":
		state = "none"
		_done()
		return
	state = "loading"
	wallet_changed.emit()
	var err := _http.request(API + address, ["Accept: application/json"])
	if err != OK:
		_fail("Could not reach impz.club (error %d)." % err)


## Re-check the wallet the Profile panel has linked right now (the menu calls this when it opens).
func sync_wallet() -> void:
	var address := str(ProfileUI.get("address")) if ProfileUI.get("address") != null else ""
	if address.to_lower() != wallet:
		load_wallet(address)


func _on_response(result: int, code: int, _headers: PackedStringArray, body: PackedByteArray) -> void:
	if result != HTTPRequest.RESULT_SUCCESS:
		_fail("Could not reach impz.club to check your Impz.")
		return
	var data = JSON.parse_string(body.get_string_from_utf8())
	if code != 200 or not data is Dictionary:
		_fail(str(data.get("error", "impz.club answered %d." % code)) if data is Dictionary else "impz.club answered %d." % code)
		return
	imps = data.get("imps", [])
	traits = data.get("traits", {})
	saved = data.get("saved", [])
	state = "ready"
	_done()


func _fail(message: String) -> void:
	state = "error"
	error = message
	_done()


func _done() -> void:
	wallet_changed.emit()
	changed.emit()
