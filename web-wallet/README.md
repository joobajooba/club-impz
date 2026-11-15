# web-wallet: Glyph for the Club Impz web build

Players connect with **Glyph** on ApeChain (`docs/game_direction.md`). Glyph's SDK (`@use-glyph/sdk-react`) is React-only, and its `glyphWalletConnector()` is a thin wrapper around Privy's cross-app wallet with Glyph's Privy app id. `src/glyph-wallet.js` uses that directly: `toPrivyWalletProvider()` from `@privy-io/cross-app-connect` gives a standard EIP-1193 provider, exposed as `window.impzGlyph`. `godot-game/ui/profile/wallet_bridge.gd` lists it first as "Glyph", next to any browser extension wallets.

The web export loads it through the Web preset's `html/head_include` (`godot-game/export_presets.cfg`). Glyph answers a login by sending its popup back to the game's page. The head include then stops the page, so the game doesn't start inside the popup.

## Test locally

```sh
cd web-wallet
npm install
npm start          # build the bundle, export the game (release), serve on http://localhost:8060
```

Or step by step: `npm run build`, `npm run export` (`-- --debug` for a debug build with the TEST trait switch), `npm run serve`. Set `GODOT` if the Godot editor exe isn't at `C:/Users/lucas/Downloads/Godot_v4.7.2-stable_win64.exe/godot.exe.exe`.

`npm run serve` runs the beta server, `game-server/server.mjs`, on port 8060. It's the same server as the live beta. It serves the build, runs the multiplayer room on `/ws`, and forwards `/api/imps` and `/api/profile` to impz.club. impz.club sends no CORS header, so in web builds the game asks its own site instead. Open the page in two tabs (or two browsers) to see two Imps.

## Notes

- The Glyph app id is copied from `@use-glyph/sdk-react` 2.2.9 (`GLYPH_PRIVY_APP_ID`). Check it again if Glyph changes its SDK.
- Connecting opens a popup, so allow popups for localhost if the browser blocks it.
- Ownership is read from the Imp contract on Robinhood Chain for the connected address. A Glyph wallet only shows Impz held at that same address.
