extends Node3D
## Items dropped from the inventory (right click a slot, ui/inventory_ui.gd): the item's picture on the ground in
## front of the Imp, bobbing and turning. Walk over it to pick it back up (after a moment, so it isn't picked up
## the instant it is dropped). It disappears after LIFETIME seconds. Only the player who dropped it sees it.

const LIFETIME := 180.0
const GRACE := 1.2                # seconds before it can be picked up again
const REACH := 1.1
const PICKUP_SOUND := "res://assets/sounds/item_pickup.wav"

var id := ""
var count := 1
var _age := 0.0
var _sprite: Sprite3D
var _base_y := 0.0


func _ready() -> void:
	_sprite = Sprite3D.new()
	_sprite.texture = GameData.item_icon(id)
	_sprite.pixel_size = 0.4 / maxf(1.0, float(_sprite.texture.get_width())) if _sprite.texture else 0.01
	_sprite.texture_filter = BaseMaterial3D.TEXTURE_FILTER_NEAREST
	_sprite.double_sided = true
	_sprite.shaded = false
	_sprite.alpha_cut = SpriteBase3D.ALPHA_CUT_DISCARD
	add_child(_sprite)
	if count > 1:
		var tag := Label3D.new()
		tag.text = "x%d" % count
		tag.billboard = BaseMaterial3D.BILLBOARD_ENABLED
		tag.font_size = 36
		tag.outline_size = 10
		tag.pixel_size = 0.004
		tag.position = Vector3(0.22, -0.12, 0)
		add_child(tag)
	_base_y = global_position.y


func _process(delta: float) -> void:
	_age += delta
	if _age > LIFETIME:
		queue_free()
		return
	_sprite.position.y = 0.25 + sin(_age * 2.5) * 0.06
	_sprite.rotation.y += delta * 1.6
	if _age < GRACE:
		return
	var main := get_tree().get_first_node_in_group("game_main")
	var player: Node3D = main.get("player") if main else null
	if player and player.global_position.distance_to(global_position) < REACH:
		if Inventory.gain(id, count):
			var snd := AudioStreamPlayer.new()
			snd.stream = load(PICKUP_SOUND)
			snd.volume_db = -6.0
			get_tree().current_scene.add_child(snd)
			snd.finished.connect(snd.queue_free)
			snd.play()
			queue_free()
		else:
			_age = 0.0                               # inventory full: try again in a moment
