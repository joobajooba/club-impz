extends Node
## Talks to browser wallets (MetaMask, Rabby, ...) through JavaScriptBridge.
## Only works in a Web export: wallet extensions live in the browser, not in the Godot editor.
## The connection lasts until the page is reloaded. It also signs the impz.club sign-in message.
##
## Wallets are found with EIP-6963 (each installed wallet announces itself by name),
## falling back to the single window.ethereum provider for older wallets.
## Glyph (game_direction.md: the game's wallet, on ApeChain) is listed first when the page loads
## web-wallet's glyph-wallet.js (window.impzGlyph, added by the web export's head_include). It is not
## an extension: connecting opens Glyph's login window.

signal wallets_listed(wallets: Array)            # [{id, name}]
signal connected(address: String, chain_id: int)
signal connect_failed(message: String)
signal account_changed(address: String)          # "" when the wallet disconnects
signal chain_changed(chain_id: int)
signal signed(result: Dictionary)                # {ok, signature} or {ok = false, error}

const CHAIN_NAMES := {
	1: "Ethereum",
	4663: "Robinhood Chain",
	33139: "ApeChain",
}

const JS := """
(function () {
	if (window.impzWallet) return;
	const found = new Map();
	window.addEventListener('eip6963:announceProvider', (e) => found.set(e.detail.info.uuid, e.detail));
	const ask = () => window.dispatchEvent(new Event('eip6963:requestProvider'));
	ask();
	let onEvent = null;
	const hooked = new WeakSet();
	const provider = (id) => (id === 'glyph' ? window.impzGlyph && window.impzGlyph.provider()
		: id === 'injected' ? window.ethereum : found.get(id) && found.get(id).provider);
	const send = (cb, data) => cb(JSON.stringify(data));
	window.impzWallet = {
		list() {
			ask();
			const out = [...found.values()].map((d) => ({ id: d.info.uuid, name: d.info.name }));
			const injected = out.length;
			if (window.impzGlyph) out.unshift({ id: 'glyph', name: 'Glyph' });
			if (!injected && window.ethereum) {
				const e = window.ethereum;
				out.push({ id: 'injected', name: e.isRabby ? 'Rabby' : e.isMetaMask ? 'MetaMask' : 'Browser wallet' });
			}
			return JSON.stringify(out);
		},
		setEvents(cb) { onEvent = cb; },
		async connectWallet(id, cb) {
			const p = provider(id);
			if (!p) return send(cb, { ok: false, error: 'That wallet is no longer available.' });
			try {
				const accounts = await p.request({ method: 'eth_requestAccounts' });
				const chainId = await p.request({ method: 'eth_chainId' });
				if (p.on && !hooked.has(p)) {
					hooked.add(p);
					p.on('accountsChanged', (a) => onEvent && send(onEvent, { type: 'accounts', address: a[0] || '' }));
					p.on('chainChanged', (c) => onEvent && send(onEvent, { type: 'chain', chainId: c }));
				}
				send(cb, { ok: true, address: accounts[0] || '', chainId });
			} catch (err) {
				const rejected = err && err.code === 4001;
				send(cb, { ok: false, error: rejected ? 'You cancelled the request in your wallet.' : String((err && err.message) || err) });
			}
		},
		// personal_sign, used to sign in to the impz.club account (ui/profile/account_panel.gd).
		// Free: it sends no transaction. Glyph shows it in its own window.
		async signMessage(id, address, message, cb) {
			const p = provider(id);
			if (!p) return send(cb, { ok: false, error: 'Connect your wallet first.' });
			const hex = '0x' + Array.from(new TextEncoder().encode(message), (b) => b.toString(16).padStart(2, '0')).join('');
			try {
				send(cb, { ok: true, signature: await p.request({ method: 'personal_sign', params: [hex, address] }) });
			} catch (err) {
				const rejected = err && err.code === 4001;
				send(cb, { ok: false, error: rejected ? 'You cancelled the signature.' : String((err && err.message) || err) });
			}
		},
		async disconnectWallet(id) {
			const p = provider(id);
			try { await p.request({ method: 'wallet_revokePermissions', params: [{ eth_accounts: {} }] }); } catch (_) {}
		},
	};
})();
"""

var _js  # untyped on purpose: its methods are JavaScript functions
# JavaScriptBridge callbacks must stay referenced, or Godot frees them before the wallet answers.
var _connect_cb: JavaScriptObject
var _event_cb: JavaScriptObject
var _sign_cb: JavaScriptObject
var _wallet_id := ""


static func is_supported() -> bool:
	return OS.has_feature("web")


static func chain_name(chain_id: int) -> String:
	return CHAIN_NAMES.get(chain_id, "Chain %d" % chain_id)


static func short_address(address: String) -> String:
	return address if address.length() < 12 else "%s…%s" % [address.left(6), address.right(4)]


func _ready() -> void:
	if not is_supported():
		return
	JavaScriptBridge.eval(JS, true)
	_js = JavaScriptBridge.get_interface("impzWallet")
	_connect_cb = JavaScriptBridge.create_callback(_on_connect_result)
	_event_cb = JavaScriptBridge.create_callback(_on_wallet_event)
	_sign_cb = JavaScriptBridge.create_callback(_on_signed)
	_js.setEvents(_event_cb)


## Emits wallets_listed. Wallets announce themselves asynchronously, so this waits a moment first.
func list_wallets() -> void:
	if not is_supported():
		wallets_listed.emit([])
		return
	_js.list()
	await get_tree().create_timer(0.25).timeout
	var parsed = JSON.parse_string(str(_js.list()))
	wallets_listed.emit(parsed if parsed is Array else [])


func connect_wallet(wallet_id: String) -> void:
	_wallet_id = wallet_id
	_js.connectWallet(wallet_id, _connect_cb)


## Asks the connected wallet to sign `message`. A coroutine: `var r := await wallet.sign_message(a, m)`.
func sign_message(address: String, message: String) -> Dictionary:
	if not is_supported() or _wallet_id == "":
		return {ok = false, error = "Connect your wallet first."}
	_js.signMessage(_wallet_id, address, message, _sign_cb)
	return await signed


func _on_signed(args: Array) -> void:
	var data = JSON.parse_string(str(args[0]))
	signed.emit(data if data is Dictionary else {ok = false, error = "The wallet gave no answer."})


func disconnect_wallet() -> void:
	if is_supported() and _wallet_id != "":
		_js.disconnectWallet(_wallet_id)
	_wallet_id = ""


static func _parse_chain(value) -> int:
	var text := str(value)
	return text.hex_to_int() if text.begins_with("0x") else int(text)


func _on_connect_result(args: Array) -> void:
	var data = JSON.parse_string(str(args[0]))
	if not data is Dictionary or not data.get("ok", false):
		_wallet_id = ""
		connect_failed.emit(str(data.get("error", "Could not connect.")) if data is Dictionary else "Could not connect.")
		return
	connected.emit(str(data.address), _parse_chain(data.chainId))


func _on_wallet_event(args: Array) -> void:
	var data = JSON.parse_string(str(args[0]))
	if not data is Dictionary:
		return
	match data.get("type"):
		"accounts":
			if str(data.address) == "":
				_wallet_id = ""
			account_changed.emit(str(data.address))
		"chain":
			chain_changed.emit(_parse_chain(data.chainId))
