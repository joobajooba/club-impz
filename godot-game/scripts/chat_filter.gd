class_name ChatFilter
## The chat filter, the same rules as game-server/chat_filter.mjs (word lists in data/chat_filter.json). The game
## checks a message before sending it so the player is told straight away; the server checks again and has the final
## say (it also undoes accents and look-alike letters, which this copy does not).
##   clean(text) -> control / zero width characters removed, spaces collapsed, at most MAX characters
##   check(text) -> {ok = false} to refuse the message, or {ok = true, text = ...} with swearing starred out

const MAX := 200
const LEET := {"0": "o", "1": "i", "3": "e", "4": "a", "5": "s", "7": "t", "@": "a", "$": "s", "!": "i", "|": "i"}

static var _lists := {}
static var _allow := {}
static var _space: RegEx


static func _load() -> void:
	if not _lists.is_empty():
		return
	_lists = JSON.parse_string(FileAccess.get_file_as_string("res://data/chat_filter.json"))
	for w in _lists["allow"]:
		_allow[w] = true
	_space = RegEx.create_from_string("\\s+")


static func clean(text: String) -> String:
	_load()
	var out := ""
	for c in text:
		var u := c.unicode_at(0)
		if u < 32 and c != " " and c != "\t" and c != "\n":
			continue
		if (u >= 0x7f and u <= 0x9f) or (u >= 0x200b and u <= 0x200f) or (u >= 0x202a and u <= 0x202e) \
				or (u >= 0x2060 and u <= 0x2064) or u == 0xfeff:
			continue
		out += c
	out = _space.sub(out, " ", true).strip_edges()
	return out.substr(0, MAX).strip_edges()


static func check(text: String) -> Dictionary:
	_load()
	var lower := text.to_lower()
	for r in _lists["raw_blocked"]:
		if lower.contains(r):
			return {ok = false}
	var ws := _join_singles(_words(text))
	for w in ws:
		for t in _lists["blocked"]:
			if _hit(w, t, 5):
				return {ok = false}
	var all := ""
	for w in ws:
		if not _allow.has(w):
			all += w
	for t in _lists["blocked"]:
		if t.length() >= 6 and (all.contains(t) or _squash(all).contains(_squash(t))):
			return {ok = false}
	var line := " %s " % " ".join(ws)
	for ph in _lists["blocked_phrases"]:
		if line.contains(" %s " % " ".join(_words(ph))):
			return {ok = false}
	var parts := text.split(" ")
	for i in parts.size():
		var w := "".join(_words(parts[i]))
		if w == "":
			continue
		for m in _lists["masked"]:
			if _hit(w, m, 4):
				parts[i] = "*".repeat(parts[i].length())
				break
	return {ok = true, text = " ".join(parts)}


static func _words(s: String) -> PackedStringArray:
	var out := ""
	for c in s.to_lower():
		var l: String = LEET.get(c, c)
		out += l if l >= "a" and l <= "z" and l.length() == 1 else " "
	return out.split(" ", false)


static func _join_singles(ws: PackedStringArray) -> PackedStringArray:
	var out := PackedStringArray()
	var run := ""
	for w in ws:
		if w.length() == 1:
			run += w
			continue
		if run != "":
			out.append(run)
		run = ""
		out.append(w)
	if run != "":
		out.append(run)
	return out


static func _squash(w: String) -> String:
	var out := ""
	for c in w:
		if out == "" or out[out.length() - 1] != c:
			out += c
	return out


static func _hit(word: String, term: String, inside: int) -> bool:
	if _allow.has(word):
		return false
	if term.length() >= inside:
		return word.contains(term) or _squash(word).contains(_squash(term))
	return word == term or word == term + "s" or word == term + "es" \
		or (word.length() > term.length() and _squash(word) == _squash(term))
